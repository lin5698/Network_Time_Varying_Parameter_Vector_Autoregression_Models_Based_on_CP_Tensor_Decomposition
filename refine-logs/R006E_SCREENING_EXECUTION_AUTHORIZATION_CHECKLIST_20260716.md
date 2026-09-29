# R006e Screening Execution Authorization Checklist

Date frozen: 2026-07-16 (Asia/Shanghai)

```yaml
document_type: R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST
schema_version: 1
requested_phase: SCREENING
current_state: NOT_AUTHORIZED
authorization_effect: NONE
self_authorizing: false
executable: false
external_authorization_required: true
evaluation_classification: simulation_only

outcome_data_inspected: false
outcome_phase_executed: false
screening_artifacts_present: false
confirmation_artifacts_present: false

authorized_by: null
authorized_at: null
authorization_decision_id: null
authorization_signature_sha256: null
external_authorization_artifact: null
```

## 1. Effect And Boundary

This checklist records the pre-outcome state and the conditions that would be
required for a later screening authorization decision. It does not authorize
screening, does not license any scientific claim, and cannot become an
authorization by editing or populating the null fields above.

A future authorization requires a separate, immutable authorization artifact
that references the SHA-256 of this checklist and is verified by a runner-side
authorization contract. That contract does not exist at this freeze. Until it
exists and a new explicit authorization is issued, all R006e screening and
confirmation execution remains closed. R006f outcome execution also remains
outside scope.

No outcome values, recovery statistics, promotion verdicts, or inferred
scientific results are recorded in this document. The complete forbidden-marker
set remains the set frozen in `scripts/experiments/r006e_native_experiment.py`.

## 2. Immutable Identities

All digests are SHA-256.

| Frozen object | Digest |
|---|---|
| Execution plan | `33146451cc65c5c2a522e66b9ddda21c48ec2c2b767ca0e08191c4a763da2fec` |
| R006e protocol | `4b1417a298a9d81d110f8c8a5b3611db993288935966753cbc96b325ad2a8bf0` |
| Runner | `145eb73391aef7ccdae6c8a7dbd0463a195ac81cce8760bfcc4d764744728c61` |
| Protocol module | `a5af1e71bfbe8027924b25df6a60732194369df1df4b8cdd6d2602611b3f7cf4` |
| Gate module | `1676b4ecd417fde0d57e0c7da1b27d816a0ec4cce06de0b306ccbde49ac87a3b` |
| Runner tests | `59a31b8fb1962b27ffd0ee3f0ae5dddbee5fbc86c751e9a092c2d31c449a837f` |
| Gate tests | `bf385941568f8eb8417a8fe405c3bf4781f33e7d824aecb24c60e740e3d15779` |
| Construction file bytes | `761e6a517bb7c6b94e27e7020d29009cba0468b533ed4a99f6b080181afd6f11` |
| Construction canonical body | `2976bc19ba494c2d7a1c2e51cd127e2cdad4467ae201faa5a6decfd29820e541` |
| Construction provenance | `ddd85c5ae4bfecd9551a25c3d16007fc2aa31ea15d54535fc11c5f4609a94456` |
| Configuration | `bc5f66f09ee46b7e3a987a877e14270a4280e781d9e29312159b3047970424c3` |
| Dependency manifest | `adb5b4c70fa7145e59cd6fb2b4e63ac9f7563a262108117eb4cf81ec319f7644` |
| Import source snapshot | `45b080e1ab194657f2692b1d8a9002cc585317dfdc20dd780698a097d7815759` |
| Candidate implementation | `55bfa0cc30730b5260e869dd6ce26a2b6f41b604caaac9d87e01728c7a95f3ae` |
| Construction manifest | `574ce51483fb218c8a4df81e73f8f1fd7893e65dd26046126b638cecbd1f2641` |

The construction manifest is
`output/high_impact_revision/r006e_native_supported_recovery/construction_manifest.sha256`.
It contains 45 entries: the artifact's complete 44-entry frozen source closure
(including the plan and protocol) plus the construction artifact itself.

Git HEAD is not a freeze identity. The worktree contains modified and untracked
protocol/source/test files, so only the content hashes above and the complete
manifest are authoritative.

## 3. Frozen Screening Scope

