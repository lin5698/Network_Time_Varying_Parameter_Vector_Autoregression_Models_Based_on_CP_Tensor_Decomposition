This supplementary note expands Methods > Propagation objects in the main manuscript and sets the notation used across the manuscript and Supplementary Information. The main manuscript studies a networked multivariate system with $N$ units, lag order $p$ and optional exogenous covariates $x_t$. The reported date label $t$ indexes the end of the rolling estimation window. For each reported date, the estimator returns direct lag blocks $A_{k,t}$, network lag blocks $B_{k,t}$ and residual covariance matrix $\Sigma_t$.

The main system is written as

$$
y_t = c_t + \sum_{k=1}^{p} A_{k,t} y_{t-k} + \sum_{k=1}^{p} B_{k,t} W_t y_{t-k} + C_t x_t + \varepsilon_t,
$$

In this system, $W_t$ denotes the network matrix used in the propagation recursion for the reported date label $t$. In the implemented estimator this object is the most recent matrix available inside the rolling window. The Supplementary Information keeps the shorter $W_t$ notation because that is how the main manuscript refers to the date-specific topology used in the horizon recursion.

It is useful to distinguish the coefficient blocks from the propagation operators they generate. For any supplied topology matrix, the operator is the direct coefficient block plus the network coefficient block multiplied by that supplied topology:

$$
M_{k,t}(W)=A_{k,t}+B_{k,t}W.
$$

At date $t$, the total dynamic recursion evaluates this operator at the date-specific topology $W_t$. The direct-only recursion evaluates it at zero network mediation. The frozen-topology recursion evaluates it at the pre-period benchmark topology $W_{pre}$. The reported propagation measures are functions of differences among these finite-horizon recursions. This notation clarifies why the paper treats the explicit network block as part of the estimand: each response is defined by switching a block or topology argument in the operator, not by post hoc attribution of a reduced-form forecast.

## Endpoint identifiability from the stored object

Fix a lag and date, suppress their subscripts, and write the map stored at the fitted topology $W_0$ as

$$
D=M(W_0)=A+BW_0.
$$

Over the unrestricted matrix-block class, the mapping from $(A,B)$ to $D$ is not injective. For any conformable matrix $H$, define

$$
A^{H}=A-HW_0, \qquad B^{H}=B+H.
$$

The perturbed blocks give the same stored map at the fitted topology,

$$
A^{H}+B^{H}W_0=A+BW_0=D,
$$

but at another supplied topology $W_1$ their operator differs from the original by

$$
\left(A^{H}+B^{H}W_1\right)-\left(A+BW_1\right)=H(W_1-W_0).
$$

Whenever an admissible $H$ satisfies $H(W_1-W_0)\neq 0$, identical collapsed maps imply different topology-substitution endpoints. The same construction covers the direct-only endpoint by setting $W_1=0$. Thus $D$ alone is insufficient for these queries over the unrestricted block class.

This result does not rule out recovery in every structured model class. Diagonal, sparse or otherwise restricted blocks may admit an inverse from $(D,W_0)$ under additional support, rank or nonzero-exposure conditions. Such an inverse and its identification conditions become part of the fitted-object contract and must survive reconstruction. The collapsed benchmark ablation in this Article does not specify or estimate that inverse: it reconstructs $D$ directly and declares component and alternative-topology readouts outside its target. The separated implementation instead stores reconstructed $A$ and $B$ blocks and evaluates the topology argument explicitly.

The baseline trade-network construction uses a trailing four-quarter bilateral import-share matrix, imposes a zero diagonal and then row-normalizes the result. Alternative export-based, symmetric and longer-window definitions provide robustness checks. The comparator $W_{pre}$ freezes topology at the average predetermined exposure matrix over the 2016 Q1--2019 Q4 benchmark window.
