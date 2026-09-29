# REC-M5 Governance Recheck V6 (Governance-Manifest Lane, V2 Patch Generation)

- record_class: `governance_recheck_receipt`
- generated: 2026-08-26 (Asia/Shanghai)
- lane: governance-manifest, independent read-only reviewer
- patch generation under review: `REC-M5_REVIEW_PATCH_V2_20260826` (V2, editorial E-T3 remediation; author-authorized 2026-08-26)
- prior governance receipt on V1 bytes: `REC-M5_GOVERNANCE_RECHECK_V5_20260823.{md,json}` (PASSED; 20/20 anchors, 12/12 protected_baseline, receipts field = 1 historical entry) — context, not re-measured here as evidence
- reviewer scope: exactly two new files written (this pair); all other operations read-only; no make/test/scientific execution; no subagents

## OVERALL VERDICT: PASS

All eight tasks PASS on current measurement. Two advisory observations are recorded verbatim below (anchor `line_range` end-line convention; legacy V1-bound schema pointers retained under the explicit `v2_revision.supersedes_bytes` declaration). Neither is drift and neither weakens any binding. Nothing was upgraded to PASS without measurement.

## G-T1 — Authoritative input hashes: PASS

Measured with `shasum -a 256` by this reviewer. All six match expected values exactly.

| # | File | Measured SHA-256 | Expected | Verdict | Size |
| --- | --- | --- | --- | --- | --- |
| 1 | refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md | 8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0 | 8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0 | MATCH | 29083 B |
| 2 | refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json | 5e1697d22ac847825e37c4090ee2e28af0385c3015ecc1d8a048bb3cbda5f2ce | 5e1697d22ac847825e37c4090ee2e28af0385c3015ecc1d8a048bb3cbda5f2ce | MATCH | 31204 B |
| 3 | refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md | 1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341 | 1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341 | MATCH | 10097 B |
| 4 | refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json | ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6 | ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6 | MATCH | 15091 B |
| 5 | refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.md | dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539 | dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539 | MATCH | 1467 B |
| 6 | refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.json | 94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee | 94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee | MATCH | 2987 B |

Result: 6/6 MATCH. No deviation.

## G-T2 — RECHECK_V10 absence / role discharge / V10 untouched: PASS

- Disk: no `REC-M5_GOVERNANCE_RECHECK_V10_20260812.{md,json}` under `refine-logs/` (verified by listing and tree-wide find; GOVERNANCE_RECHECK family present only as TERRA V1/V3/V4 and V2–V9 dated 20260812 plus V5 dated 20260823).
- Git: `git ls-files` contains no RECHECK_V10 path.
- Role discharge: `REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}` (both opened) declare result `CURRENT_HASH_CHAIN_READY_FOR_TERRA_MAX_DIRECT_REVIEW`, `contradictions_reviewed=true`, review route `gpt-5.6-terra`/`max` with required roles including governance-manifest — the baseline discharges the role a RECHECK_V10 record would have held.
- V10 untouched: measured hashes of both V10 files equal the authoritative expected values in G-T1 (rows 5–6). Hash equality is the non-mutation evidence.

## G-T3 — independent_review_receipts audit + v2_revision metadata: PASS

Exact contents of `independent_review_receipts` inside REC-M5_REVIEW_PATCH_V2_20260826.json — count = **1**:

```json
[{
  "path": "refine-logs/REC-M5_EDITORIAL_RECHECK_V2_20260812.md",
  "sha256": "332bedf26d1d06387d9a6a00dc1e5d9f0eea5f7ef02a454b6748a67b9760212d",
  "model": "gpt-5.6-luna",
  "reasoning_effort": "max",
  "verdict": "BLOCKED_PENDING_EDITORIAL_REVISIONS",
  "revisions_applied": true,
  "final_recheck": "SERVICE_INTERRUPTED",
  "current_version_applicability": "HISTORICAL_ONLY_PATCH_CHANGED_AFTER_ALL_AUTHOR_INPUT_CONFIRMATIONS"
}]
```

Matches expectation: inherited single HISTORICAL_ONLY entry; NO current-byte receipt registered for any lane (scientific-boundary, editorial-traceability, or governance-manifest) against the V2 bytes. The JSON's own `verification.semantic_service_note` states no earlier service failure is represented as an adjudication.

