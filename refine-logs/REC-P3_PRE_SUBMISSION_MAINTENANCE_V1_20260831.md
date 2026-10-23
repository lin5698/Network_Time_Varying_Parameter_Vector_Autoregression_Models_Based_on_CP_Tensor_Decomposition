# REC-P3 Pre-Submission Maintenance V1

- Date: 2026-08-31
- Scope: Rebuild and validate the current NatCS submission package before external decisions are available.
- Scientific experiments rerun: No
- Git snapshot created: No

## Rebuild

The following targets completed successfully, in order:

1. `make natcs-evidence`
2. `make natcs-manuscript`
3. `make natcs-reviewer-archive`
4. `make natcs-submission-materials`
5. `make natcs-upload-freeze-manifest`

Generated package facts:

- Submission inventory: 27 items
- Upload freeze manifest: 11 artifacts
- Reviewer archive: 342 files

## Verification

- `node scripts/check_natcs_final_gates.mjs`: `PASS_WITH_WARNINGS_ALLOWED`, 225 passes, 0 errors
- `node scripts/audit_natcs_release_safety.mjs --check`: 0 blockers, 0 warnings; 425 files seen, 355 text files scanned, 70 binary files skipped
- Focused NatCS regression suite: 8 tests passed, 0 failed
- `git diff --check`: passed

## Open external gates

- Final author decision sheet: 4 open markers
- Fig. 2 portal preview: 5 open markers; no portal observation recorded
- Raw-source access: 42 open markers; no author sign-off recorded
- Public-release readiness: 25 open markers; no repository, DOI, licence or access-term record assigned

Current release posture remains `RC-1 = ACTIVATED`, `RC-2 = ACTIVATED_WITH_LIMITATIONS`, and `RCEP F3 = not_identified`. This receipt records local package maintenance only and does not close any external gate.
