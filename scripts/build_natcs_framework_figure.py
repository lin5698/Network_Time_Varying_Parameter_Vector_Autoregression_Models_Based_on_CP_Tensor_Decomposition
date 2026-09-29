from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT_BASENAME = ROOT / "output" / "natcs_assets" / "figure1_natcs_framework"

WARM = "#C85A3A"
WARM_DARK = "#9F3F28"
WARM_LIGHT = "#F7E8E3"
COOL = "#367C8D"
COOL_LIGHT = "#E5F0F2"
INK = "#202428"
MID = "#687078"
LINE = "#AEB4B8"
PALE = "#F3F4F4"
WHITE = "#FFFFFF"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.linewidth": 0.6,
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def add_text(
    ax: plt.Axes,
    x: float,
    y: float,
    label: str,
    *,
    size: float = 7,
    weight: str = "normal",
    color: str = INK,
    ha: str = "left",
    va: str = "center",
    style: str = "normal",
    zorder: int = 6,
) -> None:
    ax.text(
        x,
        y,
        label,
        fontsize=size,
        fontweight=weight,
        color=color,
        ha=ha,
        va=va,
        fontstyle=style,
        linespacing=1.15,
        zorder=zorder,
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    facecolor: str = WHITE,
    edgecolor: str = LINE,
    linewidth: float = 0.8,
    radius: float = 0.012,
    linestyle: str = "solid",
    zorder: int = 1,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.004,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = INK,
    linewidth: float = 1.1,
    mutation_scale: float = 8,
    connectionstyle: str = "arc3",
    linestyle: str = "solid",
    zorder: int = 4,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=linewidth,
            color=color,
            linestyle=linestyle,
            connectionstyle=connectionstyle,
            shrinkA=0,
            shrinkB=0,
            zorder=zorder,
        )
    )


def draw_network(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    variant: int = 0,
    edgecolor: str = COOL,
    nodecolor: str = WHITE,
    alpha: float = 1.0,
    linewidth: float = 0.8,
) -> None:
    points = {
        0: (0.06, 0.45),
        1: (0.31, 0.83),
        2: (0.68, 0.72),
        3: (0.42, 0.12),
        4: (0.92, 0.29),
    }
    edge_sets = [
        [(0, 1), (0, 3), (1, 2), (1, 3), (2, 4), (3, 4)],
        [(0, 1), (0, 3), (1, 3), (2, 3), (2, 4), (3, 4)],
        [(0, 2), (0, 3), (1, 2), (1, 3), (2, 4), (3, 4)],
    ]
    positions = {
        key: (x + px * width, y + py * height) for key, (px, py) in points.items()
    }
    for source, target in edge_sets[variant % len(edge_sets)]:
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        ax.plot(
            [x0, x1],
            [y0, y1],
            color=edgecolor,
            linewidth=linewidth,
            alpha=alpha,
            solid_capstyle="round",
            zorder=2,
        )
    radius = min(width, height) * 0.075
    for px, py in positions.values():
        ax.add_patch(
            Circle(
                (px, py),
                radius,
                facecolor=nodecolor,
                edgecolor=edgecolor,
                linewidth=linewidth,
                alpha=alpha,
                zorder=3,
            )
        )


def draw_matrix(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    color: str,
    diagonal: bool = False,
    alpha: float = 1.0,
) -> None:
    values = (
        ((0.90, 0.10, 0.05), (0.10, 0.72, 0.08), (0.05, 0.08, 0.56))
        if diagonal
        else ((0.18, 0.82, 0.34), (0.64, 0.12, 0.76), (0.38, 0.58, 0.20))
    )
    rows = len(values)
    cols = len(values[0])
    cell_w = width / cols
    cell_h = height / rows
    rgb = mpl.colors.to_rgb(color)
    for row, row_values in enumerate(values):
        for col, value in enumerate(row_values):
            blend = tuple(1 - (1 - channel) * value for channel in rgb)
            ax.add_patch(
                Rectangle(
                    (x + col * cell_w, y + (rows - 1 - row) * cell_h),
                    cell_w,
                    cell_h,
                    facecolor=blend,
                    edgecolor=WHITE,
                    linewidth=0.55,
                    alpha=alpha,
                    zorder=3,
                )
            )
    ax.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor="none",
            edgecolor=color,
            linewidth=0.7,
            alpha=alpha,
            zorder=4,
        )
    )


