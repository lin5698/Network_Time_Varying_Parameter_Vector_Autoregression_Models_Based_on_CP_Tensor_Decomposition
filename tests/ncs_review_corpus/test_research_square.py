from __future__ import annotations

import hashlib
import unittest

from scripts.ncs_review_corpus.research_square import (
    MATCH_STATUSES,
    OUTPUT_FIELDS,
    match_research_square_metadata,
    validate_public_url,
)


NCS_DOI = "10.1038/s43588-024-00001-1"


def ncs_metadata() -> dict[str, object]:
    return {
        "doi": NCS_DOI,
        "title": "Network-aware tensor forecasting",
        "authors": ["Ada Lovelace", "Alan Turing"],
    }


def candidate(
    doi: str,
    *,
    title: str = "Network-aware tensor forecasting",
    authors: list[str] | None = None,
    url: str | None = None,
    relation: object | None = None,
    source: str = "Crossref",
    version: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "doi": doi,
        "title": title,
        "authors": authors if authors is not None else ["Ada Lovelace"],
        "date": "2024-02-03",
        "publisher": "Research Square",
        "url": url or f"https://www.researchsquare.com/article/rs-123/{version or 'v1'}",
        "source": source,
    }
    if version is not None:
        record["version"] = version
    if relation is not None:
        record["relation"] = relation
    return record


class ResearchSquareMatchingTests(unittest.TestCase):
    def test_relation_to_ncs_doi_is_confirmed_and_has_priority(self) -> None:
        relation_candidate = candidate(
            "10.21203/rs.3.rs-900/v2",
            title="Different title",
            authors=["Different Author"],
            relation={"is-preprint-of": [{"id": NCS_DOI, "id-type": "DOI"}]},
            version="v2",
        )
        plausible_candidate = candidate(
            "10.21203/rs.3.rs-100/v1",
            relation=None,
        )

        result = match_research_square_metadata(
            ncs_metadata(),
            [plausible_candidate, relation_candidate],
            response=b'{"items":2}',
        )

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["doi"], "10.21203/rs.3.rs-900/v2")
        self.assertEqual(result["version"], "v2")
        self.assertEqual(result["match_basis"], "RELATION")

    def test_exact_normalized_title_and_author_overlap_is_plausible(self) -> None:
        result = match_research_square_metadata(
            ncs_metadata(),
            [
                candidate(
                    "10.21203/rs.3.rs-101/v1",
                    title="Network aware: tensor forecasting!",
                    authors=[{"given": "A.", "family": "Lovelace"}],
                )
            ],
        )

        self.assertEqual(result["status"], "PLAUSIBLE")
        self.assertEqual(result["doi"], "10.21203/rs.3.rs-101/v1")
        self.assertEqual(result["author_overlap_count"], 1)
        self.assertTrue(result["title_exact"])

    def test_multiple_plausible_candidates_are_ambiguous_with_stable_ranking(self) -> None:
        first = candidate("10.21203/rs.3.rs-200/v1")
        second = candidate(
            "10.21203/rs.3.rs-201/v1",
            authors=["Ada Lovelace", "Grace Hopper"],
        )
        duplicate = dict(first)

        forward = match_research_square_metadata(
            ncs_metadata(), [second, duplicate, first]
        )
        reverse = match_research_square_metadata(
            ncs_metadata(), [first, second, duplicate]
        )

        self.assertEqual(forward["status"], "AMBIGUOUS")
        self.assertEqual(forward["doi"], reverse["doi"])
        self.assertEqual(forward["doi"], "10.21203/rs.3.rs-200/v1")
        self.assertEqual(forward["deduplicated_candidate_count"], 2)

    def test_title_match_without_author_overlap_is_no_match(self) -> None:
        result = match_research_square_metadata(
            ncs_metadata(),
            [
                candidate(
                    "10.21203/rs.3.rs-300/v1",
                    authors=["Grace Hopper"],
                )
            ],
        )

        self.assertEqual(result["status"], "NO_MATCH_FOUND")
        self.assertIsNone(result["doi"])
        self.assertEqual(result["matched_candidate_count"], 0)

    def test_restricted_research_square_urls_are_rejected(self) -> None:
        for url in (
            "https://www.researchsquare.com/api/v1/articles/rs-1",
            "https://www.researchsquare.com/article/rs-1/v1.pdf",
            "https://www.researchsquare.com/article/rs-1/v1/full-text",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_public_url(url)

        with self.assertRaises(ValueError):
            match_research_square_metadata(
                ncs_metadata(),
                [candidate(
                    "10.21203/rs.3.rs-301/v1",
                    url="https://www.researchsquare.com/article/rs-301/v1?download=pdf",
                )],
            )

    def test_output_is_limited_to_metadata_and_audit_whitelist(self) -> None:
        result = match_research_square_metadata(
            ncs_metadata(), [candidate("10.21203/rs.3.rs-400/v1")]
        )

        self.assertTrue(set(result).issubset(OUTPUT_FIELDS))
        self.assertEqual(set(MATCH_STATUSES), {
            "CONFIRMED",
            "PLAUSIBLE",
            "AMBIGUOUS",
            "NO_MATCH_FOUND",
        })
        self.assertNotIn("relation", result)
        self.assertNotIn("raw", result)

    def test_response_sha256_is_hash_of_supplied_response_bytes(self) -> None:
        response = b'{"source":"public-search","results":1}'
        result = match_research_square_metadata(
            ncs_metadata(), [candidate("10.21203/rs.3.rs-500/v1")], response=response
        )

        self.assertEqual(result["response_sha256"], hashlib.sha256(response).hexdigest())


if __name__ == "__main__":
    unittest.main()
