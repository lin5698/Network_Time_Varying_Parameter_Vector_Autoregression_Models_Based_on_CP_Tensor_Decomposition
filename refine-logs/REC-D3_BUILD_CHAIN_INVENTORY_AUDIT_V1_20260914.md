# D3 Build-Chain and Package-Inventory Audit V1

- Date: 2026-09-14
- Task: D3 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (static build-chain audit + inventory comparison vs baseline; no rebuild executed as part of this task)
- Scope: read-only audit of the Makefile, the five release builders, and the existing `output/` inventories. No `make` target was executed by this task; no file outside this receipt was changed.

## 1. Five-target chain and enforcement points

| Stage (required order) | Makefile line | Script | Input gate |
| --- | --- | --- | --- |
| 1. `natcs-evidence` | `Makefile:1-2` | `scripts/build_natcs_evidence.mjs` | `requireReleaseableNatcsEvidence(ROOT)` first, at `:1475` |
| 2. `natcs-manuscript` | `:4-8` (three scripts: `build_natcs_manuscript.mjs`, `finalize_natcs_package.mjs`, `create_natcs_figure_source_package.mjs`) | builder calls `requireReleaseableNatcsEvidence` at `:700` and re-checks package consistency (missing evidence paths / blocked evidence) at `:585-600` | consumes evidence outputs by path |
| 3. `natcs-reviewer-archive` | `:12-13` | `scripts/build_natcs_reviewer_archive.mjs`, `requireReleaseableNatcsEvidence` at `:880` | re-renders manuscript sources |
| 4. `natcs-submission-materials` | `:15-16` | `scripts/finalize_natcs_submission_materials.mjs`; throws on any missing authored doc (`:44-45`) and on nonzero release-safety blockers (`:60-62`) | copies authored docs + runs live release-safety audit |
| 5. `natcs-upload-freeze-manifest` | `:18-19` | `scripts/create_natcs_upload_freeze_manifest.mjs`, `requireReleaseableNatcsEvidence` at `:120` | inventories main/SI PDF+DOCX, upload ZIPs, figure-source ZIP, reviewer-archive ZIP/manifest/README, submission inventory, own manifest |

Order enforcement is **gate-based, not Makefile-dependency-based**: the Makefile targets carry no inter-target prerequisites, but each stage re-verifies the audit posture (`requireReleaseableNatcsEvidence`, `scripts/natcs_utils.mjs:28-43`: both root audits PASS with `rcep_nyc_value_audited_*` reason codes, RC-1/RC-2 activation receipt present, rerun flag false) and consumes the previous stage's outputs by path. A stage run out of order fails on missing inputs (stage 2's existence scan at `build_natcs_manuscript.mjs:585-600`; stage 4's missing-doc throw) rather than silently producing a stale package. The adjacent targets (`natcs-figure-source-package` `:9-10`, `natcs-release-safety-audit` `:21-22`, `natcs-final-gate-check` `:24-25`, `natcs-source-only-gate-check` `:27-28`) are supporting checks; the figure-source ZIP is folded into stage 2 and packaged downstream by stage 5 (`create_natcs_upload_freeze_manifest.mjs:144`), so there is no unpackaged generator output.

## 2. Inventory comparison vs P6 baseline (2026-09-03)

| Item | P6 baseline | Current (2026-09-14) | Delta | Explanation |
| --- | --- | --- | --- | --- |
| Submission-material entries (inventory `files.submission_materials` keys) | 27 | **10** | −17 | Explained: the submission-materials finalize stage (stage 4) has **not** been re-run since the package drifted; `output/submission_package/natcs_current/03_submission_materials/` holds 12 files instead of the 27-inventory set (release-safety audits, Fig. 2 contact sheets, worksheets, freeze manifest all absent). The authored sources for all 27 entries still exist (`finalize_natcs_submission_materials.mjs` DOCS list intact), so a full chain re-run restores the count. **Unexplained root cause: why stage 4-5 were last run 2026-09-04/05 while P6 receipts (2026-09-03) recorded 27/11/342 — a post-baseline regeneration evidently skipped the last two stages. This is the same drift recorded in REC-A2.** |
| Upload-freeze artifacts | 11 | **manifest absent** | −11 | Same cause: stage 5 never produced/survived past the drift window; `natcs_upload_freeze_manifest.json/.md` missing from `03_submission_materials/`. |
| Reviewer archive files | 342 | **342** | 0 | Matches baseline byte-count of files (`output/reviewer_archive/natcs_reviewer_archive/`); archive manifest mtime 2026-09-03. |
| Release-safety scanned files | 425 | 397 seen (329 text, 68 binary) | −28 | Explained: fewer generated files exist in the drifted `output/submission_package` tree; audit result remains 0 blockers / 0 warnings. |

**Classification: the −17/−11 deltas are explained mechanically (last-two-stages not re-run) but the post-baseline event that caused the partial package is unexplained by any receipt — recorded as an open finding for the E1-lane (a full five-target rebuild plus E2 review is required before submission-day use).**

## 3. Determinism spot-check

During D2, `tests/test_natcs_release_gate.mjs` involuntarily re-ran stages 1-2 (it spawns `build_natcs_evidence.mjs` and `build_natcs_manuscript.mjs`, `tests/test_natcs_release_gate.mjs:12-13`; documented behavior per `REC-P6_STATUS_RECONCILIATION_REBUILD_V1_20260831`). Post-rebuild values equal the pre-rebuild bytes (`nyc_validation` share medians 0.3714912…/0.4809697… unchanged), confirming the evidence/manuscript stages are deterministic under the current source state; the drift is confined to stages 4-5 not being run.

## 4. Findings

1. **Package drift (pre-existing, blocking submission-day use):** stages 4-5 outputs missing; final gate 167 passes / 63 errors, all errors being missing `03_submission_materials` files or SVG-diff items against the drifted package. Repair path: run the five-target chain in order after the next accepted source change (E1-class), then E2 review.
2. **No order-violation risk found** in the five-target chain; gate-first ordering is enforced inside every stage script.
3. **No downstream omission found:** every generator output referenced by the freeze manifest exists or is covered by the stage-2/4 flows; the legacy `scripts/natcs_evidence.py` is actively excluded from the archive (`build_natcs_reviewer_archive.mjs:817-819`).
4. **Sibling directories** `output/submission_package/natcs_current 2|3|4` are historical leftovers (June/July mtimes), referenced by nothing in the chain; recorded as cleanup candidates for the author, not touched.

## Verification

- `node scripts/check_natcs_final_gates.mjs`: pre-existing FAIL (167/63) — unchanged by this task; see finding 1.
- `node scripts/audit_natcs_release_safety.mjs --check`: 0 blockers, 0 warnings.
- Reviewer archive file count re-counted: 342.
- `git diff --check`: passed. Footprint: this receipt only; no `output/` directory was written by D3 itself.
