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
  assert.match(text, /PAPER_CLAIM_AUDIT=BLOCKED/i, `${relativePath} must retain the paper-claim block.`);
  assert.match(text, /EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL/i, `${relativePath} must retain the implementation block.`);
}

const checklist = read("manuscript_src/natcs/submission_checklist.md");
const decisionSheet = read("manuscript_src/natcs/natcs_final_author_decision_sheet.md");
assert.doesNotMatch(checklist, /Upload the main manuscript|Run `node scripts\/build_natcs_manuscript\.mjs`/i);
assert.doesNotMatch(decisionSheet, /Go with the conservative submission package|Submission-Day Stop\/Go/i);

console.log("NCS submission-support disablement test passed.");
