"""Fixture-only checks for the E3 synthetic core.

These tests exercise small deterministic construction examples. They are not
the authorized E3 recovery grid, do not write an outcome directory, and do not
produce manuscript-eligible evidence.
"""

from __future__ import annotations

import inspect
from fractions import Fraction
import unittest
from unittest import mock

import numpy as np

from scripts.experiments import e3_synthetic_core as core


class E3SyntheticCoreFixtureTests(unittest.TestCase):
    def test_exact_query_transfer_fixture_inventory(self) -> None:
        report = core.exact_query_transfer_fixture_report()
        self.assertEqual(report["f1_negative"]["status"], core.STATUS_OUTSIDE_TARGET)
        self.assertEqual(report["f2_unrestricted_negative"]["status"], core.STATUS_OUTSIDE_TARGET)
        self.assertEqual(report["f2_diagonal_negative"]["status"], core.STATUS_OUTSIDE_TARGET)
        self.assertEqual(report["f2_diagonal_positive"]["status"], core.STATUS_AVAILABLE)
        self.assertEqual(report["f2_diagonal_positive"]["row_ranks"], [3, 3, 3])
        self.assertEqual(report["non_equivalence"]["status"], "DISTINCT_FAMILY")

    def test_domain_stability_certificate_covers_both_families_and_all_fixture_cases(self) -> None:
        projection_parameters = inspect.signature(
            core.project_blocks_to_stability_envelope
        ).parameters
        self.assertEqual(tuple(projection_parameters), ("blocks", "envelope"))

        report = core.domain_stability_fixture_report()

        self.assertEqual(report["status"], core.STATUS_AVAILABLE)
        self.assertEqual(report["envelope"], 0.90)
        self.assertEqual(report["families"], [core.FAMILY1, core.FAMILY2])
        self.assertEqual(
            report["coefficient_cases"],
            ["zero", "boundary", "projected"],
        )
        self.assertEqual(
            report["topology_cases"],
            ["signed_row_normalized", "directed_sparse", "latent_position"],
        )
        self.assertEqual(report["checked_endpoints"], 18)
        self.assertLessEqual(report["max_projected_block_norm"], 0.90 + 1e-12)
        self.assertLessEqual(report["max_spectral_radius"], 0.90 + 1e-12)

    def test_exact_domain_stability_certificate_uses_rational_row_sum_bounds(self) -> None:
        report = core.exact_domain_stability_certificate_report()

        self.assertEqual(report["status"], core.STATUS_AVAILABLE)
        self.assertEqual(report["arithmetic"], "fractions.Fraction")
        self.assertEqual(report["envelope"], "9/10")
        self.assertEqual(report["checked_operators"], 18)
        self.assertEqual(report["max_projected_block_norm"], "9/10")
        self.assertLessEqual(
            Fraction(report["max_operator_infinity_norm"]),
            Fraction(9, 10),
        )
        self.assertTrue(report["spectral_radius_bound_follows_from_induced_norm"])

    def test_second_order_operator_uses_raw_matrix_square(self) -> None:
        topology = np.array(
            [
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.0],
            ]
        )
        blocks = np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
            ]
        )
        operator = core._diagonal_blocks_to_operator(core.FAMILY2, blocks, topology)
        self.assertTrue(np.array_equal(operator, np.diag(blocks[2]) @ (topology @ topology)))
        self.assertEqual(operator[0, 2], 1.0)

    def test_collapsed_control_has_no_numeric_endpoint(self) -> None:
        endpoint = core.collapsed_endpoint_control()
        self.assertEqual(endpoint.status, core.STATUS_OUTSIDE_TARGET)
        self.assertIsNone(endpoint.blocks)
        self.assertIsNone(endpoint.operator)
        self.assertIsNone(endpoint.responses)

    def test_validation_selection_interface_has_no_query_argument(self) -> None:
        parameters = inspect.signature(core.select_hyperparameter).parameters
        self.assertEqual(tuple(parameters), ("fit_data", "method"))

    def test_native_endpoint_retains_complete_family_two_response(self) -> None:
        topology = np.array(
            [
                [0.0, 0.5, 0.0],
                [0.0, 0.0, 0.5],
                [0.5, 0.0, 0.0],
            ]
        )
        blocks = np.array(
            [
                [0.12, 0.13, 0.14],
                [0.10, 0.10, 0.10],
                [0.06, 0.06, 0.06],
            ]
        )
        endpoint = core._native_endpoint(
            core.FAMILY2, blocks, topology, 4, stability_threshold=0.98
        )
        self.assertEqual(endpoint.status, core.STATUS_AVAILABLE)
        assert endpoint.operator is not None
        assert endpoint.responses is not None
        self.assertEqual(endpoint.operator.shape, (3, 3))
        self.assertEqual(endpoint.responses.shape, (4, 3, 3))

    def test_native_path_requires_query_only_at_evaluation(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY1, config, seed=4101)
        fit_data = core.fit_data_from_panel(panel)
        path = core.fit_native_path(fit_data, "local_structured", 8)
        endpoint = path.evaluate(
            panel.query_topologies["in_family_interpolation"][config.validation_stop],
            4,
            config.validation_stop,
        )
        self.assertIn(endpoint.status, core.STATUS_SCHEMA)

    def test_native_fit_enforces_query_independent_domain_stability_envelope(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        topology = np.zeros((config.n, config.n), dtype=float)
        for node in range(config.n):
            topology[node, (node + 1) % config.n] = 1.0
        observed = np.repeat(topology[None, :, :], config.total_time, axis=0)
        responses = np.zeros((config.total_time, config.n), dtype=float)
        responses[80] = 1.0
        for time in range(81, config.total_time):
            responses[time] = 1.5 * responses[time - 1]
        fit_data = core.FitData(
            family=core.FAMILY2,
            config=config,
            seed=9901,
            observed_topologies=observed,
            responses=responses,
        )

        path = core.fit_native_path(fit_data, "local_structured", 8)
        endpoint = path.evaluate(topology, 4, config.validation_stop)

        self.assertEqual(endpoint.status, core.STATUS_AVAILABLE)
        assert endpoint.blocks is not None
        self.assertLessEqual(
            float(np.max(np.sum(np.abs(endpoint.blocks), axis=0))),
            0.90 + 1e-12,
        )
        assert endpoint.spectral_radius is not None
        self.assertLessEqual(endpoint.spectral_radius, 0.90 + 1e-12)

    def test_selection_evaluation_and_recursive_bootstrap_share_the_frozen_envelope(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4107)
        fit_data = core.fit_data_from_panel(panel)
        real_projection = core.project_blocks_to_stability_envelope
        observed_envelopes: list[float] = []

        def trace_projection(blocks: np.ndarray, envelope: float) -> np.ndarray:
            projected = real_projection(blocks, envelope)
            observed_envelopes.append(envelope)
            self.assertLessEqual(
                float(np.max(np.sum(np.abs(projected), axis=0))),
                envelope + 1e-12,
            )
            return projected

        with mock.patch.object(
            core,
            "project_blocks_to_stability_envelope",
            side_effect=trace_projection,
        ):
            selection = core.select_hyperparameter(fit_data, "fixed_rank_basis")
            selection_calls = len(observed_envelopes)
            self.assertGreater(selection_calls, 0)

            path = core.fit_native_path(fit_data, "fixed_rank_basis", 1)
            endpoint = path.evaluate(
                panel.query_topologies["cross_generator"][config.validation_stop],
                4,
                config.validation_stop,
            )
            evaluation_calls = len(observed_envelopes) - selection_calls
            self.assertGreater(evaluation_calls, 0)
            self.assertEqual(endpoint.status, core.STATUS_AVAILABLE)

            bootstrap_selection = core.SelectionResult(
                "fixed_rank_basis", 1, 0.0, core.STATUS_AVAILABLE, (0.0,)
            )
            before_bootstrap = len(observed_envelopes)
            core._recursive_bootstrap_fit_data(
                panel,
                "fixed_rank_basis",
                bootstrap_selection,
                18,
                np.random.default_rng(9205),
            )
            self.assertGreater(len(observed_envelopes) - before_bootstrap, 0)

        self.assertEqual(set(observed_envelopes), {config.stability_envelope})

    def test_public_e3_paths_are_gated_and_internal_fit_helpers_are_not_public(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY1, config, seed=4101)
        fit_data = core.fit_data_from_panel(panel)
        path = core.fit_native_path(fit_data, "local_structured", 8)
        bad_report = core.exact_query_transfer_fixture_report()
        bad_report["f2_diagonal_positive"] = {"status": core.STATUS_OUTSIDE_TARGET}
        with mock.patch.object(core, "exact_query_transfer_fixture_report", return_value=bad_report):
            with self.assertRaisesRegex(core.E3SyntheticError, "E3-1 gate"):
                core.make_synthetic_panel(core.FAMILY1, config, seed=4102)
            with self.assertRaisesRegex(core.E3SyntheticError, "E3-1 gate"):
                core.fit_native_path(fit_data, "local_structured", 8)
            with self.assertRaisesRegex(core.E3SyntheticError, "E3-1 gate"):
                core.select_hyperparameter(fit_data, "local_structured")
            with self.assertRaisesRegex(core.E3SyntheticError, "E3-1 gate"):
                path.evaluate(panel.observed_topologies[config.validation_stop], 4, config.validation_stop)
            with self.assertRaisesRegex(core.E3SyntheticError, "E3-1 gate"):
                core.evaluate_method_at_query(
                    panel,
                    "local_structured",
                    core.SelectionResult(
                        "local_structured", None, None, core.STATUS_NONCONVERGED, (None,)
                    ),
                    "in_family_interpolation",
                    config.validation_stop,
                    4,
                )

        self.assertFalse(hasattr(core, "FittedNativePath"))
        self.assertFalse(hasattr(core, "estimate_native_blocks"))
        self.assertFalse(hasattr(core, "native_endpoint"))
        self.assertFalse(hasattr(core, "diagonal_blocks_to_operator"))

    def test_small_synthetic_fixture_preserves_statuses_without_result_writing(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4101)
        selection = core.select_hyperparameter(core.fit_data_from_panel(panel), "local_structured")
        self.assertIn(selection.status, core.STATUS_SCHEMA)
        record = core.evaluate_method_at_query(
            panel,
            "local_structured",
            selection,
            "in_family_interpolation",
            int(config.validation_stop),
            4,
        )
        self.assertIn(record.status, core.STATUS_SCHEMA)
        if record.status != core.STATUS_AVAILABLE:
            self.assertIsNone(record.operator_mse)
            self.assertIsNone(record.response_mse)
        self.assertIsNotNone(record.truth_spectral_radius)

    def test_panel_recovery_accepts_paths_cached_from_the_same_panel(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4104)
        selections = {
            "local_structured": core.SelectionResult(
                "local_structured", 8, 0.0, core.STATUS_AVAILABLE, (0.0,)
            ),
            "causal_temporal_smoother": core.SelectionResult(
                "causal_temporal_smoother", 0.25, 0.0, core.STATUS_AVAILABLE, (0.0,)
            ),
            "fixed_rank_basis": core.SelectionResult(
                "fixed_rank_basis", 1, 0.0, core.STATUS_AVAILABLE, (0.0,)
            ),
        }

        def zero_blocks(*_args: object, **_kwargs: object) -> np.ndarray:
            return np.zeros((core.coefficient_block_count(panel.family), panel.config.n), dtype=float)

        def stable_endpoint(
            family: core.Family,
            blocks: np.ndarray,
            _query: np.ndarray,
            horizon: int,
            *,
            stability_threshold: float,
        ) -> core.Endpoint:
            del family, stability_threshold
            operator = np.zeros((panel.config.n, panel.config.n), dtype=float)
            responses = np.zeros((horizon, panel.config.n, panel.config.n), dtype=float)
            return core.Endpoint(
                core.STATUS_AVAILABLE,
                "stable fixture endpoint",
                np.asarray(blocks, dtype=float).copy(),
                operator,
                responses,
                0.0,
            )

        with (
            mock.patch.object(
                core,
                "_select_hyperparameter",
                side_effect=lambda _fit_data, method: selections[method],
            ),
            mock.patch.object(core, "_estimate_native_blocks", side_effect=zero_blocks),
            mock.patch.object(core, "_native_endpoint", side_effect=stable_endpoint),
        ):
            records = core.evaluate_panel_recovery(panel)

        expected_records = (
            len(core.METHODS)
            * len(core.QUERY_CLASSES)
            * len(config.horizons)
            * len(config.evaluation_indices)
        )
        self.assertEqual(len(records), expected_records)
        self.assertTrue(all(record.status == core.STATUS_AVAILABLE for record in records))

    def test_fixed_rank_bootstrap_refit_schedule_is_rank_aware(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)

        schedules = {
            rank: core.fixed_rank_bootstrap_refit_schedule(config, rank, target_time=143)
            for rank in config.basis_ranks
        }

        self.assertEqual(schedules[1].first_refit_time, 14)
        self.assertEqual(schedules[2].first_refit_time, 14)
        self.assertEqual(schedules[3].first_refit_time, 15)
        self.assertTrue(all(schedule.valid_refit_count >= 2 for schedule in schedules.values()))
        self.assertNotIn(13, schedules[1].refit_times)
        self.assertNotIn(13, schedules[2].refit_times)
        self.assertNotIn(13, schedules[3].refit_times)

    def test_recursive_bootstrap_rebuilds_lags_from_pseudo_history(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4105)
        selection = core.SelectionResult(
            "fixed_rank_basis", 1, 0.0, core.STATUS_AVAILABLE, (0.0,)
        )
        target_time = 18
        schedule = core.fixed_rank_bootstrap_refit_schedule(
            config, 1, target_time=target_time
        )
        residual_outputs = np.stack(
            [np.full(config.n, 0.01 * (index + 1)) for index in range(len(schedule.refit_times))]
        )

        with mock.patch.object(
            core,
            "_method_predictions_before_target",
            return_value=(np.zeros_like(residual_outputs), residual_outputs),
        ), mock.patch.object(
            core,
            "_moving_block_indices",
            return_value=np.arange(len(schedule.refit_times), dtype=int)[::-1],
        ):
            pseudo_fit_data = core._recursive_bootstrap_fit_data(
                panel,
                "fixed_rank_basis",
                selection,
                target_time,
                np.random.default_rng(9203),
            )

        pseudo_features = core._panel_features(pseudo_fit_data)
        original_features = core._panel_features(core.fit_data_from_panel(panel))
        recursive_times = np.asarray(schedule.refit_times, dtype=int)
        self.assertIsNot(pseudo_fit_data.responses, panel.responses)
        self.assertFalse(
            np.allclose(
                pseudo_fit_data.responses[recursive_times],
                panel.responses[recursive_times],
            )
        )
        for time in recursive_times[1:]:
            expected = core._feature_vector(
                panel.family,
                pseudo_fit_data.responses[time - 1],
                panel.observed_topologies[time],
            )
            self.assertTrue(np.allclose(pseudo_features[time], expected))
        changed_previous = next(
            int(time)
            for time in recursive_times[1:]
            if not np.allclose(
                pseudo_fit_data.responses[time - 1], panel.responses[time - 1]
            )
        )
        self.assertFalse(
            np.allclose(
                pseudo_features[changed_previous], original_features[changed_previous]
            )
        )

    def test_interval_retunes_and_rebuilds_features_for_every_pseudo_series(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4106)
        selection = core.SelectionResult(
            "fixed_rank_basis", 1, 0.0, core.STATUS_AVAILABLE, (0.0,)
        )
        baseline = core.EvaluationRecord(
            family=panel.family,
            n=panel.config.n,
            seed=panel.seed,
            method="fixed_rank_basis",
            query_class="cross_generator",
            target_time=config.validation_stop,
            horizon=4,
            status=core.STATUS_AVAILABLE,
            operator_mse=0.0,
            response_mse=0.0,
            estimated_spectral_radius=0.2,
            truth_spectral_radius=0.2,
            selected_hyperparameter=1,
            validation_loss=0.0,
        )
        pseudo_fit_data_seen: list[core.FitData] = []
        feature_fit_data_seen: list[core.FitData] = []

        def recursive_fit_data(*_args: object, **_kwargs: object) -> core.FitData:
            responses = panel.responses.copy()
            responses[14] += 0.1 + 0.01 * len(pseudo_fit_data_seen)
            return core.FitData(
                family=panel.family,
                config=panel.config,
                seed=panel.seed,
                observed_topologies=panel.observed_topologies,
                responses=responses,
            )

        def retune(fit_data: core.FitData, method: core.Method) -> core.SelectionResult:
            self.assertEqual(method, "fixed_rank_basis")
            self.assertIsNot(fit_data.responses, panel.responses)
            pseudo_fit_data_seen.append(fit_data)
            return selection

        real_panel_features = core._panel_features

        def record_panel_features(fit_data: core.FitData) -> np.ndarray:
            feature_fit_data_seen.append(fit_data)
            return real_panel_features(fit_data)

        def stable_endpoint(
            family: core.Family,
            blocks: np.ndarray,
            _query: np.ndarray,
            horizon: int,
            *,
            stability_threshold: float,
        ) -> core.Endpoint:
            del family, stability_threshold
            operator = np.zeros((panel.config.n, panel.config.n), dtype=float)
            responses = np.zeros((horizon, panel.config.n, panel.config.n), dtype=float)
            return core.Endpoint(
                core.STATUS_AVAILABLE,
                "stable fixture endpoint",
                np.asarray(blocks, dtype=float).copy(),
                operator,
                responses,
                0.0,
            )

        def zero_blocks(*_args: object, **_kwargs: object) -> np.ndarray:
            return np.zeros(
                (core.coefficient_block_count(panel.family), panel.config.n), dtype=float
            )

        with (
            mock.patch.object(core, "_evaluate_method_at_query", return_value=baseline),
            mock.patch.object(core, "_recursive_bootstrap_fit_data", side_effect=recursive_fit_data),
            mock.patch.object(core, "_select_hyperparameter", side_effect=retune),
            mock.patch.object(core, "_panel_features", side_effect=record_panel_features),
            mock.patch.object(core, "_estimate_native_blocks", side_effect=zero_blocks),
            mock.patch.object(core, "_native_endpoint", side_effect=stable_endpoint),
        ):
            interval = core.simultaneous_response_interval(
                panel,
                selection,
                "cross_generator",
                config.validation_stop,
                bootstrap_seed=9204,
            )

        self.assertEqual(len(pseudo_fit_data_seen), config.bootstrap_replicates)
        pseudo_ids = {id(fit_data.responses) for fit_data in pseudo_fit_data_seen}
        self.assertEqual(len(pseudo_ids), config.bootstrap_replicates)
        feature_ids = {id(fit_data.responses) for fit_data in feature_fit_data_seen}
        self.assertTrue(pseudo_ids.issubset(feature_ids))
        self.assertEqual(interval["bootstrap_retune_attempts"], config.bootstrap_replicates)

    def test_bootstrap_records_every_replicate_status_and_targets_r4(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4102)
        selection = core.select_hyperparameter(core.fit_data_from_panel(panel), "fixed_rank_basis")
        interval = core.simultaneous_response_interval(
            panel,
            selection,
            "cross_generator",
            config.validation_stop,
            bootstrap_seed=9201,
        )
        counts = interval["bootstrap_status_counts"]
        self.assertIsInstance(counts, dict)
        assert isinstance(counts, dict)
        expected_count = config.bootstrap_replicates if selection.status == core.STATUS_AVAILABLE else 0
        self.assertEqual(sum(counts.values()), expected_count)
        self.assertIn(interval["status"], core.STATUS_SCHEMA)

    def test_any_failed_bootstrap_replicate_invalidates_the_interval(self) -> None:
        config = core.E3SyntheticConfig(n=4, bootstrap_replicates=3)
        panel = core.make_synthetic_panel(core.FAMILY2, config, seed=4103)
        selection = core.SelectionResult(
            "fixed_rank_basis", 1, 0.0, core.STATUS_AVAILABLE, (0.0,)
        )
        baseline = core.EvaluationRecord(
            family=panel.family,
            n=panel.config.n,
            seed=panel.seed,
            method="fixed_rank_basis",
            query_class="cross_generator",
            target_time=config.validation_stop,
            horizon=4,
            status=core.STATUS_AVAILABLE,
            operator_mse=0.0,
            response_mse=0.0,
            estimated_spectral_radius=0.2,
            truth_spectral_radius=0.2,
            selected_hyperparameter=1,
            validation_loss=0.0,
        )
        calls = 0

        def fail_first_bootstrap(*_args: object, **_kwargs: object) -> np.ndarray:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise core.E3SyntheticError("forced bootstrap failure")
            return panel.responses.copy()

        def stable_endpoint(
            family: core.Family,
            blocks: np.ndarray,
            _query: np.ndarray,
            horizon: int,
            *,
            stability_threshold: float,
        ) -> core.Endpoint:
            del family, stability_threshold
            operator = np.zeros((panel.config.n, panel.config.n), dtype=float)
            responses = np.zeros((horizon, panel.config.n, panel.config.n), dtype=float)
            return core.Endpoint(
                core.STATUS_AVAILABLE,
                "stable fixture endpoint",
                np.asarray(blocks, dtype=float).copy(),
                operator,
                responses,
                0.0,
            )

        def zero_blocks(*_args: object, **_kwargs: object) -> np.ndarray:
            return np.zeros((core.coefficient_block_count(panel.family), panel.config.n), dtype=float)

        with (
            mock.patch.object(core, "_evaluate_method_at_query", return_value=baseline),
            mock.patch.object(core, "_estimate_native_blocks", side_effect=zero_blocks),
            mock.patch.object(core, "_native_endpoint", side_effect=stable_endpoint),
            mock.patch.object(core, "_bootstrap_outputs", side_effect=fail_first_bootstrap),
        ):
            interval = core.simultaneous_response_interval(
                panel,
                selection,
                "cross_generator",
                config.validation_stop,
                bootstrap_seed=9202,
            )

        self.assertNotEqual(interval["status"], core.STATUS_AVAILABLE)
        self.assertIsNone(interval["coverage"])
        self.assertIsNone(interval["mean_interval_width"])
        self.assertGreater(interval["bootstrap_status_counts"][core.STATUS_NONCONVERGED], 0)

    def test_common_completion_keeps_failure_statuses_out_of_numeric_pairs(self) -> None:
        available = core.EvaluationRecord(
            family=core.FAMILY1,
            n=20,
            seed=4101,
            method="fixed_rank_basis",
            query_class="cross_generator",
            target_time=96,
            horizon=4,
            status=core.STATUS_AVAILABLE,
            operator_mse=0.2,
            response_mse=0.3,
            estimated_spectral_radius=0.5,
            truth_spectral_radius=0.4,
            selected_hyperparameter=1,
            validation_loss=0.1,
        )
        unavailable = core.EvaluationRecord(
            family=core.FAMILY1,
            n=20,
            seed=4101,
            method="local_structured",
            query_class="cross_generator",
            target_time=96,
            horizon=4,
            status=core.STATUS_UNSTABLE,
            operator_mse=None,
            response_mse=None,
            estimated_spectral_radius=1.0,
            truth_spectral_radius=0.4,
            selected_hyperparameter=8,
            validation_loss=0.1,
        )
        paired = core.paired_common_completion(
            (available, unavailable),
            candidate_method="fixed_rank_basis",
            comparator_method="local_structured",
        )
        self.assertEqual(paired["declared_date_keys"], 1)
        self.assertEqual(paired["common_completion_date_keys"], 0)
        self.assertEqual(paired["comparator_status_counts"][core.STATUS_UNSTABLE], 1)


if __name__ == "__main__":
    unittest.main()
