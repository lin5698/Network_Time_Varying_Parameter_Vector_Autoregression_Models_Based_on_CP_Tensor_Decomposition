# REC-M5 Editorial Recheck V5 (Editorial-Traceability Lane, V2 Patch Generation) — Consolidated Receipt

- record_class: `editorial_recheck_receipt`
- record_id: `REC-M5_EDITORIAL_RECHECK_V5_20260826`
- generated: 2026-08-26
- timezone basis: `Asia/Shanghai`
- lane: A2 — editorial traceability (consolidation)
- supersedes: `REC-M5_EDITORIAL_RECHECK_V4_20260823` (**FAIL**, on E-T3 only)
- review object: `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` + `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json`
- consolidation mode: pure assembly of four independently authored fragment verdicts; **no fragment verdict, evidence item, or advisory text was altered during consolidation**; every task verdict below is attributed to its adjudicating fragment.

---

## Review-object identity

| File | Expected SHA-256 (orchestrator-declared) | Size | Provenance status |
| --- | --- | --- | --- |
| `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` | `8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0` | 29083 B | Orchestrator-declared; **corroborated** by `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` G-T1 row 1, measured MATCH (29083 B) |
| `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json` | `5e1697d22ac847825e37c4090ee2e28af0385c3015ecc1d8a048bb3cbda5f2ce` | 31204 B (as reported in the same G-T1 row) | Orchestrator-declared; **corroborated** by `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` G-T1 row 2, measured MATCH |

Both expected values were adopted as declared; neither was re-hashed by this lane (shell execution unavailable to every worker in this topology). Identity rests on **cross-lane corroboration** against the independently measured G-T1 tables of `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` (both rows MATCH; access declaration in its G-T8). This is corroboration, not fresh measurement by this lane.

---

## Per-task verdicts

| Task | Verdict | Adjudicating fragment |
| --- | --- | --- |
| E-T1 — Relocated AIN-RESULT status note | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET1_ET3_20260826` |
| E-T2 — 26-unit traceability | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET2_20260826` |
| E-T3 — Reader-facing register sweep | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET1_ET3_20260826` |
| E-T4 — Manifest-only containment | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET4_ET5_ET6_20260826` |
| E-T5 — Claim ceilings | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET4_ET5_ET6_20260826` |
| E-T6 — Author-input traceability V1→V2 | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET4_ET5_ET6_20260826` |
| E-T7 — Diff discipline (hunk→revision-log mapping) | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET7_ET8_20260826` |
| E-T8 — Byte-generation declaration | **PASS** | `REC-M5_EDITORIAL_V5_FRAGMENT_ET7_ET8_20260826` |

### Key evidence per task (verbatim/near-verbatim from the adjudicating fragments)

**E-T1 — PASS** (fragment ET1_ET3)

- G04 structural cleanliness confirmed: exactly one `Target:` line and four "Proposed paragraph N:" markers, each followed immediately by its single blockquote; zero interleaved prose between any pair of proposed paragraphs; the token `AIN-RESULT` occurs exactly once in the whole V2 markdown — line 295, inside the record-level risk-flag section.
- Record-level placement with adjacent disclaimer confirmed: the note sits under `## Missing information and risk flags` (line 289), which follows all manuscript-target groups G01–G10; combined with the section's title and trailing-record position, the file-header application rule (line 14) and line 298 ("this file is not authorized to apply or submit"), the AIN-RESULT note is unambiguously excluded from manuscript-reachable content.
- Genuine remedy, not displacement: (1) structural inertness — the destination contains no blockquote, no `Proposed` label, no candidate table and no edit-group payload, so the original defect cannot recur from this position; (2) truth coherence — "all author-input groups are resolved" now agrees with the machine state verified in V4 E-T6 (`still_unresolved: []`); (3) prescribed remedy matched — TERRA-V3-E1's option one ("move it to a manifest-only traceability section or remove it") was taken without information loss.

**E-T2 — PASS** (fragment ET2)

