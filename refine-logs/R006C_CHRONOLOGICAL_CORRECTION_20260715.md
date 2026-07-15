# R006c Chronological-Validation and Provenance Correction

**Date:** 2026-07-15  
**Status:** frozen before corrected outcome execution

## Reason

The first independent integrity review confirmed the R006c numerical `FAIL`, endpoint non-leakage, gate fidelity and duplicate determinism, but identified two audit gaps before claim judgment:

1. fused-TV selection excluded the final evaluation tail but smoothed the complete validation prefix before scoring each validation date; this was not strictly rolling within that prefix;
2. construction provenance hashed the four R006c modules but did not hash three executed numerical dependencies.

The initial primary and duplicate outputs are preserved as historical pre-correction artifacts in:

```text
output/high_impact_revision/r006c_endpoint_aware_pre_chronological_correction/
output/high_impact_revision/r006c_endpoint_aware_repeat_pre_chronological_correction/
```

## Frozen Correction

For each fused-TV penalty and validation date, the corrected selector reconstructs only the local-estimate prefix available through that date and scores the final coefficient of that prefix at the corresponding observed training topology. No later validation local estimate and no evaluation-tail estimate can affect that date's score. Candidate scores aggregate the per-date prediction squared errors over the same frozen validation dates.

Construction provenance now hashes:

- `r006c_endpoint_protocol.py`
- `r006c_endpoint_estimators.py`
- `r006c_endpoint_metrics.py`
- `r006c_endpoint_aware_experiment.py`
- `high_impact_metrics.py`
- `r005_separation_stability_pilot.py`
- `r006b_stability_signal_deconfounding.py`

The approved grid, nine methods, random-stream mapping, endpoint availability, required cells, thresholds and stop-go interpretation are unchanged. Corrected formal outputs must be regenerated from new pre-outcome construction artifacts and independently duplicated before result-to-claim judgment.
