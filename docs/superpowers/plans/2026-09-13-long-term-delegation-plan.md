# NatCS 长期工作与子代理派发总控计划

> 本文件是后续长期工作的派发入口。它合并已有计划与当前收据的有效约束，只规划任务，不改变科学结论、外部闸门状态或 Git 快照。

## 1. 当前基线

- 分支：`codex/m5-current-luna-science-recheck`。
- 工作树已有用户和历史未提交修改。所有代理必须保留这些修改，不得重置、清理、提交、打标签、合并或推送。
- 本地发布链最近一次成功基线由 `REC-P6_POST_DECISION_REBUILD_V1_20260903` 与 `REC-P6_WEEKLY_MAINTENANCE_V1_20260903` 记录。
- 本地检查基线：final gate 为 `225 passes / 0 errors`；release safety 为 `0 blockers / 0 warnings`；focused suite 为 `8/8`。
- 当前作者决策：`RC-1 = ACTIVATED`；`RC-2 = ACTIVATED_WITH_LIMITATIONS`；`RCEP F3 = not_identified`。
- 四组外部闸门仍开放：作者确认、Fig. 2 真实投稿门户观察、原始数据访问/许可、public-release readiness。
- 真实科学证据边界：当前最强贡献是 query-preserving representation/estimand principle；不能把它表述为 CP estimator superiority。
- 最新 endpoint-aware qualification 不能与早期正向 benchmark 混称：CP `0/16`、Tucker `6/16`、native Tucker `0/8`，当前没有候选方法获晋级。
- `EXPERIMENT_TRACKER.md` 中 E4-R006、E4-R007、E4-R009 为 `BLOCKED`，E4-R008 仅允许 artifact-level descriptive use；恢复跟踪器中 REC-M0/M1 为 `PASS`，REC-M2 至 M5 为 `BLOCKED`。

## 2. 不可突破的边界

1. 本地构建、surrogate、静态测试和文件存在性都不能代替外部门户、许可、作者授权或 DOI 记录。
2. 不得擅自激活 RCEP/NYC 的新经验性数值、RCEP F3、native held-out topology recovery 或任何 `POTENTIAL_ONLY_NOT_ACTIVATED` 内容。
3. 不得把历史 `EXPERIMENT_AUDIT` 的 `FAIL` 改写成总体 `PASS`；新审计只能明确其作用域与当前 downstream-build gate 的关系。
4. 不得把 CP/Tucker endpoint availability 写成 identification、recovery、causal effect 或 estimator superiority。
5. 不得在没有明确实验授权、预注册协议和输入冻结前重跑科学实验。
6. 不得生成新的 hash/SHA256 内容；只有现有仓库流程明确要求时，才能更新由流程生成的元数据。
7. 任何源稿、数字、图、估计器、运行清单、许可或发布状态的修改，都必须有对应证据记录并触发完整重建。

## 3. 长期工作流

### WS-A：状态与证据治理（最高优先级）

目标是维护单一、可追溯的状态图，区分历史审计、当前源稿、生成包和外部证据。

- 维护 claim-evidence ledger，补齐每条 active claim 的来源、scope、允许措辞、禁止延伸和当前 review status。
- 核对 `empirical_run_manifest.json`、生成摘要、运行清单和收据之间的权威关系；发现 RCEP rank 1/2、Figure 4 network-share estimand 等冲突时先登记，再由作者或科学负责人决定。
- 为每次实质变更创建日期化 Markdown/JSON receipt，保留 previous state、evidence reference、resulting state。
- 维持四个外部闸门独立计数，禁止用一个闸门的状态推导其他闸门。

### WS-B：实验复现与 claim-evidence ledger

目标是只在授权后处理实验，不让历史或 quarantine 结果意外进入当前稿件。

