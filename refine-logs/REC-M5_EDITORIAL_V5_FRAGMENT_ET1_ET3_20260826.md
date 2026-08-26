# REC-M5 Editorial V5 Fragment — E-T1 / E-T3 (lane A, editorial traceability)

- Fragment id: `REC-M5_EDITORIAL_V5_FRAGMENT_ET1_ET3_20260826`
- Generated: 2026-08-26 (timezone basis `Asia/Shanghai`)
- Review object: `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` (V2 patch, editorial E-T3 remediation)
- Finding definitions consumed from: `refine-logs/REC-M5_EDITORIAL_RECHECK_V4_20260823.md` (F1–F5; its overall verdict was FAIL on E-T3 only)
- Fragment scope: tasks E-T1 and E-T3 only. Other V5 tasks (E-T2, E-T4–E-T7) are out of this fragment's scope and are not adjudicated here.
- Line references below are to the V2 patch markdown as read in this session (298 lines total).

## Input-integrity note (hash)

Expected SHA-256 for the V2 patch was declared as `8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0`. Shell execution is prohibited for this fragment, so no independent recomputation was possible. The value is **corroborated** by row 1 of the G-T1 table in `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` ("Measured SHA-256 … MATCH, 29083 B"). This is recorded as cross-lane corroboration, not an independent measurement.

---

## E-T1 — Relocated AIN-RESULT status note: PASS

### (a) G04 structural cleanliness — confirmed

The G04 section (V2 md lines 96–114) contains exactly one `Target:` line (line 98) and four proposal markers — "Proposed paragraph 1:" (100), "Proposed paragraph 2:" (104), "Proposed paragraph 3:" (108), "Proposed paragraph 4:" (112) — each followed immediately by its single blockquote (lines 102, 106, 110, 114). There is zero interleaved prose between any pair of proposed paragraphs; the section closes at line 114 and line 116 opens `## G05`. No process/status statement appears anywhere inside the G04 group. The token `AIN-RESULT` occurs exactly once in the whole V2 markdown — line 295, inside the record-level risk-flag section.

### (b) Record-level placement with adjacent disclaimer — confirmed

Line 295 ("- G04: AIN-RESULT is confirmed and bound to the released benchmark summary; all author-input groups are resolved, while independent semantic review remains required.") sits under `## Missing information and risk flags` (line 289), which follows all manuscript-target groups G01–G10 (lines 68–254) and the record-level "Unit coverage" and "Manuscript change checklist" sections. The immediately following bullet (line 296) ends: "All author-input groups are resolved; only the independent semantic review gate remains. **This note is not manuscript text.**"

Honest nuance recorded: the explicit sentence grammatically binds to the manifest-only traceability bullet on line 296 rather than restating itself on line 295. Combined with (i) the section's title and trailing-record position, (ii) the file-header application rule (line 14: "no text below may be applied until M5-C independent review passes and the user separately authorizes manuscript mutation") and (iii) line 298 ("this file is not authorized to apply or submit"), the AIN-RESULT note is unambiguously excluded from manuscript-reachable content. This is the same construction the V4 receipt accepted on the V1 bytes.

### (c) Adjudication: genuine remedy, not displacement

Three grounds:

1. **Structural inertness.** The destination contains no blockquote, no `Proposed` label, no candidate table and no edit-group payload; under the documented paragraph-anchored application mechanism the trailing record section is unreachable by any applier. The original defect (an unmarked interleaved process note inside the G04 group) cannot recur from this position.
2. **Truth coherence, not relocation of a falsehood.** The note's claim "all author-input groups are resolved" now agrees with the machine state verified in V4 E-T6 (`still_unresolved: []`; acceptance flags true) — the substance of TERRA-V3-E1 was precisely such a contradiction. Displacement would mean moving a false or contradictory claim to a quieter spot; here the statement is accurate, marked, and retains the honest caveat "independent semantic review remains required".
3. **Prescribed remedy matched.** TERRA-V3-E1 prescribed "move it to a manifest-only traceability section or remove it"; option one was taken without information loss (the binding to the released benchmark summary is preserved).

Verdict: **E-T1 = PASS**.

---

## E-T3 — Reader-facing register sweep: PASS

### Method

Every proposed paragraph/blockquote and candidate table row in the V2 markdown was read as would-be published prose: G01 (74), G02 (84), G03 (94), G04-P1…P4 (102, 106, 110, 114), G05-A table (124–129), G05-B (137), G05-C (147–149), G05-D (157), G05-E (165), G05-F table (173–176) plus blockquotes (178, 180), G06 reader-facing text (190), G07 boundary (221), G08 (233), G09 (241), G10 (251). Manifest-only notes (lines 139, 243, 253, 254) and record scaffolding were excluded per the task rule.

### Check 1 — internal verdict/status codes: none found

`NOT_RUN`, `BLOCKED`, `NOT_RUN/ABSTAIN`, `BLOCKED/null`, `AVAILABLE` occur in the V2 markdown only at lines 39, 45–47 (record-level strategy/ceiling tables) and 139, 254 (manifest-only notes). Zero occurrences inside any proposed paragraph/blockquote/candidate table. `OUTSIDE TARGET` is retained (G03 line 94, G04-P2 line 106, G05-C line 147) but is introduced and defined inline at each use ("This mark means that the fitted representation does not return the requested readout…"; "denotes an unavailable readout, not a zero-valued estimate…"); it is the paper's own defined terminology, concurring with V4's borderline adjudication — not an internal code leak.

