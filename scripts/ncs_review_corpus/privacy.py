"""Shared privacy markers for public review-corpus exports."""

from __future__ import annotations

import re


PRIVATE_TOKENS = (
    "NATCOMPUTSCI-26-2822",
    "@us.nature.com",
    "@nature.com",
    "mts-natcomputsci.nature.com",
)

EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+",
    flags=re.IGNORECASE,
)

SUBMISSION_LINK_PATTERN = re.compile(
    r"https?://[^\s<>\"']*(?:editorialmanager|manuscriptcentral|mts-[^./]+\.nature\.com)"
    r"[^\s<>\"']*",
    flags=re.IGNORECASE,
)
