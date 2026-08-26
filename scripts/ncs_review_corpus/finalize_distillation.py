#!/usr/bin/env python3
"""Assemble public NCS review adjudications into auditable distillation reports."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .core import MODEL_ID, REASONING_EFFORT, sha256_file, utc_now, write_json
from .privacy import EMAIL_PATTERN, PRIVATE_TOKENS, SUBMISSION_LINK_PATTERN


CALIBRATION_IDS = ["CAL-D01", "CAL-D02", "CAL-D03", "CAL-E01", "CAL-E02", "CAL-E03"]
ADJUDICATION_DIRS = ("coding/adjudication_results", "coding/adjudication/results")
ADJUDICATION_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "adjudication.schema.json"
EXPECTED_TOTAL_ITEMS = 165
ADJUDICATION_ISSUE_TYPES = (
    "PRAISE",
    "CONCERN",
    "REQUEST",
    "CONDITION",
    "RESPONSE",
    "DECISION",
    "OTHER",
)
ISSUE_TYPE_NORMALIZATION = {
    "QUESTION": "OTHER",
    "DECISION_SIGNAL": "DECISION",
}
PUBLIC_DOCUMENT_GRADES = {
    "PEER_REVIEW_FILE": "JPR",
    "ARTICLE_HTML": "VCO",
    "ARTICLE_PDF": "VCO",
    "REPORTING_SUMMARY": "VCO",
    "SUPPLEMENTARY_INFORMATION": "VCO",
}
UNRESOLVED_STATUSES = {
    "NO_RESPONSE",
    "ACKNOWLEDGED_ONLY",
    "PARTIAL",
    "CONTRADICTED",
    "DEFERRED",
    "DECLINED_WITH_REASON",
    "UNRESOLVED",
}


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"Unsupported JSON Schema type: {expected}")


def validate_json_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the dependency-free JSON Schema subset used by this output contract."""
    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not in the allowed enum")

    expected_types = schema.get("type")
    if expected_types is not None:
        types = [expected_types] if isinstance(expected_types, str) else expected_types
        if not any(_schema_type_matches(value, expected) for expected in types):
            errors.append(f"{path}: expected type {types}, got {type(value).__name__}")
            return errors

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, child in value.items():
            if key in properties:
                errors.extend(validate_json_schema(child, properties[key], f"{path}.{key}"))

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than {schema['maxItems']} items")
        if schema.get("uniqueItems") and len(value) != len({json.dumps(item, sort_keys=True) for item in value}):
            errors.append(f"{path}: items are not unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_json_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: string does not match required pattern")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string is shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string exceeds {schema['maxLength']} characters")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: value is above {schema['maximum']}")

    for child in schema.get("allOf", []):
        errors.extend(validate_json_schema(value, child, path))
    if "if" in schema:
        condition_errors = validate_json_schema(value, schema["if"], path)
        branch = schema.get("then") if not condition_errors else schema.get("else")
        if branch:
            errors.extend(validate_json_schema(value, branch, path))
    return errors

