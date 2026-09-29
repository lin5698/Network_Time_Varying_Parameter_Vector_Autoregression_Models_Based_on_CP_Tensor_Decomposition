"""Deterministic, fail-closed output publication for R006e screening v2."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import secrets
import stat
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from scripts.experiments.r006e_duplicate_audit_v2 import recompute_scientific_digests
from scripts.experiments.r006e_native_gates import evaluate_screening_gate
from scripts.experiments.r006e_native_protocol import R006EConfig, SCREENING_SEEDS
from scripts.experiments.r006e_screening_executor_v2 import CellExecution
from scripts.experiments.r006e_screening_schema_v2 import (
    DOCUMENT_TYPES,
    DIAGNOSTIC_FIELDS,
    FORMAL_REPLICATION_FIELDS,
    REPLICATION_IDENTITIES,
    RECORD_CARDINALITIES,
    RESOURCE_FIELDS,
    ROW_JOURNAL_FIELDS,
    SCHEMA_VERSION,
    SCIENTIFIC_RESULT_FIELDS,
    SchemaValidationError,
    SUMMARY_FIELDS,
    SUMMARY_IDENTITIES,
    SUMMARY_ROW_FIELDS,
    TERMINAL_FIELDS,
    MANIFEST_FIELDS,
    validate_diagnostic_record,
    validate_formal_replication_record,
    validate_resource_record,
    validate_row_journal_record,
    validate_schema,
)


PUBLICATION_ORDER = (
    "row_journal",
    "replication",
    "diagnostic",
    "resource",
    "summary",
    "result",
    "terminal",
    "manifest",
)
ROLE_FILE_NAMES = MappingProxyType(
    {
        "row_journal": "screening_row_journal.jsonl",
        "replication": "screening_replications.csv",
        "diagnostic": "screening_diagnostics.jsonl",
        "resource": "screening_resources.jsonl",
        "summary": "screening_summary.csv",
        "result": "screening_results.json",
        "terminal": "screening_terminal.json",
        "manifest": "screening_manifest.json",
    }
)
_HAS_DESCRIPTOR_RELATIVE_LINK = (
    os.link in os.supports_dir_fd and os.unlink in os.supports_dir_fd
)


class OutputIntegrityError(ValueError):
    """Raised when serialized or published role output violates v2 governance."""


@dataclass(frozen=True)
class SummaryBuild:
    rows: tuple[Mapping[str, object], ...]
    status: str
    identity_completeness: bool


@dataclass(frozen=True)
class RoleMetadata:
    decision_id: str
    attempt_id: str
    role: str
    pair_claim_sha256: str
    role_start_sha256: str
    construction_sha256: str
    config_sha256: str
    candidate_sha256: str
    provenance_sha256: str
    started_at: str
    finished_at: str
    generated_at: str


@dataclass(frozen=True)
class RoleArtifacts:
    files: Mapping[str, bytes]


@dataclass(frozen=True)
class PublishedRoleSnapshot:
    root: Path
    root_identity: tuple[int, int]
    published_names: tuple[str, ...]
    paths: tuple[Path, ...]
    fingerprints: tuple[tuple[int, int, int, int, str], ...]
    _lease: _DirectoryLease

    def close(self) -> None:
        self._lease.close()


class _DirectoryLease:
    def __init__(self, descriptor: int) -> None:
        self._descriptor = descriptor
        self._lock = threading.Lock()

    def borrow(self) -> int:
        with self._lock:
            if self._descriptor < 0:
                raise OutputIntegrityError("published root descriptor is closed")
            return self._descriptor

    def close(self) -> None:
        with self._lock:
            if self._descriptor >= 0:
                os.close(self._descriptor)
                self._descriptor = -1


def _validate_json_tree(
    value: object,
    location: str = "$",
    active: set[int] | None = None,
) -> None:
    if value is None or type(value) in {str, bool, int}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise OutputIntegrityError(f"non-finite JSON number at {location}")
        return
    if type(value) not in {dict, list}:
        raise OutputIntegrityError(f"unsupported JSON value at {location}")
    seen = set() if active is None else active
    identity = id(value)
    if identity in seen:
        raise OutputIntegrityError(f"cyclic JSON value at {location}")
    seen.add(identity)
    try:
        if type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise OutputIntegrityError(f"non-string JSON key at {location}")
                _validate_json_tree(item, f"{location}.{key}", seen)
        else:
            for index, item in enumerate(value):
                _validate_json_tree(item, f"{location}[{index}]", seen)
    finally:
        seen.remove(identity)


def _encode_json_scalar(value: object) -> str:
    if value is None:
        return ""
    _validate_json_tree(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise OutputIntegrityError(f"non-canonical CSV value: {exc}") from exc


def _serialize_csv(
    records: Sequence[Mapping[str, object]],
    fields: tuple[str, ...],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(fields)
    for record in records:
        writer.writerow([_encode_json_scalar(record[field]) for field in fields])
    return stream.getvalue().encode("utf-8")


def _strict_json_scalar(text: str, location: str) -> object:
    if text == "":
        return None

    def reject_constant(token: str) -> None:
        raise OutputIntegrityError(f"non-finite JSON constant at {location}: {token}")

    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise OutputIntegrityError(f"duplicate JSON key at {location}: {key}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            parse_constant=reject_constant,
            object_pairs_hook=reject_pairs,
        )
    except OutputIntegrityError:
        raise
    except json.JSONDecodeError as exc:
        raise OutputIntegrityError(f"invalid JSON scalar at {location}: {exc}") from exc


def _parse_csv(
    payload: bytes,
    fields: tuple[str, ...],
) -> list[dict[str, object]]:
    if b"\r" in payload or not payload.endswith(b"\n"):
        raise OutputIntegrityError("CSV must use LF endings and end with LF")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OutputIntegrityError("CSV must be UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise OutputIntegrityError("CSV header is missing or malformed") from exc
    if tuple(header) != fields:
        raise OutputIntegrityError("CSV header/order mismatch")
    records: list[dict[str, object]] = []
    try:
        for row_index, row in enumerate(reader):
            if len(row) != len(fields):
                raise OutputIntegrityError(f"CSV row width mismatch at {row_index}")
            records.append(
                {
                    field: _strict_json_scalar(value, f"row[{row_index}].{field}")
                    for field, value in zip(fields, row)
                }
            )
    except csv.Error as exc:
        raise OutputIntegrityError(f"malformed CSV: {exc}") from exc
    return records


def _identities(records: Sequence[Mapping[str, object]]) -> tuple[tuple[object, ...], ...]:
    fields = ("seed", "rho", "a3", "eta", "method")
    return tuple(tuple(record[field] for field in fields) for record in records)


def serialize_replication_csv(execution: CellExecution) -> bytes:
    """Serialize the immutable Task 4 aggregate in frozen identity order."""

    if not isinstance(execution, CellExecution):
        raise OutputIntegrityError("execution must be a CellExecution")
    records = execution.replications
    try:
        for record in records:
            validate_formal_replication_record(record)
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    if _identities(records) != REPLICATION_IDENTITIES:
        raise OutputIntegrityError("replication identities/order mismatch")
    return _serialize_csv(records, FORMAL_REPLICATION_FIELDS)


def parse_replication_csv(payload: bytes) -> tuple[Mapping[str, object], ...]:
    """Strictly parse and validate canonical replication CSV bytes."""

    records = _parse_csv(payload, FORMAL_REPLICATION_FIELDS)
    try:
        for record in records:
            validate_formal_replication_record(record)
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    if _identities(records) != REPLICATION_IDENTITIES:
        raise OutputIntegrityError("replication identities/order mismatch")
    canonical = _serialize_csv(records, FORMAL_REPLICATION_FIELDS)
    if canonical != payload:
        raise OutputIntegrityError("replication CSV is not canonical")
    return tuple(records)


def _canonical_json_bytes(value: object) -> bytes:
    _validate_json_tree(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OutputIntegrityError(f"non-canonical JSON value: {exc}") from exc


def _serialize_jsonl(
    records: Sequence[Mapping[str, object]],
    fields: tuple[str, ...],
    validator: Any,
) -> bytes:
    lines: list[bytes] = []
    try:
        for record in records:
            validator(record)
            if tuple(record) != fields:
                raise OutputIntegrityError("JSONL field order mismatch")
            lines.append(_canonical_json_bytes(dict(record)))
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    if _identities(records) != REPLICATION_IDENTITIES:
        raise OutputIntegrityError("JSONL identities/order mismatch")
    return b"\n".join(lines) + b"\n"


def _strict_json_object(payload: bytes, location: str) -> dict[str, object]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OutputIntegrityError(f"JSON must be UTF-8 at {location}") from exc

    def reject_constant(token: str) -> None:
        raise OutputIntegrityError(f"non-finite JSON constant at {location}: {token}")

    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise OutputIntegrityError(f"duplicate JSON key at {location}: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            text,
            parse_constant=reject_constant,
            object_pairs_hook=reject_pairs,
        )
    except OutputIntegrityError:
        raise
    except json.JSONDecodeError as exc:
        raise OutputIntegrityError(f"malformed JSON at {location}: {exc}") from exc
    if type(value) is not dict:
        raise OutputIntegrityError(f"JSON record must be an object at {location}")
    _validate_json_tree(value, location)
    return value


def _parse_jsonl(
    payload: bytes,
    fields: tuple[str, ...],
    validator: Any,
) -> tuple[Mapping[str, object], ...]:
    if b"\r" in payload or not payload.endswith(b"\n"):
        raise OutputIntegrityError("JSONL must use LF endings and end with LF")
    raw_lines = payload[:-1].split(b"\n")
    if not raw_lines or any(not line for line in raw_lines):
        raise OutputIntegrityError("JSONL contains an empty record")
    records = tuple(
        _strict_json_object(line, f"line[{index}]")
        for index, line in enumerate(raw_lines)
    )
    try:
        for record in records:
            validator(record)
            if tuple(record) != fields:
                raise OutputIntegrityError("JSONL field order mismatch")
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    if _identities(records) != REPLICATION_IDENTITIES:
        raise OutputIntegrityError("JSONL identities/order mismatch")
    if _serialize_jsonl(records, fields, validator) != payload:
        raise OutputIntegrityError("JSONL is not canonical")
    return records


def serialize_diagnostic_jsonl(execution: CellExecution) -> bytes:
    return _serialize_jsonl(execution.diagnostics, DIAGNOSTIC_FIELDS, validate_diagnostic_record)


def parse_diagnostic_jsonl(payload: bytes) -> tuple[Mapping[str, object], ...]:
    return _parse_jsonl(payload, DIAGNOSTIC_FIELDS, validate_diagnostic_record)


def serialize_resource_jsonl(execution: CellExecution) -> bytes:
    return _serialize_jsonl(execution.resources, RESOURCE_FIELDS, validate_resource_record)


def parse_resource_jsonl(payload: bytes) -> tuple[Mapping[str, object], ...]:
    return _parse_jsonl(payload, RESOURCE_FIELDS, validate_resource_record)


def serialize_row_journal_jsonl(execution: CellExecution) -> bytes:
    return _serialize_jsonl(
        execution.row_journals, ROW_JOURNAL_FIELDS, validate_row_journal_record
    )


def parse_row_journal_jsonl(payload: bytes) -> tuple[Mapping[str, object], ...]:
    return _parse_jsonl(payload, ROW_JOURNAL_FIELDS, validate_row_journal_record)


def _canonical_sorted_json(value: object) -> str:
    _validate_json_tree(value)
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise OutputIntegrityError(f"non-canonical JSON value: {exc}") from exc


def _require_complete_aggregate(execution: CellExecution) -> None:
    if not isinstance(execution, CellExecution):
        raise OutputIntegrityError("execution must be a CellExecution")
    specifications = (
        (execution.replications, validate_formal_replication_record, "replication"),
        (execution.diagnostics, validate_diagnostic_record, "diagnostic"),
        (execution.resources, validate_resource_record, "resource"),
        (execution.row_journals, validate_row_journal_record, "row_journal"),
    )
    try:
        for records, validator, name in specifications:
            for record in records:
                validator(record)
            if _identities(records) != REPLICATION_IDENTITIES:
                raise OutputIntegrityError(f"{name} identities/order mismatch")
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc


def _summary_from_native_gate(gate: object) -> SummaryBuild:
    """Freeze and cross-check one native gate verdict."""

    if type(gate) is not dict or gate.get("status") not in {"PASS", "FAIL"}:
        raise OutputIntegrityError("native gate returned an invalid verdict")
    cells = gate.get("cells")
    if type(cells) is not list or len(cells) != 8:
        raise OutputIntegrityError("gate adapter must return exactly eight cells")
    rows: list[Mapping[str, object]] = []
    for index, (cell, identity) in enumerate(zip(cells, SUMMARY_IDENTITIES)):
        if type(cell) is not dict:
            raise OutputIntegrityError(f"gate cell {index} must be an object")
        actual_identity = (cell.get("rho"), cell.get("a3"), cell.get("eta"))
        if actual_identity != identity:
            raise OutputIntegrityError(f"gate cell identity/order mismatch at {index}")
        conditions = cell.get("conditions")
        if type(conditions) is not dict or tuple(conditions) != SUMMARY_FIELDS:
            raise OutputIntegrityError(f"gate condition schema/order mismatch at {index}")
        if any(type(conditions[name]) is not bool for name in SUMMARY_FIELDS):
            raise OutputIntegrityError(f"gate conditions must be boolean at {index}")
        expected_failed = [name for name in SUMMARY_FIELDS if not conditions[name]]
        if cell.get("failed_conditions") != expected_failed:
            raise OutputIntegrityError(f"failed-condition mismatch at {index}")
        passed = all(conditions.values())
        if cell.get("passed") is not passed:
            raise OutputIntegrityError(f"gate cell status mismatch at {index}")
        audit_values = cell.get("audit_values", {})
        if type(audit_values) is not dict:
            raise OutputIntegrityError(f"audit_values must be an object at {index}")
        values: dict[str, object] = {
            "rho": identity[0],
            "a3": identity[1],
            "eta": identity[2],
            "passed": passed,
            **conditions,
            "failed_conditions_json": _canonical_sorted_json(expected_failed),
            "audit_values_json": _canonical_sorted_json(audit_values),
        }
        rows.append({field: values[field] for field in SUMMARY_ROW_FIELDS})
    recomputed_status = "PASS" if all(row["passed"] for row in rows) else "FAIL"
    passed_cells = sum(bool(row["passed"]) for row in rows)
    if gate.get("total_cells") != 8 or gate.get("passed_cells") != passed_cells:
        raise OutputIntegrityError("gate cell counts do not match recomputed cells")
    if gate["status"] != recomputed_status:
        raise OutputIntegrityError("gate status does not match recomputed cells")
    return SummaryBuild(
        rows=tuple(rows),
        status=recomputed_status,
        identity_completeness=True,
    )


def build_summary_rows(
    execution: CellExecution,
    *,
    config: R006EConfig,
) -> SummaryBuild:
    """Build eight frozen summary rows from the native screening gate."""

    _require_complete_aggregate(execution)
    if not isinstance(config, R006EConfig):
        raise OutputIntegrityError("config must be an R006EConfig")
    gate = evaluate_screening_gate(
        [dict(row) for row in execution.replications],
        config=config,
    )
    return _summary_from_native_gate(gate)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: str, name: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise OutputIntegrityError(f"{name} must be lowercase SHA-256")


def _json_document(value: Mapping[str, object], fields: tuple[str, ...]) -> bytes:
    if tuple(value) != fields:
        raise OutputIntegrityError("JSON document field order mismatch")
    return _canonical_json_bytes(dict(value)) + b"\n"


def build_role_artifacts(
    execution: CellExecution,
    *,
    config: R006EConfig,
    metadata: RoleMetadata,
) -> RoleArtifacts:
    """Build the exact eight immutable role artifacts without publication."""

    _require_complete_aggregate(execution)
    if not isinstance(metadata, RoleMetadata):
        raise OutputIntegrityError("metadata must be RoleMetadata")
    for name in (
        "pair_claim_sha256",
        "role_start_sha256",
        "construction_sha256",
        "config_sha256",
        "candidate_sha256",
        "provenance_sha256",
    ):
        _require_sha256(getattr(metadata, name), name)
    if metadata.role not in {"primary", "repeat"}:
        raise OutputIntegrityError("metadata role must be primary or repeat")
    for resource, journal in zip(execution.resources, execution.row_journals):
        if (
            resource["attempt_id"] != metadata.attempt_id
            or journal["attempt_id"] != metadata.attempt_id
            or resource["role"] != metadata.role
            or journal["role"] != metadata.role
        ):
            raise OutputIntegrityError("aggregate attempt/role metadata mismatch")

    summary = build_summary_rows(execution, config=config)
    replication_records = [dict(row) for row in execution.replications]
    summary_records = [dict(row) for row in summary.rows]
    result_values: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["scientific_result"],
        "status": summary.status,
        "semantic_replication_sha256": "0" * 64,
        "semantic_summary_sha256": "0" * 64,
        "construction_sha256": metadata.construction_sha256,
        "config_sha256": metadata.config_sha256,
        "candidate_sha256": metadata.candidate_sha256,
        "provenance_sha256": metadata.provenance_sha256,
        "seed_ids": list(SCREENING_SEEDS),
        "identity_completeness": summary.identity_completeness,
        "evaluation_classification": "simulation-only",
    }
    result = {field: result_values[field] for field in SCIENTIFIC_RESULT_FIELDS}
    digests = recompute_scientific_digests(
        {
            "replication": replication_records,
            "summary": summary_records,
            "result": result,
        }
    )
    result["semantic_replication_sha256"] = digests["replication"]
    result["semantic_summary_sha256"] = digests["summary"]
    try:
        validate_schema("scientific_result", result)
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc

    files: dict[str, bytes] = {
        "row_journal": serialize_row_journal_jsonl(execution),
        "replication": serialize_replication_csv(execution),
        "diagnostic": serialize_diagnostic_jsonl(execution),
        "resource": serialize_resource_jsonl(execution),
        "summary": _serialize_csv(summary.rows, SUMMARY_ROW_FIELDS),
        "result": _json_document(result, SCIENTIFIC_RESULT_FIELDS),
    }
    terminal_values: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["terminal"],
        "decision_id": metadata.decision_id,
        "attempt_id": metadata.attempt_id,
        "role": metadata.role,
        "status": summary.status,
        "pair_claim_sha256": metadata.pair_claim_sha256,
        "role_start_sha256": metadata.role_start_sha256,
        "replication_sha256": _sha256(files["replication"]),
        "summary_sha256": _sha256(files["summary"]),
        "result_sha256": _sha256(files["result"]),
        "diagnostics_sha256": _sha256(files["diagnostic"]),
        "resources_sha256": _sha256(files["resource"]),
        "row_journal_sha256": _sha256(files["row_journal"]),
        "started_at": metadata.started_at,
        "finished_at": metadata.finished_at,
        "exit_code": 0,
        "failure_code": None,
        "failure_reason": None,
    }
    terminal = {field: terminal_values[field] for field in TERMINAL_FIELDS}
    try:
        validate_schema("terminal", terminal)
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    files["terminal"] = _json_document(terminal, TERMINAL_FIELDS)

    identity_payload = _canonical_sorted_json(
        [list(identity) for identity in REPLICATION_IDENTITIES]
    ).encode("utf-8")
    manifest_values: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["manifest"],
        "decision_id": metadata.decision_id,
        "attempt_id": metadata.attempt_id,
        "role": metadata.role,
        "status": summary.status,
        "pair_claim_sha256": metadata.pair_claim_sha256,
        "role_start_sha256": metadata.role_start_sha256,
        "terminal_sha256": _sha256(files["terminal"]),
        "replication_sha256": _sha256(files["replication"]),
        "summary_sha256": _sha256(files["summary"]),
        "result_sha256": _sha256(files["result"]),
        "diagnostics_sha256": _sha256(files["diagnostic"]),
        "resources_sha256": _sha256(files["resource"]),
        "row_journal_sha256": _sha256(files["row_journal"]),
        "replication_count": RECORD_CARDINALITIES["replication"],
        "summary_count": RECORD_CARDINALITIES["summary"],
        "diagnostic_count": RECORD_CARDINALITIES["diagnostic"],
        "resource_count": RECORD_CARDINALITIES["resource"],
        "row_journal_count": RECORD_CARDINALITIES["row_journal"],
        "identity_set_sha256": _sha256(identity_payload),
        "generated_at": metadata.generated_at,
    }
    manifest = {field: manifest_values[field] for field in MANIFEST_FIELDS}
    try:
        validate_schema("manifest", manifest)
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    files["manifest"] = _json_document(manifest, MANIFEST_FIELDS)
    return RoleArtifacts(files=MappingProxyType({name: files[name] for name in PUBLICATION_ORDER}))


def _require_directory_binding(
    root: Path,
    descriptor: int,
    expected: tuple[int, int],
) -> None:
    pinned = os.fstat(descriptor)
    if (pinned.st_dev, pinned.st_ino) != expected:
        raise OutputIntegrityError("publication root descriptor identity changed")
    try:
        bound = os.stat(root, follow_symlinks=False)
    except OSError as exc:
        raise OutputIntegrityError("publication root binding changed") from exc
    if not os.path.isdir(root) or (bound.st_dev, bound.st_ino) != expected:
        raise OutputIntegrityError("publication root binding changed")


def _exclusive_publish_at(
    root: Path,
    root_fd: int,
    root_identity: tuple[int, int],
    name: str,
    payload: bytes,
) -> tuple[int, int, int, int, str]:
    """Durably hard-link one new file relative to a pinned directory."""

    if not _HAS_DESCRIPTOR_RELATIVE_LINK:
        raise OutputIntegrityError("descriptor-relative hard-link publication unavailable")
    temporary = f".r006e-v2-output-{secrets.token_hex(16)}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600, dir_fd=root_fd)
    linked = False
    fingerprint: tuple[int, int, int, int, str] | None = None
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _require_directory_binding(root, root_fd, root_identity)
        os.link(
            temporary,
            name,
            src_dir_fd=root_fd,
            dst_dir_fd=root_fd,
            follow_symlinks=False,
        )
        linked = True
        read_flags = (
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        source_fd = os.open(temporary, read_flags, dir_fd=root_fd)
        try:
            destination_fd = os.open(name, read_flags, dir_fd=root_fd)
            try:
                source_fingerprint = _fingerprint_descriptor(
                    source_fd, temporary, expected_payload=payload
                )
                fingerprint = _fingerprint_descriptor(
                    destination_fd, name, expected_payload=payload
                )
            finally:
                os.close(destination_fd)
        finally:
            os.close(source_fd)
        if source_fingerprint[:2] != fingerprint[:2]:
            raise OutputIntegrityError(f"published file inode binding changed: {name}")
        os.fsync(root_fd)
        _require_directory_binding(root, root_fd, root_identity)
    finally:
        try:
            os.unlink(temporary, dir_fd=root_fd)
            os.fsync(root_fd)
        except FileNotFoundError:
            pass
    if not linked:
        raise OutputIntegrityError(f"failed to publish {name}")
    if fingerprint is None:
        raise OutputIntegrityError(f"published file fingerprint missing: {name}")
    return fingerprint


def _fingerprint_descriptor(
    descriptor: int,
    name: str,
    *,
    expected_payload: bytes | None = None,
) -> tuple[int, int, int, int, str]:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode):
        raise OutputIntegrityError(f"published file is not regular: {name}")
    chunks: list[bytes] = []
    while chunk := os.read(descriptor, 1024 * 1024):
        chunks.append(chunk)
    after = os.fstat(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity:
        raise OutputIntegrityError(f"published file changed while reading: {name}")
    payload = b"".join(chunks)
    fingerprint = (*after_identity, _sha256(payload))
    if expected_payload is not None and (
        after.st_size != len(expected_payload)
        or fingerprint[-1] != _sha256(expected_payload)
    ):
        raise OutputIntegrityError(f"published file payload changed: {name}")
    return fingerprint


def _fingerprint_at(root_fd: int, name: str) -> tuple[int, int, int, int, str]:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(name, flags, dir_fd=root_fd)
    try:
        fingerprint = _fingerprint_descriptor(descriptor, name)
    finally:
        os.close(descriptor)
    bound = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
    if fingerprint[:2] != (bound.st_dev, bound.st_ino):
        raise OutputIntegrityError(f"published file binding changed: {name}")
    return fingerprint


def publish_role_artifacts(root: Path, artifacts: RoleArtifacts) -> PublishedRoleSnapshot:
    """Publish all eight files exclusively in the frozen role order."""

    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise OutputIntegrityError("publication root must be an existing directory")
    if not isinstance(artifacts, RoleArtifacts) or tuple(artifacts.files) != PUBLICATION_ORDER:
        raise OutputIntegrityError("role artifacts/order mismatch")
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    root_fd = os.open(root, flags)
    try:
        stat = os.fstat(root_fd)
        root_identity = (stat.st_dev, stat.st_ino)
        _require_directory_binding(root, root_fd, root_identity)
        paths = tuple(root / ROLE_FILE_NAMES[name] for name in PUBLICATION_ORDER)
        fingerprints = tuple(
            _exclusive_publish_at(
                root, root_fd, root_identity, ROLE_FILE_NAMES[name], artifacts.files[name]
            )
            for name in PUBLICATION_ORDER
        )
        _require_directory_binding(root, root_fd, root_identity)
    except BaseException:
        os.close(root_fd)
        raise
    return PublishedRoleSnapshot(
        root=root,
        root_identity=root_identity,
        published_names=PUBLICATION_ORDER,
        paths=paths,
        fingerprints=fingerprints,
        _lease=_DirectoryLease(root_fd),
    )


def _stable_read(
    root: Path,
    root_fd: int,
    root_identity: tuple[int, int],
    name: str,
    expected: tuple[int, int, int, int, str],
) -> bytes:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    _require_directory_binding(root, root_fd, root_identity)
    try:
        descriptor = os.open(name, flags, dir_fd=root_fd)
    except OSError as exc:
        raise OutputIntegrityError(f"published file changed: {name}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OutputIntegrityError(f"published file is not regular: {name}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    current = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        _sha256(payload),
    )
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = current[:4]
    try:
        path_identity = _fingerprint_at(root_fd, name)
    except OSError as exc:
        raise OutputIntegrityError(f"published file changed: {name}") from exc
    if before_identity != after_identity or current != expected or path_identity != expected:
        raise OutputIntegrityError(f"published file drift: {name}")
    _require_directory_binding(root, root_fd, root_identity)
    return payload


def _parse_summary_csv(payload: bytes) -> tuple[Mapping[str, object], ...]:
    rows = _parse_csv(payload, SUMMARY_ROW_FIELDS)
    if len(rows) != 8:
        raise OutputIntegrityError("summary cardinality must equal 8")
    identities = tuple((row["rho"], row["a3"], row["eta"]) for row in rows)
    if identities != SUMMARY_IDENTITIES:
        raise OutputIntegrityError("summary identities/order mismatch")
    for index, row in enumerate(rows):
        if any(type(row[field]) is not bool for field in ("passed", *SUMMARY_FIELDS)):
            raise OutputIntegrityError(f"summary booleans invalid at {index}")
        failed = _strict_json_scalar(
            row["failed_conditions_json"], f"summary[{index}].failed_conditions_json"
        )
        audit = _strict_json_scalar(
            row["audit_values_json"], f"summary[{index}].audit_values_json"
        )
        expected_failed = [field for field in SUMMARY_FIELDS if not row[field]]
        if failed != expected_failed or type(audit) is not dict:
            raise OutputIntegrityError(f"summary JSON binding mismatch at {index}")
        if row["passed"] is not all(row[field] for field in SUMMARY_FIELDS):
            raise OutputIntegrityError(f"summary status mismatch at {index}")
    if _serialize_csv(rows, SUMMARY_ROW_FIELDS) != payload:
        raise OutputIntegrityError("summary CSV is not canonical")
    return tuple(rows)


def verify_published_role(
    snapshot: PublishedRoleSnapshot,
    *,
    config: R006EConfig,
) -> Mapping[str, bytes]:
    """Stably reread and independently verify every published role artifact."""

    if not isinstance(snapshot, PublishedRoleSnapshot):
        raise OutputIntegrityError("snapshot must be PublishedRoleSnapshot")
    if not isinstance(config, R006EConfig):
        raise OutputIntegrityError("config must be an R006EConfig")
    if snapshot.published_names != PUBLICATION_ORDER:
        raise OutputIntegrityError("snapshot publication order changed")
    root_fd = snapshot._lease.borrow()
    payloads = {
        name: _stable_read(
            snapshot.root,
            root_fd,
            snapshot.root_identity,
            ROLE_FILE_NAMES[name],
            fingerprint,
        )
        for name, fingerprint in zip(
            snapshot.published_names,
            snapshot.fingerprints,
        )
    }
    replications = parse_replication_csv(payloads["replication"])
    diagnostics = parse_diagnostic_jsonl(payloads["diagnostic"])
    resources = parse_resource_jsonl(payloads["resource"])
    journals = parse_row_journal_jsonl(payloads["row_journal"])
    summaries = _parse_summary_csv(payloads["summary"])
    native_summary = _summary_from_native_gate(
        evaluate_screening_gate(
            [dict(row) for row in replications],
            config=config,
        )
    )
    if _serialize_csv(native_summary.rows, SUMMARY_ROW_FIELDS) != payloads["summary"]:
        raise OutputIntegrityError("stored summary drift from native gate")
    result = _strict_json_object(payloads["result"], "result")
    terminal = _strict_json_object(payloads["terminal"], "terminal")
    manifest = _strict_json_object(payloads["manifest"], "manifest")
    try:
        validate_schema("scientific_result", result)
        validate_schema("terminal", terminal)
        validate_schema("manifest", manifest)
    except SchemaValidationError as exc:
        raise OutputIntegrityError(str(exc)) from exc
    if _json_document(result, SCIENTIFIC_RESULT_FIELDS) != payloads["result"]:
        raise OutputIntegrityError("result JSON is not canonical")
    if _json_document(terminal, TERMINAL_FIELDS) != payloads["terminal"]:
        raise OutputIntegrityError("terminal JSON is not canonical")
    if _json_document(manifest, MANIFEST_FIELDS) != payloads["manifest"]:
        raise OutputIntegrityError("manifest JSON is not canonical")

    for index, (replication, diagnostic, resource, journal) in enumerate(
        zip(replications, diagnostics, resources, journals)
    ):
        identities = {
            tuple(row[field] for field in ("seed", "rho", "a3", "eta", "method"))
            for row in (replication, diagnostic, resource, journal)
        }
        if len(identities) != 1:
            raise OutputIntegrityError(f"row journal identity drift at {index}")
        expected_journal_hashes = {
            "replication_sha256": _sha256(
                _canonical_sorted_json(dict(replication)).encode("utf-8")
            ),
            "diagnostic_sha256": _sha256(
                _canonical_sorted_json(dict(diagnostic)).encode("utf-8")
            ),
            "resource_sha256": _sha256(
                _canonical_sorted_json(dict(resource)).encode("utf-8")
            ),
        }
        if any(
            journal[field] != digest
            for field, digest in expected_journal_hashes.items()
        ):
            raise OutputIntegrityError(f"row journal hash drift at {index}")

    expected_raw = {
        "replication_sha256": _sha256(payloads["replication"]),
        "summary_sha256": _sha256(payloads["summary"]),
        "result_sha256": _sha256(payloads["result"]),
        "diagnostics_sha256": _sha256(payloads["diagnostic"]),
        "resources_sha256": _sha256(payloads["resource"]),
        "row_journal_sha256": _sha256(payloads["row_journal"]),
    }
    if any(terminal[field] != digest for field, digest in expected_raw.items()):
        raise OutputIntegrityError("terminal raw hash drift")
    if any(manifest[field] != digest for field, digest in expected_raw.items()):
        raise OutputIntegrityError("manifest raw hash drift")
    if manifest["terminal_sha256"] != _sha256(payloads["terminal"]):
        raise OutputIntegrityError("manifest terminal hash drift")
    expected_counts = {
        "replication_count": len(replications),
        "summary_count": len(summaries),
        "diagnostic_count": len(diagnostics),
        "resource_count": len(resources),
        "row_journal_count": len(journals),
    }
    if any(manifest[field] != count for field, count in expected_counts.items()):
        raise OutputIntegrityError("manifest cardinality drift")
    identity_payload = _canonical_sorted_json(
        [list(identity) for identity in REPLICATION_IDENTITIES]
    ).encode("utf-8")
    if manifest["identity_set_sha256"] != _sha256(identity_payload):
        raise OutputIntegrityError("manifest identity digest drift")
    semantic = recompute_scientific_digests(
        {
            "replication": [dict(row) for row in replications],
            "summary": [dict(row) for row in summaries],
            "result": result,
        }
    )
    if (
        result["semantic_replication_sha256"] != semantic["replication"]
        or result["semantic_summary_sha256"] != semantic["summary"]
    ):
        raise OutputIntegrityError("scientific result semantic digest drift")
    if (
        result["status"] != native_summary.status
        or terminal["status"] != native_summary.status
        or manifest["status"] != native_summary.status
    ):
        raise OutputIntegrityError("result status differs from recomputed gate")
    for field in ("decision_id", "attempt_id", "role", "pair_claim_sha256", "role_start_sha256"):
        if terminal[field] != manifest[field]:
            raise OutputIntegrityError(f"terminal/manifest metadata drift: {field}")
    return MappingProxyType(payloads)
