This supplementary note defines the controlled benchmark contract behind `Results > Validation and benchmarking`. It separates endpoint availability from numerical recovery and restricts performance claims to the exact evaluated design. The primary replicated rows have $N=15$ and $N=30$, with 20 replications per primary row. At $N=50$, local, CP, Tucker, collapsed and low-rank no-network rows have four replications; sparse and projected graph-feature diagnostics have one each. These bounded scaling stress checks are not headline evidence. No application setting enters this benchmark.

| Design | N | T | Window | Topology weight | True/fitted rank | H | Replication or seed coverage | Evidence role |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | --- |
| Primary scale N=15 | 15 | 160 | 40 | 0.04 | 2 / 2 | 4 | 20 replications | Headline controlled recovery |
| Primary scale N=30 | 30 | 200 | 48 | 0.05 | 2 / 2 | 4 | 20 replications | Headline controlled recovery |
| Bounded stress N=50 | 50 | 240 | 56 | 0.05 | 2 / 2 | 4 | 4 for local/CP/Tucker/collapsed/no-network; 1 for sparse/projected diagnostics | Scaling stress, not headline evidence |
| Separate endpoint-aware qualification | 20 | 200 | Separate design | Separate design | rank-3 candidates | Separate design | 10 recorded seeds per cell | Simulation-only qualification under a pre-registered decision rule |

The active controlled-benchmark comparator hierarchy is as follows. A separate frozen native-comparator audit uses a different registry whose `local_structured`, `causal_temporal_smoother` and `fixed_rank_basis` entries correspond to native local-structured, causal-temporal-structured and fixed low-rank/basis methods, respectively. These labels are not aliases for the active CP, Tucker or unrestricted-local rows, and the audit is not an additional active benchmark row.

| Comparator class | Stored representation | Declared topology-response endpoints | Evidence role |
| --- | --- | --- | --- |
| CP-network | Separated direct/network coefficient tensor | Total, direct-only, frozen-topology and network-component readouts | Main controlled estimator |
| Tucker-network | Separated direct/network coefficient tensor | Same endpoint class as CP | Same-target representation comparator |
| Unrestricted local rolling | Separated local coefficient blocks | Same endpoints before low-rank reconstruction | Primary controlled recovery comparator |
| Collapsed-operator CP | Smoothed total map | Total-map and total-response only | Structural negative control |
| Low-rank no-network | Reduced-form dynamics without explicit network block | Total-map and total-response only | Reduced-form control |

An `OUTSIDE TARGET` mark is assigned before numerical scoring. It is not a numerical zero, missing observation or failed estimate; it records that a fitted object has not retained the blocks or verified inverse required by the requested readout. The collapsed and no-network controls therefore cannot be ranked on direct-only, frozen-topology or network-component columns.

All declared failure, non-finite, outside-target and unstable statuses remain in the accounting denominator. A zero count in one frozen run is an observed status count, not evidence of failure-free operation or a failure-rate bound.

In the original controlled $N=15$ and $N=30$ simulation benchmark, separated CP reduced the reported effective-operator and finite-horizon unit-shock response errors relative to unrestricted local rolling estimation. The DGP-generated objects are simulation truth, not independent empirical ground truth. The result is limited to the declared DGP, endpoint, comparator and replicated rows; it is not evidence of native held-out recovery, empirical fairness, broad superiority, cross-family generality or application performance. The stress protocol records category labels for rank specification, coefficient drift, topology volatility, graph sparsity, missing observed edges, noisy observed weights and shock tails. The four retained topology rows have fixed, separately documented amplitudes and generation-versus-observation roles, but their asymmetric coverage supports only bounded diagnostics, not a matched ranking or general topology-robustness claim.

Projected graph-feature stress tests are retained only as diagnostics of a mapping problem. Their native fitted objects require a fixed projection to the direct/network operator protocol before they can be scored on that protocol. They are neither native graph-learning comparisons nor part of a main-text ranking. A future comparative claim would require methods that natively return the same declared endpoint under matched inputs, tuning budget, horizon and stability treatment, with chronology, selection inputs, held-out query identity, endpoint signature and truth isolation frozen and recorded in advance.

### Stricter endpoint-aware recovery gate

| Candidate | Rank | Required cells passed | Matched-design cells | Native-design cells | Rule outcome |
| --- | --- | ---: | ---: | ---: | --- |
| CP anchor split | 3 | 0/16 | 0/8 | 0/8 | Threshold not met |
| Tucker anchor split | (3,3,3) | 6/16 | 6/8 | 0/8 | Threshold not met |

A separate simulation-only endpoint-aware experiment used cells with $N=20$ and $T=200$ and required one fixed candidate to pass both recorded endpoints in every required cell. No candidate met the pre-registered decision rule. The gate classification is not empirical ground truth or native recovery, and the negative result is not a universal failure theorem.

Because the protocols and designs differ, this qualification fixes the inheritance boundary without changing the original $N=15/N=30$ comparison. The controlled simulation gain supports only its declared rows and unrestricted rolling comparator, not independent empirical ground truth, broad endpoint-aware recovery, native held-out recovery, fairness or broad superiority.
