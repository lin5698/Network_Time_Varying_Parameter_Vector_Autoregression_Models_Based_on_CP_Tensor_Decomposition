# External Release Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the remaining externally controlled release gates and produce a final, evidence-backed NatCS submission package without changing the approved empirical scope.

**Architecture:** Keep the manuscript source, generated submission package, reviewer archive, and release receipts as one reproducible chain. External observations are recorded first; only then are affected materials regenerated and the final gates rerun. RC-1 stays activated, RC-2 stays limited to descriptive reproducible readouts, RCEP F3 stays `not_identified`, and no scientific experiment is rerun.

**Tech Stack:** Markdown/JSON decision receipts, Node.js build scripts, Make targets, static release-gate tests, Git status/diff inspection.

---

### Task 1: Prepare the external evidence intake

**Files:**
- Review: `manuscript_src/natcs/natcs_final_author_decision_sheet.md`
- Review: `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`
- Review: `manuscript_src/natcs/raw_source_access_decision_worksheet.md`
- Review: `manuscript_src/natcs/public_release_readiness_worksheet.md`
- Review: `refine-logs/REC-P3_RELEASE_POSTURE_FOLLOWUP_V1_20260830.md`

- [ ] Confirm the four open marker groups and copy their current unresolved wording into the working checklist; do not change any decision row.
- [ ] Define the minimum evidence required for each marker: dated Fig. 2 portal observation, signed raw-source rows, assigned repository/DOI/licence/access terms, and byte-identical companion support files.
- [ ] Verify that the current package remains locally reproducible before collecting external evidence:

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
```

Expected: `status: PASS_WITH_WARNINGS_ALLOWED`, `errors: []`, and release-safety `blockers: 0`.

### Task 2: Record only supplied external decisions

**Files:**
- Create: `refine-logs/REC-P3_EXTERNAL_GATE_DECISIONS_V1_YYYYMMDD.md`
- Create: `refine-logs/REC-P3_EXTERNAL_GATE_DECISIONS_V1_YYYYMMDD.json`
- Modify only when evidence exists: the four source worksheets/checklists under `manuscript_src/natcs/`

- [ ] For each supplied artifact, record its date, source, exact observation or authorization, affected marker, and resulting state (`closed` or `open`).
- [ ] Leave a marker open when the supplied evidence does not meet the worksheet's closure condition.
- [ ] Do not record portal success from a local surrogate, do not infer raw-source access from repository presence, and do not assign DOI/licence/access terms without an author or platform record.
- [ ] Validate the receipt shape and inspect the diff:

```bash
node --check scripts/check_natcs_final_gates.mjs
git diff --check
git status --short
```

Expected: no syntax or whitespace errors; only explicitly authorized receipt/worksheet changes are present.

### Task 3: Apply an evidence-specific material update

**Files:**
- Modify only the source file(s) implicated by the accepted decision.
- Use the existing generators: `scripts/build_natcs_manuscript.mjs`, `scripts/finalize_natcs_package.mjs`, `scripts/create_natcs_figure_source_package.mjs`, `scripts/build_natcs_reviewer_archive.mjs`, `scripts/finalize_natcs_submission_materials.mjs`, `scripts/create_natcs_upload_freeze_manifest.mjs`.

- [ ] If Fig. 2 passes portal preview, archive the observation and keep figure sources unchanged.
- [ ] If Fig. 2 fails preview, follow `manuscript_src/natcs/ncs_fig2_redesign_contract.md`, regenerate the figure set, refresh the contact sheet and figure-source package, and perform page-render QA before continuing.
- [ ] If raw-source defaults are signed off without new access, transfer the sign-off only; do not rewrite availability wording.
- [ ] If confirmed raw-source or public-release access changes, update the affected availability text while preserving the existing overclaim bans and representation-level positioning.
- [ ] Rebuild the complete chain after any accepted source update:

```bash
make natcs-evidence
make natcs-manuscript
make natcs-reviewer-archive
make natcs-submission-materials
make natcs-upload-freeze-manifest
```

Expected: every target exits `0`; generated source and packaged copies are refreshed.

### Task 4: Run final release validation

**Files:**
- Review: `scripts/check_natcs_final_gates.mjs`
- Review: `scripts/audit_natcs_release_safety.mjs`
- Create: `refine-logs/REC-P3_RELEASE_POSTURE_FINAL_V1_YYYYMMDD.md`
- Create: `refine-logs/REC-P3_RELEASE_POSTURE_FINAL_V1_YYYYMMDD.json`

- [ ] Run the final checks:

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
node tests/test_natcs_submission_support_disabled.mjs
node tests/test_natcs_active_manuscript_source_only.mjs
node tests/test_natcs_inactive_empirical_source_gate.mjs
node tests/test_natcs_fig2_surrogate_gate.mjs
node tests/test_empirical_results_numeric_alignment.mjs
node tests/test_natcs_release_gate.mjs
node tests/test_natcs_reviewer_archive_path_sanitization.mjs
```

- [ ] Record exact error and warning counts, marker states, artifact counts, and the empirical-scope invariants in the final posture receipt.
- [ ] Accept `PASS_WITH_WARNINGS_ALLOWED` only while warnings correspond to explicitly unresolved external markers; require an empty `errors` array.

### Task 5: Decide whether a Git snapshot is authorized

**Files:**
- Review only: `git status --short`, `git diff --stat`, and the final posture receipt.

- [ ] Present the exact snapshot scope to the author before staging anything.
- [ ] Create no commit, tag, or snapshot unless the author explicitly authorizes that exact scope.
- [ ] If authorized, stage only the listed files, run `git diff --cached --check`, and report the resulting commit identifier; otherwise leave the worktree unchanged.

## Success Criteria

- Every externally closed marker has a dated, inspectable evidence record.
- Unsupported markers remain visible and open.
- The regenerated package has no final-gate errors and no release-safety blockers.
- RC-1 and RC-2 statuses are unchanged; RCEP F3 remains `not_identified`.
- No scientific experiment is rerun and no unauthorized Git snapshot is created.

## Self-Review Checklist

- [ ] No task infers external evidence from local build success.
- [ ] No task changes scientific numbers or quarantine status.
- [ ] Every generated artifact is rebuilt before final gate evaluation.
- [ ] The plan contains exact files, commands, expected outcomes, and an explicit authorization boundary.
