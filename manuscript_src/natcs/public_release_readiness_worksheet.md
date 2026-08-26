# Public Release Readiness Worksheet

Purpose: author-facing checklist for finalizing the acceptance-stage DOI-minting release promised in the Data availability and Code availability statements. This is a working document and should stay out of the upload set unless completed and checked by the authors.

Boundary: this worksheet does not claim that a public DOI, repository or licence exists today. It records the decisions needed before manuscript text can move from "will deposit" to a specific public-release identifier.

Status 2026-08-26: every release-decision row below remains OPEN pending author confirmation. The 2026-08-26 audit chain (both controlling audits PASS under `rcep_nyc_value_audited` reason codes) authorizes the downstream rebuild chain alone and creates no public-release right or identifier.

Serves: reproducibility / rigour / clarity.

## Current Manuscript Claim

The current submission uses a conservative future-release statement: on acceptance, the authors will deposit the redistributable code-and-derived-evidence release in a DOI-minting repository and update the public-release record with the assigned persistent identifier, licence and access terms.

Do not replace this statement with a DOI, repository name or licence until the corresponding row below is confirmed.

## Submission-Day Quick Decision

Use this quick decision before editing Data availability, Code availability, Supplementary Note 7 or any portal field.

| Current release state | Manuscript wording to use now | Immediate action |
| --- | --- | --- |
| No repository, DOI, licence or access terms are assigned. | Keep future-tense DOI-minting language. | Leave Data/Code availability unchanged; complete this worksheet after author decisions. |
| A reviewer archive exists for peer review, with no public deposit. | Describe the archive only as a journal-approved peer-review route. | Avoid describing the archive as a public release. |
| A repository route exists while DOI or licence remain pending. | Use repository language only if the journal asks for a concrete pre-publication route. | Record pending fields here and keep final DOI/licence wording out of the manuscript. |
| Repository, DOI, licence, access terms and release contents are all confirmed. | Replace future-tense text with the actual repository, DOI, licence, access terms and exclusions. | Update Data availability, Code availability and Supplementary Note 7 together, then rebuild and rerun final gates. |

## Author Action for This Revision

Before any acceptance-stage wording is inserted, record three decisions:

1. Which files are included, excluded or waiting for licence/source checks.
2. Which repository, DOI, licence and embargo/public-timing choices are confirmed.
3. Which exact manuscript files must be updated after the public record exists.

While any item below remains unresolved, keep the formal manuscript language in future tense and keep the public-release promise bounded to redistributable code and derived evidence.

## Release Decision Table

| Release item | Required decision before acceptance-stage update | Current default | Author decision | Evidence needed |
| --- | --- | --- | --- | --- |
| DOI-minting repository | Choose a repository or archive route: institutional repository, Zenodo, Figshare, OSF or a journal-approved archive. | No repository or DOI is named in the manuscript; keep future-tense DOI-minting language. | Unresolved; author to choose repository. | Repository URL, deposit policy, DOI-minting confirmation. |
| Release title | Decide the public-release title and whether it matches the manuscript title. | `Query-certified operator learning for evolving weighted networks: code and derived evidence` | Unresolved; author to confirm final title and author list. | Final title and author list. |
| Code licence | Choose a licence for redistributable scripts. | No licence is named in the manuscript. | Unresolved; author/institution to choose licence. | Co-author and institution approval; dependency compatibility. |
| Derived-evidence data licence | Choose access terms for redistributable derived panels, benchmark outputs, bootstrap outputs, figures and checksums. | No derived-evidence licence is named in the manuscript. | Unresolved pending provider-term check. | Provider-term check; raw-source worksheet decisions. |
| Restricted raw inputs | Decide whether raw files are included, linked publicly, supplied only by provider route, or excluded. | Exclude restricted raw files unless author-confirmed otherwise. | Unresolved; default is exclusion from public release. | Completed raw-source access worksheet. |
| RCEP helper checkout | Decide whether to release a cleaned helper, replace it with public scripts, or leave it out with acquisition notes only. | Not redistributed. | Unresolved; default is acquisition notes only. | Credential/private-code audit; dependency/licence audit. |
| NYC Taxi upstream route | Confirm whether the upstream commit and TLC route stay accessible, and whether an archived snapshot or DOI is needed. | Public route recorded; no archive DOI named. | Unresolved for archival route; public route suffices for bounded wording. | URL/commit availability check; optional archival DOI. |
| Environment files | Decide which lock files, environment snapshots and version records ship. | Include reviewer-archive environment files. | Provisionally include; author to confirm final release contents. | Clean-copy rebuild log and manifest. |
| Checksums | Decide which regenerated artifacts receive checksums in the public release. | Include manuscript-facing evidence checksums. | Provisionally include; author to confirm after the final rebuild. | Current checksum records. |
| Release embargo | Decide whether the release goes public on acceptance, on publication, or stays reviewer-only during peer review. | Public-release update on acceptance. | Unresolved; author to confirm against journal policy. | Journal policy and author preference. |

