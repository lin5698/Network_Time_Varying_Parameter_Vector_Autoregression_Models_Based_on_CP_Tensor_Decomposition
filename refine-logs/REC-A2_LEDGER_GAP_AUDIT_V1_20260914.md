# A2 Claim-Evidence Ledger Gap Audit V1

- Date: 2026-09-14
- Task: A2 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (ledger gap audit; minimal evidence-backed revision only)
- Scope: read-only audit of `manuscript_src/natcs/claim_evidence_ledger.csv` with one minimal evidence-backed revision. No new numbers, no fence edits, no experiments, no rebuilds, no Git snapshot.
- Inputs: ledger CSV (21 rows, C001–C020 plus C001A), the A1 status map `refine-logs/REC-STATUS-RECONCILIATION_V2_20260914.md`, the C2 recovery receipt `refine-logs/REC-C2_E4_RECOVERY_CONDITIONS_V1_20260914.md`, the root audits, and the author decision sheet.

## Ledger structure finding

The ledger has 10 columns (`claim_id`, `manuscript_location`, `claim`, `evidence_source`, `experiment_or_artifact`, `scope`, `review_status`, `allowed_wording`, `prohibited_extension`, `review_goal`) and 21 rows. Every row carries all five required fields for the A2 acceptance test (evidence reference, scope, allowed wording, prohibited extension, review status). No structural gap exists.

## Row classification

| Rows | Class | Note |
| --- | --- | --- |
| C001, C001A, C002, C003, C004, C011, C012, C013, C014, C015, C016 | active, supported within stated scope | C002 scope-restricted to the controlled benchmark; C013 has "empirical values pending rerun" boundary |
| C005 | active, supported qualification result | frozen counts CP 0/16; Tucker 6/16; native Tucker 0/8; no promotion |
| C006, C007, C008, C010 | fenced | `blocked pending corrected rerun` (C006/C007/C008) and `blocked for submission` (C010); untouched per plan §2.3 |
| C009 | active, explicit exclusion | unsupported-and-excluded causal wording fence intact |
| C017, C018, C019, C020 | future-manuscript-only fences | `Future manuscript only; do not promote`; untouched |

## Evidence-reference verification (the actual gap audit)

All 13 file-path evidence references resolve to existing files, with one precision gap:

| Row | Reference | Resolves? | Action |
| --- | --- | --- | --- |
| C002 | `output/natcs_benchmarks/benchmark_summary.csv`; `benchmark_replications.csv` | yes | none (the "Supplementary Tables 2-3" labels resolve in the built reviewer archive, `output/reviewer_archive/natcs_reviewer_archive/README.md:35`; supp_note4 contains the corresponding benchmark tables as structured sections) |
| C005 | `manuscript_src/natcs/r006c_endpoint_gate.json`; three `output/high_impact_revision/r006c_endpoint_aware/*` files | yes (4/4) | none |
| C006 | two `output/natcs_empirical_cp/rcep/*bootstrap_summary.json` | yes | none (fenced row; status unchanged) |
| C007 | two `output/natcs_empirical_cp/nyc_taxi/*` files | yes | none (fenced row) |
| C015 | `scripts/run_cp_empirical_pipeline.py`; `tests/test_natcs_theory_contract.py` | yes | none |
| C016 | `refine-logs/NCS_FINITE_BASIS_QUERY_CERTIFICATE_PROOF_20260731.md` | yes | none |
| **C016** | `finite_basis_proof_audit_20260731.json` (unqualified) | **no as written** — actual location is `paper_rewriting_output/finite_basis_proof_audit_20260731.json`, consumed there by `tests/test_natcs_finite_basis_certificate.mjs:22` | **REVISED**: evidence_source cell now reads the repo-qualified path. Status cell (`supported as representation theory only`) untouched, so the ledger-consumer assertion at `tests/test_natcs_finite_basis_certificate.mjs:47` is unaffected. |
| C017–C020 | `refine-logs/NCS_E3_MINIMUM_EVIDENCE_PROTOCOL.md`; frozen E4-r3 records; result-to-claim traces | yes | none (fenced rows) |

Fence markers verified intact after the edit: three `blocked pending corrected rerun` cells (C006/C007/C008) unchanged; no status cell touched. Therefore the `PAPER_CLAIM_AUDIT` re-audit trigger (edit of a ledger fence) is not tripped; still, per that verdict's own condition, any future fence edit requires re-audit.

## Review-status consistency spot checks

- C005 allowed wording matches the frozen qualification boundary recorded in the A1 map.
- C002 prohibited extension (no native recovery / no broad superiority) matches the plan §1 boundary sentence.
- C013 "empirical values pending rerun" is consistent with C006–C008 fencing.
- No row claims anything beyond its `review_status`; no new numbers were introduced.

## Non-goal findings (recorded, not fixed)

1. The ledger is consumed by exactly one test (`tests/test_natcs_finite_basis_certificate.mjs:21`); no build gate parses it. That is a WS-F observation, not an A2 change.
2. Pre-existing final-gate state is currently `FAIL` (167 passes / 63 errors), all errors being missing files under `output/submission_package/natcs_current/03_submission_materials/` — a stale generated package from 2026-09-04/05, after the 2026-09-03 P6 baseline receipts recorded 27 entries. A controlled A/B re-run (ledger cell reverted vs edited) produced byte-identical gate output (167/63, zero ledger-related errors), proving the failure is pre-existing package drift unrelated to this task. Per plan §6 stop conditions, repair belongs to a build task (E1-class), not to this ledger audit; recorded as an open blocker for the E-lane.
3. `manuscript_src/natcs/claim_evidence_ledger.csv` line 23 is an empty trailing line; left as-is (formatting convention).

## Verification

- `node scripts/check_natcs_final_gates.mjs`: pre-existing FAIL unchanged by this task (see finding 2; A/B-verified unrelated to the ledger edit).
- `node scripts/audit_natcs_release_safety.mjs --check`: 0 blockers, 0 warnings (397 files seen).
- `node --test tests/test_natcs_finite_basis_certificate.mjs`: 1/1 pass (ledger consumer).
- `git diff --check`: passed.

## Working-tree provenance note

`git diff` on the ledger shows 5 rows changed, not 1. Four of those changes (C001A, C005, C013, C015) are **pre-existing uncommitted user modifications** in the evidence_source column (adding `tests/test_natcs_theory_contract.py` references and an additional r006c path); they were present before this task and were preserved untouched. Only the C016 evidence_source cell change (unqualified → repo-qualified `paper_rewriting_output/finite_basis_proof_audit_20260731.json`) is this task's edit. No user change was reverted, and the task's own footprint is the single C016 cell plus this receipt.
