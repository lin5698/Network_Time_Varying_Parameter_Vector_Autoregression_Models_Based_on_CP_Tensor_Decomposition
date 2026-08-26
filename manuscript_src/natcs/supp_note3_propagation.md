This supplementary note expands `Methods > Readout and design separation` and `Methods > Finite-horizon transfer`. It provides the precise definitions of the raw pair-level contribution, a bounded pair-level summary and the aggregate propagation index. It also distinguishes the moving-average coefficient from the shock-normalized response. For a reported date $t$ and supplied topology $W$, let

$$
\Phi_h(t,W)=J\mathcal{C}_t(W)^hJ'
$$

be the horizon-$h$ moving-average coefficient. The implemented generalized-response normalization uses

$$
S_t=\Sigma_t\operatorname{diag}\left\{(\Sigma_{jj,t}+\delta)^{-1/2}\right\}_{j=1}^{N},
\qquad \delta=10^{-12},
$$

so the matrix of floor-regularized one-standard-deviation generalized responses is

$$
R_h(t,W)=\Phi_h(t,W)S_t.
$$

Its $(i,j)$ entry is the response of receiver $i$ to the normalized innovation in unit $j$. This definition matches the implementation: the moving-average coefficient is multiplied by $\Sigma_t e_j/\sqrt{\Sigma_{jj,t}+\delta}$ exactly once.

For target date $t$, define $\bar W_t:=W_{t-1}$ as the final topology available inside the rolling estimation window. The total response uses $\bar W_t$, the direct-only response uses the zero-network argument and the frozen-topology response uses $W_{pre}$:

$$
R_h^{tot}(t)=R_h(t,\bar W_t),
\qquad
R_h^{dir}(t)=R_h(t,0),
\qquad
R_h^{pre}(t)=R_h(t,W_{pre}).
$$

These three response families share the same reconstructed coefficient path and shock-normalization map. They differ only in the explicit network argument.

For an ordered receiver-shock pair $i\leftarrow j$ and horizon $H$, the raw pair-level network contribution is the normalized difference between the total absolute response mass and the direct-only absolute response mass:

$$
q^{raw}_{ij}(t,H) =
\frac{
\sum_{h=0}^{H} \left| e_i' R^{tot}_{h}(t)e_j \right|
-
\sum_{h=0}^{H} \left| e_i' R^{dir}_{h}(t)e_j \right|
}{
\max \left\{
\sum_{h=0}^{H} \left| e_i' R^{tot}_{h}(t)e_j \right|,
\epsilon
\right\}
},
\qquad \epsilon=10^{-12}>0.
$$

The bounded pair-level summary clips that raw contribution to the interval from 0 to 1:

$$
q^{bound}_{ij}(t,H)=\min\{1,\max\{0,q^{raw}_{ij}(t,H)\}\}.
$$

The aggregate index applies the same total-minus-direct construction after summing over ordered non-self pairs:

$$
G(t,H)=
\frac{
\sum_{i \neq j}\sum_{h=0}^{H} \left| e_i' R^{tot}_{h}(t)e_j \right|
-
\sum_{i \neq j}\sum_{h=0}^{H} \left| e_i' R^{dir}_{h}(t)e_j \right|
}{
\max \left\{
\sum_{i \neq j}\sum_{h=0}^{H} \left| e_i' R^{tot}_{h}(t)e_j \right|,
\epsilon
\right\}
}.
$$

The aggregate index is intentionally not clipped and can be negative when the network block dampens cumulative responses. The raw and bounded pair-level summaries distinguish signed attenuation from a unit-interval diagnostic. The fixed positive floor $\epsilon$ makes both ratio maps defined and continuous even when the total response mass is zero.

The frozen-topology benchmark keeps the coefficient blocks fixed at the same reported date and replaces the evolving network by the pre-period benchmark topology. This benchmark asks how the measured propagation signal changes when topology evolution is switched off.

## Joint-design separation and the implemented ridge estimator

Fix one equation and one rolling window, with integers $n\geq1$ and $m\geq1$. Let $X\in\mathbb{R}^{n\times q}$ contain every nuisance/direct regressor used in that equation: the intercept, all $p$ direct lags and any declared optional exogenous regressors. Let $Z\in\mathbb{R}^{n\times m}$ contain all $p$ network-exposure lag blocks jointly. Write

$$
Y=Xa+Zb+U.
$$

Let $P_X=XX^{\dagger}$ be the orthogonal projector onto the column span of $X$, where $X^{\dagger}$ is the Moore-Penrose inverse, and let $M_X=I-P_X$. Define $Z^{\perp}=M_XZ$ and $Y^{\perp}=M_XY$. The unpenalized network coefficient satisfies the Frisch-Waugh-Lovell normal equation

