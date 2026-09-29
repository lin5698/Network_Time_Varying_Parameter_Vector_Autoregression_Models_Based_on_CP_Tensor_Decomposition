# R006e Screening V2 Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Every task uses vertical RED-GREEN TDD, specification review, then code-quality review. Do not commit and do not run a scientific outcome phase.

**Goal:** Build and freeze a versioned, fail-closed R006e screening executor with durable primary/repeat attempt governance while keeping every scientific outcome path unauthorized.

**Architecture:** Preserve the complete frozen v1 authority set byte-for-byte:
the v1 checklist and every immutable identity it declares, including the v1
plan, protocol, runner, protocol/gate modules and tests, construction artifact,
45-entry construction manifest/source closure, configuration, dependencies,
import snapshot, candidate implementation, and both v1 output roots. Add
focused v2 modules for schemas, attempt governance, scientific cell execution,
output publication, and duplicate audit. V2 receives a fresh outcome-free
construction artifact and a new `NOT_AUTHORIZED` checklist before any screening
command can pass authorization.

**Tech Stack:** Python 3 standard library, NumPy/SciPy, existing R006e scientific modules, `unittest`, canonical JSON, CSV, JSONL, SHA-256, durable exclusive filesystem publication.

The frozen v1 checklist is the existing external governance record
`refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.md`
with detached sidecar
`refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_20260716.sha256`.
It is not a runner-generated artifact or runner phase. The two existing v1
runner construction files are exactly
`output/high_impact_revision/r006e_native_supported_recovery/construction_gate_preoutcome.json`
and
`output/high_impact_revision/r006e_native_supported_recovery/construction_manifest.sha256`.
The plan preserves and verifies these governance and runner files according to
their distinct roles; it never asks the v1 runner to generate a checklist.

---

## Non-Negotiable Boundaries

- Never write into `r006e_native_supported_recovery/` or `r006e_native_supported_recovery_repeat/` except to read and verify the frozen v1 files.
- Use only `r006e_native_supported_recovery_v2/`, `r006e_native_supported_recovery_v2_repeat/`, and `r006e_native_supported_recovery_v2_control/` for v2 fixtures or future artifacts.
- The v2 protocol explicitly supersedes the v1 two-root restriction only for those three exact versioned roots. It does not amend, reinterpret, or authorize any write to either v1 root.
- Do not execute formal screening, confirmation, or any R006f outcome.
- Keep confirmation technically refused.
- Do not change seeds, cells, methods, estimator grids, endpoints, metrics, gates, splits, ranks, starts, or stopping rules.
- Any source change invalidates v1 for future execution and therefore requires a new v2 construction artifact. It does not overwrite or reinterpret v1.
- Define `FROZEN_V1_AUTHORITY` from the immutable-identity table and complete
  45-entry manifest in the v1 checklist. Every v2 construction build,
  verification, authorization verification, and screening preflight must stably
  reread and recompute that full set; checking only the v1 artifact or checklist
  hash is insufficient.
- The production authorization artifact and trust evidence remain absent throughout this plan. Tests use temporary fixture authorization records only.

## Frozen V2 Operational Decisions

