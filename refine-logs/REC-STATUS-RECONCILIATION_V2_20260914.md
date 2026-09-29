# Status Reconciliation Receipt V2

- Date: 2026-09-14
- Task: A1 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (current-status vs historical-audit mapping)
- Scope: read-only reconciliation. Inputs: the three root audits (`EXPERIMENT_AUDIT`, `PAPER_CLAIM_AUDIT`, `PROOF_AUDIT`), the additional root re-adjudication `EMPIRICAL_IMPLEMENTATION_AUDIT`, the two controlling P6 receipts, the author decision sheet, the experiment tracker and the recovery tracker. This receipt does not modify, supersede or activate any scientific claim, closes no external gate, and creates no Git snapshot.
- Lineage: extends `REC-STATUS_RECONCILIATION_V1_20260829` and `REC-P6_STATUS_RECONCILIATION_REBUILD_V1_20260831`. Controlling release baseline: `REC-P6_POST_DECISION_REBUILD_V1_20260903` and `REC-P6_WEEKLY_MAINTENANCE_V1_20260903`.

## Audit status map (scope / verdict / condition)

| Artifact | jq path(s) | Verdict | Verdict scope | Standing condition |
| --- | --- | --- | --- | --- |
| `EXPERIMENT_AUDIT.json` | `.overall_verdict` = `fail`; `.integrity_status` = `fail`; `.scientific_outcome` = `fail` | **FAIL (historical, retained)** | Original 2026-07-19 execution-readiness scope plus preserved R006c negative method gate. The 2026-07-31 E4 addendum (`.e4_preoutcome_audit.overall_verdict` = `pass`) is explicitly local pre-outcome only and does not supersede the overall FAIL. | Historical FAIL is preserved verbatim; it must not be rewritten to an overall PASS. New audits may only state their own scope relative to the current downstream-build gate. |
| `EMPIRICAL_IMPLEMENTATION_AUDIT.json` | `.verdict` = `PASS`; `.reason_code` = `rcep_nyc_value_audited_downstream_build_authorized` | PASS (scoped) | Releases only the authorized downstream rebuild gate. Promotes nothing, activates nothing. | Audit-time conditions (`.remaining_conditions`): RC-1 `NOT_GRANTED`, RC-2 `REQUIRES_SEPARATE_AUTHORIZATION`. Current posture is superseded by author decisions D-2/D-3 (see below), not by this audit. |
| `PAPER_CLAIM_AUDIT.json` | `.verdict` = `PASS`; `.reason_code` = `rcep_nyc_value_audited_no_active_stale_citations` | PASS (scoped) | Fail-closed re-adjudication: no active manuscript source binds to stale promoted or quarantined values in the audited active source set. | Re-audit required if any boundary-draft marker is removed, the evidence-build gate is rewired, or any ledger fence is edited (`.release_condition`). Does not grant promotion. |
| `PROOF_AUDIT.json` | `.verdict` = `PASS`; `.reason_code` = `all_active_source_only_proof_obligations_complete` | PASS (scoped) | Source-only mathematical claims on three hashed manuscript files. Non-controlling for release. | No empirical application, estimator superiority, rank recovery, calibration or release conclusion is covered. |
| P6 release baseline | `refine-logs/REC-P6_POST_DECISION_REBUILD_V1_20260903.md`; `refine-logs/REC-P6_WEEKLY_MAINTENANCE_V1_20260903.md` | Local build complete | Focused suite 8/8; five make targets (`natcs-evidence` … `natcs-upload-freeze-manifest`) all succeeded; final gate `PASS_WITH_WARNINGS_ALLOWED` 225 passes / 0 errors; release safety 0 blockers / 0 warnings over 425 files; inventories 27 submission materials / 11 freeze artifacts / 342 reviewer-archive files. | Local package integrity only. Upload, portal entry, repository/DOI claim and Git snapshot remain unauthorized. |

## Current posture map

| State object | Controlling record | Current state | Standing condition |
| --- | --- | --- | --- |
| Author decisions | `manuscript_src/natcs/natcs_final_author_decision_sheet.md` D-2/D-3 | `RC-1 = ACTIVATED`; `RC-2 = ACTIVATED_WITH_LIMITATIONS`; `RCEP F3 = not_identified`; active empirical numbers limited to the four D-4 percentages (93.6 / 96.8 / 82.5 / 87.3). | Section 4 still carries 4 open author-confirmation items; upload stays gated on them. |
| External gate: final author decision | P6 receipts | 4 open markers | Counted independently; no cross-gate inference. |
| External gate: Fig. 2 portal preview | `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md` | Checklist disabled; 5 `Not checked` preview markers; no portal observation exists | Only a real portal observation may close a row; the local surrogate is a gate test only. |
| External gate: raw-source access / licence | P6 receipts | 42 open markers | No DOI, licence, access or redistribution inference. |
| External gate: public-release readiness | P6 receipts | 25 open markers | Repository/DOI/public release remain open. |
| Experiment tracker | `refine-logs/EXPERIMENT_TRACKER.md` (E4-R006…R009 rows) | E4-R006 `BLOCKED`; E4-R007 `BLOCKED`; E4-R008 `PASS` restricted to artifact-level descriptive use (activation and promotion stay blocked); E4-R009 `BLOCKED` | No rerun without explicit authorization, pre-registered protocol and frozen inputs. |
| Recovery tracker | `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md` | `REC-M0 = PASS`; `REC-M1 = PASS`; `REC-M2`…`REC-M5 = BLOCKED`; OPT-S1…S4 decision-pending/deferred | M2–M5 remain blocked pending governance recovery. |
| Frozen R006c endpoint-aware qualification | `EXPERIMENT_AUDIT.md` preserved checks | CP `0/16`; Tucker `6/16` (6/8 matched, 0/8 native); no candidate promoted | Must not be mixed with early positive benchmark wording; no method is promoted. |
| Strongest current scientific claim | Plan §1 boundary | Query-preserving representation/estimand principle | Must not be stated as CP estimator superiority. |

## Reconciliation conclusion

The historical `EXPERIMENT_AUDIT` overall FAIL is retained unchanged: it describes its original audit scope, and the later re-adjudications discharge only downstream-build preconditions under their own stated scopes. The author's D-2/D-3 decisions activate promotion and claim posture with limitations, but RC-3 post-regeneration review has not run on any currently rebuilt package and all four external gate groups remain open. The package state is therefore **readiness maintenance with external gates open**, not submission-closed.

No experiment was run, no manuscript source was changed, no claim was promoted, no external marker was closed, and no Git snapshot was created by this receipt.

## Verification

- Every jq path listed above was extracted from the referenced artifact with `jq -r` on 2026-09-14; all resolve.
- `git diff --check`: passed (only the two new receipt files of this task were added; pre-existing user changes untouched).
