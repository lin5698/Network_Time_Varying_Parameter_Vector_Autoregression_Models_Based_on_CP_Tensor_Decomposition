# REC-M5 Editorial Recheck V4

Record class: `editorial_recheck_receipt`
Generated: 2026-08-26
Timezone basis: `Asia/Shanghai`
Lane: A — editorial traceability
Dispatch packet: `refine-logs/REC-M5_RECHECK_DISPATCH_V1_20260823.md` (measured SHA-256 `45326339fea28f83333bdd9aa540af97830e51ef806abfcbe69282157a7b5220`)
Supersedes: `REC-M5_EDITORIAL_RECHECK_TERRA_V3_20260812` (`BLOCKED`, whose finding TERRA-V3-E1 referenced superseded input hashes `b95a0960…`, `8c0546a7…`, `c7664285…`; its finding text was read as context only, its hashes were not adopted).

## OVERALL VERDICT

**FAIL** — editorial clearance is withheld on current bytes solely by E-T3 (reader-facing register violations inside proposed manuscript text). Input integrity, byte-generation control, unit traceability, manifest-only containment, claim ceilings, author-input traceability and TERRA-V3-E1 closure all verified `PASS`. No BLOCKED condition exists: every opened authoritative input matched its expected hash and byte count exactly. Because one lane task carries `FAIL`, this lane does not clear M5-C editorial traceability, and per the dispatch closure condition the package is not ready for receipt registration or M5-D request until the E-T3 revisions are made and re-reviewed on the revised bytes. All flagged text sits inside `CANDIDATE_NOT_APPLIED` proposals; nothing has been applied to any manuscript source.

## Per-task verdicts

| Task | Verdict |
| --- | --- |
| E-T1 — TERRA-V3-E1 closure adjudication | `PASS` |
| E-T2 — 26-unit traceability | `PASS` |
| E-T3 — reader-facing test of proposed paragraphs | `FAIL` |
| E-T4 — four `manifest-only` labels | `PASS` |
| E-T5 — claim ceilings | `PASS` |
| E-T6 — author-input traceability | `PASS` |
| E-T7 — byte-generation declaration | `PASS` |

## Files opened — measured size and SHA-256

