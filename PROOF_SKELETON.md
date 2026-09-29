# Proof Skeleton

## Scope and status

This ledger covers the representation and finite-horizon theory used by the Nature Computational Science manuscript. It does not use R006e or R006f outcome evidence. The statistical benchmark results are inputs to the manuscript's evidence boundary, not premises of the propositions below.

## Dependency DAG

```text
D1 topology-indexed lag operator M_k(W)=A_k+B_kW
  -> P1 exact unrestricted-block query-factorization boundary
     -> C1 fitted-topology total operator is determined over the unrestricted class
     -> C2 direct-only operator is determined iff W0=0 over the unrestricted class
     -> C3 unrestricted alternative-topology operator is not determined when W1!=W0
     -> C4 response endpoints inherit non-identification only when they vary with the changed operator
  -> C5 diagonal structured inverse for zero-diagonal W0
     -> C6 nonzero exposure rows identify (a_i,b_i)
     -> C7 zero rows permit exactly the queries whose corresponding W1 rows are zero

D2 joint local design Y=Xa+Zb+U
  -> L1 unpenalized orthogonal residualization M_X=I-P_X
     -> L2 network-block design condition lambda_min(n^-1 Z'M_XZ)>0
     -> L3 Euclidean perturbation bound for unpenalized b
  -> L4 joint-ridge Schur complement M_X,lambda
     -> C8 penalized numerical uniqueness for lambda>0
     -> C9 penalized uniqueness is not unpenalized design identification

D3 companion matrix C(W), selector J and common shock map S
  -> L5 telescoping identity for powers
     -> L6 h K^2 companion-power perturbation bound
     -> P2 cumulative finite-horizon response-transfer bound
        -> C10 spectral-norm block-error corollary
        -> C11 separate application to observed, zero-network and frozen topology
```

The graph is acyclic. P1 does not depend on the estimator or P2. The weak-separation results concern the local design and do not prove P1 or P2. P2 is conditional on coefficient error and bounded powers; it does not prove CP rank recovery, CP-ALS convergence or estimator superiority.

## Typed symbol table

| Symbol | Type and domain | Meaning |
| --- | --- | --- |
| `N` | integer, `N>=1` | number of units |
| `p` | integer, `p>=1` | lag order |
| `A_k,B_k` | real `N x N` matrices in P1; diagonal real matrices in C5 and the empirical estimator | direct and network-mediated lag blocks |
| `a_k,b_k` | real vectors in `R^N` | diagonal entries of the implemented `A_k,B_k` blocks |
| `W,W0,W1` | real `N x N` matrices | supplied, fitted and queried topology matrices |
| `T_W0` | map `(R^{NxN})^2 -> R^{NxN}` | `T_W0(A,B)=A+BW0` |
| `Q_W1` | map `(R^{NxN})^2 -> R^{NxN}` | `Q_W1(A,B)=A+BW1` |
| `D` | real `N x N` matrix | collapsed operator at `W0` |
| `bar W_t` | real `N x N` matrix | last topology available in the rolling window labelled by target date `t`, equal to `W_{t-1}` |
| `X` | real `n x q` matrix | all nuisance/direct regressors in one equation and window, including intercept and all direct lags; optional exogenous regressors when present |
| `Z` | real `n x m` matrix | all network-exposure lag blocks jointly |
| `P_X` | orthogonal projector on `col(X)` | defined using the Moore-Penrose inverse if needed |
| `M_X` | real symmetric projector | `I-P_X` |
| `M_X,lambda` | real symmetric positive-definite contraction | `I-X(X'X+lambda I)^{-1}X'` for `lambda>0` |
| `eta` | non-negative scalar | minimum eigenvalue of `n^{-1}Z'M_XZ` |
| `C(W), Chat(W)` | real `Np x Np` matrices | true and reconstructed companion matrices |
| `J` | real `N x Np` matrix | first-state selector; spectral norm one |
| `S` | real `N x N` matrix | common shock-normalization map |
| `Phi_h(W)` | real `N x N` matrix | moving-average coefficient `J C(W)^h J'` |
| `R_h(W)` | real `N x N` matrix | normalized response `Phi_h(W)S` |
| `H` | integer, `H>=1` | finite response horizon |
| `K` | scalar, `K>=1` | uniform bound on true and reconstructed companion powers through `H` |
| `L_S` | non-negative scalar | upper bound on `||S||_2` |
| `epsilon` | fixed positive scalar | reported ratio denominator floor |

## Canonical quantified statements

### Proposition 1: exact unrestricted-block query-factorization boundary

For every integer `N>=1` and every `W0,W1 in R^{NxN}`, there exists a function `F:R^{NxN}->R^{NxN}` satisfying

