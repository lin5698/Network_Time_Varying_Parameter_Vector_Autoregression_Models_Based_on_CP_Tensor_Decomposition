# REC-P2 Plan Staleness Correction V1

Generated: 2026-08-24

Audit timezone basis: `Asia/Shanghai`

Status: `CORRECTION_APPLIED_PROVENANCE_PARTIALLY_UNVERIFIABLE`

Decision: `NOT_AUTHORIZED`

Record class: plan_document_staleness_correction_record。机器可读伴档为 `REC-P2_PLAN_STALENESS_CORRECTION_V1_20260824.json`，SHA-256 `feb33ab871783abc43b7b6f16281062ec078d7d00a0abc62b97354ca8ac8418d`。两者不一致时以 JSON 为准。

计划文档 §P2 的过时事实更正已落地，但其引用的更正记录此前不存在，形成悬空引用。本记录闭合该引用：逐条核对更正后的事实陈述、留档前后哈希、并说明哪一项无法核对。

## 授权范围

作者授权原文：「授权更改」（conversation turn 2026-08-24）。

解释后的范围：仅授权更正计划文档 §P2 中「E4 网格未运行」这一过时说法，以及 D3 处随之而来的表述。

以下各项**未**获授权，本记录也未触及：

- 签发 D1 / D2 / D3 任何一份授权草案
- 开启 E4-R007 的独立 result-to-claim 复核
- 更正 EXPERIMENT_AUDIT.md 第 34 行
- 任何 manuscript_src、formal register、generated TeX 或授权文件改动
- 任何 git 操作、make 目标、测试套件或 scientific entry

## 一处需要作者看到的先后顺序问题

更正落地时间 `2026-08-24 14:31:13`，落地方 `ACTOR_OUTSIDE_THIS_SESSION`。

判定依据：本会话在该时刻处于等待作者输入状态，未发出任何写操作；本会话当轮的写入只有 14:05 的 REC-P2 两份文件。90 分钟窗口内全仓（排除 .git）仅三个文件被修改：REC-P2 两份（14:05，本会话）与本计划文档（14:31）。

文档内自述的授权声明（bold lead-in）：「更正记录（2026-08-24，经作者授权）。」

**风险。** 更正段在作者实际授权之前即自称「经作者授权」，且引用了一份当时并不存在的记录。作者授权现已给出，引用亦由本记录闭合，但这一先后顺序本身应被看到：它意味着有第二个行为者在同一工作副本上写入。

**建议。** 在 P0 闭合前避免多会话并行写同一工作副本。git 不可解析时没有任何写冲突检测，哈希冻结记录会被静默失配。

## 前后字节

| 状态 | 字节 | SHA-256 | 可否重新实测 |
| --- | ---: | --- | :---: |
| 更正前 | 12393 | `f61a0e2e…` | 否 |
| 更正后 | 15009 | `f962cfd1…` | 是 |

字节增量 +2616。更正前摘要的唯一存世来源是 `refine-logs/REC-P2_AUTHORIZATION_DRAFTS_V1_20260824.json measured_inputs`；那批字节本身已不可重建，因此无法做逐字 diff。

悬空引用闭合：`docs/superpowers/plans/2026-08-23-followup-work-plan.md line 98` 引用的 `refine-logs/REC-P2_PLAN_STALENESS_CORRECTION_V1_20260824.md` 由 `ABSENT` 变为 `MATERIALIZED`。

## 更正后事实陈述逐条核对

共 8 条：7 条有字节支撑，1 条不可核对。不可核对的一条按 fail-closed 记为 `NOT_VERIFIABLE`，不记为通过。