DOMAIN_FILES = {
    "NOVELTY_SIGNIFICANCE": ["abstract.md", "introduction.md", "discussion.md", "cover_letter.md"],
    "SCOPE_POSITIONING": ["abstract.md", "introduction.md", "discussion.md", "supp_note8_scope.md"],
    "CORRECTNESS_THEORY": ["methods_theory.md", "supp_note1_notation.md", "supp_note3_propagation.md"],
    "METHOD_MODEL": ["methods_estimator.md", "methods_propagation.md", "supp_note2_estimator.md"],
    "DATA_PROVENANCE": ["methods_data.md", "data_availability.md", "supp_note7_repro.md"],
    "EXPERIMENT_VALIDATION": ["results_validation.md", "results_generality.md", "supp_note4_benchmarks.md"],
    "STATISTICS_UNCERTAINTY": ["methods_uncertainty.md", "results_validation.md", "supp_note6_robustness.md"],
    "BASELINE_COMPARATOR": ["results_validation.md", "supp_note4_benchmarks.md", "supp_note6_robustness.md"],
    "REPRODUCIBILITY": ["code_availability.md", "data_availability.md", "supp_note7_repro.md"],
    "CLARITY_FIGURES": ["ncs_figure_qa_memo.md", "ncs_fig2_portal_preview_checklist.md", "supplementary.md"],
    "WRITING_FORMAT": ["abstract.md", "introduction.md", "discussion.md"],
    "ETHICS_COMPLIANCE": ["methods_data.md", "data_availability.md"],
    "OTHER": ["discussion.md", "supp_note8_scope.md"],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def paragraph_index(documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for document in documents:
        document_id = document.get("document_id")
        document_type = document.get("document_type")
        if not isinstance(document_id, str) or not isinstance(document_type, str):
            raise ValueError("Public source package has a document without identity metadata")
        for page in document.get("pages", []):
            for paragraph in page.get("paragraphs", []):
                paragraph_id = paragraph.get("paragraph_id")
                if not isinstance(paragraph_id, str):
                    raise ValueError(f"Public source package has an invalid paragraph ID in {document_id}")
                if paragraph_id in index:
                    raise ValueError(f"Duplicate public paragraph ID: {paragraph_id}")
                index[paragraph_id] = {
                    "document_id": document_id,
                    "document_type": document_type,
                    "page_number": page.get("page_number"),
                    "text": normalize(paragraph.get("text", "")),
                }
    return index


def validate_public_evidence(
    payload: dict[str, Any],
    pass_name: str,
    calibration_id: str,
    source_package: dict[str, Any],
    paragraphs: dict[str, dict[str, Any]],
) -> tuple[list[str], int]:
    errors: list[str] = []
    if payload.get("calibration_id") != calibration_id:
        errors.append(f"{pass_name}: calibration_id does not match {calibration_id}")
    if payload.get("source_documents_sha256") != source_package.get("documents_sha256"):
        errors.append(f"{pass_name}: source_documents_sha256 does not match public package")

    issues = payload.get("issues")
    if not isinstance(issues, list):
        return errors + [f"{pass_name}: issues is not an array"], 0

    evidence_count = 0
    for issue_index, issue in enumerate(issues, start=1):
        issue_id = issue.get("issue_id")
        evidence_items = issue.get("evidence") or []
        if not isinstance(evidence_items, list) or not evidence_items:
            errors.append(f"{pass_name} issue {issue_index} ({issue_id}): missing evidence")
            continue
        for evidence_index, evidence in enumerate(evidence_items, start=1):
            evidence_count += 1
            prefix = f"{pass_name} issue {issue_id} evidence {evidence_index}"
            if not isinstance(evidence, dict):
                errors.append(f"{prefix}: evidence is not an object")
                continue
            paragraph_id = evidence.get("paragraph_id")
            source = paragraphs.get(paragraph_id)
            if source is None:
                errors.append(f"{prefix}: unknown public paragraph_id {paragraph_id!r}")
                continue
            if evidence.get("document_id") != source["document_id"]:
                errors.append(f"{prefix}: document_id does not own cited paragraph")
            if evidence.get("page_number") != source["page_number"]:
                errors.append(f"{prefix}: page_number does not match cited paragraph")
            expected_grade = PUBLIC_DOCUMENT_GRADES.get(source["document_type"])
            if expected_grade is None:
                errors.append(f"{prefix}: unsupported public document type {source['document_type']!r}")
            elif evidence.get("grade") != expected_grade:
                errors.append(
                    f"{prefix}: grade {evidence.get('grade')!r} does not match {expected_grade}"
                )
            quote = evidence.get("quote")
            normalized_quote = normalize(quote) if isinstance(quote, str) else ""
            if not normalized_quote:
                errors.append(f"{prefix}: quote is empty")
            elif normalized_quote not in source["text"]:
                errors.append(f"{prefix}: quote is not verbatim in cited paragraph")
            if isinstance(quote, str) and len(quote) > 300:
                errors.append(f"{prefix}: quote exceeds 300 characters")
    return errors, evidence_count


def find_adjudication(root: Path, calibration_id: str) -> Path:
    filename = f"{calibration_id.lower()}.json"
    candidates = [root / "output/ncs_review_corpus" / directory / filename for directory in ADJUDICATION_DIRS]
    matches = [path for path in candidates if path.is_file()]
    if len(matches) != 1:
        raise ValueError(f"Expected one adjudication result for {calibration_id}, found {matches}")
    return matches[0]


def validate_adjudication_payload(
    payload: dict[str, Any],
    schema: dict[str, Any],
    *,
    expected_calibration_id: str | None = None,
    expected_indices: list[int] | None = None,
    expected_kinds: list[str] | None = None,
    source_packet_sha256: str | None = None,
) -> list[str]:
    """Validate one adjudication result against its packet and output contract."""
    errors = validate_json_schema(payload, schema)
    if expected_calibration_id is not None and payload.get("calibration_id") != expected_calibration_id:
        errors.append("calibration_id does not match the expected adjudication packet")
    if payload.get("model") != MODEL_ID or payload.get("reasoning_effort") != REASONING_EFFORT:
        errors.append(f"model provenance is not {MODEL_ID}/{REASONING_EFFORT}")
    if source_packet_sha256 is not None and payload.get("source_packet_sha256") != source_packet_sha256:
        errors.append("source_packet_sha256 does not match the adjudication packet")

    adjudications = payload.get("adjudications")
    if not isinstance(adjudications, list):
        return errors
    actual_indices = [item.get("item_index") for item in adjudications if isinstance(item, dict)]
    if len(actual_indices) != len(adjudications):
        errors.append("adjudications must contain only objects")
    if len(actual_indices) != len(set(actual_indices)):
        errors.append("adjudications contain duplicate item_index")
    if expected_indices is not None and actual_indices != expected_indices:
        errors.append("adjudication item indices do not exactly match packet order")
    if expected_kinds is not None:
        actual_kinds = [item.get("kind") for item in adjudications if isinstance(item, dict)]
        if actual_kinds != expected_kinds:
            errors.append("adjudication kinds do not exactly match packet order")

    for item in adjudications:
        if not isinstance(item, dict):
            continue
        disposition = item.get("disposition")
        canonical_issue_ids = item.get("canonical_issue_ids")
        canonical_fields = item.get("canonical_fields")
        is_drop = disposition in {"DROP_DUPLICATE", "DROP_UNSUPPORTED"}
        if is_drop:
            if canonical_issue_ids != [] or canonical_fields is not None:
                errors.append(
                    f"item {item.get('item_index')}: drop disposition must have empty IDs and null canonical_fields"
                )
        else:
            if not isinstance(canonical_issue_ids, list) or not canonical_issue_ids:
                errors.append(f"item {item.get('item_index')}: non-drop disposition must retain issue IDs")
            elif len(canonical_issue_ids) != len(set(canonical_issue_ids)):
                errors.append(f"item {item.get('item_index')}: canonical_issue_ids contain duplicates")
            if not isinstance(canonical_fields, dict):
                errors.append(f"item {item.get('item_index')}: non-drop disposition must have canonical_fields")
            else:
                issue_type = canonical_fields.get("issue_type")
                if issue_type in ISSUE_TYPE_NORMALIZATION:
                    errors.append(
                        f"item {item.get('item_index')}: issue_type {issue_type} must be normalized to "
                        f"{ISSUE_TYPE_NORMALIZATION[issue_type]}"
                    )
    return errors


def issue_evidence(pass_payloads: list[dict[str, Any]], issue_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for payload in pass_payloads:
        for issue in payload.get("issues", []):
            if issue.get("issue_id") not in issue_ids:
                continue
            for evidence in issue.get("evidence", []):
                key = (
                    evidence.get("document_id", ""),
                    evidence.get("paragraph_id", ""),
                    evidence.get("quote", ""),
                    evidence.get("grade", ""),
                )
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "source_issue_id": issue["issue_id"],
                        "grade": evidence.get("grade"),
                        "document_id": evidence.get("document_id"),
                        "paragraph_id": evidence.get("paragraph_id"),
                        "page_number": evidence.get("page_number"),
                        "quote": evidence.get("quote"),
                    }
                )
    return rows


def check_public_text(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if EMAIL_PATTERN.search(text):
            errors.append(f"{path}: email address present")
        if SUBMISSION_LINK_PATTERN.search(text):
            errors.append(f"{path}: submission-system link present")
        for token in PRIVATE_TOKENS:
            if token.lower() in text.lower():
                errors.append(f"{path}: private token present: {token}")
    return errors


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def assemble(root: Path) -> dict[str, Any]:
    output_root = root / "output/ncs_review_corpus"
    coding_root = output_root / "coding"
    distill_root = output_root / "distillation"
    distill_root.mkdir(parents=True, exist_ok=True)
    manifest = load_json(root / "archive/research_corpus/ncs/public/calibration/calibration_manifest.json")
    metadata = {record["calibration_id"]: record for record in manifest["records"]}
    adjudication_schema = load_json(ADJUDICATION_SCHEMA_PATH)

    cards: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    concern_rows: list[dict[str, Any]] = []
    validation: list[dict[str, Any]] = []
    issue_type_counts: Counter[str] = Counter()

    for calibration_id in CALIBRATION_IDS:
        adjudication_path = find_adjudication(root, calibration_id)
        adjudication = load_json(adjudication_path)
        packet_path = coding_root / "adjudication" / f"{calibration_id.lower()}.json"
        packet = load_json(packet_path)
        pass_a = load_json(coding_root / "pass_a" / f"{calibration_id.lower()}.json")
        pass_b = load_json(coding_root / "pass_b_cli" / f"{calibration_id.lower()}.json")
        source_documents_path = (
            root
            / "archive/research_corpus/ncs/public/calibration/extracted"
            / f"{calibration_id.lower()}_documents.json"
        )
        source_package = load_json(source_documents_path)
        if source_package.get("calibration_id") != calibration_id:
            raise ValueError(f"Public source package identity mismatch for {calibration_id}")
        paragraphs = paragraph_index(source_package.get("documents", []))
        evidence_errors: list[str] = []
        pass_a_errors, pass_a_evidence_count = validate_public_evidence(
            pass_a, "pass A", calibration_id, source_package, paragraphs
        )
        pass_b_errors, pass_b_evidence_count = validate_public_evidence(
            pass_b, "pass B", calibration_id, source_package, paragraphs
        )
        evidence_errors.extend(pass_a_errors)
        evidence_errors.extend(pass_b_errors)
        if evidence_errors:
            raise ValueError(f"{calibration_id} public evidence validation failed:\n" + "\n".join(evidence_errors))

        packet_items = packet.get("items")
        adjudications = adjudication.get("adjudications")
        if not isinstance(packet_items, list) or not isinstance(adjudications, list):
            raise ValueError(f"{calibration_id} packet/adjudication items must be arrays")
        expected_indices = [item.get("item_index") for item in packet_items]
        actual_indices = [item.get("item_index") for item in adjudications]
        expected_kinds = [item.get("kind") for item in packet_items]
        packet_hash = sha256_file(packet_path)
        errors = validate_adjudication_payload(
            adjudication,
            adjudication_schema,
            expected_calibration_id=calibration_id,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            source_packet_sha256=packet_hash,
        )
        if packet.get("calibration_id") != calibration_id:
            errors.append("adjudication packet calibration_id does not match")
        if packet.get("item_count") != len(packet_items):
            errors.append("adjudication packet item_count does not match packet items")
        if any(item_index is None for item_index in expected_indices):
            errors.append("adjudication packet contains an item without item_index")
        if len(expected_indices) != len(set(expected_indices)):
            errors.append("adjudication packet contains duplicate item indices")
        if len(actual_indices) != packet.get("item_count"):
            errors.append("adjudication count does not match packet count")
        if errors:
            validation_status = "FAIL"
        else:
            validation_status = "PASS"
        validation.append(
            {
                "calibration_id": calibration_id,
                "adjudication_file": str(adjudication_path),
                "packet_file": str(packet_path),
                "source_documents_file": str(source_documents_path),
                "source_documents_sha256": source_package.get("documents_sha256"),
                "packet_sha256": packet_hash,
                "item_count": len(actual_indices),
                "public_evidence": {
                    "status": "PASS",
                    "pass_a_evidence_count": pass_a_evidence_count,
                    "pass_b_evidence_count": pass_b_evidence_count,
                },
                "status": validation_status,
                "errors": errors,
            }
        )

        issue_payloads = [pass_a, pass_b]
        by_domain: Counter[str] = Counter()
        by_status: Counter[str] = Counter()
        by_action: Counter[str] = Counter()
        distilled_items: list[dict[str, Any]] = []
        pass_issue_ids = {
            issue.get("issue_id")
            for payload in issue_payloads
            for issue in payload.get("issues", [])
        }
        for item in adjudications:
            disposition = item.get("disposition")
            raw_fields = item.get("canonical_fields")
            fields = raw_fields if isinstance(raw_fields, dict) else {}
            canonical_issue_ids = item.get("canonical_issue_ids", [])
            is_drop = disposition in {"DROP_DUPLICATE", "DROP_UNSUPPORTED"}
            if is_drop:
                if canonical_issue_ids or raw_fields is not None:
                    raise ValueError(
                        f"{calibration_id} item {item.get('item_index')}: drop disposition must have empty IDs and null canonical_fields"
                    )
            else:
                if not isinstance(raw_fields, dict):
                    raise ValueError(
                        f"{calibration_id} item {item.get('item_index')}: canonical_fields must be an object"
                    )
                issue_type = raw_fields.get("issue_type")
                if issue_type in ISSUE_TYPE_NORMALIZATION:
                    expected = ISSUE_TYPE_NORMALIZATION[issue_type]
                    raise ValueError(
                        f"{calibration_id} item {item.get('item_index')}: issue_type {issue_type} must be normalized to {expected}"
                    )
                if issue_type not in ADJUDICATION_ISSUE_TYPES:
                    raise ValueError(
                        f"{calibration_id} item {item.get('item_index')}: issue_type {issue_type!r} is outside the adjudication enum"
                    )
                issue_type_counts[issue_type] += 1
            domain = fields.get("concern_domain", "OTHER")
            status = fields.get("response_status", "UNRESOLVED")
            action = fields.get("requested_action", "UNKNOWN")
            by_domain[domain] += 1
            by_status[status] += 1
            by_action[action] += 1
            if not isinstance(canonical_issue_ids, list):
                raise ValueError(f"{calibration_id} item {item.get('item_index')}: canonical_issue_ids must be an array")
            if is_drop:
                evidence = []
            else:
                if not canonical_issue_ids:
                    raise ValueError(f"{calibration_id} item {item.get('item_index')}: missing canonical issue IDs")
                unknown_issue_ids = sorted(set(canonical_issue_ids) - pass_issue_ids)
                if unknown_issue_ids:
                    raise ValueError(
                        f"{calibration_id} item {item.get('item_index')}: unknown canonical issue IDs {unknown_issue_ids}"
                    )
                evidence = issue_evidence(issue_payloads, canonical_issue_ids)
                if not evidence:
                    raise ValueError(
                        f"{calibration_id} item {item.get('item_index')}: no public paragraph evidence"
                    )
            row = {
                "calibration_id": calibration_id,
                "item_index": item["item_index"],
                "disposition": disposition,
                "canonical_issue_ids": canonical_issue_ids,
                "canonical_fields": raw_fields,
                "canonical_summary_zh": item.get("canonical_summary_zh", ""),
                "rationale_zh": item.get("rationale_zh", ""),
                "unresolved_or_unobserved_zh": item.get("unresolved_or_unobserved_zh", []),
                "evidence": evidence,
            }
            distilled_items.append(row)
            evidence_rows.append(
                {
                    "calibration_id": calibration_id,
                    "item_index": item["item_index"],
                    "disposition": item["disposition"],
                    "issue_ids": ";".join(canonical_issue_ids),
                    "actor_role": fields.get("actor_role", "UNKNOWN"),
                    "issue_type": fields.get("issue_type", "OTHER"),
                    "concern_domain": domain,
                    "requested_action": action,
                    "response_status": status,
                    "cost_level": fields.get("cost_level", "UNKNOWN"),
                    "summary_zh": item.get("canonical_summary_zh", ""),
                    "paragraph_ids": ";".join(sorted({e["paragraph_id"] for e in evidence if e.get("paragraph_id")})),
                    "quotes": " || ".join(e["quote"] for e in evidence if e.get("quote")),
                    "unresolved_or_unobserved_zh": "；".join(item.get("unresolved_or_unobserved_zh", [])),
                }
            )
            if fields.get("actor_role") == "REVIEWER" and status in UNRESOLVED_STATUSES:
                concern_rows.append(evidence_rows[-1].copy())

        article_card = pass_a.get("article_card", {})
        cards.append(
            {
                "calibration_id": calibration_id,
                "title": metadata.get(calibration_id, {}).get("title", ""),
                "doi": metadata.get(calibration_id, {}).get("doi", ""),
                "source_documents_sha256": pass_a["source_documents_sha256"],
                "article_card": article_card,
                "paper_level_editor_priorities_zh": adjudication.get("paper_level_editor_priorities_zh", []),
                "paper_level_reviewer_worries_zh": adjudication.get("paper_level_reviewer_worries_zh", []),
                "paper_level_limitations_zh": adjudication.get("paper_level_limitations_zh", []),
                "adjudication_summary": {
                    "item_count": len(distilled_items),
                    "disposition_counts": dict(Counter(item["disposition"] for item in adjudication["adjudications"])),
                    "concern_domain_counts": dict(by_domain),
                    "response_status_counts": dict(by_status),
                    "requested_action_counts": dict(by_action),
                    "unresolved_or_unobserved_count": sum(by_status[s] for s in UNRESOLVED_STATUSES),
                },
                "items": distilled_items,
            }
        )

    if len(cards) != len(CALIBRATION_IDS):
        raise ValueError(f"Expected {len(CALIBRATION_IDS)} distillation cards, got {len(cards)}")
    total_items = sum(record["item_count"] for record in validation)
    if total_items != EXPECTED_TOTAL_ITEMS or len(evidence_rows) != EXPECTED_TOTAL_ITEMS:
        raise ValueError(
            f"Expected {EXPECTED_TOTAL_ITEMS} adjudications, got records={total_items}, rows={len(evidence_rows)}"
        )
    if any(record["status"] != "PASS" for record in validation):
        raise ValueError(json.dumps(validation, ensure_ascii=False, indent=2))

    cards_path = distill_root / "distillation_cards.json"
    evidence_path = distill_root / "concern_evidence_matrix.csv"
    worries_path = distill_root / "reviewer_worries_matrix.csv"
    validation_path = distill_root / "adjudication_validation.json"
    final_evidence_count = sum(len(item["evidence"]) for card in cards for item in card["items"])
    if not set(issue_type_counts).issubset(set(ADJUDICATION_ISSUE_TYPES)):
        raise ValueError("Canonical issue type validation produced an unknown value")
    write_json(cards_path, {"schema_version": "ncs-distillation-v1", "generated_at": utc_now(), "scope": "SIX_FROZEN_PUBLIC_CALIBRATIONS", "cards": cards})
    write_json(
        validation_path,
        {
            "schema_version": "ncs-adjudication-validation-v1",
            "generated_at": utc_now(),
            "model_contract": {"model": MODEL_ID, "reasoning_effort": REASONING_EFFORT},
            "coverage": {
                "expected_item_count": EXPECTED_TOTAL_ITEMS,
                "actual_item_count": total_items,
                "status": "PASS",
            },
            "public_evidence": {
                "status": "PASS",
                "items_with_evidence": len(evidence_rows),
                "evidence_count": final_evidence_count,
            },
            "canonical_fields_contract": {
                "issue_type": {
                    "allowed_values": list(ADJUDICATION_ISSUE_TYPES),
                    "normalization": ISSUE_TYPE_NORMALIZATION,
                    "status": "PASS",
                    "counts": dict(issue_type_counts),
                }
            },
            "privacy_scan": "PASS",
            "records": validation,
        },
    )
    fields = ["calibration_id", "item_index", "disposition", "issue_ids", "actor_role", "issue_type", "concern_domain", "requested_action", "response_status", "cost_level", "summary_zh", "paragraph_ids", "quotes", "unresolved_or_unobserved_zh"]
    write_csv(evidence_path, evidence_rows, fields)
    write_csv(worries_path, concern_rows, fields)

    editor_md = distill_root / "editor_priorities_report.md"
    editor_lines = [
        "# Nature Computational Science 公开同行评审编辑关注点",
        "",
        "范围：六篇冻结公开校准包。以下是逐篇蒸馏，不是期刊政策、频率或接受概率估计。",
        "",
    ]
    for card in cards:
        editor_lines += [f"## {card['calibration_id']}｜{card['title']}", f"DOI: `{card['doi']}`", "", "编辑优先级："]
        editor_lines += [f"- {text}" for text in card["paper_level_editor_priorities_zh"]] or ["- 未观察到独立编辑优先级。"]
        editor_lines += ["", "审稿人主要担忧："]
        editor_lines += [f"- {text}" for text in card["paper_level_reviewer_worries_zh"]] or ["- 未观察到独立审稿人担忧。"]
        editor_lines += ["", "限制："]
        editor_lines += [f"- {text}" for text in card["paper_level_limitations_zh"]] or ["- 无额外逐篇限制摘要。"]
        editor_lines += [""]
    editor_md.write_text("\n".join(editor_lines), encoding="utf-8")

    risk_md = distill_root / "v0_v1_manuscript_risk_mapping.md"
    risk_lines = [
        "# V0/V1 稿件风险映射",
        "",
        "定义：V0 指当前 `manuscript_src/natcs` 工作区快照；V1 指基于本次公开校准提出的下一版风险控制动作。此表不表示任何动作已经写入稿件，也不替代作者审批。",
        "",
        "| 风险域 | V0 可见承载文件 | V0 观察 | V1 建议动作 | 证据边界 |",
        "|---|---|---|---|---|",
    ]
    domain_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        domain_rows[row["concern_domain"]].append(row)
    manuscript_root = root / "manuscript_src/natcs"
    for domain, filenames in DOMAIN_FILES.items():
        rows = domain_rows.get(domain, [])
        files = [name for name in filenames if (manuscript_root / name).is_file()]
        unresolved = [row for row in rows if row["response_status"] in UNRESOLVED_STATUSES]
        actions = sorted({row["requested_action"] for row in unresolved})
        observation = f"公开校准中 {len(rows)} 个裁决项；其中 {len(unresolved)} 个仍为部分解决、拒绝、延期或未解决状态。" if rows else "本次六篇校准未形成该风险域的裁决项。"
        action = "、".join(actions) if actions else "保持现有边界并做逐句证据核对"
        evidence = "仅限公开同行评审与文章呈现；不把作者报告等同于第三方复现。"
        risk_lines.append(f"| {domain} | {', '.join(files) or '未找到承载文件'} | {observation} | {action} | {evidence} |")
    risk_lines += ["", "V1 执行顺序建议：先处理 `HIGH + PARTIAL/UNRESOLVED/DECLINED_WITH_REASON`，再处理 `MEDIUM` 的可复现性与比较公平性；接受信号仅作为状态字段保存。"]
    risk_md.write_text("\n".join(risk_lines), encoding="utf-8")

    report_manifest = distill_root / "distillation_manifest.json"
    report_paths = [cards_path, evidence_path, worries_path, validation_path, editor_md, risk_md]
    write_json(report_manifest, {"schema_version": "ncs-distillation-manifest-v1", "generated_at": utc_now(), "files": [{"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in report_paths]})
    privacy_errors = check_public_text(report_paths + [report_manifest])
    if privacy_errors:
        raise ValueError("Generated report privacy scan failed:\n" + "\n".join(privacy_errors))
    return {
        "cards": len(cards),
        "adjudications": len(evidence_rows),
        "expected_adjudications": EXPECTED_TOTAL_ITEMS,
        "reviewer_worries": len(concern_rows),
        "public_evidence": "PASS",
        "model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
        "output": str(distill_root),
        "privacy": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(assemble(args.root.resolve()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
