from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_BASENAME = ROOT / "output" / "natcs_assets" / "figure1_natcs_framework"

WIDTH = 1536
HEIGHT = 1024


def svg_text(
    x: int,
    y: int,
    text: str,
    cls: str = "label",
    anchor: str = "start",
) -> str:
    return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{text}</text>'


def rect(x: int, y: int, w: int, h: int, cls: str = "box", rx: int = 0) -> str:
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>'


def edge(x1: int, y1: int, x2: int, y2: int, cls: str = "edge") -> str:
    return f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'


def connector(points: list[tuple[int, int]], cls: str = "edge") -> str:
    coords = " ".join(f"{x},{y}" for x, y in points)
    return f'<polyline class="{cls}" points="{coords}" fill="none"/>'


def node(
    x: int,
    y: int,
    label: str = "",
    r: int = 17,
    fill: str = "#ffffff",
    stroke: str = "#111111",
    label_cls: str = "nodeLabel",
) -> str:
    label_part = ""
    if label:
        label_part = f'<text class="{label_cls}" x="{x}" y="{y + 5}" text-anchor="middle">{label}</text>'
    return (
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="1.8"/>'
        f"{label_part}"
    )


def matrix_glyph(x: int, y: int, cell: int = 19, cols: int = 5, rows: int = 4) -> str:
    shades = [
        "#ececec",
        "#d0d0d0",
        "#f7f7f7",
        "#bebebe",
        "#e2e2e2",
        "#fafafa",
        "#d9d9d9",
        "#efefef",
        "#c6c6c6",
        "#ededed",
        "#d3d3d3",
        "#f3f3f3",
    ]
    out = [f'<g transform="translate({x},{y})">']
    for row in range(rows):
        for col in range(cols):
            shade = shades[(row * cols + col) % len(shades)]
            out.append(
                f'<rect x="{col * cell}" y="{row * cell}" width="{cell}" height="{cell}" '
                f'fill="{shade}" stroke="#9f9f9f" stroke-width="0.85"/>'
            )
    out.append(f'<text class="matrixDots" x="{cols * cell + 9}" y="{rows * cell - 31}">...</text>')
    out.append(f'<text class="matrixDots" x="{cols * cell - 33}" y="{rows * cell + 18}">...</text>')
    out.append("</g>")
    return "\n".join(out)


def mini_network(
    x: int,
    y: int,
    mode: str,
    scale: float = 1.0,
    labels: bool = True,
    frame: bool = False,
) -> str:
    def sx(value: float) -> int:
        return round(x + value * scale)

    def sy(value: float) -> int:
        return round(y + value * scale)

    pts = {
        "1": (sx(0), sy(44)),
        "2": (sx(60), sy(18)),
        "3": (sx(116), sy(40)),
        "4": (sx(48), sy(102)),
        "5": (sx(128), sy(96)),
    }
    if mode == "observed":
        edges = [("1", "2"), ("2", "3"), ("2", "4"), ("4", "5"), ("3", "5"), ("1", "4")]
        edge_cls = "edgeNoArrow"
        frame_cls = "boxMini"
        node_stroke = "#111111"
        node_cls = "nodeLabel"
    elif mode == "frozen":
        edges = [("1", "4"), ("4", "3"), ("2", "5"), ("1", "2")]
        edge_cls = "edgeDashNoArrow"
        frame_cls = "boxMiniDash"
        node_stroke = "#111111"
        node_cls = "nodeLabel"
    else:
        edges = []
        edge_cls = "edgeMutedNoArrow"
        frame_cls = "boxMiniMuted"
        node_stroke = "#777777"
        node_cls = "nodeLabelMuted"

    out: list[str] = []
    if frame:
        out.append(
            f'<rect class="{frame_cls}" x="{sx(-25)}" y="{sy(-8)}" '
            f'width="{round(180 * scale)}" height="{round(132 * scale)}" rx="6"/>'
        )
    for a, b in edges:
        x1, y1 = pts[a]
        x2, y2 = pts[b]
        out.append(edge(x1, y1, x2, y2, edge_cls))
    for idx, (k, (px, py)) in enumerate(pts.items()):
        fill = "#ffffff"
        if mode == "observed" and not labels and idx in {1, 2, 3}:
            fill = "#d4d4d4"
        out.append(
            node(
                px,
                py,
                k if labels else "",
                r=round(17 * scale),
                fill=fill,
                stroke=node_stroke,
                label_cls=node_cls,
            )
        )
    return "\n".join(out)


