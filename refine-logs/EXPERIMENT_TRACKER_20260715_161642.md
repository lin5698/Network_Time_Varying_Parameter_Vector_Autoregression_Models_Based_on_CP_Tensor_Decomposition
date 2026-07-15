# 实验跟踪表

| Run ID | Milestone | Purpose | System / Variant | Split / Grid | Metrics | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | M0 | 验证 single-topology 非识别 | Exact linear construction | N=3/5 toy | kernel inclusion, endpoint gap | MUST | TODO | 不依赖统计模拟 |
| R002 | M0 | 验证 multi-topology query condition | Exact linear construction | 2-6 stored topologies | rank, identified dimension, query error | MUST | TODO | 含 full-rank 与 partial-query cases |
| R003 | M0 | 审计 response metrics | Truth vs perturbed operators | H=1/4/8; rho=0.5/0.95/1.01 | raw and stabilized errors | MUST | TODO | 禁止 stabilization 掩盖 failure |
| R004 | M0 | 验证 seed 和配对设计 | Existing benchmark harness | N=15; 3 seeds rerun | exact checksums, paired rows | MUST | TODO | 为后续扩展建立 deterministic contract |
| R005 | M1 | separation x stability pilot | Local/CP/Tucker/fused | N=20,T=200,10 seeds | operator/GIRF/frozen errors | MUST | TODO | 第一 stop-go run |
| R006 | M1 | approximate-rank pilot | CP/Tucker/fused | rank decay grid,10 seeds | error, selected rank, bias | MUST | TODO | 排除 exact CP DGP 优势 |
| R007 | M1 | temporal misspecification pilot | CP/Tucker/fused/local | smooth/abrupt/non-factor paths | error, failure | MUST | TODO | 预先声明 negative region |
| R008 | M1 | topology measurement pilot | Same-target methods | edge drop/weight noise | endpoint and topology errors | MUST | TODO | 对齐 uniform topology bound |
| R009 | M1 | 实现 temporal fused baseline | Fused/spline TVP-NVAR | chronological validation | validation loss, response error | MUST | TODO | 强 classical baseline |
| R010 | M1 | 数值实现规模审计 | NumPy/JAX port vs JS | N=20/50/100 | runtime, memory, equality | MUST | TODO | N>=100 前置条件 |
| R011 | M2 | 扩展 N=50 主行 | Local/CP/Tucker/fused/collapsed | 20 paired reps | 4 endpoint errors, cost | MUST | TODO | 消除 bounded stress |
| R012 | M2 | N=20 主 phase grid | Core methods | 50 paired seeds | paired effects, IQR/CI | MUST | TODO | Main Fig. 2 source |
| R013 | M2 | N=50 phase grid | Core methods | 20-50 paired seeds | paired effects, IQR/CI | MUST | TODO | 资源允许后扩到50 |
| R014 | M2 | N=100 core grid | Core scalable methods | 20 paired seeds | error, stability, cost | MUST | TODO | 先小 grid |
| R015 | M2 | rank-selection audit | CP/Tucker/fused | chronological grid | selection frequency, test error | MUST | TODO | 禁止 oracle rank headline |
| R016 | M2 | horizon sensitivity | Core methods | H=1/4/8/12 | response error growth | MUST | TODO | 对齐 H(H+1)/2 bound |
| R017 | M2 | negative-region audit | Core methods | eta low/rho high/misspecified rank | failure map | MUST | TODO | 主文 operating regime |
| R018 | M3 | 一阶 basis family | Basis CP/Tucker/collapsed | A+B1W | availability, recovery | MUST | TODO | 现有模型重构 |
| R019 | M3 | 二阶 diffusion family | Basis CP/Tucker/collapsed | A+B1W+B2W2 | availability, recovery | MUST | TODO | Generalization gate |
| R020 | M3 | 受限 collapsed inverse | Diagonal/sparse blocks | known supports | condition pass/fail, error | MUST | TODO | 避免 universal impossibility overclaim |
| R021 | M3 | adversarial equivalence stress | Exact + noisy maps | rank tolerances | endpoint gap | MUST | TODO | Theory figure source |
| R022 | M4 | DCRNN protocol smoke test | Public implementation | synthetic N=20; 3 seeds | forecast, query error | MUST | TODO | 需 GPU；先验证 adjacency swap |
| R023 | M4 | 第二 native graph baseline | Supplied-adjacency model | synthetic N=20; 3 seeds | forecast, query error | MUST | TODO | 选择前检查维护状态和许可证 |
| R024 | M4 | baseline tuning parity | All strong baselines | fixed trial budget | best val/test, trials, params | MUST | TODO | Main Table 2 audit |
| R025 | M4 | N=200 scaling | CP/Tucker/fused/local subset | 10 paired seeds | runtime, memory, error | MUST | TODO | 失败也需报告 |
| R026 | M4 | prediction-query Pareto | All eligible models | synthetic + applications | forecast vs query error | MUST | TODO | 不合并为单一排名 |
| R027 | M5 | coherent bootstrap smoke | Series-level MBB | N=20; 100 draws | coverage, width, runtime | MUST | TODO | 与 independent-window sensitivity 分离 |
| R028 | M5 | bootstrap calibration grid | MBB/dependent wild | N=20; 500 draws; 100 DGP reps | 90/95 coverage | MUST | TODO | 成本 gate |
| R029 | M5 | near-stability coverage | Best coherent bootstrap | rho=0.8/0.95/0.99 | coverage, failure, width | MUST | TODO | 可能形成限制结论 |
| R030 | M5 | empirical uncertainty rerun | Final method | RCEP/NYC/EIA | interval and sensitivity comparison | MUST | TODO | 不覆盖旧结果，另存版本 |
| R031 | M6 | EIA 数据获取与 schema audit | EIA-930 official data | BA load/interchange | completeness, provenance | MUST | TODO | outcome inspection 前完成 |
| R032 | M6 | EIA preregistration freeze | Analysis contract | Uri/pre-event/placebos | frozen config checksum | MUST | TODO | 先冻结再计算 response |
| R033 | M6 | EIA topology construction | Directed interchange shares | hourly/daily variants | coverage, turnover, stability | MUST | TODO | 不按效果挑网络定义 |
| R034 | M6 | EIA model selection | CP/Tucker/fused | chronological split | forecast, rank, diagnostics | MUST | TODO | 只用 pre-event tuning |
| R035 | M6 | EIA topology readouts | Final selected models | event/frozen/attenuated | response contrast, uncertainty | MUST | TODO | descriptive, non-causal |
| R036 | M6 | EIA placebo and robustness | Final selected models | placebo windows/topology rules | placebo rank, stability | MUST | TODO | Broad-impact application gate |
| R037 | M7 | Claim-to-evidence audit | All outputs | final tables/figures | pass/fail by C1/C2 | MUST | TODO | 决定是否再冲高 |
| R038 | M7 | Target-journal decision | Manuscript package | scope comparison | evidence sufficiency | MUST | TODO | 未通过则转专业期刊 |

Status values: `TODO`, `RUNNING`, `PASS`, `FAIL`, `BLOCKED`, `CUT`.
