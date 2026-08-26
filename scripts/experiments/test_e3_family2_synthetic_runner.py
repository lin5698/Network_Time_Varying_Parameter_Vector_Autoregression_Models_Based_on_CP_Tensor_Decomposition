"""Public tests for the fail-closed E3-1 source-only runner scaffold.

No test in this module invokes topology generation, estimation, response
evaluation, output writing, or a production scientific executor.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.experiments import e3_family2_candidate_ready as candidate_ready
from scripts.experiments import e3_family2_preoutcome as e3
from scripts.experiments import e3_family2_synthetic_runner as runner


class E3Family2SyntheticRunnerTests(unittest.TestCase):
    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _proof_review_payload(proof_packet_sha256: str) -> dict[str, object]:
        return {
            "schema_version": "e3-family2-proof-blind-review-v1",
            "audit_skill": "proof-checker",
            "verdict": "PASS",
            "proof_packet_sha256": proof_packet_sha256,
            "reviewer_model": "gpt-5.6-terra",
            "reviewer_reasoning": "xhigh",
            "review_mode": "fresh_blind_read_only",
            "scientific_execution": "NOT_AUTHORIZED",
            "open_findings": [],
            "generated_at": "2026-07-22T00:00:00Z",
        }

    def _candidate_ready_content_by_id(self, root: Path) -> dict[str, dict[str, object]]:
        domain_stability = e3.artifact_schemas.source_only_content(
            "family2_query_contract"
        )["domain_stability"]
        content_by_id: dict[str, dict[str, object]] = {}
        for artifact_id in e3.REQUIRED_PREOUTCOME_ARTIFACT_IDS:
            content = e3.artifact_schemas.source_only_content(artifact_id)
            if artifact_id == "family2_query_contract":
                content["node_order"] = {
                    "hash_algorithm": "sha256",
                    "node_order_sha256": "1" * 64,
                }
                content["topology_preprocessing"]["normalization"] = "identity"
                content["lag_order"] = 1
                content["maximum_horizon"] = 3
            elif artifact_id == "family2_factorization_proof_packet":
                receipt = root / "proof-review-receipt.json"
                receipt.write_text(
                    json.dumps(
                        self._proof_review_payload(content["proof_packet"]["sha256"]),
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
                content["independent_blind_review"] = {
                    "status": "PASS",
                    "receipt": {"path": str(receipt), "sha256": self._sha256(receipt)},
                }
            elif artifact_id == "comparator_registry":
                native_proof = root / "native-evaluator-proof.md"
                native_proof.write_text("fixture native evaluator proof\n", encoding="utf-8")
                reference = {"path": str(native_proof), "sha256": self._sha256(native_proof)}
                content["registry_state"] = "FROZEN"
                content["records"] = [
                    {
                        "comparator_id": "native-local",
                        "role": "native_local_structured",
                        "source_identity": "fixture-native-local-v1",
                        "parameterization": {"penalty": "fixed"},
                        "fit_signature": content["required_interface"]["fit"],
                        "evaluate_signature": content["required_interface"]["evaluate"],
                        "endpoint_shape": "full_operator_and_finite_horizon_response",
                        "native_evaluator_proof": reference,
                    },
                    {
                        "comparator_id": "fixed-basis",
                        "role": "fixed_low_rank_or_basis",
                        "source_identity": "fixture-fixed-basis-v1",
                        "parameterization": {"rank": 2},
                        "fit_signature": content["required_interface"]["fit"],
                        "evaluate_signature": content["required_interface"]["evaluate"],
                        "endpoint_shape": "full_operator_and_finite_horizon_response",
                        "native_evaluator_proof": reference,
                    },
                ]
            elif artifact_id == "tuning_split_manifest":
                content = {
                    "manifest_state": "FROZEN",
                    "selection_loss": "observed_topology_one_step_prediction",
                    "truth_access": "PROHIBITED",
                    "chronological_partitions": {
                        "train": {"start": 0, "stop": 19},
                        "validation": {"start": 20, "stop": 29},
                        "evaluation": {"start": 30, "stop": 39},
                    },
                    "candidate_lists": {"native-local": ["fixed"], "fixed-basis": [2]},
                    "maximum_budget": 1,
                    "tie_break": "lexicographic_comparator_id",
                    "random_streams": {"root_seed": 620001},
                    "bootstrap_refit_history": {
                        "method": "fixed_rank_basis",
                        "local_window": 12,
                        "minimum_local_estimates": 2,
                        "allowed_ranks": [2],
                        "minimum_valid_refit_opportunities_per_allowed_rank": 2,
                        "evaluation_target_times": [39],
                        "rank_aware_start_times": {"2": 14},
                    },
                    "bootstrap_procedure": {
                        "method": "recursive_residual_circular_moving_block_bootstrap",
                        "initial_history": "observed_prefix_before_rank_aware_start",
                        "lag_feature_source": "pseudo_response_history",
                        "parameter_selection": "validation_loss_on_each_pseudo_series",
                        "retune_inside_bootstrap": True,
                        "retune_candidate_list": [1, 2, 3],
                        "failure_retention": "all_replicates",
                    },
                    "domain_stability": domain_stability,
                }
            elif artifact_id == "authorization_gate_tests":
                receipt = root / "gate-test-receipt.json"
                stdout = ""
                stderr = (
                    ".\n----------------------------------------------------------------------\n"
                    "Ran 1 test in 0.001s\n\nOK\n"
                )
                receipt.write_text(
                    json.dumps(
                        {
                            "schema_version": e3.artifact_schemas.gate_receipt.SCHEMA_VERSION,
                            "verdict": "PASS",
                            "command": e3.artifact_schemas.gate_receipt._expected_command(),
                            "suite_modules": list(
                                e3.artifact_schemas.gate_receipt.GATE_TEST_MODULES
                            ),
                            "suite_sha256": e3.artifact_schemas.gate_receipt._suite_hashes(),
                            "recorder": e3.artifact_schemas.gate_receipt._recorder_identity(),
                            "started_at": "2026-07-31T00:00:00Z",
                            "completed_at": "2026-07-31T00:00:01Z",
                            "returncode": 0,
                            "tests_run": 1,
                            "stdout": stdout,
                            "stderr": stderr,
                            "stdout_sha256": e3.artifact_schemas.gate_receipt._sha256_bytes(
                                stdout.encode("utf-8")
                            ),
                            "stderr_sha256": e3.artifact_schemas.gate_receipt._sha256_bytes(
                                stderr.encode("utf-8")
                            ),
                            "scientific_execution": "NOT_AUTHORIZED",
                        },
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
                content["verification_receipt"] = {
                    "status": "PASS",
                    "receipt": {"path": str(receipt), "sha256": self._sha256(receipt)},
                }
            elif artifact_id == "duplicate_and_claim_audit_design":
                content["design_state"] = "FROZEN"
            content_by_id[artifact_id] = content
        return content_by_id

    def _write_candidate(
        self,
        root: Path,
        *,
        quarantine_root: Path,
        bind_synthetic_runner: bool = True,
        source_only_artifact_id: str | None = None,
    ) -> tuple[Path, str]:
        artifact_root = root / "candidate-ready-artifacts"
        written = candidate_ready.materialize_candidate_ready_artifacts(
            artifact_root,
            content_by_id=self._candidate_ready_content_by_id(root),
        )
        if source_only_artifact_id is not None:
            e3.artifact_schemas.write_preoutcome_artifact(
                written[source_only_artifact_id],
                artifact_id=source_only_artifact_id,
                lifecycle=e3.artifact_schemas.SOURCE_ONLY,
                content=e3.artifact_schemas.source_only_content(source_only_artifact_id),
            )
        preoutcome_artifacts = {
            artifact_id: {"path": str(path), "sha256": self._sha256(path)}
            for artifact_id, path in written.items()
        }
        synthetic_specification = root / "synthetic-specification.json"
        synthetic_specification.write_text(
            json.dumps({"input_route": "synthetic_only", "fixture": "no-outcomes"}),
            encoding="utf-8",
        )
        dependency_lock = root / "dependency-lock.json"
        dependency_lock.write_text(
            json.dumps({"runtime": "stdlib-only", "scientific_execution": "not-authorized"}),
            encoding="utf-8",
        )
        domain_stability = e3.artifact_schemas.source_only_content(
            "family2_query_contract"
        )["domain_stability"]
        configuration = {
            "topology_generators": ["frozen-synthetic-generator"],
            "scales": [20, 50],
            "panel_lengths": [40],
            "horizons": [1, 3],
            "seeds": [620001],
            "split_policy": "chronological",
            "tuning_budget": 1,
            "comparators": ["native-local-structured"],
            "bootstrap_refit_history": {
                "method": "fixed_rank_basis",
                "local_window": 12,
                "minimum_local_estimates": 2,
                "allowed_ranks": [2],
                "minimum_valid_refit_opportunities_per_allowed_rank": 2,
                "evaluation_target_times": [39],
                "rank_aware_start_times": {"2": 14},
            },
            "bootstrap_procedure": {
                "method": "recursive_residual_circular_moving_block_bootstrap",
                "initial_history": "observed_prefix_before_rank_aware_start",
                "lag_feature_source": "pseudo_response_history",
                "parameter_selection": "validation_loss_on_each_pseudo_series",
                "retune_inside_bootstrap": True,
                "retune_candidate_list": [1, 2, 3],
                "failure_retention": "all_replicates",
            },
            "domain_stability": domain_stability,
            "cross_generator_failure_boundary": {
                "query_class": "cross_generator",
                "instability": "scientific_failure_boundary",
                "threshold_relaxation": "PROHIBITED",
                "stable_cell_selection": "PROHIBITED",
                "retention": "all_predeclared_cells",
            },
        }
        static_runner = Path(e3.__file__).resolve()
        schema_module = Path(e3.artifact_schemas.__file__).resolve()
        source_hashes = {
            str(static_runner): self._sha256(static_runner),
            str(schema_module): self._sha256(schema_module),
        }
        if bind_synthetic_runner:
            synthetic_runner = Path(runner.__file__).resolve()
            source_hashes[str(synthetic_runner)] = self._sha256(synthetic_runner)
        candidate = {
            "schema_version": e3.EXECUTION_CANDIDATE_SCHEMA_VERSION,
            "candidate_id": "fixture-e3-family2-candidate",
            "execution": {
                "invocation_limit": 1,
                "input_route": "synthetic_only",
                "excluded_routes": ["RCEP", "NYC", "R006e", "R006f"],
                "prohibitions": [
                    "outcome_promotion",
                    "downstream_builds",
                    "manuscript_promotion",
                    "audit_status_changes",
                ],
            },
            "bindings": {
                "runner_sha256": self._sha256(static_runner),
                "source_hashes": source_hashes,
                "dependency_hashes": {str(dependency_lock): self._sha256(dependency_lock)},
                "preoutcome_artifacts": preoutcome_artifacts,
                "inputs": [
                    {
                        "input_id": "synthetic-specification",
                        "path": str(synthetic_specification),
                        "sha256": self._sha256(synthetic_specification),
                    }
                ],
                "configuration": configuration,
                "configuration_sha256": e3.artifact_schemas.canonical_sha256(configuration),
                "quarantine_output_root": str(quarantine_root),
            },
            "trust_evidence": {
                "pinned_key_id": "fixture-production-key",
                "trust_policy_id": "fixture-production-policy",
                "detached_signature": "fixture-detached-signature",
            },
        }
        candidate_path = root / "candidate.json"
        candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
        return candidate_path, self._sha256(candidate_path)

    def _write_approval(
        self,
        root: Path,
        *,
        candidate_path: Path,
        candidate_sha256: str,
        candidate_sha_override: str | None = None,
    ) -> tuple[Path, str]:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        bindings = candidate["bindings"]
        approval = {
            "schema_version": runner.EXECUTION_APPROVAL_SCHEMA_VERSION,
            "approval_id": "fixture-e3-family2-synthetic-approval",
            "decision": "AUTHORIZE",
            "candidate_sha256": candidate_sha_override or candidate_sha256,
            "candidate_id": candidate["candidate_id"],
            "synthetic_runner_sha256": self._sha256(Path(runner.__file__).resolve()),
            "execution": candidate["execution"],
            "bindings": {
                "source_hashes_sha256": e3.artifact_schemas.canonical_sha256(
                    bindings["source_hashes"]
                ),
                "dependency_hashes_sha256": e3.artifact_schemas.canonical_sha256(
                    bindings["dependency_hashes"]
                ),
                "configuration_sha256": bindings["configuration_sha256"],
                "preoutcome_artifacts_sha256": e3.artifact_schemas.canonical_sha256(
                    bindings["preoutcome_artifacts"]
                ),
                "quarantine_output_root": bindings["quarantine_output_root"],
            },
            "trust_evidence": candidate["trust_evidence"],
        }
        approval_path = root / "approval.json"
        approval_path.write_text(json.dumps(approval, sort_keys=True), encoding="utf-8")
        return approval_path, self._sha256(approval_path)

    def test_candidate_ready_materializer_requires_complete_caller_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content_by_id = self._candidate_ready_content_by_id(root)
            content_by_id.pop("failure_metric_schema")
            artifact_root = root / "candidate-ready-artifacts"

            with self.assertRaisesRegex(candidate_ready.CandidateReadyArtifactError, "complete"):
                candidate_ready.materialize_candidate_ready_artifacts(
                    artifact_root,
                    content_by_id=content_by_id,
                )

            self.assertFalse(artifact_root.exists())

    def test_candidate_ready_materializer_emits_only_validated_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact_root = root / "candidate-ready-artifacts"
            written = candidate_ready.materialize_candidate_ready_artifacts(
                artifact_root,
                content_by_id=self._candidate_ready_content_by_id(root),
            )

            self.assertEqual(set(written), set(e3.REQUIRED_PREOUTCOME_ARTIFACT_IDS))
            self.assertEqual(
                sorted(path.name for path in artifact_root.iterdir()),
                sorted(e3.artifact_schemas.ARTIFACT_FILENAMES.values()),
            )
            for artifact_id, path in written.items():
                verified = e3.verify_preoutcome_artifact(
                    path,
                    artifact_id=artifact_id,
                    require_candidate_ready=True,
                )
                self.assertEqual(verified["lifecycle"], e3.artifact_schemas.CANDIDATE_READY)
                self.assertEqual(verified["scientific_execution"], "NOT_AUTHORIZED")

    def test_candidate_ready_materializer_never_replaces_an_existing_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact_root = root / "candidate-ready-artifacts"
            artifact_root.mkdir()
            sentinel = artifact_root / "reviewed-sentinel.txt"
            sentinel.write_text("preserve existing package\n", encoding="utf-8")

            with self.assertRaisesRegex(candidate_ready.CandidateReadyArtifactError, "absent"):
                candidate_ready.materialize_candidate_ready_artifacts(
                    artifact_root,
                    content_by_id=self._candidate_ready_content_by_id(root),
                )

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve existing package\n")
            self.assertEqual(sorted(path.name for path in artifact_root.iterdir()), [sentinel.name])

    def test_fixture_static_validation_returns_no_execution_capability_or_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root,
                quarantine_root=quarantine_root,
            )
            approval_path, approval_sha256 = self._write_approval(
                root,
                candidate_path=candidate_path,
                candidate_sha256=candidate_sha256,
            )

            receipt = runner.verify_fixture_synthetic_authorization(
                candidate_path=candidate_path,
                expected_candidate_sha256=candidate_sha256,
                approval_path=approval_path,
                expected_approval_sha256=approval_sha256,
                expected_quarantine_root=quarantine_root,
            )

            self.assertEqual(receipt.status, runner.STATIC_VALIDATED_NO_EXECUTION)
            self.assertEqual(receipt.candidate_sha256, candidate_sha256)
            self.assertEqual(receipt.approval_sha256, approval_sha256)
            self.assertFalse(quarantine_root.exists())
            self.assertFalse(hasattr(receipt, "run"))

    def test_fixture_static_validation_requires_v3_bootstrap_cross_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root,
                quarantine_root=quarantine_root,
            )
            approval_path, approval_sha256 = self._write_approval(
                root,
                candidate_path=candidate_path,
                candidate_sha256=candidate_sha256,
            )

            with mock.patch.object(
                runner.preoutcome,
                "_validate_bootstrap_history_bindings",
                side_effect=runner.preoutcome.ContractError("bootstrap cross-binding drift"),
            ):
                with self.assertRaisesRegex(runner.AuthorizationError, "bootstrap"):
                    runner.verify_fixture_synthetic_authorization(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        approval_path=approval_path,
                        expected_approval_sha256=approval_sha256,
                        expected_quarantine_root=quarantine_root,
                    )

            self.assertFalse(quarantine_root.exists())

    def test_fixture_validation_rejects_malformed_trust_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root,
                quarantine_root=quarantine_root,
            )
            approval_path, approval_sha256 = self._write_approval(
                root,
                candidate_path=candidate_path,
                candidate_sha256=candidate_sha256,
            )
            approval = json.loads(approval_path.read_text(encoding="utf-8"))
            approval["trust_evidence"]["detached_signature"] = ""
            approval_path.write_text(json.dumps(approval, sort_keys=True), encoding="utf-8")
            approval_sha256 = self._sha256(approval_path)

            with self.assertRaisesRegex(runner.AuthorizationError, "trust evidence"):
                runner.verify_fixture_synthetic_authorization(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    approval_path=approval_path,
                    expected_approval_sha256=approval_sha256,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertFalse(quarantine_root.exists())

    def test_fixture_validation_rejects_approval_bound_to_another_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root,
                quarantine_root=quarantine_root,
            )
            approval_path, approval_sha256 = self._write_approval(
                root,
                candidate_path=candidate_path,
                candidate_sha256=candidate_sha256,
                candidate_sha_override="0" * 64,
            )

            with self.assertRaisesRegex(runner.AuthorizationError, "candidate SHA"):
                runner.verify_fixture_synthetic_authorization(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    approval_path=approval_path,
                    expected_approval_sha256=approval_sha256,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertFalse(quarantine_root.exists())

    def test_fixture_validation_rejects_unbound_runner_and_source_only_artifact(self) -> None:
        cases = (
            {"bind_synthetic_runner": False, "source_only_artifact_id": None, "message": "runner"},
            {
                "bind_synthetic_runner": True,
                "source_only_artifact_id": "failure_metric_schema",
                "message": "candidate-ready",
            },
        )
        for case in cases:
            with self.subTest(case=case["message"]), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                quarantine_root = root / "fresh-quarantine-root"
                candidate_path, candidate_sha256 = self._write_candidate(
                    root,
                    quarantine_root=quarantine_root,
                    bind_synthetic_runner=case["bind_synthetic_runner"],
                    source_only_artifact_id=case["source_only_artifact_id"],
                )
                approval_path, approval_sha256 = self._write_approval(
                    root,
                    candidate_path=candidate_path,
                    candidate_sha256=candidate_sha256,
                )

                with self.assertRaisesRegex(runner.AuthorizationError, case["message"]):
                    runner.verify_fixture_synthetic_authorization(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        approval_path=approval_path,
                        expected_approval_sha256=approval_sha256,
                        expected_quarantine_root=quarantine_root,
                    )

                self.assertFalse(quarantine_root.exists())

    def test_production_entry_refuses_before_candidate_or_root_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"

            with self.assertRaisesRegex(runner.AuthorizationError, "production trust authority"):
                runner.prepare_production_synthetic_execution(
                    candidate_path=root / "missing-candidate.json",
                    expected_candidate_sha256="0" * 64,
                    approval_path=root / "missing-approval.json",
                    expected_approval_sha256="0" * 64,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertFalse(quarantine_root.exists())

    def test_production_entry_refuses_even_valid_fixture_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root,
                quarantine_root=quarantine_root,
            )
            approval_path, approval_sha256 = self._write_approval(
                root,
                candidate_path=candidate_path,
                candidate_sha256=candidate_sha256,
            )

            with self.assertRaisesRegex(runner.AuthorizationError, "candidate-bound E3-1 executor"):
                runner.prepare_production_synthetic_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    approval_path=approval_path,
                    expected_approval_sha256=approval_sha256,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertFalse(quarantine_root.exists())

    def test_direct_runner_call_is_hard_refused_without_root_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"

            with self.assertRaisesRegex(runner.AuthorizationError, "unavailable"):
                runner.run_synthetic_once("forged-capability", quarantine_output_root=quarantine_root)

            self.assertFalse(quarantine_root.exists())

    def test_runner_exposes_no_cli_or_callback_injection_api(self) -> None:
        self.assertFalse(hasattr(runner, "main"))
        self.assertFalse(hasattr(runner, "build_argument_parser"))
        self.assertFalse(hasattr(runner, "SyntheticOnlyEntrypoints"))
        self.assertFalse(hasattr(runner, "issue_synthetic_execution_capability"))


if __name__ == "__main__":
    unittest.main()
