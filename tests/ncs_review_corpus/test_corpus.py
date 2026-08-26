from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ncs_review_corpus.core import MODEL_ID, REASONING_EFFORT, normalize_doi
from scripts.ncs_review_corpus.extract import (
    _split_pdf_paragraphs,
    ocr_textless_pdf_pages,
    paragraph_lookup,
)
from scripts.ncs_review_corpus.luna import is_transient_failure
from scripts.ncs_review_corpus.nature import (
    MaterialParser,
    classify_material,
    is_retryable_download_error,
    select_archive_materials,
    validate_archived_article,
    write_immutable,
)
from scripts.ncs_review_corpus.snapshot import build_snapshot, normalize_item
from scripts.ncs_review_corpus.survey_candidates import resolve_source_snapshot, select_records
from scripts.ncs_review_corpus.validate import scan_public_exports, validate_evidence_items


class SnapshotTests(unittest.TestCase):
    def test_crossref_record_is_normalized(self) -> None:
        record = normalize_item(
            {
                "DOI": "10.1038/S43588-024-00732-2",
                "title": ["Example"],
                "published-online": {"date-parts": [[2024, 10, 1]]},
                "author": [{"given": "A", "family": "Author"}],
                "type": "journal-article",
            }
        )
        self.assertEqual(record["doi"], "10.1038/s43588-024-00732-2")
        self.assertEqual(record["publication_date"], "2024-10-01")
        self.assertEqual(
            record["official_url"],
            "https://www.nature.com/articles/s43588-024-00732-2",
        )

    def test_repeated_cursor_can_still_deliver_final_page(self) -> None:
        responses = iter(
            [
                {
                    "message": {
                        "total-results": 3,
                        "next-cursor": "stable-token",
                        "items": [
                            {"DOI": "10.1038/a", "title": ["A"]},
                            {"DOI": "10.1038/b", "title": ["B"]},
                        ],
                    }
                },
                {
                    "message": {
                        "total-results": 3,
                        "next-cursor": "stable-token",
                        "items": [{"DOI": "10.1038/c", "title": ["C"]}],
                    }
                },
            ]
        )
        with patch(
            "scripts.ncs_review_corpus.snapshot.fetch_page",
            side_effect=lambda *_args: next(responses),
        ):
            snapshot = build_snapshot(2, "test@example.invalid", 1, 0)
        self.assertEqual(snapshot["summary"]["unique_doi_count"], 3)


