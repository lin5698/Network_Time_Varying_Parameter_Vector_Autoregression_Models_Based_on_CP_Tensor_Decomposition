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

assert.match(
  rcep,
  /Inactive audit-boundary draft: RCEP protocol/i,
  "RCEP must remain an inactive audit-boundary record while claims are blocked.",
);
assert.match(
  rcep,
  /No selected rank, coefficient, interval, ratio, aggregate response, stability statement, topology association, figure or table/i,
  "RCEP must explicitly withhold all quarantined empirical values and artifacts.",
);
assert.match(
  generality,
  /Inactive audit-boundary draft: NYC protocol/i,
  "NYC must remain an inactive audit-boundary record while claims are blocked.",
);
assert.match(
  generality,
  /No selected rank, contrast magnitude, stability statement, bootstrap summary, figure or cross-domain inference/i,
  "NYC must explicitly withhold all quarantined empirical values and artifacts.",
);
assert.doesNotMatch(rcep, /point-series mean difference|Bootstrap median differences|mean 0\.0023/i);
assert.doesNotMatch(generality, /Mean aggregate propagation is|near-null aggregate topology contrast/i);
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
