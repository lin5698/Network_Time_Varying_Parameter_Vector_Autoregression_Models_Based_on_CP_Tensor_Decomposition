# C1 R006 Endpoint-Aware Evidence Boundary Memo V1

- Date: 2026-09-14
- Task: C1 of `docs/superpowers/plans/2026-09-13-long-term-delegation-plan.md` (promotion/blocking memo for the R006 endpoint-aware evidence boundary)
- Scope: read-only audit. No active claim, ledger row, or manuscript wording was changed; footprint is this file only. No experiment, no rebuild, no hash generation, no Git snapshot.

## 1. Frozen qualification numbers (controlling statement)

The frozen endpoint-aware qualification stands at:

- **CP (`anchor_split_cp3`, rank 3): 0/16 required cells** — threshold not met.
- **Tucker (`anchor_split_tucker333`, rank (3,3,3)): 6/16 required cells** — 6/8 matched-design cells, **0/8 native-design cells**.
- **Promoted candidate: none** (`promoted_candidate: null`).

These counts are frozen and currently triple-enforced:

1. `manuscript_src/natcs/r006c_endpoint_gate.json` (`evidence_status: frozen_v1_audited`, `scientific_outcome: fail`) with source SHA-256 binding to the raw run record.
2. `scripts/build_natcs_evidence.mjs:476-495` — the evidence builder hard-throws if the frozen summary no longer matches the audited manuscript claim, and `:497-511` re-verifies the raw source bytes and counts.
3. `scripts/check_natcs_final_gates.mjs:1881-1885` — the final gate re-parses the frozen record and fails if counts changed.

The detailed preserved audit is `refine-logs/R006C_AUDIT_20260715.md` (overall `WARN`; claim impact at `:99-100`: "CP endpoint-aware promotion: unsupported (`0/16`). Tucker endpoint-aware promotion: unsupported (`6/16`; native `0/8`)"). The root `EXPERIMENT_AUDIT.md` preserved checks confirm: "CP passes `0/16`; Tucker passes `6/16`; no candidate is promoted" (`:186-187`) and the promotion contract "requires one fixed candidate across both endpoints and all 16 cells" (`:213-215`).

**Tier separation.** These qualification counts belong to the N=20/T=200 simulation-only endpoint-aware gate (an evidence tier whose purpose is to bound inheritance). They are a separate evidence tier from the early positive controlled benchmark (N=15/N=30, 20 replications; the four active percentages 93.6/96.8/82.5/87.3 in the author decision sheet D-4). The active sources already enforce the separation: `results_validation.md:5` states the qualification "is not used to extend these gains", and the final gate (`check_natcs_final_gates.mjs:1859-1880`) fails any headline file that promotes the exact counts and any Methods text that states them. The two tiers must never be mixed: no wording may present the controlled gains as validated by, or extending to, the endpoint-aware qualification.

## 2. Ledger-row mapping for R006c/endpoint citations

| Ledger row | Current status | Allowed wording | Prohibited extension |
| --- | --- | --- | --- |
| C005 (`claim_evidence_ledger.csv:7`) | `supported qualification result: CP 0/16; Tucker 6/16; native Tucker 0/8; no promotion` | The qualification does not support inheriting the controlled gains as native held-out recovery; exact counts stay in Methods pointer + Supplementary Note 4 | No promotion to abstract/cover letter/main figure/headline; no endpoint-aware superiority, native recovery, or promoted-candidate claim |
| C002 (`:4`) | `supported only in stated benchmark; not confirmatory for native held-out recovery` | Controlled N=15/N=30 benchmark gain versus unrestricted rolling only | No generalisation to native endpoint recovery, unseen topology families, or broad estimator superiority |
| C003 (`:5`) | `supported as availability only` | Both separated reconstructions keep declared response endpoints defined | No equal-identification or successful-recovery inference |
| C011 (`:13`) | `supported as a conceptual and operational distinction` | Evaluability/identification/recovery/stability are distinct layers | No identification or recovery inference from endpoint availability alone |
| C017 (`:19`) | `quarantined outcome; integrity WARN; result-to-claim partial (high confidence); manuscript activation blocked` | Future-manuscript wording only, with named endpoint and exact scope | No ranking of projected graph-feature outputs with native estimators |
| C018 (`:20`) | same fence class as C017 | Future wording per family/scale/horizon including failures | No pooling of passing cells; no cross-family recovery claim |
| C019 (`:21`) | same fence class (medium confidence) | Future wording must report coverage/width/error/stability per cell | No empirical-calibration inference beyond H=4 |

## 3. Promotion gate contract and enforcement points

- **Contract** (ledger C005 scope and gate JSON `promotion_rule`): `cell_requires_every_recorded_endpoint_to_pass: true`; `candidate_requires_every_required_cell_to_pass: true`; `candidate_switching_across_cells: false`. Stress, weak-separation, collapsed, oracle and projected diagnostics cannot rescue a required-cell failure (preserved audit check H, `EXPERIMENT_AUDIT.md:211-215`).
- **Runtime enforcement**: `build_natcs_evidence.mjs:476-511` (throws on count drift or source mismatch), `check_natcs_final_gates.mjs:1859-1886` (headline/Methods/SI placement plus frozen-record check).
- **Test enforcement**: `tests/test_main_fig3_qualification_scope.mjs` — asserts the frozen counts (0/6/0), schema version, source SHA-256, per-cell endpoint structure, and that the gate function exists in the final gate script; `tests/test_figure3_python_backend.mjs:19` — forbids the qualification counts appearing in the Figure 3 visual narrative. Both verified passing: `node --test` → 2/2 pass on 2026-09-14.

## 4. Overstatement-risk findings (recorded, not fixed)

1. `manuscript_src/natcs/discussion.md:5` — "The numerical results establish the value of endpoint-preserving reconstruction in the experiment designed to test it." The sentence's scope qualifier ("in the experiment designed to test it") plus the following qualification sentence keeps it inside C002's boundary; flagged here only because "establish the value" is the strongest active phrasing adjacent to the R006c boundary. No change made: the final gate already asserts the claim-inheritance boundary in the same file (`results_validation.md:5`; enforced at `check_natcs_final_gates.mjs:1863-1865`).
2. Ledger C005's `review_status` embeds the exact counts in the shared CSV; any future edit of that status cell is a fence-adjacent edit and requires re-audit per `PAPER_CLAIM_AUDIT` release condition.
3. No wording found in scope that converts 6/16 matched into evidence of native capability; the 0/8 native column is consistently present wherever the 6/16 figure appears (SI table, gate JSON, audit records).

## Verification

- `node --test tests/test_main_fig3_qualification_scope.mjs tests/test_figure3_python_backend.mjs`: 2/2 pass.
- `git diff --check`: passed (footprint = this file only).
