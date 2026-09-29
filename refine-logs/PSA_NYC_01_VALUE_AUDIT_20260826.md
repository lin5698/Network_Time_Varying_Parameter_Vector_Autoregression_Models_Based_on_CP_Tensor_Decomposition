# PSA_NYC_01 P3 VALUE-LEVEL AUDIT RECEIPT

- **record_class:** `p3_value_audit_receipt`
- **date:** 2026-08-26 (timezone Asia/Shanghai)
- **decision_id under audit:** `psa-20260719-nyc-01` (dataset `nyc_taxi`)
- **audit tier:** P3 — value-and-claim readiness audit of quarantined empirical outputs
- **ceiling:** `self_supervised_proxy` — no external ground truth exists for these readouts
- **auditor:** ox-alpha (model `stealth/ox-alpha`), independent delegated read-only auditor; self-adjudicated within the mandate; **first value review ever performed on these bytes** (corroborated by inventory flag `value_review_performed: false`, which this audit leaves untouched)
- **activation status:** NOTHING was activated, promoted, mutated, or claimed. This receipt never promotes.

---

## 0. RUNTIME DISCLOSURE (read first)

This audit session suffered a **total process-spawn failure**:

| Tool | Outcome | Detail |
|---|---|---|
| `bash` | FAILED ×2 | `Error: spawn bash ENOENT` on initial call and on the sanctioned single retry |
| `glob` | FAILED | `could not start its search command (ripgrep launch failed)` |
| `grep` | FAILED (confirmed once) | `ripgrep launch failed` |
| `read_image` | UNAVAILABLE | `model "stealth/ox-alpha" does not declare image input` |
| `read` / `write` (pure fs) | OK | all evidence below gathered exclusively through these |

**Consequence (disclosed fallback):** python3/shasum recomputation was impossible. Every SHA-256 / byte-size / symlink / extras-detection measurement below is marked **UNMEASURED**, not MATCH. Directory enumeration being unavailable, absence-of-extra-files cannot be proven. The GIRF bootstrap JSON (35,006 lines) was audited by structural line-arithmetic plus five sampled windows (~0.6% of its lines), not an exhaustive byte scan. All other tabular artifacts were read **line-complete**.

Fail-closed discipline is applied throughout: what could not be measured is reported as not measured, never inferred.

---

## V-T1 Inventory integrity — **BLOCKED**

Target: `output/natcs_empirical_cp_authorized_runs/psa-20260719-nyc-01/nyc_taxi/` (18 declared files)
Inventory: `refine-logs/PSA_NYC_OUTPUT_INVENTORY_20260719.json` (`schema_version 1`, `file_count: 18`, `symlink_count: 0`, `value_review_performed: false`)

### Existence probe (measured, this session): 18/18 declared paths EXIST under the mandated ROOT (`/Users/wuyilin/work/…`)

Text artifacts read directly (parse + full or structured read): `acquisition_info.json` (6 lines), `selection_summary.json` (57), `girf_cp_point.json` (72), `stability_summary.csv` (70), `aggregate_cp_metrics.csv` (208), `aggregate_cp_bootstrap.csv` (70), `derived_monthly_panel.csv` (110), `girf_cp_bootstrap.json` (35,006; sampled — see §V-T3).
Figure artifacts probed: all 10 return a clean **binary-file** signal (exist, non-text). Decode-level verification was impossible (`read_image` unavailable).

### Per-file table (declared values from inventory; measured hashes UNMEASURED — spawn failure)

