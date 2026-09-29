import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const rcep = read("manuscript_src/natcs/results_rcep.md");
const generality = read("manuscript_src/natcs/results_generality.md");
const manuscriptBuilder = read("scripts/build_natcs_manuscript.mjs");
const evidenceBuilder = read("scripts/build_natcs_evidence.mjs");
const finalGates = read("scripts/check_natcs_final_gates.mjs");

assert.match(generality, /\b66\b/);
assert.match(rcep, /\{\{rcep_pre_point_difference\}\}/i);
assert.match(generality, /\{\{nyc_mean_gnet\}\}/i);
assert.match(
  manuscriptBuilder,
  /requireReleaseableNatcsEvidence\(ROOT\)/,
  "The manuscript builder must refuse before it can regenerate an empirical manuscript package.",
);
assert.match(
  evidenceBuilder,
  /requireReleaseableNatcsEvidence\(ROOT\)/,
  "The evidence builder must refuse before it can write manuscript-facing evidence artifacts.",
);
assert.match(
  finalGates,
  /function checkPaperClaimAudit\(\)/,
  "The final-gate script must require the independent paper claim audit.",
);

console.log("Blocked empirical-result boundary test passed.");
