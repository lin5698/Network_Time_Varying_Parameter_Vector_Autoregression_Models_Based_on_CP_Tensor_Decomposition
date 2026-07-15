# NCS Reference Strategy Memo

Purpose: use primary-source materials from the four target Nature Communications papers, plus the current manuscript package, to guide the next Nature Computational Science-oriented revision. This memo is a strategy artifact, not manuscript text.

Primary sources inspected:

- Peixoto and Rosvall, "Modelling sequences and temporal networks with dynamic community structures", Nature Communications 2017: https://www.nature.com/articles/s41467-017-00148-9
- Williams, Lacasa, Millan and Latora, "The shape of memory in temporal networks", Nature Communications 2022: https://www.nature.com/articles/s41467-022-28123-z
- He et al., "Sequential stacking link prediction algorithms for temporal networks", Nature Communications 2024: https://www.nature.com/articles/s41467-024-45598-0
- Murphy, Laurence and Allard, "Deep learning of contagion dynamics on complex networks", Nature Communications 2021: https://www.nature.com/articles/s41467-021-24732-2
- Nature Computational Science Article format page: https://www.nature.com/natcomputsci/submission-guidelines/content-types

Verification update, 2026-07-07: official Nature PDF pages were accessible for the four Nature Communications papers. The article-level architecture, figure count/order, Methods placement and data/code availability pattern below are therefore PDF-verified. This memo still does not make unverified claims about peer-review history, hidden source-code internals, article-level impact or how Nature Computational Science editors would judge the current manuscript.

## Stage 0: Material Sufficiency

Available for the current manuscript:

- Title, abstract, introduction, results, discussion and methods source sections.
- Main manuscript, supplementary information, cover letter and submission materials generated in `output/submission_package/natcs_current`.
- Four main figures and two main tables in the generated manuscript.
- Supplementary notes on notation, estimator, propagation objects, benchmarks, empirical construction, robustness, reproducibility and scope.
- Code/data availability statements and cleanroom reproduction checks.
- Evidence registers, scope-boundary checks, readiness tables and numeric traceability tables.

Still missing or externally constrained:

- Figure source files and production artwork files for the four comparator papers. This affects detailed typography imitation, source-data packaging imitation and final artwork-file judgement.
- A complete raw-to-derived rebuild path for restricted trade inputs. This affects reproducibility at the raw-data acquisition layer.
- Journal portal rendering for the submitted manuscript and standalone figure sources, especially Fig. 2. Local page-render QA for the current main figures is complete, but the portal preview can still rasterize or scale figures differently.
- Any editor pre-submission feedback from Nature Computational Science. This affects fit judgement.

Analysis still possible:

- NCS fit, claim-evidence alignment, figure-sequence logic, reproducibility boundary, cover-letter positioning and reviewer-risk diagnosis can be assessed from the current package.
- Reference article structure can now be used to calibrate argument architecture, main-figure pacing, Methods/Supplementary split and trust-building moves. It remains unsafe to infer hidden review history, exact production decisions or code internals from the PDFs alone.

Stage 0 next most valuable modification:

- Complete the Fig. 2 journal-portal preview record or confirm that the standalone Fig. 2 PDF/SVG is inspectable with comfortable zoom. This is the highest-impact missing material because Fig. 2 carries the endpoint-availability gate. Tags: visual communication / rigour.
- Add a one-page author statement on which raw input blocks can be shared with reviewers. This would not change the derived-evidence claim, but it would make the raw-to-derived boundary easier for a reproducibility reviewer to assess. Tags: reproducibility / clarity.

## Stage 1: Reference Article Analysis

