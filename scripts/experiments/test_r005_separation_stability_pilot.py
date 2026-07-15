import importlib
import tempfile
import unittest
from pathlib import Path

import numpy as np


class R005SeparationStabilityPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.pilot = importlib.import_module(
                "scripts.experiments.r005_separation_stability_pilot"
            )
        except ModuleNotFoundError:
            cls.pilot = None

    def require_pilot(self):
        self.assertIsNotNone(
            self.pilot,
            "R005 pilot module must implement the frozen separation/stability design",
        )
        return self.pilot

    def test_generated_operators_hit_true_spectral_radius_target(self):
        pilot = self.require_pilot()
        panel = pilot.generate_panel(
            n=8,
            t_len=70,
            rank=2,
            separation_strength=0.15,
            target_rho=0.95,
            sigma=0.25,
            seed=101,
        )
        measured = [pilot.spectral_radius(matrix) for matrix in panel["M"]]
        self.assertLess(np.max(np.abs(np.asarray(measured) - 0.95)), 1e-10)

    def test_topology_variation_controls_residualized_separation(self):
        pilot = self.require_pilot()
        common = dict(n=8, t_len=100, rank=2, target_rho=0.5, sigma=0.25, seed=202)
        low = pilot.generate_panel(separation_strength=0.02, **common)
        high = pilot.generate_panel(separation_strength=0.45, **common)
        low_value = np.median(
            pilot.rolling_separation_diagnostics(low["y"], low["W"], window=40)
        )
        high_value = np.median(
            pilot.rolling_separation_diagnostics(high["y"], high["W"], window=40)
        )
        self.assertGreater(high_value, 2.0 * low_value)

    def test_unstable_truth_keeps_raw_errors_separate_for_all_methods(self):
        pilot = self.require_pilot()
        config = pilot.PilotConfig(
            n=6,
            t_len=65,
            window=24,
            rank=2,
            spline_df=6,
            cp_iterations=15,
            cp_starts=1,
            evaluation_fraction=0.2,
        )
        rows = pilot.run_replication(
            config=config,
            separation_strength=0.15,
            target_rho=1.01,
            seed=303,
        )
        self.assertEqual(
            {row["method"] for row in rows},
            {"local", "cp_rank2", "tucker_222", "spline_df6"},
        )
        for row in rows:
            self.assertGreaterEqual(row["raw_response_error_mean"], 0.0)
            self.assertEqual(row["stability_qualified_rate"], 0.0)
            self.assertIsNone(row["stability_qualified_error_mean"])
            self.assertGreaterEqual(row["projected_sensitivity_error_mean"], 0.0)

    def test_run_grid_accepts_relative_output_directory(self):
        pilot = self.require_pilot()
        config = pilot.PilotConfig(
            n=6,
            t_len=55,
            window=24,
            rank=2,
            spline_df=6,
            cp_iterations=5,
            cp_starts=1,
            evaluation_fraction=0.2,
        )
        temporary_root = pilot.ROOT / "tmp"
        temporary_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            relative_output = Path(directory).relative_to(pilot.ROOT)
            try:
                result = pilot.run_grid(
                    config=config,
                    separation_levels=(0.15,),
                    stability_levels=(0.5,),
                    seeds=(404,),
                    workers=1,
                    output_dir=relative_output,
                    smoke=True,
                )
            except ValueError as exc:
                self.fail(f"relative output directory was rejected: {exc}")
        self.assertEqual(result["output_dir"], str(relative_output))


if __name__ == "__main__":
    unittest.main()
