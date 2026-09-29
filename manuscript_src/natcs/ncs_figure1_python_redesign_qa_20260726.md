# NCS Figure 1 Python Redesign QA

Date: 2026-07-26

Status: Figure 1 source/export QA complete. This record does not activate E3,
RCEP or NYC evidence and does not change either controlling audit state.

## Visual Claim

Core conclusion: one fitted separated coefficient path remains callable when
the evaluation topology is observed, set to zero or supplied from a frozen
period; a collapsed total map without a declared inverse does not define the
same topology-substitution query.

Archetype: schematic-led composite with an asymmetric qualification strip.

Panel hierarchy:

- panel a is the dominant callable-object schematic;
- panel b shows three calls with the fitted state, shock and horizon held
  fixed;
- panel c is a neutral-grey qualification boundary and is visually
  subordinate to the positive capability.

The final visual check confirmed that panel a remains the first read, the
supplied topology enters at evaluation rather than fitting, the three readouts
share one path and no label is clipped or overlapped. The right boundary is not
encoded as a red failure panel.

Serves: novelty / clarity / rigour / visual communication.

## Backend And Export Contract

The source is `scripts/build_natcs_framework_figure.py`. Matplotlib now
generates SVG, PDF and PNG directly. `scripts/build_natcs_manuscript.mjs` no
longer invokes `rsvg-convert` for Figure 1.

| Check | Fresh evidence | Status |
| --- | --- | --- |
| Backend exclusivity | Python creates every Figure 1 export | PASS |
| Final width | PDF page width `518.4 pt`, approximately `183 mm` | PASS |
| SVG editability | `53` text elements; `0` embedded image elements | PASS |
| PDF fonts | Embedded CID TrueType Arial regular, bold and bold italic; no Type 3 font | PASS |
| Raster preview | `4320 x 3090 px` at approximately `600 dpi` | PASS |
| Palette | warm `#C85A3A`, cool `#367C8D`, neutral greys | PASS |
| Evidence traceability | conceptual schematic only; no quantitative mark or blocked outcome | PASS |

Current export SHA-256 values:

- SVG: `25cd0001c13eba8d7620a2a15965acc2da8f645262521532c95788a8ec61897f`
- PDF: `905dce456c87fbde5f1e0111fa56a5ee69f8211c005b295c5a8a45fb41a04995`
- PNG: `03e5c68646a961aba83c74254e521b5e4ebc0429e168e84fd8f1b5c37e21711f`

The latest direct re-render (same source and parameters; SVG/PDF metadata
timestamps changed) has SHA-256 values:

- SVG: `25cd0001c13eba8d7620a2a15965acc2da8f645262521532c95788a8ec61897f`
- PDF: `4a7b962daa4264fdc6a1ebfc577b17bfff3666918a7831703295d3c7cbe9ff69`
- PNG: `03e5c68646a961aba83c74254e521b5e4ebc0429e168e84fd8f1b5c37e21711f`

## Verification

Fresh commands and outcomes:

```text
node tests/test_figure1_python_backend.mjs
Figure 1 Python-backend contract test passed.

python3 -m py_compile scripts/build_natcs_framework_figure.py
exit 0

python3 scripts/build_natcs_framework_figure.py
exit 0
```

A Figure-1-only structure check confirmed editable SVG text and absence of an
embedded raster image. `tests/test_figure_source_editability.mjs` was also
attempted, but its read of the pre-existing
`output/natcs_evidence/fig_validation_recovery.svg` did not return. The test was
terminated without modifying Figure 2. Therefore this record claims Figure 1
source editability only, not completion of the combined Figure 1/2 gate.

## Remaining Figure-Sequence Work

1. Redesign Figure 2 around the exact factorization certificate and structured
   positive route using only released theorem/fixture evidence.
2. Rebuild Figure 3 from released controlled `N=15/N=30` recovery evidence and
   the strict native operating-boundary counts.
3. Keep all RCEP, NYC and E3 values out of active main figures.
4. Run manuscript-page visual QA only after the Figure 2 asset can be read and
   the active Figure 1-3 sequence has been rebuilt.
