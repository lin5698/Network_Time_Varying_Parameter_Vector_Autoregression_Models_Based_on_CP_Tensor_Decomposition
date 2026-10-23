# D2 Figure 4 Network-Share Estimand Audit V1

- Date: 2026-09-14
- Task: D2 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (formula-to-code mapping for the Figure 4 network-share estimand)
- Scope: read-only audit; footprint is this file only. No figure, formula, manifest, caption or builder was changed; no rebuild was run; `output/` trees were used as read-only evidence.

## 1. Figure identification

Figure 4 is the NYC second-domain portability figure, built by `scripts/build_nyc_portability_figure.py` (output under `output/natcs_empirical_cp/nyc_taxi/figures/`). Its panel c is the GIRF decomposition panel with "point share" labels (`draw_girf`, `scripts/build_nyc_portability_figure.py:85-120`). The manuscript-facing text is `manuscript_src/natcs/results_generality.md:5` ("Figure 4c reports point-path shares …"), and the final gate pins this wording (`scripts/check_natcs_final_gates.mjs:1922`).

## 2. Four-surface estimand mapping

The estimand is the **absolute explicit-channel share**: `|network|₁ / max(|direct|₁ + |network|₁, 1e-12)`.

| Surface | Location | Statement | Consistent? |
| --- | --- | --- | --- |
| Formula (manuscript text) | `results_generality.md:5` (rendered in archive at `output/reviewer_archive/natcs_reviewer_archive/code/manuscript_src/natcs/results_generality.md:5`) | "bootstrap-draw means and medians under the same explicit-channel estimand"; medians 0.3715 (early) / 0.4810 (late) | YES — wording names the explicit-channel estimand without restating a conflicting formula |
| Implementation (figure builder) | `build_nyc_portability_figure.py:53-57` (`absolute_explicit_channel_share`) applied at :98 to `total/direct/network` fields of `girf_cp_point.json` | same formula | YES — arithmetic-verified below |
| Caption/manifest (evidence builder) | `scripts/build_natcs_evidence.mjs:966-970` (`absoluteExplicitChannelShare`), `:1028` (`network_share_estimand: "absolute_explicit_channel_share"`), `:218` (`network_share_formula: "sum(abs(network)) / (sum(abs(direct)) + sum(abs(network)))"`), reader-facing summary at `output/natcs_evidence/summary_metrics.json` | formula string exactly matches code | YES — arithmetic-verified: 0.7/(3.5+0.7) equals code output |
| Numeric agreement (early/late) | `output/natcs_evidence/summary_metrics.json` `nyc_validation.early_network_share.median = 0.3714912…`, `late = 0.4809697…`; manuscript placeholders `nyc_early_share_median = "0.3715"`, `nyc_late_share_median = "0.4810"` (`scripts/build_natcs_manuscript.mjs:101,105`) | 4-decimal rounding verified | YES — recomputed from raw draws: bootstrap medians at `2019-12-31` = 0.3715, `2021-12-31` = 0.4810 (500 draws each) |

Point-path vs bootstrap distinction holds: Figure 4c labels come from the **point** file (`girf_cp_point.json`: 0.2372 / 0.3246), while the text's 0.3715 / 0.4810 are **bootstrap medians** — exactly the split the sentence asserts ("Figure 4c reports point-path shares, while bootstrap-draw means and medians … Supplementary Table 5"). The two value sets are not conflated.

## 3. RCEP-side estimand and the legacy-helper discrepancy

- The RCEP switch figure (`scripts/build_rcep_operator_switch_figure.py:55-59,177`) uses the identical `absolute_explicit_channel_share` helper — same estimand across both domain figures (ledger C014's estimand-distinction boundary is unaffected; the pair-level regression versus aggregate response distinction is a different axis).
- `scripts/build_natcs_evidence.mjs:1285-1287,1353-1356` recomputes `girf_network_contribution` (RCEP, dates 2018-12-31/2022-12-31) via the same `networkShareFromDraws` → explicit-channel formula. Verified against raw bytes: recomputed mean at 2018-12-31 = 0.030943127896876192 vs stored 0.030943127896876196.
- **Legacy discrepancy (demoted, not in active chain):** `scripts/natcs_evidence.py:195-201,258-259` defines a differently-normalized block, `(‖total‖₁ − ‖direct‖₁)/max(‖total‖₁, 1e-12)`, over the same RCEP dates. This is the superseded claim-wording helper: the reviewer-archive builder **refuses to ship it** (`build_natcs_reviewer_archive.mjs:817-819` throws if `natcs_evidence.py` is present in the archive; `check_natcs_final_gates.mjs:637` checks the same), and the Makefile build chain (`Makefile:2-3`) never invokes it. It is quarantine-grade legacy code, not an active inconsistency.

## 4. Findings and conflict status

1. **`Supplementary Table 5` pointer is currently unverifiable in the built SI.** The SI builder (`scripts/build_natcs_supplementary_source_only.mjs`) numbers tables up to Supplementary Table 4 and, per its own header, must never read RCEP/NYC material; the built `supplementary_information.tex` (2026-09-05) contains no network-share table. The text pointer and the final-gate regex (`check_natcs_final_gates.mjs:1922`) both assert the pointer, but the referenced table does not exist in the current generated SI. Recorded as a **finding requiring the science-lead/build-lane decision** (either the NYC descriptive SI table was dropped in a demotion wave and the pointer is stale, or the table belongs to a future authorized build) — **BLOCKED-pending-A3/decision; not fixed here.**
2. `output/natcs_evidence/summary_metrics.json` (2026-09-05) coexists two blocks: the RCEP `girf_network_contribution` (legacy-dated block produced by the current builder) and `nyc_validation` share fields — both consistent with their own code paths; no numeric contradiction found between them.
3. The plan's registered "Figure 4 network-share estimand vs empirical run manifests" conflict was **not reproduced as a formula conflict** in the active chain: formula string, code, caption and manifest all agree. The residual conflict surface is finding 1 (missing referenced SI table), which should be attached to the A3 decision request.

## Verification

- Arithmetic re-computation performed from raw artifacts (RCEP mean share; NYC point and bootstrap shares, 500 draws) — all match stored/printed values.
- `node --test tests/test_natcs_release_gate.mjs`: 1/1 pass (post-audit sanity that the release gate still passes with this read-only footprint).
- `git diff --check`: passed.

## Correction: generated-output side effect

The `tests/test_natcs_release_gate.mjs` run spawned `build_natcs_evidence.mjs` and `build_natcs_manuscript.mjs` (`tests/test_natcs_release_gate.mjs:12-13`), regenerating `output/natcs_evidence/summary_metrics.json`, `output/submission_package/natcs_current/01_main_manuscript/…` and `submission_inventory.json` (mtimes 2026-09-14 ~10:20). No manuscript source, builder or manifest under version control was changed; this is generated-directory churn only, consistent with the known behavior recorded in `REC-P6_STATUS_RECONCILIATION_REBUILD_V1_20260831` ("test_natcs_release_gate.mjs invokes the evidence and manuscript builders and therefore recreates the submission package"). It was not a deliberate rebuild, and it did not complete the five-target chain (submission-materials and upload-freeze stages were not re-run; the pre-existing 2026-09-05 package drift documented in REC-A2 remains).
