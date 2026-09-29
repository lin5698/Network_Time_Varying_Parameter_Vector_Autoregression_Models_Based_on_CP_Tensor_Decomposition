# REC-M5 Governance Recheck V5 (Lane B — governance manifest)

- record_class: `governance_recheck_receipt`
- record_id: `REC-M5-governance-recheck-v5-20260823`
- generation_date: 2026-08-26
- timezone: Asia/Shanghai (timestamps +08:00)
- generated_at_utc+8: 2026-08-26T03:44:52+08:00
- dispatch: `refine-logs/REC-M5_RECHECK_DISPATCH_V1_20260823.md` (Lane B)
- lane_scope: governance manifest recheck of current bytes, independent read-only reviewer
- repo_HEAD_at_measurement: `e7ce60c28f27c17ecfffe5348dd04d8c957fb077` (branch `refs/heads/codex/m5-current-luna-science-recheck`)
- context_update_reflected: P0 iCloud working-copy repair CLOSED 2026-08-26; all bytes materialized; `git rev-parse HEAD` works; `git status --porcelain -uno` = 76 changed tracked entries.

## 0. Independence and provenance disclosure

Producing agent/model: **ox-alpha** (LLM developed by an undisclosed organization), executed as a delegated read-only Lane B reviewer subagent under DeepSeek Harness. All measurements in this receipt were taken by this agent directly (`shasum -a 256`, Python 3 `hashlib`, exact-path existence probes, read-only git `rev-parse`/`status`/`ls-files`). Verdicts are **self-adjudicated** by the same agent that performed the measurements. This agent is not the producer of any audited record, did not participate in TERRA_V4/V5 reviews, and received no instruction channel other than the dispatch text quoted in the tasking. No preflight recomputation was trusted: every anchor hash was recomputed from file bytes by this agent's own code.

## 1. G-T1 — Authoritative input hashes (verdict: PASS)

All six opened at their exact canonical paths. Measured vs expected:

| # | Path | Expected SHA-256 | Measured SHA-256 | Bytes | Delta |
| --- | --- | --- | --- | --- | --- |
| 1 | `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md` | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` | 27202 | none |
| 2 | `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.json` | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` | 28217 | none |
| 3 | `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` | 10097 | none |
| 4 | `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` | 15091 | none |
| 5 | `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` | 1467 | none |
| 6 | `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` | 2987 | none |

6/6 measured == expected. **G-T1 = PASS.**

## 2. G-T2 — V10 path-name resolution (verdict: PASS)

Independent exact-path probes (no globbing), plus `git ls-files`:

- `refine-logs/REC-M5_GOVERNANCE_RECHECK_V10_20260812.md` — ABSENT on disk, untracked in git index.
- `refine-logs/REC-M5_GOVERNANCE_RECHECK_V10_20260812.json` — ABSENT on disk, untracked in git index.
- `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}` — EXIST; hashes equal the dispatch-bound values (see §1 rows 5–6).

Adjudication: the governance-baseline ROLE is discharged by `REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}`. Its content performs the baseline function end-to-end: binds the current-byte hash chain of all four M5-A/M5-B records (`current_artifacts`, matching measured values), declares result `CURRENT_HASH_CHAIN_READY_FOR_TERRA_MAX_DIRECT_REVIEW`, restates the full authorization boundary (manuscript/formal-register NOT_AUTHORIZED; scientific payload, authorization file, generated TeX PROHIBITED; claim activation NOT_AUTHORIZED; git operations NONE), and names the next gate (fresh Terra/max direct review over the three roles). The name `GOVERNANCE_RECHECK_V10`, under which TERRA_V4 stalled, is a nominal label that does not exist anywhere in this tree; the mismatch is nomenclature, not substance. Per task constraint the V10 baseline was **not edited** — its bytes are bound inside the SCIENTIFIC_RECHECK_TERRA_V5 PASS receipt and remain intact here (measured dfd4385f…/94668a91…). **G-T2 = PASS (role discharged by BASELINE record).**

## 3. G-T3 — `independent_review_receipts` audit (verdict: PASS)

Inside `REC-M5_REVIEW_PATCH_V1_20260811.json` (hash-bound above):

