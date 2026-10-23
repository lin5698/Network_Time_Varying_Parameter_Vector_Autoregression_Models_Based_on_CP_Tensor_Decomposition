# NCS Submission Checklist

Status, 2026-08-26: rebuilt from governed records after both audits returned `PASS` (reason-code family `rcep_nyc_value_audited_*`). Each item names its evidence; tick an item only when that evidence exists.

## Completed, Evidence On Record

- [x] `PAPER_CLAIM_AUDIT` returns `PASS`; reason code `rcep_nyc_value_audited_no_active_stale_citations` (2026-08-26).
- [x] `EMPIRICAL_IMPLEMENTATION_AUDIT` returns `PASS`; same reason-code family (2026-08-26).
- [x] Active numeric discipline locked: 93.6% and 96.8% effective-operator error reduction (N=15, N=30); 82.5% and 87.3% finite-horizon unit-shock response error reduction (N=15, N=30); quarantined RCEP/NYC values stay outside active text.
- [x] Title set: "Predictive fit does not certify topology-indexed network responses".
- [x] RCEP and NYC sections contain only activated descriptive readouts with explicit characterization limits.
- [x] RC-1 is `ACTIVATED` and RC-2 is `ACTIVATED_WITH_LIMITATIONS`; RCEP F3 remains `not_identified`.
- [x] Author-decision support drafting under backlog item A covers this checklist, the final author decision sheet, the coauthor action request, the completion audit and the artifact QA memo.

## Open Before Any Upload — **Needs action** On Each Row

- [ ] Fig. 2 journal portal preview recorded in `ncs_fig2_portal_preview_checklist.md`.
- [ ] Raw-source access defaults signed off in `raw_source_access_decision_worksheet.md`.
- [ ] Public repository, DOI, licence and access terms assigned in `public_release_readiness_worksheet.md`.
- [ ] Remaining governed support documents upgraded from disabled stubs and copied byte-identically into `03_submission_materials`.
- [ ] Generated package refreshed: routing README and notes, 27-key `submission_inventory.json`, contact sheets, editorial triage brief, release-safety outputs and upload freeze manifest.
- [ ] Full rebuild chain executed with `node scripts/check_natcs_final_gates.mjs` green at the end.

## Positioning Guardrail During Portal Entry

Enter short portal fields with the representation-level claim first: query preservation for topology-substitution response queries, anchored in the fitted object, CP named as implementation layer. Take wording from the length-limited variants in `ncs_portal_field_kit.md`; never restate quarantined RCEP/NYC values as active results.

## Late-Evidence Rule

Fig. 2, raw-source, public-release or portal-wording evidence arriving after a freeze routes through the Post-Confirmation Update Checklist in `natcs_final_author_decision_sheet.md`, followed by a full rebuild chain and a final-gate rerun.

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
