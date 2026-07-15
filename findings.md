# Research Findings

## 2026-07-15: R005/R006 Result-to-Claim Gate

### Intended claim

Block-preserving low-rank reconstruction improves topology-query recovery under controllable separation, approximate rank and stability conditions, beyond unrestricted local estimation and strong temporal-only smoothing.

### Experiments

- R005: exact-rank separation x stability pilot, N=20, T=200, 10 paired seeds, 360 method rows.
- R006: calibrated approximate-rank pilot, a3 in {0, 0.10, 0.25, 0.50}, rho in {0.80, 0.95}, 10 paired seeds, 720 method rows.
- Baselines: local, spline-df10 and validation-selected fused-TV. Low-rank diagnostics include CP/Tucker ranks 2, 3 and 5.

### Verdict

- `claim_supported`: **partial**
- `confidence`: **high**
- `integrity_status`: **unavailable at the R006 verdict time**; that verdict was provisional. The later R006b experiment has its own completed audit below and does not retroactively certify R005/R006.

### Supported

In the tested smooth, fixed-subspace design, block-preserving rank-3 reconstruction improves finite-horizon topology-query response estimation when rank-3 approximation error is at most 0.25 in the rho=0.95 scaling regime. CP-3 and Tucker-333 improve 22-25% over both local and fused-TV, win on all 10 paired seeds and pass the frozen absolute operator and zero-operator response gates. Tucker is generally equal to or better than CP.

### Not supported

- The frozen R006 overall gate fails.
- At rho=0.80, CP/Tucker operator errors remain above 1 even though response errors improve 43-46% relative to local and fused-TV.
- Exact-rank rho=0.80 fails the same absolute operator gate, so this failure is not caused by approximate-rank tail energy.
- Common scaling changes query norm and state scale together with spectral radius. Mean query Frobenius norm is 1.135 at rho=0.80 and 1.347 at rho=0.95; state RMS is 0.265 and 0.309, respectively. Stability and effective signal strength are therefore confounded.
- No evidence supports CP-specific superiority, a general stability boundary or a globally monotone separation effect.
- Rank 5 does not rescue the failed cells and cannot replace the prespecified rank-3 gate.

### Working claim

In the tested smooth, fixed-subspace design, block-preserving rank-3 reconstruction, particularly Tucker, improves finite-horizon topology-query response estimation over unrestricted local estimation and validation-selected temporal smoothing when rank-3 approximation error is at most 0.25; absolute operator recovery is demonstrated only in the rho=0.95 scaling regime.

### Routing

1. Retain R006 as `FAIL`; do not promote it to manuscript-facing main evidence.
2. Run a preregistered R006b design that varies spectral radius while holding query Frobenius norm and estimator scaling fixed and explicitly auditing state RMS/SNR.
3. Run R007 smooth/abrupt x fixed/rotating paths only after R006b resolves the scale confound.
4. Re-run result-to-claim before N=50/100 expansion or manuscript revision.

The full independent reviewer trace is stored under `.aris/traces/result-to-claim/2026-07-15_run01/`.

## 2026-07-15: R006b Deconfounded Result-to-Claim Gate

### Experiment

- Fixed `||M_t(W_ref)||_F=1.20` at `rho in {0.80, 0.95}` with exact separated identity `A_t+B_tW_ref=M_t(W_ref)`.
- Matched-excitation and native-VAR layers; `a3 in {0, 0.10, 0.25, 0.50}`; 10 paired seeds; 800 method rows.
- Local, spline-df10, causally validation-selected fused-TV, CP-3 and Tucker-333.
- Corrected full run and duplicate both retain `FAIL`; all 800 non-runtime rows reproduce exactly.

### Verdict

- `claim_supported`: **partial**
- `confidence`: **high**
- `integrity_status`: **pass** after causal fused-selection correction and independent re-audit

### Supported

With query norm, matched design covariance and adaptive ridge scale controlled, operator recovery is effectively unchanged across the two stability levels: the paired Tucker operator-error ratio `rho=0.95 / rho=0.80` is `1.003` at both required a3 levels. Finite-horizon response transfer is nevertheless amplified by `1.476` and `1.494`. This supports a controlled stability-to-response amplification diagnostic, not a general stability boundary.

In the native VAR layer, Tucker reduces median operator error from roughly `2.43-2.53` for local estimation to `1.09-1.15` and reduces response error from roughly `0.96-1.00` to `0.35-0.51`. Absolute recovery still fails: Tucker's zero-operator ratios remain about `1.03-1.06`.

### Contradicted or unsupported

- All four matched required cells fail the frozen method gate.
- Tucker is `104-143%` worse than local and fused-TV in paired median raw response error and records `0/10` joint wins in every required cell.
- Tucker's matched query-operator error is about `0.966-0.970`, compared with about `0.56` for local estimation.
- CP-specific superiority, broad low-rank superiority and a general stability boundary remain unsupported.
- R006's earlier regime-specific method claim is not robust to the deconfounded matched-excitation design and cannot be promoted as main evidence.

