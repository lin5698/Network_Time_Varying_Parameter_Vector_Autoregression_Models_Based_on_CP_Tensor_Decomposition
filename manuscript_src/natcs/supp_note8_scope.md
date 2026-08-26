This supplementary note collects the operating regime, diagnostic failure modes and interpretation boundaries distributed across the main text.

The framework targets separable direct/network response operators with a supplied topology argument. It is useful only when the topology can be treated as predetermined for the declared fixed-path readout, when direct persistence and lagged network exposure are substantively distinct, and when a low-dimensional temporal reconstruction is a plausible regularizer for noisy local coefficient estimates. It is not a topology-formation model, a generic dynamics-discovery method or a causal intervention design.

The main failure modes are ordered rather than pooled. A collapsed representation can fail to define the requested topology readout. An evaluable representation can still have weak separation between direct and network regressors. An identifiable target can be poorly recovered by a chosen estimator. A recovered coefficient path can still give unstable finite-horizon responses. The qualification sequence reports each failure at its own stage; a prediction score or a later numerical calculation cannot repair an earlier unmet condition.

The evidence hierarchy separates theoretical scope from numerical scope. Theorem 1 establishes the finite-basis kernel certificate for one- and two-hop row-separable bases. Their strict non-equivalence is proved on every declared topology domain containing the directed three-cycle $P$. Proposition 1 and Corollary 1 establish the unrestricted one-hop boundary and its diagonal structured-inverse exception. The controlled $N=15/N=30$ benchmark supports only its stated one-hop CP-versus-unrestricted-local comparison. The endpoint-aware $N=20$, $T=200$ gate prevents that comparison from being inherited as broad native recovery. Projected graph-feature diagnostics do not establish a native same-endpoint comparison. No application output contributes to this hierarchy.

The weak-separation diagnostic operationalizes only one local design screen. It uses the exact lag-specific topology sequence, residualizes all network-exposure lag blocks jointly against the intercept, direct lags and declared exogenous regressors, then evaluates the residualized joint Gram matrix. Rank deficiency and a $10^{-8}$ numerical screen identify degenerate or near-singular directions, but their absence does not establish sufficient excitation, causal identification, penalty irrelevance or estimator recovery.

The interpretation sequence is therefore as follows.

1. Declare the topology-indexed response query, including fitted path, topology argument, shock normalization and horizon.
2. Verify that the fitted representation retains separated blocks or a valid inverse for that query.
3. Assess design separation without equating penalized numerical uniqueness with identification.
4. Evaluate recovery only with the same declared endpoint and a declared comparator contract.
5. Qualify finite-horizon results by the stated stability condition and retain unavailable, unstable and non-finite cases.
6. Treat fixed-path topology contrasts and generated-regressor associations as descriptive unless an independent causal design is supplied.

Under this sequence, query certification is a scoped computational reporting and design rule. The finite-basis theorem establishes representation sufficiency only under its stated kernel condition. It does not establish empirical transfer or numerical recovery outside the one-hop controlled evidence.
