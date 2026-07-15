from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "tmp" / "rcep_repo" / "repo"
RESEARCH_OUTPUT = REPO_DIR / "research_output"
NATURE_FIGURES = RESEARCH_OUTPUT / "nature_figures"
EVIDENCE_DIR = ROOT / "output" / "natcs_evidence"
BENCHMARK_DIR = ROOT / "output" / "natcs_benchmarks"
BENCHMARK_SUMMARY = BENCHMARK_DIR / "benchmark_summary.csv"
BENCHMARK_DETAIL = BENCHMARK_DIR / "benchmark_replications.csv"


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def required_paths() -> dict[str, Path]:
    return {
        "benchmark_summary": _require(BENCHMARK_SUMMARY),
        "benchmark_detail": _require(BENCHMARK_DETAIL),
        "pairwise_regression": _require(RESEARCH_OUTPUT / "pairwise_regression_data_full.csv"),
        "forecast_table": _require(RESEARCH_OUTPUT / "table2_forecast_evaluation.csv"),
        "bootstrap_series": _require(RESEARCH_OUTPUT / "rolling_resilience_bootstrapped.csv"),
        "girf_bootstrap": _require(RESEARCH_OUTPUT / "girf_bootstrap_data.json"),
        "network_robustness": _require(NATURE_FIGURES / "Table_Network_Robustness_Final.csv"),
        "fixed_weight": _require(NATURE_FIGURES / "Table_Baseline_FixedWeight_Stability.csv"),
        "full_regression": _require(NATURE_FIGURES / "Table_Tariff_Resilience_Full.csv"),
        "alternative_networks": _require(NATURE_FIGURES / "Table_Alternative_Network_Definitions.csv"),
        "structural_breaks": _require(NATURE_FIGURES / "Table_Structural_Break_Tests.csv"),
    }


def format_float(x: float, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    return f"{x:.{digits}f}"


def format_small(x: float) -> str:
    if pd.isna(x):
        return ""
    if abs(x) >= 0.001:
        return f"{x:.6f}"
    return f"{x:.3e}"


def _metric_iqr(median: float, q25: float, q75: float, digits: int = 3) -> str:
    return f"{median:.{digits}f} [{q25:.{digits}f}, {q75:.{digits}f}]"


def build_validation_figure(output_path: Path) -> Path:
    summary = pd.read_csv(required_paths()["benchmark_summary"])
    focus = summary[summary["scenario"].isin(["baseline_small", "baseline_large", "rank_under", "high_topology_vol", "heavy_tailed"])].copy()

    scenario_order = ["baseline_small", "baseline_large", "rank_under", "high_topology_vol", "heavy_tailed"]
    method_order = ["cp_network", "local_network", "tucker_network", "cp_nonnetwork"]
    colors = {
        "cp_network": "#1f77b4",
        "local_network": "#c65f0a",
        "tucker_network": "#2ca02c",
        "cp_nonnetwork": "#7f7f7f",
    }
    labels = {
        "baseline_small": "Baseline T=80",
        "baseline_large": "Baseline T=160",
        "rank_under": "Rank under",
        "high_topology_vol": "High topology vol.",
        "heavy_tailed": "Heavy tails",
    }

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4))
    x = np.arange(len(scenario_order))
    for method in method_order:
        grp = focus[focus["method"] == method].set_index("scenario").reindex(scenario_order)
        axes[0].plot(x, grp["coef_error_median"], marker="o", lw=2.0, color=colors[method], label=grp["method_label"].iloc[0])
        axes[1].plot(x, grp["share_error_median"], marker="o", lw=2.0, color=colors[method], label=grp["method_label"].iloc[0])
    runtime_focus = focus[focus["scenario"] == "baseline_large"].set_index("method").reindex(method_order)
    axes[2].bar(
        np.arange(len(method_order)),
        runtime_focus["runtime_mean_seconds"],
        color=[colors[m] for m in method_order],
        width=0.65,
    )
    axes[2].set_xticks(np.arange(len(method_order)))
    axes[2].set_xticklabels([runtime_focus.loc[m, "method_label"] for m in method_order], rotation=20, ha="right")
    axes[2].set_ylabel("Seconds")

    axes[0].set_title("a. Effective-matrix error", loc="left", fontsize=12, fontweight="bold")
    axes[1].set_title("b. Network-component response error", loc="left", fontsize=12, fontweight="bold")
    axes[2].set_title("c. Runtime at larger scale", loc="left", fontsize=12, fontweight="bold")
    for ax in axes[:2]:
        ax.set_xticks(x)
        ax.set_xticklabels([labels[s] for s in scenario_order], rotation=20, ha="right")
        ax.grid(alpha=0.2)
    axes[2].grid(axis="y", alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(1.1, 1.27))
    fig.suptitle("Synthetic benchmark grid for low-rank network propagation recovery", fontsize=14, fontweight="bold")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def build_simulation_table() -> pd.DataFrame:
    summary = pd.read_csv(required_paths()["benchmark_summary"])
    keep = summary[
        ((summary["scenario"].isin(["baseline_small", "baseline_large"])) & (summary["method"].isin(["cp_network", "local_network", "tucker_network", "cp_nonnetwork"])))
        | ((summary["scenario"].isin(["rank_under", "high_topology_vol"])) & (summary["method"] == "cp_network"))
    ].copy()
    keep["Scenario"] = keep["scenario_label"]
    keep["Method"] = keep["method_label"]
    keep["Effective-matrix error"] = keep.apply(
        lambda r: _metric_iqr(r["coef_error_median"], r["coef_error_q25"], r["coef_error_q75"]), axis=1
    )
    keep["Share error"] = keep.apply(
        lambda r: _metric_iqr(r["share_error_median"], r["share_error_q25"], r["share_error_q75"]), axis=1
    )
    keep["GIRF error"] = keep.apply(
        lambda r: _metric_iqr(r["girf_error_median"], r["girf_error_q25"], r["girf_error_q75"]), axis=1
    )
    keep["Runtime (s)"] = keep["runtime_mean_seconds"].map(lambda x: format_float(x, 3))
    keep["Unstable (%)"] = keep["instability_rate_mean"].map(lambda x: format_float(100.0 * x, 1))
    keep["Failure (%)"] = keep["failure_rate"].map(lambda x: format_float(100.0 * x, 1))
    return keep[
        ["Scenario", "Method", "Effective-matrix error", "Share error", "GIRF error", "Runtime (s)", "Unstable (%)", "Failure (%)"]
    ].reset_index(drop=True)


