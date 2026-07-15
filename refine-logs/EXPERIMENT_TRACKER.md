# 实验跟踪表

| Run ID | Milestone | Purpose | System / Variant | Split / Grid | Metrics | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | M0 | 验证 single-topology 非识别 | Exact linear construction | N=2 exact toy | kernel inclusion, endpoint gap | MUST | PASS | stored gap 6.36e-17; target endpoint gap 0.308221 |
| R002 | M0 | 验证 multi-topology query condition | Exact linear construction | N=2 full/partial cases | rank, identified dimension, query error | MUST | PASS | partial rank 2/4; in-span PASS; out-of-span rejected; full rank 4/4 |
| R003 | M0 | 审计 response metrics | Truth vs perturbed operators | H=1/4/8; rho=0.5/0.95/1.01 | raw and stability-qualified errors | MUST | PASS | legacy pre-evaluation stabilization 可压缩或抹去误差，不用于新实验；独立 NumPy 指标契约 4/4 tests PASS |
| R004 | M0 | 验证 seed 和配对设计 | Existing benchmark harness | N=15; isolated duplicate runs | exact deterministic fields, paired rows | MUST | PASS | 4 methods 的 deterministic fields 完全一致；canonical benchmark SHA-256 保持 b8c881d... / c29aa14... |
| R005 | M1 | separation x stability pilot | Local/CP/Tucker/spline | N=20,T=200,10 seeds | frozen-query operator/response errors | MUST | PASS | 360/360；CP/Tucker response improvement 54.1%/53.3%；exact-rank 且部分 operator relative error 0.9-1.6，separation 梯度非全局单调，不能升级为主证据 |
| R006 | M1 | approximate-rank pilot | CP/Tucker/fused | a3=0/0.10/0.25/0.50; rho=0.80/0.95; 10 seeds | absolute/relative query recovery | MUST | FAIL | 720/720；rho=0.95 required cells PASS，rho=0.80 operator<1 gate FAIL；整体缩放混杂 stability 与 SNR，claim verdict=partial |
| R006b | M1 | stability-signal deconfounding | CP/Tucker/fused/local | fixed query Frobenius norm x rho; matched/native; 10 seeds | operator/response/SNR diagnostics | MUST | FAIL | corrected 800/800、零数值失败、integrity PASS；operator-error 0.95/0.80=1.003 且 response-transfer=1.476/1.494，但 Tucker 在 matched required cells 对 local/fused 为 -104% 至 -143%、0/10 joint wins；保留 FAIL |
| R006c | M1 | query/cancellation-preserving estimator gate | Anchor split/oracle/local/CP/Tucker/collapsed | matched/native x separation; frozen before outcomes | dual-endpoint operator/response, cancellation | MUST | FAIL | corrected 2160/2160、零失败、duplicate 非 runtime 差异 0、integrity PASS；CP 0/16、Tucker 6/16（matched 6/8、native 0/8），claim verdict=no；不升级方法主张 |
| R007 | M1 | temporal misspecification pilot | CP/Tucker/fused/local | smooth/abrupt/non-factor paths | error, failure | MUST | TODO | FROZEN：R006c 无可推广 candidate；仅在新的 prespecified estimator question 通过后才作为确认性实验，fused penalty 必须 causal rolling-prefix 选择 |
| R008 | M1 | topology measurement pilot | Same-target methods | edge drop/weight noise | endpoint and topology errors | MUST | TODO | 对齐 uniform topology bound |
| R009 | M1 | 实现 temporal fused baseline | Fused/spline TVP-NVAR | chronological validation | validation loss, response error | MUST | PASS | 向量化 fused-TV ADMM；R006b 已修正为 pre-evaluation prefix 选 penalty，25/25 tests PASS；原 R006 历史输出不覆盖，未来实验禁用 full-path validation selection |
| R010 | M1 | 数值实现规模审计 | NumPy/MLX-or-MPS port vs JS | N=20/50/100 | runtime, memory, equality | MUST | TODO | Apple M5 Metal 4 可用；当前无 MLX/PyTorch，须先做后端安装与数值等价性审计 |
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
| R022 | M4 | DCRNN protocol smoke test | Public implementation | synthetic N=20; 3 seeds | forecast, query error | MUST | TODO | 可先评估 Mac MPS；依赖/算子兼容后再验证 adjacency swap，必要时转外部 GPU |
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
