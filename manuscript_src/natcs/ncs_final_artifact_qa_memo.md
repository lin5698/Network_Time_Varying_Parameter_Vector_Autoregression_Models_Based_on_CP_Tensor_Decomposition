# NCS Final Artifact QA Memo

> **Current-status supersession, 2026-07-22.** This is a historical render and
> package QA record, not evidence that any current submission artifact is
> usable. `PAPER_CLAIM_AUDIT.md` (`BLOCKED`) and
> `EMPIRICAL_IMPLEMENTATION_AUDIT.md` (`FAIL`) control all current decisions.
> Do not use the findings below to support an upload, a manuscript rebuild,
> Figs. 3-4, Table 2, RCEP/NYC claims, or reproducibility claims. The only
> retained revision reference is the non-numeric Fig. 1/Fig. 2 visual logic,
> subject to a future authorized rebuild and fresh QA.

Purpose: record page-level and upload-artifact QA for the current Nature Computational Science-oriented package after the final prose pass. This is a working QA artifact, not manuscript text.

Audit date: 2026-07-07.

Serves: clarity / rigour / reproducibility / visual communication.

## Materials Checked

- Main manuscript PDF: `output/pdf/natcs_manuscript.pdf`.
- Supplementary Information PDF: `output/pdf/natcs_supplementary.pdf`.
- Main manuscript DOCX: `output/doc/natcs_manuscript.docx`.
- Word-only upload package: `output/integrated_package/latest_submission_upload_word_only`.
- Main page renders: `tmp/pdfs/natcs_main/page-01.png`, `page-06.png`, `page-07.png`, `page-09.png`, `page-10.png` and `page-21.png`.
- Text extraction checks using `pdftotext -layout` and `pandoc ... -t plain`.

## Page-Level Findings

| Item | QA result | Review target |
| --- | --- | --- |
| Page 1, title/abstract/Introduction opening | Pass. The title, authors, funding line, abstract and revised Introduction opening render without overlap or truncation. The abstract avoids inline formula notation, retains the topology-switchable-operator wording and preserves the derived-evidence reproducibility boundary. | clarity / novelty |
| Fig. 2 page | Pass with known caution. The endpoint-availability gate and panel hierarchy remain visible at page scale; smallest secondary labels still require zoom or standalone source inspection. This remains the only major visual-communication gate for journal upload preview. | rigour / visual communication |
| Fig. 3 page | Pass. The RCEP figure makes the fixed-path versus re-estimation boundary visually dominant, and the adjacent text keeps the empirical interpretation descriptive. | significance / rigour / clarity |
| Table 2 and NYC opening page | Pass. Table 2 fits within the page, and the NYC section opens as a public second-domain operator check with near-null contrast language. | generality / clarity |
| Fig. 4 and Discussion opening page | Pass. The NYC near-null readout and Discussion opening connect cleanly. The first Discussion paragraphs foreground query preservation and the transferable criterion. | generality / visual communication |
| References end page | Pass. The final references page has no visible clipping, overlap or dangling heading. | clarity |

## DOCX Upload Finding And Fix

The first DOCX extraction pass showed a cover-letter risk: the inline mathematical operator in the cover letter could be flattened poorly by text extraction, yielding an empty formula in the plain-text preview. This is an upload-preview risk for editor-facing material, even though the manuscript PDF renders equations correctly.

Fix applied: the cover letter now uses the plain-text operator string `M_{k,t}(W)=A_{k,t}+B_{k,t}W` instead of a Word equation. The regenerated DOCX plain-text extraction retains the full operator string.

This change affects only the cover letter. The main manuscript keeps the formal mathematical operator in the Introduction and Methods. The abstract now uses formula-insensitive wording so submission-system and DOCX plain-text extraction preserve the computational object.

## Build-Locality Finding And Fix

The rebuild preflight later caught active PNG resources with macOS `dataless` flags in empirical and evidence output directories. These were cloud-placeholder files, not new evidence. The affected active PNG/PDF duplicates were regenerated from their local PDF counterparts or overwritten from the canonical local figure exports.

Fix applied: active figure resources referenced by the manuscript and reviewer archive are now local files. Historical archive and backup paths remain outside the active submission boundary. This change affects file availability only; it does not change estimates, captions, figure logic or manuscript claims.

## Verification

- `node scripts/build_natcs_manuscript.mjs` passed after the cover-letter and build-locality fixes.
- `node scripts/create_clean_natcs_integrated_package.mjs` passed after the current package rebuild.
- `node scripts/check_natcs_final_gates.mjs` reports `PASS_WITH_WARNINGS_ALLOWED` with only the expected external author/portal warnings.
- `pandoc output/integrated_package/latest_submission_upload_word_only/cover_letter_natcs.docx -t plain --wrap=none` retains `M_{k,t}(W)=A_{k,t}+B_{k,t}W`.
- The upload-facing main-manuscript DOCX abstract extraction retains the first-screen topology-switchable-operator, separated-input, endpoint-availability and raw-to-derived-boundary phrases.
- The current abstract remains within the 150-word Article target at 149 words.
- The active build-locality gate reports no active `dataless` blockers.

## Remaining External Gate

This QA does not replace journal portal preview. Fig. 2 still needs either:

- a completed `ncs_fig2_portal_preview_checklist.md` record showing that panel a is readable and the figure can be inspected at comfortable zoom, or
- a redesign using `ncs_fig2_redesign_contract.md` if the portal rasterizes the embedded figure or blocks source-file inspection.

The raw-source and public-release decisions remain governed by `raw_source_access_decision_worksheet.md`, `public_release_readiness_worksheet.md` and `submission_external_dependency_register.md`.
