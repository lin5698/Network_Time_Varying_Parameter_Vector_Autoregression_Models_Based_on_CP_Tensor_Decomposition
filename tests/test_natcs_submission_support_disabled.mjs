import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const files = [
  "manuscript_src/natcs/ncs_portal_field_kit.md",
  "manuscript_src/natcs/ncs_editorial_triage_response_pack.md",
  "manuscript_src/natcs/submission_checklist.md",
  "manuscript_src/natcs/natcs_final_author_decision_sheet.md",
  "manuscript_src/natcs/natcs_coauthor_action_request.md",
];

for (const relativePath of files) {
  const text = read(relativePath);
  assert.doesNotMatch(text, /PAPER_CLAIM_AUDIT=BLOCKED|EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL/i, `${relativePath} must not retain superseded audit blocks.`);
}

const checklist = read("manuscript_src/natcs/submission_checklist.md");
const decisionSheet = read("manuscript_src/natcs/natcs_final_author_decision_sheet.md");
assert.doesNotMatch(checklist, /Upload the main manuscript|Run `node scripts\/build_natcs_manuscript\.mjs`/i);
assert.match(decisionSheet, /Submission-Day Stop\/Go/i);
assert.doesNotMatch(
  decisionSheet,
  /RC-1, manuscript promotion \| `NOT_GRANTED`|RC-2, claim activation \| gated by `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD`/i,
);

console.log("NCS submission-support disablement test passed.");
