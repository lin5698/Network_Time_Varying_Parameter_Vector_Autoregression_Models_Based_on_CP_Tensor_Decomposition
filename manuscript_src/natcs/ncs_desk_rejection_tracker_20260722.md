# NCS Desk-Rejection Revision Tracker

Date: 2026-07-22

Status: source-level revision record only. This is not an appeal, a response letter or a submission authorization. `PAPER_CLAIM_AUDIT=BLOCKED` and `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain controlling restrictions for empirical claims and all downstream manuscript builds.

## Editorial Signal

The editor's decision identifies a fit and contribution problem rather than a technical error: the manuscript was judged likely to interest specialists, but not to provide a sufficiently substantial practical or conceptual/methodological advance for an immediate broad computational-science readership. The decision does not invite revision or appeal. The transfer option is procedural information, not a positive assessment of the current evidence package.

## Comment-Action Tracker

| ID | Editor concern | Diagnosis | Action | Manuscript location | Status | Serves |
| --- | --- | --- | --- | --- | --- | --- |
| E.1 | The contribution is not yet a substantial conceptual or methodological advance. | The prior framing could be read as CP smoothing for one separable network VAR. | Reframe the contribution as a query-preservation audit: a pre-readout test of endpoint evaluability, design identification, recovery and stability. Define it as an ordered stopping rule, not a new label. Keep CP as an implementation layer. | Abstract; Introduction; Results framework; Results validation; Methods theory; Discussion | Text revision completed; broader methodological claim remains evidence-limited. | novelty / clarity / significance |
| E.2 | The work may not be of immediate interest beyond related experts. | The practical consequence of representation loss was implicit rather than explicit. | State that unavailable structural endpoints must be marked outside target before scenario analysis, rather than scored as zero or as a failed estimate. Make the rule explicit in Figure 1 and Figure 2 captions. | Abstract; Introduction; Results framework; Results validation; Figure 1/2 captions; Discussion | Text revision completed within the declared separable-operator scope. | significance / rigour / visual communication |
| E.3 | The empirical and benchmark evidence may not establish broad relevance. | The active evidence is a theorem, a controlled N=15/N=30 benchmark and an endpoint-aware qualification. E4-r3 adds a quarantined two-family, same-endpoint, held-out and uncertainty/stability grid, but its integrity verdict is `WARN` and both result-to-claim verdicts are `partial`. | Keep the method-led NCS route centred on the representation criterion. Activate E4 evidence only after the missing pre-registered metric/CI issue and E4-R008 claim-fidelity gate are resolved. Treat a public-network application as an optional significance amplifier rather than a compulsory section. | Abstract; Results validation; Discussion; `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` | E4-r3 executed and frozen; claim activation remains blocked. | rigour / generality / reproducibility |
| E.4 | Transfer to another journal is offered. | This is not a request to prepare an NCS revision. | Do not draft an appeal or transfer response from this letter. Select a future venue only after its scope and evidence requirements are assessed. | Submission materials, later | Deferred. | clarity |

## What Text Can Solve Now

1. Lead with a reusable computational failure mode: fitting an observed-topology trajectory does not establish that a fitted representation can answer a later topology-indexed query.
2. Define the reusable object as a query contract, not a CP decomposition or a trade application.
3. Make the practical rule visible in Figure 1 and the first Results paragraph: unavailable endpoints are outside target, not zero-valued or directly rankable errors.
4. Separate the four layers of the audit throughout the manuscript: evaluability, design identification, numerical recovery and finite-horizon stability.

## Post-revision Re-review

The source-only three-perspective re-review is recorded in [ncs_desk_rejection_rereview_20260722.md](ncs_desk_rejection_rereview_20260722.md). It found that the revised text made E.1 and E.2 more legible. Since that review, E4-r3 has produced quarantined synthetic evidence. The scoped integrity verdict is `WARN`, and the independent reviewer returned `partial` for both claims, so the E.3 activation gap remains open.

The E.3 design route is recorded in [NCS_E3_MINIMUM_EVIDENCE_PROTOCOL.md](../../refine-logs/NCS_E3_MINIMUM_EVIDENCE_PROTOCOL.md). Its E4-r3 execution is frozen under a scoped audit; neither the protocol nor that outcome authorizes manuscript promotion.

## What Requires New Evidence

The following are not satisfied by the current text and must not be implied as complete:

1. A theorem or empirical validation extending beyond separable direct/network response operators with supplied topology arguments.
2. Claim-ready same-endpoint comparisons with the pre-registered metric package complete.
3. Independently approved recovery across the pre-specified topology families, scales and held-out endpoints represented in E4-r3.
4. An uncertainty/stability claim whose wording is bound to the simulation-only, horizon and panel-count ceiling.
5. A scientifically consequential public-network application only if the paper elects to claim practical consequence rather than a method-led conceptual advance.

## Current Readiness

| Route | Readiness | Reason |
| --- | --- | --- |
| New Nature Computational Science submission | Blocked | E4-r3 is quarantined with integrity `WARN`; both result-to-claim verdicts are `partial`. The blocker is claim-ready methodological evidence, not the absence of an application by itself. |
| Appeal | Not indicated | The decision identifies editorial selectivity and fit, not a factual or procedural error. |
| Specialist-journal reframing | Possible after venue selection | The current theory and controlled benchmark can support a narrower, evidence-bounded methods contribution once venue-specific requirements are assessed. |

## Selected Long-Route Direction

The author has selected an evidence-led future NCS route rather than a
text-only resubmission. The source-only claim and figure activation conditions
are recorded in [ncs_e3_manuscript_activation_map.md](ncs_e3_manuscript_activation_map.md).
This records a research direction only: it does not authorize E3 execution,
RCEP/NYC inspection, R006e/R006f outcome, manuscript build, upload or claim
promotion. Until the map's activation gates and the controlling audits pass,
the NCS submission status in the table above remains `Blocked`.
