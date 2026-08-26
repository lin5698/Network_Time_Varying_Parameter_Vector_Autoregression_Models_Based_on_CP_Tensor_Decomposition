# Experiment Audit Report

**Date:** 2026-07-19
**Audit timezone basis:** `Asia/Shanghai`
**Auditor:** independent Codex reviewers, read-only
**Current scope:** preserved R006c audit plus RCEP/NYC execution readiness

## Overall Verdict: FAIL

## Integrity Status: fail

## Scientific Outcome: R006c FAIL; RCEP AND NYC QUARANTINED UNREVIEWED

The preserved R006c experiment remains a procedurally sound negative method
gate. The current execution-readiness audit found no fake ground truth or
self-normalized performance claim, but the manuscript still depends on stale,
pre-correction RCEP/NYC artifacts. Static execution gates were remediated after
the review. Corrected NYC and RCEP-03 runs exist only in quarantine and remain
value-unreviewed after the rank-deficiency repair.
The overall verdict remains `FAIL`.

## E4 Pre-outcome Integrity Addendum (2026-07-31): PASS

An independent read-only reviewer rechecked the E4 domain-stability proof,
test-execution receipt, v4 schemas, eight pre-outcome artifacts and r2
candidate. The first pass found a self-declared `PASS` receipt gap. After the
candidate builder was changed to accept only a separately recorded and
validated subprocess receipt, the second pass returned `PASS` with no blocking
finding.

This is a local pre-outcome verdict only. It permits E4-R001 through E4-R005 to
be recorded as complete; it does not change this report's overall `FAIL`, the
paper-claim block, the empirical implementation failure, or E4-R006 through
E4-R009. The E4 grid was not run and the r2 quarantine root remains absent.

The controlling addendum is
`refine-logs/NCS_E4_PREOUTCOME_INTEGRITY_REVIEW_20260731.md`; the parsed trace is
`.aris/traces/experiment-audit/2026-07-31_run01/parsed-audit.json`.

### E4 r2 execution incident

The subsequently authorized r2 process created only its running manifest and
ended without a result, completion or caught-failure payload. The exact
authorization is consumed and cannot be retried. This infrastructure incident
does not change the E4 pre-outcome integrity verdict, does not constitute a
scientific result, and leaves E4-R006 through E4-R009 blocked. The controlling
record is `refine-logs/NCS_E4_R2_EXECUTION_INCIDENT_20260731.md`.

## Current Execution-Readiness Checks

### A. Ground-Truth Provenance: WARN

R006c is explicitly simulation-only. RCEP and NYC use real panels but their
topology-substitution readouts have no external ground truth and are classified
as `self_supervised_proxy`. NYC and RCEP-03 each completed one authorized
corrected run in quarantine; neither value set has been audited.

### B. Score Normalization: WARN

Declared denominator floors, clipping and small-denominator suppression are
implemented and tested. Archived RCEP aggregate ratio behavior remains
numerically unstable and cannot be used as current evidence.

### C. Result Existence and Match: WARN

Named corrected artifacts now exist in the RCEP-03 and NYC quarantines, while
the promoted RCEP/NYC CP-derived files still predate the corrected
implementation. Unresolved empirical placeholders remain unbound pending
independent value and claim audit.

### D. Dead Code and Stored Metrics: PASS

The corrected rank-selection, full-path bootstrap and weak-separation paths are
implemented and covered by focused tests. No declared metric in the reviewed
surface was found to be unreachable or test-orphaned.

### E. Scope and Manuscript Language: FAIL

The abstract and empirical Results still carry cross-domain and numerical
wording whose claim ledger status is blocked. Static code readiness cannot
support those statements without regenerated RCEP/NYC evidence.

### F. Evaluation Classification: PASS

R006c is `simulation_only`; RCEP and NYC operator checks are
`self_supervised_proxy`. No `real_gt` performance evaluation or `human_eval`
was found in the reviewed scientific surface.

## Post-Audit Static Remediation

- The runner now requires an exact authorization file and separately approved
  SHA-256 before helper import, data loading or output creation.
- NYC is independent of the RCEP helper gate.
- RCEP binds the two input CSV files actually selected by the verified helper;
  RCEP CSV and NYC NPZ inputs are parsed only from SHA-256-verified in-memory
  snapshots read through `O_NOFOLLOW` descriptors.
- Authorized outputs use an immediate no-follow quarantine reservation and
  deny existing or symlinked directories.
- Fresh CP contract, theory and candidate-audit tests pass `85/85`. They cover
  the Round 3 findings on local-import closure, dynamic import/code rejection,
  same-manifest checkout drift, validation-before-output ordering, parent-inode
  replacement and partial helper-load cleanup.
- Fresh screening-v2 governance tests pass `145/145` in 24.557 seconds under an
  isolated `/tmp` pycache prefix. These are fixture-only tests of trust refusal,
  loader mutation/failure, preclaim drift, claim publication races, rollback,
  singleton claims, post-claim sidecar refusal, terminal binding and
  schema/output contracts.
