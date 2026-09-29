import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import unittest
from dataclasses import replace
from unittest import mock

import numpy as np

from scripts.experiments.r006e_native_protocol import FitInputs, R006EConfig, keyed_seed
from scripts.experiments.r006e_native_estimators import FittedPath
from scripts.experiments import r006e_dw_tucker as candidate


def fixed_fit(seed: int = 7, *, n: int = 3, dates: int = 6, window: int = 8) -> FitInputs:
    rng = np.random.default_rng(seed)
    total = window + dates
    predictors = rng.normal(scale=0.4, size=(total, n))
    topology = rng.normal(scale=0.1, size=(total, n, n))
    w_ref = np.eye(n) * 0.2
    theta = rng.normal(scale=0.08, size=(n, 2 * n, dates))
    outcomes = rng.normal(scale=0.03, size=(total, n))
    for position, date in enumerate(range(window, total)):
        delta = (topology[date] - w_ref) @ predictors[date]
        q = np.concatenate([predictors[date], delta])
        outcomes[date] = theta[:, :, position] @ q
    return FitInputs(
        predictors=predictors,
        outcomes=outcomes,
        topology=topology,
        w_ref=w_ref,
        coefficient_dates=np.arange(window, total, dtype=int),
    )


def fixed_anchor(fit: FitInputs, seed: int = 8) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = fit.predictors.shape[1]
    return rng.normal(scale=0.05, size=(n, 2 * n, len(fit.coefficient_dates)))


