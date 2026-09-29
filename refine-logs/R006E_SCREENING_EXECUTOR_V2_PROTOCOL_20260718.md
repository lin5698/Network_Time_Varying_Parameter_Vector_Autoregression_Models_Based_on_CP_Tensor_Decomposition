# R006e Screening Executor V2 Protocol

Date frozen: 2026-07-18 (Asia/Shanghai)
Schema version: 2
Evaluation classification: simulation-only
Authorization state at freeze: `NOT_AUTHORIZED`

## 1. Scope And Supersession

This protocol freezes operational contracts only. It does not execute or
authorize a DGP, fit, evaluation, gate, screening, confirmation, or R006f
operation. Production authorization and production trust evidence are absent.

V2 supersedes the v1 two-root restriction only by reserving these three exact
relative roots, in this order:

1. `output/high_impact_revision/r006e_native_supported_recovery_v2`
2. `output/high_impact_revision/r006e_native_supported_recovery_v2_repeat`
3. `output/high_impact_revision/r006e_native_supported_recovery_v2_control`

It neither amends nor permits writes to the v1 primary and repeat roots
`output/high_impact_revision/r006e_native_supported_recovery` and
`output/high_impact_revision/r006e_native_supported_recovery_repeat`. The first
v2 root may eventually contain only its prescribed construction inputs before
claim; repeat and control must be empty before the singleton pair claim.

## 2. Ordered Scientific Schemas

All CSV order is byte-significant. Formal replication has exactly 85 columns:
the existing 86-column `SCREENING_CSV_FIELDS` minus only
`peak_memory_worker_pid`:

Every formal replication field named by the frozen existing
`SCREENING_FLAG_FIELDS` evaluator contract is an exact JSON integer `0` or `1`.
JSON booleans and all other integers are invalid. Summary gate flags and
`passed` remain JSON booleans.

The nonbinary integer set is derived exactly as `SCREENING_INTEGER_FIELDS`
minus `peak_memory_worker_pid` and the binary flag fields. It includes `seed`,
`evaluation_date_start`, `evaluation_date_end`, `evaluation_dates`,
`family_selected_index`, `peak_memory_bytes`, each endpoint's
`evaluation_dates` and `raw_date_count`, and both alternative endpoints'
`evaluation_retained_rank_min`. Values are exact JSON integers, never booleans
or integral floats; only fields in the frozen nullable set may be null.

```text
seed, rho, a3, eta, method, fit_sha256, parameterization, fit_success,
scorable, selected_hyperparameter, at_least_one_converged_start,
selected_objective_trace_nonincreasing, failure_code, failure_reason,
runtime_seconds, fit_diagnostics_json, endpoint_construction_status,
endpoint_failure_reasons_json, family_selected_index, w_ref_available,
w_ref_availability_status, w_ref_operator_relative_error_mean,
w_ref_operator_absolute_error_mean, w_ref_raw_response_error_mean,
w_ref_response_zero_ratio_mean, w_ref_stability_qualified_error_mean,
w_ref_stability_qualified_rate, w_ref_projected_sensitivity_error_mean,
w_ref_estimated_spectral_radius_mean, w_ref_estimated_instability_rate,
w_ref_raw_date_count, w_ref_evaluation_dates, w_alt_interp_available,
w_alt_interp_availability_status, w_alt_interp_operator_relative_error_mean,
w_alt_interp_operator_absolute_error_mean,
w_alt_interp_raw_response_error_mean, w_alt_interp_response_zero_ratio_mean,
w_alt_interp_stability_qualified_error_mean,
w_alt_interp_stability_qualified_rate,
w_alt_interp_projected_sensitivity_error_mean,
w_alt_interp_estimated_spectral_radius_mean,
w_alt_interp_estimated_instability_rate, w_alt_interp_raw_date_count,
w_alt_interp_evaluation_dates, w_alt_family_available,
w_alt_family_availability_status, w_alt_family_operator_relative_error_mean,
w_alt_family_operator_absolute_error_mean,
w_alt_family_raw_response_error_mean, w_alt_family_response_zero_ratio_mean,
w_alt_family_stability_qualified_error_mean,
w_alt_family_stability_qualified_rate,
w_alt_family_projected_sensitivity_error_mean,
w_alt_family_estimated_spectral_radius_mean,
w_alt_family_estimated_instability_rate, w_alt_family_raw_date_count,
w_alt_family_evaluation_dates, observed_topology_prediction_rmse,
m_ref_relative_error_mean, b_relative_error_mean,
topology_slope_interp_error_mean, topology_slope_family_error_mean,
estimated_instability_rate, evaluation_date_start, evaluation_date_end,
evaluation_dates, w_alt_interp_calibration_chi_max,
w_alt_interp_evaluation_chi_mean, w_alt_interp_evaluation_chi_max,
w_alt_interp_evaluation_amplification_mean,
w_alt_interp_evaluation_amplification_max,
w_alt_interp_evaluation_alpha_mean,
w_alt_interp_evaluation_retained_rank_min,
w_alt_interp_evaluation_condition_number_max,
w_alt_family_calibration_chi_max, w_alt_family_evaluation_chi_mean,
w_alt_family_evaluation_chi_max,
w_alt_family_evaluation_amplification_mean,
w_alt_family_evaluation_amplification_max,
w_alt_family_evaluation_alpha_mean,
w_alt_family_evaluation_retained_rank_min,
w_alt_family_evaluation_condition_number_max, peak_memory_bytes,
peak_memory_scope
```

