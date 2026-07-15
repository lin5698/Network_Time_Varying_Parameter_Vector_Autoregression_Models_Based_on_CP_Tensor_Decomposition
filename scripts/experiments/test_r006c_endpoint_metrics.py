import unittest

import numpy as np

from scripts.experiments import r006c_endpoint_metrics as metrics
from scripts.experiments.r006c_endpoint_estimators import fit_method_bundle
from scripts.experiments.r006c_endpoint_protocol import (
    R006CConfig,
    generate_endpoint_panel,
)


class R006CEndpointMetricsTest(unittest.TestCase):
    @staticmethod
    def config():
        return R006CConfig(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            cp_iterations=3,
            cp_starts=1,
            fused_penalties=(0.10,),
            fused_max_iterations=100,
        )

    def panel_and_bundle(self):
        config = self.config()
        panel = generate_endpoint_panel(
            config=config,
            layer="matched",
            target_rho=0.80,
            approximation_target=0.10,
            separation_strength=0.15,
            seed=240100,
        )
        bundle = fit_method_bundle(
            panel.estimation,
            truth_B=panel.B,
            config=config,
            seed=240100,
            layer="matched",
            rho=0.80,
            a3=0.10,
            eta=0.15,
        )
        return panel, bundle

    def test_anchor_queries_are_exact_at_reference_and_alternative(self):
        rng = np.random.default_rng(3)
        m_ref = rng.normal(size=(4, 3, 3))
        b = rng.normal(size=(4, 3, 3))
        w_ref = rng.normal(size=(3, 3))
        w_alt = rng.normal(size=(3, 3))
        np.testing.assert_array_equal(
            metrics.query_anchor(m_ref, b, w_ref, w_ref), m_ref
        )
        np.testing.assert_allclose(
            metrics.query_anchor(m_ref, b, w_ref, w_alt),
            m_ref + np.einsum(
                "tij,jk->tik", b, w_alt - w_ref, optimize=True
            ),
        )

    def test_cancellation_index_returns_zero_for_exact_estimate(self):
        zeros = np.zeros((3, 3))
        self.assertEqual(
            metrics.cancellation_index(zeros, zeros, np.eye(3)), 0.0
        )

    def test_cancellation_index_is_large_for_cancelling_errors(self):
        delta_b = np.eye(3)
        delta_a = -delta_b
        self.assertGreater(
            metrics.cancellation_index(delta_a, delta_b, np.eye(3)), 1e12
        )

    def test_collapsed_marks_alternative_endpoints_unavailable(self):
        self.assertEqual(
            metrics.endpoint_availability("collapsed_ref_tucker333"),
            {"w_ref": True, "w_alt_main": False, "w_alt_stress": False},
        )

    def test_collapsed_row_uses_none_not_numeric_endpoint_placeholders(self):
        panel, bundle = self.panel_and_bundle()
        row = metrics.evaluate_fitted_method(
            bundle.methods["collapsed_ref_tucker333"], panel, self.config()
        )
        self.assertEqual(row["w_ref_available"], 1)
        self.assertEqual(row["w_alt_main_available"], 0)
        self.assertEqual(row["w_alt_stress_available"], 0)
        self.assertIsNone(row["w_alt_main_raw_response_error_mean"])
        self.assertIsNone(row["w_alt_stress_operator_relative_error_mean"])

    def test_anchor_row_stores_separate_metrics_at_all_endpoints(self):
        panel, bundle = self.panel_and_bundle()
        row = metrics.evaluate_fitted_method(
            bundle.methods["anchor_split_tucker333"], panel, self.config()
        )
        for endpoint in ("w_ref", "w_alt_main", "w_alt_stress"):
            self.assertEqual(row[f"{endpoint}_available"], 1)
            self.assertIsInstance(
                row[f"{endpoint}_raw_response_error_mean"], float
            )
            self.assertIn(f"{endpoint}_stability_qualified_error_mean", row)
            self.assertIn(f"{endpoint}_projected_sensitivity_error_mean", row)
        self.assertIsInstance(row["B_relative_error_mean"], float)
        self.assertIsInstance(row["topology_slope_main_error_mean"], float)
        self.assertIsInstance(row["full_stored_object_error_mean"], float)
        self.assertIsInstance(row["cancellation_index_w_ref_mean"], float)
        self.assertIsInstance(row["retrospective_prediction_rmse"], float)
        self.assertIsInstance(row["separation_diagnostic_median"], float)
        self.assertGreater(row["adaptive_ridge_penalty_mean"], 0.0)
        self.assertGreaterEqual(row["runtime_seconds"], 0.0)

    def test_cp_row_flattens_both_split_reconstruction_diagnostics(self):
        panel, bundle = self.panel_and_bundle()
        row = metrics.evaluate_fitted_method(
            bundle.methods["anchor_split_cp3"], panel, self.config()
        )
        self.assertIsInstance(row["cp_m_ref_best_relative_objective"], float)
        self.assertIsInstance(row["cp_b_best_relative_objective"], float)
        self.assertIsNone(row["cp_joint_best_relative_objective"])

    def test_unstable_estimate_keeps_raw_and_projected_metrics_separate(self):
        truth = np.repeat((0.8 * np.eye(3))[None, :, :], 2, axis=0)
        estimate = np.repeat((1.2 * np.eye(3))[None, :, :], 2, axis=0)
        result = metrics.evaluate_endpoint_path(
            truth,
            estimate,
            horizon=4,
            stability_threshold=0.98,
            projection_target=0.95,
        )
        self.assertTrue(np.isfinite(result["raw_response_error_mean"]))
        self.assertEqual(result["stability_qualified_rate"], 0.0)
        self.assertIsNone(result["stability_qualified_error_mean"])
        self.assertTrue(
            np.isfinite(result["projected_sensitivity_error_mean"])
        )


if __name__ == "__main__":
    unittest.main()
