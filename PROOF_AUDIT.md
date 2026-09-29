# Proof Audit

Audit date: 2026-07-31

## Scoped verdict: PASS

The active source-only mathematical claims pass independent review on the exact hashes below. This receipt covers representation, design and finite-horizon transfer results. It does not validate an empirical application, estimator consistency, CP rank recovery, uncertainty calibration or manuscript release.

| File | SHA-256 |
| --- | --- |
| `manuscript_src/natcs/methods_theory.md` | `1e81d2d355dbf3846690dba232c4201ce3ae4775b043bc7f3ee7409afea45766` |
| `manuscript_src/natcs/supp_note1_notation.md` | `a97ba5e41923d07017d01779111ec3bcab5fead1a23a99dd50228c95a7bfe5b4` |
| `manuscript_src/natcs/supp_note3_propagation.md` | `66f6f6d0dd2502c6f7f0260f5552840da5a62bd2330d1e3ec0fc34691e848b7f` |

## Claims reviewed

| Proof branch | Verdict | Exact scope |
| --- | --- | --- |
| Finite-basis query certificate | PASS | Row-separable finite topology bases; rowwise kernel inclusion is equivalent to reversed row-space inclusion. |
| Complete endpoint equivalence | PASS | The endpoint depends on the queried operator tuple alone and retains it through `pi_G o Psi = id`. |
| One-hop and two-hop family relation | PASS | Strict inclusion holds on every declared topology domain containing the directed three-cycle `P`; no two-hop recovery claim follows. |
| Unrestricted and structured one-hop boundaries | PASS | Proposition 1 applies to unrestricted blocks; Corollary 1 gives the diagonal zero-row condition and rowwise inverse. |
| Design and ridge algebra | PASS | Singular residualized Gram gives an absorbed network direction; the positive ridge Hessian gives uniqueness in exact arithmetic. |
| Finite-horizon transfer | PASS | The deterministic bound is conditional on a common shock map and bounded companion powers through finite `H`. |

## Review disposition

The first complete review found two local issues: an invalid `eta=0` implication and an omitted endpoint-dependence premise. Both were repaired. A blind follow-up confirmed the critical claims and requested two cosmetic clarifications. The current sources now fix `H` as a finite integer with `H>=1` and describe ridge uniqueness as uniqueness in exact arithmetic. Exact-hash verification found no remaining mathematical issue.

## Controlling boundary

This mathematical PASS is non-controlling for release. `PAPER_CLAIM_AUDIT` remains `BLOCKED`, and `EMPIRICAL_IMPLEMENTATION_AUDIT` remains `FAIL`. No R006e/R006f outcome, application result, downstream build or manuscript promotion is authorized by this receipt.
