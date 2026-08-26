# Production Scientific Authorization Candidate Decision

Date: 2026-07-19  
Authorization source: explicit workspace-author instruction in the active Codex task

## Authorized Candidate Scope

Two dataset-specific schema-v1 candidates are generated because the production
runner requires one manifest per dataset:

- `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_RCEP_20260719.json`
  - SHA-256: `04eb83670e0648d8e42e0194fcb3795499c296363ae91b6dc8e94fd2d7f14d84`
- `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_NYC_20260719.json`
  - SHA-256: `4155bbed29b18be0fcd6d7c052439e26e946fcc37c47f6170862a1a0c3a8bd5d`

Each candidate binds one invocation of `scripts/run_cp_empirical_pipeline.py`
with `window=40`, `p=2`, `n_boot=500`, `block_size=4`, `cp_inits=6`,
`cp_max_iter=100` and `cp_tol=1e-6`.

The RCEP candidate binds the author-approved C3 helper checkout, installed
schema-v2 trust manifest and the two exact CSV files selected by the runner's
local-first input contract. The NYC candidate binds the verified
`datasets/NYC-taxi` directory and frozen upstream commit.

## Explicit Exclusions

This candidate decision does not authorize:

- R006e or R006f outcome execution or inspection;
- downstream evidence or manuscript builds;
- promotion of quarantine outputs into manuscript evidence;
- overwrite or reuse of an existing output directory;
- a second invocation under either decision ID.

Every output must remain quarantined until its inventory and SHA-256 closure
are frozen and an independent result/claim audit is complete.

## Activation Boundary

These are completed candidates, not yet executable approvals. The production
contract additionally requires the workspace author to approve the exact
SHA-256 of each completed candidate. Until that separate hash approval is
recorded, no command may pass either candidate to the production runner and no
scientific output root may be created.
