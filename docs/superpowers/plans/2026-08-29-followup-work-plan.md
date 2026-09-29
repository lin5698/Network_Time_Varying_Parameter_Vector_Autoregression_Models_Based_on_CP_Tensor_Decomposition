# Post-Wave-B Closure and Submission Readiness Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Each task is gated by the preceding authorization and review result.

**Goal:** Close the remaining audit and authorization gaps after Wave B, then produce a reproducible manuscript/submission package without activating unsupported empirical claims.

**Architecture:** Keep the current fail-closed governance model. Treat audit records, authorization records, source manuscript files, generated evidence, and submission materials as separate state transitions. No quarantined value enters active manuscript sources until the author grants explicit promotion and claim-activation authority, and every generated package receives an independent post-regeneration review.

**Tech Stack:** Git, JSON/Markdown audit receipts, Node.js build scripts, Python empirical pipeline, and the repository test suite.

---

## Current Baseline

- Working tree: clean on `codex/m5-current-luna-science-recheck`.
- `git fsck --full`: passes; no dataless placeholder files detected.
- `EMPIRICAL_IMPLEMENTATION_AUDIT.json`: `PASS` for the downstream rebuild gate only.
- `PAPER_CLAIM_AUDIT.json`: `PASS` for no active stale citations; it does not grant promotion.
- `PROOF_AUDIT.json`: scoped source-only `PASS`.
- Wave B NYC and RCEP receipts exist and report reproducible outputs.
- Open conditions remain: RC-1 manuscript-promotion authorization, RC-2 empirical claim activation, RC-3 post-regeneration independent review.
- Open characterization flags remain explicitly blocking activation of affected fragments: RCEP F1/F2/F3 and the listed NYC characterization flags.
- `EXPERIMENT_AUDIT.md` is a historical overall `FAIL`; its relationship to the newer P3 adjudications must be made explicit before any release summary is written.

## Success Criteria

1. Historical and current audit records have an explicit, non-contradictory status map.
2. The author has recorded separate decisions for promotion, each open characterization flag, and claim activation scope.
3. The authorized rebuild produces a clean evidence, manuscript, reviewer-archive, figure-source, submission-materials, and upload-freeze package.
4. Final gates and an independent post-regeneration review report no open `FATAL` or `CRITICAL` issue.
5. Any unresolved characterization remains visibly fenced and is not represented as an activated empirical claim.

### Task 1: Reconcile the audit status map

**Files:**
- Review: `EMPIRICAL_IMPLEMENTATION_AUDIT.md`, `EMPIRICAL_IMPLEMENTATION_AUDIT.json`, `PAPER_CLAIM_AUDIT.md`, `PAPER_CLAIM_AUDIT.json`
- Review: `EXPERIMENT_AUDIT.md`, `EXPERIMENT_AUDIT.json`
- Create: `refine-logs/REC-STATUS_RECONCILIATION_V1_20260829.md`
- Create: `refine-logs/REC-STATUS_RECONCILIATION_V1_20260829.json`

- [ ] Record that the historical experiment audit remains `FAIL` for its original scope, while the P3 re-adjudications release only the downstream rebuild gate.
- [ ] Preserve the original audit files and reason codes; do not silently flip the historical `FAIL` to `PASS`.
- [ ] Add a table mapping each gate to scope, controlling artifact, current verdict, and remaining condition.
- [ ] Verify all referenced JSON paths and verdict strings with `jq` before recording the receipt.
- [ ] Commit only the status-reconciliation records and explicitly authorized audit wording.

Run:

```bash
jq -e '.verdict == "PASS"' EMPIRICAL_IMPLEMENTATION_AUDIT.json
jq -e '.verdict == "PASS"' PAPER_CLAIM_AUDIT.json
jq -e '.verdict == "PASS"' PROOF_AUDIT.json
git diff --check
```

Expected: all three scoped checks succeed and the diff has no whitespace errors.

### Task 2: Close the author-decision queue

**Files:**
- Review: `refine-logs/REC-P2_D1D2D3_DECISION_CLOSURE_V1_20260825.md`
- Review: `refine-logs/REC-P3S8_WAVE_B_RCEP_METHOD_REMEDIATION_20260827_011000.md`
- Review: `refine-logs/REC-P3S7_WAVE_B_NYC_INFRA_VALIDATION_20260827_001700.md`
- Create: `refine-logs/REC-P3_PROMOTION_AND_CHARACTERIZATION_DECISION_V1_20260829.md`
- Create: `refine-logs/REC-P3_PROMOTION_AND_CHARACTERIZATION_DECISION_V1_20260829.json`

- [ ] Obtain an explicit author decision on RC-1: whether any Wave B value, figure, or claim fragment may enter manuscript sources.
- [ ] For each RCEP and NYC flag, record one of: resolve with evidence, accept as a stated limitation, or keep blocked.
- [ ] Keep RCEP F3 as `not_identified` unless the author authorizes a new pre-declared design and rerun; do not reinterpret it as a positive result.
- [ ] Keep E4-R006/E4-R007 decisions separate from P3 application decisions; no empirical activation follows automatically from a downstream-build authorization.
- [ ] Require a new authorization record if the decision changes any frozen input, source text, estimator, or scientific output.

