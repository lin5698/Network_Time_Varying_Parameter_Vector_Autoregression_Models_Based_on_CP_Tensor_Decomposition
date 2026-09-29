# REC-P0 Repair Closure (V1, 2026-08-26)

Record class: `p0_repair_closure`
Generated: 2026-08-26 (Asia/Shanghai)
Authority: author chat instruction「同意上述分析，请继续后续工作」(2026-08-26) executing `docs/superpowers/plans/2026-08-26-followup-work-plan.md`; two structured author decisions taken the same day: `e4r007_handling = independent_review_first`, `icloud_migration = migrate_to_home_work`.

## Scope

Closes P0 (working-copy availability) defined by the 2026-08-23 follow-up plan and continued in the 2026-08-26 plan. All operations were host-side macOS actions plus read-only verification. Repository relocated out of the iCloud sync domain.

## Timeline (all times local, 2026-08-26)

| time | event |
| --- | --- |
| 03:01 | Baseline measured: placeholder files (size>0, blocks=0) across repo ≈ 9000 per top dir (.git 1147, archive 4200, output 1888, scripts 453, refine-logs 606, tests 99, manuscript_src 64, paper_rewriting_output 63, docs 3). Reads of placeholder bytes hang >60s (`REC-M5_RECHECK_DISPATCH_V1_20260823.md`, `PROOF_CHECK_STATE.json` confirmed). |
| 03:09 | Directory-level `brctl download` scheduled for every top-level subtree returned ok but zero materialization over 3 min (poll count stable at 9180). Strategy switched to enumerated per-file downloads. |
| 03:14–03:26 | Per-file parallel `brctl download` loop (`tmp/materialize_all.sh`): 9179 → 0 placeholders in ~12 minutes. Exit code 0. |
| 03:27 | Git health on repaired copy: `git rev-parse HEAD` = `e7ce60c28f27c17ecfffe5348dd04d8c957fb077`; branch `refs/heads/codex/m5-current-luna-science-recheck`; `git status --porcelain -uno` = 76 modified tracked files (uncommitted drift past HEAD — supersedes the 08-23 observation of an apparently clean tree, which was an artifact of dataless bytes matching index stat); full porcelain scan 666 lines including untracked additions; **`git fsck --full` exits rc=0** (dangling objects only; no corruption; previously dumped core). Audit-critical files `scripts/experiments/config.py`, `research_data_construction.py`, `research_network_tvp_var.py` are clean relative to HEAD. |
| 03:28 | M5-C frozen-input re-verification after re-materialization — all six measured SHA-256 MATCH the V10-chain values recorded 2026-08-23 (patch md/json, author-input md/json, governance baseline md/json). The intervening iCloud eviction changed no bytes. |
| 03:29 | Conflict-copy pairwise audit (`tmp/conflict_copy_audit_20260826.sh`, TSV at `tmp/conflict_copy_audit_20260826.tsv`): total 369; BYTE_IDENTICAL 341; DIFFERS 17; ORIGINAL_MISSING 11. See adjudication table below. No deletion performed. |
| 03:31 | Cold copy `rsync -a` to `$HOME/work/<repo>` (10285 files each side; du 4975528 vs 4975524 KiB); `git bundle create $HOME/work/repo-bundle-20260826.bundle --all` verifies "complete history"; six frozen inputs MATCH at destination; destination `git fsck --full` rc=0. |
| 03:33 | Source directory moved intact to `$HOME/.Trash/<repo>-pre-migration-20260826` (recoverable; outside sync domain). Final state at `$HOME/work/Network_Time_Varying_Parameter_Vector_Autoregression_Models_Based_on_CP_Tensor_Decomposition`: HEAD matches, 76 modified tracked, placeholder count 0. |

## Conflict-copy adjudication input (369 pairs; disposition NOT yet executed)

| class | count | detail |
| --- | --- | --- |
| BYTE_IDENTICAL_DELETABLE_CANDIDATE | 341 | pairwise sha256 equal |
| DIFFERS, copy strictly older (mtime earlier) | 15 | originals authoritative; includes 4 UNTRACKED superseded-generation copies in refine-logs (`REC-M5_REVIEW_PATCH_V1_20260811 2.{md,json}`, `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812 2.{md,json}`) whose originals hash-match the governance chain |
| DIFFERS, same mtime divergent older draft | 2 | `manuscript_src/natcs/discussion 2.md` (earlier representation-boundary framing vs current query-certified text) and `scripts/build_natcs_framework_figure 2.py` (pre-matplotlib variant); recommend preserve-or-review, not silent delete |
| ORIGINAL_MISSING | 11 | all inside superseded `_archives` snapshot trees; self-contained orphans |

Disposition requires separate author sign-off. This record deletes nothing.

## Concurrently dispatched (not part of this record's own actions)

Three read-only review lanes dispatched 2026-08-26 under the luna worker discipline: Lane A editorial traceability → `REC-M5_EDITORIAL_RECHECK_V4_20260823.{md,json}`; Lane B governance manifest → `REC-M5_GOVERNANCE_RECHECK_V5_20260823.{md,json}`; Lane C independent E4-R007 result-to-claim → `NCS_E4_R007_INDEPENDENT_RESULT_TO_CLAIM_V1_20260826.{md,json}`. Their receipts are authored by those lanes and disclose their own provenance. M5-C closure steps (closure record; registering three current-byte receipts into patch JSON, which invalidates hash `938e5218…`) remain sequenced AFTER both lanes report.

## Boundary statement

No modification to `manuscript_src/natcs/*.md`, `controlled_benchmark_contract.json`, formal register, pre-existing frozen records, authorization files or generated TeX. No `make` target, test suite or scientific entry executed. No claim activated; scientific execution remains NOT_AUTHORIZED. New files created this round: this record pair, `tmp/materialize_all.sh`, `tmp/conflict_copy_audit_20260826.sh`, `tmp/m5c_input_hash_recheck_20260826.sh`, `tmp/migrate_stage1.sh`, `tmp/conflict_copy_audit_20260826.tsv`, `tmp/placeholders_20260826.list`, plus the three lane receipt pairs listed above (authored by the lanes).
