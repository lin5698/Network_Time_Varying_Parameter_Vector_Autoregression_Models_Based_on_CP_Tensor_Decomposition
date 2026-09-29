# REC-M5 Scientific Recheck Terra V1

Verdict: `BLOCKED`

Readiness: `NOT_READY_FOR_SEMANTIC_ACCEPTANCE_OR_M5-D`

## Decision

The requested current-version scientific-boundary semantic review did not produce
a usable GPT-5.6-Terra review payload or either authorized receipt. The Terra
worker was invoked with reasoning effort `max`, remained without a final response
through bounded waits, and was stopped after one same-lineage retry. Under the
explicit service policy, this is `BLOCKED`, never `PASS`.

The deterministic evidence preflight is positive for the declared bindings, but it
is not a Terra semantic adjudication. V8 independently records the current patch
as hash-current, deterministic harness `85/85 PASS`, M4 allowlist `247/247 PASS`,
and the semantic gate as `BLOCKED_NOT_PASS` after prior 503 failures.

## Service provenance

| Field | Value |
| --- | --- |
| Model | `gpt-5.6-terra` |
| Reasoning effort | `max` |
| Service tier | worker invocation; no usable final payload returned |
| Agent lineage | `019ff40a-0cd5-79e1-8c57-1a38589a2d34` |
| Initial attempt | No final response and no authorized output files after bounded waits |
| Retry | One same-lineage retry; no final response and no authorized output files |
| Terminal handling | Worker stopped after retry made no progress |
| Service status | `UNUSABLE_COMPLETION_WITHOUT_FINAL_PAYLOAD_OR_RECEIPT` |
| Semantic adjudication | `NOT_AVAILABLE` |
| Service-failure policy | Failure/interruption/no usable payload is not PASS |
| Fallback producer | Parent evidence preflight only; not a substitute for Terra review |

## Exact input hashes

| Input | SHA-256 | Hash check |
| --- | --- | --- |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md` | `336c3cc4e25276ac6eeb56d597b3fd8486e8a90d02c7d977ace172048138c07d` | `PASS` |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.json` | `8d9b1d2a7536daa6a7f7cb3ade5bc0f5b0674d2087d5efeb2fd2a8dcbf3e603a` | `PASS` |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `d622854aba0b0e190ef8653fc87ab95324239be5257ff02d25478e2cdde571cd` | `PASS` |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `83197e8828f894cabf9b21fe108be0c61c751dc8c967bdca684dc1220dfe4913` | `PASS` |
| `refine-logs/REC-M5_GOVERNANCE_RECHECK_V8_20260812.md` | `8c6620d60a5fcc31cd22d5dbb0abfb6c8104cdc57d1dadba4b0c1bb7913f435c` | `PASS` |
| `refine-logs/REC-M5_GOVERNANCE_RECHECK_V8_20260812.json` | `ff4182a3e5e67a23c095e8aac69c4a92ee9abcf217d93cc431572bb9f292d966` | `PASS` |

Declared evidence hashes checked during the local preflight:

- `scripts/natcs_benchmarks.mjs`: `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`
- `output/natcs_benchmarks/benchmark_summary.csv`: `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`
- `refine-logs/REC-M5_RESULT_CANDIDATE_EXTRACTION_V1_20260812.json`: `48853866e02588d5833699b53ecd42843936cc3ec9d5a4d96faa587b4ed06f84`
- `refine-logs/REC-M5_ALS_TOPOLOGY_CANDIDATE_EXTRACTION_V1_20260812.json`: `778367b26bb2d770a5f4125144585731ac8b6a8106fdb3bc2f9a392655b45031`

## Evidence-bounded recomputation

G04 binds the exact formula
`100 * (local_network_metric_median - cp_network_metric_median) /
local_network_metric_median`, using the same-scenario, same-endpoint
`local_network` median as denominator and `cp_network` as candidate. The released
fields bind `coef_error_median` to `effective_operator` and `girf_error_median` to
`total_response`, over 20 released replications at each primary N=15/N=30 scale.
The four recomputed reductions match the candidate record:

| Binding | Reduction |
| --- | ---: |
| Operator, N=15 | 93.55203369881073% (93.6% display) |
| Operator, N=30 | 96.76394154622214% (96.8% display) |
| Response, N=15 | 82.54278845800611% (82.5% display) |
| Response, N=30 | 87.32161861932515% (87.3% display) |

These are evidence-bound simulation summaries only. They do not establish native
held-out recovery, empirical ground truth, fairness, ranking, equivalence,
superiority, cross-family generality, or application performance.

## Scientific boundary checks

| Check | Preflight finding | Verdict under missing Terra adjudication |
| --- | --- | --- |
| Evidence-bounded claims | G04 values and declared benchmark evidence are present, hash-bound, and numerically reproducible. | `BLOCKED`; no semantic PASS available. |
| G04 formula binding | Formula, denominator, comparator, endpoints, four values, and display rounding are explicit. | `BLOCKED`; simulation-only ceiling remains. |
| Fixed-60 ALS | `cpAls` defaults to 60 and loops `it < iterations`; no objective/residual monitor, tolerance, or early-stop branch is present. Exceptions are recorded as failures. | `BLOCKED`; this does not imply convergence or global optimality. |
| Topology amplitudes/roles/coverage | Four retained scenarios are exact: `high_topology_vol` (`topologyVol=0.18`, generation), `sparse_misspecified` (`topologyVol=0.08`, `sparsity=0.55`, `wNoise=0.18`, generation and observation), `edge_missing` (`topologyVol=0.06`, `wDrop=0.30`, observation), and `noisy_network` (`topologyVol=0.06`, `wNoise=0.35`, observation). | `BLOCKED`; asymmetric released coverage permits bounded diagnostics only, not matched ranking or general robustness. |
| Source-unavailable decisions | Application/bootstrap 100/80, spectral-radius wording, and 50% top-exposure attenuation canonical Markdown ownership are unavailable. Generated TeX is excluded as an ownership source. | `BLOCKED`; no unavailable source may be reconstructed or imported into CAL-E03. |
| Current readiness | V8 is hash-current for the four current patch/author-input artifacts and states deterministic-only acceptance with semantic gate blocked. | `BLOCKED`; not ready for semantic acceptance or M5-D. |
| Overclaim ceilings | Current patch retains V1-026, V1-033, and V1-045 limits, including NOT_RUN/ABSTAIN and blocked/null telemetry boundaries. | `BLOCKED`; all ceilings remain binding. |

## Topology coverage ceiling

The code-derived seed policy is rooted at `20260328`, with CP initialization using
`simSeed + 1001 + zero-based replication index`; seeds are not serialized in the
released CSV. For `high_topology_vol`, `edge_missing`, and `noisy_network`,
`local_network` has three released replications while each other released method
has 20. `sparse_misspecified` has three replications per released method. Endpoint
availability remains method-specific; `OUTSIDE TARGET` is not a zero or a failed
numeric estimate. These facts support bounded protocol description only.

## Source-unavailable ceiling

- The application/bootstrap 100/80 iteration wording has no accepted canonical
  Markdown owner; generated `main.tex`/`supplementary.tex` cannot supply ownership.
- The canonical spectral-radius wording source is unavailable; generated TeX cannot
  reconstruct it or create a metric mapping for the controlled benchmark.
- The canonical 50% top-exposure attenuation source is unavailable; the operation
  remains outside CAL-E03.
- No source-unavailable decision authorizes manuscript mutation, claim activation,
  scientific execution, or formal-register mutation.

## Required recovery

1. Obtain a completed, auditable GPT-5.6-Terra `max` semantic review payload for
   this exact six-file input set, or a separately authorized service-recovery wave.
2. Recheck the same evidence and ceilings against that payload; service failure
   must remain non-PASS.
3. Obtain separate explicit authorization before any manuscript or formal-register
   change.

## Review-only boundary and changed paths

No manuscript source, formal register, scientific payload, authorization file,
generated TeX, script, test, or Git state was modified.

Only these paths are authorized as outputs:

- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V1_20260812.md`
- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V1_20260812.json`
