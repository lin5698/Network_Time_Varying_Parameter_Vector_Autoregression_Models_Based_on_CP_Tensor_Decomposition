# Raw Source Access Decision Worksheet

Purpose: author-facing checklist for finalizing the raw-source access position before Nature Computational Science submission. This is a working document and should stay out of the upload set unless completed and checked by the authors.

Boundary: this worksheet does not claim that any raw input can be redistributed. It records decisions that must be confirmed from provider terms, licences, institutional constraints and the journal's reviewer-file route.

Status 2026-08-26: every author-decision row below remains OPEN. The 2026-08-26 audit chain (both controlling audits PASS under `rcep_nyc_value_audited` reason codes) changed none of these access positions; quarantine-candidate RCEP/NYC values stay activation-gated regardless of any future access decision recorded here.

Serves: reproducibility / rigour / clarity.

## Why This Matters

The current submission claim is derived-evidence complete: reviewers can inspect and regenerate manuscript-facing tables, figures and numerical summaries from shipped derived objects of the frozen build. The remaining reproducibility boundary is raw-to-derived reconstruction. NCS reviewers may ask whether raw inputs can be inspected under peer review, whether only acquisition notes can be provided, or whether a public route exists.

## Author Action for This Revision

For each source block, fill the `Author-confirmed status` and `Evidence reference` fields before changing any formal availability text. If a row remains unresolved, keep the upload-safe default in the table below. This keeps the manuscript aligned with the visible package while leaving a precise route toward stronger wording after provider terms, licences or journal-reviewer routes are confirmed.

Allowed status options are:

- `Reviewer raw-file sharing confirmed`
- `Provider public route only`
- `Derived substitute only`
- `Mixed`
- `Replace helper route`

Any other wording should be converted into one of these labels before `Data availability`, `Code availability` or Supplementary Note 7 is changed.

Option definitions:

- `Reviewer raw-file sharing confirmed`: the source files can travel through the journal-approved reviewer route, with any access condition recorded.
- `Provider public route only`: reviewers obtain the raw input from the provider or public repository, with acquisition notes supplied.
- `Derived substitute only`: raw inputs cannot be redistributed; derived evidence and acquisition notes are the reviewer substitute.
- `Mixed`: some files in a source block are shareable while others require public acquisition or derived substitutes.
- `Replace helper route`: the acquisition layer depends on a non-redistributed helper or source route that should give way to a cleaner public or reviewer-safe route.

Legacy labels in older notes map as follows: `Shareable with reviewers` maps to `Reviewer raw-file sharing confirmed`; `Public route only` maps to `Provider public route only`; `Derived-only` maps to `Derived substitute only`; `Replace before submission` maps to `Replace helper route`.

## Submission-Day Quick Decision

Use this quick decision before editing Data availability, Code availability, Supplementary Note 7 or portal text.

| Current source-access state | Manuscript wording to use now | Immediate action |
| --- | --- | --- |
| A source block is unresolved or provider terms have not been checked. | Keep the current conservative wording and name the derived substitute. | Do not claim raw-file sharing, public raw access or full raw-to-derived reproducibility for that block. |
| A provider route is public while raw files remain unbundled. | State the provider route, version, query date, URL or commit, and keep raw files outside the shipped archive. | Record the route in the decision table and acquisition notes before changing formal text. |
| Journal-confidential reviewer sharing is confirmed for one source block. | Add a source-block-specific reviewer route and access condition for that block alone. | Do not generalize the permission to other source blocks. |
| A source block has mixed permissions. | Split the source block into shareable, public-route and derived-substitute subparts. | Update Data availability only after each subpart has a confirmed status and evidence reference. |
| The RCEP helper checkout is unaudited or carries unresolved private/licence constraints. | Keep the helper outside the default reviewer path. | Do not claim helper availability until a clean route or tested replacement exists. |

## Decision Table

Complete one row per source block before final upload.

