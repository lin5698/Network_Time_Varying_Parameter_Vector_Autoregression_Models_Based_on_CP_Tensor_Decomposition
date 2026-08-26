# REC-M3 V1-026 / CAL-E01:75 Patch Proposal

## Audit status

This is a read-only text and contract audit. No manuscript, register, E4-r3, authorization, or git state was modified.

- Register item: `V1-026`, item index `75`, register key `CAL-E01:75`
- Register action: `DIRECT_TEXT_REVISION`; priority `P0`; current response `PARTIAL`
- M2C primary artifact: `cal-e01-75-raw-audit`; verdict `PASS`; scientific execution `NOT_RUN`; claim activation `BLOCKED`
- M2C boundary: raw comparator ledger, raw paired differences, and status inventory; `descriptive_audit_only`
- Output companion: `refine-logs/REC-M3_V1_026_CLAIM_LEDGER_20260811.json`

The M2C primary E01 output is a separate frozen E4 comparator audit. Its comparator names must not be silently mapped onto the active manuscript rows `CP-network`, `Tucker-network`, or `Unrestricted local rolling`.

## Comparator audit

The frozen registry declares one native full-operator/finite-horizon-response interface for three methods. The recovery grid is `family1|family2` x `N=20|N=50` x `in_family_interpolation|cross_generator` x `H=4|H=12`, giving 16 method cells per comparator. Each method cell has 20 seeds and 48 target dates, or 960 endpoint records.

| Comparator | Frozen role | Declared endpoint and interface | Coverage | Status and failure handling | Matched-target boundary | Scientific ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| `local_structured` | `native_local_structured` | `full_operator_and_finite_horizon_response`; `fit(training_histories, observed_training_topologies, frozen_hyperparameters)` and `evaluate(fitted_state, W_q, H_max)`; windows `8, 12, 16` | 16 cells; 20 seeds x 48 target dates per cell; 960 records per cell; 15,360 method records | All 15,360 recovery records are `AVAILABLE`; `NONCONVERGED`, `NONFINITE`, `OUTSIDE_TARGET`, and `UNSTABLE` are retained as explicit bins and observed at zero; no retained failure records | Pairwise raw differences are valid only within the same family, scale, query class, horizon, seed, and target date, and only for the frozen fixed-rank-basis versus local pair cells | Descriptive role, endpoint, coverage, and status audit only. No new CI, ranking, superiority, native-held-out claim, or activation | 
| `causal_temporal_smoother` | `causal_temporal_structured` | Same native full-operator/finite-horizon-response interface; alphas `0.25, 0.55, 0.85` | 16 cells; 20 seeds x 48 target dates per cell; 960 records per cell; 15,360 method records | All 15,360 recovery records are `AVAILABLE`; all failure/non-finite/outside-target/unstable bins are retained and zero; no retained failure records | Pairwise raw differences are valid only within the same frozen cell and common endpoint key, for the fixed-rank-basis versus causal pair cells | Descriptive role, endpoint, coverage, and status audit only. No new CI, ranking, superiority, native-held-out claim, or activation | 
| `fixed_rank_basis` | `fixed_low_rank_or_basis` | Same native full-operator/finite-horizon-response interface; ranks `1, 2, 3` | 16 cells; 20 seeds x 48 target dates per cell; 960 records per cell; 15,360 method records | All 15,360 recovery records are `AVAILABLE`; all failure/non-finite/outside-target/unstable bins are retained and zero; no retained failure records | It is the candidate in the frozen paired arrays against `local_structured` and `causal_temporal_smoother`; comparisons remain cell- and endpoint-key matched | Descriptive role, endpoint, coverage, and status audit only. No new CI, ranking, superiority, native-held-out claim, or activation | 

The endpoint-parity audit reports the same endpoint-key set across all three methods for every declared cell. The paired artifact contains 32 fixed-rank-basis pair cells, with 960 common endpoint keys per pair and matching raw arrays/status counts. These are integrity and coverage facts, not an inferential result.

The status inventory reports 46,080 recovery records, 30,720 paired candidate records, 30,720 paired comparator records, 160 interval records, and 12,800 bootstrap records. Its policy is `retain and count; never impute`. The existence of interval/bootstrapped records does not authorize a manuscript confidence interval: the M2C artifact manifest remains `descriptive_audit_only` with `claim_activation: BLOCKED`.

## Proposed sentence changes

These are proposal-only changes. They clarify protocol ownership and prevent the E01 raw audit from being read as an activated ranking. Each sentence is bound to V1-026 / CAL-E01:75 and to exact artifact key paths in the companion ledger.

### P-001: separate the active hierarchy from the E01 registry

