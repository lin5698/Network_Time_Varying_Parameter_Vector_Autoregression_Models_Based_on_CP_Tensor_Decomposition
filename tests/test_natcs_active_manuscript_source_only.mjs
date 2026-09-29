import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const builder = read("scripts/build_natcs_manuscript.mjs");

assert.doesNotMatch(builder, /import \{ buildNatcsEvidence \}/, "The active manuscript builder must not import the mixed evidence builder.");
assert.doesNotMatch(builder, /import \{ buildNatcsReviewerArchive/, "The active manuscript builder must not import the empirical reviewer archive builder.");

const controlledStart = builder.indexOf("function computeControlledContext");
const controlledEnd = builder.indexOf("function buildMainBenchmarkTable", controlledStart);
assert.ok(controlledStart >= 0 && controlledEnd > controlledStart, "Controlled context function must be independently inspectable.");
const controlledContext = builder.slice(controlledStart, controlledEnd);
assert.match(controlledContext, /benchmark_summary\.csv/, "Controlled context must read the frozen benchmark summary.");
assert.doesNotMatch(controlledContext, /summary_metrics|RCEP|NYC|empirical/i, "Controlled context must not read mixed or application evidence.");
assert.match(controlledContext, /replication contract is unmatched/, "Controlled context must fail closed on unmatched comparator coverage.");

const syncStart = builder.indexOf("function syncSourceOnlySubmissionPackage");
const syncEnd = builder.indexOf("export function buildNatcsManuscript", syncStart);
assert.ok(syncStart >= 0 && syncEnd > syncStart, "Source-only package synchronizer must be independently inspectable.");
const sourceOnlySync = builder.slice(syncStart, syncEnd);
for (const required of [
  "table1_simulation_benchmark.csv",
  "table1b_baseline_tuning_projection.csv",
  "table1d_benchmark_fairness_audit.csv",
  "benchmark_summary.csv",
  "benchmark_replications.csv",
  "controlled_benchmark_contract.json",
]) {
  assert.ok(sourceOnlySync.includes(required), `Source-only package must keep ${required}.`);
}
assert.doesNotMatch(
  sourceOnlySync,
  /summary_metrics|results_rcep|results_generality|buildReadinessReport|buildEditorialClaimLedger|buildNatcsReviewerArchive|portal_surrogate|RCEP|NYC/i,
  "Source-only package synchronizer must not generate historical empirical support material.",
);

const activeStart = builder.indexOf("export function buildNatcsManuscript");
const activeEnd = builder.indexOf("if (import.meta.url", activeStart);
assert.ok(activeStart >= 0 && activeEnd > activeStart, "Active manuscript entry point must be independently inspectable.");
const activeEntry = builder.slice(activeStart, activeEnd);
assert.match(activeEntry, /requireReleaseableNatcsEvidence\(ROOT\)/, "The active entry point must retain the controlling fail-closed gate.");
assert.match(activeEntry, /computeControlledContext\(meta\)/, "The active entry point must use the controlled context.");
assert.match(activeEntry, /syncSourceOnlySubmissionPackage/, "The active entry point must use the source-only package synchronizer.");
assert.doesNotMatch(
  activeEntry,
  /buildNatcsEvidence|summary_metrics|computeContext\(|syncLegacyEmpiricalSubmissionPackage|buildNatcsReviewerArchive|build_natcs_fig2_portal_surrogate|RCEP|NYC/i,
  "The active call graph must not touch mixed evidence, application support or historical portal artifacts.",
);

for (const removedLegacyFunction of [
  "computeContext",
  "buildReadinessReport",
  "buildEditorialClaimLedger",
  "buildClaimSupportMatrix",
  "buildClaimEvidencePositioning",
  "buildNatcsComplianceMatrix",
  "buildIntegrityAudit",
  "buildOverclaimAudit",
  "buildRobustnessEvidenceMap",
  "buildNumericClaimAudit",
  "buildEditorialTriageBrief",
  "buildCleanroomReproductionCheck",
  "buildReproducibilityModeMatrix",
  "syncLegacyEmpiricalSubmissionPackage",
]) {
  assert.doesNotMatch(builder, new RegExp(`function ${removedLegacyFunction}\\b`), `Active builder must not retain legacy function ${removedLegacyFunction}.`);
}

const archivedLegacyBuilder = read("scripts/_archives/legacy_empirical_submission_support_builder_20260731.mjs");
assert.match(archivedLegacyBuilder, /ARCHIVED LEGACY EMPIRICAL SUBMISSION SUPPORT/);
assert.match(archivedLegacyBuilder, /throw new Error\(/, "Archived empirical support must fail closed on import or execution.");

const activeReaderSources = [
  "abstract.md",
  "introduction.md",
  "results_framework.md",
  "results_validation.md",
  "discussion.md",
  "methods_data.md",
  "methods_estimator.md",
  "methods_theory.md",
  "methods_propagation.md",
  "methods_uncertainty.md",
  "supplementary.md",
  "supp_note1_notation.md",
  "supp_note2_estimator.md",
  "supp_note3_propagation.md",
  "supp_note4_benchmarks.md",
  "supp_note8_scope.md",
  "cover_letter.md",
  "data_availability.md",
  "code_availability.md",
].map((name) => read(path.join("manuscript_src/natcs", name))).join("\n");

assert.doesNotMatch(activeReaderSources, /PAPER_CLAIM_AUDIT|EMPIRICAL_IMPLEMENTATION_AUDIT|\bRCEP\b|\bNYC\b|quarantin|scientific execution authorization/i, "Reader-facing active sources must not expose internal governance or inactive applications.");

for (const pattern of [
  /\bE4-R008\b/i,
  /\bCAL-E01:75\b/i,
  /c96e620006d55b1459331c3ead28069920962ccf2df1a682030a37f47e97e635/i,
  /derived-panel-log-error-ratios/i,
  /response_log_error_ratio|operator_log_error_ratio/i,
  /response_cell_ci|operator_cell_ci/i,
  /response_panel_values|operator_panel_values/i,
  /log-error-ratio/i,
]) {
  assert.doesNotMatch(
    activeReaderSources,
    pattern,
    `E4 derived log-ratio/CI material must remain outside active reader sources: ${pattern}`,
  );
}

console.log("NCS active manuscript source-only call-graph test passed.");
