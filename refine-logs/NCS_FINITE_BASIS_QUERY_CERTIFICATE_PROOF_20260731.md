# Finite-Basis Query Certificate Proof

Date: 2026-07-31

Status: `SOURCE_ONLY_PROOF_ACCEPTED`, `TWO_FRESH_BLIND_REVIEWS_COMPLETED`,
`NO_NUMERICAL_OR_EMPIRICAL_CLAIM`.

Acceptance record:
`paper_rewriting_output/finite_basis_proof_audit_20260731.md`.

This packet establishes an algebraic representation theorem for row-separable
topology-indexed operators. It does not establish estimator consistency,
recovery, uncertainty calibration, stability or application performance.

## 1. Operator class and typed spaces

Fix integers (N\geq 1), (p\geq 1), (m\geq 0) and
(H_{\max}\geq 1). Let \(\mathcal W\subseteq\mathbb R^{N\times N}\)
be a declared topology domain with a fixed node order. Choose fixed basis maps

\[
\Phi_r:\mathcal W\longrightarrow\mathbb R^{N\times N},
\qquad r=0,\ldots,m.
\]

The maps \(\Phi_r\) need not be linear in \(W\). For lag \(k\), let

\[
C_{r,k}=\operatorname{diag}(c_{r,k,1},\ldots,c_{r,k,N}),
\qquad
c_{k,i}=(c_{0,k,i},\ldots,c_{m,k,i})^\top\in\mathbb R^{m+1},
\]

and define the row-separable finite-basis operator

\[
G_{k,c}^{\Phi}(W)=\sum_{r=0}^{m}C_{r,k}\Phi_r(W).
\]

For row \(i\), define

\[
X_i^{\Phi}(W)=
\left[
\Phi_0(W)_{i,:}^{\top},\ldots,
\Phi_m(W)_{i,:}^{\top}
\right]\in\mathbb R^{N\times(m+1)}.
\]

The transpose of row \(i\) of \(G_{k,c}^{\Phi}(W)\) is exactly
(X_i^{\Phi}(W)c_{k,i}\).

Let

\[
\mathcal C_{N,p,m}=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}\mathbb R^{m+1},
\qquad
\mathcal D_{N,p}=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}\mathbb R^{N}.
\]

Define the retained-collapse map at \(W_0\in\mathcal W\) and the operator
query at \(W_q\in\mathcal W\) by

\[
T_{W_0}^{\Phi}(c)=
\left(X_i^{\Phi}(W_0)c_{k,i}\right)_{k,i},
\qquad
Q_{W_q}^{G,\Phi}(c)=
\left(X_i^{\Phi}(W_q)c_{k,i}\right)_{k,i}.
\]

Both are linear in the coefficient object \(c\), even when the basis maps are
nonlinear in topology.

Define the fixed reshape isomorphism

\[
\mathscr R:\mathcal D_{N,p}\longrightarrow
(\mathbb R^{N\times N})^p,
\qquad
[\mathscr R(d)_k]_{i,:}=d_{k,i}^{\top}.
\]

## 2. Complete finite-horizon endpoint

For \(g=(G_1,\ldots,G_p)\), let \(\mathcal C(g)\) be the standard lag-
\(p\) companion matrix and \(J=[I_N,0,\ldots,0]\). Define

\[
\Psi_{p,H_{\max}}(g)=
\left(
g,
\{J\mathcal C(g)^hJ^\top\}_{h=1}^{H_{\max}}
\right).
\]

The map is deterministic and may be nonlinear. It retains the operator tuple
as its first component, so the projection \(\pi_G\) satisfies
\(\pi_G\circ\Psi_{p,H_{\max}}=\operatorname{id}\). The complete endpoint is

\[
Q_{W_q}^{E,\Phi}
=\Psi_{p,H_{\max}}\circ\mathscr R\circ Q_{W_q}^{G,\Phi}.
\]

## 3. Linear factorization lemma

**Lemma 1 (kernel criterion).** Let \(T:V\to U\) and \(Q:V\to Z\) be
linear maps between real vector spaces. There is a unique linear map
\(F:\operatorname{im}(T)\to Z\) satisfying \(Q=F\circ T\) if and only if

\[
\ker T\subseteq\ker Q.
\]

