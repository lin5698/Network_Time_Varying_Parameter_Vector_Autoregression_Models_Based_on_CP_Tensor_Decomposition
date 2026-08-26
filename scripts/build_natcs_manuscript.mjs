import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";
// The Supplementary Information document is composed exclusively by the
// source-only builder below. The historical empirical supplement composition
// (RCEP/NYC tables, stability/clipping diagnostics, application figures,
// Notes 5-7) was demoted on 2026-07-26 to
// scripts/_archives/legacy_empirical_supplement_builder_20260726.mjs and must
// not be re-imported here while the controlling audits remain non-releaseable.
import { buildSourceOnlySupplementaryMarkdown } from "./build_natcs_supplementary_source_only.mjs";
import { assertReaderFacingTextClean, ensureDir, markdownTable, readCsv, readJson, readText, readerFacingSubmissionText, referencesBlock, renderTemplate, requireReleaseableNatcsEvidence, runCommand, writeText, yamlHeader } from "./natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SRC = path.join(ROOT, "manuscript_src", "natcs");
const TMP = path.join(ROOT, "tmp", "manuscript_build", "natcs");
const LATEX_BUILD = path.join(ROOT, "tmp", "latex_build");
const PDF_RENDER = path.join(ROOT, "tmp", "pdfs");
const SUBMISSION_PACKAGE = path.join(ROOT, "output", "submission_package", "natcs_current");
const FRAMEWORK_BASENAME = path.join(ROOT, "output", "natcs_assets", "figure1_natcs_framework");
const QUERY_CERTIFICATE_BASENAME = path.join(ROOT, "output", "natcs_assets", "figure2_natcs_query_certificate");
const SUPPORTED_REGIME_BASENAME = path.join(ROOT, "output", "natcs_assets", "figure3_natcs_supported_regime");
const END_MATTER_FILES = [
  ["data_availability", "data_availability.txt"],
  ["code_availability", "code_availability.txt"],
  ["author_contributions", "author_contributions.txt"],
  ["competing_interests", "competing_interests.txt"],
  ["ethics_statement", "ethics_statement.txt"],
  ["ai_use_statement", "ai_use_statement.txt"],
];

function loadMetadata() {
  return readJson(path.join(SRC, "metadata.json"));
}

function loadSection(name, context) {
  return readerFacingSubmissionText(renderTemplate(readText(path.join(SRC, `${name}.md`)).trim(), context));
}

function splitLeadParagraph(text) {
  const paragraphs = String(text || "").trim().split(/\n\s*\n/);
  if (paragraphs.length <= 1) return [String(text || "").trim(), ""];
  return [paragraphs[0].trim(), paragraphs.slice(1).join("\n\n").trim()];
}

export function computeControlledContext(meta = {}) {
  const summaryPath = path.join(ROOT, "output", "natcs_benchmarks", "benchmark_summary.csv");
  const rows = readCsv(summaryPath);
  const rowFor = (scenario, method) => {
    const matches = rows.filter((row) => row.scenario === scenario && row.method === method);
    if (matches.length !== 1) {
      throw new Error(`Controlled benchmark requires exactly one ${scenario}/${method} summary row; found ${matches.length}`);
    }
    return matches[0];
  };
  const numberField = (row, field) => {
    const value = Number(row[field]);
    if (!Number.isFinite(value)) {
      throw new Error(`Controlled benchmark field ${row.scenario}/${row.method}/${field} is not finite`);
    }
    return value;
  };
  const replicationCount = (scenario) => {
    const local = numberField(rowFor(scenario, "local_network"), "replications");
    const cp = numberField(rowFor(scenario, "cp_network"), "replications");
    if (!Number.isInteger(local) || local < 1 || local !== cp) {
      throw new Error(`Controlled benchmark replication contract is unmatched for ${scenario}: local=${local}, CP=${cp}`);
    }
    return local;
  };
  const reduction = (scenario, field) => {
    const local = numberField(rowFor(scenario, "local_network"), field);
    const cp = numberField(rowFor(scenario, "cp_network"), field);
    if (local <= 0 || cp <= 0) {
      throw new Error(`Controlled benchmark recovery values must be positive for ${scenario}/${field}`);
    }
    return 100 * (local - cp) / local;
  };

  const operatorGains = ["scale_n15", "scale_n30"].map((scenario) => reduction(scenario, "coef_error_median"));
  const responseGains = ["scale_n15", "scale_n30"].map((scenario) => reduction(scenario, "girf_error_median"));
  return {
    title: meta.title || "Query-certified operator learning for evolving weighted networks",
    operator_gain_n15: operatorGains[0].toFixed(1),
    operator_gain_n30: operatorGains[1].toFixed(1),
    response_gain_n15: responseGains[0].toFixed(1),
    response_gain_n30: responseGains[1].toFixed(1),
    baseline_coef_gain_replicated_range: operatorGains.map((value) => value.toFixed(1)).join("-"),
    baseline_girf_gain_replicated_range: responseGains.map((value) => value.toFixed(1)).join("-"),
    scale_replications_n15: replicationCount("scale_n15"),
    scale_replications_n30: replicationCount("scale_n30"),
    scale_replications_n50: replicationCount("scale_n50"),
  };
}

