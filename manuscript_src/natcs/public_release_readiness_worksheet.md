# Public Release Readiness Worksheet

Purpose: author-facing checklist for finalizing the acceptance-stage DOI-minting release promised in the Data availability and Code availability statements. This is a working document and should not be uploaded unless completed and checked by the authors.

Boundary: this worksheet does not claim that a public DOI, repository or licence already exists. It records the decisions needed before the manuscript text can be updated from "will deposit" to a specific public-release identifier.

Serves: reproducibility / rigour / clarity.

## Current Manuscript Claim

The current submission uses a conservative future-release statement: on acceptance, the authors will deposit the redistributable code-and-derived-evidence release in a DOI-minting repository and update the public-release record with the assigned persistent identifier, licence and access terms.

Do not replace this statement with a DOI, repository name or licence until the corresponding row below is confirmed.

## Submission-Day Quick Decision

Use this quick decision before editing Data availability, Code availability, Supplementary Note 7 or any portal field.

| Current release state | Manuscript wording to use now | Immediate action |
| --- | --- | --- |
| No repository, DOI, licence or access terms are assigned. | Keep future-tense DOI-minting language. | Leave Data/Code availability unchanged and complete this worksheet after author decisions. |
| Reviewer archive exists for peer review, with no public deposit yet. | Describe the reviewer archive only as a journal-approved peer-review route. | Avoid calling the reviewer archive a public release. |
| Repository route exists, with DOI or licence still pending. | Use repository language only if the journal asks for a concrete pre-publication route. | Record pending fields in this worksheet and keep final DOI/licence wording out of the manuscript. |
| Repository, DOI, licence, access terms and release contents are all confirmed. | Replace future-tense text with the actual repository, DOI, licence, access terms and exclusions. | Update Data availability, Code availability and Supplementary Note 7 together, then rebuild and rerun final gates. |

## Author Action for This Revision

Before any acceptance-stage wording is inserted, record three decisions:

1. Which files are included, excluded or waiting for licence/source checks.
2. Which repository, DOI, licence and embargo/public-timing choices are confirmed.
3. Which exact manuscript files must be updated after the public record exists.

If any item below remains unresolved, keep the formal manuscript language in future tense and keep the public-release promise bounded to redistributable code and derived evidence.

## Release Decision Table

| Release item | Required decision before acceptance-stage update | Current default | Author decision | Evidence needed |
| --- | --- | --- | --- | --- |
| DOI-minting repository | Choose repository or archive route, e.g. institutional repository, Zenodo, Figshare, OSF or journal-approved archive. | No repository or DOI is named in the manuscript; keep future-tense DOI-minting language. | Unresolved; author to choose repository. | Repository URL, deposit policy, DOI-minting confirmation. |
| Release title | Decide the public-release title and whether it matches the manuscript title. | `When reconstructed network models retain topology-dependent responses: code and derived data` | Unresolved; author to confirm final title and author list. | Final title and author list. |
| Code licence | Choose a licence for redistributable scripts. | No licence is named in the manuscript. | Unresolved; author/institution to choose licence. | Co-author and institution approval; dependency compatibility. |
| Derived-evidence data licence | Choose access terms for redistributable derived panels, benchmark outputs, bootstrap outputs, figures and checksums. | No derived-evidence licence is named in the manuscript. | Unresolved pending provider-term check. | Provider-term check; raw-source worksheet decisions. |
| Restricted raw inputs | Decide whether any raw files can be included, linked publicly, supplied only by provider route, or excluded. | Exclude restricted raw files unless author-confirmed otherwise. | Unresolved; default is exclusion from public release. | Completed raw-source access worksheet. |
| RCEP helper checkout | Decide whether to release a cleaned helper, replace it with public scripts, or leave it out with acquisition notes only. | Not redistributed. | Unresolved; default is acquisition notes only. | Credential/private-code audit; dependency/licence audit. |
| NYC Taxi upstream route | Confirm whether the upstream repository commit and TLC route remain accessible, and whether an archived snapshot or DOI is needed. | Public route recorded; no archive DOI named. | Unresolved for archival route; public route currently sufficient for bounded wording. | URL/commit availability check; optional archival DOI. |
| Environment files | Decide which lock files, environment snapshots and version records are included. | Include reviewer archive environment files. | Provisionally include; author to confirm final release contents. | Clean-copy rebuild log and manifest. |
| Checksums | Decide which regenerated artifacts receive checksums in the public release. | Include manuscript-facing evidence checksums. | Provisionally include; author to confirm after final rebuild. | Current checksum records. |
| Release embargo | Decide whether the release is public on acceptance, public on publication, or available to reviewers during peer review only. | Public-release update on acceptance. | Unresolved; author to confirm against journal policy. | Journal policy and author preference. |

## Minimal Public-Release Manifest

Use this as the public-deposit contents checklist. Do not mark an item as `Include` until the licence and provenance fields have been checked.