- T2.1/T2.2: `unit_coverage` rows counted **26/26** with **0** duplicate `unit_id` values (also 26 distinct `(source_item, unit_id)` pairs); source items present **only** {V1-026 ×3, V1-033 ×13, V1-045 ×10} — 3+13+10 = 26, matching the expected distribution exactly; every row carries a single scalar group anchor, all inside G01–G10.
- T2.3: groups with ≥1 unit = **10/10** (G01×1, G02×2, G03×1, G04×6, G05×9, G06×1, G07×1, G08×1, G09×2, G10×2; per-group counts sum to 26 with no double counting); units mapping outside G01–G10 = **0**.
- T2.4: exact per-group set equality between `traceability.G*.source_units` and `unit_coverage` rows (union = all 26 rows; 0 missing, 0 extra/unresolvable); `clause_traceability` audited over 17 clause keys — 0 orphan units, 0 dangling references, every clause's references within its own prefix group; the markdown `## Patch index` and `## Unit coverage` sections agree with the JSON with **zero disagreement** across all 10 rows.

**E-T3 — PASS** (fragment ET1_ET3)

- Checks 1–3 clean: internal verdict/status codes (`NOT_RUN`, `BLOCKED`, `NOT_RUN/ABSTAIN`, `BLOCKED/null`, `AVAILABLE`) occur only at record-level strategy/ceiling tables and manifest-only notes — zero occurrences inside any proposed paragraph/blockquote/candidate table (`OUTSIDE TARGET` retained but introduced and defined inline as the paper's own terminology, concurring with V4's borderline adjudication); zero "author-confirmed" strings inside proposed text (F2 remediation present at G04-P4 line 114 and G05-D line 157, both reading "fixed, separately documented amplitudes"); no backticked `*_median` token remains in any main-text-bound proposal (metrics named verbally at G04-P1 line 102).
- Check 4: all three F5 quotations absent from proposed text — G05-A evidence-role cell reads "Simulation-only qualification under a pre-registered decision rule"; G05-F table header uses "Rule outcome" with both endpoint-aware candidates failed-by-rule ("**Threshold not met**"; CP anchor split 0/16, Tucker anchor split 6/16); prose reads "No candidate met the pre-registered decision rule." Residual single bare word "gate" at line 178 refers to the target file's own retained heading and carries no "promotion" semantics — recorded as non-failing advisory A1, not a violation under F5's definition.
- Check 5 + completeness spot-check: the `## V2 revision log` (lines 18–30) is pure meta-documentation correctly excluded from the reader-facing sweep; R1→R5a–e→C1→C2a/C2b all verified landed against current bytes with no discrepancy between claimed and actual edits within the fragment's scope.

**E-T4 — PASS** (fragment ET4_ET5_ET6)

- Inventory: five manifest-only notes present, matching the expected population of five (G05-B line 139; G09 line 243; G10 lines 253 and 254; risk-flag line 296); the four enumerated labels all carry the exact harmonized parenthetical "(manifest-only; do not apply as manuscript text)" — confirming C2a/C2b landed — and the fifth (risk-flag) note uses the containment-equivalent exclusion sentence "This note is not manuscript text." (its phrasing was not in C2a/C2b scope).
- Containment: no manifest-only note text appears inside any "Proposed …text" block (all notes are plain paragraphs/risk-flag bullets with no `>` prefix); the V2 json `clause_traceability` object contains only G01-P1…G10-P1 keys mapping to REC-M3 unit-id strings, so none of the five notes appears there; and none is reachable by a paragraph-level applier — `pre_apply_anchor_checks` operates over paragraphs of the *target* manuscript files with `fail_closed_on_drift: true`, so no anchor-hash-driven paragraph operation can select, carry, or emit the patch-file notes into a target file.

**E-T5 — PASS** (fragment ET4_ET5_ET6)

