# NCS Submission Completion Audit

> **Current-status supersession, 2026-07-22.** This pre-audit completion record
> is historical QA only. It is superseded for every submission, empirical,
> reproducibility and figure-availability decision by `PAPER_CLAIM_AUDIT.md`
> (`BLOCKED`), `EMPIRICAL_IMPLEMENTATION_AUDIT.md` (`FAIL`),
> `ncs_desk_rejection_tracker_20260722.md` and
> `ncs_desk_rejection_rereview_20260722.md`. In particular, it must not be
> used to support an NCS resubmission, an upload, Figs. 3-4, Table 2,
> RCEP/NYC values, or a derived-evidence reproducibility claim. Its historical
> discussion of source-package architecture is retained only for traceability.

Purpose: requirement-by-requirement audit of the current Nature Computational Science-oriented package. This is a working strategy artifact, not manuscript text.

Audit date: 2026-07-07.

Literature-scope supersession, 2026-07-22: any historic references in this audit to sources outside the author-approved whitelist of Nature, Nature Reviews, Nature disciplinary journals and Nature Communications are excluded background. They must not set current NCS positioning, novelty wording or future literature tasks. The active positioning corpus is `nature_portfolio_2026_positioning_matrix.md`.

Primary audited materials:

- Source sections in `manuscript_src/natcs`: abstract, introduction, results, methods, discussion, cover letter, code/data availability and Supplementary notes.
- Generated package in `output/submission_package/natcs_current`.
- Integrated word-only upload archive: `output/integrated_package/latest_submission_upload_word_only.zip`.
- Main figure source archive: `output/figure_source_package/latest_natcs_main_figure_sources.zip`.
- Existing support audits: integrity check, scope boundary check, evidence support table, numeric evidence check, risk response table, reference strategy memo, figure QA memo, release-safety audit and external dependency register.

Boundary: this audit does not verify raw third-party data access, journal portal upload rendering, comparator-paper figure source files, or hidden peer-review expectations. It evaluates the visible package only. The four comparator-paper PDFs used in the reference strategy memo were accessible and checked on 2026-07-07.

Policy cross-check, 2026-07-07: Nature Portfolio guidance requires data/code restrictions to be disclosed at submission and data availability statements to state where and how supporting data can be accessed. The current package is aligned with that bounded position by separating submitted-evidence regeneration, fresh rerun modes and restricted raw-source acquisition. Author confirmation is still needed before strengthening any raw-source sharing claim.

Editor-facing positioning update, 2026-07-07: the generated editorial scope note was tightened to lead with endpoint availability after temporal regularization, then benchmark evidence, then bounded empirical operator readouts. Descriptive RCEP/NYC topology-correlation details were removed from the scope note so the first editorial read stays focused on the reusable computational object, not the application panels.

Submission-tone update, 2026-07-07: the generated editorial scope note was converted from a pre-submission inquiry letter into a submission-support scope memo. It now opens with the scope argument for the submitted Article and leaves originality, prior-discussion and competing-interest declarations to the formal cover letter.

Editorial-triage response update, 2026-07-07: `ncs_editorial_triage_response_pack.md` now gives evidence-bound answers to the most likely initial misreadings: trade-application framing, CP-as-novelty framing, native temporal-GNN benchmark framing, RCEP-causality framing, broad NYC generality and raw-to-derived reproducibility overclaim. It is a support artifact for portal fields and editor/reviewer queries, not new manuscript evidence.

Reference-strategy packaging update, 2026-07-07: `ncs_reference_strategy_memo.md` is now copied into `03_submission_materials`, recorded in `submission_inventory.json` and checked by `scripts/check_natcs_final_gates.mjs`. This keeps the PDF-verified comparator-paper architecture analysis available with the current package and protects the Stage 1/2 reference-pattern diagnosis from drifting out of sync with the source tree. It is a strategy artifact, not manuscript evidence.

Editorial first-screen audit update, 2026-07-07: `ncs_editorial_first_screen_audit.md` now audits the title, abstract sentence functions, cover-letter opening, portal snippets, desk-reject trigger claims and first-screen claim-evidence boundaries. It is a support artifact for submission QA and portal wording, not new manuscript evidence.

Portal-field kit update, 2026-07-07: `ncs_portal_field_kit.md` now gives paste-ready wording for short submission-system fields: novelty, significance, computational advance, evidence, boundary, reproducibility, a short editorial summary, field-specific variants and keywords. The kit keeps query preservation and the explicit topology-argument object ahead of RCEP, CP and raw-data claims, so portal wording remains aligned with the manuscript's evidence boundary.

Portal length-limit update, 2026-07-07: `ncs_portal_field_kit.md` now includes 150-character and 300-character variants for novelty, significance, computational advance, evidence, boundary and reproducibility fields. This reduces upload-time drift when the submission system imposes tight text boxes and keeps the short fields aligned with query preservation, bounded empirical evidence and derived-evidence reproducibility.

Portal length-limit gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now parses the length-limited portal-field table and verifies that the expected novelty, significance, computational-advance, evidence, boundary and reproducibility rows are present, with every 150-character variant at or below 150 characters and every 300-character variant at or below 300 characters. This catches upload-time first-screen wording drift before portal text is pasted.

Portal pasteable-wording gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now scans the paste-ready portal wording in `ncs_portal_field_kit.md`, including one-line fields, length-limited variants, the short editorial summary and field-specific "use this wording" cells while excluding the human-facing "avoid" column. The gate blocks public-DOI/raw-data/RCEP-causality/policy-effect/generalization/temporal-GNN overclaims and checks that the core novelty and editor-summary snippets foreground query preservation, endpoint preservation or the topology-switchable operator before CP/RCEP/application terms.

Portal pasteable-style gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now treats discouraged transition patterns in paste-ready portal snippets as blockers, including `rather than`, `since`, `however`, `therefore`, `not only` and compact `not ... but` constructions. This keeps the submission-system first screen direct and non-defensive, matching the manuscript's object-first NCS positioning.

Portal formula-sensitivity gate update, 2026-07-07: paste-ready portal snippets in `ncs_portal_field_kit.md` now avoid formula-dependent notation and describe the contribution as query preservation with an explicit topology argument. `scripts/check_natcs_final_gates.mjs` blocks formula-sensitive notation in those snippets so short submission fields remain readable in plain text, narrow web forms and editorial-preview systems. The formal operator equation remains available in the cover letter, Introduction and Methods.

Support response-snippet gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now applies the same overclaim, formula-sensitivity, object-first and direct-style checks to pasteable support snippets in `ncs_editorial_triage_response_pack.md` and `ncs_reviewer_recheck_matrix.md`. This prevents editor-query and reviewer-response wording from drifting back to formula-dependent, CP-first, RCEP-first, causal-policy, broad-generality or raw-reproducibility-overclaim language. The check targets only reusable snippets and does not block the formal operator equation in the manuscript, cover letter or claim-evidence tables.

