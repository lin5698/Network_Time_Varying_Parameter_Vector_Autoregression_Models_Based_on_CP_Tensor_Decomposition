"""Shared contracts for the NCS review corpus."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
MODEL_ID = "gpt-5.6-luna"
REASONING_EFFORT = "max"
CORPUS_CUTOFF = "2026-08-01"
PUBLIC_ACCESS_STATUSES = {"FULL_TEXT", "ABSTRACT_ONLY", "ACCESS_BLOCKED"}
EVIDENCE_GRADES = {"JPR", "PPR", "CPR", "VCO", "STATUS_ONLY"}
RELATEDNESS_LEVELS = {"A", "B", "C", "D"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_doi(value: str) -> str:
    normalized = normalize_space(value).lower()
    return re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", normalized)


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def doi_slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "__", normalize_doi(value)).strip("_")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Refusing to hash non-regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(payload)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def assert_ignored_private_path(path: Path, workspace: Path) -> None:
    resolved_workspace = workspace.resolve()
    resolved = path.resolve()
    expected = (resolved_workspace / "archive" / "research_corpus" / "ncs" / "private").resolve()
    if not resolved.is_relative_to(expected):
        raise ValueError(f"Private material must remain below {expected}: {resolved}")


def safe_relative(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))
