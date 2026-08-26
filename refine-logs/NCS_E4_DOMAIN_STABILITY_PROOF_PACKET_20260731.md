# E4 domain-uniform stability certificate

**Lifecycle:** PRE_OUTCOME  
**Scientific execution:** NOT_AUTHORIZED  
**Scope:** deterministic algebra and fixture verification only

## 1. Declared topology domain

Let

\[
\mathcal W=\{W\in\mathbb R^{N\times N}:\lVert W\rVert_\infty\leq 1\},
\qquad
\lVert W\rVert_\infty=\max_i\sum_j|W_{ij}|.
\]

Each topology is zero-diagonalized and normalized once before fitting and
evaluation. Family 2 uses the unmodified matrix product \(W^2=W W\); it does
not renormalize or threshold the square. Submultiplicativity gives

\[
\lVert W^2\rVert_\infty\leq\lVert W\rVert_\infty^2\leq1.
\]

## 2. Query-independent coefficient projection

For node \(i\), collect the retained diagonal coefficients in
\(c_i=(c_{0i},\ldots,c_{Ki})\), with \(K=1\) for Family 1 and \(K=2\) for
Family 2. Freeze \(\eta=0.90\) and define

\[
\Pi_\eta(c_i)=s_i c_i,
\qquad
s_i=\min\left\{1,\frac{\eta}{\max(\lVert c_i\rVert_1,\epsilon)}\right\}.
\]

The implementation applies this projection after fitting and before any query
topology is supplied. Its arguments are only the fitted coefficient blocks and
\(\eta\). The same projected path is used by selection, held-out evaluation,
recursive bootstrap refitting and bootstrap retuning.

## 3. Operator bound

For Family 1,

\[
G_1(W)=\operatorname{diag}(c_0)+\operatorname{diag}(c_1)W.
\]

For each row \(i\),

\[
\sum_j |[G_1(W)]_{ij}|
\leq |c_{0i}|+|c_{1i}|\sum_j|W_{ij}|
\leq\lVert c_i\rVert_1\leq\eta.
\]

For Family 2,

\[
G_2(W)=\operatorname{diag}(c_0)+\operatorname{diag}(c_1)W
+\operatorname{diag}(c_2)W^2,
\]

and therefore

\[
\sum_j |[G_2(W)]_{ij}|
\leq |c_{0i}|+|c_{1i}|\lVert W\rVert_\infty
+|c_{2i}|\lVert W^2\rVert_\infty
\leq\lVert c_i\rVert_1\leq\eta.
\]

Thus, for either family and every \(W\in\mathcal W\),

\[
\rho\{G_k(W)\}\leq\lVert G_k(W)\rVert_\infty\leq\eta=0.90<0.98.
\]

The last number, 0.98, remains the frozen evaluation threshold. It is not
relaxed by this construction.

## 4. Exact fixture derivation

`exact_domain_stability_certificate_report` uses `fractions.Fraction` and no
floating-point eigenvalue calculation. It crosses:

- Family 1 and Family 2;
- zero, boundary and projected-out-of-envelope coefficient cases;
- signed row-normalized, directed sparse and dense positive topology cases.

For all 18 operators, it computes \(\lVert W\rVert_\infty\),
\(\lVert W^2\rVert_\infty\), the projected node-wise block norm and
\(\lVert G_k(W)\rVert_\infty\) exactly. The frozen expected summary is:

- envelope: `9/10`;
- checked operators: `18`;
- maximum projected block norm: `9/10`;
- maximum operator infinity norm: at most `9/10`;
- spectral-radius conclusion: induced-norm inequality, not a floating-point
  rank or eigenvalue surrogate.

The separate float64 report exercises the runtime projection and endpoint
construction. It is an implementation check, not the proof of the bound.

## 5. Scope boundary

This certificate establishes domain-uniform stability for the declared
normalized topology class and the two diagonal-block operator families. It
does not establish recovery accuracy, uncertainty calibration or empirical
generality. Those remain outcome-dependent E4 gates and are not authorized or
promoted by this packet.
