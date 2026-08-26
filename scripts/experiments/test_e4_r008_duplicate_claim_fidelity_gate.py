import json
import shutil
import tempfile
from pathlib import Path
import unittest

from scripts.experiments import e4_r008_duplicate_claim_fidelity_gate as gate


def _write_json(path: Path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


class E4R008DuplicateClaimFidelityGateTests(unittest.TestCase):
    def _materialize_root(self, root: Path, *, claim_activation: str = "BLOCKED") -> None:
        root.mkdir(parents=True)
        files = {
            "claim-audit.json": {
                "claim_activation": claim_activation,
                "evidence_ceiling": gate.EVIDENCE_CEILING,
                "excluded_routes": ["RCEP", "NYC"],
                "independent_cell_ci": "DERIVED_DESCRIPTIVE_ONLY",
                "independent_panel_log_ratio": "DERIVED_ARTIFACT_ONLY",
                "manuscript_or_register_update": False,
            },
            "comparator-audit.json": {"register_key": gate.REGISTER_KEY},
            "derived-panel-log-error-ratios.json": {
                "derived_values_withheld": False,
                "frozen_result_unchanged": True,
                "pair_audits": [{"ci_is_descriptive_only": True}],
            },
            "distributions.json": {"register_key": gate.REGISTER_KEY},
            "input-manifest.json": {"frozen_result_mutated": False},
            "sufficiency-audit.json": {
                "claim_activation": "BLOCKED",
                "frozen_result_mutated": False,
            },
        }
        for filename, value in files.items():
            _write_json(root / filename, value)
        output_sha256 = {
            filename: gate.sha256_file(root / filename) for filename in sorted(files)
        }
        _write_json(
            root / "artifact-manifest.json",
            {
                "author_decision_register_modified": False,
                "claim_activation": "BLOCKED",
                "content_address": "a" * 64,
                "frozen_result_mutated": False,
                "manuscript_modified": False,
                "output_sha256": output_sha256,
                "quarantine_modified": False,
                "register_key": gate.REGISTER_KEY,
            },
        )

    def test_identical_roots_with_blocked_claims_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            primary = Path(tmp) / "primary" / "cal-e01-75-aaaaaaaaaaaaaaaa"
            duplicate = Path(tmp) / "duplicate" / "cal-e01-75-aaaaaaaaaaaaaaaa"
            self._materialize_root(primary)
            shutil.copytree(primary, duplicate)

            receipt = gate.build_gate_receipt(primary, duplicate)

            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(receipt["duplicate_status"], "PASS")
            self.assertEqual(receipt["claim_fidelity_status"], "PASS")
            self.assertFalse(receipt["manuscript_values_written_by_gate"])

    def test_duplicate_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            primary = Path(tmp) / "primary" / "cal-e01-75-aaaaaaaaaaaaaaaa"
            duplicate = Path(tmp) / "duplicate" / "cal-e01-75-aaaaaaaaaaaaaaaa"
            self._materialize_root(primary)
            shutil.copytree(primary, duplicate)
            payload = json.loads((duplicate / "claim-audit.json").read_text(encoding="utf-8"))
            payload["evidence_ceiling"] = "empirical"
            _write_json(duplicate / "claim-audit.json", payload)

            with self.assertRaisesRegex(gate.GateError, "differ"):
                gate.build_gate_receipt(primary, duplicate)

    def test_claim_activation_fails_closed_even_when_roots_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            primary = Path(tmp) / "primary" / "cal-e01-75-aaaaaaaaaaaaaaaa"
            duplicate = Path(tmp) / "duplicate" / "cal-e01-75-aaaaaaaaaaaaaaaa"
            self._materialize_root(primary, claim_activation="SUPPORTED")
            shutil.copytree(primary, duplicate)

            with self.assertRaisesRegex(gate.GateError, "claim-fidelity"):
                gate.build_gate_receipt(primary, duplicate)


if __name__ == "__main__":
    unittest.main()
