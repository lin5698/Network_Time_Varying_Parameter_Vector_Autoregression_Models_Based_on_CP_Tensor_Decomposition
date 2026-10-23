"""Tests for the deterministic CAL-E02:128 frozen-data audit."""

from __future__ import annotations

import json
import copy
from pathlib import Path
import tempfile
import unittest

from scripts.experiments import analyze_cal_e02_128 as audit
from scripts.experiments.test_analyze_cal_e01_75 import (
    _execution_authorization_fixture,
    _execution_paths_fixture,
)


ROOT = Path(__file__).resolve().parents[2]
QUARANTINE = ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3"
REGISTER = ROOT / "output/ncs_review_corpus/v1_author_decision_register.json"
AUTHORIZATION_V2 = ROOT / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json"
FROZEN_PATHS = {
    "results": QUARANTINE / "e3-results.json",
    "execution_manifest": QUARANTINE / "execution-manifest.json",
    "execution_complete": QUARANTINE / "execution-complete.json",
    "terminal_inventory": ROOT / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
    "candidate": ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json",
    "workspace_authorization": ROOT / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
}


def _v2_fixture():
    authorization = json.loads(AUTHORIZATION_V2.read_text(encoding="utf-8"))
    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    frozen_values = {
        role: json.loads(path.read_text(encoding="utf-8"))
        for role, path in FROZEN_PATHS.items()
    }
    return authorization, register, FROZEN_PATHS, frozen_values