| Dimension | Frozen value |
|---|---|
| Seeds | `240100` through `240109`, exactly 10 |
| Cells | `rho={0.80,0.95}` x `a3={0.10,0.25}` x `eta={0.15,0.45}`, exactly 8 |
| Methods | `anchor_local`, `anchor_fused_tv`, `anchor_split_tucker333`, `dw_joint_tucker333`, exactly 4 |
| Endpoint queries per method row | `w_alt_interp` and `w_alt_family`; they do not multiply row identities |
| Replication identities | `10 x 8 x 4 = 320`, all unique and retained |
| Construction identities | `10 x 8 = 80`, all unique and `CONSTRUCTION_PASS` |
| Calibration dates | `80-139`, 60 dates |
| Validation dates | `140-163`, 24 dates |
| Evaluation dates | `164-199`, 36 dates |
| Candidate rank | `(3,3,3)` |
| Optimizer starts | 3 |
| Iteration cap | 300 |
| Screening decision | all nine frozen gates must pass in all eight cells |

The evaluation is simulation-only. It cannot support causal, empirical-system,
clinical, policy, or general real-world effectiveness claims.

## 4. Fresh Preflight Required Before Any Later Decision

Every item below must be rerun immediately before a separate authorization
decision. Each check must record its command, exit code, timestamp, stdout
SHA-256, and pre/post stable file identity where applicable.

- [ ] Read every frozen input as a regular non-symlink file using stable
      device/inode/size/mtime snapshots.
- [ ] Verify all 45 entries in `construction_manifest.sha256` with zero
      mismatches.
- [ ] Recompute the raw construction-file digest, canonical-body digest,
      provenance digest, configuration digest, dependency digest, import-source
      snapshot, candidate digest, and all 44 source hashes.
- [ ] Run `verify_construction_artifact` against the exact on-disk artifact and
      require schema version 1, `run_type=FORMAL`, `CONSTRUCTION_PASS`, 80 exact
      seed-cell certificates, no duplicates, and every prerequisite status
      `PASS`.
- [ ] Freshly execute the three test commands frozen in `TEST_COMMANDS`; stored
      construction-time statuses are not sufficient.
- [ ] Recheck every immutable identity after tests and immediately before any
      authorization artifact is published.
- [ ] Scan both exact primary and repeat output roots directly. In the primary
      root, permit only the exact frozen `construction_gate_preoutcome.json` and
      `construction_manifest.sha256`; the repeat root must be empty. Reject any
      other pre-existing manifest, attempt marker, temporary artifact,
      diagnostic, screening artifact, confirmation artifact, symlink, or
      non-regular file.
- [ ] Require a separate authorization artifact whose schema and verifier have
      been implemented and tested before any scientific call.

## 5. Intended Command Scope, Currently Non-Executable

The intended primary invocation is frozen as:

```bash
python3 -m scripts.experiments.r006e_native_experiment \
  --phase screening --workers 6 \
  --output output/high_impact_revision/r006e_native_supported_recovery
```

The required duplicate uses `--repeat` and only the isolated
`output/high_impact_revision/r006e_native_supported_recovery_repeat` root.

These commands are declarations, not permission to execute. The current parser
does not expose `--workers`, and `main()` rejects every non-construction phase.
No command may be approximated with alternative workers, seeds, cells, methods,
output roots, smoke status, or regenerated construction.

## 6. Required Attempt And Publication Contract

Before screening can be authorized, the implementation must provide all of the
following and pass tests for crash and adversarial file states:

- [ ] Atomically create an exclusive durable attempt record before any
      scientific call, separately for the primary and repeat roots.
- [ ] Bind each attempt record to role, attempt ID, phase, checklist digest,
      authorization-artifact digest, construction/config/provenance/source and
      dependency digests, exact seeds/cells/methods, output names, and worker
      count.
- [ ] Treat any prior marker, partial output, deleted prior output, crash, or
      worker failure as a retained incomplete/failed attempt, never as permission
      for a cleaner rerun.
- [ ] Scan actual directories inside the runner; caller-supplied filenames or
      an empty default cannot establish a first attempt.
- [ ] Recompute and match every seed-cell design-input digest, endpoint digest,
      selected family index, support certificate, and stream declaration before
      fitting. No endpoint redraw or replacement is allowed.
- [ ] Produce exactly 320 complete rows per attempt, retaining unavailable,
      non-scorable, non-converged, unstable, non-finite, crash, and worker-failure
      states without dropping or replacing identities.
- [ ] Hash the complete replication payload before summary/gate computation;
      recompute all nine gates from that exact payload.
- [ ] Publish every artifact exclusively and atomically, reject overwrites and
      symlinks, and preserve diagnostics and attempt state on failure.
