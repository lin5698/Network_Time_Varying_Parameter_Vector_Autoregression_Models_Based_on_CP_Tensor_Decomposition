import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const trackedArtifacts = [
  "output/natcs_assets/figure1_natcs_framework.svg",
  "output/natcs_evidence/summary_metrics.json",
];
for (const script of ["scripts/build_natcs_evidence.mjs", "scripts/build_natcs_manuscript.mjs"]) {
  const result = spawnSync("node", [script], { cwd: root, encoding: "utf8" });
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  assert.equal(result.status, 0, `${script} must run after RC-1/RC-2 activation: ${output}`);
}
for (const relativePath of trackedArtifacts) assert.ok(fs.existsSync(path.join(root, relativePath)), `Authorized builds must produce ${relativePath}.`);

console.log("NCS release gate activation test passed.");
