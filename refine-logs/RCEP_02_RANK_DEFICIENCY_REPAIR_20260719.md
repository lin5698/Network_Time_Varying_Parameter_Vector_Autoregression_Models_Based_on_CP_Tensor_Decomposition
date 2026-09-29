# RCEP stability-exclusion repair record

## Scope

This record covers only the code repair after the failed `psa-20260719-rcep-02` run. It does not authorize or report a new scientific execution, R006e/R006f outcome, downstream build, or manuscript promotion.

## Failure diagnosis

The previous run reached `stability_exclusion_summary()` and failed because the stable-date subset had no identifying variation in `TC_relief`: all 17 retained stable dates had `TC_relief = 0`. A pair-and-date fixed-effects regression therefore cannot identify the treatment coefficient. Forcing `PanelOLS` to continue with `check_rank=False` would create an invalid scientific estimate.

## Repair

`fit_panel(..., allow_unidentified=True)` now performs an explicit rank/absorption check for diagnostic subsets. If the regressor is not identified, it returns `Status=not_identified`, leaves coefficient, standard error and p-value missing, and records the reason. The stability sensitivity plot labels that point `not identified` instead of plotting a fabricated interval. Default estimation paths still reject rank-deficient designs.

## Verification

- `python3 -m unittest discover -s tests -p 'test_cp_pipeline_contracts.py'`: 62 tests passed.
- `python3 -m unittest discover -s tests -p 'test_cp_rank_selection.py'`: 3 tests passed.
- `python3 -m py_compile scripts/run_cp_empirical_pipeline.py`: passed.
- Added regression coverage: `StabilityExclusionContractTests.test_stability_exclusion_reports_unidentified_regression`.

## New candidate

- Candidate: `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_RCEP_03_20260719.json`
- Candidate SHA-256: `ab9556bef62a8086bb6b05787f5442318107507ed8ffc06b9b289747f22f347f`
- Runner SHA-256: `647f35cd433d0fb12b8d7ae903ad09bdf874a8fe01421b47c7fb1b22a371c31e`
- Output root: `output/natcs_empirical_cp_authorized_runs/psa-20260719-rcep-03/rcep`

The candidate remains pending explicit approval of this exact candidate SHA.
