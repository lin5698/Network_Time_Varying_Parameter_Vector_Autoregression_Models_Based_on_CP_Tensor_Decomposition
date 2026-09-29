# NatCS Pre-Submission Long-Term Work Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Maintain a reproducible, evidence-bounded Nature Computational Science submission package until all author-controlled and externally controlled pre-submission gates are resolved.

**Architecture:** Keep authored sources under `manuscript_src/natcs`, generated artifacts under ignored `output/`, and dated decision evidence under `refine-logs/`. Rebuild the complete chain after every accepted source or access decision. RC-1 remains activated, RC-2 remains limited to descriptive reproducible readouts, and RCEP F3 remains `not_identified` unless a new scientific decision is explicitly documented.

**Tech Stack:** Markdown/JSON decision records, Node.js build scripts, Python figure utilities, Make targets, static Node test suite, Git status/diff inspection.

---

### Phase 1: Keep the current package reproducible

**Files:**
- Review: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Review: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Review: `manuscript_src/natcs/public_release_readiness_worksheet.md`
- Review: `refine-logs/REC-P3_RELEASE_POSTURE_FOLLOWUP_V1_20260830.md`

- [x] At each maintenance checkpoint, run `node scripts/check_natcs_final_gates.mjs` and require `errors: []`.
- [x] Run `node scripts/audit_natcs_release_safety.mjs --check` and require `blockers: 0` and `warnings: 0`.
- [ ] Reconcile historical gate wording before each submission review: compare the current author decision sheet with the Fig. 2 checklist and other audit notes; preserve historical audit context, but ensure the upload-day entry point states the current RC-1/RC-2 posture without implying that a portal observation exists.
- [x] Confirm the four unresolved marker counts remain visible: author decision, Fig. 2 portal preview, raw-source access, and public-release readiness.
- [x] Do not rerun scientific experiments or edit empirical numbers during maintenance-only checkpoints.

### Phase 2: Collect author-controlled decisions

**Files:**
- Modify only after author confirmation: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Modify only after author confirmation: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Modify only after author confirmation: `manuscript_src/natcs/public_release_readiness_worksheet.md`
- Create for each decision batch: `refine-logs/REC-P3_EXTERNAL_GATE_DECISIONS_V1_YYYYMMDD.md` and `.json`

- [ ] Record each decision with date, decision-maker/source, exact authorization, affected row, and resulting state.
- [ ] Complete raw-source rows source-by-source; retain `Derived substitute only` or `Provider public route only` where redistribution terms are unknown.
- [ ] Choose code licence, derived-evidence terms, repository route, release title, and embargo only from explicit author/institution approval and applicable provider/journal terms.
- [ ] Keep DOI, repository, licence, and public-access claims absent until a concrete record exists.

### Phase 3: Close the journal-portal gate only with portal evidence

**Files:**
- Modify after an actual upload observation: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review: `manuscript_src/natcs/ncs_fig2_redesign_contract.md`
- Review: `scripts/build_natcs_fig2_portal_surrogate.py`
- Create: dated portal observation receipt under `refine-logs/`

- [ ] During a real submission or journal-provided preview, capture the portal state, upload width, raster/vector behavior, labels, page placement, and observation timestamp.
- [ ] Close only checklist rows directly supported by that observation; keep local surrogate checks explicitly separate.
- [ ] If the portal fails, apply the existing redesign contract, regenerate figures, refresh contact sheets and source ZIP, then perform rendered-page QA.
- [ ] If the portal passes, preserve the approved figure sources and record the evidence without redesign.

### Phase 4: Rebuild and validate after accepted evidence

**Files:**
- Use: `scripts/build_natcs_evidence.mjs`
- Use: `scripts/build_natcs_manuscript.mjs`
- Use: `scripts/finalize_natcs_package.mjs`
- Use: `scripts/create_natcs_figure_source_package.mjs`
- Use: `scripts/build_natcs_reviewer_archive.mjs`
- Use: `scripts/finalize_natcs_submission_materials.mjs`
- Use: `scripts/create_natcs_upload_freeze_manifest.mjs`

