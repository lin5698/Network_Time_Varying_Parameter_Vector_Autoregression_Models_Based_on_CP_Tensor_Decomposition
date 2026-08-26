### Query certificate

The method is specified from the intended response query backward. It asks whether one fitted coefficient path can be evaluated under a supplied topology rather than re-fitted after the topology changes. The query first fixes the topology, coefficient path, shock normalization, horizon and readout. The certificate then determines whether the fitted object can evaluate that topology argument from retained blocks or a verified inverse. If the endpoint is available, design identification asks whether observed regressors contain enough independent variation to distinguish the required blocks; numerical recovery and finite-horizon stability are assessed only afterwards. The method therefore returns a qualified response or stops at the first unsupported requirement. A representation-level absence is labelled outside target, whereas an available endpoint with unresolved identification, recovery or stability remains unvalidated for the corresponding interpretation. Fit and one-step prediction cannot substitute for a missing query argument. Proof details and full notation are in Supplementary Notes 1 and 3; estimator performance is assessed in the controlled benchmarks.

### Finite-basis representation certificate

Let $\mathcal W$ be a declared topology domain and let $\Phi_0,\ldots,\Phi_m$ be fixed matrix-valued basis maps on that domain. For lag $k$, define the row-separable operator

$$
G_{k,c}^{\Phi}(W)=\sum_{r=0}^{m}C_{r,k}\Phi_r(W),
\qquad C_{r,k}=\operatorname{diag}(c_{r,k,1},\ldots,c_{r,k,N}).
$$

For row $i$, collect the topology basis in

$$
X_i^{\Phi}(W)=
\left[\Phi_0(W)_{i,:}',\ldots,\Phi_m(W)_{i,:}'\right].
$$

The retained map $T_{W_0}^{\Phi}$ evaluates every lag and row at $W_0$. The query map $Q_{W_q}^{G,\Phi}$ evaluates the same coefficients at a supplied $W_q$.

**Theorem 1 (exact finite-basis query certificate).** Fix $W_0,W_q\in\mathcal W$. A unique linear evaluator on $\operatorname{im}(T_{W_0}^{\Phi})$ satisfies $Q_{W_q}^{G,\Phi}=F\circ T_{W_0}^{\Phi}$ if and only if, for every row $i$,

$$
\ker X_i^{\Phi}(W_0)\subseteq\ker X_i^{\Phi}(W_q).
$$

Equivalently, $\operatorname{row}X_i^{\Phi}(W_q)\subseteq\operatorname{row}X_i^{\Phi}(W_0)$ for every row. The same condition applies to a deterministic endpoint of the queried operator tuple alone, $Q^E=\Psi\circ\mathscr R\circ Q^G$. Here $\Psi$ must retain that tuple through a projection $\pi_G\circ\Psi=\operatorname{id}$. Full column rank of every retained row design is sufficient, but not necessary, for every supplied query.

The condition applies to one-hop $\Phi=(I,W)$ and two-hop $\Phi=(I,W,W^2)$ bases. These families are not relabellings. On a three-node directed cycle $P$, every row of $P^2$ lies outside the span of the corresponding rows of $I$ and $P$. Hence $W\mapsto W^2$ belongs to the two-hop class but not the one-hop row-separable class on any topology domain containing $P$. Supplementary Note 1 gives the full direct-sum proof, endpoint converse and exact boundary fixtures.

### Operator and representation boundary

The controlled benchmark uses the one-hop operator below and reconstructs unrestricted direct and network blocks separately. Beyond the row-separable theorem, unrestricted one-hop blocks provide a sharp negative boundary. The diagonal class then supplies a constructive positive certificate. For lag k and reported date t, the response-evaluation operator is

$$
M_{k,t}(W)=A_{k,t}+B_{k,t}W .
$$

The need to retain the blocks can be stated as an exact representation-sufficiency criterion. Fix a fitted topology $W_0$ and let $D_{k,t}=A_{k,t}+B_{k,t}W_0$ be the collapsed map. For a queried topology $W_1$, define $T_{W_0}(A,B)=A+BW_0$ and $Q_{W_1}(A,B)=A+BW_1$.

**Proposition 1 (exact unrestricted-block query-factorization boundary).** Let $N\geq 1$ and let $(A,B)$ range over all pairs of real $N\times N$ matrices. A function $F$ satisfying $Q_{W_1}=F\circ T_{W_0}$ for every $(A,B)$ exists if and only if $W_1=W_0$.

Sufficiency follows because the queried operator then equals the collapsed map. For necessity, if $W_1\neq W_0$, the block pairs $(0,0)$ and $(-W_0,I)$ both collapse to zero at $W_0$ but yield queried operators $0$ and $W_1-W_0$. Over this unrestricted class, the fitted-topology total operator is always determined, direct-only evaluation is determined only when $W_0=0$, and a genuine alternative-topology operator with $W_1\neq W_0$ is not determined. A scalar response inherits this non-identification only when it changes with the altered operator.