| 编号 | 陈述 | 位置 | 判定 |
| --- | --- | --- | --- |
| `C-1` | E4 r3 已于 2026-08-01 完成并经独立审计；48 recovery / 32 paired-comparison / 8 interval cell 与 46080 条 recovery record、160 条 interval record 齐备 | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 96` | `SUPPORTED` |
| `C-2` | check A/B/C/E/F/G/H/I 为 PASS，唯一 WARN 为 check D | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 96` | `SUPPORTED` |
| `C-3` | r2 quarantine root 存在，但仅含 execution-manifest.json（408 字节，status RUNNING_QUARANTINE_ONLY），无结果字节 | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 96` | `SUPPORTED` |
| `C-4` | r3 root 下 e3-results.json、execution-complete.json、execution-manifest.json 三者齐备，但 manifest 仍为 RUNNING_QUARANTINE_ONLY 而 completion marker 为 COMPLETE_QUARANTINE_ONLY，终态证据落在 marker 而非 manifest 上 | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 96` | `SUPPORTED` |
| `C-5` | 被更正的原说法源自 EXPERIMENT_AUDIT.md 第 34 行，且该行逐字为 "The E4 grid was not run and the r2 quarantine root remains absent." | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 98` | `SUPPORTED` |
| `C-6` | EXPERIMENT_PLAN 第 72 行预声明 paired panel-level log error ratio，第 74 行预声明等权 cell-level 置信区间 | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 104` | `SUPPORTED` |
| `C-7` | E4-R006 activation blocked、E4-R007 activation blocked-pending-result-to-claim，与更正段「R006 结构性封闭 / R007 只需复核」的切分一致 | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 104` | `SUPPORTED` |
| `C-8` | 本次更改仅限 §P2 事实段与 D3 表述；D1、D2 两行未动 | `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 98` | `NOT_VERIFIABLE_NO_PRE_CORRECTION_BYTES` |

**`C-8` 为什么不可核对。** 更正前字节在可达范围内没有任何留存：P0 下 git 不可解析，本文件既无备份也无 `' 2.'` 冲突副本，会话转录又在可达文件系统之外。存世的更正前状态只有字节数 12393 与摘要 `f61a0e2e…`（来源 REC-P2 measured_inputs）。因此「改动仅限该段与 D3」这一断言只能取落地方的说法，本记录不予背书。

### 关键实测取值

r3 审计规模：recovery cell 48、paired comparison cell 32、interval cell 8；recovery record 46080、interval record 160；每 cell 20 个 panel seed。overall verdict `warn`，evaluation type `simulation_only`。

唯一 WARN 的检查项是 `reachability_declared_metrics`，在 checks 顺序中位列第 4，即计划文档所称的 check D。

r2 root `PRESENT`，仅含 `execution-manifest.json`（408 字节，status `RUNNING_QUARANTINE_ONLY`）；结果字节是否存在：否。

r3 root 含 `e3-results.json`、`execution-complete.json`、`execution-manifest.json`；manifest status `RUNNING_QUARANTINE_ONLY`，completion marker status `COMPLETE_QUARANTINE_ONLY`。终态证据确实落在 marker 而非 manifest。

被更正的原句，逐字引自 `EXPERIMENT_AUDIT.md` 第 34 行：

> E4-R009. The E4 grid was not run and the r2 quarantine root remains absent.

预声明取自 `refine-logs/EXPERIMENT_PLAN_20260731_115719.md`：

- line 72：**Primary metrics**：response MSE、operator MSE、status/failure rate、paired panel-level log error ratio；prediction loss 仅作为 selection record。
- line 74：**Secondary evidence**：operator MSE 与 response MSE 方向一致；等权 cell-level paired log-ratio 置信区间；runtime/selection/failure inventory。

全文检索 90% / 95% / 99% 这类置信水平取值，命中 0 处。这正是 E4-R006 在 r3 字节上结构性封闭的根据：CI 的置信水平从未被 pre-outcome 声明。

审计对两项主张的记载：

| claim | impact | activation | ceiling |
| --- | --- | --- | --- |
| `E4-R006` | `qualified` | `blocked` | `declared-synthetic-dgp-only` |
| `E4-R007` | `qualified` | `blocked-pending-result-to-claim` | `simulation-only-h4-20-panels-per-cell` |

## 仍未处理的三处不精确

这三处都不由本次更正引入，本记录只留档，不擅自改动。

**`I-1` 严重度 `LOW_WORDING`** — 位置 `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 96`。

更正段写「r3 同名 root」，但两个 root 名并不相同（…-quarantine-r2 与 …-quarantine-r3）。指称对象正确，措辞会让读者误以为是同一目录。

处置：留档，不改。改它属于第二次改动，超出本次授权范围。

**`I-2` 严重度 `MEDIUM_MISREADS_AS_MEASURED`** — 位置 `docs/superpowers/plans/2026-08-23-followup-work-plan.md line 96`。

该行为 primary root 的两个文件给出 SHA-256，读起来像本地实测值；实测这两个文件均为 iCloud 未落地占位符（blocks=0，读取失败），因此那两个摘要只能是冻结 checklist 的记录值，在 P0 闭合前不可核对。REC-P2 已将同族摘要判为 NOT_VERIFIABLE_DATALESS。

处置：留档并提请作者注意。这是更正之前就存在的问题，不由本次更改引入。

**`I-3` 严重度 `BY_DESIGN`** — 位置 `EXPERIMENT_AUDIT.md line 34`。

原始过时句仍留在 EXPERIMENT_AUDIT.md 第 34 行，未更正。

处置：刻意不动。它是既有审计记录，在其记录日期（2026-07-31）为真；改它需要另一次授权。更正段已显式声明这一点。

## 与 REC-P2 的关系

取代字段 `decisions.D3.plan_statement_correction.correction_status`：原值 `PLAN_NOT_YET_CORRECTED_SEPARATE_AUTHORIZATION_REQUIRED`，现应读作 `PLAN_CORRECTED_2026-08-24_SEE_REC-P2_PLAN_STALENESS_CORRECTION_V1`。

append-only：不改动已冻结的 REC-P2 字节，改由本记录取代该字段。REC-P2 中 docs/superpowers/plans/2026-08-23-followup-work-plan.md 的实测摘要指的是更正前字节。

REC-P2 两份文件字节未变：json `31baa95f…`、md `5119ae1e…`。

D1 DO_NOT_SIGN、D2 MAINTAIN_ABSTENTION、D3 RESCOPE_NOT_SCHEDULE 三项建议不因本次更正而改变；本次更正只消除了 D3-G1 这一项前置缺口。本次闭合的缺口是 `D3-G1`；仍未闭合的是 `D3-G2`、`D3-G3`。

## primary root 实测状态

`output/high_impact_revision/r006e_native_supported_recovery_v2` — `PRESENT`

| 文件 | 字节 | blocks | 可读 |
| --- | ---: | ---: | :---: |
| `construction_gate_preoutcome.json` | 10295332 | 0 | 否 |
| `construction_manifest.sha256` | 5383 | 0 | 否 |

两个文件 `blocks` 为 0 且读取失败，是 iCloud 未落地占位符。这支持 `I-2`：计划文档为它们给出的摘要不可能是本地实测值。

## 实测输入

| 路径 | 字节 | SHA-256 | 状态 |
| --- | ---: | --- | --- |
| `docs/superpowers/plans/2026-08-23-followup-work-plan.md` | 15009 | `f962cfd1…` | `MATERIALIZED` |
| `EXPERIMENT_AUDIT.md` | 11064 | `8897901c…` | `MATERIALIZED` |
| `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md` | 4785 | `921033ac…` | `MATERIALIZED` |
| `refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.json` | 1736 | `60523c09…` | `MATERIALIZED` |
| `refine-logs/EXPERIMENT_PLAN_20260731_115719.md` | 10228 | `777f77f7…` | `MATERIALIZED` |
| `refine-logs/REC-P2_AUTHORIZATION_DRAFTS_V1_20260824.json` | 44276 | `31baa95f…` | `MATERIALIZED` |
| `refine-logs/REC-P2_AUTHORIZATION_DRAFTS_V1_20260824.md` | 23318 | `5119ae1e…` | `MATERIALIZED` |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r2/execution-manifest.json` | 408 | `6a9109b4…` | `MATERIALIZED` |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-manifest.json` | 408 | `42d2b2da…` | `MATERIALIZED` |
| `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json` | 301 | `18e7dc81…` | `MATERIALIZED` |

## 沿用的阻断约束

`P0-C1` 不得删除 `manuscript_src/natcs/discussion 2.md`。
`P0-C2` 不得删除 `refine-logs` 中哈希冻结 `REC` 记录的 `' 2.'` 副本。
`P0-C3` 不得把 `ORPHAN_NO_BASE` 副本视为冗余。
`P0-C4` 落地完成前不得运行任何 `make` 目标、测试套件或科学入口。
`P0-C5` git 未解析前，`tracked/clean`、`247/247`、`85/85`、`145/145` 一律报 `NOT_VERIFIABLE`。

## manuscript_src 未变更的依据

`manuscript_src/natcs` 下 64 个 md 文件中 63 个可读，1 个为 iCloud 未落地占位符（`manuscript_src/natcs/_archives/superseded_text_before_20260618_2140/abstract_2.md`，errno 35）。

全部文件中最新 mtime 为 `2026-08-12 13:41:40`（`manuscript_src/natcs/ncs_source_only_rereview_20260723.md`），远早于本轮。非变更结论取自 mtime 与 90 分钟窗口的全仓 find，不取自聚合摘要比对。

此前记录的聚合摘要 `b9989a7f…` 判定 `NOT_COMPARABLE_METHOD_NOT_RECORDED`。此前记录的 63 文件聚合摘要未同时记录聚合方法（拼接字节 / 摘要串接 / 含路径的清单行三种都试过，均不重现该取值），故按 fail-closed 记为不可比对，不记为 PASS，也不记为 MISMATCH。文件集一致：64 个 md 中 63 个可读，1 个为 iCloud 未落地占位符。

## 本轮未做的事

- 未运行任何 make 目标、测试套件或 scientific entry
- 未执行任何 git 操作
- 未读取 R006e / R006f 的未落地产物字节（记录为 placeholder，不推断内容）
- 未重建更正前字节，故未做逐字 diff

## 改动路径

- `refine-logs/REC-P2_PLAN_STALENESS_CORRECTION_V1_20260824.json`
- `refine-logs/REC-P2_PLAN_STALENESS_CORRECTION_V1_20260824.md`

manuscript_src、formal register、所有既有冻结记录（含 REC-P2 两份）、所有授权文件与生成的 TeX 均未改动。未执行 git 操作、make 目标、测试套件或 scientific entry。scientific execution 与 claim activation 仍为 NOT_AUTHORIZED。
