import inspect
import unittest
from dataclasses import replace

import numpy as np

from scripts.experiments.r006c_endpoint_protocol import (
    EstimationInputs,
    METHODS,
    R006CConfig,
    generate_endpoint_panel,
    row_normalize,
)
from scripts.experiments import r006c_endpoint_estimators as estimators


class R006CEndpointEstimatorsTest(unittest.TestCase):
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

    def panel(self):
        return generate_endpoint_panel(
            config=self.config(),
            layer="matched",
            target_rho=0.80,
            approximation_target=0.10,
            separation_strength=0.15,
            seed=240100,
        )

    def fit(self, panel=None):
        selected = panel or self.panel()
        return estimators.fit_method_bundle(
            selected.estimation,
            truth_B=selected.B,
            config=self.config(),
            seed=240100,
            layer="matched",
            rho=0.80,
            a3=0.10,
            eta=0.15,
        )

    def test_anchor_local_uses_delta_topology_design(self):
        panel = self.panel()
        tensor, indices, separation, ridge = estimators.estimate_anchor_local(
            panel.estimation,
            window=self.config().window,
            ridge_multiplier=self.config().ridge_multiplier,
        )
        self.assertEqual(tensor.shape, (8, 16, 24))
        self.assertEqual(indices.tolist(), list(range(24, 48)))
        self.assertEqual(separation.shape, (24,))
        self.assertTrue(np.all(np.isfinite(separation)))
        self.assertTrue(np.all(ridge["ridge_penalties"] > 0.0))
        self.assertTrue(np.all(ridge["gram_scales"] > 0.0))

    def test_fit_bundle_has_exactly_the_nine_frozen_methods(self):
        bundle = self.fit()
        self.assertEqual(tuple(bundle.methods), METHODS)
        self.assertEqual(len(bundle.methods), 9)

    def test_split_candidates_reconstruct_m_ref_and_b_separately(self):
        bundle = self.fit()
        for name in ("anchor_split_cp3", "anchor_split_tucker333"):
            fitted = bundle.methods[name]
            self.assertEqual(fitted.parameterization, "anchor")
            self.assertEqual(fitted.tensor.shape, (8, 16, 24))
            self.assertIn("M_ref", fitted.reconstruction_diagnostics)
            self.assertIn("B", fitted.reconstruction_diagnostics)

    def test_collapsed_discards_b_and_oracle_substitutes_true_b(self):
        panel = self.panel()
        bundle = self.fit(panel)
        collapsed = bundle.methods["collapsed_ref_tucker333"]
        oracle = bundle.methods["oracle_b_anchor"]
        self.assertEqual(collapsed.parameterization, "collapsed")
        self.assertEqual(collapsed.tensor.shape, (8, 8, 24))
        expected_b = np.moveaxis(panel.B[oracle.indices], 0, 2)
        np.testing.assert_array_equal(oracle.tensor[:, 8:, :], expected_b)

    def test_fit_api_has_no_heldout_topology_parameter(self):
        parameters = inspect.signature(estimators.fit_method_bundle).parameters
        self.assertNotIn("W_alt_main", parameters)
        self.assertNotIn("W_alt_stress", parameters)

    def test_holdout_perturbation_leaves_fit_and_selection_bitwise_identical(self):
        panel = self.panel()
        rng = np.random.default_rng(91)
        holdout = row_normalize(rng.uniform(size=panel.W_ref.shape))
        changed = replace(
            panel,
            W_holdout=holdout,
            W_alt_main=row_normalize(0.75 * panel.W_ref + 0.25 * holdout),
            W_alt_stress=row_normalize(rng.uniform(size=panel.W_ref.shape)),
        )
        first = self.fit(panel)
        second = self.fit(changed)
        self.assertFalse(np.array_equal(panel.W_alt_main, changed.W_alt_main))
        self.assertFalse(np.array_equal(panel.W_alt_stress, changed.W_alt_stress))
        self.assertEqual(first.fit_digest(), second.fit_digest())
        self.assertEqual(
            first.selected_hyperparameters(), second.selected_hyperparameters()
        )

    def test_anchor_ridge_is_invariant_to_global_data_scaling(self):
        panel = self.panel()
        reference, _, _, _ = estimators.estimate_anchor_local(
            panel.estimation,
            window=self.config().window,
            ridge_multiplier=self.config().ridge_multiplier,
        )
        for scale in (0.05, 7.0, 100.0):
            scaled_inputs = EstimationInputs(
                predictors=scale * panel.estimation.predictors,
                outcomes=scale * panel.estimation.outcomes,
                topology=panel.estimation.topology,
                W_ref=panel.estimation.W_ref,
            )
            scaled, _, _, _ = estimators.estimate_anchor_local(
                scaled_inputs,
                window=self.config().window,
                ridge_multiplier=self.config().ridge_multiplier,
            )
            self.assertLess(float(np.max(np.abs(reference - scaled))), 1e-8)

    def test_fused_selection_excludes_evaluation_local_estimates(self):
        config = replace(
            self.config(),
            fused_penalties=(0.10, 1.00),
            evaluation_fraction=0.25,
            validation_fraction=0.20,
        )
        panel = self.panel()
        local, indices, _, _ = estimators.estimate_local_blocks(
            panel.estimation.predictors,
            panel.estimation.outcomes,
            panel.estimation.topology,
            window=config.window,
            ridge_multiplier=config.ridge_multiplier,
        )
        evaluation_count = int(np.ceil(config.evaluation_fraction * len(indices)))
        perturbed = local.copy()
        perturbed[:, :, -evaluation_count:] += 100.0
        fit_panel = {
            "predictors": panel.estimation.predictors,
            "outcomes": panel.estimation.outcomes,
            "W": panel.estimation.topology,
        }
        selected, diagnostics = estimators.select_fused_penalty(
            local, fit_panel, indices, config
        )
        changed, changed_diagnostics = estimators.select_fused_penalty(
            perturbed, fit_panel, indices, config
        )
        self.assertEqual(selected, changed)
        self.assertEqual(
            diagnostics["candidate_scores"],
            changed_diagnostics["candidate_scores"],
        )
        self.assertEqual(
            diagnostics["evaluation_dates_excluded"], evaluation_count
        )

    def test_fused_validation_score_never_uses_later_validation_estimates(self):
        config = replace(
            self.config(),
            fused_penalties=(0.10, 1.00),
            evaluation_fraction=0.25,
            validation_fraction=0.20,
        )
        panel = self.panel()
        local, indices, _, _ = estimators.estimate_local_blocks(
            panel.estimation.predictors,
            panel.estimation.outcomes,
            panel.estimation.topology,
            window=config.window,
            ridge_multiplier=config.ridge_multiplier,
        )
        fit_panel = {
            "predictors": panel.estimation.predictors,
            "outcomes": panel.estimation.outcomes,
            "W": panel.estimation.topology,
        }
        _, diagnostics = estimators.select_fused_penalty(
            local, fit_panel, indices, config
        )
        first_validation = diagnostics["validation_positions"][0]
        perturbed = local.copy()
        perturbed[:, :, first_validation + 1] += 100.0
        _, changed = estimators.select_fused_penalty(
            perturbed, fit_panel, indices, config
        )
        for penalty in ("0.1", "1"):
            self.assertEqual(
                diagnostics["candidate_date_scores"][penalty][0],
                changed["candidate_date_scores"][penalty][0],
            )


if __name__ == "__main__":
    unittest.main()
