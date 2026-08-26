"""Tests for fail-closed R006e screening-v2 attempt governance."""

from __future__ import annotations

import tempfile
import hashlib
import json
import os
import threading
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest import mock

from scripts.experiments.r006e_attempt_ledger_v2 import (
    AuthorizationError,
    ClaimError,
    ConfiguredTrustVerifier,
    PAIR_CLAIM_FILENAME,
    PreparedPairCapability,
    PRIMARY_CONSTRUCTION_NAMES,
    ScreeningV2Paths,
    TestOnlyFixtureTrustVerifier,
    canonical_json_sha256,
    claim_screening_pair,
    derive_attempt_state,
    prepare_screening_pair_for_test,
    prepare_screening_pair,
    publish_incomplete_terminal,
    publish_terminal,
    scan_v2_roots_for_test,
    start_screening_role,
)
import scripts.experiments.r006e_attempt_ledger_v2 as ledger
from scripts.experiments.r006e_screening_outputs_v2 import ROLE_FILE_NAMES
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


class ScientificSpy:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


class AttemptLedgerV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.paths = ScreeningV2Paths.under(Path(self.temporary.name))
        for root in (self.paths.primary, self.paths.repeat, self.paths.control):
            root.mkdir()
        for name in PRIMARY_CONSTRUCTION_NAMES:
            (self.paths.primary / name).write_text("fixture", encoding="utf-8")
        self.spy = ScientificSpy()
        self.v1_digest = "f" * 64

    def _payload(self, decision_id: str = "decision-1") -> dict[str, object]:
        return {
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

    def _write_authorization(
        self, *, payload_updates: dict[str, object] | None = None,
        envelope_updates: dict[str, object] | None = None,
    ) -> Path:
        payload = self._payload()
        payload.update(payload_updates or {})
        payload_sha256 = canonical_json_sha256(payload)
        artifact_core = {
            "schema_version": SCHEMA_VERSION,
            "document_type": DOCUMENT_TYPES["authorization_envelope"],
            "payload": payload,
            "payload_sha256": payload_sha256,
        }
        artifact_sha256 = canonical_json_sha256(artifact_core)
        detached_signature = "fixture-detached-signature"
        trust = {
            "schema_version": SCHEMA_VERSION,
            "document_type": DOCUMENT_TYPES["trust_evidence"],
            "authorization_artifact_sha256": artifact_sha256,
            "signed_payload_sha256": payload_sha256,
            "signature_algorithm": "TEST-ONLY",
            "pinned_key_id": "fixture-key",
            "detached_signature": detached_signature,
            "detached_signature_sha256": hashlib.sha256(
                detached_signature.encode("utf-8")
            ).hexdigest(),
            "trust_policy_id": "fixture-policy",
            "external_witness_id": "fixture-witness",
        }
        envelope = {
            **artifact_core,
            "artifact_sha256": artifact_sha256,
            "trust_evidence": trust,
            "trust_evidence_sha256": canonical_json_sha256(trust),
        }
        envelope.update(envelope_updates or {})
        path = Path(self.temporary.name) / "authorization.json"
        path.write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        return path

    def _fixture_verifier(self) -> TestOnlyFixtureTrustVerifier:
        return TestOnlyFixtureTrustVerifier(
            lambda evidence, signed_payload: (
                evidence["detached_signature"] == "fixture-detached-signature"
                and canonical_json_sha256(json.loads(signed_payload))
                == evidence["signed_payload_sha256"]
            )
        )

    def _v1_verifier(self) -> str:
        return self.v1_digest

    def _claim(self, *, paths: ScreeningV2Paths | None = None):
        return prepare_screening_pair_for_test(
            paths=paths or self.paths,
            authorization=self._write_authorization(),
            fixture_trust_verifier=self._fixture_verifier(),
            frozen_v1_verifier=self._v1_verifier,
            preflight=lambda payload, paths: None,
            scientific_runner=self.spy,
        )

    def _fresh_paths(self, label: str) -> ScreeningV2Paths:
        paths = ScreeningV2Paths.under(Path(self.temporary.name) / label)
        for root in (paths.primary, paths.repeat, paths.control):
            root.mkdir(parents=True)
        for name in PRIMARY_CONSTRUCTION_NAMES:
            (paths.primary / name).write_text("fixture", encoding="utf-8")
        return paths

    @staticmethod
    def _control_terminal_path(paths: ScreeningV2Paths, role: str) -> Path:
        return paths.control / f"screening_{role}_terminal_claim.json"

    def _write_terminal_fixture(self, path: Path, attempt, **updates: object) -> None:
        terminal = {
            "schema_version": SCHEMA_VERSION,
            "document_type": DOCUMENT_TYPES["terminal"],
            "decision_id": attempt.claim.authorization.decision_id,
            "attempt_id": attempt.attempt_id,
            "role": attempt.role,
            "status": "INCOMPLETE",
            "pair_claim_sha256": attempt.claim.pair_claim_sha256,
            "role_start_sha256": attempt.role_start_sha256,
            "replication_sha256": None,
            "summary_sha256": None,
            "result_sha256": None,
            "diagnostics_sha256": None,
            "resources_sha256": None,
            "row_journal_sha256": None,
            "started_at": attempt.started_at,
            "finished_at": attempt.started_at,
            "exit_code": -9,
            "failure_code": "ROLE_CHILD_DIED",
            "failure_reason": "fixture child death",
        }
        terminal.update(updates)
        ledger.validate_schema("terminal", terminal)
        path.write_text(
            json.dumps(terminal, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def _claim_with_post_trust_preclaim(
        self,
        callback,
        *,
        authorization: Path | None = None,
        trust_verifier: TestOnlyFixtureTrustVerifier | None = None,
        frozen_v1_verifier=None,
    ):
        try:
            return prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=authorization or self._write_authorization(),
                fixture_trust_verifier=trust_verifier or self._fixture_verifier(),
                frozen_v1_verifier=frozen_v1_verifier or self._v1_verifier,
                preflight=lambda payload, paths: None,
                post_trust_preclaim=callback,
                scientific_runner=self.spy,
            )
        except TypeError as error:
            if "post_trust_preclaim" in str(error):
                self.fail(f"post-trust preclaim callback is unsupported: {error}")
            raise

    def test_missing_authorization_refuses_before_science(self) -> None:
        with self.assertRaisesRegex(AuthorizationError, "authorization"):
            prepare_screening_pair(
                paths=self.paths,
                authorization=None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_fixture_authorization_claims_pair_without_science(self) -> None:
        token = prepare_screening_pair_for_test(
            paths=self.paths,
            authorization=self._write_authorization(),
            fixture_trust_verifier=self._fixture_verifier(),
            frozen_v1_verifier=self._v1_verifier,
            preflight=lambda payload, paths: None,
            scientific_runner=self.spy,
        )
        self.assertEqual(token.primary_attempt_id, derive_attempt_id("decision-1", "primary"))
        self.assertEqual(token.repeat_attempt_id, derive_attempt_id("decision-1", "repeat"))
        self.assertEqual(self.spy.calls, 0)

    def test_raw_authorization_and_snapshot_cannot_call_public_claim(self) -> None:
        authorization = ledger._verify_envelope(self._write_authorization())
        snapshot = scan_v2_roots_for_test(self.paths)
        self.addCleanup(snapshot.close)
        with self.assertRaises(TypeError):
            claim_screening_pair(authorization, snapshot)
        with self.assertRaises(TypeError):
            PreparedPairCapability()
        forged = object.__new__(PreparedPairCapability)
        with self.assertRaisesRegex(ClaimError, "capability"):
            claim_screening_pair(forged)

    def test_failed_prepared_claim_closes_fds_once_and_consumes_capability(self) -> None:
        captured: dict[str, object] = {}
        original_claim = claim_screening_pair
        original_close = os.close
        close_calls: list[int] = []

        def capture_then_claim(capability):
            state = ledger._PREPARED_PAIR_CAPABILITIES[capability._nonce]
            captured["capability"] = capability
            captured["snapshot"] = state.snapshot
            captured["fds"] = tuple(
                item.descriptor
                for item in (
                    state.snapshot.primary,
                    state.snapshot.repeat,
                    state.snapshot.control,
                )
            )
            return original_claim(capability)

        def record_close(descriptor: int) -> None:
            if descriptor in captured.get("fds", ()):
                close_calls.append(descriptor)
            original_close(descriptor)

        def poison_after_scan(evidence, signed_payload) -> bool:
            (self.paths.repeat / "late-output").write_text("x", encoding="utf-8")
            return True

        with mock.patch.object(
            ledger, "claim_screening_pair", side_effect=capture_then_claim
        ), mock.patch.object(ledger.os, "close", side_effect=record_close):
            with self.assertRaisesRegex(ClaimError, "unexpected|changed"):
                prepare_screening_pair_for_test(
                    paths=self.paths,
                    authorization=self._write_authorization(),
                    fixture_trust_verifier=TestOnlyFixtureTrustVerifier(
                        poison_after_scan
                    ),
                    frozen_v1_verifier=self._v1_verifier,
                    preflight=lambda payload, paths: None,
                    scientific_runner=self.spy,
                )
        fds = captured["fds"]
        snapshot = captured["snapshot"]
        self.assertEqual([close_calls.count(fd) for fd in fds], [1, 1, 1])
        self.assertEqual(snapshot._descriptor_lease.active_descriptors(), ())
        self.assertEqual(
            (
                snapshot.primary.descriptor,
                snapshot.repeat.descriptor,
                snapshot.control.descriptor,
            ),
            fds,
        )
        with self.assertRaisesRegex(ClaimError, "consumed"):
            original_claim(captured["capability"])
        self.assertEqual(self.spy.calls, 0)

    def test_authorized_snapshot_bindings_are_immutable_before_publication(self) -> None:
        claim = self._claim()
        redirect = Path(self.temporary.name) / "redirect-control"
        redirect.mkdir()
        control = claim.root_snapshot.control
        with self.assertRaises(FrozenInstanceError):
            control.path = redirect
        with self.assertRaises(FrozenInstanceError):
            control.identity = (0, 0)
        with self.assertRaises(FrozenInstanceError):
            control.descriptor = control.descriptor + 1000
        start_screening_role(claim, "primary")
        self.assertEqual(tuple(redirect.iterdir()), ())
        self.assertEqual(self.spy.calls, 0)

    def test_fixture_verifier_classification_cannot_be_overridden(self) -> None:
        with self.assertRaises(TypeError):
            TestOnlyFixtureTrustVerifier(
                lambda evidence, signed_payload: True,
                test_only=False,
            )

    def test_trust_verifier_exception_is_governed_without_message_leak(self) -> None:
        def explode(evidence, signed_payload) -> bool:
            raise RuntimeError("secret verifier internals")

        with self.assertRaises(AuthorizationError) as raised:
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(),
                fixture_trust_verifier=TestOnlyFixtureTrustVerifier(explode),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(str(raised.exception), "trust verifier failed")
        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertNotIn("secret", str(raised.exception))
        self.assertEqual(self.spy.calls, 0)

    def test_production_entry_rejects_fixture_verifier_before_science(self) -> None:
        with self.assertRaisesRegex(AuthorizationError, "test-only"):
            prepare_screening_pair(
                paths=self.paths,
                authorization=self._write_authorization(),
                trust_verifier=self._fixture_verifier(),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_production_rejects_arbitrary_parent_with_exact_root_basenames(self) -> None:
        verifier = ConfiguredTrustVerifier(
            pinned_key_id="fixture-key",
            trust_policy_id="fixture-policy",
            verify_detached=lambda evidence, signed_payload: True,
        )
        with self.assertRaisesRegex(ClaimError, "absolute|frozen"):
            prepare_screening_pair(
                paths=self.paths,
                authorization=self._write_authorization(),
                trust_verifier=verifier,
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_configured_production_verifier_is_a_fail_closed_boundary(self) -> None:
        verifier = ConfiguredTrustVerifier(
            pinned_key_id="fixture-key",
            trust_policy_id="fixture-policy",
            verify_detached=lambda evidence, signed_payload: False,
        )
        authorization = ledger._verify_envelope(self._write_authorization())
        self.assertFalse(
            verifier.verify(
                authorization.envelope["trust_evidence"],
                json.dumps(
                    authorization.payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8"),
            )
        )
        self.assertEqual(self.spy.calls, 0)

    def test_schema_digest_and_attempt_id_drift_refuse_before_science(self) -> None:
        bad = self._write_authorization(
            payload_updates={"primary_attempt_id": "r006e-v2-wrong"}
        )
        with self.assertRaisesRegex(AuthorizationError, "attempt|schema"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=bad,
                fixture_trust_verifier=self._fixture_verifier(),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_authorization_symlink_refuses_before_science(self) -> None:
        authorization = self._write_authorization()
        link = Path(self.temporary.name) / "authorization-link.json"
        link.symlink_to(authorization)
        with self.assertRaisesRegex(AuthorizationError, "non-symlink"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=link,
                fixture_trust_verifier=self._fixture_verifier(),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_frozen_v1_digest_is_verified_twice_and_drift_refuses(self) -> None:
        calls = iter((self.v1_digest, "e" * 64, "e" * 64))
        with self.assertRaisesRegex(AuthorizationError, "frozen v1"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(),
                fixture_trust_verifier=self._fixture_verifier(),
                frozen_v1_verifier=lambda: next(calls),
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_trust_callback_v1_mutation_refuses_before_claim(self) -> None:
        drifted = False

        def v1_verifier() -> str:
            return "e" * 64 if drifted else self.v1_digest

        def mutate_authority(evidence, signed_payload) -> bool:
            nonlocal drifted
            drifted = True
            return True

        with self.assertRaisesRegex(AuthorizationError, "frozen v1"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(),
                fixture_trust_verifier=TestOnlyFixtureTrustVerifier(
                    mutate_authority
                ),
                frozen_v1_verifier=v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())
        self.assertEqual(self.spy.calls, 0)

    def test_post_trust_preclaim_runs_after_trust_and_before_claim(self) -> None:
        events: list[str] = []

        def trust(evidence, signed_payload) -> bool:
            del evidence, signed_payload
            events.append("trust")
            return True

        def post_trust(payload, paths) -> None:
            del payload, paths
            events.append("post-trust")
            self.assertEqual(events, ["trust", "post-trust"])
            self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())

        claim = self._claim_with_post_trust_preclaim(
            post_trust,
            trust_verifier=TestOnlyFixtureTrustVerifier(trust),
        )

        self.assertEqual(events, ["trust", "post-trust"])
        self.assertTrue(claim.claim_path.exists())
        self.assertEqual(self.spy.calls, 0)

    def test_post_trust_preclaim_payload_mutation_cannot_change_claim_metadata(
        self,
    ) -> None:
        retained: dict[str, object] = {}

        def mutate_copy(payload, paths) -> None:
            del paths
            retained["payload"] = payload
            payload["decision_id"] = "mutated-decision"
            payload["cells"][0][0] = -1
            payload["methods"].append("mutated-method")

        claim = self._claim_with_post_trust_preclaim(mutate_copy)
        retained_payload = retained["payload"]
        retained_payload["candidate_sha256"] = "b" * 64
        persisted = json.loads(claim.claim_path.read_text(encoding="utf-8"))

        self.assertEqual(claim.authorization.decision_id, "decision-1")
        self.assertEqual(
            claim.authorization.payload["cells"][0],
            list(SUMMARY_IDENTITIES[0]),
        )
        self.assertNotIn("mutated-method", claim.authorization.payload["methods"])
        self.assertEqual(claim.authorization.payload["candidate_sha256"], "a" * 64)
        self.assertEqual(persisted["decision_id"], "decision-1")

    def test_post_trust_preclaim_exception_refuses_claim_without_science(
        self,
    ) -> None:
        def explode(payload, paths) -> None:
            del payload, paths
            raise RuntimeError("private loader failure")

        with self.assertRaises(AuthorizationError) as raised:
            self._claim_with_post_trust_preclaim(explode)

        self.assertEqual(
            str(raised.exception),
            "post-trust preclaim verification failed",
        )
        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertNotIn("private loader", str(raised.exception))
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())
        self.assertEqual(self.spy.calls, 0)

    def test_post_trust_preclaim_authorization_file_mutation_refuses_claim(
        self,
    ) -> None:
        authorization = self._write_authorization()

        def mutate_authorization(payload, paths) -> None:
            del payload, paths
            authorization.write_text(
                authorization.read_text(encoding="utf-8") + " ",
                encoding="utf-8",
            )

        with self.assertRaisesRegex(AuthorizationError, "changed"):
            self._claim_with_post_trust_preclaim(
                mutate_authorization,
                authorization=authorization,
            )
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_post_trust_preclaim_frozen_v1_mutation_refuses_claim(self) -> None:
        current_digest = self.v1_digest

        def verify_v1() -> str:
            return current_digest

        def mutate_v1(payload, paths) -> None:
            nonlocal current_digest
            del payload, paths
            current_digest = "e" * 64

        with self.assertRaisesRegex(AuthorizationError, "frozen v1"):
            self._claim_with_post_trust_preclaim(
                mutate_v1,
                frozen_v1_verifier=verify_v1,
            )
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_post_trust_preclaim_root_mutation_refuses_claim(self) -> None:
        def mutate_root(payload, paths) -> None:
            del payload
            (paths.repeat / "late-output").write_text("x", encoding="utf-8")

        with self.assertRaisesRegex(ClaimError, "unexpected|changed"):
            self._claim_with_post_trust_preclaim(mutate_root)
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())

    def test_root_scan_ignores_caller_names_and_rejects_unexpected_file(self) -> None:
        (self.paths.repeat / "unexpected.csv").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(ClaimError, "unexpected"):
            scan_v2_roots_for_test(self.paths, existing_names={"repeat": set()})

    def test_primary_scan_permits_only_construction_pair(self) -> None:
        snapshot = scan_v2_roots_for_test(self.paths)
        self.assertEqual(set(snapshot.primary.entries), set(PRIMARY_CONSTRUCTION_NAMES))

    def test_claim_requires_both_construction_inputs(self) -> None:
        (self.paths.primary / PRIMARY_CONSTRUCTION_NAMES[1]).unlink()
        with self.assertRaisesRegex(ClaimError, "construction"):
            self._claim()
        self.assertEqual(self.spy.calls, 0)

    def test_empty_external_witness_refuses_before_science(self) -> None:
        authorization = self._write_authorization()
        envelope = json.loads(authorization.read_text(encoding="utf-8"))
        envelope["trust_evidence"]["external_witness_id"] = ""
        envelope["trust_evidence_sha256"] = canonical_json_sha256(
            envelope["trust_evidence"]
        )
        authorization.write_text(
            json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AuthorizationError, "external_witness_id"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=authorization,
                fixture_trust_verifier=self._fixture_verifier(),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_root_scan_rejects_dotfile_symlink_fifo_and_v1_root(self) -> None:
        cases = (".partial", "symlink", "fifo")
        for index, case in enumerate(cases):
            with self.subTest(case=case):
                root = Path(self.temporary.name) / f"case-{index}"
                paths = ScreeningV2Paths.under(root)
                for directory in (paths.primary, paths.repeat, paths.control):
                    directory.mkdir(parents=True)
                for name in PRIMARY_CONSTRUCTION_NAMES:
                    (paths.primary / name).write_text("fixture", encoding="utf-8")
                target = paths.repeat / case
                if case == "symlink":
                    target.symlink_to(paths.primary)
                elif case == "fifo":
                    os.mkfifo(target)
                else:
                    target.write_text("partial", encoding="utf-8")
                with self.assertRaisesRegex(ClaimError, "unexpected|regular|dotfile"):
                    scan_v2_roots_for_test(paths)
        v1 = ScreeningV2Paths(
            Path(self.temporary.name) / "r006e_native_supported_recovery",
            self.paths.repeat,
            self.paths.control,
        )
        with self.assertRaisesRegex(ClaimError, "exact v2"):
            scan_v2_roots_for_test(v1)

    def test_root_swap_after_snapshot_refuses_claim(self) -> None:
        moved = Path(self.temporary.name) / "moved-repeat"

        def swap_after_verification(evidence, signed_payload) -> bool:
            self.paths.repeat.rename(moved)
            self.paths.repeat.mkdir()
            return True

        with self.assertRaisesRegex(ClaimError, "changed"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(),
                fixture_trust_verifier=TestOnlyFixtureTrustVerifier(
                    swap_after_verification
                ),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )

    def test_construction_replacement_after_trust_refuses_claim(self) -> None:
        target = self.paths.primary / PRIMARY_CONSTRUCTION_NAMES[0]

        def replace_after_verification(evidence, signed_payload) -> bool:
            replacement = self.paths.primary / "replacement"
            replacement.write_text("changed", encoding="utf-8")
            os.replace(replacement, target)
            return True

        with self.assertRaisesRegex(ClaimError, "changed"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(),
                fixture_trust_verifier=TestOnlyFixtureTrustVerifier(
                    replace_after_verification
                ),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_construction_in_place_mutation_after_trust_refuses_claim(self) -> None:
        target = self.paths.primary / PRIMARY_CONSTRUCTION_NAMES[0]

        def mutate_after_verification(evidence, signed_payload) -> bool:
            with target.open("r+b") as handle:
                handle.seek(0)
                handle.write(b"mutate!")
                handle.flush()
                os.fsync(handle.fileno())
            return True

        with self.assertRaisesRegex(ClaimError, "changed"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(),
                fixture_trust_verifier=TestOnlyFixtureTrustVerifier(
                    mutate_after_verification
                ),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_pair_claim_swap_at_link_never_publishes_replacement_root(self) -> None:
        moved = Path(self.temporary.name) / "moved-control-at-claim"
        original_link = os.link
        swapped = False

        def swap_then_link(source, destination, *args, **kwargs):
            nonlocal swapped
            original_source = Path(source)
            pathname_publication = "src_dir_fd" not in kwargs
            if Path(destination).name == PAIR_CLAIM_FILENAME and not swapped:
                swapped = True
                self.paths.control.rename(moved)
                self.paths.control.mkdir()
                if pathname_publication:
                    source = moved / Path(source).name
            result = original_link(source, destination, *args, **kwargs)
            if swapped and pathname_publication:
                original_source.touch()
            return result

        with mock.patch.object(ledger.os, "link", side_effect=swap_then_link):
            with self.assertRaisesRegex(ClaimError, "changed|identity|replaced"):
                self._claim()
        self.assertFalse((self.paths.control / PAIR_CLAIM_FILENAME).exists())
        self.assertEqual(self.spy.calls, 0)

    def test_pair_claim_link_boundary_mutation_rolls_back_before_activation(
        self,
    ) -> None:
        original_link = os.link
        original_scan = ledger.scan_v2_roots_for_test
        late_output = self.paths.repeat / "late-output"
        captured: dict[str, object] = {}
        injected = False

        def capture_snapshot(paths, **kwargs):
            snapshot = original_scan(paths, **kwargs)
            captured["snapshot"] = snapshot
            return snapshot

        def link_then_mutate(source, destination, *args, **kwargs):
            nonlocal injected
            result = original_link(source, destination, *args, **kwargs)
            if Path(destination).name == PAIR_CLAIM_FILENAME and not injected:
                injected = True
                late_output.write_text("hostile mutation", encoding="utf-8")
            return result

        with (
            mock.patch.object(
                ledger,
                "scan_v2_roots_for_test",
                side_effect=capture_snapshot,
            ),
            mock.patch.object(ledger.os, "link", side_effect=link_then_mutate),
        ):
            with self.assertRaisesRegex(ClaimError, "changed|unexpected"):
                self._claim()

        snapshot = captured["snapshot"]
        claim_path = self.paths.control / PAIR_CLAIM_FILENAME
        self.assertTrue(injected)
        self.assertTrue(late_output.exists())
        self.assertFalse(claim_path.exists())
        self.assertNotIn(claim_path, ledger._ACTIVE_CLAIMS)
        self.assertEqual(snapshot._descriptor_lease.active_descriptors(), ())
        self.assertEqual(self.spy.calls, 0)

    def test_pair_claim_file_mutation_during_post_link_scan_rolls_back(
        self,
    ) -> None:
        original_scan = ledger.scan_v2_roots_for_test
        original_snapshot_file = ledger._snapshot_directory_file
        claim_path = self.paths.control / PAIR_CLAIM_FILENAME
        captured: dict[str, object] = {}
        claim_snapshot_calls = 0
        injected = False

        def capture_snapshot(paths, **kwargs):
            snapshot = original_scan(paths, **kwargs)
            captured["snapshot"] = snapshot
            return snapshot

        def snapshot_then_mutate(descriptor, name):
            nonlocal claim_snapshot_calls, injected
            snapshot = original_snapshot_file(descriptor, name)
            if name == PAIR_CLAIM_FILENAME:
                claim_snapshot_calls += 1
                if claim_snapshot_calls == 2:
                    with claim_path.open("r+b") as handle:
                        handle.seek(0)
                        handle.write(b"X")
                        handle.flush()
                        os.fsync(handle.fileno())
                    injected = True
            return snapshot

        with (
            mock.patch.object(
                ledger,
                "scan_v2_roots_for_test",
                side_effect=capture_snapshot,
            ),
            mock.patch.object(
                ledger,
                "_snapshot_directory_file",
                side_effect=snapshot_then_mutate,
            ),
        ):
            with self.assertRaisesRegex(ClaimError, "content|changed|mismatch"):
                self._claim()

        snapshot = captured["snapshot"]
        self.assertTrue(injected)
        self.assertFalse(claim_path.exists())
        self.assertNotIn(claim_path, ledger._ACTIVE_CLAIMS)
        self.assertEqual(snapshot._descriptor_lease.active_descriptors(), ())
        self.assertEqual(self.spy.calls, 0)

    def test_pair_claim_link_creation_then_exception_rolls_back(self) -> None:
        original_link = os.link
        original_scan = ledger.scan_v2_roots_for_test
        claim_path = self.paths.control / PAIR_CLAIM_FILENAME
        captured: dict[str, object] = {}
        injected = False

        def capture_snapshot(paths, **kwargs):
            snapshot = original_scan(paths, **kwargs)
            captured["snapshot"] = snapshot
            return snapshot

        def link_then_raise(source, destination, *args, **kwargs):
            nonlocal injected
            result = original_link(source, destination, *args, **kwargs)
            if Path(destination).name == PAIR_CLAIM_FILENAME and not injected:
                injected = True
                raise OSError("injected exception after link creation")
            return result

        with (
            mock.patch.object(
                ledger,
                "scan_v2_roots_for_test",
                side_effect=capture_snapshot,
            ),
            mock.patch.object(ledger.os, "link", side_effect=link_then_raise),
        ):
            with self.assertRaisesRegex(OSError, "exception after link creation"):
                self._claim()

        snapshot = captured["snapshot"]
        self.assertTrue(injected)
        self.assertFalse(claim_path.exists())
        self.assertNotIn(claim_path, ledger._ACTIVE_CLAIMS)
        self.assertEqual(snapshot._descriptor_lease.active_descriptors(), ())
        self.assertEqual(self.spy.calls, 0)

    def test_pair_claim_transaction_success_activates_and_closes_descriptors(
        self,
    ) -> None:
        claim = self._claim()
        snapshot = claim.root_snapshot
        self.addCleanup(snapshot.close)

        self.assertTrue(claim.claim_path.exists())
        self.assertEqual(
            ledger._ACTIVE_CLAIMS.get(claim.claim_path),
            claim.capability,
        )
        self.assertNotEqual(snapshot._descriptor_lease.active_descriptors(), ())

        snapshot.close()
        self.assertEqual(snapshot._descriptor_lease.active_descriptors(), ())
        self.assertEqual(self.spy.calls, 0)

    def test_concurrent_claim_has_exactly_one_winner(self) -> None:
        barrier = threading.Barrier(2)
        outcomes: list[str] = []
        lock = threading.Lock()
        authorization = self._write_authorization()

        def contender() -> None:
            try:
                barrier.wait()
                prepare_screening_pair_for_test(
                    paths=self.paths,
                    authorization=authorization,
                    fixture_trust_verifier=self._fixture_verifier(),
                    frozen_v1_verifier=self._v1_verifier,
                    preflight=lambda payload, paths: None,
                    scientific_runner=self.spy,
                )
            except ClaimError:
                outcome = "refused"
            else:
                outcome = "claimed"
            with lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=contender) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertCountEqual(outcomes, ["claimed", "refused"])
        self.assertEqual(self.spy.calls, 0)

    def test_later_decision_cannot_bypass_singleton_claim(self) -> None:
        self._claim()
        later = self._payload("decision-2")
        with self.assertRaisesRegex(ClaimError, "unexpected|prior claim"):
            prepare_screening_pair_for_test(
                paths=self.paths,
                authorization=self._write_authorization(
                    payload_updates={
                        "decision_id": later["decision_id"],
                        "primary_attempt_id": later["primary_attempt_id"],
                        "repeat_attempt_id": later["repeat_attempt_id"],
                    }
                ),
                fixture_trust_verifier=self._fixture_verifier(),
                frozen_v1_verifier=self._v1_verifier,
                preflight=lambda payload, paths: None,
                scientific_runner=self.spy,
            )
        self.assertEqual(self.spy.calls, 0)

    def test_start_without_terminal_derives_incomplete(self) -> None:
        claim = self._claim()
        attempt = start_screening_role(claim, "primary")
        self.assertEqual(attempt.attempt_id, claim.primary_attempt_id)
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "INCOMPLETE")

    def test_unexpected_file_in_any_root_before_start_refuses_publication(self) -> None:
        for root_name in ("primary", "repeat", "control"):
            with self.subTest(root=root_name):
                paths = self._fresh_paths(f"start-{root_name}")
                claim = self._claim(paths=paths)
                sidecar = getattr(paths, root_name) / "unexpected-start-sidecar.json"
                sidecar.write_text("fixture", encoding="utf-8")

                with self.assertRaisesRegex(ClaimError, "unexpected"):
                    start_screening_role(claim, "primary")

                self.assertFalse(
                    (
                        paths.control
                        / ledger.ROLE_CONTROL_START_FILENAMES["primary"]
                    ).exists()
                )
                self.assertFalse(
                    (paths.primary / ledger.ROLE_START_FILENAMES["primary"]).exists()
                )
                self.assertTrue(sidecar.exists())
        self.assertEqual(self.spy.calls, 0)

    def test_role_start_swap_at_link_never_publishes_replacement_root(self) -> None:
        claim = self._claim()
        moved = Path(self.temporary.name) / "moved-control-at-start"
        original_link = os.link
        swapped = False

        def swap_then_link(source, destination, *args, **kwargs):
            nonlocal swapped
            original_source = Path(source)
            pathname_publication = "src_dir_fd" not in kwargs
            if (
                Path(destination).name
                == ledger.ROLE_CONTROL_START_FILENAMES["primary"]
                and not swapped
            ):
                swapped = True
                self.paths.control.rename(moved)
                self.paths.control.mkdir()
                if pathname_publication:
                    source = moved / Path(source).name
            result = original_link(source, destination, *args, **kwargs)
            if swapped and pathname_publication:
                original_source.touch()
            return result

        with mock.patch.object(ledger.os, "link", side_effect=swap_then_link):
            with self.assertRaisesRegex(ClaimError, "changed|identity|replaced"):
                start_screening_role(claim, "primary")
        self.assertFalse(
            (
                self.paths.control
                / ledger.ROLE_CONTROL_START_FILENAMES["primary"]
            ).exists()
        )

    def test_live_supervisor_records_child_death_then_starts_repeat(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        terminal = publish_incomplete_terminal(
            primary,
            exit_code=-9,
            failure_code="ROLE_CHILD_DIED",
            failure_reason="child exited without a terminal",
        )
        self.assertEqual(terminal.status, "INCOMPLETE")
        repeat = start_screening_role(claim, "repeat")
        self.assertEqual(repeat.attempt_id, claim.repeat_attempt_id)
        self.assertEqual(derive_attempt_state(self.paths, "repeat"), "INCOMPLETE")
        self.assertEqual(self.spy.calls, 0)

    def test_forged_role_terminal_without_control_cannot_start_repeat(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        role_terminal = self.paths.primary / ledger.ROLE_TERMINAL_FILENAMES["primary"]
        self._write_terminal_fixture(role_terminal, primary)
        self.assertFalse(self._control_terminal_path(self.paths, "primary").exists())

        with self.assertRaisesRegex(ClaimError, "terminal.*(control|pair|marker)"):
            start_screening_role(claim, "repeat")

        self.assertFalse(
            (
                self.paths.control
                / ledger.ROLE_CONTROL_START_FILENAMES["repeat"]
            ).exists()
        )
        self.assertFalse(
            (self.paths.repeat / ledger.ROLE_START_FILENAMES["repeat"]).exists()
        )
        self.assertEqual(self.spy.calls, 0)

    def test_forged_role_terminal_without_control_has_no_derived_state(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        role_terminal = self.paths.primary / ledger.ROLE_TERMINAL_FILENAMES["primary"]
        self._write_terminal_fixture(role_terminal, primary)

        with self.assertRaisesRegex(ClaimError, "terminal.*(control|pair|marker)"):
            derive_attempt_state(self.paths, "primary")
        self.assertEqual(self.spy.calls, 0)

    def test_partial_protocol_outputs_allow_incomplete_terminal_then_repeat(
        self,
    ) -> None:
        output_names = tuple(ROLE_FILE_NAMES.values())
        self.assertEqual(ledger._ROLE_OUTPUT_FILENAMES, frozenset(output_names))
        for partition in (0, 1):
            with self.subTest(partition=partition):
                paths = self._fresh_paths(f"partial-output-{partition}")
                claim = self._claim(paths=paths)
                primary = start_screening_role(claim, "primary")
                for name in output_names[partition::2]:
                    (paths.primary / name).write_text("fixture", encoding="utf-8")

                terminal = publish_incomplete_terminal(
                    primary,
                    exit_code=-9,
                    failure_code="ROLE_CHILD_DIED",
                    failure_reason="fixture partial output",
                )
                repeat = start_screening_role(claim, "repeat")

                self.assertEqual(terminal.status, "INCOMPLETE")
                self.assertEqual(repeat.attempt_id, claim.repeat_attempt_id)
        self.assertEqual(self.spy.calls, 0)

    def test_supervisor_death_contract_retains_incomplete_and_blocks_repeat(self) -> None:
        claim = self._claim()
        start_screening_role(claim, "primary")
        with self.assertRaisesRegex(ClaimError, "primary terminal"):
            start_screening_role(claim, "repeat")
        with self.assertRaisesRegex(ClaimError, "original supervisor"):
            start_screening_role(replace(claim, supervisor_pid=os.getpid() + 1), "primary")
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "INCOMPLETE")

    def test_terminal_is_exclusive_and_cannot_be_replaced(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        publish_terminal(
            primary,
            status="FAIL",
            replication_sha256=None,
            summary_sha256=None,
            result_sha256=None,
            diagnostics_sha256=None,
            resources_sha256=None,
            row_journal_sha256=None,
            exit_code=1,
            failure_code="SCIENTIFIC_FAILURE",
            failure_reason="fixture failure",
        )
        with self.assertRaisesRegex(ClaimError, "prior claim|overwrite|publication"):
            publish_incomplete_terminal(
                primary,
                exit_code=-9,
                failure_code="ROLE_CHILD_DIED",
                failure_reason="cannot replace terminal",
            )
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "FAIL")

    def test_terminal_publishes_identical_role_and_control_markers(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        terminal = publish_incomplete_terminal(
            primary,
            exit_code=-9,
            failure_code="ROLE_CHILD_DIED",
            failure_reason="fixture child death",
        )
        control_terminal = self._control_terminal_path(self.paths, "primary")

        self.assertTrue(control_terminal.exists())
        self.assertEqual(terminal.path.read_bytes(), control_terminal.read_bytes())
        self.assertEqual(
            terminal.terminal_sha256,
            hashlib.sha256(control_terminal.read_bytes()).hexdigest(),
        )

    def test_terminal_pair_byte_drift_has_no_derived_state(self) -> None:
        for drifted_root in ("role", "control"):
            with self.subTest(root=drifted_root):
                paths = self._fresh_paths(f"terminal-drift-{drifted_root}")
                claim = self._claim(paths=paths)
                primary = start_screening_role(claim, "primary")
                publish_incomplete_terminal(
                    primary,
                    exit_code=-9,
                    failure_code="ROLE_CHILD_DIED",
                    failure_reason="fixture child death",
                )
                role_terminal = (
                    paths.primary / ledger.ROLE_TERMINAL_FILENAMES["primary"]
                )
                control_terminal = self._control_terminal_path(paths, "primary")
                if not control_terminal.exists():
                    control_terminal.write_bytes(role_terminal.read_bytes())
                drifted = (
                    role_terminal if drifted_root == "role" else control_terminal
                )
                value = json.loads(drifted.read_text(encoding="utf-8"))
                value["failure_reason"] = f"tampered {drifted_root} terminal"
                ledger.validate_schema("terminal", value)
                drifted.write_text(
                    json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    ClaimError, "terminal.*(digest|bytes|differ|drift|binding)"
                ):
                    derive_attempt_state(paths, "primary")
        self.assertEqual(self.spy.calls, 0)

    def test_semantically_invalid_matching_terminal_pair_is_rejected_by_readers(
        self,
    ) -> None:
        for reader in ("repeat", "derive"):
            with self.subTest(reader=reader):
                paths = self._fresh_paths(f"invalid-terminal-semantics-{reader}")
                claim = self._claim(paths=paths)
                primary = start_screening_role(claim, "primary")
                publish_incomplete_terminal(
                    primary,
                    exit_code=-9,
                    failure_code="ROLE_CHILD_DIED",
                    failure_reason="fixture child death",
                )
                role_terminal = (
                    paths.primary / ledger.ROLE_TERMINAL_FILENAMES["primary"]
                )
                control_terminal = self._control_terminal_path(paths, "primary")
                value = json.loads(role_terminal.read_text(encoding="utf-8"))
                value["status"] = "PASS"
                ledger.validate_schema("terminal", value)
                payload = (
                    json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
                )
                role_terminal.write_text(payload, encoding="utf-8")
                control_terminal.write_text(payload, encoding="utf-8")

                with self.assertRaisesRegex(
                    ClaimError, "PASS terminal requires complete hashes and clean exit"
                ):
                    if reader == "repeat":
                        start_screening_role(claim, "repeat")
                    else:
                        derive_attempt_state(paths, "primary")
        self.assertEqual(self.spy.calls, 0)

    def test_control_only_start_binding_drift_has_no_derived_state(self) -> None:
        mutations = {
            "decision_attempt": {
                "decision_id": "forged-decision",
                "attempt_id": derive_attempt_id("forged-decision", "primary"),
            },
            "pair_claim": {"pair_claim_sha256": "0" * 64},
        }
        for binding, updates in mutations.items():
            with self.subTest(binding=binding):
                paths = self._fresh_paths(f"control-start-drift-{binding}")
                claim = self._claim(paths=paths)
                primary = start_screening_role(claim, "primary")
                primary.start_path.unlink()
                control_start = (
                    paths.control
                    / ledger.ROLE_CONTROL_START_FILENAMES["primary"]
                )
                value = json.loads(control_start.read_text(encoding="utf-8"))
                value.update(updates)
                ledger.validate_schema("role_start", value)
                control_start.write_text(
                    json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    ClaimError, "role start .* binding changed"
                ):
                    derive_attempt_state(paths, "primary")
        self.assertEqual(self.spy.calls, 0)

    def test_unexpected_file_in_any_root_before_terminal_refuses_publication(
        self,
    ) -> None:
        for root_name in ("primary", "repeat", "control"):
            with self.subTest(root=root_name):
                paths = self._fresh_paths(f"terminal-{root_name}")
                claim = self._claim(paths=paths)
                primary = start_screening_role(claim, "primary")
                sidecar = getattr(paths, root_name) / "unexpected-terminal-sidecar.json"
                sidecar.write_text("fixture", encoding="utf-8")

                with self.assertRaisesRegex(ClaimError, "unexpected"):
                    publish_incomplete_terminal(
                        primary,
                        exit_code=-9,
                        failure_code="ROLE_CHILD_DIED",
                        failure_reason="fixture child death",
                    )

                self.assertFalse(
                    (
                        paths.primary
                        / ledger.ROLE_TERMINAL_FILENAMES["primary"]
                    ).exists()
                )
                self.assertTrue(sidecar.exists())
        self.assertEqual(self.spy.calls, 0)

    def test_terminal_swap_at_link_never_publishes_replacement_root(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        moved = Path(self.temporary.name) / "moved-primary-at-terminal"
        original_link = os.link
        swapped = False

        def swap_then_link(source, destination, *args, **kwargs):
            nonlocal swapped
            original_source = Path(source)
            pathname_publication = "src_dir_fd" not in kwargs
            if (
                Path(destination).name
                == ledger.ROLE_TERMINAL_FILENAMES["primary"]
                and not swapped
            ):
                swapped = True
                self.paths.primary.rename(moved)
                self.paths.primary.mkdir()
                if pathname_publication:
                    source = moved / Path(source).name
            result = original_link(source, destination, *args, **kwargs)
            if swapped and pathname_publication:
                original_source.touch()
            return result

        with mock.patch.object(ledger.os, "link", side_effect=swap_then_link):
            with self.assertRaisesRegex(ClaimError, "changed|identity|replaced"):
                publish_incomplete_terminal(
                    primary,
                    exit_code=-9,
                    failure_code="ROLE_CHILD_DIED",
                    failure_reason="fixture child death",
                )
        self.assertFalse(
            (self.paths.primary / ledger.ROLE_TERMINAL_FILENAMES["primary"]).exists()
        )

    def test_role_output_deletion_does_not_erase_control_claim(self) -> None:
        claim = self._claim()
        primary = start_screening_role(claim, "primary")
        primary.start_path.unlink()
        self.assertTrue((self.paths.control / PAIR_CLAIM_FILENAME).exists())
        self.assertEqual(derive_attempt_state(self.paths, "primary"), "INCOMPLETE")
        with self.assertRaisesRegex(ClaimError, "prior claim|started"):
            start_screening_role(claim, "primary")
        with self.assertRaisesRegex(ClaimError, "unexpected|prior claim"):
            self._claim()

    def test_no_resume_reset_or_reclaim_api_exists(self) -> None:
        for name in ("resume_screening_role", "reset_screening_pair", "reclaim_screening_pair"):
            self.assertFalse(hasattr(ledger, name), name)


if __name__ == "__main__":
    unittest.main()
