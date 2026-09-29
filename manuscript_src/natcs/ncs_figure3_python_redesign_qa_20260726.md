# Figure 3 Python Redesign QA

Date: 2026-07-31

Status: source-only figure QA. It does not authorize a manuscript build,
figure-source package build, application evidence, scientific execution or an
audit-status change.

## Scientific contract

Core conclusion: target-matched endpoint-preserving reconstruction improves
the declared operator and response recovery in the released controlled design.
The separate held-out qualification remains fully reported in Methods and
Supplementary Note 4, but it is no longer promoted as a main-figure panel.

Source bindings:

- Point estimates and interquartile ranges:
  `output/natcs_evidence/table1_simulation_benchmark.csv`.
- Unrounded medians and replication checks:
  `output/natcs_benchmarks/benchmark_summary.csv`.
- Machine-readable DGP and metric contract:
  `manuscript_src/natcs/controlled_benchmark_contract.json`.

The generator refuses unless CP and unrestricted-local rows exist uniquely at
`N=15` and `N=30`, each row has 20 replications, and every plotted interval is
finite and ordered. The main visual does not read the held-out gate record.

## Visual audit

The revised source uses three panels. Panels a-b directly label the supported
reductions (`93.6%`, `96.8%`, `82.5%`, `87.3%`). Panel c expands across the
lower width and makes the common endpoint and matched 20-replication contract
explicit. This is a source-level design review only: the controlling release
gate has not permitted regeneration, so no claim is made about the pixels,
dimensions, hashes or final page rendering of the revised asset.

## Export verification

Static verification completed:

```text
Figure 3 Python-backend and released-evidence contract test passed.
Main Fig. 3 launch-narrative qualification-scope test passed.
NCS controlled benchmark machine-readable contract passed.
```

Asset-level export, font, overlap and hash checks remain pending a permitted
Figure 3 regeneration.

## Claim boundary

Figure 3 supports the released controlled `N=15/N=30` comparison against
unrestricted local rolling and explains why that comparison is endpoint
matched. It does not support universal estimator superiority, native held-out
recovery, cross-family transfer, calibrated uncertainty or application impact.
`N=50`, stress rows and exact held-out qualification counts remain
supplementary evidence.
