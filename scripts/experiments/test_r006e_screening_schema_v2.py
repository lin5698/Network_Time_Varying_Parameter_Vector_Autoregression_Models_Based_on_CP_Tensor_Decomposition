"""Contract tests for the R006e screening v2 schemas."""

from __future__ import annotations

import math
import hashlib
import unittest

from scripts.experiments.r006e_native_experiment import (
    SCREENING_CSV_FIELDS,
    SCREENING_FLAG_FIELDS,
    SCREENING_INTEGER_FIELDS,
)
from scripts.experiments.r006e_native_protocol import (
    METHODS,
    SCREENING_SEEDS,
    keyed_seed,
    primary_cells,
)
from scripts.experiments.r006e_screening_schema_v2 import (
    ALLOWED_DUPLICATE_EXCLUSIONS,
    AUTHORIZATION_ENVELOPE_FIELDS,
    AUTHORIZATION_PAYLOAD_FIELDS,
    DOCUMENT_TYPES,
    DIAGNOSTIC_FIELDS,
    DUPLICATE_COMPARISON_FIELDS,
    ATTEMPT_STATES,
    EVALUATION_CLASSIFICATION,
    FORMAL_REPLICATION_FIELDS,
    FORMAL_REPLICATION_FLAG_FIELDS,
    FORMAL_REPLICATION_INTEGER_FIELDS,
    FORMAL_PEAK_MEMORY_SCOPE,
    MANIFEST_FIELDS,
    NULLABLE_FIELDS,
    PAIR_CLAIM_FIELDS,
    PASS_FAIL_STATES,
    RESOURCE_FIELDS,
    ROLE_START_FIELDS,
    ROW_JOURNAL_FIELDS,
    FAILED_CELL_RECORDS_BY_CLASS,
    RECORD_CARDINALITIES,
    REPLICATION_IDENTITIES,
    REQUIRED_WORKERS,
    SCHEMA_FIELDS,
    SCIENTIFIC_RESULT_FIELDS,
    COMPARABLE_SCIENTIFIC_FIELDS,
    SUMMARY_FIELDS,
    SUMMARY_IDENTITIES,
    SUMMARY_ROW_FIELDS,
    TERMINAL_FIELDS,
    TERMINAL_STATES,
    TRUST_EVIDENCE_FIELDS,
    EXPECTED_ROWS,
    SchemaValidationError,
    V2_CONTROL_ROOT,
    V2_PRIMARY_ROOT,
    V2_REPEAT_ROOT,
    derive_attempt_id,
    validate_comparable_scientific_payload,
    validate_formal_replication_record,
    validate_diagnostic_record,
    validate_resource_record,
    validate_row_journal_record,
    validate_state_transition,
    validate_schema,
)


def make_authorization_payload() -> dict[str, object]:
    return {
        "schema_version": 2,
        "document_type": DOCUMENT_TYPES["authorization_payload"],
        "decision": "AUTHORIZE",
        "phase": "SCREENING",
        "decision_id": "decision-20260718",
        "authorizer_id": "authorizer-1",
        "issued_at": "2026-07-18T12:00:00+08:00",
        "checklist_sha256": "a" * 64,
        "protocol_sha256": "b" * 64,
        "plan_sha256": "c" * 64,
        "runner_contract_sha256": "d" * 64,
        "construction_file_sha256": "e" * 64,
        "construction_canonical_sha256": "f" * 64,
        "provenance_sha256": "1" * 64,
        "config_sha256": "2" * 64,
        "dependency_manifest_sha256": "3" * 64,
        "source_manifest_sha256": "4" * 64,
        "candidate_sha256": "5" * 64,
        "frozen_v1_authority_digest": "6" * 64,
        "primary_root": V2_PRIMARY_ROOT,
        "repeat_root": V2_REPEAT_ROOT,
        "control_root": V2_CONTROL_ROOT,
        "primary_attempt_id": derive_attempt_id("decision-20260718", "primary"),
        "repeat_attempt_id": derive_attempt_id("decision-20260718", "repeat"),
        "workers": REQUIRED_WORKERS,
        "seeds": list(SCREENING_SEEDS),
        "cells": [list(identity) for identity in SUMMARY_IDENTITIES],
        "methods": list(METHODS),
        "output_names": [
            "screening_replications.csv",
            "screening_summary.csv",
            "screening_results.json",
        ],
        "expected_rows": EXPECTED_ROWS,
    }


