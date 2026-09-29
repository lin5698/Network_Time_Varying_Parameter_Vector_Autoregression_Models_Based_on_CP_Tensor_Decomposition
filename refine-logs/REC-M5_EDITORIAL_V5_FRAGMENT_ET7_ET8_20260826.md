# REC-M5 EDITORIAL FRAGMENT ET7-ET8 (lane_a2_frag_ed_et7_et8)

- Fragment id: `REC-M5_EDITORIAL_V5_FRAGMENT_ET7_ET8_20260826`
- Date: 2026-08-26 (Asia/Shanghai)
- Lane: editorial-traceability, independent read-only review fragment
- Parent adjudication: feeds `REC-M5_EDITORIAL_RECHECK_V5_20260826`

## VERDICTS (fail-closed)

| Task | Verdict |
| --- | --- |
| **E-T7** — Diff discipline (hunk→revision-log mapping) | **PASS** |
| **E-T8** — Byte-generation declaration | **PASS** |

---

## E-T7 — Diff discipline: full hunk→log mapping

Instrument: `tmp/v1_v2_unified.diff` (114 lines total, 2 file-header lines + 9 hunks), pre-computed by the orchestrator party's shell; adjudicated here, not produced here.

### Hunk→log mapping table

| # | Hunk header (old → new) | Diff body lines | Content change | Maps to | Verification performed |
| --- | --- | --- | --- | --- | --- |
| A1/A2 | `@@ -1,6 +1,6 @@` | L4–L11 | Title `...Patch V1`→`...Patch V2`; `Generated: 2026-08-11T23:06:28+08:00`→`Generated: 2026-08-26 (Asia/Shanghai). Supersedes the bytes of REC-M5_REVIEW_PATCH_V1_20260811 (which remain frozen and unmodified).` | Structural header/provenance change (H1 title, H2 provenance); not numbered log entries; entailed by the V2 document header itself and the log-basis authorization sentence | 6 ctx-equivalent lines both sides (4 ctx + 1 del + 1 add); new side equals V2[1..6] verbatim |
| B | `@@ -15,6 +15,20 @@` | L13–L32 | Insertion of `## V2 revision log`: heading + blank + Basis paragraph (editorial recheck `REC-M5_EDITORIAL_RECHECK_V4_20260823`, sole FAIL E-T3; author authorization 2026-08-26, `et3_remediation = V2 patch re-review`) + blank + table header/separator + 7 rows (R1; R2a/R2b; R3; R4; R5a–e; C1; C2a/C2b) + trailing separator blank | **H3** — insertion of the entire `## V2 revision log` block | Forced composition: 14 adds, 0 dels, 6 ctx → net **+14** ✓ matches "+14 log insertion"; block equals V2[18..31] verbatim |
| C | `@@ -85,7 +99,7 @@` | L34–L41 | G04 Proposed paragraph 1: backticked raw CSV field identifiers `` `coef_error_median` `` / `` `girf_error_median` `` removed; replaced by verbal naming "the same scenario's effective-operator error or finite-horizon unit-shock response error, respectively" | **H4** = **R3 / F3** (moderate) | 1 del + 1 add + 6 ctx (old 7 = new 7 ✓); offset shift +14 ✓; new line equals V2[102] verbatim |
| D | `@@ -97,7 +111,7 @@` | L43–L50 | G04 Proposed paragraph 4: (i) `` `NOT_RUN` `` / `` `BLOCKED` `` and the governance term "claim activation" removed → "it was not executed under this benchmark's evaluation protocol, carries no evaluative claim of its own, and was not used to extend the benchmark result"; (ii) "author-confirmed amplitudes" → "fixed, separately documented amplitudes" (first of two) | **H5a** = **R1 / F1** (major) AND **H5b** = **R2a / F2a** — one hunk covers both adjacent edits within the same paragraph, as anticipated | 1 del + 1 add + 6 ctx ✓; offset +14 ✓; new line equals V2[114] verbatim |
| E | `@@ -112,13 +126,11 @@` | L52–L65 | (i) G05-A table final row: `Separate gate`×3 → `Separate design`×3; `Simulation-only promotion gate` → `Simulation-only qualification under a pre-registered decision rule`. (ii) G05-B: deletion of blank line + duplicated `Proposed text:` label preceding `Proposed reader-facing text:` | **H6** = **R5a / F5** (G05-A row) AND **H7** = **C1** (advisory, G05-B duplicate-label removal) | Composition forced: 1 add + 3 dels + 10 ctx → old 13, new 11, **net −2** ✓ (arithmetic verified: the −2 is exactly the two deleted C1 lines minus the one replacement-row add); offset +14 ✓; results equal V2[129], V2[133]→blank(134)→`Proposed reader-facing text:`(135) verbatim |
| F | `@@ -142,7 +154,7 @@` | L67–L74 | G05-D paragraph: "author-confirmed amplitudes" → "fixed, separately documented amplitudes" (second of two) | **H8** = **R2b / F2b** | 1 del + 1 add + 6 ctx ✓; offset now **+12** (= +14 − 2, first hunk carrying the C1 deletion) ✓; new line equals V2[157] verbatim |
| G | `@@ -158,12 +170,12 @@` | L76–L91 | G05-F, three edit sites: (i) header cell `Promotion status` → `Rule outcome`; (ii) both data cells `Not promoted` → `Threshold not met` (CP anchor split; Tucker anchor split); (iii) prose `prespecified promotion rule` → `pre-registered decision rule` | **H9–H11** = **R5b–e / F5** (G05-F header/cells/prose), three sites inside one hunk | 4 dels + 4 adds + 8 ctx → old 12 = new 12, net 0 ✓; offset +12 ✓; results equal V2[173], V2[175–176], V2[178] verbatim |
| H | `@@ -228,7 +240,7 @@` | L93–L100 | G09 manifest-only internal traceability note gains "; do not apply as manuscript text" | **H12** = **C2a** (advisory) | 1 del + 1 add + 6 ctx ✓; offset +12 ✓; result equals V2[243] verbatim |
| I | `@@ -236,10 +248,10 @@` | L102–L114 | G10: (i) proposed text: "`NOT_RUN/ABSTAIN`" → ", and we abstain from any claim at either scale"; "unavailable (`BLOCKED/null`)" → "unavailable for this audit". (ii) internal traceability note AND internal state record each gain "; do not apply as manuscript text" (state record itself retains the codes, consistently with its manifest-only status) | **H13** = **R4 / F4** AND **H14** = **C2b** — one hunk covers both | 3 dels + 3 adds + 7 ctx → old 10 = new 10, net 0 ✓; offset +12 ✓; results equal V2[251], V2[253–254] verbatim |