- 首先审计 E4-R006 至 E4-R009 和 REC-M2 至 M5 的阻塞原因、输入冻结条件和缺失产物。
- 若获得新的 pre-outcome authorization，单独执行 construction、execution、audit、result-to-claim 四步，并保留 unavailable、unstable、failed rows。
- 对 RCEP/NYC 仅允许 corrected implementation 的受控重建；在重建和复审前，C006-C008 的数值 claim 保持 blocked。
- 任何实验代理都不得直接修改 active manuscript source；它只能交付结果、证据路径和 promotion request。

### WS-C：理论、证明和实现契约维护

目标是保持表示理论、对角结构化逆、finite-horizon transfer bound、ridge Schur complement 和 weak-separation 诊断的一致性。

- 维护 theorem/proposition 的假设、适用域和反例边界。
- 检查公式与实现是否一致，尤其是 Figure 4 network-share estimand 和 joint ridge update。
- 只增加能验证既有契约的测试，不为不可能场景添加防御性分支或宽泛错误吞除。

### WS-D：稿件、图表和数字一致性

目标是确保 active manuscript 只使用已授权、可定位、可重建的 evidence object。

- 检查摘要、Introduction、Results、Discussion、Methods、Supplementary Notes、Figure captions 和 availability statements 的 claim scope。
- 把“controlled N=15/N=30 benchmark”“endpoint-aware qualification”“RCEP/NYC descriptive checks”分成不同证据层级。
- Figure 2 只接受真实门户观察关闭预览行；本地 surrogate 只能作为 gate test。
- 图源、figure package、manuscript package、reviewer archive 和 upload freeze 必须由同一 build chain 产生。

### WS-E：发布包与外部闸门

目标是把本地 readiness 维护到真实提交日，且不伪造外部闭环。

- 处理作者决定、真实门户预览、raw-source access/licence、repository/DOI/licence/public release 四类外部输入。
- 每类输入都记录来源、日期、原文观察或授权、受影响行、previous state 和 resulting state。
- 只有明确授权和完整证据到位后，才运行完整发布链并更新 upload-freeze manifest。
- 提交日记录 manuscript ID、timestamp、uploaded version、portal messages；没有确认时使用 `UPLOAD_NOT_CONFIRMED`。

### WS-F：测试、构建和审计基础设施

目标是让代理能快速验证局部变更，并保持最终链条可重复。

- 维护 focused suite、final gate、release safety、source-only gate 和路径清理测试。
- 对生成器、清单和收据 schema 增加最小必要的回归测试。
- 任何构建失败先定位真实契约或输入问题，不用延长 timeout、静默默认值或后处理补丁掩盖失败。

## 4. 可派发任务矩阵

每行是一个单一目标。代理必须只修改“允许修改”列中的文件；未列文件只能读取。

