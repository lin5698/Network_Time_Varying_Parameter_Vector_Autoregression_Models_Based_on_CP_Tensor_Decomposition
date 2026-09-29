# NCS E.3 Minimum Evidence Protocol

Date: 2026-07-22

Status: protocol-only. This document authorizes no scientific execution, data acquisition, dependency installation, RCEP/NYC inspection, R006e/R006f outcome, downstream build or manuscript promotion. `PAPER_CLAIM_AUDIT=BLOCKED` and `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling restrictions.

## Decision

The NCS desk-rejection gap is not closed by another CP-versus-local run. The smallest defensible future package must show that query preservation changes a declared computational task across a genuinely different operator family, not merely within the current diagonal first-order network VAR. It must also make recovery comparisons only among methods that answer the same endpoint.

This is a delta protocol. It does not replace `refine-logs/EXPERIMENT_PLAN.md`, alter the frozen R006e/R006f protocols, or reinterpret their outcomes. It identifies which later work could close E.3 and which existing tracks must not be presented as doing so.

## Future Claim Freeze

| ID | Eligible future claim, only if all linked blocks pass | Anti-claim that must remain excluded | Reviewer goal |
| --- | --- | --- | --- |
| C1 | A query-preservation condition classifies topology-indexed readouts across two pre-specified finite-basis operator families. | Query preservation is universal for arbitrary graph, nonlinear or topology-forming models. | novelty / generality / rigour |
| C2 | Under a declared stable regime, an endpoint-preserving reconstruction can recover held-out topology responses against fair same-endpoint comparators. | CP, Tucker or any candidate is generally superior, transferable or causal. | rigour / reproducibility |
| C3 | A pre-registered public-network readout shows that the audit changes which descriptive conclusion is permitted. | A topology substitution identifies a policy, formation or causal effect. | significance / clarity |

The current manuscript may not adopt C1-C3 until their evidence and independent audits exist. The existing first-order theorem, controlled $N=15/N=30$ benchmark and frozen endpoint-aware failure remain the only currently usable evidence.

## Common Contract For Every Block

1. Freeze the operator family, response endpoint, topology source, horizon, stability rule, tuning budget, random streams and stop rules before any outcome is inspected.
2. Classify endpoint availability before calculating response error. `outside target` is not a zero value, an imputed loss or a rankable result.
3. Keep topology endpoints out of fitting, initialization, hyperparameter selection and stopping decisions. Use distinct calibration, validation and evaluation regions.
4. Retain non-convergence, unavailable endpoints, instability and non-finite output as failures. Do not redraw an endpoint, replace a seed or condition on successful rows.
5. Separate observed-topology prediction from topology-response recovery. Prediction is secondary unless the model answers the declared structural endpoint.

## Minimum Evidence Blocks

### E3-1. Two-family query-transfer challenge

**Question.** Does the representation rule persist beyond the first-order operator $A+BW$?

**Family 1.** Retain the current separable direct/network operator as the reference family.

**Family 2.** Pre-specify a genuinely distinct finite graph-filter family,

$$
G_{k,t}(W)=C_{0,k,t}+C_{1,k,t}W+C_{2,k,t}W^2,
$$

with the three coefficient blocks stored and fitted separately. The $W^2$ term must not be folded into $C_1W$, substituted after fitting, or treated as a projected graph-feature surrogate.

**Required evidence.**

- State and prove a query-factorization or kernel-inclusion condition for the stored representation and each declared query.
- Construct observed-topology-equivalent coefficient worlds that disagree at a held-out topology for both families.
- Include one restricted or structured-inverse case in which a collapsed representation can answer the query, so the paper does not imply universal impossibility.
- Verify the exact construction numerically with fixed tolerances, without treating floating-point rank as a proof.

**Pass interpretation.** The same condition correctly classifies available, outside-target and structured-inverse endpoints in both families.

**Failure interpretation.** If the second family reduces to the first-order diagonal representation, or no distinct factorization boundary is established, C1 fails. The manuscript remains a one-family representation result.

**Manuscript role.** Revised Figure 1 and theorem section only after independent proof audit. Serves novelty / generality / clarity.

### E3-2. Fair same-endpoint recovery contract

**Question.** Does the endpoint-preserving reconstruction improve recovery without comparing unlike outputs?

**Eligible systems per family.** Use at most three systems that natively return the exact declared endpoint:

1. a local structured fit with retained coefficient blocks;
2. a causally tuned temporal structured smoother; and
3. one fixed endpoint-preserving low-rank or basis-structured candidate selected before outcomes.

A collapsed-map model may appear only as an `outside target` negative control. It must never receive a topology-response error or enter a numerical rank ordering. Projected graph-feature rows and post-hoc output mappings are not native same-endpoint baselines. A native graph-sequence model is eligible only if its supplied-adjacency response functional is defined before fitting and yields the same endpoint without projection.

**Fairness contract.** All eligible systems share input histories, chronological splits, topology endpoints, response horizons, tuning-trial budget, failure handling and stability treatment. Record parameter count, run time, memory, convergence state and every tuning candidate. A candidate may lose to the native structured comparator; that result removes estimator-superiority language but does not invalidate C1.

**Primary metrics.** Endpoint availability, raw finite-horizon response error, operator error, instability/failure rate and paired seed-level differences. Observed-topology prediction is secondary and cannot compensate for query failure.

**Failure interpretation.** Any comparison based on a projected or mismatched output is non-comparable. A loss to the local or temporal structured comparator restricts the paper to an audit/diagnostic contribution.

**Manuscript role.** Main recovery table plus a Supplementary tuning and fairness audit. Serves rigour / reproducibility.

### E3-3. Held-out topology, scale and horizon recovery

**Question.** Does the result survive a topology query not used in fitting or selection?

**Required split.** For each family, freeze:

- one in-family interpolation topology;
- one cross-family topology from a distinct pre-specified generator or graph-filter basis;
- a calibration region for endpoint feasibility only;
- disjoint chronological validation and evaluation regions.

The endpoint identity and all candidate hyperparameters must be invariant when held-out topology and truth targets are perturbed. The first reportable scale set is $N=20$ and $N=50$, with a primary and a longer finite horizon. Each headline cell needs at least 20 paired independent simulation units; any smaller run is diagnostic only. No selected $N=50$ stress row may become a headline result.

**Primary decision rule.** Report each family, topology class, scale and horizon separately. A cross-family failure, support loss, non-finite response, or instability blocks a generality claim even if interpolation succeeds. Do not pool successful cells to offset a failure.

**Failure interpretation.** Interpolation-only success supports interpolation only. A failure at larger scale or longer horizon defines the operating boundary rather than a row to omit.

**Manuscript role.** Main recovery figure showing operating and failure regions; full grid in Supplementary Information. Serves generality / rigour.

### E3-4. Uncertainty and stability gate

**Question.** Is the response readout both numerically stable and accompanied by an uncertainty procedure whose calibration has been tested?

**Required evidence.** Freeze one simultaneous response-interval algorithm before outcomes. On independent simulated panels with known truth, report empirical coverage and interval width for the primary response horizon. Separately report raw response error, stability-qualified response error, power-bound or stability diagnostic, and the share of unavailable/non-finite/unstable rows. The procedure may use a series-level resampling method only if the full refit, dependence structure and confidence allocation are fixed in advance.

The unresolved R006e simultaneous-median-bound prerequisite is not an uncertainty result. Its eventual resolution cannot be used as a substitute for response-interval coverage in this protocol.

**Pass interpretation.** Coverage, width and stability are reported for every declared primary cell, with no post-evaluation stabilization or deletion of failed paths.

**Failure interpretation.** Point recovery without calibrated uncertainty or stable finite-horizon behaviour supports descriptive point-estimation diagnostics only, not a scientific response readout.

**Manuscript role.** Main stability/coverage panel or a clearly labelled Supplementary gate, depending on figure budget. Serves rigour / reproducibility.

### E3-5. One consequential, noncausal public-network application

**Entry condition.** This block may be designed only after E3-1 through E3-4 pass and the relevant source, licence and implementation audits permit work. It is not authorization to acquire data or inspect application outcomes.

**Design.** Pre-register one public temporal network, one event or temporal holdout, one benchmark topology, one response horizon, one descriptive decision rule and placebo windows. The event, nodes, preprocessing, topology definition, model-selection period and response threshold must be frozen before fitting. The target may be a pre-defined propagation ranking or threshold classification, but it must be meaningful without being interpreted as a causal topology effect.

**Required contrast.** The application must make the audit operational: an endpoint-preserving representation supports a stable, uncertainty-qualified descriptive conclusion, while a non-preserving representation is explicitly `outside target` or fails a pre-specified later gate. A null or unstable result remains a valid outcome and may not trigger a search for a more favourable event or topology definition.

**Failure interpretation.** If the application does not change a permitted descriptive conclusion, it is illustrative rather than evidence of practical significance. If it fails the stability or uncertainty gate, it cannot be promoted to the main manuscript.

**Manuscript role.** A single bounded application figure; RCEP and NYC remain out of the claim set until their independent audits pass. Serves significance / clarity / reproducibility.

## Explicit Cuts And Deferrals

| Item | Decision | Reason |
| --- | --- | --- |
| Another R006e-only screening pass | Not an E3 block | Even a pass is a one-family, $N=20$ result with explicit anti-claims. |
| Existing $N=50$ bounded stress rows | Not headline evidence | They do not meet the pre-specified replication threshold. |
| Projected graph-feature rows | Supplementary diagnostic only | They do not constitute native same-endpoint comparisons. |
| $W_{ref}$ performance | Safety guardrail only | It is not a held-out primary endpoint. |
| R006f exact-support abstention | Separate identification evidence | It cannot promote an estimator or rescue recovery failure. |
| Native GNN benchmark | Conditional deferment | It is ineligible until a native supplied-adjacency response functional is frozen. |
| RCEP/NYC results | Excluded | Current audits prohibit their use as evidence. |

## Execution Order And Stop Gates

| Phase | Deliverable before any outcome | Go condition | Stop condition | Status |
| --- | --- | --- | --- | --- |
| P0 | Versioned protocol, code/data provenance plan and claim ledger update | Independent review confirms no endpoint leakage or mismatched target | Missing authorization, unresolved source rights or ambiguous endpoint | Drafted only |
| P1 | E3-1 theorem and exact-fixture audit | Distinct Family 2 and exact classification boundary | Family 2 collapses to Family 1 or proof audit fails | Not authorized |
| P2 | E3-2 comparator and tuning contract | Every eligible method returns the same endpoint | Any post-hoc mapping or unfair tuning route | Not authorized |
| P3 | E3-3 split/scale/horizon construction audit | Held-out endpoints are invariant to truth/outcome perturbation | Support loss, leakage or insufficient replication | Not authorized |
| P4 | E3-4 uncertainty/stability construction audit | Interval and stability procedures are fully fixed | Unspecified confidence allocation or post-evaluation stabilization | Not authorized |
| P5 | E3-5 application preregistration | E3-1 through E3-4 and external audits pass | Any prior gate fails or application outcome is unaudited | Not authorized |

## Manuscript Promotion Rule

No new evidence enters the manuscript merely because a protocol exists. A future claim must pass its own independent result-to-claim audit, reproduce in an isolated duplicate where appropriate, and be reconciled with the exact claim/evidence ledger before any source, figure, abstract, title or submission artifact changes. Until then, the current manuscript remains bounded by its existing theorem, controlled benchmark and negative endpoint-aware gate.

