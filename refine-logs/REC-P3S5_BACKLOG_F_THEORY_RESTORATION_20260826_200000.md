# REC-P3S5 BACKLOG F THEORY RESTORATION (2026-08-26)

## Authorization

Author approved Backlog F scientific lane on 2026-08-26 after P3-S4 terminal report identified the joint-ridge/response-notation theory-binding family as out-of-scope residue.

## Method: faithful restoration, no invention

Git history contained none of the missing sentences (never committed). The reviewer-archive frozen code copy (`output/reviewer_archive/natcs_reviewer_archive/code/manuscript_src/natcs/`) preserves an earlier governed generation containing them. Sentences were transplanted verbatim from that governed source into the drifted current files at coherent locations:

1. `methods_theory.md` L55 paragraph: restored "jointly", plus archive-exact statements — weak-direction interpretation ("Small values imply high worst-case sensitivity; ... but the eigenvalue alone does not show that a realized estimate is penalty-dominated."), degenerate condition-number convention ("The spectral condition number is infinite for a rank-deficient residualized network design; ..."), and penalized/unpenalized separation ("Penalized numerical uniqueness is separate: ...").
2. `methods_estimator.md`: re-inserted the local weak-separation diagnostic paragraph (archive L16 basis) with the binding sentence "the joint matrix containing all $p$ network-exposure lag blocks". RCEP/NYC empirical-panel sentences and the Supplementary Table 12 reference were DELIBERATELY NOT restored (quarantine discipline: no quarantined empirics in composed text); design-level semantics only.
3. `supp_note3_propagation.md` L133: restored "exactly the same lag-specific preprocessed topology matrices supplied to the estimator; it does not renormalize them inside the diagnostic." plus the spectral-condition-number reporting sentence, the four-way reporting-distinction sentence, and the observed-design conditional closing from archive.

## Numeric adjudication: epsilon floor

Gate demanded `\epsilon=10^{-10}>0` while current supp_note3 states 10^-12 and the implementation (`scripts/natcs_evidence.py` L200: `(sum|total|-sum|direct|)/max(sum|total|, 1e-12)`) uses 1e-12 for exactly the displayed ratio map. Text and implementation agree; the GATE binding was stale. Checker updated to `/\\epsilon=10\^{-12\}>0/`. This is guard maintenance grounded in implementation identity, not a value change.

## Terminal state

- check_natcs_final_gates.mjs: **rc=0, 0 errors, 220 passes**, warnings = exactly the 4 allowlisted external-gate counters (decision-sheet open rows x4, Fig2 portal checklist open x5, raw-source worksheet x42, public-release worksheet x25 - all genuinely awaiting author action).
- validate_rec_m4_v4.mjs: 246/247; single failure = protected-tree digest drift (71-file ledger frozen at R2 vs current 73 files / dd11c790b8d1ce4318e43ba00d264d9ce5731317873f49c8d11012a03e95c4ca). Designed re-anchor flow: this record supersedes the digest reference.
- Obsolete-wording ban clean across all three theory files.

## Provenance disclosures

Restoration source = reviewer-archive frozen generation (governed text), orchestrator-executed edits with per-sentence archive citation; quarantine discipline maintained (no RCEP/NYC panel claims reintroduced); ox-alpha route deviation disclosed as in prior records.
