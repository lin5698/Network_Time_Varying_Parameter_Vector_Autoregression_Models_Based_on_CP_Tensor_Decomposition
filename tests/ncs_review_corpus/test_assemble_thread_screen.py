from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.ncs_review_corpus.assemble_thread_screen import assemble_thread_screen
from scripts.ncs_review_corpus.core import MODEL_ID, REASONING_EFFORT, sha256_json


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "scripts/ncs_review_corpus/schemas/screen_batch.schema.json"


def source_record(index: int) -> dict:
    return {"doi": f"10.1038/example-{index}", "title": f"Example {index}", "publication_date": "2026-01-01"}


def result_record(record: dict) -> dict:
    return {
        "doi": record["doi"],
        "relatedness_level": "A",
        "document_kind": "ORIGINAL_RESEARCH_CANDIDATE",
        "reason": "The title explicitly concerns a relevant network method.",
        "tags": ["network"],
    }


class ThreadScreenAssemblyTests(unittest.TestCase):
    def write_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        records = [source_record(index) for index in range(5)]
        snapshot = {"records": records, "records_sha256": sha256_json(records)}
        snapshot_path = root / "snapshot.json"
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
        raw_dir = root / "raw"
        raw_dir.mkdir()
        for batch_number, start in enumerate(range(0, len(records), 2), start=1):
            payload = {
                "schema_version": "1.0",
                "records": [result_record(record) for record in records[start : start + 2]],
            }
            (raw_dir / f"batch_{batch_number:03d}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
        provenance_path = root / "provenance.json"
        provenance_path.write_text(
            json.dumps(
                {
                    "batches": [
                        {
                            "batch_number": number,
                            "thread_id": f"thread-{number}",
                            "model": MODEL_ID,
                            "reasoning_effort": REASONING_EFFORT,
                        }
                        for number in range(1, 4)
                    ]
                }
            ),
            encoding="utf-8",
        )
        return snapshot_path, raw_dir, provenance_path

    def test_valid_thread_batches_assemble_with_explicit_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            snapshot, raw_dir, provenance = self.write_fixture(root)
            output = assemble_thread_screen(
                snapshot, raw_dir, provenance, root / "screen.json", SCHEMA, batch_size=2
            )
            self.assertEqual(output["summary"]["record_count"], 5)
            self.assertEqual(output["semantic_execution_route"], "CODEX_THREADS")
            self.assertEqual(output["batches"][2]["source_count"], 1)
            self.assertEqual(output["batches"][0]["thread_id"], "thread-1")

    def test_non_luna_provenance_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            snapshot, raw_dir, provenance = self.write_fixture(root)
            payload = json.loads(provenance.read_text(encoding="utf-8"))
            payload["batches"][0]["model"] = "other-model"
            provenance.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                assemble_thread_screen(
                    snapshot, raw_dir, provenance, root / "screen.json", SCHEMA, batch_size=2
                )

    def test_missing_or_extra_batch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            snapshot, raw_dir, provenance = self.write_fixture(root)
            (raw_dir / "batch_002.json").unlink()
            with self.assertRaises(ValueError):
                assemble_thread_screen(
                    snapshot, raw_dir, provenance, root / "screen.json", SCHEMA, batch_size=2
                )


if __name__ == "__main__":
    unittest.main()
