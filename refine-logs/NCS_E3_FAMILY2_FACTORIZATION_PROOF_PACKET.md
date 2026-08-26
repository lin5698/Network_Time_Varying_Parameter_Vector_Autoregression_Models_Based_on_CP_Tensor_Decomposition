# NCS E3 Family-2 Factorization Proof Packet

Date: 2026-07-22

Status: `SOURCE_ONLY`, `BLIND_REVIEW_RECEIPT_GOVERNED`, `NOT_AUTHORIZED`.

This packet proves only an algebraic representation statement for the declared
diagonal Family-2 operator. It provides no estimator guarantee, numerical
stability result, recovery result, uncertainty result, scientific outcome or
execution authorization. `PAPER_CLAIM_AUDIT=BLOCKED` and
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling.

## 1. Scope, domains and notation

Fix integers `N >= 1`, `p >= 1` and `H_max >= 1`. Let `W_0, W_q` belong to
`\mathbb{R}^{N\times N}`, with the same fixed node order. Define `W^2 := W W` exactly; no
post-square normalization, diagonal deletion, projection or reference-topology
substitution is part of this packet.

For each lag `k` and row `i`, the coefficient vector is

$$
c_{k,i}=(c_{0,k,i},c_{1,k,i},c_{2,k,i})^T \in \mathbb{R}^3,
$$

and `C_{j,k}=diag(c_{j,k,1},...,c_{j,k,N})`. The Family-2 operator is

$$
G_{k,c}(W)=C_{0,k}+C_{1,k}W+C_{2,k}W^2.
$$

Write the row coefficient and operator spaces as

$$
\mathcal C_{N,p}=\bigoplus_{k=1}^p\bigoplus_{i=1}^N \mathbb{R}^3,
\qquad
\mathcal D_{N,p}=\bigoplus_{k=1}^p\bigoplus_{i=1}^N \mathbb{R}^N
\cong\bigoplus_{k=1}^p \mathbb{R}^{N\times N}.
$$

Write `\mathcal G_{N,p}=(\mathbb{R}^{N\times N})^p`. The displayed
isomorphism is fixed, not implicit: define the linear reshape map

$$
\mathscr R:\mathcal D_{N,p}\longrightarrow\mathcal G_{N,p},
\qquad
[\mathscr R(d)_k]_{i,:}=d_{k,i}^T.
$$

Its inverse reads each matrix row as a column. Thus row-coordinate objects and
operator tuples are never silently identified in the argument below.

For `i in {1,...,N}`, define the exact row design matrix

$$
X_i(W)=\left[e_i,\ W_{i,:}^T,\ (W^2)_{i,:}^T\right] \in \mathbb{R}^{N\times 3}.
$$

The `i`-th row of `G_{k,c}(W)`, written as a column, is exactly
`X_i(W)c_{k,i}`. Thus no orientation convention is implicit: if `d_{k,i}`
denotes that column, then

$$
d_{k,i}=X_i(W_0)c_{k,i}.
$$

Define the observed-collapse map and the query-operator map by

$$
T^{(2)}_{W_0}(c)=\left(X_i(W_0)c_{k,i}\right)_{k,i},
\qquad
Q^{G,(2)}_{W_q}(c)=\left(X_i(W_q)c_{k,i}\right)_{k,i}.
$$

Both maps are linear from `\mathcal C_{N,p}` to `\mathcal D_{N,p}`.
After the declared reshape `\mathscr R`, they are respectively the `p`
collapsed operators at `W_0` and the `p` query operators at `W_q`.

## 2. Full endpoint as a deterministic composition

For a tuple `g=(G_1,...,G_p)` in `\mathcal G_{N,p}`, let
`\mathcal C(g)\in\mathbb{R}^{Np\times Np}` be the declared companion matrix
and let `J=[I_N,0,...,0]\in\mathbb{R}^{N\times Np}`. Define the deterministic,
generally nonlinear map

$$
\Psi_{p,H_{max}}:\mathcal G_{N,p}\longrightarrow
\mathcal G_{N,p}\times(\mathbb{R}^{N\times N})^{H_{max}},
\qquad
\Psi_{p,H_{max}}(g)=
\left(\{G_k\}_{k=1}^p,
\{J\,\mathcal C(g)^hJ^T\}_{h=1}^{H_{max}}\right).
$$

This is a deterministic finite algebraic map. It includes the full operator
tuple as its first component. Hence the projection `pi_G` onto that component
satisfies

