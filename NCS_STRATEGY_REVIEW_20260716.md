# Nature Computational Science strategy review

Date: 2026-07-16  
Scope: visible manuscript, Supplementary Information, compiled PDFs, figures, experiment audits, refinement logs and four locally available reference articles.  
Status: read-only manuscript review; no manuscript text or result artifact was modified.

## 给作者的中文结论

当前稿件最有价值的计算科学贡献不是“CP 分解提高了预测或响应精度”，而是：**时序网络模型在重构后能否回答某个下游问题，取决于存储表示是否保留该 query 所需的信息。** 对本文而言，需要严格区分四层：端点在代数上是否定义、数据是否识别该端点、估计器能否恢复该端点、误差能否在有限期响应中稳定传播。

稿件目前不适合直接投 Nature Computational Science。决定性障碍是 evidence hierarchy：摘要和 Results 以早期 `N=15/N=30` 正向 benchmark 为 headline，但最新 endpoint-aware audit 的 CP 为 `0/16`、Tucker 为 `6/16`、native Tucker 为 `0/8`，没有候选方法晋级。两批实验并非必然使用相同 DGP，不能简单称为数值矛盾；但当前稿件也没有说明早期结果只能支持哪个窄 claim，因此形成了方法优越性 overclaim。

此外存在两个必须先修复的可复现性问题：主文/补充表选 RCEP rank 1，而 Supplementary Methods 写 rank 2；Figure 4c 与正文使用两种不同的 network-share 公式。图 4 的差异不是普通的 point estimate 与 bootstrap 区别，必须先选择并论证统一 estimand，再重算所有值。

本轮建议不直接修改主稿。先完成两项：建立逐条 `claim-evidence ledger`，并从实际 artifact metadata 生成唯一 `empirical_run_manifest`。完成后才能决定走“representation/estimand theorem”路线，还是等待新的 native held-out recovery gate 通过后走“estimator/method”路线。

### Evidence labels and inheritance

- **Visible fact:** directly supported by a manuscript passage, rendered figure, result artifact, audit or local full-text PDF.
- **Pending verification:** a plausible explanation that cannot be selected without source metadata or a new experiment.
- **Strategic hypothesis:** a proposed route whose success depends on future evidence; it is not a manuscript claim.
- In tables, the `Review goal` column applies to every recommendation in that row. In prose lists, the goals in the subsection heading apply to every item unless a narrower goal is attached.

### Pending-verification assumptions

| Item | Status | Why it matters |
|---|---|---|
| The early N=15/N=30 benchmark and R006c test different DGPs/protocols | Visible materials indicate distinct experiments; exact claim inheritance still needs a ledger | They are not automatically numerically contradictory, but the early result cannot license the stricter native-recovery claim |
| Figure 4 share values use different formulas | Visible fact from figure/evidence scripts | Figure 4 uses `sum(abs(network))/sum(abs(total))`; manuscript bootstrap summaries use `(sum(abs(total))-sum(abs(direct)))/sum(abs(total))`. One estimand must be selected and all outputs regenerated |
| A design-weighted joint estimator can pass Track A | Strategic hypothesis only | No superiority, recovery or NCS-method claim may depend on it before a frozen test passes |
| A consequential public application will yield a non-trivial result | Strategic hypothesis only | The outcome must not be inspected or implied before a protocol is fixed |
| The described NCS pattern predicts editorial outcome | Evidence-based judgement, not an official journal rule | It calibrates strategy but cannot guarantee acceptance or rejection |

## Executive decision

The paper currently contains a potentially useful computational-science idea: a reconstructed temporal-network model should be judged not only by predictive or operator error, but also by whether it retains the inputs required for a declared downstream query. The strongest defensible contribution is therefore a **query-preserving representation/estimand principle**, not a demonstrated CP estimator superiority claim.

The present NCS route is blocked by evidence, not prose. The abstract and Results headline the earlier `N=15/N=30` CP improvements, whereas the latest independently audited endpoint-aware experiment reports CP `0/16`, Tucker `6/16`, native Tucker `0/8`, and no promoted candidate. In addition, the reported RCEP rank conflicts across the main and Supplementary Methods, the principal benchmark lacks confirmatory paired inference, the strongest temporal baseline is not part of the headline comparison, and both empirical applications are deliberately bounded (RCEP re-estimation interval crosses zero; NYC is near-null).

**Current editorial forecast:** high desk-rejection risk at Nature Computational Science. A language-only revision would make the paper easier to reject, not materially more publishable, because it would expose rather than close the evidence gap.

**Highest-priority action:** build a claim-evidence ledger, reconcile every headline statement with the latest audited experiment, and freeze manuscript promotion until a prespecified native held-out-topology recovery gate passes.

---

## Stage 0. Material completeness check

### Available materials

| Material | Visible evidence | What it permits |
|---|---|---|
| Main manuscript | `main.tex`; 19-page compiled PDF | Full structural, language, claim and figure-sequence review |
| Supplementary Information | `supplementary.tex`; 66-page compiled PDF | Review of derivations, benchmark design, robustness and reproducibility detail |
| Four requested reference articles | Local publisher PDFs for Peixoto & Rosvall (2017), Williams et al. (2022), He et al. (2024), Murphy et al. (2021) | Full-text structural analysis; no “needs full text verification” qualifier is required for these four |
| Main and supplementary figures | Rendered page PNGs plus PDF/PNG assets | Visual hierarchy, panel logic, labelling and narrative-role review |
| Synthetic benchmark outputs | CSV/JSON/Markdown outputs, stress grids and tests | Verification of reported scopes and visible audit conclusions |
| Independent experiment audit | `EXPERIMENT_AUDIT.md/.json`, `findings.md`, R006/R006b/R006c/R006d logs | Identification of negative method gates and claim restrictions |
| Empirical derived data | Processed parquet/CSV/JSON files and model summaries | Derived-to-figure reproducibility assessment |
| Availability statements | Data/code availability and submission materials | Review of what is actually promised versus already deposited |
| Build and validation scripts | manuscript, evidence, figure and audit scripts; tests | Assessment of internal reproducibility infrastructure |

### Missing or unresolved materials

