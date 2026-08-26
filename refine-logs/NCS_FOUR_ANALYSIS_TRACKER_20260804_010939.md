# NCS 四项新增分析跟踪器

**快照时间**：2026-08-04 01:09 CST  
**模型**：`gpt-5.6-luna`  
**推理程度**：`max`

| Run ID | Register key | Task ID | Priority | Status | Scope |
|---|---|---|---|---|---|
| NCS-NA-001 | `CAL-E01:75` | `019fc899-672b-7970-989a-a43d3d3da142` | P0 | ACTIVE | comparator 完整性、paired 数值与 claim audit |
| NCS-NA-002 | `CAL-E02:128` | `019fc899-672c-7a70-87d8-0c4abef9072f` | P0 | ACTIVE | truth provenance、held-out design 与 leakage audit |
| NCS-NA-003 | `CAL-E02:135` | `019fc899-672b-7970-989a-a45bb511e8e3` | P0 | ACTIVE | overfitting/stopping-rule 跨 seed 与场景敏感性 |
| NCS-NA-004 | `CAL-E03:164` | `019fc899-672c-7a70-87d8-0c2a8d916073` | P1 | ACTIVE | cross-scale/stress、失败、稳定性与资源审计 |
| NCS-NA-AUDIT | all four | not created | P0 | BLOCKED_PENDING_RUNS | 四项均完成后创建独立统一验收任务 |

## 运行边界

- 四项均在独立 worktree 中运行，不共享可写输出目录。
- E4-r3 quarantine、稿件和 author decision register 均保持只读。
- 若 frozen records 不足，只允许建立新 protocol/candidate/pre-outcome freeze；不得事后补指标或复用 E4-r3 candidate。
- 当前 `promotion` 与稿件 claim 状态保持不变。