**Corollary 1 (diagonal structured inverse).** Restrict $A$ and $B$ to diagonal matrices and let $W_0$ have zero diagonal. Then $Q_{W_1}$ factors through $T_{W_0}$ if and only if every zero row of $W_0$ is also zero in $W_1$. When every row of $W_0$ is nonzero, $a_i=D_{ii}$ and $b_i=D_{i,-i}w_{0,i,-i}'/\|w_{0,i,-i}\|_2^2$, so any supplied-topology operator can be recovered from $(D,W_0)$. Proposition 1 therefore does not establish non-identification for this structured class. The collapsed benchmark ablation does not enforce this image or apply the rowwise inverse after smoothing; its structural endpoints are outside its declared reconstruction target rather than mathematically impossible to recover. Supplementary Note 1 gives the proof and zero-row boundary.

### Readout and design separation

Here $W$ is a supplied exposure matrix for response evaluation on a fixed fitted path. The target date $t$ follows a rolling window containing observations through $t-1$, and $\bar W_t:=W_{t-1}$ denotes the last exposure matrix available inside that window. When a frozen-topology comparator is used, $W_{pre}$ must be declared before response evaluation from a predetermined reference interval. Topology laws of motion, memory kernels and nonlinear contagion rules are outside this response-evaluation argument.

The total response recursion evaluates this operator at the date-specific topology. The direct-only recursion evaluates it at zero network mediation, which leaves the direct coefficient block alone. The frozen-topology recursion evaluates it at the pre-period benchmark topology with the same coefficient blocks. The network-mediated propagation object is the finite-horizon difference between these recursions. It is computationally defined when the fitted representation stores the separated blocks and the topology argument. Statistical interpretation additionally requires a design that distinguishes lagged direct regressors from lagged network-exposure regressors and a predetermined exposure matrix for the response recursion.

Design separation is distinct from penalized numerical uniqueness. For a rolling design, let $Z$ contain all network-exposure lag blocks and let $X$ contain the intercept, direct lags and declared exogenous regressors. Projecting $Z$ off the column span of $X$ exposes network directions that can be absorbed by the direct or nuisance design. A small minimum eigenvalue of the residualized joint Gram matrix indicates high worst-case sensitivity, whereas a positive ridge penalty can still make the numerical solution unique. Supplementary Note 3 gives the corresponding joint-ridge Schur complement. The controlled recovery experiment evaluates the resulting operator errors directly rather than treating penalized solvability as identification evidence.

### Reconstruction target

The low-rank stage is interpretable when the local coefficient path is noisy and close to a low-dimensional temporal trajectory. It regularizes the separated coefficient tensor while retaining the block index needed for the reported operator. Its recovery advantage is an empirical question: the benchmark compares separated CP reconstruction with unrestricted local rolling estimation under declared endpoint and replication contracts.

### Finite-horizon transfer

Finite-horizon stability links coefficient recovery to response recovery. If the companion powers generated by the evaluated operators remain bounded over the reported horizon, perturbation bounds map block-level coefficient error continuously into response error. The same argument applies to observed, direct-only and frozen-topology recursions by evaluating the topology argument at $\bar W_t$, zero or a predeclared $W_{pre}$. The fixed positive denominator floor makes the ratio summaries continuous over the finite-dimensional response entries.

**Proposition 2 (finite-horizon response transfer).** Fix a reported date, a supplied topology matrix $W$ and an integer horizon $H\geq 1$. Throughout, $\|\cdot\|_2$ is the spectral matrix norm. Let $\mathcal{C}(W)$ and $\widehat{\mathcal{C}}(W)$ be the true and reconstructed companion matrices, and suppose

$$
\max_{0\leq r\leq H}\left\{\|\mathcal{C}(W)^r\|_2,\|\widehat{\mathcal{C}}(W)^r\|_2\right\}\leq K
$$

for $K\geq 1$. Let the fixed companion-state selection map $J$ satisfy $\|J\|_2=\|J'\|_2=1$, and let the true and reconstructed responses use the same shock-normalization map $S$ with $\|S\|_2\leq L_S$. Define $R_h(W)=J\mathcal{C}(W)^hJ'S$ and its reconstructed analogue. Then

$$
\sum_{h=1}^{H}\left\|\widehat{R}_{h}(W)-R_{h}(W)\right\|_2
\leq
L_SK^{2}\frac{H(H+1)}{2}
\left\|\widehat{\mathcal{C}}(W)-\mathcal{C}(W)\right\|_2.
$$

For the standard lag-$p$ companion construction, the spectral norm of the companion difference is bounded by the square-root sum of squared lag-operator errors and hence by

$$
\sum_{k=1}^{p}\left\{\|\widehat{A}_{k,t}-A_{k,t}\|_2+\|W\|_2\|\widehat{B}_{k,t}-B_{k,t}\|_2\right\}.
$$

The statement applies separately at observed, zero-network and frozen-topology arguments. A simultaneous bound uses $K$ equal to the maximum power bound over all three true and reconstructed companion families. This proposition transfers a given separated-block error into a finite-horizon response bound. It does not establish a CP rank, CP-ALS global convergence or lower error than unrestricted local estimation. Supplementary Note 3 gives the proof; benchmark recovery results test the latter comparison.

### Interpretation boundary

Scientific interpretation is strongest when four conditions hold: the topology matrix is predetermined for the response recursion; the local design distinguishes direct lags from network exposure; reconstruction preserves separate direct and network blocks or an identified inverse; and finite-horizon stability is assessed when the supplied topology changes exposure. Controlled topology-measurement scenarios and an endpoint-aware recovery gate assess parts of this contract. They do not replace endpoint-specific recovery tests or convert a fixed-path contrast into a causal effect.
