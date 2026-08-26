"""Hand-calculated tests for the frozen R006e result gates."""

from __future__ import annotations

import math
import json
import unittest

from scripts.experiments.r006e_native_gates import (
    confirmation_contrasts,
    confirmation_sign_inference,
    exact_binomial_upper_tail,
    evaluate_confirmation_gate,
    evaluate_screening_gate,
    holm_adjust,
    paired_seed_bootstrap,
)
from scripts.experiments.r006e_native_protocol import (
    CONFIRMATION_SEEDS,
    METHODS,
    SCREENING_SEEDS,
    R006EConfig,
    primary_cells,
)


ENDPOINTS = ("w_alt_interp", "w_alt_family")
CANDIDATE = "dw_joint_tucker333"
COMPARATORS = tuple(method for method in METHODS if method != CANDIDATE)


def passing_screening_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in SCREENING_SEEDS:
        for rho, a3, eta in primary_cells():
            for method in METHODS:
                candidate = method == CANDIDATE
                row: dict[str, object] = {
                    "seed": seed,
                    "rho": rho,
                    "a3": a3,
                    "eta": eta,
                    "method": method,
                    "peak_memory_bytes": 1024,
                    "runtime_seconds": 0.25,
                    "scorable": 1,
                    "at_least_one_converged_start": 1,
                    "selected_objective_trace_nonincreasing": 1,
                    "observed_topology_prediction_rmse": 1.0 if candidate else 1.1,
                    "w_ref_raw_response_error_mean": 1.0 if candidate else 1.1,
                }
                for endpoint in ENDPOINTS:
                    row[f"{endpoint}_available"] = 1
                    row[f"{endpoint}_raw_response_error_mean"] = (
                        0.8 if candidate else 1.0
                    )
                    row[f"{endpoint}_operator_relative_error_mean"] = 0.5
                    row[f"{endpoint}_response_zero_ratio_mean"] = 0.5
                rows.append(row)
    return rows


def confirmation_rows(ratio: float = 1.20) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in CONFIRMATION_SEEDS:
        for rho, a3, eta in primary_cells():
            for method in METHODS:
                row: dict[str, object] = {
                    "seed": seed,
                    "rho": rho,
                    "a3": a3,
                    "eta": eta,
                    "method": method,
                    "peak_memory_bytes": 1024,
                    "runtime_seconds": 0.25,
                    "scorable": 1,
                    "at_least_one_converged_start": 1,
                    "selected_objective_trace_nonincreasing": 1,
                }
                for endpoint in ENDPOINTS:
                    row[f"{endpoint}_available"] = 1
                    row[f"{endpoint}_raw_response_error_mean"] = (
                        1.0 if method == CANDIDATE else ratio
                    )
                rows.append(row)
    return rows


