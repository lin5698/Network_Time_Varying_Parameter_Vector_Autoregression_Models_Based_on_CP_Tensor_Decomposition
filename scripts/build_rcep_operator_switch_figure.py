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
    "font.size": 6.8,
    "axes.titlesize": 7.4,
    "axes.labelsize": 6.8,
    "axes.linewidth": 0.75,
    "xtick.labelsize": 6.0,
    "ytick.labelsize": 6.0,
    "legend.fontsize": 5.9,
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
LIGHT_TEAL = "#e4f0ef"


def load_json(path: Path):
    with open(path) as f:
        return json.load(f)


def clean_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=2.5, width=0.65, color=BLACK)


def absolute_explicit_channel_share(direct, network):
    direct_abs = np.abs(direct).sum()
    network_abs = np.abs(network).sum()
    return network_abs / max(direct_abs + network_abs, 1e-12)


def panel_label(ax, label: str):
    ax.text(-0.11, 1.09, label, transform=ax.transAxes, ha="left", va="top", fontweight="bold", fontsize=8.0)


def panel_label_d(ax, label: str):
    ax.text(-0.18, 1.13, label, transform=ax.transAxes, ha="left", va="top", fontweight="bold", fontsize=8.0)


def draw_topology_contrast(ax, out_dir: Path):
    metrics = pd.read_csv(out_dir / "aggregate_cp_metrics.csv", parse_dates=["date"])
    boot = pd.read_csv(out_dir / "aggregate_cp_bootstrap.csv", parse_dates=["date"])
    observed = metrics.loc[metrics["variant_key"] == "baseline_import", ["date", "g_net"]]
    frozen = metrics.loc[metrics["variant_key"] == "fixed_pre", ["date", "g_net"]]
    merged = observed.merge(frozen, on="date", suffixes=("_observed", "_frozen"))
    merged["diff"] = merged["g_net_observed"] - merged["g_net_frozen"]
    ax.fill_between(boot["date"], boot["g_net_diff_p025"], boot["g_net_diff_p975"], color=LIGHT_BLUE, alpha=0.85, linewidth=0)
    ax.fill_between(boot["date"], boot["g_net_diff_p16"], boot["g_net_diff_p84"], color="#a9cbd5", alpha=0.65, linewidth=0)
    ax.plot(merged["date"], merged["diff"], color=BLACK, lw=1.45)
    ax.axhline(0, color=BLACK, lw=0.7)
    entry = pd.Timestamp("2022-01-01")
    ax.axvline(entry, color=GREY, lw=0.75, ls="--")
    ax.annotate(
        "2022 Q1",
        xy=(entry, 1.0),
        xycoords=("data", "axes fraction"),
        xytext=(4, -2),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=5.8,
        color=GREY,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 0.6},
        annotation_clip=False,
    )
    ax.set_title("Fixed-path observed-minus-frozen propagation", loc="left", pad=3)
    ax.set_ylabel(r"$G(W_t)-G(W_{pre})$")
    ax.set_xlabel("Date")
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_coefficient_boundary(ax, out_dir: Path):
    conditional = pd.read_csv(ROOT / "output" / "natcs_evidence" / "table2b_rcep_attenuation_uncertainty.csv")
    full_path = pd.read_csv(ROOT / "output" / "natcs_evidence" / "table2c_rcep_full_path_attenuation_uncertainty.csv")
    rows = [
        ("Observed\n$W_t$", "evolving_coefficient", TEAL),
        ("Frozen\n$W_{pre}$", "frozen_coefficient", "#7aa6ae"),
        ("Observed -\nfrozen", "attenuation_difference", GOLD),
    ]
    y = np.arange(len(rows))[::-1]
    all_lows = []
    all_highs = []
    for idx, (label, quantity, color) in enumerate(rows):
        cy = y[idx]
        cond_row = conditional[conditional["quantity"] == quantity].iloc[0]
        full_row = full_path[full_path["quantity"] == quantity].iloc[0]
        point = float(cond_row["point"])
        full_low = float(full_row["p025"])
        full_high = float(full_row["p975"])
        cond_low = float(cond_row["p025"])
        cond_high = float(cond_row["p975"])
        all_lows.extend([full_low, cond_low])
        all_highs.extend([full_high, cond_high])
        ax.plot([cond_low, cond_high], [cy + 0.16, cy + 0.16], color=color, lw=2.7, zorder=3)
        ax.scatter([point], [cy + 0.16], s=32, color=color, edgecolor="white", linewidth=0.5, zorder=4)
        ax.plot([full_low, full_high], [cy - 0.16, cy - 0.16], color="#555555", lw=1.35, ls=(0, (3, 2)), zorder=1)
        ax.scatter([point], [cy - 0.16], s=24, facecolor="white", edgecolor="#555555", linewidth=0.9, zorder=2)
    ax.axvline(0, color=BLACK, lw=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows])
    x_min = min(-0.00085, min(all_lows) - 0.00018)
    x_max = max(0.00405, max(all_highs) + 0.00018)
    ax.set_title("Coefficient estimates and uncertainty layers", loc="left", pad=5, fontsize=8.2)
    ax.set_xlabel("Coefficient", fontsize=7.2)
    ax.grid(axis="x", color="#eeeeee", lw=0.45)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-0.62, len(rows) - 0.50)
    ax.text(
        0.62,
        0.30,
        "fixed-path CI",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=7.1,
        color=GOLD,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.6},
    )
    ax.text(
        0.62,
        0.18,
        "re-estimated CI",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=7.1,
        color="#555555",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 0.6},
    )
    ax.plot([0.59, 0.61], [0.30, 0.30], transform=ax.transAxes, color=GOLD, lw=2.7, clip_on=False)
    ax.plot([0.59, 0.61], [0.18, 0.18], transform=ax.transAxes, color="#555555", lw=1.35, ls=(0, (3, 2)), clip_on=False)
    clean_axes(ax)