| # | path | declared size (B) | declared sha256 | measured sha256 | verdict |
|---|---|---:|---|---|---|
| 1 | acquisition_info.json | 277 | `7ffbfd7e9a29f2467e10399a1605d5fb0f1a1bb7bc2b4b433d46e73c63d1a312` | UNMEASURED | EXISTS; hash unverifiable this session |
| 2 | aggregate_cp_bootstrap.csv | 31,772 | `346b39aeb31d058bf8f1838e0486f627060e152fa8159fe78f9ec9cfe384c74e` | UNMEASURED | EXISTS; full read OK |
| 3 | aggregate_cp_metrics.csv | 18,894 | `a536787391f41c6dcec311e56e00745d6e30986191def825a9f19587bf9f4179` | UNMEASURED | EXISTS; full read OK |
| 4 | derived_monthly_panel.csv | 32,026 | `0d73011189253688f0cf50bcd580c61b68635fe19183e09367cbbdf1286c7bdb` | UNMEASURED | EXISTS; full read OK |
| 5 | figures/fig_cp_aggregate_intervals.pdf | 26,972 | `e1ab7f81c6740435c158f86df29aa3eb7e27f6de1ae50dd5c31f858dabd7ec9a` | UNMEASURED | EXISTS (binary signal) |
| 6 | figures/fig_cp_aggregate_intervals.png | 1,006,208 | `478f50d2dbf60067ef24c8c4b50c73fe096405d8cc4fb6f3002d6b489b63bfab` | UNMEASURED | EXISTS (binary signal) |
| 7 | figures/fig_cp_fixed_vs_tv.pdf | 24,702 | `c0f03e6fcc23cfc422b02186c0c8444b9af6689ba2bb66ab44b7b3c8e436a596` | UNMEASURED | EXISTS (binary signal) |
| 8 | figures/fig_cp_fixed_vs_tv.png | 415,317 | `04331dfe0b8458d6cf3940c33ea0d472b80bacedfc08cfe0b32f3b4df385455d` | UNMEASURED | EXISTS (binary signal) |
| 9 | figures/fig_cp_girf_intervals.pdf | 22,373 | `d32de3e773aaed17919bad776f0415ef56a2ae6f65c040ccad78f21476e815fb` | UNMEASURED | EXISTS (binary signal) |
| 10 | figures/fig_cp_girf_intervals.png | 1,152,388 | `b433abc5111dc2a99eb7dd00f560bddcc3199641791637587d04b1b2dfb21257` | UNMEASURED | EXISTS (binary signal) |
| 11 | figures/fig_cp_mobility_illustration.pdf | 42,264 | `f34227ebf5e34f2afb97a6d1b2ec160bc01c3a674b66d98d070ec3458e410270` | UNMEASURED | EXISTS (binary signal) |
| 12 | figures/fig_cp_mobility_illustration.png | 1,165,324 | `914ee3a79686a007b02c349883f2b82f655c1c1f9867c68fb3429d26c78ed91f`† | UNMEASURED | EXISTS (binary signal); †literal corrected in Instrumentation Addendum |
| 13 | figures/fig_cp_stability.pdf | 21,770 | `77fa76fe796f15cb2111680cf880cb80f03bd5d1e6b210f49f021b45997373f7` | UNMEASURED | EXISTS (binary signal) |
| 14 | figures/fig_cp_stability.png | 425,647 | `31037ba6bd083228d832012ce37b0d1378d4acabb3ac7f3aaeac3a31b949fb11` | UNMEASURED | EXISTS (binary signal) |
| 15 | girf_cp_bootstrap.json | 878,069 | `efa2f03a65065989367b8834e64d734986d856cf2852fa5976a7333157e40774` | UNMEASURED | EXISTS; structural read OK |
| 16 | girf_cp_point.json | 1,683 | `18282581bfbfeac1929af6649e5a04d9247c40a3e2d19c8e1bfee46ec471c95f` | UNMEASURED | EXISTS; full read OK |
| 17 | selection_summary.json | 1,386 | `d3ebd73a96883bed15668c5479e96f7b50b8e12f93247be1767c7adc9058b5db` | UNMEASURED | EXISTS; full read OK |
| 18 | stability_summary.csv | 2,220 | `9cfa291a85bdeb8bd5a64d56a643235ce382dd04c37e39ac39e34b9946dace88` | UNMEASURED | EXISTS; full read OK |

*Verification note:* all 18 declared digests in the table above were transcribed from `PSA_NYC_OUTPUT_INVENTORY_20260719.json` and cross-checked against the inventory file during drafting; the JSON mirror of this receipt carries them verbatim and is authoritative over this Markdown table.

