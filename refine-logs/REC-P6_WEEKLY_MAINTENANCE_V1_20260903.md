# REC-P6 Weekly Maintenance V1

- Date: 2026-09-03
- Scope: NatCS weekly maintenance checkpoint under `docs/superpowers/plans/2026-09-03-next-phase-operational-plan.md` Task 1.
- Scientific experiments rerun: No
- External markers closed: No
- Git snapshot created: No
- Outcome: `PASS_WITH_FOLLOW_UP`

## Evidence check

No new dated author reply, journal-portal screenshot or observation, raw-source licence/access record, repository assignment, DOI record, or public-release decision was found in the four gate worksheets or `refine-logs` after the 2026-08-31 controlling rebuild. A filesystem timestamp scan is recorded only as a maintenance observation; it is not treated as external evidence.

The four external gate groups therefore remain open:

- Final author decision: 4 markers
- Fig. 2 portal preview: 5 markers
- Raw-source access: 42 markers
- Public-release readiness: 25 markers

## Verification

- `node scripts/check_natcs_final_gates.mjs`: `PASS_WITH_WARNINGS_ALLOWED`; 225 passes, 0 errors; the four known external-marker warnings remain.
- `node scripts/audit_natcs_release_safety.mjs --check`: 0 blockers, 0 warnings; 425 files scanned, 355 text files scanned, 70 binary files skipped.
- `git diff --check`: passed.

## Confirmed maintenance finding

The current controlling author decision sheet records `RC-1 = ACTIVATED` and `RC-2 = ACTIVATED_WITH_LIMITATIONS` (`manuscript_src/natcs/natcs_final_author_decision_sheet.md:10-11`). The Fig. 2 portal checklist still describes manuscript promotion as `NOT_GRANTED` and empirical activation as gated (`manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md:9-10`), while its four preview rows correctly remain `Not checked` because no real portal observation exists (`:19-22`).

This is a confirmed documentation-consistency defect, not evidence that the Fig. 2 portal gate has passed. The checklist must be reconciled with the current RC-1/RC-2 posture while preserving the no-observation boundary and all four open preview rows.

## Minimal follow-up

At the next authorized source edit, update only the explanatory Fig. 2 checklist wording to reflect the current limited activation posture. Do not close any preview row or infer portal acceptance. After that source edit, run the complete Task 4 focused-suite/build/final-gate sequence and create the corresponding rebuild receipt.

The package remains in readiness maintenance. No upload, repository/DOI claim, raw-source access claim, or Git snapshot is authorized by this receipt.
