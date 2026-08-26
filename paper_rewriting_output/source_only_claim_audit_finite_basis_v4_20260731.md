# Source-only claim audit: finite-basis manuscript v4

**Generated:** 2026-07-30T19:44:06Z  
**Auditor:** fresh zero-context `gpt-5.6-terra` reviewer, xhigh reasoning  
**Scope:** active source-only manuscript, proof-bearing Supplementary Notes, controlled benchmark contract and raw CSVs, frozen R006c gate/raw result, Figure 1-3 source scripts and SVG assets  
**Overall verdict:** PASS

## Result

No material issue was found. The auditor reported zero unsupported claims, scope overclaims, number mismatches, aggregation mismatches, configuration mismatches, missing-evidence findings or ambiguous mappings.

The four headline gains recompute from the replication-level CSV as 93.552034%, 96.763942%, 82.542788% and 87.321619%, which correctly round to 93.6%, 96.8%, 82.5% and 87.3%. Primary and N=50 replication coverage, endpoint availability, `NaN` to `OUTSIDE TARGET` semantics, denominator and stability thresholds, finite-basis theorem scope, R006c qualification counts, and Figure 1-3 source/asset/caption alignment were also reconciled.

## Residual risk

The Figure 3 interval-export artifact used by the plotting script was outside the declared audit input set. The reviewer verified the displayed gains, panel text, axes and manuscript-cited values, but did not independently reconstruct every whisker coordinate. This is a bounded figure-runtime risk, not a detected manuscript/data mismatch.

## Governance boundary

This receipt is scoped to source-only claim fidelity. It does not change `PAPER_CLAIM_AUDIT=BLOCKED`, `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`, any RCEP/NYC or R006e/R006f outcome state, manuscript promotion, or release authorization.

The authoritative declared-input hashes are stored in the sibling JSON receipt and the trace manifest at `.aris/traces/paper-claim-audit/2026-07-31_run04/input_manifest.sha256`.
