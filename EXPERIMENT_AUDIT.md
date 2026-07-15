# Experiment Audit Report

**Date:** 2026-07-15  
**Auditor:** independent Codex reviewer, read-only  
**Current scope:** R006c endpoint-aware estimator, post-remediation

## Overall Verdict: WARN

## Integrity Status: pass

## Scientific Outcome: FAIL

The corrected R006c experiment is numerically and procedurally sound. The
reviewer's only warning was the then-stale project documentation, which is
updated after this audit. R006c remains a negative method gate.

## Checks

### A. Ground-Truth Provenance: PASS

R006c is simulation-only. Analytical `A`, `B`, `M_ref`, observed operators and
endpoint truth are generated before estimation. True `B` is used only by the
explicitly ineligible oracle mechanism diagnostic.

### B. Score Normalization: PASS

Relative operator error uses the truth norm; response ratios use the declared
zero-operator baseline. Raw, stability-qualified and projected sensitivity
metrics are retained separately, and projected sensitivity is excluded from
promotion.

### C. Result Existence and Match: PASS

Independent CSV parsing found 2,160 unique rows, zero failures, 240 complete
simulation/seed cells, ten seeds in every required cell and 216 summary rows.
All 32 candidate-cell records and 64 endpoint gates recompute with zero numeric
mismatches. CP passes `0/16`; Tucker passes `6/16`; no candidate is promoted.

### D. Dead Code and Stored Metrics: PASS

The formal CLI reaches all declared construction, fitting, evaluation and gate
paths. Fresh tests pass `44/44` for R006c and `69/69` across the experiment
suite.

### E. Leakage and Causality: PASS

Held-out endpoints are absent from fitting inputs. Fused validation reconstructs
only the prefix available through each validation date, and a regression test
proves later validation estimates cannot change earlier scores.

### F. Duplicate and Provenance: PASS

Protocol, correction-addendum and seven transitive-code hashes match both
pre-outcome artifacts and result payloads. The corrected primary and repeat
runs have zero non-runtime differences; pre-correction history remains isolated.

### G. Scope: PASS

This is an `N=20`, `T=200`, simulation-only estimator gate. Broad endpoint-aware
superiority and general topology-switch claims remain unsupported.

### H. Gate Fidelity: PASS

Promotion requires one fixed candidate across both endpoints and all 16 cells.
Stress, weak-separation, collapsed, oracle and projected diagnostics cannot
rescue a required-cell failure.

## Claim Impact

- R006c overall `FAIL`: independently supported.
- `anchor_split_cp3`: unsupported, `0/16`.
- `anchor_split_tucker333`: unsupported, `6/16` (`6/8` matched, `0/8` native).
- Endpoint-aware/topology-switch superiority: unsupported.
- Matched Tucker, collapsed and oracle behavior: diagnostic only.

## Routing

Keep the manuscript, R007 confirmation and N=50/100 expansion frozen. A new
prespecified estimator question is required before further method-design work.
The detailed report is `refine-logs/R006C_AUDIT_20260715.md`.

## Prior Audit

R006b retains integrity `pass` and scientific `FAIL` after its causal-selection
correction. Its full result-to-claim record remains in `findings.md` and its
trace remains under `.aris/traces/experiment-audit/2026-07-15_run01/`.
