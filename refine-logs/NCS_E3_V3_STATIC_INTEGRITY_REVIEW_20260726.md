# NCS E3 v3 Static Integrity Review

Date: 2026-07-26

Scope: read-only review of the E3 Family-2 v3 source boundary, eight
pre-outcome artifacts, fixture tests, v3 input and historical v2 quarantine
identity records. No scientific grid was run.

## Initial Findings And Remediation

| Finding | Initial classification | Remediation | Current state |
| --- | --- | --- | --- |
| The executed `e3_synthetic_core.py` was not mandatory in candidate source closure. | BLOCKING | Production preflight now requires the exact hash of the imported core before issuing an execution capability; the candidate builder already binds the same core. | CLOSED |
| Fixture-only authorization validation did not invoke v3 bootstrap-history cross-binding. | NONBLOCKING | Fixture supervisor now calls `_validate_bootstrap_history_bindings`; regression test exercises refusal when the cross-binding rejects. | CLOSED |
| Candidate builder validated only selected v3 fields and could defer drift rejection to execution preflight. | NONBLOCKING | Builder pins the exact SHA-256 of `synthetic-e3-v3.json` and rejects byte-level drift before materialization. | CLOSED |
| Executor mismatch text still said `v1`. | NONBLOCKING | Error text now identifies frozen v3. | CLOSED |

## Integrity Checks

| Check | Result | Boundary |
| --- | --- | --- |
| Ground-truth provenance | WARN | Synthetic references are simulation truth; proof-review receipt is source-only and not empirical evidence. |
| Score normalization | PASS | No self-normalization or metric laundering found. |
| Result existence/promotion | PASS | Historical quarantine outputs remain quarantine-only and are not wired into manuscript activation. |
| Dead code | PASS | Recursive bootstrap, per-replicate retuning and status retention are reachable from the interval route. |
| Scope language | WARN | Scope is synthetic and source-only; no broad recovery or application language is released. |
| Evaluation type | PASS | Synthetic simulation plus static governance, not public-data or empirical evaluation. |
| Recursive bootstrap semantics | PASS | Observed-prefix initialization, pseudo-history lag rebuilding, new `FitData`, retuning and status retention are all bound. |
| Minimum-history gate | PASS | Every allowed rank requires at least two valid causal refit opportunities; threshold relaxation and stable-cell selection are prohibited. |
| Candidate closure | PASS after remediation | Core, executor, preflight, artifacts, v3 input, parameters and isolated root are bound for any future candidate; no candidate currently exists. |

## Fresh Verification

```text
PYTHONDONTWRITEBYTECODE=1 /Users/wuyilin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest scripts.experiments.test_e3_synthetic_core scripts.experiments.test_e3_family2_synthetic_runner scripts.experiments.test_e3_family2_preoutcome scripts.experiments.test_e3_family2_candidate_package scripts.experiments.test_e3_family2_authorized_executor
Ran 64 tests in 0.756s
OK

PYTHONDONTWRITEBYTECODE=1 /Users/wuyilin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m scripts.experiments.e3_family2_preoutcome verify --input refine-logs/e3_family2_preoutcome.json
status: SOURCE_ONLY_VERIFIED
scientific_execution: NOT_AUTHORIZED
production_execution: UNAVAILABLE
```

An independent targeted re-review confirmed all three remediation findings are
closed. The reviewer did not edit files, create a candidate, reserve an output
root, issue authorization, run science, promote a claim or change either
controlling audit.

## Release Boundary

This review supports source integrity and future candidate readiness only. It
does not support recovery, uncertainty coverage, stability, cross-generator
generality, public-network impact or manuscript promotion. `PAPER_CLAIM_AUDIT`
remains `BLOCKED`; `EMPIRICAL_IMPLEMENTATION_AUDIT` remains `FAIL`; E3-1 through
E3-4 remain `NOT_AUTHORIZED` in the tracker.
