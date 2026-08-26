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
const before = new Map(
  trackedArtifacts.map((relativePath) => {
    const file = path.join(root, relativePath);
    return [relativePath, fs.statSync(file).mtimeMs];
  }),
);

for (const script of ["scripts/build_natcs_evidence.mjs", "scripts/build_natcs_manuscript.mjs"]) {
  const result = spawnSync("node", [script], { cwd: root, encoding: "utf8" });
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  assert.notEqual(result.status, 0, `${script} must refuse while controlling audits are non-releaseable.`);
  assert.match(output, /NCS_BUILD_REFUSED before evidence generation/i, `${script} must identify the pre-write release gate.`);
}

for (const [relativePath, mtimeMs] of before) {
  const file = path.join(root, relativePath);
  assert.equal(fs.statSync(file).mtimeMs, mtimeMs, `Blocked builds must not rewrite ${relativePath}.`);
}

console.log("NCS release gate test passed.");
