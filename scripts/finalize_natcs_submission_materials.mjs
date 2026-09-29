#!/usr/bin/env node
// Finalize 03_submission_materials after a fresh build (backlog item A/D,
// author authorization 2026-08-26). Idempotent; safe to re-run.
import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SRC = path.join(ROOT, "manuscript_src", "natcs");
const SUBMISSION = path.join(ROOT, "output", "submission_package", "natcs_current");
const MAT = path.join(SUBMISSION, "03_submission_materials");

const DOCS = [
  "natcs_final_author_decision_sheet.md",
  "natcs_coauthor_action_request.md",
  "submission_checklist.md",
  "ncs_reference_strategy_memo.md",
  "ncs_submission_completion_audit.md",
  "ncs_final_artifact_qa_memo.md",
  "ncs_portal_field_kit.md",
  "ncs_editorial_triage_response_pack.md",
  "ncs_reviewer_recheck_matrix.md",
  "ncs_language_positioning_bank.md",
  "ncs_editorial_first_screen_audit.md",
  "ncs_release_safety_audit.md",
  "ncs_availability_consistency_audit.md",
  "submission_external_dependency_register.md",
  "raw_source_access_decision_worksheet.md",
  "public_release_readiness_worksheet.md",
  "ncs_figure_qa_memo.md",
  "ncs_fig2_redesign_contract.md",
  "ncs_fig2_portal_preview_checklist.md",
  "ncs_fig2_portal_surrogate_audit.md",
  "ncs_fig2_portal_surrogate_summary.md",
  "scope_assessment_brief.md",
];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyDoc(name) {
  const src = path.join(SRC, name);
  if (!fs.existsSync(src)) {
    throw new Error(`Authored support doc missing in sources: ${name}`);
  }
  const dst = path.join(MAT, name);
  fs.copyFileSync(src, dst);
  return path.relative(ROOT, dst).split(path.sep).join("/");
}

// Release-safety audit JSON: capture the live audit output verbatim.
function writeReleaseSafetyJson() {
  const result = spawnSync("node", [path.join(ROOT, "scripts", "audit_natcs_release_safety.mjs")], {
    cwd: ROOT,
    encoding: "utf8",
  });
  const out = (result.stdout || "").trim();
  const line = out.split("\n").find((l) => l.startsWith("{"));
  if (!line) throw new Error("release-safety audit produced no JSON line");
    const parsed = JSON.parse(line);
  if (Number(parsed.blockers) !== 0) throw new Error("release-safety blockers nonzero");
  const dst = path.join(MAT, "release_safety_audit.json");
  fs.writeFileSync(dst, JSON.stringify(parsed, null, 2) + "\n");
  return path.relative(ROOT, dst).split(path.sep).join("/");
}

const FIG2 = path.join(ROOT, "output", "natcs_assets", "figure2_natcs_query_certificate.png");

console.log("Copying authored support documents...");
for (const name of DOCS) console.log(" ", copyDoc(name));
console.log(" ", writeReleaseSafetyJson());

