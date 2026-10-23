# NatCS Post-Readiness Long-Term Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the verified NatCS package, close only externally evidenced gates, execute a controlled submission workflow, and retain an inspectable post-submission record without changing the approved scientific scope.

**Architecture:** Treat the 2026-08-31 readiness recheck as the local baseline. Keep maintenance, author decisions, portal observations, package rebuilds, submission events, and Git authorization as separate state transitions. Every accepted source or access change triggers the complete evidence-first five-target rebuild; local success never substitutes for author or journal evidence.

**Tech Stack:** Markdown/JSON records, Node.js release gates, Make targets, Python figure sources, Node test runner, Git read-only inspection.

---

## Baseline And Boundaries

- Controlling local receipt: `refine-logs/REC-P5_SUBMISSION_READINESS_RECHECK_V1_20260831.md` and `.json`.
- Verified state: final gate 225 passes and 0 errors; release safety 0 blockers and 0 warnings; focused suite 8/8 passing.
- Open markers: author decision 4, Fig. 2 portal preview 5, raw-source access 42, public-release readiness 25.
- Scientific posture: `RC-1 = ACTIVATED`, `RC-2 = ACTIVATED_WITH_LIMITATIONS`, `RCEP F3 = not_identified`.
- Do not rerun scientific experiments, edit empirical values, or add new artifact-digest logic.
- Do not create a commit, tag, merge, push, or snapshot without exact scope authorization.
- Do not close a marker from a surrogate, build result, repository presence, expected DOI, or assumed licence.
- At the start of a real maintenance or external-evidence event, set `NATCS_EVENT_DATE=$(date +%Y%m%d)` and use `${NATCS_EVENT_DATE}` as the receipt filename suffix.

### Task 1: Reconcile Current And Historical Gate Wording

**Files:**
- Modify: `manuscript_src/natcs/submission_external_dependency_register.md`
- Review: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Review: `refine-logs/REC-P3_RC1_RC2_ACTIVATION_V1_20260830.md`

- [x] **Step 1: Locate historical status statements.**

```bash
rg -n "NOT_GRANTED|POTENTIAL_ONLY_NOT_ACTIVATED|RC-1|RC-2|RC-3" manuscript_src/natcs/submission_external_dependency_register.md manuscript_src/natcs/natcs_final_author_decision_sheet.md
```

Expected: the dependency register exposes its 2026-08-26 historical wording; the decision sheet exposes the current activated posture.

- [x] **Step 2: Add a dated current-state notice.**

State that the old dependency rows are retained as historical context and that the current controlling state is `RC-1 = ACTIVATED`, `RC-2 = ACTIVATED_WITH_LIMITATIONS`, `RCEP F3 = not_identified`. Do not rewrite historical rows or imply a portal observation.

- [x] **Step 3: Verify consistency.**

```bash
rg -n "ACTIVATED|ACTIVATED_WITH_LIMITATIONS|not_identified|No external portal observation" manuscript_src/natcs/natcs_final_author_decision_sheet.md manuscript_src/natcs/submission_external_dependency_register.md
git diff --check
```

Expected: current status is visible, historical context remains visible, and the diff check passes.

### Task 2: Maintain The Package While Waiting

**Files:**
- Review: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Review: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Review: `manuscript_src/natcs/public_release_readiness_worksheet.md`
- Create only after a material change: dated `REC-P6_WEEKLY_MAINTENANCE` Markdown/JSON pair under `refine-logs/`

