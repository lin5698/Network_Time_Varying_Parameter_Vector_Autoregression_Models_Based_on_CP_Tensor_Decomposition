# REC-M5 Author Input Request V1

Generated: 2026-08-12

## Routing

- Phase: M5-A, author-decision intake.
- Package state: `author_input_complete_pending_independent_review`.
- Action label: `INDEPENDENT_REVIEW_REQUIRED`.
- This worksheet does not authorize manuscript mutation, formal-register mutation, scientific execution or claim activation.
- Please fill only fields for which a real source, executed result or author decision exists. Do not infer missing values from another scenario, compiled TeX, zero failure counts or a different audit.

## AIN-RESULT: four controlled-result placeholders

These fields are required before G04 can be applied. A percentage alone is insufficient; the formula, denominator, endpoint and comparator must be bound.

| ID | Required field | Author value | Evidence locator |
| --- | --- | --- | --- |
| AIN-RESULT-OP-N15 | Operator-error relative reduction at N=15 | 93.55203369881073% (93.6% display) | `output/natcs_benchmarks/benchmark_summary.csv`, `scale_n15`, `local_network/cp_network`, `coef_error_median` |
| AIN-RESULT-OP-N30 | Operator-error relative reduction at N=30 | 96.76394154622214% (96.8% display) | `output/natcs_benchmarks/benchmark_summary.csv`, `scale_n30`, `local_network/cp_network`, `coef_error_median` |
| AIN-RESULT-RESP-N15 | Response-error relative reduction at N=15 | 82.54278845800611% (82.5% display) | `output/natcs_benchmarks/benchmark_summary.csv`, `scale_n15`, `local_network/cp_network`, `girf_error_median` |
| AIN-RESULT-RESP-N30 | Response-error relative reduction at N=30 | 87.32161861932515% (87.3% display) | `output/natcs_benchmarks/benchmark_summary.csv`, `scale_n30`, `local_network/cp_network`, `girf_error_median` |

Required common fields:

- `formula`: exact relative-reduction formula, including whether the value is computed from ratios of median errors, a median of per-replication changes, or another declared statistic;
- `numerator_and_denominator`: exact endpoint fields and comparator fields;
- `replication_unit`: confirm the 20-replication unit for each primary row;
- `evidence_hash`: SHA-256 of the artifact containing the values;
- `manuscript_locator`: canonical source section and paragraph, with no invented line number.

Author confirmation received on 2026-08-12: the user accepted the preceding
candidate extraction, including the ratio-of-medians formula, one-decimal display,
endpoint mapping and local-versus-CP comparator. That confirmation event applied
only to AIN-RESULT; later confirmation events are recorded in their own sections.

Confirmed formula: `100 * (local_network_metric_median - cp_network_metric_median) / local_network_metric_median`.
The evidence SHA-256 is `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`.

## AIN-ALS: CAL-E03 solver contract

| ID | Required field | Author value | Evidence locator |
| --- | --- | --- | --- |
| AIN-ALS-01 | Is 60 ALS iterations a fixed count or a maximum? | Fixed count when the call completes normally | `scripts/natcs_benchmarks.mjs:292-317` |
| AIN-ALS-02 | Monitored quantity | None | `scripts/natcs_benchmarks.mjs:292-317` |
| AIN-ALS-03 | Tolerance | Not applicable; no stopping tolerance (`1e-6` is a Gram regularizer) | `scripts/natcs_benchmarks.mjs:299-307` |
| AIN-ALS-04 | Early-stop condition | None | `scripts/natcs_benchmarks.mjs:292-317` |
| AIN-ALS-05 | Rule precedence | Execute all 60 iterations unless an exception aborts; the caller records failure | `scripts/natcs_benchmarks.mjs:292-317,957-985` |
| AIN-ALS-06 | Canonical source for application 100-iteration setting | Unavailable | Generated TeX is observed but is not the canonical ownership source |
| AIN-ALS-07 | Canonical source for bootstrap 80-iteration setting | Unavailable | Generated TeX is observed but is not the canonical ownership source |
| AIN-ALS-08 | Explicit separation from CAL-E03 | Yes; CAL-E03 uses its own fixed-60 implementation and the unowned 100/80 wording must not be imported | `scripts/natcs_benchmarks.mjs:292-317,957-985` |

Until AIN-ALS-01 through AIN-ALS-08 are complete, no convergence, global-optimum or solver-comparability wording may be activated.

Author confirmation received on 2026-08-12 for AIN-ALS-01 through AIN-ALS-08.
This establishes implementation semantics only; it does not establish convergence or
global optimality.

## AIN-TOPOLOGY: CAL-E03 stress-row bindings

Provide one row for every topology-stress scenario that is intended to remain in the manuscript.

