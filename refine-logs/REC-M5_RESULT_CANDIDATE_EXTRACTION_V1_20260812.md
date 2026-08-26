# REC-M5 Result Candidate Extraction V1

Status: `AUTHOR_CONFIRMED_FOR_AIN_RESULT_ONLY`

This is a deterministic extraction from the released benchmark summary. The user
confirmed the AIN-RESULT formula, values, endpoint/comparator mapping and one-decimal
display on 2026-08-12. It does not authorize manuscript application or activate the
G04 claim.

## Source and formula

- Source: `output/natcs_benchmarks/benchmark_summary.csv`
- Source SHA-256: `c29aa14107f3815ef128ba6308bc3edfbc91da0404952d2d548042bc1c929cc1`
- Formula: `100 * (local_network_metric_median - cp_network_metric_median) / local_network_metric_median`
- Statistic: ratio of across-replication medians; 20 released replications at each primary scale.
- Comparator: `local_network` / Local rolling.
- Candidate: `cp_network` / CP-network.

| M5-A field | Scenario | Released field | Local median | CP median | Candidate reduction |
| --- | --- | --- | ---: | ---: | ---: |
| AIN-RESULT-OP-N15 | `scale_n15` | `coef_error_median` | 624.6125531760274 | 40.274806941788114 | 93.55203369881073% (93.6% display) |
| AIN-RESULT-OP-N30 | `scale_n30` | `coef_error_median` | 1371.693631145596 | 44.38880771061946 | 96.76394154622214% (96.8% display) |
| AIN-RESULT-RESP-N15 | `scale_n15` | `girf_error_median` | 0.4103961733321335 | 0.07164372813883849 | 82.54278845800611% (82.5% display) |
| AIN-RESULT-RESP-N30 | `scale_n30` | `girf_error_median` | 0.3971572031343755 | 0.05035310489419762 | 87.32161861932515% (87.3% display) |

The metric mapping is `coef_error_median` -> effective-operator error /
`effective_operator`, and `girf_error_median` -> finite-horizon unit-shock response
error / `total_response`.

## Author confirmation

The user response `同意，请继续` confirms the ratio-of-medians statistic, the four
values, endpoint/comparator wording, one-decimal display and evidence binding for
AIN-RESULT only. AIN-ALS, AIN-TOPOLOGY and AIN-SOURCE-OWNERSHIP remain unresolved,
so overall M5-A readiness remains `needs_author_input`.
