"""Governance-only fixture tests for the R006e screening v2 cell boundary."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import inspect
import json
import math
from types import SimpleNamespace
import unittest

from scripts.experiments.r006e_native_protocol import (
    METHODS,
    SCREENING_SEEDS,
    keyed_seed,
    primary_cells,
)
from scripts.experiments.r006e_native_protocol import R006EConfig
from scripts.experiments.r006e_native_protocol import build_native_panel
from scripts.experiments.r006e_endpoint_support import construct_supported_endpoints
from scripts.experiments.r006e_native_estimators import fit_required_comparators
from scripts.experiments.r006e_dw_tucker import fit_dw_joint_tucker
from scripts.experiments.r006e_native_metrics import evaluate_method
from scripts.experiments.r006e_native_experiment import SCREENING_FLAG_FIELDS
from scripts.experiments.r006e_native_metrics import (
    EVALUATOR_INTEGER_FIELDS,
    EVALUATOR_NULLABLE_FIELDS,
    EVALUATOR_ROW_FIELDS,
    EVALUATOR_STRING_FIELDS,
)
from scripts.experiments.r006e_screening_schema_v2 import (
    DIAGNOSTIC_FIELDS,
    FORMAL_REPLICATION_FIELDS,
    RESOURCE_FIELDS,
    ROW_JOURNAL_FIELDS,
    SUMMARY_FIELDS,
    SchemaValidationError,
    derive_attempt_id,
    validate_diagnostic_record,
    validate_formal_replication_record,
    validate_resource_record,
    validate_row_journal_record,
)
from scripts.experiments.r006e_screening_executor_v2 import (
    ScientificPrimitives,
    adapt_runner_failure_gates,
    combine_cell_executions,
    production_scientific_primitives,
    retain_worker_failure,
    run_screening_cell,
    run_screening_cell_fixture,
    _FIXTURE_CAPABILITY,
    screening_cell_tasks,
)


governance_only = True
PRIMARY_ATTEMPT_ID = derive_attempt_id("fixture-decision", "primary")
REPEAT_ATTEMPT_ID = derive_attempt_id("fixture-decision", "repeat")


def _record_sha256(record: dict[str, object]) -> str:
    payload = json.dumps(
        record,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ScreeningExecutorV2Tests(unittest.TestCase):
    governance_only = True

    def test_production_signature_cannot_inject_fixture_controls(self) -> None:
        parameters = inspect.signature(run_screening_cell).parameters
        self.assertEqual(
            tuple(parameters),
            ("task", "construction_certificate", "config", "attempt_id", "role", "generated_at"),
        )
        self.assertNotIn("primitives", parameters)
        self.assertNotIn("worker_pid", parameters)
        self.assertNotIn("peak_rss_reader", parameters)
        self.assertNotIn("governance_only", parameters)
        with self.assertRaisesRegex(RuntimeError, "fixture capability"):
            run_screening_cell_fixture(
                screening_cell_tasks()[0],
                construction_certificate={},
                config=R006EConfig(),
                primitives=production_scientific_primitives(),
                attempt_id=PRIMARY_ATTEMPT_ID,
                role="primary",
                generated_at="2026-07-18T00:00:00Z",
                worker_pid=1,
                peak_rss_reader=lambda: 1,
                fixture_capability=object(),
            )

    def test_exact_ordered_screening_tasks_and_method_identities(self) -> None:
        tasks = screening_cell_tasks()
        expected_cells = tuple(
            (seed, rho, a3, eta)
            for seed in SCREENING_SEEDS
            for rho, a3, eta in primary_cells()
        )
        self.assertEqual(tuple(task.identity for task in tasks), expected_cells)
        self.assertEqual(len(tasks), 80)
        for task in tasks:
            self.assertEqual(
                task.method_seed,
                keyed_seed(task.seed, task.rho, task.a3, task.eta, "optimizer"),
            )
            self.assertEqual(
                task.method_identities,
                tuple((*task.identity, method) for method in METHODS),
            )

    def test_certificate_mismatch_retains_rows_before_any_fit_or_evaluation(self) -> None:
        task = screening_cell_tasks()[0]
        evidence = {
            "status": "CONSTRUCTION_PASS",
            "failure_reasons": [],
            "design_inputs_sha256": "a" * 64,
            "family_seed": 123,
            "dgp_and_interp_streams": {"operator_structure": {"used": True}},
            "interp_endpoint_sha256": "b" * 64,
            "family_endpoint_sha256": "c" * 64,
            "family_selected_index": 0,
            "interp_calibration": {"maximum_chi": 0.01},
            "interp_prospective": {"maximum_chi": 0.02},
            "family_calibration": {"maximum_chi": 0.03},
            "family_prospective": {"maximum_chi": 0.04},
            "family_candidate_certificates": [
                {"index": 0, "endpoint_sha256": "c" * 64,
                 "calibration_maximum_chi": 0.03}
            ],
        }
        certificate = {
            "seed": task.seed,
            "rho": task.rho,
            "a3": task.a3,
            "eta": task.eta,
            **evidence,
        }
        for field in evidence:
            with self.subTest(field=field):
                calls = {"fit": 0, "evaluate": 0}

                def forbidden_fit(*args, **kwargs):
                    calls["fit"] += 1
                    raise AssertionError("fit must not run")

                def forbidden_evaluate(*args, **kwargs):
                    calls["evaluate"] += 1
                    raise AssertionError("evaluation must not run")

                panel = SimpleNamespace(
                    fit=object(),
                    truth=object(),
                    w_alt_interp=object(),
                    endpoint_stream_seed=123,
                )
                primitives = ScientificPrimitives(
                    build_native_panel=lambda *args, **kwargs: panel,
                    construct_supported_endpoints=lambda *args, **kwargs: object(),
                    fit_required_comparators=forbidden_fit,
                    fit_dw_joint_tucker=forbidden_fit,
                    evaluate_method=forbidden_evaluate,
                    certificate_evidence=lambda *args, **kwargs: evidence,
                )
                mismatched = deepcopy(certificate)
                mismatched[field] = "mismatch"
                execution = run_screening_cell_fixture(
                    task,
                    construction_certificate=mismatched,
                    config=R006EConfig(),
                    primitives=primitives,
                    attempt_id=PRIMARY_ATTEMPT_ID,
                    role="primary",
                    generated_at="2026-07-18T00:00:00Z",
                    worker_pid=1234,
                    peak_rss_reader=lambda: 4096,
                    fixture_capability=_FIXTURE_CAPABILITY,
                )
                self.assertEqual(calls, {"fit": 0, "evaluate": 0})
                self.assertEqual(len(execution.replications), 4)
                self.assertEqual(len(execution.diagnostics), 4)
                self.assertEqual(len(execution.resources), 4)
                self.assertEqual(len(execution.row_journals), 4)
                self.assertTrue(all(
                    row["failure_code"] == "V2_CERTIFICATE_MISMATCH"
                    and row["fit_success"] == 0
                    and row["scorable"] == 0
                    for row in execution.replications
                ))

    def test_certificate_requires_exact_finite_json_type_exact_schema(self) -> None:
        task = screening_cell_tasks()[0]

        def base_evidence() -> dict[str, object]:
            return {
                "status": "CONSTRUCTION_PASS",
                "failure_reasons": [],
                "design_inputs_sha256": "a" * 64,
                "family_seed": 123,
                "dgp_and_interp_streams": {"operator_structure": {"used": True}},
                "interp_endpoint_sha256": "b" * 64,
                "family_endpoint_sha256": None,
                "family_selected_index": 0,
                "interp_calibration": {"maximum_chi": 0.01},
                "interp_prospective": {"maximum_chi": 0.02},
                "family_calibration": {"maximum_chi": 0.03},
                "family_prospective": {"maximum_chi": 0.04},
                "family_candidate_certificates": [{"index": 0}],
            }

        cases = (
            (
                "missing_nullable",
                lambda certificate, evidence: certificate.pop("family_endpoint_sha256"),
            ),
            ("extra_key", lambda certificate, evidence: certificate.update(extra=object())),
            ("bool_for_integer", lambda certificate, evidence: certificate.update(family_seed=True)),
            (
                "nested_type_drift",
                lambda certificate, evidence: certificate["dgp_and_interp_streams"]
                ["operator_structure"].update(used=1),
            ),
            (
                "nested_signed_zero_drift",
                lambda certificate, evidence: (
                    certificate["interp_calibration"].update(maximum_chi=0.0),
                    evidence["interp_calibration"].update(maximum_chi=-0.0),
                ),
            ),
            (
                "nested_nan",
                lambda certificate, evidence: (
                    certificate["interp_calibration"].update(maximum_chi=math.nan),
                    evidence["interp_calibration"].update(maximum_chi=math.nan),
                ),
            ),
            (
                "nested_object",
                lambda certificate, evidence, sentinel=object(): (
                    certificate["interp_calibration"].update(maximum_chi=sentinel),
                    evidence["interp_calibration"].update(maximum_chi=sentinel),
                ),
            ),
            ("non_string_key", lambda certificate, evidence: certificate.update({1: "x"})),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                evidence = base_evidence()
                certificate = {
                    "seed": task.seed,
                    "rho": task.rho,
                    "a3": task.a3,
                    "eta": task.eta,
                    **deepcopy(evidence),
                }
                mutate(certificate, evidence)
                calls = {"fit": 0, "evaluate": 0}

                def forbidden_fit(*args, **kwargs):
                    calls["fit"] += 1
                    raise AssertionError("fit must not run")

                def forbidden_evaluate(*args, **kwargs):
                    calls["evaluate"] += 1
                    raise AssertionError("evaluation must not run")

                panel = SimpleNamespace(
                    fit=object(), truth=object(), w_alt_interp=object(), endpoint_stream_seed=123
                )
                execution = run_screening_cell_fixture(
                    task,
                    construction_certificate=certificate,
                    config=R006EConfig(),
                    primitives=ScientificPrimitives(
                        build_native_panel=lambda *args, **kwargs: panel,
                        construct_supported_endpoints=lambda *args, **kwargs: object(),
                        fit_required_comparators=forbidden_fit,
                        fit_dw_joint_tucker=forbidden_fit,
                        evaluate_method=forbidden_evaluate,
                        certificate_evidence=lambda *args, **kwargs: evidence,
                    ),
                    attempt_id=PRIMARY_ATTEMPT_ID,
                    role="primary",
                    generated_at="2026-07-18T00:00:00Z",
                    worker_pid=1234,
                    peak_rss_reader=lambda: 4096,
                    fixture_capability=_FIXTURE_CAPABILITY,
                )
                self.assertEqual(calls, {"fit": 0, "evaluate": 0})
                self.assertTrue(all(
                    len(records) == 4
                    for records in (
                        execution.replications,
                        execution.diagnostics,
                        execution.resources,
                        execution.row_journals,
                    )
                ))
                self.assertTrue(all(
                    row["failure_code"] == "V2_CERTIFICATE_MISMATCH"
                    for row in execution.replications
                ))

    def test_success_path_fits_before_evaluation_and_returns_exact_schemas(self) -> None:
        task = screening_cell_tasks()[0]
        evidence = {
            "status": "CONSTRUCTION_PASS",
            "failure_reasons": [],
            "design_inputs_sha256": "a" * 64,
            "family_seed": 123,
            "dgp_and_interp_streams": {"operator_structure": {"used": True}},
            "interp_endpoint_sha256": "b" * 64,
            "family_endpoint_sha256": "c" * 64,
            "family_selected_index": 0,
            "interp_calibration": {"maximum_chi": 0.01},
            "interp_prospective": {"maximum_chi": 0.02},
            "family_calibration": {"maximum_chi": 0.03},
            "family_prospective": {"maximum_chi": 0.04},
            "family_candidate_certificates": [
                {"index": 0, "endpoint_sha256": "c" * 64,
                 "calibration_maximum_chi": 0.03}
            ],
        }
        certificate = {"seed": task.seed, "rho": task.rho, "a3": task.a3,
                       "eta": task.eta, **evidence}
        fit_inputs = object()
        truth = object()
        endpoints = object()
        panel = SimpleNamespace(
            fit=fit_inputs,
            truth=truth,
            w_alt_interp=object(),
            endpoint_stream_seed=123,
        )
        events: list[str] = []

        def comparator_fit(received_fit, *, config, method_seed):
            self.assertIs(received_fit, fit_inputs)
            self.assertNotIn(truth, (received_fit, config, method_seed))
            events.append("comparators")
            return {method: {"method": method} for method in METHODS[:3]}

        def candidate_fit(received_fit, *, config, method_seed):
            self.assertIs(received_fit, fit_inputs)
            self.assertNotIn(truth, (received_fit, config, method_seed))
            events.append("candidate")
            return {"method": METHODS[3]}

        def evaluator(fitted, *, fit, truth: object, endpoints, config):
            self.assertIs(fit, fit_inputs)
            self.assertIs(truth, panel.truth)
            events.append(f"evaluate:{fitted['method']}")
            row: dict[str, object] = {}
            for field in EVALUATOR_ROW_FIELDS:
                if field in EVALUATOR_NULLABLE_FIELDS:
                    row[field] = None
                elif field in SCREENING_FLAG_FIELDS:
                    row[field] = 1
                elif field in EVALUATOR_INTEGER_FIELDS:
                    row[field] = 1
                elif field in EVALUATOR_STRING_FIELDS:
                    row[field] = "available"
                else:
                    row[field] = 1.0
            row.update({
                "method": fitted["method"],
                "fit_sha256": "d" * 64,
                "parameterization": "anchor",
                "fit_success": 1,
                "scorable": 1,
                "fit_diagnostics_json": "{}",
                "endpoint_construction_status": "CONSTRUCTION_PASS",
                "endpoint_failure_reasons_json": "[]",
                "failure_code": None,
                "failure_reason": None,
            })
            return row

        primitives = ScientificPrimitives(
            build_native_panel=lambda *args, **kwargs: panel,
            construct_supported_endpoints=lambda *args, **kwargs: endpoints,
            fit_required_comparators=comparator_fit,
            fit_dw_joint_tucker=candidate_fit,
            evaluate_method=evaluator,
            certificate_evidence=lambda *args, **kwargs: evidence,
        )
        execution = run_screening_cell_fixture(
            task,
            construction_certificate=certificate,
            config=R006EConfig(),
            primitives=primitives,
            attempt_id=REPEAT_ATTEMPT_ID,
            role="repeat",
            generated_at="2026-07-18T00:00:00Z",
            worker_pid=5678,
            peak_rss_reader=lambda: 8192,
            fixture_capability=_FIXTURE_CAPABILITY,
        )
        self.assertEqual(
            events,
            ["comparators", "candidate", *(f"evaluate:{method}" for method in METHODS)],
        )
        collections = (
            (execution.replications, FORMAL_REPLICATION_FIELDS),
            (execution.diagnostics, DIAGNOSTIC_FIELDS),
            (execution.resources, RESOURCE_FIELDS),
            (execution.row_journals, ROW_JOURNAL_FIELDS),
        )
        for records, fields in collections:
            self.assertEqual(len(records), 4)
            self.assertTrue(all(tuple(record) == fields for record in records))
            self.assertEqual(
                tuple(tuple(record[key] for key in ("seed", "rho", "a3", "eta", "method"))
                      for record in records),
                task.method_identities,
            )
        self.assertTrue(all(row["peak_memory_bytes"] == 8192
                            for row in execution.resources))
        self.assertTrue(all(row["worker_pid"] == 5678
                            for row in execution.resources))
        for records, validator in (
            (execution.replications, validate_formal_replication_record),
            (execution.diagnostics, validate_diagnostic_record),
            (execution.resources, validate_resource_record),
            (execution.row_journals, validate_row_journal_record),
        ):
            for record in records:
                self.assertIs(validator(record), record)

    def test_one_evaluation_failure_remains_method_local(self) -> None:
        task = screening_cell_tasks()[0]
        evidence = {
            "status": "CONSTRUCTION_PASS",
            "failure_reasons": [],
            "design_inputs_sha256": "a" * 64,
            "family_seed": 123,
            "dgp_and_interp_streams": {"operator_structure": {"used": True}},
            "interp_endpoint_sha256": "b" * 64,
            "family_endpoint_sha256": "c" * 64,
            "family_selected_index": 0,
            "interp_calibration": {"maximum_chi": 0.01},
            "interp_prospective": {"maximum_chi": 0.02},
            "family_calibration": {"maximum_chi": 0.03},
            "family_prospective": {"maximum_chi": 0.04},
            "family_candidate_certificates": [
                {"index": 0, "endpoint_sha256": "c" * 64,
                 "calibration_maximum_chi": 0.03}
            ],
        }
        certificate = {
            "seed": task.seed, "rho": task.rho, "a3": task.a3,
            "eta": task.eta, **evidence,
        }
        panel = SimpleNamespace(
            fit=object(), truth=object(), w_alt_interp=object(),
            endpoint_stream_seed=123,
        )
        failed_method = METHODS[1]

        def evaluator(fitted, **kwargs):
            row: dict[str, object] = {}
            for field in EVALUATOR_ROW_FIELDS:
                if field in EVALUATOR_NULLABLE_FIELDS:
                    row[field] = None
                elif field in SCREENING_FLAG_FIELDS:
                    row[field] = 1
                elif field in EVALUATOR_INTEGER_FIELDS:
                    row[field] = 1
                elif field in EVALUATOR_STRING_FIELDS:
                    row[field] = "available"
                else:
                    row[field] = 1.0
            row.update({
                "method": fitted["method"],
                "fit_sha256": "d" * 64,
                "parameterization": "anchor",
                "fit_success": 1,
                "scorable": 1,
                "fit_diagnostics_json": "{}",
                "endpoint_construction_status": "CONSTRUCTION_PASS",
                "endpoint_failure_reasons_json": "[]",
                "failure_code": None,
                "failure_reason": None,
            })
            if fitted["method"] == failed_method:
                row.update({
                    "scorable": 0,
                    "failure_code": "EVALUATION_NUMERICAL_FAIL",
                    "failure_reason": "FloatingPointError: fixture",
                })
            return row

        primitives = ScientificPrimitives(
            build_native_panel=lambda *args, **kwargs: panel,
            construct_supported_endpoints=lambda *args, **kwargs: object(),
            fit_required_comparators=lambda *args, **kwargs: {
                method: {"method": method} for method in METHODS[:3]
            },
            fit_dw_joint_tucker=lambda *args, **kwargs: {"method": METHODS[3]},
            evaluate_method=evaluator,
            certificate_evidence=lambda *args, **kwargs: evidence,
        )
        execution = run_screening_cell_fixture(
            task,
            construction_certificate=certificate,
            config=R006EConfig(),
            primitives=primitives,
            attempt_id=PRIMARY_ATTEMPT_ID,
            role="primary",
            generated_at="2026-07-18T00:00:00Z",
            worker_pid=2468,
            peak_rss_reader=lambda: 8192,
            fixture_capability=_FIXTURE_CAPABILITY,
        )
        by_method = {row["method"]: row for row in execution.replications}
        diagnostics = {row["method"]: row for row in execution.diagnostics}
        self.assertEqual(by_method[failed_method]["fit_success"], 1)
        self.assertEqual(by_method[failed_method]["scorable"], 0)
        self.assertEqual(
            by_method[failed_method]["failure_code"],
            "EVALUATION_NUMERICAL_FAIL",
        )
        self.assertTrue(diagnostics[failed_method]["fit_success"])
        self.assertFalse(diagnostics[failed_method]["scorable"])
        self.assertTrue(all(
            row["failure_code"] is None
            for method, row in by_method.items()
            if method != failed_method
        ))
        self.assertTrue(all(
            journal["row_status"] == "RECORDED"
            for journal in execution.row_journals
        ))
        for journal, replication, diagnostic, resource_record in zip(
            execution.row_journals,
            execution.replications,
            execution.diagnostics,
            execution.resources,
        ):
            self.assertEqual(journal["replication_sha256"], _record_sha256(replication))
            self.assertEqual(journal["diagnostic_sha256"], _record_sha256(diagnostic))
            self.assertEqual(journal["resource_sha256"], _record_sha256(resource_record))

    def test_worker_failure_is_retained_and_forces_all_nine_gates_false(self) -> None:
        task = screening_cell_tasks()[3]
        certificate = {
            "seed": task.seed,
            "rho": task.rho,
            "a3": task.a3,
            "eta": task.eta,
            "status": "CONSTRUCTION_PASS",
            "failure_reasons": [],
        }
        execution = retain_worker_failure(
            task,
            construction_certificate=certificate,
            attempt_id=PRIMARY_ATTEMPT_ID,
            role="primary",
            generated_at="2026-07-18T00:00:00Z",
            worker_pid=4321,
            peak_memory_bytes=2048,
        )
        for records in (
            execution.replications,
            execution.diagnostics,
            execution.resources,
            execution.row_journals,
        ):
            self.assertEqual(len(records), 4)
            self.assertEqual(
                tuple(tuple(row[key] for key in ("seed", "rho", "a3", "eta", "method"))
                      for row in records),
                task.method_identities,
            )
        for row in execution.replications:
            self.assertEqual(row["failure_code"], "V2_WORKER_FAILURE")
            self.assertEqual(row["failure_reason"], "worker_failure")
            self.assertEqual(
                adapt_runner_failure_gates(row),
                {field: False for field in SUMMARY_FIELDS},
            )
        for records, validator in (
            (execution.replications, validate_formal_replication_record),
            (execution.diagnostics, validate_diagnostic_record),
            (execution.resources, validate_resource_record),
            (execution.row_journals, validate_row_journal_record),
        ):
            for record in records:
                self.assertIs(validator(record), record)
        self.assertFalse(hasattr(execution, "resubmit"))
        self.assertFalse(hasattr(execution, "replace"))

    def test_hostile_certificate_retention_is_total_bounded_and_deterministic(self) -> None:
        task = screening_cell_tasks()[3]
        hostile_certificates = (
            {"extra": object()},
            {1: "x"},
            {"x": math.nan},
            {"x": object()},
        )
        provenance_values = set()
        for certificate in hostile_certificates:
            with self.subTest(certificate=repr(certificate)):
                execution = retain_worker_failure(
                    task,
                    construction_certificate=certificate,
                    attempt_id=PRIMARY_ATTEMPT_ID,
                    role="primary",
                    generated_at="2026-07-18T00:00:00Z",
                    worker_pid=4321,
                    peak_memory_bytes=2048,
                )
                self.assertTrue(all(
                    len(records) == 4
                    for records in (
                        execution.replications,
                        execution.diagnostics,
                        execution.resources,
                        execution.row_journals,
                    )
                ))
                provenance_values.add(execution.replications[0]["fit_diagnostics_json"])
        self.assertEqual(len(provenance_values), 1)
        self.assertEqual(
            json.loads(provenance_values.pop()),
            {
                "construction_support_provenance": {"certificate_state": "malformed"},
                "runner_failure_code": "V2_WORKER_FAILURE",
                "runner_failure_reason": "worker_failure",
            },
        )

    def test_complete_governance_fixture_role_has_four_exact_320_identity_sets(self) -> None:
        executions = []
        for task in screening_cell_tasks():
            executions.append(retain_worker_failure(
                task,
                construction_certificate={
                    "seed": task.seed,
                    "rho": task.rho,
                    "a3": task.a3,
                    "eta": task.eta,
                    "status": "CONSTRUCTION_PASS",
                    "failure_reasons": [],
                },
                attempt_id=PRIMARY_ATTEMPT_ID,
                role="primary",
                generated_at="2026-07-18T00:00:00Z",
                worker_pid=999,
                peak_memory_bytes=1024,
            ))
        role = combine_cell_executions(tuple(executions), governance_only=True)
        expected = tuple(
            (seed, rho, a3, eta, method)
            for seed in SCREENING_SEEDS
            for rho, a3, eta in primary_cells()
            for method in METHODS
        )
        for records in (
            role.replications,
            role.diagnostics,
            role.resources,
            role.row_journals,
        ):
            self.assertEqual(len(records), 320)
            self.assertEqual(
                tuple(tuple(row[key] for key in ("seed", "rho", "a3", "eta", "method"))
                      for row in records),
                expected,
            )
        for journal, replication, diagnostic, resource_record in zip(
            role.row_journals,
            role.replications,
            role.diagnostics,
            role.resources,
        ):
            self.assertEqual(
                journal["replication_sha256"], _record_sha256(dict(replication))
            )
            self.assertEqual(
                journal["diagnostic_sha256"], _record_sha256(dict(diagnostic))
            )
            self.assertEqual(
                journal["resource_sha256"], _record_sha256(dict(resource_record))
            )
        with self.assertRaisesRegex(ValueError, "80 cell executions"):
            combine_cell_executions(tuple(executions[:-1]), governance_only=True)
        mutations = (
            ("replications", "runtime_seconds", 1.0),
            ("diagnostics", "generated_at", "2026-07-18T00:00:01Z"),
            ("resources", "peak_memory_bytes", 2048),
            ("row_journals", "replication_sha256", "f" * 64),
        )
        for attribute, field, replacement in mutations:
            mutated = deepcopy(tuple(executions))
            getattr(mutated[0], attribute)[0][field] = replacement
            with self.subTest(attribute=attribute, field=field):
                with self.assertRaisesRegex(SchemaValidationError, "hash binding"):
                    combine_cell_executions(mutated, governance_only=True)

        original_runtime = role.replications[0]["runtime_seconds"]
        executions[0].replications[0]["runtime_seconds"] = original_runtime + 1.0
        self.assertEqual(role.replications[0]["runtime_seconds"], original_runtime)
        for records in (
            role.replications,
            role.diagnostics,
            role.resources,
            role.row_journals,
        ):
            with self.assertRaises(TypeError):
                records[0][next(iter(records[0]))] = "forbidden"

    def test_production_bundle_names_frozen_scientific_primitives_without_calling(self) -> None:
        primitives = production_scientific_primitives()
        self.assertIs(primitives.build_native_panel, build_native_panel)
        self.assertIs(
            primitives.construct_supported_endpoints,
            construct_supported_endpoints,
        )
        self.assertIs(primitives.fit_required_comparators, fit_required_comparators)
        self.assertIs(primitives.fit_dw_joint_tucker, fit_dw_joint_tucker)
        self.assertIs(primitives.evaluate_method, evaluate_method)
        self.assertEqual(
            primitives.certificate_evidence.__name__,
            "_runtime_certificate_evidence",
        )


if __name__ == "__main__":
    unittest.main()
