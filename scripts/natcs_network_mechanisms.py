import os
import sys
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

helper_repo = os.environ.get("NATCS_RCEP_HELPER_REPO")
if helper_repo:
    sys.path.insert(0, str(Path(helper_repo).expanduser().resolve()))

try:
    from research_data_construction import RCEP_LIST, build_trade_network_w, load_quarterly_macro_and_bilateral
except ModuleNotFoundError:
    RCEP_LIST = None
    build_trade_network_w = None
    load_quarterly_macro_and_bilateral = None


OUT_DIR = ROOT / "output" / "natcs_empirical_cp" / "rcep"
FIG_DIR = OUT_DIR / "figures"
EPS = 1e-12
MECHANISM_LABELS = {
    "spectral_gap_W": "Spectral gap",
    "directional_asymmetry": "Directional asymmetry",
    "weighted_reciprocity": "Weighted reciprocity",
    "import_exposure_gini": "Import exposure Gini",
    "node_strength_gini": "Node-strength Gini",
    "spectral_effective_rank_W": "Spectral effective rank",
    "spectral_entropy_W": "Spectral entropy",
    "stationary_exposure_gini": "Stationary exposure Gini",
    "top3_import_exposure_share": "Top-3 import exposure",
    "top3_stationary_exposure_share": "Top-3 stationary exposure",
    "weight_concentration_gini": "Weight concentration",
    "weight_turnover": "Weight turnover",
    "import_exposure_rank_turnover": "Import-rank turnover",
    "stationary_exposure_turnover": "Stationary turnover",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def safe_row_normalize(W):
    W = np.asarray(W, dtype=float).copy()
    np.fill_diagonal(W, 0.0)
    W[~np.isfinite(W)] = 0.0
    W[W < 0] = 0.0
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums <= EPS] = 1.0
    return W / row_sums