- Round 4 independently reviewed the screening preclaim and claim transaction.
  It reported no confirmed Medium-or-higher finding and had retained one Low
  post-claim allowed-entry hardening item. Round 5 independently reviewed the
  fixture-only remediation, closed that Low and reported no confirmed in-scope
  finding. The Round 3 through Round 5 records are
  `.aris/traces/security-audit/2026-07-19_run01/003-independent-blind-security-review.response.md`
  `.aris/traces/security-audit/2026-07-19_run01/004-final-post-remediation-security-review.response.md`
  and
  `.aris/traces/security-audit/2026-07-19_run01/005-fixture-only-postclaim-low-closure.response.md`.

### Scientific execution status

All RCEP and NYC exact-SHA decisions are consumed. RCEP-03 exited `0` after the
rank-deficiency repair and froze 36 files; NYC exited `0` and froze 18 files.
Both sets remain isolated and value-unreviewed. No result-value review, claim
audit, downstream build or manuscript promotion was performed.

The screening primary root still contains only its frozen construction pair:
`construction_gate_preoutcome.json` at SHA-256
`4c3139c6cfee8c452b418f09b3bf04ec977e08f8ada5eb4e8b9d032309d5f090`
and `construction_manifest.sha256` at SHA-256
`424ee25104b325bf3e63359d3f61c0d3adb97604e6c9c81d7f5bcf1a4009346b`.
Repeat and control roots are absent. The two explicitly authorized
provider-governed RCEP CSVs were read only for RCEP-03 scientific execution;
no R006e/R006f outcome was accessed.

### C3 and residual boundaries

The installed C3 manifest binds commit
`d0e398b896848f26413cf9aa9dfca15fb4e7ce64`, passes all eight required API
checks and has zero unbound local dependencies. Static inspection also records
five import-time side-effect indicators and no top-level licence. The helper was
not executed. The supportable claim is limited to static identity and
local-import closure; open-source, redistribution, side-effect-free,
execution-ready and scientific-validity claims are not supported.

`flock` is advisory and constrains cooperating writers only. An actor able to
control both role roots and the trusted control ledger is outside the local
content-addressed threat model; an external append-only witness remains a
production-authorization prerequisite. Control-first partial publication is an
intentional witness-first fail-closed abstention and has no recovery promise.
The private production verifier/certificate loader is an external-I/O boundary
not exercised by fixture tests. Python dependencies and cache directories
initialize before the CP authorization gate. None of these residuals licenses
scientific execution or outcome review.

These controls improve rigour and reproducibility but do not validate any
archived numerical result.

## Current Claim Impact

- Theory/representation claims and the negative R006c claim remain separately
  supportable within their stated boundaries.
- RCEP coefficient, interval, ratio and propagation claims remain blocked.
- NYC near-null, stability and portability claims remain blocked.
- Cross-domain empirical computability and raw-to-derived reproducibility claims
  remain blocked until corrected regeneration and independent audit.

## Preserved R006c Checks

### A. Ground-Truth Provenance: PASS

R006c is simulation-only. Analytical `A`, `B`, `M_ref`, observed operators and
endpoint truth are generated before estimation. True `B` is used only by the
explicitly ineligible oracle mechanism diagnostic.

### B. Score Normalization: PASS

Relative operator error uses the truth norm; response ratios use the declared
zero-operator baseline. Raw, stability-qualified and projected sensitivity
metrics are retained separately, and projected sensitivity is excluded from
promotion.

### C. Result Existence and Match: PASS

Independent CSV parsing found 2,160 unique rows, zero failures, 240 complete
simulation/seed cells, ten seeds in every required cell and 216 summary rows.
All 32 candidate-cell records and 64 endpoint gates recompute with zero numeric
mismatches. CP passes `0/16`; Tucker passes `6/16`; no candidate is promoted.

### D. Dead Code and Stored Metrics: PASS

The formal CLI reaches all declared construction, fitting, evaluation and gate
paths. Fresh tests pass `44/44` for R006c and `69/69` across the experiment
suite.

### E. Leakage and Causality: PASS

Held-out endpoints are absent from fitting inputs. Fused validation reconstructs
only the prefix available through each validation date, and a regression test
proves later validation estimates cannot change earlier scores.

### F. Duplicate and Provenance: PASS

Protocol, correction-addendum and seven transitive-code hashes match both
pre-outcome artifacts and result payloads. The corrected primary and repeat
runs have zero non-runtime differences; pre-correction history remains isolated.

### G. Scope: PASS

This is an `N=20`, `T=200`, simulation-only estimator gate. Broad endpoint-aware
superiority and general topology-switch claims remain unsupported.

### H. Gate Fidelity: PASS

Promotion requires one fixed candidate across both endpoints and all 16 cells.
Stress, weak-separation, collapsed, oracle and projected diagnostics cannot
rescue a required-cell failure.

## Claim Impact

- R006c overall `FAIL`: independently supported.
- `anchor_split_cp3`: unsupported, `0/16`.
- `anchor_split_tucker333`: unsupported, `6/16` (`6/8` matched, `0/8` native).
- Endpoint-aware/topology-switch superiority: unsupported.
- Matched Tucker, collapsed and oracle behavior: diagnostic only.

## Routing

Keep the manuscript, R007 confirmation and N=50/100 expansion frozen. A new
prespecified estimator question is required before further method-design work.
The detailed report is `refine-logs/R006C_AUDIT_20260715.md`.

## Prior Audit

R006b retains integrity `pass` and scientific `FAIL` after its causal-selection
correction. Its full result-to-claim record remains in `findings.md` and its
trace remains under `.aris/traces/experiment-audit/2026-07-15_run01/`.
