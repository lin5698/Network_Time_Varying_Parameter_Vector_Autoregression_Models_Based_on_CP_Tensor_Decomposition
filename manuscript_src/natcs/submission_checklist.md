# NatCS Final Submission Checklist

Use this checklist only after the manuscript text is frozen for submission.

Before uploading, open `manuscript_src/natcs/natcs_final_author_decision_sheet.md` and apply the Submission-Day Stop/Go Triage table. If any Fig. 2, source-access, DOI/licence or portal-wording evidence has arrived after the last freeze, also apply the Post-Confirmation Update Checklist in that file. Continue only if the route is `Go with the conservative submission package` or if every required rebuild has already been completed and rechecked.

## 1. Rebuild the final package

- Run `node scripts/build_natcs_manuscript.mjs`.
- Confirm the refreshed outputs exist at `output/pdf/natcs_manuscript.pdf`, `output/doc/natcs_manuscript.docx`, `output/pdf/natcs_supplementary.pdf`, `output/doc/natcs_supplementary.docx`, `output/submission_package/natcs_current`, and `output/reviewer_archive/natcs_reviewer_archive`.
- After creating the clean integrated upload package, run `node scripts/create_natcs_upload_freeze_manifest.mjs` or `make natcs-upload-freeze-manifest` to freeze the exact upload-facing artifact hashes.
- Run `node scripts/check_natcs_final_gates.mjs` or `make natcs-final-gate-check`; treat errors as blockers and warnings as external author/portal gates to close or leave conservative.
- If a full evidence refresh is required, confirm `output/natcs_evidence/summary_metrics.json` reports `bootstrap_replications = 500`.

## 2. Check manuscript scope and claims

- Re-read `Abstract`, `Results > Synthetic benchmark`, `Results > RCEP case study`, `Results > Second-domain operator check`, and `Discussion`.
- Confirm the main claim remains query preservation for topology-substitution responses: the fitted object keeps the supplied topology argument evaluable after temporal smoothing.
- Confirm the recovery claims are limited to stable time-varying effective operators and GIRFs with an explicit lagged network block.
- Confirm the text states that raw pair-level network-contribution recovery remains difficult and scenario-sensitive.
- Confirm the RCEP application is framed as topology-sensitive measurement and decomposition, not policy identification.
- Confirm the NYC Taxi application is framed as a public second-domain check of the same operator readouts, not as a second policy or causal chapter.

## 3. Check citations and end matter

- Confirm the source tree contains `manuscript_src/natcs/references.bib` and `manuscript_src/natcs/nature.csl`, and no `references.txt`.
- Confirm there are no manual numeric citation strings such as `[1]` or `[2]` in `manuscript_src/natcs`.
- Confirm every citation key used in `manuscript_src/natcs/*.md` exists in `references.bib`, and every bibliography entry is either cited or intentionally retained with a note.
- Confirm `Abstract` and `References` are unnumbered in `main.tex`, while the main body sections remain numbered.
- Confirm `output/submission_package/natcs_current/03_submission_materials` contains the text end-matter files used to build the portal upload materials:
- `data_availability.txt`
- `code_availability.txt`
- `author_contributions.txt`
- `competing_interests.txt`
- `ethics_statement.txt`
- `ai_use_statement.txt`
- Confirm the clean word-only `submission_upload` directory contains the corresponding `.docx` files, including `data_availability.docx`, `code_availability.docx`, `author_contributions.docx`, `competing_interests.docx`, `ethics_statement.docx` and `ai_use_statement.docx`.

## 4. Check figures and tables

- Confirm Figure 1, Figure 2, and all empirical figures are available as PDF or SVG for LaTeX and as PNG for DOCX fallback.
- Confirm `output/figure_source_package/latest_natcs_main_figure_sources.zip` contains `figure1_topology_switchable_operator`, `figure2_endpoint_preservation_benchmark`, `figure3_rcep_operator_readout` and `figure4_nyc_operator_check` PDF/PNG exports, plus SVG exports where available.
- Confirm `output/natcs_benchmarks/benchmark_summary.csv` includes `network_component_error_*` and `frozen_counterfactual_error_*` columns.
- Confirm `output/natcs_evidence/table1_simulation_benchmark.csv` marks the collapsed-operator CP and low-rank no-network baselines as `Outside target` for network-component and frozen-topology tasks.
- Confirm `output/natcs_evidence/evidence_data_dictionary.md` states that `NaN` values in raw benchmark CSV files denote response definitions absent from that fitted object or not-applicable metrics and are rendered as `Outside target` in manuscript-facing tables.
- Confirm Results and Supplementary Note 4 explicitly distinguish reduced-form recovery targets from network-propagation targets so that the low-rank no-network comparator is not over-interpreted.
- Confirm the main-text benchmark figure uses only the `N=15`, `N=30`, and `N=50` scale baselines.
- Complete `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md` after journal upload preview. Confirm Fig. 2 panel a is readable at first view or allows comfortable zoom/standalone inspection of `figure2_endpoint_preservation_benchmark.pdf` or `.svg`; redesign Fig. 2 only if this check fails.
- Confirm the RCEP main-text figure is `figure3_rcep_operator_readout`, showing fixed-path topology substitution with the estimation-path boundary. Confirm descriptive topology diagnostics, coefficient robustness, the frozen/evolving ratio interval and representative GIRFs are retained in the Supplementary Information.

