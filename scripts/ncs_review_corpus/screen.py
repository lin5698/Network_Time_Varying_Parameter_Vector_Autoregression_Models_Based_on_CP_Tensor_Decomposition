#!/usr/bin/env python3
"""Classify the complete NCS title inventory with Luna Max in auditable batches."""

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
    sha256_json,
    utc_now,
    write_json,
)
from .luna import run_luna


SYSTEM_RULES = """You are screening the complete Nature Computational Science title inventory for a review-corpus study. Use only each supplied title and DOI. Do not use tools, web search, memory about paper contents, or hidden assumptions. This is a high-recall first-stage screen; uncertainty should move a record upward, not downward.

Assign exactly one relatedness level:
A direct: dynamic/time-varying/temporal networks; network dynamics or reconstruction; graph-structure operators or queries; VAR/response analysis; tensor/low-rank methods when used for dynamic systems or networks.
B method: operator learning; identifiability; uncertainty; OOD/reliability; reconstruction; statistical inference; benchmarking; scaling when the title plausibly concerns a reusable computational method relevant to evaluating a network/time-varying method.
C evidence architecture: large-scale computational resources, fair comparison infrastructure, reproducibility, computational efficiency, or broad cross-domain validation that can teach evidence standards even without technical proximity.
D background: outside A-C, commentary/news/editorial without direct normative value, or unrelated domain work.

Document kind is title-only and provisional. Mark corrections/retractions explicitly. Editorials, comments, perspectives, primers, or news-like titles are NORMATIVE_BACKGROUND only when they plausibly state a journal norm relevant to A-C; otherwise OTHER. Keep each reason factual and explicitly title-based. Return one and only one record for every supplied DOI in the original order."""


DEFAULT_BATCH_SIZE = 50
BATCH_CONTRACT_FIELDS = {
    "source_records_sha256",
    "batch_number",
    "start",
    "end",
    "source_count",
    "source_sha256",
    "prompt_sha256",
    "schema_sha256",
    "model",
    "reasoning_effort",
}
RESULT_FIELDS = {"schema_version", "records"}
SCREEN_RECORD_FIELDS = {
    "doi",
    "relatedness_level",
    "document_kind",
    "reason",
    "tags",
}
RUN_LUNA_METADATA_FIELDS = {
    "model",
    "reasoning_effort",
    "invoked_at",
    "attempt_count",
    "transient_failure_count",
    "prompt_sha256",
    "schema_sha256",
    "stdout_tail",
    "stderr_warnings_present",
}
ENVELOPE_FIELDS = {"batch", "result", "metadata"}


def build_prompt(records: list[dict[str, Any]]) -> str:
    compact = [
        {
            "doi": record["doi"],
            "title": record["title"],
            "publication_date": record.get("publication_date"),
        }
        for record in records
    ]
    return SYSTEM_RULES + "\n\nINPUT_RECORDS:\n" + json.dumps(compact, ensure_ascii=False)


def _source_dois(source: list[dict[str, Any]]) -> list[str]:
    if not isinstance(source, list):
        raise ValueError("Source records must be a JSON array")
    dois: list[str] = []
    for index, record in enumerate(source):
        if not isinstance(record, dict):
            raise ValueError(f"Source record {index} must be a JSON object")
        doi = record.get("doi")
        if not isinstance(doi, str) or not doi:
            raise ValueError(f"Source record {index} has an invalid DOI")
        title = record.get("title")
        if not isinstance(title, str):
            raise ValueError(f"Source record {index} has an invalid title")
        dois.append(doi)
    if len(dois) != len(set(dois)):
        raise ValueError("Source snapshot contains duplicate DOIs")
    return dois


def validate_source_snapshot(snapshot: dict[str, Any]) -> str:
    if not isinstance(snapshot, dict):
        raise ValueError("Source snapshot must be a JSON object")
    records = snapshot.get("records")
    records_sha256 = snapshot.get("records_sha256")
    if not isinstance(records_sha256, str) or not records_sha256:
        raise ValueError("Source snapshot is missing records_sha256")
    _source_dois(records)
    actual_sha256 = sha256_json(records)
    if records_sha256 != actual_sha256:
        raise ValueError(
            "Source snapshot records_sha256 mismatch; refusing to screen or resume"
        )
    return records_sha256


