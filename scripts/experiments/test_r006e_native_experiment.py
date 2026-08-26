"""Contract tests for the phase-locked R006e experiment runner."""

import copy
import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import subprocess
from concurrent.futures import ThreadPoolExecutor
import os

import numpy as np

from scripts.experiments import r006e_native_experiment as experiment
from scripts.experiments import r006e_native_metrics as metrics
from scripts.experiments import r006c_endpoint_protocol as r006c


class R006ENativeExperimentTest(unittest.TestCase):
    def test_screening_csv_freezes_complete_evaluator_and_runner_schema(self):
        self.assertEqual(
            experiment.SCREENING_CSV_FIELDS,
            (
                "seed", "rho", "a3", "eta",
                *metrics.EVALUATOR_ROW_FIELDS,
                "peak_memory_bytes", "peak_memory_scope",
                "peak_memory_worker_pid",
            ),
        )

    @staticmethod
    def _passing_screening_rows():
        rows = []
        for seed in experiment.SCREENING_SEEDS:
            for rho, a3, eta in experiment.primary_cells():
                for method in experiment.METHODS:
                    candidate = method == "dw_joint_tucker333"
                    evaluator = {
                        field: (
                            "value" if field in metrics.EVALUATOR_STRING_FIELDS
                            else 1 if field in metrics.EVALUATOR_INTEGER_FIELDS
                            else 0.5
                        )
                        for field in metrics.EVALUATOR_ROW_FIELDS
                    }
                    evaluator.update({
                        "method": method,
                        "fit_sha256": "a" * 64,
                        "parameterization": "anchor",
                        "failure_code": None,
                        "failure_reason": None,
                        "fit_diagnostics_json": (
                            '{"evaluation":[{"selected_start_index":0,'
                            '"starts":[{"converged":true,'
                            '"objective_trace":[2.0,1.0]}]}],"status":"success"}'
                            if candidate else '{"status":"success"}'
                        ),
                        "endpoint_construction_status": "CONSTRUCTION_PASS",
                        "endpoint_failure_reasons_json": "[]",
                        "runtime_seconds": 0.25,
                        "observed_topology_prediction_rmse": 1.0 if candidate else 1.1,
                        "w_ref_raw_response_error_mean": 1.0 if candidate else 1.1,
                        "evaluation_date_start": 164,
                        "evaluation_date_end": 199,
                        "evaluation_dates": 36,
                    })
                    if not candidate:
                        evaluator["at_least_one_converged_start"] = 0
                        evaluator["selected_objective_trace_nonincreasing"] = 0
                    for endpoint in ("w_ref", "w_alt_interp", "w_alt_family"):
                        evaluator[f"{endpoint}_availability_status"] = "available"
                    for endpoint in ("w_alt_interp", "w_alt_family"):
                        evaluator[f"{endpoint}_raw_response_error_mean"] = 0.8 if candidate else 1.0
                    row = {
                        "seed": seed, "rho": rho, "a3": a3, "eta": eta,
                        **evaluator,
                        "peak_memory_bytes": 1024,
                        "peak_memory_scope": "fresh_worker_process_peak_rss",
                        "peak_memory_worker_pid": 12345,
                    }
                    rows.append(row)
        return rows

    @staticmethod
    def _as_failed_evaluator_row(row):
        failed = copy.deepcopy(row)
        intended_dates = list(range(80, 200))
        failed.update({
            "fit_success": 0,
            "scorable": 0,
            "selected_hyperparameter": None,
            "at_least_one_converged_start": 0,
            "selected_objective_trace_nonincreasing": 0,
            "failure_code": "SyntheticFailure",
            "failure_reason": "synthetic fit failed",
            "fit_diagnostics_json": json.dumps({
                "status": "failure",
                "error_type": "SyntheticFailure",
                "error_message": "synthetic fit failed",
                "method_seed": 123,
                "intended_dates": intended_dates,
                "intended_count": len(intended_dates),
                "expected_tensor_shape": [10, 20, len(intended_dates)],
            }, separators=(",", ":"), sort_keys=True),
        })
        for field in metrics.EVALUATOR_NULLABLE_FIELDS:
            if (
                field not in {"failure_code", "failure_reason"}
                and (
                    field in metrics.MECHANISM_AND_EVALUATION_FIELDS
                    or any(
                        field == f"{endpoint}_{metric}"
                        for endpoint in metrics.ENDPOINT_NAMES
                        for metric in metrics.ENDPOINT_METRICS
                    )
                )
            ):
                failed[field] = None
        return failed

    @classmethod
    def _successful_evaluator_payload(cls):
        row = cls._passing_screening_rows()[0]
        return {field: row[field] for field in metrics.EVALUATOR_ROW_FIELDS}

    @staticmethod
    def _write_screening_csv(path, rows):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=experiment.SCREENING_CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _screening_csv_bytes(rows, fields=None):
        handle = io.StringIO(newline="")
        writer = csv.DictWriter(
            handle, fieldnames=fields or experiment.SCREENING_CSV_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
        return handle.getvalue().encode("utf-8")

    def test_screening_csv_strictly_parses_every_frozen_field(self):
        rows = self._passing_screening_rows()
        parsed = experiment._parse_screening_replications(
            self._screening_csv_bytes(rows)
        )
        self.assertEqual(len(parsed), 320)
        self.assertEqual(tuple(parsed[0]), experiment.SCREENING_CSV_FIELDS)
        self.assertIsNone(parsed[0]["failure_code"])
        self.assertEqual(
            parsed[0]["peak_memory_scope"], "fresh_worker_process_peak_rss"
        )

    def test_screening_csv_rejects_header_schema_variants(self):
        rows = self._passing_screening_rows()
        fields = experiment.SCREENING_CSV_FIELDS
        variants = {
            "missing": fields[:-1],
            "unknown": (*fields, "unfrozen_field"),
            "duplicate": (*fields[:-1], fields[-2]),
        }
        for label, variant in variants.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, "header mismatch"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows, variant)
                )

    def test_screening_csv_rejects_hidden_scientific_and_resource_tamper(self):
        cases = {
            "nonfinite hidden metric": ("m_ref_relative_error_mean", float("nan"), "nonfinite"),
            "negative hidden metric": ("m_ref_relative_error_mean", -0.1, "negative"),
            "wrong memory scope": ("peak_memory_scope", "process_rss", "peak-memory scope"),
            "zero worker pid": ("peak_memory_worker_pid", 0, "zero integer"),
        }
        for label, (field, value, message) in cases.items():
            rows = self._passing_screening_rows()
            rows[0][field] = value
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, message
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_rejects_noncanonical_fit_digest(self):
        rows = self._passing_screening_rows()
        rows[0]["fit_sha256"] = "A" * 64
        with self.assertRaisesRegex(RuntimeError, "fit_sha256"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_non_anchor_parameterization(self):
        rows = self._passing_screening_rows()
        rows[0]["parameterization"] = "native"
        with self.assertRaisesRegex(RuntimeError, "parameterization"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_malformed_or_wrong_json_containers(self):
        cases = {
            "malformed diagnostics": ("fit_diagnostics_json", "{"),
            "diagnostics list": ("fit_diagnostics_json", "[]"),
            "nonfinite diagnostics": (
                "fit_diagnostics_json", '{"loss":NaN,"status":"success"}'
            ),
            "overflow diagnostics": (
                "fit_diagnostics_json",
                '{"nested":{"losses":[0.5,1e999]},"status":"success"}',
            ),
            "failure reasons object": ("endpoint_failure_reasons_json", "{}"),
            "non-string failure reason": ("endpoint_failure_reasons_json", "[1]"),
        }
        for label, (field, value) in cases.items():
            rows = self._passing_screening_rows()
            rows[0][field] = value
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, field
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_rejects_invalid_construction_state(self):
        cases = {
            "unknown status": ("PASS", "[]"),
            "pass with failure": (
                "CONSTRUCTION_PASS", '["interp_lost_support_prospectively"]'
            ),
            "fail without failure": ("CONSTRUCTION_FAIL", "[]"),
            "unknown failure": ("CONSTRUCTION_FAIL", '["unknown_reason"]'),
        }
        for label, (status, reasons) in cases.items():
            rows = self._passing_screening_rows()
            rows[0]["endpoint_construction_status"] = status
            rows[0]["endpoint_failure_reasons_json"] = reasons
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, "construction|failure"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_rejects_inconsistent_endpoint_availability(self):
        cases = {
            "unknown status": ("w_alt_interp", 1, "value"),
            "reference unavailable": ("w_ref", 0, "lost_support"),
            "available with zero flag": ("w_alt_interp", 0, "available"),
            "lost support with one flag": ("w_alt_family", 1, "lost_support"),
            "interp unavailable enum": ("w_alt_interp", 0, "unavailable"),
        }
        for label, (endpoint, available, status) in cases.items():
            rows = self._passing_screening_rows()
            rows[0][f"{endpoint}_available"] = available
            rows[0][f"{endpoint}_availability_status"] = status
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, "availability"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_accepts_real_shaped_success_and_failed_fit_rows(self):
        rows = self._passing_screening_rows()
        rows[0] = self._as_failed_evaluator_row(rows[0])
        parsed = experiment._parse_screening_replications(
            self._screening_csv_bytes(rows)
        )
        self.assertEqual(parsed[0]["fit_success"], 0)
        self.assertEqual(parsed[0]["failure_code"], "SyntheticFailure")
        self.assertEqual(
            json.loads(parsed[0]["fit_diagnostics_json"])["status"], "failure"
        )
        self.assertEqual(parsed[0]["family_selected_index"], 1)
        self.assertIsNone(parsed[0]["w_alt_family_raw_response_error_mean"])
        self.assertIsNone(parsed[0]["topology_slope_family_error_mean"])
        for suffix in metrics.SUPPORT_SUFFIXES:
            self.assertIsNotNone(parsed[0][f"w_alt_family_{suffix}"])

    def test_screening_csv_rejects_inconsistent_fit_and_failure_states(self):
        cases = {
            "success diagnostics say failure": {
                "fit_diagnostics_json": '{"status":"failure"}',
            },
            "success has failure code": {
                "failure_code": "SyntheticFailure",
                "failure_reason": "failed",
            },
            "failure lacks reason": {
                "fit_success": 0,
                "scorable": 0,
                "failure_code": "SyntheticFailure",
                "failure_reason": None,
                "fit_diagnostics_json": '{"status":"failure"}',
            },
            "failed fit is scorable": {
                "fit_success": 0,
                "scorable": 1,
                "failure_code": "SyntheticFailure",
                "failure_reason": "failed",
                "fit_diagnostics_json": '{"status":"failure"}',
            },
            "wrong numerical failure code": {
                "fit_success": 1,
                "scorable": 0,
                "failure_code": "SyntheticFailure",
                "failure_reason": "failed",
            },
        }
        for label, updates in cases.items():
            rows = self._passing_screening_rows()
            rows[0].update(updates)
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, "fit|failure|diagnostics"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_rejects_gate_flags_contradicting_diagnostics(self):
        rows = self._passing_screening_rows()
        candidate = next(
            row for row in rows if row["method"] == "dw_joint_tucker333"
        )
        candidate["at_least_one_converged_start"] = 0
        with self.assertRaisesRegex(RuntimeError, "converged|diagnostics"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_failed_fit_diagnostic_mismatch(self):
        base_rows = self._passing_screening_rows()
        base_rows[0] = self._as_failed_evaluator_row(base_rows[0])
        cases = {
            "error type mismatch": {"failure_code": "OtherFailure"},
            "error message mismatch": {"failure_reason": "other message"},
            "selected hyperparameter retained": {"selected_hyperparameter": 0.5},
            "missing intended dates": {"diagnostic_remove": "intended_dates"},
            "shape is not a list": {"diagnostic_update": {"expected_tensor_shape": "10x20x120"}},
            "count disagrees": {"diagnostic_update": {"intended_count": 119}},
        }
        for label, mutation in cases.items():
            rows = copy.deepcopy(base_rows)
            row = rows[0]
            diagnostics = json.loads(row["fit_diagnostics_json"])
            if "diagnostic_remove" in mutation:
                diagnostics.pop(mutation["diagnostic_remove"])
            if "diagnostic_update" in mutation:
                diagnostics.update(mutation["diagnostic_update"])
            row.update({
                key: value for key, value in mutation.items()
                if key not in {"diagnostic_remove", "diagnostic_update"}
            })
            row["fit_diagnostics_json"] = json.dumps(
                diagnostics, separators=(",", ":"), sort_keys=True
            )
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, "failure|diagnostic|hyperparameter|shape|count"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_rejects_unavailable_endpoint_with_metric(self):
        rows = self._passing_screening_rows()
        row = rows[0]
        row["w_alt_family_available"] = 0
        row["w_alt_family_availability_status"] = "lost_support"
        row["w_alt_family_raw_response_error_mean"] = 0.5
        with self.assertRaisesRegex(RuntimeError, "unavailable|endpoint metric"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_nonscorable_row_with_scientific_metrics(self):
        rows = self._passing_screening_rows()
        row = rows[0]
        row.update({
            "scorable": 0,
            "failure_code": "EVALUATION_NUMERICAL_FAIL",
            "failure_reason": "FloatingPointError: overflow",
        })
        with self.assertRaisesRegex(RuntimeError, "non-scorable|scientific metric"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_requires_complete_scorable_metrics(self):
        cases = {
            "available endpoint metric missing": {
                "w_ref_operator_absolute_error_mean": None,
            },
            "mechanism metric missing": {"m_ref_relative_error_mean": None},
            "available family slope missing": {
                "topology_slope_family_error_mean": None,
            },
        }
        for label, updates in cases.items():
            rows = self._passing_screening_rows()
            rows[0].update(updates)
            with self.subTest(label=label), self.assertRaisesRegex(
                RuntimeError, "scorable|metric|family slope"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

        rows = self._passing_screening_rows()
        rows[0]["w_ref_stability_qualified_error_mean"] = None
        parsed = experiment._parse_screening_replications(
            self._screening_csv_bytes(rows)
        )
        self.assertIsNone(parsed[0]["w_ref_stability_qualified_error_mean"])

    def test_screening_csv_binds_family_slope_to_missing_family_endpoint(self):
        rows = self._passing_screening_rows()
        row = rows[0]
        row.update({
            "endpoint_construction_status": "CONSTRUCTION_FAIL",
            "endpoint_failure_reasons_json": '["no_supported_family_candidate"]',
            "family_selected_index": None,
            "w_alt_family_available": 0,
            "w_alt_family_availability_status": "unavailable",
            "topology_slope_family_error_mean": None,
        })
        for metric in metrics.ENDPOINT_METRICS:
            row[f"w_alt_family_{metric}"] = None
        for suffix in metrics.SUPPORT_SUFFIXES:
            row[f"w_alt_family_{suffix}"] = None
        parsed = experiment._parse_screening_replications(
            self._screening_csv_bytes(rows)
        )
        self.assertIsNone(parsed[0]["topology_slope_family_error_mean"])

        row["topology_slope_family_error_mean"] = 0.5
        with self.assertRaisesRegex(RuntimeError, "family slope"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_available_family_without_selected_index(self):
        rows = self._passing_screening_rows()
        rows[0]["family_selected_index"] = None
        with self.assertRaisesRegex(RuntimeError, "family.*index|selected"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_family_index_outside_frozen_pool(self):
        for index in (-1, 64):
            rows = self._passing_screening_rows()
            rows[0]["family_selected_index"] = index
            with self.subTest(index=index), self.assertRaisesRegex(
                RuntimeError, "family.*index|negative"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_requires_all_selected_family_support_summaries(self):
        for suffix in metrics.SUPPORT_SUFFIXES:
            rows = self._passing_screening_rows()
            rows[0][f"w_alt_family_{suffix}"] = None
            with self.subTest(suffix=suffix), self.assertRaisesRegex(
                RuntimeError, "family support"
            ):
                experiment._parse_screening_replications(
                    self._screening_csv_bytes(rows)
                )

    def test_screening_csv_rejects_absent_family_with_support_summary(self):
        rows = self._passing_screening_rows()
        row = rows[0]
        row.update({
            "endpoint_construction_status": "CONSTRUCTION_FAIL",
            "endpoint_failure_reasons_json": '["no_supported_family_candidate"]',
            "family_selected_index": None,
            "w_alt_family_available": 0,
            "w_alt_family_availability_status": "unavailable",
            "topology_slope_family_error_mean": None,
        })
        for metric in metrics.ENDPOINT_METRICS:
            row[f"w_alt_family_{metric}"] = None
        for suffix in metrics.SUPPORT_SUFFIXES:
            row[f"w_alt_family_{suffix}"] = None
        row["w_alt_family_calibration_chi_max"] = 0.5
        with self.assertRaisesRegex(RuntimeError, "absent family|family support"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )

    def test_screening_csv_rejects_selected_index_for_unavailable_family(self):
        rows = self._passing_screening_rows()
        row = rows[0]
        row.update({
            "endpoint_construction_status": "CONSTRUCTION_FAIL",
            "endpoint_failure_reasons_json": '["no_supported_family_candidate"]',
            "family_selected_index": 1,
            "w_alt_family_available": 0,
            "w_alt_family_availability_status": "unavailable",
            "topology_slope_family_error_mean": None,
        })
        for metric in metrics.ENDPOINT_METRICS:
            row[f"w_alt_family_{metric}"] = None
        with self.assertRaisesRegex(RuntimeError, "family.*index|availability"):
            experiment._parse_screening_replications(
                self._screening_csv_bytes(rows)
            )
    def test_runner_exposes_construction_phase(self):
        parser = experiment.build_argument_parser()
        arguments = parser.parse_args(["--phase", "construction", "--output", "/tmp/r006e-test"])
        self.assertEqual(arguments.phase, "construction")

    @staticmethod
    def _path(maximum_chi=0.05):
        dates = np.arange(80, 140)
        return SimpleNamespace(
            dates=dates,
            chi=np.full(dates.size, maximum_chi),
            maximum_chi=maximum_chi,
            amplification=np.ones(dates.size),
            alpha=np.ones(dates.size),
            retained_rank=np.full(dates.size, 2, dtype=int),
            condition_number=np.ones(dates.size),
            singular_values=tuple(np.ones(2) for _ in dates),
        )

    @classmethod
    def _construction(cls, *, status="CONSTRUCTION_PASS", selected=3):
        prospective = cls._path()
        prospective.dates = np.arange(140, 200)
        family_prospective = prospective
        if status == "CONSTRUCTION_FAIL":
            family_prospective = cls._path(maximum_chi=0.2)
            family_prospective.dates = np.arange(140, 200)
        endpoint = np.eye(2)
        records = tuple(
            SimpleNamespace(
                index=index, endpoint=endpoint,
                path=cls._path(maximum_chi=0.2 if index < selected else 0.05),
            )
            for index in range(64)
        )
        return SimpleNamespace(
            status=status,
            failure_reasons=() if status == "CONSTRUCTION_PASS" else ("family_lost_support_prospectively",),
            w_alt_interp=endpoint,
            w_alt_family=endpoint,
            family_selected_index=selected,
            interp_calibration=cls._path(),
            interp_prospective=prospective,
            family_calibration=cls._path(),
            family_prospective=family_prospective,
            family_candidates=records,
        )

    def _fixed_artifact(self, *, status="CONSTRUCTION_PASS"):
        def panel(*args, **kwargs):
            seed = kwargs["seed"]
            children = r006c.spawn_named_seed_sequences(seed)
            declarations = tuple(
                r006c.StreamDeclaration(
                    name=name, entropy=int(child.entropy),
                    spawn_key=tuple(child.spawn_key), used=name != "stress_topology",
                )
                for name, child in children.items()
            )
            return SimpleNamespace(
                fit=SimpleNamespace(sha256=lambda: "a" * 64),
                design_sha256=lambda: "a" * 64,
                w_alt_interp=np.eye(2),
                family_seed=experiment.keyed_seed(
                    seed, kwargs["rho"], kwargs["a3"], kwargs["eta"], "family_endpoint"
                ),
                stream_metadata=declarations,
            )
        with patch.object(experiment, "build_native_construction_inputs", side_effect=panel), patch.object(
            experiment, "construct_supported_endpoints", return_value=self._construction(status=status)
        ):
            return experiment.build_construction_artifact(
                test_command_status={command: "PASS" for command in experiment.TEST_COMMANDS}
            )

    @staticmethod
    def _redigest(artifact):
        body = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
        artifact["artifact_sha256"] = experiment.hashlib.sha256(
            experiment._canonical_json_bytes(body)
        ).hexdigest()
        return artifact

    def _confirmation_artifact(self, construction, specification, screening_sha):
        token = experiment.verify_construction_artifact(construction)
        certificates = []
        by_identity = {
            (item["seed"], item["rho"], item["a3"], item["eta"]): item
            for item in construction["screening_support_certificates"]
        }
        confirmation_streams = construction["contract"]["confirmation"]["stream_declarations"]
        for offset, seed in enumerate(range(250100, 250130)):
            source_seed = 240100 + (offset % 10)
            for rho, a3, eta in experiment.primary_cells():
                item = copy.deepcopy(by_identity[(source_seed, rho, a3, eta)])
                item["seed"] = seed
                item["dgp_and_interp_streams"] = confirmation_streams[str(seed)]["dgp_and_interp_streams"]
                item["family_seed"] = experiment.keyed_seed(
                    seed, rho, a3, eta, "family_endpoint"
                )
                certificates.append(item)
        body = {
            "schema_version": 1,
            "run_type": "FORMAL_CONFIRMATION_CONSTRUCTION",
            "status": "CONSTRUCTION_PASS",
            "current_state": "CONFIRMATION_NOT_AUTHORIZED",
            "seed_ids": list(range(250100, 250130)),
            "construction_artifact_sha256": token.artifact_sha256,
            "provenance_sha256": token.provenance_sha256,
            "provenance": experiment.current_provenance(),
            "config_sha256": construction["contract"]["config_sha256"],
            "candidate_sha256": construction["provenance"]["source_hashes"]["scripts/experiments/r006e_dw_tucker.py"],
            "median_specification_sha256": specification["specification_sha256"],
            "median_tests_sha256": specification["tests_sha256"],
            "screening_artifact_sha256": screening_sha,
            "confirmation_support_certificates": certificates,
        }
        return {**body, "artifact_sha256": experiment.hashlib.sha256(experiment._canonical_json_bytes(body)).hexdigest()}

    def test_construction_builds_only_80_screening_seed_cells(self):
        def panel(*args, **kwargs):
            return SimpleNamespace(
                fit=SimpleNamespace(sha256=lambda: "a" * 64),
                design_sha256=lambda: "a" * 64,
                w_alt_interp=np.eye(2), stream_metadata=(),
                family_seed=experiment.keyed_seed(
                    kwargs["seed"], kwargs["rho"], kwargs["a3"], kwargs["eta"],
                    "family_endpoint",
                ),
            )
        with patch.object(experiment, "build_native_construction_inputs", side_effect=panel) as build, patch.object(
            experiment, "construct_supported_endpoints", return_value=self._construction()
        ) as endpoints:
            artifact = experiment.build_construction_artifact()
        self.assertEqual(build.call_count, 80)
        self.assertEqual(endpoints.call_count, 80)
        self.assertEqual({call.kwargs["seed"] for call in build.call_args_list}, set(range(240100, 240110)))
        self.assertTrue(all(call.kwargs["seed"] < 250000 for call in build.call_args_list))
        declarations = artifact["contract"]["confirmation"]
        self.assertEqual(declarations["seed_ids"], list(range(250100, 250130)))
        self.assertEqual(declarations["construction"], "DECLARATIONS_ONLY")
        self.assertEqual(len(artifact["screening_support_certificates"]), 80)
        for call, certificate in zip(endpoints.call_args_list, artifact["screening_support_certificates"]):
            self.assertEqual(call.kwargs["family_seed"], certificate["family_seed"])
            self.assertEqual(
                certificate["family_seed"],
                experiment.keyed_seed(
                    certificate["seed"], certificate["rho"], certificate["a3"],
                    certificate["eta"], "family_endpoint",
                ),
            )

    def test_construction_never_materializes_truth_or_native_panel(self):
        support_only = SimpleNamespace(
            fit=SimpleNamespace(sha256=lambda: "a" * 64),
            design_sha256=lambda: "a" * 64,
            w_alt_interp=np.eye(2), family_seed=23, stream_metadata=(),
        )
        with patch.object(experiment, "build_native_construction_inputs", return_value=support_only), patch(
            "scripts.experiments.r006e_native_protocol.TruthBundle",
            side_effect=AssertionError("truth materialized"),
        ), patch(
            "scripts.experiments.r006e_native_protocol.NativePanel",
            side_effect=AssertionError("panel materialized"),
        ), patch.object(experiment, "construct_supported_endpoints", return_value=self._construction()):
            artifact = experiment.build_construction_artifact(
                test_command_status={command: "PASS" for command in experiment.TEST_COMMANDS}
            )
        self.assertEqual(len(artifact["screening_support_certificates"]), 80)

    def test_construction_is_outcome_free_and_retains_failed_endpoint(self):
        artifact = self._fixed_artifact(status="CONSTRUCTION_FAIL")
        serialized = json.dumps(artifact, sort_keys=True).lower()
        for forbidden in ("raw_response_error", "operator_error", "truth_b", "promotion_result"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(artifact["status"], "CONSTRUCTION_FAIL")
        self.assertEqual(artifact["screening_support_certificates"][0]["family_selected_index"], 3)
        self.assertEqual(artifact["screening_support_certificates"][0]["failure_reasons"], ["family_lost_support_prospectively"])

    def test_not_run_or_failed_prerequisites_cannot_produce_construction_pass(self):
        panel = SimpleNamespace(
            fit=SimpleNamespace(sha256=lambda: "a" * 64), w_alt_interp=np.eye(2),
            design_sha256=lambda: "a" * 64,
            family_seed=23, stream_metadata=(),
        )
        with patch.object(experiment, "build_native_construction_inputs", return_value=panel), patch.object(
            experiment, "construct_supported_endpoints", return_value=self._construction()
        ):
            not_run = experiment.build_construction_artifact()
            failed = experiment.build_construction_artifact(
                test_command_status={
                    command: ("FAIL" if index == 0 else "PASS")
                    for index, command in enumerate(experiment.TEST_COMMANDS)
                }
            )
        self.assertEqual(not_run["status"], "CONSTRUCTION_FAIL")
        self.assertEqual(failed["status"], "CONSTRUCTION_FAIL")

    def test_unknown_test_command_status_is_rejected_even_for_failure(self):
        artifact = self._fixed_artifact()
        artifact["status"] = "CONSTRUCTION_FAIL"
        artifact["test_command_status"][experiment.TEST_COMMANDS[0]] = "UNKNOWN"
        self._redigest(artifact)
        with self.assertRaisesRegex(RuntimeError, "test-command status"):
            experiment.verify_construction_artifact(artifact)

    def test_cli_runs_frozen_prerequisites_before_construction(self):
        completed = subprocess.CompletedProcess([], 0, "", "")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", root), patch.object(
                experiment.subprocess, "run", return_value=completed
            ) as run, patch.object(
                experiment, "build_construction_artifact", return_value={"status": "CONSTRUCTION_FAIL"}
            ) as build, patch.object(experiment, "write_artifact", return_value=root / experiment.CONSTRUCTION_ARTIFACT_NAME):
                result = experiment.main(["--phase", "construction", "--output", str(root)])
        self.assertEqual(result, 1)
        self.assertEqual(run.call_count, len(experiment.TEST_COMMANDS))
        statuses = build.call_args.kwargs["test_command_status"]
        self.assertEqual(statuses, {command: "PASS" for command in experiment.TEST_COMMANDS})

    def test_verification_recomputes_hashes_and_rejects_tamper(self):
        artifact = self._fixed_artifact()
        token = experiment.verify_construction_artifact(artifact)
        self.assertEqual(token.status, "CONSTRUCTION_PASS")
        tampered = copy.deepcopy(artifact)
        first = next(iter(tampered["provenance"]["source_hashes"]))
        tampered["provenance"]["source_hashes"][first] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "provenance mismatch"):
            experiment.verify_construction_artifact(tampered)

    def test_provenance_covers_all_experiment_sources_and_native_dependencies(self):
        provenance = experiment.current_provenance()
        expected = {
            path.relative_to(experiment.ROOT).as_posix()
            for path in (experiment.ROOT / "scripts/experiments").glob("*.py")
        }
        self.assertTrue(expected <= set(provenance["source_hashes"]))
        dependencies = provenance["dependency_versions"]
        self.assertIn("scipy", dependencies)
        self.assertIn("numpy_build_config_text", dependencies)
        self.assertEqual(
            dependencies["numpy_build_config_sha256"],
            experiment.hashlib.sha256(dependencies["numpy_build_config_text"].encode()).hexdigest(),
        )

    def test_transitive_source_change_changes_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scripts/experiments").mkdir(parents=True)
            (root / "refine-logs").mkdir()
            (root / "docs/superpowers/plans").mkdir(parents=True)
            transitive = root / "scripts/experiments/transitive.py"
            protocol = root / "refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md"
            plan = root / "docs/superpowers/plans/2026-07-16-r006e-native-supported-recovery.md"
            transitive.write_text("VALUE = 1\n")
            protocol.write_text("protocol\n")
            plan.write_text("plan\n")
            with patch.object(experiment, "ROOT", root):
                before = experiment.current_provenance()
                transitive.write_text("VALUE = 2\n")
                after = experiment.current_provenance()
            self.assertNotEqual(before["source_hashes"], after["source_hashes"])

    def test_cli_refuses_dependency_changed_after_prerequisite_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            dependency = Path(temporary) / "dependency.py"
            dependency.write_text("VALUE = 1\n")
            snapshot = {str(dependency): experiment._sha256_file(dependency)}
            def run_tests_then_mutate():
                dependency.write_text("VALUE = 2\n")
                return {command: "PASS" for command in experiment.TEST_COMMANDS}
            with patch.object(experiment, "IMPORT_SOURCE_SNAPSHOT", snapshot), patch.object(
                experiment, "_scientific_source_paths", return_value=(dependency,)
            ), patch.object(experiment, "run_preconstruction_tests", side_effect=run_tests_then_mutate), patch.object(
                experiment, "build_construction_artifact"
            ) as build, patch.object(experiment, "write_artifact") as write:
                with self.assertRaisesRegex(RuntimeError, "loaded source snapshot"):
                    experiment.main(["--phase", "construction", "--output", str(experiment.PRIMARY_OUTPUT_DIR)])
            build.assert_not_called()
            write.assert_not_called()

    def test_post_publication_source_mismatch_removes_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "primary"
            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", root), patch.object(
                experiment, "run_preconstruction_tests",
                return_value={command: "PASS" for command in experiment.TEST_COMMANDS},
            ), patch.object(
                experiment, "build_construction_artifact",
                return_value={"status": "CONSTRUCTION_FAIL"},
            ), patch.object(
                experiment, "_assert_loaded_source_snapshot",
                side_effect=[None, None, None, RuntimeError("loaded source snapshot mismatch")],
            ):
                with self.assertRaisesRegex(RuntimeError, "loaded source snapshot"):
                    experiment.main(["--phase", "construction", "--output", str(root)])
            self.assertFalse((root / experiment.CONSTRUCTION_ARTIFACT_NAME).exists())

    def test_post_publication_cleanup_preserves_concurrent_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "primary"
            destination = root / experiment.CONSTRUCTION_ARTIFACT_NAME
            calls = 0

            def replace_then_report_source_mismatch():
                nonlocal calls
                calls += 1
                if calls == 4:
                    destination.unlink()
                    destination.write_text('{"replacement":true}\n')
                    raise RuntimeError("loaded source snapshot mismatch")

            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", root), patch.object(
                experiment, "run_preconstruction_tests",
                return_value={command: "PASS" for command in experiment.TEST_COMMANDS},
            ), patch.object(
                experiment, "build_construction_artifact",
                return_value={"status": "CONSTRUCTION_FAIL"},
            ), patch.object(
                experiment, "_assert_loaded_source_snapshot",
                side_effect=replace_then_report_source_mismatch,
            ):
                with self.assertRaisesRegex(RuntimeError, "publication ownership"):
                    experiment.main(
                        ["--phase", "construction", "--output", str(root)]
                    )
            self.assertEqual(destination.read_text(), '{"replacement":true}\n')

    def test_cleanup_restores_replacement_moved_at_quarantine_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "primary"
            destination = root / experiment.CONSTRUCTION_ARTIFACT_NAME
            snapshot_calls = 0
            real_replace = os.replace

            def source_check():
                nonlocal snapshot_calls
                snapshot_calls += 1
                if snapshot_calls == 4:
                    raise RuntimeError("loaded source snapshot mismatch")

            def replace_public_at_rename(source, target):
                source_path = Path(source)
                if source_path.name == experiment.CONSTRUCTION_ARTIFACT_NAME:
                    source_path.unlink()
                    source_path.write_text('{"boundary_replacement":true}\n')
                return real_replace(source, target)

            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", root), patch.object(
                experiment, "run_preconstruction_tests",
                return_value={command: "PASS" for command in experiment.TEST_COMMANDS},
            ), patch.object(
                experiment, "build_construction_artifact",
                return_value={"status": "CONSTRUCTION_FAIL"},
            ), patch.object(
                experiment, "_assert_loaded_source_snapshot",
                side_effect=source_check,
            ), patch.object(experiment.os, "replace", side_effect=replace_public_at_rename):
                with self.assertRaisesRegex(RuntimeError, "publication ownership"):
                    experiment.main(
                        ["--phase", "construction", "--output", str(root)]
                    )
            self.assertEqual(
                destination.read_text(), '{"boundary_replacement":true}\n'
            )

    def test_cleanup_retains_quarantine_when_newer_public_replacement_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "primary"
            destination = root / experiment.CONSTRUCTION_ARTIFACT_NAME
            snapshot_calls = 0
            real_replace = os.replace

            def source_check():
                nonlocal snapshot_calls
                snapshot_calls += 1
                if snapshot_calls == 4:
                    raise RuntimeError("loaded source snapshot mismatch")

            def replace_twice_at_rename(source, target):
                source_path = Path(source)
                result = None
                if source_path.name == experiment.CONSTRUCTION_ARTIFACT_NAME:
                    source_path.unlink()
                    source_path.write_text('{"boundary_replacement":true}\n')
                    result = real_replace(source, target)
                    source_path.write_text('{"newer_replacement":true}\n')
                    return result
                return real_replace(source, target)

            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", root), patch.object(
                experiment, "run_preconstruction_tests",
                return_value={command: "PASS" for command in experiment.TEST_COMMANDS},
            ), patch.object(
                experiment, "build_construction_artifact",
                return_value={"status": "CONSTRUCTION_FAIL"},
            ), patch.object(
                experiment, "_assert_loaded_source_snapshot",
                side_effect=source_check,
            ), patch.object(experiment.os, "replace", side_effect=replace_twice_at_rename):
                with self.assertRaisesRegex(RuntimeError, "publication ownership"):
                    experiment.main(
                        ["--phase", "construction", "--output", str(root)]
                    )
            self.assertEqual(destination.read_text(), '{"newer_replacement":true}\n')
            quarantines = list(root.glob(
                f".{experiment.CONSTRUCTION_ARTIFACT_NAME}.cleanup.*"
            ))
            self.assertEqual(len(quarantines), 1)
            self.assertEqual(
                quarantines[0].read_text(), '{"boundary_replacement":true}\n'
            )

    def test_stream_contract_uses_actual_r006c_seedsequence_children(self):
        contract = experiment.frozen_contract(experiment.R006EConfig())
        declaration = contract["screening"]["stream_map"]["240100"]
        children = np.random.SeedSequence(240100).spawn(len(r006c.STREAM_NAMES))
        for name, child in zip(r006c.STREAM_NAMES, children):
            stored = declaration["dgp_and_interp_streams"][name]
            self.assertEqual(stored["entropy"], child.entropy)
            self.assertEqual(stored["spawn_key"], list(child.spawn_key))
        self.assertTrue(declaration["dgp_and_interp_streams"]["stress_topology"]["spawned"])
        self.assertFalse(declaration["dgp_and_interp_streams"]["stress_topology"]["used"])
        family = declaration["family_endpoint_by_cell"]["0.8|0.1|0.15"]
        self.assertEqual(family, experiment.keyed_seed(240100, 0.8, 0.1, 0.15, "family_endpoint"))

    def test_verification_rejects_malformed_duplicate_and_recovery_fields(self):
        artifact = self._fixed_artifact()
        malformed = copy.deepcopy(artifact)
        malformed["screening_support_certificates"].append(copy.deepcopy(malformed["screening_support_certificates"][0]))
        with self.assertRaisesRegex(RuntimeError, "duplicate|exactly 80"):
            experiment.verify_construction_artifact(malformed)
        injected = copy.deepcopy(artifact)
        injected["raw_response_error"] = 0.1
        with self.assertRaisesRegex(RuntimeError, "schema|recovery"):
            experiment.verify_construction_artifact(injected)

    def test_verification_rejects_missing_candidate_and_false_support_pass(self):
        artifact = self._fixed_artifact()
        missing = copy.deepcopy(artifact)
        missing["screening_support_certificates"][0]["family_candidate_certificates"].pop()
        with self.assertRaisesRegex(RuntimeError, "candidate"):
            experiment.verify_construction_artifact(missing)
        unsupported = copy.deepcopy(artifact)
        unsupported["screening_support_certificates"][0]["family_prospective"]["maximum_chi"] = 0.2
        with self.assertRaisesRegex(RuntimeError, "support|status"):
            experiment.verify_construction_artifact(unsupported)

    def test_certificate_semantic_tampering_is_rejected_after_redigest(self):
        base = self._fixed_artifact()
        mutations = {
            "maximum chi": lambda c: c["interp_prospective"].__setitem__("maximum_chi", 0.04),
            "negative chi": lambda c: c["interp_prospective"]["chi"].__setitem__(0, -0.1),
            "boolean rank": lambda c: c["interp_prospective"]["retained_rank"].__setitem__(0, True),
            "derived alpha": lambda c: c["interp_prospective"]["alpha"].__setitem__(0, 2.0),
            "derived condition": lambda c: c["interp_prospective"]["condition_number"].__setitem__(0, 2.0),
            "derived rank": lambda c: c["interp_prospective"]["retained_rank"].__setitem__(0, 1),
            "bad design hash": lambda c: c.__setitem__("design_inputs_sha256", "xyz"),
            "wrong selected index": lambda c: c.__setitem__("family_selected_index", 4),
            "wrong selected hash": lambda c: c.__setitem__("family_endpoint_sha256", "0" * 64),
            "candidate max mismatch": lambda c: c["family_candidate_certificates"][3].__setitem__("calibration_maximum_chi", 0.04),
            "wrong family seed": lambda c: c.__setitem__("family_seed", c["family_seed"] + 1),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                artifact = copy.deepcopy(base)
                mutate(artifact["screening_support_certificates"][0])
                self._redigest(artifact)
                with self.assertRaisesRegex(RuntimeError, "certificate|support|hash|selected|chi|rank"):
                    experiment.verify_construction_artifact(artifact)

    def test_phase_authorization_is_fail_closed(self):
        artifact = self._fixed_artifact()
        experiment.authorize_screening(artifact, existing_names=())
        with self.assertRaisesRegex(RuntimeError, "on-disk screening"):
            experiment.authorize_confirmation({"status": "FAIL"}, artifact)
        screening = {
            "status": "PASS",
            "seed_ids": list(range(240100, 240110)),
            "config_sha256": artifact["contract"]["config_sha256"],
            "candidate_sha256": artifact["provenance"]["source_hashes"]["scripts/experiments/r006e_dw_tucker.py"],
        }
        with self.assertRaisesRegex(RuntimeError, "on-disk screening"):
            experiment.authorize_confirmation(screening, artifact, median_bound_specification=None)

    def test_status_enrichment_and_atomic_isolated_writer_contract(self):
        self.assertNotEqual(experiment.normalize_run_status("PASS", run_type="SMOKE"), "PASS")
        row = experiment.enrich_replication_row(
            self._successful_evaluator_payload(), seed=240100, rho=0.8,
            a3=0.1, eta=0.15, peak_memory_bytes=123,
            peak_memory_worker_pid=12345,
        )
        self.assertEqual((row["seed"], row["rho"], row["a3"], row["eta"]), (240100, 0.8, 0.1, 0.15))
        self.assertEqual(row["peak_memory_bytes"], 123)
        with self.assertRaises(experiment.RunnerContractError):
            experiment.enrich_replication_row(
                self._successful_evaluator_payload(), seed=None, rho=0.8,
                a3=0.1, eta=0.15, peak_memory_bytes=1,
                peak_memory_worker_pid=12345,
            )
        with tempfile.TemporaryDirectory() as temporary:
            primary = Path(temporary) / "primary"
            repeat = Path(temporary) / "repeat"
            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", primary), patch.object(experiment, "REPEAT_OUTPUT_DIR", repeat):
                path = experiment.write_artifact(primary, experiment.CONSTRUCTION_ARTIFACT_NAME, artifact={"x": 1}, repeat=False)
                self.assertEqual(json.loads(path.read_text()), {"x": 1})
                with self.assertRaisesRegex(FileExistsError, "overwrite"):
                    experiment.write_artifact(primary, experiment.CONSTRUCTION_ARTIFACT_NAME, artifact={"x": 1}, repeat=False)
                with self.assertRaisesRegex(ValueError, "isolated"):
                    experiment.write_artifact(repeat, experiment.CONSTRUCTION_ARTIFACT_NAME, artifact={"x": 1}, repeat=False)

    def test_enrichment_rejects_missing_or_extra_evaluator_field(self):
        complete = self._successful_evaluator_payload()
        missing = dict(complete)
        missing.pop("m_ref_relative_error_mean")
        extra = {**complete, "native_sum": 1.0}
        for label, payload in (("missing", missing), ("extra", extra)):
            with self.subTest(label=label), self.assertRaisesRegex(
                experiment.RunnerContractError, "evaluator payload schema"
            ):
                experiment.enrich_replication_row(
                    payload, seed=240100, rho=0.8, a3=0.1, eta=0.15,
                    peak_memory_bytes=123, peak_memory_worker_pid=12345,
                )

    def test_enrichment_returns_exact_full_runner_schema(self):
        row = experiment.enrich_replication_row(
            self._successful_evaluator_payload(),
            seed=240100, rho=0.8, a3=0.1, eta=0.15,
            peak_memory_bytes=123, peak_memory_worker_pid=12345,
        )
        self.assertEqual(tuple(row), experiment.SCREENING_CSV_FIELDS)

    def test_atomic_publication_is_exclusive_under_concurrent_writers(self):
        with tempfile.TemporaryDirectory() as temporary:
            primary = Path(temporary) / "primary"
            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", primary):
                def publish(index):
                    return experiment.write_artifact(
                        primary, experiment.CONSTRUCTION_ARTIFACT_NAME,
                        artifact={"writer": index}, repeat=False,
                    )
                with ThreadPoolExecutor(max_workers=12) as pool:
                    futures = [pool.submit(publish, index) for index in range(12)]
                successes = [future.result() for future in futures if future.exception() is None]
                failures = [future.exception() for future in futures if future.exception() is not None]
            self.assertEqual(len(successes), 1)
            self.assertTrue(all(isinstance(error, FileExistsError) for error in failures))
            payload = json.loads(successes[0].read_text())
            self.assertIn(payload["writer"], range(12))

    def test_cli_outcome_phases_refuse_without_scientific_calls(self):
        for phase in ("screening", "confirmation"):
            with self.subTest(phase=phase), patch.object(experiment, "build_native_construction_inputs") as build, patch.object(
                experiment, "construct_supported_endpoints"
            ) as endpoints:
                with self.assertRaisesRegex(RuntimeError, "not authorized"):
                    experiment.main(["--phase", phase, "--output", "/tmp/unused-r006e"])
                build.assert_not_called()
                endpoints.assert_not_called()

    def test_confirmation_validates_separate_gate_then_remains_unauthorized(self):
        artifact = self._fixed_artifact()
        token = experiment.verify_construction_artifact(artifact)
        screening = {
            "status": "PASS",
            "seed_ids": list(range(240100, 240110)),
            "config_sha256": artifact["contract"]["config_sha256"],
            "candidate_sha256": artifact["provenance"]["source_hashes"]["scripts/experiments/r006e_dw_tucker.py"],
        }
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "primary"
            output_root.mkdir()
            replications = output_root / "screening_replications.csv"
            summary = output_root / "screening_summary.csv"
            rows = self._passing_screening_rows()
            self._write_screening_csv(replications, rows)
            summary.write_text("summary\n")
            screening_body = {
                "schema_version": 1,
                "status": "PASS",
                "gate_result": experiment.evaluate_screening_gate(
                    rows, config=experiment.R006EConfig()
                ),
                "seed_ids": list(range(240100, 240110)),
                "config_sha256": artifact["contract"]["config_sha256"],
                "candidate_sha256": artifact["provenance"]["source_hashes"]["scripts/experiments/r006e_dw_tucker.py"],
                "construction_artifact_sha256": token.artifact_sha256,
                "provenance_sha256": token.provenance_sha256,
                "screening_replications_sha256": experiment._sha256_file(replications),
                "screening_summary_sha256": experiment._sha256_file(summary),
            }
            screening_result = {**screening_body, "artifact_sha256": experiment.hashlib.sha256(experiment._canonical_json_bytes(screening_body)).hexdigest()}
            screening_path = output_root / "screening_results.json"
            screening_path.write_bytes(experiment._canonical_json_bytes(screening_result) + b"\n")
            spec_path = Path(temporary) / "median_spec.md"
            tests_path = Path(temporary) / "test_median_spec.py"
            spec_path.write_text("approved median specification\n")
            tests_path.write_text("def test_spec(): pass\n")
            specification = {
                "confidence_allocation": "frozen",
                "order_statistic_indexing": "frozen",
                "equality_handling": "frozen",
                "finite_sample_rounding": "frozen",
                "approved_spec_path": str(spec_path),
                "approved_test_path": str(tests_path),
                "specification_sha256": experiment._sha256_file(spec_path),
                "tests_sha256": experiment._sha256_file(tests_path),
            }
            separate = self._confirmation_artifact(artifact, specification, screening_result["artifact_sha256"])
            wrong_family = copy.deepcopy(separate)
            first = wrong_family["confirmation_support_certificates"][0]
            first["family_seed"] = experiment.keyed_seed(
                240100, first["rho"], first["a3"], first["eta"], "family_endpoint"
            )
            self._redigest(wrong_family)
            with self.assertRaisesRegex(RuntimeError, "confirmation family seed"):
                experiment.verify_confirmation_construction_artifact(
                    wrong_family, artifact, specification,
                    screening_result["artifact_sha256"],
                )
            shallow = {"status": "CONSTRUCTION_PASS", "seed_ids": list(range(250100, 250130))}
            with self.assertRaisesRegex(RuntimeError, "schema"):
                experiment.verify_confirmation_construction_artifact(
                    shallow, artifact, specification, screening_result["artifact_sha256"]
                )
            with self.assertRaisesRegex(RuntimeError, "paths mismatch"):
                with patch.object(experiment, "PRIMARY_OUTPUT_DIR", output_root):
                    experiment.authorize_confirmation(screening_path, artifact, specification, separate)
            tampered_rows = copy.deepcopy(rows)
            for row in tampered_rows:
                if row["method"] == "dw_joint_tucker333" and (
                    row["rho"], row["a3"], row["eta"]
                ) == (0.8, 0.1, 0.15):
                    row["w_alt_interp_raw_response_error_mean"] = 9.0
            self._write_screening_csv(replications, tampered_rows)
            screening_result["screening_replications_sha256"] = experiment._sha256_file(replications)
            self._redigest(screening_result)
            screening_path.write_bytes(experiment._canonical_json_bytes(screening_result) + b"\n")
            with self.assertRaisesRegex(RuntimeError, "recomputed screening gate"):
                with patch.object(experiment, "PRIMARY_OUTPUT_DIR", output_root):
                    experiment.authorize_confirmation(screening_path, artifact, specification, separate)
            self._write_screening_csv(replications, rows)
            screening_result["screening_replications_sha256"] = experiment._sha256_file(replications)
            self._redigest(screening_result)
            screening_path.write_bytes(experiment._canonical_json_bytes(screening_result) + b"\n")
            real_gate = experiment.evaluate_screening_gate
            def mutate_summary_after_gate(parsed_rows, *, config):
                result = real_gate(parsed_rows, config=config)
                summary.write_text("changed summary\n")
                return result
            with patch.object(experiment, "evaluate_screening_gate", side_effect=mutate_summary_after_gate), patch.object(
                experiment, "PRIMARY_OUTPUT_DIR", output_root
            ):
                with self.assertRaisesRegex(RuntimeError, "stable snapshot changed"):
                    experiment._verify_screening_results(screening_path, artifact, repeat=False)
            summary.write_text("summary\n")
            symlink_target = output_root / "screening_summary_target.csv"
            symlink_target.write_text("summary\n")
            summary.unlink()
            summary.symlink_to(symlink_target)
            with patch.object(experiment, "PRIMARY_OUTPUT_DIR", output_root):
                with self.assertRaisesRegex(RuntimeError, "non-symlink"):
                    experiment._verify_screening_results(
                        screening_path, artifact, repeat=False
                    )
            summary.unlink()
            summary.write_text("summary\n")
            exact_missing = dict(specification)
            exact_missing["approved_spec_path"] = str(experiment.MEDIAN_SPEC_PATH)
            exact_missing["approved_test_path"] = str(experiment.MEDIAN_TEST_PATH)
            with self.assertRaisesRegex(RuntimeError, "file is absent"):
                with patch.object(experiment, "PRIMARY_OUTPUT_DIR", output_root):
                    experiment.authorize_confirmation(
                        screening_path, artifact, exact_missing, separate,
                    )

    def test_median_snapshot_mutation_during_unittest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "refine-logs").mkdir()
            (root / "scripts/experiments").mkdir(parents=True)
            (root / "docs/superpowers/plans").mkdir(parents=True)
            protocol = root / "refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md"
            plan = root / "docs/superpowers/plans/2026-07-16-r006e-native-supported-recovery.md"
            spec = root / "refine-logs/R006E_SIMULTANEOUS_MEDIAN_BOUND_SPECIFICATION.md"
            test_file = root / "scripts/experiments/test_r006e_median_bound.py"
            protocol.write_text("protocol\n")
            plan.write_text("plan\n")
            spec.write_text("median spec\n")
            test_file.write_text("def test_bound(): pass\n")
            mapping = {
                "confidence_allocation": "frozen", "order_statistic_indexing": "frozen",
                "equality_handling": "frozen", "finite_sample_rounding": "frozen",
                "approved_spec_path": str(spec), "approved_test_path": str(test_file),
                "specification_sha256": experiment._sha256_file(spec),
                "tests_sha256": experiment._sha256_file(test_file),
            }
            def mutate(*args, **kwargs):
                spec.write_text("changed median spec\n")
                return subprocess.CompletedProcess([], 0, "", "")
            with patch.object(experiment, "ROOT", root), patch.object(
                experiment, "MEDIAN_SPEC_PATH", spec
            ), patch.object(experiment, "MEDIAN_TEST_PATH", test_file), patch.object(
                experiment, "_run_median_tests", side_effect=mutate
            ):
                with self.assertRaisesRegex(RuntimeError, "stable snapshot changed"):
                    experiment._verify_median_specification(mapping)

    def test_median_specification_rejects_symlink_at_approved_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "refine-logs/R006E_SIMULTANEO_MEDIAN_BOUND_SPECIFICATION.md"
            test_file = root / "scripts/experiments/test_r006e_median_bound.py"
            spec.parent.mkdir(parents=True)
            test_file.parent.mkdir(parents=True)
            target = root / "real_median_spec.md"
            target.write_text("median spec\n")
            spec.symlink_to(target)
            test_file.write_text("def test_bound(): pass\n")
            mapping = {
                "confidence_allocation": "frozen",
                "order_statistic_indexing": "frozen",
                "equality_handling": "frozen",
                "finite_sample_rounding": "frozen",
                "approved_spec_path": str(spec),
                "approved_test_path": str(test_file),
                "specification_sha256": experiment._sha256_file(target),
                "tests_sha256": experiment._sha256_file(test_file),
            }
            provenance = {
                "source_hashes": {
                    "refine-logs/R006E_SIMULTANEO_MEDIAN_BOUND_SPECIFICATION.md": "a" * 64,
                    "scripts/experiments/test_r006e_median_bound.py": "b" * 64,
                }
            }
            with patch.object(experiment, "ROOT", root), patch.object(
                experiment, "MEDIAN_SPEC_PATH", spec
            ), patch.object(experiment, "MEDIAN_TEST_PATH", test_file), patch.object(
                experiment, "current_provenance", return_value=provenance
            ), patch.object(
                experiment, "_run_median_tests",
                return_value=subprocess.CompletedProcess([], 0, "", ""),
            ):
                with self.assertRaisesRegex(RuntimeError, "non-symlink"):
                    experiment._verify_median_specification(mapping)

    def test_measured_enrichment_uses_native_nonnegative_peak_memory(self):
        row = experiment.measure_and_enrich_replication_row(
            self._successful_evaluator_payload,
            seed=240100, rho=0.8, a3=0.1, eta=0.15,
        )
        self.assertIs(type(row["peak_memory_bytes"]), int)
        self.assertGreaterEqual(row["peak_memory_bytes"], 0)
        self.assertEqual(row["peak_memory_scope"], "fresh_worker_process_peak_rss")
        self.assertNotEqual(row["peak_memory_worker_pid"], os.getpid())

    def test_measured_enrichment_rejects_incomplete_evaluator_payload(self):
        payload = self._successful_evaluator_payload()
        payload.pop("m_ref_relative_error_mean")
        with self.assertRaisesRegex(
            experiment.RunnerContractError, "evaluator payload schema"
        ):
            experiment.measure_and_enrich_replication_row(
                lambda: payload,
                seed=240100, rho=0.8, a3=0.1, eta=0.15,
            )

    def test_peak_rss_covers_native_numpy_and_requires_fresh_worker_contract(self):
        before = experiment.process_peak_rss_bytes()
        def allocate_native():
            values = np.ones(2_000_000, dtype=np.float64)
            if float(values.sum()) <= 0.0:
                raise AssertionError("native allocation failed")
            return self._successful_evaluator_payload()
        row = experiment.measure_and_enrich_replication_row(
            allocate_native, seed=240100, rho=0.8, a3=0.1, eta=0.15,
        )
        second = experiment.measure_and_enrich_replication_row(
            self._successful_evaluator_payload,
            seed=240100, rho=0.8, a3=0.1, eta=0.15,
        )
        self.assertGreater(row["peak_memory_bytes"], 0)
        self.assertNotEqual(row["peak_memory_worker_pid"], os.getpid())
        self.assertNotEqual(row["peak_memory_worker_pid"], second["peak_memory_worker_pid"])


if __name__ == "__main__":
    unittest.main()