$$
\widehat b=\left((Z^{\perp})'Z^{\perp}\right)^{-1}(Z^{\perp})'Y^{\perp}
$$

when the residualized joint network Gram matrix is nonsingular. If, for the Euclidean vector norm and spectral matrix norm,

$$
\lambda_{\min}\!\left(n^{-1}(Z^{\perp})'Z^{\perp}\right)\geq\eta>0,
$$

then

$$
\|\widehat b-b\|_2
\leq
\eta^{-1}\left\|n^{-1}(Z^{\perp})'U\right\|_2.
$$

If $\lambda_{\min}\{n^{-1}(Z^{\perp})'Z^{\perp}\}=0$, there is a nonzero network-direction vector $v$ with $Zv\in\operatorname{col}(X)$. That direction can be absorbed by the nuisance/direct span, so the unpenalized network block is not unique. Complete uniqueness of both $a$ and $b$ additionally requires full column rank of the joint design $[X\;Z]$. A per-lag calculation is not sufficient: all network lag blocks must enter $Z$ jointly, or the other network lags must be included among the regressors projected out.

The implemented local estimator instead minimizes the all-coefficient joint ridge objective

$$
\|Y-Xa-Zb\|_2^2+\lambda\left(\|a\|_2^2+\|b\|_2^2\right),
\qquad \lambda>0.
$$

Eliminating $a$ from its two block normal equations gives the exact ridge Schur complement. Define

$$
M_{X,\lambda}=I-X(X'X+\lambda I)^{-1}X'.
$$

Then the implemented network-block update satisfies

$$
\left\{Z'M_{X,\lambda}Z+\lambda I\right\}\widehat b_{\lambda}
=Z'M_{X,\lambda}Y.
$$

This follows by substituting

$$
\widehat a_{\lambda}=(X'X+\lambda I)^{-1}X'(Y-Z\widehat b_{\lambda})
$$

into the network-block normal equation. The matrix $M_{X,\lambda}$ is not the ordinary FWL projection when $\lambda>0$. The positive penalty makes the joint ridge Hessian positive definite and the penalized coefficient vector unique in exact arithmetic even if the unpenalized design is singular. That penalized uniqueness is not evidence of unpenalized design identification. A weak-separation diagnostic therefore uses the unpenalized projector $M_X$, the joint $Z$ matrix and the same lag-specific topology matrices supplied to the estimator. A small residualized eigenvalue implies worst-case sensitivity in a weak network direction; it does not by itself show that the realized estimate is penalty-dominated. This distinction motivates reporting design separation and endpoint-specific recovery separately.

## Proof of Proposition 2: finite-horizon response transfer

Let $\mathcal{C}(W)$ and $\widehat{\mathcal{C}}(W)$ denote the true and reconstructed companion matrices for a fixed reported date and fixed topology argument $W$. Throughout this proof, $\|\cdot\|_2$ is the spectral matrix norm. Let $H\geq1$, and suppose

$$
\max_{0\leq r\leq H}\left\{\|\mathcal{C}(W)^r\|_2,\|\widehat{\mathcal{C}}(W)^r\|_2\right\}\leq K
$$

for $K\geq1$. The standard finite telescoping identity gives

$$
\widehat{\mathcal{C}}^{h}-\mathcal{C}^{h}
=
\sum_{r=0}^{h-1}
\widehat{\mathcal{C}}^{r}
(\widehat{\mathcal{C}}-\mathcal{C})
\mathcal{C}^{h-1-r}.
$$

Spectral-norm submultiplicativity gives, for $1\leq h\leq H$,

$$
\|\widehat{\mathcal{C}}^{h}-\mathcal{C}^{h}\|_2
\leq h K^{2}\|\widehat{\mathcal{C}}-\mathcal{C}\|_2.
$$

Let $J$ be the fixed companion-state selection map, with $\|J\|_2=\|J'\|_2=1$, and let $S$ be the shock-normalization map shared by the true and reconstructed responses, with $\|S\|_2\leq L_S$. Define

$$
R_h(W)=J\mathcal{C}(W)^hJ'S,
\qquad
\widehat R_h(W)=J\widehat{\mathcal{C}}(W)^hJ'S.
$$

The response error is bounded by $hL_SK^2\|\widehat{\mathcal{C}}(W)-\mathcal{C}(W)\|_2$. Summing from $h=1$ through $H$ gives

$$
\sum_{h=1}^{H}\left\|\widehat R_{h}(W)-R_{h}(W)\right\|_2
\leq
L_SK^{2}\frac{H(H+1)}{2}
\left\|\widehat{\mathcal{C}}(W)-\mathcal{C}(W)\right\|_2.
$$

For the standard lag-$p$ companion embedding, only the top block row differs. Writing $\Delta M_k(W)=\widehat M_{k,t}(W)-M_{k,t}(W)$, the spectral norm obeys

$$
\left\|\widehat{\mathcal{C}}(W)-\mathcal{C}(W)\right\|_2
\leq
\left\{\sum_{k=1}^{p}\|\Delta M_k(W)\|_2^2\right\}^{1/2}
\leq
\sum_{k=1}^{p}\|\Delta M_k(W)\|_2.
$$

For $M_{k,t}(W)=A_{k,t}+B_{k,t}W$,

$$
\|\Delta M_k(W)\|_2
\leq
\|\widehat A_{k,t}-A_{k,t}\|_2
+\|W\|_2\|\widehat B_{k,t}-B_{k,t}\|_2.
$$

The observed, direct-only and frozen-topology cases apply the same proof separately at $\bar W_t$, zero and $W_{pre}$. If one common constant is reported, $K$ is the maximum of the true and reconstructed power bounds over all three companion families. The fixed positive denominator floor makes the ratio metrics continuous over the full finite-dimensional response domain. Proposition 2 is conditional on a supplied coefficient error, a common shock map and bounded powers; it does not prove CP-ALS convergence, rank selection or a gain over local estimation. It also does not empirically verify the power-bound assumption.