| Missing/unresolved item | Affected judgement | Impact |
|---|---|---|
| Single authoritative claim-evidence ledger | novelty, rigour, clarity | Cannot tell which benchmark is intended to license each abstract/Results claim |
| Authoritative artifact metadata for empirical rank and hashes | rigour, reproducibility | Main text says RCEP rank 1, while one Supplementary Methods passage says rank 2 |
| Prespecified confirmatory analysis for headline benchmark | rigour | Median/IQR ranges do not establish paired superiority or control multiple primary contrasts |
| Successful native held-out-topology recovery experiment | novelty, significance, generality | Latest endpoint-aware gate is negative; current evidence supports availability more than recovery |
| Equal-budget primary baseline matrix | rigour, significance | Local, fused temporal, Tucker and other methods do not share a clear primary protocol and replication contract |
| Statistical recovery theory or oracle result | novelty, rigour | Existing deterministic finite-horizon transfer bound does not establish estimator recovery |
| Coherent time-series uncertainty/coverage validation | rigour | Current moving-block perturbation is a sensitivity layer, conditional on tuning, not a general coverage result |
| Consequential application with a stable non-trivial contrast | significance, generality | RCEP is descriptive and crosses zero after re-estimation; NYC is near-null |
| Public DOI/repository release and clean-room raw-to-result audit | reproducibility | Derived-to-figure reproduction is stronger than independent raw-to-result reproduction |
| Formal author decision on paper type | clarity, novelty | The draft alternates between method, representation theorem and empirical application narratives |

### Judgements possible despite missing information

1. The stored-representation/query distinction is conceptually clearer than the CP-specific novelty.
2. Endpoint **definition**, endpoint **identification**, statistical **recoverability**, and finite-horizon **stability** must be separated throughout.
3. The current abstract overweights earlier positive benchmark evidence relative to the latest audited negative gate.
4. Figure 1 is a viable conceptual anchor; Figures 3 and 4 do not currently supply a sufficiently consequential evidence climax.
5. Methods contain substantial detail, but truth conflicts and protocol hierarchy matter more than adding further equations.
6. The paper is closer to an estimand/representation contribution than to an NCS-ready reusable computational method.

### Minimum next-material package [rigour / reproducibility / clarity]

1. `claim_evidence_ledger.csv`: claim ID, manuscript location, experiment ID/version, DGP/data, endpoint, comparator, replication unit, statistic/interval, audit verdict, allowed wording.
2. `empirical_run_manifest.json`: actual ridge/rank, code hash, input hash and output hash for every main empirical figure/table.
3. A frozen Track A protocol for native held-out endpoints with equal seeds and tuning budgets across local, causal fused-TV, matched Tucker and the proposed estimator.
4. A paired confirmatory inference plan: primary endpoints, seed as pairing unit, interval/test, win fraction and multiplicity control.
5. A one-page contribution decision: representation theorem route versus estimator route.

**Next most valuable modification [rigour / reproducibility]:** reconcile the rank conflict and create the claim-evidence ledger before changing a title, abstract, figure or sentence.

---

## Stage 1. Reference-article analysis

### 1. Peixoto & Rosvall, 2017

**Research question and gap.** The paper asks how to infer dynamic community structure from both event sequences and temporal networks without imposing arbitrary time windows. The gap is representational and inferential: conventional network aggregation discards ordering, whereas conventional sequence models do not jointly represent network structure and temporal state changes.

**Novelty type.** A unified generative modelling framework: layered temporal-network representation, dynamic community states, model selection and inference in one probabilistic description. The novelty is not “another clustering algorithm”; it is a common computational object that makes sequences and temporal networks comparable.

**Organisation.** The abstract moves from dynamic interactions, through arbitrary-window/overfitting gaps, to an arbitrary-order community Markov model and non-parametric Bayesian selection. The Introduction frames static communities and sequence models as incomplete halves. Results progress from Markov inference and community structure to sequence cases, temporal-network extension, multi-domain data and held-out prediction. A short Discussion returns to arbitrary order, no preset time scale and extensibility. Methods starts in the main article and carries Bayesian integration, priors, likelihoods, prediction, algorithms and data.

**Figures.** Six main figures. Figures 1-2 establish the unified dynamics-on/of-networks object and the Markov/community representation; Figures 3-4 carry the principal flight and proximity-network demonstrations; Figures 5-6 expose time-model and sequence behaviour. Early panels are explanatory and denser; later panels reuse group/state colours across empirical displays. The sequence is concept -> inference -> varied empirical behaviour, not a generic benchmark dashboard.

**Credibility.** Exact description length/Bayesian evidence penalises both misfit and complexity. Token-order shuffling returns every data set to a memoryless random model, testing spurious structure. A first-half/second-half held-out likelihood check agrees with description-length selection. Static DCSBM is a nested special case. Data sources are itemised and a C++ implementation is available through graph-tool. Trust comes from generative closure, null shuffling, predictive agreement and cross-domain cases rather than a conventional significance-test package.

**Language.** Broad phenomenon first, formalism second. Terms such as “dynamic communities” remain interpretable to non-specialists. Claims describe what the representation enables and where information would otherwise be lost.

**Transferable strategy [novelty / clarity / rigour].** Open with the scientific operation that fails after reconstruction; show a minimal counterexample; then prove the query-preservation condition and demonstrate that it changes inference on held-out topologies. Do not lead with CP decomposition.

### 2. Williams et al., 2022

Bibliographic note: the visible publisher PDF lists Oliver E. Williams, Lucas Lacasa, Ana P. Millán and Vito Latora; “Lillo” in the supplied shorthand should be corrected before the reference is reused.

**Research question and gap.** The paper asks how memory should be represented and measured in temporal networks when temporal dependence is richer than a single Markov order or scalar memory parameter. The gap is that existing scalar or fixed-order summaries can miss the shape and scale of dependence.

**Novelty type.** A representation/measurement contribution: memory is treated as a structured object with a shape, not a single coefficient. The contribution links representation to observable temporal-network behaviour.

**Organisation.** The abstract moves from a disputed concept, to a multidimensional definition and estimator, to synthetic validation, real-system variation and a virtual-loop mechanism. The Introduction formally defines temporal-network memory, shows the combinatorial and physical-information failure of scalar encodings, and contrasts pathway approaches. Results proceed through co-memory, virtual loops/spreading, higher-order effects, four synthetic validations and seven real-network classes. The short Discussion states the pairwise limitation and points to collective/simplicial memory. There is no standalone Methods section in the main PDF; detailed estimation, theorems, generation and algorithms are routed to the Supplementary Information.

**Figures.** Four main figures. Figure 1 defines memory shape and virtual loops; Figure 2 connects them to spreading; Figure 3 validates the scalar-memory hit rate on synthetic ensembles; Figure 4 maps memory shapes across real temporal networks. Colour encodes links/memory profiles or systems, with selective annotations and most technical detail carried by axes/captions. The sequence performs definition -> consequence -> synthetic validation -> empirical diversity.

