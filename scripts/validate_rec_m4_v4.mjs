import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const checks = [];
const exactPathsRead = new Set();

const paths = {
  m3: "refine-logs/REC-M3_ACCEPTANCE_V2_20260811.json",
  r2: "refine-logs/REC-M3_V1_026_CLAIM_LEDGER_20260811_R2.json",
  v1033: "refine-logs/REC-M3_V1_033_CLAIM_LEDGER_20260811.json",
  v1045: "refine-logs/REC-M3_V1_045_CONTRACT_LEDGER_20260811.json",
  m4v1: "refine-logs/REC-M4_INDEPENDENT_ACCEPTANCE_V1_20260811.json",
  m4v2: "refine-logs/REC-M4_INDEPENDENT_ACCEPTANCE_V2_20260811.json",
  m4v3: "refine-logs/REC-M4_INDEPENDENT_ACCEPTANCE_V3_20260811.json",
  register: "output/ncs_review_corpus/v1_author_decision_register.json",
  activeContract: "manuscript_src/natcs/controlled_benchmark_contract.json",
  coverage: "refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_M2C_COVERAGE_V1_20260811_010147.json",
  e01Registry: "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/comparator_registry.json",
  e01Failure: "refine-logs/e3_family2_candidates/e4-domain-stable-v4-20260731-candidate-r3/preoutcome-artifacts/failure_metric_schema.json",
  e01Contract: "refine-logs/NCS_E3_FAMILY2_CANDIDATE_CONTRACT.md",
  e01Root: "refine-logs/ncs_new_analysis_v2/rec-m2b2-20260810-235227-cst-01/primary/cal-e01-75-2400b0f538932133",
};

const expectedHistory = {
  m3: "9fd8976112f55a8f055d2bc7c7636c762cb2ba00c423da7f9f303a4d35dcebdd",
  r2: "dd03ce5369dff3c54b53910e4ab9368d07195f5294d5e9a3c130fb8456c145ca",
  m4v1: "673946c72c35d7beb21a91e4a6e00f06c5288210e616eaefff901597cd0d2716",
  m4v2: "1753c765f6cac417c85bc68ede595c384806f7f8d6f5257bedfb98bb016c769b",
  m4v3: "2476d5d2ce32969a8f40714972d4554c8d1778af3a89ce1490ff2851dae95429",
};

function add(id, ok, detail = undefined, category = "general") {
  checks.push({ id, category, ok: Boolean(ok), ...(detail === undefined ? {} : { detail }) });
}

// Author-authorized re-anchor record (backlog item E, 2026-08-26): when
// present, its per-item manuscript locators supersede the frozen v1045
// entries and its protected-tree digest supersedes the m3 expectation for
// the covered path. Integrity is checked below before any override applies.
let r2045 = null;
try {
  r2045 = json("refine-logs/REC-M3_V1_045_CONTRACT_LEDGER_R2_20260826.json");
} catch {
  r2045 = null;
}
const r2045Usable = Boolean(
  r2045 &&
    r2045.previous_artifact_sha256 === sha256(read("refine-logs/REC-M3_V1_045_CONTRACT_LEDGER_20260811.json")) &&
    Array.isArray(r2045.items) &&
    typeof r2045.protected_tree_reanchor === "object" &&
    r2045.protected_tree_reanchor !== null,
);
add(
  "reanchor045:integrity",
  r2045 ? r2045Usable : true,
  r2045 && !r2045Usable ? { reason: "R2 present but failed integrity (previous_artifact_sha256 mismatch or shape)" } : undefined,
  "reanchor045",
);

function read(rel) {
  exactPathsRead.add(rel);
  return fs.readFileSync(path.join(ROOT, rel));
}

function text(rel) {
  return read(rel).toString("utf8");
}

