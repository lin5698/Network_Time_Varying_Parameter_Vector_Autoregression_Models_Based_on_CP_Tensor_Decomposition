# NatCS Coauthor Action Request

Purpose: one-page request for the corresponding author, submitting author and data-owning coauthors to close the remaining external gates before Nature Computational Science upload. This is a working support note, not manuscript text and not new evidence.

Boundary: this note does not change the current conservative Data availability, Code availability, figure-quality or public-release claims. If an item is unanswered, keep the default listed below and do not strengthen the formal manuscript wording.

Serves: rigour / reproducibility / clarity / visual communication.

## Reply Needed

Please reply to each row with one of the acceptable answers or attach the requested evidence. Use the detailed worksheet listed in the `File to update after confirmation` column only after the fact is confirmed.

| Request | Who should answer | Acceptable answer or evidence | Default if unanswered | File to update after confirmation | Reviewer target |
| --- | --- | --- | --- | --- | --- |
| Fig. 2 journal portal preview | Submitting author | A completed `ncs_fig2_portal_preview_checklist.md` entry with a portal screenshot or written preview note showing that panel a is readable at first view, or that standalone `figure2_endpoint_preservation_benchmark.pdf` or `.svg` is accepted and comfortably zoomable. | Keep current Fig. 2 only with the local-QA caveat; if panel a is unreadable and no standalone route exists, redraw before submission. | `ncs_fig2_portal_preview_checklist.md`; `ncs_figure_qa_memo.md`; `submission_external_dependency_register.md` | rigour / visual communication |
| Raw source access for macro, trade, tariff/import, MRIO and NYC blocks | Data-owning authors | For each source block, choose one status from `Reviewer raw-file sharing confirmed`, `Provider public route only`, `Derived substitute only` or `Mixed`, with provider terms, licence notes, public route, query date or reviewer-route evidence. | Keep current derived-evidence wording; do not claim raw-file sharing or full raw-to-derived rebuild. | `raw_source_access_decision_worksheet.md`; then only confirmed rows in `data_availability.md`, `code_availability.md` and Supplementary Note 7 | reproducibility / rigour / clarity |
| RCEP acquisition helper checkout | Author who owns the helper route | A checked statement that the helper has no private credentials, private paths, unpublished code or non-redistributable dependencies, plus either a cleaned release route or a tested public replacement route. | Keep the helper non-redistributed and outside the default reviewer path. | `raw_source_access_decision_worksheet.md`; `public_release_readiness_worksheet.md`; then `code_availability.md` and Supplementary Note 7 only if a clean route exists | reproducibility / rigour |
| Acceptance-stage public release route | Corresponding author or repository owner | Repository choice, DOI/accession if assigned, release title, code licence, derived-evidence licence/access terms, embargo timing and excluded restricted files. | Keep future-tense wording: the redistributable code-and-derived-evidence release will be deposited on acceptance in a DOI-minting repository. | `public_release_readiness_worksheet.md`; then `data_availability.md`, `code_availability.md` and Supplementary Note 7 only after the record exists or the journal requests it | reproducibility / clarity |
| Public-release safety check | Repository owner and submitting author | Confirmation that no restricted raw files, credentials, API keys, private paths, institution-only caches or non-redistributable helper code are included in any public release candidate. | Do not deposit the public release as final; keep reviewer-archive and future-release wording. | `public_release_readiness_worksheet.md`; `ncs_release_safety_audit.md`; release README/manifest | reproducibility / rigour / clarity |
| Frozen upload package use | Submitting author | Confirmation during portal upload that the files used match `natcs_upload_freeze_manifest.md/json`, with no post-freeze edits to manuscript, figures, reviewer archive or end matter. | Regenerate the package and upload-freeze manifest before upload. | `natcs_final_author_decision_sheet.md`; `natcs_upload_freeze_manifest.md/json`; `submission_checklist.md` | reproducibility / rigour |
| Final positioning guardrail | Corresponding author | Confirm the representation-level query-preservation positioning remains in the title, abstract, cover letter and portal fields, and confirm no new wording claims policy identification, domain-wide transfer, native graph-neural-network superiority, public access to every raw input, assigned repository identifiers/licences or complete raw-layer reproducibility. | Keep the current bounded title, abstract, cover letter, portal fields and availability statements. | `natcs_final_author_decision_sheet.md`; `ncs_portal_field_kit.md`; `ncs_availability_consistency_audit.md` | novelty / clarity / rigour |

## Minimal Email Text

Please review the attached NatCS support package and answer the seven rows in `natcs_coauthor_action_request.md`. The current submission is intentionally conservative: it supports manuscript-facing evidence from derived objects, keeps raw-source and helper-code boundaries explicit, and promises a DOI-minting public release only on acceptance. We should change Data availability, Code availability, Fig. 2, or public-release wording only where you can provide the specific evidence requested in the table.

## If No Further Evidence Arrives

Use the current conservative submission path:

1. Complete the Fig. 2 portal preview check after upload and redraw only if the portal view fails the checklist.
2. Leave Data availability and Code availability in derived-evidence mode.
3. Keep public DOI, repository and licence wording in future tense.
4. Upload from the frozen package recorded in `natcs_upload_freeze_manifest.md/json`.
5. Keep the representation-level query-preservation portal wording and do not add stronger causal, generality, raw-data or public-release claims during portal entry.
