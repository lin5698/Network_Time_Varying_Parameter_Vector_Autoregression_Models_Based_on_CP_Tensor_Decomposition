import importlib
import tempfile
import unittest
from pathlib import Path

import numpy as np


class R006ApproximateRankPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.pilot = importlib.import_module(
                "scripts.experiments.r006_approximate_rank_pilot"
            )
        except ModuleNotFoundError:
            cls.pilot = None

    def require_pilot(self):
        self.assertIsNotNone(
            self.pilot,
            "R006 pilot module must implement the frozen approximate-rank design",
        )
        return self.pilot

    def test_generator_calibrates_rank_tail_and_query_radius(self):
        pilot = self.require_pilot()
        panel = pilot.generate_approximate_rank_panel(
            n=8,
            t_len=75,
            true_rank=6,
            head_rank=3,
            approximation_target=0.25,
            separation_strength=0.15,
            target_rho=0.8,
            sigma=0.25,
            seed=501,
        )
        self.assertLess(abs(panel["a3_ratio"] - 0.25), 1e-6)
        radii = [pilot.spectral_radius(matrix) for matrix in panel["M"]]
        self.assertLess(np.max(np.abs(np.asarray(radii) - 0.8)), 1e-10)
        self.assertGreaterEqual(panel["a5_ratio"], 0.0)
        self.assertLessEqual(panel["a5_ratio"], panel["a3_ratio"])

    def test_fused_tv_preserves_constant_and_reduces_noisy_total_variation(self):
        pilot = self.require_pilot()
        constant = np.full((40, 3), 2.5)
        preserved, constant_diagnostics = pilot.fused_tv_denoise(
            constant, penalty_multiplier=0.5
        )
        np.testing.assert_allclose(preserved, constant, atol=1e-10)
        self.assertTrue(constant_diagnostics["converged"])

        rng = np.random.default_rng(502)
        truth = np.concatenate([np.zeros(20), np.ones(20)])[:, None]
        noisy = truth + rng.normal(scale=0.25, size=(40, 1))
        denoised, diagnostics = pilot.fused_tv_denoise(
            noisy, penalty_multiplier=1.0
        )
        noisy_variation = np.abs(np.diff(noisy[:, 0])).sum()
        denoised_variation = np.abs(np.diff(denoised[:, 0])).sum()
        self.assertLess(denoised_variation, noisy_variation)
        self.assertTrue(diagnostics["converged"])

    def test_small_replication_stores_primary_and_rank_diagnostic_metrics(self):
        pilot = self.require_pilot()
        config = pilot.R006Config(
            n=6,
            t_len=70,
            window=28,
            true_rank=5,
            head_rank=3,
            fitted_ranks=(2, 3, 5),
            spline_df=6,
            cp_iterations=10,
            cp_starts=2,
            fused_penalties=(0.1, 0.5),
            fused_max_iterations=100,
            evaluation_fraction=0.2,
            validation_fraction=0.2,
        )
        rows = pilot.run_replication(
            config=config,
            approximation_target=0.10,
            target_rho=0.8,
            seed=503,
        )
        expected_methods = {
            "local",
            "spline_df6",
            "fused_tv",
            "cp_rank2",
            "cp_rank3",
            "cp_rank5",
            "tucker_222",
            "tucker_333",
            "tucker_555",
        }
        self.assertEqual({row["method"] for row in rows}, expected_methods)
        for row in rows:
            self.assertGreaterEqual(row["raw_response_error_mean"], 0.0)
            self.assertGreaterEqual(row["response_error_zero_ratio_mean"], 0.0)
            self.assertGreaterEqual(row["block_error_mean"], 0.0)
            self.assertLess(abs(row["actual_a3_ratio"] - 0.10), 1e-6)
        cp_rows = [row for row in rows if row["method"].startswith("cp_rank")]
        self.assertTrue(
            all(row["cp_start_objective_spread"] is not None for row in cp_rows)
        )
        fused_row = next(row for row in rows if row["method"] == "fused_tv")
        self.assertIn(fused_row["selected_fused_penalty"], config.fused_penalties)

    def test_smoke_report_handles_unrun_required_gate_cells(self):
        pilot = self.require_pilot()
        config = pilot.R006Config(
            n=6,
            t_len=60,
            window=26,
            true_rank=5,
            head_rank=3,
            fitted_ranks=(2, 3, 5),
            spline_df=6,
            cp_iterations=5,
            cp_starts=1,
            fused_penalties=(0.1,),
            fused_max_iterations=80,
            evaluation_fraction=0.2,
            validation_fraction=0.2,
        )
        temporary_root = pilot.ROOT / "tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            try:
                result = pilot.run_grid(
                    config=config,
                    approximation_targets=(0.0,),
                    stability_levels=(0.8,),
                    seeds=(504,),
                    workers=1,
                    output_dir=Path(directory),
                    run_type="SMOKE",
                )
            except TypeError as exc:
                self.fail(f"smoke report rejected missing gate cells: {exc}")
        self.assertEqual(result["run_type"], "SMOKE")


if __name__ == "__main__":
    unittest.main()
