# REC-M5 Semantic Recheck Service Incident V4

Result: `BLOCKED`

## Recovery attempt

A bounded read-only CLI attempt was requested with `gpt-5.6-terra` and
reasoning `max`, using the six current M5-C input files. The returned structured
payload reported `verdict=BLOCKED`, but its own provenance was `gpt-5 (Codex)`
with reasoning `high`. This model-route mismatch makes the payload unusable as
the requested Terra semantic adjudication. It is retained only as a diagnostic;
service failure or provenance mismatch is never a PASS.

Temporary output SHA-256:

`c3e84d4caef28945c02fb96d0dcb4fd3f0158ae06d40c6692829d19bb3d728b2`

## Role disposition

Scientific-boundary, editorial-traceability, and governance-manifest remain
`BLOCKED`. The diagnostic payload found no fail-level overclaim, but that
observation does not replace a verifiable Terra/max semantic receipt.

## Input and deterministic boundary

The six input hashes remain those recorded in V8 and the Terra receipts. The
reported `85/85` core checks and `247/247` M4 checks are deterministic
corroboration only. They do not authorize semantic acceptance, manuscript
application, formal-register mutation, claim activation, or M5-D/M5-F promotion.

## Mutation policy

This was review-only and record-only. No manuscript source, formal register,
scientific payload, authorization file, generated TeX, or Git state was changed.
The previously prohibited E4 main and duplicate-final paths were not read.

Changed paths, and only these paths:

- `refine-logs/REC-M5_SEMANTIC_RECHECK_SERVICE_INCIDENT_V4_20260812.md`
- `refine-logs/REC-M5_SEMANTIC_RECHECK_SERVICE_INCIDENT_V4_20260812.json`

## Next gate

Retry only after the service can return a verifiable `gpt-5.6-terra`/`max`
payload for all three roles, with exact current-input hashes and explicit
semantic findings. Until then the M5-C gate remains `BLOCKED_NOT_PASS`.