| Component | Include / Exclude / Needs licence check | Upload-safe default | Licence/provenance check needed | Availability wording consequence |
| --- | --- | --- | --- | --- |
| Estimator, simulation and benchmark scripts | Include if dependency licences permit | Include redistributable scripts only | Software licence; dependency compatibility; no private paths or credentials. | Code Availability may name the public repository only after the release exists. |
| Empirical CP and operator-recovery scripts using derived inputs | Include if derived inputs are redistributable | Include scripts that run on bundled derived objects | Confirm scripts do not require restricted raw files for submitted-evidence mode. | Supports derived-evidence reproducibility; does not imply raw-to-derived reproducibility. |
| Figure-generation and manuscript-evidence build scripts | Include | Include | Confirm they match final submitted figures/tables and checksums. | Supports manuscript-facing evidence rebuild. |
| Derived quarterly trade panel and time-indexed network matrices | Needs licence check | Exclude from public release until provider-term implications are confirmed | Raw-source worksheet decisions; provenance and transformation notes. | Keep derived-evidence wording in reviewer archive; public-release wording only after rights are confirmed. |
| Derived tariff-relief panel and association outputs | Needs licence check | Exclude from public release until source/provider terms are checked | Official schedule/import-record access terms; provenance notes. | Do not state public availability unless the derived panel can be redistributed. |
| Derived MRIO exposure variables | Needs licence check | Exclude unless MRIO licence permits derived redistribution | MRIO licence and transformation notes. | Keep restricted-boundary wording if licence remains unresolved. |
| Derived NYC Taxi monthly panel and acquisition JSON | Needs licence check | Include only if upstream and derived-panel terms permit | Upstream repository commit, TLC route and derived-panel licence. | Public-route wording may be strengthened only with licence/archival confirmation. |
| Benchmark summaries, bootstrap outputs and operator-check tables | Include if generated by redistributable scripts/inputs | Include manuscript-facing derived outputs | Confirm no restricted raw values are embedded. | Supports reproducibility of reported numerical summaries. |
| Environment files, manifests, checksums and reproduction entry points | Include | Include | Confirm paths are portable and checksums correspond to final release. | Supports Code Availability and reviewer/public rerun instructions. |
| Acquisition notes for non-redistributed raw inputs | Include | Include notes, exclude restricted files | Confirm notes do not expose private credentials or non-public provider material. | Supports transparent raw-to-derived boundary without claiming raw-file access. |
| Provider-restricted IMF, tariff, bilateral trade and licensed MRIO raw files | Exclude unless permissions are confirmed | Exclude | Completed raw-source worksheet with reviewer/public route if any exception is made. | Keep formal statement explicit that these raw files are not bundled. |
| RCEP helper checkout | Exclude or replace with clean route | Exclude | Credential/private-path audit; ownership and dependency licences; tested replacement if any. | Do not claim helper availability unless clean route exists and passes. |
| README, file manifest and data dictionary | Include | Include | Map files to figures/tables, variables, units, missing values and reproduction modes. | Required before a DOI release can credibly support NCS reproducibility expectations. |

## Current Package Evidence Snapshot

This snapshot records what the visible package supports today. It is not a public-release claim.

| Evidence item | Current support | Manuscript wording allowed now |
| --- | --- | --- |
| Reviewer archive | Assembled as a peer-review code-and-derived-evidence archive with scripts, derived objects, environment files, manifests, checksums and reproduction entry points. | State that a reviewer archive is available through the journal-approved route. |
| Submitted-evidence rebuild | The Code availability statement names the submitted-evidence rebuild commands and states that a clean-copy execution passed locally. | State derived-evidence reproducibility for manuscript-facing outputs. |
| Raw-to-derived acquisition | Documented but externally constrained by provider access and helper checkouts. | Keep raw-to-derived rebuilding outside the default reviewer path. |
| Public DOI release | Planned for acceptance, with no DOI, repository, licence or access terms assigned in the visible package. | Use future tense only: "will deposit ... in a DOI-minting repository". |
| Restricted files | No author-confirmed permission is recorded for redistributing restricted IMF, tariff, bilateral trade, licensed MRIO or helper-code inputs. | Exclude restricted raw inputs unless the raw-source worksheet is completed otherwise. |

## Minimum Release Contents

The public release should include enough material to support the published claims without redistributing restricted raw inputs.

Required unless provider terms prevent release:

- Estimator scripts and synthetic benchmark scripts.
- Empirical CP pipeline scripts that operate on redistributable derived inputs.
- Figure-generation and manuscript-evidence build scripts.
- Derived quarterly trade panel used for manuscript-facing evidence, if release terms permit.
- Derived monthly NYC Taxi panel and acquisition JSON.
- Time-indexed network matrices used for manuscript-facing evidence, if release terms permit.
- Benchmark summaries, bootstrap outputs and manuscript-facing evidence tables.
- Environment files, manifest, checksum records and reproduction entry points.
- Acquisition notes for non-redistributed raw inputs.
- README that separates submitted-evidence rebuild, fresh rerun and raw-to-derived acquisition modes.

Excluded unless explicitly confirmed:

- Provider-restricted IMF, tariff, bilateral trade and licensed MRIO raw files.
- API keys, credentials, private file paths and institution-specific cache directories.
- Non-redistributable helper code or dependencies.
- Any raw-source file whose redistribution status is unresolved.

## Acceptance-Stage Text Update Rules

Update manuscript text only after the release exists or the journal asks for a concrete pre-publication repository record.

| If release status is... | Data availability action | Code availability action | Supplementary action |
| --- | --- | --- | --- |
| DOI assigned | Replace future-tense deposit language with DOI, repository name, licence and access terms. | Add DOI and specify code licence. | Update Supplementary Note 7 with public-release contents and commands. |
| Repository created but DOI pending | State repository route only if journal permits pending DOI language. | Keep "will update with DOI" unless DOI is assigned. | Record pending status in a release note, not as a final identifier. |
| Reviewer-only archive during peer review | Keep current peer-review archive wording. | Keep current reviewer-route wording. | Do not describe reviewer archive as public release. |
| Release blocked by source terms | Keep derived-evidence release only and state restricted raw-source boundaries. | Include only redistributable scripts and derived objects. | Cross-reference raw-source access worksheet and acquisition notes. |

## Acceptance-Stage Text Update Checklist

When the release record exists, update the manuscript in this order. Leave any line unchanged if the required evidence is missing.

| Text location | Update only after | Exact update to make | If unresolved |
| --- | --- | --- | --- |
| `data_availability.md` | Repository landing page, DOI/accession, release title, file scope and data licence/access terms exist. | Replace future-tense deposit sentence with repository name, DOI/accession, release title, licence/access terms and exclusions for restricted raw sources. | Keep future-tense DOI-minting language. |
| `code_availability.md` | Code release exists and software licence is approved. | Add repository DOI/accession, software licence, version/tag and reviewer/public execution modes. | Keep reviewer-archive wording and acceptance-stage deposit promise. |
| Supplementary Note 7 / reproducibility appendix | Public release contents and commands match final files. | Add public-release command set, expected inputs, runtime boundary and raw-to-derived limitations. | Keep current reviewer-archive mode matrix only. |
| Repository README | Final file list, variables, provenance, licences and restrictions are confirmed. | Map each released object to manuscript figures/tables and reproduction commands. | Do not deposit as final public record. |
| Cover letter or editor note, if used | Reviewer archive and restricted-source boundaries are final. | State the reviewer archive route and disclose unresolved third-party restrictions without implying public raw-file sharing. | Keep current bounded statement; do not add DOI/licence claims. |

## Pre-Deposit Audit

Complete before uploading the public release.

| Check | Status: Confirmed / Unresolved | Author note |
| --- | --- | --- |
| No restricted raw files are included without permission. | Unresolved | TODO |
| No credentials, API keys, private paths or institution-only caches are included. | Unresolved | TODO |
| Public release contents match the final submitted manuscript version. | Unresolved | TODO |
| Manifest lists reproduction modes and expected runtime boundaries. | Unresolved | TODO |
| Checksums correspond to the final release files. | Unresolved | TODO |
| README states raw-to-derived limitations without weakening the derived-evidence claim. | Unresolved | TODO |
| Licence files are present and compatible with dependencies and source-provider terms. | Unresolved | TODO |
| DOI, repository URL and access terms are recorded for manuscript update. | Unresolved | TODO |

## Pre-Deposit Blocker Checks

Treat these as blockers for a public DOI release. A blocker does not prevent submission with the current bounded future-tense language, but it prevents changing the formal manuscript to a concrete public-release claim.

| Blocker check | Passing evidence | If not passed |
| --- | --- | --- |
| Release-safety scan reports zero blockers. | `natcs-release-safety-audit` output or copied audit JSON/markdown for the final release candidate. | Remove credentials, private paths, sensitive filenames or restricted files before deposit. |
| Raw-source worksheet is complete for every source block represented in the public release. | Final status option, evidence reference and author initials/date are filled. | Exclude the affected files or keep them as acquisition notes only. |
| Licence and rights fields are explicit for code and each released derived-data family. | Licence file plus README/access-term fields. | Do not apply open licences to third-party-derived data until rights are confirmed. |
| Public release matches the final manuscript version. | Manifest/checksum record dated after the final build. | Rebuild, regenerate checksums and update README before deposit. |
| Repository private-review link or final DOI has been tested outside the author account. | External access check recorded with date. | Do not cite the link or DOI in manuscript text. |
| Restricted raw files and helper code are absent unless specifically cleared. | Manifest review plus release-safety audit. | Remove files or document the exact reviewer-controlled route. |

## Reviewer-Risk Interpretation

Strongest position: the public release has a DOI, clear licence, executable derived-evidence rebuild, acquisition notes and explicit restricted-raw boundaries.

Acceptable bounded position: the submission has a reviewer archive and a concrete acceptance-stage release plan, while the public DOI is inserted after acceptance.

Weak position: the manuscript promises a DOI-minting release but does not specify what will be released, what will be excluded, or which text must be updated.

Current visible package is in the acceptable bounded position. Moving to the strongest position requires the author decisions above and an actual DOI-minting deposit.