def draw_trace(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    color: str,
    variant: int,
    linewidth: float = 1.2,
) -> None:
    profiles = [
        (0.10, 0.82, 0.34, 0.68, 0.43, 0.57, 0.48),
        (0.12, 0.68, 0.31, 0.52, 0.38, 0.45, 0.40),
        (0.08, 0.76, 0.25, 0.60, 0.34, 0.51, 0.42),
    ]
    profile = profiles[variant % len(profiles)]
    xs = [x + width * index / (len(profile) - 1) for index in range(len(profile))]
    ys = [y + height * value for value in profile]
    ax.plot(xs, ys, color=color, linewidth=linewidth, solid_capstyle="round", zorder=5)
    ax.plot([x, x + width], [y + height * 0.40] * 2, color=LINE, linewidth=0.45, zorder=2)


def draw_panel_a(ax: plt.Axes) -> None:
    add_text(ax, 0.018, 0.963, "a", size=8.5, weight="bold")
    add_text(
        ax,
        0.047,
        0.963,
        "A learned network operator that remains callable",
        size=9,
        weight="bold",
    )

    add_text(ax, 0.070, 0.868, "observed evolving system", size=7.3, weight="bold")
    history_x = (0.055, 0.124, 0.193)
    for index, x in enumerate(history_x):
        draw_network(ax, x, 0.690, 0.056, 0.105, variant=index, edgecolor=COOL)
        time_label = "t" if index == 2 else f"t - {2 - index}"
        add_text(ax, x + 0.028, 0.668, time_label, size=5.7, color=MID, ha="center")
    ax.plot([0.062, 0.242], [0.640, 0.640], color=LINE, linewidth=0.65, zorder=2)
    add_text(ax, 0.152, 0.610, "responses and weighted topologies", size=6.2, color=MID, ha="center")

    arrow(ax, (0.255, 0.750), (0.306, 0.750), color=INK, linewidth=1.0)
    add_text(ax, 0.281, 0.779, "fit once", size=5.8, color=MID, ha="center")

    rounded_box(
        ax,
        0.310,
        0.575,
        0.292,
        0.290,
        facecolor=WHITE,
        edgecolor=WARM,
        linewidth=1.35,
        radius=0.014,
    )
    ax.add_patch(
        Rectangle(
            (0.310, 0.816),
            0.292,
            0.049,
            facecolor=WARM,
            edgecolor=WARM,
            linewidth=0,
            zorder=2,
        )
    )
    add_text(ax, 0.456, 0.841, "query-certified learned object", size=7.2, weight="bold", color=WHITE, ha="center")

    rounded_box(ax, 0.335, 0.676, 0.104, 0.102, facecolor=WARM_LIGHT, edgecolor=WARM, linewidth=0.85)
    rounded_box(ax, 0.473, 0.676, 0.104, 0.102, facecolor=WARM_LIGHT, edgecolor=WARM, linewidth=0.85)
    draw_matrix(ax, 0.347, 0.697, 0.032, 0.055, color=WARM, diagonal=True)
    draw_matrix(ax, 0.485, 0.697, 0.032, 0.055, color=WARM, diagonal=True)
    add_text(ax, 0.409, 0.733, "A", size=9, weight="bold", color=WARM_DARK, ha="center")
    add_text(ax, 0.409, 0.705, "direct", size=5.7, color=MID, ha="center")
    add_text(ax, 0.547, 0.733, "B", size=9, weight="bold", color=WARM_DARK, ha="center")
    add_text(ax, 0.547, 0.705, "network", size=5.7, color=MID, ha="center")
    add_text(ax, 0.456, 0.635, "separated coefficient path", size=6.4, weight="bold", ha="center")
    add_text(ax, 0.456, 0.605, "topology remains an evaluation argument", size=5.9, color=MID, ha="center")

    rounded_box(ax, 0.372, 0.463, 0.168, 0.075, facecolor=COOL_LIGHT, edgecolor=COOL, linewidth=0.9)
    draw_network(ax, 0.388, 0.477, 0.047, 0.047, variant=2, edgecolor=COOL, linewidth=0.65)
    add_text(ax, 0.452, 0.506, "supplied topology W*", size=6.6, weight="bold", color=COOL)
    add_text(ax, 0.452, 0.480, "at readout only", size=5.7, color=MID)
    arrow(ax, (0.456, 0.538), (0.456, 0.574), color=COOL, linewidth=1.05)

    arrow(ax, (0.604, 0.750), (0.649, 0.750), color=WARM, linewidth=1.25)
    add_text(ax, 0.625, 0.781, "call", size=5.8, color=WARM_DARK, ha="center")

    rounded_box(ax, 0.653, 0.575, 0.127, 0.290, facecolor=WHITE, edgecolor=INK, linewidth=0.85)
    add_text(ax, 0.7165, 0.827, "topology-indexed", size=6.3, weight="bold", ha="center")
    add_text(ax, 0.7165, 0.801, "response", size=6.3, weight="bold", ha="center")
    add_text(ax, 0.7165, 0.752, "M(W*) at (k, t)", size=7.7, weight="bold", color=WARM_DARK, ha="center", style="italic")
    add_text(ax, 0.7165, 0.721, "= A(k,t) + B(k,t) W*", size=6.2, color=INK, ha="center")
    draw_matrix(ax, 0.679, 0.641, 0.075, 0.060, color=WARM)
    draw_trace(ax, 0.674, 0.591, 0.085, 0.043, color=WARM, variant=0)
    add_text(ax, 0.7165, 0.557, "finite-horizon readout", size=5.8, color=MID, ha="center")


