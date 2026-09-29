# NCS Final Author Decision Sheet

Status, 2026-08-26: **bounded submission preparation is authorized by governed records; upload stays gated on the open author confirmations listed below.** This sheet replaces the earlier disabled record under that record's own re-entry instruction, after both independent audits returned `PASS` on 2026-08-26 with reason codes in the `rcep_nyc_value_audited_*` family (`PAPER_CLAIM_AUDIT`: `rcep_nyc_value_audited_no_active_stale_citations`; `EMPIRICAL_IMPLEMENTATION_AUDIT`: same family).

## 1. Confirmed Decision Register

| ID | Item | Recorded decision |
| --- | --- | --- |
| D-1 | Independent audits | `PASS` for both audits, 2026-08-26; reason codes `rcep_nyc_value_audited_*`. |
| D-2 | RC-1, manuscript promotion | `NOT_GRANTED`. RCEP and NYC section drafts remain inactive audit-boundary drafts with template placeholders. |
| D-3 | RC-2, claim activation | Gated by `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD`, carrying the RCEP F1, F2 and F3 characterization flags together with the NYC characterization flags. The gate is evidential; no build-side defect is cited. |
| D-4 | Active empirical number set | Effective-operator error reductions of 93.6% and 96.8% (N=15, N=30) and finite-horizon unit-shock response error reductions of 82.5% and 87.3% (N=15, N=30) are the only active empirical numbers. Quarantined RCEP/NYC values stay outside active text. |
| D-5 | Title | "Predictive fit does not certify topology-indexed network responses". |

## 2. Positioning Guardrail For Upload-Time Edits

The editor-facing claim stays representation-level: query preservation for topology-substitution response queries is the contribution signal, the fitted object determines which such queries remain measurable after temporal smoothing, and CP remains the implementation layer. Every portal field, cover-letter paragraph and availability statement edited at upload time must preserve this framing; the final-gate positioning check fails any file that drops it.

## 3. Submission-Day Stop/Go Triage

| Signal | Action |
| --- | --- |
| All Section 4 rows closed and the package freshly rebuilt | Go: proceed with portal entry using the routing in 5.7. |
| Fig. 2 portal preview still unrecorded | Hold: keep the frozen package in place and schedule the preview. **Needs action** |
| New material proposes activating quarantined RCEP/NYC values | Stop: RC-2 gating stands; route the material through the characterization process, away from text edits. |

## 4. Open Items (author confirmation pending)

| # | Gate | Current state | Evidence that closes it |
| --- | --- | --- | --- |
| O-1 | Fig. 2 journal portal preview | No external portal observation on record; local surrogate stress checks exist. **Needs action** | Dated observation record in `ncs_fig2_portal_preview_checklist.md`. |
| O-2 | Raw-source access defaults | Conservative defaults prefilled in `raw_source_access_decision_worksheet.md`; author sign-off absent. **Needs action** | Signed-off worksheet row for each source block. |
| O-3 | Public-release record | Repository route, DOI, licence and access terms unassigned in `public_release_readiness_worksheet.md`. **Needs action** | Assigned-record confirmation at acceptance stage. |
| O-4 | Companion support documents | Governed support companions await upgrade from disabled stubs under backlog item A assignments. | Upgraded source files copied byte-identically into `03_submission_materials`. |

## 5. Post-Confirmation Update Checklist

Apply each branch that matches newly arrived evidence, in order, counting from the most recent freeze:

### 5.1 Fig. 2 portal preview passes

Archive the dated portal observation and screenshots in `ncs_fig2_portal_preview_checklist.md`, close its open markers, keep the frozen figure sources unchanged, then run the close-out step in 5.7.

### 5.2 Fig. 2 portal preview fails

Invoke `ncs_fig2_redesign_contract.md` (two-tier layout with an enlarged endpoint-gate panel), regenerate the figure set, refresh the figure-source package with contact-sheet and summary updates, complete a fresh page-render QA pass, then run 5.7.

### 5.3 Raw-source defaults are signed off

Transfer the dated sign-off into the worksheet record and leave Data availability wording exactly at the signed-off conservative level; this branch alone calls for no availability rewrite.

### 5.4 raw-source blocks gain confirmed reviewer or public access

Raise `data_availability.md` block by block to the confirmed access level, rerun the availability-consistency review against the worksheet, and treat the outcome as a formal-text edit under 5.6.

### 5.5 Public repository, DOI, licence and access terms are assigned

Insert the assigned identifiers and terms into `code_availability.md` and `data_availability.md`, keeping derived-evidence wording inside the overclaim bans (no raw-data-completeness assertion), and treat the outcome as a formal-text edit under 5.6.

### 5.6 Portal fields, title, abstract, cover letter or formal availability text are edited

Re-apply the Section 2 guardrail, take short portal fields from the length-limited variants in `ncs_portal_field_kit.md`, hold the abstract at 120-150 words with no TeX math, keep the cover-letter formula string `M_{k,t}(W)=A_{k,t}+B_{k,t}W` intact, and regenerate the generated formal texts so source and packaged copies match byte for byte.

### 5.7 Close-Out

After any branch fires: **Rebuild the package end to end and rerun final gates** — `make natcs-manuscript`; `node scripts/finalize_natcs_package.mjs`; `node scripts/create_clean_natcs_integrated_package.mjs`; `node scripts/create_natcs_upload_freeze_manifest.mjs`; `node scripts/check_natcs_final_gates.mjs`. The packaged twin of this sheet lives at `output/submission_package/natcs_current/03_submission_materials/natcs_final_author_decision_sheet.md` and must stay byte-identical to this source file.

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
