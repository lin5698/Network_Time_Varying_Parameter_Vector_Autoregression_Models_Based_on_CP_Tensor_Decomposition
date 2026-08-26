# R006f Construction-Only Audit

**Date:** 2026-07-16  
**Auditor:** Codex, direct independent read-only reconstruction  
**Scope:** R006f construction artifact only; no seed, paired-world, estimator, or outcome execution  
**Verdict:** `PASS` for the construction artifact, more precisely the artifact's frozen status `CONSTRUCTION_PASS`

## Authorization boundary

The approved dual-track design says that it authorizes no formal outcome generation (`docs/superpowers/specs/2026-07-16-r006e-r006f-dual-track-design.md:4`). The frozen protocol authorizes construction and construction-only tests and explicitly withholds formal paired-outcome generation, a formal experimental `PASS`, and result-to-claim work (`refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md:4,16,171`). This audit therefore did not call `generate_paired_worlds`, `run_pair`, any seed, or any outcome runner. **Formal R006f outcomes remain unauthorized.** The verdict above is not a formal experimental result.

The audit independently restated the DCT and matrix formulas in a separate in-memory calculation. It did not import the project construction or abstention modules for the numerical reconstruction and did not write a recomputed artifact. The only file created by the audit is this report.

## Artifact integrity and provenance

Artifact inspected: `output/high_impact_revision/r006f_exact_support_abstention/construction_gate_preoutcome.json`.

- Declared canonical body SHA-256: `875cf969c7c591c11bd45893f4f00c35e8585f0508ea086ffeed146815f4eea5`.
- Independently recomputed canonical body SHA-256, using sorted keys, compact separators, UTF-8, and excluding `artifact_sha256`: `875cf969c7c591c11bd45893f4f00c35e8585f0508ea086ffeed146815f4eea5`. Exact match.
- Raw artifact-file SHA-256, including its trailing newline: `04656168790710d4e9a537cf54332bc4399b74c2d34073d45ca0537686d0eeef`.
- Full canonical JSON SHA-256, including `artifact_sha256`: `9eb88b7d8704cfbe3e26edfd653a80a2dfd22bf5a3bd527280eca4f3c9ce08f8`.
- Canonical provenance-object SHA-256: `c9502269181c69daf1ab225ae8a089f4411291f984db69595eb1e6ec1e4b91b3`.

Every declared source digest equals the current file digest:

| Frozen input | SHA-256 | Match |
| --- | --- | --- |
| Protocol | `652a41dedac9d7629b944c08b57edb526318b0d3ec8d243b9b71599b5c83af9f` | yes |
| Approved dual-track design | `8f9aa2e6284fb619dc08473212b00ebefc2db8456761b5be9936e35bad1fe9c9` | yes |
| Exact-design code | `c0c1d2f20c09ad0f40d72198f8c8549be653cc6853a71a14fd9a884d2d6c1128` | yes |
| Exact-abstention code | `500ac7d20f413bae27c9c7858b6f49434ee1edacc1b8e35334637a5dbb89308d` | yes |
| Construction-gate code | `9c73be978d21f06fa25d64db5236266c8397ecfc878f6ae1db2de192ec9763e6` | yes |
| Canonical NumPy configuration | `8fbdddb9fa0748d2a5efc93c4dfc28ae1ad97d785989e597d1a49d6aa0d48deb` | yes |

The artifact has exactly the seven top-level schema keys declared by the gate: `artifact_sha256`, `checks`, `contract`, `provenance`, `run_type`, `schema_version`, and `status`. The nested key structure also matches the gate schema. Values are `schema_version=1`, `run_type="construction_only"`, and `status="CONSTRUCTION_PASS"`. The contract dimensions are exactly `N=6`, rank `r=2`, and `T=96`, matching the approved design and frozen protocol.

## Independent numerical reconstruction

The reconstruction used the prescribed orthonormal DCT-II bases, `U=[q1,q2]`, `u_perp=q3`, `v1=q4`, `v2=q5`, the unrenormalized topology formulas, FWL residualization by an independent least-squares call, and a fresh SVD. Exact scales were `epsilon_strong=0.4754134895549027` and `epsilon_star=0.13397459621556135`.

