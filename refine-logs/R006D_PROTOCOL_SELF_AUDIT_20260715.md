# R006d Protocol Self-Audit

**Date:** 2026-07-15  
**Decision:** `CONSTRUCTION_FAIL`  
**Scope:** theory and preregistration audit only; no estimator implementation, outcome run, manuscript edit or R007 release

## Audit Result

The design-weighted estimator question remains warranted by corrected R006c, but the first protocol draft was not implementation-ready. Five material issues were corrected:

1. Endpoint selection could inspect predictor designs from evaluation prefixes. It is now restricted to a disjoint calibration region, with prospective support recomputation and no endpoint replacement.
2. The original `tau=1e-3 s_max` rule could classify every numerically full-rank direction as supported and make abstention vacuous. The certificate now has a fixed inverse-amplification interpretation, `kappa_max=50`, and construction fails if no genuinely unsupported candidate exists.
3. The outcome and penalty terms did not have an auditable common scale. The protocol now defines a normalized loss and an explicit training-prefix Gram scale.
4. The nonconvex Tucker routine lacked a post-projection descent rule, stationarity diagnostic and deterministic start-selection criterion. These are now frozen.
5. Thirty confirmation seeds alone did not define a confirmatory estimand or multiplicity control. The seed is now the clustered inferential unit; four prespecified worst-case comparator contrasts use Holm-adjusted one-sided sign inference.

## Hidden Leakage Assessment

Formal topology endpoints remain absent from estimator fitting and hyperparameter selection. Endpoint eligibility may depend on calibration-prefix lagged predictors because support is a property of the realized training design, but it cannot depend on validation/evaluation prefixes, response targets, true coefficient blocks or endpoint recovery errors. All 64 candidate certificates must be retained so lowest-index selection is auditable.

## Mathematical Assessment

The exact kernel theorem and the thresholded numerical certificate are now separated. Exact identifiability uses `ker(Z_tilde) subset ker(Delta W')`. The thresholded projector answers a different question: recoverability under a frozen conditioning tolerance. A small nonzero singular direction is not called exactly unidentified.

The end-to-end theory remains incomplete. Restricted curvature is an assumption, not a consequence of Tucker rank, and no global convergence or finite-sample statistical rate is currently proved. The protocol may test a method, but another broad methods submission still requires the T4 oracle/rate result described in the literature strategy.

## Construction Entry Criteria

Only construction code and tests may proceed next. Before any simulated recovery outcome is generated, they must establish:

- disjoint calibration, validation and evaluation indices after the rolling warm-up;
- feasible supported `W_alt_interp` and `W_alt_family` endpoints under the fixed rule;
- feasible unsupported `W_alt_out` endpoints without threshold search;
- exact support algebra and loss/Gram equivalence on toy cases;
- endpoint-selection independence from response targets and truth;
- deterministic projected optimization mechanics on synthetic objective-only fixtures.

If topology support construction fails, the correct result is `CONSTRUCTION_FAIL`. It is not permissible to enlarge candidate pools, alter `kappa_max`, lower support thresholds or redesign the DGP after inspecting recovery outcomes.

## Frozen Boundaries

The manuscript, figures, submission package, active experiment tracker, R007, N=50/100 expansion, native GNN runs, coherent bootstrap and EIA outcome inspection remain frozen. Projected graph-feature comparisons remain Supplementary.

## Executed Gate Update

The frozen construction-only gate completed 160 seed-cell records. Every calibration prefix retained all 20 topology-exposure directions; the maximum `chi_tau` over the entire unsupported candidate pool was `2.60e-15`. Consequently, no unsupported endpoint existed under the prespecified rule and all 160 records failed for `no_unsupported_candidate` only.

This invalidates the combined recovery-plus-abstention R006d question in the current DGP. It does not invalidate the two supported held-out endpoint classes, which were feasible in all records, and it does not license choosing a harsher threshold after seeing these spectra. The next protocol must split native supported-endpoint recovery from a separate exact low-dimensional excitation experiment.
