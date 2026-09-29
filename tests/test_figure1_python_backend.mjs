import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const builder = fs.readFileSync(path.join(root, "scripts/build_natcs_manuscript.mjs"), "utf8");
const figureSource = fs.readFileSync(path.join(root, "scripts/build_natcs_framework_figure.py"), "utf8");

assert.doesNotMatch(
  builder,
  /rsvg-convert/,
  "Figure 1 previews and exports must not leave the selected Python backend.",
);
assert.match(
  figureSource,
  /svg\.fonttype[^\n]+none/,
  "Figure 1 must keep SVG text editable.",
);
for (const format of ["svg", "pdf", "png"]) {
  assert.match(
    figureSource,
    new RegExp(`with_suffix\\(\\\"\\.${format}\\\"\\)`),
    `Figure 1 Python source must export ${format.toUpperCase()} directly.`,
  );
}

console.log("Figure 1 Python-backend contract test passed.");
