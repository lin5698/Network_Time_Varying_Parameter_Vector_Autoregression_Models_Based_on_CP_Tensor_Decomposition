# Empirical Implementation Audit — Re-adjudication (P3 Stage-3, Step 1)

Audit date: 2026-08-26

Audit timezone basis: `Asia/Shanghai`

Verdict: **PASS — `rcep_nyc_value_audited_downstream_build_authorized`** (build gate released ONLY; promotion and activation remain unauthorized)

**Summary.** Re-adjudication of the standing FAIL (`rcep_nyc_quarantined_unreviewed`) against the completed 2026-08-26 review chain. Release-condition part 1 is satisfied: both quarantined corrected runs passed independent value audit (RCEP-03 36/36 files, NYC-01 18/18 files, both `SUPPORTED_FOR_DOWNSTREAM_REVIEW`; hash-frozen bytes verified MATCH 36/36 and 18/18 by orchestrator-executed instrumentation with empty drift/missing/extra-on-disk/symlinks), the receipts are internally coherent and cross-consistent, and this adjudicator's own spot-checks reproduced nine load-bearing statements against the underlying artifacts. Part 2 is satisfied: author decision 2026-08-26 (`p3_stage3=授权复审+重建链`) grants separate downstream-build authorization while explicitly excluding quarantine-tree promotion and empirical claim activation. Manuscript-promotion authorization was **not granted** and is recorded as a remaining condition rather than a build-gate blocker, because `PAPER_TO_EVIDENCE_AUDIT_V1_20260826` found zero active stale citations and zero manuscript sentences bound to quarantine candidates. PASS releases only the fail-closed build gate for the authorized rebuild chain; open characterization flags F1/F2/F3 (RCEP) plus NYC characterizations block activation, not build.

*Note on timestamp precision:* UTC wall-clock second-level precision was unmeasurable in this session (spawn tooling failed — see Provenance); only the date is asserted, under the Asia/Shanghai basis.

## Previous artifact

This artifact supersedes `EMPIRICAL_IMPLEMENTATION_AUDIT.json` at
`sha256:29d5656ab2aebc05ebfb424b45eed47849f9394a3a6c811530e0de8f367d527c`
(audit date 2026-07-19, verdict FAIL, reason code `rcep_nyc_quarantined_unreviewed`).

## Readjudication Basis

Release condition adjudicated (verbatim from the superseded artifact): *"Independently audit both corrected quarantine inventories and values, then obtain separate downstream-build and manuscript-promotion authorization."*

### Part 1 — Independent audit of both corrected quarantine inventories and values: **SATISFIED**

**RCEP lane** — `refine-logs/PSA_RCEP_03_VALUE_AUDIT_20260826.{md,json}`, overall `SUPPORTED_FOR_DOWNSTREAM_REVIEW` (amended; V-T1 `PASS_QUALIFIED_INSTRUMENT_MEDIATED`):
36/36 declared quarantine files covered (18 text/data read+parsed, 18 figures existence-verified). Inventory integrity: MATCH 36/36 vs `PSA_RCEP_03_OUTPUT_INVENTORY_20260719.json` via `tmp/rcep_vt1_measurement_20260826.json`; drift/missing/extra-on-disk/symlinks all empty. Per-task: V-T1 PASS (qualified), V-T2 PARTIAL, V-T3 PASS_WITH_FLAGS, V-T4 PASS (characterization only), V-T5 PASS (readiness only).

**NYC lane** — `refine-logs/PSA_NYC_01_VALUE_AUDIT_20260826.{md,json}`, overall `SUPPORTED_FOR_DOWNSTREAM_REVIEW` (revised from initial BLOCKED after instrumentation adjudication):
18/18 declared files found and MATCH under the corrected base `output/natcs_empirical_cp_authorized_runs/psa-20260719-nyc-01/nyc_taxi` via `tmp/nyc_vt1_measurement_20260826.json`. The row-12 transcription incident is CLOSED (zero git changes today; inventory mtime 2026-08-12T13:41:40 predates the session; fresh PNG digest equals the current-authoritative inventory value). Per-task VT1–VT5 all PASS (VT1 qualified).

Both instrumentation files were read in full by this adjudicator: rows enumerate exactly the 36 / 18 declared paths; every row is `MATCH` with `sha256 == exp_sha256`, `size == exp_size`, `is_symlink: false`.

*Qualification (disclosed):* all hash measurements are orchestrator-custody; this adjudicator could not recompute any digest. Accepted as instrument-mediated evidence consistent with both receipts' own qualifications.

### Adjudicator's independent spot-checks (all CONFIRMED)

