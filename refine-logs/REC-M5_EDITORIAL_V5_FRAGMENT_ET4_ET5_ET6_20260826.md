# REC-M5 Editorial V5 Fragment — E-T4 / E-T5 / E-T6

- Fragment id: `lane_a2_frag_ec_et4_et5_et6` → `REC-M5_EDITORIAL_V5_FRAGMENT_ET4_ET5_ET6_20260826.md`
- Date: 2026-08-26 (Asia/Shanghai)
- Lane: editorial traceability (M5-C), read-only fragment worker
- Adjudication mode: fail-closed; any weakening or extension would be recorded as FAIL

## Verdict summary

| Code | Scope | Verdict |
|------|-------|---------|
| **E-T4** | Manifest-only containment on V2 (G05-B / G09 / G10 internal notes) | **PASS** |
| **E-T5** | Claim ceilings preserved verbatim-in-meaning in V2 proposed text | **PASS** |
| **E-T6** | Author-input traceability unchanged across V1→V2 | **PASS** |

---

## E-T4 — Manifest-only containment on V2: **PASS**

### Inventory of manifest-only notes in `REC-M5_REVIEW_PATCH_V2_20260826.md`

Five manifest-only-flagged notes are present, matching the expected population of five:

1. **G05-B, line 139** — "Internal E01 traceability record **(manifest-only; do not apply as manuscript text)**: the audit covers 16 cells per method … Scientific execution is `` `NOT_RUN` `` and claim activation is `` `BLOCKED` ``; these are descriptive audit counts, not active benchmark rows or ranking evidence."
2. **G09, line 243** — "Internal traceability note **(manifest-only; do not apply as manuscript text)**: this paragraph refers to REC-M2C CAL-E03:164."
3. **G10, line 253** — "Internal traceability note **(manifest-only; do not apply as manuscript text)**: this paragraph refers to REC-M2C CAL-E03:164."
4. **G10, line 254** — "Internal state record **(manifest-only; do not apply as manuscript text)**: $N=100$ and $N=200$ are `` `NOT_RUN/ABSTAIN` ``; resource telemetry is `` `BLOCKED/null` ``."
5. **Risk flags, line 296** — "**Manifest-only traceability:** the four G04 values, ratio-of-medians formula, denominator, endpoint/comparator fields and evidence hash were confirmed on 2026-08-12 … **This note is not manuscript text.**" (This is the G04 author-input traceability note; the V2 json `verification.semantic_service_note` independently calls it "the internal G04 traceability note is manifest-only".)

Count reconciliation: the four enumerated labels (G05-B ×1; G09 ×1; G10 ×2) all carry the exact harmonized parenthetical "(manifest-only; do not apply as manuscript text)" — confirming C2a/C2b landed ("harmonized the spelled-out exclusion phrase \"do not apply as manuscript text\"", V2 revision log, line 30). The fifth note (item 5) sits in the "Missing information and risk flags" section outside any proposal block and uses the equivalent exclusion sentence "This note is not manuscript text."; C2a/C2b was scoped to "G09/G10 manifest-only notes" only, so its phrasing is containment-equivalent, not a harmonization miss.

### Containment checks

