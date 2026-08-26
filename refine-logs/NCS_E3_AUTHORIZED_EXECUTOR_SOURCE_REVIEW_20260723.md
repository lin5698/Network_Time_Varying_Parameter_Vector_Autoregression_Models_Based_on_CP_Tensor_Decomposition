# E3 Authorized Executor Source Review

Date: 2026-07-23

Scope: source-level review of the synthetic-only E3 candidate builder and
authorized executor. This is not a scientific execution, outcome audit,
manuscript claim audit, cryptographic security assessment or a change to
`PAPER_CLAIM_AUDIT=BLOCKED` / `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`.

## Verdict

`PASS_WITH_SCOPE_LIMITS` for materializing a new static candidate and requesting
an exact-SHA workspace-author authorization. No E3 grid, bootstrap, quarantine
result root, RCEP/NYC/R006e/R006f access or manuscript promotion occurred.

## Verified Source Properties

| Check | Source evidence | Result |
| --- | --- | --- |
| Exact authority precedes science | `prepare_authorized_execution()` validates the candidate SHA and authorization SHA before returning a capability; `main()` calls `execute_authorized_e3()` only after that preflight. | Pass |
| Candidate closure includes live executor | The package builder adds `e3_family2_authorized_executor.py` to `source_hashes`; preflight requires its current file hash. | Pass |
| Frozen route and configuration | The executor accepts only the complete E3 v1 JSON, derives the execution configuration from it, and rejects configuration drift. | Pass |
| Node-order provenance | The candidate node-order JSON is hash-checked and matched to the `family2_query_contract` artifact. | Pass |
| Runtime reproducibility | The sole dependency lock is hash-checked and must match the current Python implementation/version and NumPy version. | Pass |
| No authorization-path science | The new tests prove missing or mismatched authorization, missing executor closure, configuration drift and runtime dependency drift all reject before panel generation or root creation. | Pass |
| Immutable approved specification | The capability retains canonical JSON bytes rather than candidate/authorization mappings that a normal caller could mutate after preflight. | Pass |
| Quarantine-only output | The sole execution writer is reached after root reservation and stamps all result states as quarantine-only with promotion prohibited. | Pass |
| Scope exclusions | The candidate schema and executor require `synthetic_only` and exclude RCEP, NYC, R006e and R006f. No manuscript-build import or call occurs in these modules. | Pass |

## Regression Evidence

The following command completed successfully on 2026-07-23:

```text
python3 -m unittest \
  scripts.experiments.test_e3_synthetic_core \
  scripts.experiments.test_e3_family2_preoutcome \
  scripts.experiments.test_e3_family2_synthetic_runner \
  scripts.experiments.test_e3_family2_candidate_package \
  scripts.experiments.test_e3_family2_authorized_executor
```

Result: `51` tests passed. The companion `py_compile` check passed for all E3
source and gate-test modules. These are fixture-only/static tests; none invokes
`execute_authorized_e3()` with a valid capability.

## Scope Limits

1. An exact-SHA workspace-author instruction is an operational approval record,
   not a detached cryptographic signature or an adversarial sandbox. A user
   with arbitrary Python execution in the workspace can always alter local
   source or bypass process rules; the gate prevents ordinary pipeline misuse
   and detects source/configuration drift before the approved CLI path runs.
2. The source review establishes neither recovery, uncertainty calibration nor
   comparator performance. Those remain E3-1 through E3-4 questions pending
   one exact candidate-specific execution authorization.
3. The executor writes quarantine results only. A separate output inventory,
   duplicate execution and independent result-to-claim audit remain required
   before any numerical value can affect the manuscript.

## Required Next Decision

Following this review, static candidate
`e3-family2-synthetic-v1-20260723-run1` was materialized with SHA-256
`5974a68832587092580b64c141128469dd06376bd279477e9a3bf81e5b8120c8`.
Obtain one explicit workspace-author instruction that names this candidate SHA,
limits execution to its bound new quarantine root, and preserves all stated
exclusions. Generate the authorization JSON only after that instruction and
verify its SHA-256 at invocation time. Broad consent to run E3 is not a
substitute for this exact candidate binding.
