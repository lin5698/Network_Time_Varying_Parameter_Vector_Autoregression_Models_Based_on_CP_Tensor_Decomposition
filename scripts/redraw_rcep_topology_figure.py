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
import pandas as pd


plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def main() -> int:
    out_dir = ROOT / "output" / "natcs_empirical_cp" / "rcep"
    fig_dir = out_dir / "figures"
    metrics = pd.read_csv(out_dir / "aggregate_cp_metrics.csv", parse_dates=["date"])
    boot = pd.read_csv(out_dir / "aggregate_cp_bootstrap.csv", parse_dates=["date"])

    observed = metrics.loc[metrics["variant_key"] == "baseline_import", ["date", "g_net"]]
    frozen = metrics.loc[metrics["variant_key"] == "fixed_pre", ["date", "g_net"]]
    merged = observed.merge(frozen, on="date", suffixes=("_observed", "_frozen"))
    merged["diff"] = merged["g_net_observed"] - merged["g_net_frozen"]

    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.fill_between(boot["date"], boot["g_net_diff_p025"], boot["g_net_diff_p975"], color="#d9e8ef", alpha=0.62, linewidth=0)
    ax.fill_between(boot["date"], boot["g_net_diff_p16"], boot["g_net_diff_p84"], color="#aac8d6", alpha=0.58, linewidth=0)
    ax.plot(merged["date"], merged["diff"], color="#111111", lw=1.65)
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
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_cp_fixed_vs_tv.png", dpi=900)
    fig.savefig(fig_dir / "fig_cp_fixed_vs_tv.pdf")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
