# R006c Endpoint-Aware Estimator Design

**Date:** 2026-07-15  
**Status:** written specification approved by the author on 2026-07-15  
**Predecessor:** R006b `FAIL` with integrity status `pass`

## 1. Decision Question

Can an anchor-parameterized low-rank estimator improve the fitted query at `W_ref` without sacrificing a topology-switch endpoint at a topology that was excluded from fitting and tuning?

R006c is a method-screening gate. It does not assume that CP remains the headline method. CP can retain that role, or a target-aware estimator can replace it, only if one fixed candidate passes every prespecified required cell. R006, R006b and their thresholds remain unchanged.

## 2. Claim Boundary

### Primary claim under test

An anchor parameterization can protect reference-query recovery while retaining an explicit network slope that supports held-out topology substitution.

### Anti-claims to rule out

- Improvement comes only from fitting the easier collapsed operator at `W_ref`.
- The selected method uses `W_alt` during fitting, validation, rank selection or penalty selection.
- Lower block error necessarily implies lower topology-query error.
- A method can pass by switching between CP and Tucker across cells.
- Projected sensitivity can replace a failed raw-response gate.

### Promotion rule

Only a single fixed candidate, either `anchor_split_cp3` or `anchor_split_tucker333`, that passes all required matched and native cells may trigger reconsideration of the manuscript method headline. A matched-only pass is a theory diagnostic and cannot support promotion.

## 3. Anchor Parameterization

For the supplied reference topology `W_ref`, rewrite the dynamic operator as

```text
M_t(W) = A_t + B_t W
       = M_ref,t + B_t (W - W_ref),

M_ref,t = A_t + B_t W_ref.
```

The local anchor regression uses

```text
y_{t+1} = M_ref,t y_t + B_t (W_t - W_ref) y_t + epsilon_{t+1}.
```

Its rolling design is `[y_t, (W_t-W_ref)y_t]`. The same scale-adaptive ridge contract used by corrected R006b applies to every local fit. The fitted separated object is `[M_ref,t, B_t]`, and the original direct block is recovered only when needed:

```text
A_t = M_ref,t - B_t W_ref.
```

For any held-out topology,

```text
M_t(W_alt) = M_ref,t + B_t (W_alt - W_ref).
```

This removes the need for `A/B` error cancellation at `W_ref` while keeping topology substitution available through `B_t`.

## 4. Topology Holdouts

Each replication uses independent named random streams for operator structure, estimation topology, innovations, the main held-out topology and the stress topology.

The stream assignment is part of the frozen protocol. For replication seed `seed`, construct `SeedSequence(seed).spawn(5)` once and map the children by position as follows:

```text
0 -> operator_structure
1 -> estimation_topology
2 -> innovations
3 -> main_holdout_topology
4 -> stress_topology
```

No method may spawn additional children from the replication-level sequence. Method-specific randomness, including CP multi-start initialization, must be derived from a separate deterministic method seed keyed by `(seed, layer, rho, a3, eta, method)` so that adding or reordering methods cannot alter the data-generating streams.

### Main held-out endpoint

Let `W_holdout` be a row-normalized topology drawn from the same generator family but from a random stream unavailable to the estimator. Define

```text
W_alt_main = row_normalize(0.75 W_ref + 0.25 W_holdout).
```

This is the primary topology-switch endpoint. It tests an in-family, moderate-distance substitution.

### Stress endpoint

Let `W_alt_stress` be an independently generated row-normalized topology with no convex mixing toward `W_ref`. It is a distribution-shift diagnostic and is not part of the pass/fail criterion.

### Leakage prohibition

Neither held-out topology may be passed to estimator, reconstruction, validation, rank selection or penalty-selection functions. A regression test must perturb both held-out topologies while holding all fitting inputs fixed and verify bitwise-identical fitted tensors and selected hyperparameters.

## 5. Frozen Core Grid

- `N=20`, `T=200`, rolling window `80`
- layers: `matched`, `native`
- `rho in {0.80, 0.95}`
- `a3 in {0.10, 0.25}`
- estimation-topology separation `eta in {0.02, 0.15, 0.45}`
- 10 paired seeds `240100` through `240109`
- innovation standard deviation `0.25`
- response horizon `8`
- adaptive ridge multiplier `0.001`
- fitted rank `3`

The expected full-grid size is

```text
2 layers x 2 rho x 2 a3 x 3 eta x 10 seeds x 9 methods = 2160 rows.
```

`eta=0.02` is a prespecified weak-separation boundary. It is reported but is not required to pass. Exact-rank `a3=0` and negative-boundary `a3=0.50` expansions are deferred until a candidate passes the core gate.

## 6. Compared Methods

### Separated-block comparators

1. `block_local`: corrected R006b rolling `[A,B]` estimator.
2. `block_fused_tv`: causally selected fused-TV smoothing of the block-local path.
3. `block_cp3`: rank-3 CP reconstruction of the block-local tensor.
4. `block_tucker333`: Tucker `(3,3,3)` reconstruction of the block-local tensor.

All four retain `[A,B]` and can be evaluated at all three endpoints.

### Anchor candidates

5. `anchor_local`: rolling `[M_ref,B]` estimator without temporal low-rank reconstruction.
6. `anchor_split_cp3`: separate rank-3 CP reconstructions of the `M_ref` tensor and the `B` tensor.
7. `anchor_split_tucker333`: separate Tucker `(3,3,3)` reconstructions of the `M_ref` tensor and the `B` tensor.

The two candidate reconstructions are deliberately split. Joint reconstruction could reintroduce domination of the reference-query block by the weakly identified network slope.

### Availability and mechanism diagnostics

