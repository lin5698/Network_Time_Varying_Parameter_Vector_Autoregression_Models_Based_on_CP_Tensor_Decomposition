# NCS E3 Family-2 Authorization Readiness

Date: 2026-07-22

Status: `SOURCE_ONLY_VERIFIED`; `PRODUCTION_EXECUTION_UNAVAILABLE`.

This record is an authorization-readiness audit only. It authorizes no
scientific execution, data acquisition, dependency installation, RCEP/NYC
inspection, R006e/R006f outcome access, manuscript build, upload or claim
promotion. `PAPER_CLAIM_AUDIT=BLOCKED` and
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling restrictions.

## Verified Static State

The following checks were run without scientific inputs, topology generation,
fitting, response evaluation or scientific output creation:

- `python3 -m unittest scripts.experiments.test_e3_family2_preoutcome`: 16
  fixture-only tests passed.
- `python3 -m scripts.experiments.e3_family2_preoutcome verify --input
  refine-logs/e3_family2_preoutcome.json`: returned
  `SOURCE_ONLY_VERIFIED`, `NOT_AUTHORIZED` and
  `production_execution=UNAVAILABLE`.
- `py_compile` passed for the static pre-outcome module, its artifact-schema
  module and the fixture-only test module.

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
| Eight pre-outcome artifacts | Schemas and source-only instances verify, but none is `CANDIDATE_READY`. | Semantically complete, versioned candidate-ready artifacts with actual frozen content and hashes for every required ID. | Changing lifecycle labels, retaining empty fields, or accepting matching hashes for semantically incomplete artifacts. |
| Scientific runner | Absent by design. `e3_family2_preoutcome.py` exposes only static construction and verification. | A separately scoped, reviewed synthetic-only runner with no route to RCEP, NYC, R006e or R006f. | Treating the static preflight module or a fixture callback as a scientific runner. |
| Source/dependency closure | Only the static boundary is currently hashable. | Exact runner, schema and dependency file hashes, all resolving within the reviewed source boundary. | Unpinned imports, mutable local dependencies or a changed runner after hashing. |
| Synthetic inputs | No production input binding exists. | Existing files named `synthetic-*`, each with a frozen path and SHA-256. | Generating or replacing inputs after authorization, or binding an external/provider route. |
| Configuration | Family/endpoint semantics are specified; run-specific grids remain unset. | Frozen topology generators, scales, panel lengths, horizons, seeds, splits, tuning budget and comparator list, plus canonical configuration SHA-256. | Selecting values after seeing response truth, recovery or stability outcomes. |
| Comparator registry | Endpoint rules are frozen; source identities and native evaluators are not bound. | Exact source identities, parameterizations and native `fit/evaluate` endpoint proofs for every rankable comparator. | Projected, post-hoc or collapsed-map rows entering a numerical ranking. |
| Production trust | Fixture trust is explicitly rejected; no configured production verifier or signature is present. | Configured key/policy identifiers and a detached signature that verifies the canonical candidate payload. | Test-only verifier, missing verifier or an unchecked signature. |
| Candidate document and SHA | No production candidate exists. | One schema-v1 candidate with an exact SHA-256 derived from the reviewed bytes. | Approving a template, a mutable path or a SHA that was not independently recomputed. |
| Quarantine root | No root is reserved. | A new, absolute, empty path whose name contains `quarantine`, bound identically in candidate and preflight. | Reusing an existing root or redirecting output after approval. |
| User authorization | No candidate-specific execution authorization is recorded. | Explicit approval naming the exact candidate SHA and limiting scope to one synthetic-only invocation. | Interpreting this readiness record, source-only tests or a general request to continue as execution authority. |

## Fail-Closed Evidence

The fixture suite proves the following source-bound properties:

1. Missing candidate authorization refuses before any topology generator,
   estimator or response evaluator is called and before a quarantine root is
   created.
2. A test-only trust verifier is rejected before any scientific callback is
   reachable.
3. A SHA-bound fixture candidate can produce only a
   `PREPARED_NO_EXECUTION` receipt; the static module has no execution command.
4. Every empty or semantically incomplete candidate-ready artifact is refused
   before scientific hooks are reachable.

These are governance and static-safety results, not numerical validation of
Family 2, a recovery result or a manuscript claim.

## Earliest Legitimate Candidate Sequence

1. Separately authorize implementation review of a synthetic-only E3-1 runner
   and of the exact candidate-ready artifacts. This is not a scientific run.
2. Independently review the runner, comparator native-endpoint proofs,
   synthetic-input route and frozen configuration.
3. Materialize one candidate, compute its SHA-256, configure production trust
   verification and run the read-only preflight. A successful receipt remains
   `PREPARED_NO_EXECUTION`.
4. Obtain a new explicit user authorization that names that exact SHA-256 and
   its single isolated output root.
5. Only then may a separately reviewed execution engine be considered. Any
   resulting files remain quarantined pending duplicate and result-to-claim
   audits; they do not activate C1, C2, C3 or manuscript promotion by default.

## NCS Relevance

The only NCS-facing purpose of this future route is to test whether the
query-preservation boundary survives a genuinely distinct second operator
family. It cannot be substituted for the required same-endpoint recovery,
held-out topology, uncertainty/stability or consequential-application blocks.

## Current Decision

Do not create or approve a production candidate yet. The next permitted work
is source-only implementation and independent review of the missing
candidate-ready components. A candidate-specific scientific authorization is a
separate future decision.
