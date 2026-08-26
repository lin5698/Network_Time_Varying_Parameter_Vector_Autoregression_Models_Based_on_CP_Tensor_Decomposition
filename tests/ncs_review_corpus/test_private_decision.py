from __future__ import annotations

import unittest

from scripts.ncs_review_corpus.private_decision import (
    classify_private_decision,
    public_projection,
)


def message(body: str) -> bytes:
    return (
        "From: editor@example.invalid\n"
        "To: author@example.invalid\n"
        "Subject: Decision\n"
        "Content-Type: text/plain; charset=utf-8\n\n"
        + body
    ).encode("utf-8")


class PrivateDecisionTests(unittest.TestCase):
    def test_decline_and_concerns_are_rule_derived_without_quotes(self) -> None:
        result = classify_private_decision(
            message(
                "We are unable to offer publication. The conceptual advance and broad "
                "interest are limited, and stronger empirical validation and baselines are needed."
            )
        )
        self.assertEqual(result["decision_class"], "DECLINE")
        self.assertEqual(
            [item["concern_domain"] for item in result["concerns"]],
            ["NOVELTY_SIGNIFICANCE", "EXPERIMENT_VALIDATION", "BASELINE_COMPARATOR"],
        )
        self.assertNotIn("unable to offer", str(result))
        self.assertNotIn("example.invalid", str(result))

    def test_html_only_message_is_not_semantically_scraped(self) -> None:
        raw = (
            "From: editor@example.invalid\nContent-Type: text/html; charset=utf-8\n\n"
            "<p>reject due to novelty</p>"
        ).encode("utf-8")
        result = classify_private_decision(raw)
        self.assertFalse(result["body_available"])
        self.assertEqual(result["decision_class"], "UNKNOWN")

    def test_public_projection_contains_no_source_or_rule_ids(self) -> None:
        result = classify_private_decision(message("Please revise the scope and figures."))
        result["source_sha256"] = "a" * 64
        projection = public_projection(result)
        self.assertNotIn("source_sha256", projection)
        self.assertNotIn("rule_ids", str(projection))
        self.assertEqual(projection["decision_class"], "REVISION_INVITE")


if __name__ == "__main__":
    unittest.main()
