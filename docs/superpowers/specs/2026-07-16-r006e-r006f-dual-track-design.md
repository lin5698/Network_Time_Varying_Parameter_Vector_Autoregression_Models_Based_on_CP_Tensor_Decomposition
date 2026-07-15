# R006e/R006f Dual-Track Experiment Design

**Date:** 2026-07-16  
**Status:** Approved design; no formal outcome generation authorized by this document  
**Parent evidence:** corrected R006c `FAIL`; R006d `CONSTRUCTION_FAIL`  
**Scientific boundary:** R006e and R006f are independent experiments. Neither track may rescue a failure in the other.

## 1. Purpose and claim separation

The current manuscript supports a representation-level claim: a fitted object must retain the topology argument, or an identified inverse to separated blocks, before topology-substitution responses are defined. It does not currently support broad estimator-level topology-switch recovery. The two new tracks test different missing links.

### R006e primary claim

In the frozen `N=20`, `T=200` native endogenous VAR simulation regime, one fixed design-weighted joint Tucker estimator improves finite-horizon response recovery at two never-fitted, design-supported topology endpoints relative to three fixed same-target comparators.

This claim is limited to the frozen DGP, horizon 8, native layer and support-conditioned endpoints. It does not imply CP superiority, universal topology-switch recovery, causal effects, empirical generality, calibrated uncertainty, native temporal-GNN superiority or scaling beyond `N=20`.

### R006f primary claim

In a fixed low-dimensional design with a known excitation subspace, an exact query-support certificate accepts supported topology queries and abstains on a prespecified unsupported query; paired observationally indistinguishable coefficient worlds show why a numerical unsupported readout is not data-identified.

R006f tests identification and abstention only. It cannot promote a recovery estimator or alter the R006c/R006e method verdict.

## 2. Shared governance

1. R006c remains recorded as CP `0/16`, Tucker `6/16` and native `0/8`; new artifacts never overwrite it.
2. The two tracks use separate protocol files, seed namespaces, code entry points, output directories, ledgers and result-to-claim gates.
3. Formal outcomes are prohibited until construction-only tests pass and a pre-outcome artifact hashes the protocol, code, dependencies, random streams, seeds, splits and tolerances.
4. Screening and confirmation remain separate. Screening results cannot be pooled with confirmation.
5. Numerical failures, lost endpoint support, instability and non-convergence are retained as failures, never filtered from the inferential unit.
6. Bug fixes require a failing regression test, a new provenance hash and a complete rerun. Outcome-informed threshold, endpoint, rank or grid changes terminate the current protocol version.

## 3. R006e native supported-endpoint recovery

### 3.1 Frozen DGP and primary cells

R006e inherits the corrected R006c native endogenous VAR construction:

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

The matched layer and `eta=0.02` may be retained only as mechanism diagnostics. They cannot satisfy or rescue a primary gate.

### 3.2 Endpoints

`W_ref` is the reference safety endpoint. It does not enter the primary held-out claim.

`W_alt_interp` is generated once per seed-cell from an independent stream:

```text
row_normalize(0.75 W_ref + 0.25 W_holdout_ER)
```

No redraw is allowed if the endpoint produces an unfavorable result.

`W_alt_family` is selected from the frozen 64-member directed degree-corrected SBM pool inherited from R006d. Selection uses calibration predictors and topologies only. The endpoint is the lowest-index candidate satisfying `max chi_tau <= 0.10`. If none passes, the seed-cell is a construction failure. The selected endpoint is not replaced if prospective validation or evaluation support later fails.

The cross-family result must be described as support-conditioned. It is not evidence for an arbitrary unseen network family.

### 3.3 Support and amplification diagnostics

For direct design `X`, topology exposure design `Z` and query difference `Delta W`:

```text
Z_tilde = (I - X X_dagger) Z
tau = max(1e-10, s_max / 50)
chi_tau = ||Delta W' (I-P_tau)||_F / max(||Delta W'||_F, 1e-12)
```

