"""Audited response metrics for the high-impact revision experiments."""

from __future__ import annotations

import numpy as np


def _as_square_matrix(matrix: np.ndarray) -> np.ndarray:
    array = np.asarray(matrix, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("response operators must be square matrices")
    return array


def spectral_radius(matrix: np.ndarray) -> float:
    """Return the largest absolute eigenvalue of a square matrix."""
    array = _as_square_matrix(matrix)
    if array.shape[0] == 0:
        return 0.0
    return float(np.max(np.abs(np.linalg.eigvals(array))))


def _finite_horizon_response_error(
    true_matrix: np.ndarray,
    estimated_matrix: np.ndarray,
    horizon: int,
) -> float:
    dimension = true_matrix.shape[0]
    true_power = np.eye(dimension)
    estimated_power = np.eye(dimension)
    total_error = 0.0

    for _ in range(horizon + 1):
        total_error += float(np.sum(np.abs(true_power - estimated_power)))
        true_power = true_matrix @ true_power
        estimated_power = estimated_matrix @ estimated_power

    return total_error / (dimension * (horizon + 1))


def _project_to_radius(matrix: np.ndarray, target: float) -> tuple[np.ndarray, bool]:
    radius = spectral_radius(matrix)
    if radius > target:
        return matrix * (target / radius), True
    return matrix.copy(), False


def evaluate_response_pair(
    true_matrix: np.ndarray,
    estimated_matrix: np.ndarray,
    horizon: int,
    stability_threshold: float,
    projection_target: float | None = None,
) -> dict[str, float | bool | None]:
    """Evaluate raw, stability-qualified and optional projected responses."""
    truth = _as_square_matrix(true_matrix)
    estimate = _as_square_matrix(estimated_matrix)
    if truth.shape != estimate.shape:
        raise ValueError("true and estimated operators must have the same shape")
    if not isinstance(horizon, (int, np.integer)) or horizon < 0:
        raise ValueError("horizon must be a non-negative integer")
    if stability_threshold <= 0:
        raise ValueError("stability_threshold must be positive")
    if projection_target is not None and projection_target <= 0:
        raise ValueError("projection_target must be positive")

    true_radius = spectral_radius(truth)
    estimated_radius = spectral_radius(estimate)
    raw_error = _finite_horizon_response_error(truth, estimate, int(horizon))
    stability_qualified = (
        true_radius < stability_threshold
        and estimated_radius < stability_threshold
    )

    projected_error = None
    projection_applied = False
    if projection_target is not None:
        projected_truth, truth_projected = _project_to_radius(truth, projection_target)
        projected_estimate, estimate_projected = _project_to_radius(
            estimate, projection_target
        )
        projected_error = _finite_horizon_response_error(
            projected_truth, projected_estimate, int(horizon)
        )
        projection_applied = truth_projected or estimate_projected

    return {
        "true_spectral_radius": true_radius,
        "estimated_spectral_radius": estimated_radius,
        "raw_response_error": raw_error,
        "stability_qualified_error": raw_error if stability_qualified else None,
        "stability_qualified": stability_qualified,
        "projected_sensitivity_error": projected_error,
        "projection_applied": projection_applied,
    }