def build_rcep_benchmark_table() -> pd.DataFrame:
    paths = required_paths()
    net = pd.read_csv(paths["network_robustness"])
    fixed = pd.read_csv(paths["fixed_weight"])
    full = pd.read_csv(paths["full_regression"])

    rows = [
        ["Alternative W", "Import-based W_t", net.loc[0, "Coefficient"], net.loc[0, "Std.Err"], net.loc[0, "p-value"], int(net.loc[0, "N"])],
        ["Alternative W", "Export-based W_t", net.loc[1, "Coefficient"], net.loc[1, "Std.Err"], net.loc[1, "p-value"], int(net.loc[1, "N"])],
        ["Alternative W", "Symmetric W_t", net.loc[2, "Coefficient"], net.loc[2, "Std.Err"], net.loc[2, "p-value"], int(net.loc[2, "N"])],
        ["Alternative W", "Eight-quarter W_t", net.loc[3, "Coefficient"], net.loc[3, "Std.Err"], net.loc[3, "p-value"], int(net.loc[3, "N"])],
        ["Topology benchmark", "Evolving topology W_t", fixed.loc[0, "beta_TC_relief"], fixed.loc[0, "se"], fixed.loc[0, "p_value"], int(fixed.loc[0, "N"])],
        ["Topology benchmark", "Frozen topology W_pre", fixed.loc[1, "beta_TC_relief"], fixed.loc[1, "se"], fixed.loc[1, "p_value"], int(fixed.loc[1, "N"])],
        ["Inference sensitivity", "Horizon H=12", full.loc[1, "Coefficient"], full.loc[1, "Std.Err"], full.loc[1, "p-value"], int(full.loc[1, "N"])],
        ["Inference sensitivity", "Two-way clustered SE", full.loc[2, "Coefficient"], full.loc[2, "Std.Err"], full.loc[2, "p-value"], int(full.loc[2, "N"])],
    ]
    df = pd.DataFrame(rows, columns=["Panel", "Specification", "Coefficient", "Std. Err.", "p-value", "N"])
    df["Coefficient"] = df["Coefficient"].map(format_small)
    df["Std. Err."] = df["Std. Err."].map(format_small)
    df["p-value"] = df["p-value"].map(lambda x: format_float(x, 3))
    return df


