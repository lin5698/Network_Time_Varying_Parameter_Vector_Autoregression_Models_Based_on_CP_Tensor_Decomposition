"""Immutable schemas for the governed R006e screening v2 executor."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from scripts.experiments.r006e_native_experiment import (
    SCREENING_CSV_FIELDS,
    SCREENING_FLAG_FIELDS,
    SCREENING_INTEGER_FIELDS,
    SCREENING_NULLABLE_FIELDS,
    SCREENING_STRING_FIELDS,
)
from scripts.experiments.r006e_native_protocol import (
    METHODS,
    SCREENING_SEEDS,
    keyed_seed,
    primary_cells,
)


SCHEMA_VERSION = 2
FORMAL_PEAK_MEMORY_SCOPE = (
    "fresh_worker_full_cell_panel_certificate_fit_evaluation"
)
REQUIRED_WORKERS = 6
EXPECTED_ROWS = 320
EVALUATION_CLASSIFICATION = "simulation-only"
V2_PRIMARY_ROOT = (
    "output/high_impact_revision/r006e_native_supported_recovery_v2"
)
V2_REPEAT_ROOT = (
    "output/high_impact_revision/r006e_native_supported_recovery_v2_repeat"
)
V2_CONTROL_ROOT = (
    "output/high_impact_revision/r006e_native_supported_recovery_v2_control"
)
SCREENING_OUTPUT_NAMES = (
    "screening_replications.csv",
    "screening_summary.csv",
    "screening_results.json",
)
FORMAL_REPLICATION_FIELDS = tuple(
    field for field in SCREENING_CSV_FIELDS if field != "peak_memory_worker_pid"
)
FORMAL_REPLICATION_FLAG_FIELDS = frozenset(
    field for field in SCREENING_FLAG_FIELDS if field in FORMAL_REPLICATION_FIELDS
)
FORMAL_REPLICATION_INTEGER_FIELDS = frozenset(SCREENING_INTEGER_FIELDS).difference(
    {"peak_memory_worker_pid"}, FORMAL_REPLICATION_FLAG_FIELDS
)
SUMMARY_FIELDS = (
    "availability",
    "finite_and_converged",
    "operator_relative_error",
    "response_zero_ratio",
    "paired_improvement",
    "joint_win_rate",
    "worst_endpoint_improvement",
    "observed_rmse_guardrail",
    "w_ref_guardrail",
)
SUMMARY_ROW_FIELDS = (
    "rho",
    "a3",
    "eta",
    "passed",
    *SUMMARY_FIELDS,
    "failed_conditions_json",
    "audit_values_json",
)
SUMMARY_BOOLEAN_FIELDS = frozenset({"passed", *SUMMARY_FIELDS})
DIAGNOSTIC_FIELDS = (
    "seed",
    "rho",
    "a3",
    "eta",
    "method",
    "method_seed",
    "fit_sha256",
    "fit_success",
    "scorable",
    "failure_code",
    "failure_reason",
    "fit_diagnostics_json",
    "generated_at",
)
RESOURCE_FIELDS = (
    "seed",
    "rho",
    "a3",
    "eta",
    "method",
    "worker_pid",
    "peak_memory_bytes",
    "peak_memory_scope",
    "attempt_id",
    "role",
)
ROW_JOURNAL_FIELDS = (
    "seed",
    "rho",
    "a3",
    "eta",
    "method",
    "attempt_id",
    "role",
    "row_status",
    "replication_sha256",
    "diagnostic_sha256",
    "resource_sha256",
    "generated_at",
)
ALLOWED_DUPLICATE_EXCLUSIONS = frozenset(
    {"runtime_seconds", "peak_memory_bytes", "generated_at"}
)
COMPARABLE_SCIENTIFIC_FIELDS = ("replication", "summary", "result")
OPERATIONAL_FIELD_NAMES = frozenset(
    {
        "attempt_id",
        "role",
        "worker_pid",
        "peak_memory_worker_pid",
        "hostname",
        "supervisor_pid",
        "supervisor_hostname",
        "authorization_artifact_sha256",
        "authorization_payload_sha256",
        "trust_evidence",
        "trust_evidence_sha256",
        "replication_sha256",
        "summary_sha256",
        "result_sha256",
        "diagnostics_sha256",
        "resources_sha256",
        "row_journal_sha256",
        "diagnostics",
        "resources",
        "row_journal",
        "terminal",
        "manifest",
    }
)
SUMMARY_IDENTITIES = primary_cells()
REPLICATION_IDENTITIES = tuple(
    (seed, rho, a3, eta, method)
    for seed in SCREENING_SEEDS
    for rho, a3, eta in SUMMARY_IDENTITIES
    for method in METHODS
)
RECORD_CARDINALITIES = MappingProxyType(
    {
        "replication": 320,
        "diagnostic": 320,
        "resource": 320,
        "row_journal": 320,
        "summary": 8,
    }
)
FAILED_CELL_RECORDS_BY_CLASS = MappingProxyType(
    {"replication": 4, "diagnostic": 4, "resource": 4, "row_journal": 4}
)

AUTHORIZATION_PAYLOAD_FIELDS = (
    "schema_version",
    "document_type",
    "decision",
    "phase",
    "decision_id",
    "authorizer_id",
    "issued_at",
    "checklist_sha256",
    "protocol_sha256",
    "plan_sha256",
    "runner_contract_sha256",
    "construction_file_sha256",
    "construction_canonical_sha256",
    "provenance_sha256",
    "config_sha256",
    "dependency_manifest_sha256",
    "source_manifest_sha256",
    "candidate_sha256",
    "frozen_v1_authority_digest",
    "primary_root",
    "repeat_root",
    "control_root",
    "primary_attempt_id",
    "repeat_attempt_id",
    "workers",
    "seeds",
    "cells",
    "methods",
    "output_names",
    "expected_rows",
)
AUTHORIZATION_ENVELOPE_FIELDS = (
    "schema_version",
    "document_type",
    "payload",
    "payload_sha256",
    "artifact_sha256",
    "trust_evidence",
    "trust_evidence_sha256",
)
TRUST_EVIDENCE_FIELDS = (
    "schema_version",
    "document_type",
    "authorization_artifact_sha256",
    "signed_payload_sha256",
    "signature_algorithm",
    "pinned_key_id",
    "detached_signature",
    "detached_signature_sha256",
    "trust_policy_id",
    "external_witness_id",
)
PAIR_CLAIM_FIELDS = (
    "schema_version",
    "document_type",
    "decision_id",
    "authorization_artifact_sha256",
    "authorization_payload_sha256",
    "trust_evidence_sha256",
    "frozen_v1_authority_digest",
    "primary_attempt_id",
    "repeat_attempt_id",
    "primary_root",
    "repeat_root",
    "control_root",
    "claimed_at",
    "supervisor_pid",
    "supervisor_hostname",
    "status",
)
ROLE_START_FIELDS = (
    "schema_version",
    "document_type",
    "decision_id",
    "attempt_id",
    "role",
    "pair_claim_sha256",
    "started_at",
    "worker_pid",
    "hostname",
    "status",
)
TERMINAL_FIELDS = (
    "schema_version",
    "document_type",
    "decision_id",
    "attempt_id",
    "role",
    "status",
    "pair_claim_sha256",
    "role_start_sha256",
    "replication_sha256",
    "summary_sha256",
    "result_sha256",
    "diagnostics_sha256",
    "resources_sha256",
    "row_journal_sha256",
    "started_at",
    "finished_at",
    "exit_code",
    "failure_code",
    "failure_reason",
)
SCIENTIFIC_RESULT_FIELDS = (
    "schema_version",
    "document_type",
    "status",
    "semantic_replication_sha256",
    "semantic_summary_sha256",
    "construction_sha256",
    "config_sha256",
    "candidate_sha256",
    "provenance_sha256",
    "seed_ids",
    "identity_completeness",
    "evaluation_classification",
)
DUPLICATE_COMPARISON_FIELDS = (
    "schema_version",
    "document_type",
    "status",
    "compared_payloads",
    "primary_replication_sha256",
    "repeat_replication_sha256",
    "primary_summary_sha256",
    "repeat_summary_sha256",
    "primary_result_sha256",
    "repeat_result_sha256",
    "mismatch_paths",
)
MANIFEST_FIELDS = (
    "schema_version",
    "document_type",
    "decision_id",
    "attempt_id",
    "role",
    "status",
    "pair_claim_sha256",
    "role_start_sha256",
    "terminal_sha256",
    "replication_sha256",
    "summary_sha256",
    "result_sha256",
    "diagnostics_sha256",
    "resources_sha256",
    "row_journal_sha256",
    "replication_count",
    "summary_count",
    "diagnostic_count",
    "resource_count",
    "row_journal_count",
    "identity_set_sha256",
    "generated_at",
)
DOCUMENT_TYPES = MappingProxyType(
    {
        "authorization_payload": "r006e_screening_authorization_payload_v2",
        "authorization_envelope": "r006e_screening_authorization_envelope_v2",
        "trust_evidence": "r006e_screening_trust_evidence_v2",
        "pair_claim": "r006e_screening_pair_claim_v2",
        "role_start": "r006e_screening_role_start_v2",
        "terminal": "r006e_screening_terminal_v2",
        "scientific_result": "r006e_screening_scientific_result_v2",
        "duplicate_comparison": "r006e_screening_duplicate_comparison_v2",
        "manifest": "r006e_screening_manifest_v2",
    }
)

SCHEMA_FIELDS = MappingProxyType(
    {
        "authorization_payload": AUTHORIZATION_PAYLOAD_FIELDS,
        "authorization_envelope": AUTHORIZATION_ENVELOPE_FIELDS,
        "trust_evidence": TRUST_EVIDENCE_FIELDS,
        "pair_claim": PAIR_CLAIM_FIELDS,
        "role_start": ROLE_START_FIELDS,
        "row_journal": ROW_JOURNAL_FIELDS,
        "terminal": TERMINAL_FIELDS,
        "scientific_result": SCIENTIFIC_RESULT_FIELDS,
        "duplicate_comparison": DUPLICATE_COMPARISON_FIELDS,
        "manifest": MANIFEST_FIELDS,
    }
)
FORMAL_REPLICATION_NULLABLE_FIELDS = frozenset(SCREENING_NULLABLE_FIELDS)
DIAGNOSTIC_NULLABLE_FIELDS = frozenset(
    {"fit_sha256", "failure_code", "failure_reason", "fit_diagnostics_json"}
)
TERMINAL_NULLABLE_FIELDS = frozenset(
    {
        "role_start_sha256",
        "replication_sha256",
        "summary_sha256",
        "result_sha256",
        "diagnostics_sha256",
        "resources_sha256",
        "row_journal_sha256",
        "started_at",
        "exit_code",
        "failure_code",
        "failure_reason",
    }
)
MANIFEST_NULLABLE_FIELDS = frozenset(
    {
        "role_start_sha256",
        "replication_sha256",
        "summary_sha256",
        "result_sha256",
        "diagnostics_sha256",
        "resources_sha256",
        "row_journal_sha256",
    }
)
NULLABLE_FIELDS = MappingProxyType(
    {
        "authorization_payload": frozenset(),
        "authorization_envelope": frozenset(),
        "trust_evidence": frozenset(),
        "pair_claim": frozenset(),
        "role_start": frozenset(),
        "row_journal": frozenset(),
        "terminal": TERMINAL_NULLABLE_FIELDS,
        "scientific_result": frozenset(),
        "duplicate_comparison": frozenset(),
        "manifest": MANIFEST_NULLABLE_FIELDS,
    }
)

TERMINAL_STATES = frozenset({"PASS", "FAIL", "INCOMPLETE"})
PASS_FAIL_STATES = frozenset({"PASS", "FAIL"})
ATTEMPT_STATES = frozenset({"CLAIMED", "STARTED", *TERMINAL_STATES})
LEGAL_STATE_TRANSITIONS = MappingProxyType(
    {
        "CLAIMED": frozenset({"STARTED", "INCOMPLETE"}),
        "STARTED": TERMINAL_STATES,
        "PASS": frozenset(),
        "FAIL": frozenset(),
        "INCOMPLETE": frozenset(),
    }
)


class SchemaValidationError(ValueError):
    """Raised when a v2 object violates its frozen structural schema."""


def derive_attempt_id(decision_id: str, role: str) -> str:
    """Derive the authorization-bound role attempt ID."""

    if not isinstance(decision_id, str) or not decision_id:
        raise ValueError("decision_id must be a non-empty string")
    if role not in {"primary", "repeat"}:
        raise ValueError("role must be primary or repeat")
    material = f"R006E_SCREENING_V2_ATTEMPT\0{decision_id}\0{role}".encode("utf-8")
    return "r006e-v2-" + hashlib.sha256(material).hexdigest()


def validate_state_transition(current: str, target: str) -> str:
    """Reject every lifecycle edge not frozen by the v2 protocol."""

    if current not in ATTEMPT_STATES or target not in ATTEMPT_STATES:
        raise SchemaValidationError(f"unknown attempt state: {current!r} -> {target!r}")
    if target not in LEGAL_STATE_TRANSITIONS[current]:
        raise SchemaValidationError(f"illegal transition: {current} -> {target}")
    return target


def _validate_json_value(value: Any, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SchemaValidationError(f"non-finite JSON number at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise SchemaValidationError(f"non-string JSON key at {path}")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise SchemaValidationError(f"unsupported JSON value at {path}")


def _require_exact_int(value: Any, path: str, expected: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaValidationError(f"{path} must be an integer")
    if expected is not None and value != expected:
        raise SchemaValidationError(f"{path} must equal {expected}")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise SchemaValidationError(f"{path} must be a boolean")
    return value


def _require_binary_int(value: Any, path: str) -> int:
    if type(value) is not int or value not in {0, 1}:
        raise SchemaValidationError(f"{path} must be the integer 0 or 1")
    return value


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise SchemaValidationError(f"{path} must be a string")
    return value


def _require_literal(value: Any, path: str, expected: str) -> str:
    if value != expected:
        raise SchemaValidationError(f"{path} must equal {expected!r}")
    return expected


def _require_member(value: Any, path: str, allowed: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise SchemaValidationError(f"{path} must be one of: {allowed_values}")
    return value


def _require_exact_sequence(
    value: Any, path: str, expected: tuple[Any, ...]
) -> tuple[Any, ...]:
    if not isinstance(value, list):
        raise SchemaValidationError(f"{path} must be a JSON array")
    actual = tuple(value)
    if actual != expected:
        raise SchemaValidationError(f"{path} must equal the frozen ordered sequence")
    return actual


def _validate_schema_semantics(name: str, value: Mapping[str, Any]) -> None:
    if "schema_version" in value:
        _require_exact_int(
            value["schema_version"], f"{name}.schema_version", SCHEMA_VERSION
        )
    if "document_type" in value and name in DOCUMENT_TYPES:
        _require_literal(
            value["document_type"],
            f"{name}.document_type",
            DOCUMENT_TYPES[name],
        )

    if name == "authorization_payload":
        _require_literal(value["decision"], f"{name}.decision", "AUTHORIZE")
        _require_literal(value["phase"], f"{name}.phase", "SCREENING")
        _require_literal(value["primary_root"], f"{name}.primary_root", V2_PRIMARY_ROOT)
        _require_literal(value["repeat_root"], f"{name}.repeat_root", V2_REPEAT_ROOT)
        _require_literal(value["control_root"], f"{name}.control_root", V2_CONTROL_ROOT)
        _require_exact_int(value["workers"], f"{name}.workers", REQUIRED_WORKERS)
        _require_exact_int(value["expected_rows"], f"{name}.expected_rows", EXPECTED_ROWS)
        _require_exact_sequence(value["seeds"], f"{name}.seeds", SCREENING_SEEDS)
        expected_cells = tuple(list(cell) for cell in SUMMARY_IDENTITIES)
        _require_exact_sequence(value["cells"], f"{name}.cells", expected_cells)
        _require_exact_sequence(value["methods"], f"{name}.methods", METHODS)
        _require_exact_sequence(
            value["output_names"],
            f"{name}.output_names",
            SCREENING_OUTPUT_NAMES,
        )
        decision_id = _require_string(value["decision_id"], f"{name}.decision_id")
        _require_literal(
            value["primary_attempt_id"],
            f"{name}.primary_attempt_id",
            derive_attempt_id(decision_id, "primary"),
        )
        _require_literal(
            value["repeat_attempt_id"],
            f"{name}.repeat_attempt_id",
            derive_attempt_id(decision_id, "repeat"),
        )
        return

    if name == "authorization_envelope":
        return

    if name == "trust_evidence":
        return

    if name == "pair_claim":
        _require_literal(value["status"], f"{name}.status", "CLAIMED")
        _require_literal(value["primary_root"], f"{name}.primary_root", V2_PRIMARY_ROOT)
        _require_literal(value["repeat_root"], f"{name}.repeat_root", V2_REPEAT_ROOT)
        _require_literal(value["control_root"], f"{name}.control_root", V2_CONTROL_ROOT)
        decision_id = _require_string(value["decision_id"], f"{name}.decision_id")
        _require_literal(
            value["primary_attempt_id"],
            f"{name}.primary_attempt_id",
            derive_attempt_id(decision_id, "primary"),
        )
        _require_literal(
            value["repeat_attempt_id"],
            f"{name}.repeat_attempt_id",
            derive_attempt_id(decision_id, "repeat"),
        )
        return

    if name == "row_journal":
        _require_member(value["role"], f"{name}.role", frozenset({"primary", "repeat"}))
        return

    if name == "role_start":
        role = _require_member(value["role"], f"{name}.role", frozenset({"primary", "repeat"}))
        _require_literal(value["status"], f"{name}.status", "STARTED")
        decision_id = _require_string(value["decision_id"], f"{name}.decision_id")
        _require_literal(
            value["attempt_id"],
            f"{name}.attempt_id",
            derive_attempt_id(decision_id, role),
        )
        return

    if name == "terminal":
        role = _require_member(value["role"], f"{name}.role", frozenset({"primary", "repeat"}))
        _require_member(value["status"], f"{name}.status", TERMINAL_STATES)
        decision_id = _require_string(value["decision_id"], f"{name}.decision_id")
        _require_literal(
            value["attempt_id"],
            f"{name}.attempt_id",
            derive_attempt_id(decision_id, role),
        )
        return

    if name == "scientific_result":
        _require_member(value["status"], f"{name}.status", TERMINAL_STATES)
        _require_exact_sequence(value["seed_ids"], f"{name}.seed_ids", SCREENING_SEEDS)
        _require_bool(
            value["identity_completeness"],
            f"{name}.identity_completeness",
        )
        _require_literal(
            value["evaluation_classification"],
            f"{name}.evaluation_classification",
            EVALUATION_CLASSIFICATION,
        )
        return

    if name == "duplicate_comparison":
        _require_member(value["status"], f"{name}.status", PASS_FAIL_STATES)
        _require_exact_sequence(
            value["compared_payloads"],
            f"{name}.compared_payloads",
            COMPARABLE_SCIENTIFIC_FIELDS,
        )
        return

    if name == "manifest":
        role = _require_member(value["role"], f"{name}.role", frozenset({"primary", "repeat"}))
        _require_member(value["status"], f"{name}.status", ATTEMPT_STATES)
        decision_id = _require_string(value["decision_id"], f"{name}.decision_id")
        _require_literal(
            value["attempt_id"],
            f"{name}.attempt_id",
            derive_attempt_id(decision_id, role),
        )
        for field_name, expected in RECORD_CARDINALITIES.items():
            manifest_field = f"{field_name}_count"
            if manifest_field in value:
                _require_exact_int(value[manifest_field], f"{name}.{manifest_field}", expected)
        return

    raise SchemaValidationError(f"unknown schema semantics: {name}")


def _require_ordered_fields(
    name: str, value: Mapping[str, Any], fields: tuple[str, ...]
) -> None:
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{name} must be a JSON object")
    actual = tuple(value)
    if frozenset(actual) != frozenset(fields):
        unknown = sorted(frozenset(actual) - frozenset(fields))
        missing = sorted(frozenset(fields) - frozenset(actual))
        raise SchemaValidationError(
            f"{name} key mismatch: unknown={unknown}, missing={missing}"
        )
    if actual != fields:
        raise SchemaValidationError(f"{name} field order mismatch")


def _require_sha256(value: Any, path: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise SchemaValidationError(f"{path} must be a lowercase SHA-256")
    return value


def _parse_json_string(value: Any, path: str, expected_type: type) -> Any:
    if type(value) is not str:
        raise SchemaValidationError(f"{path} must be a JSON string")
    try:
        parsed = json.loads(
            value,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"non-finite constant {constant}")
            ),
        )
    except (TypeError, ValueError) as error:
        raise SchemaValidationError(f"{path} must encode finite JSON") from error
    if type(parsed) is not expected_type:
        raise SchemaValidationError(
            f"{path} must encode a JSON {expected_type.__name__}"
        )
    _validate_json_value(parsed, path)
    return parsed


def validate_formal_replication_record(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate one ordered formal replication record without aggregation."""

    name = "formal_replication"
    _require_ordered_fields(name, value, FORMAL_REPLICATION_FIELDS)
    for field, item in value.items():
        if item is None and field not in FORMAL_REPLICATION_NULLABLE_FIELDS:
            raise SchemaValidationError(f"{name}.{field} is not nullable")
    _validate_json_value(value, name)
    _require_exact_int(value["seed"], f"{name}.seed")
    for field in ("rho", "a3", "eta"):
        item = value[field]
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise SchemaValidationError(f"{name}.{field} must be numeric")
        if not math.isfinite(float(item)):
            raise SchemaValidationError(f"{name}.{field} must be finite")
    _require_member(value["method"], f"{name}.method", frozenset(METHODS))
    for field in FORMAL_REPLICATION_FLAG_FIELDS:
        _require_binary_int(value[field], f"{name}.{field}")
    for field in FORMAL_REPLICATION_INTEGER_FIELDS:
        if value[field] is not None:
            _require_exact_int(value[field], f"{name}.{field}")
    for field in SCREENING_STRING_FIELDS.intersection(FORMAL_REPLICATION_FIELDS):
        item = value[field]
        if item is not None and (type(item) is not str or not item):
            raise SchemaValidationError(f"{name}.{field} must be a non-empty string")
    classified = {
        "seed", "rho", "a3", "eta", "method",
        *FORMAL_REPLICATION_FLAG_FIELDS,
        *FORMAL_REPLICATION_INTEGER_FIELDS,
        *SCREENING_STRING_FIELDS,
    }
    for field in FORMAL_REPLICATION_FIELDS:
        item = value[field]
        if field in classified or item is None:
            continue
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise SchemaValidationError(f"{name}.{field} must be numeric")
        if not math.isfinite(float(item)):
            raise SchemaValidationError(f"{name}.{field} must be finite")
    _require_sha256(value["fit_sha256"], f"{name}.fit_sha256")
    if value["parameterization"] not in {"anchor", "runner_failure"}:
        raise SchemaValidationError(
            f"{name}.parameterization has an invalid literal"
        )
    if value["peak_memory_scope"] != FORMAL_PEAK_MEMORY_SCOPE:
        raise SchemaValidationError(
            f"{name}.peak_memory_scope must equal {FORMAL_PEAK_MEMORY_SCOPE!r}"
        )
    _parse_json_string(value["fit_diagnostics_json"], "fit_diagnostics_json", dict)
    reasons = _parse_json_string(
        value["endpoint_failure_reasons_json"],
        "endpoint_failure_reasons_json",
        list,
    )
    if any(type(reason) is not str or not reason for reason in reasons):
        raise SchemaValidationError(
            "endpoint_failure_reasons_json entries must be non-empty strings"
        )
    if (value["failure_code"] is None) != (value["failure_reason"] is None):
        raise SchemaValidationError("failure_code and failure_reason must be paired")
    return value


