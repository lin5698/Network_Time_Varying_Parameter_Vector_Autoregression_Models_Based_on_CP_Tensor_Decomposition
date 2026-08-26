// Active source-only Supplementary Information builder.
//
// Contract: this module composes the reader-facing Supplementary document from
// theory notes, the controlled synthetic benchmark and the operating-regime
// note ONLY. It must never read RCEP, NYC or E3 material, selection summaries,
// stability diagnostics, empirical application figures or the retired
// validation figure, and it must never load the inactive audit-boundary
// protocol records (supp_note5_empirical, supp_note6_robustness,
// supp_note7_repro). Those records stay in the manuscript source tree as
// audit-boundary documentation but are not part of this document while
// `PAPER_CLAIM_AUDIT=BLOCKED` and `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL`
// remain controlling.
//
// Allowed inputs:
//   - manuscript_src/natcs/supplementary.md            (overview declaration)
//   - manuscript_src/natcs/supp_note1_notation.md      (theory)
//   - manuscript_src/natcs/supp_note2_estimator.md     (methodological contract)
//   - manuscript_src/natcs/supp_note3_propagation.md   (theory)
//   - manuscript_src/natcs/supp_note4_benchmarks.md    (controlled benchmark)
//   - manuscript_src/natcs/supp_note8_scope.md         (operating regime)
//   - output/natcs_benchmarks/benchmark_summary.csv    (controlled benchmark)
//   - scripts/natcs_benchmark_contract_tables.mjs      (static contract rows)
//
// The static guard test tests/test_natcs_active_supplementary_source_only.mjs
// enforces this boundary; extend that test if the allowed-input set changes.

import path from "path";
import {
  assertReaderFacingTextClean,
  markdownTable,
  readCsv,
  readText,
  readerFacingSubmissionText,
  referencesBlock,
  renderTemplate,
  yamlHeader,
} from "./natcs_utils.mjs";
import { baselineTuningProjectionRows, benchmarkFairnessAuditRows } from "./natcs_benchmark_contract_tables.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SRC = path.join(ROOT, "manuscript_src", "natcs");
const BENCHMARK_SUMMARY = path.join(ROOT, "output", "natcs_benchmarks", "benchmark_summary.csv");

const ALLOWED_SECTIONS = new Set([
  "supplementary",
  "supp_note1_notation",
  "supp_note2_estimator",
  "supp_note3_propagation",
  "supp_note4_benchmarks",
  "supp_note8_scope",
]);

function loadAllowedSection(name) {
  if (!ALLOWED_SECTIONS.has(name)) {
    throw new Error(`Source-only Supplementary builder refused section outside its contract: ${name}`);
  }
  // The empty template context is intentional: if a placeholder is ever added
  // to an allowed note, the build fails loudly instead of silently binding an
  // application value.
  return readerFacingSubmissionText(renderTemplate(readText(path.join(SRC, `${name}.md`)).trim(), {}));
}

function objectsToMarkdown(rows, headers) {
  return markdownTable(headers, rows.map((row) => headers.map((key) => row[key] ?? "")));
}

function compactIqr(median, q25, q75) {
  return Number.isFinite(median)
    ? `${Number(median).toFixed(3)} (${Number(q25).toFixed(3)}-${Number(q75).toFixed(3)})`
    : "Outside";
}

