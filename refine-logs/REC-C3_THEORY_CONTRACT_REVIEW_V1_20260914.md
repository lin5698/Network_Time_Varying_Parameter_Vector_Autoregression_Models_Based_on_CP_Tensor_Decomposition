# C3 Theory-Implementation Contract Review V1

- Date: 2026-09-14
- Task: C3 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (theory vs implementation contract review)
- Scope: read-only mapping of theory contracts to implementations and tests, plus one minimal contract-verifying test addition to `tests/test_natcs_theory_contract.py`. No scientific formula or implementation was changed; no abstraction added; no defensive branch for impossible scenarios added.

## Contract-to-implementation-to-test mapping

| Theory contract | Formula location | Implementation location | Test location | Consistency |
| --- | --- | --- | --- | --- |
| Finite-basis query certificate (kernel-criterion / row-space inclusion) | `manuscript_src/natcs/methods_theory.md` (Theorem 1 block); `supp_note1_notation.md` (proof, Lemma 1 + rowwise inclusion at :91) | fixture-level constructions; certificate test reads the proof-audit JSON | `tests/test_natcs_finite_basis_certificate.mjs` (source + hash binding); `tests/test_natcs_theory_contract.py::test_finite_basis_two_hop_negative_and_full_rank_fixtures` (:12) | YES |
| Complete endpoint equivalence (`pi_G ∘ Ψ = id`) | `methods_theory.md` (Theorem 1); enforced by `tests/test_natcs_finite_basis_certificate.mjs:36-38` regex assertions on sources | N/A (representation theorem; no numeric implementation surface) | `tests/test_natcs_finite_basis_certificate.mjs` | YES |
| One-hop / two-hop family relation, strictness on domains containing P | `methods_theory.md`; `supp_note1_notation.md` | fixture algebra | `test_natcs_theory_contract.py::test_two_hop_family_is_strictly_larger_at_directed_cycle` (:29) | YES |
| Corollary 1 diagonal structured inverse + zero-row boundary (rowwise inverse `b_i = D_{i,-i} w0' / ‖w0‖²`) | `methods_theory.md:47` | diagnostic boundary in the ablation contract | `test_natcs_theory_contract.py::test_diagonal_structured_inverse_and_zero_row_boundary` (:50), `test_direct_only_is_identified_in_diagonal_zero_diagonal_class` (:73) | YES |
| Joint ridge Schur complement `{Z'M_{X,λ}Z + λI} b̂ = Z'M_{X,λ}Y` | `supp_note3_propagation.md:110-127` | `scripts/natcs_design_contract.py::equationwise_ridge_fit` (:15-64; design rows, `lhs = design.T@design + λI`, :56-57); consumed by `scripts/run_cp_empirical_pipeline.py::var_ols` (:639-645) | `test_natcs_theory_contract.py::test_joint_ridge_schur_complement_matches_full_solution` (:80), `test_ordinary_residualized_ridge_is_not_joint_ridge` (:104) | YES |
| Weak-separation diagnostic (joint Z, unpenalized residualization, same tolerance for rank/condition, rank deficiency always flags, 1e-8 flag / 1e-12 tolerance) | `supp_note3_propagation.md:129-135`; `methods_theory.md:55` | `scripts/natcs_weak_separation.py::residualized_network_stats` (:33-66; shared EPS=1e-12 scale, `weak_flag` at :65) | `test_natcs_theory_contract.py::test_rank_deficient_condition_number_is_infinite` (:169) … `test_rank_deficiency_always_triggers_weak_flag` (:200) — 6 tests | YES |
| Proposition 2 finite-horizon response transfer (per-h `h·L_S·K²·ΔC` bound; summed `L_S·K²·H(H+1)/2·ΔC`; common shock map) | `methods_theory.md:65-84`; `supp_note3_propagation.md:140-176` | bound used as reporting contract; companion algebra in estimator | `test_finite_telescoping_identity` (:134, telescoping identity), `test_spectral_companion_block_bound` (:124, lag-p top-row bound) | YES — **gap fixed this task**: the summed transfer bound with J and S had no direct test |
| Historical-topology exposure semantics (lagged exposure uses historical W, not report-date W) | `methods_theory.md` interpretation boundary | `scripts/natcs_design_contract.py::lagged_network_exposure` | `test_production_lagged_exposure_uses_historical_topology` (:149) | YES |

## Test addition (only change)

Added `test_finite_horizon_response_transfer_bound` to `tests/test_natcs_theory_contract.py` (after `test_spectral_companion_block_bound`). It verifies the existing Proposition 2 contract on random fixtures: with `J = I`, a normalized shock map `S` (so `L_S = ‖S‖₂ = 1`), and `K` taken as the maximum true/reconstructed companion power norm through `H`, the summed response error through `h = 1..H` stays within the declared constant `L_S·K²·H(H+1)/2·‖Ĉ−C‖₂`. This is a regression-style verification of an existing formula; it introduces no new abstraction, no defensive branch, and no assertion loosening. Test count: 16 → 17, all passing.

## Registered-conflict boundary (not decided here)

Two surfaces remain under the A3/science-lead decision and are marked BLOCKED-pending-A3, untouched by this review:

1. **RCEP rank 1 vs rank 2** — stale promoted tree shows `cp_rank 1` while quarantine candidates show `cp_rank 2` (`PAPER_CLAIM_AUDIT.md:30-31`); no rank choice is made here.
2. **Figure 4 network-share estimand vs manifests** — audited separately in task D2 (`refine-logs/REC-D2_FIG4_ESTIMAND_AUDIT_V1_20260914.md`); the formula itself was not edited by this task.

## Known limitation (recorded, not fixed)

`scripts/natcs_weak_separation.py` sets env vars and creates `tmp/` cache directories at import time (`:1-10`). This is an import-time side effect visible to any new importer; it is outside this task's mandate to restructure, and the production estimator path already imports only `natcs_design_contract`.

## Verification

- `python3 -m unittest tests.test_natcs_theory_contract`: 17/17 pass (0.007s).
- `git diff --check`: passed. Footprint: one test method added + this receipt.