`SUMMARY_FIELDS` is exactly the nine existing gates, with identity completeness
kept as a separate result/audit precondition:

```text
availability, finite_and_converged, operator_relative_error,
response_zero_ratio, paired_improvement, joint_win_rate,
worst_endpoint_improvement, observed_rmse_guardrail, w_ref_guardrail
```

The ordered summary CSV row is:

```text
rho, a3, eta, passed, <the nine SUMMARY_FIELDS in the order above>,
failed_conditions_json, audit_values_json
```

The comparable scientific object has exactly the ordered keys
`replication, summary, result`. Replication and summary are arrays using the
schemas above. Result has exactly:

```text
schema_version, document_type, status, semantic_replication_sha256,
semantic_summary_sha256, construction_sha256, config_sha256,
candidate_sha256, provenance_sha256, seed_ids, identity_completeness,
evaluation_classification
```

Attempt IDs, roles, PIDs, hostnames, authorization evidence, operational raw
hashes, diagnostics, resources, row journals, terminals, and manifests are
forbidden from all three comparable scientific objects. Identity completeness
is not a tenth gate and must not replace, merge, or rename a gate.

## 3. Ordered Operational Record Schemas

Every method record begins with the exact identity
`seed, rho, a3, eta, method`. The complete ordered records are:

```text
diagnostic: seed, rho, a3, eta, method, method_seed, fit_sha256,
fit_success, scorable, failure_code, failure_reason, fit_diagnostics_json,
generated_at

resource: seed, rho, a3, eta, method, worker_pid, peak_memory_bytes,
peak_memory_scope, attempt_id, role

row_journal: seed, rho, a3, eta, method, attempt_id, role, row_status,
replication_sha256, diagnostic_sha256, resource_sha256, generated_at
```

The row-journal record deliberately contains neither `schema_version` nor
`document_type`; its exact field list above is nested in schema-version-2 role
artifacts. Validators must not infer or index undeclared schema metadata.

Diagnostic state semantics are method-local. `scorable=true` requires
`fit_success=true` and null `failure_code`/`failure_reason`. `scorable=false`
requires paired, nonempty failure code and reason; `fit_success` may be false
for a fit-stage failure or true for an evaluation-stage failure such as
`EVALUATION_NUMERICAL_FAIL`. `fit_success=false, scorable=true` is forbidden.
One method-level evaluation failure is retained without converting successful
peer methods into a cell-level runner failure.

