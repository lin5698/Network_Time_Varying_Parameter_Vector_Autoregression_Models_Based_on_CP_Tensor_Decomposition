import inspect
import itertools
import unittest
from dataclasses import FrozenInstanceError

import numpy as np

from scripts.experiments.r006f_exact_design import (
    R006FConfig,
    build_exact_panel,
    generate_paired_worlds,
)


class R006FExactDesignTest(unittest.TestCase):
    def test_paired_worlds_share_observations_and_have_the_approved_truth_gaps(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=906001, scale=1.0)

        self.assertLessEqual(
            float(np.max(np.abs(worlds.world0.y - worlds.world1.y))),
            1e-12,
        )
        coefficient_gap = worlds.world1.b - worlds.world0.b
        supported_gap = coefficient_gap @ panel.delta_supported
        unsupported_gap = coefficient_gap @ panel.delta_unsupported
        expected = (
            panel.config.beta
            * panel.epsilon_star
            * np.outer(panel.node_basis[:, 0], panel.v2)
        )
        self.assertLessEqual(float(np.linalg.norm(supported_gap)), 1e-12)
        self.assertGreater(float(np.linalg.norm(unsupported_gap)), 0.0)
        relative_error = np.linalg.norm(unsupported_gap - expected) / np.linalg.norm(
            expected
        )
        self.assertLessEqual(float(relative_error), 1e-10)

    def test_fixture_seed_scale_pairs_pass_observation_and_truth_gates(self):
        config = R006FConfig()

        for scale, seed in itertools.product(
            config.excitation_scales, (906001, 906002)
        ):
            with self.subTest(scale=scale, seed=seed):
                panel = build_exact_panel(scale=scale)
                worlds = generate_paired_worlds(seed=seed, scale=scale)
                coefficient_gap = worlds.world1.b - worlds.world0.b
                supported_gap = coefficient_gap @ panel.delta_supported
                unsupported_gap = coefficient_gap @ panel.delta_unsupported
                expected = (
                    config.beta
                    * panel.epsilon_star
                    * np.outer(panel.node_basis[:, 0], panel.v2)
                )

                self.assertLessEqual(
                    float(np.max(np.abs(worlds.world0.y - worlds.world1.y))),
                    1e-12,
                )
                self.assertLessEqual(float(np.linalg.norm(supported_gap)), 1e-12)
                self.assertGreater(float(np.linalg.norm(unsupported_gap)), 0.0)
                relative_error = np.linalg.norm(
                    unsupported_gap - expected
                ) / np.linalg.norm(expected)
                self.assertLessEqual(float(relative_error), 1e-10)

    def test_paired_noise_is_seed_keyed_and_reproducible(self):
        first = generate_paired_worlds(seed=906001, scale=1.0)
        replay = generate_paired_worlds(seed=906001, scale=1.0)
        weak = generate_paired_worlds(seed=906001, scale=0.25)
        different = generate_paired_worlds(seed=906002, scale=1.0)

        np.testing.assert_array_equal(first.noise, replay.noise)
        np.testing.assert_array_equal(first.noise, weak.noise)
        np.testing.assert_array_equal(first.world0.y, replay.world0.y)
        self.assertFalse(np.array_equal(first.noise, different.noise))
        self.assertFalse(np.array_equal(first.world0.y, different.world0.y))

    def test_paired_worlds_follow_the_frozen_coefficients_and_dgp(self):
        panel = build_exact_panel(scale=1.0)
        worlds = generate_paired_worlds(seed=906001, scale=1.0)
        q0 = panel.node_basis[:, 0]
        expected_m = 0.20 * np.eye(6)
        expected_b0 = 0.15 * np.eye(6)
        expected_b1 = expected_b0 + 0.50 * np.outer(q0, panel.u_perp)
        expected_noise = np.random.default_rng(906001).normal(size=(96, 6))

        np.testing.assert_array_equal(worlds.world0.m, expected_m)
        np.testing.assert_array_equal(worlds.world1.m, expected_m)
        np.testing.assert_array_equal(worlds.world0.b, expected_b0)
        np.testing.assert_allclose(worlds.world1.b, expected_b1, atol=0.0)
        np.testing.assert_array_equal(worlds.noise, expected_noise)
        for world in (worlds.world0, worlds.world1):
            expected_y = (
                panel.x @ world.m.T
                + panel.topology_exposure @ world.b.T
                + 0.05 * expected_noise
            )
            np.testing.assert_array_equal(world.y, expected_y)

    def test_paired_world_dataclasses_are_frozen_read_only_and_unaliased(self):
        worlds = generate_paired_worlds(seed=906001, scale=1.0)

        with self.assertRaises(FrozenInstanceError):
            worlds.a = np.zeros(6)
        with self.assertRaises(FrozenInstanceError):
            worlds.world0.y = np.zeros((96, 6))

        arrays = {
            "noise": worlds.noise,
            "a": worlds.a,
            "analytic_unsupported_gap": worlds.analytic_unsupported_gap,
            "world0.m": worlds.world0.m,
            "world0.b": worlds.world0.b,
            "world0.y": worlds.world0.y,
            "world1.m": worlds.world1.m,
            "world1.b": worlds.world1.b,
            "world1.y": worlds.world1.y,
        }
        for name, value in arrays.items():
            with self.subTest(field=name):
                self.assertFalse(value.flags.writeable)
                with self.assertRaises(ValueError):
                    value.flat[0] = value.flat[0]
        for (left_name, left), (right_name, right) in itertools.combinations(
            arrays.items(), 2
        ):
            with self.subTest(left=left_name, right=right_name):
                self.assertFalse(np.shares_memory(left, right))

    def test_config_freezes_approved_protocol_constants(self):
        config = R006FConfig()

        self.assertEqual(config.n, 6)
        self.assertEqual(config.rank, 2)
        self.assertEqual(config.t_len, 96)
        self.assertEqual(config.seeds, tuple(range(620001, 620051)))
        self.assertEqual(config.excitation_scales, (1.0, 0.25))
        self.assertEqual(config.kappa_max, 50.0)
        self.assertEqual(config.classification_threshold, 0.05)
        self.assertEqual(
            (config.m_scale, config.b0_scale, config.beta, config.sigma),
            (0.20, 0.15, 0.50, 0.05),
        )

    def test_config_is_immutable(self):
        config = R006FConfig()

        with self.assertRaises(FrozenInstanceError):
            config.n = 7

    def test_exact_panel_topology_is_nonnegative_and_row_stochastic(self):
        panel = build_exact_panel(scale=1.0)

        self.assertEqual(panel.topology.shape, (96, 6, 6))
        self.assertGreaterEqual(float(panel.topology.min()), 0.0)
        self.assertLessEqual(
            float(abs(panel.topology.sum(axis=2) - 1.0).max()), 1e-12
        )

    def test_query_endpoints_are_nonnegative_and_row_stochastic(self):
        panel = build_exact_panel(scale=1.0)

        for name, delta in (
            ("supported", panel.delta_supported),
            ("unsupported", panel.delta_unsupported),
        ):
            with self.subTest(endpoint=name):
                endpoint = panel.w_ref + delta
                self.assertGreaterEqual(float(endpoint.min()), 0.0)
                self.assertLessEqual(
                    float(np.max(np.abs(endpoint.sum(axis=1) - 1.0))),
                    1e-12,
                )

    def test_exact_panel_has_rank_two_fwl_topology_exposure(self):
        panel = build_exact_panel(scale=1.0)
        q4 = panel.node_basis[:, 4]

        self.assertLessEqual(float(abs(panel.x @ q4 - 1.0).max()), 1e-12)
        self.assertEqual(panel.direct_exposure.shape, (96, 6))
        self.assertEqual(panel.topology_exposure.shape, (96, 6))
        self.assertEqual(
            np.linalg.matrix_rank(panel.z_tilde, tol=1e-12), 2
        )

    def test_exact_and_svd_projectors_classify_fixed_queries(self):
        panel = build_exact_panel(scale=1.0)
        expected = panel.u @ panel.u.T

        np.testing.assert_allclose(
            panel.analytic_projector, expected, atol=1e-14
        )
        self.assertLessEqual(
            np.linalg.norm(panel.svd_projector - panel.analytic_projector),
            1e-10,
        )
        self.assertLessEqual(panel.supported_chi, 1e-10)
        self.assertGreaterEqual(panel.unsupported_chi, 1.0 - 1e-10)

    def test_weak_excitation_scales_singular_values_but_not_queries_or_chi(self):
        strong = build_exact_panel(scale=1.0)
        weak = build_exact_panel(scale=0.25)

        np.testing.assert_allclose(
            weak.singular_values[:2],
            strong.singular_values[:2] / 4.0,
            rtol=1e-10,
            atol=1e-14,
        )
        np.testing.assert_array_equal(
            weak.delta_supported, strong.delta_supported
        )
        np.testing.assert_array_equal(
            weak.delta_unsupported, strong.delta_unsupported
        )
        self.assertAlmostEqual(
            weak.supported_chi, strong.supported_chi, places=10
        )
        self.assertAlmostEqual(
            weak.unsupported_chi, strong.unsupported_chi, places=10
        )

    def test_panel_is_frozen_and_scale_is_validated(self):
        panel = build_exact_panel(scale=1.0)

        with self.assertRaises(FrozenInstanceError):
            panel.scale = 0.25
        for invalid in (0.5, 0.0, -1.0):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    build_exact_panel(scale=invalid)
        for invalid in (True, "1.0", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    build_exact_panel(scale=invalid)

    def test_construction_does_not_call_a_nonlinear_row_normalizer(self):
        source = inspect.getsource(
            __import__(
                "scripts.experiments.r006f_exact_design", fromlist=["*"]
            )
        )

        self.assertNotRegex(source, r"\b(?:row_)?normalize\s*\(")

    def test_panel_arrays_are_independent_read_only_defensive_copies(self):
        panel = build_exact_panel(scale=1.0)
        arrays = {
            name: value
            for name, value in vars(panel).items()
            if isinstance(value, np.ndarray)
        }

        self.assertTrue(arrays)
        for name, value in arrays.items():
            with self.subTest(field=name):
                self.assertFalse(value.flags.writeable)
                with self.assertRaises(ValueError):
                    value.flat[0] = value.flat[0]
        for (left_name, left), (right_name, right) in itertools.combinations(
            arrays.items(), 2
        ):
            with self.subTest(left=left_name, right=right_name):
                self.assertFalse(np.shares_memory(left, right))
        self.assertFalse(np.shares_memory(panel.x, panel.direct_exposure))

    def test_node_and_time_bases_follow_the_fixed_dct_ii_convention(self):
        panel = build_exact_panel(scale=1.0)
        node_positions = np.arange(6, dtype=float) + 0.5
        expected_q1 = np.sqrt(2.0 / 6.0) * np.cos(
            np.pi * node_positions / 6.0
        )
        expected_q5 = np.sqrt(2.0 / 6.0) * np.cos(
            5.0 * np.pi * node_positions / 6.0
        )

        np.testing.assert_allclose(
            panel.node_basis.T @ panel.node_basis, np.eye(6), atol=1e-14
        )
        np.testing.assert_allclose(
            panel.node_basis[:, 0], np.ones(6) / np.sqrt(6.0), atol=1e-14
        )
        self.assertTrue(np.all(panel.node_basis[:, 0] > 0.0))
        np.testing.assert_allclose(
            panel.node_basis[:, 1], expected_q1, atol=1e-14
        )
        np.testing.assert_allclose(
            panel.node_basis[:, 5], expected_q5, atol=1e-14
        )
        self.assertGreater(panel.node_basis[0, 1], 0.0)
        self.assertLess(panel.node_basis[-1, 1], 0.0)
        self.assertGreater(panel.node_basis[0, 5], 0.0)
        self.assertLess(panel.node_basis[-1, 5], 0.0)

        time_positions = np.arange(96, dtype=float) + 0.5
        frequencies = np.arange(1, 8, dtype=float)
        expected_f = np.sqrt(2.0 / 96.0) * np.cos(
            np.pi
            * time_positions[:, None]
            * frequencies[None, :]
            / 96.0
        )
        np.testing.assert_allclose(
            panel.time_basis[:, 1:8], expected_f, atol=1e-14
        )

    def test_scale_accepts_real_scalars_and_rejects_other_values(self):
        self.assertEqual(build_exact_panel(np.float32(0.25)).scale, 0.25)
        self.assertEqual(build_exact_panel(np.int64(1)).scale, 1.0)

        for invalid in (True, False, "0.25", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    build_exact_panel(invalid)
        for invalid in (np.nan, np.inf, -np.inf, 0.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    build_exact_panel(invalid)


if __name__ == "__main__":
    unittest.main()
