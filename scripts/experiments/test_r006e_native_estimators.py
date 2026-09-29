import dataclasses
import inspect
import unittest
from unittest import mock

import numpy as np

from scripts.experiments.r006e_native_protocol import FitInputs, R006EConfig
from scripts.experiments import r006e_native_estimators as estimators


def toy_config() -> R006EConfig:
    return R006EConfig(n=4, true_rank=4, fitted_rank=3)


def fixed_toy_fit_inputs() -> FitInputs:
    rng = np.random.default_rng(910501)
    predictors = rng.normal(size=(200, 4))
    topology = rng.normal(scale=0.08, size=(200, 4, 4))
    topology += np.eye(4)[None, :, :]
    outcomes = rng.normal(scale=0.2, size=(200, 4))
    return FitInputs(
        predictors=predictors,
        outcomes=outcomes,
        topology=topology,
        w_ref=np.eye(4),
        coefficient_dates=np.arange(80, 200, dtype=int),
    )


def fixed_toy_anchor_path() -> np.ndarray:
    rng = np.random.default_rng(910502)
    return rng.normal(scale=0.05, size=(4, 8, 120))


class R006ENativeEstimatorsTest(unittest.TestCase):
    def test_required_comparator_names_and_penalty_declarations(self):
        self.assertEqual(
            estimators.REQUIRED_COMPARATORS,
            ("anchor_local", "anchor_fused_tv", "anchor_split_tucker333"),
        )
        config = toy_config()
        self.assertEqual(config.fused_penalties, (0.10, 0.25, 0.50, 1.00))
        self.assertEqual(len(config.temporal_penalties), 4)

    def test_comparator_algorithms_freeze_four_penalties_and_rank_three(self):
        local = fixed_toy_anchor_path()
        config = dataclasses.replace(
            toy_config(), fitted_rank=2, fused_penalties=(9.0,)
        )

        def identity(prefix, penalty, fused_config):
            del penalty, fused_config
            return prefix.copy(), {"converged": True}

        with mock.patch.object(
            estimators, "_fused_reconstruct", side_effect=identity
        ) as fused:
            selected, _ = estimators.select_anchor_fused_penalty(
                local,
                fit=fixed_toy_fit_inputs(),
                validation_positions=(60,),
                config=config,
            )
        self.assertEqual(selected, 0.10)
        self.assertEqual(
            [call.args[1] for call in fused.call_args_list],
            [0.10, 0.25, 0.50, 1.00],
        )

        with mock.patch.object(
            estimators, "_tucker_reconstruct", side_effect=lambda tensor, rank: tensor
        ) as tucker:
            estimators.fit_anchor_split_tucker_evaluation(
                local,
                dates=np.arange(80, 200),
                evaluation_positions=(84,),
                config=config,
            )
        self.assertEqual([call.args[1] for call in tucker.call_args_list], [3, 3])

    def test_anchor_local_returns_full_anchor_path_and_ridge_diagnostics(self):
        path = estimators.fit_anchor_local(
            fixed_toy_fit_inputs(), config=toy_config()
        )
        self.assertEqual(path.method, "anchor_local")
        self.assertEqual(path.parameterization, "anchor")
        self.assertEqual(path.tensor.shape, (4, 8, 120))
        self.assertEqual(path.dates.tolist(), list(range(80, 200)))
        self.assertEqual(len(path.diagnostics["gram_scales"]), 120)
        self.assertEqual(len(path.diagnostics["ridge_penalties"]), 120)
        self.assertTrue(all(x > 0.0 for x in path.diagnostics["gram_scales"]))
        self.assertTrue(all(x > 0.0 for x in path.diagnostics["ridge_penalties"]))

    def test_anchor_validation_score_uses_delta_from_reference_topology(self):
        fit = fixed_toy_fit_inputs()
        position = 60
        date = int(fit.coefficient_dates[position])
        tensor = np.zeros((4, 8, position + 1))
        tensor[:, 4:, -1] = np.eye(4)
        expected = (fit.topology[date] - fit.w_ref) @ fit.predictors[date]
        altered = FitInputs(
            predictors=fit.predictors,
            outcomes=np.array(fit.outcomes, copy=True),
            topology=fit.topology,
            w_ref=fit.w_ref,
            coefficient_dates=fit.coefficient_dates,
        )
        outcomes = np.array(altered.outcomes, copy=True)
        outcomes[date] = expected
        aligned = FitInputs(
            predictors=altered.predictors,
            outcomes=outcomes,
            topology=altered.topology,
            w_ref=altered.w_ref,
            coefficient_dates=altered.coefficient_dates,
        )
        self.assertEqual(
            estimators.anchor_prediction_rmse(tensor, fit=aligned, position=position),
            0.0,
        )

    def test_anchor_fused_validation_is_strict_prefix_and_uses_all_positions(self):
        local = fixed_toy_anchor_path()
        fit = fixed_toy_fit_inputs()
        positions = tuple(range(60, 84))
        first, diagnostics = estimators.select_anchor_fused_penalty(
            local, fit=fit, validation_positions=positions, config=toy_config()
        )
        changed = local.copy()
        changed[:, :, 84:] += 1000.0
        second, changed_diagnostics = estimators.select_anchor_fused_penalty(
            changed, fit=fit, validation_positions=positions, config=toy_config()
        )
        self.assertEqual(first, second)
        self.assertEqual(
            diagnostics["candidate_scores"],
            changed_diagnostics["candidate_scores"],
        )
        self.assertEqual(diagnostics["validation_positions"], positions)
        self.assertEqual(diagnostics["validation_count"], 24)

    def test_fused_selection_refits_each_candidate_at_each_prefix_and_ties_small(self):
        local = fixed_toy_anchor_path()
        positions = tuple(range(60, 84))

        def identity(prefix, penalty, config):
            del penalty, config
            return prefix.copy(), {"converged": True}

        with mock.patch.object(
            estimators, "_fused_reconstruct", side_effect=identity
        ) as reconstruct:
            selected, _ = estimators.select_anchor_fused_penalty(
                local,
                fit=fixed_toy_fit_inputs(),
                validation_positions=positions,
                config=toy_config(),
            )

        self.assertEqual(selected, 0.10)
        self.assertEqual(reconstruct.call_count, 4 * 24)
        self.assertEqual(
            [call.args[0].shape[2] for call in reconstruct.call_args_list[:24]],
            [position + 1 for position in positions],
        )

    def test_fused_evaluation_is_prefixwise_for_all_36_dates(self):
        local = fixed_toy_anchor_path()
        positions = tuple(range(84, 120))

        def marker(prefix, penalty, config):
            del penalty, config
            result = np.zeros_like(prefix)
            result[:, :, -1] = prefix.shape[2]
            return result, {"converged": True}

        with mock.patch.object(
            estimators, "_fused_reconstruct", side_effect=marker
        ) as reconstruct:
            path = estimators.fit_anchor_fused_evaluation(
                local,
                dates=np.arange(80, 200),
                evaluation_positions=positions,
                selected_penalty=0.25,
                config=toy_config(),
                selection_diagnostics={"validation_count": 24},
            )

        self.assertEqual(reconstruct.call_count, 36)
        self.assertEqual(
            [call.args[0].shape[2] for call in reconstruct.call_args_list],
            list(range(85, 121)),
        )
        self.assertEqual(path.tensor.shape, (4, 8, 36))
        np.testing.assert_array_equal(path.tensor[0, 0], np.arange(85, 121))
        self.assertEqual(path.diagnostics["evaluation_count"], 36)

    def test_split_tucker_is_separate_and_prefixwise_for_all_evaluation_dates(self):
        local = fixed_toy_anchor_path()
        positions = tuple(range(84, 120))

        def marker(tensor, rank):
            self.assertEqual(rank, 3)
            return np.full_like(tensor, tensor.shape[2])

        with mock.patch.object(
            estimators, "_tucker_reconstruct", side_effect=marker
        ) as reconstruct:
            path = estimators.fit_anchor_split_tucker_evaluation(
                local,
                dates=np.arange(80, 200),
                evaluation_positions=positions,
                config=toy_config(),
            )

        self.assertEqual(reconstruct.call_count, 72)
        self.assertEqual(
            [call.args[0].shape[2] for call in reconstruct.call_args_list[::2]],
            list(range(85, 121)),
        )
        self.assertEqual(path.tensor.shape, (4, 8, 36))
        np.testing.assert_array_equal(path.tensor[0, 0], np.arange(85, 121))
        self.assertEqual(path.diagnostics["split_rank"], 3)
        self.assertEqual(path.diagnostics["evaluation_count"], 36)

    def test_fit_bundle_has_exact_order_counts_and_retains_method_failure(self):
        bundle = estimators.fit_required_comparators(
            fixed_toy_fit_inputs(), config=toy_config(), method_seed=910503
        )
        self.assertEqual(tuple(bundle), estimators.REQUIRED_COMPARATORS)
        self.assertEqual(bundle["anchor_local"].tensor.shape[2], 120)
        for method in estimators.REQUIRED_COMPARATORS[1:]:
            self.assertEqual(bundle[method].dates.tolist(), list(range(164, 200)))
            self.assertEqual(bundle[method].diagnostics["evaluation_count"], 36)
        self.assertEqual(
            bundle["anchor_fused_tv"].diagnostics["validation_count"], 24
        )

        with mock.patch.object(
            estimators, "fit_anchor_local", side_effect=RuntimeError("forced")
        ):
            failed = estimators.fit_required_comparators(
                fixed_toy_fit_inputs(), config=toy_config(), method_seed=910504
            )
        self.assertEqual(tuple(failed), estimators.REQUIRED_COMPARATORS)
        for name, path in failed.items():
            self.assertEqual(path.method, name)
            self.assertEqual(path.status, "failure")
            self.assertFalse(path.is_success)
            self.assertEqual(path.diagnostics["error_type"], "RuntimeError")
            self.assertEqual(path.tensor.shape[2], 0)
            self.assertEqual(path.dates.size, 0)
            self.assertEqual(
                path.diagnostics["intended_count"],
                120 if name == "anchor_local" else 36,
            )
            self.assertEqual(
                path.diagnostics["expected_tensor_shape"],
                (4, 8, 120 if name == "anchor_local" else 36),
            )
            self.assertTrue(np.all(np.isfinite(path.tensor)))
            self.assertTrue(np.isfinite(path.runtime_seconds))
            with self.assertRaises(RuntimeError):
                path.require_success()

    def test_failure_path_schema_prevents_scientific_payload(self):
        diagnostics = {
            "status": "failure",
            "error_type": "RuntimeError",
            "error_message": "forced",
            "intended_dates": [164],
            "intended_count": 1,
            "expected_tensor_shape": [4, 8, 1],
        }
        for tensor, dates in (
            (np.zeros((4, 8, 1)), np.array([164])),
            (np.zeros((4, 8, 1)), np.array([], dtype=int)),
            (np.zeros((4, 8, 0)), np.array([164])),
        ):
            with self.subTest(shape=tensor.shape, dates=dates.tolist()):
                with self.assertRaises(ValueError):
                    estimators.FittedPath(
                        method="failed",
                        parameterization="anchor",
                        tensor=tensor,
                        dates=dates,
                        selected_penalty=None,
                        diagnostics=diagnostics,
                        runtime_seconds=0.0,
                    )

    def test_fit_source_and_api_do_not_accept_truth_or_endpoint_inputs(self):
        parameters = set(inspect.signature(estimators.fit_required_comparators).parameters)
        forbidden = {
            "truth",
            "b_true",
            "m_ref_true",
            "w_alt_interp",
            "w_alt_family",
            "endpoint",
        }
        self.assertTrue(parameters.isdisjoint(forbidden))
        source = inspect.getsource(estimators.fit_required_comparators).lower()
        self.assertFalse(any(name in source for name in forbidden))


if __name__ == "__main__":
    unittest.main()
