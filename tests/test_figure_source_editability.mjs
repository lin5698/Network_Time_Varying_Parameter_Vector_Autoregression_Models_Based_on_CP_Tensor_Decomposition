import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const finalGates = fs.readFileSync(path.join(root, "scripts/check_natcs_final_gates.mjs"), "utf8");

assert.match(finalGates, /function checkFigureSourceEditability\(\)/, "Final gate must verify editable Fig. 1/2 SVG source files.");
for (const file of [
  "output/natcs_assets/figure1_natcs_framework.svg",
  "output/natcs_evidence/fig_validation_recovery.svg",
]) {
  const svg = fs.readFileSync(path.join(root, file), "utf8");
  assert.match(svg, /<text(?:\s|>)/, `${file} must retain text elements for editable source-figure inspection.`);
  assert.doesNotMatch(svg, /<image(?:\s|>)/, `${file} must not replace the figure with an embedded raster image.`);
}

console.log("Figure-source editability test passed.");