**Credibility.** The co-memory/scalar relationship is theorem-backed. Spreading time is checked analytically and with (10^7) Monte Carlo runs. Four synthetic generators use (10^3) realisations per parameter point and sequences of length (10^6) to test hit rates against known memory. Network size, finite-size behaviour, non-stationarity, resolution and loop decoherence are discussed. Seven real-system classes, multiple resolutions/bands, multi-language code and a Zenodo DOI complete the evidence chain.

**Language.** The title and section framing use a memorable but precise concept (“shape of memory”). Technical definitions are introduced only after the reader sees why a scalar summary fails.

**Transferable strategy [novelty / clarity / significance].** Name the paper around the lost scientific query, not the tensor factorisation. Your analogue is “which response queries survive reconstruction?”, but the paper must also show empirical or benchmark consequences of the distinction.

### 3. He et al., 2024

**Research question and gap.** The paper asks how to predict links in a target temporal-network layer by exploiting a sequence of related network layers. The gap is that many link-prediction methods use a single aggregated graph or a fixed temporal representation and do not exploit ordered layer-to-layer predictive information.

**Novelty type.** Algorithmic architecture plus evaluation protocol: sequential stacking combines predictions across layers and is tested against link-prediction alternatives over multiple temporal-network data sets.

**Organisation.** The abstract leads with the accuracy/scalability/interpretability trade-off, states the counter-intuitive static-feature stacking result and validates it on synthetic and 19 real networks. The Introduction reviews static, temporal-feature, tensor, time-series and deep-learning routes before stating two design goals. Results move through temporal-feature comparison, runtime, two synthetic oracle tests, 19 real networks and feature-importance analysis. Discussion returns to efficiency and no-free-lunch boundaries. Methods defines the two target-observation settings, dyad sampling, leakage-resistant cross-validation, 41 features, random forest, AUC, baseline parameters and synthetic generators.

**Figures.** Eight main figures. Figure 1 explains the sequential-stacking data flow. Figures 2-3 compare predictive performance and computational complexity. Figures 4-5 cover partially and completely unobserved synthetic targets. Figure 6 moves to real networks, and Figures 7-8 analyse feature importance. Repeated algorithm colours and AUC axes make a long validation sequence readable; captions carry high panel density.

**Credibility.** Two synthetic temporal stochastic block-model families cover 90 controlled parameter settings and supply oracle maxima. Nineteen real networks test partially and completely unobserved targets. Tensorial-SBM, E-LSTM-D and ARIMA/time-series baselines are evaluated on the native task. Five-fold cross-validation with ten repeats yields 50 runs, with balanced dyads and explicit target-layer isolation. Runtime, AUC, supplementary precision-recall, feature importance, Zenodo data/code and a Git commit build converging trust.

**Language.** Direct, task-centred and comparative. The algorithm appears after the prediction challenge is explicit. Performance claims are tied to data sets and metrics rather than presented as universal superiority.

**Transferable strategy [rigour / reproducibility / generality].** If the paper claims an estimator contribution, every primary method must be evaluated under the same chronological split, tuning budget, seeds and native topology-query endpoint. Projected graph-feature diagnostics cannot substitute for native baselines.

### 4. Murphy et al., 2021

**Research question and gap.** The paper asks whether a learned model can infer contagion dynamics on complex networks across structural and dynamical settings where analytic or simulation-based calculations are expensive or unavailable. The gap combines computational cost, nonlinear dynamics and topology dependence.

**Novelty type.** A reusable learning framework tied to a mechanistic scientific task. The novelty is supported by generalisation experiments, not only architecture.

**Organisation.** The abstract contrasts tractable mechanistic models with a data-driven complement, then previews arbitrary-network simulation and the Spain case. The Introduction sharpens the tractability/expressivity tension and asks whether GNNs can learn dynamics rather than only structure. Results proceed without subsection headings: task/locality formalisation, four synthetic dynamics, local transition recovery, ER/BA transfer, unseen-Poisson bifurcations and Spain out-of-sample prediction. Discussion frames the method as a complement to mechanistic modelling and notes data scarcity. Methods covers architecture, attention, training, importance weights, metrics, synthetic dynamics, COVID data and baselines.

**Figures.** Six main figures. Figure 1 introduces prediction quality on a representative network/dynamics setting; Figure 2 crosses contagion dynamics with ER/BA structures and degree-dependent error; Figure 3 tests learned bifurcation behaviour beyond direct point prediction; Figures 4-5 move to the Spain mobility/COVID-19 application and out-of-sample evaluation; Figure 6 places architecture detail with Methods. Colours distinguish dynamics/structure/model conditions and error bars or held-out shading identify variability and train-test boundaries.

**Credibility.** Four dynamics of increasing complexity are tested against known local transition probabilities, with MLE as a statistical reference. ER- and BA-trained models transfer to unseen Poisson networks and different mean degrees; their simulations recover bifurcation diagrams with simulation standard deviations. The Spain analysis separates in- and out-of-sample periods and compares three neural architectures, VAR and a mechanistic metapopulation model; locality/connectivity variants act as ablations. Data and code have Zenodo DOIs, and attention coefficients are explicitly not over-interpreted as causal influence.

**Language.** The paper alternates broad scientific stakes with concrete computational tasks. It avoids selling deep learning in isolation; the method matters because it enables contagion-dynamics inference.

**Transferable strategy [significance / generality / rigour].** Tie topology substitution to a recognisable decision or scientific conclusion, test unseen topology families, and report when the model should abstain. A second domain that merely produces a near-zero readout demonstrates computability, not comparable generalisation.

### Cross-paper synthesis

| Shared move | What the four papers do | What this manuscript should do | Review goal |
|---|---|---|---|
| Start with a lost or expensive scientific capability | Dynamic structure, memory shape, ordered-layer prediction or contagion inference | Start with fixed-shock response comparison under alternative topologies | novelty, significance, clarity |
| Make representation operational | The representation changes inference/prediction | Show that query preservation changes recoverable held-out responses, not only endpoint labels | novelty, rigour |
| Put a visual computational object early | Framework/pipeline appears before dense validation | Retain Figure 1, but add the exact support/excitation boundary | visual communication, clarity |
| Validate on the native task | Recovery, prediction or dynamics inference is measured directly | Use native topology-query endpoints and fair causal validation | rigour, generality |
| Generalise by design | Multiple systems, structures or held-out regimes | Test at least in-family and cross-family held-out topologies; mark unsupported directions | generality, rigour |
| Build trust through converging evidence | Theory/model, controls, baselines and empirical diversity agree | Align theorem, estimator gate, uncertainty and application; do not let early positive and later negative gates coexist silently | rigour, reproducibility |

**Next most valuable modification [novelty / clarity]:** rewrite the literature paragraph around four computational operations and their limits, then state exactly which operation remains unresolved: preserving and estimating a supplied-topology response after temporal reconstruction.

