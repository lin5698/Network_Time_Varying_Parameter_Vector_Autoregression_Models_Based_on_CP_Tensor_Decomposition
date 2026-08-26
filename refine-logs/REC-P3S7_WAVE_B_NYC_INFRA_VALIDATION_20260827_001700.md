# REC-P3S7 WAVE B NYC INFRASTRUCTURE VALIDATION (2026-08-27)

## Authorization and execution

- Author approved NYC infrastructure validation after Wave B code implementation.
- Runtime authorization: `SCIENTIFIC_EXECUTION_AUTHORIZATION_WAVE_B_NYC_20260826.json`
  raw sha256 `a5dcdfdec9c02d059c79b519ae11caaeffe1b2be6523533f54d11e63a99626c7`.
- Implementation locked at run time: run_cp_empirical_pipeline.py `111f2130...`,
  natcs_design_contract.py `45e14cb8...`.
- Args: window=40, p=2, n_boot=500, block_size=4, cp_inits=6,
  cp_max_iter=100, cp_tol=1e-6.
- Input: NYC vars repo commit 7e63ba9; all ten 2012-2021 npz files present;
  pinned 2012/2013 sha256 values verified before run.
- Exit status: 0. Selected ridge lambda=0.01 and CP rank=4 (same as frozen reference).

## Output verification

New isolated run: `output/natcs_empirical_cp_authorized_runs/wave-b-nyc-20260826-230000-01/nyc_taxi/`.
Frozen reference: `output/natcs_empirical_cp_authorized_runs/psa-20260719-nyc-01/nyc_taxi/`.

- 13/13 non-PDF reference artifacts byte-identical: every CSV/JSON scientific output,
  all PNG figures, derived panel and acquisition record. No new empirical value was produced.
- 5/5 PDFs differ only at byte level. The run log records matplotlib/fontTools glyph
  subsetting. Their paired PNG renderings are byte-identical; PDF byte instability is a
  rendering-metadata/font-subset issue, not a value drift.
- One additive artifact: run_metadata.json. It echoes seed_root=20260328, stage seed
  rules, implementation digests, input identity, argv and authorization ID.
- Frozen run-tree inventory digest before value review: `41eb3fa8a203f6f3dac117edf874ea7a20817fcc3400c85caa28b69bb30b3314`.

## Scope conclusion

NYC validation proves the new authorization gate, migrated dataset binding, isolated output
namespace and seed echo work end to end. It also proves numeric/JSON/CSV reproducibility against
the frozen NYC reference. The F2 bootstrap promoted-summary logic and F3 absorption variant are
RCEP-branch methods; they remain unexecuted until the digest-pinned RCEP helper checkout is
restored. No quarantined result is activated by this receipt.

## Helper-origin reconnaissance

Repository records preserve the helper commit and three file digests but contain no origin URL.
Recovery needs an author-supplied checkout/archive or git origin. The trust manifest will reject
any candidate whose commit or file digest differs.

---
Orchestrator-executed run, inventory freeze, byte comparison and receipt hashing; three delegated
analysis lanes failed before write and left no residue (disclosed). Review-only, fail-closed.