$$
\pi_G \circ \Psi_{p,H_{max}}=id.
$$

The declared full-endpoint query map is

$$
Q^{E,(2)}_{W_q}=\Psi_{p,H_{max}}\circ\mathscr R\circ Q^{G,(2)}_{W_q}.
$$

This definition resolves the distinction between an operator-query theorem and
the rankable endpoint: the endpoint does not discard the operator tuple.

## 3. Linear factorization lemma

**Lemma 1 (kernel criterion).** Let `T: V -> U` and `Q: V -> Z` be linear maps
between real vector spaces. Then a linear `F: im(T) -> Z` exists with
`Q=F circ T` if and only if `ker(T) subseteq ker(Q)`.

**Proof.** If `Q=F circ T`, then `T(v)=0` implies `Q(v)=F(0)=0`, giving the
kernel inclusion. Conversely, assume the inclusion. For every `u` in `im(T)`,
choose `v` such that `u=T(v)` and set `F(u)=Q(v)`. If both `v` and `v'` map to
`u`, then `v-v'` is in `ker(T)`, hence in `ker(Q)`, so `Q(v)=Q(v')`. Therefore
`F` is well-defined. Its linearity follows from linearity of `T` and `Q`, and
the defining relation gives `Q=F circ T`. QED.

No probability, limit, rank approximation or floating-point computation is
used in this lemma.

## 4. Family-2 factorization theorem

**Theorem 1 (rowwise exact query factorization).** For the diagonal Family-2
class above, the following are equivalent:

$$
Q^{G,(2)}_{W_q}\text{ admits a linear factor through }T^{(2)}_{W_0}
\quad\Longleftrightarrow\quad
\ker X_i(W_0)\subseteq\ker X_i(W_q)
\quad\text{for every }i.
$$

They are also equivalent to the existence of a deterministic, not necessarily
linear map

$$
K:\operatorname{im}(T^{(2)}_{W_0})\longrightarrow
\mathcal G_{N,p}\times(\mathbb{R}^{N\times N})^{H_{max}}
$$

such that

$$
Q^{E,(2)}_{W_q}=K\circ T^{(2)}_{W_0}.
$$

**Proof.** By the direct-sum definitions,

$$
\ker T^{(2)}_{W_0}=
\bigoplus_{k=1}^p\bigoplus_{i=1}^N\ker X_i(W_0),
\qquad
\ker Q^{G,(2)}_{W_q}=
\bigoplus_{k=1}^p\bigoplus_{i=1}^N\ker X_i(W_q).
$$

The first direct-sum kernel is contained in the second exactly when every
rowwise inclusion holds: necessity follows by placing an arbitrary vector from
one row kernel in its single direct-sum coordinate; sufficiency follows by
componentwise inclusion. Lemma 1 then gives the stated equivalence for the
query-operator map.

If `Q^{G,(2)}_{W_q}=F circ T^{(2)}_{W_0}` with `F` linear, then
`Q^{E,(2)}_{W_q}=(Psi_{p,H_max} circ \mathscr R circ F) circ T^{(2)}_{W_0}`,
so deterministic endpoint factorization follows; `Psi_{p,H_max}` need not be
linear. Conversely, suppose `Q^{E,(2)}_{W_q}=K circ T^{(2)}_{W_0}` for a
deterministic `K`. If `T^{(2)}_{W_0}(c)=T^{(2)}_{W_0}(c')`, their endpoints
agree. Projection onto the retained operator tuple gives
`\mathscr R(Q^{G,(2)}_{W_q}(c))=\mathscr R(Q^{G,(2)}_{W_q}(c'))`; injectivity of
`\mathscr R` gives `Q^{G,(2)}_{W_q}(c)=Q^{G,(2)}_{W_q}(c')`. Taking `c'=0` for
any vector in the kernel shows
`ker T^{(2)}_{W_0} subseteq ker Q^{G,(2)}_{W_q}`. Lemma 1 then supplies the
required linear factor for `Q^{G,(2)}_{W_q}`. QED.

## 5. Full-rank structured-positive corollary

**Corollary 1.** If `rank X_i(W_0)=3` for every row `i`, then every query
topology `W_q` factors through the observed collapse within this diagonal
Family-2 representation class.

