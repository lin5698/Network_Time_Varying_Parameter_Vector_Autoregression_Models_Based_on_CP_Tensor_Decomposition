"""Phase-locked construction runner for frozen R006e.

The initial construction phase creates screening support certificates only.
Screening and confirmation execution are deliberately unavailable here.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import hmac
import json
import math
import multiprocessing
import os
import platform
from pathlib import Path
import resource
import secrets
import shlex
import subprocess
import stat
import sys
import tempfile
from typing import Any, Callable, Mapping
import io

import numpy as np
import scipy

from scripts.experiments import r006c_endpoint_protocol as r006c
from scripts.experiments.r006e_endpoint_support import construct_supported_endpoints
from scripts.experiments.r006e_native_gates import evaluate_screening_gate
from scripts.experiments.r006e_native_metrics import (
    EVALUATOR_INTEGER_FIELDS,
    EVALUATOR_NULLABLE_FIELDS,
    EVALUATOR_ROW_FIELDS,
    EVALUATOR_STRING_FIELDS,
    validate_evaluator_row_contract,
)
from scripts.experiments.r006e_native_protocol import (
    CONFIRMATION_SEEDS,
    METHODS,
    SCREENING_SEEDS,
    STREAM_NAMES,
    R006EConfig,
    build_native_construction_inputs,
    chronological_regions,
    keyed_seed,
    primary_cells,
)


ROOT = Path(__file__).resolve().parents[2]
PRIMARY_OUTPUT_DIR = ROOT / "output/high_impact_revision/r006e_native_supported_recovery"
REPEAT_OUTPUT_DIR = ROOT / "output/high_impact_revision/r006e_native_supported_recovery_repeat"
CONSTRUCTION_ARTIFACT_NAME = "construction_gate_preoutcome.json"
CONFIRMATION_CONSTRUCTION_ARTIFACT_NAME = "confirmation_construction_gate_preoutcome.json"
MEDIAN_SPEC_PATH = ROOT / "refine-logs/R006E_SIMULTANEOUS_MEDIAN_BOUND_SPECIFICATION.md"
MEDIAN_TEST_PATH = ROOT / "scripts/experiments/test_r006e_median_bound.py"
MEDIAN_TEST_COMMAND = "python3 -m unittest scripts.experiments.test_r006e_median_bound -v"
SCREENING_ARTIFACT_NAMES = (
    "screening_replications.csv",
    "screening_summary.csv",
    "screening_results.json",
)
CONFIRMATION_ARTIFACT_NAMES = (
    "confirmation_replications.csv",
    "confirmation_inference.csv",
    "confirmation_results.json",
)
WRITER_NAMES = frozenset(
    (CONSTRUCTION_ARTIFACT_NAME, CONFIRMATION_CONSTRUCTION_ARTIFACT_NAME)
    + SCREENING_ARTIFACT_NAMES
    + CONFIRMATION_ARTIFACT_NAMES
    + ("screening_diagnostics.jsonl", "confirmation_diagnostics.jsonl")
)
FORBIDDEN_RECOVERY_MARKERS = (
    "raw_response_error",
    "operator_error",
    "operator_relative_error",
    "truth_b",
    "truth_bundle",
    "promotion_result",
    "promotion_status",
)
TEST_COMMANDS = (
    "python3 -m unittest scripts.experiments.test_r006e_native_experiment -v",
    "python3 -m unittest discover -s scripts/experiments -p 'test_r006e_*.py'",
    "python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol scripts.experiments.test_r006d_endpoint_support scripts.experiments.test_r006d_construction_gate",
)
SCREENING_CSV_FIELDS = (
    "seed", "rho", "a3", "eta", *EVALUATOR_ROW_FIELDS,
    "peak_memory_bytes", "peak_memory_scope", "peak_memory_worker_pid",
)
SCREENING_INTEGER_FIELDS = frozenset({
    "seed", *EVALUATOR_INTEGER_FIELDS,
    "peak_memory_bytes", "peak_memory_worker_pid",
})
SCREENING_STRING_FIELDS = frozenset({
    *EVALUATOR_STRING_FIELDS, "peak_memory_scope",
})
SCREENING_NULLABLE_FIELDS = EVALUATOR_NULLABLE_FIELDS
SCREENING_FLAG_FIELDS = frozenset({
    "fit_success", "scorable", "at_least_one_converged_start",
    "selected_objective_trace_nonincreasing",
    *(f"{endpoint}_available" for endpoint in (
        "w_ref", "w_alt_interp", "w_alt_family"
    )),
})


class RunnerContractError(ValueError):
    """Raised when runner-owned identity or resource context is invalid."""


@dataclass(frozen=True)
class ConstructionToken:
    status: str
    artifact_sha256: str
    provenance_sha256: str


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    content: bytes
    sha256: str
    identity: tuple[int, int, int, int]


@dataclass(frozen=True)
class PublicationToken:
    path: Path
    device: int
    inode: int
    payload_sha256: str


def _stable_read(path: Path) -> FileSnapshot:
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    try:
        link_stat = os.lstat(target)
    except OSError as error:
        raise RuntimeError(f"stable snapshot missing: {target}") from error
    if stat.S_ISLNK(link_stat.st_mode) or not stat.S_ISREG(link_stat.st_mode):
        raise RuntimeError(f"stable snapshot requires a regular non-symlink file: {target}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags)
    except OSError as error:
        raise RuntimeError(
            f"stable snapshot requires a regular non-symlink file: {target}"
        ) from error
    try:
        before = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    link_identity = (
        link_stat.st_dev, link_stat.st_ino, link_stat.st_size, link_stat.st_mtime_ns
    )
    content = b"".join(chunks)
    if (
        link_identity != before_identity
        or before_identity != after_identity
        or len(content) != before.st_size
    ):
        raise RuntimeError(f"file changed during stable snapshot read: {target}")
    return FileSnapshot(
        target, content, hashlib.sha256(content).hexdigest(), before_identity
    )


def _require_unchanged_snapshot(snapshot: FileSnapshot) -> None:
    current = _stable_read(snapshot.path)
    if current.sha256 != snapshot.sha256 or current.identity != snapshot.identity:
        raise RuntimeError(f"stable snapshot changed during validation: {snapshot.path}")


def _canonical_json_bytes(value: Any) -> bytes:
    _assert_json_primitives(value)
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _assert_json_primitives(value: Any, *, location: str = "$") -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number at {location}")
        return
    if type(value) is list:
        for index, child in enumerate(value):
            _assert_json_primitives(child, location=f"{location}[{index}]")
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for key, child in value.items():
            _assert_json_primitives(child, location=f"{location}.{key}")
        return
    raise ValueError(f"non-JSON primitive at {location}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _scientific_source_paths() -> tuple[Path, ...]:
    experiment_dir = ROOT / "scripts/experiments"
    paths = {
        ROOT / "refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md",
        ROOT / "docs/superpowers/plans/2026-07-16-r006e-native-supported-recovery.md",
    }
    future_median_spec = ROOT / "refine-logs/R006E_SIMULTANEOUS_MEDIAN_BOUND_SPECIFICATION.md"
    if future_median_spec.is_file():
        paths.add(future_median_spec)
    paths.update(experiment_dir.glob("*.py"))
    return tuple(sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix()))


def dependency_version_manifest() -> dict[str, Any]:
    numpy_build_config_text = _canonical_json_bytes(
        np.show_config(mode="dicts")
    ).decode("utf-8")
    return {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "byteorder": sys.byteorder,
        "numpy_build_config_text": numpy_build_config_text,
        "numpy_build_config_sha256": hashlib.sha256(
            numpy_build_config_text.encode("utf-8")
        ).hexdigest(),
    }


def _capture_loaded_source_snapshot() -> dict[str, str]:
    return {
        str(path.resolve()): _sha256_file(path)
        for path in _scientific_source_paths()
    }


IMPORT_SOURCE_SNAPSHOT = _capture_loaded_source_snapshot()


def _assert_loaded_source_snapshot(
    expected: Mapping[str, str] | None = None,
) -> None:
    snapshot = IMPORT_SOURCE_SNAPSHOT if expected is None else dict(expected)
    current_paths = {str(path.resolve()) for path in _scientific_source_paths()}
    if set(snapshot) != current_paths:
        raise RuntimeError("loaded source snapshot closure mismatch")
    for name, digest in snapshot.items():
        path = Path(name)
        if not path.is_file() or _sha256_file(path) != digest:
            raise RuntimeError(f"loaded source snapshot mismatch: {path}")


def current_provenance() -> dict[str, Any]:
    source_hashes = {
        path.relative_to(ROOT).as_posix(): _sha256_file(path)
        for path in _scientific_source_paths()
    }
    dependencies = dependency_version_manifest()
    protocol_path = ROOT / "refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md"
    return {
        "protocol": protocol_path.relative_to(ROOT).as_posix(),
        "protocol_sha256": _sha256_file(protocol_path),
        "source_hashes": source_hashes,
        "dependency_versions": dependencies,
        "dependency_manifest_sha256": hashlib.sha256(
            _canonical_json_bytes(dependencies)
        ).hexdigest(),
        "python_version": dependencies["python"],
        "numpy_version": dependencies["numpy"],
        "platform_version": dependencies["platform"],
        "import_source_snapshot_sha256": hashlib.sha256(
            _canonical_json_bytes(IMPORT_SOURCE_SNAPSHOT)
        ).hexdigest(),
    }


def _config_dict(config: R006EConfig) -> dict[str, Any]:
    value = asdict(config)
    value["fused_penalties"] = list(value["fused_penalties"])
    value["temporal_penalties"] = list(value["temporal_penalties"])
    return value


def _stream_map(seeds: tuple[int, ...]) -> dict[str, Any]:
    result = {}
    for seed in seeds:
        children = r006c.spawn_named_seed_sequences(seed)
        dgp_streams = {
            name: {
                "entropy": int(child.entropy),
                "spawn_key": [int(value) for value in child.spawn_key],
                "spawned": True,
                "used": name != "stress_topology",
            }
            for name, child in children.items()
        }
        family_by_cell = {
            f"{rho:g}|{a3:g}|{eta:g}": keyed_seed(
                seed, rho, a3, eta, "family_endpoint"
            )
            for rho, a3, eta in primary_cells()
        }
        result[str(seed)] = {
            "dgp_and_interp_streams": dgp_streams,
            "family_endpoint_by_cell": family_by_cell,
        }
    return result


def frozen_contract(config: R006EConfig) -> dict[str, Any]:
    regions = chronological_regions(config)
    config_value = _config_dict(config)
    return {
        "config": config_value,
        "config_sha256": hashlib.sha256(_canonical_json_bytes(config_value)).hexdigest(),
        "splits": {
            "calibration": regions.calibration.tolist(),
            "validation": regions.validation.tolist(),
            "evaluation": regions.evaluation.tolist(),
        },
        "primary_cells": [
            {"rho": rho, "a3": a3, "eta": eta}
            for rho, a3, eta in primary_cells()
        ],
        "grids_and_tolerances": {
            "fused_penalties": list(config.fused_penalties),
            "temporal_penalties": list(config.temporal_penalties),
            "objective_tolerance": config.objective_tolerance,
            "stationarity_tolerance": config.stationarity_tolerance,
            "support_floor": config.support_floor,
            "support_threshold": config.support_threshold,
            "kappa_max": config.kappa_max,
        },
        "screening": {
            "seed_ids": list(SCREENING_SEEDS),
            "stream_map": _stream_map(SCREENING_SEEDS),
        },
        "confirmation": {
            "seed_ids": list(CONFIRMATION_SEEDS),
            "stream_declarations": _stream_map(CONFIRMATION_SEEDS),
            "construction": "DECLARATIONS_ONLY",
            "authorization": "CONFIRMATION_NOT_AUTHORIZED",
        },
    }


def _array_digest(value: Any) -> str | None:
    if value is None:
        return None
    array = np.ascontiguousarray(np.asarray(value))
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.tobytes())
    return digest.hexdigest()


def _path_certificate(path: Any) -> dict[str, Any] | None:
    if path is None:
        return None
    return {
        "dates": np.asarray(path.dates, dtype=int).tolist(),
        "chi": np.asarray(path.chi, dtype=float).tolist(),
        "maximum_chi": float(path.maximum_chi),
        "amplification": np.asarray(path.amplification, dtype=float).tolist(),
        "alpha": np.asarray(path.alpha, dtype=float).tolist(),
        "retained_rank": np.asarray(path.retained_rank, dtype=int).tolist(),
        "condition_number": np.asarray(path.condition_number, dtype=float).tolist(),
        "singular_values": [
            np.asarray(values, dtype=float).tolist() for values in path.singular_values
        ],
    }


def _stream_declaration_certificate(declarations: Any) -> dict[str, Any]:
    return {
        declaration.name: {
            "entropy": int(declaration.entropy),
            "spawn_key": [int(value) for value in declaration.spawn_key],
            "spawned": True,
            "used": bool(declaration.used),
        }
        for declaration in declarations
    }


def _construction_certificate(
    construction: Any, *, seed: int, rho: float, a3: float, eta: float,
    design_sha256: str, stream_metadata: Any, family_seed: int,
) -> dict[str, Any]:
    return {
        "seed": seed,
        "rho": rho,
        "a3": a3,
        "eta": eta,
        "status": construction.status,
        "failure_reasons": list(construction.failure_reasons),
        "design_inputs_sha256": design_sha256,
        "family_seed": family_seed,
        "dgp_and_interp_streams": _stream_declaration_certificate(stream_metadata),
        "interp_endpoint_sha256": _array_digest(construction.w_alt_interp),
        "family_endpoint_sha256": _array_digest(construction.w_alt_family),
        "family_selected_index": construction.family_selected_index,
        "interp_calibration": _path_certificate(construction.interp_calibration),
        "interp_prospective": _path_certificate(construction.interp_prospective),
        "family_calibration": _path_certificate(construction.family_calibration),
        "family_prospective": _path_certificate(construction.family_prospective),
        "family_candidate_certificates": [
            {
                "index": int(record.index),
                "endpoint_sha256": _array_digest(record.endpoint),
                "calibration_maximum_chi": float(record.path.maximum_chi),
            }
            for record in construction.family_candidates
        ],
    }


def normalize_run_status(status: str, *, run_type: str) -> str:
    if run_type == "SMOKE":
        return f"SMOKE_{status}"
    if run_type != "FORMAL":
        raise RunnerContractError("run_type must be FORMAL or SMOKE")
    return status


def build_construction_artifact(
    config: R006EConfig | None = None,
    *,
    run_type: str = "FORMAL",
    test_command_status: Mapping[str, str] | None = None,
    expected_source_snapshot: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build screening support once; confirmation remains declarations only."""
    config = R006EConfig() if config is None else config
    if expected_source_snapshot is not None:
        _assert_loaded_source_snapshot(expected_source_snapshot)
    if not isinstance(config, R006EConfig):
        raise TypeError("config must be an R006EConfig")
    statuses = dict(test_command_status or {command: "NOT_RUN" for command in TEST_COMMANDS})
    if set(statuses) != set(TEST_COMMANDS) or any(
        value not in {"PASS", "FAIL", "NOT_RUN"} for value in statuses.values()
    ):
        raise RunnerContractError("test-command status is incomplete or invalid")

    certificates: list[dict[str, Any]] = []
    for seed in SCREENING_SEEDS:
        for rho, a3, eta in primary_cells():
            panel = build_native_construction_inputs(
                config, rho=rho, a3=a3, eta=eta, seed=seed
            )
            construction = construct_supported_endpoints(
                panel.fit,
                w_alt_interp=panel.w_alt_interp,
                family_seed=panel.family_seed,
                config=config,
            )
            certificates.append(
                _construction_certificate(
                    construction,
                    seed=seed,
                    rho=rho,
                    a3=a3,
                    eta=eta,
                    design_sha256=panel.design_sha256(),
                    stream_metadata=panel.stream_metadata,
                    family_seed=panel.family_seed,
                )
            )
    passed = (
        all(item["status"] == "CONSTRUCTION_PASS" for item in certificates)
        and all(statuses[command] == "PASS" for command in TEST_COMMANDS)
    )
    body = {
        "schema_version": 1,
        "run_type": run_type,
        "status": normalize_run_status(
            "CONSTRUCTION_PASS" if passed else "CONSTRUCTION_FAIL", run_type=run_type
        ),
        "current_state": "CONFIRMATION_NOT_AUTHORIZED",
        "contract": frozen_contract(config),
        "provenance": current_provenance(),
        "test_command_status": {command: statuses[command] for command in TEST_COMMANDS},
        "screening_support_certificates": certificates,
    }
    if expected_source_snapshot is not None:
        _assert_loaded_source_snapshot(expected_source_snapshot)
    return {
        **body,
        "artifact_sha256": hashlib.sha256(_canonical_json_bytes(body)).hexdigest(),
    }


