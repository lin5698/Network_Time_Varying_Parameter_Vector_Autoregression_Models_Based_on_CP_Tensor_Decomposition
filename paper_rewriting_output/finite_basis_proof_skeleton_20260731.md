# Finite-Basis Query Certificate: Proof-Obligation Ledger

Date: 2026-07-31

## Dependency DAG

`D1 basis maps and typed row design -> D2 direct-sum T/Q maps -> L1 kernel lemma -> T1 kernel certificate -> {T1-row row-space form, C1 full-rank corollary, C2 one-hop corollary, C3 two-hop corollary}`.

`D3 complete endpoint -> T1 endpoint equivalence` uses the retained-operator projection. The non-equivalence witness and the negative/positive fixtures are independent exact checks.

No dependency cycle is present.

## Typed Symbols

| Symbol | Type | Role |
| --- | --- | --- |
| \(\mathcal W\) | subset of \(\mathbb R^{N\times N}\) | declared topology domain |
| \(\Phi_r\) | map \(\mathcal W\to\mathbb R^{N\times N}\) | fixed topology basis map |
| \(c_{k,i}\) | \(\mathbb R^{m+1}\) | row coefficients at lag \(k\) |
| \(X_i^\Phi(W)\) | \(\mathbb R^{N\times(m+1)}\) | coefficient-to-row design |
| \(T_{W_0}^\Phi\) | linear map \(\mathcal C_{N,p,m}\to\mathcal D_{N,p}\) | retained collapse |
| \(Q_{W_q}^{G,\Phi}\) | linear map \(\mathcal C_{N,p,m}\to\mathcal D_{N,p}\) | queried operator tuple |
| \(\mathscr R\) | linear isomorphism \(\mathcal D_{N,p}\to(\mathbb R^{N\times N})^p\) | row-to-matrix reshape |
| \(\Psi\) | deterministic map on operator tuples | complete finite-horizon endpoint |

## Canonical Quantified Claim

For every \(N,p\geq1\), \(m\geq0\), declared topology domain \(\mathcal W\), fixed basis maps \(\Phi_0,\ldots,\Phi_m\), and every \(W_0,W_q\in\mathcal W\), the queried operator factors linearly through the retained collapse if and only if the rowwise retained kernel is contained in the query kernel. The equivalent row-space inclusion has the reverse containment direction. Complete-endpoint equivalence additionally assumes that the endpoint retains the operator tuple through a deterministic left projection.

## Micro-Claims

| ID | Goal | Rule and discharged conditions |
| --- | --- | --- |
| MC1 | operator row equals \(X_i^\Phi(W)c_{k,i}\) | expand diagonal left multiplication rowwise |
| MC2 | kernels of T and Q are direct sums of row kernels | each coordinate map acts independently |
| MC3 | direct-sum inclusion iff every row inclusion | singleton-coordinate necessity and componentwise sufficiency |
| MC4 | linear factor iff kernel inclusion | quotient/image construction; well-definedness checked |
| MC5 | kernel inclusion iff reverse row-space inclusion | \(\ker X=(\operatorname{row}X)^\perp\) in finite-dimensional Euclidean space |
| MC6 | operator factor implies endpoint factor | deterministic composition with reshape and endpoint map |
| MC7 | endpoint factor implies operator factor | endpoint retains operator tuple; apply projection and inverse reshape |
| MC8 | full column rank implies all-query availability | retained row kernels are zero |
| MC9 | one-hop zero-row criterion | zero diagonal makes \(e_i\) orthogonal to a nonzero exposure row |
| MC10 | two-hop admissible non-equivalence | \(\mathcal G_1\subseteq\mathcal G_2\) by zeroing the quadratic coefficient; strictness follows because, at the admissible three-cycle \(P\), each row of \(P^2\) lies outside the span of the corresponding rows of \(I\) and \(P\) |

## Counterexample Pass

Checked: \(N=1\); \(N<m+1\); matched query; rank-deficient retained design; reversed row-space direction; endpoint without operator projection; and attempted one-hop representation of \(W^2\) at an admissible row-stochastic zero-diagonal three-cycle. No probability limits, asymptotics, interchanges or hidden constants occur.
