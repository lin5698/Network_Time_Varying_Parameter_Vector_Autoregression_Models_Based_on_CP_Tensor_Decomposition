import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp" / "matplotlib_cache"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp" / "xdg_cache"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 7.0,
    "axes.titlesize": 7.6,
    "axes.labelsize": 7.0,
    "xtick.labelsize": 6.2,
    "ytick.labelsize": 6.2,
    "axes.linewidth": 0.75,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

EPS = 1e-12
OUT_DIR = ROOT / "output" / "natcs_empirical_cp" / "nyc_taxi"
FIG_DIR = OUT_DIR / "figures"
TAXI_ROOT = ROOT / "tmp" / "vars_repo" / "datasets" / "NYC-taxi"


def safe_row_normalize(W):
    W = np.asarray(W, dtype=float).copy()
    np.fill_diagonal(W, 0.0)
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums <= EPS] = 1.0
    return W / row_sums


def build_monthly_mats():
    monthly_mats = []
    monthly_dates = []
    for year in range(2012, 2022):
        arr = np.load(TAXI_ROOT / f"yellow_taxi_trip_{year}.npz")["arr_0"]
        dates = pd.date_range(f"{year}-01-01", periods=arr.shape[2], freq="D")
        month_index = pd.PeriodIndex(dates, freq="M")
        for period in month_index.unique():
            idx = np.where(month_index == period)[0]
            monthly_mats.append(arr[:, :, idx].sum(axis=2))
            monthly_dates.append(period.to_timestamp("M"))
    return monthly_dates, monthly_mats


def raw_taxi_files_available():
    return all((TAXI_ROOT / f"yellow_taxi_trip_{year}.npz").exists() for year in range(2012, 2022))


def mobility_network_path():
    monthly_dates, monthly_mats = build_monthly_mats()
    rolling_dates = []
    rolling_mats = []
    for idx in range(11, len(monthly_mats)):
        rolling_dates.append(monthly_dates[idx])
        rolling_mats.append(sum(monthly_mats[idx - j] for j in range(12)))

    acquisition = json.loads((OUT_DIR / "acquisition_info.json").read_text())
    top_idx = acquisition.get("top_indices")
    if top_idx is None:
        total_volume = np.zeros(rolling_mats[0].shape[0], dtype=float)
        for mat in rolling_mats:
            total_volume += mat.sum(axis=1) + mat.sum(axis=0)
        top_idx = np.argsort(total_volume)[::-1][:15].tolist()

    rows = []
    for date, mat in zip(rolling_dates, rolling_mats):
        sub = np.asarray(mat[np.ix_(top_idx, top_idx)], dtype=float)
        W = safe_row_normalize(sub)
        rows.append((pd.Timestamp(date), W))
    return rows


def spectral_effective_rank(W):
    s = np.linalg.svd(W, compute_uv=False)
    p = s / max(s.sum(), EPS)
    entropy = -(p * np.log(np.maximum(p, EPS))).sum()
    return float(np.exp(entropy))


def gini(x):
    x = np.asarray(x, dtype=float)
    if np.allclose(x, 0):
        return 0.0
    x = np.sort(np.maximum(x, 0))
    n = len(x)
    return float((2 * np.arange(1, n + 1) @ x) / (n * x.sum()) - (n + 1) / n)


def network_metrics(date, W, prev_W=None):
    eig = np.linalg.eigvals(W)
    abs_eig = np.sort(np.abs(eig))[::-1]
    spectral_radius = float(abs_eig[0]) if len(abs_eig) else 0.0
    spectral_gap = float(abs_eig[0] - abs_eig[1]) if len(abs_eig) > 1 else spectral_radius
    asym = float(np.linalg.norm(W - W.T, ord="fro") / max(np.linalg.norm(W, ord="fro"), EPS))
    reciprocity = float(np.minimum(W, W.T).sum() / max(W.sum(), EPS))
    incoming = W.sum(axis=0)
    outgoing = W.sum(axis=1)
    weights = W[~np.eye(W.shape[0], dtype=bool)]
    turnover = np.nan
    if prev_W is not None:
      turnover = float(np.abs(W - prev_W).sum() / max(np.abs(prev_W).sum(), EPS))
    return {
        "date": date.strftime("%Y-%m-%d"),
        "spectral_radius_W": spectral_radius,
        "spectral_gap_W": spectral_gap,
        "spectral_effective_rank_W": spectral_effective_rank(W),
        "directional_asymmetry": asym,
        "weighted_reciprocity": reciprocity,
        "incoming_gini": gini(incoming),
        "outgoing_gini": gini(outgoing),
        "top3_incoming_share": float(np.sort(incoming)[-3:].sum() / max(incoming.sum(), EPS)),
        "weight_concentration_gini": gini(weights),
        "weight_turnover": turnover,
    }