function buildMainBenchmarkTable(context) {
  return objectsToMarkdown(
    [
      {
        "Endpoint": "Primary replicated recovery (N=15/N=30)",
        "Primary evidence": `${context.baseline_coef_gain_replicated_range}% lower operator error; ${context.baseline_girf_gain_replicated_range}% lower response error`,
        "Scope flag": "Headline benchmark evidence",
      },
      {
        "Endpoint": "Ablation: switchable readouts unavailable",
        "Primary evidence": "Collapsed CP keeps total-map and total-response outputs only; network and frozen-topology readouts are outside target",
        "Scope flag": "Endpoint-preservation ablation",
      },
      {
        "Endpoint": "Coverage boundary",
        "Primary evidence": `N=15 and N=30 rows use ${context.scale_replications_n15} and ${context.scale_replications_n30} replications; CP/local/Tucker/collapsed/low-rank N=50 rows use ${context.scale_replications_n50} replications, while sparse and graph-feature diagnostics use one`,
        "Scope flag": "Headline claim anchored to replicated rows",
      },
    ],
    ["Endpoint", "Primary evidence", "Scope flag"]
  );
}

function objectsToMarkdown(rows, headers) {
  return markdownTable(headers, rows.map((row) => headers.map((key) => row[key] ?? "")));
}

function ensureFrameworkFigure() {
  removeFiles([
    `${FRAMEWORK_BASENAME}.svg`,
    `${FRAMEWORK_BASENAME}.pdf`,
    `${FRAMEWORK_BASENAME}.png`,
  ]);
  runCommand("python3", ["scripts/build_natcs_framework_figure.py"], { cwd: ROOT });
  return {
    svg: `${FRAMEWORK_BASENAME}.svg`,
    pdf: `${FRAMEWORK_BASENAME}.pdf`,
    png: `${FRAMEWORK_BASENAME}.png`,
  };
}

function ensureQueryCertificateFigure() {
  removeFiles([
    `${QUERY_CERTIFICATE_BASENAME}.svg`,
    `${QUERY_CERTIFICATE_BASENAME}.pdf`,
    `${QUERY_CERTIFICATE_BASENAME}.png`,
  ]);
  runCommand("python3", ["scripts/build_natcs_query_certificate_figure.py"], { cwd: ROOT });
  return {
    svg: `${QUERY_CERTIFICATE_BASENAME}.svg`,
    pdf: `${QUERY_CERTIFICATE_BASENAME}.pdf`,
    png: `${QUERY_CERTIFICATE_BASENAME}.png`,
  };
}

function ensureSupportedRegimeFigure() {
  removeFiles([
    `${SUPPORTED_REGIME_BASENAME}.svg`,
    `${SUPPORTED_REGIME_BASENAME}.pdf`,
    `${SUPPORTED_REGIME_BASENAME}.png`,
  ]);
  runCommand("python3", ["scripts/build_natcs_supported_regime_figure.py"], { cwd: ROOT });
  return {
    svg: `${SUPPORTED_REGIME_BASENAME}.svg`,
    pdf: `${SUPPORTED_REGIME_BASENAME}.pdf`,
    png: `${SUPPORTED_REGIME_BASENAME}.png`,
  };
}

function writeEndMatterFiles(context, outDir) {
  const written = {};
  for (const [name, filename] of END_MATTER_FILES) {
    const text = `${loadSection(name, context)}\n`;
    const target = path.join(outDir, filename);
    writeText(target, text);
    written[name] = target;
  }
  return written;
}

function cleanupLegacyMarkdownFiles() {
  for (const filename of ["main.md", "supplementary.md"]) {
    const target = path.join(TMP, filename);
    if (fs.existsSync(target)) fs.unlinkSync(target);
  }
}

function removeFileIfPresent(file) {
  if (fs.existsSync(file) && !fs.lstatSync(file).isDirectory()) {
    fs.rmSync(file, { force: true });
  }
}

