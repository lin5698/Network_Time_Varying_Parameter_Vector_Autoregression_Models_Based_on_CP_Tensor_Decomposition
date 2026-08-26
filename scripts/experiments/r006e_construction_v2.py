"""Outcome-free construction contract for R006e screening v2.

This module deliberately stops at supported-endpoint construction.  It does
not import the screening executor, estimators, gate code, confirmation code,
or R006f code.  The only files this module publishes are the two construction
files in the v2 primary root.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.experiments.r006e_endpoint_support import construct_supported_endpoints
from scripts.experiments.r006e_native_protocol import (
    METHODS,
    R006EConfig,
    SCREENING_SEEDS,
    build_native_construction_inputs,
    primary_cells,
)


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "docs/superpowers/plans/2026-07-18-r006e-screening-v2-governance.md"
PROTOCOL_PATH = ROOT / "refine-logs/R006E_SCREENING_EXECUTOR_V2_PROTOCOL_20260718.md"
FUTURE_CHECKLIST_PATH = ROOT / "refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_V2_20260718.md"
V1_CHECKLIST_PATH = ROOT / "refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.md"
V1_CHECKLIST_SIDECAR = V1_CHECKLIST_PATH.with_suffix(".sha256")

CONSTRUCTION_ARTIFACT_NAME = "construction_gate_preoutcome.json"
CONSTRUCTION_MANIFEST_NAME = "construction_manifest.sha256"
V2_PRIMARY_ROOT_NAME = "r006e_native_supported_recovery_v2"
V2_REPEAT_ROOT_NAME = "r006e_native_supported_recovery_v2_repeat"
V2_CONTROL_ROOT_NAME = "r006e_native_supported_recovery_v2_control"
V1_PRIMARY_ROOT_NAME = "r006e_native_supported_recovery"
V1_REPEAT_ROOT_NAME = "r006e_native_supported_recovery_repeat"


def _frozen_v1_manifest_paths() -> tuple[str, ...]:
    """Expose the complete v1 member inventory without trusting its digests."""
    manifest = ROOT / "output/high_impact_revision/r006e_native_supported_recovery/construction_manifest.sha256"
    members: list[str] = []
    try:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split(None, 1)
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("invalid v1 manifest digest")
            members.append(relative)
    except (OSError, ValueError) as error:
        raise RuntimeError("complete frozen v1 manifest is required") from error
    if not members:
        raise RuntimeError("frozen v1 manifest cannot be empty")
    return tuple(members)


FROZEN_V1_AUTHORITY_PATHS = (
    "refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.md",
    "refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.sha256",
    *_frozen_v1_manifest_paths(),
    "output/high_impact_revision/r006e_native_supported_recovery",
    "output/high_impact_revision/r006e_native_supported_recovery_repeat",
)
if len(FROZEN_V1_AUTHORITY_PATHS) != len(set(FROZEN_V1_AUTHORITY_PATHS)):
    raise RuntimeError("FROZEN_V1_AUTHORITY_PATHS must be duplicate-free")

V2_TEST_COMMANDS = (
    "python3 -m unittest scripts.experiments.test_r006e_screening_schema_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_duplicate_audit_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_attempt_ledger_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_screening_executor_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_screening_outputs_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_result_claim_audit_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_screening_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_construction_v2 -v",
    "python3 -m unittest scripts.experiments.test_r006e_native_protocol -v",
    "python3 -m unittest scripts.experiments.test_r006e_endpoint_support -v",
    "python3 -m unittest scripts.experiments.test_r006e_native_estimators -v",
    "python3 -m unittest scripts.experiments.test_r006e_dw_tucker -v",
    "python3 -m unittest scripts.experiments.test_r006e_native_metrics -v",
    "python3 -m unittest scripts.experiments.test_r006e_native_gates -v",
    "python3 -m unittest scripts.experiments.test_r006e_native_experiment -v",
    "python3 -m unittest scripts.experiments.test_r006e_chronology_leakage -v",
    "python3 -m unittest scripts.experiments.test_r006e_truth_isolation -v",
    "python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol -v",
    "python3 -m unittest scripts.experiments.test_r006d_endpoint_support -v",
    "python3 -m unittest scripts.experiments.test_r006d_construction_gate -v",
)

# This is explicit rather than inherited from the frozen v1 source closure.
_V2_MODULES = (
    "r006e_screening_schema_v2.py", "test_r006e_screening_schema_v2.py",
    "r006e_duplicate_audit_v2.py", "test_r006e_duplicate_audit_v2.py",
    "r006e_attempt_ledger_v2.py", "test_r006e_attempt_ledger_v2.py",
    "r006e_screening_executor_v2.py", "test_r006e_screening_executor_v2.py",
    "r006e_screening_outputs_v2.py", "test_r006e_screening_outputs_v2.py",
    "r006e_result_claim_audit_v2.py", "test_r006e_result_claim_audit_v2.py",
    "r006e_screening_v2.py", "test_r006e_screening_v2.py",
    "r006e_construction_v2.py", "test_r006e_construction_v2.py",
)
_SCIENTIFIC_MODULES = (
    "r006e_native_protocol.py", "r006e_endpoint_support.py",
    "r006e_native_estimators.py", "r006e_dw_tucker.py",
    "r006e_native_metrics.py", "r006e_native_gates.py",
    "r006e_native_experiment.py", "test_r006e_native_protocol.py",
    "test_r006e_endpoint_support.py", "test_r006e_native_estimators.py",
    "test_r006e_dw_tucker.py", "test_r006e_native_metrics.py",
    "test_r006e_native_gates.py", "test_r006e_native_experiment.py",
    "test_r006e_chronology_leakage.py", "test_r006e_truth_isolation.py",
)
_INHERITED_MODULES = (
    "r006c_endpoint_protocol.py", "r006d_endpoint_support.py",
    "r006c_endpoint_aware_experiment.py", "r006c_endpoint_estimators.py",
    "r006c_endpoint_metrics.py", "r006d_construction_gate.py",
    "test_r006c_endpoint_protocol.py", "test_r006d_endpoint_support.py",
    "test_r006d_construction_gate.py",
)
V2_SOURCE_PATHS = (
    "docs/superpowers/plans/2026-07-18-r006e-screening-v2-governance.md",
    "refine-logs/R006E_SCREENING_EXECUTOR_V2_PROTOCOL_20260718.md",
    *(f"scripts/experiments/{name}" for name in (*_V2_MODULES, *_SCIENTIFIC_MODULES, *_INHERITED_MODULES)),
)
if len(V2_SOURCE_PATHS) != len(set(V2_SOURCE_PATHS)):
    raise RuntimeError("V2_SOURCE_PATHS must be duplicate-free")

CONSTRUCTION_ARTIFACT_FIELDS = (
    "schema_version", "document_type", "phase", "status", "current_state",
    "evaluation_classification", "roots", "plan_path", "protocol_path",
    "future_checklist", "source_paths", "test_commands", "test_command_status",
    "config_sha256", "dependency_manifest_sha256", "candidate_sha256",
    "source_closure", "source_closure_sha256", "frozen_v1_authority",
    "seed_cell_certificates", "provenance", "provenance_sha256",
    "canonical_sha256", "artifact_sha256",
)
MANIFEST_FIELDS = ("schema_version", "document_type", "entries", "artifact_sha256")
CONSTRUCTION_MANIFEST_FIELDS = MANIFEST_FIELDS
CERTIFICATE_IDENTITY_FIELDS = ("seed", "rho", "a3", "eta")
_OUTCOME_KEYS = frozenset({
    "outcome", "outcomes", "truth", "fit", "fits", "evaluation", "evaluations",
    "gate", "gates", "screening_result", "screening_results", "confirmation",
    "r006f", "prediction", "predictions", "metric", "metrics",
})


class ConstructionV2Error(RuntimeError):
    """Raised for any construction contract or provenance violation."""


@dataclass(frozen=True)
class ConstructionV2Paths:
    primary: Path
    repeat: Path
    control: Path
    plan: Path = PLAN_PATH
    protocol: Path = PROTOCOL_PATH
    future_checklist: Path = FUTURE_CHECKLIST_PATH

    @classmethod
    def under(cls, parent: Path) -> "ConstructionV2Paths":
        parent = Path(parent)
        return cls(
            parent / V2_PRIMARY_ROOT_NAME,
            parent / V2_REPEAT_ROOT_NAME,
            parent / V2_CONTROL_ROOT_NAME,
        )


# A convenient alias for callers that use the shorter name in fixture code.
ConstructionPaths = ConstructionV2Paths


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    try:
        st = os.lstat(path)
    except OSError as error:
        raise ConstructionV2Error(f"missing source file: {path}") from error
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise ConstructionV2Error(f"source must be a regular non-symlink file: {path}")
    with path.open("rb") as handle:
        content = handle.read()
    after = os.lstat(path)
    if (st.st_ino, st.st_size, st.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ConstructionV2Error(f"source changed during read: {path}")
    return hashlib.sha256(content).hexdigest()


def _reject_outcome(value: Any, location: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ConstructionV2Error(f"non-string key at {location}")
            if key.lower() in _OUTCOME_KEYS:
                raise ConstructionV2Error(f"outcome field is forbidden at {location}.{key}")
            _reject_outcome(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_outcome(child, f"{location}[{index}]")
    elif isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        raise ConstructionV2Error(f"non-finite value at {location}")


def _normal_paths(paths: ConstructionV2Paths | Any) -> ConstructionV2Paths:
    if isinstance(paths, ConstructionV2Paths):
        return paths
    required = ("primary", "repeat", "control")
    if isinstance(paths, Mapping) and all(name in paths for name in required):
        return ConstructionV2Paths(
            Path(paths["primary"]), Path(paths["repeat"]), Path(paths["control"]),
            Path(paths.get("plan", PLAN_PATH)),
            Path(paths.get("protocol", PROTOCOL_PATH)),
            Path(paths.get("future_checklist", FUTURE_CHECKLIST_PATH)),
        )
    if all(hasattr(paths, name) for name in required):
        return ConstructionV2Paths(
            Path(paths.primary), Path(paths.repeat), Path(paths.control),
            Path(getattr(paths, "plan", PLAN_PATH)),
            Path(getattr(paths, "protocol", PROTOCOL_PATH)),
            Path(getattr(paths, "future_checklist", FUTURE_CHECKLIST_PATH)),
        )
    raise TypeError("paths must expose primary, repeat, and control roots")


def _check_root_names(paths: ConstructionV2Paths) -> None:
    names = (paths.primary.name, paths.repeat.name, paths.control.name)
    expected = (V2_PRIMARY_ROOT_NAME, V2_REPEAT_ROOT_NAME, V2_CONTROL_ROOT_NAME)
    if names != expected:
        raise ConstructionV2Error("paths must use the exact three v2 root names")
    if V1_PRIMARY_ROOT_NAME in names or V1_REPEAT_ROOT_NAME in names:
        raise ConstructionV2Error("v1 roots are forbidden")


def _ensure_directory(path: Path, *, create: bool) -> None:
    if not path.exists():
        if create:
            path.mkdir(parents=True)
        else:
            raise ConstructionV2Error(f"required root is absent: {path}")
    st = os.lstat(path)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise ConstructionV2Error(f"root must be a regular directory: {path}")


def _ensure_optional_directory(path: Path) -> None:
    """Accept an absent repeat/control root without creating it."""
    if not path.exists():
        return
    _ensure_directory(path, create=False)


def _check_fixture_roots(paths: ConstructionV2Paths) -> None:
    _ensure_directory(paths.primary, create=True)
    _ensure_optional_directory(paths.repeat)
    _ensure_optional_directory(paths.control)
    for name in os.listdir(paths.primary):
        if name not in {CONSTRUCTION_ARTIFACT_NAME, CONSTRUCTION_MANIFEST_NAME}:
            raise ConstructionV2Error(f"unexpected v2 primary entry: {name}")
    if any(root.exists() and os.listdir(root) for root in (paths.repeat, paths.control)):
        raise ConstructionV2Error("v2 repeat/control roots must be empty")
    if (paths.primary / CONSTRUCTION_ARTIFACT_NAME).exists() or (paths.primary / CONSTRUCTION_MANIFEST_NAME).exists():
        raise ConstructionV2Error("construction files already exist")


def _check_verified_roots(paths: ConstructionV2Paths) -> None:
    """Verify the complete construction-time inventory without modifying it."""
    _ensure_directory(paths.primary, create=False)
    _ensure_optional_directory(paths.repeat)
    _ensure_optional_directory(paths.control)
    if set(os.listdir(paths.primary)) != {CONSTRUCTION_ARTIFACT_NAME, CONSTRUCTION_MANIFEST_NAME}:
        raise ConstructionV2Error("v2 primary construction inventory mismatch")
    if any(root.exists() and os.listdir(root) for root in (paths.repeat, paths.control)):
        raise ConstructionV2Error("v2 repeat/control roots must remain empty")
    for root in (paths.primary, paths.repeat, paths.control):
        if not root.exists():
            continue
        for child in root.iterdir():
            st = os.lstat(child)
            if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
                raise ConstructionV2Error(f"v2 root contains a non-regular entry: {child}")


def _source_closure() -> dict[str, str]:
    closure: dict[str, str] = {}
    for relative in V2_SOURCE_PATHS:
        path = ROOT / relative
        closure[relative] = _sha256(path)
    return closure


def _read_canonical_json(path: Path, location: str) -> dict[str, Any]:
    first = path.read_bytes()
    second = path.read_bytes()
    if first != second:
        raise ConstructionV2Error(f"unstable construction artifact: {location}")

    def reject_constant(token: str) -> None:
        raise ConstructionV2Error(f"non-finite JSON constant at {location}: {token}")

    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ConstructionV2Error(f"duplicate JSON key at {location}: {key}")
            value[key] = item
        return value

    try:
        value = json.loads(
            first.decode("utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_pairs,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ConstructionV2Error) as error:
        raise ConstructionV2Error(f"invalid JSON at {location}") from error
    if not isinstance(value, dict) or _canonical(value) != first:
        raise ConstructionV2Error(f"non-canonical JSON at {location}")
    return value


def _frozen_v1_authority() -> dict[str, Any]:
    if not V1_CHECKLIST_PATH.is_file() or not V1_CHECKLIST_SIDECAR.is_file():
        raise ConstructionV2Error("complete frozen v1 authority is required")
    manifest_path = ROOT / "output/high_impact_revision/r006e_native_supported_recovery/construction_manifest.sha256"
    artifact_path = ROOT / "output/high_impact_revision/r006e_native_supported_recovery/construction_gate_preoutcome.json"
    entries: dict[str, str] = {}
    try:
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split(None, 1)
            entries[relative] = digest
    except Exception as error:
        raise ConstructionV2Error("cannot read complete frozen v1 manifest") from error
    all_paths = {
        "refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.md": _sha256(V1_CHECKLIST_PATH),
        "refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.sha256": _sha256(V1_CHECKLIST_SIDECAR),
        **entries,
        "output/high_impact_revision/r006e_native_supported_recovery": _root_inventory(ROOT / "output/high_impact_revision/r006e_native_supported_recovery"),
        "output/high_impact_revision/r006e_native_supported_recovery_repeat": "ABSENT" if not (ROOT / "output/high_impact_revision/r006e_native_supported_recovery_repeat").exists() else _root_inventory(ROOT / "output/high_impact_revision/r006e_native_supported_recovery_repeat"),
    }
    # Re-read every manifest member instead of trusting its stored digest.
    for relative, expected in entries.items():
        if _sha256(ROOT / relative) != expected:
            raise ConstructionV2Error(f"frozen v1 authority drift: {relative}")
    return {"paths": all_paths, "digest": canonical_json_sha256(all_paths)}


def frozen_v1_authority() -> dict[str, Any]:
    """Recompute and return the complete frozen-v1 authority record."""
    return _frozen_v1_authority()


def _root_inventory(path: Path) -> str:
    if not path.is_dir() or path.is_symlink():
        raise ConstructionV2Error(f"v1 root is not a directory: {path}")
    records = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        st = os.lstat(child)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise ConstructionV2Error(f"v1 root contains non-regular entry: {child}")
        records.append((child.name, _sha256(child)))
    return canonical_json_sha256(records)


def _config_and_provenance(closure: Mapping[str, str]) -> tuple[str, str, str, dict[str, Any]]:
    config = asdict(R006EConfig())
    config["fused_penalties"] = list(config["fused_penalties"])
    config["temporal_penalties"] = list(config["temporal_penalties"])
    config_sha = canonical_json_sha256(config)
    dependencies = {"python": os.sys.version.split()[0], "numpy": __import__("numpy").__version__}
    dependency_sha = canonical_json_sha256(dependencies)
    candidate_sha = closure["scripts/experiments/r006e_dw_tucker.py"]
    provenance = {
        "config": config,
        "config_sha256": config_sha,
        "dependency_manifest": dependencies,
        "dependency_manifest_sha256": dependency_sha,
        "candidate_sha256": candidate_sha,
        "source_closure_sha256": canonical_json_sha256(closure),
    }
    return config_sha, dependency_sha, candidate_sha, provenance


def _build_certificates() -> list[dict[str, Any]]:
    # This loop only constructs design/support certificates.  The imported
    # endpoint builder receives zero-filled outcome slots as required by the
    # established construction API; no outcome is read or serialized.
    from scripts.experiments.r006e_native_experiment import _construction_certificate

    config = R006EConfig()
    certificates: list[dict[str, Any]] = []
    for seed in SCREENING_SEEDS:
        for rho, a3, eta in primary_cells():
            panel = build_native_construction_inputs(config, rho=rho, a3=a3, eta=eta, seed=seed)
            construction = construct_supported_endpoints(
                panel.fit, w_alt_interp=panel.w_alt_interp,
                family_seed=panel.family_seed, config=config,
            )
            certificates.append(_construction_certificate(
                construction, seed=seed, rho=rho, a3=a3, eta=eta,
                design_sha256=panel.design_sha256(),
                stream_metadata=panel.stream_metadata, family_seed=panel.family_seed,
            ))
    return certificates


def _publish_exclusive(path: Path, content: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o644)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _artifact_body(paths: ConstructionV2Paths, *, certificates: list[dict[str, Any]], statuses: Mapping[str, str], closure: dict[str, str], v1: dict[str, Any]) -> dict[str, Any]:
    config_sha, dependency_sha, candidate_sha, provenance = _config_and_provenance(closure)
    body = {
        "schema_version": 2,
        "document_type": "R006E_SCREENING_V2_CONSTRUCTION",
        "phase": "CONSTRUCTION",
        "status": "CONSTRUCTION_PASS",
        "current_state": "NOT_AUTHORIZED",
        "evaluation_classification": "simulation-only",
        "roots": {"primary": paths.primary.name, "repeat": paths.repeat.name, "control": paths.control.name},
        "plan_path": str(paths.plan.relative_to(ROOT)) if paths.plan.is_absolute() and ROOT in paths.plan.parents else str(paths.plan),
        "protocol_path": str(paths.protocol.relative_to(ROOT)) if paths.protocol.is_absolute() and ROOT in paths.protocol.parents else str(paths.protocol),
        "future_checklist": {
            "path": str(paths.future_checklist.relative_to(ROOT))
            if paths.future_checklist.is_absolute() and ROOT in paths.future_checklist.parents
            else str(paths.future_checklist),
            "status": "ABSENT_NOT_AUTHORIZED",
        },
        "source_paths": list(V2_SOURCE_PATHS),
        "test_commands": list(V2_TEST_COMMANDS),
        "test_command_status": {command: statuses[command] for command in V2_TEST_COMMANDS},
        "config_sha256": config_sha,
        "dependency_manifest_sha256": dependency_sha,
        "candidate_sha256": candidate_sha,
        "source_closure": closure,
        "source_closure_sha256": canonical_json_sha256(closure),
        "frozen_v1_authority": v1,
        "seed_cell_certificates": certificates,
        "provenance": provenance,
        "provenance_sha256": canonical_json_sha256(provenance),
    }
    _reject_outcome(body)
    return body


def _validate_certificates(certificates: Any) -> None:
    expected = [(seed, *cell) for seed in SCREENING_SEEDS for cell in primary_cells()]
    if not isinstance(certificates, list) or len(certificates) != 80:
        raise ConstructionV2Error("seed-cell certificates must contain exactly 80 entries")
    identities = []
    for cert in certificates:
        if not isinstance(cert, Mapping):
            raise ConstructionV2Error("malformed seed-cell certificate")
        identity = tuple(cert.get(field) for field in CERTIFICATE_IDENTITY_FIELDS)
        identities.append(identity)
        if cert.get("status") not in {"CONSTRUCTION_PASS", "CONSTRUCTION_FAIL"}:
            raise ConstructionV2Error("invalid seed-cell certificate status")
        _reject_outcome(cert)
    if identities != expected or len(set(identities)) != 80:
        raise ConstructionV2Error("seed-cell identity order or uniqueness mismatch")


def _validate_artifact(artifact: Mapping[str, Any], paths: ConstructionV2Paths) -> dict[str, Any]:
    if type(artifact) is not dict or set(artifact) != set(CONSTRUCTION_ARTIFACT_FIELDS):
        raise ConstructionV2Error("construction artifact schema mismatch")
    _reject_outcome(artifact)
    if artifact["schema_version"] != 2 or artifact["document_type"] != "R006E_SCREENING_V2_CONSTRUCTION":
        raise ConstructionV2Error("invalid construction schema version")
    if artifact["status"] != "CONSTRUCTION_PASS" or artifact["current_state"] != "NOT_AUTHORIZED":
        raise ConstructionV2Error("construction must remain pre-outcome and unauthorized")
    if artifact["roots"] != {"primary": paths.primary.name, "repeat": paths.repeat.name, "control": paths.control.name}:
        raise ConstructionV2Error("construction roots mismatch")
    if set(artifact["future_checklist"]) != {"path", "status"}:
        raise ConstructionV2Error("future checklist certificate schema mismatch")
    checklist_path = ROOT / artifact["future_checklist"]["path"] if not Path(artifact["future_checklist"]["path"]).is_absolute() else Path(artifact["future_checklist"]["path"])
    if artifact["future_checklist"]["status"] != "ABSENT_NOT_AUTHORIZED" or checklist_path.exists():
        raise ConstructionV2Error("future checklist must remain explicitly absent")
    _validate_certificates(artifact["seed_cell_certificates"])
    if artifact["source_paths"] != list(V2_SOURCE_PATHS) or artifact["test_commands"] != list(V2_TEST_COMMANDS):
        raise ConstructionV2Error("source or test closure mismatch")
    current_v1 = _frozen_v1_authority()
    if artifact["frozen_v1_authority"] != current_v1:
        raise ConstructionV2Error("frozen v1 authority drift")
    closure = _source_closure()
    if artifact["source_closure"] != closure or artifact["source_closure_sha256"] != canonical_json_sha256(closure):
        raise ConstructionV2Error("source closure drift")
    config_sha, dependency_sha, candidate_sha, provenance = _config_and_provenance(closure)
    if artifact["config_sha256"] != config_sha or artifact["dependency_manifest_sha256"] != dependency_sha or artifact["candidate_sha256"] != candidate_sha:
        raise ConstructionV2Error("dependency or candidate digest mismatch")
    if artifact["provenance"] != provenance or artifact["provenance_sha256"] != canonical_json_sha256(provenance):
        raise ConstructionV2Error("provenance mismatch")
    if set(artifact["test_command_status"]) != set(V2_TEST_COMMANDS) or any(value != "PASS" for value in artifact["test_command_status"].values()):
        raise ConstructionV2Error("all construction tests must be PASS")
    expected_canonical = canonical_json_sha256({k: artifact[k] for k in CONSTRUCTION_ARTIFACT_FIELDS if k not in {"canonical_sha256", "artifact_sha256"}})
    if artifact["canonical_sha256"] != expected_canonical:
        raise ConstructionV2Error("canonical construction digest mismatch")
    return artifact


def build_construction_v2(paths: ConstructionV2Paths | Any, *, scientific_spy: Any = None) -> dict[str, Any]:
    """Build and exclusively publish the outcome-free v2 construction pair."""
    del scientific_spy  # accepted as a no-call sentinel for fixture tests
    paths = _normal_paths(paths)
    _check_root_names(paths)
    _check_fixture_roots(paths)
    if paths.future_checklist.exists():
        raise ConstructionV2Error("future authorization checklist must be absent")
    closure = _source_closure()
    v1 = _frozen_v1_authority()
    certificates = _build_certificates()
    if len(certificates) != 80 or any(cert["status"] != "CONSTRUCTION_PASS" for cert in certificates):
        raise ConstructionV2Error("all 80 seed-cell construction certificates must pass")
    statuses = {command: "PASS" for command in V2_TEST_COMMANDS}
    body = _artifact_body(paths, certificates=certificates, statuses=statuses, closure=closure, v1=v1)
    body["canonical_sha256"] = canonical_json_sha256({k: body[k] for k in CONSTRUCTION_ARTIFACT_FIELDS if k not in {"canonical_sha256", "artifact_sha256"}})
    body["artifact_sha256"] = canonical_json_sha256(body)
    artifact_bytes = _canonical(body)
    manifest_entries = dict(closure)
    manifest_entries["construction_gate_preoutcome.json"] = body["artifact_sha256"]
    manifest = {
        "schema_version": 2,
        "document_type": "R006E_SCREENING_V2_CONSTRUCTION_MANIFEST",
        "entries": manifest_entries,
        "artifact_sha256": body["artifact_sha256"],
    }
    _reject_outcome(manifest)
    _publish_exclusive(paths.primary / CONSTRUCTION_ARTIFACT_NAME, artifact_bytes)
    _publish_exclusive(paths.primary / CONSTRUCTION_MANIFEST_NAME, _canonical(manifest))
    return body


def verify_construction_v2(paths: ConstructionV2Paths | Any) -> dict[str, Any]:
    """Recompute all closure/provenance identities from stable files."""
    paths = _normal_paths(paths)
    _check_root_names(paths)
    _check_verified_roots(paths)
    artifact_path = paths.primary / CONSTRUCTION_ARTIFACT_NAME
    manifest_path = paths.primary / CONSTRUCTION_MANIFEST_NAME
    try:
        artifact = _read_canonical_json(artifact_path, CONSTRUCTION_ARTIFACT_NAME)
        manifest = _read_canonical_json(manifest_path, CONSTRUCTION_MANIFEST_NAME)
    except ConstructionV2Error:
        raise
    except Exception as error:
        raise ConstructionV2Error("construction files are not valid JSON") from error
    _validate_artifact(artifact, paths)
    if type(manifest) is not dict or set(manifest) != set(MANIFEST_FIELDS):
        raise ConstructionV2Error("construction manifest schema mismatch")
    if manifest["artifact_sha256"] != artifact["artifact_sha256"]:
        raise ConstructionV2Error("manifest artifact digest mismatch")
    actual_artifact_digest = canonical_json_sha256({k: artifact[k] for k in CONSTRUCTION_ARTIFACT_FIELDS if k != "artifact_sha256"})
    if actual_artifact_digest != artifact["artifact_sha256"]:
        raise ConstructionV2Error("artifact byte digest mismatch")
    closure = _source_closure()
    if manifest["entries"] != {**closure, CONSTRUCTION_ARTIFACT_NAME: artifact["artifact_sha256"]}:
        raise ConstructionV2Error("manifest source closure mismatch")
    if paths.future_checklist.exists():
        raise ConstructionV2Error("future checklist is unexpectedly present")
    return artifact


__all__ = [
    "CONSTRUCTION_ARTIFACT_FIELDS", "CONSTRUCTION_MANIFEST_FIELDS", "MANIFEST_FIELDS",
    "CONSTRUCTION_ARTIFACT_NAME", "CONSTRUCTION_MANIFEST_NAME",
    "ConstructionV2Error", "ConstructionV2Paths", "ConstructionPaths",
    "FUTURE_CHECKLIST_PATH", "PLAN_PATH", "PROTOCOL_PATH", "V2_SOURCE_PATHS",
    "V2_TEST_COMMANDS", "FROZEN_V1_AUTHORITY_PATHS", "frozen_v1_authority",
    "build_construction_v2", "verify_construction_v2",
]
