import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const introduction = fs.readFileSync(path.join(root, "manuscript_src/natcs/introduction.md"), "utf8");
const finalGates = fs.readFileSync(path.join(root, "scripts/check_natcs_final_gates.mjs"), "utf8");

assert.match(
  introduction,
  /Endpoint availability must be verified at the fitted-object level/i,
  "The Introduction must make topology-switchability a specification-level check, not an unverified family-level claim.",
);
assert.match(
  introduction,
  /separate four requirements for a topology-dependent response: the endpoint must be defined by the fitted object, identified by the design, numerically recoverable and stable over the reported horizon/i,
  "The Introduction must distinguish definition, identification, recovery and stability.",
);
assert.match(
  introduction,
  /The contribution is a testable representation criterion, not a claim that every defined endpoint is statistically recoverable/i,
  "The Introduction must state the contribution as a testable reconstruction criterion.",
);
assert.match(
  introduction,
  /GVAR formulations can use time-varying trade weights and support scenario and impulse-response analysis \[@pesaran2004; @chudik2016/i,
  "The Introduction must acknowledge the closest GVAR time-varying-weight and response-analysis precedent.",
);
assert.match(
  finalGates,
  /function checkIntroductionContributionScope\(\)/,
  "The final gate must preserve the contribution-scope distinction.",
);
assert.match(
  finalGates,
  /GVAR formulations can use time-varying trade weights and support scenario and impulse-response analysis/,
  "The final gate must preserve the verified GVAR precedent acknowledgement.",
);

console.log("Introduction contribution-scope test passed.");