function removeFiles(files) {
  for (const file of files) removeFileIfPresent(file);
}

function removeDocxSiblingOutputs(targetFile) {
  const dir = path.dirname(targetFile);
  const ext = path.extname(targetFile);
  const stem = path.basename(targetFile, ext);
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir)) {
    if (entry === `${stem}${ext}` || new RegExp(`^${stem.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")} [0-9]+${ext.replace(".", "\\.")}$`).test(entry)) {
      fs.unlinkSync(path.join(dir, entry));
    }
  }
}

function buildMainMarkdown(meta, context, evidence, assetFormat = "vector") {
  const frameworkFigure = assetFormat === "vector" ? evidence.framework_figure_pdf : evidence.framework_figure_png;
  const frameworkFigureWidth = assetFormat === "vector" ? "92%" : "6.8in";
  const queryCertificateFigure = assetFormat === "vector" ? evidence.query_certificate_figure_pdf : evidence.query_certificate_figure_png;
  const queryCertificateFigureWidth = assetFormat === "vector" ? "94%" : "6.8in";
  const supportedRegimeFigure = assetFormat === "vector" ? evidence.supported_regime_figure_pdf : evidence.supported_regime_figure_png;
  const supportedRegimeFigureWidth = assetFormat === "vector" ? "95%" : "6.8in";
  const affiliations = `${meta.affiliations.map((line) => `*${line}*`).join("  \n")}  \n`;
  const abstract = loadSection("abstract", context);
  const introduction = loadSection("introduction", context);
  const resultsFramework = loadSection("results_framework", context);
  const [resultsFrameworkLead, resultsFrameworkBody] = splitLeadParagraph(resultsFramework);
  const resultsValidation = loadSection("results_validation", context);
  const [resultsValidationLead, resultsValidationBody] = splitLeadParagraph(resultsValidation);
  const discussion = loadSection("discussion", context);
  const methodsData = loadSection("methods_data", context);
  const methodsEstimator = loadSection("methods_estimator", context);
  const methodsTheory = loadSection("methods_theory", context);
  const methodsPropagation = loadSection("methods_propagation", context);
  const methodsUncertainty = loadSection("methods_uncertainty", context);
  const dataAvailability = loadSection("data_availability", context);
  const codeAvailability = loadSection("code_availability", context);
  const acknowledgements = loadSection("acknowledgements", context);
  const authorContributions = loadSection("author_contributions", context);
  const competingInterests = loadSection("competing_interests", context);
  const ethicsStatement = loadSection("ethics_statement", context);
  const aiUseStatement = loadSection("ai_use_statement", context);
  const refs = referencesBlock([
    introduction,
    resultsFramework,
    resultsValidation,
    discussion,
    methodsData,
    methodsEstimator,
    methodsTheory,
    methodsPropagation,
    methodsUncertainty,
    dataAvailability,
    codeAvailability,
    acknowledgements,
    authorContributions,
    competingInterests,
    ethicsStatement,
    aiUseStatement,
  ]);

  const mainBenchmarkTable = buildMainBenchmarkTable(context);
  const visibleTitleBlock = [];

  return readerFacingSubmissionText([
    yamlHeader(meta, { singleLineAuthors: assetFormat === "raster", srcDir: SRC }),
    ...visibleTitleBlock,
    affiliations,
    `*${meta.correspondence}*  `,
    `*${meta.funding}*`,
    "",
    "# Abstract {-}",
    "",
    abstract,
    "",
    `**Keywords:** ${(meta.keywords || []).join("; ")}`,
    "",
    "# Introduction {-}",
    "",
    introduction,
    "",
    "# Results",
    "",
    "## Query certificates define callable topology responses",
    "",
    resultsFrameworkLead,
    "",
    "$$",
    "y_{\\tau} = c_t + \\sum_{k=1}^{p} A_{k,t} y_{\\tau-k} + \\sum_{k=1}^{p} B_{k,t} W_{\\tau-k} y_{\\tau-k} + C_t x_{\\tau} + \\varepsilon_{\\tau}, \\quad \\tau \\in \\mathcal{I}_t",
    "$$",
    "",
    "This rolling equation uses lag-specific historical exposure matrices. Response evaluation is separate: for target date $t$, the last matrix available inside the window, $\\bar W_t=W_{t-1}$, is held fixed through the horizon. Reconstruction must keep the direct and network blocks separately evaluable, or provide an identified inverse to those blocks, for topology to remain a readout argument. This representation condition defines the query; design identification, numerical recovery and finite-horizon stability are evaluated separately.",
    "",
    "![Figure 1 | One learned coefficient path remains callable under supplied topologies. a, The fitted object retains direct and network-mediated blocks while topology remains an argument supplied at readout. b, Observed, direct-only and frozen-topology responses use the same fitted state, shock normalization and horizon; changing topology does not refit the model. c, A collapsed total map without a declared inverse does not expose a genuine topology-substitution response.](" + path.relative(ROOT, frameworkFigure) + "){ width=" + frameworkFigureWidth + " }",
    "",
    resultsFrameworkBody,
    "",
    "![Figure 2 | Query preservation is certified by factorization through the retained representation. a, For a row-separable finite-basis operator, a requested query is callable exactly when the retained kernel is contained in the query kernel, equivalently when the query factors through the retained object. The criterion applies to the one-hop (I,W) and two-hop (I,W,W2) bases; strict family inclusion holds on every declared topology domain containing the directed-cycle fixture P. This is a representation result, not two-hop recovery evidence. b, For unrestricted one-hop blocks and W1 distinct from W0, the pairs (A,B)=(0,0) and (-W0,I) share the retained map D=0 at W0 but return 0 and W1-W0 at W1, so no single evaluator exists. c, For diagonal A and B with zero-diagonal W0, the displayed rowwise inverse recovers the separated coefficients when each exposure row is nonzero; the full condition additionally requires every zero row of W0 to remain zero in W1. d, Endpoint availability is assigned before error comparison. Separated CP and Tucker define the declared total, network-component and frozen-topology responses, whereas the evaluated collapsed and no-network controls retain total responses only; grey dashes denote outside-target readouts, not zero error.](" + path.relative(ROOT, queryCertificateFigure) + "){ width=" + queryCertificateFigureWidth + " }",
    "",
    "## Structured reconstruction preserves response queries in a controlled regime",
    "",
    resultsValidationLead,
    "",
    "*Table 1 | Endpoint-preservation benchmark matrix. The table separates the response endpoint tested, the manuscript-facing evidence and the comparison scope. Replication counts, full comparator diagnostics and bounded-stress rows are reported in Supplementary Tables 1b-3.*",
    "",
    mainBenchmarkTable,
    "",
    resultsValidationBody,
    "",
    `![Figure 3 | Target-matched reconstruction improves controlled operator and response recovery. a, Across ${context.scale_replications_n15} and ${context.scale_replications_n30} replications at N=15 and N=30, respectively, CP reconstruction reduced median effective-operator error by ${context.operator_gain_n15}% and ${context.operator_gain_n30}% relative to unrestricted local rolling. b, Median finite-horizon unit-shock response error decreased by ${context.response_gain_n15}% and ${context.response_gain_n30}% under the same comparison. Response error uses the common 0.95 spectral-norm stabilization rule; unscaled instability is reported separately. Points show medians and intervals show interquartile ranges; axes are logarithmic and lower values indicate better recovery. c, Both methods return the same declared operator and finite-horizon response endpoint, and both primary scales use 20 matched replications. Stress rows and the separate held-out qualification are reported in Supplementary Note 4.](${path.relative(ROOT, supportedRegimeFigure)}){ width=${supportedRegimeFigureWidth} }`,
    "",
    "\\FloatBarrier",
    "",
    "# Discussion",
    "",
    discussion,
    "",
    "# Methods",
    "",
    "## Controlled benchmark design",
    "",
    methodsData,
    "",
    "## Estimator",
    "",
    methodsEstimator,
    "",
    "## Query definition, representation sufficiency and response stability",
    "",
    methodsTheory,
    "",
    "## Propagation objects",
    "",
    methodsPropagation,
    "",
    "## Uncertainty and stability",
    "",
    methodsUncertainty,
    "",
    "## AI use",
    "",
    aiUseStatement,
    "",
    "# Data availability",
    "",
    dataAvailability,
    "",
    "# Code availability",
    "",
    codeAvailability,
    "",
    "# Acknowledgements",
    "",
    acknowledgements,
    "",
    "# Author contributions",
    "",
    authorContributions,
    "",
    "# Competing interests",
    "",
    competingInterests,
    "",
    "# Ethics statement",
    "",
    ethicsStatement,
    "",
    ...refs,
  ].join("\n"));
}

