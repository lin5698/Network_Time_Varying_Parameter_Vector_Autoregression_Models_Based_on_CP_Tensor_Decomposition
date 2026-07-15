# Submission External Dependency Register

Purpose: collect the remaining submission dependencies that cannot be closed from the manuscript source tree alone. This is an author-facing gate register, not manuscript text. It should not be uploaded as a formal article file unless the authors choose to include it as part of a submission-support bundle.

Boundary: this register does not strengthen any Data availability, Code availability, figure-quality or public-release claim. It records what evidence would permit a change and what the default conservative position remains when evidence is absent.

Serves: rigour / reproducibility / clarity / visual communication.

## Executive Gate Table

| Gate | Owner | Decision needed | Evidence that closes the gate | Current default if unresolved | Allowed change after closure | Review target |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 2 journal portal preview | Submitting author | Decide whether the current embedded Fig. 2 remains readable in the journal upload system or whether a redesign is required. | Completed `ncs_fig2_portal_preview_checklist.md`, with portal screenshot or written upload-preview note confirming that panel a is readable at first view, or that the standalone `figure2_endpoint_preservation_benchmark.pdf` or `.svg` is accepted and comfortably zoomable. | Keep the current Fig. 2, upload or retain standalone PDF/SVG, and state only that local page-render QA passed with a zoom/source-file caveat. | If pass: no manuscript change needed; record preview pass in the figure QA memo. If fail: redesign Fig. 2 using `ncs_fig2_redesign_contract.md`, rebuild manuscript and figure-source package, then rerun figure QA. | rigour / visual communication |
| Raw-source access and helper-code boundary | Authors/data owner | Decide, source block by source block, whether raw files can be shared with reviewers, obtained through public routes, or only represented by derived evidence and acquisition notes. | `raw_source_access_decision_worksheet.md` reviewed and either signed off with the prefilled conservative defaults or overwritten with provider-term/licence evidence, exact reviewer routes where applicable and a RCEP helper audit. | Retain the current conservative Data availability and Code availability wording: derived-evidence rebuild is supported; raw-to-derived reconstruction is documented but externally constrained. | Strengthen Data availability, Code availability or Supplementary Note 7 only for source blocks with confirmed sharing/public-route decisions. Leave unresolved blocks conservative. | reproducibility / rigour / clarity |
| Acceptance-stage public DOI release | Authors/corresponding author | Decide repository route, code licence, derived-evidence licence, release contents, exclusions and embargo timing. | `public_release_readiness_worksheet.md` reviewed and either signed off with the prefilled future-release defaults or overwritten with repository URL/DOI, licence files and a pre-deposit audit showing no restricted raw files, credentials, private paths or non-redistributable helper code. | Keep future-tense wording: on acceptance, the authors will deposit the redistributable code-and-derived-evidence release in a DOI-minting repository. Do not name a DOI, licence or repository as final. | Replace future-tense wording only after the release route and access terms exist or the journal requests a concrete pre-publication repository record. | reproducibility / clarity |

## Submission Triage Rules

- Fig. 2 is the only dependency that can directly change a main figure before final upload. If portal preview fails, redesign before submission.
- Raw-source access can remain bounded at submission if the Data availability statement stays conservative and the derived-evidence archive remains complete for manuscript-facing outputs.
- The public DOI release can remain future-tense at submission. Do not insert a DOI, repository name or licence until those facts exist.
- If a source block is unresolved, avoid wording that implies complete raw-file availability, complete raw-layer reproducibility or an already public deposit for that block.
- If the portal accepts only the manuscript file and no standalone figure source, Fig. 2 must be readable enough in the embedded manuscript preview to carry the endpoint-availability argument.
- After any gate evidence arrives, apply the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md` before editing formal wording, rebuilding packages or marking the gate closed.

## Decision-To-Text Map

| Dependency outcome | Text/package action | Do not do |
| --- | --- | --- |
| Fig. 2 preview passes and standalone source files are accepted | Keep current Fig. 2. Add a dated note to `ncs_figure_qa_memo.md` if desired. Keep `latest_natcs_main_figure_sources.zip` available for upload or editor/reviewer zoom inspection. | Do not redesign only for aesthetic preference after the text is frozen. |
| Fig. 2 preview fails | Redesign according to `ncs_fig2_redesign_contract.md`, rebuild the manuscript and figure-source package, rerun page-render QA and checksum/zip checks. | Do not submit a rasterized unreadable benchmark figure; Fig. 2 carries the main methods evidence. |
| Raw source block is shareable with reviewers | Update Data availability with the exact reviewer route and access condition for that block. Update Supplementary Note 7 with file placement and command expectations. | Do not generalize one shareable source block to all source blocks. |
| Raw source block is public-route only | Record source URL, version, query date or commit hash. Keep raw files unbundled unless terms permit bundling. | Do not imply that public-route raw files are included in the reviewer archive. |
| Raw source block is derived-only | Keep the current boundary and identify the derived substitute used for manuscript-facing outputs. | Do not weaken the derived-evidence claim; the derived layer remains the reviewable evidence layer. |
| DOI release is assigned | Replace future-tense wording with DOI, repository name, licence and access terms. Update public-release notes and Supplementary Note 7. | Do not insert placeholder DOI, expected DOI or unconfirmed licence. |

## Reviewer-Risk Interpretation

NCS senior editor: the register reduces the chance that unresolved external items look like hidden weaknesses. It shows that the manuscript's main scientific claim does not depend on unverified raw-data openness or a future DOI.

Computational methods reviewer: the raw-source and code-release gates preserve the evidence hierarchy. The reviewer can evaluate the derived-evidence rebuild claim without being asked to accept a stronger raw-to-derived reproducibility claim.

Figure/visual reviewer: the Fig. 2 gate keeps the decisive benchmark figure tied to actual upload rendering as well as local source quality.

## Minimum Author Inputs

Use `natcs_coauthor_action_request.md` as the one-page request to collect replies from the corresponding author, submitting author and data-owning coauthors. Use `natcs_final_author_decision_sheet.md` as the consolidated sign-off dashboard. It points back to the detailed worksheets below.

1. A completed `ncs_fig2_portal_preview_checklist.md` row set, with portal-preview screenshot or written confirmation for Fig. 2 after upload.
2. Author sign-off or corrections for the prefilled source-block defaults in `raw_source_access_decision_worksheet.md`.
3. Author sign-off or corrections for the prefilled release-route, licence and embargo defaults in `public_release_readiness_worksheet.md`.
4. Confirmation that the reviewer archive and figure-source package used at upload are the final frozen versions.
5. Confirmation that any changed gate status has been processed through the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md`.
