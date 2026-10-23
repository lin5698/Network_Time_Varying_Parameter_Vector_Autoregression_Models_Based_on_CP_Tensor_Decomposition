# REC-P5 Submission Readiness Review V1

- Date: 2026-08-31
- Scope: Local submission-readiness review after the current NatCS package rebuild.
- Scientific experiments rerun: No
- Git snapshot created: No

## Rebuild and package evidence

The package was rebuilt in the required order, with the downstream submission-materials and freeze steps rerun when the manifest files were found absent:

1. `make natcs-evidence`
2. `make natcs-manuscript`
3. `make natcs-reviewer-archive`
4. `make natcs-submission-materials`
5. `make natcs-upload-freeze-manifest`

Current package evidence:

- `submission_inventory.json`: 27-key schema; all inventory paths exist.
- Upload freeze manifest: 11 artifacts.
- Reviewer archive: 342 files.
- Main manuscript and supplementary PDF/DOCX/TeX files share modification time `2026-08-31T00:33:38+0800`.
- Figure source ZIP, reviewer archive ZIP, inventory, freeze manifest, cover letter, metadata, declarations and references are present and routed by the inventory/manifest.
- `natcs_final_author_decision_sheet.md` is copied into the submission materials as the upload-day entry point; the four external marker groups remain visible.

## Verification

- `node scripts/check_natcs_final_gates.mjs`: `PASS_WITH_WARNINGS_ALLOWED`, 225 passes, 0 errors.
- `node scripts/audit_natcs_release_safety.mjs --check`: 0 blockers, 0 warnings; 425 files scanned.
- Focused NatCS regression suite: 8 passed, 0 failed.
- `git diff --check`: passed.
- Release-safety and package routing checks found no credentials, private paths, restricted raw files, unsupported DOI/licence claims, or hidden experimental outputs in the upload package.

## Open external gates and scientific posture

- Final author decision sheet: 4 open markers.
- Fig. 2 portal preview: 5 open markers; no portal observation recorded.
- Raw-source access: 42 open markers; no author sign-off recorded.
- Public-release readiness: 25 open markers; no repository, DOI, licence or access-term record assigned.

Release posture remains `RC-1 = ACTIVATED`, `RC-2 = ACTIVATED_WITH_LIMITATIONS`, and `RCEP F3 = not_identified`. This receipt confirms local readiness checks only; it does not close author-controlled or portal-controlled gates.
