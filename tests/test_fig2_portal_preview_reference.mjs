import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checklistPath = path.join(root, "manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md");
const manuscriptPdf = path.join(root, "output/pdf/natcs_manuscript.pdf");
const finalGatesPath = path.join(root, "scripts/check_natcs_final_gates.mjs");
const surrogateBuilderPath = path.join(root, "scripts/build_natcs_fig2_portal_surrogate.py");
const surrogateSummaryPath = path.join(root, "output/natcs_fig2_portal_surrogate/fig2_portal_surrogate_summary.json");
const figureQaMemoPath = path.join(root, "manuscript_src/natcs/ncs_figure_qa_memo.md");
const checklist = fs.readFileSync(checklistPath, "utf8");
const finalGates = fs.readFileSync(finalGatesPath, "utf8");
const surrogateBuilder = fs.readFileSync(surrogateBuilderPath, "utf8");
const surrogateSummary = JSON.parse(fs.readFileSync(surrogateSummaryPath, "utf8"));
const figureQaMemo = fs.readFileSync(figureQaMemoPath, "utf8");

const reference = checklist.match(/Current local PDF page:\s*`(\d+)`/);
assert.ok(reference, "Fig. 2 portal checklist must state the current local PDF page.");
assert.match(finalGates, /function checkFig2PortalPreviewReference\(\)/, "Final gate must verify the Fig. 2 portal-preview page reference.");
assert.match(surrogateBuilder, /def locate_fig2_page\(/, "Fig. 2 portal surrogate must locate the current manuscript page from the caption.");
assert.doesNotMatch(surrogateBuilder, /page-0?6\.png/, "Fig. 2 portal surrogate must not hard-code a manuscript page number.");
assert.doesNotMatch(figureQaMemo, /Fig\. 2(?: on)?[^\n]*page-\d+\.png/i, "Fig. 2 QA memo must point to the checked portal reference instead of hard-coding a page number.");

const pageCount = Number(execFileSync("pdfinfo", [manuscriptPdf], { encoding: "utf8" }).match(/^Pages:\s+(\d+)/m)?.[1]);
let detectedPage = null;
for (let page = 1; page <= pageCount; page += 1) {
  const text = execFileSync("pdftotext", ["-f", String(page), "-l", String(page), manuscriptPdf, "-"], { encoding: "utf8" });
  if (text.includes("Endpoint-preserving reconstruction keeps topology-substitution")) {
    detectedPage = page;
    break;
  }
}

assert.equal(detectedPage, Number(reference[1]), "Fig. 2 portal checklist page must match the current manuscript PDF.");
assert.equal(surrogateSummary.sources.embedded_manuscript_page_number, detectedPage, "Fig. 2 portal surrogate must use the current manuscript PDF page.");
assert.equal(surrogateSummary.sources.embedded_manuscript_page_png, `tmp/pdfs/natcs_main/page-${String(detectedPage).padStart(2, "0")}.png`, "Fig. 2 portal surrogate must record the current rendered page path.");
console.log("Fig. 2 portal-preview reference test passed.");
