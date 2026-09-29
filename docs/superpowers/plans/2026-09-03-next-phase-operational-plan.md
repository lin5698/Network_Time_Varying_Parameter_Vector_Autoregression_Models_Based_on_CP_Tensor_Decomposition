# NatCS Next-Phase Operational Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the verified NatCS package from readiness maintenance to evidence-controlled submission without changing scientific content or treating local checks as external approval.

**Architecture:** Keep four external gates independent: author decisions, Fig. 2 portal observation, raw-source access, and public-release readiness. Use the 2026-08-31 status-reconciliation rebuild as the local baseline. A material source or accepted decision change triggers the five-target build chain; unchanged state receives only non-mutating maintenance checks.

**Tech Stack:** Markdown/JSON evidence records, Node.js release gates, Make build targets, Git read-only inspection.

---

## Current Baseline

- Branch: `codex/m5-current-luna-science-recheck`.
- Controlling local receipt: `refine-logs/REC-P6_STATUS_RECONCILIATION_REBUILD_V1_20260831.md` and `.json`.
- Verified local posture: final gate `225` passes and `0` errors; release-safety audit `0` blockers and `0` warnings; focused suite `8/8` passing.
- Scientific posture: `RC-1 = ACTIVATED`; `RC-2 = ACTIVATED_WITH_LIMITATIONS`; `RCEP F3 = not_identified`.
- External gates still open: author decision, Fig. 2 portal preview, raw-source access, and public-release readiness.
- Existing worktree changes are preserved. Do not stage, commit, tag, merge, push, or create a Git snapshot without exact author authorization.

## Task 1: Weekly Maintenance Checkpoint

**Files:**
- Review: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Review: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Review: `manuscript_src/natcs/public_release_readiness_worksheet.md`

- [ ] **Step 1: Inspect for new evidence.**

Check whether a dated author reply, portal screenshot/observation, source licence/access record, repository assignment, or release decision has entered the workspace. Do not infer evidence from file presence, local surrogates, expected DOI, or build success.

- [ ] **Step 2: Run non-mutating maintenance gates only when no material change exists.**

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
git diff --check
```

Expected: final-gate errors are `0`, release-safety blockers/warnings are `0`, and only the known unresolved external-marker warnings remain visible.

- [ ] **Step 3: Avoid repetitive receipts.**

Do not create a maintenance receipt when source files, generators, accepted decisions, and external markers are unchanged. When a material maintenance finding or evidence change is recorded, set `NATCS_EVENT_DATE=$(date +%Y%m%d)` and create `REC-P6_WEEKLY_MAINTENANCE_V1_${NATCS_EVENT_DATE}.md/.json`.

## Task 2: Process A Real Author Decision Batch

**Files:**
- Review: `manuscript_src/natcs/natcs_coauthor_action_request.md`
- Modify only from explicit replies: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Modify only from explicit replies: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Modify only from explicit replies: `manuscript_src/natcs/public_release_readiness_worksheet.md`
- Create: dated `refine-logs/REC-P6_EXTERNAL_GATE_DECISIONS_V1_${NATCS_EVENT_DATE}.md/.json`, after setting `NATCS_EVENT_DATE=$(date +%Y%m%d)`.

- [ ] **Step 1: Record provenance before changing status.**

For each decision, record the date, named source, exact authorization or restriction, affected worksheet row, evidence reference, previous state, and resulting state.

- [ ] **Step 2: Apply only the narrowest wording.**

Keep `Derived substitute only` or `Provider public route only` where redistribution authority is absent. Do not add repository, DOI, licence, embargo, or public-access claims without a supplied record that establishes them.

- [ ] **Step 3: Validate the decision record.**

```bash
NATCS_EVENT_DATE=$(date +%Y%m%d)
jq -e . "refine-logs/REC-P6_EXTERNAL_GATE_DECISIONS_V1_${NATCS_EVENT_DATE}.json" >/dev/null
git diff --check
```

Expected: valid JSON and a diff limited to directly evidenced rows and their wording consequences. Then continue immediately to Task 4.

## Task 3: Process The First Real Fig. 2 Portal Preview

**Files:**
- Modify only during the actual preview: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review on failure: `manuscript_src/natcs/ncs_fig2_redesign_contract.md`
- Modify on failure only: `scripts/build_natcs_fig2_portal_surrogate.py`
- Create: dated `refine-logs/REC-P6_FIG2_PORTAL_OBSERVATION_V1_${NATCS_EVENT_DATE}.md/.json`, after setting `NATCS_EVENT_DATE=$(date +%Y%m%d)`.

- [ ] **Step 1: Capture the complete observation.**

Record portal state, timestamp, uploaded filename, displayed width, raster/vector behavior, label readability, page placement, validation messages, and screenshot path. A local surrogate cannot close a portal row.

- [ ] **Step 2: Close only observed checklist rows.**

Leave every requirement open when the portal view does not expose the required evidence. If the preview fails, apply only the corresponding redesign-contract requirement and regenerate the governed figure outputs.

- [ ] **Step 3: Return to Task 4 after any accepted portal change.**

Do not upload a corrected figure set until the complete package rebuild and final gates pass.

## Task 4: Rebuild After Any Accepted Change

**Files/targets:**
- `make natcs-evidence`
- `make natcs-manuscript`
- `make natcs-reviewer-archive`
- `make natcs-submission-materials`
- `make natcs-upload-freeze-manifest`

- [ ] **Step 1: Run the focused suite first.**

```bash
node --test tests/test_natcs_submission_support_disabled.mjs tests/test_natcs_active_manuscript_source_only.mjs tests/test_natcs_inactive_empirical_source_gate.mjs tests/test_natcs_fig2_surrogate_gate.mjs tests/test_empirical_results_numeric_alignment.mjs tests/test_natcs_source_empirical_boundary.mjs tests/test_natcs_release_gate.mjs tests/test_natcs_reviewer_archive_path_sanitization.mjs
```

Expected: `8` tests pass and `0` fail. This step may recreate downstream package content, so it must precede the final rebuild.

- [ ] **Step 2: Run the complete build chain in order.**

```bash
make natcs-evidence
make natcs-manuscript
make natcs-reviewer-archive
make natcs-submission-materials
make natcs-upload-freeze-manifest
```

Expected: every target exits `0`; do not start at `natcs-manuscript` when downstream artifacts must be preserved.

- [ ] **Step 3: Run final non-mutating verification.**

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
git diff --check
jq '.files.submission_materials | keys | length' output/submission_package/natcs_current/03_submission_materials/submission_inventory.json
jq '.artifacts | length' output/submission_package/natcs_current/03_submission_materials/natcs_upload_freeze_manifest.json
jq '.reviewer_archive.file_count' output/submission_package/natcs_current/03_submission_materials/natcs_upload_freeze_manifest.json
```

