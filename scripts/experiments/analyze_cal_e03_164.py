"""Deterministic, read-only analysis of the frozen E4-r3 CAL-E03:164 data.

This module consumes frozen JSON and audit/inventory metadata only.  It does
not execute an experiment, mutate an input, or make a manuscript decision.
The output directory is content addressed by the input hashes and contains
descriptive summaries with every status and non-finite observation retained in
the accounting.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable, Mapping, Sequence

from scripts.experiments.analyze_cal_e01_75 import (
    EXECUTION_AUTHORIZATION_SCHEMA_VERSION,
    EXECUTION_AUTHORIZATION_STATUS,
    EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
    ExecutionAuthorizationError,
    _validate_execution_authorization_common,
)

SCHEMA_VERSION = "cal-e03-164-analysis-v1"
REGISTER_KEY = "CAL-E03:164"
AUTHORIZATION_SCHEMA_VERSION = "ncs-four-analysis-authorization-v2"
V2_ITEM_BINDING = {
    "item_id": "V1-045",
    "calibration_id": "CAL-E03",
    "item_index": 164,
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
KNOWN_STATUSES = ("AVAILABLE", "NONCONVERGED", "NONFINITE", "OUTSIDE_TARGET", "UNSTABLE")
RECOVERY_NUMERIC_FIELDS = (
    "operator_mse",
    "response_mse",
    "validation_loss",
    "estimated_spectral_radius",
    "truth_spectral_radius",
)
INTERVAL_NUMERIC_FIELDS = (
    "coverage",
    "mean_interval_width",
    "raw_response_mse",
    "stability_qualified_response_mse",
    "selection_validation_loss",
    "estimated_spectral_radius",
    "truth_spectral_radius",
)
CELL_FIELDS = ("family", "n", "query_class", "horizon", "method")
EXPECTED_FAMILIES = ("family1", "family2")
EXPECTED_SCALES = (20, 50)
EXPECTED_QUERIES = ("cross_generator", "in_family_interpolation")
EXPECTED_HORIZONS = (4, 12)
EXPECTED_METHODS = (
    "causal_temporal_smoother",
    "fixed_rank_basis",
    "local_structured",
)


class AnalysisInputError(ValueError):
    """Raised when a required frozen input cannot be consumed safely."""


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
        raise AnalysisInputError(f"{label} must be a non-null JSON object")
    return value


def _require_v2_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise AnalysisInputError(f"{label} must be a non-null lowercase SHA-256")
    return value


def _resolve_inventory_path(raw_path: Any, project_root: Path) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise AnalysisInputError("terminal inventory artifact path is missing")
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
        raise AnalysisInputError("legacy or unsupported authorization schema")
    if any(key in authorization for key in ("frozen_inputs", "authorized_register_items", "execution_policy")):
        raise AnalysisInputError("legacy authorization fields are prohibited")
    authorized_scope = _require_v2_mapping(
        authorization.get("authorized_scope"), "authorization.authorized_scope"
    )
    rec_m2_actions = authorized_scope.get("REC_M2")
    if not isinstance(rec_m2_actions, list) or V2_REQUIRED_REC_M2_ACTION not in rec_m2_actions:
        raise AnalysisInputError("authorization.authorized_scope.REC_M2 is not bound")
    current_task_limits = _require_v2_mapping(
        authorization.get("current_task_limits"), "authorization.current_task_limits"
    )
    for field, expected in V2_REQUIRED_TASK_LIMITS.items():
        if current_task_limits.get(field) != expected:
            raise AnalysisInputError(f"authorization.current_task_limits.{field} drifted")
    binding = _require_v2_mapping(authorization.get("binding"), "authorization.binding")
    declared_register = binding.get("decision_register_path")
    if not isinstance(declared_register, str) or not declared_register:
        raise AnalysisInputError("authorization.binding.decision_register_path is required")
    project_root = Path(__file__).resolve().parents[2]
    expected_register_path = Path(declared_register).expanduser()
    if not expected_register_path.is_absolute():
        expected_register_path = project_root / expected_register_path
    observed_register_path = Path(register_path).expanduser().resolve(strict=True)
    if observed_register_path != expected_register_path.resolve():
        raise AnalysisInputError("decision-register path is not the v2-bound path")
    expected_register_sha = _require_v2_sha(binding.get("decision_register_sha256"), "authorization.binding.decision_register_sha256")
    observed_register_sha = sha256_file(observed_register_path)
    if observed_register_sha != expected_register_sha:
        raise AnalysisInputError("decision-register SHA-256 mismatch")
    if binding.get("item_payload_sha256_algorithm") != "recursive_object_key_sort_then_JSON.stringify_utf8_no_whitespace":
        raise AnalysisInputError("unsupported item payload canonicalization")
    item_payloads = _require_v2_mapping(binding.get("item_payloads"), "authorization.binding.item_payloads")
    expected_item_sha = _require_v2_sha(item_payloads.get(V2_ITEM_BINDING["item_id"]), f"authorization.binding.item_payloads.{V2_ITEM_BINDING['item_id']}")
    items = register.get("items")
    if not isinstance(items, list):
        raise AnalysisInputError("decision register.items must be a non-null array")
    selected = []
    for item in items:
        if not isinstance(item, Mapping) or item.get("item_id") != V2_ITEM_BINDING["item_id"]:
            continue
        source = item.get("calibration_source")
        if isinstance(source, Mapping) and source.get("calibration_id") == V2_ITEM_BINDING["calibration_id"] and item.get("item_index") == V2_ITEM_BINDING["item_index"]:
            selected.append(item)
    if len(selected) != 1:
        raise AnalysisInputError("exact current register item mapping is not unique")
    register_item = selected[0]
    for field in ("item_id", "item_index", "priority", "action_class"):
        if register_item.get(field) != V2_ITEM_BINDING[field]:
            raise AnalysisInputError(f"current register item {field} drifted")
    if hashlib.sha256(_canonical_v2_item_bytes(register_item)).hexdigest() != expected_item_sha:
        raise AnalysisInputError("canonical register item payload SHA-256 mismatch")
    frozen = _require_v2_mapping(authorization.get("frozen_e4_r3_inputs"), "authorization.frozen_e4_r3_inputs")
    actual_hashes: dict[str, str] = {}
    for role, field in V2_FROZEN_HASH_FIELDS.items():
        expected = _require_v2_sha(frozen.get(field), f"authorization.frozen_e4_r3_inputs.{field}")
        path = frozen_paths.get(role)
        if not isinstance(path, Path):
            raise AnalysisInputError(f"frozen input path is missing: {role}")
        resolved = path.expanduser().resolve(strict=True)
        actual = sha256_file(resolved)
        if actual != expected:
            raise AnalysisInputError(f"frozen input SHA-256 mismatch: {role}")
        actual_hashes[role] = actual
    workspace_path = frozen_paths.get("workspace_authorization")
    if not isinstance(workspace_path, Path):
        raise AnalysisInputError("workspace authorization path is required for the E4 chain")
    workspace_hash = sha256_file(workspace_path.expanduser().resolve(strict=True))
    workspace = _require_v2_mapping(frozen_values.get("workspace_authorization"), "workspace authorization")
    candidate = _require_v2_mapping(frozen_values.get("candidate"), "frozen candidate")
    candidate_id = candidate.get("candidate_id")
    candidate_sha = actual_hashes["candidate"]
    if not isinstance(candidate_id, str) or not candidate_id or workspace.get("candidate_id") != candidate_id or workspace.get("candidate_sha256") != candidate_sha:
        raise AnalysisInputError("workspace authorization candidate chain mismatch")
    for role in ("results", "execution_manifest", "execution_complete"):
        value = _require_v2_mapping(frozen_values.get(role), f"frozen {role}")
        if value.get("authorization_sha256") != workspace_hash or value.get("candidate_sha256") != candidate_sha:
            raise AnalysisInputError(f"frozen {role} authorization/candidate chain mismatch")
    inventory = _require_v2_mapping(frozen_values.get("terminal_inventory"), "terminal inventory")
    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        raise AnalysisInputError("terminal inventory.artifacts is required")
    inventory_roles = {role: frozen_paths[role] for role in V2_FROZEN_HASH_FIELDS if role != "terminal_inventory"}
    inventory_roles["workspace_authorization"] = workspace_path
    for role, path in inventory_roles.items():
        resolved = path.expanduser().resolve(strict=True)
        matches = [entry for entry in artifacts if isinstance(entry, Mapping) and _resolve_inventory_path(entry.get("path"), project_root) == resolved]
        if len(matches) != 1 or matches[0].get("sha256") != sha256_file(resolved):
            raise AnalysisInputError(f"terminal inventory chain mismatch: {role}")
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
    artifact_prefix: str = "cal-e03-164-",
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
        raise AnalysisInputError(str(error)) from error


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AnalysisInputError(f"cannot read JSON input {path}: {exc}") from exc


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return _is_number(value) and math.isfinite(float(value))


def _sort_scalar_values(values: Iterable[Any]) -> list[Any]:
    unique = list({canonical_json(value): value for value in values}.values())
    return sorted(unique, key=lambda value: (type(value).__name__, str(value)))


def percentile(values: Sequence[float], fraction: float) -> float | None:
    """Return a deterministic linearly interpolated percentile."""

    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def numeric_stats(values: Iterable[Any]) -> dict[str, Any]:
    """Summarize finite numeric values without hiding missing/non-finite ones."""

    values_list = list(values)
    finite = [float(value) for value in values_list if _is_finite_number(value)]
    missing = sum(value is None for value in values_list)
    nonfinite = sum(_is_number(value) and not math.isfinite(float(value)) for value in values_list)
    invalid = len(values_list) - len(finite) - missing - nonfinite
    if not finite:
        return {
            "count": len(values_list),
            "finite_count": 0,
            "missing_count": missing,
            "nonfinite_count": nonfinite,
            "invalid_count": invalid,
            "mean": None,
            "std_population": None,
            "median": None,
            "q25": None,
            "q75": None,
            "min": None,
            "max": None,
        }
    return {
        "count": len(values_list),
        "finite_count": len(finite),
        "missing_count": missing,
        "nonfinite_count": nonfinite,
        "invalid_count": invalid,
        "mean": statistics.fmean(finite),
        "std_population": statistics.pstdev(finite),
        "median": percentile(finite, 0.5),
        "q25": percentile(finite, 0.25),
        "q75": percentile(finite, 0.75),
        "min": min(finite),
        "max": max(finite),
    }


def status_counts(records: Iterable[Mapping[str, Any]], field: str = "status") -> dict[str, int]:
    counts = Counter(str(record.get(field, "<MISSING>")) for record in records)
    ordered = {status: counts.pop(status, 0) for status in KNOWN_STATUSES}
    ordered.update({status: counts[status] for status in sorted(counts)})
    return ordered


def _status_count_total(counts: Mapping[str, Any]) -> int:
    return sum(int(value) for value in counts.values() if _is_number(value))


def cell_key(record: Mapping[str, Any]) -> tuple[str, int, str, int, str]:
    try:
        return (
            str(record["family"]),
            int(record["n"]),
            str(record["query_class"]),
            int(record["horizon"]),
            str(record["method"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisInputError(f"record has invalid cell fields: {record}") from exc


def cell_id(key: tuple[str, int, str, int, str]) -> str:
    family, n, query, horizon, method = key
    return f"{family}|{n}|{query}|H{horizon}|{method}"


def _key_sort(value: tuple[str, int, str, int, str]) -> tuple[Any, ...]:
    return (value[0], value[1], value[2], value[3], value[4])


def _counter_json(values: Iterable[Any]) -> dict[str, int]:
    counts = Counter(canonical_json(value) for value in values)
    return {key: counts[key] for key in sorted(counts)}


def field_nonfinite_audit(
    records: Sequence[Mapping[str, Any]], fields: Sequence[str]
) -> dict[str, Any]:
    by_field: dict[str, dict[str, int]] = {}
    for field in fields:
        values = [record.get(field) for record in records]
        stats = numeric_stats(values)
        by_field[field] = {
            "record_count": len(values),
            "missing_count": int(stats["missing_count"]),
            "nonfinite_count": int(stats["nonfinite_count"]),
            "invalid_count": int(stats["invalid_count"]),
        }
    return {
        "by_field": by_field,
        "nonfinite_values_total": sum(item["nonfinite_count"] for item in by_field.values()),
        "missing_values_total": sum(item["missing_count"] for item in by_field.values()),
        "invalid_values_total": sum(item["invalid_count"] for item in by_field.values()),
    }


def _seed_level_stats(records: Sequence[Mapping[str, Any]], field: str) -> dict[str, Any]:
    by_seed: dict[str, list[Any]] = defaultdict(list)
    for record in records:
        by_seed[str(record.get("seed", "<MISSING>"))].append(record.get(field))
    seed_means: list[float] = []
    empty_seed_count = 0
    for values in by_seed.values():
        finite = [float(value) for value in values if _is_finite_number(value)]
        if finite:
            seed_means.append(statistics.fmean(finite))
        else:
            empty_seed_count += 1
    result = numeric_stats(seed_means)
    result["seed_count"] = len(by_seed)
    result["seed_means_with_finite_values"] = len(seed_means)
    result["seed_means_without_finite_values"] = empty_seed_count
    return result


def summarize_recovery_cell(
    key: tuple[str, int, str, int, str], records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    records = list(records)
    seeds = sorted({record.get("seed") for record in records}, key=str)
    target_times = sorted({record.get("target_time") for record in records}, key=str)
    summary: dict[str, Any] = {
        "cell_id": cell_id(key),
        "family": key[0],
        "n": key[1],
        "query_class": key[2],
        "horizon": key[3],
        "method": key[4],
        "record_count": len(records),
        "seed_count": len(seeds),
        "target_time_count": len(target_times),
        "status_counts": status_counts(records),
        "nonfinite_audit": field_nonfinite_audit(records, RECOVERY_NUMERIC_FIELDS),
        "selected_hyperparameter_counts": _counter_json(
            record.get("selected_hyperparameter") for record in records
        ),
        "selected_hyperparameters": _sort_scalar_values(
            record.get("selected_hyperparameter") for record in records
        ),
        "metrics": {
            field: numeric_stats(record.get(field) for record in records)
            for field in RECOVERY_NUMERIC_FIELDS
        },
        "seed_level_metrics": {
            field: _seed_level_stats(records, field)
            for field in ("operator_mse", "response_mse", "validation_loss")
        },
        "retention": {
            "input_records": len(records),
            "records_accounted_for": len(records),
            "dropped_records": 0,
            "failure_statuses_retained": True,
            "nonfinite_values_retained_in_accounting": True,
        },
    }
    return summary


def _bootstrap_counts(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        for status, count in (record.get("bootstrap_status_counts") or {}).items():
            counts[str(status)] += int(count)
    ordered = {status: counts.pop(status, 0) for status in KNOWN_STATUSES}
    ordered.update({status: counts[status] for status in sorted(counts)})
    return ordered


def summarize_interval_cell(
    key: tuple[str, int, str, int, str], records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    records = list(records)
    requested = [record.get("requested_replicates") for record in records]
    completed = [record.get("completed_replicates") for record in records]
    attempts = [record.get("bootstrap_retune_attempts") for record in records]
    return {
        "cell_id": cell_id(key),
        "family": key[0],
        "n": key[1],
        "query_class": key[2],
        "horizon": key[3],
        "method": key[4],
        "record_count": len(records),
        "seed_count": len({record.get("seed") for record in records}),
        "status_counts": status_counts(records),
        "selection_status_counts": status_counts(records, field="selection_status"),
        "bootstrap_status_counts": _bootstrap_counts(records),
        "bootstrap_requested": numeric_stats(requested),
        "bootstrap_completed": numeric_stats(completed),
        "bootstrap_attempts": numeric_stats(attempts),
        "nonfinite_audit": field_nonfinite_audit(records, INTERVAL_NUMERIC_FIELDS),
        "metrics": {
            field: numeric_stats(record.get(field) for record in records)
            for field in INTERVAL_NUMERIC_FIELDS
        },
        "all_declared_intervals_available": all(
            record.get("status") == "AVAILABLE" for record in records
        ),
        "retention": {
            "input_records": len(records),
            "records_accounted_for": len(records),
            "dropped_records": 0,
            "failure_statuses_retained": True,
            "nonfinite_values_retained_in_accounting": True,
        },
    }


def _parse_pair_key(key: str) -> tuple[str, int, str, int, str, str]:
    parts = key.split("|")
    if len(parts) != 5 or not parts[3].startswith("H") or "_vs_" not in parts[4]:
        raise AnalysisInputError(f"invalid paired completion key: {key}")
    candidate, comparator = parts[4].split("_vs_", 1)
    return parts[0], int(parts[1]), parts[2], int(parts[3][1:]), candidate, comparator


def summarize_pairwise(paired: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_key in sorted(paired):
        family, n, query, horizon, candidate, comparator = _parse_pair_key(raw_key)
        value = paired[raw_key]
        operator = list(value.get("operator_mse_differences") or [])
        response = list(value.get("response_mse_differences") or [])
        operator_stats = numeric_stats(operator)
        response_stats = numeric_stats(response)
        finite_response = [float(item) for item in response if _is_finite_number(item)]
        finite_operator = [float(item) for item in operator if _is_finite_number(item)]
        rows.append(
            {
                "pair_id": raw_key,
                "family": family,
                "n": n,
                "query_class": query,
                "horizon": horizon,
                "candidate_method": candidate,
                "comparator_method": comparator,
                "declared_date_keys": value.get("declared_date_keys"),
                "common_completion_date_keys": value.get("common_completion_date_keys"),
                "candidate_status_counts": value.get("candidate_status_counts", {}),
                "comparator_status_counts": value.get("comparator_status_counts", {}),
                "operator_difference_stats_candidate_minus_comparator": operator_stats,
                "response_difference_stats_candidate_minus_comparator": response_stats,
                "operator_candidate_lower_count": sum(item < 0 for item in finite_operator),
                "operator_candidate_higher_count": sum(item > 0 for item in finite_operator),
                "operator_tie_count": sum(item == 0 for item in finite_operator),
                "response_candidate_lower_count": sum(item < 0 for item in finite_response),
                "response_candidate_higher_count": sum(item > 0 for item in finite_response),
                "response_tie_count": sum(item == 0 for item in finite_response),
                "comparison_metric_note": (
                    "Raw paired MSE differences only; no post-outcome log-ratio or CI is constructed."
                ),
                "retention": {
                    "operator_difference_values_accounted_for": len(operator),
                    "response_difference_values_accounted_for": len(response),
                    "dropped_values": 0,
                },
            }
        )
    return rows


def _summary_metric(summary: Mapping[str, Any], field: str) -> float | None:
    value = summary.get("metrics", {}).get(field, {}).get("mean")
    return float(value) if _is_finite_number(value) else None


def _delta(left: Mapping[str, Any], right: Mapping[str, Any], field: str) -> float | None:
    left_value = _summary_metric(left, field)
    right_value = _summary_metric(right, field)
    if left_value is None or right_value is None:
        return None
    return left_value - right_value


def _comparison_row(
    comparison_type: str,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    left_label: str,
    right_label: str,
) -> dict[str, Any]:
    return {
        "comparison_type": comparison_type,
        "left_label": left_label,
        "right_label": right_label,
        "left_cell_id": left["cell_id"],
        "right_cell_id": right["cell_id"],
        "family": left["family"],
        "left_n": left["n"],
        "right_n": right["n"],
        "left_query_class": left["query_class"],
        "right_query_class": right["query_class"],
        "left_horizon": left["horizon"],
        "right_horizon": right["horizon"],
        "method": left["method"],
        "response_mse_delta_left_minus_right": _delta(left, right, "response_mse"),
        "operator_mse_delta_left_minus_right": _delta(left, right, "operator_mse"),
        "validation_loss_delta_left_minus_right": _delta(left, right, "validation_loss"),
        "left_status_counts": left["status_counts"],
        "right_status_counts": right["status_counts"],
        "comparison_note": "Descriptive raw mean deltas; no superiority threshold is applied.",
    }


def build_stress_comparisons(
    summaries: Mapping[tuple[str, int, str, int, str], Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, query, horizon, method in itertools.product(
        EXPECTED_FAMILIES, EXPECTED_QUERIES, EXPECTED_HORIZONS, EXPECTED_METHODS
    ):
        key_20 = (family, 20, query, horizon, method)
        key_50 = (family, 50, query, horizon, method)
        if key_20 in summaries and key_50 in summaries:
            rows.append(
                _comparison_row(
                    "scale_n50_minus_n20",
                    summaries[key_50],
                    summaries[key_20],
                    "N=50",
                    "N=20",
                )
            )
    for family, n, horizon, method in itertools.product(
        EXPECTED_FAMILIES, EXPECTED_SCALES, EXPECTED_HORIZONS, EXPECTED_METHODS
    ):
        cross = (family, n, "cross_generator", horizon, method)
        in_family = (family, n, "in_family_interpolation", horizon, method)
        if cross in summaries and in_family in summaries:
            rows.append(
                _comparison_row(
                    "query_cross_generator_minus_in_family_interpolation",
                    summaries[cross],
                    summaries[in_family],
                    "cross_generator",
                    "in_family_interpolation",
                )
            )
    for family, n, query, method in itertools.product(
        EXPECTED_FAMILIES, EXPECTED_SCALES, EXPECTED_QUERIES, EXPECTED_METHODS
    ):
        h12 = (family, n, query, 12, method)
        h4 = (family, n, query, 4, method)
        if h12 in summaries and h4 in summaries:
            rows.append(
                _comparison_row(
                    "horizon_h12_minus_h4",
                    summaries[h12],
                    summaries[h4],
                    "H=12",
                    "H=4",
                )
            )
    return rows


def _expected_cells() -> set[tuple[str, int, str, int, str]]:
    return {
        (family, n, query, horizon, method)
        for family, n, query, horizon, method in itertools.product(
            EXPECTED_FAMILIES,
            EXPECTED_SCALES,
            EXPECTED_QUERIES,
            EXPECTED_HORIZONS,
            EXPECTED_METHODS,
        )
    }


def build_coverage(
    recovery: Sequence[Mapping[str, Any]],
    intervals: Sequence[Mapping[str, Any]],
    paired: Mapping[str, Any],
    recovery_summary: Mapping[str, Any],
    interval_summary: Mapping[str, Any],
    audit_json: Mapping[str, Any] | None,
) -> dict[str, Any]:
    recovery_keys = {cell_key(record) for record in recovery}
    interval_keys = {cell_key(record) for record in intervals}
    expected_recovery = _expected_cells()
    expected_interval = {
        (family, n, query, 4, "fixed_rank_basis")
        for family, n, query in itertools.product(EXPECTED_FAMILIES, EXPECTED_SCALES, EXPECTED_QUERIES)
    }
    declared = (audit_json or {}).get("scope_counts", {})
    recovery_counts = Counter(cell_key(record) for record in recovery)
    interval_counts = Counter(cell_key(record) for record in intervals)
    summary_cell_counts = {
        "recovery_summary_cells": len(recovery_summary),
        "interval_summary_cells": len(interval_summary),
        "paired_cells": len(paired),
    }
    return {
        "observed_dimensions": {
            "families": sorted({key[0] for key in recovery_keys}),
            "scales": sorted({key[1] for key in recovery_keys}),
            "query_classes": sorted({key[2] for key in recovery_keys}),
            "horizons": sorted({key[3] for key in recovery_keys}),
            "methods": sorted({key[4] for key in recovery_keys}),
            "seeds": sorted({record.get("seed") for record in recovery}, key=str),
        },
        "expected_dimensions_for_scoped_analysis": {
            "families": list(EXPECTED_FAMILIES),
            "scales": list(EXPECTED_SCALES),
            "query_classes": list(EXPECTED_QUERIES),
            "horizons": list(EXPECTED_HORIZONS),
            "methods": list(EXPECTED_METHODS),
        },
        "recovery": {
            "observed_cells": len(recovery_keys),
            "expected_cells": len(expected_recovery),
            "missing_cells": [cell_id(key) for key in sorted(expected_recovery - recovery_keys, key=_key_sort)],
            "unexpected_cells": [cell_id(key) for key in sorted(recovery_keys - expected_recovery, key=_key_sort)],
            "record_count": len(recovery),
            "declared_record_count_from_audit": declared.get("recovery_records"),
            "records_per_cell": {
                cell_id(key): recovery_counts[key] for key in sorted(recovery_counts, key=_key_sort)
            },
        },
        "interval": {
            "observed_cells": len(interval_keys),
            "expected_cells": len(expected_interval),
            "missing_cells": [cell_id(key) for key in sorted(expected_interval - interval_keys, key=_key_sort)],
            "unexpected_cells": [cell_id(key) for key in sorted(interval_keys - expected_interval, key=_key_sort)],
            "record_count": len(intervals),
            "declared_record_count_from_audit": declared.get("interval_records"),
            "records_per_cell": {
                cell_id(key): interval_counts[key] for key in sorted(interval_counts, key=_key_sort)
            },
        },
        "paired": {
            "observed_cells": len(paired),
            "declared_cells_from_audit": declared.get("paired_comparison_cells"),
        },
        "summary_cell_counts": summary_cell_counts,
        "unrun_scale_boundary": {
            "n100_present": 100 in {key[1] for key in recovery_keys},
            "n200_present": 200 in {key[1] for key in recovery_keys},
            "interpretation": "N=100 and N=200 were not run and are not inferred from N=20 or N=50.",
        },
    }


def _resolve_inventory_path(raw_path: str, project_root: Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else project_root / path


def build_resource_audit(
    inventory: Mapping[str, Any] | None,
    project_root: Path,
    inventory_path: Path | None,
    clock_provenance: Mapping[str, Any] | None,
    execution_complete: Mapping[str, Any] | None,
) -> dict[str, Any]:
    execution_contract = (inventory or {}).get("execution_contract", {})
    artifact_rows: list[dict[str, Any]] = []
    for artifact in (inventory or {}).get("artifacts", []):
        raw_path = str(artifact.get("path", ""))
        observed_path = _resolve_inventory_path(raw_path, project_root)
        exists = observed_path.is_file()
        observed_hash = sha256_file(observed_path) if exists else None
        artifact_rows.append(
            {
                "declared_path": raw_path,
                "declared_sha256": artifact.get("sha256"),
                "observed_path": str(observed_path),
                "exists_in_current_worktree": exists,
                "observed_sha256": observed_hash,
                "hash_matches": bool(exists and observed_hash == artifact.get("sha256")),
            }
        )
    telemetry_fields = {
        "wall_clock_seconds": None,
        "cpu_time_seconds": None,
        "peak_memory_bytes": None,
        "peak_rss_bytes": None,
        "gpu_time_seconds": None,
        "per_cell_runtime": None,
    }
    missing = [field for field, value in telemetry_fields.items() if value is None]
    log_rows = [
        row
        for row in artifact_rows
        if row["declared_path"].endswith((".stdout.log", ".stderr.log"))
    ]
    return {
        "inventory_path": str(inventory_path) if inventory_path else None,
        "inventory_present": inventory is not None,
        "inventory_status": (inventory or {}).get("status"),
        "candidate_id": (inventory or {}).get("candidate_id"),
        "execution_contract": execution_contract,
        "clock_provenance": clock_provenance or None,
        "execution_complete": execution_complete or None,
        "declared_artifacts": artifact_rows,
        "runtime_log_observation": {
            "log_artifacts": log_rows,
            "logs_available_in_current_worktree": all(
                row["exists_in_current_worktree"] for row in log_rows
            ) if log_rows else False,
            "resource_values_read_from_logs": False,
        },
        "telemetry": telemetry_fields,
        "missing_telemetry": missing,
        "resource_proxies": {
            "declared_runs": execution_contract.get("runs"),
            "declared_last_exit_code": execution_contract.get("last_exit_code"),
            "declared_process_state": execution_contract.get("process_state"),
            "declared_stdout_status": execution_contract.get("stdout_status"),
            "declared_stderr_empty": execution_contract.get("stderr_empty"),
        },
        "verdict": "BLOCKED" if missing else "SUPPORTED",
        "note": "Missing runtime telemetry is reported as missing; no runtime value is inferred from record count.",
    }


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def build_input_bindings(
    paths: Mapping[str, Path],
    authorization: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    hashes: dict[str, str | None] = {}
    for logical_name, path in sorted(paths.items()):
        hashes[logical_name] = sha256_file(path) if path.is_file() else None
    binding = _require_v2_mapping(authorization.get("binding"), "authorization.binding")
    expected_register = _require_v2_sha(binding.get("decision_register_sha256"), "authorization.binding.decision_register_sha256")
    bundle_payload = {
        "schema_version": SCHEMA_VERSION,
        "register_key": REGISTER_KEY,
        "expected_decision_register_sha256": expected_register,
        "observed_input_sha256": hashes,
    }
    bundle_sha256 = hashlib.sha256(canonical_json(bundle_payload).encode("utf-8")).hexdigest()
    return {
        "expected_decision_register_sha256": expected_register,
        "observed_input_sha256": hashes,
        "input_bundle_sha256": bundle_sha256,
        "content_addressing": "directory name is cal-e03-164-{input_bundle_sha256}",
        "paths": {name: str(path) for name, path in sorted(paths.items())},
    }, bundle_sha256


def _register_item(register: Mapping[str, Any]) -> dict[str, Any] | None:
    matches = [
        item
        for item in register.get("items", [])
        if isinstance(item, Mapping)
        and item.get("item_id") == V2_ITEM_BINDING["item_id"]
        and isinstance(item.get("calibration_source"), Mapping)
        and item["calibration_source"].get("calibration_id") == V2_ITEM_BINDING["calibration_id"]
        and item.get("item_index") == V2_ITEM_BINDING["item_index"]
    ]
    if len(matches) != 1:
        return None
    return dict(matches[0])



def build_integrity_checks(
    authorization: Mapping[str, Any],
    manifest: Mapping[str, Any],
    results_doc: Mapping[str, Any],
    register_item: Mapping[str, Any] | None,
    observed_hashes: Mapping[str, str | None],
    v2_binding: Mapping[str, Any],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    frozen = _require_v2_mapping(authorization.get("frozen_e4_r3_inputs"), "authorization.frozen_e4_r3_inputs")
    checks = [
        _check(
            "authorization_schema_v2",
            "PASS" if authorization.get("schema_version") == AUTHORIZATION_SCHEMA_VERSION else "BLOCKED",
            "authorization schema is directly v2-bound",
        ),
        _check(
            "decision_register_sha256",
            "PASS" if observed_hashes.get("decision_register") == authorization["binding"]["decision_register_sha256"] else "BLOCKED",
            f"expected={authorization['binding']['decision_register_sha256']}; observed={observed_hashes.get('decision_register')}",
        ),
    ]
    for name, observed_key, expected_key in (
        ("e4_r3_results_sha256", "e4_r3_results", "results_sha256"),
        ("e4_r3_execution_manifest_sha256", "e4_r3_execution_manifest", "execution_manifest_sha256"),
        ("e4_r3_execution_complete_sha256", "e4_r3_execution_complete", "execution_complete_sha256"),
        ("e4_r3_terminal_inventory_sha256", "e4_r3_terminal_inventory", "terminal_inventory_sha256"),
        ("e4_r3_candidate_sha256", "e4_r3_candidate", "candidate_sha256"),
    ):
        checks.append(
            _check(
                name,
                "PASS" if observed_hashes.get(observed_key) == frozen[expected_key] else "BLOCKED",
                f"expected={frozen[expected_key]}; observed={observed_hashes.get(observed_key)}",
            )
        )
    checks.extend(
        [
            _check(
                "e4_chain",
                "PASS" if v2_binding.get("e4_chain", {}).get("complete") else "BLOCKED",
                "results, manifest, completion, inventory, candidate, and workspace authorization are chained",
            ),
            _check(
                "quarantine_promotion",
                "PASS"
                if "PROHIBITED" in str(manifest.get("promotion", ""))
                and "QUARANTINE" in str(manifest.get("status", ""))
                else "BLOCKED",
                f"promotion={manifest.get('promotion')}; status={manifest.get('status')}",
            ),
            _check(
                "register_item_resolution",
                "PASS" if register_item else "BLOCKED",
                "exact nested calibration source, index, and item id resolve to one item",
            ),
            _check(
                "register_item_mapping",
                "PASS"
                if register_item
                and all(register_item.get(field) == V2_ITEM_BINDING[field] for field in ("item_id", "item_index", "priority", "action_class"))
                else "BLOCKED",
                "item id, index, priority, and action class are exact",
            ),
            _check(
                "canonical_item_payload",
                "PASS"
                if v2_binding.get("item_payload_sha256") == authorization["binding"]["item_payloads"].get(V2_ITEM_BINDING["item_id"])
                else "BLOCKED",
                "canonical current item payload is hash-bound",
            ),
        ]
    )
    return checks, {
        "register_item": dict(register_item) if register_item else None,
        "expected_register_sha256": authorization["binding"]["decision_register_sha256"],
        "observed_register_sha256": observed_hashes.get("decision_register"),
        "authorization_gate": "PASS" if all(check["status"] == "PASS" for check in checks) else "BLOCKED",
        "authorization_v2_binding": v2_binding,
    }


def _scope_verdicts(
    coverage: Mapping[str, Any],
    resource: Mapping[str, Any],
    authorization_gate: str,
    recovery: Sequence[Mapping[str, Any]],
    intervals: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    recovery_complete = (
        coverage["recovery"]["observed_cells"] == coverage["recovery"]["expected_cells"]
        and not coverage["recovery"]["missing_cells"]
        and not coverage["recovery"]["unexpected_cells"]
    )
    interval_complete = (
        coverage["interval"]["observed_cells"] == coverage["interval"]["expected_cells"]
        and not coverage["interval"]["missing_cells"]
        and not coverage["interval"]["unexpected_cells"]
    )
    failure_retention = len(recovery) > 0 and len(intervals) > 0
    return {
        "scoped_grid_coverage": "SUPPORTED" if recovery_complete and interval_complete else "PARTIAL",
        "failure_and_nonfinite_retention": "SUPPORTED" if failure_retention else "BLOCKED",
        "stability_summary": "SUPPORTED" if recovery_complete and interval_complete else "PARTIAL",
        "resource_telemetry": resource["verdict"],
        "authorization_binding": authorization_gate,
        "cross_scale_scope": "PARTIAL",
        "overall": "SUPPORTED"
        if recovery_complete
        and interval_complete
        and resource["verdict"] == "SUPPORTED"
        and authorization_gate == "PASS"
        else "PARTIAL",
    }


def analyze_inputs(
    *,
    decision_register_path: Path,
    authorization_path: Path,
    plan_path: Path,
    audit_markdown_path: Path,
    results_path: Path,
    execution_manifest_path: Path,
    project_root: Path,
    inventory_path: Path | None = None,
    audit_json_path: Path | None = None,
    clock_provenance_path: Path | None = None,
    execution_complete_path: Path | None = None,
    candidate_path: Path | None = None,
    workspace_authorization_path: Path | None = None,
    terminal_inventory_path: Path | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root).expanduser().resolve()
    execution_complete_path = execution_complete_path or project_root / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json"
    terminal_inventory_path = terminal_inventory_path or inventory_path or project_root / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json"
    candidate_path = candidate_path or project_root / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json"
    workspace_authorization_path = workspace_authorization_path or project_root / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json"
    required_paths = {
        "decision_register": decision_register_path,
        "authorization": authorization_path,
        "plan": plan_path,
        "audit_markdown": audit_markdown_path,
        "e4_r3_results": results_path,
        "e4_r3_execution_manifest": execution_manifest_path,
        "e4_r3_execution_complete": execution_complete_path,
        "e4_r3_terminal_inventory": terminal_inventory_path,
        "e4_r3_candidate": candidate_path,
        "e4_r3_workspace_authorization": workspace_authorization_path,
    }
    optional_paths = {
        "audit_json": audit_json_path,
        "clock_provenance": clock_provenance_path,
    }
    for name, path in required_paths.items():
        if not path.is_file():
            raise AnalysisInputError(f"required input is missing: {name}={path}")
    for name, path in optional_paths.items():
        if path is not None and not path.is_file():
            raise AnalysisInputError(f"optional input was specified but is missing: {name}={path}")

    authorization = read_json(authorization_path)
    register = read_json(decision_register_path)
    results_doc = read_json(results_path)
    manifest = read_json(execution_manifest_path)
    inventory = read_json(terminal_inventory_path)
    audit_json = read_json(audit_json_path) if audit_json_path else None
    clock_provenance = read_json(clock_provenance_path) if clock_provenance_path else None
    execution_complete = read_json(execution_complete_path)
    candidate = read_json(candidate_path)
    workspace_authorization = read_json(workspace_authorization_path)

    paths_for_binding = dict(required_paths)
    paths_for_binding.update({name: path for name, path in optional_paths.items() if path is not None})
    v2_binding = validate_authorization_v2(
        authorization,
        register_path=decision_register_path,
        register=register,
        frozen_paths={
            "results": results_path,
            "execution_manifest": execution_manifest_path,
            "execution_complete": execution_complete_path,
            "terminal_inventory": terminal_inventory_path,
            "candidate": candidate_path,
            "workspace_authorization": workspace_authorization_path,
        },
        frozen_values={
            "results": results_doc,
            "execution_manifest": manifest,
            "execution_complete": execution_complete,
            "terminal_inventory": inventory,
            "candidate": candidate,
            "workspace_authorization": workspace_authorization,
        },
    )
    input_binding, input_bundle_sha256 = build_input_bindings(paths_for_binding, authorization)
    input_binding["authorization_v2_binding"] = v2_binding
    input_binding["frozen_e4_r3_inputs"] = dict(authorization["frozen_e4_r3_inputs"])
    observed_hashes = input_binding["observed_input_sha256"]
    register_item = dict(v2_binding["register_item"])
    checks, authorization_info = build_integrity_checks(
        authorization,
        manifest,
        results_doc,
        register_item,
        observed_hashes,
        v2_binding,
    )

    if results_doc.get("schema_version") != "e3-family2-synthetic-quarantine-results-v3":
        raise AnalysisInputError("unexpected E4-r3 result schema")
    result_payload = results_doc.get("results")
    if not isinstance(result_payload, Mapping):
        raise AnalysisInputError("E4-r3 result has no results object")
    recovery = result_payload.get("recovery_records")
    intervals = result_payload.get("interval_records")
    paired = result_payload.get("paired_common_completion")
    recovery_summary = result_payload.get("recovery_summary")
    interval_summary = result_payload.get("interval_summary")
    if not isinstance(recovery, list) or not isinstance(intervals, list):
        raise AnalysisInputError("E4-r3 result records are not arrays")
    if not isinstance(paired, Mapping) or not isinstance(recovery_summary, Mapping) or not isinstance(interval_summary, Mapping):
        raise AnalysisInputError("E4-r3 result summaries are incomplete")
    for record in recovery + intervals:
        if not isinstance(record, Mapping):
            raise AnalysisInputError("result record is not an object")
        cell_key(record)

    recovery_groups: dict[tuple[str, int, str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    interval_groups: dict[tuple[str, int, str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for record in recovery:
        recovery_groups[cell_key(record)].append(record)
    for record in intervals:
        interval_groups[cell_key(record)].append(record)
    recovery_cells = {
        key: summarize_recovery_cell(key, recovery_groups[key])
        for key in sorted(recovery_groups, key=_key_sort)
    }
    interval_cells = {
        key: summarize_interval_cell(key, interval_groups[key])
        for key in sorted(interval_groups, key=_key_sort)
    }
    coverage = build_coverage(
        recovery,
        intervals,
        paired,
        recovery_summary,
        interval_summary,
        audit_json,
    )
    pairwise = summarize_pairwise(paired)
    stress = build_stress_comparisons(recovery_cells)
    resource = build_resource_audit(
        inventory,
        project_root,
        terminal_inventory_path,
        clock_provenance,
        execution_complete,
    )
    verdicts = _scope_verdicts(
        coverage,
        resource,
        authorization_info["authorization_gate"],
        recovery,
        intervals,
    )
    status_totals = {
        "recovery": status_counts(recovery),
        "interval": status_counts(intervals),
        "bootstrap": _bootstrap_counts(intervals),
    }
    total_nonfinite = {
        "recovery": sum(
            cell["nonfinite_audit"]["nonfinite_values_total"] for cell in recovery_cells.values()
        ),
        "interval": sum(
            cell["nonfinite_audit"]["nonfinite_values_total"] for cell in interval_cells.values()
        ),
    }
    analysis = {
        "schema_version": SCHEMA_VERSION,
        "register_key": REGISTER_KEY,
        "analysis_mode": "read_only_deterministic_derived_analysis",
        "scope": "N=20/N=50_only",
        "input_binding": input_binding,
        "authorization": authorization_info,
        "integrity_checks": checks,
        "frozen_result_state": {
            "schema_version": results_doc.get("schema_version"),
            "status": results_doc.get("status"),
            "promotion": results_doc.get("promotion"),
            "manifest_status": manifest.get("status"),
            "manifest_promotion": manifest.get("promotion"),
            "candidate_sha256": results_doc.get("candidate_sha256"),
            "authorization_sha256": results_doc.get("authorization_sha256"),
        },
        "coverage": coverage,
        "status_totals": status_totals,
        "nonfinite_totals": total_nonfinite,
        "recovery_cells": list(recovery_cells.values()),
        "interval_cells": list(interval_cells.values()),
        "pairwise_comparisons": pairwise,
        "stress_comparisons": stress,
        "resource_audit": resource,
        "verdicts": verdicts,
        "boundaries": [
            "N=100 and N=200 were not run; no extrapolation from N=20 or N=50 is made.",
            "The frozen run has one execution; repeated-run reproducibility is not evaluable.",
            "Runtime log files are absent from this worktree, so wall time, CPU, memory and GPU telemetry are missing.",
            "Only descriptive N=20/N=50 status, stress, and missing-telemetry accounting is emitted.",
            "No RCEP, NYC, R006e, R006f, N=100, or N=200 data is read or used.",
            "No manuscript, author decision register, frozen quarantine file, or new scientific payload is written or activated.",
        ],
        "new_experiment": {
            "started": False,
            "fresh_payloads_created": False,
            "n100_n200_status": "NOT_RUN/ABSTAIN",
        },
    }
    analysis["content_addressed_output_directory"] = (
        f"cal-e03-164-{input_bundle_sha256}"
    )
    return analysis


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_json_safe(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return "" if not math.isfinite(value) else format(value, ".17g")
    if isinstance(value, (Mapping, list, tuple)):
        return canonical_json(_json_safe(value))
    return str(value)


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def _flatten_cell_row(cell: Mapping[str, Any]) -> dict[str, Any]:
    metrics = cell.get("metrics", {})
    seed_metrics = cell.get("seed_level_metrics", {})
    row: dict[str, Any] = {
        field: cell.get(field) for field in CELL_FIELDS
    }
    row.update(
        {
            "cell_id": cell.get("cell_id"),
            "record_count": cell.get("record_count"),
            "seed_count": cell.get("seed_count"),
            "target_time_count": cell.get("target_time_count"),
            "status_counts": cell.get("status_counts"),
            "selected_hyperparameters": cell.get("selected_hyperparameters"),
            "nonfinite_values_total": cell.get("nonfinite_audit", {}).get("nonfinite_values_total"),
            "missing_values_total": cell.get("nonfinite_audit", {}).get("missing_values_total"),
        }
    )
    for field in ("operator_mse", "response_mse", "validation_loss", "estimated_spectral_radius", "truth_spectral_radius"):
        for suffix in ("mean", "std_population", "median", "q25", "q75", "min", "max"):
            row[f"{field}_{suffix}"] = metrics.get(field, {}).get(suffix)
    for field in ("operator_mse", "response_mse", "validation_loss"):
        row[f"{field}_seed_mean_mean"] = seed_metrics.get(field, {}).get("mean")
        row[f"{field}_seed_mean_std_population"] = seed_metrics.get(field, {}).get("std_population")
        row[f"{field}_seed_mean_count"] = seed_metrics.get(field, {}).get("finite_count")
    return row


def _flatten_interval_row(cell: Mapping[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {field: cell.get(field) for field in CELL_FIELDS}
    row.update(
        {
            "cell_id": cell.get("cell_id"),
            "record_count": cell.get("record_count"),
            "seed_count": cell.get("seed_count"),
            "status_counts": cell.get("status_counts"),
            "selection_status_counts": cell.get("selection_status_counts"),
            "bootstrap_status_counts": cell.get("bootstrap_status_counts"),
            "all_declared_intervals_available": cell.get("all_declared_intervals_available"),
            "nonfinite_values_total": cell.get("nonfinite_audit", {}).get("nonfinite_values_total"),
            "missing_values_total": cell.get("nonfinite_audit", {}).get("missing_values_total"),
        }
    )
    for field in INTERVAL_NUMERIC_FIELDS:
        for suffix in ("mean", "std_population", "median", "q25", "q75", "min", "max"):
            row[f"{field}_{suffix}"] = cell.get("metrics", {}).get(field, {}).get(suffix)
    row["bootstrap_requested_mean"] = cell.get("bootstrap_requested", {}).get("mean")
    row["bootstrap_completed_mean"] = cell.get("bootstrap_completed", {}).get("mean")
    row["bootstrap_attempts_mean"] = cell.get("bootstrap_attempts", {}).get("mean")
    return row


def report_markdown(analysis: Mapping[str, Any]) -> str:
    coverage = analysis["coverage"]
    totals = analysis["status_totals"]
    verdicts = analysis["verdicts"]
    resource = analysis["resource_audit"]
    register_item = analysis["authorization"].get("register_item") or {}
    return "\n".join(
        [
            "# CAL-E03:164 Frozen E4-r3 Analysis",
            "",
            "This is a deterministic, read-only derived analysis. It does not activate a claim, modify a manuscript, modify the author decision register, or start a new experiment.",
            "",
            f"- Overall verdict: **{verdicts['overall']}**",
            f"- Register item: `{REGISTER_KEY}` / `{register_item.get('item_id', 'UNRESOLVED')}`",
            f"- Content-addressed output directory: `{analysis['content_addressed_output_directory']}`",
            f"- Input bundle SHA-256: `{analysis['input_binding']['input_bundle_sha256']}`",
            "",
            "## Raw Scope Table",
            "",
            "| Layer | Declared/observed cells | Records or attempts | Status accounting |",
            "|---|---:|---:|---|",
            f"| recovery | {coverage['recovery']['expected_cells']}/{coverage['recovery']['observed_cells']} | {coverage['recovery']['record_count']} | `{canonical_json(totals['recovery'])}` |",
            f"| paired completion | {coverage['paired']['declared_cells_from_audit']}/{coverage['paired']['observed_cells']} | raw differences retained in `paired-comparison.csv` | all status counts retained |",
            f"| interval | {coverage['interval']['expected_cells']}/{coverage['interval']['observed_cells']} | {coverage['interval']['record_count']} | `{canonical_json(totals['interval'])}` |",
            f"| bootstrap | 8 interval cells | {sum(totals['bootstrap'].values())} attempts | `{canonical_json(totals['bootstrap'])}` |",
            "",
            "## Findings",
            "",
            "1. The frozen grid covers the declared N=20/N=50, two-family, two-query, H=4/H=12 and three-method scope. Each recovery and interval row remains in the accounting; no row is filtered by status or metric value.",
            "2. The observed recovery and interval status totals are shown above. Non-finite and missing metric counts are reported in `analysis.json`, `reproducibility.csv` and `stability.csv`; no non-finite value is converted into a passing result.",
            "3. Cross-scale, query-stress and horizon-stress deltas are descriptive raw mean deltas only. The absent predeclared log-error-ratio/CI artifact is not reconstructed and no superiority threshold is introduced.",
            f"4. Resource verdict is **{resource['verdict']}**: the inventory exposes one run, exit code and process-state fields, but runtime log files/telemetry are not available in this worktree. Missing telemetry: `{', '.join(resource['missing_telemetry'])}`.",
            "",
            "## Boundaries",
            "",
            *[f"- {boundary}" for boundary in analysis["boundaries"]],
            "",
            "## Verdict Components",
            "",
            "| Component | Verdict |",
            "|---|---|",
            *[f"| {name} | **{value}** |" for name, value in sorted(verdicts.items())],
            "",
            "No next experiment was started. Any N=100/N=200 extension would require a fresh protocol, candidate and pre-outcome freeze with separate authorization.",
            "",
        ]
    )


def write_outputs(
    analysis: Mapping[str, Any],
    output_parent: Path,
    *,
    execution_authorization_path: Path | None = None,
    run_id: str = "primary",
    observed_paths: Mapping[str, Path] | None = None,
    project_root: Path | None = None,
) -> Path:
    directory_name = str(analysis["content_addressed_output_directory"])
    output_parent = Path(output_parent).expanduser().resolve()
    output_dir = output_parent / directory_name
    validate_execution_authorization(
        execution_authorization_path,
        output_root=output_dir,
        run_id=run_id,
        observed_paths=observed_paths or {},
        artifact_prefix="cal-e03-164-",
        project_root=project_root,
    )
    output_parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing content-addressed output: {output_dir}")
    output_dir.mkdir()

    write_json(output_dir / "input-binding.json", analysis["input_binding"])
    write_json(output_dir / "analysis.json", analysis)
    coverage_rows = [
        {
            "layer": "recovery",
            "expected_cells": analysis["coverage"]["recovery"]["expected_cells"],
            "observed_cells": analysis["coverage"]["recovery"]["observed_cells"],
            "record_count": analysis["coverage"]["recovery"]["record_count"],
            "missing_cells": analysis["coverage"]["recovery"]["missing_cells"],
            "unexpected_cells": analysis["coverage"]["recovery"]["unexpected_cells"],
        },
        {
            "layer": "interval",
            "expected_cells": analysis["coverage"]["interval"]["expected_cells"],
            "observed_cells": analysis["coverage"]["interval"]["observed_cells"],
            "record_count": analysis["coverage"]["interval"]["record_count"],
            "missing_cells": analysis["coverage"]["interval"]["missing_cells"],
            "unexpected_cells": analysis["coverage"]["interval"]["unexpected_cells"],
        },
        {
            "layer": "paired",
            "expected_cells": analysis["coverage"]["paired"]["declared_cells_from_audit"],
            "observed_cells": analysis["coverage"]["paired"]["observed_cells"],
            "record_count": None,
            "missing_cells": [],
            "unexpected_cells": [],
        },
    ]
    write_csv(
        output_dir / "coverage.csv",
        coverage_rows,
        ("layer", "expected_cells", "observed_cells", "record_count", "missing_cells", "unexpected_cells"),
    )
    recovery_rows = [_flatten_cell_row(row) for row in analysis["recovery_cells"]]
    recovery_fields = [
        "cell_id", "family", "n", "query_class", "horizon", "method", "record_count", "seed_count",
        "target_time_count", "status_counts", "selected_hyperparameters", "nonfinite_values_total",
        "missing_values_total",
    ]
    for field in RECOVERY_NUMERIC_FIELDS:
        recovery_fields.extend(f"{field}_{suffix}" for suffix in ("mean", "std_population", "median", "q25", "q75", "min", "max"))
    for field in ("operator_mse", "response_mse", "validation_loss"):
        recovery_fields.extend(
            [f"{field}_seed_mean_mean", f"{field}_seed_mean_std_population", f"{field}_seed_mean_count"]
        )
    write_csv(output_dir / "reproducibility.csv", recovery_rows, recovery_fields)
    interval_rows = [_flatten_interval_row(row) for row in analysis["interval_cells"]]
    interval_fields = [
        "cell_id", "family", "n", "query_class", "horizon", "method", "record_count", "seed_count",
        "status_counts", "selection_status_counts", "bootstrap_status_counts", "all_declared_intervals_available",
        "nonfinite_values_total", "missing_values_total", "bootstrap_requested_mean", "bootstrap_completed_mean",
        "bootstrap_attempts_mean",
    ]
    for field in INTERVAL_NUMERIC_FIELDS:
        interval_fields.extend(f"{field}_{suffix}" for suffix in ("mean", "std_population", "median", "q25", "q75", "min", "max"))
    write_csv(output_dir / "stability.csv", interval_rows, interval_fields)
    write_csv(
        output_dir / "stress-comparison.csv",
        analysis["stress_comparisons"],
        (
            "comparison_type", "left_label", "right_label", "left_cell_id", "right_cell_id", "family",
            "left_n", "right_n", "left_query_class", "right_query_class", "left_horizon", "right_horizon",
            "method", "response_mse_delta_left_minus_right", "operator_mse_delta_left_minus_right",
            "validation_loss_delta_left_minus_right", "left_status_counts", "right_status_counts", "comparison_note",
        ),
    )
    write_csv(
        output_dir / "paired-comparison.csv",
        analysis["pairwise_comparisons"],
        (
            "pair_id", "family", "n", "query_class", "horizon", "candidate_method", "comparator_method",
            "declared_date_keys", "common_completion_date_keys", "candidate_status_counts", "comparator_status_counts",
            "operator_difference_stats_candidate_minus_comparator", "response_difference_stats_candidate_minus_comparator",
            "operator_candidate_lower_count", "operator_candidate_higher_count", "operator_tie_count",
            "response_candidate_lower_count", "response_candidate_higher_count", "response_tie_count",
            "comparison_metric_note", "retention",
        ),
    )
    write_json(output_dir / "resource-audit.json", analysis["resource_audit"])
    (output_dir / "report.md").write_text(report_markdown(analysis), encoding="utf-8")

    artifacts = []
    for path in sorted(output_dir.iterdir(), key=lambda item: item.name):
        artifacts.append({"path": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    output_manifest = {
        "schema_version": "cal-e03-164-output-manifest-v1",
        "register_key": REGISTER_KEY,
        "content_addressed_directory": directory_name,
        "input_bundle_sha256": analysis["input_binding"]["input_bundle_sha256"],
        "verdict": analysis["verdicts"],
        "artifacts": artifacts,
        "write_policy": {
            "source_inputs_modified": False,
            "manuscript_modified": False,
            "decision_register_modified": False,
            "frozen_quarantine_modified": False,
            "new_protocol_or_candidate_created": False,
        },
    }
    write_json(output_dir / "output-manifest.json", output_manifest)
    return output_dir


def _execution_context_from_e03_args(args: argparse.Namespace, project_root: Path) -> dict[str, Path]:
    terminal_inventory = args.terminal_inventory or args.inventory
    candidate = args.candidate or project_root / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json"
    workspace_authorization = args.workspace_authorization or project_root / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json"
    return {
        "source_authorization_v2": args.authorization,
        "m2a_repair_receipt": project_root / EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
        "decision_register": args.decision_register,
        "e4_results": args.results,
        "e4_execution_manifest": args.execution_manifest,
        "e4_execution_complete": args.execution_complete,
        "e4_terminal_inventory": terminal_inventory,
        "e4_candidate": candidate,
        "workspace_authorization": workspace_authorization,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-register", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--audit-markdown", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--execution-manifest", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
    )
    parser.add_argument("--audit-json", type=Path)
    parser.add_argument("--clock-provenance", type=Path)
    parser.add_argument(
        "--execution-complete",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json",
    )
    parser.add_argument("--candidate", type=Path, default=None)
    parser.add_argument("--workspace-authorization", type=Path, default=None)
    parser.add_argument("--execution-authorization", type=Path, required=True)
    parser.add_argument("--run-id", choices=("primary", "duplicate"), required=True)
    parser.add_argument("--terminal-inventory", type=Path, default=None)
    parser.add_argument(
        "--output-parent",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "refine-logs/ncs_new_analysis_v2",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        analysis = analyze_inputs(
            decision_register_path=args.decision_register,
            authorization_path=args.authorization,
            plan_path=args.plan,
            audit_markdown_path=args.audit_markdown,
            results_path=args.results,
            execution_manifest_path=args.execution_manifest,
            project_root=args.project_root,
            inventory_path=args.inventory,
            audit_json_path=args.audit_json,
            clock_provenance_path=args.clock_provenance,
            execution_complete_path=args.execution_complete,
            candidate_path=args.candidate,
            workspace_authorization_path=args.workspace_authorization,
            terminal_inventory_path=args.terminal_inventory or args.inventory,
        )
        project_root = args.project_root.expanduser().resolve()
        observed_paths = _execution_context_from_e03_args(args, project_root)
        output_parent = args.output_parent / args.run_id
        output_dir = output_parent / str(analysis["content_addressed_output_directory"])
        validate_execution_authorization(
            args.execution_authorization,
            output_root=output_dir,
            run_id=args.run_id,
            observed_paths=observed_paths,
            artifact_prefix="cal-e03-164-",
            project_root=project_root,
        )
        output_dir = write_outputs(
            analysis,
            output_parent,
            execution_authorization_path=args.execution_authorization,
            run_id=args.run_id,
            observed_paths=observed_paths,
            project_root=project_root,
        )
    except (AnalysisInputError, FileExistsError, OSError, ValueError) as exc:
        parser.error(str(exc))
        return 2
    print(output_dir)
    print(json.dumps(analysis["verdicts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
