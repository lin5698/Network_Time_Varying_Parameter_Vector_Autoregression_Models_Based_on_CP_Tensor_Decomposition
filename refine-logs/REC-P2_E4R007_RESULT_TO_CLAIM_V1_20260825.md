# REC-P2 E4-R007 Result-to-Claim Review (V1, 2026-08-25)

Record SHA-256: `718bf5ae2ab5887b1a8cb5298a36ab78eeb41792762cb526b230b5630e1b2f64`

**Record class:** result_to_claim_review  
**Generated:** 2026-08-25 (Asia/Shanghai)  
**Authority:** Author decision D3 (RESCOPE_NOT_SCHEDULE), authorized 2026-08-24/25.

## Purpose

Independent result-to-claim review of E4-R007 against the frozen E4 r3 synthetic bytes, per NCS_E4_R3_EXPERIMENT_AUDIT_20260801 required next action #2. NO new execution. NO claim activation. Read-only.

## Inputs consumed (measured SHA-256)

| path | sha256 | role |
| --- | --- | --- |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json` | `09394a3c68a0babc…` | frozen_r3_result |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json` | `18e7dc81acf8c75d…` | frozen_completion_marker |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json` | `42d2b2da3649c4cf…` | frozen_execution_manifest |
| `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` | `921033acbf4568d6…` | prior_independent_audit |
| `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.json` | `60523c09126fca78…` | prior_independent_audit_machine |
| `refine-logs/EXPERIMENT_PLAN_20260731_115719.md` | `777f77f753b78f18…` | predeclaration_source |

## R3 scope measured

- **interval_records_total**: `160`
- **interval_cells_total**: `8`
- **families**: `['family1', 'family2']`
- **n_values**: `[20, 50]`
- **horizons**: `[4]`
- **methods**: `['fixed_rank_basis']`
- **query_classes**: `['cross_generator', 'in_family_interpolation']`
- **all_records_status_AVAILABLE**: `True`
- **all_records_coverage_1_0**: `True`
- **all_records_completed_replicates_80**: `True`
- **all_records_requested_replicates_80**: `True`
- **aggregated_bootstrap_status_counts**: `{'AVAILABLE': 12800, 'NONCONVERGED': 0, 'NONFINITE': 0, 'OUTSIDE_TARGET': 0, 'UNSTABLE': 0}`
- **non_available_bootstrap_count**: `0`

## Per-cell measured (8 interval cells)

| cell | n | panels | available | declared | boot | cov | rho_est_max | rho_truth_max | mean_width | raw_mse_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| family1|20|cross_generator | 20 | 20 | 20 | 20 | 1600 | 1.0 | 0.6186 | 0.3701 | 0.4158 | 1.01e-05 |
| family1|20|in_family_interpolation | 20 | 20 | 20 | 20 | 1600 | 1.0 | 0.4534 | 0.3441 | 0.3367 | 2.39e-06 |
| family1|50|cross_generator | 50 | 20 | 20 | 20 | 1600 | 1.0 | 0.6704 | 0.3957 | 0.4606 | 2.73e-06 |
| family1|50|in_family_interpolation | 50 | 20 | 20 | 20 | 1600 | 1.0 | 0.5235 | 0.3339 | 0.4460 | 6.48e-07 |
| family2|20|cross_generator | 20 | 20 | 20 | 20 | 1600 | 1.0 | 0.4717 | 0.3649 | 0.0960 | 2.29e-06 |
| family2|20|in_family_interpolation | 20 | 20 | 20 | 20 | 1600 | 1.0 | 0.2823 | 0.3193 | 0.0487 | 1.83e-07 |
| family2|50|cross_generator | 50 | 20 | 20 | 20 | 1600 | 1.0 | 0.4464 | 0.3787 | 0.0743 | 3.16e-07 |
| family2|50|in_family_interpolation | 50 | 20 | 20 | 20 | 1600 | 1.0 | 0.3544 | 0.3025 | 0.0592 | 3.94e-08 |

## Terminal provenance

- e3-results.promotion: `PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT`
- execution-complete.promotion: `PROHIBITED`
- execution-manifest.status: `RUNNING_QUARANTINE_ONLY`
- note: execution-manifest.status = RUNNING_QUARANTINE_ONLY while execution-complete.status = COMPLETE_QUARANTINE_ONLY. This is the WARN-forecasting terminal-status mismatch recorded as D3-G3. The 160 AVAILABLE records and both markers are present; the mismatch is a provenance-label inconsistency, not a data-availability gap.

## Claim-to-path mapping: E4-R007

| claim fragment | frozen path | measured | verdict |
| --- | --- | --- | --- |
| 160 panel-level interval records present | `results.interval_records` | `len=160` | CONFIRMED |
| 8 interval cells present | `results.interval_summary` | `8 keys` | CONFIRMED |
| each record status AVAILABLE | `results.interval_records[*].status` | `all AVAILABLE` | CONFIRMED |
| 80 available bootstrap replicates per record | `results.interval_records[*].completed_replicates` | `all 80` | CONFIRMED |
| 20 simulated panels per cell | `results.interval_summary[*].distinct_panels / declared_panel_records` | `all 20` | CONFIRMED |
| horizon 4 | `results.interval_records[*].horizon` | `all [4]` | CONFIRMED |
| does not support other horizons | `results.interval_records[*].horizon` | `horizons observed = [4]` | CONFIRMED (no h!=4 present) |
| simulation_only ceiling | `authoritative audit evaluation_type` | `simulation_only` | CONFIRMED |

## Out of scope

- **E4-R006**: STRUCTURALLY_FORECLOSED_ON_R3_BYTES — predeclared paired panel-level log error ratio and cell-level confidence interval are not serialized. No post-outcome metric substitution permitted by the prior audit. This review does not touch E4-R006.
- **RCEP/NYC**: All empirical RCEP/NYC artifacts remain under P3 quarantine; not addressed here.

## Independence disclosure

This review was produced by the same party that synthesized the M5 patch and the P2 authorization drafts. It is a result-to-claim mapping over frozen bytes, NOT an independent external reviewer's receipt, and NOT a claim activation. Activation remains a separate author decision gated by the r3 audit's status invariants (PAPER_CLAIM_AUDIT BLOCKED, EMPIRICAL_IMPLEMENTATION_AUDIT FAIL).

## Verdict

- **E4-R007 result-to-claim**: `QUALIFIED_SUPPORTED`
- **qualifier**: WARN-inherited terminal-status label mismatch (manifest RUNNING vs complete COMPLETE) is disclosed but does not affect data availability. All 160 records AVAILABLE, all coverage 1.0, all 80/80 bootstrap, 8 cells x 20 panels. Ceiling retained: simulation_only, h4, 20 panels/cell.
- **claim activation**: `NOT_ACTIVATED_BY_THIS_RECORD`

## Fail-closed notes

- No make target, test, or scientific entry was run.
- No manuscript_src, formal register, generated TeX, or frozen record was modified.
- git operations: 0.
- P0 does not block this review: all consumed r3 bytes are materialized and readable.
