"""Run the outcome-free R006f exact-support construction gate."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import hmac
import json
import math
import os
import platform
from pathlib import Path
import tempfile
from types import MappingProxyType
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_NAME = "construction_gate_preoutcome.json"
PROTOCOL_PATH = (
    ROOT / "refine-logs" / "R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md"
)
DESIGN_PATH = (
    ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-07-16-r006e-r006f-dual-track-design.md"
)
EXACT_DESIGN_PATH = Path(__file__).with_name("r006f_exact_design.py")
EXACT_ABSTENTION_PATH = Path(__file__).with_name("r006f_exact_abstention.py")
FORMAL_SEEDS = tuple(range(620001, 620051))
EXCITATION_SCALES = (1.0, 0.25)
ARTIFACT_SCHEMA: dict[str, Any] = {
    "schema_version": None,
    "run_type": None,
    "status": None,
    "contract": {
        "formal_seeds": None,
        "excitation_scales": None,
        "dimensions": {"n": None, "rank": None, "t_len": None},
        "thresholds": {
            "topology_row_sum_error": None,
            "projector_error": None,
            "supported_chi_maximum": None,
            "unsupported_chi_minimum": None,
            "singular_ratio_error": None,
        },
        "controls": {
            "kappa_max": None,
            "absolute_floor": None,
            "classification_threshold": None,
            "m_scale": None,
            "b0_scale": None,
            "beta": None,
            "sigma": None,
        },
    },
    "provenance": {
        "protocol": None,
        "protocol_sha256": None,
        "design_spec": None,
        "design_spec_sha256": None,
        "exact_design_code_sha256": None,
        "exact_abstention_code_sha256": None,
        "gate_code_sha256": None,
        "numpy_version": None,
        "python_version": None,
        "numpy_config": {
            "blas": {
                "name": None,
                "version": None,
                "detection_method": None,
            },
            "lapack": {
                "name": None,
                "version": None,
                "detection_method": None,
            },
            "simd": {"baseline": None, "found": None, "not_found": None},
            "machine": {
                "cpu": None,
                "family": None,
                "endian": None,
                "system": None,
            },
        },
        "numpy_config_sha256": None,
    },
    "checks": {
        label: {
            "passed": None,
            "failure_reasons": None,
            "scale": None,
            "topology": {
                "minimum_entry": None,
                "maximum_row_sum_error": None,
                "passed": None,
            },
            "supported_query_topology": {
                "minimum_entry": None,
                "maximum_row_sum_error": None,
                "passed": None,
            },
            "unsupported_query_topology": {
                "minimum_entry": None,
                "maximum_row_sum_error": None,
                "passed": None,
            },
            "rank": None,
            "projector_error": None,
            "supported_chi": None,
            "unsupported_chi": None,
            "tau": None,
            "retained_singular_values": None,
            "analytic_gap": {
                "formula": None,
                "beta": None,
                "epsilon_star": None,
                "frobenius_norm": None,
                "expected_frobenius_norm": None,
                "absolute_error": None,
            },
        }
        for label in ("strong", "weak")
    }
    | {
        "cross_scale": {
            "passed": None,
            "expected_weak_to_strong_singular_ratio": None,
            "observed_weak_to_strong_singular_ratios": None,
            "maximum_absolute_ratio_error": None,
        }
    },
    "artifact_sha256": None,
}
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "output"
    / "high_impact_revision"
    / "r006f_exact_support_abstention"
)
DEFAULT_OUTPUT = DEFAULT_OUTPUT_DIR / ARTIFACT_NAME


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class LoadedSource:
    path: Path
    content: bytes
    sha256: str


@dataclass(frozen=True)
class GateToken:
    """Immutable capability that a future formal runner must consume at once."""

    artifact_sha256: str
    provenance_sha256: str


@dataclass(frozen=True)
class GateWriteResult:
    artifact: dict[str, Any]
    artifact_path: Path


def _capture_loaded_sources() -> MappingProxyType:
    paths = {
        "protocol": PROTOCOL_PATH,
        "design_spec": DESIGN_PATH,
        "exact_design_code": EXACT_DESIGN_PATH,
        "exact_abstention_code": EXACT_ABSTENTION_PATH,
        "gate_code": Path(__file__),
    }
    captured = {}
    for name, path in paths.items():
        content = path.read_bytes()
        captured[name] = LoadedSource(
            path=path,
            content=content,
            sha256=hashlib.sha256(content).hexdigest(),
        )
    return MappingProxyType(captured)


LOADED_SOURCE_SNAPSHOT = _capture_loaded_sources()


def _assert_loaded_sources_match_disk() -> None:
    for name, source in LOADED_SOURCE_SNAPSHOT.items():
        disk_content = source.path.read_bytes()
        disk_sha256 = hashlib.sha256(disk_content).hexdigest()
        if not hmac.compare_digest(source.sha256, disk_sha256):
            raise RuntimeError(
                f"loaded-source snapshot mismatch for {name}: {source.path}"
            )


try:
    from scripts.experiments.r006f_exact_design import build_exact_panel
except ModuleNotFoundError:  # Direct execution from scripts/experiments.
    from r006f_exact_design import build_exact_panel  # type: ignore

_assert_loaded_sources_match_disk()


def _numpy_config_summary() -> dict[str, Any]:
    config = np.show_config(mode="dicts")
    dependencies = config.get("Build Dependencies", {})

    def dependency(name: str) -> dict[str, str]:
        values = dependencies.get(name, {})
        return {
            "name": str(values.get("name", "unknown")),
            "version": str(values.get("version", "unknown")),
            "detection_method": str(
                values.get("detection method", "unknown")
            ),
        }

    simd = config.get("SIMD Extensions", {})
    machine = config.get("Machine Information", {}).get("host", {})
    return {
        "blas": dependency("blas"),
        "lapack": dependency("lapack"),
        "simd": {
            "baseline": list(simd.get("baseline", [])),
            "found": list(simd.get("found", [])),
            "not_found": list(simd.get("not found", [])),
        },
        "machine": {
            "cpu": str(machine.get("cpu", "unknown")),
            "family": str(machine.get("family", "unknown")),
            "endian": str(machine.get("endian", "unknown")),
            "system": str(machine.get("system", "unknown")),
        },
    }


NUMPY_CONFIG_SUMMARY = _numpy_config_summary()


def _canonical_json_bytes(value: Any) -> bytes:
    _assert_finite_numbers(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _body_digest(body: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(body)).hexdigest()


def _assert_finite_numbers(value: Any, *, location: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number at {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_finite_numbers(child, location=f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_finite_numbers(child, location=f"{location}[{index}]")


def _reject_nonfinite_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant: {value}")


def current_provenance() -> dict[str, Any]:
    """Return hashes for every frozen input to the construction gate."""
    _assert_loaded_sources_match_disk()
    config_sha256 = hashlib.sha256(
        _canonical_json_bytes(NUMPY_CONFIG_SUMMARY)
    ).hexdigest()
    return {
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "protocol_sha256": LOADED_SOURCE_SNAPSHOT["protocol"].sha256,
        "design_spec": str(DESIGN_PATH.relative_to(ROOT)),
        "design_spec_sha256": LOADED_SOURCE_SNAPSHOT["design_spec"].sha256,
        "exact_design_code_sha256": LOADED_SOURCE_SNAPSHOT[
            "exact_design_code"
        ].sha256,
        "exact_abstention_code_sha256": LOADED_SOURCE_SNAPSHOT[
            "exact_abstention_code"
        ].sha256,
        "gate_code_sha256": LOADED_SOURCE_SNAPSHOT["gate_code"].sha256,
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "numpy_config": NUMPY_CONFIG_SUMMARY,
        "numpy_config_sha256": config_sha256,
    }


def frozen_contract() -> dict[str, Any]:
    """Serialize formal constants without consuming any random stream."""
    return {
        "formal_seeds": list(FORMAL_SEEDS),
        "excitation_scales": list(EXCITATION_SCALES),
        "dimensions": {"n": 6, "rank": 2, "t_len": 96},
        "thresholds": {
            "topology_row_sum_error": 1e-12,
            "projector_error": 1e-10,
            "supported_chi_maximum": 1e-10,
            "unsupported_chi_minimum": 1.0 - 1e-10,
            "singular_ratio_error": 1e-10,
        },
        "controls": {
            "kappa_max": 50.0,
            "absolute_floor": 1e-12,
            "classification_threshold": 0.05,
            "m_scale": 0.20,
            "b0_scale": 0.15,
            "beta": 0.50,
            "sigma": 0.05,
        },
    }


def _topology_check(matrix: np.ndarray) -> dict[str, float | bool]:
    minimum_entry = float(np.min(matrix))
    maximum_row_sum_error = float(
        np.max(np.abs(np.sum(matrix, axis=-1) - 1.0))
    )
    return {
        "minimum_entry": minimum_entry,
        "maximum_row_sum_error": maximum_row_sum_error,
        "passed": minimum_entry >= 0.0 and maximum_row_sum_error <= 1e-12,
    }


def _panel_checks(panel: Any) -> dict[str, Any]:
    topology = _topology_check(panel.topology)
    supported_query = _topology_check(panel.w_ref + panel.delta_supported)
    unsupported_query = _topology_check(
        panel.w_ref + panel.delta_unsupported
    )
    rank = int(np.linalg.matrix_rank(panel.z_tilde))
    projector_error = float(
        np.linalg.norm(
            panel.svd_projector - panel.analytic_projector, ord="fro"
        )
    )
    q0 = panel.node_basis[:, 0]
    analytic_gap = (
        panel.config.beta
        * panel.epsilon_star
        * np.outer(q0, panel.v2)
    )
    gap_norm = float(np.linalg.norm(analytic_gap, ord="fro"))
    expected_gap_norm = float(panel.config.beta * panel.epsilon_star)
    gap_error = abs(gap_norm - expected_gap_norm)
    retained = panel.singular_values[panel.singular_values >= panel.tau]
    failures = []
    if not topology["passed"]:
        failures.append("training_topology_not_row_stochastic_nonnegative")
    if not supported_query["passed"]:
        failures.append("supported_query_not_row_stochastic_nonnegative")
    if not unsupported_query["passed"]:
        failures.append("unsupported_query_not_row_stochastic_nonnegative")
    if rank != 2:
        failures.append("residualized_design_rank_not_two")
    if projector_error > 1e-10:
        failures.append("projector_error_exceeds_tolerance")
    if panel.supported_chi > 1e-10:
        failures.append("supported_chi_exceeds_tolerance")
    if panel.unsupported_chi < 1.0 - 1e-10:
        failures.append("unsupported_chi_below_tolerance")
    if gap_error > 1e-12:
        failures.append("analytic_gap_formula_mismatch")
    return {
        "passed": not failures,
        "failure_reasons": failures,
        "scale": panel.scale,
        "topology": topology,
        "supported_query_topology": supported_query,
        "unsupported_query_topology": unsupported_query,
        "rank": rank,
        "projector_error": projector_error,
        "supported_chi": panel.supported_chi,
        "unsupported_chi": panel.unsupported_chi,
        "tau": panel.tau,
        "retained_singular_values": retained.tolist(),
        "analytic_gap": {
            "formula": "beta * epsilon_star * outer(q0, v2)",
            "beta": panel.config.beta,
            "epsilon_star": panel.epsilon_star,
            "frobenius_norm": gap_norm,
            "expected_frobenius_norm": expected_gap_norm,
            "absolute_error": gap_error,
        },
    }


def _artifact_body(smoke: bool) -> dict[str, Any]:
    strong, weak = (
        build_exact_panel(scale=scale) for scale in EXCITATION_SCALES
    )
    strong_checks = _panel_checks(strong)
    weak_checks = _panel_checks(weak)
    strong_singular = np.asarray(strong_checks["retained_singular_values"])
    weak_singular = np.asarray(weak_checks["retained_singular_values"])
    ratio = weak_singular / strong_singular
    ratio_error = float(np.max(np.abs(ratio - 0.25)))
    cross_scale = {
        "passed": ratio_error <= 1e-10,
        "expected_weak_to_strong_singular_ratio": 0.25,
        "observed_weak_to_strong_singular_ratios": ratio.tolist(),
        "maximum_absolute_ratio_error": ratio_error,
    }
    passed = bool(
        strong_checks["passed"]
        and weak_checks["passed"]
        and cross_scale["passed"]
    )
    if smoke:
        status = (
            "SMOKE_CONSTRUCTION_PASS"
            if passed
            else "SMOKE_CONSTRUCTION_FAIL"
        )
    else:
        status = "CONSTRUCTION_PASS" if passed else "CONSTRUCTION_FAIL"
    return {
        "schema_version": 1,
        "status": status,
        "run_type": "construction_only",
        "contract": frozen_contract(),
        "provenance": current_provenance(),
        "checks": {
            "strong": strong_checks,
            "weak": weak_checks,
            "cross_scale": cross_scale,
        },
    }


def _validate_exact_schema(
    value: Any, schema: Any, *, location: str = "$"
) -> None:
    if schema is None:
        return
    if not isinstance(value, dict):
        raise RuntimeError(f"schema mismatch at {location}")
    if set(value) != set(schema):
        raise RuntimeError(f"schema mismatch at {location}")
    for key, child_schema in schema.items():
        _validate_exact_schema(
            value[key], child_schema, location=f"{location}.{key}"
        )


def _atomic_write(destination: Path, payload: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def write_preoutcome_gate(
    artifact_path: Path, smoke: bool = False
) -> GateWriteResult:
    """Evaluate deterministic panels and write a construction-only artifact."""
    destination = Path(artifact_path).expanduser().resolve(strict=False)
    if destination.name != ARTIFACT_NAME:
        raise ValueError(f"artifact filename must be {ARTIFACT_NAME}")
    if smoke and destination == DEFAULT_OUTPUT.resolve(strict=False):
        raise ValueError("smoke writes require a non-formal artifact path")
    body = _artifact_body(smoke)
    artifact = {**body, "artifact_sha256": _body_digest(body)}
    _validate_exact_schema(artifact, ARTIFACT_SCHEMA)
    _atomic_write(destination, _canonical_json_bytes(artifact) + b"\n")
    return GateWriteResult(artifact=artifact, artifact_path=destination)


def write_preoutcome_gate_to_dir(
    output_dir: Path, smoke: bool = False
) -> dict[str, Any]:
    """Directory-oriented compatibility wrapper with an explicit name."""
    return write_preoutcome_gate(
        Path(output_dir) / ARTIFACT_NAME, smoke=smoke
    ).artifact


def _verify_artifact_path(artifact_path: Path) -> GateToken:
    if not artifact_path.is_file():
        raise RuntimeError("missing pre-outcome artifact")
    artifact = json.loads(
        artifact_path.read_text(encoding="utf-8"),
        parse_constant=_reject_nonfinite_constant,
    )
    _assert_finite_numbers(artifact)
    _validate_exact_schema(artifact, ARTIFACT_SCHEMA)
    if artifact["status"] != "CONSTRUCTION_PASS":
        raise RuntimeError("formal construction artifact did not pass")
    body = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    if not hmac.compare_digest(artifact["artifact_sha256"], _body_digest(body)):
        raise RuntimeError("pre-outcome artifact digest mismatch")
    expected_body = _artifact_body(False)
    expected = {
        **expected_body,
        "artifact_sha256": _body_digest(expected_body),
    }
    if artifact != expected:
        raise RuntimeError("pre-outcome artifact differs from recomputation")
    return GateToken(
        artifact_sha256=artifact["artifact_sha256"],
        provenance_sha256=hashlib.sha256(
            _canonical_json_bytes(artifact["provenance"])
        ).hexdigest(),
    )


def verify_preoutcome_gate(output_dir: Path) -> GateToken:
    """Refuse stale or incomplete construction provenance before outcomes."""
    artifact_path = Path(output_dir) / ARTIFACT_NAME
    try:
        return _verify_artifact_path(artifact_path)
    except Exception as error:
        raise RuntimeError(f"{artifact_path}: {error}") from error


class _ConstructionArgumentParser(argparse.ArgumentParser):
    def parse_args(
        self, args: Any = None, namespace: Any = None
    ) -> argparse.Namespace:
        parsed = super().parse_args(args=args, namespace=namespace)
        resolved_output = parsed.output.expanduser().resolve(strict=False)
        if resolved_output.name != ARTIFACT_NAME:
            self.error(f"--output filename must be {ARTIFACT_NAME}")
        if (
            parsed.smoke
            and resolved_output == DEFAULT_OUTPUT.resolve(strict=False)
        ):
            self.error("--smoke requires an explicit non-formal --output")
        parsed.output = resolved_output
        return parsed


def build_argument_parser() -> argparse.ArgumentParser:
    parser = _ConstructionArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--smoke", action="store_true")
    return parser


def main(argv: Any = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    result = write_preoutcome_gate(arguments.output, smoke=arguments.smoke)
    print(
        json.dumps(
            {
                "status": result.artifact["status"],
                "output": str(result.artifact_path),
            },
            sort_keys=True,
        )
    )
    return (
        0
        if result.artifact["status"].endswith("CONSTRUCTION_PASS")
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