class R006ENativeGatesTest(unittest.TestCase):
    @staticmethod
    def _target_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        return [
            row
            for row in rows
            if (row["rho"], row["a3"], row["eta"]) == (0.80, 0.10, 0.15)
        ]

    def _failed_conditions(self, rows: list[dict[str, object]]) -> list[str]:
        result = evaluate_screening_gate(rows, config=R006EConfig())
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["passed_cells"], 7)
        return next(
            cell["failed_conditions"] for cell in result["cells"] if not cell["passed"]
        )

    def test_all_eight_hand_constructed_screening_cells_pass(self) -> None:
        result = evaluate_screening_gate(
            passing_screening_rows(), config=R006EConfig()
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["passed_cells"], 8)

    def test_operator_equality_fails_one_cell_and_names_condition(self) -> None:
        rows = passing_screening_rows()
        target = (0.95, 0.25, 0.45)
        for row in rows:
            if (
                (row["rho"], row["a3"], row["eta"]) == target
                and row["method"] == CANDIDATE
            ):
                row["w_alt_family_operator_relative_error_mean"] = 1.0

        result = evaluate_screening_gate(rows, config=R006EConfig())

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["passed_cells"], 7)
        failed = next(cell for cell in result["cells"] if not cell["passed"])
        self.assertEqual(failed["failed_conditions"], ["operator_relative_error"])

    def test_duplicate_identity_is_a_fail_closed_verdict(self) -> None:
        rows = passing_screening_rows()
        rows.append(dict(rows[0]))

        result = evaluate_screening_gate(rows, config=R006EConfig())

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_code"], "DUPLICATE_ROW_IDENTITY")

    def test_missing_identity_is_not_dropped_or_imputed(self) -> None:
        result = evaluate_screening_gate(
            passing_screening_rows()[:-1], config=R006EConfig()
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_code"], "MISSING_ROW_IDENTITY")

    def test_malformed_identity_is_a_fail_closed_verdict(self) -> None:
        rows = passing_screening_rows()
        rows[0]["rho"] = "not-a-coordinate"

        result = evaluate_screening_gate(rows, config=R006EConfig())

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failure_code"], "INVALID_ROW_IDENTITY")

    def test_identity_rejects_coercible_seed_coordinate_and_method_types(self) -> None:
        mutations = (
            ("float seed", "seed", 240100.0),
            ("string seed", "seed", "240100"),
            ("boolean seed", "seed", True),
            ("string rho", "rho", "0.8"),
            ("boolean a3", "a3", False),
            ("nonfinite eta", "eta", float("inf")),
            ("non-string method", "method", 1),
        )
        for label, key, value in mutations:
            with self.subTest(label=label):
                rows = passing_screening_rows()
                rows[0][key] = value
                result = evaluate_screening_gate(rows, config=R006EConfig())
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["failure_code"], "INVALID_ROW_IDENTITY")

    def test_screening_refuses_confirmation_seed_namespace(self) -> None:
        with self.assertRaisesRegex(ValueError, "screening seed set"):
            evaluate_screening_gate(confirmation_rows(), config=R006EConfig())

    def test_unavailable_endpoint_is_checked_before_missing_metrics(self) -> None:
        rows = passing_screening_rows()
        row = rows[0]
        row["w_alt_interp_available"] = 0
        row["w_alt_interp_raw_response_error_mean"] = None
        row["w_alt_interp_operator_relative_error_mean"] = None
        row["w_alt_interp_response_zero_ratio_mean"] = None

        result = evaluate_screening_gate(rows, config=R006EConfig())

        self.assertEqual(result["status"], "FAIL")
        failed = result["cells"][0]
        self.assertIn("availability", failed["failed_conditions"])
        self.assertIn("finite_and_converged", failed["failed_conditions"])

    def test_confirmation_contrast_uses_worst_cell_and_endpoint(self) -> None:
        rows = confirmation_rows()
        for row in rows:
            if (
                row["seed"] == 250100
                and (row["rho"], row["a3"], row["eta"])
                == (0.80, 0.10, 0.15)
                and row["method"] == "anchor_local"
            ):
                row["w_alt_family_raw_response_error_mean"] = 1.05

        contrasts = confirmation_contrasts(rows)

        self.assertAlmostEqual(contrasts["anchor_local"][250100], math.log(1.05))

    def test_confirmation_contrasts_reject_duplicate_and_nonfinite_rows(self) -> None:
        rows = confirmation_rows()
        with self.assertRaisesRegex(ValueError, "duplicate confirmation"):
            confirmation_contrasts(rows + [dict(rows[0])])
        rows[0]["w_alt_interp_raw_response_error_mean"] = float("inf")
        with self.assertRaisesRegex(ValueError, "losses must be finite"):
            confirmation_contrasts(rows)

    def test_confirmation_requires_complete_scorable_nonnegative_rows(self) -> None:
        mutations = (
            ("unavailable", lambda row: row.__setitem__("w_alt_interp_available", 0)),
            ("boolean flag", lambda row: row.__setitem__("scorable", True)),
            ("nonscorable", lambda row: row.__setitem__("scorable", 0)),
            ("missing memory", lambda row: row.pop("peak_memory_bytes")),
            ("negative memory", lambda row: row.__setitem__("peak_memory_bytes", -1)),
            (
                "negative loss",
                lambda row: row.__setitem__(
                    "w_alt_family_raw_response_error_mean", -0.01
                ),
            ),
            ("float seed", lambda row: row.__setitem__("seed", 250100.0)),
            ("string coordinate", lambda row: row.__setitem__("rho", "0.8")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                rows = confirmation_rows()
                mutate(rows[0])
                with self.assertRaises(ValueError):
                    confirmation_contrasts(rows)

        with self.assertRaisesRegex(ValueError, "missing confirmation"):
            confirmation_contrasts(confirmation_rows()[:-1])

    def test_exact_binomial_tail_and_holm_ties_follow_frozen_formulas(self) -> None:
        self.assertEqual(exact_binomial_upper_tail(30), 1 / 2**30)
        self.assertEqual(exact_binomial_upper_tail(29), 31 / 2**30)
        raw = {
            "anchor_local": 0.01,
            "anchor_fused_tv": 0.01,
            "anchor_split_tucker333": 0.04,
        }

        result = holm_adjust(raw)

        self.assertEqual(
            result["order"],
            ["anchor_local", "anchor_fused_tv", "anchor_split_tucker333"],
        )
        self.assertEqual(
            result["adjusted_p_values"],
            {
                "anchor_local": 0.03,
                "anchor_fused_tv": 0.03,
                "anchor_split_tucker333": 0.04,
            },
        )
        self.assertEqual(result["rejected"], dict.fromkeys(COMPARATORS, True))

    def test_even_seed_median_averages_the_two_central_values(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["method"] == CANDIDATE:
                row["w_alt_interp_operator_relative_error_mean"] = (
                    0.9 if row["seed"] in SCREENING_SEEDS[:5] else 1.1
                )

        self.assertIn("operator_relative_error", self._failed_conditions(rows))

    def test_holm_stops_after_first_nonrejection(self) -> None:
        result = holm_adjust(
            {
                "anchor_local": 0.01,
                "anchor_fused_tv": 0.03,
                "anchor_split_tucker333": 0.04,
            }
        )

        self.assertEqual(
            result["rejected"],
            {
                "anchor_local": True,
                "anchor_fused_tv": False,
                "anchor_split_tucker333": False,
            },
        )

    def test_holm_rejects_nonfinite_and_out_of_range_p_values(self) -> None:
        for invalid in (float("nan"), float("inf"), -0.01, 1.01, True):
            with self.subTest(invalid=invalid):
                raw = dict.fromkeys(COMPARATORS, 0.01)
                raw["anchor_local"] = invalid
                with self.assertRaises(ValueError):
                    holm_adjust(raw)

    def test_confirmation_checks_seed_namespace_before_refusing_authority(self) -> None:
        with self.assertRaisesRegex(ValueError, "confirmation seed set"):
            evaluate_confirmation_gate(
                passing_screening_rows(), config=R006EConfig()
            )

    def test_confirmation_refuses_before_any_gating_verdict(self) -> None:
        with self.assertRaisesRegex(
            RuntimeError,
            "CONFIRMATION_NOT_AUTHORIZED.*median-bound specification",
        ):
            evaluate_confirmation_gate(confirmation_rows(), config=R006EConfig())

    def test_confirmation_validates_rows_before_authorization_refusal(self) -> None:
        rows = confirmation_rows()
        rows[0]["w_alt_interp_raw_response_error_mean"] = -1.0

        with self.assertRaisesRegex(ValueError, "finite and nonnegative"):
            evaluate_confirmation_gate(rows, config=R006EConfig())

    def test_confirmation_sign_success_is_strictly_above_log_1_10(self) -> None:
        q = math.log(1.10)
        contrasts = {
            comparator: {
                seed: q if seed == CONFIRMATION_SEEDS[0] else q + 0.01
                for seed in CONFIRMATION_SEEDS
            }
            for comparator in COMPARATORS
        }

        result = confirmation_sign_inference(contrasts)

        self.assertEqual(result["threshold"], q)
        self.assertEqual(result["success_counts"], dict.fromkeys(COMPARATORS, 29))
        self.assertEqual(
            result["raw_p_values"], dict.fromkeys(COMPARATORS, 31 / 2**30)
        )

    def test_paired_seed_bootstrap_is_deterministic_shared_and_non_gating(self) -> None:
        base = {
            seed: float(position - 15)
            for position, seed in enumerate(CONFIRMATION_SEEDS)
        }
        contrasts = {
            "anchor_local": base,
            "anchor_fused_tv": {seed: -value for seed, value in base.items()},
            "anchor_split_tucker333": {
                seed: 2.0 * value for seed, value in base.items()
            },
        }

        first = paired_seed_bootstrap(contrasts)
        second = paired_seed_bootstrap(contrasts)

        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )
        self.assertEqual(first["audit_seed"], 260901)
        self.assertEqual(first["replicates"], 10000)
        self.assertIs(first["gating"], False)
        local = first["intervals"]["anchor_local"]
        fused = first["intervals"]["anchor_fused_tv"]
        split = first["intervals"]["anchor_split_tucker333"]
        self.assertAlmostEqual(fused["lower"], -local["upper"])
        self.assertAlmostEqual(fused["upper"], -local["lower"])
        self.assertAlmostEqual(split["lower"], 2.0 * local["lower"])
        self.assertAlmostEqual(split["upper"], 2.0 * local["upper"])

        with self.assertRaisesRegex(RuntimeError, "CONFIRMATION_NOT_AUTHORIZED"):
            evaluate_confirmation_gate(confirmation_rows(), config=R006EConfig())

    def test_gate_2_nonfinite_or_candidate_trace_failure_is_retained(self) -> None:
        rows = passing_screening_rows()
        target = self._target_rows(rows)
        target[0]["observed_topology_prediction_rmse"] = float("nan")
        next(row for row in target if row["method"] == CANDIDATE)[
            "selected_objective_trace_nonincreasing"
        ] = 0

        failed = self._failed_conditions(rows)

        self.assertIn("finite_and_converged", failed)

    def test_gate_2_rejects_nonfinite_non_gating_scientific_metric(self) -> None:
        rows = passing_screening_rows()
        self._target_rows(rows)[0]["m_ref_relative_error_mean"] = float("inf")

        failed = self._failed_conditions(rows)

        self.assertIn("finite_and_converged", failed)

    def test_gate_2_requires_native_nonnegative_memory_and_valid_runtime(self) -> None:
        mutations = (
            ("missing memory", lambda row: row.pop("peak_memory_bytes")),
            ("boolean memory", lambda row: row.__setitem__("peak_memory_bytes", True)),
            ("float memory", lambda row: row.__setitem__("peak_memory_bytes", 1.0)),
            ("negative memory", lambda row: row.__setitem__("peak_memory_bytes", -1)),
            ("negative runtime", lambda row: row.__setitem__("runtime_seconds", -0.1)),
            ("infinite runtime", lambda row: row.__setitem__("runtime_seconds", float("inf"))),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                rows = passing_screening_rows()
                mutate(self._target_rows(rows)[0])
                self.assertIn("finite_and_converged", self._failed_conditions(rows))

    def test_flags_reject_boolean_cross_type_values(self) -> None:
        flag_keys = (
            "scorable",
            "w_alt_interp_available",
            "w_alt_family_available",
            "at_least_one_converged_start",
            "selected_objective_trace_nonincreasing",
        )
        for key in flag_keys:
            with self.subTest(key=key):
                rows = passing_screening_rows()
                target = next(
                    row
                    for row in self._target_rows(rows)
                    if row["method"] == CANDIDATE
                )
                target[key] = True
                result = evaluate_screening_gate(rows, config=R006EConfig())
                self.assertEqual(result["status"], "FAIL")

    def test_gate_2_scorable_zero_fails_in_isolation(self) -> None:
        rows = passing_screening_rows()
        self._target_rows(rows)[0]["scorable"] = 0
        self.assertIn("finite_and_converged", self._failed_conditions(rows))

    def test_gate_2_candidate_convergence_zero_fails_in_isolation(self) -> None:
        rows = passing_screening_rows()
        next(row for row in self._target_rows(rows) if row["method"] == CANDIDATE)[
            "at_least_one_converged_start"
        ] = 0
        self.assertIn("finite_and_converged", self._failed_conditions(rows))

    def test_gate_2_candidate_trace_zero_fails_in_isolation(self) -> None:
        rows = passing_screening_rows()
        next(row for row in self._target_rows(rows) if row["method"] == CANDIDATE)[
            "selected_objective_trace_nonincreasing"
        ] = 0
        self.assertIn("finite_and_converged", self._failed_conditions(rows))

    def test_gate_2_nonfinite_value_fails_in_isolation(self) -> None:
        rows = passing_screening_rows()
        self._target_rows(rows)[0]["m_ref_relative_error_mean"] = float("nan")
        self.assertIn("finite_and_converged", self._failed_conditions(rows))

    def test_negative_loss_or_scientific_metric_fails_instead_of_flooring(self) -> None:
        for key in (
            "w_alt_interp_raw_response_error_mean",
            "m_ref_relative_error_mean",
        ):
            with self.subTest(key=key):
                rows = passing_screening_rows()
                target = next(
                    row
                    for row in self._target_rows(rows)
                    if row["method"] == CANDIDATE
                )
                target[key] = -0.01
                self.assertIn("finite_and_converged", self._failed_conditions(rows))

    def test_gate_4_response_zero_equality_is_not_below_one(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["method"] == CANDIDATE:
                row["w_alt_interp_response_zero_ratio_mean"] = 1.0

        self.assertIn("response_zero_ratio", self._failed_conditions(rows))

    def test_gate_5_paired_endpoint_median_below_ten_percent_fails(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["method"] == "anchor_local":
                row["w_alt_interp_raw_response_error_mean"] = 0.85

        self.assertIn("paired_improvement", self._failed_conditions(rows))

    def test_gate_6_three_exact_ties_reduce_joint_win_rate_to_seventy_percent(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["seed"] in SCREENING_SEEDS[:3] and row["method"] == "anchor_local":
                row["w_alt_interp_raw_response_error_mean"] = 0.8

        failed = self._failed_conditions(rows)

        self.assertIn("joint_win_rate", failed)
        self.assertNotIn("paired_improvement", failed)

    def test_gate_7_endpoint_minimum_precedes_seed_median(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["method"] != "anchor_local":
                continue
            endpoint = (
                "w_alt_interp"
                if row["seed"] in SCREENING_SEEDS[:5]
                else "w_alt_family"
            )
            row[f"{endpoint}_raw_response_error_mean"] = 0.8 / 0.95

        failed = self._failed_conditions(rows)

        self.assertIn("worst_endpoint_improvement", failed)
        self.assertNotIn("paired_improvement", failed)
        self.assertNotIn("joint_win_rate", failed)

    def test_gate_8_observed_rmse_uses_median_then_best_comparator(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["method"] == CANDIDATE:
                row["observed_topology_prediction_rmse"] = 1.1550001

        self.assertIn("observed_rmse_guardrail", self._failed_conditions(rows))

    def test_gate_9_w_ref_uses_raw_response_median_guardrail(self) -> None:
        rows = passing_screening_rows()
        for row in self._target_rows(rows):
            if row["method"] == CANDIDATE:
                row["w_ref_raw_response_error_mean"] = 1.1550001

        self.assertIn("w_ref_guardrail", self._failed_conditions(rows))

    def test_guardrail_equality_at_one_point_zero_five_passes(self) -> None:
        rows = passing_screening_rows()
        for row in rows:
            if row["method"] == CANDIDATE:
                row["observed_topology_prediction_rmse"] = 1.155
                row["w_ref_raw_response_error_mean"] = 1.155

        result = evaluate_screening_gate(rows, config=R006EConfig())

        self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
