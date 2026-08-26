# REC-M5 Recheck Dispatch V1

Generated: 2026-08-23

Audit timezone basis: `Asia/Shanghai`

Status: `AWAITING_REVIEWER_EXECUTION`

Record class: dispatch packet. The machine-readable companion is `REC-M5_RECHECK_DISPATCH_V1_20260823.json`, SHA-256 `54a2c2d03a7dd5611afc910cc46e713d0e01ee3aaece468d7adc117fcb3e0b11`.

A dispatch packet specifies work. It does not perform or substitute for it. This record is not an independent review receipt and does not satisfy M5-C.

## Purpose

M5-C requires three independent review lanes. Only the scientific-boundary lane holds a `PASS` on current bytes. The editorial and governance lanes both returned `BLOCKED`, and in both cases the block traces to which bytes the reviewer actually opened rather than to a defect in the patch. This packet dispatches those two lanes with exact paths and expected hashes so that a third failure of the same kind cannot recur.

## Reviewer requirements

Provenance `gpt-5.6-terra` / `max`, direct self-adjudication.

The reviewer must not treat `REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823` as evidence. That record was produced by the same party that synthesized the patch and is supplied only to localize prior findings.

Fail-closed policy applies without exception. Missing, unreadable or contradictory input yields `BLOCKED` or `FAIL`, never a default `PASS`. A zero failure count is not evidence of coverage. Generated TeX may not be used to reconstruct source ownership.

Byte-generation control is the critical procedural requirement. `refine-logs` currently holds two byte generations of these record names. Open only the exact paths listed below. Never resolve a path by glob or by name approximation. The `' 2.'` conflict copies are the superseded generation, bound by 33 to 39 historical receipts each, and are not interchangeable with current bytes.

Report measured SHA-256 for every file opened, a per-task verdict, and an explicit overall verdict. Do not summarize verdict codes into prose equivalents.

## Authoritative inputs

| Path | Bytes | Expected SHA-256 |
| --- | ---: | --- |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md` | 27202 | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.json` | 28217 | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | 10097 | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | 15091 | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` |
| `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | 1467 | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` |
| `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | 2987 | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` |

Advisory, explicitly non-authoritative: `REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823.md` (`d768bc97…`), its JSON companion (`dfc8ac5e…`), and `REC-P0_WORKING_COPY_INTEGRITY_V1_20260823.md` for availability context.

Prior receipts, for context only: `SCIENTIFIC_RECHECK_TERRA_V5` (`PASS`, valid on current bytes, does not transfer across lanes); `EDITORIAL_RECHECK_TERRA_V3` (`BLOCKED`, read the `TERRA-V3-E1` finding text but note its input hashes `b95a0960…`, `8c0546a7…`, `c7664285…` are superseded bytes); `GOVERNANCE_RECHECK_TERRA_V4` (`BLOCKED`, read the unresolved-path failure but do not reuse its input path spellings).

## Lane A, editorial traceability

Supersedes `REC-M5_EDITORIAL_RECHECK_TERRA_V3_20260812`. Required output: `refine-logs/REC-M5_EDITORIAL_RECHECK_V4_20260823.{md,json}`.

`E-T1` adjudicate `TERRA-V3-E1` closure. The finding was an unmarked `AIN-RESULT binding` process note between G04 `Proposed paragraph 1` and `Proposed paragraph 2`. On current bytes that statement sits at line 283 under `## Missing information and risk flags`. Judge independently whether the G04 proposed-paragraph run is free of process statements, and whether relocating the statement into a record-level status section is an adequate remedy or merely displaces the risk. Do not accept the preflight's structural `PASS` as this lane's finding.

`E-T2` verify 26-unit traceability. Each unit must trace to its `source_item` (V1-026, V1-033, V1-045) and to a G01–G10 group anchor, with no orphan and no duplicate.

`E-T3` apply a reader-facing test to every proposed paragraph. Each must read as journal manuscript prose. Flag any governance vocabulary, record identifier, verdict code, hash or internal process reference that would be inappropriate in published text.

`E-T4` verify the four `manifest-only` labels at lines 127, 231, 241 and 242. Confirm each unambiguously excludes its content from manuscript application, and that no `manifest-only` content is reachable by a paragraph-level applier.

`E-T5` verify no claim ceiling is exceeded. V1-026 stays descriptive with `NOT_RUN`/`BLOCKED`. V1-033 stays simulation-only and `NOT_EVALUABLE`. V1-045 stays limited to N=20 and N=50, with N=100 and N=200 as `NOT_RUN/ABSTAIN` and `resource_telemetry` `BLOCKED/null`. G06 and G07 are `AUTHOR_CONFIRMED_REVIEW_ONLY` and must not read as convergence, global optimum or general topology robustness.