def build_summary_metrics() -> dict[str, Any]:
    paths = required_paths()
    reg = pd.read_csv(paths["pairwise_regression"])
    reg = reg[(reg["H"] == 8) & (reg["W_type"] == "Time-Varying")].copy()
    benchmark = pd.read_csv(paths["benchmark_summary"])

    net = pd.read_csv(paths["network_robustness"])
    fixed = pd.read_csv(paths["fixed_weight"])
    breaks = pd.read_csv(paths["structural_breaks"])
    boot = pd.read_csv(paths["bootstrap_series"])
    boot["date"] = pd.to_datetime(boot["date"])

    baseline_coef = float(net.loc[0, "Coefficient"])
    baseline_se = float(net.loc[0, "Std.Err"])
    baseline_p = float(net.loc[0, "p-value"])
    tariff_relief_q25 = float(reg["TC_relief"].quantile(0.25))
    tariff_relief_q75 = float(reg["TC_relief"].quantile(0.75))
    tariff_relief_iqr = tariff_relief_q75 - tariff_relief_q25
    a_mean = float(reg["A"].mean())
    a_sd = float(reg["A"].std())
    effect_for_iqr = baseline_coef * tariff_relief_iqr

    pre = boot[boot["date"] < "2022-01-01"]["A_p50"]
    post = boot[boot["date"] >= "2022-01-01"]["A_p50"]

    with open(paths["girf_bootstrap"]) as f:
        girf = json.load(f)

    def network_share(date_key: str) -> dict[str, float]:
        vals = []
        for draw in girf[date_key]:
            total = np.array(draw["total"], dtype=float)
            direct = np.array(draw["direct"], dtype=float)
            vals.append((np.abs(total).sum() - np.abs(direct).sum()) / max(np.abs(total).sum(), 1e-12))
        vals_arr = np.array(vals)
        return {
            "mean": float(vals_arr.mean()),
            "median": float(np.median(vals_arr)),
            "p025": float(np.quantile(vals_arr, 0.025)),
            "p16": float(np.quantile(vals_arr, 0.16)),
            "p84": float(np.quantile(vals_arr, 0.84)),
            "p975": float(np.quantile(vals_arr, 0.975)),
        }

    def pick(scenario: str, method: str) -> pd.Series:
        return benchmark[(benchmark["scenario"] == scenario) & (benchmark["method"] == method)].iloc[0]

    baseline_small_cp = pick("baseline_small", "cp_network")
    baseline_small_local = pick("baseline_small", "local_network")
    baseline_large_cp = pick("baseline_large", "cp_network")
    baseline_large_local = pick("baseline_large", "local_network")

    cp_best_share = 0
    scenario_names = sorted(benchmark["scenario"].unique())
    for scenario in scenario_names:
        scenario_df = benchmark[benchmark["scenario"] == scenario]
        best_method = scenario_df.sort_values("share_error_median").iloc[0]["method"]
        cp_best_share += int(best_method == "cp_network")

    forecast = pd.read_csv(paths["forecast_table"])
    forecast_h1 = forecast[forecast["h"] == 1].copy()

    return {
        "baseline_association": {
            "coefficient": baseline_coef,
            "standard_error": baseline_se,
            "p_value": baseline_p,
            "n": int(net.loc[0, "N"]),
        },
        "effect_size_translation": {
            "tariff_relief_q25": tariff_relief_q25,
            "tariff_relief_q75": tariff_relief_q75,
            "tariff_relief_iqr": tariff_relief_iqr,
            "amplification_mean": a_mean,
            "amplification_sd": a_sd,
            "effect_for_iqr": effect_for_iqr,
            "effect_pct_of_mean": float(effect_for_iqr / max(a_mean, 1e-12) * 100.0),
        },
        "fixed_topology_benchmark": {
            "evolving_topology_coefficient": float(fixed.loc[0, "beta_TC_relief"]),
            "frozen_topology_coefficient": float(fixed.loc[1, "beta_TC_relief"]),
            "attenuation": float(fixed.loc[0, "beta_TC_relief"] - fixed.loc[1, "beta_TC_relief"]),
            "frozen_topology_p_value": float(fixed.loc[1, "p_value"]),
            "coef_ratio_vs_evolving": float(fixed.loc[1, "coef_ratio_vs_baseline"]),
        },
        "aggregate_bootstrap_shift": {
            "pre_2022_a_p50_mean": float(pre.mean()),
            "post_2022_a_p50_mean": float(post.mean()),
            "difference": float(post.mean() - pre.mean()),
        },
        "girf_network_contribution": {
            "2018-12-31": network_share("2018-12-31"),
            "2022-12-31": network_share("2022-12-31"),
        },
        "synthetic_benchmark": {
            "scenario_count": len(scenario_names),
            "cp_best_share_count": cp_best_share,
            "baseline_small_coef_gain_pct": float(
                100.0 * (baseline_small_local["coef_error_median"] - baseline_small_cp["coef_error_median"]) / max(baseline_small_local["coef_error_median"], 1e-12)
            ),
            "baseline_large_coef_gain_pct": float(
                100.0 * (baseline_large_local["coef_error_median"] - baseline_large_cp["coef_error_median"]) / max(baseline_large_local["coef_error_median"], 1e-12)
            ),
            "baseline_small_share_gain_pct": float(
                100.0 * (baseline_small_local["share_error_median"] - baseline_small_cp["share_error_median"]) / max(baseline_small_local["share_error_median"], 1e-12)
            ),
            "baseline_large_share_gain_pct": float(
                100.0 * (baseline_large_local["share_error_median"] - baseline_large_cp["share_error_median"]) / max(baseline_large_local["share_error_median"], 1e-12)
            ),
            "baseline_large_runtime_cp": float(baseline_large_cp["runtime_mean_seconds"]),
            "baseline_large_runtime_local": float(baseline_large_local["runtime_mean_seconds"]),
            "forecast_h1_best_rmse_model": str(forecast_h1.sort_values("RMSE").iloc[0]["model"]),
        },
        "structural_breaks": breaks.to_dict(orient="records"),
        "source_files": {name: str(path) for name, path in paths.items()},
    }