`v2_revision` metadata block (verbatim fields): generated `2026-08-26`; timezone_basis `Asia/Shanghai`; authorization "author structured decision et3_remediation=V2 patch re-review, 2026-08-26"; basis_receipt `refine-logs/REC-M5_EDITORIAL_RECHECK_V4_20260823.md` (E-T3 FAIL, F1–F5); revisions_applied F1,F2a,F2b,F3,F4,F5a–F5e,C1,C2a,C2b; semantic_ceiling_changes "none". Declared supersedes hash: path `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md`, sha256 `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` — equals the recorded V1 md value `69888df4…`. Independently corroborated without opening any V1 byte: `GOVERNANCE_BASELINE_V10` records the identical full hash for that file in its current-artifacts table.

## G-T4 — Independent anchor recomputation: PASS

Algorithm as recorded: SHA-256 of UTF-8 paragraph fragments after CRLF normalization and trimEnd; paragraph numbering follows blank-line splitting; `fail_closed_on_drift=true`. Reviewer reimplemented the algorithm independently (own Python segmentation + hashlib) and parsed expected values programmatically from the authoritative JSON (no transcription).

Per-anchor recomputed vs recorded (20 paragraph segments across 10 group anchors):

| Group | Target | Para(s) | Recomputed vs recorded | Result |
| --- | --- | --- | --- | --- |
| G01 | methods_estimator.md | 3 | 6ea69844…7853d = recorded | MATCH |
| G02 | methods_estimator.md | 5 | 00fc2f01…c71d = recorded | MATCH |
| G03 | methods_estimator.md | 4 | 6119a2fa…0933 = recorded | MATCH |
| G06 | methods_estimator.md | 2 | 3c924d1d…58ef = recorded | MATCH |
| G04 | results_validation.md | 1,2,3,4 | 444a38bc…6468, 2722adfe…1d6b, db8937fa…a265, c0ffcc7c…ebdb | 4/4 MATCH |
| G05 | supp_note4_benchmarks.md | 1,2,4,5,6,8,9,10 | ccf0b748…268a, 9f4678c9…a778, a85b0cb6…7afff, 5a56b931…c2526, f99c544b…118d8, b70faebe…b851e, 0ada4ae5…c9567, 348e6b96…eabde | 8/8 MATCH |
| G07 | methods_data.md | 5 | 352d7418…8c0c = recorded | MATCH |
| G08 | methods_uncertainty.md | 2 | 36ae766e…ddda1 = recorded | MATCH |
| G09 | supp_note7_repro.md | 4 | 5d5ebb7a…7770e = recorded | MATCH |
| G10 | supp_note8_scope.md | 8 | 2f42751c…bbb1a = recorded | MATCH |

Full-value table is mirrored machine-readably in the JSON companion (`anchors_recomputed`). Totals: **20/20 segment hashes recomputed equal to the recorded V1-era values; 10/10 group anchors bind current TARGET manuscript bytes.** Anchors therefore confirm zero manuscript-source drift since the frozen bindings.

Advisory observation (metadata only, non-binding): 5 of 20 recorded `line_range` end-lines exceed strict content-line observation by exactly 1 — G02 para 5 ("9-10" vs content 9), G04 para 4 ("7-8" vs 7), G05 para 10 ("28-29" vs 28), G09 para 4 ("7-8" vs 7), G10 para 8 ("20-21" vs 20). Verified cause: each is the final paragraph of its file, and the recorded end bound counts the file's terminal-newline empty element (confirmed by direct line inspection: e.g., methods_estimator.md has 9 real lines ending `…lity.\n`; supp_note4_benchmarks.md 28 real lines). Start-lines agree in all 20 cases; all 20 hashes agree. Classified METADATA_CONVENTION_NOTE — not drift; fail-closed binding is the sha256 field.

## G-T5 — protected_baseline fail-closed measurement: PASS