def _find_forbidden_recovery_field(value: Any, *, location: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if location != "$.provenance.source_hashes" and any(
                marker in lowered for marker in FORBIDDEN_RECOVERY_MARKERS
            ):
                return f"{location}.{key}"
            found = _find_forbidden_recovery_field(child, location=f"{location}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_forbidden_recovery_field(child, location=f"{location}[{index}]")
            if found:
                return found
    return None


def verify_construction_artifact(artifact: Mapping[str, Any]) -> ConstructionToken:
    """Verify exact structure and every current provenance hash without simulation."""
    if type(artifact) is not dict:
        raise RuntimeError("construction artifact must be a JSON object")
    expected_keys = {
        "schema_version", "run_type", "status", "current_state", "contract",
        "provenance", "test_command_status", "screening_support_certificates",
        "artifact_sha256",
    }
    if set(artifact) != expected_keys:
        raise RuntimeError("construction artifact schema mismatch")
    try:
        _assert_json_primitives(artifact)
    except ValueError as error:
        raise RuntimeError(f"construction artifact schema mismatch: {error}") from error
    forbidden = _find_forbidden_recovery_field(artifact)
    if forbidden:
        raise RuntimeError(f"unexpected recovery field at {forbidden}")
    if artifact["schema_version"] != 1 or artifact["run_type"] != "FORMAL":
        raise RuntimeError("construction artifact is not a formal schema-v1 artifact")
    if artifact["current_state"] != "CONFIRMATION_NOT_AUTHORIZED":
        raise RuntimeError("construction artifact has invalid current state")
    if artifact["provenance"] != current_provenance():
        raise RuntimeError("construction provenance mismatch")
    config = R006EConfig()
    if artifact["contract"] != frozen_contract(config):
        raise RuntimeError("construction contract mismatch")
    if set(artifact["test_command_status"]) != set(TEST_COMMANDS):
        raise RuntimeError("test-command status mismatch")
    if any(
        artifact["test_command_status"][command] not in {"PASS", "FAIL", "NOT_RUN"}
        for command in TEST_COMMANDS
    ):
        raise RuntimeError("test-command status has an invalid value")
    if artifact["status"] == "CONSTRUCTION_PASS" and any(
        artifact["test_command_status"][command] != "PASS"
        for command in TEST_COMMANDS
    ):
        raise RuntimeError("CONSTRUCTION_PASS requires every test-command status PASS")
    certificates = artifact["screening_support_certificates"]
    if type(certificates) is not list or len(certificates) != 80:
        raise RuntimeError("screening certificates must contain exactly 80 entries")
    expected_identities = {
        (seed, rho, a3, eta)
        for seed in SCREENING_SEEDS
        for rho, a3, eta in primary_cells()
    }
    identities = []
    required_certificate_keys = {
        "seed", "rho", "a3", "eta", "status", "failure_reasons",
        "design_inputs_sha256", "family_seed", "interp_endpoint_sha256", "family_endpoint_sha256",
        "dgp_and_interp_streams",
        "family_selected_index", "interp_calibration", "interp_prospective",
        "family_calibration", "family_prospective", "family_candidate_certificates",
    }
    path_keys = {
        "dates", "chi", "maximum_chi", "amplification", "alpha",
        "retained_rank", "condition_number", "singular_values",
    }

    def validate_path(path: Any, expected_dates: list[int], *, label: str) -> None:
        if type(path) is not dict or set(path) != path_keys:
            raise RuntimeError(f"malformed {label} support certificate")
        count = len(expected_dates)
        if path["dates"] != expected_dates:
            raise RuntimeError(f"invalid dates in {label} support certificate")
        vector_keys = ("chi", "amplification", "alpha", "retained_rank", "condition_number")
        if any(type(path[key]) is not list or len(path[key]) != count for key in vector_keys):
            raise RuntimeError(f"misaligned vectors in {label} support certificate")
        if type(path["singular_values"]) is not list or len(path["singular_values"]) != count:
            raise RuntimeError(f"misaligned spectra in {label} support certificate")
        for key in ("chi", "amplification", "condition_number"):
            if any(
                type(value) not in (int, float) or isinstance(value, bool)
                or not math.isfinite(float(value)) or float(value) < 0.0
                for value in path[key]
            ):
                raise RuntimeError(f"invalid {key} in {label} support certificate")
        if any(
            type(value) not in (int, float) or isinstance(value, bool)
            or not math.isfinite(float(value)) or float(value) <= 0.0
            for value in path["alpha"]
        ):
            raise RuntimeError(f"invalid alpha in {label} support certificate")
        if any(type(rank) is not int or rank < 0 for rank in path["retained_rank"]):
            raise RuntimeError(f"invalid retained rank in {label} support certificate")
        for index, (rank, spectrum) in enumerate(
            zip(path["retained_rank"], path["singular_values"])
        ):
            if type(spectrum) is not list or rank > len(spectrum) or any(
                type(value) not in (int, float) or isinstance(value, bool)
                or not math.isfinite(float(value)) or float(value) < 0.0
                for value in spectrum
            ):
                raise RuntimeError(f"invalid singular spectrum in {label} support certificate")
            expected_alpha = 1.0 / max(path["amplification"][index], 1e-12)
            if path["alpha"][index] != expected_alpha:
                raise RuntimeError(f"derived alpha mismatch in {label} support certificate")
            maximum_singular = max(spectrum) if spectrum else 0.0
            tau = max(1e-10, maximum_singular / 50.0)
            retained = [value for value in spectrum if value >= tau]
            expected_rank = len(retained)
            expected_condition = (
                maximum_singular / min(retained) if retained else 0.0
            )
            if rank != expected_rank:
                raise RuntimeError(f"derived retained rank mismatch in {label} support certificate")
            if path["condition_number"][index] != expected_condition:
                raise RuntimeError(f"derived condition mismatch in {label} support certificate")
        maximum = path["maximum_chi"]
        if (
            type(maximum) not in (int, float) or isinstance(maximum, bool)
            or not math.isfinite(float(maximum)) or float(maximum) < 0.0
            or maximum != max(path["chi"])
        ):
            raise RuntimeError(f"maximum chi mismatch in {label} support certificate")

    def lower_sha256(value: Any) -> bool:
        return (
            type(value) is str and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )

    for certificate in certificates:
        if type(certificate) is not dict or set(certificate) != required_certificate_keys:
            raise RuntimeError("malformed screening support certificate")
        identity = tuple(certificate[key] for key in ("seed", "rho", "a3", "eta"))
        identities.append(identity)
        if certificate["status"] not in {"CONSTRUCTION_PASS", "CONSTRUCTION_FAIL"}:
            raise RuntimeError("malformed screening support certificate status")
        if not isinstance(certificate["failure_reasons"], list):
            raise RuntimeError("malformed screening failure reasons")
        if (certificate["status"] == "CONSTRUCTION_PASS") != (not certificate["failure_reasons"]):
            raise RuntimeError("screening status and failures disagree")
        if any(type(reason) is not str or not reason for reason in certificate["failure_reasons"]):
            raise RuntimeError("malformed screening failure reasons")
        for hash_key in ("design_inputs_sha256", "interp_endpoint_sha256"):
            if not lower_sha256(certificate[hash_key]):
                raise RuntimeError(f"invalid {hash_key} hash")
        expected_family_seed = keyed_seed(
            certificate["seed"], certificate["rho"], certificate["a3"],
            certificate["eta"], "family_endpoint",
        )
        if type(certificate["family_seed"]) is not int or certificate["family_seed"] != expected_family_seed:
            raise RuntimeError("family seed certificate mismatch")
        expected_streams = artifact["contract"]["screening"]["stream_map"][str(certificate["seed"])]["dgp_and_interp_streams"]
        if certificate["dgp_and_interp_streams"] != expected_streams:
            raise RuntimeError("DGP stream certificate mismatch")
        validate_path(certificate["interp_calibration"], list(range(80, 140)), label="interpolation calibration")
        validate_path(certificate["interp_prospective"], list(range(140, 200)), label="interpolation prospective")
        candidates = certificate["family_candidate_certificates"]
        if type(candidates) is not list or len(candidates) != config.family_pool_size:
            raise RuntimeError("family candidate certificates must contain exactly 64 entries")
        indices = [candidate.get("index") for candidate in candidates if type(candidate) is dict]
        candidate_keys = {"index", "endpoint_sha256", "calibration_maximum_chi"}
        if (
            any(type(candidate) is not dict or set(candidate) != candidate_keys for candidate in candidates)
            or indices != list(range(config.family_pool_size))
        ):
            raise RuntimeError("malformed or duplicate family candidate entries")
        for candidate in candidates:
            maximum = candidate["calibration_maximum_chi"]
            if (
                not lower_sha256(candidate["endpoint_sha256"])
                or type(maximum) not in (int, float) or isinstance(maximum, bool)
                or not math.isfinite(float(maximum)) or float(maximum) < 0.0
            ):
                raise RuntimeError("invalid family candidate certificate")
        selected = certificate["family_selected_index"]
        supported_indices = [
            candidate["index"] for candidate in candidates
            if candidate["calibration_maximum_chi"] <= config.support_threshold
        ]
        expected_selected = min(supported_indices) if supported_indices else None
        if selected != expected_selected:
            raise RuntimeError("selected family candidate is not the lowest supported index")
        family_calibration = certificate["family_calibration"]
        family_prospective = certificate["family_prospective"]
        if selected is not None:
            validate_path(family_calibration, list(range(80, 140)), label="family calibration")
            validate_path(family_prospective, list(range(140, 200)), label="family prospective")
            selected_candidate = candidates[selected]
            if certificate["family_endpoint_sha256"] != selected_candidate["endpoint_sha256"]:
                raise RuntimeError("selected family endpoint hash mismatch")
            if family_calibration["maximum_chi"] != selected_candidate["calibration_maximum_chi"]:
                raise RuntimeError("selected family calibration certificate mismatch")
        elif any(value is not None for value in (
            certificate["family_endpoint_sha256"], family_calibration, family_prospective
        )):
            raise RuntimeError("missing selection must not carry family endpoint certificates")
        family_complete = (
            type(selected) is int
            and 0 <= selected < config.family_pool_size
            and lower_sha256(certificate["family_endpoint_sha256"])
            and family_calibration is not None
            and family_prospective is not None
        )
        prospective_supported = (
            certificate["interp_calibration"]["maximum_chi"] <= config.support_threshold
            and certificate["interp_prospective"]["maximum_chi"] <= config.support_threshold
            and family_complete
            and family_calibration["maximum_chi"] <= config.support_threshold
            and family_prospective["maximum_chi"] <= config.support_threshold
        )
        expected_failures = []
        if certificate["interp_calibration"]["maximum_chi"] > config.support_threshold:
            expected_failures.append("interp_not_supported_in_calibration")
        elif certificate["interp_prospective"]["maximum_chi"] > config.support_threshold:
            expected_failures.append("interp_lost_support_prospectively")
        if selected is None:
            expected_failures.append("no_supported_family_candidate")
        elif family_prospective["maximum_chi"] > config.support_threshold:
            expected_failures.append("family_lost_support_prospectively")
        if certificate["failure_reasons"] != expected_failures:
            raise RuntimeError("construction failure reasons disagree with support certificates")
        if (certificate["status"] == "CONSTRUCTION_PASS") != prospective_supported:
            raise RuntimeError("construction status disagrees with prospective support")
    if len(identities) != len(set(identities)):
        raise RuntimeError("duplicate screening certificate identity")
    if set(identities) != expected_identities:
        raise RuntimeError("screening certificate identities are incomplete or unexpected")
    expected_status = (
        "CONSTRUCTION_PASS"
        if all(item["status"] == "CONSTRUCTION_PASS" for item in certificates)
        and all(artifact["test_command_status"][command] == "PASS" for command in TEST_COMMANDS)
        else "CONSTRUCTION_FAIL"
    )
    if artifact["status"] != expected_status:
        raise RuntimeError("construction aggregate status mismatch")
    body = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    digest = hashlib.sha256(_canonical_json_bytes(body)).hexdigest()
    if not isinstance(artifact["artifact_sha256"], str) or not hmac.compare_digest(
        artifact["artifact_sha256"], digest
    ):
        raise RuntimeError("construction artifact digest mismatch")
    provenance_digest = hashlib.sha256(
        _canonical_json_bytes(artifact["provenance"])
    ).hexdigest()
    return ConstructionToken(artifact["status"], digest, provenance_digest)


def authorize_screening(
    construction: Mapping[str, Any], *, existing_names: Any = ()
) -> ConstructionToken:
    token = verify_construction_artifact(construction)
    if token.status != "CONSTRUCTION_PASS":
        raise RuntimeError("exact CONSTRUCTION_PASS required before screening")
    forbidden_existing = set(existing_names) & set(
        SCREENING_ARTIFACT_NAMES + CONFIRMATION_ARTIFACT_NAMES
        + (CONFIRMATION_CONSTRUCTION_ARTIFACT_NAME,)
    )
    if forbidden_existing:
        raise RuntimeError("existing phase artifacts forbid screening")
    return token


def _verify_median_specification(specification: Mapping[str, Any]) -> None:
    required = {
        "confidence_allocation", "order_statistic_indexing", "equality_handling",
        "finite_sample_rounding", "approved_spec_path", "approved_test_path",
        "specification_sha256", "tests_sha256",
    }
    if type(specification) is not dict or set(specification) != required:
        raise RuntimeError("median-bound specification is incomplete")
    for key in required - {"specification_sha256", "tests_sha256"}:
        if type(specification[key]) is not str or not specification[key]:
            raise RuntimeError("median-bound specification is incomplete")
    expected_paths = {
        "approved_spec_path": MEDIAN_SPEC_PATH,
        "approved_test_path": MEDIAN_TEST_PATH,
    }
    for key, expected in expected_paths.items():
        supplied = Path(specification[key]).expanduser()
        supplied = supplied if supplied.is_absolute() else Path.cwd() / supplied
        normalized = supplied.parent.resolve(strict=False) / supplied.name
        expected_normalized = (
            expected.expanduser().parent.resolve(strict=False) / expected.name
        )
        if normalized != expected_normalized:
            raise RuntimeError("approved median-bound specification paths mismatch")
    provenance_paths = set(current_provenance()["source_hashes"])
    snapshots = []
    for path_key, hash_key in (("approved_spec_path", "specification_sha256"), ("approved_test_path", "tests_sha256")):
        path = Path(specification[path_key]).expanduser()
        path = path if path.is_absolute() else Path.cwd() / path
        normalized = path.parent.resolve(strict=False) / path.name
        try:
            os.lstat(path)
        except OSError as error:
            raise RuntimeError(
                "approved median-bound specification file is absent"
            ) from error
        try:
            relative = normalized.relative_to(ROOT.resolve(strict=False)).as_posix()
        except ValueError as error:
            raise RuntimeError(
                "approved median-bound specification is outside provenance"
            ) from error
        if relative not in provenance_paths:
            raise RuntimeError("approved median-bound specification is outside provenance")
        snapshot = _stable_read(path)
        snapshots.append(snapshot)
        if specification[hash_key] != snapshot.sha256:
            raise RuntimeError("median-bound specification hash mismatch")
    completed = _run_median_tests()
    if completed.returncode != 0:
        raise RuntimeError("approved median-bound specification tests did not PASS")
    for snapshot in snapshots:
        _require_unchanged_snapshot(snapshot)


def _run_median_tests() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        shlex.split(MEDIAN_TEST_COMMAND), cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )


def verify_confirmation_construction_artifact(
    artifact: Mapping[str, Any], construction: Mapping[str, Any],
    specification: Mapping[str, Any], screening_artifact_sha256: str,
) -> None:
    expected_keys = {
        "schema_version", "run_type", "status", "current_state", "seed_ids",
        "construction_artifact_sha256", "provenance_sha256", "provenance",
        "config_sha256", "candidate_sha256", "median_specification_sha256",
        "median_tests_sha256", "screening_artifact_sha256",
        "confirmation_support_certificates",
        "artifact_sha256",
    }
    if type(artifact) is not dict or set(artifact) != expected_keys:
        raise RuntimeError("confirmation construction schema mismatch")
    try:
        _assert_json_primitives(artifact)
    except ValueError as error:
        raise RuntimeError(f"confirmation construction schema mismatch: {error}") from error
    if _find_forbidden_recovery_field(artifact):
        raise RuntimeError("confirmation construction contains recovery fields")
    body = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    expected_digest = hashlib.sha256(_canonical_json_bytes(body)).hexdigest()
    if not hmac.compare_digest(artifact["artifact_sha256"], expected_digest):
        raise RuntimeError("confirmation construction digest mismatch")
    token = verify_construction_artifact(construction)
    candidate_hash = construction["provenance"]["source_hashes"][
        "scripts/experiments/r006e_dw_tucker.py"
    ]
    exact_values = {
        "schema_version": 1,
        "run_type": "FORMAL_CONFIRMATION_CONSTRUCTION",
        "status": "CONSTRUCTION_PASS",
        "current_state": "CONFIRMATION_NOT_AUTHORIZED",
        "seed_ids": list(CONFIRMATION_SEEDS),
        "construction_artifact_sha256": token.artifact_sha256,
        "provenance_sha256": token.provenance_sha256,
        "provenance": current_provenance(),
        "config_sha256": construction["contract"]["config_sha256"],
        "candidate_sha256": candidate_hash,
        "median_specification_sha256": specification["specification_sha256"],
        "median_tests_sha256": specification["tests_sha256"],
        "screening_artifact_sha256": screening_artifact_sha256,
    }
    for key, expected in exact_values.items():
        if artifact[key] != expected:
            raise RuntimeError(f"confirmation construction {key} mismatch")
    certificates = artifact["confirmation_support_certificates"]
    if type(certificates) is not list or len(certificates) != 240:
        raise RuntimeError("confirmation construction requires exactly 240 certificates")
    expected_identities = {
        (seed, rho, a3, eta)
        for seed in CONFIRMATION_SEEDS for rho, a3, eta in primary_cells()
    }
    identities = [
        tuple(item.get(key) for key in ("seed", "rho", "a3", "eta"))
        for item in certificates if type(item) is dict
    ]
    if len(identities) != 240 or len(set(identities)) != 240 or set(identities) != expected_identities:
        raise RuntimeError("confirmation certificate identities mismatch")
    confirmation_streams = construction["contract"]["confirmation"]["stream_declarations"]
    for certificate in certificates:
        expected_stream = confirmation_streams[str(certificate["seed"])]["dgp_and_interp_streams"]
        if certificate.get("dgp_and_interp_streams") != expected_stream:
            raise RuntimeError("confirmation DGP stream certificate mismatch")
        expected_family_seed = keyed_seed(
            certificate["seed"], certificate["rho"], certificate["a3"],
            certificate["eta"], "family_endpoint",
        )
        if type(certificate.get("family_seed")) is not int or certificate["family_seed"] != expected_family_seed:
            raise RuntimeError("confirmation family seed certificate mismatch")

    # Reuse the screening validator in three exact 10-seed batches.
    for group in range(3):
        mapped = json.loads(json.dumps(construction["screening_support_certificates"]))
        source = certificates[group * 80 : (group + 1) * 80]
        for target, original in zip(mapped, source):
            target.clear()
            target.update(json.loads(json.dumps(original)))
            screening_seed = 240100 + (original["seed"] - (250100 + group * 10))
            target["seed"] = screening_seed
            target["dgp_and_interp_streams"] = construction["contract"]["screening"]["stream_map"][str(screening_seed)]["dgp_and_interp_streams"]
            target["family_seed"] = keyed_seed(
                screening_seed, target["rho"], target["a3"], target["eta"],
                "family_endpoint",
            )
        synthetic = json.loads(json.dumps(construction))
        synthetic["screening_support_certificates"] = mapped
        synthetic_body = {key: value for key, value in synthetic.items() if key != "artifact_sha256"}
        synthetic["artifact_sha256"] = hashlib.sha256(
            _canonical_json_bytes(synthetic_body)
        ).hexdigest()
        verify_construction_artifact(synthetic)


def _verify_screening_results(
    screening_path: Path, construction: Mapping[str, Any], *, repeat: bool,
) -> dict[str, Any]:
    if not isinstance(screening_path, Path):
        raise RuntimeError("exact on-disk screening_results.json required")
    root = (REPEAT_OUTPUT_DIR if repeat else PRIMARY_OUTPUT_DIR).resolve(strict=False)
    expected_path = root / "screening_results.json"
    path = screening_path.expanduser()
    path = path if path.is_absolute() else Path.cwd() / path
    normalized = path.parent.resolve(strict=False) / path.name
    if normalized != expected_path:
        raise RuntimeError("exact on-disk screening_results.json required")
    result_snapshot = _stable_read(path)
    replication_snapshot = _stable_read(root / "screening_replications.csv")
    summary_snapshot = _stable_read(root / "screening_summary.csv")
    try:
        artifact = json.loads(result_snapshot.content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("screening results JSON is malformed") from error
    expected_keys = {
        "schema_version", "status", "gate_result", "seed_ids", "config_sha256",
        "candidate_sha256", "construction_artifact_sha256", "provenance_sha256",
        "screening_replications_sha256", "screening_summary_sha256",
        "artifact_sha256",
    }
    if type(artifact) is not dict or set(artifact) != expected_keys:
        raise RuntimeError("screening results schema mismatch")
    body = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    digest = hashlib.sha256(_canonical_json_bytes(body)).hexdigest()
    if not hmac.compare_digest(artifact["artifact_sha256"], digest):
        raise RuntimeError("screening results artifact digest mismatch")
    token = verify_construction_artifact(construction)
    expected = {
        "schema_version": 1,
        "status": "PASS",
        "seed_ids": list(SCREENING_SEEDS),
        "config_sha256": construction["contract"]["config_sha256"],
        "candidate_sha256": construction["provenance"]["source_hashes"]["scripts/experiments/r006e_dw_tucker.py"],
        "construction_artifact_sha256": token.artifact_sha256,
        "provenance_sha256": token.provenance_sha256,
    }
    for key, value in expected.items():
        if artifact[key] != value:
            raise RuntimeError(f"screening results {key} mismatch")
    for snapshot, filename, hash_key in (
        (replication_snapshot, "screening_replications.csv", "screening_replications_sha256"),
        (summary_snapshot, "screening_summary.csv", "screening_summary_sha256"),
    ):
        if artifact[hash_key] != snapshot.sha256:
            raise RuntimeError(f"screening results {filename} hash mismatch")
    rows = _parse_screening_replications(replication_snapshot.content)
    recomputed_gate = evaluate_screening_gate(rows, config=R006EConfig())
    if recomputed_gate.get("status") != "PASS" or artifact["status"] != "PASS":
        raise RuntimeError("recomputed screening gate did not PASS")
    if artifact["gate_result"] != recomputed_gate:
        raise RuntimeError("recomputed screening gate result mismatch")
    for snapshot in (result_snapshot, replication_snapshot, summary_snapshot):
        _require_unchanged_snapshot(snapshot)
    return artifact


def _parse_screening_replications(payload: bytes) -> list[dict[str, object]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError("screening replications CSV is not UTF-8") from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != SCREENING_CSV_FIELDS:
        raise RuntimeError("screening replications CSV header mismatch")
    rows: list[dict[str, object]] = []
    for line_number, raw in enumerate(reader, start=2):
        if None in raw or set(raw) != set(SCREENING_CSV_FIELDS):
            raise RuntimeError(f"malformed screening CSV row {line_number}")
        converted: dict[str, object] = {}
        for key in SCREENING_CSV_FIELDS:
            value = raw[key]
            if value == "" and key in SCREENING_NULLABLE_FIELDS:
                converted[key] = None
                continue
            if value is None or value == "":
                raise RuntimeError(f"empty screening CSV field {key} at row {line_number}")
            if key in SCREENING_STRING_FIELDS:
                if key == "method" and value not in METHODS:
                    raise RuntimeError(f"invalid screening method at row {line_number}")
                if key == "peak_memory_scope" and value != "fresh_worker_process_peak_rss":
                    raise RuntimeError(f"invalid peak-memory scope at row {line_number}")
                converted[key] = value
            elif key in SCREENING_INTEGER_FIELDS:
                try:
                    parsed = int(value, 10)
                except ValueError as error:
                    raise RuntimeError(f"invalid integer {key} at row {line_number}") from error
                if str(parsed) != value:
                    raise RuntimeError(f"noncanonical integer {key} at row {line_number}")
                if parsed < 0 or key == "peak_memory_worker_pid" and parsed == 0:
                    raise RuntimeError(f"negative or zero integer {key} at row {line_number}")
                if key in SCREENING_FLAG_FIELDS and parsed not in (0, 1):
                    raise RuntimeError(f"invalid binary flag {key} at row {line_number}")
                converted[key] = parsed
            else:
                try:
                    parsed_float = float(value)
                except ValueError as error:
                    raise RuntimeError(f"invalid float {key} at row {line_number}") from error
                if not math.isfinite(parsed_float):
                    raise RuntimeError(f"nonfinite float {key} at row {line_number}")
                if parsed_float < 0.0:
                    raise RuntimeError(f"negative float {key} at row {line_number}")
                converted[key] = parsed_float
        try:
            validate_evaluator_row_contract(converted)
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                f"invalid evaluator contract at row {line_number}: {error}"
            ) from error
        rows.append(converted)
    if len(rows) != 320:
        raise RuntimeError("screening replications CSV must contain exactly 320 rows")
    return rows


def authorize_confirmation(
    screening: Path,
    construction: Mapping[str, Any],
    median_bound_specification: Mapping[str, Any] | None = None,
    confirmation_construction: Mapping[str, Any] | None = None,
    *,
    existing_names: Any = (),
    repeat: bool = False,
) -> None:
    screening_artifact = _verify_screening_results(
        screening, construction, repeat=repeat
    )
    token = verify_construction_artifact(construction)
    candidate_hash = construction["provenance"]["source_hashes"].get(
        "scripts/experiments/r006e_dw_tucker.py"
    )
    if screening_artifact["candidate_sha256"] != candidate_hash:
        raise RuntimeError("screening candidate hash mismatch")
    if median_bound_specification is None:
        raise RuntimeError("median-bound specification required before confirmation")
    _verify_median_specification(median_bound_specification)
    if confirmation_construction is None:
        raise RuntimeError("separate confirmation construction required")
    verify_confirmation_construction_artifact(
        confirmation_construction, construction, median_bound_specification,
        screening_artifact["artifact_sha256"],
    )
    if not repeat and set(existing_names) & set(CONFIRMATION_ARTIFACT_NAMES):
        raise RuntimeError("existing confirmation artifact forbids primary confirmation")
    raise RuntimeError("CONFIRMATION_NOT_AUTHORIZED")


def enrich_replication_row(
    payload: Mapping[str, Any], *, seed: int, rho: float, a3: float, eta: float,
    peak_memory_bytes: int, peak_memory_worker_pid: int,
) -> dict[str, Any]:
    context = {"seed": seed, "rho": rho, "a3": a3, "eta": eta}
    if set(payload) != set(EVALUATOR_ROW_FIELDS):
        raise RunnerContractError("evaluator payload schema mismatch")
    try:
        validate_evaluator_row_contract(payload)
    except (TypeError, ValueError) as error:
        raise RunnerContractError(f"invalid evaluator payload: {error}") from error
    if set(payload) & (set(context) | {
        "peak_memory_bytes", "peak_memory_scope", "peak_memory_worker_pid"
    }):
        raise RunnerContractError("payload may not supply runner-owned context")
    if type(seed) is not int or seed not in SCREENING_SEEDS + CONFIRMATION_SEEDS:
        raise RunnerContractError("invalid or missing seed loop context")
    if any(type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(float(value)) for value in (rho, a3, eta)):
        raise RunnerContractError("invalid or missing cell loop context")
    if (float(rho), float(a3), float(eta)) not in set(primary_cells()):
        raise RunnerContractError("cell context is outside the frozen grid")
    if type(peak_memory_bytes) is not int or peak_memory_bytes < 0:
        raise RunnerContractError("invalid or missing native peak-memory measurement")
    if type(peak_memory_worker_pid) is not int or peak_memory_worker_pid <= 0:
        raise RunnerContractError("invalid or missing peak-memory worker PID")
    values = {
        **context, **dict(payload),
        "peak_memory_bytes": peak_memory_bytes,
        "peak_memory_scope": "fresh_worker_process_peak_rss",
        "peak_memory_worker_pid": peak_memory_worker_pid,
    }
    return {field: values[field] for field in SCREENING_CSV_FIELDS}


def process_peak_rss_bytes() -> int:
    """Return the OS-reported lifetime peak RSS in bytes for this process."""
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _rss_worker(evaluator: Callable[[], Mapping[str, Any]], connection: Any) -> None:
    try:
        payload = dict(evaluator())
        connection.send(("ok", payload, process_peak_rss_bytes(), os.getpid()))
    except BaseException as error:
        connection.send(("error", type(error).__name__, str(error)))
    finally:
        connection.close()


def measure_and_enrich_replication_row(
    evaluator: Callable[[], Mapping[str, Any]], *, seed: int, rho: float,
    a3: float, eta: float,
) -> dict[str, Any]:
    if "fork" not in multiprocessing.get_all_start_methods():
        raise RunnerContractError("fresh fork worker is unsupported on this platform")
    context = multiprocessing.get_context("fork")
    parent_connection, child_connection = context.Pipe(duplex=False)
    process = context.Process(target=_rss_worker, args=(evaluator, child_connection))
    process.start()
    child_connection.close()
    try:
        message = parent_connection.recv()
    except EOFError as error:
        raise RunnerContractError("fresh worker exited without a result") from error
    finally:
        parent_connection.close()
        process.join()
    if process.exitcode != 0:
        raise RunnerContractError(f"fresh worker exited with status {process.exitcode}")
    if message[0] == "error":
        raise RunnerContractError(f"fresh worker {message[1]}: {message[2]}")
    _, payload, peak, worker_pid = message
    row = enrich_replication_row(
        payload, seed=seed, rho=rho, a3=a3, eta=eta,
        peak_memory_bytes=int(peak),
        peak_memory_worker_pid=int(worker_pid),
    )
    return row


def _atomic_write(destination: Path, payload: bytes) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            published_stat = os.fstat(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError as error:
            raise FileExistsError(f"refusing to overwrite {destination}") from error
        temporary.unlink()
        temporary = None
        destination_stat = os.lstat(destination)
        if (destination_stat.st_dev, destination_stat.st_ino) != (
            published_stat.st_dev, published_stat.st_ino
        ):
            raise RuntimeError("published artifact identity mismatch")
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory_fd = os.open(destination.parent, directory_flags)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return published_stat.st_dev, published_stat.st_ino
    except BaseException:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def write_artifact(
    output_dir: Path, name: str, *, artifact: Mapping[str, Any], repeat: bool
) -> Path:
    return _publish_artifact(
        output_dir, name, artifact=artifact, repeat=repeat
    ).path


def _publish_artifact(
    output_dir: Path, name: str, *, artifact: Mapping[str, Any], repeat: bool
) -> PublicationToken:
    if name not in WRITER_NAMES:
        raise ValueError("artifact writer name is not frozen")
    destination_root = Path(output_dir).expanduser().resolve(strict=False)
    expected_root = (REPEAT_OUTPUT_DIR if repeat else PRIMARY_OUTPUT_DIR).resolve(strict=False)
    if destination_root != expected_root:
        raise ValueError("primary/repeat writes require the exact isolated output root")
    lowered_parts = {part.lower() for part in destination_root.parts}
    if any(label in lowered_parts for label in ("r006c", "r006d", "r006f")):
        raise ValueError("R006c/R006d/R006f output paths are forbidden")
    payload = _canonical_json_bytes(dict(artifact)) + b"\n"
    destination = destination_root / name
    device, inode = _atomic_write(destination, payload)
    return PublicationToken(
        destination, device, inode, hashlib.sha256(payload).hexdigest()
    )


def _remove_published_artifact(token: PublicationToken) -> None:
    quarantine = token.path.parent / (
        f".{token.path.name}.cleanup.{os.getpid()}.{secrets.token_hex(16)}"
    )
    try:
        os.replace(token.path, quarantine)
    except OSError as error:
        raise RuntimeError("publication ownership mismatch during cleanup") from error
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(token.path.parent, directory_flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        snapshot = _stable_read(quarantine)
        owned = (
            snapshot.sha256 == token.payload_sha256
            and snapshot.identity[:2] == (token.device, token.inode)
        )
    except RuntimeError:
        owned = False
    if owned:
        quarantine.unlink()
    else:
        try:
            os.link(quarantine, token.path, follow_symlinks=False)
        except FileExistsError:
            pass
        else:
            quarantine.unlink()
    descriptor = os.open(token.path.parent, directory_flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if not owned:
        raise RuntimeError(
            f"publication ownership mismatch during cleanup; quarantined={quarantine}"
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=("construction", "screening", "confirmation"), required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat", action="store_true")
    return parser


def run_preconstruction_tests() -> dict[str, str]:
    statuses = {}
    for command in TEST_COMMANDS:
        completed = subprocess.run(
            shlex.split(command), cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
        )
        statuses[command] = "PASS" if completed.returncode == 0 else "FAIL"
    return statuses


def main(argv: Any = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    if arguments.phase != "construction":
        raise RuntimeError(
            f"{arguments.phase} execution is refused: phase is not authorized"
        )
    _assert_loaded_source_snapshot()
    test_statuses = run_preconstruction_tests()
    _assert_loaded_source_snapshot()
    artifact = build_construction_artifact(
        test_command_status=test_statuses,
        expected_source_snapshot=IMPORT_SOURCE_SNAPSHOT,
    )
    _assert_loaded_source_snapshot()
    publication = _publish_artifact(
        arguments.output,
        CONSTRUCTION_ARTIFACT_NAME,
        artifact=artifact,
        repeat=arguments.repeat,
    )
    try:
        _assert_loaded_source_snapshot()
    except BaseException:
        _remove_published_artifact(publication)
        raise
    print(json.dumps({
        "status": artifact["status"], "output": str(publication.path)
    }, sort_keys=True))
    return 0 if artifact["status"] == "CONSTRUCTION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