Policy-identification boundary update, 2026-07-07: the abstract, Introduction, Discussion and cover letter now phrase the empirical boundary as `policy-effect identification` in place of a looser policy-effect object. The change keeps RCEP as fixed-path topology-sensitive measurement and reduces the chance that a domain reviewer reads the manuscript as claiming policy identification. It does not add empirical evidence or strengthen the RCEP claim.

Policy-boundary regression gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now treats loose policy-causality wording in formal manuscript-facing files as forbidden overclaim patterns. This preserves the fixed-path topology-measurement boundary after future edits to the abstract, Introduction, Discussion, cover letter or generated formal end matter.

First-screen positioning gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now checks that the title remains object-first and that the abstract and cover letter name query preservation, endpoint preservation or the topology-switchable operator before CP, RCEP or application terms. This turns the current NCS positioning into a regression check so later edits cannot silently return the package to CP-first or RCEP-first framing.

Abstract-length regression gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now checks that the source abstract remains within the 150-word Article target using the same math-stripping word-count logic as the generated integrity audit. The first-screen audit now records the abstract as nine short sentences and under target, avoiding stale fixed word counts after small wording changes.

Support-file sync gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now compares SHA-256 hashes for copied author-support files between `manuscript_src/natcs` and `output/submission_package/natcs_current/03_submission_materials`. This catches stale submission-support packages after edits to portal wording, author action sheets, first-screen audits, availability worksheets, figure QA notes or submission checklists.

Formal end-matter sync gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now compares source formal text in `manuscript_src/natcs` with the generated submission-material files for the cover letter, Data availability, Code availability, author contributions, competing interests, ethics statement and AI-use statement after the same reader-facing text normalization used by the manuscript builder. This catches stale generated end matter after source edits before an upload package is used.

Upload-DOCX end-matter sync gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now extracts plain text from the Word-only upload DOCX files for the cover letter, Data availability, Code availability, author contributions, competing interests, ethics statement and AI-use statement, and compares each file with the corresponding submission-material source rendered through the same Pandoc Markdown-to-plain path. This catches stale or unexpectedly transformed upload DOCX files after the text package has already passed source-to-generated sync.

Upload-DOCX abstract extraction gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now extracts the Abstract section from the upload-facing `main_manuscript.docx` and verifies that the first-screen topology-switchable-operator, separated-input, endpoint-availability and raw-to-derived-boundary phrases survive plain-text conversion. The gate also blocks TeX math in the source abstract and operator-dropout patterns such as `operator, .`, preventing submission-system or editorial-preview extraction from silently erasing the computational object.

Word-only upload-content gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now checks that `output/integrated_package/latest_submission_upload_word_only` and `latest_submission_upload_word_only.zip` contain exactly the expected ten DOCX files: main manuscript, Supplementary Information, references, cover letter, Data availability, Code availability, author contributions, competing interests, ethics statement and AI-use statement. This catches missing portal files, non-DOCX additions and accidental inclusion of support/private/debug materials before upload.

Residual-warning allowlist update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now allows only four final-gate warning families: open final-author action rows, unresolved Fig. 2 journal-portal preview markers, raw-source author sign-off markers and public-release author sign-off markers. Any additional warning is upgraded to a final-gate error so new release-safety, DOCX extraction, archive, language or package drift warnings cannot be hidden behind the `PASS_WITH_WARNINGS_ALLOWED` status.

Submission-package navigation update, 2026-07-07: the generated package README and submission-materials notes now separate upload-facing files from support artifacts. They point authors to the Word-only upload ZIP, figure-source ZIP, reviewer archive, portal-field kit, final author decision sheet and upload-freeze manifest in the intended order. The final checklist now directs authors to use the portal-field kit during short-field entry.

Reviewer re-check update, 2026-07-07: `ncs_reviewer_recheck_matrix.md` now simulates likely senior-editor, computational-methods, temporal/complex-networks, reproducibility and visual-reviewer re-checks after the current revision. It records major-revision triggers, evidence-bound response snippets and next minimal author materials; it is not new manuscript evidence.

Availability consistency update, 2026-07-07: `ncs_availability_consistency_audit.md` now checks the formal Data availability and Code availability statements against Nature/NCS availability expectations, current package evidence, unresolved raw-source gates and public-release gates. It is a support artifact for preventing overclaim during final edits, not new manuscript evidence.

Final-upload checklist update, 2026-07-07: the author-facing submission checklist was aligned with the current word-only package names, end-matter file split and figure-source package. The checklist now distinguishes text end-matter files in `03_submission_materials` from `.docx` files in the clean word-only upload directory, points to `natcs_integrated_submission_word_only_*` in place of superseded clean-package names, and records `latest_natcs_main_figure_sources.zip` as the standalone figure-source bundle.

Final figure-render update, 2026-07-07: the regenerated main manuscript PDF (`output/pdf/natcs_manuscript.pdf`, 21 pages) was inspected at page-render level for the four main-figure pages and adjacent text. Fig. 1, Fig. 3 and Fig. 4 pass their narrative roles. Fig. 2 remains logically correct and page-usable, with the known caveat that smallest embedded labels require zoom or standalone source inspection. The refreshed figure-source package is `output/figure_source_package/latest_natcs_main_figure_sources.zip`.

Figure-source package content gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now verifies that the main-figure source directory and `latest_natcs_main_figure_sources.zip` contain exactly the expected Figure 1-4 PDF/PNG/SVG exports, figure QA notes, Fig. 2 portal-preview notes, contact sheets, summary JSON, README and manifest. It also checks that the manifest lists the expected four figure IDs and that every manifest SHA-256 and byte count matches the packaged file. This catches missing source formats, stale visual QA notes and manifest drift before upload or reviewer inspection.

Raw-source decision-gate update, 2026-07-07: the raw-source access worksheet now includes a submission gate, decision-to-text map and final author sign-off table. This keeps the current Data availability statement conservative unless authors confirm stronger reviewer sharing, public-route or replacement-script decisions for each source block.

Fig. 2 portal-preview gate update, 2026-07-07: `ncs_fig2_portal_preview_checklist.md` now defines pass/fail criteria for the only unresolved main-figure visual gate. The checklist records local evidence, a portal upload procedure, standalone Fig. 2 PDF/SVG routes, required portal observations, screenshot naming conventions, a dated preview-note template, decision rules and author sign-off fields without claiming that the journal portal has passed the figure.

Fig. 2 local surrogate-preview update, 2026-07-07: `ncs_fig2_portal_surrogate_audit.md` and the generated `fig2_portal_surrogate_contact_sheet.png`, `fig2_panel_a_contact_sheet.png` and JSON summary now record local low-width preview stress checks for standalone Fig. 2, the embedded manuscript page and the panel-a endpoint gate. This reduces redesign-decision ambiguity but does not close the journal portal-preview gate.

Public-release planning update, 2026-07-07: a public-release readiness worksheet was added for the acceptance-stage DOI-minting release. It records repository-route, licence, release-content, exclusion, pre-deposit audit and text-update decisions without claiming that a DOI or public repository already exists.