All 12 entries measured now (exact-path SHA-256, per the manifest's comparison_policy). Every row reported:

| Protected path | Measured SHA-256 | Recorded | Result |
| --- | --- | --- | --- |
| manuscript_src/natcs/methods_estimator.md | 8f4cb0f7efdb1438fcfad1fe1a3441ed80877093077fe7c7b9f8ec56508cb25d | same | MATCH |
| manuscript_src/natcs/results_validation.md | 746567db7d4087c2335c65768e35a1a9e8b275791095c896afefd632d8278bb3 | same | MATCH |
| manuscript_src/natcs/supp_note4_benchmarks.md | 0bec42db15fd153c7480f42a68280111bef986e04496e72c35612af6a181939e | same | MATCH |
| manuscript_src/natcs/methods_data.md | 26e0a984ac5af6676466fba2f403882a1fc841832c221b83b06e8c0d01cf7a2d | same | MATCH |
| manuscript_src/natcs/methods_uncertainty.md | 2faf37836b9b274c9f2bd2cede54cbea9ce5c27a32bdc951ae7b1ee5e00f1601 | same | MATCH |
| manuscript_src/natcs/supp_note7_repro.md | c33c63370a55ae4afe7abb2e1fb4deef47988585b411d03fa5f54809f6337230 | same | MATCH |
| manuscript_src/natcs/supp_note8_scope.md | 1f8a02a810b372a479bc9e3f877613c2dd670bea4b1d9deffdec681b9933d8fa | same | MATCH |
| manuscript_src/natcs/controlled_benchmark_contract.json | 95199a3c16e6f55a2cf94f7f67289a658bcac7ccb4e17ceee9efa5cc8d7934ba | same | MATCH |
| output/ncs_review_corpus/v1_author_decision_register.json | c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2 | same | MATCH |
| refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.json | 60523c09126fca78f9e87c1ef4776a74b6f5025bbed19ad65ec1755838d77c68 | same | MATCH |
| refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json | 5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046 | same | MATCH |
| refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json | 73c135edef24e8b4310297070d127d4be6f12d857e009fe178d62e30dba694e6 | same | MATCH |

**12/12 MATCH**, including `output/ncs_review_corpus/v1_author_decision_register.json`, whose measured value equals the post-P0-closure expected value `c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2`. Zero-mismatch was not substituted for reporting — every row above is individually reported.

## G-T6 — No-mutation verification: PASS

Measured from the V2 JSON and current bytes:

- `output.applied = false`; `output.submission_ready = false`.
- All 10 edit groups (G01–G10) have disposition `CANDIDATE_NOT_APPLIED` (10/10).
- `unit_coverage`: 26 rows; 26 unique unit_id values (also 26 unique (source_item, unit_id) pairs); distribution V1-026: 3, V1-033: 13, V1-045: 10 → 26/26 unique coverage confirmed.
- Placeholder tokens: mechanical regex scan (`\{\{[^}]*\}\}`) of the current V2 payload REC-M5_REVIEW_PATCH_V2_20260826.md → **0 tokens** (matches `expected_draft_count: 0` and the manifest's `PASS_NO_DOUBLE_BRACE_TOKENS` self-report).
- Manuscript targets byte-equal to frozen bindings: established by G-T4 (20/20 anchor hashes over current target bytes) plus G-T5 (12/12 protected_baseline exact-path hashes). No manuscript-source mutation.
- NOT_VERIFIABLE-by-binding: `main.tex` and `supplementary.tex` (generated outputs carry no binding in this manifest) and formal-register adjudication (explicitly deferred to a separate M5-F authorization). Their state cannot be verified by this lane's bindings and no claim about them is made.

Advisory observation (schema-level, disclosed): legacy fields of the V2-generation JSON still point at superseded V1 bytes under the explicit supersession declaration — `record_id` remains `REC-M5-review-patch-v1-20260811`, `generated_at` remains `2026-08-11T23:06:28+08:00`, `output.path`/`output.sha256` and `placeholder_scan.targets` reference `REC-M5_REVIEW_PATCH_V1_20260811.md` (= `69888df4…`, the declared supersedes hash). These pointers are internally consistent with `v2_revision.supersedes_bytes` and do not affect the V1-era frozen manuscript bindings verified in G-T4/G-T5; noted so downstream consumers do not misread `output.path` as the V2 payload location.

## G-T7 — Gate items, current facts: PASS (with NOT_VERIFIABLE items preserved)

- Tracked/clean: MEASURED TRUE now. `git rev-parse HEAD` = `53f63f0fdf632b72d62aa497f6d9e6c9287dc029` (short 53f63f0) on branch `codex/m5-current-luna-science-recheck`; `git status --porcelain -uno` count = 0. (Tree contains untracked files outside tracking — full `git status --porcelain` shows 338 `??` entries — which does not affect tracked-tree cleanliness.)
- Suite counts 247/247 (m4 allowlist validator), 85/85, 145/145: **NOT_VERIFIABLE** — no suite was run by any party within this lane's visibility, suites remain forbidden pre-M5-D, and this reviewer executed none. The `247/247 PASS before/after` strings inside the V2 JSON are historical V1-era self-reports carried through verification metadata, not current measurements.
- Nothing upgraded to PASS without measurement: confirmed for every gate item in this receipt.

## G-T8 — Generation declaration: PASS

Every file opened by this review, with access mode:

| File | Access | SHA-256 |
| --- | --- | --- |
| refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md | content opened + hashed | 8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0 |
| refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json | content opened + hashed | 5e1697d22ac847825e37c4090ee2e28af0385c3015ecc1d8a048bb3cbda5f2ce |
| refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md | hashed (content not consumed) | 1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341 |
| refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json | hashed (content not consumed) | ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6 |
| refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.md | content opened + hashed | dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539 |
| refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.json | content opened + hashed | 94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee |

Additional byte-level reads performed strictly for measurement (no content consumed into evidence): the 12 protected_baseline paths and the anchor-target manuscript paragraphs listed in G-T4/G-T5; directory listings; git queries. Mechanical count-only regex scan of the V2 markdown for placeholder tokens.

Superseded-generation copies: spot-verified absent — no `' 2.'` filenames exist anywhere in `refine-logs/`, and a whole-tree search finds exactly one copy of each of the three input basename families (the six authoritative inputs). None was opened or consumed. This matches the deletion recorded (context-only) in `REC-M5_CONFLICT_DISPOSITION_V1_20260826.json`.

Not touched: `REC-M5_REVIEW_PATCH_V1_20260811.*` were never opened, hashed, or scanned — zero byte-access by this lane (the supersedes-hash check was satisfied against recorded values per G-T3).

## Independence & provenance disclosure

- Producing agent/model: ox-alpha (stealth model via DeepSeek Harness), executing as an independent delegated read-only reviewer; this receipt pair is the sole write product of this session.
- Self-adjudication disclosure: verdicts above were adjudicated by the producing agent itself against pre-stated expected values; no second independent agent cross-checked them within this session.
- Synthesis-party disclosure: the reviewed V2 patch generation (`REC-M5_REVIEW_PATCH_V2_20260826.{md,json}`) was synthesized by the orchestrator party, not by an independent third party; this lane verifies the V2 bytes and their bindings independently, but the producer of the V2 artifact and the coordinator of this review are not independent of each other.
- Environment note: intermittent harness shell-spawn failures occurred during this session (`spawn bash ENOENT`, transient); every affected command was retried successfully and no reported measurement derives from a failed invocation.

## Explicit not-done statements

- Only `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` and `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.json` were written; nothing else was created, modified, or deleted.
- No make, test, build, or scientific execution was run.
- No authorization was issued and none may be inferred from this receipt; `applied=false` and `submission_ready=false` remain operative.
- No claim was activated; all scientific ceilings of the underlying records remain intact.
- No V1-byte access; the V1↔V2 diff remains owned by its designated lane.
- Suites remain NOT_VERIFIABLE and remain forbidden pre-M5-D; main.tex/supplementary.tex state and formal register remain NOT_VERIFIABLE-by-binding (M5-F separate).

## Verdict summary

- Overall: **PASS**
- G-T1 input hashes: **PASS** (6/6 match)
- G-T2 RECHECK_V10 absence/discharge/non-mutation: **PASS**
- G-T3 receipts field + v2_revision/supersedes hash: **PASS** (1 HISTORICAL_ONLY entry; supersedes = `69888df4…`)
- G-T4 anchor recomputation: **PASS** (20/20 segments, 10/10 groups; line-range end-line convention noted, non-binding)
- G-T5 protected_baseline: **PASS** (12/12 measured MATCH incl. v1_author_decision_register.json = `c970d829…`)
- G-T6 no-mutation: **PASS** (flags false; 10/10 CANDIDATE_NOT_APPLIED; 26/26 unique; 0 placeholders; bindings hold; main.tex/supplementary.tex/formal register NOT_VERIFIABLE-by-binding)
- G-T7 gates: **PASS** (tracked-clean measurable and TRUE at 53f63f0; suites 247/247, 85/85, 145/145 NOT_VERIFIABLE)
- G-T8 generation declaration: **PASS** (all opens declared; no superseded copies exist or were consumed)

Notable findings: (1) five recorded anchor line_ranges use a terminal-newline-inclusive end-line convention on final paragraphs — hashes unaffected, classified advisory; (2) V2 JSON retains legacy V1-bound pointers (record_id, generated_at, output.path/sha256, placeholder_scan.targets) beneath the explicit `v2_revision.supersedes_bytes` declaration — advisory; (3) no current-byte independent-review receipt exists yet for any lane on V2 bytes — consistent with expectations; the Terra/max semantic reviews remain outstanding gates.
