import fs from "fs";
import path from "path";
import crypto from "crypto";
import { spawnSync } from "child_process";
import { requireReleaseableNatcsEvidence } from "./natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT_ROOT = path.join(ROOT, "output", "figure_source_package");
const PACKAGE_DIR = path.join(OUT_ROOT, "natcs_main_figure_sources");
const FIG_DIR = path.join(PACKAGE_DIR, "figures");
const NOTES_DIR = path.join(PACKAGE_DIR, "notes");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyFile(src, dest) {
  if (!fs.existsSync(src)) {
    throw new Error(`Missing required figure source: ${src}`);
  }
  ensureDir(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function rel(file) {
  return path.relative(PACKAGE_DIR, file).replaceAll(path.sep, "/");
}

function writeText(file, text) {
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, text);
}

function zipDir(srcDir, zipFile) {
  if (fs.existsSync(zipFile)) fs.unlinkSync(zipFile);
  const result = spawnSync("zip", ["-r", zipFile, path.basename(srcDir)], {
    cwd: path.dirname(srcDir),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || result.stdout || "zip failed");
  }
}

function main() {
  // Fail closed while the controlling audits are blocked: this produces a
  // submission-facing artifact package.
  requireReleaseableNatcsEvidence(ROOT);
  fs.rmSync(PACKAGE_DIR, { recursive: true, force: true });
  ensureDir(FIG_DIR);
  ensureDir(NOTES_DIR);

  const figures = [
    {
      id: "figure_1",
      title: "Callable topology-indexed operator",
      manuscriptRole: "Defines the learned object and its three same-path topology readouts.",
      serves: "novelty / clarity / visual communication",
      files: [
        ["output/natcs_assets/figure1_natcs_framework.pdf", "figures/figure1_callable_operator.pdf"],
        ["output/natcs_assets/figure1_natcs_framework.png", "figures/figure1_callable_operator.png"],
        ["output/natcs_assets/figure1_natcs_framework.svg", "figures/figure1_callable_operator.svg"],
      ],
    },
    {
      id: "figure_2",
      title: "Query factorization certificate",
      manuscriptRole: "Pairs the exact unrestricted boundary with the constructive diagonal inverse and endpoint classification.",
      serves: "novelty / rigour / clarity / visual communication",
      files: [
        ["output/natcs_assets/figure2_natcs_query_certificate.pdf", "figures/figure2_query_certificate.pdf"],
        ["output/natcs_assets/figure2_natcs_query_certificate.png", "figures/figure2_query_certificate.png"],
        ["output/natcs_assets/figure2_natcs_query_certificate.svg", "figures/figure2_query_certificate.svg"],
      ],
    },
    {
      id: "figure_3",
      title: "Supported controlled operating regime",
      manuscriptRole: "Shows released controlled recovery first and the strict native qualification as a bounded inset.",
      serves: "significance / rigour / clarity / reproducibility / visual communication",
      files: [
        ["output/natcs_assets/figure3_natcs_supported_regime.pdf", "figures/figure3_supported_regime.pdf"],
        ["output/natcs_assets/figure3_natcs_supported_regime.png", "figures/figure3_supported_regime.png"],
        ["output/natcs_assets/figure3_natcs_supported_regime.svg", "figures/figure3_supported_regime.svg"],
      ],
    },
  ];

  const manifest = {
    package: "natcs_main_figure_sources",
    purpose: "Standalone main-figure source bundle for submission preview, editor checks and reviewer zoom inspection.",
    boundary: "This package contains generated figure exports and QA notes. It does not replace the manuscript, Supplementary Information or reviewer reproducibility archive.",
    generatedAt: new Date().toISOString(),
    figures: [],
    notes: [],
  };

  for (const figure of figures) {
    const entry = {
      id: figure.id,
      title: figure.title,
      manuscriptRole: figure.manuscriptRole,
      serves: figure.serves,
      files: [],
    };
    for (const [srcRel, destRel] of figure.files) {
      const src = path.join(ROOT, srcRel);
      const dest = path.join(PACKAGE_DIR, destRel);
      copyFile(src, dest);
      entry.files.push({
        path: destRel,
        sha256: sha256(dest),
        bytes: fs.statSync(dest).size,
      });
    }
    manifest.figures.push(entry);
  }

  const notes = [
    ["manuscript_src/natcs/ncs_figure_qa_memo.md", "ncs_figure_qa_memo.md", "Current visual-sequence QA memo."],
    ["manuscript_src/natcs/ncs_fig2_redesign_contract.md", "ncs_fig2_redesign_contract.md", "Figure 2 scientific and visual contract."],
    ["manuscript_src/natcs/ncs_figure1_python_redesign_qa_20260726.md", "ncs_figure1_python_redesign_qa_20260726.md", "Figure 1 Python export and visual QA."],
    ["manuscript_src/natcs/ncs_figure2_python_redesign_qa_20260726.md", "ncs_figure2_python_redesign_qa_20260726.md", "Figure 2 Python export and visual QA."],
    ["manuscript_src/natcs/ncs_figure3_python_redesign_qa_20260726.md", "ncs_figure3_python_redesign_qa_20260726.md", "Figure 3 Python export and visual QA."],
    ["paper_rewriting_output/ncs_figure_sequence_contract_20260726.md", "ncs_figure_sequence_contract_20260726.md", "Active Figure 1-3 narrative contract."],
  ];
  for (const [sourceRelative, destinationName, role] of notes) {
    const source = path.join(ROOT, sourceRelative);
    const destination = path.join(NOTES_DIR, destinationName);
    copyFile(source, destination);
    manifest.notes.push({
      path: rel(destination),
      role,
      sha256: sha256(destination),
      bytes: fs.statSync(destination).size,
    });
  }

  const readme = [
    "# NatCS Main Figure Source Package",
    "",
    "This source definition collects the generated exports for the three active main manuscript figures.",
    "",
    "Use it to inspect standalone figure quality during submission preview or peer review.",
    "",
    "The visual sequence is capability (Figure 1), exact certificate (Figure 2) and supported controlled regime (Figure 3). Each figure is supplied as editable SVG/PDF plus a 600 dpi PNG.",
    "",
    "RCEP, NYC and E3 outcome figures are excluded because they are not active manuscript evidence under the controlling audits.",
    "",
    "Included files are generated artifacts, not hand-edited illustrator files. Regeneration is controlled by Python source and the manuscript build entry point.",
    "",
  ].join("\n");
  writeText(path.join(PACKAGE_DIR, "README.md"), readme);
  writeText(path.join(PACKAGE_DIR, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);

  const latestZip = path.join(OUT_ROOT, "latest_natcs_main_figure_sources.zip");
  const stampedZip = path.join(OUT_ROOT, `natcs_main_figure_sources_${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}.zip`);
  zipDir(PACKAGE_DIR, stampedZip);
  if (fs.existsSync(latestZip)) fs.unlinkSync(latestZip);
  fs.copyFileSync(stampedZip, latestZip);

  console.log(JSON.stringify({
    packageDir: path.relative(ROOT, PACKAGE_DIR),
    zip: path.relative(ROOT, stampedZip),
    latestZip: path.relative(ROOT, latestZip),
  }, null, 2));
}

main();
