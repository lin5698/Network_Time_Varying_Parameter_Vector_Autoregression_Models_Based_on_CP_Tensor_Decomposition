# E4 实验跟踪表

| Run ID | Milestone | Purpose | System / Variant | Split / Grid | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| E4-R001 | M0 | 证明 domain-uniform stability envelope | Family 1/2 exact contract | $\lVert W\rVert_\infty\leq1$, $\eta=0.90$ | block envelope, spectral-radius bound | MUST | PASS | 18 个 Fraction endpoint；proof SHA `8ebf5c63...`；不使用 held-out outcome |
| E4-R002 | M0 | public interface tracer test | native fit/evaluate | forced out-of-envelope fixture | fitted block envelope, query independence | MUST | PASS | fit 后、query 前投影；public fit 无 query 参数 |
| E4-R003 | M1 | 覆盖 selection/evaluation/bootstrap refit | three native methods | fixture-only | route coverage, status retention | MUST | PASS | selection/evaluation/refit/retuning 同路；threshold 固定 0.98 |
| E4-R004 | M2 | v4 schema/artifact binding | candidate package | source-only | semantic validators, hashes | MUST | PASS | r3 candidate SHA `0c49bca6...`；八项 artifact；新 root 尚不存在 |
| E4-R005 | M2 | trust/preflight refusal | authorized executor | missing/mismatched trust cases | refusal before science/root creation | MUST | PASS | 73-test receipt + 独立复核 PASS；仅表示 pre-outcome readiness |
| E4-R006 | M3 | 两 family held-out recovery | local/smoother/fixed-rank | 2 families × 2 N × 2 query × 2 H × 20 panels | response/operator MSE, paired ratios, failures | MUST | BLOCKED | r2 consumed-incomplete；r3 SHA `0c49bca6...` 静态就绪，等待 exact authorization |
| E4-R007 | M4 | uncertainty qualification | fixed-rank basis | H=4, 8 cells, 20 panels, 80 bootstrap | simultaneous coverage, width, statuses | MUST | BLOCKED | 依赖完整 frozen output；不允许成功子集条件化 |
| E4-R008 | M4 | isolated duplicate + claim audit | frozen output | full grid | deterministic equality, claim fidelity | MUST | BLOCKED | 依赖完整 frozen output；不授权 promotion |
| E4-R009 | M5 | NCS activation decision | manuscript claim map | audited evidence only | novelty/generality/rigour/significance | MUST | BLOCKED | build 与 promotion 单独保持关闭 |

Status values: `TODO`, `RUNNING`, `PASS`, `FAIL`, `BLOCKED`, `CUT`.

Controlling boundary: `PAPER_CLAIM_AUDIT=BLOCKED`,
`EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`; no r3 scientific execution, downstream
build, manuscript promotion or audit-status change has been authorized.
