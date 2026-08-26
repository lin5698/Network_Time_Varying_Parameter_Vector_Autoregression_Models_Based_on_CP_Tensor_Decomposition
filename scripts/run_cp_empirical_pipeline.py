import argparse
import ast
import builtins
import functools
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import io
import json
import logging
import math
import os
import site
import stat
import subprocess
import sys
import sysconfig
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp" / "matplotlib_cache"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp" / "xdg_cache"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.iv.absorbing import AbsorbingLS
from linearmodels.panel import PanelOLS
from linearmodels.panel.utility import AbsorbingEffectError
from natcs_design_contract import equationwise_ridge_fit, lagged_network_exposure

RAW_HELPER_ERROR = (
    "A scientific rebuild requires a verified helper checkout and frozen trust manifest."
)
helper_repo = os.environ.get("NATCS_RCEP_HELPER_REPO")
RCEP_HELPER_TRUST_MANIFEST = ROOT / "manuscript_src" / "natcs" / "rcep_helper_trust_manifest.json"
_HELPER_IDENTITY = None
RCEP_HELPER_TRUST_SCHEMA_VERSION = 2
RCEP_HELPER_FILES = {
    "config.py",
    "research_data_construction.py",
    "research_network_tvp_var.py",
}

RCEP_DATA_APIS = (
    "RCEP_LIST",
    "build_tariff_relief_tc",
    "chow_lin_quarterly_vax",
    "load_quarterly_macro_and_bilateral",
    "quality_control_missing",
    "quality_control_outliers",
)
RCEP_NETWORK_APIS = ("girf_one", "moving_average_coefficients")


def _sha256(path: Path) -> str:
    # Hash the same descriptor-backed, no-follow snapshot that authorized
    # readers consume.  This keeps the identity check from reopening a path
    # through a symlink or a replaced non-regular file.
    return hashlib.sha256(_read_nofollow_snapshot(path, "hash input")).hexdigest()


def _read_nofollow_snapshot(path: Path, label: str) -> bytes:
    source = Path(path)
    if source.is_symlink():
        raise RuntimeError(f"The {label} path is a symlink.")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(source, flags)
    except OSError as exc:
        raise RuntimeError(f"The {label} cannot be opened without following symlinks.") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError(f"The {label} is not a regular file.")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def read_authorized_input_snapshot(path: Path, expected_sha256: str) -> bytes:
    if not _is_sha256(expected_sha256):
        raise RuntimeError("The authorized input snapshot SHA-256 is invalid.")
    snapshot = _read_nofollow_snapshot(path, "authorized input")
    if hashlib.sha256(snapshot).hexdigest() != expected_sha256.lower():
        raise RuntimeError("The authorized input snapshot SHA-256 does not match.")
    return snapshot


