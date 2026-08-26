import numpy as np


def lagged_network_exposure(W_list, Y, tau: int, lag: int) -> np.ndarray:
    """Return the lag-specific exposure vector used in each rolling equation."""
    if lag < 1 or tau - lag < 0:
        raise ValueError("lagged exposure requires lag >= 1 and tau - lag >= 0")
    y_lag = np.asarray(Y[tau - lag], dtype=float)
    W_lag = W_list[tau - lag]
    if W_lag is None:
        return np.zeros_like(y_lag, dtype=float)
    return np.asarray(W_lag, dtype=float) @ y_lag


def equationwise_ridge_fit(Y, W_list, X_exog=None, p=2, lambda_ridge=1e-4):
    """Fit the diagonal direct/network block parameterization used in the paper."""
    Y = np.asarray(Y, dtype=float)
    if Y.ndim != 2 or not np.all(np.isfinite(Y)):
        raise ValueError("Y must be a finite two-dimensional array")
    T, N = Y.shape
    if not isinstance(p, (int, np.integer)) or p < 1:
        raise ValueError("p must be an integer greater than or equal to one")
    if T <= p:
        raise ValueError("Y must contain more observations than the lag order")
    if not np.isfinite(lambda_ridge) or float(lambda_ridge) <= 0:
        raise ValueError("lambda_ridge must be finite and strictly positive")
    if len(W_list) != T:
        raise ValueError("W_list and Y must have the same time dimension")
    for idx, W in enumerate(W_list):
        if W is None:
            continue
        W_array = np.asarray(W, dtype=float)
        if W_array.shape != (N, N) or not np.all(np.isfinite(W_array)):
            raise ValueError(f"W_list[{idx}] must be a finite {N} by {N} matrix or None")
    if X_exog is None:
        X_exog = np.zeros((T, 0))
    X_exog = np.asarray(X_exog, dtype=float)
    if X_exog.ndim != 2 or X_exog.shape[0] != T or not np.all(np.isfinite(X_exog)):
        raise ValueError("X_exog must be finite, two-dimensional and aligned with Y")
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
                row.append(lagged_network_exposure(W_list, Y, tau, lag)[i])
            if K > 0:
                row.extend(X_exog[tau])
            rows.append(row)

        design = np.asarray(rows, dtype=float)
        outcome = Y[p:, i]
        lhs = design.T @ design + float(lambda_ridge) * np.eye(design.shape[1])
        rhs = design.T @ outcome
        beta_i, _, _, _ = np.linalg.lstsq(lhs, rhs, rcond=None)

        c[i] = beta_i[0]
        for lag in range(p):
            A_list[lag][i, i] = beta_i[1 + lag]
            B_list[lag][i, i] = beta_i[1 + p + lag]
        if K > 0:
            Pi[i, :] = beta_i[1 + 2 * p:]
        residuals[:, i] = outcome - design @ beta_i

    Sigma = (residuals.T @ residuals) / max(residuals.shape[0] - 1, 1)
    Sigma = (Sigma + Sigma.T) / 2 + 1e-8 * np.eye(N)
    return c, A_list, B_list, Pi, Sigma, residuals