- V1-026: forbidden list intact ("No CI, ranking, superiority, equivalence, native-held-out claim or promotion." — all six barred categories present, corroborated by json `scientific_boundaries.V1-026.forbidden` and the response-strategy sentence); post-R1 plain English at G04-P4 carries exactly the four required semantics (descriptive only; was not executed; carries no evaluative claim of its own; was not used to extend the benchmark result), with codes confined to off-manuscript surfaces (Scientific ceilings table; manifest-only G05-B internal note).
- V1-033: "These objects provide simulation truth within the declared design; they are not independent empirical ground truth…" preserved (G02, G05-D); the five unresolved gaps restated in canonical order (G02 boundary, G05-E, Scientific ceilings, risk flags). V1-045: N=20/N=50 scope; post-R4 plain-word abstention at G10 ("N=100 and N=200 were not evaluated, and we abstain from any claim at either scale"); telemetry unavailable with "not substitutes" language; single-execution boundary ("Seed coverage from one execution is not repeated-run reproducibility").
- G06: disposition `AUTHOR_CONFIRMED_REVIEW_ONLY` / `CANDIDATE_NOT_APPLIED`; fixed-60 / no-tolerance ALS semantics matching AIN-ALS-01…05 verbatim in meaning; affirmative negation "do not establish convergence or global optimality"; barred import of the unowned 100/80 wording. G07: asymmetric replication disclosed (3 vs 20 replications; sparse row 3 per released method) with amplitudes value-identical to the author-input request (0.18/0.15/0/0; 0.08/0.55/0.18/0; 0.06/0.15/0/0.30; 0.06/0.15/0.35/0); negation of matched-ranking/general-topology-robustness claims; 50% attenuation remains outside CAL-E03. Weakening/extension sweep: no ceiling weakened and no claim extended anywhere in the proposed text.

**E-T6 — PASS** (fragment ET4_ET5_ET6)

- Four percentages (93.6/96.8/82.5/87.3 display values; unrounded 93.55…/96.76…/82.54…/87.32…), the ratio-of-medians formula `$100\times(m_{\mathrm{local}}-m_{\mathrm{CP}})/m_{\mathrm{local}}$`, the across-replication-median denominator, and the endpoint/comparator binding (local_network vs cp_network, 20 replications per primary scenario) are carried identically from the author-input artifacts; evidence hash `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1` present in all three locations (author-input md line 38; author-input json `evidence_sha256`/`submitted_evidence`; V2 patch json `evidence_bundle_hashes`).
- Unavailable sources remain barred everywhere in V2: canonical sources for the application/bootstrap 100/80-iteration, spectral-radius and 50%-attenuation wording are unavailable; none may be recovered from generated TeX or imported (G06 line 204, G07 line 223, G08 line 227, checklist lines 282–284, risk flag line 293, json `source_ownership.unresolved_canonical_source`); no proposed text reconstructs any of the three wordings.
- Unchanged-region disclosure honored: the one listed revision touching G04-P1's prose (R3, raw CSV field identifiers → verbal metric names) is presentation-only — every traced value, formula, denominator, comparator, replication count and binding survives identically in meaning, and the binding identifiers survive unchanged in the untouched author-input artifacts and the V2 json binding field. No value, formula, denominator, binding or hash changed across V1→V2.

**E-T7 — PASS** (fragment ET7_ET8)