def draw_call_card(
    ax: plt.Axes,
    x: float,
    title: str,
    query: str,
    output: str,
    *,
    variant: int,
    topology: str,
) -> None:
    width = 0.222
    rounded_box(ax, x, 0.094, width, 0.206, facecolor=WHITE, edgecolor=LINE, linewidth=0.75)
    add_text(ax, x + width / 2, 0.270, title, size=6.6, weight="bold", ha="center")
    if topology == "zero":
        rounded_box(ax, x + 0.018, 0.181, 0.060, 0.057, facecolor=PALE, edgecolor=LINE, linewidth=0.6)
        add_text(ax, x + 0.048, 0.210, "0", size=9, weight="bold", color=MID, ha="center")
    else:
        draw_network(
            ax,
            x + 0.019,
            0.181,
            0.057,
            0.057,
            variant=variant,
            edgecolor=COOL if topology == "observed" else MID,
            linewidth=0.6,
        )
    add_text(ax, x + 0.089, 0.221, query, size=6.2, weight="bold", color=COOL if topology == "observed" else INK)
    add_text(ax, x + 0.089, 0.193, output, size=5.8, color=MID)
    draw_trace(ax, x + 0.025, 0.117, width - 0.050, 0.045, color=WARM, variant=variant)


def draw_panel_b(ax: plt.Axes) -> None:
    add_text(ax, 0.018, 0.385, "b", size=8.5, weight="bold")
    add_text(ax, 0.047, 0.385, "Three calls from the same fitted path", size=8.4, weight="bold")
    rounded_box(ax, 0.315, 0.337, 0.232, 0.039, facecolor=WARM_LIGHT, edgecolor="none", linewidth=0)
    add_text(ax, 0.431, 0.356, "same state  |  same shock  |  same horizon", size=5.9, color=WARM_DARK, ha="center")
    ax.plot([0.081, 0.720], [0.322, 0.322], color=WARM, linewidth=1.0, zorder=2)
    for center in (0.149, 0.387, 0.625):
        ax.plot([center, center], [0.322, 0.303], color=WARM, linewidth=1.0, zorder=2)

    draw_call_card(
        ax,
        0.038,
        "observed topology",
        "W* = W(t-1)",
        "observed response",
        variant=0,
        topology="observed",
    )
    draw_call_card(
        ax,
        0.276,
        "zero network mediation",
        "W* = 0",
        "direct-only response",
        variant=1,
        topology="zero",
    )
    draw_call_card(
        ax,
        0.514,
        "frozen topology",
        "W* = W(pre)",
        "matched frozen response",
        variant=2,
        topology="frozen",
    )
    add_text(ax, 0.387, 0.055, "topology changes at evaluation; the model is not refitted", size=6.2, color=MID, ha="center")


