# NCS Figure QA Memo

Date: 2026-08-01 update to the 2026-07-26 QA

Purpose: record source-level visual QA for the active Nature Computational
Science figure sequence. This is a working QA artifact, not manuscript text.

Status: `PAPER_CLAIM_AUDIT=BLOCKED` and
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` remain unchanged. No full manuscript,
figure-source package or application build was run in this pass. RCEP, NYC and
the quarantined E4-r3 outcomes are excluded from the active main-figure
sequence.

## Active sequence

| Figure | Reader question | Core evidence | Visual role | QA record |
| --- | --- | --- | --- | --- |
| 1 | What can the learned object return after fitting? | Separated blocks and supplied topology readouts | Callable-object hero | `ncs_figure1_python_redesign_qa_20260726.md` |
| 2 | When is a topology query preserved by the representation? | Exact factorization boundary and diagonal inverse | Theorem/certificate hero | `ncs_figure2_python_redesign_qa_20260726.md` |
| 3 | Where is controlled numerical recovery supported? | Released target-matched N=15/N=30 comparison | Quantitative operating regime; strict qualification remains in Supplementary Note 4 | `ncs_figure3_python_redesign_qa_20260726.md` |

All three figures use Python/Matplotlib for drawing, export, preview and QA.
Each exports editable SVG, PDF and 600 dpi PNG. The three SVGs contain editable
`text` elements and no embedded images. The figure sequence is designed as a
narrative, not a dashboard: one dominant reader question per figure, with
boundary evidence visually subordinate but explicit.

## Evidence and claim controls

- Figure 1 contains no numerical result; it defines the callable operator and
  the collapsed-map boundary.
- Figure 2 contains only the released Proposition 1, Corollary 1, their exact
  fixture derivations and the frozen endpoint-availability classification.
- Figure 3 reads the released benchmark CSV and raw 20-replication summary. It
  does not read the held-out gate or plot its exact qualification counts. Those
  counts remain in Supplementary Note 4, where they delimit claim inheritance
  without competing with the main visual advantage.
- Outside-target endpoints are shown as categorical dashes, never as zero
  errors.
- No panel claims estimator consistency, native held-out recovery,
  uncertainty calibration, cross-family transfer or application impact.

## Remaining submission-stage check

When a future authorized manuscript build is available, inspect the embedded
Figure 1-3 pages at final width and confirm that the standalone vector files
remain selectable/zoomable. That upload-preview check is a later production
step; it is not evidence that the current blocked package is submission-ready.