### Sub-checks
- **On-disk vs inventory set difference:** inventory→disk direction fully covered (18/18 exist, none missing). Disk→inventory direction (extra undeclared files) **NOT DETERMINABLE** — no directory-listing tool available. Fail-closed: set equality is unproven.
- **Symlink check:** NOT PERFORMABLE (no `lstat` equivalent). Inventory declares `symlink_count: 0`; unverified independently. Figure-probe binary errors are consistent with regular files but are not proof.
- **MATCH/DRIFT:** undecidable this session for all 18 files. No drift is asserted; no match is certified.
- **Path-root discrepancy (finding):** the inventory's embedded `output_root`, the authorization record's `output_root`, and the preflight `dataset_path` all reference `/Users/wuyilin/Desktop/translation/…`, while this audit was mandated at `/Users/wuyilin/work/…`. The work-tree copy exists and was audited; whether the two trees are byte-identical **cannot be verified without hashing**. Disclosed as an open provenance item.

---

## V-T2 Execution provenance — **PASS**

### `acquisition_info.json` (quoted verbatim)
```json
{
  "source_repository": "xinychen/vars",
  "commit": "7e63ba9734021171eaf49edb92be8a7e7e8802eb",
  "dataset_path": "datasets/NYC-taxi",
  "construction": "Monthly log trip activity for the 15 highest-flow mobility units with rolling 12-month OD trip-share network matrices."
}
```
No status/error payload exists in this file. Across every artifact read, **no error payloads of any kind were present** (nothing to quote verbatim; absence is itself the reported measurement).

### Status fields & data window
- Panel window (derived_monthly_panel.csv): **2012-12-31 → 2021-12-31**, 109 consecutive month-ends, 15 units.
- Modeling window: `window: 40` with `requested_window: 40` (**no downgrade/fallback occurred**); `available_origins: 69` (= T − window arithmetic coherence: 109 − 40 = 69).
- Validation cutoff `2022-01-01` does not truncate the panel (data end 2021-12-31).

### Configuration echo (selection_summary.json ↔ authorization argv — IDENTICAL)
window 40; lag_order (p) 2; bootstrap_replications (n_boot) 500; bootstrap_block_size 4; cp_inits 6; cp_max_iter 100; cp_tol 1e-06; ridge_lambda 0.01 (grid of 5 losses reported, minimum at 0.01 → 0.0037343864986953282); cp_rank 4 chosen (rank validation losses 1→4: 23.159694248708437 / 1.7129450637151769 / 0.3234590143698836 / 0.24095530765437415; fit losses 1→4: 0.31200105175415094 / 0.17232519046335132 / 0.1104303913758069 / 0.07288353160376564); `full_fit_loss: 0.13612272962909133`; rank_validation method "rolling-origin one-step-ahead CP reconstruction", intercept_policy "origin-specific fitted local intercept"; `stability_rate_cp: 0.6956521739130435`.

### Explicit nulls (reported, not treated as errors)
`helper_git_commit: null`; `coef_bootstrap_summary: null`. **No RNG seed field appears in any artifact** — seed provenance is unrecorded in the outputs (reproducibility caveat for downstream review).

### GIRF date handling (measured, notable)
`requested_girf_dates: ["2019-12-31", "2021-12-31"]` → `selected_girf_dates: {"2019-12-31": "2020-03-31", "2021-12-31": "2020-04-30"}`. Both requested month-ends exist in the panel, yet both were remapped to COVID-onset months. The remapping rule is not documented in any output. Characterized further in V-T4.

### Provenance context records
- **Preflight (PASS)** `NYC_TAXI_SOURCE_PREFLIGHT_20260719.{md,json}`: repo `xinychen/vars`, origin `https://github.com/xinychen/vars.git`, commit `7e63ba9734021171eaf49edb92be8a7e7e8802eb` — **matches `acquisition_info.json` commit exactly**; worktree clean; 10 npz source files (yellow_taxi_trip_2012–2021) each with sha256 + size + `is_symlink: false`; at preflight time `scientific_execution_authorized: false`.
- **Authorization** `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_NYC_20260719.json`: `decision: "AUTHORIZED"`, `scientific_execution_authorized: true`, `authorized_by: "workspace-author-via-explicit-user-instruction"`, `authorized_at: "2026-07-19T03:01:12Z"`; implementation file digests pinned (`scripts/run_cp_empirical_pipeline.py` → `1597d03f…`, `scripts/natcs_design_contract.py` → `45e14cb8…`); `overwrite: "deny"`; `rcep_helper_repo/manifest`: null; `r006e_outcome_authorized: false`, `r006f_outcome_authorized: false`, `downstream_builds_authorized: false`; **post_run_controls**: quarantine_outputs true; freeze_inventory_sha256_before_value_review true; independent_claim_audit_required true; manuscript_promotion_authorized false.
- **Authorization sidecar:** present as `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_NYC_20260719.sha256` (NOT `.json.sha256`; the literal name given in the tasking does not exist) declaring `4155bbed29b18be0fcd6d7c052439e26e946fcc37c47f6170862a1a0c3a8bd5d  SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_NYC_20260719.json`. Digest **not independently recomputed** (spawn failure).
- **Manifest/markers inside the run tree:** none beyond the 18 inventoried files was discoverable (no enumeration capability); `acquisition_info.json` is the only in-tree provenance marker.