def response_card(
    x: int,
    y: int,
    w: int,
    h: int,
    formula: str,
    label: str,
    box_cls: str = "box",
    trace_cls: str = "trace",
) -> str:
    base_y = y + h - 43
    left = 38
    right = w - 56
    xs = [left + (right - left) * frac for frac in (0, 0.14, 0.28, 0.42, 0.56, 0.70, 0.84, 1)]
    offsets_by_trace = {
        "trace": [4, -13, 11, -3, 6, -9, 9, -1],
        "traceMuted": [1, -6, 5, -4, 3, -5, 4, -2],
        "traceDash": [8, -15, 13, -9, 11, -14, 12, -5],
    }
    offsets = offsets_by_trace.get(trace_cls, offsets_by_trace["trace"])
    points = [(round(x + px), base_y + dy) for px, dy in zip(xs, offsets)]
    trace_points = " ".join(f"{px},{py}" for px, py in points)
    return "\n".join(
        [
            rect(x, y, w, h, box_cls, rx=8),
            svg_text(x + w // 2, y + 46, formula, "mathCard", "middle"),
            svg_text(x + w // 2, y + 78, label, "tiny", "middle"),
            f'<polyline class="{trace_cls}" points="{trace_points}" fill="none"/>',
        ]
    )


def build_svg() -> str:
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        "<defs>",
        '  <marker id="arrow" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">',
        '    <polygon points="0,0 9,3.5 0,7" fill="#111111"/>',
        "  </marker>",
        '  <marker id="arrowGrey" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">',
        '    <polygon points="0,0 9,3.5 0,7" fill="#555555"/>',
        "  </marker>",
        "  <style>",
        "    .panel { font-family: Arial, Helvetica, sans-serif; font-size: 34px; font-weight: 700; fill: #111111; }",
        "    .labelBold { font-family: Arial, Helvetica, sans-serif; font-size: 24px; font-weight: 700; fill: #111111; }",
        "    .small { font-family: Arial, Helvetica, sans-serif; font-size: 21px; fill: #333333; }",
        "    .smallBold { font-family: Arial, Helvetica, sans-serif; font-size: 21px; font-weight: 700; fill: #111111; }",
        "    .tiny { font-family: Arial, Helvetica, sans-serif; font-size: 18px; fill: #444444; }",
        "    .micro { font-family: Arial, Helvetica, sans-serif; font-size: 15px; fill: #555555; }",
        "    .nodeLabel { font-family: Arial, Helvetica, sans-serif; font-size: 16px; fill: #111111; }",
        "    .nodeLabelMuted { font-family: Arial, Helvetica, sans-serif; font-size: 16px; fill: #4a4a4a; }",
        "    .matrixDots { font-family: Arial, Helvetica, sans-serif; font-size: 17px; font-weight: 700; fill: #333333; }",
        "    .math { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 30px; fill: #111111; }",
        "    .mathSmall { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 24px; fill: #111111; }",
        "    .mathCard { font-family: Georgia, 'Times New Roman', serif; font-style: italic; font-size: 23px; fill: #111111; }",
        "    .blocked { font-family: Arial, Helvetica, sans-serif; font-size: 19px; font-weight: 700; fill: #555555; }",
        "    .panelFrame { fill: #ffffff; stroke: #111111; stroke-width: 1.35; shape-rendering: crispEdges; }",
        "    .innerFrame { fill: #fbfbfb; stroke: #b8b8b8; stroke-width: 1.3; }",
        "    .box { fill: #ffffff; stroke: #111111; stroke-width: 1.75; }",
        "    .boxDash { fill: #ffffff; stroke: #111111; stroke-width: 1.75; stroke-dasharray: 8 6; }",
        "    .boxMuted { fill: #ffffff; stroke: #777777; stroke-width: 1.65; }",
        "    .boxArgument { fill: #ffffff; stroke: #555555; stroke-width: 1.65; }",
        "    .boxMini { fill: #ffffff; stroke: #111111; stroke-width: 1.75; }",
        "    .boxMiniDash { fill: #ffffff; stroke: #111111; stroke-width: 1.75; stroke-dasharray: 8 6; }",
        "    .boxMiniMuted { fill: #ffffff; stroke: #777777; stroke-width: 1.65; }",
        "    .band { fill: #f1f1f1; stroke: #b8b8b8; stroke-width: 1.75; }",
        "    .edge { stroke: #111111; stroke-width: 2.25; marker-end: url(#arrow); stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .edgeNoArrow { stroke: #111111; stroke-width: 2.25; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .edgeDashNoArrow { stroke: #111111; stroke-width: 2.1; stroke-dasharray: 7 5; stroke-linecap: butt; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .edgeDash { stroke: #111111; stroke-width: 2.1; stroke-dasharray: 7 5; marker-end: url(#arrow); stroke-linecap: butt; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .edgeMuted { stroke: #555555; stroke-width: 2; marker-end: url(#arrowGrey); stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .edgeMutedNoArrow { stroke: #777777; stroke-width: 1.9; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .trace { stroke: #111111; stroke-width: 2; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .traceMuted { stroke: #777777; stroke-width: 2; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .traceDash { stroke: #777777; stroke-width: 2; stroke-dasharray: 8 6; stroke-linecap: square; stroke-linejoin: miter; shape-rendering: geometricPrecision; }",
        "    .separator { stroke: #d1d1d1; stroke-width: 1.2; shape-rendering: crispEdges; }",
        "    .blockLine { stroke: #555555; stroke-width: 3.1; stroke-linecap: round; shape-rendering: geometricPrecision; }",
        "    .blockedCross { stroke: #555555; stroke-width: 2.7; stroke-linecap: round; shape-rendering: geometricPrecision; }",
        "  </style>",
        "</defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
    ]

    # Panel frames.
    parts += [
        rect(14, 15, 590, 994, "panelFrame"),
        rect(618, 15, 504, 994, "panelFrame"),
        rect(1136, 15, 386, 994, "panelFrame"),
    ]

    # Panel a: preserved object.
    parts += [
        svg_text(43, 66, "a", "panel"),
        svg_text(82, 63, "Query contract before readout", "labelBold"),
        svg_text(121, 182, "operator inputs", "smallBold", "middle"),
        rect(52, 230, 138, 116, "box", rx=7),
        svg_text(121, 281, "A<tspan baseline-shift=\"sub\" font-size=\"14\">k,t</tspan>", "math", "middle"),
        rect(52, 470, 138, 116, "box", rx=7),
        svg_text(121, 521, "B<tspan baseline-shift=\"sub\" font-size=\"14\">k,t</tspan>", "math", "middle"),
        svg_text(121, 672, "topology input", "smallBold", "middle"),
        mini_network(77, 711, "observed", scale=0.72, labels=False, frame=True),
        svg_text(121, 837, "last available W", "smallBold", "middle"),
        svg_text(326, 126, "evaluation operator", "smallBold", "middle"),
        rect(214, 156, 224, 724, "innerFrame", rx=12),
        rect(246, 205, 158, 166, "box", rx=8),
        svg_text(325, 246, "direct", "tiny", "middle"),
        svg_text(325, 283, "A<tspan baseline-shift=\"sub\" font-size=\"13\">k,t</tspan>", "mathSmall", "middle"),
        matrix_glyph(280, 307, cell=17, cols=4, rows=3),
        svg_text(325, 410, "+", "math", "middle"),
        rect(246, 445, 158, 166, "box", rx=8),
        svg_text(325, 486, "network", "tiny", "middle"),
        svg_text(325, 523, "B<tspan baseline-shift=\"sub\" font-size=\"13\">k,t</tspan>", "mathSmall", "middle"),
        matrix_glyph(280, 547, cell=17, cols=4, rows=3),
        svg_text(325, 650, "&#215;", "math", "middle"),
        rect(246, 676, 158, 150, "boxArgument", rx=8),
        svg_text(325, 718, "topology", "tiny", "middle"),
        mini_network(286, 742, "observed", scale=0.56, labels=False, frame=False),
        edge(190, 288, 242, 288, "edge"),
        edge(190, 528, 242, 528, "edge"),
        edge(190, 763, 242, 763, "edgeMuted"),
        edge(438, 528, 452, 528, "edge"),
        rect(456, 398, 134, 206, "box", rx=8),
        svg_text(523, 454, "M<tspan baseline-shift=\"sub\" font-size=\"12\">k,t</tspan>(W<tspan baseline-shift=\"sub\" font-size=\"12\">t-1</tspan>)", "mathSmall", "middle"),
        svg_text(523, 508, "=", "mathSmall", "middle"),
        svg_text(523, 554, "A<tspan baseline-shift=\"sub\" font-size=\"11\">k,t</tspan> +", "mathSmall", "middle"),
        svg_text(523, 594, "B<tspan baseline-shift=\"sub\" font-size=\"11\">k,t</tspan>W<tspan baseline-shift=\"sub\" font-size=\"11\">t-1</tspan>", "mathSmall", "middle"),
    ]

    # Panel b: matched readouts from one fitted path.
    parts += [
        svg_text(650, 66, "b", "panel"),
        svg_text(690, 63, "Same fitted path, three readouts", "labelBold"),
    ]
    rows = [
        (
            150,
            "observed topology",
            "M<tspan baseline-shift=\"sub\" font-size=\"12\">k,t</tspan>(W<tspan baseline-shift=\"sub\" font-size=\"12\">t-1</tspan>)",
            "observed response",
            "observed",
            "box",
            "edge",
            "trace",
        ),
        (
            418,
            "zero network mediation",
            "M<tspan baseline-shift=\"sub\" font-size=\"12\">k,t</tspan>(<tspan font-family=\"Arial, Helvetica, sans-serif\" font-style=\"normal\">0</tspan>)",
            "direct-only response",
            "direct",
            "boxMuted",
            "edgeMuted",
            "traceMuted",
        ),
        (
            686,
            "pre-period topology",
            "M<tspan baseline-shift=\"sub\" font-size=\"12\">k,t</tspan>(W<tspan baseline-shift=\"sub\" font-size=\"12\">pre</tspan>)",
            "frozen response",
            "frozen",
            "boxDash",
            "edgeDash",
            "traceDash",
        ),
    ]
    for idx, (y, label, formula, readout, mode, box_cls, edge_cls, trace_cls) in enumerate(rows):
        if idx:
            parts.append(edge(642, y - 58, 1097, y - 58, "separator"))
        parts += [
            svg_text(666, y, label, "small"),
            mini_network(696, y + 63, mode, scale=0.95, labels=False, frame=True),
            edge(850, y + 122, 874, y + 122, edge_cls),
            response_card(878, y + 43, 210, 150, formula, readout, box_cls, trace_cls),
        ]

    # Panel c: unrestricted factorization boundary and diagonal exception.
    parts += [
        svg_text(1168, 66, "c", "panel"),
        svg_text(1208, 63, "Query endpoint gate", "labelBold"),
        svg_text(1330, 162, "stored at fitted topology", "smallBold", "middle"),
        svg_text(1330, 204, "D = A + BW<tspan baseline-shift=\"sub\" font-size=\"12\">0</tspan>", "mathSmall", "middle"),
        rect(1260, 236, 142, 126, "band"),
        matrix_glyph(1282, 258, cell=20, cols=4, rows=3),
        edge(1330, 362, 1330, 420, "edge"),
        rect(1218, 420, 224, 142, "box", rx=8),
        svg_text(1330, 470, "collapsed fitted object", "smallBold", "middle"),
        svg_text(1330, 518, "D", "mathCard", "middle"),
        edge(1330, 562, 1330, 634, "edgeMuted"),
        f'<line class="blockLine" x1="1302" y1="648" x2="1358" y2="648"/>',
        f'<line class="blockedCross" x1="1318" y1="628" x2="1342" y2="652"/>',
        f'<line class="blockedCross" x1="1342" y1="628" x2="1318" y2="652"/>',
        rect(1208, 694, 244, 112, "boxMuted", rx=8),
        svg_text(1330, 726, "unrestricted blocks", "blocked", "middle"),
        svg_text(1330, 754, "W<tspan baseline-shift=\"sub\" font-size=\"11\">1</tspan> query not determined", "blocked", "middle"),
        svg_text(1330, 786, "OUTSIDE TARGET", "blocked", "middle"),
        svg_text(1330, 934, "diagonal blocks: verified inverse", "micro", "middle"),
        svg_text(1330, 960, "endpoint defined only under conditions", "micro", "middle"),
        mini_network(1279, 826, "observed", scale=0.77, labels=False, frame=True),
        "</svg>",
    ]
    return "\n".join(parts)


def main() -> None:
    OUT_BASENAME.parent.mkdir(parents=True, exist_ok=True)
    OUT_BASENAME.with_suffix(".svg").write_text(build_svg(), encoding="utf8")


if __name__ == "__main__":
    main()