| Paper | PDF-verified research problem and gap | Novelty type | PDF-verified article architecture | Main-figure strategy | Credibility-building moves | Transferable strategy for current manuscript |
| --- | --- | --- | --- | --- | --- | --- |
| Peixoto and Rosvall 2017 | Sequences and temporal networks need a representation that can infer time-dependent community structure rather than collapsing dynamics into static modules or independent snapshots. | Statistical-inference/model framework for dynamic community structure. | Abstract and introduction define the representation problem; Results build the model object and demonstrate inferred structures; Methods are extensive in the article body; Data and Code availability are explicit. | Six main figures. Fig. 1 introduces the model object. Later figures progressively test compression, interaction recovery, empirical networks and model comparison. | Clear object definition, formal likelihood/description-length basis, empirical demonstrations, data availability and code availability. | Put the computational object before the domain readout. Fig. 1 should make the response object visually unavoidable; later evidence can then test what the object makes measurable. Serves novelty / clarity / visual communication. |
| Williams, Lacasa, Millan and Latora 2022 | Memory in temporal networks needs a measurable shape rather than a single decay summary, and that shape differs across empirical systems. | Measurement/characterization framework for temporal-network memory. | Introduction motivates memory as a network-science object; Results move from a schematic memory kernel to empirical shapes, reconstruction and model comparison; Methods are compact in the article body with further material in the Supplementary; Data and Code availability are explicit. | Four main figures. The sequence is compact: conceptual kernel, empirical memory-shape estimation, reconstruction consequences and model comparison/fit. | Cross-system evaluation, a named measurement object, source-data/code statements and supplementary expansion. | Keep empirical domains as tests of one measurement object. For the current manuscript, RCEP and NYC should read as endpoint demonstrations of the same topology-switchable operator, not as two separate application papers. Serves significance / generality / visual communication. |
| He et al. 2024 | Temporal link prediction requires methods that use temporal order and can be evaluated fairly across multiple datasets and objectives. | Algorithmic framework and benchmark study. | The paper frames the prediction task, defines sequential stacking, reports broad benchmark comparisons, then places algorithm details, datasets and evaluation settings in Methods; Data, Code and Supplementary information are explicit. | Eight main figures. The figure sequence is benchmark-heavy: method/task schematic, dataset-level comparisons, parameter/sequence-length sensitivity, run-time or scaling evidence and additional predictive settings. | Many datasets, many baselines, explicit train-test/evaluation protocol, code availability and data pointers. | Comparator rows in the current manuscript must remain target-aligned. They should be framed as operator-recovery stress tests after projection, not as native temporal-link-prediction or temporal-GNN rankings. Serves rigour / reproducibility / clarity. |
| Murphy, Laurence and Allard 2021 | Contagion dynamics on complex networks are expensive or difficult to emulate across settings without a learned dynamical surrogate that respects network structure. | Deep-learning computational framework for network dynamics. | The article introduces the computational challenge, defines the graph neural network surrogate, validates it on epidemic/spreading dynamics, reports transfer and scalability settings, then gives Methods plus Data and Code availability. | Six main figures. The sequence combines architecture/schematic panels, validation against simulated dynamics, transfer/generalization tests and scaling or real-network settings. | Controlled simulation tasks, explicit process definitions, comparison against dynamical baselines, generalization tests, data/code statements. | Transfer claims need task-matched evidence. The current manuscript should keep NYC as same-operator execution outside trade; broad transfer across nonlinear dynamics would require separate validation. Serves generality / rigour. |

PDF-verified cross-paper lessons:

1. The strongest computational papers name the reusable object or task before showing empirical domains. For this manuscript, the reusable object is the topology-indexed response operator and its endpoint-preservation contract. Tags: novelty / clarity.
2. Main figures typically start with a schematic or task figure, then move to validation, benchmarks and empirical demonstrations. The current Fig. 1 -> Fig. 2 -> Fig. 3 -> Fig. 4 order matches this pattern. Tags: visual communication / rigour.
3. Benchmark-heavy papers make evaluation protocol and comparator scope visible. The current manuscript should keep endpoint availability and target alignment before accuracy rankings. Tags: rigour / reproducibility.
4. Generality claims are earned through matched tasks or multiple systems. NYC supports same-operator execution outside trade; it does not support broad temporal-network generalization. Tags: generality / clarity.
5. Trust-building is procedural as much as numerical: Methods, Supplementary, Data availability and Code availability are part of the argument. The current derived-evidence rebuild and raw-source boundary should remain explicit. Tags: reproducibility / rigour.

Stage 1 next most valuable modification:

- Keep the current Fig. 1 -> Fig. 2 -> Fig. 3 -> Fig. 4 sequence and avoid adding a domain-first empirical figure before the operator and endpoint gate. The reference articles lead with the computational object or task; this manuscript should keep the topology-switchable operator in that role. Tags: novelty / visual communication / clarity.

## Stage 2: Common Nature/NCS Pattern For This Manuscript Class

Common structural pattern:

1. State a computationally necessary representation problem, not only a domain problem.
2. Define the object or algorithm that makes the desired query possible.
3. Establish what the object preserves or predicts before ranking numerical performance.
4. Use controlled benchmarks to separate target availability from target accuracy.
5. Use empirical systems as demonstrations of what the object returns, with boundaries.
6. Put broad diagnostics, sensitivity grids and implementation details in Supplementary.
7. Make code/data availability visible and specific.

Title pattern:

- Strong titles identify the object and domain class.
- Avoid "based on CP tensor decomposition" as the headline because CP is implementation, not the contribution.
- Current title, "Topology-switchable response operators for evolving weighted networks", follows the stronger pattern.

Abstract pattern:

- Background: why the network class matters.
- Computational gap: what query is unavailable under existing representations.
- Approach: define the object.
- Evidence: benchmark recovery and endpoint availability.
- Empirical readout: bounded, not overclaimed.
- Boundary: causal effects, topology formation and broad generality require separate designs.

Figure sequence pattern:

- Fig. 1: object and query.
- Fig. 2: validation and endpoint gate.
- Fig. 3: main empirical readout with uncertainty boundary.
- Fig. 4: second-domain operator check or move to Supplementary if space is tight.

Methods/Results split:

- Results should tell readers what the object makes possible and what evidence supports it.
- Methods should carry estimator details, hyperparameters, stability, weak separation, uncertainty and reproducibility.
- Supplementary should carry comparator fairness, full benchmark grids, robustness, perturbations and raw-data constraints.

Language pattern:

- Prefer "defines", "preserves", "evaluates", "reports", "bounds" and "tests".
- Avoid "reveals mechanism", "generalizes broadly", "policy-effect identification", "universal", "state-of-the-art" unless supported by matching evidence.

Stage 2 next most valuable modification:

- Preserve the Methods/Supplementary split as an explicit trust-building device: main Methods should state the estimator, tuning, uncertainty and stability regime; Supplementary should retain full comparator grids, projection rules, diagnostics and raw-source boundaries. This mirrors the reference-article pattern without requiring new experiments. Tags: rigour / reproducibility / clarity.

## Stage 3: Current Manuscript Diagnosis

Current NCS fit:

- Stronger than a results-reporting manuscript because the central contribution is now query preservation.
- The manuscript is a methods/object paper with bounded empirical readouts.
- The main editorial risk is whether the operator-level contribution appears broad enough for Nature Computational Science.

Current main claim:

- A topology-indexed finite-horizon operator, `M_{k,t}(W)=A_{k,t}+B_{k,t}W`, preserves observed-topology, direct-only and frozen-topology readouts from one reconstructed coefficient path.

Evidence chain:

- Fig. 1 defines the object and the tested collapsed-map target boundary.
- Fig. 2/Table 1 test endpoint availability and recovery.
- Fig. 3/Table 2 apply the object to RCEP with estimation-path boundary.
- Fig. 4 applies the same readouts to NYC Taxi as a public second-domain operator check.
- Scope and integrity checks pass in the current generated package.

First-impression issues now mostly controlled:

- The abstract remains within the NCS Article target of 150 words or fewer.
- Main display items are 4 figures and 2 tables, within the NCS Article target.
- RCEP is bounded as descriptive topology-sensitive measurement.
- NYC is bounded as same-operator execution, not broad empirical generality.

Residual risks:

- Theoretical support is deterministic finite-horizon perturbation, not CP-ALS asymptotics.
- Raw-to-derived reproducibility depends on third-party raw-data access and helper checkouts.
- Projected graph-feature rows may still be challenged as non-native comparator evaluations.
- Fine-grained pair-level recovery remains fragile and should stay secondary.