**Proof.** If \(Q=F\circ T\), then \(T(v)=0\) implies \(Q(v)=F(0)=0\).
Conversely, assume the kernel inclusion. For \(u\in\operatorname{im}(T)\),
choose \(v\) with \(T(v)=u\) and define \(F(u)=Q(v)\). If
\(T(v)=T(v')\), then \(v-v'\in\ker T\subseteq\ker Q\), so
\(Q(v)=Q(v')\); hence \(F\) is well-defined. Linearity follows from the
linearity of \(T\) and \(Q\). Uniqueness holds because every element of
\(\operatorname{im}(T)\) has the form \(T(v)\). \(\square\)

## 4. Finite-basis query theorem

**Theorem 1 (exact finite-basis query certificate).** Fix
\(W_0,W_q\in\mathcal W\). The following statements are equivalent:

1. A linear \(F:\operatorname{im}(T_{W_0}^{\Phi})\to\mathcal D_{N,p}\)
   exists such that \(Q_{W_q}^{G,\Phi}=F\circ T_{W_0}^{\Phi}\).
2. For every row \(i\),
   \[
   \ker X_i^{\Phi}(W_0)\subseteq\ker X_i^{\Phi}(W_q).
   \]
3. For every row \(i\),
   \[
   \operatorname{row}X_i^{\Phi}(W_q)
   \subseteq
   \operatorname{row}X_i^{\Phi}(W_0)
   \quad\text{as subspaces of }\mathbb R^{m+1}.
   \]
4. A deterministic map
   \[
   K:\operatorname{im}(T_{W_0}^{\Phi})\to
   (\mathbb R^{N\times N})^p\times
   (\mathbb R^{N\times N})^{H_{\max}}
   \]
   exists such that \(Q_{W_q}^{E,\Phi}=K\circ T_{W_0}^{\Phi}\).

**Proof.** Because the coefficient and output spaces are direct sums and each
coordinate map acts only on its own \((k,i)\) coefficient,

\[
\ker T_{W_0}^{\Phi}
=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}
\ker X_i^{\Phi}(W_0),
\qquad
\ker Q_{W_q}^{G,\Phi}
=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}
\ker X_i^{\Phi}(W_q).
\]

The first direct-sum kernel is contained in the second if and only if every
rowwise inclusion in statement 2 holds. Necessity follows by placing an
arbitrary vector from one row kernel in a single direct-sum coordinate;
sufficiency follows componentwise. Lemma 1 proves the equivalence of 1 and 2.

For any real matrix \(X\),
\(\ker X=(\operatorname{row}X)^\perp\). Therefore
\(\ker X_i^{\Phi}(W_0)\subseteq\ker X_i^{\Phi}(W_q)\) if and only if
\(\operatorname{row}X_i^{\Phi}(W_q)\subseteq
\operatorname{row}X_i^{\Phi}(W_0)\), proving the equivalence of 2 and 3.

If statement 1 holds, then

\[
K=\Psi_{p,H_{\max}}\circ\mathscr R\circ F
\]

gives statement 4. Conversely, suppose statement 4 holds. If
\(T_{W_0}^{\Phi}(c)=T_{W_0}^{\Phi}(c')\), the endpoints agree. Applying
\(\pi_G\) and then \(\mathscr R^{-1}\) gives
\(Q_{W_q}^{G,\Phi}(c)=Q_{W_q}^{G,\Phi}(c')\). Taking \(c'=0\) for any
\(c\in\ker T_{W_0}^{\Phi}\) yields
\(\ker T_{W_0}^{\Phi}\subseteq\ker Q_{W_q}^{G,\Phi}\); Lemma 1 then gives
statement 1. \(\square\)

## 5. Constructive consequences

**Corollary 1 (full-column-rank sufficiency).** If
\(\operatorname{rank}X_i^{\Phi}(W_0)=m+1\) for every row \(i\), then every
query \(W_q\in\mathcal W\) factors through \(T_{W_0}^{\Phi}\).

**Proof.** Full column rank gives \(\ker X_i^{\Phi}(W_0)=\{0\}\), so the
kernel inclusions in Theorem 1 hold for every query. Equivalently, a left
inverse \(L_i\in\mathbb R^{(m+1)\times N}\) exists and recovers
\(c_{k,i}=L_i d_{k,i}\) from the retained row \(d_{k,i}\). \(\square\)

This condition is sufficient, not necessary. It requires \(N\geq m+1\);
when it fails, Theorem 1 still decides a specified query by kernel inclusion.

**Corollary 2 (one-hop diagonal class).** Let
\(\Phi_0(W)=I_N\), \(\Phi_1(W)=W\), and suppose \(W_0\) and \(W_q\) have
zero diagonal. Then the query factors if and only if every zero row of
\(W_0\) is also a zero row of \(W_q\).

**Proof.** The row design is \(X_i(W)=[e_i,W_{i,:}^{\top}]\). If row \(i\)
of \(W_0\) is nonzero, zero diagonals make its two columns nonzero and
orthogonal, hence the design has full column rank. If that row is zero, its
kernel is \(\operatorname{span}\{(0,1)^\top\}\), which is contained in the
query kernel exactly when row \(i\) of \(W_q\) is also zero. \(\square\)

**Corollary 3 (two-hop diagonal class).** Let
\(\Phi_0(W)=I_N\), \(\Phi_1(W)=W\), and \(\Phi_2(W)=W^2\), where
\(W^2=WW\) with no renormalization or diagonal deletion. Then a supplied
query factors exactly when

\[
\ker[e_i,W_{0,i,:}^{\top},(W_0^2)_{i,:}^{\top}]
\subseteq
\ker[e_i,W_{q,i,:}^{\top},(W_q^2)_{i,:}^{\top}]
\quad\text{for all }i.
\]

Full column rank three at every observed row is sufficient for every supplied
query, but it is not necessary for a particular query.

## 6. The two-hop family is not a relabelled one-hop family

Let \(\mathcal W\) contain the three-node directed-cycle topology

\[
P=\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix}.
\]

This topology is nonnegative, row-stochastic and zero-diagonal. Consider the
one-hop and two-hop row-separable function classes

\[
\mathcal G_1
=\{W\mapsto D_0I+D_1W:D_0,D_1\text{ diagonal}\}
\]

and

\[
\mathcal G_2
=\{W\mapsto C_0I+C_1W+C_2W^2:C_0,C_1,C_2\text{ diagonal}\},
\]

where the coefficient matrices are fixed across \(W\). Setting \(C_2=0\)
shows \(\mathcal G_1\subseteq\mathcal G_2\). To see that the inclusion is
strict, consider the two-hop map \(H(W)=W^2\), obtained with
\(C_0=C_1=0\) and \(C_2=I\). If \(H\) belonged to \(\mathcal G_1\), some
fixed diagonal matrices \(D_0,D_1\) would satisfy

\[
P^2=D_0I+D_1P.
\]

For each row \(i\), the row vectors \(e_i^\top\), \(P_{i,:}\) and
\((P^2)_{i,:}\) are three distinct standard basis vectors. Row \(i\) of
\(D_0I+D_1P\) lies in
\(\operatorname{span}\{e_i^\top,P_{i,:}\}\), whereas
\((P^2)_{i,:}\) does not. The displayed equality is therefore impossible.
Thus \(\mathcal G_1\subsetneq\mathcal G_2\) on any declared topology domain
containing \(P\): the two-hop family is genuinely larger than the one-hop
row-separable family, not a relabelling of it.

## 7. Exact boundary fixtures

For the two-hop diagonal class, take

\[
W_0=\begin{bmatrix}0&1&0\\0&0&0\\0&0&0\end{bmatrix},
\qquad
W_q=\begin{bmatrix}0&1&0\\0&0&1\\0&0&0\end{bmatrix}.
\]

Then \(W_0^2=0\), while \((W_q^2)_{1,3}=1\). The coefficient direction
\(c_{k,1}=(0,0,1)^\top\) lies in
\(\ker X_1^{\Phi}(W_0)\) but not in
\(\ker X_1^{\Phi}(W_q)\). Thus the retained object cannot answer this
query.

For the structured-positive fixture, set \(W_0=P\). For every row, the
columns \(e_i\), \(P_{i,:}^{\top}\) and \((P^2)_{i,:}^{\top}\) are the
three distinct standard basis vectors. Hence every row design has rank three,
and Corollary 1 makes every supplied query available within the declared
two-hop diagonal class.

## 8. Counterexample ledger and scope

| Attempt | Result | Consequence |
| --- | --- | --- |
| (N<m+1) | Full column rank is impossible | Full rank is only a sufficient condition; use the exact kernel test. |
| (W_q=W_0) | Kernel and row spaces are equal | Matched-topology availability does not establish topology transfer. |
| Rank-deficient (X_i(W_0)) | Some queries pass and others fail | Rank deficiency alone does not imply outside target. |
| Reverse row-space inclusion | Gives the wrong kernel direction | The required direction is row(query) contained in row(retained). |
| Endpoint omits the operator tuple | Projection argument is unavailable | Equivalence with the complete endpoint then requires a separate injectivity proof. |
| Represent \(W^2\) by a one-hop row-separable map at \(W=P\) | Every row of \(P^2\) lies outside the span of the corresponding rows of \(I\) and \(P\) | The two-hop function class strictly contains the one-hop class on a domain containing \(P\). |
| Floating-point rank tolerance | Not part of the algebraic theorem | Numerical rank diagnostics cannot replace exact factorization. |

The theorem is representation-level. It does not imply statistical
identification, numerical conditioning, estimator recovery, response
stability or causal interpretation.