| ID | Artifact | Load-bearing statement verified |
| --- | --- | --- |
| SC-1 | RCEP quarantine `selection_summary.json` | cp_rank 2; ridge 0.01; rank_losses {0.70804, 0.46326, 13.42220, 13.29576}; full_fit_loss 0.6196736654708991; stability_rate 0.5277777777777778; helper commit echo d0e398b…; F1 remap 2022-12-31→2020-03-31; F2 point 0.0022967865167819556 > p975 0.0020326520698283287; attenuation_difference.point ≡ evolving−frozen exact |
| SC-2 | RCEP quarantine `stability_summary.csv` | 36 dates; first unstable 2020-06-30 then all subsequent → exactly 19 unstable (= rate); min radius 0.4496630475143816, max 1.4489532745859717; unstable ⟺ radius>1 on every row |
| SC-3 | NYC quarantine `stability_summary.csv` | 69 data rows; exactly 48 unstable; 48/69 = 0.6956521739130435 ≡ selection_summary.stability_rate_cp |
| SC-4 | NYC quarantine `selection_summary.json` | cp_rank 4; rank/fit losses verbatim; full_fit_loss 0.13612272962909133; origins 66/69 per rank; window 40/lag 2/boot 500/block 4/inits 6/iter 100/tol 1e-06; helper commit null; GIRF remap {2019-12-31→2020-03-31, 2021-12-31→2020-04-30} |
| SC-5 | NYC quarantine `derived_monthly_panel.csv` | header + exactly 109 monthly rows, 2012-12-31..2021-12-31, strict month-end continuity incl. leap rows; 16 cols = date + the receipt's 15 zone names verbatim |
| SC-6 | Stale `output/natcs_empirical_cp/rcep/selection_summary.json` | cp_rank 1, monotone rank losses; full_fit_loss 1.014484343302525 ≡ governance identifier; ridge grid byte-identical to candidate; no intercept_policy field |
| SC-7 | RCEP quarantine `table_rcep_cp_benchmark.csv` | Evolving coefficient 0.0022967865167819556 ≡ summary point to 16 digits, p = 5.406453063017125e-11; Frozen 0.0015920158589193666; N=7560; trimmed N=7408 (=7560−152) |
| SC-8 | Stale RCEP `table_rcep_cp_benchmark.csv` | stale headline 0.0008732456785415317 at p=0.01395; two-way-clustered p literally 0.0; candidate/stale ratio ≈ 2.63× reproduces |
| SC-9 | `PAPER_CLAIM_AUDIT.json` (read-only) | verdict BLOCKED, reason `rcep_nyc_quarantines_unreviewed`, as asserted by the stage-2 receipt |

No discrepancy was found between today's receipts and underlying bytes on any load-bearing statement tested.

### Part 2 — Separate downstream-build authorization: **SATISFIED**

Author decision 2026-08-26 (`p3_stage3=授权复审+重建链`) authorizes re-adjudication plus the rebuild chain, explicitly excluding quarantine-tree promotion and empirical claim activation. This is the distinct downstream-build authorization the 2026-07-19 release condition required.

### Manuscript-promotion authorization: **NOT GRANTED — remaining condition, not a build-gate blocker**

`PAPER_TO_EVIDENCE_AUDIT_V1_20260826` independently established, and this adjudicator verified key elements of: `stale_citation_retest.answer_today = NO` active citations of stale promoted values; `BOUND_TO_QUARANTINE_CANDIDATE` count bound to any manuscript sentence = 0; per-claim counts 35 OK / 4 STALE_BOUND / 0 CRITICAL, with the four STALE_BOUND items self-fenced ledger pointers (C006/C007/C008), gate-gated latent builder strings (unreachable while PAPER_CLAIM_AUDIT=BLOCKED and this audit previously FAIL), or inert on-disk residue excluded by submission-packaging scans. Because nothing in the current manuscript binds to quarantine or stale values for active use, promotion authorization can remain pending without blocking the authorized rebuild chain.

### Receipts cited (sha256 from today's orchestrator-measured hash pack)

| Receipt | sha256 |
| --- | --- |
| `refine-logs/PSA_RCEP_03_VALUE_AUDIT_20260826.md` | `e74aba57439cc34a692ee50e93a6f4fb2d177cfa5aa0c9271447b5287b266b0e` |
| `refine-logs/PSA_RCEP_03_VALUE_AUDIT_20260826.json` | `9a1dd905ad34624540d523dcd34dd2431e2a4f9ac2bbb87642355871fd499250` |
| `refine-logs/PSA_NYC_01_VALUE_AUDIT_20260826.md` | `3ad9c691eccbe39e7bdf47f7c5a399d1fe17ad141e7d0324ef7c88d240682764` |
| `refine-logs/PSA_NYC_01_VALUE_AUDIT_20260826.json` | `d3cf2b74951cf760dc79b83ff2bb04d5b5f8aec8747c2ed46a70e0f970cfcf56` |
| `refine-logs/PAPER_TO_EVIDENCE_AUDIT_V1_20260826.md` | `085e9bf409b06d29eca3f8261076084ea700a07d7b602ddcb2b85c4297ca1623` |
| `refine-logs/PAPER_TO_EVIDENCE_AUDIT_V1_20260826.json` | `f111daeff0eca254e00db65fddd775bc29b25a610d8bde646c8dfe1493675cfa` |
| `refine-logs/REC-P3_VALUE_AUDIT_WAVE_V1_20260826.md` | `b36dfc0bcd42b3a62844f95532fe7f0867ea44a526556c2cdabe9d964c44a6da` |
| `refine-logs/REC-P3_VALUE_AUDIT_WAVE_V1_20260826.json` | `3fdb6572d6b07cbb0527c22fa9e1c449c5e8fd43474410ce5476c1df0d12aa86` |

