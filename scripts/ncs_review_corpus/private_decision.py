#!/usr/bin/env python3
"""Derive non-quoting risk labels from a private decision email using fixed rules."""

from __future__ import annotations

import argparse
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from .core import SCHEMA_VERSION, assert_ignored_private_path, sha256_file, utc_now, write_json


DECISION_RULES = {
    "DECLINE": (
        r"\bdeclin(?:e|ed|ing)\b",
        r"\breject(?:ed|ion)?\b",
        r"\b(?:unable|not able|cannot) to offer publication\b",
        r"\bwill not be considered\b",
    ),
    "REVISION_INVITE": (
        r"\brevis(?:e|ed|ion)\b",
        r"\bresubmit\b",
    ),
    "ACCEPT": (
        r"\baccept(?:ed|ance)?\b",
    ),
}

CONCERN_RULES = {
    "NOVELTY_SIGNIFICANCE": (
        r"\bnovel(?:ty)?\b",
        r"\bsignifican(?:ce|t)\b",
        r"\bconceptual advance\b",
        r"\bsubstantial advance\b",
        r"\bbroad (?:interest|importance|impact)\b",
    ),
    "SCOPE_POSITIONING": (
        r"\bscope\b",
        r"\breadership\b",
        r"\bjournal fit\b",
        r"\bsuitab(?:le|ility) for (?:the )?journal\b",
    ),
    "CORRECTNESS_THEORY": (
        r"\bcorrectness\b",
        r"\btheorem(?:s)?\b",
        r"\bproof(?:s)?\b",
        r"\btheoretical (?:guarantee|result|analysis)\b",
    ),
    "METHOD_MODEL": (
        r"\bmethodolog(?:y|ical)\b",
        r"\bcomputational method\b",
        r"\bmodel(?:ling|ing)? framework\b",
    ),
    "DATA_PROVENANCE": (
        r"\bdata provenance\b",
        r"\bdata source(?:s)?\b",
        r"\bdataset(?:s)?\b",
    ),
    "EXPERIMENT_VALIDATION": (
        r"\bempirical\b",
        r"\bexperiment(?:s|al)?\b",
        r"\bvalidat(?:e|ed|ion)\b",
        r"\bbenchmark(?:s|ing)?\b",
        r"\breal[- ]world\b",
        r"\bapplication(?:s)?\b",
    ),
    "STATISTICS_UNCERTAINTY": (
        r"\buncertaint(?:y|ies)\b",
        r"\bconfidence interval(?:s)?\b",
        r"\bstatistical(?:ly)?\b",
        r"\bsignificance test(?:s|ing)?\b",
    ),
    "BASELINE_COMPARATOR": (
        r"\bbaseline(?:s)?\b",
        r"\bcompar(?:e|ed|ison|isons|ative)\b",
        r"\bstate[- ]of[- ]the[- ]art\b",
    ),
    "REPRODUCIBILITY": (
        r"\breproducib(?:le|ility)\b",
        r"\bsource code\b",
        r"\bcode availability\b",
    ),
    "CLARITY_FIGURES": (
        r"\bclarity\b",
        r"\bfigure(?:s)?\b",
        r"\bpresentation\b",
    ),
}

TRANSFER_RULES = (r"\btransfer\b", r"\btransfer desk\b")


def extract_plain_body(raw_message: bytes) -> str:
    message = BytesParser(policy=policy.default).parsebytes(raw_message)
    if message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_type() != "text/plain":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            parts.append(part.get_content())
        return "\n".join(parts)
    if message.get_content_type() == "text/plain":
        return message.get_content()
    return ""


def _rule_hits(text: str, rules: tuple[str, ...]) -> list[str]:
    return [f"R{index:02d}" for index, pattern in enumerate(rules, start=1) if re.search(pattern, text, re.I)]


def classify_private_decision(raw_message: bytes) -> dict[str, Any]:
    body = extract_plain_body(raw_message)
    normalized = re.sub(r"\s+", " ", body).strip()
    decision_hits = {
        label: hits for label, rules in DECISION_RULES.items()
        if (hits := _rule_hits(normalized, rules))
    }
    if "DECLINE" in decision_hits:
        decision_class = "DECLINE"
    elif "REVISION_INVITE" in decision_hits:
        decision_class = "REVISION_INVITE"
    elif "ACCEPT" in decision_hits:
        decision_class = "ACCEPT"
    else:
        decision_class = "UNKNOWN"
    concerns = []
    for category, rules in CONCERN_RULES.items():
        hits = _rule_hits(normalized, rules)
        if hits:
            concerns.append(
                {"concern_domain": category, "rule_ids": hits, "rule_hit_count": len(hits)}
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "derived_at": utc_now(),
        "classification": "PRIVATE_RULE_DERIVED_NOT_FOR_PUBLICATION",
        "method": "DETERMINISTIC_REGEX_V1",
        "body_available": bool(normalized),
        "decision_class": decision_class,
        "decision_rule_ids": decision_hits.get(decision_class, []),
        "transfer_offer_detected": bool(_rule_hits(normalized, TRANSFER_RULES)),
        "concerns": concerns,
        "limitations": [
            "Rules detect explicit English lexical signals only.",
            "Absence of a category means NOT_DETECTED, not evidence that the concern was absent.",
            "No quoted sentence, identity, address, manuscript identifier, or URL is retained.",
            "This private artifact must not be supplied to any model service.",
        ],
    }


def public_projection(private_result: dict[str, Any]) -> dict[str, Any]:
    """Return the only fields permitted to enter a public risk-mapping template."""
    return {
        "source_class": "PRIVATE_DECISION_RULE_DERIVED",
        "method": private_result["method"],
        "decision_class": private_result["decision_class"],
        "transfer_offer_detected": private_result["transfer_offer_detected"],
        "concern_domains_detected": [
            item["concern_domain"] for item in private_result["concerns"]
        ],
        "limitation": "Category absence means NOT_DETECTED; no private text was exported.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, type=Path)
    parser.add_argument("--private-output", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assert_ignored_private_path(args.private_output, args.workspace)
    raw = args.email.read_bytes()
    result = classify_private_decision(raw)
    result["source_sha256"] = sha256_file(args.email)
    write_json(args.private_output, result)
    print(
        f"wrote private rule-derived labels: decision={result['decision_class']}, "
        f"concern_domains={len(result['concerns'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