| Source block | Current manuscript statement | Upload-safe default status | Author-confirmed status | Evidence reference required before changing text | Reviewer/public route to record if stronger than default | Fallback if unresolved | Data availability wording consequence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Quarterly macro indicators | IMF IFS and national statistical offices; raw source files are not redistributed because provider terms apply. | `Derived substitute only` or `Provider public route only` | Unresolved | Provider terms, downloaded-file provenance, national-statistics reuse terms. | Journal-confidential reviewer route only if provider terms permit; otherwise provider route, version/query date and access notes. | Derived quarterly panel, source list, acquisition notes. | Keep conservative non-redistribution wording unless evidence supports reviewer sharing or a precise public route. |
| Bilateral trade weights | UN Comtrade extracts with BACI, WITS, OEC and Atlas fallback/cross-check slots; raw exports and fallback files are not recursively redistributed. | `Derived substitute only` or `Mixed` | Unresolved | UN Comtrade and fallback-source redistribution terms; extraction logs for each source family. | Split by UN Comtrade, BACI, WITS, OEC and Atlas when only some inputs are shareable or publicly routable. | Derived network matrices, source-coverage summaries, acquisition notes. | Keep one bounded statement while unresolved; split into source-specific sentences only after each subset has a confirmed status. |
| Tariff schedules and bilateral import records | Official RCEP tariff schedules and bilateral import records; raw schedule and bilateral source files remain subject to upstream terms. | `Derived substitute only` or `Provider public route only` | Unresolved | Official schedule reuse terms, source URLs, query/download dates and import-data access terms. | Exact official-source route or journal-confidential reviewer route if terms permit. | Derived tariff-relief panel and association outputs. | Do not imply bundled raw schedules/import records unless permission and route are recorded. |
| MRIO-derived trade exposure inputs | Annual MRIO information used for value-added trade proxies; licensed or otherwise restricted raw inputs are unbundled. | `Derived substitute only` | Unresolved | MRIO licence, institutional access terms and redistribution restrictions. | Reviewer sharing only if the licence permits the exact files to move through the journal route. | Derived exposure variables and robustness summaries. | Keep licensed/restricted boundary language unless licence terms permit a stronger claim. |
| RCEP acquisition helper checkout | Non-redistributed helper checkout is required only for raw acquisition and construction. | `Replace helper route` or `Derived substitute only` | Unresolved | Ownership of helper code, dependency licences, secrets/API-key audit and private-path audit. | Clean public helper, journal-safe helper, or tested replacement acquisition route. | Acquisition notes and derived-evidence rebuild. | No strengthening; revise only after a helper audit or replacement route passes. |
| NYC Taxi source tensor | Public upstream `xinychen/vars` repository at commit `7e63ba9734021171eaf49edb92be8a7e7e8802eb`, path `datasets/NYC-taxi`; TLC source route recorded. | `Provider public route only`, plus redistributed derived panel if licence permits | Unresolved for derived-panel licence and archival route | Repository availability, commit hash, TLC source terms and intended derived-panel licence. | Public repository route and TLC route are already recorded; add an archive DOI only once created. | Derived monthly mobility panel, acquisition JSON, operator-check table. | Keep public-route wording; add DOI/licence wording only after an archive record and licence are confirmed. |

## Submission Gate

Run this gate before changing `Data availability`, `Code availability` or Supplementary Note 7.

| Gate question | Required answer before strengthening the manuscript text | If the answer is no or unknown |
| --- | --- | --- |
| Have provider terms or licences been checked for each source block? | Yes, with notes or links recorded in the decision table. | Keep the current conservative language. |
| Can the source files move through a journal-confidential reviewer route? | Yes, with the exact route and access conditions recorded. | Do not claim reviewer raw-file sharing. Use `Provider public route only`, `Derived substitute only` or `Mixed`. |
| Does the RCEP helper checkout contain zero private credentials, private paths, unpublished files or non-redistributable dependencies? | Yes, and a clean reviewer-safe route is recorded. | Keep the helper described as non-redistributed and required only for raw acquisition. |
| Can a reviewer run the raw-to-derived rebuild without author intervention? | Yes, with source access, commands and environment notes recorded. | Keep raw-to-derived rebuilding outside the default reviewer path. |
| Are the derived substitutes tied to every manuscript-facing figure, table and numerical summary? | Yes; the submitted-evidence archive and checksums cover the manuscript-facing outputs. | Fix the derived-evidence traceability gap before submission. |

Default submission position: while no stronger author-confirmed access decision is recorded, retain the bounded claim. The manuscript should say reviewers can regenerate manuscript-facing evidence from derived objects, while raw-to-derived reconstruction stays documented and externally constrained.

