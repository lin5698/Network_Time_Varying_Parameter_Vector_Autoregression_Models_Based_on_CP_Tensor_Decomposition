# NCS E3 Synthetic Core Source Review

Date: 2026-07-23

Status: `PASS`, `SOURCE_ONLY`, `NOT_AUTHORIZED`.

## Scope

An independent read-only review examined the E3 synthetic core, its fixture
tests, and the native-endpoint interface note. No topology grid, recovery
calculation, bootstrap outcome, quarantine output, RCEP/NYC route, R006e/R006f
route, manuscript build, or claim promotion was executed.

## Verified properties

1. All public synthetic generator, fit, selection, query-evaluation, panel
   recovery, interval, and native-path evaluation routes run the E3-1 exact
   classification gate before numerical work.
2. The retained-block estimator and endpoint constructors are private helpers,
   not alternate public fitting or endpoint routes.
3. Cached native paths are accepted only when they retain the exact observed
   arrays, family, configuration and seed of the evaluated panel. The former
   wrapper-identity comparison that forced cached paths to `NONCONVERGED` is
   covered by a regression fixture.
4. Bootstrap status accounting retains every replicate, and any non-available
   replicate invalidates the interval instead of conditioning a band on the
   successful subset.

## Source-only verification

- `python3 -m unittest scripts.experiments.test_e3_synthetic_core`: 12 tests
  passed.
- `python3 -m unittest scripts.experiments.test_e3_family2_preoutcome`: 17
  tests passed.
- `python3 -m unittest scripts.experiments.test_e3_family2_synthetic_runner`:
  11 tests passed.
- `python3 -m unittest scripts.experiments.test_e3_family2_candidate_package`:
  4 tests passed.
- `py_compile` passed for the E3 core, pre-outcome boundary, source-only
  runner, candidate-ready materializer and candidate-package builder.

The associated machine-readable authorization-gate receipt is
`refine-logs/e3_family2_inputs/e3-authorization-gate-test-receipt-20260723.json`.
It records source-only test hashes and is neither a production trust signature
nor a scientific execution authorization.

## Boundary

This review supports only source readiness for a future candidate package. It
does not establish E3-1 through E3-4 outcomes, change
`PAPER_CLAIM_AUDIT=BLOCKED` or `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`, or allow
the paper to describe synthetic recovery, cross-family generality, uncertainty
calibration or stability results.