- Instrument: `tmp/v1_v2_unified.diff` (114 lines total, 2 file-header lines + 9 hunks), pre-computed by the orchestrator party's shell and adjudicated here, not produced here. All 9 hunks are mapped: A1/A2 (structural header/title-provenance), B (**H3** — insertion of the entire `## V2 revision log` block), C (**H4** = R3/F3), D (**H5a** = R1/F1 AND **H5b** = R2a/F2a, one hunk covering two adjacent edits), E (**H6** = R5a/F5 AND **H7** = C1), F (**H8** = R2b/F2b), G (**H9–H11** = R5b–e/F5, three sites in one hunk), H (**H12** = C2a), I (**H13** = R4/F4 AND **H14** = C2b). Coverage equality holds — every logged revision appears in the diff, nothing unmapped; all remaining body lines are unchanged context.
- Net line arithmetic verified: Σ old counts = 75, Σ new counts = 87, net **+12** = +14 (revision-log insertion, hunk B) − 2 (C1 deletion, hunk E); V2 measured directly at **298 lines** ⇒ V1 = 298 − 12 = **286 lines**, entailed arithmetically from the diff alone — consistent with the claimed 286→298 without opening any V1 byte; per-hunk cumulative offset (+14 through hunk E, +12 from hunk F onward) consistent with the C1 −2 shift.
- Bidirectional spot-verification: the new side of every hunk was placed against the actual V2 file bytes (V2 lines 1–6, 15–34, 99–105, 111–117, 126–135, 154–160, 170–181, 240–246, 248–257) — all match verbatim. Non-failing observations recorded downstream: (1) untouched V1-carried regions contain register items outside the findings' logged scope (see Advisories — ED observations); they are identical-to-V1 bytes, absent from the diff, i.e., **not unmapped changes**; (2) the diff instrument embeds filesystem timestamps and carries no embedded content hash — orchestrator shell instrumentation, not hash-bound by G-T1/G-T8.

**E-T8 — PASS** (fragment ET7_ET8)

- Declared from the governance receipt's **independently measured** tables, not merely orchestrator claims: patch V2 markdown and JSON are the **current generation** (G-T1 rows 1–2 MATCH); the author-input pair `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.{md,json}` is current (G-T1 rows 3–4 MATCH — the `_V1_` token is name-generation, not a superseded byte state); the governance baseline pair is current (G-T1 rows 5–6 MATCH).
- Superseded `' 2.'` duplicate-generation copies: **do not exist** — G-T8 records spot-verification absent (no `' 2.'` filenames anywhere in `refine-logs/`, and a whole-tree search finds exactly one copy of each of the three input basename families); none was opened or consumed.
- V1 patch bytes `REC-M5_REVIEW_PATCH_V1_20260811.{md,json}` were **not consumed by anyone in this lane** — zero V1-byte access; the V1↔V2 comparison used exclusively the pre-computed `tmp/v1_v2_unified.diff` instrument. Declaration summary: nothing consumed is of unknown or stale generation.

---

## OVERALL VERDICT: PASS

**PASS.** The sole failing task of the superseded generation — **E-T3** (reader-facing register sweep), which alone carried the overall **FAIL** of `REC-M5_EDITORIAL_RECHECK_V4_20260823` — is **remediated and verified PASS on the V2 bytes** (`refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.{md,json}`), with findings F1–F5 confirmed remediated (R1, R2a/R2b, R3, R4, R5a–e) and advisories C1, C2a/C2b applied. With E-T1, E-T2, E-T4, E-T5, E-T6, E-T7 and E-T8 also PASS, **no failing or blocked task remains**: editorial-traceability clearance holds on the V2 patch generation. This verdict applies nothing and authorizes nothing by itself (see Not-done statements).

---

## Advisories carried forward (non-failing; optional-polish items for a future generation, not blockers)

