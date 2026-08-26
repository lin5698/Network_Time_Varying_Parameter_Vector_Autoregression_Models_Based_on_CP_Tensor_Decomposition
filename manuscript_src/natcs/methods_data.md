The numerical study uses synthetic evolving weighted networks so that the topology-indexed lag operators and their finite-horizon responses are known. Each panel follows the one-lag system

$$
y_t=A_t y_{t-1}+B_tW_{t-1}y_{t-1}+\varepsilon_t.
$$

The exposure matrices have zero diagonals, non-negative entries and unit row sums. They evolve by mixing the previous topology with a newly generated weighted graph. The direct and network coefficient paths share a rank-two latent temporal trajectory and are rescaled when necessary so that the effective operator has spectral norm at most 0.78 at generation. Gaussian innovations have marginal scale 0.03 in the primary design.

The headline recovery experiment contains two declared scales. The first uses $N=15$, $T=160$, a 40-observation rolling window and topology-mixing weight 0.04. The second uses $N=30$, $T=200$, a 48-observation window and topology-mixing weight 0.05. Both use the true and fitted rank two, horizon four and 20 replications. At $N=50$ and $T=240$, local, CP, Tucker, collapsed and low-rank no-network rows use a 56-observation window and four replications. The sparse and four projected graph-feature diagnostics contain one replication each. All $N=50$ rows are bounded scaling stress checks rather than headline evidence.

Additional controlled scenarios vary fitted rank, coefficient drift, topology volatility, graph sparsity, missing observed edges, noisy observed weights and shock tails.

| Scenario | Role | Exact settings | Released replication coverage |
| --- | --- | --- | --- |
| `high_topology_vol` | generation of `truth.W` | `topologyVol=0.18`, `sparsity=0.15`, `wNoise=0`, `wDrop=0` | local 3; each other released method 20 |
| `sparse_misspecified` | generation of `truth.W` and observation in `WEst` | `topologyVol=0.08`, `sparsity=0.55`, `wNoise=0.18`, `wDrop=0` | each released method 3 |
| `edge_missing` | observation in `WEst`, with generation volatility 0.06 | `topologyVol=0.06`, `sparsity=0.15`, `wNoise=0`, `wDrop=0.30` | local 3; each other released method 20 |
| `noisy_network` | observation in `WEst`, with generation volatility 0.06 | `topologyVol=0.06`, `sparsity=0.15`, `wNoise=0.35`, `wDrop=0` | local 3; each other released method 20 |

The retained topology-stress rows distinguish changes to topology generation from changes to the observed topology. High topology volatility changes the generation mixture to 0.18. The sparse/misspecified row combines generation sparsity 0.55 and topology volatility 0.08 with observed-weight mixing 0.18. The missing-edge row independently drops each observed nonzero off-diagonal edge with probability 0.30 before row normalization, whereas the noisy-weight row mixes 0.65 of the generated topology with 0.35 of an alternative random graph before row normalization. Scenario and replication seeds follow the deterministic implementation rooted at 20260328, and endpoints follow the per-method availability contract. Released stress coverage is not uniformly matched: `local_network` has three replications in the volatility, missing-edge and noisy-weight rows while the other released methods have twenty; the combined sparse/misspecified row has three per released method. These rows therefore provide bounded diagnostics and do not support a matched ranking or general topology-robustness claim. These rows test the declared operator-recovery protocol under perturbations of the generating design. Main-text performance claims are restricted to the replicated $N=15$ and $N=30$ rows. The released benchmark CSV records every scenario, comparator, endpoint and replication count; Supplementary Note 4 states the interpretation contract.

The stricter endpoint-aware qualification is a separate design with $N=20$, $T=200$, 16 required cells per candidate, eight native-design cells and ten recorded seeds per cell. It tests whether the favourable controlled comparison can be inherited as a native held-out recovery claim. The recorded gate requires both declared endpoints to pass in every required cell for one candidate. Supplementary Note 4 reports the complete qualification result.
