"""Synthetic contract tests for truth-isolated R006e endpoint metrics."""

from __future__ import annotations

import inspect
import json
import unittest

import numpy as np

from scripts.experiments.r006e_endpoint_support import (
    EndpointConstruction,
    FamilyCandidateRecord,
    QuerySupportPath,
)
from scripts.experiments.r006e_native_metrics import (
    EVALUATOR_ROW_FIELDS,
    anchor_query,
    evaluate_endpoint_path,
    evaluate_method,
)
from scripts.experiments.r006e_native_estimators import FittedPath
from scripts.experiments.r006e_native_estimators import fit_path_digest
from scripts.experiments.r006e_native_protocol import (
    FitInputs,
    R006EConfig,
    TruthBundle,
)


def synthetic_config() -> R006EConfig:
    return R006EConfig(n=2, true_rank=2, fitted_rank=1, horizon=1)


def synthetic_support_path(dates: np.ndarray, *, chi: float = 0.01) -> QuerySupportPath:
    count = len(dates)
    return QuerySupportPath(
        dates=dates,
        chi=np.full(count, chi),
        amplification=np.full(count, 2.0),
        alpha=np.full(count, 0.5),
        retained_rank=np.full(count, 2),
        condition_number=np.full(count, 3.0),
        singular_values=tuple(np.array([3.0, 1.0]) for _ in range(count)),
    )


def synthetic_endpoints(*, family_prospective_chi: float = 0.01) -> EndpointConstruction:
    calibration = synthetic_support_path(np.arange(80, 140))
    prospective = synthetic_support_path(np.arange(140, 200))
    family_prospective = synthetic_support_path(
        np.arange(140, 200), chi=family_prospective_chi
    )
    interp = np.array([[0.0, 1.0], [1.0, 0.0]])
    family = np.array([[0.75, 0.25], [0.25, 0.75]])
    records = tuple(
        FamilyCandidateRecord(
            index=index,
            endpoint=family if index == 0 else np.full((2, 2), float(index)),
            path=calibration,
        )
        for index in range(64)
    )
    lost = family_prospective_chi > synthetic_config().support_threshold
    return EndpointConstruction(
        status="CONSTRUCTION_FAIL" if lost else "CONSTRUCTION_PASS",
        failure_reasons=("family_lost_support_prospectively",) if lost else (),
        w_alt_interp=interp,
        w_alt_family=family,
        family_selected_index=0,
        interp_calibration=calibration,
        interp_prospective=prospective,
        family_calibration=calibration,
        family_prospective=family_prospective,
        family_candidates=records,
    )


def synthetic_evaluation_fixture() -> tuple[
    FittedPath, FitInputs, TruthBundle, EndpointConstruction, R006EConfig
]:
    config = synthetic_config()
    dates = np.arange(80, 200)
    w_ref = np.eye(2)
    predictors = np.ones((200, 2))
    topology = np.repeat(w_ref[None, :, :], 200, axis=0)
    m_ref = np.zeros((200, 2, 2))
    b = np.zeros((200, 2, 2))
    for date in range(164, 200):
        m_ref[date] = np.diag([date / 1000.0, date / 2000.0])
        b[date] = np.array([[0.01, 0.02], [0.03, 0.01]])
    outcomes = np.einsum("tij,tj->ti", m_ref, predictors, optimize=True)
    fit = FitInputs(
        predictors=predictors,
        outcomes=outcomes,
        topology=topology,
        w_ref=w_ref,
        coefficient_dates=dates,
    )
    tensor = np.full((2, 4, 120), 50.0)
    tensor[:, :2, 84:] = np.moveaxis(m_ref[164:200], 0, 2)
    tensor[:, 2:, 84:] = np.moveaxis(b[164:200], 0, 2)
    fitted = FittedPath(
        method="synthetic_anchor",
        parameterization="anchor",
        tensor=tensor,
        dates=dates,
        selected_penalty=0.25,
        diagnostics={
            "status": "success",
            "evaluation": [
                {
                    "selected_start_index": 1,
                    "starts": [
                        {"converged": False, "objective_trace": [4.0, 3.0]},
                        {"converged": True, "objective_trace": [3.0, 2.0, 2.0]},
                    ],
                }
            ],
        },
        runtime_seconds=1.25,
    )
    truth = TruthBundle(
        m_ref=m_ref,
        b=b,
        observed_operator=m_ref,
    )
    return fitted, fit, truth, synthetic_endpoints(), config


