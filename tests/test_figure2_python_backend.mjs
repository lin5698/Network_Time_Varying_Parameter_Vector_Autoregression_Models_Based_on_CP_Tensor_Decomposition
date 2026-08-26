import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const figureSource = fs.readFileSync(
  path.join(root, "scripts/build_natcs_query_certificate_figure.py"),
  "utf8",
);
const manuscriptBuilder = fs.readFileSync(
  path.join(root, "scripts/build_natcs_manuscript.mjs"),
  "utf8",
);

assert.match(
  figureSource,
  /svg\.fonttype[^\n]+none/,
  "Figure 2 must keep SVG text editable.",
);
assert.match(
  figureSource,
  /\\ker T\^\\Phi\(W_0\).*\\subseteq.*\\ker Q\^\\Phi\(W_1\)/,
  "Figure 2 must foreground the exact finite-basis kernel certificate.",
);
assert.match(
  figureSource,
  /one-hop.*\\Phi=\(I,W\).*two-hop.*\\Phi=\(I,W,W\^2\)/,
  "Figure 2 must show the two non-equivalent finite-basis instances.",
);
assert.match(
  figureSource,
  /\(A, B\) = \(-W0, I\)/,
  "Figure 2 must retain the exact unrestricted counterexample.",
);
assert.match(
  figureSource,
  /verified rowwise inverse/,
  "Figure 2 must state the constructive diagonal exception.",
);
assert.doesNotMatch(
  figureSource,
  /\bFamily-2\b|\bE3\b|\bRCEP\b|\bNYC\b/,
  "Figure 2 must use only released theorem and endpoint evidence.",
);
for (const format of ["svg", "pdf", "png"]) {
  assert.match(
    figureSource,
    new RegExp(`with_suffix\\(\\"\\.${format}\\"\\)`),
    `Figure 2 Python source must export ${format.toUpperCase()} directly.`,
  );
}
assert.match(
  manuscriptBuilder,
  /Figure 2 \| Query preservation is certified by factorization through the retained representation/,
  "The manuscript must position the certificate as Figure 2.",
);
assert.match(
  manuscriptBuilder,
  /Figure 3 \| Target-matched reconstruction improves controlled operator and response recovery/,
  "The numerical recovery figure must follow the certificate as Figure 3.",
);

console.log("Figure 2 Python-backend and evidence-boundary contract test passed.");
