import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.audit_rcep_helper_candidates import audit_candidate, build_report


DATA_SOURCE = """
RCEP_LIST = ['A', 'B']
def build_tariff_relief_tc(): pass
def chow_lin_quarterly_vax(): pass
def load_quarterly_macro_and_bilateral(): pass
def quality_control_missing(): pass
def quality_control_outliers(): pass
"""

NETWORK_SOURCE = """
def girf_one(): pass
def moving_average_coefficients(): pass
"""


class CandidateAuditTests(unittest.TestCase):
    def make_repo(self, root: Path, data_source: str = DATA_SOURCE, network_source: str = NETWORK_SOURCE) -> Path:
        repo = root / "repo"
        repo.mkdir()
        (repo / "research_data_construction.py").write_text(data_source, encoding="utf-8")
        (repo / "research_network_tvp_var.py").write_text(network_source, encoding="utf-8")
        (repo / "config.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / "LICENSE").write_text("Test-only fixture licence.\n", encoding="utf-8")
        (repo / "README.md").write_text("Test-only helper.\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.name=Candidate Audit Test",
                "-c",
                "user.email=candidate-audit@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        return repo

    def test_clean_self_contained_candidate_passes_static_preflight(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self.make_repo(Path(tmpdir))
            result = audit_candidate("fixture", repo)
        self.assertEqual(result["preflight_status"], "PASS")
        self.assertTrue(result["api_contract"]["static_contract_pass"])
        self.assertFalse(result["production_trust_granted"])

    def test_missing_required_api_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self.make_repo(Path(tmpdir), network_source="def girf_one(): pass\n")
            result = audit_candidate("fixture", repo)
        self.assertEqual(result["preflight_status"], "FAIL")
        self.assertEqual(result["api_contract"]["missing_network_callables"], ["moving_average_coefficients"])

    def test_unbound_local_import_fails_current_manifest_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo = self.make_repo(root, data_source="import local_config\n" + DATA_SOURCE)
            (repo / "local_config.py").write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "local_config.py"], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "-c",
                    "user.name=Candidate Audit Test",
                    "-c",
                    "user.email=candidate-audit@example.invalid",
                    "commit",
                    "-qm",
                    "add local dependency",
                ],
                check=True,
            )
            result = audit_candidate("fixture", repo)
        self.assertEqual(result["preflight_status"], "FAIL")
        self.assertIn("local_import_dependency_not_bound_by_current_manifest", result["failures"])
        dependency_files = result["dependency_scan"]["unbound_dependency_files"]
        self.assertEqual([item["relative_path"] for item in dependency_files], ["local_config.py"])
        self.assertTrue(dependency_files[0]["git_tracked"])

    def test_dirty_checkout_warns_but_never_grants_trust(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self.make_repo(Path(tmpdir))
            (repo / "README.md").write_text("changed\n", encoding="utf-8")
            result = audit_candidate("fixture", repo)
        self.assertEqual(result["preflight_status"], "WARN")
        self.assertIn("git_worktree_is_dirty", result["warnings"])
        self.assertFalse(result["production_trust_granted"])

    def test_import_time_write_side_effect_warns(self):
        data_source = "from pathlib import Path\nPath('output').mkdir(exist_ok=True)\n" + DATA_SOURCE
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self.make_repo(Path(tmpdir), data_source=data_source)
            result = audit_candidate("fixture", repo)
        self.assertEqual(result["preflight_status"], "WARN")
        self.assertIn("import_time_side_effect_indicator_present", result["warnings"])
        indicators = result["safety_scan"]["import_time_side_effect_indicators"]
        self.assertTrue(any(item["call"].rsplit(".", 1)[-1] == "mkdir" for item in indicators))

    def test_report_keeps_every_outcome_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = self.make_repo(Path(tmpdir))
            report = build_report([("fixture", repo)])
        self.assertFalse(report["candidate_selection_made"])
        self.assertFalse(report["production_trust_granted"])
        self.assertFalse(report["scientific_execution_authorized"])
        self.assertFalse(report["r006e_outcome_authorized"])
        self.assertFalse(report["r006f_outcome_authorized"])


if __name__ == "__main__":
    unittest.main()