Each role has exactly 320 replication, 320 diagnostic, 320 resource, and 320
row-journal records with one common identity set. A failed cell retains exactly
four records in each class. Summary has exactly eight rows.

## 4. Identity Order

Replication order is seed-major for seeds `240100` through `240109`; within a
seed, cells follow the Cartesian product order
`rho=(0.80,0.95)`, `a3=(0.10,0.25)`, `eta=(0.15,0.45)`; within a cell, methods
are `anchor_local`, `anchor_fused_tv`, `anchor_split_tucker333`, and
`dw_joint_tucker333`. This yields 320 unique identities. Summary order is the
same eight-cell Cartesian product without seed or method.

### 4.1 Cell Boundary, Certificate, And Aggregate Ownership

The production `run_screening_cell` entry point accepts exactly `task`,
`construction_certificate`, `config`, `attempt_id`, `role`, and `generated_at`.
It fixes the production scientific primitives, process ID, and peak-RSS reader
internally. Injection is available only through the separate fixture entry
point, which requires identity with the module-private opaque fixture
capability; caller-created lookalikes are rejected before execution.

The construction certificate has exactly these 17 keys, with no missing or
additional keys, including fields whose values may be null:

```text
seed, rho, a3, eta, status, failure_reasons, design_inputs_sha256,
family_seed, dgp_and_interp_streams, interp_endpoint_sha256,
family_endpoint_sha256, family_selected_index, interp_calibration,
interp_prospective, family_calibration, family_prospective,
family_candidate_certificates
```

Runtime evidence has exactly the final 13 evidence keys in that list.
Certificate identity and evidence comparisons are recursive, finite-JSON, and
type-exact: in particular a JSON boolean never equals an integer, object keys
must be strings, arrays retain order, and NaN, Infinity, cycles, non-JSON
objects, missing keys, and extra keys are mismatches. Any mismatch is retained
as four records per class before any fit or evaluation call.

Failure records never serialize the raw, unvalidated certificate. Their
construction provenance is a deterministic bounded object containing only
`certificate_state`, whose value is `schema_valid` for an exact finite-JSON
certificate schema and `malformed` otherwise. This rule makes retention total
for hostile values such as non-string keys, NaN, cycles, and non-JSON objects.

Role aggregation revalidates every input schema, identity order, cardinality,
and row-journal hash binding, then owns a defensive copy of every record and
exposes each copy as an immutable mapping. Later source mutation cannot change
the aggregate, and aggregate item assignment is an error.

## 5. Strict Governance Object Key Sets

Unknown keys, missing keys, duplicate declared fields, non-string JSON object
keys, non-JSON values, and NaN or positive/negative Infinity at any depth are
errors. Ordered key sets are:

```text
authorization_payload: schema_version, document_type, decision, phase,
decision_id, authorizer_id, issued_at, checklist_sha256, protocol_sha256,
plan_sha256, runner_contract_sha256, construction_file_sha256,
construction_canonical_sha256, provenance_sha256, config_sha256,
dependency_manifest_sha256, source_manifest_sha256, candidate_sha256,
frozen_v1_authority_digest, primary_root, repeat_root, control_root,
primary_attempt_id, repeat_attempt_id, workers, seeds, cells, methods,
output_names, expected_rows

authorization_envelope: schema_version, document_type, payload,
payload_sha256, artifact_sha256, trust_evidence, trust_evidence_sha256

trust_evidence: schema_version, document_type,
authorization_artifact_sha256, signed_payload_sha256, signature_algorithm,
pinned_key_id, detached_signature, detached_signature_sha256,
trust_policy_id, external_witness_id

pair_claim: schema_version, document_type, decision_id,
authorization_artifact_sha256, authorization_payload_sha256,
trust_evidence_sha256, frozen_v1_authority_digest, primary_attempt_id,
repeat_attempt_id, primary_root, repeat_root, control_root, claimed_at,
supervisor_pid, supervisor_hostname, status

role_start: schema_version, document_type, decision_id, attempt_id, role,
pair_claim_sha256, started_at, worker_pid, hostname, status

terminal: schema_version, document_type, decision_id, attempt_id, role,
status, pair_claim_sha256, role_start_sha256, replication_sha256,
summary_sha256, result_sha256, diagnostics_sha256, resources_sha256,
row_journal_sha256, started_at, finished_at, exit_code, failure_code,
failure_reason

duplicate_comparison: schema_version, document_type, status,
compared_payloads, primary_replication_sha256, repeat_replication_sha256,
primary_summary_sha256, repeat_summary_sha256, primary_result_sha256,
repeat_result_sha256, mismatch_paths

manifest: schema_version, document_type, decision_id, attempt_id, role,
status, pair_claim_sha256, role_start_sha256, terminal_sha256,
replication_sha256, summary_sha256, result_sha256, diagnostics_sha256,
resources_sha256, row_journal_sha256, replication_count, summary_count,
diagnostic_count, resource_count, row_journal_count, identity_set_sha256,
generated_at
```

