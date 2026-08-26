"""Canonical scientific duplicate comparison for R006e screening v2."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any, TypeAlias

from scripts.experiments.r006e_screening_schema_v2 import (
    ALLOWED_DUPLICATE_EXCLUSIONS,
    COMPARABLE_SCIENTIFIC_FIELDS,
    DOCUMENT_TYPES,
    OPERATIONAL_FIELD_NAMES,
    SCHEMA_VERSION,
    SchemaValidationError,
    validate_comparable_scientific_payload,
    validate_schema,
)


class DuplicateIntegrityError(ValueError):
    """Raised when scientific payloads cannot be compared safely."""


ScientificPayloads: TypeAlias = Mapping[str, Any]
DuplicateComparison: TypeAlias = dict[str, Any]


def raw_byte_sha256(data: bytes) -> str:
    """Hash role artifact bytes without making them scientific content."""

    if not isinstance(data, bytes):
        raise TypeError("raw artifact data must be bytes")
    return hashlib.sha256(data).hexdigest()


def _reject_constant(token: str) -> None:
    raise DuplicateIntegrityError(f"non-finite JSON constant: {token}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateIntegrityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json_loads(text: str, path: str) -> Any:
    try:
        return json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_reject_duplicate_keys,
        )
    except DuplicateIntegrityError:
        raise
    except (TypeError, json.JSONDecodeError) as exc:
        raise DuplicateIntegrityError(f"malformed JSON at {path}: {exc}") from exc


def _canonicalize(value: Any, path: str) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            if key in ALLOWED_DUPLICATE_EXCLUSIONS:
                continue
            if key in OPERATIONAL_FIELD_NAMES:
                raise DuplicateIntegrityError(f"unexpected operational field at {path}.{key}")
            normalized[key] = _canonicalize(value[key], f"{path}.{key}")
        return normalized
    if isinstance(value, list):
        return [_canonicalize(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, float) and not math.isfinite(value):
        raise DuplicateIntegrityError(f"non-finite JSON number at {path}")
    return value


def _normalize_payload_structure(payload: Mapping[str, Any]) -> dict[str, Any]:
    try:
        validate_comparable_scientific_payload(payload)
    except SchemaValidationError as exc:
        raise DuplicateIntegrityError(str(exc)) from exc

    normalized = copy.deepcopy(dict(payload))
    for index, row in enumerate(normalized["replication"]):
        text = row["fit_diagnostics_json"]
        if not isinstance(text, str):
            raise DuplicateIntegrityError(
                f"fit_diagnostics_json must be a string at replication[{index}]"
            )
        parsed = _strict_json_loads(text, f"replication[{index}].fit_diagnostics_json")
        if not isinstance(parsed, Mapping):
            raise DuplicateIntegrityError(
                "fit_diagnostics_json must decode to a JSON object at "
                f"replication[{index}]"
            )
        canonical_diagnostics = _canonicalize(
            parsed, f"replication[{index}].fit_diagnostics_json"
        )
        row["fit_diagnostics_json"] = json.dumps(
            canonical_diagnostics,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    return _canonicalize(normalized, "scientific_payload")


def semantic_digest(payload: ScientificPayloads) -> str:
    """Validate and SHA-256 hash canonical comparable scientific content."""

    canonical = json.dumps(
        _normalized_payload(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def recompute_scientific_digests(
    payload: ScientificPayloads,
) -> dict[str, str]:
    """Recompute component digests after strict structural normalization."""

    normalized = _normalize_payload_structure(payload)
    return {
        name: _canonical_sha256(normalized[name])
        for name in COMPARABLE_SCIENTIFIC_FIELDS
    }


def _normalized_payload(payload: ScientificPayloads) -> dict[str, Any]:
    normalized = _normalize_payload_structure(payload)
    claims = (
        ("semantic_replication_sha256", "replication"),
        ("semantic_summary_sha256", "summary"),
    )
    for result_field, payload_name in claims:
        expected = _canonical_sha256(normalized[payload_name])
        if normalized["result"][result_field] != expected:
            raise DuplicateIntegrityError(
                f"result.{result_field} does not match canonical {payload_name} digest"
            )
    return normalized


def _mismatch_paths(left: Any, right: Any, path: str) -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, Mapping):
        mismatches: list[str] = []
        for key in sorted(set(left) | set(right)):
            child_path = f"{path}.{key}" if path else key
            if key not in left or key not in right:
                mismatches.append(child_path)
            else:
                mismatches.extend(_mismatch_paths(left[key], right[key], child_path))
        return mismatches
    if isinstance(left, list):
        mismatches = []
        for index in range(max(len(left), len(right))):
            child_path = f"{path}[{index}]"
            if index >= len(left) or index >= len(right):
                mismatches.append(child_path)
            else:
                mismatches.extend(_mismatch_paths(left[index], right[index], child_path))
        return mismatches
    return [] if _canonical_sha256(left) == _canonical_sha256(right) else [path]


def compare_scientific_attempts(
    primary: ScientificPayloads,
    repeat: ScientificPayloads,
) -> DuplicateComparison:
    """Compare exactly replication, summary, and result semantically."""

    primary_normalized = _normalized_payload(primary)
    repeat_normalized = _normalized_payload(repeat)
    primary_digests = {
        name: _canonical_sha256(primary_normalized[name])
        for name in COMPARABLE_SCIENTIFIC_FIELDS
    }
    repeat_digests = {
        name: _canonical_sha256(repeat_normalized[name])
        for name in COMPARABLE_SCIENTIFIC_FIELDS
    }
    mismatches: list[str] = []
    for name in COMPARABLE_SCIENTIFIC_FIELDS:
        mismatches.extend(
            _mismatch_paths(primary_normalized[name], repeat_normalized[name], name)
        )
    all_digests_match = all(
        primary_digests[name] == repeat_digests[name]
        for name in COMPARABLE_SCIENTIFIC_FIELDS
    )
    comparison = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["duplicate_comparison"],
        "status": "PASS" if all_digests_match else "FAIL",
        "compared_payloads": list(COMPARABLE_SCIENTIFIC_FIELDS),
        "primary_replication_sha256": primary_digests["replication"],
        "repeat_replication_sha256": repeat_digests["replication"],
        "primary_summary_sha256": primary_digests["summary"],
        "repeat_summary_sha256": repeat_digests["summary"],
        "primary_result_sha256": primary_digests["result"],
        "repeat_result_sha256": repeat_digests["result"],
        "mismatch_paths": mismatches,
    }
    try:
        validate_schema("duplicate_comparison", comparison)
    except SchemaValidationError as exc:
        raise DuplicateIntegrityError(str(exc)) from exc
    return comparison
