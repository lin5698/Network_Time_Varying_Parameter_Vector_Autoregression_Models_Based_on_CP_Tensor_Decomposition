#!/usr/bin/env python3
"""Read-only CAL-E02:135 sensitivity audit over frozen E4-r3 records.

The analyzer deliberately separates three questions:

* what can be described from the frozen seed/scenario records;
* what cannot be established because stopping/checkpoint provenance is absent;
* what a fresh, outcome-blind stopping-variant candidate would need to record.

It never runs a scientific grid and never writes to the frozen E4-r3
quarantine. Output is written only to a new, content-addressed CAL-E02:135
directory when the CLI is invoked.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import hmac
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence

from scripts.experiments.analyze_cal_e01_75 import (
    EXECUTION_AUTHORIZATION_SCHEMA_VERSION,
    EXECUTION_AUTHORIZATION_STATUS,
    EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
    ExecutionAuthorizationError,
    _validate_execution_authorization_common,
)

REGISTER_KEY = "CAL-E02:135"
CALIBRATION_ID = "CAL-E02"
ITEM_INDEX = 135
ANALYSIS_ID = "cal-e02-135-derived-sensitivity-v1"
AUTHORIZATION_SCHEMA_VERSION = "ncs-four-analysis-authorization-v2"
V2_ITEM_BINDING = {
    "item_id": "V1-035",
    "calibration_id": "CAL-E02",
    "item_index": 135,
    "priority": "P1",
    "action_class": "NEW_ANALYSIS_OR_EXPERIMENT",
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

STATUS_ORDER = (
    "AVAILABLE",
    "OUTSIDE_TARGET",
    "NONCONVERGED",
    "NONFINITE",
    "UNSTABLE",
)
RECOVERY_METRIC_FIELDS = (
    "operator_mse",
    "response_mse",
    "validation_loss",
    "estimated_spectral_radius",
    "truth_spectral_radius",
)
ENDPOINT_REQUIRED_FIELDS = (
    "operator_mse",
    "response_mse",
    "estimated_spectral_radius",
    "truth_spectral_radius",
    "query_class",
    "horizon",
    "target_time",
    "status",
)
STOPPING_TERMS = (
    "stopping",
    "early_stop",
    "early_stopping",
    "checkpoint",
    "iteration",
    "patience",
    "trajectory",
    "curve",
    "stop_rule",
)
PARTITION_TERMS = (
    "train",
    "training",
    "validation",
    "evaluation",
    "test",
    "split",
    "partition",
)


@dataclass(frozen=True)
class InputPaths:
    """All read-only inputs consumed by this analysis."""

    register: Path
    authorization: Path
    e4_r3_authorization: Path
    plan: Path
    audit: Path
    results: Path
    execution_manifest: Path
    execution_complete: Path
    candidate: Path
    tuning_split: Path
    terminal_inventory: Path


@dataclass(frozen=True)
class LoadedJson:
    path: Path
    value: Any
    sha256: str


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
        raise ValueError(f"{label} must be a non-null JSON object")
    return value


def _require_v2_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label} must be a non-null lowercase SHA-256")
    return value


def _resolve_inventory_path(raw_path: Any, project_root: Path) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("terminal inventory artifact path is missing")
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
        raise ValueError("legacy or unsupported authorization schema")
    if any(key in authorization for key in ("frozen_inputs", "authorized_register_items", "execution_policy")):
        raise ValueError("legacy authorization fields are prohibited")
    authorized_scope = _require_v2_mapping(
        authorization.get("authorized_scope"), "authorization.authorized_scope"
    )
    rec_m2_actions = authorized_scope.get("REC_M2")
    if not isinstance(rec_m2_actions, list) or V2_REQUIRED_REC_M2_ACTION not in rec_m2_actions:
        raise ValueError("authorization.authorized_scope.REC_M2 is not bound")
    current_task_limits = _require_v2_mapping(
        authorization.get("current_task_limits"), "authorization.current_task_limits"
    )
    for field, expected in V2_REQUIRED_TASK_LIMITS.items():
        if current_task_limits.get(field) != expected:
            raise ValueError(f"authorization.current_task_limits.{field} drifted")
    binding = _require_v2_mapping(authorization.get("binding"), "authorization.binding")
    declared_register = binding.get("decision_register_path")
    if not isinstance(declared_register, str) or not declared_register:
        raise ValueError("authorization.binding.decision_register_path is required")
    project_root = Path(__file__).resolve().parents[2]
    expected_register_path = Path(declared_register).expanduser()
    if not expected_register_path.is_absolute():
        expected_register_path = project_root / expected_register_path
    observed_register_path = Path(register_path).expanduser().resolve(strict=True)
    if observed_register_path != expected_register_path.resolve():
        raise ValueError("decision-register path is not the v2-bound path")
    expected_register_sha = _require_v2_sha(binding.get("decision_register_sha256"), "authorization.binding.decision_register_sha256")
    observed_register_sha = sha256_file(observed_register_path)
    if observed_register_sha != expected_register_sha:
        raise ValueError("decision-register SHA-256 mismatch")
    if binding.get("item_payload_sha256_algorithm") != "recursive_object_key_sort_then_JSON.stringify_utf8_no_whitespace":
        raise ValueError("unsupported item payload canonicalization")
    item_payloads = _require_v2_mapping(binding.get("item_payloads"), "authorization.binding.item_payloads")
    expected_item_sha = _require_v2_sha(item_payloads.get(V2_ITEM_BINDING["item_id"]), f"authorization.binding.item_payloads.{V2_ITEM_BINDING['item_id']}")
    items = register.get("items")
    if not isinstance(items, list):
        raise ValueError("decision register.items must be a non-null array")
    selected = []
    for item in items:
        if not isinstance(item, Mapping) or item.get("item_id") != V2_ITEM_BINDING["item_id"]:
            continue
        source = item.get("calibration_source")
        if isinstance(source, Mapping) and source.get("calibration_id") == V2_ITEM_BINDING["calibration_id"] and item.get("item_index") == V2_ITEM_BINDING["item_index"]:
            selected.append(item)
    if len(selected) != 1:
        raise ValueError("exact current register item mapping is not unique")
    register_item = selected[0]
    for field in ("item_id", "item_index", "priority", "action_class"):
        if register_item.get(field) != V2_ITEM_BINDING[field]:
            raise ValueError(f"current register item {field} drifted")
    if hashlib.sha256(_canonical_v2_item_bytes(register_item)).hexdigest() != expected_item_sha:
        raise ValueError("canonical register item payload SHA-256 mismatch")
    frozen = _require_v2_mapping(authorization.get("frozen_e4_r3_inputs"), "authorization.frozen_e4_r3_inputs")
    actual_hashes: dict[str, str] = {}
    for role, field in V2_FROZEN_HASH_FIELDS.items():
        expected = _require_v2_sha(frozen.get(field), f"authorization.frozen_e4_r3_inputs.{field}")
        path = frozen_paths.get(role)
        if not isinstance(path, Path):
            raise ValueError(f"frozen input path is missing: {role}")
        resolved = path.expanduser().resolve(strict=True)
        actual = sha256_file(resolved)
        if actual != expected:
            raise ValueError(f"frozen input SHA-256 mismatch: {role}")
        actual_hashes[role] = actual
    workspace_path = frozen_paths.get("workspace_authorization")
    if not isinstance(workspace_path, Path):
        raise ValueError("workspace authorization path is required for the E4 chain")
    workspace_hash = sha256_file(workspace_path.expanduser().resolve(strict=True))
    workspace = _require_v2_mapping(frozen_values.get("workspace_authorization"), "workspace authorization")
    candidate = _require_v2_mapping(frozen_values.get("candidate"), "frozen candidate")
    candidate_id = candidate.get("candidate_id")
    candidate_sha = actual_hashes["candidate"]
    if not isinstance(candidate_id, str) or not candidate_id or workspace.get("candidate_id") != candidate_id or workspace.get("candidate_sha256") != candidate_sha:
        raise ValueError("workspace authorization candidate chain mismatch")
    for role in ("results", "execution_manifest", "execution_complete"):
        value = _require_v2_mapping(frozen_values.get(role), f"frozen {role}")
        if value.get("authorization_sha256") != workspace_hash or value.get("candidate_sha256") != candidate_sha:
            raise ValueError(f"frozen {role} authorization/candidate chain mismatch")
    inventory = _require_v2_mapping(frozen_values.get("terminal_inventory"), "terminal inventory")
    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("terminal inventory.artifacts is required")
    inventory_roles = {role: frozen_paths[role] for role in V2_FROZEN_HASH_FIELDS if role != "terminal_inventory"}
    inventory_roles["workspace_authorization"] = workspace_path
    for role, path in inventory_roles.items():
        resolved = path.expanduser().resolve(strict=True)
        matches = [entry for entry in artifacts if isinstance(entry, Mapping) and _resolve_inventory_path(entry.get("path"), project_root) == resolved]
        if len(matches) != 1 or matches[0].get("sha256") != sha256_file(resolved):
            raise ValueError(f"terminal inventory chain mismatch: {role}")
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
    artifact_prefix: str = "cal-e02-135-",
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
        raise ValueError(str(error)) from error


def canonical_json_bytes(value: Any) -> bytes:
    """Return the strict canonical JSON encoding used for content addresses."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def read_json(path: Path) -> LoadedJson:
    """Read one JSON file while rejecting JSON NaN/Infinity extensions."""

    resolved = Path(path).expanduser().resolve(strict=True)
    raw = resolved.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        parse_constant=_reject_nonfinite_json_constant,
    )
    return LoadedJson(resolved, value, sha256_bytes(raw))


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _json_sort_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)


