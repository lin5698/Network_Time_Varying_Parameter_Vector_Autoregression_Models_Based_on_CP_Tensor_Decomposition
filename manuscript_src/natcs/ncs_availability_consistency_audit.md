# Data and Code Availability Consistency Audit

> **Status refresh, 2026-08-26.** The controlling governance records changed on this date: `PAPER_CLAIM_AUDIT.json` and `EMPIRICAL_IMPLEMENTATION_AUDIT.json` both carry verdict PASS under reason codes in the `rcep_nyc_value_audited` family, authorizing the downstream rebuild chain alone. Manuscript-promotion authorization remains NOT_GRANTED (RC-1), empirical claim activation stays gated behind `OPEN_CHARACTERIZATION_FLAGS_BLOCKING_ACTIVATION_NOT_BUILD` (RC-2), and rebuilt artifacts remain subject to post-regeneration review (RC-3). This audit is a current consistency record under that posture. It authorizes no new or stronger availability claim, and every worksheet-driven gate below stays in force.

Purpose: verify that the Data availability and Code availability statements stay aligned with Nature Computational Science expectations, visible package evidence and unresolved author/source-access gates. This is a submission-support artifact, is not manuscript text and is not new evidence.

Audit date: 2026-08-26 (supersedes the 2026-07-07 pass).

Policy anchor checked:

- Nature Computational Science reporting standards require a Data availability statement for original research and transparent access conditions for the minimum dataset needed to interpret, verify and extend the work.
- Nature Portfolio policy requires restrictions on data, materials, code or protocols to be disclosed to editors at submission.
- Code availability statements should state whether and how custom code can be accessed, including restrictions.
- Official pages used: Nature Computational Science reporting standards (`https://www.nature.com/natcomputsci/editorial-policies/reporting-standards`) and Nature Computational Science AIP/formatting source-data guidance (`https://www.nature.com/natcomputsci/natcomputsci/submission-guidelines/aip-and-formatting`).

Boundary: this audit does not claim that raw sources are redistributable, that a public DOI exists, or that source-provider permissions have been confirmed. It checks consistency under the current conservative submission position.

Serves: reproducibility / rigour / clarity.

## 1. Current Availability Position

The current formal position has three layers:

1. Submitted-evidence layer: reviewer archive with derived objects, scripts, environment files, manifests, checksums and reproduction entry points, tied to the build version it was frozen from.
2. Raw-source acquisition layer: documented and externally constrained by third-party access terms and helper-checkout boundaries.
3. Public-release layer: DOI-minting release planned on acceptance, with repository, licence and access terms unassigned.

This remains an acceptable bounded position for submission only while the formal statements keep restrictions explicit and avoid implying full raw-source redistribution.

## 1.1 Worksheet Gate for Formal Wording

Do not update `data_availability.md`, `code_availability.md`, Supplementary Note 7, the cover letter or the repository README toward a stronger public/raw-source claim until the relevant worksheet row has moved from `Unresolved` to a confirmed status with evidence.

| Desired wording change | Required worksheet evidence | If evidence is absent |
| --- | --- | --- |
| Claim raw files can be shared with reviewers. | `raw_source_access_decision_worksheet.md` records `Reviewer raw-file sharing confirmed`, journal route, access condition and provider/licence evidence for the specific source block. | Keep raw-source non-redistribution language and rely on derived substitutes/acquisition notes. |
| Claim a public provider route is sufficient for raw reconstruction. | `raw_source_access_decision_worksheet.md` records `Provider public route only` with source URL, version, query/download date or commit. | Keep the route described as documented and externally constrained. |
| Claim a derived dataset will be public. | `public_release_readiness_worksheet.md` marks the component as `Include` and records licence/provenance clearance. | Keep future-tense or archive-only wording. |
| Claim a DOI, repository name, licence or release version. | `public_release_readiness_worksheet.md` records the repository landing page, DOI/accession, licence, access terms and external access check. | Keep the current DOI-minting future-tense statement. |
| Claim the RCEP helper checkout is available or replaceable. | Both worksheets record a clean helper or tested replacement route, plus release-safety and licence checks. | Keep the helper outside the default reviewer path. |

