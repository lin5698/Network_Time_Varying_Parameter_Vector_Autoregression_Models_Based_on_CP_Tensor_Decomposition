import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";

export function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

export function readText(file) {
  return fs.readFileSync(file, "utf8");
}

export function writeText(file, text) {
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, text, "utf8");
}

export function readJson(file) {
  return JSON.parse(readText(file));
}

/**
 * Refuse to turn source drafts into manuscript-facing artifacts until both
 * controlling audits release the empirical claim set and the source has
 * deliberately replaced its inactive empirical boundary records. This check
 * performs no scientific execution and is evaluated before any build write.
 */
export function requireReleaseableNatcsEvidence(root) {
  const audits = [
    ["PAPER_CLAIM_AUDIT", path.join(root, "PAPER_CLAIM_AUDIT.json")],
    ["EMPIRICAL_IMPLEMENTATION_AUDIT", path.join(root, "EMPIRICAL_IMPLEMENTATION_AUDIT.json")],
  ];
  const failures = [];

  const activationReceipt = path.join(root, "refine-logs", "REC-P3_RC1_RC2_ACTIVATION_V1_20260830.json");
  if (!fs.existsSync(activationReceipt)) {
    failures.push("RC-1/RC-2 activation receipt is missing");
  } else {
    const decision = readJson(activationReceipt);
    if (decision.rc1_manuscript_promotion !== "ACTIVATED") failures.push("RC-1 manuscript promotion is not activated");
    if (decision.rc2_empirical_claim_activation !== "ACTIVATED_WITH_LIMITATIONS") failures.push("RC-2 empirical claim activation is not limitation-bounded");
    if (decision.scientific_experiments_rerun !== false) failures.push("scientific execution rerun is not explicitly false");
  }

  const parsedAudits = {};
  for (const [label, file] of audits) {
    if (!fs.existsSync(file)) {
      failures.push(`${label} is missing`);
      continue;
    }
    let audit;
    try {
      audit = readJson(file);
    } catch (error) {
      failures.push(`${label} is unreadable (${error.message})`);
      continue;
    }
    parsedAudits[label] = audit;
    if (audit.verdict !== "PASS") {
      failures.push(`${label}=${audit.verdict || "missing"}${audit.reason_code ? ` (${audit.reason_code})` : ""}`);
    }
  }

  const inactiveEmpiricalSources = [
    [
      "RCEP empirical source",
      path.join(root, "manuscript_src", "natcs", "results_rcep.md"),
      /#\s*Inactive audit-boundary draft:\s*RCEP protocol/i,
    ],
    [
      "NYC empirical source",
      path.join(root, "manuscript_src", "natcs", "results_generality.md"),
      /#\s*Inactive audit-boundary draft:\s*NYC protocol/i,
    ],
  ];

  for (const [label, file, inactiveMarker] of inactiveEmpiricalSources) {
    if (!fs.existsSync(file)) {
      failures.push(`${label} is missing`);
      continue;
    }
    if (inactiveMarker.test(readText(file))) failures.push(`${label} remains explicitly inactive`);
  }

  if (failures.length) {
    throw new Error(
      `NCS_BUILD_REFUSED before evidence generation: ${failures.join("; ")}. `
      + "The source-only revision may be edited, but no manuscript, evidence, figure, archive or submission artifact was generated.",
    );
  }
}

export function writeJson(file, value) {
  writeText(file, JSON.stringify(value, null, 2));
}

function splitCsvLine(line) {
  const cells = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      cells.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  cells.push(current);
  return cells;
}

export function readCsv(file) {
  const lines = readText(file).replace(/\r\n/g, "\n").trim().split("\n");
  if (!lines.length || !lines[0]) return [];
  const header = splitCsvLine(lines[0]);
  return lines.slice(1).filter(Boolean).map((line) => {
    const cells = splitCsvLine(line);
    const row = {};
    header.forEach((key, idx) => {
      const raw = cells[idx] ?? "";
      const trimmed = raw.trim();
      if (trimmed !== "" && !Number.isNaN(Number(trimmed))) {
        row[key] = Number(trimmed);
      } else {
        row[key] = raw;
      }
    });
    return row;
  });
}

