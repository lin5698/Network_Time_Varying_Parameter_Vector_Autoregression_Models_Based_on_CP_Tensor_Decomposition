# NCS E3 Synthetic Execution Design v1

Date: 2026-07-23

Status: `DRAFTED`, `SYNTHETIC_ONLY`, `PRE_OUTCOME`.

This design freezes a future synthetic E3 route. It is not an execution
authorization, a result, an audit pass, a manuscript promotion, or a change to
`PAPER_CLAIM_AUDIT=BLOCKED` or `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`. It
prohibits RCEP, NYC, R006e and R006f access.

## Purpose and evidence boundary

The route tests four separable questions in order.

| Block | Question | Eligible future conclusion | Explicitly excluded conclusion |
| --- | --- | --- | --- |
| E3-1 | Does the pre-specified factorization rule classify the one-hop and second-order families? | The stated classification holds for the two specified finite-basis families. | Universal query preservation or recovery superiority. |
| E3-2 | Do all ranked methods natively return the same full endpoint? | The comparison is endpoint-comparable. | That any method is superior. |
| E3-3 | Does recovery persist across held-out topology class, scale and horizon? | Recovery is bounded to the reported synthetic operating cells. | Transfer beyond the reported cells or domains. |
| E3-4 | Are response intervals calibrated under a fixed stability rule? | Coverage and stability are reported for the declared synthetic procedure. | Calibrated uncertainty in unrestricted settings. |

Failure of an earlier block stops later execution and leaves its evidence state
unchanged. No successful result may offset a failed or unavailable declared
cell.

## Fixed operator and endpoint contract

Every run uses ordered, weighted, zero-diagonal adjacency matrices. Each
topology is normalized once by its maximum absolute row sum before it enters a
model; the second-order term is then computed exactly as `W @ W`, with no
post-square normalization, diagonal deletion, projection or reference-topology
substitution.

The two pre-specified families are

\[
G^{(1)}_t(W)=A_t+B_tW,\qquad
G^{(2)}_t(W)=C_{0,t}+C_{1,t}W+C_{2,t}W^2,
\]

where every coefficient block is diagonal. Family 2 has a non-zero
second-order block in every simulated panel. The execution uses lag order
`p=1`, shock map `I_N`, and the full endpoint

\[
\mathfrak E_{t,H}(W_q)=\left(G_t(W_q),\{G_t(W_q)^h\}_{h=1}^{H}\right).
\]

The headline horizons are `H=4` and `H=12`. The primary numerical losses are
the unnormalised operator and response mean squared Frobenius errors over the
declared endpoint. A method may be ranked only when it reports this endpoint
natively from retained coefficient blocks. `OUTSIDE_TARGET`, `NONCONVERGED`,
`NONFINITE`, and `UNSTABLE` have no numerical loss.

## Synthetic data-generating process

The process has `T=144` observations per independent panel, with fixed
chronological regions: train `1:72`, validation `73:96`, and evaluation
`97:144`. The outcome equation is

\[
y_t=G_t(W_t)y_{t-1}+\varepsilon_t,
\]

with independent Gaussian innovations of fixed standard deviation `0.08`.
Each diagonal coefficient path is a pre-specified bounded sinusoid plus a
panel-specific offset generated before fitting. The coefficient bounds are
fixed so the induced truth operator is in the declared stable regime for all
generated observed and held-out topologies; the runner must nevertheless
calculate and retain the actual spectral-radius diagnostic for every truth and
estimated endpoint.

Observed topologies use a directed sparse weighted generator with a fixed
support seed and smooth time variation. Two query topologies are generated
independently of every fitting and tuning route:

1. `in_family_interpolation`: a held-out weighted interpolation from two
   generator draws not included in the observed topology sequence;
2. `cross_generator`: a held-out directed latent-position weighted graph with
   an independently drawn support and weights.

The query paths are not passed to `fit`, validation loss, initialization,
stopping, or hyperparameter selection. They are passed only to `evaluate` once
a fitted state has been fixed.

## Same-endpoint methods and tuning

Each method implements the same interface:

```text
fit(training_histories, observed_training_topologies, frozen_hyperparameters)
evaluate(fitted_state, W_q, H) -> {G, R_1:H, status}
```

The ranked methods are limited to the following native coefficient-block
estimators.

