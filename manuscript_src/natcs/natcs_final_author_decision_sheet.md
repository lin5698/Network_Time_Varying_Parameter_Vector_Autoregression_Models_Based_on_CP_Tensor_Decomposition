# NatCS Final Author Decision Sheet

Purpose: give the corresponding author and submitting author one consolidated decision sheet before Nature Computational Science upload. This is a working author sign-off document, not manuscript text.

Boundary: this sheet does not claim that any external gate is closed. It summarizes the current conservative submission path and names the evidence needed before changing manuscript wording, figure files or availability statements.

Serves: rigour / reproducibility / clarity / visual communication.

## Current Best Submission Path

The manuscript can remain evidence-bound if the following default positions are kept:

1. Keep Fig. 2 only if the journal upload preview or standalone PDF/SVG route passes the Fig. 2 portal checklist after the actual upload preview.
2. Keep Data availability and Code availability in derived-evidence mode unless authors confirm stronger raw-source sharing rights.
3. Keep public DOI wording in future tense unless a DOI, repository route, licence and access terms actually exist.
4. Keep the representation-level query-preservation positioning in the title, abstract, cover letter, portal fields and scope note without adding causal RCEP, broad generality or temporal-GNN superiority language.

## Submission-Day Stop/Go Triage

Use this table before pressing final submit in the journal portal.

| Situation at upload | Decision | Required action |
| --- | --- | --- |
| Final gate has no errors; upload ZIPs pass integrity checks; Fig. 2 passes the portal route; raw-source and public-release decisions are unresolved but formal wording stays conservative; uploaded files match the freeze manifest. | Go with the conservative submission package. | Keep Data/Code availability unchanged, retain support notes, and record the upload confirmation. |
| Final gate has no errors, but Fig. 2 portal readability is still unknown. | Hold final submission until Fig. 2 is checked. | Complete `ncs_fig2_portal_preview_checklist.md` or confirm standalone PDF/SVG inspection. |
| Fig. 2 fails portal preview and no standalone source route is available. | Rebuild before submission. | Redesign Fig. 2 under `ncs_fig2_redesign_contract.md`, rebuild all packages and rerun final gates. |
| Any Data availability, Code availability, title, abstract, cover letter, figure, reviewer archive or portal-field wording changes after the upload-freeze manifest. | Rebuild before submission. | Regenerate the manuscript package, figure-source package, upload-freeze manifest and final gate output. |
| Any new wording claims raw-file sharing, public DOI/licence, RCEP policy identification, broad empirical generality or native graph-learning superiority without confirmed evidence. | Stop and revert to bounded wording. | Use the portal-field kit, raw-source worksheet and public-release worksheet before submitting. |

## Final Gate Dashboard

| Gate | Minimum author action before upload | If unresolved | If pass/confirmed | Files to update only if status changes | Review target |
| --- | --- | --- | --- | --- | --- |
| Fig. 2 portal preview | Complete `ncs_fig2_portal_preview_checklist.md` after journal upload preview. Upload or retain the standalone Fig. 2 PDF/SVG route if the portal permits it. Save page or panel-a screenshot if possible. | Do not mark Fig. 2 gate as passed. If panel a is unreadable and no standalone source route exists, redesign before submission. | Keep current Fig. 2 and retain `latest_natcs_main_figure_sources.zip` for source inspection. | `ncs_figure_qa_memo.md`; `submission_external_dependency_register.md`; rebuild figure-source package only if redesigned. | rigour / visual communication |
| Raw-source access | Review `raw_source_access_decision_worksheet.md` and either sign off conservative defaults or record source-block permissions. | Keep current Data/Code availability. Do not claim raw-file sharing or full raw rebuild. | Strengthen only the confirmed source blocks, with exact reviewer route or public query route. | `data_availability.md`; `code_availability.md`; Supplementary Note 7; raw-source worksheet. | reproducibility / rigour / clarity |
| RCEP helper checkout | Confirm whether helper checkout has private credentials, private paths, unpublished code or non-redistributable dependencies. | Keep helper non-redistributed and outside the default reviewer path. | Release a cleaned helper or record a tested public replacement route. | `code_availability.md`; Supplementary Note 7; raw-source worksheet; public-release worksheet. | reproducibility / rigour |
| Public DOI release | Review `public_release_readiness_worksheet.md` and choose repository route, code licence, data licence, exclusions and embargo timing. | Keep future-tense DOI-minting language. Do not name a repository, DOI or licence. | Replace future-tense wording only after the record exists or the journal requests a pre-publication repository. | `data_availability.md`; `code_availability.md`; Supplementary Note 7; public-release worksheet. | reproducibility / clarity |
| Reviewer archive freeze | Confirm the archive used at upload matches the local upload-freeze manifest and has not changed after clean-copy checks. | Do not make stronger reproducibility claims. Use the latest verified package only. | Retain the frozen archive path, figure-source ZIP and checksums for editor/reviewer transfer. | `submission_checklist.md`; `natcs_upload_freeze_manifest.md/json`; cleanroom reproduction notes only if rerun. | reproducibility / rigour |
| Final title and positioning | Confirm the title remains object-first and the NCS fit remains representation-level: the fitted object determines which topology-substitution readouts stay measurable after temporal smoothing. | Keep current title and current query-preservation wording. | Change only if all title/abstract/cover-letter/portal-field references are updated together. | `abstract.md`; `cover_letter.md`; `ncs_portal_field_kit.md`; metadata in build script if needed. | novelty / clarity |

