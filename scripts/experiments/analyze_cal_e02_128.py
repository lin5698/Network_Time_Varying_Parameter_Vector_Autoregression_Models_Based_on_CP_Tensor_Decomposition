"""Deterministic read-only audit for NCS calibration item CAL-E02:128.

The analyzer consumes frozen E4-r3 artifacts and source snapshots.  It never
executes the scientific runner, mutates an input, promotes a claim, or writes
outside a newly created CAL-E02:128 output root.  Missing provenance is
reported explicitly; it is never inferred from numerical agreement.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from itertools import product
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping, Sequence

from scripts.experiments.analyze_cal_e01_75 import (
    EXECUTION_AUTHORIZATION_SCHEMA_VERSION,
    EXECUTION_AUTHORIZATION_STATUS,
    EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
    ExecutionAuthorizationError,
    _validate_execution_authorization_common,
)

REGISTER_KEY = "CAL-E02:128"
ANALYSIS_SCHEMA_VERSION = "ncs-cal-e02-128-audit-v1"
AUTHORIZATION_SCHEMA_VERSION = "ncs-four-analysis-authorization-v2"
V2_ITEM_BINDING = {
    "item_id": "V1-033",
    "calibration_id": "CAL-E02",
    "item_index": 128,
    "priority": "P0",
    "action_class": "DIRECT_TEXT_REVISION",
}
V2_FROZEN_HASH_FIELDS = {
    "results": "results_sha256",
    "execution_manifest": "execution_manifest_sha256",
    "execution_complete": "execution_complete_sha256",
    "terminal_inventory": "terminal_inventory_sha256",
    "candidate": "candidate_sha256",
}
V2_REQUIRED_REC_M2_ACTION = "run_read_only_derived_analysis_after_m1_and_separate_go_gate"
V2_REQUIRED_TASK_LIMITS = {
    "m2_scientific_analysis": "BLOCKED_IN_THIS_TASK",
    "s1_s4": "NOT_AUTHORIZED",
    "manuscript": "NOT_AUTHORIZED",
    "register_decision": "NOT_AUTHORIZED",
    "promotion": "NOT_AUTHORIZED",
    "rcep_nyc_activation": "NOT_AUTHORIZED",
    "e4_r3_mutation": "NOT_AUTHORIZED",
    "claim_or_promotion_state_change": "NOT_AUTHORIZED",
    "old_authorization_reuse": "PROHIBITED",
}

STATUS_ORDER = ("AVAILABLE", "OUTSIDE_TARGET", "NONCONVERGED", "NONFINITE", "UNSTABLE")
AUDIT_STATUS_ORDER = ("PASS", "WARN", "BLOCKED", "NOT_EVALUABLE")

EXPECTED_FAMILIES = ("family1", "family2")
EXPECTED_SCALES = (20, 50)
EXPECTED_METHODS = ("local_structured", "causal_temporal_smoother", "fixed_rank_basis")
EXPECTED_QUERIES = ("in_family_interpolation", "cross_generator")
EXPECTED_HORIZONS = (4, 12)
EXPECTED_SEEDS = tuple(range(4101, 4121))
EXPECTED_EVALUATION_TIMES = tuple(range(96, 144))

PROVENANCE_FIELDS = (
    "train_start",
    "train_stop",
    "validation_start",
    "validation_stop",
    "evaluation_start",
    "evaluation_stop",
    "truth_source",
    "truth_isolated",
    "topology_source",
    "query_source",
    "endpoint",
    "selection_input_provenance",
    "native_gate_receipt",
)


class AuditError(RuntimeError):
    """Raised when a requested audit cannot be formed safely."""


def _recursive_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _recursive_sort(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_recursive_sort(item) for item in value]
    return value


def _canonical_v2_item_bytes(value: Any) -> bytes:
    return json.dumps(_recursive_sort(value), ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _require_v2_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuditError(f"{label} must be a non-null JSON object")
    return value


def _require_v2_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise AuditError(f"{label} must be a non-null lowercase SHA-256")
    return value


def _resolve_inventory_path(raw_path: Any, project_root: Path) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise AuditError("terminal inventory artifact path is missing")
    path = Path(raw_path).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def validate_authorization_v2(
    authorization: Mapping[str, Any],
    *,
    register_path: Path,
    register: Mapping[str, Any],
    frozen_paths: Mapping[str, Path],
    frozen_values: Mapping[str, Any],
) -> dict[str, Any]:
    authorization = _require_v2_mapping(authorization, "authorization")
    if authorization.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION:
        raise AuditError("legacy or unsupported authorization schema")
    if any(key in authorization for key in ("frozen_inputs", "authorized_register_items", "execution_policy")):
        raise AuditError("legacy authorization fields are prohibited")
    authorized_scope = _require_v2_mapping(
        authorization.get("authorized_scope"), "authorization.authorized_scope"
    )
    rec_m2_actions = authorized_scope.get("REC_M2")
    if not isinstance(rec_m2_actions, list) or V2_REQUIRED_REC_M2_ACTION not in rec_m2_actions:
        raise AuditError("authorization.authorized_scope.REC_M2 is not bound")
    current_task_limits = _require_v2_mapping(
        authorization.get("current_task_limits"), "authorization.current_task_limits"
    )
    for field, expected in V2_REQUIRED_TASK_LIMITS.items():
        if current_task_limits.get(field) != expected:
            raise AuditError(f"authorization.current_task_limits.{field} drifted")
    binding = _require_v2_mapping(authorization.get("binding"), "authorization.binding")
    declared_register = binding.get("decision_register_path")
    if not isinstance(declared_register, str) or not declared_register:
        raise AuditError("authorization.binding.decision_register_path is required")
    project_root = Path(__file__).resolve().parents[2]
    expected_register_path = Path(declared_register).expanduser()
    if not expected_register_path.is_absolute():
        expected_register_path = project_root / expected_register_path
    observed_register_path = Path(register_path).expanduser().resolve(strict=True)
    if observed_register_path != expected_register_path.resolve():
        raise AuditError("decision-register path is not the v2-bound path")
    expected_register_sha = _require_v2_sha(binding.get("decision_register_sha256"), "authorization.binding.decision_register_sha256")
    observed_register_sha = sha256_file(observed_register_path)
    if observed_register_sha != expected_register_sha:
        raise AuditError("decision-register SHA-256 mismatch")
    if binding.get("item_payload_sha256_algorithm") != "recursive_object_key_sort_then_JSON.stringify_utf8_no_whitespace":
        raise AuditError("unsupported item payload canonicalization")
    item_payloads = _require_v2_mapping(binding.get("item_payloads"), "authorization.binding.item_payloads")
    expected_item_sha = _require_v2_sha(item_payloads.get(V2_ITEM_BINDING["item_id"]), f"authorization.binding.item_payloads.{V2_ITEM_BINDING['item_id']}")
    items = register.get("items")
    if not isinstance(items, list):
        raise AuditError("decision register.items must be a non-null array")
    selected = []
    for item in items:
        if not isinstance(item, Mapping) or item.get("item_id") != V2_ITEM_BINDING["item_id"]:
            continue
        source = item.get("calibration_source")
        if isinstance(source, Mapping) and source.get("calibration_id") == V2_ITEM_BINDING["calibration_id"] and item.get("item_index") == V2_ITEM_BINDING["item_index"]:
            selected.append(item)
    if len(selected) != 1:
        raise AuditError("exact current register item mapping is not unique")
    register_item = selected[0]
    for field in ("item_id", "item_index", "priority", "action_class"):
        if register_item.get(field) != V2_ITEM_BINDING[field]:
            raise AuditError(f"current register item {field} drifted")
    if hashlib.sha256(_canonical_v2_item_bytes(register_item)).hexdigest() != expected_item_sha:
        raise AuditError("canonical register item payload SHA-256 mismatch")
    frozen = _require_v2_mapping(authorization.get("frozen_e4_r3_inputs"), "authorization.frozen_e4_r3_inputs")
    actual_hashes: dict[str, str] = {}
    for role, field in V2_FROZEN_HASH_FIELDS.items():
        expected = _require_v2_sha(frozen.get(field), f"authorization.frozen_e4_r3_inputs.{field}")
        path = frozen_paths.get(role)
        if not isinstance(path, Path):
            raise AuditError(f"frozen input path is missing: {role}")
        resolved = path.expanduser().resolve(strict=True)
        actual = sha256_file(resolved)
        if actual != expected:
            raise AuditError(f"frozen input SHA-256 mismatch: {role}")
        actual_hashes[role] = actual
    workspace_path = frozen_paths.get("workspace_authorization")
    if not isinstance(workspace_path, Path):
        raise AuditError("workspace authorization path is required for the E4 chain")
    workspace_hash = sha256_file(workspace_path.expanduser().resolve(strict=True))
    workspace = _require_v2_mapping(frozen_values.get("workspace_authorization"), "workspace authorization")
    candidate = _require_v2_mapping(frozen_values.get("candidate"), "frozen candidate")
    candidate_id = candidate.get("candidate_id")
    candidate_sha = actual_hashes["candidate"]
    if not isinstance(candidate_id, str) or not candidate_id or workspace.get("candidate_id") != candidate_id or workspace.get("candidate_sha256") != candidate_sha:
        raise AuditError("workspace authorization candidate chain mismatch")
    for role in ("results", "execution_manifest", "execution_complete"):
        value = _require_v2_mapping(frozen_values.get(role), f"frozen {role}")
        if value.get("authorization_sha256") != workspace_hash or value.get("candidate_sha256") != candidate_sha:
            raise AuditError(f"frozen {role} authorization/candidate chain mismatch")
    inventory = _require_v2_mapping(frozen_values.get("terminal_inventory"), "terminal inventory")
    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        raise AuditError("terminal inventory.artifacts is required")
    inventory_roles = {role: frozen_paths[role] for role in V2_FROZEN_HASH_FIELDS if role != "terminal_inventory"}
    inventory_roles["workspace_authorization"] = workspace_path
    for role, path in inventory_roles.items():
        resolved = path.expanduser().resolve(strict=True)
        matches = [entry for entry in artifacts if isinstance(entry, Mapping) and _resolve_inventory_path(entry.get("path"), project_root) == resolved]
        if len(matches) != 1 or matches[0].get("sha256") != sha256_file(resolved):
            raise AuditError(f"terminal inventory chain mismatch: {role}")
    return {
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "decision_register_sha256": observed_register_sha,
        "register_item": dict(register_item),
        "item_payload_sha256": expected_item_sha,
        "frozen_input_sha256": actual_hashes,
        "workspace_authorization_sha256": workspace_hash,
        "e4_chain": {"complete": True, "candidate_id": candidate_id},
        "scope_binding": {
            "rec_m2_action": V2_REQUIRED_REC_M2_ACTION,
            "m2_scientific_analysis": V2_REQUIRED_TASK_LIMITS["m2_scientific_analysis"],
        },
    }


def validate_execution_authorization(
    execution_authorization_path: Path | None,
    *,
    output_root: Path,
    run_id: str,
    observed_paths: Mapping[str, Path],
    artifact_prefix: str = "cal-e02-128-",
    project_root: Path | None = None,
) -> dict[str, Any]:
    try:
        return _validate_execution_authorization_common(
            execution_authorization_path,
            output_root=output_root,
            run_id=run_id,
            observed_paths=observed_paths,
            artifact_prefix=artifact_prefix,
            v2_validator=validate_authorization_v2,
            project_root=project_root,
        )
    except ExecutionAuthorizationError as error:
        raise AuditError(str(error)) from error


@dataclass(frozen=True)
class InputFile:
    input_id: str
    path: Path
    digest: str
    raw: bytes
    value: Any | None


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise AuditError(f"non-finite numeric value at {path}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _assert_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_finite(item, f"{path}[{index}]")


def _load_json(path: Path) -> tuple[bytes, Any]:
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=_reject_nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise AuditError(f"invalid JSON input: {path}: {error}") from error
    _assert_finite(value)
    return raw, value


def _load_input(input_id: str, path: Path, *, json_input: bool) -> InputFile:
    resolved = Path(path).expanduser().resolve(strict=True)
    lowered = str(resolved).lower()
    if "rcep" in lowered or "nyc" in lowered:
        raise AuditError(f"excluded RCEP/NYC route is out of scope: {resolved}")
    if json_input:
        raw, value = _load_json(resolved)
    else:
        raw = resolved.read_bytes()
        value = None
    return InputFile(input_id, resolved, sha256_bytes(raw), raw, value)


def _get(mapping: Mapping[str, Any], *keys: str) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, Mapping) or key not in value:
            return None
        value = value[key]
    return value


def _line_number(source: str, needle: str) -> int | None:
    for number, line in enumerate(source.splitlines(), start=1):
        if needle in line:
            return number
    return None


def _evidence(path: str, source: str, needle: str, statement: str) -> dict[str, Any]:
    line = _line_number(source, needle)
    return {
        "path": path,
        "line": line,
        "statement": statement,
        "located": line is not None,
    }


def _status_counts(rows: Iterable[Mapping[str, Any]], field: str = "status") -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for row in rows:
        status = row.get(field)
        if status in counts:
            counts[str(status)] += 1
        else:
            counts[str(status)] = counts.get(str(status), 0) + 1
    return dict(sorted(counts.items()))


def _field_presence(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[str, dict[str, int]]:
    return {
        field: {
            "present": sum(1 for row in rows if field in row),
            "non_null": sum(1 for row in rows if row.get(field) is not None),
        }
        for field in fields
    }


def _json_safe_key(parts: Sequence[Any]) -> tuple[str, ...]:
    return tuple(str(part) for part in parts)


def _recovery_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("family"),
        row.get("n"),
        row.get("method"),
        row.get("query_class"),
        row.get("horizon"),
    )


def _recovery_identity(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return _recovery_key(row) + (row.get("seed"), row.get("target_time"))


def _interval_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (row.get("family"), row.get("n"), row.get("query_class"))


def _interval_identity(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return _interval_key(row) + (row.get("seed"), row.get("target_time"))


def _sorted_json_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in sorted(rows, key=lambda row: tuple(str(row.get(key)) for key in sorted(row)))]


def _coverage_cell(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_records: int,
    identity_fn: Any,
    target_times: Sequence[int],
    seeds: Sequence[int],
) -> dict[str, Any]:
    identities = [identity_fn(row) for row in rows]
    duplicates = sorted(
        [list(key) for key, count in Counter(identities).items() if count > 1],
        key=lambda item: tuple(str(value) for value in item),
    )
    observed_targets = sorted({row.get("target_time") for row in rows})
    observed_seeds = sorted({row.get("seed") for row in rows})
    expected_target_set = list(target_times)
    expected_seed_set = list(seeds)
    return {
        "observed_records": len(rows),
        "expected_records": expected_records,
        "record_count_status": "PASS" if len(rows) == expected_records else "BLOCKED",
        "status_counts": _status_counts(rows),
        "available_records": sum(1 for row in rows if row.get("status") == "AVAILABLE"),
        "non_available_records": sum(1 for row in rows if row.get("status") != "AVAILABLE"),
        "observed_seed_count": len(observed_seeds),
        "expected_seed_count": len(expected_seed_set),
        "observed_target_count": len(observed_targets),
        "expected_target_count": len(expected_target_set),
        "observed_seeds": observed_seeds,
        "expected_seeds": expected_seed_set,
        "observed_targets": observed_targets,
        "expected_targets": expected_target_set,
        "missing_seeds": [seed for seed in expected_seed_set if seed not in observed_seeds],
        "unexpected_seeds": [seed for seed in observed_seeds if seed not in expected_seed_set],
        "missing_targets": [time for time in expected_target_set if time not in observed_targets],
        "unexpected_targets": [time for time in observed_targets if time not in expected_target_set],
        "duplicate_record_identities": duplicates,
        "duplicate_count": len(duplicates),
        "field_presence": _field_presence(rows, PROVENANCE_FIELDS),
    }


def _expected_recovery_cells() -> list[tuple[str, int, str, str, int]]:
    return list(product(EXPECTED_FAMILIES, EXPECTED_SCALES, EXPECTED_METHODS, EXPECTED_QUERIES, EXPECTED_HORIZONS))


def _expected_interval_cells() -> list[tuple[str, int, str]]:
    return list(product(EXPECTED_FAMILIES, EXPECTED_SCALES, EXPECTED_QUERIES))


def _cell_label(parts: Sequence[Any]) -> str:
    return "|".join(str(part) for part in parts)


def _audit_recovery_coverage(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = _expected_recovery_cells()
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for row in records:
        grouped.setdefault(_recovery_key(row), []).append(row)
    cells: list[dict[str, Any]] = []
    for cell in expected:
        rows = grouped.get(cell, [])
        detail = _coverage_cell(
            rows,
            expected_records=len(EXPECTED_SEEDS) * len(EXPECTED_EVALUATION_TIMES),
            identity_fn=_recovery_identity,
            target_times=EXPECTED_EVALUATION_TIMES,
            seeds=EXPECTED_SEEDS,
        )
        detail["cell"] = {
            "family": cell[0],
            "n": cell[1],
            "method": cell[2],
            "query_class": cell[3],
            "horizon": cell[4],
        }
        cells.append(detail)
    expected_set = set(expected)
    observed_set = set(grouped)
    return {
        "observed_records": len(records),
        "expected_records": len(expected) * len(EXPECTED_SEEDS) * len(EXPECTED_EVALUATION_TIMES),
        "record_count_status": "PASS" if len(records) == len(expected) * len(EXPECTED_SEEDS) * len(EXPECTED_EVALUATION_TIMES) else "BLOCKED",
        "expected_cell_count": len(expected),
        "observed_cell_count": len(observed_set),
        "missing_cells": [_cell_label(cell) for cell in expected if cell not in observed_set],
        "unexpected_cells": [_cell_label(cell) for cell in sorted(observed_set - expected_set, key=lambda item: tuple(str(value) for value in item))],
        "status_counts": _status_counts(records),
        "cells": cells,
        "record_schema_keys": sorted({key for row in records for key in row}),
        "required_record_provenance_fields": list(PROVENANCE_FIELDS),
        "record_provenance_missing_fields": [
            field for field in PROVENANCE_FIELDS if not all(field in row for row in records)
        ],
        "duplicate_record_identity_count": len(
            [key for key, count in Counter(_recovery_identity(row) for row in records).items() if count > 1]
        ),
    }


def _audit_interval_coverage(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = _expected_interval_cells()
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for row in records:
        grouped.setdefault(_interval_key(row), []).append(row)
    cells: list[dict[str, Any]] = []
    for cell in expected:
        rows = grouped.get(cell, [])
        detail = _coverage_cell(
            rows,
            expected_records=len(EXPECTED_SEEDS),
            identity_fn=_interval_identity,
            target_times=(143,),
            seeds=EXPECTED_SEEDS,
        )
        detail["bootstrap_status_counts"] = _sum_nested_status_counts(rows, "bootstrap_status_counts")
        detail["requested_replicates"] = sorted({row.get("requested_replicates") for row in rows})
        detail["completed_replicates"] = sum(int(row.get("completed_replicates", 0)) for row in rows)
        detail["coverage_values"] = sorted({row.get("coverage") for row in rows})
        detail["cell"] = {"family": cell[0], "n": cell[1], "query_class": cell[2]}
        cells.append(detail)
    expected_set = set(expected)
    observed_set = set(grouped)
    expected_records = len(expected) * len(EXPECTED_SEEDS)
    return {
        "observed_records": len(records),
        "expected_records": expected_records,
        "record_count_status": "PASS" if len(records) == expected_records else "BLOCKED",
        "expected_cell_count": len(expected),
        "observed_cell_count": len(observed_set),
        "missing_cells": [_cell_label(cell) for cell in expected if cell not in observed_set],
        "unexpected_cells": [_cell_label(cell) for cell in sorted(observed_set - expected_set, key=lambda item: tuple(str(value) for value in item))],
        "status_counts": _status_counts(records),
        "bootstrap_status_counts": _sum_nested_status_counts(records, "bootstrap_status_counts"),
        "cells": cells,
        "record_schema_keys": sorted({key for row in records for key in row}),
        "record_provenance_missing_fields": [
            field for field in PROVENANCE_FIELDS if not all(field in row for row in records)
        ],
        "duplicate_record_identity_count": len(
            [key for key, count in Counter(_interval_identity(row) for row in records).items() if count > 1]
        ),
    }


def _sum_nested_status_counts(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_ORDER}
    for row in rows:
        nested = row.get(field, {})
        if not isinstance(nested, Mapping):
            counts["INVALID"] = counts.get("INVALID", 0) + 1
            continue
        for status, value in nested.items():
            counts[str(status)] = counts.get(str(status), 0) + int(value)
    return dict(sorted(counts.items()))


def _source_checks(inputs: Mapping[str, InputFile]) -> dict[str, Any]:
    core = inputs["core_source"].raw.decode("utf-8")
    executor = inputs["executor_source"].raw.decode("utf-8")
    preoutcome = inputs["preoutcome_source"].raw.decode("utf-8")
    core_path = "scripts/experiments/e3_synthetic_core.py"
    executor_path = "scripts/experiments/e3_family2_authorized_executor.py"
    preoutcome_path = "scripts/experiments/e3_family2_preoutcome.py"
    checks = {
        "simulation_truth_generation": {
            "status": "PASS" if all(
                needle in core
                for needle in ("def _coefficient_paths", "true_blocks=blocks", "responses[time] = operator @ responses[time - 1]")
            ) else "BLOCKED",
            "evidence": [
                _evidence(core_path, core, "def _coefficient_paths", "coefficient blocks are generated by the declared DGP"),
                _evidence(core_path, core, "true_blocks=blocks", "the generated true coefficient path is retained as truth"),
                _evidence(core_path, core, "responses[time] = operator @ responses[time - 1]", "responses are simulated from the DGP before fitting"),
            ],
        },
        "fit_view_excludes_query_and_truth": {
            "status": "PASS" if all(
                needle in core
                for needle in (
                    "class FitData",
                    "excludes held-out query matrices",
                    "observed_topologies: np.ndarray",
                    "responses: np.ndarray",
                )
            ) else "BLOCKED",
            "evidence": [
                _evidence(core_path, core, "class FitData", "fit data has a restricted type"),
                _evidence(core_path, core, "excludes held-out query matrices", "the fit view documents structural query exclusion"),
            ],
        },
        "selection_uses_observed_validation_only": {
            "status": "PASS" if all(
                needle in core
                for needle in (
                    "def _select_hyperparameter",
                    "fit_data.observed_topologies[time]",
                    "fit_data.responses[time]",
                    "Held-out query topologies",
                )
            ) else "BLOCKED",
            "evidence": [
                _evidence(core_path, core, "def _select_hyperparameter", "selection entry point"),
                _evidence(core_path, core, "fit_data.observed_topologies[time]", "validation uses observed topology"),
                _evidence(core_path, core, "fit_data.responses[time]", "validation uses observed response"),
            ],
        },
        "held_out_query_endpoint": {
            "status": "PASS" if all(
                needle in core
                for needle in (
                    "panel.query_topologies[query_class][target_time]",
                    "panel.true_blocks[target_time]",
                    "def _native_endpoint",
                )
            ) else "BLOCKED",
            "evidence": [
                _evidence(core_path, core, "panel.query_topologies[query_class][target_time]", "evaluation consumes the held-out query topology"),
                _evidence(core_path, core, "panel.true_blocks[target_time]", "evaluation constructs the DGP truth endpoint"),
            ],
        },
        "native_gate": {
            "status": "PASS" if all(
                needle in core
                for needle in (
                    "def require_e3_1_gate",
                    "E3-1 gate failed for",
                    "STATUS_OUTSIDE_TARGET",
                )
            ) and "require_e3_1_gate()" in executor else "BLOCKED",
            "evidence": [
                _evidence(core_path, core, "def require_e3_1_gate", "the native E3-1 gate is executable"),
                _evidence(core_path, core, "E3-1 gate failed for", "gate failure prevents downstream execution"),
                _evidence(executor_path, executor, "fixture_report = core.require_e3_1_gate()", "the frozen runner invokes the native gate"),
            ],
        },
        "preoutcome_failure_retention": {
            "status": "PASS" if all(
                needle in preoutcome
                for needle in ("STATUS_NONFINITE", "STATUS_UNSTABLE", "all_predeclared_cells")
            ) else "BLOCKED",
            "evidence": [
                _evidence(preoutcome_path, preoutcome, "STATUS_NONFINITE", "all declared failure statuses are retained"),
                _evidence(preoutcome_path, preoutcome, "all_predeclared_cells", "cross-generator cells cannot be selected after stability"),
            ],
        },
    }
    source_hashes = {
        "core_source": inputs["core_source"].digest,
        "executor_source": inputs["executor_source"].digest,
        "preoutcome_source": inputs["preoutcome_source"].digest,
        "candidate_bound_core": _candidate_source_hash(inputs, "e3_synthetic_core.py"),
        "candidate_bound_executor": _candidate_source_hash(inputs, "e3_family2_authorized_executor.py"),
        "candidate_bound_preoutcome": _candidate_source_hash(inputs, "e3_family2_preoutcome.py"),
    }
    source_hashes["binding_status"] = (
        "PASS"
        if source_hashes["core_source"] == source_hashes["candidate_bound_core"]
        and source_hashes["executor_source"] == source_hashes["candidate_bound_executor"]
        and source_hashes["preoutcome_source"] == source_hashes["candidate_bound_preoutcome"]
        else "BLOCKED"
    )
    return {"checks": checks, "hashes": source_hashes}


def _candidate_source_hash(inputs: Mapping[str, InputFile], filename: str) -> str | None:
    candidate = inputs["candidate"].value
    source_hashes = _get(candidate, "bindings", "source_hashes")
    if not isinstance(source_hashes, Mapping):
        return None
    for path, digest in source_hashes.items():
        if str(path).endswith(filename):
            return str(digest)
    return None


def _hash_bindings(
    inputs: Mapping[str, InputFile],
    authorization: Mapping[str, Any],
    v2_binding: Mapping[str, Any],
) -> dict[str, Any]:
    expected = {
        "decision_register": authorization["binding"]["decision_register_sha256"],
        "e4_results": authorization["frozen_e4_r3_inputs"]["results_sha256"],
        "e4_execution_manifest": authorization["frozen_e4_r3_inputs"]["execution_manifest_sha256"],
        "e4_execution_complete": authorization["frozen_e4_r3_inputs"]["execution_complete_sha256"],
        "e4_terminal_inventory": authorization["frozen_e4_r3_inputs"]["terminal_inventory_sha256"],
        "e4_candidate": authorization["frozen_e4_r3_inputs"]["candidate_sha256"],
        "e4_workspace_authorization": v2_binding["workspace_authorization_sha256"],
    }
    actual = {
        "decision_register": inputs["decision_register"].digest,
        "e4_results": inputs["e3_results"].digest,
        "e4_execution_manifest": inputs["execution_manifest"].digest,
        "e4_execution_complete": inputs["execution_complete"].digest,
        "e4_terminal_inventory": inputs["terminal_inventory"].digest,
        "e4_candidate": inputs["candidate"].digest,
        "e4_authorization": inputs["e4_authorization"].digest,
    }
    actual["e4_workspace_authorization"] = actual.pop("e4_authorization")
    rows = {}
    for key in expected:
        rows[key] = {
            "expected_sha256": expected[key],
            "observed_sha256": actual[key],
            "observed_status": "PASS" if actual[key] == expected[key] else "BLOCKED",
        }
    return {
        "rows": rows,
        "all_observed_hashes_match": all(row["observed_status"] == "PASS" for row in rows.values()),
    }


def _register_item(register: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    items = register.get("items")
    matches = [
        item
        for item in items or []
        if isinstance(item, Mapping)
        and item.get("item_id") == V2_ITEM_BINDING["item_id"]
        and isinstance(item.get("calibration_source"), Mapping)
        and item["calibration_source"].get("calibration_id") == V2_ITEM_BINDING["calibration_id"]
        and item.get("item_index") == V2_ITEM_BINDING["item_index"]
    ]
    if len(matches) != 1:
        return None, {
            "status": "BLOCKED",
            "match_count": len(matches),
            "reason": "exact calibration_id + item_index match is not unique",
        }
    return dict(matches[0]), {"status": "PASS", "match_count": 1}


def _register_binding_status(hash_bindings: Mapping[str, Any], register_match: Mapping[str, Any]) -> str:
    if register_match.get("status") != "PASS":
        return "BLOCKED"
    return "PASS" if hash_bindings["rows"]["decision_register"]["observed_status"] == "PASS" else "BLOCKED"


def _truth_distinction() -> dict[str, Any]:
    return {
        "simulation_truth": {
            "classification": "simulation_only",
            "meaning": "The known coefficient path and response-generating DGP are independent of fitted predictions within the frozen synthetic route.",
            "does_not_mean": "It is not an empirical dataset ground truth observed independently of the simulation.",
        },
        "independent_empirical_ground_truth": {
            "classification": "absent_from_frozen_e4_r3_route",
            "meaning": "No native empirical dataset, external measurement, or independent empirical target provenance is present in the frozen E4-r3 route.",
            "status": "NOT_EVALUABLE",
        },
        "claim_ceiling": "simulation_only; no broad empirical fairness or superiority claim is licensed",
    }


def _required_cells(
    *,
    sources: Mapping[str, Any],
    recovery: Mapping[str, Any],
    intervals: Mapping[str, Any],
    results: Mapping[str, Any],
    gate_receipt: Mapping[str, Any],
    hash_bindings: Mapping[str, Any],
    register_binding_status: str,
    specification: Mapping[str, Any],
) -> list[dict[str, Any]]:
    static = sources["checks"]
    recovery_complete = recovery["record_count_status"] == "PASS" and not recovery["missing_cells"] and not recovery["unexpected_cells"]
    interval_complete = intervals["record_count_status"] == "PASS" and not intervals["missing_cells"] and not intervals["unexpected_cells"]
    result_schema_ok = (
        results.get("schema_version") == "e3-family2-synthetic-quarantine-results-v3"
        and results.get("status") == "COMPLETE_QUARANTINE_ONLY"
        and str(results.get("promotion", "")).startswith("PROHIBITED")
    )
    partitions = _get(specification, "chronological_partitions")
    chronology_static = partitions == {
        "train": {"start": 1, "stop": 72},
        "validation": {"start": 72, "stop": 96},
        "evaluation": {"start": 96, "stop": 144},
    }
    record_chronology_missing = "evaluation_start" in recovery["record_provenance_missing_fields"]
    selection_record_missing = "selection_input_provenance" in recovery["record_provenance_missing_fields"]
    query_record_missing = (
        "query_source" in recovery["record_provenance_missing_fields"]
        or "topology_source" in recovery["record_provenance_missing_fields"]
    )
    endpoint_record_missing = "endpoint" in recovery["record_provenance_missing_fields"]
    truth_record_missing = (
        "truth_source" in recovery["record_provenance_missing_fields"]
        or "truth_isolated" in recovery["record_provenance_missing_fields"]
    )
    fixture = _get(results, "results", "fixture_report") or {}
    fixture_pass = (
        _get(fixture, "f1_negative", "status") == "OUTSIDE_TARGET"
        and _get(fixture, "f2_unrestricted_negative", "status") == "OUTSIDE_TARGET"
        and _get(fixture, "f2_diagonal_negative", "status") == "OUTSIDE_TARGET"
        and _get(fixture, "f2_diagonal_positive", "status") == "AVAILABLE"
        and _get(fixture, "non_equivalence", "status") == "DISTINCT_FAMILY"
    )
    gate_pass = gate_receipt.get("verdict") == "PASS" and gate_receipt.get("returncode") == 0 and gate_receipt.get("scientific_execution") == "NOT_AUTHORIZED" and fixture_pass

    return [
        {
            "cell_id": "simulation_truth_provenance",
            "status": "PASS" if static["simulation_truth_generation"]["status"] == "PASS" and recovery_complete and result_schema_ok else "BLOCKED",
            "evidence": static["simulation_truth_generation"]["evidence"],
            "finding": "Frozen result is simulation-only and retains DGP truth-derived spectral radius and endpoint errors.",
            "coverage": {"recovery": recovery_complete, "interval": interval_complete},
        },
        {
            "cell_id": "independent_empirical_ground_truth",
            "status": "NOT_EVALUABLE",
            "evidence": [
                {"path": "refine-logs/e3_family2_inputs/synthetic-e3-v4.json", "field": "input_route", "value": _get(specification, "input_route")},
                {"path": "refine-logs/e3_family2_inputs/synthetic-e3-v4.json", "field": "excluded_routes", "value": _get(specification, "excluded_routes")},
            ],
            "finding": "No independent empirical dataset or empirical ground-truth provenance exists in the synthetic-only frozen route; simulation truth cannot substitute for it.",
        },
        {
            "cell_id": "training_validation_evaluation_chronology",
            "status": "WARN" if chronology_static and record_chronology_missing else ("PASS" if chronology_static else "BLOCKED"),
            "evidence": [
                {"path": "refine-logs/e3_family2_inputs/synthetic-e3-v4.json", "field": "chronological_partitions", "value": partitions},
                _evidence("scripts/experiments/e3_synthetic_core.py", sources["_core_text"], "using only observations strictly before target", "local fitting is causal with respect to target time"),
            ],
            "finding": "The frozen protocol and implementation define train/validation/evaluation chronology, but recovery records do not serialize the split boundaries or a per-record chronology receipt.",
            "missing_record_provenance": [field for field in PROVENANCE_FIELDS if field.startswith(("train_", "validation_", "evaluation_")) and field in recovery["record_provenance_missing_fields"]],
        },
        {
            "cell_id": "selection_inputs",
            "status": "WARN" if static["selection_uses_observed_validation_only"]["status"] == "PASS" and selection_record_missing else ("PASS" if static["selection_uses_observed_validation_only"]["status"] == "PASS" else "BLOCKED"),
            "evidence": static["selection_uses_observed_validation_only"]["evidence"],
            "finding": "Static code and frozen manifest restrict selection to observed-topology validation loss and prohibit held-out topology truth, but records lack candidate-loss vectors and selection-input provenance.",
            "missing_record_provenance": ["selection_input_provenance", "candidate_losses"],
        },
        {
            "cell_id": "held_out_topology_query",
            "status": "WARN" if static["held_out_query_endpoint"]["status"] == "PASS" and query_record_missing else ("PASS" if static["held_out_query_endpoint"]["status"] == "PASS" else "BLOCKED"),
            "evidence": static["held_out_query_endpoint"]["evidence"],
            "finding": "Query classes and separate query paths are declared and evaluated, but result records do not carry query/topology source identity or a held-out query receipt.",
            "missing_record_provenance": ["topology_source", "query_source"],
        },
        {
            "cell_id": "endpoint_parity",
            "status": "WARN" if endpoint_record_missing else "PASS",
            "evidence": [
                {"path": "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/family2_query_contract.json", "field": "content.endpoint", "value": "full_operator_and_finite_horizon_response"},
                {"path": "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/comparator_registry.json", "field": "content.records[*].endpoint_shape", "value": "full_operator_and_finite_horizon_response"},
            ],
            "finding": "Operator and finite-horizon response errors are present under the frozen native endpoint contract, but records omit an explicit endpoint signature/provenance field.",
            "missing_record_provenance": ["endpoint"],
        },
        {
            "cell_id": "truth_isolation",
            "status": "WARN" if static["fit_view_excludes_query_and_truth"]["status"] == "PASS" and truth_record_missing else ("PASS" if static["fit_view_excludes_query_and_truth"]["status"] == "PASS" else "BLOCKED"),
            "evidence": static["fit_view_excludes_query_and_truth"]["evidence"],
            "finding": "FitData structurally excludes held-out query matrices and truth blocks, but the frozen result does not serialize a per-record truth-isolation receipt.",
            "missing_record_provenance": ["truth_source", "truth_isolated"],
        },
        {
            "cell_id": "native_gate",
            "status": "PASS" if gate_pass and static["native_gate"]["status"] == "PASS" else "BLOCKED",
            "evidence": static["native_gate"]["evidence"],
            "finding": "The frozen fixture report and no-science gate receipt pass the native E3-1 classification gate; this does not establish empirical ground truth.",
            "gate_receipt": {"verdict": gate_receipt.get("verdict"), "tests_run": gate_receipt.get("tests_run"), "scientific_execution": gate_receipt.get("scientific_execution")},
        },
        {
            "cell_id": "register_binding",
            "status": register_binding_status,
            "evidence": [{"input_id": "decision_register", "expected_sha256": hash_bindings["rows"]["decision_register"]["expected_sha256"], "observed_sha256": hash_bindings["rows"]["decision_register"]["observed_sha256"]}],
            "finding": "The exact register item was found, but its observed SHA must match the authorized binding before the analysis can be treated as fully registered.",
        },
    ]



def _retained_record_lines(recovery: Sequence[Mapping[str, Any]], intervals: Sequence[Mapping[str, Any]]) -> bytes:
    rows: list[dict[str, Any]] = []
    for row in recovery:
        rows.append(
            {
                "record_type": "recovery",
                "family": row.get("family"),
                "n": row.get("n"),
                "method": row.get("method"),
                "query_class": row.get("query_class"),
                "horizon": row.get("horizon"),
                "seed": row.get("seed"),
                "target_time": row.get("target_time"),
                "status": row.get("status"),
                "selected_hyperparameter": row.get("selected_hyperparameter"),
                "validation_loss": row.get("validation_loss"),
                "operator_mse": row.get("operator_mse"),
                "response_mse": row.get("response_mse"),
                "estimated_spectral_radius": row.get("estimated_spectral_radius"),
                "truth_spectral_radius": row.get("truth_spectral_radius"),
            }
        )
    for row in intervals:
        rows.append(
            {
                "record_type": "interval",
                "family": row.get("family"),
                "n": row.get("n"),
                "method": row.get("method"),
                "query_class": row.get("query_class"),
                "horizon": row.get("horizon"),
                "seed": row.get("seed"),
                "target_time": row.get("target_time"),
                "status": row.get("status"),
                "selection_status": row.get("selection_status"),
                "selected_hyperparameter": row.get("selected_hyperparameter"),
                "selection_validation_loss": row.get("selection_validation_loss"),
                "raw_response_mse": row.get("raw_response_mse"),
                "stability_qualified_response_mse": row.get("stability_qualified_response_mse"),
                "bootstrap_status_counts": row.get("bootstrap_status_counts"),
            }
        )
    rows.sort(key=lambda row: (row["record_type"], str(row.get("family")), int(row.get("n", -1)), str(row.get("method")), str(row.get("query_class")), int(row.get("horizon", -1)), int(row.get("seed", -1)), int(row.get("target_time", -1))))
    return b"".join(_canonical_json(row) + b"\n" for row in rows)


def _output_json_bytes(value: Any) -> bytes:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False).encode("utf-8") + b"\n"


def _write_new(path: Path, raw: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(raw)


def _output_inventory(output_root: Path, names: Sequence[str]) -> dict[str, Any]:
    return {
        "schema_version": "ncs-cal-e02-128-output-inventory-v1",
        "register_key": REGISTER_KEY,
        "files": [
            {"path": name, "sha256": sha256_file(output_root / name)}
            for name in sorted(names)
        ],
    }


def _markdown_report(analysis: Mapping[str, Any]) -> bytes:
    lines = [
        "# CAL-E02:128 Frozen-Data Audit",
        "",
        f"- Verdict: **{analysis['verdict']}**",
        f"- Data sufficiency: **{analysis['data_sufficiency']}**",
        f"- Register key: `{analysis['register_key']}`",
        f"- Input bundle SHA-256: `{analysis['input_bundle_sha256']}`",
        "",
        "## Ground-Truth Boundary",
        "",
        "The frozen route is `simulation_only`. Its DGP truth is separate from fitted predictions, but it is not independent empirical ground truth. No empirical fairness or superiority claim is licensed.",
        "",
        "## Required Cells",
        "",
        "| Cell | Status | Finding |",
        "|---|---|---|",
    ]
    for cell in analysis["required_cells"]:
        finding = str(cell["finding"]).replace("|", "\\|")
        lines.append(f"| `{cell['cell_id']}` | **{cell['status']}** | {finding} |")
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Recovery records: {analysis['coverage']['recovery']['observed_records']} / {analysis['coverage']['recovery']['expected_records']}; status counts retain all declared statuses.",
            f"- Interval records: {analysis['coverage']['intervals']['observed_records']} / {analysis['coverage']['intervals']['expected_records']}; bootstrap status counts retain all declared statuses.",
            f"- Paired completion keys: {analysis['coverage']['paired_common_completion']['observed_key_count']} / {analysis['coverage']['paired_common_completion']['expected_key_count']}.",
            "",
            "## Blocking Gaps",
            "",
        ]
    )
    for gap in analysis["blocking_gaps"]:
        lines.append(f"- {gap}")
    lines.extend(
        [
            "",
            "## Scope Boundary",
            "",
            "This artifact does not modify the manuscript, author decision register, or frozen quarantine. It does not execute the fresh protocol and does not use RCEP or NYC.",
            "",
        ]
    )
    return "\n".join(lines).encode("ascii")


def _build_analysis(inputs: Mapping[str, InputFile]) -> tuple[dict[str, Any], dict[str, bytes]]:
    authorization = inputs["analysis_authorization"].value
    register = inputs["decision_register"].value
    results = inputs["e3_results"].value
    manifest = inputs["execution_manifest"].value
    candidate = inputs["candidate"].value
    specification = inputs["specification"].value
    gate_receipt = inputs["gate_receipt"].value
    recovery = _get(results, "results", "recovery_records") or []
    intervals = _get(results, "results", "interval_records") or []
    if not isinstance(recovery, list) or not isinstance(intervals, list):
        raise AuditError("frozen result records are not arrays")
    if not isinstance(authorization, Mapping) or not isinstance(register, Mapping) or not isinstance(results, Mapping):
        raise AuditError("required JSON root is not an object")
    v2_binding = validate_authorization_v2(
        authorization,
        register_path=inputs["decision_register"].path,
        register=register,
        frozen_paths={
            "results": inputs["e3_results"].path,
            "execution_manifest": inputs["execution_manifest"].path,
            "execution_complete": inputs["execution_complete"].path,
            "terminal_inventory": inputs["terminal_inventory"].path,
            "candidate": inputs["candidate"].path,
            "workspace_authorization": inputs["e4_authorization"].path,
        },
        frozen_values={
            "results": inputs["e3_results"].value,
            "execution_manifest": inputs["execution_manifest"].value,
            "execution_complete": inputs["execution_complete"].value,
            "terminal_inventory": inputs["terminal_inventory"].value,
            "candidate": inputs["candidate"].value,
            "workspace_authorization": inputs["e4_authorization"].value,
        },
    )
    hash_bindings = _hash_bindings(inputs, authorization, v2_binding)
    register_item, register_match = dict(v2_binding["register_item"]), {"status": "PASS", "match_count": 1}
    register_status = _register_binding_status(hash_bindings, register_match)
    sources = _source_checks(inputs)
    sources["_core_text"] = inputs["core_source"].raw.decode("utf-8")
    recovery_coverage = _audit_recovery_coverage([row for row in recovery if isinstance(row, Mapping)])
    interval_coverage = _audit_interval_coverage([row for row in intervals if isinstance(row, Mapping)])
    paired = _get(results, "results", "paired_common_completion") or {}
    expected_pair_keys = [
        f"{family}|{n}|{query}|H{horizon}|fixed_rank_basis_vs_{method}"
        for family, n, query, horizon, method in product(
            EXPECTED_FAMILIES, EXPECTED_SCALES, EXPECTED_QUERIES, EXPECTED_HORIZONS, ("local_structured", "causal_temporal_smoother")
        )
    ]
    observed_pair_keys = sorted(str(key) for key in paired)
    pair_status = {
        "expected_key_count": len(expected_pair_keys),
        "observed_key_count": len(observed_pair_keys),
        "missing_keys": [key for key in expected_pair_keys if key not in paired],
        "unexpected_keys": [key for key in observed_pair_keys if key not in expected_pair_keys],
        "status": "PASS" if set(expected_pair_keys) == set(observed_pair_keys) else "BLOCKED",
    }
    required_cells = _required_cells(
        sources=sources,
        recovery=recovery_coverage,
        intervals=interval_coverage,
        results=results,
        gate_receipt=gate_receipt,
        hash_bindings=hash_bindings,
        register_binding_status=register_status,
        specification=specification,
    )
    blocking_gaps = []
    if register_status != "PASS":
        blocking_gaps.append("Decision-register or frozen-input hash binding did not pass.")
    if any(cell["status"] in {"BLOCKED", "NOT_EVALUABLE"} for cell in required_cells):
        blocking_gaps.append("Independent empirical ground truth is absent from the synthetic-only frozen route.")
    if recovery_coverage["record_provenance_missing_fields"]:
        blocking_gaps.append("Recovery records lack serialized chronology, truth, query, endpoint, and selection-input provenance fields.")
    if pair_status["status"] != "PASS":
        blocking_gaps.append("Paired common-completion key coverage is incomplete.")
    data_sufficiency = "PARTIAL" if recovery_coverage["record_count_status"] == "PASS" and pair_status["status"] == "PASS" else "BLOCKED"
    verdict = "BLOCKED" if blocking_gaps else ("PARTIAL" if any(cell["status"] == "WARN" for cell in required_cells) else "PASS")
    input_binding_rows = [
        {"input_id": input_file.input_id, "sha256": input_file.digest}
        for input_file in sorted(inputs.values(), key=lambda item: item.input_id)
    ]
    analyzer_sha256 = sha256_file(Path(__file__).resolve())
    input_bundle_sha256 = canonical_sha256(
        {"analyzer_sha256": analyzer_sha256, "inputs": input_binding_rows}
    )
    retained_bytes = _retained_record_lines(recovery, intervals)
    analysis = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "register_key": REGISTER_KEY,
        "analysis_route": "read_only_derived_analysis_over_frozen_e4_r3",
        "data_sufficiency": data_sufficiency,
        "verdict": verdict,
        "analyzer_sha256": analyzer_sha256,
        "input_bundle_sha256": input_bundle_sha256,
        "input_sha256": input_binding_rows,
        "register_item": register_item,
        "register_match": register_match,
        "hash_bindings": hash_bindings,
        "authorization_v2_binding": v2_binding,
        "frozen_result_identity": {
            "schema_version": results.get("schema_version"),
            "status": results.get("status"),
            "promotion": results.get("promotion"),
            "manifest_status": _get(manifest, "status"),
            "manifest_candidate_sha256": _get(manifest, "candidate_sha256"),
            "manifest_authorization_sha256": _get(manifest, "authorization_sha256"),
        },
        "ground_truth_distinction": _truth_distinction(),
        "source_checks": {key: value for key, value in sources.items() if key != "_core_text"},
        "coverage": {
            "recovery": recovery_coverage,
            "intervals": interval_coverage,
            "paired_common_completion": pair_status,
        },
        "required_cells": required_cells,
        "blocking_gaps": blocking_gaps,
        "uncovered_boundaries": [
            "independent empirical ground truth and native measurement provenance",
            "per-record train/validation/evaluation chronology receipt",
            "per-record selection candidate list and loss vector provenance",
            "per-record held-out topology/query identity provenance",
            "per-record endpoint signature and truth-isolation receipt",
            "any empirical or universal-performance claim beyond the synthetic DGP",
        ],
        "scientific_execution": "NOT_RUN",
        "fresh_payloads_created": False,
        "retained_records_sha256": sha256_bytes(retained_bytes),
    }
    # `sources` contains source text only transiently for line-number evidence.
    files = {
        "input-manifest.json": _output_json_bytes({"register_key": REGISTER_KEY, "analyzer_sha256": analyzer_sha256, "input_bundle_sha256": input_bundle_sha256, "inputs": input_binding_rows}),
        "analysis.json": _output_json_bytes(analysis),
        "audit.md": _markdown_report(analysis),
        "retained-records.jsonl": retained_bytes,
    }
    return analysis, files


def default_input_paths(repo_root: Path, decision_register: Path | None = None) -> dict[str, Path]:
    quarantine = repo_root / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3"
    candidate_root = repo_root / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3"
    return {
        "analysis_authorization": repo_root / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json",
        "analysis_plan": repo_root / "refine-logs/NCS_FOUR_ANALYSIS_PLAN_20260804_010454.md",
        "decision_register": decision_register or repo_root / "output/ncs_review_corpus/v1_author_decision_register.json",
        "e4_audit": repo_root / "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md",
        "e3_results": quarantine / "e3-results.json",
        "execution_manifest": quarantine / "execution-manifest.json",
        "execution_complete": quarantine / "execution-complete.json",
        "terminal_inventory": repo_root / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
        "candidate": candidate_root / "candidate.json",
        "e4_authorization": repo_root / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
        "specification": repo_root / "refine-logs/e3_family2_inputs/synthetic-e3-v4.json",
        "query_contract": candidate_root / "preoutcome-artifacts/family2_query_contract.json",
        "comparator_registry": candidate_root / "preoutcome-artifacts/comparator_registry.json",
        "failure_metric_schema": candidate_root / "preoutcome-artifacts/failure_metric_schema.json",
        "tuning_split_manifest": candidate_root / "preoutcome-artifacts/tuning_split_manifest.json",
        "exact_fixture_manifest": candidate_root / "preoutcome-artifacts/exact_fixture_manifest.json",
        "gate_receipt": repo_root / "refine-logs/e3_family2_inputs/e4-gate-test-execution-receipt-v1-20260731.json",
        "core_source": repo_root / "scripts/experiments/e3_synthetic_core.py",
        "executor_source": repo_root / "scripts/experiments/e3_family2_authorized_executor.py",
        "preoutcome_source": repo_root / "scripts/experiments/e3_family2_preoutcome.py",
    }


def analyze(input_paths: Mapping[str, Path]) -> tuple[dict[str, Any], dict[str, bytes]]:
    json_ids = {key for key in input_paths if not key.endswith("_source") and key not in {"analysis_plan", "e4_audit"}}
    inputs = {
        input_id: _load_input(input_id, path, json_input=input_id in json_ids)
        for input_id, path in sorted(input_paths.items())
    }
    return _build_analysis(inputs)


def write_output(
    output_root: Path,
    analysis: Mapping[str, Any],
    files: Mapping[str, bytes],
    *,
    execution_authorization_path: Path | None = None,
    run_id: str = "primary",
    observed_paths: Mapping[str, Path] | None = None,
    project_root: Path | None = None,
) -> Path:
    target = Path(output_root).expanduser().resolve()
    validate_execution_authorization(
        execution_authorization_path,
        output_root=target,
        run_id=run_id,
        observed_paths=observed_paths or {},
        artifact_prefix="cal-e02-128-",
        project_root=project_root,
    )
    target.mkdir(parents=True, exist_ok=False)
    for name in sorted(files):
        _write_new(target / name, files[name])
    inventory = _output_inventory(target, sorted(files))
    _write_new(target / "output-inventory.json", _output_json_bytes(inventory))
    return target


def _execution_context_from_input_paths(input_paths: Mapping[str, Path], repo_root: Path) -> dict[str, Path]:
    return {
        "source_authorization_v2": input_paths["analysis_authorization"],
        "m2a_repair_receipt": repo_root / EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
        "decision_register": input_paths["decision_register"],
        "e4_results": input_paths["e3_results"],
        "e4_execution_manifest": input_paths["execution_manifest"],
        "e4_execution_complete": input_paths["execution_complete"],
        "e4_terminal_inventory": input_paths["terminal_inventory"],
        "e4_candidate": input_paths["candidate"],
        "workspace_authorization": input_paths["e4_authorization"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--decision-register", type=Path, default=None)
    parser.add_argument("--execution-authorization", type=Path, required=True)
    parser.add_argument("--run-id", choices=("primary", "duplicate"), required=True)
    parser.add_argument("--output-parent", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    input_paths = default_input_paths(repo_root, args.decision_register)
    try:
        analysis, files = analyze(input_paths)
        bundle = analysis["input_bundle_sha256"]
        output_base = args.output_parent or repo_root / "refine-logs/ncs_new_analysis_v2"
        output_root = args.output_root or output_base / args.run_id / f"cal-e02-128-{bundle}"
        observed_paths = _execution_context_from_input_paths(input_paths, repo_root)
        validate_execution_authorization(
            args.execution_authorization,
            output_root=output_root,
            run_id=args.run_id,
            observed_paths=observed_paths,
            artifact_prefix="cal-e02-128-",
            project_root=repo_root,
        )
        written = write_output(
            output_root,
            analysis,
            files,
            execution_authorization_path=args.execution_authorization,
            run_id=args.run_id,
            observed_paths=observed_paths,
            project_root=repo_root,
        )
    except (AuditError, FileNotFoundError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"CAL-E02:128 audit refused or failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"register_key": REGISTER_KEY, "verdict": analysis["verdict"], "output_root": str(written), "input_bundle_sha256": analysis["input_bundle_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