def make_trust_evidence() -> dict[str, object]:
    return {
        "schema_version": 2,
        "document_type": DOCUMENT_TYPES["trust_evidence"],
        "authorization_artifact_sha256": "7" * 64,
        "signed_payload_sha256": "8" * 64,
        "signature_algorithm": "ed25519",
        "pinned_key_id": "authorizer-key-1",
        "detached_signature": "base64:abc",
        "detached_signature_sha256": "9" * 64,
        "trust_policy_id": "policy-1",
        "external_witness_id": "witness-1",
    }


def make_terminal(*, status: str = "PASS", role: str = "primary") -> dict[str, object]:
    return {
        "schema_version": 2,
        "document_type": DOCUMENT_TYPES["terminal"],
        "decision_id": "decision-20260718",
        "attempt_id": derive_attempt_id("decision-20260718", role),
        "role": role,
        "status": status,
        "pair_claim_sha256": "a" * 64,
        "role_start_sha256": None,
        "replication_sha256": None,
        "summary_sha256": None,
        "result_sha256": None,
        "diagnostics_sha256": None,
        "resources_sha256": None,
        "row_journal_sha256": None,
        "started_at": None,
        "finished_at": "2026-07-18T12:01:00+08:00",
        "exit_code": None,
        "failure_code": None,
        "failure_reason": None,
    }


def make_result(*, status: str = "PASS") -> dict[str, object]:
    return {
        "schema_version": 2,
        "document_type": DOCUMENT_TYPES["scientific_result"],
        "status": status,
        "semantic_replication_sha256": "a" * 64,
        "semantic_summary_sha256": "b" * 64,
        "construction_sha256": "c" * 64,
        "config_sha256": "d" * 64,
        "candidate_sha256": "e" * 64,
        "provenance_sha256": "f" * 64,
        "seed_ids": list(SCREENING_SEEDS),
        "identity_completeness": True,
        "evaluation_classification": EVALUATION_CLASSIFICATION,
    }


def make_replication_row(
    identity: tuple[int, float, float, float, str],
) -> dict[str, object]:
    seed, rho, a3, eta, method = identity
    row = {field: 0 for field in FORMAL_REPLICATION_FIELDS}
    row.update(
        {
            "seed": seed,
            "rho": rho,
            "a3": a3,
            "eta": eta,
            "method": method,
            "fit_sha256": "a" * 64,
            "parameterization": "anchor",
            "peak_memory_scope": FORMAL_PEAK_MEMORY_SCOPE,
            "fit_diagnostics_json": "{}",
            "endpoint_construction_status": "CONSTRUCTION_PASS",
            "endpoint_failure_reasons_json": "[]",
            "w_ref_availability_status": "available",
            "w_alt_interp_availability_status": "available",
            "w_alt_family_availability_status": "available",
            "evaluation_date_start": 164,
            "evaluation_date_end": 199,
            "evaluation_dates": 36,
            "w_ref_evaluation_dates": 36,
            "w_alt_interp_evaluation_dates": 36,
            "w_alt_family_evaluation_dates": 36,
            "selected_hyperparameter": 0.1,
            "failure_code": None,
            "failure_reason": None,
            "family_selected_index": 0,
        }
    )
    for field in SCREENING_FLAG_FIELDS:
        if field in row:
            row[field] = 1
    return row


def make_summary_row(identity: tuple[float, float, float]) -> dict[str, object]:
    rho, a3, eta = identity
    row = {field: True for field in SUMMARY_ROW_FIELDS}
    row.update(
        {
            "rho": rho,
            "a3": a3,
            "eta": eta,
            "passed": True,
            "failed_conditions_json": "[]",
            "audit_values_json": "{}",
        }
    )
    return row


def make_diagnostic_record(
    identity: tuple[int, float, float, float, str],
) -> dict[str, object]:
    seed, rho, a3, eta, method = identity
    return {
        "seed": seed,
        "rho": rho,
        "a3": a3,
        "eta": eta,
        "method": method,
        "method_seed": keyed_seed(seed, rho, a3, eta, "optimizer"),
        "fit_sha256": "a" * 64,
        "fit_success": True,
        "scorable": True,
        "failure_code": None,
        "failure_reason": None,
        "fit_diagnostics_json": "{}",
        "generated_at": "2026-07-18T00:00:00Z",
    }