class R006EDWTuckerTest(unittest.TestCase):
    def test_direct_and_gram_losses_agree_with_temporal_penalty(self):
        fit = fixed_fit()
        theta = fixed_anchor(fit)
        cache = candidate.build_gram_cache(fit)
        direct = candidate.normalized_outcome_loss(theta, fit, lambda_t=0.05)
        gram = candidate.normalized_gram_loss(theta, cache, lambda_t=0.05)
        self.assertLess(abs(direct - gram), 1e-10)
        self.assertAlmostEqual(cache.g_bar, np.mean([
            np.trace(value) / (cache.window_sizes[i] * 2 * cache.n)
            for i, value in enumerate(cache.grams)
        ]))

    def test_tensor_orientation_is_y_minus_q_theta_transpose(self):
        fit = fixed_fit(seed=11, n=2, dates=3, window=5)
        theta = np.zeros((2, 4, 3))
        theta[:, :, 0] = np.array([[1, 2, 3, 4], [5, 6, 7, 8]]) / 10
        date = int(fit.coefficient_dates[0])
        rows = []
        for s in range(date - 5, date):
            exposure = (fit.topology[s] - fit.w_ref) @ fit.predictors[s]
            rows.append(np.concatenate([fit.predictors[s], exposure]))
        q = np.asarray(rows)
        expected = np.sum((fit.outcomes[date - 5:date] - q @ theta[:, :, 0].T) ** 2)
        cache = candidate.build_gram_cache(fit)
        self.assertAlmostEqual(candidate.slice_outcome_loss(theta[:, :, 0], fit, position=0), expected)
        self.assertEqual(cache.grams.shape, (3, 4, 4))
        self.assertEqual(cache.cross_products.shape, (3, 2, 4))

    def test_complete_objective_gradient_matches_finite_differences(self):
        fit = fixed_fit(seed=13, n=2, dates=4, window=6)
        theta = fixed_anchor(fit, seed=14)
        cache = candidate.build_gram_cache(fit)
        gradient = candidate.complete_objective_gradient(theta, cache, lambda_t=0.2)
        epsilon = 1e-6
        for index in ((0, 0, 0), (1, 3, 2), (0, 2, 3)):
            plus = theta.copy()
            minus = theta.copy()
            plus[index] += epsilon
            minus[index] -= epsilon
            numeric = (
                candidate.normalized_gram_loss(plus, cache, lambda_t=0.2)
                - candidate.normalized_gram_loss(minus, cache, lambda_t=0.2)
            ) / (2 * epsilon)
            self.assertAlmostEqual(gradient[index], numeric, places=7)

    def test_hosvd_projection_has_rank_sign_normalization_and_reproducible_bytes(self):
        tensor = np.random.default_rng(21).normal(size=(5, 7, 6))
        first = candidate.project_tucker333(tensor, rank=3, return_decomposition=True)
        second = candidate.project_tucker333(tensor, rank=3, return_decomposition=True)
        self.assertEqual(first.tensor.tobytes(), second.tensor.tobytes())
        self.assertEqual(
            hashlib.sha256(first.tensor.tobytes()).hexdigest(),
            "f9f349aa8d62fd30b032956966aedff89b809054ece975a0e9854987288e21e0",
        )
        for mode, factor in enumerate(first.factors):
            self.assertEqual(factor.shape, (tensor.shape[mode], 3))
            np.testing.assert_allclose(factor.T @ factor, np.eye(3), atol=1e-12)
            for column in range(3):
                values = factor[:, column]
                pivot = int(np.flatnonzero(np.abs(values) == np.max(np.abs(values)))[0])
                self.assertGreaterEqual(values[pivot], 0.0)
            unfolded = np.moveaxis(first.tensor, mode, 0).reshape(tensor.shape[mode], -1)
            self.assertLessEqual(np.linalg.matrix_rank(unfolded, tol=1e-10), 3)

    def test_tied_singular_subspace_uses_rotation_invariant_coordinate_basis(self):
        self.assertEqual(
            candidate.SVD_TIE_TOLERANCE_FORMULA,
            "64*eps*max(sigma_max,1)",
        )
        tensor = np.zeros((4, 4, 4))
        singular_values = np.array([5.0, 4.0, 3.0, 3.0])
        identity = np.eye(4)
        angle = 0.37
        rotated = identity.copy()
        rotated[:, 2:4] = identity[:, 2:4] @ np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ])
        vh = np.eye(4, 16)
        with mock.patch.object(
            candidate.np.linalg, "svd", return_value=(identity, singular_values, vh)
        ):
            reference = candidate._signed_left_vectors(tensor, 0, 3)
        with mock.patch.object(
            candidate.np.linalg, "svd", return_value=(rotated, singular_values, vh)
        ):
            actual = candidate._signed_left_vectors(tensor, 0, 3)
        np.testing.assert_allclose(actual, reference, atol=1e-12)

    def test_singular_values_just_above_frozen_tolerance_are_not_tied(self):
        tensor = np.zeros((4, 4, 4))
        identity = np.eye(4)
        angle = 0.37
        rotated = identity.copy()
        rotated[:, 2:4] = identity[:, 2:4] @ np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ])
        tolerance = 64 * np.finfo(float).eps * 5.0
        singular_values = np.array([5.0, 4.0, 3.0, 3.0 - 2.0 * tolerance])
        with mock.patch.object(
            candidate.np.linalg,
            "svd",
            return_value=(rotated, singular_values, np.eye(4, 16)),
        ):
            actual = candidate._signed_left_vectors(tensor, 0, 4)
        np.testing.assert_allclose(actual, rotated, atol=1e-15)

    def test_tied_block_mgs_skips_residuals_at_the_same_frozen_tolerance(self):
        tensor = np.zeros((3, 2, 2))
        residual_norm = 1e-10
        first_row = residual_norm * np.array([1.0, 1.0]) / np.sqrt(2.0)
        remainder = np.linalg.cholesky(
            np.eye(2) - np.outer(first_row, first_row)
        ).T
        tied_block = np.vstack([first_row, remainder])
        null_vector = np.linalg.svd(tied_block.T, full_matrices=True)[2][-1]
        left = np.column_stack([tied_block, null_vector])
        projector = tied_block @ tied_block.T
        expected_first = projector[:, 1] / np.linalg.norm(projector[:, 1])
        pivot = int(np.argmax(np.abs(expected_first)))
        if expected_first[pivot] < 0.0:
            expected_first *= -1.0

        with mock.patch.object(
            candidate.np.linalg,
            "svd",
            return_value=(left, np.array([1e6, 1e6, 0.0]), np.eye(3, 4)),
        ):
            actual = candidate._signed_left_vectors(tensor, 0, 2)

        np.testing.assert_allclose(actual[:, 0], expected_first, atol=1e-15)

    def test_perturbation_starts_are_exactly_keyed_scaled_in_tensor_space(self):
        fit = fixed_fit(seed=22, n=3, dates=5, window=7)
        anchor = fixed_anchor(fit, seed=23)
        starts = candidate.make_optimizer_starts(
            anchor,
            method_seed=91,
            prefix_end_date=11,
            lambda_grid_index=2,
            rank=3,
        )
        self.assertEqual(tuple(item.start_index for item in starts), (0, 1, 2))
        np.testing.assert_array_equal(starts[0].pre_projection_tensor, anchor)
        np.testing.assert_array_equal(starts[0].tensor, anchor)
        scale = 0.05 * max(np.linalg.norm(starts[0].tensor), 1.0)
        for item in starts[1:]:
            self.assertEqual(item.key, (91, 11, 2, item.start_index))
            self.assertEqual(item.seed, keyed_seed(91, 11, 2, item.start_index))
            difference = item.pre_projection_tensor - starts[0].tensor
            self.assertAlmostEqual(np.linalg.norm(difference), scale, places=12)
            repeated = candidate.make_optimizer_starts(
                anchor, method_seed=91, prefix_end_date=11,
                lambda_grid_index=2, rank=3,
            )[item.start_index]
            self.assertEqual(item.tensor.tobytes(), repeated.tensor.tobytes())

    def test_anchor_split_start_is_jointly_projected_to_rank_333(self):
        n = 4
        raw = np.random.default_rng(24).normal(size=(n, 2 * n, 9))
        anchor = candidate.anchor_split_tucker_prefix(raw, n=n, rank=3)
        for mode, dimension in enumerate(anchor.shape):
            unfolded = np.moveaxis(anchor, mode, 0).reshape(dimension, -1)
            self.assertLessEqual(np.linalg.matrix_rank(unfolded, tol=1e-10), 3)

    def test_optimizer_start_and_no_converged_error_are_deeply_immutable(self):
        source = np.arange(24.0).reshape(2, 4, 3)
        start = candidate.OptimizerStart(0, None, None, source, source)
        source.fill(-1.0)
        self.assertNotEqual(float(start.tensor[0, 0, 1]), -1.0)
        for value in (start.pre_projection_tensor, start.tensor):
            with self.assertRaises(ValueError):
                value.setflags(write=True)
        error = candidate.NoConvergedStartError(
            "none converged", (candidate.synthetic_start_result(0, 1.0, converged=False),)
        )
        with self.assertRaises(AttributeError):
            error._start_results = ()
        self.assertEqual(len(error.start_results), 1)

    def test_backtracking_uses_exact_trials_and_accepts_first_eligible(self):
        theta = np.ones((2, 4, 3))
        gradient = np.ones_like(theta)
        calls = []

        def objective(value):
            alpha = float(1.0 - value[0, 0, 0])
            calls.append(alpha)
            return 2.0 if alpha > 0.25 else 1.0

        accepted = candidate.backtracking_projected_step(
            theta, gradient, prior_objective=1.0, objective=objective,
            rank=3, projector=lambda value, rank: value,
        )
        self.assertEqual(calls, [1.0, 0.5, 0.25])
        self.assertEqual(accepted.step_size, 0.25)
        self.assertTrue(accepted.accepted)

        failed_calls = []
        failed = candidate.backtracking_projected_step(
            theta, gradient, prior_objective=1.0,
            objective=lambda value: failed_calls.append(value) or 2.0,
            rank=3, projector=lambda value, rank: value,
        )
        self.assertFalse(failed.accepted)
        self.assertEqual(len(failed_calls), 25)

    def test_relative_improvement_and_stopping_reasons_are_frozen(self):
        self.assertEqual(candidate.relative_improvement(2.0, 1.5), 0.25)
        self.assertEqual(candidate.relative_improvement(0.0, 0.0), 0.0)
        cases = (
            (dict(relative_improvements=(1e-7,) * 5, stationarity=1.0), ("OBJECTIVE_TOLERANCE", True)),
            (dict(relative_improvements=(), stationarity=1e-4), ("STATIONARITY", True)),
            (dict(relative_improvements=(), stationarity=1.0, backtrack_failed=True), ("BACKTRACK_FAIL", False)),
            (dict(relative_improvements=(), stationarity=1.0, iteration=300, max_iterations=300), ("ITERATION_CAP", False)),
            (dict(relative_improvements=(), stationarity=np.nan, numerical_failed=True), ("NUMERICAL_FAIL", False)),
        )
        for arguments, expected in cases:
            defaults = dict(iteration=0, max_iterations=300, backtrack_failed=False, numerical_failed=False)
            defaults.update(arguments)
            with self.subTest(expected=expected):
                self.assertEqual(candidate.classify_stopping(**defaults), expected)
        self.assertIsNone(candidate.classify_stopping(
            relative_improvements=(0.0, 2e-6, 0.0, 0.0, 0.0, 0.0),
            stationarity=1.0, iteration=4, max_iterations=300,
            backtrack_failed=False, numerical_failed=False,
        ))

    def test_projected_gradient_proxy_matches_unit_step_formula(self):
        theta = np.arange(24.0).reshape(2, 4, 3) / 10
        gradient = np.ones_like(theta) * 0.3
        projector = lambda value, rank: value * 0.5
        expected = np.linalg.norm(theta - projector(theta - gradient, 3)) / max(np.linalg.norm(theta), 1.0)
        actual = candidate.projected_gradient_proxy(theta, gradient, rank=3, projector=projector)
        self.assertAlmostEqual(actual, expected)

    def test_start_selection_uses_only_finite_converged_objective_and_exact_tie_index(self):
        starts = [
            candidate.synthetic_start_result(0, 1.0, converged=True),
            candidate.synthetic_start_result(1, 0.5, converged=False),
            candidate.synthetic_start_result(2, 1.0, converged=True),
        ]
        self.assertEqual(candidate.select_optimizer_start(starts).start_index, 0)
        with self.assertRaises(candidate.NoConvergedStartError):
            candidate.select_optimizer_start([
                candidate.synthetic_start_result(0, 0.1, converged=False),
                candidate.synthetic_start_result(1, np.inf, converged=True),
            ])

    def test_no_converged_error_retains_all_start_details_and_distances(self):
        fit = fixed_fit(seed=27, n=3, dates=4, window=7)
        anchor = fixed_anchor(fit, seed=28)
        shape = anchor.shape
        forced = []
        for index in range(3):
            forced.append(candidate.OptimizerStartResult(
                start_index=index,
                tensor=np.full(shape, float(index)),
                initial_objective=3.0 + index,
                final_objective=2.0 + index,
                objective_trace=(3.0 + index, 2.0 + index),
                accepted_step_sizes=(0.5,),
                iteration_count=1,
                stationarity_proxy=0.9 + index,
                stopping_reason="ITERATION_CAP" if index < 2 else "BACKTRACK_FAIL",
                converged=False,
                runtime_seconds=0.1 + index,
            ))
        with mock.patch.object(candidate, "_optimize_start", side_effect=forced):
            with self.assertRaises(candidate.NoConvergedStartError) as raised:
                candidate.optimize_dw_tucker_prefix(
                    fit, anchor_tensor=anchor, lambda_t=0.0, rank=3,
                    method_seed=8, prefix_end_date=10, lambda_grid_index=0,
                )
        retained = raised.exception.start_results
        self.assertIsInstance(retained, tuple)
        self.assertEqual(len(retained), 3)
        with self.assertRaises(AttributeError):
            raised.exception.start_results = ()
        self.assertEqual(
            tuple(item.stopping_reason for item in retained),
            ("ITERATION_CAP", "ITERATION_CAP", "BACKTRACK_FAIL"),
        )
        expected = np.linalg.norm(np.ones(shape))
        self.assertAlmostEqual(retained[0].pairwise_solution_distances[1], expected)
        self.assertAlmostEqual(retained[0].pairwise_solution_distances[2], 2 * expected)
        with self.assertRaises((AttributeError, TypeError)):
            retained[0].pairwise_solution_distances += (9.0,)

    def test_optimizer_trace_is_monotone_and_records_three_starts_and_distances(self):
        fit = fixed_fit(seed=31, n=3, dates=5, window=7)
        result = candidate.optimize_dw_tucker_prefix(
            fit,
            anchor_tensor=fixed_anchor(fit, seed=32),
            lambda_t=0.05,
            rank=3,
            method_seed=12,
            prefix_end_date=int(fit.coefficient_dates[-1]),
            lambda_grid_index=2,
            max_iterations=8,
            objective_tolerance=1e-6,
            stationarity_tolerance=1e6,
        )
        self.assertEqual(len(result.starts), 3)
        expected = min(
            result.starts, key=lambda start: (start.final_objective, start.start_index)
        )
        self.assertEqual(result.selected.start_index, expected.start_index)
        for start in result.starts:
            trace = np.asarray(start.objective_trace)
            self.assertTrue(np.all(np.diff(trace) <= 1e-12))
            self.assertEqual(len(start.pairwise_solution_distances), 3)
            self.assertEqual(start.pairwise_solution_distances[start.start_index], 0.0)
            self.assertGreaterEqual(start.runtime_seconds, 0.0)

    def test_initial_stationarity_projection_failure_retains_all_starts(self):
        fit = fixed_fit(seed=33, n=3, dates=5, window=7)
        with mock.patch.object(
            candidate, "projected_gradient_proxy", side_effect=FloatingPointError("svd failed")
        ):
            with self.assertRaises(candidate.NoConvergedStartError) as raised:
                candidate.optimize_dw_tucker_prefix(
                    fit, anchor_tensor=fixed_anchor(fit, seed=34), lambda_t=0.05,
                    rank=3, method_seed=12, prefix_end_date=11,
                    lambda_grid_index=2, max_iterations=2,
                )
        retained = raised.exception.start_results
        self.assertEqual(len(retained), 3)
        self.assertEqual(tuple(item.stopping_reason for item in retained), ("NUMERICAL_FAIL",) * 3)
        self.assertTrue(all(item.iteration_count == 0 for item in retained))
        self.assertTrue(all(len(item.pairwise_solution_distances) == 3 for item in retained))

    def test_post_step_stationarity_projection_failure_retains_prior_finite_step(self):
        fit = fixed_fit(seed=35, n=3, dates=5, window=7)
        cache = candidate.build_gram_cache(fit)
        start = candidate.make_optimizer_starts(
            fixed_anchor(fit, seed=36), method_seed=12, prefix_end_date=11,
            lambda_grid_index=2, rank=3,
        )[0]
        accepted_tensor = np.asarray(start.tensor) * 0.9
        accepted_objective = candidate.normalized_gram_loss(
            accepted_tensor, cache, lambda_t=0.05
        )
        accepted = candidate.BacktrackingResult(
            True, accepted_tensor, accepted_objective, 1.0, 1
        )
        with mock.patch.object(
            candidate, "projected_gradient_proxy",
            side_effect=[1.0, np.linalg.LinAlgError("svd failed")],
        ), mock.patch.object(candidate, "backtracking_projected_step", return_value=accepted):
            result = candidate._optimize_start(
                start, cache, lambda_t=0.05, rank=3, max_iterations=2,
                objective_tolerance=1e-6, stationarity_tolerance=1e-4,
            )
        self.assertEqual(result.stopping_reason, "NUMERICAL_FAIL")
        self.assertFalse(result.converged)
        self.assertEqual(result.iteration_count, 1)
        np.testing.assert_array_equal(result.tensor, accepted_tensor)
        self.assertEqual(result.final_objective, accepted_objective)

    def test_fit_api_is_keyword_only_and_has_no_truth_or_endpoint_surface(self):
        signature = inspect.signature(candidate.fit_dw_joint_tucker)
        self.assertEqual(tuple(signature.parameters), ("fit", "config", "method_seed"))
        self.assertEqual(signature.parameters["config"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(signature.parameters["method_seed"].kind, inspect.Parameter.KEYWORD_ONLY)
        source = inspect.getsource(candidate.fit_dw_joint_tucker).lower()
        for forbidden in ("truth", "endpoint", "w_alt", "oracle"):
            self.assertNotIn(forbidden, source)

    def test_lambda_grid_and_prefix_counts_are_exact_and_later_data_cannot_change_earlier_fit(self):
        self.assertEqual(candidate.TEMPORAL_PENALTIES, (0.0, 0.01, 0.05, 0.20))
        self.assertEqual(candidate.VALIDATION_POSITIONS, tuple(range(60, 84)))
        self.assertEqual(candidate.EVALUATION_POSITIONS, tuple(range(84, 120)))
        fit = fixed_fit(seed=41, n=3, dates=6, window=7)
        prefix = candidate.prefix_fit_inputs(fit, 2)
        altered_outcomes = np.array(fit.outcomes, copy=True)
        altered_topology = np.array(fit.topology, copy=True)
        later_date = int(fit.coefficient_dates[3])
        altered_outcomes[later_date:] += 999
        altered_topology[later_date:] -= 999
        altered = FitInputs(fit.predictors, altered_outcomes, altered_topology, fit.w_ref, fit.coefficient_dates)
        changed_prefix = candidate.prefix_fit_inputs(altered, 2)
        self.assertEqual(candidate.build_gram_cache(prefix).sha256(), candidate.build_gram_cache(changed_prefix).sha256())

    def test_joint_fit_uses_96_validation_and_36_selected_lambda_prefixes(self):
        fit = fixed_fit(seed=51, n=4, dates=120, window=80)
        config = R006EConfig(n=4, true_rank=4, fitted_rank=3)
        local_tensor = fixed_anchor(fit, seed=52)
        local = FittedPath(
            method="anchor_local", parameterization="anchor",
            tensor=local_tensor, dates=fit.coefficient_dates,
            selected_penalty=None, diagnostics={"status": "success"},
            runtime_seconds=0.0,
        )
        calls = []

        def optimized(prefix, **kwargs):
            calls.append((len(prefix.coefficient_dates), kwargs["lambda_t"], kwargs["lambda_grid_index"]))
            shape = (4, 8, len(prefix.coefficient_dates))
            starts = []
            for index in range(3):
                base = candidate.synthetic_start_result(index, 1.0 + index, converged=True)
                tensor = np.full(shape, kwargs["lambda_t"] + index)
                starts.append(replace(base, tensor=tensor))
            return candidate.PrefixOptimization(tuple(starts), 0)

        def residual(coefficient, fit, position):
            del fit, position
            return np.full(4, abs(float(coefficient[0, 0]) - 0.05))

        with mock.patch.object(candidate, "fit_anchor_local", return_value=local), \
             mock.patch.object(candidate, "optimize_dw_tucker_prefix", side_effect=optimized), \
             mock.patch.object(candidate, "_observed_residual", side_effect=residual):
            path = candidate.fit_dw_joint_tucker(fit, config=config, method_seed=71)

        self.assertEqual(path.status, "success")
        self.assertEqual(path.selected_penalty, 0.05)
        self.assertEqual(len(calls), 4 * 24 + 36)
        self.assertEqual([value[0] for value in calls[:24]], list(range(61, 85)))
        self.assertEqual([value[0] for value in calls[-36:]], list(range(85, 121)))
        self.assertTrue(all(value[1:] == (0.05, 2) for value in calls[-36:]))
        self.assertEqual(path.tensor.shape, (4, 8, 36))
        np.testing.assert_array_equal(path.tensor, np.full((4, 8, 36), 0.05))
        self.assertEqual(
            path.diagnostics["svd_tie_tolerance_formula"],
            candidate.SVD_TIE_TOLERANCE_FORMULA,
        )

        calls.clear()
        with mock.patch.object(candidate, "fit_anchor_local", return_value=local), \
             mock.patch.object(candidate, "optimize_dw_tucker_prefix", side_effect=optimized), \
             mock.patch.object(candidate, "_observed_residual", return_value=np.ones(4)):
            tied = candidate.fit_dw_joint_tucker(fit, config=config, method_seed=73)
        self.assertEqual(tied.selected_penalty, 0.0)
        self.assertTrue(all(value[1:] == (0.0, 0) for value in calls[-36:]))

        with mock.patch.object(candidate, "fit_anchor_local", return_value=local), \
             mock.patch.object(
                 candidate, "optimize_dw_tucker_prefix",
                 side_effect=candidate.NoConvergedStartError("no finite converged optimizer start"),
             ):
            failed = candidate.fit_dw_joint_tucker(fit, config=config, method_seed=72)
        self.assertEqual(failed.status, "failure")
        self.assertEqual(failed.tensor.shape, (4, 8, 0))
        self.assertEqual(failed.diagnostics["intended_count"], 36)
        self.assertEqual(failed.diagnostics["error_type"], "NoConvergedStartError")
        with self.assertRaises(RuntimeError):
            failed.require_success()

    def test_fit_retains_completed_and_failing_prefix_start_diagnostics(self):
        fit = fixed_fit(seed=61, n=4, dates=120, window=80)
        config = R006EConfig(n=4, true_rank=4, fitted_rank=3)
        local = FittedPath(
            method="anchor_local", parameterization="anchor",
            tensor=fixed_anchor(fit, seed=62), dates=fit.coefficient_dates,
            selected_penalty=None, diagnostics={"status": "success"},
            runtime_seconds=0.0,
        )
        shape = (4, 8, 63)
        failed_starts = tuple(candidate.OptimizerStartResult(
            start_index=index,
            tensor=np.full(shape, index, dtype=float),
            initial_objective=4.0 + index,
            final_objective=3.0 + index,
            objective_trace=(4.0 + index, 3.0 + index),
            accepted_step_sizes=(0.25,), iteration_count=1,
            stationarity_proxy=0.8 + index,
            stopping_reason=("ITERATION_CAP", "BACKTRACK_FAIL", "NUMERICAL_FAIL")[index],
            converged=False, runtime_seconds=0.2 + index,
            pairwise_solution_distances=(float(index), float(index + 1), float(index + 2)),
        ) for index in range(3))
        error = candidate.NoConvergedStartError(
            "no finite converged optimizer start", failed_starts
        )
        successes = []
        for position in (60, 61):
            prefix_shape = (4, 8, position + 1)
            starts = tuple(replace(
                candidate.synthetic_start_result(index, 1.0 + index, converged=True),
                tensor=np.zeros(prefix_shape),
                pairwise_solution_distances=(0.0, 1.0, 2.0),
            ) for index in range(3))
            successes.append(candidate.PrefixOptimization(starts, 0))
        with mock.patch.object(candidate, "fit_anchor_local", return_value=local), \
             mock.patch.object(
                 candidate, "optimize_dw_tucker_prefix",
                 side_effect=[*successes, error],
             ):
            result = candidate.fit_dw_joint_tucker(fit, config=config, method_seed=81)
        self.assertEqual(result.status, "failure")
        failure = result.diagnostics["optimizer_failure"]
        self.assertEqual(failure["phase"], "validation")
        self.assertEqual(failure["lambda_t"], 0.0)
        self.assertEqual(failure["lambda_grid_index"], 0)
        self.assertEqual(failure["position"], 62)
        self.assertEqual(failure["date"], 142)
        self.assertEqual([item["position"] for item in failure["completed_prefixes"]], [60, 61])
        starts = failure["failing_prefix"]["starts"]
        self.assertEqual(len(starts), 3)
        self.assertEqual(starts[2]["stopping_reason"], "NUMERICAL_FAIL")
        self.assertEqual(starts[1]["objective_trace"], (5.0, 4.0))
        self.assertEqual(starts[0]["accepted_step_sizes"], (0.25,))
        self.assertEqual(starts[0]["pairwise_solution_distances"], (0.0, 1.0, 2.0))

    def test_public_fit_rejects_nonfrozen_optimizer_controls(self):
        fit = fixed_fit(seed=71, n=4, dates=120, window=80)
        base = R006EConfig(n=4, true_rank=4, fitted_rank=3)
        cases = (
            (replace(base, optimizer_iterations=299), "optimizer_iterations must equal 300"),
            (replace(base, objective_tolerance=2e-6), "objective_tolerance must equal 1e-6"),
            (replace(base, stationarity_tolerance=2e-4), "stationarity_tolerance must equal 1e-4"),
        )
        for config, message in cases:
            with self.subTest(message=message):
                result = candidate.fit_dw_joint_tucker(fit, config=config, method_seed=91)
                self.assertEqual(result.status, "failure")
                self.assertIn(message, result.diagnostics["error_message"])

    def test_public_fit_rejects_malformed_config_before_failure_path(self):
        fit = fixed_fit(seed=72, n=4, dates=120, window=80)
        with self.assertRaisesRegex(TypeError, "config must be a frozen R006e record"):
            candidate.fit_dw_joint_tucker(fit, config=object(), method_seed=91)

    def test_numpy_integer_config_is_normalized_before_failure_retention(self):
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
        config = R006EConfig(
            n=np.int64(4),
            t_len=np.int64(200),
            window=np.int64(80),
            true_rank=np.int64(4),
            fitted_rank=np.int64(3),
            horizon=np.int64(8),
            optimizer_starts=np.int64(3),
            optimizer_iterations=np.int64(300),
            family_pool_size=np.int64(64),
        )
        fit = fixed_fit(seed=73, n=4, dates=120, window=80)

        with mock.patch.object(
            candidate, "fit_anchor_local", side_effect=RuntimeError("forced failure")
        ):
            result = candidate.fit_dw_joint_tucker(
                fit, config=config, method_seed=91
            )

        self.assertTrue(all(type(getattr(config, name)) is int for name in integral_fields))
        self.assertEqual(result.status, "failure")
        self.assertEqual(result.diagnostics["error_type"], "RuntimeError")
        json.dumps(result.diagnostics.to_json_dict())

    def test_fixture_benchmark_is_outcome_free_and_writes_nothing(self):
        roots = (
            Path("output/high_impact_revision/r006e_native_supported_recovery"),
            Path("output/high_impact_revision/r006e_native_supported_recovery_repeat"),
        )

        def snapshot():
            return tuple(
                tuple(sorted(
                    (str(path.relative_to(root)), path.stat().st_size, path.stat().st_mtime_ns)
                    for path in root.rglob("*") if path.is_file()
                )) if root.exists() else ()
                for root in roots
            )

        before = snapshot()
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.experiments.r006e_dw_tucker", "--fixture-benchmark"],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(snapshot(), before)
        self.assertIn("OUTCOME_FREE_FIXTURE", completed.stdout)
        self.assertIn("iterations_per_second=", completed.stdout)
        self.assertIn("fixture_shape=6x12x18", completed.stdout)
        self.assertIn("extrapolation_basis=3_starts_x_(4x24+36)_prefixes_x_300_cap", completed.stdout)
        self.assertIn("projection_only=true", completed.stdout)
        self.assertIn("not_formal_runtime_evidence=true", completed.stdout)
        self.assertIn("excluded_overhead=gram+objective+backtracking", completed.stdout)
        self.assertIn("benchmark_n=6", completed.stdout)
        self.assertIn("optimizer_iteration_budget=118800", completed.stdout)
        self.assertIn("full_cap_first_trial_projection_calls=237996", completed.stdout)
        self.assertIn("full_cap_worst_case_projection_calls=3089196", completed.stdout)
        source = inspect.getsource(candidate.fixture_benchmark).lower()
        self.assertNotIn("build_native_panel", source)
        self.assertNotIn("generate_endpoint_panel", source)
        self.assertNotIn("open(", source)


if __name__ == "__main__":
    unittest.main()