1. Formal scientific replication CSV has 85 columns: the existing 86-field runner schema minus `peak_memory_worker_pid`. PID is retained only in the role-specific resource journal and raw attempt manifest.
2. Scientific duplicate comparison recursively excludes exactly `runtime_seconds`, `peak_memory_bytes`, and `generated_at`. No other key is excluded.
3. The comparable scientific set contains exactly replication, summary, and result. Scientific result payloads bind semantic replication and summary digests computed after those exact exclusions. Diagnostics, resources, row journals, and raw byte hashes are operational artifacts: terminals/manifests bind their raw hashes, but no operational hash or field enters a compared scientific result.
4. Attempt IDs, roles, PIDs, hostnames, raw hashes, authorization evidence, diagnostics, resources, and row journals live only in operational ledgers/manifests or role-specific operational files, not in scientific replication, summary, result, or the comparable scientific set.
5. Exactly one primary and one unconditional repeat are claimed together before either scientific call. The pair supervisor runs each role in an independent child process. If a role child dies while the supervisor remains alive, the supervisor publishes an `INCOMPLETE` terminal and proceeds to repeat. If the supervisor itself dies, any started role and the pair remain permanently `INCOMPLETE`; no process may resume, reset, reclaim, or complete the missing repeat. Thus unconditional repeat is guaranteed only while the original supervisor remains alive.
6. Each role must publish exactly 320 formal replication rows, 320 method-level diagnostic records, 320 resource records, and 320 row-journal records, all sharing the exact identity set `(seed, rho, a3, eta, method)`. A failed cell contributes exactly four identities to every one of those four record classes. The role manifest binds every exact cardinality and identity-set digest.
7. Content hashes establish integrity, not authorization authenticity. Production authorization additionally requires externally anchored trust evidence verified by a configured production trust verifier against a pinned authorizer key/policy. Test fixtures may use an explicitly test-only verifier that production entry points reject. The production authorization artifact and trust evidence remain absent throughout this plan, so every production authorization check remains a hard refusal.
8. The local threat model is content-addressed research governance, not protection against an actor able to delete both output roots and the control ledger. A stronger deletion guarantee requires an external append-only witness and remains a stated prerequisite for authorization.

### Task 1: Freeze V2 Operational Protocol And Schemas

**Files:**
- Create: `refine-logs/R006E_SCREENING_EXECUTOR_V2_PROTOCOL_20260718.md`
- Create: `scripts/experiments/r006e_screening_schema_v2.py`
- Create: `scripts/experiments/test_r006e_screening_schema_v2.py`

- [ ] **Step 1: Write one RED test for the formal replication schema**

```python
def test_formal_replication_schema_omits_pid_only():
    self.assertEqual(
        FORMAL_REPLICATION_FIELDS,
        tuple(field for field in SCREENING_CSV_FIELDS
              if field != "peak_memory_worker_pid"),
    )
    self.assertEqual(len(FORMAL_REPLICATION_FIELDS), 85)
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_screening_schema_v2 -v`

Expected: missing module or symbols.

- [ ] **Step 3: Implement exact immutable schemas**

Define:

```python
SCHEMA_VERSION = 2
FORMAL_REPLICATION_FIELDS = tuple(
    field for field in SCREENING_CSV_FIELDS
    if field != "peak_memory_worker_pid"
)
SUMMARY_FIELDS = (
    "rho", "a3", "eta", "passed",
    "availability",
    "finite_and_converged",
    "operator_relative_error",
    "response_zero_ratio",
    "paired_improvement",
    "joint_win_rate",
    "worst_endpoint_improvement",
    "observed_rmse_guardrail",
    "w_ref_guardrail",
    "failed_conditions_json", "audit_values_json",
)
DIAGNOSTIC_FIELDS = (
    "seed", "rho", "a3", "eta", "method", "method_seed",
    "fit_sha256", "fit_success", "scorable", "failure_code",
    "failure_reason", "fit_diagnostics_json", "generated_at",
)
RESOURCE_FIELDS = (
    "seed", "rho", "a3", "eta", "method", "worker_pid",
    "peak_memory_bytes", "peak_memory_scope", "attempt_id", "role",
)
ALLOWED_DUPLICATE_EXCLUSIONS = frozenset({
    "runtime_seconds", "peak_memory_bytes", "generated_at",
})
```

Freeze strict key sets for authorization payload/envelope/trust evidence, pair
claim, role start, row journal, terminal, scientific result, duplicate
comparison, and manifest. Identity completeness is a separate result/audit
precondition and must never replace, merge, or rename any of the nine gates.
The protocol document must state all field lists, cardinalities, ordering,
nullability, state transitions, v2 roots, semantic-digest algorithm, and the
filesystem-only deletion limitation without placeholders.

