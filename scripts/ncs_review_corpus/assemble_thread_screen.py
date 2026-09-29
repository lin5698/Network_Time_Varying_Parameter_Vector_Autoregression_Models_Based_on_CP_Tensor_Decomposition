#!/usr/bin/env python3
"""Assemble Luna Max thread-authored screening batches with strict provenance."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .core import (
    MODEL_ID,
    REASONING_EFFORT,
    SCHEMA_VERSION,
    sha256_bytes,
    sha256_file,
    sha256_json,
    utc_now,
    write_json,
)
from .screen import (
    DEFAULT_BATCH_SIZE,
    build_batch_contract,
    build_prompt,
    validate_batch,
    validate_batch_envelope,
    validate_complete_screen,
    validate_source_snapshot,
)


def expected_batch_names(record_count: int, batch_size: int) -> list[str]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    return [
        f"batch_{batch_number:03d}.json"
        for batch_number, _ in enumerate(range(0, record_count, batch_size), start=1)
    ]


def _validate_exact_file_set(raw_dir: Path, expected: list[str]) -> None:
    actual = sorted(path.name for path in raw_dir.glob("batch_*.json"))
    if actual != expected:
        raise ValueError(
            f"Thread batch file set mismatch; expected={expected}, actual={actual}"
        )


def _provenance_by_batch(
    provenance: dict[str, Any], expected_count: int
) -> dict[int, dict[str, Any]]:
    records = provenance.get("batches")
    if not isinstance(records, list):
        raise ValueError("Thread provenance must contain a batches array")
    result: dict[int, dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Thread provenance batch must be an object")
        batch_number = item.get("batch_number")
        if type(batch_number) is not int or not 1 <= batch_number <= expected_count:
            raise ValueError("Thread provenance has an invalid batch_number")
        if batch_number in result:
            raise ValueError(f"Duplicate thread provenance for batch {batch_number}")
        if item.get("model") != MODEL_ID or item.get("reasoning_effort") != REASONING_EFFORT:
            raise ValueError(f"Batch {batch_number} is not provenanced to Luna Max")
        thread_id = item.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            raise ValueError(f"Batch {batch_number} has no thread_id")
        result[batch_number] = item
    if set(result) != set(range(1, expected_count + 1)):
        raise ValueError("Thread provenance does not cover every expected batch")
    return result


def assemble_thread_screen(
    snapshot_path: Path,
    raw_dir: Path,
    provenance_path: Path,
    output_path: Path,
    schema_path: Path,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    source_records_sha256 = validate_source_snapshot(snapshot)
    records = snapshot["records"]
    names = expected_batch_names(len(records), batch_size)
    _validate_exact_file_set(raw_dir, names)
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance_map = _provenance_by_batch(provenance, len(names))
    batch_dir = output_path.parent / "screen_batches"
    screened: list[dict[str, Any]] = []
    batch_metadata: list[dict[str, Any]] = []

    for batch_number, start in enumerate(range(0, len(records), batch_size), start=1):
        source = records[start : start + batch_size]
        raw_path = raw_dir / f"batch_{batch_number:03d}.json"
        result = json.loads(raw_path.read_text(encoding="utf-8"))
        validate_batch(source, result)
        prompt = build_prompt(source)
        contract = build_batch_contract(
            source_records_sha256,
            batch_number,
            start,
            source,
            prompt,
            schema_path,
        )
        receipt = provenance_map[batch_number]
        metadata = {
            **contract,
            "semantic_executor": "CODEX_THREAD",
            "thread_id": receipt["thread_id"],
            "invoked_at": receipt.get("completed_at") or provenance.get("assembled_at") or utc_now(),
            "attempt_count": 1,
            "transient_failure_count": 0,
            "stdout_tail": "",
            "stderr_warnings_present": False,
            "raw_result_sha256": sha256_file(raw_path),
        }
        envelope = {"batch": contract, "result": result, "metadata": metadata}
        validate_batch_envelope(
            envelope,
            source,
            source_records_sha256,
            batch_number,
            start,
            prompt,
            schema_path,
        )
        batch_path = batch_dir / raw_path.name
        write_json(batch_path, envelope)
        screened.extend(result["records"])
        batch_metadata.append(
            {
                **contract,
                "file": str(batch_path),
                "semantic_executor": "CODEX_THREAD",
                "thread_id": receipt["thread_id"],
                "raw_result_sha256": metadata["raw_result_sha256"],
            }
        )

    validate_complete_screen(records, screened)
    counts = Counter(record["relatedness_level"] for record in screened)
    output = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "source_snapshot": str(snapshot_path),
        "source_records_sha256": source_records_sha256,
        "model_contract": {"model": MODEL_ID, "reasoning_effort": REASONING_EFFORT},
        "semantic_execution_route": "CODEX_THREADS",
        "screen_stage": "TITLE_ONLY_HIGH_RECALL",
        "limitations": [
            "This stage uses title, DOI, and date only.",
            "Levels are provisional until official article type and abstract/full text are checked.",
            "No frequency or journal-wide editorial inference may be made from these labels.",
            "Batches were independently authored in explicitly configured Luna Max Codex threads.",
        ],
        "summary": {
            "record_count": len(screened),
            "level_counts": dict(sorted(counts.items())),
        },
        "batches": batch_metadata,
        "records": screened,
        "audit": {
            "raw_directory": str(raw_dir),
            "raw_directory_sha256": sha256_json(
                {name: sha256_file(raw_dir / name) for name in names}
            ),
            "provenance_file": str(provenance_path),
            "provenance_sha256": sha256_file(provenance_path),
            "schema_sha256": sha256_bytes(schema_path.read_bytes()),
        },
    }
    write_json(output_path, output)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = assemble_thread_screen(
        args.snapshot,
        args.raw_dir,
        args.provenance,
        args.output,
        args.schema,
        args.batch_size,
    )
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
