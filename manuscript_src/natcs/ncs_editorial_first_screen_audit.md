# NCS Editorial First-Screen Audit

Purpose: audit what a Nature Computational Science editor sees before reading the full manuscript. This is a submission-support artifact for title, abstract, cover-letter and portal-field checks. It is not manuscript text and adds no new evidence.

> **Current-status refresh, 2026-08-26.** `PAPER_CLAIM_AUDIT.json` (reason code
> `rcep_nyc_value_audited_no_active_stale_citations`) and
> `EMPIRICAL_IMPLEMENTATION_AUDIT.json` (reason code
> `rcep_nyc_value_audited_downstream_build_authorized`) both record PASS dated
> 2026-08-26, superseding the 2026-07-23 historical banner. This audit is
> reactivated as the current first-screen review under author backlog
> authorization (item A); its rows are re-checked against the active title,
> abstract and cover-letter sources. Submission-readiness actions stay sequenced
> behind RC-1 promotion authorization (NOT_GRANTED), RC-2 activation clearance
> (RCEP F1/F2/F3 plus NYC characterization flags), the Fig. 2 portal-preview
> gate and the outstanding author sign-off worksheets.

Audit date: 2026-07-07. Recheck refresh: 2026-08-26 under author backlog authorization (item A).

Scope anchor: Nature Computational Science publishes fundamental and applied work built around computational techniques, mathematical models, algorithms, tools, frameworks and novel computational uses for difficult scientific problems. The current first screen should lead with the reusable computational object, then show bounded evidence and reproducibility.

Serves: novelty / significance / rigour / clarity / generality / reproducibility / visual communication.

## 1. Title Signal

Current title: "Query-certified operator learning for topology-indexed responses" (64 characters, settled in `metadata.json`).

First-screen read:

| Screen question | Current signal | Risk | Keep or revise | Tags |
| --- | --- | --- | --- | --- |
| Does the title name a computational object? | Yes: "query-certified operator learning" names the certified object and "topology-indexed responses" names the question class. | Low. | Keep the certification and query pairing. | novelty / clarity |
| Does it overlead with implementation or application terms? | No. Canonical-polyadic implementation vocabulary and trade-application wording stay out of the title. | Low. | Keep implementation and application wording out of headline position. | novelty / significance |
| Does it imply universal temporal-network scope? | No. Scope stays bounded by the response question class. | Moderate if readers assume all temporal-network models. | Keep limitations in abstract and cover letter. | generality / clarity |

Title checks: the settled title satisfies the 75-character Nature-style ceiling, foregrounds the topology-indexed response question, keeps forbidden implementation/application terms out of first screen and matches `metadata.json`.

## 2. Abstract Sentence-Function Audit

Current abstract is a single paragraph of eight sentences carrying context, gap, object, criterion, boundary, bounded evidence and implication.

| Sentence | Function | What it achieves | First-screen risk | Required action | Tags |
| --- | --- | --- | --- | --- | --- |
| 1 | Context and use case. | Establishes evolving networks and computations reaching beyond observed-data fit. | Low. | Keep. | significance / clarity |
| 2 | Computational gap. | States that compression can remove inputs such computations require even when predictive fit under observed conditions survives. | Low to moderate. | Keep the gap ahead of the method reveal. | novelty / rigour / clarity |
| 3 | Approach and object. | Introduces query-certified operator learning and makes query preservation a checkable property of the fitted object. | Strong. | Keep the fitted-object framing verbatim. | novelty / rigour |
| 4 | Criterion scope. | Derives an exact kernel criterion for row-separable finite-basis operators on topology-indexed dynamics. | Low. | Keep tied to the stated basis classes. | novelty / clarity |
| 5 | Boundary and coverage. | Gives the exact unrestricted-block boundary and structured diagonal inverse and identifies unsupported readouts before numerical scoring. | Strong guardrail. | Keep boundary language before numerical claims. | rigour / clarity |
| 6 | Operator evidence. | Reports median effective-operator error cuts across 20 replications at N = 15 and N = 30 via build-time gain placeholders. | Low to moderate; placeholders resolve at build from the benchmark summary. | Keep numbers tied to replicated controlled rows in all related texts. | rigour / generality |
| 7 | Response evidence. | Reports median finite-horizon unit-shock response error reductions relative to unrestricted local rolling. | Low. | Keep the comparator explicit. | rigour / clarity |
| 8 | Implication. | Positions query certification as an explicit target of representation design with retained objects shipping a statement of preserved computations. | Strong closing guardrail. | Keep as the final sentence. | significance / clarity |