- **Not inside any blockquote proposal.** Every proposed-text block in the V2 md is `>`-prefixed (e.g., G05-B reader-facing text at line 137, G09 proposed text at line 241, G10 proposed text at line 251). Notes 1–4 are plain paragraphs immediately following those blocks (lines 139, 243, 253–254) with no `>` prefix; note 5 is a risk-flag bullet. No manifest-only note text appears inside any "Proposed …text" block.
- **Absent from `clause_traceability`.** The V2 json `clause_traceability` object (lines 513–576) contains only keys `G01-P1` … `G10-P1` whose values are REC-M3 unit-id strings (e.g., `"G05-B": ["V1-026:P-001"]`). No key or value contains, names, or embeds any of the five notes.
- **Not reachable by a paragraph-level applier.** Under `pre_apply_anchor_checks` (json lines 595–712; algorithm "SHA-256 of UTF-8 paragraph fragments after CRLF normalization and trimEnd; paragraph numbering follows blank-line splitting", `fail_closed_on_drift: true`), an applier operates over paragraphs of the *target* manuscript files (methods_estimator.md, results_validation.md, supp_note4_benchmarks.md, methods_data.md, methods_uncertainty.md, supp_note7_repro.md para 4, supp_note8_scope.md para 8, controlled_benchmark_contract.json). All five notes live exclusively inside the patch document itself — they are neither anchor targets nor part of any serialized proposed text, so no anchor-hash-driven paragraph operation can select, carry, or emit them into a target file. Redundant barriers: every edit_group `disposition` is `CANDIDATE_NOT_APPLIED`, and the application rule (md line 14) bars any application "until M5-C independent review passes and the user separately authorizes manuscript mutation."

Conclusion: all five notes are contained to the manifest; none is reachable by a paragraph-level applier under the documented anchor mechanism. No containment breach found → **PASS**.

---

## E-T5 — Claim ceilings preserved verbatim-in-meaning in V2 proposed text: **PASS**

### V1-026 (native-comparator audit; forbidden list)

- Post-R1 plain English (G04-P4, line 114): "The separate frozen native-comparator output is **descriptive only**; it **was not executed** under this benchmark's evaluation protocol, **carries no evaluative claim of its own**, and **was not used to extend the benchmark result**." — exactly the required four semantics, with the `NOT_RUN`/`BLOCKED` codes and the governance term "claim activation" removed from manuscript prose per R1 (revision log line 24). The codes survive only in the governance register (Scientific ceilings table line 45) and the manifest-only G05-B internal note (line 139), i.e., off-manuscript surfaces.
- Descriptive-only role also preserved at G01 (line 74: "are not aliases for, or additional rows in, the active CP, Tucker or unrestricted-local benchmark"; boundary line 76: "protocol disclosure only"), G05-B reader-facing text (line 137: "the audit is not an additional active benchmark row").
- **Forbidden list intact** (Scientific ceilings, line 45): "No CI, ranking, superiority, equivalence, native-held-out claim or promotion." — all six barred categories present; corroborated by json `scientific_boundaries.V1-026.forbidden` (confidence interval claim / ranking / superiority or equivalence / native-held-out or general-performance claim / promotion) and response strategy line 35 ("do not add active benchmark rows, empirical ground truth, confidence intervals, superiority claims, claim activation or manuscript promotion").

### V1-033 (simulation truth ≠ empirical ground truth; five unresolved gaps)

- G02 (line 84): "These objects provide **simulation truth** within the declared design; they are **not independent empirical ground truth**, empirical calibration evidence or evidence of general performance."
- G02 boundary (line 86): "it remains **simulation-only** and limited to the declared $H=4$ endpoint; its **chronology, selection inputs, held-out query identity, endpoint signature and truth isolation remain unresolved**." — all five gaps restated, in canonical order; repeated at G05-E (line 165), Scientific ceilings (line 46), and risk flags (line 294: "no wording in this patch closes them").
- G05-D (line 157): "The DGP-generated objects are simulation truth, not independent empirical ground truth."

### V1-045 (N=20/N=50 scope; abstentions; telemetry; single execution)

- Scope: Scientific ceilings line 47 "N=20/N=50 only"; json `scope: "N=20/N=50 only"`.
- Post-R4 plain-word abstention (G10 proposed text, line 251): "$N=100$ and $N=200$ **were not evaluated**, and we **abstain from any claim at either scale**. No performance, failure, resource or scalability conclusion is made for either scale." Status codes (`NOT_RUN/ABSTAIN`, `BLOCKED/null`) remain confined to the manifest-only internal state record (line 254) and register surfaces, consistent with R4 (revision log line 27).
- Telemetry unavailable: line 251 "Wall-clock time, CPU time, peak memory or RSS, GPU time and per-cell runtime were **unavailable** for this audit; exit status, process state, record counts and log presence are **not substitutes** for resource measurements".
- Single-execution boundary where stated (G09, line 241): "each scoped cell has 20 recorded seeds **from one execution** … Seed coverage from one execution is **not repeated-run reproducibility** and does not replace the original replication contract"; json: `execution_count: 1`, `repeated_run_reproducibility: false`.

