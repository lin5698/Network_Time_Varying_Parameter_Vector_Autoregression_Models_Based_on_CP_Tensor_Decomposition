import fs from "fs";
import path from "path";
import crypto from "crypto";
import { spawnSync } from "child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SRC = path.join(ROOT, "manuscript_src", "natcs");
const SUBMISSION = path.join(ROOT, "output", "submission_package", "natcs_current");
const SUBMISSION_MATERIALS = path.join(SUBMISSION, "03_submission_materials");
const LATEST_UPLOAD_ZIP = path.join(ROOT, "output", "integrated_package", "latest_submission_upload_word_only.zip");
const LATEST_UPLOAD_DIR = path.join(ROOT, "output", "integrated_package", "latest_submission_upload_word_only");
const FIGURE_ZIP = path.join(ROOT, "output", "figure_source_package", "latest_natcs_main_figure_sources.zip");
const FIGURE_SOURCE_DIR = path.join(ROOT, "output", "figure_source_package", "natcs_main_figure_sources");
const REVIEWER_ARCHIVE_DIR = path.join(ROOT, "output", "reviewer_archive", "natcs_reviewer_archive");
const REVIEWER_ARCHIVE_ZIP = path.join(ROOT, "output", "reviewer_archive", "latest_natcs_reviewer_archive.zip");
const PAPER_CLAIM_AUDIT = path.join(ROOT, "PAPER_CLAIM_AUDIT.json");
const EMPIRICAL_IMPLEMENTATION_AUDIT = path.join(ROOT, "EMPIRICAL_IMPLEMENTATION_AUDIT.json");

const errors = [];
const warnings = [];
const passes = [];

const COPIED_SUPPORT_FILES = [
  "natcs_final_author_decision_sheet.md",
  "natcs_coauthor_action_request.md",
  "ncs_reference_strategy_memo.md",
  "ncs_editorial_first_screen_audit.md",
  "ncs_portal_field_kit.md",
  "ncs_reviewer_recheck_matrix.md",
  "ncs_editorial_triage_response_pack.md",
  "ncs_language_positioning_bank.md",
  "ncs_availability_consistency_audit.md",
  "ncs_release_safety_audit.md",
  "submission_external_dependency_register.md",
  "ncs_fig2_portal_preview_checklist.md",
  "ncs_fig2_portal_surrogate_audit.md",
  "ncs_figure_qa_memo.md",
  "ncs_fig2_redesign_contract.md",
  "raw_source_access_decision_worksheet.md",
  "public_release_readiness_worksheet.md",
  "submission_checklist.md",
  "ncs_submission_completion_audit.md",
  "ncs_final_artifact_qa_memo.md",
];

const GENERATED_FORMAL_TEXT_FILES = [
  ["cover_letter.md", "cover_letter_natcs.md"],
  ["data_availability.md", "data_availability.txt"],
  ["code_availability.md", "code_availability.txt"],
  ["author_contributions.md", "author_contributions.txt"],
  ["competing_interests.md", "competing_interests.txt"],
  ["ethics_statement.md", "ethics_statement.txt"],
  ["ai_use_statement.md", "ai_use_statement.txt"],
];

const UPLOAD_FORMAL_DOCX_FILES = [
  ["cover_letter_natcs.md", "cover_letter_natcs.docx", "Cover Letter"],
  ["data_availability.txt", "data_availability.docx", "Data availability"],
  ["code_availability.txt", "code_availability.docx", "Code availability"],
  ["author_contributions.txt", "author_contributions.docx", "Author contributions"],
  ["competing_interests.txt", "competing_interests.docx", "Competing interests"],
  ["ethics_statement.txt", "ethics_statement.docx", "Ethics statement"],
  ["ai_use_statement.txt", "ai_use_statement.docx", "AI use statement"],
];

const EXPECTED_UPLOAD_DOCX_FILES = [
  "ai_use_statement.docx",
  "author_contributions.docx",
  "code_availability.docx",
  "competing_interests.docx",
  "cover_letter_natcs.docx",
  "data_availability.docx",
  "ethics_statement.docx",
  "main_manuscript.docx",
  "references.docx",
  "supplementary_information.docx",
];

const ALLOWED_FINAL_WARNING_PATTERNS = [
  /^final author decision sheet has open action rows: \d+ marker\(s\)$/,
  /^Fig\. 2 portal checklist is not externally closed: \d+ marker\(s\)$/,
  /^raw-source worksheet still awaits author sign-off: \d+ marker\(s\)$/,
  /^public-release worksheet still awaits author sign-off: \d+ marker\(s\)$/,
];

const PORTAL_LENGTH_LIMIT_FIELDS = [
  "Novelty",
  "Significance",
  "Computational advance",
  "Evidence",
  "Boundary",
  "Reproducibility",
];

const EXPECTED_UPLOAD_ABSTRACT_PHRASES = [
  "Scientific models of evolving networks",
  "query-certified operator learning",
  "exact unrestricted-block boundary and a structured diagonal inverse",
  "93.6% and 96.8%",
  "82.5% and 87.3%",
  "computations they preserve",
];

const EXPECTED_FIGURE_SOURCE_FILES = [
  "README.md",
  "figures/figure1_callable_operator.pdf",
  "figures/figure1_callable_operator.png",
  "figures/figure1_callable_operator.svg",
  "figures/figure2_query_certificate.pdf",
  "figures/figure2_query_certificate.png",
  "figures/figure2_query_certificate.svg",
  "figures/figure3_supported_regime.pdf",
  "figures/figure3_supported_regime.png",
  "figures/figure3_supported_regime.svg",
  "manifest.json",
  "notes/ncs_fig2_redesign_contract.md",
  "notes/ncs_figure1_python_redesign_qa_20260726.md",
  "notes/ncs_figure2_python_redesign_qa_20260726.md",
  "notes/ncs_figure3_python_redesign_qa_20260726.md",
  "notes/ncs_figure_sequence_contract_20260726.md",
  "notes/ncs_figure_qa_memo.md",
];

const EXPECTED_FIGURE_IDS = ["figure_1", "figure_2", "figure_3"];

const EXPECTED_REVIEWER_ARCHIVE_ENTRYPOINTS = [
  "README.md",
  "manifest.json",
  "reproduce/reproduce_evidence.sh",
  "reproduce/reproduce_manuscript.sh",
  "environment/python-requirements-lock.txt",
  "environment/node-environment.txt",
  "environment/tool_versions.json",
  "data_access/restricted_data_instructions.md",
  "code/scripts/build_natcs_evidence.mjs",
  "code/scripts/build_natcs_manuscript.mjs",
  "code/output/natcs_evidence/evidence_support_map.json",
  "code/output/natcs_evidence/claim_evidence_map.json",
  "code/output/natcs_evidence/reader_facing_evidence_summary.md",
  "code/output/natcs_evidence/reader_facing_summary_metrics.json",
];

const ACTIVE_BUILD_LOCALITY_ROOTS = [
  path.join(ROOT, "output", "natcs_assets"),
  path.join(ROOT, "output", "natcs_benchmarks"),
  path.join(ROOT, "output", "natcs_empirical_cp"),
  path.join(ROOT, "output", "natcs_evidence"),
  REVIEWER_ARCHIVE_DIR,
  SUBMISSION,
  FIGURE_SOURCE_DIR,
  LATEST_UPLOAD_DIR,
  SRC,
  path.join(ROOT, "scripts"),
];

const ACTIVE_BUILD_LOCALITY_FILES = [
  LATEST_UPLOAD_ZIP,
  FIGURE_ZIP,
  REVIEWER_ARCHIVE_ZIP,
];

function rel(file) {
  return path.relative(ROOT, file).replaceAll(path.sep, "/");
}

