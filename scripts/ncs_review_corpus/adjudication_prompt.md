You are adjudicating disagreements between two independent coding passes for frozen, public Nature Computational Science peer-review material.

Hard constraints:

- Use only the assigned per-paper adjudication packet and its named public extracted package.
- Never access private decision email, submission portal material, `archive/research_corpus/ncs/private/**`, another paper, or the manuscript under review.
- Use `gpt-5.6-luna` with reasoning effort `max`.
- Treat the actionable issue as the minimum coding unit. A finer split is valid only when concerns require different actions or have different response states.
- Preserve unresolved, partly resolved, declined, unsupported, and not-observed concerns.
- Distinguish author-reported changes from reviewer-confirmed resolution.
- Do not infer journal-wide frequencies, editorial policy, acceptance probability, or causal requirements for acceptance.
- Return one adjudication for every input item, in ascending `item_index`, with no omissions or duplicates.

Return exactly one JSON object:

```json
{
  "schema_version": "1.0",
  "calibration_id": "CAL-...",
  "model": "gpt-5.6-luna",
  "reasoning_effort": "max",
  "source_packet_sha256": "64 lowercase hex characters",
  "adjudications": [
    {
      "item_index": 1,
      "kind": "the input kind exactly",
      "disposition": "ACCEPT_A | ACCEPT_B | MERGE | KEEP_SEPARATE | DROP_DUPLICATE | DROP_UNSUPPORTED",
      "canonical_issue_ids": ["source issue IDs retained by the decision"],
      "canonical_fields": {
        "actor_role": "EDITOR | REVIEWER | AUTHOR | UNKNOWN",
        "issue_type": "PRAISE | CONCERN | REQUEST | CONDITION | RESPONSE | DECISION | OTHER",
        "concern_domain": "one value from the coding schema",
        "requested_action": "one value from the coding schema",
        "response_status": "one value from the coding schema",
        "cost_level": "LOW | MEDIUM | HIGH | UNKNOWN"
      },
      "canonical_summary_zh": "concise grounded Chinese summary",
      "rationale_zh": "why this boundary and field choice best matches the cited public evidence",
      "unresolved_or_unobserved_zh": ["limitations that must remain visible"]
    }
  ],
  "paper_level_editor_priorities_zh": [],
  "paper_level_reviewer_worries_zh": [],
  "paper_level_limitations_zh": []
}
```

For `KEEP_SEPARATE`, `canonical_issue_ids` may contain multiple IDs and `canonical_fields` should describe the first retained issue; explain the additional issue boundaries in `rationale_zh`. For a drop disposition, use an empty `canonical_issue_ids` array and set `canonical_fields` to `null`.
