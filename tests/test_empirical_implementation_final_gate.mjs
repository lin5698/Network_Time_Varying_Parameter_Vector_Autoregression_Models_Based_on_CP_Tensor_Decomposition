import assert from "assert";
import path from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const result = spawnSync(
  process.execPath,
  ["scripts/check_natcs_final_gates.mjs", "--only-empirical-implementation-audit"],
  { cwd: root, encoding: "utf8" }
);

assert.equal(result.status, 1, "stale corrected outputs must fail the final gate");
const summary = JSON.parse(result.stdout);
assert.equal(summary.status, "FAIL");
assert(
  summary.errors.some((error) =>
    error.includes("verdict=FAIL, reason_code=rcep_nyc_quarantined_unreviewed")
  ),
  "the final gate must expose the empirical audit reason code"
);

console.log("Empirical implementation final-gate blocker: PASS");
