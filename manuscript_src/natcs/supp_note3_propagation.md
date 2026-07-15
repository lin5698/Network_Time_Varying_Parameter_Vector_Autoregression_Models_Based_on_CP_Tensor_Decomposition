This supplementary note expands `Methods > Propagation objects` and provides the precise definitions of the raw pair-level contribution, the bounded regression contribution and the aggregate propagation index. For a reported date label t, $\Psi_h^{tot}(t)$ denotes the horizon-h moving-average coefficient implied by the estimated direct block, network block and within-horizon topology $W_t$. $\Psi_h^{dir}(t)$ denotes the corresponding direct-only recursion with the same direct block and covariance matrix but with the network block set to zero.

Equivalently, the total response uses the lag operator $M_{k,t}(W_t)$, the direct-only response uses $M_{k,t}(0)$, and the frozen-topology response $\Psi_h^{pre}(t)$ uses $M_{k,t}(W_{pre})$. These three response families share the same reconstructed coefficient path and shock normalization. They differ only in the explicit network argument, which defines the propagation decomposition as operator-level readouts from one fitted path.

For an ordered receiver-shock pair i <- j and horizon H, the raw pair-level network contribution is the normalized difference between the total absolute response mass and the direct-only absolute response mass:

$$
q^{raw}_{ij}(t,H) =
\frac{
\sum_{h=0}^{H} \left| e_i' \Psi^{tot}_{h}(t)\Sigma_t e_j \right|
-
\sum_{h=0}^{H} \left| e_i' \Psi^{dir}_{h}(t)\Sigma_t e_j \right|
}{
\max \left\{
\sum_{h=0}^{H} \left| e_i' \Psi^{tot}_{h}(t)\Sigma_t e_j \right|,
\epsilon
\right\}
}.
$$

The bounded regression metric clips that raw contribution to the interval from 0 to 1:

$$
q^{bound}_{ij}(t,H)=\min\{1,\max\{0,q^{raw}_{ij}(t,H)\}\},
$$

This bounded metric is used only in the second-stage panel regressions. The aggregate index reported in the time-series figures applies the same total-minus-direct construction after summing over ordered non-self pairs:

$$
G(t,H)=
\frac{
\sum_{i \neq j}\sum_{h=0}^{H} \left| e_i' \Psi^{tot}_{h}(t)\Sigma_t e_j \right|
-
\sum_{i \neq j}\sum_{h=0}^{H} \left| e_i' \Psi^{dir}_{h}(t)\Sigma_t e_j \right|
}{
\max \left\{
\sum_{i \neq j}\sum_{h=0}^{H} \left| e_i' \Psi^{tot}_{h}(t)\Sigma_t e_j \right|,
\epsilon
\right\}
}.
$$

The aggregate index is intentionally not clipped and can be negative when the network block dampens cumulative responses. The bounded pair-level metric is used only as a dependent-variable transform for the second-stage panel association. The raw pair-level series is retained as an untruncated regression sensitivity because boundary mass and clipping can change regression magnitudes even when the reconstructed response path is unchanged.

The frozen-topology benchmark keeps the coefficient blocks fixed at the same reported date and replaces the evolving network by the pre-period benchmark topology. This benchmark asks how the measured propagation signal changes when topology evolution is switched off.

Proof sketch for the local weak-separation condition in the main Methods. Fix one equation, one rolling window and one lag block; stacking equations only repeats the same argument row by row. Let X denote the direct lag design and Z denote the network-exposure design. The local least-squares target regresses the outcome Y on direct coefficients a and network coefficients b, plus residual U:

$$
Y = X a + Z b + U,
$$

Here a and b are the direct and network coefficient vectors for the considered equation and lag. Residualize the network-exposure design and the outcome against the direct lag design. By the Frisch-Waugh-Lovell theorem, the unregularized network coefficient is obtained from the residualized normal equation:

