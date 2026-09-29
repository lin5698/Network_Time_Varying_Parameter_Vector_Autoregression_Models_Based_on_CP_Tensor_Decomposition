# NCS E3 Family-2 Authorization Readiness

Date: 2026-07-23

Status: `SOURCE_ONLY_AND_EXECUTION_GATE_VERIFIED`; `STATIC_CANDIDATE_PREFLIGHT_PASS`; `SCIENTIFIC_EXECUTION_NOT_AUTHORIZED`.

This record is an authorization-readiness audit only. It authorizes no
scientific execution, data acquisition, dependency installation, RCEP/NYC
inspection, R006e/R006f outcome access, manuscript build, upload or claim
promotion. `PAPER_CLAIM_AUDIT=BLOCKED` and
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling restrictions.

## Verified Static State

The following checks were run without scientific inputs, topology generation,
  fitting, response evaluation or scientific output creation:

- `python3 -m unittest scripts.experiments.test_e3_synthetic_core
  scripts.experiments.test_e3_family2_preoutcome
  scripts.experiments.test_e3_family2_synthetic_runner
  scripts.experiments.test_e3_family2_candidate_package
  scripts.experiments.test_e3_family2_authorized_executor`: 51 fixture-only
  and static-gate tests passed.
- `py_compile` passed for the E3 core, static artifact/pre-outcome modules,
  candidate-package builder, authorized executor and their new gate test.
- The refreshed `e3-authorization-gate-test-receipt-20260723.json` binds the
  current authorization-executor test SHA-256 as an additional source-only
  suite. The receipt itself remains `NOT_AUTHORIZED`.

The verified pre-outcome contract SHA-256 is
`e7e4faaf96ace52e47359b6ffe645bf7536a7fa26a0a9ec385b2e9c8127fc614`.
All eight bound artifacts have lifecycle `SOURCE_ONLY` and scientific-execution
state `NOT_AUTHORIZED`. The separately bound Family-2 proof-review receipt is
`PASS` for proof packet SHA-256
`72f3ae670ea82b89e513c48f06c15d0019ea9792d8b3472df43c6a1c6cdc1efd`.
Neither fact is E3 outcome evidence.

## Production Preflight Closure Matrix

| Required preflight element | Current state | What must exist before a candidate can be reviewed | Bypass prohibited |
| --- | --- | --- | --- |
| Eight pre-outcome artifacts | The static candidate package binds all eight semantically validated `CANDIDATE_READY` artifacts, its proof receipt, node-order binding and test receipt. | These files must remain unchanged through exact-SHA preflight. | Changing lifecycle labels, retaining empty fields, or accepting matching hashes for semantically incomplete artifacts. |
| Scientific runner | `e3_family2_authorized_executor.py` is implemented and fixture-tested, but has not received a candidate-specific execution approval. It excludes RCEP, NYC, R006e and R006f. | Exact candidate binding of the executor source and a one-time exact-SHA workspace-author authorization. | Treating `e3_family2_preoutcome.py`, a fixture callback or a broad consent as an execution authorization. |
| Source/dependency closure | The candidate builder hashes the pre-outcome boundary, schemas, candidate-ready builder, package builder, E3 core and authorized executor. Preflight rechecks the current executor source. | A candidate whose closure and dependency-lock SHA-256 values survive preflight unchanged. | Unpinned imports, mutable local dependencies or a changed runner after hashing. |
| Synthetic inputs | The frozen `synthetic-e3-v1.json` exists; a node-order manifest is generated only as a static candidate input. | An exact binding of those two synthetic inputs, with the node-order hash matched to the Family-2 query contract. | Generating or replacing inputs after authorization, or binding an external/provider route. |
| Configuration | The executor accepts only the full frozen E3 v1 specification and derives the configuration it checks against the candidate hash. | Frozen topology generators, scales, panel lengths, horizons, seeds, splits, tuning budget and comparator list, plus canonical configuration SHA-256. | Selecting values after seeing response truth, recovery or stability outcomes. |
| Comparator registry | Candidate-ready static records bind the native endpoint interface, source identity, parameterization and evaluator proof for the three declared methods. | The records must validate as part of one candidate package. | Projected, post-hoc or collapsed-map rows entering a numerical ranking. |
| Production trust | The trust model is a workspace-author's separately recorded exact candidate-SHA instruction, not a cryptographic signature or general-purpose trust root. | The author must name the exact candidate SHA and one-time scope; the resulting authorization JSON records those fields and its own SHA is checked by the executor. | Test-only verifier, a missing authorization file, a mutable path or an unchecked SHA-256. |
| Candidate document and SHA | `e3-family2-synthetic-v1-20260723-run1` is a static candidate at `refine-logs/e3_family2_candidates/e3-family2-synthetic-v1-20260723-run1/candidate.json`, SHA-256 `5974a68832587092580b64c141128469dd06376bd279477e9a3bf81e5b8120c8`. | An explicit one-time approval of this exact candidate SHA and its bound root must precede authorization-record creation. | Approving a template, a mutable path or a SHA that was not independently recomputed. |
| Quarantine root | No root is reserved. | A new, absolute, empty path whose name contains `quarantine`, bound identically in candidate and preflight. | Reusing an existing root or redirecting output after approval. |
| User authorization | No candidate-specific execution authorization is recorded. | Explicit approval naming the exact candidate SHA and limiting scope to one synthetic-only invocation. | Interpreting this readiness record, source-only tests or a general request to continue as execution authority. |

## Fail-Closed Evidence

The fixture suite proves the following source-bound properties:

1. Missing or mismatched candidate/authorization SHA-256 values refuse before
   topology generation, selection or quarantine-root reservation.
2. A candidate that omits the current authorized-executor source hash refuses
   even if a matching fixture authorization is constructed around that altered
   candidate.
3. Exact authorization preflight returns an opaque, non-executing capability;
   it creates neither a panel nor a quarantine root. Its E3 specification is
   retained as immutable canonical JSON rather than a caller-mutable mapping.
4. A candidate configuration that differs from the frozen E3 v1 specification
   refuses before science. The node-order manifest must also match the
   candidate's Family-2 query-contract hash.
5. A forged capability with the wrong internal token cannot reserve a root or
   start the runner.

These are governance and static-safety results, not numerical validation of
Family 2, a recovery result or a manuscript claim.

## Earliest Legitimate Candidate Sequence

1. Obtain a new explicit workspace-author authorization that names the exact
   candidate SHA-256 and its single isolated output root. Then generate the
   authorization record and verify its SHA-256 against the resulting bytes.
2. Run the executor exactly once only after successful preflight. Resulting
   files remain quarantined pending inventory freeze, duplicate run and
   independent result-to-claim audit; they do not activate C1, C2, C3 or
   manuscript promotion by default.

## NCS Relevance

The only NCS-facing purpose of this future route is to test whether the
query-preservation boundary survives a genuinely distinct second operator
family. It cannot be substituted for the required same-endpoint recovery,
held-out topology, uncertainty/stability or consequential-application blocks.

## Current Decision

The named static candidate has passed semantic preflight without execution; its
bound quarantine root is still absent. Do not execute it until an explicit
workspace-author instruction names its candidate SHA-256 and that one new
quarantine root. The subsequent authorization JSON must faithfully record this
instruction and is checked by its own SHA-256 at execution time. That candidate
precision is still required even though the user has given broad consent to run
the E3 evidence route at the appropriate time.
