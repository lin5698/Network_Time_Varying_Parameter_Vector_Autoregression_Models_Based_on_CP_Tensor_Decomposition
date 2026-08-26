"""Design-weighted joint Tucker candidate for the frozen R006e protocol."""

from __future__ import annotations

import argparse
import hashlib
import math
import time
from dataclasses import dataclass, replace
from typing import Callable, Iterable

import numpy as np

from scripts.experiments.r005_separation_stability_pilot import _tucker_reconstruct
from scripts.experiments.r006e_native_estimators import (
    FittedPath,
    fit_anchor_local,
)
from scripts.experiments.r006e_native_protocol import (
    FitInputs,
    R006EConfig,
    keyed_seed,
)


TEMPORAL_PENALTIES = (0.0, 0.01, 0.05, 0.20)
VALIDATION_POSITIONS = tuple(range(60, 84))
EVALUATION_POSITIONS = tuple(range(84, 120))
TUCKER_RANK = 3
BACKTRACKING_STEPS = tuple(2.0 ** (-j) for j in range(25))
SVD_TIE_TOLERANCE_MULTIPLIER = 64.0
SVD_TIE_TOLERANCE_FORMULA = "64*eps*max(sigma_max,1)"


def _readonly(value: np.ndarray) -> np.ndarray:
    contiguous = np.ascontiguousarray(value)
    return np.frombuffer(contiguous.tobytes(), dtype=contiguous.dtype).reshape(
        contiguous.shape
    )


def _require_tensor(value: np.ndarray, shape: tuple[int, int, int]) -> np.ndarray:
    tensor = np.asarray(value, dtype=float)
    if tensor.shape != shape:
        raise ValueError(f"coefficient tensor must have shape {shape}")
    if not np.all(np.isfinite(tensor)):
        raise ValueError("coefficient tensor must be finite")
    return tensor


@dataclass(frozen=True)
class GramCache:
    grams: np.ndarray
    cross_products: np.ndarray
    outcome_squares: np.ndarray
    window_sizes: np.ndarray
    g_bar: float
    n: int
    dates: np.ndarray

    def __post_init__(self) -> None:
        grams = np.asarray(self.grams, dtype=float)
        cross = np.asarray(self.cross_products, dtype=float)
        squares = np.asarray(self.outcome_squares, dtype=float)
        sizes = np.asarray(self.window_sizes, dtype=int)
        dates = np.asarray(self.dates, dtype=int)
        d = len(dates)
        expected = (d, 2 * self.n, 2 * self.n)
        if grams.shape != expected or cross.shape != (d, self.n, 2 * self.n):
            raise ValueError("Gram cache arrays are not aligned")
        if squares.shape != (d,) or sizes.shape != (d,) or np.any(sizes <= 0):
            raise ValueError("Gram cache scales are not aligned")
        if not all(np.all(np.isfinite(x)) for x in (grams, cross, squares)):
            raise ValueError("Gram cache must be finite")
        if not math.isfinite(self.g_bar) or self.g_bar < 0.0:
            raise ValueError("g_bar must be finite and non-negative")
        for name, value in (
            ("grams", grams), ("cross_products", cross),
            ("outcome_squares", squares), ("window_sizes", sizes),
            ("dates", dates),
        ):
            object.__setattr__(self, name, _readonly(value))

    def sha256(self) -> str:
        digest = hashlib.sha256()
        for value in (
            self.grams, self.cross_products, self.outcome_squares,
            self.window_sizes, self.dates,
        ):
            array = np.ascontiguousarray(value)
            digest.update(array.dtype.str.encode("ascii"))
            digest.update(repr(array.shape).encode("ascii"))
            digest.update(array.tobytes())
        digest.update(np.float64(self.g_bar).tobytes())
        return digest.hexdigest()


def _window_design(fit: FitInputs, date: int, window: int) -> tuple[np.ndarray, np.ndarray]:
    if date - window < 0:
        raise ValueError("coefficient date does not contain a full rolling window")
    predictors = np.asarray(fit.predictors[date - window:date], dtype=float)
    delta = np.asarray(fit.topology[date - window:date], dtype=float) - fit.w_ref[None]
    exposure = np.einsum("tij,tj->ti", delta, predictors, optimize=True)
    design = np.concatenate([predictors, exposure], axis=1)
    outcomes = np.asarray(fit.outcomes[date - window:date], dtype=float)
    return design, outcomes


def _resolve_window(fit: FitInputs, window: int | None) -> int:
    result = int(fit.coefficient_dates[0]) if window is None else int(window)
    if result <= 0:
        raise ValueError("window must be positive")
    return result


