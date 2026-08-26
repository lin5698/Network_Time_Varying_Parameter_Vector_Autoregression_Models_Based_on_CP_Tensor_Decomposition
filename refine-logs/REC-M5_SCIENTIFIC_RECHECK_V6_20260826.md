# REC-M5 Scientific-Boundary Recheck V6 — REC-M5_REVIEW_PATCH_V2_20260826

- **Record class:** `scientific_boundary_recheck_receipt`
- **Date:** 2026-08-26 (Asia/Shanghai)
- **Lane:** SCIENTIFIC-BOUNDARY recheck, independent read-only reviewer
- **Candidate under review:** `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` (editorial E-T3 remediation patch V2; claimed zero semantic change vs. frozen V1)
- **Prior receipt not transferable:** `SCIENTIFIC_RECHECK_TERRA_V5_20260812` is hash-bound to the V1 bytes.
- **Reviewer identity (producing agent/model):** `ox-alpha` on the DeepSeek Harness.

---

## 0. OVERALL VERDICT: **BLOCKED** (fail-closed on instrumentation; zero substantive contradictions found)

The scientific-boundary substance of V2 was fully reviewed and is **clean on content**: every change maps to a declared revision, every restatement preserves the original boundary, and no ceiling is weakened or extended. However, this session's execution environment could not spawn any process (`bash` → `spawn ENOENT`; `glob`/`grep` → ripgrep launch failure), so the two **mandated mechanical verifications — SHA-256 measurement of the inputs and byte-level `diff` V1↔V2 — were NOT executable**. Under the lane's fail-closed rule (never default PASS), the receipt cannot be certified PASS without them. All content-level findings are recorded below so that a single `sha256sum` + `diff` re-run in a shell-capable environment can upgrade or refute this verdict without redoing the review.

**Upgrade path:** if measured SHA-256 of files 1–3 match the expected/corroborated values and `diff` confirms exactly the hunk set in §4, then S-T1 converts to PASS on the recorded mapping and the OVERALL verdict becomes PASS (S-T2..S-T5 already PASS on content).

---

## 1. Environment and instrumentation disclosure

| Instrument | Required by | Status | Evidence |
| --- | --- | --- | --- |
| `bash` (sha256sum) | Input hash verification | **NOT EXECUTABLE** | Every invocation returned `Error: spawn bash ENOENT` |
| `bash` (diff) | S-T1 mechanical diff | **NOT EXECUTABLE** | Same launcher failure |
| glob/grep (ripgrep) | Inventory / search support | **NOT EXECUTABLE** | `ripgrep launch failed` |
| read (Node fs) | Full-content inspection | WORKING | Used for all four opened files |

Substitute method for S-T1: complete literal read of both files with line-by-line paired comparison and constant-offset accounting across all section anchors (ledger in §4). Residual risk disclosed: whitespace-only or invisible-character differences inside otherwise matching lines cannot be excluded without a byte-level tool.

## 2. Inputs and hash table

Measured values: **NOT MEASURABLE IN THIS SESSION** (no hash-capable tool available). Expected values are recorded as given by the lane; no expected value was stated for input 3.

