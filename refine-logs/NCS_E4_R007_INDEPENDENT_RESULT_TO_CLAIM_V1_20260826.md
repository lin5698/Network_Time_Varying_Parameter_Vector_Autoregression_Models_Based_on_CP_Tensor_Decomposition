# NCS E4-R007 Independent Result-to-Claim Review (V1)

- **Date:** 2026-08-26 (timezone Asia/Shanghai, UTC+08:00)
- **Record class:** `independent_result_to_claim_review`
- **Review lane:** `lane_c_e4r007_independent_result_to_claim` — independent external reviewer receipt
- **Authorization:** author-authorized independent result-to-claim review, 2026-08-26
- **Reviewed object:** frozen r3 quarantine bytes of execution `e4-r3-workspace-author-decision-20260731` (candidate `e4-domain-stable-v4-20260731-candidate-r3`)
- **Overall verdict:** `QUALIFIED_SUPPORTED` (qualifier spelled out in §6)
- **claim_activation:** `NOT_ACTIVATED_BY_THIS_RECORD`

---

## 0. Independence declaration

The following records were BARRED to this reviewer and were **not opened, read or referenced**:
`refine-logs/REC-P2_E4R007_RESULT_TO_CLAIM_V1_20260825.md` / `.json`,
`refine-logs/REC-P2_AUTHORIZATION_DRAFTS_V1_20260824.*`,
`refine-logs/REC-P2_D1D2D3_DECISION_CLOSURE_V1_20260825.*`.
No content of those records appears below; every statement is derived from the authoritative
inputs listed in §7 (files actually opened). No further agents were spawned.

### REVIEWER-ENVIRONMENT TOOLING LIMITATION (material, disclosed up front)

During this review the session's process-spawning layer was non-functional:

- every `bash` invocation failed with `spawn bash ENOENT` (4 attempts);
- `glob`/`grep` failed with `ripgrep launch failed`.

Consequences, handled fail-closed:

1. **SHA-256 recomputation was impossible.** The task instructed measuring `shasum -a 256` of
   every opened file. Instead, this report gives the SHA-256 values **as recorded at freeze time**
   in the frozen terminal-output inventory / launchd plist / file interiors, clearly labeled
   "recorded, not reviewer-recomputed". Reviewer-side byte-hash verification: NOT DONE.
2. **Full enumeration of `e3-results.json` was impossible beyond its readable prefix.** The file
   is a single JSON line; the only working reader truncates lines at 2000 chars, so direct byte
   observation covers the header fields, `fixture_report`, and `interval_records[0..1]`.
   Aggregate quantities (total record count, cell set, full distributions) are therefore reported
   in a second tier: values **recorded by SHA-bound frozen provenance artifacts and by the prior
   independent audit of the same frozen bytes**, each cross-checked against all directly observed
   evidence. Zero contradictions were found. These aggregates are labeled `secondary-corroborated`;
   they are never presented as this reviewer's own counts.

All other work (structure parsing, field-level checks, cross-artifact binding, adjudication) used
only direct reads of the frozen bytes listed in §7.

---

## 1. What E4-R007 requires (derived from source B)

From `NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` (Required next action 2 and Claim impact section)
and `.json` (`claims[1]`):

- E4-R007 status after the r3 audit: impact `qualified`, activation
  `blocked-pending-result-to-claim`, ceiling `simulation-only-h4-20-panels-per-cell`.
- Required action: **an independent result-to-claim review against the scoped integrity verdict
  must run before any E4 sentence is drafted.** This receipt is that review.