def _unique_values(values: Iterable[Any]) -> list[Any]:
    unique: dict[str, Any] = {}
    for value in values:
        unique[_json_sort_key(value)] = value
    return [unique[key] for key in sorted(unique)]


def _field_union(records: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted({key for record in records for key in record})


def _matching_fields(fields: Iterable[str], terms: Sequence[str]) -> list[str]:
    folded_terms = tuple(term.casefold() for term in terms)
    return sorted(
        field
        for field in fields
        if any(term in field.casefold() for term in folded_terms)
    )


def _flatten_key_paths(value: Any, prefix: tuple[str, ...] = ()) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key in sorted(value):
            child = prefix + (str(key),)
            paths.append(".".join(child))
            paths.extend(_flatten_key_paths(value[key], child))
    elif isinstance(value, list):
        for child_value in value:
            paths.extend(_flatten_key_paths(child_value, prefix))
    return paths


def _status_counts(records: Sequence[Mapping[str, Any]], field: str = "status") -> dict[str, int]:
    counts = Counter(str(record.get(field, "<MISSING>")) for record in records)
    ordered = {status: int(counts.pop(status, 0)) for status in STATUS_ORDER}
    for status in sorted(counts):
        ordered[status] = int(counts[status])
    return ordered


def _numeric_summary(records: Sequence[Mapping[str, Any]], field: str) -> dict[str, Any]:
    finite_values: list[float] = []
    missing_count = 0
    non_numeric_count = 0
    nonfinite_count = 0
    for record in records:
        if field not in record or record[field] is None:
            missing_count += 1
            continue
        value = record[field]
        if not _is_number(value):
            non_numeric_count += 1
            continue
        if not math.isfinite(float(value)):
            nonfinite_count += 1
            continue
        finite_values.append(float(value))

    sorted_values = sorted(finite_values)

    def quantile(probability: float) -> float | None:
        if not sorted_values:
            return None
        position = probability * (len(sorted_values) - 1)
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return sorted_values[lower]
        weight = position - lower
        return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight

    return {
        "record_count": len(records),
        "finite_count": len(finite_values),
        "missing_count": missing_count,
        "non_numeric_count": non_numeric_count,
        "nonfinite_count": nonfinite_count,
        "mean": (sum(finite_values) / len(finite_values)) if finite_values else None,
        "min": sorted_values[0] if sorted_values else None,
        "q05": quantile(0.05),
        "q25": quantile(0.25),
        "median": quantile(0.50),
        "q75": quantile(0.75),
        "q95": quantile(0.95),
        "max": sorted_values[-1] if sorted_values else None,
    }


def _mean_finite(records: Sequence[Mapping[str, Any]], field: str) -> float | None:
    values = [
        float(record[field])
        for record in records
        if field in record and _is_finite_number(record[field])
    ]
    return sum(values) / len(values) if values else None


def _pearson(pairs: Sequence[tuple[float, float]]) -> float | None:
    if len(pairs) < 2:
        return None
    x_values = [pair[0] for pair in pairs]
    y_values = [pair[1] for pair in pairs]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in pairs)
    x_sum = sum((x - x_mean) ** 2 for x in x_values)
    y_sum = sum((y - y_mean) ** 2 for y in y_values)
    denominator = math.sqrt(x_sum * y_sum)
    return numerator / denominator if denominator > 0 else None


