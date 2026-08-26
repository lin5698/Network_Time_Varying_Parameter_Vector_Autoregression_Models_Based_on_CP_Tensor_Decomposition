# NCS E3 Native Endpoint Interface Proof

Date: 2026-07-23

Status: `SOURCE_ONLY`, `PRE_OUTCOME`, `NOT_AUTHORIZED`.

This source note documents the native interface that a later E3-2 candidate
must hash-bind. It records no fit, endpoint, loss, rank, runtime, bootstrap or
application result.

## Contract

Every rankable method must implement the conceptual interface

```text
fit(training_histories, observed_training_topologies, frozen_hyperparameters)
evaluate(fitted_state, W_q, H) -> {G, R_1:H, status}
```

The concrete synthetic implementation is
`scripts/experiments/e3_synthetic_core.py`:

- `FitData` contains only the observed topology history and responses. It does
  not contain a held-out topology or its response truth.
- `make_synthetic_panel`, `fit_native_path`, `select_hyperparameter`,
  `evaluate_method_at_query`, `evaluate_panel_recovery`,
  `simultaneous_response_interval`, and `NativePath.evaluate` each first run
  the exact E3-1 fixture gate. A failed classification therefore prevents a
  public generator, fit, selection or endpoint evaluation call.
- `fit_native_path(FitData, method, frozen_hyperparameter)` freezes a method
  state without accepting `W_q` and returns a public `NativePath` handle.
- `NativePath.evaluate(query_topology, horizon, target_time)` evaluates a
  supplied query only after that gate has passed. Its private backing state
  causally estimates the retained coefficient blocks and forms the complete
  endpoint directly from them.
- The block estimator and operator/response constructors are private module
  helpers (`_estimate_native_blocks`, `_native_endpoint` and related helpers),
  rather than alternate public fit or endpoint routes. They remain covered by
  source-level fixture tests but do not constitute a callable E3 interface.

No projection from an embedding, graph feature, collapsed map or post-hoc
response adapter occurs in this path.

## Eligible implementations

| Comparator ID | Role | Retained state | Direct endpoint route |
| --- | --- | --- | --- |
| `local_structured` | `native_local_structured` | rowwise Family-1 `A,B` or Family-2 `C0,C1,C2` blocks | local causal ridge fit -> `native_endpoint` |
| `causal_temporal_smoother` | `causal_temporal_structured` | the same separate blocks after one-sided smoothing | causal smoother -> `native_endpoint` |
| `fixed_rank_basis` | `fixed_low_rank_or_basis` | the same separate blocks after a one-sided rank-restricted reconstruction | fixed-rank basis path -> `native_endpoint` |

The candidate lists and selection rule are frozen in
`refine-logs/e3_family2_inputs/synthetic-e3-v1.json`. Tuning receives only a
`FitData` object and uses observed-topology one-step prediction loss. A
held-out topology enters only `NativePath.evaluate` after the selected
hyperparameter is fixed.

## Ineligible control

`collapsed_endpoint_control` returns `OUTSIDE_TARGET` with no blocks,
operator, response sequence, loss or rank. It may illustrate unavailable
query semantics but cannot enter a recovery table.

## Boundary

This interface proof does not establish that a method converges, is stable,
recovers a held-out endpoint, provides calibrated intervals or outperforms a
comparator. Those are later E3-2 to E3-4 questions and require an exact
candidate, isolated execution and independent audit.