8. `collapsed_ref_tucker333`: Tucker smoothing of the anchor-local `M_ref` path after discarding `B`. It reports `W_ref` metrics and explicit `unavailable` values at both `W_alt` endpoints. It cannot pass the main gate.
9. `oracle_b_anchor`: the same smoothed `M_ref` path as the anchor-Tucker candidate combined with the true simulated `B` path. It distinguishes failure of `B` estimation from failure of reference-query smoothing. It is never eligible to pass the main gate.

The hard anchor identity is tested as a construction diagnostic rather than added as a tenth grid method. Joint constrained CP is deferred unless a split anchor candidate passes.

## 7. Validation and Reconstruction Rules

- Fused-TV penalties are selected only from the pre-evaluation prefix, using chronological validation prediction at observed training topologies.
- Evaluation dates cannot influence candidate fitting used for validation scoring.
- CP and Tucker ranks are fixed at `3`; no outcome-facing rank selection occurs in R006c.
- `W_alt_main` and `W_alt_stress` are excluded from every validation score.
- Full-path smoothed prediction error is stored as `retrospective_prediction_rmse`, not described as out-of-sample forecasting.
- Raw, stability-qualified and projected response metrics remain separate.

## 8. Stored Metrics

For each available endpoint:

- relative operator error
- absolute operator Frobenius error
- raw finite-horizon response error
- response error relative to a zero-operator estimate
- stability-qualified response error and qualification rate
- projected sensitivity error, stored only as sensitivity
- estimated spectral radius and instability rate

For each separated method:

- `B` block relative error
- topology-slope error `||(B_hat-B)(W_alt-W_ref)||_F`
- full stored-object error
- cancellation index

The cancellation index at `W_ref` is

```text
(||Delta A||_F + ||Delta B W_ref||_F)
-------------------------------------------------
          ||Delta A + Delta B W_ref||_F
```

where `Delta` denotes estimate minus truth. Large values indicate that small query error relies on cancellation between large block errors.

Numerically, let the numerator be `u` and the denominator be `v`. Return `0` when `u == 0` and `v == 0` (the exact-estimate case); otherwise return `u / max(v, 1e-12)`. This convention preserves a large diagnostic value for genuine cancelling errors without producing `NaN` or infinity.

Additional stored fields are endpoint availability, separation diagnostics, design-Gram spectrum, adaptive ridge scale, selected fused penalty, CP multi-start diagnostics, runtime, layer state diagnostics and all construction-gate errors.

## 9. Required Cells and Stop-Go Gate

Required cells use `eta in {0.15, 0.45}`, both layers, both rho values and both a3 values. Each candidate therefore faces 16 required cells with 10 paired seeds per cell.

A fixed candidate passes a required cell only if all conditions hold:

1. `W_ref` and `W_alt_main` availability are both 100%.
2. Median relative operator error is below `1.0` at both endpoints.
3. Median response-error/zero-error ratio is below `1.0` at both endpoints.
4. Paired median raw-response improvement is at least `10%` against each of `block_local`, `block_fused_tv` and `block_tucker333`, separately at both endpoints.
5. Joint win rate against all three comparators is at least `80%`, separately at both endpoints.
6. Per-seed worst-endpoint raw response is `max(error_ref, error_alt_main)`. Its paired median improvement is at least `10%` against each comparator's corresponding worst-endpoint value.
7. All 10 paired seeds are present and have no numerical failure.

A candidate can trigger method promotion only if the same method passes all 16 required cells. Cellwise switching between anchor CP and anchor Tucker is prohibited. Passing only the matched layer is recorded as a controlled diagnostic. `eta=0.02`, `W_alt_stress`, collapsed and oracle rows never substitute for a failed required cell.

## 10. Failure Interpretation

- `anchor_local` succeeds but split low-rank fails: reconstruction, not parameterization, is the bottleneck.
- Oracle-B succeeds but feasible anchors fail: network-slope estimation is the bottleneck.
- Oracle-B fails at `W_ref`: reference-query smoothing is the bottleneck.
- `W_ref` passes but `W_alt_main` fails: the method protects the anchor but does not preserve useful switchability.
- Matched passes but native fails: endogenous state/design coupling blocks a method claim.
- Collapsed wins at `W_ref`: this confirms the easier reduced-form target but provides no evidence for topology substitution.
- Both anchor candidates fail: retain the target-mismatch result and stop before R007 confirmation or scale expansion.

## 11. Test Contract

Implementation begins with RED tests for:

- exact anchor identity at `W_ref`
- correct query construction at `W_alt_main` and `W_alt_stress`
- fitted-output invariance to held-out-topology perturbation
- independent random-stream reproducibility
- collapsed endpoint unavailability
- oracle-B substitution identity
- scale-adaptive ridge invariance
- causal fused validation exclusion
- cancellation-index behavior on exact and cancelling-error examples
- separate raw, qualified and projected metric storage
- smoke runs cannot report full `PASS`

## 12. Run Order and Artifacts

1. RED/GREEN construction and metric tests.
2. One-seed smoke over both layers, both rho values, both a3 values and all eta values.
3. Construction-only gate artifact with protocol/code hashes before outcome execution.
4. Frozen 2160-row full run using Apple Accelerate CPU workers.
5. Isolated duplicate run and non-runtime deterministic comparison.
6. Independent experiment-integrity audit.
7. Independent result-to-claim judgment.

New outputs are isolated under:

```text
output/high_impact_revision/r006c_endpoint_aware/
output/high_impact_revision/r006c_endpoint_aware_repeat/
```

No R006, R006b, rejected-submission or manuscript-facing result is overwritten. Manuscript revision and N=50/100 expansion remain frozen until the R006c result-to-claim gate completes.