The stored design diagnostics include the full singular spectrum, absolute retained singular values, condition number, `chi_tau` and query amplification. Full numerical rank is not interpreted as accurate recovery.

### 3.4 Compared systems

The sole promotion candidate is `dw_joint_tucker333`:

- fitted object `Theta_t=[M_ref,t, B_t]`;
- normalized rolling outcome loss using the realized design;
- Tucker rank fixed at `(3,3,3)`;
- temporal penalty `lambda_T in {0, 0.01, 0.05, 0.20}`;
- three deterministic starts, frozen backtracking, 300-iteration cap and R006d convergence diagnostics;
- no unsupported-direction penalty because the primary R006e question contains supported endpoints only.

Required same-target comparators are:

1. `anchor_local`: scale-adaptive rolling ridge for `[M_ref,B]`;
2. `anchor_fused_tv`: strictly chronological four-penalty fused-TV smoothing of the anchor-local path;
3. `anchor_split_tucker333`: the fixed R006c rank-3 split reconstruction of `M_ref` and `B`.

Block-parameterized methods may appear as supplementary diagnostics only. Oracle methods use a separate API and cannot be passed into the promotion fit path.

### 3.5 Chronology and leakage contract

- Held-out endpoints are absent from estimator inputs, initialization, rank, penalty, stopping and start selection.
- Endpoint pools read calibration predictors and topologies only, never outcomes, truth or endpoint errors.
- All 24 validation positions use strictly rolling reconstruction prefixes.
- Evaluation targets cannot change any hyperparameter or earlier fit.
- Perturbing truth blocks or held-out endpoints must leave the candidate fit digest and selected hyperparameters bitwise unchanged.
- DGP, endpoint, optimizer and confirmation streams are independently named and hashed.

### 3.6 Screening and confirmation seeds

Development screening uses `240100-240109`. These seeds have influenced prior method design and cannot support a confirmatory claim.

Confirmation uses the newly frozen IDs `250100-250129`. The seed is the clustered inferential unit across all eight cells. Confirmation outcomes may be generated only after an unchanged screening pass.

### 3.7 Primary estimand and stored metrics

For every seed, cell, endpoint and method, primary loss is the mean raw finite-horizon response error over the 36 evaluation dates. Estimated stability does not remove dates and projected responses do not replace raw responses.

For comparator `b`, the confirmation contrast is:

```text
d_s,b = min over 8 primary cells and 2 held-out endpoints
        log(max(loss_b,1e-12) / max(loss_candidate,1e-12))
```

Secondary metrics include relative and absolute operator error, response/zero ratio, `W_ref` response error, observed-topology prediction RMSE, `M_ref` and `B` error, topology-slope error, instability, support/amplification diagnostics, runtime, memory, convergence traces and multi-start solution distances.

### 3.8 Screening gate

One unchanged candidate must pass all eight primary cells:

1. both held-out endpoints have 100% availability;
2. all rows are finite and at least one optimizer start converges with a non-increasing accepted objective trace;
3. median relative operator error is below 1 at each endpoint;
4. median response/zero ratio is below 1 at each endpoint;
5. paired median raw-response improvement is at least 10% against every required comparator at each endpoint;
6. joint win rate against all three comparators is at least 80% at each endpoint;
7. the per-seed worst-held-out-endpoint median improvement is at least 10% for each comparator;
8. observed-topology prediction RMSE is no more than 5% worse than the best comparator;
9. `W_ref` raw-response error is no more than 5% worse than the best comparator.

Any primary-cell failure stops the track before confirmation.

### 3.9 Confirmation gate

The unchanged descriptive gates are applied to 30 new seeds. For the three `d_s,b` contrasts, exact one-sided sign inference tests improvement beyond `log(1.10)`. Holm adjustment controls familywise error at 0.05. Promotion requires all three adjusted tests to reject and all three simultaneous median lower bounds to exceed `log(1.10)`.

Paired seed bootstrap intervals may be reported as secondary summaries but cannot replace the exact primary inference.

