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
    "font.size": 7.2,
    "axes.titlesize": 8.2,
    "axes.labelsize": 7.2,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def girf_plot(girf_point, girf_boot, out_png: Path, out_pdf: Path):
    date_keys = sorted(girf_point.keys())
    fig, axes = plt.subplots(1, len(date_keys), figsize=(4.85 * len(date_keys), 3.85), sharey=True)
    if len(date_keys) == 1:
        axes = [axes]
    for ax, date_key in zip(axes, date_keys):
        draws = girf_boot.get(date_key, [])
        horizon = list(range(len(girf_point[date_key]["total"])))
        for label, color in [("total", "#1f77b4"), ("direct", "#ff7f0e"), ("network", "#2ca02c")]:
            arr = np.array([d[label] for d in draws], dtype=float)
            if arr.size:
                p16 = np.quantile(arr, 0.16, axis=0)
                p84 = np.quantile(arr, 0.84, axis=0)
                p025 = np.quantile(arr, 0.025, axis=0)
                p975 = np.quantile(arr, 0.975, axis=0)
                ax.fill_between(horizon, p025, p975, color=color, alpha=0.12)
                ax.fill_between(horizon, p16, p84, color=color, alpha=0.25)
            ax.plot(horizon, girf_point[date_key][label], color=color, lw=2, label=label if date_key == date_keys[0] else None)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(date_key, fontsize=8.2, pad=4)
        ax.set_xlabel("Horizon")
        ax.tick_params(labelsize=8)
    axes[0].set_ylabel("Response")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout(w_pad=2.2)
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def stability_sensitivity_plot(exclusion_df: pd.DataFrame, projected_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.85))

    coef_rows = [
        exclusion_df[(exclusion_df["Statistic"] == "Pair-level coefficient") & (exclusion_df["Sample"] == "Full sample")].iloc[0],
        exclusion_df[(exclusion_df["Statistic"] == "Pair-level coefficient") & (exclusion_df["Sample"] == "Stable dates only")].iloc[0],
        projected_df[(projected_df["Statistic"] == "Pair-level coefficient") & (projected_df["Sample"] == "Stability-projected path")].iloc[0],
    ]
    coef_labels = ["Full\nsample", "Stable\ndates", "Projected\npath"]
    y = np.arange(len(coef_rows))[::-1]
    coef_vals = [float(row["Value"]) for row in coef_rows]
    coef_err = [1.96 * float(row["Std.Err"]) for row in coef_rows]
    axes[0].axvline(0, color="black", lw=0.8)
    axes[0].errorbar(coef_vals, y, xerr=coef_err, fmt="o", color="#1f77b4", ecolor="#93c5fd", capsize=3)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(coef_labels)
    axes[0].set_xlabel("Pair-level coefficient")
    axes[0].set_title("a  Pair-level coefficient sensitivity", loc="left", fontsize=8.2, fontweight="bold", pad=5)
    axes[0].tick_params(axis="both", labelsize=8)

    diff_rows = [
        exclusion_df[(exclusion_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (exclusion_df["Sample"] == "Full sample")].iloc[0],
        exclusion_df[(exclusion_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (exclusion_df["Sample"] == "Stable dates only")].iloc[0],
        projected_df[(projected_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (projected_df["Sample"] == "Stability-projected path")].iloc[0],
    ]
    diff_vals = [float(row["Value"]) for row in diff_rows]
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].plot(coef_labels, diff_vals, marker="o", color="#15803d", lw=2)
    axes[1].set_ylabel("Mean topology difference")
    axes[1].set_title("b  Topology-difference sensitivity", loc="left", fontsize=8.2, fontweight="bold", pad=5)
    axes[1].tick_params(axis="both", labelsize=8)

    fig.tight_layout(w_pad=2.4)
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def main() -> int:
    rcep = ROOT / "output" / "natcs_empirical_cp" / "rcep"
    fig_dir = rcep / "figures"
    girf_point = json.loads((rcep / "girf_cp_point.json").read_text())
    girf_boot = json.loads((rcep / "girf_cp_bootstrap.json").read_text())
    girf_plot(girf_point, girf_boot, fig_dir / "fig_cp_girf_intervals.png", fig_dir / "fig_cp_girf_intervals.pdf")

    exclusion = pd.read_csv(rcep / "stability_exclusion_sensitivity.csv")
    projected = pd.read_csv(rcep / "stability_projected_sensitivity.csv")
    stability_sensitivity_plot(
        exclusion,
        projected,
        fig_dir / "fig_cp_stability_sensitivity.png",
        fig_dir / "fig_cp_stability_sensitivity.pdf",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