function buildPandoc(markdownFile, outFile, meta) {
  if (!fs.existsSync(markdownFile)) {
    throw new Error(`Pandoc input is missing before conversion: ${path.relative(ROOT, markdownFile)}`);
  }
  assertPandocInputsLocal(markdownFile, outFile, meta);
  ensureDir(path.dirname(outFile));
  const args = [
    markdownFile,
    "--standalone",
    "--from",
    "markdown+tex_math_dollars+pipe_tables+raw_tex",
    "--citeproc",
    "--number-sections",
    "--to",
    outFile.endsWith(".tex") ? "latex" : "docx",
    "--output",
    outFile,
    "--resource-path",
    ROOT,
  ];
  if (outFile.endsWith(".docx") && meta.reference_docx) {
    const referenceDocx = path.join(ROOT, meta.reference_docx);
    if (fs.existsSync(referenceDocx)) {
      args.push("--reference-doc", referenceDocx);
    }
  }
  runCommand("pandoc", args, { cwd: ROOT });
}

function markdownResourcePaths(markdownFile) {
  const text = readText(markdownFile);
  const resources = new Set();
  for (const match of text.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)) {
    const resource = match[1].trim();
    if (!resource || /^[a-z]+:/i.test(resource) || resource.startsWith("#")) continue;
    resources.add(path.isAbsolute(resource) ? resource : path.join(ROOT, resource));
  }
  return [...resources];
}