- Array length: exactly **1** entry.
- Sole entry: `refine-logs/REC-M5_EDITORIAL_RECHECK_V2_20260812.md`, model `gpt-5.6-luna`, effort `max`, verdict `BLOCKED_PENDING_EDITORIAL_REVISIONS`, `revisions_applied=true`, `final_recheck=SERVICE_INTERRUPTED`, `current_version_applicability=HISTORICAL_ONLY_PATCH_CHANGED_AFTER_ALL_AUTHOR_INPUT_CONFIRMATIONS`.
- Outstanding lanes with no current-byte receipt registered: scientific-boundary review and governance-manifest review (and a fresh editorial-traceability recheck); `delegated_review` marks all three `CURRENT_ALL_AUTHOR_INPUT_BOUND_VERSION_RECHECK_REQUIRED`. No entry in the receipts array claims to cover them on current bytes.
- Consistent corroboration in-record: baseline `semantic_review_gate.status=PENDING_CURRENT_HASH_REVIEW`; author-input acceptance gate `terra_max_semantic_recheck=REQUIRED`.

Confirmed: one historical-only receipt only; no current-byte receipt for either outstanding lane. **G-T3 = PASS.**

## 4. G-T4 — Independent anchor recomputation (verdict: PASS)

Algorithm extracted from `pre_apply_anchor_checks.algorithm`: SHA-256 over UTF-8 paragraph fragments after CRLF normalization and trimEnd; paragraph numbering follows blank-line splitting; `fail_closed_on_drift=true`. Recomputed by this agent's own Python code against current file bytes (CRLF→LF, split on blank lines, fragment `.rstrip()`, UTF-8 SHA-256). 20 paragraph segments across 10 group anchor records:

| Group | Target | Paragraph | Recorded SHA-256 | Recomputed | Match |
| --- | --- | --- | --- | --- | --- |
| G01 | methods_estimator.md | 3 | `6ea69844ccd957cb53ae04a8ee91715a1b2ef2d6d1da2e0b705f9a075bc7853d` | same | OK |
| G02 | methods_estimator.md | 5 | `00fc2f0136720fd021658ebf5baa46459c65d0cbe2e7c5f2593564d7cfe0c71d` | same | OK |
| G03 | methods_estimator.md | 4 | `6119a2fae8cf48d4aeb30c0e440cead32b0da9b902f200c62c7d0e38651f0933` | same | OK |
| G04 | results_validation.md | 1 | `444a38bcf59dde43cc425bd6e8ea1bceb8818c5009584f3e646326660d264468` | same | OK |
| G04 | results_validation.md | 2 | `2722adfe458c759aa449c707e65ab20f3f9ee286fb2c5a8be61f103383141d6b` | same | OK |
| G04 | results_validation.md | 3 | `db8937fac634420ef220ac231d68529e877ae0de4fde2d2b7000ee1ed960a265` | same | OK |
| G04 | results_validation.md | 4 | `c0ffcc7c0fbb5d8f4923238556ef11e6e4adcd70fd0d7946a97fbeb03b70ebdb` | same | OK |
| G05 | supp_note4_benchmarks.md | 1 | `ccf0b74830e983794fc55a841091bc53643abd0eae7a6505e93225483f99268a` | same | OK |
| G05 | supp_note4_benchmarks.md | 2 | `9f4678c98470b14780da63c17cabd16a1da0602856be41261c4068e4fe76a778` | same | OK |
| G05 | supp_note4_benchmarks.md | 4 | `a85b0cb6f9a8084f2dac2c3dce3fb982f7985fe1493aea2bca51d423c2c7afff` | same | OK |
| G05 | supp_note4_benchmarks.md | 5 | `5a56b9311724a97da964edbb18c90fbc76d61751c38253115d99242e222c2526` | same | OK |
| G05 | supp_note4_benchmarks.md | 6 | `f99c544b7ab4505ac74495ee075755b120fb2a8e3389e1d72748ec63238118d8` | same | OK |
| G05 | supp_note4_benchmarks.md | 8 | `b70faebee53dd4532953fb18984ef96b0a3d63b67d56437532fe12db05bb851e` | same | OK |
| G05 | supp_note4_benchmarks.md | 9 | `0ada4ae5361dc9649fa9ebdf4e8e85f7f779ba3794f1971d51c11c1cf61c9567` | same | OK |
| G05 | supp_note4_benchmarks.md | 10 | `348e6b96f5842bf719fae734a4d9e9dde5d45d5cf0ce7d7af9036823361eabde` | same | OK |
| G06 | methods_estimator.md | 2 | `3c924d1da145ab5e840a4892df3853390db6eeb21c1a23751496524ec01f58ef` | same | OK |
| G07 | methods_data.md | 5 | `352d74189d598706ce2034e27fc16525ebf814ea2b2fe1e7cb7cec65b99d8c0c` | same | OK |
| G08 | methods_uncertainty.md | 2 | `36ae766e672c84154389c3f5bfdf9f32c9146b589198c43c33e786f6e0dddda1` | same | OK |
| G09 | supp_note7_repro.md | 4 | `5d5ebb7a8ed67aa34eda6619189baace8faaa3303dbe5a89e3e2a74adbc8770e` | same | OK |
| G10 | supp_note8_scope.md | 8 | `2f42751ca0ef001d91c0cd8f05079dffc1137340bc4d6e47e89ec42052abbb1a` | same | OK |