## 5. Check diagnostics and empirical defaults

- Confirm `output/natcs_empirical_cp/rcep/selection_summary.json` reports `bootstrap_replications = 500`, `cp_inits = 6`, and `cp_max_iter = 100`.
- Confirm `output/natcs_empirical_cp/rcep` contains `clipping_summary.csv`, `stability_summary.csv`, `stability_exclusion_sensitivity.csv`, and `block_length_sensitivity.csv`.
- Confirm the corresponding RCEP diagnostic figures exist in `output/natcs_empirical_cp/rcep/figures`.
- Confirm `output/natcs_empirical_cp/nyc_taxi/selection_summary.json` records the requested and effective rolling windows, and that the dataset-specific outputs live under `output/natcs_empirical_cp/nyc_taxi`.
- Confirm `output/natcs_evidence/table3_nyc_validation.csv` reports the NYC monthly implementation-check boundary, including effective window and instability rate.
- Confirm Supplementary Note 8 states the operating regime, diagnostic failure modes and interpretation boundaries, including the non-exhaustive temporal-GNN comparison boundary.

## 6. Check archive reproducibility

- Extract `output/reviewer_archive/latest_natcs_reviewer_archive.zip` into a clean temporary directory; confirm its contents match `output/reviewer_archive/natcs_reviewer_archive` before testing.
- Use the supplied evidence and manuscript reproduction entry points in that copy; confirm both complete successfully and regenerate the sanitized manuscript and SI.
- Confirm the archive copy contains the derived NYC Taxi monthly panel, validation table, acquisition notes, environment snapshot, manifest, checksums and shell reproduction entry points.

## 7. Manual editorial pass before upload

- Send or complete `manuscript_src/natcs/natcs_coauthor_action_request.md` before changing Fig. 2 status, Data availability, Code availability, public-release wording or portal-field claims.
- If any external gate status changed, apply the Post-Confirmation Update Checklist in `manuscript_src/natcs/natcs_final_author_decision_sheet.md` before editing formal text or uploading revised files.
- Confirm `manuscript_src/natcs/submission_external_dependency_register.md` reflects the final status of the Fig. 2 portal preview, raw-source access decisions and public DOI-release plan. If a gate is unresolved, keep the corresponding manuscript wording conservative.
- Use `manuscript_src/natcs/ncs_portal_field_kit.md` for short submission-system fields. Keep the representation-level query-preservation wording and do not write new CP-first, RCEP-first, raw-data-open or broad-generality wording during upload.
- Confirm the Fig. 2 preview evidence uses the pass/fail criteria in `manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md`, not an informal visual impression.
- Open the final PDF and DOCX and confirm title casing, line breaks, figure labels, and table captions look publication-ready.
- Confirm first-line indentation is present in body paragraphs in the DOCX output, while the title, abstract, figure captions, and table captions are not indented.
- Confirm the funding statement reads exactly: `Natural Science Foundation of Fujian Province, Project No. 2025J011145.`
- Confirm `Data availability` and `Code availability` describe the reviewer archive, lock files, shell reproduction entry points, manifest and acquisition notes in execution-ready language.
- Confirm `manuscript_src/natcs/raw_source_access_decision_worksheet.md` is either completed with author-confirmed source decisions or left unresolved with the current conservative Data availability wording unchanged.
- Confirm `manuscript_src/natcs/public_release_readiness_worksheet.md` records the intended DOI-minting repository route, release contents, exclusions and text-update rules, or leave the manuscript in future-tense "on acceptance" wording.
- Confirm the sentence `This study uses aggregate public or licensed data and did not involve human participants or animals.` appears in the end matter.

## 8. Upload set

- Upload the main manuscript PDF or DOCX required by the journal portal.
- Upload the supplementary PDF or DOCX required by the journal portal.
- Upload or retain standalone main figure source files when the portal permits it, especially `figure2_endpoint_preservation_benchmark.pdf` or `.svg`.
- Upload from `output/integrated_package/latest_submission_upload_word_only` or from the clean `submission_upload` directory inside the latest `output/integrated_package/natcs_integrated_submission_word_only_*` package, not from the full reviewer archive.
- If the portal accepts a ZIP upload for Word-only materials, use `output/integrated_package/latest_submission_upload_word_only.zip` after confirming `unzip -t` passes.
- Keep `output/figure_source_package/latest_natcs_main_figure_sources.zip` available for standalone figure-source upload or editor/reviewer zoom inspection.
- Retain `output/submission_package/natcs_current/03_submission_materials` as the support bundle; it contains evidence maps, compliance checks and readiness notes in addition to formal end-matter files.
- Keep the reviewer archive unchanged after the final clean-room check so that the archive matches the submitted manuscript version.
