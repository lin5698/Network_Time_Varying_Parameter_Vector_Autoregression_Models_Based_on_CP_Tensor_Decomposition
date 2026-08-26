import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.ncs_review_corpus.qwen_batch import (
    CALIBRATION_IDS,
    MAX_INPUT_BYTES,
    build_public_review_bundle,
    build_requests,
    call_qwen,
    discover_public_sources,
    TASK_ID,
    run_batch,
    run_one,
)


def source_package(text: str = "Reviewer concern") -> dict:
    return {
        "calibration_id": "CAL-T01",
        "documents_sha256": "a" * 64,
        "documents": [
            {
                "document_id": "CAL-T01-HTML",
                "document_type": "ARTICLE_HTML",
                "pages": [],
            },
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
        ],
    }


def source_package_with_paragraphs(count: int) -> dict:
    package = source_package()
    package["documents"][1]["pages"] = [
        {
            "page_number": 1,
            "paragraphs": [
                {
                    "paragraph_id": f"CAL-T01-PR-P0001-{index:03d}",
                    "text": f"Reviewer paragraph {index}: " + ("evidence " * 80),
                }
                for index in range(1, count + 1)
            ],
        }
    ]
    return package


class QwenBatchTests(unittest.TestCase):
    def test_bundle_contains_only_redacted_public_peer_review_paragraphs(self):
        text = (
            "Reviewer concern; contact editor@example.com; "
            "see https://mts-natcomputsci.nature.com/secure/record; "
            "NATCOMPUTSCI-26-2822."
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(source_package(text)), encoding="utf-8")

            bundle = build_public_review_bundle(source, root)

        self.assertEqual(bundle["documents"][0]["document_type"], "PEER_REVIEW_FILE")
        self.assertEqual(
            bundle["documents"][0]["pages"][0]["paragraphs"][0]["paragraph_id"],
            "CAL-T01-PR-P0001-001",
        )
        redacted = bundle["documents"][0]["pages"][0]["paragraphs"][0]["text"]
        self.assertNotIn("editor@example.com", redacted)
        self.assertNotIn("mts-natcomputsci.nature.com", redacted)
        self.assertNotIn("NATCOMPUTSCI-26-2822", redacted)

    def test_requests_are_byte_bounded_and_cover_each_paragraph_once(self):
        package = source_package_with_paragraphs(12)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(package), encoding="utf-8")
            requests = build_requests(source, root, max_input_bytes=5_000)

        self.assertGreater(len(requests), 1)
        request_ids = [
            paragraph_id
            for request in requests
            for paragraph_id in request["paragraph_ids"]
        ]
        expected_ids = [
            f"CAL-T01-PR-P0001-{index:03d}" for index in range(1, 13)
        ]
        self.assertEqual(request_ids, expected_ids)
        self.assertEqual(len(request_ids), len(set(request_ids)))
        self.assertEqual({request["chunk_count"] for request in requests}, {len(requests)})
        for request in requests:
            serialized_bytes = len(
                json.dumps(
                    request["messages"], ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
            )
            self.assertEqual(request["request_bytes"], serialized_bytes)
            self.assertLessEqual(serialized_bytes, 5_000)
            self.assertLessEqual(serialized_bytes, MAX_INPUT_BYTES)

    def test_real_d02_is_split_without_loss_or_overlap(self):
        root = Path(__file__).resolve().parents[2]
        public_root = root / "archive/research_corpus/ncs/public"
        source = public_root / "calibration/extracted/cal-d02_documents.json"

        bundle = build_public_review_bundle(source, public_root)
        requests = build_requests(source, public_root)
        expected_ids = [
            paragraph["paragraph_id"]
            for page in bundle["documents"][0]["pages"]
            for paragraph in page["paragraphs"]
        ]
        actual_ids = [
            paragraph_id
            for request in requests
            for paragraph_id in request["paragraph_ids"]
        ]

        self.assertGreater(len(requests), 1)
        self.assertEqual(actual_ids, expected_ids)
        self.assertEqual(len(actual_ids), len(set(actual_ids)))
        self.assertLessEqual(max(request["request_bytes"] for request in requests), MAX_INPUT_BYTES)

    def test_discovery_is_exactly_the_six_public_calibrations(self):
        root = Path(__file__).resolve().parents[2]
        public_root = root / "archive/research_corpus/ncs/public"

        sources = discover_public_sources(public_root)

        self.assertEqual(tuple(sources), CALIBRATION_IDS)
        for calibration_id, source in sources.items():
            self.assertEqual(source.name, f"{calibration_id.lower()}_documents.json")
            self.assertTrue(source.is_relative_to(public_root))

    def test_private_ncs_root_is_rejected_before_reading_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            private_root = Path(directory) / "archive/research_corpus/ncs/private"
            private_root.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "private"):
                discover_public_sources(private_root)

    def test_call_qwen_reads_only_configured_environment_key_and_fixed_model(self):
        captured = {}

        class FakeConversation:
            @staticmethod
            def call(**kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    status_code=200,
                    output=SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content=[{"text": '{"ok": true}'}]
                                )
                            )
                        ]
                    ),
                )

        fake_dashscope = SimpleNamespace(MultiModalConversation=FakeConversation)
        messages = [{"role": "user", "content": [{"text": "{}"}]}]
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "unit-test-sentinel"}, clear=False):
            with patch.dict(sys.modules, {"dashscope": fake_dashscope}):
                response = call_qwen(messages)

        self.assertEqual(response, '{"ok": true}')
        self.assertEqual(captured["api_key"], "unit-test-sentinel")
        self.assertEqual(captured["model"], "qwen3.7-plus")
        self.assertEqual(captured["messages"], messages)

    def test_missing_api_key_completes_six_dry_runs_as_blocked(self):
        root = Path(__file__).resolve().parents[2]
        public_root = root / "archive/research_corpus/ncs/public"
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "qwen_aux"
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("DASHSCOPE_API_KEY", None)
                summary = run_batch(public_root, output_dir)

            self.assertEqual(summary["status"], "BLOCKED")
            self.assertEqual(summary["mode"], "DRY_RUN")
            self.assertEqual(tuple(summary["calibration_ids"]), CALIBRATION_IDS)
            self.assertEqual(len(summary["records"]), 6)
            self.assertIn("DASHSCOPE_API_KEY", summary["blocked_reason"])
            for record in summary["records"]:
                self.assertEqual(record["status"], "BLOCKED")
                self.assertEqual(record["mode"], "DRY_RUN")
                self.assertNotEqual(record["status"], "COMPLETE")
                receipt = json.loads((output_dir / record["output_file"]).read_text())
                self.assertEqual(receipt["status"], "BLOCKED")
                self.assertEqual(receipt["mode"], "DRY_RUN")
                self.assertEqual(receipt["blocked_reason"], summary["blocked_reason"])

            d02 = next(record for record in summary["records"] if record["calibration_id"] == "CAL-D02")
            d02_receipt = json.loads((output_dir / d02["output_file"]).read_text())
            self.assertEqual(d02_receipt["input"]["request_count"], 2)
            self.assertEqual(len(d02_receipt["input"]["requests"]), 2)
            self.assertEqual(
                sum(item["paragraph_count"] for item in d02_receipt["input"]["requests"]),
                371,
            )

    def test_live_result_is_grounded_before_complete_is_written(self):
        from unittest.mock import patch

        text = "Reviewer concern with a directly supported quote."
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(source_package(text)), encoding="utf-8")
            result = {
                "task": TASK_ID,
                "calibration_id": "CAL-T01",
                "chunk_index": 1,
                "chunk_count": 1,
                "issue_inventory": [
                    {
                        "paragraph_id": "CAL-T01-PR-P0001-001",
                        "quote": "Reviewer concern with a directly supported quote.",
                    }
                ],
                "editor_priorities_zh": [],
                "reviewer_worries_zh": ["保留该段落中的审稿人担忧。"],
                "possible_coverage_gaps_zh": [],
                "limitations_zh": [],
            }
            with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}, clear=False):
                with patch(
                    "scripts.ncs_review_corpus.qwen_batch.call_qwen",
                    return_value=json.dumps(result, ensure_ascii=False),
                ):
                    receipt = run_one(source, root, root / "out")

            self.assertEqual(receipt["status"], "COMPLETE")
            self.assertEqual(receipt["mode"], "LIVE")
            self.assertEqual(receipt["chunks"][0]["status"], "COMPLETE")
            written = (root / "out/cal-t01.json").read_text(encoding="utf-8")
            self.assertNotIn("test-key", written)

    def test_invalid_live_result_is_recorded_as_failed(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps(source_package()), encoding="utf-8")
            invalid = {
                "task": TASK_ID,
                "calibration_id": "CAL-T01",
                "chunk_index": 1,
                "chunk_count": 1,
                "issue_inventory": [
                    {"paragraph_id": "CAL-T01-PR-P0001-001", "quote": "invented"}
                ],
            }
            with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}, clear=False):
                with patch(
                    "scripts.ncs_review_corpus.qwen_batch.call_qwen",
                    return_value=json.dumps(invalid),
                ):
                    receipt = run_one(source, root, root / "out")

            self.assertEqual(receipt["status"], "FAILED")
            self.assertNotEqual(receipt["status"], "COMPLETE")
            self.assertIn("verbatim", receipt["error"])


if __name__ == "__main__":
    unittest.main()
