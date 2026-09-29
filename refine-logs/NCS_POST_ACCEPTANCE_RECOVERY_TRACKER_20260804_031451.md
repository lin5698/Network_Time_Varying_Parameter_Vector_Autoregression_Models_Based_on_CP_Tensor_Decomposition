# NCS Post-Acceptance Recovery Tracker Snapshot

Snapshot checkpoint: `2026-08-04T03:14:51+08:00`

| ID | Workstream | Priority | Dependency | Status | Go gate |
|---|---|---|---|---|---|
| REC-M0 | Final V1 and item payload refreeze | MUST / P0 | none | PASS | Register and four canonical payload hashes match |
| REC-M1 | Analyzer/test persistent rematerialization | MUST / P0 | M0 | PASS | Eight files parse/compile and 17 fixture tests are recorded as passed |
| REC-M2 | Four read-only derived reruns | MUST / P0 | M1 | BLOCKED | v2 authorization must bind directly before any analyzer CLI |
| REC-M3 | V1-026/033/045 text and contract audit | MUST / P0 | M2 | BLOCKED | Waiting for M2 |
| REC-M4 | Independent unified acceptance | MUST / P0 | M2, M3 | BLOCKED | Waiting for M2/M3 |
| REC-M5 | Controlled manuscript update | MUST AFTER PASS | M4 | BLOCKED | Not authorized |
| OPT-S1 | E01 predeclared log-ratio/CI | OPTIONAL | M0 + author approval | DECISION_PENDING | Not part of blocked M2 |
| OPT-S2 | E02:128 independent truth | OPTIONAL / HIGH | M0 + author approval | DEFERRED | Not authorized in this run |
| OPT-S3 | E02:135 stopping variants | RECOMMENDED OPTIONAL / P1 | M0 + author approval | DECISION_PENDING | Not authorized in this run |
| OPT-S4 | E03 N=20/50 resource telemetry | OPTIONAL | M0 + author approval | DEFERRED | Not authorized in this run |
| OUT-1 | N=100/200 extension | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | No experiment created |
| OUT-2 | RCEP/NYC activation | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | No activation |

## REC-M2 Preflight Evidence

- Versioned preflight receipt: `NCS_POST_ACCEPTANCE_RECOVERY_M2_PREFLIGHT_20260804_031451.json`.
- Versioned preflight report: `NCS_POST_ACCEPTANCE_RECOVERY_M2_PREFLIGHT_20260804_031451.md`.
- Current register SHA-256: `c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2`.
- Current authorization schema: `ncs-four-analysis-authorization-v2`.
- Legacy authorization reuse: `false`.
- Real analyzer CLI invoked: `false`.
- Scientific output root created: `false`.
- Required raw frozen-input coverage rechecked structurally: 46,080 recovery, 48 recovery summary cells, 32 paired cells, 160 interval, 8 interval cells, 12,800 bootstrap.

## Hard Boundary

REC-M2 is blocked before analysis because the restored analyzers still require the legacy authorization schema and, in two analyzers, the legacy register hash. Do not modify manuscript sources, register decisions, claim/promotion state, E4-r3 files, RCEP/NYC, S1-S4, or N=100/200. A new preflight is required after the minimum source/test repair.