function macFileFlags(file) {
  const result = spawnSync("stat", ["-f", "%Sf", file], { cwd: ROOT, encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim() : "";
}

function isDatalessFile(file) {
  return macFileFlags(file).split(",").includes("dataless");
}

function uniqueFiles(files) {
  return [...new Set(files.filter(Boolean).map((file) => path.resolve(file)))];
}

function assertLocalFiles(label, files) {
  const unique = uniqueFiles(files);
  const missing = unique
    .filter((file) => !fs.existsSync(file))
    .map((file) => path.relative(ROOT, file));
  const dataless = unique
    .filter((file) => fs.existsSync(file))
    .filter((file) => isDatalessFile(file))
    .map((file) => path.relative(ROOT, file));
  if (missing.length || dataless.length) {
    const lines = [];
    if (missing.length) lines.push(`missing:\n${missing.join("\n")}`);
    if (dataless.length) lines.push(`dataless:\n${dataless.join("\n")}`);
    throw new Error(
      `${label} includes unavailable local file(s); hydrate or regenerate before continuing:\n${lines.join("\n\n")}`
    );
  }
}

function pandocDependencyPaths(markdownFile, outFile, meta) {
  const deps = [
    ...markdownResourcePaths(markdownFile),
    path.join(SRC, "references.bib"),
    path.join(SRC, "nature.csl"),
  ];
  if (outFile.endsWith(".docx") && meta.reference_docx) {
    deps.push(path.join(ROOT, meta.reference_docx));
  }
  return deps;
}

function assertPandocInputsLocal(markdownFile, outFile, meta) {
  assertLocalFiles(
    `Pandoc dependencies for ${path.relative(ROOT, markdownFile)}`,
    pandocDependencyPaths(markdownFile, outFile, meta)
  );
}

function postprocessDocx(file) {
  runCommand("python3", ["scripts/postprocess_natcs_docx.py", file], { cwd: ROOT });
  if (!fs.existsSync(file)) {
    throw new Error(`DOCX postprocess did not produce expected output: ${path.relative(ROOT, file)}`);
  }
}

function compilePdf(texFile, outPdf, buildDir) {
  ensureDir(buildDir);
  runCommand(
    "latexmk",
    ["-pdf", "-interaction=nonstopmode", "-halt-on-error", `-output-directory=${buildDir}`, path.basename(texFile)],
    { cwd: ROOT }
  );
  const builtPdf = path.join(buildDir, `${path.basename(texFile, ".tex")}.pdf`);
  copyArtifact(builtPdf, outPdf);
}

function renderPdf(pdfFile, outDir) {
  ensureDir(outDir);
  for (const entry of fs.readdirSync(outDir)) {
    if (entry.endsWith(".png")) fs.unlinkSync(path.join(outDir, entry));
  }
  runCommand("pdftoppm", ["-png", pdfFile, path.join(outDir, "page")], { cwd: ROOT });
}

function copyArtifact(src, dest) {
  assertLocalFiles(`Copy source ${path.relative(ROOT, src)}`, [src]);
  ensureDir(path.dirname(dest));
  if (fs.existsSync(dest) && !fs.lstatSync(dest).isDirectory()) {
    fs.rmSync(dest, { force: true });
  }
  fs.copyFileSync(src, dest);
}

function mergeTree(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    ensureDir(dest);
    for (const entry of fs.readdirSync(src)) {
      mergeTree(path.join(src, entry), path.join(dest, entry));
    }
    return;
  }
  copyArtifact(src, dest);
}

function normalizeNumberedSibling(dir) {
  const numbered = `${dir} 2`;
  if (!fs.existsSync(numbered)) return;
  mergeTree(numbered, dir);
  fs.rmSync(numbered, { recursive: true, force: true });
}

function normalizeNumberedSiblingsRecursive(root) {
  if (!fs.existsSync(root)) return;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    const numbered = entry.match(/^(.*) \d+$/);
    const numberedFile = entry.match(/^(.*) \d+(\.[^.]+)$/);
    if (numberedFile && fs.statSync(current).isFile()) {
      const dest = path.join(root, `${numberedFile[1]}${numberedFile[2]}`);
      if (!fs.existsSync(dest)) fs.renameSync(current, dest);
      else fs.rmSync(current, { force: true });
      continue;
    }
    if (!fs.statSync(current).isDirectory()) continue;
    if (numbered) {
      const dest = path.join(root, numbered[1]);
      mergeTree(current, dest);
      fs.rmSync(current, { recursive: true, force: true });
      normalizeNumberedSiblingsRecursive(dest);
      continue;
    }
    normalizeNumberedSiblingsRecursive(current);
  }
}