def make_resource_record(
    identity: tuple[int, float, float, float, str],
    *,
    role: str = "primary",
) -> dict[str, object]:
    seed, rho, a3, eta, method = identity
    return {
        "seed": seed,
        "rho": rho,
        "a3": a3,
        "eta": eta,
        "method": method,
        "worker_pid": 1234,
        "peak_memory_bytes": 4096,
        "peak_memory_scope": FORMAL_PEAK_MEMORY_SCOPE,
        "attempt_id": derive_attempt_id("fixture-decision", role),
        "role": role,
    }


def make_row_journal_record(
    identity: tuple[int, float, float, float, str],
    *,
    role: str = "primary",
) -> dict[str, object]:
    seed, rho, a3, eta, method = identity
    return {
        "seed": seed,
        "rho": rho,
        "a3": a3,
        "eta": eta,
        "method": method,
        "attempt_id": derive_attempt_id("fixture-decision", role),
        "role": role,
        "row_status": "RECORDED",
        "replication_sha256": "a" * 64,
        "diagnostic_sha256": "b" * 64,
        "resource_sha256": "c" * 64,
        "generated_at": "2026-07-18T00:00:00Z",
    }


def make_comparable_payload() -> dict[str, object]:
    return {
        "replication": [make_replication_row(identity) for identity in REPLICATION_IDENTITIES],
        "summary": [make_summary_row(identity) for identity in SUMMARY_IDENTITIES],
        "result": make_result(),
    }