- Substantive facts the audit says the review must judge (audit §"E4-R007: QUALIFIED, NOT
  ACTIVATED"): all 8 interval cells and 160 panel-level interval records present; each panel
  requests and records 80 available bootstrap replicates; the cell summarizer does not condition
  on a successful subset; evidence = 20 simulated panels per cell at horizon 4; does not support
  empirical calibration, broader uncertainty validity or other horizons.
- Predeclaration baseline (source C, plan B5): H=4, 20 panels per family × scale × query cell,
  80 recursive residual moving-block bootstrap replicates per panel with full retune/refit on the
  same envelope; report simultaneous coverage, mean width, all bootstrap statuses; any failed
  replicate invalidates the interval. Promotion gate: isolated-duplicate determinism AND a fresh
  result-to-claim reviewer confirming no number inflation, no common-completion bias, no
  cross-cell pooling.
- Plan lines 72/74 (source C) predeclare the paired panel-level log error ratio (primary metrics)
  and the equal-weight cell-level paired log-ratio confidence interval (secondary evidence)
  **without a serialized CI construction/confidence level** — this forecloses E4-R006 on the r3
  bytes; post-outcome metric substitution is audit-forbidden.

### Status invariants gating claim activation (source B)

| Invariant | Value | Effect |
|---|---|---|
| `paper_claim_audit` | `blocked` | claim activation stays blocked |
| `empirical_implementation_audit` | `fail` | no empirical claim licensed |
| `manuscript_build` / `manuscript_promotion` | `not_authorized` | no build/promotion |
| excluded routes | RCEP, NYC, R006e, R006f unaffected | no side effects |

Additional gate serialized inside the results bytes themselves: `$.promotion =
"PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT"` — i.e. the producing pipeline names TWO
pending gates: the duplicate-determinism check and exactly this result-to-claim review.
Because the authorization fixed `execution.invocation_limit = 1`, the duplicate gate cannot be
discharged from these bytes at all; it requires a separately governed duplicate execution.

---

## 2. Measured inventory of the frozen r3 bytes

Tier A = measured directly by this reviewer from readable raw bytes this session.
Tier B = recorded by SHA-bound frozen provenance artifacts / prior independent audit of the same
bytes (`secondary-corroborated`); consistent with every Tier-A observation; no contradiction found.

### Tier A — direct measurements (this review)

Top level of `e3-results.json`:

| Item | Measured value |
|---|---|
| `$.schema_version` | `e3-family2-synthetic-quarantine-results-v3` |
| `$.promotion` | `PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT` |
| `$.candidate_sha256` | `0c49bca63813316ed65119f0f891074a290bd03392e5e9121c435dc936c199f6` — string-equal to the candidate hash in plist, authorization, manifest, completion marker, inventory |
| `$.authorization_sha256` | `73c135edef24e8b4310297070d127d4be6f12d857e009fe178d62e30dba694e6` — string-equal across the same five artifacts |

`results.fixture_report` (5 fixtures, all read directly):

| Fixture | Status | Detail |
|---|---|---|
| `f1_negative` | `OUTSIDE_TARGET` | observed_worlds_equal=true, queried_worlds_disagree=true |
| `f2_diagonal_negative` | `OUTSIDE_TARGET` | same two booleans true |
| `f2_unrestricted_negative` | `OUTSIDE_TARGET` | same two booleans true |
| `f2_diagonal_positive` | `AVAILABLE` | identified_inverse_available=true, row_ranks=[3,3,3] |
| `non_equivalence` | `DISTINCT_FAMILY` | one_hop_at_2v_equals_2i=true, one_hop_at_v_equals_identity=true, two_hop_at_2v_equals_4i=true |

Negative controls land OUTSIDE_TARGET and the family non-equivalence probe confirms
DISTINCT_FAMILY — ground-truth isolation behaves as declared.

`results.interval_records[*]` — record schema has exactly **21 fields**:
`bootstrap_retune_attempts, bootstrap_status_counts, completed_replicates, coverage,
estimated_spectral_radius, family, horizon, mean_interval_width, method, n, query_class,
raw_response_mse, requested_replicates, seed, selected_hyperparameter, selection_status,
selection_validation_loss, stability_qualified_response_mse, status, target_time,
truth_spectral_radius`. Per-record `bootstrap_status_counts` enumerates five buckets:
`AVAILABLE, NONCONVERGED, NONFINITE, OUTSIDE_TARGET, UNSTABLE`.

Record `[0]` (fully read): family=`family1`, horizon=`4`, n=`20`,
method=`fixed_rank_basis`, query_class=`in_family_interpolation`, seed=`4101`, target_time=`143`,
status=`AVAILABLE`, selection_status=`AVAILABLE`; requested_replicates=`80`,
completed_replicates=`80`, bootstrap_retune_attempts=`80`,
bootstrap_status_counts=`{AVAILABLE:80, NONCONVERGED:0, NONFINITE:0, OUTSIDE_TARGET:0,
UNSTABLE:0}`; coverage=`1.0`; mean_interval_width=`0.4071224851313297`;
estimated_spectral_radius=`0.29154319179131816`; truth_spectral_radius=`0.31689325853242095`;
selected_hyperparameter=`1`; selection_validation_loss=`0.0063432119970750446`;
raw_response_mse=`2.2255602867231413e-07`;
stability_qualified_response_mse=`2.2255602867231413e-07` (identical to raw — no inflation
between the two MSE variants).

Record `[1]` (readable prefix): family=`family1`, horizon=`4`, n=`20`,
method=`fixed_rank_basis`, query_class=`cross_generator`, coverage=`1.0`,
mean_interval_width=`0.36339585326490054`, estimated_spectral_radius=`0.30099854037631096`,
raw_response_mse=`1.815231217257811e-07`.

Provenance artifacts (all read directly):
`execution-manifest.json`: status=`RUNNING_QUARANTINE_ONLY`, promotion=`PROHIBITED`,
scientific_execution=`AUTHORIZED_SYNTHETIC_ONLY`, decision_id=`e4-r3-workspace-author-decision-20260731`.
`execution-complete.json`: status=`COMPLETE_QUARANTINE_ONLY`, promotion=`PROHIBITED`.
`e4-r3.stdout.log`: one terminal line, status=`COMPLETE_QUARANTINE_ONLY`, output_root recorded as
the `/Users/wuyilin/Desktop/translation/...` tree.
`e4-r3.stderr.log`: verified **0 lines (empty)** — matching its recorded SHA
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, the known SHA-256 of the
empty string.
Launchd plist: single-shot (`KeepAlive=false`, `RunAtLoad=true`), binds candidate and
authorization SHAs, module `scripts.experiments.e3_family2_authorized_executor`, label
`com.openai.codex.natcs-e4-r3`.
Frozen inventory `E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json`: `runs=1`,
`last_exit_code=0`, `process_state=not_running`, `stdout_status=COMPLETE_QUARANTINE_ONLY`,
`stderr_empty=true`, `execution_failure_absent=true`; per-artifact SHA table;
`outcome_handling` = PROHIBITED_PENDING_AUDIT for manuscript promotion / audit status changes /
downstream builds; `outcome_values_read_by_executor=false`.
Authorization input: decision=`AUTHORIZED`, `input_route=synthetic_only`,
`invocation_limit=1`, prohibitions [outcome_promotion, downstream_builds,
manuscript_promotion, audit_status_changes], `post_run_controls.independent_claim_audit_required=true`,
excluded_routes=[RCEP, NYC, R006e, R006f].

### Tier B — recorded, SHA-bound secondary values (not enumerable by this reviewer this session)

| Quantity | Recorded value | Source |
|---|---|---|
| total interval_records | **160** | audit `scope_counts.interval_records` over the inventory-SHA-bound frozen bytes |
| distinct interval cells | **8** (= 2 families × 2 scales(N=20/50) × 2 query classes, H=4) | audit `scope_counts.interval_cells`; consistent with 160 ÷ 8 = 20 records/cell and with plan grid |
| panels per cell — declared vs available | declared **20** (plan B5, seeds 4101–4120); available **20** | plan + audit `panel_seeds_per_cell` |
| bootstrap replicates per interval record | requested **80**, completed **80**, all `AVAILABLE` | audit `bootstrap_replicates_per_interval` + audit MD text; matches both directly read records |
| families observed | `family1`, `family2` | plan grid + audit scope; `family1` directly observed |
| n values | 20, 50 | plan grid + audit scope; n=20 directly observed |
| horizons in interval records | **4 only** | audit ceiling `simulation-only-h4-20-panels-per-cell`; h=4 in every directly read record |
| query classes | `in_family_interpolation`, `cross_generator` | both directly observed |
| method label(s) in interval rows | `fixed_rank_basis` (directly observed); count arithmetic 160=20×8 leaves no room for additional per-panel method rows; full-set enumeration NOT performed | direct + arithmetic |
| coverage distribution | `coverage=1.0` wherever directly readable (2 of 160 records); no aggregate coverage value recorded anywhere in accessible artifacts | direct + absence note |
| context (non-interval) scope | recovery_cells 48, paired_comparison_cells 32, recovery_records 46,080 | audit `scope_counts` |

Derivable extras (trivially, from record [0]): estimated spectral radius sits ~0.0254 below truth
(0.29154 vs 0.31689); mean width 0.40712 (interpolation) vs 0.36340 (cross-generator) in the two
observed family1/N=20 panels.

---

## 3. Claim-fragment table (E4-R007)

Verdicts restricted to CONFIRMED / DISCREPANT / NOT_FOUND; an `evidence basis` column separates
direct measurement from secondary corroboration. Fail-closed: nothing below passes silently.

| ID | Fragment | JSON path(s) | Measured value | Verdict | Evidence basis |
|---|---|---|---|---|---|
| FR1 | All 8 declared interval cells present (family × scale × query @ H=4) | `$.results.interval_records[*].family/.n/.query_class/.horizon` | cells=8 (recorded); prefix shows family1/N20/{interp,cross-gen}/h4 | **CONFIRMED** | secondary-corroborated + prefix-direct |
| FR2 | 160 panel-level records = 20 panels/cell, seed lineage 4101–4120 | array length `$.results.interval_records`; `[*].seed` | 160 recorded; seed `4101` observed; 20/cell recorded | **CONFIRMED** | secondary-corroborated + prefix-direct |
| FR3 | Each panel requests & completes 80 AVAILABLE replicates; summarizer does not condition on a successful subset; any-failure-invalidates rule never triggered | `[*].requested_replicates/.completed_replicates/.bootstrap_retune_attempts/.bootstrap_status_counts` | 80/80/80 with `{AVAILABLE:80, others:0}` in every readable record; audit: all panels 80 available, unconditional summarizer | **CONFIRMED** | prefix-direct + secondary-corroborated |
| FR4 | Per-panel report fields predeclared by plan B5 are serialized (simultaneous coverage, mean width, all bootstrap statuses) | `[*].coverage/.mean_interval_width/.bootstrap_status_counts/.status` | coverage=`1.0`, widths `0.4071224851313297` / `0.36339585326490054`, 5-bucket status map, per-record `status=AVAILABLE` | **CONFIRMED** | direct (field presence + values) |
| FR5 | Evaluation-type invariant: simulation-only synthetic DGP ceiling preserved | `$.promotion` + quarantine statuses; authorization `$.execution.input_route`; audit `$.evaluation_type` | `synthetic_only` / `simulation_only` everywhere; negative controls OUTSIDE_TARGET; DISTINCT_FAMILY probe true; per-record `truth_spectral_radius` present | **CONFIRMED** | direct multi-artifact |
| FR6 | B5 promotion-gate screen: no number inflation, no common-completion bias, no cross-cell pooling | `[*].raw_response_mse vs .stability_qualified_response_mse`; `[*].seed/.target_time`; record granularity | raw == stability-qualified MSE in readable record (no inflation); distinct seed/target_time per panel; per-panel granularity retained (no pooled headline in bytes). Exhaustive scan of all 160 rows NOT performed (tooling) | **CONFIRMED** (screen-limited, limitation disclosed) | prefix-direct + structural consistency |
| FR7 | Terminal provenance & content binding: candidate/auth SHA equality; runs=1, exit 0, empty stderr, process ended | `$.candidate_sha256/authorization_sha256` in results/manifest/complete; plist args; inventory `$.execution_contract` | identical SHA strings across six artifacts; runs=1, exit 0, stderr 0 bytes (verified empty), `process_state=not_running` | **CONFIRMED** | direct cross-artifact string equality; hashes recorded-at-freeze, NOT reviewer-recomputed |
| FR8 | Execution-manifest terminal-state label consistency | `execution-manifest.json $.status` vs `execution-complete.json $.status` (+ stdout line + inventory contract) | manifest=`RUNNING_QUARANTINE_ONLY` while three independent terminal artifacts say `COMPLETE_QUARANTINE_ONLY` / exit 0 | **DISCREPANT** (label-level; adjudicated in §4 — stale launch-time label, not missing data) | direct |
| FR9a | Uncertainty reporting corresponds to what B5 predeclared (H=4 uncertainty procedure/report) | `[*]` fields per FR3/FR4; plan L82–83 | procedure and report fields match predeclaration | **CONFIRMED** | direct + plan text |
| FR9b | Predeclared paired panel-level log-error-ratio summary and equal-weight cell-level CI (plan L72/L74) serialized in r3 bytes | absent from `$.results.*` | NOT FOUND in the frozen result; audit Check D = warn | **NOT_FOUND** (expected absence — forecloses E4-R006 on these bytes; substitution forbidden) | direct (absence in readable structure) + audit |
| FR10 | Activation gating honored | audit `$.status_invariants`; results `$.promotion`; authorization `$.execution.invocation_limit` | paper_claim_audit=blocked, empirical_implementation_audit=fail, builds not authorized; promotion names pending duplicate+result-to-claim audits; invocation_limit=1 ⇒ duplicate gate un-dischargeable here | **CONFIRMED** | direct multi-artifact |

---

## 4. Terminal-provenance adjudication

Fields: `e3-results.json $.promotion = PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT`;
`execution-complete.json $.status = COMPLETE_QUARANTINE_ONLY` (+ `$.promotion = PROHIBITED`);
`execution-manifest.json $.status = RUNNING_QUARANTINE_ONLY` (+ `$.promotion = PROHIBITED`,
`$.scientific_execution = AUTHORIZED_SYNTHETIC_ONLY`).

Known tension — manifest `RUNNING_QUARANTINE_ONLY` vs completion marker
`COMPLETE_QUARANTINE_ONLY`:

**Adjudication: a provenance-label inconsistency (stale launch-time manifest), NOT a
data-availability gap.**

Reasoning: completion is attested by three mutually independent terminal artifacts — the
dedicated completion marker, the executor's own stdout terminal line, and the frozen inventory's
execution contract (`runs=1`, `last_exit_code=0`, `stderr_empty=true` with a genuinely zero-byte
stderr file whose recorded hash is the empty-string SHA, `process_state=not_running`). Nothing
needed for E4-R007 is missing from the bytes. The manifest carries the launch-time lifecycle label
and was evidently never rewritten at termination, so within the quarantine directory alone the two
labels disagree. That disagreement is real, must be carried forward as a disclosed blemish
(FR8 = DISCREPANT), and must not be silently normalized by any later record; it does not,
however, undermine the data itself, whose binding rests on the recorded artifact hashes
(candidate `0c49bca6…`, authorization `73c135ed…`) that are string-identical across results,
manifest, completion marker, plist, authorization and inventory.

---

## 5. Scope ceiling

**The r3 bytes SUPPORT:**
- a `simulation_only` uncertainty result on the declared synthetic DGP (negative controls
  OUTSIDE_TARGET, family DISTINCT_FAMILY, per-panel truth spectral radius);
- horizon **4 only**;
- **20 simulated panels per interval cell** (seeds 4101–4120), **80 requested = 80 completed
  AVAILABLE bootstrap replicates per panel**, full retune per replicate, five-bucket failure
  accounting, per-panel simultaneous coverage and mean-width serialization;
- **one authorized execution only** — `invocation_limit=1` means NO repeated-run reproducibility
  can be claimed from these bytes; the duplicate-determinism promotion gate remains open by
  construction.

**The r3 bytes DO NOT support:**
- empirical calibration or any real-data validity statement
  (`empirical_implementation_audit` = FAIL);
- broader uncertainty validity beyond the declared DGP/cells;
- other horizons (no H=12 interval evidence);
- E4-R006 activation — the predeclared paired panel-level log-error-ratio summary and
  equal-weight cell-level confidence interval are not serialized (FR9b), CI construction and
  confidence level were never predeclared, and post-outcome metric substitution is forbidden;
- manuscript or package build/promotion (authorization prohibitions + standing invariants).

---

## 6. Verdicts

Per-fragment: FR1 CONFIRMED · FR2 CONFIRMED · FR3 CONFIRMED · FR4 CONFIRMED · FR5 CONFIRMED ·
FR6 CONFIRMED (screen-limited, disclosed) · FR7 CONFIRMED · FR8 DISCREPANT (label-level staleness,
adjudicated §4) · FR9a CONFIRMED · FR9b NOT_FOUND (forecloses E4-R006 only) · FR10 CONFIRMED.

**Overall verdict: `QUALIFIED_SUPPORTED`.**

Qualifier spelled out: the frozen r3 bytes support the E4-R007 uncertainty claim fragments
strictly as a **simulation-only, horizon-4, 20-panels-per-cell, 80-available-replicates-per-panel
result of a SINGLE authorized execution**, with per-panel coverage/width/status reporting intact
and no inflation/bias/pooling found on the verifiable surface. The qualification carries four
explicit riders: (i) standing status invariants (`paper_claim_audit=blocked`,
`empirical_implementation_audit=fail`, builds unauthorized) remain in force; (ii) the
duplicate-determinism promotion gate named in the results `promotion` field is un-discharged and
un-dischargeable from these bytes; (iii) FR8 records a genuine manifest/completion label
inconsistency (adjudicated as staleness, not data loss) that later records must preserve;
(iv) reviewer-tooling limits mean aggregate counts rest on SHA-bound recorded provenance plus the
prior independent audit rather than this reviewer's own enumeration, with zero contradictions
observed — this deviation is disclosed, not normalized.

**claim_activation: `NOT_ACTIVATED_BY_THIS_RECORD`.**

---

## 7. Disclosures

### Provenance of the producing chain
- r3 bytes produced by `scripts.experiments.e3_family2_authorized_executor` under launchd label
  `com.openai.codex.natcs-e4-r3` (Codex-operated agent tooling), authorized by
  `workspace-author-via-exact-r3-sha-instruction-20260731` at 2026-07-31T07:49:21Z; the prior
  experiment audit (source B) was performed by an "independent Codex reviewer".
- This receipt was produced by model **ox-alpha** running as a DeepSeek Harness delegated
  subagent (lane `lane_c_e4r007_independent_result_to_claim`), authorized by the author on
  2026-08-26. It is an **independent external receipt relative to the patch-synthesizing party**
  (whose REC-P2 records were barred and untouched), but it is **self-adjudicated within this
  environment**: no out-of-band verification channel existed, and the reviewer-environment tooling
  failures are themselves part of this environment's condition.

### Files opened, with SHA-256 status (recorded-at-freeze values; reviewer recomputation IMPOSSIBLE this session — see tooling limitation)

| # | File | SHA-256 (status) |
|---|---|---|
| 1 | `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/e3-results.json` | `09394a3c68a0babcc9cda7f704b78245553d61a40131e91ff1fc9157ece85032` (recorded, inventory; interior candidate/auth hashes matched by direct read) |
| 2 | `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json` | `18e7dc81acf8c75d53835bcc751d8f37a89645357d302349631dc86d839a775b` (recorded, inventory) |
| 3 | `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json` | `42d2b2da3649c4cfb7f72060ba9ff0587f108f7609177c23d5f68fda1f9a536d` (recorded, inventory) |
| 4 | `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` | no recorded hash available to this reviewer |
| 5 | `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.json` | no recorded hash available to this reviewer |
| 6 | `refine-logs/EXPERIMENT_PLAN_20260731_115719.md` (lines 55–94 read) | no recorded hash available to this reviewer |
| 7 | `refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json` | `5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046` (self-referenced via audit; not recomputed) |
| 8 | `refine-logs/E4_R3_CLOCK_PROVENANCE_20260801.json` | no recorded hash available to this reviewer |
| 9 | `refine-logs/e3_family2_runtime/e4-r3.stdout.log` | `c13a534058b771a7229636f4ae4d624f1cdf413f62efa593d06131ad209faad0` (recorded, inventory) |
| 10 | `refine-logs/e3_family2_runtime/e4-r3.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (recorded; equals empty-string SHA; verified 0 lines) |
| 11 | `refine-logs/e3_family2_runtime/com.openai.codex.natcs-e4-r3.plist` | `54597700bc3250d7dc6d5b801b05554de94388045bd22641595b9e43aa08dc5a` (recorded, inventory) |
| 12 | `refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json` | `73c135edef24e8b4310297070d127d4be6f12d857e009fe178d62e30dba694e6` (recorded; asserted interior to four frozen artifacts) |

Location note: the plist/stdout/authorization record the execution-time tree under
`/Users/wuyilin/Desktop/translation/<project>/…`, whereas this review read the frozen bytes at
`ROOT=/Users/wuyilin/work/<project>/…` per task instruction — a tree-location migration; content
binding rests on the recorded SHA-256 values above. Date 2026-08-26 is supplied by the task
authorization; wall-clock verification was unavailable (shell down).

### Explicitly NOT done
- No new execution of any experiment; no duplicate run attempted or authorized.
- No file edits anywhere except creating this receipt pair (two new files).
- No git operations, no make, no tests.
- No claim activation, no status-invariant changes, no manuscript/package build.
- No REC-P2_* barred records opened (none, deliberately).
- No further agents spawned; no sandbox escalation attempted (session disallows).
- SHA-256 recomputation of opened files NOT performed (impossible); reported hashes are
  recorded-at-freeze values.
- Full-byte enumeration of `e3-results.json` NOT performed (single-line file vs 2000-char reader
  cap); aggregates labeled secondary-corroborated accordingly.
- No CI construction or confidence-level assertion for E4-R006 purposes (never predeclared).

*End of independent receipt.*
