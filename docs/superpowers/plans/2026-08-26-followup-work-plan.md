# 后续工作计划（2026-08-26）

本文件是 review-only 规划产物。它不应用任何补丁、不激活任何主张、不签发任何授权，也不构成独立复核收据。

生成时区基准：`Asia/Shanghai`。取代 `docs/superpowers/plans/2026-08-23-followup-work-plan.md` 作为当前工作排序依据；该文件的 2026-08-24 更正记录与 `REC-P2_D1D2D3_DECISION_CLOSURE_V1_20260825` 的三项裁定继续有效，此处只做增量与重排。

## 0. 门禁快照（2026-08-26 实测）

| 记录 | 状态 | 变化 |
| --- | --- | --- |
| `EXPERIMENT_AUDIT` | 总体 `FAIL`；E4 pre-outcome 附录 `PASS` | 无变化 |
| E4 r3 | 已跑完并独立审计（overall `warn`，`simulation_only`） | 已由 08-24 更正确认 |
| P2 三决策（D1/D2/D3） | **已收口**：`DO_NOT_SIGN` / `MAINTAIN_ABSTENTION` / `RESCOPE_NOT_SCHEDULE` | 新增，见 §3 |
| E4-R007 result-to-claim | `QUALIFIED_SUPPORTED`，claim activation `NOT_ACTIVATED` | 新增，见 §3 |
| `PAPER_CLAIM_AUDIT` | `BLOCKED`（RCEP/NYC 隔离区未复核） | 无变化 |
| `EMPIRICAL_IMPLEMENTATION_AUDIT` | `FAIL` | 无变化 |
| `PROOF_AUDIT` | `PASS`（scoped，source-only） | 无变化 |
| M5-C | 未收口：仍缺两份基于当前哈希的复核收据 | 无实质变化，但输入可用性恶化，见 P0 |
| 工作副本物理层 | **仍不完整**，且出现再驱逐迹象 | 恶化，见 P0 |

## P0（前置，仍未闭合）：工作副本落地与再驱逐

### 本轮实测（2026-08-26 03:00 CST）

相对 08-23 的进展：

- `git rev-parse HEAD` 正常输出 `e7ce60c…`；`git status --porcelain -uno` 为空（tracked 树按索引报告 clean）；`git log` 正常。
- `main.tex`、`supplementary.tex` 当前可读（此前不可读）。

仍然阻断的事实：

- 占位符文件（size>0 且 blocks=0）按顶层目录实测：`.git` 1147、`archive` 4200、`output` 1888、`data` 518、`scripts` 453、`refine-logs` 606、`tests` 99、`manuscript_src` 64、`paper_rewriting_output` 63、`docs` 3。
- **M5-C 的全部六个冻结输入现已退回占位符**：`REC-M5_REVIEW_PATCH_V1_20260811.{md,json}`、`REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.{md,json}`、`REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}` 八个文件实测均为 blocks=0。08-23 时它们曾落地且哈希逐项吻合，说明 iCloud 在两次规划之间发生了再驱逐。哈希链复核在物理上当前无法开始。
- 读占位符会长时间挂起而非快速失败：`REC-M5_RECHECK_DISPATCH_V1_20260823.md`、`PROOF_CHECK_STATE.json` 的读取均触发 60 秒超时；不带 `-uno` 的 `git status` 同理（扫描未跟踪树时挂起）。
- 369 个 `* 2.*` 冲突副本数量未变，分布与 08-23 记录一致。

### 处置动作（不变，宿主 macOS 侧执行）

1. 只读全量落地：Finder 对项目根 Download Now，或宿主终端逐子树 `brctl download`。顺序：`.git` → `manuscript_src` → `refine-logs` → `scripts` → `tests` → `output`/`data`/`archive`/`docs`/`paper_rewriting_output`。
2. 落地后立即复验并**当场记录哈希**：`git rev-parse HEAD`、`git status --porcelain -uno`、`git fsck --full` 全部正常输出。鉴于已发生一次再驱逐，「验证通过」只在验证时刻有效，任何后续消费前应先 `stat` 目标文件确认 blocks>0 再读。
3. 强烈建议迁出 iCloud 同步域（如 `~/work/`），迁移前先 `git bundle create` 或整目录冷备。再驱逐已经实际打断了 P1 输入链，这是迁移理由从「建议」升级为「强建议」的直接证据。
4. 369 个冲突副本处置流程不变：先生成逐对 SHA-256 对照清单；byte-identical 才可删除；内容不同者逐条按 governance 记录裁定。
5. P0 闭合前：不运行任何 `make` 目标、pytest/node 测试、scientific entry；`85/85`、`145/145`、`247/247` 及一切 tracked/clean 结论维持 `NOT_VERIFIABLE`。

## P1（主推）：M5-C 收口 → M5-D 应用

执行顺序沿用 08-23 计划第 1–8 步，仅作两点更新：

