# Paper Claim Audit — Re-adjudication

Audit date: 2026-08-26

Audit timezone basis: `Asia/Shanghai`

Status: **PASS**

Reason code: `rcep_nyc_value_audited_no_active_stale_citations`

Previous artifact (`PAPER_CLAIM_AUDIT.json`, audit 2026-07-19, verdict BLOCKED, reason `rcep_nyc_quarantines_unreviewed`) SHA-256: `3fe91793793a0b7bb9a6acc6b53793b735c5c5eb3667c27f7b59b7d92ff41d92`

## Scope and effect

This is a fail-closed re-adjudication of the standing BLOCKED verdict against current bytes and the completed 2026-08-26 review chain, under author decision `p3_stage3=授权复审+重建链`. PASS records ONLY that no active manuscript source currently binds to stale promoted or quarantined values, satisfying the paper-claim precondition for the authorized downstream rebuild chain. It does NOT authorize manuscript promotion or empirical claim activation, promotes nothing, and activates nothing. All hash digests are orchestrator-custody measurements from `tmp/p3_readjud_hash_pack_20260826.json` (disclosed; this adjudicator had no shell and could not recompute any digest).

## Why the three blockers no longer hold

**PCA-B003 (quarantines unreviewed) — DISCHARGED.** `PSA_RCEP_03_VALUE_AUDIT_20260826` and `PSA_NYC_01_VALUE_AUDIT_20260826` are the first completed independent value reviews of those bytes: both overall `SUPPORTED_FOR_DOWNSTREAM_REVIEW`, inventory integrity MATCH 36/36 (RCEP, V-T1 PASS_QUALIFIED_INSTRUMENT_MEDIATED) and 18/18 (NYC, PASS qualified; row-12 incident CLOSED as a transcription error by wave-record checks). `EMPIRICAL_IMPLEMENTATION_AUDIT.json` was re-adjudicated to PASS earlier today by a separate lane and was independently verified on disk by this adjudicator: `verdict=PASS`, `reason_code=rcep_nyc_value_audited_downstream_build_authorized`, remaining condition RC-1 present and NOT_GRANTED.

**PCA-B001 / PCA-B002 (stale-evidence precondition on `results_rcep.md` / `results_generality.md`) — DISCHARGED, no active binding.** Both files remain explicitly inactive audit-boundary drafts: their line-1 markers are intact, both contain zero numeric values, and both still state that the two audits remain controlling (their "not received independent value audit" clause is now conservatively outdated — the drift PTE-25/27 flagged). The evidence-build gate refuses while either marker exists (`scripts/natcs_utils.mjs`: both audit verdicts must be PASS AND markers absent, else `NCS_BUILD_REFUSED`). Ledger rows C006/C007/C008 remain self-fenced `blocked pending corrected rerun`; latent builder bindings sit behind `requireReleaseableNatcsEvidence(ROOT)` called first in `buildNatcsEvidence()`; on-disk residue in `output/natcs_evidence/summary_metrics.json` carries the stale literals but is generator output outside the active source graph.

## Stale-citation retest — reproduced first-hand

`PAPER_TO_EVIDENCE_AUDIT_V1_20260826` answered NO active citations of stale promoted values (39 entries: 35 OK / 4 fenced STALE_BOUND / 0 CRITICAL; BOUND_TO_QUARANTINE_CANDIDATE = 0). This adjudicator reproduced its key findings directly:

1. Inactive markers intact on both draft files; zero values present (full reads).
2. Four headline controlled percentages recomputed from `output/natcs_benchmarks/benchmark_summary.csv` at replications=20: N15 operator 624.6125531760274 → 40.274806941788114 = **93.55%** → printed 93.6 ✓; N30 operator 1371.693631145596 → 44.38880771061946 = **96.76%** → 96.8 ✓; N15 response 0.4103961733321335 → 0.07164372813883849 = **82.54%** → 82.5 ✓; N30 response 0.3971572031343755 → 0.05035310489419762 = **87.32%** → 87.3 ✓. Abstract uses build-time placeholders only.
3. Ledger C006/C007/C008 self-fenced verbatim (`blocked pending corrected rerun` + allowed-wording fences).
4. Stale promoted trees match every governance identifier identify-only: RCEP full_fit_loss `1.014484343302525` (= `1.0144843433`), cp_rank 1, no intercept_policy, degenerate ratio mean `-471724.7`; NYC full_fit_loss `0.7194454937345255` (= `0.7194454937`), rank-loss vector identical to receipts' stale arrays.
5. Quarantine candidate trees match every receipted value: RCEP cp_rank 2, full_fit_loss `0.6196736654708991`, stability_rate_cp `0.5277777777777778` (19/36), F1 remap literal present, F2 reproduced arithmetically (point `0.0022967865167819556` > p975 `0.0020326520698283287`, attenuation identity exact); NYC cp_rank 4, full_fit_loss `0.13612272962909133`, stability_rate_cp `0.6956521739130435` (48/69), double GIRF remap, helper_git_commit null.
6. Gate wiring verified: `build_natcs_evidence.mjs` L1474-1475 calls the release gate first; `natcs_utils.mjs` refuses on non-PASS verdicts and on either inactive marker; `EMPIRICAL_ROOT` points at the stale promoted tree so latent bindings cannot reach output under current wiring.
7. Legacy empirical supplement builder confirmed demoted 2026-07-26 with fail-closed import guard — the old EXPERIMENT_AUDIT scope finding does not reproduce.

