# R006e Native Supported-Endpoint Recovery Protocol

**Date:** 2026-07-16
**Status:** frozen design; construction and implementation authorized; formal outcomes prohibited until the hash-locked construction gate passes

**Parent evidence:** corrected R006c `FAIL`; R006d `CONSTRUCTION_FAIL`
**Scientific boundary:** R006e and R006f are independent experiments. R006f cannot rescue an R006e failure, promote an R006e estimator, or alter the R006c/R006e method verdict.

## Primary Claim

**Prespecified target claim, licensed only if every frozen screening, conditional-confirmation, duplicate, and independent audit gate passes:**

In the frozen N=20, T=200 native endogenous VAR simulation regime, one fixed design-weighted joint Tucker estimator improves finite-horizon response recovery at two never-fitted, design-supported topology endpoints relative to three fixed same-target comparators.

This sentence is the required claim text, not a statement that an outcome has been achieved. If licensed, it is limited to the frozen DGP, horizon 8, native layer, and support-conditioned endpoints.

## Anti-Claims
- no CP superiority;
- no universal topology-switch recovery;
- no causal or empirical-generalization claim;
- no calibrated uncertainty;
- no scale claim beyond N=20;
- no abstention claim.

R006e also does not license native temporal-GNN superiority. The cross-family result, if it passes every gate, remains support-conditioned and is not evidence for arbitrary unseen network families.

## Frozen DGP And Splits

R006e inherits the corrected R006c native endogenous VAR construction.

| Field | Frozen value |
| --- | --- |
| Nodes and dates | `N=20`, `T=200` |
| Rolling window | 80 |
| Response horizon | 8 |
| Innovation scale | 0.25 |
| Layer | native only |
| Query spectral radius | `rho in {0.80, 0.95}` |
| Rank-3 approximation target | `a3 in {0.10, 0.25}` |
| Required topology separation | `eta in {0.15, 0.45}` |
| Primary cells | 8 |
| Calibration dates | 80-139 |
| Validation dates | 140-163 |
| Evaluation dates | 164-199 |

The matched layer and `eta=0.02` may be retained only as mechanism diagnostics. They cannot satisfy or rescue a primary gate. All 24 validation positions use strictly rolling reconstruction prefixes. The evaluation region contains 36 dates.

Development screening uses the ten seed IDs `240100-240109`. These seeds have influenced prior method design and cannot support a confirmatory claim. Conditional confirmation uses the 30 newly frozen seed IDs `250100-250129`. The seed is the clustered inferential unit across all eight primary cells.

## Supported Endpoints

`W_ref` is the reference safety endpoint. It is a guardrail and does not enter the primary held-out claim.

`W_alt_interp` is generated once per seed-cell from an independent stream:

```text
row_normalize(0.75 W_ref + 0.25 W_holdout_ER)
```

Its calibration support maximum must satisfy `max chi_tau <= 0.10`. The endpoint is constructed exactly once: no redraw is allowed for failed calibration support, prospective support loss, or an unfavorable recovery result. Failed calibration support is a construction failure.

`W_alt_family` is selected from the frozen 64-member directed degree-corrected SBM pool inherited from R006d. Selection uses calibration predictors and topologies only. The endpoint is the lowest-index candidate satisfying `max chi_tau <= 0.10`. If none passes, the seed-cell is a construction failure. The selected endpoint is not replaced if prospective validation or evaluation support later fails.

For direct design `X`, topology exposure design `Z`, and query difference `Delta W`, the support calculation is

```text
Z_tilde = (I - X X_dagger) Z
tau = max(1e-10, s_max / 50)
chi_tau = ||Delta W' (I-P_tau)||_F / max(||Delta W'||_F, 1e-12)
```

The stored design diagnostics include the full singular spectrum, absolute retained singular values, condition number, `chi_tau`, and query amplification. Full numerical rank is not interpreted as accurate recovery.

For a seed-cell, a held-out endpoint is **available** only when it is constructed exactly once, has a finite calibration support path with `max chi_tau <= 0.10`, has finite prospective support diagnostics, and retains `chi_tau <= 0.10` at every one of the 24 validation and 36 evaluation prefixes. `W_alt_family` additionally requires a selected member of the fixed 64-candidate pool. Both held-out endpoints must be available for every required method row. Failed construction, missing endpoint or method row, nonfinite support value, or support loss makes availability false. The originally constructed or selected endpoint is retained in the record and is never redrawn or replaced.

## Compared Systems

The sole promotion candidate is `dw_joint_tucker333`:

