# Fig. 2 Portal Surrogate Audit

Purpose: document a local, repeatable stress check for Fig. 2 readability before journal upload. This is a visual-communication support artifact, not manuscript text and not a substitute for the Nature submission portal preview.

Audit date: 2026-07-07.

Generated artifacts:

- Contact sheet: `output/natcs_fig2_portal_surrogate/fig2_portal_surrogate_contact_sheet.png`
- Panel-a contact sheet: `output/natcs_fig2_portal_surrogate/fig2_panel_a_contact_sheet.png`
- Summary JSON: `output/natcs_fig2_portal_surrogate/fig2_portal_surrogate_summary.json`
- Preview folder: `output/natcs_fig2_portal_surrogate`

Boundary: this audit uses local PNG exports generated after the manuscript build. It cannot prove how the journal portal will rasterize, crop, zoom or expose standalone source files. Do not mark the Fig. 2 portal gate as passed from this audit alone.

Serves: rigour / clarity / visual communication.

## Local Surrogate Inputs

| Input | Local source | Role | Boundary |
| --- | --- | --- | --- |
| Standalone Fig. 2 PNG | `output/natcs_evidence/fig_validation_recovery.png` | Tests the standalone source figure that reviewers should inspect when the portal permits source upload or zoom. | PNG preview does not replace PDF/SVG vector inspection. |
| Embedded manuscript page | Current Fig. 2 page recorded in `ncs_fig2_portal_preview_checklist.md` and the generated surrogate summary. | Tests the page-scale view that editors may see during quick PDF preview. | Local page render may differ from journal portal rendering. |
| Panel-a crops | `fig2_panel_a_contact_sheet.png` and panel-a preview files in `output/natcs_fig2_portal_surrogate` | Isolates the endpoint-availability gate from the full figure so the author can judge whether the fitted-object x endpoint matrix remains readable. | Crops are local evidence; portal screenshots are still required to close the gate. |

## Current Interpretation

The current strategy remains unchanged:

1. Keep Fig. 2 as the main benchmark figure if the portal keeps panel a readable or allows comfortable standalone PDF/SVG inspection.
2. Treat page-scale embedded readability as a first-screen risk because the smallest labels require zoom.
3. Use the standalone Fig. 2 PDF/SVG as the reviewer-facing inspection route when the portal allows separate figure-source upload.
4. Redesign Fig. 2 only if the portal rasterizes the figure at low resolution, blocks zoom or prevents standalone source inspection.

## What This Audit Adds

| Question | Local surrogate answer | Required author action | Tags |
| --- | --- | --- | --- |
| Is there a reproducible local preview of Fig. 2 compression risk? | Yes. The Python script `scripts/build_natcs_fig2_portal_surrogate.py` regenerates low-width standalone, embedded-page and panel-a crop previews. | Inspect the contact sheet and panel-a contact sheet before upload and keep them with the submission QA record. | visual communication / rigour |
| Does this close the journal portal gate? | No. It is a local surrogate only. | Complete `ncs_fig2_portal_preview_checklist.md` after portal upload. | rigour / clarity |
| Does this justify redesigning Fig. 2 now? | No, unless the local preview or portal preview shows panel a is unreadable and standalone inspection is unavailable. | Use `ncs_fig2_redesign_contract.md` only after a failed preview. | visual communication / clarity |
| Which claim depends most on Fig. 2 readability? | Endpoint availability before recovery scoring. | Keep panel a and the endpoint gate visually dominant in any redesign. | rigour / visual communication |

## Redesign Trigger

Redesign Fig. 2 if any of the following is true in the journal portal:

- panel a cannot be read at first view or comfortable zoom;
- standalone PDF/SVG upload is not accepted or cannot be inspected;
- the portal rasterizes Fig. 2 so that outside-target labels or endpoint-gate labels blur into the grid;
- the figure appears cropped, clipped or mismatched with its caption.

If none of these occur, keep the current Fig. 2 and use the standalone PDF/SVG source files for reviewer inspection.
