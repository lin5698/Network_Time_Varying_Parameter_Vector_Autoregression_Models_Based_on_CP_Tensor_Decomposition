// Controlled-benchmark contract tables (Supplementary Tables 1b and 1d).
//
// These rows are source-level declarations about the synthetic controlled
// benchmark only. They contain no RCEP, NYC or other application material and
// read nothing outside `output/natcs_benchmarks/benchmark_summary.csv`.
// They are shared by the active source-only Supplementary builder and by
// `build_natcs_evidence.mjs` so the reader document and the evidence CSVs
// cannot drift apart.

import fs from "fs";
import path from "path";
import { readCsv } from "./natcs_utils.mjs";

const DEFAULT_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

export function graphAwareCoverageText(root = DEFAULT_ROOT) {
  const summaryPath = path.join(root, "output", "natcs_benchmarks", "benchmark_summary.csv");
  const summaryRows = fs.existsSync(summaryPath) ? readCsv(summaryPath) : [];
  const graphAwareMethods = ["sparse_network", "graph_filter", "graph_neural_var", "diffusion_graph_var", "recurrent_graph_filter"];
  const graphAwareN50Counts = graphAwareMethods
    .map((method) => summaryRows.find((row) => row.scenario === "scale_n50" && row.method === method))
    .filter(Boolean)
    .map((row) => Number(row.replications ?? 0))
    .filter((value) => Number.isFinite(value) && value > 0);
  const graphAwareN50Coverage = graphAwareN50Counts.length
    ? Math.min(...graphAwareN50Counts) === Math.max(...graphAwareN50Counts)
      ? Math.min(...graphAwareN50Counts) === 1
        ? "N=50 projected graph-feature rows are bounded stress outputs with one replication per row disclosed in Supplementary Table 3."
        : `N=50 projected graph-feature rows are bounded stress outputs with ${Math.min(...graphAwareN50Counts)} replications disclosed in Supplementary Table 3.`
      : `N=50 projected graph-feature rows are bounded stress outputs with ${Math.min(...graphAwareN50Counts)}-${Math.max(...graphAwareN50Counts)} replications disclosed in Supplementary Table 3.`
    : "N=50 projected graph-feature rows are bounded stress outputs with disclosed replication coverage.";
  return `Matched 20-replication coverage at N=15, N=30 and the three topology-stress scenarios; ${graphAwareN50Coverage}`;
}

export function baselineTuningProjectionRows(root = DEFAULT_ROOT) {
  const graphAwareCoverage = graphAwareCoverageText(root);
  return [
    {
      Comparator: "CP-network",
      "Tuning or fixed setting": "Scenario rank fixed by validation design; scale rows use R=2, rank-under and rank-over stress rows use R=1 and R=3; local ridge floor 1e-6.",
      "Projection to readout protocol": "Native separated direct/network tensor; no projection needed before evaluating M(W_t), M(0) or M(W_pre).",
      "Matched replication coverage": "Matched to local rolling on the replicated N=15 and N=30 scale rows; N=50 is retained as a bounded stress check.",
      Boundary: "Main estimator for the submitted topology-switching propagation outputs.",
    },
    {
      Comparator: "Tucker-network",
      "Tuning or fixed setting": "Matched multilinear rank (R,R,R) using the same scenario rank as CP-network.",
      "Projection to readout protocol": "Native separated direct/network tensor after Tucker reconstruction.",
      "Matched replication coverage": "Included on the same stress and scale grids where preservation comparators are reported.",
      Boundary: "Tests preservation beyond CP; Tucker optimality belongs to a separate study.",
    },
    {
      Comparator: "Collapsed-operator CP",
      "Tuning or fixed setting": "Uses the same rank setting on the collapsed reduced-form tensor A+B W_t.",
      "Projection to readout protocol": "Evaluated as a reduced-form total map; separated network-component and frozen-topology responses sit outside the fitted object's target.",
      "Matched replication coverage": "Included on the same scale and topology-stress grids as the preservation ablation.",
      Boundary: "Direct ablation for loss of the topology argument after collapse.",
    },
    {
      Comparator: "Low-rank no-network",
      "Tuning or fixed setting": "Uses the same rank setting on a reduced-form no-network tensor.",
      "Projection to readout protocol": "Evaluated on total-map and finite-horizon unit-shock response endpoints only.",
      "Matched replication coverage": "Included on the same scale and topology-stress grids as the reduced-form smoothing comparator.",
      Boundary: "Prediction and total-map denoising comparator; structural network outputs are outside its reconstruction target.",
    },
    {
      Comparator: "Sparse network TVP-VAR",
      "Tuning or fixed setting": "Direct and network coefficient blocks are soft-thresholded entrywise at 0.025 after the common local ridge fit.",
      "Projection to readout protocol": "Projected to the same direct/network operator blocks before propagation evaluation.",
      "Matched replication coverage": graphAwareCoverage,
      Boundary: "Graph-feature operator-recovery comparator under the declared projection contract.",
    },
    {
      Comparator: "Graph-convolution VAR",
      "Tuning or fixed setting": "Rolling regression keeps diagonal direct terms and first-order graph-filter exposure terms.",
      "Projection to readout protocol": "Projected to direct/network blocks before evaluating the same propagation responses.",
      "Matched replication coverage": graphAwareCoverage,
      Boundary: "Fixed graph-filter structural baseline for operator recovery.",
    },
    {
      Comparator: "Graph neural VAR",
      "Tuning or fixed setting": "Lightweight graph-neural surrogate augments lagged direct and network exposures with tanh features under the same local ridge floor.",
      "Projection to readout protocol": "Feature coefficients are mapped back to direct and network blocks before evaluation.",
      "Matched replication coverage": graphAwareCoverage,
      Boundary: "Projected graph-feature comparator under the operator-recovery protocol.",
    },
    {
      Comparator: "Diffusion graph VAR",
      "Tuning or fixed setting": "Adds second-order graph-diffusion features under the same local ridge floor.",
      "Projection to readout protocol": "Two-hop terms are projected through the current reference topology into the network block.",
      "Matched replication coverage": graphAwareCoverage,
      Boundary: "Diffusion-feature structural comparator under the operator-recovery protocol.",
    },
    {
      Comparator: "Recurrent graph-filter VAR",
      "Tuning or fixed setting": "Adds a fixed rolling memory term with weights 0.45, 0.35 and 0.20 on lagged direct, lagged network and previous prediction components.",
      "Projection to readout protocol": "Recurrent and two-hop terms are projected back to direct/network blocks before propagation evaluation.",
      "Matched replication coverage": graphAwareCoverage,
      Boundary: "Recurrent graph-feature comparator under the operator-recovery protocol.",
    },
  ];
}

