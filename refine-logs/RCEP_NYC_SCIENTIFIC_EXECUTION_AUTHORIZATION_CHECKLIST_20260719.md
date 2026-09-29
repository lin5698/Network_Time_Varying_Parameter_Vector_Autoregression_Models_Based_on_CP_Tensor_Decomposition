# RCEP/NYC Scientific Execution Authorization Checklist

Date: 2026-07-19

Current state: **NYC COMPLETED IN QUARANTINE; RCEP-02 FAILED AFTER ESTIMATION; PARTIAL QUARANTINES FROZEN**

Pending replacement: **RCEP-02 CLOSED AFTER ONE FAILED INVOCATION; NEW IMPLEMENTATION AUTHORIZATION REQUIRED**

## Static Closures

- The author-approved C3 helper trust manifest is installed and statically validated.
- The NYC source checkout is bound to its frozen upstream commit.
- The runner requires a separate authorization file, its separately approved SHA-256 and all seven explicit numeric CLI arguments before helper loading, authorized dataset reads, scientific calls or scientific output-tree creation.
- NYC no longer depends on the RCEP helper gate.
- RCEP authorization binds the two CSV byte identities selected by the runner's frozen filename/fallback contract; this selection is not attributed to helper configuration.
- The authorization, RCEP helper manifest/source files, RCEP CSVs and NYC NPZs are parsed or executed only from verified in-memory snapshots read through no-follow descriptors. NYC expected file hashes are derived from the frozen commit blobs rather than worktree status alone. The constrained helper loader rejects relative imports, dynamic code/import controls (including `runpy`), import-path mutation and module resolution outside the verified helper modules or the invoking interpreter's standard-library and installed-package roots; lazy calls reinstall the runtime import guard, and the verified helper bytes remain the explicit trust root rather than untrusted sandbox input.
- The current helper/NYC checkout and dataset-specific input identities are verified before the quarantine output tree is reserved; cached helper use must reproduce the current authorized checkout identity.
- Outputs are reserved in a new no-follow quarantine tree; every output file is exclusively created against the registered parent-directory identity, so overwrite, child symlinks, parent replacement and directory reuse are denied.
- R006e/R006f outcomes, downstream evidence builds and manuscript promotion remain excluded.

Static runtime boundary: Python dependency imports and configured Matplotlib/XDG cache-directory initialization occur before the authorization gate. They are not scientific data access or outcome execution. The current proof therefore does not claim a side-effect-free interpreter bootstrap; it claims refusal before helper loading, authorized dataset reads, estimator/statistical/GIRF calls and scientific output-tree creation.

## Completed Candidate Bindings

One completed manifest has been generated for each dataset. Each candidate states:

1. `dataset`: exactly `rcep` or `nyc_taxi`;
2. all seven numeric arguments, with no reliance on implicit defaults;
3. final implementation hashes after code freeze;
4. exact dataset-specific input paths and identities;
5. a unique decision ID and new absolute quarantine output root;
6. authorizer identity and authorization time;
7. the exact completed manifest SHA-256 approved for execution.

For RCEP, the original candidate bound the C3 checkout and the two
provider-governed CSV inputs selected from `repo/data`. Its SHA-256 was
`04eb83670e0648d8e42e0194fcb3795499c296363ae91b6dc8e94fd2d7f14d84`.
The remediated RCEP-02 candidate bound the same inputs with runner SHA-256
`dea5621e6fe2b300d22ac083087720ef8c2dd1dd53496a89538e2a9b8ff8d8ad` and
candidate SHA-256
`c06b34c44081a390d0ea277db8c80640ccd7e0737b6dc0fc83f1ddc255f47fbc`.

For NYC, the candidate binds the verified source path, frozen commit, explicit
parameters and new quarantine output root. Its SHA-256 is
`4155bbed29b18be0fcd6d7c052439e26e946fcc37c47f6170862a1a0c3a8bd5d`.

The workspace author approved both exact SHA-256 values for one production
invocation per dataset. The approvals remain limited to the bound input,
parameters and quarantine output roots. R006e/R006f outcomes, downstream
builds and manuscript promotion remain unauthorized.

## Pre-Activation Record

The exact completed candidate SHA-256 values were separately approved at
2026-07-19T03:13:04Z. The approval record is
`PRODUCTION_SCIENTIFIC_AUTHORIZATION_APPROVAL_20260719.md`.

## Execution Record

- The original RCEP candidate exited with code 1 during verified helper source
  execution because the constrained import guard rejected installed `pandas`.
  It was fixture-remediated and not retried.
- RCEP-02 exited with code 1 after estimation/bootstrap and partial figure/table
  publication. `PanelOLS` rejected a stability-exclusion regression because the
  filtered exogenous design was rank deficient. Its 31-file quarantine is
  frozen in `PSA_RCEP_02_OUTPUT_INVENTORY_20260719.json`; no value review, claim
  audit or promotion was performed. No retry or output reuse is permitted.
- NYC Taxi exited with code 0. Its 18 output files remain under the authorized
  quarantine root. Only file names, sizes and SHA-256 values were frozen; no
  value review, claim audit, downstream build or manuscript promotion was
  performed.
- The original decision IDs are closed. Any RCEP remediation changes the bound
  implementation hash and therefore requires a new candidate and new exact
  SHA-256 approval.

The remediated RCEP-02 candidate was
`SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_RCEP_02_20260719.json`, SHA-256
`c06b34c44081a390d0ea277db8c80640ccd7e0737b6dc0fc83f1ddc255f47fbc`.
It binds runner SHA-256
`dea5621e6fe2b300d22ac083087720ef8c2dd1dd53496a89538e2a9b8ff8d8ad`,
decision ID `psa-20260719-rcep-02` and a new absent quarantine output root.
The workspace author approved its exact SHA-256 for one invocation. That
decision is now consumed and closed after the failed partial run. Fixing the
rank-deficient regression requires a new implementation hash and a new exact
SHA-256 authorization.

RCEP and NYC data were read only under their approved candidates. No R006e/R006f
outcome was inspected or executed, and no downstream build or manuscript
promotion was performed.

Tasks 6-9 of the R006e screening-v2 governance plan remain complete only at the implementation and outcome-free construction-freeze level. Their production screening and outcome stages remain separately unauthorized and are not covered by this checklist.
