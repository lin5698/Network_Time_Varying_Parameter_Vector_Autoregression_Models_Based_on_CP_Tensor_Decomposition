import dataclasses
import inspect
import unittest
from unittest import mock

import numpy as np

from scripts.experiments import r006e_dw_tucker as candidate
from scripts.experiments import r006e_endpoint_support as support
from scripts.experiments import r006e_native_estimators as estimators
from scripts.experiments import r006e_native_protocol as protocol
from scripts.experiments.r006d_endpoint_support import DesignSupportPath


def toy_config() -> protocol.R006EConfig:
    return protocol.R006EConfig(n=4, true_rank=4, fitted_rank=3)


def toy_fit(*, outcomes=None) -> protocol.FitInputs:
    rng = np.random.default_rng(920701)
    predictors = rng.normal(scale=0.2, size=(200, 4))
    topology = rng.normal(scale=0.04, size=(200, 4, 4))
    topology += np.eye(4)[None]
    default_outcomes = rng.normal(scale=0.1, size=(200, 4))
    return protocol.FitInputs(
        predictors=predictors,
        outcomes=default_outcomes if outcomes is None else outcomes,
        topology=topology,
        w_ref=np.eye(4),
        coefficient_dates=np.arange(80, 200),
    )


def toy_truth(offset: float = 0.0) -> protocol.TruthBundle:
    shape = (200, 4, 4)
    return protocol.TruthBundle(
        m_ref=np.zeros(shape) + offset,
        b=np.ones(shape) + offset,
        observed_operator=np.full(shape, 2.0) + offset,
    )


def successful_path(method="anchor_local", tensor=None, penalty=None):
    values = np.zeros((4, 8, 120)) if tensor is None else tensor
    return estimators.FittedPath(
        method=method,
        parameterization="anchor",
        tensor=values,
        dates=np.arange(80, 80 + values.shape[2]),
        selected_penalty=penalty,
        diagnostics={"status": "success"},
        runtime_seconds=0.0,
    )


def input_sensitive_local(fit):
    tensor = np.empty((4, 8, len(fit.coefficient_dates)))
    for position, raw_date in enumerate(fit.coefficient_dates):
        date = int(raw_date)
        signal = (
            np.mean(fit.predictors[:date])
            + np.mean(fit.outcomes[:date])
            + np.mean(fit.topology[:date])
            + np.mean(fit.w_ref)
        )
        tensor[:, :, position] = signal
    return successful_path(tensor=tensor)


def fake_prefix_optimization(fit, **kwargs):
    lambda_t = float(kwargs["lambda_t"])
    date = int(fit.coefficient_dates[-1])
    signal = (
        np.mean(fit.predictors[:date])
        + np.mean(fit.outcomes[:date])
        + np.mean(fit.topology[:date])
        + lambda_t
    )
    tensor = np.full((4, 8, len(fit.coefficient_dates)), signal)
    starts = tuple(
        candidate.OptimizerStartResult(
            start_index=index,
            tensor=tensor,
            initial_objective=float(index),
            final_objective=float(index),
            objective_trace=(float(index),),
            accepted_step_sizes=(),
            iteration_count=0,
            stationarity_proxy=0.0,
            stopping_reason="STATIONARITY",
            converged=True,
            runtime_seconds=0.0,
            pairwise_solution_distances=(0.0, 0.0, 0.0),
        )
        for index in range(3)
    )
    return candidate.PrefixOptimization(starts=starts, selected_start_index=0)


def query_path(dates, chi):
    dates = np.asarray(dates)
    count = len(dates)
    return support.QuerySupportPath(
        dates=dates,
        chi=np.full(count, chi),
        amplification=np.ones(count),
        alpha=np.ones(count),
        retained_rank=np.full(count, 4),
        condition_number=np.ones(count),
        singular_values=tuple(np.ones(4) for _ in range(count)),
    )


def design_path(dates):
    dates = np.asarray(dates)
    return DesignSupportPath(
        dates=dates,
        tau=np.ones(len(dates)),
        retained_rank=np.full(len(dates), 4),
        singular_values=tuple(np.ones(4) for _ in dates),
        projectors=tuple(np.eye(4) for _ in dates),
    )


