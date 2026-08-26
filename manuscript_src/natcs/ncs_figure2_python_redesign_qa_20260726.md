# Figure 2 Python Redesign QA

Date: 2026-07-26

Status: source-only figure QA. No manuscript build, submission promotion,
scientific execution or audit-status change is implied.

## Scientific and visual audit

- Core conclusion: query preservation is a factorization property of the
  retained computational object.
- Hero evidence: `Q(W1) = h(W1) o T(W0)`.
- Exact negative evidence: unrestricted pairs `(0,0)` and `(-W0,I)` share the
  retained map at `W0` and disagree at `W1 != W0`.
- Constructive evidence: the diagonal rowwise inverse is shown beside the
  unrestricted boundary with its row conditions visible.
- Operational consequence: endpoint availability is classified before error
  comparison.
- Evidence exclusions: no Family-2, E3, RCEP or NYC result appears.

The 4,320 x 2,970 original PNG was inspected after the second layout pass.
Panel-b text remains within the right boundary, the structured-inverse labels
do not overlap the query arrow, and the endpoint strip remains subordinate to
the factorization panel. Warm, cool and neutral encodings remain distinguishable
without relying on a red/green contrast.

## Export verification

Fresh Python-only generation and checks reported:

```text
Figure 2 Python-backend and evidence-boundary contract test passed.
Figure-source editability test passed.
PNG: 4320 x 2970; 600 x 600 dpi; RGBA
PDF: 518.4 x 356.4 pt; one page
PDF fonts: Type 0 embedded Arial variants; no Type 3 font
SVG: 61 text nodes; 0 embedded images
```

Frozen asset hashes for this QA pass:

- SVG: `2404b1c0dbb3604f6e6ccca837e58e6d9f97690fd8ec053bd827b3891dda834d`
- PDF: `3146cbedee97ae8cd66031a8832c095ea6e0ee03ac67c5b0be429fa5ce108b94`
- PNG: `4ac4881f71cb96168412b7d0e2e26ac0ea72f5c335da1e9be6408a11e061621b`

## Manuscript placement

The source manuscript sequence is now:

1. Figure 1: callable learned object.
2. Figure 2: exact query certificate and constructive structured route.
3. Figure 3: released controlled recovery and strict native qualification.

The build entry point generates Figure 2 through the Python script and uses
separate vector and raster assets. The complete manuscript build remains
blocked by the controlling audits and was not run during this QA pass.
