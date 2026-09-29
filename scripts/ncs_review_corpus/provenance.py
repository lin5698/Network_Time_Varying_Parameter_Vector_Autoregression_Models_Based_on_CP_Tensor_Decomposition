"""Create and verify privacy-preserving receipts for future model calls.

Receipts deliberately contain only bounded identifiers, UTC timestamps, and
SHA-256 digests.  ``write_receipt`` publishes a receipt once and refuses to
replace an existing path, while hardening the published inode to read-only
mode at creation time.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .privacy import EMAIL_PATTERN, PRIVATE_TOKENS, SUBMISSION_LINK_PATTERN


SCHEMA_VERSION = "1.0"
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_.:-]{0,63}$")
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)

REQUIRED_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "provider",
        "model",
        "reasoning",
        "task_id",
        "thread_id",
        "invoked_at",
        "completed_at",
        "input_file_hashes",
        "prompt_sha256",
        "schema_sha256",
        "output_sha256",
        "validator",
        "status",
    }
)
VALIDATOR_REQUIRED_FIELDS = frozenset({"name", "status", "error_count"})
VALIDATOR_OPTIONAL_FIELDS = frozenset({"codes"})
VALIDATOR_STATUSES = frozenset({"PASS", "FAIL"})

_FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "api_key",
        "access_token",
        "body",
        "content",
        "environment",
        "environment_value",
        "env_value",
        "file_path",
        "filename",
        "input_body",
        "input_text",
        "key",
        "material",
        "output",
        "output_body",
        "output_text",
        "path",
        "password",
        "private_material",
        "private_path",
        "prompt",
        "prompt_body",
        "prompt_text",
        "public_material",
        "public_material_text",
        "quote",
        "raw",
        "raw_output",
        "raw_prompt",
        "raw_response",
        "response",
        "response_body",
        "response_text",
        "secret",
        "text",
        "token",
    }
)
_ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?i)(?:^|[\s\"'=])(?:[a-z]:[\\/]|/(?:users|home|private|var|tmp|volumes|system|opt|etc)/)"
)
_PRIVATE_PATH_PATTERN = re.compile(
    r"(?i)(?:archive[\\/]research_corpus[\\/]ncs[\\/]private|[\\/]private[\\/])"
)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|credential|authorization|bearer)\b\s*[:=]\s*\S+"
)
_ENV_ASSIGNMENT_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\s*=\s*\S+")
_COMMON_TOKEN_PATTERN = re.compile(
    r"(?i)\b(?:sk-[a-z0-9_-]{12,}|sk_[a-z0-9_-]{12,}|gsk_[a-z0-9_-]{12,}|"
    r"xai-[a-z0-9_-]{12,}|AIza[a-z0-9_-]{20,}|AKIA[a-z0-9]{16})\b"
)


def utc_now() -> str:
    """Return a canonical UTC timestamp suitable for a receipt."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha256_bytes(value: bytes) -> str:
    """Hash bytes without retaining or serializing the bytes."""

    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash a regular file and reject symlinks and other file types."""

    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"Refusing to hash non-regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_safe_identifier(value: Any) -> bool:
    return isinstance(value, str) and SAFE_IDENTIFIER_PATTERN.fullmatch(value) is not None


def _is_safe_code(value: Any) -> bool:
    return isinstance(value, str) and SAFE_CODE_PATTERN.fullmatch(value) is not None


def _validate_label(label: Any) -> None:
    if not _is_safe_identifier(label):
        raise ValueError(
            "Input file labels must be short logical identifiers, not paths or file contents"
        )


def hash_input_files(input_files: Mapping[str, Path]) -> dict[str, str]:
    """Return hashes keyed by safe logical labels; no file path is persisted."""

    if not isinstance(input_files, Mapping) or not input_files:
        raise ValueError("At least one input file is required")
    result: dict[str, str] = {}
    for label, path in input_files.items():
        _validate_label(label)
        if not isinstance(path, Path):
            raise TypeError("Input file values must be pathlib.Path instances")
        result[str(label)] = sha256_file(path)
    return result


def _artifact_digest(value: Path | bytes | str, *, allow_text: bool = True) -> str:
    if isinstance(value, Path):
        return sha256_file(value)
    if isinstance(value, bytes):
        return sha256_bytes(value)
    if allow_text and isinstance(value, str):
        return sha256_bytes(value.encode("utf-8"))
    raise TypeError("Artifact must be bytes, text, or pathlib.Path")


def _timestamp(value: str) -> datetime | None:
    if not isinstance(value, str) or UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _sensitive_environment_values() -> tuple[str, ...]:
    values: list[str] = []
    for name, value in os.environ.items():
        normalized_name = name.upper()
        if not any(
            marker in normalized_name
            for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH")
        ):
            continue
        if value and len(value) >= 8:
            values.append(value)
    return tuple(sorted(set(values), key=len, reverse=True))


def scan_receipt_privacy(value: Any) -> list[str]:
    """Return privacy violations without echoing the detected value."""

    errors: list[str] = []
    environment_values = _sensitive_environment_values()

    def visit(node: Any, location: str) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_text = str(key)
                key_normalized = key_text.lower()
                child_location = f"{location}.{key_text}"
                if key_normalized in _FORBIDDEN_FIELD_NAMES:
                    errors.append(f"{child_location}: body, secret, environment, or path field")
                visit(child, child_location)
            return
        if isinstance(node, (list, tuple)):
            for index, child in enumerate(node):
                visit(child, f"{location}[{index}]")
            return
        if not isinstance(node, str):
            return
        if EMAIL_PATTERN.search(node):
            errors.append(f"{location}: email address")
        if SUBMISSION_LINK_PATTERN.search(node):
            errors.append(f"{location}: submission-system link")
        if any(token.lower() in node.lower() for token in PRIVATE_TOKENS):
            errors.append(f"{location}: private identifier")
        if _ABSOLUTE_PATH_PATTERN.search(node) or _PRIVATE_PATH_PATTERN.search(node):
            errors.append(f"{location}: filesystem path")
        if _SECRET_ASSIGNMENT_PATTERN.search(node) or _COMMON_TOKEN_PATTERN.search(node):
            errors.append(f"{location}: secret-like value")
        if _ENV_ASSIGNMENT_PATTERN.search(node):
            errors.append(f"{location}: environment assignment")
        if any(environment_value in node for environment_value in environment_values):
            errors.append(f"{location}: environment value")

    visit(value, "$")
    return list(dict.fromkeys(errors))


def validate_receipt(value: Any) -> list[str]:
    """Return structural and privacy errors for one receipt object."""

    errors: list[str] = []
    if not isinstance(value, Mapping):
        return ["$: receipt must be a JSON object"]

    actual_fields = set(value)
    missing = sorted(REQUIRED_RECEIPT_FIELDS - actual_fields)
    extra = sorted(actual_fields - REQUIRED_RECEIPT_FIELDS)
    if missing:
        errors.append("$: missing required field(s): " + ", ".join(missing))
    if extra:
        errors.append("$: unknown field(s): " + ", ".join(str(item) for item in extra))

    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append("$.schema_version: unsupported schema version")

    for field in ("provider", "model", "reasoning", "task_id", "thread_id"):
        if not _is_safe_identifier(value.get(field)):
            errors.append(f"$.{field}: unsafe or missing identifier")

    for field in ("invoked_at", "completed_at"):
        if _timestamp(value.get(field)) is None:
            errors.append(f"$.{field}: timestamp must be UTC and end in Z")
    invoked_at = _timestamp(value.get("invoked_at"))
    completed_at = _timestamp(value.get("completed_at"))
    if invoked_at is not None and completed_at is not None and completed_at < invoked_at:
        errors.append("$.completed_at: earlier than invoked_at")

    input_hashes = value.get("input_file_hashes")
    labels: set[str] = set()
    if not isinstance(input_hashes, list) or not input_hashes:
        errors.append("$.input_file_hashes: must be a non-empty array")
    else:
        for index, item in enumerate(input_hashes):
            location = f"$.input_file_hashes[{index}]"
            if not isinstance(item, Mapping) or set(item) != {"label", "sha256"}:
                errors.append(f"{location}: must contain only label and sha256")
                continue
            label = item.get("label")
            if not _is_safe_identifier(label):
                errors.append(f"{location}.label: unsafe logical identifier")
            elif label in labels:
                errors.append(f"{location}.label: duplicate label")
            else:
                labels.add(label)
            if not _is_sha256(item.get("sha256")):
                errors.append(f"{location}.sha256: invalid SHA-256 digest")

    for field in ("prompt_sha256", "schema_sha256", "output_sha256"):
        if not _is_sha256(value.get(field)):
            errors.append(f"$.{field}: invalid SHA-256 digest")

    validator = value.get("validator")
    if not isinstance(validator, Mapping):
        errors.append("$.validator: must be an object")
    else:
        validator_fields = set(validator)
        missing_validator = sorted(VALIDATOR_REQUIRED_FIELDS - validator_fields)
        extra_validator = sorted(
            validator_fields - VALIDATOR_REQUIRED_FIELDS - VALIDATOR_OPTIONAL_FIELDS
        )
        if missing_validator:
            errors.append(
                "$.validator: missing required field(s): " + ", ".join(missing_validator)
            )
        if extra_validator:
            errors.append(
                "$.validator: unknown field(s): "
                + ", ".join(str(item) for item in extra_validator)
            )
        if not _is_safe_identifier(validator.get("name")):
            errors.append("$.validator.name: unsafe or missing identifier")
        if validator.get("status") not in VALIDATOR_STATUSES:
            errors.append("$.validator.status: must be PASS or FAIL")
        if type(validator.get("error_count")) is not int or validator.get("error_count") < 0:
            errors.append("$.validator.error_count: must be a non-negative integer")
        codes = validator.get("codes")
        if codes is not None:
            if not isinstance(codes, list):
                errors.append("$.validator.codes: must be an array")
            else:
                if len(codes) > 64:
                    errors.append("$.validator.codes: must contain at most 64 codes")
                if all(isinstance(code, str) for code in codes) and len(codes) != len(set(codes)):
                    errors.append("$.validator.codes: codes must be unique")
                if any(not _is_safe_code(code) for code in codes):
                    errors.append("$.validator.codes: contains an unsafe code")

    status = value.get("status")
    if not isinstance(status, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{0,31}", status) is None:
        errors.append("$.status: must be an uppercase status code")

    errors.extend(scan_receipt_privacy(value))
    return list(dict.fromkeys(errors))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _validated_validator(validator: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        "name": validator.get("name"),
        "status": validator.get("status"),
        "error_count": validator.get("error_count"),
    }
    if "codes" in validator:
        result["codes"] = list(validator["codes"])
    return result


def create_receipt(
    *,
    provider: str,
    model: str,
    reasoning: str,
    task_id: str,
    thread_id: str,
    invoked_at: str,
    completed_at: str,
    input_file_hashes: Mapping[str, str],
    prompt_sha256: str,
    schema_sha256: str,
    output_sha256: str,
    validator: Mapping[str, Any],
    status: str,
) -> dict[str, Any]:
    """Build a receipt from already-derived metadata and digests only."""

    if not isinstance(input_file_hashes, Mapping) or not input_file_hashes:
        raise ValueError("input_file_hashes must be a non-empty mapping")
    input_entries = []
    for label, digest in sorted(input_file_hashes.items()):
        _validate_label(label)
        input_entries.append({"label": str(label), "sha256": digest})
    if not isinstance(validator, Mapping):
        raise TypeError("validator must be a mapping")

    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "provider": provider,
        "model": model,
        "reasoning": reasoning,
        "task_id": task_id,
        "thread_id": thread_id,
        "invoked_at": invoked_at,
        "completed_at": completed_at,
        "input_file_hashes": input_entries,
        "prompt_sha256": prompt_sha256,
        "schema_sha256": schema_sha256,
        "output_sha256": output_sha256,
        "validator": _validated_validator(validator),
        "status": status,
    }
    errors = validate_receipt(receipt)
    if errors:
        raise ValueError("Invalid model-call receipt: " + "; ".join(errors))
    return receipt


def create_receipt_from_artifacts(
    *,
    provider: str,
    model: str,
    reasoning: str,
    task_id: str,
    thread_id: str,
    invoked_at: str,
    completed_at: str,
    input_files: Mapping[str, Path],
    prompt: str | bytes,
    schema: Path | bytes,
    output: Path | bytes | str,
    validator: Mapping[str, Any],
    status: str,
) -> dict[str, Any]:
    """Hash call artifacts in memory and return a receipt with no bodies."""

    schema_digest = _artifact_digest(schema, allow_text=False)
    return create_receipt(
        provider=provider,
        model=model,
        reasoning=reasoning,
        task_id=task_id,
        thread_id=thread_id,
        invoked_at=invoked_at,
        completed_at=completed_at,
        input_file_hashes=hash_input_files(input_files),
        prompt_sha256=_artifact_digest(prompt),
        schema_sha256=schema_digest,
        output_sha256=_artifact_digest(output),
        validator=validator,
        status=status,
    )


def _receipt_input_hashes(receipt: Mapping[str, Any]) -> dict[str, str]:
    return {
        item["label"]: item["sha256"] for item in receipt["input_file_hashes"]
    }


def verify_receipt_hashes(
    receipt: Mapping[str, Any],
    *,
    input_files: Mapping[str, Path] | None = None,
    prompt: str | bytes | None = None,
    schema: Path | bytes | None = None,
    output: Path | bytes | str | None = None,
) -> None:
    """Verify supplied artifacts against a receipt without exposing bodies."""

    structural_errors = validate_receipt(receipt)
    if structural_errors:
        raise ValueError("Cannot verify invalid receipt: " + "; ".join(structural_errors))

    errors: list[str] = []
    expected_inputs = _receipt_input_hashes(receipt)
    if input_files is not None:
        supplied_labels = set(input_files)
        expected_labels = set(expected_inputs)
        if supplied_labels != expected_labels:
            errors.append("input_file_hashes labels do not match")
        for label in sorted(expected_labels & supplied_labels):
            try:
                actual = sha256_file(input_files[label])
            except (OSError, TypeError, ValueError):
                errors.append(f"input_file_hashes[{label}]: could not hash input")
                continue
            if actual != expected_inputs[label]:
                errors.append(f"input_file_hashes[{label}]: digest mismatch")

    if prompt is not None and _artifact_digest(prompt) != receipt["prompt_sha256"]:
        errors.append("prompt_sha256: digest mismatch")
    if schema is not None:
        try:
            actual_schema = _artifact_digest(schema, allow_text=False)
        except (OSError, TypeError, ValueError):
            errors.append("schema_sha256: could not hash schema")
        else:
            if actual_schema != receipt["schema_sha256"]:
                errors.append("schema_sha256: digest mismatch")
    if output is not None and _artifact_digest(output) != receipt["output_sha256"]:
        errors.append("output_sha256: digest mismatch")

    if errors:
        raise ValueError("Receipt hash verification failed: " + "; ".join(errors))


def write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    """Atomically create one read-only receipt and refuse replacement attempts."""

    structural_errors = validate_receipt(receipt)
    if structural_errors:
        raise ValueError("Cannot write invalid receipt: " + "; ".join(structural_errors))

    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(f"Receipt already exists: {path}")

    payload = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o400)
            os.fsync(stream.fileno())
        try:
            # A hard-link publication is atomic and fails with EEXIST instead
            # of replacing a receipt that another writer won the race for. The
            # target inherits the temporary inode's read-only mode.
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(f"Receipt already exists: {path}") from None
        _fsync_directory(path.parent)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _fsync_directory(directory: Path) -> None:
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


# These names make the small public API discoverable for callers that use
# "build" or "verify" terminology while keeping one implementation.
build_receipt = create_receipt
verify_hashes = verify_receipt_hashes


__all__ = [
    "SCHEMA_VERSION",
    "build_receipt",
    "create_receipt",
    "create_receipt_from_artifacts",
    "hash_input_files",
    "scan_receipt_privacy",
    "sha256_bytes",
    "sha256_file",
    "utc_now",
    "validate_receipt",
    "verify_hashes",
    "verify_receipt_hashes",
    "write_receipt",
]