## Minimal Public-Release Manifest

Use this as the public-deposit contents checklist. Do not mark an item as `Include` until its licence and provenance fields have been checked.

| Component | Include / Exclude / Needs licence check | Upload-safe default | Licence/provenance check needed | Availability wording consequence |
| --- | --- | --- | --- | --- |
| Estimator, simulation and benchmark scripts | Include if dependency licences permit | Include redistributable scripts only | Software licence; dependency compatibility; zero private paths or credentials. | Code availability may name the public repository only after the release exists. |
| Empirical pipeline scripts that run on derived inputs | Include if derived inputs are redistributable | Include scripts that run on bundled derived objects | Confirm the submitted-evidence mode needs no restricted raw files. | Supports derived-evidence reproducibility; implies nothing about raw-to-derived reproducibility. |
| Figure-generation and manuscript-evidence build scripts | Include | Include | Confirm they match final submitted figures/tables and checksums. | Supports manuscript-facing evidence rebuild. |
| Derived quarterly trade panel and time-indexed network matrices | Needs licence check | Exclude from public release until provider-term implications are confirmed | Raw-source worksheet decisions; provenance and transformation notes. | Keep derived-evidence wording tied to the shipped archive; public wording only after rights are confirmed. |
| Derived tariff-relief panel and association outputs | Needs licence check | Exclude from public release until source/provider terms are checked | Official schedule/import-record access terms; provenance notes. | Do not state public availability unless the panel can be redistributed. |
| Derived MRIO exposure variables | Needs licence check | Exclude unless the MRIO licence permits derived redistribution | MRIO licence and transformation notes. | Keep restricted-boundary wording while the licence stays unresolved. |
| Derived NYC Taxi monthly panel and acquisition JSON | Needs licence check | Include only if upstream and derived-panel terms permit | Upstream commit, TLC route and derived-panel licence. | Public-route wording may strengthen only with licence/archival confirmation. |
| Benchmark summaries, bootstrap outputs and operator-check tables | Include if generated by redistributable scripts/inputs | Include manuscript-facing derived outputs | Confirm zero restricted raw values embedded. | Supports reproducibility of reported numerical summaries. |
| Environment files, manifests, checksums and reproduction entry points | Include | Include | Confirm portable paths and checksums matching the final release. | Supports code availability and reviewer/public rerun instructions. |
| Acquisition notes for non-redistributed raw inputs | Include | Include notes; exclude restricted files | Confirm notes expose zero private credentials or non-public provider material. | Supports a transparent raw-to-derived boundary without claiming raw-file access. |
| Provider-restricted IMF, tariff, bilateral trade and licensed MRIO raw files | Exclude unless permissions are confirmed | Exclude | Completed raw-source worksheet plus reviewer/public route if any exception is made. | Keep the formal statement explicit that these raw files are unbundled. |
| RCEP helper checkout | Exclude or replace with clean route | Exclude | Credential/private-path audit; ownership and dependency licences; tested replacement if any. | Do not claim helper availability unless a clean route exists and passes. |
| README, file manifest and data dictionary | Include | Include | Map files to figures/tables, variables, units, missing values and reproduction modes. | Required before a DOI release can credibly support NCS reproducibility expectations. |

## Current Package Evidence Snapshot