External-dependency register update, 2026-07-07: `submission_external_dependency_register.md` now consolidates the three remaining non-source-tree gates: Fig. 2 journal portal preview, raw-source access/helper-code decisions and acceptance-stage public DOI release. The register maps each gate to the evidence needed before any manuscript wording can be strengthened and records the conservative default when evidence is absent.

Worksheet prefill update, 2026-07-07: the raw-source access and public-release readiness worksheets now include prefilled conservative defaults, current-package evidence snapshots and author confirmation prompts. These additions do not strengthen Data availability or Code availability claims; they reduce the final author-signoff work needed to decide whether any source block, repository route, licence or embargo can be stated more specifically.

Final artifact QA update, 2026-07-07: `ncs_final_artifact_qa_memo.md` records page-level inspection of the revised main PDF and Word-only upload artifacts. The QA found and fixed a cover-letter DOCX extraction risk by changing the cover-letter operator from a Word equation to a plain-text formula string. The main PDF pages inspected for the abstract, Fig. 2, Fig. 3, Table 2/NYC opening, Fig. 4/Discussion opening and references end page passed, with Fig. 2 retaining the known portal-preview caveat.

Final author-decision sheet update, 2026-07-07: `natcs_final_author_decision_sheet.md` now consolidates the remaining external gates into one author sign-off dashboard: Fig. 2 portal preview, raw-source access, RCEP helper boundary, acceptance-stage public release, reviewer archive freeze and final positioning language. It separates the local technical freeze, which is supported by the upload-freeze manifest, from the author upload-time confirmation that the frozen package was used without post-freeze edits. It does not close journal portal, raw-source, helper-code or public-release gates.

Coauthor action-request update, 2026-07-07: `natcs_coauthor_action_request.md` now gives a one-page request for the corresponding author, submitting author and data-owning coauthors. It lists the exact acceptable evidence needed for Fig. 2 portal preview, raw-source access, RCEP helper checkout, acceptance-stage public release, public-release safety, frozen upload use and final positioning guardrails. It is a support artifact and does not strengthen any manuscript claim by itself.

Upload-freeze manifest update, 2026-07-07: `natcs_upload_freeze_manifest.md/json` is now generated after the clean integrated upload package is created. It records SHA-256 hashes for the upload-facing manuscript artifacts, latest upload ZIP, stamped submission-upload ZIP, main figure-source ZIP, submission inventory and reviewer-archive manifest/README. The final gate checker verifies these hashes so later file drift is caught before upload.

Release-safety gate update, 2026-07-07: `ncs_release_safety_audit.md` documents the release-hygiene protocol, and `release_safety_audit.md/json` are generated into `03_submission_materials` before the upload-freeze manifest hashes the submission inventory. The final gate checker reruns the scanner in read-only mode and treats credential-like findings or sensitive filenames as blockers while allowing private-path warnings to remain reviewable. This gate serves reproducibility / rigour / clarity; it does not prove raw-source permissions, public DOI assignment, licence compatibility or legal redistributability.

Reviewer-archive integrity gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now verifies the separate reviewer reproducibility archive entry points: README, manifest, evidence and manuscript reproduction scripts, environment snapshots, restricted-data instructions, manuscript build scripts and the canonical/alias evidence maps. It checks that the reproduction scripts are executable, that the manifest records the default and 500-draw rebuild commands, that the raw-to-derived boundary note is present and that every file listed in the manifest checksum table exists and matches its SHA-256 hash. This supports the Code/Data availability claim that the archive is derived-evidence complete without claiming a raw-to-derived rebuild.

Evidence-map alias consistency gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now verifies that the local derived-evidence `evidence_support_map.json` and `claim_evidence_map.json` files and their two reviewer-archive aliases all exist and share the same SHA-256 hash. This prevents the support-map and claim-evidence-map aliases from drifting after evidence rebuilds or archive refreshes, strengthening the derived-evidence reproducibility boundary without expanding the raw-to-derived claim.

Build-locality hardening update, 2026-07-07: manuscript rebuilding exposed macOS `dataless` placeholder files in active manuscript sources, build scripts, Pandoc control files, figure outputs and package targets. The build scripts now treat such placeholders as unavailable local files instead of silently passing them to external tools. `scripts/build_natcs_manuscript.mjs` checks Pandoc image, bibliography, CSL and reference-document dependencies before conversion, clears figure targets before external renderers write them, and copies package artifacts by unlinking stale non-directory targets before writing. `scripts/build_natcs_evidence.mjs` treats `dataless` evidence objects as cache misses and clears known figure/output targets before re-generation. `scripts/build_natcs_reviewer_archive.mjs` and `scripts/finalize_natcs_package.mjs` use the same unlink-before-copy pattern for reviewer and submission-package synchronization. This hardening improves local rebuild reliability and reviewer reproducibility diagnostics; it does not add data, change estimates or expand the raw-to-derived reproducibility claim.

Active build-locality gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now scans active manuscript sources, scripts, derived-evidence outputs, benchmark/empirical outputs, reviewer archive contents, submission materials, figure-source package files and upload-facing DOCX/ZIP artifacts for macOS `dataless` flags. The scan excludes historical `_archives`, Python `__pycache__`, `backup_before_*` folders and numbered duplicate files. Any active placeholder file is now a final-gate error, preventing stale cloud placeholders from passing the reproducibility/package check while keeping historical/cache noise outside the submission boundary.

Release-safety and inventory consistency update, 2026-07-07: `scripts/audit_natcs_release_safety.mjs` now writes `release_safety_audit.md/json` into the submission materials and supports a read-only `--check` mode for the final gate. `scripts/build_natcs_manuscript.mjs` records these generated files in `submission_inventory.json`, and `scripts/finalize_natcs_package.mjs` runs the scanner before inventory validation. This closes the package-consistency gap in which generated release-safety files existed but were not part of the inventory checked before freezing. The scanner is pattern-based: zero blocker findings support release hygiene, not legal redistributability or raw-source permissions.

Representation-level first-screen wording update, 2026-07-07: the cover letter, portal-field kit, editorial-triage pack and reviewer re-check matrix now use the same editor-facing claim that the NCS fit is representation-level. The shared wording says that the fitted object determines which topology-substitution response queries remain measurable after temporal smoothing. This strengthens first-screen positioning without adding evidence, changing empirical claims or expanding the raw-to-derived reproducibility boundary.

Author-facing positioning guardrail update, 2026-07-07: the final author decision sheet, coauthor action request, submission checklist and editorial first-screen audit now require the representation-level query-preservation positioning to be preserved during upload-time edits and portal-field entry. This adds a positive positioning check alongside the existing overclaim guardrails; it does not change manuscript evidence, empirical interpretation or availability statements.

Representation-level regression-gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now blocks drift in the representation-level query-preservation position across the cover letter, generated cover letter, portal-field kit, editorial-triage pack, reviewer re-check matrix, final author decision sheet, coauthor action request and submission checklist. The check protects the editor-facing claim that the fitted object determines which topology-substitution readouts remain measurable after temporal smoothing. It does not add manuscript evidence or strengthen empirical, causal, generality or raw-reproducibility claims.