class R006ENativeMetricsTest(unittest.TestCase):
    def _row_with_synthetic_evaluation_diagnostic(
        self, record: dict[str, object]
    ) -> dict[str, object]:
        fitted, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        replaced = FittedPath(
            method=fitted.method,
            parameterization=fitted.parameterization,
            tensor=fitted.tensor,
            dates=fitted.dates,
            selected_penalty=fitted.selected_penalty,
            diagnostics={"status": "success", "evaluation": [record]},
            runtime_seconds=fitted.runtime_seconds,
        )
        return evaluate_method(
            replaced, fit=fit, truth=truth, endpoints=endpoints, config=config
        )

    def test_anchor_query_at_reference_is_m_ref_exactly(self) -> None:
        m_ref = np.arange(8.0).reshape(2, 2, 2)
        b = np.ones_like(m_ref)
        w_ref = np.eye(2)

        np.testing.assert_array_equal(
            anchor_query(m_ref, b, w_ref, w_ref),
            m_ref,
        )

    def test_synthetic_endpoint_queries_use_right_multiplication_orientation(self) -> None:
        m_ref = np.array([[1.0, 2.0], [3.0, 4.0]])
        b = np.array([[2.0, 1.0], [0.0, 3.0]])
        w_ref = np.eye(2)
        w_alt_interp = np.array([[0.0, 1.0], [0.25, 0.75]])
        w_alt_family = np.array([[0.6, 0.4], [0.1, 0.9]])

        np.testing.assert_array_equal(anchor_query(m_ref, b, w_ref, w_ref), m_ref)
        for endpoint in (w_alt_interp, w_alt_family):
            np.testing.assert_allclose(
                anchor_query(m_ref, b, w_ref, endpoint),
                m_ref + b @ (endpoint - w_ref),
            )

    def test_synthetic_unstable_dates_remain_in_raw_mean(self) -> None:
        truth = np.zeros((36, 1, 1))
        estimate = (np.arange(1.0, 37.0) / 10.0).reshape(36, 1, 1)

        result = evaluate_endpoint_path(
            truth,
            estimate,
            horizon=1,
            stability_threshold=0.98,
            projection_target=0.95,
        )

        expected_raw_mean = float(np.mean(estimate[:, 0, 0] / 2.0))
        self.assertEqual(result["raw_date_count"], len(truth))
        self.assertEqual(result["evaluation_dates"], 36)
        self.assertAlmostEqual(
            result["raw_response_error_mean"], expected_raw_mean
        )
        self.assertNotEqual(
            result["raw_response_error_mean"],
            result["projected_sensitivity_error_mean"],
        )

    def test_evaluator_has_exact_truth_isolation_boundary(self) -> None:
        self.assertEqual(
            list(inspect.signature(evaluate_method).parameters),
            ["fitted", "fit", "truth", "endpoints", "config"],
        )

    def test_synthetic_evaluator_uses_only_dates_164_through_199(self) -> None:
        fitted, fit, truth, endpoints, config = synthetic_evaluation_fixture()

        row = evaluate_method(
            fitted,
            fit=fit,
            truth=truth,
            endpoints=endpoints,
            config=config,
        )

        self.assertEqual(row["evaluation_date_start"], 164)
        self.assertEqual(row["evaluation_date_end"], 199)
        self.assertEqual(row["evaluation_dates"], 36)
        for endpoint in ("w_ref", "w_alt_interp", "w_alt_family"):
            self.assertEqual(row[f"{endpoint}_available"], 1)
            self.assertEqual(row[f"{endpoint}_raw_date_count"], 36)
            self.assertAlmostEqual(
                row[f"{endpoint}_operator_relative_error_mean"], 0.0
            )
        self.assertAlmostEqual(row["observed_topology_prediction_rmse"], 0.0)
        self.assertEqual(row["fit_success"], 1)
        self.assertEqual(row["scorable"], 1)
        self.assertEqual(row["at_least_one_converged_start"], 1)
        self.assertEqual(row["selected_objective_trace_nonincreasing"], 1)
        self.assertEqual(row["selected_hyperparameter"], 0.25)
        self.assertEqual(set(row), set(EVALUATOR_ROW_FIELDS))
        json.dumps(row, allow_nan=False, sort_keys=True)

    def test_synthetic_lost_family_support_is_unavailable_without_redraw(self) -> None:
        fitted, fit, truth, _, config = synthetic_evaluation_fixture()
        endpoints = synthetic_endpoints(family_prospective_chi=0.11)

        row = evaluate_method(
            fitted,
            fit=fit,
            truth=truth,
            endpoints=endpoints,
            config=config,
        )

        self.assertEqual(row["family_selected_index"], 0)
        self.assertEqual(row["w_alt_interp_available"], 1)
        self.assertEqual(row["w_alt_family_available"], 0)
        self.assertEqual(row["w_alt_family_availability_status"], "lost_support")
        self.assertIsNone(row["w_alt_family_raw_response_error_mean"])

    def test_synthetic_failed_fit_is_retained_as_flat_nonscorable_row(self) -> None:
        _, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        failed = FittedPath(
            method="synthetic_failed",
            parameterization="anchor",
            tensor=np.empty((2, 4, 0)),
            dates=np.array([], dtype=int),
            selected_penalty=None,
            diagnostics={
                "status": "failure",
                "error_type": "SyntheticFailure",
                "error_message": "toy fixture failed",
                "intended_dates": list(range(164, 200)),
                "intended_count": 36,
                "expected_tensor_shape": [2, 4, 36],
            },
            runtime_seconds=0.5,
        )

        row = evaluate_method(
            failed,
            fit=fit,
            truth=truth,
            endpoints=endpoints,
            config=config,
        )

        self.assertEqual(row["method"], "synthetic_failed")
        self.assertEqual(row["fit_success"], 0)
        self.assertEqual(row["scorable"], 0)
        self.assertEqual(row["failure_code"], "SyntheticFailure")
        self.assertEqual(row["failure_reason"], "toy fixture failed")
        self.assertIsNone(row["w_alt_interp_raw_response_error_mean"])
        self.assertIsNone(row["observed_topology_prediction_rmse"])
        self.assertTrue(
            all(
                value is None or isinstance(value, (str, bool, int, float))
                for value in row.values()
            )
        )
        self.assertEqual(set(row), set(EVALUATOR_ROW_FIELDS))
        json.dumps(row, allow_nan=False, sort_keys=True)

    def test_synthetic_method_raw_mean_keeps_all_36_dates_in_order(self) -> None:
        _, fit, _, endpoints, config = synthetic_evaluation_fixture()
        values = np.arange(1.0, 37.0) / 10.0
        tensor = np.zeros((2, 4, 36))
        for position, value in enumerate(values):
            tensor[:, :2, position] = np.eye(2) * value
        fitted = FittedPath(
            method="synthetic_unstable",
            parameterization="anchor",
            tensor=tensor,
            dates=np.arange(164, 200),
            selected_penalty=None,
            diagnostics={
                "status": "success",
                "converged": True,
                "objective_trace": [2.0, 1.0],
            },
            runtime_seconds=0.0,
        )
        zero_truth = TruthBundle(
            m_ref=np.zeros((200, 2, 2)),
            b=np.zeros((200, 2, 2)),
            observed_operator=np.zeros((200, 2, 2)),
        )
        zero_fit = FitInputs(
            predictors=fit.predictors,
            outcomes=np.zeros_like(fit.outcomes),
            topology=fit.topology,
            w_ref=fit.w_ref,
            coefficient_dates=fit.coefficient_dates,
        )

        row = evaluate_method(
            fitted,
            fit=zero_fit,
            truth=zero_truth,
            endpoints=endpoints,
            config=config,
        )

        self.assertAlmostEqual(
            row["w_ref_raw_response_error_mean"], float(np.mean(values / 2.0))
        )
        self.assertEqual(row["w_ref_raw_date_count"], 36)
        self.assertAlmostEqual(
            row["w_ref_estimated_instability_rate"], 27.0 / 36.0
        )
        self.assertNotEqual(
            row["w_ref_raw_response_error_mean"],
            row["w_ref_projected_sensitivity_error_mean"],
        )

    def test_synthetic_success_row_contains_required_frozen_metrics(self) -> None:
        fitted, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        row = evaluate_method(
            fitted, fit=fit, truth=truth, endpoints=endpoints, config=config
        )
        required = {
            "w_ref_raw_response_error_mean",
            "w_alt_interp_raw_response_error_mean",
            "w_alt_family_raw_response_error_mean",
            "w_alt_interp_operator_relative_error_mean",
            "w_alt_family_response_zero_ratio_mean",
            "observed_topology_prediction_rmse",
            "m_ref_relative_error_mean",
            "b_relative_error_mean",
            "topology_slope_interp_error_mean",
            "topology_slope_family_error_mean",
            "estimated_instability_rate",
            "w_alt_interp_evaluation_amplification_mean",
            "w_alt_family_evaluation_chi_max",
            "runtime_seconds",
            "fit_success",
            "scorable",
            "at_least_one_converged_start",
            "selected_objective_trace_nonincreasing",
            "fit_diagnostics_json",
        }
        self.assertTrue(required.issubset(row), required - set(row))

    def test_evaluator_payload_leaves_identity_and_memory_to_task10_runner(self) -> None:
        fitted, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        row = evaluate_method(
            fitted, fit=fit, truth=truth, endpoints=endpoints, config=config
        )

        self.assertEqual(row["method"], fitted.method)
        self.assertEqual(row["fit_sha256"], fit_path_digest(fitted))
        # Task 10 attaches run identity and measured memory around this payload.
        self.assertTrue(
            {"seed", "rho", "a3", "eta", "peak_memory_bytes"}.isdisjoint(row)
        )

    def test_synthetic_finite_overflow_is_retained_as_evaluation_failure(self) -> None:
        _, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        tensor = np.zeros((2, 4, 36))
        tensor[:, :2, :] = 1e200
        fitted = FittedPath(
            method="synthetic_finite_overflow",
            parameterization="anchor",
            tensor=tensor,
            dates=np.arange(164, 200),
            selected_penalty=None,
            diagnostics={"status": "success", "converged": True,
                         "objective_trace": [2.0, 1.0]},
            runtime_seconds=0.0,
        )

        row = evaluate_method(
            fitted, fit=fit, truth=truth, endpoints=endpoints, config=config
        )

        self.assertEqual(row["fit_success"], 1)
        self.assertEqual(row["scorable"], 0)
        self.assertEqual(row["failure_code"], "EVALUATION_NUMERICAL_FAIL")
        self.assertIsInstance(row["failure_reason"], str)
        self.assertIsNone(row["w_ref_raw_response_error_mean"])
        self.assertIsNone(row["m_ref_relative_error_mean"])
        self.assertEqual(row["w_ref_available"], 1)
        self.assertTrue(
            all(
                value is None or isinstance(value, (str, bool, int, float))
                for value in row.values()
            )
        )
        json.dumps(row, allow_nan=False, sort_keys=True)

    def test_synthetic_nonfinite_truth_is_retained_as_evaluation_failure(self) -> None:
        fitted, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        nonfinite_m_ref = np.array(truth.m_ref, copy=True)
        nonfinite_m_ref[164, 0, 0] = np.nan
        nonfinite_truth = TruthBundle(
            m_ref=nonfinite_m_ref,
            b=truth.b,
            observed_operator=truth.observed_operator,
        )

        row = evaluate_method(
            fitted,
            fit=fit,
            truth=nonfinite_truth,
            endpoints=endpoints,
            config=config,
        )

        self.assertEqual(row["fit_success"], 1)
        self.assertEqual(row["scorable"], 0)
        self.assertEqual(row["failure_code"], "EVALUATION_NUMERICAL_FAIL")
        self.assertIn("endpoint paths must be finite", row["failure_reason"])
        self.assertIsNone(row["w_ref_raw_response_error_mean"])
        self.assertIsNone(row["observed_topology_prediction_rmse"])
        self.assertEqual(row["w_ref_available"], 1)
        json.dumps(row, allow_nan=False, sort_keys=True)

    def test_synthetic_malformed_success_tensor_shape_raises_contract_error(self) -> None:
        _, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        malformed = FittedPath(
            method="synthetic_bad_shape",
            parameterization="anchor",
            tensor=np.zeros((2, 3, 36)),
            dates=np.arange(164, 200),
            selected_penalty=None,
            diagnostics={"status": "success"},
            runtime_seconds=0.0,
        )

        with self.assertRaisesRegex(
            ValueError, "fitted tensor does not match config"
        ):
            evaluate_method(
                malformed,
                fit=fit,
                truth=truth,
                endpoints=endpoints,
                config=config,
            )

    def test_synthetic_mismatched_config_raises_contract_error(self) -> None:
        fitted, fit, truth, endpoints, _ = synthetic_evaluation_fixture()
        mismatched = R006EConfig(n=3, true_rank=3, fitted_rank=1, horizon=1)

        with self.assertRaisesRegex(ValueError, "fit inputs do not match config"):
            evaluate_method(
                fitted,
                fit=fit,
                truth=truth,
                endpoints=endpoints,
                config=mismatched,
            )

    def test_synthetic_missing_required_evaluation_date_raises_contract_error(self) -> None:
        fitted, fit, truth, endpoints, config = synthetic_evaluation_fixture()
        missing_date = FittedPath(
            method="synthetic_missing_date",
            parameterization="anchor",
            tensor=fitted.tensor[:, :, 83:119],
            dates=np.arange(163, 199),
            selected_penalty=None,
            diagnostics={"status": "success"},
            runtime_seconds=0.0,
        )

        with self.assertRaisesRegex(
            ValueError, "every evaluation date 164..199"
        ):
            evaluate_method(
                missing_date,
                fit=fit,
                truth=truth,
                endpoints=endpoints,
                config=config,
            )

    def test_synthetic_prefix_missing_selected_start_index_cannot_pass(self) -> None:
        row = self._row_with_synthetic_evaluation_diagnostic(
            {
                "starts": [
                    {"converged": True, "objective_trace": [2.0, 1.0]}
                ]
            }
        )
        self.assertEqual(row["at_least_one_converged_start"], 1)
        self.assertEqual(row["selected_objective_trace_nonincreasing"], 0)
        self.assertEqual(row["scorable"], 0)

    def test_synthetic_prefix_out_of_range_selected_index_cannot_pass(self) -> None:
        row = self._row_with_synthetic_evaluation_diagnostic(
            {
                "selected_start_index": 3,
                "starts": [
                    {"converged": True, "objective_trace": [2.0, 1.0]}
                ],
            }
        )
        self.assertEqual(row["at_least_one_converged_start"], 1)
        self.assertEqual(row["selected_objective_trace_nonincreasing"], 0)
        self.assertEqual(row["scorable"], 0)

    def test_synthetic_unconverged_selected_start_cannot_borrow_other_start(self) -> None:
        row = self._row_with_synthetic_evaluation_diagnostic(
            {
                "selected_start_index": 0,
                "starts": [
                    {"converged": False, "objective_trace": [2.0, 1.0]},
                    {"converged": True, "objective_trace": [3.0, 2.0]},
                ],
            }
        )
        self.assertEqual(row["at_least_one_converged_start"], 1)
        self.assertEqual(row["selected_objective_trace_nonincreasing"], 0)
        self.assertEqual(row["scorable"], 0)

    def test_synthetic_nonmonotone_selected_trace_cannot_borrow_other_start(self) -> None:
        row = self._row_with_synthetic_evaluation_diagnostic(
            {
                "selected_start_index": 0,
                "starts": [
                    {"converged": True, "objective_trace": [1.0, 2.0]},
                    {"converged": True, "objective_trace": [3.0, 2.0]},
                ],
            }
        )
        self.assertEqual(row["at_least_one_converged_start"], 1)
        self.assertEqual(row["selected_objective_trace_nonincreasing"], 0)
        self.assertEqual(row["scorable"], 0)


if __name__ == "__main__":
    unittest.main()
