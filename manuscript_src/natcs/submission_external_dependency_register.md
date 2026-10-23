# Submission External Dependency Register

Purpose: collect the remaining submission dependencies that cannot be closed from the manuscript source tree alone. This is an author-facing gate register, is not manuscript text and should stay out of the formal upload set unless the authors choose to include it inside a submission-support bundle.

Boundary: this register does not strengthen any Data availability, Code availability, figure-quality or public-release claim. It records what evidence would permit a change and what the default conservative position remains while evidence is absent.

Register date: 2026-08-26 refresh against the current governance records.

Current controlling status, 2026-08-31: the 2026-08-26 `RC-1 = NOT_GRANTED` and `POTENTIAL_ONLY_NOT_ACTIVATED` entries below are retained as historical gate context. The subsequent author-approved activation record controls the current package: `RC-1 = ACTIVATED`, `RC-2 = ACTIVATED_WITH_LIMITATIONS`, and `RCEP F3 = not_identified`. This status update does not close the author-controlled raw-source or public-release rows and does not imply that an external Fig. 2 portal observation exists.

Serves: rigour / reproducibility / clarity / visual communication.

## Executive Gate Table

| Gate | Owner | Decision needed | Evidence that closes the gate | Current default if unresolved | Allowed change after closure | Review target |
| --- | --- | --- | --- | --- | --- | --- |
| Main-figure upload readability | Submitting author | Confirm that the active Figure 1-3 sequence stays readable in the journal upload preview. | A portal screenshot or written upload-preview note from the actual submission event, plus the standalone editable SVG/PDF files and the three source-level QA records. | Keep the standalone vector files and state only that source-level QA passed; the portal-preview checklist stays disabled and claims no portal validation before upload. | If a final upload preview rasterizes a figure poorly, revise only the affected Python source, rebuild the authorized package and rerun the three-figure QA. | rigour / visual communication |
| Raw-source access and helper-code boundary | Authors/data owner | Decide, source block by source block, whether raw files can be shared with reviewers, obtained through public routes, or represented only by derived evidence and acquisition notes. | `raw_source_access_decision_worksheet.md` reviewed and either signed off with the conservative defaults or overwritten with provider-term/licence evidence, exact reviewer routes where applicable and an RCEP helper audit. | Retain the conservative Data availability and Code availability wording: derived-evidence rebuild supported; raw-to-derived reconstruction documented and externally constrained. All rows remain OPEN pending author confirmation. | Strengthen Data availability, Code availability or Supplementary Note 7 only for source blocks with confirmed sharing/public-route decisions; leave unresolved blocks conservative. | reproducibility / rigour / clarity |
| Acceptance-stage public DOI release | Authors/corresponding author | Decide repository route, code licence, derived-evidence licence, release contents, exclusions and embargo timing. | `public_release_readiness_worksheet.md` reviewed and either signed off with the future-release defaults or overwritten with repository URL/DOI, licence files and a pre-deposit audit showing no restricted raw files, credentials, private paths or non-redistributable helper code. | Keep future-tense wording: on acceptance the authors will deposit the redistributable code-and-derived-evidence release in a DOI-minting repository. No DOI, licence or repository may be named as final. | Replace future-tense wording only after the release route and access terms exist or the journal requests a concrete pre-publication repository record. | reproducibility / clarity |
| Manuscript-promotion authorization (RC-1) | Author | Grant or withhold separate authorization for any quarantined-run value, figure or claim fragment to enter manuscript promotion. | A dated author decision recorded alongside the controlling audits; status today is NOT_GRANTED. | No quarantined-run value enters any manuscript surface; `results_rcep.md` and `results_generality.md` keep their inactive audit-boundary draft markers. | Only after RC-1 is granted may a previously quarantined fragment be considered for promotion, still subject to RC-2 flag resolution for touched fragments. | rigour / reproducibility |
| Empirical claim activation (RC-2) | Author + pipeline owners | Resolve or explicitly accept every open characterization flag for any fragment slated for activation. | Disposition record moving `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD` to closed, covering RCEP F1 (undocumented GIRF date substitution), F2 (point outside its bootstrap CI), F3 (stable-subsample regression not identified), NYC stability-rate semantics, NYC GIRF date remap, origins 66-of-69, negative late-period g_net estimates and the missing RNG-seed record. | Quarantine-candidate mappings stay POTENTIAL_ONLY_NOT_ACTIVATED; controlled gains 93.6/96.8/82.5/87.3 remain the only active empirical numbers in manuscript sources. | Per-fragment activation becomes possible once its flags are resolved or accepted in writing by the author. | rigour / reproducibility |
| Post-regeneration review (RC-3) | Independent reviewer lane | Confirm that the rebuilt manuscript, reviewer archive, clean submission package and upload-freeze manifest carry no open FATAL or CRITICAL issue. | An independent post-regeneration review report over the rebuilt artifacts, plus refrozen checksums and a passing final-gate check. | Prior frozen builds remain the reference; rebuilt artifacts stay unsubmitted until reviewed. | Upload-version freeze and submission-day triage proceed after the review reports clean. | rigour / clarity |

