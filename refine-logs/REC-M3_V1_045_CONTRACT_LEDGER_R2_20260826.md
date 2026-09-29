# REC-M3_V1_045_CONTRACT_LEDGER_R2 (2026-08-26)

Class: `contract_ledger_r2` — supersedes `REC-M3_V1_045_CONTRACT_LEDGER_20260811.json` (baee769a51c5861b…) for locator/currency purposes only. All non-reanchored items inherited verbatim.

## Why

First regeneration of this generation shifted main.tex/supplementary.tex content positions (bounds-only validation had masked main-range drift into the reference section); M5-D G06/G07/G08 changed contract facts.

### V1-045-ALS
- locators: [{"file": "methods_estimator", "lines": "3"}, {"file": "contract", "lines": "27-38"}, {"file": "main", "lines": "636-646"}, {"file": "compiled_supplement", "lines": "451-457"}]
- note: compiled_supplement remapped 359-363/398-403 -> 451-457 (single consolidated description block); third old range 2784-2786 (application-layer iteration/tolerance parameters) no longer present in the regenerated 2169-line supplement and is dropped with this note; main 1102-1107 -> 636-646 (content-accurate re-measurement; prior bounds-only validity masked reference-section drift).
### V1-045-TOPOLOGY
- locators: [{"file": "methods_data", "lines": "11,13,15-25"}, {"file": "supp_note4", "lines": "19-23"}, {"file": "main", "lines": "554-562"}, {"file": "compiled_supplement", "lines": "893-899"}]
- note: compiled_supplement remapped 2409-2412 -> 893-899; main 497-501 -> 554-562 (content-accurate); methods_data locators extended to the G07 scenario table rows.
### V1-045-STABILITY
- locators: [{"file": "methods_uncertainty", "lines": "3"}, {"file": "main", "lines": "1000-1013"}]
- note: compiled_supplement entry DROPPED: the threshold statement is no longer part of the regenerated 2169-line supplement; declarations live in main.tex 1000-1013 (incl. G08 spectral-norm qualification sentence) and methods_uncertainty.md. Old main 1128-1132 -> 1000-1013.

## Protected-tree re-anchor

manuscript_src/natcs digest re-measured after authorized mutations: `822d72c2b198026952dd2556eeec1c3f465562466c47017d6897b510cbfd26b3` (71 files). Previous expectation: 21a1319b… / 72 files. File-count delta 72→71 predates this session's records and is recorded as observed, not explained.

## Provenance

ox-alpha orchestrator-measured against regenerated artifacts; authorization chain in JSON companion. No manuscript sources modified by this record.