---

## Stage 2. Nature/NCS writing paradigm

| NCS writing module | Target reader question | Recommended form | Common failure | Implication here |
|---|---|---|---|---|
| Title | What scientific/computational capability is delivered? | Name the operation and domain in plain searchable terms | Stack bespoke nouns and method acronyms | Keep topology-dependent response/reconstruction; omit CP from the preferred title |
| Abstract context | Why does the problem matter beyond one data set? | One sentence naming the scientific query | Generic “complex systems are ubiquitous” opening | Use fixed-shock propagation under alternative exposure graphs |
| Abstract gap | What fails computationally? | State the lost input/query and why existing output cannot answer it | “Existing methods have limitations” | A collapsed map need not retain direct/network components |
| Abstract approach | What object resolves the gap? | Define the representation or algorithm at one level of abstraction | Introduce CP, ALS, ranks and operator notation too early | Say “separated direct, network and topology arguments” |
| Abstract evidence | What is the strongest verified result? | Give one quantitative result plus scope and uncertainty | Report best-case ranges while omitting a stricter failed gate | Reconcile R006c before restoring any CP number |
| Abstract implication | What can readers now do, and what remains out of scope? | One reusable implication plus one boundary | End with package mechanics or universal claim | Query design before smoothing; no causal topology claim |
| Introduction hourglass | Why this gap, why now, why this paper? | phenomenon -> computational operation -> closest methods -> exact unresolved gap -> study/evidence | Citation catalogue or equations before the reader understands the operation | Four paragraphs; equation moves to final paragraph/Fig. 1 |
| Results opening | What is the paper's central claim? | Claim-led subsection and one decisive figure | Chronology of implementation steps | Start with representation theorem/counterexample |
| Results validation | Should I trust the method? | Fair native baselines, matched splits, uncertainty and failure regimes | Mix endpoint availability dashes with numerical superiority | Separate availability matrix from common-endpoint performance |
| Figure sequence | Can I understand and verify the story without Methods? | object -> decisive benchmark -> generalisation/scale -> consequential application | Two descriptive/near-null applications after weak validation | Figure 3 should be held-out/scale; application only after a non-trivial result |
| Methods | Can I reproduce and audit the result? | Data, estimator, tuning, baselines, metrics, uncertainty and compute in explicit contracts | Long derivation with unresolved truth conflicts | Fix rank provenance and protocol hierarchy first |
| Discussion | What changed in computational science? | Finding -> relation to fields -> operating regime -> limitations -> reuse | Repeat model definition and list distant applications | Emphasise query-preserving computation and distinguish support from recovery |
| Cross-disciplinary access | What must a non-network specialist know? | Define topology substitution, endpoint and frozen path once | Repeated specialised synonyms | Use a fixed four-level terminology throughout |
| Reproducibility | Can another group regenerate and extend this? | DOI, environment, hashes, source-data map, clean command and restricted-data route | Future-tense “will deposit” plus internal archive narration | Keep future tense until DOI exists; provide a clean-room manifest |

### Recommended hourglass

`network response question -> information lost by reconstruction -> exact query-preservation condition -> estimator/evidence -> implications for temporal-network computation -> boundaries`

### Recommended figure grammar [visual communication / clarity / reproducibility]

- Black/grey: common fitted path, unavailable/unsupported endpoint and controls.
- Teal: proposed separated or supported-query method.
- Ochre: comparator/alternative representation.
- Red only: failed stability/support condition, never a routine comparator.
- Same method, same colour and marker in every figure.
- Put sample size/replications in each panel, not only the caption.
- Use “unsupported” and “outside target” as distinct visual states.

**Next most valuable modification [novelty / clarity / rigour]:** rebuild the story around one reusable computational distinction: representation defines a query; data excitation identifies it; estimation recovers it; stability transports error to responses.

---

## Stage 3. Diagnosis against NCS standards

| Current issue | Nature/NCS comparator practice | Why it matters | Exact change | Review goal | Priority |
|---|---|---|---|---|---|
| Earlier positive benchmark dominates despite latest negative gate | Strongest and most relevant validation controls the headline | Selective evidence hierarchy invites immediate rejection | Remove/qualify CP superiority until claim ledger resolves R006c; report stricter negative gate | rigour, clarity | P0 |
| Availability is partially conflated with identification/recovery | Representation papers separate formal support from empirical performance | A defined endpoint can still be unidentifiable or badly estimated | Fix four terms: defined, identified, recoverable, stable | novelty, rigour, clarity | P0 |
| RCEP rank is inconsistent | NCS resources require one auditable configuration | Readers cannot reproduce empirical figures | Resolve rank from artifact metadata; regenerate cleanly | reproducibility, rigour | P0 |
| Figure 4 uses two network-share estimands | Figure labels and prose must name the same quantity | Panel c computes absolute network mass over absolute total mass (about 0.24/0.32); prose/bootstrap computes the residual of total and direct absolute masses (0.379/0.485; medians 0.371/0.481) | Select the scientifically intended estimand, justify its denominator, recompute point/bootstrap values and regenerate figure, caption and prose | reproducibility, rigour, visual communication | P0 |
| Headline baseline is unrestricted rolling | Native task papers compare strong, tuned alternatives fairly | A weak baseline inflates apparent gain | Add causal fused-TV/spline, local, matched Tucker under equal budgets | rigour, significance | P0 |
| Primary ranges lack paired confirmation | Strong claims use prespecified units and uncertainty | Median/IQR plots do not quantify paired superiority | Report paired effect, 95% interval, win fraction and multiplicity contract | rigour | P0 |
| Collapsed-map dashes are treated as method evidence | Structural controls and performance baselines have different roles | “Undefined by design” cannot lose a numerical contest | Label structural negative control; compare common endpoints numerically | clarity, rigour | P0 |
| RCEP inference changes across uncertainty layers | Strong applications foreground full estimation uncertainty | Conditional fixed-path CI is narrower than re-estimated CI that crosses zero | Make re-estimation interval the interpretation boundary | rigour, clarity | P0 |
| Methods theory is deterministic only | NCS method papers connect algorithm to recovery or approximation theory | Current lemma transfers assumed error but does not establish estimator success | Add support/identification theorem and oracle/rate result, or narrow paper type | novelty, rigour | P1 |
| NYC only shows computability and near-null output | Generality requires varied regimes or held-out structures | Second domain alone does not establish transfer | Call it a public falsifiability/reproducibility check; move to Supplementary unless it gains scientific consequence | generality, significance | P1 |
| Figure 2 mixes availability, accuracy, scale and stability | Main figures usually answer one major reader question | Dense scope flags compete with the result | Split “can answer?” from “how accurately?”; show paired distributions and failure boundary | visual communication, clarity | P1 |
| Figures 3 and 4 do not deliver an evidence climax | Final main figure often establishes impact/generalisation | Two bounded/near-null applications flatten the narrative | Use Fig. 3 for held-out/scale; keep one consequential Fig. 4 or stop at three figures | visual communication, significance | P1 |
| Introduction cites four fields as a list | Nature introductions synthesise an operation-level gap | Current paragraph looks borrowed rather than necessary | Contrast what each representation preserves, then isolate response-query preservation | novelty, clarity | P1 |
| Methods are detailed but reader-facing text repeats contracts | Main text gives only what interprets results | Repeated “same path/endpoint contract” slows Results | Define once in Fig. 1; move implementation and inventory to Methods/SI | clarity | P2 |
| Code/data are promised, not deposited | NCS favours immediately inspectable resources | Future availability weakens trust | Deposit DOI, environment lock, source maps and checksums before submission | reproducibility | P1 |

