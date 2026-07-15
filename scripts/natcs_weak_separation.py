import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp" / "matplotlib_cache"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "tmp" / "xdg_cache"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)

import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT / "scripts"))
from run_cp_empirical_pipeline import (  # noqa: E402
    build_w_list,
    load_dataset,
    safe_row_normalize,
)


OUT_ROOT = ROOT / "output" / "natcs_empirical_cp"
EPS = 1e-12


def output_dir(dataset):
    out = OUT_ROOT / dataset
    out.mkdir(parents=True, exist_ok=True)
    return out


def effective_window(y_len, requested_window, p):
    return requested_window if y_len > requested_window + 8 else max(p + 8, y_len - 8)


def weak_separation_rows(Y, W_list, dates, unit_names, p, window, dataset):
    rows = []
    T, N = Y.shape
    for t in range(window, T):
      date = pd.Timestamp(dates[t])
      for unit_idx, unit in enumerate(unit_names):
          x_cols = []
          z_cols = []
          for tau in range(t - window + p, t):
              x_cols.append([Y[tau - lag, unit_idx] for lag in range(1, p + 1)])
              z_vals = []
              for lag in range(1, p + 1):
                  W = safe_row_normalize(np.asarray(W_list[tau - lag], dtype=float))
                  z_vals.append(float((W @ Y[tau - lag])[unit_idx]))
              z_cols.append(z_vals)
          X = np.asarray(x_cols, dtype=float)
          Z = np.asarray(z_cols, dtype=float)
          if X.shape[0] == 0 or Z.shape[0] == 0:
              continue
          X_aug = np.column_stack([np.ones(X.shape[0]), X])
          coef, *_ = np.linalg.lstsq(X_aug, Z, rcond=None)
          Z_perp = Z - X_aug @ coef
          gram = (Z_perp.T @ Z_perp) / max(Z_perp.shape[0], 1)
          eig = np.linalg.eigvalsh((gram + gram.T) / 2.0)
          eig = np.maximum(eig, 0.0)
          min_eig = float(np.min(eig)) if len(eig) else float("nan")
          max_eig = float(np.max(eig)) if len(eig) else float("nan")
          condition = float(max_eig / max(min_eig, EPS)) if np.isfinite(max_eig) else float("nan")
          rows.append(
              {
                  "dataset": dataset,
                  "date": date,
                  "unit": unit,
                  "window": int(window),
                  "lag_order": int(p),
                  "n_window_rows": int(Z_perp.shape[0]),
                  "network_lag_dimension": int(Z_perp.shape[1]),
                  "direct_design_rank": int(np.linalg.matrix_rank(X_aug)),
                  "residualized_network_rank": int(np.linalg.matrix_rank(Z_perp, tol=1e-10)),
                  "residualized_min_eigenvalue": min_eig,
                  "residualized_max_eigenvalue": max_eig,
                  "residualized_condition_number": condition,
                  "weak_separation_flag": int(min_eig <= 1e-8),
              }
          )
    return rows


def summarize(df):
    numeric = df.copy()
    rows = []
    for dataset, grp in numeric.groupby("dataset"):
        min_eigs = pd.to_numeric(grp["residualized_min_eigenvalue"], errors="coerce")
        conds = pd.to_numeric(grp["residualized_condition_number"], errors="coerce")
        rows.append(
            {
                "dataset": dataset,
                "n_windows_units": int(len(grp)),
                "window": int(grp["window"].iloc[0]),
                "lag_order": int(grp["lag_order"].iloc[0]),
                "median_min_eigenvalue": float(min_eigs.median()),
                "p10_min_eigenvalue": float(min_eigs.quantile(0.10)),
                "p01_min_eigenvalue": float(min_eigs.quantile(0.01)),
                "min_min_eigenvalue": float(min_eigs.min()),
                "median_condition_number": float(conds.replace([np.inf, -np.inf], np.nan).median()),
                "p90_condition_number": float(conds.replace([np.inf, -np.inf], np.nan).quantile(0.90)),
                "weak_separation_flag_pct": float(100 * grp["weak_separation_flag"].mean()),
            }
        )
    return pd.DataFrame(rows)


def run(datasets, window, p):
    all_rows = []
    for name in datasets:
        data = load_dataset(name)
        Y = data["Y"]
        dates = data["dates"]
        if name == "rcep":
            W_list = build_w_list(
                data["df_bilateral"],
                dates,
                window_quarters=data["w_window_quarters"],
                mode=data["w_mode"],
            )
        else:
            W_list = data["w_list"]
        w_eff = effective_window(len(Y), window, p)
        rows = weak_separation_rows(Y, W_list, dates, data["unit_names"], p, w_eff, name)
        df = pd.DataFrame(rows)
        out = output_dir(name)
        df.to_csv(out / "weak_separation_diagnostics.csv", index=False)
        all_rows.extend(rows)
    summary = summarize(pd.DataFrame(all_rows))
    summary.to_csv(OUT_ROOT / "weak_separation_summary.csv", index=False)
    return summary


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["rcep", "nyc_taxi", "all"], default="all")
    parser.add_argument("--window", type=int, default=40)
    parser.add_argument("--p", type=int, default=2)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    datasets = ["rcep", "nyc_taxi"] if args.dataset == "all" else [args.dataset]
    print(run(datasets, args.window, args.p).to_string(index=False))
