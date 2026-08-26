"""Discover and archive official Nature article materials."""

from __future__ import annotations

import html
import http.client
import json
import re
import socket
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .core import normalize_space, sha256_bytes, sha256_file, utc_now, write_json


USER_AGENT = "Mozilla/5.0 (compatible; NCSReviewCorpus/1.0)"
ALLOWED_DOWNLOAD_HOSTS = {"www.nature.com", "media.springernature.com"}
DEFAULT_ARCHIVE_KINDS = {
    "ARTICLE_PDF",
    "SUPPLEMENTARY_INFORMATION",
    "PEER_REVIEW_FILE",
    "REPORTING_SUMMARY",
}


class MaterialParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.metadata: dict[str, list[str]] = {}
        self.materials: list[dict[str, str]] = []
        self._anchor: dict[str, str] | None = None
        self._anchor_parts: list[str] = []
        self._category_depth = 0
        self._category_parts: list[str] = []
        self.article_category: str | None = None

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key.lower(): value or "" for key, value in attrs_list}
        tag = tag.lower()
        if tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or "").lower()
            content = normalize_space(attrs.get("content", ""))
            if name and content:
                self.metadata.setdefault(name, []).append(content)
        if tag == "a" and attrs.get("href"):
            self._anchor = attrs
            self._anchor_parts = []
        if self._category_depth:
            self._category_depth += 1
        elif attrs.get("data-test") == "article-category":
            self._category_depth = 1
            self._category_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._anchor is not None:
            label = normalize_space("".join(self._anchor_parts))
            href = html.unescape(self._anchor.get("href", ""))
            if label and href:
                self.materials.append(
                    {
                        "label": label,
                        "href": href,
                        "data_test": self._anchor.get("data-test", ""),
                        "track_label": self._anchor.get("data-track-label", ""),
                    }
                )
            self._anchor = None
            self._anchor_parts = []
        if self._category_depth:
            self._category_depth -= 1
            if self._category_depth == 0 and self.article_category is None:
                self.article_category = normalize_space("".join(self._category_parts)) or None

    def handle_data(self, data: str) -> None:
        if self._anchor is not None:
            self._anchor_parts.append(data)
        if self._category_depth:
            self._category_parts.append(data)


def is_retryable_download_error(exc: BaseException) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code < 600
    return isinstance(
        exc,
        (http.client.IncompleteRead, TimeoutError, socket.timeout, ConnectionError, URLError),
    )


