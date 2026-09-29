This supplementary note expands the propagation objects and proves the representation results used in the main manuscript. The study has $N$ units, lag order $p$ and optional exogenous covariates $x_t$. The reported label $t$ is the target date after a rolling window containing observations through $t-1$. Theorem 1 covers row-separable finite-basis operators. Proposition 1 applies separately to unrestricted one-hop matrix blocks. Corollary 1 identifies a diagonal one-hop class in which a collapsed map admits an explicit inverse.

For an observation index $\tau$ inside the rolling window ending at reported date $t$, the fitted equation is

$$
y_{\tau} = c_t + \sum_{k=1}^{p} A_{k,t} y_{\tau-k} + \sum_{k=1}^{p} B_{k,t} W_{\tau-k} y_{\tau-k} + C_t x_{\tau} + \varepsilon_{\tau}.
$$

Thus estimation uses the lag-specific historical exposure $W_{\tau-k}y_{\tau-k}$, exactly as in the implemented design. Response evaluation is a distinct operation. Define $\bar W_t:=W_{t-1}$ as the last topology available inside the window labelled by target date $t$. After the rolling coefficients have been estimated and reconstructed, a supplied matrix $W$ replaces the historical exposure matrices in the finite-horizon recursion while $A_{k,t}$, $B_{k,t}$, $\Sigma_t$, the shock and the horizon are held fixed. The observed-topology readout uses $\bar W_t$.

It is useful to distinguish the coefficient blocks from the propagation operators they generate. For any supplied topology matrix, the operator is the direct coefficient block plus the network coefficient block multiplied by that supplied topology:

$$
M_{k,t}(W)=A_{k,t}+B_{k,t}W.
$$

At reported target date $t$, the total dynamic recursion evaluates this operator at the last-available topology $\bar W_t$. The direct-only recursion evaluates it at zero network mediation. The frozen-topology recursion evaluates it at the pre-period benchmark topology $W_{pre}$. The reported propagation measures are functions of differences among these finite-horizon recursions. This notation clarifies why the paper treats the explicit network block as part of the estimand: each response is defined by switching a block or topology argument in the operator, not by post hoc attribution of a reduced-form forecast.

## Exact finite-basis query certificate

Fix integers $N,p\geq1$ and $m\geq0$. Let $\mathcal W\subseteq\mathbb R^{N\times N}$ be a declared topology domain with fixed node order. Choose basis maps

$$
\Phi_r:\mathcal W\longrightarrow\mathbb R^{N\times N},
\qquad r=0,\ldots,m.
$$

The maps may be nonlinear in $W$. For lag $k$, define diagonal coefficient matrices $C_{r,k}=\operatorname{diag}(c_{r,k,1},\ldots,c_{r,k,N})$ and the row-separable operator

$$
G_{k,c}^{\Phi}(W)=\sum_{r=0}^{m}C_{r,k}\Phi_r(W).
$$

For row $i$, write $c_{k,i}=(c_{0,k,i},\ldots,c_{m,k,i})'$ and

$$
X_i^{\Phi}(W)=
\left[\Phi_0(W)_{i,:}',\ldots,\Phi_m(W)_{i,:}'\right]
\in\mathbb R^{N\times(m+1)}.
$$

The transpose of row $i$ of $G_{k,c}^{\Phi}(W)$ is $X_i^{\Phi}(W)c_{k,i}$. Define

$$
\mathcal C_{N,p,m}=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}\mathbb R^{m+1},
\qquad
\mathcal D_{N,p}=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}\mathbb R^{N}.
$$

For $W_0,W_q\in\mathcal W$, the retained-collapse and queried-operator maps are

$$
T_{W_0}^{\Phi}(c)=\left(X_i^{\Phi}(W_0)c_{k,i}\right)_{k,i},
\qquad
Q_{W_q}^{G,\Phi}(c)=\left(X_i^{\Phi}(W_q)c_{k,i}\right)_{k,i}.
$$

Both maps are linear in $c$. Let $\mathscr R:\mathcal D_{N,p}\to(\mathbb R^{N\times N})^p$ be the fixed row-to-matrix reshape isomorphism. Fix a finite integer $H\geq1$. For an operator tuple $g=(G_1,\ldots,G_p)$, define the complete finite-horizon endpoint

