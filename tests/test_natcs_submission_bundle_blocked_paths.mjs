// Static guard: the submission evidence bundle and every standalone packaging
// entry point stay isolated from blocked RCEP/NYC evidence while
// PAPER_CLAIM_AUDIT=BLOCKED and EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL are
// controlling.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

// --- 1. The packaged evidence bundle enumerates controlled-benchmark
// artifacts only. ---

const builder = read("scripts/build_natcs_manuscript.mjs");
const listStart = builder.indexOf("const supportingArtifacts = [");
assert.notEqual(listStart, -1, "supportingArtifacts list must exist.");
const listEnd = builder.indexOf("];", listStart);
assert.notEqual(listEnd, -1, "supportingArtifacts list must terminate.");
const supportingArtifacts = builder.slice(listStart, listEnd);

assert.doesNotMatch(
  supportingArtifacts,
  /rcep|nyc|empirical|validation_recovery|summary_metrics|weak_separation|clipping|stability|selection_summary|girf/i,
  "The evidence bundle may only package controlled-benchmark artifacts while the audits are blocked."
);
for (const requiredEntry of [
  "table1_simulation_benchmark.csv",
  "table1b_baseline_tuning_projection.csv",
  "table1d_benchmark_fairness_audit.csv",
  "benchmark_summary.csv",
  "benchmark_replications.csv",
  "controlled_benchmark_contract.json",
]) {
  assert.ok(
    supportingArtifacts.includes(requiredEntry),
    `The evidence bundle must keep the controlled-benchmark artifact ${requiredEntry}.`
  );
}

// --- 2. Runtime backstop: the package consistency check refuses blocked
// evidence paths regardless of how they enter the bundle. ---

assert.match(
  builder,
  /blockedEvidencePattern\s*=\s*\/\(rcep\|nyc\|empirical\|validation_recovery\|selection_summary\|summary_metrics\|weak_separation\|clipping\|stability\|girf_cp\)\/i/,
  "assertSubmissionPackageClean must scan for blocked evidence basenames."
);
assert.match(
  builder,
  /blocked evidence paths \(PAPER_CLAIM_AUDIT=BLOCKED \/ EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL\)/,
  "The consistency failure must name the controlling audits."
);

// --- 3. Every standalone packaging entry point fails closed on the audit
// gate, so blocked artifacts cannot be re-packaged via Makefile targets. ---

const gatedPackagers = [
  ["scripts/build_natcs_manuscript.mjs", /requireReleaseableNatcsEvidence\(ROOT\)/],
  ["scripts/build_natcs_evidence.mjs", /requireReleaseableNatcsEvidence\(ROOT\)/],
  ["scripts/build_natcs_reviewer_archive.mjs", /export function buildNatcsReviewerArchive\(\) \{[^]*?requireReleaseableNatcsEvidence\(ROOT\);/],
  ["scripts/finalize_natcs_package.mjs", /export function finalizeNatcsPackage\(\) \{[^]*?requireReleaseableNatcsEvidence\(ROOT\);/],
  ["scripts/create_natcs_figure_source_package.mjs", /function main\(\) \{[^]*?requireReleaseableNatcsEvidence\(ROOT\);/],
  ["scripts/create_natcs_upload_freeze_manifest.mjs", /function main\(\) \{[^]*?requireReleaseableNatcsEvidence\(ROOT\);/],
  ["scripts/create_clean_natcs_integrated_package.mjs", /export function createCleanIntegratedPackage\(\) \{[^]*?requireReleaseableNatcsEvidence\(ROOT\);/],
];
for (const [relativePath, pattern] of gatedPackagers) {
  assert.match(
    read(relativePath),
    pattern,
    `${relativePath} must refuse to package artifacts while the controlling audits are blocked.`
  );
}

console.log("NCS submission-bundle blocked-path isolation test passed.");