## Author Confirmation Prompts

Use these prompts to complete the decision table without changing manuscript text prematurely.

| Source block | Minimum answer needed from authors | If unanswered at upload |
| --- | --- | --- |
| Quarterly macro indicators | Can IMF/national-statistics raw files move through a journal-confidential route, or should reviewers use provider routes plus the derived panel? | Keep `Derived substitute only` or `Provider public route only`. |
| Bilateral trade weights | For UN Comtrade, BACI, WITS, OEC and Atlas inputs, which files are shareable, which need public routes, and which exist only as derived matrices? | Keep `Derived substitute only` or `Mixed`, without naming raw-file sharing. |
| Tariff schedules and bilateral import records | Are official schedule/import files shareable, publicly linkable with query dates, or derived-only? | Keep `Derived substitute only` or `Provider public route only`. |
| MRIO-derived trade exposure inputs | Does the MRIO licence permit reviewer sharing or public redistribution of the exact raw inputs? | Keep `Derived substitute only`. |
| RCEP acquisition helper checkout | Does the helper contain private credentials, private paths, unpublished code or non-redistributable dependencies, and can a cleaned route be released? | Keep the helper non-redistributed and outside the default reviewer path. |
| NYC Taxi source tensor | Is the upstream commit still accessible, and can the derived monthly panel be redistributed under the intended release terms? | Keep public-route and bundled derived-panel wording; do not claim an archival DOI. |

## Text-Change Rules

Change the manuscript only after the corresponding decision row is confirmed.

- When a source block becomes `Reviewer raw-file sharing confirmed`, update `Data availability` to state that the raw files will be provided through the journal-approved reviewer route, with any access conditions named.
- When a source block stays `Provider public route only`, keep the provider route, version, query date or commit hash explicit.
- When a source block stays `Derived substitute only`, keep the boundary language and make the derived substitute concrete.
- When a source block is `Mixed`, split it inside `Data availability` so each input has one clear access path.
- When a source block is `Replace helper route`, leave the availability claim unchanged until the replacement route has been tested.

## Per-Source Sign-Off Record

Complete this compact record after the decision table is filled. It gives the manuscript owner a one-screen check before any formal text is strengthened.

| Source block | Final status option | Evidence reference | Formal wording action | Author initials/date |
| --- | --- | --- | --- | --- |
| Quarterly macro indicators | Unresolved | TODO | Keep conservative wording. | TODO |
| Bilateral trade weights | Unresolved | TODO | Keep conservative wording. | TODO |
| Tariff schedules and bilateral import records | Unresolved | TODO | Keep conservative wording. | TODO |
| MRIO-derived trade exposure inputs | Unresolved | TODO | Keep conservative wording. | TODO |
| RCEP acquisition helper checkout | Unresolved | TODO | Keep helper outside default reviewer path. | TODO |
| NYC Taxi source tensor | Unresolved | TODO | Keep public-route wording; no DOI/licence claim. | TODO |

## Minimum Author Inputs Needed

1. Provider terms or licence notes for each raw-source block.
2. Whether journal-confidential reviewer sharing is permitted for each block.
3. Whether any helper checkout contains private credentials, unpublished code or non-redistributable dependencies.
4. Whether any raw-source file was modified manually outside scripted acquisition.
5. The final DOI repository plan for the redistributable code-and-derived-evidence release.

## Final Author Sign-Off

Complete this section before final upload. Leave a row as `Unresolved` when the answer is unknown; unresolved rows mean the current conservative Data availability wording stays in force.

| Item | Status: Confirmed / Unresolved | Author note |
| --- | --- | --- |
| Quarterly macro source access decision is recorded. | Unresolved | TODO |
| Bilateral trade source access decision is recorded. | Unresolved | TODO |
| Tariff schedule/import-record access decision is recorded. | Unresolved | TODO |
| MRIO access decision is recorded. | Unresolved | TODO |
| RCEP helper checkout is audited for private credentials and redistribution limits. | Unresolved | TODO |
| NYC Taxi public route and derived-panel redistribution are confirmed. | Unresolved | TODO |
| Data availability text has stayed conservative or moved only on confirmed decisions. | Unresolved | TODO |
| Code availability and Supplementary Note 7 match the final access decisions. | Unresolved | TODO |

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
