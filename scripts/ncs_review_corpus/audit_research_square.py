#!/usr/bin/env python3
"""Audit public Research Square metadata candidates for frozen NCS records."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .core import sha256_bytes, utc_now, write_json
from .research_square import match_research_square_metadata


def _query_filename(doi: str) -> str:
    return re.sub(r"[/.]", "_", doi.lower()) + ".json"


def _is_research_square(item: dict[str, Any]) -> bool:
    doi = str(item.get("DOI") or item.get("doi") or "").lower()
    publisher = str(item.get("publisher") or "").lower()
    url = str(item.get("URL") or item.get("url") or "")
    host = (urlsplit(url).hostname or "").lower()
    return (
        doi.startswith("10.21203/")
        or "research square" in publisher
        or host == "researchsquare.com"
        or host.endswith(".researchsquare.com")
    )


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def audit(
    extraction_index_path: Path,
    ncs_snapshot_path: Path,
    query_directory: Path,
    output_path: Path,
) -> dict[str, Any]:
    extraction_index = _load_object(extraction_index_path)
    ncs_snapshot = _load_object(ncs_snapshot_path)
    target_by_doi = {
        record["doi"].lower(): record for record in ncs_snapshot.get("records", [])
    }
    records: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()
    expected_queries: set[str] = set()

    calibration_records = extraction_index.get("records", [])
    if len(calibration_records) != 6:
        raise ValueError(f"Expected six calibration records, got {len(calibration_records)}")
    for calibration in calibration_records:
        doi = calibration["doi"].lower()
        target = target_by_doi.get(doi)
        if target is None:
            raise ValueError(f"NCS Crossref snapshot is missing calibration DOI: {doi}")
        query_name = _query_filename(doi)
        expected_queries.add(query_name)
        query_path = query_directory / query_name
        raw_response = query_path.read_bytes()
        response = json.loads(raw_response)
        items = response.get("message", {}).get("items", [])
        if not isinstance(items, list):
            raise ValueError(f"Crossref response has no item array: {query_path}")
        candidates = [item for item in items if isinstance(item, dict) and _is_research_square(item)]
        result = match_research_square_metadata(
            target,
            candidates,
            response_bytes=raw_response,
            source="Crossref",
        )
        statuses[result["status"]] += 1
        records.append(
            {
                "calibration_id": calibration["calibration_id"],
                "ncs_doi": doi,
                "ncs_title": target.get("title"),
                "query_file": str(query_path),
                "query_response_sha256": sha256_bytes(raw_response),
                "crossref_total_results": response.get("message", {}).get("total-results"),
                "crossref_returned_items": len(items),
                "research_square_candidate_count": len(candidates),
                "match": result,
            }
        )

    actual_queries = {path.name for path in query_directory.glob("*.json")}
    if actual_queries != expected_queries:
        raise ValueError(
            f"Unexpected query file set; missing={sorted(expected_queries - actual_queries)}, "
            f"unexpected={sorted(actual_queries - expected_queries)}"
        )
    audit_result = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "scope": "SIX_FROZEN_NCS_CALIBRATION_RECORDS",
        "method": "CROSSREF_POSTED_CONTENT_METADATA_ONLY",
        "restrictions": {
            "research_square_api_accessed": False,
            "research_square_html_accessed": False,
            "research_square_pdf_or_full_text_accessed": False,
        },
        "summary": {
            "record_count": len(records),
            "status_counts": dict(sorted(statuses.items())),
        },
        "records": records,
    }
    write_json(output_path, audit_result)
    return audit_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction-index", required=True, type=Path)
    parser.add_argument("--ncs-snapshot", required=True, type=Path)
    parser.add_argument("--query-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = audit(
        extraction_index_path=args.extraction_index,
        ncs_snapshot_path=args.ncs_snapshot,
        query_directory=args.query_directory,
        output_path=args.output,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
