"""Tests for the read-only CAL-E03:164 frozen-data analyzer."""

from __future__ import annotations

import hashlib
import copy
import json
from pathlib import Path
import tempfile
import unittest
import math

from scripts.experiments import analyze_cal_e03_164 as analyzer
from scripts.experiments.test_analyze_cal_e01_75 import _execution_authorization_fixture


WORKTREE = Path(__file__).resolve().parents[1]
MAIN_REGISTER = WORKTREE / "output/ncs_review_corpus/v1_author_decision_register.json"
RESULTS = WORKTREE / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json"
MANIFEST = WORKTREE / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json"
AUTHORIZATION = WORKTREE / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json"
PLAN = WORKTREE / "refine-logs/NCS_FOUR_ANALYSIS_PLAN_20260804_010454.md"
AUDIT_MARKDOWN = WORKTREE / "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md"
INVENTORY = WORKTREE / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json"
AUDIT_JSON = WORKTREE / "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.json"
CLOCK = WORKTREE / "refine-logs/E4_R3_CLOCK_PROVENANCE_20260801.json"
EXECUTION_COMPLETE = WORKTREE / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json"
AUTHORIZATION_V2 = WORKTREE / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json"
V2_FROZEN_PATHS = {
    "results": RESULTS,
    "execution_manifest": MANIFEST,
    "execution_complete": EXECUTION_COMPLETE,
    "terminal_inventory": INVENTORY,
    "candidate": WORKTREE / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json",
    "workspace_authorization": WORKTREE / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
}


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_item_sha(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class AnalyzerUnitTests(unittest.TestCase):
    def test_v2_authorization_binds_exact_register_item_and_e4_chain(self) -> None:
        authorization = json.loads(AUTHORIZATION_V2.read_text(encoding="utf-8"))
        register = json.loads(MAIN_REGISTER.read_text(encoding="utf-8"))
        frozen_values = {
            role: json.loads(path.read_text(encoding="utf-8"))
            for role, path in V2_FROZEN_PATHS.items()
        }
        binding = analyzer.validate_authorization_v2(
            authorization,
            register_path=MAIN_REGISTER,
            register=register,
            frozen_paths=V2_FROZEN_PATHS,
            frozen_values=frozen_values,
        )
        self.assertEqual(binding["register_item"]["item_id"], "V1-045")
        self.assertEqual(binding["register_item"]["item_index"], 164)
        self.assertTrue(binding["e4_chain"]["complete"])
        self.assertEqual(
            binding["scope_binding"]["rec_m2_action"],
            analyzer.V2_REQUIRED_REC_M2_ACTION,
        )

    def test_legacy_missing_and_tampered_bindings_are_rejected(self) -> None:
        authorization = json.loads(AUTHORIZATION_V2.read_text(encoding="utf-8"))
        register = json.loads(MAIN_REGISTER.read_text(encoding="utf-8"))
        frozen_values = {
            role: json.loads(path.read_text(encoding="utf-8"))
            for role, path in V2_FROZEN_PATHS.items()
        }
        legacy = copy.deepcopy(authorization)
        legacy["schema_version"] = "ncs-four-analysis-authorization-v1"
        with self.assertRaises(analyzer.AnalysisInputError):
            analyzer.validate_authorization_v2(
                legacy,
                register_path=MAIN_REGISTER,
                register=register,
                frozen_paths=V2_FROZEN_PATHS,
                frozen_values=frozen_values,
            )

        missing = copy.deepcopy(authorization)
        del missing["binding"]["item_payloads"]["V1-045"]
        with self.assertRaises(analyzer.AnalysisInputError):
            analyzer.validate_authorization_v2(
                missing,
                register_path=MAIN_REGISTER,
                register=register,
                frozen_paths=V2_FROZEN_PATHS,
                frozen_values=frozen_values,
            )

        missing_scope = copy.deepcopy(authorization)
        del missing_scope["authorized_scope"]
        with self.assertRaises(analyzer.AnalysisInputError):
            analyzer.validate_authorization_v2(
                missing_scope,
                register_path=MAIN_REGISTER,
                register=register,
                frozen_paths=V2_FROZEN_PATHS,
                frozen_values=frozen_values,
            )

        tampered = copy.deepcopy(frozen_values)
        tampered["execution_complete"]["authorization_sha256"] = "0" * 64
        with self.assertRaises(analyzer.AnalysisInputError):
            analyzer.validate_authorization_v2(
                authorization,
                register_path=MAIN_REGISTER,
                register=register,
                frozen_paths=V2_FROZEN_PATHS,
                frozen_values=tampered,
            )

    def test_numeric_stats_counts_missing_nonfinite_and_invalid(self) -> None:
        summary = analyzer.numeric_stats([1.0, float("nan"), None, "bad", 3.0])
        self.assertEqual(summary["count"], 5)
        self.assertEqual(summary["finite_count"], 2)
        self.assertEqual(summary["missing_count"], 1)
        self.assertEqual(summary["nonfinite_count"], 1)
        self.assertEqual(summary["invalid_count"], 1)

    def test_pairwise_summary_retains_adverse_and_favorable_differences(self) -> None:
        rows = analyzer.summarize_pairwise(
            {
                "family1|20|cross_generator|H4|fixed_rank_basis_vs_local_structured": {
                    "candidate_status_counts": {"AVAILABLE": 2, "UNSTABLE": 1},
                    "comparator_status_counts": {"AVAILABLE": 3},
                    "declared_date_keys": 3,
                    "common_completion_date_keys": 2,
                    "operator_mse_differences": [-1.0, 2.0, float("nan")],
                    "response_mse_differences": [-0.5, 0.25, 0.0],
                }
            }
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["operator_candidate_lower_count"], 1)
        self.assertEqual(row["operator_candidate_higher_count"], 1)
        self.assertEqual(row["response_candidate_lower_count"], 1)
        self.assertEqual(row["response_candidate_higher_count"], 1)
        self.assertEqual(row["retention"]["operator_difference_values_accounted_for"], 3)
        self.assertEqual(row["common_completion_date_keys"], 2)

    def test_small_bundle_is_deterministic_and_writes_only_new_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            register = root / "register.json"
            authorization = root / "authorization.json"
            plan = root / "plan.md"
            audit_markdown = root / "audit.md"
            results = root / "results.json"
            manifest = root / "manifest.json"
            inventory = root / "inventory.json"
            audit_json = root / "audit.json"
            completion = root / "execution-complete.json"
            candidate = root / "candidate.json"
            workspace_authorization = root / "workspace-authorization.json"

            _write_json(
                register,
                {
                    "items": [
                        {
                            "item_id": "V1-045",
                            "calibration_source": {"calibration_id": "CAL-E03"},
                            "item_index": 164,
                            "priority": "P0",
                            "action_class": "DIRECT_TEXT_REVISION",
                            "calibration_requested_action": "NEW_ANALYSIS",
                        }
                    ]
                },
            )
            plan.write_text("plan\n", encoding="utf-8")
            audit_markdown.write_text("audit\n", encoding="utf-8")
            results_payload = {
                "schema_version": "e3-family2-synthetic-quarantine-results-v3",
                "status": "COMPLETE_QUARANTINE_ONLY",
                "promotion": "PROHIBITED",
                "authorization_sha256": "authorization-binding",
                "candidate_sha256": "candidate-binding",
                "results": {
                    "fixture_report": {},
                    "recovery_records": [
                        {
                            "family": "family1",
                            "n": 20,
                            "query_class": "cross_generator",
                            "horizon": 4,
                            "method": "fixed_rank_basis",
                            "seed": 1,
                            "target_time": 1,
                            "status": "AVAILABLE",
                            "operator_mse": 1.0,
                            "response_mse": 2.0,
                            "validation_loss": 3.0,
                            "estimated_spectral_radius": 0.2,
                            "truth_spectral_radius": 0.1,
                            "selected_hyperparameter": 1,
                        },
                        {
                            "family": "family1",
                            "n": 20,
                            "query_class": "cross_generator",
                            "horizon": 4,
                            "method": "fixed_rank_basis",
                            "seed": 1,
                            "target_time": 2,
                            "status": "NONFINITE",
                            "operator_mse": None,
                            "response_mse": None,
                            "validation_loss": None,
                            "estimated_spectral_radius": None,
                            "truth_spectral_radius": 0.1,
                            "selected_hyperparameter": 1,
                        },
                    ],
                    "interval_records": [
                        {
                            "family": "family1",
                            "n": 20,
                            "query_class": "cross_generator",
                            "horizon": 4,
                            "method": "fixed_rank_basis",
                            "seed": 1,
                            "target_time": 2,
                            "status": "AVAILABLE",
                            "selection_status": "AVAILABLE",
                            "coverage": 1.0,
                            "mean_interval_width": 1.0,
                            "raw_response_mse": 2.0,
                            "stability_qualified_response_mse": 2.0,
                            "selection_validation_loss": 3.0,
                            "estimated_spectral_radius": 0.2,
                            "truth_spectral_radius": 0.1,
                            "requested_replicates": 2,
                            "completed_replicates": 2,
                            "bootstrap_retune_attempts": 2,
                            "bootstrap_status_counts": {"AVAILABLE": 2},
                        }
                    ],
                    "paired_common_completion": {},
                    "recovery_summary": {},
                    "interval_summary": {},
                },
            }
            _write_json(audit_json, {"scope_counts": {"recovery_records": 2, "interval_records": 1}})
            candidate_payload = {"candidate_id": "fixture-candidate-r3"}
            _write_json(candidate, candidate_payload)
            candidate_sha = _sha256(candidate)
            _write_json(
                workspace_authorization,
                {
                    "authorization_id": "fixture-workspace-authorization",
                    "candidate_id": candidate_payload["candidate_id"],
                    "candidate_sha256": candidate_sha,
                },
            )
            workspace_sha = _sha256(workspace_authorization)
            results_payload["authorization_sha256"] = workspace_sha
            results_payload["candidate_sha256"] = candidate_sha
            _write_json(results, results_payload)
            manifest_payload = {
                "authorization_sha256": workspace_sha,
                "candidate_sha256": candidate_sha,
                "promotion": "PROHIBITED",
                "schema_version": "e3-family2-synthetic-quarantine-results-v3",
                "scientific_execution": "AUTHORIZED_SYNTHETIC_ONLY",
                "status": "RUNNING_QUARANTINE_ONLY",
            }
            _write_json(manifest, manifest_payload)
            _write_json(
                completion,
                {
                    "authorization_sha256": workspace_sha,
                    "candidate_sha256": candidate_sha,
                    "status": "COMPLETE_QUARANTINE_ONLY",
                },
            )
            inventory_entries = [
                {"path": str(path.resolve()), "sha256": _sha256(path)}
                for path in (results, manifest, completion, candidate, workspace_authorization)
            ]
            _write_json(
                inventory,
                {
                    "status": "FROZEN_PENDING_INDEPENDENT_AUDIT",
                    "execution_contract": {"runs": 1, "last_exit_code": 0},
                    "artifacts": inventory_entries,
                },
            )
            register_item = json.loads(register.read_text(encoding="utf-8"))["items"][0]
            _write_json(
                authorization,
                {
                    "authorization_id": "fixture-analysis-authorization-v2",
                    "authorized_at": "2026-08-10T00:00:00+08:00",
                    "schema_version": "ncs-four-analysis-authorization-v2",
                    "authorized_scope": {
                        "REC_M2": [analyzer.V2_REQUIRED_REC_M2_ACTION]
                    },
                    "current_task_limits": dict(analyzer.V2_REQUIRED_TASK_LIMITS),
                    "binding": {
                        "decision_register_path": str(register.resolve()),
                        "decision_register_sha256": _sha256(register),
                        "item_payload_sha256_algorithm": "recursive_object_key_sort_then_JSON.stringify_utf8_no_whitespace",
                        "item_payloads": {"V1-045": _canonical_item_sha(register_item)},
                    },
                    "frozen_e4_r3_inputs": {
                        "results_sha256": _sha256(results),
                        "execution_manifest_sha256": _sha256(manifest),
                        "execution_complete_sha256": _sha256(completion),
                        "terminal_inventory_sha256": _sha256(inventory),
                        "candidate_sha256": candidate_sha,
                    },
                },
            )

            kwargs = {
                "decision_register_path": register,
                "authorization_path": authorization,
                "plan_path": plan,
                "audit_markdown_path": audit_markdown,
                "results_path": results,
                "execution_manifest_path": manifest,
                "project_root": root,
                "inventory_path": inventory,
                "audit_json_path": audit_json,
                "execution_complete_path": completion,
                "candidate_path": candidate,
                "workspace_authorization_path": workspace_authorization,
                "terminal_inventory_path": inventory,
            }
            first = analyzer.analyze_inputs(**kwargs)
            second = analyzer.analyze_inputs(**kwargs)
            self.assertEqual(first, second)
            self.assertEqual(first["verdicts"]["overall"], "PARTIAL")
            self.assertEqual(first["status_totals"]["recovery"]["NONFINITE"], 1)
            self.assertEqual(first["coverage"]["unrun_scale_boundary"]["n100_present"], False)
            self.assertEqual(first["coverage"]["unrun_scale_boundary"]["n200_present"], False)
            self.assertEqual(first["new_experiment"]["n100_n200_status"], "NOT_RUN/ABSTAIN")
            self.assertEqual(first["resource_audit"]["verdict"], "BLOCKED")
            self.assertEqual(first["authorization"]["authorization_gate"], "PASS")

            execution_path, execution_parent, observed_paths, _ = _execution_authorization_fixture(root)
            output_parent = execution_parent / "primary"
            with self.assertRaises(analyzer.AnalysisInputError):
                analyzer.write_outputs(first, output_parent)
            output_dir = analyzer.write_outputs(
                first,
                output_parent,
                execution_authorization_path=execution_path,
                run_id="primary",
                observed_paths=observed_paths,
            )
            self.assertTrue(output_dir.name.startswith("cal-e03-164-"))
            self.assertTrue((output_dir / "analysis.json").is_file())
            self.assertTrue((output_dir / "output-manifest.json").is_file())
            with self.assertRaises(analyzer.AnalysisInputError):
                analyzer.write_outputs(
                    first,
                    output_parent,
                    execution_authorization_path=execution_path,
                    run_id="primary",
                    observed_paths=observed_paths,
                )
            self.assertFalse((root / "register.json").stat().st_mtime == 0)


class FrozenE4R3IntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        MAIN_REGISTER.is_file() and RESULTS.is_file() and MANIFEST.is_file(),
        "frozen E4-r3 or main-project register input is unavailable",
    )
    def test_frozen_scope_and_hash_boundary(self) -> None:
        analysis = analyzer.analyze_inputs(
            decision_register_path=MAIN_REGISTER,
            authorization_path=AUTHORIZATION,
            plan_path=PLAN,
            audit_markdown_path=AUDIT_MARKDOWN,
            results_path=RESULTS,
            execution_manifest_path=MANIFEST,
            project_root=WORKTREE,
            inventory_path=INVENTORY,
                audit_json_path=AUDIT_JSON,
                clock_provenance_path=CLOCK,
                execution_complete_path=EXECUTION_COMPLETE,
                candidate_path=V2_FROZEN_PATHS["candidate"],
                workspace_authorization_path=V2_FROZEN_PATHS["workspace_authorization"],
                terminal_inventory_path=INVENTORY,
        )
        self.assertEqual(len(analysis["recovery_cells"]), 48)
        self.assertEqual(len(analysis["interval_cells"]), 8)
        self.assertEqual(len(analysis["pairwise_comparisons"]), 32)
        self.assertEqual(analysis["coverage"]["recovery"]["record_count"], 46080)
        self.assertEqual(analysis["coverage"]["interval"]["record_count"], 160)
        self.assertEqual(analysis["status_totals"]["recovery"]["AVAILABLE"], 46080)
        self.assertEqual(analysis["status_totals"]["interval"]["AVAILABLE"], 160)
        self.assertEqual(analysis["status_totals"]["bootstrap"]["AVAILABLE"], 12800)
        self.assertEqual(analysis["nonfinite_totals"], {"recovery": 0, "interval": 0})
        self.assertEqual(analysis["verdicts"]["overall"], "PARTIAL")
        self.assertEqual(analysis["verdicts"]["authorization_binding"], "PASS")
        self.assertFalse(analysis["coverage"]["unrun_scale_boundary"]["n100_present"])
        self.assertFalse(analysis["coverage"]["unrun_scale_boundary"]["n200_present"])
        self.assertEqual(
            analysis["input_binding"]["expected_decision_register_sha256"],
            json.loads(AUTHORIZATION_V2.read_text(encoding="utf-8"))["binding"]["decision_register_sha256"],
        )
        self.assertEqual(
            analysis["input_binding"]["expected_decision_register_sha256"],
            analysis["input_binding"]["observed_input_sha256"]["decision_register"],
        )


if __name__ == "__main__":
    unittest.main()
