# NCS E3 v3 Recursive-Bootstrap Candidate Readiness

Date: 2026-07-26

Status: source and fixture review boundary only. No v3 candidate package,
execution authorization, scientific execution, downstream build, manuscript
promotion or audit-status change is created by this record.

## Decision

Any future E3 candidate must use the v3 uncertainty contract. The historical
v1 and v2 candidates remain immutable records of their original semantics and
must not be relabelled as recursive or retuned. In particular, a candidate
bound to `synthetic-e3-v1.json` or `synthetic-e3-v2.json` cannot inherit the v3
implementation by source substitution.

The v3 source boundary is defined by
`refine-logs/e3_family2_inputs/synthetic-e3-v3.json` and the current bound
source files. It replaces the fixed-design bootstrap design for future
candidate construction, but it does not repair, reopen or promote any
historical quarantine outcome.

## Required v3 Semantics

| Contract element | Frozen v3 requirement | Refusal condition |
| --- | --- | --- |
| Pseudo-series generation | Recursive residual circular moving-block bootstrap | Lagged features remain fixed at the observed response history |
| Initialization | Observed prefix before the rank-aware first refit time | Pseudo-responses are used before a valid causal history exists |
| Lag construction | Rebuild every lag feature from the pseudo-response history available at that time | Any later pseudo-response uses the original observed lag in place of pseudo-history |
| Bootstrap fitting | Construct a new `FitData` object for each pseudo-series | The original panel response array is reused as the bootstrap fitting object |
| Parameter selection | Retune the fixed-rank method by validation loss on every pseudo-series over ranks `[1, 2, 3]` | The original selected rank is silently reused for the reported bootstrap endpoint |
| Target refit | Rebuild features and refit at the target using the replicate-specific selected rank | The endpoint is evaluated from fixed-design coefficients |
| Failure inventory | Retain `AVAILABLE`, `OUTSIDE_TARGET`, `NONCONVERGED`, `NONFINITE` and `UNSTABLE` counts for every requested replicate | Failed replicates are dropped from the inventory or converted into numerical scores |
| Stability boundary | Keep the spectral-radius threshold at `0.98` | Threshold relaxation, post-outcome stabilization or stable-cell selection |
| Cross-generator cells | Retain every predeclared cell as a scientific operating-boundary test | An unstable cell is omitted to manufacture a stable subset |

The recursive generator may use the originally selected fixed rank to generate
the pseudo-series. The uncertainty endpoint itself must be retuned and refitted
inside each replicate. This distinction must remain visible in code review and
future Methods text.

## Minimum-History Hard Gate

The bootstrap history contract is frozen to a local window of `12`, at least
two local estimates and allowed ranks `[1, 2, 3]`. For target time `143`, the
rank-aware first refit times are:

| Rank | First valid refit time | Minimum required valid opportunities |
| --- | --- | --- |
| 1 | 14 | 2 |
| 2 | 14 | 2 |
| 3 | 15 | 2 |

Candidate construction and execution preflight must validate the opportunity
count for every allowed rank, not only the rank selected on the observed
series. A candidate must be refused before scientific code is called if any
allowed rank has fewer than two causal refit opportunities.

## Version And Binding Boundary

A future candidate must bind all of the following as one exact closure:

- input schema `e3-synthetic-input-v3`;
- execution candidate schema `e3-family2-execution-candidate-v3`;
- workspace authorization schema
  `e3-family2-synthetic-execution-authorization-v3`;
- quarantine result schema `e3-family2-synthetic-quarantine-results-v3`;
- trust policy `one-time-synthetic-only-e3-v3`;
- tuning artifact schema `e3-family2-tuning-split-v3`;
- the current recursive-bootstrap core, candidate builder, preflight,
  authorized executor and their dependencies;
- all eight versioned pre-outcome artifacts after semantic validation;
- the v3 synthetic specification, frozen parameters and a new absent
  quarantine output root.

Path existence and SHA-256 equality are necessary but insufficient. Preflight
must also compare the recursive-bootstrap procedure, minimum-history gate,
allowed rank list, target-time list and cross-generator failure policy across
the candidate configuration, tuning artifact and v3 input specification.

## Fixture Verification

The following command is permitted because it runs fixture-only unit tests and
does not call the full scientific grid:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/wuyilin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest scripts.experiments.test_e3_synthetic_core scripts.experiments.test_e3_family2_synthetic_runner scripts.experiments.test_e3_family2_preoutcome scripts.experiments.test_e3_family2_candidate_package scripts.experiments.test_e3_family2_authorized_executor
```

Fresh result on 2026-07-26: `64` tests passed in `0.580 s`.

The independent targeted re-review closed the three preflight findings that
preceded this v3 readiness record:

- the authorized executor now requires the exact hash of the imported
  `e3_synthetic_core.py` in the candidate source closure;
- the fixture-only supervisor invokes the v3 bootstrap-history cross-binding;
- the candidate builder rejects any byte-level drift from the frozen v3
  specification before materializing a candidate-ready package.

The stale executor mismatch message referring to "v1" was also corrected to
"v3". The reviewer made no repository edits and confirmed that no candidate,
output, promotion or audit-state change occurred.

This result supports source consistency and refusal-path coverage only. It does
not establish recovery, coverage, stability, cross-family generality or
practical significance.

## Remaining Gates Before Any Scientific Execution

1. Complete an independent static review of the v3 source and all eight
   artifact bindings, with blocking findings resolved.
2. Materialize a new v3 candidate in a new directory and record its exact
   SHA-256 without reusing a historical candidate or authorization.
3. Bind deployment-owned production trust evidence and a new absent quarantine
   output root.
4. Obtain a new exact, single-use scientific authorization for that candidate.
5. Run only through the authorized executor and retain every predeclared cell
   and failure status.
6. Keep every resulting value in quarantine until independent result-to-claim
   review explicitly releases a claim.

Until these gates close, E3-1 through E3-4 remain unavailable to the manuscript
and `PAPER_CLAIM_AUDIT=BLOCKED` and
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain unchanged. The current closure
raises source confidence; it does not create scientific evidence.
