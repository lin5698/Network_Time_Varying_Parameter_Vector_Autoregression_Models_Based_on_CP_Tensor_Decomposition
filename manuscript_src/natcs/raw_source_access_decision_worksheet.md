# Raw Source Access Decision Worksheet

Purpose: author-facing checklist for finalizing the raw-source access position before Nature Computational Science submission. This is a working document and should not be uploaded unless completed and checked by the authors.

Boundary: this worksheet does not claim that any raw input can be redistributed. It records decisions that must be confirmed from provider terms, licences, institutional constraints and the journal's reviewer-file route.

## Why This Matters

The current submission claim is derived-evidence complete: reviewers can inspect and regenerate manuscript-facing tables, figures and numerical summaries from shipped derived objects. The remaining reproducibility boundary is raw-to-derived reconstruction. NCS reviewers may ask whether raw inputs can be inspected under peer review, whether only acquisition notes can be provided, or whether a public route exists.

Serves: reproducibility / rigour / clarity.

## Author Action for This Revision

For each source block, fill the `Author-confirmed status` and `Evidence reference` fields before changing any formal availability text. If a row remains unresolved, use the upload-safe default in the table below. This keeps the manuscript aligned with the visible package while leaving a precise route for stronger wording after provider terms, licences or journal-reviewer routes are confirmed.

Allowed status options are:

- `Reviewer raw-file sharing confirmed`
- `Provider public route only`
- `Derived substitute only`
- `Mixed`
- `Replace helper route`

Any other wording should be converted into one of these labels before `Data availability`, `Code availability` or Supplementary Note 7 is changed.

## Submission-Day Quick Decision

Use this quick decision before editing Data availability, Code availability, Supplementary Note 7 or portal text.

| Current source-access state | Manuscript wording to use now | Immediate action |
| --- | --- | --- |
| A source block is unresolved or provider terms have not been checked. | Keep the current conservative wording and name the derived substitute. | Do not claim raw-file sharing, public raw access or full raw-to-derived reproducibility for that block. |
| A provider route is public but raw files are not bundled. | State the provider route, version, query date, URL or commit, and keep raw files outside the reviewer archive. | Record the route in the decision table and acquisition notes before changing formal text. |
| Journal-confidential reviewer sharing is confirmed for one source block. | Add a source-block-specific reviewer route and access condition for that block only. | Do not generalize the permission to other source blocks. |
| A source block has mixed permissions. | Split the source block into shareable, public-route and derived-substitute subparts. | Update Data availability only after each subpart has a confirmed status and evidence reference. |
| The RCEP helper checkout is unaudited or contains unresolved private/licence constraints. | Keep the helper outside the default reviewer path. | Do not claim helper availability until a clean route or tested replacement exists. |

## Decision Table

Complete one row per source block before final upload.

| Source block | Current manuscript statement | Upload-safe default status | Author-confirmed status | Evidence reference required before changing text | Reviewer/public route to record if stronger than default | Fallback if unresolved | Data availability wording consequence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Quarterly macro indicators | IMF IFS and national statistical offices; raw source files are not redistributed because provider terms apply. | `Derived substitute only` or `Provider public route only` | Unresolved | Provider terms, downloaded-file provenance, national-statistics reuse terms. | Journal-confidential reviewer route only if provider terms permit; otherwise provider route, version/query date and access notes. | Derived quarterly panel, source list, acquisition notes. | Keep conservative non-redistribution wording unless evidence supports reviewer sharing or a precise public route. |
| Bilateral trade weights | UN Comtrade extracts with BACI, WITS, OEC and Atlas fallback/cross-check slots; raw exports and fallback files are not recursively redistributed. | `Derived substitute only` or `Mixed` | Unresolved | UN Comtrade and fallback-source redistribution terms; extraction logs for each source family. | Split by UN Comtrade, BACI, WITS, OEC and Atlas if only some inputs are shareable or publicly routable. | Derived network matrices, source-coverage summaries, acquisition notes. | Keep one bounded statement if unresolved; split into source-specific sentences only after each subset has a confirmed status. |
| Tariff schedules and bilateral import records | Official RCEP tariff schedules and bilateral import records; raw schedule and bilateral source files remain subject to upstream terms. | `Derived substitute only` or `Provider public route only` | Unresolved | Official schedule reuse terms, source URLs, query/download dates and import-data access terms. | Exact official-source route or journal-confidential reviewer route if terms permit. | Derived tariff-relief panel and association outputs. | Do not imply bundled raw schedules/import records unless permission and route are recorded. |
| MRIO-derived trade exposure inputs | Annual MRIO information used for value-added trade proxies; licensed or otherwise restricted raw inputs are not bundled. | `Derived substitute only` | Unresolved | MRIO licence, institutional access terms and redistribution restrictions. | Reviewer sharing only if the licence permits the exact files to be shared through the journal route. | Derived exposure variables and robustness summaries. | Keep licensed/restricted boundary language unless licence terms permit a stronger claim. |
| RCEP acquisition helper checkout | Non-redistributed helper checkout is required only for raw acquisition and construction. | `Replace helper route` or `Derived substitute only` | Unresolved | Ownership of helper code, dependency licences, secrets/API-key audit and private-path audit. | Clean public helper, journal-safe helper, or tested replacement acquisition route. | Acquisition notes and derived evidence rebuild. | No strengthening; revise only after helper audit or replacement route passes. |
| NYC Taxi source tensor | Public upstream `xinychen/vars` repository at commit `7e63ba9734021171eaf49edb92be8a7e7e8802eb`, path `datasets/NYC-taxi`; TLC source route recorded. | `Provider public route only` plus redistributed derived panel if licence permits | Unresolved for derived-panel licence and archival route | Repository availability, commit hash, TLC source terms and intended derived-panel licence. | Public repository route and TLC route are recorded; add archive DOI only if created. | Derived monthly mobility panel, acquisition JSON, operator-check table. | Keep public-route wording; add DOI/licence wording only after an archive record and licence are confirmed. |

