# NCS 四项新增分析执行计划

**日期**：2026-08-04  
**授权回执**：`NCS_FOUR_ANALYSIS_AUTHORIZATION_20260804_010454.json`  
**初始证据源**：冻结 E4-r3 synthetic-only 结果，仅读取、不重跑、不改写  
**稿件边界**：本计划不授权修改稿件、激活 claim、使用 RCEP/NYC，或提升 E4-r3 的 promotion 状态。

## Claim Map

| Register key | 要检验的限定命题 | 最低充分证据 | 初始路线 |
|---|---|---|---|
| `CAL-E01:75` | 所有预声明 comparator 在相同端点与复制契约下得到完整、公平且可核查的呈现。 | comparator、cell、endpoint、seed、状态和失败全覆盖；数值与摘要逐项复算；缺失与反转不隐藏。 | 从 46,080 recovery records 与 32 个 paired cells 派生完整性和 claim audit。 |
| `CAL-E02:128` | 生成真值、训练/选择信息和 held-out 评价严格分离，不把 simulation truth 写成独立经验 ground truth。 | truth provenance、chronology、selection inputs、endpoint parity 和 leakage gate 全部可追踪；任何未证实项明确阻断。 | 联合冻结结果、candidate/protocol 与实现做静态和记录级 audit。 |
| `CAL-E02:135` | 结论不依赖单一 seed、单一最佳配置或隐含 stopping rule，且失败/不稳定场景被保留。 | 跨 seed/场景的误差分布、selection/stopping provenance、敏感性与拒绝推断规则；若缺 stopping variants，则只完成缺口判定和新 protocol。 | 先判断 frozen records 是否足以做 seed/scenario sensitivity；不足时预注册新候选，不直接执行新 grid。 |
| `CAL-E03:164` | 策略效益、失败阈值与资源开销在已声明规模/压力场景内可复现，且不外推到未运行规模。 | N=20/50、family、query、horizon 的完整失败/稳定性/资源分析；N=100/200 缺失必须显式列为边界。 | 从 E4-r3 派生 cross-scale/stress audit；未覆盖规模只形成新 protocol 需求。 |

## 共同治理

1. 所有分析以输入 SHA-256 绑定，输出写入新的内容寻址目录；冻结 quarantine 文件保持字节不变。
2. 分析器必须是确定性的只读消费者，并配套最小测试；不得根据观察到的结果改指标、删 cell 或改阈值。
3. 所有失败、不稳定、non-finite、缺失字段和不利结果均保留并进入汇总。
4. 每项输出必须区分 `SUPPORTED`、`PARTIAL`、`BLOCKED` 与 `NOT_EVALUABLE`，不得把缺证据当作通过。
5. 四项输出完成后，由独立任务复核覆盖、枚举、哈希、数值复算和 scope；复核前不更新 author decision register。

## Run Order and Decision Gates

| 阶段 | 工作 | Go 条件 | Stop 条件 |
|---|---|---|---|
| M0 | 冻结输入与 schema inventory | 三个输入哈希匹配，E4-r3 仍为 `COMPLETE_QUARANTINE_ONLY`/promotion prohibited | 任一哈希漂移或旧输出被改写 |
| M1 | 四项独立派发并行做只读充分性审计 | 能从冻结材料回答的部分形成可复算 artifact | 需要未预注册指标替换或修改旧 candidate |
| M2 | 运行派生分析与单元测试 | 记录级覆盖完整，测试通过，输出内容寻址 | 失败记录丢失、cell 数不符或分析不可确定复现 |
| M3 | 独立统一验收 | 四项逐一通过哈希、覆盖、数值和 scope 复核 | 任一 P0 项审计缺失或 provenance 不完整 |
| M4 | 决定是否需要新实验 | 只有冻结数据确实不足时，创建全新 protocol/candidate/output root 并 pre-outcome freeze | 复用 E4-r3 candidate 身份、事后改 stopping rule 或直接修改稿件 |

## 预期计算

- 初始阶段：本地 Apple M5 CPU/NumPy，四项均以只读派生与静态审计为主。
- 新科学 grid：当前不启动；只有 `CAL-E02:135` 或 `CAL-E03:164` 的充分性审计证明必要时，另行给出规模、种子、预计时长与授权门禁。
- 最高风险：冻结结果可能没有序列化 stopping-rule variants 或资源 telemetry；该缺口只能导向 `PARTIAL/BLOCKED` 或新 protocol，不能由推断补齐。

## 完成定义

- 四个 register key 均有独立 artifact、测试、输入哈希和明确 verdict。
- 四项均报告数据覆盖与未覆盖范围。
- 独立统一验收完成前，register 保持 `PENDING`，manuscript 和 promotion 状态不变。