- fitted object `Theta_t=[M_ref,t, B_t]`;
- normalized rolling outcome loss using the realized design;
- Tucker rank fixed at `(3,3,3)`;
- temporal penalty `lambda_T in {0, 0.01, 0.05, 0.20}`;
- three deterministic starts, frozen backtracking, 300-iteration cap, and R006d convergence diagnostics;
- no unsupported-direction penalty because the primary R006e question contains supported endpoints only.

The three required same-target comparators are:

1. `anchor_local`: scale-adaptive rolling ridge for `[M_ref,B]`;
2. `anchor_fused_tv`: strictly chronological four-penalty fused-TV smoothing of the anchor-local path;
3. `anchor_split_tucker333`: the fixed R006c rank-3 split reconstruction of `M_ref` and `B`.

Block-parameterized methods may appear as supplementary diagnostics only. Oracle methods use a separate API and cannot be passed into the promotion fit path.

`anchor_fused_tv` uses exactly the four penalties `(0.10, 0.25, 0.50, 1.00)`. For each penalty and each of the 24 validation positions it smooths only `local[:, :, :position+1]` and scores only the final coefficient at the observed topology. Its aggregate RMSE is the square root of the mean squared error after concatenating every scalar component of the 24 observed-topology prediction-residual vectors. Selection minimizes the ordered pair `(aggregate RMSE, penalty)`, so an exact score tie selects the smaller penalty. At evaluation it refits each of the 36 available prefixes with the selected penalty and retains only that prefix's final slice; it never smooths the full evaluation tail in one call.

## Candidate Objective And Optimizer

For each coefficient date `t`, the candidate uses the realized rolling design and the normalized outcome loss inherited from R006d:

```text
L_t(Theta_t)
  = sum_s || y_(s+1)
              - M_ref,t y_s
              - B_t (W_s-W_ref) y_s ||_2^2

g_bar = mean_t trace(Q_t' Q_t / n_t) / (2N)

(1/D) sum_t L_t(Theta_t) / (N n_t)
  + lambda_T g_bar / (2 N^2 (D-1))
      sum_t ||Theta_t-Theta_(t-1)||_F^2
```

Here `Q_t=[X_t,Z_t]`, `D` is the number of fitted coefficient dates, and `n_t` is the rolling-window size. `g_bar` is recomputed using only the available training prefix for every validation and evaluation-prefix fit; no value from a later prefix is reused. Unlike R006d, R006e has no unsupported-direction penalty and no `lambda_B` grid.

The Tucker rank is fixed at `(3,3,3)`. The frozen temporal grid is `lambda_T in {0, 0.01, 0.05, 0.20}`. For every grid value and every one of the 24 validation dates, the candidate fits only the coefficient prefix available at that date and scores only the final slice at the observed topology. Its aggregate RMSE is the square root of the mean squared error after concatenating every scalar component of the 24 observed-topology prediction-residual vectors. Selection minimizes `(aggregate RMSE, lambda_T)`, so an exact score tie selects the smaller `lambda_T`. With that fixed value, each of the 36 evaluation prefixes is fitted independently and only its final slice is retained.

Optimization uses exactly three deterministic starts. Construct the prefix-specific anchor split-Tucker tensor by projecting `M_ref` and `B` separately, concatenate the two blocks, and then apply the joint deterministic rank-`(3,3,3)` projection and normalization once; this joint projection is start 0, `Theta_0`. For starts 1 and 2, draw an i.i.d. standard-normal tensor `G_j` using a keyed optimizer substream whose key tuple is `(method_seed, prefix_end_date, lambda_T_grid_index, start_index)`, with start indices 1 and 2, and set

```text
Theta_j,pre = Theta_0
  + 0.05 * max(||Theta_0||_F, 1) * G_j / max(||G_j||_F, 1e-12).
```

Project `Theta_j,pre` once to Tucker rank `(3,3,3)` by the same deterministic truncated-HOSVD projection and sign convention used in every optimizer iteration, then apply the same factor normalization. Perturbations are therefore applied in tensor space, not factor space. For every unfolding, singular values belong to the same tied block when their absolute difference is at most `64 * eps * max(s_max,1)`. Within a tied block, form its rotation-invariant projector, project coordinate axes in increasing index order, and apply deterministic modified Gram-Schmidt; skip residual norms at or below the same tolerance. Fix each retained vector's sign so its lowest-index maximum-absolute entry is positive. If the rank cutoff intersects a tied block, retain the first required canonical vectors in that order. No other random rotation, sign choice, perturbation scale, or warm start is permitted. Optimization randomness cannot enter the DGP or endpoint streams.

