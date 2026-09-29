# REC-M2 Preflight: BLOCKED

Generated at `2026-08-04T03:14:51+08:00` for parent task `019fbdde-2c02-7662-b9d2-9dc2b70e1253`.

## Conclusion

The fail-closed compatibility gate is **BLOCKED** before any real analyzer CLI. The current formal register and all frozen input hashes are internally consistent, but the four restored analyzers cannot directly bind `ncs-four-analysis-authorization-v2` without source changes. The legacy authorization was not reused, no analyzer CLI was called, and no scientific output root was created.

Governance status: `BLOCKED`.

Scientific status: `NOT_RUN`.

## Rechecked Inputs

- Current register: `output/ncs_review_corpus/v1_author_decision_register.json`, SHA-256 `c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2`.
- Current V1 payloads: `V1-026 eb30214e...`, `V1-033 79937fd8...`, `V1-035 c9b9c201...`, `V1-045 25cd8fbf...`; canonical byte counts are 2111, 2094, 2152, and 2281.
- M0 receipt: `168b692d...`; authorization v2: `7d657681...`; M1 receipt: `71e5e0bd...`.
- E4-r3 results/manifest/completion/inventory: `09394a3c...`, `42d2b2da...`, `18e7dc81...`, `5cf086c4...`.
- E4-r3 candidate and workspace authorization: `0c49bca6...` and `73c135ed...`.
- All eight analyzer/test files were present, had the recorded byte hashes, and parsed with `python3 -B ast.parse`. No bytecode was written.

The E4-r3 input structure has 46,080 recovery records, 48 recovery summary cells, 32 paired cells, 160 interval records, 8 interval cells, and 12,800 bootstrap records. The raw frozen records currently contain only `AVAILABLE` statuses; the zero adverse counts do not substitute for the required output retention check, which was not run because the compatibility gate stopped execution.

## Blocking Findings

All four analyzers read legacy authorization fields that are absent from v2: `frozen_inputs`, `authorized_register_items`, and, for E03, `execution_policy`.

- `CAL-E01:75`: [analyze_cal_e01_75.py](/Users/wuyilin/Desktop/translation/Network_Time_Varying_Parameter_Vector_Autoregression_Models_Based_on_CP_Tensor_Decomposition/scripts/experiments/analyze_cal_e01_75.py:551) requires `authorization.frozen_inputs`, with legacy hash keys at lines 553-556 and 571; lines 601-608 require `authorized_register_items`. Its default output is `refine-logs/ncs_new_analysis` at line 1488. It also computes and serializes normal-approximation CIs and derived log-ratio payloads at lines 243, 880-881, and 1418, beyond the requested E01 raw comparator ledger / paired-difference boundary.
- `CAL-E02:128`: [analyze_cal_e02_128.py](/Users/wuyilin/Desktop/translation/Network_Time_Varying_Parameter_Vector_Autoregression_Models_Based_on_CP_Tensor_Decomposition/scripts/experiments/analyze_cal_e02_128.py:32) hardcodes the old register SHA `3e1aa708...`; lines 519-523 read legacy `frozen_inputs`; lines 541-556 look for top-level `calibration_id` instead of the current nested `calibration_source.calibration_id`; line 1047 defaults to the old authorization file. The code also creates fresh protocol/candidate/preoutcome payloads at lines 975-1038, outside the M2 report-only boundary.
- `CAL-E02:135`: [analyze_cal_e02_135.py](/Users/wuyilin/Desktop/translation/Network_Time_Varying_Parameter_Vector_Autoregression_Models_Based_on_CP_Tensor_Decomposition/scripts/experiments/analyze_cal_e02_135.py:36) hardcodes the old register SHA; lines 491-500 read legacy `frozen_inputs`; line 458 treats a missing expected hash as a match; lines 1022-1025 continue with no authorized item; and line 1218 defaults to the old authorization. Lines 1060-1064 and 1145-1147 create fresh protocol/candidate/preoutcome files, which is not part of the requested descriptive M2 run.
- `CAL-E03:164`: [analyze_cal_e03_164.py](/Users/wuyilin/Desktop/translation/Network_Time_Varying_Parameter_Vector_Autoregression_Models_Based_on_CP_Tensor_Decomposition/scripts/experiments/analyze_cal_e03_164.py:27) retains the old register SHA constant; lines 641 and 678-685 read legacy `frozen_inputs`; lines 744-759 require `authorized_register_items`; lines 771-780 require `execution_policy`. With v2 unchanged, it falls through to a null expected register hash and a blocked authorization gate rather than a direct v2 binding.

The corresponding tests encode the legacy schema or do not exercise authorization binding: `test_analyze_cal_e01_75.py` only tests local metric retention; `test_analyze_cal_e02_128.py` uses the legacy default authorization; `test_analyze_cal_e02_135.py` constructs `authorized_register_items` and `frozen_inputs`; and `test_analyze_cal_e03_164.py` points at the legacy authorization and asserts the old register mismatch.

## Write And Scope Audit

Static source contracts show content-addressing and no-overwrite checks in all four analyzers, and explicit retention paths for failed/non-finite/unstable records. Those contracts were not exercised in M2 because authorization compatibility is a precondition. The required v2 root `refine-logs/ncs_new_analysis_v2` did not exist before this preflight and remains without scientific artifacts.

Protected input and source hashes were captured before writing this receipt. The after-write recheck is recorded in the JSON receipt; it must match the before-write values. No register, manuscript, analyzer/test, E4-r3 quarantine, E4-r3 candidate, inventory, RCEP, NYC, S1-S4, or N=100/200 file was modified.

## Minimum Repair

Before a new M2 attempt, update the analyzer/test contract to require `ncs-four-analysis-authorization-v2` directly, bind the current register and exact canonical V1 item payloads, bind every required E4-r3 hash from `frozen_e4_r3_inputs`, and fail closed on missing fields. Remove old register constants and default authorization paths. Fix the CAL-E02:128 nested register selector. Constrain E01 to raw comparator/paired outputs only, keep E02:128 and E02:135 descriptive without creating fresh S-route freeze payloads, and add tests for v2 binding, legacy rejection, no-overwrite, required run paths, and complete status retention.

No M2 analyzer run is authorized from this preflight. A later retry requires a new versioned preflight after those source/test changes.