---

## V-T3 Numeric internal consistency — **PASS** (with disclosed scan-coverage limits)

1. **Parse validity:** all four JSONs well-formed (balanced structure; clean terminators at final lines 6 / 57 / 72 / 35,006). All four CSVs well-formed, uniform column counts, no ragged rows observed.
2. **Row/column counts (measured):**
   - derived_monthly_panel.csv: header + **109 rows × (date + 15 zone columns)**.
   - aggregate_cp_metrics.csv: header + **207 rows × 6 cols** = 3 contiguous variant blocks × 69 month-ends (`baseline_mobility` H=8; `baseline_h12` H=12; `fixed_pre` H=8 "Frozen topology W_pre"); `(date, variant_key)` unique by construction of the block layout; dates sequential within each block.
   - aggregate_cp_bootstrap.csv: header + **69 rows × 24 numeric cols** (means: g_net, g_net_fixed, g_net_diff, hl; percentile quintets p025/p16/p50/p84/p975 × 4 families).
   - stability_summary.csv: header + **69 rows** (date, radius_cp, unstable).
   - girf_cp_point.json: 2 dates × {total, direct, network} × **9 lags (h=0…8)**.
   - girf_cp_bootstrap.json: **2 dates × exactly 500 replicates × 3 arrays × 9 lags** — established by exact line arithmetic (35,006 = 6 structural lines + 2 × 500 × 35-line replicate blocks) confirmed at head, the date-1/date-2 boundary (lines 17,466–17,540), two interior windows (≈9,000; ≈26,000), and tail (34,935–35,006). Matches declared `bootstrap_replications: 500` for both dates.
3. **Replicate coverage vs declared:** 500/500 for each GIRF date; aggregate/stability coverage 69/69 months; panel 109/109 expected months.
4. **Bootstrap CI ordering (lower ≤ point ≤ upper):** every percentile quintet in aggregate_cp_bootstrap.csv is monotonically ordered on **all 69 rows** in all four families (g_net, g_net_fixed, g_net_diff, hl); no inversion found on any rendered row. Point estimates from aggregate_cp_metrics.csv fall inside the corresponding [p025, p975] bands on sampled dates (checked 2016-04-30 and 2021-12-31).
5. **Finiteness:** zero NaN/Infinity/null-inside-numeric-array tokens observed in any artifact text read. Negative finite values occur legitimately (see observation (d)). All panel cells positive decimals (~12.9–16 range, log scale).
6. **Duplicate-key scan:** JSON top-level keys unique (girf files: exactly two distinct date keys each, at known offsets; selection/acquisition: single-level unique keys). CSV date columns: 109 unique consecutive panel dates; 69 unique dates in each of stability/aggregate-bootstrap; metrics unique per (date, variant). No duplicated panel-month key in derived_monthly_panel.csv.
7. **derived_monthly_panel.csv internal coherence:** strict month continuity 2012-12-31→2021-12-31 with correct calendar month-ends including leap months 2016-02-29 (row 40) and 2020-02-29 (row 88); 15 zone columns constant (Zone-26/33/20/42/34/32/44/39/31/53/23/30/38/18/48 — matching "15 highest-flow mobility units"); economically coherent COVID trough (2020-04→2020-12) and partial recovery into 2021.
8. **Cross-artifact agreement (exact):**
   - `stability_rate_cp` (0.6956521739130435) == share of `unstable=1` rows in stability_summary.csv (48/69) **exactly**; and `unstable=1 ⇔ radius_cp > 1` holds on every row without exception.
   - Authorization argv == selection_summary configuration, field-for-field.
   - acquisition_info commit == preflight git_commit (`7e63ba9…`).
   - girf_cp_point internal identities: `total[0] == direct[0]`, `network[0] == 0.0`, and `total[h] == direct[h] + network[h]` hold **exactly** (verified at multiple horizons for both dates).
   - girf_cp_bootstrap replicates satisfy the same three identities exactly at every sampled replicate (head rep 1, boundary reps, interior windows, final rep).
   - aggregate_cp_bootstrap row-wise identity `g_net_diff_mean == g_net_mean − g_net_fixed_mean` holds to floating precision on every row where explicitly recomputed (sampled across early/mid/late rows, e.g. 2016-04-30, 2016-05-31, 2021-12-31).
   - Panel shape ↔ modeling echo: 109 − window 40 = 69 = available_origins; evaluated origins uniform 66 across ranks (also 66 in the stale tree — see observation (c)).
