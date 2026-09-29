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
from natcs_design_contract import lagged_network_exposure  # noqa: E402


OUT_ROOT = ROOT / "output" / "natcs_empirical_cp"
EPS = 1e-12


def spectral_condition_number(min_eig, max_eig, rank=None, dimension=None, tolerance=EPS):
    if not np.isfinite(min_eig) or not np.isfinite(max_eig):
        return float("nan")
    if rank is not None and dimension is not None and rank < dimension:
        return float("inf")
    if min_eig <= tolerance:
        return float("inf")
    return float(max_eig / min_eig)


def residualized_network_stats(X_aug, Z):
    X_aug = np.asarray(X_aug, dtype=float)
    Z = np.asarray(Z, dtype=float)
    if X_aug.ndim != 2 or Z.ndim != 2 or X_aug.shape[0] != Z.shape[0]:
        raise ValueError("X_aug and Z must be row-aligned two-dimensional arrays")
    if X_aug.shape[0] < 1 or Z.shape[1] < 1:
        raise ValueError("weak-separation diagnostics require at least one row and one network column")
    coef, *_ = np.linalg.lstsq(X_aug, Z, rcond=None)
    Z_perp = Z - X_aug @ coef
    gram = (Z_perp.T @ Z_perp) / Z_perp.shape[0]
    eig = np.linalg.eigvalsh((gram + gram.T) / 2.0)
    eig = np.maximum(eig, 0.0)
    min_eig = float(np.min(eig))
    max_eig = float(np.max(eig))
    # Rank, condition and the degenerate-design flag must use the same
    # residualized-Gram scale. Scaling by the unprojected Z can otherwise mark
    # a well-separated residual direction as rank deficient.
    residualized_rank = int(np.count_nonzero(eig > EPS))
    condition = spectral_condition_number(
        min_eig,
        max_eig,
        rank=residualized_rank,
        dimension=Z_perp.shape[1],
        tolerance=EPS,
    )
    return {
        "Z_perp": Z_perp,
        "min_eig": min_eig,
        "max_eig": max_eig,
        "rank": residualized_rank,
        "condition": condition,
        "weak_flag": int(min_eig <= 1e-8 or residualized_rank < Z_perp.shape[1]),
    }


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
                  Wy = lagged_network_exposure(W_list, Y, tau, lag)
                  z_vals.append(float(Wy[unit_idx]))
              z_cols.append(z_vals)
          X = np.asarray(x_cols, dtype=float)
          Z = np.asarray(z_cols, dtype=float)
          if X.shape[0] == 0 or Z.shape[0] == 0:
              continue
          X_aug = np.column_stack([np.ones(X.shape[0]), X])
          stats = residualized_network_stats(X_aug, Z)
          Z_perp = stats["Z_perp"]
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
                  "residualized_network_rank": stats["rank"],
                  "residualized_min_eigenvalue": stats["min_eig"],
                  "residualized_max_eigenvalue": stats["max_eig"],
                  "residualized_condition_number": stats["condition"],
                  "weak_separation_flag": stats["weak_flag"],
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
    from run_cp_empirical_pipeline import build_w_list, load_dataset

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
