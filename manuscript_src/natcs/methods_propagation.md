For an observation index $\tau$ in the rolling window ending at reported date $t$, the implemented equation-wise estimator uses

$$
y_{\tau} = c_t + \sum_{k=1}^{p} A_{k,t} y_{\tau-k} + \sum_{k=1}^{p} B_{k,t} W_{\tau-k} y_{\tau-k} + C_t x_{\tau} + \varepsilon_{\tau},
$$

where $A_{k,t}$ and $B_{k,t}$ are unrestricted direct and network blocks in the controlled benchmark. Estimation therefore uses lag-specific historical matrices $W_{\tau-k}$. Response evaluation is separate: for the target date $t$, define $\bar W_t:=W_{t-1}$ as the last topology available inside the estimation window. A supplied matrix $W$ enters $M_{k,t}(W)=A_{k,t}+B_{k,t}W$ and is held fixed through the declared horizon. Let $\Phi_h(t,W)$ denote the resulting moving-average coefficient. For an ordered shock from $j$ to $i$, the floor-regularized one-standard-deviation generalized response is $\psi_{i \leftarrow j}(h;t,W)=e_i'\Phi_h(t,W)\Sigma_t e_j/\sqrt{\Sigma_{jj,t}+\delta}$, with $\delta=10^{-12}$. In the controlled benchmark, the shock map is the identity, so the reported response-recovery metric compares unit-shock paths rather than an estimated covariance-normalized response. Observed, direct-only and frozen-topology responses use $\bar W_t$, zero network mediation and a predeclared benchmark topology $W_{pre}$, respectively, with coefficients, horizon and shock normalization held fixed. The main propagation quantities compare the observed response with the direct-only evaluation. For each ordered receiver-shock pair, the raw network share is computed with the target-date parameterization and $\bar W_t$ held fixed throughout the horizon:

$$
q^{raw}_{ij}(t,H)=\frac{\sum_{h=0}^{H}\left|\psi^{tot}_{i \leftarrow j}(h;t)\right|-\sum_{h=0}^{H}\left|\psi^{dir}_{i \leftarrow j}(h;t)\right|}{\max\left\{\sum_{h=0}^{H}\left|\psi^{tot}_{i \leftarrow j}(h;t)\right|,\epsilon\right\}}.
$$

The implementation fixes $\epsilon=10^{-12}>0$, so the ratio remains defined when the total response mass is zero.

The bounded pair-level diagnostic clips the raw network share to the interval from 0 to 1. The aggregate index uses the same numerator and denominator after summing over ordered non-self pairs:

$$
G(t,H)=\frac{\sum_{i \neq j}\sum_{h=0}^{H}\left|\psi^{tot}_{i \leftarrow j}(h;t)\right|-\sum_{i \neq j}\sum_{h=0}^{H}\left|\psi^{dir}_{i \leftarrow j}(h;t)\right|}{\max\left\{\sum_{i \neq j}\sum_{h=0}^{H}\left|\psi^{tot}_{i \leftarrow j}(h;t)\right|,\epsilon\right\}}.
$$

The aggregate index is left unclipped and can be negative when the network block dampens cumulative responses. The frozen-topology comparator replaces $\bar W_t$ with the fixed benchmark matrix $W_{pre}$ and holds the fitted coefficient path fixed. The generalized impulse responses follow the generalized-response convention of Koop, Pesaran and Potter and its linear-Gaussian specialization by Pesaran and Shin [@koop1996; @pesaran1998]. Supplementary Note 1 standardizes the notation, and Supplementary Note 3 gives the precise pair-level and aggregate definitions.

The horizon-truncated half-decay summary is computed from the absolute response path. The first maximum defines the peak; the statistic is the first horizon at or after that peak at which the response is no greater than half the peak. If no crossing occurs within the reported horizon, the value is right-censored at the final horizon. This convention prevents pre-peak near-zero responses from being misclassified as immediate decay.