def build_gram_cache(fit: FitInputs, *, window: int | None = None) -> GramCache:
    if not isinstance(fit, FitInputs):
        raise TypeError("fit must be a FitInputs record")
    rolling_window = _resolve_window(fit, window)
    n = fit.predictors.shape[1]
    grams: list[np.ndarray] = []
    cross_products: list[np.ndarray] = []
    outcome_squares: list[float] = []
    sizes: list[int] = []
    for raw_date in fit.coefficient_dates:
        design, outcomes = _window_design(fit, int(raw_date), rolling_window)
        grams.append(design.T @ design)
        cross_products.append(outcomes.T @ design)
        outcome_squares.append(float(np.sum(np.square(outcomes))))
        sizes.append(len(design))
    gram_array = np.stack(grams)
    size_array = np.asarray(sizes, dtype=int)
    g_bar = float(np.mean([
        np.trace(gram_array[i]) / (size_array[i] * 2 * n)
        for i in range(len(size_array))
    ]))
    return GramCache(
        grams=gram_array,
        cross_products=np.stack(cross_products),
        outcome_squares=np.asarray(outcome_squares),
        window_sizes=size_array,
        g_bar=g_bar,
        n=n,
        dates=fit.coefficient_dates,
    )


def slice_outcome_loss(
    coefficient: np.ndarray,
    fit: FitInputs,
    *,
    position: int,
    window: int | None = None,
) -> float:
    if not 0 <= int(position) < len(fit.coefficient_dates):
        raise ValueError("position does not index a coefficient date")
    rolling_window = _resolve_window(fit, window)
    design, outcomes = _window_design(
        fit, int(fit.coefficient_dates[int(position)]), rolling_window
    )
    theta = np.asarray(coefficient, dtype=float)
    n = fit.predictors.shape[1]
    if theta.shape != (n, 2 * n):
        raise ValueError("coefficient slice has incompatible dimensions")
    residual = outcomes - design @ theta.T
    return float(np.sum(np.square(residual)))


def _temporal_penalty(theta: np.ndarray, cache: GramCache, lambda_t: float) -> float:
    d = theta.shape[2]
    if d < 2 or lambda_t == 0.0:
        return 0.0
    differences = np.diff(theta, axis=2)
    scale = lambda_t * cache.g_bar / (2 * cache.n ** 2 * (d - 1))
    return float(scale * np.sum(np.square(differences)))


def normalized_outcome_loss(
    theta: np.ndarray,
    fit: FitInputs,
    *,
    lambda_t: float = 0.0,
    window: int | None = None,
) -> float:
    cache = build_gram_cache(fit, window=window)
    tensor = _require_tensor(theta, (cache.n, 2 * cache.n, len(cache.dates)))
    losses = [
        slice_outcome_loss(tensor[:, :, i], fit, position=i, window=window)
        / (cache.n * cache.window_sizes[i])
        for i in range(len(cache.dates))
    ]
    return float(np.mean(losses) + _temporal_penalty(tensor, cache, lambda_t))


def normalized_gram_loss(
    theta: np.ndarray, cache: GramCache, *, lambda_t: float = 0.0
) -> float:
    tensor = _require_tensor(theta, (cache.n, 2 * cache.n, len(cache.dates)))
    losses: list[float] = []
    for i in range(len(cache.dates)):
        coefficient = tensor[:, :, i]
        quadratic = float(np.einsum(
            "ij,jk,ik->", coefficient, cache.grams[i], coefficient,
            optimize=True,
        ))
        linear = float(np.sum(coefficient * cache.cross_products[i]))
        losses.append(
            (quadratic - 2.0 * linear + cache.outcome_squares[i])
            / (cache.n * cache.window_sizes[i])
        )
    return float(np.mean(losses) + _temporal_penalty(tensor, cache, lambda_t))


def complete_objective_gradient(
    theta: np.ndarray, cache: GramCache, *, lambda_t: float = 0.0
) -> np.ndarray:
    tensor = _require_tensor(theta, (cache.n, 2 * cache.n, len(cache.dates)))
    d = tensor.shape[2]
    gradient = np.empty_like(tensor)
    for i in range(d):
        gradient[:, :, i] = (
            2.0
            * (tensor[:, :, i] @ cache.grams[i] - cache.cross_products[i])
            / (d * cache.n * cache.window_sizes[i])
        )
    if d >= 2 and lambda_t != 0.0:
        coefficient = lambda_t * cache.g_bar / (cache.n ** 2 * (d - 1))
        differences = np.diff(tensor, axis=2)
        gradient[:, :, 0] -= coefficient * differences[:, :, 0]
        gradient[:, :, -1] += coefficient * differences[:, :, -1]
        if d > 2:
            gradient[:, :, 1:-1] += coefficient * (
                differences[:, :, :-1] - differences[:, :, 1:]
            )
    return gradient


@dataclass(frozen=True)
class TuckerDecomposition:
    tensor: np.ndarray
    core: np.ndarray
    factors: tuple[np.ndarray, np.ndarray, np.ndarray]


