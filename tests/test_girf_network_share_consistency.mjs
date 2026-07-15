import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const readJson = (relativePath) => JSON.parse(read(relativePath));

const absSum = (values) => values.reduce((sum, value) => sum + Math.abs(Number(value)), 0);
const share = (draw) => {
  const direct = absSum(draw.direct);
  const network = absSum(draw.network);
  return network / Math.max(direct + network, 1e-12);
};
const mean = (values) => values.reduce((sum, value) => sum + value, 0) / values.length;
const quantile = (values, q) => {
  const sorted = [...values].sort((a, b) => a - b);
  const position = (sorted.length - 1) * q;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
};

const evidenceSource = read("scripts/build_natcs_evidence.mjs");
const nycFigureSource = read("scripts/build_nyc_portability_figure.py");
const rcepFigureSource = read("scripts/build_rcep_operator_switch_figure.py");

assert.match(evidenceSource, /function absoluteExplicitChannelShare\(directValues, networkValues\)/);
assert.match(nycFigureSource, /def absolute_explicit_channel_share\(direct, network\):/);
assert.match(rcepFigureSource, /def absolute_explicit_channel_share\(direct, network\):/);
assert.doesNotMatch(
  evidenceSource,
  /\(total\s*-\s*direct\)\s*\/\s*Math\.max\(total/,
  "Evidence summaries must not infer a network channel by subtracting absolute masses.",
);

const bootstrap = readJson("output/natcs_empirical_cp/nyc_taxi/girf_cp_bootstrap.json");
const summary = readJson("output/natcs_evidence/summary_metrics.json").nyc_validation;
for (const [label, summaryKey] of [
  [summary.early_girf_label, "early_network_share"],
  [summary.late_girf_label, "late_network_share"],
]) {
  const values = bootstrap[label].map(share);
  assert.ok(Math.abs(summary[summaryKey].mean - mean(values)) < 1e-12, `${label} mean must use the explicit-channel share.`);
  assert.ok(Math.abs(summary[summaryKey].median - quantile(values, 0.5)) < 1e-12, `${label} median must use the explicit-channel share.`);
}

assert.equal(summary.network_share_estimand, "absolute_explicit_channel_share");
console.log("GIRF network-share consistency test passed.");
