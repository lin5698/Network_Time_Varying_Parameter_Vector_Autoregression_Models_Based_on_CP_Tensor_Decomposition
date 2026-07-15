# NCS Editorial Writing Audit

**Date:** 2026-07-16  
**Scope:** title, abstract, Introduction, Results and Discussion  
**Decision:** `MAJOR REVISION AFTER EVIDENCE GATES`; manuscript remains frozen

## 1. Editorial Diagnosis

The supplied Nature Computational Science guidance is consistent with the desk decision. The paper's reader-facing problem is not merely style. Its title and abstract make a technical object visible, but the current evidence does not yet establish the broad practical or methodological advance expected by the journal. Clearer prose can improve first-screen access; it cannot substitute for native recovery, fair contemporary comparisons, statistical confirmation or a consequential application.

The current narrative should therefore be revised in evidence order:

1. establish supported-endpoint recovery and the support theorem;
2. decide the defensible contribution level;
3. select the title;
4. write the Abstract from the final evidence;
5. revise the Introduction preview, Results hierarchy and Discussion implication.

## 2. Title Audit

Current title:

> Topology-switchable response operators for evolving weighted networks

The title contains three stacked technical noun phrases: `topology-switchable`, `response operators` and `evolving weighted networks`. It is precise for specialists but asks a broad reader to decode the method before learning the scientific operation. `Topology-switchable` is also a manuscript-specific label rather than a likely search term.

### Title route if supported-endpoint recovery passes

Preferred:

> Preserving topology-dependent responses after smoothing evolving networks

Alternatives:

- Measuring network responses under changing topology
- Network responses that remain evaluable as topology changes

The preferred title names the operation, the failure point and the domain without an acronym or bespoke method name. It is only eligible if Track A validates recovery, not only endpoint availability.

### Title route if the estimator gate fails

Preferred:

> When reconstructed network models retain topology-dependent responses

Alternative:

- Identifying topology-dependent responses after network-model reconstruction

This route makes a representation/identifiability contribution and avoids implying a successful broadly useful estimator.

## 3. Abstract Audit

The current Abstract has the correct broad move order but contains four first-screen problems:

1. `collapsed map`, `endpoint preservation`, `topology-switchable response operator` and `supplied exposure matrix` arrive before a plain-language explanation.
2. The long scope exclusion appears before the main result and interrupts the problem-to-solution progression.
3. The benchmark sentence is the only quantitative result, while practical use is represented by one positive-but-uncertain trade readout and a near-null mobility contrast.
4. The final sentence describes derived objects and raw-source access. It leaves the reader with package mechanics rather than scientific meaning.

The final sentence about the evidence workflow must be removed from the Abstract. Reproducibility belongs in Data availability, Code availability and a neutral Supplementary Methods section.

### Post-gate abstract architecture

Use 130-160 words and no more than seven sentences:

1. **Problem:** models of evolving networks are smoothed for stability, but smoothing can remove the separation needed to compare propagation under another network.
2. **Gap:** existing fitted representations do not automatically retain every alternative-topology response query.
3. **Solution:** define a representation that keeps direct dynamics, network-mediated dynamics and the supplied network separately evaluable, plus an availability/support test.
4. **Primary result:** insert the unchanged Track A confirmation effect, interval and supported endpoint scope.
5. **Ablation:** state that a collapsed representation retained total responses but did not define the alternative-topology endpoint.
6. **Application:** report only the strongest empirically defensible consequence; do not promote a near-null portability check as practical impact.
7. **Meaning:** explain that the framework separates whether a network-response question is computable from whether it is statistically recoverable.

Do not insert Track A values, `alpha_tau` performance claims or abstention language until their protocols pass. Keep at most one boundary clause in the Abstract and move the complete exclusion list to Discussion.

## 4. Introduction Audit

The Introduction already follows an hourglass structure and identifies the representation problem. Its main weakness is the last paragraph. It previews benchmark components and applications, then ends with a long list of excluded mechanisms. The reader reaches Results remembering what the paper does not claim rather than what it found and why the result matters.

Required post-gate revision:

- paragraph 1: retain the plain scientific operation, but reduce `query`, `matched topology` and inverse terminology;
- paragraph 2: connect representation choice to a recognizable computational consequence, not only four literature categories;
- paragraph 3: state why existing smoothing targets do not guarantee the requested readout and explain the exact difference from close network-VAR/GVAR work;
- paragraph 4: preview the method, strongest confirmed result and practical meaning; move the full non-claim inventory to Discussion.

