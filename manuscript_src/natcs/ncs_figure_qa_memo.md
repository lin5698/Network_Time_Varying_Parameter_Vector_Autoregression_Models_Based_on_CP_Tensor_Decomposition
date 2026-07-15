# NCS Figure QA Memo

Purpose: record the figure-level audit for the current Nature Computational Science-oriented package. This is a working QA artifact, not manuscript text.

Audit basis:

- Main manuscript PDF rendered to page PNGs in `tmp/pdfs/natcs_main`.
- Main figure exports:
  - `output/natcs_assets/figure1_natcs_framework.pdf/png/svg`
  - `output/natcs_evidence/fig_validation_recovery.pdf/png/svg`
  - `output/natcs_empirical_cp/rcep/figures/fig_rcep_operator_switch.pdf/png`
  - `output/natcs_empirical_cp/nyc_taxi/figures/fig_nyc_portability_summary.pdf/png`
- Figure captions in `output/submission_package/natcs_current/01_main_manuscript/main_manuscript.tex`.
- Fig. 2 redesign contract in `manuscript_src/natcs/ncs_fig2_redesign_contract.md`.
- Fig. 2 portal-preview checklist in `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`.
- Fig. 2 local surrogate-preview audit in `manuscript_src/natcs/ncs_fig2_portal_surrogate_audit.md`.

Boundary: this audit checks visual argument, final-PDF readability, source traceability signals and caption alignment. It is not a full production-prepress audit by the journal and does not verify Nature's final artwork portal requirements.

Main-figure scope update, 2026-07-11: Fig. 2 now limits its numerical comparisons to endpoint availability, unrestricted-local versus CP recovery, the CP/Tucker same-target preservation contrast, the collapsed-map ablation and the finite-horizon stability boundary. Projected graph-feature diagnostics, their numerical rows and mapping rules remain in Supplementary Note 4 and Supplementary Tables 1b-3, rather than appearing as a main-figure comparison. This reduces the risk that a common-readout diagnostic is mistaken for a native graph-learning ranking.

Local readability update, 2026-07-11: the regenerated manuscript PDF page containing Fig. 2, identified by the checked portal-preview reference and surrogate summary, was inspected at 1275 x 1650 px alongside the standalone Fig. 2 PNG/PDF/SVG exports. The endpoint gate, CP/Tucker contrast, collapsed-map boundary and stability panel remain visually distinct at page scale. Detailed labels still require zoom or standalone-file inspection. The appropriate response is to submit or retain the standalone PDF/SVG and redesign only if the journal portal rasterizes the embedded figure or does not allow comfortable zoom.

Local surrogate-preview update, 2026-07-07: `scripts/build_natcs_fig2_portal_surrogate.py` now regenerates low-width previews of standalone Fig. 2, the embedded manuscript page and panel-a crops for the endpoint-availability gate. The generated contact sheets and JSON summary are local QA evidence only; they do not replace the journal portal-preview checklist.

Final page-render spot check, 2026-07-07 14:00 build: the regenerated main manuscript PDF has 21 pages (`output/pdf/natcs_manuscript.pdf`; rendered pages in `tmp/pdfs/natcs_main`). Page-level inspection covered the current main-figure pages and adjacent text:

- Fig. 1 on `page-03.png` remains a true object-definition figure. It shows the topology-switchable operator, the three same-path readouts and the collapsed-map ablation before the benchmark section begins. Keep as the first Results figure. Serves novelty / clarity / visual communication.
- Fig. 2 remains logically correct and page-usable on the page identified by the checked portal-preview reference and surrogate summary. The endpoint-availability gate is visible and the caption states the N=15/N=30 headline boundary, N=50 bounded stress role, CP/Tucker preservation contrast and collapsed/no-network endpoint boundary. The new panel-a crop contact sheet isolates the fitted-object x endpoint matrix for upload-preview comparison. The smallest embedded labels still require zoom or standalone source inspection. Keep, with portal-preview confirmation. Serves rigour / clarity / visual communication.
- Fig. 3 on `page-07.png` remains the strongest empirical-boundary figure. Panel a dominates and separates fixed-path coefficient intervals from the re-estimated uncertainty layer, which helps prevent RCEP causal or policy overreading. Panel d is labelled as a descriptive Spearman diagnostic, not a mechanism or causal analysis. Keep as the RCEP main figure. Serves significance / rigour / clarity.
- Table 2 and the NYC section opening on `page-09.png` keep the fixed-path/re-estimated distinction and introduce NYC as a public second-domain operator check, not a second causal application.
- Fig. 4 on `page-10.png` remains appropriate as the bounded second-domain same-operator check. Panels a and b show near-overlap and near-null contrast, while panel c shows channel decomposition. The figure supports computability and reproducibility, not broad generality. Serves generality / reproducibility / visual communication.