| Scenario ID | Category | Exact amplitude | Affected object | Generation or observation | Seed policy | Endpoint | Replication count | Evidence path/key | Evidence SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| `high_topology_vol` | topology volatility | `topologyVol=0.18`, `sparsity=0.15`, `wNoise=0`, `wDrop=0` | `truth.W` evolution | generation | deterministic scenario/replication seed from base 20260328 | per-method declared endpoints | local 3; each other released method 20 | `scripts/natcs_benchmarks.mjs:27,405-408,442-482`; released summary rows | script `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`; summary `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1` |
| `sparse_misspecified` | combined graph sparsity and noisy observed weights | `topologyVol=0.08`, `sparsity=0.55`, `wNoise=0.18`, `wDrop=0` | `truth.W` and `WEst` | generation and observation | deterministic scenario/replication seed from base 20260328 | per-method declared endpoints | each released method 3 | `scripts/natcs_benchmarks.mjs:28,391-414,442-482`; released summary rows | script `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`; summary `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1` |
| `edge_missing` | missing observed edges | `topologyVol=0.06`, `sparsity=0.15`, `wNoise=0`, `wDrop=0.30` | observed nonzero off-diagonal edges in `WEst` | observation, with generation volatility 0.06 | deterministic scenario/replication seed from base 20260328 | per-method declared endpoints | local 3; each other released method 20 | `scripts/natcs_benchmarks.mjs:29,417-420,468-483`; released summary rows | script `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`; summary `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1` |
| `noisy_network` | noisy observed weights | `topologyVol=0.06`, `sparsity=0.15`, `wNoise=0.35`, `wDrop=0` | observed weights in `WEst` | observation, with generation volatility 0.06 | deterministic scenario/replication seed from base 20260328 | per-method declared endpoints | local 3; each other released method 20 | `scripts/natcs_benchmarks.mjs:30,411-414,468-483`; released summary rows | script `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`; summary `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1` |

Rules:

- Do not use the application-layer 50% top-exposure attenuation as a CAL-E03 amplitude unless the contract explicitly binds it.
- Category labels without amplitude and generation/observation role remain descriptive only.
- A zero status count does not supply a missing amplitude, replication or robustness result.

Author confirmation received on 2026-08-12: retain all four rows, accept the
code-derived seed policy, disclose the asymmetric released replication coverage and
do not treat these rows as a matched ranking or general topology-robustness result.

## AIN-SOURCE-OWNERSHIP: generated-text provenance

| ID | Required field | Author value | Evidence locator |
| --- | --- | --- | --- |
| AIN-SOURCE-01 | Canonical Markdown source for application/bootstrap 100/80 iteration wording | Unavailable | Generated `main.tex`/`supplementary.tex` are not canonical ownership sources |
| AIN-SOURCE-02 | Canonical Markdown source for spectral-radius wording | Unavailable | Canonical-source audit recorded in `REC-M5_GOVERNANCE_RECHECK_V5_20260812.json`; generated TeX is excluded |
| AIN-SOURCE-03 | Canonical Markdown source for 50% top-exposure attenuation | Unavailable | Canonical-source audit recorded in `REC-M5_GOVERNANCE_RECHECK_V6_20260812.json`; generated TeX is excluded |
| AIN-SOURCE-04 | Confirmation that generated TeX is not the ownership source | Yes | `scripts/build_natcs_manuscript.mjs`; canonical ownership must precede generated TeX |

Author confirmation received on 2026-08-12 for AIN-SOURCE-02. The canonical
spectral-radius wording source is unavailable; generated TeX must not be used to
reconstruct source ownership or import a spectral-radius mapping into the controlled
benchmark.

Author confirmation received on 2026-08-12 for AIN-SOURCE-03. The canonical
50% top-exposure attenuation source is unavailable; generated TeX must not be used
to reconstruct ownership, and the operation remains outside CAL-E03.

## Acceptance rules for returned inputs

- Every requested field is either filled with a source-backed value or explicitly marked unavailable with a reason.
- Every numeric value has a source path, key/field, and SHA-256 where an artifact exists.
- No field may import results from the separate M2C audit into the original N=15/N=30 benchmark contract.
- Missing, contradictory or unbound fields remain `AUTHOR_INPUT_NEEDED`; they do not become `PASS` by default.
- After intake, run an independent semantic review again. Only then may a separate explicit M5-D authorization be considered.

## 中文核对

- `AIN-RESULT`: 已确认四个百分比、中位数之比公式、分母、endpoint/comparator 字段和证据哈希；其余作者输入组也均已确认，当前仅待独立语义复核。
- `AIN-ALS`: 已确认固定 60 次、无监控量/停止容差/提前停止，异常时记失败；100/80 次规范 Markdown 来源记为不可用。
- `AIN-TOPOLOGY`: 已确认四个场景、精确参数、作用对象、generation/observation 角色、代码派生 seed 和不对称重复数边界。
- `AIN-SOURCE-OWNERSHIP`: 已确认生成 TeX 不是规范源，且 application/bootstrap 100/80、spectral-radius 和 50% top-exposure 的规范来源均不可用。