def weighted_gini(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0 or np.sum(np.abs(x)) <= EPS:
        return 0.0
    x = np.sort(np.abs(x))
    n = len(x)
    return float((2 * np.arange(1, n + 1) @ x) / (n * x.sum()) - (n + 1) / n)


def spectral_gap(W):
    vals = np.linalg.eigvals(np.asarray(W, dtype=float))
    mags = np.sort(np.abs(vals))[::-1]
    if len(mags) < 2:
        return 0.0
    return float(mags[0] - mags[1])


def spectral_effective_rank(W):
    s = np.linalg.svd(np.asarray(W, dtype=float), compute_uv=False)
    total = float(s.sum())
    if total <= EPS:
        return 0.0, 0.0
    p = s / total
    entropy = float(-(p[p > EPS] * np.log(p[p > EPS])).sum())
    return float(np.exp(entropy)), entropy


def weighted_reciprocity(W):
    W = safe_row_normalize(W)
    off = W[~np.eye(W.shape[0], dtype=bool)]
    denom = float(off.sum())
    if denom <= EPS:
        return 0.0
    mutual = np.minimum(W, W.T)
    return float(mutual[~np.eye(W.shape[0], dtype=bool)].sum() / denom)


def weighted_assortativity(W, scores):
    W = safe_row_normalize(W)
    scores = np.asarray(scores, dtype=float)
    rows, cols = np.where(~np.eye(W.shape[0], dtype=bool))
    weights = W[rows, cols]
    keep = weights > EPS
    if keep.sum() < 3:
        return np.nan
    weights = weights[keep]
    x = scores[rows[keep]]
    y = scores[cols[keep]]
    wx = float(np.average(x, weights=weights))
    wy = float(np.average(y, weights=weights))
    cov = float(np.average((x - wx) * (y - wy), weights=weights))
    vx = float(np.average((x - wx) ** 2, weights=weights))
    vy = float(np.average((y - wy) ** 2, weights=weights))
    if vx <= EPS or vy <= EPS:
        return np.nan
    return float(cov / np.sqrt(vx * vy))


def rank_turnover(values, previous_values):
    if previous_values is None:
        return np.nan
    current = pd.Series(np.asarray(values, dtype=float)).rank(method="average")
    previous = pd.Series(np.asarray(previous_values, dtype=float)).rank(method="average")
    rho = current.corr(previous, method="spearman")
    if pd.isna(rho):
        return np.nan
    return float(1.0 - rho)


def spectral_bipartition_modularity(W):
    W = safe_row_normalize(W)
    A = 0.5 * (W + W.T)
    total = float(A.sum())
    if total <= EPS:
        return 0.0, 0.0
    degree = A.sum(axis=1)
    B = A - np.outer(degree, degree) / total
    vals, vecs = np.linalg.eigh(B)
    leading = np.real(vecs[:, int(np.argmax(vals))])
    labels = leading >= 0
    if labels.all() or (~labels).all():
        return 0.0, 0.0
    same = labels[:, None] == labels[None, :]
    modularity = float(B[same].sum() / total)
    cross_share = float(A[~same].sum() / total)
    return modularity, cross_share


def stationary_exposure(W):
    W = safe_row_normalize(W)
    vals, vecs = np.linalg.eig(W.T)
    idx = int(np.argmin(np.abs(vals - 1.0)))
    v = np.real(vecs[:, idx])
    if np.sum(v) < 0:
        v = -v
    v = np.abs(v)
    if v.sum() <= EPS:
        return np.repeat(1.0 / W.shape[0], W.shape[0])
    return v / v.sum()


def normalized_in_strength(W):
    incoming = safe_row_normalize(W).sum(axis=0)
    return incoming / max(incoming.sum(), EPS)


def network_metrics(W, W_prev=None):
    W = safe_row_normalize(W)
    n = W.shape[0]
    off = W[~np.eye(n, dtype=bool)]
    active = off > 1e-8
    node_strength = W.sum(axis=0) + W.sum(axis=1)
    import_exposure = normalized_in_strength(W)
    stationary = stationary_exposure(W)
    effective_rank, spectral_entropy = spectral_effective_rank(W)
    modularity, cross_block_share = spectral_bipartition_modularity(W)
    edge_turnover = np.nan
    weight_turnover = np.nan
    import_exposure_turnover = np.nan
    stationary_turnover = np.nan
    import_exposure_rank_turnover = np.nan
    stationary_exposure_rank_turnover = np.nan
    if W_prev is not None:
        Wp = safe_row_normalize(W_prev)
        active_prev = Wp[~np.eye(n, dtype=bool)] > 1e-8
        union = np.logical_or(active, active_prev).sum()
        edge_turnover = float(np.logical_xor(active, active_prev).sum() / max(union, 1))
        weight_turnover = float(np.sum(np.abs(W - Wp)) / max(np.sum(np.abs(Wp)), EPS))
        prev_import = normalized_in_strength(Wp)
        prev_stationary = stationary_exposure(Wp)
        import_exposure_turnover = float(np.sum(np.abs(import_exposure - prev_import)))
        stationary_turnover = float(np.sum(np.abs(stationary - prev_stationary)))
        import_exposure_rank_turnover = rank_turnover(import_exposure, prev_import)
        stationary_exposure_rank_turnover = rank_turnover(stationary, prev_stationary)
    return {
        "density": float(active.mean()),
        "weight_concentration_gini": weighted_gini(off),
        "node_strength_gini": weighted_gini(node_strength),
        "max_node_strength_share": float(node_strength.max() / max(node_strength.sum(), EPS)),
        "import_exposure_gini": weighted_gini(import_exposure),
        "max_import_exposure_share": float(import_exposure.max()),
        "top3_import_exposure_share": float(np.sort(import_exposure)[-3:].sum()),
        "stationary_exposure_gini": weighted_gini(stationary),
        "max_stationary_exposure_share": float(stationary.max()),
        "top3_stationary_exposure_share": float(np.sort(stationary)[-3:].sum()),
        "spectral_radius_W": float(np.max(np.abs(np.linalg.eigvals(W)))),
        "spectral_gap_W": spectral_gap(W),
        "spectral_effective_rank_W": effective_rank,
        "spectral_entropy_W": spectral_entropy,
        "weighted_reciprocity": weighted_reciprocity(W),
        "directional_asymmetry": float(1.0 - weighted_reciprocity(W)),
        "import_exposure_assortativity": weighted_assortativity(W, import_exposure),
        "stationary_exposure_assortativity": weighted_assortativity(W, stationary),
        "spectral_bipartition_modularity": modularity,
        "cross_block_weight_share": cross_block_share,
        "edge_turnover": edge_turnover,
        "weight_turnover": weight_turnover,
        "import_exposure_turnover": import_exposure_turnover,
        "stationary_exposure_turnover": stationary_turnover,
        "import_exposure_rank_turnover": import_exposure_rank_turnover,
        "stationary_exposure_rank_turnover": stationary_exposure_rank_turnover,
    }


def build_w(date, df_bilateral):
    W = build_trade_network_w(df_bilateral, date, window_quarters=4, mode="import")
    if isinstance(W, pd.DataFrame):
        W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0).values
    return safe_row_normalize(W)


