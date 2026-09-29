# Nature / Nature Computational Science Recent Re-check

**Date:** 2026-07-18  
**Purpose:** Re-check the current NCS positioning against recent Nature Computational Science (NCS) and Nature Communications work before the next manuscript revision.  
**Scope:** literature and manuscript strategy only. No R006e/R006f outcome phase was opened, and no scientific result was generated in this re-check.

## 1. Access boundary

The search used Crossref metadata and publisher HTML pages, together with the validated local PDFs already present in `tmp/pdfs/nature_recent_text/`. The evidence status is deliberately separated:

| Status | Meaning |
| --- | --- |
| `full_text_verified` | Publisher PDF or open-access HTML was downloaded, parsed and inspected for the relevant sections/figures. |
| `abstract_preview` | Publisher abstract and availability sections were inspected, but the full article body/figure sequence was not available in the current access path. |
| `metadata_only` | Bibliographic metadata only; not used for detailed method or evidence claims. |

This memo does not infer peer-review history, hidden code, or journal priority from titles. A recent article is used as a structural or evidential analogue, not as proof that the current contribution is absent from the literature.

## 2. Recent NCS papers most informative for this manuscript

| Article | Evidence status | What the paper makes computationally explicit | Evidence pattern relevant to us | Transferable lesson / boundary |
| --- | --- | --- | --- | --- |
| Yin et al., “A scalable framework for learning the geometry-dependent solution operators of partial differential equations”, **Nature Computational Science** 4, 928–940 (2024), DOI `10.1038/s43588-024-00732-2` | `full_text_verified` | A geometry-dependent solution operator is treated as the object of learning. The method transports inputs and outputs to a reference domain and exposes geometry as an operator argument. | Three settings (Laplace, reaction–diffusion, patient-specific cardiac propagation); held-out geometries; absolute/relative errors; cross-validation; inference-time and memory/scaling analysis; explicit limitations and code/data statements. | This is the closest structural analogue to a topology-indexed response operator. Our manuscript should make the supplied topology an explicit argument of the fitted object and test unseen topologies, not merely show that a response can be calculated on one path. The PDE operator-learning claim must not be borrowed as a claim of neural-operator novelty.
| Milisav et al., “A simulated annealing algorithm for randomizing weighted networks”, **Nature Computational Science** 5, 48–64 (2025), DOI `10.1038/s43588-024-00735-z` | `full_text_verified` | A weighted-network null model preserves a declared strength sequence and network constraints, rather than silently changing the object being compared. | Three algorithms; 10,000 null networks per empirical brain network; strength sequence/distribution diagnostics; morphospace variability; directed/signed and diverse real-network tests; statistical comparisons; alternative objectives/schedules and computational-cost analysis; open data/code. | The transferable pattern is a declared preservation contract followed by stress, null, variability and cost diagnostics. For us, “query preservation” must be a measurable contract with an explicit negative control and a reported abstention/stability boundary, not a qualitative slogan.
| Cappelletti et al., “GRAPE for fast and scalable graph processing and random-walk-based embedding”, **Nature Computational Science** 3, 552–568 (2023), DOI `10.1038/s43588-023-00465-8` | `full_text_verified` | A software/resource contribution is justified by a reusable interface, large-scale implementation and fair evaluation infrastructure. | Standardized interfaces; modular pipelines; >80,000 graphs; comparison with multiple libraries; time/memory complexity; node/edge prediction and resource availability. | This sets the NCS reproducibility/resource bar. Our current paper should not imitate the scale claim, but must expose a clean query contract, fixed comparator target, source data and runnable audit path. A package/manifest description alone is not a scientific contribution.
| Yu et al., “Discovering network dynamics with neural symbolic regression”, **Nature Computational Science** 6, 156–168 (2026), DOI `10.1038/s43588-025-00893-8` | `abstract_preview` (publisher HTML preview; full article body not available in the current path) | Automated equation discovery for high-dimensional network dynamics; the abstract reports ten benchmark systems, two empirical systems, and epidemic transmission over mobility networks of different scales. | The abstract reports recovery of forms/parameters, empirical prediction-error reductions of 59.98% and 55.94%, multiscale epidemic analysis, plus GitHub/Zenodo data and code and source-data files. Figure order and detailed baseline protocol were not independently checked here. | This is a direct novelty warning: “learning network dynamics from observations”, “interpretable network dynamics” and broad epidemic application are already occupied. Our novelty must be the representation/query-preservation contract and its identifiability boundary, not equation discovery or generic network-dynamics learning. The reported transfer across scales also raises the generality bar.
| Yang et al., “Transferable human mobility network reconstruction with neuroGravity”, **Nature Computational Science** 6, 630–641 (2026), DOI `10.1038/s43588-026-01003-y` | `abstract_preview` (publisher HTML preview) | Mobility-network reconstruction is framed as transfer to unobserved cities, with a learned transferability predictor. | The abstract reports transfer to unobserved cities, a segregation-based transferability index and proxies for more than 1,200 cities; publisher page exposes source-data files and code/data availability. Full figure sequence and exact split/baseline details were not independently checked here. | A second-domain near-null or computability check is far below this paper’s transferability standard. Our NYC panel can remain a bounded operator readout, but cannot be called cross-domain generality unless a pre-specified held-out topology-family test is added and passes.
| Feng et al., “Reliable deep learning in anomalous diffusion against out-of-distribution dynamics”, **Nature Computational Science** 4, 761–772 (2024), DOI `10.1038/s43588-024-00703-7` | `abstract_preview` (publisher HTML preview; correction noted on publisher page) | Reliability is defined as performance under out-of-distribution dynamics, not only in-distribution accuracy. | A general OOD evaluation framework, a baseline, multiple experimentally diverse systems, Code Ocean reproduction package and source data; the publisher page records a correction. | The relevant lesson is to make a failure boundary part of the method. Our native endpoint-aware failure should be promoted as a designed boundary condition, with no language that turns the controlled benchmark into broad recovery.