def draw_girf_reallocation(ax, out_dir: Path):
    points = load_json(out_dir / "girf_cp_point.json")
    dates = list(points.keys())
    stats = []
    for date in dates:
        total = np.asarray(points[date]["total"], dtype=float)
        direct = np.asarray(points[date]["direct"], dtype=float)
        network = np.asarray(points[date]["network"], dtype=float)
        stats.append({
            "date": date[:4],
            "direct_abs": np.abs(direct).sum(),
            "network_abs": np.abs(network).sum(),
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
            f"network share\n{s['network_share']:.2f}",
            ha="center",
            va="bottom",
            color=BLACK,
            fontsize=5.6,
            linespacing=0.92,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.35},
            clip_on=False,
        )
    ax.set_xticks(x)
    ax.set_xticklabels([s["date"] for s in stats])
    ax.set_ylabel("Absolute GIRF mass")
    ax.set_title("GIRF mass by channel", loc="left", pad=5)
    ax.set_ylim(0, ymax)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.01), ncol=2, handlelength=0.9, columnspacing=0.8)
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_stability(ax, out_dir: Path):
    stability = pd.read_csv(out_dir / "stability_summary.csv", parse_dates=["date"])
    ax.plot(stability["date"], stability["radius_cp"], color=BLACK, lw=1.1)
    ax.axhline(1.0, color="#9d4f4d", lw=0.8, ls="--")
    unstable = stability[stability["unstable"] == 1]
    if not unstable.empty:
        ax.scatter(unstable["date"], unstable["radius_cp"], s=10, color="#9d4f4d", zorder=3)
    ax.set_title("Stability monitor", loc="left", pad=3)
    ax.set_ylabel("Spectral radius")
    ax.set_xlabel("Date")
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_topology_diagnostics(ax, out_dir: Path):
    corr = pd.read_csv(out_dir / "network_mechanism_correlations.csv")
    corr = corr[(corr["target"] == "g_net") & corr["spearman"].notna()].copy()
    keep = [
        ("Spectral gap", "spectral_gap_W"),
        ("Asymmetry", "directional_asymmetry"),
        ("Import inequality", "import_exposure_gini"),
        ("Eff. rank", "spectral_effective_rank_W"),
    ]
    rows = []
    for label, metric in keep:
        hit = corr[corr["metric"] == metric]
        if not hit.empty:
            rows.append((label, float(hit.iloc[0]["spearman"])))
    labels = [r[0] for r in rows]
    vals = np.array([r[1] for r in rows])
    colors = [TEAL if v >= 0 else BLUE for v in vals]
    y = np.arange(len(rows))[::-1]
    ax.barh(y, vals, color=colors, height=0.56)
    ax.axvline(0, color=BLACK, lw=0.65)
    for yy, val in zip(y, vals):
        offset = 0.018 if val >= 0 else -0.018
        ha = "left" if val >= 0 else "right"
        ax.text(val + offset, yy, f"{val:.2f}", ha=ha, va="center", fontsize=5.8, color=BLACK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel(r"Descriptive Spearman with $G(t,H)$")
    ax.set_title("Level association only", loc="left", pad=3)
    ax.set_xlim(-0.55, 0.55)
    ax.grid(axis="x", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def draw_perturbation(ax, out_dir: Path):
    summary = pd.read_csv(out_dir / "network_propagation_perturbation_summary.csv").iloc[0]
    vals = [summary["mean_g_net_base"], summary["mean_g_net_perturbed"]]
    labels = ["Observed", "50% attenuated"]
    colors = [GREY, TEAL]
    ax.bar(labels, vals, color=colors, width=0.52)
    ax.axhline(0, color=BLACK, lw=0.65)
    ax.set_title("Top-exposure perturbation", loc="left", pad=4)
    ax.set_ylabel(r"Mean $G(t,H)$")
    ax.set_xlabel("Exposure setting", labelpad=3)
    ax.tick_params(axis="x", pad=3)
    ymax = max(vals) * 1.82
    ax.set_ylim(0, ymax)
    x0, x1 = 0, 1
    y = max(vals) + ymax * 0.045
    bracket_h = ymax * 0.018
    ax.plot([x0, x0, x1, x1], [y, y + bracket_h, y + bracket_h, y], color=BLACK, lw=0.65)
    ax.text(
        0.5,
        y + bracket_h + ymax * 0.014,
        rf"$\Delta$ {summary['mean_g_net_delta']:.4f}",
        ha="center",
        va="bottom",
        fontsize=5.8,
        color=BLACK,
        clip_on=False,
    )
    ax.grid(axis="y", color="#eeeeee", lw=0.45)
    clean_axes(ax)


def main() -> int:
    out_dir = ROOT / "output" / "natcs_empirical_cp" / "rcep"
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(7.35, 5.95))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.08, 1.02, 0.92], hspace=0.78, wspace=0.50)
    axes = [
        fig.add_subplot(gs[0, :]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[2, :]),
    ]
    draw_coefficient_boundary(axes[0], out_dir)
    draw_topology_contrast(axes[1], out_dir)
    draw_girf_reallocation(axes[2], out_dir)
    draw_topology_diagnostics(axes[3], out_dir)
    for label, ax in zip("abcd", axes):
        panel_label(ax, label)
    fig.savefig(fig_dir / "fig_rcep_operator_switch.png", dpi=900, bbox_inches="tight")
    fig.savefig(fig_dir / "fig_rcep_operator_switch.pdf", bbox_inches="tight")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