class ScreeningSchemaV2Tests(unittest.TestCase):
    def test_formal_replication_schema_omits_pid_only(self) -> None:
        self.assertEqual(
            FORMAL_REPLICATION_FIELDS,
            tuple(
                field
                for field in SCREENING_CSV_FIELDS
                if field != "peak_memory_worker_pid"
            ),
        )
        self.assertEqual(len(FORMAL_REPLICATION_FIELDS), 85)

    def test_formal_nonbinary_integer_fields_derive_from_frozen_v1(self) -> None:
        self.assertEqual(
            FORMAL_REPLICATION_INTEGER_FIELDS,
            frozenset(SCREENING_INTEGER_FIELDS)
            - {"peak_memory_worker_pid"}
            - FORMAL_REPLICATION_FLAG_FIELDS,
        )
        self.assertTrue({
            "evaluation_dates",
            "w_ref_evaluation_dates",
            "w_alt_interp_evaluation_dates",
            "w_alt_family_evaluation_dates",
        } <= FORMAL_REPLICATION_INTEGER_FIELDS)

    def test_formal_record_validator_rejects_type_null_literal_hash_and_order(self) -> None:
        row = make_replication_row(REPLICATION_IDENTITIES[0])
        self.assertIs(validate_formal_replication_record(row), row)
        for field in FORMAL_REPLICATION_INTEGER_FIELDS:
            if row[field] is None:
                continue
            for bad in (float(row[field]), True):
                mutated = dict(row)
                mutated[field] = bad
                with self.subTest(field=field, bad=bad):
                    with self.assertRaisesRegex(SchemaValidationError, "integer"):
                        validate_formal_replication_record(mutated)
        mutated = dict(row)
        mutated["fit_success"] = True
        with self.assertRaisesRegex(SchemaValidationError, "integer 0 or 1"):
            validate_formal_replication_record(mutated)
        mutated = dict(row)
        mutated["evaluation_dates"] = None
        with self.assertRaisesRegex(SchemaValidationError, "not nullable"):
            validate_formal_replication_record(mutated)
        mutated = dict(row)
        mutated["fit_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(SchemaValidationError, "lowercase SHA-256"):
            validate_formal_replication_record(mutated)
        mutated = dict(row)
        mutated["peak_memory_scope"] = "partial_scope"
        with self.assertRaisesRegex(SchemaValidationError, "peak_memory_scope"):
            validate_formal_replication_record(mutated)
        mutated = dict(reversed(tuple(row.items())))
        with self.assertRaisesRegex(SchemaValidationError, "field order"):
            validate_formal_replication_record(mutated)
        mutated = dict(row)
        mutated["runtime_seconds"] = math.inf
        with self.assertRaisesRegex(SchemaValidationError, "finite"):
            validate_formal_replication_record(mutated)

    def test_diagnostic_validator_rejects_type_null_hash_seed_and_order(self) -> None:
        record = make_diagnostic_record(REPLICATION_IDENTITIES[0])
        self.assertIs(validate_diagnostic_record(record), record)
        for field, bad in (
            ("method_seed", 1.0),
            ("method_seed", True),
            ("fit_success", 1),
            ("scorable", 0),
            ("fit_sha256", "bad-hash"),
            ("method_seed", record["method_seed"] + 1),
        ):
            mutated = dict(record)
            mutated[field] = bad
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(SchemaValidationError):
                    validate_diagnostic_record(mutated)
        mutated = dict(record)
        mutated["method_seed"] = None
        with self.assertRaisesRegex(SchemaValidationError, "not nullable"):
            validate_diagnostic_record(mutated)
        mutated = dict(reversed(tuple(record.items())))
        with self.assertRaisesRegex(SchemaValidationError, "field order"):
            validate_diagnostic_record(mutated)
        mutated = dict(record)
        mutated["fit_diagnostics_json"] = '{"bad":NaN}'
        with self.assertRaisesRegex(SchemaValidationError, "finite JSON"):
            validate_diagnostic_record(mutated)

    def test_diagnostic_scorability_distinguishes_fit_and_evaluation_failure(self) -> None:
        evaluation_failure = make_diagnostic_record(REPLICATION_IDENTITIES[0])
        evaluation_failure.update({
            "fit_success": True,
            "scorable": False,
            "failure_code": "EVALUATION_NUMERICAL_FAIL",
            "failure_reason": "FloatingPointError: fixture",
        })
        self.assertIs(validate_diagnostic_record(evaluation_failure), evaluation_failure)

        fit_failure = dict(evaluation_failure)
        fit_failure["fit_success"] = False
        self.assertIs(validate_diagnostic_record(fit_failure), fit_failure)

        invalid = dict(evaluation_failure)
        invalid.update({"scorable": True, "failure_code": None, "failure_reason": None})
        invalid["fit_success"] = False
        with self.assertRaisesRegex(SchemaValidationError, "fit_success"):
            validate_diagnostic_record(invalid)

        invalid = dict(evaluation_failure)
        invalid.update({"failure_code": None, "failure_reason": None})
        with self.assertRaisesRegex(SchemaValidationError, "failure details"):
            validate_diagnostic_record(invalid)

    def test_resource_validator_rejects_null_type_literal_role_attempt_and_order(self) -> None:
        record = make_resource_record(REPLICATION_IDENTITIES[0])
        self.assertIs(validate_resource_record(record), record)
        for field, bad in (
            ("worker_pid", 1234.0),
            ("worker_pid", True),
            ("worker_pid", 0),
            ("peak_memory_bytes", 4096.0),
            ("peak_memory_bytes", True),
            ("peak_memory_bytes", -1),
            ("peak_memory_scope", "partial"),
            ("role", "replacement"),
            ("attempt_id", "fixture-attempt"),
        ):
            mutated = dict(record)
            mutated[field] = bad
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(SchemaValidationError):
                    validate_resource_record(mutated)
        mutated = dict(record)
        mutated["worker_pid"] = None
        with self.assertRaisesRegex(SchemaValidationError, "not nullable"):
            validate_resource_record(mutated)
        mutated = dict(reversed(tuple(record.items())))
        with self.assertRaisesRegex(SchemaValidationError, "field order"):
            validate_resource_record(mutated)

    def test_row_journal_validator_has_no_schema_version_and_rejects_mutations(self) -> None:
        record = make_row_journal_record(REPLICATION_IDENTITIES[0])
        self.assertNotIn("schema_version", ROW_JOURNAL_FIELDS)
        self.assertNotIn("document_type", ROW_JOURNAL_FIELDS)
        self.assertIs(validate_schema("row_journal", record), record)
        self.assertIs(validate_row_journal_record(record), record)
        for field, bad in (
            ("replication_sha256", "bad-hash"),
            ("diagnostic_sha256", 1),
            ("resource_sha256", "A" * 64),
            ("row_status", "REPLACED"),
            ("role", "replacement"),
            ("attempt_id", "fixture-attempt"),
        ):
            mutated = dict(record)
            mutated[field] = bad
            with self.subTest(field=field, bad=bad):
                with self.assertRaises(SchemaValidationError):
                    validate_row_journal_record(mutated)
        mutated = dict(record)
        mutated["replication_sha256"] = None
        with self.assertRaisesRegex(SchemaValidationError, "not nullable"):
            validate_row_journal_record(mutated)
        mutated = {"schema_version": 2, **record}
        with self.assertRaisesRegex(SchemaValidationError, "key mismatch"):
            validate_row_journal_record(mutated)
        mutated = dict(reversed(tuple(record.items())))
        with self.assertRaisesRegex(SchemaValidationError, "field order"):
            validate_row_journal_record(mutated)

    def test_field_lists_preserve_scientific_and_operational_boundaries(self) -> None:
        gates = (
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
        self.assertEqual(SUMMARY_FIELDS, gates)
        self.assertEqual(
            SUMMARY_ROW_FIELDS,
            ("rho", "a3", "eta", "passed", *gates,
             "failed_conditions_json", "audit_values_json"),
        )
        identity = ("seed", "rho", "a3", "eta", "method")
        self.assertEqual(DIAGNOSTIC_FIELDS[:5], identity)
        self.assertEqual(RESOURCE_FIELDS[:5], identity)
        self.assertEqual(ROW_JOURNAL_FIELDS[:5], identity)
        self.assertEqual(
            ALLOWED_DUPLICATE_EXCLUSIONS,
            frozenset({"runtime_seconds", "peak_memory_bytes", "generated_at"}),
        )

    def test_identity_enumeration_and_cardinalities_are_exact(self) -> None:
        expected_replications = tuple(
            (seed, rho, a3, eta, method)
            for seed in SCREENING_SEEDS
            for rho, a3, eta in primary_cells()
            for method in METHODS
        )
        self.assertEqual(REPLICATION_IDENTITIES, expected_replications)
        self.assertEqual(len(REPLICATION_IDENTITIES), 320)
        self.assertEqual(len(set(REPLICATION_IDENTITIES)), 320)
        self.assertEqual(SUMMARY_IDENTITIES, primary_cells())
        self.assertEqual(len(SUMMARY_IDENTITIES), 8)
        self.assertEqual(
            RECORD_CARDINALITIES,
            {"replication": 320, "diagnostic": 320,
             "resource": 320, "row_journal": 320, "summary": 8},
        )
        self.assertEqual(
            FAILED_CELL_RECORDS_BY_CLASS,
            {"replication": 4, "diagnostic": 4,
             "resource": 4, "row_journal": 4},
        )

    def test_governance_object_key_sets_are_exact_and_immutable(self) -> None:
        expected = {
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
        self.assertEqual(dict(SCHEMA_FIELDS), expected)
        with self.assertRaises(TypeError):
            SCHEMA_FIELDS["extra"] = ("field",)  # type: ignore[index]
        for name, fields in expected.items():
            self.assertEqual(len(fields), len(set(fields)), name)

    def test_strict_validator_rejects_unknown_missing_and_nonfinite_json(self) -> None:
        valid = make_trust_evidence()
        self.assertIs(validate_schema("trust_evidence", valid), valid)
        with self.assertRaisesRegex(SchemaValidationError, "unknown keys"):
            validate_schema("trust_evidence", {**valid, "surprise": 1})
        missing = dict(valid)
        missing.pop(TRUST_EVIDENCE_FIELDS[-1])
        with self.assertRaisesRegex(SchemaValidationError, "missing keys"):
            validate_schema("trust_evidence", missing)
        for bad in (math.nan, math.inf, -math.inf):
            candidate = dict(valid)
            candidate[TRUST_EVIDENCE_FIELDS[0]] = {"nested": [bad]}
            with self.assertRaisesRegex(SchemaValidationError, "non-finite"):
                validate_schema("trust_evidence", candidate)
        candidate = dict(valid)
        candidate[TRUST_EVIDENCE_FIELDS[0]] = {1, 2}
        with self.assertRaisesRegex(SchemaValidationError, "JSON value"):
            validate_schema("trust_evidence", candidate)

    def test_non_string_keys_raise_governed_schema_errors(self) -> None:
        trust = {**make_trust_evidence(), 1: "bad", "unexpected": "bad"}
        with self.assertRaisesRegex(SchemaValidationError, "non-string JSON key"):
            validate_schema("trust_evidence", trust)

        payload = make_comparable_payload()
        contaminated_row = {
            **payload["replication"][0],
            1: "bad",
            "unexpected": "bad",
        }
        with self.assertRaisesRegex(SchemaValidationError, "non-string JSON key"):
            validate_comparable_scientific_payload(
                {**payload, "replication": [contaminated_row, *payload["replication"][1:]]}
            )

    def test_schema_semantics_require_exact_literals_and_ints(self) -> None:
        payload = make_authorization_payload()
        self.assertIs(validate_schema("authorization_payload", payload), payload)
        with self.assertRaisesRegex(SchemaValidationError, "schema_version"):
            validate_schema("authorization_payload", {**payload, "schema_version": True})
        with self.assertRaisesRegex(SchemaValidationError, "document_type"):
            validate_schema(
                "authorization_payload",
                {**payload, "document_type": "authorization_payload"},
            )
        with self.assertRaisesRegex(SchemaValidationError, "decision"):
            validate_schema("authorization_payload", {**payload, "decision": "DENY"})
        with self.assertRaisesRegex(SchemaValidationError, "phase"):
            validate_schema(
                "authorization_payload",
                {**payload, "phase": "CONFIRMATION"},
            )
        with self.assertRaisesRegex(SchemaValidationError, "workers"):
            validate_schema("authorization_payload", {**payload, "workers": True})
        with self.assertRaisesRegex(SchemaValidationError, "expected_rows"):
            validate_schema(
                "authorization_payload",
                {**payload, "expected_rows": EXPECTED_ROWS - 1},
            )
        with self.assertRaisesRegex(SchemaValidationError, "primary_root"):
            validate_schema(
                "authorization_payload",
                {**payload, "primary_root": "output/high_impact_revision/r006e_native_supported_recovery"},
            )

        terminal = make_terminal()
        self.assertIs(validate_schema("terminal", terminal), terminal)
        with self.assertRaisesRegex(SchemaValidationError, "status"):
            validate_schema("terminal", {**terminal, "status": "RESUMED"})
        with self.assertRaisesRegex(SchemaValidationError, "role"):
            validate_schema("terminal", {**terminal, "role": "replacement"})

        result = make_result()
        self.assertIs(validate_schema("scientific_result", result), result)
        with self.assertRaisesRegex(SchemaValidationError, "seed_ids"):
            validate_schema(
                "scientific_result",
                {**result, "seed_ids": list(reversed(SCREENING_SEEDS))},
            )
        with self.assertRaisesRegex(SchemaValidationError, "identity_completeness"):
            validate_schema(
                "scientific_result",
                {**result, "identity_completeness": 1},
            )
        with self.assertRaisesRegex(SchemaValidationError, "evaluation_classification"):
            validate_schema(
                "scientific_result",
                {**result, "evaluation_classification": "production"},
            )

    def test_attempt_identity_roots_and_terminal_transitions_are_frozen(self) -> None:
        decision_id = "decision-20260718"
        for role in ("primary", "repeat"):
            material = (
                f"R006E_SCREENING_V2_ATTEMPT\0{decision_id}\0{role}"
            ).encode("utf-8")
            expected = "r006e-v2-" + hashlib.sha256(material).hexdigest()
            self.assertEqual(derive_attempt_id(decision_id, role), expected)
        with self.assertRaisesRegex(ValueError, "role"):
            derive_attempt_id(decision_id, "replacement")
        self.assertEqual(
            (V2_PRIMARY_ROOT, V2_REPEAT_ROOT, V2_CONTROL_ROOT),
            (
                "output/high_impact_revision/r006e_native_supported_recovery_v2",
                "output/high_impact_revision/r006e_native_supported_recovery_v2_repeat",
                "output/high_impact_revision/r006e_native_supported_recovery_v2_control",
            ),
        )
        self.assertEqual(TERMINAL_STATES, frozenset({"PASS", "FAIL", "INCOMPLETE"}))
        self.assertEqual(
            ATTEMPT_STATES,
            frozenset({"CLAIMED", "STARTED", "PASS", "FAIL", "INCOMPLETE"}),
        )
        for target in TERMINAL_STATES:
            self.assertEqual(validate_state_transition("STARTED", target), target)
        self.assertEqual(validate_state_transition("CLAIMED", "STARTED"), "STARTED")
        self.assertEqual(validate_state_transition("CLAIMED", "INCOMPLETE"), "INCOMPLETE")
        for terminal in TERMINAL_STATES:
            with self.assertRaisesRegex(SchemaValidationError, "illegal transition"):
                validate_state_transition(terminal, "STARTED")

    def test_comparable_payload_contains_only_three_scientific_objects(self) -> None:
        payload = make_comparable_payload()
        self.assertEqual(
            COMPARABLE_SCIENTIFIC_FIELDS,
            ("replication", "summary", "result"),
        )
        self.assertIs(validate_comparable_scientific_payload(payload), payload)
        with self.assertRaisesRegex(SchemaValidationError, "unknown keys"):
            validate_comparable_scientific_payload({**payload, "diagnostics": []})
        contaminated = {**payload["replication"][0], "attempt_id": "operational"}
        with self.assertRaisesRegex(SchemaValidationError, "operational field"):
            validate_comparable_scientific_payload(
                {**payload, "replication": [contaminated]}
            )
        contaminated_result = dict(payload["result"])
        contaminated_result["role"] = "primary"
        with self.assertRaisesRegex(SchemaValidationError, "operational field"):
            validate_comparable_scientific_payload(
                {**payload, "result": contaminated_result}
            )

    def test_comparable_payload_requires_exact_cardinality_identity_and_scalar_rules(
        self,
    ) -> None:
        payload = make_comparable_payload()
        self.assertIs(validate_comparable_scientific_payload(payload), payload)

        with self.assertRaisesRegex(SchemaValidationError, "replication cardinality"):
            validate_comparable_scientific_payload(
                {**payload, "replication": payload["replication"][:-1]}
            )
        with self.assertRaisesRegex(SchemaValidationError, "summary cardinality"):
            validate_comparable_scientific_payload(
                {**payload, "summary": payload["summary"][:-1]}
            )

        reordered = list(payload["replication"])
        reordered[0], reordered[1] = reordered[1], reordered[0]
        with self.assertRaisesRegex(SchemaValidationError, "replication identities"):
            validate_comparable_scientific_payload({**payload, "replication": reordered})

        drifted = [dict(row) for row in payload["summary"]]
        drifted[0]["eta"] = 0.3
        with self.assertRaisesRegex(SchemaValidationError, "summary identities"):
            validate_comparable_scientific_payload({**payload, "summary": drifted})

        bool_seed = [dict(row) for row in payload["replication"]]
        bool_seed[0]["seed"] = True
        with self.assertRaisesRegex(SchemaValidationError, "replication\\[0\\]\\.seed"):
            validate_comparable_scientific_payload({**payload, "replication": bool_seed})

        for invalid_flag in (True, False, -1, 2):
            with self.subTest(invalid_flag=invalid_flag):
                drifted_flags = [dict(row) for row in payload["replication"]]
                drifted_flags[0]["fit_success"] = invalid_flag
                with self.assertRaisesRegex(
                    SchemaValidationError,
                    "replication\\[0\\]\\.fit_success",
                ):
                    validate_comparable_scientific_payload(
                        {**payload, "replication": drifted_flags}
                    )

        int_passed = [dict(row) for row in payload["summary"]]
        int_passed[0]["passed"] = 1
        with self.assertRaisesRegex(SchemaValidationError, "summary\\[0\\]\\.passed"):
            validate_comparable_scientific_payload({**payload, "summary": int_passed})

    def test_nullability_is_explicit_and_fail_closed(self) -> None:
        self.assertEqual(NULLABLE_FIELDS["trust_evidence"], frozenset())
        self.assertEqual(
            NULLABLE_FIELDS["terminal"],
            frozenset({
                "role_start_sha256", "replication_sha256", "summary_sha256",
                "result_sha256", "diagnostics_sha256", "resources_sha256",
                "row_journal_sha256", "started_at", "exit_code",
                "failure_code", "failure_reason",
            }),
        )
        with self.assertRaises(TypeError):
            NULLABLE_FIELDS["trust_evidence"] = frozenset({"extra"})  # type: ignore[index]
        trust = make_trust_evidence()
        self.assertIs(validate_schema("trust_evidence", trust), trust)
        trust["external_witness_id"] = None
        with self.assertRaisesRegex(SchemaValidationError, "not nullable"):
            validate_schema("trust_evidence", trust)
        terminal = make_terminal()
        terminal["failure_reason"] = None
        self.assertIs(validate_schema("terminal", terminal), terminal)


if __name__ == "__main__":
    unittest.main()
