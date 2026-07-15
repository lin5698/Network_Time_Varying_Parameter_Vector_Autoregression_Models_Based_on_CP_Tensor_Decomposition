import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OUTPUT_DIR = path.join(ROOT, "output", "high_impact_revision");
const JSON_PATH = path.join(OUTPUT_DIR, "response_metric_audit.json");
const MD_PATH = path.join(OUTPUT_DIR, "response_metric_audit.md");

function cumulativeScalarResponse(coefficient, horizon) {
  return Array.from({ length: horizon + 1 }, (_, h) => coefficient ** h);
}

function responseError(truth, estimate, horizon) {
  const trueResponse = cumulativeScalarResponse(truth, horizon);
  const estimatedResponse = cumulativeScalarResponse(estimate, horizon);
  return trueResponse.reduce((total, value, h) => total + Math.abs(value - estimatedResponse[h]), 0) / (horizon + 1);
}

function stabilize(coefficient, threshold = 0.95) {
  return Math.abs(coefficient) >= threshold
    ? Math.sign(coefficient || 1) * threshold
    : coefficient;
}

const cases = [
  { id: "stable", truth: 0.80, estimate: 0.70, horizon: 8 },
  { id: "near_boundary", truth: 0.99, estimate: 0.90, horizon: 8 },
  { id: "one_unstable", truth: 1.10, estimate: 0.90, horizon: 8 },
  { id: "both_unstable", truth: 1.20, estimate: 1.05, horizon: 8 },
].map((entry) => {
  const rawError = responseError(entry.truth, entry.estimate, entry.horizon);
  const stabilizedTruth = stabilize(entry.truth);
  const stabilizedEstimate = stabilize(entry.estimate);
  const stabilizedError = responseError(stabilizedTruth, stabilizedEstimate, entry.horizon);
  return {
    ...entry,
    stabilized_truth: stabilizedTruth,
    stabilized_estimate: stabilizedEstimate,
    raw_response_error: rawError,
    stabilized_response_error: stabilizedError,
    retained_error_fraction: rawError > 0 ? stabilizedError / rawError : 1,
  };
});

const stable = cases.find((entry) => entry.id === "stable");
const bothUnstable = cases.find((entry) => entry.id === "both_unstable");
const oneUnstable = cases.find((entry) => entry.id === "one_unstable");

if (Math.abs(stable.raw_response_error - stable.stabilized_response_error) > 1e-12) {
  throw new Error("Stable-case response error changed under stabilization");
}
if (bothUnstable.stabilized_response_error > 1e-12 || bothUnstable.raw_response_error <= 0) {
  throw new Error("The audit did not reproduce the both-unstable metric collapse");
}
if (oneUnstable.retained_error_fraction >= 0.5) {
  throw new Error("The audit expected substantial error compression in the unstable case");
}

const report = {
  generated_at: new Date().toISOString(),
  audit_status: "ACTION_REQUIRED",
  current_metric_behavior_reproduced: true,
  finding: "Pre-evaluation stabilization can compress or erase response error near and beyond the stability boundary.",
  required_change: "Report raw finite-horizon response error and stability-qualified error separately; never use stabilized error as the only recovery metric.",
  cases,
};

fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.writeFileSync(JSON_PATH, `${JSON.stringify(report, null, 2)}\n`);
const rows = cases.map((entry) => `| ${entry.id} | ${entry.truth.toFixed(2)} | ${entry.estimate.toFixed(2)} | ${entry.raw_response_error.toFixed(6)} | ${entry.stabilized_response_error.toFixed(6)} | ${(100 * entry.retained_error_fraction).toFixed(1)}% |`).join("\n");
fs.writeFileSync(MD_PATH, `# Response Metric Audit

- Audit status: **${report.audit_status}**
- Finding: ${report.finding}
- Required change: ${report.required_change}

| Case | True coefficient | Estimated coefficient | Raw response error | Stabilized response error | Error retained |
| --- | ---: | ---: | ---: | ---: | ---: |
${rows}

This scalar construction isolates metric behavior. It does not evaluate estimator quality.
`);

process.stdout.write(`${JSON.stringify({ status: report.audit_status, json: path.relative(ROOT, JSON_PATH), markdown: path.relative(ROOT, MD_PATH) }, null, 2)}\n`);