### Mechanism

Tucker does denoise the coefficient blocks: matched median block error falls from about `6.94` for local estimation to `2.86`. Under weak block separation, however, the local query estimate benefits from cancellation between block errors in `A+B W_ref`. Unconstrained low-rank reconstruction changes that cancellation and shrinks the query estimate toward zero, worsening the target even while improving block error. The target-aware loss and the block-recovery loss therefore cannot be treated as interchangeable.

### Integrity correction

The first audit found that fused-TV candidates were smoothed over the full local path before validation scoring. The corrected implementation fits candidate smoothers only on the pre-evaluation prefix, stores `retrospective_prediction_rmse`, and writes protocol/addendum/code hashes. Original outputs remain untouched. Corrected results are numerically unchanged because all fused cells select penalty `1.0`.

### Revised working claim

With query norm and matched excitation controlled, proximity to the stability boundary leaves operator-estimation error essentially unchanged but amplifies finite-horizon response-transfer error by about `1.48-1.49`. Tucker block reconstruction improves relative errors in the tested native VAR design but does not achieve absolute query recovery and can be harmful when topology-query accuracy depends on cancellation between coefficient blocks.

### Routing

1. Retain R006 and R006b as `FAIL`; do not modify their thresholds or promote passing subgates into method superiority.
2. Run R006c: direct-query and cancellation-preserving low-rank estimators, including an oracle constrained comparator and collapsed-map ablation.
3. Run R007 smooth/abrupt x fixed/rotating paths only after R006c identifies an endpoint-aware estimator worth confirming.
4. Keep N=50/100 expansion and manuscript revision frozen until the next result-to-claim gate.

The independent reviewer trace is stored under `.aris/traces/result-to-claim/2026-07-15_run02/`.

## 2026-07-15: R006c Endpoint-Aware Result-to-Claim Gate

### Experiment

- Anchor parameterization `M(W)=M_ref+B(W-W_ref)` with held-out same-family
  `W_alt_main` and independent stress endpoint `W_alt_stress`.
- Matched-excitation and native-VAR layers; `rho in {0.80, 0.95}`;
  `a3 in {0.10, 0.25}`; `eta in {0.02, 0.15, 0.45}`; 10 paired seeds.
- Nine frozen methods and two eligible fixed candidates:
  `anchor_split_cp3` and `anchor_split_tucker333`.
- Corrected full and repeat runs each contain 2,160 unique rows with zero
  failures and zero non-runtime differences.

### Verdict

- `claim_supported`: **no**
- `confidence`: **high**
- `integrity_status`: **pass** after chronological-validation correction,
  transitive provenance expansion and independent CSV recomputation

### Supported

The endpoint-aware construction is feasible, reproducible and leakage-free.
All construction gates pass, eligible methods make both required endpoints
available, and the corrected runs have no numerical failures. In the
simulation-only matched-excitation layer, fixed `anchor_split_tucker333` passes
both endpoints and the worst-endpoint gate in `6/8` required cells. This is a
limited conditional diagnostic, not a promotion result.

### Contradicted or unsupported

- No fixed candidate passes all 16 required cells.
- `anchor_split_cp3` passes `0/16`.
- `anchor_split_tucker333` passes `6/16`, with `0/8` native cells.
- Tucker's two matched failures are at `rho=0.95, eta=0.45`; at `W_alt_main`,
  improvement over local/fused-TV is only about `9.2-9.5%`, below the frozen
  10% threshold, and joint wins are `0.7-0.8`.
- Every native cell fails both required endpoint gates. Operator-error medians
  exceed one, and Tucker generally underperforms `block_tucker333` at
  `W_alt_main` by about `3.7-61.8%`.
- Improvement over local and fused-TV alone does not establish improvement
  over all three frozen comparators.
- Collapsed, oracle-B, stress, `eta=0.02` and projected-sensitivity rows are
  mechanism or sensitivity diagnostics and cannot rescue promotion.

### Revised claim boundary

In the frozen `N=20, T=200` simulation, split Tucker anchoring preserves
reference and same-family held-out endpoint recovery in `6/8`
matched-excitation cells, but fails both required endpoints in all native-VAR
cells; neither fixed anchor candidate provides robust topology-switch
superiority across the operating region.

### Routing

1. Record R006c as a valid negative result and reject endpoint-aware method
   promotion.
2. Keep the manuscript, R007 and N=50/100 expansion frozen.
3. Before further method screening, preregister a new estimator question that
   directly addresses native endogenous-design failure, for example joint
   regularization of the anchor operator and topology slope.
4. Retain the unchanged fixed-candidate, dual-endpoint, all-cell gate; do not
   reuse diagnostic rows or cellwise method switching.

The independent reviewer trace is stored under
`.aris/traces/result-to-claim/2026-07-15_run03/`.