### First-impression risks in order

1. Claim-evidence mismatch between headline and latest audit.
2. Unclear paper identity: CP method, representation theorem or empirical network application.
3. Novelty may be read as “keep (A), (B) and (W) separate” unless the query-support theorem and statistical boundary are formalised.
4. No decisive empirical consequence and no successful native held-out recovery.
5. Reproducibility conflict in selected rank.

### Defensible contribution statement now

> We formalise topology substitution as a query on a reconstructed time-varying network autoregression and show that the query is not defined by a collapsed dynamic map unless an additional inverse is identified. This representation result does not by itself guarantee statistical recovery, which depends on design excitation and response stability.

### Claims not currently licensed

- CP generally improves topology-switch recovery.
- The framework determines which unseen topologies are statistically recoverable.
- RCEP establishes a substantive or causal propagation effect.
- NYC establishes cross-domain generalisation.
- Projected graph-feature rows establish superiority over native graph-learning systems.

**Next most valuable modification [novelty / clarity / rigour]:** decide the paper identity. With current evidence, use the representation/estimand route; switch to an estimator-method route only after the native recovery gate, theory and fair baseline package pass.

---

## Stage 4. NCS submission optimisation plan

### Five title options [novelty / clarity / significance]

| Title | Positioning | Risk |
|---|---|---|
| **When reconstructed network models retain topology-dependent responses** | Accurate representation/condition paper; current preferred route | Less method-forward; may appear conceptual unless theorem/evidence is strengthened |
| **Preserving topology-dependent queries in evolving network models** | Reusable computational-principle framing | “Preserving” may imply successful statistical recovery; use only if the text distinguishes definition from recovery |
| **Topology-dependent responses after temporal network reconstruction** | Searchable and neutral | Descriptive; does not signal the precise contribution |
| **Query-preserving reconstruction of time-varying network dynamics** | Strong computational-method framing | Not licensed until a native estimator succeeds |
| **Low-rank reconstruction for topology-indexed network responses** | Algorithmic CP/Tucker route | Highest risk: invites direct accuracy, scale and baseline scrutiny that current evidence does not pass |

### Evidence-bounded abstract rewrite [clarity / rigour / significance]

This version is scientifically consistent with the visible evidence. It is **not** a recommended submission abstract until the method gate is resolved, because the negative result leaves an NCS-level significance gap.

1. **[background]** Evolving-network models are often smoothed before analysts compare how a fixed shock propagates under alternative exposure graphs.
2. **[computational gap]** A reconstructed dynamic map, however, need not retain the direct and network components required to define that comparison.
3. **[approach]** Here we formulate topology substitution as a query on a time-varying network autoregression and separate endpoint definition, identification, statistical recovery and response stability.
4. **[result]** A representation that retains direct dynamics, network transmission and topology as separate arguments defines observed, zero-network and benchmark-topology responses, whereas a collapsed map requires an additional identified inverse.
5. **[result]** Earlier controlled benchmarks showed lower error than unrestricted rolling estimation in specific low-dimensional designs, but a stricter endpoint-aware benchmark did not validate general native recovery by the tested CP or Tucker candidates.
6. **[result/boundary]** Trade and mobility examples demonstrate fixed-path computation; the trade contrast crosses zero after re-estimation and the mobility contrast is near zero.
7. **[implication]** The results establish a representation criterion for topology-dependent response queries, while statistical recovery and causal interpretation require additional excitation and design assumptions.

### Post-gate abstract template [clarity / novelty / significance / rigour]

Use this only if a prespecified successor experiment passes:

1. **[background]** Evolving-network models are often smoothed before analysts compare how a fixed shock propagates under alternative exposure graphs.
2. **[computational gap]** Existing reconstruction objectives can fit the observed dynamics while discarding or weakly identifying the components required for this comparison.
3. **[approach]** We develop a query-preserving estimator that retains direct and network dynamics and reports whether a held-out topology lies within the training-excited response subspace.
4. **[result]** Across [number] prespecified regimes and [number] held-out topology families, the method reduced [primary endpoint] error by [effect and 95% CI] relative to [strongest fair baseline], with [win fraction] paired wins.
5. **[result]** It correctly marked [number/percentage] unsupported topology directions and maintained [accuracy/cost] through (N=[value]).
6. **[result]** In [application], topology substitution changed [scientifically interpretable quantity] by [effect and uncertainty], while placebo and re-estimation analyses [outcome].
7. **[implication/boundary]** Query-aware reconstruction makes alternative-topology responses reusable when excitation and stability conditions hold; it does not identify endogenous network formation or causal interventions.

### Introduction reconstruction [novelty / clarity / significance]

| Paragraph | Rhetorical function | Reader question | Evidence needed | Avoid |
|---|---|---|---|---|
| 1 | Establish the scientific operation | Why compare the same shock under different topologies? | Examples from network propagation/response analysis already cited | Generic complex-systems opening; equation |
| 2 | Show representation failure | What information can smoothing remove? | Minimal two-representation counterexample and relation to temporal-network memory/community work | Four-paper citation list |
| 3 | Locate closest computational methods | Why do TVP-VAR, GVAR, low-rank and graph methods not already settle this? | Operation-level comparison: fitted target, stored object, supported query | Claiming all prior methods fail; method-family labels |
| 4 | State exact challenge and contribution | What must be defined, identified and estimated? | Query-support theorem, excitation condition, finite-horizon transfer | Conflating algebraic availability with recovery |
| 5 | Preview evidence and boundaries | What did the paper actually test and find? | Strongest reconciled benchmark, held-out topologies, scale, application | Long non-claim inventory; unverified CP numbers |

#### Proposed Introduction opening and gap paragraphs

