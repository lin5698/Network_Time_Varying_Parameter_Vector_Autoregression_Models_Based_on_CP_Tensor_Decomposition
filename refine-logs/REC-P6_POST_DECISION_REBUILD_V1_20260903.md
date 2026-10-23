# REC-P6 Post-Decision Rebuild V1

- Date: 2026-09-03
- Scope: Reconcile the Fig. 2 portal-preview checklist with the controlling RC-1/RC-2 decision posture, then rebuild and verify the generated NatCS package.
- Scientific experiments rerun: No
- External markers closed: No
- Git snapshot created: No

## Source change

`manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md` now records `RC-1 = ACTIVATED` and `RC-2 = ACTIVATED_WITH_LIMITATIONS`, including the current `RCEP F3 = not_identified` limitation. The checklist remains disabled, all four portal-preview rows remain `Not checked`, and no portal observation was inferred.

## Verification sequence

The focused suite passed 8/8. The complete chain then ran successfully:

1. `make natcs-evidence`
2. `make natcs-manuscript`
3. `make natcs-reviewer-archive`
4. `make natcs-submission-materials`
5. `make natcs-upload-freeze-manifest`

Final non-mutating checks:

- Final gate: `PASS_WITH_WARNINGS_ALLOWED`; 225 passes, 0 errors.
- Release safety: 0 blockers, 0 warnings; 425 files scanned.
- `git diff --check`: passed.
- Submission inventory: 27 submission-material entries.
- Upload freeze manifest: 11 artifacts.
- Reviewer archive: 342 files.
- Packaged Fig. 2 portal-preview checklist matches its authored source byte-for-byte.

## Remaining external gates

- Final author decision: 4 open markers.
- Fig. 2 portal preview: 5 open markers.
- Raw-source access: 42 open markers.
- Public-release readiness: 25 open markers.

This record establishes local package integrity after the checklist status correction. It does not authorize portal upload, close an author-controlled decision, infer portal acceptance, or authorize a Git snapshot.