- [ ] **Step 4: Add vertical tests for every schema transition**

Add one test then minimal implementation for: unknown/missing key rejection,
non-finite JSON rejection, exact 320 identity enumeration, exact 8 summary
identities, allowed terminal states, and absence of operational fields from
comparable scientific payloads.

- [ ] **Step 5: Run focused schema tests**

Expected: all tests `OK`; no output files created.

### Task 2: Implement Canonical Scientific Duplicate Semantics

**Files:**
- Create: `scripts/experiments/r006e_duplicate_audit_v2.py`
- Create: `scripts/experiments/test_r006e_duplicate_audit_v2.py`

- [ ] **Step 1: Write RED tests for recursive exact exclusions**

```python
def test_semantic_canonicalization_excludes_only_three_names():
    left = fixture_payload(runtime=1.0, memory=100, generated="a")
    right = fixture_payload(runtime=9.0, memory=999, generated="b")
    self.assertEqual(semantic_digest(left), semantic_digest(right))
    right["peak_memory_worker_pid"] = 99
    with self.assertRaisesRegex(DuplicateIntegrityError, "unexpected field"):
        semantic_digest(right)
```

- [ ] **Step 2: Verify RED, then implement recursive canonicalization**

Recursively remove a mapping entry only when its exact key is in
`ALLOWED_DUPLICATE_EXCLUSIONS`. Parse nested `fit_diagnostics_json` as JSON,
canonicalize it recursively, and serialize it back canonically before hashing.
Never remove by suffix, substring, type, position, or runtime-like value.

- [ ] **Step 3: Add tests for raw-hash/semantic-hash separation**

Require role raw hashes to differ when allowed runtime fields differ while
semantic digests match. Require changes to identities, metrics, failures,
support, convergence, hyperparameters, status, or semantic digest to fail.

- [ ] **Step 4: Implement `compare_scientific_attempts`**

```python
def compare_scientific_attempts(
    primary: ScientificPayloads,
    repeat: ScientificPayloads,
) -> DuplicateComparison:
    """Compare exactly replication, summary, and result semantically."""
```

Return exact replication/summary/result digests, mismatch paths, and `PASS`
only for zero non-excluded differences. Diagnostics are raw-hashed and
integrity-bound in each role manifest, but are not scientifically compared.

- [ ] **Step 5: Run focused duplicate tests**

Expected: all tests `OK`.

### Task 3: Implement V2 Authorization And Durable Pair Claim

**Files:**
- Create: `scripts/experiments/r006e_attempt_ledger_v2.py`
- Create: `scripts/experiments/test_r006e_attempt_ledger_v2.py`

- [ ] **Step 1: Write RED tests proving authorization precedes science**

```python
def test_missing_authorization_refuses_before_science():
    spy = ScientificSpy()
    with self.assertRaisesRegex(AuthorizationError, "authorization"):
        prepare_screening_pair(paths=temp_paths(), authorization=None,
                               scientific_runner=spy)
    self.assertEqual(spy.calls, 0)
```

- [ ] **Step 2: Freeze and implement strict authorization verification**

The envelope has exactly:

```text
schema_version, document_type, payload, payload_sha256, artifact_sha256,
trust_evidence, trust_evidence_sha256
```

The payload binds decision `AUTHORIZE`, phase `SCREENING`, decision ID,
authorizer ID, issued time, checklist/protocol/plan/runner-contract/construction
file/construction canonical/provenance/config/dependency/source-manifest/candidate
digests, exact roots, both attempt IDs, workers=6, exact seeds/cells/methods,
output names, and expected rows=320. Verify both canonical digests and stable
non-symlink file identity. The trust-evidence object has an exact schema binding
the authorization artifact digest, signed payload digest, signature algorithm,
pinned key identifier, detached signature bytes/digest, trust-policy identifier,
and external witness identifier. A production `TrustVerifier` must verify the
detached signature and pinned policy; hash agreement alone is insufficient.
Fixture substitutes are accepted only through an explicitly test-only API that
the production CLI cannot select. Missing production trust evidence or verifier
is a hard refusal before any scientific call.