| # | File (path relative to ROOT) | Expected SHA-256 | Measured SHA-256 | Result |
| --- | --- | --- | --- | --- |
| 1 | `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md` | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` | NOT MEASURED (env) | **UNVERIFIED** |
| 2 | `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` | `8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0` | NOT MEASURED (env) | **UNVERIFIED** |
| 3 | `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` | (none stated by lane) | NOT MEASURED (env) | **UNMEASURED** (no expectation to breach) |

Corroborating (third-party, not my measurement): the V2 JSON `v2_revision.supersedes_bytes.sha256` and legacy `output.sha256` both declare `69888df4…580bd` for the V1 markdown, consistent with the lane's expected value for file 1. This corroborates provenance bookkeeping but does not substitute for measurement.

## 3. Files opened / not opened

Opened (read-only): files 1, 2, 3 above; `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json` lines 1–80 only, solely to confirm the `v2_revision` metadata block.
Metadata confirmation: `v2_revision.semantic_ceiling_changes = "none; restatements preserve boundary meanings verbatim"` ✔ declared as required. The JSON also lists revisions applied as finding IDs F1, F2a, F2b, F3, F4, F5a–F5e, C1, C2a, C2b — corresponding one-to-one with the markdown log's R-numbering (R1↔F1, R2a↔F2a, R2b↔F2b, R3↔F3, R4↔F4, R5a–e↔F5a–F5e).
Not opened: any `' 2.'` duplicate copies (none encountered; directory enumeration unavailable in this environment — the four target paths resolved directly); remainder of the V2 JSON beyond the permitted metadata slice.

---

## 4. S-T1 — Mechanical diff V1↔V2 (substituted inspection). Verdict: **BLOCKED** (instrument unavailable; mapping result clean)

Mandated `diff` not runnable; performed full-content literal inspection instead. Line-count arithmetic closes: V2 (298 lines) = V1 (286) + 14 inserted (revision-log block) − 2 deleted (C1 duplicated label + blank). Offset ledger: +14 from V1 L17 through V1 L128; −2 at C1; +12 from V1 L129 through EOF (anchors: L18→32, 27→41, 35→49, 39→53, 54→68, 82→96, 102→116, 117→131, 129→141, 155→167, 170→182, 194→206, 213→225, 223→235, 233→245, 244→256, 264→276, 277→289, 286→298). Constant offsets between anchors with matched text on every paired line ⇒ **14 contiguous diff regions, no unmapped change found by inspection**.

### Hunk-to-log mapping table

| # | Region (V1 line(s) → V2 line(s)) | Change | Markdown log entry | JSON finding ID | Semantic verdict (§5) |
| --- | --- | --- | --- | --- | --- |
| H1 | L1 → L1 | Title "Patch V1" → "Patch V2" | headers/provenance (implicit; declared by v2_revision overlay) | record_version | EQUIVALENT |
| H2 | L3 → L3 | Generated timestamp → date + supersedes-freeze sentence | headers/provenance (implicit) | v2_revision.generated/supersedes_bytes | EQUIVALENT |
| H3 | — → L18–31 inserted | New `## V2 revision log` section (basis ¶ + 7-row table) | log insertion | v2_revision block | EQUIVALENT (meta-documentation; its self-description is the object of this review) |
| H4 | L88 → L102 | G04-P1: formula clause rewritten; CSV field ids `` `coef_error_median` ``/`` `girf_error_median` `` removed, metrics named verbally ("of the same scenario's … respectively") | R3 | F3 | EQUIVALENT |
| H5a | L100 → L114 | G04-P4: "author-confirmed amplitudes" → "fixed, separately documented amplitudes" | R2a | F2a | EQUIVALENT |
| H5b | L100 → L114 (same line, second span) | G04-P4 final sentence: "`scientific execution` is `NOT_RUN`, its `claim activation` is `BLOCKED`, … benchmark claim" → "was not executed under this benchmark's evaluation protocol, carries no evaluative claim of its own, … benchmark result" | R1 | F1 | EQUIVALENT |
| H6 | L115 → L129 | G05-A row 4: "Separate gate"×3 → "Separate design"; evidence role "Simulation-only promotion gate" → "Simulation-only qualification under a pre-registered decision rule" | R5a–e (G05-A table share) | F5a (+F5e aggregate) | EQUIVALENT |
| H7 | L121–122 deleted | G05-B: duplicated "Proposed text:" label + blank removed | C1 | C1 | EQUIVALENT (formatting only) |
| H8 | L145 → L157 | G05-D: "author-confirmed amplitudes" → "fixed, separately documented amplitudes" (second occurrence) | R2b | F2b | EQUIVALENT |
| H9 | L161 → L173 | G05-F table header cell "Promotion status" → "Rule outcome" | R5a–e (G05-F table share) | F5b | EQUIVALENT |
| H10 | L163–164 → L175–176 | G05-F outcome cells ×2: "Not promoted" → "Threshold not met" | R5a–e (collective; sub-letter assignment not decomposed in md log) | F5c/F5d | EQUIVALENT |
| H11 | L166 → L178 | G05-F prose: "prespecified promotion rule" → "pre-registered decision rule" | R5a–e (prose share) | F5e | EQUIVALENT |
| H12 | L231 → L243 | G09 manifest note: adds "; do not apply as manuscript text" | C2a | C2a | EQUIVALENT (restriction strengthened) |
| H13 | L239 → L251 | G10 proposed text: "`NOT_RUN/ABSTAIN`" → "were not evaluated, and we abstain from any claim at either scale"; "(`BLOCKED/null`)" → "for this audit" | R4 | F4 | EQUIVALENT |
| H14 | L241–242 → L253–254 | G10 manifest notes ×2: add "; do not apply as manuscript text"; status codes retained verbatim in state record | C2b | C2b | EQUIVALENT (restriction strengthened) |

