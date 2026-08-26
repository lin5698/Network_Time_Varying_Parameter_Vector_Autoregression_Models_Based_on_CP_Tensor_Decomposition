from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FixedLocator, FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "output" / "natcs_evidence" / "table1_simulation_benchmark.csv"
RAW_SUMMARY_PATH = ROOT / "output" / "natcs_benchmarks" / "benchmark_summary.csv"
OUT_BASENAME = ROOT / "output" / "natcs_assets" / "figure3_natcs_supported_regime"

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

SCENARIOS = {
    "N=15": "Scale baseline (T=160, N=15)",
    "N=30": "Scale baseline (T=200, N=30)",
}
METHODS = ("CP-network", "Local rolling")

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


@dataclass(frozen=True)
class Interval:
    median: float
    q25: float
    q75: float


def parse_interval(value: str) -> Interval:
    match = re.fullmatch(
        r"\s*([-+0-9.eE]+)\s*\[\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*\]\s*",
        value,
    )
    if not match:
        raise ValueError(f"Expected a median [q25, q75] interval, received {value!r}")
    median, q25, q75 = (float(item) for item in match.groups())
    if not all(math.isfinite(item) and item > 0 for item in (median, q25, q75)):
        raise ValueError(f"Figure 3 requires finite positive errors, received {value!r}")
    if not q25 <= median <= q75:
        raise ValueError(f"Interval ordering is invalid: {value!r}")
    return Interval(median=median, q25=q25, q75=q75)


def load_controlled_rows() -> dict[tuple[str, str], dict[str, Interval]]:
    with SUMMARY_PATH.open(newline="", encoding="utf8") as handle:
        rows = list(csv.DictReader(handle))
    selected: dict[tuple[str, str], dict[str, Interval]] = {}
    for display_scenario, source_scenario in SCENARIOS.items():
        for method in METHODS:
            matches = [row for row in rows if row["Scenario"] == source_scenario and row["Method"] == method]
            if len(matches) != 1:
                raise ValueError(f"Expected one released row for {source_scenario!r} and {method!r}")
            row = matches[0]
            selected[(display_scenario, method)] = {
                "operator": parse_interval(row["Effective-operator error"]),
                "response": parse_interval(row["GIRF error"]),
            }
    return selected


def load_raw_controlled_values() -> dict[tuple[str, str, str], float]:
    with RAW_SUMMARY_PATH.open(newline="", encoding="utf8") as handle:
        rows = list(csv.DictReader(handle))
    source_methods = {"CP-network": "cp_network", "Local rolling": "local_network"}
    source_scenarios = {"N=15": "scale_n15", "N=30": "scale_n30"}
    raw_values: dict[tuple[str, str, str], float] = {}
    for scenario, source_scenario in source_scenarios.items():
        for method, source_method in source_methods.items():
            matches = [row for row in rows if row["scenario"] == source_scenario and row["method"] == source_method]
            if len(matches) != 1:
                raise ValueError(f"Replication record missing for {scenario} and {method}")
            replications = int(float(matches[0]["replications"]))
            if replications != 20:
                raise ValueError(f"Figure 3 requires 20 replications for {scenario} and {method}; found {replications}")
            raw_values[(scenario, method, "operator")] = float(matches[0]["coef_error_median"])
            raw_values[(scenario, method, "response")] = float(matches[0]["girf_error_median"])
    if not all(math.isfinite(value) and value > 0 for value in raw_values.values()):
        raise ValueError("Figure 3 raw medians must be finite and positive")
    return raw_values


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
    transform=None,
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
        linespacing=1.15,
        transform=transform or ax.transAxes,
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
        transform=ax.transAxes,
        clip_on=False,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def reduction_pct(raw_values: dict[tuple[str, str, str], float], scenario: str, metric: str) -> float:
    cp = raw_values[(scenario, "CP-network", metric)]
    local = raw_values[(scenario, "Local rolling", metric)]
    return 100.0 * (local - cp) / local