The authorization payload also binds one canonical
`frozen_v1_authority_digest` covering every path/digest in
`FROZEN_V1_AUTHORITY`, including all 45 v1 manifest entries. Authorization
preflight must stably reread and recompute every member immediately before
claim, then recheck it after tests and before accepting trust evidence. Any v1
drift refuses even when all v2 hashes match.

Both attempt IDs are deterministic authorization inputs, not values allocated
after claim:

```python
def derive_attempt_id(decision_id: str, role: str) -> str:
    material = f"R006E_SCREENING_V2_ATTEMPT\0{decision_id}\0{role}".encode("utf-8")
    return "r006e-v2-" + hashlib.sha256(material).hexdigest()
```

The authorization must bind those exact derived IDs for `primary` and `repeat`.
The control root uses one fixed pair-claim filename independent of decision ID,
so a later decision or fresh IDs cannot bypass any retained prior claim.

- [ ] **Step 3: Write RED tests for actual-directory scans**

Cover unexpected regular files, dotfiles, symlinks, FIFOs, temp files,
manifests, partial outputs, v1 roots, root swapping, and caller-supplied name
spoofing. Primary v2 permits only its exact v2 construction artifact/manifest;
repeat and control must be empty before claim.

- [ ] **Step 4: Implement descriptor-backed scans and pair claim**

```python
def scan_v2_roots(paths: ScreeningV2Paths) -> RootSnapshot: ...
def claim_screening_pair(
    authorization: ScreeningAuthorization,
    snapshot: RootSnapshot,
) -> PairClaimToken: ...
def start_screening_role(
    claim: PairClaimToken, role: Literal["primary", "repeat"]
) -> AttemptToken: ...
def derive_attempt_state(paths: ScreeningV2Paths, role: str) -> AttemptState: ...
```

Open directories with `O_DIRECTORY` and `O_NOFOLLOW` where available, compare
pre/post directory identities, publish claims exclusively with the existing
durable hard-link primitive, and fsync directories. Never delete attempt files.

- [ ] **Step 5: Add concurrency/crash/deletion tests**

Prove only one concurrent claim succeeds; derived attempt IDs match the
authorization; a later decision/new IDs cannot bypass a retained singleton
claim; start-without-terminal derives `INCOMPLETE`; deletion of role outputs
does not erase the control claim; and there is no resume/reset/reclaim API.
Prove separately that a live supervisor publishes `INCOMPLETE` for an unclean
primary child death and then starts repeat, whereas supervisor death leaves the
pair permanently `INCOMPLETE` and no later process may start the missing role.

- [ ] **Step 6: Run focused ledger tests**

Expected: all tests `OK`, scientific spy calls remain zero.

### Task 4: Implement Screening Cell Execution And Failure Retention

**Files:**
- Create: `scripts/experiments/r006e_screening_executor_v2.py`
- Create: `scripts/experiments/test_r006e_screening_executor_v2.py`
- Modify only if required by a reviewed RED test: `scripts/experiments/r006e_native_metrics.py`

- [ ] **Step 1: Write a fixture-only RED test for exact task enumeration**

Require 80 ordered cell tasks and four ordered method identities per task.
Freeze `method_seed = keyed_seed(seed, rho, a3, eta, "optimizer")`.

- [ ] **Step 2: Implement the single scientific cell boundary**

```python
def run_screening_cell(
    task: ScreeningCellTask,
    *,
    construction_certificate: Mapping[str, object],
    config: R006EConfig,
) -> CellExecution:
    """Return four replication, diagnostic, resource, and journal records."""
```

The function constructs the native panel, reconstructs endpoints, verifies
design-input/endpoint/family-index/support/stream hashes against the frozen
certificate before fitting, fits the three required comparators plus candidate,
and calls `evaluate_method` only after fit completion. Truth never enters a fit
API. Peak RSS scope includes panel construction, certificate verification, fit,
and evaluation in one fresh worker.