Mapping completeness: every region ↔ ≥1 log entry; every log entry (R1, R2a/R2b, R3, R4, R5a–e, C1, C2a/C2b, headers, log insertion) ↔ ≥1 region. Sub-letter granularity of R5a–e is not decomposed inside the markdown log (single collective row); five atomic governance-vocabulary edits observed across G05-A/G05-F, count-consistent with F5a–F5e all applied per the JSON. No unmapped change detected anywhere else in either file.

## 5. S-T2 — Semantic-equivalence judgment. Verdict: **PASS** (content level; conditional on §2 input verification)

No restatement weakens or extends any boundary. Special attention items:

- **R1 (H5b):** Non-execution preserved — "`scientific execution` is `NOT_RUN`" ≡ "was not executed under this benchmark's evaluation protocol" for the reader-facing register (the scoping phrase matches the register's implicit CAL-E01 scope; neither asserts nor denies execution elsewhere; machine code retained in G05-B internal record L139, ceilings L45, response summary L39). No-own-claim preserved categorically — "`claim activation` is `BLOCKED`" ≡ "carries no evaluative claim of its own": still an absolute negation, not softened toward "limited evidence". Non-extension preserved — "was not used to extend the benchmark claim/result" (noun swap only). No weakening, no new capability.
- **R2 (H5a/H8):** Provenance term swapped for property terms ("fixed, separately documented"); true within the package (G07 amplitude table + source bindings). Both trailing negations untouched and verbatim-identical: "their asymmetric released coverage is disclosed, and they do not support a matched ranking or general topology-robustness claim" (G04-P4); "their asymmetric coverage supports only bounded diagnostics, not a matched ranking or general topology-robustness claim" (G05-D). Fixed amplitudes remain fixed documented amplitudes ⇒ bounded diagnostics only; no matched ranking; no general robustness.
- **R4 (H13):** Abstention preserved and made explicit ("we abstain from any claim at either scale" ≡ ABSTAIN component; non-evaluation stated); unavailability preserved ("were unavailable for this audit", same sentence scope); operative negation unchanged ("No performance, failure, resource or scalability conclusion is made for either scale."); codes retained in the manifest-only state record (V2 L254), so no information lost at the machine layer.
- **R5 / F5 (H6, H9–H11):** The negative gate is NOT converted into a softer outcome. Both candidates keep categorical failure-by-rule: outcome cells "Threshold not met" (both rows), prose "No candidate met the pre-registered decision rule", numbers unchanged (CP 0/16, 0/8, 0/8; Tucker 6/16, 6/8, 0/8), bounding sentence unchanged ("the negative result is not a universal failure theorem"). "Rule outcome / Threshold not met" states rule-failure, not deferral or partial credit. "Pre-registered" ≡ "prespecified" (identical advance-fixation strength). G05-A row-4 rename describes the mechanism/design separation, not the outcome; the negative disposition lives in G05-F and is intact.
- **R3 (H4):** Definitional clause only; m remains bound to the same two metrics; no restriction touched (field identifiers remain recoverable via the manifest-only traceability note referencing `REC-M5_RESULT_CANDIDATE_EXTRACTION_V1_20260812.json`, unchanged).
- **C1/C2 (H7, H12, H14):** Formatting removal and added application restrictions on manifest-only notes — restrictive direction only; no reader-facing science text altered.

## 6. S-T3 — Ceilings inventory. Verdict: **PASS** (content level, zero hunks in all listed structures)

Confirmed identical between V1 and V2 (no diff regions; constant offset, matched text):
- `## Scientific ceilings` table (V1 L27–33 ↔ V2 L41–47) — all three rows incl. `NOT_RUN`/`BLOCKED`/`PARTIAL`/`NOT_EVALUABLE` codes and maximum-permitted-interpretation cells.
- `## Source ownership` (V1 L35–37 ↔ V2 L49–51).
- `## Response strategy summary` bullets (V1 L20–25 ↔ V2 L34–39), incl. retention of `NOT_RUN/ABSTAIN`, `BLOCKED/null`, "one execution as insufficient".
- G06 full section (V1 L170–192 ↔ V2 L182–204): disposition, target, reader-facing text, contract-field JSON block, source binding incl. SHA `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`.
- G07 full section (V1 L194–211 ↔ V2 L206–223): disposition, target, four-scenario amplitude table, reader-facing boundary, source bindings.
- `## Unit coverage` + V1-045 crosswalk (V1 L244–262 ↔ V2 L256–274).
- `## Manuscript change checklist` (V1 L264–275 ↔ V2 L276–287), all 11 items, checkbox states identical.
- `Missing information and risk flags`: all 8 items identical, order and positions unchanged (V1 L279–286 ↔ V2 L291–298).
- All other proposed paragraphs not named in the revision log: G01, G02 (+boundary), G03, G04-P2, G04-P3, G05-B quote + internal E01 record (codes retained), G05-C, G05-E, G05-F second paragraph, G08, G09 proposed text — verified identical.

Caveat: "identical" = identical as returned byte-visibly by the filesystem read tool, with constant offsets; invisible whitespace/EOL variants cannot be excluded without `diff` (see §1 residual risk).

## 7. S-T4 — Boundary-negation sweep over all V2 proposed text. Verdict: **PASS** (content level)

Every negating/bounding sentence has a V1 counterpart with identical meaning. Per group:

| Group | Negating/bounding sentences in V2 | V1 counterpart |
| --- | --- | --- |
| Package status | source mutation none; formal register none; execution/activation none; git none; application gate | identical |
| G01 | audit labels "are not aliases for, or additional rows in, the active … benchmark"; boundary: "does not import the E01 raw arrays, intervals, method ordering or activation state" | identical |
| G02 | "not independent empirical ground truth, empirical calibration evidence or evidence of general performance"; runtime/memory claims "require an explicitly bound field and are not supplied by the separate audit"; boundary: "do not describe the frozen E4-r3 route as empirical validation … remain unresolved" | identical |
| G03 | "does not return the requested readout"; "not a zero error, a missing observation or a failed estimate" | identical |
| G04-P1 | "supports only a bounded tested-endpoint statement …"; "It is not independent empirical validation, a fairness result or evidence of broad estimator superiority; N=50 rows remain scaling stress checks" | identical (only H4 definitional clause changed) |
| G04-P2 | "structural negative control rather than a numerical recovery competitor"; OUTSIDE TARGET "not a zero-valued estimate, missing score or failed estimate"; graph-feature rows "are not native same-endpoint comparisons and do not license fairness or superiority ranking" | identical |
| G04-P3 | qualification "not used to extend these gains"; gain "is not independent empirical ground truth, native held-out recovery, cross-family generality or performance outside the stated regime" | identical |
| G04-P4 | Tucker "does not by itself establish recovery superiority"; topology rows "do not support a matched ranking or general topology-robustness claim"; graph-feature rows "remain projection diagnostics rather than native forecasting comparisons"; final triple negation (R1-restated) | counterparts verified; see §5 R1 |
| G05-A | row 3 "Scaling stress, not headline evidence" | identical |
| G05-B | labels "are not aliases …"; audit "is not an additional active benchmark row"; internal record "Scientific execution is `NOT_RUN` and claim activation is `BLOCKED`; … not active benchmark rows or ranking evidence" | identical (codes retained here by design — R1 scoped to G04-P4 only) |
| G05-C | controls "cannot be ranked on direct-only, frozen-topology or network-component columns"; zero count "not evidence of failure-free operation or a failure-rate bound"; mark "is not a numerical zero, missing observation or failed estimate" | identical |
| G05-D | "simulation truth, not independent empirical ground truth"; "is not evidence of native held-out recovery, empirical fairness, broad superiority, cross-family generality or application performance"; topology rows "supports only bounded diagnostics, not a matched ranking or general topology-robustness claim" | identical (only H8 phrase changed) |
| G05-E | "retained only as diagnostics of a mapping problem"; "neither native graph-learning comparisons nor part of a main-text ranking"; future claim requires frozen-and-recorded conditions | identical |
| G05-F | "No candidate met the pre-registered decision rule"; "gate classification is not empirical ground truth or native recovery"; negative result "not a universal failure theorem"; inheritance para negation list | counterparts verified; see §5 R5/F5 |
| G06 | "does not monitor an objective or residual and has no convergence tolerance or early-stop predicate"; 10⁻⁶ "is not a stopping tolerance"; semantics "do not establish convergence or global optimality" | identical |
| G07 | coverage "is not uniformly matched"; rows "provide bounded diagnostics and do not support a matched ranking or general topology-robustness claim" | identical |
| G08 | radius diagnostics "are not interchangeable … unless an explicit contract-bound metric mapping is serialized in a machine-readable artifact"; disposition "does not reproduce, validate or map the unowned spectral-radius wording" | identical |
| G09 | "This does not revise the original N=15/N=30 controlled comparison or the bounded N=50 stress designation"; "Seed coverage from one execution is not repeated-run reproducibility and does not replace the original replication contract" | identical |
| G10 | "we abstain from any claim at either scale" (≡ ABSTAIN, §5 R4); "No performance, failure, resource or scalability conclusion is made for either scale."; substitutes "are not substitutes for resource measurements"; other tables' measurements "do not fill these fields" | counterparts verified; codes retained in manifest state record |
| Risk flags | G06/G07/V1-033/source-ownership/G01-G05 negation sentences | identical |

Boundary statements present in V1 but absent/weakened in V2: **none found**. Wholly new evaluative sentences in V2: **none within proposed manuscript text**. New non-manuscript sentences are limited to: the revision-log section (meta, self-describing), the supersedes/freeze clause in the header (meta, protective), and three additions of "; do not apply as manuscript text" to manifest-only notes (restrictive). The revision-log's own claim ("no ceiling, scope or disposition semantic was weakened or extended") is the hypothesis tested by this review and is confirmed on content.

## 8. S-T5 — Consistency with standing synthetic-result invariants. Verdict: **PASS** (content level)

Against `NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` (`simulation_only` ceiling; E4-R006/E4-R007 QUALIFIED, NOT ACTIVATED; `PAPER_CLAIM_AUDIT` remains `BLOCKED`; `EMPIRICAL_IMPLEMENTATION_AUDIT` remains `FAIL`) and the V2 ceilings table:
- **Empirical calibration:** nowhere asserted; explicitly negated in G02, G04-P1, G05-D, G05-F.
- **Cross-domain validity:** nowhere asserted; negated via cross-family generality, application performance, universal failure theorem disclaimers.
- **Convergence / global optimality:** nowhere asserted; explicitly negated in G06 (unchanged).
- **Repeated-run reproducibility:** nowhere asserted; G09 negation intact; response-summary "one execution insufficient" bullet intact.
- **Promotion of any endpoint-aware candidate:** gate remains failed-by-rule for both candidates (Threshold not met ×2; "No candidate met"); G05-A rename changes mechanism vocabulary only; no candidate is described as promoted, qualified-pass, or pending.
- Simulation-only framing, status-code registers in ceilings/manifest records, and the M5-C application gate all survive unchanged.

## 9. Per-task verdict summary

| Task | Verdict | Basis |
| --- | --- | --- |
| Input hash verification | **BLOCKED** | Measurement not executable in this environment (§1–2); expected values unverified by me |
| S-T1 mechanical diff | **BLOCKED** | Mandated `diff` unavailable; substituted inspection clean (14 regions, all mapped, §4) |
| S-T2 semantic equivalence | **PASS** | Content judgment complete; no weakening/extension (§5) |
| S-T3 ceilings inventory | **PASS** | Zero hunks in all protected structures (§6) |
| S-T4 boundary-negation sweep | **PASS** | All negations preserved; no new evaluative sentence (§7) |
| **OVERALL** | **BLOCKED** | Fail-closed: mandated mechanical verifications unexecutable; zero substantive contradictions found; upgrade path in §0 |

## 10. Independence and provenance disclosure (honest statement)

- Producing agent/model: `ox-alpha` (DeepSeek Harness), executing the designated independent scientific-boundary reviewer lane.
- Self-adjudication: this receipt is authored and adjudicated by the same agent instance within one session; no second independent model or out-of-band reviewer has checked this adjudication. The independence claimed here is **independence from the orchestrator party that synthesized V2**, and it holds only within this shared environment (same filesystem, same toolchain).
- V2 was synthesized by the orchestrator party; this reviewer did not participate in V2 generation and received it as a frozen artifact, but shares its execution environment and file store. Mechanical verification instruments were additionally degraded in this environment (§1), further limiting the strength of independent certification relative to a shell-capable session.
- The lane authorization derives from the delegating task definition (author structured decision `et3_remediation = V2 patch re-review`, 2026-08-26, as recorded in V2); this reviewer issued no authorization of its own.

## 11. Not-done statements

- Only this receipt pair (`REC-M5_SCIENTIFIC_RECHECK_V6_20260826.md/.json`) was written; nothing else was created or modified.
- No manuscript, contract, formal-register, or generated-TeX file was edited.
- No `make`, test, or scientific entry point was executed; no computation was run.
- No SHA-256 was measured (environment incapable); no byte-level `diff` was produced.
- No `' 2.'` duplicate copies were opened; the V2 JSON was opened only for the permitted metadata confirmation.
- No subagents were used (per lane constraints).
- No authorization was issued; no claim was activated; no application rule was lifted; package readiness remains `ready_for_independent_review`.

— End of receipt —
