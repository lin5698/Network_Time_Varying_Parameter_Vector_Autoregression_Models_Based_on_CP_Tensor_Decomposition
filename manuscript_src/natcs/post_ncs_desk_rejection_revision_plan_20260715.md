# Post-NCS Desk-Rejection Diagnosis and Revision Plan

Date: 2026-07-15

Status: diagnostic and planning artifact only. The submitted NCS manuscript has not been overwritten.

## 1. Editorial Decision Signal

The decision does not allege technical error, inadequate reporting or misconduct. The operative reason is editorial significance and journal fit: the manuscript was not judged to provide a sufficiently substantial practical or conceptual/methodological advance for the broad computational-science readership of Nature Computational Science.

This is not a request for a rebuttal. The realistic routes are:

1. a text-focused transfer to a specialist methods, forecasting or network-science journal; or
2. a materially strengthened study before another broad, high-selectivity computational-science submission.

An appeal is not recommended unless there is clear evidence that the editor missed a specific factual point. The letter gives no such opening.

## 2. Confirmed Reader-Facing Language Problem

Internal reproducibility and packaging language has entered the scientific narrative. This weakens the first screen because it uses scarce abstract and Methods space to describe submission mechanics rather than scientific advance.

Confirmed locations:

| Source | Current problem | Required disposition |
| --- | --- | --- |
| `abstract.md` | Ends with workflow, derived-object and raw-to-derived rebuild language. | Remove completely from the Abstract and replace with a scientific implication. |
| `methods_data.md` | Describes a separate archive, manuscript-facing regeneration, helper checkouts and submitted evidence. | Retain only data provenance, transformations and access limitations; move package mechanics to Data Availability. |
| `methods_estimator.md` | Refers to the default reviewer reproduction path and raw-to-derived reconstruction. | Remove from the estimator description. |
| `methods_estimator.md` | Refers to reproduction entry points in the benchmark paragraph. | Replace with a scientific pointer to settings, projection rules and replication coverage. |
| `methods_uncertainty.md` | Refers to derived evidence objects in a separate reproducibility archive. | Keep the bootstrap settings; remove the archive sentence. |
| `methods_uncertainty.md` | Names `manifest.json`, reproduction commands, environment variables and reviewer rebuild modes. | Remove from scientific Methods; retain seed conventions in Supplementary Methods and operational details in Code Availability/README. |

The Data Availability, Code Availability and dedicated reproducibility note may describe access boundaries and executable materials. The Abstract, Introduction, Results, scientific Methods and Discussion should not describe reviewer archives, manifests, checksums, submission packages, internal commands or build modes.

## 3. QA Process Failure That Must Be Corrected

The prior first-screen audit treated the Abstract's reproducibility sentence as a strong editorial guardrail and recommended keeping it. The final gate then encoded the exact phrase `raw-to-derived rebuilds follow third-party access constraints` as a required Abstract phrase. This made the build process preserve an editorially weak sentence.

Required gate correction:

1. Remove raw-to-derived/package wording from `EXPECTED_UPLOAD_ABSTRACT_PHRASES`.
2. Keep positive checks for the scientific object, separated inputs and collapsed-map endpoint boundary.
3. Add a negative Abstract gate for `workflow`, `derived objects`, `raw-to-derived`, `reviewer`, `archive`, `manifest`, `rebuild`, `submission package`, `checksum` and execution-command language.
4. Add the same negative scan to the reader-facing scientific sections while explicitly excluding Data Availability, Code Availability and the reproducibility supplement.
5. Update the first-screen audit so Abstract sentence functions end with scientific consequence, not package availability.

## 4. Why the Desk-Rejection Risk Was Broader Than the Bad Sentence

Removing internal workflow language is necessary but is unlikely to reverse the editorial assessment by itself.

Current first-screen risks:

- The conceptual contribution is framed as endpoint/query preservation, but the editor may read it as a representation constraint for a separable network VAR rather than a broadly new computational method.
- CP, rolling ridge VAR and finite-horizon impulse responses are established components. The paper must make the new operation enabled by their combination more concrete and consequential.
- Proposition 1 is a deterministic finite-horizon perturbation transfer result. It bounds interpretation but does not establish a new estimator rate, identification result, rank-selection theory or CP convergence result.
- The main benchmark headline compares primarily with unrestricted rolling estimation. Tucker is the strongest same-target comparator; projected graph-feature methods are bounded stress diagnostics rather than native competing systems.
- The RCEP result is explicitly descriptive and its re-estimation interval crosses zero. The NYC result is deliberately near-null. These are rigorous boundaries, but they provide a weak immediate-practical-impact signal to a broad editor.
- The Abstract devotes substantial space to exclusions and reproducibility mechanics. This makes the paper look defensive before the reader sees why the operator changes scientific practice.