## Submission Triage Rules

- Main-figure upload readability is the only external dependency that can directly change a main figure before final upload. If a portal preview fails, revise the affected source before submission.
- Raw-source access can remain bounded at submission while the Data availability statement stays conservative and the derived-evidence archive stays complete for manuscript-facing outputs.
- The public DOI release can remain future-tense at submission. Do not insert a DOI, repository name or licence until those facts exist.
- If a source block is unresolved, avoid wording that implies complete raw-file availability, complete raw-layer reproducibility or an existing public deposit for that block.
- If the portal accepts only the manuscript file and no standalone figure source, Figures 1-3 must remain readable enough in the embedded manuscript preview to carry the capability, certificate and operating-regime arguments.
- After any gate evidence arrives, apply the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md` before editing formal wording, rebuilding packages or marking the gate closed.

## Decision-To-Text Map

| Dependency outcome | Text/package action | Do not do |
| --- | --- | --- |
| Figure 1-3 upload preview passes | Keep the active sequence and retain the standalone editable files for editor/reviewer zoom inspection. | Do not redesign only for aesthetic preference after the text is frozen. |
| One figure upload preview fails | Revise only that figure's Python source, rebuild the authorized manuscript/figure package, rerun page-render QA and checksum checks. | Do not replace a source-controlled vector figure with a raster screenshot. |
| Raw source block is shareable with reviewers | Update Data availability with the exact reviewer route and access condition for that block; update Supplementary Note 7 with file placement and command expectations. | Do not generalize one shareable source block to all source blocks. |
| Raw source block is public-route only | Record source URL, version, query date or commit hash; keep raw files unbundled unless terms permit bundling. | Do not imply that public-route raw files ride inside the shipped archive. |
| Raw source block is derived-only | Keep the current boundary and identify the derived substitute used for manuscript-facing outputs. | Do not weaken the derived-evidence claim; the derived layer remains the reviewable evidence layer. |
| DOI release is assigned | Replace future-tense wording with DOI, repository name, licence and access terms; update public-release notes and Supplementary Note 7. | Do not insert placeholder DOI, expected DOI or an unconfirmed licence. |
| RC-1 granted / RC-2 flags dispositioned | Route the affected fragments through re-audit, then update results sources through the governed build chain with fresh inactive-marker removal decisions recorded first. | Do not paste quarantined values into drafts ahead of the authorization chain. |

## Reviewer-Risk Interpretation

NCS senior editor: the register reduces the chance that unresolved external items look like hidden weaknesses. It shows that the main scientific claim rests on the controlled benchmark evidence and does not depend on unverified raw-data openness, a future DOI or quarantined application values.

Computational methods reviewer: the raw-source and code-release gates preserve the evidence hierarchy. The reviewer can evaluate the derived-evidence rebuild claim without being asked to accept a stronger raw-to-derived reproducibility claim.

Figure/visual reviewer: the upload gate keeps the three-figure narrative tied to actual rendering as well as local source quality.

## Minimum Author Inputs

Use `natcs_coauthor_action_request.md` as the one-page request to collect replies from the corresponding author, submitting author and data-owning coauthors. Use `natcs_final_author_decision_sheet.md` as the consolidated sign-off dashboard pointing back to the detailed worksheets.

1. A completed upload-preview record for the active Figure 1-3 sequence after upload.
2. Author sign-off or corrections for the prefilled source-block defaults in `raw_source_access_decision_worksheet.md`.
3. Author sign-off or corrections for the prefilled release-route, licence and embargo defaults in `public_release_readiness_worksheet.md`.
4. A dated author decision on RC-1 (manuscript-promotion authorization) and on each RC-2 characterization flag touched by any intended fragment.
5. Confirmation that the reviewer archive and figure-source package used at upload are the final refrozen versions, following the RC-3 post-regeneration review.
6. Processing of every changed gate status through the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md`.

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
