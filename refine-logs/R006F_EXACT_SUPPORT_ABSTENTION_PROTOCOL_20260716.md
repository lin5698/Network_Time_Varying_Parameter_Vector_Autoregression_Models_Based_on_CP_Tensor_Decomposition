# R006f Exact-Support Abstention Protocol

**Date:** 2026-07-16  
**Status:** Frozen construction protocol; formal paired outcomes are not authorized  
**Approved source:** `docs/superpowers/specs/2026-07-16-r006e-r006f-dual-track-design.md`  
**Parent evidence:** corrected R006c `FAIL`; R006d `CONSTRUCTION_FAIL`

## 1. Claim boundary

The sole R006f claim under test is:

> In a fixed low-dimensional design with a known excitation subspace, an exact query-support certificate accepts supported topology queries and abstains on a prespecified unsupported query; paired observationally indistinguishable coefficient worlds show why a numerical unsupported readout is not data-identified.

R006f tests identification and abstention only. It does not establish estimator recovery or predictive superiority, CP or Tucker superiority, topology-switch recovery in a dynamic VAR, causal effects, empirical generality, calibrated uncertainty, temporal-GNN performance, or scaling beyond `N=6`. It cannot promote a recovery estimator, alter the R006c/R006e method verdict, repair an R006e failure, overwrite prior evidence, or authorize a manuscript claim.

This protocol version authorizes construction and construction-only tests. It does **not** authorize formal paired-outcome generation, a formal `PASS`, or a result-to-claim decision. Formal paired outcomes require a later unchanged pre-outcome artifact that hashes this protocol, code, dependencies, random streams, seeds and tolerances.

## 2. Fixed-design and self-loop convention

The experiment is a fixed-design regression stress test with `N=6`, excitation rank `r=2`, and `T=96`. A dynamic outer shell is excluded because recursion stability and initialization would confound the exact identification question.

Self-loops are allowed. Every topology must be non-negative and row-stochastic. No topology may be nonlinearly renormalized. There is no candidate pool, redraw, random rotation, sign selection, or recovery-conditioned query selection.

## 3. Exact DCT construction

Let `q0,...,q5` be the orthonormal DCT-II basis on six nodes, ordered by frequency, with `q0 = 1/sqrt(N) 1`. Freeze

```text
U = [q1,q2]
u_perp = q3
v1 = q4
v2 = q5
W_ref = 11'/N
```

For `t=0,...,95`, define

```text
f_k(t) = sqrt(2/T) cos(pi (t+1/2) k / T),  k=1,...,7
h_t = [f_6(t), f_7(t)]'
x_t = q4 + f_1(t) q0 + f_2(t) q1 + f_3(t) q2
          + f_4(t) q3 + f_5(t) q5
```

The direct-design time span is orthogonal to the excitation span and `v1' x_t=1` exactly. For excitation level `c in {1,0.25}`, set

```text
W_t = W_ref + epsilon_c U h_t v1'
epsilon_strong = 1 / (4 N max_t ||U h_t v1'||_infinity)
epsilon_weak = epsilon_strong / 4
```

Consequently,

```text
(W_t-W_ref)x_t = epsilon_c U h_t
Z_tilde = Z
row(Z_tilde) = span(U)
ker(Z_tilde) = span(U_perp)
```

The construction gate checks topology non-negativity and row sums directly, without renormalization.

## 4. Frozen topology queries

Freeze

```text
epsilon_star = 1 /
  (4 N max(||q1 v2'||_infinity, ||u_perp v2'||_infinity))
Delta W_sup = epsilon_star q1 v2'
Delta W_unsup = epsilon_star u_perp v2'
```

The exact targets are `chi_sup=0` and `chi_unsup=1`. Query classification uses the fixed threshold `chi<=0.05`. Changing this threshold terminates this protocol version.

## 5. Paired indistinguishable worlds

Freeze the two coefficient worlds as

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

Both truth labels share the same fixed design and identical noise draw for a given seed and excitation level. Since `u_perp' U=0`, their observed training datasets are identical. Supported-query truth is identical. Unsupported-query truth differs by the nonzero analytic gap