def corr_row(df, x, y):
    sub = df[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if len(sub) < 4:
        return {"metric": x, "target": y, "n": len(sub), "pearson": np.nan, "spearman": np.nan}
    return {
        "metric": x,
        "target": y,
        "n": int(len(sub)),
        "pearson": float(sub[x].corr(sub[y], method="pearson")),
        "spearman": float(sub[x].corr(sub[y], method="spearman")),
    }


def perturb_top_exposure(W, scale_factor=0.5):
    W = safe_row_normalize(W)
    exposure = normalized_in_strength(W)
    hub = int(np.argmax(exposure))
    incoming = W.copy()
    incoming[:, hub] *= scale_factor
    incoming = safe_row_normalize(incoming)
    outgoing = W.copy()
    outgoing[hub, :] *= scale_factor
    outgoing = safe_row_normalize(outgoing)
    both = W.copy()
    both[:, hub] *= scale_factor
    both[hub, :] *= scale_factor
    both = safe_row_normalize(both)
    return hub, {
        "attenuate_top_import_exposure_incoming": incoming,
        "attenuate_top_import_exposure_outgoing": outgoing,
        "attenuate_top_import_exposure_both": both,
    }


def perturbation_rows(merged, df_bilateral):
    rows = []
    for date in list(merged["date"]):
        W = build_w(date, df_bilateral)
        base = network_metrics(W)
        hub, variants = perturb_top_exposure(W)
        unit = RCEP_LIST[hub]
        base_gap = base["spectral_gap_W"]
        base_stationary = base["stationary_exposure_gini"]
        base_import = base["import_exposure_gini"]
        for variant, Wp in variants.items():
            pm = network_metrics(Wp)
            rows.append({
                "date": pd.Timestamp(date),
                "perturbation": variant,
                "target_unit": unit,
                "spectral_gap_delta": pm["spectral_gap_W"] - base_gap,
                "import_exposure_gini_delta": pm["import_exposure_gini"] - base_import,
                "stationary_exposure_gini_delta": pm["stationary_exposure_gini"] - base_stationary,
                "baseline_spectral_gap": base_gap,
                "perturbed_spectral_gap": pm["spectral_gap_W"],
                "baseline_import_exposure_gini": base_import,
                "perturbed_import_exposure_gini": pm["import_exposure_gini"],
                "baseline_stationary_exposure_gini": base_stationary,
                "perturbed_stationary_exposure_gini": pm["stationary_exposure_gini"],
            })
    return pd.DataFrame(rows)


def perturbation_summary(perturb, merged):
    gnet = merged[["date", "g_net"]].copy()
    out = perturb.merge(gnet, on="date", how="left")
    rows = []
    for variant, grp in out.groupby("perturbation"):
        rows.append({
            "perturbation": variant,
            "n": int(len(grp)),
            "mean_spectral_gap_delta": float(grp["spectral_gap_delta"].mean()),
            "mean_import_exposure_gini_delta": float(grp["import_exposure_gini_delta"].mean()),
            "mean_stationary_exposure_gini_delta": float(grp["stationary_exposure_gini_delta"].mean()),
            "spearman_gap_delta_vs_g_net": float(grp["spectral_gap_delta"].corr(grp["g_net"], method="spearman")),
            "spearman_import_gini_delta_vs_g_net": float(grp["import_exposure_gini_delta"].corr(grp["g_net"], method="spearman")),
            "dominant_target_unit": grp["target_unit"].mode().iloc[0],
        })
    return pd.DataFrame(rows)


def plot_mechanisms(merged, corr, out_png, out_pdf):
    fig, axes = plt.subplots(2, 2, figsize=(8.4, 6.2))
    ax = axes[0, 0]
    ax.plot(merged["date"], merged["g_net"], color="#111111", lw=1.45, label="Aggregate propagation")
    ax2 = ax.twinx()
    ax2.plot(merged["date"], merged["weight_concentration_gini"], color="#b78b50", lw=1.25, label="Weight concentration")
    ax.set_title("a  Propagation with concentration diagnostic", loc="left", fontweight="normal")
    ax.set_ylabel("Aggregate network-propagation index")
    ax2.set_ylabel("Gini")

    ax = axes[0, 1]
    ax.plot(merged["date"], merged["weight_turnover"], color="#111111", lw=1.45, label="Weight turnover")
    ax2 = ax.twinx()
    ax2.plot(merged["date"], merged["spectral_gap_W"], color="#8fb6c9", lw=1.25, label="Spectral gap")
    ax.set_title("b  Turnover and spectral diagnostics", loc="left", fontweight="normal")
    ax.set_ylabel("Turnover")
    ax2.set_ylabel("Spectral gap")

    ax = axes[1, 0]
    ax.scatter(
        merged["stationary_exposure_gini"],
        merged["g_net"],
        s=18,
        color="#111111",
        alpha=0.62,
        linewidths=0,
    )
    ax.set_title("c  Exposure inequality diagnostic", loc="left", fontweight="normal")
    ax.set_xlabel("Stationary exposure Gini")
    ax.set_ylabel("Aggregate network-propagation index")

    ax = axes[1, 1]
    plot_corr = corr[corr["target"] == "g_net"].copy()
    plot_corr = plot_corr.replace([np.inf, -np.inf], np.nan).dropna(subset=["spearman"])
    redundant_metrics = {
        "weighted_reciprocity",
        "spectral_entropy_W",
        "node_strength_gini",
        "max_import_exposure_share",
        "max_stationary_exposure_share",
        "max_node_strength_share",
    }
    plot_corr = plot_corr[~plot_corr["metric"].isin(redundant_metrics)]
    plot_corr = plot_corr.assign(abs_spearman=plot_corr["spearman"].abs())
    plot_corr = plot_corr.sort_values("abs_spearman", ascending=False).head(8)
    plot_corr = plot_corr.sort_values("spearman")
    plot_corr["label"] = plot_corr["metric"].map(MECHANISM_LABELS).fillna(
        plot_corr["metric"].str.replace("_", " ").str.replace(" W", "", regex=False).str.title()
    )
    colors = np.where(plot_corr["spearman"] >= 0, "#777777", "#b78b50")
    ax.barh(plot_corr["label"], plot_corr["spearman"], color=colors, height=0.55)
    ax.axvline(0, color="#111111", lw=0.85)
    ax.set_title("d  Rank associations with aggregate propagation", loc="left", fontweight="normal")
    ax.set_xlabel("Spearman with aggregate index")
    ax.tick_params(axis="y", labelsize=7.1)

    for a in axes.ravel():
        a.grid(axis="y", color="#eeeeee", lw=0.55)
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)
    for a in fig.axes:
        a.spines["top"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def plot_perturbations(summary, out_png, out_pdf):
    labels = [x.replace("attenuate_top_import_exposure_", "") for x in summary["perturbation"]]
    x = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.6))
    axes[0].bar(x - 0.18, summary["mean_spectral_gap_delta"], width=0.36, color="#7c3aed", label="Spectral gap")
    axes[0].bar(x + 0.18, summary["mean_import_exposure_gini_delta"], width=0.36, color="#b45309", label="Import exposure Gini")
    axes[0].axhline(0, color="black", lw=1)
    axes[0].set_xticks(x, labels, rotation=20, ha="right")
    axes[0].set_title("a. Top-exposure perturbation shifts topology")
    axes[0].set_ylabel("Mean change")
    axes[0].legend(frameon=False, fontsize=8)

    axes[1].bar(x, summary["spearman_gap_delta_vs_g_net"], color="#4b5563")
    axes[1].axhline(0, color="black", lw=1)
    axes[1].set_xticks(x, labels, rotation=20, ha="right")
    axes[1].set_title("b. Perturbation strength versus propagation")
    axes[1].set_ylabel("Spearman correlation with aggregate index")
    for ax in axes:
        ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    existing_panel = OUT_DIR / "network_mechanism_panel.csv"
    existing_corr = OUT_DIR / "network_mechanism_correlations.csv"
    if existing_panel.exists() and existing_corr.exists() and os.environ.get("NATCS_REBUILD_MECHANISM_EVIDENCE") != "1":
        merged = pd.read_csv(existing_panel, parse_dates=["date"])
        corr = pd.read_csv(existing_corr)
        plot_mechanisms(
            merged,
            corr,
            FIG_DIR / "fig_network_mechanisms.png",
            FIG_DIR / "fig_network_mechanisms.pdf",
        )
        print({
            "mode": "redraw_from_existing_evidence",
            "panel": str(existing_panel),
            "correlations": str(existing_corr),
            "figure": str(FIG_DIR / "fig_network_mechanisms.pdf"),
        })
        return

    if load_quarterly_macro_and_bilateral is None:
        raise ModuleNotFoundError("research_data_construction is unavailable and existing mechanism evidence CSVs were not found")

    _, df_bilateral = load_quarterly_macro_and_bilateral()
    agg = pd.read_csv(OUT_DIR / "aggregate_cp_metrics.csv", parse_dates=["date"])
    agg = agg[agg["variant_key"] == "baseline_import"].copy()
    dates = list(agg["date"])
    rows = []
    prev = None
    for date in dates:
        W = build_w(date, df_bilateral)
        row = {"date": pd.Timestamp(date), **network_metrics(W, prev)}
        rows.append(row)
        prev = W
    metrics = pd.DataFrame(rows)
    merged = agg.merge(metrics, on="date", how="left")
    metric_cols = [
        "density",
        "weight_concentration_gini",
        "node_strength_gini",
        "max_node_strength_share",
        "import_exposure_gini",
        "max_import_exposure_share",
        "top3_import_exposure_share",
        "stationary_exposure_gini",
        "max_stationary_exposure_share",
        "top3_stationary_exposure_share",
        "spectral_radius_W",
        "spectral_gap_W",
        "spectral_effective_rank_W",
        "spectral_entropy_W",
        "weighted_reciprocity",
        "directional_asymmetry",
        "import_exposure_assortativity",
        "stationary_exposure_assortativity",
        "spectral_bipartition_modularity",
        "cross_block_weight_share",
        "edge_turnover",
        "weight_turnover",
        "import_exposure_turnover",
        "stationary_exposure_turnover",
        "import_exposure_rank_turnover",
        "stationary_exposure_rank_turnover",
    ]
    corr = pd.DataFrame([corr_row(merged, m, target) for target in ["g_net", "half_life"] for m in metric_cols])
    perturb = perturbation_rows(merged, df_bilateral)
    perturb_summary_df = perturbation_summary(perturb, merged)
    metrics.to_csv(OUT_DIR / "network_structure_metrics.csv", index=False)
    corr.to_csv(OUT_DIR / "network_mechanism_correlations.csv", index=False)
    merged.to_csv(OUT_DIR / "network_mechanism_panel.csv", index=False)
    perturb.to_csv(OUT_DIR / "network_topology_perturbations.csv", index=False)
    perturb_summary_df.to_csv(OUT_DIR / "network_topology_perturbation_summary.csv", index=False)
    plot_mechanisms(
        merged,
        corr,
        FIG_DIR / "fig_network_mechanisms.png",
        FIG_DIR / "fig_network_mechanisms.pdf",
    )
    plot_perturbations(
        perturb_summary_df,
        FIG_DIR / "fig_network_perturbations.png",
        FIG_DIR / "fig_network_perturbations.pdf",
    )
    print({
        "metrics": str(OUT_DIR / "network_structure_metrics.csv"),
        "correlations": str(OUT_DIR / "network_mechanism_correlations.csv"),
        "perturbations": str(OUT_DIR / "network_topology_perturbation_summary.csv"),
        "figure": str(FIG_DIR / "fig_network_mechanisms.pdf"),
    })


if __name__ == "__main__":
    main()