| Check | Strong (`1.0`) | Weak (`0.25`) | Gate requirement |
| --- | ---: | ---: | --- |
| Training-topology minimum entry | `0.125` | `0.15625` | at least `0` |
| Training maximum row-sum error | `2.220446049250313e-16` | `2.220446049250313e-16` | at most `1e-12` |
| Supported-query topology minimum entry | `0.125` | `0.125` | at least `0` |
| Supported-query maximum row-sum error | `2.220446049250313e-16` | `2.220446049250313e-16` | at most `1e-12` |
| Unsupported-query topology minimum entry | `0.1361645496846301` | `0.1361645496846301` | at least `0` |
| Unsupported-query maximum row-sum error | `0.0` | `0.0` | at most `1e-12` |
| `rank(Z_tilde)` | `2` | `2` | exactly `2` |
| `||P_SVD-UU'||_F`, independent | `1.5257521659920596e-15` | `6.848340275076281e-15` | at most `1e-10` |
| `chi_supported`, independent | `8.056024595699693e-16` | `3.2650524758254096e-15` | at most `1e-10` |
| `chi_unsupported`, independent | `1.0` | `1.0` | at least `0.9999999999` |
| Retained singular values | `[0.47541348955490276, 0.4754134895549025]` | `[0.11885337238872568, 0.11885337238872565]` | rank two |
| `tau` | `0.009508269791098055` | `0.0023770674477745137` | `max(1e-12,s_max/50)` |

The artifact records projector errors `1.5217866018691425e-15` and `6.828231229767587e-15`, supported chi values `7.791746249224777e-16` and `3.25409048371478e-15`, and unsupported chi values `0.9999999999999998` and `1.0`. The independent values differ only at ordinary last-bit SVD/linear-algebra scale and lead to the same exact classifications by a margin of more than four orders of magnitude relative to the frozen tolerances.

The observed weak-to-strong retained-singular ratios are exactly `[0.24999999999999997, 0.25000000000000006]`; maximum absolute error from `0.25` is `5.551115123125783e-17`. Thus the weak excitation singular values are one quarter of the strong values.

The unsupported analytic gap is `0.5 * epsilon_star * outer(q0,v2)`. Its independently recomputed Frobenius norm is `0.06698729810778066`, versus the analytic scalar norm `0.06698729810778067`; absolute error is `1.3877787807814457e-17`. Its maximum absolute matrix entry is `0.015251058491018276`. This is nonzero and agrees exactly with the artifact values at the stored precision.

## Randomness and output isolation

The construction entry path calls only `build_exact_panel` for scales `1.0` and `0.25` (`scripts/experiments/r006f_construction_gate.py:407-410`). Static AST inspection finds no random call, `generate_paired_worlds` call, or `run_pair` call anywhere in the construction-gate module. The sole RNG construction in the inspected implementation is inside the separate `generate_paired_worlds` function at `scripts/experiments/r006f_exact_design.py:216-225`; it is not reachable from the construction gate. Formal seed IDs are serialized as contract metadata only. No formal RNG was generated during this audit.

Filesystem enumeration found exactly one R006f output directory and exactly one file beneath it: the inspected `construction_gate_preoutcome.json`. The repeat directory is absent. No paired-result, per-seed, estimator-result, summary-result, or other formal outcome artifact exists. The JSON key audit likewise found construction checks and frozen seed metadata only, with no outcome rows or recovery metrics.

## Findings, verdict, and limitations

No integrity, schema, provenance, algebra, topology, rank, projector, query-classification, excitation-ratio, analytic-gap, RNG-use, or output-isolation finding was identified. The artifact is internally canonical, current with respect to every frozen source hash, and passes all construction-only thresholds. Verdict: `CONSTRUCTION_PASS` confirmed.

Limitations: this was deliberately not a formal outcome audit. It did not instantiate paired worlds, test observed-data identity under any seed, fit FWL OLS, evaluate certificate behavior over 50 seeds, test supported-query error scaling, check the silent-estimator half-gap condition, or validate outcome decomposition residuals. Those are later formal gates and remain untested here because their execution is not authorized. Independence here means that the construction formulas and numerical checks were restated and recomputed separately from the artifact-producing code path.