def draw_panel_c(ax: plt.Axes) -> None:
    rounded_box(ax, 0.812, 0.055, 0.170, 0.900, facecolor=PALE, edgecolor="#D8DCDE", linewidth=0.7)
    add_text(ax, 0.827, 0.919, "c", size=8.5, weight="bold")
    add_text(ax, 0.855, 0.919, "Qualification\nboundary", size=6.8, weight="bold")
    add_text(ax, 0.897, 0.861, "collapsed at W0", size=6.5, weight="bold", ha="center")
    rounded_box(ax, 0.842, 0.749, 0.110, 0.079, facecolor=WHITE, edgecolor=LINE, linewidth=0.7)
    add_text(ax, 0.897, 0.789, "D = A + B W0", size=6.8, weight="bold", ha="center", style="italic")
    add_text(ax, 0.897, 0.718, "retains a total map", size=5.9, color=MID, ha="center")

    ax.plot([0.897, 0.897], [0.684, 0.625], color=LINE, linewidth=0.9, zorder=2)
    rounded_box(ax, 0.842, 0.538, 0.110, 0.082, facecolor=WHITE, edgecolor=LINE, linewidth=0.7, linestyle="dashed")
    add_text(ax, 0.897, 0.588, "query W1", size=6.7, weight="bold", ha="center")
    add_text(ax, 0.897, 0.562, "W1 differs from W0", size=5.5, color=MID, ha="center")

    ax.plot([0.897, 0.897], [0.536, 0.476], color=LINE, linewidth=0.9, zorder=2)
    ax.plot([0.884, 0.910], [0.501, 0.501], color=MID, linewidth=1.3, zorder=4)
    add_text(ax, 0.897, 0.436, "no declared inverse", size=6.2, weight="bold", color=MID, ha="center")
    add_text(ax, 0.897, 0.397, "topology-substitution", size=5.9, color=MID, ha="center")
    add_text(ax, 0.897, 0.369, "response is not callable", size=5.9, color=MID, ha="center")

    rounded_box(ax, 0.839, 0.274, 0.116, 0.060, facecolor="#E7E9EA", edgecolor="none", linewidth=0)
    add_text(ax, 0.897, 0.304, "OUTSIDE TARGET", size=6.1, weight="bold", color=MID, ha="center")
    add_text(ax, 0.897, 0.227, "not a zero response", size=5.7, color=MID, ha="center")
    add_text(ax, 0.897, 0.198, "not an error score", size=5.7, color=MID, ha="center")
    ax.plot([0.842, 0.952], [0.159, 0.159], color="#D4D7D9", linewidth=0.6, zorder=2)
    add_text(ax, 0.897, 0.122, "A verified structured inverse", size=5.6, color=COOL, ha="center")
    add_text(ax, 0.897, 0.096, "defines a different contract", size=5.6, color=COOL, ha="center")


def build_figure() -> plt.Figure:
    width_inches = 183 / 25.4
    fig = plt.figure(figsize=(width_inches, 5.15), facecolor=WHITE)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("auto")
    ax.axis("off")

    ax.plot([0.018, 0.783], [0.423, 0.423], color="#D9DCDE", linewidth=0.65, zorder=1)
    draw_panel_a(ax)
    draw_panel_b(ax)
    draw_panel_c(ax)
    return fig


def main() -> None:
    OUT_BASENAME.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".svg", ".pdf", ".png"):
        output_path = OUT_BASENAME.with_suffix(suffix)
        if output_path.exists():
            output_path.unlink()
    fig = build_figure()
    fig.savefig(OUT_BASENAME.with_suffix(".svg"), format="svg")
    fig.savefig(OUT_BASENAME.with_suffix(".pdf"), format="pdf")
    fig.savefig(OUT_BASENAME.with_suffix(".png"), format="png", dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    main()
