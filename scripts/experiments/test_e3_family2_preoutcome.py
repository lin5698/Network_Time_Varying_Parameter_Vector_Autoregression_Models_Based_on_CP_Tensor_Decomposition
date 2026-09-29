"""Public safety tests for the source-only E3 Family-2 boundary."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.experiments import e3_family2_preoutcome as e3


class E3Family2PreoutcomeTests(unittest.TestCase):
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

    def _write_candidate(
        self,
        root: Path,
        *,
        quarantine_root: Path,
    ) -> tuple[Path, str]:
        artifact_root = root / "candidate-ready-artifacts"
        domain_stability = e3.artifact_schemas.source_only_content(
            "family2_query_contract"
        )["domain_stability"]
        preoutcome_artifacts: dict[str, dict[str, str]] = {}
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
            path = artifact_root / e3.artifact_schemas.ARTIFACT_FILENAMES[artifact_id]
            e3.artifact_schemas.write_preoutcome_artifact(
                path,
                artifact_id=artifact_id,
                lifecycle=e3.artifact_schemas.CANDIDATE_READY,
                content=content,
            )
            preoutcome_artifacts[artifact_id] = {
                "path": str(path),
                "sha256": self._sha256(path),
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
        runner = Path(e3.__file__).resolve()
        schema_module = Path(e3.artifact_schemas.__file__).resolve()
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
                "runner_sha256": self._sha256(runner),
                "source_hashes": {
                    str(runner): self._sha256(runner),
                    str(schema_module): self._sha256(schema_module),
                },
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
                "configuration_sha256": hashlib.sha256(
                    json.dumps(configuration, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
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

    def test_bootstrap_history_gate_refuses_legacy_start_and_insufficient_rank_opportunities(self) -> None:
        legacy_contract = {
            "method": "fixed_rank_basis",
            "local_window": 12,
            "minimum_local_estimates": 2,
            "allowed_ranks": [1, 2, 3],
            "minimum_valid_refit_opportunities_per_allowed_rank": 2,
            "evaluation_target_times": [143],
            "rank_aware_start_times": {"1": 13, "2": 13, "3": 13},
        }
        with self.assertRaisesRegex(e3.ContractError, "rank-aware start"):
            e3.validate_fixed_rank_bootstrap_history_gate(legacy_contract)

        insufficient_contract = {
            "method": "fixed_rank_basis",
            "local_window": 12,
            "minimum_local_estimates": 2,
            "allowed_ranks": [1, 2, 3],
            "minimum_valid_refit_opportunities_per_allowed_rank": 2,
            "evaluation_target_times": [16],
            "rank_aware_start_times": {"1": 14, "2": 14, "3": 15},
        }
        with self.assertRaisesRegex(e3.ContractError, "two valid bootstrap refit opportunities"):
            e3.validate_fixed_rank_bootstrap_history_gate(insufficient_contract)

    def test_source_only_artifact_package_has_all_versioned_ids_and_is_not_candidate_ready(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_root = Path(temporary_directory) / "artifacts"
            written = e3.write_source_only_preoutcome_artifacts(artifact_root)

            self.assertEqual(set(written), set(e3.REQUIRED_PREOUTCOME_ARTIFACT_IDS))
            for artifact_id, path in written.items():
                with self.subTest(artifact_id=artifact_id):
                    verified = e3.verify_preoutcome_artifact(path, artifact_id=artifact_id)
                    self.assertEqual(verified["artifact_id"], artifact_id)
                    self.assertEqual(verified["lifecycle"], "SOURCE_ONLY")
                    self.assertEqual(verified["scientific_execution"], "NOT_AUTHORIZED")
                    with self.assertRaisesRegex(e3.ContractError, "candidate-ready"):
                        e3.verify_preoutcome_artifact(
                            path,
                            artifact_id=artifact_id,
                            require_candidate_ready=True,
                        )

    def test_proof_review_receipt_rejects_malformed_or_mismatched_content(self) -> None:
        mutations = {
            "missing-review-mode": lambda payload: payload.pop("review_mode"),
            "mismatched-proof-hash": lambda payload: payload.__setitem__(
                "proof_packet_sha256", "0" * 64
            ),
            "unresolved-finding": lambda payload: payload.__setitem__(
                "open_findings", ["F2-01"]
            ),
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    content = e3.artifact_schemas.source_only_content(
                        "family2_factorization_proof_packet"
                    )
                    receipt_payload = self._proof_review_payload(
                        content["proof_packet"]["sha256"]
                    )
                    mutate(receipt_payload)
                    receipt = root / f"{label}.json"
                    receipt.write_text(
                        json.dumps(receipt_payload, sort_keys=True), encoding="utf-8"
                    )
                    content["independent_blind_review"] = {
                        "status": "PASS",
                        "receipt": {
                            "path": str(receipt),
                            "sha256": self._sha256(receipt),
                        },
                    }
                    artifact_path = root / f"{label}-proof-packet.json"
                    with self.assertRaisesRegex(
                        e3.artifact_schemas.ArtifactValidationError,
                        "proof review receipt",
                    ):
                        e3.artifact_schemas.write_preoutcome_artifact(
                            artifact_path,
                            artifact_id="family2_factorization_proof_packet",
                            lifecycle=e3.artifact_schemas.CANDIDATE_READY,
                            content=content,
                        )

    def test_missing_authorization_refuses_before_science_or_quarantine_root(self) -> None:
        calls: list[str] = []

        def forbidden(name: str):
            def callback(*_args: object, **_kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"{name} must not be called")

            return callback

        entrypoints = e3.ScientificEntrypoints(
            topology_generator=forbidden("topology_generator"),
            estimator=forbidden("estimator"),
            response_evaluator=forbidden("response_evaluator"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            quarantine_root = Path(temporary_directory) / "new-quarantine-root"
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=None,
                    expected_candidate_sha256=None,
                    trust_verifier=None,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_fixture_trust_verifier_is_rejected_by_production_before_science(self) -> None:
        calls: list[str] = []

        def forbidden(name: str):
            def callback(*_args: object, **_kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"{name} must not be called")

            return callback

        entrypoints = e3.ScientificEntrypoints(
            topology_generator=forbidden("topology_generator"),
            estimator=forbidden("estimator"),
            response_evaluator=forbidden("response_evaluator"),
        )
        fixture_verifier = e3.TestOnlyFixtureTrustVerifier(
            verify_fixture=lambda _evidence, _payload: True
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "new-quarantine-root"
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=root / "candidate.json",
                    expected_candidate_sha256="0" * 64,
                    trust_verifier=fixture_verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_legacy_verifier_methods_hard_refuse_without_invoking_callbacks(self) -> None:
        calls: list[str] = []

        def fixture_callback(*_args: object, **_kwargs: object) -> bool:
            calls.append("fixture")
            raise AssertionError("fixture callback must not be called")

        def detached_callback(*_args: object, **_kwargs: object) -> bool:
            calls.append("detached")
            raise AssertionError("detached callback must not be called")

        fixture_verifier = e3.TestOnlyFixtureTrustVerifier(fixture_callback)
        configured_verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=detached_callback,
        )

        with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
            fixture_verifier.verify({}, b"fixture-payload")
        with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
            configured_verifier.verify(
                {
                    "pinned_key_id": "fixture-production-key",
                    "trust_policy_id": "fixture-production-policy",
                },
                b"configured-payload",
            )

        self.assertEqual(calls, [])

    def test_construction_writes_only_a_static_preoutcome_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = Path(temporary_directory) / e3.ARTIFACT_NAME
            artifact = e3.write_preoutcome_contract(artifact_path)

            self.assertEqual(artifact["run_type"], "construction_only")
            self.assertEqual(artifact["scientific_execution"], "NOT_AUTHORIZED")
            self.assertEqual(artifact["fixtures"]["f1_negative"]["status"], "OUTSIDE_TARGET")
            self.assertEqual(artifact["fixtures"]["f2_unrestricted_negative"]["status"], "OUTSIDE_TARGET")
            self.assertEqual(artifact["fixtures"]["f2_diagonal_negative"]["status"], "OUTSIDE_TARGET")
            self.assertEqual(artifact["fixtures"]["f2_diagonal_positive"]["status"], "AVAILABLE")
            self.assertEqual(artifact["fixtures"]["non_equivalence"]["status"], "DISTINCT_FAMILY")
            self.assertEqual(
                sorted(path.name for path in Path(temporary_directory).iterdir()),
                [e3.ARTIFACT_NAME],
            )
            serialized = json.dumps(artifact, sort_keys=True)
            for forbidden_field in (
                "operator_error",
                "response_error",
                "recovery_metric",
                "simulation_result",
            ):
                self.assertNotIn(forbidden_field, serialized)
            self.assertEqual(
                e3.verify_preoutcome_contract(artifact_path)["artifact_sha256"],
                artifact["artifact_sha256"],
            )

    def test_ineligible_comparators_are_rejected_before_fitting(self) -> None:
        fit_calls: list[str] = []

        def forbidden_fit(*_args: object, **_kwargs: object) -> object:
            fit_calls.append("fit")
            raise AssertionError("an ineligible comparator must never be fitted")

        cases = (
            {
                "comparator_id": "collapsed",
                "representation": "collapsed_only",
                "retained_blocks": ["D"],
                "endpoint_output": "collapsed_operator",
                "projected_output": False,
                "posthoc_mapping": False,
                "fit": forbidden_fit,
            },
            {
                "comparator_id": "projected",
                "representation": "coefficient_blocks",
                "retained_blocks": ["C0", "C1", "C2"],
                "endpoint_output": "full_operator_and_finite_horizon_response",
                "projected_output": True,
                "posthoc_mapping": False,
                "fit": forbidden_fit,
            },
            {
                "comparator_id": "posthoc",
                "representation": "coefficient_blocks",
                "retained_blocks": ["C0", "C1", "C2"],
                "endpoint_output": "full_operator_and_finite_horizon_response",
                "projected_output": False,
                "posthoc_mapping": True,
                "fit": forbidden_fit,
            },
        )
        for comparator in cases:
            with self.subTest(comparator=comparator["comparator_id"]):
                with self.assertRaises(e3.ComparatorEligibilityError):
                    e3.validate_comparator_before_fitting(comparator)

        endpoint = e3.classify_endpoint_availability(cases[0])
        self.assertEqual(endpoint.status, "OUTSIDE_TARGET")
        self.assertIsNone(endpoint.numerical_score)
        self.assertEqual(fit_calls, [])

    def test_production_preflight_hard_refuses_valid_fixture_before_science(self) -> None:
        calls: list[str] = []

        def forbidden(name: str):
            def callback(*_args: object, **_kwargs: object) -> object:
                calls.append(name)
                raise AssertionError(f"{name} must not be called")

            return callback

        entrypoints = e3.ScientificEntrypoints(
            topology_generator=forbidden("topology_generator"),
            estimator=forbidden("estimator"),
            response_evaluator=forbidden("response_evaluator"),
        )
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=lambda evidence, _payload: evidence["detached_signature"]
            == "fixture-detached-signature",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_each_semantically_empty_artifact_with_matching_hash_is_refused_before_science(
        self,
    ) -> None:
        for artifact_id in e3.REQUIRED_PREOUTCOME_ARTIFACT_IDS:
            with self.subTest(artifact_id=artifact_id):
                calls: list[str] = []

                def forbidden(*_args: object, **_kwargs: object) -> object:
                    calls.append("scientific")
                    raise AssertionError("science must not run")

                entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
                verifier = e3.ConfiguredTrustVerifier(
                    pinned_key_id="fixture-production-key",
                    trust_policy_id="fixture-production-policy",
                    verify_detached=lambda _evidence, _payload: True,
                )
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory) / artifact_id
                    root.mkdir()
                    quarantine_root = root / "fresh-quarantine-root"
                    candidate_path, _candidate_sha256 = self._write_candidate(
                        root, quarantine_root=quarantine_root
                    )
                    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
                    placeholder = root / f"{artifact_id}-placeholder.json"
                    placeholder.write_text(
                        json.dumps({"artifact_id": artifact_id}, sort_keys=True),
                        encoding="utf-8",
                    )
                    candidate["bindings"]["preoutcome_artifacts"][artifact_id] = {
                        "path": str(placeholder),
                        "sha256": self._sha256(placeholder),
                    }
                    candidate_path.write_text(
                        json.dumps(candidate, sort_keys=True), encoding="utf-8"
                    )
                    candidate_sha256 = self._sha256(candidate_path)

                    with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                        e3.prepare_production_execution(
                            candidate_path=candidate_path,
                            expected_candidate_sha256=candidate_sha256,
                            trust_verifier=verifier,
                            scientific_entrypoints=entrypoints,
                            expected_quarantine_root=quarantine_root,
                        )

                    self.assertEqual(calls, [])
                    self.assertFalse(quarantine_root.exists())

    def test_missing_production_trust_refuses_a_valid_candidate_before_science(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=None,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_candidate_sha_mismatch_refuses_before_science_or_quarantine_root(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=lambda _evidence, _payload: True,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, _candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256="0" * 64,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_existing_quarantine_root_refuses_before_science(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=lambda _evidence, _payload: True,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "existing-quarantine-root"
            quarantine_root.mkdir()
            candidate_path, candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertTrue(quarantine_root.is_dir())

    def test_candidate_without_dependency_hashes_is_refused_before_science(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=lambda _evidence, _payload: True,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, _candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["bindings"].pop("dependency_hashes", None)
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_excluded_route_in_a_candidate_binding_refuses_before_science(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=lambda _evidence, _payload: True,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, _candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            excluded_input = root / "RCEP-synthetic-specification.json"
            excluded_input.write_text("static fixture only\n", encoding="utf-8")
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["bindings"]["inputs"][0]["path"] = str(excluded_input)
            candidate["bindings"]["inputs"][0]["sha256"] = self._sha256(excluded_input)
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_rejected_trust_stops_before_bound_input_access(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=lambda _evidence, _payload: False,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, _candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["bindings"]["inputs"][0]["path"] = str(root / "missing-synthetic-specification.json")
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_failed_trust_verifier_becomes_a_controlled_authorization_refusal(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("scientific")
            raise AssertionError("science must not run")

        verifier_calls: list[str] = []

        def failed_verifier(_evidence: object, _payload: object) -> bool:
            verifier_calls.append("verify")
            raise RuntimeError("fixture verifier failure")

        entrypoints = e3.ScientificEntrypoints(forbidden, forbidden, forbidden)
        verifier = e3.ConfiguredTrustVerifier(
            pinned_key_id="fixture-production-key",
            trust_policy_id="fixture-production-policy",
            verify_detached=failed_verifier,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            quarantine_root = root / "fresh-quarantine-root"
            candidate_path, candidate_sha256 = self._write_candidate(
                root, quarantine_root=quarantine_root
            )
            with self.assertRaisesRegex(e3.AuthorizationError, "source-only build"):
                e3.prepare_production_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    trust_verifier=verifier,
                    scientific_entrypoints=entrypoints,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertEqual(calls, [])
            self.assertEqual(verifier_calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_cli_exposes_static_construction_and_verification_without_scientific_run(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = Path(temporary_directory) / e3.ARTIFACT_NAME
            with redirect_stdout(io.StringIO()) as construction_stdout:
                self.assertEqual(
                    e3.main(["construction", "--output", str(artifact_path)]),
                    0,
                )
            self.assertTrue(artifact_path.is_file())
            construction = json.loads(construction_stdout.getvalue())
            self.assertEqual(construction["scientific_execution"], "NOT_AUTHORIZED")
            self.assertEqual(
                e3.verify_preoutcome_contract(artifact_path)["scientific_execution"],
                "NOT_AUTHORIZED",
            )
            with redirect_stdout(io.StringIO()) as verification_stdout:
                self.assertEqual(e3.main(["verify", "--input", str(artifact_path)]), 0)
            verification = json.loads(verification_stdout.getvalue())
            self.assertEqual(verification["run_type"], "verification_only")
            self.assertEqual(verification["status"], "SOURCE_ONLY_VERIFIED")
            self.assertEqual(verification["scientific_execution"], "NOT_AUTHORIZED")
            self.assertEqual(verification["production_execution"], "UNAVAILABLE")
            self.assertEqual(
                [item["artifact_id"] for item in verification["preoutcome_artifacts"]],
                list(e3.REQUIRED_PREOUTCOME_ARTIFACT_IDS),
            )
            self.assertTrue(
                all(
                    item["lifecycle"] == "SOURCE_ONLY"
                    and item["scientific_execution"] == "NOT_AUTHORIZED"
                    for item in verification["preoutcome_artifacts"]
                )
            )
            self.assertEqual(
                sorted(path.name for path in Path(temporary_directory).iterdir()),
                [e3.ARTIFACT_NAME],
            )
            artifact_path.write_text(
                artifact_path.read_text(encoding="utf-8").replace(
                    '"status":"CONSTRUCTION_PASS"', '"status":"MUTATED"', 1
                ),
                encoding="utf-8",
            )
            with redirect_stderr(io.StringIO()) as refused_stderr:
                self.assertEqual(e3.main(["verify", "--input", str(artifact_path)]), 2)
            self.assertIn("verify refused", refused_stderr.getvalue())
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as rejected:
                e3.build_argument_parser().parse_args(["run"])
        self.assertEqual(rejected.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
