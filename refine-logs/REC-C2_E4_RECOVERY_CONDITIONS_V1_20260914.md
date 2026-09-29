# REC-C2: E4-R006–R009 and REC-M2–M5 Recovery-Condition Checklist (V1, 2026-09-14)

- Date: 2026-09-14
- Task: C2 / P1 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (task-matrix row C2; workflow WS-B: "audit the blocking causes, input-freeze conditions and missing artifacts of E4-R006–R009 and REC-M2–M5")
- Scope: strictly read-only audit. No experiment, analyzer, executor, make target or test was run; no hash was computed; no tracker status was changed; no claim was activated; no Git snapshot was created. The only file created is this receipt.
- Lineage: extends `REC-STATUS-RECONCILIATION_V2_20260914` (A1 current-status map, read first per task order). Predecessor lane C1 (endpoint-aware evidence-boundary memo) was not found in `refine-logs/` as of this date (see Open Finding F3); this audit is anchored on the A1 map.
- Boundary: this memo documents preconditions only. It grants no authorization, discharges no gate, and flips no status. Every recovery listed below requires explicit authorization plus a pre-registered protocol plus frozen inputs before any execution.

## 1. Status map at audit time

| Item | Tracker status (path:line) | Receipt-level state | Audit posture |
| --- | --- | --- | --- |
| E4-R006 | `BLOCKED` — `refine-logs/EXPERIMENT_TRACKER.md:10` | r3 frozen bytes audited `WARN` (integrity); result-to-claim = structurally foreclosed | BLOCKED |
| E4-R007 | `BLOCKED` — `refine-logs/EXPERIMENT_TRACKER.md:11` | r3 frozen bytes `QUALIFIED_SUPPORTED`; `claim_activation = NOT_ACTIVATED_BY_THIS_RECORD` | BLOCKED (evidence qualified, activation closed) |
| E4-R008 | `PASS` (restricted) — `refine-logs/EXPERIMENT_TRACKER.md:12` | gate receipt `NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810` = `PASS`; derived metric artifact-only/descriptive | PASS-with-restriction |
| E4-R009 | `BLOCKED` — `refine-logs/EXPERIMENT_TRACKER.md:13` | no activation decision record exists; build and promotion separately closed | BLOCKED |
| REC-M2 | `BLOCKED` — `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:10` (checkpoint note `:41`) | M2C sub-lane receipt = `REC-M2C PASS` (27/27 byte-identical), tracker row never reconciled | BLOCKED (tracker) / go-gate evidenced (receipts) — see F1 |
| REC-M3 | `BLOCKED` — `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:11` | `REC-M3_ACCEPTANCE_V2_20260811.json` = `REC-M3_GOVERNANCE_ACCEPTANCE_PASS` | BLOCKED (tracker) / lane governance-accepted — see F1 |
| REC-M4 | `BLOCKED` — `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:12` | `REC-M4_INDEPENDENT_ACCEPTANCE_V4_20260811.json` = `REC-M4_INDEPENDENT_ACCEPTANCE_PASS` (governance/artifact integrity only) | BLOCKED (tracker) / V4 acceptance PASS — see F1 |
| REC-M5 | `BLOCKED` — `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:13` | M5-C CLOSED; M5-D applied 2026-08-26 under author authorization; final gates deferred to P3, later discharged by `REC-P6_POST_DECISION_REBUILD_V1_20260903` | BLOCKED (tracker) / application executed; formal register (M5-F) still unauthorized |

The A1 map records the same tracker-side posture at `refine-logs/REC-STATUS-RECONCILIATION_V2_20260914.md:27-28`.

## 2. E4 checklist

### 2.1 E4-R006 — two-family held-out recovery (M3)