function assertSubmissionPackageClean(evidenceDir, supportingDestinations) {
  normalizeNumberedSiblingsRecursive(SUBMISSION_PACKAGE);
  normalizeNumberedSibling(evidenceDir);
  normalizeNumberedSibling(path.join(SUBMISSION_PACKAGE, "02_supporting_materials"));
  const junk = [];
  const scan = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir)) {
      const current = path.join(dir, entry);
      if (entry === ".DS_Store" || entry.includes(" 2")) {
        junk.push(path.relative(ROOT, current));
        continue;
      }
      if (fs.statSync(current).isDirectory()) scan(current);
    }
  };
  scan(SUBMISSION_PACKAGE);
  // Runtime backstop for the source-level bundle restriction: while the
  // controlling audits are non-releaseable, no blocked empirical artifact may
  // appear in the packaged evidence bundle regardless of how it got there.
  const blockedEvidencePattern = /(rcep|nyc|empirical|validation_recovery|selection_summary|summary_metrics|weak_separation|clipping|stability|girf_cp)/i;
  const blockedEvidence = [];
  const scanBlocked = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir)) {
      const current = path.join(dir, entry);
      if (blockedEvidencePattern.test(entry)) {
        blockedEvidence.push(path.relative(ROOT, current));
      }
      if (fs.statSync(current).isDirectory()) scanBlocked(current);
    }
  };
  scanBlocked(evidenceDir);
  const missing = supportingDestinations.filter((file) => !fs.existsSync(file)).map((file) => path.relative(ROOT, file));
  if (junk.length || missing.length || blockedEvidence.length) {
    const parts = [];
    if (junk.length) parts.push(`junk paths:\n${junk.join("\n")}`);
    if (missing.length) parts.push(`missing evidence paths:\n${missing.join("\n")}`);
    if (blockedEvidence.length) parts.push(`blocked evidence paths (PAPER_CLAIM_AUDIT=BLOCKED / EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL):\n${blockedEvidence.join("\n")}`);
    throw new Error(`Submission package consistency check failed:\n${parts.join("\n\n")}`);
  }
}

function buildSourceOnlySubmissionReadme(meta) {
  return [
    `# Source-only submission package | ${meta.title}`,
    "",
    "This package contains the theory-and-controlled-evidence manuscript, its five-note Supplementary Information and the frozen controlled benchmark records used by Table 1 and Figure 3.",
    "",
    "The evidence bundle is intentionally limited to the declared synthetic benchmark. It contains no application output, mixed evidence summary, empirical support document or reviewer archive.",
    "",
    "## Contents",
    "",
    "- `01_main_manuscript`: main manuscript in LaTeX, DOCX and PDF.",
    "- `02_supporting_materials`: Supplementary Information and controlled benchmark records.",
    "- `03_submission_materials`: metadata, bibliography assets, cover letter draft, end-matter text and the package inventory.",
    "",
  ].join("\n");
}

