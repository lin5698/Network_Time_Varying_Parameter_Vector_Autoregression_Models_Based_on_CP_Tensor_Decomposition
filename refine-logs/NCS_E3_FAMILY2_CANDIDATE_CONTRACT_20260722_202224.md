# NCS E3 Family-2 Candidate Contract

Date: 2026-07-22

Status: `DRAFTED`, `SOURCE_ONLY`, `NOT_EXECUTABLE`.

Supersedes the fixed-name candidate contract derived from `NCS_E3_FAMILY2_CANDIDATE_CONTRACT_20260722_201758.md`. The earlier timestamped file is retained as history only. This revision incorporates an independent methods-review check that a two-hop-only formulation could be mistaken for an after-the-fact input relabelling.

This document defines no result and authorizes no scientific execution, data acquisition, dependency installation, outcome inspection, RCEP/NYC access, R006e/R006f activity, manuscript build or manuscript promotion. `PAPER_CLAIM_AUDIT=BLOCKED` and `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling. They cannot be changed by a protocol or an authorisation message; only their corresponding independent evidence audits can change them.

## Purpose And Claim Boundary

This is a candidate design for the future-only ledger items `C016` and `C017`. Its sole possible future contribution is a family-specific query contract:

> A declared query-preservation condition classifies topology-indexed readouts across the existing one-hop family and one independently specified second-order graph-filter family.

It does not establish universal query preservation, estimator superiority, cross-domain transfer, calibrated uncertainty, causal topology effects or NCS readiness. A future recovery claim remains conditional on E3-3 and E3-4 after separate authorization and audit.

## Topology And Endpoint Semantics

For every panel, $W\in\mathbb{R}^{N\times N}$ is an ordered weighted adjacency with a frozen node order and a frozen raw zero-diagonal convention. Any allowed normalization is applied once to $W$ before fitting and evaluation. The second-order term is defined exactly as

$$
W^2:=WW.
$$

The executor must not renormalize $W^2$, delete its diagonal, replace it with a graph feature, or fold it through an observed reference topology. A future exact manifest must record the topology preprocessing function, node-order hash and $W^2$ implementation.

Fix $S_\star=I_N$ as the common shock map, a lag order $p$, and a maximum horizon $H_{\max}$. For each date $t$ and supplied query topology $W_q$, the only rankable endpoint is the full operator-and-response object

$$
\mathfrak E^{(2)}_{t,H_{\max}}(W_q)=
\left(
\{G^{(2)}_{k,t}(W_q)\}_{k=1}^{p},
\{R^{(2)}_{t,h}(W_q)\}_{h=1}^{H_{\max}}
\right),
$$

where $R^{(2)}_{t,h}(W_q)=J\mathcal C^{(2)}_t(W_q)^hJ'$ and $\mathcal C^{(2)}_t(W_q)$ is the companion matrix formed from the declared Family-2 lag operators. A scalar ratio, a node ranking, a prediction, an embedding or a post-hoc response curve is not the primary endpoint. Family 1 uses the same endpoint structure with $A_{k,t}+B_{k,t}W_q$ in place of $G^{(2)}_{k,t}(W_q)$.

Within one fixed family/topology/scale/horizon cell, report only

$$
L_G=\frac{1}{pN^2}\sum_{k=1}^{p}\left\|\widehat G_k(W_q)-G_k^\star(W_q)\right\|_F^2,
\qquad
L_R=\frac{1}{H_{\max}N^2}\sum_{h=1}^{H_{\max}}\left\|\widehat R_h(W_q)-R_h^\star(W_q)\right\|_F^2.
$$

`OUTSIDE_TARGET` produces neither $L_G$ nor $L_R$. It is not zero, missing-at-random, imputed or rankable. `NONCONVERGED`, `NONFINITE` and `UNSTABLE` are distinct retained statuses. Pairwise errors are reported only on a pre-declared common-completion set alongside each method's complete failure rate.

## Family-2 Candidate And Exact Boundary

### Operator family

The candidate second family is the diagonal, finite graph-filter response operator

$$
G^{(2)}_{k,t}(W)=C_{0,k,t}+C_{1,k,t}W+C_{2,k,t}W^2,
\qquad
C_{j,k,t}=\operatorname{diag}(c_{j,k,t}).
$$

The three coefficient blocks must be stored and fitted separately. $C_2$ must have a pre-specified nonzero structural witness; it cannot be fixed to zero, absorbed into $C_1W$, or introduced only after inspecting outcomes. The unrestricted three-block class is used only for an exact structural negative fixture. The recovery comparison, if later authorized, is restricted to this declared diagonal class.

### Candidate diagonal factorization criterion

Suppress lag and date subscripts. Let the stored collapsed object be

$$
D=C_0+C_1W_0+C_2W_0^2.
$$

For row $i$, let $e_i$ be the $i$th standard basis vector, let

$$
X_i(W)=\left[e_i,\;W_{i,:}^{\mathsf T},\;(W^2)_{i,:}^{\mathsf T}\right]\in\mathbb{R}^{N\times3},
\qquad
d_i^{\mathsf T}=X_i(W_0)c_i,
$$

where $c_i=(c_{0i},c_{1i},c_{2i})^{\mathsf T}$. The future proof audit must establish, without relying on floating-point rank, the candidate condition

$$
Q^{(2)}_{W_q}\text{ factors through }T^{(2)}_{W_0}
\quad\Longleftrightarrow\quad
\ker X_i(W_0)\subseteq\ker X_i(W_q)\ \text{for every }i.
$$

The positive structured case is explicit: if $\operatorname{rank}X_i(W_0)=3$ for every $i$, the collapsed object identifies $c_i$ rowwise and hence evaluates any supplied query in this diagonal class. This is a representation result only. It does not establish design identification, numerical recovery, stability or estimator superiority.

### Non-equivalence condition

Family 2 must not be relabelled as the one-hop family. The proof/fixture audit must show that the nonzero-second-order instance $G(W)=W^2$ cannot equal one fixed $A+BW$ on the pre-specified topology set $\{0,V,2V\}$, where

$$
V=\begin{pmatrix}0&1\\1&0\end{pmatrix}.
$$

At $W=0$, equality gives $A=0$; at $W=V$, it gives $BV=I$; at $W=2V$, the one-hop map gives $2I$ while $W^2=4I$. A candidate fails before execution if it removes this witness, transforms the supplied input to $W^2$ before defining the query, or evaluates a first-order surrogate.

## Exact No-Outcome Fixtures

All fixtures use rational or integer matrices and must be checked algebraically. A future implementation may add a `float64` check with maximum absolute error no greater than $10^{-12}$, but floating-point agreement cannot substitute for the proof.

| Fixture | Fixed construction | Required status | What it prevents |
| --- | --- | --- | --- |
| F1 structural negative | $P=\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix}$, $W_0=P$, $W_q=P^2$; worlds $(A,B)=(0,0)$ and $(-P,I)$ | Family 1 collapsed query is `OUTSIDE_TARGET` | Treating different raw topologies as interchangeable in $A+BW$. |
| F2 unrestricted structural negative | Same $P,W_0,W_q$; worlds $(C_0,C_1,C_2)=(0,0,0)$ and $(-P-2P^2,I,2I)$ | Family 2 collapsed query is `OUTSIDE_TARGET` | Claiming that a three-block filter is universally evaluable after collapse. |
| F2 diagonal structural negative | $W_0=\begin{bmatrix}0&1&0\\0&0&0\\0&0&0\end{bmatrix}$, $W_q=\begin{bmatrix}0&1&0\\0&0&1\\0&0&0\end{bmatrix}$; compare zero blocks with $C_2=\operatorname{diag}(1,0,0)$ | Family 2 diagonal query is `OUTSIDE_TARGET` | Misapplying the positive structured inverse to rank-deficient rows. |
| F2 diagonal structured positive | $W_0=P$, $W_q=P^2$, all three blocks diagonal | `AVAILABLE through identified inverse` because every $X_i(P)$ has rank three | Applying unrestricted counterexamples to every diagonal implementation. |
| Executor guard | Supply a collapsed-only object to the Family-2 evaluator | Refuse before response/error construction | A software path that silently invents $C_0,C_1,C_2$ from $D$. |

For the unrestricted F2 negative fixture, both worlds collapse to zero at $P$, while their queried operators at $P^2$ differ by $P-P^2\neq0$. For the diagonal F2 negative fixture, $W_0^2=0$ but $(W_q^2)_{13}=1$, so a hidden $C_2$ direction changes the query. These are expected exact classifications, not experimental results.

## Same-Endpoint Comparator Contract

E3-2 remains unavailable until the E3-1 proof and fixture audits pass. Each ranked system must implement the same pre-registered interface:

```text
fit(training histories, observed training topologies, frozen hyperparameters)
evaluate(fitted_state, W_q, H_max) -> {G_1:p(W_q), R_1:Hmax(W_q), status}
```

| System | Required native state/output | Eligible only when | Ineligible when |
| --- | --- | --- | --- |
| Native local structured fit | All $C_0,C_1,C_2$ blocks and direct evaluator | Fits direct, one-hop and two-hop exposure blocks in the declared node order | Stores only $G(W_0)$ or refits at $W_q$. |
| Causal temporal structured smoother | Smoothed paths for all three block tensors | Smoothing precedes every query and preserves the coefficient-block mode | Smooths a collapsed map or recovers blocks after smoothing. |
| Fixed low-rank/basis candidate | Retained three-block coefficient tensor and direct evaluator | Candidate family, block mode, tuning list and tie-break are frozen before outcomes | Rank/basis/endpoints change after response truth or evaluation outcomes are visible. |
| Collapsed graph-filter map | $D=C_0+C_1W_0+C_2W_0^2$ only | Availability negative control only | Any $L_G$, $L_R$, rank, win rate or headline comparison. |
| GNN, graph-feature or diffusion model | No current eligible form | Only after an independently reviewed native evaluator returns the exact full endpoint without projection | Any feature-to-block projection, response adapter or reference-topology folding. |

All eligible systems must use the same input histories, chronological train/validation/evaluation partition, query topology, horizons, $S_\star$, stability rule, random streams, iteration cap, hardware record and failure retention. Hyperparameters may use only the common time-ordered validation region and observed-topology one-step prediction loss. That loss selects an implementation; it is not topology-response recovery evidence and must never inspect held-out topology truth, held-out response truth or evaluation metrics. The exact grids, maximum candidate count $B$, seed schedule and tie-break remain unset in this draft and are mandatory fields of the later pre-outcome manifest.

## Required Pre-Outcome Artifacts

Before a scientific invocation can be proposed, all of the following must exist and pass static review:

1. `family2_query_contract`: node order, one-time topology normalization, $W^2$ semantics, $p$, $H_{\max}$, $S_\star=I_N$ and status schema.
2. `family2_factorization_proof_packet`: the unrestricted negative fixture, the diagonal kernel-inclusion theorem, the rank-three structured-positive case and the non-equivalence witness.
3. `exact_fixture_manifest`: all matrix fixtures, expected symbolic classifications, tolerance and hard-rejection rules.
4. `comparator_registry`: source identities, parameterization, the `fit/evaluate` interface, endpoint shapes and a native-ness proof for every ranked method.
5. `tuning_split_manifest`: chronological partitions, all candidate lists, maximum budget $B$, tie-break and independent random streams.
6. `failure_metric_schema`: mutually exclusive `AVAILABLE`, `OUTSIDE_TARGET`, `NONCONVERGED`, `NONFINITE` and `UNSTABLE` records, with no numerical metric for unavailable endpoints.
7. `authorization_gate_tests`: a hard refusal before any generator, estimator, response evaluator, outcome writer or scientific output directory exists when authorization/trust evidence is absent or mismatched.
8. `duplicate_and_claim_audit_design`: an isolated duplicate and an independent result-to-claim audit bound to the eventual same manifest.

## Future One-Time Execution Authorization

This file requests no authorization. A future explicit approval can authorize one invocation only after a reviewed candidate SHA-256 exists. That candidate must bind the exact runner, source/dependency hashes, all pre-outcome artifact hashes, synthetic-only input route, scales, panel lengths, horizons, seeds, topology generators, splits, tuning budget, comparator roster and a new quarantine output root.

It must also bind a production trust verifier whose absence or failure stops before science, and explicitly prohibit RCEP/NYC access, R006e/R006f access, manuscript promotion, downstream builds, result use and audit-status changes. Any result remains quarantine material until its prescribed duplicate and independent audits pass and a separate promotion authorization is granted.

## Stop Conditions

Stop before execution if any of the following is true:

1. $W^2$ is re-normalized, projected, folded through $W_0$, or otherwise differs from the declared $WW$ calculation.
2. The non-equivalence witness, unrestricted negative fixture, diagonal negative fixture or rank-three positive fixture fails its exact audit.
3. A ranked comparator does not return the complete declared endpoint natively.
4. Endpoint selection, hyperparameter choice, topology generator, seed, horizon or candidate identity depends on held-out truth or outcomes.
5. A failure, unstable path, unavailable endpoint or non-finite value is replaced, omitted, redrawn or converted to a numerical score.
6. Any party treats completion of this contract as evidence for `C016` or `C017`, or as permission to alter the two controlling audit verdicts.

## Current Decision

This source-only candidate improves the experimental path but supplies no new evidence. E3-1 through E3-5 remain `NOT_AUTHORIZED` or `BLOCKED`; the paper remains restricted to its current theorem, bounded controlled benchmark and endpoint-aware negative result.