```text
for all A,B in R^{NxN}, Q_W1(A,B)=F(T_W0(A,B))
```

if and only if `W1=W0`.

No response-level non-identification is asserted without an additional sensitivity condition showing that the response endpoint changes when `Q_W1` changes.

### Corollary 1: diagonal structured inverse

For every integer `N>=1`, diagonal `A=diag(a)` and `B=diag(b)`, zero-diagonal `W0 in R^{NxN}` and arbitrary `W1 in R^{NxN}`, there exists a function `F` satisfying

```text
for all a,b in R^N, Q_W1(diag(a),diag(b))=F(T_W0(diag(a),diag(b)))
```

if and only if each zero row of `W0` is also a zero row of `W1`. If every row of `W0` is nonzero, `T_W0` is injective on the diagonal class and

```text
a_i=D_ii,
b_i=<D_i,-i,w0_i,-i>/||w0_i,-i||_2^2.
```

Direct-only evaluation is always determined on this zero-diagonal diagonal-block class because every row of the zero query topology is zero.

### Joint-design identification statement

For fixed finite integers `n>=1`, `m>=1` and `q>=0`, let `Y=Xa+Zb+U`, let `P_X` be the orthogonal projector onto `col(X)`, and set `M_X=I-P_X`. If

```text
lambda_min(n^-1 Z'M_XZ) >= eta > 0,
```

then the unpenalized network block is unique conditional on the nuisance span and

```text
||bhat-b||_2 <= eta^-1 ||n^-1 Z'M_XU||_2.
```

If the minimum eigenvalue is zero, a nonzero network direction is absorbed by `col(X)`, so the unpenalized network block is not unique. Complete direct/network parameter uniqueness additionally requires full column rank of the joint design.

For `lambda>0`, the implemented all-coefficient ridge objective has a unique minimizer and its network block satisfies

```text
[Z'M_X,lambda Z + lambda I] bhat_lambda = Z'M_X,lambda Y,
M_X,lambda = I-X(X'X+lambda I)^-1 X'.
```

This penalized uniqueness does not imply unpenalized design identification.

### Proposition 2: finite-horizon response transfer

For every integer `H>=1`, fixed supplied topology `W`, common shock map `S`, and companion matrices `C(W),Chat(W)`, assume

```text
max_{0<=r<=H}{||C(W)^r||_2,||Chat(W)^r||_2} <= K,
K>=1, ||S||_2<=L_S, ||J||_2=||J'||_2=1.
```

Then, with `R_h(W)=J C(W)^h J'S` and its reconstructed analogue,

```text
sum_{h=1}^H ||Rhat_h(W)-R_h(W)||_2
<= L_S K^2 H(H+1)/2 ||Chat(W)-C(W)||_2.
```

For the standard companion embedding,

```text
||Chat(W)-C(W)||_2
<= [sum_{k=1}^p ||Mhat_k(W)-M_k(W)||_2^2]^(1/2)
<= sum_{k=1}^p {||Ahat_k-A_k||_2+||W||_2||Bhat_k-B_k||_2}.
```

If one bound is reported jointly for observed, zero-network and frozen topology, `K` is the maximum over all three corresponding true and reconstructed companion-power families.

## Assumption ledger

| Result | Hypothesis | Where discharged |
| --- | --- | --- |
| P1 | `N>=1`; unrestricted square matrix blocks; `W0,W1` known | proposition statement; Supplementary Note 1 |
| P1 necessity | `W1-W0!=0` | counterexample pair `(-W0,I)` and `(0,0)` |
| Unrestricted direct-only corollary | query topology is zero | P1 with `W1=0`; failure iff `W0!=0` over unrestricted blocks |
| C5 diagonal inverse | `A,B` diagonal; `diag(W0)=0` | Corollary 1 statement; empirical implementation stores only diagonal block entries and topology construction sets zero diagonal |
| C5 query factorization | every zero row of `W0` is zero in `W1` | rowwise proof in Supplementary Note 1 |
| L2/L3 | `Z` contains all network lags; `X` contains all nuisance/direct regressors | Methods estimator; Supplementary Note 3; diagnostic implementation |
| L2/L3 | `n>=1`, `m>=1`; diagnostic and estimator use identical lag-specific topology inputs | Supplementary Note 3; shared `natcs_design_contract.py` helper; production contract tests |
| L3 | Euclidean vector norm and spectral matrix norm | Supplementary Note 3 statement |
| L4/C8 | joint ridge penalizes all columns with common `lambda>0` | implementation `Z'Z+lambda I`; Supplementary Note 3 |
| P2 | common shock map for true and reconstructed paths | proposition statement; fixed-path evaluations |
| P2 | bounded powers through finite `H` | assumed, not empirically proved; stability diagnostics are not a discharge of the theorem assumption |
| C7 | spectral norm and standard companion embedding | proposition statement and Supplementary Note 3 proof |
| Ratio continuity | fixed `epsilon>0` | metric definitions; implementation floor |