- [ ] **Step 3: Add vertical tests for certificate mismatch before fitting**

Use spies to prove every design/endpoint/stream mismatch refuses with zero fit
and evaluation calls. No endpoint redraw or fallback is permitted.

- [ ] **Step 4: Implement schema-complete runner-failure retention**

Add a v2 runner-failure row envelope rather than fabricating evaluator success.
For a cell-level exception, emit exactly four retained method identities with
scientific fields null, deterministic failure code/reason, construction support
provenance, four method-level diagnostic records, four resource records, and
four row-journal records. The v2 gate adapter must force all nine conditions
false for any runner-failure row.

- [ ] **Step 5: Add crash/worker-failure tests**

One failed cell still produces four identities in each record class. A complete
fixture role produces exactly 320 replication, 320 diagnostic, 320 resource,
and 320 row-journal records with identical identity sets. No selective
resubmission or row replacement API exists.

- [ ] **Step 6: Run executor tests only with fixtures/spies**

Expected: all tests `OK`; do not invoke the formal DGP in tests marked
`governance_only`.

### Task 5: Implement Deterministic Outputs And Gate Recalculation

**Files:**
- Create: `scripts/experiments/r006e_screening_outputs_v2.py`
- Create: `scripts/experiments/test_r006e_screening_outputs_v2.py`

- [ ] **Step 1: Write RED tests for canonical CSV/JSONL bytes**

Require LF endings, UTF-8, exact header order, deterministic row order, no NaN,
and exclusive publication. Parsing each of replication, diagnostic, resource,
and row-journal bytes must reproduce the same exact 320 identities.

- [ ] **Step 2: Implement byte serializers and exclusive publishers**

Use `_atomic_write` only for new files. Never call cleanup on an attempt or
outcome file. Each role has one fixed row-journal JSONL, replication CSV,
diagnostic JSONL, resource JSONL, summary CSV, result JSON, terminal JSON, and
manifest. Publish them in exactly that order. The manifest binds the four
320-record cardinalities, their common identity-set digest, and every raw hash.

- [ ] **Step 3: Implement pure summary construction**

Build exactly eight ordered rows from `evaluate_screening_gate`. Store the nine
named flags, canonical failed-condition list, and canonical audit-values JSON.
Add equality-edge tests for every gate.

- [ ] **Step 4: Implement general PASS-or-FAIL result verification**

The result status must exactly equal the recomputed gate status. It binds only
the semantic replication digest, semantic summary digest,
construction/config/candidate/provenance digests, exact seed list, and separate
identity-completeness result. Diagnostics have no semantic result digest. Every
diagnostic/resource/journal raw hash belongs only to the terminal/manifest.

- [ ] **Step 5: Add post-publication stable reread tests**

Mutate or replace any replication/summary/result/diagnostic/resource/journal
file between computation and final verification and require failure without
deleting any file. Operational drift fails manifest integrity but does not
silently expand the three-payload scientific duplicate comparison.

- [ ] **Step 6: Run focused output tests**

Expected: all tests `OK`.

### Task 6: Implement Pair Orchestration And Screening-Only CLI

**Files:**
- Create: `scripts/experiments/r006e_screening_v2.py`
- Create: `scripts/experiments/test_r006e_screening_v2.py`

- [ ] **Step 1: Write RED CLI tests**

Freeze phases `construction-v2`, `verify-authorization`, and `screening-pair`;
require exact `--workers 6`, exact v2 roots, and an authorization path for
`screening-pair`. Missing authorization, absent trust evidence, root mismatch,
or any source drift refuses before a scientific spy call.

- [ ] **Step 2: Implement unconditional pair orchestration**

