# REC-M5 Scientific Recheck V4

Status: `BLOCKED`

Release readiness: `FAIL_NOT_READY`

## Decision

The current all-author-input-bound M5 scientific-boundary recheck is not a PASS.
The required `gpt-5.6-luna` review at `max` reasoning effort was invoked twice on
the current project state, but each invocation completed without a final response
or either required review artifact. A service interruption or no-output completion
is not an adjudication and is never a PASS.

The record is also not ready to be released or advanced to M5-D: governance V7
does not hash-bind the current review-patch Markdown, review-patch JSON, or
author-input JSON. Those freshness failures are distinct from, and additive to,
the unavailable semantic adjudication.

## Provenance and service status

| Field | Value |
| --- | --- |
| Required model | `gpt-5.6-luna` |
| Required reasoning effort | `max` |
| Service attempts | Initial invocation and one same-lineage retry |
| Agent lineage | `019ff359-b4a3-7b70-9af6-9f4f6bb56dfc` |
| Attempt outcomes | Both completed without final text and without either authorized output path |
| Service status | `INTERRUPTED_NO_USABLE_REVIEW_OUTPUT` |
| Usable Luna semantic adjudication | `false` |
| Record producer | Parent orchestration fallback; evidence preflight only, not a substitute for Luna adjudication |

## Artifact freshness

V7 labels its artifact set current, but the following observed SHA-256 values do
not equal the values in `REC-M5_GOVERNANCE_RECHECK_V7_20260812.json`.

| Artifact | V7 declared SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| `REC-M5_REVIEW_PATCH_V1_20260811.md` | `6837bbe5fe4e7f9549553b9749ebf49b0870a0a1045678234beea873f5ba8c06` | `336c3cc4e25276ac6eeb56d597b3fd8486e8a90d02c7d977ace172048138c07d` | `FAIL_STALE_V7_BINDING` |
| `REC-M5_REVIEW_PATCH_V1_20260811.json` | `cacd0e6ec75760601c6e3ed3229e122bf70810d6f5c26dec7c9435d1c304ae7b` | `8d9b1d2a7536daa6a7f7cb3ade5bc0f5b0674d2087d5efeb2fd2a8dcbf3e603a` | `FAIL_STALE_V7_BINDING` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `d622854aba0b0e190ef8653fc87ab95324239be5257ff02d25478e2cdde571cd` | `d622854aba0b0e190ef8653fc87ab95324239be5257ff02d25478e2cdde571cd` | `PASS` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `a0890f4c956853c2564478f1f205be93d3694562aefde8b0068bedb4e2dc0018` | `83197e8828f894cabf9b21fe108be0c61c751dc8c967bdca684dc1220dfe4913` | `FAIL_STALE_V7_BINDING` |

The current review-patch hashes do match the source-document hashes recorded in
the author-input request. This does not repair V7's separate current-artifact
binding claim.

## Evidence preflight

The following checks establish only availability and internal binding of declared
evidence. They do not turn this record into the missing Luna semantic review.

- `scripts/natcs_benchmarks.mjs` has SHA-256
  `9cfe55a771f7434617bf67bbc78c22aadcd74fd528b4ea5d8b7762e0ad2b4633`,
  matching the ALS/topology extraction.
- `output/natcs_benchmarks/benchmark_summary.csv` has SHA-256
  `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`,
  matching both candidate extractions.
- G04 declares `100 * (local_network_metric_median - cp_network_metric_median) /
  local_network_metric_median`: a ratio of across-replication medians with the
  same-scenario `local_network` denominator and `cp_network` candidate. The four
  declared values bind `coef_error_median` to `effective_operator` and
  `girf_error_median` to `total_response`; their released CSV medians match the
  candidate extraction.
- G06 declares a fixed 60-iteration CAL-E03 ALS call on normal completion, no
  monitored objective, stopping tolerance, or early-stop predicate, and exception
  abort/failure recording. The `1e-6` Gram regularizer is not a stopping tolerance.
- G07 declares exactly four retained rows: `high_topology_vol`,
  `sparse_misspecified`, `edge_missing`, and `noisy_network`. Their exact parameter,
  generation/observation, deterministic-seed, and asymmetric-coverage bindings are
  present in the author-input record. The three former rows give `local_network`
  three released replications and each other released method 20; the combined
  sparse/misspecified row gives every released method three.

## Scientific-boundary check matrix

| Check | Formal result | Evidence preflight | Required ceiling or blocker |
| --- | --- | --- | --- |
| Evidence-bounded claims | `BLOCKED` | Declared evidence is present and hashed for the CAL-E03 script and benchmark summary. | No semantic PASS without a usable Luna result. |
| G04 formula binding | `BLOCKED` | Formula, comparator, denominator, endpoint mapping, four values, and CSV hash are bound. | Simulation-only, declared N=15/N=30 rows; no native held-out, empirical, fairness, ranking, equivalence, or broad-superiority claim. |
| Fixed-60 ALS | `BLOCKED` | Candidate record binds fixed count, no monitored residual/objective, no tolerance, no early stop, and exception failure. | Do not infer convergence or global optimality; do not import separate 100/80 wording into CAL-E03. |
| Exact topology rows and asymmetric coverage | `BLOCKED` | Four scenario rows and released coverage counts are bound. | No matched ranking or general topology-robustness claim; endpoint availability remains per method. |
| Source-unavailable decisions | `BLOCKED` | AIN-SOURCE-01 through AIN-SOURCE-04 are explicitly recorded. | Keep application/bootstrap 100/80, spectral-radius, and 50% attenuation sources unavailable; generated TeX is not a canonical owner and must not reconstruct ownership. |
| Current readiness | `FAIL_NOT_READY` | Patch and author-input records say ready for independent review; V7 itself requires this Luna/max recheck. | Luna service produced no adjudication and V7 current-artifact binding is stale. |
| Overclaim ceilings | `BLOCKED` | Declared ceilings are visible in the current patch. | Preserve V1-026 non-execution/claim block, V1-033 unresolved provenance and endpoint gaps, V1-045 N=20/N=50-only scope, N=100/N=200 abstention, and blocked/null resource telemetry. |

## Source-unavailable decisions

- Application/bootstrap 100/80 iteration wording: canonical Markdown owner remains
  unavailable; generated `main.tex` and `supplementary.tex` are not canonical
  ownership sources.
- Spectral-radius wording: canonical source remains unavailable and cannot be
  reconstructed from generated TeX or mapped into the controlled benchmark.
- 50% top-exposure attenuation: canonical source remains unavailable and remains
  outside CAL-E03.
- No unavailable source may be silently upgraded to source-backed evidence by this
  review record.

## Required recovery before a PASS

1. Regenerate or otherwise supply a hash-current governance receipt for the exact
   review-patch and author-input artifacts to be reviewed.
2. Obtain a completed `gpt-5.6-luna` `max` scientific-boundary review with an
   auditable final response and both requested output artifacts.
3. Preserve the listed claim ceilings and obtain separate authorization before any
   manuscript or formal-register mutation.

## Scope and changed paths

This was review-only. No manuscript source, formal register, scientific payload,
authorization file, generated TeX file, script, test, or Git state was changed by
this operation.

Changed paths:

- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_V4_20260812.md`
- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_V4_20260812.json`