Wave record consolidation (`REC-P3_VALUE_AUDIT_WAVE_V1_20260826`): both lanes SUPPORTED_FOR_DOWNSTREAM_REVIEW; activated claims = none; standing blockers recorded as PAPER_CLAIM_AUDIT=BLOCKED and EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL — the second is discharged by this artifact; PAPER_CLAIM_AUDIT discharge belongs to the sequential second lane.

## Flag Dispositions

**Disposition class: `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD`.** Each flag remains OPEN as a characterization issue: it blocks any manuscript use or claim activation of the affected fragment until separately resolved or explicitly accepted by the author; none blocks the downstream rebuild chain authorized on 2026-08-26.

Carried forward verbatim from the wave record: `RCEP_F1_girf_date_substitution_undocumented`, `RCEP_F2_point_outside_bootstrap_CI`, `RCEP_F3_stable_dates_not_identified`, `NYC_stability_rate_semantics`, `NYC_girf_date_remap`, `NYC_origins_66_of_69`, `NYC_negative_late_g_net`, `no_rng_seed_recorded_both_trees`.

Verbatim flag text from the RCEP receipt:

- **F1**: "girf date substitution 2022-12-31->2020-03-31 unexplained in artifacts; BOTH dates present in outputs (girf_cp_point.json literal key + full 500-rep bootstrap blocks for both keys)"
- **F2**: "headline evolving_coefficient point lies OUTSIDE its own bootstrap percentile CI (point 0.00229679 > p975 0.00203265); analytic-SE significance coexists with this"
- **F3**: "stable-dates-only pair-level regression NOT identified under repaired run (TC_relief collinear with pair/time effects; N=3570); honest empty fields in artifact"

NYC characterizations (verbatim from the NYC receipt, observations a–f): stability_rate_cp numerically equals the UNSTABLE share (radius>1 fraction) — semantics/labeling question for pipeline owners; requested GIRF month-ends remapped to COVID-onset months although they exist in-panel, rule undocumented, stale tree honored requests identically; evaluated origins uniformly 66 < 69 available across ranks in BOTH trees; late-period g_net point estimates negative (baseline_mobility −0.376..−0.696 for 2021-05..2021-12; baseline_h12 to −4.353 at 2021-06), finite and internally echoed by bootstrap medians near/below 0; half_life pinned at cap H (=8/12) through 2020-05..2021-04 in all variants; bootstrap means differ materially from full-sample points in several months — skew, internally consistent. Plus: no RNG seed recorded in any output artifact of either tree.

Binding effect: all quarantine-candidate mappings remain POTENTIAL_ONLY_NOT_ACTIVATED; RCEP F1/F2/F3 and NYC flags block any future activation of the fragments they touch.

## Remaining Conditions

1. **RC-1 — Manuscript-promotion authorization: NOT GRANTED** (owner: author). Required before any quarantined-run value, figure, or claim fragment may enter manuscript promotion. Not a blocker to the authorized downstream build gate because zero active manuscript citations bind to quarantine or stale values.
2. **RC-2 — Empirical claim activation requires separate authorization**, blocked by the open characterization flags above; all mappings stay POTENTIAL_ONLY_NOT_ACTIVATED.
3. **RC-3 — Post-regeneration review with no open FATAL/CRITICAL issue** (carried from original condition clause 3). Rebuilt manuscript/reviewer archive/submission package/upload-freeze manifest remain subject to standing fail-closed gates (e.g., the evidence build release gate currently refusing while PAPER_CLAIM_AUDIT=BLOCKED).

## Historical Context (2026-07-19, unmodified)

The full scientific-execution closure record, blocking findings EIA-001..003 (all implementation issues since fixed, outputs then quarantined-unreviewed), resolved controls EIA-004..006, helper candidate preflight (C3 selected; manifest sha256 02b15147…; permitted claim limited to static identity + import closure), NYC source preflight (commit 7e63ba97…), test suites (85 + 145 passing), security review rounds 3–5, and the original release condition are preserved verbatim under `historical_context_2026_07_19_unmodified` in the JSON twin of this artifact, pinned by `previous_artifact_sha256`. They are historical context only and do not describe the current verdict; statements such as "unreviewed" describe the state before the 2026-08-26 value-audit wave.