| Path | Role | Measured bytes | Measured SHA-256 | Expected match |
| --- | --- | ---: | --- | --- |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md` | authoritative input | 27202 | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` | MATCH (27202 / `69888df4…`) |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.json` | authoritative input | 28217 | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` | MATCH (28217 / `938e5218…`) |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | authoritative input | 10097 | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` | MATCH (10097 / `1555484a…`) |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | authoritative input | 15091 | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` | MATCH (15091 / `ebb639ed…`) |
| `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | authoritative input | 1467 | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` | MATCH (1467 / `dfd4385f…`) |
| `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | authoritative input | 2987 | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` | MATCH (2987 / `94668a91…`) |
| `refine-logs/REC-M5_RECHECK_DISPATCH_V1_20260823.md` | instruction source (this lane's dispatch) | 9924 | `45326339fea28f83333bdd9aa540af97830e51ef806abfcbe69282157a7b5220` | n/a (no expected value declared) |
| `refine-logs/REC-M5_EDITORIAL_RECHECK_TERRA_V3_20260812.md` | prior-receipt context only | 3898 | `2a83385f4f07b03199ce77cb9666e8593484c26ebd2a2cf54ecaa98523261202` | n/a (context) |
| `refine-logs/REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823.md` | advisory only, NOT treated as evidence | 8596 | `d768bc973faf552be2284a8cf8b373d63b736cbb51d6083aaa976fd9e56fef2f` | consistent with dispatch-declared prefix `d768bc97…` |
| `refine-logs/REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823.json` | advisory only, NOT treated as evidence | 21753 | `dfc8ac5ece1dd3a2387b511355b10528eab3a84b4987374eb6368d15bcb2a0c3` | consistent with dispatch-declared prefix `dfc8ac5e…` |
| `refine-logs/REC-P0_WORKING_COPY_INTEGRITY_V1_20260823.md` | advisory only, NOT treated as evidence | 7666 | `e57d61afbe36e5ea807480f527f784cb73eed2fb7f274b8c586028724edfeb86` | n/a (context) |

Six of six authoritative inputs match expected byte counts and SHA-256 values exactly. All three machine records parse as valid JSON. Zero mismatches.

## E-T7 — byte generation consumed

The **current generation** of all six authoritative inputs was consumed, proven by exact-path resolution plus measured-hash equality with the dispatch's expected values. The `refine-logs` directory does contain `' 2.'` conflict copies of two authoritative names (`REC-M5_REVIEW_PATCH_V1_20260811 2.md/.json`, `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812 2.md/.json`); **none of them was opened**, directly or indirectly. No path used in this review resolved to a conflict copy, so the conditional BLOCKED of E-T7 is not triggered. This is consistent with the advisory P0 record's stale-generation hazard table, which lists different copy-side hashes (`336c3cc4…`, `8d9b1d2a…`, `d622854a…`, `83197e88…`) that appear nowhere in my measurements.

## E-T1 — TERRA-V3-E1 closure adjudication (PASS)

Verified on current bytes, independently of the preflight:

- The G04 section (patch md lines 82–100) contains exactly one `Target:` line and four `Proposed paragraph N:` labels, each followed immediately by a single blockquote. There is zero interleaved prose between proposed paragraphs 1 and 2 (or between any of them).
- Characteristic residue strings return zero matches across the whole patch md: `AIN-RESULT binding` 0, `partial M5-A response` 0, `remaining author inputs` 0, `AUTHOR_INPUT_NEEDED` 0. The token `AIN-` occurs exactly once in the file, at line 283.
- Line 283 ("- G04: AIN-RESULT is confirmed and bound to the released benchmark summary; all author-input groups are resolved, while independent semantic review remains required.") now sits under `## Missing information and risk flags` (line 277), a record-level status section outside every manuscript-target group, and the adjacent line 284 explicitly marks that content "not manuscript text".

Independent judgment on adequacy: the relocation is a genuine remedy, not merely displacement, because (a) the destination is structurally unreachable by paragraph-level application — the statement appears in no `clause_traceability` entry, no edit-group payload, and no blockquote; (b) the relocated wording no longer contradicts the machine state — it now agrees with the author-input JSON (`author_input_needed: []`, `still_unresolved: []`, all acceptance flags true), which was the substance of the original E1 complaint; and (c) it matches the remedy the V3 finding itself prescribed ("move it to a manifest-only traceability section or remove it"). Scope caveat recorded: the closure of E-T1 concerns process-note *placement* only. Governance vocabulary that remains *inside* G04 Proposed paragraph 4 is a distinct defect and is reported under E-T3 below; it does not reinstate E1, whose locus was an unmarked interleaved note.

## E-T2 — 26-unit traceability (PASS)

Programmatic validation of `unit_coverage` in the patch JSON, cross-checked against the markdown patch index:

- Total units: 26. Duplicate `unit_id`s: none. Orphans (missing/invalid `source_item` or out-of-range group anchor): none.
- Distribution: V1-026 ×3 (P-001→G05, P-002→G01, P-003→G04); V1-033 ×13 (M01,M02→G02; M03→G03; R01–R05→G04; S01–S05→G05); V1-045 ×10 (RANK,WINDOW,FAILURE→G05; ALS→G06; TOPOLOGY→G07; STABILITY→G08; REPLICATION,SCOPE→G09; UNRUN,RESOURCE→G10).
- Group anchors hit: G01×1, G02×2, G03×1, G04×6, G05×9, G06×1, G07×1, G08×1, G09×2, G10×2 — every group in G01–G10 carries ≥1 unit; no unit maps outside G01–G10.
- Bidirectional consistency: every `traceability.G*.source_units` entry corresponds to a `unit_coverage` row and vice versa (no missing, no extra); every unit is referenced by at least one `clause_traceability` clause and no clause references an unknown unit; the markdown patch index and the proposal-native crosswalk agree with the JSON.

Violations found: **0**.

## E-T3 — reader-facing test (FAIL)

Every proposed paragraph/blockquote was read as would-be journal prose. Flagged findings, in descending severity:

- **F1 (major) — patch md line 100, G04 Proposed paragraph 4:** "its scientific execution is `NOT_RUN`, its claim activation is `BLOCKED`, and it was not used to extend the benchmark claim." Internal execution/verdict codes and the governance concept "claim activation" embedded in results-section prose destined for `results_validation.md`. Published text must express this in plain scientific English without weakening the boundary (the audit output was descriptive and supported no comparative claim).
- **F2 (moderate) — lines 100 and 145 (G04-P4, G05-D):** "author-confirmed amplitudes and generation-versus-observation roles" / "have author-confirmed amplitudes". Process-provenance vocabulary about who confirmed what has no place in published text; readers need the values and their roles, not the confirmation event.
- **F3 (moderate) — line 88, G04 Proposed paragraph 1:** raw data-schema field identifiers `` `coef_error_median` `` and `` `girf_error_median` `` printed inside main-text results prose. These are internal CSV column names; the metrics should be named verbally, with field identifiers confined to supplementary/data-availability material.
- **F4 (moderate) — line 239, G10 proposed insertion:** status codes `` `NOT_RUN/ABSTAIN` `` and `` `BLOCKED/null` `` in supplementary scope prose. The abstention facts are publishable; the internal code spellings are not appropriate as-is.
- **F5 (minor) — lines 110–115 (G05-A table) and 161–166 (G05-F):** project-internal gate vocabulary in reader-facing tables ("Simulation-only promotion gate", "Promotion status … Not promoted", "prespecified promotion rule"). Defensible as pre-registered decision-rule reporting, but the "promotion" register is project-governance language; standard phrasing should be considered.

Borderline observations, flagged but not scored as failures: the `OUTSIDE TARGET` mark (G03, G04-P2, G05-C) is acceptable because it is introduced and defined inline as the paper's own terminology; registry labels `local_structured`/`causal_temporal_smoother`/`fixed_rank_basis` (G05-B, line 125) are borderline machine identifiers retained for necessary disambiguation; "explicitly bound field" phrasing (G02, line 70) leans contract-language. No hash string appears inside any blockquoted proposed text (verified mechanically; the only long hex in the file, `9cfe55a7…`, is in the G06 source-binding note outside the blockquote, in a REVIEW_ONLY group).

Remediation note: these rewrites must preserve the E-T5 ceilings verbatim in meaning — plain-English restatement, not deletion, of the non-execution and non-claim boundaries. After revision, this lane must be re-dispatched on the revised bytes.

## E-T4 — four `manifest-only` labels (PASS)

Positions verified on current bytes: lines **127** (G05-B, "Internal E01 traceability record (manifest-only; do not apply as manuscript text)"), **231** and **241** (G09/G10, "Internal traceability note (manifest-only)…"), **242** (G10, "Internal state record (manifest-only)…"). Each label unambiguously excludes its content from manuscript application: the tag `manifest-only` is applied consistently, the first occurrence spells out the exclusion, and the record-level section at line 284 independently states such notes "are not manuscript text". Reachability: none of the four notes appears in any `clause_traceability` key (G01-P1…G10-P1), none is inside a blockquoted proposal, the JSON `edit_groups` carry no text payloads, and application anchors are defined over target-file paragraphs (`pre_apply_anchor_checks`) rather than patch-file prose. Under the documented anchoring mechanism, no manifest-only content is reachable by a paragraph-level applier.

Residual advisories (do not change the verdict): lines 231/241/242 carry the `(manifest-only)` tag without the spelled-out "do not apply as manuscript text" phrase that line 127 has; all four sit physically adjacent to proposed text inside their group sections, so a naive whole-section copier that ignores the documented anchoring could ingest them; and G05-B carries a duplicated label pair ("Proposed text:" then "Proposed reader-facing text:", lines 121–123) which slightly blurs which marker governs the blockquote.

## E-T5 — claim ceilings (PASS)

- **V1-026**: stays descriptive; scientific execution `NOT_RUN` / activation `BLOCKED` preserved in the boundaries table (md line 31), JSON `scientific_boundaries.V1-026`, and G04-P4/G05-B wording; forbidden list (CI, ranking, superiority, equivalence, native-held-out, promotion) intact. The quantified median reductions in G04-P1 are bounded tested-endpoint statements whose own closing sentences negate empirical validation, fairness and broad superiority.
- **V1-033**: simulation-only preserved (md lines 32, 70–72, 145, 153, 166–168; JSON `evaluation: simulation_only`, ground truth `NOT_EVALUABLE`); the five retained gaps (chronology, selection inputs, held-out query identity, endpoint signature, truth isolation) are restated unresolved; the negative gate result is explicitly "not a universal failure theorem".
- **V1-045**: limited to N=20/N=50 (md lines 33, 229; JSON `scope`); N=100/N=200 stated `NOT_RUN/ABSTAIN` and resource telemetry `BLOCKED/null` (md lines 25, 33, 239, 242; JSON fields identical); single-execution seed coverage explicitly distinguished from repeated-run reproducibility.
- **G06**: disposition `AUTHOR_CONFIRMED_REVIEW_ONLY` / `CANDIDATE_NOT_APPLIED` (md line 172; JSON anchor_mode `author_confirmed_review_only`); proposed text affirmatively negates convergence and global optimality (md line 178); the unowned 100/80 wording is barred from import (md line 192).
- **G07**: disposition `AUTHOR_CONFIRMED_REVIEW_ONLY` / `CANDIDATE_NOT_APPLIED`; boundary text negates matched ranking and general topology-robustness claims and discloses asymmetric coverage (md line 209); 50%-attenuation kept outside CAL-E03 (md line 211).

No ceiling exceeded; no convergence, global-optimum, robustness or generalization reading is available from the current candidate text.

## E-T6 — author-input traceability (PASS)

Each AIN-derived value traces to `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.{md,json}`:

- Four percentages: author values 93.55203369881073 → 93.6, 96.76394154622214 → 96.8, 82.54278845800611 → 82.5, 87.32161861932515 → 87.3 (unrounded + declared one-decimal display); the patch prints exactly the display values at line 88. Rounding checked and correct.
- Formula: author expression `100 * (local_network_metric_median - cp_network_metric_median) / local_network_metric_median`, statistic "ratio of across-replication medians"; patch renders $100\times(m_{\mathrm{local}}-m_{\mathrm{CP}})/m_{\mathrm{local}}$ — same expression under renamed symbols.
- Denominator: author-recorded as the local_network metric median for the same scenario and endpoint; patch states $m_{\mathrm{local}}$, the across-replication median of the unrestricted-local comparator. Consistent.
- Endpoint/comparator binding: `coef_error_median` / `girf_error_median` fields, comparator local_network vs cp_network, 20 replications per primary scenario — all present in both records and reflected in the patch.
- Evidence hash `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`: identical in the author-input md (line 38), the author-input JSON (`submitted_evidence`, bound to `output/natcs_benchmarks/benchmark_summary.csv`), and the patch JSON `evidence_bundle_hashes`.
- Unavailable sources honored: AIN-ALS-06/07 and AIN-SOURCE-01..04 recorded Unavailable with generated TeX excluded; the patch nowhere reconstructs the application/bootstrap 100/80, spectral-radius or 50%-attenuation wording from generated TeX (G06 bars import, G08 refuses reproduction/mapping, G07 keeps attenuation outside CAL-E03). Generated TeX was never opened during this review.
- Author confirmation events recorded with scopes AIN-RESULT; AIN-ALS+AIN-TOPOLOGY+AIN-SOURCE-01/04; AIN-SOURCE-02; AIN-SOURCE-03; `still_unresolved: []`.

Advisory note (cosmetic, does not affect the verdict): the evidence_path_key locator strings differ by one line-range endpoint between the author-input md (`…442-482`) and JSON (`…442-483`) for the topology rows; all bound values, amplitudes and hashes are identical.

## Independence and provenance disclosure

This receipt was produced by the agent/model **ox-alpha** running under the DeepSeek Harness, as an independent read-only reviewer, in **direct self-adjudication** mode: the reviewing agent performed the checks and issued the verdicts itself; no second independent party adjudicated this receipt, no external model, CLI model invocation or external payload service was used, and no subagents were spawned. Disclosure of route deviation: the dispatch requests provenance `gpt-5.6-terra` / `max`; this reviewer is ox-alpha, not that route, so the dispatch's provenance preference is **not satisfied** and this fact is recorded rather than concealed. The prior deterministic preflight was read as localization context only; none of its structural `PASS` results was accepted as this lane's finding — every verdict above rests on measurements and readings performed here against the six authoritative inputs. Context honesty note: the orchestrator-supplied P0 update (iCloud working-copy repair closed 2026-08-26; HEAD resolves to e7ce60c…; `git fsck --full` exit 0; 76 modified tracked files relative to HEAD) is recorded as received context and was **not** independently re-measured, because git execution is prohibited for this lane.

## Explicit statement of what was NOT done

- No file was created, modified, moved or deleted except this receipt pair (`REC-M5_EDITORIAL_RECHECK_V4_20260823.md` and `.json`). All existing files, including all `' 2.'` conflict copies, remain untouched.
- No git command, no `make` target, no test suite and no scientific entry point was executed; no build was run.
- No manuscript source, formal register, authorization file, frozen record or generated TeX (`main.tex`, `supplementary.tex`) was edited or regenerated; generated TeX was never read.
- No claim was activated and no scientific result was produced or promoted; all 26 candidates remain `CANDIDATE_NOT_APPLIED`.
- No authorization is granted or implied by this receipt. Manuscript mutation, formal-register mutation, generated-TeX mutation, scientific execution and claim activation remain NOT_AUTHORIZED / PROHIBITED; M5-D and M5-F remain separately required.
- The four `manifest-only` notes, the record-level risk-flag section and all governance scaffolding were treated as record content, never as applicable manuscript text.

— End of receipt.
