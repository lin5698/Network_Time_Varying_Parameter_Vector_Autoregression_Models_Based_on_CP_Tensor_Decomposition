#!/usr/bin/env python3
"""Survey official Nature pages for candidate material availability."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .core import SCHEMA_VERSION, normalize_doi, utc_now, write_json
from .nature import discover_materials


def resolve_source_snapshot(source: str, input_path: Path, cwd: Path | None = None) -> Path:
    """Resolve recorded snapshot paths while preserving older input-relative exports."""
    snapshot_path = Path(source)
    if snapshot_path.is_absolute():
        return snapshot_path
    workspace_candidate = ((cwd or Path.cwd()) / snapshot_path).resolve()
    if workspace_candidate.exists():
        return workspace_candidate
    return (input_path.parent / snapshot_path).resolve()


def select_records(payload: dict[str, Any], input_path: Path, levels: set[str]) -> list[dict[str, Any]]:
    records = payload["records"]
    if not records or "relatedness_level" not in records[0]:
        return records
    if "source_snapshot" not in payload:
        raise ValueError("Screened records require source_snapshot for official URLs")
    snapshot_path = resolve_source_snapshot(payload["source_snapshot"], input_path)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    metadata_by_doi = {record["doi"]: record for record in snapshot["records"]}
    return [
        metadata_by_doi[record["doi"]]
        for record in records
        if record["relatedness_level"] in levels and record["doi"] in metadata_by_doi
    ]


def survey(record: dict[str, Any], timeout: float) -> dict[str, Any]:
    try:
        discovery = discover_materials(record["official_url"], timeout)
        return {
            "doi": normalize_doi(record["doi"]),
            "title": record["title"],
            "official_url": record["official_url"],
            "status": "OK",
            "metadata": discovery["metadata"],
            "retrieved_at": discovery["retrieved_at"],
            "page_sha256": discovery["raw_sha256"],
            "materials": discovery["materials"],
            "material_kinds": sorted({item["kind"] for item in discovery["materials"]}),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - retained as auditable access state
        return {
            "doi": normalize_doi(record["doi"]),
            "title": record["title"],
            "official_url": record["official_url"],
            "status": "ERROR",
            "metadata": {},
            "retrieved_at": utc_now(),
            "page_sha256": None,
            "materials": [],
            "material_kinds": [],
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--levels", default="A,B,C")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    levels = {level.strip() for level in args.levels.split(",") if level.strip()}
    selected = select_records(payload, args.input, levels)
    if args.limit:
        selected = selected[: args.limit]
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(survey, record, args.timeout) for record in selected]
        for index, future in enumerate(futures, start=1):
            record = future.result()
            records.append(record)
            print(f"[{index}/{len(futures)}] {record['doi']}: {record['status']}", flush=True)
    records.sort(key=lambda record: record["doi"])
    status_counts = Counter(record["status"] for record in records)
    kind_counts = Counter(kind for record in records for kind in record["material_kinds"])
    output = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "source": str(args.input),
        "selected_levels": sorted(levels),
        "summary": {
            "candidate_count": len(records),
            "status_counts": dict(sorted(status_counts.items())),
            "material_kind_counts": dict(sorted(kind_counts.items())),
            "peer_review_file_count": sum(
                "PEER_REVIEW_FILE" in record["material_kinds"] for record in records
            ),
        },
        "records": records,
    }
    write_json(args.output, output)
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