1. **Current status.** `BLOCKED`, `refine-logs/EXPERIMENT_TRACKER.md:10`; confirmed `refine-logs/REC-STATUS-RECONCILIATION_V2_20260914.md:27`.
2. **Blockers (each locatable):**
   - B1 — r2 execution authorization consumed-incomplete: `refine-logs/NCS_E4_R2_EXECUTION_INCIDENT_20260731.md:46-49` ("The r2 authorization is consumed... neither the same authorization nor the same root may be reused"); root cause = external non-catchable PTY termination (`:39-43`); r2 root holds only `execution-manifest.json` (`:21-24`; root present at `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r2/`).
   - B2 — r3 identity is single-use and already executed: candidate SHA `0c49bca63813316ed65119f0f891074a290bd03392e5e9121c435dc936c199f6` (`refine-logs/NCS_E4_R3_DETACHED_EXECUTION_READINESS_20260731.md:5-7`); `invocation_limit: 1` (`refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json:19`); single-run terminal attestation (`refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json`, `$.execution_contract.runs = 1`, `$.execution_contract.last_exit_code = 0`). No reproducibility is claimable from these bytes.
   - B3 — the predeclared panel-level log-error-ratio summary and its cell-level confidence interval are not serialized in the frozen r3 bytes: scoped integrity audit `WARN`, check D (`refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md:9, 20-24, 33`), E4-R006 claim impact "QUALIFIED, NOT ACTIVATED" (`:47-56`), required next action 1 (`:70-72`); independently corroborated by FR9b `NOT_FOUND` (`refine-logs/NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.md:206`) and by `REC-P2_E4R007_RESULT_TO_CLAIM_V1_20260825.json` `$.out_of_scope["E4-R006"] = STRUCTURALLY_FORECLOSED_ON_R3_BYTES`. CI construction method and confidence level were never predeclared; post-outcome metric substitution is audit-forbidden (`NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md:21-24`).
   - B4 — standing status invariants: `PAPER_CLAIM_AUDIT = BLOCKED`, `EMPIRICAL_IMPLEMENTATION_AUDIT = FAIL` (`refine-logs/EXPERIMENT_TRACKER.md:17-18`; invariants restated `NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md:79-84`). Root `EXPERIMENT_AUDIT.md:8` overall FAIL is historical and retained; the E4 pre-outcome addendum (`EXPERIMENT_AUDIT.md:22-34`) is local pre-outcome only and explicitly does not change E4-R006 through E4-R009.
   - B5 — author decision D3 = `RESCOPE_NOT_SCHEDULE`: "E4-R006 status: BLOCKED — needs pre-outcome CI construction + confidence level spec, or a new pre-outcome declaration plus rerun (separate authorization)" (`refine-logs/REC-P2_D1D2D3_DECISION_CLOSURE_V1_20260825.md:29`).
   - B6 — the corresponding optional lane OPT-S1 (E01 predeclared log-ratio/CI) is `DECISION_PENDING` (`refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:14`).
3. **Required authorizations to resume.** All of: (a) the author must supply a serialized pre-outcome CI construction + confidence-level specification covering panel statistic, cell aggregation, weighting and failure handling (OPT-S1 gate, `NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:14`; rules at `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_PLAN.md:89-96`), or approve a fresh pre-outcome declaration; (b) any new execution needs a new candidate identity, a new absent quarantine root, and a new exact-SHA single-use authorization binding that candidate (`NCS_E4_R2_EXECUTION_INCIDENT_20260731.md:52-55`; `NCS_E4_PREOUTCOME_INTEGRITY_REVIEW_20260731.md:91-96`); (c) the launch must be detached from the interactive PTY and independently monitored (`NCS_E4_R2_EXECUTION_INCIDENT_20260731.md:53-55`; launchd contract `NCS_E4_R3_DETACHED_EXECUTION_READINESS_20260731.md:50-63`); (d) post-run `independent_claim_audit_required` remains binding (`e4-r3-workspace-author-authorization-20260731.json:38-42`).
4. **Missing artifacts / freeze conditions.** The serialized pre-registered panel-level log-error-ratio + CI artifact does not exist anywhere in `refine-logs/` (absence verified by the three audits cited in B3; OPT-S1 unresolved). The existing E4-R008 derived artifact `refine-logs/ncs_new_analysis_v2/e4_r008_primary_final/cal-e01-75-c96e620006d55b14/derived-panel-log-error-ratios.json` is post-outcome and classified `DERIVED_ARTIFACT_ONLY` / `DERIVED_DESCRIPTIVE_ONLY` (`NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.json`, `$.claim_fidelity_checks[name="derived_metric_is_artifact_only"].details`); it cannot satisfy the predeclared E4-R006 metric. Frozen inputs that must remain unchanged: r3 candidate SHA, authorization SHA `73c135edef24e8b4310297070d127d4be6f12d857e009fe178d62e30dba694e6`, r3 quarantine bytes, and inventory SHA `5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046` (tracker row `EXPERIMENT_TRACKER.md:10`; inventory jq paths above).
5. **Not allowed today.** No rerun of the E4 grid; no post-outcome selection of a normal/t/bootstrap CI to close E4-R006 (`NCS_POST_ACCEPTANCE_RECOVERY_PLAN.md:94`); no E4-R006 sentence in the manuscript; no activation or promotion; no mutation of frozen r3 bytes; no reuse of the r2 root or authorization.

