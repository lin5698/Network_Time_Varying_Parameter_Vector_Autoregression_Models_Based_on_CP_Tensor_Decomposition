"""Endpoint and mechanism metrics for R006c fitted objects."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

try:
    from scripts.experiments.high_impact_metrics import evaluate_response_pair
    from scripts.experiments.r006c_endpoint_estimators import FittedMethod
    from scripts.experiments.r006c_endpoint_protocol import (
        EndpointPanel,
        R006CConfig,
    )
except ModuleNotFoundError:  # Direct execution from scripts/experiments.
    from high_impact_metrics import evaluate_response_pair  # type: ignore
    from r006c_endpoint_estimators import FittedMethod  # type: ignore
    from r006c_endpoint_protocol import EndpointPanel, R006CConfig  # type: ignore


ENDPOINTS = ("w_ref", "w_alt_main", "w_alt_stress")
ENDPOINT_METRICS = (
    "operator_relative_error_mean",
    "operator_absolute_error_mean",
    "raw_response_error_mean",
    "response_zero_ratio_mean",
    "stability_qualified_error_mean",
    "stability_qualified_rate",
    "projected_sensitivity_error_mean",
    "estimated_spectral_radius_mean",
    "estimated_instability_rate",
)


def query_anchor(
    m_ref: np.ndarray,
    b: np.ndarray,
    w_ref: np.ndarray,
    endpoint: np.ndarray,
) -> np.ndarray:
    return m_ref + np.einsum(
        "tij,jk->tik", b, endpoint - w_ref, optimize=True
    )


def query_block(
    a: np.ndarray,
    b: np.ndarray,
    endpoint: np.ndarray,
) -> np.ndarray:
    return a + np.einsum("tij,jk->tik", b, endpoint, optimize=True)


def cancellation_index(
    delta_a: np.ndarray,
    delta_b: np.ndarray,
    w_ref: np.ndarray,
) -> float:
    numerator = float(
        np.linalg.norm(delta_a) + np.linalg.norm(delta_b @ w_ref)
    )
    denominator = float(np.linalg.norm(delta_a + delta_b @ w_ref))
    if numerator == 0.0 and denominator == 0.0:
        return 0.0
    return numerator / max(denominator, 1e-12)


def endpoint_availability(method: str) -> dict[str, bool]:
    alternatives_available = method != "collapsed_ref_tucker333"
    return {
        "w_ref": True,
        "w_alt_main": alternatives_available,
        "w_alt_stress": alternatives_available,
    }


def evaluate_endpoint_path(
    truth: np.ndarray,
    estimate: np.ndarray,
    *,
    horizon: int,
    stability_threshold: float,
    projection_target: float,
) -> dict[str, float | None]:
    true_path = np.asarray(truth, dtype=float)
    estimated_path = np.asarray(estimate, dtype=float)
    if true_path.ndim != 3 or true_path.shape != estimated_path.shape:
        raise ValueError("truth and estimate must be aligned operator paths")
    if true_path.shape[0] == 0:
        raise ValueError("endpoint path cannot be empty")

    relative_errors = []
    absolute_errors = []
    raw_errors = []
    zero_ratios = []
    qualified_errors = []
    projected_errors = []
    estimated_radii = []
    unstable = 0
    for truth_matrix, estimate_matrix in zip(true_path, estimated_path):
        absolute_error = float(np.linalg.norm(estimate_matrix - truth_matrix))
        absolute_errors.append(absolute_error)
        relative_errors.append(
            absolute_error / max(float(np.linalg.norm(truth_matrix)), 1e-12)
        )
        response = evaluate_response_pair(
            truth_matrix,
            estimate_matrix,
            horizon=horizon,
            stability_threshold=stability_threshold,
            projection_target=projection_target,
        )
        zero_response = evaluate_response_pair(
            truth_matrix,
            np.zeros_like(truth_matrix),
            horizon=horizon,
            stability_threshold=stability_threshold,
        )
        raw_error = float(response["raw_response_error"])
        raw_errors.append(raw_error)
        zero_ratios.append(
            raw_error
            / max(float(zero_response["raw_response_error"]), 1e-12)
        )
        if response["stability_qualified_error"] is not None:
            qualified_errors.append(
                float(response["stability_qualified_error"])
            )
        projected_errors.append(
            float(response["projected_sensitivity_error"])
        )
        estimated_radius = float(response["estimated_spectral_radius"])
        estimated_radii.append(estimated_radius)
        unstable += estimated_radius >= stability_threshold

    count = len(true_path)
    return {
        "operator_relative_error_mean": float(np.mean(relative_errors)),
        "operator_absolute_error_mean": float(np.mean(absolute_errors)),
        "raw_response_error_mean": float(np.mean(raw_errors)),
        "response_zero_ratio_mean": float(np.mean(zero_ratios)),
        "stability_qualified_error_mean": (
            float(np.mean(qualified_errors)) if qualified_errors else None
        ),
        "stability_qualified_rate": len(qualified_errors) / count,
        "projected_sensitivity_error_mean": float(np.mean(projected_errors)),
        "estimated_spectral_radius_mean": float(np.mean(estimated_radii)),
        "estimated_instability_rate": unstable / count,
    }


def _unavailable_endpoint(prefix: str) -> dict[str, Any]:
    row: dict[str, Any] = {f"{prefix}_available": 0}
    row.update({f"{prefix}_{name}": None for name in ENDPOINT_METRICS})
    return row


def _prefixed_endpoint(
    prefix: str,
    values: dict[str, float | None],
) -> dict[str, Any]:
    row: dict[str, Any] = {f"{prefix}_available": 1}
    row.update({f"{prefix}_{name}": value for name, value in values.items()})
    return row


def _cp_diagnostics(fitted: FittedMethod) -> dict[str, float | None]:
    output = {
        "cp_joint_best_relative_objective": None,
        "cp_joint_start_objective_spread": None,
        "cp_m_ref_best_relative_objective": None,
        "cp_m_ref_start_objective_spread": None,
        "cp_b_best_relative_objective": None,
        "cp_b_start_objective_spread": None,
    }
    diagnostics = fitted.reconstruction_diagnostics
    for source, prefix in (
        (diagnostics.get("joint"), "joint"),
        (diagnostics.get("M_ref"), "m_ref"),
        (diagnostics.get("B"), "b"),
    ):
        if isinstance(source, dict) and "best_relative_objective" in source:
            output[f"cp_{prefix}_best_relative_objective"] = float(
                source["best_relative_objective"]
            )
            output[f"cp_{prefix}_start_objective_spread"] = float(
                source["start_objective_spread"]
            )
    return output


def evaluate_fitted_method(
    fitted: FittedMethod,
    panel: EndpointPanel,
    config: R006CConfig,
) -> dict[str, Any]:
    evaluation_count = max(
        1, int(math.ceil(config.evaluation_fraction * len(fitted.indices)))
    )
    positions = np.arange(len(fitted.indices) - evaluation_count, len(fitted.indices))
    dates = fitted.indices[positions]
    tensor_path = np.moveaxis(fitted.tensor[:, :, positions], 2, 0)

    estimated_a = None
    estimated_b = None
    if fitted.parameterization == "block":
        estimated_a = tensor_path[:, :, : config.n]
        estimated_b = tensor_path[:, :, config.n :]
        endpoint_estimates = {
            "w_ref": query_block(estimated_a, estimated_b, panel.W_ref),
            "w_alt_main": query_block(
                estimated_a, estimated_b, panel.W_alt_main
            ),
            "w_alt_stress": query_block(
                estimated_a, estimated_b, panel.W_alt_stress
            ),
        }
    elif fitted.parameterization == "anchor":
        estimated_m_ref = tensor_path[:, :, : config.n]
        estimated_b = tensor_path[:, :, config.n :]
        estimated_a = estimated_m_ref - np.einsum(
            "tij,jk->tik", estimated_b, panel.W_ref, optimize=True
        )
        endpoint_estimates = {
            "w_ref": estimated_m_ref,
            "w_alt_main": query_anchor(
                estimated_m_ref,
                estimated_b,
                panel.W_ref,
                panel.W_alt_main,
            ),
            "w_alt_stress": query_anchor(
                estimated_m_ref,
                estimated_b,
                panel.W_ref,
                panel.W_alt_stress,
            ),
        }
    elif fitted.parameterization == "collapsed":
        endpoint_estimates = {"w_ref": tensor_path}
    else:
        raise ValueError(f"unknown parameterization {fitted.parameterization}")

    truth_m_ref = panel.M_ref[dates]
    truth_b = panel.B[dates]
    endpoint_truth = {
        "w_ref": truth_m_ref,
        "w_alt_main": query_anchor(
            truth_m_ref, truth_b, panel.W_ref, panel.W_alt_main
        ),
        "w_alt_stress": query_anchor(
            truth_m_ref, truth_b, panel.W_ref, panel.W_alt_stress
        ),
    }
    availability = endpoint_availability(fitted.name)
    row: dict[str, Any] = {}
    for endpoint in ENDPOINTS:
        if not availability[endpoint]:
            row.update(_unavailable_endpoint(endpoint))
            continue
        endpoint_values = evaluate_endpoint_path(
            endpoint_truth[endpoint],
            endpoint_estimates[endpoint],
            horizon=config.horizon,
            stability_threshold=config.stability_threshold,
            projection_target=config.projection_target,
        )
        row.update(_prefixed_endpoint(endpoint, endpoint_values))

    if estimated_b is None or estimated_a is None:
        row.update(
            {
                "B_relative_error_mean": None,
                "topology_slope_main_error_mean": None,
                "topology_slope_stress_error_mean": None,
                "full_stored_object_error_mean": None,
                "cancellation_index_w_ref_mean": None,
            }
        )
        observed_estimate = tensor_path
    else:
        truth_a = panel.A[dates]
        b_relative_errors = []
        slope_main_errors = []
        slope_stress_errors = []
        stored_errors = []
        cancellation = []
        for position in range(evaluation_count):
            delta_b = estimated_b[position] - truth_b[position]
            delta_a = estimated_a[position] - truth_a[position]
            b_relative_errors.append(
                float(np.linalg.norm(delta_b))
                / max(float(np.linalg.norm(truth_b[position])), 1e-12)
            )
            slope_main_errors.append(
                float(np.linalg.norm(delta_b @ (panel.W_alt_main - panel.W_ref)))
            )
            slope_stress_errors.append(
                float(np.linalg.norm(delta_b @ (panel.W_alt_stress - panel.W_ref)))
            )
            if fitted.parameterization == "block":
                estimated_stored = np.concatenate(
                    [estimated_a[position], estimated_b[position]], axis=1
                )
                truth_stored = np.concatenate(
                    [truth_a[position], truth_b[position]], axis=1
                )
            else:
                estimated_stored = np.concatenate(
                    [endpoint_estimates["w_ref"][position], estimated_b[position]],
                    axis=1,
                )
                truth_stored = np.concatenate(
                    [truth_m_ref[position], truth_b[position]], axis=1
                )
            stored_errors.append(
                float(np.linalg.norm(estimated_stored - truth_stored))
                / max(float(np.linalg.norm(truth_stored)), 1e-12)
            )
            cancellation.append(
                cancellation_index(delta_a, delta_b, panel.W_ref)
            )
        row.update(
            {
                "B_relative_error_mean": float(np.mean(b_relative_errors)),
                "topology_slope_main_error_mean": float(
                    np.mean(slope_main_errors)
                ),
                "topology_slope_stress_error_mean": float(
                    np.mean(slope_stress_errors)
                ),
                "full_stored_object_error_mean": float(np.mean(stored_errors)),
                "cancellation_index_w_ref_mean": float(np.mean(cancellation)),
            }
        )
        if fitted.parameterization == "block":
            observed_estimate = estimated_a + np.einsum(
                "tij,tjk->tik",
                estimated_b,
                panel.estimation.topology[dates],
                optimize=True,
            )
        else:
            observed_estimate = endpoint_estimates["w_ref"] + np.einsum(
                "tij,tjk->tik",
                estimated_b,
                panel.estimation.topology[dates] - panel.W_ref[None, :, :],
                optimize=True,
            )

    predictions = np.einsum(
        "tij,tj->ti",
        observed_estimate,
        panel.estimation.predictors[dates],
        optimize=True,
    )
    prediction_errors = panel.estimation.outcomes[dates] - predictions
    row.update(
        {
            "retrospective_prediction_rmse": float(
                np.sqrt(np.mean(np.square(prediction_errors)))
            ),
            "evaluation_dates": evaluation_count,
            "separation_diagnostic_median": float(
                np.median(fitted.separation[positions])
            ),
            "adaptive_gram_scale_mean": float(
                np.mean(fitted.ridge_diagnostics["gram_scales"])
            ),
            "adaptive_ridge_penalty_mean": float(
                np.mean(fitted.ridge_diagnostics["ridge_penalties"])
            ),
            "selected_fused_penalty": fitted.selected_fused_penalty,
            "runtime_seconds": float(fitted.runtime_seconds),
        }
    )
    row.update(_cp_diagnostics(fitted))
    return row