## Micro-claim inventory

- **MC-01**: `W1=W0` entails `Q_W1=T_W0`; factorization uses the identity function.
- **MC-02**: If `W1!=W0`, `(A,B)=(0,0)` and `(-W0,I)` have the same `T_W0` value and different `Q_W1` values.
- **MC-03**: P1 therefore has both directions and includes `W0=0` and `W1=W0` boundary cases.
- **MC-04**: Direct-only factorization is P1 evaluated at `W1=0`, hence holds exactly when `W0=0`.
- **MC-05**: Operator non-identification implies response non-identification only for endpoints nonconstant along the constructed equivalence class.
- **MC-06**: With diagonal blocks and zero-diagonal `W0`, row `i` of `D` equals `a_i e_i'+b_iw0_i'` and gives `a_i=D_ii`.
- **MC-07**: A nonzero zero-diagonal row `w0_i` is linearly independent of `e_i`, giving the displayed rowwise formula for `b_i`.
- **MC-08**: If row `i` of `W0` is zero, `D` omits `b_i`; the queried row is independent of `b_i` exactly when row `i` of `W1` is zero.
- **MC-09**: `M_X X=0` and the unpenalized normal equation reduces to `Z'M_XZ bhat=Z'M_XY`.
- **MC-10**: A positive smallest eigenvalue of `n^-1 Z'M_XZ` gives the stated Euclidean inverse bound.
- **MC-11**: A zero eigenvalue supplies nonzero `v` with `Zv in col(X)`, yielding an unpenalized absorbed network direction.
- **MC-12**: Eliminating `a` from the two joint-ridge normal equations gives the stated ridge Schur complement exactly.
- **MC-13**: `lambda>0` makes the joint ridge Hessian positive definite, independent of unpenalized design rank.
- **MC-14**: The telescoping identity for `Chat^h-C^h` follows by finite algebra and needs no limit interchange.
- **MC-15**: Spectral submultiplicativity and bounded powers give `hK^2||Chat-C||_2`.
- **MC-16**: Left/right multiplication by `J,J',S` gives the response bound; finite summation gives `H(H+1)/2`.
- **MC-17**: The spectral norm of the companion top block row is at most the Euclidean aggregation of its block norms and hence at most their sum.
- **MC-18**: `Mhat_k(W)-M_k(W)=Delta A_k+Delta B_k W` gives the lag-block triangle bound.
- **MC-19**: A fixed positive denominator floor makes the reported ratio map continuous everywhere in the finite-dimensional response entries.

## Counterexample log

| ID | Target | Construction | Outcome |
| --- | --- | --- | --- |
| CE-01 | direct-only overclaim | `N=1`, `W0=W1=0` | `D=A`; direct-only is identified. Confirms need for exact boundary. |
| CE-02 | ordinary residualized ridge as joint ridge | `X=Z=Y=[1]`, `lambda=1` | residualized-only formula gives `b=0`; joint ridge gives `a=b=1/3`. |
| CE-03 | per-lag weak separation | `X=(1,1)'`, `z1=z2=(1,-1)'` | each isolated lag appears nondegenerate, but joint network design is singular. |
| CE-04 | arbitrary induced-norm block corollary | weighted max norm on `R^2`, `Delta M1=0`, `Delta M2=1` | companion error norm is 10 while block sum is 1. Confirms spectral-norm restriction. |
| CE-05 | response-level overclaim | `H=0` or common shock map `S=0` | operator may differ while the reported response endpoint is unchanged. |
| CE-06 | penalty-dominance overclaim | `M_XY=0` with arbitrarily small positive Gram eigenvalue | OLS and ridge network estimates may both be zero. Small eigenvalue implies worst-case sensitivity, not actual penalty dominance. |
| CE-07 | applying P1 to the diagonal implementation | `N=2`, zero-diagonal swap `W0`, diagonal `A,B` | `D` identifies both blocks exactly. Confirms need for Corollary 1 and the restricted-class scope boundary. |
| CE-08 | diagonal zero-row query | second row of `W0` zero; compare two values of `b_2` | same `D`; query remains identical only when the second row of `W1` is zero. |
| CE-09 | floor-regularized condition number | `Z_perp=0` | old ratio returned zero; exact diagnostic convention is infinite condition number and a positive weak-separation flag. |

## Limit-order map

The audited propositions are finite-dimensional deterministic statements. They contain no big-O, little-o, asymptotic limit, expectation, integral, derivative or probability-mode interchange. The empirical benchmark has separate finite-replication claims and is not used to discharge these proof obligations.
