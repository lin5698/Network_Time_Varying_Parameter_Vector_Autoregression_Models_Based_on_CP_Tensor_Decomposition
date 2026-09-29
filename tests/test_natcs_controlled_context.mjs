import assert from "node:assert/strict";

import { computeControlledContext } from "../scripts/build_natcs_manuscript.mjs";

const context = computeControlledContext({ title: "fixture title" });

assert.equal(context.title, "fixture title");
assert.equal(context.operator_gain_n15, "93.6");
assert.equal(context.operator_gain_n30, "96.8");
assert.equal(context.response_gain_n15, "82.5");
assert.equal(context.response_gain_n30, "87.3");
assert.equal(context.scale_replications_n15, 20);
assert.equal(context.scale_replications_n30, 20);
assert.equal(context.scale_replications_n50, 4);
assert.equal(context.baseline_coef_gain_replicated_range, "93.6-96.8");
assert.equal(context.baseline_girf_gain_replicated_range, "82.5-87.3");

console.log("NCS controlled context values and replication contracts passed.");