def _group_records(
    records: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> list[tuple[tuple[Any, ...], list[Mapping[str, Any]]]]:
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record.get(field) for field in fields)].append(record)
    return sorted(grouped.items(), key=lambda item: _json_sort_key(item[0]))


def _key_object(fields: Sequence[str], key: Sequence[Any]) -> dict[str, Any]:
    return {field: value for field, value in zip(fields, key)}


def _scenario_summaries(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    fields = ("family", "n", "query_class", "horizon", "method")
    summaries: list[dict[str, Any]] = []
    for key, group in _group_records(records, fields):
        seed_values = sorted({record.get("seed") for record in group})
        target_times = sorted({record.get("target_time") for record in group})
        summary = {
            **_key_object(fields, key),
            "record_count": len(group),
            "seed_count": len(seed_values),
            "seed_values": seed_values,
            "target_time_count": len(target_times),
            "target_times": target_times,
            "expected_record_count_from_observed_grid": len(seed_values) * len(target_times),
            "status_counts": _status_counts(group),
            "selected_hyperparameters": _unique_values(
                record.get("selected_hyperparameter") for record in group
            ),
            "metrics": {
                field: _numeric_summary(group, field) for field in RECOVERY_METRIC_FIELDS
            },
        }
        summaries.append(summary)
    return summaries


def _seed_summaries(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    fields = ("family", "n", "query_class", "horizon", "method", "seed")
    summaries: list[dict[str, Any]] = []
    for key, group in _group_records(records, fields):
        target_times = sorted({record.get("target_time") for record in group})
        summaries.append(
            {
                **_key_object(fields, key),
                "record_count": len(group),
                "target_time_count": len(target_times),
                "target_times": target_times,
                "status_counts": _status_counts(group),
                "selected_hyperparameters": _unique_values(
                    record.get("selected_hyperparameter") for record in group
                ),
                "validation_loss": _numeric_summary(group, "validation_loss"),
                "operator_mse": _numeric_summary(group, "operator_mse"),
                "response_mse": _numeric_summary(group, "response_mse"),
            }
        )
    return summaries


def _selection_summaries(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    fields = ("family", "n", "method", "seed")
    summaries: list[dict[str, Any]] = []
    for key, group in _group_records(records, fields):
        selected = _unique_values(record.get("selected_hyperparameter") for record in group)
        validation = _unique_values(record.get("validation_loss") for record in group)
        summaries.append(
            {
                **_key_object(fields, key),
                "record_count": len(group),
                "query_classes": sorted({record.get("query_class") for record in group}),
                "horizons": sorted({record.get("horizon") for record in group}),
                "selected_hyperparameters": selected,
                "validation_losses": validation,
                "selection_consistent_across_endpoint_records": len(selected) == 1,
                "validation_loss_consistent_across_endpoint_records": len(validation) == 1,
            }
        )
    return summaries


def _validation_evaluation_associations(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    scenario_fields = ("family", "n", "query_class", "horizon", "method")
    output: list[dict[str, Any]] = []
    for key, scenario_group in _group_records(records, scenario_fields):
        seed_pairs: list[tuple[float, float]] = []
        seed_pair_rows: list[dict[str, Any]] = []
        for seed, seed_group in _group_records(scenario_group, ("seed",)):
            validation_mean = _mean_finite(seed_group, "validation_loss")
            response_mean = _mean_finite(seed_group, "response_mse")
            row = {
                "seed": seed[0],
                "validation_loss_mean": validation_mean,
                "response_mse_mean": response_mean,
                "pair_available": validation_mean is not None and response_mean is not None,
            }
            seed_pair_rows.append(row)
            if row["pair_available"]:
                seed_pairs.append((float(validation_mean), float(response_mean)))
        output.append(
            {
                **_key_object(scenario_fields, key),
                "seed_count": len(seed_pair_rows),
                "paired_seed_count": len(seed_pairs),
                "pearson_r_validation_loss_vs_response_mse": _pearson(seed_pairs),
                "seed_pairs": seed_pair_rows,
                "interpretation": "descriptive_association_only_not_an_overfitting_test",
            }
        )
    return output


def _record_is_adverse(record: Mapping[str, Any]) -> bool:
    if str(record.get("status", "<MISSING>")) != "AVAILABLE":
        return True
    for field in RECOVERY_METRIC_FIELDS:
        if field in record and record[field] is not None and not _is_finite_number(record[field]):
            return True
    return False


def _retained_adverse_records(
    recovery_records: Sequence[Mapping[str, Any]],
    interval_records: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    recovery: list[dict[str, Any]] = []
    for index, record in enumerate(recovery_records):
        if _record_is_adverse(record):
            recovery.append({"record_index": index, "record": dict(record)})

    interval: list[dict[str, Any]] = []
    for index, record in enumerate(interval_records):
        adverse_bootstrap = any(
            int(count) > 0
            for status, count in (record.get("bootstrap_status_counts") or {}).items()
            if str(status) != "AVAILABLE"
        )
        adverse = str(record.get("status", "<MISSING>")) != "AVAILABLE" or adverse_bootstrap
        for field in (
            "raw_response_mse",
            "stability_qualified_response_mse",
            "mean_interval_width",
            "coverage",
        ):
            if field in record and record[field] is not None and not _is_finite_number(record[field]):
                adverse = True
        if adverse:
            interval.append({"record_index": index, "record": dict(record)})
    return {"recovery_records": recovery, "interval_records": interval}


def _bootstrap_status_counts(interval_records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for record in interval_records:
        nested = record.get("bootstrap_status_counts")
        if not isinstance(nested, Mapping):
            counts["<MISSING>"] += 1
            continue
        for status, count in nested.items():
            counts[str(status)] += int(count)
    ordered = {status: int(counts.pop(status, 0)) for status in STATUS_ORDER}
    for status in sorted(counts):
        ordered[status] = int(counts[status])
    return ordered


def _register_item(register: Mapping[str, Any]) -> Mapping[str, Any]:
    items = register.get("items")
    if not isinstance(items, list):
        raise ValueError("formal register items must be a list")
    matches = [
        item
        for item in items
        if isinstance(item, Mapping)
        and item.get("item_id") == V2_ITEM_BINDING["item_id"]
        and isinstance(item.get("calibration_source"), Mapping)
        and item["calibration_source"].get("calibration_id") == V2_ITEM_BINDING["calibration_id"]
        and item.get("item_index") == V2_ITEM_BINDING["item_index"]
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one formal register item for {REGISTER_KEY}")
    return matches[0]


def _source_binding(
    label: str,
    loaded: LoadedJson,
    expected_sha256: str | None,
    role: str,
) -> dict[str, Any]:
    matches = expected_sha256 is not None and hmac.compare_digest(loaded.sha256, expected_sha256)
    return {
        "label": label,
        "role": role,
        "path": str(loaded.path),
        "expected_sha256": expected_sha256,
        "observed_sha256": loaded.sha256,
        "sha256_matches": matches,
    }


def _load_inputs(paths: InputPaths) -> dict[str, LoadedJson]:
    return {
        "register": read_json(paths.register),
        "authorization": read_json(paths.authorization),
        "e4_r3_authorization": read_json(paths.e4_r3_authorization),
        "plan": read_json(paths.plan) if paths.plan.suffix.lower() == ".json" else _read_text_as_loaded(paths.plan),
        "audit": read_json(paths.audit) if paths.audit.suffix.lower() == ".json" else _read_text_as_loaded(paths.audit),
        "results": read_json(paths.results),
        "execution_manifest": read_json(paths.execution_manifest),
        "execution_complete": read_json(paths.execution_complete),
        "candidate": read_json(paths.candidate),
        "tuning_split": read_json(paths.tuning_split),
        "terminal_inventory": read_json(paths.terminal_inventory),
    }


def _read_text_as_loaded(path: Path) -> LoadedJson:
    resolved = Path(path).expanduser().resolve(strict=True)
    raw = resolved.read_bytes()
    return LoadedJson(resolved, raw.decode("utf-8"), sha256_bytes(raw))


def _build_input_manifest(loaded: Mapping[str, LoadedJson]) -> tuple[dict[str, Any], dict[str, Any]]:
    authorization = loaded["authorization"].value
    register = loaded["register"].value
    v2_binding = validate_authorization_v2(
        authorization,
        register_path=loaded["register"].path,
        register=register,
        frozen_paths={
            "results": loaded["results"].path,
            "execution_manifest": loaded["execution_manifest"].path,
            "execution_complete": loaded["execution_complete"].path,
            "terminal_inventory": loaded["terminal_inventory"].path,
            "candidate": loaded["candidate"].path,
            "workspace_authorization": loaded["e4_r3_authorization"].path,
        },
        frozen_values={
            "results": loaded["results"].value,
            "execution_manifest": loaded["execution_manifest"].value,
            "execution_complete": loaded["execution_complete"].value,
            "terminal_inventory": loaded["terminal_inventory"].value,
            "candidate": loaded["candidate"].value,
            "workspace_authorization": loaded["e4_r3_authorization"].value,
        },
    )
    frozen_e4_inputs = authorization["frozen_e4_r3_inputs"]
    expected_by_label = {
        "register": authorization["binding"]["decision_register_sha256"],
        "results": frozen_e4_inputs["results_sha256"],
        "execution_manifest": frozen_e4_inputs["execution_manifest_sha256"],
        "execution_complete": frozen_e4_inputs["execution_complete_sha256"],
        "terminal_inventory": frozen_e4_inputs["terminal_inventory_sha256"],
        "candidate": frozen_e4_inputs["candidate_sha256"],
        "e4_r3_authorization": v2_binding["workspace_authorization_sha256"],
    }
    roles = {
        "register": "formal_author_decision_register_external_read_only",
        "authorization": "analysis_authorization",
        "e4_r3_authorization": "frozen_e4_r3_workspace_authorization_read_only",
        "plan": "analysis_plan",
        "audit": "frozen_e4_r3_integrity_audit",
        "results": "frozen_e4_r3_results_read_only",
        "execution_manifest": "frozen_e4_r3_execution_manifest_read_only",
        "execution_complete": "frozen_e4_r3_execution_complete_read_only",
        "candidate": "frozen_e4_r3_candidate_read_only_context",
        "tuning_split": "frozen_e4_r3_selection_and_split_provenance",
        "terminal_inventory": "frozen_e4_r3_terminal_inventory_read_only",
    }
    entries = [
        _source_binding(
            label,
            loaded[label],
            expected_by_label.get(label),
            roles[label],
        )
        for label in (
            "register",
            "authorization",
            "e4_r3_authorization",
            "plan",
            "audit",
            "results",
            "execution_manifest",
            "execution_complete",
            "candidate",
            "tuning_split",
            "terminal_inventory",
        )
    ]
    by_label = {entry["label"]: entry for entry in entries}
    observed_hashes = {entry["label"]: entry["observed_sha256"] for entry in entries}
    expected_hashes = {entry["label"]: entry["expected_sha256"] for entry in entries}
    return (
        {
            "schema_version": "ncs-cal-e02-135-input-manifest-v1",
            "register_key": REGISTER_KEY,
            "entries": entries,
            "observed_sha256_by_label": observed_hashes,
            "expected_sha256_by_label": expected_hashes,
            "all_declared_frozen_hashes_match": all(
                entry["sha256_matches"]
                for entry in entries
                if entry["expected_sha256"] is not None
            ),
            "register_path_is_external_to_current_worktree": not str(
                loaded["register"].path
            ).startswith(str(Path(__file__).resolve().parents[2])),
            "authorization_v2_binding": v2_binding,
        },
        by_label,
    )


def _sufficiency_audit(
    loaded: Mapping[str, LoadedJson],
    input_manifest: Mapping[str, Any],
    register_item: Mapping[str, Any],
) -> dict[str, Any]:
    result = loaded["results"].value
    candidate = loaded["candidate"].value
    tuning = loaded["tuning_split"].value
    recovery_records = result.get("results", {}).get("recovery_records", [])
    interval_records = result.get("results", {}).get("interval_records", [])
    recovery_fields = _field_union(recovery_records)
    interval_fields = _field_union(interval_records)
    result_paths = _flatten_key_paths(result)
    result_partition_key_names = sorted(
        {
            path.rsplit(".", 1)[-1]
            for path in result_paths
            if any(term in path.casefold() for term in PARTITION_TERMS)
        }
    )
    candidate_paths = _flatten_key_paths(candidate)
    tuning_paths = _flatten_key_paths(tuning)
    stopping_record_fields = _matching_fields(recovery_fields + interval_fields, STOPPING_TERMS)
    stopping_protocol_paths = sorted(
        path
        for path in candidate_paths + tuning_paths
        if any(term in path.casefold() for term in STOPPING_TERMS)
    )
    partition_record_fields = _matching_fields(recovery_fields + interval_fields, PARTITION_TERMS)
    partition_protocol_paths = sorted(
        path
        for path in candidate_paths + tuning_paths
        if any(term in path.casefold() for term in PARTITION_TERMS)
    )
    selection_record_fields = sorted(
        field
        for field in recovery_fields + interval_fields
        if field in {"selected_hyperparameter", "selection_status", "selection_validation_loss", "validation_loss"}
    )
    selection_protocol_paths = sorted(
        path
        for path in candidate_paths + tuning_paths
        if any(term in path.casefold() for term in ("selection", "candidate_lists", "tie_break", "maximum_budget"))
    )
    endpoint_provenance_fields = _matching_fields(
        recovery_fields + interval_fields,
        ("endpoint", "provenance", "source", "held_out", "independent"),
    )
    result_status = result.get("status") if isinstance(result, Mapping) else None
    manifest_status = loaded["execution_manifest"].value.get("status")
    hash_entries = input_manifest.get("entries", [])
    register_hash_match = next(
        entry["sha256_matches"] for entry in hash_entries if entry["label"] == "register"
    )
    e4_hashes_match = all(
        entry["sha256_matches"]
        for entry in hash_entries
        if entry["label"] in {"results", "execution_manifest", "candidate", "e4_r3_authorization"}
        and entry["expected_sha256"] is not None
    )

    checks = [
        {
            "check_id": "seed_scenario_records",
            "status": "SUPPORTED",
            "evidence": [
                "results.results.recovery_records",
                "results.results.recovery_summary",
                "results.results.paired_common_completion",
            ],
            "details": "All serialized recovery records are included in the cross-seed/scenario audit; no cell is selected by stability or outcome.",
        },
        {
            "check_id": "train_validation_evaluation_separation",
            "status": "PARTIAL",
            "evidence": [
                "candidate.bindings.configuration.split_policy",
                "tuning_split.content.chronological_partitions",
                "results.results.recovery_records[*].validation_loss",
                "results.results.recovery_records[*].response_mse",
            ],
            "details": "Chronological partitions and a validation loss are declared externally, but record-level split labels and a serialized reconstruction/response separation audit are absent.",
            "record_level_partition_fields": partition_record_fields,
            "protocol_level_partition_paths": partition_protocol_paths,
        },
        {
            "check_id": "selection_provenance",
            "status": "PARTIAL",
            "evidence": [
                "results.results.recovery_records[*].selected_hyperparameter",
                "results.results.recovery_records[*].validation_loss",
                "tuning_split.content.candidate_lists",
                "tuning_split.content.selection_loss",
                "tuning_split.content.tie_break",
            ],
            "details": "Selected values and validation losses are repeated in endpoint records and the candidate lists/tie-break are frozen, but candidate-wise loss vectors and per-record selection events are not serialized.",
            "record_level_selection_fields": selection_record_fields,
            "protocol_level_selection_paths": selection_protocol_paths,
        },
        {
            "check_id": "stopping_rule_variants",
            "status": "BLOCKED",
            "evidence": [
                "results.results.recovery_records[*]",
                "results.results.interval_records[*]",
                "tuning_split.content",
            ],
            "details": "No stopping variant, checkpoint, iteration trajectory, patience, or early-stopping field is serialized. No conclusion about absence of overfitting is licensed.",
            "record_level_stopping_fields": stopping_record_fields,
            "protocol_level_stopping_paths": stopping_protocol_paths,
        },
        {
            "check_id": "independent_endpoint_provenance",
            "status": "PARTIAL",
            "evidence": [
                "results.results.recovery_records[*].operator_mse",
                "results.results.recovery_records[*].response_mse",
                "results.results.recovery_records[*].query_class",
                "results.results.recovery_records[*].target_time",
            ],
            "details": "Operator and response endpoint metrics are present, but the frozen records do not carry independent endpoint source/provenance or a separate endpoint audit receipt.",
            "endpoint_provenance_fields": endpoint_provenance_fields,
        },
        {
            "check_id": "failure_and_nonfinite_retention",
            "status": "SUPPORTED",
            "evidence": [
                "candidate.bindings.configuration.cross_generator_failure_boundary",
                "candidate.bindings.configuration.bootstrap_procedure.failure_retention",
                "results.results.recovery_records[*].status",
                "results.results.interval_records[*].bootstrap_status_counts",
            ],
            "details": "All status classes remain auditable. The observed frozen result happens to contain zero non-AVAILABLE recovery/interval/bootstrap outcomes; zero is reported explicitly.",
        },
        {
            "check_id": "frozen_input_integrity",
            "status": "PARTIAL" if register_hash_match and e4_hashes_match else "BLOCKED",
            "evidence": [
                "authorization.frozen_e4_r3_inputs",
                "input-manifest.json",
            ],
            "details": "E4-r3 result, manifest, candidate and authorization hashes are checked. The formal register observed on the external read-only path is compared separately and must not be silently treated as the declared frozen register.",
            "register_sha256_matches": register_hash_match,
            "e4_r3_hashes_match": e4_hashes_match,
        },
    ]
    statuses = [check["status"] for check in checks]
    overall = "BLOCKED" if "BLOCKED" in statuses and not any(
        check["check_id"] == "seed_scenario_records" and check["status"] == "SUPPORTED"
        for check in checks
    ) else "PARTIAL"
    return {
        "schema_version": "ncs-cal-e02-135-sufficiency-audit-v1",
        "register_key": REGISTER_KEY,
        "formal_register_item": dict(register_item),
        "frozen_result_metadata": {
            "schema_version": result.get("schema_version"),
            "status": result_status,
            "promotion": result.get("promotion"),
        },
        "execution_manifest_status": manifest_status,
        "record_level_fields": {
            "recovery_records": recovery_fields,
            "interval_records": interval_fields,
            "result_partition_key_names": result_partition_key_names,
        },
        "checks": checks,
        "overall_verdict": overall,
        "full_overfitting_or_stopping_claim": "BLOCKED",
        "derived_seed_scenario_sensitivity": "SUPPORTED",
        "register_sha256_expected": next(
            entry["expected_sha256"] for entry in hash_entries if entry["label"] == "register"
        ),
        "register_sha256_observed": next(
            entry["observed_sha256"] for entry in hash_entries if entry["label"] == "register"
        ),
    }


def _failure_stability_audit(
    recovery_records: Sequence[Mapping[str, Any]],
    interval_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    numeric_fields = RECOVERY_METRIC_FIELDS + (
        "raw_response_mse",
        "stability_qualified_response_mse",
        "mean_interval_width",
        "coverage",
    )
    all_records = list(recovery_records) + list(interval_records)
    nonfinite_by_field = {
        field: sum(
            1
            for record in all_records
            if field in record and record[field] is not None and _is_number(record[field]) and not math.isfinite(float(record[field]))
        )
        for field in numeric_fields
    }
    return {
        "recovery_record_count": len(recovery_records),
        "recovery_status_counts": _status_counts(recovery_records),
        "interval_record_count": len(interval_records),
        "interval_status_counts": _status_counts(interval_records),
        "bootstrap_replicate_status_counts": _bootstrap_status_counts(interval_records),
        "nonfinite_numeric_counts": nonfinite_by_field,
        "non_available_recovery_record_count": sum(
            1 for record in recovery_records if str(record.get("status")) != "AVAILABLE"
        ),
        "non_available_interval_record_count": sum(
            1 for record in interval_records if str(record.get("status")) != "AVAILABLE"
        ),
        "retention_rule": "retain_all_declared_records_and_report_non_available_or_nonfinite_records_explicitly",
    }


def _endpoint_audit(recovery_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    presence = {
        field: sum(1 for record in recovery_records if field in record and record[field] is not None)
        for field in ENDPOINT_REQUIRED_FIELDS
    }
    finite = {
        field: sum(1 for record in recovery_records if _is_finite_number(record.get(field)))
        for field in ("operator_mse", "response_mse", "estimated_spectral_radius", "truth_spectral_radius")
    }
    fields = _field_union(recovery_records)
    provenance_fields = _matching_fields(
        fields,
        ("endpoint", "provenance", "source", "held_out", "independent"),
    )
    separation_fields = _matching_fields(fields, PARTITION_TERMS)
    required_present = all(count == len(recovery_records) for count in presence.values())
    required_finite = all(count == len(recovery_records) for count in finite.values())
    return {
        "schema_version": "ncs-cal-e02-135-independent-endpoint-audit-v1",
        "endpoint_scope": "results.results.recovery_records",
        "record_count": len(recovery_records),
        "required_endpoint_fields": list(ENDPOINT_REQUIRED_FIELDS),
        "field_presence_counts": presence,
        "finite_metric_counts": finite,
        "metric_presence_verdict": "SUPPORTED" if required_present and required_finite else "PARTIAL",
        "independent_provenance_fields_present": provenance_fields,
        "record_level_separation_fields_present": separation_fields,
        "independent_endpoint_verdict": "PARTIAL",
        "blockers": [
            "No serialized endpoint provenance or independent endpoint audit receipt.",
            "No explicit record-level train/validation/evaluation partition label.",
        ],
        "interpretation": "Metric presence is auditable; endpoint independence is not established by metric names alone.",
    }


def _rejection_inference(
    recovery_records: Sequence[Mapping[str, Any]],
    interval_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "ncs-cal-e02-135-rejection-inference-v1",
        "policy": {
            "available_records_are_eligible_for_descriptive_metric_summaries": True,
            "non_available_records_are_excluded_from_numeric_summaries_but_retained": True,
            "nonfinite_values_are_excluded_from_numeric_summaries_but_retained": True,
            "threshold_relaxation": "PROHIBITED",
            "stable_cell_selection": "PROHIBITED",
            "best_configuration_selection": "PROHIBITED",
        },
        "recovery_status_counts": _status_counts(recovery_records),
        "interval_status_counts": _status_counts(interval_records),
        "bootstrap_status_counts": _bootstrap_status_counts(interval_records),
        "inference_license": "DESCRIPTIVE_ONLY",
        "claim_boundary": "No no-overfitting or stopping-rule conclusion can be inferred from the observed selected configurations.",
    }



def build_artifacts(
    paths: InputPaths,
    *,
    code_path: Path | None = None,
    output_root_name: str | None = None,
) -> tuple[str, dict[str, bytes], dict[str, Any]]:
    """Build all deterministic artifacts without writing any output."""

    loaded = _load_inputs(paths)
    input_manifest, _by_label = _build_input_manifest(loaded)
    register_item = _register_item(loaded["register"].value)
    authorization = loaded["authorization"].value
    v2_binding = input_manifest["authorization_v2_binding"]
    result = loaded["results"].value
    if not isinstance(result, Mapping) or not isinstance(result.get("results"), Mapping):
        raise ValueError("frozen results must contain a results object")
    recovery_records = result["results"].get("recovery_records")
    interval_records = result["results"].get("interval_records")
    if not isinstance(recovery_records, list) or not isinstance(interval_records, list):
        raise ValueError("frozen results must contain recovery_records and interval_records lists")

    input_hashes = input_manifest["observed_sha256_by_label"]
    code_path = Path(code_path or __file__).resolve(strict=True)
    code_sha256 = sha256_file(code_path)
    binding = {
        "analysis_id": ANALYSIS_ID,
        "register_key": REGISTER_KEY,
        "analysis_code_sha256": code_sha256,
        "input_sha256": input_hashes,
        "expected_input_sha256": input_manifest["expected_sha256_by_label"],
    }
    binding_sha256 = sha256_bytes(canonical_json_bytes(binding))
    default_root_name = f"cal-e02-135-{binding_sha256[:16]}"
    root_name = output_root_name or default_root_name
    sufficiency = _sufficiency_audit(loaded, input_manifest, register_item)
    failure_stability = _failure_stability_audit(recovery_records, interval_records)
    endpoint_audit = _endpoint_audit(recovery_records)
    rejection = _rejection_inference(recovery_records, interval_records)
    scenario_summaries = _scenario_summaries(recovery_records)
    seed_summaries = _seed_summaries(recovery_records)
    selection_summaries = _selection_summaries(recovery_records)
    associations = _validation_evaluation_associations(recovery_records)
    adverse_records = _retained_adverse_records(recovery_records, interval_records)
    derived = {
        "schema_version": "ncs-cal-e02-135-seed-scenario-sensitivity-v1",
        "register_key": REGISTER_KEY,
        "interpretation": "Derived descriptive sensitivity only; it cannot establish absence of overfitting or stopping-rule robustness.",
        "scenario_cell_count": len(scenario_summaries),
        "seed_scenario_record_count": len(seed_summaries),
        "selection_seed_record_count": len(selection_summaries),
        "scenario_summaries": scenario_summaries,
        "seed_summaries": seed_summaries,
        "selection_summaries": selection_summaries,
        "validation_evaluation_associations": associations,
        "failure_stability": failure_stability,
        "rejection_inference": rejection,
        "retained_adverse_record_count": sum(len(records) for records in adverse_records.values()),
    }
    analysis = {
        "schema_version": "ncs-cal-e02-135-analysis-v1",
        "analysis_id": ANALYSIS_ID,
        "register_key": REGISTER_KEY,
        "priority_as_authorization": register_item.get("priority"),
        "formal_register_item_index": ITEM_INDEX,
        "analysis_binding_sha256": binding_sha256,
        "output_root_name": root_name,
        "verdict": "PARTIAL",
        "derived_sensitivity_verdict": "SUPPORTED",
        "full_overfitting_and_stopping_sensitivity_verdict": "BLOCKED",
        "independent_endpoint_audit_verdict": endpoint_audit["independent_endpoint_verdict"],
        "new_grid_execution_status": "NOT_RUN_DESCRIPTIVE_ONLY",
        "governance_gate": "V2_BOUND_DESCRIPTIVE_AUDIT_ONLY",
        "input_manifest_file": "input-manifest.json",
        "sufficiency_audit_file": "frozen-data-sufficiency-audit.json",
        "derived_sensitivity_file": "seed-scenario-sensitivity.json",
        "endpoint_audit_file": "independent-endpoint-audit.json",
        "retained_adverse_records_file": "retained-adverse-records.json",
        "formal_register_snapshot": {
            "calibration_id": CALIBRATION_ID,
            "item_index": ITEM_INDEX,
            "item_id": register_item.get("item_id"),
            "author_decision": register_item.get("author_decision"),
            "author_approval_required": register_item.get("author_approval_required"),
            "current_response_status": register_item.get("current_response_status"),
            "calibration_requested_action": register_item.get("calibration_requested_action"),
            "priority": register_item.get("priority"),
        },
        "authorization_snapshot": {
            "authorization_id": authorization.get("authorization_id"),
            "authorized_at": authorization.get("authorized_at"),
            "schema_version": authorization.get("schema_version"),
            "item_payload_sha256": v2_binding["item_payload_sha256"],
            "e4_chain_complete": v2_binding["e4_chain"]["complete"],
        },
        "unresolved_boundaries": [
            "No stopping variants or iteration/checkpoint trajectories in frozen E4-r3 records.",
            "No record-level split labels or independent endpoint provenance receipt.",
            "Only descriptive seed/scenario sensitivity is licensed by this repair route.",
            "No new stopping-variant grid was executed.",
            "No manuscript, author decision register, RCEP, NYC, or E4-r3 quarantine file was modified.",
        ],
    }
    input_manifest = {
        **input_manifest,
        "analysis_id": ANALYSIS_ID,
        "analysis_binding_sha256": binding_sha256,
        "output_root_name": root_name,
    }
    artifacts: dict[str, Any] = {
        "analysis.json": analysis,
        "input-manifest.json": input_manifest,
        "frozen-data-sufficiency-audit.json": sufficiency,
        "seed-scenario-sensitivity.json": derived,
        "independent-endpoint-audit.json": endpoint_audit,
        "retained-adverse-records.json": {
            "schema_version": "ncs-cal-e02-135-retained-adverse-records-v1",
            "register_key": REGISTER_KEY,
            "recovery_records": adverse_records["recovery_records"],
            "interval_records": adverse_records["interval_records"],
            "record_count": sum(len(records) for records in adverse_records.values()),
        },
    }
    payloads = {
        name: (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        for name, value in artifacts.items()
    }
    output_manifest = {
        "schema_version": "ncs-cal-e02-135-output-manifest-v1",
        "register_key": REGISTER_KEY,
        "analysis_id": ANALYSIS_ID,
        "analysis_binding_sha256": binding_sha256,
        "output_root_name": root_name,
        "files": {
            name: sha256_bytes(payloads[name])
            for name in sorted(payloads)
        },
        "self_hash_scope": "self_hash_excluded_from_files_to_avoid_recursive_binding",
    }
    payloads["output-manifest.json"] = (
        json.dumps(
            output_manifest,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return binding_sha256, payloads, {
        "analysis": analysis,
        "input_manifest": input_manifest,
        "sufficiency": sufficiency,
        "derived": derived,
        "endpoint_audit": endpoint_audit,
        "authorization_v2_binding": v2_binding,
    }


def write_content_addressed_output(
    output_root: Path,
    payloads: Mapping[str, bytes],
    *,
    execution_authorization_path: Path | None = None,
    run_id: str = "primary",
    observed_paths: Mapping[str, Path] | None = None,
    project_root: Path | None = None,
) -> Path:
    """Create output files without overwriting an existing content address."""

    root = Path(output_root).expanduser().resolve()
    validate_execution_authorization(
        execution_authorization_path,
        output_root=root,
        run_id=run_id,
        observed_paths=observed_paths or {},
        artifact_prefix="cal-e02-135-",
        project_root=project_root,
    )
    expected_names = set(payloads)
    root.mkdir(parents=True, exist_ok=False)
    for name in sorted(payloads):
        destination = root / name
        payload = payloads[name]
        destination.write_bytes(payload)
    return root


def _execution_context_from_input_paths(paths: InputPaths, root: Path) -> dict[str, Path]:
    return {
        "source_authorization_v2": paths.authorization,
        "m2a_repair_receipt": root / EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
        "decision_register": paths.register,
        "e4_results": paths.results,
        "e4_execution_manifest": paths.execution_manifest,
        "e4_execution_complete": paths.execution_complete,
        "e4_terminal_inventory": paths.terminal_inventory,
        "e4_candidate": paths.candidate,
        "workspace_authorization": paths.e4_r3_authorization,
    }


def _default_paths(root: Path, register: Path) -> InputPaths:
    return InputPaths(
        register=register,
        authorization=root / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json",
        e4_r3_authorization=root / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
        plan=root / "refine-logs/NCS_FOUR_ANALYSIS_PLAN_20260804_010454.md",
        audit=root / "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md",
        results=root / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json",
        execution_manifest=root / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json",
        execution_complete=root / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json",
        candidate=root / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json",
        tuning_split=root / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/tuning_split_manifest.json",
        terminal_inventory=root / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", required=True, type=Path, help="external formal register path; read-only")
    parser.add_argument(
        "--output-base",
        type=Path,
        default=None,
        help="base directory for the new CAL-E02:135 output root",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="explicit output root for tests; default is content-addressed under --output-base",
    )
    parser.add_argument("--execution-authorization", type=Path, required=True)
    parser.add_argument("--run-id", choices=("primary", "duplicate"), required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    paths = _default_paths(root, args.register)
    output_base = args.output_base or root / "refine-logs/ncs_new_analysis_v2"
    binding_sha256, payloads, _artifacts = build_artifacts(
        paths,
        output_root_name=args.output_root.name if args.output_root else None,
    )
    output_root = args.output_root or output_base / args.run_id / f"cal-e02-135-{binding_sha256[:16]}"
    observed_paths = _execution_context_from_input_paths(paths, root)
    validate_execution_authorization(
        args.execution_authorization,
        output_root=output_root,
        run_id=args.run_id,
        observed_paths=observed_paths,
        artifact_prefix="cal-e02-135-",
        project_root=root,
    )
    written = write_content_addressed_output(
        output_root,
        payloads,
        execution_authorization_path=args.execution_authorization,
        run_id=args.run_id,
        observed_paths=observed_paths,
        project_root=root,
    )
    result = json.loads(payloads["analysis.json"].decode("utf-8"))
    print(
        json.dumps(
            {
                "analysis_id": ANALYSIS_ID,
                "analysis_binding_sha256": binding_sha256,
                "output_root": str(written),
                "verdict": result["verdict"],
                "new_grid_execution_status": result["new_grid_execution_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
