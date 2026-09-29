import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checklistPath = path.join(root, "manuscript_src/natcs/ncs_fig2_portal_preview_checklist.md");
const finalGatesPath = path.join(root, "scripts/check_natcs_final_gates.mjs");
const surrogateBuilderPath = path.join(root, "scripts/build_natcs_fig2_portal_surrogate.py");
const figureQaMemoPath = path.join(root, "manuscript_src/natcs/ncs_figure_qa_memo.md");
const checklist = fs.readFileSync(checklistPath, "utf8");
const finalGates = fs.readFileSync(finalGatesPath, "utf8");
const surrogateBuilder = fs.readFileSync(surrogateBuilderPath, "utf8");
const figureQaMemo = fs.readFileSync(figureQaMemoPath, "utf8");

assert.match(checklist, /Figure 2 Portal Preview Checklist \(Disabled\)/i);
assert.match(checklist, /PAPER_CLAIM_AUDIT=BLOCKED/i);
assert.match(checklist, /EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL/i);
assert.doesNotMatch(checklist, /Current local PDF page:/i);
assert.match(finalGates, /function checkFig2PortalPreviewDisabled\(\)/, "The final gate must verify disabled status without treating historical previews as current evidence.");
assert.doesNotMatch(finalGates, /Current local PDF page:\\s\*`\(\\d\+\)`/, "The final gate must not require a stale manuscript page reference.");
assert.match(surrogateBuilder, /def require_releaseable_fig2_preview\(\)/, "The portal surrogate must reject inactive source drafts before any preview write.");
assert.doesNotMatch(surrogateBuilder, /page-0?6\.png/, "The portal surrogate must not hard-code a manuscript page number.");
assert.doesNotMatch(figureQaMemo, /Fig\. 2(?: on)?[^\n]*page-\d+\.png/i, "The Figure 2 QA memo must not hard-code a rendered page reference.");

console.log("Fig. 2 portal-preview disablement test passed.");