class CalE02128AuditTests(unittest.TestCase):
    def test_v2_authorization_binds_exact_register_item_and_e4_chain(self) -> None:
        authorization, register, frozen_paths, frozen_values = _v2_fixture()
        binding = audit.validate_authorization_v2(
            authorization,
            register_path=REGISTER,
            register=register,
            frozen_paths=frozen_paths,
            frozen_values=frozen_values,
        )
        self.assertEqual(binding["register_item"]["item_id"], "V1-033")
        self.assertEqual(binding["register_item"]["item_index"], 128)
        self.assertTrue(binding["e4_chain"]["complete"])
        self.assertEqual(
            binding["scope_binding"]["rec_m2_action"],
            audit.V2_REQUIRED_REC_M2_ACTION,
        )

    def test_legacy_missing_item_and_chain_hashes_are_rejected(self) -> None:
        authorization, register, frozen_paths, frozen_values = _v2_fixture()
        legacy = copy.deepcopy(authorization)
        legacy["schema_version"] = "ncs-four-analysis-authorization-v1"
        with self.assertRaises(audit.AuditError):
            audit.validate_authorization_v2(
                legacy,
                register_path=REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        missing = copy.deepcopy(authorization)
        del missing["binding"]["item_payloads"]["V1-033"]
        with self.assertRaises(audit.AuditError):
            audit.validate_authorization_v2(
                missing,
                register_path=REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        missing_scope = copy.deepcopy(authorization)
        del missing_scope["authorized_scope"]
        with self.assertRaises(audit.AuditError):
            audit.validate_authorization_v2(
                missing_scope,
                register_path=REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        tampered_values = copy.deepcopy(frozen_values)
        tampered_values["execution_manifest"]["authorization_sha256"] = "0" * 64
        with self.assertRaises(audit.AuditError):
            audit.validate_authorization_v2(
                authorization,
                register_path=REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=tampered_values,
            )

    def test_recovery_coverage_retains_non_available_statuses(self) -> None:
        rows = [
            {
                "family": "family1",
                "n": 20,
                "method": "local_structured",
                "query_class": "cross_generator",
                "horizon": 4,
                "seed": 4101,
                "target_time": 96,
                "status": "UNSTABLE",
            },
            {
                "family": "family1",
                "n": 20,
                "method": "local_structured",
                "query_class": "cross_generator",
                "horizon": 4,
                "seed": 4101,
                "target_time": 96,
                "status": "AVAILABLE",
            },
        ]
        coverage = audit._audit_recovery_coverage(rows)
        cell = next(
            cell
            for cell in coverage["cells"]
            if cell["cell"]
            == {
                "family": "family1",
                "n": 20,
                "method": "local_structured",
                "query_class": "cross_generator",
                "horizon": 4,
            }
        )
        self.assertEqual(cell["status_counts"]["UNSTABLE"], 1)
        self.assertEqual(cell["status_counts"]["AVAILABLE"], 1)
        self.assertEqual(cell["duplicate_count"], 1)
        self.assertEqual(coverage["record_count_status"], "BLOCKED")

    def test_descriptive_audit_does_not_create_fresh_freeze_payloads(self) -> None:
        analysis, files = audit.analyze(audit.default_input_paths(ROOT, REGISTER))
        self.assertFalse(analysis["fresh_payloads_created"])
        self.assertFalse(
            any(
                any(term in name for term in ("protocol", "candidate", "preoutcome"))
                for name in files
            )
        )

    def test_real_frozen_inputs_bind_v2_but_remain_blocked_by_provenance(self) -> None:
        self.assertTrue(REGISTER.is_file(), "the formal register is an external read-only input")
        paths = audit.default_input_paths(ROOT, REGISTER)
        before = {path: audit.sha256_file(path) for path in QUARANTINE.iterdir() if path.is_file()}
        analysis, files = audit.analyze(paths)
        after = {path: audit.sha256_file(path) for path in QUARANTINE.iterdir() if path.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(analysis["register_key"], "CAL-E02:128")
        self.assertEqual(analysis["coverage"]["recovery"]["observed_records"], 46080)
        self.assertEqual(analysis["coverage"]["intervals"]["observed_records"], 160)
        self.assertEqual(analysis["coverage"]["paired_common_completion"]["observed_key_count"], 32)
        self.assertEqual(analysis["data_sufficiency"], "PARTIAL")
        self.assertEqual(analysis["verdict"], "BLOCKED")
        self.assertEqual(
            analysis["hash_bindings"]["rows"]["decision_register"]["observed_status"],
            "PASS",
        )
        for check in analysis["source_checks"]["checks"].values():
            if check["status"] == "PASS":
                self.assertTrue(all(evidence["located"] for evidence in check["evidence"]))
        statuses = {cell["cell_id"]: cell["status"] for cell in analysis["required_cells"]}
        self.assertEqual(statuses["simulation_truth_provenance"], "PASS")
        self.assertEqual(statuses["independent_empirical_ground_truth"], "NOT_EVALUABLE")
        self.assertEqual(statuses["native_gate"], "PASS")
        self.assertTrue(analysis["coverage"]["recovery"]["record_provenance_missing_fields"])
        self.assertIn("retained-records.jsonl", files)

    def test_output_is_content_addressed_and_does_not_overwrite(self) -> None:
        paths = audit.default_input_paths(ROOT, REGISTER)
        analysis, files = audit.analyze(paths)
        repeated_analysis, repeated_files = audit.analyze(paths)
        self.assertEqual(analysis, repeated_analysis)
        self.assertEqual(
            {name: audit.sha256_bytes(raw) for name, raw in files.items()},
            {name: audit.sha256_bytes(raw) for name, raw in repeated_files.items()},
        )
        with tempfile.TemporaryDirectory() as temporary:
            fixture_dir = Path(temporary)
            execution_path, output_parent, observed_paths, _ = _execution_authorization_fixture(fixture_dir)
            root = output_parent / "primary" / f"cal-e02-128-{analysis['input_bundle_sha256']}"
            with self.assertRaises(audit.AuditError):
                audit.write_output(
                    root,
                    analysis,
                    files,
                    execution_authorization_path=None,
                    run_id="primary",
                    observed_paths=observed_paths,
                )
            audit.write_output(
                root,
                analysis,
                files,
                execution_authorization_path=execution_path,
                run_id="primary",
                observed_paths=observed_paths,
            )
            with self.assertRaises(audit.AuditError):
                audit.write_output(
                    root,
                    analysis,
                    files,
                    execution_authorization_path=execution_path,
                    run_id="primary",
                    observed_paths=observed_paths,
                )
            loaded = json.loads((root / "analysis.json").read_text(encoding="utf-8"))
            self.assertEqual(loaded["input_bundle_sha256"], analysis["input_bundle_sha256"])
            self.assertEqual(loaded["verdict"], "BLOCKED")

    def test_execution_authorization_fixture_binds_two_run_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            execution_path, output_parent, observed_paths, _ = _execution_authorization_fixture(directory)
            for prefix, width, digit in (
                ("cal-e01-75-", 16, "0"),
                ("cal-e02-128-", 64, "1"),
                ("cal-e02-135-", 16, "2"),
                ("cal-e03-164-", 64, "3"),
            ):
                (output_parent / "primary" / f"{prefix}{digit * width}").mkdir(parents=True)
            binding = audit.validate_execution_authorization(
                execution_path,
                output_root=output_parent / "duplicate" / ("cal-e02-128-" + "0" * 64),
                run_id="duplicate",
                observed_paths=observed_paths,
                artifact_prefix="cal-e02-128-",
                project_root=ROOT,
            )
            self.assertEqual(binding["run_id"], "duplicate")
            self.assertTrue(binding["fresh_output_required"])


if __name__ == "__main__":
    unittest.main()