function maybeNumber(value) {
  if (value === "" || value == null) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function fixedOrBlank(value, digits = 3) {
  const parsed = maybeNumber(value);
  return parsed == null ? "" : parsed.toFixed(digits);
}

function replicationsFor(rows, scenario, method) {
  const row = rows.find((entry) => entry.scenario === scenario && entry.method === method);
  const value = Number(row?.replications ?? NaN);
  return Number.isFinite(value) && value > 0 ? value : null;
}

function graphAwareN50CoverageText(rows) {
  const graphAwareMethods = ["sparse_network", "graph_filter", "graph_neural_var", "diffusion_graph_var", "recurrent_graph_filter"];
  const counts = graphAwareMethods
    .map((method) => replicationsFor(rows, "scale_n50", method))
    .filter((value) => value != null);
  if (!counts.length) return "disclosed row-level coverage";
  const min = Math.min(...counts);
  const max = Math.max(...counts);
  if (min === max) {
    return min === 1 ? "one replication per projected N=50 graph-feature row" : `${min} replications`;
  }
  return `${min}-${max} replications`;
}

function buildBaselineTuningProjectionTable(assetFormat) {
  const rows = baselineTuningProjectionRows(ROOT);
  if (assetFormat === "vector") {
    return objectsToMarkdown(rows, [
      "Comparator",
      "Tuning or fixed setting",
      "Projection to readout protocol",
      "Matched replication coverage",
      "Boundary",
    ]);
  }
  const docxRows = rows.map((row) => ({
    Comparator: row.Comparator,
    "Response-evaluation rule": `${row["Projection to readout protocol"]} ${row["Tuning or fixed setting"]}`,
    Coverage: row["Matched replication coverage"],
    Boundary: row.Boundary,
  }));
  return objectsToMarkdown(docxRows, ["Comparator", "Response-evaluation rule", "Coverage", "Boundary"]);
}

function buildFairnessAuditTable() {
  return objectsToMarkdown(benchmarkFairnessAuditRows(), [
    "Reviewer check",
    "What is compared",
    "Where to verify",
    "Boundary protected",
  ]);
}

function buildPositioningTable(assetFormat) {
  if (assetFormat !== "vector") {
    return objectsToMarkdown(
      [
        {
          "Method family": "Standard TVP-VAR",
          "Switchable operator status": "Fits a time-varying total map; topology-substitution readouts require an added preservation target.",
          "Boundary for this paper": "Useful coefficient-drift baseline, not a topology-substitution measurement object.",
        },
        {
          "Method family": "Spatial, network autoregressive or GVAR-style models",
          "Switchable operator status": "May include network terms; topology-substitution responses are specification-specific.",
          "Boundary for this paper": "Closest conceptual relatives; this paper targets a finite-horizon operator with observed, direct-only and frozen-topology evaluations.",
        },
        {
          "Method family": "Matrix or tensor decomposition of spatiotemporal coefficients",
          "Switchable operator status": "Supports smoothing; a collapsed target needs an identified inverse to recover switchability.",
          "Boundary for this paper": "Low-rank structure is used only when it preserves the topology argument.",
        },
        {
          "Method family": "Graph convolutional, diffusion or neural graph predictors",
          "Switchable operator status": "Often strong for prediction; separable direct/network response objects require extra projection.",
          "Boundary for this paper": "Projected graph-feature rows are stress tests for operator recovery, not native forecasting benchmarks.",
        },
        {
          "Method family": "Reduced-form low-rank no-network predictors",
          "Switchable operator status": "Recovers a total map; network-component and frozen-topology outputs require separated direct/network blocks.",
          "Boundary for this paper": "Useful denoising comparator for reduced-form columns.",
        },
        {
          "Method family": "This framework",
          "Switchable operator status": "Preserves M_{k,t}(W)=A_{k,t}+B_{k,t}W, so observed, direct-only and frozen-topology responses are evaluated from one fitted path.",
          "Boundary for this paper": "Interpretation still requires predetermined topology, weak direct/network separation and finite-horizon stability.",
        },
      ],
      ["Method family", "Switchable operator status", "Boundary for this paper"]
    );
  }
  return objectsToMarkdown(
    [
      {
        "Method family": "Standard TVP-VAR",
        "Total map": "Yes",
        "Explicit network channel": "No by default",
        "Switch W argument": "No",
        "Network/topology objects": "Outside the default target",
        "Boundary for this paper": "Useful coefficient-drift baseline, not a topology-substitution measurement object.",
      },
      {
        "Method family": "Spatial, network autoregressive or GVAR-style models",
        "Total map": "Partly, depending on specification",
        "Explicit network channel": "Often yes",
        "Switch W argument": "Specification-dependent validation target",
        "Network/topology objects": "Model-specific evidence links across reconstruction and robustness steps",
        "Boundary for this paper": "Closest conceptual relatives; the contribution is the topology-preserving finite-horizon operator under evolving topology.",
      },
      {
        "Method family": "Matrix or tensor decomposition of spatiotemporal coefficients",
        "Total map": "Yes",
        "Explicit network channel": "No, unless the tensor is block-structured around it",
        "Switch W argument": "Outside target unless an identified block inverse is supplied",
        "Network/topology objects": "Outside the unrestricted reconstruction target",
        "Boundary for this paper": "Low-rank structure is used only when it preserves the direct/network operator split.",
      },
      {
        "Method family": "Graph convolutional, diffusion or neural graph predictors",
        "Total map": "Often yes for prediction",
        "Explicit network channel": "Feature-dependent, not generally a separable operator block",
        "Switch W argument": "Not without an additional topology-evaluation architecture",
        "Network/topology objects": "Usually post hoc for the fitted predictor",
        "Boundary for this paper": "Projected graph-feature stress tests examine object recovery, not exhaustive temporal-GNN forecasting performance.",
      },
      {
        "Method family": "Reduced-form low-rank no-network predictors",
        "Total map": "Yes",
        "Explicit network channel": "No",
        "Switch W argument": "No",
        "Network/topology objects": "Outside target",
        "Boundary for this paper": "Can win reduced-form denoising columns while still failing the network-propagation estimand.",
      },
      {
        "Method family": "This framework",
        "Total map": "Yes, through M_{k,t}(W_t)",
        "Explicit network channel": "Yes, through separated B_{k,t}W",
        "Switch W argument": "Yes",
        "Network/topology objects": "Defined by the same reconstructed operator path",
        "Boundary for this paper": "Interpretation still requires predetermined W_t, weak direct/network separation and finite-horizon stability.",
      },
    ],
    ["Method family", "Total map", "Explicit network channel", "Switch W argument", "Network/topology objects", "Boundary for this paper"]
  );
}

export function buildSourceOnlySupplementaryMarkdown(meta, assetFormat = "vector") {
  const overview = loadAllowedSection("supplementary");
  const note1 = loadAllowedSection("supp_note1_notation");
  const note2 = loadAllowedSection("supp_note2_estimator");
  const note3 = loadAllowedSection("supp_note3_propagation");
  const note4 = loadAllowedSection("supp_note4_benchmarks");
  const note5Scope = loadAllowedSection("supp_note8_scope");
  const refs = referencesBlock([overview, note1, note2, note3, note4, note5Scope]);

  const benchmarkRawRows = readCsv(BENCHMARK_SUMMARY);
  const scenarioCodes = new Map();
  const scenarioDisplays = new Map();
  const methodCodes = new Map();
  const codeFor = (map, label) => {
    if (!map.has(label)) map.set(label, String(map.size + 1));
    return map.get(label);
  };
  const benchmarkSummaryRows = benchmarkRawRows.map((row) => {
    const scenario = row.scenario_label;
    const method = row.method_label;
    const scenarioCode = codeFor(scenarioCodes, scenario);
    const methodCode = codeFor(methodCodes, method);
    if (!scenarioDisplays.has(scenario)) {
      scenarioDisplays.set(
        scenario,
        /\bT=\d+/.test(scenario) ? scenario : `${scenario} (T=${row.T}, N=${row.N})`
      );
    }
    return {
      S: scenarioCode,
      M: methodCode,
      "Eff. op.": compactIqr(row.coef_error_median, row.coef_error_q25, row.coef_error_q75),
      "Raw pair": compactIqr(row.share_error_median, row.share_error_q25, row.share_error_q75),
      "Net comp.": compactIqr(row.network_component_error_median, row.network_component_error_q25, row.network_component_error_q75),
      Frozen: compactIqr(row.frozen_counterfactual_error_median, row.frozen_counterfactual_error_q25, row.frozen_counterfactual_error_q75),
      Response: compactIqr(row.girf_error_median, row.girf_error_q25, row.girf_error_q75),
      Pred: compactIqr(row.prediction_error_median, row.prediction_error_q25, row.prediction_error_q75),
      "Run s": fixedOrBlank(row.runtime_mean_seconds, 3),
      "Mem MB": Number.isFinite(row.memory_mb_median) ? `${Number(row.memory_mb_median).toFixed(1)} (${Number(row.memory_mb_q25).toFixed(1)}-${Number(row.memory_mb_q75).toFixed(1)})` : "",
      "Unst. %": maybeNumber(row.instability_rate_mean) == null ? "" : (100 * maybeNumber(row.instability_rate_mean)).toFixed(1),
      "Fail %": maybeNumber(row.failure_rate) == null ? "" : (100 * maybeNumber(row.failure_rate)).toFixed(1),
    };
  });
  const scenarioLegend = Array.from(scenarioCodes.entries()).map(([label, code]) => ({ code, label }));
  const methodLegend = Array.from(methodCodes.entries()).map(([label, code]) => ({ code, label }));
  const benchmarkLegendRows = Array.from({ length: Math.max(scenarioLegend.length, methodLegend.length) }, (_, index) => ({
    S: scenarioLegend[index]?.code ?? "",
    Scenario: scenarioLegend[index] ? scenarioDisplays.get(scenarioLegend[index].label) : "",
    M: methodLegend[index]?.code ?? "",
    Method: methodLegend[index]?.label ?? "",
  }));
  const benchmarkLegendTable = objectsToMarkdown(benchmarkLegendRows, ["S", "Scenario", "M", "Method"]);
  const benchmarkRecoveryTable = objectsToMarkdown(benchmarkSummaryRows, ["S", "M", "Eff. op.", "Response", "Pred"]);
  const benchmarkTopologyTable = objectsToMarkdown(benchmarkSummaryRows, ["S", "M", "Raw pair", "Net comp.", "Frozen"]);
  const benchmarkCostTable = objectsToMarkdown(benchmarkSummaryRows, ["S", "M", "Run s", "Mem MB"]);
  const benchmarkStatusTable = objectsToMarkdown(benchmarkSummaryRows, ["S", "M", "Unst. %", "Fail %"]);
  const benchmarkReplicationTable = objectsToMarkdown(
    benchmarkRawRows.map((row) => ({
      Scenario: row.scenario_label,
      Method: row.method_label,
      Reps: row.replications,
      "Fail (%)": maybeNumber(row.failure_rate) == null ? "" : (100 * maybeNumber(row.failure_rate)).toFixed(1),
    })),
    ["Scenario", "Method", "Reps", "Fail (%)"]
  );

  const scaleRepsN15 = replicationsFor(benchmarkRawRows, "scale_n15", "cp_network") ?? "disclosed";
  const scaleRepsN30 = replicationsFor(benchmarkRawRows, "scale_n30", "cp_network") ?? "disclosed";
  const scaleRepsN50 = replicationsFor(benchmarkRawRows, "scale_n50", "cp_network") ?? "disclosed";
  const graphAwareCoverage = graphAwareN50CoverageText(benchmarkRawRows);

  const document = readerFacingSubmissionText([
    yamlHeader(
      {
        ...meta,
        title: `Supplementary Information for ${meta.title}`,
      },
      { srcDir: SRC }
    ),
    overview,
    "",
    "# Notation and model objects",
    "",
    note1,
    "",
    "# Estimator and implementation pipeline",
    "",
    note2,
    "",
    "# Propagation objects and topology-argument decomposition",
    "",
    note3,
    "",
    "# Synthetic benchmark design and comparator set",
    "",
    note4,
    "",
    buildBaselineTuningProjectionTable(assetFormat),
    "",
    "*Supplementary Table 1b | Benchmark tuning-and-projection contract for synthetic comparators. Graph-feature rows are projected to the reported direct/network operator protocol; matched N=15, N=30 and topology-stress projected rows use 20 replications, while N=50 graph-feature rows are bounded stress outputs with disclosed replication coverage.*",
    "",
    buildFairnessAuditTable(),
    "",
    "*Supplementary Table 1d | Reviewer-facing benchmark fairness audit. The table condenses the benchmark target, tuning, projection, coverage, stability and endpoint-hierarchy checks that govern how Supplementary Tables 1b, 2 and 3 should be read.*",
    "",
    "Main Figure 3 summarizes the endpoint-defined recovery benchmark. Supplementary Tables 2a-2d give the full benchmark grid with compact scenario and method codes to keep the Word tables readable. The scenario legend reports T and N. Metric cells report median (q25-q75) unless noted; Outside marks a readout outside the fitted target. The source CSV is included with the supplementary evidence files and mirrored in the build tree under `output/natcs_benchmarks/benchmark_summary.csv`. Its `girf_error_*` columns are legacy storage names for the identity-shock finite-horizon response error used in this controlled benchmark; they do not denote covariance-normalized generalized impulse responses.",
    "",
    benchmarkLegendTable,
    "",
    "*Supplementary Table 2a | Synthetic benchmark recovery endpoints across all benchmark settings and comparator methods. Eff. op., Response and Pred denote effective-operator, finite-horizon unit-shock response and one-step prediction errors.*",
    "",
    benchmarkRecoveryTable,
    "",
    "*Supplementary Table 2b | Topology-specific recovery endpoints across the same scenario grid. Raw pair, Net comp. and Frozen denote raw pair-level, network-component and frozen-topology errors.*",
    "",
    benchmarkTopologyTable,
    "",
    "*Supplementary Table 2c | Computational cost across the same scenario grid. Run s is mean runtime in seconds; Mem MB is median (q25-q75) peak memory in megabytes.*",
    "",
    benchmarkCostTable,
    "",
    "*Supplementary Table 2d | Stability and run-status diagnostics across the same scenario grid. Unst. % is the mean instability rate and Fail % is the failed-replication rate.*",
    "",
    benchmarkStatusTable,
    "",
    benchmarkReplicationTable,
    "",
    `*Supplementary Table 3 | Synthetic benchmark replication coverage and failure rates. Matched CP-network/local scale rows are reported at N=15 (${scaleRepsN15} replications) and N=30 (${scaleRepsN30} replications). N=50 is retained as a bounded stress setting: CP-network/local/Tucker/low-rank rows have ${scaleRepsN50} replications where reported. Projected graph-feature N=50 rows are bounded stress outputs with ${graphAwareCoverage}. Projected graph-feature rows disclose their own coverage, with matched 20-replication rows at N=15, N=30 and in the topology-stress scenarios, and are evaluated under the declared projection contract.*`,
    "",
    "# Operating regime and interpretation",
    "",
    note5Scope,
    "",
    buildPositioningTable(assetFormat),
    "",
    "*Supplementary Table 4 | Estimand comparison for the proposed operator-level measurement framework relative to common dynamic-network, low-rank and graph-learning model families. `Switch W argument` asks whether observed, direct-only and frozen-topology recursions are defined from one fitted path; `network/topology objects` refers to network-component and frozen-topology summaries.*",
    "",
    ...refs,
  ].join("\n"));
  assertReaderFacingTextClean("supplementary_source_only", document);
  return document;
}