**20/20 segment hashes match; no drift; fail-closed condition not triggered.** Robustness note: three algorithm variants were tested (blank-line split incl./excl. whitespace-only separators; whole-fragment vs per-line trimEnd) — all yield identical 20/20 because no anchored fragment contains internal trailing whitespace or whitespace-only lines.

Non-binding annotation finding: recorded `line_range` end-lines exceed my content-only computed end-line by 1 for 5 segments (G02 p5 "9-10" vs computed 9-9; G04 p4 "7-8" vs 7-7; G05 p10 "28-29" vs 28-28; G09 p4 "7-8" vs 7-7; G10 p8 "20-21" vs 20-20) — consistent with the recorder counting the trailing blank separator line into the range. The binding values (hashes) match 20/20 and each target's whole-file SHA-256 equals its protected_baseline binding, so this is annotation convention, not byte drift.

**G-T4 = PASS.**

## 5. G-T5 — protected_baseline fail-closed verification (verdict: PASS)

All 12 entries measured now (P0 closed; nothing defaulted to NOT_VERIFIABLE):

| Path | Bound SHA-256 | Measured SHA-256 | Bytes | Result |
| --- | --- | --- | --- | --- |
| `manuscript_src/natcs/methods_estimator.md` | `8f4cb0f7…508cb25d` | `8f4cb0f7efdb1438fcfad1fe1a3441ed80877093077fe7c7b9f8ec56508cb25d` | 2698 | MATCH |
| `manuscript_src/natcs/results_validation.md` | `746567db…d8278bb3` | `746567db7d4087c2335c65768e35a1a9e8b275791095c896afefd632d8278bb3` | 2749 | MATCH |
| `manuscript_src/natcs/supp_note4_benchmarks.md` | `0bec42db…6a181939e` | `0bec42db15fd153c7480f42a68280111bef986e04496e72c35612af6a181939e` | 4019 | MATCH |
| `manuscript_src/natcs/methods_data.md` | `26e0a984…01cf7a2d` | `26e0a984ac5af6676466fba2f403882a1fc841832c221b83b06e8c0d01cf7a2d` | 2260 | MATCH |
| `manuscript_src/natcs/methods_uncertainty.md` | `2faf3783…e00f1601` | `2faf37836b9b274c9f2bd2cede54cbea9ce5c27a32bdc951ae7b1ee5e00f1601` | 2203 | MATCH |
| `manuscript_src/natcs/supp_note7_repro.md` | `c33c6337…f6337230` | `c33c63370a55ae4afe7abb2e1fb4deef47988585b411d03fa5f54809f6337230` | 1731 | MATCH |
| `manuscript_src/natcs/supp_note8_scope.md` | `1f8a02a8…1b9933d8fa` | `1f8a02a810b372a479bc9e3f877613c2dd670bea4b1d9deffdec681b9933d8fa` | 3531 | MATCH |
| `manuscript_src/natcs/controlled_benchmark_contract.json` | `95199a3c…8d7934ba` | `95199a3c16e6f55a2cf94f7f67289a658bcac7ccb4e17ceee9efa5cc8d7934ba` | 7765 | MATCH |
| `output/ncs_review_corpus/v1_author_decision_register.json` | `c970d829…b901fb2` | **`c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2`** | 110685 | MATCH |
| `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.json` | `60523c09…38d77c68` | `60523c09126fca78f9e87c1ef4776a74b6f5025bbed19ad65ec1755838d77c68` | 1736 | MATCH |
| `refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json` | `5cf086c4…7b276f9046` | `5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046` | 2281 | MATCH |
| `refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json` | `73c135ed…dba694e6` | `73c135edef24e8b4310297070d127d4be6f12d857e009fe178d62e30dba694e6` | 1822 | MATCH |

