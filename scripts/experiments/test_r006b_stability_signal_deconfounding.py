import importlib
import tempfile
import unittest
from pathlib import Path

import numpy as np


try:
    r006b = importlib.import_module(
        "scripts.experiments.r006b_stability_signal_deconfounding"
    )
except ModuleNotFoundError:
    r006b = None


class R006BStabilitySignalDeconfoundingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.common = {
            "n": 10,
            "t_len": 48,
            "true_rank": 8,
            "head_rank": 3,
            "query_frobenius_norm": 1.20,
            "separation_strength": 0.15,
            "sigma": 0.25,
            "seed": 260715,
        }

    def require_module(self):
        if r006b is None:
            self.fail("R006b implementation module is missing")
        return r006b

    def require_attribute(self, name):
        module = self.require_module()
        if not hasattr(module, name):
            self.fail(f"R006b implementation is missing {name}")
        return getattr(module, name)

    def panel(self, *, target_rho=0.95, approximation_target=0.25, layer="matched"):
        module = self.require_module()
        return module.generate_deconfounded_panel(
            **self.common,
            target_rho=target_rho,
            approximation_target=approximation_target,
            layer=layer,
        )

    def test_query_radius_hits_each_declared_stability_level(self):
        module = self.require_module()
        for target_rho in (0.80, 0.95):
            panel = self.panel(target_rho=target_rho)
            error = max(
                abs(module.spectral_radius(matrix) - target_rho)
                for matrix in panel["M"]
            )
            self.assertLess(error, 1e-10)

    def test_query_frobenius_norm_is_matched_across_stability_levels(self):
        low = self.panel(target_rho=0.80)
        high = self.panel(target_rho=0.95)
        low_norms = np.linalg.norm(low["M"], axis=(1, 2))
        high_norms = np.linalg.norm(high["M"], axis=(1, 2))
        self.assertLess(float(np.max(np.abs(low_norms - high_norms))), 1e-6)
        self.assertLess(
            float(np.max(np.abs(low_norms - self.common["query_frobenius_norm"]))),
            1e-10,
        )

    def test_separated_query_identity_holds(self):
        panel = self.panel()
        reconstructed = panel["A"] + np.einsum(
            "tij,jk->tik", panel["B"], panel["W_reference"], optimize=True
        )
        self.assertLess(float(np.max(np.abs(reconstructed - panel["M"]))), 1e-10)

    def test_each_concatenated_block_component_is_rank_one(self):
        panel = self.panel()
        for component in range(self.common["true_rank"]):
            for date in range(self.common["t_len"]):
                block = np.concatenate(
                    [
                        panel["direct_components"][component, date],
                        panel["network_components"][component, date],
                    ],
                    axis=1,
                )
                singular_values = np.linalg.svd(block, compute_uv=False)
                self.assertLess(float(singular_values[1]), 1e-10)

    def test_scale_adaptive_ridge_is_invariant_to_global_data_scaling(self):
        module = self.require_module()
        rng = np.random.default_rng(715)
        design = rng.normal(size=(96, 12))
        outcome = rng.normal(size=(96, 5))
        reference, diagnostics = module.fit_scale_adaptive_ridge(
            design, outcome, ridge_multiplier=0.01
        )
        self.assertGreater(diagnostics["ridge_penalty"], 0.0)
        for scale in (0.05, 7.0, 100.0):
            scaled, _ = module.fit_scale_adaptive_ridge(
                scale * design, scale * outcome, ridge_multiplier=0.01
            )
            self.assertLess(float(np.max(np.abs(reference - scaled))), 1e-8)

    def test_matched_excitation_design_covariance_is_shared_across_rho(self):
        module = self.require_module()
        low = self.panel(target_rho=0.80, layer="matched")
        high = self.panel(target_rho=0.95, layer="matched")
        low_covariance = module.design_covariance(
            low["predictors"], low["W"]
        )
        high_covariance = module.design_covariance(
            high["predictors"], high["W"]
        )
        mismatch = np.linalg.norm(low_covariance - high_covariance) / max(
            np.linalg.norm(low_covariance), 1e-12
        )
        self.assertLess(float(mismatch), 0.01)

    def test_rank_three_tail_calibration_hits_declared_targets(self):
        for target in (0.0, 0.10, 0.25, 0.50):
            panel = self.panel(approximation_target=target)
            self.assertLess(abs(panel["a3_ratio"] - target), 1e-6)

    def test_observed_topology_operators_remain_finite_horizon_bounded(self):
        module = self.require_module()
        for target_rho in (0.80, 0.95):
            panel = self.panel(target_rho=target_rho, layer="native")
            radii = [module.spectral_radius(matrix) for matrix in panel["M_observed"]]
            self.assertTrue(np.all(np.isfinite(radii)))
            self.assertLess(max(radii), 1.05)

    def test_generic_rolling_estimator_uses_adaptive_positive_penalties(self):
        module = self.require_module()
        estimate_local_blocks = self.require_attribute("estimate_local_blocks")
        panel = self.panel(approximation_target=0.10, layer="matched")
        tensor, indices, diagnostics, ridge_diagnostics = (
            estimate_local_blocks(
                panel["predictors"],
                panel["outcomes"],
                panel["W"],
                window=24,
                ridge_multiplier=0.001,
            )
        )
        self.assertEqual(tensor.shape, (10, 20, 24))
        self.assertEqual(indices.tolist(), list(range(24, 48)))
        self.assertEqual(diagnostics.shape, (24,))
        self.assertTrue(np.all(ridge_diagnostics["ridge_penalties"] > 0.0))
        self.assertTrue(np.all(ridge_diagnostics["gram_scales"] > 0.0))

    def test_small_replication_stores_both_layer_and_method_diagnostics(self):
        module = self.require_module()
        config_class = self.require_attribute("R006BConfig")
        run_replication = self.require_attribute("run_replication")
        config = config_class(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            spline_df=6,
            cp_iterations=4,
            cp_starts=1,
            fused_penalties=(0.10,),
            fused_max_iterations=100,
            evaluation_fraction=0.25,
            validation_fraction=0.20,
        )
        expected_methods = {
            "local",
            "spline_df6",
            "fused_tv",
            "cp_rank3",
            "tucker_333",
        }
        for layer in ("matched", "native"):
            rows = run_replication(
                config=config,
                approximation_target=0.10,
                target_rho=0.80,
                seed=260716,
                layer=layer,
            )
            self.assertEqual({row["method"] for row in rows}, expected_methods)
            self.assertTrue(all(row["layer"] == layer for row in rows))
            self.assertTrue(all(row["failure"] == 0 for row in rows))
            for row in rows:
                self.assertIn("raw_response_error_mean", row)
                self.assertIn("stability_qualified_error_mean", row)
                self.assertIn("projected_sensitivity_error_mean", row)
                self.assertIn("design_gram_condition", row)
                self.assertIn("innovation_to_state_variance_ratio", row)
                self.assertIn("retrospective_prediction_rmse", row)
            if layer == "native":
                self.assertTrue(
                    all(
                        row["innovation_to_state_variance_ratio"] is not None
                        for row in rows
                    )
                )

    def test_smoke_report_cannot_pass_the_full_protocol(self):
        module = self.require_module()
        config_class = self.require_attribute("R006BConfig")
        run_grid = self.require_attribute("run_grid")
        config = config_class(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            spline_df=6,
            cp_iterations=2,
            cp_starts=1,
            fused_penalties=(0.10,),
            fused_max_iterations=100,
        )
        with tempfile.TemporaryDirectory() as directory:
            report = run_grid(
                config=config,
                approximation_targets=(0.10,),
                stability_levels=(0.80,),
                seeds=(260717,),
                layers=("matched",),
                workers=1,
                output_dir=Path(directory),
                smoke=True,
            )
            self.assertIn(report["status"], {"SMOKE_PASS", "SMOKE_FAIL"})
            self.assertNotEqual(report["status"], "PASS")
            self.assertTrue((Path(directory) / "r006b_results.json").exists())

    def test_fused_penalty_selection_excludes_evaluation_local_estimates(self):
        module = self.require_module()
        config_class = self.require_attribute("R006BConfig")
        select_fused_penalty = self.require_attribute("select_fused_penalty")
        estimate_local_blocks = self.require_attribute("estimate_local_blocks")
        config = config_class(
            n=10,
            t_len=48,
            window=24,
            true_rank=8,
            fused_penalties=(0.10, 1.00),
            fused_max_iterations=200,
            evaluation_fraction=0.25,
            validation_fraction=0.20,
        )
        panel = self.panel(approximation_target=0.10, layer="matched")
        local_tensor, indices, _, _ = estimate_local_blocks(
            panel["predictors"],
            panel["outcomes"],
            panel["W"],
            window=config.window,
            ridge_multiplier=config.ridge_multiplier,
        )
        evaluation_count = int(np.ceil(config.evaluation_fraction * len(indices)))
        perturbed = local_tensor.copy()
        perturbed[:, :, -evaluation_count:] += 100.0

        selected, diagnostics = select_fused_penalty(
            local_tensor, panel, indices, config
        )
        perturbed_selected, perturbed_diagnostics = select_fused_penalty(
            perturbed, panel, indices, config
        )
        self.assertEqual(selected, perturbed_selected)
        self.assertEqual(
            diagnostics["candidate_scores"],
            perturbed_diagnostics["candidate_scores"],
        )
        self.assertEqual(diagnostics["evaluation_dates_excluded"], evaluation_count)

    def test_result_payload_stores_protocol_and_code_hashes(self):
        module = self.require_module()
        config_class = self.require_attribute("R006BConfig")
        run_grid = self.require_attribute("run_grid")
        config = config_class(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            spline_df=6,
            cp_iterations=2,
            cp_starts=1,
            fused_penalties=(0.10,),
            fused_max_iterations=100,
        )
        with tempfile.TemporaryDirectory() as directory:
            payload = run_grid(
                config=config,
                approximation_targets=(0.10,),
                stability_levels=(0.80,),
                seeds=(260718,),
                layers=("matched",),
                workers=1,
                output_dir=Path(directory),
                smoke=True,
            )
            self.assertIn("provenance", payload)
            self.assertRegex(payload["provenance"]["protocol_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(payload["provenance"]["code_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
