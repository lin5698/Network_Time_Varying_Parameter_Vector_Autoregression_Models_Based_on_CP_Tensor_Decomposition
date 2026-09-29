# REC-M5 Conflict Copy Disposition (V1, 2026-08-26)

Record class: `conflict_copy_disposition`
Generated: 2026-08-26 (Asia/Shanghai)
Authority: author structured decision `conflict_disposition = per-audit-recommendation` (2026-08-26).
Evidence base: pairwise SHA-256 audit table (369 pairs) frozen in the JSON companion; execution journal at `tmp/conflict_disposition_journal_20260826.txt`.

## Actions executed

| class | count | action |
| --- | --- | --- |
| BYTE_IDENTICAL_DELETABLE_CANDIDATE | 341 | deleted after per-file hash re-verification |
| DIFFERS — copy strictly older generation | 15 | deleted after hash re-verification; originals authoritative (4 of these were UNTRACKED superseded-generation copies inside refine-logs whose originals hash-match the governance chain) |
| DIFFERS — same-mtime divergent older draft | 2 | MOVED to `archive/icloud_conflict_quarantine_20260826/` preserving relative paths (`discussion 2.md`, `build_natcs_framework_figure 2.py`) |
| ORIGINAL_MISSING (superseded `_archives` orphans) | 11 | kept in place |

Hash-drift or failure events: **0**. Post-condition: exactly 11 `* 2.*` files remain repo-wide, all inside superseded archive trees; manuscript_src and scripts working dirs contain no conflict copies.

No governed byte was altered: deletions touched only untracked `' 2.'` sync artifacts; the two relocated drafts are preserved intact under the quarantine path with hashes recorded in the JSON companion.
