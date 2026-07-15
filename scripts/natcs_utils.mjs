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
