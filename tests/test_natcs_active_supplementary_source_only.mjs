// Static guard: the active Supplementary Information build path is
// source-only. It must not load the inactive audit-boundary notes
// (supp_note5_empirical, supp_note6_robustness, supp_note7_repro), any
// RCEP/NYC/E3 artifact, selection summaries, stability diagnostics,
// application figures or the retired validation figure, and the demoted
// legacy empirical supplement builder must stay out of every active script.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const stripLineComments = (source) => source
  .split("\n")
  .filter((line) => !line.trim().startsWith("//"))
  .join("\n");

// --- 1. The source-only Supplementary builder module is totally clean. ---

const moduleSource = read("scripts/build_natcs_supplementary_source_only.mjs");
const moduleCode = stripLineComments(moduleSource);

const moduleForbidden = [
  [/supp_note5|supp_note6|supp_note7/i, "inactive audit-boundary notes (Notes 5-7)"],
  [/natcs_empirical_cp/i, "promoted empirical artifact tree"],
  [/\brcep\b/i, "RCEP material"],
  [/\bnyc\b|nyc_taxi/i, "NYC material"],
  [/\be3\b|e3_family2|refine-logs/i, "E3 candidate material"],
  [/selection_summary/i, "selection summaries"],
  [/summary_metrics/i, "mixed evidence summary metrics"],
  [/fig_validation_recovery|validation_recovery/i, "retired validation figure"],
  [/fig_cp_|fig_nyc_|fig_network_/i, "application figures"],
  [/table2_rcep|table2b_|table2c_|table2d_|table3_nyc/i, "blocked empirical evidence tables"],
  [/weak_separation/i, "weak-separation diagnostics"],
  [/clipping_summary|clipping/i, "clipping diagnostics"],
  [/stability_exclusion|stability_projected|stability_summary|(?<!in)stability_rate/i, "stability diagnostics"],
  [/network_mechanism|propagation_perturbation|structural_break/i, "empirical mechanism/perturbation/break tables"],
  [/girf_cp|bootstrap/i, "empirical GIRF/bootstrap outputs"],
  [/ridge_lambda|cp_rank|selected\s+lambda|selected\s+rank/i, "empirically selected tuning parameters"],
  [/!\[/, "image includes (the source-only supplement carries no figures)"],
];
for (const [pattern, label] of moduleForbidden) {
  assert.doesNotMatch(moduleCode, pattern, `Source-only Supplementary builder must not reference ${label}: ${pattern}`);
}

const moduleRequired = [
  /supp_note1_notation/,
  /supp_note2_estimator/,
  /supp_note3_propagation/,
  /supp_note4_benchmarks/,
  /supp_note8_scope/,
  /"supplementary"/,
  /benchmark_summary\.csv/,
  /ALLOWED_SECTIONS/,
  /refused section outside its contract/,
];
for (const pattern of moduleRequired) {
  assert.match(moduleCode, pattern, `Source-only Supplementary builder must keep its allowed-input contract: ${pattern}`);
}

// The shared contract-table module used by the supplement must be equally clean.
const contractCode = stripLineComments(read("scripts/natcs_benchmark_contract_tables.mjs"));
for (const [pattern, label] of moduleForbidden.filter(([p]) => !/bootstrap/.test(String(p)))) {
  assert.doesNotMatch(contractCode, pattern, `Benchmark contract tables must not reference ${label}: ${pattern}`);
}

// --- 2. The manuscript builder delegates the supplement to the source-only
// module and retains no empirical supplement composition of its own. ---

const builderSource = read("scripts/build_natcs_manuscript.mjs");
const builderCode = stripLineComments(builderSource);

assert.match(
  builderCode,
  /import \{ buildSourceOnlySupplementaryMarkdown \} from "\.\/build_natcs_supplementary_source_only\.mjs";/,
  "The manuscript builder must import the source-only Supplementary builder."
);
assert.match(
  builderCode,
  /const suppTexSource = buildSourceOnlySupplementaryMarkdown\(meta, "vector"\);/,
  "The LaTeX supplement must come from the source-only builder."
);
assert.match(
  builderCode,
  /const suppDocxSource = buildSourceOnlySupplementaryMarkdown\(meta, "raster"\);/,
  "The DOCX supplement must come from the source-only builder."
);
assert.doesNotMatch(
  builderCode,
  /function buildSupplementaryMarkdown/,
  "No local Supplementary composer may exist in the manuscript builder."
);
assert.doesNotMatch(
  builderCode,
  /supp_note5|supp_note7/,
  "The manuscript builder must not touch the inactive Notes 5 and 7 at all."
);

assert.doesNotMatch(
  builderCode,
  /supp_note6|buildOverclaimAudit/,
  "The active manuscript builder must not scan or compose the inactive Note 6."
);

assert.doesNotMatch(
  builderCode,
  /natcs_empirical_cp/,
  "The manuscript builder must not read or copy anything under output/natcs_empirical_cp."
);
assert.doesNotMatch(
  builderCode,
  /"natcs_evidence",\s*"(table2|table3_nyc|fig_validation_recovery)/,
  "The manuscript builder must not read blocked evidence tables or the retired validation figure."
);
assert.doesNotMatch(
  builderCode,
  /path\.join\([^\n]*fig_(cp|nyc|network)_/,
  "The manuscript builder must not construct application-figure paths."
);
assert.doesNotMatch(
  builderCode,
  /selection_summary\.json/,
  "The manuscript builder must not read RCEP/NYC selection summaries."
);
assert.doesNotMatch(
  builderCode,
  /stability_exclusion_sensitivity|stability_projected_sensitivity/,
  "The manuscript builder must not read the RCEP stability sensitivity diagnostics."
);

// --- 3. The demoted legacy builder stays quarantined. ---

const legacyRelative = "scripts/_archives/legacy_empirical_supplement_builder_20260726.mjs";
const legacySource = read(legacyRelative);
assert.match(legacySource, /LEGACY_EMPIRICAL_SUPPLEMENT_DISABLED/, "Legacy module must carry the fail-closed guard.");
assert.match(
  legacySource,
  /NATCS_ALLOW_LEGACY_EMPIRICAL_SUPPLEMENT !== "explicitly-authorized-review-only"/,
  "Legacy module must require the explicit review-only authorization variable."
);
assert.match(legacySource, /throw new Error/, "Legacy guard must throw.");

const activeScriptDir = path.join(root, "scripts");
for (const entry of fs.readdirSync(activeScriptDir)) {
  const file = path.join(activeScriptDir, entry);
  if (!fs.statSync(file).isFile()) continue;
  if (!/\.(mjs|js)$/.test(entry)) continue;
  const text = fs.readFileSync(file, "utf8");
  assert.doesNotMatch(
    text,
    /(from\s+["'][^"']*legacy_empirical_supplement|import\(\s*["'][^"']*legacy_empirical_supplement)/,
    `Active script must not import the legacy empirical supplement builder: scripts/${entry}`
  );
}

// --- 4. The Supplementary declaration matches the composed document. ---

const declaration = read("manuscript_src/natcs/supplementary.md");
assert.match(declaration, /five notes/i, "Declaration must describe the five-note source-only supplement.");
assert.doesNotMatch(declaration, /eight notes/i, "Declaration must no longer describe the eight-note empirical supplement.");
assert.match(declaration, /Application protocols and application-derived results are outside this document/i, "Declaration must state the reader-facing evidence boundary without internal governance language.");
assert.match(
  declaration,
  /No application-derived value, figure, table, selected parameter/i,
  "Declaration must retain the no-application-content commitment."
);
assert.doesNotMatch(declaration, /PAPER_CLAIM_AUDIT|EMPIRICAL_IMPLEMENTATION_AUDIT|\bRCEP\b|\bNYC\b/i, "Reader-facing declaration must not expose internal audit state or inactive applications.");

// --- 5. Dynamic smoke check: compose the document in memory (no files are
// written) and verify the reader-facing surface. ---

const { buildSourceOnlySupplementaryMarkdown } = await import(
  path.join(root, "scripts", "build_natcs_supplementary_source_only.mjs")
);
const meta = JSON.parse(read("manuscript_src/natcs/metadata.json"));

for (const assetFormat of ["vector", "raster"]) {
  const document = buildSourceOnlySupplementaryMarkdown(meta, assetFormat);

  for (const requiredSection of [
    "# Notation and model objects",
    "# Estimator and implementation pipeline",
    "# Propagation objects and topology-argument decomposition",
    "# Synthetic benchmark design and comparator set",
    "# Operating regime and interpretation",
  ]) {
    assert.ok(document.includes(requiredSection), `Composed supplement must keep section: ${requiredSection}`);
  }
  for (const removedSection of [
    "Empirical construction, quarterlyization and inference",
    "Robustness inventory and benchmark dependence",
    "Reproducibility package and availability",
  ]) {
    assert.ok(!document.includes(removedSection), `Composed supplement must not contain the retired section: ${removedSection}`);
  }

  assert.doesNotMatch(document, /!\[/, "Composed supplement must contain no figures.");
  assert.doesNotMatch(document, /Supplementary Figure/i, "Composed supplement must contain no figure captions.");
  assert.doesNotMatch(document, /PAPER_CLAIM_AUDIT|EMPIRICAL_IMPLEMENTATION_AUDIT|\bRCEP\b|\bNYC\b|quarantin/i, "Composed supplement must exclude internal governance and inactive applications.");
  assert.doesNotMatch(
    document,
    /\*Supplementary Table (5|6|7|8|9|10|12|13)\b/,
    "Composed supplement must not carry the retired empirical tables 5-13."
  );
  for (const requiredTable of [
    "*Supplementary Table 1b |",
    "*Supplementary Table 1d |",
    "*Supplementary Table 2a |",
    "*Supplementary Table 2d |",
    "*Supplementary Table 3 |",
    "*Supplementary Table 4 |",
  ]) {
    assert.ok(document.includes(requiredTable), `Composed supplement must keep ${requiredTable.replace(" |", "")}.`);
  }

  const quarantinedValuePatterns = [
    /79\.4%/i,
    /74\.3-87\.5%/i,
    /0\.000022-0\.000530/i,
    /-0\.000071 to 0\.000470/i,
    /2021 Q2/i,
    /7560 observations/i,
    /selected lambda=/i,
    /selected rank=/i,
    /selected ridge loss/i,
    /selected rank validation loss/i,
    /selected ridge penalty is/i,
    /selected CP rank is/i,
  ];
  for (const pattern of quarantinedValuePatterns) {
    assert.doesNotMatch(document, pattern, `Composed supplement leaked a quarantined empirical value: ${pattern}`);
  }
  assert.ok(document.includes("five notes"), "Composed supplement must open with the five-note declaration.");
  assert.doesNotMatch(document, /Fig\. 2a|Fig\. 2e/, "Composed supplement must not retain the retired benchmark-panel numbering.");
  assert.match(document, /Fig\. 2d; Fig\. 3c/, "Endpoint alignment must point to the active availability panels.");
  assert.match(document, /Fig\. 3a-b/, "Replication coverage must point to the active recovery panels.");
}

console.log("NCS active source-only Supplementary guard test passed.");