The persistent pair supervisor claims both roles first, then launches each role
as a child process. A clean role completion publishes `PASS` or `FAIL`. If a
role child exits without its own terminal while the supervisor remains alive,
the supervisor exclusively publishes `INCOMPLETE`; after any primary terminal
state it launches repeat. A caught, schema-complete scientific failure is
`FAIL`, not `INCOMPLETE`. Never rerun a role. Compare only two complete
replication/summary/result payload sets; incomplete roles produce pair integrity
`FAIL`. If the supervisor itself dies, the orphaned pair remains permanently
`INCOMPLETE`, no replacement supervisor is permitted, and unconditional-repeat
completion is not claimed.

- [ ] **Step 3: Implement worker orchestration**

Accept only workers=6. Enumerate exactly 80 tasks. Each task runs in a fresh
process and returns exactly four rows or four retained failures. Sort by frozen
identity before publication; scheduling order cannot affect bytes.

- [ ] **Step 4: Add end-to-end fixture tests**

Use injected fixed cell runners only. Cover primary PASS/repeat PASS match,
primary FAIL/repeat mandatory, worker crash retention, duplicate mismatch,
source drift, prior claim, missing production authorization, role-child death
with a live supervisor, and supervisor death before repeat. No formal DGP or
estimator call is allowed in these tests.

- [ ] **Step 5: Run focused CLI/orchestration tests**

Expected: all tests `OK` and no workspace v2 artifacts.

### Task 7: Add Independent Result/Claim Audit

**Files:**
- Create: `scripts/experiments/r006e_result_claim_audit_v2.py`
- Create: `scripts/experiments/test_r006e_result_claim_audit_v2.py`

- [ ] **Step 1: Write RED tests for independent recalculation**

Require rejection of missing/duplicate identities, stored/recomputed gate
disagreement, duplicate mismatch, manifest mismatch, and claims beyond
simulation-only recovery.

- [ ] **Step 2: Implement audit from raw stable files**

Do not call the executor's summary/result builders. Parse replication bytes,
independently reconstruct identity coverage and gate inputs, recompute all nine
conditions, verify primary/repeat semantics, and classify claim scope.

- [ ] **Step 3: Run focused audit tests**

Expected: all tests `OK` using fixtures only.

### Task 8: Implement Outcome-Free V2 Construction Contract

**Files:**
- Create: `scripts/experiments/r006e_construction_v2.py`
- Create: `scripts/experiments/test_r006e_construction_v2.py`
- Update protocol generated in Task 1 with the final frozen closure

- [ ] **Step 1: Write RED tests for the exact construction schema**

Freeze strict artifact and manifest schemas plus public APIs
`build_construction_v2(paths, *, scientific_spy)` and
`verify_construction_v2(paths)`. The artifact must bind status
`CONSTRUCTION_PASS`, exact v2 roots, the current plan/protocol paths, the
reserved future-checklist path plus an explicit `ABSENT_NOT_AUTHORIZED`
pre-construction absence certificate, all v2 source/test files, inherited
scientific dependencies, test-command results, dependency/config/candidate
digests, seed-cell certificates, and fresh canonical/provenance/source-closure
digests. Unknown, missing, non-finite, or outcome fields are rejected. The
later checklist binds the completed construction; it is not retroactively
inserted into the already-frozen source closure.

- [ ] **Step 2: Freeze `V2_SOURCE_PATHS` and `V2_TEST_COMMANDS`**

`V2_SOURCE_PATHS` contains this plan, the v2 protocol, every v2
implementation/test module from Tasks 1-8, and every inherited
R006e scientific module whose bytes can influence construction or future
screening. `V2_TEST_COMMANDS` contains every focused v2 test command plus all
existing R006e and inherited R006c/R006d construction tests. Both collections
are ordered, duplicate-free, content-addressed, and verified against the current
filesystem; the builder may not inherit the v1 closure by implication. The
reserved checklist path is schema-bound separately as absent and therefore is
not falsely treated as an existing content-addressed source.

