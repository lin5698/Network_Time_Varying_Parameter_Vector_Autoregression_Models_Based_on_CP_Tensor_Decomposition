import fs from "fs";
import path from "path";
import { execFileSync } from "child_process";
import { finalizeNatcsPackage } from "./finalize_natcs_package.mjs";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT = path.join(ROOT, "output");
const SRC = path.join(ROOT, "manuscript_src", "natcs");
const TMP = path.join(ROOT, "tmp", "word_only_submission_materials");
const PACKAGE_ROOT = path.join(OUT, "submission_package", "natcs_current");
const REVIEWER_ROOT = path.join(OUT, "reviewer_archive", "natcs_reviewer_archive");
const INTEGRATED_ROOT = path.join(OUT, "integrated_package");

const UPLOAD_DOCX_FILES = [
  ["01_main_manuscript/main_manuscript.docx", "main_manuscript.docx"],
  ["02_supporting_materials/supplementary_information.docx", "supplementary_information.docx"],
];

const STANDALONE_WORD_MATERIALS = [
  ["03_submission_materials/cover_letter_natcs.md", "cover_letter_natcs.docx", "Cover Letter"],
  ["03_submission_materials/data_availability.txt", "data_availability.docx", "Data availability"],
  ["03_submission_materials/code_availability.txt", "code_availability.docx", "Code availability"],
  ["03_submission_materials/author_contributions.txt", "author_contributions.docx", "Author contributions"],
  ["03_submission_materials/competing_interests.txt", "competing_interests.docx", "Competing interests"],
  ["03_submission_materials/ethics_statement.txt", "ethics_statement.docx", "Ethics statement"],
  ["03_submission_materials/ai_use_statement.txt", "ai_use_statement.docx", "AI use statement"],
];

const CLEAN_SUBMISSION_FILES = [
  ["01_main_manuscript/main_manuscript.docx", "01_main_manuscript/main_manuscript.docx"],
  ["01_main_manuscript/main_manuscript.pdf", "01_main_manuscript/main_manuscript.pdf"],
  ["01_main_manuscript/main_manuscript.tex", "01_main_manuscript/main_manuscript.tex"],
  ["02_supporting_materials/supplementary_information.docx", "02_supporting_materials/supplementary_information.docx"],
  ["02_supporting_materials/supplementary_information.pdf", "02_supporting_materials/supplementary_information.pdf"],
  ["02_supporting_materials/supplementary_information.tex", "02_supporting_materials/supplementary_information.tex"],
  ["03_submission_materials/cover_letter_natcs.md", "03_submission_materials/cover_letter_natcs.md"],
  ["03_submission_materials/references.bib", "03_submission_materials/references.bib"],
  ["03_submission_materials/nature.csl", "03_submission_materials/nature.csl"],
  ["03_submission_materials/data_availability.txt", "03_submission_materials/data_availability.txt"],
  ["03_submission_materials/code_availability.txt", "03_submission_materials/code_availability.txt"],
  ["03_submission_materials/author_contributions.txt", "03_submission_materials/author_contributions.txt"],
  ["03_submission_materials/competing_interests.txt", "03_submission_materials/competing_interests.txt"],
  ["03_submission_materials/ethics_statement.txt", "03_submission_materials/ethics_statement.txt"],
  ["03_submission_materials/ai_use_statement.txt", "03_submission_materials/ai_use_statement.txt"],
];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function removeIfExists(target) {
  fs.rmSync(target, { recursive: true, force: true });
}

