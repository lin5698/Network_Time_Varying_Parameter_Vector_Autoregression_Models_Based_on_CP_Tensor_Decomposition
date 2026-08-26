import fs from "fs";
import path from "path";
import crypto from "crypto";
import { spawnSync } from "child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SUBMISSION_MATERIALS = path.join(ROOT, "output", "submission_package", "natcs_current", "03_submission_materials");
const INTEGRATED_DIR = path.join(ROOT, "output", "integrated_package");

function rel(file) {
  return path.relative(ROOT, file).replaceAll(path.sep, "/");
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

function fileEntry(label, file, required = true) {
  const exists = fs.existsSync(file);
  if (!exists && required) {
    throw new Error(`Missing required freeze artifact: ${file}`);
  }
  if (!exists) {
    return { label, path: rel(file), exists: false };
  }
  return {
    label,
    path: rel(file),
    bytes: fs.statSync(file).size,
    sha256: sha256(file),
    exists: true,
  };
}

function newestStampedUploadZip() {
  if (!fs.existsSync(INTEGRATED_DIR)) return null;
  const matches = fs.readdirSync(INTEGRATED_DIR)
    .filter((name) => /natcs_integrated_submission_word_only_[0-9_]+_submission_upload\.zip$/.test(name))
    .sort();
  return matches.length ? path.join(INTEGRATED_DIR, matches.at(-1)) : null;
}

function countFiles(dir) {
  if (!fs.existsSync(dir)) return 0;
  let count = 0;
  const scan = (current) => {
    for (const entry of fs.readdirSync(current)) {
      const next = path.join(current, entry);
      if (fs.statSync(next).isDirectory()) scan(next);
      else count += 1;
    }
  };
  scan(dir);
  return count;
}

function readOpenGateCounts() {
  const gates = [
    {
      label: "Final author decision sheet",
      file: path.join(SUBMISSION_MATERIALS, "natcs_final_author_decision_sheet.md"),
      pattern: /Needs action/g,
    },
    {
      label: "Fig. 2 portal preview checklist",
      file: path.join(SUBMISSION_MATERIALS, "ncs_fig2_portal_preview_checklist.md"),
      pattern: /Not checked|Unresolved/g,
    },
    {
      label: "Raw-source access worksheet",
      file: path.join(SUBMISSION_MATERIALS, "raw_source_access_decision_worksheet.md"),
      pattern: /Unresolved|TODO/g,
    },
    {
      label: "Public-release readiness worksheet",
      file: path.join(SUBMISSION_MATERIALS, "public_release_readiness_worksheet.md"),
      pattern: /Unresolved|TODO/g,
    },
  ];
  return gates.map((gate) => {
    if (!fs.existsSync(gate.file)) {
      return { label: gate.label, path: rel(gate.file), exists: false, open_markers: null };
    }
    const matches = [...fs.readFileSync(gate.file, "utf8").matchAll(gate.pattern)];
    return {
      label: gate.label,
      path: rel(gate.file),
      exists: true,
      open_markers: matches.length,
    };
  });
}

function writeText(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

function runReleaseSafetyAudit() {
  const result = spawnSync("node", ["scripts/audit_natcs_release_safety.mjs"], { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`Release safety audit failed before freeze manifest: ${(result.stderr || result.stdout || "").trim()}`);
  }
  return result.stdout || "";
}

function markdownTable(rows) {
  return [
    "| Label | Path | Bytes | SHA-256 |",
    "| --- | --- | ---: | --- |",
    ...rows.map((row) => `| ${row.label} | \`${row.path}\` | ${row.exists ? row.bytes : "missing"} | ${row.exists ? `\`${row.sha256}\`` : "missing"} |`),
  ].join("\n");
}

function main() {
  // Fail closed while the controlling audits are blocked: the freeze manifest
  // certifies upload-facing artifact hashes and may not be produced from
  // stale blocked evidence.
  requireReleaseableNatcsEvidence(ROOT);
  runReleaseSafetyAudit();
  const stampedUploadZip = newestStampedUploadZip();
  const reviewerArchive = path.join(ROOT, "output", "reviewer_archive", "natcs_reviewer_archive");
  const jsonFile = path.join(SUBMISSION_MATERIALS, "natcs_upload_freeze_manifest.json");
  const mdFile = path.join(SUBMISSION_MATERIALS, "natcs_upload_freeze_manifest.md");
  const inventoryFile = path.join(SUBMISSION_MATERIALS, "submission_inventory.json");
  if (fs.existsSync(inventoryFile)) {
    const inventory = JSON.parse(fs.readFileSync(inventoryFile, "utf8"));
    inventory.files ??= {};
    inventory.files.submission_materials ??= {};
    inventory.files.submission_materials.upload_freeze_manifest_json = rel(jsonFile);
    inventory.files.submission_materials.upload_freeze_manifest_md = rel(mdFile);
    inventory.updated_at = new Date().toISOString();
    writeText(inventoryFile, `${JSON.stringify(inventory, null, 2)}\n`);
  }

  const artifacts = [
    fileEntry("Main manuscript PDF", path.join(ROOT, "output", "pdf", "natcs_manuscript.pdf")),
    fileEntry("Main manuscript DOCX", path.join(ROOT, "output", "doc", "natcs_manuscript.docx")),
    fileEntry("Supplementary PDF", path.join(ROOT, "output", "pdf", "natcs_supplementary.pdf")),
    fileEntry("Supplementary DOCX", path.join(ROOT, "output", "doc", "natcs_supplementary.docx")),
    fileEntry("Latest word-only upload ZIP", path.join(ROOT, "output", "integrated_package", "latest_submission_upload_word_only.zip")),
    fileEntry("Latest stamped submission-upload ZIP", stampedUploadZip || path.join(ROOT, "output", "integrated_package", "NO_STAMPED_UPLOAD_ZIP"), Boolean(stampedUploadZip)),
    fileEntry("Main figure source ZIP", path.join(ROOT, "output", "figure_source_package", "latest_natcs_main_figure_sources.zip")),
    fileEntry("Latest reviewer archive ZIP", path.join(ROOT, "output", "reviewer_archive", "latest_natcs_reviewer_archive.zip")),
    fileEntry("Submission inventory", path.join(SUBMISSION_MATERIALS, "submission_inventory.json")),
    fileEntry("Reviewer archive manifest", path.join(reviewerArchive, "manifest.json")),
    fileEntry("Reviewer archive README", path.join(reviewerArchive, "README.md")),
  ];

  const reviewerArchiveSummary = {
    path: rel(reviewerArchive),
    exists: fs.existsSync(reviewerArchive),
    file_count: countFiles(reviewerArchive),
  };

  const freeze = {
    generated_at: new Date().toISOString(),
    purpose: "Freeze current NatCS upload-facing artifacts and support checksums before final submission.",
    boundary: "This manifest records local file identity. It does not close external journal portal, raw-source, helper-code or public-release gates.",
    artifacts,
    reviewer_archive: reviewerArchiveSummary,
    external_gate_markers: readOpenGateCounts(),
  };

  writeText(jsonFile, `${JSON.stringify(freeze, null, 2)}\n`);

  const md = [
    "# NatCS Upload Freeze Manifest",
    "",
    "Purpose: record the exact local artifacts intended for Nature Computational Science upload or reviewer/editor support.",
    "",
    "Boundary: this manifest records file identity and open-gate status. It does not claim that Fig. 2 passed the journal portal preview, that raw sources are shareable, or that a public DOI exists.",
    "",
    `Generated at: ${freeze.generated_at}`,
    "",
    "## Frozen Artifacts",
    "",
    markdownTable(artifacts),
    "",
    "## Reviewer Archive",
    "",
    `- Path: \`${reviewerArchiveSummary.path}\``,
    `- Exists: ${reviewerArchiveSummary.exists ? "yes" : "no"}`,
    `- File count: ${reviewerArchiveSummary.file_count}`,
    "",
    "## Open External Gate Markers",
    "",
    "| Gate | Source | Open markers |",
    "| --- | --- | ---: |",
    ...freeze.external_gate_markers.map((gate) => `| ${gate.label} | \`${gate.path}\` | ${gate.open_markers ?? "missing"} |`),
    "",
    "Interpretation: open markers are expected until authors or the journal portal provide the required external evidence. Keep manuscript wording conservative for unresolved gates.",
    "",
  ].join("\n");
  writeText(mdFile, md);

  console.log(JSON.stringify({
    markdown: rel(mdFile),
    json: rel(jsonFile),
    artifact_count: artifacts.length,
    reviewer_archive_file_count: reviewerArchiveSummary.file_count,
  }, null, 2));
}

main();
