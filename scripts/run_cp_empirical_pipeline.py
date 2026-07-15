import argparse
import json
import logging
import math
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
from linearmodels.iv.absorbing import AbsorbingLS
from linearmodels.panel import PanelOLS

helper_repo = os.environ.get("NATCS_RCEP_HELPER_REPO")
if not helper_repo:
    raise RuntimeError(
        "A raw-to-derived RCEP rebuild requires NATCS_RCEP_HELPER_REPO to point to the authorized helper checkout."
    )
sys.path.insert(0, str(Path(helper_repo).expanduser().resolve()))

from research_data_construction import (  # noqa: E402
    RCEP_LIST,
    build_tariff_relief_tc,
    build_trade_network_w,
    chow_lin_quarterly_vax,
    load_quarterly_macro_and_bilateral,
    quality_control_missing,
    quality_control_outliers,
)
from research_network_tvp_var import (  # noqa: E402
    girf_one,
    moving_average_coefficients,
    var_ols,
)

EPS = 1e-10


def build_trade_network_w(df_bilateral, date_val, window_quarters=4, use_import_share=True, mode="import"):
    """Local compatibility wrapper for pandas/numpy read-only pivot arrays."""
    df = df_bilateral[
        (df_bilateral["date"] <= date_val)
        & (df_bilateral["date"] > (date_val - pd.DateOffset(months=3 * window_quarters)))
    ].copy()
    if df.empty:
        return pd.DataFrame(np.zeros((len(RCEP_LIST), len(RCEP_LIST))), index=RCEP_LIST, columns=RCEP_LIST)

    flow_col = "import_usd" if "import_usd" in df.columns else "export_usd"
    df["flow"] = pd.to_numeric(df[flow_col], errors="coerce").fillna(0)

    if mode == "export":
        if "export_usd" in df.columns:
            df["flow"] = pd.to_numeric(df["export_usd"], errors="coerce").fillna(0)
        agg = df.groupby(["reporter_iso", "partner_iso"])["flow"].sum().reset_index()
        total_j = agg.groupby("partner_iso")["flow"].sum().reset_index().rename(columns={"flow": "total"})
        agg = agg.merge(total_j, on="partner_iso")
        agg["w"] = agg["flow"] / agg["total"].replace(0, np.nan)
        W = agg.pivot_table(index="reporter_iso", columns="partner_iso", values="w", fill_value=0)
    elif mode == "symmetric":
        df["pair"] = df.apply(lambda x: tuple(sorted([x["reporter_iso"], x["partner_iso"]])), axis=1)
        agg = df.groupby("pair")["flow"].sum().reset_index()
        pairs = []
        for pair, flow in zip(agg["pair"], agg["flow"]):
            pairs.append({"reporter_iso": pair[0], "partner_iso": pair[1], "flow": flow})
            pairs.append({"reporter_iso": pair[1], "partner_iso": pair[0], "flow": flow})
        agg = pd.DataFrame(pairs)
        total_i = agg.groupby("reporter_iso")["flow"].sum().reset_index().rename(columns={"flow": "total"})
        agg = agg.merge(total_i, on="reporter_iso")
        agg["w"] = agg["flow"] / agg["total"].replace(0, np.nan)
        W = agg.pivot_table(index="reporter_iso", columns="partner_iso", values="w", fill_value=0)
    else:
        agg = df.groupby(["reporter_iso", "partner_iso"])["flow"].sum().reset_index()
        total_i = agg.groupby("reporter_iso")["flow"].sum().reset_index().rename(columns={"flow": "total"})
        agg = agg.merge(total_i, on="reporter_iso")
        agg["w"] = agg["flow"] / agg["total"].replace(0, np.nan)
        W = agg.pivot_table(index="reporter_iso", columns="partner_iso", values="w", fill_value=0)

    W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0)
    values = W.to_numpy(dtype=float, copy=True)
    np.fill_diagonal(values, 0.0)
    W = pd.DataFrame(values, index=W.index, columns=W.columns)
    row_sums = W.sum(axis=1).replace(0, np.nan)
    return W.div(row_sums, axis=0).fillna(0)


def var_ols(Y, W_list, X_exog=None, p=2, lambda_ridge=1e-4):
    T, N = Y.shape
    if X_exog is None:
        X_exog = np.zeros((T, 0))
    K = X_exog.shape[1]

    A_list = [np.zeros((N, N)) for _ in range(p)]
    B_list = [np.zeros((N, N)) for _ in range(p)]
    c = np.zeros(N)
    Pi = np.zeros((N, K))
    residuals = np.zeros((T - p, N))

    for i in range(N):
        rows = []
        for tau in range(p, T):
            row = [1.0]
            for lag in range(1, p + 1):
                row.append(Y[tau - lag, i])
            for lag in range(1, p + 1):
                Wy = W_list[tau - lag] @ Y[tau - lag] if W_list[tau - lag] is not None else np.zeros(N)
                row.append(Wy[i])
            if K > 0:
                row.extend(X_exog[tau])
            rows.append(row)

        Z = np.asarray(rows, dtype=float)
        y = Y[p:, i]
        lhs = Z.T @ Z + float(lambda_ridge) * np.eye(Z.shape[1])
        rhs = Z.T @ y
        beta_i, _, _, _ = np.linalg.lstsq(lhs, rhs, rcond=None)

        c[i] = beta_i[0]
        for lag in range(p):
            A_list[lag][i, i] = beta_i[1 + lag]
            B_list[lag][i, i] = beta_i[1 + p + lag]
        if K > 0:
            Pi[i, :] = beta_i[1 + 2 * p:]
        residuals[:, i] = y - Z @ beta_i

    Sigma = (residuals.T @ residuals) / max(residuals.shape[0] - 1, 1)
    Sigma = (Sigma + Sigma.T) / 2 + 1e-8 * np.eye(N)
    return c, A_list, B_list, Pi, Sigma, residuals

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
EMPIRICAL_OUT_ROOT = ROOT / "output" / "natcs_empirical_cp"
NYC_TAXI_UPSTREAM_COMMIT = "7e63ba9734021171eaf49edb92be8a7e7e8802eb"

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def output_paths(dataset: str):
    out_dir = EMPIRICAL_OUT_ROOT / dataset
    fig_dir = out_dir / "figures"
    ensure_dir(out_dir)
    ensure_dir(fig_dir)
    return out_dir, fig_dir


def quarter_label(ts: pd.Timestamp) -> str:
    return f"{ts.year}Q{ts.quarter}"


def safe_row_normalize(W: np.ndarray) -> np.ndarray:
    W = np.asarray(W, dtype=float).copy()
    np.fill_diagonal(W, 0.0)
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums <= EPS] = 1.0
    return W / row_sums


def top_import_exposure_perturbation(W: np.ndarray, scale_factor: float = 0.5):
    W_base = safe_row_normalize(W)
    incoming = W_base.sum(axis=0)
    hub = int(np.argmax(incoming / max(incoming.sum(), EPS)))
    W_perturbed = W_base.copy()
    W_perturbed[:, hub] *= scale_factor
    return hub, safe_row_normalize(W_perturbed)


def load_rcep_panel_data():
    df_macro, df_bilateral = load_quarterly_macro_and_bilateral()
    df_tc = build_tariff_relief_tc(df_bilateral)

    vax = chow_lin_quarterly_vax(df_macro)
    vax_p = vax.set_index(["date", "iso3"])["vax_q"].unstack("iso3")
    for c in vax_p.columns:
        vax_p[c] = quality_control_outliers(quality_control_missing(vax_p[c]))
    Y = np.log(vax_p + 1e-6).diff().dropna(how="all")
    Y = Y.reindex(columns=RCEP_LIST).fillna(0.0)
    return {
        "dataset": "rcep",
        "Y": Y.values,
        "dates": list(pd.to_datetime(Y.index)),
        "df_bilateral": df_bilateral,
        "df_tc": df_tc,
        "unit_names": list(RCEP_LIST),
        "w_window_quarters": 4,
        "w_mode": "import",
        "primary_label": "Time-Varying",
        "girf_pair": ("CHN", "JPN"),
        "requested_girf_dates": [pd.Timestamp("2018-12-31"), pd.Timestamp("2022-12-31")],
    }


def _build_monthly_taxi_tensor():
    taxi_dataset_dir = os.environ.get("NATCS_NYC_TAXI_DATASET_DIR")
    if not taxi_dataset_dir:
        raise RuntimeError(
            "A raw-to-derived NYC Taxi rebuild requires NATCS_NYC_TAXI_DATASET_DIR to point to datasets/NYC-taxi."
        )
    taxi_root = Path(taxi_dataset_dir).expanduser().resolve()
    monthly_mats = []
    monthly_dates = []
    for year in range(2012, 2022):
        arr = np.load(taxi_root / f"yellow_taxi_trip_{year}.npz")["arr_0"]
        dates = pd.date_range(f"{year}-01-01", periods=arr.shape[2], freq="D")
        month_index = pd.PeriodIndex(dates, freq="M")
        for period in month_index.unique():
            idx = np.where(month_index == period)[0]
            monthly_mats.append(arr[:, :, idx].sum(axis=2))
            monthly_dates.append(period.to_timestamp("M"))
    return monthly_dates, monthly_mats