Expected: `0` final-gate errors, `0` release-safety blockers/warnings, and current baseline counts of `27`, `11`, and `342` unless an evidenced requirement changes them.

- [ ] **Step 4: Write the rebuild receipt.**

Set `NATCS_EVENT_DATE=$(date +%Y%m%d)` and record the accepted evidence, build targets, test/gate outcomes, package counts, remaining markers, and unchanged scientific posture in `REC-P6_POST_DECISION_REBUILD_V1_${NATCS_EVENT_DATE}.md/.json`. Do not stage files.

## Task 5: Submission-Day Authorization And Archival

**Files:**
- Modify after explicit authorization: `manuscript_src/natcs/submission_checklist.md`
- Review: `manuscript_src/natcs/ncs_portal_field_kit.md`
- Review: `output/submission_package/natcs_current/03_submission_materials/natcs_upload_freeze_manifest.md`
- Create only from real events, after setting `NATCS_EVENT_DATE=$(date +%Y%m%d)`: `REC-P6_SUBMISSION_DAY_AUTHORIZATION_V1_${NATCS_EVENT_DATE}.md/.json` and `REC-P6_SUBMISSION_EVENT_V1_${NATCS_EVENT_DATE}.md/.json`

- [ ] **Step 1: Require an intended date and submitting-author authorization.**

Without both, retain readiness-only status and do not upload or alter the checklist to imply submission.

- [ ] **Step 2: Freeze the exact upload list.**

Copy the exact manuscript, supplement, figure-source, cover-letter, metadata, declaration, and reference filenames from the current upload-freeze manifest. Preserve representation-level claims, the four active benchmark values, and the causal/generality boundary.

- [ ] **Step 3: Verify immediately before upload.**

Run the final gate and release-safety commands from Task 4. Expected: `0` final-gate errors and `0` release-safety blockers/warnings.

- [ ] **Step 4: Record the actual event.**

Record manuscript ID, timestamp, uploaded version, submitting author, accepted/rejected files, portal messages, Fig. 2 observation, metadata corrections, and confirmation reference. If no confirmation exists, use the literal status `UPLOAD_NOT_CONFIRMED`.

- [ ] **Step 5: Handle corrections through the same rebuild chain.**

Any source-controlled wording or figure correction returns to Task 4 before another upload. A post-submission Git snapshot remains a separate action requiring exact path authorization.

## Cadence And Stop Conditions

- Weekly while no external evidence changes: Task 1 only.
- On author replies: Tasks 2 and 4 in the same session.
- On the first real portal preview: Tasks 3 and 4.
- Seven days before an authorized submission: Tasks 1 and 4, then prepare Task 5.
- On submission day: Task 5 through the event receipt.
- Stop on any final-gate error, release-safety blocker/warning, focused-test failure, ambiguous access/licence/portal evidence, unauthorized figure redesign, unauthorized upload, or missing exact Git scope.

## Completion Criteria

The phase is complete only when every closed external marker has dated evidence, the submitted artifact list has passed one evidence-first rebuild, and the submission receipt contains manuscript ID, timestamp, uploaded version, and portal feedback. `PASS_WITH_WARNINGS_ALLOWED` never means that external markers are closed.
