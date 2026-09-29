import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const activeSources = [
  "manuscript_src/natcs/methods_data.md",
  "manuscript_src/natcs/methods_estimator.md",
  "manuscript_src/natcs/methods_propagation.md",
  "manuscript_src/natcs/methods_theory.md",
  "manuscript_src/natcs/methods_uncertainty.md",
  "manuscript_src/natcs/supplementary.md",
  "manuscript_src/natcs/supp_note1_notation.md",
  "manuscript_src/natcs/supp_note2_estimator.md",
  "manuscript_src/natcs/supp_note3_propagation.md",
  "manuscript_src/natcs/supp_note4_benchmarks.md",
  "manuscript_src/natcs/supp_note8_scope.md",
].map(read).join("\n");

for (const pattern of [
  /PAPER_CLAIM_AUDIT/i,
  /EMPIRICAL_IMPLEMENTATION_AUDIT/i,
  /\bRCEP\b/i,
  /\bNYC\b/i,
  /quarantin/i,
  /production scientific execution/i,
]) {
  assert.doesNotMatch(activeSources, pattern, `Active reader sources must exclude internal empirical-governance language: ${pattern}`);
}

for (const pattern of [
  /79\.4%/i,
  /74\.3-87\.5%/i,
  /0\.000022-0\.000530/i,
  /-0\.000071 to 0\.000470/i,
  /2021 Q2/i,
  /7560 observations/i,
  /selected ridge penalty is 0\.01/i,
  /selected CP rank is 1/i,
  /will be deposited in a DOI-minting repository/i,
]) {
  assert.doesNotMatch(activeSources, pattern, `Quarantined application value leaked into active reader source: ${pattern}`);
}

const data = read("manuscript_src/natcs/methods_data.md");
const estimator = read("manuscript_src/natcs/methods_estimator.md");
const uncertainty = read("manuscript_src/natcs/methods_uncertainty.md");
const note4 = read("manuscript_src/natcs/supp_note4_benchmarks.md");
assert.match(data, /20 replications/i);
assert.doesNotMatch(activeSources, /independent (?:synthetic )?replications/i, "Reader-facing sources must not infer independence without released seed provenance.");
assert.match(estimator, /N\\times 2N\\times T_\{roll\}/i);
assert.match(uncertainty, /0\.95 spectral-norm stabilization rule|spectral norm at or above 0\.95/i);
assert.match(note4, /\| CP anchor split \| 3 \| 0\/16/i);
assert.match(note4, /\| Tucker anchor split \| \(3,3,3\) \| 6\/16/i);

for (const inactive of ["supp_note5_empirical.md", "supp_note6_robustness.md", "supp_note7_repro.md"]) {
  assert.match(read(path.join("manuscript_src/natcs", inactive)), /inactive|not a data- or code-availability declaration/i, `${inactive} must remain an explicitly inactive source record.`);
}

console.log("NCS reader-source empirical-boundary test passed.");