### G06 (ALS stopping semantics)

- Disposition (line 184): "`AUTHOR_CONFIRMED_REVIEW_ONLY`; no manuscript or contract change is applied." Corroborated by json `anchor_mode: "author_confirmed_review_only"` / `disposition: "CANDIDATE_NOT_APPLIED"`.
- Fixed-60 / no-tolerance semantics (line 190): "performs a **fixed count of 60** alternating-least-squares iterations when the call completes normally. It **does not monitor** an objective or residual and has **no convergence tolerance or early-stop predicate**. The $10^{-6}$ value regularizes the Gram systems; it is **not a stopping tolerance**." Matches author input AIN-ALS-01…05 verbatim in meaning.
- Affirmative negation (line 190): "These implementation semantics **do not establish convergence or global optimality**."; risk flag line 291 repeats it.
- Barred import (line 204): "The application/bootstrap 100/80-iteration wording **has no identified canonical Markdown owner and must not be imported** into CAL-E03 or patched in generated TeX." Matches AIN-ALS-06/07/08 and json `compiled_100_80_settings: "SEPARATE_CANONICAL_MARKDOWN_SOURCE_UNAVAILABLE"`.

### G07 (topology perturbation amplitudes)

- Disposition (line 208): "`AUTHOR_CONFIRMED_REVIEW_ONLY`; no manuscript or contract change is applied."
- Asymmetric replication disclosed (table lines 214–217: "local 3; each other released method 20"; sparse row "each released method 3") and in reader-facing text (line 221): "Released stress coverage is **not uniformly matched**: `local_network` has three replications … while the other released methods have twenty; the combined sparse/misspecified row has three per released method."
- Negations (line 221): "These rows therefore provide bounded diagnostics and **do not support a matched ranking or general topology-robustness claim**."; risk flag line 292 repeats both negations. Matches AIN-TOPOLOGY author confirmation ("do not treat these rows as a matched ranking or general topology-robustness result").
- 50% attenuation (line 223): "The application-layer 50% top-exposure attenuation has no identified canonical owner and **remains outside CAL-E03**." Amplitudes in the V2 table are value-identical to the author-input request (0.18/0.15/0/0; 0.08/0.55/0.18/0; 0.06/0.15/0/0.30; 0.06/0.15/0.35/0).

### Weakening/extension sweep

R5a–e's restatement of promotion-gate vocabulary as "pre-registered decision rule" wording (G05-A/G05-F) preserves semantics: outcomes stay "Threshold not met" (0/16, 6/16) with "the negative result is not a universal failure theorem" and the inheritance boundary intact (line 178–180). G08's conditional ("not interchangeable … unless an explicit contract-bound metric mapping is serialized in a machine-readable artifact") keeps the non-interchangeability default and does not reproduce, validate, or map the unowned spectral-radius wording (disposition line 227). No ceiling was weakened and no claim extended anywhere in the proposed text → **PASS**.

---

## E-T6 — Author-input traceability unchanged across V1→V2: **PASS**

