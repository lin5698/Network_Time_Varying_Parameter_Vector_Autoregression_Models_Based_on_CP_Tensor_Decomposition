# NCS 四项新增分析跟踪器

| Run ID | Register key | Purpose | Frozen input | Priority | Status | Stop/Go note |
|---|---|---|---|---|---|---|
| NCS-NA-001 | `CAL-E01:75` | comparator 完整性与独立数值/claim audit | E4-r3 result + protocol + audit | P0 | DISPATCH_READY | 先做派生审计；不得激活 comparator superiority claim |
| NCS-NA-002 | `CAL-E02:128` | independent-truth、native held-out 与 leakage audit | E4-r3 result + candidate + source | P0 | DISPATCH_READY | 任何 provenance/chronology 缺口均阻断 broad native recovery |
| NCS-NA-003 | `CAL-E02:135` | 跨 seed/场景 overfitting 与 stopping-rule sensitivity | E4-r3 records + selection provenance | P0 | DISPATCH_READY | 缺 stopping variants 时只预注册新实验，不事后构造通过结论 |
| NCS-NA-004 | `CAL-E03:164` | cross-scale/stress reproducibility、failure、stability、resource audit | E4-r3 N=20/50 records + logs/manifests | P1 | DISPATCH_READY | 未运行 N=100/200 不外推；资源 telemetry 缺失必须显式报告 |
| NCS-NA-AUDIT | all four | 独立统一验收 | 四项 content-addressed outputs | P0 | BLOCKED_PENDING_RUNS | 四项完成后再派发；验收前不改 register 或稿件 |