## Audited Input Hashes (fresh subset)

**Custody disclosure:** ALL digests below were measured by the **orchestrator** (full tooling) and recorded in `tmp/p3_readjud_hash_pack_20260826.json`; this adjudicator has no spawn capability and could not recompute any digest. Disclosed reliance, not first-party verification.

- `EMPIRICAL_IMPLEMENTATION_AUDIT.md` — `sha256:ab2ad0de9f752c0d1457ff4176d97e37aec969c6a07126878167b3c4a09c09df`
- `EMPIRICAL_IMPLEMENTATION_AUDIT.json` (previous) — `sha256:29d5656ab2aebc05ebfb424b45eed47849f9394a3a6c811530e0de8f367d527c`
- `PAPER_CLAIM_AUDIT.md` — `sha256:800c0b68a84066d2ca2d71de7ae7c4602445814e07a11b3069e37e672bfe8cae`
- `PAPER_CLAIM_AUDIT.json` — `sha256:3fe91793793a0b7bb9a6acc6b53793b735c5c5eb3667c27f7b59b7d92ff41d92`
- `refine-logs/PSA_RCEP_03_VALUE_AUDIT_20260826.{md,json}` — `sha256:e74aba57…266b0e`, `sha256:9a1dd905…499250`
- `refine-logs/PSA_NYC_01_VALUE_AUDIT_20260826.{md,json}` — `sha256:3ad9c691…682764`, `sha256:d3cf2b74…cfcf56`
- `refine-logs/PAPER_TO_EVIDENCE_AUDIT_V1_20260826.{md,json}` — `sha256:085e9bf4…ca1623`, `sha256:f111daef…675cfa`
- `refine-logs/REC-P3_VALUE_AUDIT_WAVE_V1_20260826.{md,json}` — `sha256:b36dfc0b…44a6da`, `sha256:3fdb6572…12aa86`
- `refine-logs/PSA_RCEP_03_OUTPUT_INVENTORY_20260719.json` — `sha256:1645eb66…53748ee9`
- `refine-logs/PSA_NYC_OUTPUT_INVENTORY_20260719.json` — `sha256:f7c0e7cd…90e9e588`
- `output/natcs_empirical_cp/rcep/selection_summary.json` (stale) — `sha256:bacaa2ac…d1b6b4920`
- `output/natcs_empirical_cp/nyc_taxi/selection_summary.json` (stale) — `sha256:d204627f…13882f751f`
- `manuscript_src/natcs/claim_evidence_ledger.csv` — `sha256:e360b18a…5770a115`

(Full 64-hex digests for every entry are recorded in the JSON twin; abbreviated forms above are display-only.)

## Provenance Disclosure

- Adjudicator model: **ox-alpha**, developing organization undisclosed; self-adjudicated within mandate, fail-closed rules; no subagents.
- Sole writes: `EMPIRICAL_IMPLEMENTATION_AUDIT.json` and `EMPIRICAL_IMPLEMENTATION_AUDIT.md`. `PAPER_CLAIM_AUDIT.*` untouched (read-only; owned by the sequential second lane). No make/test/git/scientific execution.
- Tooling: bash spawn ENOENT on initial call AND the mandated single retry (no shell all session); glob and grep failed ripgrep launch repeatedly; all evidence gathered via direct file reads. UTC second-level wall-clock precision therefore unmeasurable (`generated_at` carries date-level precision only).
- Hash custody: every sha256 herein originates from the orchestrator-measured pack `tmp/p3_readjud_hash_pack_20260826.json` (orchestrator-executed instrumentation custody, mirroring the V-T1 remediation pattern disclosed in both value-audit receipts). The adjudicator verified internal coherence of the measurement files and reproduced content statements by direct reads; NO first-party cryptographic reproduction was performed.
- Ceiling: `self_supervised_proxy`. Out of scope and confirmed not done: quarantine-tree promotion, empirical claim activation. Nothing was activated.

## Release Condition (current)

PASS releases **only** the fail-closed downstream build gate for the rebuild chain authorized by `p3_stage3` (2026-08-26). It does **not** authorize manuscript promotion or empirical claim activation. Manuscript promotion additionally requires: (1) separate author authorization; (2) resolution or explicit author acceptance of every OPEN characterization flag (RCEP F1/F2/F3, NYC characterizations) for any fragment it touches; (3) post-regeneration independent review reporting no open FATAL or CRITICAL issue. `PAPER_CLAIM_AUDIT` remains BLOCKED; its discharge is owned by the sequential second lane.

Until those conditions are met, no artifact of this workspace is **submission-ready**, and no quarantined value may be cited as evidence in any manuscript text.
