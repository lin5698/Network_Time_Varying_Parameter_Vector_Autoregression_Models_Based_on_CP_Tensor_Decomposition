import unittest
from dataclasses import replace

import numpy as np

from scripts.experiments import r006c_endpoint_protocol as protocol


class R006CEndpointProtocolTest(unittest.TestCase):
    @staticmethod
    def small_config():
        return protocol.R006CConfig(n=8, t_len=48, window=24, true_rank=8)

    def panel(self, **overrides):
        arguments = {
            "config": self.small_config(),
            "layer": "matched",
            "target_rho": 0.80,
            "approximation_target": 0.10,
            "separation_strength": 0.15,
            "seed": 240100,
        }
        arguments.update(overrides)
        return protocol.generate_endpoint_panel(**arguments)

    def test_full_grid_has_2160_rows(self):
        self.assertEqual(protocol.expected_row_count(), 2160)

    def test_each_candidate_has_sixteen_required_cells(self):
        self.assertEqual(len(protocol.required_cells()), 16)

    def test_named_streams_are_reproducible(self):
        first = protocol.spawn_named_streams(240100)
        second = protocol.spawn_named_streams(240100)
        self.assertEqual(tuple(first), protocol.STREAM_NAMES)
        for name in protocol.STREAM_NAMES:
            np.testing.assert_array_equal(
                first[name].normal(size=8), second[name].normal(size=8)
            )

    def test_named_streams_are_independent(self):
        streams = protocol.spawn_named_streams(240100)
        draws = [streams[name].normal(size=8) for name in protocol.STREAM_NAMES]
        self.assertEqual(len({draw.tobytes() for draw in draws}), 5)

    def test_method_seed_is_stable(self):
        key = (240100, "matched", 0.80, 0.10, 0.15, "anchor_split_cp3")
        self.assertEqual(protocol.method_seed(*key), protocol.method_seed(*key))

    def test_method_seed_is_key_sensitive(self):
        base = protocol.method_seed(
            240100, "matched", 0.80, 0.10, 0.15, "anchor_split_cp3"
        )
        changed = protocol.method_seed(
            240100, "matched", 0.80, 0.10, 0.15, "anchor_split_tucker333"
        )
        self.assertNotEqual(base, changed)

    def test_panel_has_exact_anchor_identity(self):
        panel = self.panel()
        anchored = panel.A + np.einsum(
            "tij,jk->tik", panel.B, panel.W_ref, optimize=True
        )
        np.testing.assert_allclose(
            anchored, panel.M_ref, atol=1e-10, rtol=0.0
        )

    def test_main_holdout_uses_declared_mixture(self):
        panel = self.panel()
        expected = protocol.row_normalize(
            0.75 * panel.W_ref + 0.25 * panel.W_holdout
        )
        np.testing.assert_array_equal(panel.W_alt_main, expected)

    def test_stress_topology_is_independent_of_main_holdout(self):
        panel = self.panel()
        self.assertFalse(np.array_equal(panel.W_alt_main, panel.W_alt_stress))
        np.testing.assert_allclose(panel.W_alt_stress.sum(axis=1), 1.0)

    def test_replacing_holdouts_preserves_all_fitting_inputs(self):
        panel = self.panel()
        rng = np.random.default_rng(91)
        holdout = protocol.row_normalize(rng.uniform(size=panel.W_ref.shape))
        main = protocol.row_normalize(0.75 * panel.W_ref + 0.25 * holdout)
        stress = protocol.row_normalize(rng.uniform(size=panel.W_ref.shape))
        changed = replace(
            panel,
            W_holdout=holdout,
            W_alt_main=main,
            W_alt_stress=stress,
        )
        self.assertEqual(panel.estimation.sha256(), changed.estimation.sha256())
        self.assertFalse(np.array_equal(panel.W_alt_main, changed.W_alt_main))
        self.assertFalse(np.array_equal(panel.W_alt_stress, changed.W_alt_stress))

    def test_fit_streams_do_not_change_across_rho(self):
        low = self.panel(target_rho=0.80)
        high = self.panel(target_rho=0.95)
        np.testing.assert_array_equal(
            low.estimation.predictors, high.estimation.predictors
        )
        np.testing.assert_array_equal(low.estimation.topology, high.estimation.topology)
        np.testing.assert_array_equal(low.W_ref, high.W_ref)
        np.testing.assert_array_equal(low.W_alt_main, high.W_alt_main)


if __name__ == "__main__":
    unittest.main()
