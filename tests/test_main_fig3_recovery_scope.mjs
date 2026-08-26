import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

const figureBuilder = read("scripts/build_natcs_evidence.mjs");
const manuscriptBuilder = read("scripts/build_natcs_manuscript.mjs");
const finalGates = read("scripts/check_natcs_final_gates.mjs");
const results = read("manuscript_src/natcs/results_validation.md");
const supplement = read("manuscript_src/natcs/supp_note4_benchmarks.md");

assert.doesNotMatch(
  figureBuilder,
  /Projection boundary: graph-feature rows/i,
  "Main Fig. 3 must not frame projected graph-feature diagnostics as a plotted comparison.",
);
assert.doesNotMatch(
  results,
  /The final benchmark evaluates projection-based graph-feature stress tests/i,
  "Main Results must not report projected graph-feature numerical comparisons.",
);
assert.match(
  results,
  /Projected graph-feature diagnostics.*Supplementary Note 4 protocol diagnostics.*not native same-endpoint comparisons.*do not license fairness or superiority ranking/i,
  "Main Results must direct projected graph-feature diagnostics to the Supplementary Information.",
);
assert.match(
  supplement,
  /Projected graph-feature stress tests/i,
  "Supplementary Note 4 must retain the projected graph-feature diagnostic record.",
);
assert.match(
  finalGates,
  /function checkMainFigure3RecoveryScope\(\)/,
  "The final gate must prevent projected graph-feature rankings from entering main Fig. 3.",
);
assert.match(
  manuscriptBuilder,
  /CP\/local\/Tucker\/collapsed\/low-rank N=50 rows use \$\{context\.scale_replications_n50\} replications, while sparse and graph-feature diagnostics use one/i,
  "Main Fig. 3 must disclose method-specific N=50 replication coverage.",
);
assert.doesNotMatch(
  manuscriptBuilder,
  /N=50 is a \$\{context\.scale_replications_n50\}-replication bounded stress row/,
  "Main Fig. 3 must not imply that every N=50 comparator has four replications.",
);

console.log("Main Fig. 3 recovery-scope test passed.");
