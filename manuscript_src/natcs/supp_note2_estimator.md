This note expands `Methods > Estimator` and records the algorithmic contract used by the controlled benchmark.

1. Generate a one-lag evolving-network panel under the scenario contract in Supplementary Note 4.
2. At each target date, estimate unrestricted direct and network blocks from a rolling ridge regression on $y_{s-1}$ and $W_{s-1}y_{s-1}$.
3. Stack the local blocks as an $N\times 2N\times T_{roll}$ tensor, keeping the direct/network columns distinct.
4. Reconstruct that tensor at the scenario rank with CP alternating least squares.
5. Evaluate every effective operator and response from the reconstructed blocks under the declared topology argument.

The local normal equations use a ridge floor of $10^{-6}$. The main scale scenarios use true and fitted rank two. CP alternating least squares runs for 60 iterations, adds $10^{-6}$ to each Gram system and normalizes the unit and coefficient-mode factors after every iteration. The implementation uses row-major unfoldings and Khatri-Rao orders $(C,B)$, $(C,A)$ and $(B,A)$ for the three updates.

The block index is part of the fitted object. If $\widehat\Theta_t=[\widehat A_t\;\widehat B_t]$ denotes one reconstructed slice, the supplied-topology operator is

$$
\widehat M_t(W)=\widehat A_t+\widehat B_tW.
$$

The same reconstructed slice therefore supports observed-topology, direct-only and frozen-topology evaluations by supplying $W_t$, zero or a declared benchmark topology. CP is the implementation layer for this separated object; query preservation follows from the retained blocks, not from the name of the decomposition.

The unrestricted local rolling estimator is the primary recovery comparator. Tucker reconstruction smooths the same separated tensor at matched multilinear rank. Collapsed-operator CP smooths $\widehat A_t+\widehat B_tW_t$ after the local fit, whereas low-rank no-network reconstruction omits the explicit network block. These reduced representations are scored on total-map and total-response endpoints only. Sparse and graph-feature rows are mapped to the operator protocol under the fixed projection rules in Supplementary Table 1b; their role is diagnostic, not a native graph-learning ranking.

The deterministic theory and the numerical benchmark have separate roles. Proposition 1 gives the unrestricted-block query-factorization boundary, Corollary 1 gives a diagonal structured inverse and Proposition 2 transfers a supplied companion-matrix error into finite-horizon response error under bounded powers. None of these results selects the CP rank, guarantees a global CP optimum or implies the observed recovery gain. Those claims are evaluated by the controlled endpoint and replication contract.