def _signed_left_vectors(tensor: np.ndarray, mode: int, rank: int) -> np.ndarray:
    unfolded = np.moveaxis(tensor, mode, 0).reshape(tensor.shape[mode], -1)
    left, singular_values, _ = np.linalg.svd(unfolded, full_matrices=False)
    tie_tolerance = (
        SVD_TIE_TOLERANCE_MULTIPLIER
        * np.finfo(float).eps
        * max(float(singular_values[0]) if singular_values.size else 0.0, 1.0)
    )
    canonical: list[np.ndarray] = []
    block_start = 0
    while block_start < singular_values.size and len(canonical) < rank:
        block_end = block_start + 1
        while (
            block_end < singular_values.size
            and abs(float(singular_values[block_end] - singular_values[block_start]))
            <= tie_tolerance
        ):
            block_end += 1
        block = left[:, block_start:block_end]
        if block.shape[1] == 1:
            canonical.append(block[:, 0].copy())
        else:
            projector = block @ block.T
            block_basis: list[np.ndarray] = []
            for coordinate in range(projector.shape[0]):
                vector = projector[:, coordinate].copy()
                for _ in range(2):
                    for prior in block_basis:
                        vector -= float(prior @ vector) * prior
                norm = float(np.linalg.norm(vector))
                if norm <= tie_tolerance:
                    continue
                vector /= norm
                pivot = int(np.argmax(np.abs(vector)))
                if vector[pivot] < 0.0:
                    vector *= -1.0
                block_basis.append(vector)
                if len(block_basis) == block.shape[1]:
                    break
            if len(block_basis) != block.shape[1]:
                raise FloatingPointError("could not canonicalize tied Tucker subspace")
            canonical.extend(block_basis)
        block_start = block_end
    vectors = np.column_stack(canonical[:rank])
    for column in range(vectors.shape[1]):
        values = vectors[:, column]
        pivot = int(np.argmax(np.abs(values)))
        if values[pivot] < 0.0:
            vectors[:, column] *= -1.0
        norm = float(np.linalg.norm(vectors[:, column]))
        if not math.isfinite(norm) or norm <= 1e-12:
            raise FloatingPointError("degenerate Tucker factor")
        vectors[:, column] /= norm
    return vectors


def project_tucker333(
    tensor: np.ndarray,
    rank: int = TUCKER_RANK,
    *,
    return_decomposition: bool = False,
) -> np.ndarray | TuckerDecomposition:
    value = np.asarray(tensor, dtype=float)
    if value.ndim != 3 or not np.all(np.isfinite(value)):
        raise ValueError("Tucker input must be a finite three-dimensional tensor")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank <= 0:
        raise ValueError("rank must be a positive integer")
    ranks = tuple(min(rank, dimension) for dimension in value.shape)
    factors = tuple(
        _signed_left_vectors(value, mode, ranks[mode]) for mode in range(3)
    )
    factor_a, factor_b, factor_c = factors
    core = np.einsum(
        "ia,jb,kc,ijk->abc", factor_a, factor_b, factor_c, value,
        optimize=True,
    )
    projected = np.einsum(
        "ia,jb,kc,abc->ijk", factor_a, factor_b, factor_c, core,
        optimize=True,
    )
    decomposition = TuckerDecomposition(
        tensor=_readonly(projected),
        core=_readonly(core),
        factors=tuple(_readonly(factor) for factor in factors),
    )
    return decomposition if return_decomposition else decomposition.tensor


def anchor_split_tucker_prefix(anchor_tensor: np.ndarray, *, n: int, rank: int = 3) -> np.ndarray:
    anchor = np.asarray(anchor_tensor, dtype=float)
    if anchor.ndim != 3 or anchor.shape[:2] != (n, 2 * n):
        raise ValueError("anchor tensor has incompatible dimensions")
    m_ref = _tucker_reconstruct(anchor[:, :n, :], rank)
    slope = _tucker_reconstruct(anchor[:, n:, :], rank)
    return np.asarray(project_tucker333(np.concatenate([m_ref, slope], axis=1), rank))


@dataclass(frozen=True)
class OptimizerStart:
    start_index: int
    seed: int | None
    key: tuple[int, int, int, int] | None
    pre_projection_tensor: np.ndarray
    tensor: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "pre_projection_tensor", _readonly(
            np.asarray(self.pre_projection_tensor, dtype=float)
        ))
        object.__setattr__(self, "tensor", _readonly(np.asarray(self.tensor, dtype=float)))


