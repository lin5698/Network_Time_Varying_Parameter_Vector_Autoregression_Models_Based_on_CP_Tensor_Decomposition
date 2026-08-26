The numerical study uses synthetic evolving weighted networks so that the topology-indexed lag operators and their finite-horizon responses are known. Each panel follows the one-lag system

$$
y_t=A_t y_{t-1}+B_tW_{t-1}y_{t-1}+\varepsilon_t.
$$

The exposure matrices have zero diagonals, non-negative entries and unit row sums. They evolve by mixing the previous topology with a newly generated weighted graph. The direct and network coefficient paths share a rank-two latent temporal trajectory and are rescaled when necessary so that the effective operator has spectral norm at most 0.78 at generation. Gaussian innovations have marginal scale 0.03 in the primary design.

The headline recovery experiment contains two declared scales. The first uses $N=15$, $T=160$, a 40-observation rolling window and topology-mixing weight 0.04. The second uses $N=30$, $T=200$, a 48-observation window and topology-mixing weight 0.05. Both use the true and fitted rank two, horizon four and 20 replications. At $N=50$ and $T=240$, local, CP, Tucker, collapsed and low-rank no-network rows use a 56-observation window and four replications. The sparse and four projected graph-feature diagnostics contain one replication each. All $N=50$ rows are bounded scaling stress checks rather than headline evidence.

Additional controlled scenarios vary fitted rank, coefficient drift, topology volatility, graph sparsity, missing observed edges, noisy observed weights and shock tails. These rows test the declared operator-recovery protocol under perturbations of the generating design. Main-text performance claims are restricted to the replicated $N=15$ and $N=30$ rows. The released benchmark CSV records every scenario, comparator, endpoint and replication count; Supplementary Note 4 states the interpretation contract.

The stricter endpoint-aware qualification is a separate design with $N=20$, $T=200$, 16 required cells per candidate, eight native-design cells and ten recorded seeds per cell. It tests whether the favourable controlled comparison can be inherited as a native held-out recovery claim. The recorded gate requires both declared endpoints to pass in every required cell for one candidate. Supplementary Note 4 reports the complete qualification result.
