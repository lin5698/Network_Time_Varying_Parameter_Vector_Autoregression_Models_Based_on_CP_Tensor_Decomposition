# R006b Causal Validation Correction

**Frozen before corrected outcome run:** 2026-07-15  
**Reason:** independent integrity audit found evaluation-period leakage into fused-TV penalty selection

## Preserved History

The original full and duplicate R006b outputs remain unchanged in:

- `output/high_impact_revision/r006b_stability_signal_deconfounding/`
- `output/high_impact_revision/r006b_stability_signal_deconfounding_repeat/`

Both retain status `FAIL`. The correction does not relabel, delete or overwrite them.

## Implementation Correction

For each fused-TV penalty, smoothing used for validation scoring is now fitted only on the local-estimate prefix ending before the evaluation segment. Evaluation-period local estimates cannot affect candidate validation scores. After selecting the penalty, the full coefficient path is smoothed for retrospective path reconstruction.

The stored `prediction_rmse` is retained for schema compatibility and duplicated under the explicit name `retrospective_prediction_rmse`. It is not described as clean out-of-sample forecasting performance.

## Unchanged Contracts

- original R006b construction and outcome thresholds
- grid, paired seeds, layers, methods and response metrics
- exact separation of raw, stability-qualified and projected sensitivity results
- R006 and original R006b `FAIL` labels

The corrected run is written to a new isolated output directory. Protocol and code SHA-256 values are stored in every corrected result payload. A construction-only artifact is written before corrected outcome execution.

## Decision Rule

The corrected run is evaluated against the original frozen thresholds. No result can be promoted because the fused comparator changes. The local-versus-Tucker comparison is unchanged in definition, but all corrected numbers are reported from the new run as a coherent set.
