# P3 VALUE AUDIT RECEIPT — psa-20260719-rcep-03 (quarantined RCEP CP run)

- record_class: `p3_value_audit_receipt`
- audit_date: 2026-08-26 (Asia/Shanghai)
- auditor_model: ox-alpha (undisclosed organization); self-adjudicated independent read-only value auditor
- run_under_audit: `psa-20260719-rcep-03` (post-rank-deficiency-repair RCEP; quarantined 2026-07-19; value_review_performed was false)
- ceiling: `self_supervised_proxy` — no external ground truth exists or is claimed
- authority: this audit ACTIVATES nothing; every downstream-useful mapping below is POTENTIAL_ONLY_NOT_ACTIVATED
- status: **FINAL — AMENDED 2026-08-26 (V-T1 re-opened; see §2A Instrumentation Addendum; F1/F2/F3 attached unchanged)**

## 0. ENVIRONMENT / TOOLING DISCLOSURE (fail-closed)

- `bash` tool: FAILED (`spawn bash ENOENT`) initial call AND mandated single retry → NO SHELL ALL SESSION.
- `glob` tool: FAILED (`ripgrep launch failed`) initial + single retry → unavailable.
- `grep` tool: FAILED (`ripgrep launch failed`) → unavailable.
- Working fs tools this session: `read`, `write` (receipts only), `edit`.
- CONSEQUENCE (fail-closed): SHA-256 recomputation of the 36 files is **UNMEASURED**; byte-size stat is **UNMEASURED**; symlink lstat is **UNMEASURED**; exact directory enumeration (to detect EXTRA unlisted files) is **UNMEASURED**. Nothing below assumes a hash match; integrity findings are existence+content-level only. → The four hash/size/symlink/enumeration dimensions were later covered by ORCHESTRATOR-EXECUTED instrumentation; adjudicated in §2A. bash remained dead (`spawn bash ENOENT`, probe + one retry) at addendum time, so first-party hashing stayed impossible.
- Path-prefix note: task ROOT `/Users/wuyilin/work/Network_…Decomposition`; session cwd `/Users/wuyilin/Desktop/translation/Network_…Decomposition`; inventory's own `output_root` cites the Desktop prefix. All reads here used the work prefix and SUCCEEDED; equivalence of prefixes unproven without lstat (**UNMEASURED**).
- Writes limited to exactly this .md and its .json sibling. No make/tests/scientific/git writes/subagents used.

## 1. INPUTS

- A. Quarantine outputs: `output/natcs_empirical_cp_authorized_runs/psa-20260719-rcep-03/rcep/` (36 declared files: 18 data + 18 figures)
- B. Inventory: `refine-logs/PSA_RCEP_03_OUTPUT_INVENTORY_20260719.json` — schema_version 1; decision_id psa-20260719-rcep-03; dataset rcep; status `completed_quarantined_unreviewed`; file_count 36; symlink_count 0; value_review_performed false; output_root cites `<Desktop prefix>/output/natcs_empirical_cp_authorized_runs/psa-20260719-rcep-03/rcep`
- B'. Sidecar found as `PSA_RCEP_03_OUTPUT_INVENTORY_20260719.sha256` (NOT `.json.sha256` as tasked): content `1645eb66267acbe57b19b5809da0e28af6ecf099cbb765703a96ddba53748ee9  PSA_RCEP_03_OUTPUT_INVENTORY_20260719.json`. Binding of that digest to the actual inventory bytes is UNMEASURED (no shell hashing).
- C. Stale baseline (identify-only, NOT evidence): promoted tree `output/natcs_empirical_cp/rcep/`; governance identifiers: id `bacaa2ac54a4d12b3a25829c5da9ee5763856679355569ae1c24683d1b6b4920`, archived full-fit loss `1.0144843433`. MEASURED corroboration: stale `selection_summary.json.full_fit_loss = 1.014484343302525` — matches the archived identifier value exactly (see V-T4).
- Lineage: prior auditor instance died pre-write; zero prior receipt bytes existed at start (task-authority assertion; no contrary evidence found); its two leads were treated as hypotheses and BOTH were then confirmed by direct measurement (V-T4).