def _validate_method_identity(name: str, value: Mapping[str, Any]) -> None:
    _require_exact_int(value["seed"], f"{name}.seed")
    for field in ("rho", "a3", "eta"):
        item = value[field]
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise SchemaValidationError(f"{name}.{field} must be numeric")
        if not math.isfinite(float(item)):
            raise SchemaValidationError(f"{name}.{field} must be finite")
    _require_member(value["method"], f"{name}.method", frozenset(METHODS))


def validate_diagnostic_record(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate one ordered method-level diagnostic record."""

    name = "diagnostic"
    _require_ordered_fields(name, value, DIAGNOSTIC_FIELDS)
    for field, item in value.items():
        if item is None and field not in DIAGNOSTIC_NULLABLE_FIELDS:
            raise SchemaValidationError(f"{name}.{field} is not nullable")
    _validate_json_value(value, name)
    _validate_method_identity(name, value)
    method_seed = _require_exact_int(value["method_seed"], f"{name}.method_seed")
    expected_seed = keyed_seed(
        value["seed"], value["rho"], value["a3"], value["eta"], "optimizer"
    )
    if method_seed != expected_seed:
        raise SchemaValidationError("diagnostic.method_seed mismatch")
    if value["fit_sha256"] is not None:
        _require_sha256(value["fit_sha256"], f"{name}.fit_sha256")
    _require_bool(value["fit_success"], f"{name}.fit_success")
    _require_bool(value["scorable"], f"{name}.scorable")
    if (value["failure_code"] is None) != (value["failure_reason"] is None):
        raise SchemaValidationError("diagnostic failure fields must be paired")
    for field in ("failure_code", "failure_reason", "generated_at"):
        item = value[field]
        if item is not None and (type(item) is not str or not item):
            raise SchemaValidationError(f"{name}.{field} must be non-empty string")
    if value["scorable"]:
        if not value["fit_success"]:
            raise SchemaValidationError("scorable diagnostic requires fit_success")
        if value["failure_code"] is not None:
            raise SchemaValidationError("scorable diagnostic cannot retain failure details")
    elif value["failure_code"] is None:
        raise SchemaValidationError(
            "nonscorable diagnostic requires paired failure details"
        )
    if value["fit_diagnostics_json"] is not None:
        _parse_json_string(
            value["fit_diagnostics_json"], "fit_diagnostics_json", dict
        )
    return value


def _require_attempt_id(value: Any, path: str) -> str:
    prefix = "r006e-v2-"
    if type(value) is not str or not value.startswith(prefix):
        raise SchemaValidationError(f"{path} must be a deterministic attempt_id")
    _require_sha256(value[len(prefix):], path)
    return value


def validate_resource_record(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate one ordered per-method resource record."""

    name = "resource"
    _require_ordered_fields(name, value, RESOURCE_FIELDS)
    for field, item in value.items():
        if item is None:
            raise SchemaValidationError(f"{name}.{field} is not nullable")
    _validate_json_value(value, name)
    _validate_method_identity(name, value)
    worker_pid = _require_exact_int(value["worker_pid"], f"{name}.worker_pid")
    if worker_pid <= 0:
        raise SchemaValidationError("resource.worker_pid must be positive")
    peak = _require_exact_int(
        value["peak_memory_bytes"], f"{name}.peak_memory_bytes"
    )
    if peak < 0:
        raise SchemaValidationError("resource.peak_memory_bytes must be nonnegative")
    if value["peak_memory_scope"] != FORMAL_PEAK_MEMORY_SCOPE:
        raise SchemaValidationError("resource.peak_memory_scope literal mismatch")
    _require_attempt_id(value["attempt_id"], f"{name}.attempt_id")
    _require_member(value["role"], f"{name}.role", frozenset({"primary", "repeat"}))
    return value


def validate_row_journal_record(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate one ordered immutable row-journal record."""

    name = "row_journal"
    _require_ordered_fields(name, value, ROW_JOURNAL_FIELDS)
    for field, item in value.items():
        if item is None:
            raise SchemaValidationError(f"{name}.{field} is not nullable")
    _validate_json_value(value, name)
    _validate_method_identity(name, value)
    _require_attempt_id(value["attempt_id"], f"{name}.attempt_id")
    _require_member(value["role"], f"{name}.role", frozenset({"primary", "repeat"}))
    _require_member(
        value["row_status"],
        f"{name}.row_status",
        frozenset({"RECORDED", "RUNNER_FAILURE"}),
    )
    for field in (
        "replication_sha256",
        "diagnostic_sha256",
        "resource_sha256",
    ):
        _require_sha256(value[field], f"{name}.{field}")
    if type(value["generated_at"]) is not str or not value["generated_at"]:
        raise SchemaValidationError("row_journal.generated_at must be non-empty string")
    return value


def _validated_field_names(
    name: str, value: Mapping[Any, Any]
) -> frozenset[str]:
    for key in value:
        if not isinstance(key, str):
            raise SchemaValidationError(f"non-string JSON key at {name}")
    return frozenset(value)


def validate_schema(name: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Require the exact named key set and recursively finite JSON values."""

    if name not in SCHEMA_FIELDS:
        raise SchemaValidationError(f"unknown schema: {name}")
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{name} must be a JSON object")
    expected = frozenset(SCHEMA_FIELDS[name])
    actual = _validated_field_names(name, value)
    unknown = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unknown:
        raise SchemaValidationError(f"{name} has unknown keys: {unknown}")
    if missing:
        raise SchemaValidationError(f"{name} has missing keys: {missing}")
    for field, item in value.items():
        if item is None and field not in NULLABLE_FIELDS[name]:
            raise SchemaValidationError(f"{name}.{field} is not nullable")
    _validate_json_value(value, name)
    _validate_schema_semantics(name, value)
    return value


def _reject_operational_fields(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in OPERATIONAL_FIELD_NAMES:
                raise SchemaValidationError(f"operational field at {path}.{key}")
            _reject_operational_fields(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_operational_fields(item, f"{path}[{index}]")


def _validate_exact_fields(
    name: str, value: Mapping[str, Any], fields: tuple[str, ...]
) -> None:
    if not isinstance(value, Mapping):
        raise SchemaValidationError(f"{name} must be a JSON object")
    actual = _validated_field_names(name, value)
    expected = frozenset(fields)
    unknown = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unknown:
        raise SchemaValidationError(f"{name} has unknown keys: {unknown}")
    if missing:
        raise SchemaValidationError(f"{name} has missing keys: {missing}")


def validate_comparable_scientific_payload(
    value: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Validate exactly replication, summary, and result scientific payloads."""

    _validate_exact_fields("scientific_payload", value, COMPARABLE_SCIENTIFIC_FIELDS)
    _reject_operational_fields(value, "scientific_payload")
    replications = value["replication"]
    summaries = value["summary"]
    if not isinstance(replications, list) or not isinstance(summaries, list):
        raise SchemaValidationError("replication and summary must be JSON arrays")
    if len(replications) != RECORD_CARDINALITIES["replication"]:
        raise SchemaValidationError("replication cardinality must equal 320")
    if len(summaries) != RECORD_CARDINALITIES["summary"]:
        raise SchemaValidationError("summary cardinality must equal 8")
    for index, row in enumerate(replications):
        _validate_exact_fields(
            f"replication[{index}]", row, FORMAL_REPLICATION_FIELDS
        )
        for field, item in row.items():
            if item is None and field not in FORMAL_REPLICATION_NULLABLE_FIELDS:
                raise SchemaValidationError(
                    f"replication[{index}].{field} is not nullable"
                )
        _require_exact_int(row["seed"], f"replication[{index}].seed")
        if isinstance(row["rho"], bool) or not isinstance(row["rho"], (int, float)):
            raise SchemaValidationError(f"replication[{index}].rho must be numeric")
        if isinstance(row["a3"], bool) or not isinstance(row["a3"], (int, float)):
            raise SchemaValidationError(f"replication[{index}].a3 must be numeric")
        if isinstance(row["eta"], bool) or not isinstance(row["eta"], (int, float)):
            raise SchemaValidationError(f"replication[{index}].eta must be numeric")
        _require_member(
            row["method"],
            f"replication[{index}].method",
            frozenset(METHODS),
        )
        for field in FORMAL_REPLICATION_INTEGER_FIELDS:
            if field in row and row[field] is not None:
                _require_exact_int(row[field], f"replication[{index}].{field}")
        for field in FORMAL_REPLICATION_FLAG_FIELDS:
            _require_binary_int(row[field], f"replication[{index}].{field}")
    for index, row in enumerate(summaries):
        _validate_exact_fields(f"summary[{index}]", row, SUMMARY_ROW_FIELDS)
        for field, item in row.items():
            if item is None:
                raise SchemaValidationError(f"summary[{index}].{field} is not nullable")
        if isinstance(row["rho"], bool) or not isinstance(row["rho"], (int, float)):
            raise SchemaValidationError(f"summary[{index}].rho must be numeric")
        if isinstance(row["a3"], bool) or not isinstance(row["a3"], (int, float)):
            raise SchemaValidationError(f"summary[{index}].a3 must be numeric")
        if isinstance(row["eta"], bool) or not isinstance(row["eta"], (int, float)):
            raise SchemaValidationError(f"summary[{index}].eta must be numeric")
        for field in SUMMARY_BOOLEAN_FIELDS:
            _require_bool(row[field], f"summary[{index}].{field}")
    validate_schema("scientific_result", value["result"])
    replication_identities = tuple(
        (
            row["seed"],
            row["rho"],
            row["a3"],
            row["eta"],
            row["method"],
        )
        for row in replications
    )
    if replication_identities != REPLICATION_IDENTITIES:
        raise SchemaValidationError(
            "replication identities must equal the frozen ordered 320-row identity set"
        )
    summary_identities = tuple(
        (row["rho"], row["a3"], row["eta"])
        for row in summaries
    )
    if summary_identities != SUMMARY_IDENTITIES:
        raise SchemaValidationError(
            "summary identities must equal the frozen ordered 8-row identity set"
        )
    _validate_json_value(value, "scientific_payload")
    return value