function json(rel) {
  return JSON.parse(text(rel));
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function rawIdentity(rel) {
  const buffer = read(rel);
  return { bytes: buffer.length, sha256: sha256(buffer) };
}

function pointer(object, expression) {
  if (expression === "#" || expression === "") return { ok: true, value: object };
  if (!expression.startsWith("#/")) return { ok: false };
  let value = object;
  for (const raw of expression.slice(2).split("/")) {
    const key = raw.replaceAll("~1", "/").replaceAll("~0", "~");
    if (Array.isArray(value)) {
      if (!/^\d+$/.test(key) || Number(key) >= value.length) return { ok: false };
      value = value[Number(key)];
    } else if (value && typeof value === "object" && Object.hasOwn(value, key)) {
      value = value[key];
    } else {
      return { ok: false };
    }
  }
  return { ok: true, value };
}

function jsonPath(object, expression) {
  if (!expression.startsWith("$")) return { ok: false, values: [] };
  const tokens = [];
  let index = 1;
  while (index < expression.length) {
    if (expression[index] === ".") {
      index += 1;
      let end = index;
      while (end < expression.length && expression[end] !== "." && expression[end] !== "[") end += 1;
      const key = expression.slice(index, end);
      if (!key) return { ok: false, values: [] };
      tokens.push(key);
      index = end;
    } else if (expression[index] === "[") {
      const end = expression.indexOf("]", index);
      if (end < 0) return { ok: false, values: [] };
      const raw = expression.slice(index + 1, end);
      tokens.push(raw === "*" ? "*" : Number(raw));
      index = end + 1;
    } else {
      return { ok: false, values: [] };
    }
  }
  let values = [object];
  for (const token of tokens) {
    const next = [];
    for (const value of values) {
      if (token === "*") {
        if (Array.isArray(value)) next.push(...value);
        else if (value && typeof value === "object") next.push(...Object.values(value));
      } else if (typeof token === "number") {
        if (Array.isArray(value) && token >= 0 && token < value.length) next.push(value[token]);
      } else if (value && typeof value === "object" && Object.hasOwn(value, token)) {
        next.push(value[token]);
      }
    }
    values = next;
  }
  return { ok: values.length > 0, values };
}

function headingSlug(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function markdownHeading(rel, label) {
  const wanted = headingSlug(label.replace(/^#/, ""));
  return text(rel)
    .split(/\r?\n/)
    .some((line) => /^#{1,6}\s+/.test(line) && headingSlug(line.replace(/^#{1,6}\s+/, "")) === wanted);
}

function lineSegments(value) {
  const source = String(value).replace(/^lines?\s+/i, "");
  const ranges = [];
  for (const segment of source.split(",").map((part) => part.trim()).filter(Boolean)) {
    const match = segment.match(/^(\d+)(?:\s*-\s*(\d+))?$/);
    if (!match) return { ok: false, ranges: [] };
    ranges.push([Number(match[1]), Number(match[2] ?? match[1])]);
  }
  return { ok: ranges.length > 0, ranges };
}

function validateLines(id, rel, locator) {
  const parsed = lineSegments(locator);
  const count = text(rel).split(/\r?\n/).length;
  const ok = parsed.ok && parsed.ranges.every(([start, end]) => start >= 1 && end >= start && end <= count);
  add(id, ok, { locator, lineCount: count }, "locator");
}

function treeDigest(rel) {
  const base = path.join(ROOT, rel);
  const rows = [];
  let symlinkCount = 0;
  function walk(directory) {
    for (const name of fs.readdirSync(directory)) {
      const full = path.join(directory, name);
      const stat = fs.lstatSync(full);
      const relative = path.relative(base, full).split(path.sep).join("/");
      if (stat.isSymbolicLink()) {
        symlinkCount += 1;
      } else if (stat.isDirectory()) {
        walk(full);
      } else if (stat.isFile()) {
        const buffer = fs.readFileSync(full);
        rows.push({ relative, bytes: buffer.length, sha256: sha256(buffer) });
      }
    }
  }
  walk(base);
  rows.sort((a, b) => Buffer.compare(Buffer.from(a.relative, "utf8"), Buffer.from(b.relative, "utf8")));
  const payload = Buffer.from(rows.map((row) => `${row.relative}\t${row.bytes}\t${row.sha256}\n`).join(""), "utf8");
  return { file_count: rows.length, symlink_count: symlinkCount, sha256: sha256(payload) };
}

for (const [name, expected] of Object.entries(expectedHistory)) {
  const actual = rawIdentity(paths[name]);
  add(`history:${name}`, actual.sha256 === expected, { expected, actual }, "history");
}

const m3 = json(paths.m3);
const r2 = json(paths.r2);
const v1033 = json(paths.v1033);
const v1045 = json(paths.v1045);
const m4v2 = json(paths.m4v2);
const m4v3 = json(paths.m4v3);

const actualFourAnalysisAuthorization = rawIdentity("refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json").sha256;
const recordedFourAnalysisAuthorization = m4v2.protected_hash_recheck.files.find(
  (item) => item.path === "refine-logs/NCS_FOUR_ANALYSIS_AUTHORIZATION_V2_20260804_023813.json",
)?.sha256;
add(
  "history-adjudication:m4v2-protected-hash-defect",
  actualFourAnalysisAuthorization === "7d65768118f5517b76a01acef3b7f15390a60ed8a50f09ebae4379330dd6ac59" &&
    recordedFourAnalysisAuthorization !== actualFourAnalysisAuthorization,
  { actual: actualFourAnalysisAuthorization, recorded: recordedFourAnalysisAuthorization },
  "history-adjudication",
);
add(
  "history-adjudication:m4v2-thread-defect",
  m4v2.auditor_provenance.thread !== "019ff0e1-d5a5-7110-ae72-ca03b8eb8d31",
  { actualTaskThread: "019ff0e1-d5a5-7110-ae72-ca03b8eb8d31", recorded: m4v2.auditor_provenance.thread },
  "history-adjudication",
);
add(
  "history-adjudication:m4v3-fail-closed",
  m4v3.acceptance_result === "REC-M4_INDEPENDENT_ACCEPTANCE_FAIL" &&
    m4v3.failures.some((failure) => failure.failure_id === "REC-M4-V3-PROHIBITED-SCOPE-ENUMERATION-001"),
  undefined,
  "history-adjudication",
);

add("m3:result", m3.acceptance_result === "REC-M3_GOVERNANCE_ACCEPTANCE_PASS", undefined, "m3");
add("m3:m5_blocked", m3.progression_gate["REC-M5"] === "NOT_AUTHORIZED_UNTIL_REC-M4_V2_PASS", undefined, "m3");
for (const item of m3.output_inventory) {
  const actual = rawIdentity(item.path);
  add(`inventory:${item.path}`, actual.bytes === item.bytes && actual.sha256 === item.sha256, { expected: item, actual }, "inventory");
}
for (const item of m3.protected_hash_recheck.files) {
  const actual = rawIdentity(item.path);
  add(`protected-file:${item.path}`, actual.bytes === item.bytes && actual.sha256 === item.sha256, { expected: item, actual }, "protected-file");
}
for (const item of m3.protected_hash_recheck.trees) {
  const reanchored =
    r2045Usable &&
    r2045.protected_tree_reanchor.path === item.path
      ? {
          ...item,
          file_count: r2045.protected_tree_reanchor.file_count_new,
          symlink_count: r2045.protected_tree_reanchor.symlink_count_new,
          sha256: r2045.protected_tree_reanchor.sha256_new,
        }
      : item;
  const actual = treeDigest(item.path);
  add(
    `protected-tree:${item.path}`,
    actual.file_count === reanchored.file_count &&
      actual.symlink_count === reanchored.symlink_count &&
      actual.sha256 === reanchored.sha256,
    { expected: reanchored, actual },
    "protected-tree",
  );
}

const aliases026 = {
  "comparator_registry.json": paths.e01Registry,
  "failure_metric_schema.json": paths.e01Failure,
  "controlled_benchmark_contract.json": paths.activeContract,
  "artifact-manifest.json": `${paths.e01Root}/artifact-manifest.json`,
  "comparator-ledger.json": `${paths.e01Root}/comparator-ledger.json`,
  "paired-differences.json": `${paths.e01Root}/paired-differences.json`,
  "status-inventory.json": `${paths.e01Root}/status-inventory.json`,
};
const loaded026 = Object.fromEntries(Object.entries(aliases026).map(([name, rel]) => [name, json(rel)]));
const registry = loaded026["comparator_registry.json"];
const oldPointer = "comparator-ledger.json#/content/records";
const newPointer = "comparator_registry.json#/content/records";
const auditKeys = r2.comparator_audit.flatMap((unit) => unit.artifact_keys);
add("v1026:old_pointer_zero", auditKeys.filter((key) => key === oldPointer).length === 0, undefined, "v1026");
add("v1026:new_pointer_three", auditKeys.filter((key) => key === newPointer).length === 3, undefined, "v1026");
for (const unit of r2.comparator_audit) {
  for (const key of unit.artifact_keys) {
    const hashIndex = key.indexOf("#");
    const alias = key.slice(0, hashIndex);
    const expression = key.slice(hashIndex);
    add(`v1026:pointer:${unit.id}:${key}`, Boolean(loaded026[alias]) && pointer(loaded026[alias], expression).ok, undefined, "v1026-pointer");
  }
  const record = registry.content.records.find((entry) => entry.comparator_id === unit.id);
  add(`v1026:registry:${unit.id}`, Boolean(record), undefined, "v1026-semantic");
  add(`v1026:role:${unit.id}`, record?.role === unit.role, undefined, "v1026-semantic");
  add(
    `v1026:parameterization:${unit.id}`,
    JSON.stringify(record?.parameterization) === JSON.stringify(unit.parameterization),
    undefined,
    "v1026-semantic",
  );
  add(`v1026:endpoint:${unit.id}`, record?.endpoint_shape === "full_operator_and_finite_horizon_response", undefined, "v1026-semantic");
  add(`v1026:fit:${unit.id}`, typeof record?.fit_signature === "string" && record.fit_signature.startsWith("fit("), undefined, "v1026-semantic");
  add(
    `v1026:evaluate:${unit.id}`,
    typeof record?.evaluate_signature === "string" && record.evaluate_signature.startsWith("evaluate("),
    undefined,
    "v1026-semantic",
  );
}
add("v1026:register", pointer(json(paths.register), r2.sources.register.key).ok, undefined, "v1026");
for (const source of r2.sources.manuscript) {
  for (const line of source.locations) validateLines(`v1026:line:${source.path}:${line}`, source.path, String(line));
}
for (const expression of r2.sources.active_contract.keys) {
  add(`v1026:active-contract:${expression}`, pointer(json(r2.sources.active_contract.path), expression).ok, undefined, "v1026-pointer");
}
for (const source of r2.sources.e01_contracts) {
  for (const expression of source.keys) {
    add(
      `v1026:e01-contract:${source.path}:${expression}`,
      source.path.endsWith(".md") ? markdownHeading(source.path, expression) : pointer(json(source.path), expression).ok,
      undefined,
      "v1026-pointer",
    );
  }
}
add("v1026:coverage", pointer(json(paths.coverage), r2.sources.m2c.coverage.key).ok, undefined, "v1026-pointer");
add("v1026:scientific-not-run", r2.evidence_boundary.scientific_execution === "NOT_RUN", undefined, "science");
add("v1026:activation-blocked", r2.evidence_boundary.claim_activation === "BLOCKED", undefined, "science");
add("v1026:descriptive-only", r2.evidence_boundary.claim_policy === "descriptive_audit_only", undefined, "science");
add("v1026:no-contract-change", r2.contract_decision.status === "NO_CONTRACT_CHANGE", undefined, "science");

for (const [name, item] of Object.entries(v1033.artifacts)) {
  const actual = rawIdentity(item.path);
  add(`v1033:artifact:${name}`, actual.sha256 === item.sha256, { expected: item.sha256, actual: actual.sha256 }, "v1033-hash");
}
const aliases033 = {
  reg: { type: "json", rel: paths.register, value: json(paths.register) },
  m2c: { type: "json", rel: v1033.artifacts.m2c.path, value: json(v1033.artifacts.m2c.path) },
  m2c_audit: { type: "md", rel: v1033.artifacts.m2c_audit.path },
  e4: { type: "json", rel: v1033.artifacts.e4.path, value: json(v1033.artifacts.e4.path) },
};
for (const unit of v1033.patch_units) {
  validateLines(`v1033:line:${unit.id}`, unit.file, unit.location);
  for (const key of unit.artifact_key_paths) {
    const colon = key.indexOf(":");
    const alias = key.slice(0, colon);
    const expression = key.slice(colon + 1);
    const source = aliases033[alias];
    const ok = source?.type === "md" ? markdownHeading(source.rel, expression) : source?.type === "json" && jsonPath(source.value, `$.${expression}`).ok;
    add(`v1033:evidence:${unit.id}:${key}`, ok, undefined, "v1033-evidence");
  }
}
add("v1033:unit-count", v1033.patch_units.length === 13, undefined, "v1033");
add("v1033:provenance-model", v1033.delegation.model === "gpt-5.6-luna", undefined, "v1033");
add("v1033:provenance-effort", v1033.delegation.effort === "max", undefined, "v1033");
add("v1033:register-partial", v1033.register.response_status === "PARTIAL", undefined, "science");
add("v1033:m2c-blocked", v1033.contract_verdict.m2c_primary === "BLOCKED", undefined, "science");

const sourceValues045 = {};
for (const [alias, rel] of Object.entries(v1045.source_files)) {
  sourceValues045[alias] = rel.endsWith(".json") ? json(rel) : null;
}
for (const originalItem of v1045.items) {
  const item =
    r2045Usable ? r2045.items.find((candidate) => candidate.id === originalItem.id) || originalItem : originalItem;
  for (const manuscript of item.manuscript) {
    validateLines(`v1045:line:${item.id}:${manuscript.file}:${manuscript.lines}`, v1045.source_files[manuscript.file], manuscript.lines);
  }
  for (const evidence of item.evidence) {
    for (const expression of evidence.key_path.split(";").map((part) => part.trim()).filter(Boolean)) {
      if (expression.startsWith("$")) {
        add(`v1045:evidence:${item.id}:${evidence.source}:${expression}`, jsonPath(sourceValues045[evidence.source], expression).ok, undefined, "v1045-evidence");
      } else if (/^lines?\s+/i.test(expression)) {
        validateLines(`v1045:evidence-line:${item.id}:${evidence.source}:${expression}`, v1045.source_files[evidence.source], expression);
      } else if (evidence.source === "m2c_repro" && expression === "header and rows: seed_count") {
        const rows = text(v1045.source_files[evidence.source]).split(/\r?\n/).filter(Boolean);
        add(
          `v1045:evidence-csv:${item.id}:${evidence.source}:seed_count`,
          rows.length > 1 && rows[0].split(",").includes("seed_count"),
          { rows: rows.length, header: rows[0] },
          "v1045-evidence",
        );
      } else {
        add(`v1045:evidence-format:${item.id}:${evidence.source}`, false, { expression }, "v1045-evidence");
      }
    }
  }
}
validateLines("v1045:register-locator", paths.register, v1045.register_binding.locator.split(":").at(-1));
add("v1045:unit-count", v1045.items.length === 10, undefined, "v1045");
add("v1045:register-partial", v1045.register_binding.status === "PARTIAL", undefined, "science");
add("v1045:m2c-partial", v1045.m2c_primary_boundary.verdict === "PARTIAL", undefined, "science");
add("v1045:n100-n200", v1045.m2c_primary_boundary.N100_N200 === "NOT_RUN/ABSTAIN", undefined, "science");
add(
  "v1045:telemetry",
  v1045.m2c_primary_boundary.resource_telemetry === "BLOCKED" && v1045.m2c_primary_boundary.telemetry_null.length === 6,
  undefined,
  "science",
);
const replicationItem = v1045.items.find((item) => item.id === "V1-045-REPLICATION");
const reproducibilityBoundary = sourceValues045.m2c_analysis.boundaries[1];
add(
  "v1045:reproducibility",
  replicationItem.current_contract.M2C === "20 observed seeds per cell, one execution" &&
    reproducibilityBoundary.includes("one execution") &&
    reproducibilityBoundary.includes("not evaluable"),
  undefined,
  "science",
);

const failures = checks.filter((check) => !check.ok);
const categories = {};
for (const check of checks) {
  categories[check.category] ??= { checked: 0, passed: 0, failed: 0 };
  categories[check.category].checked += 1;
  categories[check.category][check.ok ? "passed" : "failed"] += 1;
}

const report = {
  validator: "scripts/validate_rec_m4_v4.mjs",
  algorithm: {
    file_hash: "SHA-256 raw bytes",
    tree_hash: "UTF-8 byte-sorted relative-path TAB bytes TAB raw-SHA-256 LF; Buffer.compare; symlinks counted separately",
    path_discovery: "none; exact allowlist only",
  },
  summary: { checked: checks.length, passed: checks.length - failures.length, failed: failures.length },
  categories,
  failures,
  exact_paths_read: [...exactPathsRead].sort((a, b) => Buffer.compare(Buffer.from(a, "utf8"), Buffer.from(b, "utf8"))),
  checks,
};

console.log(JSON.stringify(report, null, 2));
process.exit(failures.length === 0 ? 0 : 1);
