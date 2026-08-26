# NCS Post-Acceptance Recovery Tracker Snapshot

Snapshot checkpoint: `2026-08-10T22:22:32+08:00`

| ID | Workstream | Priority | Dependency | Status | Go gate |
|---|---|---|---|---|---|
| REC-M0 | Final V1 and item payload refreeze | MUST / P0 | none | PASS | Register and four canonical payload hashes match |
| REC-M1 | Analyzer/test persistent rematerialization | MUST / P0 | M0 | PASS | Eight source/test files parse, compile, and fixture tests run |
| REC-M2A | Authorization-v2 compatibility repair and refreeze | MUST / P0 | M1 | PASS | Strict v2 binding, fixture tests, and repair receipt complete |
| REC-M2 | Four read-only derived reruns | MUST / P0 | REC-M2A | BLOCKED_PENDING_NEW_PREFLIGHT | A new preflight is required before any analyzer CLI |
| REC-M3 | V1-026/033/045 text and contract audit | MUST / P0 | M2 | BLOCKED | Waiting for REC-M2 |
| REC-M4 | Independent unified acceptance | MUST / P0 | M2, M3 | BLOCKED | Waiting for REC-M2/M3 |
| REC-M5 | Controlled manuscript update | MUST AFTER PASS | M4 | BLOCKED | Not authorized |
| OPT-S1 | E01 predeclared log-ratio/CI | OPTIONAL | M0 + author approval | DECISION_PENDING | Not part of REC-M2A |
| OPT-S2 | E02:128 independent truth | OPTIONAL / HIGH | M0 + author approval | DEFERRED | Not authorized |
| OPT-S3 | E02:135 stopping variants | RECOMMENDED OPTIONAL / P1 | M0 + author approval | DECISION_PENDING | Not authorized |
| OPT-S4 | E03 N=20/50 resource telemetry | OPTIONAL | M0 + author approval | DEFERRED | Not authorized |
| OUT-1 | N=100/200 extension | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | No experiment created |
| OUT-2 | RCEP/NYC activation | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | No activation |

## REC-M2A Evidence

- Repair authorization: `NCS_POST_ACCEPTANCE_RECOVERY_M2A_REPAIR_AUTHORIZATION_V1_20260810_222232.json`.
- Repair receipt: `NCS_POST_ACCEPTANCE_RECOVERY_M2A_REPAIR_RECEIPT_V1_20260810_222232.json` and `.md`.
- Authorization-v2 binding is direct and fail-closed for schema, current register SHA, canonical item hashes, frozen E4-r3 inputs, workspace authorization chain, REC_M2 scope, and current task limits.
- Eight-file compilation and 30 fixture/unit tests passed.
- No real analyzer CLI was invoked, and no REC-M2 scientific result was generated.

## Hard Boundary

REC-M2 remains BLOCKED_PENDING_NEW_PREFLIGHT. REC-M2A PASS is a source/test compatibility and evidence-freeze status only; it is not a scientific REC-M2 pass.