### 2.2 E4-R007 — uncertainty qualification (M4)

1. **Current status.** `BLOCKED`, `refine-logs/EXPERIMENT_TRACKER.md:11`; confirmed `REC-STATUS-RECONCILIATION_V2_20260914.md:27`.
2. **Blockers:**
   - B1 — the independent result-to-claim review exists and returned `QUALIFIED_SUPPORTED`, but `claim_activation = NOT_ACTIVATED_BY_THIS_RECORD` (`NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.md:8-9, 284`), with four explicit riders (`:275-282`), including the standing invariants (`paper_claim_audit = blocked`, `empirical_implementation_audit = fail`, builds unauthorized, `:74-88`) and the disclosed FR8 manifest/completion label blemish that later records must preserve (`:211-234`).
   - B2 — the duplicate-determinism promotion gate named inside the results bytes (`$.promotion = PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT`) is un-dischargeable from the r3 bytes because `invocation_limit = 1`; it requires a separately governed duplicate execution (`NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.md:82-88, 247-249`; limit at `e4-r3-workspace-author-authorization-20260731.json:19`).
   - B3 — author deferral of E4-R007 claim activation: "Claim activation: nowhere activated (incl. E4-R007, deferred by author decision; independent receipt archived)" (`refine-logs/REC-M5_C_CLOSURE_V1_20260826.md:41`).
   - B4 — evidence ceiling: simulation-only, horizon 4, 20 panels per cell, single execution (`NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.md:238-259`; tracker note `EXPERIMENT_TRACKER.md:11`).
3. **Required authorizations to resume/activate.** (a) A separately governed duplicate execution with its own exact-SHA authorization, new/derived identity handling and content-addressed root (gate named in the frozen `$.promotion` field); (b) lifting of the standing invariants through the controlling audits — not by any downstream record; (c) an explicit author claim-activation decision reversing or superseding the recorded deferral (`REC-M5_C_CLOSURE_V1_20260826.md:41`); (d) routing through E4-R009 (the M5 activation decision) before any manuscript entry.
4. **Missing artifacts.** A governed duplicate-run result root plus duplicate-determinism receipt; a sentence-level claim ledger binding each activated sentence to exact frozen JSON key paths while retaining the `simulation_only` ceiling (required next action 3, `NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md:75-77`). The result-to-claim review itself is complete (2026-08-26 receipt) and is not a missing artifact.
5. **Not allowed today.** No activation; no conditioning on a successful bootstrap subset; no extrapolation to other horizons, empirical calibration or broader validity; no manuscript/figure use of any interval value; no promotion.

### 2.3 E4-R008 — isolated duplicate + claim audit (M4)

1. **Current status.** `PASS` with restriction, `refine-logs/EXPERIMENT_TRACKER.md:12` ("derived metric remains artifact-only/descriptive, claim activation and manuscript/figure promotion remain blocked").
2. **What is secured.** Gate verdict `PASS` (`refine-logs/NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.md:6`); primary and duplicate content-addressed roots agree (`:9-12`, content address `c96e620006d55b1459331c3ead28069920962ccf2df1a682030a37f47e97e635`); all seven fidelity checks PASS in the machine-readable receipt (`NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.json`, `$.claim_fidelity_status = PASS`). The gate script fails closed on activation drift: `scripts/experiments/e4_r008_duplicate_claim_fidelity_gate.py:100-101` and `:134-136` require `claim_activation == "BLOCKED"`.
3. **Restrictions / what is explicitly NOT allowed today.** The derived metric (panel log-ratio and cell CI) is artifact-level and descriptive only (`$.claim_fidelity_checks[name="derived_metric_is_artifact_only"]`); `simulation_only` ceiling and RCEP/NYC exclusion retained (`NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.md:15-17`); no manuscript or figure values were written and none may be promoted (`:22-25`); the derived artifact does not activate E4-R006 (see 2.1 item 4).
4. **Required to change status.** Only an E4-R009-level author activation decision plus a sentence-level claim ledger and the full rebuild chain; no analyzer or gate rerun is needed or authorized by itself.
5. **Freeze conditions.** Frozen E4-r3 result unchanged by the gate (`$.frozen_quarantine_modified_by_gate = false`); roots must remain content-addressed and unmodified.