export function benchmarkFairnessAuditRows() {
  return [
    {
      "Reviewer check": "Target alignment",
      "What is compared": "Each method is evaluated only on response endpoints that its fitted object defines.",
      "Where to verify": "Fig. 2d; Fig. 3c; Table 1; Supplementary Tables 2a-2b",
      "Boundary protected": "Blank or Outside-target structural endpoints are not treated as numerical losses.",
    },
    {
      "Reviewer check": "Tuning parity",
      "What is compared": "Regression-style local fits share the 1e-6 ridge floor; CP, Tucker, collapsed and no-network rows use the scenario rank contract.",
      "Where to verify": "Supplementary Table 1b; benchmark scripts; validation-grid notes",
      "Boundary protected": "Tucker and graph-feature rows are declared comparators, not separately optimized method-development studies.",
    },
    {
      "Reviewer check": "Projection contract",
      "What is compared": "Sparse, graph-filter, graph-neural, diffusion and recurrent graph-feature fits are mapped to direct/network operator blocks before topology-response evaluation.",
      "Where to verify": "Supplementary Table 1b; Supplementary Note 4; benchmark_replications.csv",
      "Boundary protected": "These rows test operator recovery under projection and do not rank native graph-learning forecasting systems.",
    },
    {
      "Reviewer check": "Replication coverage",
      "What is compared": "Headline recovery uses replicated N=15 and N=30 rows; N=50 rows are bounded stress outputs with row-level coverage disclosed.",
      "Where to verify": "Table 1; Fig. 3a-b; Supplementary Table 3",
      "Boundary protected": "The 93.6-96.8% and 82.5-87.3% claims are anchored to replicated N=15/N=30 comparisons.",
    },
    {
      "Reviewer check": "Stability and failures",
      "What is compared": "Instability and failure rates travel with recovery errors; finite-horizon response errors use the common stability convention while unscaled instability is still reported.",
      "Where to verify": "Supplementary Table 2d; Supplementary Note 4",
      "Boundary protected": "A finite response error with high instability is a diagnostic warning, not a stability claim.",
    },
    {
      "Reviewer check": "Endpoint hierarchy",
      "What is compared": "Operator and finite-horizon unit-shock response recovery are the primary evidence; raw pair-level contribution is retained as a fragile fine-grained attribution diagnostic.",
      "Where to verify": "Table 1; Supplementary Table 2b; Results validation text",
      "Boundary protected": "Weak raw pair-level recovery does not carry the headline measurement claim.",
    },
  ];
}
