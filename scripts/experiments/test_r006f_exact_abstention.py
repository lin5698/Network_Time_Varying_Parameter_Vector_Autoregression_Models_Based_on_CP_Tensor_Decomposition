import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import patch

import numpy as np

from scripts.experiments.r006f_exact_design import (
    build_exact_panel,
    generate_paired_worlds,
)
from scripts.experiments import r006f_exact_abstention as abstention


FIXTURE_SEEDS = (906001, 906002)


class R006FExactAbstentionTest(unittest.TestCase):
    def test_truncated_svd_retains_singular_value_on_relative_boundary(self):
        design = np.diag([1.0, 0.02])
        outcome = design @ np.array([[2.0], [-3.0]])

        solution = abstention.truncated_svd_solve(
            design, outcome, kappa_max=50.0, absolute_floor=1e-12
        )

        self.assertEqual(solution.retained_rank, 2)
        self.assertEqual(solution.tau, 0.02)
        np.testing.assert_allclose(solution.coefficient[:, 0], [2.0, -3.0])

    def test_truncated_svd_applies_absolute_floor(self):
        design = np.diag([1e-11, 5e-13])
        outcome = design @ np.array([[2.0], [-3.0]])

        solution = abstention.truncated_svd_solve(
            design, outcome, kappa_max=50.0, absolute_floor=1e-12
        )

        self.assertEqual(solution.retained_rank, 1)
        self.assertEqual(solution.tau, 1e-12)
        np.testing.assert_allclose(solution.coefficient[:, 0], [2.0, 0.0])

    def test_fwl_noiseless_fit_estimates_only_supported_slope_projection(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=FIXTURE_SEEDS[0], scale=1.0)
        truth = worlds.world1.b
        noiseless_y = (
            panel.x @ worlds.world1.m.T
            + panel.topology_exposure @ truth.T
        )

        fitted = abstention.fwl_min_norm_ols(
            panel.x, panel.topology_exposure, noiseless_y
        )

        np.testing.assert_allclose(
            fitted.slope,
            truth @ panel.analytic_projector,
            atol=1e-12,
        )
        self.assertGreater(
            np.linalg.norm(fitted.slope - truth, ord="fro"), 0.0
        )
        self.assertEqual(fitted.retained_rank, 2)
        self.assertAlmostEqual(fitted.tau, panel.tau, places=15)
        np.testing.assert_allclose(
            fitted.singular_values, panel.singular_values, atol=1e-14
        )

    def test_fwl_rejects_invalid_arrays_and_threshold_controls(self):
        x = np.eye(3)
        z = np.eye(3)
        y = np.ones((3, 2))
        invalid_arrays = (
            (x[None, :, :], z, y),
            (x, z[:, 0], y),
            (x, z, y[:, 0]),
            (x[:-1], z, y),
            (x, z[:-1], y),
            (np.where(x == 1.0, np.nan, x), z, y),
            (x, np.where(z == 1.0, np.inf, z), y),
            (x, z, np.full_like(y, np.nan)),
        )
        for invalid_x, invalid_z, invalid_y in invalid_arrays:
            with self.subTest(shapes=(invalid_x.shape, invalid_z.shape, invalid_y.shape)):
                with self.assertRaises(ValueError):
                    abstention.fwl_min_norm_ols(
                        invalid_x, invalid_z, invalid_y
                    )
        for invalid_kappa in (1.0, 0.0, -1.0, np.nan, np.inf):
            with self.subTest(kappa=invalid_kappa):
                with self.assertRaises(ValueError):
                    abstention.fwl_min_norm_ols(
                        x, z, y, kappa_max=invalid_kappa
                    )
        for invalid_floor in (0.0, -1.0, np.nan, np.inf):
            with self.subTest(floor=invalid_floor):
                with self.assertRaises(ValueError):
                    abstention.fwl_min_norm_ols(
                        x, z, y, absolute_floor=invalid_floor
                    )

    def test_query_result_rejects_contradictory_or_nonfinite_state(self):
        matrix = np.eye(2)
        invalid = (
            ("other", matrix, 0.0),
            ("available", None, 0.0),
            ("unsupported", matrix, 1.0),
            ("available", np.ones(2), 0.0),
            ("available", np.full((2, 2), np.nan), 0.0),
            ("available", np.full((2, 2), np.inf), 0.0),
            ("available", matrix, np.nan),
            ("available", matrix, np.inf),
            ("available", matrix, -1e-12),
        )
        for status, value, chi in invalid:
            with self.subTest(status=status, chi=chi):
                with self.assertRaises(ValueError):
                    abstention.QueryResult(status, value, chi)

        result = abstention.QueryResult("available", matrix, 0.0)
        self.assertFalse(result.matrix.flags.writeable)

    def test_certificate_evaluator_rejects_invalid_threshold(self):
        for threshold in (-1e-12, np.nan, np.inf):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    abstention.certificate_aware_evaluator(
                        np.eye(2), np.eye(2), 0.0, threshold
                    )

    def test_supported_query_is_available(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=FIXTURE_SEEDS[0], scale=1.0)
        fitted = abstention.fwl_min_norm_ols(
            panel.x, panel.topology_exposure, worlds.world0.y
        )

        result = abstention.certificate_aware_evaluator(
            fitted.slope,
            panel.delta_supported,
            panel.supported_chi,
        )

        self.assertEqual(result.status, "available")
        self.assertIsNotNone(result.matrix)
        self.assertEqual(result.matrix.shape, (6, 6))
        self.assertTrue(np.isfinite(result.matrix).all())

    def test_unsupported_query_abstains_without_a_matrix(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=FIXTURE_SEEDS[0], scale=1.0)
        fitted = abstention.fwl_min_norm_ols(
            panel.x, panel.topology_exposure, worlds.world0.y
        )

        result = abstention.certificate_aware_evaluator(
            fitted.slope,
            panel.delta_unsupported,
            panel.unsupported_chi,
        )

        self.assertEqual(result.status, "unsupported")
        self.assertIsNone(result.matrix)

    def test_fixture_classification_has_zero_false_support_or_abstention(self):
        false_support = 0
        false_abstention = 0
        for seed in FIXTURE_SEEDS:
            for scale in (1.0, 0.25):
                panel = build_exact_panel(scale=scale)
                worlds = generate_paired_worlds(seed=seed, scale=scale)
                fitted = abstention.fwl_min_norm_ols(
                    panel.x, panel.topology_exposure, worlds.world0.y
                )
                supported = abstention.certificate_aware_evaluator(
                    fitted.slope, panel.delta_supported, panel.supported_chi
                )
                unsupported = abstention.certificate_aware_evaluator(
                    fitted.slope,
                    panel.delta_unsupported,
                    panel.unsupported_chi,
                )
                false_abstention += supported.status != "available"
                false_support += unsupported.status != "unsupported"

        self.assertEqual(false_support, 0)
        self.assertEqual(false_abstention, 0)

    def test_silent_evaluator_forces_a_matrix_for_every_query_from_same_fit(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=FIXTURE_SEEDS[0], scale=1.0)
        fitted = abstention.fwl_min_norm_ols(
            panel.x, panel.topology_exposure, worlds.world0.y
        )

        for delta, chi in (
            (panel.delta_supported, panel.supported_chi),
            (panel.delta_unsupported, panel.unsupported_chi),
        ):
            with self.subTest(chi=chi):
                result = abstention.silent_evaluator(fitted.slope, delta, chi)
                self.assertEqual(result.status, "available")
                self.assertEqual(result.matrix.shape, (6, 6))
                self.assertTrue(np.isfinite(result.matrix).all())

    def test_oracle_supported_projection_is_an_independent_diagnostic(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=FIXTURE_SEEDS[0], scale=1.0)

        diagnostic = abstention.oracle_supported_projection(
            worlds.world1.b, panel.analytic_projector
        )

        np.testing.assert_allclose(
            diagnostic,
            worlds.world1.b @ panel.analytic_projector,
            atol=0.0,
        )
        self.assertFalse(diagnostic.flags.writeable)

    def test_silent_two_world_errors_obey_independent_half_gap_bound(self):
        for seed in FIXTURE_SEEDS:
            for scale in (1.0, 0.25):
                with self.subTest(seed=seed, scale=scale):
                    panel = build_exact_panel(scale=scale)
                    worlds = generate_paired_worlds(seed=seed, scale=scale)
                    fitted = abstention.fwl_min_norm_ols(
                        panel.x, panel.topology_exposure, worlds.world0.y
                    )
                    silent = abstention.silent_evaluator(
                        fitted.slope,
                        panel.delta_unsupported,
                        panel.unsupported_chi,
                    )
                    truth0 = worlds.world0.b @ panel.delta_unsupported
                    truth1 = worlds.world1.b @ panel.delta_unsupported
                    error0 = np.linalg.norm(
                        silent.matrix - truth0, ord="fro"
                    )
                    error1 = np.linalg.norm(
                        silent.matrix - truth1, ord="fro"
                    )
                    analytic_half_gap = 0.5 * np.linalg.norm(
                        (worlds.world1.b - worlds.world0.b)
                        @ panel.delta_unsupported,
                        ord="fro",
                    )

                    self.assertGreaterEqual(
                        max(error0, error1) + 1e-12,
                        analytic_half_gap,
                    )

    def test_supported_projection_decomposition_residual_is_negligible(self):
        for seed in FIXTURE_SEEDS:
            for scale in (1.0, 0.25):
                with self.subTest(seed=seed, scale=scale):
                    panel = build_exact_panel(scale=scale)
                    worlds = generate_paired_worlds(seed=seed, scale=scale)
                    residual = abstention.decomposition_residual(
                        worlds.world1.b,
                        panel.delta_unsupported,
                        panel.analytic_projector,
                    )
                    direct = worlds.world1.b @ panel.delta_unsupported
                    supported = (
                        worlds.world1.b
                        @ panel.analytic_projector
                        @ panel.delta_unsupported
                    )
                    unsupported = (
                        worlds.world1.b
                        @ (np.eye(6) - panel.analytic_projector)
                        @ panel.delta_unsupported
                    )
                    independent = np.linalg.norm(
                        direct - supported - unsupported, ord="fro"
                    )
                    self.assertAlmostEqual(
                        residual, independent, places=15
                    )
                    self.assertLessEqual(residual, 1e-10)

    def test_same_noise_excitation_obeys_approved_analytic_scaling(self):
        strong = build_exact_panel(scale=1.0)
        weak = build_exact_panel(scale=0.25)

        self.assertAlmostEqual(
            weak.supported_chi, strong.supported_chi, places=10
        )
        self.assertAlmostEqual(
            weak.unsupported_chi, strong.unsupported_chi, places=10
        )
        strong_nonzero = strong.singular_values[
            strong.singular_values >= strong.tau
        ]
        weak_nonzero = weak.singular_values[
            weak.singular_values >= weak.tau
        ]
        np.testing.assert_allclose(
            weak_nonzero,
            strong_nonzero / 4.0,
            rtol=1e-10,
            atol=1e-14,
        )
        strong_inverse = 1.0 / strong_nonzero[-1]
        weak_inverse = 1.0 / weak_nonzero[-1]
        self.assertAlmostEqual(
            weak_inverse, 4.0 * strong_inverse, places=10
        )

        for seed in FIXTURE_SEEDS:
            strong_worlds = generate_paired_worlds(seed=seed, scale=1.0)
            weak_worlds = generate_paired_worlds(seed=seed, scale=0.25)
            np.testing.assert_array_equal(
                strong_worlds.noise, weak_worlds.noise
            )
            strong_fit = abstention.fwl_min_norm_ols(
                strong.x,
                strong.topology_exposure,
                strong_worlds.world0.y,
            )
            weak_fit = abstention.fwl_min_norm_ols(
                weak.x,
                weak.topology_exposure,
                weak_worlds.world0.y,
            )
            strong_error = np.linalg.norm(
                (strong_fit.slope - strong_worlds.world0.b)
                @ strong.delta_supported,
                ord="fro",
            )
            weak_error = np.linalg.norm(
                (weak_fit.slope - weak_worlds.world0.b)
                @ weak.delta_supported,
                ord="fro",
            )
            self.assertLessEqual(
                abs(weak_error - 4.0 * strong_error), 1e-8
            )

    def test_run_pair_returns_a_frozen_read_only_result(self):
        result = abstention.run_pair(seed=FIXTURE_SEEDS[0], scale=1.0)

        self.assertEqual((result.seed, result.scale), (906001, 1.0))
        self.assertEqual(result.supported.status, "available")
        self.assertEqual(result.unsupported.status, "unsupported")
        self.assertIsNone(result.unsupported.matrix)
        self.assertEqual(result.silent_unsupported.status, "available")
        self.assertEqual(result.retained_rank, 2)
        self.assertAlmostEqual(result.tau, result.panel.tau, places=15)
        self.assertGreater(result.analytic_gap_norm, 0.0)
        self.assertLessEqual(result.decomposition_residual, 1e-10)
        with self.assertRaises(FrozenInstanceError):
            result.seed = 0
        for array in (
            result.fitted_slope,
            result.oracle_world0,
            result.oracle_world1,
            result.retained_singular_values,
            result.supported.matrix,
            result.silent_unsupported.matrix,
        ):
            self.assertFalse(array.flags.writeable)
            with self.assertRaises(ValueError):
                array.flat[0] = array.flat[0]

    def test_run_pair_reuses_the_exact_panel_carried_by_paired_worlds(self):
        worlds = generate_paired_worlds(seed=FIXTURE_SEEDS[0], scale=1.0)
        with patch.object(
            abstention, "generate_paired_worlds", return_value=worlds
        ) as generator:
            result = abstention.run_pair(seed=FIXTURE_SEEDS[0], scale=1.0)

        generator.assert_called_once_with(seed=FIXTURE_SEEDS[0], scale=1.0)
        self.assertIs(result.panel, worlds.panel)


if __name__ == "__main__":
    unittest.main()
