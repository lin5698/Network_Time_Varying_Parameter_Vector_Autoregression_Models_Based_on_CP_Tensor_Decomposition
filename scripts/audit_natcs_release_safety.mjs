import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SUBMISSION_MATERIALS = path.join(ROOT, "output", "submission_package", "natcs_current", "03_submission_materials");

const ROOTS = [
  ["Reviewer archive", path.join(ROOT, "output", "reviewer_archive", "natcs_reviewer_archive")],
  ["Submission package", path.join(ROOT, "output", "submission_package", "natcs_current")],
  ["Figure source package", path.join(ROOT, "output", "figure_source_package", "natcs_main_figure_sources")],
  ["Latest word-only upload directory", path.join(ROOT, "output", "integrated_package", "latest_submission_upload_word_only")],
];

const BINARY_EXTENSIONS = new Set([
  ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".zip", ".gz", ".tgz", ".xlsx", ".xls", ".pyc",
]);

const SENSITIVE_FILENAME_PATTERNS = [
  /(^|[/\\])\.env(?:\.|$)/i,
  /(^|[/\\])id_(?:rsa|dsa|ecdsa|ed25519)(?:\.|$)/i,
  /(?:secret|credential|password|private[_-]?key|api[_-]?key|access[_-]?token)/i,
];

