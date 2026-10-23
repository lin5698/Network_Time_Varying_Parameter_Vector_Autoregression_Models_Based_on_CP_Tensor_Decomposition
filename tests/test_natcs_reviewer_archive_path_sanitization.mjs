import assert from "node:assert/strict";
import { sanitizeArchivePythonSource } from "../scripts/build_natcs_reviewer_archive.mjs";

const source = `ROOT = Path(__file__).resolve().parents[2]\nREGISTER = Path(\n  "/Users/private-user/Desktop/project/output/ncs_review_corpus/v1_author_decision_register.json"\n)`;
const sanitized = sanitizeArchivePythonSource(source);

assert.equal(
  sanitized,
  `ROOT = Path(__file__).resolve().parents[2]\nREGISTER = ROOT / "output/ncs_review_corpus/v1_author_decision_register.json"`
);
assert.doesNotMatch(sanitized, /\/(?:Users|home)\/private-user/);
console.log("NatCS reviewer archive path sanitization test passed.");
