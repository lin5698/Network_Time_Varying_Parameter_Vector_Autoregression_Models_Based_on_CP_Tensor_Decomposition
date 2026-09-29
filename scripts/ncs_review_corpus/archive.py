#!/usr/bin/env python3
"""Archive the frozen calibration corpus from official Nature endpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import doi_slug, write_json
from .nature import archive_article, discover_materials, validate_archived_article


REQUIRED_CALIBRATION_KINDS = {
    "ARTICLE_PDF",
    "PEER_REVIEW_FILE",
    "SUPPLEMENTARY_INFORMATION",
}
REQUIRED_PDF_KINDS = {"PEER_REVIEW_FILE", "SUPPLEMENTARY_INFORMATION"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    calibration = json.loads(args.manifest.read_text(encoding="utf-8"))
    archived: list[dict[str, object]] = []
    for index, record in enumerate(calibration["records"], start=1):
        article_url = f"https://www.nature.com/articles/{record['doi'].split('/')[-1]}"
        destination = args.destination / doi_slug(record["doi"])
        manifest_path = destination / "manifest.json"
        if manifest_path.exists():
            article_manifest = validate_archived_article(
                manifest_path,
                record["doi"],
                REQUIRED_CALIBRATION_KINDS,
                REQUIRED_PDF_KINDS,
            )
            source = "VALIDATED_EXISTING"
        else:
            discovery = discover_materials(article_url, args.timeout)
            article_manifest = archive_article(discovery, destination, args.timeout)
            validate_archived_article(
                manifest_path,
                record["doi"],
                REQUIRED_CALIBRATION_KINDS,
                REQUIRED_PDF_KINDS,
            )
            source = "DOWNLOADED"
        kinds = sorted({item["kind"] for item in article_manifest["materials"]})
        archived.append(
            {
                "calibration_id": record["calibration_id"],
                "doi": record["doi"],
                "directory": destination.name,
                "material_kinds": kinds,
                "material_count": len(article_manifest["materials"]),
                "archive_source": source,
                "article_fulltext_evidence": "ARTICLE_PDF"
                if any(
                    item["kind"] == "ARTICLE_PDF" and item.get("is_pdf")
                    for item in article_manifest["materials"]
                )
                else "OFFICIAL_FULLTEXT_HTML",
                "article_pdf_status": "AVAILABLE"
                if any(
                    item["kind"] == "ARTICLE_PDF" and item.get("is_pdf")
                    for item in article_manifest["materials"]
                )
                else "ACCESS_ENDPOINT_RETURNED_HTML",
            }
        )
        print(
            f"[{index}/{len(calibration['records'])}] {record['doi']} ({source}): "
            f"{', '.join(kinds)}",
            flush=True,
        )
    index = {
        "schema_version": "1.0",
        "source_manifest": str(args.manifest),
        "records": archived,
    }
    write_json(args.destination / "archive_index.json", index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