def _validate_screen_record(record: Any, index: int) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"Screened record {index} must be a JSON object")
    if set(record) != SCREEN_RECORD_FIELDS:
        raise ValueError(f"Screened record {index} has an invalid JSON structure")
    if not isinstance(record["doi"], str) or not record["doi"]:
        raise ValueError(f"Screened record {index} has an invalid DOI")
    if record["relatedness_level"] not in {"A", "B", "C", "D"}:
        raise ValueError(f"Screened record {index} has an invalid relatedness level")
    if record["document_kind"] not in {
        "ORIGINAL_RESEARCH_CANDIDATE",
        "NORMATIVE_BACKGROUND",
        "CORRECTION_OR_RETRACTION",
        "OTHER",
    }:
        raise ValueError(f"Screened record {index} has an invalid document kind")
    reason = record["reason"]
    if not isinstance(reason, str) or not 0 < len(reason) <= 260:
        raise ValueError(f"Screened record {index} has an invalid reason")
    tags = record["tags"]
    if not isinstance(tags, list) or len(tags) > 6:
        raise ValueError(f"Screened record {index} has invalid tags")
    if any(not isinstance(tag, str) or not 0 < len(tag) <= 60 for tag in tags):
        raise ValueError(f"Screened record {index} has invalid tags")


