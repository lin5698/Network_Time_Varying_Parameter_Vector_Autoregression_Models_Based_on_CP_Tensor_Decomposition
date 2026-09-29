# REC-M5 Semantic Recheck Service Incident V3

Result: `BLOCKED`

This is a unified current-version service-event record for the three Terra
semantic roles. It is review-only and record-only. A missing, timed-out,
interrupted, or otherwise unverifiable Terra response is not a PASS.

## Provenance and service disposition

- Required model: `gpt-5.6-terra`
- Required reasoning effort: `max`
- Roles: scientific-boundary, editorial-traceability, governance-manifest
- Scientific Terra receipt: `BLOCKED`; no verifiable semantic payload or
  terminal result was available.
- Editorial Terra receipt: `BLOCKED`; no completion signal or usable semantic
  payload was available before bounded shutdown.
- Governance Terra receipt: `BLOCKED`; both bounded waits timed out without a
  terminal result or usable semantic payload.
- All three roles remain `BLOCKED`; none may be counted as `PASS`.

## Current Terra receipt hashes

| Role | Receipt | SHA-256 |
| --- | --- | --- |
| scientific-boundary | `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V1_20260812.md` | `778833e44c849a48ddb4d2bb178f258365c372e053193dbb4b660cacf89f1e54` |
| scientific-boundary | `refine-logs/REC-M5_SCIENTIFIC_RECHECK_TERRA_V1_20260812.json` | `5dda9ea9b4385215a745e032fe9c7223b4d6670b08c3e70508a355d62e97cf1c` |
| editorial-traceability | `refine-logs/REC-M5_EDITORIAL_RECHECK_TERRA_V1_20260812.md` | `ec9a52eb9993a883b627298e90717116ebb67df77407823a9819af1c00c53c72` |
| editorial-traceability | `refine-logs/REC-M5_EDITORIAL_RECHECK_TERRA_V1_20260812.json` | `9e22d031fdc34a9296c900781030481017e97649b69e57c356d13f0f6acbbd09` |
| governance-manifest | `refine-logs/REC-M5_GOVERNANCE_RECHECK_TERRA_V1_20260812.md` | `d2a05cc123b8f0c6f3a74f3007fbb612a5fe35c9c329f59ec6df197139776488` |
| governance-manifest | `refine-logs/REC-M5_GOVERNANCE_RECHECK_TERRA_V1_20260812.json` | `720eea9aa3f628fd94e4287fc1ccda0ba9182eb33c22d13e3f5946a59fceea7e` |

## Current core input hashes

| Input | SHA-256 |
| --- | --- |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.md` | `336c3cc4e25276ac6eeb56d597b3fd8486e8a90d02c7d977ace172048138c07d` |
| `refine-logs/REC-M5_REVIEW_PATCH_V1_20260811.json` | `8d9b1d2a7536daa6a7f7cb3ade5bc0f5b0674d2087d5efeb2fd2a8dcbf3e603a` |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.md` | `d622854aba0b0e190ef8653fc87ab95324239be5257ff02d25478e2cdde571cd` |
| `refine-logs/REC-M5_AUTHOR_INPUT_REQUEST_V1_20260812.json` | `83197e8828f894cabf9b21fe108be0c61c751dc8c967bdca684dc1220dfe4913` |

## Deterministic evidence boundary

The prior local evidence reports `85/85` current-core checks and `247/247`
M4 allowlisted checks. These are deterministic corroboration only; they do not
replace a Terra semantic adjudication and do not permit a PASS. The current
patch remains review-only with its author-input bindings and paragraph coverage
unchanged.

## Promotion and mutation boundary

- M5-D manuscript application: not permitted; separate authorization remains
  required after a verifiable semantic PASS.
- M5-F formal-register change: not permitted; separate authorization remains
  required.
- Manuscript sources: `NOT_AUTHORIZED` to modify.
- Formal register: `NOT_AUTHORIZED` to modify.
- Scientific payload or execution authorization: `PROHIBITED`.
- Authorization files: `PROHIBITED` to modify.
- Generated TeX: `PROHIBITED` to modify or use as canonical ownership.
- Claim activation: `NOT_AUTHORIZED`.
- Git operations: `NONE`.

No E4 main or duplicate-final path was read for this record. The pre-existing
dirty worktree is preserved.

## Changed paths

- `refine-logs/REC-M5_SEMANTIC_RECHECK_SERVICE_INCIDENT_V3_20260812.md`
- `refine-logs/REC-M5_SEMANTIC_RECHECK_SERVICE_INCIDENT_V3_20260812.json`

