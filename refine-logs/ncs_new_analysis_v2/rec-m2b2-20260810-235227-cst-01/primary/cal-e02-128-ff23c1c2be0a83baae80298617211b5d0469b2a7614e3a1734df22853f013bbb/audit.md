# CAL-E02:128 Frozen-Data Audit

- Verdict: **BLOCKED**
- Data sufficiency: **PARTIAL**
- Register key: `CAL-E02:128`
- Input bundle SHA-256: `ff23c1c2be0a83baae80298617211b5d0469b2a7614e3a1734df22853f013bbb`

## Ground-Truth Boundary

The frozen route is `simulation_only`. Its DGP truth is separate from fitted predictions, but it is not independent empirical ground truth. No empirical fairness or superiority claim is licensed.

## Required Cells

| Cell | Status | Finding |
|---|---|---|
| `simulation_truth_provenance` | **PASS** | Frozen result is simulation-only and retains DGP truth-derived spectral radius and endpoint errors. |
| `independent_empirical_ground_truth` | **NOT_EVALUABLE** | No independent empirical dataset or empirical ground-truth provenance exists in the synthetic-only frozen route; simulation truth cannot substitute for it. |
| `training_validation_evaluation_chronology` | **WARN** | The frozen protocol and implementation define train/validation/evaluation chronology, but recovery records do not serialize the split boundaries or a per-record chronology receipt. |
| `selection_inputs` | **WARN** | Static code and frozen manifest restrict selection to observed-topology validation loss and prohibit held-out topology truth, but records lack candidate-loss vectors and selection-input provenance. |
| `held_out_topology_query` | **WARN** | Query classes and separate query paths are declared and evaluated, but result records do not carry query/topology source identity or a held-out query receipt. |
| `endpoint_parity` | **WARN** | Operator and finite-horizon response errors are present under the frozen native endpoint contract, but records omit an explicit endpoint signature/provenance field. |
| `truth_isolation` | **WARN** | FitData structurally excludes held-out query matrices and truth blocks, but the frozen result does not serialize a per-record truth-isolation receipt. |
| `native_gate` | **PASS** | The frozen fixture report and no-science gate receipt pass the native E3-1 classification gate; this does not establish empirical ground truth. |
| `register_binding` | **PASS** | The exact register item was found, but its observed SHA must match the authorized binding before the analysis can be treated as fully registered. |

## Coverage

- Recovery records: 46080 / 46080; status counts retain all declared statuses.
- Interval records: 160 / 160; bootstrap status counts retain all declared statuses.
- Paired completion keys: 32 / 32.

## Blocking Gaps

- Independent empirical ground truth is absent from the synthetic-only frozen route.
- Recovery records lack serialized chronology, truth, query, endpoint, and selection-input provenance fields.

## Scope Boundary

This artifact does not modify the manuscript, author decision register, or frozen quarantine. It does not execute the fresh protocol and does not use RCEP or NYC.
