# NatCS Release Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the remaining external release gates while preserving the limited descriptive empirical activation already approved.

**Architecture:** Treat the current manuscript/evidence/archive chain as frozen until an external marker is resolved. Each author or portal decision is recorded as a receipt, followed by a complete rebuild and final-gate audit. No scientific experiment is rerun and no historical audit verdict is rewritten.

**Tech Stack:** Markdown/JSON receipts, Node.js build scripts, `make` targets, static release gates.

---

### Task 1: Review the four open author marker groups

**Files:**
- Review: `output/submission_package/natcs_current/03_submission_materials/natcs_final_author_decision_sheet.md`
- Review: `output/submission_package/natcs_current/03_submission_materials/ncs_fig2_portal_preview_checklist.md`
- Review: `output/submission_package/natcs_current/03_submission_materials/raw_source_access_decision_worksheet.md`
- Review: `output/submission_package/natcs_current/03_submission_materials/public_release_readiness_worksheet.md`

- [ ] Record the author's decision for each marker without changing unresolved rows.
- [ ] Keep the current conservative statements where portal, raw-source or DOI evidence is absent.

### Task 2: Resolve only externally evidenced decisions

**Files:**
- Create: `refine-logs/REC-P3_EXTERNAL_GATE_DECISIONS_V1_YYYYMMDD.{md,json}`

- [ ] Record portal preview evidence, raw-source access decisions and public-release status only when supplied by the author or external system.
- [ ] Do not infer closure from local build success; leave unsupported markers open.

### Task 3: Rebuild after any accepted decision

**Files:**
- Use: `scripts/build_natcs_evidence.mjs`
- Use: `scripts/build_natcs_manuscript.mjs`
- Use: `scripts/build_natcs_reviewer_archive.mjs`
- Use: `scripts/finalize_natcs_submission_materials.mjs`
- Use: `scripts/create_natcs_upload_freeze_manifest.mjs`

- [ ] Run `make natcs-evidence`.
- [ ] Run `make natcs-manuscript`.
- [ ] Run `make natcs-reviewer-archive`.
- [ ] Run `make natcs-submission-materials`.
- [ ] Run `make natcs-upload-freeze-manifest`.

### Task 4: Re-run release gates and archive posture

**Files:**
- Use: `scripts/audit_natcs_release_safety.mjs`
- Use: `scripts/check_natcs_final_gates.mjs`
- Create: `refine-logs/REC-P3_RELEASE_POSTURE_FOLLOWUP_V1_YYYYMMDD.{md,json}`

- [ ] Require release safety to report zero blockers and zero warnings.
- [ ] Require final gate errors to be empty; warnings may remain only for explicitly unresolved external markers.
- [ ] Record the resulting posture and marker counts.

### Task 5: Git snapshot decision

- [ ] Do not create a commit or snapshot automatically.
- [ ] Create one only after the author explicitly authorizes the exact snapshot scope.

## Success Criteria

- RC-1 remains activated and RC-2 remains limited to descriptive, reproducible readouts.
- RCEP F3 remains `not_identified`.
- No scientific experiment is rerun.
- All regenerated packages pass the final gate with no errors.
- Unsupported external markers remain visible and are not auto-closed.
