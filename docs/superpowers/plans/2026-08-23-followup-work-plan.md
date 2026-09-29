# 后续工作计划（2026-08-23）

本文件是 review-only 规划产物。它不应用任何补丁、不激活任何主张、不签发任何授权，也不构成独立复核收据。

生成时区基准：`Asia/Shanghai`。

## 0. 当前门禁快照

| 记录 | 日期 | verdict | 控制性 |
| --- | --- | --- | --- |
| `PROOF_AUDIT` | 2026-07-31 | `PASS`（scoped，source-only 数学主张） | 自述 non-controlling |
| `PAPER_CLAIM_AUDIT` | 2026-07-19 | `BLOCKED`，reason `rcep_nyc_quarantines_unreviewed` | 控制性 |
| `EMPIRICAL_IMPLEMENTATION_AUDIT` | 2026-07-19 | `FAIL`（RCEP/NYC 隔离区完成但未复核） | 控制性 |
| `EXPERIMENT_AUDIT` | 2026-07-19 | `FAIL`；E4 pre-outcome 附录 2026-07-31 `PASS` | 控制性 |
| `REC-M5_REVIEW_PATCH_V1` | 2026-08-11 | `ready_for_independent_review`，26 单元全部 unapplied | 待收口 |

本轮新增一项此前未记录的阻断项：工作副本在物理层不完整（见 P0）。

## P0（前置）工作副本可用性

### 观测事实

- `.git/HEAD` 指向 `refs/heads/codex/m5-current-luna-science-recheck`。该 ref 文件 `size=41 blocks=0`；`refs/heads/main` 与 `ORIG_HEAD` 同为 `size=41 blocks=0`。
- `.git` 下 1146 / 1153 个文件为 `size>0 blocks=0` 的未落地占位符。`git rev-parse HEAD` 报 `unknown revision`，`git log` 报 `your current branch appears to be broken`，`git fsck` 直接 dump core。
- 全库 8095 个文件处于同样的未落地状态，分布为 `archive` 4200、`output` 1888、`.git` 1146、`data` 518、`scripts` 205、`.aris` 81、`tests` 32。
- `main.tex`、`supplementary.tex`、`monte_carlo_cp_network_tvp_var_results.csv` 当前不可读。
- 369 个 `* 2.*` 同步冲突副本，分布为 `refine-logs` 164、`scripts/experiments` 56、`paper_rewriting_output` 31、`scripts/ncs_review_corpus` 24、`tests` 21、`scripts` 10，日期跨 2026-07-16 至 2026-08-12。
- 仓库位于 `~/Desktop/translation/…`，症状（占位符 + 冲突副本 + 读取报 `EDEADLK`）与 iCloud Drive 桌面同步一致。

### 为什么必须前置

现有门禁条款直接依赖 git 可解析性：`EMPIRICAL_IMPLEMENTATION_AUDIT` 第 7 项要求 helper trust manifest 绑定 helper Git commit，且 `config.py`、`research_data_construction.py`、`research_network_tvp_var.py` 三者相对该 commit 必须 tracked and clean；第 9 项要求 NYC 数据在 frozen upstream commit `7e63ba9734021171eaf49edb92be8a7e7e8802eb` 下十个 2012–2021 NPZ 全部 tracked、clean、non-symlink；C3 静态证据绑定 commit `d0e398b896848f26413cf9aa9dfca15fb4e7ce64`。git 不可解析时，这三条在原理上都无法复验，任何"tracked and clean"结论都不可采信。

冲突副本落在 `tests/` 与 `scripts/` 内，可能被测试收集或哈希清单扫描命中，直接威胁 `85/85`、`145/145`、`247/247` 这类计数型证据的语义。`refine-logs` 下 164 个副本位于哈希冻结治理区，尤其不能凭直觉处理。

### 处置动作（宿主 macOS 侧执行，VM 内无法触发落地）

1. 只读全量落地，不做写操作。Finder 中对项目根执行 Download Now，或宿主终端逐子树 `brctl download`。建议顺序：`.git` → `manuscript_src` → `refine-logs` → `scripts` → `tests` → `output`/`data`/`archive`。
2. 落地后复验三条命令都要有正常输出：`git rev-parse HEAD`、`git status --porcelain`、`git fsck --full`。
3. 建议将仓库迁出 iCloud 同步域（例如 `~/work/`）。不迁移则冻结哈希会被同步层反复破坏。迁移前先做 `git bundle create` 或整目录冷备。
4. 冲突副本按审计流程处置：先生成 369 个副本与正本的逐对 SHA-256 对照清单；byte-identical 才可删除，内容不同的必须按 governance 记录逐条裁定。
5. P0 闭合前不要运行任何 `make` 目标、任何 pytest / node 测试、任何 scientific entry。部分文件不可读会产生假失败或假通过。