Response-ready paragraph update, 2026-07-07: `ncs_editorial_triage_response_pack.md` now includes a response-ready paragraph bank for editor fit, comparator scope, RCEP interpretation boundary, reproducibility boundary and Fig. 2 readability. These paragraphs are intended for portal notes, editor queries or reviewer-response drafts. They preserve the evidence boundary and do not add new claims.

Submission-day quick-decision update, 2026-07-07: the Fig. 2 portal checklist, raw-source worksheet and public-release worksheet now each contain a short submission-day decision table. These tables turn the long gate details into upload-time actions: keep or redraw Fig. 2, keep or strengthen source-block access wording, and keep future-tense or replace public-release wording. The tables reduce upload-time drift but do not close the external gates.

Stop/Go triage update, 2026-07-07: `natcs_final_author_decision_sheet.md` now begins the upload decision with a Submission-Day Stop/Go Triage table. It distinguishes conservative-package submission, hold for Fig. 2 preview, rebuild after Fig. 2 failure or post-freeze edits, and stop/revert if new wording adds unsupported raw sharing, DOI/licence, RCEP policy identification, broad generality or native graph-learning superiority claims.

Submission-checklist routing update, 2026-07-07: `submission_checklist.md` now directs the submitting author to apply the Stop/Go triage before continuing with rebuild and upload steps. This makes the author decision gate the entry point for upload rather than a separate support file that can be skipped.

Submission-package README routing update, 2026-07-07: `scripts/build_natcs_manuscript.mjs` now writes the Stop/Go triage route into the generated submission-package README and submission-materials notes. Authors who start from the generated package are directed to `natcs_final_author_decision_sheet.md` before choosing upload files, portal snippets or figure-source routes.

Submission-package navigation regression-gate update, 2026-07-07: `scripts/check_natcs_final_gates.mjs` now verifies that the generated submission-package README and `submission_materials_notes.md` retain the Submission-Day Stop/Go Triage route and point to `natcs_final_author_decision_sheet.md`. This prevents future build-script or package-text edits from silently bypassing the author Stop/Go decision gate before portal upload.

Post-confirmation closure-checklist update, 2026-07-08: `natcs_final_author_decision_sheet.md` now includes a Post-Confirmation Update Checklist for the six evidence-arrival branches most likely to affect submission integrity: Fig. 2 portal pass, Fig. 2 portal fail, conservative raw-source sign-off, strengthened raw-source access, assigned public repository/DOI/licence and edits to portal/formal wording. `scripts/check_natcs_final_gates.mjs` verifies that this checklist remains present in both the source and generated submission-material copies. This turns gate closure into an auditable package-sync workflow without claiming that any external gate has already closed.

Post-confirmation route update, 2026-07-08: the submission checklist, external-dependency register and generated package README/notes now point authors to the Post-Confirmation Update Checklist whenever new Fig. 2, source-access, DOI/licence or portal-wording evidence arrives after the last freeze. `scripts/check_natcs_final_gates.mjs` checks that the generated README and notes retain this route. This keeps late evidence handling tied to formal-text edits, package rebuilds, upload-freeze hashes and final-gate reruns.

Editorial-triage brief regression-gate update, 2026-07-08: the generated `scope_assessment_brief.md` now opens with query preservation and the topology-switchable finite-horizon operator, states representation-level query preservation as the novelty signal, and keeps CP as the benchmark implementation layer. `scripts/check_natcs_final_gates.mjs` verifies that this generated brief exists and preserves the NCS-fit anchor, evidence section, boundary section, reviewer-package section and key overclaim boundaries. This protects the editor-facing first-screen summary without adding new evidence.

Reviewer-archive README positioning update, 2026-07-08: `scripts/build_natcs_reviewer_archive.mjs` now writes a first-screen computational-target paragraph into the reviewer archive README. It states that the archive supports query preservation for topology-substitution responses, endpoint availability and recovery for the topology-switchable operator, and that CP is the benchmark implementation layer. `scripts/check_natcs_final_gates.mjs` verifies that the reviewer archive README preserves these anchors, the raw-data boundary and the graph-feature benchmark boundary. This protects the methods/reproducibility reviewer entry point without expanding the archive's raw-to-derived claim.

Reviewer-archive manifest target update, 2026-07-08: the reviewer archive `manifest.json` now includes a machine-readable `computational_target` block. It records the topology-switchable response operator, query-preservation claim, CP implementation boundary, derived-evidence review scope and excluded claims covering raw-data completeness, RCEP causal identification, native temporal-GNN forecasting, broad domain generality and latent-network recovery. `scripts/check_natcs_final_gates.mjs` verifies these fields so reproducibility metadata preserves the same NCS positioning and evidence boundary as the manuscript and README.

Reader-facing evidence-guide target update, 2026-07-08: `reader_facing_evidence_summary.md` now opens with a computational-target section and an evidence-boundary section. It directs reviewers to read the evidence as query preservation for topology-substitution responses, with endpoint availability before recovery scoring, CP as implementation layer and no claim to raw-data completeness, RCEP causal identification, native temporal-GNN forecasting performance, broad empirical domain generality or latent-network recovery. `scripts/check_natcs_final_gates.mjs` verifies these target and boundary phrases in both the local evidence output and reviewer archive copy.

Reader-facing summary-metrics scope update, 2026-07-08: `reader_facing_summary_metrics.json` now separates replicated N=15/N=30 benchmark gains from the N=50 bounded stress gain. The generator adds N=30-specific gain fields instead of reusing the legacy `baseline_large_*` fields, which refer to N=50 in `summary_metrics.json`. The reader-facing JSON also carries a `computational_target` block matching the Markdown evidence guide. `scripts/check_natcs_final_gates.mjs` verifies both local and reviewer-archive JSON copies, blocks ambiguous legacy gain fields and checks that N=50 does not enter the replicated N=15/N=30 effective-operator claim.

Reviewer-archive legacy-helper exclusion update, 2026-07-08: `scripts/build_natcs_reviewer_archive.mjs` now excludes the legacy `scripts/natcs_evidence.py` helper from the reviewer archive. The active reviewer path uses `build_natcs_evidence.mjs`, the manuscript-facing evidence tables, reader-facing evidence guide and evidence maps. The excluded helper contains superseded scenario names and older claim wording, so including it in the archive would invite claim-evidence drift. `scripts/check_natcs_final_gates.mjs` now fails if that helper reappears in the reviewer archive.

Reviewer-archive ZIP parity update, 2026-07-10: the active reviewer directory was clean, but the pre-existing `latest_natcs_reviewer_archive.zip` still contained an older snapshot with `natcs_evidence.py`. The archive builder now refreshes that canonical ZIP after every reviewer-directory build. The final gate checks ZIP integrity, exact file-set parity, per-file SHA-256 parity and absence of the legacy helper; the upload-freeze manifest records the ZIP itself. The exclusion predicate now matches the legacy basename exactly, so the transparent `build_natcs_evidence.py` wrapper may remain while the active evidence implementation stays `build_natcs_evidence.mjs`. This closes a delivery-artifact gap without changing manuscript results or claims.