### Coverage equality

Every logged revision appears in the diff, nothing is unmapped:

| Log entry | Finding | Realized in hunk(s) | Confirmed |
| --- | --- | --- | --- |
| R1 | F1 (major) | D | ✓ codes `NOT_RUN`/`BLOCKED` + "claim activation" gone from G04-P4 reader-facing text |
| R2a | F2 (moderate) | D | ✓ first "fixed, separately documented amplitudes" |
| R2b | F2 (moderate) | F | ✓ second instance (twice total, exactly as logged) |
| R3 | F3 (moderate) | C | ✓ CSV identifiers removed, metrics named verbally |
| R4 | F4 (moderate) | I | ✓ plain abstention/unavailability wording |
| R5a | F5 (minor) | E | ✓ G05-A row de-gated |
| R5b–d | F5 (minor) | G | ✓ G05-F header cell + both outcome cells |
| R5e | F5 (minor) | G | ✓ G05-F prose decision-rule restatement |
| C1 | advisory | E | ✓ duplicate label removed |
| C2a | advisory | H | ✓ G09 note harmonized |
| C2b | advisory | I | ✓ both G10 manifest-only notes harmonized |
| (structural) | — | A1/A2, B | ✓ V2 identity/provenance header + the revision-log block itself |

Exactly 9 hunk headers exist; all 9 are mapped; every del/add pair in every hunk is enumerated above; all remaining body lines are unchanged context. No unmapped change exists.

### Net line arithmetic (verified)

- Σ old counts = 6+6+7+7+13+7+12+7+10 = **75**; Σ new counts = 6+20+7+7+11+7+12+7+10 = **87**; net **+12**.
- Decomposition: **+14** (revision-log insertion, hunk B) **− 2** (C1 deletion, hunk E) = **+12** ✓.
- V2 measured directly at **298 lines** (read tool line census) ⇒ V1 = 298 − 12 = **286 lines**, entailed arithmetically from the diff alone — consistent with the claimed 286→298 without this lane ever opening a V1 byte (see E-T8).
- Per-hunk cumulative offset: +14 through hunk E; +12 from hunk F onward ✓ (shift drops by exactly the C1 −2).
- Bidirectional spot-verification: the new side of every hunk was placed against the actual V2 file bytes (V2 lines 1–6, 15–34, 99–105, 111–117, 126–135, 154–160, 170–181, 240–246, 248–257) — all match verbatim.

### Observations (non-failing, recorded for downstream lanes)

1. Untouched V1-carried regions still contain register items outside the findings' logged scope — e.g. V2[37] "simulation-only negative promotion gate" (Response strategy summary) and V2[139] retained `NOT_RUN`/"claim activation"/`BLOCKED` inside the G05-B *manifest-only* internal E01 traceability record. These bytes are identical to V1 (absent from the diff), i.e. they are **not unmapped changes**; E-T7 adjudicates hunk↔log completeness, not a whole-file semantic sweep. Flagged so later tasks scope their own sweeps.
2. The diff instrument embeds filesystem timestamps (V1 `2026-08-12 15:11:03`, V2 `2026-08-26 11:35:00`) and carries no embedded content hash; it is orchestrator shell instrumentation, adjudicated as such (see provenance below), not hash-bound by G-T1/G-T8.