### 2.4 E4-R009 — NCS activation decision (M5)

1. **Current status.** `BLOCKED`, `refine-logs/EXPERIMENT_TRACKER.md:13` ("build 与 promotion 单独保持关闭"); confirmed `REC-STATUS-RECONCILIATION_V2_20260914.md:27`.
2. **Blockers.** The activation decision must rest on audited evidence only, and its only activatable upstream evidence today is E4-R008's descriptive artifact; E4-R006 (2.1) and E4-R007 (2.2) remain closed. Standing invariants (`EXPERIMENT_TRACKER.md:17-20`) and the historical root FAIL (`EXPERIMENT_AUDIT.md:8-20`) remain in force. No activation-decision record exists in `refine-logs/` for E4-R009. The 2026-08-30 author decisions RC-1/RC-2 (`refine-logs/REC-P3_RC1_RC2_ACTIVATION_V1_20260830.md`) activate the RCEP/NYC correction posture only; they do not touch E4 rows.
3. **Required authorizations.** An explicit author activation decision for E4-R009; a sentence-level claim/evidence ledger binding each sentence to exact frozen JSON key paths with the `simulation_only` ceiling retained (`NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md:75-77`); a controlled manuscript-update authorization in the REC-M5 pattern; and the full ordered rebuild chain (`docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md:183-191`).
4. **Missing artifacts.** The claim map / sentence-level ledger; the activation decision record itself.
5. **Not allowed today.** No activation, no promotion, no downstream build triggered by E4 evidence, no audit-status change.

## 3. REC-M2..M5 governance chain (M2 → M3 → M4 → M5)

Dependency order is pre-registered at `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_PLAN.md:127-137` and in the tracker dependency column (`NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:10-13`). M0/M1 are `PASS` (`NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:8-9`, receipts `NCS_POST_ACCEPTANCE_RECOVERY_M0_REFREEZE_RECEIPT_20260804_023813.json`, `NCS_POST_ACCEPTANCE_RECOVERY_M1_RECEIPT_20260804_025115.json`).

### 3.1 REC-M2 — read-only derived rerun (go gate: two runs byte-identical, coverage complete)

- **Blocker history (all locatable).** First preflight BLOCKED on legacy authorization-field incompatibility in all four analyzers (`NCS_POST_ACCEPTANCE_RECOVERY_M2_PREFLIGHT_20260804_031451.md:1-9`, findings `:24-33`); M2A authorization-v2 compatibility repair PASS with `REC-M2 BLOCKED_PENDING_NEW_PREFLIGHT` (`NCS_POST_ACCEPTANCE_RECOVERY_M2A_REPAIR_RECEIPT_V1_20260810_222232.md:35`); M2B preflight PASS with `REC-M2 BLOCKED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE` (`NCS_POST_ACCEPTANCE_RECOVERY_M2B_TRACKER_V1_20260810_231758.md:5, 35`); M2B2 repair/preflight PASS with the same pending condition (`NCS_POST_ACCEPTANCE_RECOVERY_M2B2_TRACKER_V1_20260810_235227.md:3, 47`).
- **Receipt-level state.** `REC-M2C PASS`: four analyzers, primary + duplicate roots, 27/27 path/byte/SHA entries equal, failure/non-finite/unstable/NOT_RUN bins preserved, protected trees unchanged (`NCS_POST_ACCEPTANCE_RECOVERY_M2C_TRACKER_V1_20260811_010147.md:3-17`; `NCS_POST_ACCEPTANCE_RECOVERY_M2C_RECEIPT_V1_20260811_010147.json` `$.final_status = "REC-M2C PASS"`, `$.comparison.all_entries_equal = true`; outputs under `refine-logs/ncs_new_analysis_v2/rec-m2b2-20260810-235227-cst-01/`).
- **Open finding F1 (status reconciliation).** The M2C receipt set evidences the tracker go gate ("两次运行字节一致、coverage 完整", `NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:10`), yet the controlling tracker row and its 2026-08-04 checkpoint were never reconciled (`:41`). Downstream M3/M4 receipts already treat `m2c = PASS` (e.g. `REC-M4_INDEPENDENT_ACCEPTANCE_V4_20260811.json` `$.scientific_state_matrix.*.m2c = PASS`), so the chain moved on while the tracker row stayed `BLOCKED`. Formal closure needs a dated tracker-row reconciliation record — a governance action this read-only task does not perform.
- **What unblocks.** A reconciliation record flipping REC-M2 to the receipt-evidenced state, or a fresh pre-registered rerun under a new authorization if reconciliation is refused.
- **Not allowed today.** No further analyzer rerun without a new versioned preflight + execution authorization; CAL boundaries hold (E01 raw comparator/paired only; E02:128/E02:135 descriptive; E03 N=20/50 only, N=100/200 `NOT_RUN/ABSTAIN`); no reuse of prior prohibited output trees (`NCS_POST_ACCEPTANCE_RECOVERY_M2B_TRACKER_V1_20260810_231758.md:22`).