Main Fig. 2 scope update, 2026-07-11: projected graph-feature numerical comparisons were moved out of the main figure and main Results validation narrative. Fig. 2 now centers the endpoint-availability gate, replicated CP versus unrestricted-local recovery, the CP/Tucker same-target preservation comparator, the collapsed-map ablation and the finite-horizon stability boundary. Supplementary Note 4 and Supplementary Tables 1b-3 retain the projection mappings, diagnostic numerical rows, coverage and fairness material. This reduces the chance that a common-operator projection diagnostic is mistaken for a native graph-learning ranking, without discarding evidence or changing any result.

Fig. 2 portal-reference update, 2026-07-11: rebuilding shifted the embedded Figure 2 from page 5 to page 6, while the upload checklist still cited the former page. The checklist now records the current rendered PDF page and `tests/test_fig2_portal_preview_reference.mjs` plus `scripts/check_natcs_final_gates.mjs` compare that reference against the current PDF caption location. This prevents a text reflow from directing submission-day inspection to the wrong page; it does not close the external portal-preview gate.

Main Fig. 3 caption-scope update, 2026-07-11: the RCEP figure has a visible panel d containing descriptive Spearman associations between the aggregate propagation index and topology summaries. Its caption and Results text now identify this panel explicitly, link it to Supplementary Figure 6 and Table 8, and state that it is an interpretive diagnostic rather than a mechanism or causal analysis. This closes a figure-caption-text mismatch without changing the diagnostic values or empirical claims.

Introduction contribution-scope update, 2026-07-11: the Introduction now treats topology re-evaluation after smoothing as specification-dependent and endpoint availability as a property to verify, rather than attributing that capability to a method family. It states the contribution as a testable reconstruction criterion that aligns the reconstruction target, availability check and finite-horizon evaluation for separable direct/network response operators with supplied topology arguments. A final gate protects these two anchors in both source and generated main text. This sharpens the NCS contribution without claiming that the operator algebra itself is new or changing any experiment, result or citation.

Historical and excluded under the 2026-07-22 literature scope: the following GVAR-precedent note is retained only to explain prior edits. It must not be used to set current positioning or novelty claims. GVAR precedent update, 2026-07-11: full-text review of Chudik and Pesaran's GVAR survey confirms that GVAR formulations can use time-varying trade weights and support scenario and impulse-response analysis. The Introduction now acknowledges that close precedent. The contribution is correspondingly limited to a reconstruction-level endpoint-availability test for fixed-path supplied-topology readouts, not to changing weights or impulse-response analysis alone. `scripts/check_natcs_final_gates.mjs` protects the acknowledgement together with the specification-level contribution boundary. This improves novelty discipline / rigour / clarity without changing estimates, figures or claims of comparative performance.

Preservation-wording precision update, 2026-07-10: implementation review confirmed that the CP stage applies standard CP-ALS reconstruction to the already separated direct/network coefficient tensor; it does not optimize an additional constrained objective. The abstract, benchmark Results, Supplementary estimator/scope text and submission-facing support snippets now call this an endpoint-preserving or block-preserving implementation. The representation contract, not the CP objective, is the preservation requirement. `scripts/check_natcs_final_gates.mjs` blocks constrained-optimization wording from returning to active manuscript and pasteable submission text. This improves methodological precision without changing the estimator, benchmark values or claims supported by the evidence.

Collapsed-map identifiability-boundary update, 2026-07-10: algebraic review showed that the earlier unqualified phrase "collapsed maps make topology substitution undefined" was too broad. Over unrestricted direct/network matrix blocks, the collapsed map is non-injective: $(A-HW_0,B+H)$ gives the same map at $W_0$ and a difference $H(W_1-W_0)$ at a new topology. Restricted block classes can admit recovery if an inverse and its identification conditions are explicitly supplied. Methods and Supplementary Note 1 now state both the non-injectivity result and this structured-inverse exception. The benchmark claim is correspondingly limited to the implemented collapsed ablation, which estimates no inverse and therefore places structural endpoints outside its declared target. This strengthens novelty / rigour / clarity without changing any experiment or numerical result.

Finite-horizon response-transfer theorem update, 2026-07-11, superseded by the 2026-07-18 proof audit: the earlier response-transfer statement was renumbered Proposition 2 after Proposition 1 was replaced by the exact single-topology query-factorization boundary. Proposition 2 now uses the spectral norm, an explicit integer horizon $H\geq1$, bounded true and reconstructed powers, a common shock map, and a spectral-norm companion-block corollary. Supplementary Note 3 supplies the telescoping proof and separates moving-average coefficients $\Phi_h$ from normalized responses $R_h=\Phi_hS$. The same note replaces the ordinary residualized-ridge display with the exact Schur complement of the implemented all-coefficient joint ridge objective and distinguishes penalized uniqueness from unpenalized design identification. The text explicitly excludes CP rank selection, CP-ALS global convergence, recovery improvement and empirical verification of the bounded-power assumption from the proposition; those are assessed separately. `scripts/check_natcs_final_gates.mjs` checks both propositions, the ridge identity, response notation and scope boundaries. These changes improve rigour / clarity without changing estimates or benchmark results.

Post-fix proof-contract update, 2026-07-18: an independent blind review found that the unrestricted Proposition 1 had been allowed to carry an unsupported application to the diagonal empirical estimator, that the displayed system conflated lag-specific estimation topology with report-date response topology, and that the weak-separation code reported an EPS-floor ratio as a condition number. The revision now pairs Proposition 1 with Corollary 1, an exact rowwise inverse and zero-row boundary for diagonal blocks under zero-diagonal topology. It explicitly states that the collapsed ablation does not apply this inverse rather than claiming mathematical non-identification. Rolling estimation uses $W_{\tau-k}y_{\tau-k}$, while response evaluation holds $\bar W_t=W_{t-1}$ fixed through the horizon. The estimator and diagnostic now share a data-independent exposure helper, rank-deficient Gram matrices return infinite spectral condition number, and production contract tests cover these boundaries. No R006e or R006f outcome was accessed or executed. These changes improve novelty / rigour / clarity / reproducibility without adding empirical outcomes.

## 1. Executive Verdict

Current verdict: the manuscript now reads much more like a computational-science methods/object paper than a results-reporting application paper. Its strongest NCS pitch is query preservation: topology substitution is treated as an endpoint-preservation problem for reconstructed dynamic-network response operators.

Largest remaining shortcoming: editorial breadth. A senior editor may still decide that the contribution is too narrow if the paper is read as "CP tensor smoothing for a trade application" instead of "a reusable topology-switchable response object for evolving weighted networks." The current text mostly controls this risk by making CP the implementation layer and the topology-indexed operator the contribution.