function csvEscape(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function writeCsv(file, rows) {
  if (!rows.length) {
    writeText(file, "");
    return;
  }
  const header = Object.keys(rows[0]);
  const lines = [header.join(",")];
  for (const row of rows) {
    lines.push(header.map((key) => csvEscape(row[key])).join(","));
  }
  writeText(file, `${lines.join("\n")}\n`);
}

export function formatFixed(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  return Number(value).toFixed(digits);
}

export function formatSmall(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  if (Math.abs(value) >= 0.001) return Number(value).toFixed(6);
  return Number(value).toExponential(3);
}

export function formatPValue(value, digits = 3) {
  if (value === null || value === undefined || value === "" || Number.isNaN(Number(value))) return "";
  const numeric = Number(value);
  const threshold = 10 ** -digits;
  if (numeric >= 0 && numeric < threshold) return `<${threshold.toFixed(digits)}`;
  return numeric.toFixed(digits);
}

export function markdownTable(headers, rows) {
  const headerLine = `| ${headers.join(" | ")} |`;
  const sepLine = `| ${headers.map(() => "---").join(" | ")} |`;
  const bodyLines = rows.map((row) => `| ${row.map((cell) => String(cell ?? "")).join(" | ")} |`);
  return [headerLine, sepLine, ...bodyLines].join("\n");
}

export function renderTemplate(text, context) {
  return text.replace(/\{\{([a-zA-Z0-9_]+)\}\}/g, (_, key) => {
    if (!(key in context)) throw new Error(`Missing template key: ${key}`);
    return String(context[key]);
  });
}

export function runCommand(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    encoding: "utf8",
    stdio: options.stdio ?? "pipe",
  });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with status ${result.status}\n${result.stdout ?? ""}\n${result.stderr ?? ""}`);
  }
  return result;
}

let crcTable = null;

function getCrcTable() {
  if (crcTable) return crcTable;
  crcTable = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) {
      c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    }
    crcTable[n] = c >>> 0;
  }
  return crcTable;
}

function crc32(buffer) {
  let crc = 0xffffffff;
  const table = getCrcTable();
  for (const value of buffer) {
    crc = table[(crc ^ value) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function makePngChunk(type, data) {
  const typeBuf = Buffer.from(type, "ascii");
  const lengthBuf = Buffer.alloc(4);
  lengthBuf.writeUInt32BE(data.length, 0);
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([lengthBuf, typeBuf, data, crcBuf]);
}

export function setPngDpi(file, dpi = 900) {
  const png = fs.readFileSync(file);
  const signature = png.subarray(0, 8);
  if (!signature.equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) {
    throw new Error(`Not a PNG file: ${file}`);
  }
  const ppm = Math.round(dpi / 0.0254);
  const physData = Buffer.alloc(9);
  physData.writeUInt32BE(ppm, 0);
  physData.writeUInt32BE(ppm, 4);
  physData.writeUInt8(1, 8);
  const physChunk = makePngChunk("pHYs", physData);
  const chunks = [signature];
  let offset = 8;
  let inserted = false;
  while (offset < png.length) {
    const length = png.readUInt32BE(offset);
    const type = png.subarray(offset + 4, offset + 8).toString("ascii");
    const end = offset + 12 + length;
    const chunk = png.subarray(offset, end);
    if (type === "pHYs") {
      if (!inserted) {
        chunks.push(physChunk);
        inserted = true;
      }
    } else {
      chunks.push(chunk);
      if (type === "IHDR" && !inserted) {
        chunks.push(physChunk);
        inserted = true;
      }
    }
    offset = end;
  }
  fs.writeFileSync(file, Buffer.concat(chunks));
}

// Shared reader-facing text hygiene and document scaffolding for the active
// manuscript and Supplementary builders. Moved out of the manuscript builder
// so the source-only Supplementary builder can use the same guarantees
// without importing any empirical composition code.

export function readerFacingSubmissionText(text) {
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

export function internalObjectPattern() {
  return /(^|[^A-Za-z0-9_])(s[\s_-]+net[\s_-]+raw|s[\s_-]+net[\s_-]+clip|g[\s_-]+net|Agg[\s_-]+g[\s_-]+net|net[\s_-]+clip|net[\s_-]+raw|gnet|Pair_[A-Z]{3}<-[A-Z]{3}_s_net(?:_clip|_raw)?)(?![A-Za-z0-9_])/i;
}

export function assertReaderFacingTextClean(label, text) {
  const source = String(text ?? "");
  const incomplete = /\{\{[A-Za-z0-9_]+\}\}|\b(?:undefined|NaN|Infinity)\b/.exec(source);
  if (incomplete) {
    const start = Math.max(0, incomplete.index - 80);
    const end = Math.min(source.length, incomplete.index + incomplete[0].length + 120);
    const excerpt = source.slice(start, end).replace(/\s+/g, " ");
    throw new Error(`Reader-facing text contains an unresolved value in ${label}: ${excerpt}`);
  }
  const pattern = internalObjectPattern();
  const match = pattern.exec(source);
  if (!match) return;
  const start = Math.max(0, match.index - 80);
  const end = Math.min(source.length, match.index + match[0].length + 120);
  const excerpt = source.slice(start, end).replace(/\s+/g, " ");
  throw new Error(`Reader-facing text contains an internal propagation variable in ${label}: ${excerpt}`);
}

export function yamlHeader(meta, options = {}) {
  const srcDir = options.srcDir;
  if (!srcDir) {
    throw new Error("yamlHeader requires options.srcDir for bibliography and CSL resolution");
  }
  const authorLines = options.singleLineAuthors
    ? [`author: "${meta.authors.join("        ")}"`]
    : [
        "author:",
        ...meta.authors.map((name) => `  - "${name}"`),
      ];
  const lines = [
    "---",
    `title: "${meta.title}"`,
    ...authorLines,
    'date: ""',
    "documentclass: article",
    "fontsize: 11pt",
    "geometry: margin=1in",
    "numbersections: true",
    `bibliography: "${path.join(srcDir, "references.bib")}"`,
    `csl: "${path.join(srcDir, "nature.csl")}"`,
    "header-includes:",
    "  - \\usepackage{booktabs}",
    "  - \\usepackage{longtable}",
    "  - \\usepackage{float}",
    "  - \\usepackage{placeins}",
    "  - \\usepackage{graphicx}",
    "  - \\usepackage{setspace}",
    "  - \\usepackage{indentfirst}",
    "  - \\onehalfspacing",
    "  - \\setlength{\\parindent}{2em}",
    "  - \\renewcommand{\\topfraction}{0.95}",
    "  - \\renewcommand{\\bottomfraction}{0.9}",
    "  - \\renewcommand{\\textfraction}{0.05}",
    "  - \\renewcommand{\\floatpagefraction}{0.85}",
    "  - \\setlength{\\textfloatsep}{12pt plus 2pt minus 2pt}",
    "  - \\setlength{\\floatsep}{10pt plus 2pt minus 2pt}",
    "  - \\makeatletter",
    "  - \\setlength{\\@fptop}{0pt}",
    "  - \\setlength{\\@fpsep}{10pt plus 1fil}",
    "  - \\setlength{\\@fpbot}{0pt plus 1fil}",
    "  - \\makeatother",
    "---",
    "",
  ];
  return lines.join("\n");
}

export function referencesBlock(sections) {
  const joined = sections.filter(Boolean).join("\n");
  if (!/\[@[A-Za-z0-9:_-]+/.test(joined)) return [];
  return [
    "# References {-}",
    "",
    "::: {#refs}",
    ":::",
    "",
  ];
}
