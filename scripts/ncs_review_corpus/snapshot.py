#!/usr/bin/env python3
"""Create a versioned Crossref snapshot of Nature Computational Science."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .core import CORPUS_CUTOFF, SCHEMA_VERSION, normalize_doi, sha256_json, utc_now, write_json


CROSSREF_ENDPOINT = "https://api.crossref.org/journals/2662-8457/works"
DEFAULT_MAILTO = "research-corpus@example.invalid"


def _date_parts(value: dict[str, Any] | None) -> str | None:
    if not value or not value.get("date-parts"):
        return None
    parts = value["date-parts"][0]
    return "-".join(str(part).zfill(2) if index else str(part) for index, part in enumerate(parts))


def fetch_page(cursor: str, rows: int, mailto: str, timeout: float) -> dict[str, Any]:
    params = {
        "filter": f"from-pub-date:2021-01-01,until-pub-date:{CORPUS_CUTOFF},type:journal-article",
        "rows": rows,
        "cursor": cursor,
        "mailto": mailto,
        "select": ",".join(
            (
                "DOI",
                "title",
                "abstract",
                "published-online",
                "published-print",
                "published",
                "type",
                "URL",
                "author",
                "subject",
                "relation",
                "update-to",
                "updated-by",
                "license",
                "link",
                "publisher",
                "container-title",
            )
        ),
    }
    request = Request(
        f"{CROSSREF_ENDPOINT}?{urlencode(params)}",
        headers={
            "User-Agent": f"NCSReviewCorpus/1.0 (mailto:{mailto})",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    title_values = item.get("title") or []
    author_values = []
    for author in item.get("author") or []:
        author_values.append(
            {
                "family": author.get("family"),
                "given": author.get("given"),
                "orcid": author.get("ORCID"),
            }
        )
    publication_date = (
        _date_parts(item.get("published-online"))
        or _date_parts(item.get("published-print"))
        or _date_parts(item.get("published"))
    )
    doi = normalize_doi(item.get("DOI", ""))
    official_url = f"https://www.nature.com/articles/{doi.split('/')[-1]}" if doi else item.get("URL")
    return {
        "doi": doi,
        "title": title_values[0] if title_values else "",
        "abstract": item.get("abstract"),
        "publication_date": publication_date,
        "type": item.get("type"),
        "official_url": official_url,
        "crossref_url": item.get("URL"),
        "authors": author_values,
        "subjects": item.get("subject") or [],
        "container_title": (item.get("container-title") or [None])[0],
        "publisher": item.get("publisher"),
        "relations": item.get("relation") or {},
        "updates": {
            "update_to": item.get("update-to") or [],
            "updated_by": item.get("updated-by") or [],
        },
        "licenses": item.get("license") or [],
        "links": item.get("link") or [],
    }


def build_snapshot(rows: int, mailto: str, timeout: float, delay: float) -> dict[str, Any]:
    cursor = "*"
    items: list[dict[str, Any]] = []
    expected_total: int | None = None
    seen: set[str] = set()
    page_count = 0
    while True:
        payload = fetch_page(cursor, rows, mailto, timeout)
        message = payload["message"]
        expected_total = expected_total or int(message.get("total-results", 0))
        raw_items = message.get("items") or []
        page_count += 1
        before_count = len(items)
        for raw in raw_items:
            normalized = normalize_item(raw)
            doi = normalized["doi"]
            if doi and doi not in seen:
                seen.add(doi)
                items.append(normalized)
        if not raw_items or len(items) >= expected_total:
            break
        next_cursor = message.get("next-cursor")
        if not next_cursor or len(items) == before_count:
            break
        cursor = next_cursor
        if delay:
            time.sleep(delay)
    items.sort(key=lambda item: (item.get("publication_date") or "", item["doi"]))
    if expected_total is not None and len(items) != expected_total:
        raise RuntimeError(
            "Incomplete Crossref snapshot: expected "
            f"{expected_total} records but retrieved {len(items)} unique DOI records"
        )
    years = Counter((item.get("publication_date") or "unknown")[:4] for item in items)
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": f"ncs-crossref-2021-{CORPUS_CUTOFF}",
        "generated_at": utc_now(),
        "cutoff_date": CORPUS_CUTOFF,
        "source": {
            "name": "Crossref",
            "endpoint": CROSSREF_ENDPOINT,
            "issn": "2662-8457",
            "filter": f"2021-01-01 through {CORPUS_CUTOFF}; journal-article",
        },
        "summary": {
            "expected_total_results": expected_total,
            "unique_doi_count": len(items),
            "page_count": page_count,
            "year_counts": dict(sorted(years.items())),
        },
        "records_sha256": sha256_json(items),
        "records": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--mailto", default=DEFAULT_MAILTO)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--delay", type=float, default=0.2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = build_snapshot(args.rows, args.mailto, args.timeout, args.delay)
    write_json(args.output, snapshot)
    print(json.dumps(snapshot["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
