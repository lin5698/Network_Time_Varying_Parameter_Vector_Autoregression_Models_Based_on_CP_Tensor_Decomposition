import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const manuscriptBuilder = read("scripts/build_natcs_manuscript.mjs");
const finalGates = read("scripts/check_natcs_final_gates.mjs");
const rcepResults = read("manuscript_src/natcs/results_rcep.md");

assert.match(
  manuscriptBuilder,
  /Panel d reports descriptive Spearman associations.*not a mechanism or causal analysis/i,
  "The Fig. 3 caption must explain its visible topology-association panel and boundary.",
);
assert.match(
  rcepResults,
  /Figure 3d and Supplementary Figure 6.*Supplementary Table 8/i,
  "The RCEP Results must locate the descriptive association claim in Fig. 3d and its supplementary record.",
);
assert.match(
  finalGates,
  /function checkMainFigure3CaptionScope\(\)/,
  "The final gate must prevent Fig. 3 panel-d caption scope from drifting.",
);
assert.match(
  finalGates,
  /Panel d reports descriptive Spearman associations\[\\s\\S\]\*\?not a mechanism or\\s\+causal analysis/,
  "The Fig. 3 final-gate caption check must tolerate LaTeX line wrapping within its boundary phrase.",
);

console.log("Main Fig. 3 caption scope test passed.");