Separately freeze `FROZEN_V1_AUTHORITY_PATHS` and their checklist-declared
digests: the exact external checklist and sidecar paths stated above;
`docs/superpowers/plans/2026-07-16-r006e-native-supported-recovery.md`;
`refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md`; the v1
runner, protocol module, gate module, runner tests, and gate tests named by the
checklist immutable-identity table; the two exact construction files stated
above; the complete 45-entry manifest/source-hash set; and the
configuration/dependency/import/candidate identities. Also freeze the direct
inventories of the exact v1 primary and repeat roots, including whether the
repeat root is absent or empty. The v2 construction artifact binds their
canonical aggregate digest; none is omitted merely because it is not a v2
source dependency.

- [ ] **Step 3: Implement outcome-free build and independent verification**

The builder may read v1 and scientific sources but may write only
`r006e_native_supported_recovery_v2/construction_gate_preoutcome.json` and
`construction_manifest.sha256`. It may construct/verify the frozen seed-cell
certificates required by the construction contract, but must not call any fit,
evaluation, screening gate, confirmation, or R006f function. The verifier
recomputes the complete closure and digests from stable files without trusting
stored status.

- [ ] **Step 4: Add no-outcome and no-v1-write tests**

Use spies and before/after byte hashes to prove zero fit/evaluation/gate calls,
zero writes to both v1 roots, zero writes to v2 repeat/control roots, refusal on
source/test/plan/protocol drift, and exclusive creation of only the two allowed
v2 construction files. Tests run entirely in temporary roots.

- [ ] **Step 5: Run focused construction tests**

Expected: all tests `OK`, scientific spy calls remain zero, and no workspace
construction artifact is generated yet.

### Task 9: Full Pre-Outcome Review And V2 Construction Freeze

**Files:**
- Generate only after dual review:
  - `output/high_impact_revision/r006e_native_supported_recovery_v2/construction_gate_preoutcome.json`
  - `output/high_impact_revision/r006e_native_supported_recovery_v2/construction_manifest.sha256`
- Create after construction audit:
  - `refine-logs/R006E_SCREENING_EXECUTION_AUTHORIZATION_CHECKLIST_V2_20260718.md`
  - detached checklist SHA-256 sidecar

- [ ] **Step 1: Run every R006e and inherited construction test**

Run the exact frozen `V2_TEST_COMMANDS`, `py_compile`, whitespace checks,
forbidden-marker scans, and stably recompute every member and all 45 manifest
entries in `FROZEN_V1_AUTHORITY_PATHS`; confirm both v1 root inventories remain
unchanged. This explicitly verifies the external checklist and its detached
sidecar as governance records plus the two runner construction files; it does
not look for a checklist in the runner's artifact schema.

- [ ] **Step 2: Obtain specification and code-quality approval**

Review exact schemas, scientific boundary, failure retention, directory races,
attempt irreversibility, output recomputation, duplicate semantics, and claim
scope. Fix every finding and repeat both reviews until approved.

- [ ] **Step 3: Run only `construction-v2`**

The reviewed Task 8 command may write only the v2 construction artifact and
manifest. It must instantiate no screening fit/evaluation, screening gate,
confirmation panel, or R006f code path.

- [ ] **Step 4: Independently audit v2 construction**

Require outcome-free content, complete seed-cell certificates, exact
`V2_SOURCE_PATHS`, exact `V2_TEST_COMMANDS`, current plan/protocol closure,
fresh provenance, exact versioned roots, and no v1 changes.

- [ ] **Step 5: Freeze a new v2 checklist as `NOT_AUTHORIZED`**

The checklist records absent production authorization/trust evidence and keeps
`screening-pair` closed. Stop before `verify-authorization` and all scientific
outcome execution.

## Final Stop Condition

This nine-task plan is complete only when v2 code/tests/schemas and the
outcome-free v2 construction contract are independently approved, v1 is
byte-for-byte unchanged, and the v2 checklist is hash-locked
`NOT_AUTHORIZED`. Production authorization/trust evidence remains absent.
Formal screening, confirmation, manuscript claims based on R006e outcomes, and
R006f outcomes remain unexecuted.
