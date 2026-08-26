import dataclasses
import inspect
import json
import unittest

import numpy as np

from scripts.experiments.r006e_native_protocol import (
    FitInputs,
    R006EConfig,
    TruthBundle,
)
from scripts.experiments.r006e_native_estimators import (
    FittedPath,
    fit_bundle_digest,
    fit_path_digest,
    fit_required_comparators,
)


def fixed_fit_inputs() -> FitInputs:
    rng = np.random.default_rng(910401)
    predictors = rng.normal(size=(200, 4))
    topology = rng.normal(scale=0.05, size=(200, 4, 4))
    topology += np.eye(4)[None, :, :]
    outcomes = 0.2 * predictors + rng.normal(scale=0.01, size=(200, 4))
    return FitInputs(
        predictors=predictors,
        outcomes=outcomes,
        topology=topology,
        w_ref=np.eye(4),
        coefficient_dates=np.arange(80, 200, dtype=int),
    )


def toy_config() -> R006EConfig:
    return R006EConfig(n=4, true_rank=4, fitted_rank=3)


class R006ETruthIsolationTest(unittest.TestCase):
    def test_promotion_fit_signature_has_only_fit_config_and_method_seed(self):
        signature = inspect.signature(fit_required_comparators)
        names = tuple(signature.parameters)
        self.assertEqual(names, ("fit", "config", "method_seed"))
        self.assertEqual(
            signature.parameters["fit"].kind,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        for name in ("config", "method_seed"):
            self.assertEqual(
                signature.parameters[name].kind,
                inspect.Parameter.KEYWORD_ONLY,
            )
        self.assertTrue(
            set(names).isdisjoint(
                {"truth", "b_true", "m_ref_true", "w_alt_interp", "w_alt_family"}
            )
        )
        with self.assertRaises(TypeError):
            fit_required_comparators(fixed_fit_inputs(), toy_config(), 91)

    def test_fitted_path_is_defensively_immutable(self):
        tensor = np.arange(24.0).reshape(2, 3, 4)
        dates = np.arange(4)
        diagnostics = {
            "status": "success",
            "nested": {"values": [1, 2]},
            "ok": True,
        }
        path = FittedPath(
            method="toy",
            parameterization="anchor",
            tensor=tensor,
            dates=dates,
            selected_penalty=0.1,
            diagnostics=diagnostics,
            runtime_seconds=0.5,
        )

        tensor[0, 0, 0] = -1
        dates[0] = -1
        diagnostics["nested"]["values"][0] = -1
        self.assertEqual(path.tensor[0, 0, 0], 0.0)
        self.assertEqual(path.dates[0], 0)
        self.assertEqual(path.diagnostics["nested"]["values"], (1, 2))
        self.assertFalse(path.tensor.flags.writeable)
        self.assertFalse(path.dates.flags.writeable)
        with self.assertRaises(ValueError):
            path.tensor[0, 0, 0] = 9
        with self.assertRaises(ValueError):
            path.tensor.setflags(write=True)
        with self.assertRaises(ValueError):
            path.dates.setflags(write=True)
        with self.assertRaises(TypeError):
            path.diagnostics["new"] = 9
        with self.assertRaises(TypeError):
            path.diagnostics["nested"]["new"] = 9
        with self.assertRaises(TypeError):
            dict.__setitem__(path.diagnostics, "new", 9)
        with self.assertRaises(TypeError):
            dict.__setitem__(path.diagnostics["nested"], "new", 9)
        digest = fit_path_digest(path)
        snapshot = path.diagnostics.to_json_dict()
        snapshot["nested"]["values"][0] = -100
        snapshot["new"] = 9
        self.assertEqual(path.diagnostics.to_json_dict()["nested"]["values"], [1, 2])
        self.assertEqual(fit_path_digest(path), digest)
        self.assertEqual(
            json.loads(json.dumps(path.diagnostics.to_json_dict())),
            {
                "status": "success",
                "nested": {"values": [1, 2]},
                "ok": True,
            },
        )
        self.assertEqual(path.status, "success")
        self.assertTrue(path.is_success)
        self.assertIs(path.require_success(), path)

    def test_fitted_path_validates_scientific_content_and_runtime(self):
        base = dict(
            method="toy",
            parameterization="anchor",
            tensor=np.zeros((2, 4, 3)),
            dates=np.arange(3),
            selected_penalty=None,
            diagnostics={"status": "success", "ok": True},
            runtime_seconds=0.0,
        )
        for changes in (
            {"method": ""},
            {"tensor": np.zeros((2, 4))},
            {"tensor": np.full((2, 4, 3), np.nan)},
            {"tensor": np.zeros((2, 4, 0)), "dates": np.array([], dtype=int)},
            {"dates": np.array([0, 2])},
            {"dates": np.array([0.0, 1.5, 2.0])},
            {"selected_penalty": -0.1},
            {"selected_penalty": float("inf")},
            {"diagnostics": {"bad": np.array([1])}},
            {"diagnostics": {"status": "unknown"}},
            {"diagnostics": {"status": "failure", "error_type": "X"}},
            {"runtime_seconds": -0.1},
            {"runtime_seconds": float("nan")},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises((TypeError, ValueError)):
                    FittedPath(**(base | changes))

    def test_digest_is_canonical_and_excludes_runtime(self):
        kwargs = dict(
            method="toy",
            parameterization="anchor",
            tensor=np.arange(24.0).reshape(2, 4, 3),
            dates=np.arange(3),
            selected_penalty=0.25,
            diagnostics={
                "status": "success",
                "z": [2, 3],
                "a": {"finite": 1.5},
            },
        )
        first = FittedPath(**kwargs, runtime_seconds=0.0)
        second = FittedPath(
            **(
                kwargs
                | {
                    "diagnostics": {
                        "a": {"finite": 1.5},
                        "z": [2, 3],
                        "status": "success",
                    }
                }
            ),
            runtime_seconds=99.0,
        )
        self.assertEqual(fit_path_digest(first), fit_path_digest(second))
        self.assertEqual(
            fit_bundle_digest({"toy": first}),
            fit_bundle_digest({"toy": second}),
        )

        changed = dataclasses.replace(first, parameterization="different")
        self.assertNotEqual(fit_path_digest(first), fit_path_digest(changed))

    def test_digest_excludes_only_nested_runtime_seconds_metadata(self):
        common = dict(
            method="toy",
            parameterization="anchor",
            tensor=np.arange(24.0).reshape(2, 4, 3),
            dates=np.arange(3),
            selected_penalty=0.25,
        )
        first = FittedPath(
            **common,
            diagnostics={
                "status": "success",
                "starts": [{
                    "runtime_seconds": 0.1,
                    "iteration_count": 7,
                    "nested": {"runtime_seconds": 0.2, "objective": 1.5},
                }],
            },
            runtime_seconds=0.3,
        )
        timing_changed = FittedPath(
            **common,
            diagnostics={
                "status": "success",
                "starts": [{
                    "runtime_seconds": 99.1,
                    "iteration_count": 7,
                    "nested": {"runtime_seconds": 99.2, "objective": 1.5},
                }],
            },
            runtime_seconds=99.3,
        )
        scientific_changed = FittedPath(
            **common,
            diagnostics={
                "status": "success",
                "starts": [{
                    "runtime_seconds": 0.1,
                    "iteration_count": 8,
                    "nested": {"runtime_seconds": 0.2, "objective": 1.5},
                }],
            },
            runtime_seconds=0.3,
        )
        self.assertEqual(fit_path_digest(first), fit_path_digest(timing_changed))
        self.assertNotEqual(fit_path_digest(first), fit_path_digest(scientific_changed))
        self.assertEqual(first.diagnostics["starts"][0]["runtime_seconds"], 0.1)
        self.assertEqual(
            first.diagnostics.to_json_dict()["starts"][0]["nested"]["runtime_seconds"],
            0.2,
        )

    def test_truth_and_endpoint_changes_do_not_change_fit_digest(self):
        fit = fixed_fit_inputs()
        shape = (200, 4, 4)
        truth = TruthBundle(
            m_ref=np.zeros(shape),
            b=np.ones(shape),
            observed_operator=np.full(shape, 2.0),
        )
        endpoint = np.eye(4)
        first = fit_required_comparators(fit, config=toy_config(), method_seed=91)

        altered_truth = dataclasses.replace(
            truth,
            m_ref=truth.m_ref - 100.0,
            b=truth.b + 100.0,
        )
        altered_endpoint = np.flip(endpoint, axis=0)
        self.assertFalse(np.array_equal(truth.b, altered_truth.b))
        self.assertFalse(np.array_equal(endpoint, altered_endpoint))
        second = fit_required_comparators(fit, config=toy_config(), method_seed=91)
        self.assertEqual(fit_bundle_digest(first), fit_bundle_digest(second))


if __name__ == "__main__":
    unittest.main()
