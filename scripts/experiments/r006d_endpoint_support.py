"""Construction-only topology support utilities for R006d."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class ChronologicalRegions:
    calibration: np.ndarray
    validation: np.ndarray
    evaluation: np.ndarray


@dataclass(frozen=True)
class SupportCertificate:
    chi: float
    tau: float
    singular_values: np.ndarray
    retained_rank: int
    projector: np.ndarray


@dataclass(frozen=True)
class SupportPath:
    dates: np.ndarray
    chi: np.ndarray
    tau: np.ndarray
    retained_rank: np.ndarray
    singular_values: tuple[np.ndarray, ...]

    @property
    def maximum_chi(self) -> float:
        return float(np.max(self.chi))

    @property
    def median_chi(self) -> float:
        return float(np.median(self.chi))


@dataclass(frozen=True)
class DesignSupportPath:
    dates: np.ndarray
    tau: np.ndarray
    retained_rank: np.ndarray
    singular_values: tuple[np.ndarray, ...]
    projectors: tuple[np.ndarray, ...]


def chronological_regions(
    *,
    t_len: int,
    window: int,
    validation_fraction: float,
    evaluation_fraction: float,
) -> ChronologicalRegions:
    if not 0 < window < t_len:
        raise ValueError("window must leave post-warmup dates")
    if not 0.0 <= validation_fraction < 1.0:
        raise ValueError("validation_fraction must lie in [0, 1)")
    if not 0.0 <= evaluation_fraction < 1.0:
        raise ValueError("evaluation_fraction must lie in [0, 1)")

    dates = np.arange(window, t_len, dtype=int)
    validation_count = int(np.ceil(validation_fraction * len(dates)))
    evaluation_count = int(np.ceil(evaluation_fraction * len(dates)))
    calibration_count = len(dates) - validation_count - evaluation_count
    if calibration_count <= 0:
        raise ValueError("calibration region must contain at least one date")

    validation_stop = calibration_count + validation_count
    return ChronologicalRegions(
        calibration=dates[:calibration_count],
        validation=dates[calibration_count:validation_stop],
        evaluation=dates[validation_stop:],
    )


def certificate_from_design(
    direct_design: np.ndarray,
    topology_design: np.ndarray,
    delta_w: np.ndarray,
    *,
    kappa_max: float = 50.0,
    absolute_floor: float = 1e-10,
) -> SupportCertificate:
    x = np.asarray(direct_design, dtype=float)
    z = np.asarray(topology_design, dtype=float)
    delta = np.asarray(delta_w, dtype=float)
    if x.ndim != 2 or z.ndim != 2 or x.shape[0] != z.shape[0]:
        raise ValueError("direct and topology designs must be aligned matrices")
    if delta.shape != (z.shape[1], z.shape[1]):
        raise ValueError("delta_w must be square with topology-design width")
    if not np.isfinite(kappa_max) or kappa_max <= 1.0:
        raise ValueError("kappa_max must be finite and exceed one")
    if absolute_floor <= 0.0:
        raise ValueError("absolute_floor must be positive")

    projection_coefficients, *_ = np.linalg.lstsq(x, z, rcond=None)
    residual = z - x @ projection_coefficients
    _, singular_values, right_vectors = np.linalg.svd(
        residual, full_matrices=False
    )
    s_max = float(singular_values[0]) if singular_values.size else 0.0
    tau = max(float(absolute_floor), s_max / float(kappa_max))
    retained = singular_values >= tau
    retained_vectors = right_vectors[retained]
    projector = retained_vectors.T @ retained_vectors

    denominator = max(float(np.linalg.norm(delta)), 1e-12)
    unsupported = delta.T @ (np.eye(z.shape[1]) - projector)
    chi = float(np.linalg.norm(unsupported) / denominator)
    return SupportCertificate(
        chi=chi,
        tau=tau,
        singular_values=singular_values,
        retained_rank=int(np.count_nonzero(retained)),
        projector=projector,
    )


def support_path(
    predictors: np.ndarray,
    topology: np.ndarray,
    w_ref: np.ndarray,
    w_star: np.ndarray,
    dates: Sequence[int] | np.ndarray,
    *,
    window: int,
    kappa_max: float = 50.0,
    absolute_floor: float = 1e-10,
) -> SupportPath:
    design_path = build_design_support_path(
        predictors,
        topology,
        w_ref,
        dates,
        window=window,
        kappa_max=kappa_max,
        absolute_floor=absolute_floor,
    )
    return evaluate_query_path(design_path, w_ref, w_star)


def build_design_support_path(
    predictors: np.ndarray,
    topology: np.ndarray,
    w_ref: np.ndarray,
    dates: Sequence[int] | np.ndarray,
    *,
    window: int,
    kappa_max: float = 50.0,
    absolute_floor: float = 1e-10,
) -> DesignSupportPath:
    x = np.asarray(predictors, dtype=float)
    w = np.asarray(topology, dtype=float)
    reference = np.asarray(w_ref, dtype=float)
    selected_dates = np.asarray(dates, dtype=int)
    if x.ndim != 2:
        raise ValueError("predictors must be a matrix")
    n = x.shape[1]
    if w.shape != (x.shape[0], n, n):
        raise ValueError("topology has incompatible dimensions")
    if reference.shape != (n, n):
        raise ValueError("reference topology has incompatible dimensions")
    if selected_dates.ndim != 1 or selected_dates.size == 0:
        raise ValueError("dates must be a non-empty vector")
    if np.any(selected_dates < window) or np.any(selected_dates >= x.shape[0]):
        raise ValueError("dates must have complete rolling windows")

    certificates = []
    for date in selected_dates:
        direct = x[date - window : date]
        delta_topology = w[date - window : date] - reference[None, :, :]
        exposure = np.einsum(
            "tij,tj->ti", delta_topology, direct, optimize=True
        )
        certificates.append(
            certificate_from_design(
                direct,
                exposure,
                np.zeros((n, n)),
                kappa_max=kappa_max,
                absolute_floor=absolute_floor,
            )
        )

    return DesignSupportPath(
        dates=selected_dates.copy(),
        tau=np.asarray([item.tau for item in certificates], dtype=float),
        retained_rank=np.asarray(
            [item.retained_rank for item in certificates], dtype=int
        ),
        singular_values=tuple(item.singular_values for item in certificates),
        projectors=tuple(item.projector for item in certificates),
    )


def evaluate_query_path(
    design_path: DesignSupportPath,
    w_ref: np.ndarray,
    w_star: np.ndarray,
) -> SupportPath:
    reference = np.asarray(w_ref, dtype=float)
    target = np.asarray(w_star, dtype=float)
    if reference.shape != target.shape or reference.ndim != 2:
        raise ValueError("topology endpoints must be aligned matrices")
    delta = target - reference
    denominator = max(float(np.linalg.norm(delta)), 1e-12)
    identity = np.eye(reference.shape[0])
    chi = np.asarray(
        [
            np.linalg.norm(delta.T @ (identity - projector)) / denominator
            for projector in design_path.projectors
        ],
        dtype=float,
    )
    return SupportPath(
        dates=design_path.dates.copy(),
        chi=chi,
        tau=design_path.tau.copy(),
        retained_rank=design_path.retained_rank.copy(),
        singular_values=design_path.singular_values,
    )


def evaluate_candidate_pool(
    design_path: DesignSupportPath,
    w_ref: np.ndarray,
    candidates: np.ndarray,
) -> tuple[SupportPath, ...]:
    pool = np.asarray(candidates, dtype=float)
    reference = np.asarray(w_ref, dtype=float)
    if pool.ndim != 3 or pool.shape[1:] != reference.shape:
        raise ValueError("candidate pool has incompatible dimensions")
    return tuple(
        evaluate_query_path(design_path, reference, candidate)
        for candidate in pool
    )


def select_supported_index(
    maximum_chi: Sequence[float], *, threshold: float
) -> int | None:
    for index, value in enumerate(maximum_chi):
        if float(value) <= threshold:
            return index
    return None


def select_unsupported_index(
    *,
    median_chi: Sequence[float],
    maximum_chi: Sequence[float],
    median_threshold: float,
    maximum_threshold: float,
) -> int | None:
    if len(median_chi) != len(maximum_chi):
        raise ValueError("certificate summaries must have equal lengths")
    eligible = [
        index
        for index, (median_value, maximum_value) in enumerate(
            zip(median_chi, maximum_chi)
        )
        if float(median_value) >= median_threshold
        and float(maximum_value) >= maximum_threshold
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda index: (
            -float(median_chi[index]),
            -float(maximum_chi[index]),
            index,
        ),
    )


def _row_normalize_candidate(matrix: np.ndarray) -> np.ndarray:
    values = np.maximum(np.asarray(matrix, dtype=float), 0.0).copy()
    np.fill_diagonal(values, 0.0)
    for row in range(values.shape[0]):
        if float(values[row].sum()) <= 0.0:
            values[row, (row + 1) % values.shape[0]] = 1.0
    return values / values.sum(axis=1, keepdims=True)


def _degree_corrected_block_candidate(
    rng: np.random.Generator,
    *,
    n: int,
    within_probability: float,
    between_probability: float,
) -> np.ndarray:
    communities = np.arange(n) // (n // 4)
    source_degree = np.clip(rng.gamma(2.0, 0.5, size=n), 0.25, 2.5)
    target_degree = np.clip(rng.gamma(2.0, 0.5, size=n), 0.25, 2.5)
    base = np.where(
        communities[:, None] == communities[None, :],
        within_probability,
        between_probability,
    )
    probability = np.minimum(
        0.95, base * source_degree[:, None] * target_degree[None, :]
    )
    np.fill_diagonal(probability, 0.0)
    edges = rng.uniform(size=(n, n)) < probability
    weights = rng.gamma(2.0, 0.5, size=(n, n)) * edges
    return _row_normalize_candidate(weights)


def generate_family_pool(*, n: int, size: int, seed: int) -> np.ndarray:
    if n < 4 or n % 4 != 0:
        raise ValueError("n must be divisible by four")
    if size <= 0:
        raise ValueError("size must be positive")
    rng = np.random.default_rng(seed)
    return np.stack(
        [
            _degree_corrected_block_candidate(
                rng,
                n=n,
                within_probability=0.48,
                between_probability=0.12,
            )
            for _ in range(size)
        ]
    )


def _hub_candidate(
    rng: np.random.Generator, *, n: int, candidate_index: int
) -> np.ndarray:
    first_hub = candidate_index % n
    second_hub = (first_hub + max(1, n // 2)) % n
    hubs = np.zeros(n, dtype=bool)
    hubs[[first_hub, second_hub]] = True
    probability = np.where(
        hubs[:, None] | hubs[None, :],
        0.70,
        0.08,
    )
    np.fill_diagonal(probability, 0.0)
    edges = rng.uniform(size=(n, n)) < probability
    weights = rng.gamma(2.0, 0.5, size=(n, n)) * edges
    return _row_normalize_candidate(weights)


def generate_unsupported_pool(*, n: int, size: int, seed: int) -> np.ndarray:
    if n < 4 or n % 4 != 0:
        raise ValueError("n must be divisible by four")
    if size <= 0:
        raise ValueError("size must be positive")
    rng = np.random.default_rng(seed)
    block_count = size // 2
    candidates = [
        _degree_corrected_block_candidate(
            rng,
            n=n,
            within_probability=0.64,
            between_probability=0.08,
        )
        for _ in range(block_count)
    ]
    candidates.extend(
        _hub_candidate(rng, n=n, candidate_index=index)
        for index in range(size - block_count)
    )
    return np.stack(candidates)
