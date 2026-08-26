from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ncs_review_corpus import screen
from scripts.ncs_review_corpus.core import (
    MODEL_ID,
    REASONING_EFFORT,
    SCHEMA_VERSION,
    sha256_bytes,
    sha256_json,
)


SCHEMA_PATH = Path(screen.__file__).parent / "schemas" / "screen_batch.schema.json"


def source_record(index: int) -> dict[str, object]:
    return {
        "doi": f"10.1038/ncs-screen-{index:04d}",
        "title": f"Network method title {index}",
        "publication_date": "2024-01-01",
    }


def source_snapshot(records: list[dict[str, object]]) -> dict[str, object]:
    return {"records_sha256": sha256_json(records), "records": records}


def screening_result(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "records": [
            {
                "doi": record["doi"],
                "relatedness_level": "A",
                "document_kind": "ORIGINAL_RESEARCH_CANDIDATE",
                "reason": "Title-only screening result.",
                "tags": ["title-only"],
            }
            for record in records
        ],
    }


def batch_envelope(
    source: list[dict[str, object]],
    *,
    snapshot_hash: str,
    batch_number: int,
    start: int,
) -> dict[str, object]:
    prompt = screen.build_prompt(source)
    contract = {
        "source_records_sha256": snapshot_hash,
        "batch_number": batch_number,
        "start": start,
        "end": start + len(source),
        "source_count": len(source),
        "source_sha256": sha256_json(source),
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "schema_sha256": sha256_bytes(SCHEMA_PATH.read_bytes()),
        "model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
    }
    metadata = {
        "model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
        "invoked_at": "2026-08-02T00:00:00+00:00",
        "attempt_count": 1,
        "transient_failure_count": 0,
        "prompt_sha256": contract["prompt_sha256"],
        "schema_sha256": contract["schema_sha256"],
        "stdout_tail": "",
        "stderr_warnings_present": False,
        **contract,
    }
    return {"batch": contract, "result": screening_result(source), "metadata": metadata}


def fake_run_luna(prompt: str, schema: Path, _workspace: Path) -> dict[str, object]:
    compact = json.loads(prompt.split("INPUT_RECORDS:\n", 1)[1])
    return {
        "result": screening_result(compact),
        "metadata": {
            "model": MODEL_ID,
            "reasoning_effort": REASONING_EFFORT,
            "invoked_at": "2026-08-02T00:00:00+00:00",
            "attempt_count": 1,
            "transient_failure_count": 0,
            "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
            "schema_sha256": sha256_bytes(schema.read_bytes()),
            "stdout_tail": "",
            "stderr_warnings_present": False,
        },
    }


