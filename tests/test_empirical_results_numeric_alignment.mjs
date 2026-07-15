import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const rcep = read("manuscript_src/natcs/results_rcep.md");
const generality = read("manuscript_src/natcs/results_generality.md");
const generatedManuscript = read("output/submission_package/natcs_current/01_main_manuscript/main_manuscript.tex");
const finalGates = read("scripts/check_natcs_final_gates.mjs");
const summary = JSON.parse(read("output/natcs_evidence/summary_metrics.json"));
const readerSummary = JSON.parse(read("output/natcs_evidence/reader_facing_summary_metrics.json"));

assert.match(
  rcep,
  /point-series mean difference is \{\{rcep_pre_point_difference\}\} before 2022 Q1 and \{\{rcep_post_point_difference\}\} afterward/i,
  "RCEP period-level point differences must be rendered from the current H=8 evidence summary.",
);
assert.match(
  rcep,
  /Bootstrap median differences average \{\{rcep_pre_bootstrap_difference\}\} and \{\{rcep_post_bootstrap_difference\}\}/i,
  "RCEP bootstrap median differences must be rendered from the current evidence summary.",
);
assert.match(
  rcep,
  /mean 0\.0023 and median 0\.0011/i,
  "The topology-perturbation summary must match the current evidence output.",
);
assert.doesNotMatch(
  rcep,
  /mean 0\.006 and median 0\.004/i,
  "The superseded topology-perturbation values must not return.",
);
assert.match(
  generality,
  /Mean aggregate propagation is \{\{nyc_mean_gnet\}\} and mean frozen-topology propagation is \{\{nyc_mean_frozen_gnet\}\}, giving a mean observed-minus-frozen difference of \{\{nyc_mean_topology_difference_4\}\}/i,
  "NYC aggregate levels must be rendered from the current second-domain summary.",
);
assert.match(
  generality,
  /Using explicit absolute channel mass, bootstrap-draw mean network shares are \{\{nyc_early_network_share_mean\}\} at \{\{nyc_early_girf_label\}\} and \{\{nyc_late_network_share_mean\}\} at \{\{nyc_late_girf_label\}\}; bootstrap medians under the same estimand are \{\{nyc_early_network_share_median\}\} and \{\{nyc_late_network_share_median\}\}\. Figure 4c separately labels the corresponding point-path shares, computed with the same formula/i,
  "NYC GIRF shares must be rendered from the current second-domain summary.",
);
assert.equal(summary.rcep_aggregate_readout?.horizon, 8, "RCEP aggregate readout must disclose its H=8 source boundary.");
assert.equal(summary.rcep_aggregate_readout?.pre_2022?.point_mean_observed_minus_frozen, -0.00009123601495351192, "RCEP pre-2022 point difference must use the H=8 baseline path.");
assert.equal(summary.rcep_aggregate_readout?.post_2022?.point_mean_observed_minus_frozen, -0.002566783975691845, "RCEP post-2022 point difference must use the H=8 baseline path.");
assert.equal(summary.synthetic_benchmark?.local_rolling_topology_stress_replications?.min, 3, "Local-rolling stress replication coverage must be machine-readable.");
assert.equal(summary.nyc_validation?.ridge_lambda, 0.01, "NYC selection metadata must include the selected ridge value.");
assert.equal(summary.nyc_validation?.rank_validation?.available_origins, 69, "NYC rank-validation coverage must be machine-readable.");
assert.equal(readerSummary.rcep_application?.aggregate_readout?.pre_2022?.date_count, 24, "Reader-facing evidence must expose RCEP period coverage.");
assert.equal(readerSummary.nyc_taxi_validation?.ridge_lambda, 0.01, "Reader-facing evidence must expose NYC selection metadata.");
assert.equal(readerSummary.nyc_taxi_validation?.network_share_estimand, "absolute_explicit_channel_share", "Reader-facing evidence must name the NYC GIRF share estimand.");
assert.match(
  generatedManuscript.replace(/\s+/g, " "),
  /point-series mean difference is -0\.00009 before 2022 Q1 and -0\.00257 afterward/i,
  "The generated manuscript must render the H=8 RCEP period summaries.",
);
assert.match(
  generatedManuscript.replace(/\s+/g, " "),
  /Mean aggregate propagation is 0\.274 and mean frozen-topology propagation is 0\.274, giving a mean observed-minus-frozen difference of -0\.0004/i,
  "The generated manuscript must render the evidence-backed NYC aggregate summary.",
);
assert.match(
  generatedManuscript.replace(/\s+/g, " "),
  /93\.6-96\.8\\%[\s\S]*?impulse-response error by 82\.5-87\.3\\%/i,
  "The generated manuscript must round replicated GIRF gains from exact benchmark values.",
);
assert.doesNotMatch(
  generatedManuscript.replace(/\s+/g, " "),
  /82\.4-87\.4\\%/,
  "The generated manuscript must not re-round GIRF gains from display-table values.",
);
assert.match(
  finalGates,
  /function checkEmpiricalResultsNumericAlignment\(\)/,
  "The final gate must prevent stale empirical result values from returning.",
);
assert.match(
  finalGates,
  /function checkEvidenceAuditTraceability\(\)/,
  "The final gate must require machine-readable evidence for empirical manuscript fields.",
);

console.log("Empirical Results numeric-alignment test passed.");