def load_nyc_taxi_data():
    monthly_dates, monthly_mats = _build_monthly_taxi_tensor()
    rolling_dates = []
    rolling_mats = []
    for idx in range(11, len(monthly_mats)):
        rolling_dates.append(monthly_dates[idx])
        rolling_mats.append(sum(monthly_mats[idx - j] for j in range(12)))

    total_volume = np.zeros(rolling_mats[0].shape[0], dtype=float)
    for mat in rolling_mats:
        total_volume += mat.sum(axis=1) + mat.sum(axis=0)
    top_idx = np.argsort(total_volume)[::-1][:15]
    unit_names = [f"Zone-{int(i) + 1}" for i in top_idx]
    level_rows = []
    w_list = []
    for mat in rolling_mats:
        sub = np.asarray(mat[np.ix_(top_idx, top_idx)], dtype=float)
        total_activity = sub.sum(axis=1) + sub.sum(axis=0)
        level_rows.append(np.log(total_activity + 1e-6))
        w_list.append(safe_row_normalize(sub))
    level = pd.DataFrame(level_rows, index=pd.to_datetime(rolling_dates), columns=unit_names)
    Y = level.copy().fillna(0.0)
    aligned_w = w_list
    aligned_dates = list(pd.to_datetime(Y.index))
    w_pre_dates = [i for i, d in enumerate(aligned_dates) if pd.Timestamp("2016-01-01") <= d <= pd.Timestamp("2019-12-31")]
    if not w_pre_dates:
        w_pre_dates = list(range(min(24, len(aligned_w))))
    W_pre = np.mean([aligned_w[i] for i in w_pre_dates], axis=0)
    return {
        "dataset": "nyc_taxi",
        "Y": Y.values,
        "dates": aligned_dates,
        "unit_names": unit_names,
        "w_list": aligned_w,
        "W_pre": safe_row_normalize(W_pre),
        "df_bilateral": None,
        "df_tc": None,
        "w_window_months": 12,
        "w_mode": "mobility",
        "primary_label": "Rolling 12-month mobility network",
        "girf_pair": (unit_names[0], unit_names[1]),
        "top_indices": [int(i) for i in top_idx],
        "level_panel": level.reset_index().rename(columns={"index": "date"}),
        "requested_girf_dates": [pd.Timestamp("2019-12-31"), pd.Timestamp("2021-12-31")],
        "acquisition_info": {
            "source_repository": "xinychen/vars",
            "commit": NYC_TAXI_UPSTREAM_COMMIT,
            "dataset_path": "datasets/NYC-taxi",
            "construction": "Monthly log trip activity for the 15 highest-flow mobility units with rolling 12-month OD trip-share network matrices.",
        },
    }


def load_dataset(name: str):
    if name == "rcep":
        return load_rcep_panel_data()
    if name == "nyc_taxi":
        return load_nyc_taxi_data()
    raise ValueError(f"Unsupported dataset: {name}")


def compute_w_pre(df_bilateral: pd.DataFrame) -> np.ndarray:
    pre_dates = pd.date_range("2016-01-01", "2019-12-31", freq="QS")
    mats = []
    for d in pre_dates:
        W = build_trade_network_w(df_bilateral, d, window_quarters=4, mode="import")
        if isinstance(W, pd.DataFrame):
            W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0).values
        mats.append(np.asarray(W, dtype=float))
    return np.mean(mats, axis=0)


def build_w_list(df_bilateral: pd.DataFrame, dates, window_quarters=4, mode="import"):
    mats = []
    for d in dates:
        W = build_trade_network_w(df_bilateral, d, window_quarters=window_quarters, mode=mode)
        if isinstance(W, pd.DataFrame):
            W = W.reindex(index=RCEP_LIST, columns=RCEP_LIST).fillna(0).values
        mats.append(np.asarray(W, dtype=float))
    return mats


def beta_matrix_from_lists(A_list, B_list):
    p = len(A_list)
    n = A_list[0].shape[0]
    beta = np.zeros((n, 2 * p))
    for l in range(p):
        beta[:, l] = np.diag(A_list[l])
        beta[:, p + l] = np.diag(B_list[l])
    return beta


def lists_from_beta(beta: np.ndarray, p: int):
    n = beta.shape[0]
    A_list = []
    B_list = []
    for l in range(p):
        A = np.zeros((n, n))
        B = np.zeros((n, n))
        np.fill_diagonal(A, beta[:, l])
        np.fill_diagonal(B, beta[:, p + l])
        A_list.append(A)
        B_list.append(B)
    return A_list, B_list


def predict_one_step(c, beta, y_hist, w_hist, p):
    A_list, B_list = lists_from_beta(beta, p)
    y_hat = np.asarray(c, dtype=float).copy()
    for l in range(1, p + 1):
        y_hat += A_list[l - 1] @ y_hist[-l]
        y_hat += B_list[l - 1] @ (w_hist[-l] @ y_hist[-l])
    return y_hat


def select_global_ridge_lambda(Y, W_list, dates, p=2, window=40, lambdas=None):
    if lambdas is None:
        lambdas = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
    cutoff = pd.Timestamp("2022-01-01")
    losses = {}
    for lam in lambdas:
        errs = []
        for t in range(window, len(Y)):
            if pd.Timestamp(dates[t]) >= cutoff:
                break
            Y_w = Y[t - window : t]
            W_w = W_list[t - window : t]
            c, A_list, B_list, _, _, _ = var_ols(Y_w, W_w, X_exog=None, p=p, lambda_ridge=lam)
            beta = beta_matrix_from_lists(A_list, B_list)
            y_hat = predict_one_step(c, beta, Y[:t], W_list[:t], p)
            errs.append(float(np.mean((Y[t] - y_hat) ** 2)))
        losses[str(lam)] = float(np.mean(errs)) if errs else float("inf")
    chosen = min(lambdas, key=lambda lam: (losses[str(lam)], lam))
    return chosen, losses


def unfold_tensor(X: np.ndarray, mode: int) -> np.ndarray:
    I, J, K = X.shape
    if mode == 0:
        return X.reshape(I, J * K)
    if mode == 1:
        return np.transpose(X, (1, 0, 2)).reshape(J, I * K)
    return np.transpose(X, (2, 0, 1)).reshape(K, I * J)