## Status Options

Use one of these labels in the author-confirmed status column:

- `Reviewer raw-file sharing confirmed`: the source files can be supplied through the journal-approved reviewer route, with any access condition recorded.
- `Provider public route only`: reviewers should obtain the raw input from the provider or public repository, with acquisition notes supplied.
- `Derived substitute only`: raw inputs cannot be redistributed; derived evidence and acquisition notes are the reviewer substitute.
- `Mixed`: some files in the source block can be shared, while others require public acquisition or derived substitutes.
- `Replace helper route`: the current acquisition layer depends on a non-redistributed helper or source route that should be replaced with a cleaner public or reviewer-safe route.

Legacy labels in older notes map as follows: `Shareable with reviewers` -> `Reviewer raw-file sharing confirmed`; `Public route only` -> `Provider public route only`; `Derived-only` -> `Derived substitute only`; `Replace before submission` -> `Replace helper route`.

## Submission Gate

Use this gate before changing `Data availability`, `Code availability` or Supplementary Note 7.

| Gate question | Required answer before strengthening the manuscript text | If the answer is no or unknown |
| --- | --- | --- |
| Have provider terms or licences been checked for each source block? | Yes, with notes or links recorded in the decision table. | Keep the current conservative language. |
| Can the source files be shared through a journal-confidential reviewer route? | Yes, with the exact route and access conditions recorded. | Do not claim reviewer raw-file sharing. Use `Provider public route only`, `Derived substitute only` or `Mixed`. |
| Does the RCEP helper checkout contain no private credentials, private paths, unpublished code or non-redistributable dependencies? | Yes, and a clean reviewer-safe route is recorded. | Keep the helper described as non-redistributed and required only for raw acquisition. |
| Can the raw-to-derived rebuild be run by a reviewer without author intervention? | Yes, with source access, commands and environment notes recorded. | Keep raw-to-derived rebuilding outside the default reviewer path. |
| Are the derived substitutes tied to every manuscript-facing figure, table and numerical summary? | Yes; the submitted-evidence archive and checksums cover the manuscript-facing outputs. | Do not submit until the derived-evidence traceability gap is fixed. |

Default submission position: if no stronger author-confirmed access decision is recorded, retain the current bounded claim. The manuscript should say that reviewers can regenerate manuscript-facing evidence from derived objects, while raw-to-derived reconstruction remains documented but externally constrained.

## Current Conservative Labels

Use these as the default position unless the authors confirm stronger access rights. This table is an author decision aid; it is not a substitute for checking provider terms.

| Source block | Conservative label for current upload | Why this is the safe label | What would strengthen it |
| --- | --- | --- | --- |
| Quarterly macro indicators | `Derived substitute only` or `Provider public route only` | The current manuscript states that raw files are not redistributed because provider terms apply. | Confirm provider terms that permit confidential reviewer sharing, or record public query routes and dates. |
| Bilateral trade weights | `Derived substitute only` or `Mixed` | The current manuscript supplies derived network matrices and source-coverage summaries, but does not claim recursive redistribution of raw extracts. | Confirm UN Comtrade and fallback-source redistribution terms, plus extraction logs. |
| Tariff schedules and bilateral import records | `Derived substitute only` or `Provider public route only` | Official schedules and bilateral records may have different upstream access terms. | Record exact public URLs, query dates and any permission for reviewer-file sharing. |
| MRIO-derived trade exposure inputs | `Derived substitute only` | The current manuscript states that licensed or otherwise restricted raw inputs are not bundled. | Confirm licence terms that allow reviewer sharing, or replace with a fully public MRIO route. |
| RCEP acquisition helper checkout | `Replace helper route` or `Derived substitute only` | The helper is non-redistributed and required only for raw acquisition and construction. | Audit for credentials/private code, then either share a cleaned helper or document a public replacement route. |
| NYC Taxi source tensor | `Provider public route only` plus redistributed derived panel if licence permits | The upstream repository commit and TLC source route are recorded, and the derived monthly panel is provided for review. | Confirm the upstream repository remains accessible and record any DOI or archived snapshot if available. |