1. **前置检查点**：派发两份复核（编辑可追溯 + 治理清单）之前，必须重新完成六输入的本地实测哈希比对——不能直接引用 08-23 记录的匹配结论，因为字节已被再驱逐过一轮。若再落地后任一哈希发生变化，M5-C 流程中止并升级为完整性事件，而不是照旧派发。
2. 其余不变：给治理复核直接下发真实路径（`BASELINE` 命名歧义不再留给对方解析）；两份 `PASS` 后写 M5-C 收口记录并把三份基于当前字节的收据（科学 V5 + 新编辑 + 新治理）写入 patch JSON 的 `independent_review_receipts`；随后请求作者 M5-D 授权，按 G01–G10 顺序应用 26 单元（每组前比对锚点哈希），重建并复跑四道门禁加 `validate_rec_m4_v4.mjs`；表述天花板（G06/G07 review-only、三处 unavailable 规范源、V1-026/033/045 边界）逐字保留。

## P2（决策已收口，遗留三个执行项）

D1/D2/D3 已由作者于 2026-08-24/25 裁定并记录在 `REC-P2_D1D2D3_DECISION_CLOSURE_V1_20260825`，不再重复论证。剩余可执行项：

1. **E4-R007 独立化与激活（低成本，可先行）**：现有 `QUALIFIED_SUPPORTED` 收据由补丁合成方自产，自述非独立外部复核。下一步是作者决定是否 (a) 就同一映射委托真正独立的 result-to-claim 复核收据，(b) 之后在 `simulation_only` / horizon 4 / 每 cell 20 panel 天花板内激活 E4-R007 主张。该审查只读冻结 r3 字节，不依赖 P0，但受 P0 影响的方式同上：读前先 stat。
2. **E4-R006 保持 BLOCKED**：r3 字节上结构性封闭，解封只有两条路——出示 r3 之前的 pre-outcome CI 规格（大概率不存在），或新的 pre-outcome 声明加重跑（独立授权事项）。无新授权前不做任何动作。
3. **R006e / R006f 维持冻结**：`DO_NOT_SIGN` 与 `MAINTAIN_ABSTENTION` 已记录；生产绑定四个 `_PRODUCTION_*` 为 None 属构造性不可执行。若未来重启，须先有新的预声明估计量问题（沿 R006c routing）+ 代码变更 + 新治理轮次，均超出本轮范围。

## P3（待 P0 与下游授权）：经验证据解封

路线与 08-23 计划完全一致，无变化：对 `psa-20260719-rcep-03`（36 文件）与 `psa-20260719-nyc-01`（18 文件）隔离区做数值级独立审计 → 独立 paper-to-evidence 审计 → 单独的 downstream-build 与 promotion 授权 → 重建稿件与图包 → post-regeneration 独立复核无 FATAL/CRITICAL。

被封锁量清单继续有效，M5 改稿中不得复活任何 RCEP/NYC 数值；陈旧工件哈希只用于识别 stale 对象。P1 与 P3 的交界判断不变：26 个 M5 单元不依赖 RCEP/NYC 数值，可在 P3 未解封前提下独立收口。

## 依赖关系与建议推进顺序

```
P0 落地+fsck ──→ P1 第6步起(M5-D 应用) ──→ 门禁复跑
   │                                  
   ├──(stat 通过的输入)──→ P1 第1–5步(两份复核收据) 
   └──(不依赖 P0)─────→ P2-1(E4-R007 独立化决策)

P0 git tracked/clean + 作者 downstream 授权 ──→ P3 全线
```

唯一能解开当前全局僵局的物理操作是宿主侧全量落地；其余一切要么被它门控，要么是零执行的作者决策。建议顺序：① 宿主落地 → ② 三命令验证 + 冷备/迁移 → ③ 冲突副本对照清单 → ④ 六输入哈希复验后派发两份复核 → ⑤ M5-C 收口 → ⑥ 作者 M5-D 授权、应用、门禁复跑；②之后任意时刻可并行推进 P2-1 的作者决策。

## 本轮授权边界声明

本文件是本轮唯一新增产物。未修改 `manuscript_src`、formal register、`refine-logs` 下任何冻结记录、authorization 文件、scientific payload、generated TeX。未执行任何 git 写操作、任何 `make` 目标、任何测试、任何 scientific entry。scientific execution 与 claim activation 均保持 `NOT_AUTHORIZED` / `NOT_ACTIVATED`。

## 执行进展（2026-08-26 追记；仓库已迁至 `~/work/`，下述路径以新址为准）

经作者指示「同意上述分析，请继续后续工作」及两项结构化决策（E4-R007 先独立复核再定激活；批准迁出 iCloud），P0 已于当日闭合：

