import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const script = path.join(root, "scripts", "build_natcs_fig2_portal_surrogate.py");
const trackedArtifacts = [
  "output/natcs_fig2_portal_surrogate/fig2_portal_surrogate_summary.json",
  "output/natcs_fig2_portal_surrogate/fig2_portal_surrogate_contact_sheet.png",
];
const before = new Map(
  trackedArtifacts
    .filter((relativePath) => fs.existsSync(path.join(root, relativePath)))
    .map((relativePath) => [relativePath, fs.statSync(path.join(root, relativePath)).mtimeMs]),
);

const result = spawnSync("python3", [script], { cwd: root, encoding: "utf8" });
const output = `${result.stdout || ""}\n${result.stderr || ""}`;
assert.notEqual(result.status, 0, "The Fig. 2 surrogate must refuse while source evidence is inactive.");
assert.match(output, /NCS_FIG2_SURROGATE_REFUSED before preview generation/i);

for (const [relativePath, mtimeMs] of before) {
  assert.equal(fs.statSync(path.join(root, relativePath)).mtimeMs, mtimeMs, `Blocked surrogate must not rewrite ${relativePath}.`);
}

console.log("Fig. 2 surrogate release-gate test passed.");