This snapshot records what the visible package supports today. It makes no public-release claim.

| Evidence item | Current support | Manuscript wording allowed now |
| --- | --- | --- |
| Reviewer archive | Assembled as a peer-review code-and-derived-evidence archive with scripts, derived objects, environment files, manifests, checksums and reproduction entry points, frozen to its build version. | State that an archive is available through the journal-approved route, tied to the uploaded version. |
| Submitted-evidence rebuild | The Code availability statement names the submitted-evidence rebuild commands and records a clean-copy local execution. | State derived-evidence reproducibility for manuscript-facing outputs. |
| Raw-to-derived acquisition | Documented and externally constrained by provider access terms and helper-checkout boundaries. | Keep raw-to-derived rebuilding outside the default reviewer path. |
| Public DOI release | Planned for acceptance; no DOI, repository, licence or access terms assigned anywhere in the package. | Future tense only: "will deposit ... in a DOI-minting repository". |
| Restricted files | Zero author-confirmed permission recorded for redistributing restricted IMF, tariff, bilateral trade, licensed MRIO or helper-code inputs. | Exclude restricted raw inputs unless the raw-source worksheet closes otherwise. |

## Acceptance-Stage Text Update Rules

Update manuscript text only after the release exists or the journal asks for a concrete pre-publication repository record.

| If release status is... | Data availability action | Code availability action | Supplementary action |
| --- | --- | --- | --- |
| DOI assigned | Replace future-tense deposit language with DOI, repository name, licence and access terms. | Add DOI and specify code licence. | Update Supplementary Note 7 with public-release contents and commands. |
| Repository created, DOI pending | State repository route only if journal permits pending-DOI language. | Keep "will update with DOI" until assignment. | Record pending status in a release note, never as a final identifier. |
| Reviewer-only archive during peer review | Keep current archive wording. | Keep current route wording. | Never describe the archive as a public release. |
| Release blocked by source terms | Keep the derived-evidence release only and state restricted raw-source boundaries. | Include only redistributable scripts and derived objects. | Cross-reference the raw-source access worksheet and acquisition notes. |

## Pre-Deposit Audit

Complete before uploading the public release.

| Check | Status: Confirmed / Unresolved | Author note |
| --- | --- | --- |
| No restricted raw files included without permission. | Unresolved | TODO |
| No credentials, API keys, private paths or institution-only caches included. | Unresolved | TODO |
| Public release contents match the final submitted manuscript version. | Unresolved | TODO |
| Manifest lists reproduction modes and expected runtime boundaries. | Unresolved | TODO |
| Checksums correspond to final release files. | Unresolved | TODO |
| README states raw-to-derived limitations without weakening the derived-evidence claim. | Unresolved | TODO |
| Licence files present and compatible with dependencies and source-provider terms. | Unresolved | TODO |
| DOI, repository URL and access terms recorded for manuscript update. | Unresolved | TODO |

## Pre-Deposit Blocker Checks

Treat these as blockers for a public DOI release. A blocker does not prevent submission under the current bounded future-tense language; it prevents moving the manuscript to a concrete public-release claim.

| Blocker check | Passing evidence | If not passed |
| --- | --- | --- |
| Release-safety scan reports zero blockers and zero warnings. | The generated audit pair in the submission materials for the final release candidate. | Remove credentials, private paths, sensitive filenames or restricted files before deposit. |
| Raw-source worksheet complete for every source block represented in the public release. | Final status option, evidence reference and author initials/date filled per block. | Exclude the affected files or keep them as acquisition notes only. |
| Licence and rights fields explicit for code and each released derived-data family. | Licence file plus README/access-term fields. | Do not apply open licences to third-party-derived data before rights are confirmed. |
| Public release matches the final manuscript version. | Manifest/checksum record dated after the final build. | Rebuild, regenerate checksums and update the README before deposit. |
| Repository private-review link or final DOI tested outside the author account. | External access check recorded with date. | Keep the link or DOI out of manuscript text. |
| Restricted raw files and helper code absent unless specifically cleared. | Manifest review plus the release-safety audit. | Remove the files or document the exact reviewer-controlled route. |

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