## Decisions That Can Stay Conservative At Submission

| Decision | Conservative submission position | Why this is acceptable for review |
| --- | --- | --- |
| Raw IMF, tariff, bilateral trade and MRIO inputs | Raw inputs are documented through acquisition notes and governed by provider terms. | The submitted-evidence layer regenerates manuscript-facing figures, tables and numerical summaries from derived objects. |
| Public DOI release | Deposit will occur on acceptance in a DOI-minting repository. | A DOI cannot be named before it exists; the release contents and exclusions are already mapped. |
| NYC upstream source | Public route and commit are recorded; derived monthly panel is available for review. | The NYC panel supports same-operator execution and reproducibility, not broad empirical generality. |
| Projected graph-feature comparisons | Rows remain operator-recovery stress tests after projection. | The benchmark target is topology-substitution endpoint recovery, not native temporal-GNN forecasting. |

## Decisions That Should Trigger Text Changes

| New author evidence | Text/package change | Guardrail |
| --- | --- | --- |
| Provider terms permit reviewer sharing for one raw-source block. | Add the exact reviewer route and access condition for that block. | Do not generalize that permission to other source blocks. |
| Repository and DOI are assigned. | Replace future-tense public-release wording with repository name, DOI, licence and access terms. | Do not insert placeholder DOI or expected licence. |
| Fig. 2 portal preview fails. | Redesign Fig. 2 using `ncs_fig2_redesign_contract.md`; rebuild manuscript and figure-source package. | Do not submit an unreadable benchmark figure because Fig. 2 carries the methods evidence chain. |
| Co-authors want stronger RCEP policy language. | Do not add it without a separate identification design and evidence. | Keep the manuscript claim as fixed-path topology-sensitive measurement. |
| Co-authors want broad domain-generalization language. | Do not add it without additional domain tests. | Keep NYC as a public second-domain operator check. |

## Post-Confirmation Update Checklist

Use this checklist after any external gate evidence arrives. A gate is closed only when the source worksheet, linked formal text and regenerated package all tell the same story.