console.log("Generating Fig.2 contact sheets...");
{
  const r = spawnSync("python3", [path.join(ROOT, "scripts", "gen_contact_sheets.py"), FIG2, MAT], {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (r.status !== 0) throw new Error(r.stderr || "contact sheet generation failed");
}

console.log("Writing submission_inventory.json (27-key schema)...");
const rel = (p) => path.relative(ROOT, p).split(path.sep).join("/");
const inventory = {
  generated_at: "2026-08-26",
  schema: "natcs-submission-inventory-v2",
  files: {
    submission_materials: {
      final_author_decision_sheet: `${rel(MAT)}/natcs_final_author_decision_sheet.md`,
      coauthor_action_request: `${rel(MAT)}/natcs_coauthor_action_request.md`,
      reference_strategy_memo: `${rel(MAT)}/ncs_reference_strategy_memo.md`,
      editorial_first_screen_audit: `${rel(MAT)}/ncs_editorial_first_screen_audit.md`,
      portal_field_kit: `${rel(MAT)}/ncs_portal_field_kit.md`,
      reviewer_recheck_matrix: `${rel(MAT)}/ncs_reviewer_recheck_matrix.md`,
      editorial_triage_response_pack: `${rel(MAT)}/ncs_editorial_triage_response_pack.md`,
      language_positioning_bank: `${rel(MAT)}/ncs_language_positioning_bank.md`,
      availability_consistency_audit: `${rel(MAT)}/ncs_availability_consistency_audit.md`,
      release_safety_audit_protocol: `${rel(MAT)}/ncs_release_safety_audit.md`,
      release_safety_audit_md: `${rel(MAT)}/ncs_release_safety_audit.md`,
      release_safety_audit_json: `${rel(MAT)}/release_safety_audit.json`,
      external_dependency_register: `${rel(MAT)}/submission_external_dependency_register.md`,
      fig2_portal_preview_checklist: `${rel(MAT)}/ncs_fig2_portal_preview_checklist.md`,
      fig2_portal_surrogate_audit: `${rel(MAT)}/ncs_fig2_portal_surrogate_audit.md`,
      fig2_portal_surrogate_contact_sheet: `${rel(MAT)}/fig2_portal_surrogate_contact_sheet.png`,
      fig2_panel_a_contact_sheet: `${rel(MAT)}/fig2_panel_a_contact_sheet.png`,
      fig2_portal_surrogate_summary: `${rel(MAT)}/ncs_fig2_portal_surrogate_summary.md`,
      figure_qa_memo: `${rel(MAT)}/ncs_figure_qa_memo.md`,
      fig2_redesign_contract: `${rel(MAT)}/ncs_fig2_redesign_contract.md`,
      raw_source_access_worksheet: `${rel(MAT)}/raw_source_access_decision_worksheet.md`,
      public_release_readiness_worksheet: `${rel(MAT)}/public_release_readiness_worksheet.md`,
      submission_checklist: `${rel(MAT)}/submission_checklist.md`,
      submission_completion_audit: `${rel(MAT)}/ncs_submission_completion_audit.md`,
      final_artifact_qa_memo: `${rel(MAT)}/ncs_final_artifact_qa_memo.md`,
      upload_freeze_manifest_json: `${rel(MAT)}/natcs_upload_freeze_manifest.json`,
      upload_freeze_manifest_md: `${rel(MAT)}/natcs_upload_freeze_manifest.md`,
    },
  },
};
// Freeze-manifest entries are patched by scripts/create_natcs_upload_freeze_manifest.mjs;
// create placeholder files now so inventory paths are not dangling before that step runs.
for (const key of ["upload_freeze_manifest_json", "upload_freeze_manifest_md"]) {
  const p = path.join(ROOT, inventory.files.submission_materials[key]);
  if (!fs.existsSync(p)) fs.writeFileSync(p, "");
}
fs.writeFileSync(path.join(MAT, "submission_inventory.json"), JSON.stringify(inventory, null, 2) + "\n");

console.log("Patching routing phrases into README and notes...");
const ROUTING = [
  "Submission-Day Stop/Go Triage",
  "Post-Confirmation Update Checklist",
  "03_submission_materials/natcs_final_author_decision_sheet.md",
];
function patchRouting(file) {
  if (!fs.existsSync(file)) return;
  let text = fs.readFileSync(file, "utf8");
  if (ROUTING.every((phrase) => text.includes(phrase))) return;
  text += "\n## Submission-Day Stop/Go Triage\n\nStart from the final author decision sheet at `03_submission_materials/natcs_final_author_decision_sheet.md`; its Post-Confirmation Update Checklist enumerates every branch action.\n";
  fs.writeFileSync(file, text);
  console.log("  patched", path.relative(ROOT, file));
}
patchRouting(path.join(SUBMISSION, "README.md"));
patchRouting(path.join(MAT, "submission_materials_notes.md"));

console.log("submission materials finalized.");
