#!/usr/bin/env python3
"""Batch public NCS peer-review files for an auxiliary Qwen cross-check."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from .core import sha256_json, utc_now, write_json
from .privacy import EMAIL_PATTERN, PRIVATE_TOKENS, SUBMISSION_LINK_PATTERN


MODEL_ID = "qwen3.7-plus"
AUTHORITATIVE_MODEL_ID = "gpt-5.6-luna"
TASK_ID = "PUBLIC_REVIEW_ISSUE_INVENTORY_CROSSCHECK"
AUXILIARY_ROLE = "AUXILIARY_PUBLIC_CROSSCHECK_ONLY"
MAX_INPUT_BYTES = 256_000
CALIBRATION_IDS = (
    "CAL-D01",
    "CAL-D02",
    "CAL-D03",
    "CAL-E01",
    "CAL-E02",
    "CAL-E03",
)


SYSTEM_PROMPT = """You are an auxiliary auditor of one frozen, public Nature Computational Science peer-review package.

Use only the supplied JSON. Do not browse, use outside knowledge, infer editorial policy, estimate acceptance probability, or make journal-wide frequency claims. Treat this as an independent coverage cross-check, not the authoritative coding or adjudication pass. Luna Max remains the only authoritative adjudicator.

Identify editor priorities and reviewer concerns, including unresolved or partly resolved concerns. Write summaries in Chinese. Every inventory item must cite at least one supplied paragraph_id and one continuous verbatim quote of at most 300 characters. Return exactly one JSON object with these keys:

- task: the exact task identifier supplied by the user message
- calibration_id
- chunk_index and chunk_count
- issue_inventory: array of objects with actor_role, concern_domain, requested_action, summary_zh, resolution_signal, paragraph_id, quote
- editor_priorities_zh: array of strings
- reviewer_worries_zh: array of strings
- possible_coverage_gaps_zh: array of strings
- limitations_zh: array of strings
"""


def _assert_not_private_path(path: Path) -> None:
    parts = [part.lower() for part in path.resolve().parts]
    if any(parts[index - 1 : index + 1] == ["ncs", "private"] for index in range(1, len(parts))):
        raise ValueError(f"Qwen batch refuses private NCS material: {path}")


def discover_public_sources(public_root: Path) -> dict[str, Path]:
    """Resolve exactly the six frozen extracted packages below the public root."""
    _assert_not_private_path(public_root)
    extracted_root = public_root / "calibration" / "extracted"
    sources: dict[str, Path] = {}
    for calibration_id in CALIBRATION_IDS:
        source = extracted_root / f"{calibration_id.lower()}_documents.json"
        _assert_not_private_path(source)
        _assert_public_regular_file(source, public_root)
        sources[calibration_id] = source
    return sources


def _assert_public_regular_file(source: Path, public_root: Path) -> None:
    _assert_not_private_path(public_root)
    _assert_not_private_path(source)
    resolved_root = public_root.resolve()
    resolved_source = source.resolve()
    if not resolved_source.is_relative_to(resolved_root):
        raise ValueError(f"Qwen input must remain below public root: {resolved_root}")
    metadata = source.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Qwen input must be a regular non-symlink file: {source}")


def _redact_sensitive_text(value: str) -> str:
    redacted = SUBMISSION_LINK_PATTERN.sub("[REDACTED_SUBMISSION_LINK]", value)
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", redacted)
    for token in PRIVATE_TOKENS:
        redacted = re.sub(re.escape(token), "[REDACTED_PRIVATE_TOKEN]", redacted, flags=re.I)
    return redacted


def build_public_review_bundle(source: Path, public_root: Path) -> dict[str, Any]:
    """Load one public package while retaining only sanitized peer-review text."""
    _assert_public_regular_file(source, public_root)
    package = json.loads(source.read_text(encoding="utf-8"))
    documents: list[dict[str, Any]] = []
    seen_paragraph_ids: set[str] = set()
    for document in package.get("documents", []):
        if document.get("document_type") != "PEER_REVIEW_FILE":
            continue
        pages: list[dict[str, Any]] = []
        for page in document.get("pages", []):
            paragraphs: list[dict[str, str]] = []
            for paragraph in page.get("paragraphs", []):
                paragraph_id = paragraph.get("paragraph_id")
                text = paragraph.get("text")
                if not paragraph_id or text is None:
                    continue
                if paragraph_id in seen_paragraph_ids:
                    raise ValueError(f"Duplicate public paragraph ID: {paragraph_id}")
                seen_paragraph_ids.add(paragraph_id)
                paragraphs.append(
                    {
                        "paragraph_id": paragraph_id,
                        "text": _redact_sensitive_text(str(text)),
                    }
                )
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


def _paragraph_entries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for document in bundle["documents"]:
        for page in document["pages"]:
            for paragraph in page["paragraphs"]:
                entries.append(
                    {
                        "document_id": document["document_id"],
                        "document_type": document["document_type"],
                        "page_number": page.get("page_number"),
                        "paragraph": paragraph,
                    }
                )
    if not entries:
        raise ValueError("Public peer-review bundle has no paragraphs")
    return entries


def _documents_from_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    document_index: dict[str, int] = {}
    page_index: dict[tuple[str, Any], int] = {}
    for entry in entries:
        document_id = entry["document_id"]
        if document_id not in document_index:
            document_index[document_id] = len(documents)
            documents.append(
                {
                    "document_id": document_id,
                    "document_type": entry["document_type"],
                    "pages": [],
                }
            )
        document = documents[document_index[document_id]]
        page_key = (document_id, entry["page_number"])
        if page_key not in page_index:
            page_index[page_key] = len(document["pages"])
            document["pages"].append(
                {"page_number": entry["page_number"], "paragraphs": []}
            )
        document["pages"][page_index[page_key]]["paragraphs"].append(entry["paragraph"])
    return documents


def _serialize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _request_payload(
    bundle: dict[str, Any],
    entries: list[dict[str, Any]],
    chunk_index: int,
    chunk_count: int,
) -> dict[str, Any]:
    return {
        "task": TASK_ID,
        "calibration_id": bundle["calibration_id"],
        "documents_sha256": bundle["documents_sha256"],
        "chunk_index": chunk_index,
        "chunk_count": chunk_count,
        "documents": _documents_from_entries(entries),
    }


def _messages_for_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
        {"role": "user", "content": [{"text": _serialize(payload)}]},
    ]


def _request_bytes(messages: list[dict[str, Any]]) -> int:
    return len(_serialize(messages).encode("utf-8"))


def _request_descriptor(
    bundle: dict[str, Any],
    entries: list[dict[str, Any]],
    chunk_index: int,
    chunk_count: int,
) -> dict[str, Any]:
    payload = _request_payload(bundle, entries, chunk_index, chunk_count)
    messages = _messages_for_payload(payload)
    return {
        "chunk_index": chunk_index,
        "chunk_count": chunk_count,
        "paragraph_ids": [entry["paragraph"]["paragraph_id"] for entry in entries],
        "messages": messages,
        "request_bytes": _request_bytes(messages),
    }


def build_requests_from_bundle(
    bundle: dict[str, Any], max_input_bytes: int = MAX_INPUT_BYTES
) -> list[dict[str, Any]]:
    """Build ordered, non-overlapping Qwen requests from one sanitized bundle."""
    if max_input_bytes <= 0 or max_input_bytes > MAX_INPUT_BYTES:
        raise ValueError(
            f"max_input_bytes must be between 1 and {MAX_INPUT_BYTES} bytes"
        )
    entries = _paragraph_entries(bundle)
    # The final chunk count cannot exceed the number of paragraphs. Using that
    # bound while packing reserves all possible digit positions in metadata.
    chunk_count_hint = len(entries)
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for entry in entries:
        candidate = current + [entry]
        descriptor = _request_descriptor(
            bundle,
            candidate,
            len(groups) + 1,
            chunk_count_hint,
        )
        if descriptor["request_bytes"] <= max_input_bytes:
            current = candidate
            continue
        if not current:
            raise ValueError(
                "Paragraph cannot fit within Qwen request byte limit: "
                f"{entry['paragraph']['paragraph_id']} requires "
                f"{descriptor['request_bytes']} bytes, limit is {max_input_bytes}"
            )
        groups.append(current)
        current = [entry]
        single = _request_descriptor(
            bundle,
            current,
            len(groups) + 1,
            chunk_count_hint,
        )
        if single["request_bytes"] > max_input_bytes:
            raise ValueError(
                "Paragraph cannot fit within Qwen request byte limit: "
                f"{entry['paragraph']['paragraph_id']} requires "
                f"{single['request_bytes']} bytes, limit is {max_input_bytes}"
            )
    if current:
        groups.append(current)

    requests = [
        _request_descriptor(bundle, group, index, len(groups))
        for index, group in enumerate(groups, start=1)
    ]
    for request in requests:
        if request["request_bytes"] > max_input_bytes:
            raise AssertionError(
                "Final Qwen request exceeded byte limit after chunk metadata was finalized"
            )
    flattened_ids = [paragraph_id for request in requests for paragraph_id in request["paragraph_ids"]]
    expected_ids = [entry["paragraph"]["paragraph_id"] for entry in entries]
    if flattened_ids != expected_ids or len(flattened_ids) != len(set(flattened_ids)):
        raise AssertionError("Qwen chunking lost or duplicated public paragraph IDs")
    return requests


def build_requests(
    source: Path,
    public_root: Path,
    max_input_bytes: int = MAX_INPUT_BYTES,
) -> list[dict[str, Any]]:
    bundle = build_public_review_bundle(source, public_root)
    return build_requests_from_bundle(bundle, max_input_bytes=max_input_bytes)


def _strip_json_fence(value: str) -> str:
    text = value.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1) if match else text


def _extract_response_text(response: Any) -> str:
    try:
        return response.output.choices[0].message.content[0]["text"]
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise RuntimeError("DashScope returned an unexpected response shape") from exc


def _safe_error_message(error: BaseException) -> str:
    message = str(error)
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if api_key:
        message = message.replace(api_key, "[REDACTED_API_KEY]")
    return message[:2_000]


def call_qwen(messages: list[dict[str, Any]]) -> str:
    """Call Qwen without accepting or exposing credentials through the API."""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
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
        raise RuntimeError(
            "DashScope request failed "
            f"({status_code}, request_id={request_id}): {message}"
        )
    return _extract_response_text(response)


def _payload_from_request(request: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(request["messages"][1]["content"][0]["text"])
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Qwen request descriptor has invalid user JSON") from exc


def _paragraph_lookup_from_request(request: dict[str, Any]) -> dict[str, str]:
    payload = _payload_from_request(request)
    lookup: dict[str, str] = {}
    for document in payload.get("documents", []):
        for page in document.get("pages", []):
            for paragraph in page.get("paragraphs", []):
                paragraph_id = paragraph.get("paragraph_id")
                if paragraph_id in lookup:
                    raise ValueError(f"Duplicate paragraph ID in Qwen request: {paragraph_id}")
                lookup[paragraph_id] = str(paragraph.get("text", ""))
    return lookup


def _privacy_errors(value: Any) -> list[str]:
    serialized = _serialize(value)
    errors: list[str] = []
    if EMAIL_PATTERN.search(serialized):
        errors.append("email address present")
    if SUBMISSION_LINK_PATTERN.search(serialized):
        errors.append("submission-system link present")
    for token in PRIVATE_TOKENS:
        if token.lower() in serialized.lower():
            errors.append(f"private token present: {token}")
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if api_key and api_key in serialized:
        errors.append("configured API key present")
    return errors


def validate_result(result: dict[str, Any], request: dict[str, Any]) -> list[str]:
    """Validate one Qwen response against only the paragraphs in its request."""
    errors: list[str] = []
    payload = _payload_from_request(request)
    if result.get("task") != TASK_ID:
        errors.append("$.task does not match the requested auxiliary task")
    if result.get("calibration_id") != payload.get("calibration_id"):
        errors.append("$.calibration_id does not match the source package")
    if result.get("chunk_index") != payload.get("chunk_index"):
        errors.append("$.chunk_index does not match the requested chunk")
    if result.get("chunk_count") != payload.get("chunk_count"):
        errors.append("$.chunk_count does not match the requested chunk")
    issues = result.get("issue_inventory")
    if not isinstance(issues, list):
        errors.append("$.issue_inventory must be an array")
        return errors
    lookup = _paragraph_lookup_from_request(request)
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
    errors.extend(f"$.result: {error}" for error in _privacy_errors(result))
    return errors


def _request_metadata(request: dict[str, Any]) -> dict[str, Any]:
    paragraph_ids = request["paragraph_ids"]
    return {
        "chunk_index": request["chunk_index"],
        "chunk_count": request["chunk_count"],
        "paragraph_count": len(paragraph_ids),
        "first_paragraph_id": paragraph_ids[0],
        "last_paragraph_id": paragraph_ids[-1],
        "request_bytes": request["request_bytes"],
    }


def _base_receipt(
    source: Path,
    bundle: dict[str, Any],
    requests: list[dict[str, Any]],
    max_input_bytes: int,
    mode: str,
    status: str,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema_version": "qwen-batch-v1",
        "generated_at": utc_now(),
        "task": TASK_ID,
        "role": AUXILIARY_ROLE,
        "model": MODEL_ID,
        "authoritative_model": AUTHORITATIVE_MODEL_ID,
        "adjudication_contract": {
            "qwen_is_auxiliary_only": True,
            "luna_max_is_authoritative_adjudicator": True,
            "qwen_result_cannot_replace_luna_max": True,
        },
        "calibration_id": bundle["calibration_id"],
        "source_file": source.name,
        "input": {
            "documents_sha256": bundle["documents_sha256"],
            "bundle_sha256": sha256_json(bundle),
            "paragraph_count": sum(len(request["paragraph_ids"]) for request in requests),
            "request_count": len(requests),
            "maximum_request_bytes": max_input_bytes,
            "requests": [_request_metadata(request) for request in requests],
            "private_material_allowed": False,
        },
        "mode": mode,
        "status": status,
        "chunks": [
            {
                **_request_metadata(request),
                "status": status,
            }
            for request in requests
        ],
    }
    if blocked_reason:
        receipt["blocked_reason"] = blocked_reason
    return receipt


def _write_receipt(
    output_dir: Path,
    receipt: dict[str, Any],
    dry_run_filename: bool,
) -> str:
    suffix = "-dry-run" if dry_run_filename else ""
    output_file = f"{receipt['calibration_id'].lower()}{suffix}.json"
    write_json(output_dir / output_file, receipt)
    return output_file


def run_one(
    source: Path,
    public_root: Path,
    output_dir: Path,
    max_input_bytes: int = MAX_INPUT_BYTES,
    dry_run: bool = False,
) -> dict[str, Any]:
    bundle = build_public_review_bundle(source, public_root)
    requests = build_requests_from_bundle(bundle, max_input_bytes=max_input_bytes)
    api_key_available = bool(os.environ.get("DASHSCOPE_API_KEY"))
    blocked_reason = None
    if not dry_run and not api_key_available:
        mode = "DRY_RUN"
        status = "BLOCKED"
        blocked_reason = "DASHSCOPE_API_KEY is not configured"
    elif dry_run:
        mode = "DRY_RUN"
        status = "DRY_RUN"
    else:
        mode = "LIVE"
        status = "PENDING"
    receipt = _base_receipt(
        source,
        bundle,
        requests,
        max_input_bytes,
        mode,
        status,
        blocked_reason,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    if mode == "LIVE":
        try:
            for index, request in enumerate(requests):
                raw_text = call_qwen(request["messages"])
                try:
                    result = json.loads(_strip_json_fence(raw_text))
                except (TypeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"Qwen chunk {request['chunk_index']} did not return one JSON object"
                    ) from exc
                if not isinstance(result, dict):
                    raise ValueError(
                        f"Qwen chunk {request['chunk_index']} returned non-object JSON"
                    )
                errors = validate_result(result, request)
                if errors:
                    raise ValueError(
                        f"Qwen chunk {request['chunk_index']} failed validation:\n"
                        + "\n".join(errors)
                    )
                receipt["chunks"][index]["status"] = "COMPLETE"
                receipt["chunks"][index]["result"] = result
            receipt["status"] = "COMPLETE"
        except Exception as exc:
            receipt["status"] = "FAILED"
            receipt["error"] = _safe_error_message(exc)
            for chunk in receipt["chunks"]:
                if chunk["status"] == "PENDING":
                    chunk["status"] = "NOT_RUN"
    _write_receipt(output_dir, receipt, dry_run_filename=mode == "DRY_RUN")
    return receipt


def run_batch(
    public_root: Path,
    output_dir: Path,
    max_input_bytes: int = MAX_INPUT_BYTES,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Process all six public packages, falling back to blocked dry-run if unkeyed."""
    sources = discover_public_sources(public_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    api_key_available = bool(os.environ.get("DASHSCOPE_API_KEY"))
    records: list[dict[str, Any]] = []
    for calibration_id, source in sources.items():
        receipt = run_one(
            source,
            public_root,
            output_dir,
            max_input_bytes=max_input_bytes,
            dry_run=dry_run,
        )
        suffix = "-dry-run" if receipt["mode"] == "DRY_RUN" else ""
        records.append(
            {
                "calibration_id": calibration_id,
                "status": receipt["status"],
                "mode": receipt["mode"],
                "output_file": f"{calibration_id.lower()}{suffix}.json",
                "request_count": receipt["input"]["request_count"],
                "paragraph_count": receipt["input"]["paragraph_count"],
                "maximum_request_bytes": max(
                    request["request_bytes"] for request in receipt["input"]["requests"]
                ),
            }
        )
    blocked_reason = (
        "DASHSCOPE_API_KEY is not configured" if not dry_run and not api_key_available else None
    )
    if blocked_reason:
        status = "BLOCKED"
        mode = "DRY_RUN"
    elif dry_run:
        status = "DRY_RUN"
        mode = "DRY_RUN"
    elif all(record["status"] == "COMPLETE" for record in records):
        status = "COMPLETE"
        mode = "LIVE"
    else:
        status = "FAILED"
        mode = "LIVE"
    summary: dict[str, Any] = {
        "schema_version": "qwen-batch-summary-v1",
        "generated_at": utc_now(),
        "task": TASK_ID,
        "role": AUXILIARY_ROLE,
        "model": MODEL_ID,
        "authoritative_model": AUTHORITATIVE_MODEL_ID,
        "adjudication_required": True,
        "calibration_ids": list(CALIBRATION_IDS),
        "mode": mode,
        "status": status,
        "records": records,
    }
    if blocked_reason:
        summary["blocked_reason"] = blocked_reason
    write_json(output_dir / "batch-summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--public-root",
        type=Path,
        default=Path("archive/research_corpus/ncs/public"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/ncs_review_corpus/qwen_aux"),
    )
    parser.add_argument("--max-input-bytes", type=int, default=MAX_INPUT_BYTES)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_batch(
        public_root=args.public_root,
        output_dir=args.output_dir,
        max_input_bytes=args.max_input_bytes,
        dry_run=args.dry_run,
    )
    print(_serialize(summary))
    return 0 if summary["status"] != "FAILED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
