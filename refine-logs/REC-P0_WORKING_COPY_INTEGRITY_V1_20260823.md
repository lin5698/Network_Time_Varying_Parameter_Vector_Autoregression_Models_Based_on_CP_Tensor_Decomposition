# REC-P0 Working Copy Integrity V1

Generated: 2026-08-23

Audit timezone basis: `Asia/Shanghai`

Result: `BLOCKED_NON_MATERIALIZED_WORKING_COPY`

Record class: deterministic read-only triage. This record is file-identity triage only. It is not an independent semantic review receipt, not a governance `PASS`, and it does not authorize any deletion, manuscript mutation, scientific execution or claim activation. The machine-readable companion is `REC-P0_WORKING_COPY_INTEGRITY_V1_20260823.json`.

## Root cause

The working copy sits in an iCloud-synced path. A large fraction of files are non-materialized placeholders with `st_size>0` and `st_blocks=0`; reads fail at the mount boundary. The failure mode is availability only. No content corruption was found. Materialization can only be performed on the host macOS side; it cannot be triggered from the analysis environment.

## Non-materialized scope

8095 files are non-materialized. Distribution by top-level entry: `archive` 4200, `output` 1888, `.git` 1146, `data` 518, `scripts` 205, `.aris` 81, `tests` 32, `.playwright-mcp` 14, `.pytest_cache` 5, plus top-level `main.tex`, `supplementary.tex`, `monte_carlo_cp_network_tvp_var_results.csv`, and one file each under `refine-logs` and `manuscript_src`.

Git is unusable. `.git` has 1146 of 1153 files non-materialized. `HEAD` points to `refs/heads/codex/m5-current-luna-science-recheck`; `git rev-parse HEAD` fails with unknown revision and `git fsck` dumps core.

Individually notable unreadable paths: `main.tex`, `supplementary.tex`, `monte_carlo_cp_network_tvp_var_results.csv`, `manuscript_src/natcs/_archives/superseded_text_before_20260618_2140/abstract_2.md`, `refine-logs/e3_family2_runtime/e4-r3.stdout.log`, `output/ncs_review_corpus/v1_author_decision_register.json`.

## Sync-conflict inventory

365 `* 2.<ext>` pairs were examined, excluding `.git`, `.playwright-mcp`, `__pycache__` and `.pytest_cache`.

| Verdict | Count | Meaning |
| --- | ---: | --- |
| `BYTE_IDENTICAL` | 336 | Copy and base hash identically |
| `CONTENT_DIVERGENT` | 6 | Copy and base differ in content |
| `NOT_VERIFIABLE_DATALESS` | 12 | At least one side is non-materialized |
| `ORPHAN_NO_BASE` | 11 | Copy exists with no surviving base counterpart |

Distribution by top-level entry: `refine-logs` 186, `scripts` 95, `paper_rewriting_output` 31, `tests` 29, `output` 16, `archive` 6, `docs` 1, `manuscript_src` 1.

The six divergent pairs are `manuscript_src/natcs/discussion 2.md`, the four `REC-M5` frozen-input copies, and `scripts/build_natcs_framework_figure 2.py`.

No copy may be deleted on the basis of this record. `BYTE_IDENTICAL` is necessary but not sufficient; see the blocking constraints.

## Stale-generation hazard

`refine-logs` currently holds two byte generations of the same hash-frozen record names, and the `' 2.'` copies are the superseded generation that most historical receipts bind to.

| Record name | Current SHA-256 | Conflict-copy SHA-256 | Receipts citing current | Receipts citing copy |
| --- | --- | --- | ---: | ---: |
| `REC-M5_REVIEW_PATCH_V1_20260811.md` | `69888df4…e580bd` | `336c3cc4…38c07d` | 6 | 39 |
| `REC-M5_REVIEW_PATCH_V1_20260811.json` | `938e5218…01e0e6` | `8d9b1d2a…` | 5 | 38 |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `1555484a…04b9341` | `d622854a…dde571cd` | 13 | 37 |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `ebb639ed…3b12d8b6` | `83197e88…` | 4 | 33 |

