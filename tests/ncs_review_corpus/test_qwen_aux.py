import json
import tempfile
import unittest
from pathlib import Path

from scripts.ncs_review_corpus.qwen_aux import (
    MAX_INPUT_BYTES,
    TASK_ID,
    build_messages,
    build_public_review_bundle,
    validate_result,
)


def source_package(text: str = "Reviewer concern with contact editor@example.com") -> dict:
    return {
        "calibration_id": "CAL-T01",
        "documents_sha256": "a" * 64,
        "documents": [
            {
                "document_id": "CAL-T01-PR",
                "document_type": "PEER_REVIEW_FILE",
                "pages": [
                    {
                        "page_number": 1,
                        "paragraphs": [
                            {"paragraph_id": "CAL-T01-PR-P0001-001", "text": text}
                        ],
                    }
                ],
            },
            {
                "document_id": "CAL-T01-HTML",
                "document_type": "ARTICLE_HTML",
                "pages": [],
            },
        ],
    }


class QwenAuxTests(unittest.TestCase):
    def test_bundle_is_public_review_only_and_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(source_package()), encoding="utf-8")
            bundle = build_public_review_bundle(source, root)
        self.assertEqual(len(bundle["documents"]), 1)
        text = bundle["documents"][0]["pages"][0]["paragraphs"][0]["text"]
        self.assertNotIn("example.com", text)
        self.assertIn("[REDACTED_EMAIL]", text)

    def test_source_outside_public_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public_root = root / "public"
            public_root.mkdir()
            source = root / "private.json"
            source.write_text(json.dumps(source_package()), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "public root"):
                build_public_review_bundle(source, public_root)

    def test_request_has_conservative_256k_byte_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(source_package()), encoding="utf-8")
            bundle = build_public_review_bundle(source, root)
        _, input_bytes = build_messages(bundle)
        self.assertLessEqual(input_bytes, MAX_INPUT_BYTES)
        with self.assertRaisesRegex(ValueError, "limit"):
            build_messages(bundle, max_input_bytes=10)

    def test_result_requires_grounded_verbatim_quote(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(source_package("Reviewer concern")), encoding="utf-8")
            bundle = build_public_review_bundle(source, root)
        result = {
            "task": TASK_ID,
            "calibration_id": "CAL-T01",
            "issue_inventory": [
                {
                    "paragraph_id": "CAL-T01-PR-P0001-001",
                    "quote": "Reviewer concern",
                }
            ],
        }
        self.assertEqual(validate_result(result, bundle), [])
        result["issue_inventory"][0]["quote"] = "invented"
        self.assertTrue(validate_result(result, bundle))


if __name__ == "__main__":
    unittest.main()