Current decision forecast based on visible materials: suitable for submission as a bounded NCS methods/object paper, with the main desk-reject risk concentrated in perceived generality, raw-source access constraints and Fig. 2 portal rendering.

## 2. Missing Information And Impact

| Material | Current status | Impact on NCS fit | Impact on novelty | Impact on rigour | Impact on reproducibility | Impact on figure narrative |
| --- | --- | --- | --- | --- | --- | --- |
| Title | Available. Current title: "Query-preserving topology-indexed responses in evolving weighted networks." | Supports object-level fit. | Signals the computational query before CP or application context. | Low impact. | Low impact. | Helps Fig. 1 anchor the story. |
| Abstract | Available and under the 150-word Article target. | Supports NCS framing. | Identifies query preservation and endpoint availability. | Quantitative claims are bounded. | States derived-evidence boundary. | Gives expected figure/evidence sequence. |
| Introduction | Available. | Strong, computational gap first. | Distinguishes query preservation from CP implementation. | States excluded mechanisms and policy-causality claims. | Low impact. | Aligns with Fig. 1/Fig. 2. |
| Results | Available. | Stronger after bounded Results organization. | Strong for endpoint-preservation object. | Benchmark and empirical readouts are bounded. | Medium impact through traceability. | Establishes problem -> object -> validation -> readouts. |
| Methods | Available. | Supports methods-paper fit. | Clarifies operating regime without claiming new CP theory. | Good: tuning, weak separation, stability and uncertainty are explicit. | Good for derived evidence; raw layer constrained. | Low direct impact. |
| Discussion | Available. | Clear, bounded NCS message. | "The contribution is query preservation" is visible. | Explicit limitations. | Low direct impact. | Reinforces figure boundary. |
| Main figures and captions | Available, four main figures. Final local page-render spot check completed for Fig. 1-Fig. 4; standalone figure-source package refreshed. | Strong sequence. | Fig. 1 supports novelty. | Fig. 2 supports rigour; smallest embedded labels need zoom/standalone inspection. | Fig. 4 supports same-operator reproducibility. | Residual risk: Fig. 2 portal rendering, not source-figure logic. |
| Supplementary | Available. | Supports depth expected for NCS. | Supports comparator scope. | Strong: benchmark grids, fairness, robustness, reproducibility. | Strong for derived evidence. | Moves diagnostics out of main line. |
| Code and data availability | Available. | Supports NCS trust. | Low impact. | Medium: reproduces evidence layer. | Good with raw-to-derived boundary. | Low impact. |
| Cover letter/significance statement and scope note | Available. Scope note now leads with endpoint availability and keeps empirical panels bounded. | Strong editor-facing pitch. | Emphasizes query preservation. | States boundaries. | Notes archive and reproducibility modes. | Low impact. |
| Target reference articles | Official Nature PDFs checked for the four comparator papers; production artwork/source files not available. | Supports article-architecture calibration. | Supports verified object-first and benchmark-first positioning lessons. | Supports Methods/Supplementary split calibration, but not hidden review expectations. | Low impact on current package. | Main figure count/order can be calibrated; typography/source-file imitation remains partial. |
| Journal portal preview | Missing; now tracked in `submission_external_dependency_register.md` and `ncs_fig2_portal_preview_checklist.md`. | Medium: formatting can affect first impression. | Low impact. | Low impact. | Low impact. | High for Fig. 2 readability. |
| Raw third-party data access proof | Externally constrained; now tracked in `submission_external_dependency_register.md` and the raw-source worksheet. | Low to medium. | Low impact. | Medium: raw-to-derived checks cannot be repeated by every reviewer. | High at raw layer; derived evidence is covered. | Low impact. |

## 3. NCS Fit Diagnosis

Classification: A, with bounded elements of B and C.

- A. New algorithm, model, tool or computational framework: yes. The framework is the topology-indexed response operator `M_{k,t}(W)=A_{k,t}+B_{k,t}W` and the endpoint-preservation contract.
- B. New scientific application: secondary. RCEP and NYC demonstrate operator readouts but are not the main contribution.
- C. Large-scale computational analysis: secondary. Benchmarks and empirical panels support the object but do not constitute a standalone discovery paper.
- D. Software/platform: no. There is a reproducibility archive, but the manuscript is not positioned as a software-system paper.
- E. Mainly domain application: current draft avoids this, but desk rejection risk returns if readers focus on RCEP before the operator.

Computational-science contribution: query preservation for topology substitution in evolving weighted networks. The manuscript argues that a reconstructed fitted object must keep direct coefficients, network coefficients and topology arguments separately evaluable, or provide an identified inverse that recovers the admissible separated blocks. The tested collapsed ablation provides neither and therefore leaves topology-substitution responses outside its target.

Is it only applying an existing method to new data? No, based on visible text. CP/PARAFAC is used as one implementation layer; the submitted claim is that the reconstruction target must preserve the response endpoint. This is broader than applying CP to RCEP.

Cross-problem reuse value: moderate to strong within a defined class. It applies to dynamic network models with separable direct/network response operators and supplied topology arguments. It does not cover nonlinear contagion, endogenous topology formation, latent-network recovery or task-optimized graph forecasting without new designs.

Does the scientific question require computation? Yes. The query requires evaluating the same fitted coefficient path under observed, zero-network and frozen-topology arguments while holding shocks and horizons fixed. That operation is unavailable if the fitted representation stores only a collapsed dynamic map.

Most likely NCS desk-reject reason: "The operator contribution is too specialized and the evidence is mainly a CP reconstruction benchmark plus a trade case study." Current mitigation: keep query preservation prominent in title, abstract, Fig. 1, Introduction, cover letter and significance statement.

## 4. Claim-Evidence Table