- **全量落地完成**：占位符 9180 → 0。目录级 `brctl download` 调度无效（3 分钟零进展），改为逐文件并行下载后约 12 分钟清零。
- **git 三命令全部通过**：HEAD `e7ce60c…`；`fsck --full` rc=0（此前 dump core）。**新事实**：内容可比对后 tracked 树并不干净——76 个已修改跟踪文件（最后一次提交后的工作漂移，非损坏）；三个审计关键实验文件相对 HEAD 干净。
- **M5-C 六冻结输入复验全部 MATCH**：再驱逐未改变任何字节。
- **冲突副本对照清单完成**（369 对：341 byte-identical；17 差异——15 个副本严格更旧、2 个同时间戳旧草稿分叉 `discussion 2.md` 与 `build_natcs_framework_figure 2.py`；11 原件缺失均在 superseded `_archives` 内）。未删除任何文件，处置待作者签核。TSV：`tmp/conflict_copy_audit_20260826.tsv`。
- **冷备 + 迁移完成**：`~/work/<repo>`（10285 文件两侧一致）+ `~/work/repo-bundle-20260826.bundle`（完整历史验证通过）；源目录整体移入 `~/.Trash/…-pre-migration-20260826` 可恢复。新址 fsck rc=0、占位符 0。iCloud 再驱逐风险自此根治。
- **三条只读复核车道已派发**（luna worker 纪律）：编辑可追溯 → `refine-logs/REC-M5_EDITORIAL_RECHECK_V4_20260823.{md,json}`；治理清单 → `refine-logs/REC-M5_GOVERNANCE_RECHECK_V5_20260823.{md,json}`；E4-R007 独立 result-to-claim → `refine-logs/NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.{md,json}`。M5-C 收口步骤（closure 记录 + 三收据写入 patch JSON，将使哈希 `938e5218…` 失效）仍按序排在两车道报告之后，随后才可请求 M5-D 授权。
- 逐项证据链见 `refine-logs/REC-P0_REPAIR_CLOSURE_V1_20260826.{md,json}`。

### 待作者决策队列（车道返回后）

1. 两车道若均 PASS → 授权写 M5-C 收口记录并注册三份收据（patch JSON 字节变更）→ M5-D 改稿授权。
2. E4-R007 独立收据 verdict → 是否在 simulation_only/h4/20-panel 天花板内激活主张。
3. 冲突副本处置签核（341 删除候选 / 15 旧代副本 / 2 旧草稿保留或审查 / 11 归档孤儿）。
4. 建议项：对当前工作态做一次快照提交（76 modified + 新增治理记录），消除漂移；属 git 写操作，需单独授权。

### 三车道结果（2026-08-26 追记二）

| 车道 | verdict | 收据（实测 SHA-256 由编排方存管） | 要点 |
| --- | --- | --- | --- |
| A 编辑可追溯 | **FAIL**（仅 E-T3） | `REC-M5_EDITORIAL_RECHECK_V4_20260823.{md,json}`，`f5524b84…` / `5749f65a…` | 六输入哈希全 MATCH、E-T1/T2/T4/T5/T6/T7 全 PASS；E-T3 查出五处治理词汇/内部状态码混入拟投稿文本（F1 major：G04-P4 的 `` `NOT_RUN` ``/`` `BLOCKED` `` 嵌入 results 散文；F2–F4 moderate；F5 minor）。子代理在收尾自检阶段故障，但交付物完整，编排方已独立验证。 |
| B 治理清单 | **PASS** | `REC-M5_GOVERNANCE_RECHECK_V5_20260823.{md,json}`，`16b9b5d9…` / `9e1fd5f9…` | 20/20 锚点零漂移；12/12 protected_baseline 实测 MATCH（含已落地的 decision register）；G-T7 如实上报 tracked/clean=FALSE（74 M + 2 D）。关键发现：七个锚点目标文件 modified-vs-HEAD 却与冻结绑定逐字节相等——HEAD 不含受管字节，工作副本即受管代际。 |
| C E4-R007 独立复核 | **QUALIFIED_SUPPORTED**（activation NOT_ACTIVATED） | `NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.{md,json}`，`2bb2379f…` / `18ed6dc5…` | FR8（manifest/completion 标签不一致）裁定为 provenance-label 瑕疵而非数据缺口；天花板：simulation_only/h4/20 panel/80 replicates/单次执行；FR9b NOT_FOUND 仅封闭 E4-R006。披露：其进程层故障导致聚合计数为 Tier-B「SHA 绑定次级佐证」（零矛盾），哈希为 freeze 时记录值而非重算。 |

**M5-C 收口未触发**（派发任务书要求两车道均 PASS）。收口记录与收据注册均未执行；patch JSON `independent_review_receipts` 仍为 1 条历史条目。

**共同披露（三条收据一致）**：实际产出方为 ox-alpha（DeepSeek Harness 内自裁决），非派发任务书要求的 `gpt-5.6-terra/max` 来源；偏离已由各收据如实记录，接受与否属作者裁定。

### E-T3 处置路径备注

修订拟投稿文本有两种合规路径：(1) **V2 补丁代际**——新建 `REC-M5_REVIEW_PATCH_V2_*`（不动 V1 冻结字节），三车道在 V2 上全链重审；干净但多一轮。(2) **作者修正案裁定**——作者明示豁免五处发现并规定「应用时以平实英文重述、语义天花板逐字保留」，修正案入 M5-D 授权记录，应用后对稿件实际字节做门禁复验。两条路径均不触碰 V1 冻结哈希链。
