"""Fixture-only tests for E3 candidate-package construction.

These tests materialize static manifests in temporary directories.  They never
generate a topology, fit an estimator, calculate a response, or create a
scientific quarantine output directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.experiments import e3_family2_candidate_package as package
from scripts.experiments import e3_family2_preoutcome as preoutcome


class E3Family2CandidatePackageTests(unittest.TestCase):
    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_gate_receipt(self, root: Path) -> Path:
        receipt = root / package.GATE_RECEIPT_FILENAME
        stdout = ""
        stderr = (
            ".\n----------------------------------------------------------------------\n"
            "Ran 1 test in 0.001s\n\nOK\n"
        )
        payload = {
            "schema_version": package.gate_receipt.SCHEMA_VERSION,
            "verdict": "PASS",
            "command": package.gate_receipt._expected_command(),
            "suite_modules": list(package.gate_receipt.GATE_TEST_MODULES),
            "suite_sha256": package.gate_receipt._suite_hashes(),
            "recorder": package.gate_receipt._recorder_identity(),
            "started_at": "2026-07-31T00:00:00Z",
            "completed_at": "2026-07-31T00:00:01Z",
            "returncode": 0,
            "tests_run": 1,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": package.gate_receipt._sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": package.gate_receipt._sha256_bytes(stderr.encode("utf-8")),
            "scientific_execution": "NOT_AUTHORIZED",
        }
        receipt.write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )
        return receipt

    def test_candidate_package_is_static_complete_and_not_authorized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            receipt = self._write_gate_receipt(root)
            package_root = root / "candidate-package"
            quarantine_root = root / "e3-fixture-quarantine"

            built = package.build_candidate_ready_package(
                package_root,
                candidate_id="e3-fixture-candidate-v1",
                quarantine_output_root=quarantine_root,
                gate_test_receipt_path=receipt,
            )

            self.assertEqual(built.status, "CANDIDATE_READY_NOT_AUTHORIZED")
            self.assertTrue(built.candidate_path.is_file())
            self.assertEqual(len(built.candidate_sha256), 64)
            self.assertFalse(quarantine_root.exists())
            candidate = json.loads(built.candidate_path.read_text(encoding="utf-8"))
            self.assertIn(
                str(package.AUTHORIZED_EXECUTOR_PATH.resolve()),
                candidate["bindings"]["source_hashes"],
            )
            preoutcome._validate_execution_candidate_shape(candidate)
            preoutcome._validate_source_hashes(candidate["bindings"])
            preoutcome._validate_dependency_hashes(candidate["bindings"])
            preoutcome._validate_preoutcome_artifacts(candidate["bindings"])
            preoutcome._validate_synthetic_inputs(candidate["bindings"])
            preoutcome._validate_configuration(candidate["bindings"])
            preoutcome._validate_bootstrap_history_bindings(candidate["bindings"])
            self.assertEqual(candidate["trust_evidence"]["detached_signature"], "PENDING")
            for artifact_id, path in built.artifact_paths.items():
                verified = preoutcome.verify_preoutcome_artifact(
                    path, artifact_id=artifact_id, require_candidate_ready=True
                )
                self.assertEqual(verified["scientific_execution"], "NOT_AUTHORIZED")

    def test_builder_refuses_stale_receipt_before_creating_package_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            receipt = self._write_gate_receipt(root)
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            payload["test_suite_sha256"] = "0" * 64
            receipt.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            package_root = root / "candidate-package"

            with self.assertRaisesRegex(package.CandidatePackageError, "receipt"):
                package.build_candidate_ready_package(
                    package_root,
                    candidate_id="e3-fixture-candidate-v1",
                    quarantine_output_root=root / "e3-fixture-quarantine",
                    gate_test_receipt_path=receipt,
                )

            self.assertFalse(package_root.exists())

    def test_v2_candidate_binds_rank_history_and_cross_generator_failure_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            built = package.build_candidate_ready_package(
                root / "candidate-package",
                candidate_id="e3-fixture-candidate-v2",
                quarantine_output_root=root / "e3-fixture-quarantine",
                gate_test_receipt_path=self._write_gate_receipt(root),
            )

            candidate = json.loads(built.candidate_path.read_text(encoding="utf-8"))
            specification = json.loads(
                package.SYNTHETIC_SPECIFICATION_PATH.read_text(encoding="utf-8")
            )
            gate = specification["uncertainty"]["bootstrap_refit_history"]
            self.assertEqual(gate["rank_aware_start_times"], {"1": 14, "2": 14, "3": 15})
            self.assertEqual(gate["minimum_valid_refit_opportunities_per_allowed_rank"], 2)
            self.assertEqual(candidate["bindings"]["configuration"]["bootstrap_refit_history"], gate)

            tuning_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["tuning_split_manifest"]["path"]
            )
            tuning_artifact = json.loads(tuning_path.read_text(encoding="utf-8"))
            self.assertEqual(tuning_artifact["content"]["bootstrap_refit_history"], gate)

            boundary = specification["stability"]["cross_generator_failure_boundary"]
            self.assertEqual(specification["stability"]["threshold"], 0.98)
            self.assertEqual(
                candidate["bindings"]["configuration"]["cross_generator_failure_boundary"], boundary
            )
            self.assertEqual(boundary["threshold_relaxation"], "PROHIBITED")
            self.assertEqual(boundary["stable_cell_selection"], "PROHIBITED")

            failure_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["failure_metric_schema"]["path"]
            )
            failure_artifact = json.loads(failure_path.read_text(encoding="utf-8"))
            self.assertEqual(
                failure_artifact["content"]["cross_generator_instability_policy"],
                "retain_as_scientific_failure_boundary_without_threshold_relaxation_or_stable_cell_selection",
            )

    def test_v4_candidate_binds_recursive_bootstrap_and_per_replicate_retuning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            built = package.build_candidate_ready_package(
                root / "candidate-package",
                candidate_id="e3-fixture-candidate-v4",
                quarantine_output_root=root / "e3-fixture-quarantine",
                gate_test_receipt_path=self._write_gate_receipt(root),
            )

            candidate = json.loads(built.candidate_path.read_text(encoding="utf-8"))
            specification = json.loads(
                package.SYNTHETIC_SPECIFICATION_PATH.read_text(encoding="utf-8")
            )
            procedure = specification["uncertainty"]["bootstrap_procedure"]
            self.assertEqual(specification["schema_version"], "e3-synthetic-input-v4")
            self.assertEqual(
                procedure["method"],
                "recursive_residual_circular_moving_block_bootstrap",
            )
            self.assertEqual(procedure["lag_feature_source"], "pseudo_response_history")
            self.assertTrue(procedure["retune_inside_bootstrap"])
            self.assertEqual(procedure["retune_candidate_list"], [1, 2, 3])
            self.assertEqual(procedure["failure_retention"], "all_replicates")
            self.assertEqual(
                candidate["bindings"]["configuration"]["bootstrap_procedure"],
                procedure,
            )

            tuning_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["tuning_split_manifest"]["path"]
            )
            tuning_artifact = json.loads(tuning_path.read_text(encoding="utf-8"))
            self.assertEqual(tuning_artifact["content"]["bootstrap_procedure"], procedure)

    def test_v4_candidate_binds_domain_stability_before_any_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            built = package.build_candidate_ready_package(
                root / "candidate-package",
                candidate_id="e4-fixture-candidate-v4",
                quarantine_output_root=root / "e4-fixture-quarantine",
                gate_test_receipt_path=self._write_gate_receipt(root),
            )

            candidate = json.loads(built.candidate_path.read_text(encoding="utf-8"))
            specification = json.loads(
                package.SYNTHETIC_SPECIFICATION_PATH.read_text(encoding="utf-8")
            )
            domain_stability = specification["stability"]["domain_uniform_envelope"]
            self.assertEqual(
                domain_stability,
                {
                    "value": 0.90,
                    "norm": "nodewise_l1_over_retained_blocks",
                    "application_stage": "after_fit_before_query",
                    "query_topology_access": "PROHIBITED",
                    "applies_to": [
                        "selection",
                        "evaluation",
                        "recursive_bootstrap_refit",
                        "bootstrap_retuning",
                    ],
                    "topology_domain": "maximum_absolute_row_sum_at_most_one",
                },
            )
            self.assertEqual(specification["stability"]["threshold"], 0.98)
            self.assertEqual(
                candidate["bindings"]["configuration"]["domain_stability"],
                domain_stability,
            )

            query_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["family2_query_contract"]["path"]
            )
            query_artifact = json.loads(query_path.read_text(encoding="utf-8"))
            self.assertEqual(query_artifact["content"]["domain_stability"], domain_stability)

            tuning_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["tuning_split_manifest"]["path"]
            )
            tuning_artifact = json.loads(tuning_path.read_text(encoding="utf-8"))
            self.assertEqual(tuning_artifact["content"]["domain_stability"], domain_stability)

    def test_legacy_v3_specification_is_rejected(self) -> None:
        legacy_path = (
            package.ROOT
            / "refine-logs"
            / "e3_family2_inputs"
            / "synthetic-e3-v3.json"
        )
        with unittest.mock.patch.object(
            package, "SYNTHETIC_SPECIFICATION_PATH", legacy_path
        ):
            with self.assertRaisesRegex(package.CandidatePackageError, "exact frozen E3 v4"):
                package._load_frozen_specification()

    def test_builder_refuses_any_drift_from_the_exact_v4_specification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            specification = json.loads(
                package.SYNTHETIC_SPECIFICATION_PATH.read_text(encoding="utf-8")
            )
            specification["lag_order"] = 2
            drifted_path = Path(temporary_directory) / "synthetic-e3-v4.json"
            drifted_path.write_text(json.dumps(specification, sort_keys=True), encoding="utf-8")

            with mock.patch.object(package, "SYNTHETIC_SPECIFICATION_PATH", drifted_path):
                with self.assertRaisesRegex(
                    package.CandidatePackageError, "exact frozen E3 v4 specification"
                ):
                    package._load_frozen_specification()

    def test_preoutcome_refuses_a_hash_valid_tuning_gate_that_differs_from_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            built = package.build_candidate_ready_package(
                root / "candidate-package",
                candidate_id="e3-fixture-candidate-v2",
                quarantine_output_root=root / "e3-fixture-quarantine",
                gate_test_receipt_path=self._write_gate_receipt(root),
            )
            candidate = json.loads(built.candidate_path.read_text(encoding="utf-8"))
            tuning_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["tuning_split_manifest"]["path"]
            )
            tuning_artifact = json.loads(tuning_path.read_text(encoding="utf-8"))
            tampered_gate = dict(tuning_artifact["content"]["bootstrap_refit_history"])
            tampered_gate["allowed_ranks"] = [1]
            tampered_gate["rank_aware_start_times"] = {"1": 14}
            tuning_artifact["content"]["bootstrap_refit_history"] = tampered_gate
            artifact_body = {
                key: value for key, value in tuning_artifact.items() if key != "artifact_sha256"
            }
            tuning_artifact["artifact_sha256"] = package.artifact_schemas.canonical_sha256(
                artifact_body
            )
            tuning_path.write_text(json.dumps(tuning_artifact, sort_keys=True), encoding="utf-8")
            candidate["bindings"]["preoutcome_artifacts"]["tuning_split_manifest"]["sha256"] = (
                self._sha256(tuning_path)
            )

            bindings = candidate["bindings"]
            preoutcome._validate_execution_candidate_shape(candidate)
            preoutcome._validate_preoutcome_artifacts(bindings)
            preoutcome._validate_configuration(bindings)
            with self.assertRaisesRegex(preoutcome.ContractError, "does not match"):
                preoutcome._validate_bootstrap_history_bindings(bindings)

    def test_hash_valid_domain_stability_drift_is_semantically_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            built = package.build_candidate_ready_package(
                root / "candidate-package",
                candidate_id="e4-domain-drift-fixture",
                quarantine_output_root=root / "e4-fixture-quarantine",
                gate_test_receipt_path=self._write_gate_receipt(root),
            )
            candidate = json.loads(built.candidate_path.read_text(encoding="utf-8"))
            query_path = Path(
                candidate["bindings"]["preoutcome_artifacts"]["family2_query_contract"]["path"]
            )
            query_artifact = json.loads(query_path.read_text(encoding="utf-8"))
            query_artifact["content"]["domain_stability"]["value"] = 0.95
            artifact_body = {
                key: value for key, value in query_artifact.items() if key != "artifact_sha256"
            }
            query_artifact["artifact_sha256"] = package.artifact_schemas.canonical_sha256(
                artifact_body
            )
            query_path.write_text(json.dumps(query_artifact, sort_keys=True), encoding="utf-8")
            candidate["bindings"]["preoutcome_artifacts"]["family2_query_contract"]["sha256"] = (
                self._sha256(query_path)
            )

            with self.assertRaisesRegex(preoutcome.ContractError, "domain stability"):
                preoutcome._validate_preoutcome_artifacts(candidate["bindings"])

    def test_builder_never_replaces_an_existing_package_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            receipt = self._write_gate_receipt(root)
            package_root = root / "candidate-package"
            package_root.mkdir()
            sentinel = package_root / "reviewed-sentinel.txt"
            sentinel.write_text("preserve\n", encoding="utf-8")

            with self.assertRaisesRegex(package.CandidatePackageError, "new and absent"):
                package.build_candidate_ready_package(
                    package_root,
                    candidate_id="e3-fixture-candidate-v1",
                    quarantine_output_root=root / "e3-fixture-quarantine",
                    gate_test_receipt_path=receipt,
                )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve\n")

    def test_builder_exposes_no_scientific_executor_or_cli(self) -> None:
        self.assertFalse(hasattr(package, "run"))
        self.assertFalse(hasattr(package, "main"))
        self.assertFalse(hasattr(package.CandidatePackage, "execute"))

    def test_gate_receipt_binds_the_candidate_package_suite(self) -> None:
        self.assertFalse(hasattr(package, "build_authorization_gate_test_receipt"))
        self.assertIn(
            "scripts.experiments.test_e3_family2_candidate_package",
            package.gate_receipt.GATE_TEST_MODULES,
        )
        self.assertIn(
            "scripts.experiments.test_e3_family2_gate_receipt",
            package.gate_receipt.GATE_TEST_MODULES,
        )


if __name__ == "__main__":
    unittest.main()
