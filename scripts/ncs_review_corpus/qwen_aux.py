#!/usr/bin/env python3
"""Run a bounded, public-only Qwen cross-check for the NCS review corpus."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from .core import sha256_bytes, utc_now, write_json
from .privacy import (
    EMAIL_PATTERN,
    PRIVATE_TOKENS,
    SUBMISSION_LINK_PATTERN,
)


MODEL_ID = "qwen3.7-plus"
TASK_ID = "PUBLIC_REVIEW_ISSUE_INVENTORY_CROSSCHECK"
MAX_INPUT_BYTES = 256_000

SYSTEM_PROMPT = """You are an auxiliary auditor of one frozen, public Nature Computational Science peer-review package.

Use only the supplied JSON. Do not browse, use outside knowledge, infer editorial policy, estimate acceptance probability, or make journal-wide frequency claims. Treat this as an independent coverage cross-check, not the authoritative coding pass.

Identify editor priorities and reviewer concerns, including unresolved or partly resolved concerns. Write summaries in Chinese. Every inventory item must cite at least one supplied paragraph_id and one continuous verbatim quote of at most 300 characters. Return exactly one JSON object with these keys:

- task: the exact task identifier supplied by the user message
- calibration_id
- issue_inventory: array of objects with actor_role, concern_domain, requested_action, summary_zh, resolution_signal, paragraph_id, quote
- editor_priorities_zh: array of strings
- reviewer_worries_zh: array of strings
- possible_coverage_gaps_zh: array of strings
- limitations_zh: array of strings
"""


def _assert_public_regular_file(source: Path, public_root: Path) -> None:
    resolved_root = public_root.resolve()
    resolved_source = source.resolve()
    if not resolved_source.is_relative_to(resolved_root):
        raise ValueError(f"Qwen input must remain below public root: {resolved_root}")
    metadata = source.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Qwen input must be a regular non-symlink file: {source}")


def _redact_sensitive_text(value: str) -> str:
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    redacted = SUBMISSION_LINK_PATTERN.sub("[REDACTED_SUBMISSION_LINK]", redacted)
    for token in PRIVATE_TOKENS:
        redacted = re.sub(re.escape(token), "[REDACTED_PRIVATE_TOKEN]", redacted, flags=re.I)
    return redacted


def build_public_review_bundle(source: Path, public_root: Path) -> dict[str, Any]:
    _assert_public_regular_file(source, public_root)
    package = json.loads(source.read_text(encoding="utf-8"))
    documents: list[dict[str, Any]] = []
    for document in package.get("documents", []):
        if document.get("document_type") != "PEER_REVIEW_FILE":
            continue
        pages: list[dict[str, Any]] = []
        for page in document.get("pages", []):
            paragraphs = [
                {
                    "paragraph_id": paragraph["paragraph_id"],
                    "text": _redact_sensitive_text(paragraph.get("text", "")),
                }
                for paragraph in page.get("paragraphs", [])
                if paragraph.get("paragraph_id") and paragraph.get("text")
            ]
            if paragraphs:
                pages.append({"page_number": page.get("page_number"), "paragraphs": paragraphs})
        if pages:
            documents.append(
                {
                    "document_id": document["document_id"],
                    "document_type": "PEER_REVIEW_FILE",
                    "pages": pages,
                }
            )
    if not documents:
        raise ValueError("Source package has no public peer-review document")
    return {
        "task": TASK_ID,
        "calibration_id": package["calibration_id"],
        "documents_sha256": package["documents_sha256"],
        "documents": documents,
    }


def build_messages(bundle: dict[str, Any], max_input_bytes: int = MAX_INPUT_BYTES) -> tuple[list[dict[str, Any]], int]:
    messages = [
        {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
        {
            "role": "user",
            "content": [
                {
                    "text": json.dumps(
                        bundle,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                }
            ],
        },
    ]
    input_bytes = len(
        json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    if input_bytes > max_input_bytes:
        raise ValueError(f"Qwen input is {input_bytes} bytes; limit is {max_input_bytes}")
    return messages, input_bytes


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.I)
    return match.group(1) if match else text


def _paragraph_lookup(bundle: dict[str, Any]) -> dict[str, str]:
    return {
        paragraph["paragraph_id"]: paragraph["text"]
        for document in bundle["documents"]
        for page in document["pages"]
        for paragraph in page["paragraphs"]
    }


def validate_result(result: dict[str, Any], bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("task") != TASK_ID:
        errors.append("$.task does not match the requested auxiliary task")
    if result.get("calibration_id") != bundle["calibration_id"]:
        errors.append("$.calibration_id does not match the source package")
    issues = result.get("issue_inventory")
    if not isinstance(issues, list) or not issues:
        errors.append("$.issue_inventory must be a non-empty array")
        return errors
    lookup = _paragraph_lookup(bundle)
    for index, issue in enumerate(issues):
        prefix = f"$.issue_inventory[{index}]"
        if not isinstance(issue, dict):
            errors.append(f"{prefix} must be an object")
            continue
        paragraph_id = issue.get("paragraph_id")
        quote = " ".join(str(issue.get("quote", "")).split())
        source_text = " ".join(lookup.get(paragraph_id, "").split())
        if paragraph_id not in lookup:
            errors.append(f"{prefix}.paragraph_id is unknown")
        elif not quote or quote not in source_text:
            errors.append(f"{prefix}.quote is not verbatim")
        if len(quote) > 300:
            errors.append(f"{prefix}.quote exceeds 300 characters")
    return errors


def _extract_response_text(response: Any) -> str:
    try:
        return response.output.choices[0].message.content[0]["text"]
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise RuntimeError("DashScope returned an unexpected response shape") from exc


def call_qwen(messages: list[dict[str, Any]]) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")
    try:
        import dashscope
    except ImportError as exc:
        raise RuntimeError(
            "dashscope is unavailable; install scripts/ncs_review_corpus/requirements.txt"
        ) from exc
    dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
    response = dashscope.MultiModalConversation.call(
        api_key=api_key,
        model=MODEL_ID,
        messages=messages,
    )
    status_code = getattr(response, "status_code", 200)
    if status_code != 200:
        request_id = getattr(response, "request_id", "unknown")
        message = getattr(response, "message", "DashScope request failed")
        raise RuntimeError(f"DashScope request failed ({status_code}, request_id={request_id}): {message}")
    return _extract_response_text(response)


def run(source: Path, public_root: Path, output: Path, max_input_bytes: int, dry_run: bool) -> dict[str, Any]:
    bundle = build_public_review_bundle(source, public_root)
    messages, input_bytes = build_messages(bundle, max_input_bytes=max_input_bytes)
    serialized_bundle = json.dumps(
        bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    paragraph_count = len(_paragraph_lookup(bundle))
    receipt: dict[str, Any] = {
        "schema_version": "qwen-aux-v1",
        "generated_at": utc_now(),
        "task": TASK_ID,
        "role": "AUXILIARY_PUBLIC_CROSSCHECK_ONLY",
        "model": MODEL_ID,
        "input": {
            "calibration_id": bundle["calibration_id"],
            "documents_sha256": bundle["documents_sha256"],
            "bundle_sha256": sha256_bytes(serialized_bundle),
            "request_bytes": input_bytes,
            "maximum_request_bytes": max_input_bytes,
            "paragraph_count": paragraph_count,
            "private_material_allowed": False,
        },
        "status": "DRY_RUN" if dry_run else "COMPLETE",
    }
    if not dry_run:
        raw_text = call_qwen(messages)
        result = json.loads(_strip_json_fence(raw_text))
        errors = validate_result(result, bundle)
        if errors:
            raise ValueError("Qwen auxiliary result failed validation:\n" + "\n".join(errors))
        serialized_result = json.dumps(result, ensure_ascii=False)
        sensitive_markers = [token for token in PRIVATE_TOKENS if token.lower() in serialized_result.lower()]
        if EMAIL_PATTERN.search(serialized_result) or SUBMISSION_LINK_PATTERN.search(serialized_result) or sensitive_markers:
            raise ValueError("Qwen auxiliary result failed privacy validation")
        receipt["result"] = result
    write_json(output, receipt)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--public-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-input-bytes", default=MAX_INPUT_BYTES, type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = run(
        source=args.source,
        public_root=args.public_root,
        output=args.output,
        max_input_bytes=args.max_input_bytes,
        dry_run=args.dry_run,
    )
    print(json.dumps({"status": receipt["status"], **receipt["input"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
