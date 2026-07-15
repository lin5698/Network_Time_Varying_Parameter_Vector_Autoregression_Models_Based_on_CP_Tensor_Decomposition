import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from scripts import run_cp_empirical_pipeline as pipeline


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
            )

        self.assertEqual(
            fitted_prefix_lengths[:-1],
            [2, 3, 4, 5, 2, 3, 4, 5],
        )


if __name__ == "__main__":
    unittest.main()