class ScreenResumeTests(unittest.TestCase):
    def run_screen(
        self,
        snapshot_path: Path,
        output_path: Path,
        workspace: Path,
        *,
        resume: bool = False,
        batch_size: int | None = None,
        run_luna=fake_run_luna,
    ) -> int:
        argv = [
            "screen.py",
            "--snapshot",
            str(snapshot_path),
            "--output",
            str(output_path),
            "--workspace",
            str(workspace),
        ]
        if resume:
            argv.append("--resume")
        if batch_size is not None:
            argv.extend(["--batch-size", str(batch_size)])
        with patch.object(sys, "argv", argv), patch.object(
            screen, "run_luna", side_effect=run_luna
        ) as mocked_run:
            self.last_run_luna = mocked_run
            exit_code = screen.main()
        return exit_code

    def test_default_batch_size_is_fifty(self) -> None:
        self.assertEqual(screen.DEFAULT_BATCH_SIZE, 50)

    def test_valid_batch_is_recovered_without_calling_luna(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            records = [source_record(index) for index in range(3)]
            snapshot = source_snapshot(records)
            snapshot_path = root / "snapshot.json"
            output_path = root / "screen.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            batch_path = root / "screen_batches" / "batch_001.json"
            batch_path.parent.mkdir()
            batch_path.write_text(
                json.dumps(
                    batch_envelope(
                        records,
                        snapshot_hash=snapshot["records_sha256"],
                        batch_number=1,
                        start=0,
                    )
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                self.run_screen(snapshot_path, output_path, root, resume=True, batch_size=50),
                0,
            )
            self.assertEqual(self.last_run_luna.call_count, 0)
            output = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [record["doi"] for record in output["records"]],
                [record["doi"] for record in records],
            )

    def test_existing_batch_with_contract_mismatch_is_rejected(self) -> None:
        mismatch_fields = (
            "source_records_sha256",
            "source_sha256",
            "prompt_sha256",
            "schema_sha256",
            "batch_number",
            "start",
            "end",
            "model",
            "reasoning_effort",
        )
        for field in mismatch_fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary_dir:
                root = Path(temporary_dir)
                records = [source_record(index) for index in range(2)]
                snapshot = source_snapshot(records)
                snapshot_path = root / "snapshot.json"
                output_path = root / "screen.json"
                snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
                envelope = batch_envelope(
                    records,
                    snapshot_hash=snapshot["records_sha256"],
                    batch_number=1,
                    start=0,
                )
                envelope["batch"][field] = "mismatch" if field not in {"batch_number", "start", "end"} else 999
                envelope["metadata"][field] = envelope["batch"][field]
                batch_path = root / "screen_batches" / "batch_001.json"
                batch_path.parent.mkdir()
                batch_path.write_text(json.dumps(envelope), encoding="utf-8")

                with self.assertRaises(ValueError):
                    self.run_screen(snapshot_path, output_path, root, resume=True, batch_size=50)
                self.assertEqual(self.last_run_luna.call_count, 0)

    def test_existing_batch_with_result_order_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            records = [source_record(index) for index in range(2)]
            snapshot = source_snapshot(records)
            snapshot_path = root / "snapshot.json"
            output_path = root / "screen.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            envelope = batch_envelope(
                records,
                snapshot_hash=snapshot["records_sha256"],
                batch_number=1,
                start=0,
            )
            result_records = envelope["result"]["records"]
            result_records[0]["doi"], result_records[1]["doi"] = (
                result_records[1]["doi"],
                result_records[0]["doi"],
            )
            batch_path = root / "screen_batches" / "batch_001.json"
            batch_path.parent.mkdir()
            batch_path.write_text(json.dumps(envelope), encoding="utf-8")

            with self.assertRaises(ValueError):
                self.run_screen(snapshot_path, output_path, root, resume=True, batch_size=50)
            self.assertEqual(self.last_run_luna.call_count, 0)

    def test_audit_metadata_contract_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            records = [source_record(index) for index in range(2)]
            snapshot = source_snapshot(records)
            snapshot_path = root / "snapshot.json"
            output_path = root / "screen.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            envelope = batch_envelope(
                records,
                snapshot_hash=snapshot["records_sha256"],
                batch_number=1,
                start=0,
            )
            envelope["metadata"]["source_count"] = True
            batch_path = root / "screen_batches" / "batch_001.json"
            batch_path.parent.mkdir()
            batch_path.write_text(json.dumps(envelope), encoding="utf-8")

            with self.assertRaises(ValueError):
                self.run_screen(snapshot_path, output_path, root, resume=True, batch_size=50)
            self.assertEqual(self.last_run_luna.call_count, 0)

    def test_corrupt_or_structurally_invalid_batch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            records = [source_record(index) for index in range(2)]
            snapshot = source_snapshot(records)
            snapshot_path = root / "snapshot.json"
            output_path = root / "screen.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            batch_path = root / "screen_batches" / "batch_001.json"
            batch_path.parent.mkdir()
            batch_path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                self.run_screen(snapshot_path, output_path, root, resume=True, batch_size=50)
            self.assertEqual(self.last_run_luna.call_count, 0)

            envelope = batch_envelope(
                records,
                snapshot_hash=snapshot["records_sha256"],
                batch_number=1,
                start=0,
            )
            del envelope["result"]["records"][0]["reason"]
            batch_path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.run_screen(snapshot_path, output_path, root, resume=True, batch_size=50)
            self.assertEqual(self.last_run_luna.call_count, 0)

    def test_default_batches_cover_1026_records_and_final_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            records = [source_record(index) for index in range(1026)]
            snapshot = source_snapshot(records)
            snapshot_path = root / "snapshot.json"
            output_path = root / "screen.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

            self.assertEqual(self.run_screen(snapshot_path, output_path, root), 0)
            self.assertEqual(self.last_run_luna.call_count, 21)
            batch_paths = sorted((root / "screen_batches").glob("batch_*.json"))
            self.assertEqual(
                [path.name for path in batch_paths],
                [f"batch_{index:03d}.json" for index in range(1, 22)],
            )
            batch_lengths = [
                len(json.loads(path.read_text(encoding="utf-8"))["result"]["records"])
                for path in batch_paths
            ]
            self.assertEqual(batch_lengths, [50] * 20 + [26])
            first_batch = json.loads(batch_paths[0].read_text(encoding="utf-8"))
            last_batch = json.loads(batch_paths[-1].read_text(encoding="utf-8"))
            self.assertEqual(first_batch["batch"]["start"], 0)
            self.assertEqual(first_batch["batch"]["end"], 50)
            self.assertEqual(last_batch["batch"]["start"], 1000)
            self.assertEqual(last_batch["batch"]["end"], 1026)
            self.assertEqual(
                first_batch["batch"]["source_records_sha256"],
                snapshot["records_sha256"],
            )
            for field in screen.BATCH_CONTRACT_FIELDS:
                self.assertEqual(first_batch["metadata"][field], first_batch["batch"][field])
            output = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(output["summary"]["record_count"], 1026)
            self.assertEqual(
                [record["doi"] for record in output["records"]],
                [record["doi"] for record in records],
            )

    def test_complete_screen_validation_rejects_duplicate_or_missing_dois(self) -> None:
        source = [source_record(index) for index in range(3)]
        valid = screening_result(source)["records"]
        screen.validate_complete_screen(source, valid)
        with self.assertRaises(ValueError):
            screen.validate_complete_screen(source, [valid[0], valid[0], valid[2]])
        with self.assertRaises(ValueError):
            screen.validate_complete_screen(source, [valid[0], valid[2]])


if __name__ == "__main__":
    unittest.main()