## 3. Recent Nature Communications near-neighbours

| Article | Evidence status | Direct relevance | What it changes in our novelty claim |
| --- | --- | --- | --- |
| Delabays et al., “Hypergraph reconstruction from dynamics”, **Nature Communications** 16, 2691 (2025), DOI `10.1038/s41467-025-57664-2` | `full_text_verified` (open-access HTML) | Inverse reconstruction from time series. The paper first asks when reconstruction is possible, identifies ambiguity when higher-order interactions are decomposable or observations are locally linearized, then proposes SINDy-based reconstruction and validates on Kuramoto/Lorenz simulations and resting-state EEG from 109 subjects. | This paper occupies the “reconstruction requires an identifiability condition plus a synthetic-to-empirical validation ladder” space. Our exact collapsed-map non-identifiability argument is promising, but should be stated as a formal response-query identifiability result, with the same care about excitation/local linearization. It is not valid to claim that CP reconstruction or network separation alone is novel.
| Hu et al., “Learning interpretable network dynamics via universal neural symbolic regression”, **Nature Communications** 16, 6226 (2025), DOI `10.1038/s41467-025-61575-7` | `full_text_verified` (open-access HTML) | High-dimensional network-dynamics discovery. The method explicitly separates self and interaction terms, accommodates incomplete state/topology masks, compares against symbolic-regression baselines across more than ten scenarios and reports real epidemic/pedestrian examples. | Direct/self versus network-mediated decomposition, incomplete topology handling and generic network-dynamics discovery are established. Our contribution must therefore be the post-reconstruction query contract: whether a supplied topology can still be inserted into one fixed fitted path, with endpoint availability separated from numerical recovery and causal interpretation.
| Peixoto & Rosvall (2017); Williams et al. (2022); Murphy et al. (2021); He et al. (2024) | `full_text_verified` in the existing local reference memo | Representation choice determines which temporal structures, memory, predictions or local dynamics remain measurable. | These papers support the representation principle, but none establishes the current topology-substitution endpoint contract. They should motivate the Introduction, not carry the novelty claim.

## 4. What the recent corpus says about the NCS bar

Across the verified NCS articles, the recurring pattern is:

1. **Name an irreducible computational object.** DIMON names a geometry-dependent solution operator; Milisav et al. name a strength-preserving weighted-network null; GRAPE names a reusable graph-processing/evaluation resource.
2. **Make the preservation or failure contract explicit.** The object is not judged by fit alone: geometry, strength sequence, memory/time or OOD dynamics are measured directly.
3. **Validate the native target before the application.** Held-out geometries, null ensembles, multi-network benchmarks or OOD settings precede the domain readout.
4. **Bind generality to an explicit split or family.** “Multiple examples” is not enough. The tested family, target availability, holdout rule and failure boundary are visible.
5. **Treat reproducibility as part of the method.** Source data, code, standardized interfaces or Code Ocean/Zenodo artifacts are stated at article level.

For this manuscript, the right analogue is therefore not “CP is better than rolling estimation.” It is:

> A reconstructed dynamic-network object either retains an evaluable supplied-topology argument, or it does not; if it does, native recovery and finite-horizon stability must be assessed under a declared design.

## 5. Updated judgment of the current manuscript

### What remains NCS-plausible

- The representation-level question is recognizable and computationally meaningful: a fitted trajectory can be useful while the fitted object no longer supports a topology-indexed response query.
- The separated operator `M_{k,t}(W)=A_{k,t}+B_{k,t}W` gives a concrete object whose query contract can be checked before propagation.
- The collapsed-map negative control and the distinction among endpoint definition, identification, recovery and stability are stronger than a conventional benchmark ranking.
- The existing conservative scope avoids claims of generic CP superiority, causal policy effects, native recovery or broad temporal-network coverage.

### What currently prevents a strong NCS submission

