# Data and Code Availability Consistency Audit

> **Current-status supersession, 2026-07-23.** This is a historical
> consistency record, not a current availability assessment. `PAPER_CLAIM_AUDIT=BLOCKED`
> and `EMPIRICAL_IMPLEMENTATION_AUDIT=FAIL` prohibit any claim that a reviewer
> archive, derived data, code, figures, tables or rerun route is available with
> a submission. Do not use the legacy three-layer availability position or its
> response templates until a new independent audit has released the exact
> package and formal statements.

Purpose: verify that the current Data availability and Code availability statements stay aligned with Nature Computational Science expectations, visible package evidence and unresolved author/source-access gates. This is a submission-support artifact, not manuscript text and not new evidence.

Audit date: 2026-07-07.

Policy anchor checked on 2026-07-07:

- Nature Computational Science reporting standards require a Data availability statement for original research and transparent access conditions for the minimum dataset needed to interpret, verify and extend the work.
- Nature Portfolio policy requires restrictions on data, materials, code or protocols to be disclosed to editors at submission.
- Code availability statements should state whether and how custom code can be accessed, including restrictions.
- Official pages used: Nature Computational Science reporting standards (`https://www.nature.com/natcomputsci/editorial-policies/reporting-standards`) and Nature Computational Science AIP/formatting source-data guidance (`https://www.nature.com/natcomputsci/natcomputsci/submission-guidelines/aip-and-formatting`).

Boundary: this audit does not claim that raw sources are redistributable, that a public DOI exists, or that source-provider permissions have been confirmed. It checks consistency under the current conservative submission position.

Serves: reproducibility / rigour / clarity.

## 1. Current Availability Position

The current formal position has three layers:

1. Submitted-evidence layer: reviewer archive with derived objects, scripts, environment files, manifests, checksums and reproduction entry points.
2. Raw-source acquisition layer: documented but externally constrained by third-party access terms and helper checkouts.
3. Public-release layer: DOI-minting release planned on acceptance, with repository, licence and access terms not yet assigned.

This is an acceptable bounded position for submission only if the formal statements keep restrictions explicit and avoid implying full raw-source redistribution.

## 1.1 Worksheet Gate for Formal Wording

Do not update `data_availability.md`, `code_availability.md`, Supplementary Note 7, the cover letter or the repository README to a stronger public/raw-source claim until the relevant worksheet row has moved from `Unresolved` to a confirmed status with evidence.

| Desired wording change | Required worksheet evidence | If evidence is absent |
| --- | --- | --- |
| Claim raw files can be shared with reviewers. | `raw_source_access_decision_worksheet.md` records `Reviewer raw-file sharing confirmed`, journal route, access condition and provider/licence evidence for the specific source block. | Keep raw-source non-redistribution language and rely on derived substitutes/acquisition notes. |
| Claim a public provider route is sufficient for raw reconstruction. | `raw_source_access_decision_worksheet.md` records `Provider public route only` with source URL, version, query/download date or commit. | Keep the route described as documented but externally constrained. |
| Claim a derived dataset will be public. | `public_release_readiness_worksheet.md` marks the component as `Include` and records licence/provenance clearance. | Keep future-tense or reviewer-archive-only wording. |
| Claim a DOI, repository name, licence or release version. | `public_release_readiness_worksheet.md` records the repository landing page, DOI/accession, licence, access terms and external access check. | Keep the current DOI-minting future-tense statement. |
| Claim the RCEP helper checkout is available or replaceable. | Both worksheets record a clean helper or tested replacement route, plus release-safety and licence checks. | Keep helper outside the default reviewer path. |

## 2. Formal Statement Consistency Matrix

| Formal statement area | Current wording position | Evidence in package | External gate | Consistency status | Do not strengthen until | Tags |
| --- | --- | --- | --- | --- | --- | --- |
| Reviewer archive access | A separate peer-review code-and-derived-evidence archive is available through the journal-approved route. | Reviewer archive, manifest, cleanroom check, upload freeze manifest. | Reviewer archive freeze/sign-off. | Consistent. | Archive path/checksum freeze is confirmed for upload. | reproducibility / rigour |
| Derived objects support manuscript evidence | Derived quarterly trade panel, NYC panel, network matrices, tariff-relief panel, benchmark outputs and bootstrap outputs regenerate manuscript-facing tables, figures and summaries. | Evidence bundle, cleanroom reproduction check, submission inventory. | None beyond final package freeze. | Consistent. | No strengthening needed. | reproducibility / clarity |
| Clean-copy rebuild | A clean-copy full-output artifact rebuild from included derived objects passed locally. | `cleanroom_reproduction_check.md`, reviewer archive README/manifest, freeze manifest. | None if current archive is frozen. | Consistent with current evidence. | Do not imply fresh raw or fresh 500-draw rerun beyond the recorded mode. | rigour / reproducibility |
| Raw IMF, trade, tariff and MRIO inputs | Raw sources remain governed by provider terms and are not bundled. | Data availability, raw-source worksheet, acquisition notes. | Author/provider permission decisions unresolved. | Consistent and conservative. | Provider terms permit exact reviewer route or public route is recorded. | reproducibility / rigour |
| RCEP helper checkout | Helper checkout is non-redistributed and required only for raw acquisition/construction. | Data availability, Code availability, raw-source worksheet. | Helper audit unresolved. | Consistent and conservative. | Credential/private-path/licence audit and clean route are complete. | reproducibility / clarity |
| NYC public route | Upstream `vars` commit and TLC route are recorded; derived monthly panel is redistributed for review. | Data availability, Supplementary note, NYC derived panel and acquisition JSON. | Optional archive DOI/licence confirmation unresolved. | Consistent. | Permanent archive/DOI exists or authors confirm a different access condition. | reproducibility / generality |
| Public DOI release | Authors will deposit redistributable code-and-derived-evidence release on acceptance. | Public-release worksheet and Code/Data availability future-tense text. | Repository, DOI, licence and embargo unresolved. | Consistent only in future tense. | DOI/repository/licence/access terms actually exist or journal requests pending repository language. | reproducibility / clarity |
| Fresh rerun modes | Fresh empirical and benchmark reruns are separate modes with flags and extra inputs. | Code availability, reproducibility mode matrix, reviewer archive README. | Compute/source access for fresh reruns. | Consistent. | Do not collapse these into the default reviewer path. | rigour / reproducibility |