The row-journal and scientific-result schemas are those stated in Sections 2
and 3 and are governed by the same exact-key rule.

Exact semantic literals are also frozen:

```text
authorization_payload.document_type = r006e_screening_authorization_payload_v2
authorization_envelope.document_type = r006e_screening_authorization_envelope_v2
trust_evidence.document_type = r006e_screening_trust_evidence_v2
pair_claim.document_type = r006e_screening_pair_claim_v2
role_start.document_type = r006e_screening_role_start_v2
terminal.document_type = r006e_screening_terminal_v2
scientific_result.document_type = r006e_screening_scientific_result_v2
duplicate_comparison.document_type = r006e_screening_duplicate_comparison_v2
manifest.document_type = r006e_screening_manifest_v2

authorization_payload.decision = AUTHORIZE
authorization_payload.phase = SCREENING
authorization_payload.workers = 6
authorization_payload.expected_rows = 320
authorization_payload.seeds = [240100, 240101, 240102, 240103, 240104,
240105, 240106, 240107, 240108, 240109]
authorization_payload.cells = [[0.8, 0.1, 0.15], [0.8, 0.1, 0.45],
[0.8, 0.25, 0.15], [0.8, 0.25, 0.45], [0.95, 0.1, 0.15],
[0.95, 0.1, 0.45], [0.95, 0.25, 0.15], [0.95, 0.25, 0.45]]
authorization_payload.methods = [anchor_local, anchor_fused_tv,
anchor_split_tucker333, dw_joint_tucker333]
authorization_payload.output_names = [screening_replications.csv,
screening_summary.csv, screening_results.json]

pair_claim.status = CLAIMED
role_start.status = STARTED
terminal.status in {PASS, FAIL, INCOMPLETE}
scientific_result.status in {PASS, FAIL, INCOMPLETE}
duplicate_comparison.status in {PASS, FAIL}
manifest.status in {CLAIMED, STARTED, PASS, FAIL, INCOMPLETE}
scientific_result.seed_ids = [240100, 240101, 240102, 240103, 240104,
240105, 240106, 240107, 240108, 240109]
scientific_result.identity_completeness is a JSON boolean
scientific_result.evaluation_classification = simulation-only
```

## 6. Nullability

Authorization payload/envelope, trust evidence, pair claim, role start, row
journal, scientific result, duplicate comparison, summary row, and resource
record have no nullable fields. Diagnostic nullable fields are exactly
`fit_sha256, failure_code, failure_reason, fit_diagnostics_json`.

Formal replication inherits exactly these v1 nullable fields:

```text
selected_hyperparameter, failure_code, failure_reason, family_selected_index,
w_ref_operator_relative_error_mean, w_ref_operator_absolute_error_mean,
w_ref_raw_response_error_mean, w_ref_response_zero_ratio_mean,
w_ref_stability_qualified_error_mean, w_ref_stability_qualified_rate,
w_ref_projected_sensitivity_error_mean, w_ref_estimated_spectral_radius_mean,
w_ref_estimated_instability_rate, w_ref_raw_date_count, w_ref_evaluation_dates,
w_alt_interp_operator_relative_error_mean,
w_alt_interp_operator_absolute_error_mean,
w_alt_interp_raw_response_error_mean, w_alt_interp_response_zero_ratio_mean,
w_alt_interp_stability_qualified_error_mean,
w_alt_interp_stability_qualified_rate,
w_alt_interp_projected_sensitivity_error_mean,
w_alt_interp_estimated_spectral_radius_mean,
w_alt_interp_estimated_instability_rate, w_alt_interp_raw_date_count,
w_alt_interp_evaluation_dates, w_alt_family_operator_relative_error_mean,
w_alt_family_operator_absolute_error_mean,
w_alt_family_raw_response_error_mean, w_alt_family_response_zero_ratio_mean,
w_alt_family_stability_qualified_error_mean,
w_alt_family_stability_qualified_rate,
w_alt_family_projected_sensitivity_error_mean,
w_alt_family_estimated_spectral_radius_mean,
w_alt_family_estimated_instability_rate, w_alt_family_raw_date_count,
w_alt_family_evaluation_dates, observed_topology_prediction_rmse,
m_ref_relative_error_mean, b_relative_error_mean,
topology_slope_interp_error_mean, topology_slope_family_error_mean,
estimated_instability_rate,
w_alt_family_calibration_chi_max, w_alt_family_evaluation_chi_mean,
w_alt_family_evaluation_chi_max,
w_alt_family_evaluation_amplification_mean,
w_alt_family_evaluation_amplification_max,
w_alt_family_evaluation_alpha_mean,
w_alt_family_evaluation_retained_rank_min,
w_alt_family_evaluation_condition_number_max
```

Terminal nullable fields are exactly `role_start_sha256,
replication_sha256, summary_sha256, result_sha256, diagnostics_sha256,
resources_sha256, row_journal_sha256, started_at, exit_code, failure_code,
failure_reason`. Manifest nullable fields are the same seven start/scientific/
operational hashes through `row_journal_sha256`; counts remain non-null and use
zero for absent records.

## 7. Attempt And Crash State Machine

Terminal states are exactly `PASS`, `FAIL`, and `INCOMPLETE`. Legal transitions
are only:

```text
CLAIMED -> STARTED
CLAIMED -> INCOMPLETE
STARTED -> PASS | FAIL | INCOMPLETE
PASS | FAIL | INCOMPLETE -> no state
```

There is no resume, reset, reclaim, selective resubmission, or row replacement.
Both attempts are authorization inputs. For role `primary` or `repeat`:

```python
material = f"R006E_SCREENING_V2_ATTEMPT\0{decision_id}\0{role}".encode("utf-8")
attempt_id = "r006e-v2-" + sha256(material).hexdigest()
```

The supervisor claims both roles before either scientific call and starts each
in an independent child process. A schema-complete caught scientific failure is
`FAIL`. If a child dies while the original supervisor remains alive, the
supervisor publishes that role `INCOMPLETE` and proceeds to repeat after any
primary terminal. If the supervisor dies, any started role and the pair remain
permanently `INCOMPLETE`; no replacement may finish a missing repeat. The
unconditional-repeat guarantee therefore applies only while the original
supervisor remains alive.

## 8. Semantic Digest And Duplicate Rule

Duplicate comparison recursively removes a mapping entry only when its exact
key is one of `runtime_seconds`, `peak_memory_bytes`, or `generated_at`. It
does not remove by suffix, substring, value, type, or position. A
`fit_diagnostics_json` string is parsed as strict finite JSON and must decode
to a JSON object. Null, arrays, numbers, booleans, and strings are invalid
top-level diagnostic values. The object is recursively canonicalized under the
same exclusions, then serialized back canonically.
Objects use UTF-8 canonical JSON with sorted keys, comma/colon separators,
`ensure_ascii=True`, and `allow_nan=False`; arrays retain their frozen order.
SHA-256 is computed over those bytes.

