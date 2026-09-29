# E3 v2 Bootstrap-History Candidate Readiness

**Status:** CANDIDATE_READY_NOT_AUTHORIZED  
**Date:** 2026-07-23  
**Scope:** Static synthetic-only candidate construction and pre-outcome validation. No scientific execution occurred.

## Candidate Identity

- Candidate ID: `e3-family2-synthetic-v2-20260723-bootstrap-history-closure`
- Candidate path: `refine-logs/e3_family2_candidates/e3-family2-synthetic-v2-20260723-bootstrap-history-closure/candidate.json`
- Candidate SHA-256: `7585cd53ffe963aeadb2d7af5a71c02e25a35c2fbee82aa6c625ac2d2d093a2d`
- Bound source-only gate-test receipt: `refine-logs/e3_family2_inputs/e3-authorization-gate-test-receipt-v2-20260723-bootstrap-history-closure.json`
- Gate-test receipt SHA-256: `982c7819436d677f14cbfc3543095e7f51211a73e1062898cce9f144c23c6eb9`
- Bound, new quarantine output root: `refine-logs/e3_family2_quarantine/e3-family2-synthetic-v2-20260723-bootstrap-history-closure-quarantine`

The quarantine root was verified absent during static validation and has not been created.

## v2 Contract Changes

The fixed-rank residual-bootstrap route now derives refit eligibility from the causal local-history requirement rather than using the former shared start time of 13:

| Allowed rank | Earliest valid refit time | Required minimum valid refit opportunities |
|---|---:|---:|
| 1 | 14 | 2 |
| 2 | 14 | 2 |
| 3 | 15 | 2 |

The v2 candidate binds this gate in all three pre-outcome locations:

1. `synthetic-e3-v2.json`
2. Candidate execution configuration
3. The versioned `tuning_split_manifest` artifact

The semantic validator recomputes the rank-aware starts and refuses a candidate if any allowed rank has fewer than two valid refit times before a declared uncertainty target. It also rejects the old start-at-13 contract.

## Cross-Generator Boundary

The v2 contract preserves the frozen stability threshold of `0.98` and binds the cross-generator policy as a scientific failure boundary:

- all predeclared cross-generator cells must be retained;
- threshold relaxation is prohibited;
- selection of stable cells is prohibited;
- instability is not converted into a passing generality result.

This is a protocol constraint, not a claim that the v2 execution will succeed. The existing v1 cross-generator instability remains an unaltered failure boundary; no v1 outcome was overwritten or reinterpreted.

## Static Evidence

The following fixture-only suites passed against the source closure bound by the candidate:

- `test_e3_synthetic_core.py`: 13 tests
- `test_e3_family2_preoutcome.py`: 18 tests
- `test_e3_family2_candidate_package.py`: 7 tests
- `test_e3_family2_synthetic_runner.py`: 11 tests
- `test_e3_family2_authorized_executor.py`: 7 tests

Static candidate validation checked the candidate shape, source hashes, dependency lock, all eight candidate-ready pre-outcome artifacts, synthetic inputs, configuration, the rank-history gate, and the unused quarantine root. A direct missing-authorization check refused before `make_synthetic_panel` could be called and left the quarantine root absent.

## Required Authorization

No `workspace-author-authorization.json` was created for this candidate. The candidate remains ineligible for scientific execution until the workspace author issues a new exact-SHA authorization under `e3-family2-synthetic-execution-authorization-v2`.

The authorization must bind exactly the candidate SHA above, the candidate ID, its source/dependency/configuration/pre-outcome-artifact hashes, and the stated quarantine root. Its scope must remain one synthetic-only invocation and must continue to prohibit RCEP, NYC, R006e/R006f outcomes, downstream builds, manuscript promotion, and audit-status changes.

Neither `PAPER_CLAIM_AUDIT=BLOCKED` nor `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` is changed by this candidate.

## Superseded Static Candidates

The earlier unexecuted v2 packages ending in `bootstrap-history-gate` and `bootstrap-history-binding-gate` were created before the final source-closure checks were added. They are retained for audit traceability only, have no author authorization, and must not be used for scientific execution. Only the closure candidate SHA above is eligible to receive a future exact authorization.