### 3.2 REC-M3 — V1-026/033/045 text and contract audit (go gate: complete sentence-to-evidence ledger)

- **Status / receipts.** Tracker `BLOCKED` (`NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:11`). Lane receipts: `REC-M3_ACCEPTANCE_V2_20260811.json` `$.acceptance_result = "REC-M3_GOVERNANCE_ACCEPTANCE_PASS"` (114-check fresh root validation; V1 supersedance recorded), patch proposals and claim/contract ledgers exist for V1-026 (incl. R2), V1-033 and V1-045 (incl. R2 2026-08-26) under `refine-logs/REC-M3_*`.
- **What unblocks.** The same tracker-row reconciliation as REC-M2 (F1). Substantively, M3 outputs are proposal-only: `manuscript_patches_applied = false` (`REC-M4_INDEPENDENT_ACCEPTANCE_V4_20260811.json` `$.proposal_only_boundaries`).
- **Not allowed today.** Direct manuscript edits outside an authorized application record; any wording that extends `simulation_only` to broad fairness/generalization (stop rule `NCS_POST_ACCEPTANCE_RECOVERY_PLAN.md:67`).

### 3.3 REC-M4 — independent unified acceptance (go gate: governance PASS, no P0 failure)

- **Status / receipts.** Tracker `BLOCKED` (`NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:12`). Lane history: V1 FAIL retained, V2 invalid pass retained, V3 fail-closed retained, V4 = `REC-M4_INDEPENDENT_ACCEPTANCE_PASS`, class `GOVERNANCE_AND_ARTIFACT_INTEGRITY_ONLY`, deterministic allowlisted validator, 26/26 audit units PASS, `m4_pass_applies_manuscript_patch = false`, `m4_pass_activates_scientific_claim = false`, and `progression_gate["REC-M5"] = NOT_AUTHORIZED_BY_THIS_RECORD` (`refine-logs/REC-M4_INDEPENDENT_ACCEPTANCE_V4_20260811.json`, `$.acceptance_result`, `$.acceptance_class`, `$.audit_units`, `$.progression_gate`).
- **What unblocks.** Any future M4-class acceptance requires a new pre-registered validation scope; M5 execution required (and on 2026-08-26 obtained) an explicit author authorization rather than an M4-derived one.
- **Not allowed today.** Treating the V4 governance/artifact PASS as scientific SUPPORTED or as license to activate claims; the receipt itself forbids both.

### 3.4 REC-M5 — controlled manuscript update (go gate: source-only/release gates pass; MUST AFTER M4 PASS)

- **Status / receipts.** Tracker `BLOCKED` (`NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:13`). Lane state: M5-C CLOSED for patch V2 after scientific V6 (+instrumentation addendum, `PASS*` with disclosed orchestrator instrumentation), editorial V5 PASS and governance V6 PASS lanes, with all 26 units `CANDIDATE_NOT_APPLIED` at closure (`REC-M5_C_CLOSURE_V1_20260826.md:8-14, 39-40`); M5-D then applied groups G01–G10 to seven manuscript sources plus `controlled_benchmark_contract.json` under explicit author authorization (`REC-M5_D_APPLICATION_V1_20260826.md:5-11`), with final gates "BLOCKED solely by the standing RCEP/NYC audit blockade (P3) — both deferred to P3 by design" (`:15`). The P3 chain subsequently executed and the current local build baseline is `REC-P6_POST_DECISION_REBUILD_V1_20260903` (focused suite 8/8; final gate 225 passes / 0 errors; release safety 0 blockers / 0 warnings, per A1 map `REC-STATUS-RECONCILIATION_V2_20260914.md:16`).
- **Residuals.** The formal author-decision register "requires separate M5-F authorization even after M5-D" (`REC-M5_C_CLOSURE_V1_20260826.md:44`); E4-R007 activation remains deferred (`:41`); all four external gate groups remain open (A1 map).
- **What unblocks.** For any further M5-class mutation: a new explicit author authorization with anchor-hash prechecks and fail-closed drift handling (pattern of `REC-M5_D_APPLICATION_V1_20260826.md:5-15`); for register decisions: M5-F authorization; for claim activation: the E4-R009 decision of 2.4.
- **Not allowed today.** Manuscript mutation without authorization; register mutation; claim activation; treating the completed P3 rebuild as closing any external gate.

