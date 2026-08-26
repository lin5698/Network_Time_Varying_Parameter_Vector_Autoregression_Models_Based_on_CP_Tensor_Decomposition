# REC-M5 Editorial Recheck V2

Generated: 2026-08-12

## Scope and verdict

This is an independent editorial and traceability recheck of `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md`. It reviews candidate wording against the canonical manuscript sources, the controlled benchmark contract, and the claim ledger. It does not apply any candidate text, mutate manuscript sources or the formal register, alter scientific payloads, or perform git operations.

Verdict: `BLOCKED_PENDING_EDITORIAL_REVISIONS`. The patch is structurally reviewable, but the findings below must be resolved before M5-C can pass for manuscript application.

## Findings

### E1 - High: CP/Tucker wording exceeds the supported claim

`REC-M5_REVIEW_PATCH_V1_20260811.md:100-102` says that the same-target Tucker comparison "tests CP-versus-Tucker recovery." The claim ledger limits C003 to endpoint availability and explicitly prohibits inferring successful statistical recovery (`manuscript_src/natcs/claim_evidence_ledger.csv:5`). The current source also describes this comparison as testing whether endpoint preservation depends on CP (`manuscript_src/natcs/results_validation.md:7`). Narrow the sentence to a representation-level endpoint-availability or endpoint-preservation comparison. Do not use `recovery` unless a separate Tucker recovery result and locator are bound.

### E2 - High: Reader-facing G10 does not preserve the required state labels

The patch summary requires `NOT_RUN/ABSTAIN` for N=100/N=200 and `BLOCKED/null` for resource telemetry (`REC-M5_REVIEW_PATCH_V1_20260811.md:25,33`). The proposed reader-facing paragraph says only "were not evaluated" and "were unavailable" (`:221-223`); the exact labels appear only in a manifest-only note (`:226`). If G10 is applied, the manuscript loses the machine-readable abstention boundary. Put the exact states in the proposed paragraph, while retaining the manifest note for traceability.

### E3 - Medium: Stress-category names are not contract-exact

G05-D names `observed-edge loss` and `observed-weight noise` (`:147`), and G07 uses `edge loss` (`:197`). The contract and source use separate categories for graph sparsity, missing observed edges, and noisy observed weights (`manuscript_src/natcs/methods_data.md:11`; `controlled_benchmark_contract.json` topology/stress bindings). Use the declared labels, or explicitly map the synonyms, so graph sparsity is not silently dropped and generation-versus-observation scope remains clear.

### E4 - Medium: Stability threshold wording drops the inequality and target

G08 says stabilization is "triggered at 0.95" and instability is "recorded at 0.98" (`:205`). The contract/source specify operators with spectral norm at or above 0.95 are rescaled to 0.95, while unscaled instability is the at-or-above-0.98 condition (`manuscript_src/natcs/methods_uncertainty.md:3`; `controlled_benchmark_contract.json#/response_evaluation`). Preserve both inequalities and the stabilization target to avoid changing threshold semantics.

### E5 - Medium: Percentage placeholders need a bound formula, not only values

G04 paragraph 1 contains four draft-only gain tokens (`:88-90`). Before author values are inserted, bind whether each percentage is computed from the ratio of median errors, the median of per-replication relative changes, or another declared statistic, and state the endpoint field and comparator locator. A numeric value alone would leave the reader-facing reduction undefined even after the placeholder gate passes.

### E6 - Low: Frozen-audit disclosure is duplicated and may confuse active rows

G01 embeds frozen-audit method identifiers in the methods paragraph (`:58-62`), while G05-B repeats the active-versus-frozen distinction and lists the same registry (`:119-129`). Keep one concise reader-facing boundary in the manuscript and move registry identifiers, cell counts and statuses to the supplementary/manifest traceability location. This avoids making the frozen audit look like additional active comparator rows.

### E7 - Low: G05-E has an avoidable grammatical ambiguity

The sentence "They are neither native graph-learning comparisons nor a main-text ranking" (`:155`) treats tests as if they were a ranking. Use wording such as "They are neither native graph-learning comparisons nor part of a main-text ranking" for a clean subject and predicate.

## Checks performed

- Candidate JSON parsed successfully; unit coverage is `26/26` with 26 unique `(source_item, unit_id)` pairs.
- All ten declared pre-apply paragraph anchor hashes match the current canonical source files.
- All protected exact-path SHA-256 hashes listed in the candidate manifest match the current workspace.
- The four G04 gain tokens are present only as draft placeholders; application remains fail-closed.
- No manuscript source, formal register, scientific payload, authorization record or git state was mutated by this recheck.

## Residual blockers

Author input remains required for ALS stopping semantics, topology-stress bindings, source ownership of compiled application/bootstrap wording, and the four G04 result values/formulas. The separate governance and scientific rechecks must also pass before any manuscript mutation is authorized.