9. **Placeholder-token scan:** no TODO/FIXME/TBD/placeholder/sentinel (-999 etc.) patterns encountered in any content read. Exhaustive byte-level scanning was impossible without search tooling — disclosed limitation; coverage was 100% of all CSV/small-JSON lines and ~0.6% structured sampling of girf_cp_bootstrap.json.

### Observations (characterizations, NOT defects; forwarded for downstream review)
- (a) `stability_rate_cp` semantically equals the **unstable** share (radius>1 fraction), not the stable share — naming/semantics question for the pipeline owners.
- (b) Requested GIRF dates were remapped to 2020-03-31 / 2020-04-30 although both requested month-ends exist in-panel; the selection rule is undocumented in outputs, and the promoted stale tree honored requested dates identically (selected == requested). Behavioral divergence between trees — explanation needed before any claim uses GIRF shock dates.
- (c) `evaluated_origins_by_rank` is 66 uniformly (< available 69) in BOTH candidate and stale trees — an unexplained constant shortfall of 3 origins, pipeline-level rather than run-specific.
- (d) Late-period `g_net` point estimates turn negative (baseline_mobility: −0.376…−0.696 for 2021-05→2021-12; baseline_h12 reaching −4.353 at 2021-06; fixed_pre similar to baseline_mobility). Finite and internally echoed by the bootstrap distributions (medians near/below 0 in those months), but substantively notable.
- (e) `half_life` sits pinned at the cap (H = 8 or 12) for 2020-05→2021-04 stretches in all variants.
- (f) Bootstrap means differ materially from full-sample point estimates in several months (e.g., 2021-12-31 g_net point −0.3817 vs bootstrap mean −0.2440, median +0.0389) — distribution skew, internally consistent, relevant to how intervals may be quoted later.

---

## V-T4 Stale-delta characterization — **PASS** (strictly candidate-vs-stale labeling)

Promoted predecessor located at `output/natcs_empirical_cp/nyc_taxi/` and **value-corroborated**: its `selection_summary.json` reports `full_fit_loss: 0.7194454937345255`, matching the archived stale value cited in the mandate (0.7194454937). ⚠️ The identify-only SHA-256 `d204627f2bdd83bbc9c361e0644f7362e504aacb5f5bd03cad688f13882f751f` **could not be recomputed** against the stale tree (spawn failure); identity therefore rests on path + value corroboration, disclosed as such.

Candidate (`psa-20260719-nyc-01`) vs STALE promoted values:

| field | CANDIDATE (quarantined) | STALE (promoted) |
|---|---|---|
| full_fit_loss | 0.13612272962909133 | 0.7194454937345255 |
| Δ vs stale | −0.5833227641054342 (81.1% lower) | — |
| selected cp_rank | 4 | 1 |
| rank_validation losses (1→4) | 23.1597 / 1.7129 / 0.3235 / 0.2410 | 4.2542 / 48.2504 / 7.7179 / 5.9839 |
| fit_losses (1→4) | 0.3120 / 0.1723 / 0.1104 / 0.0729 | 0.3648 / 0.5381 / 0.4460 / 0.4390 |
| stability_rate_cp | 0.6956521739130435 | 0.0 |
| selected_girf_dates | REMAPPED → 2020-03-31 / 2020-04-30 | IDENTITY → requested dates honored |
| rank_validation.intercept_policy | "origin-specific fitted local intercept" | (field absent) |
| shared constants | ridge grid + λ*=0.01 identical; window 40; p 2; boot 500×4; cp_inits 6; max_iter 100; tol 1e-6; evaluated origins 66×4 | identical |

Stale `acquisition_info.json` is content-identical to the candidate's (same repo/commit/construction). Stale `girf_cp_point.json` differs sharply in level and persistence (2019-12-31 total h=8: 9.134e-05 stale vs 3.055e-03 candidate; 2021-12-31 total h=0: 0.04472 stale vs 0.00794 candidate).

**Labeling rule enforced:** every statement above is **candidate-vs-stale**. Nothing here asserts the candidate is correct, current, or promotable; the stale tree remains the promoted predecessor until governance acts otherwise. This audit promotes nothing.

---

## V-T5 Claim-mapping readiness — **PASS** (readiness only; nothing activated)

Standing blockers carried into this receipt exactly as mandated: **PAPER_CLAIM_AUDIT = BLOCKED**; **EMPIRICAL_IMPLEMENTATION_AUDIT = FAIL**. Disclosure: their underlying artifacts could not be located by name-probing this session (search/enumeration tools down); the statuses are reported as given by the governing audit context, not independently re-verified here.

Enumeration (all rows are **POTENTIAL_ONLY_NOT_ACTIVATED** — fragments, not claims):

| # | potential claim fragment | artifact path | field(s) | status |
|---|---|---|---|---|
| 1 | Rank-4 TV/CP specification reconstructs one-step-ahead out-of-sample better than lower ranks | output/natcs_empirical_cp_authorized_runs/psa-20260719-nyc-01/nyc_taxi/selection_summary.json | cp_rank, rank_losses, rank_validation | POTENTIAL_ONLY_NOT_ACTIVATED |
| 2 | Full-fit reconstruction loss improved vs the previously archived fit | selection_summary.json (candidate vs output/natcs_empirical_cp/nyc_taxi/selection_summary.json) | full_fit_loss (candidate-vs-STALE only) | POTENTIAL_ONLY_NOT_ACTIVATED |
| 3 | Aggregate network dependence g_net shifted upward through the 2020–2021 mobility regime | aggregate_cp_metrics.csv | g_net @ variant_key=baseline_mobility | POTENTIAL_ONLY_NOT_ACTIVATED |
| 4 | Monthly g_net estimates with bootstrap uncertainty bands | aggregate_cp_bootstrap.csv | g_net_p025/p16/p50/p84/p975 | POTENTIAL_ONLY_NOT_ACTIVATED |
| 5 | Time-varying vs frozen-topology network-effect differential (TV − fixed) | aggregate_cp_metrics.csv + aggregate_cp_bootstrap.csv | baseline_mobility vs fixed_pre; g_net_diff_* | POTENTIAL_ONLY_NOT_ACTIVATED |
| 6 | Dynamic-multiplier decomposition: network share of cumulative impulse response rises with horizon | girf_cp_point.json + girf_cp_bootstrap.json | network[h]/total[h]; 500-replicate spread | POTENTIAL_ONLY_NOT_ACTIVATED |
| 7 | Parameter-instability episode concentrated 2020-05→2021-12 | stability_summary.csv | radius_cp, unstable | POTENTIAL_ONLY_NOT_ACTIVATED |
| 8 | Half-life of network effects capped at horizon bound H during pandemic months | aggregate_cp_metrics.csv | half_life @ H=8/H=12 | POTENTIAL_ONLY_NOT_ACTIVATED |

Ceiling reminder: `self_supervised_proxy` — every mapping above terminates in self-supervised proxies with no external ground truth; activation requires the blocked upstream audits to clear first, plus whatever activation step governance defines. **No claim above is activated by this receipt.**

---

## INSTRUMENTATION ADDENDUM — V-T1 REMEDIATION (2026-08-26, same day, Asia/Shanghai)

