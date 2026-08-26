# REC-M5 Scientific Recheck Terra V5

Date: 2026-08-12

## Verdict

`PASS` for the frozen, review-only scientific-boundary adjudication. This result
does not authorize a manuscript edit, formal-register edit, scientific execution,
claim activation, generated-TeX edit, authorization-file edit, or Git action.

## Reviewer Provenance

- Reviewer route: `gpt-5.6-terra`.
- Reasoning effort: `max`.
- Adjudication mode: direct self-adjudication.
- Delegation, CLI adjudicator, Qwen, and external payload: not used.
- Scope read: only the six frozen current M5 inputs named below.
- Prohibited E4 paths read: none.

## Frozen Input Hash Verification

| Input | Expected SHA-256 | Actual SHA-256 | Result |
| --- | --- | --- | --- |
| `REC-M5_REVIEW_PATCH_V1_20260811.md` | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` | `PASS` |
| `REC-M5_REVIEW_PATCH_V1_20260811.json` | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` | `PASS` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` | `PASS` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` | `PASS` |
| `REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` | `PASS` |
| `REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` | `PASS` |

## Scientific-Boundary Adjudication

### G04: Controlled Result Statements

`PASS`. The four values agree across the patch and author-input records:
effective-operator reductions of 93.55203369881073% (93.6% display) at N=15
and 96.76394154622214% (96.8% display) at N=30, and finite-horizon response
reductions of 82.54278845800611% (82.5% display) and 87.32161861932515%
(87.3% display), respectively. They are unambiguously defined as ratios of
across-replication medians:
`100 * (local_network_metric_median - cp_network_metric_median) /
local_network_metric_median`. The denominator, endpoint fields
(`coef_error_median` and `girf_error_median`), comparator (`local_network`),
candidate (`cp_network`), and 20-replication primary-row unit are bound.

The wording retains the required ceiling: a declared synthetic-DGP, declared
endpoint, local-versus-CP, N=15/N=30 result only. It expressly excludes
independent empirical validation, fairness, broad superiority, native held-out
recovery, cross-family generality, and use of N=50 stress rows as headline
evidence. This review verifies the frozen binding and claim boundary, not an
independent recomputation from an out-of-scope evidence artifact.

### G06: Fixed-60 ALS Semantics

`PASS`. The candidate consistently specifies 60 ALS iterations as a fixed count
on normal completion, with no monitored objective or residual, no stopping
tolerance, and no early-stop predicate. The value `1e-6` is confined to Gram
regularization. An exception aborts the call and is recorded as reconstruction
failure. The candidate explicitly does not infer convergence or global
optimality and keeps application/bootstrap 100/80 wording separate because its
canonical Markdown owner is unavailable.

### G07: Topology Stress

`PASS`. All four retained settings are present with exact amplitudes and roles:
`high_topology_vol` is generation of `truth.W` with
`topologyVol=0.18, sparsity=0.15, wNoise=0, wDrop=0`; `sparse_misspecified`
binds generation and observation with `0.08, 0.55, 0.18, 0`; `edge_missing`
binds observation with generation volatility 0.06 and `wDrop=0.30`; and
`noisy_network` binds observation with generation volatility 0.06 and
`wNoise=0.35`. The frozen records disclose that local coverage is three versus
twenty for each other released method in volatility, missing-edge, and noisy-
weight rows, while sparse/misspecified has three for every released method.
The candidate therefore limits them to bounded diagnostics and expressly
forbids a matched ranking or general topology-robustness claim.

### G08 and Source Ownership

`PASS`. The candidate keeps the controlled-benchmark spectral-norm and
unscaled-instability thresholds distinct from separately reported spectral-radius
diagnostics. It neither reconstructs unowned spectral-radius wording nor imports
a spectral-radius metric mapping. The author-input and patch records agree that
the canonical Markdown owners for application/bootstrap 100/80 iterations,
spectral-radius wording, and 50% top-exposure attenuation are unavailable;
generated TeX is explicitly excluded as an ownership source, and attenuation
remains outside CAL-E03.

## Claim Ceilings and Authorization Boundary

`PASS`. The patch remains candidate-only and all relevant ceilings are retained:
V1-026 remains descriptive with scientific execution `NOT_RUN` and claim
activation `BLOCKED`; V1-033 remains simulation-only with empirical ground truth
`NOT_EVALUABLE`; and V1-045 remains partial, restricted to N=20/N=50,
`N=100/N=200 NOT_RUN/ABSTAIN`, `resource_telemetry BLOCKED/null`, and not
repeated-run reproducibility. No frozen record upgrades those states.

The authorization boundary remains exactly review-only: manuscript-source and
formal-register mutation are `NOT_AUTHORIZED`; scientific-payload and
authorization-file mutation are `PROHIBITED`; generated-TeX mutation is
`PROHIBITED`; scientific execution and claim activation are `NOT_AUTHORIZED`;
and Git operations are `NONE`. A separate M5-D authorization remains required
before any manuscript mutation, and a separate M5-F authorization remains
required before any formal-register mutation.

## Failure Policy and Changed Paths

No service, missing-input, or hash failure occurred. Under this recheck policy,
any such failure would produce `BLOCKED`, never `PASS`.

Exactly changed paths:

- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V5_20260812.md`
- `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V5_20260812.json`
