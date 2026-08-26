# SCIENTIFIC EXECUTION AUTHORIZATION - WAVE B METHODOLOGICAL REMEDIATION (draft)

id: rcep-nyc-wave-b-methodological-20260826-230000-cst-01
Authorizer: Yilin Wu | status: PLANNED_PENDING_AUTHOR_SIGNATURE | authorized_at: 2026-08-26T23:00:00+08:00

## Purpose

One merged methodological re-run per empirical dataset to complete Wave B:
1. F2 bootstrap correction - emit point AND bootstrap median with percentile interval for the
   flagged statistic; promote the interval-supported summary or disclose skew explicitly.
   Finding: point 0.0023 outside CI with bootstrap p50 approx 0.00073; genuine skew,
   deterministically reproducible under fixed seeds.
2. F3 absorption variant - complete the half-implemented variant (:1654-1660) and record
   whether a stable subsample is identified or remains not_identified.
3. Seed echo - echo root seed 20260328 and per-stage seeds into all artifact headers,
   with equivalence check against frozen pre-Wave-B outputs for unchanged components.
4. (Optional) g_net offline decomposition from existing CSVs.

## Implementation files (digest-locked)

- scripts/run_cp_empirical_pipeline.py  647f35cd433d0fb12b8d7ae903ad09bdf874a8fe01421b47c7fb1b22a371c31e
- scripts/natcs_design_contract.py      45e14cb8fdaf10e2f4b07e7a27c630841e968994cd246e44d0e27c017a58388b

## Run plan

- NYC: READY (env NATCS_NYC_TAXI_DATASET_DIR = tmp/external/vars_repo/datasets/NYC-taxi,
  commit 7e63ba9, npz digests verified).
- RCEP: BLOCKED_PENDING_HELPER_ORIGIN (legacy path dead; trust manifest pins commit
  d0e398b + file digests for verification once origin is supplied).
- Outputs: output/natcs_empirical_cp_authorized_runs/rcep-nyc-wave-b-methodological-20260826-230000-cst-01/

## Quarantine contract

All outputs remain inactive boundary material until a re-adjudication lane and an explicit
author RC-1 promotion decision. No manuscript-source change occurs under this instrument.

## Preconditions

1. Author signature (field OPEN_PENDING_CONFIRMATION).
2. NYC env bound (ready). RCEP env bound after helper origin resolution.
3. Dependency freeze (tmp/requirements_freeze_20260826.txt).
4. Output root exists (created).

---
Drafted 2026-08-26 under author Wave B authorization to draft; assistant-drafted;
orchestrator-executed hashing; author signature field OPEN awaiting confirmation.
