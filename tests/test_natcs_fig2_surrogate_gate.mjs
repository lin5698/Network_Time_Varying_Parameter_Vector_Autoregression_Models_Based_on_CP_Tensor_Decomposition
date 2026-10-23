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
const result = spawnSync("python3", [script], { cwd: root, encoding: "utf8" });
const output = `${result.stdout || ""}\n${result.stderr || ""}`;
assert.equal(result.status, 0, `The Fig. 2 surrogate should run after RC-1/RC-2 activation: ${output}`);
assert.match(output, /fig2_portal_surrogate_contact_sheet\.png/i);
for (const relativePath of trackedArtifacts) {
  assert.ok(fs.existsSync(path.join(root, relativePath)), `Surrogate must generate ${relativePath}.`);
}

console.log("Fig. 2 surrogate release-gate test passed.");