function copyFile(src, dest) {
  ensureDir(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

function firstExisting(paths) {
  for (const candidate of paths) {
    if (candidate && fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function findPythonWithPypdf() {
  const candidates = [
    process.env.NATCS_PYTHON,
    path.join(process.env.HOME || "", ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "bin", "python3"),
    "/opt/homebrew/bin/python3",
    "/usr/bin/python3",
    "python3",
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      execFileSync(candidate, ["-c", "import pypdf"], { stdio: "ignore" });
      return candidate;
    } catch {
      // Try the next interpreter.
    }
  }
  throw new Error("Could not find a Python interpreter with pypdf installed for PDF metadata scrubbing.");
}

function scrubPdfMetadata(src, dest) {
  ensureDir(path.dirname(dest));
  const gs = firstExisting(["/opt/homebrew/bin/gs", "/usr/local/bin/gs", "/usr/bin/gs", "gs"]);
  if (!gs) throw new Error("Ghostscript is required for deep PDF metadata scrubbing but was not found.");
  const py = findPythonWithPypdf();
  const tmpGs = `${dest}.gs-tmp.pdf`;
  const tmpClean = `${dest}.clean-tmp.pdf`;
  removeIfExists(tmpGs);
  removeIfExists(tmpClean);
  execFileSync(gs, [
    "-q",
    "-dNOPAUSE",
    "-dBATCH",
    "-sDEVICE=pdfwrite",
    "-dCompatibilityLevel=1.7",
    "-dAutoRotatePages=/None",
    `-sOutputFile=${tmpGs}`,
    "-f",
    src,
    "-c",
    "[ /Title () /Author () /Subject () /Keywords () /Creator () /Producer () /DOCINFO pdfmark",
  ], { stdio: "ignore" });
  const scrubScript = `
from pathlib import Path
from pypdf import PdfReader, PdfWriter
src = Path(r'''${tmpGs}''')
dst = Path(r'''${tmpClean}''')
reader = PdfReader(str(src))
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
try:
    writer.xmp_metadata = None
except Exception:
    pass
writer.add_metadata({
    '/Title': '',
    '/Author': '',
    '/Subject': '',
    '/Keywords': '',
    '/Creator': '',
    '/Producer': '',
    '/CreationDate': '',
    '/ModDate': '',
})
with dst.open('wb') as f:
    writer.write(f)
`;
  execFileSync(py, ["-c", scrubScript], { stdio: "ignore" });
  fs.renameSync(tmpClean, dest);
  removeIfExists(tmpGs);
}

function copySubmissionFile(src, dest) {
  if (src.toLowerCase().endsWith(".pdf")) scrubPdfMetadata(src, dest);
  else copyFile(src, dest);
}

function copyTree(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.lstatSync(src);
  if (stat.isDirectory()) {
    ensureDir(dest);
    for (const entry of fs.readdirSync(src)) {
      if (entry === ".DS_Store") continue;
      copyTree(path.join(src, entry), path.join(dest, entry));
    }
    return;
  }
  copyFile(src, dest);
}

function walk(root, files = []) {
  if (!fs.existsSync(root)) return files;
  for (const entry of fs.readdirSync(root)) {
    const current = path.join(root, entry);
    const stat = fs.lstatSync(current);
    if (stat.isDirectory()) walk(current, files);
    else files.push(current);
  }
  return files;
}

function internalNamePattern() {
  const terms = [
    "au" + "dit",
    "led" + "ger",
    "mat" + "rix",
    "inven" + "tory",
    "meta" + "data",
    "readi" + "ness",
    "tri" + "age",
    "re" + "jection",
    "pre" + "submission",
    "check" + "list",
    "no" + "tes",
  ];
  return new RegExp(`(${terms.join("|")})`, "i");
}

function internalObjectPattern() {
  return /(^|[^A-Za-z0-9_])(s[\s_-]+net[\s_-]+raw|s[\s_-]+net[\s_-]+clip|g[\s_-]+net|Agg[\s_-]+g[\s_-]+net|net[\s_-]+clip|net[\s_-]+raw|gnet|Pair_[A-Z]{3}<-[A-Z]{3}_s_net(?:_clip|_raw)?)(?![A-Za-z0-9_])/i;
}

function assertDocxNoInternalObjects(file) {
  const py = firstExisting([
    path.join(process.env.HOME || "", ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "bin", "python3"),
    "/opt/homebrew/bin/python3",
    "/usr/bin/python3",
    "python3",
  ]);
  const script = `
import re, sys, zipfile
from xml.etree import ElementTree as ET
pattern = re.compile(r'(^|[^A-Za-z0-9_])(s[\\\\s_-]+net[\\\\s_-]+raw|s[\\\\s_-]+net[\\\\s_-]+clip|g[\\\\s_-]+net|Agg[\\\\s_-]+g[\\\\s_-]+net|net[\\\\s_-]+clip|net[\\\\s_-]+raw|gnet|Pair_[A-Z]{3}<-[A-Z]{3}_s_net(?:_clip|_raw)?)(?![A-Za-z0-9_])', re.I)
path = sys.argv[1]
hits = []
def visible_text(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return xml_bytes.decode('utf-8', 'ignore')
    parts = []
    for node in root.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if tag in {'t', 'instrText', 'delText'} and node.text:
            parts.append(node.text)
        elif tag in {'tab', 'br'}:
            parts.append(' ')
    return ''.join(parts)
with zipfile.ZipFile(path) as z:
    for name in z.namelist():
        if not (name.endswith('.xml') or name.endswith('.rels')):
            continue
        data = z.read(name)
        visible = visible_text(data) if name.startswith('word/') and name.endswith('.xml') else data.decode('utf-8', 'ignore')
        m = pattern.search(visible)
        if m:
            start = max(0, m.start() - 80)
            end = min(len(visible), m.end() + 120)
            hits.append(f'{name}: ' + re.sub(r'\\\\s+', ' ', visible[start:end]))
if hits:
    print('DOCX contains internal propagation variable names: ' + path)
    print('\\\\n'.join(hits[:10]))
    sys.exit(1)
`;
  execFileSync(py, ["-c", script, file], { cwd: ROOT, stdio: "pipe" });
}

function assertCleanUpload(uploadDir) {
  const bannedName = internalNamePattern();
  const hits = [];
  const nonWord = [];
  for (const file of walk(uploadDir)) {
    const rel = path.relative(uploadDir, file);
    if (path.extname(file).toLowerCase() !== ".docx") {
      nonWord.push(rel);
    } else {
      assertDocxNoInternalObjects(file);
    }
    if (rel.includes(".DS_Store") || / \d+(?=\.|$)/.test(rel) || bannedName.test(path.basename(rel))) {
      hits.push(rel);
    }
  }
  if (nonWord.length) {
    throw new Error(`Clean upload must contain Word files only:\n${nonWord.join("\n")}`);
  }
  if (hits.length) {
    throw new Error(`Clean upload contains internal or junk files:\n${hits.join("\n")}`);
  }
}

function assertCleanTree(root, label) {
  const bannedName = internalNamePattern();
  const hits = [];
  for (const file of walk(root)) {
    const rel = path.relative(root, file);
    if (rel.includes(".DS_Store") || / \d+(?=\.|$)/.test(rel) || bannedName.test(path.basename(rel))) {
      hits.push(rel);
    }
  }
  if (hits.length) {
    throw new Error(`${label} contains internal or junk files:\n${hits.join("\n")}`);
  }
}

function makeTimestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return [
    d.getFullYear(),
    pad(d.getMonth() + 1),
    pad(d.getDate()),
    "_",
    pad(d.getHours()),
    pad(d.getMinutes()),
    pad(d.getSeconds()),
  ].join("");
}

function postprocessDocx(file) {
  execFileSync("python3", ["scripts/postprocess_natcs_docx.py", file], {
    cwd: ROOT,
    stdio: "inherit",
  });
}

function pandocToDocx(markdownFile, outFile, extraArgs = []) {
  const referenceDocx = path.join(OUT, "doc", "natcs_manuscript.docx");
  const args = [
    markdownFile,
    "--standalone",
    "--from",
    "markdown+tex_math_dollars+pipe_tables+raw_tex",
    "--to",
    "docx",
    "--output",
    outFile,
    "--resource-path",
    ROOT,
    ...extraArgs,
  ];
  if (fs.existsSync(referenceDocx)) {
    args.push("--reference-doc", referenceDocx);
  }
  execFileSync("pandoc", args, { cwd: ROOT, stdio: "inherit" });
  postprocessDocx(outFile);
}

function createStandaloneWordMaterial(srcFile, outFile, heading) {
  ensureDir(TMP);
  const tmpMd = path.join(TMP, `${path.basename(outFile, ".docx")}.md`);
  const body = fs.readFileSync(srcFile, "utf8").trim();
  fs.writeFileSync(tmpMd, `# ${heading}\n\n${body}\n`, "utf8");
  pandocToDocx(tmpMd, outFile);
}

function createReferencesWordMaterial(outFile) {
  ensureDir(TMP);
  const tmpMd = path.join(TMP, "references.md");
  const bib = path.join(SRC, "references.bib");
  const csl = path.join(SRC, "nature.csl");
  if (!fs.existsSync(bib)) throw new Error("Missing references.bib for Word references document.");
  if (!fs.existsSync(csl)) throw new Error("Missing nature.csl for Word references document.");
  fs.writeFileSync(
    tmpMd,
    [
      "---",
      `bibliography: "${bib}"`,
      `csl: "${csl}"`,
      "nocite: |",
      "  @*",
      "---",
      "",
      "# References {-}",
      "",
      "::: {#refs}",
      ":::",
      "",
    ].join("\n"),
    "utf8"
  );
  pandocToDocx(tmpMd, outFile, ["--citeproc"]);
}

function createUpload(uploadDir) {
  removeIfExists(uploadDir);
  ensureDir(uploadDir);
  removeIfExists(TMP);
  ensureDir(TMP);
  for (const [srcRel, destRel] of UPLOAD_DOCX_FILES) {
    const src = path.join(PACKAGE_ROOT, srcRel);
    if (!fs.existsSync(src)) throw new Error(`Missing upload source: ${srcRel}`);
    copyFile(src, path.join(uploadDir, destRel));
  }
  for (const [srcRel, destRel, heading] of STANDALONE_WORD_MATERIALS) {
    const src = path.join(PACKAGE_ROOT, srcRel);
    if (!fs.existsSync(src)) throw new Error(`Missing Word material source: ${srcRel}`);
    createStandaloneWordMaterial(src, path.join(uploadDir, destRel), heading);
  }
  createReferencesWordMaterial(path.join(uploadDir, "references.docx"));
  assertCleanUpload(uploadDir);
}

function createCleanSubmissionPackage(destDir) {
  removeIfExists(destDir);
  ensureDir(destDir);
  for (const [srcRel, destRel] of CLEAN_SUBMISSION_FILES) {
    const src = path.join(PACKAGE_ROOT, srcRel);
    if (!fs.existsSync(src)) throw new Error(`Missing clean submission source: ${srcRel}`);
    copySubmissionFile(src, path.join(destDir, destRel));
  }
  assertCleanTree(destDir, "Clean submission package");
}

function zipDir(dir, zipPath = `${dir}.zip`) {
  removeIfExists(zipPath);
  execFileSync("/usr/bin/zip", ["-r", "-X", zipPath, path.basename(dir)], {
    cwd: path.dirname(dir),
    stdio: "inherit",
  });
  return zipPath;
}

function zipDocxUploadOnly(uploadDir, zipPath) {
  removeIfExists(zipPath);
  const entries = walk(uploadDir)
    .filter((file) => path.extname(file).toLowerCase() === ".docx")
    .map((file) => path.join(path.basename(uploadDir), path.relative(uploadDir, file)))
    .sort();
  if (!entries.length) {
    throw new Error(`No DOCX files found for upload zip: ${uploadDir}`);
  }
  execFileSync("/usr/bin/zip", ["-X", zipPath, ...entries], {
    cwd: path.dirname(uploadDir),
    stdio: "inherit",
  });
  return zipPath;
}

function archiveLatestPointers(timestamp) {
  const archiveDir = path.join(INTEGRATED_ROOT, "_archives", `superseded_word_only_before_${timestamp}`);
  const latestDir = path.join(INTEGRATED_ROOT, "latest_submission_upload_word_only");
  const latestZip = path.join(INTEGRATED_ROOT, "latest_submission_upload_word_only.zip");
  if (fs.existsSync(latestDir) || fs.existsSync(latestZip)) ensureDir(archiveDir);
  if (fs.existsSync(latestDir)) {
    fs.renameSync(latestDir, path.join(archiveDir, "latest_submission_upload_word_only"));
  }
  if (fs.existsSync(latestZip)) {
    fs.renameSync(latestZip, path.join(archiveDir, "latest_submission_upload_word_only.zip"));
  }
}

function archiveSupersededIntegratedPackages(timestamp) {
  if (!fs.existsSync(INTEGRATED_ROOT)) return;
  const archiveDir = path.join(INTEGRATED_ROOT, "_archives", `superseded_timestamped_word_only_before_${timestamp}`);
  const pattern = /^natcs_integrated_submission_word_only_\d{8}_\d{6}(?:_submission_upload)?(?:\.zip)?$/;
  const entries = fs.readdirSync(INTEGRATED_ROOT)
    .filter((entry) => pattern.test(entry))
    .sort();
  if (!entries.length) return;
  ensureDir(archiveDir);
  for (const entry of entries) {
    const src = path.join(INTEGRATED_ROOT, entry);
    const dest = path.join(archiveDir, entry);
    removeIfExists(dest);
    fs.renameSync(src, dest);
  }
}

function refreshLatestUpload(uploadDir) {
  const latestDir = path.join(INTEGRATED_ROOT, "latest_submission_upload_word_only");
  const latestZip = path.join(INTEGRATED_ROOT, "latest_submission_upload_word_only.zip");
  removeIfExists(latestDir);
  copyTree(uploadDir, latestDir);
  zipDocxUploadOnly(latestDir, latestZip);
  return {
    latest_upload_dir: path.relative(ROOT, latestDir),
    latest_upload_zip: path.relative(ROOT, latestZip),
  };
}

export function createCleanIntegratedPackage() {
  finalizeNatcsPackage();
  const timestamp = makeTimestamp();
  archiveLatestPointers(timestamp);
  archiveSupersededIntegratedPackages(timestamp);
  const integratedDir = path.join(INTEGRATED_ROOT, `natcs_integrated_submission_word_only_${timestamp}`);
  removeIfExists(integratedDir);
  ensureDir(integratedDir);

  const uploadDir = path.join(integratedDir, "submission_upload");
  createUpload(uploadDir);
  execFileSync("python3", ["scripts/audit_natcs_submission.py", "--package", integratedDir, "--skip-text-tree"], {
    cwd: ROOT,
    stdio: "inherit",
  });

  const zipPath = zipDir(integratedDir);
  const uploadZip = zipDocxUploadOnly(uploadDir, path.join(INTEGRATED_ROOT, `${path.basename(integratedDir)}_submission_upload.zip`));
  const latest = refreshLatestUpload(uploadDir);
  finalizeNatcsPackage();
  return {
    integrated_dir: path.relative(ROOT, integratedDir),
    zip: path.relative(ROOT, zipPath),
    upload_dir: path.relative(ROOT, uploadDir),
    upload_zip: path.relative(ROOT, uploadZip),
    ...latest,
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  console.log(JSON.stringify(createCleanIntegratedPackage(), null, 2));
}
