# REC-M5 Editorial Recheck V3

Generated: 2026-08-12

## Scope and provenance

This receipt is a fresh editorial traceability review of the current all-author-input-bound M5 review patch and its author-input worksheet. The requested reviewer configuration is `gpt-5.6-luna` with reasoning effort `max`; this review completed without a service interruption. Only the two input records named below were reviewed. No manuscript, patch, author-input, register, authorization or generated-output file was modified.

## Verdict

`BLOCKED`

The scientific ceilings, source-unavailable boundaries, status labels in the candidate paragraphs and no-application controls are substantively present, but the current package is not editorially ready for a PASS because its package-status prose is internally stale and one process note is not clearly excluded from reader-facing G04 text.

## Findings

### E1 - High: current package status contradicts the all-author-input-bound state

The patch opens with `Package readiness: needs_author_input` (`REC-M5_REVIEW_PATCH_V1_20260811.md:5-14`), while the same patch ends with `Package readiness is ready_for_independent_review` (`:287`) and its JSON status is `M5_B_G04_G06_G07_G08_AUTHOR_INPUT_COMPLETE_FINAL_SEMANTIC_RECHECK_REQUIRED`. The author-input JSON independently reports `AUTHOR_INPUT_COMPLETE_PENDING_INDEPENDENT_REVIEW` and `ready_for_independent_review`. Update the opening status and any stale “remaining author inputs” wording before this version can be treated as current.

### E2 - High: G04 contains an unmarked process note inside proposed reader-facing content

Immediately after the proposed Results paragraph, `:90` states “AIN-RESULT binding”, names an internal extraction artifact and says the patch remains ineligible while remaining inputs close. This is not marked `manifest-only` and would be inappropriate Nature Computational Science prose if the G04 paragraph were applied. Move it to an explicitly manifest-only traceability section or remove it from the proposed manuscript text. The same sentence also says “remaining author inputs” although the author-input record has `still_unresolved: []`.

### E3 - Medium: G04 reader prose exposes internal CSV field names

The proposed Results paragraph (`:88`) embeds `coef_error_median` and `girf_error_median`. These are useful evidence locators, but they are implementation field names rather than reader-facing metric names. Keep the ratio-of-medians formula in mathematical prose and move exact field names, source hashes and scenario keys to the traceability record. This preserves the confirmed AIN-RESULT binding without lowering the manuscript's editorial register.

### E4 - Medium: the author worksheet retains a stale contradictory Chinese status line

The worksheet's English routing and JSON state are complete (`REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md:5-10`; JSON `acceptance_gate.all_required_fields_resolved=true`, unresolved list empty), but the Chinese checklist says “其余组仍待补充” (`REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md:108`). That directly contradicts the following confirmed ALS, topology and source-ownership lines. The worksheet is not a manuscript source, but this stale statement breaks current-version traceability and should be corrected before a final receipt is accepted.

### E5 - Low: G06 reader-facing sentence has a grammar defect

The proposed sentence says “performs a fixed 60 alternating-least-squares iterations” (`REC-M5_REVIEW_PATCH_V1_20260811.md:180`). Use “performs 60 fixed alternating-least-squares iterations” or “performs a fixed count of 60 alternating-least-squares iterations.” The implementation boundary and no-convergence claim are otherwise appropriately scoped.

## Positive checks

- All 18 author-input fields have values or explicit unavailable decisions; `still_unresolved` is empty and all AIN acceptance booleans are true.
- The four G04 values are bound to a ratio-of-across-replication-medians formula, exact metric fields, scenario/comparator mapping and evidence hashes.
- G06 fixed-60 semantics, G07 four topology rows and asymmetric replication coverage, and AIN-SOURCE-01/02/03/04 unavailable/source-ownership decisions are explicitly represented.
- G04-G10 preserve `NOT_RUN/ABSTAIN`, `BLOCKED/null`, `NOT_AUTHORIZED`, simulation-only, no-promotion and no-generated-TeX-import boundaries.
- The patch contains zero double-brace placeholders, covers all 26 units exactly once, and all ten current pre-apply anchor hashes match.
- Current artifact hashes and the patch's declared output hash match at review time; no manuscript or authorization mutation occurred.

## Remaining boundary

This receipt does not authorize M5-D manuscript mutation or M5-F formal-register mutation. The patch must retain its no-application state until the stale status/process prose is corrected and the independent semantic gates close.