| New evidence received | Files to update first | Rebuild and verification required before upload | What this protects |
| --- | --- | --- | --- |
| Fig. 2 portal preview passes. | `ncs_fig2_portal_preview_checklist.md`; `ncs_figure_qa_memo.md`; `submission_external_dependency_register.md`; this sheet. | Rebuild the submission package and upload-freeze manifest, then rerun `scripts/check_natcs_final_gates.mjs` and both ZIP integrity tests. | The visual gate is recorded without changing the benchmark claim or figure files. |
| Fig. 2 portal preview fails. | `ncs_fig2_redesign_contract.md`; figure-generation script or source figure; `ncs_figure_qa_memo.md`; this sheet. | Regenerate figures, manuscript, figure-source package, upload-freeze manifest and final gates. Inspect the redesigned Fig. 2 page and source figure before upload. | The endpoint-preservation benchmark remains readable enough to support the methods claim. |
| Raw-source defaults are signed off with no stronger sharing route. | `raw_source_access_decision_worksheet.md`; this sheet; `submission_external_dependency_register.md`. | Rebuild the submission package and rerun final gates. Keep Data availability, Code availability and Supplementary Note 7 unchanged. | The conservative reproducibility boundary is explicitly confirmed. |
| One or more raw-source blocks gain confirmed reviewer or public access. | `raw_source_access_decision_worksheet.md`; `data_availability.md`; `code_availability.md`; Supplementary Note 7; this sheet. | Rebuild manuscript artifacts, reviewer archive if file contents or routes change, upload-freeze manifest and final gates. Check that strengthened wording names only the confirmed blocks. | Source access is improved without implying full raw-layer reproducibility. |
| Public repository, DOI, licence and access terms are assigned. | `public_release_readiness_worksheet.md`; `data_availability.md`; `code_availability.md`; Supplementary Note 7; this sheet. | Rebuild manuscript artifacts, release-safety audit, upload-freeze manifest and final gates. Check the release contains no restricted raw files or private helper material. | Public-release wording matches an existing record and remains release-safe. |
| Portal fields, title, abstract, cover letter or formal availability text are edited. | The edited source file plus `ncs_portal_field_kit.md` or `ncs_availability_consistency_audit.md` as applicable. | Rebuild all submission artifacts and rerun final gates before using the edited text. | First-screen positioning, overclaim boundaries and DOCX extraction remain synchronized. |

## Local Freeze Evidence

The current package includes a local upload-freeze manifest in `output/submission_package/natcs_current/03_submission_materials/natcs_upload_freeze_manifest.md` and `.json`. This manifest records hashes for the main manuscript PDF/DOCX, Supplementary PDF/DOCX, latest word-only upload ZIP, stamped submission-upload ZIP, main figure-source ZIP, submission inventory, reviewer-archive manifest and reviewer-archive README.

Interpretation: this closes the local file-identity check for the current build. It does not close the journal portal preview, raw-source access, helper-code or public-release gates. If any manuscript wording, figure file, reviewer archive file or end-matter file changes, rebuild and regenerate the upload-freeze manifest before upload.

## Final Author Sign-Off

Complete this table before upload.

| Item | Status: Confirmed / Conservative / Needs action | Author note |
| --- | --- | --- |
| Fig. 2 portal-preview checklist completed. | Needs action | TODO |
| Standalone Fig. 2 PDF/SVG route accepted or manuscript preview zoom is comfortable. | Needs action | TODO |
| Raw-source access worksheet signed off or corrected. | Needs action | TODO |
| RCEP helper checkout boundary signed off. | Needs action | TODO |
| Public-release readiness worksheet signed off or corrected. | Needs action | TODO |
| Reviewer archive and figure-source package are locally frozen and hashed. | Confirmed | See `natcs_upload_freeze_manifest.md/json`; rerun after any edits. |
| Upload uses the frozen package without post-freeze edits. | Needs action | Confirm during portal upload. |
| Representation-level query-preservation positioning is preserved in title, abstract, cover letter and portal fields. | Conservative | Keep current object-first wording unless all linked files are updated together. |
| No causal RCEP, broad generality, native temporal-GNN superiority or full raw-data reproducibility language has been added. | Conservative | Keep current bounded wording unless new evidence exists. |

## Next Action Order

1. Upload the manuscript from the latest clean upload package and, if allowed, upload or retain `figure2_endpoint_preservation_benchmark.pdf` and `.svg` from the figure-source package.
2. Inspect Fig. 2 using `ncs_fig2_portal_preview_checklist.md`; compare panel a against `fig2_panel_a_contact_sheet.png`.
3. If Fig. 2 fails and no standalone source inspection route exists, redraw before submission using `ncs_fig2_redesign_contract.md`.
4. If Fig. 2 passes, sign off raw-source and public-release defaults or provide stronger source/licence evidence.
5. Rebuild the package only after any wording or figure-status change.
