import dataclasses
import unittest
from unittest import mock

import numpy as np

from scripts.experiments import r006c_endpoint_protocol as r006c
from scripts.experiments import r006e_native_protocol as p


class R006ENativeProtocolTest(unittest.TestCase):
    @staticmethod
    def fit_inputs(coefficient_dates):
        predictors = np.zeros((200, 3))
        return p.FitInputs(
            predictors=predictors,
            outcomes=np.ones_like(predictors),
            topology=np.zeros((200, 3, 3)),
            w_ref=np.eye(3),
            coefficient_dates=np.asarray(coefficient_dates),
        )

    def test_frozen_grid_and_regions(self):
        config = p.R006EConfig()
        self.assertEqual(config.n, 20)
        self.assertEqual(config.t_len, 200)
        self.assertEqual(config.window, 80)
        self.assertEqual(config.horizon, 8)
        self.assertEqual(p.SCREENING_SEEDS, tuple(range(240100, 240110)))
        self.assertEqual(p.CONFIRMATION_SEEDS, tuple(range(250100, 250130)))
        self.assertEqual(len(p.primary_cells()), 8)
        regions = p.chronological_regions(config)
        self.assertEqual(regions.calibration.tolist(), list(range(80, 140)))
        self.assertEqual(regions.validation.tolist(), list(range(140, 164)))
        self.assertEqual(regions.evaluation.tolist(), list(range(164, 200)))

    def test_named_streams_are_reproducible_and_distinct(self):
        left = p.spawn_named_streams(910001)
        right = p.spawn_named_streams(910001)
        self.assertEqual(tuple(left), p.STREAM_NAMES)
        a = [left[name].normal(size=16) for name in p.STREAM_NAMES]
        b = [right[name].normal(size=16) for name in p.STREAM_NAMES]
        for x, y in zip(a, b):
            np.testing.assert_array_equal(x, y)
        self.assertEqual(len({x.tobytes() for x in a}), len(a))

    def test_keyed_seed_is_stable_and_key_sensitive(self):
        key = (910002, 0.80, 0.10, 0.15, "family_endpoint")
        self.assertEqual(p.keyed_seed(*key), p.keyed_seed(*key))
        self.assertNotEqual(
            p.keyed_seed(*key),
            p.keyed_seed(910002, 0.80, 0.10, 0.15, "optimizer"),
        )

    def test_fit_inputs_have_no_truth_or_endpoint_fields(self):
        names = {field.name for field in dataclasses.fields(p.FitInputs)}
        self.assertEqual(
            names,
            {"predictors", "outcomes", "topology", "w_ref", "coefficient_dates"},
        )
        self.assertTrue(
            names.isdisjoint(
                {"truth", "m_ref", "b", "w_alt_interp", "w_alt_family"}
            )
        )

    def test_config_rejects_non_frozen_region_lengths(self):
        for overrides in (
            {"t_len": 199},
            {"window": 79},
            {"t_len": 119, "window": -1},
            {"n": 2, "true_rank": 8},
            {"fitted_rank": 8},
            {"sigma": 0.0},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    p.R006EConfig(**overrides)

    def test_config_rejects_float_and_boolean_integral_controls(self):
        integral_fields = (
            "n",
            "t_len",
            "window",
            "true_rank",
            "fitted_rank",
            "horizon",
            "optimizer_starts",
            "optimizer_iterations",
            "family_pool_size",
        )
        defaults = p.R006EConfig()
        for name in integral_fields:
            for value in (float(getattr(defaults, name)), True):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        p.R006EConfig(**{name: value})

    def test_config_normalizes_caller_owned_penalty_lists(self):
        fused = [0.10, 0.25]
        temporal = [0.0, 0.05]
        config = p.R006EConfig(
            fused_penalties=fused, temporal_penalties=temporal
        )

        fused.append(9.0)
        temporal[0] = 9.0
        self.assertEqual(config.fused_penalties, (0.10, 0.25))
        self.assertEqual(config.temporal_penalties, (0.0, 0.05))
        self.assertIsInstance(config.fused_penalties, tuple)
        self.assertIsInstance(config.temporal_penalties, tuple)

    def test_config_rejects_nonfinite_scalars_and_penalties(self):
        scalar_fields = (
            field.name
            for field in dataclasses.fields(p.R006EConfig)
            if field.name not in {"fused_penalties", "temporal_penalties"}
        )
        for name in scalar_fields:
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        p.R006EConfig(**{name: value})
        for name in ("fused_penalties", "temporal_penalties"):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(name=name, value=value):
                    with self.assertRaises(ValueError):
                        p.R006EConfig(**{name: [0.0, value]})

    def test_fit_inputs_accepts_planned_integer_dates(self):
        fit = self.fit_inputs(np.arange(80, 200, dtype=int))
        np.testing.assert_array_equal(fit.coefficient_dates, np.arange(80, 200))

    def test_fit_inputs_arrays_cannot_be_made_writeable_or_change_digest(self):
        fit = self.fit_inputs(np.arange(80, 200, dtype=int))
        arrays = (
            fit.predictors,
            fit.outcomes,
            fit.topology,
            fit.w_ref,
            fit.coefficient_dates,
        )
        original_bytes = tuple(value.tobytes() for value in arrays)
        original_digest = fit.sha256()

        for value in arrays:
            with self.assertRaises(ValueError):
                value.setflags(write=True)
            with self.assertRaises(ValueError):
                value.flat[0] = -1

        self.assertEqual(tuple(value.tobytes() for value in arrays), original_bytes)
        self.assertEqual(fit.sha256(), original_digest)

    def test_fit_inputs_rejects_invalid_coefficient_dates(self):
        invalid_dates = {
            "empty": [],
            "fractional": [80.0, 81.5],
            "nonfinite": [80.0, float("nan")],
            "duplicate": [80, 80, 81],
            "not_increasing": [81, 80],
            "unsigned_not_increasing": np.array([81, 80], dtype=np.uint64),
        }
        for label, dates in invalid_dates.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    self.fit_inputs(dates)

    def test_adapter_is_native_only_immutable_and_drops_stress_endpoint(self):
        config = p.R006EConfig()
        shape = (config.t_len, config.n)
        predictors = np.arange(np.prod(shape), dtype=float).reshape(shape)
        outcomes = predictors + 1.0
        topology = np.zeros((config.t_len, config.n, config.n))
        w_ref = np.eye(config.n)
        m_ref = np.ones((config.t_len, config.n, config.n))
        b = np.full_like(m_ref, 2.0)
        observed = np.full_like(m_ref, 3.0)
        interp = np.full((config.n, config.n), 4.0)
        stress = np.full((config.n, config.n), 99.0)
        endpoint = r006c.EndpointPanel(
            estimation=r006c.EstimationInputs(predictors, outcomes, topology, w_ref),
            A=np.zeros_like(m_ref),
            B=b,
            M_ref=m_ref,
            M_observed=observed,
            innovations=np.zeros(shape),
            W_ref=w_ref,
            W_holdout=np.zeros_like(w_ref),
            W_alt_main=interp,
            W_alt_stress=stress,
            a3_ratio=0.10,
            layer="native",
        )

        with mock.patch.object(
            r006c, "generate_endpoint_panel", return_value=endpoint
        ) as generate:
            panel = p.build_native_panel(
                config, rho=0.80, a3=0.10, eta=0.15, seed=910003
            )

        generate.assert_called_once()
        call = generate.call_args.kwargs
        self.assertEqual(call["layer"], "native")
        self.assertEqual(call["target_rho"], 0.80)
        self.assertEqual(call["approximation_target"], 0.10)
        self.assertEqual(call["separation_strength"], 0.15)
        self.assertEqual(call["seed"], 910003)
        self.assertFalse(hasattr(panel, "w_alt_stress"))
        self.assertFalse(any(value is stress for value in dataclasses.astuple(panel)))
        self.assertEqual(
            panel.endpoint_stream_seed,
            p.keyed_seed(910003, 0.80, 0.10, 0.15, "family_endpoint"),
        )

        returned_arrays = (
            panel.fit.predictors,
            panel.fit.outcomes,
            panel.fit.topology,
            panel.fit.w_ref,
            panel.fit.coefficient_dates,
            panel.truth.m_ref,
            panel.truth.b,
            panel.truth.observed_operator,
            panel.w_alt_interp,
        )
        self.assertTrue(all(not value.flags.writeable for value in returned_arrays))
        for value in returned_arrays:
            with self.assertRaises(ValueError):
                value.flat[0] = -1

        predictors.flat[0] = -10
        outcomes.flat[0] = -11
        topology.flat[0] = -12
        w_ref.flat[0] = -13
        m_ref.flat[0] = -14
        b.flat[0] = -15
        observed.flat[0] = -16
        interp.flat[0] = -17
        self.assertNotEqual(panel.fit.predictors.flat[0], -10)
        self.assertNotEqual(panel.fit.outcomes.flat[0], -11)
        self.assertNotEqual(panel.fit.topology.flat[0], -12)
        self.assertNotEqual(panel.fit.w_ref.flat[0], -13)
        self.assertNotEqual(panel.truth.m_ref.flat[0], -14)
        self.assertNotEqual(panel.truth.b.flat[0], -15)
        self.assertNotEqual(panel.truth.observed_operator.flat[0], -16)
        self.assertNotEqual(panel.w_alt_interp.flat[0], -17)

    def test_support_only_builder_matches_full_panel_without_truth_result(self):
        config = p.R006EConfig()
        kwargs = dict(rho=0.80, a3=0.10, eta=0.15, seed=240100)
        full = p.build_native_panel(config, **kwargs)
        construction = p.build_native_construction_inputs(config, **kwargs)
        self.assertEqual(
            {field.name for field in dataclasses.fields(construction)},
            {"fit", "w_alt_interp", "family_seed", "stream_metadata"},
        )
        self.assertFalse(hasattr(construction, "truth"))
        for name in ("predictors", "topology", "w_ref", "coefficient_dates"):
            np.testing.assert_array_equal(getattr(construction.fit, name), getattr(full.fit, name))
        np.testing.assert_array_equal(construction.fit.outcomes, 0.0)
        self.assertFalse(np.array_equal(construction.fit.outcomes, full.fit.outcomes))
        self.assertFalse(construction.fit.outcomes.flags.writeable)
        np.testing.assert_array_equal(construction.w_alt_interp, full.w_alt_interp)
        self.assertEqual(construction.family_seed, full.endpoint_stream_seed)
        self.assertNotEqual(construction.design_sha256(), full.fit.sha256())


if __name__ == "__main__":
    unittest.main()