Each iteration computes the gradient of the complete normalized prefix objective, takes a trial step, projects to rank `(3,3,3)`, applies factor normalization, and evaluates the post-projection objective. Backtracking tests exactly `alpha_j=2^{-j}` for `j=0,...,24`, accepting the first finite objective no larger than the preceding accepted objective plus `1e-12`. Failure of all 25 trials records `BACKTRACK_FAIL`, leaves the preceding iterate as the final tensor, and is not convergence.

After every accepted step from `Theta_old` to `Theta_new`, relative improvement is `(F_old-F_new)/max(abs(F_old),1e-12)`. The objective-tolerance rule fires after five consecutive accepted steps with finite relative improvement in `[0,1e-6)`. The projected-gradient stationarity proxy is

```text
||Theta - Pi_333(Theta - grad F(Theta))||_F
  / max(||Theta||_F, 1),
```

where `Pi_333` is the identical deterministic rank-`(3,3,3)` projection and normalization operator. A start has `converged=True` only when it stops by the five-step objective-tolerance rule or has stationarity proxy at most `1e-4`, including at its initial iterate. Reaching the 300-iteration cap without either condition records `ITERATION_CAP` and is not convergence; a nonfinite objective or gradient records `NUMERICAL_FAIL` and is not convergence.

Start selection is restricted to starts that both converge and have a finite final training objective; among those eligible starts, it selects the smallest final training objective, breaking an exact objective tie by start order. Endpoint error never enters start selection. Every start's initial and final objective, accepted steps, objective trace, stationarity proxy, stopping reason, convergence status, runtime, and pairwise solution distance is stored. A row is eligible only if at least one finite converged start exists and every accepted objective step for the selected start is non-increasing within the frozen `1e-12` acceptance tolerance.

## Chronology And Leakage Contract

- Held-out endpoints are absent from estimator inputs, initialization, rank, penalty, stopping, and start selection.
- Endpoint pools read calibration predictors and topologies only, never outcomes, truth, or endpoint errors.
- All 24 validation positions use strictly rolling reconstruction prefixes.
- Evaluation targets cannot change any hyperparameter or earlier fit.
- Perturbing truth blocks or held-out endpoints must leave the candidate fit digest and selected hyperparameters bitwise unchanged.
- DGP, endpoint, optimizer, and confirmation streams are independently named and hashed.
- Screening and conditional confirmation remain separate and are never pooled.
- Numerical failures, lost endpoint support, instability, and non-convergence are retained as failures and are never filtered from the inferential unit.

For every seed, primary cell, held-out endpoint, and method, primary loss is the mean raw finite-horizon response error over the 36 evaluation dates. Estimated instability does not remove dates, and projected responses do not replace raw responses.

Secondary metrics include relative and absolute operator error, response/zero ratio, `W_ref` response error, observed-topology prediction RMSE, `M_ref` and `B` error, topology-slope error, instability, support and amplification diagnostics, runtime, memory, convergence traces, and multi-start solution distances. The truth-isolated `evaluate_method` API returns the method-level scientific payload because its frozen signature contains no seed or cell coordinates. The phase-locked experiment runner must attach `seed`, `rho`, `a3`, `eta`, and measured `peak_memory_bytes` from its frozen loop and resource-measurement context before writing each replication row. These fields may not be inferred from array contents, method seeds, truth, endpoints, or recovery results; a missing identity or memory measurement makes the row incomplete and non-scorable.

## Screening Gate

One unchanged candidate must pass all eight primary cells under seeds `240100-240109`:

1. both held-out endpoints have 100% availability;
2. all rows are finite and at least one optimizer start converges with a non-increasing accepted objective trace;
3. median relative operator error is below 1 at each endpoint;
4. median response/zero ratio is below 1 at each endpoint;
5. paired median raw-response improvement is at least 10% against every required comparator at each endpoint;
6. joint win rate against all three comparators is at least 80% at each endpoint;
7. the per-seed worst-held-out-endpoint median improvement is at least 10% for each comparator;
8. observed-topology prediction RMSE is no more than 5% worse than the best comparator;
9. `W_ref` raw-response error is no more than 5% worse than the best comparator.

The uniquely frozen calculations for each primary cell are as follows. Let `L(s,m,e)` be method `m`'s mean raw response loss over all 36 evaluation dates for seed `s` at held-out endpoint `e`. For comparator `b`, define paired improvement

```text
I(s,b,e) = 1 - L(s,candidate,e) / max(L(s,b,e), 1e-12).
```