Spot-check verdict: **ALL CONFIRMED — nine independent legs (PCA-SC-1..9), zero discrepancies.**

## Receipts relied on (SHA-256 from orchestrator pack)

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

Freshly flipped audits: `EMPIRICAL_IMPLEMENTATION_AUDIT.json` `d2650fdcf65cae54456f754e3409ae81f6df03e1ff658c21b352239b86ca15db`, `.md` `d4b2e5767ed4ed19e74bd1ba74a99ef300d71c4ddf0b0d393ee760847bdb35fd`.

## Open characterization flags — blocking activation, NOT build

Disposition class: `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD`. Each flag stays OPEN; it blocks manuscript use or claim activation of any fragment it touches until resolved or explicitly accepted by the author. None blocks the authorized downstream rebuild chain.

Carried forward verbatim from the wave record: `RCEP_F1_girf_date_substitution_undocumented`, `RCEP_F2_point_outside_bootstrap_CI`, `RCEP_F3_stable_dates_not_identified`, `NYC_stability_rate_semantics`, `NYC_girf_date_remap`, `NYC_origins_66_of_69`, `NYC_negative_late_g_net`, `no_rng_seed_recorded_both_trees`.

Detail verbatim from the receipts (see `PAPER_CLAIM_AUDIT.json` § flag_dispositions): RCEP F1 — girf date substitution 2022-12-31→2020-03-31 unexplained, BOTH dates present in outputs; RCEP F2 — headline evolving_coefficient point outside its own bootstrap percentile CI (0.00229679 > p975 0.00203265); RCEP F3 — stable-dates-only pair-level regression NOT identified (TC_relief collinear with pair/time effects; N=3570); NYC characterizations — stability_rate equals UNSTABLE share, GIRF remap rule undocumented, origins 66<69 uniformly in both trees, negative late-period g_net points, half_life pinned at cap H through 2020-05..2021-04, bootstrap means materially off point estimates in several months; no RNG seed recorded in either tree. F1's remap literal and F2's inequality were reproduced arithmetically today (PCA-SC-6); the rest are carried without merits re-adjudication.

All quarantine-candidate mappings remain POTENTIAL_ONLY_NOT_ACTIVATED.

## Remaining conditions

- **RC-1 — manuscript-promotion authorization: NOT_GRANTED.** Separate author decision required before any quarantined-run value, figure or claim fragment enters promotion. Not a build-gate blocker because zero active citations bind to quarantine or stale values.
- **RC-2 — empirical claim activation: REQUIRES_SEPARATE_AUTHORIZATION,** additionally blocked per-flag by OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD.
- **RC-3 — post-regeneration review with no open FATAL/CRITICAL issue:** carried from the original condition clause 3; rebuilt manuscript, reviewer archive, clean submission package and upload-freeze manifest remain behind the standing gates (including inactive-marker refusals still wired into the release gate).

This verdict must be re-audited if any boundary draft marker is removed, the evidence-build gate is rewired, or any ledger fence is edited.

## Honest limits of this PASS

- No first-party SHA-256 recomputation (no shell: bash spawn ENOENT initial + mandated retry; grep ripgrep-launch failure); every digest quoted from the orchestrator-custody pack — disclosed reliance, not cryptographic reproduction.
- Directory enumeration impossible: unlisted-file sweeps and exhaustive residue inventories remain UNMEASURED.
- PASS is scoped to the CURRENT active source set; it does not certify quarantined values for activation and promotes nothing.

## Historical context 2026-07-19 (unmodified)

The superseded BLOCKED artifact's sections are preserved unmodified in `PAPER_CLAIM_AUDIT.json` under `historical_context_2026_07_19_unmodified`: `scientific_execution_closure` (quarantined completion state, authorization template digest `25001859…`, refusal probes, screening-root construction pair), `verification_evidence` (CP contract/theory/candidate tests **85 passed / 0 failed**; screening-governance fixture tests **145 passed / 0 failed** in 24.557 s; security review rounds 3–5 traces and APPROVE verdicts), `separately_valid_theory` (Proposition 1, Corollary 1, unpenalized FWL/design statement, joint-ridge Schur complement, Proposition 2 — none expanded by this audit; frozen R006c remains CP 0/16, Tucker 6/16, native 0/8, no promotion), and `c3_static_boundary` (helper commit `d0e398b8…`, manifest `02b15147…`, API contract PASS_8_of_8, five import-time side-effect indicators, licence absent; permitted claim limited to static identity/import closure). Those sections describe the pre-wave state and do not describe the current verdict.

## Provenance disclosure

Adjudicator model ox-alpha (developing organization undisclosed); independent read-only re-adjudicator for P3 stage-3 step 2, self-adjudicated within mandate, ceiling `self_supervised_proxy`. Sole writes: this file and `PAPER_CLAIM_AUDIT.json`. No subagents; no make/test/git/scientific execution. Step 1's EIA flip was verified on disk, not trusted blindly. No activation performed.
