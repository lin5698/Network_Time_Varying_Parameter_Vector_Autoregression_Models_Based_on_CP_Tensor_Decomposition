# Release Safety Audit Protocol

Purpose: describe the local safety scan run before reviewer/archive transfer or acceptance-stage public release. This is a submission-support artifact, not manuscript text and not evidence of source-provider permission.

Audit date: 2026-07-07.

Generated outputs after final gate:

- Markdown audit: `output/submission_package/natcs_current/03_submission_materials/release_safety_audit.md`
- JSON audit: `output/submission_package/natcs_current/03_submission_materials/release_safety_audit.json`
- Script: `scripts/audit_natcs_release_safety.mjs`

Boundary: this audit is pattern-based. It checks the visible reviewer/upload-facing package roots for private paths, sensitive filenames and credential-like content. It does not prove legal redistributability, source-provider permissions, DOI assignment, licence compatibility or absence of all possible secrets.

Serves: reproducibility / rigour / clarity.

## Scan Scope

The audit scans these package roots when present:

| Root | Role | Review target |
| --- | --- | --- |
| `output/reviewer_archive/natcs_reviewer_archive` | Separate reviewer code-and-derived-evidence archive. | reproducibility / rigour |
| `output/submission_package/natcs_current` | Generated manuscript, Supplementary Information and submission support materials. | clarity / reproducibility |
| `output/figure_source_package/natcs_main_figure_sources` | Standalone main-figure source bundle and figure QA notes. | visual communication / rigour |
| `output/integrated_package/latest_submission_upload_word_only` | Latest Word-only upload directory. | clarity / reproducibility |

## What The Audit Flags

| Finding class | Severity | Why it matters | Required action |
| --- | --- | --- | --- |
| Sensitive filenames such as `.env`, `.pem`, `.key`, `id_rsa`, `secret`, `token` or `credential`. | Blocker | These file names often indicate credentials or non-release-safe material. | Inspect and remove or replace before transfer. |
| Private-key blocks, AWS/GitHub/OpenAI/Slack-token-like strings and credential assignments. | Blocker | Credential-like content must not be sent to reviewers or public repositories. | Remove, rotate if real, and rerun the audit. |
| Absolute user paths such as `/Users/...`, `/home/...` or `C:\Users\...`. | Warning | Private paths reduce reproducibility and may reveal local machine structure. | Replace with relative paths unless the path appears only in local audit metadata. |

## Current Use Rule

Run `node scripts/audit_natcs_release_safety.mjs` after the reviewer archive, submission package, figure-source package and latest upload directory have been regenerated. The upload-freeze manifest script runs this write-mode audit before hashing the submission inventory. The final gate checker runs `node scripts/audit_natcs_release_safety.mjs --check` in read-only mode and treats blocker findings as submission blockers.

Do not use this audit to strengthen Data availability or Code availability claims. It only checks release hygiene; raw-source access and public DOI decisions still require the raw-source and public-release worksheets.
