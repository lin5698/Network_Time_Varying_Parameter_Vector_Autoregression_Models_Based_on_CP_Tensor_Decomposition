# P3 Downstream Rebuild Blocked Receipt V1

Date: 2026-08-29

## Completed stages

- Evidence build completed successfully.
- Manuscript build, PDF/DOCX generation, package finalization, and figure-source package completed successfully.
- Reviewer archive completed after adding the four current controlled-template context keys to `scripts/build_natcs_reviewer_archive.mjs`.
- Submission materials and upload-freeze manifest completed successfully.

## Blocking gate result

`make natcs-final-gate-check` failed under the repository fail-closed policy with 218 passes and one release-safety warning. A standalone release-safety audit reported `blockers=0`, `warnings=1`, `files_seen=425`, `text_files_scanned=355`, and `binary_files_skipped=70`.

The warning is a private absolute-path pattern in:

`output/reviewer_archive/natcs_reviewer_archive/code/scripts/experiments/test_analyze_cal_e02_128.py`

The generated submission materials also retain open author/checklist markers. No marker was closed automatically.

## Disposition

- Build gate: `BLOCKED_BY_WARNING`
- Promotion authorization: unchanged (`NOT_GRANTED`)
- Empirical claim activation: unchanged (`NOT_ACTIVATED`)
- Upload-freeze conclusion: not issued
- Scientific rerun: not performed

Next action requires an explicitly authorized archive sanitization change, followed by regeneration of the reviewer archive and all downstream package checks.