## 2. Formal Statement Consistency Matrix

| Formal statement area | Current wording position | Evidence in package | External gate | Consistency status | Do not strengthen until | Tags |
| --- | --- | --- | --- | --- | --- | --- |
| Reviewer archive access | A separate peer-review code-and-derived-evidence archive is available through the journal-approved route, tied to its frozen build version. | Reviewer archive, manifest, cleanroom check record, upload freeze manifest once reissued. | RC-3 post-regeneration review of the rebuilt package. | Consistent with the frozen prior build; refreeze required for the upload version. | Archive path/checksum freeze is confirmed for the actual upload version. | reproducibility / rigour |
| Derived objects support manuscript evidence | Derived quarterly trade panel, NYC panel, network matrices, tariff-relief panel, benchmark outputs and bootstrap outputs regenerate manuscript-facing tables, figures and summaries. | Evidence bundle, cleanroom reproduction record, submission inventory. | None beyond final package freeze. | Consistent. | No strengthening needed. | reproducibility / clarity |
| Clean-copy rebuild | A clean-copy full-output artifact rebuild from included derived objects passed locally at the frozen build. | Cleanroom reproduction record, reviewer archive README/manifest, freeze manifest. | None while the frozen archive ships. | Consistent with recorded evidence. | Do not imply a fresh raw-layer rerun or a fresh 500-draw bootstrap beyond the recorded mode. | rigour / reproducibility |
| Raw IMF, trade, tariff and MRIO inputs | Raw sources remain governed by provider terms and are unbundled. | Data availability, raw-source worksheet, acquisition notes. | Author/provider permission decisions OPEN in `raw_source_access_decision_worksheet.md`. | Consistent and conservative. | Provider terms permit an exact reviewer route or a public route is recorded per block. | reproducibility / rigour |
| RCEP helper checkout | Helper checkout is non-redistributed and required only for raw acquisition/construction. | Data availability, Code availability, raw-source worksheet. | Helper audit unresolved; quarantine-candidate RCEP values remain activation-gated (RC-2). | Consistent and conservative. | Credential/private-path/licence audit passes and a clean route exists. | reproducibility / clarity |
| NYC public route | Upstream `vars` commit and TLC route are recorded; the derived monthly panel is redistributed for review. | Data availability, supplementary note, NYC derived panel and acquisition JSON. | Optional archive DOI/licence confirmation unresolved; NYC characterization flags block any GIRF/stability claim reuse (RC-2). | Consistent. | A permanent archive/DOI exists or authors confirm a different access condition. | reproducibility / generality |
| Public DOI release | Authors will deposit the redistributable code-and-derived-evidence release on acceptance. | Public-release worksheet and future-tense Data/Code availability text. | Repository, DOI, licence and embargo decisions OPEN in `public_release_readiness_worksheet.md`. | Consistent only in future tense. | DOI/repository/licence/access terms exist or the journal requests pending repository language. | reproducibility / clarity |
| Fresh rerun modes | Fresh empirical and benchmark reruns are separate modes with flags and extra inputs. | Code availability, reproduction mode matrix, reviewer archive README. | Compute/source access for fresh reruns. | Consistent. | Keep these modes distinct from the default submitted-evidence rebuild. | rigour / reproducibility |

## 3. Forbidden Availability Drift

Do not add any of the following unless author-confirmed evidence exists and the worksheets are updated:

| Drift phrase or implication | Why it would be unsafe | Required evidence before use | Tags |
| --- | --- | --- | --- |
| "All raw data and code are publicly available." | Restricted trade, tariff, macro, MRIO and helper-code boundaries are unresolved. | Completed raw-source worksheet plus a public release record. | reproducibility / rigour |
| "Fully reproducible from raw data." | Raw-to-derived reconstruction depends on third-party source access and helper-checkout constraints. | Tested raw-to-derived rebuild with a documented public/reviewer-safe source route. | reproducibility / rigour |
| "Zenodo DOI" or another specific DOI. | No DOI is assigned anywhere in the visible package. | An actual repository record and DOI. | reproducibility / clarity |
| "Raw files will be supplied to reviewers" across all source blocks. | Provider permissions are unrecorded for most blocks. | Source-block-specific permission and journal route. | rigour / clarity |
| "The public release includes all data." | Public release contents and exclusions remain undecided. | Pre-deposit audit and licence decisions. | reproducibility / rigour |
| "The helper checkout is available." | The helper lacks a completed credentials/private-path/redistribution audit record. | A clean helper or public replacement route. | reproducibility / clarity |

## 4. Editor-Question Response Templates

Use these replies only if editors or reviewers ask about data/code access.

### If asked whether results can be reproduced

The shipped archive regenerates manuscript-facing tables, figures and numerical summaries from included derived objects under the documented submitted-evidence mode. Raw-to-derived reconstruction is documented separately because several source blocks remain governed by third-party access terms and helper-checkout constraints.

Tags: reproducibility / rigour / clarity.

### If asked why raw files are not bundled

The raw macro, trade, tariff and MRIO inputs are subject to provider terms. The submission supplies derived panels, network matrices, acquisition notes and manuscript-facing evidence objects for review, keeping source-provider access conditions explicit throughout.

Tags: reproducibility / rigour.

### If asked about public release

The manuscript uses future-tense release language because no public DOI, repository route, licence or access terms have been assigned. On acceptance, the redistributable code-and-derived-evidence release should be deposited in a DOI-minting repository, and the availability statements should then name the actual identifier and access terms.

Tags: reproducibility / clarity.

## 5. Minimal Text-Change Triggers

| New evidence | Formal text change allowed | Files to update | Verification needed |
| --- | --- | --- | --- |
| A raw-source block is shareable with reviewers. | Add a source-block-specific reviewer route and access condition. | `data_availability.md`, raw-source worksheet, Supplementary Note 7 when commands change. | Provider terms and route recorded. |
| A source block has a stable public route. | Add provider route, query date, version or commit. | `data_availability.md`, acquisition notes. | URL/version/commit checked. |
| DOI/repository/licence assigned. | Replace future-tense DOI language with the actual repository, DOI, licence and access terms. | `data_availability.md`, `code_availability.md`, public-release worksheet, Supplementary Note 7. | Repository record exists and release contents match the final manuscript. |
| Clean helper route exists. | Replace the non-redistributed-helper boundary with the clean helper or public replacement route. | `code_availability.md`, raw-source worksheet, public-release worksheet. | Credential/private-path/licence audit passed and the command tested. |
| Fig. 2 or manuscript evidence changes. | Rebuild reviewer archive, figure-source package, upload package and freeze manifest. | Submission package and manifests. | Final gate check passes with updated checksums. |

## 6. Current Risk Interpretation

NCS senior editor: the conservative availability position stays acceptable while the reusable computational object and the derived-evidence rebuild remain clear. A vague or overpromised availability statement would weaken the computational-science pitch.

Computational methods reviewer: the derived-evidence rebuild supports inspection of the reported claims. A reviewer may still request raw-source clarity, so the source-block worksheet should stay ready.

Temporal/complex networks reviewer: the NYC public route helps reproducibility and generality. RCEP raw-source restrictions are acceptable only while derived substitutes stay traceable to each manuscript-facing figure and table.

## 7. Next Minimal Author Material

1. Confirm source-block decisions in `raw_source_access_decision_worksheet.md`.
2. Confirm repository route, licence and embargo timing in `public_release_readiness_worksheet.md`.
3. Confirm the reviewer archive and figure-source package are refrozen for the actual upload version after the authorized rebuild chain runs.
4. Leave formal Data/Code wording unchanged unless one of the text-change triggers above is satisfied.

---

Drafted 2026-08-26 under author backlog authorization (item A); assistant-drafted from governed records; open items await author confirmation.
