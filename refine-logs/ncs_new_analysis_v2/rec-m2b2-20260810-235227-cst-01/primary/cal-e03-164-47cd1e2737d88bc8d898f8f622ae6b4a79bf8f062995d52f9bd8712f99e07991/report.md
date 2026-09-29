# CAL-E03:164 Frozen E4-r3 Analysis

This is a deterministic, read-only derived analysis. It does not activate a claim, modify a manuscript, modify the author decision register, or start a new experiment.

- Overall verdict: **PARTIAL**
- Register item: `CAL-E03:164` / `V1-045`
- Content-addressed output directory: `cal-e03-164-47cd1e2737d88bc8d898f8f622ae6b4a79bf8f062995d52f9bd8712f99e07991`
- Input bundle SHA-256: `47cd1e2737d88bc8d898f8f622ae6b4a79bf8f062995d52f9bd8712f99e07991`

## Raw Scope Table

| Layer | Declared/observed cells | Records or attempts | Status accounting |
|---|---:|---:|---|
| recovery | 48/48 | 46080 | `{"AVAILABLE":46080,"NONCONVERGED":0,"NONFINITE":0,"OUTSIDE_TARGET":0,"UNSTABLE":0}` |
| paired completion | None/32 | raw differences retained in `paired-comparison.csv` | all status counts retained |
| interval | 8/8 | 160 | `{"AVAILABLE":160,"NONCONVERGED":0,"NONFINITE":0,"OUTSIDE_TARGET":0,"UNSTABLE":0}` |
| bootstrap | 8 interval cells | 12800 attempts | `{"AVAILABLE":12800,"NONCONVERGED":0,"NONFINITE":0,"OUTSIDE_TARGET":0,"UNSTABLE":0}` |

## Findings

1. The frozen grid covers the declared N=20/N=50, two-family, two-query, H=4/H=12 and three-method scope. Each recovery and interval row remains in the accounting; no row is filtered by status or metric value.
2. The observed recovery and interval status totals are shown above. Non-finite and missing metric counts are reported in `analysis.json`, `reproducibility.csv` and `stability.csv`; no non-finite value is converted into a passing result.
3. Cross-scale, query-stress and horizon-stress deltas are descriptive raw mean deltas only. The absent predeclared log-error-ratio/CI artifact is not reconstructed and no superiority threshold is introduced.
4. Resource verdict is **BLOCKED**: the inventory exposes one run, exit code and process-state fields, but runtime log files/telemetry are not available in this worktree. Missing telemetry: `wall_clock_seconds, cpu_time_seconds, peak_memory_bytes, peak_rss_bytes, gpu_time_seconds, per_cell_runtime`.

## Boundaries

- N=100 and N=200 were not run; no extrapolation from N=20 or N=50 is made.
- The frozen run has one execution; repeated-run reproducibility is not evaluable.
- Runtime log files are absent from this worktree, so wall time, CPU, memory and GPU telemetry are missing.
- Only descriptive N=20/N=50 status, stress, and missing-telemetry accounting is emitted.
- No RCEP, NYC, R006e, R006f, N=100, or N=200 data is read or used.
- No manuscript, author decision register, frozen quarantine file, or new scientific payload is written or activated.

## Verdict Components

| Component | Verdict |
|---|---|
| authorization_binding | **PASS** |
| cross_scale_scope | **PARTIAL** |
| failure_and_nonfinite_retention | **SUPPORTED** |
| overall | **PARTIAL** |
| resource_telemetry | **BLOCKED** |
| scoped_grid_coverage | **SUPPORTED** |
| stability_summary | **SUPPORTED** |

No next experiment was started. Any N=100/N=200 extension would require a fresh protocol, candidate and pre-outcome freeze with separate authorization.