- Register item: `V1-026` / `CAL-E01:75` (`output/ncs_review_corpus/v1_author_decision_register.json#/items/25`)
- Manuscript location: `manuscript_src/natcs/supp_note4_benchmarks.md:3`
- Current sentence: `The declared comparator hierarchy is as follows.`
- Suggested sentence: `The active controlled benchmark comparator hierarchy is as follows; the separate CAL-E01:75 audit uses a frozen E4-r3 native-comparator registry and is not an additional active benchmark row.`
- Artifact key paths: `refine-logs/ncs_new_analysis_v2/rec-m2b2-20260810-235227-cst-01/primary/cal-e01-75-2400b0f538932133/comparator-ledger.json#/declared_methods`; `.../artifact-manifest.json#/claim_activation`; `.../artifact-manifest.json#/content_address_payload/raw_scope/claim_policy`; `refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_M2C_COVERAGE_V1_20260811_010147.json#/analyzer_coverage/CAL-E01:75/artifact_boundary`; `refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/comparator_registry.json#/content/records`
- Scientific ceiling: disclosure of protocol separation only; no E01 performance ranking, CI, superiority/equivalence claim, or claim activation.

### P-002: disambiguate E01 roles from active manuscript rows

- Register item: `V1-026` / `CAL-E01:75` (`output/ncs_review_corpus/v1_author_decision_register.json#/items/25`)
- Manuscript location: `manuscript_src/natcs/methods_estimator.md:5`
- Current sentence: `Comparator roles are assigned by the fitted object they return.`
- Suggested sentence: `Comparator roles are assigned by the fitted object they return; the separate CAL-E01:75 registry labels local_structured, causal_temporal_smoother, and fixed_rank_basis as native local-structured, causal-temporal-structured, and fixed low-rank/basis methods, respectively, and these labels are not aliases for the active CP, Tucker, or unrestricted-local rows.`
- Artifact key paths: `refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/comparator_registry.json#/content/records`; `.../comparator_registry.json#/content/required_interface`; `refine-logs/ncs_new_analysis_v2/rec-m2b2-20260810-235227-cst-01/primary/cal-e01-75-2400b0f538932133/comparator-ledger.json#/declared_methods`; `.../artifact-manifest.json#/content_address_payload/raw_scope/comparator_ledger_fields`
- Scientific ceiling: role and interface disclosure only. The E01 endpoint shape is not an authorization to map these methods to every active `controlled_benchmark_contract.json#/endpoint_availability/endpoint_ids` entry.

### P-003: carry the raw-only ceiling into validation prose

- Register item: `V1-026` / `CAL-E01:75` (`output/ncs_review_corpus/v1_author_decision_register.json#/items/25`)
- Manuscript location: `manuscript_src/natcs/results_validation.md:7`
- Current sentence: `Across these analyses, availability is established before numerical ranking, and failure and stability records travel with the corresponding errors.`
- Suggested sentence: `Across the active benchmark analyses, availability is established before numerical comparison and failure and stability records travel with the corresponding errors; the separate CAL-E01:75 output is a raw descriptive audit with claim activation blocked and therefore does not add a new confidence interval, superiority comparison, or manuscript claim.`
- Artifact key paths: `refine-logs/ncs_new_analysis_v2/rec-m2b2-20260810-235227-cst-01/primary/cal-e01-75-2400b0f538932133/status-inventory.json#/nonfinite_policy`; `.../status-inventory.json#/inventory`; `.../paired-differences.json#/pairs`; `.../artifact-manifest.json#/claim_activation`; `.../artifact-manifest.json#/content_address_payload/raw_scope/claim_policy`; `manuscript_src/natcs/controlled_benchmark_contract.json#/aggregation_contract/failure_handling`
- Scientific ceiling: retain failure/non-finite/outside-target semantics and the active benchmark boundary; do not report the raw paired arrays as a new CI, superiority result, or activated claim.

## Contract decision

No change to `manuscript_src/natcs/controlled_benchmark_contract.json` is proposed in REC-M3. Its active contract already specifies:

- failure handling and no favourable imputation at `#/aggregation_contract/failure_handling`;
- `NaN` / `OUTSIDE TARGET` semantics at `#/endpoint_availability/unavailable_sentinel`;
- active method-to-endpoint mappings at `#/endpoint_availability/method_to_endpoint_ids`;
- primary `N=15` and `N=30` replication counts at `#/primary_scenarios`; and
- bounded `N=50` replication coverage at `#/bounded_scale_stress/replication_coverage_by_method`.

The E01 registry's `full_operator_and_finite_horizon_response` endpoint is a separate E4 contract. Adding its method names to the active method-to-endpoint map would conflate protocols and is not recommended. The current issue is an omission/ambiguity in protocol naming, not a contradiction in the active contract.

## No-change determinations

- `manuscript_src/natcs/results_validation.md:3-5` already marks collapsed/projected outputs as outside-target or diagnostic and limits the headline result to matched `N=15/N=30` rows.
- `manuscript_src/natcs/supp_note4_benchmarks.md:13` correctly states that outside-target is neither zero, missing data, nor a failed estimate.
- `manuscript_src/natcs/methods_data.md:9-11` and the controlled contract correctly keep the active replication regime separate from the E01 `N=20/N=50` audit grid.
- No sentence should import E01 interval values, bootstrap intervals, raw paired differences, or method ordering into the active CP/Tucker/local claim.

## Verification target

The companion JSON records the source-path checks, protected pre-write hashes, and post-write equality checks. Expected final status is `PASS` for JSON parsing, source-path existence, M2C primary output hashes, register hash, manuscript tree hash, E4 candidate tree hash, and E4 quarantine tree hash.
