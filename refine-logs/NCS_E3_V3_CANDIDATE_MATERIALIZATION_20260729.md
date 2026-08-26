# NCS E3 v3 Candidate Materialization

Date: 2026-07-29

Status: `CANDIDATE_READY_NOT_AUTHORIZED`. This record materializes a new E3
Family-2 v3 execution candidate and reports its static verification. It does
not authorize scientific execution, does not create a quarantine output root,
does not alter either controlling audit, and does not promote any manuscript
claim.

## Candidate Identity

- Candidate ID: `e3-family2-synthetic-v3-20260729-recursive-bootstrap`
- Candidate path: `refine-logs/e3_family2_candidates/e3-family2-synthetic-v3-20260729-recursive-bootstrap/candidate.json`
- Candidate SHA-256: `aa4384ca7cc7efd0dcdcfb92b2ab923bc02ee8457ffb039bdcdfcfcd8e2a137e`
- Schema version: `e3-family2-execution-candidate-v3`
- Bound source-only gate-test receipt: `refine-logs/e3_family2_inputs/e3-authorization-gate-test-receipt-v3-20260729.json`
- Gate-test receipt SHA-256: `9164ea8234d19c0eec01951c065ab4ae79d761e8deb27e519d96db1c55973cd9`
- Bound, new quarantine output root: `refine-logs/e3_family2_quarantine/e3-family2-synthetic-v3-20260729-recursive-bootstrap-quarantine`

The quarantine root was verified absent before and after materialization and
remains absent as of this record. It has not been created.

This is a **new** candidate identity distinct from every historical
candidate. It does not reuse or relabel the v1 candidate
(`e3-family2-synthetic-v1-20260723-run1`) or any of the three v2 candidates
(`bootstrap-history-gate`, `bootstrap-history-binding-gate`,
`bootstrap-history-closure`). It binds the v3 recursive-bootstrap
specification (`synthetic-e3-v3.json`) exclusively, per the frozen-boundary
rule in `NCS_E3_V3_RECURSIVE_BOOTSTRAP_CANDIDATE_READINESS_20260726.md`.

## How It Was Built

The candidate was materialized by calling the existing, already-reviewed
`scripts/experiments/e3_family2_candidate_package.build_candidate_ready_package`
function with a fresh candidate ID, a fresh gate-test receipt (recomputed
directly from `build_authorization_gate_test_receipt()` against the current
source tree), and a new, absent, `quarantine`-labelled output root path. No
source file was modified to do this; the candidate-package builder already
existed and had simply never been invoked for a v3 identity.

## Static Checks Passed

All checks below were run directly against the on-disk candidate bytes, not
against an in-memory object, and all passed:

1. Candidate SHA-256 matches the bytes on disk.
2. `_validate_execution_candidate_shape` — schema version, execution scope,
   and prohibition list are exact.
3. `_validate_source_hashes` — the nine bound source files (core, executor,
   preoutcome, candidate-package, candidate-ready, artifact-schemas, and the
   five fixture-test files) match their current on-disk SHA-256 values.
4. `_validate_dependency_hashes` — the dependency-lock file matches.
5. `_validate_preoutcome_artifacts` — all eight `CANDIDATE_READY` artifacts
   validate against their schemas and hash-match the candidate binding.
6. `_validate_synthetic_inputs` — the bound `synthetic-e3-v3.json` matches the
   frozen specification SHA-256
   (`53e496ff708f2b5d7b0dbcc258483920b8029b856aee307df5032899740ee450`).
7. `_validate_configuration` — the candidate's execution configuration
   matches the specification's scales `[20, 50]`, horizons `[4, 12]`, and
   panel seeds `4101`-`4120`.
8. `_validate_bootstrap_history_bindings` — the v3 recursive-bootstrap
   procedure (`recursive_residual_circular_moving_block_bootstrap`,
   pseudo-response lag rebuilding, per-replicate retuning over ranks
   `[1, 2, 3]`, full failure retention) and the rank-aware minimum-history
   gate (`{"1": 14, "2": 14, "3": 15}`, minimum 2 valid refit opportunities
   per rank) are bound identically in the specification, the candidate
   configuration, and the `tuning_split_manifest` artifact.
9. `_validate_new_quarantine_root` — the bound quarantine root is absolute,
   labelled `quarantine`, and does not exist.

## Negative-Path Verification

A direct call to `prepare_authorized_execution` with the correct candidate
path and SHA-256 but **no** authorization file was made to confirm the
executor still refuses before any scientific code runs:

```text
Refused as expected: AuthorizationError: execution authorization and its
exact SHA-256 are required
quarantine root exists (must remain False): False
```

The quarantine root remained absent after the refusal, confirming the
executor's precondition ordering (authorization check before any output-root
reservation) still holds for this new candidate.

## Fixture Suite

The full fixture-only suite was re-run after materialization to confirm no
regression:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts.experiments.test_e3_synthetic_core scripts.experiments.test_e3_family2_synthetic_runner scripts.experiments.test_e3_family2_preoutcome scripts.experiments.test_e3_family2_candidate_package scripts.experiments.test_e3_family2_authorized_executor
Ran 64 tests in 2.204s
OK
```

## What This Does Not Do

- Does not run `make_synthetic_panel`, any estimator fit, or any response
  evaluation.
- Does not create, reserve, or write to a quarantine output root.
- Does not create, read, or reference an authorization JSON.
- Does not change `PAPER_CLAIM_AUDIT` (`BLOCKED`) or
  `EMPIRICAL_IMPLEMENTATION_AUDIT` (`FAIL`).
- Does not change any status in `refine-logs/NCS_E3_EVIDENCE_TRACKER.md`;
  E3-1 through E3-4 remain `NOT_AUTHORIZED` and E3-5 remains `BLOCKED`.
- Does not access RCEP, NYC, R006e, or R006f routes; the candidate's
  `excluded_routes` field is unchanged from the frozen list.
- Does not build, promote, or otherwise touch the manuscript.

## Next Gate

Per `NCS_E3_V3_RECURSIVE_BOOTSTRAP_CANDIDATE_READINESS_20260726.md`, "Remaining
Gates Before Any Scientific Execution", this record closes gate 2
("materialize a new v3 candidate in a new directory and record its exact
SHA-256 without reusing a historical candidate or authorization").

Gate 3 ("bind deployment-owned production trust evidence and a new absent
quarantine output root") is partially satisfied: the quarantine root is bound
and confirmed absent, but `trust_evidence.detached_signature` remains
`"PENDING"` in the candidate document, and no deployment-owned production
trust evidence has been supplied.

Gate 4 ("obtain a new exact, single-use scientific authorization for that
candidate") requires an explicit decision by the workspace author binding the
exact candidate SHA-256 above (`aa4384ca7cc7efd0dcdcfb92b2ab923bc02ee8457ffb039bdcdfcfcd8e2a137e`)
for exactly one invocation at the bound quarantine root. This is an author
decision point; it is not created, inferred, or assumed by this record.

Neither `PAPER_CLAIM_AUDIT=BLOCKED` nor `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`
is changed by this candidate.