function syncSourceOnlySubmissionPackage(meta, artifacts, context) {
  fs.rmSync(SUBMISSION_PACKAGE, { recursive: true, force: true });

  const mainDir = path.join(SUBMISSION_PACKAGE, "01_main_manuscript");
  const supportingDir = path.join(SUBMISSION_PACKAGE, "02_supporting_materials");
  const evidenceDir = path.join(supportingDir, "evidence_bundle");
  const submissionDir = path.join(SUBMISSION_PACKAGE, "03_submission_materials");
  for (const dir of [mainDir, supportingDir, evidenceDir, submissionDir]) ensureDir(dir);

  const manuscriptArtifacts = [
    [artifacts.main_tex, path.join(mainDir, "main_manuscript.tex")],
    [artifacts.main_docx, path.join(mainDir, "main_manuscript.docx")],
    [artifacts.main_pdf, path.join(mainDir, "main_manuscript.pdf")],
    [artifacts.supplementary_tex, path.join(supportingDir, "supplementary_information.tex")],
    [artifacts.supplementary_docx, path.join(supportingDir, "supplementary_information.docx")],
    [artifacts.supplementary_pdf, path.join(supportingDir, "supplementary_information.pdf")],
  ];
  for (const [source, destination] of manuscriptArtifacts) copyArtifact(source, destination);

  const supportingArtifacts = [
    path.join(ROOT, "output", "natcs_evidence", "table1_simulation_benchmark.csv"),
    path.join(ROOT, "output", "natcs_evidence", "table1_simulation_benchmark.md"),
    path.join(ROOT, "output", "natcs_evidence", "table1b_baseline_tuning_projection.csv"),
    path.join(ROOT, "output", "natcs_evidence", "table1b_baseline_tuning_projection.md"),
    path.join(ROOT, "output", "natcs_evidence", "table1d_benchmark_fairness_audit.csv"),
    path.join(ROOT, "output", "natcs_evidence", "table1d_benchmark_fairness_audit.md"),
    path.join(ROOT, "output", "natcs_benchmarks", "benchmark_summary.csv"),
    path.join(ROOT, "output", "natcs_benchmarks", "benchmark_replications.csv"),
    path.join(SRC, "controlled_benchmark_contract.json"),
  ];
  assertLocalFiles("Controlled benchmark submission artifacts", supportingArtifacts);
  const supportingDestinations = supportingArtifacts.map((source) => {
    const destination = path.join(evidenceDir, path.relative(path.join(ROOT, "output"), source));
    copyArtifact(source, destination);
    return destination;
  });
  assertSubmissionPackageClean(evidenceDir, supportingDestinations);

  const metadataFile = path.join(submissionDir, "manuscript_metadata.json");
  const referencesFile = path.join(submissionDir, "references.bib");
  const cslFile = path.join(submissionDir, "nature.csl");
  const coverLetterFile = path.join(submissionDir, "cover_letter_natcs.md");
  writeText(metadataFile, `${JSON.stringify({ ...meta, reference_docx: "" }, null, 2)}\n`);
  copyArtifact(path.join(SRC, "references.bib"), referencesFile);
  copyArtifact(path.join(SRC, "nature.csl"), cslFile);
  writeText(coverLetterFile, `${loadSection("cover_letter", context)}\n`);
  const endMatterFiles = writeEndMatterFiles(context, submissionDir);

  const inventory = {
    title: meta.title,
    package_scope: "theory_and_controlled_evidence_only",
    updated_at: new Date().toISOString(),
    files: {
      main_manuscript: Object.fromEntries(manuscriptArtifacts.slice(0, 3).map(([source, destination]) => [path.extname(source).slice(1), path.relative(ROOT, destination)])),
      supplementary_information: Object.fromEntries(manuscriptArtifacts.slice(3).map(([source, destination]) => [path.extname(source).slice(1), path.relative(ROOT, destination)])),
      evidence_bundle: supportingDestinations.map((file) => path.relative(ROOT, file)),
      submission_materials: {
        metadata: path.relative(ROOT, metadataFile),
        references: path.relative(ROOT, referencesFile),
        csl: path.relative(ROOT, cslFile),
        cover_letter: path.relative(ROOT, coverLetterFile),
        ...Object.fromEntries(Object.entries(endMatterFiles).map(([name, file]) => [name, path.relative(ROOT, file)])),
      },
    },
  };
  writeText(path.join(SUBMISSION_PACKAGE, "README.md"), buildSourceOnlySubmissionReadme(meta));
  writeText(
    path.join(submissionDir, "submission_materials_notes.md"),
    "# Submission materials notes\n\nThese materials are assembled only from the active theory-and-controlled-evidence source graph.\n"
  );
  writeText(path.join(submissionDir, "submission_inventory.json"), `${JSON.stringify(inventory, null, 2)}\n`);
  assertSubmissionPackageClean(evidenceDir, supportingDestinations);

  return {
    package_root: SUBMISSION_PACKAGE,
    main_dir: mainDir,
    supporting_dir: supportingDir,
    submission_dir: submissionDir,
  };
}

