# NCS E4-R008 Duplicate/Claim-Fidelity Gate

**Date:** 2026-08-10  
**Gate:** `E4-R008`  
**Register key:** `CAL-E01:75`  
**Verdict:** `PASS`

The independent log-error-ratio/CI derivation is stored under two separate
content-addressed output roots:

- `refine-logs/ncs_new_analysis_v2/e4_r008_primary_final/cal-e01-75-c96e620006d55b14`
- `refine-logs/ncs_new_analysis_v2/e4_r008_duplicate_final/cal-e01-75-c96e620006d55b14`

The duplicate comparator found identical file inventories, content address and
artifact hashes. The claim-fidelity checks confirm that the derived metric is
artifact-only, the CI is descriptive, the evidence ceiling remains
`simulation_only`, and RCEP/NYC remain excluded.

Content address: `c96e620006d55b1459331c3ead28069920962ccf2df1a682030a37f47e97e635`  
Root inventory SHA-256: `6c3d32d806aaaaf4fdc9ceb72857d9de533ce5856c7ce455d74080f7e8de54ee`

The frozen E4-r3 result was not modified. Claim activation remains `BLOCKED`;
this gate wrote no manuscript or figure values. A separate activation decision
and sentence-level claim ledger are still required before any E4 value can
enter the manuscript or figures.

Machine-readable receipt:
`refine-logs/NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.json`
