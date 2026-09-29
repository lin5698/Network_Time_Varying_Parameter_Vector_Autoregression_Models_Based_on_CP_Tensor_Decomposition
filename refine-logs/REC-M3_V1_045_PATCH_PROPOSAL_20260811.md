# REC-M3 V1-045 / CAL-E03:164 Patch Proposal

Date: 2026-08-11

Mode: read-only audit. No manuscript, formal register, E4-r3 artifact, authorization record, or Git state was modified.

Register binding: `V1-045` / `CAL-E03:164`, item index 164, current status `PARTIAL`, action class `DIRECT_TEXT_REVISION`.

Ledger: `refine-logs/REC-M3_V1_045_CONTRACT_LEDGER_20260811.json`

## Decision Summary

The manuscript's controlled benchmark contract is present and internally consistent for the primary rank/window/replication values and the stability/failure semantics. The direct text revision remains necessary because the supplement does not repeat the full parameter table, ALS stopping is not declared, and topology perturbation magnitudes are not bound. The M2C primary output is a separate, read-only N=20/N=50 audit grid. It supports descriptive coverage and status accounting only; it does not replace the manuscript's N=15/N=30 headline design or activate a claim.

The required non-inferential boundaries are:

- N=20/N=50 are the M2C primary scope only. The original manuscript contract remains N=15/N=30 primary plus bounded N=50 stress, with a separate N=20 endpoint-aware qualification.
- N=100/N=200 are `NOT_RUN/ABSTAIN`. No performance, failure, resource, or scalability conclusion is made for either scale.
- Resource telemetry is `BLOCKED`. Null telemetry, an exit code, process state, record counts, or log presence do not support runtime, memory, GPU, cost, or scale-efficiency claims.
- M2C status accounting retains failure and non-finite categories, but its observed zero counts do not establish failure-free operation or a failure-rate bound.

## Sentence-Level Patch Set

These are proposed edits only. They are not applied by REC-M3.

### P1. Add one complete benchmark parameter table

Target: `manuscript_src/natcs/supp_note4_benchmarks.md` after line 1.

Proposed text:

```markdown
The original controlled benchmark uses true rank 2 and fitted rank 2. Its declared rows are: N=15, T=160, window=40, topology-mixing weight=0.04, horizon=4, 20 replications; N=30, T=200, window=48, topology-mixing weight=0.05, horizon=4, 20 replications; and bounded N=50 stress, T=240, window=56, topology-mixing weight=0.05, true/fitted rank=2, horizon=4, with four replications for local/CP/Tucker/collapsed/no-network rows and one replication for sparse/projected diagnostics. The endpoint-aware qualification is a separate N=20, T=200 design with rank-3 candidates and ten recorded seeds per cell.
```

Reason: `methods_data.md` and `controlled_benchmark_contract.json` agree on these values, but the supplement currently leaves the reader to reconstruct them across files. Do not insert the M2C N=20/N=50 grid into this table as if it were the original benchmark.

### P2. Close the ALS stopping-rule gap and separate solver contracts

Targets: `manuscript_src/natcs/methods_estimator.md` line 3, the `estimator_configuration` object in `controlled_benchmark_contract.json`, and the compiled text at `main.tex:1102-1107` and `supplementary.tex:359-363, 398-403, 2784-2786`.

The CAL-E03 controlled contract declares a 1e-6 Gram regularizer and 60 iterations but no stopping criterion: it does not state the monitored quantity, tolerance, early-stopping rule, or precedence. The compiled manuscript separately reports a main/application CP setting of six initializations, at most 100 iterations and tolerance 1e-6, plus a bootstrap setting of four initializations, at most 80 iterations and tolerance 1e-5. `supplementary.tex` repeats the main 100/1e-6 setting in its implementation section and records the 80/1e-5 bootstrap setting later. The current text does not explicitly bind those application/bootstrap settings to CAL-E03, so the discrepancy must remain a contract mismatch rather than being resolved by inference from M2C.

```text
For the CAL-E03 controlled benchmark, declare whether 60 ALS iterations is a fixed count or a maximum. If it is a maximum, state the monitored quantity, tolerance, early-stop rule and precedence. Separately label the main/application 100-iteration setting and the bootstrap 80-iteration setting.
```

Do not select a stopping rule from the 100/80 compiled settings or from M2C status counts. Until the CAL-E03 rule is bound to the contract, do not describe the controlled fit as converged or globally optimized.

### P3. Make topology perturbations reproducible

Targets: `manuscript_src/natcs/methods_data.md` line 11 and `manuscript_src/natcs/supp_note4_benchmarks.md` lines 15-17; keep the compiled application-layer sensitivity at `main.tex:497-501` and `supplementary.tex:2409-2412` separate unless it is explicitly bound to CAL-E03.

