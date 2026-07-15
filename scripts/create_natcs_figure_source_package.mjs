import fs from "fs";
import path from "path";
import crypto from "crypto";
import { spawnSync } from "child_process";

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
  const surrogateResult = spawnSync("python3", ["scripts/build_natcs_fig2_portal_surrogate.py"], {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (surrogateResult.status !== 0) {
    throw new Error(surrogateResult.stderr || surrogateResult.stdout || "Fig. 2 surrogate preview build failed");
  }

  fs.rmSync(PACKAGE_DIR, { recursive: true, force: true });
  ensureDir(FIG_DIR);
  ensureDir(NOTES_DIR);

  const figures = [
    {
      id: "figure_1",
      title: "Topology-switchable evaluation operator",
      manuscriptRole: "Defines the switchable response operator and collapsed-map failure.",
      serves: "novelty / clarity / visual communication",
      files: [
        ["output/natcs_assets/figure1_natcs_framework.pdf", "figures/figure1_topology_switchable_operator.pdf"],
        ["output/natcs_assets/figure1_natcs_framework.png", "figures/figure1_topology_switchable_operator.png"],
        ["output/natcs_assets/figure1_natcs_framework.svg", "figures/figure1_topology_switchable_operator.svg"],
      ],
    },
    {
      id: "figure_2",
      title: "Endpoint-preservation benchmark",
      manuscriptRole: "Applies the endpoint gate and reports recovery, stress and stability evidence.",
      serves: "rigour / clarity / visual communication",
      files: [
        ["output/natcs_evidence/fig_validation_recovery.pdf", "figures/figure2_endpoint_preservation_benchmark.pdf"],
        ["output/natcs_evidence/fig_validation_recovery.png", "figures/figure2_endpoint_preservation_benchmark.png"],
        ["output/natcs_evidence/fig_validation_recovery.svg", "figures/figure2_endpoint_preservation_benchmark.svg"],
      ],
    },
    {
      id: "figure_3",
      title: "RCEP fixed-path topology substitution",
      manuscriptRole: "Shows the bounded empirical operator readout and estimation-path boundary.",
      serves: "significance / rigour / clarity",
      files: [
        ["output/natcs_empirical_cp/rcep/figures/fig_rcep_operator_switch.pdf", "figures/figure3_rcep_operator_readout.pdf"],
        ["output/natcs_empirical_cp/rcep/figures/fig_rcep_operator_switch.png", "figures/figure3_rcep_operator_readout.png"],
      ],
    },
    {
      id: "figure_4",
      title: "Public second-domain operator check",
      manuscriptRole: "Shows same-operator execution in the NYC Taxi mobility panel.",
      serves: "generality / reproducibility / visual communication",
      files: [
        ["output/natcs_empirical_cp/nyc_taxi/figures/fig_nyc_portability_summary.pdf", "figures/figure4_nyc_operator_check.pdf"],
        ["output/natcs_empirical_cp/nyc_taxi/figures/fig_nyc_portability_summary.png", "figures/figure4_nyc_operator_check.png"],
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

  const qaMemo = path.join(ROOT, "manuscript_src", "natcs", "ncs_figure_qa_memo.md");
  const qaDest = path.join(NOTES_DIR, "ncs_figure_qa_memo.md");
  copyFile(qaMemo, qaDest);
  manifest.notes.push({
    path: rel(qaDest),
    role: "Current main-figure QA memo and residual visual-risk audit.",
    sha256: sha256(qaDest),
    bytes: fs.statSync(qaDest).size,
  });
  const fig2Contract = path.join(ROOT, "manuscript_src", "natcs", "ncs_fig2_redesign_contract.md");
  const fig2ContractDest = path.join(NOTES_DIR, "ncs_fig2_redesign_contract.md");
  copyFile(fig2Contract, fig2ContractDest);
  manifest.notes.push({
    path: rel(fig2ContractDest),
    role: "Controlled redesign brief for Figure 2 if upload preview readability fails.",
    sha256: sha256(fig2ContractDest),
    bytes: fs.statSync(fig2ContractDest).size,
  });
  const fig2PortalChecklist = path.join(ROOT, "manuscript_src", "natcs", "ncs_fig2_portal_preview_checklist.md");
  const fig2PortalChecklistDest = path.join(NOTES_DIR, "ncs_fig2_portal_preview_checklist.md");
  copyFile(fig2PortalChecklist, fig2PortalChecklistDest);
  manifest.notes.push({
    path: rel(fig2PortalChecklistDest),
    role: "Pass/fail checklist for Figure 2 journal portal preview and standalone-source inspection.",
    sha256: sha256(fig2PortalChecklistDest),
    bytes: fs.statSync(fig2PortalChecklistDest).size,
  });
  const fig2SurrogateAudit = path.join(ROOT, "manuscript_src", "natcs", "ncs_fig2_portal_surrogate_audit.md");
  const fig2SurrogateAuditDest = path.join(NOTES_DIR, "ncs_fig2_portal_surrogate_audit.md");
  copyFile(fig2SurrogateAudit, fig2SurrogateAuditDest);
  manifest.notes.push({
    path: rel(fig2SurrogateAuditDest),
    role: "Local low-width Fig. 2 surrogate preview audit; does not close journal portal gate.",
    sha256: sha256(fig2SurrogateAuditDest),
    bytes: fs.statSync(fig2SurrogateAuditDest).size,
  });
  const fig2SurrogateContactSheet = path.join(ROOT, "output", "natcs_fig2_portal_surrogate", "fig2_portal_surrogate_contact_sheet.png");
  const fig2SurrogateContactSheetDest = path.join(NOTES_DIR, "fig2_portal_surrogate_contact_sheet.png");
  copyFile(fig2SurrogateContactSheet, fig2SurrogateContactSheetDest);
  manifest.notes.push({
    path: rel(fig2SurrogateContactSheetDest),
    role: "Contact sheet for local standalone and embedded-page Fig. 2 preview stress checks.",
    sha256: sha256(fig2SurrogateContactSheetDest),
    bytes: fs.statSync(fig2SurrogateContactSheetDest).size,
  });
  const fig2PanelAContactSheet = path.join(ROOT, "output", "natcs_fig2_portal_surrogate", "fig2_panel_a_contact_sheet.png");
  const fig2PanelAContactSheetDest = path.join(NOTES_DIR, "fig2_panel_a_contact_sheet.png");
  copyFile(fig2PanelAContactSheet, fig2PanelAContactSheetDest);
  manifest.notes.push({
    path: rel(fig2PanelAContactSheetDest),
    role: "Panel-a crop contact sheet for checking endpoint-gate readability before journal portal upload.",
    sha256: sha256(fig2PanelAContactSheetDest),
    bytes: fs.statSync(fig2PanelAContactSheetDest).size,
  });
  const fig2SurrogateSummary = path.join(ROOT, "output", "natcs_fig2_portal_surrogate", "fig2_portal_surrogate_summary.json");
  const fig2SurrogateSummaryDest = path.join(NOTES_DIR, "fig2_portal_surrogate_summary.json");
  copyFile(fig2SurrogateSummary, fig2SurrogateSummaryDest);
  manifest.notes.push({
    path: rel(fig2SurrogateSummaryDest),
    role: "Machine-readable summary of local Fig. 2 surrogate preview dimensions and decision rule.",
    sha256: sha256(fig2SurrogateSummaryDest),
    bytes: fs.statSync(fig2SurrogateSummaryDest).size,
  });

  const readme = [
    "# NatCS Main Figure Source Package",
    "",
    "This package collects the generated source exports for the four main manuscript figures.",
    "",
    "Use it to inspect standalone figure quality during submission preview or peer review.",
    "",
    "Key figure-risk note: Figure 2 is the densest figure in the embedded manuscript PDF because it carries the endpoint-availability gate, recovery benchmark, measurement stress and stability boundary. Local page-render QA found the standalone Figure 2 source legible, while the smallest embedded manuscript labels require zoom. The standalone PDF/SVG files in this package should be used when the journal portal allows separate figure-source upload.",
    "",
    "Use `notes/ncs_fig2_portal_preview_checklist.md` to record the portal-preview pass/fail evidence. If the journal portal preview rasterizes Figure 2 poorly or makes panel a unreadable, use `notes/ncs_fig2_redesign_contract.md` as the controlled redesign brief. It preserves the endpoint-availability argument and prevents accidental addition of unsupported evidence.",
    "",
    "The local surrogate preview files in `notes/` document low-width Fig. 2 compression stress before upload. The panel-a contact sheet isolates the endpoint gate because that panel carries the methods-reviewer logic. These files are QA evidence only and should not be uploaded as manuscript figures.",
    "",
    "Included files are generated artifacts, not hand-edited illustrator files. Regeneration is controlled by the manuscript build scripts and reviewer archive.",
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
