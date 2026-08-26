# NCS E4 r3 Experiment Audit

**Date:** 2026-08-01  
**Auditor:** independent Codex reviewer, read-only  
**Scope:** frozen synthetic-only E4 r3 execution  
**Inventory:** `E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json`  
**Inventory SHA-256:** `5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046`

## Overall verdict: WARN

## Integrity status: warn

The authorized r3 execution is complete, content-addressed and internally
traceable. Ground truth comes from the declared simulation data-generating
process; raw metrics are retained; the full declared recovery and uncertainty
grid is present; bootstrap retuning and failure retention are reachable; and
the one-time execution binding is intact. The evaluation type is
`simulation_only`.

The audit remains below `PASS` because the frozen result does not serialize one
predeclared E4-R006 metric family: the paired panel-level log error ratio and
its cell-level confidence interval. Raw paired errors are present, but they do
not replace the missing predeclared summary. No protocol amendment or
post-outcome metric substitution is accepted by this audit.

## Checks

| Check | Status | Controlling evidence |
|---|---|---|
| A. Ground-truth provenance | PASS | Synthetic DGP truth is constructed independently of predictions in `scripts/experiments/e3_synthetic_core.py`. |
| B. Score normalization | PASS | Raw operator, response, interval and stability metrics are retained; no self-normalization was found. |
| C. Result existence and traceability | PASS | Candidate, authorization, manifest, result, completion marker, launch plist and logs exist and match the frozen SHA inventory. |
| D. Reachability and declared metrics | WARN | Recovery, status, pairing, bootstrap and interval paths are reached, but the predeclared log-ratio metric and confidence interval are absent. |
| E. Scope | PASS | 48 recovery cells, 32 paired-comparison cells, 8 interval cells, 46,080 recovery records and 160 interval records are present. |
| F. Evaluation classification | PASS | `simulation_only`; no empirical or universal-performance claim is licensed. |
| G. Isolation, parity and retention | PASS | Truth isolation, one-time topology normalization, no-query selection, same-endpoint evaluation, full-cell retention and fixed thresholds are preserved. |
| H. Bootstrap implementation | PASS | Recursive pseudo-history, per-replicate retuning, rank-aware history gates, failure retention and simultaneous max-deviation intervals are implemented and represented. |
| I. Terminal provenance | PASS | `runs=1`, exit code `0`, empty stderr, quarantine-only stdout and matching artifact hashes. |

The initial reviewer chronology warning was withdrawn after reading
`E4_R3_CLOCK_PROVENANCE_20260801.json`. The run crossed local midnight in
`Asia/Shanghai`; the 2026-08-01 inventory and review timestamps are therefore
internally coherent.

## Claim impact

### E4-R006: QUALIFIED, NOT ACTIVATED

The frozen output supports a complete synthetic recovery grid, same-endpoint
comparisons and retention of every declared family-scale-query-horizon cell.
The reviewer found lower panel-level median response error for the fixed-rank
basis method than for both declared comparators in every such cell.

This evidence cannot yet activate an E4-R006 manuscript claim because the
predeclared panel-level log-error-ratio summary and confidence interval are not
serialized. The evidence ceiling remains the declared synthetic DGP.

### E4-R007: QUALIFIED, NOT ACTIVATED

All 8 interval cells and 160 panel-level interval records are present. Each
panel requests and records 80 available bootstrap replicates, and the cell
summarizer does not condition on a successful subset.

The evidence is based on 20 simulated panels per cell at horizon 4. It does not
support empirical calibration, broader uncertainty validity or other horizons.
A separate result-to-claim judgment is required before any wording is drafted.

## Required next action

1. Keep E4-R006 blocked unless a separately governed, content-addressed
   derived artifact supplies the predeclared panel-level log-error-ratio
   summary and confidence interval without changing the frozen r3 result.
2. Run an independent result-to-claim review against the scoped integrity
   verdict before drafting any E4 sentence.
3. If claims are later activated, create a sentence-level ledger that binds
   each claim to exact frozen JSON key paths and retains the `simulation_only`
   ceiling.

## Status invariants

- `PAPER_CLAIM_AUDIT` remains `BLOCKED`.
- `EMPIRICAL_IMPLEMENTATION_AUDIT` remains `FAIL`.
- No RCEP, NYC, R006e or R006f outcome is affected.
- No manuscript or package build is authorized by this report.

Review trace: `.aris/traces/experiment-audit/2026-08-01_run01/`.