const BLOCKER_CONTENT_PATTERNS = [
  ["private_key_block", /-----BEGIN [A-Z ]*PRIVATE KEY-----/i],
  ["openai_api_key", /\bsk-[A-Za-z0-9_-]{20,}\b/],
  ["github_token", /\bgh[pousr]_[A-Za-z0-9_]{20,}\b/],
  ["aws_access_key", /\bAKIA[0-9A-Z]{16}\b/],
  ["credential_assignment", /\b(?:api[_-]?key|secret|token|password)\s*[:=]\s*["']?[A-Za-z0-9_./+=-]{16,}(?=$|[\s"'`;,#])/i],
];

const WARNING_CONTENT_PATTERNS = [
  ["private_absolute_path", /(?:\/Users\/[A-Za-z0-9_-][A-Za-z0-9._-]*|\/home\/[A-Za-z0-9_-][A-Za-z0-9._-]*|[A-Za-z]:\\Users\\[A-Za-z0-9_-][^\\\s`"']*)/],
];

function rel(file) {
  return path.relative(ROOT, file).split(path.sep).join("/");
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function writeText(file, text) {
  ensureDir(path.dirname(file));
  if (fs.existsSync(file) && !fs.lstatSync(file).isDirectory()) {
    fs.rmSync(file, { force: true });
  }
  fs.writeFileSync(file, text, "utf8");
}

function macFileFlags(file) {
  const result = spawnSync("stat", ["-f", "%Sf", file], { cwd: ROOT, encoding: "utf8" });
  return result.status === 0 ? result.stdout.trim() : "";
}

function isDataless(file) {
  return macFileFlags(file).split(",").includes("dataless");
}

function collectFiles(root) {
  if (!fs.existsSync(root)) return [];
  const files = [];
  const walk = (current) => {
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink()) return;
    if (stat.isDirectory()) {
      for (const entry of fs.readdirSync(current).sort()) {
        if (entry === ".DS_Store") continue;
        walk(path.join(current, entry));
      }
      return;
    }
    if (stat.isFile()) files.push(current);
  };
  walk(root);
  return files;
}

function isBinaryLike(file) {
  if (BINARY_EXTENSIONS.has(path.extname(file).toLowerCase())) return true;
  if (isDataless(file)) return true;
  const fd = fs.openSync(file, "r");
  try {
    const buffer = Buffer.alloc(512);
    const bytes = fs.readSync(fd, buffer, 0, buffer.length, 0);
    return buffer.subarray(0, bytes).includes(0);
  } finally {
    fs.closeSync(fd);
  }
}

function snippet(text, match) {
  const index = typeof match.index === "number" ? match.index : 0;
  const start = Math.max(0, index - 50);
  const end = Math.min(text.length, index + String(match[0] || "").length + 50);
  return text.slice(start, end).replace(/\s+/g, " ").replace(/[A-Za-z0-9_./+=-]{24,}/g, "[redacted]");
}

function scanText(file, text) {
  const findings = [];
  for (const [kind, pattern] of BLOCKER_CONTENT_PATTERNS) {
    const match = pattern.exec(text);
    if (match) findings.push({ severity: "blocker", kind, file: rel(file), snippet: snippet(text, match) });
  }
  for (const [kind, pattern] of WARNING_CONTENT_PATTERNS) {
    const match = pattern.exec(text);
    if (match) findings.push({ severity: "warning", kind, file: rel(file), snippet: snippet(text, match) });
  }
  return findings;
}

function audit() {
  const generatedAt = new Date().toISOString();
  const roots = ROOTS.map(([label, file]) => ({ label, path: rel(file), exists: fs.existsSync(file) }));
  const findings = [];
  let filesSeen = 0;
  let textFilesScanned = 0;
  let binaryFilesSkipped = 0;

  for (const [, root] of ROOTS) {
    for (const file of collectFiles(root)) {
      filesSeen += 1;
      const relative = rel(file);
      if (SENSITIVE_FILENAME_PATTERNS.some((pattern) => pattern.test(relative))) {
        findings.push({ severity: "blocker", kind: "sensitive_filename", file: relative, snippet: path.basename(relative) });
      }
      if (isBinaryLike(file)) {
        binaryFilesSkipped += 1;
        continue;
      }
      textFilesScanned += 1;
      const text = fs.readFileSync(file, "utf8");
      findings.push(...scanText(file, text));
    }
  }

  const blockerCount = findings.filter((finding) => finding.severity === "blocker").length;
  const warningCount = findings.filter((finding) => finding.severity === "warning").length;
  return {
    generated_at: generatedAt,
    purpose: "Scan NatCS reviewer/upload-facing packages for private paths, sensitive filenames and credential-like content before transfer or public release.",
    boundary: "Pattern-based local audit. It does not prove provider permissions, public DOI assignment or legal redistributability.",
    roots,
    files_seen: filesSeen,
    text_files_scanned: textFilesScanned,
    binary_files_skipped: binaryFilesSkipped,
    findings,
    blocker_count: blockerCount,
    warning_count: warningCount,
  };
}

function markdownTable(rows) {
  return [
    "| Severity | Kind | File | Redacted snippet |",
    "| --- | --- | --- | --- |",
    ...rows.map((row) => `| ${row.severity} | ${row.kind} | \`${row.file}\` | ${String(row.snippet || "").replace(/\|/g, "\\|")} |`),
  ].join("\n");
}

function renderMarkdown(result) {
  const findingRows = result.findings.length
    ? result.findings
    : [{ severity: "none", kind: "none", file: "none", snippet: "none" }];
  return [
    "# NatCS Release Safety Audit",
    "",
    "Purpose: scan reviewer/upload-facing packages for private paths, sensitive filenames and credential-like content before transfer or public release.",
    "",
    "Boundary: this is a pattern-based local audit. It does not prove source-provider permissions, public DOI assignment, licence compatibility or legal redistributability.",
    "",
    `Generated at: ${result.generated_at}`,
    "",
    "## Scope",
    "",
    "| Root | Path | Exists |",
    "| --- | --- | --- |",
    ...result.roots.map((root) => `| ${root.label} | \`${root.path}\` | ${root.exists ? "yes" : "no"} |`),
    "",
    "## Scan Summary",
    "",
    `- Files seen: ${result.files_seen}`,
    `- Text files scanned: ${result.text_files_scanned}`,
    `- Binary files skipped: ${result.binary_files_skipped}`,
    `- Blockers: ${result.blocker_count}`,
    `- Warnings: ${result.warning_count}`,
    "",
    "## Findings",
    "",
    markdownTable(findingRows),
    "",
    "## Interpretation",
    "",
    result.blocker_count === 0
      ? "Interpretation: no credential-like blocker patterns were detected in the scanned reviewer/upload-facing package roots."
      : "Interpretation: blocker patterns were detected and must be removed before transfer or public release.",
    "",
    result.warning_count === 0
      ? "No private absolute-path warnings were detected by this scan."
      : "Private absolute-path warnings were detected and should be reviewed before transfer or public release.",
    "",
  ].join("\n");
}

function main() {
  const checkOnly = process.argv.includes("--check");
  const result = audit();
  if (checkOnly) {
    console.log(JSON.stringify({
      blockers: result.blocker_count,
      warnings: result.warning_count,
      files_seen: result.files_seen,
      text_files_scanned: result.text_files_scanned,
      binary_files_skipped: result.binary_files_skipped,
    }));
    process.exit(result.blocker_count > 0 ? 1 : 0);
  }
  writeText(path.join(SUBMISSION_MATERIALS, "release_safety_audit.json"), `${JSON.stringify(result, null, 2)}\n`);
  writeText(path.join(SUBMISSION_MATERIALS, "release_safety_audit.md"), renderMarkdown(result));
  console.log(JSON.stringify({
    blockers: result.blocker_count,
    warnings: result.warning_count,
    files_seen: result.files_seen,
    text_files_scanned: result.text_files_scanned,
    binary_files_skipped: result.binary_files_skipped,
  }));
  process.exit(result.blocker_count > 0 ? 1 : 0);
}

main();
