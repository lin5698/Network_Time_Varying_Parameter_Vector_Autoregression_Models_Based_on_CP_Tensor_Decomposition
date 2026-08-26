# Figure 2 Portal Preview Checklist (Disabled)

Status: **no portal action is authorised** under this checklist. No journal portal preview of Figure 2 or of any manuscript page has occurred as of 2026-08-26, so every preview item below is recorded as Not checked. This file exists to keep that absence explicit and auditable.

## Why The Checklist Stays Disabled

The 2026-08-26 audit chain moved the controlling records to verdict PASS (reason codes `rcep_nyc_value_audited_no_active_stale_citations` and `rcep_nyc_value_audited_downstream_build_authorized`). That authorization releases the downstream rebuild chain alone. It grants none of the three things a portal preview would require:

1. Manuscript-promotion authorization remains NOT_GRANTED (RC-1), so there is no promoted manuscript version to preview.
2. Empirical claim activation stays gated behind `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD` (RC-2), so no rebuilt application evidence exists to appear beside the certificate figure.
3. Post-regeneration review (RC-3) has yet to run on any rebuilt package, so no reviewed artifact set exists to carry into an upload event.

A disabled checklist is the correct steady state while any of these conditions holds.

## Preview Record

| # | Preview item | Status | Evidence required to close |
| --- | --- | --- | --- |
| 1 | Figure 2 renders legibly at final upload width in the journal portal. | Not checked | Screenshot or written note from the actual submission event. |
| 2 | Certificate labels, panel letters and endpoint dashes survive portal rasterization. | Not checked | Same upload-event evidence, compared against the editable SVG/PDF sources. |
| 3 | Standalone vector files remain selectable and zoomable after upload. | Not checked | Portal-side inspection record or editor confirmation. |
| 4 | Page placement of Figure 2 matches the rebuilt manuscript version of record. | Not checked | Page reference from the uploaded build, recorded after RC-3 review closes. |

Historical page numbers, PNG crops and PDF/SVG renderings from earlier local builds are superseded. They are not current evidence, are not an upload route and must never be cited as proof that a Figure 2 review, manuscript build or Nature portal preview took place.

## Activation Preconditions

Before this checklist can activate, all of the following must hold:

1. Both controlling audits are independently releaseable at rebuild time, with reason codes current.
2. Manuscript promotion is separately authorized by the author (RC-1 granted).
3. Every characterization flag touching fragments displayed alongside Figure 2 is resolved or explicitly accepted (RC-2 closed for those fragments).
4. A fresh manuscript and standalone figure build has passed claim-to-evidence and visual review (RC-3 clean).
5. A real journal upload event exists, giving the preview record above genuine evidence to accept.

Until then, Figure 2 remains governed by the source-only contract in `ncs_fig2_redesign_contract.md`, and the pass/fail branches (`Fig. 2 portal preview passes` / `Fig. 2 portal preview fails`) stay reserved for the final author decision sheet once a preview event can actually be evaluated.

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