### 门禁条件

P0 未闭合前，`tracked/clean`、`247/247`、`85/85`、`145/145` 的任何复述均标记 `NOT_VERIFIABLE`。

## P1（主推）M5-C 收口

### 哈希链现状

当前六个冻结输入实测 SHA-256 与 `REC-M5_GOVERNANCE_BASELINE_V10_20260812` 记录值逐项一致：

| 输入 | SHA-256 |
| --- | --- |
| `REC-M5_REVIEW_PATCH_V1_20260811.md` | `69888df4a1f369eba0bb79e9f8c76d583d1f92e0f7319d98a967e44b05e580bd` |
| `REC-M5_REVIEW_PATCH_V1_20260811.json` | `938e5218280fcdf25ffb206040d420e2420851a3483e1cc7c282dabf0c01e0e6` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `1555484a0849fd96425754ebfa4e3191473cf8c32008cd4df69091b2404b9341` |
| `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `ebb639ed613520ac643ee1ac21b53c9420e4bbf3a010af1f130a8e3d3b12d8b6` |
| `REC-M5_GOVERNANCE_BASELINE_V10_20260812.md` | `dfd4385fd1f6f027e7a9ba12fc91f8e710e059edbe38179606898264e3d00539` |
| `REC-M5_GOVERNANCE_BASELINE_V10_20260812.json` | `94668a914aeba43dc2d8ca34e7639cb4930e34b2abbe8211980a77bf4adfd3ee` |

### 三条复核车道对当前字节的实际覆盖

| 车道 | 最新收据 | verdict | 覆盖字节 | 对当前字节是否有效 |
| --- | --- | --- | --- | --- |
| 科学边界 | `REC-M5_SCIENTIFIC_RECHECK_TERRA_V5_20260812` | `PASS` | 上表六项，expected = actual | 有效 |
| 编辑可追溯 | `REC-M5_EDITORIAL_RECHECK_TERRA_V3_20260812` | `BLOCKED` | patch md `b95a0960…`、json `8c0546a7…`、AIN json `c7664285…` | 失效，审的是修复前字节 |
| 治理清单 | `REC-M5_GOVERNANCE_RECHECK_TERRA_V4_20260812` | `BLOCKED` | 同上旧字节 | 失效 |

### 两条 BLOCKED 的性质判定

`TERRA-V3-E1` 是唯一实质编辑阻断项：G04 两个提议段落之间夹了一条未标注的 `AIN-RESULT binding` 过程说明，存在被段落级工具写入 `results_validation.md` 的风险。在当前字节中检索 `AIN-RESULT binding`、`partial M5-A response`、`remaining author inputs` 三个特征串均无命中；当前字节含 4 处显式 `manifest-only` 标注，patch JSON 的 `verification.semantic_service_note` 亦记载该 G04 traceability note 为 manifest-only。据此判定已修复，但此判定由规划方作出，不构成独立复核收据，仍须由独立复核确认。

`TERRA-V4` 的 `BLOCKED` 原因是它要验的路径写作 `refine-logs/REC-M5_GOVERNANCE_RECHECK_V10_20260812.{md,json}`，而实际文件名为 `REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}`，报告自述 exact paths 未在该 agent 工作区材料化。这是路径命名不匹配，很可能叠加 P0 的未落地问题，不是实质治理发现。

结论：M5-C 只差两份基于当前哈希的新收据。

### 执行顺序

1. 修正 V10 基线中对治理复核输入的路径记法（`BASELINE` 与 `RECHECK` 命名歧义），或在派发时直接给出真实路径与期望哈希，避免第三次因路径落空而 `BLOCKED`。
2. 派发编辑可追溯复核。provenance `gpt-5.6-terra` / `max`、direct self-adjudication；输入锁定为上表六个哈希；任务为复验 `TERRA-V3-E1` 是否闭合、26 单元逐段可追溯性、以及提议文本中不含 reader-facing 之外的过程语句。
3. 派发治理清单复核。同一 provenance；要求本地实测哈希与期望值逐项比对；缺失或不可读输入一律 `BLOCKED`，不得默认 `PASS`。
4. 两份均 `PASS` 后写 M5-C 收口记录，并把当前字节的三份收据（科学 V5 + 新编辑 + 新治理）写入 patch JSON 的 `independent_review_receipts`。该字段目前只有一条 `EDITORIAL_RECHECK_V2`，且自标 `HISTORICAL_ONLY_PATCH_CHANGED_AFTER_ALL_AUTHOR_INPUT_CONFIRMATIONS`。
5. 向作者请求 M5-D 授权。在 M5-D 之前不得改 `manuscript_src`、不得改 formal register、不得动 generated TeX。
6. M5-D 授权后只改 `manuscript_src/natcs/*.md` 与 `controlled_benchmark_contract.json`，按 G01–G10 顺序应用；每组应用前先比对 `pre_apply_anchor_checks` 锚点哈希（现记录 `PASS_10_OF_10_GROUP_ANCHOR_RECORDS`）。
7. 应用后重建与复跑门禁：`make natcs-manuscript`，随后 `make natcs-source-only-gate-check`、`make natcs-final-gate-check`、`make natcs-release-safety-audit`，并重跑 `scripts/validate_rec_m4_v4.mjs`。此步必须在 P0 之后。
8. 表述天花板不得越界。G06 / G07 为 `AUTHOR_CONFIRMED_REVIEW_ONLY`，只建立实现语义，不得升级为 convergence、global optimum 或 general topology-robustness 表述。application/bootstrap 100/80、spectral-radius、50% top-exposure 三处规范源仍为 unavailable，不得从 generated TeX 反向补源。V1-026 保持 descriptive / `NOT_RUN` / `BLOCKED`；V1-033 保持 simulation-only / `NOT_EVALUABLE`；V1-045 保持 N=20/N=50 限定、N=100/N=200 `NOT_RUN/ABSTAIN`、`resource_telemetry BLOCKED/null`。

M5-D 之后，formal register 变更仍需单独的 M5-F 授权。

## P2（待作者决策）R006e / R006f 与 E4

### 事实

生产 screening primary root 仅含 `construction_gate_preoutcome.json`（`4c3139c6cfee8c452b418f09b3bf04ec977e08f8ada5eb4e8b9d032309d5f090`）与 `construction_manifest.sha256`（`424ee25104b325bf3e63359d3f61c0d3adb97604e6c9c81d7f5bcf1a4009346b`），repeat root 与 control root 缺失。受管调用 `python3 -m scripts.experiments.r006e_screening_v2 screening-pair --workers 6 --authorization …` 退出码 `2`，`screening-pair refused by governed preflight`。双轨设计见 `docs/superpowers/specs/2026-07-16-r006e-r006f-dual-track-design.md`。E4 pre-outcome integrity 为 `PASS`，允许 E4-R001 至 R005 记为完成。E4 r3 已于 2026-08-01 完成并经独立审计（`refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md`，overall `warn`，`simulation_only`）：48 recovery cell、32 paired-comparison cell、8 interval cell 与 46080 条 recovery record、160 条 interval record 齐备，check A/B/C/E/F/G/H/I 为 `PASS`，唯一 `WARN` 为 check D。阻断项是一族未序列化的预声明指标 —— paired panel-level log error ratio 及其 cell-level 置信区间 —— 审计明写 “No protocol amendment or post-outcome metric substitution is accepted by this audit.”。r2 quarantine root `refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r2` 存在，但仅含 `execution-manifest.json`（408 字节，`status: RUNNING_QUARANTINE_ONLY`），无结果字节；r3 同名 root 下 `e3-results.json`、`execution-complete.json`、`execution-manifest.json` 三者齐备，但 manifest 仍为 `RUNNING_QUARANTINE_ONLY` 而 completion marker 为 `COMPLETE_QUARANTINE_ONLY`，终态证据落在 marker 而非 manifest 上。

> **更正记录（2026-08-24，经作者授权）。** 上段原写作「E4 网格未运行，r2 quarantine root 缺失」，源自 `EXPERIMENT_AUDIT.md`（2026-07-31）第 34 行 “The E4 grid was not run and the r2 quarantine root remains absent.”。该说法已过时（r3 已跑完并经审计），且对 r2 不准确（root 存在，缺的是结果字节）。本次更改仅限本段与下文 D3 的表述；D1、D2 两行未动。逐字前后对照、前后哈希与依据链见 `refine-logs/REC-P2_PLAN_STALENESS_CORRECTION_V1_20260824.md`。`EXPERIMENT_AUDIT.md` 第 34 行本身仍未更正 —— 它是既有审计记录，改它需要另一次授权。

### 需要的三个决策

- D1：是否在本轮开启 R006e 生产授权。需签发 exact-SHA one-time authorization，并先补齐 repeat 与 control root。
- D2：R006f exact-support abstention 轨是否维持 abstain 立场（当前为 witness-first 弃权，无恢复承诺）。
- D3：E4 不是排期问题，而是重定范围问题。网格已跑完，故可签的不是「排期执行」。E4-R006 在 r3 字节上结构性封闭：`refine-logs/EXPERIMENT_PLAN_20260731_115719.md` 第 72 行预声明了 paired panel-level log error ratio、第 74 行预声明了等权 cell-level 置信区间，但从未序列化 CI 的构造方法与置信水平，现在补任何取值都属审计禁止的 post-outcome substitution；解封需要出示 r3 之前的 pre-outcome CI 规格，否则要新的 pre-outcome 声明加重跑（属独立授权事项）。E4-R007 则无需任何新执行，只需按 r3 审计 required next action 第 2 条，对已冻结的 8 个 interval cell、160 条 interval record 做一次独立 result-to-claim 复核。既有边界不变：单次执行不构成 repeated-run reproducibility；主张上限为每 cell 20 个模拟 panel、horizon 4、`simulation_only`，不支撑 empirical calibration、更广 uncertainty validity 或其他 horizon。详见 `refine-logs/REC-P2_AUTHORIZATION_DRAFTS_V1_20260824.md` 的 D3。

### 授权文本须写入的残余风险

`flock` 仅 advisory，只保护协作写者。能同时控制 role roots 与 trusted control ledger 的行为者超出本地内容寻址威胁模型，需外部 append-only witness 才可进入生产授权。Python 依赖导入与 cache 目录初始化发生在 CP authorization gate 之前。

## P3（本轮不主推）经验证据解封路线

`PAPER_CLAIM_AUDIT` 的五项 required closure evidence 与 `EMPIRICAL_IMPLEMENTATION_AUDIT` 的三项 release condition 指向同一条路径：对 `psa-20260719-rcep-03`（36 文件）与 `psa-20260719-nyc-01`（18 文件）做数值级独立审计，再做独立 paper-to-evidence 审计，再取得单独的 downstream-build 与 promotion 授权，重建稿件与图包，最后由独立 post-regeneration 复核确认无 FATAL / CRITICAL。

被封锁量不得在 M5 改稿中复活：selected CP ranks 与 rank-validation losses、reconstructed coefficient paths 与 topology contrasts、GIRFs 与聚合/配对传播度量与网络份额、half-decay 与 stability 摘要、signed frozen/evolving ratios 及相关回归、fixed-path 与 full-path bootstrap 区间、以及全部 RCEP / NYC 图表。

陈旧工件哈希只可用于识别 stale 对象，不得作为科学证据：RCEP `bacaa2ac54a4d12b3a25829c5da9ee5763856679355569ae1c24683d1b6b4920`，NYC `d204627f2bdd83bbc9c361e0644f7362e504aacb5f5bd03cad688f13882f751f`。archived full-fit losses `1.0144843433`（RCEP）与 `0.7194454937`（NYC）属 stale。

P1 与 P3 的交界：26 个 M5 单元全部落在 synthetic controlled benchmark 与边界表述上，不依赖 RCEP / NYC 数值，因此 P1 可在 P3 未解封的前提下独立收口；但改稿后不得让任何 RCEP / NYC 数字进入 active 源。

## 依赖关系

P0 是 P1 第 7 步与整个 P3 的前置。P1 第 1 至 5 步只读 `refine-logs` 下已落地的 md / json，可与 P0 并行。P2 只需作者决策，不占执行资源。P3 依赖 P0 的 git tracked/clean 与作者的 downstream 授权。

## 本轮授权边界声明

本文件是本轮唯一新增产物。未修改 `manuscript_src`、formal register、`refine-logs` 下任何冻结记录、authorization 文件、scientific payload、generated TeX。未执行任何 git 操作、任何 `make` 目标、任何测试、任何 scientific entry。scientific execution 与 claim activation 均保持 `NOT_AUTHORIZED`。
