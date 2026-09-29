#!/usr/bin/env python3
"""Assemble six validated coding pairs into agreement and adjudication artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .coding import build_agreement, load_json, validate_coding_payload
from .core import MODEL_ID, REASONING_EFFORT, SCHEMA_VERSION, sha256_file, utc_now, write_json
from .validate import scan_public_exports


def _expected_pass_files(index: dict[str, Any]) -> dict[str, str]:
    return {
        record["calibration_id"]: record["file"].replace("_documents.json", ".json")
        for record in index["records"]
    }


def _assert_exact_json_set(directory: Path, expected: set[str]) -> None:
    actual = {path.name for path in directory.glob("*.json")}
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            f"Unexpected coding file set in {directory}; missing={missing}, unexpected={unexpected}"
        )


def _thread_ids(value: str | list[str]) -> list[str]:
    values = [value] if isinstance(value, str) else value
    normalized = [item.strip() for item in values if item and item.strip()]
    if not normalized:
        raise ValueError("At least one coding thread ID is required per pass")
    return list(dict.fromkeys(normalized))


def assemble(
    pass_a_dir: Path,
    pass_b_dir: Path,
    extracted_index_path: Path,
    schema_path: Path,
    output_dir: Path,
    pass_a_thread_id: str | list[str],
    pass_b_thread_id: str | list[str],
) -> dict[str, Any]:
    index = load_json(extracted_index_path)
    schema = load_json(schema_path)
    expected = _expected_pass_files(index)
    if len(expected) != 6:
        raise ValueError(f"Expected exactly six frozen calibration records, got {len(expected)}")
    _assert_exact_json_set(pass_a_dir, set(expected.values()))
    _assert_exact_json_set(pass_b_dir, set(expected.values()))

    source_root = extracted_index_path.parent
    agreement_dir = output_dir / "agreement"
    records: list[dict[str, Any]] = []
    adjudication_items: list[dict[str, Any]] = []
    total_a = total_b = total_matched = 0
    macro_f1: list[float] = []
    categorical_totals = {field: Counter() for field in (
        "actor_role", "issue_type", "concern_domain", "requested_action",
        "response_status", "cost_level",
    )}
    privacy_paths: list[Path] = []

    for record in index["records"]:
        calibration_id = record["calibration_id"]
        filename = expected[calibration_id]
        source_path = source_root / record["file"]
        pass_a_path = pass_a_dir / filename
        pass_b_path = pass_b_dir / filename
        source = load_json(source_path)
        pass_a = load_json(pass_a_path)
        pass_b = load_json(pass_b_path)
        privacy_paths.extend([pass_a_path, pass_b_path])
        errors = [
            *(f"A: {error}" for error in validate_coding_payload(pass_a, "A", source, schema)),
            *(f"B: {error}" for error in validate_coding_payload(pass_b, "B", source, schema)),
        ]
        if errors:
            raise ValueError(f"{calibration_id} failed validation:\n" + "\n".join(errors))
        agreement = build_agreement(pass_a, pass_b)
        agreement_path = agreement_dir / filename
        write_json(agreement_path, agreement)
        matching = agreement["issue_matching"]
        total_a += matching["A_count"]
        total_b += matching["B_count"]
        total_matched += matching["matched_count"]
        macro_f1.append(matching["f1"])
        for field, values in agreement["categorical_agreement"].items():
            categorical_totals[field]["agree"] += values["agreement_count"]
            categorical_totals[field]["disagree"] += values["disagreement_count"]
        for item in agreement["adjudication_items"]:
            adjudication_items.append({"calibration_id": calibration_id, **item})
        records.append(
            {
                "calibration_id": calibration_id,
                "source_documents_sha256": source["documents_sha256"],
                "pass_A": {
                    "file": str(pass_a_path),
                    "sha256": sha256_file(pass_a_path),
                    "episode_count": len(pass_a["episodes"]),
                    "issue_count": len(pass_a["issues"]),
                },
                "pass_B": {
                    "file": str(pass_b_path),
                    "sha256": sha256_file(pass_b_path),
                    "episode_count": len(pass_b["episodes"]),
                    "issue_count": len(pass_b["issues"]),
                },
                "agreement_file": str(agreement_path),
                "agreement_sha256": sha256_file(agreement_path),
                "issue_f1": matching["f1"],
                "adjudication_item_count": len(agreement["adjudication_items"]),
            }
        )

    privacy_errors = scan_public_exports(privacy_paths)
    if privacy_errors:
        raise ValueError("Privacy scan failed:\n" + "\n".join(privacy_errors))
    categorical = {}
    for field, counts in categorical_totals.items():
        denominator = counts["agree"] + counts["disagree"]
        categorical[field] = {
            "agreement_count": counts["agree"],
            "disagreement_count": counts["disagree"],
            "agreement_rate": counts["agree"] / denominator if denominator else None,
        }
    micro_f1 = 2 * total_matched / (total_a + total_b) if total_a or total_b else 1.0
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "corpus_scope": "SIX_FROZEN_PUBLIC_CALIBRATION_PACKAGES",
        "model_contract": {"model": MODEL_ID, "reasoning_effort": REASONING_EFFORT},
        "coding_threads": {
            "A": _thread_ids(pass_a_thread_id),
            "B": _thread_ids(pass_b_thread_id),
        },
        "validation": {
            "json_schema": "PASS",
            "source_hashes": "PASS",
            "document_page_grade_grounding": "PASS",
            "verbatim_quotes": "PASS",
            "privacy_scan": "PASS",
        },
        "aggregate_agreement": {
            "A_issue_count": total_a,
            "B_issue_count": total_b,
            "matched_issue_count": total_matched,
            "micro_f1": micro_f1,
            "macro_f1": sum(macro_f1) / len(macro_f1),
            "categorical": categorical,
            "adjudication_item_count": len(adjudication_items),
        },
        "records": records,
    }
    write_json(output_dir / "coding_audit.json", summary)
    adjudication_rules = [
        "Use only the original public extracted package and the A/B issue records named here.",
        "Do not infer journal-wide frequencies, policy, or acceptance probability.",
        "Preserve unresolved concerns and distinguish author claims from reviewer confirmation.",
        "Return one adjudicated disposition for every item in original order.",
    ]
    indexed_items = [
        {"item_index": index, **item}
        for index, item in enumerate(adjudication_items, start=1)
    ]
    write_json(
        output_dir / "adjudication_packet.json",
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_now(),
            "source_coding_audit": str(output_dir / "coding_audit.json"),
            "model_required": MODEL_ID,
            "reasoning_effort_required": REASONING_EFFORT,
            "rules": adjudication_rules,
            "item_count": len(indexed_items),
            "items": indexed_items,
        },
    )
    source_files = {
        record["calibration_id"]: str(source_root / record["file"])
        for record in index["records"]
    }
    for calibration_id in expected:
        items = [
            item for item in indexed_items if item["calibration_id"] == calibration_id
        ]
        write_json(
            output_dir / "adjudication" / f"{calibration_id.lower()}.json",
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at": utc_now(),
                "calibration_id": calibration_id,
                "source_extracted_package": source_files[calibration_id],
                "model_required": MODEL_ID,
                "reasoning_effort_required": REASONING_EFFORT,
                "rules": adjudication_rules,
                "item_count": len(items),
                "items": items,
            },
        )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pass-a-dir", required=True, type=Path)
    parser.add_argument("--pass-b-dir", required=True, type=Path)
    parser.add_argument("--extracted-index", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--pass-a-thread-id", required=True, action="append")
    parser.add_argument("--pass-b-thread-id", required=True, action="append")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = assemble(
        args.pass_a_dir,
        args.pass_b_dir,
        args.extracted_index,
        args.schema,
        args.output_dir,
        args.pass_a_thread_id,
        args.pass_b_thread_id,
    )
    print(json.dumps(summary["aggregate_agreement"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