def make_optimizer_starts(
    anchor_tensor: np.ndarray,
    *,
    method_seed: int,
    prefix_end_date: int,
    lambda_grid_index: int,
    rank: int = TUCKER_RANK,
) -> tuple[OptimizerStart, OptimizerStart, OptimizerStart]:
    anchor = np.asarray(anchor_tensor, dtype=float)
    if anchor.ndim != 3 or not np.all(np.isfinite(anchor)):
        raise ValueError("anchor start must be a finite three-dimensional tensor")
    theta_zero = anchor
    starts: list[OptimizerStart] = [OptimizerStart(
        start_index=0,
        seed=None,
        key=None,
        pre_projection_tensor=_readonly(anchor),
        tensor=_readonly(theta_zero),
    )]
    perturbation_norm = 0.05 * max(float(np.linalg.norm(theta_zero)), 1.0)
    for start_index in (1, 2):
        key = (int(method_seed), int(prefix_end_date), int(lambda_grid_index), start_index)
        seed = keyed_seed(*key)
        gaussian = np.random.default_rng(seed).normal(size=theta_zero.shape)
        perturbation = perturbation_norm * gaussian / max(
            float(np.linalg.norm(gaussian)), 1e-12
        )
        before_projection = theta_zero + perturbation
        starts.append(OptimizerStart(
            start_index=start_index,
            seed=seed,
            key=key,
            pre_projection_tensor=_readonly(before_projection),
            tensor=_readonly(project_tucker333(before_projection, rank)),
        ))
    return tuple(starts)  # type: ignore[return-value]


@dataclass(frozen=True)
class BacktrackingResult:
    accepted: bool
    tensor: np.ndarray
    objective: float
    step_size: float | None
    trials: int


def backtracking_projected_step(
    theta: np.ndarray,
    gradient: np.ndarray,
    *,
    prior_objective: float,
    objective: Callable[[np.ndarray], float],
    rank: int = TUCKER_RANK,
    projector: Callable[[np.ndarray, int], np.ndarray] = project_tucker333,
) -> BacktrackingResult:
    current = np.asarray(theta, dtype=float)
    direction = np.asarray(gradient, dtype=float)
    for trial, alpha in enumerate(BACKTRACKING_STEPS, start=1):
        try:
            projected = np.asarray(projector(current - alpha * direction, rank), dtype=float)
            value = float(objective(projected))
        except (FloatingPointError, ValueError, np.linalg.LinAlgError):
            continue
        if math.isfinite(value) and value <= prior_objective + 1e-12:
            return BacktrackingResult(True, _readonly(projected), value, alpha, trial)
    return BacktrackingResult(False, _readonly(current), float(prior_objective), None, 25)


def relative_improvement(old: float, new: float) -> float:
    return float((old - new) / max(abs(old), 1e-12))


def projected_gradient_proxy(
    theta: np.ndarray,
    gradient: np.ndarray,
    *,
    rank: int = TUCKER_RANK,
    projector: Callable[[np.ndarray, int], np.ndarray] = project_tucker333,
) -> float:
    current = np.asarray(theta, dtype=float)
    projected = np.asarray(projector(current - np.asarray(gradient), rank), dtype=float)
    return float(np.linalg.norm(current - projected) / max(np.linalg.norm(current), 1.0))


def classify_stopping(
    *,
    relative_improvements: Iterable[float],
    stationarity: float,
    iteration: int,
    max_iterations: int,
    backtrack_failed: bool,
    numerical_failed: bool,
    objective_tolerance: float = 1e-6,
    stationarity_tolerance: float = 1e-4,
) -> tuple[str, bool] | None:
    if numerical_failed or not math.isfinite(stationarity):
        return "NUMERICAL_FAIL", False
    if stationarity <= stationarity_tolerance:
        return "STATIONARITY", True
    recent = tuple(relative_improvements)[-5:]
    if len(recent) == 5 and all(
        math.isfinite(value) and 0.0 <= value < objective_tolerance
        for value in recent
    ):
        return "OBJECTIVE_TOLERANCE", True
    if backtrack_failed:
        return "BACKTRACK_FAIL", False
    if iteration >= max_iterations:
        return "ITERATION_CAP", False
    return None


@dataclass(frozen=True)
class OptimizerStartResult:
    start_index: int
    tensor: np.ndarray
    initial_objective: float
    final_objective: float
    objective_trace: tuple[float, ...]
    accepted_step_sizes: tuple[float, ...]
    iteration_count: int
    stationarity_proxy: float
    stopping_reason: str
    converged: bool
    runtime_seconds: float
    pairwise_solution_distances: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tensor", _readonly(np.asarray(self.tensor, dtype=float)))
        object.__setattr__(self, "objective_trace", tuple(self.objective_trace))
        object.__setattr__(self, "accepted_step_sizes", tuple(self.accepted_step_sizes))
        object.__setattr__(
            self,
            "pairwise_solution_distances",
            tuple(self.pairwise_solution_distances),
        )


class NoConvergedStartError(RuntimeError):
    def __init__(
        self,
        message: str,
        start_results: Iterable[OptimizerStartResult] = (),
    ) -> None:
        super().__init__(message)
        object.__setattr__(self, "_start_results", tuple(start_results))
        object.__setattr__(self, "_records_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_records_locked", False):
            raise AttributeError("optimizer failure records are immutable")
        object.__setattr__(self, name, value)

    @property
    def start_results(self) -> tuple[OptimizerStartResult, ...]:
        return self._start_results


