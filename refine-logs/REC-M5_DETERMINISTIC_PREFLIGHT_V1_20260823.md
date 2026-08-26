# REC-M5 Deterministic Preflight V1

Generated: 2026-08-23

Audit timezone basis: `Asia/Shanghai`

Result: `PREFLIGHT_PASS_INDEPENDENT_SEMANTIC_REVIEW_STILL_REQUIRED`

Record class: deterministic read-only preflight. The machine-readable companion is `REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823.json`, SHA-256 `dfc8ac5ece1dd3a2387b511355b10528eab3a84b4987374eb6368d15bcb2a0c3`.

## What this record is not

This record recomputes hash and structural facts on current bytes. It is produced by the same party that synthesized `REC-M5_REVIEW_PATCH_V1_20260811`, so it cannot discharge the M5-C independent-review requirement for any lane. It is not an independent review receipt, not a governance `PASS`, and it authorizes no manuscript mutation, no claim activation and no register change. Every `PASS` below is mechanical: it states that recomputed bytes agree with recorded bytes, nothing about semantic adequacy.

## Naming deviation from the plan

The follow-up plan tentatively named this record `REC-M5_GOVERNANCE_RECHECK_V11_20260823`. It is filed instead as `REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823`. The `BASELINE` versus `RECHECK` name collision is the root cause of the `TERRA_V4` `BLOCKED` verdict, and reusing `GOVERNANCE_RECHECK` for a record that is explicitly not a receipt would extend exactly that ambiguity.

## C1 Frozen input hashes

Six inputs, six `PASS`. Measured values agree with `REC-M5_GOVERNANCE_BASELINE_V10_20260812` item by item.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `REC-M5_REVIEW_PATCH_V1_20260811.md` | 27202 | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` |
| `REC-M5_REVIEW_PATCH_V1_20260811.json` | 28217 | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | 10097 | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | 15091 | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` |
| `REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | 1467 | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` |
| `REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | 2987 | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` |

The V10 JSON hash is self-referential and is reported as measured rather than as cross-recorded, since a record cannot contain its own hash.

## C2 Protected baseline

Twelve entries: 11 `PASS`, 0 `MISMATCH`, 1 `NOT_VERIFIABLE_DATALESS` (`output/ncs_review_corpus/v1_author_decision_register.json`). The single failure is the same P0 availability failure recorded in `REC-P0_WORKING_COPY_INTEGRITY_V1_20260823`, not a content divergence. All eight `manuscript_src/natcs` sources and `controlled_benchmark_contract.json` reproduce their recorded hashes exactly.

## C3 Pre-apply anchors

Algorithm as recorded: SHA-256 of UTF-8 paragraph fragments after CRLF normalization and `trimEnd`, with paragraph numbering following blank-line splitting. `fail_closed_on_drift` is `true`.

| Group | Target | Segments | Verdict |
| --- | --- | ---: | --- |
| G01 | `methods_estimator.md` | 1/1 | `PASS` |
| G02 | `methods_estimator.md` | 1/1 | `PASS` |
| G03 | `methods_estimator.md` | 1/1 | `PASS` |
| G04 | `results_validation.md` | 4/4 | `PASS` |
| G05 | `supp_note4_benchmarks.md` | 8/8 | `PASS` |
| G06 | `methods_estimator.md` | 1/1 | `PASS` |
| G07 | `methods_data.md` | 1/1 | `PASS` |
| G08 | `methods_uncertainty.md` | 1/1 | `PASS` |
| G09 | `supp_note7_repro.md` | 1/1 | `PASS` |
| G10 | `supp_note8_scope.md` | 1/1 | `PASS` |

Groups 10/10 `PASS`; paragraph segments 20/20 `PASS`. This upgrades the patch JSON's recorded `PASS_10_OF_10_GROUP_ANCHOR_RECORDS` from an assertion to an independently recomputed fact, and establishes that no manuscript drift has occurred since 2026-08-11. The 26-unit patch remains applicable to current bytes.

Issuance note on this table. The target column above was initially transcribed by hand and carried three wrong filenames for G07, G09 and G10. A pre-issuance self-check against the JSON companion, which derives every target programmatically from `pre_apply_anchor_checks`, caught and corrected all three before this record was cited anywhere. No verdict changed, since verdicts were computed from the JSON path values, not from the transcription. Where this record and its JSON companion disagree, the JSON governs.