$$
\widehat{b}=\left((Z^{\perp})'Z^{\perp}\right)^{-1}(Z^{\perp})'Y^{\perp}
$$

This expression is valid when the residualized network Gram matrix is nonsingular. If its sample-scaled minimum eigenvalue is at least eta > 0, then

$$
\|\widehat{b}-b\|
\leq
\eta^{-1}
\left\|
n^{-1}(Z^{\perp})'U
\right\|.
$$

With a ridge penalty applied to the residualized network block, the corresponding penalized update is

$$
\widehat{b}_{\lambda}
=
\left((Z^{\perp})'Z^{\perp}+\lambda I\right)^{-1}(Z^{\perp})'Y^{\perp},
$$

so perturbations in the residualized moment are damped by the ridge-adjusted eigenvalue bound, while the penalty introduces shrinkage bias relative to the unpenalized coefficient. The implemented equation-wise ridge regression penalizes the joint local design; the displayed formula is a diagnostic proof device for the same weak-separation condition. Thus a positive residualized eigenvalue lower bound is the finite-sample condition under which the network block is a locally stable coefficient block. If eta equals zero, a nonzero network-direction vector can be absorbed by the direct design inside the same window, so the direct/network split is not uniquely identified from the local design. This motivates the main-text near-collinearity diagnostic and the benchmark checks for network misspecification and topology perturbation. The statement is conditional on the observed design and leaves causal identification under endogenous network formation to a separate design.

Proof of Proposition 1 (finite-horizon response transfer). Let $\mathcal{C}(W)$ and $\widehat{\mathcal{C}}(W)$ denote the true and reconstructed companion matrices for a fixed reported date and a fixed topology argument $W$. Throughout this proof, the norm is the compatible induced, hence submultiplicative matrix norm used in the proposition, and the fixed companion-state selection map $J$ and its transpose $J'$ have norm one. The standard telescoping identity gives

$$
\widehat{\mathcal{C}}^{h}-\mathcal{C}^{h}
=
\sum_{r=0}^{h-1}
\widehat{\mathcal{C}}^{r}
(\widehat{\mathcal{C}}-\mathcal{C})
\mathcal{C}^{h-1-r}.
$$

If $\|\widehat{\mathcal{C}}^{r}\|\leq K$ and $\|\mathcal{C}^{r}\|\leq K$ for all powers used up to horizon $H$, submultiplicativity gives

$$
\|\widehat{\mathcal{C}}^{h}-\mathcal{C}^{h}\|
\leq h K^{2}\|\widehat{\mathcal{C}}-\mathcal{C}\|.
$$

Let $J$ be the fixed companion-state selection map and let $S$ be the shared shock-normalization map, with $\|S\|\leq L_{\Sigma}$. Since $\Psi_h(W)=J\mathcal{C}(W)^hJ'S$, the response error is bounded by $hL_{\Sigma}K^2\|\widehat{\mathcal{C}}(W)-\mathcal{C}(W)\|$. Summing from $h=1$ through $H$ gives

$$
\sum_{h=1}^{H}\left\|\widehat{\Psi}_{h}(W)-\Psi_{h}(W)\right\|
\leq
L_{\Sigma}K^{2}\frac{H(H+1)}{2}
\left\|\widehat{\mathcal{C}}(W)-\mathcal{C}(W)\right\|.
$$

For the standard lag-$p$ companion embedding, only the top block row differs. The triangle inequality bounds its norm by the sum of the lag-operator differences, and for $M_{k,t}(W)=A_{k,t}+B_{k,t}W$,

$$
\|\widehat{M}_{k,t}(W)-M_{k,t}(W)\|
\leq
\|\widehat{A}_{k,t}-A_{k,t}\|+\|W\|\|\widehat{B}_{k,t}-B_{k,t}\|.
$$

The direct-only and frozen-topology cases use the same argument with the zero-network and frozen benchmark topology arguments. The ratio metrics are continuous on the restricted domain where the normalizing denominator exceeds the explicit denominator floor, so the estimator keeps that floor and reports stability diagnostics. The proposition is conditional on the supplied coefficient error and bounded powers; it does not prove CP-ALS convergence, rank selection or a gain over local estimation.
