from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT_BASENAME = ROOT / "output" / "natcs_assets" / "figure2_natcs_query_certificate"

WARM = "#C85A3A"
WARM_DARK = "#9F3F28"
WARM_LIGHT = "#F7E8E3"
COOL = "#367C8D"
COOL_DARK = "#245E6C"
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
    linewidth: float = 1.0,
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


def draw_matrix(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    color: str,
    diagonal: bool = False,
    zero_diagonal: bool = False,
    alpha: float = 1.0,
) -> None:
    if diagonal:
        values = ((0.88, 0.0, 0.0), (0.0, 0.68, 0.0), (0.0, 0.0, 0.48))
    elif zero_diagonal:
        values = ((0.0, 0.76, 0.32), (0.56, 0.0, 0.70), (0.28, 0.61, 0.0))
    else:
        values = ((0.18, 0.82, 0.34), (0.64, 0.12, 0.76), (0.38, 0.58, 0.20))
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
                    linewidth=0.45,
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


def draw_panel_a(ax: plt.Axes) -> None:
    add_text(ax, 0.018, 0.965, "a", size=8.5, weight="bold")
    add_text(ax, 0.047, 0.965, "Finite-basis queries admit an exact certificate", size=9, weight="bold")
    add_text(
        ax,
        0.047,
        0.924,
        "The retained representation must determine the requested operator on every parameter pair it identifies.",
        size=6.2,
        color=MID,
    )

    rounded_box(ax, 0.060, 0.716, 0.130, 0.110, facecolor=WHITE, edgecolor=INK, linewidth=0.85)
    add_text(ax, 0.125, 0.789, "parameter pair", size=5.8, color=MID, ha="center")
    add_text(ax, 0.125, 0.750, "theta = (A, B)", size=8.5, weight="bold", ha="center", style="italic")

    rounded_box(ax, 0.300, 0.716, 0.146, 0.110, facecolor=PALE, edgecolor=LINE, linewidth=0.85)
    add_text(ax, 0.373, 0.789, "retained object", size=5.8, color=MID, ha="center")
    add_text(ax, 0.373, 0.750, "T(W0; theta)", size=8.5, weight="bold", ha="center", style="italic")

    rounded_box(ax, 0.548, 0.716, 0.145, 0.110, facecolor=WARM_LIGHT, edgecolor=WARM, linewidth=1.15)
    add_text(ax, 0.6205, 0.789, "requested operator", size=5.8, color=WARM_DARK, ha="center")
    add_text(ax, 0.6205, 0.750, "Q(W1; theta)", size=8.5, weight="bold", color=WARM_DARK, ha="center", style="italic")

    arrow(ax, (0.192, 0.771), (0.296, 0.771), color=INK, linewidth=1.0)
    add_text(ax, 0.244, 0.797, "T(W0)", size=6.1, color=MID, ha="center", style="italic")
    arrow(ax, (0.448, 0.771), (0.544, 0.771), color=WARM, linewidth=1.35)
    add_text(ax, 0.496, 0.797, "h(W1)", size=6.1, color=WARM_DARK, ha="center", style="italic")
    arrow(
        ax,
        (0.151, 0.829),
        (0.584, 0.829),
        color=LINE,
        linewidth=0.8,
        connectionstyle="arc3,rad=-0.20",
    )
    add_text(ax, 0.373, 0.882, "Q(W1)", size=6.1, color=MID, ha="center", style="italic")

    rounded_box(ax, 0.157, 0.612, 0.438, 0.073, facecolor=WARM, edgecolor=WARM, linewidth=0)
    add_text(
        ax,
        0.376,
        0.657,
        r"CALLABLE iff  $\ker T^\Phi(W_0) \subseteq \ker Q^\Phi(W_1)$",
        size=7.2,
        weight="bold",
        color=WHITE,
        ha="center",
    )
    add_text(ax, 0.376, 0.629, "equivalently: Q(W1) = h(W1) o T(W0)", size=5.8, color=WHITE, ha="center")
    add_text(
        ax,
        0.376,
        0.587,
        r"one-hop  $\Phi=(I,W)$    |    two-hop  $\Phi=(I,W,W^2)$",
        size=6.1,
        color=MID,
        ha="center",
    )


