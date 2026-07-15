# Research Output Manifest

> Auto-maintained by ARIS skills. Tracks all generated artifacts across the research lifecycle.

| Timestamp | Skill | File | Stage | Description |
|-----------|-------|------|-------|-------------|
| 2026-07-15 16:16 | /experiment-plan | refine-logs/EXPERIMENT_PLAN_20260715_161642.md | implementation | 高影响重投的 claim-driven 实验计划，含五个 evidence blocks、资源预算与 stop-go gates |
| 2026-07-15 16:16 | /experiment-plan | refine-logs/EXPERIMENT_PLAN.md | implementation | 最新实验计划副本 |
| 2026-07-15 16:16 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER_20260715_161642.md | implementation | 38 个 theory、simulation、baseline、scale、uncertainty 和 EIA runs 的执行跟踪表 |
| 2026-07-15 16:16 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | implementation | 最新实验跟踪表副本 |
| 2026-07-15 16:16 | /formula-derivation | DERIVATION_PACKAGE.md | implementation | Query identifiability、local recovery、low-rank projection 与 response transfer 的理论推导包 |
| 2026-07-15 16:27 | /run-experiment | scripts/experiments/query_identifiability_checks.mjs | implementation | R001/R002 query-identifiability 精确验证脚本 |
| 2026-07-15 16:27 | /run-experiment | output/high_impact_revision/query_identifiability_checks.json | implementation | R001/R002 结构化运行结果，status PASS |
| 2026-07-15 16:27 | /run-experiment | output/high_impact_revision/query_identifiability_checks.md | implementation | R001/R002 人类可读结果摘要 |
| 2026-07-15 16:27 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER_20260715_162744.md | implementation | 标记 R001/R002 PASS 的版本化跟踪表 |
| 2026-07-15 16:27 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | implementation | 标记 R001/R002 PASS 的最新跟踪表 |
| 2026-07-15 17:20 | /run-experiment | scripts/experiments/audit_response_metrics.mjs | implementation | R003 旧 response metric 的标量反例审计脚本 |
| 2026-07-15 17:20 | /run-experiment | output/high_impact_revision/response_metric_audit.json | implementation | R003 结构化审计结果；legacy pre-evaluation stabilization 标记为 ACTION_REQUIRED |
| 2026-07-15 17:20 | /run-experiment | output/high_impact_revision/response_metric_audit.md | implementation | R003 人类可读审计摘要，记录误差压缩与抹除反例 |
| 2026-07-15 17:20 | /run-experiment | scripts/experiments/check_benchmark_reproducibility.mjs | implementation | R004 隔离输出的 deterministic duplicate-run 检查 |
| 2026-07-15 17:20 | /run-experiment | output/high_impact_revision/benchmark_reproducibility_check.json | implementation | R004 结构化结果；4 个方法的 deterministic fields 完全匹配 |
| 2026-07-15 17:20 | /run-experiment | output/high_impact_revision/benchmark_reproducibility_check.md | implementation | R004 人类可读复现性摘要 |
| 2026-07-15 17:20 | /run-experiment | scripts/natcs_benchmarks.mjs | implementation | 支持 NATCS_BENCHMARK_OUTPUT_DIR，使审计运行与已投稿 canonical outputs 隔离 |
| 2026-07-15 17:44 | /test-driven-development | scripts/experiments/test_high_impact_metrics.py | implementation | R003 新指标契约测试：特征值半径、raw error、稳定性合格误差与独立投影敏感性 |
| 2026-07-15 17:44 | /test-driven-development | scripts/experiments/high_impact_metrics.py | implementation | R003 独立 NumPy 指标模块；不在主 response metric 前稳定化算子 |
| 2026-07-15 17:44 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER_20260715_174454.md | implementation | 标记 R003/R004 PASS 的版本化跟踪表 |
| 2026-07-15 17:44 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | implementation | 标记 R003/R004 PASS 的最新跟踪表 |
| 2026-07-15 17:50 | /run-experiment | refine-logs/R005_PROTOCOL_20260715.md | implementation | outcome-blind separation x stability pilot 协议、指标契约与 frozen stop-go rules |
| 2026-07-15 17:56 | /test-driven-development | scripts/experiments/test_r005_separation_stability_pilot.py | implementation | R005 DGP 半径、separation、metric storage 与相对输出目录回归测试 |
| 2026-07-15 17:56 | /run-experiment | scripts/experiments/r005_separation_stability_pilot.py | implementation | R005 NumPy/SciPy runner，含 local、CP、Tucker、temporal spline 与隔离输出 |
| 2026-07-15 17:57 | /run-experiment | output/high_impact_revision/r005_phase_pilot/r005_replications.csv | implementation | R005 3x3 grid、10 seeds、4 methods 的 360 条 replication-level 结果 |
| 2026-07-15 17:57 | /run-experiment | output/high_impact_revision/r005_phase_pilot/r005_summary.csv | implementation | R005 cell-level median/IQR 与 failure summary |
| 2026-07-15 17:57 | /run-experiment | output/high_impact_revision/r005_phase_pilot/r005_paired_improvements.csv | implementation | R005 相对 local 的 paired raw-response improvements |
| 2026-07-15 17:57 | /run-experiment | output/high_impact_revision/r005_phase_pilot/r005_results.json | implementation | R005 结构化配置、环境、frozen checks 与 stop-go PASS 结果 |
| 2026-07-15 17:57 | /run-experiment | output/high_impact_revision/r005_phase_pilot/r005_results.md | implementation | R005 人类可读审计摘要；记录 exact-rank pilot 边界 |
| 2026-07-15 18:02 | /experiment-plan | refine-logs/EXPERIMENT_PLAN.md | implementation | 将 Apple M5 Metal 4 纳入 R010/R022 后端评估路线，未将未安装框架标为可用 |
| 2026-07-15 18:02 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER_20260715_180212.md | implementation | 标记 R005 PASS 并记录 Mac GPU 后端待审计的版本化跟踪表 |
| 2026-07-15 18:02 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | implementation | 标记 R005 PASS 的最新跟踪表 |
| 2026-07-15 18:08 | /ablation-planner | refine-logs/R006_R007_ABLATION_PLAN_20260715.md | implementation | reviewer-led approximate-rank 与 temporal/subspace misspecification 消融设计 |
| 2026-07-15 18:08 | /run-experiment | refine-logs/R006_PROTOCOL_20260715.md | implementation | outcome-blind R006 grid、absolute recovery metrics 与 frozen stop-go rules |
| 2026-07-15 18:17 | /test-driven-development | scripts/experiments/test_r006_approximate_rank_pilot.py | implementation | R006 a3/radius calibration、fused-TV、rank schema 与 smoke-report 回归测试 |
| 2026-07-15 18:17 | /run-experiment | scripts/experiments/r006_approximate_rank_pilot.py | implementation | R006 8-component calibrated-tail runner，含 local/spline/fused-TV/CP/Tucker ranks 2/3/5 |
| 2026-07-15 18:17 | /run-experiment | scripts/experiments/r005_separation_stability_pilot.py | implementation | CP-ALS 新增可选 multi-start objective diagnostics，默认 R005 行为不变 |
| 2026-07-15 18:19 | /run-experiment | output/high_impact_revision/r006_approximate_rank/r006_replications.csv | implementation | R006 4x2 grid、10 seeds、9 methods 的 720 条 replication-level 结果 |
| 2026-07-15 18:19 | /run-experiment | output/high_impact_revision/r006_approximate_rank/r006_summary.csv | implementation | R006 cell-level median/IQR、absolute recovery、zero-operator normalization 与 runtime summary |
| 2026-07-15 18:19 | /run-experiment | output/high_impact_revision/r006_approximate_rank/r006_results.json | implementation | R006 结构化配置与 frozen gate FAIL；rho=0.80 absolute operator cells 未通过 |
| 2026-07-15 18:19 | /run-experiment | output/high_impact_revision/r006_approximate_rank/r006_results.md | implementation | R006 人类可读 gate breakdown，保留全部负面 cells |
| 2026-07-15 18:26 | /result-to-claim | findings.md | implementation | C2 partial/high-confidence verdict、工作 claim、unsupported claims 与后续路由 |
| 2026-07-15 18:26 | /result-to-claim | refine-logs/R006_AUDIT_20260715.md | implementation | R006 FAIL 审计与 stability-signal confound 定量诊断 |
| 2026-07-15 18:28 | /experiment-plan | refine-logs/R006B_DESIGN_GATE_20260715.md | implementation | fixed-query-norm 与 matched-excitation/native-VAR 两层 deconfounding 前置设计 |
| 2026-07-15 18:28 | /experiment-plan | refine-logs/EXPERIMENT_PLAN.md | implementation | 将 C2 降级为 partial 并冻结 R006b/R007 前的主文与 scale 扩展 |
| 2026-07-15 18:31 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER_20260715_183148.md | implementation | 标记 R006 FAIL、R009 PASS 并新增 R006b 的版本化跟踪表 |
| 2026-07-15 18:31 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | implementation | R006 claim verdict 后的最新实验跟踪表 |