class R006EChronologyLeakageTest(unittest.TestCase):
    def candidate_fit(
        self,
        fit,
        *,
        optimizer_side_effect=fake_prefix_optimization,
        local_factory=input_sensitive_local,
    ):
        local = local_factory(fit)
        with mock.patch.object(candidate, "fit_anchor_local", return_value=local), \
             mock.patch.object(
                 candidate, "anchor_split_tucker_prefix", side_effect=lambda x, **_: x
             ), mock.patch.object(
                 candidate,
                 "optimize_dw_tucker_prefix",
                 side_effect=optimizer_side_effect,
             ):
            return candidate.fit_dw_joint_tucker(
                fit, config=toy_config(), method_seed=920702
            )

    def endpoint_construction(self):
        fit = toy_fit()
        endpoint = np.eye(4) * 0.5
        pool = np.stack([np.eye(4) + index for index in range(64)])
        calibration = design_path(np.arange(80, 140))
        prospective = design_path(np.arange(140, 200))
        queried_prospective_endpoints = []
        design_calls = []
        residual_calls = []

        def controlled_design(predictors, topology, w_ref, dates, **kwargs):
            design_calls.append(
                (predictors, topology, w_ref, tuple(int(x) for x in dates), kwargs)
            )
            return (
                calibration
                if tuple(dates) == tuple(range(80, 140))
                else prospective
            )

        def controlled_residuals(received_fit, dates, **kwargs):
            residual_calls.append(
                (received_fit, tuple(int(x) for x in dates), kwargs)
            )
            return object()

        def controlled_query(design, grams, w_ref, proposed):
            del grams, w_ref
            if design is calibration:
                if np.array_equal(proposed, endpoint):
                    return query_path(np.arange(80, 140), 0.01)
                index = int(round(proposed[0, 0] - 1.0))
                return query_path(
                    np.arange(80, 140), 0.05 if index == 1 else 0.20
                )
            queried_prospective_endpoints.append(np.array(proposed, copy=True))
            return query_path(np.arange(140, 200), 0.20)

        with mock.patch.object(
            support,
            "build_design_support_path",
            side_effect=controlled_design,
        ), mock.patch.object(
            support, "_residual_grams", side_effect=controlled_residuals
        ), mock.patch.object(
            support, "generate_family_pool", return_value=pool
        ), mock.patch.object(
            support, "_query_path", side_effect=controlled_query
        ):
            result = support.construct_supported_endpoints(
                fit,
                w_alt_interp=endpoint,
                family_seed=920703,
                config=toy_config(),
            )
        return (
            result,
            pool,
            queried_prospective_endpoints,
            design_calls,
            residual_calls,
            fit,
        )

    def test_endpoints_absent_from_all_fit_signatures(self):
        forbidden = {
            "truth", "m_ref", "b", "observed_operator", "endpoints",
            "endpoint", "w_alt_interp", "w_alt_family",
        }
        fit_functions = [
            function
            for module in (estimators, candidate)
            for name, function in inspect.getmembers(module, inspect.isfunction)
            if name.startswith("fit_") and function.__module__ == module.__name__
        ]
        self.assertGreaterEqual(len(fit_functions), 6)
        for function in fit_functions:
            with self.subTest(function=function.__name__):
                self.assertTrue(
                    forbidden.isdisjoint(inspect.signature(function).parameters)
                )
        self.assertEqual(
            tuple(inspect.signature(candidate.fit_dw_joint_tucker).parameters),
            ("fit", "config", "method_seed"),
        )

    def test_prefix_fit_inputs_structurally_excludes_future_rows(self):
        fit = toy_fit()
        final_position = 60
        final_date = int(fit.coefficient_dates[final_position])
        prefix = candidate.prefix_fit_inputs(fit, final_position)

        self.assertEqual(prefix.predictors.shape[0], final_date + 1)
        self.assertEqual(prefix.outcomes.shape[0], final_date + 1)
        self.assertEqual(prefix.topology.shape[0], final_date + 1)
        np.testing.assert_array_equal(
            prefix.predictors, fit.predictors[: final_date + 1]
        )
        np.testing.assert_array_equal(
            prefix.outcomes, fit.outcomes[: final_date + 1]
        )
        np.testing.assert_array_equal(
            prefix.topology, fit.topology[: final_date + 1]
        )
        np.testing.assert_array_equal(
            prefix.coefficient_dates, fit.coefficient_dates[: final_position + 1]
        )
        np.testing.assert_array_equal(prefix.w_ref, fit.w_ref)
        for value in (
            prefix.predictors,
            prefix.outcomes,
            prefix.topology,
            prefix.coefficient_dates,
            prefix.w_ref,
        ):
            self.assertFalse(value.flags.writeable)

    def test_truth_perturbation_keeps_candidate_digest_bitwise_identical(self):
        fit = toy_fit()
        first_truth = toy_truth()
        changed_truth = toy_truth(100.0)
        first_panel = protocol.NativePanel(
            fit=fit,
            truth=first_truth,
            w_alt_interp=np.eye(4),
            endpoint_stream_seed=920702,
        )
        changed_panel = dataclasses.replace(first_panel, truth=changed_truth)
        self.assertGreaterEqual(
            np.min(np.abs(changed_panel.truth.b - first_panel.truth.b)), 100.0
        )
        first = self.candidate_fit(first_panel.fit)
        second = self.candidate_fit(changed_panel.fit)
        self.assertTrue(first.is_success)
        self.assertEqual(
            estimators.fit_path_digest(first), estimators.fit_path_digest(second)
        )
        contaminated_outcomes = np.array(fit.outcomes, copy=True) + 100.0
        contaminated_fit = protocol.FitInputs(
            predictors=fit.predictors,
            outcomes=contaminated_outcomes,
            topology=fit.topology,
            w_ref=fit.w_ref,
            coefficient_dates=fit.coefficient_dates,
        )
        self.assertNotEqual(fit.sha256(), contaminated_fit.sha256())
        self.assertNotEqual(
            estimators.fit_path_digest(first),
            estimators.fit_path_digest(self.candidate_fit(contaminated_fit)),
        )

    def test_endpoint_perturbation_keeps_all_fit_digests_identical(self):
        fit = toy_fit()
        endpoint = np.eye(4)
        changed_endpoint = endpoint + 100.0
        panel = protocol.NativePanel(
            fit=fit,
            truth=toy_truth(),
            w_alt_interp=endpoint,
            endpoint_stream_seed=920704,
        )
        changed_panel = dataclasses.replace(
            panel, w_alt_interp=changed_endpoint
        )
        self.assertGreaterEqual(
            np.min(
                np.abs(changed_panel.w_alt_interp - panel.w_alt_interp)
            ),
            100.0,
        )

        def fit_all(panel_fit):
            local = input_sensitive_local(panel_fit)
            with mock.patch.object(
                estimators, "fit_anchor_local", return_value=local
            ), mock.patch.object(
                estimators,
                "_fused_reconstruct",
                side_effect=lambda prefix, *_: (prefix.copy(), {"converged": True}),
            ), mock.patch.object(
                estimators, "_tucker_reconstruct", side_effect=lambda tensor, _: tensor
            ):
                bundle = estimators.fit_required_comparators(
                    panel_fit, config=toy_config(), method_seed=920704
                )
            bundle["dw_joint_tucker333"] = self.candidate_fit(panel_fit)
            return bundle

        first = fit_all(panel.fit)
        second = fit_all(changed_panel.fit)
        self.assertEqual(set(first), set(protocol.METHODS))
        self.assertEqual(
            {name: estimators.fit_path_digest(path) for name, path in first.items()},
            {name: estimators.fit_path_digest(path) for name, path in second.items()},
        )
        contaminated_topology = np.array(fit.topology, copy=True) + 100.0
        contaminated_fit = protocol.FitInputs(
            predictors=fit.predictors,
            outcomes=fit.outcomes,
            topology=contaminated_topology,
            w_ref=fit.w_ref,
            coefficient_dates=fit.coefficient_dates,
        )
        contaminated = fit_all(contaminated_fit)
        self.assertNotEqual(fit.sha256(), contaminated_fit.sha256())
        for method in protocol.METHODS:
            with self.subTest(contamination_control=method):
                self.assertNotEqual(
                    estimators.fit_path_digest(first[method]),
                    estimators.fit_path_digest(contaminated[method]),
                )

    def test_later_local_estimate_cannot_change_earlier_validation_score(self):
        fit = toy_fit()
        rng = np.random.default_rng(920705)
        local = rng.normal(size=(4, 8, 120))
        changed = local.copy()
        scored_position = 60
        changed[:, :, scored_position + 1:] += 100.0

        shapes = []

        def future_sensitive(prefix, *_):
            shapes.append(prefix.shape[2])
            result = prefix.copy()
            result[:, :, -1] = np.sum(prefix, axis=2)
            return result, {"converged": True}

        with mock.patch.object(
            estimators, "_fused_reconstruct", side_effect=future_sensitive
        ):
            _, first = estimators.select_anchor_fused_penalty(
                local,
                fit=fit,
                validation_positions=(scored_position,),
                config=toy_config(),
            )
            _, second = estimators.select_anchor_fused_penalty(
                changed,
                fit=fit,
                validation_positions=(scored_position,),
                config=toy_config(),
            )
        self.assertEqual(first["candidate_date_scores"], second["candidate_date_scores"])
        self.assertEqual(shapes, [scored_position + 1] * 8)
        full_first, _ = future_sensitive(local, 0.1, None)
        full_changed, _ = future_sensitive(changed, 0.1, None)
        self.assertFalse(np.array_equal(full_first[:, :, -1], full_changed[:, :, -1]))

    def test_evaluation_target_cannot_change_selected_penalty(self):
        fit = toy_fit()
        changed_outcomes = np.array(fit.outcomes, copy=True)
        changed_outcomes[164:] += 100.0
        changed_fit = protocol.FitInputs(
            predictors=fit.predictors,
            outcomes=changed_outcomes,
            topology=fit.topology,
            w_ref=fit.w_ref,
            coefficient_dates=fit.coefficient_dates,
        )
        local = np.random.default_rng(920706).normal(size=(4, 8, 120))

        def identity(prefix, *_):
            return prefix.copy(), {"converged": True}

        with mock.patch.object(estimators, "_fused_reconstruct", side_effect=identity):
            first_fused, first_scores = estimators.select_anchor_fused_penalty(
                local, fit=fit, validation_positions=tuple(range(60, 84)),
                config=toy_config(),
            )
            second_fused, second_scores = estimators.select_anchor_fused_penalty(
                local, fit=changed_fit, validation_positions=tuple(range(60, 84)),
                config=toy_config(),
            )
        self.assertEqual(first_fused, second_fused)
        self.assertEqual(first_scores["candidate_scores"], second_scores["candidate_scores"])
        validation_calls = []

        def target_sensitive_optimizer(prefix, **kwargs):
            lambda_t = float(kwargs["lambda_t"])
            date = int(prefix.coefficient_dates[-1])
            if date < 164:
                validation_calls.append(
                    (
                        date,
                        tuple(int(x) for x in prefix.coefficient_dates),
                        lambda_t,
                        prefix.predictors.shape[0],
                        prefix.outcomes.shape[0],
                        prefix.topology.shape[0],
                    )
                )
            x = np.asarray(prefix.predictors[date])
            y = np.asarray(prefix.outcomes[date])
            scale = 1.0 - 10.0 * abs(lambda_t - 0.05)
            coefficient = scale * np.outer(y, x) / max(float(x @ x), 1e-12)
            tensor = np.zeros((4, 8, len(prefix.coefficient_dates)))
            tensor[:, :4, -1] = coefficient
            starts = tuple(
                candidate.OptimizerStartResult(
                    start_index=index,
                    tensor=tensor,
                    initial_objective=float(index + lambda_t),
                    final_objective=float(index + lambda_t),
                    objective_trace=(float(index + lambda_t),),
                    accepted_step_sizes=(),
                    iteration_count=0,
                    stationarity_proxy=0.0,
                    stopping_reason="STATIONARITY",
                    converged=True,
                    runtime_seconds=0.0,
                    pairwise_solution_distances=(0.0, 0.0, 0.0),
                )
                for index in range(3)
            )
            return candidate.PrefixOptimization(starts=starts, selected_start_index=0)

        first_candidate = self.candidate_fit(
            fit, optimizer_side_effect=target_sensitive_optimizer
        )
        first_calls = list(validation_calls)
        validation_calls.clear()
        second_candidate = self.candidate_fit(
            changed_fit, optimizer_side_effect=target_sensitive_optimizer
        )
        second_calls = list(validation_calls)
        self.assertEqual(first_candidate.selected_penalty, 0.05)
        self.assertEqual(second_candidate.selected_penalty, 0.05)
        self.assertEqual(first_calls, second_calls)
        self.assertEqual(len(first_calls), 4 * 24)
        for date, dates, _, predictor_rows, outcome_rows, topology_rows in first_calls:
            self.assertLess(date, 164)
            self.assertLess(max(dates), 164)
            self.assertEqual(dates[-1], date)
            self.assertEqual(predictor_rows, date + 1)
            self.assertEqual(outcome_rows, date + 1)
            self.assertEqual(topology_rows, date + 1)

    def test_family_selection_reads_calibration_dates_only(self):
        (
            result, pool, prospective_queries, design_calls, residual_calls, fit
        ) = self.endpoint_construction()
        self.assertEqual(result.family_selected_index, 1)
        np.testing.assert_array_equal(result.w_alt_family, pool[1])
        self.assertEqual(
            [record.path.dates.tolist() for record in result.family_candidates],
            [list(range(80, 140))] * 64,
        )
        self.assertEqual(len(prospective_queries), 2)
        np.testing.assert_array_equal(prospective_queries[1], pool[1])
        self.assertEqual(
            [call[3] for call in design_calls],
            [tuple(range(80, 140)), tuple(range(140, 200))],
        )
        for predictors, topology, w_ref, _, kwargs in design_calls:
            self.assertIs(predictors, fit.predictors)
            self.assertIs(topology, fit.topology)
            self.assertIs(w_ref, fit.w_ref)
            self.assertEqual(kwargs["window"], 80)
        self.assertEqual(
            [call[1] for call in residual_calls],
            [tuple(range(80, 140)), tuple(range(140, 200))],
        )
        for received_fit, _, kwargs in residual_calls:
            self.assertIs(received_fit, fit)
            self.assertEqual(kwargs["window"], 80)

    def test_lost_family_support_is_not_replaced(self):
        result, pool, prospective_queries, _, _, _ = self.endpoint_construction()
        self.assertEqual(result.family_selected_index, 1)
        np.testing.assert_array_equal(result.w_alt_family, pool[1])
        np.testing.assert_array_equal(prospective_queries[-1], pool[1])
        self.assertIn("family_lost_support_prospectively", result.failure_reasons)
        self.assertEqual(result.status, "CONSTRUCTION_FAIL")

    def test_all_24_validation_positions_are_used(self):
        fit = toy_fit()
        local = input_sensitive_local(fit)
        calls = []

        def recording_fused(prefix, penalty, _):
            calls.append((prefix.shape[2], float(penalty)))
            return prefix.copy(), {"converged": True}

        with mock.patch.object(
            estimators, "fit_anchor_local", return_value=local
        ), mock.patch.object(
            estimators, "_fused_reconstruct", side_effect=recording_fused
        ), mock.patch.object(
            estimators, "_tucker_reconstruct", side_effect=lambda tensor, _: tensor
        ):
            bundle = estimators.fit_required_comparators(
                fit, config=toy_config(), method_seed=920708
            )
        validation_calls = [call for call in calls if call[0] <= 84]
        expected = [
            (length, penalty)
            for penalty in estimators.FUSED_PENALTIES
            for length in range(61, 85)
        ]
        self.assertEqual(validation_calls, expected)
        self.assertEqual(len(validation_calls), 96)
        self.assertEqual(
            bundle["anchor_fused_tv"].diagnostics["validation_count"], 24
        )

        candidate_calls = []

        def recording_optimizer(prefix, **kwargs):
            candidate_calls.append(
                (len(prefix.coefficient_dates) - 1, kwargs["lambda_t"])
            )
            return fake_prefix_optimization(prefix, **kwargs)

        path = self.candidate_fit(fit, optimizer_side_effect=recording_optimizer)
        candidate_validation_calls = candidate_calls[:4 * 24]
        self.assertTrue(path.is_success)
        self.assertEqual(
            candidate_validation_calls,
            [
                (position, penalty)
                for penalty in candidate.TEMPORAL_PENALTIES
                for position in range(60, 84)
            ],
        )
        self.assertEqual(path.diagnostics["validation_count"], 24)

    def test_candidate_and_fused_each_have_four_penalty_options(self):
        config = toy_config()
        self.assertEqual(
            estimators.FUSED_PENALTIES, (0.10, 0.25, 0.50, 1.00)
        )
        self.assertEqual(
            candidate.TEMPORAL_PENALTIES, (0.0, 0.01, 0.05, 0.20)
        )
        self.assertEqual(config.fused_penalties, (0.10, 0.25, 0.50, 1.00))
        self.assertEqual(config.temporal_penalties, (0.0, 0.01, 0.05, 0.20))

    def test_optimizer_randomness_cannot_change_dgp_or_endpoint_streams(self):
        baseline = protocol.spawn_named_streams(920707)
        changed = protocol.spawn_named_streams(920707)
        changed["optimizer"].normal(size=10000)
        protected = (
            "operator_structure", "estimation_topology", "innovations",
            "interp_endpoint", "family_endpoint",
        )
        for name in protected:
            with self.subTest(stream=name):
                np.testing.assert_array_equal(
                    baseline[name].normal(size=128),
                    changed[name].normal(size=128),
                )


if __name__ == "__main__":
    unittest.main()
