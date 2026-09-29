# NCS Figure QA Memo

Date: 2026-08-26 status refresh of the 2026-07-26 QA records (previous memo update 2026-08-01).

Purpose: record source-level visual QA for the active Nature Computational Science figure sequence and its current governance posture. This is a working QA artifact, is not manuscript text and is not a portal or upload validation record.

Serves: visual communication / rigour / clarity.

## Governance Status for Figures

The controlling audits carry verdict PASS as of 2026-08-26, with reason codes `rcep_nyc_value_audited_no_active_stale_citations` (paper claims) and `rcep_nyc_value_audited_downstream_build_authorized` (empirical implementation). This authorizes the downstream rebuild chain alone. Manuscript-promotion authorization stays NOT_GRANTED (RC-1), empirical claim activation stays gated behind `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD` (RC-2), and rebuilt figures stay subject to post-regeneration review (RC-3). No figure in the active sequence carries any quarantined RCEP or NYC value; those lanes remain excluded from the active main-figure set.

## Active Sequence

| Figure | Reader question | Core evidence | Visual role | QA record |
| --- | --- | --- | --- | --- |
| 1 | What can the learned object return after fitting? | Separated blocks and supplied topology readouts | Callable-object hero | `ncs_figure1_python_redesign_qa_20260726.md` |
| 2 | When does the representation preserve a topology query? | Exact factorization boundary and diagonal inverse | Theorem/certificate hero | `ncs_figure2_python_redesign_qa_20260726.md` |
| 3 | Where is controlled numerical recovery supported? | Released target-matched N=15/N=30 comparison | Quantitative operating regime; strict qualification remains in Supplementary Note 4 | `ncs_figure3_python_redesign_qa_20260726.md` |

All three figures use Python/Matplotlib for drawing, export, preview and QA. Each exports editable SVG, PDF and 600 dpi PNG. The three SVGs contain editable text elements and zero embedded images. The sequence reads as one narrative with a single dominant reader question per figure; boundary evidence stays visually subordinate while explicit.

## Evidence and Claim Controls

- Figure 1 contains no numerical result; it defines the callable operator and the collapsed-map boundary.
- Figure 2 contains only the released Proposition 1, Corollary 1, their exact fixture derivations and the frozen endpoint-availability classification. Its contract lives in `ncs_fig2_redesign_contract.md`; portal-preview status lives in `ncs_fig2_portal_preview_checklist.md`.
- Figure 3 reads the released benchmark CSV and raw 20-replication summary only. The active empirical numbers are the controlled reductions 93.6% / 96.8% (effective-operator error) and 82.5% / 87.3% (finite-horizon unit-shock response error) at N=15/N=30. It does not read the held-out gate and plots none of its exact qualification counts; those counts remain in Supplementary Note 4, where they delimit claim inheritance without competing with the main visual advantage.
- Outside-target endpoints render as categorical dashes, never as zero errors.
- No panel claims estimator consistency, native held-out recovery, uncertainty calibration, cross-family transfer or application impact.

## Remaining Submission-Stage Check

When an authorized rebuilt manuscript exists after the downstream rebuild chain, inspect the embedded Figure 1-3 pages at final width and confirm that the standalone vector files stay selectable and zoomable. That upload-preview step has yet to occur; the portal-preview checklist remains explicitly disabled until a real preview event exists, and source-level QA never counts as evidence that a package is submission-ready.

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
