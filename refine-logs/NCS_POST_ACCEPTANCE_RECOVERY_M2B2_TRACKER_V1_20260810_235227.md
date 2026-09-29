# REC-M2B2 Preflight Tracker

Overall status: **REC-M2B2 PASS / REC-M2 BLOCKED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE**

Independent preflight acceptance remains required. This tracker records an authorization and validator repair only; it is not evidence that scientific M2 ran.

## Versioned Records

| Record | Raw SHA-256 | Status |
|---|---|---|
| `NCS_POST_ACCEPTANCE_RECOVERY_M2B2_EXECUTION_AUTHORIZATION_V1_20260810_235227.json` | `c012f7d1a40168b264027c55a3760424c7686cd0e7941cf6765d99c2629fd63f` | `PLANNED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE` |
| `NCS_POST_ACCEPTANCE_RECOVERY_M2B2_PREFLIGHT_RECEIPT_V1_20260810_235227.json` | `9c9ed70253aed3aba2be3a348727e89ba4efde16d19fa09c6e9e0e0db535d583` | `REC-M2B2_PASS` |

The historic M2B1/v1 records remain unchanged. Their preserved status is `REC-M2B PASS / REC-M2 BLOCKED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE`.

## Checks

| Check | Result | Evidence |
|---|---|---|
| Shared four-artifact primary continuation | PASS | Four validators accepted sequential primary roots while the validator itself made no writes; committed-root state was then represented in temporary fixtures. |
| Shared four-artifact duplicate continuation | PASS | Four validators accepted sequential duplicate roots after a complete primary directory. |
| State and path refusal | PASS | Unknown/malformed siblings, duplicate-before-primary, root reuse, third run, symlink/non-directory children, wrong roots, traversal, E4-r008, and out-of-layout paths are rejected. |
| Authorization binding | PASS | M2B2 schema binds source authorization-v2, M2A receipt, formal register and four canonical items, five E4-r3 leaves, workspace chain, and final bytes/SHA for exactly eight files. |
| Fresh compile | PASS | `python3 -m py_compile` over exactly eight allowed files; exit code 0. |
| Fresh tests | PASS | 35 tests: CAL-E01 16, CAL-E02:128 7, CAL-E02:135 6, CAL-E03:164 6; all exit code 0. |
| Actual authorization check | PASS | Four read-only wrapper validations accepted the actual M2B2 authorization; no permanent write. |
| Planned parent | PASS | `refine-logs/ncs_new_analysis_v2/rec-m2b2-20260810-235227-cst-01` absent before and after verification. |
| Protected trees and records | PASS | Manuscript tree 72 files, E4 candidate tree 11 files, E4 quarantine tree 3 files, formal register, workspace authorization, terminal inventory, and historic M2B1 records unchanged. |
| Scientific execution | BLOCKED | No real analyzer CLI, scientific analysis, scientific output, claim activation, or promotion occurred. |

## Boundaries

The permitted run IDs are only `primary` and `duplicate`. Each run permits one strict content-addressed root per analyzer: CAL-E01:75, CAL-E02:128, CAL-E02:135, and CAL-E03:164. The duplicate run requires all four primary roots. Unknown children, malformed names, path traversal, symlinks, root reuse, E4-r008 paths, and writes outside the authorized layout are prohibited.

The source authorization-v2 status remains exactly `current_task_limits.m2_scientific_analysis = BLOCKED_IN_THIS_TASK`. Claims, promotion, RCEP/NYC, S1-S4, and N=100/N=200 remain unauthorized; CAL-E03 N=100/N=200 remain `NOT_RUN/ABSTAIN`.

## Non-Mutations

- `manuscript_src/natcs` was not modified by REC-M2B2.
- The E4-r3 candidate, quarantine, workspace authorization, and terminal inventory were not modified.
- The formal author-decision register was not modified.
- Existing `e4_r008` outputs were not used, reused, compared, or modified.
- The planned output parent and all analyzer roots were not created.

Receipt: `NCS_POST_ACCEPTANCE_RECOVERY_M2B2_PREFLIGHT_RECEIPT_V1_20260810_235227.json`

REC-M2 remains **BLOCKED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE**.