### 3.10 R006e stop interpretations

- Any screening failure: record `FAIL`; do not create an R006e-b estimator.
- Held-out pass with `W_ref` guardrail failure: query-specific diagnostic only.
- Interpolation pass and cross-family failure: in-family interpolation only.
- Fused-TV matches the candidate: no design-weighted Tucker contribution established.
- Split Tucker matches the candidate: no joint-estimation contribution established.
- Confirmation failure: screening remains exploratory and cannot enter a headline claim.
- Material multi-start disagreement: numerical recovery is unstable; no promotion.

## 4. R006f exact-support abstention

### 4.1 Scope and fixed-design choice

R006f is a fixed-design regression stress test with `N=6`, excitation rank `r=2` and `T=96`. A dynamic outer shell is intentionally excluded because it would mix the exact identification question with recursion stability and initialization. Self-loops are allowed. Every topology must be non-negative and row-stochastic; nonlinear renormalization is prohibited.

### 4.2 Exact construction

Let `q0,...,q5` be the orthonormal DCT-II basis on six nodes, ordered by frequency, with `q0=1/sqrt(N) 1`. No random rotation or sign selection is allowed. Define:

```text
U = [q1,q2]
u_perp = q3
v1 = q4
v2 = q5
W_ref = 11'/N
```

For `t=0,...,95`, define normalized time columns

```text
f_k(t) = sqrt(2/T) cos(pi (t+1/2) k / T),  k=1,...,7
h_t = [f_6(t), f_7(t)]'
x_t = q4 + f_1(t) q0 + f_2(t) q1 + f_3(t) q2
           + f_4(t) q3 + f_5(t) q5
```

The direct-design time span is therefore orthogonal to the excitation span, and `v1' x_t=1` exactly. Training topology is:

```text
W_t = W_ref + epsilon_c U h_t v1'
c in {1, 0.25}
```

The predictor path is constructed so that `v1' x_t=1`. Consequently:

```text
(W_t-W_ref)x_t = epsilon_c U h_t
Z_tilde = Z
row(Z_tilde) = span(U)
ker(Z_tilde) = span(U_perp)
```

`epsilon_strong` is the deterministic entrywise bound

```text
1 / (4 N max_t ||U h_t v1'||_infinity)
```

and `epsilon_weak=epsilon_strong/4`. The construction gate verifies non-negativity and row sums without renormalization.

### 4.3 Fixed queries

```text
Delta W_sup = epsilon_star q1 v2'
Delta W_unsup = epsilon_star u_perp v2'
```

The query scale is frozen as

```text
epsilon_star = 1 /
  (4 N max(||q1 v2'||_infinity, ||u_perp v2'||_infinity))
```

The exact target is `chi_sup=0` and `chi_unsup=1`. No candidate pool, redraw or recovery-conditioned selection is allowed.

### 4.4 Paired indistinguishable worlds

Freeze the regression worlds as:

```text
M = 0.20 I_N
B0 = 0.15 I_N
beta = 0.50
a = q0
B1 = B0 + beta a u_perp'
sigma = 0.05
y_t = M x_t + B_k (W_t-W_ref) x_t + sigma xi_t
xi_t ~ N(0,I_N), keyed only by the paired seed
```

With identical noise draws, `u_perp' U=0` makes the two fixed-design training datasets identical. Supported-query truth is identical, while unsupported-query truth differs by the nonzero analytic gap:

```text
(B1-B0) Delta W_unsup = beta epsilon_star a v2'
```

An always-answer estimator must incur at least half this gap in one of the two indistinguishable worlds.

### 4.5 Estimator and controls

1. Certificate-aware FWL min-norm OLS estimates the supported projection and returns a query only when `chi<=0.05`.
2. Silent min-norm OLS uses the same fit but always returns a number.
3. Oracle supported projection is a decomposition diagnostic only.

No CP, Tucker or GNN comparison is included because R006f does not test predictive or recovery superiority.

