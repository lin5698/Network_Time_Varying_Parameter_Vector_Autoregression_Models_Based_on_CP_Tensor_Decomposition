import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts import run_cp_empirical_pipeline as pipeline


class CpAlsContractTest(unittest.TestCase):
    def test_exact_rank_one_tensor_is_reconstructed_to_machine_precision(self):
        a = np.array([1.25, -0.75, 2.0])
        b = np.array([0.4, -1.2])
        c = np.array([0.8, -0.3, 1.1, 0.5])
        tensor = np.einsum("i,j,k->ijk", a, b, c)

        factors, relative_loss = pipeline.cp_fit(
            tensor,
            rank=1,
            n_init=1,
            max_iter=100,
            tol=1e-12,
            seed=7,
        )
        reconstruction = pipeline.cp_reconstruct(factors)

        self.assertLess(relative_loss, 1e-10)
        np.testing.assert_allclose(reconstruction, tensor, rtol=1e-10, atol=1e-12)


class ChronologicalCpRankSelectionTest(unittest.TestCase):
    def test_each_validation_origin_fits_only_its_available_tensor_prefix(self):
        beta_tensor = np.arange(5, dtype=float).reshape(1, 1, 5)
        rolling_dates = [2, 3, 4, 5, 6]
        dates = list(pd.date_range("2020-01-01", periods=7, freq="QE"))
        y = np.zeros((7, 1), dtype=float)
        w_list = [np.eye(1) for _ in range(7)]
        fitted_prefix_lengths = []

        def fake_cp_fit(tensor, rank, **_kwargs):
            fitted_prefix_lengths.append(tensor.shape[2])
            return tensor.copy(), 0.0

        with patch.object(pipeline, "cp_fit", side_effect=fake_cp_fit), patch.object(
            pipeline, "cp_reconstruct", side_effect=lambda factors: factors
        ), patch.object(pipeline, "predict_one_step", return_value=np.zeros(1)):
            pipeline.select_cp_rank(
                beta_tensor,
                rolling_dates,
                dates,
                y,
                w_list,
                window=2,
                p=1,
                ranks=(1, 2),
                local_intercepts=np.zeros((5, 1)),
            )

        self.assertEqual(
            fitted_prefix_lengths[:-1],
            [2, 3, 4, 5, 2, 3, 4, 5],
        )

    def test_fitted_local_intercept_can_flip_rank_ordering(self):
        beta_tensor = np.zeros((1, 2, 2), dtype=float)
        rolling_dates = [2, 3]
        dates = list(pd.date_range("2020-01-01", periods=4, freq="QE"))
        y = np.array([[1.0], [1.0], [1.0], [0.4]])
        w_list = [np.zeros((1, 1)) for _ in range(4)]

        def fake_cp_fit(tensor, rank, **_kwargs):
            return (rank, tensor.shape), 0.0

        def fake_cp_reconstruct(factors):
            rank, shape = factors
            reconstruction = np.zeros(shape, dtype=float)
            if rank == 2:
                reconstruction[:, 0, :] = 1.0
            return reconstruction

        with patch.object(pipeline, "cp_fit", side_effect=fake_cp_fit), patch.object(
            pipeline, "cp_reconstruct", side_effect=fake_cp_reconstruct
        ):
            chosen_with_intercept, losses_with_intercept, *_ = pipeline.select_cp_rank(
                beta_tensor,
                rolling_dates,
                dates,
                y,
                w_list,
                window=2,
                p=1,
                ranks=(1, 2),
                local_intercepts=np.array([[0.0], [-0.6]]),
            )
            chosen_with_zero, losses_with_zero, *_ = pipeline.select_cp_rank(
                beta_tensor,
                rolling_dates,
                dates,
                y,
                w_list,
                window=2,
                p=1,
                ranks=(1, 2),
                local_intercepts=np.zeros((2, 1)),
            )

        self.assertEqual(chosen_with_intercept, 2)
        self.assertLess(losses_with_intercept[2], losses_with_intercept[1])
        self.assertEqual(chosen_with_zero, 1)
        self.assertLess(losses_with_zero[1], losses_with_zero[2])


if __name__ == "__main__":
    unittest.main()