Stage 3 next most valuable modification:

- Add no stronger claim until the external gates close. The safest local improvement is to keep pair-level and graph-feature evidence secondary and make every future edit pass the same claim-evidence boundary: endpoint availability first, replicated N=15/N=30 operator/GIRF recovery second, empirical readouts third. Tags: rigour / clarity / generality.

## Stage 4: NCS Optimization Plan

Core positioning:

- Claim: topology substitution is an endpoint-preservation problem for reconstructed dynamic-network operators.
- Contribution: query preservation.
- Implementation: CP-network reconstruction is the tested implementation layer.
- Boundary: the paper does not claim policy-effect identification, latent-network recovery, exhaustive forecasting superiority, or universal domain generality.

Abstract move:

1. Background: evolving weighted networks motivate fixed-shock, fixed-horizon topology-substitution questions.
2. Computational gap: a collapsed map alone does not identify the query over unrestricted blocks; a structured inverse requires its own explicit conditions.
3. Approach: define topology-switchable response operator.
4. Evidence: controlled benchmark gains and collapsed-map endpoint loss.
5. Empirical readout: RCEP and NYC illustrate bounded operator outputs.
6. Boundary: raw-to-derived and causal/generality constraints.

Introduction last two paragraphs:

- Paragraph 1 should define the query loss caused by collapsed reconstruction.
- Paragraph 2 should state the object, evidence sequence and excluded claims.
- Avoid starting with CP or tensor rank.

Results organization:

- Results 1: object and endpoint availability.
- Results 2: benchmark recovery under endpoint contract.
- Results 3: RCEP operator readout and uncertainty boundary.
- Results 4: public second-domain operator check.

Figure plan:

- Fig. 1: schematic-led composite. Panels should answer: what is stored; how topology is switched; why the tested collapsed object lacks a declared switch endpoint. Serves novelty / rigour / clarity / visual communication.
- Fig. 2: quantitative grid. Panels should answer: which endpoints are defined; how recovery performs; where stability bounds apply. Serves rigour / visual communication.
- Fig. 3: empirical readout. Panels should answer: fixed-path coefficient contrast; aggregate observed-minus-frozen propagation; GIRF channel decomposition. Serves significance / rigour.
- Fig. 4: second-domain operator check. Panels should answer: whether same readouts compute; whether contrast is near null; whether GIRF channel decomposition remains available. Serves generality / reproducibility.

Methods optimization:

- Main Methods: data construction, estimator, propagation definitions, uncertainty/stability, code/data statements.
- Supplementary: hyperparameters, comparator contracts, full benchmark grids, perturbations, diagnostics, cleanroom reproduction.
- Code/Data availability: state derived-evidence rebuild, raw-source restrictions and helper dependencies.

Discussion optimization:

- Open with "The contribution is query preservation."
- Connect to temporal-network representation choices, dynamic communities, memory, prediction and contagion as examples of computational objects defining what can be measured.
- State the transferable criterion: a model class must preserve a separable direct/network response operator and an evaluable topology argument.
- End with bounded implication, not a broad application claim.

Stage 4 next most valuable modification:

- If space or editor-facing wording must be tightened, revise only the portal and cover-letter summaries, not the manuscript evidence hierarchy. The needed message is: representation-level NCS contribution; CP as implementation; RCEP/NYC as bounded readouts; derived-evidence reproducibility with raw-source constraints. Tags: novelty / significance / reproducibility / clarity.

## Stage 5: Wording Bank

Computational gap:

- "A collapsed dynamic map alone does not supply topology-substitution endpoints; recovery requires an identified inverse to admissible separated blocks."
- "The missing object is not another smoothed coefficient path; it is a fitted path whose topology argument remains evaluable."

Methodological contribution:

- "We formulate topology substitution as an endpoint-preservation problem for reconstructed dynamic-network operators."
- "The contribution is query preservation: the same fitted path supports observed-topology, direct-only and benchmark-topology readouts."

Algorithmic novelty:

- "The CP layer is used to regularize the coefficient path while preserving the direct/network split required by the response operator."
- "Comparator rows are evaluated only where their fitted objects define the same endpoint."

