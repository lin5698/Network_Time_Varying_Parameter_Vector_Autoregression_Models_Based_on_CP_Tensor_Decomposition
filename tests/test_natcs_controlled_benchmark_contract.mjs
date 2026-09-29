import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readCsv } from "../scripts/natcs_utils.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const benchmarkSource = fs.readFileSync(path.join(root, "scripts/natcs_benchmarks.mjs"), "utf8");
const diagnosticSource = fs.readFileSync(path.join(root, "scripts/natcs_weak_separation.py"), "utf8");
const contract = JSON.parse(fs.readFileSync(path.join(root, "manuscript_src/natcs/controlled_benchmark_contract.json"), "utf8"));
const summary = readCsv(path.join(root, contract.released_artifacts.summary));

assert.equal(contract.schema_version, "natcs-controlled-benchmark-contract-v2");
assert.equal(contract.operator_generation.target_effective_operator_spectral_norm_max, 0.78);
assert.equal(contract.operator_generation.innovation_marginal_scale, 0.03);
assert.equal(contract.operator_generation.topology.diagonal, "zero");
assert.equal(contract.operator_generation.topology.entries, "non-negative");

assert.equal(contract.estimator_configuration.local_ridge_normal_equation_regularizer, 1e-6);
assert.equal(contract.estimator_configuration.cp_als_gram_regularizer, 1e-6);
assert.equal(contract.estimator_configuration.cp_als_iterations, 60);
assert.equal(contract.response_evaluation.spectral_norm_stabilization_trigger, 0.95);
assert.equal(contract.response_evaluation.unscaled_instability_threshold, 0.98);
assert.equal(contract.weak_separation_diagnostic.residualized_gram_rank_tolerance, 1e-12);
assert.equal(contract.weak_separation_diagnostic.minimum_eigenvalue_flag_threshold, 1e-8);

for (const [metric, expectedPrefix] of Object.entries({
  coef_error: "coef_error_",
  share_error: "share_error_",
  girf_error: "girf_error_",
  network_component_error: "network_component_error_",
  frozen_counterfactual_error: "frozen_counterfactual_error_",
  prediction_error: "prediction_error_",
})) {
  assert.equal(contract.metric_dictionary[metric].released_field_prefix, expectedPrefix);
  assert.ok(contract.metric_dictionary[metric].reader_facing_name.length > 0);
  assert.ok(contract.metric_dictionary[metric].definition.length > 0);
}
assert.equal(contract.metric_dictionary.coef_error.reader_facing_name, "effective-operator error");
assert.equal(contract.metric_dictionary.girf_error.reader_facing_name, "finite-horizon unit-shock response error");

for (const expected of [
  /if \(radius > 0\.78\)/,
  /function safeRowNormalize\(W\)[\s\S]*?out\[i\]\[i\] = 0/,
  /Math\.max\(out\[i\]\[j\], 0\) \/ sum/,
  /\(1 - vol\) \* x \+ vol \* draw\[i\]\[j\]/,
  /i === j \? 1e-6 : 0/,
  /function cpAls\(tensor, rank, next, iterations = 60\)/,
  /scale\(eye\(rank\), 1e-6\)/,
  /radius >= 0\.95 \? scale\(M, 0\.95/,
  /spectralRadiusApprox\(MHat\) >= 0\.98/,
]) {
  assert.match(benchmarkSource, expected, `Benchmark implementation no longer matches ${expected}.`);
}
assert.match(diagnosticSource, /eig > EPS/);
assert.match(diagnosticSource, /min_eig <= 1e-8 or residualized_rank < Z_perp\.shape\[1\]/);

for (const scenario of contract.primary_scenarios) {
  const sourcePattern = new RegExp(`name: "${scenario.scenario}"[^\\n]+tLen: ${scenario.T}[^\\n]+n: ${scenario.N}[^\\n]+window: ${scenario.rolling_window}[^\\n]+topologyVol: ${scenario.topology_mixing_weight}[^\\n]+sigma: ${contract.operator_generation.innovation_marginal_scale}[^\\n]+horizon: ${scenario.response_horizon}`);
  assert.match(benchmarkSource, sourcePattern, `Source contract drifted for ${scenario.scenario}.`);
  const rows = summary.filter((row) => row.scenario === scenario.scenario && ["cp_network", "local_network"].includes(row.method));
  assert.equal(rows.length, 2, `Released summary must contain the primary CP/local pair for ${scenario.scenario}.`);
  assert.ok(rows.every((row) => Number(row.replications) === scenario.released_replications), `Released replication coverage drifted for ${scenario.scenario}.`);
}

const stress = contract.bounded_scale_stress;
const stressRows = summary.filter((row) => row.scenario === stress.scenario);
assert.deepEqual(
  Object.fromEntries(stressRows.map((row) => [row.method, Number(row.replications)]).sort(([a], [b]) => a.localeCompare(b))),
  Object.fromEntries(Object.entries(stress.replication_coverage_by_method).sort(([a], [b]) => a.localeCompare(b))),
  "N=50 method-specific replication coverage drifted from the released summary.",
);

const fullEndpointMethods = [
  "local_network",
  "cp_network",
  "tucker_network",
  "sparse_network",
  "graph_filter",
  "graph_neural_var",
  "diffusion_graph_var",
  "recurrent_graph_filter",
];
for (const method of fullEndpointMethods) {
  const endpoints = contract.endpoint_availability.method_to_endpoint_ids[method];
  assert.ok(endpoints.includes("direct_only_response"));
  assert.ok(endpoints.includes("network_component_response"));
  assert.ok(endpoints.includes("frozen_topology_response"));
}
for (const method of ["collapsed_operator_cp", "cp_nonnetwork"]) {
  assert.deepEqual(
    contract.endpoint_availability.method_to_endpoint_ids[method],
    ["effective_operator", "total_response", "one_step_prediction"],
  );
  const row = summary.find((item) => item.scenario === "scale_n15" && item.method === method);
  assert.ok(row, `Missing released ${method} row.`);
  for (const field of ["share_error_median", "network_component_error_median", "frozen_counterfactual_error_median"]) {
    assert.equal(row[field], contract.endpoint_availability.unavailable_sentinel.released_csv_value);
  }
}
assert.equal(contract.endpoint_availability.unavailable_sentinel.reader_facing_label, "OUTSIDE TARGET");

console.log("NCS controlled benchmark semantic and execution contract passed.");