def synthetic_start_result(
    start_index: int, objective: float, *, converged: bool
) -> OptimizerStartResult:
    return OptimizerStartResult(
        start_index=start_index,
        tensor=_readonly(np.asarray([[[float(start_index)]]])),
        initial_objective=float(objective),
        final_objective=float(objective),
        objective_trace=(float(objective),),
        accepted_step_sizes=(),
        iteration_count=0,
        stationarity_proxy=0.0 if converged else 1.0,
        stopping_reason="STATIONARITY" if converged else "ITERATION_CAP",
        converged=converged,
        runtime_seconds=0.0,
    )


def select_optimizer_start(starts: Iterable[OptimizerStartResult]) -> OptimizerStartResult:
    eligible = [
        start for start in starts
        if start.converged and math.isfinite(start.final_objective)
    ]
    if not eligible:
        raise NoConvergedStartError("no finite converged optimizer start")
    return min(eligible, key=lambda item: (item.final_objective, item.start_index))


def _optimize_start(
    start: OptimizerStart,
    cache: GramCache,
    *,
    lambda_t: float,
    rank: int,
    max_iterations: int,
    objective_tolerance: float,
    stationarity_tolerance: float,
) -> OptimizerStartResult:
    started = time.perf_counter()
    theta = np.asarray(start.tensor, dtype=float)
    objective = lambda value: normalized_gram_loss(value, cache, lambda_t=lambda_t)
    initial = objective(theta)
    trace = [initial]
    steps: list[float] = []
    improvements: list[float] = []
    stationarity = math.inf
    stopping_reason = "NUMERICAL_FAIL"
    converged = False
    iteration_count = 0

    if math.isfinite(initial):
        gradient = complete_objective_gradient(theta, cache, lambda_t=lambda_t)
        if np.all(np.isfinite(gradient)):
            try:
                stationarity = projected_gradient_proxy(theta, gradient, rank=rank)
            except (FloatingPointError, ValueError, np.linalg.LinAlgError):
                stationarity = math.nan
            initial_stop = classify_stopping(
                relative_improvements=improvements,
                stationarity=stationarity,
                iteration=0,
                max_iterations=max_iterations,
                backtrack_failed=False,
                numerical_failed=False,
                objective_tolerance=objective_tolerance,
                stationarity_tolerance=stationarity_tolerance,
            )
            if initial_stop is not None:
                stopping_reason, converged = initial_stop
            else:
                for iteration in range(1, max_iterations + 1):
                    iteration_count = iteration
                    gradient = complete_objective_gradient(theta, cache, lambda_t=lambda_t)
                    if not np.all(np.isfinite(gradient)):
                        stopping_reason = "NUMERICAL_FAIL"
                        break
                    trial = backtracking_projected_step(
                        theta, gradient, prior_objective=trace[-1],
                        objective=objective, rank=rank,
                    )
                    if not trial.accepted:
                        stopping_reason = "BACKTRACK_FAIL"
                        break
                    previous = trace[-1]
                    theta = np.asarray(trial.tensor)
                    trace.append(trial.objective)
                    steps.append(float(trial.step_size))
                    improvements.append(relative_improvement(previous, trial.objective))
                    next_gradient = complete_objective_gradient(theta, cache, lambda_t=lambda_t)
                    numerical = not np.all(np.isfinite(next_gradient))
                    if numerical:
                        stationarity = math.nan
                    else:
                        try:
                            stationarity = projected_gradient_proxy(
                                theta, next_gradient, rank=rank
                            )
                        except (FloatingPointError, ValueError, np.linalg.LinAlgError):
                            stationarity = math.nan
                            numerical = True
                    decision = classify_stopping(
                        relative_improvements=improvements,
                        stationarity=stationarity,
                        iteration=iteration,
                        max_iterations=max_iterations,
                        backtrack_failed=False,
                        numerical_failed=numerical,
                        objective_tolerance=objective_tolerance,
                        stationarity_tolerance=stationarity_tolerance,
                    )
                    if decision is not None:
                        stopping_reason, converged = decision
                        break
    return OptimizerStartResult(
        start_index=start.start_index,
        tensor=_readonly(theta),
        initial_objective=float(initial),
        final_objective=float(trace[-1]),
        objective_trace=tuple(float(value) for value in trace),
        accepted_step_sizes=tuple(steps),
        iteration_count=iteration_count,
        stationarity_proxy=float(stationarity),
        stopping_reason=stopping_reason,
        converged=converged,
        runtime_seconds=time.perf_counter() - started,
    )


@dataclass(frozen=True)
class PrefixOptimization:
    starts: tuple[OptimizerStartResult, OptimizerStartResult, OptimizerStartResult]
    selected_start_index: int

    @property
    def selected(self) -> OptimizerStartResult:
        return self.starts[self.selected_start_index]


