# NCS E3 Family-2 Candidate Contract

Date: 2026-07-22

Status: `DRAFTED`, `SOURCE_ONLY`, `NOT_EXECUTABLE`.

This candidate defines no result, authorizes no code execution, data acquisition, dependency installation, outcome inspection, RCEP/NYC access, R006e/R006f activity, manuscript build or manuscript promotion. `PAPER_CLAIM_AUDIT=BLOCKED` and `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling. A protocol or a future author approval cannot change either audit verdict; only the corresponding independent evidence audit can do so.

## Purpose And Claim Boundary

The purpose is to turn E3-1 and E3-2 of `NCS_E3_MINIMUM_EVIDENCE_PROTOCOL.md` into a reviewable future candidate. It targets one narrow future claim only:

> Across two pre-specified finite topology-indexed operator families, a query-preservation condition classifies whether a declared readout is evaluable from the stored representation.

It does not support a claim of universal query preservation, estimator superiority, general transfer, causal topology effects, empirical relevance or a releaseable application result. A recovery claim remains conditional on later E3-3 and E3-4 evidence.

## Frozen Conceptual Families

### Family 1: direct plus one-hop response

For comparison, retain the existing unrestricted family

$$
M(W)=A+BW,
$$

with stored collapsed object $D_1=M(W_0)$ and query $Q^{(1)}_{W_1}(A,B)=A+BW_1$. Its exact unrestricted boundary is already stated in Proposition 1: factorization through $D_1$ occurs if and only if $W_1=W_0$.

### Family 2: direct plus two-hop graph-filter response

The proposed distinct family is

$$
G(W)=C+E W^2,
$$

where $C$ and $E$ are separately stored coefficient blocks and $W$ is the supplied weighted adjacency at readout. The absence of a one-hop coefficient is intentional: Family 2 represents direct and exactly two-hop propagation, rather than a relabelled $A+BW$ response. The finite-horizon response recursion must evaluate $G(W)$ directly; it must not fold $W^2$ through an observed reference topology and then report a first-order endpoint.

For a fitted topology $W_0$, define

$$
T^{(2)}_{W_0}(C,E)=C+EW_0^2,
\qquad
Q^{(2)}_{W_1}(C,E)=C+EW_1^2.
$$

On unrestricted square matrix blocks, $Q^{(2)}_{W_1}$ factors through $T^{(2)}_{W_0}$ for every $(C,E)$ if and only if $W_1^2=W_0^2$. Sufficiency is immediate. For necessity, the worlds $(C,E)=(0,0)$ and $(\widetilde C,\widetilde E)=(-W_0^2,I)$ share the stored object zero but return $0$ and $W_1^2-W_0^2$ at the query. This is an operator-level classification; a scalar response need not differ if its response map is constant along the constructed operator difference.

### Non-equivalence requirement

Family 2 must not be presented as a one-hop model with an after-the-fact feature substitution. The future proof/fixture audit must establish that no fixed $A,B$ reproduces $G(W)=W^2$ on the pre-specified topology set $\{0,V,2V\}$, where

$$
V=\begin{pmatrix}0&1\\1&0\end{pmatrix}.
$$

At $W=0$, equality forces $A=0$; at $W=V$, it forces $BV=I$; at $W=2V$, the first-order representation gives $2I$ whereas $W^2=4I$. A future candidate fails E3-1 if it removes this non-equivalence audit, silently redefines the input as $W^2$, or evaluates a first-order surrogate instead of the declared two-hop query.

## Exact No-Outcome Fixture Set

These matrices are fixed algebraic fixtures, not simulated outcomes and not a production run.

$$
W_0=\begin{pmatrix}0&1\\1&0\end{pmatrix},
\qquad
W_{\mathrm{same\ square}}=\begin{pmatrix}0&2\\1/2&0\end{pmatrix},
\qquad
W_{\mathrm{different\ square}}=\begin{pmatrix}0&2\\1&0\end{pmatrix}.
$$

They satisfy $W_0^2=W_{\mathrm{same\ square}}^2=I$ and $W_{\mathrm{different\ square}}^2=2I$.

| Fixture | Required classification | What it falsifies | Permitted conclusion |
| --- | --- | --- | --- |
| Family 1 at $W_{\mathrm{same\ square}}$ | `outside target` for a collapsed $A+BW_0$ object | Treating different raw topologies as interchangeable in Family 1 | Family 1 cannot answer that query from its collapsed object. |
| Family 2 at $W_{\mathrm{same\ square}}$ | `available` for the unrestricted collapsed $C+EW_0^2$ object | A universal claim that every altered raw topology is unavailable after collapse | Family 2 can answer this declared two-hop query because the queried squared topology is unchanged. |
| Family 2 at $W_{\mathrm{different\ square}}$ | `outside target` for the unrestricted collapsed object | Calling Family 2 universally available | The two-hop query is not determined when the squared topology changes. |
| Family 2 structured inverse | `available` under the stated diagonal condition below | Applying the unrestricted impossibility result to every structured implementation | The structured class is a separate reconstruction contract. |

No response-error, prediction-error, recovery, ranking or significance statistic may be computed from an `outside target` fixture.

## Family-2 Structured-Inverse Exception

For the diagonal implementation class, let $C=\operatorname{diag}(c)$, $E=\operatorname{diag}(e)$ and $H_r=W_r^2$. If row $i$ of $H_0$ has a nonzero off-diagonal component, then

$$
e_i=\frac{D_{i,-i}H_{0,i,-i}^{\prime}}{\|H_{0,i,-i}\|_2^2},
\qquad
c_i=D_{ii}-e_iH_{0,ii}.
$$

If $H_{0,i,-i}=0$, the queried row is independent of the unidentified $e_i$ if and only if $H_{1,i\cdot}=H_{0,i\cdot}$. Thus the diagonal Family-2 query factors through the collapsed representation exactly when every row with $H_{0,i,-i}=0$ is unchanged between $H_0$ and $H_1$. If every off-diagonal row is nonzero, the collapsed representation is injective on this structured class.

The exact structured fixture uses

$$
W_0=\begin{pmatrix}0&1&1\\1&0&1\\1&1&0\end{pmatrix},
\qquad W_1=\tfrac12 W_0.
$$

Here $W_0^2$ has nonzero off-diagonal entries in every row. A formal fixture audit must recover the diagonal blocks from the collapsed object and verify the declared query at $W_1$. It must not treat numerical full rank as a proof of the stated rowwise condition.

## E3-2 Same-Endpoint Comparator Contract

The future recovery comparison is eligible only after E3-1's proof and fixture audit pass. For Family 2, every ranked system must natively return the same object $\widehat G(W)=\widehat C+\widehat E W^2$ and the same finite-horizon response functional at every declared topology.

| System | Required native output | Eligibility condition | Ineligibility condition |
| --- | --- | --- | --- |
| Local two-hop structured fit | Separately fitted $\widehat C,\widehat E$ | Fits direct and $W^2$ exposure blocks without a post-hoc mapping | Stores only $\widehat G(W_0)$ or folds two-hop exposure through $W_0$. |
| Blockwise temporal structured smoother | Smoothed $\widehat C_t,\widehat E_t$ | Smoothing acts on both retained blocks before any query | Smooths a collapsed map or reconstructs blocks after smoothing. |
| Fixed low-rank or basis-structured candidate | Retained two-block coefficient tensor and direct query evaluator | Rank/basis family and tuning route are frozen before outcomes | Rank, basis or endpoint changes after viewing recovery outcomes. |
| Collapsed two-hop map | $\widehat D=\widehat C+\widehat E W_0^2$ only | Negative-control availability panel only | Any topology-response error, ranking, win rate or headline comparison. |
| Projected graph-feature, GNN or diffusion model | None in the current contract | Only after a pre-fitted, supplied-adjacency evaluator returns exactly $\widehat C+\widehat E W^2$ without projection | Any output mapping, reference-topology folding or feature-to-block projection. |

All eligible systems must share the same historical input range, chronological calibration/validation/evaluation split, supplied topology endpoints, response horizons, stability rule, failure retention, random streams and maximum tuning-fit budget. The current candidate does not freeze numerical grids, seeds, horizons, panel lengths, source hashes or an implementation. Those fields must be committed in a later pre-outcome manifest before any request for execution authorization. Their absence is a hard refusal, not permission to select them during a run.

## Required Pre-Outcome Artifacts

Before a scientific invocation can even be proposed, all of the following must exist and pass static review:

1. A proof and exact-fixture audit for the two Family-2 boundaries, including the non-equivalence check and structured-inverse exception.
2. A canonical execution manifest that freezes the DGP, topology generators, scales, panel lengths, horizons, seed schedule, chronological splits, exact tuning grids and the common maximum tuning-fit budget.
3. A same-endpoint contract test that rejects collapsed, projected or post-hoc-mapped methods before fitting.
4. A truth-isolation test that perturbs held-out truth and evaluation outcomes without changing endpoint selection, selected hyperparameters or candidate identity.
5. A pre-outcome stability/interval specification. E3-4's coverage rule remains an independent future gate and cannot be satisfied by this contract alone.
6. A hard-rejection test proving that missing or mismatched authorization and trust evidence abort before a generator, estimator, response evaluator, outcome writer or scientific output directory is created.
7. An isolated duplicate-run and result-to-claim audit design, both bound to the eventual exact manifest.

## Future One-Time Authorization Checklist

No authorisation is requested by this file. A later explicit authorization must name the SHA-256 of one reviewed candidate and authorize only one invocation. The candidate must bind:

- the exact runner and its source/dependency hashes;
- the canonical pre-outcome manifest and all fixture/configuration hashes;
- a synthetic-only input route with no RCEP, NYC or provider-governed empirical inputs;
- exact scales, panel lengths, horizons, seed schedule, splits, tuning budget and comparator roster;
- one new quarantine output root that does not overlap any manuscript, R006e, R006f, RCEP or NYC output tree;
- the production trust verifier and evidence needed for the runner to fail closed before science;
- an explicit prohibition on manuscript promotion, result use, downstream builds and audit-status changes.

After that single invocation, the output remains quarantine material. It cannot alter `PAPER_CLAIM_AUDIT`, `EMPIRICAL_IMPLEMENTATION_AUDIT`, E3 status, manuscript claims or the NCS submission state without the separately specified duplicate, independent audit and a new promotion authorization.

## Stop Conditions

Stop before execution if any of the following is true:

1. Family 2 is evaluated through a first-order or projected surrogate rather than $C+EW^2$.
2. The observed-topology-equivalent fixtures do not produce the required Family-1/Family-2 classification contrast.
3. A comparator cannot natively return the declared endpoint.
4. Endpoint identity, seed, tuning choice, topology generator or response horizon depends on held-out truth or outcomes.
5. A failure, unstable path, unavailable endpoint or non-finite output is omitted, redrawn or converted to a score.
6. Any controlling audit remains blocked or failed without an independently approved, fail-closed route for this new synthetic-only runner.

## Current Decision

This candidate improves the experimental design path, but it supplies no new evidence. The only currently justified paper position remains the existing one-family theorem, bounded controlled benchmark and endpoint-aware negative recovery result. E3-1 through E3-5 remain `NOT_AUTHORIZED` or `BLOCKED` as recorded in `NCS_E3_EVIDENCE_TRACKER.md`.