| ID / 优先级 | 子代理目标 | 允许修改范围 | 前置依赖 | 交付物 | 验收标准 |
|---|---|---|---|---|---|
| A1 / P0 | 建立当前状态与历史审计映射 | 新建 `refine-logs/REC-STATUS-RECONCILIATION_*.md/.json` | 读取三份审计和 P6 收据 | scope/verdict/condition 表 | `jq` 路径有效；历史 FAIL 保留；`git diff --check` 通过 |
| A2 / P0 | 审计 claim-evidence ledger 缺口 | `manuscript_src/natcs/claim_evidence_ledger.csv`，仅在有证据时改 | A1 状态映射 | 缺口表和最小 ledger 修订 | 每条 active claim 有 evidence、scope、allowed/prohibited wording；无新数字 |
| A3 / P0 | 核对运行清单和 estimand 冲突 | 新建审计 receipt；必要时仅修改 `empirical_run_manifest.json` 的已授权字段 | A1；需科学负责人决定冲突处理 | 冲突清单、决定请求、影响分析 | 未获决定时保持 blocked；不自行选择 rank 或公式 |
| A4 / P0 | 周期性外部闸门维护 | 四个 worksheet 只读；无证据时不改源文件 | 当前 P6 基线 | maintenance receipt（仅有实质发现才建） | final gate 0 errors；release safety 0 blockers/warnings |
| B1 / P0 | 处理一批真实作者决定 | 仅修改作者决定直接涉及的 worksheet 和对应 receipt | 收到带来源的明确回复 | decision receipt `.md/.json` | 每行有日期、来源、原文授权、previous/resulting state；无隐含授权 |
| B2 / P0 | 处理真实 Fig. 2 门户观察 | `ncs_fig2_portal_preview_checklist.md`；失败时才改 surrogate generator | 实际门户/期刊预览 | portal observation receipt 和截图路径 | 只关闭实际观察支持的行；surrogate 不关闭 portal gate |
| B3 / P0 | 处理 raw-source/public-release 决定 | 对应两个 worksheet 和 receipt | 作者/机构/提供方的明确记录 | access/release decision receipt | 无 DOI、许可、公开访问或可再分发推断 |
| C1 / P1 | 审计 R006 endpoint-aware 证据边界 | 只读 `r006c_*`、`claim_evidence_ledger.csv`、相关测试；新建审计记录 | A1 | promotion/blocking memo | 明确 CP 0/16、Tucker 6/16、native Tucker 0/8；不改变 active claim |
| C2 / P1 | 审计 E4-R006~R009 阻塞恢复条件 | 只读 `refine-logs/` 和 `scripts/experiments/`；新建恢复清单 | C1 | 每项 blocker、所需授权、缺失产物 | 不执行实验；每个 blocker 可定位到文件/协议 |
| C3 / P1 | 理论与实现契约复核 | `tests/test_natcs_theory_contract.py` 及对应 receipt；不改科学公式 | 已确认公式冲突范围 | contract review | 现有理论测试通过；不增加一次性抽象或不可能分支 |
| D1 / P1 | 稿件 claim scope 一致性审计 | 只读 `manuscript_src/natcs/*.md`；新建 issue/receipt | A2、C1 | source-only findings | active 数字均能落到 evidence；quarantine fence 保持 |
| D2 / P1 | Figure 4 estimand 一致性审计 | 只读 figure builder、manifest、caption、测试；新建审计记录 | A3 | formula-to-code mapping | 公式、代码、caption、manifest 一致；未决则保持 blocked |
| D3 / P1 | 构建链与 package inventory 审计 | 只读 Makefile/generators/output manifests；新建 receipt | 任一 accepted source change 后 | package inventory comparison | 五个 make target 顺序正确；无下游遗漏 |
| E1 / P1 | 实施授权后的完整重建 | 生成输出目录与对应 dated receipt；不得改源稿 | B1/B2/B3 的 accepted change | evidence/manuscript/archive/materials/freeze package | focused suite 8/8；五目标全 0；final gate 0 errors |
| E2 / P1 | 独立 post-regeneration review | 只读生成包、tests、receipts；新建 review receipt | E1 | PASS/WARN/FATAL/CRITICAL 分类 | 无 FATAL/CRITICAL；active/inactive 边界完整 |
| F1 / P2 | 测试与门禁维护 | 只改明确失败对应的 `tests/` 或 `scripts/` 文件 | 已复现失败 | 最小代码修复和回归测试 | 先复现再修复；不靠放宽断言或 timeout |
| F2 / P2 | 提交日准备与事件归档 | 只在明确提交授权后改 `submission_checklist.md` 并建事件 receipt | E2、四类外部 gate 关闭、日期和提交作者确认 | authorization/event receipts | manifest 文件名精确；记录 ID、时间、版本、门户反馈；未确认则标记 `UPLOAD_NOT_CONFIRMED` |
| F3 / P2 | Git 快照（独立动作） | 仅作者明确列出的路径 | 作者对 exact scope 的明确授权 | commit id 和 staged diff 检查结果 | 只 stage 列定文件；不由任何发布代理自动执行 |

## 5. 依赖与并行安排