export function buildNatcsManuscript() {
  requireReleaseableNatcsEvidence(ROOT);
  const meta = loadMetadata();
  const context = computeControlledContext(meta);
  const frameworkFigure = ensureFrameworkFigure();
  const queryCertificateFigure = ensureQueryCertificateFigure();
  const supportedRegimeFigure = ensureSupportedRegimeFigure();
  const evidence = {
    framework_figure_pdf: frameworkFigure.pdf,
    framework_figure_png: frameworkFigure.png,
    framework_figure_svg: frameworkFigure.svg,
    query_certificate_figure_pdf: queryCertificateFigure.pdf,
    query_certificate_figure_png: queryCertificateFigure.png,
    query_certificate_figure_svg: queryCertificateFigure.svg,
    supported_regime_figure_pdf: supportedRegimeFigure.pdf,
    supported_regime_figure_png: supportedRegimeFigure.png,
    supported_regime_figure_svg: supportedRegimeFigure.svg,
  };

  ensureDir(TMP);
  cleanupLegacyMarkdownFiles();
  const mainTexMd = path.join(TMP, "main_tex.md");
  const mainDocxMd = path.join(TMP, "main_docx.md");
  const suppTexMd = path.join(TMP, "supplementary_tex.md");
  const suppDocxMd = path.join(TMP, "supplementary_docx.md");
  const mainTexSource = buildMainMarkdown(meta, context, evidence, "vector");
  const mainDocxSource = buildMainMarkdown(meta, context, evidence, "raster");
  const suppTexSource = buildSourceOnlySupplementaryMarkdown(meta, "vector");
  const suppDocxSource = buildSourceOnlySupplementaryMarkdown(meta, "raster");
  assertReaderFacingTextClean("main_tex.md", mainTexSource);
  assertReaderFacingTextClean("main_docx.md", mainDocxSource);
  assertReaderFacingTextClean("supplementary_tex.md", suppTexSource);
  assertReaderFacingTextClean("supplementary_docx.md", suppDocxSource);
  writeText(mainTexMd, mainTexSource);
  writeText(mainDocxMd, mainDocxSource);
  writeText(suppTexMd, suppTexSource);
  writeText(suppDocxMd, suppDocxSource);

  const mainTex = path.join(ROOT, "main.tex");
  const suppTex = path.join(ROOT, "supplementary.tex");
  removeDocxSiblingOutputs(path.join(ROOT, meta.output_docx));
  removeDocxSiblingOutputs(path.join(ROOT, meta.output_supp_docx));
  buildPandoc(mainTexMd, mainTex, meta);
  buildPandoc(suppTexMd, suppTex, meta);
  buildPandoc(mainDocxMd, path.join(ROOT, meta.output_docx), meta);
  buildPandoc(suppDocxMd, path.join(ROOT, meta.output_supp_docx), meta);
  postprocessDocx(path.join(ROOT, meta.output_docx));
  postprocessDocx(path.join(ROOT, meta.output_supp_docx));

  compilePdf(mainTex, path.join(ROOT, meta.output_pdf), path.join(LATEX_BUILD, "main"));
  compilePdf(suppTex, path.join(ROOT, meta.output_supp_pdf), path.join(LATEX_BUILD, "supplementary"));

  renderPdf(path.join(ROOT, meta.output_pdf), path.join(PDF_RENDER, "natcs_main"));
  renderPdf(path.join(ROOT, meta.output_supp_pdf), path.join(PDF_RENDER, "natcs_supplementary"));

  const submissionPackage = syncSourceOnlySubmissionPackage(meta, {
    main_tex: mainTex,
    supplementary_tex: suppTex,
    main_docx: path.join(ROOT, meta.output_docx),
    main_pdf: path.join(ROOT, meta.output_pdf),
    supplementary_docx: path.join(ROOT, meta.output_supp_docx),
    supplementary_pdf: path.join(ROOT, meta.output_supp_pdf),
  }, context);

  return {
    main_markdown: mainTexMd,
    supplementary_markdown: suppTexMd,
    main_tex: mainTex,
    supplementary_tex: suppTex,
    main_docx: path.join(ROOT, meta.output_docx),
    main_pdf: path.join(ROOT, meta.output_pdf),
    supplementary_docx: path.join(ROOT, meta.output_supp_docx),
    supplementary_pdf: path.join(ROOT, meta.output_supp_pdf),
    framework_figure: frameworkFigure.pdf,
    query_certificate_figure: queryCertificateFigure.pdf,
    supported_regime_figure: supportedRegimeFigure.pdf,
    pdf_render_dir: path.join(PDF_RENDER, "natcs_main"),
    submission_package: submissionPackage.package_root,
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.log(buildNatcsManuscript());
}