**E-T7 verdict: PASS** — coverage equality holds; nothing unmapped; all arithmetic consistent.

---

## E-T8 — Byte-generation declaration

Declared from the governance receipt `REC-M5_GOVERNANCE_RECHECK_V6_20260826.md`'s **independently measured** tables (G-T1: `shasum -a 256`, 6/6 MATCH vs authoritative expected values; G-T8: open/access declaration plus tree-wide superseded-copy search) — not merely from orchestrator claims.

| Input family | Generation consumed by THIS lane | Independent measurement relied upon | Opened by this lane? |
| --- | --- | --- | --- |
| Patch V2 markdown `REC-M5_REVIEW_PATCH_V2_20260826.md` | **Current generation** (V2 bytes, sha-256 `8a9bf747ea18e997387fdbbc6f8c486bb0a7ee76721c4f2264ffa853b641bdf0`, 29083 B) | G-T1 row 1 MATCH; same value re-declared in G-T8 | Yes — read (its `## V2 revision log`) |
| Patch V2 JSON `REC-M5_REVIEW_PATCH_V2_20260826.json` | **Current generation** (sha-256 `5e1697d22ac847825e37c4090ee2e28af0385c3015ecc1d8a048bb3cbda5f2ce`) | G-T1 row 2 MATCH | No — not opened; generation identified by measurement only |
| Author-input pair `REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.{md,json}` | **Current generation** (`1555484a…b9341` / `ebb639ed…2d8b6`) — the `_V1_` token is name-generation, not a superseded byte state; G-T1 rows 3–4 MATCH confirms both files are the authoritative current bytes | G-T1 rows 3–4 | No — not opened |
| Governance baseline pair `REC-M5_GOVERNANCE_BASELINE_V10_20260812.{md,json}` | **Current generation** (`dfd4385f…00539` / `94668a91…fd3ee`) | G-T1 rows 5–6 MATCH | No — not opened |
| Superseded `' 2.'` duplicate-generation copies | **Do not exist**: G-T8 records spot-verification absent — no `' 2.'` filenames anywhere in `refine-logs/`, and a whole-tree search finds exactly one copy of each of the three input basename families | G-T8 (deletion corroborated by `REC-M5_CONFLICT_DISPOSITION_V1_20260826.json`, context-only) | None exist; none consumed |
| V1 patch bytes `REC-M5_REVIEW_PATCH_V1_20260811.{md,json}` | **Not consumed by anyone in this lane** — zero V1-byte access; the V1↔V2 comparison was made exclusively via the pre-computed `tmp/v1_v2_unified.diff` instrument | G-T8 "Not touched" statement (governance lane) + this lane's own session record (only three reads: diff, V2 md, V6 receipt); V1 supersedes-hash `69888df4…` known only from recorded values (G-T3), never self-hashed | No — deliberately avoided |
| `tmp/v1_v2_unified.diff` (instrument) | Orchestrator-produced shell artifact, consumed as instrumentation for E-T7; **outside** the six authoritative inputs and not hash-covered by G-T1/G-T8 | Provenance disclosure below | Yes — read |

Declaration summary: every byte this lane consumed is accounted to its current generation via the V6 receipt's independently measured hash tables (patch V2 md/json current; author-input pair current; baseline pair current); no superseded `' 2.'` copies exist tree-wide and none were consumed; nobody in this lane opened the V1 patch markdown or JSON (the diff file was consumed instead). Nothing consumed is of unknown or stale generation.

**E-T8 verdict: PASS**

---

## Provenance disclosure

- Producing agent/model: **ox-alpha** (stealth model via DeepSeek Harness).
- Self-adjudicated fragment: the E-T7/E-T8 verdicts above were adjudicated by the producing agent itself; no second independent agent cross-checked them within this session.
- Reads-only lane: the sole write product of this session is this fragment file (`refine-logs/REC-M5_EDITORIAL_V5_FRAGMENT_ET7_ET8_20260826.md`).
- No shell/bash/glob/grep was invoked by this lane; read/write text tools only. All line counts cited were taken from read-tool output.
- Instrument disclosure: `tmp/v1_v2_unified.diff` was produced by the **orchestrator party's shell** (not by this lane) and is adjudicated here as pre-computed instrumentation; its internal arithmetic and its new side were independently reconciled against the actual V2 bytes by this lane.
- Hash reliance disclosure: this lane executed no hashing; all sha-256 values are quoted from the governance V6 receipt's G-T1/G-T8 measured tables as instructed.
- No authorization is issued or implied by this fragment; `applied=false` and `submission_ready=false` remain operative; no scientific ceiling is altered.