## 5. Revision Strategy

### Phase A: Preserve and isolate

- Keep the submitted NCS files and archives unchanged as a dated record.
- Create a separate resubmission directory only after the next target journal is selected.
- Record the NCS decision as a fit/significance outcome, not as evidence of technical failure.

### Phase B: Scientific-narrative cleanup

- Rewrite the Abstract to follow: recurring scientific problem -> information loss in collapsed smoothing -> topology-switchable operator -> benchmark evidence -> empirical demonstration -> reusable scientific implication.
- Remove all package/reviewer/build language from reader-facing scientific sections.
- Keep one concise estimand boundary in the Abstract; move detailed exclusions to Methods and Discussion.
- Replace submission-specific terms such as `submitted operator protocol` with venue-neutral scientific language.
- Keep code/data access details in formal availability statements and the reproducibility appendix only.

Recommended Abstract closing function:

> These results establish endpoint preservation as a practical design criterion for topology-sensitive response analysis in evolving networks.

This sentence is a direction, not final wording. It must remain qualified by the separable-operator and supplied-topology scope stated elsewhere.

### Phase C: Sharpen the contribution claim

- Define the contribution as an operation that existing collapsed representations cannot answer without an identified inverse: matched topology substitution on one fitted dynamic path.
- State explicitly what becomes newly computable, for whom, and in which model class.
- Separate three claims throughout: endpoint availability, numerical recovery, and empirical readout. Do not present CP itself as the conceptual novelty.
- Explain the practical failure caused by losing the topology argument: observed, zero-network and frozen-topology responses can no longer be matched evaluations of one fitted path.
- Reframe the applications as demonstrations of both a non-zero and a near-null answer returned by the same operator, while preserving the descriptive/non-causal boundary.

### Phase D1: Text-only specialist-journal route

Use this route if no new experiments or theory are planned.

- Reframe the title and Abstract for a methods/network-econometrics audience.
- Keep the current benchmark and empirical evidence, with transparent comparator scopes.
- Shorten NCS-specific broad-readership positioning and remove all portal/reviewer language.
- Candidate-fit order for detailed evaluation: `Computational Statistics & Data Analysis`, `Journal of Network Science`, and `International Journal of Forecasting` if the forecasting evaluation is strengthened in presentation.
- `Journal of Econometrics` would likely require substantially deeper identification or asymptotic theory than the current manuscript provides.
- Within Nature Portfolio, `Scientific Reports` is the most plausible transfer without a major evidence expansion; transfer to `Nature Communications` is not recommended on the present evidence because the same broad-significance objection would probably recur.

Journal scope and current author guidelines must be verified before choosing a target.

### Phase D2: Broad high-selectivity route

Use this route only if new work is authorized. Text changes alone are insufficient.

Priority evidence additions:

1. Show the endpoint-loss problem in multiple model families or supply a general operator-preservation theorem beyond the current separable network-VAR construction.
2. Add native, fairly tuned comparison protocols for methods that genuinely support the same topology-substitution query, rather than relying mainly on projected stress mappings.
3. Expand scale and topology regimes beyond the bounded N=50 stress rows.
4. Add at least one application where topology substitution changes a consequential scientific conclusion while uncertainty remains informative.
5. Strengthen theory with identification conditions, statistical error rates or inferential guarantees if the target journal expects a methodological advance rather than a measurement protocol.

## 6. Proposed Editing Order

1. Select the target journal and freeze its article type, length, anonymity and data/code rules.
2. Create an isolated resubmission copy.
3. Rewrite Title, Abstract and the final Introduction paragraph for the selected audience.
4. Remove internal workflow language from scientific Methods and update cross-references.
5. Rework Results headings and Discussion around endpoint availability, recovery and scientific use.
6. Update figures only after the new narrative hierarchy is fixed.
7. Revise Data/Code Availability for the selected journal without leaking those details back into the Abstract or Methods.
8. Replace the obsolete NCS first-screen audit and fix the final gate.
9. Rebuild DOCX/PDF, inspect the first two pages visually and scan all reader-facing text for internal terms.
10. Run claim, citation, figure and package consistency checks before transfer or resubmission.

## 7. Acceptance Criteria for the Next Version

- The Abstract contains no repository, archive, reviewer, manifest, build, workflow or raw-to-derived execution language.
- The scientific Methods describe data, algorithms and uncertainty, not submission-package operation.
- The first 150 words identify a scientific problem, a specific computational advance and evidence for that advance.
- The title and Abstract match the selected journal's readership rather than retaining NCS-specific positioning by default.
- Every headline claim is supported by the existing benchmark, theorem or empirical result, or is explicitly marked as requiring new evidence.
- Availability statements remain accurate and conservative, but do not consume scientific-narrative space.
- The next submission package is physically separate from the rejected NCS submission record.