- [x] Run, in order: `make natcs-evidence`, `make natcs-manuscript`, `make natcs-reviewer-archive`, `make natcs-submission-materials`, `make natcs-upload-freeze-manifest`.
- [x] Run `node scripts/check_natcs_final_gates.mjs`, `node scripts/audit_natcs_release_safety.mjs --check`, and `git diff --check`.
- [x] Run the full focused suite: `node --test tests/test_natcs_submission_support_disabled.mjs tests/test_natcs_active_manuscript_source_only.mjs tests/test_natcs_inactive_empirical_source_gate.mjs tests/test_natcs_fig2_surrogate_gate.mjs tests/test_empirical_results_numeric_alignment.mjs tests/test_natcs_source_empirical_boundary.mjs tests/test_natcs_release_gate.mjs tests/test_natcs_reviewer_archive_path_sanitization.mjs`.
- [x] Record artifact counts, warning counts, marker states, RC-1/RC-2, and RCEP F3 in a dated posture receipt.

### Phase 5: Submission-readiness review

**Files:**
- Review: `output/submission_package/natcs_current/README.md`
- Review: `output/submission_package/natcs_current/03_submission_materials/submission_inventory.json`
- Review: `output/submission_package/natcs_current/03_submission_materials/natcs_upload_freeze_manifest.md`
- Review: `output/reviewer_archive/natcs_reviewer_archive/manifest.json`
- Review: `manuscript_src/natcs/submission_checklist.md`

- [x] Confirm main manuscript and supplementary PDF/DOCX/TeX artifacts correspond to one rebuild timestamp.
- [x] Confirm figure source ZIP, reviewer archive ZIP, inventory, freeze manifest, cover letter, metadata, declarations, and references are present and mutually routed.
- [x] Confirm the final author decision sheet is the upload-day entry point and unresolved external markers remain visible.
- [x] Confirm no credentials, private paths, restricted raw files, unsupported DOI/licence claims, or hidden experimental outputs enter the upload package.
- [ ] Prepare a submission-day checklist containing only actions authorized by the author and journal portal.

### Phase 6: Submission-day and immediate follow-up

**Files:**
- Review/update after the actual event: `manuscript_src/natcs/ncs_portal_field_kit.md`
- Review/update after the actual event: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Create: dated submission-event and portal-observation receipts under `refine-logs/`

- [ ] Before upload, record the exact frozen artifact names and local manifest timestamp.
- [ ] During upload, record portal validation messages and Fig. 2 observations; do not infer success from local files.
- [ ] After submission, record manuscript ID, date, uploaded version, and any requested metadata corrections supplied by the journal.
- [ ] If a correction changes authored sources, rebuild the complete chain and rerun all gates before sending an update.

### Phase 7: Snapshot authorization and archival hygiene

**Files:**
- Review: `git status --short`
- Review: `git diff --stat`
- Review: final posture receipt

- [ ] Present the exact tracked-file snapshot scope to the author before staging.
- [ ] Create no commit, tag, or branch snapshot without explicit authorization for that exact scope.
- [ ] If authorized, stage only the approved files, run `git diff --cached --check`, and record the commit identifier.

## Long-Term Cadence

- Weekly while waiting: run the Phase 1 checks and review unresolved marker ownership; do not rebuild unless source files changed.
- After every author or portal decision: execute Phases 2-4 immediately and archive the receipt.
- One week before intended submission: execute Phase 5 and resolve only blockers that have evidence or explicit authorization.
- On submission day: execute Phase 6 against the frozen package.
- After submission: preserve the submitted artifact manifest and keep any post-submission changes in a new dated chain.

## Success Criteria

- Final gate has no errors and release-safety audit has zero blockers.
- Every closed external marker has a dated, inspectable evidence record; unsupported markers remain open.
- RC-1 and RC-2 statuses are unchanged, and RCEP F3 remains `not_identified` unless separately authorized.
- No scientific experiment is rerun as part of release preparation.
- No Git snapshot is created without explicit author authorization.
