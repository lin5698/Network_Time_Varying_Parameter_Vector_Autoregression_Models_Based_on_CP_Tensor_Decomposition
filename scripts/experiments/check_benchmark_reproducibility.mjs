import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { readCsv } from "../natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUTPUT_DIR = path.join(ROOT, "output", "high_impact_revision");
const RUN_ROOT = path.join(OUTPUT_DIR, "r004_seed_reproducibility");
const JSON_PATH = path.join(OUTPUT_DIR, "benchmark_reproducibility_check.json");
const MD_PATH = path.join(OUTPUT_DIR, "benchmark_reproducibility_check.md");
const METHODS = "local_network,cp_network,tucker_network,collapsed_operator_cp";

function runOnce(label) {
  const relativeOutput = path.relative(ROOT, path.join(RUN_ROOT, label));
  const result = spawnSync(process.execPath, ["scripts/natcs_benchmarks.mjs"], {
    cwd: ROOT,
    encoding: "utf8",
    env: {
      ...process.env,
      NATCS_BENCHMARK_OUTPUT_DIR: relativeOutput,
      NATCS_BENCHMARK_SCENARIOS: "scale_n15",
      NATCS_BENCHMARK_METHODS: METHODS,
      NATCS_BENCHMARK_SCALE_REPS: "1",
      NATCS_BENCHMARK_STRESS_REPS: "1",
      NATCS_BENCHMARK_CHECKPOINT: "0",
    },
  });
  if (result.status !== 0) {
    throw new Error(`Benchmark ${label} failed:\n${result.stderr || result.stdout}`);
  }
  return path.join(ROOT, relativeOutput, "benchmark_replications.csv");
}

function deterministicRows(csvPath) {
  return readCsv(csvPath).map((row) => {
    const { runtime_seconds: _runtime, memory_mb: _memory, ...deterministic } = row;
    return deterministic;
  });
}

fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.rmSync(RUN_ROOT, { recursive: true, force: true });
const firstPath = runOnce("run_a");
const secondPath = runOnce("run_b");
const first = deterministicRows(firstPath);
const second = deterministicRows(secondPath);
const firstCanonical = JSON.stringify(first);
const secondCanonical = JSON.stringify(second);
const exactMatch = firstCanonical === secondCanonical;

if (!exactMatch) throw new Error("Deterministic benchmark fields differ across identical runs");
if (first.length !== 4) throw new Error(`Expected four method rows, found ${first.length}`);

const report = {
  generated_at: new Date().toISOString(),
  status: "PASS",
  scenario: "scale_n15",
  replications: 1,
  methods: METHODS.split(","),
  compared_fields: Object.keys(first[0]),
  excluded_volatile_fields: ["runtime_seconds", "memory_mb"],
  row_count: first.length,
  exact_deterministic_match: exactMatch,
};

fs.writeFileSync(JSON_PATH, `${JSON.stringify(report, null, 2)}\n`);
fs.writeFileSync(MD_PATH, `# Benchmark Reproducibility Check

- Status: **${report.status}**
- Scenario: \`${report.scenario}\`
- Methods: ${report.methods.map((method) => `\`${method}\``).join(", ")}
- Compared rows: ${report.row_count}
- Exact match across deterministic fields: **${report.exact_deterministic_match}**
- Excluded volatile fields: \`${report.excluded_volatile_fields.join("\`, \`")}\`

Both runs used isolated output directories. Canonical manuscript benchmark files were not modified.
`);

process.stdout.write(`${JSON.stringify({ status: report.status, json: path.relative(ROOT, JSON_PATH), markdown: path.relative(ROOT, MD_PATH) }, null, 2)}\n`);