def style_metric_axis(ax: plt.Axes, *, xlim: tuple[float, float], ticks: tuple[float, ...], xlabel: str) -> None:
    ax.set_xscale("log")
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.55, 1.55)
    ax.set_yticks([1, 0], ["N=15", "N=30"])
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.minorticks_off()
    ax.grid(axis="x", color="#E4E6E7", linewidth=0.55)
    ax.tick_params(axis="both", labelsize=6, length=2.5, width=0.55, color=MID)
    ax.set_xlabel(xlabel, fontsize=6.1, color=MID, labelpad=4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(axis="y", length=0, pad=5)


def draw_metric_panel(
    ax: plt.Axes,
    rows: dict[tuple[str, str], dict[str, Interval]],
    raw_values: dict[tuple[str, str, str], float],
    *,
    metric: str,
    xlim: tuple[float, float],
    ticks: tuple[float, ...],
    xlabel: str,
) -> None:
    style_metric_axis(ax, xlim=xlim, ticks=ticks, xlabel=xlabel)
    for y, scenario in zip((1, 0), SCENARIOS):
        cp = rows[(scenario, "CP-network")][metric]
        local = rows[(scenario, "Local rolling")][metric]
        ax.plot([cp.median, local.median], [y, y], color=LINE, linewidth=1.0, zorder=2)
        for interval, color, marker in ((local, INK, "s"), (cp, WARM, "o")):
            ax.errorbar(
                interval.median,
                y,
                xerr=[[interval.median - interval.q25], [interval.q75 - interval.median]],
                fmt=marker,
                markersize=4.8,
                color=color,
                markerfacecolor=color,
                markeredgecolor=WHITE,
                markeredgewidth=0.45,
                ecolor=color,
                elinewidth=1.0,
                capsize=2.1,
                capthick=0.8,
                zorder=4,
            )
        center = math.sqrt(cp.median * local.median)
        ax.text(
            center,
            y + 0.19,
            f"-{reduction_pct(raw_values, scenario, metric):.1f}%",
            fontsize=6.0,
            fontweight="bold",
            color=WARM_DARK,
            ha="center",
            va="bottom",
            zorder=5,
        )


def draw_endpoint_panel(ax: plt.Axes) -> None:
    ax.axis("off")
    add_text(ax, 0.00, 0.94, "c", size=8.5, weight="bold")
    add_text(ax, 0.030, 0.94, "Target-matched evidence contract", size=8.2, weight="bold")
    rounded_box(ax, 0.030, 0.16, 0.940, 0.610, facecolor=PALE, edgecolor="#D8DCDE", linewidth=0.7)
    add_text(ax, 0.065, 0.665, "CP reconstruction", size=6.2, weight="bold", color=WARM_DARK)
    add_text(ax, 0.065, 0.405, "unrestricted local", size=6.2, weight="bold", color=INK)
    for y, color in ((0.665, WARM), (0.405, INK)):
        ax.scatter([0.305], [y], s=24, color=color, edgecolors=WHITE, linewidths=0.5, transform=ax.transAxes, zorder=5)
        ax.plot([0.320, 0.390], [y, y], color=LINE, linewidth=0.8, transform=ax.transAxes, zorder=2)
        rounded_box(ax, 0.405, y - 0.075, 0.300, 0.150, facecolor=WHITE, edgecolor=LINE, linewidth=0.65)
        add_text(ax, 0.555, y + 0.027, "M(W) + finite-horizon response", size=5.4, weight="bold", ha="center")
        add_text(ax, 0.555, y - 0.035, "same declared endpoint", size=5.2, color=MID, ha="center")
        ax.plot([0.720, 0.775], [y, y], color=LINE, linewidth=0.8, transform=ax.transAxes, zorder=2)
        add_text(ax, 0.805, y + 0.025, "N = 15, 30", size=5.6, weight="bold")
        add_text(ax, 0.805, y - 0.035, "20 replications per scale", size=5.2, color=MID)
    add_text(ax, 0.500, 0.075, "Recovery is compared only where endpoint and replication contracts match", size=5.7, weight="bold", color=MID, ha="center")


def build_figure() -> plt.Figure:
    rows = load_controlled_rows()
    raw_values = load_raw_controlled_values()

    width_inches = 183 / 25.4
    fig = plt.figure(figsize=(width_inches, 4.35), facecolor=WHITE)
    canvas = fig.add_axes((0, 0, 1, 1))
    canvas.set_xlim(0, 1)
    canvas.set_ylim(0, 1)
    canvas.axis("off")

    add_text(canvas, 0.018, 0.965, "a", size=8.5, weight="bold")
    add_text(canvas, 0.047, 0.965, "Controlled operator recovery", size=8.8, weight="bold")
    add_text(canvas, 0.047, 0.925, "Separated reconstruction versus unrestricted local rolling", size=5.9, color=MID)
    add_text(canvas, 0.592, 0.965, "b", size=8.5, weight="bold")
    add_text(canvas, 0.622, 0.965, "Matched response recovery", size=8.3, weight="bold")
    add_text(canvas, 0.622, 0.925, "Same scales, endpoint and replications", size=5.9, color=MID)

    ax_a = fig.add_axes((0.075, 0.485, 0.445, 0.345))
    draw_metric_panel(
        ax_a,
        rows,
        raw_values,
        metric="operator",
        xlim=(20, 2000),
        ticks=(30, 100, 300, 1000),
        xlabel="effective-operator error (log scale; lower is better)",
    )
    ax_b = fig.add_axes((0.650, 0.485, 0.305, 0.345))
    draw_metric_panel(
        ax_b,
        rows,
        raw_values,
        metric="response",
        xlim=(0.035, 0.60),
        ticks=(0.05, 0.10, 0.20, 0.50),
        xlabel="Response error (log scale; lower is better)",
    )

    canvas.scatter([0.245], [0.875], s=22, color=WARM, edgecolors=WHITE, linewidths=0.45, zorder=6)
    add_text(canvas, 0.258, 0.875, "CP reconstruction", size=5.7, color=WARM_DARK)
    canvas.scatter([0.390], [0.875], s=22, marker="s", color=INK, edgecolors=WHITE, linewidths=0.45, zorder=6)
    add_text(canvas, 0.403, 0.875, "unrestricted local", size=5.7, color=INK)

    canvas.plot([0.018, 0.982], [0.405, 0.405], color="#D9DCDE", linewidth=0.65, zorder=1)
    endpoint_ax = fig.add_axes((0.018, 0.035, 0.964, 0.330))
    draw_endpoint_panel(endpoint_ax)
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
