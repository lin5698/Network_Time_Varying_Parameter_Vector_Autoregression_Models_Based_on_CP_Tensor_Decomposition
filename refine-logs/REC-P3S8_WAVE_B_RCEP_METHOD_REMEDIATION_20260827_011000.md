# REC-P3S8 WAVE B RCEP METHODOLOGICAL REMEDIATION (2026-08-27)

## Authorization and exact inputs
- Author approved RCEP Wave B run.
- Runtime authorization raw sha256: `0b4caf9bea0480b43a2d8f7b35835eb5c812ff848094ac31076c1557c9c36cd3`.
- Helper checkout: HEAD d0e398b, clean, non-symlink; three source digests match the frozen trust manifest.
- RCEP inputs match the old authorization exactly: macro `27a3dbb7...`, bilateral `2dfa09cc...`.
- Implementation: run_cp_empirical_pipeline.py `111f2130...`; natcs_design_contract.py `45e14cb8...`.
- Args: window=40, p=2, n_boot=500, block_size=4, cp_inits=6, cp_max_iter=100, cp_tol=1e-6.
- Exit status 0; ridge lambda=0.01; CP rank=2.

## F2 bootstrap promoted-summary decision
- Evolving coefficient point = 0.0022967865167819556.
- 95% percentile interval = [-0.0010370999135430404, 0.0020326520698283287].
- Bootstrap median = 0.0007330858716416624.
- Point is outside the interval; `promoted_summary=bootstrap_median`, `interval_support=outside`, with explicit skew disclosure.
- Frozen bootstrap distribution and point bytes remain unchanged; only decision fields were added.
- Frozen/fixed coefficient, attenuation difference and frozen/evolving ratio points lie inside their intervals and retain `promoted_summary=point`.

## F3 absorption-variant result
- Primary pair/time rank check: `not_identified`, N=3570, TC_relief collinear with pair/time effects.
- Completed origin/destination AbsorbingLS variant: `not_identified`; TC_relief is fully absorbed by the declared effects.
- This is a confirmed data/design property, not an implementation omission. The correct report remains `not_identified` with both attempts recorded.
- `stability_exclusion_sensitivity.csv` base 8x8 values equal the frozen reference exactly; only `Variant` was added.

## Reproducibility and drift
- 23 reference artifacts byte-identical (core CSV/JSON/PNG scientific outputs).
- Expected additive differences: F2 summary CSV/JSON + selection_summary; F3 Variant column; new `run_metadata.json` and `stable_subsample_absorption_variant.json`.
- PDF byte differences are font-subsetting metadata; paired PNGs are byte-identical.
- Seed echo: root 20260328 and stage rules in run_metadata.json.
- Inventory frozen before value review: `4bf4af2aaee71b45ad23c673ea721f62ef1a3781c4857ed40c14cf961921ccbb`.

## Governance conclusion
F2 and F3 are methodologically closed: F2 uses the interval-supported bootstrap median with explicit skew disclosure; F3 remains honestly not_identified after both fixed-effect paths. No manuscript activation occurs under this receipt. Outputs next enter independent value audit, EIA/PCA re-adjudication, then an author RC-1 promotion decision.

---
Orchestrator-executed run, byte comparison, inventory freeze and hashing; review-only, fail-closed.
