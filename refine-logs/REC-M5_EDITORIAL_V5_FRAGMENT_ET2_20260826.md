# REC-M5 Editorial Traceability V5 — Fragment E-T2 (26-Unit Traceability on V2)

- fragment_id: `E-T2`
- lane: editorial-traceability, independent read-only reviewer fragment
- generated: 2026-08-26 (Asia/Shanghai)
- subject under review: `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.json` (machine manifest, read in full) and restricted sections of `refine-logs/REC-M5_REVIEW_PATCH_V2_20260826.md` (`## Patch index`, lines 53–66; `## Unit coverage`, lines 256–274)
- hash cross-reference: expected manifest sha256 `5e1697d22ac847825e37c4090ee2e28af0385c3015ecc1d8a048bb3cbda5f2ce` agrees with the value recorded as measured-and-matched in `refine-logs/REC-M5_GOVERNANCE_RECHECK_V6_20260826.md`, G-T1 table row 2 (this lane performed no shell hashing; see provenance)

## VERDICT E-T2: PASS

All four E-T2 checks pass on current measurement of the V2 manifest bytes. Zero violations found. Measured numbers below.

---

## T2.1 — Enumeration and uniqueness: PASS

- `unit_coverage` rows counted: **26 / 26** (matches `verification.unit_count_expected = 26` and self-report `unit_count_actual = 26`).
- Duplicate `unit_id` values: **0**. All 26 identifiers are distinct (also 26 distinct `(source_item, unit_id)` pairs).

Full enumeration as read from the JSON (row order preserved):

| # | unit_id | source_item | group |
| --- | --- | --- | --- |
| 1 | P-001 | V1-026 | G05 |
| 2 | P-002 | V1-026 | G01 |
| 3 | P-003 | V1-026 | G04 |
| 4 | V1-033-M01 | V1-033 | G02 |
| 5 | V1-033-M02 | V1-033 | G02 |
| 6 | V1-033-M03 | V1-033 | G03 |
| 7 | V1-033-R01 | V1-033 | G04 |
| 8 | V1-033-R02 | V1-033 | G04 |
| 9 | V1-033-R03 | V1-033 | G04 |
| 10 | V1-033-R04 | V1-033 | G04 |
| 11 | V1-033-R05 | V1-033 | G04 |
| 12 | V1-033-S01 | V1-033 | G05 |
| 13 | V1-033-S02 | V1-033 | G05 |
| 14 | V1-033-S03 | V1-033 | G05 |
| 15 | V1-033-S04 | V1-033 | G05 |
| 16 | V1-033-S05 | V1-033 | G05 |
| 17 | V1-045-RANK | V1-045 | G05 |
| 18 | V1-045-WINDOW | V1-045 | G05 |
| 19 | V1-045-ALS | V1-045 | G06 |
| 20 | V1-045-TOPOLOGY | V1-045 | G07 |
| 21 | V1-045-STABILITY | V1-045 | G08 |
| 22 | V1-045-FAILURE | V1-045 | G05 |
| 23 | V1-045-REPLICATION | V1-045 | G09 |
| 24 | V1-045-SCOPE | V1-045 | G09 |
| 25 | V1-045-UNRUN | V1-045 | G10 |
| 26 | V1-045-RESOURCE | V1-045 | G10 |

## T2.2 — Source-item and single-group-anchor validity: PASS

- Source items present: **only** {V1-026, V1-033, V1-045}; no other or malformed value appears. Every one of the 26 rows traces to a valid source_item.
- Measured distribution: **V1-026 ×3** (P-001, P-002, P-003), **V1-033 ×13** (M01–M03, R01–R05, S01–S05), **V1-045 ×10** (RANK, WINDOW, ALS, TOPOLOGY, STABILITY, FAILURE, REPLICATION, SCOPE, UNRUN, RESOURCE). Total 3+13+10 = 26. Matches the expected distribution exactly (verified, not assumed).
- Exactly one group anchor per unit: every row carries a single scalar `group`; no multi-valued assignment; all 26 values lie inside G01–G10.

## T2.3 — Group coverage G01–G10: PASS

Measured units per group (from `unit_coverage`):

| Group | Count | Units |
| --- | ---: | --- |
| G01 | 1 | V1-026:P-002 |
| G02 | 2 | V1-033:M01, V1-033:M02 |
| G03 | 1 | V1-033:M03 |
| G04 | 6 | V1-026:P-003; V1-033:R01–R05 |
| G05 | 9 | V1-026:P-001; V1-033:S01–S05; V1-045:RANK, WINDOW, FAILURE |
| G06 | 1 | V1-045:ALS |
| G07 | 1 | V1-045:TOPOLOGY |
| G08 | 1 | V1-045:STABILITY |
| G09 | 2 | V1-045:REPLICATION, SCOPE |
| G10 | 2 | V1-045:UNRUN, RESOURCE |

- Groups with ≥1 unit: **10/10** (minimum count = 1, at G01/G03/G06/G07/G08).
- Sum of per-group counts = **26** = total rows; no double counting.
- Units mapping outside G01–G10: **0**. The JSON `traceability` object contains exactly the ten keys G01…G10 (no extra, no missing group key), and `edit_groups` likewise declares G01–G10.

## T2.4 — Bidirectional consistency: PASS

**(a) `traceability.G*.source_units` ↔ `unit_coverage` rows — exact set equality per group, no missing/extra.**
Each composite `"source_item:unit_id"` entry was resolved against the `(source_item, unit_id)` rows carrying that group:

- G01 [V1-026:P-002] ↔ rows {P-002} — equal.
- G02 [V1-033:M01, V1-033:M02] ↔ rows {M01, M02} — equal.
- G03 [V1-033:M03] ↔ rows {M03} — equal.
- G04 [V1-026:P-003; V1-033:R01–R05] ↔ rows {P-003, R01–R05} — equal (6/6).
- G05 [V1-026:P-001; V1-033:S01–S05; V1-045:RANK, WINDOW, FAILURE] ↔ rows {same 9} — equal (9/9).
- G06 [V1-045:ALS], G07 [V1-045:TOPOLOGY], G08 [V1-045:STABILITY] ↔ rows — equal (1/1 each).
- G09 [V1-045:REPLICATION, SCOPE]; G10 [V1-045:UNRUN, RESOURCE] ↔ rows — equal (2/2 each).
- Union of all ten `source_units` lists = **26 distinct composites = all 26 rows**: 0 units missing from traceability, 0 extra/unresolvable entries.

**(b) `clause_traceability` — every unit referenced by ≥1 clause; no unknown-unit references.**
17 clause keys audited (G01-P1; G02-P1; G03-P1; G04-P1…P4; G05-A…F; G06-P1; G07-P1; G08-P1; G09-P1; G10-P1), carrying 26 references total:

| Unit | Clause(s) | Unit | Clause(s) |
| --- | --- | --- | --- |
| P-001 | G05-B | V1-033-S03 | G05-E |
| P-002 | G01-P1 | V1-033-S04 | G05-F |
| P-003 | G04-P4 | V1-033-S05 | G05-F |
| V1-033-M01 | G02-P1 | V1-045-RANK | G05-A |
| V1-033-M02 | G02-P1 | V1-045-WINDOW | G05-A |
| V1-033-M03 | G03-P1 | V1-045-ALS | G06-P1 |
| V1-033-R01 | G04-P1 | V1-045-TOPOLOGY | G07-P1 |
| V1-033-R02 | G04-P1 | V1-045-STABILITY | G08-P1 |
| V1-033-R03 | G04-P2 | V1-045-FAILURE | G05-C |
| V1-033-R04 | G04-P3 | V1-045-REPLICATION | G09-P1 |
| V1-033-R05 | G04-P4 | V1-045-SCOPE | G09-P1 |
| V1-033-S01 | G05-C | V1-045-UNRUN | G10-P1 |
| V1-033-S02 | G05-D | V1-045-RESOURCE | G10-P1 |

- Orphan units (referenced by no clause): **0** (each of the 26 is referenced exactly once; 26 references / 26 units).
- Dangling references (clause citing an unknown unit_id): **0**; every reference resolves to a valid unit.
- Structural coherence: every clause's references stay within its own prefix group's unit set (e.g., G04-P4 cites only the two G04 units P-003 and R05); no cross-group misplacement observed.

**(c) Markdown patch index agrees with JSON.**
The `## Patch index` table (md lines 53–66) lists exactly groups G01–G10 with REC-M3 unit lists identical to the JSON per-group sets measured in T2.3/T2.4(a): G01=P-002; G02=M01,M02; G03=M03; G04=P-003,R01–R05; G05=P-001,S01–S05,RANK,WINDOW,FAILURE; G06=ALS; G07=TOPOLOGY; G08=STABILITY; G09=REPLICATION,SCOPE; G10=UNRUN,RESOURCE. Zero disagreement across all 10 rows.
The `## Unit coverage` section (md lines 256–276) states "all 26 REC-M3 units … represented once", V1-026 3/3, V1-033 13/13, V1-045 10/10 — each agreeing with the measured counts — and its V1-045 crosswalk table (RANK/WINDOW→P1/G05; ALS→P2/G06; TOPOLOGY→P3/G07; STABILITY→P4/G08; FAILURE→P5/G05; REPLICATION/SCOPE→P6/G09; UNRUN/RESOURCE→P7/G10) agrees row-for-row with the JSON `proposal_crosswalk` and with each unit's `unit_coverage.group`.

## Violations

None. No duplicate unit_ids, no invalid source_item, no multi-group or out-of-range group assignment, no empty group, no traceability/clause asymmetry, no markdown↔JSON divergence.

## Corroboration notes (context, non-binding)

- Governance lane receipt `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` G-T6 independently recorded the same facts (26 rows, 26 unique, distribution 3/13/10) — consistent with this fragment's independent recount.
- Manifest self-check block `verification` states `unit_count_expected: 26`, `unit_count_actual: 26`, `unit_uniqueness: PASS`, `clause_traceability: PASS` — all four self-reports are consistent with this lane's measurements.

## Provenance disclosure

- Producing agent/model: **ox-alpha** (stealth model via DeepSeek Harness), executing as an independent delegated read-only REVIEW FRAGMENT worker for the editorial-traceability lane.
- **Self-adjudicated fragment**: the PASS verdict above was adjudicated by the producing agent itself against the pre-stated E-T2 expectations; no second independent agent cross-checked it within this session.
- **Reads-only scope honored**: opened exactly three files — the V2 machine manifest (full), the V2 markdown patch (consumed only for evidence from its `## Patch index` and `## Unit coverage` sections), and `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md` (solely to cross-reference the expected manifest sha256 via its G-T1 table). No manuscript, protected-baseline, or V1 byte was accessed.
- **No shell**: bash/glob/grep were never invoked per execution constraint. Consequence disclosed: the manifest sha256 was NOT recomputed by this lane; identity with the expected value `5e1697d2…f2ce` rests on the governance receipt's G-T1 measured-match record, not on a fresh hash here.
- **Sole write = this fragment**: `refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET2_20260826.md`. Nothing else created, modified, or deleted; no authorization issued or implied by this fragment; `applied=false` and `submission_ready=false` remain operative.