- [ ] Freeze exact schemas/cardinalities for replication, summary, diagnostics,
      result, attempt, duplicate-comparison, and screening-manifest artifacts.

Expected primary output names are:

- `screening_replications.csv`
- `screening_summary.csv`
- `screening_results.json`
- `screening_diagnostics.jsonl`

No confirmation file may be created by screening.

## 7. Mandatory Primary And Repeat

Exactly one primary attempt and one unconditional repeat attempt are required.
The repeat runs whether the primary passes, fails, or is incomplete. It is not a
selectable rerun.

The duplicate comparison must exclude exactly:

- `runtime_seconds`
- `peak_memory_bytes`
- `generated_at`

Every other identity, seed, cell, endpoint, method, metric, failure, support,
convergence, selected hyperparameter, status, digest, and decision field must
match with zero differences. Any mismatch is an integrity failure and blocks
claim licensing and confirmation.

## 8. Stop Rules

- Any absent external authorization, failed preflight, hash mismatch, unstable
  file, prior attempt evidence, source drift, schema mismatch, missing identity,
  duplicate identity, or unexpected output: do not execute or stop fail-closed.
- Any cell failing any frozen screening gate makes the screening decision
  `FAIL`. Preserve all rows and diagnostics; do not change thresholds, grids,
  endpoints, methods, or seeds.
- A crash or worker failure is not permission to restart selectively. Preserve
  the attempt and apply the predeclared incomplete/failure rule.
- Primary/repeat disagreement is an integrity failure even if both individual
  gate decisions are `PASS`.
- A screening `PASS` does not authorize confirmation and does not license a
  manuscript claim by itself.
- A genuine implementation defect requires a new protocol version, regression
  tests, new construction, and complete new primary/repeat attempts. It may not
  replace R006e results in place.

## 9. Confirmation Separation

Confirmation remains technically and procedurally blocked. It uses only seeds
`250100-250129` and requires, after an unchanged screening `PASS` and exact
primary/repeat agreement:

- a separately approved simultaneous-median-bound specification and tests;
- a separate post-screening confirmation construction artifact containing all
  240 confirmation seed-cells and no outcomes;
- a separate hash-locked authorization decision;
- isolated confirmation outputs with no pooling with screening.

No confirmation panel, certificate, fit, metric, or result may be generated by
this checklist or by any screening preflight.

## 10. Authorization Review At Freeze

| Integrity area | Status | Evidence at freeze |
|---|---|---|
| Prespecified design and nine-gate semantics | PASS | Protocol and gate tests freeze 10 seeds, 8 cells, 4 methods, 320 identities and nine gates |
| Outcome-free construction and leakage boundary | PASS | 80/80 construction certificates pass; no outcome artifact exists |
| Complete-row and failure retention | PASS | Parser and gate require all 320 identities and fail closed on invalid rows |
| Confirmation isolation | PASS | Confirmation remains declarations-only and technically refused |
| Construction/source manifest | PASS | 45/45 manifest entries verify at this freeze |
| Screening executor and CLI | FAIL | Screening execution is absent; non-construction phases are refused; `--workers` is absent |
| Durable first-attempt and rerun control | FAIL | No exclusive attempt ledger or deletion/crash history exists |
| Primary/repeat enforcement and comparator | FAIL | No unconditional repeat orchestration or exact duplicate comparator exists |
| Output schemas and writers | FAIL | Formal screening summary/diagnostic/result production is not implemented and fully frozen |
| External authorization contract | FAIL | No separate authorization schema, signature rule, path, or runner verifier exists |

Overall authorization verdict: **FAIL - NOT_AUTHORIZED**.

## 11. Blocking Work Before A New Authorization Request

1. Implement and test a screening-only executor without changing the frozen
   scientific design, metrics, gates, or construction identities.
2. Implement durable primary/repeat attempt records and actual-directory scans.
3. Freeze every screening output schema and implement exclusive atomic writers.
4. Implement the unconditional duplicate run and exact comparison contract.
5. Define a separate external authorization artifact and runner-side verifier.
6. Resolve the plan's checkpoint/commit requirement or explicitly supersede it
   with an approved content-addressed freeze policy; Git HEAD is currently not
   an adequate provenance identity.
7. Submit the new implementation, tests, schemas, and this checklist digest for
   a fresh specification and integrity review.

Until all seven items are complete and a new explicit authorization is issued,
the outcome phase remains closed.
