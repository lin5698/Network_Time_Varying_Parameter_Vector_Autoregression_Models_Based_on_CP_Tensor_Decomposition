import copy
import contextlib
import hashlib
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

from scripts.experiments import analyze_cal_e01_75 as analyzer
from scripts.experiments import analyze_cal_e02_128 as analyzer_e02_128
from scripts.experiments import analyze_cal_e02_135 as analyzer_e02_135
from scripts.experiments import analyze_cal_e03_164 as analyzer_e03_164
from scripts.experiments.analyze_cal_e01_75 import (
    STATUS_AVAILABLE,
    STATUS_NONFINITE,
    build_panel_log_error_ratio,
    compute_normal_approximation_ci,
    reconstruct_paired_differences,
    _status_inventory,
)


def _row(method, target_time, response_mse, operator_mse, status=STATUS_AVAILABLE):
    return {
        "family": "family1",
        "n": 20,
        "query_class": "cross_generator",
        "horizon": 4,
        "seed": 4101,
        "target_time": target_time,
        "method": method,
        "status": status,
        "response_mse": response_mse,
        "operator_mse": operator_mse,
    }


ROOT = Path(__file__).resolve().parents[2]
V2_AUTHORIZATION = ROOT / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json"
V2_REGISTER = ROOT / "output/ncs_review_corpus/v1_author_decision_register.json"
V2_FROZEN_PATHS = {
    "results": ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json",
    "execution_manifest": ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json",
    "execution_complete": ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json",
    "terminal_inventory": ROOT / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
    "candidate": ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json",
    "workspace_authorization": ROOT / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
}
COMPARATOR_REGISTRY = ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/comparator_registry.json"
FAILURE_METRIC_SCHEMA = ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/failure_metric_schema.json"
PLAN = ROOT / "refine-logs/NCS_FOUR_ANALYSIS_PLAN_20260804_010454.md"
E4_AUDIT = ROOT / "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md"
M2A_RECEIPT = ROOT / "refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_M2A_REPAIR_RECEIPT_V1_20260810_222232.json"
EXECUTION_CODE_FILES = (
    "scripts/experiments/analyze_cal_e01_75.py",
    "scripts/experiments/test_analyze_cal_e01_75.py",
    "scripts/experiments/analyze_cal_e02_128.py",
    "scripts/experiments/test_analyze_cal_e02_128.py",
    "scripts/experiments/analyze_cal_e02_135.py",
    "scripts/experiments/test_analyze_cal_e02_135.py",
    "scripts/experiments/analyze_cal_e03_164.py",
    "tests/test_analyze_cal_e03_164.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _execution_paths_fixture():
    return {
        "source_authorization_v2": V2_AUTHORIZATION,
        "m2a_repair_receipt": M2A_RECEIPT,
        "decision_register": V2_REGISTER,
        "e4_results": V2_FROZEN_PATHS["results"],
        "e4_execution_manifest": V2_FROZEN_PATHS["execution_manifest"],
        "e4_execution_complete": V2_FROZEN_PATHS["execution_complete"],
        "e4_terminal_inventory": V2_FROZEN_PATHS["terminal_inventory"],
        "e4_candidate": V2_FROZEN_PATHS["candidate"],
        "workspace_authorization": V2_FROZEN_PATHS["workspace_authorization"],
    }


def _execution_authorization_fixture(directory: Path):
    output_parent = directory / "refine-logs/ncs_new_analysis_v2/rec-m2b2-fixture-20260810-01"
    execution_path = directory / (
        "refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_M2B2_EXECUTION_AUTHORIZATION_V1_"
        "20260810_235900_SYNTHETIC.json"
    )
    paths = _execution_paths_fixture()
    item_hashes = {
        "V1-026": "eb30214e8c353b27d446c1c77242bd6b2dd246841150205c8f339ddafc8f7e20",
        "V1-033": "79937fd8b053e2bc7fd9abb864938b35a72134ecf93f5f621d7c8088fd383630",
        "V1-035": "c9b9c201f94a7fd37b2049bfc44220258947f22483e769b39c19253a37e55ee8",
        "V1-045": "25cd8fbf2e623cfd2fbcdc163f50959f1beb8e8cb1b59322da78d191e802cf82",
    }
    e4_hashes = {
        "results": _sha256(paths["e4_results"]),
        "execution_manifest": _sha256(paths["e4_execution_manifest"]),
        "execution_complete": _sha256(paths["e4_execution_complete"]),
        "terminal_inventory": _sha256(paths["e4_terminal_inventory"]),
        "candidate": _sha256(paths["e4_candidate"]),
    }
    payload = {
        "schema_version": "ncs-post-acceptance-recovery-m2b2-execution-authorization-v1",
        "authorization_id": "ncs-post-acceptance-recovery-m2b2-execution-fixture-20260810-01",
        "authorized_at": "2026-08-10T23:59:00+08:00",
        "status": "PLANNED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE",
        "purpose": "planned_shared_two_run_read_only_derived_m2b2",
        "source_bindings": {
            "source_authorization_v2": {
                "path": str(paths["source_authorization_v2"].resolve()),
                "raw_sha256": _sha256(paths["source_authorization_v2"]),
            },
            "m2a_repair_receipt": {
                "path": str(paths["m2a_repair_receipt"].resolve()),
                "raw_sha256": _sha256(paths["m2a_repair_receipt"]),
            },
            "decision_register": {
                "path": str(paths["decision_register"].resolve()),
                "raw_sha256": _sha256(paths["decision_register"]),
                "canonical_item_sha256": item_hashes,
            },
            "frozen_e4_r3_inputs": {
                role: {
                    "path": str(paths[key].resolve()),
                    "raw_sha256": e4_hashes[role],
                }
                for role, key in (
                    ("results", "e4_results"),
                    ("execution_manifest", "e4_execution_manifest"),
                    ("execution_complete", "e4_execution_complete"),
                    ("terminal_inventory", "e4_terminal_inventory"),
                    ("candidate", "e4_candidate"),
                )
            },
            "workspace_authorization_chain": {
                "path": str(paths["workspace_authorization"].resolve()),
                "raw_sha256": _sha256(paths["workspace_authorization"]),
            },
        },
        "implementation": {
            "sha256_algorithm": "sha256(raw bytes)",
            "source_test_sha256": {
                path: _sha256(ROOT / path) for path in EXECUTION_CODE_FILES
            },
            "source_test_bytes": {
                path: (ROOT / path).stat().st_size for path in EXECUTION_CODE_FILES
            },
        },
        "scope": {
            "run_type": "deterministic_read_only_derived_m2",
            "run_count": 2,
            "run_ids": ["primary", "duplicate"],
            "read_only_derived": True,
            "deterministic": True,
            "register_mutation": False,
            "manuscript_mutation": False,
            "e4_r3_mutation": False,
            "claim_activation": "NOT_AUTHORIZED",
            "promotion": "NOT_AUTHORIZED",
            "rcep_nyc": "NOT_AUTHORIZED",
            "s1_s4": "NOT_AUTHORIZED",
            "n100_n200": "NOT_AUTHORIZED",
        },
        "artifact_boundary": {
            "CAL-E01:75": {
                "allowed": ["raw_comparator", "raw_paired_differences", "status_inventory"],
                "fresh_freezes": False,
            },
            "CAL-E02:128": {"allowed": ["descriptive_only"], "fresh_freezes": False},
            "CAL-E02:135": {"allowed": ["descriptive_only"], "fresh_freezes": False},
            "CAL-E03:164": {
                "allowed_scales": [20, 50],
                "n100": "NOT_RUN/ABSTAIN",
                "n200": "NOT_RUN/ABSTAIN",
            },
        },
        "output_plan": {
            "output_parent": str(output_parent.resolve()),
            "execution_id": output_parent.name,
            "fresh_before_execution": True,
            "no_overwrite": True,
            "allowed_run_ids": ["primary", "duplicate"],
            "run_layout": {
                "primary": "primary/<one-content-addressed-root-per-authorized-analyzer>",
                "duplicate": "duplicate/<one-content-addressed-root-per-authorized-analyzer>",
            },
            "authorized_artifact_prefixes": [
                "cal-e01-75-",
                "cal-e02-128-",
                "cal-e02-135-",
                "cal-e03-164-",
            ],
            "root_hex_lengths": {
                "cal-e01-75-": [16],
                "cal-e02-128-": [64],
                "cal-e02-135-": [16],
                "cal-e03-164-": [64],
            },
            "prohibited_path_tokens": ["e4_r008", "E4_R008"],
            "continuation_policy": {
                "primary": {
                    "first_call": "declared_parent_absent",
                    "later_calls": "only_primary_directory_with_prior_unique_roots",
                    "duplicate_run_forbidden": True,
                },
                "duplicate": {
                    "first_call": "completed_primary_directory_with_all_four_roots",
                    "later_calls": "only_primary_and_duplicate_directories",
                    "root_reuse_forbidden": True,
                },
            },
        },
        "provenance": {
            "parent_task": "019fbdde-2c02-7662-b9d2-9dc2b70e1253",
            "delegated_model": "gpt-5.6-luna",
            "delegated_reasoning_effort": "max",
            "independent_preflight_required": True,
            "m2_execution_proof": "NOT_ESTABLISHED",
            "historic_m2b1_status_preserved": True,
        },
    }
    execution_path.parent.mkdir(parents=True, exist_ok=True)
    execution_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return execution_path, output_parent, paths, payload


def _v2_fixture():
    authorization = json.loads(V2_AUTHORIZATION.read_text(encoding="utf-8"))
    register = json.loads(V2_REGISTER.read_text(encoding="utf-8"))
    frozen_values = {
        role: json.loads(path.read_text(encoding="utf-8"))
        for role, path in V2_FROZEN_PATHS.items()
    }
    return authorization, register, V2_FROZEN_PATHS, frozen_values


def _input_paths_fixture():
    return analyzer.InputPaths(
        results=V2_FROZEN_PATHS["results"],
        manifest=V2_FROZEN_PATHS["execution_manifest"],
        authorization=V2_AUTHORIZATION,
        register=V2_REGISTER,
        candidate=V2_FROZEN_PATHS["candidate"],
        comparator_registry=COMPARATOR_REGISTRY,
        failure_metric_schema=FAILURE_METRIC_SCHEMA,
        plan=PLAN,
        e4_audit=E4_AUDIT,
        execution_complete=V2_FROZEN_PATHS["execution_complete"],
        terminal_inventory=V2_FROZEN_PATHS["terminal_inventory"],
        workspace_authorization=V2_FROZEN_PATHS["workspace_authorization"],
    )


class AnalyzeCalE0175Tests(unittest.TestCase):
    def test_v2_authorization_binds_exact_register_item_and_e4_chain(self):
        authorization, register, frozen_paths, frozen_values = _v2_fixture()

        binding = analyzer.validate_authorization_v2(
            authorization,
            register_path=V2_REGISTER,
            register=register,
            frozen_paths=frozen_paths,
            frozen_values=frozen_values,
        )

        self.assertEqual(binding["schema_version"], "ncs-four-analysis-authorization-v2")
        self.assertEqual(binding["register_item"]["item_id"], "V1-026")
        self.assertEqual(binding["register_item"]["item_index"], 75)
        self.assertEqual(binding["register_item"]["priority"], "P0")
        self.assertEqual(binding["register_item"]["action_class"], "DIRECT_TEXT_REVISION")
        self.assertTrue(binding["e4_chain"]["complete"])
        self.assertEqual(
            authorization["current_task_limits"]["m2_scientific_analysis"],
            "BLOCKED_IN_THIS_TASK",
        )
        self.assertEqual(
            binding["scope_binding"]["rec_m2_action"],
            analyzer.V2_REQUIRED_REC_M2_ACTION,
        )

    def test_load_and_bind_inputs_exposes_current_v2_register_item(self):
        bound = analyzer._load_and_bind_inputs(_input_paths_fixture())

        self.assertEqual(bound["register_item"]["item_id"], "V1-026")
        self.assertEqual(bound["register_item"]["item_index"], 75)
        self.assertTrue(bound["hash_binding"]["terminal_inventory"]["matches"])
        self.assertTrue(bound["hash_binding"]["workspace_authorization"]["matches"])

    def test_cli_parser_accepts_only_raw_artifact_mode(self):
        raw_args = analyzer._parser().parse_args(
            [
                "--results",
                "results.json",
                "--manifest",
                "manifest.json",
                "--authorization",
                "authorization.json",
                "--register",
                "register.json",
                "--candidate",
                "candidate.json",
                "--comparator-registry",
                "comparator-registry.json",
                "--failure-metric-schema",
                "failure-metric-schema.json",
                "--execution-authorization",
                "execution-authorization.json",
                "--run-id",
                "primary",
                "--artifact-mode",
                "raw",
            ]
        )

        self.assertEqual(raw_args.artifact_mode, "raw")
        self.assertEqual(raw_args.run_id, "primary")
        self.assertEqual(raw_args.execution_authorization, Path("execution-authorization.json"))
        self.assertTrue(
            str(raw_args.output_parent).endswith("refine-logs/ncs_new_analysis_v2")
        )
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                analyzer._parser().parse_args(
                    [
                        "--results",
                        "results.json",
                        "--manifest",
                        "manifest.json",
                        "--authorization",
                        "authorization.json",
                        "--register",
                        "register.json",
                        "--candidate",
                        "candidate.json",
                        "--comparator-registry",
                        "comparator-registry.json",
                        "--failure-metric-schema",
                        "failure-metric-schema.json",
                        "--execution-authorization",
                        "execution-authorization.json",
                        "--run-id",
                        "primary",
                        "--artifact-mode",
                        "derived",
                    ]
                )

    def test_execution_authorization_is_direct_and_rejects_binding_or_layout_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            execution_path, output_parent, observed_paths, payload = _execution_authorization_fixture(directory)
            output_root = output_parent / "primary" / ("cal-e01-75-" + "0" * 16)
            binding = analyzer.validate_execution_authorization(
                execution_path,
                output_root=output_root,
                run_id="primary",
                observed_paths=observed_paths,
                artifact_prefix="cal-e01-75-",
                project_root=ROOT,
            )
            self.assertEqual(binding["schema_version"], analyzer.EXECUTION_AUTHORIZATION_SCHEMA_VERSION)
            self.assertEqual(binding["status"], analyzer.EXECUTION_AUTHORIZATION_STATUS)
            self.assertEqual(binding["run_id"], "primary")

            def reject(name, mutate, target=output_root):
                candidate = copy.deepcopy(payload)
                mutate(candidate)
                tampered = execution_path.with_name(
                    "NCS_POST_ACCEPTANCE_RECOVERY_M2B2_EXECUTION_AUTHORIZATION_V1_"
                    f"20260810_235900_{name}.json"
                )
                tampered.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                with self.assertRaises(analyzer.AuditInputError):
                    analyzer.validate_execution_authorization(
                        tampered,
                        output_root=target,
                        run_id="primary",
                        observed_paths=observed_paths,
                        artifact_prefix="cal-e01-75-",
                        project_root=ROOT,
                    )

            reject("legacy", lambda value: value.update({"schema_version": "ncs-four-analysis-authorization-v1"}))
            reject("status", lambda value: value.update({"status": "AUTHORIZED_TO_RUN"}))
            reject(
                "source-v2",
                lambda value: value["source_bindings"]["source_authorization_v2"].update({"raw_sha256": "0" * 64}),
            )
            reject(
                "m2a-receipt",
                lambda value: value["source_bindings"]["m2a_repair_receipt"].update({"raw_sha256": "0" * 64}),
            )
            reject(
                "code-sha",
                lambda value: value["implementation"]["source_test_sha256"].update(
                    {EXECUTION_CODE_FILES[0]: "0" * 64}
                ),
            )
            reject(
                "item-sha",
                lambda value: value["source_bindings"]["decision_register"]["canonical_item_sha256"].update(
                    {"V1-026": "0" * 64}
                ),
            )
            reject(
                "e4-sha",
                lambda value: value["source_bindings"]["frozen_e4_r3_inputs"]["results"].update(
                    {"raw_sha256": "0" * 64}
                ),
            )
            reject(
                "workspace-sha",
                lambda value: value["source_bindings"]["workspace_authorization_chain"].update(
                    {"raw_sha256": "0" * 64}
                ),
            )
            reject("scope", lambda value: value["scope"].update({"n100_n200": "AUTHORIZED"}))
            reject(
                "layout",
                lambda value: value["output_plan"]["run_layout"].update(
                    {"primary": "duplicate/<one-content-addressed-calibration-root>"}
                ),
            )
            e4_root = directory / "refine-logs/ncs_new_analysis_v2/e4_r008-reused"
            e4_target = e4_root / "primary" / ("cal-e01-75-" + "1" * 16)
            candidate = copy.deepcopy(payload)
            candidate["output_plan"]["output_parent"] = str(e4_root)
            candidate["output_plan"]["execution_id"] = e4_root.name
            e4_auth = execution_path.with_name(
                "NCS_POST_ACCEPTANCE_RECOVERY_M2_EXECUTION_AUTHORIZATION_V1_20260810_223606_E4.json"
            )
            e4_auth.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.validate_execution_authorization(
                    e4_auth,
                    output_root=e4_target,
                    run_id="primary",
                    observed_paths=observed_paths,
                    artifact_prefix="cal-e01-75-",
                    project_root=ROOT,
                )

            tampered_v2 = directory / "tampered-source-v2.json"
            tampered_v2.write_text("{}\n", encoding="utf-8")
            tampered_paths = dict(observed_paths)
            tampered_paths["source_authorization_v2"] = tampered_v2
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.validate_execution_authorization(
                    execution_path,
                    output_root=output_root,
                    run_id="primary",
                    observed_paths=tampered_paths,
                    artifact_prefix="cal-e01-75-",
                    project_root=ROOT,
                )
            missing_paths = dict(observed_paths)
            missing_paths["m2a_repair_receipt"] = directory / "missing-m2a-receipt.json"
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.validate_execution_authorization(
                    execution_path,
                    output_root=output_root,
                    run_id="primary",
                    observed_paths=missing_paths,
                    artifact_prefix="cal-e01-75-",
                    project_root=ROOT,
                )

            output_parent.mkdir(parents=True)
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.validate_execution_authorization(
                    execution_path,
                    output_root=output_root,
                    run_id="primary",
                    observed_paths=observed_paths,
                    artifact_prefix="cal-e01-75-",
                    project_root=ROOT,
                )

    def test_shared_multi_artifact_primary_and_duplicate_sequence_has_no_validator_writes(self):
        calls = (
            (analyzer, "cal-e01-75-", 16, "0"),
            (analyzer_e02_128, "cal-e02-128-", 64, "1"),
            (analyzer_e02_135, "cal-e02-135-", 16, "2"),
            (analyzer_e03_164, "cal-e03-164-", 64, "3"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            execution_path, output_parent, observed_paths, _ = _execution_authorization_fixture(directory)

            def target(run_id, prefix, width, digit):
                return output_parent / run_id / f"{prefix}{digit * width}"

            def validate(module, run_id, prefix, width, digit):
                root = target(run_id, prefix, width, digit)
                before = sorted(str(path.relative_to(directory)) for path in directory.rglob("*"))
                binding = module.validate_execution_authorization(
                    execution_path,
                    output_root=root,
                    run_id=run_id,
                    observed_paths=observed_paths,
                    artifact_prefix=prefix,
                    project_root=ROOT,
                )
                after = sorted(str(path.relative_to(directory)) for path in directory.rglob("*"))
                self.assertEqual(before, after)
                self.assertEqual(binding["run_id"], run_id)
                return root

            self.assertFalse(output_parent.exists())
            for module, prefix, width, digit in calls:
                root = validate(module, "primary", prefix, width, digit)
                root.mkdir(parents=True)
                (root / "artifact-manifest.json").write_text("{}\n", encoding="utf-8")

            primary_children = sorted(path.name for path in (output_parent / "primary").iterdir())
            self.assertEqual(
                primary_children,
                [
                    "cal-e01-75-" + "0" * 16,
                    "cal-e02-128-" + "1" * 64,
                    "cal-e02-135-" + "2" * 16,
                    "cal-e03-164-" + "3" * 64,
                ],
            )

            for module, prefix, width, digit in calls:
                root = validate(module, "duplicate", prefix, width, str(int(digit) + 4))
                root.mkdir(parents=True)
                (root / "artifact-manifest.json").write_text("{}\n", encoding="utf-8")

            self.assertEqual(
                sorted(path.name for path in output_parent.iterdir()),
                ["duplicate", "primary"],
            )

    def test_shared_layout_rejects_invalid_continuations_and_path_attacks(self):
        def make_file_child(parent):
            parent.mkdir(parents=True)
            (parent / "primary").write_text("not a directory\n", encoding="utf-8")

        def make_symlink_child(parent):
            parent.mkdir(parents=True)
            (parent / "primary").symlink_to(parent)

        def expect_rejection(setup, *, run_id="primary", prefix="cal-e01-75-", root_name=None):
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                execution_path, output_parent, observed_paths, _ = _execution_authorization_fixture(directory)
                setup(output_parent)
                target = output_parent / run_id / (root_name or prefix + "0" * 16)
                with self.assertRaises(analyzer.AuditInputError):
                    analyzer.validate_execution_authorization(
                        execution_path,
                        output_root=target,
                        run_id=run_id,
                        observed_paths=observed_paths,
                        artifact_prefix=prefix,
                        project_root=ROOT,
                    )

        expect_rejection(lambda parent: None, run_id="third")
        expect_rejection(
            lambda parent: (parent / "surprise").mkdir(parents=True),
        )
        expect_rejection(
            make_file_child,
            run_id="duplicate",
            root_name="cal-e01-75-" + "0" * 16,
        )
        expect_rejection(
            make_symlink_child,
            run_id="duplicate",
            root_name="cal-e01-75-" + "0" * 16,
        )
        expect_rejection(
            lambda parent: (parent / "primary").mkdir(parents=True),
            root_name="wrong-root-" + "0" * 16,
        )
        expect_rejection(
            lambda parent: (parent / "primary" / "malformed").mkdir(parents=True),
        )
        expect_rejection(
            lambda parent: (parent / "primary" / ("cal-e01-75-" + "1" * 16)).mkdir(parents=True),
        )

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            execution_path, output_parent, observed_paths, _ = _execution_authorization_fixture(directory)
            primary = output_parent / "primary"
            for prefix, width, digit in (
                ("cal-e01-75-", 16, "0"),
                ("cal-e02-128-", 64, "1"),
                ("cal-e02-135-", 16, "2"),
                ("cal-e03-164-", 64, "3"),
            ):
                (primary / f"{prefix}{digit * width}").mkdir(parents=True)
            duplicate_root = output_parent / "duplicate" / ("cal-e01-75-" + "4" * 16)
            duplicate_root.mkdir(parents=True)
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.validate_execution_authorization(
                    execution_path,
                    output_root=duplicate_root,
                    run_id="duplicate",
                    observed_paths=observed_paths,
                    artifact_prefix="cal-e01-75-",
                    project_root=ROOT,
                )

            traversal = output_parent / "primary" / ".." / ("cal-e02-128-" + "5" * 64)
            with self.assertRaises(analyzer_e02_128.AuditError):
                analyzer_e02_128.validate_execution_authorization(
                    execution_path,
                    output_root=traversal,
                    run_id="primary",
                    observed_paths=observed_paths,
                    artifact_prefix="cal-e02-128-",
                    project_root=ROOT,
                )

    def test_writer_requires_execution_authorization_before_any_permanent_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_parent = Path(tmp) / "refine-logs/ncs_new_analysis_v2/rec-m2b-missing-authorization/primary"
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.write_analysis_artifacts(
                    _input_paths_fixture(),
                    output_parent=output_parent,
                    artifact_mode="raw",
                )
            self.assertFalse(output_parent.exists())

    def test_full_analysis_uses_candidate_ready_comparator_registry(self):
        analysis = analyzer.analyze_frozen_inputs(_input_paths_fixture())
        coverage = analysis["record_audit"]["coverage"]

        self.assertEqual(coverage["recovery_records"], 46080)
        self.assertEqual(coverage["expected_recovery_records"], 46080)
        self.assertEqual(coverage["paired_cells"], 32)
        self.assertEqual(coverage["expected_paired_cells"], 32)
        self.assertEqual(
            sorted(coverage["methods"]),
            ["causal_temporal_smoother", "fixed_rank_basis", "local_structured"],
        )
        self.assertFalse(analysis["derivation_authorized"])

    def test_raw_artifact_writer_excludes_ci_and_log_ratio_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            execution_path, execution_parent, observed_paths, _ = _execution_authorization_fixture(Path(tmp))
            summary = analyzer.write_analysis_artifacts(
                _input_paths_fixture(),
                output_parent=execution_parent / "primary",
                artifact_mode="raw",
                execution_authorization_path=execution_path,
                run_id="primary",
                observed_paths=observed_paths,
            )

            output_dir = Path(summary["output_dir"])
            expected = {
                "artifact-manifest.json",
                "comparator-ledger.json",
                "input-manifest.json",
                "paired-differences.json",
                "status-inventory.json",
            }
            self.assertEqual(
                {path.name for path in output_dir.iterdir() if path.is_file()},
                expected,
            )
            for path in output_dir.iterdir():
                if path.suffix == ".json":
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    serialized = json.dumps(payload, sort_keys=True)
                    self.assertNotIn("log_error_ratio", serialized)
                    self.assertNotIn("confidence_interval", serialized)
                    self.assertNotIn("normal_approximation", serialized)
                    self.assertNotIn("bootstrap_ci", serialized)
            self.assertEqual(summary["claim_activation"], "BLOCKED")
            with self.assertRaises(analyzer.AuditInputError):
                analyzer.write_analysis_artifacts(
                    _input_paths_fixture(),
                    output_parent=execution_parent / "primary",
                    artifact_mode="raw",
                    execution_authorization_path=execution_path,
                    run_id="primary",
                    observed_paths=observed_paths,
                )

    def test_derived_artifact_mode_is_rejected_without_writing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                analyzer.write_analysis_artifacts(
                    _input_paths_fixture(),
                    output_parent=Path(tmp),
                    artifact_mode="derived",
                )
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_legacy_missing_and_tampered_v2_bindings_are_rejected(self):
        authorization, register, frozen_paths, frozen_values = _v2_fixture()

        legacy = copy.deepcopy(authorization)
        legacy["schema_version"] = "ncs-four-analysis-authorization-v1"
        with self.assertRaises(analyzer.AuditInputError):
            analyzer.validate_authorization_v2(
                legacy,
                register_path=V2_REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        missing = copy.deepcopy(authorization)
        del missing["binding"]["decision_register_sha256"]
        with self.assertRaises(analyzer.AuditInputError):
            analyzer.validate_authorization_v2(
                missing,
                register_path=V2_REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        missing_scope = copy.deepcopy(authorization)
        del missing_scope["current_task_limits"]
        with self.assertRaises(analyzer.AuditInputError):
            analyzer.validate_authorization_v2(
                missing_scope,
                register_path=V2_REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        tampered_register = copy.deepcopy(register)
        target = next(item for item in tampered_register["items"] if item["item_id"] == "V1-026")
        target["priority"] = "P9"
        with self.assertRaises(analyzer.AuditInputError):
            analyzer.validate_authorization_v2(
                authorization,
                register_path=V2_REGISTER,
                register=tampered_register,
                frozen_paths=frozen_paths,
                frozen_values=frozen_values,
            )

        tampered_values = copy.deepcopy(frozen_values)
        tampered_values["results"]["candidate_sha256"] = "0" * 64
        with self.assertRaises(analyzer.AuditInputError):
            analyzer.validate_authorization_v2(
                authorization,
                register_path=V2_REGISTER,
                register=register,
                frozen_paths=frozen_paths,
                frozen_values=tampered_values,
            )

    def test_panel_log_ratio_is_median_of_paired_log_ratios(self):
        rows = [
            _row("fixed_rank_basis", 96, 2.0, 4.0),
            _row("local_structured", 96, 4.0, 8.0),
            _row("fixed_rank_basis", 97, 1.0, 3.0),
            _row("local_structured", 97, 2.0, 6.0),
        ]

        result = build_panel_log_error_ratio(
            rows,
            candidate_method="fixed_rank_basis",
            comparator_method="local_structured",
            expected_target_times=(96, 97),
        )

        self.assertEqual(result["status"], STATUS_AVAILABLE)
        self.assertEqual(result["paired_count"], 2)
        self.assertAlmostEqual(result["response_log_error_ratio"], math.log(0.5))
        self.assertAlmostEqual(result["operator_log_error_ratio"], math.log(0.5))


    def test_panel_keeps_nonfinite_or_failed_endpoint_out_of_metrics(self):
        rows = [
            _row("fixed_rank_basis", 96, 2.0, 4.0),
            _row("local_structured", 96, 4.0, 8.0),
            _row("fixed_rank_basis", 97, float("nan"), None, STATUS_NONFINITE),
            _row("local_structured", 97, 2.0, 6.0),
        ]

        result = build_panel_log_error_ratio(
            rows,
            candidate_method="fixed_rank_basis",
            comparator_method="local_structured",
            expected_target_times=(96, 97),
        )

        self.assertEqual(result["status"], "PARTIAL_COMMON_COMPLETION")
        self.assertEqual(result["declared_count"], 2)
        self.assertEqual(result["paired_count"], 1)
        self.assertEqual(result["nonfinite_or_failed_count"], 1)
        self.assertAlmostEqual(result["response_log_error_ratio"], math.log(0.5))


    def test_cell_ci_is_deterministic_and_reports_equal_weight_panel_mean(self):
        result = compute_normal_approximation_ci(
            [-0.2, 0.0, 0.2], confidence_level=0.95
        )

        self.assertEqual(result["n"], 3)
        self.assertAlmostEqual(result["mean"], 0.0)
        self.assertAlmostEqual(result["sample_std"], 0.2)
        self.assertAlmostEqual(
            result["lower"], -1.96 * 0.2 / math.sqrt(3), places=12
        )
        self.assertAlmostEqual(
            result["upper"], 1.96 * 0.2 / math.sqrt(3), places=12
        )
        self.assertEqual(result["method"], "normal_approximation_two_sided")


    def test_reconstructed_paired_differences_match_frozen_order(self):
        rows = [
            _row("fixed_rank_basis", 97, 1.0, 3.0),
            _row("local_structured", 97, 2.0, 6.0),
            _row("fixed_rank_basis", 96, 2.0, 4.0),
            _row("local_structured", 96, 4.0, 8.0),
        ]

        result = reconstruct_paired_differences(
            rows,
            candidate_method="fixed_rank_basis",
            comparator_method="local_structured",
        )

        self.assertEqual(result["declared_count"], 2)
        self.assertEqual(result["common_completion_count"], 2)
        self.assertEqual(result["operator_mse_differences"], (-4.0, -3.0))
        self.assertEqual(result["response_mse_differences"], (-2.0, -1.0))

    def test_status_inventory_checks_paired_status_bins_without_dropping_failures(self):
        summary = {status: 0 for status in ("AVAILABLE", "NONCONVERGED", "NONFINITE", "OUTSIDE_TARGET", "UNSTABLE")}
        inventory = _status_inventory(
            [{"status": "AVAILABLE"}],
            [{"status": "AVAILABLE"}],
            {
                "family1|20|cross_generator": {
                    "status_counts": summary,
                    "bootstrap_status_counts": summary,
                }
            },
            {
                "family1|20|cross_generator|H4|fixed_rank_basis_vs_local_structured": {
                    "candidate_status_counts": summary,
                    "comparator_status_counts": summary,
                }
            },
        )

        self.assertTrue(inventory["failure_bins_present_in_summaries"])
        self.assertEqual(inventory["retained_failure_records"]["NONFINITE"], 0)


if __name__ == "__main__":
    unittest.main()