### Task 3: Prepare and execute the authorized downstream rebuild

**Files:**
- Read-only inputs: `scripts/build_natcs_evidence.mjs`, `scripts/build_natcs_manuscript.mjs`, `scripts/finalize_natcs_package.mjs`, `scripts/create_natcs_figure_source_package.mjs`, `scripts/build_natcs_reviewer_archive.mjs`, `scripts/finalize_natcs_submission_materials.mjs`, `scripts/create_natcs_upload_freeze_manifest.mjs`
- Generated outputs: `output/natcs_evidence/`, `output/03_submission_materials/`, `output/04_reviewer_archive/`, `output/05_upload_freeze/`
- Create: `refine-logs/REC-P3_DOWNSTREAM_REBUILD_V1_20260829.md`
- Create: `refine-logs/REC-P3_DOWNSTREAM_REBUILD_V1_20260829.json`

- [ ] Before running, verify the author authorization ID, current `HEAD`, all input file sizes, and the frozen Wave B inventory records.
- [ ] Run the commands in dependency order; stop on the first non-zero exit:

```bash
make natcs-evidence
make natcs-manuscript
make natcs-reviewer-archive
make natcs-submission-materials
make natcs-upload-freeze-manifest
```

- [ ] Run `make natcs-final-gate-check` and `make natcs-release-safety-audit`.
- [ ] Record exact command results, generated paths, authorization ID, and current Git commit in the rebuild receipt.
- [ ] Do not delete stale or quarantined artifacts as part of the rebuild; preserve them for provenance and auditability.

### Task 4: Independent post-regeneration review

**Files:**
- Review: all generated files from Task 3
- Review: `tests/` gate and alignment tests
- Create: `refine-logs/REC-P3_POST_REGENERATION_REVIEW_V1_20260829.md`
- Create: `refine-logs/REC-P3_POST_REGENERATION_REVIEW_V1_20260829.json`

- [ ] Check that every active manuscript numeric value resolves to an evidence object in the rebuilt package.
- [ ] Check that inactive markers and `POTENTIAL_ONLY_NOT_ACTIVATED` fences remain intact where authorization is absent.
- [ ] Run focused checks first, then the complete repository gate suite:

```bash
python3 -m pytest tests/test_cp_pipeline_contracts.py tests/test_cp_rank_selection.py
node tests/test_empirical_results_numeric_alignment.mjs
node tests/test_natcs_controlled_benchmark_contract.mjs
node tests/test_natcs_release_gate.mjs
make natcs-final-gate-check
```

- [ ] Classify every finding as `PASS`, `WARN`, `FATAL`, or `CRITICAL`; do not downgrade a failed gate by narrative explanation.
- [ ] If any `FATAL` or `CRITICAL` issue appears, stop release preparation, create a remediation record, and do not issue an upload-freeze conclusion.

### Task 5: Decide release posture and snapshot the result

**Files:**
- Create: `refine-logs/REC-P3_RELEASE_POSTURE_V1_20260829.md`
- Create: `refine-logs/REC-P3_RELEASE_POSTURE_V1_20260829.json`
- Review: `MANIFEST.md`, `README.md`, `NCS_STRATEGY_REVIEW_20260716.md`

- [ ] If Task 4 passes and RC-1/RC-2 are authorized, record the exact activated claim set and its operating boundaries.
- [ ] If RC-1 or RC-2 remains open, record `BUILD_COMPLETE_BUT_PROMOTION_BLOCKED`; do not describe the package as submission-ready.
- [ ] Record unresolved flags and their affected fragments in the release posture receipt.
- [ ] Create a Git snapshot commit only after the author authorizes the snapshot; include audit receipts and generated-manifest references, not unrelated ignored outputs.
- [ ] Re-run `git status --short --branch`, `git fsck --full --no-progress`, and `git diff --check` after the snapshot.

## Explicit Non-Goals

- Do not activate RCEP/NYC empirical claims without separate author authorization.
- Do not rewrite or delete historical `EXPERIMENT_AUDIT` records merely to make top-level statuses look uniform.
- Do not rerun scientific experiments unless a new pre-outcome authorization and protocol are issued.
- Do not resolve conflict copies or dangling Git objects in this plan; those are separate archival-maintenance work.
- Do not claim Nature Computational Science submission readiness until RC-3 is independently closed.

## Dependency Order

```text
Task 1 status reconciliation
        |
        v
Task 2 author decisions
        |
        v
Task 3 authorized downstream rebuild
        |
        v
Task 4 independent post-regeneration review
        |
        v
Task 5 release posture and optional snapshot
```

No task may bypass a missing authorization or convert a `NOT_GRANTED` condition into an implicit approval.
