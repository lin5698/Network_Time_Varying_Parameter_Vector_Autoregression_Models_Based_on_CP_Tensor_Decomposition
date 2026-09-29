import assert from "assert";
import fs from "fs";
import os from "os";
import path from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const gateScript = path.join(root, "scripts", "check_natcs_final_gates.mjs");

function runAuditOnly(cwdRoot, script) {
  return spawnSync(process.execPath, [script, "--only-empirical-implementation-audit"], {
    cwd: cwdRoot,
    encoding: "utf8",
  });
}

// 1. The gate must fail closed on a non-PASS audit and expose its reason code.
//    Run against an isolated fixture so the check does not depend on the
//    repository's current audit verdict.
const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "natcs-empirical-audit-gate-"));
try {
  fs.mkdirSync(path.join(fixtureRoot, "scripts"));
  const fixtureScript = path.join(fixtureRoot, "scripts", "check_natcs_final_gates.mjs");
  fs.copyFileSync(gateScript, fixtureScript);

  const missing = runAuditOnly(fixtureRoot, fixtureScript);
  assert.equal(missing.status, 1, "a missing empirical audit must fail the final gate");
  assert.equal(JSON.parse(missing.stdout).status, "FAIL");

  fs.writeFileSync(
    path.join(fixtureRoot, "EMPIRICAL_IMPLEMENTATION_AUDIT.json"),
    JSON.stringify({ verdict: "FAIL", reason_code: "rcep_nyc_quarantined_unreviewed" }),
    "utf8"
  );
  const failed = runAuditOnly(fixtureRoot, fixtureScript);
  assert.equal(failed.status, 1, "a non-PASS empirical audit must fail the final gate");
  const failedSummary = JSON.parse(failed.stdout);
  assert.equal(failedSummary.status, "FAIL");
  assert(
    failedSummary.errors.some((error) =>
      error.includes("verdict=FAIL, reason_code=rcep_nyc_quarantined_unreviewed")
    ),
    "the final gate must expose the empirical audit reason code"
  );
} finally {
  fs.rmSync(fixtureRoot, { recursive: true, force: true });
}

// 2. The repository gate result must agree with the recorded audit verdict.
const audit = JSON.parse(fs.readFileSync(path.join(root, "EMPIRICAL_IMPLEMENTATION_AUDIT.json"), "utf8"));
const current = runAuditOnly(root, gateScript);
const currentSummary = JSON.parse(current.stdout);
if (audit.verdict === "PASS") {
  assert.equal(current.status, 0, "a PASS empirical audit must let the audit-only gate pass");
  assert.equal(currentSummary.status, "PASS");
} else {
  assert.equal(current.status, 1, "a non-PASS empirical audit must fail the audit-only gate");
  assert.equal(currentSummary.status, "FAIL");
}

console.log("Empirical implementation final-gate blocker: PASS");
