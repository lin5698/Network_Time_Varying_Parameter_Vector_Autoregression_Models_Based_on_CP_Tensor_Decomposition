#!/usr/bin/env python3
"""Validate independent coding passes and build a deterministic agreement packet."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .core import SCHEMA_VERSION, normalize_space, sha256_json, utc_now, write_json
from .validate import scan_public_exports


CODING_PASSES = {"A", "B"}
CATEGORICAL_FIELDS = (
    "actor_role",
    "issue_type",
    "concern_domain",
    "requested_action",
    "response_status",
    "cost_level",
)
DOCUMENT_GRADE = {
    "PEER_REVIEW_FILE": "JPR",
    "ARTICLE_HTML": "VCO",
    "ARTICLE_PDF": "VCO",
    "REPORTING_SUMMARY": "VCO",
    "SUPPLEMENTARY_INFORMATION": "VCO",
}


def _type_matches(value: Any, expected: str) -> bool:
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


def validate_json_schema(
    value: Any, schema: dict[str, Any], path: str = "$"
) -> list[str]:
    """Validate the subset of JSON Schema used by the coding contract."""
    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not in the allowed enum")

    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(_type_matches(value, expected) for expected in expected_types):
            errors.append(f"{path}: expected type {expected_types}, got {type(value).__name__}")
            return errors

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
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
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_json_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: string does not match required pattern")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: string exceeds {schema['maxLength']} characters")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: value is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: value is above {schema['maximum']}")
    return errors


def _paragraph_index(documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for document in documents:
        for page in document.get("pages", []):
            for paragraph in page.get("paragraphs", []):
                paragraph_id = paragraph["paragraph_id"]
                if paragraph_id in index:
                    raise ValueError(f"Duplicate paragraph ID in source package: {paragraph_id}")
                index[paragraph_id] = {
                    "document_id": document["document_id"],
                    "document_type": document["document_type"],
                    "page_number": page.get("page_number"),
                    "text": normalize_space(paragraph.get("text", "")),
                }
    return index


def validate_coding_payload(
    payload: dict[str, Any],
    expected_pass: str,
    source_package: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    errors = validate_json_schema(payload, schema)
    if expected_pass not in CODING_PASSES:
        raise ValueError(f"Unknown coding pass: {expected_pass}")
    if payload.get("coding_pass") != expected_pass:
        errors.append(
            f"$.coding_pass: expected {expected_pass!r}, got {payload.get('coding_pass')!r}"
        )
    if payload.get("calibration_id") != source_package.get("calibration_id"):
        errors.append("$.calibration_id: does not match the extracted source package")
    if payload.get("source_documents_sha256") != source_package.get("documents_sha256"):
        errors.append("$.source_documents_sha256: does not match the extracted source package")

    episodes = payload.get("episodes") or []
    issues = payload.get("issues") or []
    episode_ids = [item.get("episode_id") for item in episodes]
    issue_ids = [item.get("issue_id") for item in issues]
    if len(episode_ids) != len(set(episode_ids)):
        errors.append("$.episodes: duplicate episode_id")
    if len(issue_ids) != len(set(issue_ids)):
        errors.append("$.issues: duplicate issue_id")
    episode_set = set(episode_ids)
    issue_set = set(issue_ids)
    episode_membership: dict[str, set[str]] = {}
    for episode in episodes:
        episode_id = episode.get("episode_id")
        declared = episode.get("issue_ids") or []
        if len(declared) != len(set(declared)):
            errors.append(f"$.episodes[{episode_id}].issue_ids: duplicate issue_id")
        unknown = sorted(set(declared) - issue_set)
        if unknown:
            errors.append(f"$.episodes[{episode_id}].issue_ids: unknown IDs {unknown}")
        episode_membership[episode_id] = set(declared)

    paragraph_index = _paragraph_index(source_package.get("documents", []))
    for issue in issues:
        issue_id = issue.get("issue_id")
        episode_id = issue.get("episode_id")
        if episode_id not in episode_set:
            errors.append(f"$.issues[{issue_id}].episode_id: unknown episode {episode_id!r}")
        elif issue_id not in episode_membership.get(episode_id, set()):
            errors.append(f"$.issues[{issue_id}]: missing from episode issue_ids")
        evidence_items = issue.get("evidence") or []
        if not any(item.get("grade") == "JPR" for item in evidence_items):
            errors.append(f"$.issues[{issue_id}].evidence: missing required JPR evidence")
        for evidence_index, item in enumerate(evidence_items, start=1):
            prefix = f"$.issues[{issue_id}].evidence[{evidence_index}]"
            paragraph_id = item.get("paragraph_id")
            source = paragraph_index.get(paragraph_id)
            if source is None:
                errors.append(f"{prefix}: unknown paragraph_id {paragraph_id!r}")
                continue
            if item.get("document_id") != source["document_id"]:
                errors.append(f"{prefix}: document_id does not own cited paragraph")
            if item.get("page_number") != source["page_number"]:
                errors.append(f"{prefix}: page_number does not match cited paragraph")
            expected_grade = DOCUMENT_GRADE.get(source["document_type"])
            if expected_grade is None:
                errors.append(f"{prefix}: unsupported source document type")
            elif item.get("grade") != expected_grade:
                errors.append(
                    f"{prefix}: grade {item.get('grade')!r} does not match "
                    f"{source['document_type']} ({expected_grade})"
                )
            quote = normalize_space(item.get("quote", ""))
            if not quote or quote not in source["text"]:
                errors.append(f"{prefix}: quote is not verbatim in cited paragraph")
    return errors


def evidence_keys(issue: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (item.get("document_id", ""), item.get("paragraph_id", ""))
        for item in issue.get("evidence", [])
    }


def _pair_score(issue_a: dict[str, Any], issue_b: dict[str, Any]) -> tuple[int, int, int]:
    shared = len(evidence_keys(issue_a) & evidence_keys(issue_b))
    if shared == 0:
        return (0, 0, 0)
    field_matches = sum(issue_a.get(field) == issue_b.get(field) for field in CATEGORICAL_FIELDS)
    weight_distance = abs(issue_a.get("impact_weight", 0) - issue_b.get("impact_weight", 0))
    return (shared, field_matches, -weight_distance)


def match_issues(
    issues_a: list[dict[str, Any]], issues_b: list[dict[str, Any]]
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    candidates: list[tuple[tuple[int, int, int], int, int]] = []
    for index_a, issue_a in enumerate(issues_a):
        for index_b, issue_b in enumerate(issues_b):
            score = _pair_score(issue_a, issue_b)
            if score[0] > 0:
                candidates.append((score, index_a, index_b))
    candidates.sort(
        key=lambda item: (
            item[0],
            issues_a[item[1]].get("issue_id", ""),
            issues_b[item[2]].get("issue_id", ""),
        ),
        reverse=True,
    )
    used_a: set[int] = set()
    used_b: set[int] = set()
    pairs: list[tuple[int, int]] = []
    for _score, index_a, index_b in candidates:
        if index_a not in used_a and index_b not in used_b:
            pairs.append((index_a, index_b))
            used_a.add(index_a)
            used_b.add(index_b)
    pairs.sort()
    return (
        pairs,
        [index for index in range(len(issues_a)) if index not in used_a],
        [index for index in range(len(issues_b)) if index not in used_b],
    )


def build_agreement(pass_a: dict[str, Any], pass_b: dict[str, Any]) -> dict[str, Any]:
    if pass_a.get("calibration_id") != pass_b.get("calibration_id"):
        raise ValueError("Cannot compare different calibration records")
    if pass_a.get("source_documents_sha256") != pass_b.get("source_documents_sha256"):
        raise ValueError("Cannot compare passes grounded in different source packages")
    issues_a = pass_a.get("issues", [])
    issues_b = pass_b.get("issues", [])
    pairs, unmatched_a, unmatched_b = match_issues(issues_a, issues_b)
    matched_count = len(pairs)
    precision = matched_count / len(issues_b) if issues_b else float(not issues_a)
    recall = matched_count / len(issues_a) if issues_a else float(not issues_b)
    f1 = 2 * matched_count / (len(issues_a) + len(issues_b)) if issues_a or issues_b else 1.0

    field_counts = {field: Counter() for field in CATEGORICAL_FIELDS}
    exact_weights = 0
    within_one_weights = 0
    matched: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for index_a, index_b in pairs:
        issue_a = issues_a[index_a]
        issue_b = issues_b[index_b]
        differences: dict[str, dict[str, Any]] = {}
        for field in CATEGORICAL_FIELDS:
            agrees = issue_a.get(field) == issue_b.get(field)
            field_counts[field]["agree" if agrees else "disagree"] += 1
            if not agrees:
                differences[field] = {"A": issue_a.get(field), "B": issue_b.get(field)}
        weight_a = issue_a.get("impact_weight")
        weight_b = issue_b.get("impact_weight")
        if weight_a == weight_b:
            exact_weights += 1
        if abs(weight_a - weight_b) <= 1:
            within_one_weights += 1
        if weight_a != weight_b:
            differences["impact_weight"] = {"A": weight_a, "B": weight_b}
        pair = {
            "issue_id_A": issue_a.get("issue_id"),
            "issue_id_B": issue_b.get("issue_id"),
            "shared_evidence": [
                {"document_id": document_id, "paragraph_id": paragraph_id}
                for document_id, paragraph_id in sorted(evidence_keys(issue_a) & evidence_keys(issue_b))
            ],
            "differences": differences,
        }
        matched.append(pair)
        if differences:
            disagreements.append(
                {"kind": "MATCHED_FIELD_DIFFERENCE", **pair, "issue_A": issue_a, "issue_B": issue_b}
            )
    for index in unmatched_a:
        disagreements.append({"kind": "UNMATCHED_A", "issue_A": issues_a[index]})
    for index in unmatched_b:
        disagreements.append({"kind": "UNMATCHED_B", "issue_B": issues_b[index]})

    categorical = {
        field: {
            "agreement_count": counts["agree"],
            "disagreement_count": counts["disagree"],
            "agreement_rate": counts["agree"] / matched_count if matched_count else None,
        }
        for field, counts in field_counts.items()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "calibration_id": pass_a["calibration_id"],
        "source_documents_sha256": pass_a["source_documents_sha256"],
        "matching_contract": {
            "primary_key": "at least one shared (document_id, paragraph_id)",
            "tie_break": "shared evidence count, categorical matches, impact-weight proximity, issue IDs",
            "semantic_adjudication_required": True,
        },
        "issue_matching": {
            "A_count": len(issues_a),
            "B_count": len(issues_b),
            "matched_count": matched_count,
            "precision_B_against_A": precision,
            "recall_B_against_A": recall,
            "f1": f1,
            "unmatched_A_count": len(unmatched_a),
            "unmatched_B_count": len(unmatched_b),
        },
        "categorical_agreement": categorical,
        "impact_weight_agreement": {
            "exact_count": exact_weights,
            "within_one_count": within_one_weights,
            "exact_rate": exact_weights / matched_count if matched_count else None,
            "within_one_rate": within_one_weights / matched_count if matched_count else None,
        },
        "matched_pairs": matched,
        "adjudication_required": bool(disagreements),
        "adjudication_items": disagreements,
        "pass_hashes": {"A": sha256_json(pass_a), "B": sha256_json(pass_b)},
    }


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass-a", required=True, type=Path)
    parser.add_argument("--pass-b", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema = load_json(args.schema)
    source = load_json(args.source)
    pass_a = load_json(args.pass_a)
    pass_b = load_json(args.pass_b)
    errors = []
    errors.extend(f"pass A: {error}" for error in validate_coding_payload(pass_a, "A", source, schema))
    errors.extend(f"pass B: {error}" for error in validate_coding_payload(pass_b, "B", source, schema))
    errors.extend(scan_public_exports([args.pass_a, args.pass_b]))
    if errors:
        raise ValueError("Coding validation failed:\n" + "\n".join(errors))
    write_json(args.output, build_agreement(pass_a, pass_b))
    print(f"validated {source['calibration_id']}; wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
