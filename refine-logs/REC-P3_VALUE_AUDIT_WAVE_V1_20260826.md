# REC-P3_VALUE_AUDIT_WAVE (V1, 2026-08-26)

Record class: `p3_wave_consolidation_record`
Generated: 2026-08-26 (Asia/Shanghai)
Route position: P3 stage-1 (value-level audits of both quarantined corrected runs) COMPLETE; stage-2 (independent paper-to-evidence audit) dispatched concurrently with this record; stage-3 (downstream build + promotion) remains a separate author decision.

## Lane outcomes

| Lane | OVERALL | Basis |
| --- | --- | --- |
| NYC-01 (`psa-20260719-nyc-01`, 18 files) | SUPPORTED_FOR_DOWNSTREAM_REVIEW | V-T1 PASS (qualified) · V-T2..T5 PASS |
| RCEP-03 (`psa-20260719-rcep-03`, 36 files) | SUPPORTED_FOR_DOWNSTREAM_REVIEW | V-T1 PASS (qualified, instrument-mediated) · V-T2 PARTIAL · V-T3 PASS_WITH_FLAGS · V-T4 PASS · V-T5 PASS_AS_READINESS_ONLY |

Neither outcome is a promotion; standing blockers (PAPER_CLAIM_AUDIT BLOCKED, EMPIRICAL_IMPLEMENTATION_AUDIT FAIL) and the `self_supervised_proxy` ceiling are unchanged; nothing was activated.

## Instrumentation topology (mandatory disclosure)

Both lane sessions suffered total process-spawn failure (bash ENOENT initial+retry; glob/grep ripgrep-launch failures), so neither auditor could hash bytes. Remediation pattern (mirrors REC-M5_SCIENTIFIC_RECHECK_V6 INSTRUMENTATION_ADDENDUM): orchestrator executed the SHA-256/size/symlink/extras passes (tmp/nyc_vt1_measurement_20260826.json, tmp/rcep_vt1_measurement_20260826.json); each lane party independently adjudicated the instrument against its own prior full-file reads and accepted it. Results: NYC 18/18 MATCH, RCEP 36/36 MATCH; zero drift, zero extra-on-disk, zero symlinks in both trees. Provenance chain accepted by both adjudications: inventory digests were recorded pre-migration against the Desktop tree; today's ~/work copies match them exactly, i.e. migration did not perturb either quarantined run.

## Row-12 incident closure (NYC)

The NYC auditor found its own earlier rendering of inventory line 68 diverged by one hex character from the current-authoritative value, adjudicated as auditor-side transcription error, corrected transparently in both receipts. The auditor named three decisive follow-ups; the orchestrator executed all three: (1) git history — inventory has historical snapshot commits, ZERO changes today; (2) mtime 2026-08-12 13:41:40 — predates this session by two weeks, excluding mid-session mutation outright; (3) fresh hash echo of figures/fig_cp_mobility_illustration.png == 914ee3a79686a007b02c349883f2b82f655c1c1f9867c68fb3429d26c78ed91f == current inventory value. Incident CLOSED: transcription error confirmed, no byte anywhere changed.

## Inherited leads: both CONFIRMED by measurement (RCEP)

(i) Quarantine stability_summary.csv = 19/36 unstable (rate 0.527778 ≡ its selection_summary.stability_rate_cp) vs stale promoted all-stable 0/36. (ii) Spectral radius band candidate [0.44966, 1.44895] crossing 1.0 for 19 consecutive quarters from 2020-06-30 vs stale [0.21109, 0.74553]. Stale full_fit_loss 1.014484343302525 exactly matches the governance identifier.

## Flags carried forward into downstream review

- RCEP F1: requested GIRF date 2022-12-31 silently substituted by 2020-03-31; both dates have complete outputs; rationale undocumented in any artifact.
- RCEP F2: headline evolving coefficient 0.00229679 lies OUTSIDE its own bootstrap percentile CI (p975=0.00203265) though analytic-SE p≈5.4e-11.
- RCEP F3: stable-dates-only regression honestly not_identified (TC_relief collinear; N=3570=210x17).
- NYC characterizations: stability_rate semantically equals UNSTABLE share; requested GIRF month-ends remapped to COVID-onset months (stale tree honored requests); evaluated origins uniformly 66<69; negative late-period g_net estimates; no RNG seed recorded anywhere.

## Boundary statement

This record consolidates read-only review outcomes only. It promotes nothing, mutates no evidence artifact, activates no claim, edits no manuscript source, and executes no make/test/scientific target. Downstream build + promotion remain subject to a separate author decision after the stage-2 paper-to-evidence audit returns.
