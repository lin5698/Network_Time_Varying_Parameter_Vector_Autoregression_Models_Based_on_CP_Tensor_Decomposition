import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const figureSource = fs.readFileSync(
  path.join(root, "scripts/build_natcs_supported_regime_figure.py"),
  "utf8",
);
const manuscriptBuilder = fs.readFileSync(
  path.join(root, "scripts/build_natcs_manuscript.mjs"),
  "utf8",
);

assert.match(figureSource, /svg\.fonttype[^\n]+none/, "Figure 3 must keep SVG text editable.");
assert.match(figureSource, /table1_simulation_benchmark\.csv/, "Figure 3 must read the released controlled summary.");
assert.match(figureSource, /replications != 20/, "Figure 3 must verify the reported replication count before plotting.");
assert.doesNotMatch(figureSource, /r006c_endpoint_gate|0\s*\/\s*16|6\s*\/\s*16|0\s*\/\s*8/i, "Figure 3 must not promote the held-out qualification counts into the main visual narrative.");
assert.match(figureSource, /Target-matched evidence contract/, "Figure 3 must explain why the recovery comparison tests the declared endpoint.");
assert.doesNotMatch(
  figureSource,
  /\bFamily-2\b|\bE3\b|\bRCEP\b|\bNYC\b/,
  "Figure 3 must exclude blocked family and application outcomes.",
);
for (const format of ["svg", "pdf", "png"]) {
  assert.match(
    figureSource,
    new RegExp(`with_suffix\\(\\"\\.${format}\\"\\)`),
    `Figure 3 Python source must export ${format.toUpperCase()} directly.`,
  );
}
assert.match(
  manuscriptBuilder,
  /Figure 3 \| Target-matched reconstruction improves controlled operator and response recovery/,
  "The manuscript must use the supported-regime asset as Figure 3.",
);
assert.match(
  manuscriptBuilder,
  /\$\{context\.operator_gain_n15\}% and \$\{context\.operator_gain_n30\}%/,
  "Figure 3 caption must derive the operator-error reductions from the controlled benchmark context.",
);
assert.match(
  manuscriptBuilder,
  /\$\{context\.response_gain_n15\}% and \$\{context\.response_gain_n30\}%/,
  "Figure 3 caption must derive the response-error reductions from the controlled benchmark context.",
);
assert.match(figureSource, /Response error \(log scale; lower is better\)/, "Figure 3 must use the implemented unit-shock response label.");
assert.doesNotMatch(figureSource, /xlabel="GIRF error/i, "Figure 3 must not label the unit-shock benchmark as a covariance-normalized GIRF.");

console.log("Figure 3 Python-backend and released-evidence contract test passed.");
