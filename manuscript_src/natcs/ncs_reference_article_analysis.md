# Reference-Article Analysis For NCS Positioning

Purpose: document the transferable article architecture and evidence practices from the four reference papers named for this submission. This memo is a strategy record, not manuscript text and not a claim that the present operator method improves their target tasks.

Evidence reviewed on 2026-07-11: the open Nature Communications PDFs downloaded from the DOI landing pages listed below. Counts and figure roles are based on the inspected PDFs, their text extraction and rendered opening figure pages.

## Materials And Boundary

| Article | DOI | Verified material | Boundary for this memo |
| --- | --- | --- | --- |
| Peixoto and Rosvall (2017) | `10.1038/s41467-017-00148-9` | 12-page PDF; six main figures | This memo assesses presentation and evidence architecture, not the validity of every model result. |
| Williams et al. (2022) | `10.1038/s41467-022-28123-z` | 8-page PDF; four main figures | The paper addresses temporal-network memory, not topology-substitution response measurement. |
| He et al. (2024) | `10.1038/s41467-024-45598-0` | 15-page PDF; eight main figures | The paper evaluates temporal link prediction, not dynamic response operators. |
| Murphy et al. (2021) | `10.1038/s41467-021-24732-2` | 11-page PDF; six main figures | The paper learns contagion dynamics, not the present linear conditional-propagation estimand. |

## Article-Level Findings

### Peixoto And Rosvall (2017)

**Research problem and advance.** The paper begins from the inability of static descriptions, extrinsic memory-order choice and imposed temporal windows to identify dynamic community structure without overfitting. Its method contribution is a nonparametric Bayesian inference framework for arbitrary-order Markov chains with community structure. The claimed object-level advance is simultaneous inference of relevant timescales, Markov order and communities from event sequences or temporal-network edges.

**Narrative architecture.** The abstract follows problem -> limitation -> principled method -> inference target. The Introduction names two concrete failure modes before presenting the method. Results begin with the generic Markov-chain inference problem, then move to temporal-network representations and empirical examples. Methods and supplementary detail carry derivations and implementation. Discussion returns to model selection, scalable code and the scope of the generative model.

**Figure system.** Six figures progress from a two-panel schematic of dynamics on versus dynamics of networks (Fig. 1), to a model representation schematic (Fig. 2), to fitted examples in flights, proximity data, waiting times and text. The early figures use restrained black/grey diagrams with a single orange Nature Communications accent; data-rich later figures carry the empirical evidence. The visual sequence makes the computational object visible before performance or application claims.

**Credibility construction.** The paper explicitly treats overfitting and arbitrary timescales as risks, then makes Bayesian model selection the countermeasure. It uses distinct data modalities and supplies code/data availability. Its transferable lesson is to make the failure of an inadequate representation visible before displaying a successful fit.

**Transfer to this paper.** Fig. 1 and the collapsed-map availability ablation should continue to precede recovery results. The present paper should not borrow the stronger claim of discovering latent community structure; its defensible analogue is the ability to evaluate a stated response query after reconstruction.

### Williams, Lacasa, Millan And Latora (2022)

**Research problem and advance.** The paper argues that scalar temporal-network memory misses microscopic, heterogeneous dependencies among links. It introduces a co-memory matrix and a "shape of memory" representation, then connects that representation to virtual loops and spreading effects. This is a representation-level methodological contribution with a mathematical object, synthetic validation and multi-domain empirical characterization.

**Narrative architecture.** The abstract identifies a disputed concept, gives the mathematical framework, then states synthetic and real-network validation. The Introduction explains why a scalar projection loses relevant structure before defining the richer object. Results move from the co-memory matrix, to virtual-loop consequences, to synthetic hit-rate validation and real-world network heat maps. The Discussion expands the meaning and limits of the representation.

**Figure system.** Four figures form a compact sequence: co-memory heat maps and distributions (Fig. 1), a small schematic plus spreading consequences (Fig. 2), synthetic recovery/hit-rate evaluation (Fig. 3), and real-network memory shapes (Fig. 4). The heat-map palette distinguishes values while retaining uncluttered labels. Each panel has one role: define, show consequence, validate, generalize descriptively.

**Credibility construction.** The paper directly contrasts its matrix-valued object with the scalar memory it critiques, holds the scalar quantity fixed in illustrative cases, tests synthetic recovery, and then examines heterogeneous real systems. This is the closest structural reference for the present paper's collapsed-map ablation: the point is what a compressed representation cannot retain, not a generic performance ranking.

**Transfer to this paper.** The main manuscript should state the contrast as an endpoint-availability test at the fitted-object level. It should avoid implying that CP itself supplies a new temporal-memory formalism or that the results describe endogenous network memory.

### He, Ghasemian, Lee, Clauset And Mucha (2024)

**Research problem and advance.** The paper targets temporal link prediction under partly or completely unobserved target layers. It argues that costly temporal topological features can be replaced by sequentially stacked static features, then evaluates predictive accuracy, computation time and feature importance. Its novelty is an algorithmic/predictive framework, not a causal or mechanistic temporal-network model.

