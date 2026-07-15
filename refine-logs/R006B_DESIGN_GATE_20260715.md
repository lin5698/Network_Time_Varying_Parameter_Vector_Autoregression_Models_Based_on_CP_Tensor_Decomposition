# R006b Stability-Signal Deconfounding Design Gate

**Status:** construction gates passed; outcome protocol frozen in `R006B_PROTOCOL_20260715.md`

## Problem Revealed by R006

R006 sets the query spectral radius by multiplying all direct and network blocks by a common scalar. This simultaneously changes:

- the query spectral radius;
- the query Frobenius norm and separated-block norm;
- the realized state scale under fixed innovation variance;
- the effective scale of the fixed ridge penalty.

Consequently, the rho=0.80 versus rho=0.95 comparison cannot isolate response amplification from coefficient-recovery SNR.

## Required Construction

Let `U` have orthonormal columns and construct the frozen-base query directly as

```text
M_t(W_ref) = sum_r lambda_{r,t} u_r u_r'
```

with a fixed Frobenius norm and a declared maximum absolute eigenvalue. Preserve the separated query contract by setting

```text
B_t = sum_r c_r lambda_{r,t} u_r u_r'
A_t = M_t(W_ref) - B_t W_ref.
```

Then `A_t + B_t W_ref = M_t(W_ref)` exactly, and each concatenated `[A_t, B_t]` component remains rank one across the two block types when `c_r` is date-invariant. Tail components can therefore be calibrated to an `a3` target without common scaling of the full operator.

## Two Required Evidence Layers

1. **Matched-excitation diagnostic.** Use a frozen predictor covariance or declared exogenous excitation so every stability cell has the same design scale. This isolates local block estimation and response transfer from endogenous state covariance.
2. **Native VAR panel.** Generate the recursive state process and report the resulting state covariance, innovation-to-state ratio and design Gram spectrum as outcomes rather than assuming they are matched.

The first layer is a controlled theory diagnostic, not a replacement for the native VAR experiment. The second layer quantifies the coupling that an autonomous dynamic system necessarily introduces.

## Estimator Scaling

Replace the fixed absolute ridge penalty in this diagnostic with a scale-adaptive penalty proportional to the average design Gram diagonal. Verify invariance by multiplying the complete predictor/outcome system by known constants. This change must be tested and applied to every compared method in R006b; it cannot retroactively alter R006.

## Pre-Run Feasibility Gates

- Query spectral radius error below `1e-10`.
- Query Frobenius-norm mismatch across stability cells below `1e-6`.
- Matched-excitation design covariance mismatch below `1%`.
- Scale-adaptive ridge coefficient estimates invariant to global data scaling within `1e-8`.
- Calibrated `a3` error below `1e-6`.
- Observed-topology operators remain numerically bounded over the finite horizon.

Only after these construction tests pass should outcome-facing stop-go thresholds be frozen. R006 remains `FAIL` regardless of R006b results.