## Author Confirmation Prompts

Use these prompts to complete the decision table without changing manuscript text prematurely.

| Source block | Minimum answer needed from authors | If unanswered at upload |
| --- | --- | --- |
| Quarterly macro indicators | Can IMF/national-statistics raw files be shared through a journal-confidential route, or should reviewers use provider routes and the derived panel? | Keep `Derived substitute only` or `Provider public route only`. |
| Bilateral trade weights | For UN Comtrade, BACI, WITS, OEC and Atlas inputs, which files are shareable, which require public routes, and which are represented only by derived matrices? | Keep `Derived substitute only` or `Mixed` without naming raw-file sharing. |
| Tariff schedules and bilateral import records | Are official schedule/import files shareable, publicly linkable with query dates, or derived-only? | Keep `Derived substitute only` or `Provider public route only`. |
| MRIO-derived trade exposure inputs | Does the MRIO licence permit reviewer sharing or public redistribution of the exact raw inputs? | Keep `Derived substitute only`. |
| RCEP acquisition helper checkout | Does the helper contain private credentials, private paths, unpublished code or non-redistributable dependencies, and can a cleaned route be released? | Keep helper non-redistributed and outside the default reviewer path. |
| NYC Taxi source tensor | Is the upstream commit still accessible, and can the derived monthly panel be redistributed under the intended release terms? | Keep public-route wording and bundled derived-panel wording; do not claim an archival DOI. |

## Text-Change Rules

Change the manuscript only after the corresponding decision row is confirmed.

- If a source block becomes `Reviewer raw-file sharing confirmed`, update `Data availability` to say that the raw files will be provided through the journal-approved reviewer route, and state any access conditions.
- If a source block remains `Provider public route only`, keep the provider route, version, query date or commit hash explicit.
- If a source block remains `Derived substitute only`, keep the current boundary language and make the derived substitute concrete.
- If a source block is `Mixed`, split the source block in `Data availability` so each input has a clear access path.
- If a source block is `Replace helper route`, do not strengthen the availability claim until the replacement route has been tested.

## Decision-To-Text Map

Use this map after the decision table is complete. Bracketed fields require author-supplied details.

| Decision label | Data availability wording action | Code availability / Supplementary action |
| --- | --- | --- |
| `Reviewer raw-file sharing confirmed` | Add: "The [source block] raw files will be provided to reviewers through [journal route] subject to [access condition]." | Add the exact raw-to-derived command and any source-file placement expected by the scripts. |
| `Provider public route only` | Add or retain provider route, version, query date, commit hash or URL. Do not imply bundled raw files. | State the checkout/download expectation and the tested command if available. |
| `Derived substitute only` | Retain current boundary language and name the derived substitute used for figures/tables. | Keep raw acquisition outside the default reviewer path; ensure the submitted-evidence rebuild remains explicit. |
| `Mixed` | Split the source block into shareable and non-shareable subparts, with one access path per subpart. | Record which scripts use bundled files, public downloads or derived substitutes. |
| `Replace helper route` | Do not strengthen the claim. Either replace the route and retest it, or state the helper/raw layer remains unavailable for reviewer rerun. | Update reproduction modes only after a clean replacement route has passed locally. |

## Per-Source Sign-Off Record

Complete this compact record after the decision table is filled. It gives the editor-facing manuscript owner a one-screen check before any formal text is strengthened.

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
4. Whether any raw-source file has been modified manually outside scripted acquisition.
5. The final DOI repository plan for the redistributable code-and-derived-evidence release.

## Final Author Sign-Off

Complete this section before final upload. Leave a row as `Unresolved` if the answer is not yet known; unresolved rows mean the current conservative Data availability wording should remain in force.

| Item | Status: Confirmed / Unresolved | Author note |
| --- | --- | --- |
| Quarterly macro source access decision is recorded. | Unresolved | TODO |
| Bilateral trade source access decision is recorded. | Unresolved | TODO |
| Tariff schedule/import-record access decision is recorded. | Unresolved | TODO |
| MRIO access decision is recorded. | Unresolved | TODO |
| RCEP helper checkout is audited for private credentials and redistribution limits. | Unresolved | TODO |
| NYC Taxi public route and derived-panel redistribution are confirmed. | Unresolved | TODO |
| Data availability text has been left conservative or updated according to confirmed decisions only. | Unresolved | TODO |
| Code availability and Supplementary Note 7 match the final access decisions. | Unresolved | TODO |

## Reviewer-Risk Interpretation

Strongest position: raw files or public routes are available for every source block, with derived evidence supplied for convenience.

Acceptable bounded position: derived evidence is complete for manuscript-facing results, and restricted raw inputs are documented through acquisition notes.

Weak position: raw-source routes are vague, helper code is unavailable without explanation, or derived substitutes are not tied to manuscript-facing outputs.

Current visible package is in the acceptable bounded position. Moving to the strongest position requires author-confirmed source-access decisions.