**Narrative architecture.** The first figure gives a detailed workflow schematic and states train/test separation directly in its caption. Results then separate partially observed and completely unobserved target settings, synthetic benchmark performance, computation-time comparisons, real-world data, and feature-importance interpretation. Discussion ties performance to interpretability and computational cost.

**Figure system.** Eight figures are deliberately evidence-heavy: workflow (Fig. 1), feature and predictor comparison (Fig. 2), time complexity and AUC (Fig. 3), synthetic regime grids (Figs. 4-5), real-network performance (Fig. 6), and feature-importance structure (Figs. 7-8). The opening schematic uses a clear time axis and coloured blocks for observed, training and target layers. Later figures reserve colour for method groups and uncertainty/benchmark distinctions.

**Credibility construction.** The study makes the prediction target, information availability, cross-validation route, baselines, AUC metric, computational cost and real-world coverage explicit. Its transferable lesson is that a native prediction claim requires a task-specific target and split, which the present propagation benchmark does not supply.

**Transfer to this paper.** Projected graph-feature rows must remain Supplementary operator-protocol diagnostics. They cannot support an argument about native temporal link prediction, temporal-GNN forecasting or feature-learning superiority. The main figure should retain only same-target preservation comparators, as now implemented.

### Murphy, Laurence And Allard (2021)

**Research problem and advance.** The paper frames contagion forecasting as limited by mechanistic simplification and proposes a GNN that learns effective local dynamics from time-series data on known networks. It tests increasingly complex synthetic contagion processes, explores learned dynamics on arbitrary structures, then gives a COVID-19 mobility-network illustration.

**Narrative architecture.** The abstract gives a concrete challenge, an architecture/training response, synthetic evidence, a generalization test over network structures and a real-data case. The Introduction makes locality and out-of-sample topology explicit assumptions. Results define the learned map and training objective before reporting synthetic learning curves, bifurcations, the Spain network, empirical prediction and architecture details. Methods carry implementation and data treatment.

**Figure system.** Six figures follow method evidence: learned transition functions (Fig. 1), performance across dynamics and graph structures (Fig. 2), bifurcation recovery (Fig. 3), empirical network/data context (Fig. 4), empirical prediction (Fig. 5), and architecture schematic (Fig. 6). The early performance figures demonstrate target fidelity before the application. The visual language uses simple coloured state/process distinctions and leaves the data panels readable.

**Credibility construction.** The paper specifies the local time-invariant target class, validates multiple synthetic dynamics and structures, includes a held-out empirical prediction route, and makes architecture visible. The transferable lesson is to tie generality to the exact invariance or target class tested.

**Transfer to this paper.** The NYC case can support same-operator execution in a second weighted-network domain. It cannot support the broader structural generalization or nonlinear-contagion claim demonstrated in this GNN paper. The current Discussion boundary should retain that distinction.

## Shared Nature Communications Pattern

1. **Lead with an irreducible computational object.** Each article makes its target visible before applications: an event-sequence/community representation, a co-memory matrix, a temporally stacked feature vector or a learned local map.
2. **Name a concrete information loss or computational failure.** The papers identify imposed timescales, scalar memory, costly/less accurate temporal features, or restrictive mechanistic assumptions. The proposed object responds to that named failure.
3. **Use a first main figure as a protocol diagram.** The reader can see inputs, retained structure, target and evaluation flow before reading numerical evidence.
4. **Place controlled validation before domain demonstration.** Synthetic recovery, prediction or learned-dynamics tests establish the target under known conditions. Real systems then show use, not proof of every mechanism.
5. **Keep the comparison target native to the claim.** Prediction papers define target-layer availability and splits; representation papers contrast the retained object with a deliberately coarser one. A benchmark should not silently change the target of a comparator.
6. **Bind scope to an explicit model class.** Generality is demonstrated through tested structures, data domains or invariances. It is not inferred from a single application.

## NCS Implications For This Submission

The revised Figure 1 -> Figure 2 -> Figure 3/4 sequence now follows the transferable structure: define the topology-indexed response object and collapsed availability loss; test endpoint and recovery properties; then report bounded RCEP and second-domain readouts. The central sentence should remain precise: this paper contributes a testable reconstruction criterion for a separable direct/network response operator with a supplied topology argument. It does not claim a new dynamic-community, memory, link-prediction or nonlinear-contagion model.

The remaining novelty question is empirical and comparative: whether a specification-level endpoint-availability criterion is sufficiently reusable and non-obvious to warrant an NCS methods/object contribution. The four references motivate why representation determines computable questions, but they do not establish that no earlier dynamic-network response work used an equivalent criterion. That priority claim needs a targeted literature check across dynamic network VAR, GVAR and spatial autoregression work.

## Next Most Valuable Modification

Add a concise, evidence-backed related-work distinction that asks a narrow question of prior separable dynamic-network response models: whether they retain an evaluable supplied topology argument after temporal smoothing and assess endpoint availability before numerical recovery. Use the four verified temporal-network papers only for the representation principle. Use separate, directly checked primary sources for the dynamic-VAR/GVAR comparison; do not infer their absence of an equivalent contract from citation titles or general field knowledge.
