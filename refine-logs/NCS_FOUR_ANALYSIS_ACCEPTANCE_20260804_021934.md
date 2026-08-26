# NCS 四项新增分析统一验收

**Checkpoint**：`NCS-NA-AUDIT-20260804-021934-CST`  
**结论**：`FAIL`  
**评分**：`38/100`  
**独立验收任务**：`019fc8c4-0124-7a83-8b3c-12bc503ce1d2`，`gpt-5.6-luna`，`max`

## 阻断结论

1. 授权回执绑定的 register SHA 为 `3e1aa708...`，而任务启动时正式 V1 已变为 `c970d829...`；schema、priority 和 action class 同时发生变化。四个 exact key 仍存在，但授权输入身份未重新冻结。
2. 四份 session trace 能证明历史上曾创建 analyzer、tests、内容寻址输出并运行测试；但原 `df05/c71f/15b8/2f85` worktree 已不存在，主项目与当前 worktrees 中也找不到这些文件，当前无法读取或复跑。
3. E4-r3 冻结输入未被污染：results、manifest、execution-complete 与 inventory 哈希均匹配，promotion 仍为 `PROHIBITED`。这只能证明原始输入完整，不能替代四项派生产物的持久化与复核。

## Register 漂移

| Key | 当前 V1 item | 授权口径 | 当前正式 V1 |
|---|---|---|---|
| `CAL-E01:75` | `V1-026` | P0 / NEW_ANALYSIS | P0 / DIRECT_TEXT_REVISION |
| `CAL-E02:128` | `V1-033` | P0 / NEW_ANALYSIS | P0 / DIRECT_TEXT_REVISION |
| `CAL-E02:135` | `V1-035` | P0 / ROBUSTNESS_CHECK | P1 / NEW_ANALYSIS_OR_EXPERIMENT |
| `CAL-E03:164` | `V1-045` | P1 / NEW_ANALYSIS | P0 / DIRECT_TEXT_REVISION |

四项在当前 register 中仍为 `PENDING`，本次验收不改变该状态。

## 冻结输入

| Artifact | SHA-256 | Verdict |
|---|---|---|
| E4-r3 results | `09394a3c68a0babcc9cda7f704b78245553d61a40131e91ff1fc9157ece85032` | PASS |
| execution manifest | `42d2b2da3649c4cfb7f72060ba9ff0587f108f7609177c23d5f68fda1f9a536d` | PASS |
| execution complete | `18e7dc81acf8c75d53835bcc751d8f37a89645357d302349631dc86d839a775b` | PASS |
| terminal inventory | `5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046` | PASS |

保留 warning：execution manifest 仍写作 `RUNNING_QUARANTINE_ONLY`，completion marker 为 `COMPLETE_QUARANTINE_ONLY`；预声明 panel-level log-ratio/CI 未被序列化。

## 逐项 Verdict

| Register key | Verdict | 可保留的内部证据 | 仍阻断的结论 |
|---|---|---|---|
| `CAL-E01:75` | PARTIAL / BLOCKED | raw comparator coverage、32 个 paired raw-difference cells | log-ratio/CI、comparator superiority、当前复跑 |
| `CAL-E02:128` | PARTIAL / BLOCKED | simulation truth provenance、bounded native-gate evidence | independent empirical truth、leakage/split/endpoint provenance |
| `CAL-E02:135` | PARTIAL / BLOCKED | 20 seeds 和跨场景描述性敏感性 | stopping rule、validation trajectory、generalization |
| `CAL-E03:164` | PARTIAL / BLOCKED | N=20/50 描述性网格 | resource telemetry、重复运行复现、N=100/200 外推 |

历史 trace 记录的共同覆盖为 46,080 recovery records、48 recovery cells、32 paired cells、160 interval records、8 interval cells、12,800 bootstrap records。由于 task-specific artifacts 当前不存在，这些计数不能作为已持久化的四项交付物验收通过。

## 最小修复顺序

1. 对当前正式 V1 register 和四个 exact item 重新 refreeze 授权。
2. 将四个 analyzer、tests 和内容寻址输出重新物化到持久路径。
3. 从干净、可读取的工作树独立复跑四项，并重新核对全部失败、non-finite、unstable records。
4. E01 在计算前预声明 log-ratio、CI、权重和失败处理协议。
5. E02:128 补 independent truth、record-level split/leakage 和 endpoint provenance。
6. E02:135 新建 stopping-variant protocol/candidate，完成 pre-outcome freeze 后再执行。
7. E03 捕获真实 wall-time/CPU/memory/GPU/per-cell runtime；没有 N=100/200 实验就保持 abstain。
8. 完成后重新做独立统一验收；通过前不改稿件、不更新 register decision、不改变 promotion。
