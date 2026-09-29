# REC-M5 Scientific Recheck Terra V3

Generated: 2026-08-12T14:38:14+0800

- Phase: M5-C independent scientific semantic recheck.
- Reviewer route: `gpt-5.6-terra` with `max` reasoning effort.
- Review mode: `DIRECT_SELF_ADJUDICATION`.
- Scope: review-only validation of the current M5 patch and author-input records against the bounded script and released benchmark summary.
- No manuscript, formal-register, scientific-payload, authorization, generated-TeX, claim-activation, or Git mutation is authorized by this receipt.

## Disposition

**Scientific semantic content: `PASS`.** The current review-only patch accurately binds the four G04 percentages, the fixed-count ALS implementation, and the four retained topology-stress rows. Its proposed language stays within the supported synthetic, endpoint-specific evidence.

**Application and activation: `BLOCKED`.** The underlying governance boundary still prohibits manuscript and formal-register mutation, scientific-payload mutation, authorization mutation, generated-TeX mutation, and claim activation. This `PASS` does not apply the patch or promote any claim.

**Scientific semantic `FAIL` findings: none.** This was a direct adjudication of available semantic payload, not a service-failure fallback or a missing-payload default.

## Input Integrity

All four required current SHA-256 values were recomputed and match the supplied values exactly.

| Input artifact | SHA-256 | Result |
| --- | --- | --- |
| `REC-M5_REVIEW_PATCH_V1_20260811.md` | `b95a09609cf45477bbdf9eac78be84021a4c177b5d4028228ed804fa22ba5891` | `PASS` |
| `REC-M5_REVIEW_PATCH_V1_20260811.json` | `8c0546a7011a82042661f3423ca68a4dbab19044261a4280037fd996279124de` | `PASS` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` | `PASS` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `c7664285eff125335e75c1f13f51b20d38a4b8a368c87db11079386f9e7c56f5` | `PASS` |

The bounded implementation and summary evidence also matched their recorded values: `scripts/natcs_benchmarks.mjs` SHA-256 `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633` and `output/natcs_benchmarks/benchmark_summary.csv` SHA-256 `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`.

## Scientific Checks

### G04: Four controlled-result percentages

`PASS`. The patch gives the exact supported one-decimal displays and identifies both endpoints, the local rolling comparator, the CP candidate, and the statistic. The summary rows contain 20 replications for both methods at each primary scale.

| Scenario | Endpoint field | Local median | CP median | Recomputed reduction | Patch display |
| --- | --- | ---: | ---: | ---: | ---: |
| `scale_n15` | `coef_error_median` | 624.6125531760274 | 40.274806941788114 | 93.55203369881073% | 93.6% |
| `scale_n30` | `coef_error_median` | 1371.693631145596 | 44.38880771061946 | 96.76394154622214% | 96.8% |
| `scale_n15` | `girf_error_median` | 0.4103961733321335 | 0.07164372813883849 | 82.54278845800611% | 82.5% |
| `scale_n30` | `girf_error_median` | 0.3971572031343755 | 0.05035310489419762 | 87.32161861932515% | 87.3% |

The declared computation is exactly `100 * (local_network_metric_median - cp_network_metric_median) / local_network_metric_median`. It is a ratio of across-replication medians, not a median of per-replication percentage changes. The patch limits the interpretation to the declared synthetic DGP, endpoint, comparator, and replicated rows.

### G06: ALS solver semantics

`PASS`. `cpAls` defaults to 60 iterations and loops for `it < iterations`. It contains no objective or residual calculation, no tolerance, and no early-stop predicate. The three `1e-6` additions regularize Gram systems and are not stopping tolerances. The caller catches an exception and records a reconstruction failure.

The proposed wording correctly states that these facts establish only implementation semantics. It does not assert convergence, convergence rate, solver comparability, or global optimality. The unavailable application/bootstrap 100/80-iteration source is explicitly kept outside CAL-E03.

### G07: Topology-stress bindings and coverage

`PASS`. The candidate bindings agree with the scenario configuration and transformation functions.

| Scenario | Verified setting | Role | Coverage consequence |
| --- | --- | --- | --- |
| `high_topology_vol` | `topologyVol=0.18` | generated `truth.W` evolution | local 3; other released methods 20 |
| `sparse_misspecified` | `topologyVol=0.08`, `sparsity=0.55`, `wNoise=0.18` | generation plus observed `WEst` perturbation | 3 per released method |
| `edge_missing` | `wDrop=0.30` | observed nonzero off-diagonal edges in `WEst` | local 3; other released methods 20 |
| `noisy_network` | `wNoise=0.35` | observed-weight perturbation in `WEst` | local 3; other released methods 20 |

`evolveW` governs topology generation, while `perturbW`, `dropObservedEdges`, and the `WEst` construction implement observed-network noise and edge loss. The summary confirms that the released coverage is asymmetric in the volatility, missing-edge, and noisy-weight scenarios and only three per method in the sparse/misspecified scenario.

The patch correctly restricts these rows to bounded diagnostics. They do not support a matched ranking or a general topology-robustness conclusion.

### Claim ceiling

`PASS`. The patch does not convert simulation truth into empirical validation or general performance evidence. It expressly excludes empirical/general superiority, fairness, native held-out recovery, cross-family generality, convergence, and global-optimality claims. Its descriptions of CP error reduction are confined to the declared primary N=15/N=30 controlled simulation endpoints; N=50 remains a bounded stress check.

## Decision Matrix

| Review question | Status | Adjudication |
| --- | --- | --- |
| Are the four G04 values numerically and statistically bound? | `PASS` | Recomputed from the identified summary medians with the declared ratio-of-medians formula. |
| Does G06 describe the code's ALS behavior without an unsupported solver claim? | `PASS` | Fixed 60 iterations, no monitor/tolerance/early stop, and Gram regularization are correctly separated. |
| Are the four G07 parameter bindings and roles accurate? | `PASS` | Source configuration and observation transformations agree with the candidate text. |
| Does asymmetric topology coverage license a ranking or general robustness claim? | `BLOCKED` | The patch correctly abstains; only bounded diagnostics are supportable. |
| Are empirical/general superiority, convergence, or global-optimality claims permitted? | `BLOCKED` | They remain outside the available evidence and are explicitly excluded. |
| Does this review authorize application, claim activation, or a scientific-payload change? | `BLOCKED` | Separate explicit authorization remains required. |

## Authorization Boundary

| Boundary | State |
| --- | --- |
| Manuscript-source mutation | `NOT_AUTHORIZED` |
| Formal-register mutation | `NOT_AUTHORIZED` |
| Scientific-payload mutation | `PROHIBITED` |
| Authorization-file mutation | `PROHIBITED` |
| Generated-TeX mutation | `PROHIBITED` |
| Claim activation | `NOT_AUTHORIZED` |
| Git operations | `NONE` |

## Changed Paths

This review created only the following records:

- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V3_20260812.md`
- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V3_20260812.json`