The recent Nature-family literature review must be converted into selective contextualization, not a citation list. The Introduction should answer: why a new tool is needed, what operation it makes possible, and what evidence shows that the operation works.

## 5. Results Audit

The current order is defensible: object definition, benchmark validation, RCEP readout and second-domain check. Comparator rationale is also stated. The main risks are evidential:

- the CP headline rests on earlier N=15/N=30 benchmarks, while corrected R006c found CP `0/16` and native Tucker `0/8` in the harder endpoint-aware gate;
- local stress anchors use only three replications and N=50 remains a bounded stress output;
- benchmark improvements are not accompanied by a confirmatory paired uncertainty statement in the main text;
- projected graph-feature comparisons are correctly moved to Supplementary, but native temporal graph baselines remain absent;
- RCEP re-estimation uncertainty crosses zero and NYC is near-null, so neither currently supplies a strong practical consequence.

No wording change can resolve these points. Track A must determine the main estimator, paired confirmation and cross-family endpoint evidence. Track B must validate support classification separately. Only the minimum method detail needed to interpret each result should remain in Results; optimizer, rank, split and construction details belong in Methods.

## 6. Discussion Audit

The Discussion contains broader interpretation and limitations, so its architecture is stronger than the Abstract's. It nevertheless remains inward-facing: `query preservation`, `reconstruction contract`, block exposure and stability diagnostics dominate the practical implication.

The revised Discussion should:

- open with the confirmed scientific finding rather than restating the operator definition;
- distinguish endpoint availability, exact support, statistical recoverability and finite-horizon stability;
- explain where the result changes practice for analysts using evolving network models;
- state the native-recovery, scale, uncertainty, topology-endogeneity and application boundaries once, without repeating them across paragraphs;
- identify concrete future opportunities only after the corresponding failure modes are documented.

If the empirical application remains near-null or descriptive, state that transparently and route the paper as a methods/measurement contribution rather than implying broad practical impact.

## 7. Four Reviewer-Risk Classes

| NCS risk class | Current status | Binding issue | Required evidence or revision |
| --- | --- | --- | --- |
| Comparisons and validation | `RED` | Corrected native recovery fails; native graph baselines and confirmatory inference are absent. | Track A pass, paired confirmation, fair comparator rationale, then scale/native baselines. |
| Context of the work | `AMBER` | Representation gap is clear, but the closest prior methods are not yet contrasted at operation level in the manuscript. | Integrate verified close literature and state the incremental contribution without first/universal claims. |
| Practical usefulness | `RED` | RCEP is descriptive with a re-estimation interval crossing zero; NYC is near-null. | A stable consequential application or a deliberately bounded measurement-method claim. |
| Overall clarity | `AMBER` | Technical title, jargon-heavy Abstract, repeated scope clauses and package mechanics in reader-facing prose. | Evidence-matched title, mini-paper Abstract, shorter section endings and removal of internal package language. |

## 8. Internal Package Language

The following reader-facing source locations still contain archive/rebuild/reviewer mechanics and must be cleaned before the next submission build:

- `abstract.md`: final evidence-workflow sentence;
- `methods_data.md`: archive and raw-to-derived contract paragraph;
- `methods_estimator.md`: default reviewer reproduction path;
- `methods_uncertainty.md`: archive manifest and reproduction commands;
- `supp_note7_repro.md`: repeated `reviewer substitute`, peer-review package, archive and future repository wording.

Supplementary Information may report data provenance, access constraints, software versions and reproducible procedures. It should not narrate the internal reviewer archive, build system, manifest mechanics or author-side repository workflow. Operational details can remain in a separate README shipped with code.

## 9. Revision Sequence

1. Keep the manuscript frozen while Track A and Track B protocols are drafted and audited.
2. Remove internal package language in one controlled reader-facing cleanup after the evidence route is fixed.
3. Choose the title route from the actual estimator decision.
4. Draft the Abstract last, using only confirmed values and one concise scope sentence.
5. Reorder the final Introduction paragraph around findings and significance.
6. Move technical benchmark and optimizer detail to Methods/Supplementary while preserving comparator rationale.
7. Run a final claim-to-evidence and sentence-length audit before rebuilding submission files.

This sequence follows the editorial reminder that title and abstract improve access but do not determine scientific merit. The current priority remains evidence, followed by evidence-matched communication.
