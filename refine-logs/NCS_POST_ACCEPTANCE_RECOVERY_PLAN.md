# NCS 验收失败后的恢复与证据计划

**日期**：2026-08-04  
**输入验收**：`NCS_FOUR_ANALYSIS_ACCEPTANCE_20260804_021934.md`  
**当前正式 register**：SHA-256 `c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2`  
**目标**：先恢复一条可持久化、可复跑、可独立验收的证据链，再决定是否投入可选强证据实验。

## 规划原则

1. 当前正式 V1 优先于旧授权。旧授权绑定 `3e1aa708...`，不得继续作为执行门禁。
2. 原 worktree 中的历史命令输出只作恢复线索，不作科学结果；所有派生产物必须在持久路径重新运行生成。
3. 当前 V1 中，`V1-026`、`V1-033`、`V1-045` 首先是 `DIRECT_TEXT_REVISION`；只有 `V1-035` 是 `NEW_ANALYSIS_OR_EXPERIMENT`。
4. 没有找到原始 pre-outcome 公式时，不得把事后定义的 E01 log-ratio/CI 称为 confirmatory。
5. N=100/200、independent empirical truth 和 resource-scaling 扩展不是自动必做项；只有作者选择强证据路线时才启动。
6. 在新的统一验收通过前，不修改稿件、不更新 register decision、不改变 promotion。

## 当前 V1 范围

| Item | Priority / Action | 当前最低动作 | 强证据是否另需授权 |
|---|---|---|---|
| `V1-026 / CAL-E01:75` | P0 / DIRECT_TEXT_REVISION | 核对 comparator role、endpoint、replication、failure/non-finite 与 bounded claim | 是 |
| `V1-033 / CAL-E02:128` | P0 / DIRECT_TEXT_REVISION | 保留 known truth、matched endpoint、outside-target 与 failed native gate 边界 | 是 |
| `V1-035 / CAL-E02:135` | P1 / NEW_ANALYSIS_OR_EXPERIMENT | 不虚构 validation-loss 证据；决定是否做 stopping-variant 分析 | 是 |
| `V1-045 / CAL-E03:164` | P0 / DIRECT_TEXT_REVISION | 核对 rank/window/ALS/topology/stability/failure/replication 契约一致性 | 是 |

## 必做恢复路线

### M0. 最终 V1 重新冻结

- 为当前 register、四个 item payload、验收报告和 E4-r3 输入分别记录 SHA-256。
- 生成新的 machine-readable authorization receipt；明确允许的只有恢复、只读派生和独立验收。
- item payload 使用 canonical JSON 单项哈希，避免整个 register 的无关改动再次使四项失效。
- **Go**：register 全文件哈希和四项子哈希同时匹配。
- **Stop**：schema、priority、action class 或 item payload 再次漂移。
- **预计**：2-4 小时，CPU 可忽略。

### M1. 持久化重新物化

- 从四份 session trace 中恢复 analyzer/test 源码，但不恢复历史结果文件。
- 每个恢复文件与 trace 中最后一次 `patch_apply_end` 内容和历史 source hash 交叉核对。
- 源码进入项目持久路径；输出进入新的 `refine-logs/ncs_new_analysis_v2/<item>-<input_bundle_sha256>/`。
- 增加统一的 read-only、no-overwrite、input-hash 和 manifest 测试。
- **Go**：四个 analyzer、四组 tests 均可在干净工作树被发现、编译和执行。
- **Stop**：无法唯一恢复最终源码、需要猜测缺失代码，或恢复内容与 trace hash 不一致。
- **预计**：0.5-1 个工作日。

### M2. 只读派生重新运行

- 使用当前 V1 refreeze 和未变化的 E4-r3 输入重新运行四个 analyzer。
- E01 此阶段只发布 raw comparator ledger/paired differences，不发布新 CI。
- E02:128 只报告 simulation-truth、native-gate 与 provenance 缺口。
- E02:135 只报告现有 20 seeds/scenarios 的描述性敏感性，不声称 stopping/generalization。
- E03 只报告 N=20/50 描述性结果和缺失 telemetry，不外推 N=100/200。
- 共同覆盖硬门：46,080 recovery、48 recovery cells、32 paired cells、160 interval、8 interval cells、12,800 bootstrap records。
- **Go**：两次独立运行输出字节一致；所有失败/non-finite/unstable bins 被显式保留；manifest 全部通过。
- **Stop**：计数不一致、旧输出被覆盖、任何记录被成功子集筛除。
- **预计**：2-6 小时，本地 Apple M5 CPU；无需 GPU。

### M3. 当前 V1 文本/契约审计

此阶段只产出 patch proposal 和 claim ledger，不直接改稿：

