"""Estimation and exact-support abstention for the R006f fixed design."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scripts.experiments.r006f_exact_design import (
    ExactPanel,
    generate_paired_worlds,
)


@dataclass(frozen=True)
class QueryResult:
    status: str
    matrix: np.ndarray | None
    chi: float

    def __post_init__(self) -> None:
        if self.status not in {"available", "unsupported"}:
            raise ValueError("status must be available or unsupported")
        if not np.isfinite(self.chi) or self.chi < 0.0:
            raise ValueError("chi must be finite and nonnegative")
        if self.status == "available":
            if self.matrix is None:
                raise ValueError("available results require a matrix")
            value = np.array(self.matrix, dtype=float, copy=True)
            if value.ndim != 2:
                raise ValueError("query matrix must be two-dimensional")
            if not np.isfinite(value).all():
                raise ValueError("query matrix must contain only finite values")
            value.setflags(write=False)
            object.__setattr__(self, "matrix", value)
        elif self.matrix is not None:
            raise ValueError("unsupported results must not contain a matrix")


@dataclass(frozen=True)
class TruncatedSVDSolution:
    coefficient: np.ndarray
    singular_values: np.ndarray
    tau: float
    retained_rank: int

    def __post_init__(self) -> None:
        for name in ("coefficient", "singular_values"):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class FWLFit:
    slope: np.ndarray
    singular_values: np.ndarray
    tau: float
    retained_rank: int

    def __post_init__(self) -> None:
        for name in ("slope", "singular_values"):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class PairResult:
    seed: int
    scale: float
    panel: ExactPanel
    fitted_slope: np.ndarray
    supported: QueryResult
    unsupported: QueryResult
    silent_supported: QueryResult
    silent_unsupported: QueryResult
    oracle_world0: np.ndarray
    oracle_world1: np.ndarray
    retained_singular_values: np.ndarray
    tau: float
    retained_rank: int
    inverse_amplification: float
    supported_ols_error: float
    silent_error_world0: float
    silent_error_world1: float
    analytic_gap_norm: float
    decomposition_residual: float

    def __post_init__(self) -> None:
        for name in (
            "fitted_slope",
            "oracle_world0",
            "oracle_world1",
            "retained_singular_values",
        ):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            value.setflags(write=False)
            object.__setattr__(self, name, value)


def truncated_svd_solve(
    design: np.ndarray,
    outcome: np.ndarray,
    *,
    kappa_max: float,
    absolute_floor: float,
) -> TruncatedSVDSolution:
    u, singular_values, vh = np.linalg.svd(design, full_matrices=False)
    s_max = float(singular_values[0]) if singular_values.size else 0.0
    tau = max(float(absolute_floor), s_max / float(kappa_max))
    retained = singular_values >= tau
    coefficient = np.zeros((design.shape[1], outcome.shape[1]), dtype=float)
    if np.any(retained):
        coefficient = (
            vh[retained].T
            @ ((u[:, retained].T @ outcome) / singular_values[retained, None])
        )
    return TruncatedSVDSolution(
        coefficient=coefficient,
        singular_values=singular_values,
        tau=tau,
        retained_rank=int(np.count_nonzero(retained)),
    )


def fwl_min_norm_ols(
    x: np.ndarray,
    z: np.ndarray,
    y: np.ndarray,
    *,
    kappa_max: float = 50.0,
    absolute_floor: float = 1e-12,
) -> FWLFit:
    """Estimate only the numerically supported slope projection by FWL OLS."""
    x_array = np.asarray(x, dtype=float)
    z_array = np.asarray(z, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if any(array.ndim != 2 for array in (x_array, z_array, y_array)):
        raise ValueError("x, z, and y must be two-dimensional")
    if not (x_array.shape[0] == z_array.shape[0] == y_array.shape[0]):
        raise ValueError("x, z, and y must have aligned rows")
    if not all(np.isfinite(array).all() for array in (x_array, z_array, y_array)):
        raise ValueError("x, z, and y must contain only finite values")
    if not np.isfinite(kappa_max) or kappa_max <= 1.0:
        raise ValueError("kappa_max must be finite and greater than one")
    if not np.isfinite(absolute_floor) or absolute_floor <= 0.0:
        raise ValueError("absolute_floor must be finite and positive")
    x_coef = np.linalg.lstsq(x_array, y_array, rcond=None)[0]
    z_coef = np.linalg.lstsq(x_array, z_array, rcond=None)[0]
    y_tilde = y_array - x_array @ x_coef
    z_tilde = z_array - x_array @ z_coef
    solution = truncated_svd_solve(
        z_tilde,
        y_tilde,
        kappa_max=kappa_max,
        absolute_floor=absolute_floor,
    )
    return FWLFit(
        slope=solution.coefficient.T,
        singular_values=solution.singular_values,
        tau=solution.tau,
        retained_rank=solution.retained_rank,
    )


def certificate_aware_evaluator(
    fitted_slope: np.ndarray,
    delta_w: np.ndarray,
    chi: float,
    threshold: float = 0.05,
) -> QueryResult:
    if not np.isfinite(threshold) or threshold < 0.0:
        raise ValueError("threshold must be finite and nonnegative")
    if chi <= threshold:
        return QueryResult(
            status="available",
            matrix=np.asarray(fitted_slope) @ np.asarray(delta_w),
            chi=float(chi),
        )
    return QueryResult(status="unsupported", matrix=None, chi=float(chi))


def silent_evaluator(
    fitted_slope: np.ndarray,
    delta_w: np.ndarray,
    chi: float,
) -> QueryResult:
    return QueryResult(
        status="available",
        matrix=np.asarray(fitted_slope) @ np.asarray(delta_w),
        chi=float(chi),
    )


def oracle_supported_projection(
    truth_slope: np.ndarray,
    projector: np.ndarray,
) -> np.ndarray:
    result = np.array(
        np.asarray(truth_slope) @ np.asarray(projector), copy=True
    )
    result.setflags(write=False)
    return result


def decomposition_residual(
    truth_slope: np.ndarray,
    delta_w: np.ndarray,
    projector: np.ndarray,
) -> float:
    b = np.asarray(truth_slope)
    delta = np.asarray(delta_w)
    p = np.asarray(projector)
    identity = np.eye(p.shape[0])
    residual = b @ delta - b @ p @ delta - b @ (identity - p) @ delta
    return float(np.linalg.norm(residual, ord="fro"))


def run_pair(seed: int = 906001, scale: float = 1.0) -> PairResult:
    worlds = generate_paired_worlds(seed=seed, scale=scale)
    panel = worlds.panel
    fitted = fwl_min_norm_ols(
        panel.x,
        panel.topology_exposure,
        worlds.world0.y,
        kappa_max=panel.config.kappa_max,
        absolute_floor=panel.config.absolute_floor,
    )
    supported = certificate_aware_evaluator(
        fitted.slope,
        panel.delta_supported,
        panel.supported_chi,
        panel.config.classification_threshold,
    )
    unsupported = certificate_aware_evaluator(
        fitted.slope,
        panel.delta_unsupported,
        panel.unsupported_chi,
        panel.config.classification_threshold,
    )
    silent_supported = silent_evaluator(
        fitted.slope, panel.delta_supported, panel.supported_chi
    )
    silent_unsupported = silent_evaluator(
        fitted.slope, panel.delta_unsupported, panel.unsupported_chi
    )
    oracle0 = oracle_supported_projection(
        worlds.world0.b, panel.analytic_projector
    )
    oracle1 = oracle_supported_projection(
        worlds.world1.b, panel.analytic_projector
    )
    retained = fitted.singular_values[fitted.singular_values >= fitted.tau]
    truth0 = worlds.world0.b @ panel.delta_unsupported
    truth1 = worlds.world1.b @ panel.delta_unsupported
    silent_error0 = float(
        np.linalg.norm(silent_unsupported.matrix - truth0, ord="fro")
    )
    silent_error1 = float(
        np.linalg.norm(silent_unsupported.matrix - truth1, ord="fro")
    )
    gap_norm = float(np.linalg.norm(truth1 - truth0, ord="fro"))
    supported_error = float(
        np.linalg.norm(
            supported.matrix - worlds.world0.b @ panel.delta_supported,
            ord="fro",
        )
    )
    residual = max(
        decomposition_residual(
            world.b,
            panel.delta_unsupported,
            panel.analytic_projector,
        )
        for world in (worlds.world0, worlds.world1)
    )
    return PairResult(
        seed=seed,
        scale=panel.scale,
        panel=panel,
        fitted_slope=fitted.slope,
        supported=supported,
        unsupported=unsupported,
        silent_supported=silent_supported,
        silent_unsupported=silent_unsupported,
        oracle_world0=oracle0,
        oracle_world1=oracle1,
        retained_singular_values=retained,
        tau=fitted.tau,
        retained_rank=fitted.retained_rank,
        inverse_amplification=float(1.0 / retained[-1]),
        supported_ols_error=supported_error,
        silent_error_world0=silent_error0,
        silent_error_world1=silent_error1,
        analytic_gap_norm=gap_norm,
        decomposition_residual=residual,
    )
