import numpy as np
import unittest

from scripts.natcs_weak_separation import (
    residualized_network_stats,
    spectral_condition_number,
)
from scripts.natcs_design_contract import equationwise_ridge_fit, lagged_network_exposure


class NatcsTheoryContractTests(unittest.TestCase):
    def test_finite_basis_two_hop_negative_and_full_rank_fixtures(self):
        w0 = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        wq = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]])
        e1 = np.array([1.0, 0.0, 0.0])
        x0 = np.column_stack([e1, w0[0], (w0 @ w0)[0]])
        xq = np.column_stack([e1, wq[0], (wq @ wq)[0]])
        quadratic_direction = np.array([0.0, 0.0, 1.0])

        np.testing.assert_allclose(x0 @ quadratic_direction, np.zeros(3))
        self.assertFalse(np.allclose(xq @ quadratic_direction, np.zeros(3)))

        cycle = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
        cycle2 = cycle @ cycle
        for i in range(3):
            design = np.column_stack([np.eye(3)[i], cycle[i], cycle2[i]])
            self.assertEqual(np.linalg.matrix_rank(design), 3)

    def test_two_hop_family_is_strictly_larger_at_directed_cycle(self):
        cycle = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
        cycle2 = cycle @ cycle
        for i in range(3):
            one_hop_rows = np.column_stack([np.eye(3)[i], cycle[i]])
            coefficients, *_ = np.linalg.lstsq(one_hop_rows, cycle2[i], rcond=None)
            residual = cycle2[i] - one_hop_rows @ coefficients
            self.assertGreater(np.linalg.norm(residual), 0.9)

    def test_exact_single_topology_factorization_counterexample(self):
        w0 = np.array([[2.0]])
        w1 = np.array([[3.0]])

        a0 = np.zeros((1, 1))
        b0 = np.zeros((1, 1))
        a1 = -w0
        b1 = np.eye(1)

        np.testing.assert_allclose(a0 + b0 @ w0, a1 + b1 @ w0)
        self.assertFalse(np.allclose(a0 + b0 @ w1, a1 + b1 @ w1))

    def test_diagonal_structured_inverse_and_zero_row_boundary(self):
        w0 = np.array([[0.0, 2.0], [0.0, 0.0]])
        a = np.array([3.0, 5.0])
        b = np.array([7.0, 11.0])
        d = np.diag(a) + np.diag(b) @ w0

        recovered_a = np.diag(d)
        recovered_b0 = d[0, 1] * w0[0, 1] / np.dot(w0[0, 1:], w0[0, 1:])
        np.testing.assert_allclose(recovered_a, a)
        self.assertAlmostEqual(recovered_b0, b[0])

        w1_same_zero_row = np.array([[0.0, 1.0], [0.0, 0.0]])
        q_first = np.diag(a) + np.diag(b) @ w1_same_zero_row
        b_alternative = b.copy()
        b_alternative[1] = -4.0
        q_second = np.diag(a) + np.diag(b_alternative) @ w1_same_zero_row
        np.testing.assert_allclose(q_first, q_second)

        w1_nonzero_queried_row = np.array([[0.0, 1.0], [1.0, 0.0]])
        q_first = np.diag(a) + np.diag(b) @ w1_nonzero_queried_row
        q_second = np.diag(a) + np.diag(b_alternative) @ w1_nonzero_queried_row
        self.assertFalse(np.allclose(q_first, q_second))

    def test_direct_only_is_identified_in_diagonal_zero_diagonal_class(self):
        w0 = np.array([[0.0, 1.0], [2.0, 0.0]])
        a = np.array([1.5, -0.5])
        b = np.array([2.0, 4.0])
        d = np.diag(a) + np.diag(b) @ w0
        np.testing.assert_allclose(np.diag(np.diag(d)), np.diag(a))

    def test_joint_ridge_schur_complement_matches_full_solution(self):
        rng = np.random.default_rng(20260718)
        x = rng.normal(size=(9, 3))
        z = rng.normal(size=(9, 2))
        y = rng.normal(size=9)
        lam = 0.7

        design = np.column_stack([x, z])
        full = np.linalg.solve(
            design.T @ design + lam * np.eye(design.shape[1]),
            design.T @ y,
        )

        m_x_lam = np.eye(x.shape[0]) - x @ np.linalg.solve(
            x.T @ x + lam * np.eye(x.shape[1]),
            x.T,
        )
        b_schur = np.linalg.solve(
            z.T @ m_x_lam @ z + lam * np.eye(z.shape[1]),
            z.T @ m_x_lam @ y,
        )

        np.testing.assert_allclose(b_schur, full[x.shape[1] :], rtol=1e-12, atol=1e-12)

    def test_ordinary_residualized_ridge_is_not_joint_ridge(self):
        x = np.ones((1, 1))
        z = np.ones((1, 1))
        y = np.ones(1)
        lam = 1.0

        ordinary_residual_maker = np.zeros((1, 1))
        residualized_only = np.linalg.solve(
            z.T @ ordinary_residual_maker @ z + lam * np.eye(1),
            z.T @ ordinary_residual_maker @ y,
        )
        design = np.column_stack([x, z])
        joint = np.linalg.solve(
            design.T @ design + lam * np.eye(2),
            design.T @ y,
        )

        np.testing.assert_allclose(residualized_only, np.array([0.0]))
        np.testing.assert_allclose(joint, np.array([1.0 / 3.0, 1.0 / 3.0]))

    def test_spectral_companion_block_bound(self):
        rng = np.random.default_rng(23)
        blocks = [rng.normal(size=(3, 3)) for _ in range(3)]
        top_row = np.hstack(blocks)
        companion_difference = np.vstack([top_row, np.zeros((6, 9))])

        lhs = np.linalg.norm(companion_difference, ord=2)
        rhs = np.sqrt(sum(np.linalg.norm(block, ord=2) ** 2 for block in blocks))
        self.assertLessEqual(lhs, rhs + 1e-12)

    def test_finite_telescoping_identity(self):
        rng = np.random.default_rng(41)
        c = rng.normal(scale=0.1, size=(4, 4))
        c_hat = c + rng.normal(scale=0.01, size=(4, 4))
        h = 5

        telescoped = sum(
            np.linalg.matrix_power(c_hat, r)
            @ (c_hat - c)
            @ np.linalg.matrix_power(c, h - 1 - r)
            for r in range(h)
        )
        direct = np.linalg.matrix_power(c_hat, h) - np.linalg.matrix_power(c, h)
        np.testing.assert_allclose(telescoped, direct, rtol=1e-12, atol=1e-12)

    def test_production_lagged_exposure_uses_historical_topology(self):
        y = np.array([[1.0, 2.0], [9.0, 8.0]])
        w_history = np.array([[0.0, 2.0], [3.0, 0.0]])
        w_report = np.zeros((2, 2))
        exposure = lagged_network_exposure([w_history, w_report], y, tau=1, lag=1)
        np.testing.assert_allclose(exposure, np.array([4.0, 3.0]))

    def test_production_estimator_returns_diagonal_blocks(self):
        rng = np.random.default_rng(118)
        y = rng.normal(size=(8, 3))
        w_list = [rng.normal(size=(3, 3)) for _ in range(8)]
        _, a_list, b_list, _, _, _ = equationwise_ridge_fit(
            y,
            w_list,
            p=2,
            lambda_ridge=0.1,
        )
        for block in [*a_list, *b_list]:
            np.testing.assert_allclose(block, np.diag(np.diag(block)))

    def test_rank_deficient_condition_number_is_infinite(self):
        x_aug = np.ones((4, 1))
        z = np.array([[1.0, 1.0], [-1.0, -1.0], [2.0, 2.0], [-2.0, -2.0]])
        stats = residualized_network_stats(x_aug, z)
        self.assertEqual(stats["rank"], 1)
        self.assertTrue(np.isinf(stats["condition"]))
        self.assertEqual(stats["weak_flag"], 1)

    def test_zero_residualized_design_is_not_condition_zero(self):
        x_aug = np.column_stack([np.ones(4), np.arange(4, dtype=float)])
        z = x_aug @ np.array([[2.0], [3.0]])
        stats = residualized_network_stats(x_aug, z)
        self.assertEqual(stats["rank"], 0)
        self.assertTrue(np.isinf(stats["condition"]))

    def test_full_rank_spectral_condition_number(self):
        self.assertAlmostEqual(
            spectral_condition_number(2.0, 8.0, rank=2, dimension=2),
            4.0,
        )

    def test_rank_diagnostic_is_scaled_by_residualized_design(self):
        x_aug = np.ones((4, 1))
        z = 1e12 * x_aug + np.array([[1.0], [-1.0], [1.0], [-1.0]])
        stats = residualized_network_stats(x_aug, z)

        self.assertEqual(stats["rank"], 1)
        self.assertTrue(np.isfinite(stats["condition"]))
        self.assertAlmostEqual(stats["condition"], 1.0)
        self.assertEqual(stats["weak_flag"], 0)

    def test_rank_deficiency_always_triggers_weak_flag(self):
        x_aug = np.ones((4, 1))
        z = np.column_stack(
            [
                np.array([1.0, -1.0, 1.0, -1.0]),
                np.array([1.0, -1.0, 1.0, -1.0]),
            ]
        )
        stats = residualized_network_stats(x_aug, z)

        self.assertLess(stats["rank"], z.shape[1])
        self.assertTrue(np.isinf(stats["condition"]))
        self.assertEqual(stats["weak_flag"], 1)


if __name__ == "__main__":
    unittest.main()