### Check 2 — "author-confirmed" process-provenance phrasing: none found

Zero occurrences inside proposed text. The F2 remediation is present exactly where claimed: G04-P4 line 114 and G05-D line 157 both now read "fixed, separately documented amplitudes". All surviving "author-confirmed" strings sit in record scaffolding (revision log line 25; dispositions lines 184, 208, 227; risk flags 291–293).

### Check 3 — raw CSV field identifiers in main-text proposals: none found

G04-P1 (line 102) names both metrics verbally — "median effective-operator error", "Median finite-horizon unit-shock response error" — and renders the formula with renamed symbols ($100\times(m_{\mathrm{local}}-m_{\mathrm{CP}})/m_{\mathrm{local}}$, "$m$ is the across-replication median…"). No backticked `*_median` token remains in any main-text-bound proposal.

### Check 4 — promotion-register vocabulary: replaced; both candidates failed-by-rule

All three F5 quotations are absent from proposed text:

- G05-A evidence-role cell (line 129): "Simulation-only qualification under a pre-registered decision rule".
- G05-F table header uses "Rule outcome"; both endpoint-aware candidates remain failed-by-rule: CP anchor split 0/16 → "**Threshold not met**"; Tucker anchor split 6/16 → "**Threshold not met**" (lines 175–176).
- G05-F prose (line 178): "No candidate met the pre-registered decision rule."

Residual observation (non-failing): the single bare word "gate" survives at line 178 ("The gate classification is not empirical ground truth or native recovery"). It refers back to the target file's own retained heading `### Stricter endpoint-aware recovery gate` (which the group replaces the *text and table under*, not the heading), and carries no "promotion" semantics. Under F5's definition — objection to the "promotion" register — this is not a violation; recorded as advisory A1.

### Check 5 — `## V2 revision log` (lines 18–30): unambiguous record scaffolding

The section is pure meta-documentation about the patch document's own revision history: finding IDs (F1–F5), revision events R1–C2 described as removals/replacements, a byte-equality declaration ("All non-listed bytes are identical to V1"), and the authorization basis. It contains no blockquote, no `Proposed` label, no candidate table, and sits before/outside every G01–G10 group; its quoted tokens (`` `NOT_RUN` ``, "`BLOCKED`", "author-confirmed amplitudes", "prespecified promotion rule", …) describe what was removed, never propose text. Correctly excluded from the reader-facing sweep.

### Remediation-completeness spot-check (revision log ↔ current bytes)

R1 → codes gone from G04-P4 (114); R2a/R2b → both replacements present (114, 157); R3 → verbal metric names (102); R4 → plain abstention/unavailability wording in G10 (251); R5a–e → decision-rule vocabulary in G05-A/G05-F (129, 173–180); C1 → G05-B carries a single label "Proposed reader-facing text:" (135); C2a/C2b → G09/G10 manifest-only notes all spell out "(manifest-only; do not apply as manuscript text)" (243, 253, 254). No discrepancy between claimed and actual edits within this fragment's scope. (Claim ceilings themselves are E-T5's task and were not re-adjudicated here.)

### Advisories (non-failing, for the V5 consolidator)

- **A1** — line 178, bare "gate" (see Check 4).
- **A2** — backticked machine identifiers in supplementary-facing content, outside F3's class (main-text results prose CSV metric columns): G05-B registry labels `local_structured`, `causal_temporal_smoother`, `fixed_rank_basis` (line 137; necessary audit-vs-active disambiguation, carried over from V4's borderline list); G07 candidate-table configuration keys `topologyVol=0.18`, `sparsity=0.55`, `wNoise=0.35`, `wDrop=0.30`, `truth.W`, `WEst` (lines 212–217) and `local_network` (line 221) — parameter/method labels in protocol disclosure, not data-schema field identifiers.
- **A3** — G02 line 84 "runtime or memory claims require an explicitly bound field" leans contract-language (carried from V4's borderline observations).

No violation of checks 1–5 was found. Verdict: **E-T3 = PASS**.

---

## Provenance disclosure

- Producing agent/model: **ox-alpha** running under the **DeepSeek Harness**, as an independent delegated read-only reviewer fragment worker.
- Self-adjudicated fragment: the producing agent performed the checks and issued the verdicts itself; no second independent party adjudicated this fragment and no subagents were spawned.
- Reads-only except the sole write of this fragment file (`refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET1_ET3_20260826.md`). No bash/glob/grep/shell execution was performed; all findings derive from direct file reads.
- Files opened: `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` (full, primary object), `refine-logs/REC-M5_EDITORIAL_RECHECK_V4_20260823.md` (finding definitions), `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` (G-T1 hash cross-check only). The optional hash corroboration is cross-lane, not an independent measurement (shell prohibited).
- Nothing in this fragment authorizes application or submission; all 26 candidates remain `CANDIDATE_NOT_APPLIED`. This fragment contributes E-T1/E-T3 verdicts only and does not by itself constitute the consolidated V5 receipt.

— End of fragment.