Any glob-based or name-approximate reader can silently bind the superseded generation. This is a plausible contributing cause of reviewer receipts reporting input hashes that match no current file, which is exactly the pattern seen in `REC-M5_EDITORIAL_RECHECK_TERRA_V3_20260812` and `REC-M5_GOVERNANCE_RECHECK_TERRA_V4_20260812`. The required control is to dispatch every recheck with explicit exact paths plus expected SHA-256, and to require the reviewer to report actual measured hashes.

## Deterministic recheck of REC-M4 preconditions

Expectations were taken from `refine-logs/REC-M3_ACCEPTANCE_V2_20260811.json`. The tree digest in `scripts/validate_rec_m4_v4.mjs` was reimplemented independently in Python: walk the tree, skip symlinks, sort rows by relative-path bytes, build payload lines `rel\tbytes\tsha256\n`, then SHA-256 the payload. Two of the three protected trees reproduced their expected digest exactly, which validates the reimplementation.

| Protected tree | Expected | Actual | Verdict |
| --- | --- | --- | --- |
| `manuscript_src/natcs` | 72 files, `21a1319b…` | 71 readable + 1 unreadable, `20fe9b46…` | `NOT_VERIFIABLE_DATALESS` |
| `refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3` | 11 files | 11 files, digest matches | `PASS` |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3` | 3 files | 3 files, digest matches | `PASS` |

Protected files: 9 total, 8 `PASS`, 0 `MISMATCH`, 0 `MISSING`, 1 `NOT_VERIFIABLE` (`output/ncs_review_corpus/v1_author_decision_register.json`). Output inventory: 6 total, 6 `PASS`.

Aggregate finding: zero `MISMATCH` across every readable protected file, protected tree and inventory item. Every failure is an availability failure.

## Blocking constraints

`P0-C1`. Do not delete `manuscript_src/natcs/discussion 2.md`. That directory is a protected tree whose expected `file_count` is 72, and the current tree contains exactly 72 files (71 readable plus 1 non-materialized) with the conflict copy included. The copy is therefore consistent with having been inside the frozen digest at REC-M3 acceptance. Deleting it would drop the count to 71 and guarantee a protected-tree mismatch. Recompute the digest after full materialization, then adjudicate.

`P0-C2`. Do not delete any `refine-logs` `' 2.'` copy of a hash-frozen `REC` record. Those copies are the superseded byte generation that 33 to 39 historical receipts bind to; they are provenance for historical verdicts, not garbage.

`P0-C3`. Do not treat `ORPHAN_NO_BASE` copies as redundant. Eleven conflict copies have no surviving base counterpart, so the `' 2.'` file is the only extant copy of that artifact.

`P0-C4`. Do not run any `make` target, test suite or scientific entry before materialization completes. Partially unreadable inputs produce false failures, and where a check treats an unreadable path as absent, false passes.

`P0-C5`. Report `tracked/clean`, `247/247`, `85/85` and `145/145` as `NOT_VERIFIABLE` until git resolves. `git rev-parse HEAD` fails and `git fsck` dumps core, so no commit-relative cleanliness claim is checkable. This directly gates `EMPIRICAL_IMPLEMENTATION_AUDIT` items 7 and 9 and the C3 static evidence, all of which bind frozen commits.

## Host-side remediation sequence

1. Materialize read-only with no writes: Finder Download Now on the repository root, or `brctl download` per subtree in the order `.git`, `manuscript_src`, `refine-logs`, `scripts`, `tests`, then `output`, `data`, `archive`.
2. Verify git: `git rev-parse HEAD`, `git status --porcelain` and `git fsck --full` must all return normally.
3. Re-run this triage to convert every `NOT_VERIFIABLE` row into `PASS` or `MISMATCH`.
4. Only then adjudicate the conflict copies, subject to `P0-C1` through `P0-C3`.
5. Recommended: relocate the repository out of the iCloud sync domain after taking a `git bundle` or a cold copy.

## Changed paths

- `refine-logs/REC-P0_WORKING_COPY_INTEGRITY_V1_20260823.md`
- `refine-logs/REC-P0_WORKING_COPY_INTEGRITY_V1_20260823.json`

No other file was created, modified or deleted. No git operation, `make` target, test suite or scientific entry was executed. Zero deletions were performed.
