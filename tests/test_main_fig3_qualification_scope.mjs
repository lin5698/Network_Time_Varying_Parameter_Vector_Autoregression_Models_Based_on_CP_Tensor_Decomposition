import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const manuscriptBuilder = read("scripts/build_natcs_manuscript.mjs");
const finalGates = read("scripts/check_natcs_final_gates.mjs");
const results = read("manuscript_src/natcs/results_validation.md");
const abstract = read("manuscript_src/natcs/abstract.md");
const discussion = read("manuscript_src/natcs/discussion.md");
const coverLetter = read("manuscript_src/natcs/cover_letter.md");
const methods = read("manuscript_src/natcs/methods_uncertainty.md");
const supplement = read("manuscript_src/natcs/supp_note4_benchmarks.md");
const gate = JSON.parse(read("manuscript_src/natcs/r006c_endpoint_gate.json"));

const headlineText = [manuscriptBuilder, results, abstract, discussion, coverLetter].join("\n");
assert.doesNotMatch(headlineText, /(?:CP[^.\n]{0,80})?(?:0|none) of 16|Tucker[^.\n]{0,80}6 of 16|0 of 8 native/i, "Exact held-out failure counts must stay out of the headline narrative.");
assert.match(results, /separate simulation-only endpoint-aware qualification[\s\S]*?is not used to extend these gains/i, "Results must retain a concise claim-inheritance boundary.");
assert.doesNotMatch(methods, /CP passed 0 of 16 cells|Tucker passed 6 of 16|0 of 8 native cells/i, "Exact qualification counts must remain supplementary rather than becoming a main-Methods result.");
assert.match(methods, /complete cell counts and promotion decision are reported in Supplementary Note 4[\s\S]*?recovery claim remains confined to the original matched controlled design/i, "Methods must preserve the qualification pointer and claim boundary.");
assert.match(supplement, /\| CP anchor split \| 3 \| 0\/16 \| 0\/8 \| 0\/8 \| Threshold not met [\s\S]*?\| Tucker anchor split \| \(3,3,3\) \| 6\/16 \| 6\/8 \| 0\/8 \| Threshold not met /i, "Supplementary Note 4 must retain the complete qualification table.");
assert.match(
  finalGates,
  /function checkMainFigure3QualificationScope\(\)/,
  "The final gate must verify that qualification counts remain supplementary and frozen.",
);
assert.equal(gate.candidates.cp.passed_cells, 0);
assert.equal(gate.candidates.tucker.passed_cells, 6);
assert.equal(gate.candidates.tucker.passed_native_cells, 0);
assert.equal(gate.schema_version, "natcs-r006c-endpoint-gate-v2");

const rawSourceBytes = fs.readFileSync(path.join(root, gate.source.path));
assert.equal(createHash("sha256").update(rawSourceBytes).digest("hex"), gate.source.sha256);
const rawSource = JSON.parse(rawSourceBytes.toString("utf8"));
assert.equal(rawSource.generated_at, gate.source.generated_at);
assert.equal(rawSource.config.n, gate.scope.n);
assert.equal(rawSource.config.t_len, gate.scope.t);
assert.equal(rawSource.config.fitted_rank, gate.scope.fitted_rank);
assert.equal(rawSource.config.head_rank, gate.scope.head_rank);
assert.equal(rawSource.config.horizon, gate.scope.response_horizon);
assert.deepEqual(rawSource.grid.layers, gate.scope.layers);
assert.deepEqual(rawSource.grid.seeds, gate.scope.seed_ids);

for (const key of ["cp", "tucker"]) {
  const declared = gate.candidates[key];
  const sourceCandidate = rawSource.checks.promotion.candidates[declared.source_candidate_id];
  assert.ok(sourceCandidate, `Missing frozen source candidate ${declared.source_candidate_id}.`);
  assert.equal(sourceCandidate.required_cells.length, gate.scope.required_cells_per_candidate);
  assert.equal(sourceCandidate.passed_cells, declared.passed_cells);
  assert.equal(sourceCandidate.required_cells.filter((cell) => cell.layer === "matched").length, gate.scope.matched_cells_per_candidate);
  assert.equal(sourceCandidate.required_cells.filter((cell) => cell.layer === "native").length, gate.scope.native_cells_per_candidate);
  assert.equal(sourceCandidate.required_cells.filter((cell) => cell.layer === "matched" && cell.pass).length, declared.passed_matched_cells);
  assert.equal(sourceCandidate.required_cells.filter((cell) => cell.layer === "native" && cell.pass).length, declared.passed_native_cells);
  assert.ok(sourceCandidate.required_cells.every((cell) => cell.candidate_seeds === gate.scope.seeds_per_cell));
  assert.ok(sourceCandidate.required_cells.every((cell) => {
    assert.deepEqual(Object.keys(cell.endpoints).sort(), [...gate.scope.required_endpoints_per_cell].sort());
    return cell.pass === Object.values(cell.endpoints).every((endpoint) => endpoint.pass === true);
  }));
  assert.equal(sourceCandidate.pass, declared.promoted);
}

console.log("Main Fig. 3 launch-narrative qualification-scope test passed.");
