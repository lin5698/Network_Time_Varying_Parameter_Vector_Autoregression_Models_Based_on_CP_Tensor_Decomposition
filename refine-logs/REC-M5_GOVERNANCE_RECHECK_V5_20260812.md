# REC-M5 Governance Recheck V5

Result: `CURRENT_PATCH_DETERMINISTIC_PASS_SOURCE_02_03_AUTHOR_DECISION_BLOCKED`

This receipt covers the current review-only patch after the author's AIN-RESULT,
AIN-ALS, AIN-TOPOLOGY, AIN-SOURCE-01 and AIN-SOURCE-04 confirmations. It does not
authorize manuscript application, formal-register mutation, scientific execution
or claim activation.

## Current deterministic checks

- Current-version deterministic harness: 84/84 PASS.
- Patch JSON and output hash: 2/2 PASS.
- Declared inputs: 11/11 PASS.
- Evidence bundles: 16/16 PASS.
- Protected baselines: 12/12 PASS.
- Pre-apply paragraph anchors: 18/18 PASS.
- Unit coverage: 26/26 PASS, unique=26, with valid edit-group references.
- Crosswalk and traceability shape: 3/3 PASS.
- G04 placeholder gate: PASS, zero double-brace tokens.
- Author worksheet source references: 3/3 PASS.
- Submitted author evidence: 7/7 PASS.
- Topology replication coverage: 4/4 PASS.
- G04 numeric recomputation from the released CSV: 4/4 PASS at tolerance 1e-12.
- M4 exact-allowlist validator: 247/247 PASS.

## Source-ownership audit

The canonical-source search was limited to Markdown under `manuscript_src/natcs/`
and `manuscript_src/natcs/controlled_benchmark_contract.json`. No canonical match
was identified for the spectral-radius wording or for a 50% top-exposure
attenuation. `supp_note3_propagation.md` contains generic signed-attenuation
language, but it does not bind a 50% top-exposure operation. Generated TeX remains
ineligible as a canonical ownership source.

Recommended author decisions, unless a canonical path can be supplied:

- AIN-SOURCE-02: mark the spectral-radius wording source unavailable.
- AIN-SOURCE-03: mark the 50% top-exposure attenuation source unavailable.

## Remaining gates

AIN-SOURCE-02 and AIN-SOURCE-03 remain unresolved until explicitly decided by the
author. After those decisions are bound, the current patch requires fresh
GPT-5.6-Luna/max scientific and editorial semantic review. M5-D manuscript
application and M5-F formal-register adjudication each require a separate later
authorization.

V2 through V4 are historical evidence for earlier patch states. This V5 receipt is
the current deterministic governance record.
