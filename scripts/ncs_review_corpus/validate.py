"""Grounding and privacy checks for review-corpus outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import normalize_space
from .extract import paragraph_lookup
from .privacy import EMAIL_PATTERN, PRIVATE_TOKENS, SUBMISSION_LINK_PATTERN


def validate_evidence_items(analysis: dict[str, Any], documents: list[dict[str, Any]]) -> list[str]:
    lookup = paragraph_lookup(documents)
    errors: list[str] = []
    for index, issue in enumerate(analysis.get("issues", []), start=1):
        evidence = issue.get("evidence") or []
        if not evidence:
            errors.append(f"issue {index}: missing evidence")
        for evidence_index, item in enumerate(evidence, start=1):
            paragraph_id = item.get("paragraph_id")
            quote = normalize_space(item.get("quote", ""))
            if paragraph_id not in lookup:
                errors.append(
                    f"issue {index} evidence {evidence_index}: unknown paragraph_id {paragraph_id!r}"
                )
                continue
            if not quote or quote not in lookup[paragraph_id]:
                errors.append(
                    f"issue {index} evidence {evidence_index}: quote is not verbatim"
                )
            if len(quote) > 300:
                errors.append(
                    f"issue {index} evidence {evidence_index}: quote exceeds 300 characters"
                )
    return errors


def scan_public_exports(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in PRIVATE_TOKENS:
            if token.lower() in text.lower():
                errors.append(f"{path}: private token present: {token}")
        if EMAIL_PATTERN.search(text):
            errors.append(f"{path}: email address present")
        if SUBMISSION_LINK_PATTERN.search(text):
            errors.append(f"{path}: submission-system link present")
    return errors