Proposed text:

```markdown
Each CAL-E03 topology stress row must report the exact perturbation amplitude, whether it changes generation or observation, the seed policy, the endpoint, and the replication count. The compiled application text's 50% top-exposure attenuation is not a CAL-E03 perturbation magnitude unless the contract explicitly binds it; category labels such as topology volatility, edge loss and observed-weight noise are not quantitative robustness evidence until those fields are bound to a readable artifact.
```

Reason: the current contract gives the baseline topology law and mixing weights, but not the magnitude of each CAL-E03 stress perturbation. No stress-row ranking should be promoted as a general topology-robustness result, and the application-layer 50% attenuation must not be silently reused as the missing CAL-E03 amplitude.

### P4. Keep the stability metric and thresholds distinct

Targets: `manuscript_src/natcs/methods_uncertainty.md` line 3 and `manuscript_src/natcs/supp_note7_repro.md`; also distinguish `main.tex:1128-1132` and `supplementary.tex:2889-2890` from the controlled contract.

Proposed text:

```text
Stability qualification in the CAL-E03 contract uses spectral norm: response stabilization is triggered at 0.95 and targets 0.95, while unscaled instability is recorded at 0.98. The compiled application text separately monitors spectral radius, flags radius at or above one and describes rescaling toward radius 0.98. A primary audit artifact or application text that reports spectral-radius fields is not interchangeable with the CAL-E03 spectral-norm contract unless it serializes the metric mapping.
```

Reason: the M2C primary output has a supported stability summary and `estimated_spectral_radius` fields, but no 0.95/0.98 spectral-norm threshold key. This is a provenance boundary, not evidence that the CAL-E03 thresholds were independently rerun or that application spectral-radius wording supplies the missing mapping.

### P5. State status retention and its limit

Target: `manuscript_src/natcs/supp_note4_benchmarks.md` after line 17.

Proposed text:

```text
All declared failure, non-finite, outside-target and unstable statuses remain in the accounting denominator. A zero status count in one frozen run is not evidence of failure-free operation or a failure-rate bound.
```

Reason: the M2C primary status totals are AVAILABLE-only, but its retention flags and non-finite audits show that this is an observed outcome, not a changed failure policy.

### P6. Separate M2C provenance from manuscript benchmark provenance

Target: `manuscript_src/natcs/supp_note7_repro.md` line 7 or a new audit-boundary paragraph in `supp_note4_benchmarks.md`.

Proposed text:

```text
The REC-M2C CAL-E03:164 primary artifact is a read-only audit of a separate N=20/N=50 grid. It does not revise the original N=15/N=30 controlled comparison, change the N=50 stress designation, or activate a manuscript claim. It contains 20 recorded seeds per scoped cell but only one execution, so it does not establish repeated-run reproducibility; the per-cell seed count does not replace the original replication contract.
```

### P7. Freeze the unrun-scale and resource wording

Target: `manuscript_src/natcs/supp_note7_repro.md` line 7 or `supp_note8_scope.md` after line 20.

Proposed text:

```text
N=100 and N=200 were not run in REC-M2C and remain NOT_RUN/ABSTAIN. No performance, failure, resource, or scalability conclusion is made for either scale. Resource telemetry is BLOCKED: wall time, CPU time, peak memory/RSS, GPU time and per-cell runtime values are null or unavailable. The compiled supplementary text reports runtime/peak-memory measurements for its own scenario tables, but those statements do not supply the missing M2C fields. No runtime, cost, memory, GPU or scalability conclusion is made.
```

Do not replace this wording with claims that N=100/N=200 failed, were too expensive, or do not scale. Those would be unsupported resource conclusions.

## Claim Ceiling After Patch

The permitted wording remains:

1. The original controlled evidence is limited to the declared synthetic N=15/N=30 primary rows and bounded N=50 stress rows, with their stated rank, windows, endpoints and replication counts.
2. The separate endpoint-aware N=20 qualification remains a qualification boundary, not broad native recovery.
3. The M2C artifact can be cited only as a read-only, descriptive N=20/N=50 audit of coverage, status retention, and raw stress accounting within its own scope.
4. No ALS convergence or global-optimum claim is licensed until stopping semantics are explicit.
5. No universal stability, topology-robustness, cross-scale, independent-reuse, native-held-out, causal, or estimator-superiority claim is licensed.
6. N=100/N=200 remain `NOT_RUN/ABSTAIN`, and resource telemetry remains `BLOCKED`.

## Release Gate

Before any proposed manuscript patch is applied, confirm the exact ALS stopping semantics and bind all topology stress magnitudes to a readable contract. After any later edit, rerun the sentence-to-evidence audit and recheck the protected hashes. REC-M3 itself authorizes neither manuscript mutation nor claim activation.
