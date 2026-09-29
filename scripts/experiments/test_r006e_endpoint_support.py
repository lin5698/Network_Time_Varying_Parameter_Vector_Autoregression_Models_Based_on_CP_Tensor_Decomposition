import dataclasses
import inspect
import json
import unittest
from unittest import mock

import numpy as np

from scripts.experiments import r006e_endpoint_support as support
from scripts.experiments.r006d_endpoint_support import DesignSupportPath
from scripts.experiments.r006e_native_protocol import FitInputs, R006EConfig


class R006EEndpointSupportTest(unittest.TestCase):
    @staticmethod
    def config() -> R006EConfig:
        return R006EConfig(n=4, true_rank=4, fitted_rank=3)

    @staticmethod
    def fit_inputs(
        *, outcome_offset: float = 0.0, coefficient_dates=None
    ) -> FitInputs:
        rng = np.random.default_rng(610_003)
        predictors = rng.normal(size=(200, 4))
        topology = rng.uniform(0.05, 1.0, size=(200, 4, 4))
        topology /= topology.sum(axis=2, keepdims=True)
        return FitInputs(
            predictors=predictors,
            outcomes=rng.normal(size=(200, 4)) + outcome_offset,
            topology=topology,
            w_ref=np.full((4, 4), 0.25),
            coefficient_dates=(
                np.arange(80, 200)
                if coefficient_dates is None
                else np.asarray(coefficient_dates)
            ),
        )

    @staticmethod
    def interp_endpoint() -> np.ndarray:
        return np.array(
            [
                [0.0, 0.5, 0.3, 0.2],
                [0.2, 0.0, 0.5, 0.3],
                [0.3, 0.2, 0.0, 0.5],
                [0.5, 0.3, 0.2, 0.0],
            ]
        )

    @staticmethod
    def design(dates: np.ndarray, projector: np.ndarray) -> DesignSupportPath:
        count = len(dates)
        rank = int(round(np.trace(projector)))
        singular = np.arange(4.0, 0.0, -1.0)
        return DesignSupportPath(
            dates=np.asarray(dates),
            tau=np.full(count, 0.08),
            retained_rank=np.full(count, rank),
            singular_values=tuple(singular.copy() for _ in range(count)),
            projectors=tuple(projector.copy() for _ in range(count)),
        )

    @staticmethod
    def query_path(dates=None, *, chi: float = 0.01):
        selected_dates = (
            np.arange(80, 140) if dates is None else np.asarray(dates)
        )
        count = len(selected_dates)
        return support.QuerySupportPath(
            dates=selected_dates,
            chi=np.full(count, chi),
            amplification=np.full(count, 2.0),
            alpha=np.full(count, 0.5),
            retained_rank=np.full(count, 2),
            condition_number=np.full(count, 3.0),
            singular_values=tuple(
                np.array([3.0, 1.0]) for _ in range(count)
            ),
        )

    @classmethod
    def family_records(cls, path=None, endpoint=None):
        selected_path = cls.query_path() if path is None else path
        selected_endpoint = cls.interp_endpoint() if endpoint is None else endpoint
        return tuple(
            support.FamilyCandidateRecord(
                index=index,
                endpoint=(
                    selected_endpoint
                    if index == 0
                    else selected_endpoint + float(index)
                ),
                path=selected_path,
            )
            for index in range(64)
        )

    @classmethod
    def valid_construction_kwargs(cls):
        calibration = cls.query_path()
        prospective = cls.query_path(np.arange(140, 200))
        endpoint = cls.interp_endpoint()
        return dict(
            status="CONSTRUCTION_PASS",
            failure_reasons=(),
            w_alt_interp=endpoint,
            w_alt_family=endpoint,
            family_selected_index=0,
            interp_calibration=calibration,
            interp_prospective=prospective,
            family_calibration=calibration,
            family_prospective=prospective,
            family_candidates=cls.family_records(calibration, endpoint),
        )

    def test_family_selection_uses_lowest_supported_index(self):
        maxima = np.array([0.12, 0.08, 0.02])
        self.assertEqual(support.first_supported(maxima, threshold=0.10), 1)

    def test_family_selection_does_not_replace_lost_endpoint(self):
        self.assertEqual(
            support.availability_status(
                calibration_max=0.08,
                prospective_max=0.11,
                threshold=0.10,
            ),
            "lost_support",
        )

    def test_query_amplification_uses_absolute_gram_scale(self):
        gram = np.diag([4.0, 1.0])
        projector = np.eye(2)
        delta = np.eye(2)
        value = support.query_amplification(gram, projector, delta)
        expected = np.sqrt(1 / 4 + 1) / np.sqrt(2)
        self.assertAlmostEqual(value, expected)

    def test_signature_cannot_receive_outcomes_truth_or_endpoint_error(self):
        parameters = inspect.signature(
            support.construct_supported_endpoints
        ).parameters
        self.assertEqual(
            tuple(parameters),
            ("fit", "w_alt_interp", "family_seed", "config"),
        )
        self.assertNotIn("truth", parameters)
        self.assertNotIn("endpoint_error", parameters)

    def test_construction_never_reads_outcomes(self):
        source = inspect.getsource(support.construct_supported_endpoints)
        source += inspect.getsource(support._validate_inputs)
        self.assertNotIn(".outcomes", source)

    def test_constructs_exact_fixed_dates_and_all_64_certificates(self):
        endpoint = self.interp_endpoint()
        result = support.construct_supported_endpoints(
            self.fit_inputs(),
            w_alt_interp=endpoint,
            family_seed=610_064,
            config=self.config(),
        )

        np.testing.assert_array_equal(result.w_alt_interp, endpoint)
        np.testing.assert_array_equal(
            result.interp_calibration.dates, np.arange(80, 140)
        )
        np.testing.assert_array_equal(
            result.interp_prospective.dates, np.arange(140, 200)
        )
        self.assertEqual(len(result.family_candidates), 64)
        self.assertEqual(
            [record.index for record in result.family_candidates],
            list(range(64)),
        )
        for record in result.family_candidates:
            np.testing.assert_array_equal(record.path.dates, np.arange(80, 140))
            self.assertEqual(record.path.chi.shape, (60,))
        self.assertEqual(result.family_selected_index, 0)
        self.assertIsNotNone(result.w_alt_family)
        self.assertIsNotNone(result.family_calibration)
        self.assertIsNotNone(result.family_prospective)

    def test_query_paths_have_finite_shapes_absolute_spectra_and_alpha(self):
        result = support.construct_supported_endpoints(
            self.fit_inputs(),
            w_alt_interp=self.interp_endpoint(),
            family_seed=610_065,
            config=self.config(),
        )
        paths = (
            result.interp_calibration,
            result.interp_prospective,
            result.family_calibration,
            result.family_prospective,
        )
        for path in paths:
            self.assertIsNotNone(path)
            count = len(path.dates)
            for value in (
                path.chi,
                path.amplification,
                path.alpha,
                path.retained_rank,
                path.condition_number,
            ):
                self.assertEqual(value.shape, (count,))
                self.assertTrue(np.all(np.isfinite(value)))
            np.testing.assert_allclose(
                path.alpha,
                1.0 / np.maximum(path.amplification, 1e-12),
            )
            self.assertEqual(len(path.singular_values), count)
            self.assertTrue(
                all(np.all(values >= 0.0) for values in path.singular_values)
            )

    def test_records_make_defensive_read_only_copies(self):
        dates = np.array([80, 81])
        chi = np.array([0.01, 0.02])
        amplification = np.array([2.0, 4.0])
        alpha = np.array([0.5, 0.25])
        ranks = np.array([2, 2])
        conditions = np.array([3.0, 3.0])
        singular = (np.array([3.0, 1.0]), np.array([2.0, 1.0]))
        path = support.QuerySupportPath(
            dates=dates,
            chi=chi,
            amplification=amplification,
            alpha=alpha,
            retained_rank=ranks,
            condition_number=conditions,
            singular_values=singular,
        )
        dates[0] = 999
        chi[0] = 999.0
        singular[0][0] = 999.0
        self.assertEqual(path.dates[0], 80)
        self.assertEqual(path.chi[0], 0.01)
        self.assertEqual(path.singular_values[0][0], 3.0)
        for value in (
            path.dates,
            path.chi,
            path.amplification,
            path.alpha,
            path.retained_rank,
            path.condition_number,
            *path.singular_values,
        ):
            self.assertFalse(value.flags.writeable)
            with self.assertRaises(ValueError):
                value.flat[0] = 0
            with self.assertRaises(ValueError):
                value.setflags(write=True)

        endpoint = self.interp_endpoint()
        kwargs = self.valid_construction_kwargs()
        kwargs["w_alt_interp"] = endpoint
        construction = support.EndpointConstruction(**kwargs)
        endpoint[0, 0] = 999.0
        self.assertEqual(construction.w_alt_interp[0, 0], 0.0)
        self.assertFalse(construction.w_alt_interp.flags.writeable)
        self.assertFalse(construction.w_alt_family.flags.writeable)
        with self.assertRaises(ValueError):
            construction.w_alt_interp.setflags(write=True)
        with self.assertRaises(ValueError):
            construction.w_alt_family.setflags(write=True)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            construction.status = "CONSTRUCTION_PASS"

    def test_family_candidate_record_is_frozen_and_directly_json_serializable(self):
        endpoint = self.interp_endpoint()
        path = self.query_path()
        source_record = support.FamilyCandidateRecord(
            index=0, endpoint=endpoint, path=path
        )
        kwargs = self.valid_construction_kwargs()
        records = list(kwargs["family_candidates"])
        records[0] = source_record
        kwargs.update(
            w_alt_family=endpoint,
            family_calibration=path,
            family_candidates=tuple(records),
        )
        construction = support.EndpointConstruction(**kwargs)
        record = construction.family_candidates[0]
        endpoint[0, 0] = 999.0
        self.assertEqual(record.endpoint[0, 0], 0.0)
        with self.assertRaises(ValueError):
            record.endpoint.setflags(write=True)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            record.index = 1

        payload = record.to_json_dict()
        encoded = json.dumps(payload, sort_keys=True)
        self.assertIn('"index": 0', encoded)
        dict.__setitem__(payload, "index", 999)
        self.assertEqual(
            construction.family_candidates[0].to_json_dict()["index"], 0
        )

    def test_construction_rejects_invalid_candidate_certificates(self):
        valid = self.valid_construction_kwargs()
        cases = []
        cases.append({"family_candidates": valid["family_candidates"][:-1]})
        wrong_indices = list(valid["family_candidates"])
        wrong_indices[1] = support.FamilyCandidateRecord(
            index=7,
            endpoint=wrong_indices[1].endpoint,
            path=wrong_indices[1].path,
        )
        cases.append({"family_candidates": tuple(wrong_indices)})
        cases.append({"family_selected_index": 64})
        cases.append({"w_alt_family": self.interp_endpoint() + 1.0})
        cases.append({"family_calibration": self.query_path(chi=0.02)})
        wrong_dates = list(valid["family_candidates"])
        wrong_dates[2] = support.FamilyCandidateRecord(
            index=2,
            endpoint=wrong_dates[2].endpoint,
            path=self.query_path(np.arange(81, 141)),
        )
        cases.append({"family_candidates": tuple(wrong_dates)})
        for overrides in cases:
            with self.subTest(overrides=tuple(overrides)):
                with self.assertRaises(ValueError):
                    support.EndpointConstruction(**{**valid, **overrides})

    def test_construction_requires_exact_coefficient_dates(self):
        alternatives = (
            np.arange(79, 199),
            np.arange(80, 199),
            np.arange(81, 200),
        )
        for dates in alternatives:
            with self.subTest(first=int(dates[0]), count=len(dates)):
                with self.assertRaisesRegex(ValueError, "coefficient_dates"):
                    support.construct_supported_endpoints(
                        self.fit_inputs(coefficient_dates=dates),
                        w_alt_interp=self.interp_endpoint(),
                        family_seed=610_069,
                        config=self.config(),
                    )

    def test_exported_date_constants_cannot_be_mutated(self):
        original = tuple(support.CALIBRATION_DATES)
        try:
            with self.assertRaises(TypeError):
                support.CALIBRATION_DATES[0] = 999
        finally:
            if isinstance(support.CALIBRATION_DATES, np.ndarray):
                support.CALIBRATION_DATES[0] = original[0]
        self.assertIsInstance(support.CALIBRATION_DATES, tuple)
        result = support.construct_supported_endpoints(
            self.fit_inputs(),
            w_alt_interp=self.interp_endpoint(),
            family_seed=610_070,
            config=self.config(),
        )
        np.testing.assert_array_equal(
            result.interp_calibration.dates, np.arange(80, 140)
        )

    def test_family_pool_is_evaluated_once(self):
        source = inspect.getsource(support.construct_supported_endpoints)
        self.assertNotIn("evaluate_candidate_pool", source)

    def test_query_path_rejects_nonfinite_and_misaligned_values(self):
        kwargs = dict(
            dates=np.array([80, 81]),
            chi=np.array([0.01, 0.02]),
            amplification=np.array([2.0, 4.0]),
            alpha=np.array([0.5, 0.25]),
            retained_rank=np.array([2, 2]),
            condition_number=np.array([3.0, 3.0]),
            singular_values=(np.array([3.0, 1.0]), np.array([2.0, 1.0])),
        )
        with self.assertRaises(ValueError):
            support.QuerySupportPath(**{**kwargs, "chi": np.array([np.nan, 0.0])})
        with self.assertRaises(ValueError):
            support.QuerySupportPath(**{**kwargs, "alpha": np.array([1.0])})
        with self.assertRaises(ValueError):
            support.QuerySupportPath(
                **{**kwargs, "singular_values": (np.array([1.0]),)}
            )

    def test_fixed_selected_endpoint_is_not_redrawn_after_support_loss(self):
        fit = self.fit_inputs()
        endpoint = self.interp_endpoint()
        family_pool = np.stack([endpoint + index for index in range(64)])
        calibration_design = self.design(np.arange(80, 140), np.eye(4))
        prospective_design = self.design(np.arange(140, 200), np.zeros((4, 4)))

        with mock.patch.object(
            support, "generate_family_pool", return_value=family_pool
        ) as generate, mock.patch.object(
            support,
            "build_design_support_path",
            side_effect=(calibration_design, prospective_design),
        ):
            result = support.construct_supported_endpoints(
                fit,
                w_alt_interp=endpoint,
                family_seed=610_066,
                config=self.config(),
            )

        generate.assert_called_once_with(n=4, size=64, seed=610_066)
        self.assertEqual(result.family_selected_index, 0)
        np.testing.assert_array_equal(result.w_alt_family, family_pool[0])
        self.assertIn("family_lost_support_prospectively", result.failure_reasons)
        self.assertIn("interp_lost_support_prospectively", result.failure_reasons)
        self.assertEqual(result.status, "CONSTRUCTION_FAIL")

    def test_failure_reasons_cover_interp_calibration_and_missing_family(self):
        zero_design = self.design(np.arange(80, 140), np.zeros((4, 4)))
        prospective_design = self.design(np.arange(140, 200), np.zeros((4, 4)))
        with mock.patch.object(
            support,
            "build_design_support_path",
            side_effect=(zero_design, prospective_design),
        ):
            result = support.construct_supported_endpoints(
                self.fit_inputs(),
                w_alt_interp=self.interp_endpoint(),
                family_seed=610_067,
                config=self.config(),
            )
        self.assertEqual(result.status, "CONSTRUCTION_FAIL")
        self.assertIn(
            "interp_not_supported_in_calibration", result.failure_reasons
        )
        self.assertIn("no_supported_family_candidate", result.failure_reasons)
        self.assertIsNone(result.family_selected_index)
        self.assertIsNone(result.w_alt_family)
        self.assertEqual(len(result.family_candidates), 64)

    def test_outcome_perturbation_cannot_change_construction(self):
        config = self.config()
        left = support.construct_supported_endpoints(
            self.fit_inputs(outcome_offset=0.0),
            w_alt_interp=self.interp_endpoint(),
            family_seed=610_068,
            config=config,
        )
        right = support.construct_supported_endpoints(
            self.fit_inputs(outcome_offset=1e100),
            w_alt_interp=self.interp_endpoint(),
            family_seed=610_068,
            config=config,
        )

        self.assertEqual(left.status, right.status)
        self.assertEqual(left.failure_reasons, right.failure_reasons)
        self.assertEqual(left.family_selected_index, right.family_selected_index)
        for name in ("w_alt_interp", "w_alt_family"):
            np.testing.assert_array_equal(getattr(left, name), getattr(right, name))
        for name in (
            "interp_calibration",
            "interp_prospective",
            "family_calibration",
            "family_prospective",
        ):
            self.assert_paths_equal(getattr(left, name), getattr(right, name))
        self.assertEqual(len(left.family_candidates), len(right.family_candidates))
        for left_record, right_record in zip(
            left.family_candidates, right.family_candidates
        ):
            self.assertEqual(left_record.index, right_record.index)
            np.testing.assert_array_equal(
                left_record.endpoint, right_record.endpoint
            )
            self.assert_paths_equal(left_record.path, right_record.path)
            self.assertEqual(
                left_record.to_json_dict(), right_record.to_json_dict()
            )

    def assert_paths_equal(self, left, right):
        if left is None or right is None:
            self.assertIs(left, right)
            return
        for field in dataclasses.fields(left):
            a = getattr(left, field.name)
            b = getattr(right, field.name)
            if isinstance(a, tuple):
                for x, y in zip(a, b):
                    np.testing.assert_array_equal(x, y)
            else:
                np.testing.assert_array_equal(a, b)


if __name__ == "__main__":
    unittest.main()
