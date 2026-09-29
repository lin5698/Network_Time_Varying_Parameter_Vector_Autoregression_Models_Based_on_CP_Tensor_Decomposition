"""Normalize PDF and HTML evidence into stable locations."""

from __future__ import annotations

import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from .core import normalize_space, sha256_file, sha256_json


class ParagraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "p" and self._parts is None:
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "p" and self._parts is not None:
            value = normalize_space("".join(self._parts))
            if len(value) >= 20:
                self.paragraphs.append(value)
            self._parts = None

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)


def _split_pdf_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", normalized)
    blocks = re.split(r"\n\s*\n+", normalized)
    paragraphs: list[str] = []
    for block in blocks:
        value = normalize_space(block)
        if len(value) >= 20 and not re.fullmatch(r"\d+", value):
            paragraphs.append(value)
    if len(paragraphs) <= 1:
        lines = [normalize_space(line) for line in normalized.splitlines()]
        buffer: list[str] = []
        paragraphs = []
        for line in lines:
            if not line:
                if buffer:
                    paragraphs.append(normalize_space(" ".join(buffer)))
                    buffer = []
                continue
            if re.fullmatch(r"\d+", line):
                continue
            buffer.append(line)
        if buffer:
            paragraphs.append(normalize_space(" ".join(buffer)))
    return [paragraph for paragraph in paragraphs if len(paragraph) >= 20]


def extract_pdf(path: Path, document_id: str, document_type: str) -> dict[str, Any]:
    reader = PdfReader(str(path))
    pages: list[dict[str, Any]] = []
    textless_pages: list[int] = []
    for page_number, page in enumerate(reader.pages, start=1):
        paragraphs = _split_pdf_paragraphs(page.extract_text() or "")
        if not paragraphs:
            textless_pages.append(page_number)
        pages.append(
            {
                "page_number": page_number,
                "extraction_method": "PYPDF_TEXT" if paragraphs else "PYPDF_TEXT_EMPTY",
                "paragraphs": [
                    {
                        "paragraph_id": f"{document_id}-P{page_number:04d}-{index:03d}",
                        "text": paragraph,
                    }
                    for index, paragraph in enumerate(paragraphs, start=1)
                ],
            }
        )
    record = {
        "schema_version": "1.0",
        "document_id": document_id,
        "document_type": document_type,
        "source_file": path.name,
        "source_sha256": sha256_file(path),
        "page_count": len(pages),
        "extraction_method": "PYPDF_TEXT" if not textless_pages else "PYPDF_TEXT_PARTIAL",
        "ocr_status": "NOT_REQUIRED" if not textless_pages else "OCR_REQUIRED",
        "textless_pages": textless_pages,
        "pages": pages,
    }
    record["content_sha256"] = sha256_json(pages)
    return record


def ocr_textless_pdf_pages(
    path: Path, record: dict[str, Any], dpi: int = 250
) -> dict[str, Any]:
    if dpi < 100:
        raise ValueError("OCR dpi must be at least 100")
    textless_pages = list(record.get("textless_pages") or [])
    if not textless_pages:
        return record
    ocr_pages: list[int] = []
    unresolved_pages: list[int] = []
    pages_by_number = {page["page_number"]: page for page in record["pages"]}
    with tempfile.TemporaryDirectory(prefix="ncs-ocr-") as temporary_dir:
        temporary = Path(temporary_dir)
        for page_number in textless_pages:
            prefix = temporary / f"page-{page_number:04d}"
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-png",
                    "-r",
                    str(dpi),
                    "-singlefile",
                    str(path),
                    str(prefix),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            image_path = prefix.with_suffix(".png")
            completed = subprocess.run(
                ["tesseract", str(image_path), "stdout", "-l", "eng"],
                check=True,
                capture_output=True,
                text=True,
            )
            paragraphs = _split_pdf_paragraphs(completed.stdout)
            page = pages_by_number[page_number]
            if paragraphs:
                page["paragraphs"] = [
                    {
                        "paragraph_id": (
                            f"{record['document_id']}-P{page_number:04d}-{index:03d}"
                        ),
                        "text": paragraph,
                    }
                    for index, paragraph in enumerate(paragraphs, start=1)
                ]
                page["extraction_method"] = "TESSERACT_OCR"
                ocr_pages.append(page_number)
            else:
                page["extraction_method"] = "OCR_ATTEMPTED_NO_TEXT"
                unresolved_pages.append(page_number)
    record["extraction_method"] = "PYPDF_TEXT_PLUS_TESSERACT_OCR"
    record["ocr_status"] = (
        "OCR_DERIVED" if not unresolved_pages else "OCR_DERIVED_WITH_UNRESOLVED_PAGES"
    )
    record["ocr_pages"] = ocr_pages
    record["textless_pages"] = unresolved_pages
    record["content_sha256"] = sha256_json(record["pages"])
    return record


def extract_html(path: Path, document_id: str, document_type: str) -> dict[str, Any]:
    parser = ParagraphParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    paragraphs = [
        {"paragraph_id": f"{document_id}-H0001-{index:03d}", "text": text}
        for index, text in enumerate(parser.paragraphs, start=1)
    ]
    record = {
        "schema_version": "1.0",
        "document_id": document_id,
        "document_type": document_type,
        "source_file": path.name,
        "source_sha256": sha256_file(path),
        "page_count": None,
        "extraction_method": "HTML_PARAGRAPHS",
        "ocr_status": "NOT_APPLICABLE",
        "textless_pages": [],
        "pages": [{"page_number": None, "paragraphs": paragraphs}],
    }
    record["content_sha256"] = sha256_json(record["pages"])
    return record


def paragraph_lookup(documents: list[dict[str, Any]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for document in documents:
        for page in document.get("pages", []):
            for paragraph in page.get("paragraphs", []):
                paragraph_id = paragraph["paragraph_id"]
                if paragraph_id in lookup:
                    raise ValueError(f"Duplicate paragraph ID: {paragraph_id}")
                lookup[paragraph_id] = normalize_space(paragraph["text"])
    return lookup