```text
(B1-B0) Delta W_unsup = beta epsilon_star a v2'.
```

An estimator that always answers must incur at least half this gap in one of the two observationally indistinguishable worlds.

## 6. Estimators and numerical controls

1. Certificate-aware FWL min-norm OLS estimates the supported projection and returns a query only when `chi<=0.05`.
2. Silent min-norm OLS uses the identical fit but always returns a numerical value.
3. Oracle supported projection is a decomposition diagnostic only.

No CP, Tucker, GNN, predictive, or recovery-superiority comparison is permitted. The numerical certificate freezes `kappa_max=50` and

```text
tau = max(1e-12, s_max/50).
```

Both the exact projector and SVD projector must be stored. The fixed scalar controls are `(m_scale,b0_scale,beta,sigma)=(0.20,0.15,0.50,0.05)`.

## 7. Seeds and paired units

Paired noise seeds are exactly `620001-620050`, inclusive. Each of the 50 seeds is evaluated at excitation scales `(1.0,0.25)`. Within each seed-level pair, both coefficient-world labels use one shared observed dataset and the same noise stream. No seed may be dropped, replaced, redrawn, or filtered after a numerical failure.

## 8. Frozen gates

### Construction and identification gate

Every seed and excitation level must satisfy:

- topology row-sum error at most `1e-12` and no negative entry;
- `rank(Z_tilde)=2`;
- projector error `||P_hat-UU'||_F <= 1e-10`;
- `chi_sup <= 1e-10` and `chi_unsup >= 1-1e-10`;
- paired observed-data difference at most `1e-12`;
- supported truth gap at most `1e-12`;
- unsupported truth gap agrees with the analytic gap within relative error `1e-10`.

### Certificate behavior gate

At each excitation level, certificate-aware behavior requires 50/50 supported returns, 50/50 unsupported abstentions, zero false support, and zero false abstention.

### Excitation gate

The two excitation levels must have unchanged `chi`; weak singular values must equal one quarter of strong singular values; inverse amplification must be four times larger under weak excitation; and the frozen same-noise supported-query error relation must match analytic scaling within `1e-8`.

### Lower-bound and decomposition gate

For every seed, the silent always-answer estimator must satisfy the paired-world half-gap lower bound. Decomposition residuals must be at most `1e-10`.

## 9. Stop rules

- A topology, rank, projector, or exact-query construction failure records `CONSTRUCTION_FAIL` and stops the track.
- Any classification that requires changing the threshold terminates this protocol version.
- Non-identical paired training data prohibits a non-identifiability claim.
- An unsupported truth gap below its frozen analytic value means the mechanism was not activated.
- A certificate gate failure records `FAIL`; endpoints may not be relabeled.
- Numerical failure, instability, or non-convergence is retained as failure and never filtered from the inferential unit.
- Outcome-informed changes to thresholds, queries, rank, excitation levels, seeds, or grids terminate this protocol version.
- R006e failure cannot be cited as repaired by R006f, and the tracks cannot rescue one another.

Bug fixes require a failing regression test, a new provenance hash, and a complete rerun. Screening or development evidence cannot be pooled with later formal outcomes.

## 10. Components and output isolation

Components remain separated into exact DCT construction, topology validation, paired-world generation, exact and numerical projectors, certificate-aware evaluation, silent evaluation, analytic lower-bound checking, and provenance audit. Each uses a narrow serialized interface. Construction artifacts contain no recovery or paired-outcome results; later outcome artifacts must consume immutable construction hashes and refuse to run on a mismatch.

The only authorized R006f paths are:

```text
refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md
scripts/experiments/r006f_exact_design.py
scripts/experiments/test_r006f_exact_design.py
output/high_impact_revision/r006f_exact_support_abstention/
output/high_impact_revision/r006f_exact_support_abstention_repeat/
```

R006f uses code entry points, seed namespaces, output directories, ledgers, and result-to-claim gates separate from R006e. It must not edit the manuscript or claim ledger before an independent result-to-claim audit. This construction-only authorization does not permit creating either formal outcome directory or running the formal paired outcomes.
