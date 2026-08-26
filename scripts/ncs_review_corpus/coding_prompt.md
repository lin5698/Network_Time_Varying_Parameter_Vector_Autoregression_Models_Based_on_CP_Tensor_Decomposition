You are independently coding one frozen public Nature Computational Science article package.

Hard constraints:

- Use only the supplied extracted JSON. Do not read other files, browse the web, or use memory about the paper.
- Never access any private decision email, submission portal material, or `archive/research_corpus/ncs/private/**`.
- The output language is Chinese except for short verbatim English evidence quotes.
- Treat the actionable issue as the minimum coding unit. Split concerns that require different actions or have different response states; do not split one concern merely because it spans paragraphs.
- Identify roles and rounds only from explicit headings or strong document structure. Otherwise use UNKNOWN and lower linkage confidence.
- Evidence grades: JPR is official journal-hosted peer-review text; VCO is article/supplement/reporting context; STATUS_ONLY supports existence/access only. Do not invent PPR or CPR evidence.
- Every issue must have at least one continuous verbatim quote no longer than 300 characters, copied exactly from the cited paragraph ID.
- Distinguish NOT_OBSERVED from evidence that DOES_NOT_SUPPORT a claim.
- Impact weights: 0 praise/format only; 1 local clarification; 2 local credibility/reproducibility; 3 core method, validation, generality or comparator; 4 core validity or explicit decision-critical condition.
- `minimum_response_zh` is the least response that directly addresses the observed issue. `strong_evidence_supplement_zh` is a stronger credibility-building option, not an invented completed result.
- Do not infer acceptance probability or editorial policy from a published sample.
- Preserve null results, limitations, rejected requests and unresolved concerns.

Return exactly one JSON object conforming to the provided schema. Preserve the supplied calibration ID, coding pass, and documents SHA-256 exactly.