`E-T6` verify author-input traceability. Every AIN-derived value must trace to the author-input record, including the four percentages, the ratio-of-medians formula, its denominator, and evidence hash `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`. The application/bootstrap 100/80, spectral-radius and 50% top-exposure attenuation sources are author-confirmed Unavailable and must not be reconstructed from generated TeX.

`E-T7` report which byte generation was consumed. State the measured SHA-256 of every file opened. If any path resolved to a `' 2.'` conflict copy, declare it and return `BLOCKED`.

## Lane B, governance manifest

Supersedes `REC-M5_GOVERNANCE_RECHECK_TERRA_V4_20260812`. Required output: `refine-logs/REC-M5_GOVERNANCE_RECHECK_V5_20260823.{md,json}`.

`G-T1` measure and compare all six authoritative input hashes. Report actual measured values. Any deviation is `BLOCKED`, not a warning.

`G-T2` resolve the path-name question that blocked `TERRA_V4`. `REC-M5_GOVERNANCE_RECHECK_V10_20260812.{md,json}` do not exist; the actual records are `REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}`. Confirm both facts independently and adjudicate whether the `BASELINE` record discharges the governance-baseline role. Do not request or perform any edit to the V10 baseline: its hashes `dfd4385f…` and `94668a91…` are bound inside the `SCIENTIFIC_RECHECK_TERRA_V5` `PASS` receipt, so rewriting it would invalidate the only current-byte `PASS` the project holds.

`G-T3` audit the `independent_review_receipts` field. Confirm it holds exactly one entry, `REC-M5_EDITORIAL_RECHECK_V2_20260812`, self-marked `HISTORICAL_ONLY_PATCH_CHANGED_AFTER_ALL_AUTHOR_INPUT_CONFIRMATIONS`, and that no current-byte receipt is yet registered for either outstanding lane.

`G-T4` independently recompute the 10 group anchor records using the recorded algorithm: SHA-256 of UTF-8 paragraph fragments after CRLF normalization and `trimEnd`, paragraph numbering by blank-line splitting. Twenty paragraph segments total. `fail_closed_on_drift` is `true`.

`G-T5` verify `protected_baseline` fail-closed. Twelve entries. `output/ncs_review_corpus/v1_author_decision_register.json` is non-materialized and unreadable; it must be reported `NOT_VERIFIABLE` and must not be scored `PASS`. A zero-mismatch count does not supply the missing row.

`G-T6` confirm no mutation has occurred. All 26 candidates unapplied; `manuscript_src`, formal register and generated TeX unchanged; no authorization issued or implied.

`G-T7` report gate items that are not verifiable in this environment. `tracked/clean`, `247/247`, `85/85` and `145/145` must be reported `NOT_VERIFIABLE` while git is unresolvable, since `git rev-parse HEAD` fails and `git fsck` dumps core.

`G-T8` report which byte generation was consumed, same requirement as `E-T7`.

## Closure condition

Both lanes must `PASS` on the six authoritative hashes. Then, in order: write the M5-C closure record; register the three current-byte receipts, meaning `SCIENTIFIC_RECHECK_TERRA_V5` plus the two new ones, into the patch JSON `independent_review_receipts` field; request M5-D manuscript mutation authorization from the author.

Registering receipts changes the patch JSON bytes and therefore invalidates hash `938e5218…`. That step is itself part of M5-C closure and must be sequenced after both lanes report, never before.

Before M5-D is granted, the following remain forbidden: editing `manuscript_src/natcs/*.md`, editing `controlled_benchmark_contract.json`, editing the formal register, editing or regenerating `main.tex` or `supplementary.tex`, running any `make` target, and activating any claim. Formal register changes require a separate M5-F authorization even after M5-D.

## Interaction with P0

Neither lane is blocked by P0. Both read only materialized `refine-logs` and `manuscript_src` bytes, so they can run in parallel with host-side materialization. Only `G-T5` and `G-T7` are affected, and both are handled by reporting `NOT_VERIFIABLE` rather than by waiting. `P0-C4` still forbids any `make` target, test suite or scientific entry until materialization completes.

## Changed paths

- `refine-logs/REC-M5_RECHECK_DISPATCH_V1_20260823.md`
- `refine-logs/REC-M5_RECHECK_DISPATCH_V1_20260823.json`

No other file was created, modified or deleted. `manuscript_src`, the formal register, all pre-existing frozen records, authorization files and generated TeX are untouched. No git operation, `make` target, test suite or scientific entry was executed. Scientific execution and claim activation remain `NOT_AUTHORIZED`.
