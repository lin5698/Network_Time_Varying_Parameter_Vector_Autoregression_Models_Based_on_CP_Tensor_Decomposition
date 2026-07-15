# Derivation Package

## Target

建立一条可用于高影响重投稿的理论主线，把以下四个问题连接起来：

1. 一个 stored representation 何时足以回答指定的 topology-substitution query？
2. rolling design 何时能稳定地区分 direct 和 topology-mediated coefficient blocks？
3. block-preserving low-rank reconstruction 如何把局部估计噪声转化为 tensor reconstruction error？
4. coefficient-block error 如何统一传递到 observed、zero-network、frozen 和 higher-order topology responses？

目标不是证明当前 CP-ALS 一定收敛到全局最优，也不是把 supplied topology response 解释为因果效应。

## Status

COHERENT AFTER REFRAMING / EXTRA ASSUMPTION

现有 Proposition 1 可以保留为 response-transfer lemma，但不足以单独支撑“实质性方法推进”。理论对象需要从特定的 $A+BW$ 重构，提升为 query identifiability for topology-basis operators，并把 approximate low-rank optimization gap、local separation 和 topology measurement error 显式纳入端到端界。

## Invariant Object

组织整条推导的对象是 topology-indexed finite-horizon response query：

$$
\mathcal{R}_{t,H}(W;\Theta_t,S_t)
=
\left\{J\mathcal{C}_t(W)^hJ'S_t:0\leq h\leq H\right\},
$$

其中 $\Theta_t$ 存储所有 topology-basis coefficient blocks，$S_t$ 是 shock-normalization map，$\mathcal{C}_t(W)$ 是由 supplied topology $W$ 生成的 companion operator。

现有 observed、direct-only 和 frozen-topology readouts 都是这个 query family 的切片，而不是三个彼此独立的 estimands。

## Assumptions

### A1. Supplied topology

$W$ 是 response evaluation 的外生输入或预定 exposure object。理论不描述 topology formation law，也不从 response contrast 推导 causal effect。

### A2. Topology-basis operator class

对每个 lag $k$ 和 date $t$，

$$
M_{k,t}(W)=\sum_{m=0}^{q}B_{m,k,t}\Phi_m(W),
\qquad \Phi_0(W)=I.
$$

现有模型是 $q=1$、$B_{0,k,t}=A_{k,t}$、$\Phi_1(W)=W$ 的特例。扩散版本可取 $\Phi_m(W)=W^m$。

### A3. Query-specific topology excitation

对一个 rolling training prefix，令 $X$ 为 direct-lag design，$Z$ 为 topology-exposure design，$M_X=I-XX^\dagger$，并定义

$$
\widetilde Z=M_XZ,
\qquad
G_Z=n^{-1}\widetilde Z'\widetilde Z.
$$

完整 slope block recovery 需要 $\lambda_{\min}(G_Z)>0$。回答指定 topology query 不需要完整 recovery；它只要求 query map 的 kernel 包含 $\ker(\widetilde Z)$。数值版本使用冻结阈值 $\tau$ 的谱投影 $P_\tau$，把 singular values 小于 $\tau$ 的方向视为未被训练 design 稳定激发。该阈值只能由 calibration-prefix scale 和预先规定的 conditioning rule 确定，不能用 validation/evaluation prefixes、held-out endpoint error 或 truth 选择。阈值化后的 $\chi_\tau$ 只描述 unsupported query share；统计可恢复性还取决于 retained subspace 上的绝对 Gram scale 和 query-specific inverse amplification。不能用 full numerical rank 或 $\chi_\tau=0$ 代替 variance control。

### A4. Local approximation and noise

rolling window 内允许 coefficient drift。令 $R_t$ 表示把 time-varying path 近似为 local target 产生的 drift remainder，$U_t$ 表示 innovation。高概率 rate 版本还需要 mixing、tail 和 moment assumptions；确定性版本只需要控制 residualized moments。

### A5. Low-rank approximability

把所有 basis blocks、lags 和 dates 堆叠为 tensor $\Theta^*$. 存在 rank-$R$ bounded-factor tensor $\Theta_R$ 使

$$
a_R=\|\Theta_R-\Theta^*\|_F
$$

足够小。Exact CP rank 不是必需条件；$a_R$ 必须进入最终界。

### A6. Approximate optimizer

实现输出 $\widetilde\Theta$ 不必是全局 CP optimum，但满足 projection objective gap

$$
\|\widehat\Theta-\widetilde\Theta\|_F^2
\leq
\inf_{\Theta\in\mathcal C_R}
\|\widehat\Theta-\Theta\|_F^2+\epsilon_{opt}.
$$

multi-start CP-ALS 只能通过记录 objective gap、失败率和 sensitivity 来支持这一假设，不能被理论自动证明。

### A6b. End-to-end restricted curvature

若使用设计加权的端到端低秩 estimator，则经验 outcome loss 必须在候选路径与 truth 的差方向上满足 restricted strong convexity。其常数记为 $\kappa_{\mathcal C}>0$。该条件作用于由真实 design 激发的 coefficient directions；它不能控制 A3 定义的 unsupported query remainder。

### A7. Uniform finite-horizon stability

对 topology class $\mathcal W$ 中所有 $W$，true 和 reconstructed companion powers 满足

$$
\max_{0\leq h\leq H}
\left\{\|\mathcal C_t(W)^h\|,
\|\widehat{\mathcal C}_t(W)^h\|\right\}\leq K_H.
$$

### A8. Bounded topology and shock maps

$$
\sup_{W\in\mathcal W}\|\Phi_m(W)\|\leq L_{\Phi,m},
\qquad
\max\{\|S_t\|,\|\widehat S_t\|\}\leq L_S.
$$

### A9. Slice control for pointwise claims

Global tensor Frobenius error naturally yields average-over-date bounds。若要声明每个 date 的 pointwise bound，还需 temporal factor incoherence or a direct maximum-slice error condition：

$$
\max_t\|\widetilde\Theta_t-\Theta_t^*\|_F
\leq \mu_T T^{-1/2}\|\widetilde\Theta-\Theta^*\|_F.
$$

## Notation

- $B_{m,k,t}$：第 $m$ 个 topology basis、lag $k$、date $t$ 的 coefficient block。
- $\Phi_m(W)$：已知 topology feature/operator，例如 $I,W,W^2$。
- $D_\ell$：representation 在 stored topology $W_\ell$ 的 operator evaluation。
- $\mathsf S$：从 coefficient blocks 到 stored representation 的线性 map。
- $\mathsf T_*$：从 coefficient blocks 到 target query $W_*$ 的线性 map。
- $\eta_t$：local weak-separation constant。
- $\widetilde Z=M_XZ$：对 direct design residualize 后的 topology-exposure design。
- $P_\tau$：由 $\widetilde Z$ 的 singular values 大于冻结阈值 $\tau$ 的右奇异向量生成的 parameter-space projector。
- $\chi_\tau(W_*)$：target topology query 的 unsupported-direction certificate。
- $\alpha_\tau(W_*)$：target query 在 retained topology-design Gram 上的 inverse-amplification certificate。
- $\kappa_{\mathcal C}$：end-to-end loss 在候选低秩差集上的 restricted-curvature constant。
- $a_R$：rank-$R$ approximation error。
- $\epsilon_{opt}$：approximate projection optimization gap。
- $K_H$：finite-horizon companion-power bound。
- $\delta_S=\|\widehat S_t-S_t\|$：shock-normalization error。

## Derivation Strategy

采用以下顺序：

1. 先用纯线性代数给出 query identifiability 的必要且充分条件。
2. 用 residualized topology design 给出 query-specific excitation、support decomposition 和 abstention certificate。
3. 区分两阶段 local-estimate-then-project bound 与 design-weighted end-to-end estimator target。
4. 用 approximate low-rank inequality或 restricted-curvature argument连接 design loss 与 coefficient/query error。
5. 扩展现有 telescoping argument，得到对 topology class 统一的 response-transfer bound。
6. 把前述误差代入 response transfer，形成 end-to-end theorem；统计 rate 只在补充 mixing/tail assumptions 后给出。

## Derivation Map

1. **Exact identity**：stored evaluations 和 target query 都是 coefficient vector 的线性 maps。
2. **Theorem 1**：query identifiable iff $\ker(\mathsf S)\subseteq\ker(\mathsf T_*)$。
3. **Corollary 1**：single collapsed map 对 unrestricted $(A,B)$ 不识别新的 topology endpoint。
4. **Corollary 2**：multiple stored topologies 只需识别 target query direction，不一定要识别完整 $B$。
5. **Proposition 2**：在 residualized design 下，target query identifiable iff $\ker(\widetilde Z)\subseteq\ker(\mathsf T_*)$。
6. **Proposition 3**：$P_\tau$ 将 target query 分为可估计的 excited component 与不可由数据消除的 unsupported remainder。
7. **Proposition 4**：full-rank local ridge block error由 excitation、innovation moment、drift remainder 和 ridge bias 控制。
8. **Estimator target**：design-weighted end-to-end low-rank loss，而不是分别对 $M_{ref}$ 与 $B$ 做 unweighted projection。
9. **Proposition 5**：approximate rank-$R$ projection error由 $a_R$、local tensor error 和 $\epsilon_{opt}$ 控制；它只描述两阶段 comparator。
10. **Theorem 2**：对 bounded topology class 的 uniform finite-horizon response error bound。
11. **Corollary 3**：topology-response map 对 $W$ 的 Lipschitz sensitivity。
12. **Theorem 3 target**：把 design loss、query support 和 response transfer 合并为 average-date end-to-end bound；pointwise 版本使用 A9。

## Main Derivation

### Step 1. Query identifiability as a kernel condition

将所有 unknown blocks vectorize 为 $\theta$. Stored representation 写为

$$
r=\mathsf S\theta,
$$

target query 写为

$$
q_*=\mathsf T_*\theta.
$$

**Theorem 1 (query-specific identifiability).** 存在一个只依赖 stored representation 的 map $g_*$，使得对 parameter class 中所有 $\theta$ 都有

$$
\mathsf T_*\theta=g_*(\mathsf S\theta),
$$

当且仅当

$$
\ker(\mathsf S)\subseteq\ker(\mathsf T_*).
$$

**Proof classification: proposition.**

- 必要性：若 $h\in\ker(\mathsf S)$，则 $\theta$ 与 $\theta+h$ 有相同 stored representation。若 query 可由 representation 唯一决定，必须有 $\mathsf T_*h=0$。
- 充分性：若 kernel inclusion 成立，则 $\mathsf T_*$ 在 $\mathsf S$ 的 equivalence classes 上为常数，因此可以在 $\operatorname{range}(\mathsf S)$ 上定义 $g_*(\mathsf S\theta)=\mathsf T_*\theta$。该定义与代表元无关。

这一定理不要求先恢复全部 coefficient blocks；它只要求 representation 保留 target query 所需的方向。

### Step 2. First-order multiple-topology specialization

固定 coefficient blocks $A,B$，设

$$
D_\ell=A+BW_\ell,
\qquad \ell=0,\ldots,L.
$$

以 $D_0$ 为基准，

$$
\operatorname{vec}(D_\ell-D_0)
=
\left((W_\ell-W_0)'\otimes I_N\right)\operatorname{vec}(B).
$$

堆叠 $\ell=1,\ldots,L$ 得

$$
d=\mathsf S_B b,
\qquad
\mathsf S_B=
\begin{bmatrix}
(W_1-W_0)'\otimes I_N\\
\vdots\\
(W_L-W_0)'\otimes I_N
\end{bmatrix}.
$$

对于 target topology $W_*$，需要识别

$$
\mathsf T_*b=
\left((W_*-W_0)'\otimes I_N\right)b.
$$

因此 target endpoint identifiable iff

$$
\ker(\mathsf S_B)\subseteq
\ker\left((W_*-W_0)'\otimes I_N\right).
$$

完整 $B$ identifiable 是更强条件 $\operatorname{rank}(\mathsf S_B)=N^2$。论文应强调 query-specific condition，因为它比 full parameter identification 更精确。

single stored topology case 没有差分信息，$\mathsf S_B$ 的 kernel 是整个 block space。除非 $W_*=W_0$ 或 parameter class 有额外 restrictions，否则新的 endpoint 不可识别。这恢复现有 $H(W_1-W_0)$ 反例。

### Step 3. General topology-basis representation

令

$$
M(W)=\sum_{m=0}^{q}B_m\Phi_m(W).
$$

把 $b=[\operatorname{vec}(B_0)',\ldots,\operatorname{vec}(B_q)']'$ 堆叠后，每个 stored evaluation 都有线性形式

$$
\operatorname{vec}(M(W_\ell))
=
\left[
\Phi_0(W_\ell)'\otimes I,
\ldots,
\Phi_q(W_\ell)'\otimes I
\right]b.
$$

因此 Theorem 1 直接适用于 polynomial graph filters、multiple exposure channels 和其他预先指定的 linear topology dictionaries。这里是 exact identity，不是近似。

若 $\Phi_m$ 由数据学习并随 fitted parameters 改变，linear-map theorem 不再直接适用；该情形需要把 learned basis 纳入 parameter vector 或采用 local Jacobian approximation。

### Step 4. Topology excitation and supported-query decomposition

在一个 rolling training prefix 内，对每个 outcome equation 写

$$
y=Xm+Zb+u,
$$

其中 $m$ 是 reference-operator row，$b$ 是 topology-slope row，且 $Z$ 的第 $s$ 行来自 $(W_s-W_{ref})x_s$。令 $M_X=I-XX^\dagger$。Frisch--Waugh--Lovell residualization 给出 exact identity

$$
\widetilde y=M_Xy=\widetilde Zb+\widetilde u,
\qquad
\widetilde Z=M_XZ.
$$

#### Step 4a. Exact query-support condition

对 target topology $W_*$，令 $\Delta W_*=W_*-W_{ref}$。该 row 的 topology-slope query 为

$$
q_*(b)=\Delta W_*'b
\equiv \mathsf T_*b.
$$

训练 design 对 $b$ 只存储 $\widetilde Zb$。因此由 Theorem 1，存在只依赖 $\widetilde Zb$ 的 map 恢复 $q_*(b)$，当且仅当

$$
\ker(\widetilde Z)\subseteq\ker(\Delta W_*').
$$

等价地，若 $P=\widetilde Z^\dagger\widetilde Z$ 是 $\operatorname{row}(\widetilde Z)$ 上的正交投影，则

$$
\Delta W_*'=\Delta W_*'P.
$$

这是 exact identifiability statement。它说明 topology endpoint 在代数上可由 fitted block 计算，并不意味着该 endpoint 被 realized training design 统计识别。

#### Step 4b. Numerical support certificate

令

$$
\widetilde Z=U\operatorname{diag}(s_1,\ldots,s_r)V',
$$

并用冻结阈值 $\tau$ 定义

$$
P_\tau=V\operatorname{diag}\{1(s_j\geq\tau)\}V'.
$$

定义 query-specific unsupported ratio

$$
\chi_\tau(W_*)
=
\frac{\|\Delta W_*'(I-P_\tau)\|_F}
{\|\Delta W_*'\|_F\vee\varepsilon}.
$$

并定义 retained component 的 query-specific inverse amplification

$$
\alpha_\tau(W_*)
=
\frac{
\|\Delta W_*'P_\tau
(P_\tau G_ZP_\tau)^\dagger{}^{1/2}\|_F
}{
\|\Delta W_*'\|_F\vee\varepsilon
}.
$$

$\chi_\tau$ 回答 query 有多少作用落在 discarded directions；$\alpha_\tau$ 回答 retained query action 会把 residualized score noise 放大多少。一个 endpoint 可以满足 $\chi_\tau=0$，同时因 $G_Z$ 的绝对尺度很小而具有很大的 $\alpha_\tau$。因此 numerical support report 必须同时给出 unsupported share、absolute singular spectrum 和 query amplification。

`supported` 只能在 $\chi_\tau(W_*)\leq\delta$ 时返回，其中 $\tau,\delta$ 以及用于构造 endpoint 的 calibration prefix 在 validation/evaluation outcome 产生前冻结。$\chi_\tau=0$ 表示相对于 thresholded subspace 的 in-support case；只有当 $P_\tau=\widetilde Z^\dagger\widetilde Z$ 时，它才同时对应 Step 4a 的 exact row-space statement。较大的值表示 query 依赖在冻结 conditioning tolerance 下未被稳定激发的 slope directions。

R006d construction audit 使用 condition-number interpretation 冻结 $\tau_t=s_{1,t}/\kappa_{max}$，其中 $\kappa_{max}=50$；绝对 machine floor 只处理 $s_{1,t}=0$ 和 floating-point degeneracy。这个规则只限制相对于 strongest direction 的 amplification，不控制 absolute noise amplification。实际 audit 中全部 9,600 个 calibration windows 都保留 rank `20/20`，$\chi_\tau$ 约为 machine precision，因而该 DGP 不能提供 unsupported endpoint；同时 absolute singular scale 仍需由 $\alpha_\tau$ 诊断。不得通过读取 recovery error 后改变 $\kappa_{max}$。

#### Step 4c. Supported and unsupported query terms

对任意 $b$ 有 exact decomposition

$$
\mathsf T_*b
=
\mathsf T_*P_\tau b
+
\mathsf T_*(I-P_\tau)b.
$$

第一项是 identifiable retained component，但其统计误差仍由 $\alpha_\tau$ 和 residualized score moment 控制。第二项不能通过同一冻结 training design 和 conditioning tolerance 消除，除非增加样本激发、structural restriction、external topology experiments 或先验。若 $\widehat b$ 只估计 excited component，则

$$
\|\mathsf T_*\widehat b-\mathsf T_*b\|
\leq
\|\mathsf T_*P_\tau\|\,\|P_\tau(\widehat b-b)\|
+
\|\mathsf T_*(I-P_\tau)b\|.
$$

最后一项是 unsupported remainder，不是 optimization error，也不能通过增加 CP/Tucker iterations 消失。对 thresholded numerical support，它可以随新增训练信息改变；对 Step 4a 的 exact null space，它在不增加识别信息时不可消除。这一分解是 T3 的 invariant object。

#### Step 4d. Full-rank local ridge bound

当目标是恢复完整 $b$ 且 $\lambda_{\min}(G_Z)\geq\eta>0$ 时，对一个 residualized equation/window 写为

$$
Y^\perp=Z^\perp b+U^\perp+R,
$$

其中 $R$ 是 rolling-window drift approximation remainder。ridge estimator 为

$$
\widehat b_\lambda
=
\left(n^{-1}(Z^\perp)'Z^\perp+\lambda I\right)^{-1}
n^{-1}(Z^\perp)'Y^\perp.
$$

减去 $b$ 得 exact identity：

$$
\widehat b_\lambda-b
=
\left(G+\lambda I\right)^{-1}
\left[
n^{-1}(Z^\perp)'U^\perp
+n^{-1}(Z^\perp)'R
-\lambda b
\right],
$$

其中 $G=n^{-1}(Z^\perp)'Z^\perp$。在 $\lambda_{\min}(G)\geq\eta$ 下，

$$
\|\widehat b_\lambda-b\|
\leq
\frac{
\|n^{-1}(Z^\perp)'U^\perp\|
+\|n^{-1}(Z^\perp)'R\|
+\lambda\|b\|
}{\eta+\lambda}.
$$

这是 deterministic proposition。query-specific 版本可以把全空间 inverse 替换为 $P_\tau$ 上的 restricted inverse，并保留 Step 4c 的 unsupported remainder。要把第一项写成 $O_p(\sqrt{d/n})$，必须增加 dependence、tail 和 effective sample-size assumptions；不能从当前文本直接推出。

### Step 5. Design-weighted end-to-end low-rank estimator target

R006c 的 native oracle-B rows 表明，只修正 $B$ 不能修复 $W_{ref}$：即使使用 true $B$，两阶段 anchor-Tucker 的 median reference-operator error 仍高于 one。理论和算法对象因此必须从 unweighted coefficient projection 改为 original design loss。

将完整 paths 记为 $\Theta=\{M_{ref,t},B_t\}_{t=1}^T$，候选 estimator 的目标形式为

$$
\widehat\Theta_{DW}
\in
\arg\min_{\Theta\in\mathcal C_R}
\left{
\sum_{t\in\mathcal I_{train}}
\|y_{t+1}-M_{ref,t}x_t-B_t(W_t-W_{ref})x_t\|_2^2
+\lambda_T\mathcal P_T(\Theta)
+\lambda_B\mathcal P_B(B)
\right}.
$$

$\mathcal C_R$ 是冻结的 bounded-factor Tucker 或其他低秩 path class，$\mathcal P_T$ 控制 temporal roughness，$\mathcal P_B$ 对 weakly excited slope directions施加 scale-adaptive shrinkage。所有 tuning 使用 chronological training prefixes。

对固定 window 的 unconstrained least-squares target $\widehat\Theta_{loc,t}$，quadratic outcome loss 可写为常数加

$$
\operatorname{tr}
\left[
(\Theta_t-\widehat\Theta_{loc,t})
G_t
(\Theta_t-\widehat\Theta_{loc,t})'
\right],
$$

其中 $G_t$ 是完整 direct/topology design Gram。这说明 end-to-end loss 等价于在 coefficient space 使用 design geometry，而不是对每个 coefficient direction 赋予相同 Frobenius weight。实现可以直接优化 outcome loss，也可以优化经严格验证的 design-weighted quadratic form；两者的数值等价误差必须进入 construction gate。

在 A6b 的 restricted curvature 和适当 stochastic assumptions 下，目标 oracle inequality 应把 design prediction error 控制为 approximation、empirical-process、temporal-penalty bias 和 optimization gap 四项。由 Step 4c 转为 held-out topology query 时，仍必须添加 unsupported remainder。当前包只固定这一 proof target，不把尚未完成的 rate 当作 theorem。

### Step 6. Approximate block-preserving low-rank projection

令 local estimate tensor 为

$$
\widehat\Theta=\Theta^*+E,
$$

且 $\widetilde\Theta$ 满足 A6。取 $\Theta_R$ 为 true tensor 在 $\mathcal C_R$ 中的最佳 approximation。由 objective gap，

$$
\|\widehat\Theta-\widetilde\Theta\|_F
\leq
\|\widehat\Theta-\Theta_R\|_F+\sqrt{\epsilon_{opt}}.
$$

triangle inequality 给出

$$
\|\widetilde\Theta-\Theta^*\|_F
\leq
a_R+2\|E\|_F+\sqrt{\epsilon_{opt}}.
$$

这是 coherent deterministic oracle-style inequality，但它本身不证明 dimension reduction 带来 statistical rate improvement。要得到

$$
\frac{1}{D}\|\widetilde\Theta-\Theta^*\|_F^2
\lesssim
\frac{a_R^2}{D}
+\frac{\sigma_E^2 d_R\log D}{D}
+\frac{\epsilon_{opt}}{D},
$$

其中 $d_R\asymp R\sum_j d_j$，需要 bounded-factor CP class 的 covering-number argument，并处理 overlapping rolling windows 造成的 dependent $E$。这是当前理论包中最大未完成证明，不应提前写入正文为既成 theorem。

### Step 7. Uniform finite-horizon response transfer

对固定 $t$ 和 $W$，定义

$$
\delta_{C,t}(W)=
\|\widehat{\mathcal C}_t(W)-\mathcal C_t(W)\|.
$$

companion top row 的 block structure 给出

$$
\delta_{C,t}(W)
\leq
\sum_{k=1}^{p}\sum_{m=0}^{q}
\|\widehat B_{m,k,t}-B_{m,k,t}\|\,\|\Phi_m(W)\|.
$$

由 telescoping identity，

$$
\widehat{\mathcal C}^h-\mathcal C^h
=
\sum_{r=0}^{h-1}
\widehat{\mathcal C}^{r}
(\widehat{\mathcal C}-\mathcal C)
\mathcal C^{h-1-r},
$$

所以在 A7 下

$$
\|\widehat{\mathcal C}^h-\mathcal C^h\|
\leq hK_H^2\delta_{C,t}(W).
$$

允许 shock map estimation error 后，

$$
\widehat\Psi_h(W)-\Psi_h(W)
=
J(\widehat{\mathcal C}^h-\mathcal C^h)J'\widehat S
+J\mathcal C^hJ'(\widehat S-S).
$$

因此

$$
\sum_{h=1}^{H}\|\widehat\Psi_h(W)-\Psi_h(W)\|
\leq
L_SK_H^2\frac{H(H+1)}{2}\delta_{C,t}(W)
+HK_H\delta_S.
$$

对 $W\in\mathcal W$ 取 supremum 并用 A8，可得

$$
\sup_{W\in\mathcal W}
\sum_{h=1}^{H}\|\widehat\Psi_h(W)-\Psi_h(W)\|
\leq
L_SK_H^2\frac{H(H+1)}{2}
\sum_{k,m}L_{\Phi,m}
\|\widehat B_{m,k,t}-B_{m,k,t}\|
+HK_H\delta_S.
$$

这是对现有 Proposition 1 的真正扩展：multiple topology bases、uniform topology class 和 shock-normalization error 都被纳入。

### Step 8. Topology sensitivity bound

对 true blocks 和两个 topology inputs $W_0,W_1$，

$$
\|M_{k,t}(W_1)-M_{k,t}(W_0)\|
\leq
\sum_{m=1}^{q}\|B_{m,k,t}\|
\|\Phi_m(W_1)-\Phi_m(W_0)\|.
$$

将该 operator difference 代入 Step 7 的 telescoping argument，得到 topology-substitution response 对 supplied topology features 的 Lipschitz bound。对于 $\Phi_m(W)=W^m$，可进一步使用

$$
W_1^m-W_0^m
=
\sum_{r=0}^{m-1}W_1^r(W_1-W_0)W_0^{m-1-r}
$$

以及 bounded topology norms 得到

$$
\|W_1^m-W_0^m\|
\leq
mL_W^{m-1}\|W_1-W_0\|.
$$

这解释了 higher-order diffusion bases 为什么会放大 topology measurement error，并直接指导 B1/B2 的实验轴。

### Step 9. End-to-end bound target

两阶段 comparator 把每个 window 的 Step 4 local error 堆叠为 $E$，再代入 Step 6 和 Step 7。design-weighted candidate 则使用 Step 5 的 restricted-curvature route，并在两条路线中都加入 Step 4c 的 unsupported remainder。对两阶段 comparator，average-date version 的 schematic target 为

$$
\frac{1}{T}\sum_{t=1}^{T}
\sup_{W\in\mathcal W}
\mathcal E_{t,H}(W)
\lesssim
C_{H,\mathcal W}
\left[
a_R
+2\Delta_{local}
+\sqrt{\epsilon_{opt}}
+\overline{\mathcal U}_\tau(\mathcal W)
\right]
+HK_H\overline{\delta_S},
$$

其中

$$
\Delta_{local}
\equiv
\left\{
\sum_t
\left(
\frac{\text{innovation moment}_t+\text{drift moment}_t+\lambda\|b_t\|}
{\eta_t+\lambda}
\right)^2
\right\}^{1/2}.
$$

其中 $\overline{\mathcal U}_\tau(\mathcal W)$ 汇总 Step 4c 的 unsupported query action；若对整个 $\mathcal W$ 取 supremum，它不能省略。对 design-weighted candidate，相应项应以 restricted-curvature route 替换 $a_R+2\Delta_{local}+\sqrt{\epsilon_{opt}}$：若 excess design loss、class approximation、penalty bias 和 observable stationarity gap 的合计为 $\Delta_{DW}$，则 excited component 的目标尺度为 $\kappa_{\mathcal C}^{-1/2}\sqrt{\Delta_{DW}}$，并仍加同一个 $\overline{\mathcal U}_\tau(\mathcal W)$。

这里 $C_{H,\mathcal W}$ 收集 $L_S,K_H,H$ 和 topology-basis norms。在完成 empirical-process bound 前，design-weighted 形式只是 proof target，不是已证明 rate。要把任一路线升级为 probability rate theorem，需要完成 Step 5 中的 dependent tensor-noise concentration；pointwise-in-date 版本还需要 A9。

## Remarks and Interpretation

- 最强的新概念不是“CP 能降噪”，而是 query identifiability 可以用 representation map 与 query map 的 kernel relation 精确判断。
- 多个 stored topologies 可能足以回答某个 target query，即使不能识别完整 coefficient blocks。这比“必须永远保存 A 和 B”更准确。
- Basis-switchable operator 让现有 $A+BW$ 成为一个特例，同时提供可实际实现的 $W^2$ diffusion extension。
- weak separation、rank approximation、optimization 和 stability 是四个不同误差来源；实验必须分别控制。
- endpoint availability、training-design support 和 numerical recovery 是三个不同 gates；一个 endpoint 可以在代码上可计算但在 realized topology design 下 unsupported。
- $\chi_\tau=0$ 只排除 unsupported remainder；只有联合报告 $\alpha_\tau$、absolute singular scale 和 score/noise scale，才能讨论 statistical recoverability。
- R006c 的 oracle-B failure 表明下一 estimator 必须改善 $M_{ref}$ 的 native recovery；只对 $B$ 做 residualization 或更强 smoothing 不足以回应现有证据。
- design-weighted end-to-end loss 保留真实预测 design 的几何；unweighted Frobenius tensor projection 继续作为 comparator，而不是默认的新方法。
- response-transfer bound 只说明 coefficient error 的后果，不自动证明某个 smoother 的 coefficient error 更小。

## Boundaries and Non-Claims

- 不证明 CP-ALS global convergence。
- 不证明 data-driven rank selection 一致性，除非新增独立定理。
- 不把 predetermined/supplied topology 当作 topology formation model。
- 不从 topology substitution 推导 causal policy effects。
- 不把 nonlinear GNN 的 finite-difference response 与 linear GIRF 视为完全相同对象；只能在预先定义的 query protocol 下比较。
- 不把现有 independent-window perturbation 称为 coherent time-series bootstrap coverage。
- 不在没有 A9 时提出 uniform-in-date recovery。

## Open Risks

1. **Dependent tensor-noise concentration**：overlapping rolling windows 使 $E_t$ 强相关；需要 blocking/mixing argument 或 sample splitting。
2. **CP class geometry**：bounded-factor、scale normalization 和 component degeneracy 必须固定，否则 covering number 不稳定。
3. **Optimization gap observability**：multi-start ALS 只能提供相对 objective evidence，不能知道 global infimum。
4. **Higher-order basis stability**：$W^2$ 等 basis 可能放大 measurement error 和 companion radius。
5. **Local drift bias**：window 内 drift remainder 必须进入 theorem 和 phase diagram，不能藏在 noise term 中。
6. **Shock normalization**：empirical GIRF 使用的 covariance/shock map estimation error 需要与 coefficient error 分开。
7. **Theory scope decision**：若无法完成 statistical rate，仍可用 exact identifiability + deterministic end-to-end bounds 形成 coherent theory，但 broad high-selectivity claim 会更弱。
8. **Query-support threshold**：$\tau$ 与 $\delta$ 必须通过无 endpoint-error 的数值规则冻结；若依 recovery performance 调整，abstention claim 失效。相对 condition-number threshold 不控制 absolute variance，后续 protocol 必须另行冻结 $\alpha_\tau$ 的解释或只把它作为连续诊断。
9. **End-to-end nonconvexity**：Tucker/CP constrained outcome loss 需要可观测的 descent、restart 和 optimization-gap diagnostics；restricted curvature 不证明算法到达 global optimum。
10. **Reference-query recovery**：若 design-weighted candidate 仍在 native oracle-B-like cells 的 $W_{ref}$ gate 失败，应停止 estimator route，而不是继续增加 topology endpoint variants。
