# E4 实验跟踪表

| Run ID | Milestone | Purpose | System / Variant | Split / Grid | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| E4-R001 | M0 | 证明 domain-uniform stability envelope | Family 1/2 exact contract | $\lVert W\rVert_\infty\leq1$, $\eta=0.90$ | block envelope, spectral-radius bound | MUST | PASS | 18 个 Fraction endpoint；proof SHA `8ebf5c63...`；不使用 held-out outcome |
| E4-R002 | M0 | public interface tracer test | native fit/evaluate | forced out-of-envelope fixture | fitted block envelope, query independence | MUST | PASS | fit 后、query 前投影；public fit 无 query 参数 |
| E4-R003 | M1 | 覆盖 selection/evaluation/bootstrap refit | three native methods | fixture-only | route coverage, status retention | MUST | PASS | selection/evaluation/refit/retuning 同路；threshold 固定 0.98 |
| E4-R004 | M2 | v4 schema/artifact binding | candidate package | source-only | semantic validators, hashes | MUST | PASS | r2 candidate SHA `9213cec8...`；八项 artifact；root 尚不存在 |
| E4-R005 | M2 | trust/preflight refusal | authorized executor | missing/mismatched trust cases | refusal before science/root creation | MUST | PASS | 73 tests + 独立复核 PASS；仅表示拒绝与 readiness，不授权 science |
| E4-R006 | M3 | 两 family held-out recovery | local/smoother/fixed-rank | 2 families × 2 N × 2 query × 2 H × 20 panels | response/operator MSE, paired ratios, failures | MUST | BLOCKED | r2 consumed-incomplete；r3 candidate SHA `0c49bca6...` 已单次执行并冻结；inventory SHA `5cf086c4...`；scoped integrity audit=`WARN`；独立 result-to-claim=`partial`（high confidence）；预注册 panel-level log-error-ratio 及其 CI 未序列化，不得进入稿件 |
| E4-R007 | M4 | uncertainty qualification | fixed-rank basis | H=4, 8 cells, 20 panels, 80 bootstrap | simultaneous coverage, width, statuses | MUST | BLOCKED | r3 冻结结果含 8 cells、160 panel records，且每 panel 记录 80 bootstrap replicates；不对成功子集条件化；独立 result-to-claim=`partial`（medium confidence）；证据上限为 simulation-only、H=4、20 panels/cell；不得激活 |
| E4-R008 | M4 | isolated duplicate + claim audit | frozen output + independent derived artifact | full grid | deterministic equality, claim fidelity | MUST | PASS | primary/duplicate content-addressed roots agree; gate receipt `NCS_E4_R008_DUPLICATE_CLAIM_FIDELITY_20260810.json`; derived metric remains artifact-only/descriptive, claim activation and manuscript/figure promotion remain blocked |
| E4-R009 | M5 | NCS activation decision | manuscript claim map | audited evidence only | novelty/generality/rigour/significance | MUST | BLOCKED | build 与 promotion 单独保持关闭 |

Status values: `TODO`, `RUNNING`, `PASS`, `FAIL`, `BLOCKED`, `CUT`.

Controlling boundary: `PAPER_CLAIM_AUDIT=BLOCKED`,
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`. The E4-r3 synthetic outcome remains in
its quarantine root and is not authorized for manuscript use. No downstream
build, manuscript promotion or audit-status change is authorized.
