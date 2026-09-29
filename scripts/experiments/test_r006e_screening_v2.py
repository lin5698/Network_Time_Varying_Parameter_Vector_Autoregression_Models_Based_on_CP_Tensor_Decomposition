"""Governance-only tests for the R006e screening-v2 pair supervisor."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.experiments import r006e_construction_v2 as construction
from scripts.experiments import r006e_screening_v2 as screening
from scripts.experiments.r006e_attempt_ledger_v2 import (
    PAIR_CLAIM_FILENAME,
    PRIMARY_CONSTRUCTION_NAMES,
    ScreeningV2Paths,
    ConfiguredTrustVerifier,
    TestOnlyFixtureTrustVerifier,
    canonical_json_sha256,
    derive_attempt_state,
)
from scripts.experiments.r006e_native_protocol import R006EConfig
from scripts.experiments.r006e_screening_executor_v2 import (
    CellExecution,
    retain_worker_failure,
)
from scripts.experiments import r006e_screening_executor_v2 as executor
from scripts.experiments.r006e_screening_schema_v2 import (
    DOCUMENT_TYPES,
    EXPECTED_ROWS,
    METHODS,
    SCHEMA_VERSION,
    SCREENING_OUTPUT_NAMES,
    SCREENING_SEEDS,
    SUMMARY_IDENTITIES,
    V2_CONTROL_ROOT,
    V2_PRIMARY_ROOT,
    V2_REPEAT_ROOT,
    derive_attempt_id,
)


def retained_failure_runner(task, certificate, attempt_id, role, generated_at):
    return retain_worker_failure(
        task,
        construction_certificate=certificate,
        attempt_id=attempt_id,
        role=role,
        generated_at=generated_at,
        worker_pid=os.getpid(),
        peak_memory_bytes=4096,
    )


def crashing_worker_runner(task, certificate, attempt_id, role, generated_at):
    if role == "primary" and task == screening.screening_cell_tasks()[0]:
        os._exit(73)
    return retained_failure_runner(task, certificate, attempt_id, role, generated_at)


def mismatching_runner(task, certificate, attempt_id, role, generated_at):
    if role == "repeat" and task == screening.screening_cell_tasks()[0]:
        return executor._retain_failed_cell(
            task,
            ValueError("fixture mismatch"),
            construction_certificate=certificate,
            attempt_id=attempt_id,
            role=role,
            generated_at=generated_at,
            worker_pid=os.getpid(),
            peak_memory_bytes=4096,
        )
    return retained_failure_runner(task, certificate, attempt_id, role, generated_at)


def malformed_worker_runner(task, certificate, attempt_id, role, generated_at):
    del task, certificate, attempt_id, role, generated_at
    return CellExecution((), (), (), ())


def synthetic_passing_runner(task, certificate, attempt_id, role, generated_at):
    base = retained_failure_runner(
        task, certificate, attempt_id, role, generated_at
    )
    replications: list[dict[str, object]] = []
    journals: list[dict[str, object]] = []
    for replication, journal in zip(base.replications, base.row_journals):
        row = dict(replication)
        row.update(
            {
                "fit_success": 1,
                "scorable": 1,
                "at_least_one_converged_start": 1,
                "selected_objective_trace_nonincreasing": 1,
                "w_alt_interp_available": 1,
                "w_alt_family_available": 1,
                "failure_code": None,
                "failure_reason": None,
                "observed_topology_prediction_rmse": 0.8,
                "w_ref_raw_response_error_mean": 0.8,
            }
        )
        for endpoint in ("w_alt_interp", "w_alt_family"):
            row[f"{endpoint}_operator_relative_error_mean"] = 0.5
            row[f"{endpoint}_response_zero_ratio_mean"] = 0.5
            row[f"{endpoint}_raw_response_error_mean"] = (
                0.8 if row["method"] == "dw_joint_tucker333" else 1.0
            )
        bound = dict(journal)
        bound["replication_sha256"] = executor._canonical_sha256(row)
        replications.append(row)
        journals.append(bound)
    return executor._validated_cell_execution(
        CellExecution(
            tuple(replications),
            base.diagnostics,
            base.resources,
            tuple(journals),
        )
    )


class ScreeningV2CliTests(unittest.TestCase):
    def _screening_args(self) -> list[str]:
        return [
            "screening-pair",
            "--workers", "6",
            "--authorization", "/tmp/authorization.json",
            "--primary-root", V2_PRIMARY_ROOT,
            "--repeat-root", V2_REPEAT_ROOT,
            "--control-root", V2_CONTROL_ROOT,
        ]

    def _construction_args(self) -> list[str]:
        return [
            "construction-v2",
            "--primary-root", V2_PRIMARY_ROOT,
            "--repeat-root", V2_REPEAT_ROOT,
            "--control-root", V2_CONTROL_ROOT,
        ]

    def _assert_loader_refuses_before_claim(self, loader) -> None:
        verifier = ConfiguredTrustVerifier(
            pinned_key_id="fixture-key",
            trust_policy_id="fixture-policy",
            verify_detached=lambda evidence, payload: True,
        )
        loader_calls: list[object] = []
        authorization_payload = {"decision_id": "fixture-decision"}

        def observed_loader(payload):
            loader_calls.append(payload)
            return loader(payload)

        def trusted_prepare(**kwargs):
            callback = kwargs.get("post_trust_preclaim")
            if callback is None:
                self.fail("screening preparation omitted post-trust certificate loading")
            callback(authorization_payload, kwargs["paths"])
            return mock.sentinel.claim

        with tempfile.TemporaryDirectory() as temporary:
            paths = ScreeningV2Paths.under(Path(temporary))
            with (
                mock.patch.object(
                    screening, "_validated_production_paths", return_value=paths
                ),
                mock.patch.object(screening, "_PRODUCTION_TRUST_VERIFIER", verifier),
                mock.patch.object(
                    screening,
                    "_PRODUCTION_FROZEN_V1_VERIFIER",
                    lambda: "f" * 64,
                ),
                mock.patch.object(
                    screening,
                    "_PRODUCTION_PREFLIGHT",
                    lambda payload, active_paths: None,
                ),
                mock.patch.object(
                    screening, "_PRODUCTION_CERTIFICATE_LOADER", observed_loader
                ),
                mock.patch.object(
                    screening,
                    "prepare_screening_pair",
                    side_effect=trusted_prepare,
                ),
                mock.patch.object(screening, "_prepare_production_claim") as prepare,
                mock.patch.object(
                    screening.multiprocessing, "get_context"
                ) as context,
                mock.patch.object(screening, "run_screening_cell") as science,
                mock.patch.object(screening, "publish_role_artifacts") as publish,
                mock.patch.object(
                    screening, "_run_production_screening_pair"
                ) as run_pair,
            ):
                self.assertEqual(
                    screening.main(
                        [
                            "screening-pair",
                            "--workers",
                            "6",
                            "--authorization",
                            "/fixture-authorization.json",
                        ]
                    ),
                    2,
                )

            self.assertEqual(len(loader_calls), 1)
            prepare.assert_not_called()
            context.assert_not_called()
            science.assert_not_called()
            publish.assert_not_called()
            run_pair.assert_not_called()
            self.assertFalse((paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_cli_freezes_exact_phases_and_workers(self) -> None:
        parser = screening.build_parser()
        choices = parser._subparsers._group_actions[0].choices
        self.assertEqual(
            tuple(choices),
            ("construction-v2", "verify-authorization", "screening-pair"),
        )
        with self.assertRaises(SystemExit):
            parser.parse_args(["screening-pair", "--workers", "5"])
        parsed = parser.parse_args(self._screening_args())
        self.assertEqual(parsed.workers, 6)
        self.assertEqual(parsed.primary_root, V2_PRIMARY_ROOT)
        self.assertFalse(any("fixture" in action.dest for action in parser._actions))

    def test_construction_root_mismatch_refuses_before_builder(self) -> None:
        arguments = self._construction_args()
        arguments[arguments.index(V2_PRIMARY_ROOT)] = "/tmp/wrong-root"
        with mock.patch.object(screening, "_run_construction_v2") as build:
            self.assertEqual(screening.main(arguments), 2)
        build.assert_not_called()

    def test_construction_v2_writes_only_two_files_in_fixture_roots(self) -> None:
        certificates = json.loads(
            (
                Path("output/high_impact_revision/r006e_native_supported_recovery")
                / construction.CONSTRUCTION_ARTIFACT_NAME
            ).read_text(encoding="utf-8")
        )["screening_support_certificates"]
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            paths = construction.ConstructionV2Paths(
                parent / construction.V2_PRIMARY_ROOT_NAME,
                parent / construction.V2_REPEAT_ROOT_NAME,
                parent / construction.V2_CONTROL_ROOT_NAME,
                future_checklist=parent / "future-checklist.md",
            )
            with (
                mock.patch.object(
                    screening, "_validated_production_paths", return_value=paths
                ),
                mock.patch.object(
                    construction, "_build_certificates", return_value=certificates
                ),
                mock.patch.object(screening, "_prepare_production_claim") as prepare,
                mock.patch.object(screening, "_load_production_certificates") as load,
                mock.patch.object(screening, "_run_production_screening_pair") as run,
                mock.patch.object(screening, "run_screening_cell") as science,
                mock.patch.object(screening, "publish_role_artifacts") as publish,
            ):
                self.assertEqual(screening.main(["construction-v2"]), 0)

            self.assertEqual(
                sorted(path.name for path in paths.primary.iterdir()),
                [
                    construction.CONSTRUCTION_ARTIFACT_NAME,
                    construction.CONSTRUCTION_MANIFEST_NAME,
                ],
            )
            self.assertFalse(paths.repeat.exists())
            self.assertFalse(paths.control.exists())
            prepare.assert_not_called()
            load.assert_not_called()
            run.assert_not_called()
            science.assert_not_called()
            publish.assert_not_called()

    def test_root_mismatch_refuses_before_task3_or_process_boundary(self) -> None:
        arguments = self._screening_args()
        arguments[arguments.index(V2_PRIMARY_ROOT)] = "/tmp/wrong-root"
        with (
            mock.patch.object(screening, "prepare_screening_pair") as claim,
            mock.patch.object(screening.multiprocessing, "get_context") as context,
            mock.patch.object(screening, "run_screening_cell") as science,
            mock.patch.object(screening, "publish_role_artifacts") as publish,
        ):
            self.assertEqual(screening.main(arguments), 2)
        claim.assert_not_called()
        context.assert_not_called()
        science.assert_not_called()
        publish.assert_not_called()

    def test_verify_dispatches_task3_only_and_closes_claim(self) -> None:
        events: list[str] = []
        claim = mock.Mock()
        claim.root_snapshot.close.side_effect = lambda: events.append("close")
        verify_args = [
            "verify-authorization",
            "--authorization", "/tmp/authorization.json",
            "--primary-root", V2_PRIMARY_ROOT,
            "--repeat-root", V2_REPEAT_ROOT,
            "--control-root", V2_CONTROL_ROOT,
        ]
        with (
            mock.patch.object(
                screening,
                "_prepare_production_claim",
                side_effect=lambda **kwargs: events.append("prepare") or claim,
            ) as prepare,
            mock.patch.object(screening, "_load_production_certificates") as load,
            mock.patch.object(screening, "_run_production_screening_pair") as run,
        ):
            self.assertEqual(screening.main(verify_args), 0)
        prepare.assert_called_once()
        load.assert_not_called()
        run.assert_not_called()
        self.assertEqual(events, ["prepare", "close"])

    def test_screening_dispatch_order_is_authorize_load_claim_then_pair(self) -> None:
        events: list[str] = []
        claim = mock.Mock()
        authorization_payload = {"decision_id": "fixture-decision"}
        certificates = {
            task.identity: {} for task in screening.screening_cell_tasks()
        }

        def trusted_prepare(**kwargs):
            events.append("authorize")
            kwargs["post_trust_preclaim"](
                authorization_payload,
                kwargs["paths"],
            )
            events.append("claim")
            return claim

        def load(payload):
            events.append("load")
            self.assertIsNot(payload, authorization_payload)
            return certificates

        verifier = ConfiguredTrustVerifier(
            pinned_key_id="fixture-key",
            trust_policy_id="fixture-policy",
            verify_detached=lambda evidence, payload: True,
        )
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch.object(
                screening,
                "_validated_production_paths",
                return_value=ScreeningV2Paths.under(Path(temporary)),
            ),
            mock.patch.object(screening, "_PRODUCTION_TRUST_VERIFIER", verifier),
            mock.patch.object(
                screening,
                "_PRODUCTION_FROZEN_V1_VERIFIER",
                lambda: "f" * 64,
            ),
            mock.patch.object(
                screening,
                "_PRODUCTION_PREFLIGHT",
                lambda payload, active_paths: None,
            ),
            mock.patch.object(
                screening,
                "_PRODUCTION_CERTIFICATE_LOADER",
                load,
            ),
            mock.patch.object(
                screening,
                "prepare_screening_pair",
                side_effect=trusted_prepare,
            ),
            mock.patch.object(screening, "_prepare_production_claim") as verify_only,
            mock.patch.object(
                screening,
                "_run_production_screening_pair",
                side_effect=lambda **kwargs: events.append("run") or mock.Mock(
                    integrity_status="PASS"
                ),
            ),
        ):
            self.assertEqual(screening.main(self._screening_args()), 0)
        verify_only.assert_not_called()
        self.assertEqual(events, ["authorize", "load", "claim", "run"])

    def test_absent_private_bindings_refuse_before_all_downstream_boundaries(self) -> None:
        with (
            mock.patch.object(screening, "prepare_screening_pair") as claim,
            mock.patch.object(screening.multiprocessing, "get_context") as context,
            mock.patch.object(screening, "run_screening_cell") as science,
            mock.patch.object(screening, "publish_role_artifacts") as publish,
        ):
            self.assertEqual(screening.main(self._screening_args()), 2)
        claim.assert_not_called()
        context.assert_not_called()
        science.assert_not_called()
        publish.assert_not_called()

    def test_absent_certificate_loader_refuses_before_claim_and_downstream_boundaries(
        self,
    ) -> None:
        verifier = ConfiguredTrustVerifier(
            pinned_key_id="fixture-key",
            trust_policy_id="fixture-policy",
            verify_detached=lambda evidence, payload: True,
        )
        with tempfile.TemporaryDirectory() as temporary:
            paths = ScreeningV2Paths.under(Path(temporary))
            with (
                mock.patch.object(
                    screening, "_validated_production_paths", return_value=paths
                ),
                mock.patch.object(screening, "_PRODUCTION_TRUST_VERIFIER", verifier),
                mock.patch.object(
                    screening,
                    "_PRODUCTION_FROZEN_V1_VERIFIER",
                    lambda: "f" * 64,
                ),
                mock.patch.object(
                    screening,
                    "_PRODUCTION_PREFLIGHT",
                    lambda payload, active_paths: None,
                ),
                mock.patch.object(screening, "_PRODUCTION_CERTIFICATE_LOADER", None),
                mock.patch.object(screening, "_prepare_production_claim") as prepare,
                mock.patch.object(
                    screening.multiprocessing, "get_context"
                ) as context,
                mock.patch.object(screening, "run_screening_cell") as science,
                mock.patch.object(screening, "publish_role_artifacts") as publish,
            ):
                self.assertEqual(
                    screening.main(
                        [
                            "screening-pair",
                            "--workers",
                            "6",
                            "--authorization",
                            "/missing-partial-binding.json",
                        ]
                    ),
                    2,
                )

            prepare.assert_not_called()
            context.assert_not_called()
            science.assert_not_called()
            publish.assert_not_called()
            self.assertFalse((paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_certificate_loader_exception_refuses_before_claim(self) -> None:
        def explode(payload):
            del payload
            raise RuntimeError("fixture loader failure")

        self._assert_loader_refuses_before_claim(explode)

    def test_certificate_loader_wrong_task_set_refuses_before_claim(self) -> None:
        self._assert_loader_refuses_before_claim(lambda payload: {})

    def test_certificate_loader_cannot_mutate_source_authorization_payload(
        self,
    ) -> None:
        payload = {"nested": {"decision": "original"}}
        certificates = {
            task.identity: {} for task in screening.screening_cell_tasks()
        }

        def mutate(received):
            received["nested"]["decision"] = "mutated"
            return certificates

        with mock.patch.object(screening, "_PRODUCTION_CERTIFICATE_LOADER", mutate):
            try:
                screening._load_production_certificates(payload)
            except (AttributeError, TypeError) as error:
                self.fail(f"loader lacks a defensive payload boundary: {error}")

        self.assertEqual(payload, {"nested": {"decision": "original"}})

    def test_loaded_certificates_are_owned_deep_copies(self) -> None:
        payload = {"decision_id": "fixture-decision"}
        certificates = {
            task.identity: {"nested": {"value": index}}
            for index, task in enumerate(screening.screening_cell_tasks())
        }
        first_identity = next(iter(certificates))

        with mock.patch.object(
            screening,
            "_PRODUCTION_CERTIFICATE_LOADER",
            lambda received: certificates,
        ):
            try:
                loaded = screening._load_production_certificates(payload)
            except (AttributeError, TypeError) as error:
                self.fail(f"certificate loader cannot accept a payload mapping: {error}")

        certificates[first_identity]["nested"]["value"] = -1
        self.assertNotEqual(loaded[first_identity]["nested"]["value"], -1)


class ScreeningV2PairTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.paths = ScreeningV2Paths.under(Path(self.temporary.name))
        for root in (self.paths.primary, self.paths.repeat, self.paths.control):
            root.mkdir()
        for name in PRIMARY_CONSTRUCTION_NAMES:
            (self.paths.primary / name).write_text("fixture", encoding="utf-8")
        self.v1_digest = "f" * 64

    def tearDown(self) -> None:
        children = multiprocessing.active_children()
        for child in children:
            child.join(1)
        self.assertEqual(multiprocessing.active_children(), [], "leaked child process")

    def _authorization(self, decision_id: str = "task6-fixture") -> Path:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "document_type": DOCUMENT_TYPES["authorization_payload"],
            "decision": "AUTHORIZE",
            "phase": "SCREENING",
            "decision_id": decision_id,
            "authorizer_id": "independent-authorizer",
            "issued_at": "2026-07-18T12:00:00+08:00",
            "checklist_sha256": "0" * 64,
            "protocol_sha256": "1" * 64,
            "plan_sha256": "2" * 64,
            "runner_contract_sha256": "3" * 64,
            "construction_file_sha256": "4" * 64,
            "construction_canonical_sha256": "5" * 64,
            "provenance_sha256": "6" * 64,
            "config_sha256": "7" * 64,
            "dependency_manifest_sha256": "8" * 64,
            "source_manifest_sha256": "9" * 64,
            "candidate_sha256": "a" * 64,
            "frozen_v1_authority_digest": self.v1_digest,
            "primary_root": V2_PRIMARY_ROOT,
            "repeat_root": V2_REPEAT_ROOT,
            "control_root": V2_CONTROL_ROOT,
            "primary_attempt_id": derive_attempt_id(decision_id, "primary"),
            "repeat_attempt_id": derive_attempt_id(decision_id, "repeat"),
            "workers": 6,
            "seeds": list(SCREENING_SEEDS),
            "cells": [list(cell) for cell in SUMMARY_IDENTITIES],
            "methods": list(METHODS),
            "output_names": list(SCREENING_OUTPUT_NAMES),
            "expected_rows": EXPECTED_ROWS,
        }
        payload_sha = canonical_json_sha256(payload)
        core = {
            "schema_version": SCHEMA_VERSION,
            "document_type": DOCUMENT_TYPES["authorization_envelope"],
            "payload": payload,
            "payload_sha256": payload_sha,
        }
        artifact_sha = canonical_json_sha256(core)
        signature = "fixture-detached-signature"
        trust = {
            "schema_version": SCHEMA_VERSION,
            "document_type": DOCUMENT_TYPES["trust_evidence"],
            "authorization_artifact_sha256": artifact_sha,
            "signed_payload_sha256": payload_sha,
            "signature_algorithm": "TEST-ONLY",
            "pinned_key_id": "fixture-key",
            "detached_signature": signature,
            "detached_signature_sha256": hashlib.sha256(signature.encode()).hexdigest(),
            "trust_policy_id": "fixture-policy",
            "external_witness_id": "fixture-witness",
        }
        envelope = {
            **core,
            "artifact_sha256": artifact_sha,
            "trust_evidence": trust,
            "trust_evidence_sha256": canonical_json_sha256(trust),
        }
        path = Path(self.temporary.name) / "authorization.json"
        path.write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return path

    def _verifier(self):
        return TestOnlyFixtureTrustVerifier(
            lambda evidence, payload: (
                evidence["detached_signature"] == "fixture-detached-signature"
                and canonical_json_sha256(json.loads(payload))
                == evidence["signed_payload_sha256"]
            )
        )

    def _prepare(self):
        return screening._prepare_fixture_supervisor(
            paths=self.paths,
            authorization=self._authorization(),
            trust_verifier=self._verifier(),
            frozen_v1_verifier=lambda: self.v1_digest,
            preflight=lambda payload, paths: None,
            config=R006EConfig(),
            construction_certificates={task.identity: {} for task in screening.screening_cell_tasks()},
        )

    def test_matching_pair_runs_exact_one_shot_tasks_and_repeat_after_fail(self) -> None:
        calls = multiprocessing.get_context("fork").Value("i", 0)

        def counted(task, certificate, attempt_id, role, generated_at):
            with calls.get_lock():
                calls.value += 1
            return retained_failure_runner(
                task, certificate, attempt_id, role, generated_at
            )

        result = screening._run_fixture_screening_pair(
            self._prepare(), cell_runner=counted, workers=6
        )
        self.assertEqual(result.integrity_status, "PASS")
        self.assertEqual(result.primary_status, "FAIL")
        self.assertEqual(result.repeat_status, "FAIL")
        self.assertEqual(calls.value, 160)
        self.assertTrue((self.paths.control / PAIR_CLAIM_FILENAME).exists())
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "FAIL")
        self.assertEqual(derive_attempt_state(self.paths, "repeat"), "FAIL")

    def test_matching_schema_valid_pass_pair_is_semantic_pass(self) -> None:
        result = screening._run_fixture_screening_pair(
            self._prepare(), cell_runner=synthetic_passing_runner, workers=6
        )
        self.assertEqual(result.primary_status, "PASS")
        self.assertEqual(result.repeat_status, "PASS")
        self.assertEqual(result.integrity_status, "PASS")
        self.assertEqual(result.comparison["status"], "PASS")

    def test_hard_worker_crash_is_retained_without_rerun(self) -> None:
        result = screening._run_fixture_screening_pair(
            self._prepare(), cell_runner=crashing_worker_runner, workers=6
        )
        self.assertEqual(result.primary_status, "FAIL")
        self.assertEqual(result.repeat_status, "FAIL")
        self.assertEqual(result.integrity_status, "PASS")

    def test_malformed_worker_result_is_retained_for_all_four_identities(self) -> None:
        result = screening._run_fixture_screening_pair(
            self._prepare(), cell_runner=malformed_worker_runner, workers=6
        )
        self.assertEqual(result.primary_status, "FAIL")
        self.assertEqual(result.repeat_status, "FAIL")
        self.assertEqual(result.integrity_status, "PASS")

    def test_complete_scientific_mismatch_fails_pair_integrity(self) -> None:
        result = screening._run_fixture_screening_pair(
            self._prepare(), cell_runner=mismatching_runner, workers=6
        )
        self.assertEqual(result.integrity_status, "FAIL")
        self.assertIsNotNone(result.comparison)
        self.assertTrue(result.comparison["mismatch_paths"])

    def test_source_drift_refuses_before_claim_or_cell_process(self) -> None:
        checks = 0
        calls = multiprocessing.get_context("fork").Value("i", 0)

        def drifting_verifier():
            nonlocal checks
            checks += 1
            return self.v1_digest if checks == 1 else "0" * 64

        with self.assertRaisesRegex(Exception, "drift"):
            screening._prepare_fixture_supervisor(
                paths=self.paths,
                authorization=self._authorization(),
                trust_verifier=self._verifier(),
                frozen_v1_verifier=drifting_verifier,
                preflight=lambda payload, paths: None,
                config=R006EConfig(),
                construction_certificates={
                    task.identity: {} for task in screening.screening_cell_tasks()
                },
            )
        self.assertEqual(calls.value, 0)
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_prior_claim_refuses_second_supervisor(self) -> None:
        self._prepare()
        with self.assertRaisesRegex(Exception, "unexpected|prior claim"):
            self._prepare()

    def test_live_supervisor_retains_role_child_death_and_runs_repeat(self) -> None:
        result = screening._run_fixture_screening_pair(
            self._prepare(),
            cell_runner=retained_failure_runner,
            workers=6,
            crash_roles=frozenset({"primary"}),
        )
        self.assertEqual(result.primary_status, "INCOMPLETE")
        self.assertEqual(result.repeat_status, "FAIL")
        self.assertEqual(result.integrity_status, "FAIL")
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "INCOMPLETE")
        self.assertEqual(derive_attempt_state(self.paths, "repeat"), "FAIL")

    def test_supervisor_loss_leaves_permanent_incomplete_without_repeat(self) -> None:
        context = multiprocessing.get_context("fork")

        def lose_supervisor():
            capability = screening._prepare_fixture_supervisor(
                paths=self.paths,
                authorization=self._authorization(),
                trust_verifier=self._verifier(),
                frozen_v1_verifier=lambda: self.v1_digest,
                preflight=lambda payload, paths: None,
                config=R006EConfig(),
                construction_certificates={
                    task.identity: {} for task in screening.screening_cell_tasks()
                },
            )
            screening._fixture_supervisor_loss(capability)

        process = context.Process(target=lose_supervisor)
        process.start()
        process.join(5)
        self.assertFalse(process.is_alive())
        self.assertNotEqual(process.exitcode, 0)
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "INCOMPLETE")
        self.assertEqual(derive_attempt_state(self.paths, "repeat"), "CLAIMED")
        with self.assertRaisesRegex(Exception, "prior claim|unexpected"):
            self._prepare()

    def test_invalid_detached_trust_reaches_task3_governed_refusal(self) -> None:
        authorization = self._authorization()
        envelope = json.loads(authorization.read_text(encoding="utf-8"))
        envelope["trust_evidence"]["detached_signature"] = "invalid-signature"
        envelope["trust_evidence_sha256"] = canonical_json_sha256(
            envelope["trust_evidence"]
        )
        authorization.write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        production_paths = ScreeningV2Paths(
            *(Path.cwd() / root for root in (V2_PRIMARY_ROOT, V2_REPEAT_ROOT, V2_CONTROL_ROOT))
        )
        verifier = ConfiguredTrustVerifier(
            pinned_key_id="fixture-key",
            trust_policy_id="fixture-policy",
            verify_detached=lambda evidence, payload: True,
        )
        with (
            mock.patch.object(screening, "_PRODUCTION_TRUST_VERIFIER", verifier),
            mock.patch.object(
                screening, "_PRODUCTION_FROZEN_V1_VERIFIER", lambda: self.v1_digest
            ),
            mock.patch.object(
                screening, "_PRODUCTION_PREFLIGHT", lambda payload, paths: None
            ),
        ):
            with self.assertRaisesRegex(Exception, "detached signature digest"):
                screening._prepare_production_claim(
                    paths=production_paths,
                    authorization=authorization,
                )

    def test_missing_production_authorization_is_governed_and_writes_nothing(self) -> None:
        before = tuple(
            tuple(sorted(path.name for path in root.iterdir()))
            for root in (self.paths.repeat, self.paths.control)
        )
        self.assertEqual(
            screening.main(
                ["screening-pair", "--workers", "6", "--authorization", "/missing"]
            ),
            2,
        )
        after = tuple(
            tuple(sorted(path.name for path in root.iterdir()))
            for root in (self.paths.repeat, self.paths.control)
        )
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
