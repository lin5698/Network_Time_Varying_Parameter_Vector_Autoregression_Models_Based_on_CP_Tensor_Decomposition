# Figure 2 Portal Preview Checklist

Purpose: record the journal-upload preview decision for Main Figure 2. This is a working upload gate, not manuscript text.

Boundary: this checklist does not claim that the Nature Computational Science portal has accepted the figure. It defines the evidence needed before the external Fig. 2 gate can be marked as passed.

Serves: rigour / clarity / visual communication.

## Current Local Evidence

| Item | Current evidence | Interpretation |
| --- | --- | --- |
| Embedded manuscript page | Current local PDF page: `6`; rendered page `tmp/pdfs/natcs_main/page-06.png` is 1275 x 1650 px. The page number can change after text reflow and is checked by `tests/test_fig2_portal_preview_reference.mjs`. | The figure hierarchy and endpoint-availability gate are visible at page scale; secondary labels require zoom. |
| Standalone figure PNG | `figure2_endpoint_preservation_benchmark.png` is 1260 x 930 px. | Suitable for local preview and quick inspection. |
| Standalone figure PDF | `figure2_endpoint_preservation_benchmark.pdf` is one page, 945 x 697.5 pt. | Suitable for vector/zoom inspection if the portal accepts standalone source files. |
| Standalone figure SVG | `figure2_endpoint_preservation_benchmark.svg` is included in the figure-source package. | Suitable for editable/vector inspection if the portal accepts SVG. |
| Panel-a crop preview | `fig2_panel_a_contact_sheet.png` is included in the submission materials and figure-source notes after rebuild. | Local comparator for deciding whether the endpoint-availability gate remains readable after upload. |
| Current figure role | Fig. 2 carries the endpoint-availability gate, headline operator recovery, topology-substitution endpoint recovery and finite-horizon stability boundary. | This figure should remain in the main manuscript unless the portal preview makes the endpoint gate unreadable. |

## Submission-Day Quick Decision

Use this quick decision before final submission, then fill the detailed checklist below.

| Portal observation | Decision | Immediate action |
| --- | --- | --- |
| Panel a is readable in the uploaded manuscript preview at ordinary browser or PDF zoom, and the caption is adjacent and complete. | Keep current Fig. 2. | Record the pass in the Author Sign-Off table and retain the figure-source ZIP. |
| The embedded preview is small, but the portal accepts standalone Fig. 2 PDF/SVG and the source file is comfortably zoomable. | Keep current Fig. 2 with source-file inspection as the pass route. | Record the standalone route and keep the PDF/SVG in the uploaded or retained figure-source package. |
| Panel a is unreadable, blurred, clipped or detached from the caption, and no standalone source route is available. | Redesign Fig. 2 before submission. | Use `ncs_fig2_redesign_contract.md`, rebuild all packages and rerun the final gate. |
| The portal preview status is uncertain. | Do not mark the gate as passed. | Save a screenshot or written preview note, then decide using the pass criteria below. |

## Portal Upload Procedure

Use this order during the actual submission preview. The goal is to test the figure route that an editor or reviewer can inspect, beyond the local PDF.

1. Upload the required main manuscript file from the latest clean upload package.
2. If the portal accepts separate figure files, upload the standalone Fig. 2 PDF first and the SVG if SVG source files are accepted.
3. If the portal accepts only article files, open the uploaded manuscript preview and navigate to the Fig. 2 page.
4. Compare the portal panel-a view against `fig2_panel_a_contact_sheet.png`.
5. Save a full-page screenshot and, if possible, a panel-a crop using the naming convention below.
6. Record the decision in the author sign-off table before final submission.

Recommended file route:

| File to inspect or upload | Location in package | Use |
| --- | --- | --- |
| Standalone Fig. 2 PDF | `output/figure_source_package/natcs_main_figure_sources/figures/figure2_endpoint_preservation_benchmark.pdf` | Preferred zoomable/vector inspection route. |
| Standalone Fig. 2 SVG | `output/figure_source_package/natcs_main_figure_sources/figures/figure2_endpoint_preservation_benchmark.svg` | Editable/vector source if the portal accepts SVG. |
| Figure-source ZIP | `output/figure_source_package/latest_natcs_main_figure_sources.zip` | Backup route when the portal or editorial office accepts a source-figure package. |
| Panel-a comparator | `output/submission_package/natcs_current/03_submission_materials/fig2_panel_a_contact_sheet.png` | Local benchmark for the endpoint-availability gate. |

Do not mark the gate as passed from local files alone. The pass decision must come from portal preview readability, accepted standalone source inspection, or both.

## Portal Preview Pass Criteria

Mark the Fig. 2 gate as `Pass` only if all required criteria below are met.

