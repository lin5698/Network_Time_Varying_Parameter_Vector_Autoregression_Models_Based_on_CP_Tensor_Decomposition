from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ncs_review_corpus.provenance import (
    SCHEMA_VERSION,
    create_receipt_from_artifacts,
    scan_receipt_privacy,
    sha256_bytes,
    validate_receipt,
    verify_receipt_hashes,
    write_receipt,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "scripts/ncs_review_corpus/schemas/model_call_receipt.schema.json"


class ProvenanceReceiptTests(unittest.TestCase):
    def make_receipt(self, root: Path) -> tuple[dict, Path, Path, bytes, bytes]:
        source = root / "public-source.json"
        source.write_bytes(b'{"records":[{"id":"public-only"}]}')
        output = b'{"result":"structured"}\n'
        prompt = b"future prompt is hashed in memory only"
        receipt = create_receipt_from_artifacts(
            provider="codex",
            model="gpt-5.6-luna",
            reasoning="max",
            task_id="NCS_REVIEW_FUTURE_CALL",
            thread_id="thread-20260803-001",
            invoked_at="2026-08-03T00:00:00Z",
            completed_at="2026-08-03T00:00:01Z",
            input_files={"public_source": source},
            prompt=prompt,
            schema=SCHEMA_PATH,
            output=output,
            validator={"name": "jsonschema", "status": "PASS", "error_count": 0},
            status="COMPLETE",
        )
        return receipt, source, SCHEMA_PATH, prompt, output

    def test_receipt_contains_only_required_metadata_and_digests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt, source, schema, prompt, output = self.make_receipt(Path(directory))
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()

        self.assertEqual(receipt["schema_version"], SCHEMA_VERSION)
        self.assertEqual(receipt["input_file_hashes"][0]["label"], "public_source")
        self.assertEqual(
            receipt["input_file_hashes"][0]["sha256"],
            source_hash,
        )
        self.assertEqual(receipt["prompt_sha256"], sha256_bytes(prompt))
        self.assertEqual(receipt["schema_sha256"], hashlib.sha256(schema.read_bytes()).hexdigest())
        self.assertEqual(receipt["output_sha256"], sha256_bytes(output))
        serialized = json.dumps(receipt, ensure_ascii=False)
        self.assertNotIn(prompt.decode(), serialized)
        self.assertNotIn(output.decode(), serialized)
        self.assertNotIn(str(schema.parent), serialized)
        self.assertEqual(validate_receipt(receipt), [])

    def test_schema_declares_all_required_receipt_fields_and_no_body_fields(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "schema_version",
                "provider",
                "model",
                "reasoning",
                "task_id",
                "thread_id",
                "invoked_at",
                "completed_at",
                "input_file_hashes",
                "prompt_sha256",
                "schema_sha256",
                "output_sha256",
                "validator",
                "status",
            }.issubset(required)
        )
        self.assertTrue(schema["additionalProperties"] is False)
        self.assertNotIn("prompt", schema["properties"])
        self.assertNotIn("output", schema["properties"])
        self.assertNotIn("path", schema["properties"])

    def test_hash_verification_detects_input_prompt_schema_and_output_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, source, schema, prompt, output = self.make_receipt(root)
            verify_receipt_hashes(
                receipt,
                input_files={"public_source": source},
                prompt=prompt,
                schema=schema,
                output=output,
            )

            source.write_bytes(source.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "input_file_hashes"):
                verify_receipt_hashes(receipt, input_files={"public_source": source})
            with self.assertRaisesRegex(ValueError, "prompt_sha256"):
                verify_receipt_hashes(receipt, prompt=b"changed prompt")
            with self.assertRaisesRegex(ValueError, "schema_sha256"):
                verify_receipt_hashes(receipt, schema=b"changed schema")
            with self.assertRaisesRegex(ValueError, "output_sha256"):
                verify_receipt_hashes(receipt, output=b"changed output")

    def test_atomic_write_refuses_existing_receipt_without_changing_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, _, _, _, _ = self.make_receipt(root)
            target = root / "receipts" / "call-001.json"
            write_receipt(target, receipt)
            original = target.read_bytes()

            with self.assertRaises(FileExistsError):
                write_receipt(target, receipt)

            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(target.parent.glob(".*.tmp")), [])
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o400)

    def test_privacy_scan_rejects_bodies_secrets_environment_values_and_private_paths(self) -> None:
        unsafe = {
            "prompt": "The full prompt body must not be persisted.",
            "output": "The public material body must not be persisted.",
            "api_key": "sk-test-secret-value-12345",
            "environment_value": "unit-test-environment-secret",
            "private_path": "/Users/example/project/archive/research_corpus/ncs/private/decision.eml",
        }
        errors = scan_receipt_privacy(unsafe)
        self.assertGreaterEqual(len(errors), 5)
        self.assertTrue(all("sk-test-secret-value-12345" not in error for error in errors))
        self.assertTrue(all("decision.eml" not in error for error in errors))

    def test_sensitive_environment_value_is_not_accepted(self) -> None:
        with patch.dict(os.environ, {"TEST_API_KEY": "sentinel-secret-value"}, clear=False):
            errors = scan_receipt_privacy({"note": "sentinel-secret-value"})
        self.assertTrue(any("environment value" in error for error in errors))

    def test_non_utc_or_earlier_completion_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt, _, _, _, _ = self.make_receipt(Path(directory))
        receipt["invoked_at"] = "2026-08-03T00:00:00+00:00"
        self.assertTrue(any("invoked_at" in error for error in validate_receipt(receipt)))
        receipt["invoked_at"] = "2026-08-03T00:00:02Z"
        self.assertTrue(any("completed_at" in error for error in validate_receipt(receipt)))


if __name__ == "__main__":
    unittest.main()
