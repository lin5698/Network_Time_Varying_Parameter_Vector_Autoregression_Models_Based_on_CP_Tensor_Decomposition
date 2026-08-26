# NCS 验收失败后的恢复跟踪器

**计划日期**：2026-08-04  
**状态基线**：统一验收 `FAIL 38/100`

| ID | Workstream | Priority | Dependency | Status | Go gate |
|---|---|---|---|---|---|
| REC-M0 | 最终 V1 与四项 payload refreeze | MUST / P0 | none | PASS | 全文件与单项哈希同时通过 |
| REC-M1 | analyzer/tests 持久化重新物化 | MUST / P0 | M0 | PASS | 目标文件可发现、编译、fixture 执行 |
| REC-M2 | 四项只读派生重新运行 | MUST / P0 | M1 | BLOCKED | 两次运行字节一致、coverage 完整 |
| REC-M3 | V1-026/033/045 文本与契约审计 | MUST / P0 | M2 | BLOCKED | sentence-to-evidence ledger 完整 |
| REC-M4 | 独立统一验收 | MUST / P0 | M2, M3 | BLOCKED | governance PASS，无 P0 failure |
| REC-M5 | 受控稿件更新 | MUST AFTER PASS | M4 | BLOCKED | source-only/release gates 通过 |
| OPT-S1 | E01 predeclared log-ratio/CI | OPTIONAL | M0 + author approval | DECISION_PENDING | 找到完整 pre-outcome 定义 |
| OPT-S2 | E02:128 independent truth | OPTIONAL / HIGH | M0 + author approval | DEFERRED | fresh protocol 通过独立审查 |
| OPT-S3 | E02:135 stopping variants | RECOMMENDED OPTIONAL / P1 | M0 + author approval | DECISION_PENDING | fresh candidate/pre-outcome freeze |
| OPT-S4 | E03 N=20/50 resource telemetry | OPTIONAL | M0 + author approval | DEFERRED | fresh instrumented candidate |
| OUT-1 | N=100/200 扩展 | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | 不适用 |
| OUT-2 | RCEP/NYC activation | OUT OF CURRENT SCOPE | explicit new approval | NOT_AUTHORIZED | 不适用 |

## 首轮建议派发

在用户批准执行后，按依赖分批创建任务：

1. **治理恢复任务**：REC-M0 + REC-M1。
2. **可复跑派生任务**：REC-M2。
3. **当前 V1 契约任务**：REC-M3。
4. **独立验收任务**：REC-M4。

`OPT-S3` 只在新的 exact-item 授权完成后另建任务；其余 optional lanes 不与恢复主线并行启动。

## 最新恢复 checkpoint

**Checkpoint**：`2026-08-04T02:51:15+08:00`  
**M0 receipt**：`NCS_POST_ACCEPTANCE_RECOVERY_M0_REFREEZE_RECEIPT_20260804_023813.json`  
**M1 receipt**：`NCS_POST_ACCEPTANCE_RECOVERY_M1_RECEIPT_20260804_025115.json`  
**Authorization**：`NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json`

- `REC-M0`: `PASS`. Register SHA, schema, item mapping and four canonical payload hashes matched.
- `REC-M1`: `PASS`. Eight source/test files were uniquely reconstructed from archived structured patch events; py_compile and 17 read-only fixture/unit tests passed.
- `REC-M2`: `BLOCKED`. No scientific analyzer CLI or formal content-addressed result root was started in this task.
- Frozen register and E4-r3 results/manifest/completion/inventory hashes remained unchanged after verification.
- Manuscript, register decision, claim/promotion state, RCEP/NYC and S1-S4 remain unchanged and unauthorized.