def draw_panel_b(ax: plt.Axes) -> None:
    ax.plot([0.724, 0.724], [0.570, 0.957], color="#D9DCDE", linewidth=0.65, zorder=1)
    add_text(ax, 0.747, 0.965, "b", size=8.5, weight="bold")
    add_text(ax, 0.777, 0.965, "Exact unrestricted boundary", size=8.2, weight="bold")
    add_text(ax, 0.747, 0.919, "For W1 != W0, the same D = 0\nhas two queried values.", size=5.6, color=MID, va="top")

    worlds = [
        (0.809, "world 1", "(A, B) = (0, 0)", "0"),
        (0.692, "world 2", "(A, B) = (-W0, I)", "W1 - W0"),
    ]
    for y, title, pair, query in worlds:
        rounded_box(ax, 0.748, y, 0.116, 0.073, facecolor=WHITE, edgecolor=LINE, linewidth=0.7)
        add_text(ax, 0.806, y + 0.050, title, size=5.3, color=MID, ha="center")
        add_text(ax, 0.806, y + 0.023, pair, size=5.7, weight="bold", ha="center", style="italic")
        arrow(ax, (0.867, y + 0.036), (0.888, y + 0.036), color=LINE, linewidth=0.75, mutation_scale=6)
        rounded_box(ax, 0.892, y, 0.078, 0.073, facecolor=PALE, edgecolor=LINE, linewidth=0.7)
        add_text(ax, 0.931, y + 0.050, "D at W0", size=5.0, color=MID, ha="center")
        add_text(ax, 0.931, y + 0.022, "0", size=7.4, weight="bold", ha="center")
        add_text(ax, 0.931, y - 0.018, f"Q at W1 = {query}", size=5.15, color=WARM_DARK, ha="center", style="italic")

    rounded_box(ax, 0.772, 0.598, 0.176, 0.052, facecolor="#E7E9EA", edgecolor="none", linewidth=0)
    add_text(ax, 0.860, 0.624, "NOT DETERMINED: no single h(W1)", size=5.7, weight="bold", color=MID, ha="center")
    add_text(ax, 0.860, 0.579, "Unrestricted blocks factor through the collapse\nif and only if W1 = W0.", size=5.25, color=MID, ha="center", va="center")


def draw_panel_c(ax: plt.Axes) -> None:
    ax.plot([0.018, 0.982], [0.548, 0.548], color="#D9DCDE", linewidth=0.65, zorder=1)
    add_text(ax, 0.018, 0.518, "c", size=8.5, weight="bold")
    add_text(ax, 0.047, 0.518, "Declared structure supplies a constructive inverse", size=8.6, weight="bold")
    add_text(ax, 0.047, 0.481, "Diagonal A and B; zero diagonal in W0; each queried zero row is also zero in W1.", size=6.0, color=MID)

    rounded_box(ax, 0.052, 0.334, 0.184, 0.111, facecolor=WHITE, edgecolor=LINE, linewidth=0.8)
    draw_matrix(ax, 0.069, 0.352, 0.052, 0.068, color=INK)
    draw_matrix(ax, 0.143, 0.352, 0.052, 0.068, color=COOL, zero_diagonal=True)
    add_text(ax, 0.095, 0.430, "D", size=6.1, weight="bold", ha="center", style="italic")
    add_text(ax, 0.169, 0.430, "W0", size=6.1, weight="bold", color=COOL_DARK, ha="center", style="italic")
    add_text(ax, 0.144, 0.343, "retained together", size=5.1, color=MID, ha="center")

    arrow(ax, (0.241, 0.390), (0.285, 0.390), color=COOL, linewidth=1.15)
    rounded_box(ax, 0.289, 0.319, 0.326, 0.142, facecolor=COOL_LIGHT, edgecolor=COOL, linewidth=1.0)
    add_text(ax, 0.452, 0.435, "verified rowwise inverse", size=6.4, weight="bold", color=COOL_DARK, ha="center")
    add_text(ax, 0.452, 0.394, "a(i) = D(i,i)", size=8.0, weight="bold", color=COOL_DARK, ha="center", style="italic")
    add_text(ax, 0.452, 0.355, "b(i) = <D(i,-i), w0(i,-i)> / ||w0(i,-i)||^2", size=6.5, color=COOL_DARK, ha="center", style="italic")
    add_text(ax, 0.452, 0.332, "for each nonzero exposure row", size=5.3, color=MID, ha="center")

    arrow(ax, (0.620, 0.390), (0.664, 0.390), color=COOL, linewidth=1.15)
    rounded_box(ax, 0.668, 0.334, 0.109, 0.111, facecolor=WHITE, edgecolor=COOL, linewidth=0.85)
    draw_matrix(ax, 0.683, 0.354, 0.031, 0.062, color=COOL, diagonal=True)
    draw_matrix(ax, 0.729, 0.354, 0.031, 0.062, color=COOL, diagonal=True)
    add_text(ax, 0.6985, 0.430, "A", size=6.0, weight="bold", color=COOL_DARK, ha="center")
    add_text(ax, 0.7445, 0.430, "B", size=6.0, weight="bold", color=COOL_DARK, ha="center")
    add_text(ax, 0.7225, 0.347, "recovered blocks", size=5.1, color=MID, ha="center")

    add_text(ax, 0.816, 0.423, "supplied W1", size=5.6, color=MID, ha="center")
    arrow(ax, (0.784, 0.390), (0.849, 0.390), color=WARM, linewidth=1.2)
    rounded_box(ax, 0.853, 0.334, 0.120, 0.111, facecolor=WARM_LIGHT, edgecolor=WARM, linewidth=1.1)
    add_text(ax, 0.913, 0.418, "callable query", size=5.7, color=WARM_DARK, ha="center")
    add_text(ax, 0.913, 0.381, "A + B W1", size=7.7, weight="bold", color=WARM_DARK, ha="center", style="italic")
    add_text(ax, 0.913, 0.350, "for any supplied W1", size=5.3, color=MID, ha="center")
    add_text(ax, 0.512, 0.285, "The structured exception is a positive certificate, not a relaxation of the unrestricted theorem.", size=5.8, color=MID, ha="center")