CHANGED-PREMISE item verified on real measurement, as instructed: `output/ncs_review_corpus/v1_author_decision_register.json` is materialized (110,685 bytes), parses as valid JSON (`schema_version=ncs-author-decision-register-v1`, `generated_at=2026-08-04`, purpose: deduplicated register of the 45 residual reviewer worries), and its measured SHA-256 equals the bound value `c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2`. Binding chain stated explicitly: the bound value lives in `REC-M5_REVIEW_PATCH_V1_20260811.json#/protected_baseline/files`, whose own bytes are bound by `REC-M5_GOVERNANCE_BASELINE_V10_20260812.json#/current_artifacts.review_patch_json`, which is the governance-baseline record adjudicated under G-T2. **12/12 MATCH. G-T5 = PASS.**

## 6. G-T6 — No candidate mutation (verdict: PASS, scope-limited as declared)

Application-state evidence from the patch manifest itself (hash-bound current bytes):

- `output.applied=false`; `output.submission_ready=false`.
- All 10 `edit_groups` carry `disposition=CANDIDATE_NOT_APPLIED` (verified exhaustively).
- `unit_coverage` = 26 units, all unique (recounted independently: 26/26 unique).
- Placeholder scan re-run by this agent: 0 `\{\{…\}\}` tokens in the patch markdown (expected_draft_count=0 satisfied; application_rule premise holds).
- Checklist application items ("Run exact-anchor hash checks before applying", "Obtain separate explicit authorization", post-application rebuild/rerun items) remain unchecked in the patch markdown.

Byte-level comparison relative to frozen bindings actually verified:

- Compared instrument A — protected_baseline bindings (§5): all 8 `manuscript_src/natcs` targets (7 .md + controlled_benchmark_contract.json) plus the decision register plus the 3 audit/authorization files measure EQUAL to their 2026-08-11/12 bound values → unchanged since the frozen bindings.
- Compared instrument B — pre_apply_anchor_checks (§4): 20/20 anchored fragments of the same 7 manuscript sources equal generation-time values → unchanged since the frozen anchors.
- `main.tex` / `supplementary.tex`: NO frozen byte binding exists in any opened authoritative record → **NOT_VERIFIABLE by byte-binding.** Auxiliary git fact (not a substitute): both paths are untracked in git (`git ls-files` count 0), so they fall outside the tracked-drift accounting entirely. Their mutation remains PROHIBITED by the authorization boundary; no receipt claims otherwise.
- Formal register: no formal-register path or hash is bound in the opened authoritative records → **NOT_VERIFIABLE by byte-binding.** Nearest bound register artifact is `v1_author_decision_register.json`, verified equal under G-T5; formal-register adjudication itself is deferred to a separate M5-F authorization per the records.

Adjudication of the 76-file drift for candidate-application status specifically: `git status --porcelain -uno` = 76 changed tracked entries (74 modified `M`, 2 deleted `D` — `tests/test_main_fig2_scope.mjs`, `tests/test_main_fig3_caption_scope.mjs`). Repo-wide "unchanged vs HEAD" does NOT hold. Notably, the 7 anchor-target manuscript sources appear IN the modified-vs-HEAD list while simultaneously measuring byte-equal to the 2026-08-11/12 frozen bindings — proving HEAD does not contain the governed current bytes and that the working tree, not HEAD, is the governed generation. Candidate-application status therefore rests on the record-bound instruments above (both clean), on the patch's own application-state fields (all false/not-applied), and on the absence of any application authorization — not on git HEAD comparison. **No candidate is applied; G-T6 = PASS within declared verification scope.**