Empirical finding:

- "In RCEP, the fixed-path readout differs under observed and frozen topology, while the re-estimated coefficient-difference interval crosses zero."
- "In NYC Taxi, the same readout is computable and returns a near-null aggregate topology contrast on a stable retained-date path."

Comparative advantage:

- "The benchmark first tests endpoint availability, then compares numerical recovery within the declared target."
- "Collapsed-map smoothing can retain total responses while losing network-component and frozen-topology endpoints."

Robustness:

- "The stability and weak-separation diagnostics define the regime in which finite-horizon readouts are interpretable."
- "Topology perturbations are operator diagnostics, not causal topology experiments."

Generality:

- "The public second-domain panel tests same-operator execution outside trade; broad domain generality requires additional designs."
- "The transferable criterion is object-level: the model must retain an evaluable topology argument."

Interpretability:

- "Direct and network-mediated blocks remain separately readable after reconstruction."
- "Channel-specific GIRF decompositions report how response mass is allocated across direct and network pathways."

Reproducibility:

- "The reviewer archive rebuilds manuscript-facing evidence from derived evidence objects under documented environment snapshots."
- "Raw-to-derived rebuilds depend on third-party source access and documented helper checkouts."

Limitation:

- "The current theory is deterministic and finite-horizon; CP-ALS asymptotic distribution theory is outside the present contribution."
- "The empirical readouts are conditional on supplied exposure matrices and do not identify topology formation or policy-effect claims."

Stage 5 next most valuable modification:

- Use the wording bank as a replacement filter during portal entry and co-author edits. Replace any new phrase that implies causal RCEP effects, native graph-learning superiority, broad cross-domain generality or fully public raw-data availability with the bounded alternatives above. Tags: rigour / clarity / reproducibility.

## Stage 6: Iterative Reviewer Re-check

NCS senior editor:

- First impression: the manuscript now has a defensible computational object and a clean editorial pitch.
- Likely concern: query preservation may be viewed as too narrow unless the paper keeps the transferable criterion prominent.
- Evidence to strengthen: one concise paragraph that places the object beside temporal-network representation, prediction and contagion frameworks.
- Risk: desk rejection if read as CP tensor applied to trade.
- Key revision: make "CP is implementation; query preservation is the contribution" visible in abstract, introduction, cover letter and Fig. 1.

Computational methods reviewer:

- First impression: the endpoint gate and comparator contract are the strongest methodological defense.
- Likely concern: projection-based graph-feature rows are not native temporal-GNN comparisons.
- Evidence to strengthen: fairness audit and target-alignment table.
- Risk: major revision if comparator scope is overstated.
- Key revision: keep graph-feature rows labelled as projected operator-recovery stress tests.

Temporal/complex networks expert:

- First impression: the paper now speaks to representation-dependent measurement in evolving networks.
- Likely concern: topology diagnostics could be mistaken for structural mechanism.
- Evidence to strengthen: keep diagnostics descriptive, report perturbations as operator diagnostics, and avoid mechanism language.
- Risk: major revision if RCEP is interpreted as causal policy/topology evidence.
- Key revision: keep RCEP as fixed-path topology-sensitive measurement and NYC as public second-domain operator check.

Stage 6 next most valuable modification:

- Prepare a short response-ready paragraph for each likely reviewer concern before submission: editor fit, comparator scope, RCEP boundary, raw-source boundary and Fig. 2 readability. The manuscript should not be changed unless a paragraph exposes a real claim-evidence mismatch. Tags: novelty / rigour / reproducibility / visual communication.

## Next Most Valuable Modification

The next highest-value modification now depends on external submission information. If the journal portal preview keeps Fig. 2 panel a readable or lets reviewers inspect the standalone PDF/SVG, keep the current figure. If the preview rasterizes Fig. 2 poorly or blocks source inspection, redraw Fig. 2 using the controlled redesign contract. In parallel, finalize the raw-source access worksheet so the Data availability statement can remain precise about submitted-evidence regeneration versus restricted raw-to-derived rebuilding.