## Figure Contract

Core conclusion: the manuscript's visual sequence should show that topology substitution is a query-preservation problem, validate endpoint recovery, then demonstrate bounded operator readouts in RCEP and NYC.

Target journal/output: Nature Computational Science Article; main manuscript has four figures and two tables, within the Article display-item target.

Backend: existing generated figures are Python/matplotlib outputs or generated vector schematic exports. This QA pass inspected existing exports and did not redraw figures.

Evidence hierarchy:

1. Fig. 1 defines the computational object and the tested collapsed-map target boundary.
2. Fig. 2 supplies the endpoint gate and benchmark recovery evidence.
3. Fig. 3 supplies the main empirical operator readout with uncertainty boundary.
4. Fig. 4 supplies a public second-domain same-operator check.

Reviewer risk: Fig. 2 carries the strongest benchmark evidence but is the densest figure in the final PDF preview. It should be supplied as a high-resolution standalone figure and checked carefully in the submission preview.

## Main Figure Audit

| Figure | Manuscript task | Archetype | QA outcome | Risk | Concrete fix or handling | Serves |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 1 | Define the topology-switchable operator and show that the tested collapsed object has no declared topology-switch endpoint. | Schematic-led composite | Pass. The page-level PDF preview remains readable; small matrix tiles are secondary visual texture, not evidence-bearing text. | Minor: PDF reports Type 3 math glyphs alongside embedded TrueType fonts. | Keep as main Fig. 1. If the submission system flags font editability, regenerate math labels with a unified sans/mathtext setting or submit the SVG/PDF source file separately. | novelty / rigour / clarity / visual communication |
| Fig. 2 | Establish endpoint availability before numerical recovery and show CP/local recovery, CP/Tucker preservation contrast, collapsed-map ablation and the stability boundary. | Quantitative grid | Pass with caution after local production-size audit. The standalone source figure is legible and panel a is visible in the manuscript page preview, but the smallest embedded labels are below comfortable print size. | Moderate: first-pass reviewers may miss outside-target labels or the N=50 bounded-stress annotation if they scan only the embedded PDF page. | Keep as main Fig. 2 because it is the core evidence figure. Submit or retain the standalone PDF/SVG figure source for zoom inspection. Redesign only if the journal portal rasterizes the page figure, blocks zoom, or makes panel a unreadable. | rigour / clarity / visual communication |
| Fig. 3 | Show RCEP fixed-path topology substitution, separate it from re-estimation uncertainty, and display bounded descriptive topology context. | Asymmetric quantitative composite | Pass. Panel a is rightly dominant because it carries the empirical boundary. Panels b/c support aggregate and GIRF readouts; panel d is an explicitly non-causal descriptive diagnostic. | Minor: caption must retain panel-d scope and interval definitions for standalone reading. | Updated caption defines fixed-path intervals, moving-block re-estimation intervals, bootstrap bands and panel-d's descriptive boundary. | significance / rigour / clarity |
| Fig. 4 | Test whether the same operator readouts compute in a public non-trade weighted network and can return a near-null contrast. | Asymmetric quantitative composite | Pass. The figure now reads as an operator check, not a second causal/domain study. | Minor: panel a/b uncertainty shading needed caption support. | Updated caption to state that shading gives pointwise bootstrap intervals for aggregate readouts. Keep as main only if the paper wants visible second-domain evidence; otherwise it can move to Supplementary without damaging the core method claim. | generality / reproducibility / visual communication |

## Source And Export Checks