- **A1** — single bare word "gate" survives at G05-F prose (line 178: "The gate classification is not empirical ground truth or native recovery"). It refers back to the target file's own retained heading `### Stricter endpoint-aware recovery gate` (which the group replaces the *text and table under*, not the heading) and carries no "promotion" semantics; under F5's definition it is not a violation. (Fragment ET1_ET3.)
- **A2** — supplementary-facing machine identifiers, outside F3's class (main-text results prose CSV metric columns): G05-B registry labels `local_structured`, `causal_temporal_smoother`, `fixed_rank_basis` (line 137; necessary audit-vs-active disambiguation, carried over from V4's borderline list); G07 candidate-table configuration keys `topologyVol=0.18`, `sparsity=0.55`, `wNoise=0.35`, `wDrop=0.30`, `truth.W`, `WEst` (lines 212–217) and `local_network` (line 221) — parameter/method labels in protocol disclosure, not data-schema field identifiers. (Fragment ET1_ET3.)
- **A3** — G02 line 84 "runtime or memory claims require an explicitly bound field" leans contract-language (carried from V4's borderline observations). (Fragment ET1_ET3.)
- **ED observations** (fragment ET7_ET8, non-failing) — untouched V1-carried register items outside the logged F1–F5 scope: the "promotion gate" wording in the Response-strategy bullet (V2[37], "simulation-only negative promotion gate") and the retained `NOT_RUN`/"claim activation"/`BLOCKED` tokens inside the G05-B *manifest-only* internal E01 traceability record (V2[139]). Both are **identical-to-V1 bytes** (absent from the diff) — not unmapped changes; E-T7 adjudicates hunk↔log completeness, not a whole-file semantic sweep; flagged so later generations scope their own sweeps.

None of the above blocks this receipt; they are optional-polish candidates for a future generation.

---

## Independence & provenance disclosure (full fidelity)

- Producing agent/model: **ox-alpha**, running under the **DeepSeek Harness**. This consolidated receipt pair is the sole write product of the consolidation session.
- Execution topology: **FOUR independent fragment reviewer instances** (each reads-only, no shell) + **ONE consolidation instance** (this agent). Verdicts were **self-adjudicated at fragment level** — each producing agent performed its own checks and issued its own verdicts; no second independent agent cross-checked a fragment within its session. **Consolidation was performed without altering any fragment verdict**, evidence item, or advisory text.
- Environmental deviations disclosed:
  1. **Shell/process spawning was unavailable to the fragment workers**, so SHA-256 values were **adopted via cross-lane corroboration** (the `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` G-T1/G-T8 measurements) instead of fresh measurement by this lane.
  2. The **V1↔V2 unified-diff instrument** (`tmp/v1_v2_unified.diff`) was produced by the **orchestrator party's shell** and adjudicated by the ET7_ET8 fragment, which also reconciled it against its own reads of the V2 bytes and arithmetic checks.
  3. **Route deviation** from the dispatch packet's requested provenance `gpt-5.6-terra`/`max`: the actual producer is **ox-alpha**. Recorded, not concealed.
  4. **V2 was synthesized by the orchestrator party**; this lane is independent of that party only within the shared environment.

---

## Explicit not-done statements

- Only this receipt pair (`refine-logs/REC-M5_EDITORIAL_RECHECK_V5_20260826.md` and `.json`) was written by this consolidation agent; nothing else was created, modified, or deleted.
- No manuscript, contract, formal-register, or generated-TeX file (`main.tex`, `supplementary.tex`) was edited or regenerated.
- No make target, test suite, or scientific execution was run.
- No git operation beyond read-only facts already published.
- No authorization is issued or implied by this receipt: M5-C closure, receipt registration, and M5-D/M5-F remain separate author decisions; `applied=false` and `submission_ready=false` remain operative.
- No claim was activated; all scientific ceilings of the underlying records remain intact; all 26 candidates remain `CANDIDATE_NOT_APPLIED`.
- No `' 2.'` conflict copy was opened by any worker in this lane's topology.

---

## Fragment ledger (evidentiary basis of this receipt)

| # | Fragment file | Tasks adjudicated | Fragment verdicts |
| --- | --- | --- | --- |
| 1 | `refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET1_ET3_20260826.md` | E-T1, E-T3 | PASS, PASS (advisories A1/A2/A3) |
| 2 | `refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET2_20260826.md` | E-T2 | PASS |
| 3 | `refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET4_ET5_ET6_20260826.md` | E-T4, E-T5, E-T6 | PASS, PASS, PASS |
| 4 | `refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET7_ET8_20260826.md` | E-T7, E-T8 | PASS, PASS (plus non-failing ED observations) |

Cross-reference sources consulted during consolidation: `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` (hash corroboration via G-T1 rows 1–2 and G-T8) and `refine-logs/REC-M5_EDITORIAL_RECHECK_V4_20260823.md` (superseded prior generation; overall FAIL on E-T3 only).

— End of receipt.
