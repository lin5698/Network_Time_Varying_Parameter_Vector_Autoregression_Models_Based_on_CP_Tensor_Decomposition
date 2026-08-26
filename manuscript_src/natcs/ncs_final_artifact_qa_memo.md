# NCS Final Artifact QA Memo

Status, 2026-08-26: QA baseline restated from governed records under backlog item A authorization; a fresh render-level pass is queued behind the next full rebuild. This edition supersedes the earlier dated QA memo, which remains retrievable from project history for traceability.

## 1. Carried-Forward QA Baseline (verified in governed records)

- Cover-letter extraction fix: the cover letter uses the plain-text formula string `M_{k,t}(W)=A_{k,t}+B_{k,t}W`, and prior plain-text DOCX extraction retained the full string.
- Build-locality hardening: macOS `dataless` placeholder detection runs across build and package tooling, and affected active resources were regenerated locally in the earlier cycle.
- Prior main-PDF page renders passed for the title/abstract opening, the Fig. 2 page (smallest embedded labels need zoom), the Fig. 3 page, the Table 2/NYC opening, the Fig. 4/Discussion opening and the references end page.
- Abstract stayed within the 150-word Article target with no TeX math.

## 2. Current Artifact State (2026-08-26)

| Artifact | QA state |
| --- | --- |
| Main PDF/DOCX | Valid as history; a fresh build is owed before any upload decision. |
| Supplementary PDF/DOCX | Same standing as the main documents. |
| Word-only upload directory and zip | Pending regeneration under the exact ten-DOCX set rule. |
| Figure-source package and zip | Pending refresh; manifest SHA-256 and byte parity required. |
| Release-safety outputs and upload freeze manifest | Pending generation after the clean integrated package exists. |
| Support-document twins in `03_submission_materials` | Pending byte-identical copies once stub upgrades finish. |

## 3. Open QA Gates

- Render-level QA pass over the next rebuilt PDF and DOCX set.
- Fig. 2 journal portal preview observation (external gate routed through the final author decision sheet).
- Post-rebuild recheck of abstract extraction phrases and the cover-letter formula string across the upload DOCX set.

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