class MaterialDiscoveryTests(unittest.TestCase):
    def test_peer_review_link_is_discovered(self) -> None:
        parser = MaterialParser()
        parser.feed(
            '<meta name="citation_pdf_url" content="https://www.nature.com/articles/example.pdf">'
            '<a data-test="supp-info-link" data-track-label="peer review file" '
            'href="https://media.springernature.com/example.pdf">Peer Review File (download PDF)</a>'
        )
        self.assertEqual(parser.materials[0]["label"], "Peer Review File (download PDF)")
        self.assertEqual(
            classify_material(parser.materials[0]["label"], parser.materials[0]["href"], None),
            "PEER_REVIEW_FILE",
        )

    def test_snapshot_path_prefers_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            workspace = root / "workspace"
            input_dir = workspace / "archive" / "screening"
            snapshot = workspace / "archive" / "snapshot.json"
            input_path = input_dir / "screen.json"
            input_dir.mkdir(parents=True)
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.touch()
            self.assertEqual(
                resolve_source_snapshot("archive/snapshot.json", input_path, workspace),
                snapshot.resolve(),
            )

    def test_snapshot_path_falls_back_to_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            workspace = root / "workspace"
            input_dir = root / "exports"
            snapshot = input_dir / "snapshot.json"
            input_path = input_dir / "screen.json"
            input_dir.mkdir(parents=True)
            workspace.mkdir()
            snapshot.touch()
            self.assertEqual(
                resolve_source_snapshot("snapshot.json", input_path, workspace),
                snapshot.resolve(),
            )

    def test_preregistered_records_do_not_require_relatedness_labels(self) -> None:
        records = [{"doi": "10.1038/example", "official_url": "https://example.invalid"}]
        payload = {"source_snapshot": "unused.json", "records": records}
        self.assertIs(select_records(payload, Path("pool.json"), {"A", "B", "C"}), records)

    def test_archive_files_are_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "source.pdf"
            first_digest = write_immutable(path, b"first")
            self.assertEqual(write_immutable(path, b"first"), first_digest)
            with self.assertRaises(FileExistsError):
                write_immutable(path, b"changed")

    def test_real_attachment_replaces_article_page_anchor(self) -> None:
        materials = [
            {
                "kind": "REPORTING_SUMMARY",
                "label": "Reporting Summary",
                "url": "https://www.nature.com/articles/example#MOESM2",
            },
            {
                "kind": "REPORTING_SUMMARY",
                "label": "Reporting summary (download PDF)",
                "url": "https://media.springernature.com/example.pdf",
            },
        ]
        self.assertEqual(
            select_archive_materials(materials, {"REPORTING_SUMMARY"}),
            [materials[1]],
        )

    def test_incomplete_read_is_retryable(self) -> None:
        import http.client

        self.assertTrue(is_retryable_download_error(http.client.IncompleteRead(b"partial")))
        self.assertFalse(is_retryable_download_error(ValueError("invalid host")))

    def test_required_non_pdf_attachment_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            landing = root / "landing.html"
            review = root / "review.bin"
            landing.write_bytes(b"<html>full text</html>")
            review.write_bytes(b"not a pdf")
            from scripts.ncs_review_corpus.core import sha256_file
            import json

            manifest = {
                "metadata": {"doi": "10.1038/example"},
                "landing_page": {"file": landing.name, "sha256": sha256_file(landing)},
                "materials": [
                    {
                        "kind": "PEER_REVIEW_FILE",
                        "file": review.name,
                        "sha256": sha256_file(review),
                        "is_pdf": False,
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_archived_article(
                    manifest_path,
                    "10.1038/example",
                    {"PEER_REVIEW_FILE"},
                    {"PEER_REVIEW_FILE"},
                )


class GroundingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents = [
            {
                "pages": [
                    {
                        "page_number": 1,
                        "paragraphs": [
                            {
                                "paragraph_id": "PR-P0001-001",
                                "text": "The reviewer requested a stronger comparison with current baselines.",
                            }
                        ],
                    }
                ]
            }
        ]

    def test_verbatim_evidence_passes(self) -> None:
        analysis = {
            "issues": [
                {
                    "evidence": [
                        {
                            "paragraph_id": "PR-P0001-001",
                            "quote": "requested a stronger comparison with current baselines",
                        }
                    ]
                }
            ]
        }
        self.assertEqual(validate_evidence_items(analysis, self.documents), [])

    def test_fabricated_quote_fails(self) -> None:
        analysis = {
            "issues": [
                {
                    "evidence": [
                        {
                            "paragraph_id": "PR-P0001-001",
                            "quote": "requested a causal experiment",
                        }
                    ]
                }
            ]
        }
        self.assertTrue(validate_evidence_items(analysis, self.documents))

    def test_pdf_line_break_hyphenation_is_joined(self) -> None:
        self.assertEqual(
            _split_pdf_paragraphs("The compari-\nson remains auditable across all benchmark runs."),
            ["The comparison remains auditable across all benchmark runs."],
        )

    def test_ocr_rejects_unreadable_resolution(self) -> None:
        with self.assertRaises(ValueError):
            ocr_textless_pdf_pages(Path("missing.pdf"), {"textless_pages": [1]}, dpi=72)


class PrivacyAndModelTests(unittest.TestCase):
    def test_model_contract_is_luna_max(self) -> None:
        self.assertEqual(MODEL_ID, "gpt-5.6-luna")
        self.assertEqual(REASONING_EFFORT, "max")

    def test_only_transient_provider_failures_are_retryable(self) -> None:
        self.assertTrue(is_transient_failure("503 Service Unavailable"))
        self.assertTrue(is_transient_failure("504 Gateway Time-out"))
        self.assertTrue(is_transient_failure("stream disconnected"))
        self.assertFalse(is_transient_failure("JSON schema validation failed"))

    def test_private_identifiers_fail_public_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "public.md"
            path.write_text("Manuscript NATCOMPUTSCI-26-2822", encoding="utf-8")
            self.assertTrue(scan_public_exports([path]))

    def test_any_email_or_submission_link_fails_public_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            email = root / "email.md"
            portal = root / "portal.md"
            email.write_text("Contact anonymous.person@example.org", encoding="utf-8")
            portal.write_text(
                "https://www.editorialmanager.com/example/default.aspx", encoding="utf-8"
            )
            self.assertTrue(scan_public_exports([email]))
            self.assertTrue(scan_public_exports([portal]))


if __name__ == "__main__":
    unittest.main()
