# Submission External Dependency Register

Purpose: collect the remaining submission dependencies that cannot be closed from the manuscript source tree alone. This is an author-facing gate register, not manuscript text. It should not be uploaded as a formal article file unless the authors choose to include it as part of a submission-support bundle.

Boundary: this register does not strengthen any Data availability, Code availability, figure-quality or public-release claim. It records what evidence would permit a change and what the default conservative position remains when evidence is absent.

Serves: rigour / reproducibility / clarity / visual communication.

## Executive Gate Table

| Gate | Owner | Decision needed | Evidence that closes the gate | Current default if unresolved | Allowed change after closure | Review target |
| --- | --- | --- | --- | --- | --- | --- |
| Main-figure upload readability | Submitting author | Confirm that the active Figure 1-3 sequence remains readable in the journal upload preview. | A later portal screenshot or written upload-preview note, plus the standalone editable SVG/PDF files and the three source-level QA records. | Retain the standalone vector files and state only that source-level QA passed; do not claim portal validation before upload. | If a final upload preview rasterizes a figure poorly, revise only the affected Python source, rebuild the authorized package and rerun the three-figure QA. | rigour / visual communication |
| Raw-source access and helper-code boundary | Authors/data owner | Decide, source block by source block, whether raw files can be shared with reviewers, obtained through public routes, or only represented by derived evidence and acquisition notes. | `raw_source_access_decision_worksheet.md` reviewed and either signed off with the prefilled conservative defaults or overwritten with provider-term/licence evidence, exact reviewer routes where applicable and a RCEP helper audit. | Retain the current conservative Data availability and Code availability wording: derived-evidence rebuild is supported; raw-to-derived reconstruction is documented but externally constrained. | Strengthen Data availability, Code availability or Supplementary Note 7 only for source blocks with confirmed sharing/public-route decisions. Leave unresolved blocks conservative. | reproducibility / rigour / clarity |
| Acceptance-stage public DOI release | Authors/corresponding author | Decide repository route, code licence, derived-evidence licence, release contents, exclusions and embargo timing. | `public_release_readiness_worksheet.md` reviewed and either signed off with the prefilled future-release defaults or overwritten with repository URL/DOI, licence files and a pre-deposit audit showing no restricted raw files, credentials, private paths or non-redistributable helper code. | Keep future-tense wording: on acceptance, the authors will deposit the redistributable code-and-derived-evidence release in a DOI-minting repository. Do not name a DOI, licence or repository as final. | Replace future-tense wording only after the release route and access terms exist or the journal requests a concrete pre-publication repository record. | reproducibility / clarity |

## Submission Triage Rules

- Main-figure upload readability is the only external dependency that can directly change a main figure before final upload. If a portal preview fails, revise the affected source before submission.
- Raw-source access can remain bounded at submission if the Data availability statement stays conservative and the derived-evidence archive remains complete for manuscript-facing outputs.
- The public DOI release can remain future-tense at submission. Do not insert a DOI, repository name or licence until those facts exist.
- If a source block is unresolved, avoid wording that implies complete raw-file availability, complete raw-layer reproducibility or an already public deposit for that block.
- If the portal accepts only the manuscript file and no standalone figure source, Figures 1-3 must remain readable enough in the embedded manuscript preview to carry the capability, certificate and operating-regime arguments.
- After any gate evidence arrives, apply the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md` before editing formal wording, rebuilding packages or marking the gate closed.

## Decision-To-Text Map

| Dependency outcome | Text/package action | Do not do |
| --- | --- | --- |
| Figure 1-3 upload preview passes | Keep the active sequence and retain the standalone editable files for editor/reviewer zoom inspection. | Do not redesign only for aesthetic preference after the text is frozen. |
| One figure upload preview fails | Revise only that figure's Python source, rebuild the authorized manuscript/figure package, rerun page-render QA and checksum checks. | Do not replace a source-controlled vector figure with a raster screenshot. |
| Raw source block is shareable with reviewers | Update Data availability with the exact reviewer route and access condition for that block. Update Supplementary Note 7 with file placement and command expectations. | Do not generalize one shareable source block to all source blocks. |
| Raw source block is public-route only | Record source URL, version, query date or commit hash. Keep raw files unbundled unless terms permit bundling. | Do not imply that public-route raw files are included in the reviewer archive. |
| Raw source block is derived-only | Keep the current boundary and identify the derived substitute used for manuscript-facing outputs. | Do not weaken the derived-evidence claim; the derived layer remains the reviewable evidence layer. |
| DOI release is assigned | Replace future-tense wording with DOI, repository name, licence and access terms. Update public-release notes and Supplementary Note 7. | Do not insert placeholder DOI, expected DOI or unconfirmed licence. |

## Reviewer-Risk Interpretation

NCS senior editor: the register reduces the chance that unresolved external items look like hidden weaknesses. It shows that the manuscript's main scientific claim does not depend on unverified raw-data openness or a future DOI.

Computational methods reviewer: the raw-source and code-release gates preserve the evidence hierarchy. The reviewer can evaluate the derived-evidence rebuild claim without being asked to accept a stronger raw-to-derived reproducibility claim.

Figure/visual reviewer: the upload gate keeps the three-figure narrative tied to actual rendering as well as local source quality.

## Minimum Author Inputs

Use `natcs_coauthor_action_request.md` as the one-page request to collect replies from the corresponding author, submitting author and data-owning coauthors. Use `natcs_final_author_decision_sheet.md` as the consolidated sign-off dashboard. It points back to the detailed worksheets below.

1. A completed upload-preview record for the active Figure 1-3 sequence after upload.
2. Author sign-off or corrections for the prefilled source-block defaults in `raw_source_access_decision_worksheet.md`.
3. Author sign-off or corrections for the prefilled release-route, licence and embargo defaults in `public_release_readiness_worksheet.md`.
4. Confirmation that the reviewer archive and figure-source package used at upload are the final frozen versions.
5. Confirmation that any changed gate status has been processed through the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md`.
