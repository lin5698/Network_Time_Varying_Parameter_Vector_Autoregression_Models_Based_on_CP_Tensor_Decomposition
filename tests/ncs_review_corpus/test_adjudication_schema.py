from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ncs_review_corpus.core import sha256_file


SCHEMA_PATH = ROOT / "scripts/ncs_review_corpus/schemas/adjudication.schema.json"
RESULT_DIRS = (
    ROOT / "output/ncs_review_corpus/coding/adjudication_results",
    ROOT / "output/ncs_review_corpus/coding/adjudication/results",
)
PACKET_ROOT = ROOT / "output/ncs_review_corpus/coding/adjudication"


def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def result_paths() -> list[Path]:
    return sorted(
        path
        for directory in RESULT_DIRS
        for path in directory.glob("*.json")
        if path.is_file()
    )


def load_result(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def packet_contract(path: Path) -> tuple[list[int], list[str], str]:
    packet = load_result(PACKET_ROOT / path.name)
    items = packet["items"]
    packet_path = PACKET_ROOT / path.name
    return (
        [item["item_index"] for item in items],
        [item["kind"] for item in items],
        sha256_file(packet_path),
    )


def validate(
    payload: dict,
    *,
    expected_indices: list[int] | None = None,
    expected_kinds: list[str] | None = None,
    expected_hash: str | None = None,
) -> list[str]:
    from scripts.ncs_review_corpus import finalize_distillation

    validator = getattr(finalize_distillation, "validate_adjudication_payload", None)
    if validator is None:
        return ["validate_adjudication_payload is missing"]
    return validator(
        payload,
        schema(),
        expected_calibration_id=payload.get("calibration_id"),
        expected_indices=expected_indices,
        expected_kinds=expected_kinds,
        source_packet_sha256=expected_hash,
    )


class AdjudicationSchemaTests(unittest.TestCase):
    def test_adjudication_schema_is_present(self) -> None:
        self.assertTrue(SCHEMA_PATH.is_file())

    def test_all_165_existing_adjudications_pass_the_contract(self) -> None:
        paths = result_paths()
        self.assertEqual(len(paths), 6)
        all_indices: list[int] = []
        keep_separate_count = 0
        for path in paths:
            payload = load_result(path)
            expected_indices, expected_kinds, expected_hash = packet_contract(path)
            errors = validate(
                payload,
                expected_indices=expected_indices,
                expected_kinds=expected_kinds,
                expected_hash=expected_hash,
            )
            self.assertEqual(errors, [], msg=f"{path}: {errors}")
            all_indices.extend(item["item_index"] for item in payload["adjudications"])
            keep_separate_count += sum(
                item["disposition"] == "KEEP_SEPARATE"
                for item in payload["adjudications"]
            )
        self.assertEqual(len(all_indices), 165)
        self.assertEqual(sorted(all_indices), list(range(1, 166)))
        self.assertEqual(keep_separate_count, 15)

    def test_illegal_enum_and_legacy_issue_types_are_rejected(self) -> None:
        path = result_paths()[0]
        payload = load_result(path)
        expected_indices, expected_kinds, expected_hash = packet_contract(path)
        payload["adjudications"][0]["disposition"] = "NOT_A_DISPOSITION"
        payload["adjudications"][0]["canonical_fields"]["issue_type"] = "QUESTION"
        errors = validate(
            payload,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash=expected_hash,
        )
        self.assertTrue(any("disposition" in error for error in errors), errors)
        self.assertTrue(any("issue_type" in error for error in errors), errors)

        decision_signal = load_result(path)
        decision_signal["adjudications"][0]["canonical_fields"]["issue_type"] = "DECISION_SIGNAL"
        errors = validate(
            decision_signal,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash=expected_hash,
        )
        self.assertTrue(any("normalized to DECISION" in error for error in errors), errors)

    def test_missing_and_duplicate_indices_are_rejected(self) -> None:
        path = result_paths()[0]
        original = load_result(path)
        expected_indices, expected_kinds, expected_hash = packet_contract(path)

        missing = copy.deepcopy(original)
        missing["adjudications"].pop()
        missing_errors = validate(
            missing,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash=expected_hash,
        )
        self.assertTrue(any("item indices" in error for error in missing_errors), missing_errors)

        duplicate = copy.deepcopy(original)
        duplicate["adjudications"][1]["item_index"] = duplicate["adjudications"][0]["item_index"]
        duplicate_errors = validate(
            duplicate,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash=expected_hash,
        )
        self.assertTrue(any("duplicate item_index" in error for error in duplicate_errors), duplicate_errors)

    def test_source_packet_hash_mismatch_is_rejected(self) -> None:
        path = result_paths()[0]
        payload = load_result(path)
        expected_indices, expected_kinds, _expected_hash = packet_contract(path)
        errors = validate(
            payload,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash="0" * 64,
        )
        self.assertTrue(any("source_packet_sha256" in error for error in errors), errors)

    def test_drop_requires_empty_ids_and_null_fields(self) -> None:
        path = result_paths()[0]
        payload = load_result(path)
        expected_indices, expected_kinds, expected_hash = packet_contract(path)
        item = payload["adjudications"][0]
        item["disposition"] = "DROP_DUPLICATE"
        errors = validate(
            payload,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash=expected_hash,
        )
        self.assertTrue(
            any("drop disposition" in error and "empty IDs" in error for error in errors),
            errors,
        )

    def test_non_luna_provenance_is_rejected(self) -> None:
        path = result_paths()[0]
        payload = load_result(path)
        expected_indices, expected_kinds, expected_hash = packet_contract(path)
        payload["model"] = "gpt-5.5"
        payload["reasoning_effort"] = "high"
        errors = validate(
            payload,
            expected_indices=expected_indices,
            expected_kinds=expected_kinds,
            expected_hash=expected_hash,
        )
        self.assertTrue(any("model provenance" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