### 3.5 Chain summary

Receipt-level, the chain M0 → M1 → (M2C) → (M3 V2) → (M4 V4) → (M5-C + M5-D, completed via P3/P6) has advanced substantially beyond the tracker rows, but the only states with standing governance force today are the tracker rows (`REC-M0/M1 PASS`, `REC-M2..M5 BLOCKED`) plus the A1 map. The single highest-leverage unblocking action for the whole REC lane is one dated reconciliation record aligning `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:10-13` with the receipt chain; it changes no scientific claim and executes nothing.

## 4. Cross-cutting invariants (apply to every item above)

1. No experiment or analyzer execution without explicit authorization + pre-registered protocol + frozen inputs (plan boundary `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md:23`; tracker `EXPERIMENT_TRACKER.md:19-20`).
2. No new hashes/SHA content generation outside process-owned metadata (plan boundary `:24`); this audit computed none.
3. The historical `EXPERIMENT_AUDIT` overall FAIL is retained verbatim and must not be rewritten to an overall PASS (A1 map `REC-STATUS-RECONCILIATION_V2_20260914.md:12`).
4. RCEP, NYC, R006e, R006f remain excluded routes for all E4 work (`e4-r3-workspace-author-authorization-20260731.json:14-17`; `NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.md:17`).
5. No claim activation, promotion, or manuscript entry may be derived from this memo; recovery authorizations flow only from the author via dated decision records.

## 5. Open findings

- **F1 — tracker rows stale vs receipt chain.** `NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:10-13` still record REC-M2..M5 `BLOCKED` while the M2C/M3-V2/M4-V4/M5-C+D receipts evidence lane progression (sections 3.1–3.4). Needs a governance reconciliation record; C2 does not modify the tracker.
- **F2 — E4-R006 required artifact does not exist.** No serialized pre-registered panel-level log-error-ratio + CI (with construction method and confidence level) exists in `refine-logs/`; OPT-S1 is `DECISION_PENDING` (`NCS_POST_ACCEPTANCE_RECOVERY_TRACKER.md:14`). This absence is attested by three independent audits (2.1 B3) and is a design-level blocker, not a located-file defect.
- **F3 — C1 predecessor not found.** No C1 (endpoint-aware evidence-boundary) receipt exists in `refine-logs/` as of 2026-09-14; C2 was executed against the A1 map. Recorded as a lineage gap only.
- **F4 — tracker annotation not pinned.** The R006/R007 row annotations "独立 result-to-claim = partial (high/medium confidence)" (`EXPERIMENT_TRACKER.md:10-11`) could not be pinned to a standalone receipt within read scope; the pinned verdicts are `STRUCTURALLY_FORECLOSED_ON_R3_BYTES` (`REC-P2_E4R007_RESULT_TO_CLAIM_V1_20260825.json` `$.out_of_scope["E4-R006"]`), `QUALIFIED_SUPPORTED` / `NOT_ACTIVATED_BY_THIS_RECORD` (`NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.md:269-284`), and integrity `WARN` (`NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md:9`). Recorded as an open finding rather than speculated.
- **F5 — duplicate-named siblings.** `" 2"`-suffixed sibling directories exist under `refine-logs/e3_family2_quarantine/` and `refine-logs/ncs_new_analysis_v2/` (iCloud-style sync copies). Any recovery must bind authoritative roots via the recorded SHA chains (candidate/authorization/inventory hashes), never by directory name. Observation only; no action taken.

## 6. Verification

- Strictly read-only: no experiment, analyzer, executor, protocol, make target, or test was executed; no hash was computed; no existing file was modified; no tracker status changed; no claim activated; no Git operation performed.
- Every blocker above is located to a file path (with line, or jq path for JSON) or to a named protocol/receipt.
- `git diff --check`: run at task end; passed. Working-tree footprint of this task = exactly one new file, `refine-logs/REC-C2_E4_RECOVERY_CONDITIONS_V1_20260914.md`; pre-existing user changes untouched.

*End of recovery-conditions receipt.*
