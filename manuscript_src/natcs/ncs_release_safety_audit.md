# NCS Release Safety Audit Protocol

Purpose: define the local safety scan that runs before reviewer/archive transfer or acceptance-stage public release, and record the current release-safety posture. This is a submission-support artifact. It is manuscript-neutral text, is not evidence of source-provider permission, and adds no availability claim.

Protocol version: 2026-08-26 refresh of the 2026-07-07 protocol.

Serves: reproducibility / rigour / clarity.

## Current Posture (2026-08-26)

The audit runs clean today. The latest pass over the four package roots recorded 0 blockers and 0 warnings, and the final-gate checker reports the release-safety scanner as passing in check mode. This clean result reflects package hygiene at scan time; it is a snapshot that must be re-earned after every rebuild, because any later edit that introduces a credential-like string, a sensitive filename or a private absolute path into a scanned root re-fatalizes the gates.

Standing requirements enforced downstream:

1. `output/submission_package/natcs_current/03_submission_materials/release_safety_audit.json` must parse and carry `blocker_count === 0`.
2. `node scripts/audit_natcs_release_safety.mjs --check` must exit 0 against the live roots.
3. Zero warnings must hold at gate time: the final-gate residual-warning allowlist recognizes only four external-gate counters, so any private-path warning found by this scanner becomes an unexpected final-gate warning and fails the run.

## Generated Outputs

- Markdown audit: `output/submission_package/natcs_current/03_submission_materials/release_safety_audit.md`
- JSON audit: `output/submission_package/natcs_current/03_submission_materials/release_safety_audit.json`
- Script: `scripts/audit_natcs_release_safety.mjs`

The JSON and Markdown pair is machine-generated. It is distinct from this protocol document: the submission inventory references the generated pair under the keys `release_safety_audit_md` and `release_safety_audit_json`, and references this protocol under the key `release_safety_audit_protocol`.

## Boundary

This audit is pattern-based. It checks visible reviewer/upload-facing package roots for private paths, sensitive filenames and credential-like content. It does not prove legal redistributability, source-provider permissions, DOI assignment, licence compatibility or absence of every conceivable secret. Raw-source access and public-release decisions stay with the dedicated worksheets.

## Scan Scope

The audit walks these package roots when present:

| Root | Role | Review target |
| --- | --- | --- |
| `output/reviewer_archive/natcs_reviewer_archive` | Separate reviewer code-and-derived-evidence archive. | reproducibility / rigour |
| `output/submission_package/natcs_current` | Generated manuscript, Supplementary Information and submission support materials, including the copied support documents. | clarity / reproducibility |
| `output/figure_source_package/natcs_main_figure_sources` | Standalone main-figure source bundle and figure QA notes. | visual communication / rigour |
| `output/integrated_package/latest_submission_upload_word_only` | Latest Word-only upload directory. | clarity / reproducibility |

Text files are scanned for content patterns; binary files are skipped after extension, dataless-flag and null-byte screening.

## What The Audit Flags

| Finding class | Severity | Why it matters | Required action |
| --- | --- | --- | --- |
| Sensitive filenames, e.g. dotfile environment files, identity-key files or names carrying secret/credential/password/private-key/api-key/access-token vocabulary. | Blocker | Such names often indicate credentials or non-release-safe material. | Inspect and remove or rename before transfer. |
| Private-key blocks, vendor token shapes, cloud access-key shapes and credential-style assignment strings. | Blocker | Credential-like content must reach neither reviewers nor public repositories. | Remove, rotate when real, and rerun the audit. |
| Private absolute user-home paths of the macOS form, `/home/<name>/...` paths or drive-letter user form. | Warning | Private paths reduce reproducibility and expose local machine structure. | Replace with repository-relative paths, then rerun to restore the zero-warning standing. |

Every warning class matters at gate time: the final-gate allowlist admits no release-safety warning, so a single finding of the third class blocks the package exactly like a blocker would.

## Current Use Rule

Run `node scripts/audit_natcs_release_safety.mjs` after the reviewer archive, submission package, figure-source package and latest upload directory have been regenerated. The upload-freeze manifest step runs this write-mode audit before hashing the submission inventory. The final-gate checker then reruns `node scripts/audit_natcs_release_safety.mjs --check` in read-only mode and treats any blocker as fatal.

Do not use this audit to strengthen Data availability or Code availability claims. It verifies release hygiene alone. Under the 2026-08-26 governance state (both controlling audits PASS with reason codes in the `rcep_nyc_value_audited` family), the clean scan authorizes hygiene for transfer preparation and nothing else: manuscript promotion stays unauthorized (RC-1, NOT_GRANTED), empirical claim activation stays gated behind the open characterization flags (RC-2), and raw-source plus public-release worksheets remain OPEN pending author confirmation.

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