def khatri_rao(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    cols = A.shape[1]
    out = np.zeros((A.shape[0] * B.shape[0], cols))
    for r in range(cols):
        out[:, r] = np.kron(A[:, r], B[:, r])
    return out


def cp_reconstruct(factors):
    A, B, C = factors
    I, R = A.shape
    J = B.shape[0]
    K = C.shape[0]
    out = np.zeros((I, J, K))
    for r in range(R):
        out += np.einsum("i,j,k->ijk", A[:, r], B[:, r], C[:, r])
    return out


def cp_fit(tensor: np.ndarray, rank: int, n_init=6, max_iter=100, tol=1e-6, seed=20260328):
    rng = np.random.default_rng(seed)
    I, J, K = tensor.shape
    best = None
    best_loss = np.inf

    for init in range(n_init):
        A = rng.normal(scale=0.3, size=(I, rank))
        B = rng.normal(scale=0.3, size=(J, rank))
        C = rng.normal(scale=0.3, size=(K, rank))
        prev_loss = np.inf

        for _ in range(max_iter):
            gram_cb = (C.T @ C) * (B.T @ B) + 1e-6 * np.eye(rank)
            A = unfold_tensor(tensor, 0) @ khatri_rao(C, B) @ np.linalg.inv(gram_cb)

            gram_ca = (C.T @ C) * (A.T @ A) + 1e-6 * np.eye(rank)
            B = unfold_tensor(tensor, 1) @ khatri_rao(C, A) @ np.linalg.inv(gram_ca)

            gram_ba = (B.T @ B) * (A.T @ A) + 1e-6 * np.eye(rank)
            C = unfold_tensor(tensor, 2) @ khatri_rao(B, A) @ np.linalg.inv(gram_ba)

            for r in range(rank):
                norm_a = np.linalg.norm(A[:, r]) or 1.0
                norm_b = np.linalg.norm(B[:, r]) or 1.0
                A[:, r] /= norm_a
                B[:, r] /= norm_b
                C[:, r] *= norm_a * norm_b

            recon = cp_reconstruct((A, B, C))
            loss = float(np.linalg.norm(tensor - recon) / max(np.linalg.norm(tensor), EPS))
            if prev_loss < np.inf and abs(prev_loss - loss) / max(prev_loss, EPS) < tol:
                break
            prev_loss = loss

        if loss < best_loss:
            best_loss = loss
            best = (A.copy(), B.copy(), C.copy())

    return best, best_loss


def rolling_origin_one_step_loss_for_rank(beta_tensor, rank, rolling_dates, Y, W_list, window, p, min_training_slices):
    errs = []
    fit_losses = []
    last_recon = None
    for k, t in enumerate(rolling_dates):
        prefix_length = k + 1
        if prefix_length < min_training_slices:
            continue
        # Slice k is estimated from observations strictly before Y[t], so it is available at this origin.
        factors, fit_loss = cp_fit(beta_tensor[:, :, :prefix_length], rank)
        recon = cp_reconstruct(factors)
        beta = recon[:, :, -1]
        y_hat = predict_one_step(np.zeros(beta.shape[0]), beta, Y[:t], W_list[:t], p)
        errs.append(float(np.mean((Y[t] - y_hat) ** 2)))
        fit_losses.append(fit_loss)
        last_recon = recon
    return (
        float(np.mean(errs)) if errs else float("inf"),
        last_recon,
        float(np.mean(fit_losses)) if fit_losses else float("inf"),
        len(errs),
    )


def select_cp_rank(beta_tensor, rolling_dates, dates, Y, W_list, window, p=2, ranks=(1, 2, 3, 4)):
    cutoff = pd.Timestamp("2022-01-01")
    valid_idx = [idx for idx, t in enumerate(rolling_dates) if pd.Timestamp(dates[t]) < cutoff]
    valid_dates = [rolling_dates[idx] for idx in valid_idx]
    valid_tensor = beta_tensor[:, :, valid_idx]

    results = {}
    fit_losses = {}
    validation_origins = {}
    min_training_slices = max(ranks)
    for rank in ranks:
        pred_loss, _, fit_loss, n_origins = rolling_origin_one_step_loss_for_rank(
            valid_tensor,
            rank,
            valid_dates,
            Y,
            W_list,
            window,
            p,
            min_training_slices,
        )
        results[rank] = pred_loss
        fit_losses[rank] = fit_loss
        validation_origins[rank] = n_origins

    chosen = min(ranks, key=lambda r: (results[r], r))
    factors, full_fit_loss = cp_fit(beta_tensor, chosen)
    full_recon = cp_reconstruct(factors)
    validation_metadata = {
        "method": "rolling-origin one-step-ahead CP reconstruction",
        "cutoff": str(cutoff.date()),
        "available_origins": len(valid_dates),
        "minimum_training_slices": min_training_slices,
        "evaluated_origins_by_rank": validation_origins,
    }
    return chosen, results, fit_losses, full_recon, factors, full_fit_loss, validation_metadata


def effective_companion_radius(A_list, B_list, W_use) -> float:
    n = A_list[0].shape[0]
    p = len(A_list)
    top = np.hstack([A_list[l] + B_list[l] @ W_use for l in range(p)])
    if p == 1:
        companion = top
    else:
        lower = np.hstack([np.eye(n * (p - 1)), np.zeros((n * (p - 1), n))])
        companion = np.vstack([top, lower])
    vals = np.linalg.eigvals(companion)
    return float(np.max(np.abs(vals)))


def half_life_pair(irf_pair):
    vals = np.abs(np.asarray(irf_pair, dtype=float))
    peak = np.max(vals)
    if peak <= EPS:
        return 0.0
    for h, v in enumerate(vals):
        if v <= 0.5 * peak:
            return float(h)
    return float(len(vals) - 1)


def pair_metrics_from_blocks(A_list, B_list, Sigma, W_use, horizon, unit_names):
    n = Sigma.shape[0]
    B_zero = [np.zeros_like(B) for B in B_list]
    Psi_total = moving_average_coefficients(A_list, B_list, [W_use] * (horizon + len(A_list)), horizon, W_fixed=W_use)
    Psi_direct = moving_average_coefficients(A_list, B_zero, [W_use] * (horizon + len(A_list)), horizon, W_fixed=W_use)

    rows = []
    s_tot_sum = 0.0
    s_dir_sum = 0.0
    hl_vals = []
    for j in range(n):
        irf_tot = [girf_one(Psi_total[h], Sigma, j) for h in range(horizon + 1)]
        irf_dir = [girf_one(Psi_direct[h], Sigma, j) for h in range(horizon + 1)]
        for i in range(n):
            if i == j:
                continue
            s_tot = sum(abs(irf_tot[h][i]) for h in range(horizon + 1))
            s_dir = sum(abs(irf_dir[h][i]) for h in range(horizon + 1))
            s_raw = (s_tot - s_dir) / max(s_tot, EPS)
            rows.append(
                {
                    "reporter_iso": unit_names[i],
                    "partner_iso": unit_names[j],
                    "s_net_raw": s_raw,
                    "s_net_clip": float(np.clip(s_raw, 0.0, 1.0)),
                }
            )
            s_tot_sum += s_tot
            s_dir_sum += s_dir
            hl_vals.append(half_life_pair([irf_tot[h][i] for h in range(horizon + 1)]))

    g_net = (s_tot_sum - s_dir_sum) / max(s_tot_sum, EPS)
    half_life = float(np.mean(hl_vals)) if hl_vals else float("nan")
    return rows, g_net, half_life, Psi_total, Psi_direct


def estimate_rolling_local(Y, W_list, dates, p=2, window=40, lambda_ridge=1e-4):
    results = []
    tensor_blocks = []
    rolling_dates = []
    for t in range(window, len(Y)):
        Y_w = Y[t - window : t]
        W_w = W_list[t - window : t]
        c, A_list, B_list, _, Sigma, residuals = var_ols(Y_w, W_w, X_exog=None, p=p, lambda_ridge=lambda_ridge)
        beta = beta_matrix_from_lists(A_list, B_list)
        tensor_blocks.append(beta)
        rolling_dates.append(t)
        results.append(
            {
                "date": pd.Timestamp(dates[t]),
                "t_idx": t,
                "c": c,
                "A_list": A_list,
                "B_list": B_list,
                "Sigma": Sigma,
                "residuals": residuals,
                "Y_window": Y_w,
                "W_window": W_w,
                "beta": beta,
            }
        )
    beta_tensor = np.stack(tensor_blocks, axis=2)
    return results, beta_tensor, rolling_dates


def cp_empirical_paths(local_results, beta_recon, p=2):
    out = []
    for k, base in enumerate(local_results):
        beta = beta_recon[:, :, k]
        A_list, B_list = lists_from_beta(beta, p)
        W_use = safe_row_normalize(np.asarray(base["W_window"][-1], dtype=float))
        row = dict(base)
        row["beta_cp"] = beta
        row["A_list_cp"] = A_list
        row["B_list_cp"] = B_list
        row["radius_cp"] = effective_companion_radius(A_list, B_list, W_use)
        out.append(row)
    return out


def resolve_target_dates(cp_results, requested_dates):
    available_dates = [pd.Timestamp(item["date"]) for item in cp_results]
    stable_dates = [pd.Timestamp(item["date"]) for item in cp_results if float(item["radius_cp"]) < 1.0]
    search_space = stable_dates or available_dates
    resolved = {}
    for requested in requested_dates:
        target = pd.Timestamp(requested)
        if target in search_space:
            chosen = target
        else:
            chosen = min(search_space, key=lambda x: abs((x - target).days))
        resolved[pd.Timestamp(chosen)] = str(target.date())
    return resolved


def build_pair_panel(cp_results, df_tc, horizon, W_mode, w_label, unit_names, girf_pair, target_dates, W_fixed=None):
    rows = []
    aggregate_rows = []
    girf_store = {}
    receiver_idx = unit_names.index(girf_pair[0])
    shock_idx = unit_names.index(girf_pair[1])
    for item in cp_results:
        W_use = safe_row_normalize(np.asarray(W_fixed if W_fixed is not None else item["W_window"][-1], dtype=float))
        pair_rows, g_net, hl, Psi_total, Psi_direct = pair_metrics_from_blocks(item["A_list_cp"], item["B_list_cp"], item["Sigma"], W_use, horizon, unit_names)
        date = item["date"]
        for row in pair_rows:
            row.update({"date": date, "H": horizon, "W_type": w_label})
            rows.append(row)
        aggregate_rows.append({"date": date, "H": horizon, "W_type": w_label, "g_net": g_net, "half_life": hl})
        if date in target_dates:
            total = [float(girf_one(Psi_total[h], item["Sigma"], shock_idx)[receiver_idx]) for h in range(horizon + 1)]
            direct = [float(girf_one(Psi_direct[h], item["Sigma"], shock_idx)[receiver_idx]) for h in range(horizon + 1)]
            girf_store[target_dates[date]] = {"total": total, "direct": direct, "network": [t - d for t, d in zip(total, direct)]}

    df_rows = pd.DataFrame(rows)
    df_rows["date"] = pd.to_datetime(df_rows["date"])
    df_all = df_rows.copy()
    if df_tc is not None:
        df_tc = df_tc.copy()
        df_tc["date"] = pd.to_datetime(df_tc["date"])
        df_all = df_rows.merge(df_tc, on=["date", "reporter_iso", "partner_iso"], how="left")
        df_all["TC_relief"] = pd.to_numeric(df_all.get("TC", 0), errors="coerce").fillna(0).abs() * 100
    else:
        df_all["TC_relief"] = 0.0
    df_all["qtr"] = df_all["date"].map(quarter_label)
    df_all["pair"] = df_all["reporter_iso"] + "_" + df_all["partner_iso"]
    df_all["origin_time"] = df_all["reporter_iso"] + "_" + df_all["qtr"]
    df_all["dest_time"] = df_all["partner_iso"] + "_" + df_all["qtr"]
    return df_all, pd.DataFrame(aggregate_rows), girf_store


def fit_panel(df, dep="s_net_clip", cluster="pair", fe="pair_time"):
    df = df.dropna(subset=[dep, "TC_relief"]).copy()
    if fe == "pair_time":
        df_reg = df.set_index(["pair", "date"])
        mod = PanelOLS.from_formula(f"{dep} ~ TC_relief + EntityEffects + TimeEffects", data=df_reg)
        if cluster == "pair":
            res = mod.fit(cov_type="clustered", cluster_entity=True)
        elif cluster == "origin_dest":
            clusters = df_reg.loc[mod.dependent.index, ["reporter_iso", "partner_iso"]]
            res = mod.fit(cov_type="clustered", clusters=clusters)
        else:
            res = mod.fit(cov_type="robust")
    else:
        absorb_df = df[["origin_time", "dest_time"]].copy()
        absorb_df["origin_time"] = absorb_df["origin_time"].astype("category")
        absorb_df["dest_time"] = absorb_df["dest_time"].astype("category")
        mod = AbsorbingLS(df[dep], df[["TC_relief"]], absorb=absorb_df)
        clusters = df["pair"] if cluster == "pair" else None
        res = mod.fit(cov_type="clustered", clusters=clusters)
    return {
        "Coefficient": float(res.params["TC_relief"]),
        "Std.Err": float(res.std_errors["TC_relief"]),
        "p-value": float(res.pvalues["TC_relief"]),
        "N": int(res.nobs),
    }


def block_bootstrap_residuals(residuals, rng, block_size=4):
    n = residuals.shape[0]
    idx = []
    while len(idx) < n:
        start = int(rng.integers(0, max(n - block_size + 1, 1)))
        idx.extend(range(start, min(start + block_size, n)))
    return residuals[np.array(idx[:n])]


def bootstrap_cp_pipeline(local_results, rank, lambda_ridge, df_tc, unit_names, girf_pair, target_dates, n_boot=500, block_size=4, p=2, W_pre=None):
    rng = np.random.default_rng(20260328)
    boot_series = []
    girf_store = {label: [] for label in target_dates.values()}
    coef_draws = []

    for b in range(n_boot):
        tensor_blocks = []
        cp_local = []
        for item in local_results:
            Y_w = item["Y_window"]
            W_w = item["W_window"]
            u_star = block_bootstrap_residuals(item["residuals"], rng, block_size=block_size)
            Y_star = np.zeros_like(Y_w)
            Y_star[:p] = Y_w[:p]
            for s in range(p, len(Y_w)):
                beta_prev = item["beta"]
                y_hat = predict_one_step(item["c"], beta_prev, Y_star[:s], W_w[:s], p)
                Y_star[s] = y_hat + u_star[s - p]
            c_b, A_b, B_b, _, Sigma_b, residuals_b = var_ols(Y_star, W_w, X_exog=None, p=p, lambda_ridge=lambda_ridge)
            beta_b = beta_matrix_from_lists(A_b, B_b)
            tensor_blocks.append(beta_b)
            cp_local.append({**item, "c": c_b, "Sigma": Sigma_b, "residuals": residuals_b, "beta": beta_b, "Y_window": Y_star})

        tensor = np.stack(tensor_blocks, axis=2)
        factors, _ = cp_fit(tensor, rank, n_init=4, max_iter=80, tol=1e-5, seed=20260328 + b)
        recon = cp_reconstruct(factors)
        cp_results = cp_empirical_paths(cp_local, recon, p=p)
        df_pair, df_agg, girf = build_pair_panel(cp_results, df_tc, horizon=8, W_mode="import", w_label="Time-Varying", unit_names=unit_names, girf_pair=girf_pair, target_dates=target_dates, W_fixed=None)
        df_fix, df_agg_fix, _ = build_pair_panel(cp_results, df_tc, horizon=8, W_mode="import", w_label="Fixed-Pre", unit_names=unit_names, girf_pair=girf_pair, target_dates=target_dates, W_fixed=W_pre)
        if df_tc is not None:
            reg_evolving = fit_panel(df_pair, dep="s_net_clip", cluster="pair", fe="pair_time")
            reg_frozen = fit_panel(df_fix, dep="s_net_clip", cluster="pair", fe="pair_time")
            evolving = reg_evolving["Coefficient"]
            frozen = reg_frozen["Coefficient"]
            coef_draws.append(
                {
                    "draw": b + 1,
                    "evolving_coefficient": evolving,
                    "frozen_coefficient": frozen,
                    "attenuation_difference": evolving - frozen,
                    "frozen_evolving_ratio": frozen / max(evolving, EPS),
                }
            )
        for (_, row_tv), (_, row_fix) in zip(df_agg.iterrows(), df_agg_fix.iterrows()):
            boot_series.append(
                {
                    "b": b + 1,
                    "date": row_tv["date"],
                    "g_net": row_tv["g_net"],
                    "half_life": row_tv["half_life"],
                    "g_net_fixed": row_fix["g_net"],
                    "half_life_fixed": row_fix["half_life"],
                    "g_net_diff": row_tv["g_net"] - row_fix["g_net"],
                }
            )
        for key in girf_store:
            if key in girf:
                girf_store[key].append(girf[key])

    boot_df = pd.DataFrame(boot_series)
    agg_rows = []
    for date, grp in boot_df.groupby("date"):
        agg_rows.append(
            {
                "date": pd.Timestamp(date),
                "g_net_mean": float(grp["g_net"].mean()),
                "g_net_p025": float(grp["g_net"].quantile(0.025)),
                "g_net_p16": float(grp["g_net"].quantile(0.16)),
                "g_net_p50": float(grp["g_net"].quantile(0.5)),
                "g_net_p84": float(grp["g_net"].quantile(0.84)),
                "g_net_p975": float(grp["g_net"].quantile(0.975)),
                "g_net_fixed_mean": float(grp["g_net_fixed"].mean()),
                "g_net_fixed_p025": float(grp["g_net_fixed"].quantile(0.025)),
                "g_net_fixed_p16": float(grp["g_net_fixed"].quantile(0.16)),
                "g_net_fixed_p50": float(grp["g_net_fixed"].quantile(0.5)),
                "g_net_fixed_p84": float(grp["g_net_fixed"].quantile(0.84)),
                "g_net_fixed_p975": float(grp["g_net_fixed"].quantile(0.975)),
                "g_net_diff_mean": float(grp["g_net_diff"].mean()),
                "g_net_diff_p025": float(grp["g_net_diff"].quantile(0.025)),
                "g_net_diff_p16": float(grp["g_net_diff"].quantile(0.16)),
                "g_net_diff_p50": float(grp["g_net_diff"].quantile(0.5)),
                "g_net_diff_p84": float(grp["g_net_diff"].quantile(0.84)),
                "g_net_diff_p975": float(grp["g_net_diff"].quantile(0.975)),
                "hl_mean": float(grp["half_life"].mean()),
                "hl_p025": float(grp["half_life"].quantile(0.025)),
                "hl_p16": float(grp["half_life"].quantile(0.16)),
                "hl_p50": float(grp["half_life"].quantile(0.5)),
                "hl_p84": float(grp["half_life"].quantile(0.84)),
                "hl_p975": float(grp["half_life"].quantile(0.975)),
            }
        )
    coef_summary = None
    if coef_draws:
        coef_draw_df = pd.DataFrame(coef_draws)

        def summarize_quantity(name: str) -> dict[str, float | str]:
            vals = coef_draw_df[name].dropna().astype(float)
            return {
                "quantity": name,
                "mean": float(vals.mean()),
                "p025": float(vals.quantile(0.025)),
                "p16": float(vals.quantile(0.16)),
                "p50": float(vals.quantile(0.5)),
                "p84": float(vals.quantile(0.84)),
                "p975": float(vals.quantile(0.975)),
            }

        coef_summary = {
            "bootstrap_type": "moving-block residual bootstrap with CP re-estimation",
            "bootstrap_replications": int(n_boot),
            "block_size": int(block_size),
            "quantities": {
                "evolving_coefficient": summarize_quantity("evolving_coefficient"),
                "frozen_coefficient": summarize_quantity("frozen_coefficient"),
                "attenuation_difference": summarize_quantity("attenuation_difference"),
                "frozen_evolving_ratio": summarize_quantity("frozen_evolving_ratio"),
            },
        }
    return pd.DataFrame(agg_rows), girf_store, coef_summary, pd.DataFrame(coef_draws)


def bootstrap_block_sensitivity(local_results, rank, lambda_ridge, df_tc, unit_names, girf_pair, target_dates, p, W_pre, block_sizes=(4, 8, 12), n_boot=120):
    rows = []
    for block_size in block_sizes:
        boot_df, _, coef_summary, _ = bootstrap_cp_pipeline(
            local_results,
            rank,
            lambda_ridge,
            df_tc,
            unit_names,
            girf_pair,
            target_dates,
            n_boot=n_boot,
            block_size=block_size,
            p=p,
            W_pre=W_pre,
        )
        coef_quantities = (coef_summary or {}).get("quantities", {})
        evolving = coef_quantities.get("evolving_coefficient", {})
        rows.append(
            {
                "block_size": block_size,
                "g_net_diff_p50_mean": float(boot_df["g_net_diff_p50"].mean()),
                "g_net_diff_p025_mean": float(boot_df["g_net_diff_p025"].mean()),
                "g_net_diff_p975_mean": float(boot_df["g_net_diff_p975"].mean()),
                "coef_p50": None if not evolving else float(evolving["p50"]),
                "coef_p025": None if not evolving else float(evolving["p025"]),
                "coef_p975": None if not evolving else float(evolving["p975"]),
                "bootstrap_replications": int(n_boot),
            }
        )
    return pd.DataFrame(rows)


def _rss_segment(y, start, end):
    seg = y[start:end]
    if len(seg) <= 1:
        return 0.0
    mu = float(np.mean(seg))
    return float(np.sum((seg - mu) ** 2))


def _chow_f_stat(y, cut):
    n = len(y)
    if cut <= 1 or cut >= n - 1:
        return np.nan
    rss_pooled = _rss_segment(y, 0, n)
    rss_split = _rss_segment(y, 0, cut) + _rss_segment(y, cut, n)
    k = 1
    denom_df = n - 2 * k
    if denom_df <= 0 or rss_split <= 0:
        return np.nan
    return float(((rss_pooled - rss_split) / k) / (rss_split / denom_df))


def _best_breaks_dp(y, max_breaks=3, min_size=8):
    n = len(y)
    best = {"cuts": [], "bic": np.inf, "rss": np.inf}

    def recurse(start, remaining, cuts):
        nonlocal best
        if remaining == 0:
            all_cuts = sorted(cuts)
            segs = [0] + all_cuts + [n]
            rss = 0.0
            for a, b in zip(segs[:-1], segs[1:]):
                rss += _rss_segment(y, a, b)
            k = len(all_cuts) + 1
            bic = n * np.log(max(rss / max(n, 1), EPS)) + k * np.log(max(n, 2))
            if bic < best["bic"]:
                best = {"cuts": all_cuts, "bic": bic, "rss": rss}
            return
        for cut in range(start + min_size, n - min_size * remaining + 1):
            recurse(cut, remaining - 1, cuts + [cut])

    recurse(0, 0, [])
    for b in range(1, max_breaks + 1):
        recurse(0, b, [])
    return best["cuts"], best["bic"], best["rss"]


def structural_break_table(agg_df, pair_df):
    series_map = {"Aggregate index, H=8": agg_df.set_index("date")["g_net"].dropna()}
    for rep, par in [("CHN", "JPN"), ("CHN", "KOR"), ("CHN", "AUS")]:
        s = pair_df[(pair_df["reporter_iso"] == rep) & (pair_df["partner_iso"] == par)].set_index("date")["s_net_clip"].dropna()
        if len(s) >= 20:
            series_map[f"Bounded pair contribution, {rep} <- {par}"] = s
    rows = []
    for name, s in series_map.items():
        y = s.values.astype(float)
        dates = list(s.index)
        cuts, bic, rss = _best_breaks_dp(y, max_breaks=3, min_size=8)
        f_stats = [_chow_f_stat(y, c) for c in cuts]
        break_dates = [quarter_label(pd.Timestamp(dates[c])) for c in cuts]
        ci_l = [quarter_label(pd.Timestamp(dates[max(c - 1, 0)])) for c in cuts]
        ci_u = [quarter_label(pd.Timestamp(dates[min(c + 1, len(dates) - 1)])) for c in cuts]
        rows.append(
            {
                "Series": name,
                "break_dates": "; ".join(break_dates) if break_dates else "None",
                "break_CI_approx": "; ".join([f"[{l},{u}]" for l, u in zip(ci_l, ci_u)]) if cuts else "None",
                "max_Chow_F": float(np.nanmax(f_stats)) if f_stats else np.nan,
                "BIC": float(bic),
                "RSS": float(rss),
            }
        )
    return pd.DataFrame(rows)


def coefficient_plot(table_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    plot_df = table_df.copy()
    plot_df["Specification"] = (
        plot_df["Specification"].astype(str)
        .str.replace("Import-based W_t", "Baseline import topology", regex=False)
        .str.replace("Export-based W_t", "Export-based topology", regex=False)
        .str.replace("Symmetric W_t", "Symmetric topology", regex=False)
        .str.replace("Eight-quarter W_t", "Eight-quarter import topology", regex=False)
        .str.replace("Evolving topology W_t", "Evolving topology", regex=False)
        .str.replace("Frozen topology W_pre", "Frozen benchmark topology", regex=False)
        .str.replace("Unclipped s_net_raw", "Unbounded raw pair contribution", regex=False)
        .str.replace("1-99 trimmed s_net_raw", "1st-99th percentile trimmed raw pair contribution", regex=False)
        .str.replace("s_net_clip", "bounded pair contribution", regex=False)
        .str.replace("s_net_raw", "raw pair contribution", regex=False)
        .str.replace("g_net", "aggregate network index", regex=False)
    )
    plot_df["coef"] = pd.to_numeric(plot_df["Coefficient"], errors="coerce")
    plot_df["se"] = pd.to_numeric(plot_df["Std.Err"], errors="coerce")
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    y = np.arange(len(plot_df))[::-1]
    ax.axvline(0, color="black", lw=1, alpha=0.7)
    ax.errorbar(plot_df["coef"], y, xerr=1.96 * plot_df["se"], fmt="o", color="#1f77b4", ecolor="#6baed6", capsize=3)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_df["Specification"])
    ax.set_xlabel("Coefficient on tariff relief")
    ax.set_title("RCEP benchmark and inference panel")
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def aggregate_plot(agg_df, boot_df, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(2, 1, figsize=(8.8, 6.8), sharex=True)
    axes[0].plot(agg_df["date"], agg_df["g_net"], color="#1f77b4", lw=2)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p16"], boot_df["g_net_p84"], color="#9ecae1", alpha=0.5)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p025"], boot_df["g_net_p975"], color="#c6dbef", alpha=0.35)
    axes[0].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[0].set_ylabel("Aggregate network-propagation index")
    axes[0].set_title("Aggregate propagation index with bootstrap intervals")

    axes[1].plot(agg_df["date"], agg_df["half_life"], color="#dd8452", lw=2)
    axes[1].fill_between(boot_df["date"], boot_df["hl_p16"], boot_df["hl_p84"], color="#fdd0a2", alpha=0.5)
    axes[1].fill_between(boot_df["date"], boot_df["hl_p025"], boot_df["hl_p975"], color="#fee6ce", alpha=0.35)
    axes[1].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[1].set_ylabel("Half-life")
    axes[1].set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def girf_plot(girf_point, girf_boot, out_png: Path, out_pdf: Path):
    date_keys = sorted(girf_point.keys())
    fig, axes = plt.subplots(1, len(date_keys), figsize=(4.7 * len(date_keys), 3.75), sharey=True)
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
        ax.set_title(date_key, fontsize=9)
        ax.set_xlabel("Horizon")
        ax.tick_params(labelsize=8)
    axes[0].set_ylabel("Response")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def topology_difference_plot(agg_tv, agg_fix, boot_df, out_png: Path, out_pdf: Path):
    merged = agg_tv[["date", "g_net"]].merge(agg_fix[["date", "g_net"]], on="date", suffixes=("_tv", "_fix"))
    merged["diff"] = merged["g_net_tv"] - merged["g_net_fix"]
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.fill_between(boot_df["date"], boot_df["g_net_diff_p025"], boot_df["g_net_diff_p975"], color="#d9e8ef", alpha=0.62, linewidth=0)
    ax.fill_between(boot_df["date"], boot_df["g_net_diff_p16"], boot_df["g_net_diff_p84"], color="#aac8d6", alpha=0.58, linewidth=0)
    ax.plot(merged["date"], merged["diff"], label="Point estimate", color="#111111", lw=1.65)
    entry = pd.Timestamp("2022-01-01")
    ax.axvline(entry, color="#111111", ls="--", lw=0.9)
    ax.axhline(0, color="#111111", lw=0.8)
    ax.set_ylabel("Observed-minus-frozen aggregate-index difference")
    ax.set_xlabel("Date")
    ax.text(
        0.02,
        0.94,
        "Evolving minus frozen topology",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )
    ax.text(entry, ax.get_ylim()[1], "RCEP entry", ha="left", va="top", fontsize=7, rotation=90)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#eeeeee", lw=0.55)
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def top_exposure_propagation_perturbations(cp_results, horizon, unit_names):
    rows = []
    for item in cp_results:
        W_base = safe_row_normalize(np.asarray(item["W_window"][-1], dtype=float))
        hub, W_perturbed = top_import_exposure_perturbation(W_base, scale_factor=0.5)
        _, g_base, hl_base, _, _ = pair_metrics_from_blocks(item["A_list_cp"], item["B_list_cp"], item["Sigma"], W_base, horizon, unit_names)
        _, g_perturbed, hl_perturbed, _, _ = pair_metrics_from_blocks(item["A_list_cp"], item["B_list_cp"], item["Sigma"], W_perturbed, horizon, unit_names)
        rows.append(
            {
                "date": item["date"],
                "perturbation": "attenuate_top_import_exposure_incoming",
                "target_unit": unit_names[hub],
                "g_net_base": g_base,
                "g_net_perturbed": g_perturbed,
                "g_net_delta": g_perturbed - g_base,
                "half_life_base": hl_base,
                "half_life_perturbed": hl_perturbed,
                "half_life_delta": hl_perturbed - hl_base,
            }
        )
    return pd.DataFrame(rows)


def top_exposure_perturbation_summary(perturb_df):
    grp = perturb_df.copy()
    return pd.DataFrame(
        [
            {
                "perturbation": "attenuate_top_import_exposure_incoming",
                "n": int(len(grp)),
                "mean_g_net_base": float(grp["g_net_base"].mean()),
                "mean_g_net_perturbed": float(grp["g_net_perturbed"].mean()),
                "mean_g_net_delta": float(grp["g_net_delta"].mean()),
                "median_g_net_delta": float(grp["g_net_delta"].median()),
                "mean_half_life_delta": float(grp["half_life_delta"].mean()),
                "share_delta_negative": float((grp["g_net_delta"] < 0).mean()),
                "dominant_target_unit": grp["target_unit"].mode().iloc[0] if len(grp) else "",
            }
        ]
    )


def top_exposure_perturbation_plot(perturb_df, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(2, 1, figsize=(8.8, 6.2), sharex=True)
    axes[0].plot(perturb_df["date"], perturb_df["g_net_base"], color="#1f77b4", lw=2, label="Observed topology")
    axes[0].plot(perturb_df["date"], perturb_df["g_net_perturbed"], color="#d62728", lw=2, label="Top-exposure attenuation")
    axes[0].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[0].set_ylabel("Aggregate network-propagation index")
    axes[0].set_title("Top-exposure topology perturbation")
    axes[0].legend(frameon=False)

    axes[1].plot(perturb_df["date"], perturb_df["g_net_delta"], color="#4b5563", lw=2)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].axvline(pd.Timestamp("2022-01-01"), color="black", ls="--", lw=1)
    axes[1].set_ylabel("Perturbed minus observed")
    axes[1].set_xlabel("Date")
    for ax in axes:
        ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def clipping_summary(panel_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, grp in panel_df.groupby("variant_key"):
        raw_p25 = float(grp["s_net_raw"].quantile(0.25))
        raw_p50 = float(grp["s_net_raw"].quantile(0.50))
        raw_p75 = float(grp["s_net_raw"].quantile(0.75))
        raw_q01 = float(grp["s_net_raw"].quantile(0.01))
        raw_q99 = float(grp["s_net_raw"].quantile(0.99))
        rows.append(
            {
                "variant_key": key,
                "n_obs": int(len(grp)),
                "clip_at_0_pct": float((grp["s_net_clip"] <= EPS).mean() * 100),
                "clip_at_1_pct": float((grp["s_net_clip"] >= 1 - EPS).mean() * 100),
                "raw_mean": float(grp["s_net_raw"].mean()),
                "raw_p25": raw_p25,
                "raw_p50": raw_p50,
                "raw_p75": raw_p75,
                "raw_median": raw_p50,
                "raw_iqr": raw_p75 - raw_p25,
                "raw_min": float(grp["s_net_raw"].min()),
                "raw_max": float(grp["s_net_raw"].max()),
                "raw_q01": raw_q01,
                "raw_q99": raw_q99,
            }
        )
    return pd.DataFrame(rows)


def clipping_histogram(panel_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    baseline = panel_df[panel_df["variant_key"] == "baseline_import"].copy()
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    ax.hist(baseline["s_net_raw"], bins=40, color="#1f77b4", alpha=0.75, edgecolor="white")
    ax.axvline(0, color="black", lw=1, ls="--")
    ax.axvline(1, color="black", lw=1, ls=":")
    ax.set_title("Distribution of the raw pair-level network-contribution metric")
    ax.set_xlabel("Raw pair contribution")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def stability_summary(cp_results: list[dict], out_csv: Path):
    rows = []
    for item in cp_results:
        rows.append(
            {
                "date": pd.Timestamp(item["date"]),
                "radius_cp": float(item["radius_cp"]),
                "unstable": int(item["radius_cp"] >= 1.0),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    return df


def stability_plots(stability_df: pd.DataFrame, out_prefix: Path):
    fig, axes = plt.subplots(2, 1, figsize=(8.3, 6.6))
    axes[0].plot(stability_df["date"], stability_df["radius_cp"], color="#7c3aed", lw=2)
    axes[0].axhline(1.0, color="black", lw=1, ls="--")
    axes[0].set_ylabel("Spectral radius")
    axes[0].set_title("Date-by-date stability monitor")
    axes[1].hist(stability_df["radius_cp"], bins=24, color="#c4b5fd", edgecolor="white")
    axes[1].axvline(1.0, color="black", lw=1, ls="--")
    axes[1].set_xlabel("Spectral radius")
    axes[1].set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(out_prefix.with_suffix(".png"), dpi=900)
    fig.savefig(out_prefix.with_suffix(".pdf"))
    plt.close(fig)


def block_sensitivity_plot(block_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(2, 1, figsize=(7.8, 6.0), sharex=True)
    axes[0].plot(block_df["block_size"], block_df["g_net_diff_p50_mean"], marker="o", color="#1f77b4", lw=2)
    axes[0].fill_between(block_df["block_size"], block_df["g_net_diff_p025_mean"], block_df["g_net_diff_p975_mean"], color="#c6dbef", alpha=0.35)
    axes[0].set_ylabel("Aggregate difference")
    axes[0].set_title("Block-length sensitivity for the topology-difference index")
    if block_df["coef_p50"].notna().any():
        axes[1].plot(block_df["block_size"], block_df["coef_p50"], marker="o", color="#dd8452", lw=2)
        axes[1].fill_between(block_df["block_size"], block_df["coef_p025"], block_df["coef_p975"], color="#fdd0a2", alpha=0.35)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_xlabel("Bootstrap block length")
    axes[1].set_ylabel("Coefficient")
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def trimmed_raw_panel(panel_df: pd.DataFrame, lower_q=0.01, upper_q=0.99):
    bounds = panel_df["s_net_raw"].quantile([lower_q, upper_q])
    lower = float(bounds.iloc[0])
    upper = float(bounds.iloc[1])
    trimmed = panel_df[(panel_df["s_net_raw"] >= lower) & (panel_df["s_net_raw"] <= upper)].copy()
    return trimmed, lower, upper


def aggregate_topology_summary(agg_df: pd.DataFrame, agg_fix_df: pd.DataFrame, allowed_dates=None):
    merged = agg_df[["date", "g_net"]].merge(agg_fix_df[["date", "g_net"]], on="date", suffixes=("_tv", "_fix"))
    if allowed_dates is not None:
        merged = merged[merged["date"].isin(allowed_dates)].copy()
    diff = merged["g_net_tv"] - merged["g_net_fix"]
    return [
        {"Statistic": "Aggregate propagation index", "Value": float(merged["g_net_tv"].mean()), "N": int(len(merged))},
        {"Statistic": "Frozen-topology aggregate index", "Value": float(merged["g_net_fix"].mean()), "N": int(len(merged))},
        {"Statistic": "Evolving-minus-frozen aggregate difference", "Value": float(diff.mean()), "N": int(len(merged))},
    ]


def stability_exclusion_summary(panel_df: pd.DataFrame, agg_df: pd.DataFrame, agg_fix_df: pd.DataFrame, stability_df: pd.DataFrame, dep="s_net_clip") -> pd.DataFrame:
    stable_dates = set(pd.to_datetime(stability_df.loc[stability_df["unstable"] == 0, "date"]))
    reg_full = fit_panel(panel_df, dep=dep, cluster="pair", fe="pair_time")
    reg_stable = fit_panel(panel_df[panel_df["date"].isin(stable_dates)], dep=dep, cluster="pair", fe="pair_time")
    rows = [
        {"Statistic": "Pair-level coefficient", "Sample": "Full sample", "Value": reg_full["Coefficient"], "Std.Err": reg_full["Std.Err"], "p-value": reg_full["p-value"], "N": reg_full["N"]},
        {"Statistic": "Pair-level coefficient", "Sample": "Stable dates only", "Value": reg_stable["Coefficient"], "Std.Err": reg_stable["Std.Err"], "p-value": reg_stable["p-value"], "N": reg_stable["N"]},
    ]
    for item in aggregate_topology_summary(agg_df, agg_fix_df):
        rows.append({**item, "Sample": "Full sample", "Std.Err": np.nan, "p-value": np.nan})
    for item in aggregate_topology_summary(agg_df, agg_fix_df, stable_dates):
        rows.append({**item, "Sample": "Stable dates only", "Std.Err": np.nan, "p-value": np.nan})
    return pd.DataFrame(rows)


def project_cp_results(cp_results: list[dict], target_radius=0.98, max_iter=8):
    projected = []
    for item in cp_results:
        row = dict(item)
        A_list = [np.asarray(A, dtype=float).copy() for A in item["A_list_cp"]]
        B_list = [np.asarray(B, dtype=float).copy() for B in item["B_list_cp"]]
        W_use = safe_row_normalize(np.asarray(item["W_window"][-1], dtype=float))
        radius = effective_companion_radius(A_list, B_list, W_use)
        total_scale = 1.0
        n_iter = 0
        while radius >= 1.0 and n_iter < max_iter:
            scale_factor = min(1.0, target_radius / max(radius, EPS))
            A_list = [A * scale_factor for A in A_list]
            B_list = [B * scale_factor for B in B_list]
            total_scale *= scale_factor
            radius = effective_companion_radius(A_list, B_list, W_use)
            n_iter += 1
        row["A_list_cp"] = A_list
        row["B_list_cp"] = B_list
        row["beta_cp"] = beta_matrix_from_lists(A_list, B_list)
        row["radius_cp_original"] = float(item["radius_cp"])
        row["radius_cp"] = float(radius)
        row["projection_scale"] = float(total_scale)
        row["projection_iterations"] = int(n_iter)
        projected.append(row)
    return projected


def stability_projected_summary(
    panel_df: pd.DataFrame,
    agg_df: pd.DataFrame,
    agg_fix_df: pd.DataFrame,
    projected_panel_df: pd.DataFrame,
    projected_agg_df: pd.DataFrame,
    projected_agg_fix_df: pd.DataFrame,
    dep="s_net_clip",
) -> pd.DataFrame:
    reg_full = fit_panel(panel_df, dep=dep, cluster="pair", fe="pair_time")
    reg_projected = fit_panel(projected_panel_df, dep=dep, cluster="pair", fe="pair_time")
    rows = [
        {"Statistic": "Pair-level coefficient", "Sample": "Original full sample", "Value": reg_full["Coefficient"], "Std.Err": reg_full["Std.Err"], "p-value": reg_full["p-value"], "N": reg_full["N"]},
        {"Statistic": "Pair-level coefficient", "Sample": "Stability-projected path", "Value": reg_projected["Coefficient"], "Std.Err": reg_projected["Std.Err"], "p-value": reg_projected["p-value"], "N": reg_projected["N"]},
    ]
    for item in aggregate_topology_summary(agg_df, agg_fix_df):
        rows.append({**item, "Sample": "Original full sample", "Std.Err": np.nan, "p-value": np.nan})
    for item in aggregate_topology_summary(projected_agg_df, projected_agg_fix_df):
        rows.append({**item, "Sample": "Stability-projected path", "Std.Err": np.nan, "p-value": np.nan})
    return pd.DataFrame(rows)


def stability_sensitivity_plot(exclusion_df: pd.DataFrame, projected_df: pd.DataFrame, out_png: Path, out_pdf: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.65))

    coef_rows = [
        exclusion_df[(exclusion_df["Statistic"] == "Pair-level coefficient") & (exclusion_df["Sample"] == "Full sample")].iloc[0],
        exclusion_df[(exclusion_df["Statistic"] == "Pair-level coefficient") & (exclusion_df["Sample"] == "Stable dates only")].iloc[0],
        projected_df[(projected_df["Statistic"] == "Pair-level coefficient") & (projected_df["Sample"] == "Stability-projected path")].iloc[0],
    ]
    coef_labels = ["Full\nsample", "Stable dates\nonly", "Stability-projected\npath"]
    y = np.arange(len(coef_rows))[::-1]
    coef_vals = [float(row["Value"]) for row in coef_rows]
    coef_err = [1.96 * float(row["Std.Err"]) for row in coef_rows]
    axes[0].axvline(0, color="black", lw=0.8)
    axes[0].errorbar(coef_vals, y, xerr=coef_err, fmt="o", color="#1f77b4", ecolor="#93c5fd", capsize=3)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(coef_labels)
    axes[0].set_xlabel("Pair-level coefficient")
    axes[0].set_title("a  Pair-level coefficient sensitivity", loc="left", fontsize=9, fontweight="bold")
    axes[0].tick_params(axis="both", labelsize=8)

    diff_rows = [
        exclusion_df[(exclusion_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (exclusion_df["Sample"] == "Full sample")].iloc[0],
        exclusion_df[(exclusion_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (exclusion_df["Sample"] == "Stable dates only")].iloc[0],
        projected_df[(projected_df["Statistic"] == "Evolving-minus-frozen aggregate difference") & (projected_df["Sample"] == "Stability-projected path")].iloc[0],
    ]
    diff_vals = [float(row["Value"]) for row in diff_rows]
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].plot(coef_labels, diff_vals, marker="o", color="#15803d", lw=2)
    axes[1].set_ylabel("Mean evolving-minus-frozen difference")
    axes[1].set_title("b  Topology-difference sensitivity", loc="left", fontsize=9, fontweight="bold")
    axes[1].tick_params(axis="both", labelsize=8)

    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def mobility_illustration_plot(agg_df: pd.DataFrame, boot_df: pd.DataFrame, girf_point: dict, out_png: Path, out_pdf: Path):
    latest_label = sorted(girf_point.keys())[-1]
    horizon = list(range(len(girf_point[latest_label]["total"])))
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 4.2))

    axes[0].plot(agg_df["date"], agg_df["g_net"], color="#1f77b4", lw=2)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p16"], boot_df["g_net_p84"], color="#9ecae1", alpha=0.45)
    axes[0].fill_between(boot_df["date"], boot_df["g_net_p025"], boot_df["g_net_p975"], color="#c6dbef", alpha=0.28)
    axes[0].set_title("a. Aggregate propagation index", loc="left", fontsize=11, fontweight="bold")

    axes[1].plot(boot_df["date"], boot_df["g_net_diff_p50"], color="#15803d", lw=2)
    axes[1].fill_between(boot_df["date"], boot_df["g_net_diff_p16"], boot_df["g_net_diff_p84"], color="#bbf7d0", alpha=0.45)
    axes[1].fill_between(boot_df["date"], boot_df["g_net_diff_p025"], boot_df["g_net_diff_p975"], color="#dcfce7", alpha=0.28)
    axes[1].axhline(0, color="black", lw=0.8)
    axes[1].set_title("b. Evolving minus frozen topology", loc="left", fontsize=11, fontweight="bold")

    for label, color in [("total", "#1f77b4"), ("direct", "#ff7f0e"), ("network", "#2ca02c")]:
        axes[2].plot(horizon, girf_point[latest_label][label], lw=2, color=color, label=label.capitalize())
    axes[2].axhline(0, color="black", lw=0.8)
    axes[2].set_title(f"c. Representative GIRF ({latest_label})", loc="left", fontsize=11, fontweight="bold")
    axes[2].legend(frameon=False, fontsize=8)

    for ax in axes:
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    fig.savefig(out_png, dpi=900)
    fig.savefig(out_pdf)
    plt.close(fig)


def run(args):
    out_dir, fig_dir = output_paths(args.dataset)
    data = load_dataset(args.dataset)
    Y = data["Y"]
    dates = data["dates"]
    df_bilateral = data.get("df_bilateral")
    df_tc = data.get("df_tc")
    unit_names = data["unit_names"]
    girf_pair = data["girf_pair"]

    if args.dataset == "rcep":
        W_pre = compute_w_pre(df_bilateral)
        base_w_list = build_w_list(df_bilateral, dates, window_quarters=data["w_window_quarters"], mode=data["w_mode"])
        baseline_key = "baseline_import"
        baseline_label = "Import-based W_t"
    else:
        W_pre = data["W_pre"]
        base_w_list = data["w_list"]
        baseline_key = "baseline_mobility"
        baseline_label = data["primary_label"]
        data["level_panel"].to_csv(out_dir / "derived_monthly_panel.csv", index=False)
        with open(out_dir / "acquisition_info.json", "w") as f:
            json.dump(data["acquisition_info"], f, indent=2)

    effective_window = args.window if len(Y) > args.window + 8 else max(args.p + 8, len(Y) - 8)
    if effective_window != args.window:
        logger.info("[%s] Requested window=%s is infeasible for T=%s; using effective window=%s", args.dataset, args.window, len(Y), effective_window)

    lambda_ridge, lambda_losses = select_global_ridge_lambda(Y, base_w_list, dates, p=args.p, window=effective_window)
    logger.info("[%s] Selected ridge lambda=%s", args.dataset, lambda_ridge)

    local_results, beta_tensor, rolling_dates = estimate_rolling_local(Y, base_w_list, dates, p=args.p, window=effective_window, lambda_ridge=lambda_ridge)
    rank, rank_losses, fit_losses, beta_recon, _, full_fit_loss, rank_validation = select_cp_rank(
        beta_tensor,
        rolling_dates,
        dates,
        Y,
        base_w_list,
        effective_window,
        p=args.p,
    )
    logger.info("[%s] Selected CP rank=%s", args.dataset, rank)

    cp_results = cp_empirical_paths(local_results, beta_recon, p=args.p)
    target_dates = resolve_target_dates(cp_results, data["requested_girf_dates"])

    panels = []
    agg_series = []
    girf_points = {}
    panel_lookup = {}
    aggregate_lookup = {}

    if args.dataset == "rcep":
        variant_specs = [
            ("baseline_import", 4, "import", "Import-based W_t"),
            ("export_network", 4, "export", "Export-based W_t"),
            ("symmetric_network", 4, "symmetric", "Symmetric W_t"),
            ("long_window_network", 8, "import", "Eight-quarter W_t"),
        ]
        for key, window_quarters, mode, label in variant_specs:
            if key == "baseline_import":
                cur_results = cp_results
            else:
                cur_w_list = build_w_list(df_bilateral, dates, window_quarters=window_quarters, mode=mode)
                local_alt, beta_tensor_alt, _ = estimate_rolling_local(Y, cur_w_list, dates, p=args.p, window=effective_window, lambda_ridge=lambda_ridge)
                factors_alt, _ = cp_fit(beta_tensor_alt, rank, n_init=args.cp_inits, max_iter=args.cp_max_iter, tol=args.cp_tol, seed=20260328 + window_quarters)
                beta_recon_alt = cp_reconstruct(factors_alt)
                cur_results = cp_empirical_paths(local_alt, beta_recon_alt, p=args.p)
            pair_df, agg_df, girf = build_pair_panel(cur_results, df_tc, horizon=8, W_mode=mode, w_label=label, unit_names=unit_names, girf_pair=girf_pair, target_dates=target_dates, W_fixed=None)
            pair_df["variant_key"] = key
            agg_df["variant_key"] = key
            panels.append(pair_df)
            agg_series.append(agg_df)
            panel_lookup[key] = pair_df
            aggregate_lookup[key] = agg_df
            if key == baseline_key:
                girf_points = girf
    else:
        pair_df, agg_df, girf = build_pair_panel(cp_results, df_tc, horizon=8, W_mode=data["w_mode"], w_label=baseline_label, unit_names=unit_names, girf_pair=girf_pair, target_dates=target_dates, W_fixed=None)
        pair_df["variant_key"] = baseline_key
        agg_df["variant_key"] = baseline_key
        panels.append(pair_df)
        agg_series.append(agg_df)
        panel_lookup[baseline_key] = pair_df
        aggregate_lookup[baseline_key] = agg_df
        girf_points = girf

    pair_h12, agg_h12, _ = build_pair_panel(cp_results, df_tc, horizon=12, W_mode=data["w_mode"], w_label=baseline_label, unit_names=unit_names, girf_pair=girf_pair, target_dates=target_dates, W_fixed=None)
    pair_h12["variant_key"] = "baseline_h12"
    agg_h12["variant_key"] = "baseline_h12"
    panels.append(pair_h12)
    agg_series.append(agg_h12)
    panel_lookup["baseline_h12"] = pair_h12
    aggregate_lookup["baseline_h12"] = agg_h12

    pair_fix, agg_fix, _ = build_pair_panel(cp_results, df_tc, horizon=8, W_mode=data["w_mode"], w_label="Frozen topology W_pre", unit_names=unit_names, girf_pair=girf_pair, target_dates=target_dates, W_fixed=W_pre)
    pair_fix["variant_key"] = "fixed_pre"
    agg_fix["variant_key"] = "fixed_pre"
    panels.append(pair_fix)
    agg_series.append(agg_fix)
    panel_lookup["fixed_pre"] = pair_fix
    aggregate_lookup["fixed_pre"] = agg_fix

    all_pairs = pd.concat(panels, ignore_index=True)
    all_agg = pd.concat(agg_series, ignore_index=True)

    boot_agg, girf_boot, coef_summary, coef_draw_df = bootstrap_cp_pipeline(
        local_results,
        rank,
        lambda_ridge,
        df_tc,
        unit_names,
        girf_pair,
        target_dates,
        n_boot=args.n_boot,
        block_size=args.block_size,
        p=args.p,
        W_pre=W_pre,
    )
    if coef_summary and df_tc is not None and baseline_key in panel_lookup and "fixed_pre" in panel_lookup:
        point_evolving = fit_panel(panel_lookup[baseline_key], dep="s_net_clip", cluster="pair", fe="pair_time")["Coefficient"]
        point_frozen = fit_panel(panel_lookup["fixed_pre"], dep="s_net_clip", cluster="pair", fe="pair_time")["Coefficient"]
        points = {
            "evolving_coefficient": point_evolving,
            "frozen_coefficient": point_frozen,
            "attenuation_difference": point_evolving - point_frozen,
            "frozen_evolving_ratio": point_frozen / max(point_evolving, EPS),
        }
        for quantity, point in points.items():
            if quantity in coef_summary.get("quantities", {}):
                coef_summary["quantities"][quantity]["point"] = float(point)

    selection = {
        "dataset": args.dataset,
        "ridge_lambda": lambda_ridge,
        "ridge_losses": lambda_losses,
        "cp_rank": rank,
        "rank_losses": rank_losses,
        "fit_losses": fit_losses,
        "full_fit_loss": full_fit_loss,
        "rank_validation": rank_validation,
        "cp_inits": args.cp_inits,
        "cp_max_iter": args.cp_max_iter,
        "cp_tol": args.cp_tol,
        "window": effective_window,
        "requested_window": args.window,
        "lag_order": args.p,
        "bootstrap_replications": args.n_boot,
        "bootstrap_block_size": args.block_size,
        "stability_rate_cp": float(np.mean([row["radius_cp"] >= 1.0 for row in cp_results])),
        "requested_girf_dates": [str(pd.Timestamp(x).date()) for x in data["requested_girf_dates"]],
        "selected_girf_dates": {label: str(pd.Timestamp(date).date()) for date, label in target_dates.items()},
    }

    all_agg.to_csv(out_dir / "aggregate_cp_metrics.csv", index=False)
    boot_agg.to_csv(out_dir / "aggregate_cp_bootstrap.csv", index=False)
    if len(coef_draw_df):
        coef_draw_df.to_csv(out_dir / "full_path_attenuation_bootstrap.csv", index=False)
        full_path_rows = []
        quantities = (coef_summary or {}).get("quantities", {})
        for quantity, row in quantities.items():
            full_path_rows.append(
                {
                    **row,
                    "bootstrap_replications": (coef_summary or {}).get("bootstrap_replications", args.n_boot),
                    "bootstrap_type": (coef_summary or {}).get("bootstrap_type", "moving-block residual bootstrap with CP re-estimation"),
                }
            )
        pd.DataFrame(full_path_rows).to_csv(out_dir / "full_path_attenuation_bootstrap_summary.csv", index=False)
        with open(out_dir / "full_path_attenuation_bootstrap_summary.json", "w") as f:
            json.dump(coef_summary, f, indent=2)
    with open(out_dir / "girf_cp_bootstrap.json", "w") as f:
        json.dump(girf_boot, f, indent=2)
    with open(out_dir / "girf_cp_point.json", "w") as f:
        json.dump(girf_points, f, indent=2)

    stability_df = stability_summary(cp_results, out_dir / "stability_summary.csv")
    stability_plots(stability_df, fig_dir / "fig_cp_stability")
    aggregate_plot(aggregate_lookup[baseline_key], boot_agg, fig_dir / "fig_cp_aggregate_intervals.png", fig_dir / "fig_cp_aggregate_intervals.pdf")
    girf_plot(girf_points, girf_boot, fig_dir / "fig_cp_girf_intervals.png", fig_dir / "fig_cp_girf_intervals.pdf")
    topology_difference_plot(aggregate_lookup[baseline_key], aggregate_lookup["fixed_pre"], boot_agg, fig_dir / "fig_cp_fixed_vs_tv.png", fig_dir / "fig_cp_fixed_vs_tv.pdf")

    if args.dataset == "rcep":
        perturb_df = top_exposure_propagation_perturbations(cp_results, horizon=8, unit_names=unit_names)
        perturb_summary_df = top_exposure_perturbation_summary(perturb_df)
        perturb_df.to_csv(out_dir / "network_propagation_perturbations.csv", index=False)
        perturb_summary_df.to_csv(out_dir / "network_propagation_perturbation_summary.csv", index=False)
        top_exposure_perturbation_plot(perturb_df, fig_dir / "fig_network_propagation_perturbation.png", fig_dir / "fig_network_propagation_perturbation.pdf")

        all_pairs.to_csv(out_dir / "pairwise_cp_panel.csv", index=False)
        trimmed_panel, trim_q01, trim_q99 = trimmed_raw_panel(panel_lookup["baseline_import"])
        table_df = pd.DataFrame(
            [
                {"Panel": "Alternative topology", "Specification": "Baseline import topology", **fit_panel(panel_lookup["baseline_import"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Alternative topology", "Specification": "Export-based topology", **fit_panel(panel_lookup["export_network"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Alternative topology", "Specification": "Symmetric topology", **fit_panel(panel_lookup["symmetric_network"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Alternative topology", "Specification": "Eight-quarter import topology", **fit_panel(panel_lookup["long_window_network"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Topology benchmark", "Specification": "Evolving topology", **fit_panel(panel_lookup["baseline_import"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Topology benchmark", "Specification": "Frozen benchmark topology", **fit_panel(panel_lookup["fixed_pre"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Inference sensitivity", "Specification": "Horizon H=12", **fit_panel(panel_lookup["baseline_h12"], dep="s_net_clip", cluster="pair", fe="pair_time")},
                {"Panel": "Inference sensitivity", "Specification": "Two-way clustered SE", **fit_panel(panel_lookup["baseline_import"], dep="s_net_clip", cluster="origin_dest", fe="pair_time")},
                {"Panel": "Metric sensitivity", "Specification": "Unbounded raw pair-level contribution", **fit_panel(panel_lookup["baseline_import"], dep="s_net_raw", cluster="pair", fe="pair_time")},
                {"Panel": "Metric sensitivity", "Specification": "1st-99th percentile trimmed raw pair-level contribution", **fit_panel(trimmed_panel, dep="s_net_raw", cluster="pair", fe="pair_time")},
            ]
        )
        table_df.to_csv(out_dir / "table_rcep_cp_benchmark.csv", index=False)
        coefficient_plot(table_df, fig_dir / "fig_cp_coefficient_plot.png", fig_dir / "fig_cp_coefficient_plot.pdf")

        breaks_df = structural_break_table(aggregate_lookup["baseline_import"], panel_lookup["baseline_import"])
        breaks_df.to_csv(out_dir / "table_rcep_cp_structural_breaks.csv", index=False)

        clip_df = clipping_summary(all_pairs)
        clip_df.loc[clip_df["variant_key"] == "baseline_import", "trim_q01"] = trim_q01
        clip_df.loc[clip_df["variant_key"] == "baseline_import", "trim_q99"] = trim_q99
        clip_df.to_csv(out_dir / "clipping_summary.csv", index=False)
        clipping_histogram(panel_lookup["baseline_import"], fig_dir / "fig_cp_clipping_histogram.png", fig_dir / "fig_cp_clipping_histogram.pdf")

        block_df = bootstrap_block_sensitivity(
            local_results,
            rank,
            lambda_ridge,
            df_tc,
            unit_names,
            girf_pair,
            target_dates,
            p=args.p,
            W_pre=W_pre,
            n_boot=min(args.n_boot, 160),
        )
        block_df.to_csv(out_dir / "block_length_sensitivity.csv", index=False)
        block_sensitivity_plot(block_df, fig_dir / "fig_cp_block_length_sensitivity.png", fig_dir / "fig_cp_block_length_sensitivity.pdf")

        exclusion_df = stability_exclusion_summary(panel_lookup["baseline_import"], aggregate_lookup["baseline_import"], aggregate_lookup["fixed_pre"], stability_df)
        exclusion_df.to_csv(out_dir / "stability_exclusion_sensitivity.csv", index=False)

        projected_results = project_cp_results(cp_results, target_radius=0.98)
        projected_pair, projected_agg, _ = build_pair_panel(
            projected_results,
            df_tc,
            horizon=8,
            W_mode=data["w_mode"],
            w_label=baseline_label,
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=None,
        )
        projected_fix, projected_agg_fix, _ = build_pair_panel(
            projected_results,
            df_tc,
            horizon=8,
            W_mode=data["w_mode"],
            w_label="Frozen topology W_pre",
            unit_names=unit_names,
            girf_pair=girf_pair,
            target_dates=target_dates,
            W_fixed=W_pre,
        )
        projected_pair["variant_key"] = "stability_projected"
        projected_agg["variant_key"] = "stability_projected"
        projected_fix["variant_key"] = "stability_projected_fixed_pre"
        projected_agg_fix["variant_key"] = "stability_projected_fixed_pre"
        projected_df = stability_projected_summary(
            panel_lookup["baseline_import"],
            aggregate_lookup["baseline_import"],
            aggregate_lookup["fixed_pre"],
            projected_pair,
            projected_agg,
            projected_agg_fix,
        )
        projected_df.to_csv(out_dir / "stability_projected_sensitivity.csv", index=False)
        stability_sensitivity_plot(
            exclusion_df,
            projected_df,
            fig_dir / "fig_cp_stability_sensitivity.png",
            fig_dir / "fig_cp_stability_sensitivity.pdf",
        )
    else:
        mobility_illustration_plot(aggregate_lookup[baseline_key], boot_agg, girf_points, fig_dir / "fig_cp_mobility_illustration.png", fig_dir / "fig_cp_mobility_illustration.pdf")

    with open(out_dir / "selection_summary.json", "w") as f:
        json.dump({**selection, "coef_bootstrap_summary": coef_summary}, f, indent=2)

    logger.info("Saved %s outputs to %s", args.dataset, out_dir)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["rcep", "nyc_taxi"], default="rcep")
    parser.add_argument("--window", type=int, default=40)
    parser.add_argument("--p", type=int, default=2)
    parser.add_argument("--n-boot", type=int, default=500)
    parser.add_argument("--block-size", type=int, default=4)
    parser.add_argument("--cp-inits", type=int, default=6)
    parser.add_argument("--cp-max-iter", type=int, default=100)
    parser.add_argument("--cp-tol", type=float, default=1e-6)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
