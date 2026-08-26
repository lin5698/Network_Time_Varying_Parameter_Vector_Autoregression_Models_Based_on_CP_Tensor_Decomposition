import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const sha256 = (relativePath) =>
  `sha256:${crypto.createHash("sha256").update(fs.readFileSync(path.join(root, relativePath))).digest("hex")}`;

const methods = read("manuscript_src/natcs/methods_theory.md");
const supplement = read("manuscript_src/natcs/supp_note1_notation.md");
const results = read("manuscript_src/natcs/results_framework.md");
const propagationSupplement = read("manuscript_src/natcs/supp_note3_propagation.md");
const headline = [
  read("manuscript_src/natcs/abstract.md"),
  read("manuscript_src/natcs/discussion.md"),
  read("manuscript_src/natcs/cover_letter.md"),
].join("\n");
const ledger = read("manuscript_src/natcs/claim_evidence_ledger.csv");
const audit = JSON.parse(read("paper_rewriting_output/finite_basis_proof_audit_20260731.json"));

assert.equal(audit.verdict, "PASS", "Finite-basis proof must pass its scoped blind audit before manuscript activation.");
for (const [relativePath, expected] of Object.entries(audit.audited_input_hashes)) {
  assert.equal(sha256(relativePath), expected, `Finite-basis proof audit is stale for ${relativePath}.`);
}

for (const source of [methods, supplement]) {
  assert.match(source, /Theorem 1 \(exact finite-basis query certificate\)/);
  assert.match(source, /\\ker X_i\^\{\\Phi\}\(W_0\)\\subseteq\\ker X_i\^\{\\Phi\}\(W_(?:q|q\})\)/);
  assert.match(source, /\\operatorname\{row\}X_i\^\{\\Phi\}\(W_q\)\\subseteq\\operatorname\{row\}X_i\^\{\\Phi\}\(W_0\)/);
}

assert.match(supplement, /The inclusion is strict on every declared topology domain containing \$P\$\./);
assert.match(methods, /endpoint of the queried operator tuple alone/);
assert.match(methods, /\\pi_G\\circ\\Psi=\\operatorname\{id\}/);
assert.match(propagationSupplement, /If \$\\lambda_\{\\min\}\\\{n\^\{-1\}\(Z\^\{\\perp\}\)'Z\^\{\\perp\}\\\}=0\$/);
assert.doesNotMatch(propagationSupplement, /If \$\\eta=0\$/);
assert.match(results, /second, non-equivalent theoretical instance/);
assert.match(results, /does not supply two-hop recovery evidence/i);
assert.match(ledger, /C016,[^\n]+supported as representation theory only/);
assert.doesNotMatch(
  headline,
  /two-hop[^.\n]{0,100}(?:recovery (?:improved|validated)|reduced .*error|empirical(?:ly)? validated)/i,
  "Headline units must not convert the two-hop theorem into a recovery or validation claim.",
);

console.log("Finite-basis certificate activation and claim-boundary test passed.");
