import inspect
import unittest

import numpy as np

from scripts.experiments import r006d_endpoint_support as support


class R006DEndpointSupportTest(unittest.TestCase):
    def test_chronological_regions_cover_post_warmup_dates_without_overlap(self):
        regions = support.chronological_regions(
            t_len=200,
            window=80,
            validation_fraction=0.20,
            evaluation_fraction=0.30,
        )
        self.assertEqual(len(regions.calibration), 60)
        self.assertEqual(len(regions.validation), 24)
        self.assertEqual(len(regions.evaluation), 36)
        self.assertEqual(regions.calibration[[0, -1]].tolist(), [80, 139])
        self.assertEqual(regions.validation[[0, -1]].tolist(), [140, 163])
        self.assertEqual(regions.evaluation[[0, -1]].tolist(), [164, 199])
        joined = np.concatenate(
            [regions.calibration, regions.validation, regions.evaluation]
        )
        np.testing.assert_array_equal(joined, np.arange(80, 200))
        self.assertEqual(len(np.unique(joined)), len(joined))

    def test_chronological_regions_reject_empty_calibration(self):
        with self.assertRaisesRegex(ValueError, "calibration"):
            support.chronological_regions(
                t_len=100,
                window=80,
                validation_fraction=0.50,
                evaluation_fraction=0.50,
            )

    def test_certificate_is_scale_invariant_and_separates_query_directions(self):
        x = np.column_stack(
            [np.ones(8), np.linspace(-1.0, 1.0, 8), np.arange(8) ** 2]
        )
        z = np.column_stack(
            [np.array([1.0, -1.0] * 4), np.zeros(8), np.zeros(8)]
        )
        supported_delta = np.diag([1.0, 0.0, 0.0])
        unsupported_delta = np.diag([0.0, 1.0, 0.0])

        supported = support.certificate_from_design(
            x, z, supported_delta, kappa_max=50.0
        )
        rescaled = support.certificate_from_design(
            x, 17.0 * z, supported_delta, kappa_max=50.0
        )
        unsupported = support.certificate_from_design(
            x, z, unsupported_delta, kappa_max=50.0
        )

        self.assertLess(supported.chi, 1e-12)
        self.assertAlmostEqual(supported.chi, rescaled.chi, places=12)
        self.assertGreater(unsupported.chi, 0.999999)
        self.assertEqual(supported.retained_rank, 1)

    def test_certificate_decomposition_is_exact(self):
        rng = np.random.default_rng(606_004)
        x = rng.normal(size=(16, 4))
        z = rng.normal(size=(16, 4))
        delta = rng.normal(size=(4, 4))
        b = rng.normal(size=4)
        certificate = support.certificate_from_design(x, z, delta)
        left = delta.T @ b
        right = (
            delta.T @ certificate.projector @ b
            + delta.T @ (np.eye(4) - certificate.projector) @ b
        )
        np.testing.assert_allclose(left, right, atol=1e-12, rtol=0.0)

    def test_selectors_use_frozen_thresholds_and_deterministic_ties(self):
        supported = support.select_supported_index(
            [0.08, 0.10, 0.04], threshold=0.10
        )
        unsupported = support.select_unsupported_index(
            median_chi=[0.10, 0.25, 0.25],
            maximum_chi=[0.40, 0.36, 0.50],
            median_threshold=0.20,
            maximum_threshold=0.35,
        )
        self.assertEqual(supported, 0)
        self.assertEqual(unsupported, 2)
        self.assertIsNone(
            support.select_unsupported_index(
                median_chi=[0.10],
                maximum_chi=[0.34],
                median_threshold=0.20,
                maximum_threshold=0.35,
            )
        )

    def test_support_apis_cannot_receive_response_targets_or_truth(self):
        for function in (
            support.support_path,
            support.select_supported_index,
            support.select_unsupported_index,
        ):
            parameters = inspect.signature(function).parameters
            self.assertNotIn("outcomes", parameters)
            self.assertNotIn("truth", parameters)
            self.assertNotIn("endpoint_error", parameters)

    def test_candidate_pools_are_reproducible_normalized_and_distinct(self):
        first_family = support.generate_family_pool(
            n=20, size=64, seed=606_005
        )
        second_family = support.generate_family_pool(
            n=20, size=64, seed=606_005
        )
        out_pool = support.generate_unsupported_pool(
            n=20, size=64, seed=606_006
        )

        np.testing.assert_array_equal(first_family, second_family)
        self.assertEqual(first_family.shape, (64, 20, 20))
        self.assertEqual(out_pool.shape, (64, 20, 20))
        for pool in (first_family, out_pool):
            np.testing.assert_allclose(pool.sum(axis=2), 1.0, atol=1e-12)
            np.testing.assert_array_equal(
                np.diagonal(pool, axis1=1, axis2=2), np.zeros((64, 20))
            )
            self.assertEqual(len({candidate.tobytes() for candidate in pool}), 64)

    def test_family_pool_requires_four_equal_communities(self):
        with self.assertRaisesRegex(ValueError, "divisible by four"):
            support.generate_family_pool(n=10, size=4, seed=1)

    def test_cached_design_path_matches_direct_query_evaluation(self):
        rng = np.random.default_rng(606_007)
        predictors = rng.normal(size=(40, 4))
        topology = rng.uniform(size=(40, 4, 4))
        topology /= topology.sum(axis=2, keepdims=True)
        w_ref = np.eye(4) / 2.0
        w_star = np.roll(w_ref, 1, axis=1)
        dates = np.arange(20, 28)

        direct = support.support_path(
            predictors,
            topology,
            w_ref,
            w_star,
            dates,
            window=20,
        )
        design_path = support.build_design_support_path(
            predictors,
            topology,
            w_ref,
            dates,
            window=20,
        )
        cached = support.evaluate_query_path(design_path, w_ref, w_star)

        np.testing.assert_allclose(direct.chi, cached.chi, atol=1e-12)
        np.testing.assert_allclose(direct.tau, cached.tau, atol=0.0)
        np.testing.assert_array_equal(
            direct.retained_rank, cached.retained_rank
        )

    def test_pool_evaluation_keeps_every_candidate_certificate(self):
        rng = np.random.default_rng(606_008)
        predictors = rng.normal(size=(36, 4))
        topology = rng.uniform(size=(36, 4, 4))
        topology /= topology.sum(axis=2, keepdims=True)
        w_ref = np.eye(4) / 2.0
        candidates = np.stack(
            [np.roll(w_ref, shift, axis=1) for shift in (1, 2, 3)]
        )
        design_path = support.build_design_support_path(
            predictors,
            topology,
            w_ref,
            np.arange(20, 24),
            window=20,
        )
        paths = support.evaluate_candidate_pool(
            design_path, w_ref, candidates
        )
        self.assertEqual(len(paths), 3)
        self.assertEqual([len(path.chi) for path in paths], [4, 4, 4])


if __name__ == "__main__":
    unittest.main()