> Models of evolving networks are often used for a question that is deliberately counterfactual in topology but fixed in dynamics: how would the same shock propagate if the exposure graph were replaced, removed or held at a benchmark state? Answering this question requires more than a fitted trajectory. The fitted object must still accept topology as an input while holding its coefficient path, shocks and response horizon unchanged.
>
> Temporal reconstruction can remove that capability even when it improves fit or prediction. If direct dynamics and network transmission are collapsed into a single map at the observed graph, an alternative-topology response is not defined without an additional inverse that recovers the separated components. This is a representation problem before it is an estimation problem. Related work on dynamic communities, temporal memory, sequential link prediction and contagion learning likewise shows that the stored representation determines which structures or dynamics remain measurable. What remains unresolved here is the corresponding condition for topology-indexed response queries after smoothing time-varying network models.
>
> Existing time-varying autoregressions, network and global vector autoregressions, and low-rank tensor models address coefficient drift, cross-unit exposure and high-dimensional regularisation. These method families do not, by name alone, establish that a reconstructed object defines or identifies responses at a supplied topology. The relevant computational distinction is query-specific: whether the stored representation retains the direct block, the network block and the topology action, or identifies them from a declared inverse under sufficient excitation.

### Results reorganisation [novelty / rigour / clarity / generality]

| Proposed subsection | Core claim | Main figure | Required evidence | Current gap |
|---|---|---|---|---|
| 1. A reconstructed map supports only queries constant on its information loss | Exact representation/query condition; collapsed map counterexample | Fig. 1 | Necessary/sufficient theorem; minimal example | Current argument is persuasive but theorem should be promoted and generalised |
| 2. Query definition does not guarantee recoverability | Availability, excitation and stability are separate gates | Fig. 2a-b | Support projector/excitation metric; exact-support stress | R006d construction failed to produce unsupported endpoint in full-rank DGP |
| 3. Native held-out topology recovery under fair comparison | One fixed estimator improves common endpoints | Fig. 2c-f | Successful Track A; local/fused/Tucker; paired CI/win fraction | Current R006c is negative; primary claim blocked |
| 4. Generalisation and computational scaling | Accuracy-cost region across topology families and (N) | Fig. 3 | Cross-family endpoints, runtime, peak memory, failures | N=50 bounded; no N=100/200 repeated scale evidence |
| 5. Topology substitution changes a scientific readout | Stable, interpretable consequence with uncertainty/placebos | Fig. 4 | Consequential public application | RCEP crosses zero; NYC near-null |

If the new estimator does not pass, stop after subsection 2, report the estimator failure transparently and target a specialist methods/theory venue. Do not fill subsections 3-5 with weaker diagnostics.

### Figure plan [visual communication / clarity / rigour / significance]

| Figure | Function | Panel design | Visual treatment | Current action | Text position |
|---|---|---|---|---|---|
| Fig. 1 | Define the computational object and exact failure | a scientific query; b separated representation; c collapsed-map counterexample; d query-support theorem/excitation boundary | Reduce boxes; use one accent colour; distinguish “undefined” from “unsupported” | **Redraw/extend** current Fig. 1; retain core logic | End of first Results subsection |
| Fig. 2 | Decisive validation | a four-gate ladder; b support classification; c-d paired held-out operator/GIRF errors; e win fractions; f stability/failure regime | Same seeds connected or shown as differences; CI plus raw points; replication counts visible | **Replace** current Fig. 2 after Track A; keep current availability panel as 2a | Central validation subsection |
| Fig. 3 | Generalisation and compute | a topology-family transfer; b temporal misspecification; c accuracy-runtime Pareto; d memory/scaling; e failures/abstention | Log scales only where necessary; one method colour grammar | **Current RCEP Fig. 3 cannot serve this role**; move it to Supplementary unless application becomes decisive | After validation |
| Fig. 4 | Consequential application | a domain/topology; b observed-vs-substituted response; c uncertainty/placebos; d decision/scientific consequence | Annotate the domain event; avoid decorative topology metrics | **NYC current Fig. 4 -> Supplementary** as near-null/public reproducibility check; replace with consequential application or omit Fig. 4 | Final Results subsection |

#### Existing-figure decisions [visual communication / clarity / rigour]

- Current Figure 1: keep and simplify; it is the strongest first-impression asset.
- Current Figure 2: conceptually strong but too dense and evidentially outdated as a headline; rebuild from the reconciled primary protocol.
- Current Figure 3: retain under the current four-figure narrative because panel a clearly distinguishes fixed-path from re-estimated uncertainty. Move panel d to Supplementary; enlarge panels a-c and label panel c as a point estimate unless an existing interval can be shown. Under the eventual NCS method route, this figure may still be displaced by held-out generalisation/scale evidence.
- Current Figure 4: correct before any layout decision. The figure script uses `sum(abs(network))/sum(abs(total))`, whereas the evidence/manuscript bootstrap path uses `(sum(abs(total))-sum(abs(direct)))/sum(abs(total))`. Select one scientifically valid network-share estimand, regenerate point and bootstrap outputs, then decide whether the near-null boundary case merits main-display space; otherwise move it to Supplementary.
- Table 1: replace prose-heavy “scope flag” matrix with a compact availability/support legend or Supplementary table.
- Table 2: keep in Supplementary; main text should state the full-estimation interval that crosses zero.

#### Figure-level visual corrections [visual communication / clarity / reproducibility]

- Figure 1: use stable low-saturation colours for direct/network/topology; add a short “separated reconstruction” entry; route a new-topology arrow directly into a visibly blocked collapsed map.
- Figure 2: let the endpoint gate occupy 35-40% of the figure height; write availability states inside cells; never place “outside target” marks on a numerical axis where they can be read as zero error. Keep only the headline operator endpoint and one topology-specific endpoint below; move stability to Supplementary.
- Figure 3: retain panel a as the hero; if panel d remains, mark `n=36 dates` and “descriptive, not causal” in the panel itself, and show an interval only if it already exists.
- Figure 4: align observed/frozen and difference panels on one time axis; state mean difference and stability in-panel; label the exact statistic represented by channel shares.
- Production: Figures 1/2 contain Type 3 glyphs while Figures 3/4 use embedded TrueType fonts. Re-export with one sans-serif/math font system. Do not use teal for both a method (Tucker) and a semantic channel (network).

### Methods optimisation [rigour / reproducibility / clarity]

**Move before Methods/main Results:**

- One-sentence model and topology-substitution estimand.
- Four-gate distinction: defined -> identified -> recoverable -> stable.
- Minimal support/excitation condition required to interpret Figure 2.
- Exact primary evaluation endpoint and strongest comparator.

**Keep in Methods:**

