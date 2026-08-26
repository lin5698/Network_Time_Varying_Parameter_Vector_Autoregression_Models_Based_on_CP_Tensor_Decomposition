# Figure 2 Portal Surrogate Audit

Status: **no portal surrogate run is authorised or recorded for the current source state as of 2026-08-26.** This audit is a submission-support artifact; it establishes no portal readability, validates no manuscript and supports no submission by itself.

Serves: rigour / clarity.

## Refusal Contract

The portal-surrogate generator operates fail-closed: it refuses before writing whenever either condition holds:

1. Either controlling audit (`PAPER_CLAIM_AUDIT.json` or `EMPIRICAL_IMPLEMENTATION_AUDIT.json`) is not releaseable at run time.
2. Either empirical Results source remains an explicitly inactive audit-boundary draft (`results_rcep.md` carrying its RCEP protocol marker, `results_generality.md` carrying its NYC protocol marker).

## Current Disposition Against The Contract

- Both controlling audits carry verdict PASS dated 2026-08-26 (`rcep_nyc_value_audited_no_active_stale_citations`, `rcep_nyc_value_audited_downstream_build_authorized`), so condition 1 is currently clear.
- Condition 2 stays engaged: both empirical Results sources keep their inactive markers with zero values present, exactly as required by the mode-gated template bindings and the build-side gate.
- With condition 2 engaged, the generator's refusal path remains active today. No fresh contact sheet, raster preview or surrogate summary JSON exists from a permitted run against the current sources.

A future surrogate run becomes permissible only after a releaseable source revision in which both inactive markers are deliberately and validably retired through the governance chain (RC-1 granted, touched RC-2 flags dispositioned, RC-3 review clean) and an independently audited figure build exists. Any such run would then constitute a narrow visual check of rendering fidelity alone — never evidence of scientific validity, claim accuracy or portal acceptance.

## Historical Assets

Historical contact sheets, raster previews and summary JSON files from earlier local builds may remain on disk for traceability. They were generated from superseded packages, may fail to correspond to current sources, and cannot establish portal readability or support submission under any circumstance. Treat them as identify-only artifacts: useful for lineage questions, void as QA evidence.

The authoritative preview-status record is `ncs_fig2_portal_preview_checklist.md` (explicitly disabled); the figure contract is `ncs_fig2_redesign_contract.md`; the one-screen companion summary for this audit is `ncs_fig2_portal_surrogate_summary.md`.

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