def fetch_bytes(
    url: str,
    timeout: float = 60.0,
    accept: str = "*/*",
    max_attempts: int = 4,
) -> tuple[bytes, int, str, str | None]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError(f"Unsupported download host: {url}")
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    for attempt in range(1, max_attempts + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urlopen(request, timeout=timeout) as response:
                return (
                    response.read(),
                    response.status,
                    response.geturl(),
                    response.headers.get("Content-Type"),
                )
        except Exception as exc:  # noqa: BLE001 - retry contract is type/status based
            if attempt == max_attempts or not is_retryable_download_error(exc):
                raise
            time.sleep(min(2**attempt, 10))
    raise AssertionError("unreachable")


def classify_material(label: str, href: str, citation_pdf_url: str | None) -> str | None:
    normalized = normalize_space(label).lower()
    href_lower = href.lower()
    if citation_pdf_url and href == citation_pdf_url:
        return "ARTICLE_PDF"
    if "peer review file" in normalized or "peer-review file" in normalized:
        return "PEER_REVIEW_FILE"
    if "supplementary information" in normalized or "supplementary material" in normalized:
        return "SUPPLEMENTARY_INFORMATION"
    if "reporting summary" in normalized:
        return "REPORTING_SUMMARY"
    if "source data" in normalized:
        return "SOURCE_DATA"
    if href_lower.endswith(".pdf") and "supp" in normalized:
        return "SUPPLEMENTARY_INFORMATION"
    return None


def discover_materials(article_url: str, timeout: float = 60.0) -> dict[str, Any]:
    raw, status, final_url, content_type = fetch_bytes(article_url, timeout, "text/html")
    parser = MaterialParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    citation_pdf_url = (parser.metadata.get("citation_pdf_url") or [None])[0]
    candidates = list(parser.materials)
    if citation_pdf_url:
        candidates.append({"label": "Article PDF", "href": citation_pdf_url})
    materials: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        href = urljoin(final_url, candidate["href"])
        kind = classify_material(candidate["label"], href, citation_pdf_url)
        if not kind:
            continue
        parsed = urlparse(href)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
            continue
        key = (kind, href)
        if key in seen:
            continue
        seen.add(key)
        materials.append({"kind": kind, "label": candidate["label"], "url": href})
    return {
        "retrieved_at": utc_now(),
        "requested_url": article_url,
        "final_url": final_url,
        "http_status": status,
        "content_type": content_type,
        "raw_sha256": sha256_bytes(raw),
        "metadata": {
            "doi": (parser.metadata.get("citation_doi") or [None])[0],
            "title": (parser.metadata.get("citation_title") or [None])[0],
            "publication_date": (parser.metadata.get("citation_publication_date") or [None])[0],
            "journal_title": (parser.metadata.get("citation_journal_title") or [None])[0],
            "article_category": parser.article_category,
            "article_pdf_url": citation_pdf_url,
        },
        "materials": materials,
        "raw_html": raw,
    }


def write_immutable(path: Path, raw: bytes) -> str:
    digest = sha256_bytes(raw)
    if path.exists():
        if not path.is_file() or sha256_bytes(path.read_bytes()) != digest:
            raise FileExistsError(f"Refusing to overwrite changed archive file: {path}")
        return digest
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(path)
    return digest


def select_archive_materials(
    materials: list[dict[str, str]], include_kinds: set[str]
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    for kind in sorted(include_kinds):
        candidates = [item for item in materials if item["kind"] == kind]
        media_candidates = [
            item for item in candidates if urlparse(item["url"]).hostname == "media.springernature.com"
        ]
        selected.extend(media_candidates or candidates)
    return selected


def archive_materials(
    discovery: dict[str, Any],
    destination: Path,
    timeout: float = 60.0,
    include_kinds: set[str] | None = None,
) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    selected_kinds = include_kinds or DEFAULT_ARCHIVE_KINDS
    records: list[dict[str, Any]] = []
    selected = select_archive_materials(discovery["materials"], selected_kinds)
    for index, material in enumerate(selected, start=1):
        raw, status, final_url, content_type = fetch_bytes(material["url"], timeout)
        extension = ".pdf" if raw.startswith(b"%PDF") else Path(urlparse(final_url).path).suffix or ".bin"
        filename = f"{index:02d}_{material['kind'].lower()}{extension}"
        target = destination / filename
        digest = write_immutable(target, raw)
        records.append(
            {
                **material,
                "final_url": final_url,
                "http_status": status,
                "content_type": content_type,
                "file": filename,
                "size_bytes": len(raw),
                "sha256": digest,
                "is_pdf": raw.startswith(b"%PDF"),
            }
        )
    return records


def archive_article(discovery: dict[str, Any], destination: Path, timeout: float = 60.0) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    landing_path = destination / "00_landing_page.html"
    landing_raw = landing_path.read_bytes() if landing_path.exists() else discovery["raw_html"]
    landing_sha256 = write_immutable(landing_path, landing_raw)
    materials = archive_materials(discovery, destination, timeout)
    manifest = {
        "schema_version": "1.0",
        "archived_at": utc_now(),
        "requested_url": discovery["requested_url"],
        "final_url": discovery["final_url"],
        "metadata": discovery["metadata"],
        "landing_page": {
            "file": landing_path.name,
            "size_bytes": len(landing_raw),
            "sha256": landing_sha256,
            "content_type": discovery["content_type"],
        },
        "materials": materials,
    }
    write_json(destination / "manifest.json", manifest)
    return manifest


def validate_archived_article(
    manifest_path: Path,
    expected_doi: str,
    required_kinds: set[str],
    required_pdf_kinds: set[str] | None = None,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archived_doi = normalize_space(manifest.get("metadata", {}).get("doi") or "").lower()
    if archived_doi != expected_doi.lower():
        raise ValueError(f"Archived DOI mismatch in {manifest_path}: {archived_doi!r}")
    records = [manifest["landing_page"], *manifest["materials"]]
    for record in records:
        path = manifest_path.parent / record["file"]
        if not path.is_file() or sha256_file(path) != record["sha256"]:
            raise ValueError(f"Archived file missing or hash mismatch: {path}")
    kinds = {record["kind"] for record in manifest["materials"]}
    missing = required_kinds - kinds
    if missing:
        raise ValueError(f"Archived article lacks required material kinds: {sorted(missing)}")
    pdf_kinds = required_pdf_kinds or set()
    invalid_pdf_kinds = {
        record["kind"]
        for record in manifest["materials"]
        if record["kind"] in pdf_kinds and not record.get("is_pdf")
    }
    if invalid_pdf_kinds:
        raise ValueError(
            f"Archived required PDF materials are not PDFs: {sorted(invalid_pdf_kinds)}"
        )
    return manifest