| Main claim | Supporting evidence in manuscript/package | Evidence strength | Risk | Required revision |
| --- | --- | --- | --- | --- |
| Topology substitution is an endpoint-preservation problem for reconstructed dynamic-network operators. | Abstract, Introduction, Fig. 1, Methods theory, Supplementary Notes 1-3. | Strong. | Underexplained if CP language takes over. | Keep "query preservation" visible in first and last paragraphs. Tags: novelty / clarity. |
| A topology-indexed operator `M_{k,t}(W)=A_{k,t}+B_{k,t}W` supports observed, direct-only and frozen-topology responses from one fitted path. | Fig. 1, Results framework, Methods propagation definitions. | Strong. | Could be read as notation only unless endpoint availability is emphasized. | Keep endpoint gate before numerical performance. Tags: novelty / rigour / clarity. |
| CP-network improves operator and GIRF recovery in replicated benchmark rows. | Abstract, Results validation, Table 1, numeric evidence check. | Strong for reported N=15/N=30 rows. | Overclaim if generalized to every metric/scenario. | Keep exact scope: replicated N=15/N=30 effective-operator and GIRF rows; N=50 as bounded stress. Tags: rigour / clarity. |
| The collapsed-map ablation leaves topology-substitution endpoints outside its target. | Fig. 1, Fig. 2 endpoint gate, Methods theory, Supplementary Note 1, evidence data dictionary. | Strong. | Keep the structured-inverse exception visible; do not generalize beyond the tested target. | Preserve target-boundary language in tables. Tags: novelty / rigour / visual communication. |
| Tucker supports the main same-target preservation stress test; projected graph-feature diagnostics remain supplementary under declared mappings. | Results validation, Figure 2, Supplementary Note 4, readiness/evidence tables. | Moderate. | Comparator fairness challenge if projection diagnostics are mistaken for native GNN rankings. | Keep projection diagnostics supplementary and label them as operator-protocol diagnostics, not GNN superiority. Tags: rigour / generality / clarity. |
| RCEP illustrates topology-sensitive fixed-path readouts. | Results RCEP, Fig. 3, Table 2, Supplementary robustness. | Moderate to strong as descriptive measurement. | Overclaim if interpreted as policy causality or directional aggregate effect. | Keep the window-wise perturbation interval crossing zero and the reconstructed-path stability monitor explicit. Tags: significance / rigour / clarity. |
| NYC Taxi is a public second-domain operator check with near-null aggregate topology contrast. | Results generality, Fig. 4, Supplementary Table 5, data availability. | Moderate. | Overclaim if called broad generality. | Keep "same-operator execution outside trade," not broad transfer. Tags: generality / reproducibility / clarity. |
| The package is reproducible from derived evidence objects. | Code/data availability, cleanroom reproduction check, manifest/checksums, upload package. | Strong for derived-evidence layer. | Raw-to-derived reproducibility is constrained. | Keep raw access/helper checkout boundary explicit. Tags: reproducibility / rigour. |
| Network diagnostics help contextualize propagation. | Supplementary topology summaries and correlation tables. | Moderate as descriptive context. | Mechanism overclaim. | Keep diagnostics in Supplementary and label as descriptive associations. Tags: clarity / rigour. |

## 5. First-Impression Risks

### Professional Editor

First impression: the current package has a credible NCS-facing object and a bounded abstract. It no longer reads primarily as a trade application.

Largest doubt: is query preservation broad enough for the journal readership?

Most likely requested addition: a sharper editor-facing paragraph explaining why topology-substitution endpoints matter across evolving weighted networks beyond RCEP and NYC, without adding unsupported domains.

Most likely text location to rewrite if needed: Introduction final paragraph and cover-letter significance paragraph.

### Computational Methods Reviewer

First impression: the endpoint gate, preservation ablation, tuning contract, weak-separation diagnostic and bootstrap layer make the methods reviewable.

Largest doubt: projected graph-feature rows are not native temporal-GNN or forecasting comparisons.

Most likely requested addition: a target-alignment/fairness table for comparator rows, with tuning, replication coverage, projection contract and endpoint availability.

Most likely text location to rewrite if needed: Results validation paragraph on projected graph-feature rows and Supplementary Note 4.

### Temporal / Complex Networks Reviewer

First impression: the manuscript now speaks to representation-dependent measurement in temporal networks and evolving weighted networks.

Largest doubt: topology diagnostics and RCEP interpretation could drift toward mechanism or policy claims.

Most likely requested addition: clearer statement that topology matrices are supplied exposure arguments, not learned topology laws of motion.

Most likely text location to rewrite if needed: RCEP Results and Discussion limitation paragraph.

## 6. Figure Narrative Audit

Current sequence: problem/object -> endpoint validation -> RCEP readout -> public second-domain operator check. This is the correct NCS order.

| Figure | Task in main line | Supports core claim? | Current status | Concrete recommendation |
| --- | --- | --- | --- | --- |
| Fig. 1 | Define topology-switchable operator and show the tested collapsed-map target boundary. | Yes: novelty and clarity. | Keep main. | Panels should continue to answer: what is stored, what changes under topology substitution, and whether an endpoint or inverse is declared. Tags: novelty / rigour / clarity / visual communication. |
| Fig. 2 | Establish endpoint availability and benchmark recovery under declared target scopes. | Yes: rigour. | Keep main with caution after local production-size audit. | Highest residual visual risk. The standalone source is legible, while the embedded page-scale labels require zoom. Use standalone PDF/SVG in the figure-source package and inspect journal upload preview. Redesign only if portal rendering makes panel a unreadable. Tags: rigour / visual communication. |
| Fig. 3 | Show RCEP fixed-path topology substitution and uncertainty boundary. | Yes, as bounded empirical readout. | Keep main. | Keep panel a dominant; captions must define fixed-path intervals, moving-block re-estimation and bootstrap bands. Tags: significance / rigour / clarity. |
| Fig. 4 | Show same-operator execution in public non-trade weighted network and near-null contrast. | Yes, for bounded generality and reproducibility. | Keep main if the paper needs visible second-domain evidence. | Do not describe as broad generalization. If space is squeezed, this is the only main figure that could move to Supplementary. Tags: generality / reproducibility / visual communication. |

Figures that are mostly diagnostic and should stay Supplementary: topology-structure correlations, perturbation summaries, stability exclusion/projection grids, full comparator grids and block-length sensitivity. Their role is risk control, not the main narrative.

## 7. Methods And Reproducibility Audit

Methods information that is adequately present:

- Data sources and construction: RCEP macro/trade/tariff/MRIO-derived inputs and NYC Taxi public tensor route are described.
- Preprocessing: quarterly allocation, lagged import-share matrices, row normalization, alternatives and public NYC monthly panel are described.
- Model and parameters: rolling window, lag order, ridge grid, selected penalties, CP rank grid, selected ranks, CP solver settings and bootstrap solver settings are reported.
- Evaluation: endpoint gate, effective-operator/GIRF errors, frozen-topology responses, projected graph-feature rows and replication boundaries are documented.
- Uncertainty: moving-block residual bootstrap, pair-cluster bootstrap, pointwise intervals and omitted hyperparameter-reselection uncertainty are stated.
- Diagnostics: weak separation, spectral stability, stable-date and stability-projected sensitivities are reported.
- Code/data: derived-evidence reproducibility, shell commands, manifest, checksums and raw-to-derived constraints are stated.

Methods material that should remain in main Methods:

- Operator definition and propagation recursions.
- Estimator contract and selected tuning protocol.
- Uncertainty and stability definitions.
- Data-source summary and reproducibility boundary.

Methods material that belongs in Supplementary:

- Full benchmark grids and comparator fairness/projection rules.
- Full validation surfaces and replication coverage.
- Full robustness, perturbation, stability and block-length sensitivity checks.
- Detailed acquisition notes for raw inputs.

Material that belongs in Code/Data availability:

- Reviewer archive content.
- Derived-evidence rebuild commands.
- Raw-to-derived access restrictions.
- DOI/licence statement on acceptance.

Residual reproducibility risk: the reviewer can inspect and regenerate manuscript-facing evidence from derived objects, but cannot fully rebuild every raw trade input without third-party access and helper checkouts. This must stay explicit. Tags: reproducibility / rigour.

## 8. Prioritized Revision Plan

### Must Fix Before Submission