def _validate_result_records(result: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(result, dict) or set(result) != RESULT_FIELDS:
        raise ValueError("Screening result has an invalid JSON structure")
    if result["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Screening result schema_version mismatch")
    records = result["records"]
    if not isinstance(records, list):
        raise ValueError("Screening result records must be a JSON array")
    for index, record in enumerate(records):
        _validate_screen_record(record, index)
    return records


def build_batch_contract(
    source_records_sha256: str,
    batch_number: int,
    start: int,
    source: list[dict[str, Any]],
    prompt: str,
    schema: Path,
) -> dict[str, Any]:
    return {
        "source_records_sha256": source_records_sha256,
        "batch_number": batch_number,
        "start": start,
        "end": start + len(source),
        "source_count": len(source),
        "source_sha256": sha256_json(source),
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "schema_sha256": sha256_bytes(schema.read_bytes()),
        "model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
    }


def validate_batch(source: list[dict[str, Any]], result: dict[str, Any]) -> None:
    expected_dois = _source_dois(source)
    returned = _validate_result_records(result)
    returned_dois = [record["doi"] for record in returned]
    if returned_dois != expected_dois:
        raise ValueError(
            "Luna screening DOI/order mismatch; expected "
            f"{len(expected_dois)} records and received {len(returned_dois)}"
        )


def validate_complete_screen(
    source: list[dict[str, Any]], screened: list[dict[str, Any]]
) -> None:
    expected_dois = _source_dois(source)
    if not isinstance(screened, list):
        raise ValueError("Complete screening result must be a JSON array")
    for index, record in enumerate(screened):
        _validate_screen_record(record, index)
    returned_dois = [record["doi"] for record in screened]
    if len(returned_dois) != len(set(returned_dois)):
        raise ValueError("Complete screening result contains duplicate DOIs")
    if returned_dois != expected_dois:
        raise ValueError(
            "Complete screening DOI sequence mismatch; expected "
            f"{len(expected_dois)} records and received {len(returned_dois)}"
        )


def _validate_contract_types(contract: dict[str, Any]) -> None:
    integer_fields = {"batch_number", "start", "end", "source_count"}
    if any(type(contract[field]) is not int for field in integer_fields):
        raise ValueError("Batch contract contains a non-integer index or count")
    if contract["batch_number"] < 1:
        raise ValueError("Batch contract batch_number must be positive")
    if contract["start"] < 0 or contract["end"] < contract["start"]:
        raise ValueError("Batch contract has invalid start/end indices")
    if contract["source_count"] != contract["end"] - contract["start"]:
        raise ValueError("Batch contract source_count does not match start/end")
    for field in BATCH_CONTRACT_FIELDS - integer_fields:
        if not isinstance(contract[field], str) or not contract[field]:
            raise ValueError(f"Batch contract field {field} must be a non-empty string")


def _validate_run_luna_metadata(metadata: dict[str, Any]) -> None:
    missing = RUN_LUNA_METADATA_FIELDS - set(metadata)
    if missing:
        raise ValueError(
            "Batch metadata is missing run_luna audit fields: "
            + ", ".join(sorted(missing))
        )
    if not isinstance(metadata["invoked_at"], str) or not metadata["invoked_at"]:
        raise ValueError("Batch metadata invoked_at is invalid")
    if type(metadata["attempt_count"]) is not int or metadata["attempt_count"] < 1:
        raise ValueError("Batch metadata attempt_count is invalid")
    if (
        type(metadata["transient_failure_count"]) is not int
        or metadata["transient_failure_count"] < 0
    ):
        raise ValueError("Batch metadata transient_failure_count is invalid")
    if not isinstance(metadata["stdout_tail"], str):
        raise ValueError("Batch metadata stdout_tail is invalid")
    if type(metadata["stderr_warnings_present"]) is not bool:
        raise ValueError("Batch metadata stderr_warnings_present is invalid")


def validate_batch_envelope(
    envelope: dict[str, Any],
    source: list[dict[str, Any]],
    source_records_sha256: str,
    batch_number: int,
    start: int,
    prompt: str,
    schema: Path,
) -> None:
    if not isinstance(envelope, dict) or set(envelope) != ENVELOPE_FIELDS:
        raise ValueError("Batch file has an invalid JSON envelope structure")
    expected_contract = build_batch_contract(
        source_records_sha256,
        batch_number,
        start,
        source,
        prompt,
        schema,
    )
    contract = envelope["batch"]
    if not isinstance(contract, dict) or set(contract) != BATCH_CONTRACT_FIELDS:
        raise ValueError("Batch file is missing the complete batch contract")
    _validate_contract_types(contract)
    if contract != expected_contract:
        mismatches = [
            field
            for field in sorted(BATCH_CONTRACT_FIELDS)
            if contract.get(field) != expected_contract[field]
        ]
        raise ValueError("Batch contract mismatch: " + ", ".join(mismatches))
    metadata = envelope["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError("Batch metadata must be a JSON object")
    _validate_run_luna_metadata(metadata)
    for field in BATCH_CONTRACT_FIELDS:
        if (
            type(metadata.get(field)) is not type(expected_contract[field])
            or metadata.get(field) != expected_contract[field]
        ):
            raise ValueError(f"Batch metadata contract mismatch: {field}")
    validate_batch(source, envelope["result"])


def _enrich_new_batch(
    envelope: dict[str, Any], contract: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(envelope, dict) or set(envelope) != {"result", "metadata"}:
        raise ValueError("run_luna returned an invalid batch envelope")
    metadata = envelope["metadata"]
    if not isinstance(metadata, dict):
        raise ValueError("run_luna returned invalid metadata")
    for field in ("model", "reasoning_effort", "prompt_sha256", "schema_sha256"):
        if metadata.get(field) != contract[field]:
            raise ValueError(f"run_luna metadata mismatch: {field}")
    enriched_metadata = dict(metadata)
    enriched_metadata.update(contract)
    return {
        "batch": contract,
        "result": envelope["result"],
        "metadata": enriched_metadata,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    source_records_sha256 = validate_source_snapshot(snapshot)
    records = snapshot["records"]
    if args.batch_size < 1:
        raise ValueError("--batch-size must be positive")
    schema = Path(__file__).parent / "schemas" / "screen_batch.schema.json"
    batch_dir = args.output.parent / "screen_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    screened: list[dict[str, Any]] = []
    batch_metadata: list[dict[str, Any]] = []
    for batch_number, start in enumerate(range(0, len(records), args.batch_size), start=1):
        source = records[start : start + args.batch_size]
        batch_path = batch_dir / f"batch_{batch_number:03d}.json"
        prompt = build_prompt(source)
        contract = build_batch_contract(
            source_records_sha256,
            batch_number,
            start,
            source,
            prompt,
            schema,
        )
        recovering = args.resume and batch_path.exists()
        if recovering:
            envelope = json.loads(batch_path.read_text(encoding="utf-8"))
        else:
            envelope = _enrich_new_batch(
                run_luna(prompt, schema, args.workspace),
                contract,
            )
        validate_batch_envelope(
            envelope,
            source,
            source_records_sha256,
            batch_number,
            start,
            prompt,
            schema,
        )
        if not recovering:
            write_json(batch_path, envelope)
        screened.extend(envelope["result"]["records"])
        batch_metadata.append(
            {
                "batch_number": batch_number,
                "start": start,
                "end": start + len(source),
                "source_count": len(source),
                "source_sha256": sha256_json(source),
                "source_records_sha256": source_records_sha256,
                "prompt_sha256": contract["prompt_sha256"],
                "schema_sha256": contract["schema_sha256"],
                "file": str(batch_path),
                "model": MODEL_ID,
                "reasoning_effort": REASONING_EFFORT,
            }
        )
        print(f"[{batch_number}] screened {len(screened)}/{len(records)}", flush=True)
    validate_complete_screen(records, screened)
    counts = Counter(record["relatedness_level"] for record in screened)
    output = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "source_snapshot": str(args.snapshot),
        "source_records_sha256": source_records_sha256,
        "model_contract": {"model": MODEL_ID, "reasoning_effort": REASONING_EFFORT},
        "screen_stage": "TITLE_ONLY_HIGH_RECALL",
        "limitations": [
            "This stage uses title, DOI, and date only.",
            "Levels are provisional until official article type and abstract/full text are checked.",
            "No frequency or journal-wide editorial inference may be made from these labels.",
        ],
        "summary": {"record_count": len(screened), "level_counts": dict(sorted(counts.items()))},
        "batches": batch_metadata,
        "records": screened,
    }
    write_json(args.output, output)
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
