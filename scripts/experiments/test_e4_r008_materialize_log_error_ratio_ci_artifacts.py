import json
from pathlib import Path
import tempfile
import unittest

from scripts.experiments import analyze_cal_e01_75 as analyzer
from scripts.experiments import e4_r008_materialize_log_error_ratio_ci_artifacts as materializer


ROOT = Path(__file__).resolve().parents[2]
INPUT_PATHS = analyzer.InputPaths(
    results=ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json",
    manifest=ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json",
    authorization=ROOT / "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json",
    register=ROOT / "output/ncs_review_corpus/v1_author_decision_register.json",
    candidate=ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/candidate.json",
    comparator_registry=ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/comparator_registry.json",
    failure_metric_schema=ROOT / "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/failure_metric_schema.json",
    plan=ROOT / "refine-logs/NCS_FOUR_ANALYSIS_PLAN_20260804_010454.md",
    e4_audit=ROOT / "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md",
    execution_complete=ROOT / "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json",
    terminal_inventory=ROOT / "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json",
    workspace_authorization=ROOT / "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json",
)


class E4R008MaterializerTests(unittest.TestCase):
    def test_materializer_writes_content_addressed_blocked_derived_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = materializer.write_derived_artifacts(
                INPUT_PATHS,
                output_parent=Path(tmp),
            )

            output_dir = Path(summary["output_dir"])
            self.assertEqual(
                output_dir.name,
                f"cal-e01-75-{summary['content_address'][:16]}",
            )
            self.assertEqual(
                {path.name for path in output_dir.iterdir() if path.is_file()},
                {
                    "artifact-manifest.json",
                    "claim-audit.json",
                    "comparator-audit.json",
                    "derived-panel-log-error-ratios.json",
                    "distributions.json",
                    "input-manifest.json",
                    "sufficiency-audit.json",
                },
            )

            manifest = json.loads(
                (output_dir / "artifact-manifest.json").read_text(encoding="utf-8")
            )
            claim = json.loads((output_dir / "claim-audit.json").read_text(encoding="utf-8"))
            derived = json.loads(
                (output_dir / "derived-panel-log-error-ratios.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(manifest["claim_activation"], "BLOCKED")
            self.assertFalse(manifest["manuscript_modified"])
            self.assertFalse(manifest["author_decision_register_modified"])
            self.assertFalse(manifest["quarantine_modified"])
            self.assertEqual(manifest["analysis_script_sha256"], analyzer.sha256_file(Path(materializer.__file__).resolve()))
            self.assertFalse(claim["manuscript_or_register_update"])
            self.assertEqual(claim["independent_panel_log_ratio"], "DERIVED_ARTIFACT_ONLY")
            self.assertEqual(claim["independent_cell_ci"], "DERIVED_DESCRIPTIVE_ONLY")
            self.assertTrue(derived["frozen_result_unchanged"])
            self.assertFalse(derived["derived_values_withheld"])
            self.assertEqual(len(derived["pair_audits"]), 32)
            self.assertTrue(
                all(pair["ci_is_descriptive_only"] for pair in derived["pair_audits"])
            )
            for filename, expected_sha in manifest["output_sha256"].items():
                self.assertEqual(analyzer.sha256_file(output_dir / filename), expected_sha)
            with self.assertRaises(FileExistsError):
                materializer.write_derived_artifacts(INPUT_PATHS, output_parent=Path(tmp))


if __name__ == "__main__":
    unittest.main()
