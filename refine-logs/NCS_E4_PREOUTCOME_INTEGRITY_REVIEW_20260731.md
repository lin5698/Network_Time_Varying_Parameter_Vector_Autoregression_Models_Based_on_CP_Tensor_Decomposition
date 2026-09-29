# NCS E4 Pre-outcome Integrity Review

**Date:** 2026-07-31  
**Reviewer:** independent Codex reviewer, read-only  
**Scope:** E4 domain-stability proof, gate-test receipt, v4 schemas, eight
pre-outcome artifacts and r2 candidate  
**Overall verdict:** PASS  
**Scientific execution:** NOT AUTHORIZED  
**Manuscript activation:** BLOCKED

## Decision boundary

This verdict is a repository-local pre-outcome integrity decision. It supports
E4-R001 through E4-R005 only. It does not validate held-out recovery,
uncertainty, duplicate outcomes, scientific claims, RCEP/NYC, R006e/R006f,
downstream builds or manuscript promotion.

The controlling repository verdicts remain `PAPER_CLAIM_AUDIT=BLOCKED` and
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`.

## Review history

The first independent pass returned `WARN`: the candidate builder could create
a static `PASS` receipt without proving that the frozen suites had run. That
receipt path was removed. The replacement recorder now runs the six frozen
suites through a subprocess, verifies an unambiguous `Ran N tests` plus `OK`
transcript, binds current suite and recorder hashes, and writes with no-replace
semantics.

The first provisional candidate at SHA-256
`9817236c0f3a726f3da7ebe8f0356cc680e4e1cd39293ce0ad6fcad092880835`
is superseded and must not be authorized or executed.

The second independent pass reviewed the remediation and r2 package and
returned `PASS` with no blocking findings.

## Evidence

### Receipt execution binding: PASS

- Candidate construction accepts only an external receipt and validates it in
  `scripts/experiments/e3_family2_candidate_package.py`.
- The dedicated recorder in
  `scripts/experiments/e3_family2_gate_receipt.py` executes the frozen unittest
  command and records command, suite modules and hashes, recorder identity,
  UTC times, return code, test count, transcript and transcript hashes.
- The negative test rejects a self-declared simplified `PASS` receipt.
- The frozen receipt records 73 tests, return code 0 and `OK` at SHA-256
  `68b9f97fed60d93819080f18caefb1a69567f3da402bd2130fe969ef0269abd9`.

### Exact proof separation: PASS

- `exact_domain_stability_certificate_report()` uses
  `fractions.Fraction` independently of the float runtime fixture.
- The exact certificate covers 18 operators, envelope `9/10`, maximum projected
  block norm `9/10` and maximum induced infinity norm `9/10`.
- The spectral-radius conclusion follows from the induced-norm inequality, not
  floating-point eigendecomposition.
- The proof packet SHA-256 is
  `8ebf5c63958ce11e70ffe183578ab366a886dce3ca226dd4c596a4bcd85b9738`.

### Candidate and artifact binding: PASS

- Specification v4 SHA-256:
  `e8301d647ce88681347228824a497fde8158f748ab4cdf1208612ed805003cd4`.
- Candidate r2 SHA-256:
  `9213cec8e947a4919aa8ca603ba5514471e7e6293136051826f234c66fbce964`.
- The candidate binds the source, dependency lock, synthetic inputs,
  configuration, query-independent `0.90` envelope, unchanged `0.98` failure
  threshold, all eight versioned pre-outcome artifacts and the new quarantine
  root.
- Hash-valid semantic drift of the envelope is rejected by the validators.

### Pre-science refusal: PASS

- Missing authorization refuses before candidate dereference, trust callbacks,
  scientific entrypoints or root creation.
- RCEP, NYC, R006e and R006f remain excluded routes.
- The r2 quarantine root
  `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r2`
  remains absent.

## Residual boundary

The receipt is repository-local evidence produced by a bound local recorder,
not an external attestation service. Within the frozen pre-outcome contract,
the recorder identity, current suite hashes, transcript and receipt hash close
the earlier self-declaration gap. This does not create production trust or
scientific validity by itself.

## Routing

E4-R001 through E4-R005 may be recorded as `PASS`. E4-R006 through E4-R009
remain `BLOCKED`. Scientific execution can be considered only after a separate
exact, single-use authorization binds the r2 candidate SHA-256 and its frozen
synthetic-only scope.
