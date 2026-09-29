from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.ncs_review_corpus.coding import build_agreement, validate_coding_payload


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "scripts/ncs_review_corpus/schemas/coding_pass.schema.json").read_text(
        encoding="utf-8"
    )
)


def source_package() -> dict:
    return {
        "calibration_id": "CAL-D01",
        "documents_sha256": "a" * 64,
        "documents": [
            {
                "document_id": "CAL-D01-PR",
                "document_type": "PEER_REVIEW_FILE",
                "pages": [
                    {
                        "page_number": 2,
                        "paragraphs": [
                            {
                                "paragraph_id": "CAL-D01-PR-P0002-001",
                                "text": "The comparison with current baselines should be strengthened.",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def coding_payload(coding_pass: str = "A") -> dict:
    issue_id = f"{coding_pass}-I001"
    episode_id = f"{coding_pass}-E001"
    return {
        "schema_version": "1.0",
        "calibration_id": "CAL-D01",
        "coding_pass": coding_pass,
        "source_documents_sha256": "a" * 64,
        "article_card": {
            "research_problem_zh": "研究问题",
            "computational_significance_zh": "计算意义",
            "contribution_zh": "贡献",
            "method_zh": "方法",
            "data_or_benchmarks_zh": "数据",
            "validation_zh": "验证",
            "principal_findings_zh": "发现",
            "boundaries_zh": "边界",
            "reproducibility_zh": "复现",
            "public_decision_signal": "EXPLICIT_PUBLIC",
        },
        "episodes": [
            {
                "episode_id": episode_id,
                "episode_kind": "REVIEW_ROUND",
                "round_label": "Round 1",
                "roles_present": ["REVIEWER"],
                "summary_zh": "摘要",
                "issue_ids": [issue_id],
                "linkage_confidence": "HIGH",
            }
        ],
        "issues": [
            {
                "issue_id": issue_id,
                "episode_id": episode_id,
                "actor_role": "REVIEWER",
                "issue_type": "REQUEST",
                "concern_domain": "BASELINE_COMPARATOR",
                "requested_action": "NEW_BASELINE",
                "issue_summary_zh": "要求加强基线比较",
                "response_status": "FULLY_ADDRESSED",
                "response_summary_zh": "已增加比较",
                "impact_weight": 3,
                "impact_rationale_zh": "影响核心验证",
                "evidence": [
                    {
                        "grade": "JPR",
                        "document_id": "CAL-D01-PR",
                        "paragraph_id": "CAL-D01-PR-P0002-001",
                        "page_number": 2,
                        "quote": "comparison with current baselines should be strengthened",
                    }
                ],
                "inductive_tags": ["baseline breadth"],
                "minimum_response_zh": "解释现有比较",
                "strong_evidence_supplement_zh": "增加现代基线",
                "supported_claims_zh": ["比较得到加强"],
                "unsupported_or_unobserved_claims_zh": [],
                "cost_level": "MEDIUM",
                "cost_basis_zh": "需要重跑基线",
                "stop_conditions_zh": ["无法公平实现基线"],
            }
        ],
        "limitations": ["仅基于公开材料"],
    }


class CodingValidationTests(unittest.TestCase):
    def test_valid_payload_passes_all_contracts(self) -> None:
        self.assertEqual(
            validate_coding_payload(coding_payload(), "A", source_package(), SCHEMA), []
        )

    def test_wrong_hash_and_non_verbatim_quote_fail(self) -> None:
        payload = coding_payload()
        payload["source_documents_sha256"] = "b" * 64
        payload["issues"][0]["evidence"][0]["quote"] = "a fabricated causal result"
        errors = validate_coding_payload(payload, "A", source_package(), SCHEMA)
        self.assertTrue(any("source_documents_sha256" in error for error in errors))
        self.assertTrue(any("not verbatim" in error for error in errors))

    def test_page_document_and_grade_must_match_source(self) -> None:
        payload = coding_payload()
        evidence = payload["issues"][0]["evidence"][0]
        evidence["document_id"] = "CAL-D01-ART"
        evidence["page_number"] = 4
        evidence["grade"] = "VCO"
        errors = validate_coding_payload(payload, "A", source_package(), SCHEMA)
        self.assertTrue(any("does not own" in error for error in errors))
        self.assertTrue(any("page_number" in error for error in errors))
        self.assertTrue(any("does not match PEER_REVIEW_FILE" in error for error in errors))
        self.assertTrue(any("missing required JPR" in error for error in errors))

    def test_schema_and_episode_references_are_enforced(self) -> None:
        payload = coding_payload()
        payload["unexpected"] = True
        payload["episodes"][0]["issue_ids"] = []
        errors = validate_coding_payload(payload, "A", source_package(), SCHEMA)
        self.assertTrue(any("unexpected property" in error for error in errors))
        self.assertTrue(any("missing from episode" in error for error in errors))


class AgreementTests(unittest.TestCase):
    def test_shared_evidence_matches_and_reports_field_difference(self) -> None:
        pass_a = coding_payload("A")
        pass_b = coding_payload("B")
        pass_b["issues"][0]["response_status"] = "PARTIAL"
        pass_b["issues"][0]["impact_weight"] = 2
        result = build_agreement(pass_a, pass_b)
        self.assertEqual(result["issue_matching"]["f1"], 1.0)
        self.assertEqual(
            result["categorical_agreement"]["response_status"]["agreement_rate"], 0.0
        )
        self.assertEqual(result["impact_weight_agreement"]["within_one_rate"], 1.0)
        self.assertTrue(result["adjudication_required"])

    def test_unshared_evidence_remains_unmatched(self) -> None:
        pass_a = coding_payload("A")
        pass_b = coding_payload("B")
        pass_b["issues"][0]["evidence"][0]["paragraph_id"] = "OTHER"
        result = build_agreement(pass_a, pass_b)
        self.assertEqual(result["issue_matching"]["matched_count"], 0)
        self.assertEqual(result["issue_matching"]["unmatched_A_count"], 1)
        self.assertEqual(result["issue_matching"]["unmatched_B_count"], 1)

    def test_source_hash_mismatch_cannot_be_compared(self) -> None:
        pass_a = coding_payload("A")
        pass_b = coding_payload("B")
        pass_b["source_documents_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            build_agreement(pass_a, pass_b)


if __name__ == "__main__":
    unittest.main()