Before a role payload is semantically digested or compared, its replication
and summary canonical digests are recomputed and must equal that same role's
`scientific_result.semantic_replication_sha256` and
`scientific_result.semantic_summary_sha256`; matching stale or fabricated
claims are an integrity error. Canonical scalar representations are also used
for mismatch paths, so `0.0` and `-0.0` differ. Duplicate status is `PASS` if
and only if all three emitted replication, summary, and result digest pairs
match.

Scientific result binds the semantic replication and summary digests. The
duplicate comparison covers exactly replication, summary, and result.
Diagnostics, resources, row journals, terminals, manifests, and their raw byte
hashes are operational integrity evidence only and never enter a comparable
scientific result. A change outside the three exact exclusions, including an
identity, metric, failure, support, convergence, hyperparameter, status, or
semantic digest, is a mismatch.

## 9. Authorization, Trust, And V1 Authority

Content hashes prove integrity, not authorization authenticity. Production use
requires the exact envelope plus externally anchored trust evidence verified by
a configured production verifier against the pinned authorizer key and policy.
A fixture verifier is permitted only through an explicitly test-only API and
must be rejected by every production entry point. Missing production evidence,
verifier, signature, pinned policy, or external witness is a hard refusal before
science.

Every v2 construction build, construction verification, authorization check,
and screening preflight must stably reread and recompute the complete
`FROZEN_V1_AUTHORITY`: the v1 checklist and detached sidecar; every immutable
identity in its table; the v1 plan, protocol, runner, protocol/gate modules and
tests; both exact v1 root inventories; the construction artifact; and every one
of the 45 manifest/source-closure entries plus configuration, dependency,
import-source, candidate, canonical-body, and provenance identities. The
authorization payload binds one canonical `frozen_v1_authority_digest` for the
whole set. Checking only a checklist, artifact, manifest, or aggregate hash is
insufficient. Drift in any member refuses authorization even if all v2 hashes
match.

## 10. Filesystem Threat-Model Limit

Exclusive durable local claims retain crashes and deletion of role outputs
while the control ledger remains. This filesystem-only design cannot prove a
prior attempt if an actor can delete both output roots and the control ledger.
No marker, placeholder, regenerated empty directory, caller-supplied filename,
or fresh decision/attempt ID closes that limitation. Authorization requires an
external append-only witness for protection against complete local deletion.

## 11. Outcome-Free Construction V2 Contract

The construction phase has one public builder and one independent verifier:

```text
build_construction_v2(paths, *, scientific_spy=None)
verify_construction_v2(paths)
```

`paths` names the exact v2 primary, repeat, and control roots. The builder may
create and publish only these two files in the primary root:
`construction_gate_preoutcome.json` and `construction_manifest.sha256`.
Repeat and control must already be absent or empty and are never created or
modified by construction. Both v1 roots are read-only authority inputs.

The construction artifact has schema version 2, document type
`R006E_SCREENING_V2_CONSTRUCTION`, phase `CONSTRUCTION`, status
`CONSTRUCTION_PASS`, and current state `NOT_AUTHORIZED`. It binds the three
versioned roots, this plan, this protocol, the reserved future checklist with
the explicit state `ABSENT_NOT_AUTHORIZED`, ordered `V2_SOURCE_PATHS`, ordered
`V2_TEST_COMMANDS` and their `PASS` statuses, configuration/dependency/
candidate digests, a fresh canonical source closure, the complete frozen-v1
authority digest, and exactly 80 seed-cell support certificates in seed-major
Cartesian order. Unknown keys, missing keys, non-finite values, and outcome
fields are invalid. The artifact and manifest use canonical UTF-8 JSON and
exclusive durable publication; verification recomputes every source, v1,
provenance, certificate, and digest identity from stable files.

Construction invokes only deterministic design/support construction. It never
invokes a fit, evaluation, screening gate, confirmation, or R006f operation,
and no outcome values are serialized. A later authorization checklist binds the
completed construction by digest; it is not part of this source closure and is
required to remain absent while construction is frozen.
