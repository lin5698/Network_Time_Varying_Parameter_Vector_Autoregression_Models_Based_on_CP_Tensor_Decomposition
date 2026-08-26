This supplementary note defines the controlled benchmark contract behind `Results > Validation and benchmarking`. It separates endpoint availability from numerical recovery and restricts performance claims to the exact evaluated design. The primary replicated rows have $N=15$ and $N=30$, with 20 replications per primary row. At $N=50$, local, CP, Tucker, collapsed and low-rank no-network rows have four replications; sparse and projected graph-feature diagnostics have one each. These bounded scaling stress checks are not headline evidence. No application setting enters this benchmark.

The declared comparator hierarchy is as follows.

| Comparator class | Stored representation | Declared topology-response endpoints | Evidence role |
| --- | --- | --- | --- |
| CP-network | Separated direct/network coefficient tensor | Total, direct-only, frozen-topology and network-component readouts | Main controlled estimator |
| Tucker-network | Separated direct/network coefficient tensor | Same endpoint class as CP | Same-target representation comparator |
| Unrestricted local rolling | Separated local coefficient blocks | Same endpoints before low-rank reconstruction | Primary controlled recovery comparator |
| Collapsed-operator CP | Smoothed total map | Total-map and total-response only | Structural negative control |
| Low-rank no-network | Reduced-form dynamics without explicit network block | Total-map and total-response only | Reduced-form control |

An outside-target mark is not a numerical zero, a missing observation or a failed estimate. It records that a fitted object has not retained the blocks or verified inverse required by the requested readout. The collapsed and no-network controls therefore cannot be ranked on direct-only, frozen-topology or network-component columns.

In the original controlled $N=15$ and $N=30$ benchmark, separated CP reduced the reported effective-operator and finite-horizon unit-shock response errors relative to unrestricted local rolling estimation. That statement is limited to the declared data-generating process, endpoint, comparator and replicated rows. It is not evidence of native held-out recovery, broad estimator superiority, cross-family generality or application performance. The controlled stress protocol separately varies rank specification, coefficient drift, topology volatility, observed-edge loss, observed-weight noise and shock tails; the current manuscript does not promote any stress-row ranking as a general result.

Projected graph-feature stress tests are retained only as a diagnostic record of a mapping problem. Their native fitted objects require a fixed projection to the direct/network operator protocol before they can be scored on that protocol. They are neither native graph-learning comparisons nor a main-text ranking. A future comparative claim would require methods that natively return the same declared topology-response endpoint under matched inputs, tuning budget, horizon and stability treatment.

### Stricter endpoint-aware recovery gate

A separate endpoint-aware experiment tested whether the original favourable scale benchmark extends to native held-out endpoints. The experiment used $N=20$, $T=200$ simulation cells and required one fixed candidate to pass both recorded endpoints in every required cell. No candidate met this promotion rule.

| Candidate | Required cells passed | Matched-design cells | Native-design cells | Promotion status |
| --- | ---: | ---: | ---: | --- |
| CP anchor split, rank 3 | 0/16 | 0/8 | 0/8 | Not promoted |
| Tucker anchor split, rank (3,3,3) | 6/16 | 6/8 | 0/8 | Not promoted |

Because the protocols and designs differ, this qualification fixes the inheritance boundary without changing the original $N=15/N=30$ comparison: the reported gain supports its controlled rows and unrestricted rolling comparator, not broad endpoint-aware or native held-out recovery. Endpoint availability, matched-design recovery and native-design recovery therefore remain separate claims.
