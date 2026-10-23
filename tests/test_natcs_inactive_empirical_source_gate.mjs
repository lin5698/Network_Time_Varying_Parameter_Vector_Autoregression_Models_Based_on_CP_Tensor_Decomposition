import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const { requireReleaseableNatcsEvidence } = await import(path.join(root, "scripts", "natcs_utils.mjs"));
const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "natcs-inactive-source-gate-"));

function write(relativePath, content) {
  const file = path.join(fixtureRoot, relativePath);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content, "utf8");
}

try {
  write("PAPER_CLAIM_AUDIT.json", JSON.stringify({ verdict: "PASS" }));
  write("EMPIRICAL_IMPLEMENTATION_AUDIT.json", JSON.stringify({ verdict: "PASS" }));
  const activationReceipt = fs.readFileSync(path.join(root, "refine-logs", "REC-P3_RC1_RC2_ACTIVATION_V1_20260830.json"), "utf8");
  write("manuscript_src/natcs/results_rcep.md", "# Inactive audit-boundary draft: RCEP protocol\n");
  write("manuscript_src/natcs/results_generality.md", "# Inactive audit-boundary draft: NYC protocol\n");

  assert.throws(
    () => requireReleaseableNatcsEvidence(fixtureRoot),
    /RCEP empirical source remains explicitly inactive; NYC empirical source remains explicitly inactive/i,
    "Passing audit JSON files cannot reactivate source sections that are still marked inactive.",
  );

  write("manuscript_src/natcs/results_rcep.md", "# Candidate active RCEP result source\n");
  write("manuscript_src/natcs/results_generality.md", "# Candidate active NYC result source\n");
  write("refine-logs/REC-P3_RC1_RC2_ACTIVATION_V1_20260830.json", activationReceipt);
  assert.doesNotThrow(
    () => requireReleaseableNatcsEvidence(fixtureRoot),
    "Replacing both inactive boundary records is a separate deliberate source change after audits pass.",
  );
} finally {
  fs.rmSync(fixtureRoot, { recursive: true, force: true });
}

console.log("Inactive empirical-source release gate test passed.");