```text
A1 状态映射
  ├── A2 ledger 审计 ──┐
  ├── A3 manifest/estimand 冲突 ──┤
  └── C1 endpoint 证据边界 ───────┤
                                  v
                         D1 稿件 scope 审计

B1 作者决定 ──┐
B2 Fig.2 观察 ─┼──> E1 完整重建 ──> E2 独立复审
B3 数据/发布决定 ─┘                         │
                                            v
                                   F2 提交日归档

C2 实验恢复条件、C3 理论契约、D2 Figure 4 审计、D3 构建审计
可在 A1 后并行；其结果不能绕过 B/E 链直接激活 claim。
```

可并行：A2、A3、C1、C2、C3、D2、D3（均为读取/审计或互不共享写入）。

必须串行：任何作者/门户/许可决定 -> E1 -> E2 -> F2；任何源稿、公式、实验输入或数字变更 -> focused suite -> 五目标 build chain -> final gates。

## 6. 优先级、停止条件和回收规则

- **P0**：状态映射、证据 ledger、外部决定 intake。没有这些结果，不派发激活或发布任务。
- **P1**：理论/稿件/图表/构建审计，以及有授权后的重建和独立复审。
- **P2**：周期性测试维护、提交日操作和独立 Git 快照。
- 任一 final-gate error、release-safety blocker/warning、focused-test failure、证据来源含糊、许可不明、门户观察不完整、数值冲突或授权范围不清，立即停止下游任务并回收给 `/root`。
- 代理不得用叙述把 `WARN` 降级为 `PASS`，也不得把 `PASS_WITH_WARNINGS_ALLOWED` 解读为外部闸门已关闭。
- 代理发现超出文件范围的问题时，只提交 finding 和建议，不顺手扩展范围。
- 同一任务连续两次因同一外部条件无法推进，应标记 `BLOCKED_EXTERNAL_DEPENDENCY`；不要重复生成无新证据的 receipt。

## 7. 代理返回格式

每个代理完成后必须返回以下字段：

```text
Task ID:
Status: PASS | PASS_WITH_FOLLOW_UP | BLOCKED_EXTERNAL_DEPENDENCY | FAIL
Objective:
Findings:
Changed files:
Evidence references:  path:line or receipt id
Commands/tests:
Results:
Open blockers:
Next dependency:
```

若没有修改文件，明确写 `Changed files: none`。若运行命令会重建 `output/`，说明其是否覆盖了下游包；不得把生成目录变化误报为源稿变更。

## 8. 标准验收命令

维护性检查：

```bash
node scripts/check_natcs_final_gates.mjs
node scripts/audit_natcs_release_safety.mjs --check
git diff --check
```

接受源稿或外部门决策后的 focused suite：

```bash
node --test \
  tests/test_natcs_submission_support_disabled.mjs \
  tests/test_natcs_active_manuscript_source_only.mjs \
  tests/test_natcs_inactive_empirical_source_gate.mjs \
  tests/test_natcs_fig2_surrogate_gate.mjs \
  tests/test_empirical_results_numeric_alignment.mjs \
  tests/test_natcs_source_empirical_boundary.mjs \
  tests/test_natcs_release_gate.mjs \
  tests/test_natcs_reviewer_archive_path_sanitization.mjs
```

完整发布链必须按顺序运行：

```bash
make natcs-evidence
make natcs-manuscript
make natcs-reviewer-archive
make natcs-submission-materials
make natcs-upload-freeze-manifest
```

当前基线参考数量：submission materials `27`、upload-freeze artifacts `11`、reviewer archive `342`。数量变化必须能追溯到已接受的输入变化。

## 9. 总体完成定义

长期阶段只有在以下条件同时满足时才算完成：每个已关闭外部 marker 有日期化证据；每个 active claim 有可定位 evidence object；最近一次接受变更经过 focused suite、完整 build chain 和 final/release-safety gates；独立 post-regeneration review 没有 FATAL/CRITICAL；提交事件 receipt 具备 manuscript ID、时间、上传版本和门户反馈。没有这些条件时，状态只能写作 readiness maintenance 或 build complete with external gates open。