def _validated_helper_identity(expected_manifest_sha256=None):
    if not helper_repo:
        raise RuntimeError(f"{RAW_HELPER_ERROR} NATCS_RCEP_HELPER_REPO is absent.")
    manifest_path = Path(RCEP_HELPER_TRUST_MANIFEST)
    try:
        manifest_snapshot = _read_nofollow_snapshot(manifest_path, "helper trust manifest")
    except RuntimeError as exc:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper trust manifest is absent or unsafe.") from exc
    manifest_sha256 = hashlib.sha256(manifest_snapshot).hexdigest()
    if expected_manifest_sha256 is not None and (
        not _is_sha256(expected_manifest_sha256) or manifest_sha256 != expected_manifest_sha256.lower()
    ):
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper trust manifest identity does not match authorization.")

    repo = Path(helper_repo).expanduser()
    if repo.is_symlink() or not repo.is_dir():
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper path must be a non-symlink directory.")
    repo = repo.resolve()
    try:
        manifest = json.loads(manifest_snapshot.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper trust manifest is unreadable.") from exc

    expected_keys = {"schema_version", "helper_git_commit", "files"}
    if set(manifest) != expected_keys or manifest.get("schema_version") != RCEP_HELPER_TRUST_SCHEMA_VERSION:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper trust manifest schema is invalid.")
    expected_files = RCEP_HELPER_FILES
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != expected_files:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper trust manifest file set is invalid.")

    try:
        head = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper Git identity cannot be verified.") from exc
    if head != manifest.get("helper_git_commit"):
        raise RuntimeError(f"{RAW_HELPER_ERROR} The helper Git commit does not match the frozen manifest.")

    for name in sorted(expected_files):
        source = repo / name
        expected_hash = files.get(name)
        if not _is_sha256(expected_hash) or not source.is_file() or source.is_symlink():
            raise RuntimeError(f"{RAW_HELPER_ERROR} Helper source identity mismatch: {name}.")
        tracked_ok, _ = _git_check(repo, "ls-files", "--error-unmatch", "--", name)
        if not tracked_ok:
            raise RuntimeError(f"{RAW_HELPER_ERROR} Helper source is not tracked by the frozen commit: {name}.")
    status_ok, helper_status = _git_check(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *sorted(expected_files),
    )
    if not status_ok:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The bound helper-file status cannot be verified.")
    if helper_status:
        raise RuntimeError(f"{RAW_HELPER_ERROR} The bound helper files are not clean relative to the frozen commit.")
    source_snapshots = {
        name: read_authorized_input_snapshot(repo / name, files[name]) for name in sorted(expected_files)
    }
    return (
        repo,
        head,
        tuple(sorted(files.items())),
        manifest_sha256,
        tuple(sorted(source_snapshots.items())),
    )


def _git_check(repo: Path, *args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        output = getattr(exc, "stderr", "") or getattr(exc, "stdout", "") or str(exc)
        return False, output.strip()
    return True, result.stdout.strip()


def _git_blob_sha256(repo: Path, relative_path: str) -> str:
    """Return SHA-256 of bytes stored at HEAD, independent of the worktree."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "blob", f"HEAD:{relative_path}"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("The frozen Git blob identity cannot be verified.") from exc
    return hashlib.sha256(result.stdout).hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_verified_helper_imports(repo: Path, source_snapshots: dict[str, bytes]) -> None:
    bound_modules = {Path(name).stem for name in source_snapshots}
    prohibited_calls = {
        "__import__",
        "builtins.__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "globals",
        "getattr",
        "importlib.import_module",
        "locals",
        "runpy.run_module",
        "runpy.run_path",
        "setattr",
        "vars",
    }
    prohibited_attributes = {
        "__dict__",
        "__getattribute__",
        "__path__",
        "meta_path",
        "modules",
        "path_hooks",
        "path_importer_cache",
    }
    for filename, snapshot in source_snapshots.items():
        try:
            tree = ast.parse(snapshot, filename=str(repo / filename))
        except SyntaxError as exc:
            raise RuntimeError(f"{RAW_HELPER_ERROR} Verified helper source is not valid Python: {filename}.") from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "__builtins__":
                raise RuntimeError(f"{RAW_HELPER_ERROR} Helper builtin mutation is outside the frozen closure.")
            if isinstance(node, ast.Attribute) and node.attr in prohibited_attributes:
                raise RuntimeError(f"{RAW_HELPER_ERROR} Helper import-path mutation is outside the frozen closure.")
            if isinstance(node, ast.Import):
                imports = [(alias.name, 0) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports = [(node.module or "", node.level)]
            else:
                imports = []
            for module_name, level in imports:
                if level:
                    raise RuntimeError(f"{RAW_HELPER_ERROR} Relative helper imports are outside the frozen closure.")
                root_name = module_name.split(".", 1)[0]
                if root_name in {"builtins", "importlib", "runpy"}:
                    raise RuntimeError(f"{RAW_HELPER_ERROR} Dynamic-import facilities are outside the frozen closure.")
                local_candidates = (repo / f"{root_name}.py", repo / root_name)
                if any(candidate.exists() for candidate in local_candidates) and root_name not in bound_modules:
                    raise RuntimeError(f"{RAW_HELPER_ERROR} Unbound local helper import: {root_name}.")
            if isinstance(node, ast.Call):
                current = node.func
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                if ".".join(reversed(parts)) in prohibited_calls:
                    raise RuntimeError(f"{RAW_HELPER_ERROR} Dynamic code or imports are outside the frozen closure.")


def _trusted_helper_import_roots() -> set[Path]:
    runtime_paths = sysconfig.get_paths()
    roots = {
        Path(runtime_paths[key]).expanduser().resolve()
        for key in ("stdlib", "platstdlib", "purelib", "platlib")
        if runtime_paths.get(key)
    }
    try:
        site_paths = list(site.getsitepackages())
    except (AttributeError, OSError):
        site_paths = []
    try:
        user_site = site.getusersitepackages()
    except (AttributeError, OSError):
        user_site = None
    if isinstance(user_site, (str, os.PathLike)):
        site_paths.append(user_site)
    elif user_site:
        site_paths.extend(user_site)
    roots.update(
        Path(path).expanduser().resolve()
        for path in site_paths
        if isinstance(path, (str, os.PathLike)) and path
    )
    return roots


def _helper_spec_uses_untrusted_code(spec, repo: Path, trusted_roots: set[Path]) -> bool:
    locations = []
    origin = getattr(spec, "origin", None)
    if origin not in (None, "built-in", "frozen"):
        locations.append(origin)
    locations.extend(getattr(spec, "submodule_search_locations", None) or ())
    if not locations and origin not in ("built-in", "frozen"):
        return True
    for location in locations:
        location_path = Path(location).expanduser().resolve()
        if _is_within(location_path, repo) or _is_within(location_path, ROOT):
            return True
        if not any(_is_within(location_path, root) for root in trusted_roots):
            return True
    return False


def _loaded_module_spec(module):
    return getattr(module, "__spec__", None)


class _VerifiedHelperMetaPathGuard(importlib.abc.MetaPathFinder):
    def __init__(self, repo: Path, bound_modules: set[str], trusted_roots: set[Path]):
        self.repo = repo
        self.bound_modules = bound_modules
        self.trusted_roots = trusted_roots

    def find_spec(self, fullname, path=None, target=None):
        root_name = fullname.split(".", 1)[0]
        if root_name in self.bound_modules:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is not None and _helper_spec_uses_untrusted_code(
            spec,
            self.repo,
            self.trusted_roots,
        ):
            raise ImportError(f"{RAW_HELPER_ERROR} Unbound local helper import: {fullname}.")
        return None


def _helper_import_guard(repo: Path, bound_modules: set[str], trusted_roots: set[Path]):
    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level:
            raise RuntimeError(f"{RAW_HELPER_ERROR} Relative helper imports are outside the frozen closure.")
        root_name = name.split(".", 1)[0]
        if root_name in {"builtins", "importlib", "runpy"}:
            raise RuntimeError(f"{RAW_HELPER_ERROR} Dynamic-import facilities are outside the frozen closure.")
        trusted_search_path = [
            str(repo),
            *(str(root) for root in sorted(trusted_roots, key=str)),
        ]
        if root_name not in bound_modules:
            module = sys.modules.get(root_name)
            if module is not None:
                spec = _loaded_module_spec(module)
            else:
                spec = importlib.machinery.BuiltinImporter.find_spec(root_name)
                if spec is None:
                    spec = importlib.machinery.FrozenImporter.find_spec(root_name)
                if spec is None:
                    spec = importlib.machinery.PathFinder.find_spec(root_name, trusted_search_path)
            if spec is None or _helper_spec_uses_untrusted_code(
                spec,
                repo,
                trusted_roots,
            ):
                raise RuntimeError(f"{RAW_HELPER_ERROR} Unbound local helper import: {root_name}.")
        original_meta_path = sys.meta_path
        original_meta_snapshot = tuple(original_meta_path)
        original_sys_path = sys.path
        original_sys_snapshot = tuple(original_sys_path)
        try:
            sys.meta_path = [
                importlib.machinery.BuiltinImporter,
                importlib.machinery.FrozenImporter,
                importlib.machinery.PathFinder,
            ]
            sys.path = list(trusted_search_path)
            imported = builtins.__import__(name, globals, locals, fromlist, level)
        finally:
            original_meta_path[:] = original_meta_snapshot
            original_sys_path[:] = original_sys_snapshot
            sys.meta_path = original_meta_path
            sys.path = original_sys_path
        imported_root = sys.modules.get(root_name)
        if root_name not in bound_modules and imported_root is not None:
            imported_spec = _loaded_module_spec(imported_root)
            if _helper_spec_uses_untrusted_code(imported_spec, repo, trusted_roots):
                raise RuntimeError(f"{RAW_HELPER_ERROR} Imported module escaped the frozen closure: {root_name}.")
        return imported

    return guarded_import


def _wrap_verified_helper_api(
    function,
    meta_path_guard: _VerifiedHelperMetaPathGuard,
):
    """Keep the verified import boundary active during lazy helper calls."""

    @functools.wraps(function)
    def guarded(*args, **kwargs):
        original_meta_path = sys.meta_path
        original_meta_snapshot = tuple(original_meta_path)
        original_sys_path = sys.path
        original_sys_snapshot = tuple(original_sys_path)
        try:
            sys.meta_path = [
                meta_path_guard,
                importlib.machinery.BuiltinImporter,
                importlib.machinery.FrozenImporter,
                importlib.machinery.PathFinder,
            ]
            return function(*args, **kwargs)
        finally:
            # Restore both the object and its contents.  A helper that replaces
            # either list cannot leak its import-path mutation into the caller.
            original_meta_path[:] = original_meta_snapshot
            original_sys_path[:] = original_sys_snapshot
            sys.meta_path = original_meta_path
            sys.path = original_sys_path

    return guarded


def require_raw_helper(expected_manifest_sha256=None):
    global _HELPER_IDENTITY
    global RCEP_LIST
    global build_tariff_relief_tc, chow_lin_quarterly_vax
    global load_quarterly_macro_and_bilateral, quality_control_missing, quality_control_outliers
    global girf_one, moving_average_coefficients

    identity = _validated_helper_identity(expected_manifest_sha256)
    if _HELPER_IDENTITY is not None:
        if _HELPER_IDENTITY != identity:
            raise RuntimeError(f"{RAW_HELPER_ERROR} The cached helper identity does not match the current checkout.")
        return _HELPER_IDENTITY
    repo = identity[0]
    helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
    preloaded = [name for name in helper_module_names if name in sys.modules]
    if preloaded:
        raise RuntimeError(
            f"{RAW_HELPER_ERROR} Helper modules were preloaded before identity verification: {', '.join(preloaded)}."
        )
    source_snapshots = dict(identity[4])
    _validate_verified_helper_imports(repo, source_snapshots)
    baseline_sys_path = tuple(sys.path)
    trusted_import_roots = _trusted_helper_import_roots()
    guarded_import = _helper_import_guard(
        repo,
        {Path(name).stem for name in source_snapshots},
        trusted_import_roots,
    )
    meta_path_guard = _VerifiedHelperMetaPathGuard(
        repo,
        {Path(name).stem for name in source_snapshots},
        trusted_import_roots,
    )
    helper_builtins = {
        name: value
        for name, value in vars(builtins).items()
        if name not in {"compile", "eval", "exec", "open"}
    }
    helper_builtins["__import__"] = guarded_import
    modules = {}
    baseline_meta_path = tuple(sys.meta_path)
    try:
        sys.meta_path[:] = [
            meta_path_guard,
            importlib.machinery.BuiltinImporter,
            importlib.machinery.FrozenImporter,
            importlib.machinery.PathFinder,
        ]
        for module_name in helper_module_names:
            source_path = repo / f"{module_name}.py"
            module = types.ModuleType(module_name)
            module.__file__ = str(source_path)
            module.__package__ = ""
            module.__dict__["__builtins__"] = types.MappingProxyType(helper_builtins)
            modules[module_name] = module
            sys.modules[module_name] = module
        for module_name in helper_module_names:
            source_path = repo / f"{module_name}.py"
            code = compile(source_snapshots[source_path.name], str(source_path), "exec")
            exec(code, modules[module_name].__dict__)
    except BaseException as exc:
        for module_name, module in modules.items():
            if sys.modules.get(module_name) is module:
                sys.modules.pop(module_name, None)
        raise RuntimeError(f"{RAW_HELPER_ERROR} Verified helper source execution failed.") from exc
    finally:
        sys.meta_path[:] = baseline_meta_path
        sys.path[:] = baseline_sys_path

    config_module = modules["config"]
    data_module = modules["research_data_construction"]
    network_module = modules["research_network_tvp_var"]
    try:
        if config_module is None or Path(config_module.__file__).resolve() != repo / "config.py":
            raise RuntimeError(f"{RAW_HELPER_ERROR} The config import resolved outside the verified checkout.")
        if Path(data_module.__file__).resolve() != repo / "research_data_construction.py":
            raise RuntimeError(f"{RAW_HELPER_ERROR} The data-helper import resolved outside the verified checkout.")
        if Path(network_module.__file__).resolve() != repo / "research_network_tvp_var.py":
            raise RuntimeError(f"{RAW_HELPER_ERROR} The network-helper import resolved outside the verified checkout.")
        missing = [name for name in RCEP_DATA_APIS if not hasattr(data_module, name)]
        missing += [name for name in RCEP_NETWORK_APIS if not callable(getattr(network_module, name, None))]
        if missing:
            raise RuntimeError(f"{RAW_HELPER_ERROR} Missing helper API: {', '.join(missing)}.")
    except BaseException:
        for module_name, module in modules.items():
            if sys.modules.get(module_name) is module:
                sys.modules.pop(module_name, None)
        raise

    RCEP_LIST = data_module.RCEP_LIST
    build_tariff_relief_tc = _wrap_verified_helper_api(
        data_module.build_tariff_relief_tc, meta_path_guard
    )
    chow_lin_quarterly_vax = _wrap_verified_helper_api(
        data_module.chow_lin_quarterly_vax, meta_path_guard
    )
    load_quarterly_macro_and_bilateral = _wrap_verified_helper_api(
        data_module.load_quarterly_macro_and_bilateral, meta_path_guard
    )
    quality_control_missing = _wrap_verified_helper_api(
        data_module.quality_control_missing, meta_path_guard
    )
    quality_control_outliers = _wrap_verified_helper_api(
        data_module.quality_control_outliers, meta_path_guard
    )
    girf_one = _wrap_verified_helper_api(network_module.girf_one, meta_path_guard)
    moving_average_coefficients = _wrap_verified_helper_api(
        network_module.moving_average_coefficients, meta_path_guard
    )
    _HELPER_IDENTITY = identity
    return identity


RCEP_LIST = ()


def _raw_helper_unavailable(*_args, **_kwargs):
    raise RuntimeError(RAW_HELPER_ERROR)


build_tariff_relief_tc = _raw_helper_unavailable
chow_lin_quarterly_vax = _raw_helper_unavailable
load_quarterly_macro_and_bilateral = _raw_helper_unavailable
quality_control_missing = _raw_helper_unavailable
quality_control_outliers = _raw_helper_unavailable
girf_one = _raw_helper_unavailable
moving_average_coefficients = _raw_helper_unavailable

EPS = 1e-10


def _local_moving_average_coefficients(A_list, B_list, W_list, horizon, W_fixed=None):
    """Dataset-neutral MA recursion used when the RCEP helper is not in scope."""
    p = len(A_list)
    n = A_list[0].shape[0]
    psi = [np.eye(n)]
    for h in range(1, horizon + 1):
        current = np.zeros((n, n))
        for lag in range(1, min(p + 1, h + 1)):
            previous = h - lag
            if previous >= len(psi):
                continue
            current += A_list[lag - 1] @ psi[previous]
            W_use = W_fixed if W_fixed is not None else (
                W_list[previous] if previous < len(W_list) else None
            )
            if W_use is not None and B_list[lag - 1] is not None:
                current += B_list[lag - 1] @ np.asarray(W_use) @ psi[previous]
        psi.append(current)
    return psi


def _local_girf_one(Phi_h, Sigma, j_shock, scale=1.0):
    """Generalized impulse response for the helper-independent NYC path."""
    n = Sigma.shape[0]
    shock_scale = np.sqrt(Sigma[j_shock, j_shock] + 1e-12)
    shock = np.zeros(n)
    shock[j_shock] = 1.0
    return (Phi_h @ Sigma @ shock) / shock_scale * scale


def build_trade_network_w(df_bilateral, date_val, window_quarters=4, use_import_share=True, mode="import"):
    """Local compatibility wrapper for pandas/numpy read-only pivot arrays."""
    require_raw_helper()
    df = df_bilateral[
        (df_bilateral["date"] <= date_val)
        & (df_bilateral["date"] > (date_val - pd.DateOffset(months=3 * window_quarters)))
    ].copy()
    if df.empty:
        return pd.DataFrame(np.zeros((len(RCEP_LIST), len(RCEP_LIST))), index=RCEP_LIST, columns=RCEP_LIST)

    flow_col = "import_usd" if "import_usd" in df.columns else "export_usd"
    df["flow"] = pd.to_numeric(df[flow_col], errors="coerce").fillna(0)

    if mode == "export":
        if "export_usd" in df.columns:
            df["flow"] = pd.to_numeric(df["export_usd"], errors="coerce").fillna(0)
        agg = df.groupby(["reporter_iso", "partner_iso"])["flow"].sum().reset_index()
        total_j = agg.groupby("partner_iso")["flow"].sum().reset_index().rename(columns={"flow": "total"})
        agg = agg.merge(total_j, on="partner_iso")
        agg["w"] = agg["flow"] / agg["total"].replace(0, np.nan)
        W = agg.pivot_table(index="reporter_iso", columns="partner_iso", values="w", fill_value=0)
    elif mode == "symmetric":
        df["pair"] = df.apply(lambda x: tuple(sorted([x["reporter_iso"], x["partner_iso"]])), axis=1)
        agg = df.groupby("pair")["flow"].sum().reset_index()
        pairs = []
        for pair, flow in zip(agg["pair"], agg["flow"]):
            pairs.append({"reporter_iso": pair[0], "partner_iso": pair[1], "flow": flow})
            pairs.append({"reporter_iso": pair[1], "partner_iso": pair[0], "flow": flow})
        agg = pd.DataFrame(pairs)
        total_i = agg.groupby("reporter_iso")["flow"].sum().reset_index().rename(columns={"flow": "total"})
        agg = agg.merge(total_i, on="reporter_iso")
        agg["w"] = agg["flow"] / agg["total"].replace(0, np.nan)
        W = agg.pivot_table(index="reporter_iso", columns="partner_iso", values="w", fill_value=0)
    else:
        agg = df.groupby(["reporter_iso", "partner_iso"])["flow"].sum().reset_index()
        total_i = agg.groupby("reporter_iso")["flow"].sum().reset_index().rename(columns={"flow": "total"})
        agg = agg.merge(total_i, on="reporter_iso")
        agg["w"] = agg["flow"] / agg["total"].replace(0, np.nan)
        W = agg.pivot_table(index="reporter_iso", columns="partner_iso", values="w", fill_value=0)

    W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0)
    values = W.to_numpy(dtype=float, copy=True)
    np.fill_diagonal(values, 0.0)
    W = pd.DataFrame(values, index=W.index, columns=W.columns)
    row_sums = W.sum(axis=1).replace(0, np.nan)
    return W.div(row_sums, axis=0).fillna(0)


def var_ols(Y, W_list, X_exog=None, p=2, lambda_ridge=1e-4):
    return equationwise_ridge_fit(
        Y,
        W_list,
        X_exog=X_exog,
        p=p,
        lambda_ridge=lambda_ridge,
    )

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
AUTHORIZED_OUTPUT_ROOT = ROOT / "output" / "natcs_empirical_cp_authorized_runs"
_AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES = {}
SCIENTIFIC_AUTHORIZATION_SCHEMA_VERSION = 1
SCIENTIFIC_AUTHORIZATION_ERROR = (
    "A scientific rebuild requires an exact, author-approved scientific execution authorization."
)
SCIENTIFIC_AUTHORIZATION_ARGV = (
    "window",
    "p",
    "n_boot",
    "block_size",
    "cp_inits",
    "cp_max_iter",
    "cp_tol",
)
SCIENTIFIC_AUTHORIZATION_IMPLEMENTATION_FILES = {
    "scripts/run_cp_empirical_pipeline.py",
    "scripts/natcs_design_contract.py",
}
NYC_TAXI_UPSTREAM_COMMIT = "7e63ba9734021171eaf49edb92be8a7e7e8802eb"
NYC_TAXI_REQUIRED_FILES = tuple(f"yellow_taxi_trip_{year}.npz" for year in range(2012, 2022))
RCEP_REQUIRED_INPUT_FILENAMES = (
    "master_quarterly_macro_2005_2024.csv",
    "master_quarterly_bilateral_2005_2024.csv",
)


def _validated_nyc_taxi_source(dataset_dir=None):
    supplied_dir = dataset_dir or os.environ.get("NATCS_NYC_TAXI_DATASET_DIR")
    if not supplied_dir:
        raise RuntimeError(
            "A raw-to-derived NYC Taxi rebuild requires NATCS_NYC_TAXI_DATASET_DIR to point to a verified datasets/NYC-taxi checkout."
        )
    source_path = Path(supplied_dir).expanduser()
    if source_path.is_symlink() or not source_path.is_dir():
        raise RuntimeError("The NYC Taxi source path must be a non-symlink directory.")
    taxi_root = source_path.resolve()

    root_ok, root_text = _git_check(taxi_root, "rev-parse", "--show-toplevel")
    commit_ok, commit = _git_check(taxi_root, "rev-parse", "HEAD")
    if not root_ok or not commit_ok:
        raise RuntimeError("The NYC Taxi source Git identity cannot be verified.")
    git_root = Path(root_text).resolve()
    if taxi_root != git_root / "datasets" / "NYC-taxi":
        raise RuntimeError("The NYC Taxi source must resolve to datasets/NYC-taxi in the verified checkout.")
    if commit != NYC_TAXI_UPSTREAM_COMMIT:
        raise RuntimeError("The NYC Taxi source commit does not match the frozen upstream commit.")

    file_hashes = []
    relative_paths = []
    for name in NYC_TAXI_REQUIRED_FILES:
        source = taxi_root / name
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f"NYC Taxi source identity mismatch: {name}.")
        relative_path = str(source.relative_to(git_root))
        tracked_ok, _ = _git_check(git_root, "ls-files", "--error-unmatch", "--", relative_path)
        if not tracked_ok:
            raise RuntimeError(f"NYC Taxi source is not tracked by the frozen commit: {name}.")
        expected_sha256 = _git_blob_sha256(git_root, relative_path)
        if _sha256(source) != expected_sha256:
            raise RuntimeError(
                f"NYC Taxi source files are not clean relative to the frozen commit: byte mismatch for {name}."
            )
        relative_paths.append(relative_path)
        file_hashes.append((name, expected_sha256))
    status_ok, source_status = _git_check(
        git_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *relative_paths,
    )
    if not status_ok:
        raise RuntimeError("The NYC Taxi source-file status cannot be verified.")
    if source_status:
        raise RuntimeError("The NYC Taxi source files are not clean relative to the frozen commit.")
    return taxi_root, commit, tuple(file_hashes)

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _open_child_directory(parent_fd: int, name: str, *, allow_existing: bool, label: str) -> int:
    try:
        os.mkdir(name, mode=0o750, dir_fd=parent_fd)
    except FileExistsError as exc:
        mode = os.stat(name, dir_fd=parent_fd, follow_symlinks=False).st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"The {label} is a symlink and cannot receive scientific outputs.") from exc
        if not allow_existing:
            raise RuntimeError(f"The {label} already exists; overwrite is denied.") from exc
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise RuntimeError(f"The {label} is not a no-follow directory.") from exc


def output_paths(dataset: str, output_root: Path):
    out_dir = Path(output_root).expanduser()
    if out_dir.name != dataset:
        raise RuntimeError("The authorized output root does not match the selected dataset.")
    authorized_base = out_dir.parent.parent
    base_parent = authorized_base.parent
    if base_parent != base_parent.resolve() or base_parent.is_symlink() or not base_parent.is_dir():
        raise RuntimeError("The authorized output base has a symlinked or unavailable parent.")
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    parent_fd = os.open(base_parent, parent_flags)
    base_fd = decision_fd = out_fd = figures_fd = None
    output_identity = figure_identity = None
    try:
        base_fd = _open_child_directory(
            parent_fd,
            authorized_base.name,
            allow_existing=True,
            label="authorized output base",
        )
        decision_fd = _open_child_directory(
            base_fd,
            out_dir.parent.name,
            allow_existing=False,
            label="authorized decision directory",
        )
        out_fd = _open_child_directory(
            decision_fd,
            dataset,
            allow_existing=False,
            label="authorized output root",
        )
        figures_fd = _open_child_directory(
            out_fd,
            "figures",
            allow_existing=False,
            label="authorized figure directory",
        )
        out_stat = os.fstat(out_fd)
        figure_stat = os.fstat(figures_fd)
        output_identity = (out_stat.st_dev, out_stat.st_ino)
        figure_identity = (figure_stat.st_dev, figure_stat.st_ino)
    finally:
        for descriptor in (figures_fd, out_fd, decision_fd, base_fd, parent_fd):
            if descriptor is not None:
                os.close(descriptor)
    if out_dir.is_symlink() or not out_dir.is_dir() or out_dir != out_dir.resolve():
        raise RuntimeError("The authorized output root changed during no-follow creation.")
    fig_dir = out_dir / "figures"
    _AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES[out_dir] = output_identity
    _AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES[fig_dir] = figure_identity
    return out_dir, fig_dir


def _open_exclusive_output(path: Path, *, binary: bool):
    target = Path(path)
    parent = target.parent
    expected_identity = _AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES.get(parent)
    if expected_identity is None:
        raise RuntimeError("The output parent is not an authorized reserved directory.")
    if target.name in {"", ".", ".."} or target.name != str(target.relative_to(parent)):
        raise RuntimeError("The output filename is invalid.")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_fd = os.open(parent, flags)
    except OSError as exc:
        raise RuntimeError("The authorized output directory cannot be reopened without following symlinks.") from exc
    try:
        parent_stat = os.fstat(parent_fd)
        if (parent_stat.st_dev, parent_stat.st_ino) != expected_identity:
            raise RuntimeError("The authorized output directory identity changed after reservation.")
        file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(target.name, file_flags, 0o600, dir_fd=parent_fd)
        except OSError as exc:
            raise RuntimeError("The authorized output file already exists or is unsafe.") from exc
    finally:
        os.close(parent_fd)
    if binary:
        return os.fdopen(descriptor, "wb")
    return os.fdopen(descriptor, "w", encoding="utf-8", newline="")


def write_output_csv(frame, path: Path):
    with _open_exclusive_output(path, binary=False) as handle:
        frame.to_csv(handle, index=False)


def write_output_json(payload, path: Path):
    with _open_exclusive_output(path, binary=False) as handle:
        json.dump(payload, handle, indent=2)


def save_output_figure(fig, path: Path, *, dpi=None):
    target = Path(path)
    output_format = target.suffix.lower().lstrip(".")
    if output_format not in {"png", "pdf"}:
        raise RuntimeError("The requested figure output format is not authorized.")
    save_options = {"format": output_format}
    if dpi is not None:
        save_options["dpi"] = dpi
    with _open_exclusive_output(target, binary=True) as handle:
        fig.savefig(handle, **save_options)


def quarter_label(ts: pd.Timestamp) -> str:
    return f"{ts.year}Q{ts.quarter}"


def safe_row_normalize(W: np.ndarray) -> np.ndarray:
    W = np.asarray(W, dtype=float).copy()
    np.fill_diagonal(W, 0.0)
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums <= EPS] = 1.0
    return W / row_sums


def top_import_exposure_perturbation(W: np.ndarray, scale_factor: float = 0.5):
    W_base = safe_row_normalize(W)
    incoming = W_base.sum(axis=0)
    hub = int(np.argmax(incoming / max(incoming.sum(), EPS)))
    W_perturbed = W_base.copy()
    W_perturbed[:, hub] *= scale_factor
    return hub, safe_row_normalize(W_perturbed)


def load_rcep_panel_data(input_identity):
    manifest_sha256 = input_identity.get("rcep_helper_manifest_sha256") if isinstance(input_identity, dict) else None
    require_raw_helper(manifest_sha256)
    authorized_files = input_identity.get("rcep_input_files") if isinstance(input_identity, dict) else None
    if not isinstance(authorized_files, dict):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP input snapshots are not authorized.")
    paths_by_name = {Path(path).name: (Path(path), digest) for path, digest in authorized_files.items()}
    if set(paths_by_name) != set(RCEP_REQUIRED_INPUT_FILENAMES):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP input snapshot set is invalid.")
    macro_path, macro_hash = paths_by_name["master_quarterly_macro_2005_2024.csv"]
    bilateral_path, bilateral_hash = paths_by_name["master_quarterly_bilateral_2005_2024.csv"]
    df_macro = pd.read_csv(io.BytesIO(read_authorized_input_snapshot(macro_path, macro_hash)))
    df_bilateral = pd.read_csv(io.BytesIO(read_authorized_input_snapshot(bilateral_path, bilateral_hash)))
    df_macro["date"] = pd.to_datetime(
        df_macro["date_quarterly"] if "date_quarterly" in df_macro.columns else df_macro["date"]
    )
    df_bilateral["date"] = pd.to_datetime(
        df_bilateral["date_quarterly"] if "date_quarterly" in df_bilateral.columns else df_bilateral["date"]
    )
    df_macro = df_macro[df_macro["iso3"].isin(RCEP_LIST)]
    df_bilateral = df_bilateral[
        df_bilateral["reporter_iso"].isin(RCEP_LIST) & df_bilateral["partner_iso"].isin(RCEP_LIST)
    ]
    df_tc = build_tariff_relief_tc(df_bilateral)

    vax = chow_lin_quarterly_vax(df_macro)
    vax_p = vax.set_index(["date", "iso3"])["vax_q"].unstack("iso3")
    for c in vax_p.columns:
        vax_p[c] = quality_control_outliers(quality_control_missing(vax_p[c]))
    Y = np.log(vax_p + 1e-6).diff().dropna(how="all")
    Y = Y.reindex(columns=RCEP_LIST).fillna(0.0)
    return {
        "dataset": "rcep",
        "Y": Y.values,
        "dates": list(pd.to_datetime(Y.index)),
        "df_bilateral": df_bilateral,
        "df_tc": df_tc,
        "unit_names": list(RCEP_LIST),
        "w_window_quarters": 4,
        "w_mode": "import",
        "primary_label": "Time-Varying",
        "girf_pair": ("CHN", "JPN"),
        "requested_girf_dates": [pd.Timestamp("2018-12-31"), pd.Timestamp("2022-12-31")],
    }


def _build_monthly_taxi_tensor(input_identity):
    if not isinstance(input_identity, dict):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC input snapshot is not authorized.")
    authorized_dir = input_identity.get("nyc_dataset_dir")
    if not isinstance(authorized_dir, str) or not authorized_dir.strip():
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC source path is not bound.")
    taxi_root, commit, file_hashes = _validated_nyc_taxi_source(authorized_dir)
    if input_identity.get("nyc_upstream_commit") != commit:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC input snapshot is not authorized.")
    expected_hashes = dict(file_hashes)
    monthly_mats = []
    monthly_dates = []
    for year in range(2012, 2022):
        name = f"yellow_taxi_trip_{year}.npz"
        snapshot = read_authorized_input_snapshot(taxi_root / name, expected_hashes[name])
        arr = np.load(io.BytesIO(snapshot), allow_pickle=False)["arr_0"]
        dates = pd.date_range(f"{year}-01-01", periods=arr.shape[2], freq="D")
        month_index = pd.PeriodIndex(dates, freq="M")
        for period in month_index.unique():
            idx = np.where(month_index == period)[0]
            monthly_mats.append(arr[:, :, idx].sum(axis=2))
            monthly_dates.append(period.to_timestamp("M"))
    return monthly_dates, monthly_mats


def load_nyc_taxi_data(input_identity):
    monthly_dates, monthly_mats = _build_monthly_taxi_tensor(input_identity)
    rolling_dates = []
    rolling_mats = []
    for idx in range(11, len(monthly_mats)):
        rolling_dates.append(monthly_dates[idx])
        rolling_mats.append(sum(monthly_mats[idx - j] for j in range(12)))

    total_volume = np.zeros(rolling_mats[0].shape[0], dtype=float)
    for mat in rolling_mats:
        total_volume += mat.sum(axis=1) + mat.sum(axis=0)
    top_idx = np.argsort(total_volume)[::-1][:15]
    unit_names = [f"Zone-{int(i) + 1}" for i in top_idx]
    level_rows = []
    w_list = []
    for mat in rolling_mats:
        sub = np.asarray(mat[np.ix_(top_idx, top_idx)], dtype=float)
        total_activity = sub.sum(axis=1) + sub.sum(axis=0)
        level_rows.append(np.log(total_activity + 1e-6))
        w_list.append(safe_row_normalize(sub))
    level = pd.DataFrame(level_rows, index=pd.to_datetime(rolling_dates), columns=unit_names)
    Y = level.copy().fillna(0.0)
    aligned_w = w_list
    aligned_dates = list(pd.to_datetime(Y.index))
    w_pre_dates = [i for i, d in enumerate(aligned_dates) if pd.Timestamp("2016-01-01") <= d <= pd.Timestamp("2019-12-31")]
    if not w_pre_dates:
        w_pre_dates = list(range(min(24, len(aligned_w))))
    W_pre = np.mean([aligned_w[i] for i in w_pre_dates], axis=0)
    return {
        "dataset": "nyc_taxi",
        "Y": Y.values,
        "dates": aligned_dates,
        "unit_names": unit_names,
        "w_list": aligned_w,
        "W_pre": safe_row_normalize(W_pre),
        "df_bilateral": None,
        "df_tc": None,
        "w_window_months": 12,
        "w_mode": "mobility",
        "primary_label": "Rolling 12-month mobility network",
        "girf_pair": (unit_names[0], unit_names[1]),
        "top_indices": [int(i) for i in top_idx],
        "level_panel": level.reset_index().rename(columns={"index": "date"}),
        "requested_girf_dates": [pd.Timestamp("2019-12-31"), pd.Timestamp("2021-12-31")],
        "acquisition_info": {
            "source_repository": "xinychen/vars",
            "commit": NYC_TAXI_UPSTREAM_COMMIT,
            "dataset_path": "datasets/NYC-taxi",
            "construction": "Monthly log trip activity for the 15 highest-flow mobility units with rolling 12-month OD trip-share network matrices.",
        },
    }


def load_dataset(name: str, input_identity):
    if name == "rcep":
        return load_rcep_panel_data(input_identity)
    if name == "nyc_taxi":
        return load_nyc_taxi_data(input_identity)
    raise ValueError(f"Unsupported dataset: {name}")


def _validate_loaded_dataset(data: dict, dataset: str, p: int) -> None:
    """Validate the loaded panel and topology before reserving output paths.

    This is deliberately structural: it checks the objects that downstream
    estimators require, without fitting a model or producing a scientific
    artifact.  The production entry point calls it immediately after loading
    authorized bytes and before creating the quarantine output tree.
    """

    if not isinstance(data, dict):
        raise ValueError("loaded dataset must be a mapping")
    if dataset not in {"rcep", "nyc_taxi"}:
        raise ValueError("unsupported loaded dataset")

    try:
        Y = np.asarray(data["Y"], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Y must be a numeric array") from exc
    if Y.ndim != 2:
        raise ValueError("Y must be two-dimensional")
    n_rows, n_units = Y.shape
    if n_rows <= p:
        raise ValueError("Y must have more rows than the lag order")
    if n_units < 1:
        raise ValueError("Y must contain at least one unit")
    if not np.isfinite(Y).all():
        raise ValueError("Y must contain only finite values")

    dates_value = data.get("dates")
    if isinstance(dates_value, (str, bytes)) or dates_value is None:
        raise ValueError("dates must be a sequence aligned with Y")
    try:
        dates = pd.DatetimeIndex(pd.to_datetime(list(dates_value), errors="raise"))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("dates must be parseable timestamps") from exc
    if len(dates) != n_rows:
        raise ValueError("dates must align with Y")
    if dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError("dates must be strictly increasing without duplicates")

    unit_names = data.get("unit_names")
    if isinstance(unit_names, (str, bytes)) or unit_names is None:
        raise ValueError("unit_names must be a sequence")
    unit_names = list(unit_names)
    if len(unit_names) != n_units:
        raise ValueError("unit_names must align with Y columns")
    if any(not isinstance(name, str) or not name.strip() for name in unit_names):
        raise ValueError("unit_names must be non-empty strings")
    if len(set(unit_names)) != len(unit_names):
        raise ValueError("unit_names must be unique")

    girf_pair = data.get("girf_pair")
    if (
        not isinstance(girf_pair, (tuple, list))
        or len(girf_pair) != 2
        or any(name not in unit_names for name in girf_pair)
        or girf_pair[0] == girf_pair[1]
    ):
        raise ValueError("girf_pair must contain two distinct known units")

    requested_dates = data.get("requested_girf_dates")
    if isinstance(requested_dates, (str, bytes)) or requested_dates is None:
        raise ValueError("requested_girf_dates must be a sequence")
    try:
        pd.to_datetime(list(requested_dates), errors="raise")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("requested_girf_dates must be parseable timestamps") from exc

    if dataset == "nyc_taxi":
        w_list = data.get("w_list")
        if not isinstance(w_list, (list, tuple)) or len(w_list) != n_rows:
            raise ValueError("w_list must have one matrix per panel row")
        for index, matrix in enumerate(w_list):
            try:
                matrix = np.asarray(matrix, dtype=float)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"w_list[{index}] must be numeric") from exc
            if matrix.shape != (n_units, n_units):
                raise ValueError(f"w_list[{index}] has the wrong matrix dimensions")
            if not np.isfinite(matrix).all():
                raise ValueError(f"w_list[{index}] must contain only finite values")
        try:
            W_pre = np.asarray(data["W_pre"], dtype=float)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("W_pre must be a numeric matrix") from exc
        if W_pre.shape != (n_units, n_units) or not np.isfinite(W_pre).all():
            raise ValueError("W_pre has the wrong dimensions or non-finite values")
        level_panel = data.get("level_panel")
        if not isinstance(level_panel, pd.DataFrame) or "date" not in level_panel.columns:
            raise ValueError("level_panel must be a table with a date column")
        if len(level_panel) != n_rows:
            raise ValueError("level_panel must align with Y")
        if any(name not in level_panel.columns for name in unit_names):
            raise ValueError("level_panel is missing a unit column")
        acquisition_info = data.get("acquisition_info")
        if not isinstance(acquisition_info, dict) or not acquisition_info:
            raise ValueError("acquisition_info must be a non-empty mapping")
    else:
        bilateral = data.get("df_bilateral")
        if not isinstance(bilateral, pd.DataFrame):
            raise ValueError("RCEP bilateral panel is missing")
        bilateral_required = {"date", "reporter_iso", "partner_iso"}
        if not bilateral_required.issubset(bilateral.columns):
            raise ValueError("RCEP bilateral panel is missing required columns")
        tariff = data.get("df_tc")
        if not isinstance(tariff, pd.DataFrame):
            raise ValueError("RCEP tariff-relief panel is missing")
        tariff_required = {"date", "reporter_iso", "partner_iso", "TC"}
        if not tariff_required.issubset(tariff.columns):
            raise ValueError("RCEP tariff-relief panel is missing required columns")
        for frame, label in ((bilateral, "bilateral"), (tariff, "tariff-relief")):
            try:
                frame_dates = pd.to_datetime(frame["date"], errors="raise")
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"RCEP {label} dates are not parseable") from exc
            if frame_dates.isna().any():
                raise ValueError(f"RCEP {label} dates contain missing values")
            if not frame[["reporter_iso", "partner_iso"]].notna().all().all():
                raise ValueError(f"RCEP {label} topology identifiers contain missing values")


def compute_w_pre(df_bilateral: pd.DataFrame) -> np.ndarray:
    pre_dates = pd.date_range("2016-01-01", "2019-12-31", freq="QS")
    mats = []
    for d in pre_dates:
        W = build_trade_network_w(df_bilateral, d, window_quarters=4, mode="import")
        if isinstance(W, pd.DataFrame):
            W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0).values
        mats.append(np.asarray(W, dtype=float))
    return np.mean(mats, axis=0)


def build_w_list(df_bilateral: pd.DataFrame, dates, window_quarters=4, mode="import"):
    mats = []
    for d in dates:
        W = build_trade_network_w(df_bilateral, d, window_quarters=window_quarters, mode=mode)
        if isinstance(W, pd.DataFrame):
            W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0).values
        mats.append(np.asarray(W, dtype=float))
    return mats


def beta_matrix_from_lists(A_list, B_list):
    p = len(A_list)
    n = A_list[0].shape[0]
    beta = np.zeros((n, 2 * p))
    for l in range(p):
        beta[:, l] = np.diag(A_list[l])
        beta[:, p + l] = np.diag(B_list[l])
    return beta


def lists_from_beta(beta: np.ndarray, p: int):
    n = beta.shape[0]
    A_list = []
    B_list = []
    for l in range(p):
        A = np.zeros((n, n))
        B = np.zeros((n, n))
        np.fill_diagonal(A, beta[:, l])
        np.fill_diagonal(B, beta[:, p + l])
        A_list.append(A)
        B_list.append(B)
    return A_list, B_list


def predict_one_step(c, beta, y_hist, w_hist, p):
    A_list, B_list = lists_from_beta(beta, p)
    y_hat = np.asarray(c, dtype=float).copy()
    for l in range(1, p + 1):
        y_hat += A_list[l - 1] @ y_hist[-l]
        y_hat += B_list[l - 1] @ (w_hist[-l] @ y_hist[-l])
    return y_hat


def select_global_ridge_lambda(Y, W_list, dates, p=2, window=40, lambdas=None):
    if lambdas is None:
        lambdas = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
    cutoff = pd.Timestamp("2022-01-01")
    losses = {}
    for lam in lambdas:
        errs = []
        for t in range(window, len(Y)):
            if pd.Timestamp(dates[t]) >= cutoff:
                break
            Y_w = Y[t - window : t]
            W_w = W_list[t - window : t]
            c, A_list, B_list, _, _, _ = var_ols(Y_w, W_w, X_exog=None, p=p, lambda_ridge=lam)
            beta = beta_matrix_from_lists(A_list, B_list)
            y_hat = predict_one_step(c, beta, Y[:t], W_list[:t], p)
            errs.append(float(np.mean((Y[t] - y_hat) ** 2)))
        losses[str(lam)] = float(np.mean(errs)) if errs else float("inf")
    chosen = min(lambdas, key=lambda lam: (losses[str(lam)], lam))
    return chosen, losses


def unfold_tensor(X: np.ndarray, mode: int) -> np.ndarray:
    I, J, K = X.shape
    if mode == 0:
        return X.reshape(I, J * K)
    if mode == 1:
        return np.transpose(X, (1, 0, 2)).reshape(J, I * K)
    return np.transpose(X, (2, 0, 1)).reshape(K, I * J)


def khatri_rao(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    cols = A.shape[1]
    out = np.zeros((A.shape[0] * B.shape[0], cols))
    for r in range(cols):
        out[:, r] = np.kron(A[:, r], B[:, r])
    return out


def cp_reconstruct(factors):
    A, B, C = factors
    I, R = A.shape
    J = B.shape[0]
    K = C.shape[0]
    out = np.zeros((I, J, K))
    for r in range(R):
        out += np.einsum("i,j,k->ijk", A[:, r], B[:, r], C[:, r])
    return out


def cp_fit(tensor: np.ndarray, rank: int, n_init=6, max_iter=100, tol=1e-6, seed=20260328):
    tensor = np.asarray(tensor, dtype=float)
    if tensor.ndim != 3 or not np.all(np.isfinite(tensor)) or 0 in tensor.shape:
        raise ValueError("tensor must be finite, three-dimensional and nonempty")
    if not isinstance(rank, (int, np.integer)) or rank < 1:
        raise ValueError("rank must be a positive integer")
    if not isinstance(n_init, (int, np.integer)) or n_init < 1:
        raise ValueError("n_init must be a positive integer")
    if not isinstance(max_iter, (int, np.integer)) or max_iter < 1:
        raise ValueError("max_iter must be a positive integer")
    if not np.isfinite(tol) or tol <= 0:
        raise ValueError("tol must be finite and strictly positive")
    rng = np.random.default_rng(seed)
    I, J, K = tensor.shape
    best = None
    best_loss = np.inf

    for init in range(n_init):
        A = rng.normal(scale=0.3, size=(I, rank))
        B = rng.normal(scale=0.3, size=(J, rank))
        C = rng.normal(scale=0.3, size=(K, rank))
        prev_loss = np.inf

        for _ in range(max_iter):
            gram_cb = (C.T @ C) * (B.T @ B)
            A = unfold_tensor(tensor, 0) @ khatri_rao(B, C) @ np.linalg.pinv(gram_cb, hermitian=True)

            gram_ca = (C.T @ C) * (A.T @ A)
            B = unfold_tensor(tensor, 1) @ khatri_rao(A, C) @ np.linalg.pinv(gram_ca, hermitian=True)

            gram_ba = (B.T @ B) * (A.T @ A)
            C = unfold_tensor(tensor, 2) @ khatri_rao(A, B) @ np.linalg.pinv(gram_ba, hermitian=True)

            for r in range(rank):
                norm_a = np.linalg.norm(A[:, r]) or 1.0
                norm_b = np.linalg.norm(B[:, r]) or 1.0
                A[:, r] /= norm_a
                B[:, r] /= norm_b
                C[:, r] *= norm_a * norm_b

            recon = cp_reconstruct((A, B, C))
            loss = float(np.linalg.norm(tensor - recon) / max(np.linalg.norm(tensor), EPS))
            if prev_loss < np.inf and abs(prev_loss - loss) / max(prev_loss, EPS) < tol:
                break
            prev_loss = loss

        if loss < best_loss:
            best_loss = loss
            best = (A.copy(), B.copy(), C.copy())

    return best, best_loss


def rolling_origin_one_step_loss_for_rank(
    beta_tensor,
    rank,
    rolling_dates,
    Y,
    W_list,
    window,
    p,
    min_training_slices,
    local_intercepts,
):
    errs = []
    fit_losses = []
    last_recon = None
    for k, t in enumerate(rolling_dates):
        prefix_length = k + 1
        if prefix_length < min_training_slices:
            continue
        # Slice k is estimated from observations strictly before Y[t], so it is available at this origin.
        factors, fit_loss = cp_fit(beta_tensor[:, :, :prefix_length], rank)
        recon = cp_reconstruct(factors)
        beta = recon[:, :, -1]
        y_hat = predict_one_step(local_intercepts[k], beta, Y[:t], W_list[:t], p)
        errs.append(float(np.mean((Y[t] - y_hat) ** 2)))
        fit_losses.append(fit_loss)
        last_recon = recon
    return (
        float(np.mean(errs)) if errs else float("inf"),
        last_recon,
        float(np.mean(fit_losses)) if fit_losses else float("inf"),
        len(errs),
    )


def select_cp_rank(
    beta_tensor,
    rolling_dates,
    dates,
    Y,
    W_list,
    window,
    p=2,
    ranks=(1, 2, 3, 4),
    local_intercepts=None,
):
    local_intercepts = np.asarray(local_intercepts, dtype=float)
    expected_intercept_shape = (beta_tensor.shape[2], beta_tensor.shape[0])
    if local_intercepts.shape != expected_intercept_shape:
        raise ValueError(
            "local_intercepts must align one fitted intercept vector with each coefficient slice; "
            f"expected {expected_intercept_shape}, got {local_intercepts.shape}"
        )
    cutoff = pd.Timestamp("2022-01-01")
    valid_idx = [idx for idx, t in enumerate(rolling_dates) if pd.Timestamp(dates[t]) < cutoff]
    valid_dates = [rolling_dates[idx] for idx in valid_idx]
    valid_tensor = beta_tensor[:, :, valid_idx]
    valid_intercepts = local_intercepts[valid_idx]

    results = {}
    fit_losses = {}
    validation_origins = {}
    min_training_slices = max(ranks)
    for rank in ranks:
        pred_loss, _, fit_loss, n_origins = rolling_origin_one_step_loss_for_rank(
            valid_tensor,
            rank,
            valid_dates,
            Y,
            W_list,
            window,
            p,
            min_training_slices,
            valid_intercepts,
        )
        results[rank] = pred_loss
        fit_losses[rank] = fit_loss
        validation_origins[rank] = n_origins

    chosen = min(ranks, key=lambda r: (results[r], r))
    factors, full_fit_loss = cp_fit(beta_tensor, chosen)
    full_recon = cp_reconstruct(factors)
    validation_metadata = {
        "method": "rolling-origin one-step-ahead CP reconstruction",
        "cutoff": str(cutoff.date()),
        "available_origins": len(valid_dates),
        "minimum_training_slices": min_training_slices,
        "evaluated_origins_by_rank": validation_origins,
        "intercept_policy": "origin-specific fitted local intercept",
    }
    return chosen, results, fit_losses, full_recon, factors, full_fit_loss, validation_metadata


def effective_companion_radius(A_list, B_list, W_use) -> float:
    n = A_list[0].shape[0]
    p = len(A_list)
    top = np.hstack([A_list[l] + B_list[l] @ W_use for l in range(p)])
    if p == 1:
        companion = top
    else:
        lower = np.hstack([np.eye(n * (p - 1)), np.zeros((n * (p - 1), n))])
        companion = np.vstack([top, lower])
    vals = np.linalg.eigvals(companion)
    return float(np.max(np.abs(vals)))


def half_life_pair(irf_pair):
    vals = np.abs(np.asarray(irf_pair, dtype=float))
    if vals.ndim != 1 or vals.size == 0 or not np.all(np.isfinite(vals)):
        raise ValueError("irf_pair must be a nonempty finite one-dimensional sequence")
    peak = np.max(vals)
    if peak <= EPS:
        return 0.0
    peak_h = int(np.argmax(vals))
    for h in range(peak_h, len(vals)):
        v = vals[h]
        if v <= 0.5 * peak:
            return float(h)
    # The reported horizon is a right-censoring boundary when no post-peak
    # half-amplitude crossing is observed.
    return float(len(vals) - 1)


def signed_ratio_or_none(numerator, denominator, tolerance=EPS):
    numerator = float(numerator)
    denominator = float(denominator)
    if not np.isfinite(numerator) or not np.isfinite(denominator):
        return None
    if abs(denominator) <= tolerance:
        return None
    return numerator / denominator


def pair_metrics_from_blocks(
    A_list,
    B_list,
    Sigma,
    W_use,
    horizon,
    unit_names,
    response_backend=None,
):
    moving_average_fn, girf_fn = response_backend or (
        moving_average_coefficients,
        girf_one,
    )
    n = Sigma.shape[0]
    B_zero = [np.zeros_like(B) for B in B_list]
    Psi_total = moving_average_fn(
        A_list,
        B_list,
        [W_use] * (horizon + len(A_list)),
        horizon,
        W_fixed=W_use,
    )
    Psi_direct = moving_average_fn(
        A_list,
        B_zero,
        [W_use] * (horizon + len(A_list)),
        horizon,
        W_fixed=W_use,
    )

    rows = []
    s_tot_sum = 0.0
    s_dir_sum = 0.0
    hl_vals = []
    for j in range(n):
        irf_tot = [girf_fn(Psi_total[h], Sigma, j) for h in range(horizon + 1)]
        irf_dir = [girf_fn(Psi_direct[h], Sigma, j) for h in range(horizon + 1)]
        for i in range(n):
            if i == j:
                continue
            s_tot = sum(abs(irf_tot[h][i]) for h in range(horizon + 1))
            s_dir = sum(abs(irf_dir[h][i]) for h in range(horizon + 1))
            s_raw = (s_tot - s_dir) / max(s_tot, EPS)
            rows.append(
                {
                    "reporter_iso": unit_names[i],
                    "partner_iso": unit_names[j],
                    "s_net_raw": s_raw,
                    "s_net_clip": float(np.clip(s_raw, 0.0, 1.0)),
                }
            )
            s_tot_sum += s_tot
            s_dir_sum += s_dir
            hl_vals.append(half_life_pair([irf_tot[h][i] for h in range(horizon + 1)]))

    g_net = (s_tot_sum - s_dir_sum) / max(s_tot_sum, EPS)
    half_life = float(np.mean(hl_vals)) if hl_vals else float("nan")
    return rows, g_net, half_life, Psi_total, Psi_direct


def estimate_rolling_local(Y, W_list, dates, p=2, window=40, lambda_ridge=1e-4):
    results = []
    tensor_blocks = []
    rolling_dates = []
    for t in range(window, len(Y)):
        Y_w = Y[t - window : t]
        W_w = W_list[t - window : t]
        c, A_list, B_list, _, Sigma, residuals = var_ols(Y_w, W_w, X_exog=None, p=p, lambda_ridge=lambda_ridge)
        beta = beta_matrix_from_lists(A_list, B_list)
        tensor_blocks.append(beta)
        rolling_dates.append(t)
        results.append(
            {
                "date": pd.Timestamp(dates[t]),
                "t_idx": t,
                "c": c,
                "A_list": A_list,
                "B_list": B_list,
                "Sigma": Sigma,
                "residuals": residuals,
                "Y_window": Y_w,
                "W_window": W_w,
                "beta": beta,
            }
        )
    beta_tensor = np.stack(tensor_blocks, axis=2)
    return results, beta_tensor, rolling_dates


def cp_empirical_paths(local_results, beta_recon, p=2):
    out = []
    for k, base in enumerate(local_results):
        beta = beta_recon[:, :, k]
        A_list, B_list = lists_from_beta(beta, p)
        W_use = safe_row_normalize(np.asarray(base["W_window"][-1], dtype=float))
        row = dict(base)
        row["beta_cp"] = beta
        row["A_list_cp"] = A_list
        row["B_list_cp"] = B_list
        row["radius_cp"] = effective_companion_radius(A_list, B_list, W_use)
        out.append(row)
    return out


def resolve_target_dates(cp_results, requested_dates):
    available_dates = [pd.Timestamp(item["date"]) for item in cp_results]
    stable_dates = [pd.Timestamp(item["date"]) for item in cp_results if float(item["radius_cp"]) < 1.0]
    search_space = stable_dates or available_dates
    resolved = {}
    for requested in requested_dates:
        target = pd.Timestamp(requested)
        if target in search_space:
            chosen = target
        else:
            chosen = min(search_space, key=lambda x: abs((x - target).days))
        resolved[pd.Timestamp(chosen)] = str(target.date())
    return resolved


def build_pair_panel(
    cp_results,
    df_tc,
    horizon,
    W_mode,
    w_label,
    unit_names,
    girf_pair,
    target_dates,
    W_fixed=None,
    response_backend=None,
):
    _, girf_fn = response_backend or (moving_average_coefficients, girf_one)
    rows = []
    aggregate_rows = []
    girf_store = {}
    receiver_idx = unit_names.index(girf_pair[0])
    shock_idx = unit_names.index(girf_pair[1])
    for item in cp_results:
        W_use = safe_row_normalize(np.asarray(W_fixed if W_fixed is not None else item["W_window"][-1], dtype=float))
        pair_rows, g_net, hl, Psi_total, Psi_direct = pair_metrics_from_blocks(
            item["A_list_cp"],
            item["B_list_cp"],
            item["Sigma"],
            W_use,
            horizon,
            unit_names,
            response_backend=response_backend,
        )
        date = item["date"]
        for row in pair_rows:
            row.update({"date": date, "H": horizon, "W_type": w_label})
            rows.append(row)
        aggregate_rows.append({"date": date, "H": horizon, "W_type": w_label, "g_net": g_net, "half_life": hl})
        if date in target_dates:
            total = [float(girf_fn(Psi_total[h], item["Sigma"], shock_idx)[receiver_idx]) for h in range(horizon + 1)]
            direct = [float(girf_fn(Psi_direct[h], item["Sigma"], shock_idx)[receiver_idx]) for h in range(horizon + 1)]
            girf_store[target_dates[date]] = {"total": total, "direct": direct, "network": [t - d for t, d in zip(total, direct)]}

    df_rows = pd.DataFrame(rows)
    df_rows["date"] = pd.to_datetime(df_rows["date"])
    df_all = df_rows.copy()
    if df_tc is not None:
        df_tc = df_tc.copy()
        df_tc["date"] = pd.to_datetime(df_tc["date"])
        df_all = df_rows.merge(df_tc, on=["date", "reporter_iso", "partner_iso"], how="left")
        df_all["TC_relief"] = pd.to_numeric(df_all.get("TC", 0), errors="coerce").fillna(0).abs() * 100
    else:
        df_all["TC_relief"] = 0.0
    df_all["qtr"] = df_all["date"].map(quarter_label)
    df_all["pair"] = df_all["reporter_iso"] + "_" + df_all["partner_iso"]
    df_all["origin_time"] = df_all["reporter_iso"] + "_" + df_all["qtr"]
    df_all["dest_time"] = df_all["partner_iso"] + "_" + df_all["qtr"]
    return df_all, pd.DataFrame(aggregate_rows), girf_store


def _unidentified_panel_result(df, reason: str) -> dict:
    return {
        "Coefficient": np.nan,
        "Std.Err": np.nan,
        "p-value": np.nan,
        "N": int(len(df)),
        "Status": "not_identified",
        "Identification": reason,
    }


def fit_panel(df, dep="s_net_clip", cluster="pair", fe="pair_time", allow_unidentified=False):
    df = df.dropna(subset=[dep, "TC_relief"]).copy()
    if df.empty:
        if allow_unidentified:
            return _unidentified_panel_result(df, "no observations remain after filtering")
        raise ValueError("panel has no observations after filtering")
    if fe == "pair_time":
        df_reg = df.set_index(["pair", "date"])
        # Build the absorbed design with rank checks disabled only for this
        # diagnostic.  The resulting matrix is inspected explicitly so a
        # stability-restricted sample with no identifying variation is
        # reported as not identified rather than estimated with a singular
        # inverse.
        mod = PanelOLS.from_formula(
            f"{dep} ~ TC_relief + EntityEffects + TimeEffects",
            data=df_reg,
            check_rank=False,
        )
        exog = mod.exog.values2d
        rank = int(np.linalg.matrix_rank(exog))
        if rank < exog.shape[1]:
            if allow_unidentified:
                return _unidentified_panel_result(
                    df,
                    "TC_relief is collinear with pair/time effects in the retained sample",
                )
            raise ValueError("exog does not have full column rank")
        try:
            if cluster == "pair":
                res = mod.fit(cov_type="clustered", cluster_entity=True)
            elif cluster == "origin_dest":
                clusters = df_reg.loc[mod.dependent.index, ["reporter_iso", "partner_iso"]]
                res = mod.fit(cov_type="clustered", clusters=clusters)
            else:
                res = mod.fit(cov_type="robust")
        except (AbsorbingEffectError, ValueError) as exc:
            if allow_unidentified:
                return _unidentified_panel_result(df, f"fixed effects absorb TC_relief: {exc}")
            raise
    else:
        absorb_df = df[["origin_time", "dest_time"]].copy()
        absorb_df["origin_time"] = absorb_df["origin_time"].astype("category")
        absorb_df["dest_time"] = absorb_df["dest_time"].astype("category")
        mod = AbsorbingLS(df[dep], df[["TC_relief"]], absorb=absorb_df)
        clusters = df["pair"] if cluster == "pair" else None
        res = mod.fit(cov_type="clustered", clusters=clusters)
    return {
        "Coefficient": float(res.params["TC_relief"]),
        "Std.Err": float(res.std_errors["TC_relief"]),
        "p-value": float(res.pvalues["TC_relief"]),
        "N": int(res.nobs),
        "Status": "identified",
        "Identification": "full rank after fixed-effect absorption",
    }


def fit_panel_stable_subsample(panel_df, dep="s_net_clip", stable_dates=None):
    """Wave B F3: complete the absorption variant for the stable-subsample check.

    Primary path mirrors the published pair_time rank-check diagnostic. When the
    retained stable sample is collinear with pair/time effects (reported as
    not_identified), the absorption variant re-fits through the two-way
    origin/destination AbsorbingLS path and returns whichever result is
    identified. The Variant field records which path produced the row.
    """
    sample = panel_df if stable_dates is None else panel_df[panel_df["date"].isin(stable_dates)]
    primary = fit_panel(sample, dep=dep, cluster="pair", fe="pair_time", allow_unidentified=True)
    primary["Variant"] = "pair_time_rank_check"
    out = primary
    attempts = {"pair_time_rank_check": dict(primary)}
    if primary.get("Status") == "not_identified":
        try:
            variant = fit_panel(sample, dep=dep, cluster="pair", fe="origin_dest")
            variant["Variant"] = "origin_dest_absorbing_two_way"
            attempts["origin_dest_absorbing_two_way"] = dict(variant)
            if variant.get("Status") == "identified":
                out = variant
        except (AbsorbingEffectError, ValueError, KeyError) as exc:
            attempts["origin_dest_absorbing_two_way"] = {
                "Status": "not_identified",
                "Identification": f"absorption variant raised: {exc}",
                "Variant": "origin_dest_absorbing_two_way",
            }
    return out, attempts


def moving_block_indices(n, rng, block_size=4):
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError("moving-block bootstrap requires at least one residual row")
    if not isinstance(block_size, (int, np.integer)) or block_size < 1:
        raise ValueError("block_size must be a positive integer")
    idx = []
    while len(idx) < n:
        start = int(rng.integers(0, max(n - block_size + 1, 1)))
        idx.extend(range(start, min(start + block_size, n)))
    return np.asarray(idx[:n], dtype=int)


def block_bootstrap_residuals(residuals, rng, block_size=4):
    residuals = np.asarray(residuals, dtype=float)
    return residuals[moving_block_indices(residuals.shape[0], rng, block_size)]


def rolling_target_residuals(Y, W_list, local_results, p, window):
    Y = np.asarray(Y, dtype=float)
    if len(local_results) != len(Y) - window:
        raise ValueError("local_results must contain one fitted path element per post-window target")
    residuals = []
    for offset, item in enumerate(local_results):
        t = window + offset
        if int(item.get("t_idx", t)) != t:
            raise ValueError("local_results are not aligned with the global target path")
        fitted = predict_one_step(item["c"], item["beta"], Y[:t], W_list[:t], p)
        residuals.append(Y[t] - fitted)
    residuals = np.asarray(residuals, dtype=float)
    return residuals - residuals.mean(axis=0, keepdims=True)


def simulate_global_bootstrap_panel(Y, W_list, local_results, rng, block_size, p, window):
    Y = np.asarray(Y, dtype=float)
    residuals = rolling_target_residuals(Y, W_list, local_results, p=p, window=window)
    sampled_indices = moving_block_indices(len(residuals), rng, block_size)
    sampled_residuals = residuals[sampled_indices]
    Y_star = np.zeros_like(Y)
    Y_star[:window] = Y[:window]
    for offset, item in enumerate(local_results):
        t = window + offset
        fitted = predict_one_step(item["c"], item["beta"], Y_star[:t], W_list[:t], p)
        Y_star[t] = fitted + sampled_residuals[offset]
    return Y_star, sampled_indices


def bootstrap_cp_pipeline(
    Y,
    W_list,
    dates,
    local_results,
    rank,
    lambda_ridge,
    df_tc,
    unit_names,
    girf_pair,
    target_dates,
    window,
    n_boot=500,
    block_size=4,
    p=2,
    W_pre=None,
    response_backend=None,
):
    rng = np.random.default_rng(20260328)
    boot_series = []
    girf_store = {label: [] for label in target_dates.values()}
    coef_draws = []

    for b in range(n_boot):
        Y_star, _ = simulate_global_bootstrap_panel(
            Y,
            W_list,
            local_results,
            rng,
            block_size=block_size,
            p=p,
            window=window,
        )
        cp_local, tensor, _ = estimate_rolling_local(
            Y_star,
            W_list,
            dates,
            p=p,
            window=window,
            lambda_ridge=lambda_ridge,
        )
        factors, _ = cp_fit(tensor, rank, n_init=4, max_iter=80, tol=1e-5, seed=20260328 + b)
        recon = cp_reconstruct(factors)
        cp_results = cp_empirical_paths(cp_local, recon, p=p)
        df_pair, df_agg, girf = build_pair_panel(
            cp_results,
            df_tc,
            horizon=8,
            W_mode="import",
            w_label="Time-Varying",
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=None,
            response_backend=response_backend,
        )
        df_fix, df_agg_fix, _ = build_pair_panel(
            cp_results,
            df_tc,
            horizon=8,
            W_mode="import",
            w_label="Fixed-Pre",
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=W_pre,
            response_backend=response_backend,
        )
        if df_tc is not None:
            reg_evolving = fit_panel(df_pair, dep="s_net_clip", cluster="pair", fe="pair_time")
            reg_frozen = fit_panel(df_fix, dep="s_net_clip", cluster="pair", fe="pair_time")
            evolving = reg_evolving["Coefficient"]
            frozen = reg_frozen["Coefficient"]
            coef_draws.append(
                {
                    "draw": b + 1,
                    "evolving_coefficient": evolving,
                    "frozen_coefficient": frozen,
                    "attenuation_difference": evolving - frozen,
                    "frozen_evolving_ratio": signed_ratio_or_none(frozen, evolving),
                }
            )
        for (_, row_tv), (_, row_fix) in zip(df_agg.iterrows(), df_agg_fix.iterrows()):
            boot_series.append(
                {
                    "b": b + 1,
                    "date": row_tv["date"],
                    "g_net": row_tv["g_net"],
                    "half_life": row_tv["half_life"],
                    "g_net_fixed": row_fix["g_net"],
                    "half_life_fixed": row_fix["half_life"],
                    "g_net_diff": row_tv["g_net"] - row_fix["g_net"],
                }
            )
        for key in girf_store:
            if key in girf:
                girf_store[key].append(girf[key])

    boot_df = pd.DataFrame(boot_series)
    agg_rows = []
    for date, grp in boot_df.groupby("date"):
        agg_rows.append(
            {
                "date": pd.Timestamp(date),
                "g_net_mean": float(grp["g_net"].mean()),
                "g_net_p025": float(grp["g_net"].quantile(0.025)),
                "g_net_p16": float(grp["g_net"].quantile(0.16)),
                "g_net_p50": float(grp["g_net"].quantile(0.5)),
                "g_net_p84": float(grp["g_net"].quantile(0.84)),
                "g_net_p975": float(grp["g_net"].quantile(0.975)),
                "g_net_fixed_mean": float(grp["g_net_fixed"].mean()),
                "g_net_fixed_p025": float(grp["g_net_fixed"].quantile(0.025)),
                "g_net_fixed_p16": float(grp["g_net_fixed"].quantile(0.16)),
                "g_net_fixed_p50": float(grp["g_net_fixed"].quantile(0.5)),
                "g_net_fixed_p84": float(grp["g_net_fixed"].quantile(0.84)),
                "g_net_fixed_p975": float(grp["g_net_fixed"].quantile(0.975)),
                "g_net_diff_mean": float(grp["g_net_diff"].mean()),
                "g_net_diff_p025": float(grp["g_net_diff"].quantile(0.025)),
                "g_net_diff_p16": float(grp["g_net_diff"].quantile(0.16)),
                "g_net_diff_p50": float(grp["g_net_diff"].quantile(0.5)),
                "g_net_diff_p84": float(grp["g_net_diff"].quantile(0.84)),
                "g_net_diff_p975": float(grp["g_net_diff"].quantile(0.975)),
                "hl_mean": float(grp["half_life"].mean()),
                "hl_p025": float(grp["half_life"].quantile(0.025)),
                "hl_p16": float(grp["half_life"].quantile(0.16)),
                "hl_p50": float(grp["half_life"].quantile(0.5)),
                "hl_p84": float(grp["half_life"].quantile(0.84)),
                "hl_p975": float(grp["half_life"].quantile(0.975)),
            }
        )
    coef_summary = None
    if coef_draws:
        coef_draw_df = pd.DataFrame(coef_draws)

        def summarize_quantity(name: str) -> dict[str, float | str]:
            vals = coef_draw_df[name].dropna().astype(float)
            if vals.empty:
                return {
                    "quantity": name,
                    "mean": None,
                    "p025": None,
                    "p16": None,
                    "p50": None,
                    "p84": None,
                    "p975": None,
                }
            return {
                "quantity": name,
                "mean": float(vals.mean()),
                "p025": float(vals.quantile(0.025)),
                "p16": float(vals.quantile(0.16)),
                "p50": float(vals.quantile(0.5)),
                "p84": float(vals.quantile(0.84)),
                "p975": float(vals.quantile(0.975)),
            }

        coef_summary = {
            "bootstrap_type": "global moving-block residual bootstrap with full rolling and CP re-estimation",
            "bootstrap_replications": int(n_boot),
            "block_size": int(block_size),
            "quantities": {
                "evolving_coefficient": summarize_quantity("evolving_coefficient"),
                "frozen_coefficient": summarize_quantity("frozen_coefficient"),
                "attenuation_difference": summarize_quantity("attenuation_difference"),
                "frozen_evolving_ratio": summarize_quantity("frozen_evolving_ratio"),
            },
        }
    return pd.DataFrame(agg_rows), girf_store, coef_summary, pd.DataFrame(coef_draws)


def bootstrap_block_sensitivity(
    Y,
    W_list,
    dates,
    local_results,
    rank,
    lambda_ridge,
    df_tc,
    unit_names,
    girf_pair,
    target_dates,
    window,
    p,
    W_pre,
    block_sizes=(4, 8, 12),
    n_boot=120,
    response_backend=None,
):
    rows = []
    for block_size in block_sizes:
        boot_df, _, coef_summary, _ = bootstrap_cp_pipeline(
            Y,
            W_list,
            dates,
            local_results,
            rank,
            lambda_ridge,
            df_tc,
            unit_names,
            girf_pair,
            target_dates,
            window=window,
            n_boot=n_boot,
            block_size=block_size,
            p=p,
            W_pre=W_pre,
            response_backend=response_backend,
        )
        coef_quantities = (coef_summary or {}).get("quantities", {})
        evolving = coef_quantities.get("evolving_coefficient", {})
        rows.append(
            {
                "block_size": block_size,
                "g_net_diff_p50_mean": float(boot_df["g_net_diff_p50"].mean()),
                "g_net_diff_p025_mean": float(boot_df["g_net_diff_p025"].mean()),
                "g_net_diff_p975_mean": float(boot_df["g_net_diff_p975"].mean()),
                "coef_p50": None if not evolving else float(evolving["p50"]),
                "coef_p025": None if not evolving else float(evolving["p025"]),
                "coef_p975": None if not evolving else float(evolving["p975"]),
                "bootstrap_replications": int(n_boot),
            }
        )
    return pd.DataFrame(rows)


def _rss_segment(y, start, end):
    seg = y[start:end]
    if len(seg) <= 1:
        return 0.0
    mu = float(np.mean(seg))
    return float(np.sum((seg - mu) ** 2))


def _chow_f_stat(y, cut):
    n = len(y)
    if cut <= 1 or cut >= n - 1:
        return np.nan
    rss_pooled = _rss_segment(y, 0, n)
    rss_split = _rss_segment(y, 0, cut) + _rss_segment(y, cut, n)
    k = 1
    denom_df = n - 2 * k
    if denom_df <= 0 or rss_split <= 0:
        return np.nan
    return float(((rss_pooled - rss_split) / k) / (rss_split / denom_df))


def _best_breaks_dp(y, max_breaks=3, min_size=8):
    n = len(y)
    best = {"cuts": [], "bic": np.inf, "rss": np.inf}

    def recurse(start, remaining, cuts):
        nonlocal best
        if remaining == 0:
            all_cuts = sorted(cuts)
            segs = [0] + all_cuts + [n]
            rss = 0.0
            for a, b in zip(segs[:-1], segs[1:]):
                rss += _rss_segment(y, a, b)
            k = len(all_cuts) + 1
            bic = n * np.log(max(rss / max(n, 1), EPS)) + k * np.log(max(n, 2))
            if bic < best["bic"]:
                best = {"cuts": all_cuts, "bic": bic, "rss": rss}
            return
        for cut in range(start + min_size, n - min_size * remaining + 1):
            recurse(cut, remaining - 1, cuts + [cut])

    recurse(0, 0, [])
    for b in range(1, max_breaks + 1):
        recurse(0, b, [])
    return best["cuts"], best["bic"], best["rss"]


def structural_break_table(agg_df, pair_df):
    series_map = {"Aggregate index, H=8": agg_df.set_index("date")["g_net"].dropna()}
    for rep, par in [("CHN", "JPN"), ("CHN", "KOR"), ("CHN", "AUS")]:
        s = pair_df[(pair_df["reporter_iso"] == rep) & (pair_df["partner_iso"] == par)].set_index("date")["s_net_clip"].dropna()
        if len(s) >= 20:
            series_map[f"Bounded pair contribution, {rep} <- {par}"] = s
    rows = []
    for name, s in series_map.items():
        y = s.values.astype(float)
        dates = list(s.index)
        cuts, bic, rss = _best_breaks_dp(y, max_breaks=3, min_size=8)
        f_stats = [_chow_f_stat(y, c) for c in cuts]
        break_dates = [quarter_label(pd.Timestamp(dates[c])) for c in cuts]
        ci_l = [quarter_label(pd.Timestamp(dates[max(c - 1, 0)])) for c in cuts]
        ci_u = [quarter_label(pd.Timestamp(dates[min(c + 1, len(dates) - 1)])) for c in cuts]
        rows.append(
            {
                "Series": name,
                "break_dates": "; ".join(break_dates) if break_dates else "None",
                "break_CI_approx": "; ".join([f"[{l},{u}]" for l, u in zip(ci_l, ci_u)]) if cuts else "None",
                "max_Chow_F": float(np.nanmax(f_stats)) if f_stats else np.nan,
                "BIC": float(bic),
                "RSS": float(rss),
            }
        )
    return pd.DataFrame(rows)


def coefficient_plot(table_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    plot_df = table_df.copy()
    plot_df["Specification"] = (
        plot_df["Specification"].astype(str)
        .str.replace("Import-based W_t", "Baseline import topology", regex=False)
        .str.replace("Export-based W_t", "Export-based topology", regex=False)
        .str.replace("Symmetric W_t", "Symmetric topology", regex=False)
        .str.replace("Eight-quarter W_t", "Eight-quarter import topology", regex=False)
        .str.replace("Evolving topology W_t", "Evolving topology", regex=False)
        .str.replace("Frozen topology W_pre", "Frozen benchmark topology", regex=False)
        .str.replace("Unclipped s_net_raw", "Unbounded raw pair contribution", regex=False)
        .str.replace("1-99 trimmed s_net_raw", "1st-99th percentile trimmed raw pair contribution", regex=False)
        .str.replace("s_net_clip", "bounded pair contribution", regex=False)
        .str.replace("s_net_raw", "raw pair contribution", regex=False)
        .str.replace("g_net", "aggregate network index", regex=False)
    )
    plot_df["coef"] = pd.to_numeric(plot_df["Coefficient"], errors="coerce")
    plot_df["se"] = pd.to_numeric(plot_df["Std.Err"], errors="coerce")
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    y = np.arange(len(plot_df))[::-1]
    ax.axvline(0, color="black", lw=1, alpha=0.7)
    ax.errorbar(plot_df["coef"], y, xerr=1.96 * plot_df["se"], fmt="o", color="#1f77b4", ecolor="#6baed6", capsize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Specification"])
    ax.set_xlabel("Coefficient on tariff relief")
    ax.set_title("RCEP benchmark and inference panel")
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def aggregate_plot(agg_df, boot_df, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(2, 1, figsize=(8.8, 6.8), sharex=True)
    axes[0].plot(agg_df["date"], agg_df["g_net"], color="#1f77b4", lw=2)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p16"], boot_df["g_net_p84"], color="#9ecae1", alpha=0.5)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p025"], boot_df["g_net_p975"], color="#c6dbef", alpha=0.35)
    axes[0].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[0].set_ylabel("Aggregate network-propagation index")
    axes[0].set_title("Aggregate propagation index with bootstrap intervals")

    axes[1].plot(agg_df["date"], agg_df["half_life"], color="#dd8452", lw=2)
    axes[1].fill_between(boot_df["date"], boot_df["hl_p16"], boot_df["hl_p84"], color="#fdd0a2", alpha=0.5)
    axes[1].fill_between(boot_df["date"], boot_df["hl_p025"], boot_df["hl_p975"], color="#fee6ce", alpha=0.35)
    axes[1].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[1].set_ylabel("Half-life")
    axes[1].set_xlabel("Date")
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def girf_plot(girf_point, girf_boot, out_png: Path, out_pdf: Path):
    date_keys = sorted(girf_point.keys())
    fig, axes = plt.subplots(1, len(date_keys), figsize=(4.7 * len(date_keys), 3.75), sharey=True)
    if len(date_keys) == 1:
        axes = [axes]
    for ax, date_key in zip(axes, date_keys):
        draws = girf_boot.get(date_key, [])
        horizon = list(range(len(girf_point[date_key]["total"])))
        for label, color in [("total", "#1f77b4"), ("direct", "#ff7f0e"), ("network", "#2ca02c")]:
            arr = np.array([d[label] for d in draws], dtype=float)
            if arr.size:
                p16 = np.quantile(arr, 0.16, axis=0)
                p84 = np.quantile(arr, 0.84, axis=0)
                p025 = np.quantile(arr, 0.025, axis=0)
                p975 = np.quantile(arr, 0.975, axis=0)
                ax.fill_between(horizon, p025, p975, color=color, alpha=0.12)
                ax.fill_between(horizon, p16, p84, color=color, alpha=0.25)
            ax.plot(horizon, girf_point[date_key][label], color=color, lw=2, label=label if date_key == date_keys[0] else None)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(date_key, fontsize=9)
        ax.set_xlabel("Horizon")
        ax.tick_params(labelsize=8)
    axes[0].set_ylabel("Response")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def topology_difference_plot(agg_tv, agg_fix, boot_df, out_png: Path, out_pdf: Path):
    merged = agg_tv[["date", "g_net"]].merge(agg_fix[["date", "g_net"]], on="date", suffixes=("_tv", "_fix"))
    merged["diff"] = merged["g_net_tv"] - merged["g_net_fix"]
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.fill_between(boot_df["date"], boot_df["g_net_diff_p025"], boot_df["g_net_diff_p975"], color="#d9e8ef", alpha=0.62, linewidth=0)
    ax.fill_between(boot_df["date"], boot_df["g_net_diff_p16"], boot_df["g_net_diff_p84"], color="#aac8d6", alpha=0.58, linewidth=0)
    ax.plot(merged["date"], merged["diff"], label="Point estimate", color="#111111", lw=1.65)
    entry = pd.Timestamp("2022-01-01")
    ax.axvline(entry, color="#111111", ls="--", lw=0.9)
    ax.axhline(0, color="#111111", lw=0.8)
    ax.set_ylabel("Observed-minus-frozen aggregate-index difference")
    ax.set_xlabel("Date")
    ax.text(
        0.02,
        0.94,
        "Evolving minus frozen topology",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )
    ax.text(entry, ax.get_ylim()[1], "RCEP entry", ha="left", va="top", fontsize=7, rotation=90)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#eeeeee", lw=0.55)
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def top_exposure_propagation_perturbations(cp_results, horizon, unit_names, response_backend=None):
    rows = []
    for item in cp_results:
        W_base = safe_row_normalize(np.asarray(item["W_window"][-1], dtype=float))
        hub, W_perturbed = top_import_exposure_perturbation(W_base, scale_factor=0.5)
        _, g_base, hl_base, _, _ = pair_metrics_from_blocks(
            item["A_list_cp"],
            item["B_list_cp"],
            item["Sigma"],
            W_base,
            horizon,
            unit_names,
            response_backend=response_backend,
        )
        _, g_perturbed, hl_perturbed, _, _ = pair_metrics_from_blocks(
            item["A_list_cp"],
            item["B_list_cp"],
            item["Sigma"],
            W_perturbed,
            horizon,
            unit_names,
            response_backend=response_backend,
        )
        rows.append(
            {
                "date": item["date"],
                "perturbation": "attenuate_top_import_exposure_incoming",
                "target_unit": unit_names[hub],
                "g_net_base": g_base,
                "g_net_perturbed": g_perturbed,
                "g_net_delta": g_perturbed - g_base,
                "half_life_base": hl_base,
                "half_life_perturbed": hl_perturbed,
                "half_life_delta": hl_perturbed - hl_base,
            }
        )
    return pd.DataFrame(rows)


def top_exposure_perturbation_summary(perturb_df):
    grp = perturb_df.copy()
    return pd.DataFrame(
        [
            {
                "perturbation": "attenuate_top_import_exposure_incoming",
                "n": int(len(grp)),
                "mean_g_net_base": float(grp["g_net_base"].mean()),
                "mean_g_net_perturbed": float(grp["g_net_perturbed"].mean()),
                "mean_g_net_delta": float(grp["g_net_delta"].mean()),
                "median_g_net_delta": float(grp["g_net_delta"].median()),
                "mean_half_life_delta": float(grp["half_life_delta"].mean()),
                "share_delta_negative": float((grp["g_net_delta"] < 0).mean()),
                "dominant_target_unit": grp["target_unit"].mode().iloc[0] if len(grp) else "",
            }
        ]
    )


def top_exposure_perturbation_plot(perturb_df, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(2, 1, figsize=(8.8, 6.2), sharex=True)
    axes[0].plot(perturb_df["date"], perturb_df["g_net_base"], color="#1f77b4", lw=2, label="Observed topology")
    axes[0].plot(perturb_df["date"], perturb_df["g_net_perturbed"], color="#d62728", lw=2, label="Top-exposure attenuation")
    axes[0].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[0].set_ylabel("Aggregate network-propagation index")
    axes[0].set_title("Top-exposure topology perturbation")
    axes[0].legend(frameon=False)

    axes[1].plot(perturb_df["date"], perturb_df["g_net_delta"], color="#4b5563", lw=2)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[1].set_ylabel("Perturbed minus observed")
    axes[1].set_xlabel("Date")
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def clipping_summary(panel_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, grp in panel_df.groupby("variant_key"):
        raw_p25 = float(grp["s_net_raw"].quantile(0.25))
        raw_p50 = float(grp["s_net_raw"].quantile(0.50))
        raw_p75 = float(grp["s_net_raw"].quantile(0.75))
        raw_q01 = float(grp["s_net_raw"].quantile(0.01))
        raw_q99 = float(grp["s_net_raw"].quantile(0.99))
        rows.append(
            {
                "variant_key": key,
                "n_obs": int(len(grp)),
                "clip_at_0_pct": float((grp["s_net_clip"] <= EPS).mean() * 100),
                "clip_at_1_pct": float((grp["s_net_clip"] >= 1 - EPS).mean() * 100),
                "raw_mean": float(grp["s_net_raw"].mean()),
                "raw_p25": raw_p25,
                "raw_p50": raw_p50,
                "raw_p75": raw_p75,
                "raw_median": raw_p50,
                "raw_iqr": raw_p75 - raw_p25,
                "raw_min": float(grp["s_net_raw"].min()),
                "raw_max": float(grp["s_net_raw"].max()),
                "raw_q01": raw_q01,
                "raw_q99": raw_q99,
            }
        )
    return pd.DataFrame(rows)


def clipping_histogram(panel_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    baseline = panel_df[panel_df["variant_key"] == "baseline_import"].copy()
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    ax.hist(baseline["s_net_raw"], bins=40, color="#1f77b4", alpha=0.75, edgecolor="white")
    ax.axvline(0, color="black", lw=1, ls="--")
    ax.axvline(1, color="black", lw=1, ls=":")
    ax.set_title("Distribution of the raw pair-level network-contribution metric")
    ax.set_xlabel("Raw pair contribution")
    ax.set_ylabel("Count")
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def stability_summary(cp_results: list[dict], out_csv: Path):
    rows = []
    for item in cp_results:
        rows.append(
            {
                "date": pd.Timestamp(item["date"]),
                "radius_cp": float(item["radius_cp"]),
                "unstable": int(item["radius_cp"] >= 1.0),
            }
        )
    df = pd.DataFrame(rows)
    write_output_csv(df, out_csv)
    return df


def stability_plots(stability_df: pd.DataFrame, out_prefix: Path):
    fig, axes = plt.subplots(2, 1, figsize=(8.3, 6.6))
    axes[0].plot(stability_df["date"], stability_df["radius_cp"], color="#7c3aed", lw=2)
    axes[0].axhline(1.0, color="black", lw=1, ls="--")
    axes[0].set_ylabel("Spectral radius")
    axes[0].set_title("Date-by-date stability monitor")
    axes[1].hist(stability_df["radius_cp"], bins=24, color="#c4b5fd", edgecolor="white")
    axes[1].axvline(1.0, color="black", lw=1, ls="--")
    axes[1].set_xlabel("Spectral radius")
    axes[1].set_ylabel("Count")
    fig.tight_layout()
    save_output_figure(fig, out_prefix.with_suffix(".png"), dpi=900)
    save_output_figure(fig, out_prefix.with_suffix(".pdf"))
    plt.close(fig)


def block_sensitivity_plot(block_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(2, 1, figsize=(7.8, 6.0), sharex=True)
    axes[0].plot(block_df["block_size"], block_df["g_net_diff_p50_mean"], marker="o", color="#1f77b4", lw=2)
    axes[0].fill_between(block_df["block_size"], block_df["g_net_diff_p025_mean"], block_df["g_net_diff_p975_mean"], color="#c6dbef", alpha=0.35)
    axes[0].set_ylabel("Aggregate difference")
    axes[0].set_title("Block-length sensitivity for the topology-difference index")
    if block_df["coef_p50"].notna().any():
        axes[1].plot(block_df["block_size"], block_df["coef_p50"], marker="o", color="#dd8452", lw=2)
        axes[1].fill_between(block_df["block_size"], block_df["coef_p025"], block_df["coef_p975"], color="#fdd0a2", alpha=0.35)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_xlabel("Bootstrap block length")
    axes[1].set_ylabel("Coefficient")
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def trimmed_raw_panel(panel_df: pd.DataFrame, lower_q=0.01, upper_q=0.99):
    bounds = panel_df["s_net_raw"].quantile([lower_q, upper_q])
    lower = float(bounds.iloc[0])
    upper = float(bounds.iloc[1])
    trimmed = panel_df[(panel_df["s_net_raw"] >= lower) & (panel_df["s_net_raw"] <= upper)].copy()
    return trimmed, lower, upper


def aggregate_topology_summary(agg_df: pd.DataFrame, agg_fix_df: pd.DataFrame, allowed_dates=None):
    merged = agg_df[["date", "g_net"]].merge(agg_fix_df[["date", "g_net"]], on="date", suffixes=("_tv", "_fix"))
    if allowed_dates is not None:
        merged = merged[merged["date"].isin(allowed_dates)].copy()
    diff = merged["g_net_tv"] - merged["g_net_fix"]
    return [
        {"Statistic": "Aggregate propagation index", "Value": float(merged["g_net_tv"].mean()), "N": int(len(merged))},
        {"Statistic": "Frozen-topology aggregate index", "Value": float(merged["g_net_fix"].mean()), "N": int(len(merged))},
        {"Statistic": "Evolving-minus-frozen aggregate difference", "Value": float(diff.mean()), "N": int(len(merged))},
    ]


def stability_exclusion_summary(panel_df: pd.DataFrame, agg_df: pd.DataFrame, agg_fix_df: pd.DataFrame, stability_df: pd.DataFrame, dep="s_net_clip") -> pd.DataFrame:
    stable_dates = set(pd.to_datetime(stability_df.loc[stability_df["unstable"] == 0, "date"]))
    reg_full = fit_panel(panel_df, dep=dep, cluster="pair", fe="pair_time")
    reg_full["Variant"] = "pair_time_rank_check"
    reg_stable, stable_attempts = fit_panel_stable_subsample(
        panel_df,
        dep=dep,
        stable_dates=stable_dates,
    )
    rows = [
        {"Statistic": "Pair-level coefficient", "Sample": "Full sample", "Value": reg_full["Coefficient"], "Std.Err": reg_full["Std.Err"], "p-value": reg_full["p-value"], "N": reg_full["N"], "Status": reg_full["Status"], "Identification": reg_full["Identification"], "Variant": reg_full["Variant"]},
        {"Statistic": "Pair-level coefficient", "Sample": "Stable dates only", "Value": reg_stable["Coefficient"], "Std.Err": reg_stable["Std.Err"], "p-value": reg_stable["p-value"], "N": reg_stable["N"], "Status": reg_stable["Status"], "Identification": reg_stable["Identification"], "Variant": reg_stable["Variant"]},
    ]
    for item in aggregate_topology_summary(agg_df, agg_fix_df):
        rows.append({**item, "Sample": "Full sample", "Std.Err": np.nan, "p-value": np.nan, "Status": "identified", "Identification": "descriptive aggregate"})
    for item in aggregate_topology_summary(agg_df, agg_fix_df, stable_dates):
        rows.append({**item, "Sample": "Stable dates only", "Std.Err": np.nan, "p-value": np.nan, "Status": "identified", "Identification": "descriptive aggregate"})
    result = pd.DataFrame(rows)
    result.attrs["stable_attempts"] = stable_attempts
    return result


def project_cp_results(cp_results: list[dict], target_radius=0.98, max_iter=8):
    projected = []
    for item in cp_results:
        row = dict(item)
        A_list = [np.asarray(A, dtype=float).copy() for A in item["A_list_cp"]]
        B_list = [np.asarray(B, dtype=float).copy() for B in item["B_list_cp"]]
        W_use = safe_row_normalize(np.asarray(item["W_window"][-1], dtype=float))
        radius = effective_companion_radius(A_list, B_list, W_use)
        total_scale = 1.0
        n_iter = 0
        while radius >= 1.0 and n_iter < max_iter:
            scale_factor = min(1.0, target_radius / max(radius, EPS))
            A_list = [A * scale_factor for A in A_list]
            B_list = [B * scale_factor for B in B_list]
            total_scale *= scale_factor
            radius = effective_companion_radius(A_list, B_list, W_use)
            n_iter += 1
        row["A_list_cp"] = A_list
        row["B_list_cp"] = B_list
        row["beta_cp"] = beta_matrix_from_lists(A_list, B_list)
        row["radius_cp_original"] = float(item["radius_cp"])
        row["radius_cp"] = float(radius)
        row["projection_scale"] = float(total_scale)
        row["projection_iterations"] = int(n_iter)
        projected.append(row)
    return projected


def stability_projected_summary(
    panel_df: pd.DataFrame,
    agg_df: pd.DataFrame,
    agg_fix_df: pd.DataFrame,
    projected_panel_df: pd.DataFrame,
    projected_agg_df: pd.DataFrame,
    projected_agg_fix_df: pd.DataFrame,
    dep="s_net_clip",
) -> pd.DataFrame:
    reg_full = fit_panel(panel_df, dep=dep, cluster="pair", fe="pair_time")
    reg_projected = fit_panel(projected_panel_df, dep=dep, cluster="pair", fe="pair_time")
    rows = [
        {"Statistic": "Pair-level coefficient", "Sample": "Original full sample", "Value": reg_full["Coefficient"], "Std.Err": reg_full["Std.Err"], "p-value": reg_full["p-value"], "N": reg_full["N"]},
        {"Statistic": "Pair-level coefficient", "Sample": "Stability-projected path", "Value": reg_projected["Coefficient"], "Std.Err": reg_projected["Std.Err"], "p-value": reg_projected["p-value"], "N": reg_projected["N"]},
    ]
    for item in aggregate_topology_summary(agg_df, agg_fix_df):
        rows.append({**item, "Sample": "Original full sample", "Std.Err": np.nan, "p-value": np.nan})
    for item in aggregate_topology_summary(projected_agg_df, projected_agg_fix_df):
        rows.append({**item, "Sample": "Stability-projected path", "Std.Err": np.nan, "p-value": np.nan})
    return pd.DataFrame(rows)


def stability_sensitivity_plot(exclusion_df: pd.DataFrame, projected_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.65))

    coef_rows = [
        exclusion_df[(exclusion_df["Statistic"] == "Pair-level coefficient") & (exclusion_df["Sample"] == "Full sample")].iloc[0],
        exclusion_df[(exclusion_df["Statistic"] == "Pair-level coefficient") & (exclusion_df["Sample"] == "Stable dates only")].iloc[0],
        projected_df[(projected_df["Statistic"] == "Pair-level coefficient") & (projected_df["Sample"] == "Stability-projected path")].iloc[0],
    ]
    coef_labels = ["Full\nsample", "Stable dates\nonly", "Stability-projected\npath"]
    y = np.arange(len(coef_rows))[::-1]
    axes[0].axvline(0, color="black", lw=0.8)
    identified = [
        (idx, float(row["Value"]), 1.96 * float(row["Std.Err"]))
        for idx, row in enumerate(coef_rows)
        if row.get("Status", "identified") == "identified"
        and np.isfinite(float(row["Value"]))
        and np.isfinite(float(row["Std.Err"]))
    ]
    if identified:
        axes[0].errorbar(
            [value for _, value, _ in identified],
            [y[idx] for idx, _, _ in identified],
            xerr=[error for _, _, error in identified],
            fmt="o",
            color="#1f77b4",
            ecolor="#93c5fd",
            capsize=3,
        )
    for idx, row in enumerate(coef_rows):
        if row.get("Status", "identified") != "identified":
            axes[0].text(0.0, y[idx], "not identified", ha="left", va="center", color="#b91c1c", fontsize=8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(coef_labels)
    axes[0].set_xlabel("Pair-level coefficient")
    axes[0].set_title("a  Pair-level coefficient sensitivity", loc="left", fontsize=9, fontweight="bold")
    axes[0].tick_params(axis="both", labelsize=8)

    diff_rows = [
        exclusion_df[(exclusion_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (exclusion_df["Sample"] == "Full sample")].iloc[0],
        exclusion_df[(exclusion_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (exclusion_df["Sample"] == "Stable dates only")].iloc[0],
        projected_df[(projected_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (projected_df["Sample"] == "Stability-projected path")].iloc[0],
    ]
    diff_vals = [float(row["Value"]) for row in diff_rows]
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].plot(coef_labels, diff_vals, marker="o", color="#15803d", lw=2)
    axes[1].set_ylabel("Mean evolving-minus-frozen difference")
    axes[1].set_title("b  Topology-difference sensitivity", loc="left", fontsize=9, fontweight="bold")
    axes[1].tick_params(axis="both", labelsize=8)

    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def mobility_illustration_plot(agg_df: pd.DataFrame, boot_df: pd.DataFrame, girf_point: dict, out_png: Path, out_pdf: Path):
    latest_label = sorted(girf_point.keys())[-1]
    horizon = list(range(len(girf_point[latest_label]["total"])))
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 4.2))

    axes[0].plot(agg_df["date"], agg_df["g_net"], color="#1f77b4", lw=2)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p16"], boot_df["g_net_p84"], color="#9ecae1", alpha=0.45)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p025"], boot_df["g_net_p975"], color="#c6dbef", alpha=0.28)
    axes[0].set_title("a. Aggregate propagation index", loc="left", fontsize=11, fontweight="bold")

    axes[1].plot(boot_df["date"], boot_df["g_net_diff_p50"], color="#15803d", lw=2)
    axes[1].fill_between(boot_df["date"], boot_df["g_net_diff_p16"], boot_df["g_net_diff_p84"], color="#bbf7d0", alpha=0.45)
    axes[1].fill_between(boot_df["date"], boot_df["g_net_diff_p025"], boot_df["g_net_diff_p975"], color="#dcfce7", alpha=0.28)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_title("b. Evolving minus frozen topology", loc="left", fontsize=11, fontweight="bold")

    for label, color in [("total", "#1f77b4"), ("direct", "#ff7f0e"), ("network", "#2ca02c")]:
        axes[2].plot(horizon, girf_point[latest_label][label], lw=2, color=color, label=label.capitalize())
    axes[2].axhline(0, color="black", lw=0.8)
    axes[2].set_title(f"c. Representative GIRF ({latest_label})", loc="left", fontsize=11, fontweight="bold")
    axes[2].legend(frameon=False, fontsize=8)

    for ax in axes:
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    save_output_figure(fig, out_png, dpi=900)
    save_output_figure(fig, out_pdf)
    plt.close(fig)


def validate_run_args(args):
    if args.dataset not in {"rcep", "nyc_taxi"}:
        raise ValueError("dataset must be rcep or nyc_taxi")
    integer_contracts = {
        "p": args.p,
        "window": args.window,
        "n_boot": args.n_boot,
        "block_size": args.block_size,
        "cp_inits": args.cp_inits,
        "cp_max_iter": args.cp_max_iter,
    }
    for name, value in integer_contracts.items():
        if not isinstance(value, (int, np.integer)) or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if args.window <= args.p:
        raise ValueError("window must be greater than the lag order")
    if not np.isfinite(args.cp_tol) or args.cp_tol <= 0:
        raise ValueError("cp_tol must be finite and strictly positive")


def _is_sha256(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


def _resolved_rcep_input_files(repo: Path) -> dict[str, str]:
    repo = Path(repo).resolve()
    local_root = repo / "data"
    fallback_root = repo.parent / "data_acquisition" / "data"
    identities = {}
    for name in RCEP_REQUIRED_INPUT_FILENAMES:
        local_path = local_root / name
        selected_path = local_path if local_path.is_file() else fallback_root / name
        if selected_path.is_symlink() or not selected_path.is_file():
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} Required RCEP input is unavailable: {name}.")
        resolved_path = selected_path.resolve()
        identities[str(resolved_path)] = _sha256(resolved_path)
    return identities


def _validated_scientific_execution_authorization(args):
    authorization_path_value = getattr(args, "authorization", None)
    approved_sha256 = getattr(args, "authorization_sha256", None)
    requested_output_root = getattr(args, "output_root", None)
    if not authorization_path_value or not approved_sha256 or not requested_output_root:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The scientific execution authorization is absent.")
    if not _is_sha256(approved_sha256):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The approved SHA-256 is invalid.")

    authorization_path = Path(authorization_path_value).expanduser()
    try:
        authorization_snapshot = read_authorized_input_snapshot(authorization_path, approved_sha256)
    except RuntimeError as exc:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} {exc}") from exc
    try:
        authorization = json.loads(authorization_snapshot.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorization file is unreadable.") from exc

    expected_keys = {
        "schema_version",
        "decision_id",
        "decision",
        "scientific_execution_authorized",
        "authorized_by",
        "authorized_at",
        "action",
        "dataset",
        "argv",
        "implementation_files",
        "input_identity",
        "output_root",
        "overwrite",
        "r006e_outcome_authorized",
        "r006f_outcome_authorized",
        "downstream_builds_authorized",
        "post_run_controls",
    }
    if not isinstance(authorization, dict) or set(authorization) != expected_keys:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorization schema is invalid.")
    if authorization.get("schema_version") != SCIENTIFIC_AUTHORIZATION_SCHEMA_VERSION:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorization schema version is invalid.")
    if authorization.get("decision") != "AUTHORIZED" or authorization.get("scientific_execution_authorized") is not True:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} Scientific execution is not authorized.")
    decision_id = authorization.get("decision_id")
    if (
        not isinstance(decision_id, str)
        or not decision_id
        or len(decision_id) > 96
        or any(not (char.isalnum() or char in "-_") for char in decision_id)
    ):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The decision ID is invalid.")
    if not all(isinstance(authorization.get(key), str) and authorization[key].strip() for key in ("authorized_by", "authorized_at")):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorizer identity or time is absent.")
    if authorization.get("action") != "run_cp_empirical_pipeline" or authorization.get("dataset") != args.dataset:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorized action or dataset does not match.")

    authorized_argv = authorization.get("argv")
    expected_argv = {name: getattr(args, name) for name in SCIENTIFIC_AUTHORIZATION_ARGV}
    if not isinstance(authorized_argv, dict) or set(authorized_argv) != set(SCIENTIFIC_AUTHORIZATION_ARGV):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorized argv schema is invalid.")
    if authorized_argv != expected_argv:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorized argv does not match the requested run.")

    implementation_files = authorization.get("implementation_files")
    if not isinstance(implementation_files, dict) or set(implementation_files) != SCIENTIFIC_AUTHORIZATION_IMPLEMENTATION_FILES:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The implementation closure is invalid.")
    for relative_path, expected_hash in implementation_files.items():
        source = ROOT / relative_path
        if not _is_sha256(expected_hash) or not source.is_file() or source.is_symlink() or _sha256(source) != expected_hash.lower():
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} Implementation identity mismatch: {relative_path}.")

    input_identity = authorization.get("input_identity")
    input_keys = {
        "rcep_helper_repo",
        "rcep_helper_manifest_sha256",
        "rcep_input_files",
        "nyc_dataset_dir",
        "nyc_upstream_commit",
    }
    if not isinstance(input_identity, dict) or set(input_identity) != input_keys:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The input-identity schema is invalid.")
    authorized_rcep_inputs = input_identity.get("rcep_input_files")
    if not isinstance(authorized_rcep_inputs, dict):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP input-file declaration is invalid.")

    if args.dataset == "rcep":
        authorized_helper = input_identity.get("rcep_helper_repo")
        authorized_manifest_hash = input_identity.get("rcep_helper_manifest_sha256")
        if not helper_repo or not isinstance(authorized_helper, str):
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP helper path is not bound.")
        supplied_helper = Path(helper_repo).expanduser()
        if supplied_helper.is_symlink() or not supplied_helper.is_dir() or supplied_helper.resolve() != Path(authorized_helper).expanduser().resolve():
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP helper path does not match.")
        trust_manifest_path = Path(RCEP_HELPER_TRUST_MANIFEST)
        try:
            read_authorized_input_snapshot(trust_manifest_path, authorized_manifest_hash)
        except RuntimeError as exc:
            raise RuntimeError(
                f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP helper manifest identity does not match."
            ) from exc
        try:
            authorized_rcep_paths = {
                Path(path).expanduser(): digest for path, digest in authorized_rcep_inputs.items()
            }
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP input identity is invalid.") from exc
        if (
            {path.name for path in authorized_rcep_paths} != set(RCEP_REQUIRED_INPUT_FILENAMES)
            or len(authorized_rcep_paths) != len(RCEP_REQUIRED_INPUT_FILENAMES)
            or any(
                not path.is_absolute() or path != path.resolve() or not _is_sha256(digest)
                for path, digest in authorized_rcep_paths.items()
            )
        ):
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP input identity is invalid.")
        if input_identity.get("nyc_dataset_dir") is not None or input_identity.get("nyc_upstream_commit") is not None:
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP authorization contains an unrelated NYC binding.")
    else:
        supplied_nyc_path = os.environ.get("NATCS_NYC_TAXI_DATASET_DIR")
        authorized_nyc_path = input_identity.get("nyc_dataset_dir")
        if not supplied_nyc_path or not isinstance(authorized_nyc_path, str):
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC source path is not bound.")
        supplied_nyc = Path(supplied_nyc_path).expanduser()
        if supplied_nyc.is_symlink() or not supplied_nyc.is_dir() or supplied_nyc.resolve() != Path(authorized_nyc_path).expanduser().resolve():
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC source path does not match.")
        if input_identity.get("nyc_upstream_commit") != NYC_TAXI_UPSTREAM_COMMIT:
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC source commit does not match.")
        if (
            input_identity.get("rcep_helper_repo") is not None
            or input_identity.get("rcep_helper_manifest_sha256") is not None
            or authorized_rcep_inputs
        ):
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The NYC authorization contains an unrelated RCEP binding.")

    post_run_controls = {
        "quarantine_outputs": True,
        "freeze_inventory_sha256_before_value_review": True,
        "independent_claim_audit_required": True,
        "manuscript_promotion_authorized": False,
    }
    if authorization.get("post_run_controls") != post_run_controls:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The post-run controls are invalid.")
    if (
        authorization.get("overwrite") != "deny"
        or authorization.get("r006e_outcome_authorized") is not False
        or authorization.get("r006f_outcome_authorized") is not False
        or authorization.get("downstream_builds_authorized") is not False
    ):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The execution boundary is invalid.")

    authorized_output_value = authorization.get("output_root")
    if not isinstance(authorized_output_value, str) or authorized_output_value != str(requested_output_root):
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorized output root does not match.")
    raw_output_root = Path(authorized_output_value).expanduser()
    if not raw_output_root.is_absolute() or raw_output_root != raw_output_root.resolve():
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The output root must be an absolute non-symlink path.")
    output_root = raw_output_root.resolve()
    authorized_base = Path(AUTHORIZED_OUTPUT_ROOT).resolve()
    expected_output_root = authorized_base / decision_id / args.dataset
    if output_root != expected_output_root:
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The output root is outside the isolated run namespace.")
    if output_root.exists() or output_root.is_symlink():
        raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The authorized output root already exists.")
    return authorization, output_root


def helper_commit_for_summary(helper_identity):
    return helper_identity[1] if helper_identity is not None else None


def run(args):
    validate_run_args(args)
    authorization, authorized_output_root = _validated_scientific_execution_authorization(args)
    helper_identity = None
    if args.dataset == "rcep":
        helper_identity = require_raw_helper(
            authorization["input_identity"]["rcep_helper_manifest_sha256"]
        )
        if _resolved_rcep_input_files(helper_identity[0]) != authorization["input_identity"]["rcep_input_files"]:
            raise RuntimeError(f"{SCIENTIFIC_AUTHORIZATION_ERROR} The RCEP input identity does not match.")
    else:
        _validated_nyc_taxi_source(authorization["input_identity"]["nyc_dataset_dir"])
    response_backend = (
        (moving_average_coefficients, girf_one)
        if args.dataset == "rcep"
        else (_local_moving_average_coefficients, _local_girf_one)
    )
    data = load_dataset(args.dataset, authorization["input_identity"])
    _validate_loaded_dataset(data, args.dataset, p=args.p)
    Y = data["Y"]
    dates = data["dates"]

    effective_window = args.window if len(Y) > args.window + 8 else max(args.p + 8, len(Y) - 8)
    if not (args.p < effective_window < len(Y)):
        raise ValueError("loaded panel is too short for rolling estimation")
    if effective_window != args.window:
        logger.info("[%s] Requested window=%s is infeasible for T=%s; using effective window=%s", args.dataset, args.window, len(Y), effective_window)

    df_bilateral = data.get("df_bilateral")
    df_tc = data.get("df_tc")
    unit_names = data["unit_names"]
    girf_pair = data["girf_pair"]

    if args.dataset == "rcep":
        W_pre = compute_w_pre(df_bilateral)
        base_w_list = build_w_list(df_bilateral, dates, window_quarters=data["w_window_quarters"], mode=data["w_mode"])
        baseline_key = "baseline_import"
        baseline_label = "Import-based W_t"
    else:
        W_pre = data["W_pre"]
        base_w_list = data["w_list"]
        baseline_key = "baseline_mobility"
        baseline_label = data["primary_label"]

    # Reserve the isolated output tree only after structural panel and
    # topology preprocessing has succeeded.
    out_dir, fig_dir = output_paths(args.dataset, authorized_output_root)
    if args.dataset == "nyc_taxi":
        write_output_csv(data["level_panel"], out_dir / "derived_monthly_panel.csv")
        write_output_json(data["acquisition_info"], out_dir / "acquisition_info.json")

    # Wave B seed echo: provenance header for the run tree.
    run_metadata = {
        "schema_version": 1,
        "authorization_id": authorization.get("decision_id"),
        "seed_root": 20260328,
        "doc_stages": {
            "cp_fit_multi_init": "default_rng(seed) per cp_fit call; seed passed as cp_fit seed arg (20260328 + b per bootstrap draw)",
            "bootstrap_cp_pipeline": "default_rng(20260328)",
            "selection_ridge_rank": "deterministic; no stochastic draws",
        },
        "implementation_files": dict(authorization.get("implementation_files", {})),
        "input_identity": {k: (v if not isinstance(v, dict) else {kk: (str(vv)[:16] + "...") for kk, vv in v.items()}) for k, v in authorization.get("input_identity", {}).items()},
        "argv": dict(authorization.get("argv", {})),
        "output_root": str(authorized_output_root),
    }
    write_output_json(run_metadata, out_dir / "run_metadata.json")

    lambda_ridge, lambda_losses = select_global_ridge_lambda(Y, base_w_list, dates, p=args.p, window=effective_window)
    logger.info("[%s] Selected ridge lambda=%s", args.dataset, lambda_ridge)

    local_results, beta_tensor, rolling_dates = estimate_rolling_local(Y, base_w_list, dates, p=args.p, window=effective_window, lambda_ridge=lambda_ridge)
    rank, rank_losses, fit_losses, beta_recon, _, full_fit_loss, rank_validation = select_cp_rank(
        beta_tensor,
        rolling_dates,
        dates,
        Y,
        base_w_list,
        effective_window,
        p=args.p,
        local_intercepts=np.stack([item["c"] for item in local_results]),
    )
    logger.info("[%s] Selected CP rank=%s", args.dataset, rank)

    cp_results = cp_empirical_paths(local_results, beta_recon, p=args.p)
    target_dates = resolve_target_dates(cp_results, data["requested_girf_dates"])

    panels = []
    agg_series = []
    girf_points = {}
    panel_lookup = {}
    aggregate_lookup = {}

    if args.dataset == "rcep":
        variant_specs = [
            ("baseline_import", 4, "import", "Import-based W_t"),
            ("export_network", 4, "export", "Export-based W_t"),
            ("symmetric_network", 4, "symmetric", "Symmetric W_t"),
            ("long_window_network", 8, "import", "Eight-quarter W_t"),
        ]
        for key, window_quarters, mode, label in variant_specs:
            if key == "baseline_import":
                cur_results = cp_results
            else:
                cur_w_list = build_w_list(df_bilateral, dates, window_quarters=window_quarters, mode=mode)
                local_alt, beta_tensor_alt, _ = estimate_rolling_local(Y, cur_w_list, dates, p=args.p, window=effective_window, lambda_ridge=lambda_ridge)
                factors_alt, _ = cp_fit(beta_tensor_alt, rank, n_init=args.cp_inits, max_iter=args.cp_max_iter, tol=args.cp_tol, seed=20260328 + window_quarters)
                beta_recon_alt = cp_reconstruct(factors_alt)
                cur_results = cp_empirical_paths(local_alt, beta_recon_alt, p=args.p)
            pair_df, agg_df, girf = build_pair_panel(
                cur_results,
                df_tc,
                horizon=8,
                W_mode=mode,
                w_label=label,
                unit_names=unit_names,
                girf_pair=girf_pair,
                target_dates=target_dates,
                W_fixed=None,
                response_backend=response_backend,
            )
            pair_df["variant_key"] = key
            agg_df["variant_key"] = key
            panels.append(pair_df)
            agg_series.append(agg_df)
            panel_lookup[key] = pair_df
            aggregate_lookup[key] = agg_df
            if key == baseline_key:
                girf_points = girf
    else:
        pair_df, agg_df, girf = build_pair_panel(
            cp_results,
            df_tc,
            horizon=8,
            W_mode=data["w_mode"],
            w_label=baseline_label,
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=None,
            response_backend=response_backend,
        )
        pair_df["variant_key"] = baseline_key
        agg_df["variant_key"] = baseline_key
        panels.append(pair_df)
        agg_series.append(agg_df)
        panel_lookup[baseline_key] = pair_df
        aggregate_lookup[baseline_key] = agg_df
        girf_points = girf

    pair_h12, agg_h12, _ = build_pair_panel(
        cp_results,
        df_tc,
        horizon=12,
        W_mode=data["w_mode"],
        w_label=baseline_label,
        unit_names=unit_names,
        girf_pair=girf_pair,
        target_dates=target_dates,
        W_fixed=None,
        response_backend=response_backend,
    )
    pair_h12["variant_key"] = "baseline_h12"
    agg_h12["variant_key"] = "baseline_h12"
    panels.append(pair_h12)
    agg_series.append(agg_h12)
    panel_lookup["baseline_h12"] = pair_h12
    aggregate_lookup["baseline_h12"] = agg_h12

    pair_fix, agg_fix, _ = build_pair_panel(
        cp_results,
        df_tc,
        horizon=8,
        W_mode=data["w_mode"],
        w_label="Frozen topology W_pre",
        unit_names=unit_names,
        girf_pair=girf_pair,
        target_dates=target_dates,
        W_fixed=W_pre,
        response_backend=response_backend,
    )
    pair_fix["variant_key"] = "fixed_pre"
    agg_fix["variant_key"] = "fixed_pre"
    panels.append(pair_fix)
    agg_series.append(agg_fix)
    panel_lookup["fixed_pre"] = pair_fix
    aggregate_lookup["fixed_pre"] = agg_fix

    all_pairs = pd.concat(panels, ignore_index=True)
    all_agg = pd.concat(agg_series, ignore_index=True)

    boot_agg, girf_boot, coef_summary, coef_draw_df = bootstrap_cp_pipeline(
        Y,
        base_w_list,
        dates,
        local_results,
        rank,
        lambda_ridge,
        df_tc,
        unit_names,
        girf_pair,
        target_dates,
        window=effective_window,
        n_boot=args.n_boot,
        block_size=args.block_size,
        p=args.p,
        W_pre=W_pre,
        response_backend=response_backend,
    )
    if coef_summary and df_tc is not None and baseline_key in panel_lookup and "fixed_pre" in panel_lookup:
        point_evolving = fit_panel(panel_lookup[baseline_key], dep="s_net_clip", cluster="pair", fe="pair_time")["Coefficient"]
        point_frozen = fit_panel(panel_lookup["fixed_pre"], dep="s_net_clip", cluster="pair", fe="pair_time")["Coefficient"]
        points = {
            "evolving_coefficient": point_evolving,
            "frozen_coefficient": point_frozen,
            "attenuation_difference": point_evolving - point_frozen,
            "frozen_evolving_ratio": signed_ratio_or_none(point_frozen, point_evolving),
        }
        for quantity, point in points.items():
            if quantity in coef_summary.get("quantities", {}):
                coef_summary["quantities"][quantity]["point"] = None if point is None else float(point)
        # Wave B F2: promote an interval-supported summary and disclose skew.
        for quantity, row in coef_summary.get("quantities", {}).items():
            point_value = row.get("point")
            lower = row.get("p025")
            upper = row.get("p975")
            median_value = row.get("p50")
            if point_value is None or lower is None or upper is None or median_value is None:
                row["promoted_summary"] = "none"
                row["interval_support"] = "unavailable"
                row["skew_disclosure"] = "bootstrap summary unavailable for this quantity"
                continue
            supported = (lower <= point_value <= upper) or (median_value is not None and point_value <= upper and point_value >= lower)
            row["interval_support"] = "inside" if supported else "outside"
            row["promoted_summary"] = "bootstrap_median" if not supported else "point"
            row["skew_disclosure"] = (
                "point estimate lies outside the 95% percentile interval; bootstrap median is promoted and must be reported alongside the point with an explicit skew note"
                if not supported
                else "point estimate lies within the 95% percentile interval"
            )

    selection = {
        "dataset": args.dataset,
        "ridge_lambda": lambda_ridge,
        "ridge_losses": lambda_losses,
        "cp_rank": rank,
        "rank_losses": rank_losses,
        "fit_losses": fit_losses,
        "full_fit_loss": full_fit_loss,
        "rank_validation": rank_validation,
        "cp_inits": args.cp_inits,
        "cp_max_iter": args.cp_max_iter,
        "cp_tol": args.cp_tol,
        "window": effective_window,
        "requested_window": args.window,
        "lag_order": args.p,
        "bootstrap_replications": args.n_boot,
        "bootstrap_block_size": args.block_size,
        "helper_git_commit": helper_commit_for_summary(helper_identity),
        "stability_rate_cp": float(np.mean([row["radius_cp"] >= 1.0 for row in cp_results])),
        "requested_girf_dates": [str(pd.Timestamp(x).date()) for x in data["requested_girf_dates"]],
        "selected_girf_dates": {label: str(pd.Timestamp(date).date()) for date, label in target_dates.items()},
    }

    write_output_csv(all_agg, out_dir / "aggregate_cp_metrics.csv")
    write_output_csv(boot_agg, out_dir / "aggregate_cp_bootstrap.csv")
    if len(coef_draw_df):
        write_output_csv(coef_draw_df, out_dir / "full_path_attenuation_bootstrap.csv")
        full_path_rows = []
        quantities = (coef_summary or {}).get("quantities", {})
        for quantity, row in quantities.items():
            full_path_rows.append(
                {
                    **row,
                    "bootstrap_replications": (coef_summary or {}).get("bootstrap_replications", args.n_boot),
                    "bootstrap_type": (coef_summary or {}).get("bootstrap_type", "global moving-block residual bootstrap with full rolling and CP re-estimation"),
                }
            )
        write_output_csv(pd.DataFrame(full_path_rows), out_dir / "full_path_attenuation_bootstrap_summary.csv")
        write_output_json(coef_summary, out_dir / "full_path_attenuation_bootstrap_summary.json")
    write_output_json(girf_boot, out_dir / "girf_cp_bootstrap.json")
    write_output_json(girf_points, out_dir / "girf_cp_point.json")

    stability_df = stability_summary(cp_results, out_dir / "stability_summary.csv")
    stability_plots(stability_df, fig_dir / "fig_cp_stability")
    aggregate_plot(aggregate_lookup[baseline_key], boot_agg, fig_dir / "fig_cp_aggregate_intervals.png", fig_dir / "fig_cp_aggregate_intervals.pdf")
    girf_plot(girf_points, girf_boot, fig_dir / "fig_cp_girf_intervals.png", fig_dir / "fig_cp_girf_intervals.pdf")
    topology_difference_plot(aggregate_lookup[baseline_key], aggregate_lookup["fixed_pre"], boot_agg, fig_dir / "fig_cp_fixed_vs_tv.png", fig_dir / "fig_cp_fixed_vs_tv.pdf")

    if args.dataset == "rcep":
        perturb_df = top_exposure_propagation_perturbations(
            cp_results,
            horizon=8,
            unit_names=unit_names,
            response_backend=response_backend,
        )
        perturb_summary_df = top_exposure_perturbation_summary(perturb_df)
        write_output_csv(perturb_df, out_dir / "network_propagation_perturbations.csv")
        write_output_csv(perturb_summary_df, out_dir / "network_propagation_perturbation_summary.csv")
        top_exposure_perturbation_plot(perturb_df, fig_dir / "fig_network_propagation_perturbation.png", fig_dir / "fig_network_propagation_perturbation.pdf")

        write_output_csv(all_pairs, out_dir / "pairwise_cp_panel.csv")
        trimmed_panel, trim_q01, trim_q99 = trimmed_raw_panel(panel_lookup["baseline_import"])
        table_df = pd.DataFrame(
            [
                {"Panel": "Alternative topology", "Specification": "Baseline import topology", **fit_panel(panel_lookup["baseline_import"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Alternative topology", "Specification": "Export-based topology", **fit_panel(panel_lookup["export_network"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Alternative topology", "Specification": "Symmetric topology", **fit_panel(panel_lookup["symmetric_network"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Alternative topology", "Specification": "Eight-quarter import topology", **fit_panel(panel_lookup["long_window_network"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Topology benchmark", "Specification": "Evolving topology", **fit_panel(panel_lookup["baseline_import"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Topology benchmark", "Specification": "Frozen benchmark topology", **fit_panel(panel_lookup["fixed_pre"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Inference sensitivity", "Specification": "Horizon H=12", **fit_panel(panel_lookup["baseline_h12"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Inference sensitivity", "Specification": "Two-way clustered SE", **fit_panel(panel_lookup["baseline_import"], dep="s_net_clip", cluster="origin_dest", fe="pair_time")},
                {"Panel": "Metric sensitivity", "Specification": "Unbounded raw pair-level contribution", **fit_panel(panel_lookup["baseline_import"], dep="s_net_raw", cluster="pair", fe="pair_time")},
                {"Panel": "Metric sensitivity", "Specification": "1st-99th percentile trimmed raw pair-level contribution", **fit_panel(trimmed_panel, dep="s_net_raw", cluster="pair", fe="pair_time")},
            ]
        )
        write_output_csv(table_df, out_dir / "table_rcep_cp_benchmark.csv")
        coefficient_plot(table_df, fig_dir / "fig_cp_coefficient_plot.png", fig_dir / "fig_cp_coefficient_plot.pdf")

        breaks_df = structural_break_table(aggregate_lookup["baseline_import"], panel_lookup["baseline_import"])
        write_output_csv(breaks_df, out_dir / "table_rcep_cp_structural_breaks.csv")

        clip_df = clipping_summary(all_pairs)
        clip_df.loc[clip_df["variant_key"] == "baseline_import", "trim_q01"] = trim_q01
        clip_df.loc[clip_df["variant_key"] == "baseline_import", "trim_q99"] = trim_q99
        write_output_csv(clip_df, out_dir / "clipping_summary.csv")
        clipping_histogram(panel_lookup["baseline_import"], fig_dir / "fig_cp_clipping_histogram.png", fig_dir / "fig_cp_clipping_histogram.pdf")

        block_df = bootstrap_block_sensitivity(
            Y,
            base_w_list,
            dates,
            local_results,
            rank,
            lambda_ridge,
            df_tc,
            unit_names,
            girf_pair,
            target_dates,
            window=effective_window,
            p=args.p,
            W_pre=W_pre,
            n_boot=min(args.n_boot, 160),
            response_backend=response_backend,
        )
        write_output_csv(block_df, out_dir / "block_length_sensitivity.csv")
        block_sensitivity_plot(block_df, fig_dir / "fig_cp_block_length_sensitivity.png", fig_dir / "fig_cp_block_length_sensitivity.pdf")

        exclusion_df = stability_exclusion_summary(panel_lookup["baseline_import"], aggregate_lookup["baseline_import"], aggregate_lookup["fixed_pre"], stability_df)
        write_output_csv(exclusion_df, out_dir / "stability_exclusion_sensitivity.csv")
        write_output_json(
            {"attempts": exclusion_df.attrs.get("stable_attempts", {})},
            out_dir / "stable_subsample_absorption_variant.json",
        )

        projected_results = project_cp_results(cp_results, target_radius=0.98)
        projected_pair, projected_agg, _ = build_pair_panel(
            projected_results,
            df_tc,
            horizon=8,
            W_mode=data["w_mode"],
            w_label=baseline_label,
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=None,
            response_backend=response_backend,
        )
        projected_fix, projected_agg_fix, _ = build_pair_panel(
            projected_results,
            df_tc,
            horizon=8,
            W_mode=data["w_mode"],
            w_label="Frozen topology W_pre",
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=W_pre,
            response_backend=response_backend,
        )
        projected_pair["variant_key"] = "stability_projected"
        projected_agg["variant_key"] = "stability_projected"
        projected_fix["variant_key"] = "stability_projected_fixed_pre"
        projected_agg_fix["variant_key"] = "stability_projected_fixed_pre"
        projected_df = stability_projected_summary(
            panel_lookup["baseline_import"],
            aggregate_lookup["baseline_import"],
            aggregate_lookup["fixed_pre"],
            projected_pair,
            projected_agg,
            projected_agg_fix,
        )
        write_output_csv(projected_df, out_dir / "stability_projected_sensitivity.csv")
        stability_sensitivity_plot(
            exclusion_df,
            projected_df,
            fig_dir / "fig_cp_stability_sensitivity.png",
            fig_dir / "fig_cp_stability_sensitivity.pdf",
        )
    else:
        mobility_illustration_plot(aggregate_lookup[baseline_key], boot_agg, girf_points, fig_dir / "fig_cp_mobility_illustration.png", fig_dir / "fig_cp_mobility_illustration.pdf")

    write_output_json({**selection, "coef_bootstrap_summary": coef_summary}, out_dir / "selection_summary.json")

    logger.info("Saved %s outputs to %s", args.dataset, out_dir)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["rcep", "nyc_taxi"], required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--authorization-sha256", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--window", type=int, required=True)
    parser.add_argument("--p", type=int, required=True)
    parser.add_argument("--n-boot", type=int, required=True)
    parser.add_argument("--block-size", type=int, required=True)
    parser.add_argument("--cp-inits", type=int, required=True)
    parser.add_argument("--cp-max-iter", type=int, required=True)
    parser.add_argument("--cp-tol", type=float, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