def corr_table(panel):
    metrics = [
        "spectral_gap_W",
        "spectral_effective_rank_W",
        "directional_asymmetry",
        "weighted_reciprocity",
        "incoming_gini",
        "outgoing_gini",
        "top3_incoming_share",
        "weight_concentration_gini",
        "weight_turnover",
    ]
    rows = []
    for metric in metrics:
        x = panel[metric]
        y = panel["g_net"]
        valid = x.notna() & y.notna()
        if valid.sum() < 3 or x[valid].nunique() <= 1 or y[valid].nunique() <= 1:
            pearson = np.nan
            spearman = np.nan
        else:
            pearson = x[valid].corr(y[valid], method="pearson")
            spearman = x[valid].corr(y[valid], method="spearman")
        rows.append({
            "metric": metric,
            "target": "g_net",
            "n": int(valid.sum()),
            "pearson": pearson,
            "spearman": spearman,
        })
    return pd.DataFrame(rows)


def plot_mechanisms(panel, corr):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    top = corr.dropna(subset=["spearman"]).copy()
    top["abs_spearman"] = top["spearman"].abs()
    top = top.sort_values("abs_spearman", ascending=False).head(4)
    labels = {
        "spectral_gap_W": "Spectral gap",
        "spectral_effective_rank_W": "Spectral effective rank",
        "directional_asymmetry": "Directional asymmetry",
        "weighted_reciprocity": "Weighted reciprocity",
        "incoming_gini": "Incoming Gini",
        "outgoing_gini": "Outgoing Gini",
        "top3_incoming_share": "Top-3 incoming share",
        "weight_concentration_gini": "Weight concentration Gini",
        "weight_turnover": "Weight turnover",
    }
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.25), dpi=300)
    axes = axes.ravel()
    for label, ax, (_, row) in zip("abcd", axes, top.iterrows()):
        metric = row["metric"]
        ax.scatter(panel[metric], panel["g_net"], s=9, color="#295f8a", alpha=0.72)
        ax.set_xlabel(labels.get(metric, metric.replace("_", " ")))
        ax.set_ylabel(r"$G(t,H)$")
        ax.set_title(f"{label}  Spearman {row['spearman']:.2f}", loc="left", fontweight="bold")
        ax.grid(alpha=0.22, lw=0.45)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    for ax in axes[len(top):]:
        ax.axis("off")
    fig.suptitle("NYC Taxi mobility topology diagnostics", fontsize=8.6, fontweight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.965), h_pad=1.9, w_pad=1.6)
    fig.savefig(FIG_DIR / "fig_nyc_network_mechanisms.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig_nyc_network_mechanisms.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if raw_taxi_files_available():
        network_rows = mobility_network_path()
        metrics = []
        prev = None
        for date, W in network_rows:
            metrics.append(network_metrics(date, W, prev))
            prev = W
        metrics_df = pd.DataFrame(metrics)
        agg = pd.read_csv(OUT_DIR / "aggregate_cp_metrics.csv")
        baseline = agg[(agg["variant_key"] == "baseline_mobility") & (agg["H"] == 8)][["date", "g_net", "half_life"]]
        panel = baseline.merge(metrics_df, on="date", how="left")
        corr = corr_table(panel)
        panel.to_csv(OUT_DIR / "nyc_network_mechanism_panel.csv", index=False)
        metrics_df.to_csv(OUT_DIR / "nyc_network_structure_metrics.csv", index=False)
        corr.to_csv(OUT_DIR / "nyc_network_mechanism_correlations.csv", index=False)
    else:
        panel_path = OUT_DIR / "nyc_network_mechanism_panel.csv"
        corr_path = OUT_DIR / "nyc_network_mechanism_correlations.csv"
        missing = [path for path in [panel_path, corr_path] if not path.exists()]
        if missing:
            missing_names = ", ".join(str(path.relative_to(ROOT)) for path in missing)
            raise FileNotFoundError(f"NYC raw files are unavailable and derived mechanism files are missing: {missing_names}")
        panel = pd.read_csv(panel_path)
        corr = pd.read_csv(corr_path)
    plot_mechanisms(panel, corr)


if __name__ == "__main__":
    main()
