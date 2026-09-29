import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.experiments import analyze_cal_e02_135 as analyzer
from scripts.experiments.test_analyze_cal_e01_75 import _execution_authorization_fixture


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION_V2 = ROOT / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json"
REGISTER_V2 = ROOT / "output/ncs_review_corpus/v1_author_decision_register.json"
FROZEN_PATHS_V2 = {
    "results": ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json",
    "execution_manifest": ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json",
    "execution_complete": ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json",
    "terminal_inventory": ROOT / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
    "candidate": ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json",
    "workspace_authorization": ROOT / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
}


def _v2_fixture():
    authorization = json.loads(AUTHORIZATION_V2.read_text(encoding="utf-8"))
    register = json.loads(REGISTER_V2.read_text(encoding="utf-8"))
    frozen_values = {
        role: json.loads(path.read_text(encoding="utf-8"))
        for role, path in FROZEN_PATHS_V2.items()
    }
    return authorization, register, FROZEN_PATHS_V2, frozen_values


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _canonical_item_sha(value: object) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _minimal_inputs(tmp_path: Path) -> analyzer.InputPaths:
    register = {
        "items": [
            {
                "item_id": "V1-035",
                "calibration_source": {"calibration_id": "CAL-E02"},
                "item_index": 135,
                "author_decision": "PENDING",
                "author_approval_required": True,
                "current_response_status": "PARTIAL",
                "calibration_requested_action": "ROBUSTNESS_CHECK",
                "priority": "P1",
                "action_class": "NEW_ANALYSIS_OR_EXPERIMENT",
            }
        ]
    }
    records = [
        {
            "family": "family1",
            "n": 20,
            "query_class": "in_family_interpolation",
            "horizon": 4,
            "method": "fixed_rank_basis",
            "seed": 4101,
            "target_time": 96,
            "selected_hyperparameter": 2,
            "validation_loss": 0.25,
            "operator_mse": 0.1,
            "response_mse": 0.2,
            "estimated_spectral_radius": 0.3,
            "truth_spectral_radius": 0.4,
            "status": "AVAILABLE",
        },
        {
            "family": "family1",
            "n": 20,
            "query_class": "in_family_interpolation",
            "horizon": 4,
            "method": "fixed_rank_basis",
            "seed": 4102,
            "target_time": 96,
            "selected_hyperparameter": 3,
            "validation_loss": 0.30,
            "operator_mse": 0.2,
            "response_mse": 0.3,
            "estimated_spectral_radius": 0.3,
            "truth_spectral_radius": 0.4,
            "status": "UNSTABLE",
        },
    ]
    interval_records = [
        {
            "family": "family1",
            "n": 20,
            "query_class": "in_family_interpolation",
            "horizon": 4,
            "method": "fixed_rank_basis",
            "seed": 4101,
            "target_time": 143,
            "selected_hyperparameter": 2,
            "selection_status": "AVAILABLE",
            "selection_validation_loss": 0.25,
            "status": "AVAILABLE",
            "requested_replicates": 80,
            "completed_replicates": 80,
            "bootstrap_status_counts": {
                "AVAILABLE": 80,
                "NONCONVERGED": 0,
                "NONFINITE": 0,
                "OUTSIDE_TARGET": 0,
                "UNSTABLE": 0,
            },
            "coverage": 1.0,
            "mean_interval_width": 0.1,
            "raw_response_mse": 0.2,
            "stability_qualified_response_mse": 0.2,
            "estimated_spectral_radius": 0.3,
            "truth_spectral_radius": 0.4,
        }
    ]
    results = {
        "schema_version": "e3-family2-synthetic-quarantine-results-v3",
        "status": "COMPLETE_QUARANTINE_ONLY",
        "promotion": "PROHIBITED",
        "results": {
            "recovery_records": records,
            "interval_records": interval_records,
            "recovery_summary": {},
            "paired_common_completion": {},
            "interval_summary": {},
            "fixture_report": {},
        },
    }
    candidate = {"candidate_id": "e4-domain-stable-v4-20260731-candidate-r3"}
    tuning_split = {
        "content": {
            "chronological_partitions": {
                "train": {"start_inclusive": 1, "stop_exclusive": 72},
                "validation": {"start_inclusive": 72, "stop_exclusive": 96},
                "evaluation": {"start_inclusive": 96, "stop_exclusive": 144},
            },
            "selection_loss": "observed_topology_one_step_prediction",
            "candidate_lists": {"fixed_rank_basis": [1, 2, 3]},
            "tie_break": "lowest_candidate_list_index",
        }
    }
    execution_manifest = {"status": "RUNNING_QUARANTINE_ONLY"}
    execution_complete = {"status": "COMPLETE_QUARANTINE_ONLY"}
    candidate = {"candidate_id": "e4-domain-stable-v4-20260731-candidate-r3"}
    e4_authorization = {"authorization_id": "e4-r3-test"}
    terminal_inventory = {"status": "FROZEN_PENDING_INDEPENDENT_AUDIT", "artifacts": []}
    paths = analyzer.InputPaths(
        register=tmp_path / "register.json",
        authorization=tmp_path / "authorization.json",
        e4_r3_authorization=tmp_path / "e4-r3-authorization.json",
        plan=tmp_path / "plan.md",
        audit=tmp_path / "audit.md",
        results=tmp_path / "results.json",
        execution_manifest=tmp_path / "execution-manifest.json",
        execution_complete=tmp_path / "execution-complete.json",
        candidate=tmp_path / "candidate.json",
        tuning_split=tmp_path / "tuning-split.json",
        terminal_inventory=tmp_path / "terminal-inventory.json",
    )
    _write_json(paths.register, register)
    _write_json(paths.candidate, candidate)
    candidate_sha = _sha256(paths.candidate)
    e4_authorization.update(
        {"candidate_id": candidate["candidate_id"], "candidate_sha256": candidate_sha}
    )
    _write_json(paths.e4_r3_authorization, e4_authorization)
    workspace_sha = _sha256(paths.e4_r3_authorization)
    results["authorization_sha256"] = workspace_sha
    results["candidate_sha256"] = candidate_sha
    _write_json(paths.results, results)
    execution_manifest["authorization_sha256"] = workspace_sha
    execution_manifest["candidate_sha256"] = candidate_sha
    _write_json(paths.execution_manifest, execution_manifest)
    _write_json(paths.execution_complete, {
        **execution_complete,
        "authorization_sha256": workspace_sha,
        "candidate_sha256": candidate_sha,
    })
    inventory_entries = [
        {"path": str(path.resolve()), "sha256": _sha256(path)}
        for path in (
            paths.results,
            paths.execution_manifest,
            paths.execution_complete,
            paths.candidate,
            paths.e4_r3_authorization,
        )
    ]
    _write_json(paths.terminal_inventory, {**terminal_inventory, "artifacts": inventory_entries})
    register_item = json.loads(paths.register.read_text(encoding="utf-8"))["items"][0]
    authorization = {
        "authorization_id": "test-authorization-v2",
        "authorized_at": "2026-08-04T01:04:54+08:00",
        "schema_version": analyzer.AUTHORIZATION_SCHEMA_VERSION,
        "authorized_scope": {"REC_M2": [analyzer.V2_REQUIRED_REC_M2_ACTION]},
        "current_task_limits": dict(analyzer.V2_REQUIRED_TASK_LIMITS),
        "binding": {
            "decision_register_path": str(paths.register.resolve()),
            "decision_register_sha256": _sha256(paths.register),
            "item_payload_sha256_algorithm": "recursive_object_key_sort_then_JSON.stringify_utf8_no_whitespace",
            "item_payloads": {"V1-035": _canonical_item_sha(register_item)},
        },
        "frozen_e4_r3_inputs": {
            "results_sha256": _sha256(paths.results),
            "execution_manifest_sha256": _sha256(paths.execution_manifest),
            "execution_complete_sha256": _sha256(paths.execution_complete),
            "terminal_inventory_sha256": _sha256(paths.terminal_inventory),
            "candidate_sha256": candidate_sha,
        },
    }
    _write_json(paths.authorization, authorization)
    _write_json(paths.candidate, candidate)
    _write_json(paths.tuning_split, tuning_split)
    paths.plan.write_text("plan", encoding="utf-8")
    paths.audit.write_text("audit", encoding="utf-8")
    return paths