First-screen verdict: the abstract reads as a methods/object abstract. It passes the context -> computational gap -> approach -> criterion -> boundary -> evidence -> implication structure. The main residual risk lies in keeping Fig. 2 readable enough to carry the endpoint-availability gate.

## 3. Cover-Letter Opening Audit

Audited text: title line plus the first two substantive paragraphs after salutation.

| Element | Current role | Pass/fail | Risk | Required action | Tags |
| --- | --- | --- | --- | --- | --- |
| Submission line | Names the Article and journal. | Pass. | Low. | Keep. | clarity |
| Paragraph 1 | Defines the topology-substitution query and topology-switchable operator. | Pass. | Low. | Keep the formula as plain text in DOCX exports. | novelty / clarity |
| Paragraph 1 final sentence | Names query preservation as the central contribution. | Pass. | Low. | Keep "central contribution" attached to query preservation. | novelty / significance |
| Paragraph 2 opening | Moves from object to benchmark evidence. | Pass. | Moderate; a quick reader could still focus on CP. | Keep "CP is the implementation layer" in this paragraph. | novelty / rigour |
| Paragraph 2 comparator scope | Declares collapsed-map, Tucker and projected graph-feature roles. | Pass. | Moderate; native graph-learning readers may challenge scope. | Keep fairness-audit pointer to Supplementary Table 1d. | rigour / clarity |
| NCS fit paragraph | States that the fit is representation-level and links temporal-network representation choices to response analysis. | Pass. | Low to moderate; it must not become a generic journal-fit claim. | Keep the fitted-object/query-preservation logic ahead of empirical domains. | novelty / significance / clarity |

First-screen verdict: the cover letter has the right order: object, evidence, empirical boundaries, reproducibility, NCS fit. The NCS fit paragraph now states the representation-level contribution directly. No change is required unless the portal asks for a shorter significance paragraph.

## 4. Portal Snippet Audit

Use these snippets only where the journal portal asks for short novelty, significance or editor-facing summaries. They are evidence-bound.

| Portal need | Current safe snippet | Evidence anchor | Avoid | Tags |
| --- | --- | --- | --- | --- |
| One-sentence novelty | This Article defines query preservation for topology-substitution responses in evolving weighted networks by keeping the topology argument evaluable after smoothing. | Abstract; Introduction; Fig. 1; Methods theory. | "A new CP tensor decomposition model for trade networks." | novelty / clarity |
| One-sentence significance | The work makes matched observed-topology, direct-only and frozen-topology response readouts computable from one reconstructed dynamic-network path. | Introduction; Fig. 1; Results framework. | "A general causal framework for network intervention." | significance / rigour |
| One-sentence evidence | Replicated N=15/N=30 benchmarks test endpoint availability and operator/GIRF recovery; RCEP and NYC panels demonstrate bounded same-operator readouts. | Abstract; Table 1; Figs. 2-4. | "The method is broadly validated across domains." | rigour / generality |
| One-sentence reproducibility | The reviewer package regenerates manuscript-facing evidence from derived objects, with raw-to-derived reconstruction documented under third-party access constraints. | Code availability; Data availability; cleanroom check. | "All raw data and code are publicly available." | reproducibility / clarity |
| One-sentence boundary | The claims concern conditional propagation under supplied topology matrices; policy-effect identification, topology formation and broad empirical generality require separate designs. | Abstract; Introduction; Discussion. | "The empirical panels identify network mechanisms." | rigour / clarity |

## 5. Desk-Reject Trigger Scan

| Trigger | First-screen status | Why it matters | Control action | Tags |
| --- | --- | --- | --- | --- |
| Application-first framing. | Controlled. Title, abstract and cover letter lead with the operator. | NCS editors may desk-reject a domain application with weak computational contribution. | Keep RCEP and NYC as empirical operator readouts. | novelty / significance |
| CP-as-novelty framing. | Controlled. CP appears as implementation and evidence layer. | CP alone may appear incremental. | Keep "query preservation" and the explicit topology-argument object before CP. | novelty / clarity |
| Forecasting or temporal-GNN competition framing. | Controlled with residual risk. | Methods reviewers may demand native forecasting benchmarks if the target is misread. | Keep projected graph-feature rows labelled as operator-recovery stress tests. | rigour / clarity |
| Causal policy or topology-formation framing. | Controlled. Abstract and cover letter exclude policy-effect identification and topology formation. | Domain reviewers may reject causal drift. | Keep RCEP wording as fixed-path descriptive readout. | rigour / significance |
| Broad generality claim. | Controlled. NYC is a public second-domain check. | One public second domain is not broad validation. | Avoid "broadly generalizes" and similar phrasing. | generality / clarity |
| Raw reproducibility overclaim. | Controlled but externally gated. | NCS expects code/data transparency. | Keep derived-evidence reproducibility claim and raw-source boundary. | reproducibility / rigour |
| Fig. 2 first-view unreadability. | Open external gate. | Fig. 2 carries the methods evidence chain. | Complete portal-preview checklist or redesign under the Fig. 2 contract. | visual communication / rigour |