Availability is evaluated first using the definition in `Supported Endpoints`; all ten seeds, both held-out endpoints, and all four required methods must be present. Any missing, unavailable, or nonfinite required row fails the cell and is not dropped or imputed. Candidate convergence requires at least one converged start and a finite non-increasing accepted objective trace in every seed-cell fit.

For gates 3 and 4, first compute each seed-method-endpoint metric over its 36 dates, then take the median over the ten seeds separately for each held-out endpoint; the candidate median must be strictly below 1. For gate 5, take `median_s I(s,b,e)` separately for every comparator and endpoint and require each value to be at least `0.10`.

For gate 6, define a seed-level joint win at endpoint `e` as

```text
J(s,e) = 1{L(s,candidate,e) < L(s,b,e) for all three comparators b}.
```

Ties are not wins. Require `mean_s J(s,e) >= 0.80` separately at both endpoints. For gate 7, compute `min_e I(s,b,e)` across the two held-out endpoints within each seed, then take its median over the ten seeds, separately for each comparator; each median must be at least `0.10`. The endpoint minimum therefore precedes the seed median.

For gate 8, compute each method's observed-topology prediction RMSE for each seed-cell, take the median over the ten seeds, and define the best comparator as the minimum of the three comparator medians. Require the candidate median to be at most `1.05` times that minimum. Gate 9 uses the same order for `W_ref` mean raw response error: compute the 36-date mean within seed and method, take the median over seeds, then compare the candidate median with `1.05` times the minimum comparator median. An exact comparator tie simply shares the minimum. `W_ref` remains a safety guardrail and does not enter gates 3-7 or the primary held-out claim.

Any primary-cell failure stops the track before confirmation. The matched layer, `eta=0.02`, `W_ref`, supplementary methods, or R006f cannot satisfy or rescue a failed primary gate.

## Conditional Confirmation Gate

Confirmation designs and outcomes may be generated only after the unchanged screening candidate passes every screening gate, all screening-construction and scientific-source hashes remain unchanged, and the inferential prerequisite below has been separately frozen. The initial construction phase stores confirmation seed identifiers and stream declarations as metadata only; it must not instantiate confirmation panels, predictors, outcomes, endpoint candidates, or support certificates because native endpoint support depends on the simulated confirmation panel. After the prerequisites pass, a separate hash-locked `confirmation_construction_gate_preoutcome.json` must construct the confirmation seed-cell endpoints exactly once before any confirmation fit or recovery evaluation. This is independent conditional confirmation of a candidate fixed after historical development and screening. It is not project-start, unconditional confirmatory error control, and no such claim may be made.

For screening construction, “outcome-free” means free of recovery evaluations, recovery metrics, promotion verdicts, serialized truth, and exposed true response targets. Native states are necessarily simulated to obtain predictors, but the support-only boundary returns predictors, topology, reference topology, the interpolation endpoint, and stream metadata only. The frozen `FitInputs` support API is satisfied with an immutable all-zero outcome sentinel that endpoint construction is prohibited from reading. DGP operators may be computed internally to simulate native states, but the construction boundary does not instantiate or return the truth bundle, actual outcomes, or the full truth-bearing endpoint panel.

The unchanged descriptive gates are applied to the 30 new seeds `250100-250129`. For each required comparator `b`, define

```text
d_s,b = min over 8 primary cells and 2 held-out endpoints
        log(max(loss_b,1e-12) / max(loss_candidate,1e-12))
```

Every seed must contribute all 16 finite cell-endpoint ratios for every comparator. Missing or unavailable rows and nonfinite losses or contrasts cause confirmation status `FAIL`, cannot be omitted or replaced, and prohibit computation of a gating p-value or median bound from a reduced sample. For threshold `q=log(1.10)`, let `k_b` be the number of the 30 seed contrasts strictly greater than `q`. A contrast exactly equal to `q` is a non-success. The exact one-sided p-value convention is

```text
p_b = Pr{Binomial(30, 0.5) >= k_b}.
```

Holm adjustment sorts the three raw p-values ascending, breaking an exact p-value tie by the frozen comparator order `anchor_local`, `anchor_fused_tv`, `anchor_split_tucker333`. At ordered position `i=1,2,3`, compare with `0.05/(4-i)` and stop rejecting at the first failure. For the comparator at ordered position `i`, the adjusted p-value is `min(1, max_{j<=i} ((4-j) p_(j)))`, mapped back to the frozen comparator order.