function readText(file) {
  return fs.readFileSync(file, "utf8");
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function listFilesRecursive(dir, prefix = "") {
  if (!fs.existsSync(dir)) return [];
  const entries = [];
  for (const name of fs.readdirSync(dir).sort()) {
    const absolute = path.join(dir, name);
    const relative = prefix ? `${prefix}/${name}` : name;
    const stat = fs.statSync(absolute);
    if (stat.isDirectory()) {
      entries.push(...listFilesRecursive(absolute, relative));
    } else {
      entries.push(relative);
    }
  }
  return entries;
}

function requireFile(file, label = rel(file)) {
  if (!fs.existsSync(file)) {
    errors.push(`Missing ${label}: ${rel(file)}`);
    return false;
  }
  passes.push(`Found ${label}`);
  return true;
}

function run(command, args, label) {
  const result = spawnSync(command, args, { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) {
    errors.push(`${label} failed: ${(result.stderr || result.stdout || "").trim()}`);
    return "";
  }
  passes.push(`${label} passed`);
  return result.stdout || "";
}

function latestStampedSubmissionUploadZip() {
  const integratedDir = path.join(ROOT, "output", "integrated_package");
  if (!fs.existsSync(integratedDir)) return null;
  const latestStamped = fs.readdirSync(integratedDir)
    .filter((name) => /natcs_integrated_submission_word_only_[0-9_]+_submission_upload\.zip$/.test(name))
    .sort()
    .at(-1);
  return latestStamped ? path.join(integratedDir, latestStamped) : null;
}

function macFileFlags(file) {
  const result = spawnSync("stat", ["-f", "%Sf", file], { cwd: ROOT, encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim() : "";
}

function isDataless(file) {
  return macFileFlags(file).split(",").includes("dataless");
}

function hasNumberedDuplicateSuffix(name) {
  return / \d+(?=(?:\.[^.]+)?$)/.test(name);
}

function isActiveBuildLocalityPath(file) {
  const relative = rel(file);
  const parts = relative.split("/");
  if (parts.includes("_archives")) return false;
  if (parts.includes("__pycache__")) return false;
  if (parts.some((part) => /^backup_before_/i.test(part))) return false;
  if (parts.some((part) => hasNumberedDuplicateSuffix(part))) return false;
  return true;
}

function activeBuildLocalityTargets() {
  return [
    ...ACTIVE_BUILD_LOCALITY_ROOTS,
    ...ACTIVE_BUILD_LOCALITY_FILES,
    latestStampedSubmissionUploadZip(),
  ].filter(Boolean);
}

function collectActiveBuildFiles(target) {
  if (!fs.existsSync(target)) return [];
  if (!isActiveBuildLocalityPath(target)) return [];
  const stat = fs.lstatSync(target);
  if (stat.isDirectory()) {
    return fs.readdirSync(target).sort().flatMap((name) => collectActiveBuildFiles(path.join(target, name)));
  }
  return stat.isFile() ? [target] : [];
}

function checkActiveBuildLocality() {
  const seen = new Set();
  let checked = 0;
  for (const target of activeBuildLocalityTargets()) {
    for (const file of collectActiveBuildFiles(target)) {
      const key = path.resolve(file);
      if (seen.has(key)) continue;
      seen.add(key);
      checked += 1;
      if (isDataless(file)) {
        errors.push(`Active build/package file is dataless: ${rel(file)}`);
      }
    }
  }
  passes.push(`Active build-locality check covered ${checked} file(s)`);
}

function checkEmpiricalImplementationAudit() {
  if (!requireFile(EMPIRICAL_IMPLEMENTATION_AUDIT, "empirical implementation audit JSON")) return;
  if (isDataless(EMPIRICAL_IMPLEMENTATION_AUDIT)) {
    errors.push("Empirical implementation audit JSON is dataless and cannot authorize scientific outputs");
    return;
  }

  let audit;
  try {
    audit = JSON.parse(readText(EMPIRICAL_IMPLEMENTATION_AUDIT));
  } catch (error) {
    errors.push(`Empirical implementation audit JSON is unreadable: ${error.message}`);
    return;
  }

  if (audit.verdict !== "PASS") {
    const reason = audit.reason_code || "missing_reason_code";
    errors.push(`Empirical implementation audit is not PASS: verdict=${audit.verdict || "missing"}, reason_code=${reason}`);
    return;
  }
  passes.push("Empirical implementation audit authorizes regenerated scientific outputs");
}

function checkPaperClaimAudit() {
  if (!requireFile(PAPER_CLAIM_AUDIT, "paper claim audit JSON")) return;
  if (isDataless(PAPER_CLAIM_AUDIT)) {
    errors.push("Paper claim audit JSON is dataless and cannot authorize manuscript claims");
    return;
  }

  let audit;
  try {
    audit = JSON.parse(readText(PAPER_CLAIM_AUDIT));
  } catch (error) {
    errors.push(`Paper claim audit JSON is unreadable: ${error.message}`);
    return;
  }

  if (audit.verdict !== "PASS") {
    const reason = audit.reason_code || "missing_reason_code";
    errors.push(`Paper claim audit is not PASS: verdict=${audit.verdict || "missing"}, reason_code=${reason}`);
    return;
  }
  passes.push("Paper claim audit authorizes manuscript-facing claims");
}

function checkReleaseSafetyAudit() {
  const result = spawnSync("node", ["scripts/audit_natcs_release_safety.mjs", "--check"], { cwd: ROOT, encoding: "utf8" });
  const output = (result.stdout || result.stderr || "").trim();
  if (result.status !== 0) {
    errors.push(`Release safety audit check failed: ${output}`);
    return;
  }
  passes.push("Release safety audit scanner passed in check mode");
  try {
    const summary = JSON.parse(result.stdout);
    if (summary.blockers > 0) {
      errors.push(`Release safety audit reported ${summary.blockers} blocker(s)`);
    }
    if (summary.warnings > 0) {
      warnings.push(`Release safety audit reported ${summary.warnings} warning(s)`);
    } else {
      passes.push("Release safety audit reported no warnings");
    }
  } catch {
    warnings.push(`Could not parse release safety audit check output: ${output}`);
  }

  const generatedJson = path.join(SUBMISSION_MATERIALS, "release_safety_audit.json");
  if (!fs.existsSync(generatedJson)) return;
  const generatedSummary = JSON.parse(readText(generatedJson));
  if (generatedSummary.blocker_count > 0) {
    errors.push(`Generated release safety audit contains ${generatedSummary.blocker_count} blocker(s)`);
  } else {
    passes.push("Generated release safety audit contains no blockers");
  }
}

function countMatches(text, regex) {
  return [...text.matchAll(regex)].length;
}

function wordCount(text) {
  const stripped = String(text)
    .replace(/\{\{[^}]+\}\}/g, " value ")
    .replace(/\{#[^}]+\}/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?/g, " ")
    .replace(/\|.*\|/g, " ")
    .replace(/\$\$[\s\S]*?\$\$/g, " ")
    .replace(/\$[^$]*\$/g, " ");
  return (stripped.match(/[A-Za-z0-9]+(?:[-'"][A-Za-z0-9]+)*/g) || []).length;
}

function readerFacingSubmissionText(text) {
  return String(text ?? "")
    .replace(/Agg_g_net\(H=8\)/g, "aggregate propagation index, H=8")
    .replace(/Pair_([A-Z]{3})<-([A-Z]{3})_s_net_clip/g, "bounded pair-level contribution, $1 <- $2")
    .replace(/Pair_([A-Z]{3})<-([A-Z]{3})_s_net_raw/g, "raw pair-level contribution, $1 <- $2")
    .replace(/(^|[^A-Za-z0-9_])net[\s_-]+clip(?![A-Za-z0-9_])/g, "$1bounded network contribution")
    .replace(/(^|[^A-Za-z0-9_])net[\s_-]+raw(?![A-Za-z0-9_])/g, "$1raw network contribution")
    .replace(/(^|[^A-Za-z0-9_])s[\s_-]+net[\s_-]+clip(?![A-Za-z0-9_])/g, "$1bounded pair-level propagation contribution")
    .replace(/(^|[^A-Za-z0-9_])s[\s_-]+net[\s_-]+raw(?![A-Za-z0-9_])/g, "$1raw pair-level propagation contribution")
    .replace(/(^|[^A-Za-z0-9_])g[\s_-]+net(?![A-Za-z0-9_])/g, "$1aggregate network-propagation index")
    .replace(/(^|[^A-Za-z0-9_])gnet(?![A-Za-z0-9_])/gi, "$1aggregate network-propagation index");
}

function normalizePlainText(text) {
  return String(text ?? "")
    .replace(/\r\n/g, "\n")
    .trim()
    .replace(/[ \t]+$/gm, "")
    .replace(/\n{3,}/g, "\n\n");
}

function pandocPlainFromMarkdown(markdown, label) {
  const result = spawnSync(
    "pandoc",
    ["--from", "markdown+tex_math_dollars+pipe_tables+raw_tex", "--to", "plain", "--wrap=none"],
    { cwd: ROOT, input: markdown, encoding: "utf8" }
  );
  if (result.status !== 0) {
    errors.push(`Could not render expected plain text for ${label}: ${(result.stderr || result.stdout || "").trim()}`);
    return null;
  }
  return normalizePlainText(result.stdout);
}

function pandocPlainFromDocx(docxFile, label) {
  const result = spawnSync("pandoc", [docxFile, "-t", "plain", "--wrap=none"], { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) {
    errors.push(`Could not extract upload DOCX ${label}: ${(result.stderr || result.stdout || "").trim()}`);
    return null;
  }
  return normalizePlainText(result.stdout);
}

function extractPlainSection(text, startHeading, endHeading) {
  const pattern = new RegExp(`(?:^|\\n)${startHeading}\\n\\n([\\s\\S]*?)\\n\\n${endHeading}(?:\\n|$)`);
  const match = pattern.exec(normalizePlainText(text));
  return match ? normalizePlainText(match[1]) : null;
}

function checkRequiredFiles() {
  for (const name of COPIED_SUPPORT_FILES) {
    requireFile(path.join(SRC, name), `source support file ${name}`);
    requireFile(path.join(SUBMISSION_MATERIALS, name), `generated support file ${name}`);
  }

  for (const [sourceName, generatedName] of GENERATED_FORMAL_TEXT_FILES) {
    requireFile(path.join(SRC, sourceName), `source formal file ${sourceName}`);
    requireFile(path.join(SUBMISSION_MATERIALS, generatedName), `generated formal file ${generatedName}`);
  }
  for (const [, docxName] of UPLOAD_FORMAL_DOCX_FILES) {
    requireFile(path.join(LATEST_UPLOAD_DIR, docxName), `upload formal DOCX ${docxName}`);
  }

  requireFile(path.join(SUBMISSION_MATERIALS, "submission_inventory.json"), "submission inventory");
  requireFile(path.join(SUBMISSION_MATERIALS, "release_safety_audit.md"), "release safety audit Markdown");
  requireFile(path.join(SUBMISSION_MATERIALS, "release_safety_audit.json"), "release safety audit JSON");
  requireFile(path.join(SUBMISSION_MATERIALS, "fig2_panel_a_contact_sheet.png"), "Fig. 2 panel-a contact sheet");
  requireFile(path.join(SUBMISSION_MATERIALS, "natcs_upload_freeze_manifest.json"), "upload freeze manifest JSON");
  requireFile(path.join(SUBMISSION_MATERIALS, "natcs_upload_freeze_manifest.md"), "upload freeze manifest Markdown");
  requireFile(LATEST_UPLOAD_ZIP, "latest word-only upload zip");
  requireFile(FIGURE_ZIP, "latest main figure-source zip");
}

function checkCopiedSupportSync() {
  let checked = 0;
  for (const name of COPIED_SUPPORT_FILES) {
    const source = path.join(SRC, name);
    const generated = path.join(SUBMISSION_MATERIALS, name);
    if (!fs.existsSync(source) || !fs.existsSync(generated)) continue;
    const sourceHash = sha256(source);
    const generatedHash = sha256(generated);
    if (sourceHash !== generatedHash) {
      errors.push(`Generated support file is stale: ${name}`);
    }
    checked += 1;
  }
  passes.push(`Copied support-file sync check covered ${checked} file(s)`);
}

function checkGeneratedFormalTextSync() {
  let checked = 0;
  for (const [sourceName, generatedName] of GENERATED_FORMAL_TEXT_FILES) {
    const source = path.join(SRC, sourceName);
    const generated = path.join(SUBMISSION_MATERIALS, generatedName);
    if (!fs.existsSync(source) || !fs.existsSync(generated)) continue;
    const sourceText = readText(source).trim();
    if (/\{\{|\}\}/.test(sourceText)) {
      errors.push(`Source formal file contains unsupported template markers for sync check: ${sourceName}`);
      continue;
    }
    const expected = `${readerFacingSubmissionText(sourceText)}\n`;
    const actual = readText(generated);
    if (actual !== expected) {
      errors.push(`Generated formal file is stale or transformed unexpectedly: ${generatedName} from ${sourceName}`);
    }
    checked += 1;
  }
  passes.push(`Generated formal text sync check covered ${checked} file(s)`);
}

function checkUploadFormalDocxSync() {
  let checked = 0;
  for (const [sourceName, docxName, heading] of UPLOAD_FORMAL_DOCX_FILES) {
    const source = path.join(SUBMISSION_MATERIALS, sourceName);
    const docx = path.join(LATEST_UPLOAD_DIR, docxName);
    if (!fs.existsSync(source) || !fs.existsSync(docx)) continue;
    const body = readText(source).trim();
    const expected = pandocPlainFromMarkdown(`# ${heading}\n\n${body}\n`, `${sourceName} -> ${docxName}`);
    const actual = pandocPlainFromDocx(docx, docxName);
    if (expected === null || actual === null) continue;
    if (actual !== expected) {
      errors.push(`Upload formal DOCX is stale or transformed unexpectedly: ${docxName} from ${sourceName}`);
    }
    checked += 1;
  }
  passes.push(`Upload formal DOCX sync check covered ${checked} file(s)`);
}

function checkWordOnlyUploadContents() {
  const expectedFiles = [...EXPECTED_UPLOAD_DOCX_FILES].sort();
  if (fs.existsSync(LATEST_UPLOAD_DIR)) {
    const actualFiles = fs.readdirSync(LATEST_UPLOAD_DIR).sort();
    const missing = expectedFiles.filter((name) => !actualFiles.includes(name));
    const extra = actualFiles.filter((name) => !expectedFiles.includes(name));
    if (missing.length > 0) errors.push(`Latest upload directory is missing expected DOCX file(s): ${missing.join(", ")}`);
    if (extra.length > 0) errors.push(`Latest upload directory contains unexpected file(s): ${extra.join(", ")}`);
    if (actualFiles.some((name) => !/\.docx$/i.test(name))) {
      errors.push("Latest upload directory contains non-DOCX file(s)");
    }
    passes.push(`Latest upload directory content check covered ${actualFiles.length} file(s)`);
  }

  if (!fs.existsSync(LATEST_UPLOAD_ZIP)) return;
  const zipOutput = run("unzip", ["-Z1", LATEST_UPLOAD_ZIP], "latest word-only upload zip listing");
  if (!zipOutput) return;
  const entries = zipOutput.trim().split(/\r?\n/).filter(Boolean).sort();
  const prefix = "latest_submission_upload_word_only/";
  const expectedEntries = expectedFiles.map((name) => `${prefix}${name}`).sort();
  const missing = expectedEntries.filter((name) => !entries.includes(name));
  const extra = entries.filter((name) => !expectedEntries.includes(name));
  if (missing.length > 0) errors.push(`Latest word-only upload zip is missing expected entry/entries: ${missing.join(", ")}`);
  if (extra.length > 0) errors.push(`Latest word-only upload zip contains unexpected entry/entries: ${extra.join(", ")}`);
  const nonDocx = entries.filter((name) => !/\.docx$/i.test(name));
  if (nonDocx.length > 0) errors.push(`Latest word-only upload zip contains non-DOCX entry/entries: ${nonDocx.join(", ")}`);
  passes.push(`Latest word-only upload zip content check covered ${entries.length} entr${entries.length === 1 ? "y" : "ies"}`);
}

function compareFileSets(label, actualFiles, expectedFiles) {
  const actual = [...actualFiles].sort();
  const expected = [...expectedFiles].sort();
  const missing = expected.filter((name) => !actual.includes(name));
  const extra = actual.filter((name) => !expected.includes(name));
  if (missing.length > 0) errors.push(`${label} is missing expected file(s): ${missing.join(", ")}`);
  if (extra.length > 0) errors.push(`${label} contains unexpected file(s): ${extra.join(", ")}`);
  passes.push(`${label} content check covered ${actual.length} file(s)`);
}

function checkFigureSourcePackageContents() {
  if (fs.existsSync(FIGURE_SOURCE_DIR)) {
    compareFileSets("Figure-source directory", listFilesRecursive(FIGURE_SOURCE_DIR), EXPECTED_FIGURE_SOURCE_FILES);
  }

  const manifestFile = path.join(FIGURE_SOURCE_DIR, "manifest.json");
  if (fs.existsSync(manifestFile)) {
    const manifest = JSON.parse(readText(manifestFile));
    const figureIds = (manifest.figures || []).map((figure) => figure.id).sort();
    compareFileSets("Figure-source manifest figure IDs", figureIds, EXPECTED_FIGURE_IDS);
    const manifestFiles = [
      ...(manifest.figures || []).flatMap((figure) => figure.files || []),
      ...(manifest.notes || []),
    ];
    for (const entry of manifestFiles) {
      const absolute = path.join(FIGURE_SOURCE_DIR, entry.path || "");
      if (!entry.path || !fs.existsSync(absolute)) {
        errors.push(`Figure-source manifest points to missing file: ${entry.path || "(empty path)"}`);
        continue;
      }
      const currentHash = sha256(absolute);
      const currentBytes = fs.statSync(absolute).size;
      if (currentHash !== entry.sha256) {
        errors.push(`Figure-source manifest hash mismatch: ${entry.path}`);
      }
      if (currentBytes !== entry.bytes) {
        errors.push(`Figure-source manifest byte-size mismatch: ${entry.path}`);
      }
    }
    const manifestListed = manifestFiles.map((entry) => entry.path).sort();
    const expectedListed = EXPECTED_FIGURE_SOURCE_FILES.filter((name) => name !== "README.md" && name !== "manifest.json").sort();
    compareFileSets("Figure-source manifest file listing", manifestListed, expectedListed);
  }

  if (!fs.existsSync(FIGURE_ZIP)) return;
  const zipOutput = run("unzip", ["-Z1", FIGURE_ZIP], "main figure-source zip listing");
  if (!zipOutput) return;
  const prefix = "natcs_main_figure_sources/";
  const files = zipOutput
    .trim()
    .split(/\r?\n/)
    .filter(Boolean)
    .filter((entry) => !entry.endsWith("/"))
    .map((entry) => entry.startsWith(prefix) ? entry.slice(prefix.length) : entry)
    .sort();
  compareFileSets("Main figure-source zip", files, EXPECTED_FIGURE_SOURCE_FILES);
}

function checkFigureSourceEditability() {
  const figures = [
    [
      path.join(ROOT, "output", "natcs_assets", "figure1_natcs_framework.svg"),
      path.join(FIGURE_SOURCE_DIR, "figures", "figure1_callable_operator.svg"),
      "Fig. 1",
    ],
    [
      path.join(ROOT, "output", "natcs_assets", "figure2_natcs_query_certificate.svg"),
      path.join(FIGURE_SOURCE_DIR, "figures", "figure2_query_certificate.svg"),
      "Fig. 2",
    ],
    [
      path.join(ROOT, "output", "natcs_assets", "figure3_natcs_supported_regime.svg"),
      path.join(FIGURE_SOURCE_DIR, "figures", "figure3_supported_regime.svg"),
      "Fig. 3",
    ],
  ];
  for (const [source, packaged, label] of figures) {
    if (!requireFile(source, `${label} editable SVG source`) || !requireFile(packaged, `${label} packaged editable SVG source`)) continue;
    const sourceSvg = readText(source);
    const packagedSvg = readText(packaged);
    for (const [svg, location] of [[sourceSvg, "source"], [packagedSvg, "figure-source package"]]) {
      if (!/<text(?:\s|>)/.test(svg)) errors.push(`${label} ${location} SVG has no editable text elements`);
      if (/<image(?:\s|>)/.test(svg)) errors.push(`${label} ${location} SVG contains an embedded raster image`);
    }
    if (sha256(source) !== sha256(packaged)) {
      errors.push(`${label} packaged SVG differs from its editable source export`);
    }
  }
  passes.push("Editable Fig. 1/2 SVG source check passed");
}

function checkReviewerArchiveEntrypoints() {
  let found = 0;
  for (const name of EXPECTED_REVIEWER_ARCHIVE_ENTRYPOINTS) {
    const absolute = path.join(REVIEWER_ARCHIVE_DIR, name);
    if (!fs.existsSync(absolute)) {
      errors.push(`Reviewer archive is missing expected entrypoint: ${name}`);
      continue;
    }
    found += 1;
  }
  passes.push(`Reviewer archive entrypoint check covered ${found} file(s)`);

  for (const name of ["reproduce/reproduce_evidence.sh", "reproduce/reproduce_manuscript.sh"]) {
    const absolute = path.join(REVIEWER_ARCHIVE_DIR, name);
    if (!fs.existsSync(absolute)) continue;
    const executable = (fs.statSync(absolute).mode & 0o111) !== 0;
    if (!executable) errors.push(`Reviewer archive reproduce script is not executable: ${name}`);
  }

  const legacyEvidenceHelper = path.join(REVIEWER_ARCHIVE_DIR, "code", "scripts", "natcs_evidence.py");
  if (fs.existsSync(legacyEvidenceHelper)) {
    errors.push("Reviewer archive includes legacy natcs_evidence.py helper with superseded claim wording");
  } else {
    passes.push("Reviewer archive excludes legacy natcs_evidence.py helper");
  }

  const readmeFile = path.join(REVIEWER_ARCHIVE_DIR, "README.md");
  if (fs.existsSync(readmeFile)) {
    const readme = readText(readmeFile);
    const readmeRequirements = [
      [/query preservation/i, "query-preservation target"],
      [/topology-substitution responses/i, "topology-substitution responses"],
      [/topology-switchable operator/i, "topology-switchable operator"],
      [/CP is the benchmark implementation layer/i, "CP implementation-layer boundary"],
      [/evidence-complete, not raw-data-complete/i, "raw-data boundary"],
      [/not native forecasting benchmarks/i, "graph-feature benchmark boundary"],
    ];
    for (const [regex, phrase] of readmeRequirements) {
      if (!regex.test(readme)) {
        errors.push(`Reviewer archive README is missing first-screen phrase: ${phrase}`);
      }
    }
    passes.push(`Reviewer archive README positioning check covered ${readmeRequirements.length} phrase(s)`);
  }

  const manifestFile = path.join(REVIEWER_ARCHIVE_DIR, "manifest.json");
  if (!fs.existsSync(manifestFile)) return;
  const manifest = JSON.parse(readText(manifestFile));
  const target = manifest.computational_target || {};
  const targetChecks = [
    [target.object, /topology-switchable finite-horizon response operator/i, "manifest computational object"],
    [target.primary_claim, /query preservation/i, "manifest primary claim"],
    [target.implementation_boundary, /CP is the benchmark and empirical implementation layer/i, "manifest CP implementation boundary"],
    [target.review_scope, /Derived-evidence regeneration/i, "manifest review scope"],
  ];
  for (const [value, regex, label] of targetChecks) {
    if (!regex.test(String(value || ""))) {
      errors.push(`Reviewer archive manifest is missing ${label}`);
    }
  }
  const excludedClaims = (target.excluded_claims || []).join(" | ");
  for (const phrase of [
    "raw-data-complete archive",
    "causal RCEP tariff-policy identification",
    "native temporal-GNN forecasting benchmark",
    "broad empirical domain generality",
    "latent-network recovery",
  ]) {
    if (!excludedClaims.includes(phrase)) {
      errors.push(`Reviewer archive manifest excluded-claims boundary is missing: ${phrase}`);
    }
  }
  passes.push("Reviewer archive manifest computational-target check covered 9 field(s)");

  const reproduction = manifest.reproduction || {};
  const entrypoints = reproduction.entrypoints || [];
  const modes = reproduction.modes || {};
  for (const entrypoint of ["Evidence rebuild", "Manuscript rebuild"]) {
    if (!entrypoints.includes(entrypoint)) errors.push(`Reviewer archive manifest missing reproduction entry point: ${entrypoint}`);
  }
  if (!modes.full_output_artifact_rebuild || !modes.fresh_empirical_rerun) {
    errors.push("Reviewer archive manifest is missing required reproduction-mode descriptions");
  }
  if (!/raw-to-derived rebuilds are not self-contained/i.test(String(reproduction.raw_to_derived_boundary_note || ""))) {
    errors.push("Reviewer archive manifest does not preserve the raw-to-derived boundary note");
  }

  const checksumFiles = manifest.checksums?.files || {};
  let checked = 0;
  for (const [name, expectedHash] of Object.entries(checksumFiles)) {
    const absolute = path.join(REVIEWER_ARCHIVE_DIR, name);
    if (!fs.existsSync(absolute)) {
      errors.push(`Reviewer archive checksum points to missing file: ${name}`);
      continue;
    }
    const actualHash = sha256(absolute);
    if (actualHash !== expectedHash) {
      errors.push(`Reviewer archive checksum mismatch: ${name}`);
    }
    checked += 1;
  }
  if (checked < 50) {
    errors.push(`Reviewer archive checksum coverage is unexpectedly small: ${checked} file(s)`);
  }
  passes.push(`Reviewer archive checksum check covered ${checked} file(s)`);
}

function checkReviewerArchiveZipContents() {
  if (!requireFile(REVIEWER_ARCHIVE_ZIP, "latest reviewer archive ZIP")) return;
  const zipOutput = run("unzip", ["-Z1", REVIEWER_ARCHIVE_ZIP], "latest reviewer archive zip listing");
  if (!zipOutput) return;

  const prefix = `${path.basename(REVIEWER_ARCHIVE_DIR)}/`;
  const zipEntries = zipOutput.trim().split(/\r?\n/).filter(Boolean);
  const unexpectedRoots = zipEntries.filter((entry) => !entry.startsWith(prefix));
  if (unexpectedRoots.length > 0) {
    errors.push(`Latest reviewer archive ZIP contains entries outside ${prefix}: ${unexpectedRoots.join(", ")}`);
  }
  const zipFiles = zipEntries
    .filter((entry) => entry.startsWith(prefix) && !entry.endsWith("/"))
    .map((entry) => entry.slice(prefix.length));
  const directoryFiles = listFilesRecursive(REVIEWER_ARCHIVE_DIR);
  compareFileSets("Latest reviewer archive ZIP", zipFiles, directoryFiles);

  if (zipFiles.includes("code/scripts/natcs_evidence.py")) {
    errors.push("Latest reviewer archive ZIP includes legacy natcs_evidence.py helper with superseded claim wording");
  } else {
    passes.push("Latest reviewer archive ZIP excludes legacy natcs_evidence.py helper");
  }

  const mismatched = [];
  let checked = 0;
  for (const name of directoryFiles) {
    if (!zipFiles.includes(name)) continue;
    const result = spawnSync("unzip", ["-p", REVIEWER_ARCHIVE_ZIP, `${prefix}${name}`], {
      cwd: ROOT,
      encoding: null,
      maxBuffer: 64 * 1024 * 1024,
    });
    if (result.status !== 0) {
      errors.push(`Could not read reviewer ZIP entry ${name}: ${String(result.stderr || result.stdout || "").trim()}`);
      continue;
    }
    const archivedHash = crypto.createHash("sha256").update(result.stdout).digest("hex");
    if (archivedHash !== sha256(path.join(REVIEWER_ARCHIVE_DIR, name))) mismatched.push(name);
    checked += 1;
  }
  if (mismatched.length > 0) {
    errors.push(`Latest reviewer archive ZIP differs from the active reviewer directory: ${mismatched.join(", ")}`);
  } else {
    passes.push(`Latest reviewer archive ZIP hash parity covered ${checked} file(s)`);
  }
}

function checkEvidenceMapAliasConsistency() {
  const targets = [
    ["derived evidence support map", path.join(ROOT, "output", "natcs_evidence", "evidence_support_map.json")],
    ["derived claim-evidence map", path.join(ROOT, "output", "natcs_evidence", "claim_evidence_map.json")],
    [
      "reviewer archive evidence support map",
      path.join(REVIEWER_ARCHIVE_DIR, "code", "output", "natcs_evidence", "evidence_support_map.json"),
    ],
    [
      "reviewer archive claim-evidence map",
      path.join(REVIEWER_ARCHIVE_DIR, "code", "output", "natcs_evidence", "claim_evidence_map.json"),
    ],
  ];

  const hashes = [];
  for (const [label, file] of targets) {
    if (!fs.existsSync(file)) {
      errors.push(`Missing evidence-map alias file (${label}): ${rel(file)}`);
      continue;
    }
    hashes.push([label, sha256(file)]);
  }
  if (hashes.length !== targets.length) return;

  const uniqueHashes = new Set(hashes.map(([, hash]) => hash));
  if (uniqueHashes.size !== 1) {
    const details = hashes.map(([label, hash]) => `${label}=${hash}`).join("; ");
    errors.push(`Evidence-map alias files do not share one SHA-256 hash: ${details}`);
    return;
  }

  passes.push(`Evidence-map alias consistency check covered ${hashes.length} file(s) with SHA-256 ${hashes[0][1]}`);
}

function checkReaderFacingEvidenceSummary() {
  const summaryFiles = [
    [path.join(ROOT, "output", "natcs_evidence", "reader_facing_evidence_summary.md"), "local reader-facing evidence guide"],
    [
      path.join(REVIEWER_ARCHIVE_DIR, "code", "output", "natcs_evidence", "reader_facing_evidence_summary.md"),
      "reviewer archive reader-facing evidence guide",
    ],
  ];
  const requirements = [
    [/## Computational target/, "computational target section"],
    [/query preservation for topology-substitution responses/i, "query-preservation target"],
    [/topology-switchable finite-horizon operator/i, "topology-switchable operator"],
    [/observed, zero-network and frozen-topology endpoints/i, "endpoint availability sequence"],
    [/CP is the benchmark and empirical implementation layer/i, "CP implementation boundary"],
    [/## Evidence boundary/, "evidence boundary section"],
    [/does not claim a raw-data-complete archive/i, "raw-data boundary"],
    [/causal RCEP tariff-policy identification/i, "RCEP causality boundary"],
    [/native temporal-GNN forecasting performance/i, "temporal-GNN boundary"],
    [/broad empirical domain generality/i, "generality boundary"],
    [/latent-network recovery/i, "latent-network boundary"],
  ];

  for (const [file, label] of summaryFiles) {
    if (!requireFile(file, label)) continue;
    const text = readText(file);
    for (const [regex, phrase] of requirements) {
      if (!regex.test(text)) {
        errors.push(`${label} is missing reader-facing evidence phrase: ${phrase}`);
      }
    }
    passes.push(`${label} target/boundary check covered ${requirements.length} phrase(s)`);
  }

  const metricsFiles = [
    [path.join(ROOT, "output", "natcs_evidence", "reader_facing_summary_metrics.json"), "local reader-facing summary metrics"],
    [
      path.join(REVIEWER_ARCHIVE_DIR, "code", "output", "natcs_evidence", "reader_facing_summary_metrics.json"),
      "reviewer archive reader-facing summary metrics",
    ],
  ];
  for (const [file, label] of metricsFiles) {
    if (!requireFile(file, label)) continue;
    const metrics = JSON.parse(readText(file));
    const target = metrics.computational_target || {};
    const targetText = [
      target.object,
      target.primary_claim,
      target.evidence_order,
      target.implementation_boundary,
      ...(target.excluded_claims || []),
    ].join(" | ");
    for (const phrase of [
      "Topology-switchable finite-horizon response operator",
      "Query preservation",
      "Endpoint availability first",
      "CP is the benchmark and empirical implementation layer",
      "raw-data-complete archive",
      "causal RCEP tariff-policy identification",
      "native temporal-GNN forecasting performance",
      "broad empirical domain generality",
      "latent-network recovery",
    ]) {
      if (!targetText.includes(phrase)) {
        errors.push(`${label} computational_target is missing: ${phrase}`);
      }
    }
    const synth = metrics.synthetic_benchmark || {};
    const replicatedCoef = synth.effective_operator_error_reduction_percent_replicated_n15_n30 || [];
    const replicatedGirf = synth.impulse_response_error_reduction_percent_replicated_n15_n30 || [];
    if (replicatedCoef.length !== 2) {
      errors.push(`${label} must report exactly two replicated N=15/N=30 effective-operator gains`);
    }
    if (replicatedGirf.length !== 2) {
      errors.push(`${label} must report exactly two replicated N=15/N=30 impulse-response gains`);
    }
    if (Math.max(...replicatedCoef.map(Number)) >= 98) {
      errors.push(`${label} appears to include the N=50 bounded stress gain in the replicated N=15/N=30 effective-operator field`);
    }
    if (!Number.isFinite(Number(synth.effective_operator_error_reduction_percent_bounded_n50))) {
      errors.push(`${label} is missing the separate N=50 bounded effective-operator gain`);
    }
    if (!Number.isFinite(Number(synth.impulse_response_error_reduction_percent_bounded_n50))) {
      errors.push(`${label} is missing the separate N=50 bounded impulse-response gain`);
    }
    for (const legacyField of [
      "effective_operator_error_reduction_percent",
      "impulse_response_error_reduction_percent",
    ]) {
      if (Object.prototype.hasOwnProperty.call(synth, legacyField)) {
        errors.push(`${label} still contains ambiguous legacy field: ${legacyField}`);
      }
    }
    passes.push(`${label} target/boundary and replicated-gain check covered 2 gain arrays`);
  }
}

function markdownTableCells(line) {
  return line.split("|").slice(1, -1).map((cell) => cell.trim());
}

function checkPortalFieldLengthLimits() {
  const file = path.join(SRC, "ncs_portal_field_kit.md");
  if (!fs.existsSync(file)) return;
  const lines = readText(file).split(/\r?\n/);
  const rows = new Map();
  let inTable = false;
  for (const line of lines) {
    if (line.startsWith("| Portal field | Up to 150 characters |")) {
      inTable = true;
      continue;
    }
    if (inTable && line.startsWith("## ")) break;
    if (!inTable || !line.startsWith("|") || /^\|\s*-+/.test(line)) continue;
    const cells = markdownTableCells(line);
    if (cells.length < 4) continue;
    const [field, short150, short300] = cells;
    rows.set(field, { short150, short300 });
  }

  for (const field of PORTAL_LENGTH_LIMIT_FIELDS) {
    const row = rows.get(field);
    if (!row) {
      errors.push(`Portal field kit is missing length-limited row: ${field}`);
      continue;
    }
    const short150Length = Array.from(row.short150).length;
    const short300Length = Array.from(row.short300).length;
    if (short150Length === 0) errors.push(`Portal 150-character variant is empty: ${field}`);
    if (short300Length === 0) errors.push(`Portal 300-character variant is empty: ${field}`);
    if (short150Length > 150) errors.push(`Portal 150-character variant exceeds limit for ${field}: ${short150Length} characters`);
    if (short300Length > 300) errors.push(`Portal 300-character variant exceeds limit for ${field}: ${short300Length} characters`);
  }

  for (const field of rows.keys()) {
    if (!PORTAL_LENGTH_LIMIT_FIELDS.includes(field)) {
      errors.push(`Portal field kit has unexpected length-limited row: ${field}`);
    }
  }
  passes.push(`Portal length-limited field check covered ${rows.size} row(s)`);
}

function checkInventory() {
  const inventoryFile = path.join(SUBMISSION_MATERIALS, "submission_inventory.json");
  if (!fs.existsSync(inventoryFile)) return;
  const inventory = JSON.parse(readText(inventoryFile));
  const materials = inventory.files?.submission_materials || {};
  const requiredKeys = [
    "final_author_decision_sheet",
    "coauthor_action_request",
    "reference_strategy_memo",
    "editorial_first_screen_audit",
    "portal_field_kit",
    "reviewer_recheck_matrix",
    "editorial_triage_response_pack",
    "language_positioning_bank",
    "availability_consistency_audit",
    "release_safety_audit_protocol",
    "release_safety_audit_md",
    "release_safety_audit_json",
    "external_dependency_register",
    "fig2_portal_preview_checklist",
    "fig2_portal_surrogate_audit",
    "fig2_portal_surrogate_contact_sheet",
    "fig2_panel_a_contact_sheet",
    "fig2_portal_surrogate_summary",
    "figure_qa_memo",
    "fig2_redesign_contract",
    "raw_source_access_worksheet",
    "public_release_readiness_worksheet",
    "submission_checklist",
    "submission_completion_audit",
    "final_artifact_qa_memo",
    "upload_freeze_manifest_json",
    "upload_freeze_manifest_md",
  ];
  for (const key of requiredKeys) {
    const listed = materials[key];
    if (!listed) {
      errors.push(`Missing submission_inventory entry: ${key}`);
      continue;
    }
    const absolute = path.join(ROOT, listed);
    if (!fs.existsSync(absolute)) {
      errors.push(`Inventory entry ${key} points to missing file: ${listed}`);
      continue;
    }
    passes.push(`Inventory entry ${key} is present`);
  }
}

function checkFreezeManifest() {
  const manifestFile = path.join(SUBMISSION_MATERIALS, "natcs_upload_freeze_manifest.json");
  if (!fs.existsSync(manifestFile)) return;
  const manifest = JSON.parse(readText(manifestFile));
  if (!Array.isArray(manifest.artifacts)) {
    errors.push("Upload freeze manifest has no artifacts array");
    return;
  }
  let checked = 0;
  for (const artifact of manifest.artifacts) {
    if (!artifact.exists) {
      warnings.push(`Freeze manifest records missing optional artifact: ${artifact.label} (${artifact.path})`);
      continue;
    }
    const absolute = path.join(ROOT, artifact.path);
    if (!fs.existsSync(absolute)) {
      errors.push(`Frozen artifact missing now: ${artifact.label} (${artifact.path})`);
      continue;
    }
    const currentHash = sha256(absolute);
    const currentBytes = fs.statSync(absolute).size;
    if (currentHash !== artifact.sha256) {
      errors.push(`Frozen artifact hash changed: ${artifact.label} (${artifact.path})`);
    }
    if (currentBytes !== artifact.bytes) {
      errors.push(`Frozen artifact byte size changed: ${artifact.label} (${artifact.path})`);
    }
    checked += 1;
  }
  passes.push(`Upload freeze manifest hash check covered ${checked} artifact(s)`);
}

function checkFormalOverclaims() {
  const formalFiles = [
    path.join(SRC, "abstract.md"),
    path.join(SRC, "introduction.md"),
    path.join(SRC, "results_validation.md"),
    path.join(SRC, "results_rcep.md"),
    path.join(SRC, "results_generality.md"),
    path.join(SRC, "discussion.md"),
    path.join(SRC, "cover_letter.md"),
    path.join(SRC, "data_availability.md"),
    path.join(SRC, "code_availability.md"),
    path.join(SUBMISSION_MATERIALS, "cover_letter_natcs.md"),
    path.join(SUBMISSION_MATERIALS, "data_availability.txt"),
    path.join(SUBMISSION_MATERIALS, "code_availability.txt"),
  ].filter((file) => fs.existsSync(file));

  const forbidden = [
    [/all raw data/gi, "all raw data"],
    [/all data are publicly available/gi, "all data are publicly available"],
    [/fully reproducible from raw/gi, "fully reproducible from raw"],
    [/raw data and code are publicly available/gi, "raw data and code are publicly available"],
    [/doi and licen[cs]e are already assigned/gi, "DOI and licence are already assigned"],
    [/zenodo doi/gi, "Zenodo DOI"],
    [/placeholder doi/gi, "placeholder DOI"],
    [/expected doi/gi, "expected DOI"],
    [/rcep caused/gi, "RCEP caused"],
    [/causal rcep/gi, "causal RCEP"],
    [/causal policy effects?/gi, "causal policy effect"],
    [/policy effects/gi, "policy effects"],
    [/policy effect\b/gi, "policy effect"],
    [/broadly generalizes/gi, "broadly generalizes"],
    [/outperforms temporal gnns/gi, "outperforms temporal GNNs"],
    [/state-of-the-art temporal gnn/gi, "state-of-the-art temporal GNN"],
  ];

  for (const file of formalFiles) {
    const text = readText(file);
    for (const [regex, label] of forbidden) {
      regex.lastIndex = 0;
      if (regex.test(text)) {
        errors.push(`Forbidden formal claim "${label}" found in ${rel(file)}`);
      }
    }
  }
  passes.push(`Formal overclaim scan covered ${formalFiles.length} files`);

  const discouraged = /\b(rather than|since|however|therefore|not only|not\s+[^.\n]{0,80}\s+but)\b/gi;
  for (const file of formalFiles) {
    const count = countMatches(readText(file), discouraged);
    if (count > 0) {
      warnings.push(`Discouraged transition pattern count in ${rel(file)}: ${count}`);
    }
  }
}

function checkPreservationWordingPrecision() {
  const files = [
    "abstract.md",
    "introduction.md",
    "results_validation.md",
    "methods_theory.md",
    "methods_estimator.md",
    "discussion.md",
    "cover_letter.md",
    "supp_note2_estimator.md",
    "supp_note4_benchmarks.md",
    "supp_note8_scope.md",
    "ncs_portal_field_kit.md",
    "ncs_editorial_triage_response_pack.md",
    "ncs_language_positioning_bank.md",
  ].map((name) => path.join(SRC, name)).filter((file) => fs.existsSync(file));
  const ambiguous = /\bpreservation-constrained\b|\b(?:target-)?preservation constraint\b|\bconstrained to preserve\b/gi;
  for (const file of files) {
    ambiguous.lastIndex = 0;
    if (ambiguous.test(readText(file))) {
      errors.push(`Ambiguous constrained-optimization wording found in ${rel(file)}`);
    }
  }
  passes.push(`Preservation-wording precision check covered ${files.length} file(s)`);
}

function checkCollapsedEndpointIdentifiabilityBoundary() {
  const methodsFile = path.join(SRC, "methods_theory.md");
  const supplementFile = path.join(SRC, "supp_note1_notation.md");
  const required = [
    [methodsFile, /Proposition 1 \(exact unrestricted-block query-factorization boundary\)/i, "exact unrestricted factorization proposition"],
    [methodsFile, /if and only if \$W_1=W_0\$/i, "iff topology boundary"],
    [methodsFile, /Corollary 1 \(diagonal structured inverse\)/i, "diagonal structured inverse"],
    [supplementFile, /T_\{W_0\}\(0,0\)=0=T_\{W_0\}\(-W_0,I\)/i, "two-pair counterexample"],
    [supplementFile, /Direct-only evaluation[\s\S]{0,160}if and only if \$W_0=0\$/i, "direct-only degenerate boundary"],
    [supplementFile, /scalar finite-horizon response inherits non-identification only if it is nonconstant/i, "response-sensitivity boundary"],
    [supplementFile, /every zero row of \$W_0\$ is also a zero row of \$W_1\$/i, "diagonal zero-row boundary"],
    [supplementFile, /does not enforce the diagonal image conditions[\s\S]{0,180}apply the displayed inverse/i, "collapsed-ablation target boundary"],
    [supplementFile, /W_\{\\tau-k\}y_\{\\tau-k\}/i, "lag-specific estimation topology"],
    [supplementFile, /\\bar W_t:=W_\{t-1\}/i, "last-available response topology"],
  ];
  for (const [file, regex, label] of required) {
    if (!fs.existsSync(file) || !regex.test(readText(file))) {
      errors.push(`Collapsed-endpoint identifiability argument is missing ${label} in ${rel(file)}`);
    }
  }

  const claimFiles = [
    "abstract.md",
    "introduction.md",
    "discussion.md",
    "cover_letter.md",
    "ncs_portal_field_kit.md",
    "ncs_editorial_triage_response_pack.md",
  ].map((name) => path.join(SRC, name)).filter((file) => fs.existsSync(file));
  const universalImpossibility = /\b(?:every|all|any) collapsed (?:map|representation|model)[^.\n]{0,120}\b(?:impossible|cannot|undefined|unavailable)\b|\bcollapsed (?:maps?|representations?|models?)[^.\n]{0,120}\bmathematically impossible\b/gi;
  for (const file of claimFiles) {
    universalImpossibility.lastIndex = 0;
    if (universalImpossibility.test(readText(file))) {
      errors.push(`Universal collapsed-map impossibility claim found in ${rel(file)}`);
    }
  }
  passes.push(`Collapsed-endpoint identifiability boundary check covered ${required.length} proof/boundary elements and ${claimFiles.length} claim file(s)`);
}

function checkFiniteHorizonResponseTransferTheory() {
  const methodsFile = path.join(SRC, "methods_theory.md");
  const supplementFile = path.join(SRC, "supp_note3_propagation.md");
  const required = [
    [methodsFile, /Proposition 2 \(finite-horizon response transfer\)/i, "formal response-transfer proposition"],
    [methodsFile, /spectral matrix norm/i, "spectral-norm assumption"],
    [methodsFile, /integer horizon \$H\\geq 1\$/i, "positive integer horizon"],
    [methodsFile, /0\\leq r\\leq H/, "true/reconstructed power bound"],
    [methodsFile, /same shock-normalization map \$S\$/i, "common shock map"],
    [methodsFile, /H\(H\+1\)/, "finite-horizon accumulation factor"],
    [methodsFile, /does not establish a CP rank, CP-ALS global convergence or lower error/i, "non-convergence/non-gain boundary"],
    [supplementFile, /Proof of Proposition 2: finite-horizon response transfer/i, "proof heading"],
    [supplementFile, /spectral matrix norm/i, "proof norm assumption"],
    [supplementFile, /R_h\(W\)=J\\mathcal\{C\}\(W\)\^hJ'S/, "response-to-companion relation"],
    [supplementFile, /sum_\{k=1\}\^\{p\}\\\|\\Delta M_k\(W\)\\\|_2\^2/, "spectral block-row bound"],
    [supplementFile, /maximum of the true and reconstructed power bounds over all three companion families/i, "three-topology common-K rule"],
    [supplementFile, /does not prove CP-ALS convergence, rank selection or a gain over local estimation/i, "proof boundary"],
  ];
  for (const [file, regex, label] of required) {
    if (!fs.existsSync(file) || !regex.test(readText(file))) {
      errors.push(`Finite-horizon response-transfer theory is missing ${label} in ${rel(file)}`);
    }
  }
  const unsupported = /projection inequality concerns the best rank-R|deterministic projection and finite-horizon perturbation|Proposition 1 formalizes the operating regime|sufficient for low-rank reconstruction to stabilize|low-rank reconstruction stabilizes the operator path|compatible induced, hence submultiplicative matrix norm/i;
  for (const file of [methodsFile, path.join(SRC, "supp_note2_estimator.md"), supplementFile]) {
    if (fs.existsSync(file) && unsupported.test(readText(file))) {
      errors.push(`Unsupported CP-recovery theory wording found in ${rel(file)}`);
    }
  }
  if (/\bC_hat\b/.test(readText(supplementFile))) {
    errors.push("Finite-horizon response-transfer proof retains plain-text C_hat notation");
  }
  passes.push(`Finite-horizon response-transfer theory check covered ${required.length} proof/boundary elements`);
}

function checkJointRidgeAndResponseNotation() {
  const methodsFile = path.join(SRC, "methods_theory.md");
  const estimatorFile = path.join(SRC, "methods_estimator.md");
  const supplementFile = path.join(SRC, "supp_note3_propagation.md");
  const required = [
    [methodsFile, /all network-exposure lag blocks jointly/i, "joint network-lag design"],
    [methodsFile, /Small values imply high worst-case sensitivity/i, "weak-direction interpretation"],
    [methodsFile, /Penalized numerical uniqueness is separate/i, "penalized/unpenalized separation"],
    [methodsFile, /spectral condition number is infinite for a rank-deficient residualized network design/i, "degenerate condition-number convention"],
    [estimatorFile, /joint matrix containing all \$p\$ network-exposure lag blocks/i, "implemented joint diagnostic description"],
    [supplementFile, /M_\{X,\\lambda\}=I-X\(X'X\+\\lambda I\)\^\{-1\}X'/i, "ridge residual-maker definition"],
    [supplementFile, /Z'M_\{X,\\lambda\}Z\+\\lambda I/i, "ridge Schur complement"],
    [supplementFile, /not the ordinary FWL projection/i, "ridge/FWL distinction"],
    [supplementFile, /penalized uniqueness is not evidence of unpenalized design identification/i, "identification boundary"],
    [supplementFile, /exactly the same lag-specific preprocessed topology matrices supplied to the estimator/i, "diagnostic-estimator topology identity"],
    [supplementFile, /integers \$n\\geq1\$ and \$m\\geq1\$/i, "nondegenerate FWL dimensions"],
    [supplementFile, /\\Phi_h\(t,W\)=J\\mathcal\{C\}_t\(W\)\^hJ'/, "moving-average notation"],
    [supplementFile, /R_h\(t,W\)=\\Phi_h\(t,W\)S_t/, "normalized-response notation"],
    [supplementFile, /\\delta=10\^\{-12\}/, "GIRF normalization floor"],
    [supplementFile, /\\epsilon=10\^\{-10\}>0/, "positive ratio floor"],
  ];
  for (const [file, regex, label] of required) {
    if (!fs.existsSync(file) || !regex.test(readText(file))) {
      errors.push(`Joint-ridge/response-notation theory is missing ${label} in ${rel(file)}`);
    }
  }
  const obsolete = /Fix one equation, one rolling window and one lag block|With a ridge penalty applied to the residualized network block|depends mainly on penalty|\\Psi_h\(W\)=J\\mathcal\{C\}\(W\)\^hJ'S|\\Psi[^\n]{0,120}\\Sigma_t e_j/i;
  for (const file of [methodsFile, estimatorFile, supplementFile]) {
    if (fs.existsSync(file) && obsolete.test(readText(file))) {
      errors.push(`Obsolete per-lag, residualized-ridge or response-notation wording found in ${rel(file)}`);
    }
  }
  passes.push(`Joint-ridge/response-notation check covered ${required.length} proof and implementation elements`);
}

function firstIndexOfAny(text, patterns) {
  const lower = text.toLowerCase();
  let first = -1;
  for (const pattern of patterns) {
    const index = lower.indexOf(pattern.toLowerCase());
    if (index === -1) continue;
    if (first === -1 || index < first) first = index;
  }
  return first;
}

function requireAnchorBeforeTerms(file, anchorPatterns, laterTerms, label) {
  if (!fs.existsSync(file)) return;
  const text = readText(file);
  const anchorIndex = firstIndexOfAny(text, anchorPatterns);
  if (anchorIndex === -1) {
    errors.push(`${label} does not foreground query preservation, endpoint preservation or the topology-switchable operator`);
    return;
  }
  for (const [term, termLabel] of laterTerms) {
    const termIndex = firstIndexOfAny(text, [term]);
    if (termIndex !== -1 && termIndex < anchorIndex) {
      errors.push(`${label} mentions ${termLabel} before the query-preservation/operator anchor`);
    }
  }
  passes.push(`${label} keeps the query-preservation/operator anchor before CP/RCEP/application terms`);
}

function checkFirstScreenPositioning() {
  const metadataFile = path.join(SRC, "metadata.json");
  if (fs.existsSync(metadataFile)) {
    const metadata = JSON.parse(readText(metadataFile));
    const title = String(metadata.title || "");
    if (!/topology-(?:dependent|indexed) responses?/i.test(title)) {
      errors.push("Title does not foreground the topology-indexed response question");
    }
    if (title.length > 75) {
      errors.push(`Title exceeds the 75-character Nature-style target: ${title.length} characters`);
    }
    if (/\b(rcep|trade|tariff|canonical polyadic|cp tensor|tensor decomposition)\b/i.test(title)) {
      errors.push("Title foregrounds application or implementation terms before the computational object");
    } else {
      passes.push(`Title foregrounds the response question, avoids implementation-first framing and is ${title.length} characters`);
    }
  }

  const anchors = [
    "topology-dependent response",
    "topology-indexed response",
    "query preservation",
    "endpoint preservation",
    "topology-switchable response operator",
    "topology-indexed operator",
    "m_{k,t}(w)=a_{k,t}+b_{k,t}w",
  ];
  const laterTerms = [
    ["canonical polyadic", "canonical polyadic implementation"],
    ["cp-network", "CP-network implementation"],
    ["cp tensor", "CP/tensor implementation"],
    ["rcep", "RCEP application"],
    ["trade network", "trade application"],
  ];

  requireAnchorBeforeTerms(path.join(SRC, "abstract.md"), anchors, laterTerms, "Abstract first screen");
  const abstractFile = path.join(SRC, "abstract.md");
  if (fs.existsSync(abstractFile)) {
    const abstractWords = wordCount(readText(abstractFile));
    if (abstractWords > 150) {
      errors.push(`Abstract exceeds 150-word Article target after math stripping: ${abstractWords} words`);
    } else if (abstractWords < 120) {
      errors.push(`Abstract is too short to carry context, approach, result and implication: ${abstractWords} words`);
    } else {
      passes.push(`Abstract length remains within the 120-150-word Article target (${abstractWords} words after math stripping)`);
    }
  }
  requireAnchorBeforeTerms(path.join(SRC, "cover_letter.md"), anchors, laterTerms, "Cover letter first screen");
  requireAnchorBeforeTerms(path.join(SUBMISSION_MATERIALS, "cover_letter_natcs.md"), anchors, laterTerms, "Generated cover letter first screen");
}

function checkReaderFacingReproducibilityLanguage() {
  const files = [
    "abstract.md",
    "methods_data.md",
    "methods_estimator.md",
    "methods_uncertainty.md",
    "supp_note7_repro.md",
    "data_availability.md",
    "code_availability.md",
    "cover_letter.md",
  ];
  const forbidden = [
    [/\breviewer(?:-facing)?\b/i, "reviewer-facing"],
    [/\bpeer-review package\b/i, "peer-review package"],
    [/\breviewer archive\b|\bseparate archive\b/i, "internal archive"],
    [/\bmanifest\.json\b/i, "manifest.json"],
    [/\braw-to-derived\b/i, "raw-to-derived workflow"],
    [/\bhelper checkouts?\b/i, "helper checkout"],
    [/\bdefault reviewer path\b|\bfast reviewer path\b/i, "internal reviewer path"],
    [/\bderived evidence objects?\b/i, "derived evidence objects"],
    [/NATCS_CP_NBOOT|reproduce\/reproduce_(?:evidence|manuscript)\.sh/i, "internal execution command"],
  ];

  let checked = 0;
  for (const name of files) {
    const file = path.join(SRC, name);
    if (!requireFile(file, `reader-facing source ${name}`)) continue;
    const content = readText(file);
    for (const [pattern, label] of forbidden) {
      if (pattern.test(content)) {
        errors.push(`Reader-facing source ${name} contains internal packaging language: ${label}`);
      }
    }
    checked += 1;
  }
  passes.push(`Reader-facing internal-packaging language gate checked ${checked} file(s)`);
}

function requireRepresentationPositioning(file, label, requirements) {
  if (!fs.existsSync(file)) {
    errors.push(`Missing representation-positioning file for ${label}: ${rel(file)}`);
    return;
  }
  const text = readText(file);
  for (const [pattern, patternLabel] of requirements) {
    if (!pattern.test(text)) {
      errors.push(`${label} is missing representation-level positioning signal: ${patternLabel}`);
    }
  }
  passes.push(`${label} preserves representation-level query-preservation positioning`);
}

function checkRepresentationLevelPositioning() {
  const sharedRequirements = [
    [/\brepresentation-level\b/i, "representation-level"],
    [/query preservation|query-preservation/i, "query preservation"],
  ];

  const fittedObjectRequirements = [
    ...sharedRequirements,
    [/fitted object|fitted representation/i, "fitted object or fitted representation"],
    [/topology-substitution/i, "topology-substitution"],
  ];

  requireRepresentationPositioning(
    path.join(SRC, "cover_letter.md"),
    "Cover letter NCS-fit paragraph",
    [
      [/\brepresentation-level contribution\b/i, "representation-level contribution"],
      [/fitted representation/i, "fitted representation"],
      [/topology-substitution readouts remain available/i, "topology-substitution readouts remain available"],
      [/supplied topology argument/i, "supplied topology argument"],
    ],
  );
  requireRepresentationPositioning(
    path.join(SUBMISSION_MATERIALS, "cover_letter_natcs.md"),
    "Generated cover letter NCS-fit paragraph",
    [
      [/\brepresentation-level contribution\b/i, "representation-level contribution"],
      [/fitted representation/i, "fitted representation"],
      [/topology-substitution readouts remain available/i, "topology-substitution readouts remain available"],
      [/supplied topology argument/i, "supplied topology argument"],
    ],
  );
  requireRepresentationPositioning(
    path.join(SRC, "ncs_portal_field_kit.md"),
    "Portal field kit Why-NCS wording",
    fittedObjectRequirements,
  );
  requireRepresentationPositioning(
    path.join(SRC, "ncs_editorial_triage_response_pack.md"),
    "Editorial triage Why-NCS wording",
    [
      ...fittedObjectRequirements,
      [/topology-switchable response operator/i, "topology-switchable response operator"],
      [/supplied topology argument/i, "supplied topology argument"],
    ],
  );
  requireRepresentationPositioning(
    path.join(SRC, "ncs_reviewer_recheck_matrix.md"),
    "Reviewer recheck senior-editor wording",
    [
      ...fittedObjectRequirements,
      [/supplied topology argument/i, "supplied topology argument"],
      [/transferable computational target/i, "transferable computational target"],
    ],
  );
  requireRepresentationPositioning(
    path.join(SRC, "natcs_final_author_decision_sheet.md"),
    "Final author decision sheet positioning guardrail",
    fittedObjectRequirements,
  );
  requireRepresentationPositioning(
    path.join(SRC, "natcs_coauthor_action_request.md"),
    "Coauthor action request positioning guardrail",
    sharedRequirements,
  );
  requireRepresentationPositioning(
    path.join(SRC, "submission_checklist.md"),
    "Submission checklist positioning guardrail",
    sharedRequirements,
  );
}

function collectPortalPasteableSnippets() {
  const file = path.join(SRC, "ncs_portal_field_kit.md");
  if (!fs.existsSync(file)) return [];
  const lines = readText(file).split(/\r?\n/);
  const snippets = [];
  let section = "";
  let shortSummary = [];
  for (const line of lines) {
    if (line.startsWith("## ")) {
      if (section === "Short Editorial Summary" && shortSummary.length > 0) {
        snippets.push({
          label: "Portal short editorial summary",
          text: shortSummary.join("\n").trim(),
          anchorRequired: true,
        });
        shortSummary = [];
      }
      section = line.replace(/^##\s+/, "").trim();
      continue;
    }

    if (section === "One-Line Fields" && line.startsWith("|") && !/^\|\s*-+/.test(line)) {
      const cells = markdownTableCells(line);
      if (cells.length >= 3 && cells[0] !== "Portal field") {
        snippets.push({
          label: `Portal one-line ${cells[0]}`,
          text: cells[1],
          anchorRequired: cells[0] === "Novelty",
        });
      }
    }

    if (section === "Length-Limited Variants" && line.startsWith("|") && !/^\|\s*-+/.test(line)) {
      const cells = markdownTableCells(line);
      if (cells.length >= 4 && cells[0] !== "Portal field") {
        snippets.push({
          label: `Portal 150-character ${cells[0]}`,
          text: cells[1],
          anchorRequired: cells[0] === "Novelty",
        });
        snippets.push({
          label: `Portal 300-character ${cells[0]}`,
          text: cells[2],
          anchorRequired: cells[0] === "Novelty",
        });
      }
    }

    if (section === "Short Editorial Summary" && line.trim() && !line.startsWith("Tags:")) {
      shortSummary.push(line);
    }

    if (section === "Field-Specific Variants" && line.startsWith("|") && !/^\|\s*-+/.test(line)) {
      const cells = markdownTableCells(line);
      if (cells.length >= 3 && cells[0] !== "If the portal asks for...") {
        snippets.push({
          label: `Portal field-specific ${cells[0]}`,
          text: cells[1],
          anchorRequired: ["Why NCS?", "Main contribution"].includes(cells[0]),
        });
      }
    }
  }
  if (section === "Short Editorial Summary" && shortSummary.length > 0) {
    snippets.push({
      label: "Portal short editorial summary",
      text: shortSummary.join("\n").trim(),
      anchorRequired: true,
    });
  }
  return snippets;
}

function collectTriagePasteableSnippets() {
  const file = path.join(SRC, "ncs_editorial_triage_response_pack.md");
  if (!fs.existsSync(file)) return [];
  const lines = readText(file).split(/\r?\n/);
  const snippets = [];
  let section = "";
  let captureWhyNcsQuote = false;
  let whyNcsQuote = [];

  const flushWhyNcsQuote = () => {
    if (whyNcsQuote.length === 0) return;
    snippets.push({
      label: "Triage Why NCS suggested wording",
      text: whyNcsQuote.join("\n").replace(/^>\s?/gm, "").trim(),
      anchorRequired: true,
    });
    whyNcsQuote = [];
  };

  for (const line of lines) {
    if (line.startsWith("## ")) {
      if (captureWhyNcsQuote) flushWhyNcsQuote();
      section = line.replace(/^##\s+/, "").trim();
      captureWhyNcsQuote = false;
      continue;
    }

    if (section === "Portal-Field Snippets" && line.startsWith("|") && !/^\|\s*-+/.test(line)) {
      const cells = markdownTableCells(line);
      if (cells.length >= 2 && cells[0] !== "Field type") {
        snippets.push({
          label: `Triage portal ${cells[0]}`,
          text: cells[1],
          anchorRequired: cells[0] === "One-sentence significance",
        });
      }
    }

    if (section === "If An Editor Asks \"Why NCS?\"" && /^Suggested wording:\s*$/.test(line.trim())) {
      captureWhyNcsQuote = true;
      continue;
    }

    if (captureWhyNcsQuote) {
      if (line.startsWith(">")) whyNcsQuote.push(line);
      else if (line.startsWith("## ")) {
        flushWhyNcsQuote();
        captureWhyNcsQuote = false;
      }
    }
  }
  if (captureWhyNcsQuote) flushWhyNcsQuote();
  return snippets;
}

function collectReviewerResponseSnippets() {
  const file = path.join(SRC, "ncs_reviewer_recheck_matrix.md");
  if (!fs.existsSync(file)) return [];
  const lines = readText(file).split(/\r?\n/);
  const snippets = [];
  let inKeySnippets = false;
  let currentLabel = "";
  let currentLines = [];

  const flush = () => {
    if (!currentLabel || currentLines.length === 0) return;
    snippets.push({
      label: `Reviewer response ${currentLabel}`,
      text: currentLines.join("\n").trim(),
      anchorRequired: /senior editor/i.test(currentLabel),
    });
    currentLabel = "";
    currentLines = [];
  };

  for (const line of lines) {
    if (line.startsWith("## ")) {
      flush();
      inKeySnippets = line.trim() === "## 5. Key Replacement Snippets";
      continue;
    }
    if (!inKeySnippets) continue;
    if (line.startsWith("### ")) {
      flush();
      currentLabel = line.replace(/^###\s+/, "").trim();
      continue;
    }
    if (!currentLabel) continue;
    if (/^Tags:\s*/.test(line.trim())) {
      flush();
      continue;
    }
    if (line.trim() && !line.startsWith("Use these only")) {
      currentLines.push(line);
    }
  }
  flush();
  return snippets;
}

function checkPasteableSnippetWording(snippets, label) {
  const forbidden = [
    [/all raw data/gi, "all raw data"],
    [/all data are publicly available/gi, "all data are publicly available"],
    [/fully reproducible from raw/gi, "fully reproducible from raw"],
    [/raw data and code are publicly available/gi, "raw data and code are publicly available"],
    [/doi and licen[cs]e are already assigned/gi, "DOI and licence are already assigned"],
    [/zenodo doi/gi, "Zenodo DOI"],
    [/placeholder doi/gi, "placeholder DOI"],
    [/expected doi/gi, "expected DOI"],
    [/rcep caused/gi, "RCEP caused"],
    [/causal rcep/gi, "causal RCEP"],
    [/causal policy effects?/gi, "causal policy effect"],
    [/policy effects/gi, "policy effects"],
    [/policy effect\b/gi, "policy effect"],
    [/broadly generalizes/gi, "broadly generalizes"],
    [/outperforms temporal gnns/gi, "outperforms temporal GNNs"],
    [/state-of-the-art temporal gnn/gi, "state-of-the-art temporal GNN"],
  ];
  const anchors = [
    "query preservation",
    "endpoint preservation",
    "endpoint-preservation",
    "endpoint-preserving",
    "topology-switchable response operator",
    "topology-indexed operator",
    "topology-substitution response queries",
    "representation problem",
    "supplied topology argument",
    "m_{k,t}(w)=a_{k,t}+b_{k,t}w",
  ];
  const laterTerms = [
    ["canonical polyadic", "canonical polyadic implementation"],
    ["cp-network", "CP-network implementation"],
    ["cp tensor", "CP/tensor implementation"],
    ["rcep", "RCEP application"],
    ["trade network", "trade application"],
  ];
  const discouraged = /\b(rather than|since|however|therefore|not only|not\s+[^.\n]{0,80}\s+but)\b/gi;
  const formulaSensitive = /(?:M_\{k,t\}|A_\{k,t\}|B_\{k,t\}|\$[^$]+\$|`[^`]*(?:M_\{k,t\}|A_\{k,t\}|B_\{k,t\})[^`]*`)/i;

  for (const snippet of snippets) {
    for (const [regex, label] of forbidden) {
      regex.lastIndex = 0;
      if (regex.test(snippet.text)) {
        errors.push(`Forbidden portal claim "${label}" found in ${snippet.label}`);
      }
    }
    const discouragedCount = countMatches(snippet.text, discouraged);
    if (discouragedCount > 0) {
      errors.push(`Discouraged transition pattern found in ${snippet.label}: ${discouragedCount}`);
    }
    if (formulaSensitive.test(snippet.text)) {
      errors.push(`Formula-sensitive notation found in paste-ready portal wording: ${snippet.label}`);
    }
    if (!snippet.anchorRequired) continue;
    const anchorIndex = firstIndexOfAny(snippet.text, anchors);
    if (anchorIndex === -1) {
      errors.push(`${snippet.label} does not foreground query preservation, endpoint preservation or the topology-switchable operator`);
      continue;
    }
    for (const [term, termLabel] of laterTerms) {
      const termIndex = firstIndexOfAny(snippet.text, [term]);
      if (termIndex !== -1 && termIndex < anchorIndex) {
        errors.push(`${snippet.label} mentions ${termLabel} before the query-preservation/operator anchor`);
      }
    }
  }
  passes.push(`${label} pasteable wording boundary check covered ${snippets.length} snippet(s)`);
}

function checkPortalPasteableWording() {
  checkPasteableSnippetWording(collectPortalPasteableSnippets(), "Portal");
}

function checkSupportPasteableWording() {
  const snippets = [
    ...collectTriagePasteableSnippets(),
    ...collectReviewerResponseSnippets(),
  ];
  checkPasteableSnippetWording(snippets, "Support");
}

function checkExternalGates() {
  const gateFiles = [
    [path.join(SRC, "natcs_final_author_decision_sheet.md"), /Needs action/g, "final author decision sheet has open action rows"],
    [path.join(SRC, "ncs_fig2_portal_preview_checklist.md"), /Not checked|Unresolved/g, "Fig. 2 portal checklist is not externally closed"],
    [path.join(SRC, "raw_source_access_decision_worksheet.md"), /Unresolved|TODO/g, "raw-source worksheet still awaits author sign-off"],
    [path.join(SRC, "public_release_readiness_worksheet.md"), /Unresolved|TODO/g, "public-release worksheet still awaits author sign-off"],
  ];
  for (const [file, regex, label] of gateFiles) {
    if (!fs.existsSync(file)) continue;
    const count = countMatches(readText(file), regex);
    if (count > 0) {
      warnings.push(`${label}: ${count} marker(s)`);
    } else {
      passes.push(`${label} has no open markers`);
    }
  }
}

function checkSubmissionPackageNavigation() {
  const navigationFiles = [
    [
      path.join(SUBMISSION, "README.md"),
      "Submission-package README",
      [
        [/Submission-Day Stop\/Go Triage/, "Submission-Day Stop/Go Triage"],
        [/Post-Confirmation Update Checklist/, "Post-Confirmation Update Checklist"],
        [/03_submission_materials\/natcs_final_author_decision_sheet\.md/, "final author decision sheet path"],
      ],
    ],
    [
      path.join(SUBMISSION_MATERIALS, "submission_materials_notes.md"),
      "Submission-materials notes",
      [
        [/Submission-Day Stop\/Go Triage/, "Submission-Day Stop/Go Triage"],
        [/Post-Confirmation Update Checklist/, "Post-Confirmation Update Checklist"],
        [/natcs_final_author_decision_sheet\.md/, "final author decision sheet filename"],
      ],
    ],
  ];

  for (const [file, label, requirements] of navigationFiles) {
    if (!requireFile(file, label)) continue;
    const text = readText(file);
    for (const [regex, phrase] of requirements) {
      if (!regex.test(text)) {
        errors.push(`${label} is missing upload-entry routing phrase: ${phrase}`);
      }
    }
    passes.push(`${label} Stop/Go navigation check covered ${requirements.length} phrase(s)`);
  }
}

function checkFinalAuthorClosureChecklist() {
  const checklistFiles = [
    [path.join(SRC, "natcs_final_author_decision_sheet.md"), "source final author decision sheet"],
    [path.join(SUBMISSION_MATERIALS, "natcs_final_author_decision_sheet.md"), "generated final author decision sheet"],
  ];
  const requirements = [
    [/Post-Confirmation Update Checklist/, "post-confirmation update checklist"],
    [/Fig\. 2 portal preview passes/, "Fig. 2 pass branch"],
    [/Fig\. 2 portal preview fails/, "Fig. 2 fail branch"],
    [/Raw-source defaults are signed off/, "raw-source conservative sign-off branch"],
    [/raw-source blocks gain confirmed reviewer or public access/, "raw-source strengthened-access branch"],
    [/Public repository, DOI, licence and access terms are assigned/, "public-release assigned-record branch"],
    [/Portal fields, title, abstract, cover letter or formal availability text are edited/, "portal/formal-text edit branch"],
    [/Rebuild .*final gates/i, "rebuild and final-gate rerun instruction"],
  ];

  for (const [file, label] of checklistFiles) {
    if (!requireFile(file, label)) continue;
    const text = readText(file);
    for (const [regex, phrase] of requirements) {
      if (!regex.test(text)) {
        errors.push(`${label} is missing post-confirmation branch: ${phrase}`);
      }
    }
    passes.push(`${label} post-confirmation checklist check covered ${requirements.length} phrase(s)`);
  }
}

function checkEditorialTriageBrief() {
  const file = path.join(SUBMISSION_MATERIALS, "scope_assessment_brief.md");
  if (!requireFile(file, "generated editorial triage brief")) return;
  const text = readText(file);
  const requirements = [
    [/# Editorial Triage Brief/, "Editorial Triage Brief heading"],
    [/## One-sentence fit/, "one-sentence fit section"],
    [/query preservation/i, "query-preservation anchor"],
    [/topology-switchable finite-horizon operator/i, "topology-switchable operator anchor"],
    [/representation-level query preservation/i, "representation-level novelty wording"],
    [/CP is the implementation layer/i, "CP implementation-layer boundary"],
    [/## Evidence that supports review/, "evidence section"],
    [/## Boundaries that should guide editorial interpretation/, "boundary section"],
    [/No causal tariff-policy claim/i, "RCEP causality boundary"],
    [/No exhaustive temporal-GNN forecasting benchmark claim/i, "temporal-GNN boundary"],
    [/## Reviewer package/, "reviewer package section"],
  ];
  for (const [regex, phrase] of requirements) {
    if (!regex.test(text)) {
      errors.push(`Editorial triage brief is missing first-screen phrase: ${phrase}`);
    }
  }
  const discouraged = /\b(rather than|instead of|since|however|therefore|not only|not\s+[^.\n]{0,80}\s+but)\b/i;
  if (discouraged.test(text)) {
    errors.push("Editorial triage brief contains discouraged defensive transition wording");
  }
  passes.push(`Editorial triage brief first-screen check covered ${requirements.length} phrase(s)`);
}

function checkMainFigure3RecoveryScope() {
  const mainFigureBuilder = path.join(ROOT, "scripts", "build_natcs_evidence.mjs");
  const validationResults = path.join(SRC, "results_validation.md");
  const mainManuscriptBuilder = path.join(ROOT, "scripts", "build_natcs_manuscript.mjs");
  const supplementaryComparators = path.join(SRC, "supp_note4_benchmarks.md");
  const figureSvg = path.join(ROOT, "output", "natcs_assets", "figure3_natcs_supported_regime.svg");
  const checks = [
    [mainFigureBuilder, /Projection boundary: graph-feature rows/i, "main Fig. 3 projection footer"],
    [validationResults, /The final benchmark evaluates projection-based graph-feature stress tests/i, "main Results graph-feature numerical comparison"],
    [mainManuscriptBuilder, /Tucker and projected graph-feature rows are interpreted/i, "main Fig. 3 graph-feature caption comparison"],
  ];

  for (const [file, forbidden, label] of checks) {
    if (!requireFile(file, label)) continue;
    if (forbidden.test(readText(file))) {
      errors.push(`Main Fig. 3 scope regression: ${label} has returned`);
    }
  }

  if (requireFile(validationResults, "main Results validation source")) {
    const text = readText(validationResults);
    if (!/Projected graph-feature diagnostics.*Supplementary Note 4.*not used as a main-text ranking/i.test(text)) {
      errors.push("Main Results no longer directs projected graph-feature diagnostics to Supplementary Note 4");
    }
  }
  if (requireFile(supplementaryComparators, "Supplementary comparator documentation")) {
    if (!/Projected graph-feature stress tests/i.test(readText(supplementaryComparators))) {
      errors.push("Supplementary Note 4 no longer retains projected graph-feature diagnostics");
    }
  }
  if (fs.existsSync(figureSvg) && /graph-feature/i.test(readText(figureSvg))) {
    errors.push("Generated main Fig. 3 SVG contains a graph-feature comparison");
  }
  if (requireFile(mainManuscriptBuilder, "main manuscript builder")) {
    const text = readText(mainManuscriptBuilder);
    if (!/CP\/local\/Tucker\/low-rank N=50 scale rows use \$\{context\.scale_replications_n50\}-replication bounded stress coverage/i.test(text)) {
      errors.push("Main Fig. 3 no longer limits four-replication N=50 coverage to non-graph scale rows");
    }
    if (/N=50 is a \$\{context\.scale_replications_n50\}-replication bounded stress row/.test(text)) {
      errors.push("Main Fig. 3 implies every N=50 comparator has four replications");
    }
  }
  passes.push("Main Fig. 3 recovery-scope gate checked main/supplementary comparator separation");
}

function checkFig2PortalPreviewDisabled() {
  const checklistPath = path.join(SRC, "ncs_fig2_portal_preview_checklist.md");
  if (!requireFile(checklistPath, "Fig. 2 portal-preview checklist")) return;
  const checklist = readText(checklistPath);
  if (!/Figure 2 Portal Preview Checklist \(Disabled\)/i.test(checklist)) {
    errors.push("Fig. 2 portal-preview checklist is not explicitly disabled");
  }
  if (/Current local PDF page:/i.test(checklist)) {
    errors.push("Disabled Fig. 2 portal-preview checklist retains a stale PDF page reference");
  }
  if (!/no portal action is authorised/i.test(checklist)) {
    errors.push("Disabled Fig. 2 portal-preview checklist lacks the no-action boundary");
  }
  passes.push("Fig. 2 portal-preview gate verified disabled source-only status without stale page evidence");
}

function checkMainFigure3QualificationScope() {
  const manuscriptBuilder = path.join(ROOT, "scripts", "build_natcs_manuscript.mjs");
  const validationResults = path.join(SRC, "results_validation.md");
  const abstract = path.join(SRC, "abstract.md");
  const discussion = path.join(SRC, "discussion.md");
  const coverLetter = path.join(SRC, "cover_letter.md");
  const uncertaintyMethods = path.join(SRC, "methods_uncertainty.md");
  const supplementaryBenchmarks = path.join(SRC, "supp_note4_benchmarks.md");
  const gateRecord = path.join(SRC, "r006c_endpoint_gate.json");
  const headlineFiles = [
    [manuscriptBuilder, "Fig. 3 caption template"],
    [validationResults, "controlled Results validation source"],
    [abstract, "Abstract source"],
    [discussion, "Discussion source"],
    [coverLetter, "cover-letter source"],
  ];
  const exactCountPattern = /(?:CP[^.\n]{0,80})?(?:0|none) of 16|Tucker[^.\n]{0,80}6 of 16|0 of 8 native/i;
  for (const [file, label] of headlineFiles) {
    if (requireFile(file, label) && exactCountPattern.test(readText(file))) {
      errors.push(`${label} promotes the held-out qualification counts into the headline narrative`);
    }
  }
  if (requireFile(validationResults, "controlled Results claim-inheritance boundary") && !/separate endpoint-aware qualification[\s\S]*?is not used to extend these gains beyond the matched controlled design/i.test(readText(validationResults))) {
    errors.push("Controlled Results no longer retain the concise held-out claim-inheritance boundary");
  }
  if (requireFile(uncertaintyMethods, "Methods qualification boundary")) {
    const methodsText = readText(uncertaintyMethods);
    if (/CP passed 0 of 16 cells|Tucker passed 6 of 16|0 of 8 native cells/i.test(methodsText)) {
      errors.push("Methods promotes exact held-out qualification counts into the main manuscript");
    }
    if (!/complete cell counts and promotion decision are reported in Supplementary Note 4[\s\S]*?recovery claim remains confined to the original matched controlled design/i.test(methodsText)) {
      errors.push("Methods no longer retain the supplementary qualification pointer and matched-design boundary");
    }
  }
  if (requireFile(supplementaryBenchmarks, "Supplementary qualification table") && !/CP anchor split, rank 3 \| 0\/16[\s\S]*?Tucker anchor split, rank \(3,3,3\) \| 6\/16[\s\S]*?0\/8/i.test(readText(supplementaryBenchmarks))) {
    errors.push("Supplementary Note 4 no longer reports the complete held-out qualification table");
  }
  if (requireFile(gateRecord, "frozen endpoint-aware gate record")) {
    const gate = JSON.parse(readText(gateRecord));
    if (gate.candidates?.cp?.passed_cells !== 0 || gate.candidates?.tucker?.passed_cells !== 6 || gate.candidates?.tucker?.passed_native_cells !== 0) {
      errors.push("Frozen endpoint-aware gate counts have changed from the Fig. 3 qualification");
    }
  }
  passes.push("Main Fig. 3 qualification gate kept exact counts in SI, preserved the main-text boundary and checked the frozen record");
}

function checkEmpiricalResultsNumericAlignment() {
  const rcepResults = path.join(SRC, "results_rcep.md");
  const generalityResults = path.join(SRC, "results_generality.md");
  const abstract = path.join(SRC, "abstract.md");
  const validationResults = path.join(SRC, "results_validation.md");
  const generatedMainTex = path.join(SUBMISSION, "01_main_manuscript", "main_manuscript.tex");
  const requirements = [
    [rcepResults, /point-series mean difference is \{\{rcep_pre_point_difference\}\} before 2022 Q1 and \{\{rcep_post_point_difference\}\} afterward/i, "RCEP point-series period templates"],
    [rcepResults, /Bootstrap median differences average \{\{rcep_pre_bootstrap_difference\}\} and \{\{rcep_post_bootstrap_difference\}\}/i, "RCEP bootstrap period templates"],
    [rcepResults, /mean 0\.0023 and median 0\.0011/i, "RCEP topology-perturbation summary"],
    [generalityResults, /Mean aggregate propagation is \{\{nyc_mean_gnet\}\} and mean frozen-topology propagation is \{\{nyc_mean_frozen_gnet\}\}, giving a mean observed-minus-frozen difference of \{\{nyc_mean_topology_difference_4\}\}/i, "NYC aggregate template"],
    [generalityResults, /Figure 4c reports point-path shares, while bootstrap-draw means and medians under the same explicit-channel estimand are reported in Supplementary Table 5/i, "NYC GIRF supplementary boundary"],
    [abstract, /effective-operator error by \{\{operator_gain_n15\}\}% and \{\{operator_gain_n30\}\}%[\s\S]*?unit-shock response error by \{\{response_gain_n15\}\}% and \{\{response_gain_n30\}\}%/i, "abstract controlled-gain templates"],
    [validationResults, /finite-horizon unit-shock response error decreased by \{\{response_gain_n15\}\}% and \{\{response_gain_n30\}\}%/i, "Results response-gain templates"],
  ];
  const staleValues = [
    [rcepResults, /mean 0\.006 and median 0\.004/i, "superseded RCEP topology-perturbation values"],
    [generalityResults, /Mean aggregate propagation is 0\.545/i, "superseded NYC aggregate level"],
  ];

  for (const [file, requirement, label] of requirements) {
    if (requireFile(file, label) && !requirement.test(readText(file))) {
      errors.push(`Empirical Results numeric alignment failed: ${label}`);
    }
  }
  for (const [file, stale, label] of staleValues) {
    if (requireFile(file, label) && stale.test(readText(file))) {
      errors.push(`Empirical Results retains ${label}`);
    }
  }
  if (requireFile(generatedMainTex, "generated main manuscript")) {
    const generated = readText(generatedMainTex);
    if (!/Mean aggregate propagation is 0\.274[\s\S]*?Figure\s+4c\s+reports\s+point-path\s+shares,[\s\S]*?Supplementary\s+Table\s+5/i.test(generated)) {
      errors.push("Generated main manuscript does not contain the evidence-aligned NYC aggregate summary and supplementary GIRF boundary");
    }
    if (!/effective-operator\s+error\s+by\s+93\.6-96\.8\\%[\s\S]*?GIRF\s+error\s+by\s+82\.5-87\.3\\%/i.test(generated) || /82\.4-87\.4\\%/.test(generated)) {
      errors.push("Generated main manuscript does not use exact-value rounding for replicated GIRF gains");
    }
  }
  passes.push("Empirical Results numeric-alignment gate checked RCEP and NYC source summaries");
}

function checkEvidenceAuditTraceability() {
  const summaryPath = path.join(ROOT, "output", "natcs_evidence", "summary_metrics.json");
  const readerSummaryPath = path.join(ROOT, "output", "natcs_evidence", "reader_facing_summary_metrics.json");
  if (!requireFile(summaryPath, "machine-readable evidence summary") || !requireFile(readerSummaryPath, "reader-facing evidence summary")) return;
  const summary = JSON.parse(readText(summaryPath));
  const reader = JSON.parse(readText(readerSummaryPath));
  const aggregate = summary.rcep_aggregate_readout || {};
  const localStress = summary.synthetic_benchmark?.local_rolling_topology_stress_replications || {};
  const nyc = summary.nyc_validation || {};
  const readerAggregate = reader.rcep_application?.aggregate_readout || {};
  const readerNyc = reader.nyc_taxi_validation || {};
  const requiredNumbers = [
    aggregate.pre_2022?.point_mean_observed_minus_frozen,
    aggregate.post_2022?.point_mean_observed_minus_frozen,
    aggregate.pre_2022?.bootstrap_median_difference_mean,
    aggregate.post_2022?.bootstrap_median_difference_mean,
    nyc.ridge_lambda,
    nyc.rank_validation?.available_origins,
    localStress.min,
    localStress.max,
  ];
  if (aggregate.horizon !== 8 || aggregate.pre_2022?.date_count !== 24 || aggregate.post_2022?.date_count !== 12) {
    errors.push("RCEP aggregate evidence no longer records the H=8 period boundary and coverage");
  }
  if (!requiredNumbers.every((value) => Number.isFinite(Number(value)))) {
    errors.push("Empirical evidence summary is missing an auditable RCEP, NYC or local-stress field");
  }
  if (Number(localStress.min) !== 3 || Number(localStress.max) !== 3) {
    errors.push("Local-rolling topology-stress replication coverage no longer records three-replication anchors");
  }
  if (Number(nyc.ridge_lambda) !== 0.01 || Number(nyc.rank_validation?.available_origins) !== 69) {
    errors.push("NYC selection evidence no longer records the submitted ridge and rank-validation coverage");
  }
  if (readerAggregate.pre_2022?.date_count !== 24 || Number(reader.nyc_taxi_validation?.ridge_lambda) !== 0.01) {
    errors.push("Reader-facing evidence summary no longer exposes RCEP aggregate or NYC selection traceability");
  }
  if (nyc.network_share_estimand !== "absolute_explicit_channel_share" || readerNyc.network_share_estimand !== "absolute_explicit_channel_share") {
    errors.push("NYC evidence summaries no longer identify the canonical explicit-channel share estimand");
  }
  passes.push("Evidence-audit traceability gate checked RCEP aggregate, NYC selection and local-stress coverage");
}

function checkIntroductionContributionScope() {
  const introduction = path.join(SRC, "introduction.md");
  const generatedMainTex = path.join(SUBMISSION, "01_main_manuscript", "main_manuscript.tex");
  const requirements = [
    ["Endpoint availability must be verified at the fitted-object level", "specification-level endpoint-availability boundary"],
    ["separate four requirements for a topology-dependent response: the endpoint must be defined by the fitted object, identified by the design, numerically recoverable and stable over the reported horizon", "four-layer endpoint distinction"],
    ["The contribution is a testable representation criterion, not a claim that every defined endpoint is statistically recoverable", "testable representation-criterion contribution"],
    ["GVAR formulations can use time-varying trade weights and support scenario and impulse-response analysis", "verified GVAR precedent acknowledgement"],
  ];

  for (const [file, label] of [
    [introduction, "Introduction contribution source"],
    [generatedMainTex, "generated Introduction contribution"],
  ]) {
    if (!requireFile(file, label)) continue;
    const text = readText(file).replace(/\s+/g, " ");
    for (const [phrase, requirement] of requirements) {
      if (!text.includes(phrase)) {
        errors.push(`${label} is missing ${requirement}`);
      }
    }
  }
  passes.push("Introduction contribution-scope gate checked reconstruction criterion and boundary");
}

function checkDocxFormula() {
  const coverDocx = path.join(LATEST_UPLOAD_DIR, "cover_letter_natcs.docx");
  if (!fs.existsSync(coverDocx)) {
    errors.push(`Missing cover letter DOCX for formula extraction: ${rel(coverDocx)}`);
    return;
  }
  const result = spawnSync("pandoc", [coverDocx, "-t", "plain", "--wrap=none"], { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) {
    warnings.push(`Could not extract cover letter DOCX with pandoc: ${(result.stderr || result.stdout || "").trim()}`);
    return;
  }
  if (!result.stdout.includes("M_{k,t}(W)=A_{k,t}+B_{k,t}W")) {
    errors.push("Cover letter DOCX extraction does not retain M_{k,t}(W)=A_{k,t}+B_{k,t}W");
    return;
  }
  passes.push("Cover letter DOCX retains plain-text operator formula");
}

function checkUploadMainAbstractPlainText() {
  const sourceAbstract = path.join(SRC, "abstract.md");
  if (fs.existsSync(sourceAbstract) && /\$[^$]+\$|\$\$/.test(readText(sourceAbstract))) {
    errors.push("Source abstract contains TeX math that may be dropped by upload/DOCX plain-text previews");
  }

  const mainDocx = path.join(LATEST_UPLOAD_DIR, "main_manuscript.docx");
  if (!fs.existsSync(mainDocx)) {
    errors.push(`Missing main manuscript DOCX for abstract extraction: ${rel(mainDocx)}`);
    return;
  }
  const plain = pandocPlainFromDocx(mainDocx, "main manuscript abstract");
  if (plain === null) return;
  const normalizedPlain = normalizePlainText(plain);
  const keywordDelimitedAbstract = /(?:^|\n)Abstract\n\n([\s\S]*?)\n\nKeywords:/m.exec(normalizedPlain);
  const abstract = keywordDelimitedAbstract
    ? normalizePlainText(keywordDelimitedAbstract[1])
    : extractPlainSection(plain, "Abstract", "Introduction");
  if (!abstract) {
    errors.push("Could not locate Abstract section in main manuscript DOCX plain-text extraction");
    return;
  }

  for (const phrase of EXPECTED_UPLOAD_ABSTRACT_PHRASES) {
    if (!abstract.includes(phrase)) {
      errors.push(`Upload main-manuscript abstract is missing first-screen phrase: ${phrase}`);
    }
  }
  if (/operator,\s*\./i.test(abstract)) {
    errors.push("Upload main-manuscript abstract contains an operator formula dropout pattern");
  }
  const abstractWords = wordCount(abstract);
  if (abstractWords > 150) {
    errors.push(`Upload main-manuscript abstract exceeds 150-word Article target after extraction: ${abstractWords} words`);
  }
  passes.push(`Upload main-manuscript abstract plain-text check covered ${EXPECTED_UPLOAD_ABSTRACT_PHRASES.length} phrase(s)`);
}

function checkArchives() {
  if (fs.existsSync(LATEST_UPLOAD_ZIP)) {
    run("unzip", ["-t", LATEST_UPLOAD_ZIP], "latest word-only upload zip integrity");
  }
  const latestStamped = latestStampedSubmissionUploadZip();
  if (latestStamped) {
    run("unzip", ["-t", latestStamped], `latest stamped submission upload zip integrity (${path.basename(latestStamped)})`);
  } else {
    warnings.push("No stamped submission upload zip found");
  }
  if (fs.existsSync(FIGURE_ZIP)) {
    run("unzip", ["-t", FIGURE_ZIP], "main figure-source zip integrity");
  }
  if (fs.existsSync(REVIEWER_ARCHIVE_ZIP)) {
    run("unzip", ["-t", REVIEWER_ARCHIVE_ZIP], "latest reviewer archive zip integrity");
  }
}

function checkResidualWarningsAllowlist() {
  const unexpected = warnings.filter((warning) => !ALLOWED_FINAL_WARNING_PATTERNS.some((pattern) => pattern.test(warning)));
  if (unexpected.length > 0) {
    errors.push(`Unexpected final-gate warning(s): ${unexpected.join(" | ")}`);
    return;
  }
  passes.push(`Residual warning allowlist check covered ${warnings.length} warning(s)`);
}

function main() {
  checkEmpiricalImplementationAudit();
  if (process.argv.includes("--only-empirical-implementation-audit")) {
    const summary = {
      status: errors.length ? "FAIL" : "PASS",
      errors,
      warnings,
      passes: passes.length,
    };
    console.log(JSON.stringify(summary, null, 2));
    if (errors.length) process.exit(1);
    return;
  }

  checkPaperClaimAudit();
  if (errors.length) {
    const summary = {
      status: "BLOCKED",
      errors,
      warnings,
      passes: passes.length,
    };
    console.log(JSON.stringify(summary, null, 2));
    process.exit(1);
  }

  checkActiveBuildLocality();
  checkReleaseSafetyAudit();
  checkRequiredFiles();
  checkCopiedSupportSync();
  checkGeneratedFormalTextSync();
  checkInventory();
  checkFreezeManifest();
  checkFormalOverclaims();
  checkPreservationWordingPrecision();
  checkCollapsedEndpointIdentifiabilityBoundary();
  checkFiniteHorizonResponseTransferTheory();
  checkJointRidgeAndResponseNotation();
  checkFirstScreenPositioning();
  checkReaderFacingReproducibilityLanguage();
  checkRepresentationLevelPositioning();
  checkPortalPasteableWording();
  checkSupportPasteableWording();
  checkExternalGates();
  checkSubmissionPackageNavigation();
  checkFinalAuthorClosureChecklist();
  checkEditorialTriageBrief();
  checkMainFigure3RecoveryScope();
  checkFig2PortalPreviewDisabled();
  checkMainFigure3QualificationScope();
  checkEmpiricalResultsNumericAlignment();
  checkEvidenceAuditTraceability();
  checkIntroductionContributionScope();
  checkDocxFormula();
  checkUploadMainAbstractPlainText();
  checkUploadFormalDocxSync();
  checkWordOnlyUploadContents();
  checkFigureSourcePackageContents();
  checkFigureSourceEditability();
  checkReviewerArchiveEntrypoints();
  checkReviewerArchiveZipContents();
  checkEvidenceMapAliasConsistency();
  checkReaderFacingEvidenceSummary();
  checkPortalFieldLengthLimits();
  checkArchives();
  checkResidualWarningsAllowlist();

  const summary = {
    status: errors.length ? "FAIL" : "PASS_WITH_WARNINGS_ALLOWED",
    errors,
    warnings,
    passes: passes.length,
  };

  console.log(JSON.stringify(summary, null, 2));
  if (errors.length) process.exit(1);
}

main();
