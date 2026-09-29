# RCEP Helper Candidate Preflight

**Date:** 2026-07-19

**Decision boundary:** This is a read-only candidate comparison. It does not select a candidate, grant production trust, authorize scientific execution, or open R006e/R006f outcomes.

| Candidate | Static preflight | Git HEAD | Worktree | API contract | Unbound local dependencies | Licence file |
|---|---:|---|---:|---:|---:|---:|
| C1 | FAIL | `d0e398b89684` | dirty/unavailable | PASS | 0 | absent |
| C2 | FAIL | `d0e398b89684` | dirty/unavailable | PASS | 0 | absent |
| C3 | WARN | `d0e398b89684` | clean | PASS | 0 | absent |

## C1

- Supplied path: `/Users/wuyilin/Desktop/translation/谁是冲击的吸收者？——RCEP关税分期减让与亚太贸易网络逆向冲击韧性/repo_rcep_shock/repo`
- Preflight status: **FAIL**
- Failures: required_file_differs_from_head:config.py, required_file_differs_from_head:research_network_tvp_var.py
- Warnings: git_worktree_is_dirty, import_time_side_effect_indicator_present, no_top_level_license_file
- `research_data_construction.py`: sha256 `a88245fdbe451a368358af5776722802ab10bb3b03a4e8cf1ab3e24d9d1d836d`; tracked=True; symlink=False; Git status=`clean`
- `research_network_tvp_var.py`: sha256 `7378bf12e1a3ae72ce584577437aa99ef3b025f6228ac5a8ed88d55ada402ecd`; tracked=True; symlink=False; Git status=`M repo/research_network_tvp_var.py`
- `config.py`: sha256 `80f8e8f43a4bb87d0941056fd8a90571a90d34b50f852b386ec256e9a0d9a6cd`; tracked=True; symlink=False; Git status=`M repo/config.py`
- Missing required APIs: none
- Absolute-path indicators: 0
- Credential/private-key indicators: 0
- Import-time side-effect indicators: 5
- Dependency credential/private-key indicators: 0
- Dependency import-time side-effect indicators: 0

## C2

- Supplied path: `/Users/wuyilin/Desktop/translation/谁是冲击的吸收者？——RCEP关税分期减让与亚太贸易网络逆向冲击韧性/repo_rcep_shock_v2/repo`
- Preflight status: **FAIL**
- Failures: required_file_differs_from_head:research_network_tvp_var.py
- Warnings: git_worktree_is_dirty, import_time_side_effect_indicator_present, no_top_level_license_file
- `research_data_construction.py`: sha256 `a88245fdbe451a368358af5776722802ab10bb3b03a4e8cf1ab3e24d9d1d836d`; tracked=True; symlink=False; Git status=`clean`
- `research_network_tvp_var.py`: sha256 `7378bf12e1a3ae72ce584577437aa99ef3b025f6228ac5a8ed88d55ada402ecd`; tracked=True; symlink=False; Git status=`M repo/research_network_tvp_var.py`
- `config.py`: sha256 `13aac959b623fb3e569b37f680c2f1b72b3ad0bad6d3b09d01bef36eae5e991f`; tracked=True; symlink=False; Git status=`clean`
- Missing required APIs: none
- Absolute-path indicators: 0
- Credential/private-key indicators: 0
- Import-time side-effect indicators: 5
- Dependency credential/private-key indicators: 0
- Dependency import-time side-effect indicators: 0

## C3

- Supplied path: `/Users/wuyilin/Desktop/2026学科竞赛/谁在托底中国新能源关键中间品供应链？——基于RCEP—“一带一路”多层贸易网络的逆向冲击韧性研究/external/Who-Absorbs-the-Shock/repo`
- Preflight status: **WARN**
- Failures: none
- Warnings: import_time_side_effect_indicator_present, no_top_level_license_file
- `research_data_construction.py`: sha256 `a88245fdbe451a368358af5776722802ab10bb3b03a4e8cf1ab3e24d9d1d836d`; tracked=True; symlink=False; Git status=`clean`
- `research_network_tvp_var.py`: sha256 `ea6568b0509ed62c62ab12189570576b31251fd921f59e1849a8c2e34b4fbc63`; tracked=True; symlink=False; Git status=`clean`
- `config.py`: sha256 `13aac959b623fb3e569b37f680c2f1b72b3ad0bad6d3b09d01bef36eae5e991f`; tracked=True; symlink=False; Git status=`clean`
- Missing required APIs: none
- Absolute-path indicators: 0
- Credential/private-key indicators: 0
- Import-time side-effect indicators: 5
- Dependency credential/private-key indicators: 0
- Dependency import-time side-effect indicators: 0

## Author Decision Still Required

No candidate is production-authorized. Before a trust manifest can be drafted, the author must identify one candidate and confirm ownership, licence/permitted use, and whether any private-code dependency may be used for this manuscript rebuild.

Even after that decision, production execution must remain closed until the selected checkout is clean or its deviations are resolved, every code dependency is hash-bound, and the manifest candidate is reviewed and explicitly signed off.