def optimize_dw_tucker_prefix(
    fit: FitInputs,
    *,
    anchor_tensor: np.ndarray,
    lambda_t: float,
    rank: int,
    method_seed: int,
    prefix_end_date: int,
    lambda_grid_index: int,
    max_iterations: int = 300,
    objective_tolerance: float = 1e-6,
    stationarity_tolerance: float = 1e-4,
) -> PrefixOptimization:
    cache = build_gram_cache(fit)
    expected = (cache.n, 2 * cache.n, len(cache.dates))
    anchor = _require_tensor(anchor_tensor, expected)
    starts = make_optimizer_starts(
        anchor,
        method_seed=method_seed,
        prefix_end_date=prefix_end_date,
        lambda_grid_index=lambda_grid_index,
        rank=rank,
    )
    results = tuple(
        _optimize_start(
            start, cache, lambda_t=lambda_t, rank=rank,
            max_iterations=max_iterations,
            objective_tolerance=objective_tolerance,
            stationarity_tolerance=stationarity_tolerance,
        )
        for start in starts
    )
    distances = tuple(tuple(
        float(np.linalg.norm(left.tensor - right.tensor)) for right in results
    ) for left in results)
    with_distances = tuple(
        replace(result, pairwise_solution_distances=distances[index])
        for index, result in enumerate(results)
    )
    try:
        selected = select_optimizer_start(with_distances)
    except NoConvergedStartError as error:
        raise NoConvergedStartError(str(error), with_distances) from None
    return PrefixOptimization(
        starts=with_distances,  # type: ignore[arg-type]
        selected_start_index=selected.start_index,
    )


def prefix_fit_inputs(fit: FitInputs, final_position: int) -> FitInputs:
    if not 0 <= int(final_position) < len(fit.coefficient_dates):
        raise ValueError("final_position does not index the coefficient path")
    final_date = int(fit.coefficient_dates[int(final_position)])
    return FitInputs(
        predictors=fit.predictors[: final_date + 1],
        outcomes=fit.outcomes[: final_date + 1],
        topology=fit.topology[: final_date + 1],
        w_ref=fit.w_ref,
        coefficient_dates=fit.coefficient_dates[: int(final_position) + 1],
    )


def _observed_residual(coefficient: np.ndarray, fit: FitInputs, position: int) -> np.ndarray:
    date = int(fit.coefficient_dates[position])
    n = fit.predictors.shape[1]
    m_ref = coefficient[:, :n]
    slope = coefficient[:, n:]
    observed = m_ref + slope @ (fit.topology[date] - fit.w_ref)
    return np.asarray(fit.outcomes[date] - observed @ fit.predictors[date])


def _finite_json(value: float) -> float | None:
    return float(value) if math.isfinite(value) else None


def _start_diagnostic(start: OptimizerStartResult) -> dict[str, object]:
    return {
        "start_index": start.start_index,
        "initial_objective": _finite_json(start.initial_objective),
        "final_objective": _finite_json(start.final_objective),
        "objective_trace": [_finite_json(value) for value in start.objective_trace],
        "accepted_step_sizes": list(start.accepted_step_sizes),
        "iteration_count": start.iteration_count,
        "stationarity_proxy": _finite_json(start.stationarity_proxy),
        "stopping_reason": start.stopping_reason,
        "converged": start.converged,
        "runtime_seconds": start.runtime_seconds,
        "pairwise_solution_distances": list(start.pairwise_solution_distances),
    }


def _prefix_diagnostic(result: PrefixOptimization, position: int) -> dict[str, object]:
    return {
        "position": position,
        "selected_start_index": result.selected_start_index,
        "starts": [_start_diagnostic(start) for start in result.starts],
    }


def _annotated_prefix_diagnostic(
    result: PrefixOptimization,
    *,
    phase: str,
    lambda_t: float,
    lambda_grid_index: int,
    position: int,
    date: int,
) -> dict[str, object]:
    return {
        "phase": phase,
        "lambda_t": lambda_t,
        "lambda_grid_index": lambda_grid_index,
        "date": date,
        **_prefix_diagnostic(result, position),
    }


class _PrefixOptimizationFailure(RuntimeError):
    def __init__(
        self,
        *,
        phase: str,
        lambda_t: float,
        lambda_grid_index: int,
        position: int,
        date: int,
        completed_prefixes: list[dict[str, object]],
        error: NoConvergedStartError,
    ) -> None:
        super().__init__(
            f"no finite converged optimizer start during {phase} "
            f"at position {position}, date {date}, lambda_T={lambda_t}"
        )
        self.diagnostics = {
            "phase": phase,
            "lambda_t": lambda_t,
            "lambda_grid_index": lambda_grid_index,
            "position": position,
            "date": date,
            "completed_prefixes": list(completed_prefixes),
            "failing_prefix": {
                "phase": phase,
                "lambda_t": lambda_t,
                "lambda_grid_index": lambda_grid_index,
                "position": position,
                "date": date,
                "selected_start_index": None,
                "starts": [_start_diagnostic(start) for start in error.start_results],
            },
        }


