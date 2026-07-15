from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp" / "matplotlib_cache"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp" / "xdg_cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 6.5,
    "axes.titlesize": 7.0,
    "axes.labelsize": 6.5,
    "axes.linewidth": 0.75,
    "xtick.labelsize": 5.8,
    "ytick.labelsize": 5.8,
    "legend.fontsize": 5.7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

BLACK = "#111111"
TEAL = "#2f8793"
BLUE = "#4d79a8"
RED = "#ca6f67"
GOLD = "#c59a46"
GREY = "#808080"
LIGHT_BLUE = "#d7e8ee"


def clean_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=2.5, width=0.65, color=BLACK)


def panel_label(ax, label: str):
    ax.text(-0.12, 1.09, label, transform=ax.transAxes, ha="left", va="top", fontweight="bold", fontsize=7.6)


def absolute_explicit_channel_share(direct, network):
    direct_abs = np.abs(direct).sum()
    network_abs = np.abs(network).sum()
    return network_abs / max(direct_abs + network_abs, 1e-12)


def draw_aggregate(ax, out_dir: Path):
    boot = pd.read_csv(out_dir / "aggregate_cp_bootstrap.csv", parse_dates=["date"])
    ax.plot(boot["date"], boot["g_net_p50"], color=BLACK, lw=1.15, label="Observed")
    ax.plot(boot["date"], boot["g_net_fixed_p50"], color=TEAL, lw=1.05, ls="--", label="Frozen")
    ax.fill_between(boot["date"], boot["g_net_p16"], boot["g_net_p84"], color=LIGHT_BLUE, alpha=0.22, linewidth=0)
    ax.set_title("Same-operator observed and frozen propagation", loc="left", pad=3)
    ax.set_ylabel(r"$G(t,H)$")
    ax.set_xlabel("Date")
    ax.legend(frameon=False, loc="upper left", ncol=2, handlelength=1.0, columnspacing=0.8)
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_difference(ax, out_dir: Path):
    boot = pd.read_csv(out_dir / "aggregate_cp_bootstrap.csv", parse_dates=["date"])
    ax.fill_between(boot["date"], boot["g_net_diff_p025"], boot["g_net_diff_p975"], color=LIGHT_BLUE, alpha=0.75, linewidth=0)
    ax.fill_between(boot["date"], boot["g_net_diff_p16"], boot["g_net_diff_p84"], color="#a9cbd5", alpha=0.6, linewidth=0)
    ax.plot(boot["date"], boot["g_net_diff_p50"], color=BLACK, lw=1.25)
    ax.axhline(0, color=BLACK, lw=0.65)
    ax.set_title("Fixed-path observed-minus-frozen propagation", loc="left", pad=3)
    ax.set_ylabel(r"$G(t,H;W_t)-G(t,H;W_{pre})$")
    ax.set_xlabel("Date")
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_girf(ax, out_dir: Path):
    points = json.loads((out_dir / "girf_cp_point.json").read_text())
    stats = []
    for date, values in points.items():
        total = np.asarray(values["total"], dtype=float)
        direct = np.asarray(values["direct"], dtype=float)
        network = np.asarray(values["network"], dtype=float)
        direct_abs = np.abs(direct).sum()
        network_abs = np.abs(network).sum()
        stats.append({
            "date": date[:4],
            "direct_abs": direct_abs,
            "network_abs": network_abs,
            "network_share": absolute_explicit_channel_share(direct, network),
        })
    x = np.arange(len(stats))
    direct_vals = np.array([s["direct_abs"] for s in stats])
    network_vals = np.array([s["network_abs"] for s in stats])
    ax.bar(x, direct_vals, color=RED, width=0.52, label="Direct")
    ax.bar(x, network_vals, bottom=direct_vals, color=BLUE, width=0.52, label="Network")
    totals = direct_vals + network_vals
    ymax = max(float(totals.max()) * 1.25, 0.04)
    label_pad = ymax * 0.025
    for i, s in enumerate(stats):
        total = totals[i]
        ax.text(
            i,
            total + label_pad,
            f"point share\n{s['network_share']:.2f}",
            ha="center",
            va="bottom",
            color=BLACK,
            fontsize=5.5,
            linespacing=0.92,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.35},
            clip_on=False,
        )
    ax.set_xticks(x)
    ax.set_xticklabels([s["date"] for s in stats])
    ax.set_ylabel("Absolute GIRF mass")
    ax.set_title("Direct and network response mass", loc="left", pad=3)
    ax.set_ylim(0, ymax)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 1.01), ncol=2, handlelength=0.9, columnspacing=0.8)
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_diagnostics(ax, out_dir: Path):
    corr = pd.read_csv(out_dir / "nyc_network_mechanism_correlations.csv")
    rows = corr[corr["target"] == "g_net"].copy()
    rows["abs_spearman"] = rows["spearman"].abs()
    labels = {
        "weight_turnover": "Weight turnover",
        "spectral_effective_rank_W": "Eff. rank",
        "top3_incoming_share": "Top-3 inflow",
        "incoming_gini": "Inflow inequality",
        "directional_asymmetry": "Asymmetry",
    }
    rows = rows[rows["metric"].isin(labels)].sort_values("spearman")
    y = np.arange(len(rows))
    colors = [BLUE if v < 0 else TEAL for v in rows["spearman"]]
    ax.barh(y, rows["spearman"], color=colors, height=0.56)
    ax.axvline(0, color=BLACK, lw=0.65)
    for yy, val in zip(y, rows["spearman"]):
        if val >= 0:
            ax.text(val + 0.025, yy, f"{val:.2f}", ha="left", va="center", fontsize=5.6, color=BLACK)
        else:
            ax.text(val + 0.045, yy, f"{val:.2f}", ha="left", va="center", fontsize=5.6, color="white")
    ax.set_yticks(y)
    ax.set_yticklabels([labels[m] for m in rows["metric"]])
    ax.set_xlabel(r"Descriptive Spearman with $G(t,H)$")
    ax.set_title("Level association only", loc="left", pad=3)
    ax.set_xlim(-0.85, 0.85)
    ax.grid(axis="x", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def main() -> int:
    out_dir = ROOT / "output" / "natcs_empirical_cp" / "nyc_taxi"
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    out_png = fig_dir / "fig_nyc_portability_summary.png"
    out_pdf = fig_dir / "fig_nyc_portability_summary.pdf"
    if os.environ.get("NATCS_REUSE_EXISTING_FIGURES") == "1" and out_png.exists() and out_pdf.exists():
        return 0

    fig = plt.figure(figsize=(7.35, 4.25))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.82, 1.0], hspace=0.72, wspace=0.5)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, :]),
    ]
    draw_aggregate(axes[0], out_dir)
    draw_difference(axes[1], out_dir)
    draw_girf(axes[2], out_dir)
    for label, ax in zip("abc", axes):
        panel_label(ax, label)
    fig.savefig(out_png, dpi=900, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
