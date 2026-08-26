#!/usr/bin/env python3
"""Extract archived calibration documents into stable evidence locations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import sha256_json, write_json
from .extract import extract_html, extract_pdf, ocr_textless_pdf_pages


DOCUMENT_PREFIXES = {
    "ARTICLE_PDF": "ART",
    "PEER_REVIEW_FILE": "PR",
    "REPORTING_SUMMARY": "RS",
    "SUPPLEMENTARY_INFORMATION": "SUPP",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--ocr-dpi", type=int, default=250)
    return parser.parse_args()


def extract_article(
    article_directory: Path, calibration_id: str, run_ocr: bool = False, ocr_dpi: int = 250
) -> dict[str, Any]:
    manifest = json.loads((article_directory / "manifest.json").read_text(encoding="utf-8"))
    documents: list[dict[str, Any]] = []
    access_artifacts: list[dict[str, Any]] = []
    landing = article_directory / manifest["landing_page"]["file"]
    documents.append(extract_html(landing, f"{calibration_id}-HTML", "ARTICLE_HTML"))
    kind_counts: dict[str, int] = {}
    for material in manifest["materials"]:
        kind = material["kind"]
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        suffix = "" if kind_counts[kind] == 1 else f"-{kind_counts[kind]:02d}"
        document_id = f"{calibration_id}-{DOCUMENT_PREFIXES[kind]}{suffix}"
        path = article_directory / material["file"]
        if not material["is_pdf"]:
            if kind != "ARTICLE_PDF":
                raise ValueError(f"Expected archived calibration material to be PDF: {path}")
            access_artifacts.append(
                {
                    "kind": kind,
                    "source_file": path.name,
                    "source_sha256": material["sha256"],
                    "status": "ACCESS_ENDPOINT_RETURNED_HTML",
                    "content_type": material.get("content_type"),
                    "final_url": material.get("final_url"),
                }
            )
            continue
        document = extract_pdf(path, document_id, kind)
        if run_ocr:
            document = ocr_textless_pdf_pages(path, document, ocr_dpi)
        documents.append(document)
    return {
        "schema_version": "1.0",
        "calibration_id": calibration_id,
        "doi": manifest["metadata"]["doi"].lower(),
        "source_directory": article_directory.name,
        "documents": documents,
        "access_artifacts": access_artifacts,
        "document_count": len(documents),
        "ocr_required_documents": [
            document["document_id"]
            for document in documents
            if document.get("textless_pages")
        ],
        "documents_sha256": sha256_json(documents),
    }


def main() -> int:
    args = parse_args()
    index = json.loads((args.archive / "archive_index.json").read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    for number, source in enumerate(index["records"], start=1):
        record = extract_article(
            args.archive / str(source["directory"]),
            str(source["calibration_id"]),
            args.ocr,
            args.ocr_dpi,
        )
        output_path = args.output / f"{record['calibration_id'].lower()}_documents.json"
        write_json(output_path, record)
        records.append(
            {
                "calibration_id": record["calibration_id"],
                "doi": record["doi"],
                "file": output_path.name,
                "document_count": record["document_count"],
                "ocr_required_documents": record["ocr_required_documents"],
                "documents_sha256": record["documents_sha256"],
            }
        )
        print(
            f"[{number}/{len(index['records'])}] {record['calibration_id']}: "
            f"{record['document_count']} documents",
            flush=True,
        )
    write_json(
        args.output / "extraction_index.json",
        {"schema_version": "1.0", "source_archive": str(args.archive), "records": records},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