def _failure_path(config: R006EConfig, error: Exception, runtime: float, method_seed: int) -> FittedPath:
    dates = list(range(config.window + 84, config.t_len))
    diagnostics: dict[str, object] = {
        "status": "failure",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "method_seed": method_seed,
        "intended_dates": dates,
        "intended_count": len(dates),
        "expected_tensor_shape": [config.n, 2 * config.n, len(dates)],
        "validation_positions": VALIDATION_POSITIONS,
        "validation_count": 24,
        "evaluation_positions": EVALUATION_POSITIONS,
        "evaluation_count": 36,
        "svd_tie_tolerance_formula": SVD_TIE_TOLERANCE_FORMULA,
    }
    if isinstance(error, _PrefixOptimizationFailure):
        diagnostics["error_type"] = "NoConvergedStartError"
        diagnostics["optimizer_failure"] = error.diagnostics
    return FittedPath(
        method="dw_joint_tucker333",
        parameterization="anchor",
        tensor=np.zeros((config.n, 2 * config.n, 0)),
        dates=np.asarray([], dtype=int),
        selected_penalty=None,
        diagnostics=diagnostics,
        runtime_seconds=max(runtime, 0.0),
    )


def fit_dw_joint_tucker(
    fit: FitInputs, *, config: R006EConfig, method_seed: int
) -> FittedPath:
    if not isinstance(config, R006EConfig):
        raise TypeError("config must be a frozen R006e record")
    started = time.perf_counter()
    try:
        if not isinstance(fit, FitInputs):
            raise TypeError("fit must be a frozen R006e record")
        if not isinstance(method_seed, int) or isinstance(method_seed, bool):
            raise TypeError("method_seed must be an integer")
        if config.temporal_penalties != TEMPORAL_PENALTIES:
            raise ValueError("temporal penalty grid differs from the frozen protocol")
        if config.fitted_rank != TUCKER_RANK or config.optimizer_starts != 3:
            raise ValueError("candidate requires rank (3,3,3) and exactly three starts")
        if config.optimizer_iterations != 300:
            raise ValueError("optimizer_iterations must equal 300")
        if config.objective_tolerance != 1e-6:
            raise ValueError("objective_tolerance must equal 1e-6")
        if config.stationarity_tolerance != 1e-4:
            raise ValueError("stationarity_tolerance must equal 1e-4")
        expected_dates = np.arange(config.window, config.t_len, dtype=int)
        if fit.predictors.shape != (config.t_len, config.n):
            raise ValueError("fit dimensions do not match config")
        if not np.array_equal(fit.coefficient_dates, expected_dates):
            raise ValueError("fit does not contain the frozen coefficient dates")

        local = fit_anchor_local(fit, config=config).require_success().tensor
        validation_records: dict[str, object] = {}
        candidates: list[tuple[float, float, int]] = []
        completed_prefixes: list[dict[str, object]] = []
        for lambda_grid_index, lambda_t in enumerate(TEMPORAL_PENALTIES):
            residuals: list[np.ndarray] = []
            prefix_records: list[dict[str, object]] = []
            for position in VALIDATION_POSITIONS:
                prefix = prefix_fit_inputs(fit, position)
                anchor = anchor_split_tucker_prefix(
                    local[:, :, : position + 1], n=config.n, rank=TUCKER_RANK
                )
                date = int(fit.coefficient_dates[position])
                try:
                    result = optimize_dw_tucker_prefix(
                        prefix,
                        anchor_tensor=anchor,
                        lambda_t=lambda_t,
                        rank=TUCKER_RANK,
                        method_seed=method_seed,
                        prefix_end_date=date,
                        lambda_grid_index=lambda_grid_index,
                        max_iterations=config.optimizer_iterations,
                        objective_tolerance=config.objective_tolerance,
                        stationarity_tolerance=config.stationarity_tolerance,
                    )
                except NoConvergedStartError as error:
                    raise _PrefixOptimizationFailure(
                        phase="validation",
                        lambda_t=lambda_t,
                        lambda_grid_index=lambda_grid_index,
                        position=position,
                        date=date,
                        completed_prefixes=completed_prefixes,
                        error=error,
                    ) from None
                residuals.append(_observed_residual(result.selected.tensor[:, :, -1], fit, position))
                record = _annotated_prefix_diagnostic(
                    result,
                    phase="validation",
                    lambda_t=lambda_t,
                    lambda_grid_index=lambda_grid_index,
                    position=position,
                    date=date,
                )
                prefix_records.append(record)
                completed_prefixes.append(record)
            pooled = float(np.sqrt(np.mean(np.square(np.concatenate(residuals)))))
            validation_records[f"{lambda_t:.12g}"] = {
                "pooled_rmse": pooled,
                "prefixes": prefix_records,
            }
            candidates.append((pooled, lambda_t, lambda_grid_index))
        _, selected_lambda, selected_grid_index = min(
            candidates, key=lambda value: (value[0], value[1])
        )

        slices: list[np.ndarray] = []
        evaluation_records: list[dict[str, object]] = []
        for position in EVALUATION_POSITIONS:
            prefix = prefix_fit_inputs(fit, position)
            anchor = anchor_split_tucker_prefix(
                local[:, :, : position + 1], n=config.n, rank=TUCKER_RANK
            )
            date = int(fit.coefficient_dates[position])
            try:
                result = optimize_dw_tucker_prefix(
                    prefix,
                    anchor_tensor=anchor,
                    lambda_t=selected_lambda,
                    rank=TUCKER_RANK,
                    method_seed=method_seed,
                    prefix_end_date=date,
                    lambda_grid_index=selected_grid_index,
                    max_iterations=config.optimizer_iterations,
                    objective_tolerance=config.objective_tolerance,
                    stationarity_tolerance=config.stationarity_tolerance,
                )
            except NoConvergedStartError as error:
                raise _PrefixOptimizationFailure(
                    phase="evaluation",
                    lambda_t=selected_lambda,
                    lambda_grid_index=selected_grid_index,
                    position=position,
                    date=date,
                    completed_prefixes=completed_prefixes,
                    error=error,
                ) from None
            slices.append(result.selected.tensor[:, :, -1])
            record = _annotated_prefix_diagnostic(
                result,
                phase="evaluation",
                lambda_t=selected_lambda,
                lambda_grid_index=selected_grid_index,
                position=position,
                date=date,
            )
            evaluation_records.append(record)
            completed_prefixes.append(record)
        return FittedPath(
            method="dw_joint_tucker333",
            parameterization="anchor",
            tensor=np.stack(slices, axis=2),
            dates=fit.coefficient_dates[list(EVALUATION_POSITIONS)],
            selected_penalty=selected_lambda,
            diagnostics={
                "status": "success",
                "method_seed": method_seed,
                "rank": [3, 3, 3],
                "temporal_penalties": TEMPORAL_PENALTIES,
                "validation_positions": VALIDATION_POSITIONS,
                "validation_count": 24,
                "validation": validation_records,
                "evaluation_positions": EVALUATION_POSITIONS,
                "evaluation_count": 36,
                "evaluation": evaluation_records,
                "strict_rolling_prefix": True,
                "observed_topology_pooled_rmse": True,
                "svd_tie_tolerance_formula": SVD_TIE_TOLERANCE_FORMULA,
            },
            runtime_seconds=time.perf_counter() - started,
        )
    except Exception as error:
        return _failure_path(config, error, time.perf_counter() - started, method_seed)