- **Percentages at G04-P1** (line 102): "reduced median effective-operator error by **93.6% and 96.8%**, respectively, relative to unrestricted local rolling estimation (Fig. 3a). Median finite-horizon unit-shock response error decreased by **82.5% and 87.3%** under the same comparison (Fig. 3b)." Identical to author-input display values (json `display_percent`: 93.6 / 96.8 / 82.5 / 87.3; unrounded 93.55203369881073 / 96.76394154622214 / 82.54278845800611 / 87.32161861932515).
- **Formula** (line 102): "computed as $100\times(m_{\mathrm{local}}-m_{\mathrm{CP}})/m_{\mathrm{local}}$" — the confirmed ratio-of-medians expression `100 * (local_network_metric_median - cp_network_metric_median) / local_network_metric_median` (author-input md line 37; json `AIN-RESULT-FORMULA.expression`, `statistic: "ratio of across-replication medians"`).
- **Denominator** (line 102): "$m$ is the **across-replication median** of the same scenario's effective-operator error or finite-horizon unit-shock response error", structured as m_local − m_CP over m_local with the unrestricted-local comparator named in P1 — matching json `denominator: "local_network metric median for the same scenario and endpoint"`.
- **Endpoint/comparator binding**: author-input locators bind `coef_error_median` / `girf_error_median`, `scale_n15`/`scale_n30`, `local_network/cp_network`, 20 replications per primary scenario (md lines 19–22; json `operator_field`/`response_field`/`comparator`/`candidate`/`replications_per_primary_scenario: 20`). V2 preserves the binding verbally in P1 ("Across **20 replications** at each of the primary $N=15$ and $N=30$ scales … relative to **unrestricted local rolling estimation**") and in the V2 json (`author_input_resolved[AIN-RESULT].binding`: "ratio of across-replication medians; **local_network versus cp_network**; one-decimal display"; risk flag line 296: "four G04 values, ratio-of-medians formula, denominator, endpoint/comparator fields and evidence hash were confirmed on 2026-08-12").
- **Evidence hash continuity** — `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1` present in all three locations:
  - author-input md line 38 ("The evidence SHA-256 is `c29aa141…9cc1`.");
  - author-input json lines 221/233/245/257 (`evidence_sha256` per topology row) and line 267–268 (`submitted_evidence`: `output/natcs_benchmarks/benchmark_summary.csv`);
  - V2 patch json `evidence_bundle_hashes` line 587: `"output/natcs_benchmarks/benchmark_summary.csv": "c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1"` (verified by direct read of `REC-M5_REVIEW_PATCH_V2_20260826.json`, solely for this field).
- **Unavailable sources still barred everywhere in V2**: Source ownership (line 51): canonical sources for "application/bootstrap 100/80-iteration, spectral-radius and 50%-attenuation wording are unavailable. None may be recovered from generated TeX or imported into the controlled benchmark." Reinforced at G06 (line 204), G07 (line 223), G08 (line 227: "does not reproduce, validate or map the unowned spectral-radius wording"), checklist lines 282–284 ([x] records for all three), risk flag line 293, and json `source_ownership.unresolved_canonical_source` ("None; … author-confirmed unavailable"). No proposed text reconstructs any of the three wordings.
- **Unchanged-region disclosure (value-level)**: V2's revision log states "All non-listed bytes are identical to V1" (line 20) and json `v2_revision.semantic_ceiling_changes: "none; restatements preserve boundary meanings verbatim"`. One listed revision did touch G04-P1's prose: R3 "removed raw CSV field identifiers from main-text prose; metrics now named verbally" (revision log line 26). This is a presentation-only change — every traced value (four percentages, formula, denominator, comparator, 20-replication unit) is carried through identically in meaning, and the binding identifiers survive unchanged in the untouched author-input artifacts and in the V2 json binding field. No value, formula, denominator, binding, or hash changed across V1→V2 → **PASS**.

---

## Provenance disclosure

- Model: ox-alpha (self-adjudicated fragment worker; independent read-only review; no parent-conversation context assumed).
- Tool discipline: reads-only via the read tool; **no bash/glob/grep/shell used**; sole write = this fragment file (written early as a skeleton, then replaced by this final content).
- Inputs read: `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md`; `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md`; `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json`; plus `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json` read solely to verify the `evidence_bundle_hashes` field for E-T6 (as sanctioned by the task brief). Hash corroboration in `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` G-T1 was not independently reopened (out of read scope).
- No manuscript, register, payload, or governance file was mutated; no git operations; no execution of any scientific step.