The numerical certificate uses `kappa_max=50` and `tau=max(1e-12,s_max/50)`. Both the exact projector and SVD projector are stored.

### 4.6 Seeds and primary gates

Paired noise seeds are `620001-620050`. Each seed and excitation level creates one observed dataset shared by both truth labels.

Construction and identification require:

- topology row-sum error at most `1e-12` and no negative entry;
- `rank(Z_tilde)=2`;
- projector error `||P_hat-UU'||_F <= 1e-10`;
- `chi_sup <= 1e-10` and `chi_unsup >= 1-1e-10`;
- paired observed-data difference at most `1e-12`;
- supported truth gap at most `1e-12`;
- unsupported truth gap matches the analytic gap within relative error `1e-10`.

Certificate behavior requires 50/50 supported returns, 50/50 unsupported abstentions, zero false support and zero false abstention at both excitation levels.

The excitation check requires unchanged `chi`, weak singular values equal to one quarter of strong singular values, inverse amplification four times larger under weak excitation, and the frozen same-noise supported-query error relation to match the analytic scaling within `1e-8`.

The silent estimator must satisfy the paired-world half-gap lower bound for every seed. Decomposition residuals must be at most `1e-10`.

### 4.7 R006f stop interpretations

- Topology, rank, projector or exact-query construction failure: `CONSTRUCTION_FAIL`.
- Classification requiring a changed threshold: terminate the protocol.
- Non-identical paired training data: no non-identifiability claim.
- Unsupported truth gap below its frozen analytic value: mechanism not activated.
- Certificate gate failure: `FAIL`; do not relabel endpoints.
- R006e failure cannot be cited as repaired by R006f.

## 5. Components and data flow

R006e components are split into: construction/splits, support-only endpoint selection, candidate fitting, comparator fitting, endpoint-blind evaluation, screening gate, confirmation inference and provenance audit. Truth and oracle controls are isolated from all promotion-fit APIs.

R006f components are split into: exact basis/DCT construction, topology validation, paired-world generator, exact and numerical projectors, certificate-aware evaluator, silent evaluator, analytic lower-bound checker and provenance audit.

Each component has a narrow serialized interface. Construction artifacts contain no recovery outcomes. Outcome artifacts consume immutable construction hashes and refuse to run if any hash differs.

## 6. Testing strategy

Before outcome generation, tests must cover:

- exact chronology and disjoint regions;
- endpoint absence from fitting and tuning APIs;
- truth perturbation invariance of R006e candidate digests;
- calibration-only endpoint selection and no replacement;
- strict rolling-prefix validation;
- deterministic optimizer starts and monotone accepted objectives;
- equal declared tuning budgets;
- exact R006f topology constraints, rank, projector and query classification;
- paired-world observational identity and analytic truth gap;
- deterministic seeds and output hashes;
- smoke runs cannot emit formal `PASS` or manuscript claims.

## 7. Output isolation

```text
refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md
refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md
output/high_impact_revision/r006e_native_supported_recovery/
output/high_impact_revision/r006e_native_supported_recovery_repeat/
output/high_impact_revision/r006f_exact_support_abstention/
output/high_impact_revision/r006f_exact_support_abstention_repeat/
```

Neither track edits the manuscript or claim ledger until an independent result-to-claim audit is complete.

## 8. Implementation sequence

1. Write separate protocol documents from this design.
2. Write construction and leakage tests before estimator/outcome code.
3. Implement R006f construction and exact algebra; run construction-only gate.
4. Implement the R006e endpoint-blind candidate and same-target baselines; benchmark objective-only iteration cost without formal DGP outcomes.
5. If full 24-prefix execution is infeasible, stop and return to a new protocol version before any formal outcome. This design does not authorize reducing the prefix set.
6. Freeze and hash both pre-outcome artifacts.
7. Run R006f formal paired outcomes and audit them independently.
8. Run R006e screening only. Run confirmation only after every unchanged screening gate passes.
9. Run independent duplicate and result-to-claim audits before any manuscript change.