Promotion requires all three adjusted tests to reject and all three simultaneous median lower bounds to exceed `log(1.10)`. The approved plan says to obtain those bounds by inverting the sign test but does not freeze the confidence allocation, order-statistic indexing, treatment of equality at candidate bounds, or finite-sample rounding convention needed for a uniquely reproducible simultaneous lower bound. Those details are a frozen implementation prerequisite, not discretionary implementation detail. Confirmation is not authorized under this protocol until a separate pre-outcome specification fixes that algorithm, its tests, and its provenance hash. No screening result may be inspected to choose the convention.

Paired seed bootstrap intervals may be reported as secondary summaries but cannot replace the exact primary inference. The frozen secondary bootstrap uses NumPy `Generator(PCG64(260901))`, exactly 10,000 replicates, and joint resampling of the 30 confirmation-seed indices with replacement so the same sampled indices are used for all three comparators in each replicate. Its statistic is the median seed contrast for each comparator, and its two-sided interval is the 0.025 and 0.975 empirical quantiles using NumPy's `linear` quantile method. Bootstrap output must carry `audit_seed=260901`, `replicates=10000`, and `gating=false`; it cannot be evaluated as a promotion condition. Screening and confirmation summaries remain separate and cannot be pooled to rescue failure.

## Failure Interpretations

- Any screening failure: record `FAIL`; do not create an R006e-b estimator.
- Held-out pass with `W_ref` guardrail failure: query-specific diagnostic only.
- Interpolation pass and cross-family failure: in-family interpolation only.
- Fused-TV matches the candidate: no design-weighted Tucker contribution established.
- Split Tucker matches the candidate: no joint-estimation contribution established.
- Confirmation failure: screening remains exploratory and cannot enter a headline claim.
- Material multi-start disagreement: numerical recovery is unstable; no promotion.
- R006f cannot rescue R006e, promote its estimator, or convert an R006e failure into a recovery claim.

## Artifact And Provenance Contract

Formal screening outcome generation is prohibited until construction-only tests pass and a pre-outcome artifact hashes this protocol, executed code, dependencies, random streams, screening seeds, confirmation seed identifiers, chronological splits, grids, endpoint pools, and tolerances. The initial artifact constructs endpoint certificates only for screening seeds and contains no recovery outcomes. Confirmation panels and endpoint certificates are prohibited in the initial artifact. Formal confirmation remains additionally prohibited by the unresolved simultaneous-median-bound prerequisite in `Conditional Confirmation Gate` and requires its own later construction artifact after an unchanged screening pass.

R006e uses its own protocol, seed namespaces, code entry points, output directories, ledgers, and result-to-claim gates. The tracked protocol and eventual independent audit report are restricted to:

```text
refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md
refine-logs/R006E_RESULT_TO_CLAIM_AUDIT_20260716.md
```

All generated construction, screening, confirmation, diagnostic, result, checkpoint, and manifest artifacts are restricted to the two isolated output trees:

```text
output/high_impact_revision/r006e_native_supported_recovery/
output/high_impact_revision/r006e_native_supported_recovery_repeat/
```

The primary output uses the screening-only `construction_gate_preoutcome.json`; conditional `confirmation_construction_gate_preoutcome.json`; `screening_replications.csv`, `screening_summary.csv`, and `screening_results.json`; conditional `confirmation_replications.csv`, `confirmation_inference.csv`, and `confirmation_results.json`; JSONL diagnostics; `r006e_results.md`; and phase manifests. The repeat output contains only isolated duplicate artifacts and its manifests. Audit implementation is restricted to `scripts/experiments/r006e_result_claim_audit.py` and its focused test; other R006e implementation and tests remain under `scripts/experiments/r006e_*.py` and `scripts/experiments/test_r006e_*.py`. No generated outcome or raw-data artifact is committed or force-added.

The screening duplicate must match the primary screening replication, summary, and result payloads with zero differences after excluding exactly `runtime_seconds`, `peak_memory_bytes`, and `generated_at`. If confirmation is later authorized, the confirmation duplicate must likewise have zero differences across replication, summary, inference, and result payloads after excluding exactly those three fields. No identity, seed, cell, endpoint, method, metric, failure, support, convergence, selected-hyperparameter, contrast, p-value, bound, status, hash, or claim field is excluded. Runtime-like or timestamp fields under any other name are not automatically ignored.

R006c remains recorded as CP `0/16`, Tucker `6/16`, and native `0/8`; R006e artifacts never overwrite it. R006e does not modify R006d or R006f artifacts, the manuscript, claim ledger, figures, R007, or `N=50/100` experiments.

Bug fixes require a failing regression test, a new provenance hash, and a complete rerun. Outcome-informed threshold, endpoint, rank, or grid changes terminate this protocol version. Neither manuscript nor claim ledger may change until an independent duplicate and result-to-claim audit is complete.