class AnalyzeCalE02135Tests(unittest.TestCase):
    def test_v2_authorization_binds_exact_register_item_and_e4_chain(self):
        authorization, register, frozen_paths, frozen_values = _v2_fixture()
        binding = analyzer.validate_authorization_v2(
            authorization,
            register_path=REGISTER_V2,
            register=register,
            frozen_paths=frozen_paths,
            frozen_values=frozen_values,
        )
        self.assertEqual(binding["register_item"]["item_id"], "V1-035")
        self.assertEqual(binding["register_item"]["item_index"], 135)
        self.assertEqual(binding["register_item"]["priority"], "P1")
        self.assertTrue(binding["e4_chain"]["complete"])
        self.assertEqual(
            binding["scope_binding"]["rec_m2_action"],
            analyzer.V2_REQUIRED_REC_M2_ACTION,
        )

    def test_legacy_missing_and_tampered_bindings_are_rejected(self):
        authorization, register, frozen_paths, frozen_values = _v2_fixture()
        legacy = copy.deepcopy(authorization)
        legacy["schema_version"] = "ncs-four-analysis-authorization-v1"
        with self.assertRaises(ValueError):
            analyzer.validate_authorization_v2(
                legacy,
                register_path=REGISTER_V2,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        missing = copy.deepcopy(authorization)
        del missing["frozen_e4_r3_inputs"]["execution_complete_sha256"]
        with self.assertRaises(ValueError):
            analyzer.validate_authorization_v2(
                missing,
                register_path=REGISTER_V2,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        missing_scope = copy.deepcopy(authorization)
        del missing_scope["current_task_limits"]
        with self.assertRaises(ValueError):
            analyzer.validate_authorization_v2(
                missing_scope,
                register_path=REGISTER_V2,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        tampered_register = copy.deepcopy(register)
        target = next(item for item in tampered_register["items"] if item["item_id"] == "V1-035")
        target["action_class"] = "DIRECT_TEXT_REVISION"
        with self.assertRaises(ValueError):
            analyzer.validate_authorization_v2(
                authorization,
                register_path=REGISTER_V2,
                register=tampered_register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

    def test_json_reader_rejects_nonfinite_extensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"value": NaN}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                analyzer.read_json(path)

    def test_summaries_retain_adverse_status_and_nonfinite_values(self) -> None:
        records = [
            {"status": "AVAILABLE", "response_mse": 1.0},
            {"status": "NONCONVERGED", "response_mse": None},
            {"status": "UNSTABLE", "response_mse": float("nan")},
        ]
        summary = analyzer._failure_stability_audit(records, [])
        self.assertEqual(summary["recovery_status_counts"]["AVAILABLE"], 1)
        self.assertEqual(summary["recovery_status_counts"]["NONCONVERGED"], 1)
        self.assertEqual(summary["recovery_status_counts"]["UNSTABLE"], 1)
        self.assertEqual(summary["nonfinite_numeric_counts"]["response_mse"], 1)
        retained = analyzer._retained_adverse_records(records, [])
        self.assertEqual(len(retained["recovery_records"]), 2)
        self.assertEqual(
            {entry["record"]["status"] for entry in retained["recovery_records"]},
            {"NONCONVERGED", "UNSTABLE"},
        )

    def test_missing_stopping_variants_blocks_full_claim_without_fresh_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = _minimal_inputs(Path(directory))
            binding, payloads, objects = analyzer.build_artifacts(
                paths,
                code_path=Path(analyzer.__file__),
            )
            self.assertEqual(len(binding), 64)
            analysis = objects["analysis"]
            self.assertEqual(analysis["verdict"], "PARTIAL")
            self.assertEqual(analysis["derived_sensitivity_verdict"], "SUPPORTED")
            self.assertEqual(analysis["full_overfitting_and_stopping_sensitivity_verdict"], "BLOCKED")
            self.assertEqual(analysis["new_grid_execution_status"], "NOT_RUN_DESCRIPTIVE_ONLY")
            self.assertEqual(
                set(objects),
                {
                    "analysis",
                    "input_manifest",
                    "sufficiency",
                    "derived",
                    "endpoint_audit",
                    "authorization_v2_binding",
                },
            )
            self.assertTrue(objects["authorization_v2_binding"]["e4_chain"]["complete"])
            self.assertEqual(objects["sufficiency"]["full_overfitting_or_stopping_claim"], "BLOCKED")
            self.assertFalse(any(
                any(term in name for term in ("protocol", "candidate", "preoutcome"))
                for name in payloads
            ))

    def test_content_addressed_writer_is_idempotent_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture_dir = Path(directory)
            execution_path, output_parent, observed_paths, _ = _execution_authorization_fixture(fixture_dir)
            output_root = output_parent / "primary" / ("cal-e02-135-" + "0" * 16)
            payloads = {"analysis.json": b"{}\n", "output-manifest.json": b"{}\n"}
            with self.assertRaises(ValueError):
                analyzer.write_content_addressed_output(
                    output_root,
                    {"analysis.json": b"changed\n"},
                )
            self.assertEqual(
                analyzer.write_content_addressed_output(
                    output_root,
                    payloads,
                    execution_authorization_path=execution_path,
                    run_id="primary",
                    observed_paths=observed_paths,
                ),
                output_root.resolve(),
            )
            with self.assertRaises(ValueError):
                analyzer.write_content_addressed_output(
                    output_root,
                    payloads,
                    execution_authorization_path=execution_path,
                    run_id="primary",
                    observed_paths=observed_paths,
                )