| Check | Evidence | Status | Action |
| --- | --- | --- | --- |
| Main figure count | Integrity audit reports four figures and two tables. | Pass | Keep display-item count unchanged. |
| High-resolution PNG fallback | Main figure PNGs are 900 DPI for DOCX fallback; standalone Fig. 2 PNG is 1260 x 930 px and the page render containing Fig. 2 is 1275 x 1650 px. | Pass with Fig. 2 caution | Keep PNGs for DOCX fallback and use Fig. 2 PDF/SVG for reviewer zoom or portal source upload. |
| Vector exports | Fig. 1 and Fig. 2 have SVG/PDF. Fig. 3 and Fig. 4 have PDF/PNG. | Pass with note | For final production, consider SVG export for Fig. 3/4 if journal requests editable vector text. |
| Font embedding | Fig. 3/4 PDFs use embedded TrueType fonts; Fig. 1/2 include Type 3 glyphs from math/vector elements. | Pass with production caution | If artwork checks fail, regenerate Fig. 1/2 with Type 42/mathtext settings or submit SVG. |
| Caption statistics | Fig. 2 defines medians/IQRs; Fig. 3/4 now define interval/shading layers. | Pass | Rebuild package after caption edits. |
| Source-data traceability | Data availability and reviewer archive state that derived objects regenerate manuscript-facing figures and tables. | Pass | Keep traceability tables with the package. |

## Highest-Priority Figure Risk

The main remaining visual-communication risk is not the empirical panels. It is Fig. 2 density. The benchmark figure carries the NCS methods-reviewer argument, so the endpoint-availability gate must be visible even in a quick editorial scan. The local page render shows the endpoint gate and panel hierarchy, but secondary annotations are below comfortable print size after manuscript scaling.

Minimum fix before submission:

1. Inspect the journal upload preview after the DOCX/PDF files are uploaded.
2. Complete `ncs_fig2_portal_preview_checklist.md` using a portal screenshot or written upload-preview note; compare panel a with `fig2_panel_a_contact_sheet.png`.
3. Confirm Fig. 2 is selectable/zoomable as a standalone figure file.
4. If the preview rasterizes Fig. 2 at low resolution, upload `figure2_endpoint_preservation_benchmark.pdf` or `figure2_endpoint_preservation_benchmark.svg` from the figure-source package as an additional figure source file if the portal allows it.
5. Redesign Fig. 2 only if panel a is not readable in the portal preview or the standalone source file cannot be inspected by editors/reviewers.

Optional later improvement:

- Redesign Fig. 2 with a larger top endpoint gate and fewer lower panels, moving the stability boundary to Supplementary. This would improve visual communication but may weaken the compact all-in-one validation story.
- If the portal preview fails, use the minimum viable redraw protocol in `ncs_fig2_redesign_contract.md`: edit `scripts/build_natcs_evidence.mjs`, keep the endpoint gate plus N=15/N=30 operator recovery plus one topology-substitution endpoint panel, move full stress/stability detail to Supplementary, then rebuild and rerun the final gate.

## Reviewer Re-check

NCS senior editor:

- First impression: the visual story now starts from a computational object and does not open with RCEP.
- Likely concern: Fig. 2 may be visually dense in the embedded manuscript.
- Key fix: ensure the standalone Fig. 2 file is available and legible.

Computational methods reviewer:

- First impression: Fig. 2 is the decisive evidence because it separates endpoint availability from accuracy.
- Likely concern: graph-feature diagnostics could be misread as native forecasting benchmarks if placed beside the main recovery comparisons.
- Key fix: retain their mappings and fairness audit in Supplementary Note 4, while keeping Fig. 2 to same-target and endpoint-boundary evidence.

Temporal/complex networks reviewer:

- First impression: Fig. 3 and Fig. 4 are bounded readouts, not mechanism claims.
- Likely concern: topology diagnostics in Supplementary may still invite mechanism language.
- Key fix: keep diagnostics outside the main figures and labelled as descriptive level associations.

## Next Most Valuable Modification

If the portal preview fails, redesign Fig. 2 as a two-tier validation figure: a larger endpoint gate across the top half and a reduced set of recovery panels below. This would serve rigour, clarity and visual communication, but it requires careful preservation of the current benchmark evidence hierarchy.

The detailed redesign contract is recorded in `ncs_fig2_redesign_contract.md` and should be used only if the journal upload preview shows that the embedded Fig. 2 cannot be read comfortably at page scale.