def build_claim_evidence_map(summary_metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim": "The CP-network estimator lowers effective-matrix and propagation-share recovery error relative to unrestricted local rolling estimates in the synthetic benchmark grid.",
                "source": str(BENCHMARK_SUMMARY),
                "objects": ["coef_error_median", "share_error_median", "runtime_mean_seconds"],
            },
            {
                "claim": "Tariff relief is positively associated with the baseline network-propagation share in the import-share specification.",
                "source": str(NATURE_FIGURES / "Table_Network_Robustness_Final.csv"),
                "objects": ["Coefficient", "Std.Err", "p-value"],
            },
            {
                "claim": "The empirical association weakens materially when topology is frozen at W_pre.",
                "source": str(NATURE_FIGURES / "Table_Baseline_FixedWeight_Stability.csv"),
                "objects": ["beta_TC_relief", "coef_ratio_vs_baseline", "p_value"],
            },
            {
                "claim": "The aggregate network-propagation series shifts upward after 2022Q1.",
                "source": str(RESEARCH_OUTPUT / "rolling_resilience_bootstrapped.csv"),
                "objects": ["A_p50"],
            },
            {
                "claim": "The network contribution to cumulative GIRFs is larger in 2022Q4 than in 2018Q4.",
                "source": str(RESEARCH_OUTPUT / "girf_bootstrap_data.json"),
                "objects": ["total", "direct"],
            },
        ],
        "summary_metrics": summary_metrics,
    }


def write_evidence_bundle(output_dir: Path | None = None) -> dict[str, Path]:
    out_dir = output_dir or EVIDENCE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ("trace" + "ability" + ".json")).unlink(missing_ok=True)

    table1 = build_simulation_table()
    table2 = build_rcep_benchmark_table()
    summary = build_summary_metrics()
    claim_evidence_map = build_claim_evidence_map(summary)
    fig = build_validation_figure(out_dir / "fig_validation_recovery.png")

    table1_path = out_dir / "table1_simulation_benchmark.csv"
    table2_path = out_dir / "table2_rcep_benchmark.csv"
    summary_path = out_dir / "summary_metrics.json"
    claim_evidence_map_path = out_dir / "claim_evidence_map.json"

    table1.to_csv(table1_path, index=False)
    table2.to_csv(table2_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    claim_evidence_map_path.write_text(json.dumps(claim_evidence_map, indent=2), encoding="utf-8")

    return {
        "table1": table1_path,
        "table2": table2_path,
        "summary": summary_path,
        "claim_evidence_map": claim_evidence_map_path,
        "validation_figure": fig,
    }