## 7. G-T7 — Gate items not verifiable / measurable-false in this environment

- `tracked/clean`: NOW MEASURABLE and **FALSE** — 76 changed tracked entries vs HEAD e7ce60c (74 `M` + 2 `D`). Implication visible to me: any EMPIRICAL_IMPLEMENTATION_AUDIT-class gate item whose semantics assert a clean tracked working tree evaluates FAIL as of 2026-08-26; it must not be carried as PASS. This receipt does not upgrade it.
- `247/247` (m4 allowlist validator): **NOT_VERIFIABLE** — suite not run here (forbidden pre-M5-D). The patch's own `verification.m4_allowlist_validator_before/after="247/247 PASS"` remains a historical generation-time claim, not re-measured.
- `85/85`: **NOT_VERIFIABLE** — suite not run here.
- `145/145`: **NOT_VERIFIABLE** — suite not run here.
- Nothing was upgraded to PASS without measurement.

## 8. G-T8 — Consumed byte generation declaration

Consumed generation = the six canonical current-byte records of §1 (measured values listed there), plus the verification subjects of §5/§6 measured from the same working tree. Conflict-copy declaration: iCloud-style `' 2.` siblings EXIST for four of the six inputs —

- `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811 2.md` (exists, NOT consumed)
- `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811 2.json` (exists, NOT consumed)
- `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812 2.md` (exists, NOT consumed)
- `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812 2.json` (exists, NOT consumed)

No path consumed by this review resolved to a conflict copy: all six inputs were opened at exact canonical paths and hash-matched the expected values, so no BLOCKED arises under G-T8. The conflict copies were existence-probed only, never opened, never hashed, never treated as inputs. **G-T8 = PASS (with mandatory disclosure above).**

## 9. Verdict summary

| Task | Verdict |
| --- | --- |
| G-T1 authoritative input hashes | PASS |
| G-T2 V10 path-name resolution / baseline role | PASS |
| G-T3 independent_review_receipts audit | PASS |
| G-T4 anchor recomputation (10 records / 20 segments) | PASS |
| G-T5 protected_baseline fail-closed (12 entries) | PASS |
| G-T6 no candidate mutation (declared scope) | PASS |
| G-T7 non-verifiable / measurable-false gate reporting | PASS (reported; `tracked/clean`=FAIL measurable; suites NOT_VERIFIABLE) |
| G-T8 consumed-generation & conflict-copy declaration | PASS |

## OVERALL VERDICT: PASS

Scope: Lane B governance-manifest recheck of the current byte generation. Every measurable check passed on real measurement; no deviation, no drift, no applied candidate, no conflict-copy consumption.

Explicit constraints carried forward (do not silently drop):

1. `tracked/clean` = FALSE (76 changed tracked entries) — measurable FAIL for any audit item asserting tree cleanliness; outside this lane's pass criteria but unresolved.
2. Test-count gates 247/247, 85/85, 145/145 remain NOT_VERIFIABLE until suites run post-M5-D.
3. `main.tex`, `supplementary.tex`, and the formal register have no frozen byte bindings in opened records — NOT_VERIFIABLE by binding; prohibitions still stand.
4. Scientific-boundary lane and fresh editorial-traceability recheck remain outstanding with no current-byte receipts; this receipt discharges only the governance-manifest lane.
5. M5-D manuscript-mutation authorization and M5-F formal-register authorization remain REQUIRED_SEPARATELY; nothing herein grants them.

## Not-done statements

- No existing file was modified, moved, or deleted; the only writes are this receipt pair (`REC-M5_GOVERNANCE_RECHECK_V5_20260823.md` / `.json`), both newly created.
- No make target, test suite, build script, or scientific entry point was executed.
- No git write operation (add/commit/push/reset/revert/stash) was performed; only `rev-parse`, `status --porcelain -uno`, and `ls-files` were used.
- The V10 baseline and all historical receipts were left untouched.
- No authorization is issued: manuscript mutation, formal-register mutation, scientific execution, claim activation, and M5-D/M5-F gates all remain NOT_AUTHORIZED / REQUIRED_SEPARATELY.
- No claim is activated by this receipt; it is a review-only, record-only governance artifact.