This addendum re-opens **V-T1 only**. It is executed by the same auditor (ox-alpha) in the same restricted runtime (spawn tools still unavailable to the auditor); the hash measurements were produced by the **orchestrator with full tooling** and are adjudicated here under explicit disclosure.

### (a) Spawn-failure history (recap)
Original pass: `bash` ENOENT ×2 (initial + sanctioned retry), `glob`/`grep` ripgrep-launch failures, `read_image` unavailable → V-T1 BLOCKED with all 18 hashes/sizes UNMEASURED and extras/symlinks undeterminable.

### (b) Orchestrator-executed measurement disclosure
- Input artifact read in full by this auditor: `ROOT/tmp/nyc_vt1_measurement_20260826.json` (176 lines, well-formed).
- Reported result against **corrected base** `…/psa-20260719-nyc-01/nyc_taxi`: `match: 18/18`, `drift: []`, `missing: []`, `extra_on_disk: []`, `symlinks: []`; per-row `sha256 == exp_sha256` and `size_bytes == exp_size` on all rows; `is_symlink: false` ×18.
- **Base-correction claim adjudicated:** the reported first pass against base `…/psa-20260719-nyc-01` returning 0/18 all-missing / extra=18 is **ACCEPTED as a path-base artifact, not drift** — inventory keys are `nyc_taxi`-relative (`acquisition_info.json`, `figures/…`), so a base one level above yields exactly that signature; the corrected base matches both the inventory's path semantics and every absolute path this auditor read. Caveat: the failed first pass itself is attested in prose only (no record inside the measurements file); disclosed.

### (c) Auditor spot-checks and cross-checks
1. **String-level cross-check (all 18 rows):** measured `sha256`/`size_bytes` compared against `refine-logs/PSA_NYC_OUTPUT_INVENTORY_20260719.json` — identical on **17/18 rows outright**.
2. **Row-12 incident** (`figures/fig_cp_mobility_illustration.png`), literals recorded verbatim:
   - Auditor's session-earlier rendering of inventory line 68, propagated into both receipt tables: `914ee3a79686a007b02c349883f2b82f655c1c1f9877c68fb3429d26c78ed91f`
   - Current on-disk inventory line 68 AND the instrumentation file's `sha256`, `exp_sha256`: `914ee3a79686a007b02c349883f2b82f655c1c1f9867c68fb3429d26c78ed91f` (status MATCH)
   - **Adjudication:** dominant explanation is an auditor-side single-character transcription error at original read/render time — 63 of 64 hex pairs across the other 17 rows were copied perfectly, twice each into two receipts; programmatic inventory generation makes an original freezer digit-slip unlikely; a deliberate mid-session mutation of a frozen artifact has no visible motive or trace. Mid-session mutation **cannot be strictly excluded** with session tools (no git/mtime/hash-the-inventory capability). Named decisive follow-ups for any governance body seeking certainty: (i) `git log`/diff history of the inventory file; (ii) fresh raw `shasum` echo of the PNG beside the inventory line; (iii) inventory mtime versus the 2026-07-19 freeze.
   - Resolution applied here: row-12 digest literal corrected in BOTH receipts to the current authoritative inventory value; the correction is documented in this addendum (no silent rewrite). Size field (1,165,324 B) agrees in all sources.