- `V1-026`：逐 comparator 核对 role、endpoint availability、复制数、失败和 outside-target。
- `V1-033`：逐句检查 known simulation truth 不被写成 independent empirical ground truth；保留 native gate negative result。
- `V1-045`：核对 methods、supplement 与 controlled contract 的 rank、window、ALS iterations、topology perturbation、stability threshold、failure handling、replication。
- **Go**：每个拟修改句子均绑定到 register item 和可读取 artifact key path。
- **Stop**：拟写内容依赖未运行实验或把 `simulation_only` 扩成 broad fairness/generalization。
- **预计**：0.5-1 个工作日。

### M4. 独立统一验收

- 使用独立任务复跑 tests、分析器、输入/输出哈希、coverage、scope 和隐私检查。
- 验收报告必须区分治理 PASS 与科学 `SUPPORTED/PARTIAL/BLOCKED`，不要求所有强证据实验都转成 PASS。
- **PASS 条件**：register/item 绑定通过；产物持久可读；独立复跑一致；E4-r3 未改变；边界表述与当前 V1 一致。
- **FAIL 条件**：任一 P0 绑定失败、产物不可复跑、记录遗漏、claim 越界。
- **预计**：0.5 个工作日。

### M5. 受控稿件更新

仅在 M4 PASS 后执行：

- 应用 M3 的 source-only patch。
- 更新 sentence-level claim/evidence ledger。
- 保持 E4-r3 为 `simulation_only`，E4-R006/E4-R007 不因恢复性分析自动激活。
- 再跑 release/source-only gates；不触发 RCEP/NYC。

## 可选强证据路线

### S1. E01 log-ratio/CI

1. 先搜索 timestamped pre-outcome artifact 是否已精确定义 panel statistic、cell aggregation、CI 方法、置信水平、权重和失败处理。
2. 若定义完整，按原定义生成独立 derived artifact。
3. 若定义缺失，停止 confirmatory 路线；只能新建 fresh protocol/candidate，或把结果明确标为 exploratory。
4. 不接受事后选择 normal/t/bootstrap CI 来关闭 E4-R006。

**预计**：定义核查 2-4 小时；派生计算少于 1 小时。

### S2. E02:128 independent-truth 路线

- 仅在作者选择扩大证据上限时执行。
- 在 independent DGP 与 native held-out ground-truth 中选择一个主路线，不同时堆叠。
- 预先冻结 DGP、split、endpoint、tuning budget、failure handling 和 claim ceiling。
- 负结果必须保留，不能用 matched-design gain 覆盖。

**预计**：设计与审查 1-2 天；执行 1-3 天，具体算力在 protocol 后评估。

### S3. E02:135 stopping-variant 路线

- 新 candidate/new output root；不复用 E4-r3 身份。
- 记录每次 ALS iteration 的 reconstruction、validation 与 held-out endpoint trajectory。
- 只比较少量预声明规则：当前 fixed-iteration contract、一个 validation-selected checkpoint 规则、一个预声明 patience 规则。
- 使用现有 family × N × query × horizon × 20 seeds；不得按结果删除场景。
- 结果只支持“对 stopping choice 的敏感或不敏感”，不自动构成 generalization proof。

**预计**：protocol/测试 1 天；本地 CPU 2-8 小时；独立验收 0.5 天。

### S4. E03 resource telemetry 路线

- 资源信息无法从 E4-r3 事后恢复；若选择该路线，必须 fresh rerun。
- 只运行当前声明的 N=20/50，记录 wall time、CPU time、peak RSS、per-cell runtime、exit/status。
- N=100/200 保持 `NOT_RUN/ABSTAIN`，除非作者另行批准规模扩展。

**预计**：仪表化 0.5 天；一次 N=20/50 rerun 预计 2-8 CPU 小时。

## 依赖顺序

```text
M0 refreeze
  -> M1 persistent rematerialization
     -> M2 deterministic derived rerun
        -> M3 source-contract audit
           -> M4 independent acceptance
              -> M5 controlled manuscript update

S1/S2/S3/S4 require M0 and separate author authorization.
They are not prerequisites for M4 governance PASS unless the selected manuscript claim depends on them.
```

## 推荐决策

- **立即执行**：M0-M4。
- **验收后执行**：M5。
- **优先考虑的强证据**：S3，因为它是当前正式 V1 中唯一仍归类为新增分析或实验的 item。
- **条件性执行**：S1，仅在找到原始预声明定义时。
- **暂缓**：S2、S4；当前 bounded manuscript wording 可先关闭风险，不应让高成本扩展阻塞治理恢复。
- **明确不做**：未授权的 N=100/200 外推、RCEP/NYC 激活、复用 E4-r3 candidate。

