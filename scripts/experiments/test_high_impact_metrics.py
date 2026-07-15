import importlib
import unittest

import numpy as np


class HighImpactMetricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.metrics = importlib.import_module("scripts.experiments.high_impact_metrics")
        except ModuleNotFoundError:
            cls.metrics = None

    def require_metrics(self):
        self.assertIsNotNone(
            self.metrics,
            "high_impact_metrics module must implement the audited response definitions",
        )
        return self.metrics

    def test_spectral_radius_uses_eigenvalues_for_nonnormal_matrix(self):
        metrics = self.require_metrics()
        matrix = np.array([[0.8, 10.0], [0.0, 0.8]])
        self.assertAlmostEqual(metrics.spectral_radius(matrix), 0.8, places=10)
        self.assertGreater(np.linalg.norm(matrix, ord=2), 10.0)

    def test_unstable_pair_keeps_raw_error_but_has_no_qualified_error(self):
        metrics = self.require_metrics()
        result = metrics.evaluate_response_pair(
            np.array([[1.2]]),
            np.array([[1.05]]),
            horizon=8,
            stability_threshold=0.98,
        )
        self.assertGreater(result["raw_response_error"], 1.0)
        self.assertIsNone(result["stability_qualified_error"])
        self.assertFalse(result["stability_qualified"])

    def test_stable_pair_reports_same_raw_and_qualified_error(self):
        metrics = self.require_metrics()
        result = metrics.evaluate_response_pair(
            np.array([[0.8]]),
            np.array([[0.7]]),
            horizon=8,
            stability_threshold=0.98,
        )
        self.assertTrue(result["stability_qualified"])
        self.assertAlmostEqual(
            result["raw_response_error"],
            result["stability_qualified_error"],
            places=12,
        )

    def test_projection_is_separate_sensitivity_and_never_replaces_raw_error(self):
        metrics = self.require_metrics()
        result = metrics.evaluate_response_pair(
            np.array([[1.2]]),
            np.array([[1.05]]),
            horizon=8,
            stability_threshold=0.98,
            projection_target=0.95,
        )
        self.assertGreater(result["raw_response_error"], 1.0)
        self.assertEqual(result["projected_sensitivity_error"], 0.0)
        self.assertTrue(result["projection_applied"])


if __name__ == "__main__":
    unittest.main()