## 6. First-Screen Claim-Evidence Boundary

| First-screen claim | Evidence visible nearby | Evidence strength | Boundary to preserve | Action before submission | Tags |
| --- | --- | --- | --- | --- | --- |
| Topology substitution can be made computable after smoothing by preserving the topology argument. | Abstract; Introduction; Fig. 1; Methods theory. | Strong. | Applies to separable direct/network response operators with supplied topology arguments. | Keep operator object in abstract and cover letter. | novelty / rigour |
| The collapsed-map ablation does not supply topology-substitution endpoints. | Fig. 1; Fig. 2; Methods theory; Supplementary Note 1. | Strong. | It estimates no inverse to separated blocks; this is not a universal impossibility claim for every structured model. | Keep "outside its target" and the structured-inverse exception together. | rigour / clarity |
| CP-network improves recovery in controlled benchmarks. | Abstract; Results validation; Table 1. | Strong for replicated N=15/N=30 rows. | Does not imply universal dominance or full native graph-learning superiority. | Keep exact metric, baseline and replication scope. | rigour / clarity |
| RCEP and NYC demonstrate operator readouts. | Cover letter; Figs. 3-4; Results sections. | Moderate to strong as bounded demonstrations. | They do not prove policy-effect identification or broad domain generality. | Keep empirical panels after benchmark evidence. | significance / generality |
| The package is reproducible from derived evidence. | Code/Data availability; cleanroom check; manifest. | Strong for derived-evidence layer. | Raw-to-derived rebuild depends on access and helper checkouts. | Keep conservative Data/Code wording until author sign-off. | reproducibility / rigour |

## 7. Recommended First-Screen Order

The current ordering should be preserved:

1. Title: query-certified operator learning for topology-indexed responses.
2. Abstract sentences 1-2: computations reaching beyond observed-data fit and the compression gap.
3. Abstract sentence 3: query-certified operator learning with query preservation as a checkable property of the fitted object.
4. Abstract sentence 4: exact kernel criterion for row-separable finite-basis operators.
5. Abstract sentence 5: unrestricted-block boundary, structured diagonal inverse and unsupported readouts before scoring.
6. Abstract sentences 6-7: replicated controlled operator and response evidence.
7. Abstract sentence 8: representation-design implication.
8. Cover letter paragraph 1: object and query preservation.
9. Cover letter paragraph 2: benchmark evidence and comparator contract.
10. Cover letter paragraph 3: empirical panels and non-causal boundary.
11. Cover letter paragraph 4: reproducibility.
12. Cover letter paragraph 5: NCS fit.

Do not move RCEP, NYC, CP rank, tariff details or topology-correlation diagnostics ahead of the operator and endpoint gate.

## 8. Minimal Pre-Submission Checks

| Check | Status | Blocking level | Needed material | Tags |
| --- | --- | --- | --- | --- |
| Title and abstract object-first. | Passed on visible source; title settled at 64 characters. | Low. | None; the title is settled. | novelty / clarity |
| Cover-letter first two paragraphs object-first. | Passed on visible source and DOCX formula extraction was previously checked. | Low. | Re-run final gate after any cover-letter edit. | clarity / reproducibility |
| Portal novelty/significance snippets evidence-bound. | Passed if snippets above are used. | Low. | None. | novelty / significance |
| Desk-reject trigger language absent from formal first screen. | Passed on visible source. | Medium after future edits. | Run final gate after edits. | rigour / clarity |
| Fig. 2 portal readability. | Not externally checked. | High visual gate. | Portal preview or screenshot using `ncs_fig2_portal_preview_checklist.md`. | visual communication / rigour |
| Raw-source and public-release statements. | Conservative. | Medium reproducibility gate. | Author sign-off worksheets before strengthening any claim. | reproducibility / rigour |

## 9. Recommended Author Decision

> **Recommendation refresh, 2026-08-26.** Downstream rebuild authorization is
> granted and both controlling audits hold PASS; submission-readiness actions
> stay sequenced behind the standing gates: RC-1 manuscript-promotion
> authorization (NOT_GRANTED), RC-2 empirical-claim activation clearance (RCEP
> F1/F2/F3 plus NYC characterization flags), the Fig. 2 portal-preview visual
> gate, and the raw-source access and public-release sign-off worksheets.
> Re-run `scripts/check_natcs_final_gates.mjs` after any edit to this screen set.

## Provenance

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
