import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const introduction = fs.readFileSync(path.join(root, "manuscript_src/natcs/introduction.md"), "utf8");
const finalGates = fs.readFileSync(path.join(root, "scripts/check_natcs_final_gates.mjs"), "utf8");

assert.match(
  introduction,
  /Controlled experiments evaluate recovery only after endpoint availability has been assigned/i,
  "The Introduction must make topology-switchability a specification-level check, not an unverified family-level claim.",
);
assert.match(
  introduction,
  /separates four requirements for a topology-dependent response: definition by the fitted object, identification by the design, numerical recovery and finite-horizon stability/i,
  "The Introduction must distinguish definition, identification, recovery and stability.",
);
assert.match(
  introduction,
  /finite-basis theorem supplies the representation criterion/i,
  "The Introduction must state the contribution as a testable reconstruction criterion.",
);
assert.match(
  introduction,
  /GVAR formulations can also use time-varying trade weights/i,
  "The Introduction must acknowledge the closest GVAR time-varying-weight and response-analysis precedent.",
);
assert.match(
  finalGates,
  /function checkIntroductionContributionScope\(\)/,
  "The final gate must preserve the contribution-scope distinction.",
);
assert.match(
  finalGates,
  /GVAR formulations can also use time-varying trade weights/,
  "The final gate must preserve the verified GVAR precedent acknowledgement.",
);

console.log("Introduction contribution-scope test passed.");
