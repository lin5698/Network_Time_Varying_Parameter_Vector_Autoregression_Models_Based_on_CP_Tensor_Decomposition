# R006e Recovery And Support Split Route

**Date:** 2026-07-15  
**Status:** route decision only; no implementation or outcome execution authorized

## Decision

R006d is closed as `CONSTRUCTION_FAIL`. Its single experiment combined two questions that the current DGP cannot jointly test:

1. whether design-weighted joint estimation improves native recovery at supported endpoints;
2. whether the method abstains when a topology query contains an unexcited direction.

The corrected R006c design supports the first question but not the second. All residualized topology designs were full rank under the frozen numerical rule, so every candidate query had `chi_tau` at machine precision.

## Track A: Supported-Endpoint Recovery

Use a new protocol label and retain the unchanged R006c native/matched grid, `W_ref`, `W_alt_interp` and the construction-validated cross-family `W_alt_family`. Compare one fixed design-weighted joint Tucker estimator with the four declared comparators and orthogonalized controls. Remove abstention from the promotion gate and add continuous query-amplification diagnostics based on the retained Gram. Do not call full rank proof of accurate recovery.

Track A may be implemented only after a complete replacement protocol freezes the normalized objective, optimizer diagnostics, endpoint identities, confirmation contrasts and the interpretation of query amplification. R006d outputs cannot be relabeled as Track A outcomes because no estimator was run.

## Track B: Exact Support And Abstention

Create an independent construction with a prespecified rank-`r` topology-exposure subspace. Let training perturbations have the form

```text
Delta W_t = U C_t V'
```

where `U` has `r<N` orthonormal columns, `V' 1=0`, coefficients are bounded so `W_ref+Delta W_t` remains nonnegative, and row sums remain one without nonlinear renormalization. Then every exposure `(Delta W_t)x_t` lies in `span(U)`.

Freeze one supported query with columns in `span(U)` and one unsupported query with a nonzero `span(U_perp)` component. Track B tests exact kernel/projector algebra, certificate classification and query-error decomposition only. It is not eligible to promote the estimator or rescue a Track A failure.

## Theory Consequence

The support report must contain two quantities:

- `chi_tau`: the share of query action in discarded directions;
- `alpha_tau`: inverse amplification of the retained query action under the residualized Gram.

`chi_tau=0` rules out an unsupported remainder but says nothing by itself about variance. Statistical recovery claims require `alpha_tau`, absolute singular scales and noise/score control.

## Frozen Boundaries

Manuscript edits, R007, scale expansion, native GNN baselines, uncertainty work and EIA outcome inspection remain frozen. The next permitted action is protocol drafting and audit for Track A and Track B, not estimator outcome generation.