- Data construction and predetermined-topology assumption.
- Joint/local estimator objective, chronological tuning and no-leakage rules.
- Baseline definitions and equal-budget contract.
- Metrics, pairing unit, confirmatory inference and multiplicity.
- Uncertainty design, including whether tuning is reselected.
- Runtime/hardware/software and failure handling.

**Move to Supplementary:**

- Full derivations, CP/Tucker ALS details, all tuning surfaces and secondary metrics.
- Projected graph-feature diagnostics, because they are not native baseline rankings.
- Alternative topology construction inventory and all descriptive topology correlations.
- NYC near-null portability check.
- Internal reproduction commands, hashes and source-acquisition detail in a dedicated reproducibility appendix/README rather than scientific prose.

**Credibility upgrades [rigour / reproducibility]:**

1. Resolve the rank conflict from source artifacts and clean-room regenerate every empirical figure.
2. Freeze all primary seeds/endpoints/comparators before successor outcomes are viewed.
3. Use equal seeds, repetitions, tuning windows and budgets for all primary methods.
4. Report every method failure and unstable response, not only stable medians.
5. Separate structural negative controls from performance baselines.
6. Publish source-data files for every main figure and a one-command derived-to-result build.
7. Record exact environment, hardware, random seeds, stopping rules and convergence failures.

### Discussion/Conclusion optimisation [significance / generality / clarity / rigour]

**Paragraph 1:** state the confirmed scientific result, not the operator definition.  
**Paragraph 2:** connect it to temporal networks: dynamic communities preserve state structure; memory representations preserve temporal dependence; link-prediction stacks preserve layer information; contagion learners preserve dynamics. Your contribution concerns which response queries survive reconstruction.  
**Paragraph 3:** state what changes for computational practice: declare downstream queries before choosing a reconstruction target; test support/excitation; return unsupported rather than extrapolate.  
**Paragraph 4:** give limitations once: native recovery, scale, tuning-conditional uncertainty, topology endogeneity and application scope.  
**Paragraph 5:** close on a bounded reusable principle, not future application lists.

#### Proposed bounded Discussion close

> The practical implication is that reconstruction should be designed around the queries that will be asked of the fitted object. Alternative-topology responses require a representation that retains, or identifies, the topology action; they also require sufficient excitation to estimate that action and sufficient stability to propagate its error. These conditions are distinct, and a model should report failure at any one of them rather than return an unqualified response. The present evidence establishes the representation distinction and demonstrates fixed-path computation, but it does not establish causal topology effects or general native recovery. A reusable topology-query method will require successful held-out recovery, calibrated uncertainty and validation across network families and scales.

**Next most valuable modification [rigour / visual communication]:** do not redraw Figures 2-4 yet. First obtain a successful and audited native recovery result; otherwise adopt the narrower representation-paper structure and change venue expectations.

---

## Stage 5. Language refinement

| Expression class | Original problem | NCS principle | Rewrite template | Directly usable example | Review goal |
|---|---|---|---|---|---|
| Computational gap | “Existing methods have limitations” | Name the unavailable operation and cause | “Although X estimates [object], it does not by itself define [query] because [missing information].” | “A smoothed total map can fit the observed dynamics without retaining the direct and network components required for an alternative-topology response.” | novelty, clarity |
| Methodological contribution | Method name precedes reader need | Define capability before implementation | “We formulate/develop [object] that enables [operation] under [conditions].” | “We formulate topology substitution as a query on a fitted network autoregression and make the required representation explicit.” | novelty, significance |
| Algorithmic novelty | CP described as inherently novel | State what changes in objective/constraint | “Unlike [closest target], the estimator optimises [native loss] while preserving [query-specific structure].” | “Unlike coefficient smoothing that weights all block directions equally, the proposed estimator [optimises the native outcome loss] while retaining the topology action.” | novelty, rigour |
| Empirical finding | Lists coefficients without claim/boundary | Lead with observation, then value and scope | “Under [design], [quantity] changed by [effect, uncertainty]; [boundary].” | “Under fixed-path substitution, the coefficient difference was 0.000180, but the re-estimation interval (-0.000071, 0.000470) included zero.” | clarity, rigour |
| Comparative advantage | “Outperforms/superior” from best-case range | Specify comparator, endpoint, pairing and uncertainty | “Relative to [baseline], [method] changed [metric] by [paired effect, CI] across [scope].” | “Relative to causal fused-TV, the estimator reduced held-out GIRF error by [effect, 95% CI] across [number] prespecified cells.” | rigour, significance |
| Robustness | Inventory of sensitivity checks | Say what conclusion survives which perturbation | “The conclusion was unchanged when [perturbations], but not when [failure].” | “The sign was unchanged across import-, export- and symmetric-weight definitions, but directional interpretation did not survive full path re-estimation.” | rigour |
| Generality | “Works across domains” from two examples | Tie scope to varied held-out regimes | “The method retained [performance] across [explicit dimensions]; evidence outside these regimes is unavailable.” | “The current analyses establish computability in trade and mobility panels; they do not yet establish recovery across topology families or network scales.” | generality, clarity |
| Interpretability | Correlation is presented as mechanism | Name the readout and non-causal status | “[Feature] was associated with [model-derived readout]; this descriptive relation does not identify [mechanism].” | “Spectral gap was associated with the fitted propagation index, but the relation does not identify a transmission mechanism.” | clarity, rigour |
| Reproducibility | “Code will be available” | State what is available now and what requires access | “The archive contains [artifacts] sufficient for [level]; reconstruction from raw sources requires [conditions].” | “The derived archive regenerates the reported figures and tables; raw-panel reconstruction additionally requires provider-governed IMF and MRIO inputs.” | reproducibility |
| Limitation | Generic closing caveat | Link each boundary to the claim it limits | “Because [condition], the result supports [narrow claim] but not [stronger claim].” | “Because topology is supplied rather than modelled, the contrasts describe propagation on a fitted path and do not identify effects of network formation or policy assignment.” | rigour, clarity |

### Ten high-risk words and replacements [clarity / rigour]

- `identify` -> `define`, `diagnose`, or `estimate`, depending on the actual layer.
- `support` -> specify `formally defines`, `is data-supported`, or `is empirically recovered`.
- `demonstrate` -> `illustrate` for applications without decisive inference.
- `robust` -> state the perturbations and surviving conclusion.
- `general` -> name network families, scales and regimes.
- `superior` -> give comparator, endpoint and paired interval.
- `mechanism` -> `association` unless causal/mechanistic evidence exists.
- `uncertainty` -> say conditional bootstrap, re-estimation sensitivity or calibrated coverage.
- `reproducible` -> distinguish derived-to-figure from raw-to-result.
- `topology-switchable` -> define once, then use `alternative-topology response` for broad readers.