1. Problem: Fig. 2 remains the densest main figure. Why it matters: methods-reviewer and editor first scan may miss the endpoint gate if the portal rasterizes the embedded page. How to fix: upload or retain standalone `figure2_endpoint_preservation_benchmark.pdf/svg`, complete `ncs_fig2_portal_preview_checklist.md`, and redesign only if panel a is unreadable or the source figure cannot be inspected. Tags: rigour / visual communication. Needs: journal upload preview or screenshot.
2. Problem: raw-to-derived reproducibility is constrained. Why it matters: NCS reviewers expect transparent computational artifacts. How to fix: keep derived-evidence rebuild as the claim, attach acquisition notes, and avoid claiming fully self-contained raw reproduction. Tags: reproducibility / rigour. Needs: author-confirmed raw input sharing/access statement.
3. Problem: broad generality could be overread. Why it matters: unsupported generality is a desk-reject or major-revision trigger. How to fix: maintain NYC as "public second-domain operator check" and state broad domain generality requires additional designs. Tags: generality / clarity. Needs: none unless adding new domains.

### Should Fix To Improve Review Outcome

1. Problem: projected graph-feature rows could be misread as native temporal-GNN benchmarks. Why it matters: methods reviewers may challenge fairness. Resolution: numerical rows and mappings are supplementary-only, while Fig. 2 contains endpoint and same-target evidence. Keep the comparator-fairness table and projection labels in Supplementary Note 4. Tags: rigour / clarity. Needs: none.
2. Problem: the contribution may feel narrow. Why it matters: NCS fit depends on reusable computational insight. How to fix: in cover letter and Introduction, keep one concise bridge to temporal-network representation choices and state the transferable criterion. Tags: novelty / significance / generality. Needs: no new data.
3. Problem: RCEP empirical section has attractive numbers that could invite causal reading. Why it matters: domain reviewers may object if policy causality is implied. How to fix: keep the moving-block re-estimation interval and stability boundary near the first RCEP claim. Tags: rigour / clarity. Needs: no new data.

### Could Improve If Space Or Time Allows

1. Problem: Fig. 2 is logically strong but visually compact. Why it matters: visual communication can shape editor confidence. How to fix: keep the current figure unless the portal preview fails; if it fails, redesign as two-tier figure with an enlarged endpoint gate on top, selected recovery panels below and stability details in Supplementary. Tags: visual communication / rigour. Needs: portal-preview evidence or figure-redesign time.
2. Problem: comparator-paper artwork calibration still lacks source files. Why it matters: detailed Nature-style typography, source-data packaging and final artwork conventions can affect production readiness. How to fix: use the PDF-verified article architecture already recorded, and rely on journal artwork checks or source-file examples only if available. Tags: clarity / visual communication. Needs: optional comparator figure source examples or journal artwork feedback.
3. Problem: raw pair-level contribution remains fragile. Why it matters: reviewers may probe fine-grained attribution. How to fix: leave raw pair-level evidence as diagnostic/secondary and avoid using it in the headline. Tags: rigour / clarity. Needs: none unless claiming pair-level reliability.

## 9. Suggested Positioning And Wording Moves

Title directions:

1. Query-preserving topology-indexed responses in evolving weighted networks.
2. Query-preserving response reconstruction for evolving weighted networks.
3. Endpoint-preserving propagation measurement in dynamic weighted networks.
4. Topology-substitution responses from reconstructed dynamic network operators.
5. Preserving topology-sensitive response queries in time-varying network models.

Recommended title: keep the current title unless the editor-facing package needs to foreground "query preserving."

Abstract structure:

1. Context: evolving weighted networks motivate response questions under changing exposure topology.
2. Computational gap: a collapsed dynamic map alone does not supply matched topology substitution; a structured inverse requires explicit identification conditions.
3. Approach: define `M_{k,t}(W)=A_{k,t}+B_{k,t}W` and preserve the endpoint.
4. Key evidence: benchmark gains and collapsed-map endpoint loss.
5. Empirical readout: RCEP and NYC demonstrate bounded operator outputs.
6. Implication with boundary: reproducible derived-evidence workflow; no causal topology/policy or broad generality claim.

Introduction final two paragraphs:

- Paragraph 1 should isolate query loss: the stored object must retain the blocks or an identified inverse to them for observed/frozen/direct-only matched readouts.
- Paragraph 2 should define the object, state "The contribution is query preservation," preview evidence and state exclusions.

Discussion first paragraph:

- Open with the object and its transferable criterion, not the application.
- State that topology-sensitive propagation becomes measurable only when the fitted path keeps the topology argument exposed.

Discussion limitation paragraph:

- Keep four boundaries together: predetermined topology, direct/network weak separation, finite-horizon stability and non-causal interpretation.
- Mention that both reconstructed paths remain inside the monitored unit-radius threshold, while retaining the distinction between that empirical monitor and the bounded-true-operator condition used in the response-transfer proposition.

## 10. Questions Needed Next

1. Can the raw trade, tariff, macro and MRIO inputs be shared with reviewers, or only acquisition notes plus derived evidence? Use `raw_source_access_decision_worksheet.md` to record the source-block decisions before changing Data availability language.
2. Will the Nature submission portal accept standalone figure source files for all four main figures, especially Fig. 2? Record the answer in `ncs_fig2_portal_preview_checklist.md`.
3. Do you want to prioritize a Fig. 2 redesign before submission, or keep the current figure and rely on the standalone source package?
4. Can you provide or obtain any journal artwork-preview feedback for Fig. 2, or should we proceed with the current standalone figure-source package?
5. Is the intended empirical claim strictly "bounded operator readout," or do any co-authors still want stronger RCEP policy language that must be removed or separately identified?

## 11. Requirement-To-Evidence Completion Matrix

| User-requested diagnostic step | Current completion | Evidence artifact | Remaining limit |
| --- | --- | --- | --- |
| Step 1 material sufficiency | Complete for visible package and PDF-verified comparator-paper architecture. | This audit; reference strategy memo; submission package inventory. | Raw-access proof and journal portal preview still missing. |
| Step 2 NCS positioning | Complete with boundary. | Introduction, significance statement, scope assessment brief. | Final editorial judgement uncertain. |
| Step 3 claim-evidence audit | Complete. | Evidence support table, numeric evidence check, this audit. | Depends on retaining bounded wording. |
| Step 4 first-impression risk | Complete. | Risk response table, this audit. | No actual editor feedback. |
| Step 5 figure narrative audit | Complete for current exports, including local Fig. 2 production-size readability audit. | Figure QA memo and figure source package. | Journal portal preview not yet checked. |
| Step 6 methods/reproducibility audit | Complete for derived-evidence workflow. | Code/data availability, cleanroom reproduction check, manifest references. | Raw-to-derived layer constrained. |
| Step 7 priority plan | Complete. | This audit. | Fig. 2 redesign optional unless preview fails. |
| Step 8 wording/positioning moves | Complete. | Reference strategy memo, current title/abstract/introduction/discussion. | Needs author choice on final title emphasis. |
