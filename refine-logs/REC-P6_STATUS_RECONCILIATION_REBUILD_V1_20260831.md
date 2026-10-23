# REC-P6 Status Reconciliation Rebuild V1

- Date: 2026-08-31
- Scope: Reconcile historical RC-1/RC-2 dependency-register wording with the current controlling posture, then rebuild and verify the generated NatCS package.
- Scientific experiments rerun: No
- External markers closed: No
- Git snapshot created: No

## Source change

`manuscript_src/natcs/submission_external_dependency_register.md` now states that its 2026-08-26 `RC-1 = NOT_GRANTED` and `POTENTIAL_ONLY_NOT_ACTIVATED` rows are retained as historical context. The current controlling posture is separately visible as `RC-1 = ACTIVATED`, `RC-2 = ACTIVATED_WITH_LIMITATIONS`, and `RCEP F3 = not_identified`. The historical rows were not rewritten, and no portal observation was inferred.

## Verification sequence

The focused suite passed 8/8. During package inspection, the workflow confirmed that `tests/test_natcs_release_gate.mjs` invokes the evidence and manuscript builders and therefore recreates the submission package. The long-term plan was corrected so focused tests run before the final rebuild.

After the tests, the complete chain ran successfully:

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
- Packaged dependency register: byte-identical to its authored source.

## Remaining external gates

- Final author decision: 4 open markers.
- Fig. 2 portal preview: 5 open markers.
- Raw-source access: 42 open markers.
- Public-release readiness: 25 open markers.

This record establishes local package integrity after the status wording correction. It does not authorize portal upload, close an author-controlled decision, or authorize a Git snapshot.