**Proof.** Full column rank gives `ker X_i(W_0)={0}` for every `i`; the
rowwise inclusions in Theorem 1 are therefore automatic. A left inverse
`L_i` of `X_i(W_0)` exists, so the observed row identifies
`c_{k,i}=L_i d_{k,i}` exactly. This is a representation statement only. It
does not state that a fitted estimator finds `d_{k,i}`, that the inverse is
well-conditioned, or that a response is stable. QED.

## 6. Exact fixture derivations

All fixture statements are finite integer-matrix identities. They are not
simulations and do not create `L_G`, `L_R`, recovery scores or outcomes.

### F1 structural negative

Let

$$
P=\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix},
\qquad W_0=P,\quad W_q=P^2.
$$

For Family 1, compare `(A,B)=(0,0)` with `(A,B)=(-P,I)`. At `W_0`,
`-P+IP=0`, so the two collapsed operators agree. At `W_q`, the second world
is `-P+P^2`, which is nonzero because `P != P^2`; the first remains zero.
Therefore the collapsed representation cannot answer this query and is
`OUTSIDE_TARGET`.

### F2 unrestricted structural negative

Use the same `P`, and compare the zero triple with

$$
(C_0,C_1,C_2)=(-P-2P^2,I,2I).
$$

At `P`, the latter equals `-P-2P^2+P+2P^2=0`. Since `P^3=I`, at `P^2` it
equals `-P-2P^2+P^2+2P=P-P^2`, which is nonzero. This fixture is deliberately
unrestricted and cannot be used to claim non-identification for the declared
diagonal recovery class.

### F2 diagonal structural negative

Let

$$
W_0=\begin{bmatrix}0&1&0\\0&0&0\\0&0&0\end{bmatrix},
\qquad
W_q=\begin{bmatrix}0&1&0\\0&0&1\\0&0&0\end{bmatrix}.
$$

Then `W_0^2=0`, while `(W_q^2)_{1,3}=1`. Compare the zero blocks with
`C_2=diag(1,0,0)` and `C_0=C_1=0`. The two worlds agree at `W_0` but differ
at `W_q`. Equivalently, `X_1(W_0)` has rank two and `X_1(W_q)` has rank three,
so a nonzero vector in `ker X_1(W_0)` cannot be contained in the zero kernel
of `X_1(W_q)`. The query is `OUTSIDE_TARGET`.

### F2 diagonal structured positive

For `W_0=P`, the three row matrices are permutations of the identity:

$$
X_1(P)=I_3,
\quad
X_2(P)=\begin{bmatrix}0&0&1\\1&0&0\\0&1&0\end{bmatrix},
\quad
X_3(P)=\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix}.
$$

Each has determinant `+1`, hence rank three. Corollary 1 classifies the
declared diagonal representation as `AVAILABLE through identified inverse` at
the supplied query `P^2`.

### Non-equivalence with a fixed one-hop family

Let

$$
V=\begin{bmatrix}0&1\\1&0\end{bmatrix}.
$$

Suppose one fixed pair `(A,B)` satisfied `W^2=A+BW` for all
`W` in `{0,V,2V}`. At zero, `A=0`. At `V`, `BV=I`, hence `B=V` after right
multiplication by `V`. At `2V`, the one-hop expression is `B(2V)=2I`, whereas
`(2V)^2=4I`, a contradiction. Thus `W^2` is not merely a relabelled fixed
one-hop map on this prespecified topology set.

## 7. Counterexample and boundary ledger

| Check | Result | Consequence |
| --- | --- | --- |
| `N=1` or any row with rank below three | Allowed by Theorem 1; no automatic availability | Do not infer identifiability from the diagonal parameterization alone. |
| `W_q=W_0` | Kernel inclusion is equality | Query factorization is available, but this says nothing about topology transfer. |
| Unrestricted F2 fixture | Exact negative only | It cannot refute the diagonal full-rank corollary. |
| Endpoint omits `G_1:p` | The projection argument fails | Such an endpoint is outside this theorem's scope. |
| Floating-point rank | Not used | It cannot replace exact algebra or the theorem. |

## 8. Proof-obligation closure state

The algebraic obligations in Sections 1--7 are written out. A blind-review
result is valid for this exact packet only when a fresh read-only receipt binds
its SHA-256 and records verdict `PASS` with no open findings. That receipt is
an audit record, not a candidate-ready transition: the packet remains
`SOURCE_ONLY` and `NOT_AUTHORIZED`, and a future preflight must refuse without
every separately required candidate-ready artifact.
