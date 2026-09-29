"""Independent, read-only result-to-claim audit for R006e screening v2.

This module deliberately does not import the v2 executor or its summary/result
builders.  It parses the published bytes, reconstructs the frozen identity
sets and screening gates, and treats stored summaries, results, terminals and
manifests as claims to be checked.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.experiments.r006e_duplicate_audit_v2 import (
    DuplicateIntegrityError,
    compare_scientific_attempts,
    recompute_scientific_digests,
)
from scripts.experiments.r006e_native_gates import evaluate_screening_gate
from scripts.experiments.r006e_native_protocol import R006EConfig
from scripts.experiments.r006e_screening_schema_v2 import (
    DIAGNOSTIC_FIELDS,
    FORMAL_REPLICATION_FIELDS,
    REPLICATION_IDENTITIES,
    RECORD_CARDINALITIES,
    RESOURCE_FIELDS,
    ROW_JOURNAL_FIELDS,
    SUMMARY_FIELDS,
    SUMMARY_IDENTITIES,
    SUMMARY_ROW_FIELDS,
    V2_CONTROL_ROOT,
    V2_PRIMARY_ROOT,
    V2_REPEAT_ROOT,
    SchemaValidationError,
    validate_diagnostic_record,
    validate_formal_replication_record,
    validate_resource_record,
    validate_row_journal_record,
    validate_schema,
)


ROLE_FILES = {
    "replication": "screening_replications.csv",
    "diagnostic": "screening_diagnostics.jsonl",
    "resource": "screening_resources.jsonl",
    "row_journal": "screening_row_journal.jsonl",
    "summary": "screening_summary.csv",
    "result": "screening_results.json",
    "terminal": "screening_terminal.json",
    "manifest": "screening_manifest.json",
}
PAIR_CLAIM_FILENAME = "screening_pair_claim.json"
ROLE_START_FILENAMES = {
    "primary": "screening_primary_start.json",
    "repeat": "screening_repeat_start.json",
}
ROLE_CONTROL_START_FILENAMES = {
    "primary": "screening_primary_start_claim.json",
    "repeat": "screening_repeat_start_claim.json",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_json(text: str, location: str) -> Any:
    def reject_constant(token: str) -> None:
        raise ValueError(f"non-finite JSON constant at {location}: {token}")

    def reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key at {location}: {key}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            parse_constant=reject_constant,
            object_pairs_hook=reject_pairs,
        )
    except (TypeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"malformed JSON at {location}: {exc}") from exc


def _strict_json_document(data: bytes, location: str) -> dict[str, Any]:
    if not data.endswith(b"\n") or b"\r" in data:
        raise ValueError(f"{location} must be LF terminated")
    try:
        value = _strict_json(data[:-1].decode("utf-8"), location)
    except UnicodeDecodeError as exc:
        raise ValueError(f"{location} must be UTF-8") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be an object")
    return value


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value), ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode("utf-8") + b"\n"


def _read_stable(path: Path) -> bytes:
    first = path.read_bytes()
    second = path.read_bytes()
    if first != second:
        raise ValueError(f"unstable artifact while reading {path.name}")
    return first


def _parse_scalar(value: str, location: str) -> Any:
    if value == "":
        return None
    return _strict_json(value, location)


def _encode_csv_scalar(value: Any) -> str:
    """Encode one parsed scalar using the publication's canonical CSV form."""
    if value is None:
        return ""
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _canonical_csv(records: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(fields)
    for record in records:
        writer.writerow([_encode_csv_scalar(record[field]) for field in fields])
    return stream.getvalue().encode("utf-8")


def _parse_csv(data: bytes, fields: Sequence[str], location: str) -> list[dict[str, Any]]:
    if b"\r" in data or not data.endswith(b"\n"):
        raise ValueError(f"{location} must use LF CSV")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{location} must be UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise ValueError(f"{location} has no header") from exc
    if tuple(header) != tuple(fields):
        raise ValueError(f"{location} header/order mismatch")
    records: list[dict[str, Any]] = []
    for index, row in enumerate(reader):
        if len(row) != len(fields):
            raise ValueError(f"{location} row width mismatch at {index}")
        records.append(
            {
                field: _parse_scalar(value, f"{location}[{index}].{field}")
                for field, value in zip(fields, row)
            }
        )
    if _canonical_csv(records, fields) != data:
        raise ValueError(f"{location} is not canonical")
    return records


def _parse_jsonl(
    data: bytes,
    fields: Sequence[str],
    validator: Any,
    location: str,
) -> list[dict[str, Any]]:
    if b"\r" in data or not data.endswith(b"\n"):
        raise ValueError(f"{location} must use LF JSONL")
    lines = data[:-1].split(b"\n")
    if not lines or any(not line for line in lines):
        raise ValueError(f"{location} contains an empty record")
    records: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        try:
            value = _strict_json(line.decode("utf-8"), f"{location}[{index}]")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{location} must be UTF-8") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{location}[{index}] must be an object")
        if tuple(value) != tuple(fields):
            raise ValueError(f"{location}[{index}] field order mismatch")
        try:
            validator(value)
        except SchemaValidationError as exc:
            raise ValueError(str(exc)) from exc
        records.append(value)
    canonical = b"\n".join(
        json.dumps(
            record,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        for record in records
    ) + b"\n"
    if canonical != data:
        raise ValueError(f"{location} is not canonical")
    return records


def _identity(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(record[field] for field in ("seed", "rho", "a3", "eta", "method"))


def _check_identity_set(
    records: Sequence[Mapping[str, Any]], name: str
) -> None:
    identities = tuple(_identity(record) for record in records)
    if len(identities) != len(set(identities)):
        raise ValueError(f"duplicate {name} identity")
    if identities != REPLICATION_IDENTITIES:
        missing = sorted(set(REPLICATION_IDENTITIES) - set(identities), key=repr)
        extra = sorted(set(identities) - set(REPLICATION_IDENTITIES), key=repr)
        if len(identities) == len(REPLICATION_IDENTITIES) and set(identities) == set(
            REPLICATION_IDENTITIES
        ):
            raise ValueError(f"reordered {name} identity set")
        raise ValueError(f"missing/identity drift in {name}: missing={missing[:2]} extra={extra[:2]}")


def _parse_role(root: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    raw = {name: _read_stable(root / filename) for name, filename in ROLE_FILES.items()}
    replication = _parse_csv(raw["replication"], FORMAL_REPLICATION_FIELDS, "replication")
    for row in replication:
        try:
            validate_formal_replication_record(row)
        except SchemaValidationError as exc:
            raise ValueError(str(exc)) from exc
    _check_identity_set(replication, "replication")
    diagnostics = _parse_jsonl(raw["diagnostic"], DIAGNOSTIC_FIELDS, validate_diagnostic_record, "diagnostic")
    resources = _parse_jsonl(raw["resource"], RESOURCE_FIELDS, validate_resource_record, "resource")
    journals = _parse_jsonl(raw["row_journal"], ROW_JOURNAL_FIELDS, validate_row_journal_record, "row_journal")
    for name, records in (("diagnostic", diagnostics), ("resource", resources), ("row_journal", journals)):
        _check_identity_set(records, name)
    summary = _parse_csv(raw["summary"], SUMMARY_ROW_FIELDS, "summary")
    if tuple((row["rho"], row["a3"], row["eta"]) for row in summary) != SUMMARY_IDENTITIES:
        raise ValueError("summary identity coverage/order mismatch")
    for index, row in enumerate(summary):
        if any(type(row[field]) is not bool for field in ("passed", *SUMMARY_FIELDS)):
            raise ValueError(f"summary boolean mismatch at {index}")
        try:
            failed = _strict_json(str(row["failed_conditions_json"]), f"summary[{index}].failed_conditions_json")
            audit = _strict_json(str(row["audit_values_json"]), f"summary[{index}].audit_values_json")
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        expected_failed = [name for name in SUMMARY_FIELDS if not row[name]]
        if failed != expected_failed or not isinstance(audit, dict):
            raise ValueError(f"summary canonical failed/audit values mismatch at {index}")
        row["_failed"] = failed
        row["_audit"] = audit
    result = _strict_json_document(raw["result"], "result")
    terminal = _strict_json_document(raw["terminal"], "terminal")
    manifest = _strict_json_document(raw["manifest"], "manifest")
    for schema_name, value in (("scientific_result", result), ("terminal", terminal), ("manifest", manifest)):
        try:
            validate_schema(schema_name, value)
        except SchemaValidationError as exc:
            raise ValueError(str(exc)) from exc
    if _canonical_json(result) != raw["result"] or _canonical_json(terminal) != raw["terminal"] or _canonical_json(manifest) != raw["manifest"]:
        raise ValueError("JSON document is not canonical")
    if result["identity_completeness"] is not True:
        raise ValueError("scientific result identity completeness is false")
    if manifest["terminal_sha256"] != _sha256(raw["terminal"]):
        raise ValueError("manifest terminal hash drift")
    expected_hashes = {
        "replication_sha256": _sha256(raw["replication"]),
        "summary_sha256": _sha256(raw["summary"]),
        "result_sha256": _sha256(raw["result"]),
        "diagnostics_sha256": _sha256(raw["diagnostic"]),
        "resources_sha256": _sha256(raw["resource"]),
        "row_journal_sha256": _sha256(raw["row_journal"]),
    }
    for field, digest in expected_hashes.items():
        if terminal[field] != digest or manifest[field] != digest:
            raise ValueError(f"{field} raw hash drift")
    expected_counts = {
        "replication_count": len(replication),
        "summary_count": len(summary),
        "diagnostic_count": len(diagnostics),
        "resource_count": len(resources),
        "row_journal_count": len(journals),
    }
    for field, count in expected_counts.items():
        if manifest[field] != count or count != RECORD_CARDINALITIES[field.removesuffix("_count")]:
            raise ValueError(f"manifest cardinality drift: {field}")
    identity_bytes = json.dumps([list(identity) for identity in REPLICATION_IDENTITIES], ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if manifest["identity_set_sha256"] != _sha256(identity_bytes):
        raise ValueError("manifest identity digest drift")
    # Row journals bind the operational records to the raw replication rows.
    for index, (replication_row, diagnostic, resource, journal) in enumerate(zip(replication, diagnostics, resources, journals)):
        identities = {_identity(replication_row), _identity(diagnostic), _identity(resource), _identity(journal)}
        if len(identities) != 1:
            raise ValueError(f"row journal identity drift at {index}")
        for field, record in (("replication_sha256", replication_row), ("diagnostic_sha256", diagnostic), ("resource_sha256", resource)):
            canonical = json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            if journal[field] != _sha256(canonical):
                raise ValueError(f"row journal {field} drift at {index}")
    payload = {
        "replication": replication,
        "summary": [{key: value for key, value in row.items() if not key.startswith("_")} for row in summary],
        "result": result,
    }
    try:
        semantic = recompute_scientific_digests(payload)
    except (DuplicateIntegrityError, SchemaValidationError, ValueError) as exc:
        raise ValueError(f"scientific semantic digest failure: {exc}") from exc
    if result["semantic_replication_sha256"] != semantic["replication"] or result["semantic_summary_sha256"] != semantic["summary"]:
        raise ValueError("scientific result semantic digest drift")
    return raw, {"replication": replication, "summary": summary, "result": result, "terminal": terminal, "manifest": manifest, "payload": payload}


def _recomputed_summary(rows: list[dict[str, Any]], config: R006EConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gate = evaluate_screening_gate(rows, config=config)
    if gate.get("status") not in {"PASS", "FAIL"} or gate.get("total_cells") != len(SUMMARY_IDENTITIES):
        raise ValueError("native gate returned malformed result")
    summary: list[dict[str, Any]] = []
    for index, (cell, identity) in enumerate(zip(gate.get("cells", []), SUMMARY_IDENTITIES)):
        if not isinstance(cell, dict) or (cell.get("rho"), cell.get("a3"), cell.get("eta")) != identity:
            raise ValueError(f"gate identity mismatch at {index}")
        conditions = cell.get("conditions")
        if not isinstance(conditions, dict) or tuple(conditions) != SUMMARY_FIELDS or any(type(conditions[name]) is not bool for name in SUMMARY_FIELDS):
            raise ValueError(f"gate condition schema mismatch at {index}")
        failed = [name for name in SUMMARY_FIELDS if not conditions[name]]
        passed = all(conditions.values())
        if cell.get("passed") is not passed or cell.get("failed_conditions") != failed:
            raise ValueError(f"gate status mismatch at {index}")
        values = {"rho": identity[0], "a3": identity[1], "eta": identity[2], "passed": passed, **conditions, "failed_conditions_json": json.dumps(failed, ensure_ascii=True, separators=(",", ":")), "audit_values_json": "{}"}
        summary.append({field: values[field] for field in SUMMARY_ROW_FIELDS})
    return gate, summary


def _scope_verdict(claim: str | None) -> dict[str, Any]:
    if claim is None:
        claim = "simulation-only recovery under the support-conditioned frozen regime"
    if not isinstance(claim, str):
        return {"claim_status": "REJECT", "claim_scope": "", "claim_reasons": ["claim must be text"]}
    text = " ".join(claim.lower().split())
    forbidden = {
        "causal": "causal claims are outside the audit scope",
        "empirical": "empirical claims are outside the audit scope",
        "clinical": "clinical claims are outside the audit scope",
        "policy": "policy claims are outside the audit scope",
        "general effectiveness": "general-effectiveness claims are outside the audit scope",
        "universal": "universal claims are outside the audit scope",
    }
    reasons = [reason for marker, reason in forbidden.items() if marker in text]
    if "simulation" not in text:
        reasons.append("claim must be explicitly simulation-only")
    if not any(marker in text for marker in ("support", "condition", "frozen")):
        reasons.append("claim must retain the support-conditioned frozen-regime boundary")
    return {"claim_status": "REJECT" if reasons else "PASS", "claim_scope": "simulation-only/support-conditioned frozen regime", "claim_reasons": reasons}


def _failure_report(issues: list[str], claim: dict[str, Any]) -> dict[str, Any]:
    return {"integrity_status": "FAIL", "scientific_status": "FAIL", "claim_status": claim["claim_status"], "claim_scope": claim["claim_scope"], "claim_reasons": claim["claim_reasons"], "issues": issues, "duplicate": None, "gates": {}}


def audit_result_claim(
    primary: Path,
    repeat: Path | None = None,
    control: Path | None = None,
    *,
    config: R006EConfig | None = None,
    claim: str | None = None,
    proposed_claim: str | None = None,
) -> dict[str, Any]:
    """Audit two stable role roots and their control ledger without running science."""
    scope = _scope_verdict(proposed_claim if proposed_claim is not None else claim)
    # Accept the shared ScreeningV2Paths value as a convenience without
    # importing the attempt ledger (the audit remains read-only).
    if repeat is None and all(hasattr(primary, name) for name in ("primary", "repeat", "control")):
        paths = primary
        primary, repeat, control = paths.primary, paths.repeat, paths.control
    if repeat is None:
        return _failure_report(["repeat role root is required"], scope)
    if config is None:
        config = R006EConfig()
    if not isinstance(config, R006EConfig):
        return _failure_report(["config must be an R006EConfig"], scope)
    if control is None:
        control = Path(primary).parent / Path(V2_CONTROL_ROOT).name
    primary = Path(primary)
    repeat = Path(repeat)
    control = Path(control)
    issues: list[str] = []
    try:
        primary_raw, primary_data = _parse_role(primary)
        repeat_raw, repeat_data = _parse_role(repeat)
        pair_raw = _read_stable(control / PAIR_CLAIM_FILENAME)
        pair = _strict_json_document(pair_raw, "pair_claim")
        validate_schema("pair_claim", pair)
        if _canonical_json(pair) != pair_raw:
            raise ValueError("pair claim is not canonical")
        if pair["primary_root"] != V2_PRIMARY_ROOT or pair["repeat_root"] != V2_REPEAT_ROOT or pair["control_root"] != V2_CONTROL_ROOT:
            raise ValueError("pair root binding mismatch")
        if pair["primary_attempt_id"] != primary_data["manifest"]["attempt_id"] or pair["repeat_attempt_id"] != repeat_data["manifest"]["attempt_id"]:
            raise ValueError("pair attempt binding mismatch")
        pair_digest = _sha256(pair_raw)
        for role, data in (("primary", primary_data), ("repeat", repeat_data)):
            terminal, manifest = data["terminal"], data["manifest"]
            if terminal["role"] != role or manifest["role"] != role or terminal["attempt_id"] != manifest["attempt_id"]:
                raise ValueError(f"{role} terminal/manifest role binding mismatch")
            if terminal["decision_id"] != pair["decision_id"] or manifest["decision_id"] != pair["decision_id"]:
                raise ValueError(f"{role} decision binding mismatch")
            if terminal["pair_claim_sha256"] != pair_digest or manifest["pair_claim_sha256"] != pair_digest:
                raise ValueError(f"{role} pair claim hash mismatch")
            if terminal["status"] != manifest["status"] or terminal["status"] != data["result"]["status"]:
                raise ValueError(f"{role} stored status mismatch")
            if terminal["status"] in {"FAIL", "INCOMPLETE"} and data["result"]["status"] == "PASS":
                raise ValueError(f"{role} incomplete/failed role cannot claim scientific PASS")
            for marker_name in (ROLE_START_FILENAMES[role], ROLE_CONTROL_START_FILENAMES[role]):
                marker = control / marker_name if marker_name.endswith("_claim.json") else (primary if role == "primary" else repeat) / marker_name
                if marker.exists():
                    marker_raw = _read_stable(marker)
                    marker_value = _strict_json_document(marker_raw, marker_name)
                    validate_schema("role_start", marker_value)
                    if marker_value["attempt_id"] != manifest["attempt_id"] or marker_value["role"] != role or marker_value["pair_claim_sha256"] != pair_digest:
                        raise ValueError(f"{role} start marker binding mismatch")
            control_marker = control / ROLE_CONTROL_START_FILENAMES[role]
            role_marker = (primary if role == "primary" else repeat) / ROLE_START_FILENAMES[role]
            if control_marker.exists() != role_marker.exists():
                raise ValueError(f"{role} control/role start marker mismatch")
            if control_marker.exists() and _read_stable(control_marker) != _read_stable(role_marker):
                raise ValueError(f"{role} control/role start bytes mismatch")
        primary_gate, primary_summary = _recomputed_summary(primary_data["replication"], config)
        repeat_gate, repeat_summary = _recomputed_summary(repeat_data["replication"], config)
        for role, data, expected_gate, expected_summary in (("primary", primary_data, primary_gate, primary_summary), ("repeat", repeat_data, repeat_gate, repeat_summary)):
            stored_summary = [{key: value for key, value in row.items() if not key.startswith("_")} for row in data["summary"]]
            if stored_summary != expected_summary:
                raise ValueError(f"{role} stored summary disagrees with independently recomputed gates")
            if data["result"]["status"] != expected_gate["status"] or data["terminal"]["status"] != expected_gate["status"] or data["manifest"]["status"] != expected_gate["status"]:
                raise ValueError(f"{role} stored status disagrees with independently recomputed gate")
        duplicate = compare_scientific_attempts(primary_data["payload"], repeat_data["payload"])
        scientific_status = "PASS" if duplicate["status"] == "PASS" and primary_data["result"]["status"] == "PASS" and repeat_data["result"]["status"] == "PASS" else "FAIL"
        return {"integrity_status": "PASS", "scientific_status": scientific_status, "claim_status": scope["claim_status"], "claim_scope": scope["claim_scope"], "claim_reasons": scope["claim_reasons"], "issues": [], "duplicate": duplicate, "gates": {"primary": primary_gate, "repeat": repeat_gate}}
    except Exception as exc:
        issues.append(str(exc))
        return _failure_report(issues, scope)


def audit_result_to_claim(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for callers using the v1 audit name."""
    return audit_result_claim(*args, **kwargs)


def duplicate_excluded_fields() -> frozenset[str]:
    """Return the only fields omitted by the scientific duplicate comparison."""
    return frozenset({"runtime_seconds", "peak_memory_bytes", "generated_at"})


def claim_verdict(result: Mapping[str, Any], proposed_claim: str) -> dict[str, Any]:
    """Classify a proposed claim without treating result metadata as evidence."""
    del result
    return _scope_verdict(proposed_claim)


def audit_rows(
    rows: list[dict[str, Any]],
    *,
    phase: str = "screening",
    config: R006EConfig | None = None,
) -> dict[str, Any]:
    """Audit an in-memory raw screening table for fixture and review tooling."""
    if phase != "screening":
        return {"integrity_status": "FAIL", "issues": ["only screening rows are supported"]}
    try:
        gate, _ = _recomputed_summary(rows, config or R006EConfig())
        return {"integrity_status": "PASS", "scientific_status": gate["status"], "gate": gate, "issues": []}
    except Exception as exc:
        return {"integrity_status": "FAIL", "scientific_status": "FAIL", "issues": [str(exc)]}


__all__ = [
    "audit_result_claim",
    "audit_result_to_claim",
    "audit_rows",
    "claim_verdict",
    "duplicate_excluded_fields",
]