| ID | Role | Retained representation | Frozen candidate list |
| --- | --- | --- | --- |
| `local_structured` | local structured comparator | Family-1 `A,B` or Family-2 `C0,C1,C2` rowwise ridge fits | windows `8, 12, 16` |
| `causal_temporal_smoother` | causal smoother | the same separate coefficient blocks after one-sided exponential smoothing | smoothing weights `0.25, 0.55, 0.85` |
| `fixed_rank_basis` | endpoint-preserving basis candidate | the same separate coefficient-block tensor after one-sided fixed-rank reconstruction | ranks `1, 2, 3` |

Every candidate list has three trials. Selection uses only observed-topology
one-step prediction loss on the validation region, with the deterministic
tie-break "lowest candidate-list index". The selected value is held fixed for
all evaluation topologies, horizons and response truth. A collapsed-only map
is recorded only as an `OUTSIDE_TARGET` negative control and is never assigned
a loss or rank.

## E3-1 exact classification gate

Before any fitted simulation, the runner must numerically verify the fixed
integer/rational fixture inventory in the Family-2 proof packet:

- Family-1 collapsed negative;
- Family-2 unrestricted collapsed negative;
- Family-2 diagonal rank-deficient negative;
- Family-2 diagonal full-rank structured-positive case; and
- non-equivalence of `W^2` with a fixed one-hop operator on `{0, V, 2V}`.

The exact check may use a `float64` consistency check at maximum absolute error
`1e-12`, but a rank tolerance or a random numerical example cannot replace the
stored algebraic classification. Any failure stops E3-2 through E3-4.

The source implementation makes this precedence executable: every public
synthetic generator, fit, selection, recovery, interval and native-path
evaluation entrypoint invokes the E3-1 gate before doing numerical work.
Block estimation and endpoint construction are private helpers, so they do
not expose an alternate public route around the classification check.

## E3-3 recovery grid and failure accounting

The recovery grid is fully crossed before outcomes:

- operator family: Family 1, Family 2;
- query class: `in_family_interpolation`, `cross_generator`;
- scale: `N=20`, `N=50`;
- horizon: `H=4`, `H=12`;
- independent paired panels: seeds `4101` through `4120`.

The same 20 panels and random streams are used for every method in a cell.
The output must contain one retained date-level record per
panel-method-query-horizon-evaluation-date, including unavailable, failed,
non-finite and unstable records. Panel-level summaries must retain the full
date-level status inventory. Pairwise differences use only the pre-declared
common-completion date-level set and are reported alongside each method's full
status counts. Cells are reported separately; they are not pooled to hide a
cross-generator, larger-scale, or longer-horizon failure.

## E3-4 uncertainty and stability gate

For each family and scale at `H=4`, the selected `fixed_rank_basis` method is
subject to a fixed-design residual circular moving-block bootstrap with 80
replicates, block length 5, and independent bootstrap streams derived from the
panel seed. Each bootstrap replicate refits the selected method with its
already-selected hyperparameter; it may not tune again. A simultaneous 95%
max-deviation band is formed over all entries of the `N x N` response matrix
`R_4` only, at the declared horizon. The runner reports, for each declared
cell, empirical simultaneous coverage, mean interval width, raw response
error at `R_4`, stability-qualified response error, truth and estimated
spectral-radius diagnostics, and counts of every primary and bootstrap status.

The interval target date is fixed before outcomes as the final evaluation date
`t=143` (zero-based target-time indexing) for every panel. Both held-out query
classes are evaluated separately. Thus each family-scale-query cell has 20
independent interval records, one per paired panel; its reported coverage and
width are calculated only from that predeclared cell and never selected across
dates, queries, scales or operator families after inspection.

An estimate with non-finite output or spectral radius at least `0.98` is
retained with its corresponding status and receives neither a stability-
qualified response loss nor a bootstrap interval. No post-evaluation rescaling
or stabilization is permitted. Likewise, any non-available bootstrap replicate
invalidates that cell's interval rather than allowing a band to be conditioned
on successful replicates; its full bootstrap status inventory remains reported.

## Reproducibility and audit conditions

The future candidate must bind this design, the runner, its standard-library
and NumPy dependency manifest, the eight `CANDIDATE_READY` artifacts, the
synthetic input/configuration file, all seed streams, an empty absolute
quarantine root, and one exact invocation. A duplicate run must use the same
candidate bytes but a distinct empty quarantine root. An independent result-to-
claim audit is required before any result is read into the manuscript.

No result from this design may change the two controlling audit states,
activate C1--C3, create an application claim, or trigger a manuscript build
without a separate promotion decision.