## C4 Unit coverage

26 entries, 26 unique `(source_item, unit_id)` pairs, 0 duplicates. Distribution: V1-026 three units, V1-033 thirteen units, V1-045 ten units. All candidates remain unapplied.

## C5 Process-text residue, the TERRA-V3-E1 locus

The original finding was an unmarked `AIN-RESULT binding` process note interleaved between G04 `Proposed paragraph 1` and `Proposed paragraph 2`, at risk of being written into `results_validation.md` by a paragraph-level tool.

On current bytes the G04 block spans lines 82 to 101 and contains one `Target:` line followed by four `Proposed paragraph` labels, each followed only by a blockquote. Interleaved prose between proposed paragraphs is zero, in G04 and in every other group. Placeholder tokens are zero. The characteristic strings `AIN-RESULT binding`, `partial M5-A response`, `remaining author inputs` and `AUTHOR_INPUT_NEEDED` all return zero matches.

The statement did not vanish; it was relocated. The G04 AIN-RESULT sentence now sits at line 283 under `## Missing information and risk flags` (line 277), a record-level status section rather than a manuscript-target section, and line 284 independently labels the G04 traceability content as `Manifest-only`. Four explicit `manifest-only` labels exist, at lines 127, 231, 241 and 242.

One disambiguation matters for the editorial lane: `Target:` and `Boundary:` lines are uniform record scaffolding, present across groups and always positioned before the proposed-paragraph run, never inside it. A naive residue scan flags them; they are not `TERRA-V3-E1` class.

This check establishes structural remediation only. Whether the relocated wording is editorially adequate is a semantic judgment reserved to the editorial lane.

## C6 Governance input path resolution

| Path | Role | Exists |
| --- | --- | --- |
| `refine-logs/REC-M5_GOVERNANCE_RECHECK_V10_20260812.md` | cited by `TERRA_V4` | no |
| `refine-logs/REC-M5_GOVERNANCE_RECHECK_V10_20260812.json` | cited by `TERRA_V4` | no |
| `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | actual on disk | yes |
| `refine-logs/REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | actual on disk | yes |

`TERRA_V4` attempted to verify records that do not exist under any materialization state. Its `BLOCKED` is a path-naming failure, not a substantive governance finding.

The required control is to carry exact paths plus expected SHA-256 in the dispatch and to require the reviewer to report measured hashes. The V10 baseline must not be edited to fix its own notation: its hashes `dfd4385f…` and `94668a91…` are bound inside the `SCIENTIFIC_RECHECK_TERRA_V5` `PASS` receipt, so rewriting it would invalidate the only current-byte `PASS` the project holds.

## M5-C closure state

| Lane | Latest receipt | Verdict | Valid on current bytes |
| --- | --- | --- | --- |
| Scientific boundary | `REC-M5_SCIENTIFIC_RECHECK_TERRA_V5_20260812` | `PASS` | yes |
| Editorial traceability | `REC-M5_EDITORIAL_RECHECK_TERRA_V3_20260812` | `BLOCKED` | no, reviewed superseded bytes |
| Governance manifest | `REC-M5_GOVERNANCE_RECHECK_TERRA_V4_20260812` | `BLOCKED` | no, unresolved input paths |

Two independent receipts on current bytes remain outstanding. M5-D may be requested only after both return `PASS`.

## Carried-forward blocking constraints

`P0-C1` do not delete `manuscript_src/natcs/discussion 2.md`. `P0-C2` do not delete `refine-logs` `' 2.'` copies of hash-frozen `REC` records. `P0-C3` do not treat `ORPHAN_NO_BASE` copies as redundant. `P0-C4` no `make` target, test suite or scientific entry before materialization completes. `P0-C5` report `tracked/clean`, `247/247`, `85/85` and `145/145` as `NOT_VERIFIABLE` until git resolves.

## Changed paths

- `refine-logs/REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823.md`
- `refine-logs/REC-M5_DETERMINISTIC_PREFLIGHT_V1_20260823.json`

No other file was created, modified or deleted. `manuscript_src`, the formal register, all pre-existing frozen records, authorization files and generated TeX are untouched. No git operation, `make` target, test suite or scientific entry was executed. Scientific execution and claim activation remain `NOT_AUTHORIZED`.
