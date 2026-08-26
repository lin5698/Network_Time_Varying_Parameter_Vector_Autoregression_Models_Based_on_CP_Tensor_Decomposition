import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SRC = path.join(ROOT, "manuscript_src", "natcs");

const errors = [];
const passes = [];

const read = (file) => fs.readFileSync(file, "utf8");
const source = (name) => path.join(SRC, name);

function checkFile(file, label) {
  if (!fs.existsSync(file)) {
    errors.push(`Missing ${label}: ${path.relative(ROOT, file)}`);
    return false;
  }
  passes.push(`Found ${label}`);
  return true;
}

function checkReaderFacingBoundary() {
  const activeFiles = [
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
  ];
  const texts = [];
  for (const name of activeFiles) {
    const file = source(name);
    if (checkFile(file, `active source ${name}`)) texts.push(read(file));
  }
  const joined = texts.join("\n");
  const blocked = /PAPER_CLAIM_AUDIT|EMPIRICAL_IMPLEMENTATION_AUDIT|\bRCEP\b|\bNYC\b|quarantin|scientific execution authorization/i;
  if (blocked.test(joined)) errors.push("Active reader-facing source graph contains inactive application or internal-governance wording");
  else passes.push("Active reader-facing source graph is source-only");
}

function checkLaunchNarrativeBoundary() {
  const headlineFiles = ["abstract.md", "results_validation.md", "discussion.md", "cover_letter.md"];
  const headline = headlineFiles.map((name) => read(source(name))).join("\n");
  const builder = read(path.join(ROOT, "scripts", "build_natcs_manuscript.mjs"));
  const exactCounts = /(?:CP[^.\n]{0,80})?(?:0|none) of 16|Tucker[^.\n]{0,80}6 of 16|0 of 8 native/i;
  if (exactCounts.test(`${headline}\n${builder}`)) errors.push("Held-out qualification counts have returned to a headline unit");
  else passes.push("Held-out qualification counts remain outside headline units");

  const methods = read(source("methods_uncertainty.md"));
  const supplement = read(source("supp_note4_benchmarks.md"));
  const results = read(source("results_validation.md"));
  if (!/separate simulation-only endpoint-aware qualification[\s\S]*?is not used to extend these gains/i.test(results)) {
    errors.push("Results no longer retain the matched-design claim-inheritance boundary");
  }
  if (/CP passed 0 of 16 cells|Tucker passed 6 of 16|0 of 8 native cells/i.test(methods)) {
    errors.push("Methods promotes exact held-out qualification counts into the main manuscript");
  }
  if (!/complete cell counts and promotion decision are reported in Supplementary Note 4[\s\S]*?recovery claim remains confined to the original matched controlled design/i.test(methods)) {
    errors.push("Methods no longer retain the supplementary qualification pointer and matched-design boundary");
  }
  if (!/0\/16[\s\S]*?6\/16[\s\S]*?0\/8/i.test(supplement)) {
    errors.push("Supplementary Note 4 no longer retains the complete held-out qualification table");
  }
  passes.push("Qualification boundary and supplementary count placement checked");
}

function checkResponseTerminology() {
  const supplementBuilder = read(path.join(ROOT, "scripts", "build_natcs_supplementary_source_only.mjs"));
  const contractTables = read(path.join(ROOT, "scripts", "natcs_benchmark_contract_tables.mjs"));
  if (/generalized impulse-response|total-GIRF|\"GIRF\"/.test(`${supplementBuilder}\n${contractTables}`)) {
    errors.push("Reader-facing controlled benchmark still labels the identity-shock endpoint as GIRF");
  } else {
    passes.push("Controlled response endpoint uses unit-shock terminology");
  }
  if (!/legacy storage names[\s\S]*?identity-shock finite-horizon response error/i.test(supplementBuilder)) {
    errors.push("Supplementary builder does not disclose the legacy girf_error_* field-name mapping");
  }
}

function checkFiniteBasisClaimBoundary() {
  const methods = read(source("methods_theory.md"));
  const supplement = read(source("supp_note1_notation.md"));
  const results = read(source("results_framework.md"));
  const headline = ["abstract.md", "discussion.md", "cover_letter.md"]
    .map((name) => read(source(name)))
    .join("\n");

  if (!/Theorem 1 \(exact finite-basis query certificate\)/.test(methods)) {
    errors.push("Methods does not expose the accepted finite-basis certificate");
  }
  if (!/The inclusion is strict on every declared topology domain containing \$P\$\./.test(supplement)) {
    errors.push("Supplementary Note 1 does not retain the exact strict-family witness");
  }
  if (!/does not supply two-hop recovery evidence/i.test(results)) {
    errors.push("Results does not state the boundary between two-hop theory and one-hop recovery evidence");
  }
  if (/two-hop[^.\n]{0,100}(?:recovery (?:improved|validated)|reduced .*error|empirical(?:ly)? validated)/i.test(headline)) {
    errors.push("Headline narrative promotes the two-hop theorem as empirical recovery evidence");
  } else {
    passes.push("Finite-basis theory remains separated from one-hop recovery evidence");
  }
}

function runStaticTests() {
  const tests = [
    "tests/test_natcs_active_manuscript_source_only.mjs",
    "tests/test_natcs_active_supplementary_source_only.mjs",
    "tests/test_natcs_controlled_context.mjs",
    "tests/test_natcs_controlled_benchmark_contract.mjs",
    "tests/test_figure1_python_backend.mjs",
    "tests/test_figure2_python_backend.mjs",
    "tests/test_figure3_python_backend.mjs",
    "tests/test_natcs_finite_basis_certificate.mjs",
    "tests/test_main_fig3_recovery_scope.mjs",
    "tests/test_main_fig3_qualification_scope.mjs",
    "tests/test_introduction_contribution_scope.mjs",
  ];
  const result = spawnSync(process.execPath, ["--test", ...tests], { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) {
    errors.push(`Source-only static tests failed: ${(result.stderr || result.stdout || "").trim()}`);
    return;
  }
  passes.push(`${tests.length} source-only static test files passed`);
}

checkReaderFacingBoundary();
checkLaunchNarrativeBoundary();
checkResponseTerminology();
checkFiniteBasisClaimBoundary();
runStaticTests();

const summary = {
  status: errors.length ? "FAIL" : "PASS",
  scope: "source_only_static_no_scientific_execution_no_release",
  errors,
  passes: passes.length,
};

console.log(JSON.stringify(summary, null, 2));
if (errors.length) process.exit(1);
