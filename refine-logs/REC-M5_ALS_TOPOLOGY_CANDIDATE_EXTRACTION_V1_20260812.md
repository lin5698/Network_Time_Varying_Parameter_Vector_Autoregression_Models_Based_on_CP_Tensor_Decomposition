# REC-M5 ALS and Topology Candidate Extraction V1

Status: `AUTHOR_CONFIRMED_FOR_AIN_ALS_AND_AIN_TOPOLOGY`

This record extracts implementation facts from `scripts/natcs_benchmarks.mjs` and
released benchmark CSVs. The user confirmed the CAL-E03 ALS and topology facts on
2026-08-12. It does not authorize manuscript application or activate a scientific claim.

## ALS candidate facts

- The controlled `cpAls` call normally executes a fixed 60 iterations.
- It monitors no objective or residual and has no convergence tolerance or early stop.
- The `1e-6` value is a Gram regularizer, not a stopping tolerance.
- If an exception aborts the call, the caller records a failure.
- Generated TeX contains separate at-most-100 application and at-most-80 bootstrap
  wording, but its canonical Markdown ownership remains unresolved.

## Topology candidate facts

| Scenario | Role | Exact settings | Released replication coverage |
| --- | --- | --- | --- |
| `high_topology_vol` | generation | `topologyVol=0.18`, `sparsity=0.15` | local 3; each other released method 20 |
| `sparse_misspecified` | generation and observation | `topologyVol=0.08`, `sparsity=0.55`, `wNoise=0.18` | each released method 3 |
| `edge_missing` | observation, with changed generation volatility | `topologyVol=0.06`, `wDrop=0.30` | local 3; each other released method 20 |
| `noisy_network` | observation, with changed generation volatility | `topologyVol=0.06`, `wNoise=0.35` | local 3; each other released method 20 |

The missing-edge mechanism drops each observed nonzero off-diagonal edge with
probability 0.30 and row-normalizes. The noisy-weight mechanism mixes 0.65 of the
generated W with 0.35 of an alternative random graph and row-normalizes.

## Author confirmation and remaining boundary

The user confirmed the implementation source, retained scenarios, fixed-60 wording,
code-derived seed policy, asymmetric replication disclosure and the absence of a
canonical Markdown source for application/bootstrap 100/80 wording. The released
stress coverage is not uniformly matched across methods, so these rows cannot support
a matched ranking or general topology-robustness claim. Canonical source ownership for
spectral-radius wording and 50% top-exposure attenuation remains unresolved.