## 2. V-T1 INVENTORY INTEGRITY — PARTIAL (existence-level PASS; hash/size/symlink UNMEASURED)

Existence verification (fs-read oracle; binary files return distinct "binary file" error vs "not found"):

| # | path (relative to …/psa-20260719-rcep-03/rcep) | exists | content-level check |
|---|---|---|---|
| 1 | aggregate_cp_bootstrap.csv | YES | read: 37 lines = header+36 dates |
| 2 | aggregate_cp_metrics.csv | YES | read: 217 lines = header+216 rows |
| 3 | block_length_sensitivity.csv | YES | read: 4 rows |
| 4 | clipping_summary.csv | YES | read: 6 rows |
| 5–22 | figures/*.pdf|.png (all 18) | YES ×18 | binary-oracle only (no visual/hash check) |
| 23 | full_path_attenuation_bootstrap.csv | YES | read: 501 lines = header+500 draws |
| 24 | full_path_attenuation_bootstrap_summary.csv | YES | read: 4 rows |
| 25 | full_path_attenuation_bootstrap_summary.json | YES | parsed OK |
| 26 | girf_cp_bootstrap.json | YES | head+tail structural probes OK; closes properly at line 35006 |
| 27 | girf_cp_point.json | YES | parsed OK |
| 28 | network_propagation_perturbation_summary.csv | YES | read: 1 row |
| 29 | network_propagation_perturbations.csv | YES | read: 37 lines = header+36 |
| 30 | pairwise_cp_panel.csv | YES | head+tail reads; 45361 lines = header+45360 rows |
| 31 | selection_summary.json | YES | parsed OK |
| 32 | stability_exclusion_sensitivity.csv | YES | read: 8 rows |
| 33 | stability_projected_sensitivity.csv | YES | read: 8 rows |
| 34 | stability_summary.csv | YES | read: 37 lines = header+36 |
| 35 | table_rcep_cp_benchmark.csv | YES | read: 10 rows |
| 36 | table_rcep_cp_structural_breaks.csv | YES | read: 4 rows |

- Inventory set (36) vs on-disk probed set (36/36 declared paths): **declared→disk = 0 missing**.
- Disk→inventory direction (EXTRA files in quarantine dirs): **UNMEASURED** — no directory listing capability (bash/glob/grep all down). Blind name-probes found `manifest.json` ABSENT at both `…rcep-03/` and `…rcep-03/rcep/` levels.
- MATCH/DRIFT table on size_bytes/sha256 (36 rows): **UNMEASURED** (cannot hash or stat without shell). Inventory declares e.g. pairwise 7716607 B / sha 277273f6…; these remain CLAIMS, not measurements.
- Symlink check: **UNMEASURED** (inventory claims symlink_count 0; unverifiable here).
- Sidecar filename discrepancy recorded (§1 B').

## 2A. INSTRUMENTATION ADDENDUM — V-T1 RE-OPENED (2026-08-26, same date, Asia/Shanghai)

(a) **Spawn-failure history**: original audit session had zero shell/search capability — `bash` failed `spawn bash ENOENT` (initial + mandated retry), `glob` and `grep` failed ripgrep launch. At addendum time the auditor re-probed `bash` (trivial probe, then an actual `shasum -a 256` verification command): BOTH again returned `spawn bash ENOENT` → first-party hash recomputation remains impossible for this auditor instance.

(b) **Orchestrator-executed measurement disclosure**: the orchestrator ran the hash pass externally and supplied raw output at `tmp/rcep_vt1_measurement_20260826.json` (read in full by this auditor; 338 lines). Method as stated by orchestrator: base auto-resolution first tried `…/psa-20260719-rcep-03/rcep` (matching this receipt's successful read paths and the inventory `output_root` semantics); all 36 declared paths exist there; result MATCH 36/36, drift=[], missing=[], extra_on_disk=[], symlinks=[]; provenance narrative: inventory digests recorded pre-migration on Desktop; today's `~/work` copy matches all 36 exactly ⇒ migrated bytes == bytes hashed at inventory time. This receipt records the measurement as ORCHESTRATOR-SUPPLIED, not auditor-executed.

(c) **Auditor spot-checks of the instrument** (all PASS):
1. Internal consistency: 36 rows, every row `status=MATCH` with `sha256==exp_sha256` and `size_bytes==exp_size`; declared_count=measured_count=match=36; empty drift/missing/extra/symlink arrays coherent with per-row statuses.
2. Expectation fidelity: every `exp_sha256`/`exp_size` pair equals the corresponding declaration in `PSA_RCEP_03_OUTPUT_INVENTORY_20260719.json` — verified against THIS auditor's own independent full read of the inventory earlier in this session (e.g., aggregate_cp_bootstrap 17293 B / aeefaada…48f; aggregate_cp_metrics 18045 B / 0897675b…dcc; stability_summary 1173 B / a249b4f4…06a; pairwise_cp_panel 7716607 B / 277273f6…6fa; girf_cp_bootstrap 911950 B / f894eb88…e91; benchmark 1767 B / c3a6be9d…856).
3. Path-set equality: rows[] path multiset == inventory path set exactly (36 names, same enumeration order, figures included).
4. Physical plausibility (size vs line count measured by this auditor): stability_summary 1173 B / 37 lines ≈ 32 B/line ✓; aggregate_cp_metrics 18045 B / 217 lines ≈ 83 B/line ✓; pairwise_cp_panel 7716607 B / 45361 lines ≈ 170 B/line ✓; girf_cp_bootstrap.json 911950 B / 35006 lines ≈ 26 B/line ✓; full_path_attenuation_bootstrap.csv 45039 B / 501 lines ≈ 90 B/line ✓.
5. Temporal stability (bytes unchanged between audit-time reads and now): re-reads of stability_summary.csv (head), table_rcep_cp_benchmark.csv (rows 1–3), selection_summary.json (tail incl. F2-relevant frozen_evolving_ratio block) are byte-identical to audit-time captures ⇒ instrument hashed the same content this receipt's numeric findings describe.
Residual limitation (disclosed, does not block): spot-checks corroborate CONSISTENCY of the instrument with independently-held expectations; they cannot cryptographically reproduce digests first-party. Custody of the measurement is orchestrator-side; recorded as such.

(d) **Revised V-T1 verdict (this auditor's judgment)**: **PASS — qualified as instrument-mediated** (auditor-adjudicated; not first-party-hashed). Rationale: all four previously-UNMEASURED dimensions (sha256 ×36, size ×36, symlink ×36, extra-file enumeration) are now covered by measurements with ZERO discrepancies; the instrument's expectations match the inventory independently held by this auditor; ≥6 plausibility/stability spot-checks pass across every artifact class; no inconsistency found anywhere in the instrument file. The qualification preserves the custody fact: hashes were recomputed by the orchestrator's instrumentation, not by the auditing session. Existence-level findings from the original §2 remain valid and unaffected.

## 3. V-T2 EXECUTION PROVENANCE — PARTIAL

Measured inside quarantine artifacts (config echo):
- `selection_summary.json`: dataset rcep; ridge_lambda 0.01 (selected min of {1e-06:75.284, 1e-05:75.047, 1e-04:72.741, 1e-03:54.637, 1e-02:11.756}); cp_rank 2 selected by rolling-origin validation losses {1:0.7080, 2:0.4633, 3:13.4222, 4:13.2958} (min=rank2 ✓ coherent); fit_losses {1:0.36416, 2:0.21150, 3:0.15039, 4:0.11289}; full_fit_loss 0.6196736654708991; window 40 = requested_window 40 (no fallback triggered); lag_order 2; cp_inits 6; cp_max_iter 100; cp_tol 1e-06; bootstrap 500 reps, block 4; rank_validation method "rolling-origin one-step-ahead CP reconstruction", cutoff 2022-01-01, available_origins 24, evaluated 21 per rank; intercept_policy "origin-specific fitted local intercept"; helper_git_commit `d0e398b896848f26413cf9aa9dfca15fb4e7ce64`.
- Completion/status markers: NO manifest/completion-marker FILE exists in quarantine (probes: manifest.json absent at both levels). Provenance lives INSIDE selection_summary.json (status string `completed_quarantined_unreviewed` comes from the INVENTORY, not from an in-run marker). Timestamp fields: NONE found in any quarantine artifact read (run wall-clock time UNRECOVERABLE from artifacts).
- Error payloads: none observed in any artifact; instead an explicit honest non-identifiability marker inside stability_exclusion_sensitivity.csv (see V-T3).
- Notable config behavior: requested_girf_dates ["2018-12-31","2022-12-31"]; selected_girf_dates maps 2018-12-31→2018-12-31 but **"2022-12-31"→"2020-03-31"** — a substitution whose rule is NOT explained inside any artifact read; simultaneously girf_cp_point.json contains an entry keyed by the literal "2022-12-31". Flagged F1 (needs code-level explanation; outside value-audit scope to adjudicate).
- Bootstrap-type string changed vs stale: quarantine "GLOBAL moving-block residual bootstrap with FULL ROLLING and CP re-estimation" vs stale "moving-block residual bootstrap with CP re-estimation" — consistent with a post-repair method change (candidate-side redesign).

## 4. V-T3 NUMERIC INTERNAL CONSISTENCY — PASS (with flagged items F1, F2, F3)

Parse validity: every text artifact parsed cleanly (CSV column counts constant per file; JSON well-formed incl. girf_cp_bootstrap.json head/tail closure at line 35006).

Row/column counts & coverage vs declared:
- stability_summary.csv: 36 rows = 2016Q1..2024Q4 quarterly, contiguous, unique dates ✓
- aggregate_cp_metrics.csv: 216 rows = 6 variants × 36 dates exactly (baseline_import, export_network, symmetric_network, long_window_network @H=8; baseline_h12 @H=12; fixed_pre @H=8); variant set EXACTLY matches clipping_summary.csv variant_key set ✓
- aggregate_cp_bootstrap.csv: 36 rows × 25 cols, all finite ✓
- pairwise_cp_panel.csv: 45360 data rows = 6 variants × 7560; 7560 = 210 directed pairs (15×14, RCEP) × 36 quarters; benchmark N=7560 ✓; tail clean at 2024Q4/fixed_pre
- full_path_attenuation_bootstrap.csv: 500 draws = declared bootstrap_replications 500 ✓ (direct count)
- girf_cp_bootstrap.json: 35006 lines; date-boundary probe at lines 17503–17504 confirms second key `"2022-12-31"` EXACTLY where 2 headers + 500×35-line rep blocks predict ⇒ both requested dates present, 500 reps/date by block arithmetic (full machine parse remains UNMEASURED)
- network_propagation_perturbations.csv: 36 rows, n=36 in summary ✓

Bootstrap CI ordering (p025 ≤ p16 ≤ p50 ≤ p84 ≤ p975):
- selection_summary.coef_bootstrap_summary: 4/4 quantities ordered ✓
- full_path_attenuation_bootstrap_summary.{csv,json}: identical values, 4/4 ordered ✓ (TRIPLE agreement with selection_summary — byte-equal numbers across three artifacts)
- block_length_sensitivity.csv: 3/3 rows ordered ✓ (reps reduced to 160 per block size — disclosed deviation from headline 500)
- aggregate_cp_bootstrap.csv: spot-checked ordering across all 36 rows (read in full) — ordered ✓; half-life columns capped at H (8/12) coherently

Finiteness scan: all numeric cells finite across every fully-read artifact; no NaN/inf/empty numeric anomalies. Placeholder scan: no TODO/FIXME/placeholder sentinels observed anywhere.

Strict containment check lower ≤ point ≤ upper [p025,p975]:
- evolving_coefficient point 0.0022967865 > p975 0.0020326521 → **point OUTSIDE its own bootstrap percentile CI** → flag **F2** (the headline evolving coefficient lies above the 97.5th percentile of its own replicates; analytic-SE significance p≈5.4e-11 in benchmark table coexists with this)
- frozen_coefficient, attenuation_difference, frozen_evolving_ratio points: inside [p025,p975] ✓ (3/4 pass)

Exact identities (internal consistency wins):
- attenuation_difference.point == evolving.point − frozen.point (0.0022967865167819556 − 0.0015920158589193666 = 0.000704770657862589) ✓ EXACT
- attenuation_difference.mean == evolving.mean − frozen.mean ✓ EXACT (0.0003823703935128176)
- frozen_evolving_ratio.point == frozen.point / evolving.point ✓ (=0.6931492532226947)
- table_rcep_cp_benchmark "Evolving topology" coefficient == selection_summary evolving point (16-digit equal) ✓; "Frozen benchmark topology" == frozen point ✓
- stability_exclusion_sensitivity N_stable 3570 == 210 pairs × 17 stable dates; 17 == 36 − 19 unstable ✓ EXACT coherence with stability_summary unstable count
- stability_rate_cp 0.5277777777777778 == 19/36 ✓ EXACT
- network_propagation summary mean_g_net_base 0.19322449676315634 == mean over perturbations g_net_base column == aggregate_cp_metrics baseline_import mean ✓ (row-wise equality also verified on sampled rows)
- GIRF identity total[h] == direct[h] + network[h], h=0..1 both dates, float-exact to ~1e-18 ✓ (h≥2 not exhaustively recomputed)
- clipping_summary n_obs 7560 per variant == panel rows/variant ✓; trimmed-row N 7408 == 7560 − 152 (2×~1% trims) ✓
- Duplicate-key scan: no duplicate dates within any per-date table; variant×date keys unique in aggregate tables (verified by reading full files)

Embedded honesty marker (not an error): stability_exclusion_sensitivity.csv row "Pair-level coefficient / Stable dates only": Value/SE/p EMPTY, N=3570, Status=`not_identified`, Identification="TC_relief is collinear with pair/time effects in the retained sample" — a genuine fail-closed result recorded by the pipeline itself. Flag **F3**: under the repaired run, the stable-subsample regression is NOT identified; any stable-subsample claim is structurally unavailable.

Cross-table agreement aggregate_cp_metrics ↔ table_rcep_cp_benchmark: benchmark has no per-date g_net column to join directly; agreement established via coefficient identity (evolving/frozen points) and N identities above ✓.

## 5. V-T4 STALE-DELTA CHARACTERIZATION — candidate-vs-stale (stale = identify-only context, NOT evidence)

BOTH inherited leads CONFIRMED BY MEASUREMENT:

Lead (i) unstable rate:
- QUARANTINE stability_summary.csv: 19/36 rows unstable=1 (first 2020-06-30, all subsequent) → rate 0.527778 == selection_summary.stability_rate_cp ✓
- STALE promoted stability_summary.csv: 0/36 unstable → rate 0.000 == stale selection_summary.stability_rate_cp 0.0 ✓
- ⇒ "~0.53 vs all-stable" CONFIRMED.

Lead (ii) spectral-radius bands:
- QUARANTINE radius_cp ∈ [0.4496630475143816 (2018-06-30), 1.4489532745859717 (2021-09-30)] ≈ "~0.45–1.45" ✓
- STALE radius_cp ∈ [0.21109482644677996 (2020-09-30), 0.7455291905789042 (2021-06-30)] ≈ "~0.21–0.75" ✓
- ⇒ bands differ materially; quarantine regime crosses 1.0 from 2020-06-30 onward (19 consecutive quarters >1). CONFIRMED.

Full-fit loss delta: stale 1.014484343302525 (== governance archived identifier 1.0144843433, corroborating WHICH tree is the archived predecessor) vs quarantine candidate 0.6196736654708991 (Δ ≈ −0.39481, −38.9%).

Selection deltas: stale cp_rank 1 (monotone validation losses 0.220→0.731) vs candidate cp_rank 2 (losses 0.708/0.463/**13.42/13.30** — rank≥3 catastrophically worse; consistent with the rank-deficiency repair narrative but the mechanism is not documented in-artifact → part of flag F1-family observations). Ridge grid byte-identical between trees (same losses) → shared upstream data/config for ridge stage.

Headline coefficient delta: stale evolving point 0.0008732456785415317 (p=0.01395) vs candidate 0.0022967865167819556 (p=5.41e-11) — candidate ≈ 2.63× stale. Stale two-way-clustered p was 0.0 (exact zero, underflow-suspicious) vs candidate 0.03658 (finite). Stale frozen_evolving_ratio bootstrap mean −471724.7 (pathological, near-zero-denominator artifacts) vs candidate mean 0.6460 (well-behaved).

Stable-subsample contrast: stale exclusion table degenerate (Stable-only rows IDENTICAL to full-sample, N=7560 — coherent only because stale had zero unstable dates); candidate honestly reports not_identified (N=3570). Aggregate index: stale 0.05345254574299113 vs candidate 0.19322449676315634.

LABELING: all quarantine values are CANDIDATE values from a quarantined, value-unreviewed-until-now run; all promoted-tree values are STALE predecessor context identified (not evidenced) by hash `bacaa2ac…`. NOTHING here promotes, demotes, or activates either.

## 6. V-T5 CLAIM-MAPPING READINESS — POTENTIAL_ONLY_NOT_ACTIVATED

Standing governance blockers (as given by delegating authority; file-level re-verification impossible this session — see §0): PAPER_CLAIM_AUDIT BLOCKED; EMPIRICAL_IMPLEMENTATION_AUDIT FAIL.

Candidate mapping fragments (each requires the standing audits to clear before ANY manuscript use):

| # | potential claim fragment | artifact path | field(s) | readiness notes |
|---|---|---|---|---|
| M1 | Evolving-topology propagation exceeds frozen benchmark (attenuation difference) | rcep/table_rcep_cp_benchmark.csv | rows Topology benchmark; coef 0.00229679 vs 0.00159202, p 5.41e-11 / 3.55e-05 | POTENTIAL_ONLY; subject to F2 (point outside own percentile CI) |
| M2 | Attenuation difference bootstrap summary | rcep/full_path_attenuation_bootstrap_summary.json (+csv, selection echo) | attenuation_difference point/CI | POTENTIAL_ONLY; triple-source identical ✓ |
| M3 | Instability episode post-2020Q2 | rcep/stability_summary.csv | unstable column (19/36), radius band | POTENTIAL_ONLY; drives F3 non-identifiability |
| M4 | Stability-projected robustness | rcep/stability_projected_sensitivity.csv | projected coef 0.00193230, p 6.78e-07 | POTENTIAL_ONLY |
| M5 | Structural breaks around 2020Q2/2021Q4 | rcep/table_rcep_cp_structural_breaks.csv | break_dates, max_Chow_F | POTENTIAL_ONLY; approximate CIs labeled approx in-artifact |
| M6 | Network propagation under CHN exposure perturbation | rcep/network_propagation_perturbation_summary.csv (+perturbations.csv) | mean_g_net_delta 0.014392 | POTENTIAL_ONLY; single-perturbation scope |
| M7 | GIRF network vs direct decomposition | rcep/girf_cp_point.json (+girf_cp_bootstrap.json) | total/direct/network arrays | POTENTIAL_ONLY; blocked by F1 date-substitution opacity |
| M8 | Rank/ridge selection transparency | rcep/selection_summary.json | rank_losses, ridge_losses | POTENTIAL_ONLY |

ALL MAPPINGS: POTENTIAL_ONLY_NOT_ACTIVATED. This audit performs no activation.

## 7. VERDICTS

- V-T1 Inventory integrity: **PASS — qualified as instrument-mediated** (AMENDED per §2A; original session scored PARTIAL_PASS_WITH_UNMEASURED_COMPONENTS) — 36/36 sha256+size MATCH vs inventory via orchestrator-executed instrumentation adjudicated by this auditor; drift/missing/extra_on_disk/symlinks all empty; qualification: hashes not first-party-reproducible by the auditor (bash ENOENT ×2 at addendum time).
- V-T2 Execution provenance: **PARTIAL** — rich in-artifact config echo measured (incl. helper_git_commit d0e398b896848f26413cf9aa9dfca15fb4e7ce64); BUT no completion/manifest marker file, no timestamps; F1 date-substitution unexplained.
- V-T3 Numeric internal consistency: **PASS** — parse validity, coverage, ordering, finiteness, duplicate-key, cross-table identities all clean; flags F2 (headline point outside own percentile CI), F3 (stable-subsample not_identified), plus disclosed rep-count reductions (block-length 160/date) and UNMEASURED girf exact-replicate parse.
- V-T4 Stale-delta characterization: **PASS (characterization only)** — both leads confirmed by measurement; deltas quantified; strictly candidate-vs-stale labeling enforced.
- V-T5 Claim-mapping readiness: **PASS_AS_READINESS_ONLY** — 8 fragments mapped, all POTENTIAL_ONLY_NOT_ACTIVATED; standing blockers unchanged.

OVERALL: **SUPPORTED_FOR_DOWNSTREAM_REVIEW** (AMENDED — unchanged in outcome, strengthened in basis). Original basis: internal coherence of the quarantined bytes, with hash-level integrity flagged open. Amendment closes the open hash question: inventory digests == today's `~/work` bytes 36/36 (instrument-mediated, §2A), so the migrated tree is byte-identical to the bytes inventoried at quarantine time; V-T2/V-T3/V-T4/V-T5 verdicts unchanged. F1/F2/F3 remain attached and unchanged. Still explicitly NOT a promotion, NOT manuscript-ready, nothing activated.

Flags register: F1 girf date substitution 2022-12-31→2020-03-31 unexplained while BOTH dates appear in outputs (girf_cp_point.json keyed by literal 2022-12-31; girf_cp_bootstrap.json contains full 500-rep blocks for both keys); F2 evolving_coefficient point 0.00229679 > p975 0.00203265 (outside own bootstrap percentile CI); F3 stable-dates-only pair-level regression not_identified (TC_relief collinear with pair/time effects, N=3570). Blind filename probes `refine-logs/EXPERIMENT_AUDIT.md`, `refine-logs/PAPER_CLAIM_AUDIT.md` → not found under those names (actual receipt filenames unknown; directory enumeration impossible).

## 8. NOT-DONE LIST (explicit)

1. ~~SHA-256 recomputation of any file~~ → RESOLVED BY INSTRUMENTATION (§2A): orchestrator-measured 36/36 MATCH vs inventory; custody qualification retained.
2. ~~Byte-size verification of any file~~ → RESOLVED BY INSTRUMENTATION (§2A), same pass.
3. ~~Symlink presence/type check (lstat)~~ → RESOLVED BY INSTRUMENTATION (§2A): symlinks=[].
4. ~~Exhaustive directory enumeration for EXTRA undeclared files~~ → RESOLVED BY INSTRUMENTATION (§2A): extra_on_disk=[].
4b. NEW residual item from the amendment: first-party cryptographic reproduction of the 36 digests by the auditing instance itself (impossible this session); instrument fabrication risk accepted as disclosed custody limitation, not independently eliminable.
5. Full machine parse of girf_cp_bootstrap.json (exact 500/date replicate count) — line-arithmetic consistency only.
6. Visual/content inspection of 18 figures (binary-oracle existence only).
7. Recomputation of sidecar digest binding (PSA_RCEP_03_OUTPUT_INVENTORY_20260719.sha256 ↔ inventory bytes).
8. Re-verification on disk of standing-blocker receipts (PAPER_CLAIM_AUDIT / EMPIRICAL_IMPLEMENTATION_AUDIT) and of where promoted id `bacaa2ac…` is registered — accepted from delegating authority; blind probes (promoted-root manifest.json) came back not found.
9. Any code-level explanation/adjudication of F1 (out of scope for a value audit).
10. Any promotion, unquarantine, activation, or manuscript use — permanently out of scope for this receipt.

## 9. PROVENANCE DISCLOSURE

Auditor: ox-alpha (model identity; developing organization undisclosed). This receipt is self-adjudicated: the auditor audited outputs it did not produce and had no role in generating, but there is no second independent system verifying this audit. This is the FIRST COMPLETED value review of these exact quarantine bytes (value_review_performed was false since 2026-07-19; prior auditor instance died leaving zero bytes). Tooling failure (bash/glob/grep spawn failures) degraded V-T1/V-T2 to partial coverage; every degradation is marked UNMEASURED rather than assumed. AMENDMENT PROVENANCE: the closing V-T1 measurements were produced by ORCHESTRATOR-EXECUTED instrumentation (`tmp/rcep_vt1_measurement_20260826.json`) outside this auditor's process, then adjudicated by spot-checks recorded in §2A(c); the auditor never gained shell capability (ENOENT at both original and addendum time). Audit performed 2026-08-26 Asia/Shanghai; session-local time-of-day not independently verifiable.