$$
\Psi_{p,H}(g)=\left(g,\{J\mathcal C(g)^hJ'\}_{h=1}^{H}\right),
$$

where $\mathcal C(g)$ is the standard lag-$p$ companion matrix. This endpoint retains $g$ as its first component. Therefore its operator projection $\pi_G$ satisfies $\pi_G\circ\Psi_{p,H}=\operatorname{id}$. The queried endpoint is

$$
Q_{W_q}^{E,\Phi}=\Psi_{p,H}\circ\mathscr R\circ Q_{W_q}^{G,\Phi}.
$$

**Lemma 1 (kernel factorization criterion).** Let $T:V\to U$ and $Q:V\to Z$ be linear maps between real vector spaces. A unique linear $F:\operatorname{im}(T)\to Z$ satisfies $Q=F\circ T$ if and only if $\ker T\subseteq\ker Q$.

**Proof.** If $Q=F\circ T$, then $T(v)=0$ implies $Q(v)=F(0)=0$. Conversely, assume the kernel inclusion. For $u\in\operatorname{im}(T)$, choose $v$ with $T(v)=u$ and set $F(u)=Q(v)$. If $T(v)=T(v')$, then $v-v'\in\ker T\subseteq\ker Q$, so $Q(v)=Q(v')$. Thus $F$ is well-defined. Linearity follows from the linearity of $T$ and $Q$. Uniqueness holds because every element of $\operatorname{im}(T)$ equals $T(v)$ for some $v$.

**Theorem 1 (exact finite-basis query certificate).** Fix $W_0,W_q\in\mathcal W$. The following statements are equivalent.

1. A linear $F:\operatorname{im}(T_{W_0}^{\Phi})\to\mathcal D_{N,p}$ satisfies $Q_{W_q}^{G,\Phi}=F\circ T_{W_0}^{\Phi}$.
2. For every row $i$, $\ker X_i^{\Phi}(W_0)\subseteq\ker X_i^{\Phi}(W_q)$.
3. For every row $i$, $\operatorname{row}X_i^{\Phi}(W_q)\subseteq\operatorname{row}X_i^{\Phi}(W_0)$ as subspaces of $\mathbb R^{m+1}$.
4. A deterministic map $K$ on $\operatorname{im}(T_{W_0}^{\Phi})$ satisfies $Q_{W_q}^{E,\Phi}=K\circ T_{W_0}^{\Phi}$.

**Proof.** Each direct-sum coordinate acts only on its own coefficient vector. Therefore

$$
\ker T_{W_0}^{\Phi}
=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}\ker X_i^{\Phi}(W_0),
\qquad
\ker Q_{W_q}^{G,\Phi}
=\bigoplus_{k=1}^{p}\bigoplus_{i=1}^{N}\ker X_i^{\Phi}(W_q).
$$

The first direct sum is contained in the second exactly when every rowwise inclusion in statement 2 holds. Necessity follows by placing an arbitrary row-kernel vector in one direct-sum coordinate. Sufficiency follows componentwise. Lemma 1 proves the equivalence of statements 1 and 2.

For every real matrix $X$, $\ker X=(\operatorname{row}X)^\perp$. Taking orthogonal complements proves the equivalence of statements 2 and 3, including the reversed containment direction.

If statement 1 holds, then $K=\Psi_{p,H}\circ\mathscr R\circ F$ gives statement 4. Conversely, suppose statement 4 holds and two coefficient objects have the same retained value. Their complete endpoints agree. Applying $\pi_G$ and then $\mathscr R^{-1}$ shows that their queried operators agree. Hence $\ker T_{W_0}^{\Phi}\subseteq\ker Q_{W_q}^{G,\Phi}$, and Lemma 1 gives statement 1.

If $\operatorname{rank}X_i^{\Phi}(W_0)=m+1$ for every row, the retained row kernels are zero. Every supplied query then factors through the retained object. This full-column-rank condition is sufficient, not necessary, and requires $N\geq m+1$. When it fails, the exact kernel inclusion still decides each specified query.

The one-hop diagonal class uses $\Phi=(I,W)$. Under zero-diagonal fitted and queried topologies, Theorem 1 reduces to the zero-row condition in Corollary 1 below. The two-hop diagonal class uses $\Phi=(I,W,W^2)$, where $W^2=WW$ without renormalization or diagonal deletion. Its exact certificate is

$$
\ker[e_i,W_{0,i,:}',(W_0^2)_{i,:}']
\subseteq
\ker[e_i,W_{q,i,:}',(W_q^2)_{i,:}']
\quad\text{for every }i.
$$

The two-hop family is strictly larger than the one-hop row-separable family on every declared weighted-topology domain containing the following matrix:

$$
P=\begin{bmatrix}0&1&0\\0&0&1\\1&0&0\end{bmatrix}.
$$

The matrix $P$ is nonnegative, row-stochastic and zero-diagonal. The one-hop maps have form $D_0I+D_1W$, while the two-hop maps have form $C_0I+C_1W+C_2W^2$, with fixed diagonal coefficients. The latter contains the former by setting $C_2=0$. It also contains $W\mapsto W^2$. If that map were one-hop, fixed diagonal $D_0,D_1$ would satisfy $P^2=D_0I+D_1P$. For every row $i$, however, $e_i'$, $P_{i,:}$ and $(P^2)_{i,:}$ are three distinct standard basis vectors. Thus $(P^2)_{i,:}$ lies outside $\operatorname{span}\{e_i',P_{i,:}\}$, a contradiction. The inclusion is strict on every declared topology domain containing $P$.

Two exact fixtures expose the rank boundary. Set

$$
W_0=\begin{bmatrix}0&1&0\\0&0&0\\0&0&0\end{bmatrix},
\qquad
W_q=\begin{bmatrix}0&1&0\\0&0&1\\0&0&0\end{bmatrix}.
$$

Then $W_0^2=0$, while $(W_q^2)_{1,3}=1$. The coefficient direction $(0,0,1)'$ lies in the retained row-one kernel but not in the queried kernel, so the query is unavailable. By contrast, setting $W_0=P$ gives three distinct standard basis columns in every row design. Every retained row design has rank three, and every supplied two-hop query is available. These fixtures are representation-level results; they do not establish two-hop estimator recovery.

## Exact query factorization from a single-topology object

Fix a lag and date, suppress their subscripts, and write the map stored at the fitted topology $W_0$ as

$$
D=M(W_0)=A+BW_0.
$$

For fixed $W_0$ and a queried topology $W_1$, define

$$
T_{W_0}(A,B)=A+BW_0,
\qquad
Q_{W_1}(A,B)=A+BW_1.
$$

**Proposition 1 (exact unrestricted-block query-factorization boundary).** Let $N\geq 1$ and let $(A,B)$ range over all pairs of real $N\times N$ matrices. There exists a function $F$ such that

$$
Q_{W_1}(A,B)=F\!\left(T_{W_0}(A,B)\right)
$$

for every $(A,B)$ if and only if $W_1=W_0$.

**Proof.** If $W_1=W_0$, then $Q_{W_1}=T_{W_0}$, so the identity function supplies the factorization. Conversely, suppose $W_1\neq W_0$. Compare the two admissible block pairs

$$
(A,B)=(0,0)
\qquad\text{and}\qquad
(\widetilde A,\widetilde B)=(-W_0,I).
$$

Both pairs give the same collapsed map,

$$
T_{W_0}(0,0)=0=T_{W_0}(-W_0,I),
$$

whereas their queried operators are

$$
Q_{W_1}(0,0)=0,
\qquad
Q_{W_1}(-W_0,I)=W_1-W_0\neq 0.
$$

No function of the common collapsed map can return both queried values. This proves necessity and the equivalence.

The result includes the boundary cases omitted by a generic non-injectivity statement. The fitted-topology total operator is always determined because $Q_{W_0}=D$. Direct-only evaluation is $Q_0$ and therefore factors through $D$ if and only if $W_0=0$. Any genuine alternative-topology operator with $W_1\neq W_0$ fails to factor through the collapsed object over this unrestricted class. The network-component query $BW_1$ is likewise not generally determined by $D$. These are operator-level statements. A scalar finite-horizon response inherits non-identification only if it is nonconstant along the constructed equivalence class; for example, a zero-horizon response or a zero shock map can remain unchanged even when $Q_{W_1}$ differs.

**Corollary 1 (diagonal structured inverse for zero-diagonal topology).** Restrict $A=\operatorname{diag}(a)$ and $B=\operatorname{diag}(b)$, and suppose $W_0$ has zero diagonal. The query $Q_{W_1}$ factors through $T_{W_0}$ on this diagonal class if and only if every zero row of $W_0$ is also a zero row of $W_1$. In particular, $T_{W_0}$ is injective when every row of $W_0$ is nonzero. In that case, writing $w_{0,i,-i}$ and $D_{i,-i}$ for row $i$ with its diagonal entry removed,

$$
a_i=D_{ii},
\qquad
b_i=\frac{D_{i,-i}w_{0,i,-i}'}{\|w_{0,i,-i}\|_2^2},
$$

so every supplied-topology operator is determined from $(D,W_0)$.

**Proof.** Row $i$ of the collapsed map is $D_{i\cdot}=a_i e_i'+b_iw_{0,i\cdot}$. Because $W_{0,ii}=0$, a nonzero $w_{0,i\cdot}$ is linearly independent of $e_i'$, which gives the displayed inverse. If row $i$ of $W_0$ is zero, $D_{i\cdot}=a_i e_i'$ contains no information about $b_i$, while row $i$ of the queried operator is $a_i e_i'+b_iw_{1,i\cdot}$. It is independent of the unidentified $b_i$ exactly when row $i$ of $W_1$ is also zero. Applying this argument row by row proves the result.

This corollary states a structured exception and shows why Proposition 1 must not be transferred from the unrestricted class to diagonal blocks without checking the topology rows. The collapsed benchmark ablation nevertheless does not enforce the diagonal image conditions, verify the nonzero-row condition or apply the displayed inverse after smoothing. Its component and alternative-topology readouts are therefore outside its declared reconstruction target, not universally impossible to recover. The separated implementation stores reconstructed $A$ and $B$ blocks directly and evaluates the topology argument explicitly.