- **Native evidence is not yet a positive method result.** The frozen endpoint-aware gate reports CP `0/16` and Tucker `6/16`, with no Tucker native cells passing. This is a valuable boundary result, but it cannot support a reusable estimator claim.
- **The controlled benchmark still risks becoming the headline.** Recent NCS papers make the target/failure contract and native holdout visible before favorable performance rows.
- **The second-domain panels do not establish transferability.** A trade interval containing zero and a near-null mobility contrast demonstrate computability and bounded interpretation only.
- **Direct/network separation is not enough for novelty.** Hu et al. 2025 and the dynamic-network literature already use self/interaction decompositions; GVAR/network-VAR work already supports topology-weighted response analysis.
- **The current abstract is not submit-ready.** It contains unresolved `{{...}}` placeholders and a numerical advantage sentence that is not yet subordinate to the endpoint boundary.
- **Methods still contain too much archive/protocol language.** NCS readers need the operator contract, target, split, estimator, stability rule and reproducibility boundary; internal governance mechanics belong in data/code documentation.

**Bottom-line decision:** the manuscript can still be developed toward NCS as a representation/query-preservation Article, but it is not presently strong enough to claim a general estimator or broad network-dynamics advance. The safest current positioning is a computational criterion with a proved/constructed non-identifiability boundary and explicitly bounded fixed-path readouts. Do not broaden the claim until new authorized native evidence passes.

## 6. Required revision sequence

### Priority 1 — change the spine

Replace the benchmark-first spine with:

1. **Query contract:** define the topology-indexed response as an operator with supplied topology, fixed coefficient path, shock normalization and horizon.
2. **Information-loss result:** show exactly what the collapsed map retains and what it cannot answer without an identified inverse.
3. **Controlled recovery:** report the favorable separated-design benchmark only after the target and negative control are defined.
4. **Native boundary:** present the endpoint-aware failure as the primary generality/stopping result; do not hide it in Supplementary.
5. **Bounded readouts:** use trade and mobility as fixed-path computational examples with explicit non-causal/near-null boundaries.

### Priority 2 — add the missing theoretical sentence, not a stronger marketing sentence

Add a short proposition or boxed criterion in Results/Methods:

> A topology-substitution response is evaluable from a reconstructed path only if the fitted representation either stores the direct block, network-mediated block and topology action separately, or supplies an identified inverse that recovers them under the declared design. Evaluability does not imply identification, recovery or finite-horizon stability.

The proposition should be accompanied by the smallest exact collapsed-map counterexample already supported by the repository. Do not call it a universal impossibility theorem unless the assumptions are stated and proved.

### Priority 3 — make generality operational

Before any outcome phase is reopened, pre-specify:

- topology families and held-out endpoints;
- whether the held-out topology is native or projected;
- excitation/support diagnostics and abstention rule;
- native baselines and comparator target;
- uncertainty and stability reporting;
- the decision rule that prevents a favorable controlled row from rescuing a failed native row.

The current R006e governance keeps this work closed until explicit authorization and production trust evidence exist. The manuscript should state the boundary as a limitation, not imply that the unrun screen is evidence.

### Priority 4 — redraw figures around the object

- **Fig. 1:** supplied topology → fixed fitted path → observed/direct-only/frozen-topology responses; annotate what is stored and what is queried.
- **Fig. 2:** exact collapsed-map non-identifiability and endpoint availability; make the structural negative control visually dominant.
- **Fig. 3:** controlled recovery with native target, comparator target and stability mask shown in the same panels.
- **Fig. 4:** native endpoint-aware boundary; show passed/failed cells and abstention, not only error bars.
- **Applications:** keep as a bounded secondary figure or Supplementary unless a stable, non-null scientific consequence is obtained under an authorized design.

## 7. Reviewer simulation after this re-check

| Reviewer | Likely first impression | Most likely concern | Evidence needed | Main risk |
| --- | --- | --- | --- | --- |
| NCS senior editor | Clear representation question, but possibly a protocol rather than a method | Is query preservation sufficiently reusable and non-obvious for NCS? | Exact operator criterion, non-identifiability construction, at least one native held-out success or a sharply valuable impossibility/boundary result | Desk rejection if the paper reads as CP benchmarking plus two applications |
| Computational methods reviewer | Careful separation of endpoint, recovery and stability | Does the estimator recover a native supplied topology, and are comparisons target-matched? | Native split, fair baselines, support/excitation diagnostics, uncertainty, cost and reproducible pipeline | Major revision if controlled rows are presented as general recovery |
| Temporal/complex-networks expert | Representation-dependent response is relevant | Is this only standard GVAR/network-AR counterfactual propagation under new terminology? | Operation-level prior-art comparison and explicit distinction from standard topology-weight substitution | Major revision or rejection if topology effects are read causally or direct/network separation is claimed as new |

## 8. Next most valuable modification

Do not add more application prose or replace the abstract with stronger adjectives. The next modification with the highest expected NCS value is to rewrite the title, abstract and final Introduction paragraph around **representation/query preservation plus an explicit identifiability boundary**, then rebuild Fig. 1–4 to follow that claim. Any numerical placeholder must remain unresolved until the corresponding authorized evidence exists; if the abstract can be made complete without those numbers, remove the sentence rather than inventing them.