- [x] **Step 1: Run weekly gates.**

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
```

Expected: final-gate errors are empty; release safety reports 0 blockers and 0 warnings. Final-gate warnings may contain only the four known marker groups.

- [x] **Step 2: Confirm marker visibility.**

```bash
rg -n "ACTIVATED|ACTIVATED_WITH_LIMITATIONS|not_identified|Needs action|Unresolved" manuscript_src/natcs/natcs_final_author_decision_sheet.md manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md manuscript_src/natcs/raw_source_access_decision_worksheet.md manuscript_src/natcs/public_release_readiness_worksheet.md
```

Expected: unresolved items remain explicit and no local result is represented as external closure.

- [x] **Step 3: Rebuild only on a material source change.**

Inspect `git status --short`. If no authored source, generator, or accepted access decision changed, do not rebuild and do not create a repetitive receipt. If one changed, proceed to Task 5.

### Task 3: Process Author Decisions

**Files:**
- Review: `manuscript_src/natcs/natcs_coauthor_action_request.md`
- Modify only from explicit replies: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Modify only from explicit replies: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Modify only from explicit replies: `manuscript_src/natcs/public_release_readiness_worksheet.md`
- Create after a real decision batch: dated `REC-P6_EXTERNAL_GATE_DECISIONS` Markdown/JSON pair under `refine-logs/`

- [ ] **Step 1: Collect only unresolved decisions.**

Request source-by-source raw access, repository route, code licence, derived-evidence terms, release contents, exclusions, and embargo timing. Do not request a scientific rerun.

- [ ] **Step 2: Record evidence provenance first.**

For each reply record its date, named source, exact authorization, affected row, evidence reference, prior state, and resulting state.

- [ ] **Step 3: Apply the narrowest authorized wording.**

Retain `Derived substitute only` or `Provider public route only` where redistribution authority is absent. Keep repository, DOI, licence, and public-access claims absent until established by the supplied record.

- [ ] **Step 4: Validate the decision batch.**

```bash
NATCS_EVENT_DATE=$(date +%Y%m%d)
jq -e . "refine-logs/REC-P6_EXTERNAL_GATE_DECISIONS_V1_${NATCS_EVENT_DATE}.json" >/dev/null
git diff --check
git diff -- manuscript_src/natcs/natcs_final_author_decision_sheet.md manuscript_src/natcs/raw_source_access_decision_worksheet.md manuscript_src/natcs/public_release_readiness_worksheet.md
```

Expected: JSON parses and the diff contains only evidenced rows and their direct wording consequences.

### Task 4: Process The Real Portal Observation

**Files:**
- Modify only during an actual preview: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review on failure: `manuscript_src/natcs/ncs_fig2_redesign_contract.md`
- Modify on failure only: `scripts/build_natcs_fig2_portal_surrogate.py`
- Create after the event: dated `REC-P6_FIG2_PORTAL_OBSERVATION` Markdown/JSON pair under `refine-logs/`

- [ ] **Step 1: Capture the observation boundary.**

Record portal state, timestamp, uploaded file, display width, raster/vector behavior, label readability, page placement, validation messages, and screenshot paths. A local surrogate does not satisfy this step.

- [ ] **Step 2: Close only observed rows.**

Leave a checklist row open when the portal view does not expose its required evidence.

- [ ] **Step 3: Follow the observed branch.**

If the preview passes, preserve figure sources. If it fails, apply only the affected redesign-contract requirement, regenerate the figure set, refresh contact sheets and the figure-source ZIP, and perform rendered-page QA.

- [ ] **Step 4: Route every accepted result to Task 5.**

Neither a portal pass nor a corrected local figure is a finished package until Task 5 passes.

### Task 5: Rebuild And Verify After Every Accepted Change

Execution batch 2026-08-31: completed for the current/historical status reconciliation change. Repeat this task after each later accepted change.

**Files:**
- Use: `scripts/build_natcs_evidence.mjs`
- Use: `scripts/build_natcs_manuscript.mjs`
- Use: `scripts/build_natcs_reviewer_archive.mjs`
- Use: `scripts/finalize_natcs_submission_materials.mjs`
- Use: `scripts/create_natcs_upload_freeze_manifest.mjs`
- Generated: `output/submission_package/natcs_current/`
- Create: dated `REC-P6_POST_DECISION_REBUILD` Markdown/JSON pair under `refine-logs/`

- [x] **Step 1: Run the focused tests before the final rebuild.**

```bash
node --test tests/test_natcs_submission_support_disabled.mjs tests/test_natcs_active_manuscript_source_only.mjs tests/test_natcs_inactive_empirical_source_gate.mjs tests/test_natcs_fig2_surrogate_gate.mjs tests/test_empirical_results_numeric_alignment.mjs tests/test_natcs_source_empirical_boundary.mjs tests/test_natcs_release_gate.mjs tests/test_natcs_reviewer_archive_path_sanitization.mjs
```

Expected: 8 focused tests pass. `test_natcs_release_gate.mjs` invokes the evidence and manuscript builders, so the package is not final after this step.

- [x] **Step 2: Run the complete dependency chain after the tests.**

```bash
make natcs-evidence
make natcs-manuscript
make natcs-reviewer-archive
make natcs-submission-materials
make natcs-upload-freeze-manifest
```

Expected: all targets exit 0. Never start at `natcs-manuscript`; it recreates `output/submission_package/natcs_current` and removes downstream artifacts.

- [x] **Step 3: Run the non-mutating release checks.**

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
git diff --check
```

