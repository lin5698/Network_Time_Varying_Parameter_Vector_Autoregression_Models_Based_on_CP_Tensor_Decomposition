import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";
import { requireReleaseableNatcsEvidence } from "./natcs_utils.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyFile(src, dest) {
  ensureDir(path.dirname(dest));
  if (fs.existsSync(dest) && !fs.lstatSync(dest).isDirectory()) {
    fs.rmSync(dest, { force: true });
  }
  fs.copyFileSync(src, dest);
}

function runReleaseSafetyAudit() {
  const result = spawnSync("node", ["scripts/audit_natcs_release_safety.mjs"], { cwd: ROOT, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(`Release safety audit failed during package finalization: ${(result.stderr || result.stdout || "").trim()}`);
  }
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
  if (path.basename(src) !== ".DS_Store") copyFile(src, dest);
}

function mergeNumberedSiblings(root) {
  if (!fs.existsSync(root)) return;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    const stat = fs.lstatSync(current);
    const numbered = entry.match(/^(.*) \d+$/);
    const numberedFile = entry.match(/^(.*) \d+(\.[^.]+)$/);
    if (stat.isDirectory() && numbered) {
      const dest = path.join(root, numbered[1]);
      mergeTree(current, dest);
      fs.rmSync(current, { recursive: true, force: true });
      mergeNumberedSiblings(dest);
      continue;
    }
    if (stat.isFile() && numberedFile) {
      const dest = path.join(root, `${numberedFile[1]}${numberedFile[2]}`);
      if (!fs.existsSync(dest)) fs.renameSync(current, dest);
      else fs.rmSync(current, { force: true });
      continue;
    }
    if (stat.isFile() && numbered) {
      const dest = path.join(root, numbered[1]);
      if (!fs.existsSync(dest)) fs.renameSync(current, dest);
      else fs.rmSync(current, { force: true });
      continue;
    }
    if (stat.isDirectory()) mergeNumberedSiblings(current);
  }
}

function removeJunk(root) {
  if (!fs.existsSync(root)) return;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    if (entry === ".DS_Store") {
      fs.rmSync(current, { recursive: true, force: true });
      continue;
    }
    if (fs.lstatSync(current).isDirectory()) removeJunk(current);
  }
}

function findJunk(root, hits = []) {
  if (!fs.existsSync(root)) return hits;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    if (entry === ".DS_Store" || / \d+(?=\.|$)/.test(entry)) {
      hits.push(path.relative(ROOT, current));
      continue;
    }
    if (fs.lstatSync(current).isDirectory()) findJunk(current, hits);
  }
  return hits;
}

function normalizeNumberedPath(value) {
  return value
    .split("/")
    .map((part) => part.replace(/ \d+(?=\.|$)/g, ""))
    .join("/");
}

function assertInventory() {
  const inventoryPath = path.join(ROOT, "output", "submission_package", "natcs_current", "03_submission_materials", "submission_inventory.json");
  if (!fs.existsSync(inventoryPath)) return;
  const inventory = JSON.parse(fs.readFileSync(inventoryPath, "utf8"));
  const missing = [];
  const evidencePrefix = "output/submission_package/natcs_current/02_supporting_materials/evidence_bundle/";
  const repairEvidenceFile = (value) => {
    if (!value.startsWith(evidencePrefix)) return false;
    const src = path.join(ROOT, "output", value.slice(evidencePrefix.length));
    const dest = path.join(ROOT, value);
    if (!fs.existsSync(src)) return false;
    copyFile(src, dest);
    return true;
  };
  const walk = (value) => {
    if (typeof value === "string" && value.startsWith("output/")) {
      const normalized = normalizeNumberedPath(value);
      if (
        !fs.existsSync(path.join(ROOT, value))
        && !fs.existsSync(path.join(ROOT, normalized))
        && !repairEvidenceFile(normalized)
        && !repairEvidenceFile(value)
      ) {
        missing.push(value);
      }
    } else if (Array.isArray(value)) {
      value.forEach(walk);
    } else if (value && typeof value === "object") {
      Object.values(value).forEach(walk);
    }
  };
  walk(inventory.files);
  if (missing.length) {
    throw new Error(`Submission inventory points to missing paths:\n${missing.join("\n")}`);
  }
}

export function finalizeNatcsPackage() {
  // Fail closed while the controlling audits are blocked: finalization is a
  // submission-facing packaging step and may not run against stale artifacts.
  requireReleaseableNatcsEvidence(ROOT);
  const targets = [
    path.join(ROOT, "output", "submission_package", "natcs_current"),
    path.join(ROOT, "output", "reviewer_archive", "natcs_reviewer_archive"),
  ];
  for (let pass = 0; pass < 5; pass += 1) {
    targets.forEach(mergeNumberedSiblings);
    targets.forEach(removeJunk);
    if (!targets.flatMap((target) => findJunk(target)).length) break;
  }
  runReleaseSafetyAudit();
  assertInventory();
  for (let pass = 0; pass < 5; pass += 1) {
    targets.forEach(mergeNumberedSiblings);
    targets.forEach(removeJunk);
    if (!targets.flatMap((target) => findJunk(target)).length) break;
  }
  const junk = targets.flatMap((target) => findJunk(target));
  if (junk.length) {
    throw new Error(`NatCS package still contains junk paths:\n${junk.join("\n")}`);
  }
  return { finalized: targets.map((target) => path.relative(ROOT, target)) };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.log(finalizeNatcsPackage());
}
