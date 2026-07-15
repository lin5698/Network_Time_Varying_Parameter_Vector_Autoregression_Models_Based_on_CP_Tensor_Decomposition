# NCS Evidence-Aligned Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revise the current manuscript onto the evidence-supported representation/estimand route, resolve reproducibility conflicts, and rebuild a consistent submission package without inventing new results.

**Architecture:** Treat generated `main.tex` and `supplementary.tex` as build outputs. Scientific prose changes belong in `manuscript_src/natcs`; evidence calculations belong in the evidence and figure scripts; traceability belongs in new machine-readable ledgers. Rebuild only after source claims, formulas, and artifact metadata agree.

**Tech Stack:** Markdown manuscript sources, Node.js evidence/build scripts, Python/Matplotlib figures, JSON/CSV artifacts, LaTeX/PDF, Node/Python regression tests.

---

### Task 1: Freeze claim and run provenance

**Files:**
- Create: `manuscript_src/natcs/claim_evidence_ledger.csv`
- Create: `manuscript_src/natcs/empirical_run_manifest.json`

- [ ] Record every first-screen claim in the abstract, validation Results, empirical Results and Discussion.
- [ ] Map each claim to its exact experiment/artifact, scope, audit verdict and allowed wording.
- [ ] Record RCEP/NYC selected rank, ridge, window, lag, bootstrap settings and source artifact paths from `selection_summary.json`.
- [ ] Validate both files with standard CSV/JSON parsers and scan for missing required fields.

### Task 2: Unify the GIRF channel-share estimand

**Files:**
- Modify: `scripts/build_natcs_evidence.mjs`
- Modify: `scripts/build_nyc_portability_figure.py`
- Modify: `scripts/build_rcep_operator_switch_figure.py`
- Test: `tests/test_girf_network_share_consistency.mjs`

- [ ] Add a regression test requiring the point and bootstrap implementations to use `network_abs / (direct_abs + network_abs)`.
- [ ] Run the test and confirm that it fails against the current two-formula implementation.
- [ ] Introduce one named helper per runtime with the same mathematical definition and zero-denominator handling.
- [ ] Rebuild evidence and the RCEP/NYC figures.
- [ ] Run the regression test and numeric-alignment tests.

### Task 3: Revise reader-facing claims

**Files:**
- Modify: `manuscript_src/natcs/abstract.md`
- Modify: `manuscript_src/natcs/introduction.md`
- Modify: `manuscript_src/natcs/results_validation.md`
- Modify: `manuscript_src/natcs/results_generality.md`
- Modify: `manuscript_src/natcs/discussion.md`
- Modify: `manuscript_src/natcs/supp_note2_estimator.md`

- [ ] Separate endpoint definition, identification, recovery and finite-horizon stability in the abstract and Introduction.
- [ ] Scope the `N=15/N=30` values to the original controlled DGP and unrestricted rolling comparator.
- [ ] State that the later endpoint-aware gate did not validate broad native recovery; do not promote failed candidates.
- [ ] Describe RCEP as re-estimation-bounded and NYC as a near-null public computability check.
- [ ] Change the stale RCEP rank from 2 to the artifact-supported rank 1.
- [ ] Replace channel-share values only through regenerated evidence tokens, never by manual number selection.

### Task 4: Rebuild and verify the package

**Files:**
- Generated: `main.tex`, `supplementary.tex`
- Generated: `tmp/latex_build/main/main.pdf`, `tmp/latex_build/supplementary/supplementary.pdf`
- Generated: `output/natcs_empirical_cp/**/figures/*.pdf`

- [ ] Run the evidence builder.
- [ ] Run the manuscript builder and LaTeX build through the repository Makefile/scripts.
- [ ] Run targeted manuscript, figure and numeric-alignment tests.
- [ ] Run the final NCS gate and submission audit scripts.
- [ ] Render and inspect pages containing Figures 2-4 for label consistency and non-overlap.
- [ ] Report all remaining failures as open evidence gates rather than editing around them.