| Criterion | Required observation in the journal portal | Pass / Fail / Not checked | Evidence to save |
| --- | --- | --- | --- |
| Embedded panel a readability | Panel a title and the fitted-object x endpoint matrix are readable in the uploaded manuscript preview at first view or with ordinary browser/PDF zoom. | Not checked | Portal screenshot showing Fig. 2 page. |
| Endpoint-gate logic | The viewer can distinguish available endpoints from outside-target endpoints in panel a. | Not checked | Screenshot crop or written preview note. |
| Panel-a local comparison | Portal panel-a screenshot is at least as readable as the local panel-a crop preview, or standalone source inspection is accepted. | Not checked | Compare against `fig2_panel_a_contact_sheet.png`. |
| Standalone inspection route | The portal accepts the standalone `figure2_endpoint_preservation_benchmark.pdf` or `.svg`, or the uploaded manuscript preview allows comfortable zoom. | Not checked | Upload confirmation or screenshot of attached figure source. |
| Caption alignment | The Fig. 2 caption remains adjacent to the figure and states that N=50 is bounded stress, Tucker is a same-target preservation comparator, and collapsed/no-network readouts have declared endpoint boundaries. | Not checked | Portal screenshot or extracted proof preview text. |
| No rasterization failure | The figure is not visibly blurred, downsampled or clipped in the portal preview. | Not checked | Portal screenshot at the default preview scale. |

## Decision Rules

| Portal outcome | Decision | Required action |
| --- | --- | --- |
| All pass criteria are met | Keep current Fig. 2. | Record the dated portal-preview pass in `ncs_figure_qa_memo.md` and `submission_external_dependency_register.md`. |
| Embedded figure is small but standalone PDF/SVG is accepted and zoomable | Keep current Fig. 2. | Record that the pass depends on standalone source inspection. Upload or retain the figure-source package. |
| Panel a is unreadable and no comfortable standalone inspection route exists | Redesign Fig. 2. | Use `ncs_fig2_redesign_contract.md`; rebuild manuscript and figure-source package; rerun page-render and zip checks. |
| Caption is detached, truncated or altered by the portal | Fix the upload package before submission. | Regenerate or re-upload the affected manuscript/figure file; do not mark the gate as passed. |
| The portal converts the figure to a blurred raster image | Redesign or upload vector source if allowed. | Prefer standalone PDF/SVG upload. If blocked, redraw with a larger endpoint gate. |

If redesign is required, use the "Minimum Viable Redraw Protocol" in `ncs_fig2_redesign_contract.md`. The fallback figure should keep the endpoint gate, N=15/N=30 operator recovery and one topology-substitution endpoint panel in the main figure, while moving full stress/stability detail to Supplementary. This preserves the methods-reviewer argument without adding new numerical evidence.

## Screenshot Naming Convention

Save portal evidence outside the manuscript text tree unless authors choose to include it in the support bundle.

- `fig2_portal_preview_page_YYYYMMDD.png`: full page preview showing figure and caption.
- `fig2_portal_preview_panel_a_YYYYMMDD.png`: crop showing panel a endpoint gate.
- `fig2_portal_source_upload_YYYYMMDD.png`: evidence that standalone PDF/SVG source was accepted.

## Dated Preview Note Template

Use this short note if a screenshot cannot be saved from the portal.

```text
Fig. 2 portal preview note, [YYYY-MM-DD]:
Uploaded file checked: [main manuscript PDF/DOCX or portal proof].
Standalone Fig. 2 route: [PDF accepted / SVG accepted / no standalone route].
Panel-a endpoint gate: [readable at first view / readable with ordinary zoom / not readable].
Outside-target cells: [distinguishable / not distinguishable].
Caption: [adjacent and complete / detached or incomplete].
Decision: [keep current Fig. 2 / redesign before submission].
Checked by: [name or initials].
```

## Author Sign-Off

Complete this table after journal upload preview.

| Item | Status: Pass / Fail / Unresolved | Author note |
| --- | --- | --- |
| Panel a readable in portal preview. | Unresolved | TODO |
| Outside-target endpoints distinguishable. | Unresolved | TODO |
| Standalone PDF/SVG accepted or manuscript preview zoom is comfortable. | Unresolved | TODO |
| Caption adjacent and complete. | Unresolved | TODO |
| Portal preview not blurred or clipped. | Unresolved | TODO |
| Final decision: keep current Fig. 2 or redesign. | Unresolved | TODO |

## Reviewer-Risk Interpretation

Strongest position: portal preview shows panel a readable and standalone PDF/SVG source files are accepted for zoom inspection.

Acceptable bounded position: embedded preview is small, but the standalone vector/PDF source is accepted and comfortably inspectable.

Weak position: the embedded manuscript preview is rasterized, panel a cannot be read and no standalone inspection route is available. In that case, Fig. 2 should be redesigned before submission because it carries the methods-reviewer evidence chain.
