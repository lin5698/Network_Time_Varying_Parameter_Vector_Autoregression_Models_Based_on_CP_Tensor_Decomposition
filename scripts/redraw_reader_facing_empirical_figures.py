from __future__ import annotations

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
    "xtick.labelsize": 6.4,
    "ytick.labelsize": 6.4,
    "legend.fontsize": 6.4,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def reader_label(value: str) -> str:
    return (
        str(value)
        .replace("Unclipped s_net_raw", "Unbounded raw pair-level contribution")
        .replace("1-99 trimmed s_net_raw", "1st-99th percentile trimmed raw pair-level contribution")
        .replace("s_net_clip", "bounded pair-level contribution")
        .replace("s_net_raw", "raw pair-level contribution")
        .replace("g_net", "aggregate network-propagation index")
        .replace("Agg_g_net(H=8)", "Aggregate network-propagation index, H=8")
    )


def save(fig, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(stem.with_suffix(".png"), dpi=900)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)


def coefficient_plot(rcep: Path) -> None:
    table = pd.read_csv(rcep / "table_rcep_cp_benchmark.csv")
    table = table.copy()
    table["Specification"] = table["Specification"].map(reader_label)
    table["coef"] = pd.to_numeric(table["Coefficient"], errors="coerce")
    table["se"] = pd.to_numeric(table["Std.Err"], errors="coerce")
    table = table.dropna(subset=["coef", "se"])

    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    y = np.arange(len(table))[::-1]
    ax.axvline(0, color="black", lw=0.8, alpha=0.75)
    ax.errorbar(table["coef"], y, xerr=1.96 * table["se"], fmt="o", color="#1f77b4", ecolor="#6baed6", capsize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(table["Specification"])
    ax.set_xlabel("Coefficient on tariff relief")
    ax.set_title("RCEP benchmark and inference panel")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save(fig, rcep / "figures" / "fig_cp_coefficient_plot")


def aggregate_plot(out_dir: Path, baseline_key: str = "baseline_import") -> None:
    metrics = pd.read_csv(out_dir / "aggregate_cp_metrics.csv", parse_dates=["date"])
    boot = pd.read_csv(out_dir / "aggregate_cp_bootstrap.csv", parse_dates=["date"])
    agg = metrics[metrics["variant_key"] == baseline_key].copy()

    fig, axes = plt.subplots(2, 1, figsize=(8.8, 6.8), sharex=True)
    axes[0].plot(agg["date"], agg["g_net"], color="#1f77b4", lw=2)
    axes[0].fill_between(boot["date"], boot["g_net_p16"], boot["g_net_p84"], color="#9ecae1", alpha=0.5)
    axes[0].fill_between(boot["date"], boot["g_net_p025"], boot["g_net_p975"], color="#c6dbef", alpha=0.35)
    axes[0].set_ylabel("Aggregate network-propagation index")
    axes[0].set_title("Aggregate propagation index with bootstrap intervals")

    axes[1].plot(agg["date"], agg["half_life"], color="#dd8452", lw=2)
    axes[1].fill_between(boot["date"], boot["hl_p16"], boot["hl_p84"], color="#fdd0a2", alpha=0.5)
    axes[1].fill_between(boot["date"], boot["hl_p025"], boot["hl_p975"], color="#fee6ce", alpha=0.35)
    axes[1].set_ylabel("Half-life")
    axes[1].set_xlabel("Date")
    for ax in axes:
        ax.axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=0.85)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    save(fig, out_dir / "figures" / "fig_cp_aggregate_intervals")


def fixed_vs_observed_plot(rcep: Path) -> None:
    metrics = pd.read_csv(rcep / "aggregate_cp_metrics.csv", parse_dates=["date"])
    boot = pd.read_csv(rcep / "aggregate_cp_bootstrap.csv", parse_dates=["date"])
    observed = metrics[metrics["variant_key"] == "baseline_import"][["date", "g_net"]]
    frozen = metrics[metrics["variant_key"] == "fixed_pre"][["date", "g_net"]]
    merged = observed.merge(frozen, on="date", suffixes=("_observed", "_frozen"))
    merged["diff"] = merged["g_net_observed"] - merged["g_net_frozen"]

    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.fill_between(boot["date"], boot["g_net_diff_p025"], boot["g_net_diff_p975"], color="#d9e8ef", alpha=0.62, linewidth=0)
    ax.fill_between(boot["date"], boot["g_net_diff_p16"], boot["g_net_diff_p84"], color="#aac8d6", alpha=0.58, linewidth=0)
    ax.plot(merged["date"], merged["diff"], color="#111111", lw=1.65, label="Point estimate")
    entry = pd.Timestamp("2022-01-01")
    ax.axvline(entry, color="#111111", ls="--", lw=0.9)
    ax.axhline(0, color="#111111", lw=0.8)
    ax.set_ylabel("Observed-minus-frozen aggregate-index difference")
    ax.set_xlabel("Date")
    ax.text(0.02, 0.94, "Evolving minus frozen topology", transform=ax.transAxes, ha="left", va="top", fontsize=8)
    ax.text(entry, ax.get_ylim()[1], "RCEP entry", ha="left", va="top", fontsize=7, rotation=90)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#eeeeee", lw=0.55)
    save(fig, rcep / "figures" / "fig_cp_fixed_vs_tv")


def main() -> int:
    rcep = ROOT / "output" / "natcs_empirical_cp" / "rcep"
    nyc = ROOT / "output" / "natcs_empirical_cp" / "nyc_taxi"
    coefficient_plot(rcep)
    aggregate_plot(rcep, "baseline_import")
    fixed_vs_observed_plot(rcep)
    aggregate_plot(nyc, "baseline_mobility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