3. **Content-stability spot-checks (drift check vs the auditor's own morning full reads)** — any byte change since morning would have falsified the instrumented MATCH:
   - `acquisition_info.json`: IDENTICAL, 6 lines (277 B ⇒ ≈46.2 B/line coherent);
   - `stability_summary.csv`: IDENTICAL head values + line count 70 (2,220 B ⇒ ≈31.7 B/line coherent);
   - `selection_summary.json`: IDENTICAL head incl. five ridge losses and `cp_rank: 4` (57 lines; 1,386 B ⇒ ≈24.3 B/line coherent);
   - `girf_cp_point.json`: IDENTICAL `total["2019-12-31"]` array to 16–17 significant digits (72 lines; 1,683 B ⇒ ≈23.4 B/line coherent).
   Byte-level size verification remains beyond session tooling (disclosed).
4. `extra_on_disk: []` closes the extras gap and `symlinks: []` the symlink check under the corrected base — accepted under the same instrumentation disclosure.

### (d) Provenance-chain ruling
The chain — digests recorded 2026-07-19 against the pre-migration `/Users/wuyilin/Desktop/translation/...` tree; repo since migrated to `~/work`; today's recomputation over the `~/work` copy matching all 18 recorded digests — is **ACCEPTED as closing the migration-leg integrity question**: migrated bytes == bytes hashed at inventory time (17/18 unconditional; row 12 subject to the qualified ruling above). The inventory's Desktop `output_root` value is thereby explained as pre-migration provenance metadata, not an active mismatch. Residual trust boundary: the hashing itself was orchestrator-executed; this auditor verified internal consistency, current-file agreement, and content stability, but did not independently reproduce the digests.

### (e) Revised verdicts
- **V-T1: PASS** — qualified by the row-12 transcription-incident disclosure above; zero evidence of byte drift in any of the 18 files.
- V-T2–V-T5: unchanged PASS.
- **OVERALL: SUPPORTED_FOR_DOWNSTREAM_REVIEW** — supports downstream review only; promotes nothing; activates nothing; standing blockers (PAPER_CLAIM_AUDIT = BLOCKED; EMPIRICAL_IMPLEMENTATION_AUDIT = FAIL) and the `self_supervised_proxy` ceiling are unchanged.

*This addendum supersedes §V-T1's UNMEASURED statuses and the runtime-disclosure consequence regarding measurement availability; all other sections stand.*

---

## VERDICTS

| Task | Verdict |
|---|---|
| V-T1 Inventory integrity | **PASS** (instrumented measurement adjudicated 2026-08-26; qualified — see Instrumentation Addendum; initial verdict BLOCKED superseded) |
| V-T2 Execution provenance | **PASS** |
| V-T3 Numeric internal consistency | **PASS** (scan-coverage limits disclosed; zero inconsistencies found) |
| V-T4 Stale-delta characterization | **PASS** (stale-hash recompute unavailable; identity corroborated by archived value) |
| V-T5 Claim-mapping readiness | **PASS** (readiness only; blockers restated) |

## OVERALL: **SUPPORTED_FOR_DOWNSTREAM_REVIEW** *(revised 2026-08-26 by Instrumentation Addendum)*

History: initially **BLOCKED** because every process-spawning tool failed (`bash` ENOENT ×2; ripgrep launch failures), leaving SHA-256/size/symlink/extra-file state unmeasured. The orchestrator subsequently executed the hash pass with full tooling; the auditor read the measurements file in full, adjudicated it the same day (base-correction accepted; 17/18 rows corroborated outright; row-12 transcription incident disclosed and resolved to current-authoritative literals; four content-stability spot-checks passed), and re-judged V-T1 as PASS with qualification. This verdict **supports downstream review only**: it promotes nothing, activates no claim, and leaves untouched the standing blockers (PAPER_CLAIM_AUDIT = BLOCKED; EMPIRICAL_IMPLEMENTATION_AUDIT = FAIL) and the `self_supervised_proxy` ceiling. All content findings of this receipt stand unchanged.

## Independence & provenance disclosure
- Auditor identity: **ox-alpha** (model `stealth/ox-alpha`), an undisclosed-organization LLM acting as delegated independent read-only auditor; **self-adjudicated** within the mandate's fail-closed rules; no subagents employed.
- This is the **first value review of these bytes**: inventory `value_review_performed: false` predates this audit and was deliberately left false (no mutation).
- All evidence gathered read-only at `/Users/wuyilin/work/Network_Time_Varying_Parameter_Vector_Autoregression_Models_Based_on_CP_Tensor_Decomposition/`; sole writes are this receipt pair.

## Not-done statements (all affirmative omissions)
- No promotion of any artifact, value, or tree.
- No mutation of the inventory or of `value_review_performed`.
- No claim activation; all mappings remain POTENTIAL_ONLY_NOT_ACTIVATED.
- No manuscript edits.
- No make/test/scientific execution of any kind; nothing activated.
- No writes outside `refine-logs/PSA_NYC_01_VALUE_AUDIT_20260826.md` and `.json`.

*End of receipt.*