**Next most valuable modification [clarity / rigour]:** run a global terminology audit that assigns every use of `support`, `identify`, `recover`, `stable`, `robust` and `general` to an explicit evidence layer.

---

## Stage 6. Iterative re-review

### Reviewer 1: Nature Computational Science senior editor

**First impression.** The manuscript has a clear representation-level question and a competent conceptual figure, but the computational advance is narrower than the title/abstract evidence hierarchy implies. The paper does not yet show a reusable method succeeding on the hard native task or producing a consequential scientific result.

**Likely challenge.** Is the contribution more than the requirement to retain (A), (B) and (W) separately when alternative (W) values will be queried? Why should NCS readers adopt this framework rather than treat it as a model-specification caution?

**Evidence most needed.** A necessary/sufficient query-support theorem, successful held-out native recovery against strong fair baselines, scale/compute evidence and one application that changes an interpretable conclusion.

**Desk-rejection risk.** Very high if the current positive CP numbers remain while the latest negative audit is omitted or if the paper is submitted as a broad estimator contribution.

**Single most important revision [novelty / significance / rigour].** Choose and prove one contribution level. With current evidence, present a bounded representation theorem; for an NCS method route, do not resubmit until the native estimator gate passes.

### Reviewer 2: computational methods reviewer

**First impression.** The manuscript is unusually explicit about endpoint contracts and limitations, but the validation hierarchy is not yet coherent. Comparator budgets, replication counts, tuning uncertainty and stronger temporal baselines are not aligned with the headline.

**Likely challenge.** Why is unrestricted rolling the principal reference when causal fused temporal smoothing is stronger? How are the earlier positive benchmark and R006c negative gate related? Which rank generated the RCEP figures?

**Evidence most needed.** Clean run manifest, equal-budget paired benchmark, chronological leakage tests, confirmatory intervals/win fractions, failure rates, and a theory result that links the proposed estimator to statistical recovery.

**Major-revision risk.** Critical. The rank conflict alone blocks reproducibility; the negative endpoint-aware gate blocks superiority.

**Single most important revision [rigour / reproducibility].** Create a versioned claim-evidence ledger and rerun the primary benchmark from a frozen, clean-room protocol with the strongest fair baselines.

### Reviewer 3: temporal/complex networks domain expert

**First impression.** The manuscript connects sensibly to temporal-network representation, but the literature bridge is currently rhetorical. Dynamic communities, memory, sequential prediction and contagion learning solve different tasks; citing them does not by itself establish a common gap.

**Likely challenge.** What exact topology information is unavailable after reconstruction, when can it be recovered from multiple observed topologies, and how does this differ from established network VAR/GVAR scenario analysis?

**Evidence most needed.** Query-specific kernel/row-space condition, topology-excitation certificate, cross-family held-out topologies and an explicit operation-level comparison with network VAR/GVAR and temporal graph models.

**Major-revision risk.** High. Without the theorem and native tests, novelty may be judged as an incremental bookkeeping constraint.

**Single most important revision [novelty / generality / rigour].** Promote the representation theorem and excitation boundary to the centre of Figure 1/Results, and test them on unseen topology families.

### Editorial synthesis

**Consensus:** the paper has a coherent question but is not presently NCS-ready. All three reviewers converge on the mismatch between a potentially valuable representation principle and insufficient evidence for a broad estimator contribution. The computational reviewer adds a reproducibility blocker; the domain reviewer adds a novelty blocker; the editor adds a significance blocker.

**Decision simulation:** reject in present form / invite resubmission only after fundamental new evidence. This is not a prose-level major revision.

### Next-round task list

| Order | Task | Completion gate | Goal |
|---|---|---|---|
| 1 | Resolve empirical rank and artifact provenance | One manifest regenerates all main empirical outputs with no configuration conflict | reproducibility, rigour |
| 1a | Reconcile Figure 4 channel-share estimand | One justified formula is used for point and bootstrap values; figure, caption, prose and source data agree | reproducibility, rigour, visual communication |
| 2 | Build claim-evidence ledger | Every abstract/Results/Discussion claim maps to a passing audit or is downgraded | rigour, clarity |
| 3 | Freeze contribution route | One-page statement selects representation or estimator route | novelty, clarity |
| 4 | Complete query-support/excitation theory | Necessary/sufficient support condition plus supported/unsupported decomposition | novelty, rigour |
| 5 | Run prespecified Track A | One fixed candidate passes all native endpoints with equal-budget baselines | rigour, significance |
| 6 | Add paired confirmation | Effect interval, win fraction and multiplicity contract pass | rigour |
| 7 | Validate scale and compute | Repeated N=50/100/200 runtime, memory, accuracy and failures | significance, generality |
| 8 | Calibrate uncertainty | Coherent series-level coverage or explicitly sensitivity-only language | rigour |
| 9 | Add/replace application | Stable non-trivial result with placebos and re-estimation boundary, or omit broad application claim | significance, generality |
| 10 | Rebuild figures and prose | Figure sequence follows theorem -> validation -> generalisation -> consequence; terminology audit passes | clarity, visual communication |
| 11 | Deposit reproducibility package | DOI, environment lock, source-data map and clean command available | reproducibility |
| 12 | Repeat three-reviewer audit | No P0 claim/evidence, baseline or provenance issue remains | all |

**Next most valuable modification [rigour / reproducibility]:** complete tasks 1 and 2 only. They are small enough to execute immediately and determine whether any later manuscript wording is scientifically legal.

---

## Final prioritisation

### P0: before any prose or figure polishing [rigour / reproducibility / clarity]

1. Reconcile RCEP rank and regenerate outputs.
2. Reconcile early positive benchmarks with R006c/R006d outcomes in a claim-evidence ledger.
3. Remove or downgrade every CP/general-recovery headline not licensed by the strongest applicable audit.
4. Decide representation-paper versus estimator-paper route.

### P1: evidence required for an NCS route [novelty / significance / rigour / generality]

1. Query-support and excitation theory.
2. Successful native held-out recovery with fair baselines and paired confirmation.
3. Cross-family topology generalisation and accuracy-cost scaling.
4. Calibrated uncertainty and one consequential application.

### P2: only after P0/P1 [clarity / visual communication / reproducibility]

1. Redraw Figures 2-4.
2. Rewrite final abstract and title.
3. Compress Methods and polish language.
4. Final claim, citation, source-data and reproducibility audit.

The central strategic rule is simple: **do not use stronger prose to compensate for a failed evidence gate.** Either narrow the paper to the representation result that the evidence supports, or generate the method, theory and application evidence required for the broader NCS claim.
