"""Fixture-only tests for R006e v2 scientific duplicate semantics."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.experiments.r006e_native_experiment import SCREENING_FLAG_FIELDS
from scripts.experiments.r006e_screening_schema_v2 import (
    DOCUMENT_TYPES,
    DUPLICATE_COMPARISON_FIELDS,
    EVALUATION_CLASSIFICATION,
    FORMAL_REPLICATION_FIELDS,
    REPLICATION_IDENTITIES,
    SCREENING_SEEDS,
    SUMMARY_IDENTITIES,
    SUMMARY_ROW_FIELDS,
)
from scripts.experiments.r006e_duplicate_audit_v2 import (
    DuplicateIntegrityError,
    compare_scientific_attempts,
    raw_byte_sha256,
    recompute_scientific_digests,
    semantic_digest,
)


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
            "parameterization": "native",
            "peak_memory_scope": "worker",
            "fit_diagnostics_json": (
                '{"generated_at":"fixture-a","nested":'
                '{"peak_memory_bytes":10,"runtime_seconds":1.0},'
                '"runtime_seconds_total":7}'
            ),
            "endpoint_construction_status": "supported",
            "endpoint_failure_reasons_json": "[]",
            "w_ref_availability_status": "available",
            "w_alt_interp_availability_status": "available",
            "w_alt_family_availability_status": "available",
            "evaluation_date_start": 80,
            "evaluation_date_end": 199,
            "evaluation_dates": 36,
            "w_ref_evaluation_dates": 36,
            "w_alt_interp_evaluation_dates": 36,
            "w_alt_family_evaluation_dates": 36,
            "selected_hyperparameter": "penalty=0.1",
            "failure_code": None,
            "failure_reason": None,
            "family_selected_index": None,
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


def make_result() -> dict[str, object]:
    return {
        "schema_version": 2,
        "document_type": DOCUMENT_TYPES["scientific_result"],
        "status": "PASS",
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


def make_scientific_payload() -> dict[str, object]:
    payload = {
        "replication": [
            make_replication_row(identity) for identity in REPLICATION_IDENTITIES
        ],
        "summary": [make_summary_row(identity) for identity in SUMMARY_IDENTITIES],
        "result": make_result(),
    }
    refresh_result_digests(payload)
    return payload


def refresh_result_digests(payload: dict[str, object]) -> None:
    digests = recompute_scientific_digests(payload)
    payload["result"]["semantic_replication_sha256"] = digests["replication"]
    payload["result"]["semantic_summary_sha256"] = digests["summary"]


class DuplicateAuditV2Tests(unittest.TestCase):
    def test_semantic_digest_excludes_exact_runtime_fields_recursively(self) -> None:
        primary = make_scientific_payload()
        repeat = copy.deepcopy(primary)
        repeat["replication"][0]["runtime_seconds"] = 99.0
        repeat["replication"][0]["peak_memory_bytes"] = 999
        repeat["replication"][0]["fit_diagnostics_json"] = (
            '{"runtime_seconds_total":7,"nested":'
            '{"runtime_seconds":99.0,"peak_memory_bytes":999},'
            '"generated_at":"fixture-b"}'
        )
        self.assertEqual(semantic_digest(primary), semantic_digest(repeat))

    def test_raw_hashes_may_differ_while_semantic_digests_match(self) -> None:
        primary = make_scientific_payload()
        repeat = copy.deepcopy(primary)
        repeat["replication"][0]["runtime_seconds"] = 123.0
        primary_bytes = json.dumps(primary, sort_keys=True).encode("utf-8")
        repeat_bytes = json.dumps(repeat, sort_keys=True).encode("utf-8")
        self.assertNotEqual(
            raw_byte_sha256(primary_bytes), raw_byte_sha256(repeat_bytes)
        )
        self.assertEqual(semantic_digest(primary), semantic_digest(repeat))

    def test_comparison_passes_only_the_three_scientific_payloads(self) -> None:
        primary = make_scientific_payload()
        repeat = copy.deepcopy(primary)
        repeat["replication"][0]["runtime_seconds"] = 123.0
        comparison = compare_scientific_attempts(primary, repeat)
        self.assertEqual(tuple(comparison), DUPLICATE_COMPARISON_FIELDS)
        self.assertEqual(comparison["status"], "PASS")
        self.assertEqual(
            comparison["compared_payloads"],
            ["replication", "summary", "result"],
        )
        self.assertEqual(comparison["mismatch_paths"], [])

    def test_identical_stale_result_digest_claims_are_rejected(self) -> None:
        primary = make_scientific_payload()
        repeat = copy.deepcopy(primary)
        primary["result"]["semantic_replication_sha256"] = "9" * 64
        repeat["result"]["semantic_replication_sha256"] = "9" * 64
        with self.assertRaisesRegex(DuplicateIntegrityError, "semantic_replication_sha256"):
            compare_scientific_attempts(primary, repeat)

    def test_fit_diagnostics_json_is_strict_and_operationally_clean(self) -> None:
        cases = {
            "malformed": "{",
            "duplicate": '{"converged":true,"converged":false}',
            "named_nonfinite": '{"objective":NaN}',
            "overflow_nonfinite": '{"objective":1e999}',
            "operational": '{"peak_memory_worker_pid":123}',
            "null_top_level": "null",
            "array_top_level": "[]",
            "number_top_level": "42",
            "boolean_top_level": "true",
            "string_top_level": '"diagnostic text"',
        }
        for label, diagnostic_json in cases.items():
            with self.subTest(label=label):
                payload = make_scientific_payload()
                payload["replication"][0]["fit_diagnostics_json"] = diagnostic_json
                with self.assertRaises(DuplicateIntegrityError):
                    semantic_digest(payload)

    def test_every_nonexcluded_scientific_category_fails_with_stable_paths(self) -> None:
        cases = {
            "metric": (
                lambda payload: payload["replication"][0].__setitem__(
                    "w_ref_operator_relative_error_mean", 0.25
                ),
                "replication[0].w_ref_operator_relative_error_mean",
            ),
            "failure": (
                lambda payload: payload["replication"][0].__setitem__(
                    "failure_code", "FIT_ERROR"
                ),
                "replication[0].failure_code",
            ),
            "support": (
                lambda payload: payload["replication"][0].__setitem__(
                    "endpoint_construction_status", "unsupported"
                ),
                "replication[0].endpoint_construction_status",
            ),
            "convergence": (
                lambda payload: payload["replication"][0].__setitem__(
                    "at_least_one_converged_start", 0
                ),
                "replication[0].at_least_one_converged_start",
            ),
            "hyperparameter": (
                lambda payload: payload["replication"][0].__setitem__(
                    "selected_hyperparameter", "penalty=0.2"
                ),
                "replication[0].selected_hyperparameter",
            ),
            "status": (
                lambda payload: payload["result"].__setitem__("status", "FAIL"),
                "result.status",
            ),
            "exclusion_substring": (
                lambda payload: payload["replication"][0].__setitem__(
                    "fit_diagnostics_json",
                    '{"runtime_seconds_total":8,"nested":{}}',
                ),
                "replication[0].fit_diagnostics_json",
            ),
        }
        for label, (mutate, expected_path) in cases.items():
            with self.subTest(label=label):
                primary = make_scientific_payload()
                repeat = copy.deepcopy(primary)
                mutate(repeat)
                refresh_result_digests(repeat)
                comparison = compare_scientific_attempts(primary, repeat)
                self.assertEqual(comparison["status"], "FAIL")
                expected_paths = [expected_path]
                if expected_path.startswith("replication"):
                    expected_paths.append("result.semantic_replication_sha256")
                self.assertEqual(comparison["mismatch_paths"], expected_paths)

    def test_changed_semantic_digest_claim_is_rejected(self) -> None:
        primary = make_scientific_payload()
        repeat = copy.deepcopy(primary)
        repeat["result"]["semantic_replication_sha256"] = "9" * 64
        with self.assertRaisesRegex(DuplicateIntegrityError, "semantic_replication_sha256"):
            compare_scientific_attempts(primary, repeat)

    def test_signed_zero_difference_has_path_and_fails_comparison(self) -> None:
        primary = make_scientific_payload()
        primary["replication"][0]["w_ref_operator_relative_error_mean"] = 0.0
        refresh_result_digests(primary)
        repeat = copy.deepcopy(primary)
        repeat["replication"][0]["w_ref_operator_relative_error_mean"] = -0.0
        refresh_result_digests(repeat)

        comparison = compare_scientific_attempts(primary, repeat)
        self.assertEqual(comparison["status"], "FAIL")
        self.assertEqual(
            comparison["mismatch_paths"],
            [
                "replication[0].w_ref_operator_relative_error_mean",
                "result.semantic_replication_sha256",
            ],
        )
        self.assertNotEqual(
            comparison["primary_replication_sha256"],
            comparison["repeat_replication_sha256"],
        )

    def test_identity_cardinality_and_diagnostics_inputs_are_rejected(self) -> None:
        primary = make_scientific_payload()
        bad_identity = copy.deepcopy(primary)
        bad_identity["replication"][0]["seed"] = -1
        with self.assertRaisesRegex(DuplicateIntegrityError, "identity set"):
            compare_scientific_attempts(primary, bad_identity)

        missing_row = copy.deepcopy(primary)
        missing_row["replication"].pop()
        with self.assertRaisesRegex(DuplicateIntegrityError, "cardinality"):
            compare_scientific_attempts(primary, missing_row)

        diagnostics_input = copy.deepcopy(primary)
        diagnostics_input["diagnostics"] = []
        with self.assertRaisesRegex(DuplicateIntegrityError, "unknown keys"):
            compare_scientific_attempts(primary, diagnostics_input)

    def test_non_string_keys_translate_to_duplicate_integrity_error(self) -> None:
        primary = make_scientific_payload()
        contaminated = copy.deepcopy(primary)
        contaminated["replication"][0][1] = "bad"
        contaminated["replication"][0]["unexpected"] = "bad"
        with self.assertRaisesRegex(DuplicateIntegrityError, "non-string JSON key"):
            compare_scientific_attempts(primary, contaminated)


if __name__ == "__main__":
    unittest.main()
