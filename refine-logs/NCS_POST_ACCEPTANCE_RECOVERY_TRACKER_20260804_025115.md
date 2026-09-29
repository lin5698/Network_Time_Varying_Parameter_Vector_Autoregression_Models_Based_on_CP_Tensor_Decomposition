# NCS 验收失败后的恢复跟踪器

**计划日期**：2026-08-04  
**状态基线**：统一验收 `FAIL 38/100`  
**Snapshot checkpoint**：`2026-08-04T02:51:15+08:00`

| ID | Workstream | Priority | Dependency | Status | Go gate |
|---|---|---|---|---|---|
| REC-M0 | 最终 V1 与四项 payload refreeze | MUST / P0 | none | PASS | 全文件与单项哈希同时通过 |
| REC-M1 | analyzer/tests 持久化重新物化 | MUST / P0 | M0 | PASS | 目标文件可发现、编译、fixture 执行 |
| REC-M2 | 四项只读派生重新运行 | MUST / P0 | M1 | BLOCKED | 本任务边界内未启动科学分析 |
| REC-M3 | V1-026/033/045 文本与契约审计 | MUST / P0 | M2 | BLOCKED | 等待 M2 |
| REC-M4 | 独立统一验收 | MUST / P0 | M2, M3 | BLOCKED | 等待 M2/M3 |
| REC-M5 | 受控稿件更新 | MUST AFTER PASS | M4 | BLOCKED | 未授权且等待 M4 |
| OPT-S1 | E01 predeclared log-ratio/CI | OPTIONAL | M0 + author approval | DECISION_PENDING | 找到完整 pre-outcome 定义 |
| OPT-S2 | E02:128 independent truth | OPTIONAL / HIGH | M0 + author approval | DEFERRED | fresh protocol 通过独立审查 |
| OPT-S3 | E02:135 stopping variants | RECOMMENDED OPTIONAL / P1 | M0 + author approval | DECISION_PENDING | fresh candidate/pre-outcome freeze |
| OPT-S4 | E03 N=20/50 resource telemetry | OPTIONAL | M0 + author approval | DEFERRED | fresh instrumented candidate |
| OUT-1 | N=100/200 扩展 | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | 不适用 |
| OUT-2 | RCEP/NYC activation | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | 不适用 |

## REC-M0 / REC-M1 evidence

- M0 receipt: `NCS_POST_ACCEPTANCE_RECOVERY_M0_REFREEZE_RECEIPT_20260804_023813.json`.
- Authorization v2: `NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json`.
- M1 receipt: `NCS_POST_ACCEPTANCE_RECOVERY_M1_RECEIPT_20260804_025115.json`.
- Eight analyzer/test files were reconstructed only from archived `patch_apply_end.changes`; all reconstructed bytes matched the in-memory ordered patch replay.
- `py_compile` passed and 17 read-only fixture/unit tests passed. No real analyzer CLI or formal scientific output root was run or created.
- Current formal register and E4-r3 results/manifest/completion/inventory SHA-256 values matched their M0 freeze after tests.

## Hard boundary

M2 remains blocked. Do not modify manuscript sources, register decisions, claim/promotion state, E4-r3 quarantine, RCEP/NYC, or S1-S4 without a later authorized stage.