def fixture_benchmark() -> None:
    shape = (6, 12, 18)
    theta = np.sin(np.arange(np.prod(shape), dtype=float)).reshape(shape) / 20.0
    gradient = np.cos(np.arange(np.prod(shape), dtype=float)).reshape(shape) / 100.0
    iterations = 12
    started = time.perf_counter()
    for _ in range(iterations):
        theta = np.asarray(project_tucker333(theta - gradient, 3))
    elapsed = max(time.perf_counter() - started, 1e-12)
    prefix_fits = 4 * len(VALIDATION_POSITIONS) + len(EVALUATION_POSITIONS)
    starts = 3 * prefix_fits
    optimizer_iteration_budget = starts * 300
    full_cap_first_trial_calls = starts + 2 * optimizer_iteration_budget
    full_cap_worst_case_calls = starts + 26 * optimizer_iteration_budget
    print(
        "OUTCOME_FREE_FIXTURE "
        "fixture_shape=6x12x18 fixture_iterations=12 "
        "benchmark_n=6 "
        "projection_only=true not_formal_runtime_evidence=true "
        "excluded_overhead=gram+objective+backtracking "
        f"iterations_per_second={iterations / elapsed:.6f} "
        f"iterations/sec={iterations / elapsed:.6f} "
        f"optimizer_iteration_budget={optimizer_iteration_budget} "
        f"full_cap_first_trial_projection_calls={full_cap_first_trial_calls} "
        f"full_cap_worst_case_projection_calls={full_cap_worst_case_calls} "
        "extrapolation_basis=3_starts_x_(4x24+36)_prefixes_x_300_cap"
    )


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-benchmark", action="store_true")
    arguments = parser.parse_args()
    if arguments.fixture_benchmark:
        fixture_benchmark()
    else:
        parser.error("only --fixture-benchmark is supported")


if __name__ == "__main__":
    _main()