Expected: 0 final-gate errors, 0 release-safety blockers/warnings, and a clean diff check.

- [x] **Step 4: Inspect package structure.**

Require the 27-key inventory, 11 upload artifacts, and 342-file reviewer archive unless an evidenced external requirement legitimately changes a count. Record the accepted-decision receipt, counts, gate results, remaining markers, and scientific posture. Do not stage files.

### Task 6: Run Submission Day And Post-Submission Archival

**Files:**
- Modify after author upload authorization: `manuscript_src/natcs/submission_checklist.md`
- Review: `manuscript_src/natcs/ncs_portal_field_kit.md`
- Review: `output/submission_package/natcs_current/03_submission_materials/natcs_upload_freeze_manifest.md`
- Create from real events: dated `REC-P6_SUBMISSION_DAY_AUTHORIZATION` and `REC-P6_SUBMISSION_EVENT` Markdown/JSON pairs under `refine-logs/`
- Create after exact Git approval: dated `REC-P7_GIT_SNAPSHOT_AUTHORIZATION` Markdown/JSON pair under `refine-logs/`

- [ ] **Step 1: Stop unless upload is explicitly authorized.**

Require an intended submission date and author authorization for portal upload. Otherwise retain readiness-only status.

- [ ] **Step 2: Freeze the authorized upload list.**

Record exact manuscript, supplement, figure-source, cover-letter, metadata, declaration, and reference artifact names from the current manifest. Use only approved portal-field variants and preserve the representation-level claim, four active benchmark values, and causal/generality boundary.

- [ ] **Step 3: Run pre-upload gates.**

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
```

Expected: 0 final-gate errors and 0 release-safety blockers/warnings.

- [ ] **Step 4: Record the actual submission event.**

Record portal validation messages, accepted/rejected files, Fig. 2 observation, metadata corrections, final file set, manuscript ID, timestamp, uploaded version, submitting author, and portal confirmation reference. If confirmation is absent, record `UPLOAD_NOT_CONFIRMED`.

- [ ] **Step 5: Rebuild before any corrected resubmission.**

If a correction changes source-controlled wording or figures, update the governed source and return to Task 5 before uploading again.

- [ ] **Step 6: Request exact Git snapshot authorization.**

Present `git status --short` and `git diff --stat`, separating unrelated pre-existing changes and ignored generated outputs. Only after exact approval stage the accepted paths, then run:

```bash
git diff --cached --check
git diff --cached --stat
```

Expected: no whitespace errors and the staged list exactly matches the approved scope. No authorization means no staging or commit.

## Cadence

- Weekly while waiting: Task 2; skip unchanged receipts.
- After an author decision: Tasks 3 and 5 in the same work session.
- During the first real portal preview: Tasks 4 and 5.
- Seven days before submission: Tasks 2 and 5, then prepare Task 6.
- On submission day: Task 6 through the event record.
- Within one day after confirmed submission: Task 6 snapshot-scope presentation, stopping before staging without exact approval.
- After a journal-requested source correction: Tasks 5 and 6 with a new dated record chain.

## Stop Conditions And Completion Criteria

- Stop on any final-gate error, release-safety blocker/warning, or focused-test failure.
- Stop when evidence is ambiguous about access, licence, repository, DOI, embargo, or portal outcome.
- Stop before figure redesign without a real portal failure, before upload without author authorization, and before staging without exact scope authorization.
- Completion requires dated evidence for every closed marker, one passing evidence-first rebuild for the submitted artifact list, and a confirmed submission record containing manuscript ID, timestamp, uploaded version, and portal feedback.
