# RCEP Helper Author Decision Sheet

Date: 2026-07-19

Current status: **MANIFEST INSTALLED AND STATICALLY VALIDATED; EXECUTION NOT AUTHORIZED**

Two staged author decisions were received in this task on 2026-07-19. The first selected C3, confirmed ownership or permitted use of the helper and provider-governed source data, accepted the non-redistribution/open-source wording boundary, and authorized generation of a schema-v2 manifest candidate only. The second identified the exact candidate SHA-256 and authorized installation plus static verification only.

This sheet concerns the raw-to-derived RCEP helper only. It does not authorize RCEP or NYC scientific execution, R006e screening/confirmation, R006f outcomes, manuscript claim promotion or submission-package rebuilding.

## Candidate Disposition

| Candidate | Preflight | Current disposition | Reason | Review objective |
|---|---:|---|---|---|
| C1 | FAIL | Exclude | `config.py` and `research_network_tvp_var.py` differ from Git HEAD; full worktree is dirty. | rigour / reproducibility |
| C2 | FAIL | Exclude | `research_network_tvp_var.py` differs from Git HEAD; full worktree is dirty. | rigour / reproducibility |
| C3 | WARN | Selected; manifest installed; execution closed | All three bound files are tracked and clean at commit `d0e398b896848f26413cf9aa9dfca15fb4e7ce64`; 8/8 required APIs are present. A top-level licence is absent and imports have filesystem side effects. | rigour / reproducibility |

Candidate C3 path:

`/Users/wuyilin/Desktop/2026学科竞赛/谁在托底中国新能源关键中间品供应链？——基于RCEP—“一带一路”多层贸易网络的逆向冲击韧性研究/external/Who-Absorbs-the-Shock/repo`

Installed schema-v2 identities:

| Bound file | SHA-256 |
|---|---|
| `config.py` | `13aac959b623fb3e569b37f680c2f1b72b3ad0bad6d3b09d01bef36eae5e991f` |
| `research_data_construction.py` | `a88245fdbe451a368358af5776722802ab10bb3b03a4e8cf1ab3e24d9d1d836d` |
| `research_network_tvp_var.py` | `ea6568b0509ed62c62ab12189570576b31251fd921f59e1849a8c2e34b4fbc63` |

## Required Author Declarations

The author must explicitly confirm all applicable statements. Silence, a generic approval or prior approval of a different plan does not satisfy this sheet.

- [x] I select **C3** as the RCEP helper candidate for this manuscript rebuild. `[reproducibility]`
- [x] I confirm that I own this code or have permission to use it for the manuscript's private raw-to-derived reconstruction. `[rigour / reproducibility]`
- [x] I understand that the checkout has no top-level licence file; until a licence or redistribution permission is documented, the helper will remain non-redistributed and will not be described as public/open-source code. `[clarity / reproducibility]`
- [x] I confirm that provider-governed raw inputs used by this helper may be processed for this study and that their access restrictions will be disclosed accurately. `[rigour / reproducibility]`
- [x] I acknowledge the import-time directory creation recorded in the preflight and authorize only a manifest-candidate draft for review. This item does **not** authorize scientific execution. `[rigour]`

## Staged Authorization

1. **Candidate selection: COMPLETE.** The declarations above are completed.
2. **Manifest drafting: COMPLETE.** Candidate SHA-256 `02b151473116bbea39e1dc200f7299cd1d1a3451f8e430bc4d59392eb2525256` was generated from the frozen C3 commit and three hashes.
3. **Manifest approval and installation: COMPLETE.** The author approved candidate SHA-256 `02b151473116bbea39e1dc200f7299cd1d1a3451f8e430bc4d59392eb2525256`; identical bytes were installed as `manuscript_src/natcs/rcep_helper_trust_manifest.json` and passed the static identity gate.
4. **Execution approval:** only after source paths and manifest gates pass may the author separately authorize corrected RCEP/NYC regeneration.

Until all four stages are complete, authoritative status remains:

- `production_trust_granted = true`
- `production_manifest_installed = true`
- `scientific_execution_authorized = false`
- `EMPIRICAL_IMPLEMENTATION_AUDIT.verdict = FAIL`
- `PAPER_CLAIM_AUDIT = BLOCKED`
- `R006e outcome = closed`
- `R006f outcome = closed`