## 3. Forbidden Availability Drift

Do not add any of the following unless author-confirmed evidence exists and the worksheets are updated:

| Drift phrase or implication | Why it would be unsafe | Required evidence before use | Tags |
| --- | --- | --- | --- |
| "All raw data and code are publicly available." | Restricted trade, tariff, macro, MRIO and helper-code boundaries are unresolved. | Completed raw-source worksheet plus public release record. | reproducibility / rigour |
| "Fully reproducible from raw data." | Raw-to-derived reconstruction depends on third-party source access and helper checkouts. | Tested raw-to-derived rebuild with documented public/reviewer-safe source route. | reproducibility / rigour |
| "Zenodo DOI" or another specific DOI. | No DOI is currently assigned in the visible package. | Actual repository record and DOI. | reproducibility / clarity |
| "Raw files will be supplied to reviewers" for all source blocks. | Provider permissions are not recorded for all blocks. | Source-block-specific permission and journal route. | rigour / clarity |
| "The public release includes all data." | Public release contents and exclusions remain unresolved. | Pre-deposit audit and licence decisions. | reproducibility / rigour |
| "The helper checkout is available." | Helper has not been audited for credentials, private paths, unpublished code or redistribution limits. | Clean helper or public replacement route. | reproducibility / clarity |

## 4. Reviewer-Facing Response Templates

Use these only if editors or reviewers ask about data/code access.

### If asked whether results can be reproduced

The submitted reviewer archive regenerates manuscript-facing tables, figures and numerical summaries from shipped derived evidence objects under the documented submitted-evidence mode. Raw-to-derived reconstruction is documented separately because several source blocks remain governed by third-party access terms and helper-checkout constraints.

Tags: reproducibility / rigour / clarity.

### If asked why raw files are not bundled

The raw macro, trade, tariff and MRIO inputs are subject to provider terms. The submission therefore supplies derived panels, network matrices, acquisition notes and manuscript-facing evidence objects for review, while keeping source-provider access conditions explicit.

Tags: reproducibility / rigour.

### If asked about public release

The current manuscript uses future-tense release language because no public DOI, repository route, licence or access terms have been assigned. On acceptance, the redistributable code-and-derived-evidence release should be deposited in a DOI-minting repository and the availability statements should be updated with the actual identifier and access terms.

Tags: reproducibility / clarity.

## 5. Minimal Text-Change Triggers

| New evidence | Formal text change allowed | Files to update | Verification needed |
| --- | --- | --- | --- |
| A raw-source block is shareable with reviewers. | Add source-block-specific reviewer route and access condition. | `data_availability.md`, raw-source worksheet, Supplementary Note 7 if commands change. | Provider terms and route recorded. |
| A source block has a stable public route. | Add provider route, query date, version or commit. | `data_availability.md`, acquisition notes. | URL/version/commit checked. |
| DOI/repository/licence assigned. | Replace future-tense DOI language with actual repository, DOI, licence and access terms. | `data_availability.md`, `code_availability.md`, public-release worksheet, Supplementary Note 7. | Repository record exists and release contents match final manuscript. |
| Clean helper route exists. | Replace non-redistributed helper boundary with clean helper or public replacement route. | `code_availability.md`, raw-source worksheet, public-release worksheet. | Credential/private-path/licence audit passed and command tested. |
| Fig. 2 or manuscript evidence changes. | Rebuild reviewer archive, figure-source package, upload package and freeze manifest. | submission package and manifests. | Final gate check passes with updated checksums. |

## 6. Current Reviewer-Risk Interpretation

NCS senior editor: the current conservative availability position is acceptable if the reusable computational object and derived-evidence rebuild stay clear. A vague or overpromised availability statement would weaken the computational-science pitch.

Computational methods reviewer: the derived-evidence rebuild supports inspection of the reported claims. The reviewer may still request raw-source clarity, so the source-block worksheet should be ready.

Temporal/complex networks reviewer: the NYC public route helps reproducibility and generality. The RCEP raw-source restrictions are acceptable only if derived substitutes remain traceable to each manuscript-facing figure and table.

## 7. Next Minimal Author Material

1. Confirm source-block decisions in `raw_source_access_decision_worksheet.md`.
2. Confirm repository route, licence and embargo timing in `public_release_readiness_worksheet.md`.
3. Confirm the reviewer archive and figure-source package are frozen for the upload version.
4. Do not update formal Data/Code wording unless one of the text-change triggers above is satisfied.