def endpoint_marker(ax: plt.Axes, x: float, y: float, *, available: bool, color: str) -> None:
    if available:
        ax.scatter([x], [y], s=18, color=color, edgecolors=WHITE, linewidths=0.4, zorder=6)
    else:
        ax.plot([x - 0.010, x + 0.010], [y, y], color=LINE, linewidth=1.5, solid_capstyle="round", zorder=6)


def draw_panel_d(ax: plt.Axes) -> None:
    ax.plot([0.018, 0.982], [0.257, 0.257], color="#D9DCDE", linewidth=0.65, zorder=1)
    add_text(ax, 0.018, 0.226, "d", size=8.5, weight="bold")
    add_text(ax, 0.047, 0.226, "Endpoint classification precedes error comparison", size=8.3, weight="bold")
    add_text(ax, 0.047, 0.190, "A dash denotes an unsupported readout, not zero error.", size=5.8, color=MID)

    endpoint_labels = ("total response", "network component", "frozen topology")
    endpoint_xs = (0.572, 0.717, 0.862)
    for x, label in zip(endpoint_xs, endpoint_labels):
        add_text(ax, x, 0.226, label, size=5.4, color=MID, ha="center")

    rows = [
        (0.166, "separated CP", (True, True, True), WARM),
        (0.126, "separated Tucker", (True, True, True), COOL),
        (0.086, "collapsed total map", (True, False, False), MID),
        (0.046, "low-rank no network", (True, False, False), MID),
    ]
    for y, method, availability, color in rows:
        add_text(ax, 0.372, y, method, size=5.9, weight="bold" if color in {WARM, COOL} else "normal", color=color, ha="right")
        ax.plot([0.401, 0.932], [y, y], color="#ECEEEF", linewidth=0.55, zorder=1)
        for x, available in zip(endpoint_xs, availability):
            endpoint_marker(ax, x, y, available=available, color=color)
    add_text(ax, 0.957, 0.166, "defined", size=5.2, color=WARM_DARK, ha="right")
    add_text(ax, 0.957, 0.086, "total only", size=5.2, color=MID, ha="right")


def build_figure() -> plt.Figure:
    width_inches = 183 / 25.4
    fig = plt.figure(figsize=(width_inches, 4.95), facecolor=WHITE)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("auto")
    ax.axis("off")

    draw_panel_a(ax)
    draw_panel_b(ax)
    draw_panel_c(ax)
    draw_panel_d(ax)
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
