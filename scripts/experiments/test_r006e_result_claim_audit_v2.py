"""Fixture-only tests for the independent R006e result/claim audit."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.experiments.r006e_result_claim_audit_v2 import audit_result_claim
from scripts.experiments.r006e_screening_outputs_v2 import (
    ROLE_FILE_NAMES,
    RoleMetadata,
    build_role_artifacts,
)
from scripts.experiments.r006e_screening_executor_v2 import (
    combine_cell_executions,
    retain_worker_failure,
    screening_cell_tasks,
)
from scripts.experiments.r006e_native_protocol import R006EConfig
from scripts.experiments.r006e_screening_schema_v2 import derive_attempt_id


def _role(root: Path, role: str, *, attempt_prefix: str = "audit-fixture", pair_claim_sha256: str | None = None) -> None:
    attempt_id = derive_attempt_id(attempt_prefix, role)
    executions = tuple(
        retain_worker_failure(
            task,
            construction_certificate={"status": "CONSTRUCTION_PASS"},
            attempt_id=attempt_id,
            role=role,
            generated_at="2026-07-18T00:00:00Z",
            worker_pid=123,
            peak_memory_bytes=1024,
        )
        for task in screening_cell_tasks()
    )
    execution = combine_cell_executions(executions, governance_only=True)
    metadata = RoleMetadata(
        decision_id=attempt_prefix,
        attempt_id=attempt_id,
        role=role,
        pair_claim_sha256=pair_claim_sha256 or "a" * 64,
        role_start_sha256="b" * 64,
        construction_sha256="c" * 64,
        config_sha256="d" * 64,
        candidate_sha256="e" * 64,
        provenance_sha256="f" * 64,
        started_at="2026-07-18T00:00:00Z",
        finished_at="2026-07-18T00:01:00Z",
        generated_at="2026-07-18T00:01:00Z",
    )
    artifacts = build_role_artifacts(execution, config=R006EConfig(), metadata=metadata)
    root.mkdir()
    for name, payload in artifacts.files.items():
        (root / ROLE_FILE_NAMES[name]).write_bytes(payload)


def _control(control: Path, *, decision_id: str = "audit-fixture") -> str:
    control.mkdir()
    pair = {
        "schema_version": 2,
        "document_type": "r006e_screening_pair_claim_v2",
        "decision_id": decision_id,
        "authorization_artifact_sha256": "0" * 64,
        "authorization_payload_sha256": "1" * 64,
        "trust_evidence_sha256": "2" * 64,
        "frozen_v1_authority_digest": "3" * 64,
        "primary_attempt_id": derive_attempt_id(decision_id, "primary"),
        "repeat_attempt_id": derive_attempt_id(decision_id, "repeat"),
        "primary_root": "output/high_impact_revision/r006e_native_supported_recovery_v2",
        "repeat_root": "output/high_impact_revision/r006e_native_supported_recovery_v2_repeat",
        "control_root": "output/high_impact_revision/r006e_native_supported_recovery_v2_control",
        "claimed_at": "2026-07-18T00:00:00Z",
        "supervisor_pid": 1,
        "supervisor_hostname": "fixture",
        "status": "CLAIMED",
    }
    payload = (json.dumps(pair, separators=(",", ":")) + "\n").encode()
    (control / "screening_pair_claim.json").write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _rewrite_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8")


def _refresh_role_hashes(root: Path) -> None:
    names = {
        "replication_sha256": "screening_replications.csv",
        "summary_sha256": "screening_summary.csv",
        "result_sha256": "screening_results.json",
        "diagnostics_sha256": "screening_diagnostics.jsonl",
        "resources_sha256": "screening_resources.jsonl",
        "row_journal_sha256": "screening_row_journal.jsonl",
    }
    terminal_path = root / "screening_terminal.json"
    manifest_path = root / "screening_manifest.json"
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for field, filename in names.items():
        digest = hashlib.sha256((root / filename).read_bytes()).hexdigest()
        terminal[field] = digest
        manifest[field] = digest
    _rewrite_json(terminal_path, terminal)
    manifest["terminal_sha256"] = hashlib.sha256(terminal_path.read_bytes()).hexdigest()
    _rewrite_json(manifest_path, manifest)


class ResultClaimAuditV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.primary = self.base / "primary"
        self.repeat = self.base / "repeat"
        self.control = self.base / "control"
        pair_digest = _control(self.control)
        _role(self.primary, "primary", pair_claim_sha256=pair_digest)
        _role(self.repeat, "repeat", pair_claim_sha256=pair_digest)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_successful_audit_is_simulation_only(self) -> None:
        report = audit_result_claim(
            self.primary, self.repeat, self.control, config=R006EConfig(),
            claim="simulation-only recovery under the support-conditioned frozen regime",
        )
        self.assertEqual(report["integrity_status"], "PASS")
        self.assertEqual(report["scientific_status"], "FAIL")
        self.assertEqual(report["claim_status"], "PASS")

    def test_missing_identity_is_rejected(self) -> None:
        path = self.primary / ROLE_FILE_NAMES["replication"]
        lines = path.read_bytes().splitlines(keepends=True)
        path.write_bytes(b"".join(lines[:-1]))
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")

    def test_duplicate_identity_is_rejected(self) -> None:
        path = self.primary / ROLE_FILE_NAMES["replication"]
        lines = path.read_bytes().splitlines(keepends=True)
        lines[-1] = lines[1]
        path.write_bytes(b"".join(lines))
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")

    def test_gate_disagreement_is_rejected(self) -> None:
        path = self.primary / ROLE_FILE_NAMES["summary"]
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace('false', 'true', 1), encoding="utf-8")
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")

    def test_claim_beyond_simulation_is_rejected(self) -> None:
        report = audit_result_claim(
            self.primary, self.repeat, self.control,
            claim="the method provides universal causal clinical effectiveness",
        )
        self.assertEqual(report["claim_status"], "REJECT")

    def test_duplicate_mismatch_is_rejected(self) -> None:
        result_path = self.repeat / ROLE_FILE_NAMES["result"]
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["provenance_sha256"] = "9" * 64
        _rewrite_json(result_path, result)
        _refresh_role_hashes(self.repeat)
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "PASS")
        self.assertEqual(report["scientific_status"], "FAIL")

    def test_manifest_mismatch_is_rejected(self) -> None:
        path = self.primary / ROLE_FILE_NAMES["manifest"]
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["replication_count"] = 319
        _rewrite_json(path, manifest)
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")

    def test_pair_mismatch_is_rejected(self) -> None:
        path = self.control / "screening_pair_claim.json"
        pair = json.loads(path.read_text(encoding="utf-8"))
        pair["repeat_attempt_id"] = derive_attempt_id("other", "repeat")
        _rewrite_json(path, pair)
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")

    def test_forged_pass_and_incomplete_role_are_rejected(self) -> None:
        result_path = self.primary / ROLE_FILE_NAMES["result"]
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["status"] = "PASS"
        _rewrite_json(result_path, result)
        _refresh_role_hashes(self.primary)
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")

        terminal_path = self.repeat / ROLE_FILE_NAMES["terminal"]
        terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
        terminal["status"] = "INCOMPLETE"
        _rewrite_json(terminal_path, terminal)
        report = audit_result_claim(self.primary, self.repeat, self.control)
        self.assertEqual(report["integrity_status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
