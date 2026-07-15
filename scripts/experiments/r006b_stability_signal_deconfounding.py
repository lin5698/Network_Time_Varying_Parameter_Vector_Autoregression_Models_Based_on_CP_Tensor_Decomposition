"""R006b stability-signal deconfounding experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scripts.experiments.high_impact_metrics import (
        evaluate_response_pair,
        spectral_radius,
    )
    from scripts.experiments.r005_separation_stability_pilot import (
        ROOT,
        _cp_reconstruct,
        _spline_reconstruct,
        _topology_path,
        _tucker_reconstruct,
    )
    from scripts.experiments.r006_approximate_rank_pilot import fused_tv_denoise
except ModuleNotFoundError:  # Direct script execution from this directory.
    from high_impact_metrics import evaluate_response_pair, spectral_radius
    from r005_separation_stability_pilot import (
        ROOT,
        _cp_reconstruct,
        _spline_reconstruct,
        _topology_path,
        _tucker_reconstruct,
    )
    from r006_approximate_rank_pilot import fused_tv_denoise


DEFAULT_OUTPUT_DIR = (
    ROOT
    / "output"
    / "high_impact_revision"
    / "r006b_stability_signal_deconfounding"
)
APPROXIMATION_TARGETS = (0.0, 0.10, 0.25, 0.50)
STABILITY_LEVELS = (0.80, 0.95)
LAYERS = ("matched", "native")
SEEDS = tuple(range(240100, 240110))


@dataclass(frozen=True)
class R006BConfig:
    n: int = 20
    t_len: int = 200
    window: int = 80
    true_rank: int = 8
    head_rank: int = 3
    fitted_rank: int = 3
    query_frobenius_norm: float = 1.20
    sigma: float = 0.25
    ridge_multiplier: float = 0.001
    separation_strength: float = 0.15
    horizon: int = 8
    stability_threshold: float = 0.98
    projection_target: float = 0.95
    spline_df: int = 10
    cp_iterations: int = 50
    cp_starts: int = 2
    cp_tolerance: float = 1e-6
    fused_penalties: tuple[float, ...] = (0.10, 0.25, 0.50, 1.00)
    fused_max_iterations: int = 200
    fused_tolerance: float = 1e-5
    evaluation_fraction: float = 0.30
    validation_fraction: float = 0.20


def component_approximation_ratio(component_norms: np.ndarray, rank: int) -> float:
    """Return the relative Frobenius energy outside the largest components."""
    squared = np.square(np.asarray(component_norms, dtype=float))
    if squared.ndim != 1 or rank <= 0:
        raise ValueError("component_norms must be one-dimensional and rank positive")
    total = float(squared.sum())
    if total <= 1e-24:
        return 0.0
    retained = float(np.sort(squared)[::-1][:rank].sum())
    return math.sqrt(max(total - retained, 0.0) / total)


def fit_scale_adaptive_ridge(
    design: np.ndarray,
    outcome: np.ndarray,
    *,
    ridge_multiplier: float,
) -> tuple[np.ndarray, dict[str, float]]:
    """Fit multivariate ridge with a penalty tied to the design Gram scale."""
    x = np.asarray(design, dtype=float)
    y = np.asarray(outcome, dtype=float)
    if x.ndim != 2 or y.ndim != 2 or x.shape[0] != y.shape[0]:
        raise ValueError("design and outcome must be row-aligned matrices")
    if x.shape[0] == 0 or x.shape[1] == 0 or ridge_multiplier < 0:
        raise ValueError("empty design or negative ridge multiplier")

    gram = x.T @ x / x.shape[0]
    gram_scale = float(np.trace(gram) / x.shape[1])
    ridge_penalty = ridge_multiplier * gram_scale
    cross_product = x.T @ y / x.shape[0]
    coefficient = np.linalg.solve(
        gram + ridge_penalty * np.eye(x.shape[1]), cross_product
    ).T
    return coefficient, {
        "gram_scale": gram_scale,
        "ridge_penalty": ridge_penalty,
    }


def _block_design(predictors: np.ndarray, topology: np.ndarray) -> np.ndarray:
    x = np.asarray(predictors, dtype=float)
    w = np.asarray(topology, dtype=float)
    if x.ndim != 2 or w.shape != (x.shape[0], x.shape[1], x.shape[1]):
        raise ValueError("predictors and topology have incompatible shapes")
    exposure = np.einsum("tij,tj->ti", w, x, optimize=True)
    return np.concatenate([x, exposure], axis=1)


def design_covariance(predictors: np.ndarray, topology: np.ndarray) -> np.ndarray:
    """Return the centered covariance of the separated block design."""
    design = _block_design(predictors, topology)
    centered = design - design.mean(axis=0, keepdims=True)
    return centered.T @ centered / design.shape[0]


def _temporal_directions(t_len: int, true_rank: int) -> tuple[np.ndarray, np.ndarray]:
    dates = np.linspace(0.0, 1.0, t_len)
    angle = np.pi / 4.0 + 0.12 * np.sin(2.0 * np.pi * dates)
    secondary = np.column_stack([np.cos(angle), np.sin(angle)])

    tail_rank = true_rank - 3
    phases = np.linspace(0.0, 2.0 * np.pi, tail_rank, endpoint=False)
    raw_tail = np.column_stack(
        [
            1.0
            + 0.15 * np.sin(2.0 * np.pi * (component + 1) * dates + phase)
            + 0.05 * np.cos(2.0 * np.pi * dates + 0.5 * phase)
            for component, phase in enumerate(phases)
        ]
    )
    tail = raw_tail / np.linalg.norm(raw_tail, axis=1, keepdims=True)
    return secondary, tail


def _eigenvalue_path(
    *,
    t_len: int,
    true_rank: int,
    target_rho: float,
    query_frobenius_norm: float,
    tail_energy: float,
) -> np.ndarray:
    residual_energy = query_frobenius_norm**2 - target_rho**2
    if not 0.0 <= tail_energy <= residual_energy:
        raise ValueError("tail energy lies outside the feasible interval")
    secondary, tail = _temporal_directions(t_len, true_rank)
    values = np.zeros((t_len, true_rank), dtype=float)
    values[:, 0] = target_rho
    values[:, 1:3] = math.sqrt(max(residual_energy - tail_energy, 0.0)) * secondary
    values[:, 3:] = math.sqrt(max(tail_energy, 0.0)) * tail
    if np.max(np.abs(values[:, 1:])) >= target_rho:
        raise ValueError("requested radius and Frobenius norm are not jointly feasible")
    return values


def _components_from_eigenvalues(
    eigenvalues: np.ndarray,
    spatial: np.ndarray,
    block_multipliers: np.ndarray,
    reference_topology: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    outer = np.einsum("ir,jr->rij", spatial, spatial, optimize=True)
    query_components = eigenvalues.T[:, :, None, None] * outer[:, None, :, :]
    network_components = block_multipliers[:, None, None, None] * query_components
    network_at_reference = np.einsum(
        "rtij,jk->rtik", network_components, reference_topology, optimize=True
    )
    direct_components = query_components - network_at_reference
    block_components = np.concatenate(
        [direct_components, network_components], axis=3
    )
    component_norms = np.sqrt(np.sum(np.square(block_components), axis=(1, 2, 3)))
    return direct_components, network_components, query_components, component_norms


def _calibrate_components(
    *,
    t_len: int,
    true_rank: int,
    head_rank: int,
    approximation_target: float,
    target_rho: float,
    query_frobenius_norm: float,
    spatial: np.ndarray,
    block_multipliers: np.ndarray,
    reference_topology: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    residual_energy = query_frobenius_norm**2 - target_rho**2

    def construct(tail_energy: float):
        eigenvalues = _eigenvalue_path(
            t_len=t_len,
            true_rank=true_rank,
            target_rho=target_rho,
            query_frobenius_norm=query_frobenius_norm,
            tail_energy=tail_energy,
        )
        components = _components_from_eigenvalues(
            eigenvalues, spatial, block_multipliers, reference_topology
        )
        ratio = component_approximation_ratio(components[3], head_rank)
        return eigenvalues, components, ratio

    if approximation_target == 0.0:
        selected_energy = 0.0
    else:
        _, _, upper_ratio = construct(residual_energy)
        if upper_ratio < approximation_target:
            raise ValueError(
                "approximation target is infeasible under the declared spectrum"
            )
        lower = 0.0
        upper = residual_energy
        for _ in range(70):
            midpoint = 0.5 * (lower + upper)
            _, _, ratio = construct(midpoint)
            if ratio < approximation_target:
                lower = midpoint
            else:
                upper = midpoint
        selected_energy = 0.5 * (lower + upper)

    eigenvalues, components, ratio = construct(selected_energy)
    direct, network, query, norms = components
    return direct, network, query, norms, ratio


def generate_deconfounded_panel(
    *,
    n: int,
    t_len: int,
    true_rank: int,
    head_rank: int,
    approximation_target: float,
    target_rho: float,
    query_frobenius_norm: float,
    separation_strength: float,
    sigma: float,
    seed: int,
    layer: str,
) -> dict[str, Any]:
    """Generate matched-excitation or native-VAR data with a fixed query norm."""
    if layer not in {"matched", "native"}:
        raise ValueError("layer must be 'matched' or 'native'")
    if not 0.0 <= approximation_target < 1.0:
        raise ValueError("approximation_target must lie in [0, 1)")
    if head_rank != 3 or not head_rank < true_rank <= n:
        raise ValueError("R006b requires head_rank=3 < true_rank <= n")
    if t_len < 4 or sigma <= 0 or target_rho <= 0:
        raise ValueError("invalid panel dimension, noise scale or target radius")
    if not target_rho < query_frobenius_norm:
        raise ValueError("query Frobenius norm must exceed the target radius")

    structure_rng = np.random.default_rng(seed)
    spatial, _ = np.linalg.qr(
        structure_rng.normal(size=(n, true_rank)), mode="reduced"
    )
    reference_topology, topology = _topology_path(
        structure_rng, n, t_len, separation_strength
    )
    block_multipliers = np.concatenate(
        [np.full(head_rank, 0.08), np.full(true_rank - head_rank, 1.00)]
    )
    direct_components, network_components, query_components, norms, a3_ratio = (
        _calibrate_components(
            t_len=t_len,
            true_rank=true_rank,
            head_rank=head_rank,
            approximation_target=approximation_target,
            target_rho=target_rho,
            query_frobenius_norm=query_frobenius_norm,
            spatial=spatial,
            block_multipliers=block_multipliers,
            reference_topology=reference_topology,
        )
    )
    direct = direct_components.sum(axis=0)
    network = network_components.sum(axis=0)
    query = query_components.sum(axis=0)
    observed = direct + np.einsum(
        "tij,tjk->tik", network, topology, optimize=True
    )

    excitation_rng = np.random.default_rng(seed + 10_000_019)
    innovations = excitation_rng.normal(scale=sigma, size=(t_len, n))
    if layer == "matched":
        raw_predictors = excitation_rng.normal(size=(t_len, n))
        covariance_root = np.diag(np.linspace(1.0, 1.4, n))
        predictors = raw_predictors @ covariance_root
        outcomes = np.einsum(
            "tij,tj->ti", observed, predictors, optimize=True
        ) + innovations
        states = None
    else:
        states = np.empty((t_len + 1, n), dtype=float)
        states[0] = excitation_rng.normal(scale=sigma, size=n)
        for date in range(t_len):
            states[date + 1] = observed[date] @ states[date] + innovations[date]
        predictors = states[:-1]
        outcomes = states[1:]

    return {
        "predictors": predictors,
        "outcomes": outcomes,
        "states": states,
        "innovations": innovations,
        "A": direct,
        "B": network,
        "W": topology,
        "W_reference": reference_topology,
        "M": query,
        "M_observed": observed,
        "direct_components": direct_components,
        "network_components": network_components,
        "component_norms": norms,
        "a3_ratio": float(a3_ratio),
        "block_multipliers": block_multipliers,
        "layer": layer,
    }


def estimate_local_blocks(
    predictors: np.ndarray,
    outcomes: np.ndarray,
    topology: np.ndarray,
    *,
    window: int,
    ridge_multiplier: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Estimate rolling separated blocks with scale-adaptive ridge."""
    x = np.asarray(predictors, dtype=float)
    y = np.asarray(outcomes, dtype=float)
    w = np.asarray(topology, dtype=float)
    if x.ndim != 2 or y.shape != x.shape:
        raise ValueError("predictors and outcomes must be aligned matrices")
    if w.shape != (x.shape[0], x.shape[1], x.shape[1]):
        raise ValueError("topology has incompatible dimensions")
    if window <= 2 * x.shape[1] or window >= x.shape[0]:
        raise ValueError("window must exceed 2N and leave evaluation dates")

    blocks = []
    indices = []
    separation = []
    gram_scales = []
    ridge_penalties = []
    for date in range(window, x.shape[0]):
        predictor_window = x[date - window : date]
        topology_window = w[date - window : date]
        outcome_window = y[date - window : date]
        exposure_window = np.einsum(
            "tij,tj->ti", topology_window, predictor_window, optimize=True
        )
        design = np.concatenate([predictor_window, exposure_window], axis=1)
        coefficient, diagnostics = fit_scale_adaptive_ridge(
            design, outcome_window, ridge_multiplier=ridge_multiplier
        )
        blocks.append(coefficient)
        indices.append(date)
        gram_scales.append(diagnostics["gram_scale"])
        ridge_penalties.append(diagnostics["ridge_penalty"])

        projection, *_ = np.linalg.lstsq(
            predictor_window, exposure_window, rcond=1e-10
        )
        residual = exposure_window - predictor_window @ projection
        residual_gram = residual.T @ residual / window
        exposure_scale = float(np.sum(np.square(exposure_window)) / window)
        exposure_scale /= x.shape[1]
        minimum_eigenvalue = max(
            float(np.linalg.eigvalsh(residual_gram)[0]), 0.0
        )
        separation.append(minimum_eigenvalue / max(exposure_scale, 1e-12))

    return (
        np.stack(blocks, axis=2),
        np.asarray(indices, dtype=int),
        np.asarray(separation, dtype=float),
        {
            "gram_scales": np.asarray(gram_scales, dtype=float),
            "ridge_penalties": np.asarray(ridge_penalties, dtype=float),
        },
    )


def _fused_reconstruct(
    tensor: np.ndarray,
    penalty_multiplier: float,
    config: R006BConfig,
) -> tuple[np.ndarray, dict[str, Any]]:
    dates = tensor.shape[2]
    flattened = np.moveaxis(tensor, 2, 0).reshape(dates, -1)
    denoised, diagnostics = fused_tv_denoise(
        flattened,
        penalty_multiplier=penalty_multiplier,
        max_iterations=config.fused_max_iterations,
        tolerance=config.fused_tolerance,
    )
    reconstructed = np.moveaxis(
        denoised.reshape(dates, *tensor.shape[:2]), 0, 2
    )
    return reconstructed, diagnostics


def _prediction_rmse(
    tensor: np.ndarray,
    panel: dict[str, Any],
    indices: np.ndarray,
    positions: range,
    n: int,
) -> float:
    squared_errors = []
    for position in positions:
        date = int(indices[position])
        coefficient = tensor[:, :, position]
        observed_operator = coefficient[:, :n] + coefficient[:, n:] @ panel["W"][date]
        prediction = observed_operator @ panel["predictors"][date]
        squared_errors.extend(np.square(panel["outcomes"][date] - prediction).tolist())
    return float(np.sqrt(np.mean(squared_errors)))


def select_fused_penalty(
    local_tensor: np.ndarray,
    panel: dict[str, Any],
    indices: np.ndarray,
    config: R006BConfig,
) -> tuple[float, dict[str, Any]]:
    """Select fused-TV strength without fitting on evaluation-period estimates."""
    total_dates = len(indices)
    evaluation_count = max(1, int(math.ceil(config.evaluation_fraction * total_dates)))
    validation_count = max(1, int(math.ceil(config.validation_fraction * total_dates)))
    validation_stop = total_dates - evaluation_count
    validation_start = max(0, validation_stop - validation_count)
    if validation_stop <= 1 or validation_start >= validation_stop:
        raise ValueError("insufficient pre-evaluation dates for fused-TV validation")

    selection_tensor = local_tensor[:, :, :validation_stop]
    selection_indices = indices[:validation_stop]
    validation_positions = range(validation_start, validation_stop)
    candidates = []
    candidate_scores: dict[str, float] = {}
    for penalty in config.fused_penalties:
        candidate, diagnostics = _fused_reconstruct(
            selection_tensor, penalty, config
        )
        if not diagnostics["converged"]:
            raise RuntimeError(f"fused-TV did not converge for penalty {penalty}")
        score = _prediction_rmse(
            candidate,
            panel,
            selection_indices,
            validation_positions,
            config.n,
        )
        candidates.append((score, penalty))
        candidate_scores[f"{penalty:.12g}"] = score
    _, selected_penalty = min(candidates, key=lambda item: item[0])
    return selected_penalty, {
        "candidate_scores": candidate_scores,
        "selection_dates": validation_stop,
        "validation_dates": validation_count,
        "evaluation_dates_excluded": evaluation_count,
    }


def _layer_diagnostics(panel: dict[str, Any]) -> dict[str, float | str | None]:
    predictors = panel["predictors"]
    covariance = design_covariance(predictors, panel["W"])
    design = _block_design(predictors, panel["W"])
    gram = design.T @ design / design.shape[0]
    eigenvalues = np.linalg.eigvalsh(gram)
    minimum = max(float(eigenvalues[0]), 0.0)
    maximum = float(eigenvalues[-1])
    predictor_variance = float(np.mean(np.var(predictors, axis=0)))
    innovation_variance = float(np.mean(np.square(panel["innovations"])))
    digest = hashlib.sha256(np.ascontiguousarray(covariance).tobytes()).hexdigest()
    return {
        "predictor_rms": float(np.sqrt(np.mean(np.square(predictors)))),
        "predictor_covariance_trace": float(np.trace(np.cov(predictors, rowvar=False))),
        "innovation_to_state_variance_ratio": (
            innovation_variance / max(predictor_variance, 1e-12)
            if panel["layer"] == "native"
            else None
        ),
        "design_gram_min_eigenvalue": minimum,
        "design_gram_max_eigenvalue": maximum,
        "design_gram_condition": maximum / max(minimum, 1e-12),
        "design_covariance_digest": digest,
    }


def _construction_diagnostics(
    panel: dict[str, Any],
    *,
    target_rho: float,
    approximation_target: float,
    query_frobenius_norm: float,
) -> dict[str, float]:
    reconstructed = panel["A"] + np.einsum(
        "tij,jk->tik", panel["B"], panel["W_reference"], optimize=True
    )
    block_components = np.concatenate(
        [panel["direct_components"], panel["network_components"]], axis=3
    )
    singular_values = np.linalg.svd(block_components, compute_uv=False)
    return {
        "true_radius_max_abs_error": max(
            abs(spectral_radius(matrix) - target_rho) for matrix in panel["M"]
        ),
        "query_frobenius_max_abs_error": max(
            abs(float(np.linalg.norm(matrix)) - query_frobenius_norm)
            for matrix in panel["M"]
        ),
        "separated_identity_max_abs_error": float(
            np.max(np.abs(reconstructed - panel["M"]))
        ),
        "component_second_singular_max": float(np.max(singular_values[..., 1])),
        "a3_calibration_abs_error": abs(panel["a3_ratio"] - approximation_target),
        "observed_radius_max": max(
            spectral_radius(matrix) for matrix in panel["M_observed"]
        ),
    }


def _evaluate_method(
    *,
    method: str,
    tensor: np.ndarray,
    panel: dict[str, Any],
    indices: np.ndarray,
    separation: np.ndarray,
    ridge_diagnostics: dict[str, np.ndarray],
    layer_diagnostics: dict[str, float | str | None],
    construction_diagnostics: dict[str, float],
    config: R006BConfig,
    approximation_target: float,
    target_rho: float,
    seed: int,
    layer: str,
    runtime_seconds: float,
    cp_diagnostics: dict[str, Any] | None = None,
    selected_fused_penalty: float | None = None,
) -> dict[str, Any]:
    evaluation_count = max(1, int(math.ceil(config.evaluation_fraction * len(indices))))
    positions = range(len(indices) - evaluation_count, len(indices))
    block_errors = []
    operator_errors = []
    operator_absolute_errors = []
    raw_errors = []
    zero_ratios = []
    qualified_errors = []
    projected_errors = []
    transfer_ratios = []
    prediction_squared_errors = []
    estimated_unstable = 0

    for position in positions:
        date = int(indices[position])
        estimate = tensor[:, :, position]
        truth_block = np.concatenate([panel["A"][date], panel["B"][date]], axis=1)
        block_errors.append(
            float(
                np.linalg.norm(estimate - truth_block)
                / max(np.linalg.norm(truth_block), 1e-12)
            )
        )
        direct_estimate = estimate[:, : config.n]
        network_estimate = estimate[:, config.n :]
        query_estimate = direct_estimate + network_estimate @ panel["W_reference"]
        query_truth = panel["M"][date]
        absolute_operator_error = float(np.linalg.norm(query_estimate - query_truth))
        operator_absolute_errors.append(absolute_operator_error)
        operator_errors.append(
            absolute_operator_error / max(float(np.linalg.norm(query_truth)), 1e-12)
        )
        response = evaluate_response_pair(
            query_truth,
            query_estimate,
            horizon=config.horizon,
            stability_threshold=config.stability_threshold,
            projection_target=config.projection_target,
        )
        zero_response = evaluate_response_pair(
            query_truth,
            np.zeros_like(query_truth),
            horizon=config.horizon,
            stability_threshold=config.stability_threshold,
        )
        raw_error = float(response["raw_response_error"])
        raw_errors.append(raw_error)
        zero_ratios.append(
            raw_error / max(float(zero_response["raw_response_error"]), 1e-12)
        )
        transfer_ratios.append(raw_error / max(absolute_operator_error, 1e-12))
        if response["stability_qualified_error"] is not None:
            qualified_errors.append(float(response["stability_qualified_error"]))
        projected_errors.append(float(response["projected_sensitivity_error"]))
        estimated_unstable += (
            response["estimated_spectral_radius"] >= config.stability_threshold
        )

        observed_estimate = direct_estimate + network_estimate @ panel["W"][date]
        prediction_error = (
            panel["outcomes"][date]
            - observed_estimate @ panel["predictors"][date]
        )
        prediction_squared_errors.extend(np.square(prediction_error).tolist())

    return {
        "layer": layer,
        "approximation_target": approximation_target,
        "actual_a3_ratio": float(panel["a3_ratio"]),
        "target_rho": target_rho,
        "seed": seed,
        "method": method,
        "method_rank": config.fitted_rank if method in {"cp_rank3", "tucker_333"} else None,
        "N": config.n,
        "T": config.t_len,
        "evaluation_dates": evaluation_count,
        "separation_diagnostic_median": float(np.median(separation[-evaluation_count:])),
        "adaptive_gram_scale_mean": float(np.mean(ridge_diagnostics["gram_scales"])),
        "adaptive_ridge_penalty_mean": float(
            np.mean(ridge_diagnostics["ridge_penalties"])
        ),
        "block_error_mean": float(np.mean(block_errors)),
        "operator_error_mean": float(np.mean(operator_errors)),
        "operator_error_median": float(np.median(operator_errors)),
        "operator_absolute_error_mean": float(np.mean(operator_absolute_errors)),
        "raw_response_error_mean": float(np.mean(raw_errors)),
        "raw_response_error_median": float(np.median(raw_errors)),
        "response_error_zero_ratio_mean": float(np.mean(zero_ratios)),
        "response_error_zero_ratio_median": float(np.median(zero_ratios)),
        "response_transfer_ratio_mean": float(np.mean(transfer_ratios)),
        "stability_qualified_error_mean": (
            float(np.mean(qualified_errors)) if qualified_errors else None
        ),
        "stability_qualified_rate": len(qualified_errors) / evaluation_count,
        "projected_sensitivity_error_mean": float(np.mean(projected_errors)),
        "prediction_rmse": float(np.sqrt(np.mean(prediction_squared_errors))),
        "retrospective_prediction_rmse": float(
            np.sqrt(np.mean(prediction_squared_errors))
        ),
        "estimated_instability_rate": estimated_unstable / evaluation_count,
        "selected_fused_penalty": selected_fused_penalty,
        "cp_start_objective_spread": (
            cp_diagnostics["start_objective_spread"] if cp_diagnostics else None
        ),
        "cp_best_relative_objective": (
            cp_diagnostics["best_relative_objective"] if cp_diagnostics else None
        ),
        "runtime_seconds": runtime_seconds,
        "failure": 0,
        "failure_reason": "",
        **layer_diagnostics,
        **construction_diagnostics,
    }


def run_replication(
    *,
    config: R006BConfig,
    approximation_target: float,
    target_rho: float,
    seed: int,
    layer: str,
) -> list[dict[str, Any]]:
    panel = generate_deconfounded_panel(
        n=config.n,
        t_len=config.t_len,
        true_rank=config.true_rank,
        head_rank=config.head_rank,
        approximation_target=approximation_target,
        target_rho=target_rho,
        query_frobenius_norm=config.query_frobenius_norm,
        separation_strength=config.separation_strength,
        sigma=config.sigma,
        seed=seed,
        layer=layer,
    )
    layer_diagnostics = _layer_diagnostics(panel)
    construction_diagnostics = _construction_diagnostics(
        panel,
        target_rho=target_rho,
        approximation_target=approximation_target,
        query_frobenius_norm=config.query_frobenius_norm,
    )

    local_started = time.perf_counter()
    local_tensor, indices, separation, ridge_diagnostics = estimate_local_blocks(
        panel["predictors"],
        panel["outcomes"],
        panel["W"],
        window=config.window,
        ridge_multiplier=config.ridge_multiplier,
    )
    local_runtime = time.perf_counter() - local_started
    methods: list[
        tuple[str, np.ndarray, float, dict[str, Any] | None, float | None]
    ] = [("local", local_tensor, local_runtime, None, None)]

    spline_started = time.perf_counter()
    spline_tensor = _spline_reconstruct(local_tensor, config.spline_df)
    methods.append(
        (
            f"spline_df{config.spline_df}",
            spline_tensor,
            local_runtime + time.perf_counter() - spline_started,
            None,
            None,
        )
    )

    fused_started = time.perf_counter()
    selected_penalty, _ = select_fused_penalty(
        local_tensor, panel, indices, config
    )
    fused_tensor, fused_diagnostics = _fused_reconstruct(
        local_tensor, selected_penalty, config
    )
    if not fused_diagnostics["converged"]:
        raise RuntimeError(
            f"fused-TV did not converge for selected penalty {selected_penalty}"
        )
    methods.append(
        (
            "fused_tv",
            fused_tensor,
            local_runtime + time.perf_counter() - fused_started,
            None,
            selected_penalty,
        )
    )

    cp_started = time.perf_counter()
    cp_tensor, cp_diagnostics = _cp_reconstruct(
        local_tensor,
        config.fitted_rank,
        seed=seed + 700_001,
        iterations=config.cp_iterations,
        starts=config.cp_starts,
        tolerance=config.cp_tolerance,
        return_diagnostics=True,
    )
    methods.append(
        (
            f"cp_rank{config.fitted_rank}",
            cp_tensor,
            local_runtime + time.perf_counter() - cp_started,
            cp_diagnostics,
            None,
        )
    )

    tucker_started = time.perf_counter()
    tucker_tensor = _tucker_reconstruct(local_tensor, config.fitted_rank)
    methods.append(
        (
            f"tucker_{config.fitted_rank}{config.fitted_rank}{config.fitted_rank}",
            tucker_tensor,
            local_runtime + time.perf_counter() - tucker_started,
            None,
            None,
        )
    )

    return [
        _evaluate_method(
            method=method,
            tensor=tensor,
            panel=panel,
            indices=indices,
            separation=separation,
            ridge_diagnostics=ridge_diagnostics,
            layer_diagnostics=layer_diagnostics,
            construction_diagnostics=construction_diagnostics,
            config=config,
            approximation_target=approximation_target,
            target_rho=target_rho,
            seed=seed,
            layer=layer,
            runtime_seconds=runtime,
            cp_diagnostics=cp_diagnostics,
            selected_fused_penalty=selected_penalty,
        )
        for method, tensor, runtime, cp_diagnostics, selected_penalty in methods
    ]


def _method_names(config: R006BConfig) -> list[str]:
    rank = config.fitted_rank
    return [
        "local",
        f"spline_df{config.spline_df}",
        "fused_tv",
        f"cp_rank{rank}",
        f"tucker_{rank}{rank}{rank}",
    ]


def _run_task(
    task: tuple[R006BConfig, float, float, int, str],
) -> list[dict[str, Any]]:
    config, approximation_target, target_rho, seed, layer = task
    try:
        return run_replication(
            config=config,
            approximation_target=approximation_target,
            target_rho=target_rho,
            seed=seed,
            layer=layer,
        )
    except Exception as exc:  # Failed cells remain visible in the frozen audit.
        return [
            {
                "layer": layer,
                "approximation_target": approximation_target,
                "actual_a3_ratio": None,
                "target_rho": target_rho,
                "seed": seed,
                "method": method,
                "method_rank": None,
                "N": config.n,
                "T": config.t_len,
                "evaluation_dates": 0,
                "failure": 1,
                "failure_reason": f"{type(exc).__name__}: {exc}",
            }
            for method in _method_names(config)
        ]


def _quantile(values: list[float], probability: float) -> float | None:
    return float(np.quantile(values, probability)) if values else None


def _summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, float, float, str], list[dict[str, Any]]] = {}
    for row in rows:
        if row["failure"]:
            continue
        key = (
            row["layer"],
            row["approximation_target"],
            row["target_rho"],
            row["method"],
        )
        grouped.setdefault(key, []).append(row)

    summary = []
    for (layer, approximation_target, target_rho, method), group in sorted(
        grouped.items()
    ):
        summary.append(
            {
                "layer": layer,
                "approximation_target": approximation_target,
                "target_rho": target_rho,
                "method": method,
                "replications": len(group),
                "operator_error_median": float(
                    np.median([row["operator_error_mean"] for row in group])
                ),
                "raw_response_error_median": float(
                    np.median([row["raw_response_error_mean"] for row in group])
                ),
                "zero_ratio_median": float(
                    np.median([row["response_error_zero_ratio_mean"] for row in group])
                ),
                "response_transfer_median": float(
                    np.median([row["response_transfer_ratio_mean"] for row in group])
                ),
                "retrospective_prediction_rmse_median": float(
                    np.median(
                        [row["retrospective_prediction_rmse"] for row in group]
                    )
                ),
                "stability_qualified_rate_mean": float(
                    np.mean([row["stability_qualified_rate"] for row in group])
                ),
                "projected_sensitivity_error_median": float(
                    np.median(
                        [row["projected_sensitivity_error_mean"] for row in group]
                    )
                ),
                "runtime_seconds_median": float(
                    np.median([row["runtime_seconds"] for row in group])
                ),
            }
        )
    return summary


def _scale_invariance_error() -> float:
    rng = np.random.default_rng(606_002)
    design = rng.normal(size=(128, 16))
    outcome = rng.normal(size=(128, 6))
    reference, _ = fit_scale_adaptive_ridge(
        design, outcome, ridge_multiplier=0.001
    )
    errors = []
    for scale in (0.05, 7.0, 100.0):
        estimate, _ = fit_scale_adaptive_ridge(
            scale * design,
            scale * outcome,
            ridge_multiplier=0.001,
        )
        errors.append(float(np.max(np.abs(reference - estimate))))
    return max(errors)


def _gate_checks(
    rows: list[dict[str, Any]],
    *,
    config: R006BConfig,
    approximation_targets: tuple[float, ...],
    stability_levels: tuple[float, ...],
    seeds: tuple[int, ...],
    layers: tuple[str, ...],
    smoke: bool,
) -> dict[str, Any]:
    expected_rows = (
        len(approximation_targets)
        * len(stability_levels)
        * len(seeds)
        * len(layers)
        * len(_method_names(config))
    )
    identities = {
        (
            row["layer"],
            row["approximation_target"],
            row["target_rho"],
            row["seed"],
            row["method"],
        )
        for row in rows
    }
    valid = [row for row in rows if row["failure"] == 0]
    failures = [row for row in rows if row["failure"] != 0]

    def maximum(name: str, default: float = math.inf) -> float:
        values = [float(row[name]) for row in valid if row.get(name) is not None]
        return max(values, default=default)

    matched_digest_mismatch = None
    if {0.80, 0.95}.issubset(set(stability_levels)) and "matched" in layers:
        mismatches = []
        local_rows = {
            (row["approximation_target"], row["target_rho"], row["seed"]): row
            for row in valid
            if row["layer"] == "matched" and row["method"] == "local"
        }
        for approximation_target in approximation_targets:
            for seed in seeds:
                low = local_rows.get((approximation_target, 0.80, seed))
                high = local_rows.get((approximation_target, 0.95, seed))
                if low is None or high is None:
                    mismatches.append(math.inf)
                else:
                    mismatches.append(
                        0.0
                        if low["design_covariance_digest"]
                        == high["design_covariance_digest"]
                        else math.inf
                    )
        matched_digest_mismatch = max(mismatches, default=math.inf)

    scale_error = _scale_invariance_error()
    construction = {
        "radius": maximum("true_radius_max_abs_error") < 1e-10,
        "query_frobenius": maximum("query_frobenius_max_abs_error") < 1e-6,
        "separated_identity": maximum("separated_identity_max_abs_error") < 1e-10,
        "component_rank": maximum("component_second_singular_max") < 1e-10,
        "adaptive_ridge_scale_invariance": scale_error < 1e-8,
        "matched_design_covariance": (
            matched_digest_mismatch is None or matched_digest_mismatch < 0.01
        ),
        "a3_calibration": maximum("a3_calibration_abs_error") < 1e-6,
        "observed_operator_bound": maximum("observed_radius_max") < 1.05,
    }

    row_lookup = {
        (
            row["layer"],
            row["approximation_target"],
            row["target_rho"],
            row["seed"],
            row["method"],
        ): row
        for row in valid
    }
    required_cells = []
    tucker_name = f"tucker_{config.fitted_rank}{config.fitted_rank}{config.fitted_rank}"
    for approximation_target in (0.10, 0.25):
        for target_rho in (0.80, 0.95):
            improvements_local = []
            improvements_fused = []
            joint_wins = []
            operator_errors = []
            zero_ratios = []
            for seed in seeds:
                tucker = row_lookup.get(
                    ("matched", approximation_target, target_rho, seed, tucker_name)
                )
                local = row_lookup.get(
                    ("matched", approximation_target, target_rho, seed, "local")
                )
                fused = row_lookup.get(
                    ("matched", approximation_target, target_rho, seed, "fused_tv")
                )
                if tucker is None or local is None or fused is None:
                    continue
                tucker_error = tucker["raw_response_error_mean"]
                local_error = local["raw_response_error_mean"]
                fused_error = fused["raw_response_error_mean"]
                improvements_local.append(
                    (local_error - tucker_error) / max(local_error, 1e-12)
                )
                improvements_fused.append(
                    (fused_error - tucker_error) / max(fused_error, 1e-12)
                )
                joint_wins.append(tucker_error < local_error and tucker_error < fused_error)
                operator_errors.append(tucker["operator_error_mean"])
                zero_ratios.append(tucker["response_error_zero_ratio_mean"])

            record = {
                "approximation_target": approximation_target,
                "target_rho": target_rho,
                "paired_seeds": len(improvements_local),
                "paired_median_improvement_vs_local": _quantile(
                    improvements_local, 0.5
                ),
                "paired_median_improvement_vs_fused": _quantile(
                    improvements_fused, 0.5
                ),
                "joint_win_rate": (
                    float(np.mean(joint_wins)) if joint_wins else None
                ),
                "operator_error_median": _quantile(operator_errors, 0.5),
                "zero_ratio_median": _quantile(zero_ratios, 0.5),
            }
            record["pass"] = (
                record["paired_seeds"] == len(seeds)
                and record["paired_median_improvement_vs_local"] is not None
                and record["paired_median_improvement_vs_local"] >= 0.10
                and record["paired_median_improvement_vs_fused"] >= 0.10
                and record["joint_win_rate"] >= 0.80
                and record["operator_error_median"] < 1.0
                and record["zero_ratio_median"] < 1.0
            )
            required_cells.append(record)

    stability_checks = []
    for approximation_target in (0.10, 0.25):
        operator_ratios = []
        transfer_ratios = []
        for seed in seeds:
            low = row_lookup.get(
                ("matched", approximation_target, 0.80, seed, tucker_name)
            )
            high = row_lookup.get(
                ("matched", approximation_target, 0.95, seed, tucker_name)
            )
            if low is None or high is None:
                continue
            operator_ratios.append(
                high["operator_error_mean"] / max(low["operator_error_mean"], 1e-12)
            )
            transfer_ratios.append(
                high["response_transfer_ratio_mean"]
                / max(low["response_transfer_ratio_mean"], 1e-12)
            )
        operator_ratio = _quantile(operator_ratios, 0.5)
        transfer_ratio = _quantile(transfer_ratios, 0.5)
        stability_checks.append(
            {
                "approximation_target": approximation_target,
                "paired_seeds": len(operator_ratios),
                "operator_error_ratio_high_low": operator_ratio,
                "response_transfer_ratio_high_low": transfer_ratio,
                "pass": (
                    len(operator_ratios) == len(seeds)
                    and operator_ratio is not None
                    and 0.80 <= operator_ratio <= 1.25
                    and transfer_ratio is not None
                    and transfer_ratio >= 1.10
                ),
            }
        )

    native_values = [
        row.get("innovation_to_state_variance_ratio")
        for row in valid
        if row["layer"] == "native"
    ]
    native_complete = "native" not in layers or (
        len(native_values) > 0
        and all(value is not None and math.isfinite(float(value)) for value in native_values)
    )
    metrics_separate = all(
        all(
            key in row
            for key in (
                "raw_response_error_mean",
                "stability_qualified_error_mean",
                "projected_sensitivity_error_mean",
            )
        )
        for row in valid
    )
    full_grid_declared = (
        approximation_targets == APPROXIMATION_TARGETS
        and stability_levels == STABILITY_LEVELS
        and seeds == SEEDS
        and layers == LAYERS
    )
    completion = {
        "row_count": len(rows) == expected_rows,
        "unique_rows": len(identities) == expected_rows,
        "no_failures": not failures,
        "native_diagnostics": native_complete,
        "separate_response_metrics": metrics_separate,
        "full_grid_declared": full_grid_declared,
    }

    construction_pass = all(construction.values())
    smoke_pass = (
        construction_pass
        and completion["row_count"]
        and completion["unique_rows"]
        and completion["no_failures"]
        and completion["native_diagnostics"]
        and completion["separate_response_metrics"]
    )
    full_pass = (
        smoke_pass
        and completion["full_grid_declared"]
        and all(record["pass"] for record in required_cells)
        and all(record["pass"] for record in stability_checks)
    )
    return {
        "status": (
            "SMOKE_PASS" if smoke and smoke_pass else
            "SMOKE_FAIL" if smoke else
            "PASS" if full_pass else
            "FAIL"
        ),
        "construction": construction,
        "completion": completion,
        "required_cells": required_cells,
        "stability_deconfounding": stability_checks,
        "failure_count": len(failures),
        "failure_reasons": sorted({row["failure_reason"] for row in failures}),
        "max_radius_error": maximum("true_radius_max_abs_error"),
        "max_query_frobenius_error": maximum("query_frobenius_max_abs_error"),
        "max_identity_error": maximum("separated_identity_max_abs_error"),
        "max_component_second_singular": maximum("component_second_singular_max"),
        "max_a3_calibration_error": maximum("a3_calibration_abs_error"),
        "max_observed_radius": maximum("observed_radius_max"),
        "matched_design_covariance_mismatch": matched_digest_mismatch,
        "scale_invariance_error": scale_error,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_report(
    *,
    output_dir: Path,
    rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    payload: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "r006b_replications.csv", rows)
    _write_csv(output_dir / "r006b_summary.csv", summary)
    (output_dir / "r006b_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    checks = payload["checks"]
    required_lines = []
    for record in checks["required_cells"]:
        local = record["paired_median_improvement_vs_local"]
        fused = record["paired_median_improvement_vs_fused"]
        win = record["joint_win_rate"]
        operator = record["operator_error_median"]
        zero = record["zero_ratio_median"]
        required_lines.append(
            "| "
            f"{record['approximation_target']:.2f} | {record['target_rho']:.2f} | "
            f"{100.0 * local:.1f}% | {100.0 * fused:.1f}% | "
            f"{100.0 * win:.1f}% | {operator:.3f} | {zero:.3f} | "
            f"{'PASS' if record['pass'] else 'FAIL'} |"
            if local is not None and fused is not None and win is not None
            and operator is not None and zero is not None
            else "| "
            f"{record['approximation_target']:.2f} | {record['target_rho']:.2f} | "
            "n/a | n/a | n/a | n/a | n/a | FAIL |"
        )
    stability_lines = []
    for record in checks["stability_deconfounding"]:
        operator = record["operator_error_ratio_high_low"]
        transfer = record["response_transfer_ratio_high_low"]
        stability_lines.append(
            "| "
            f"{record['approximation_target']:.2f} | "
            f"{operator:.3f} | {transfer:.3f} | "
            f"{'PASS' if record['pass'] else 'FAIL'} |"
            if operator is not None and transfer is not None
            else "| "
            f"{record['approximation_target']:.2f} | n/a | n/a | FAIL |"
        )
    construction_lines = [
        f"- {name}: `{'PASS' if passed else 'FAIL'}`"
        for name, passed in checks["construction"].items()
    ]
    report = f"""# R006b Stability-Signal Deconfounding Results

**Status:** `{payload['status']}`  
**Run type:** `{payload['run_type']}`  
**Rows:** `{payload['row_count']}`  
**Elapsed seconds:** `{payload['elapsed_seconds']:.3f}`

R006 remains `FAIL`. This result is evaluated only against the frozen R006b protocol.

## Construction Gates

{chr(10).join(construction_lines)}

- maximum radius error: `{checks['max_radius_error']:.3e}`
- maximum query Frobenius error: `{checks['max_query_frobenius_error']:.3e}`
- maximum a3 error: `{checks['max_a3_calibration_error']:.3e}`
- maximum observed radius: `{checks['max_observed_radius']:.5f}`

## Required Matched Cells

| a3 | rho | vs local | vs fused-TV | joint wins | operator error | zero ratio | gate |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
{chr(10).join(required_lines)}

## Stability Deconfounding

| a3 | operator error 0.95/0.80 | response transfer 0.95/0.80 | gate |
| ---: | ---: | ---: | :---: |
{chr(10).join(stability_lines)}

Raw, stability-qualified and projected-sensitivity response metrics are stored separately in `r006b_replications.csv`.
"""
    (output_dir / "r006b_results.md").write_text(report, encoding="utf-8")


def run_grid(
    *,
    config: R006BConfig,
    approximation_targets: tuple[float, ...] = APPROXIMATION_TARGETS,
    stability_levels: tuple[float, ...] = STABILITY_LEVELS,
    seeds: tuple[int, ...] = SEEDS,
    layers: tuple[str, ...] = LAYERS,
    workers: int = 1,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    smoke: bool = False,
) -> dict[str, Any]:
    started = time.perf_counter()
    tasks = [
        (config, approximation_target, target_rho, seed, layer)
        for layer in layers
        for approximation_target in approximation_targets
        for target_rho in stability_levels
        for seed in seeds
    ]
    if workers <= 1:
        nested_rows = [_run_task(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            nested_rows = list(executor.map(_run_task, tasks))
    rows = [row for group in nested_rows for row in group]
    rows.sort(
        key=lambda row: (
            row["layer"],
            row["approximation_target"],
            row["target_rho"],
            row["seed"],
            row["method"],
        )
    )
    summary = _summarize_rows(rows)
    checks = _gate_checks(
        rows,
        config=config,
        approximation_targets=approximation_targets,
        stability_levels=stability_levels,
        seeds=seeds,
        layers=layers,
        smoke=smoke,
    )
    elapsed = time.perf_counter() - started
    protocol_path = ROOT / "refine-logs" / "R006B_PROTOCOL_20260715.md"
    correction_path = (
        ROOT / "refine-logs" / "R006B_CAUSAL_CORRECTION_20260715.md"
    )
    code_path = Path(__file__).resolve()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_type": "SMOKE" if smoke else "FULL_PROTOCOL",
        "status": checks["status"],
        "protocol": "refine-logs/R006B_PROTOCOL_20260715.md",
        "provenance": {
            "protocol_sha256": _sha256_file(protocol_path),
            "correction_addendum_sha256": _sha256_file(correction_path),
            "code_sha256": _sha256_file(code_path),
        },
        "config": asdict(config),
        "grid": {
            "approximation_targets": list(approximation_targets),
            "stability_levels": list(stability_levels),
            "seeds": list(seeds),
            "layers": list(layers),
            "workers": workers,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "elapsed_seconds": elapsed,
        "checks": checks,
        "row_count": len(rows),
        "summary": summary,
    }
    _write_report(
        output_dir=output_dir,
        rows=rows,
        summary=summary,
        payload=payload,
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, min(8, (os.cpu_count() or 2) - 1)),
    )
    parser.add_argument("--smoke", action="store_true")
    arguments = parser.parse_args()

    if arguments.smoke:
        config = R006BConfig(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            spline_df=6,
            cp_iterations=10,
            cp_starts=1,
            fused_penalties=(0.10, 0.50),
            fused_max_iterations=100,
        )
        approximation_targets = (0.10,)
        stability_levels = STABILITY_LEVELS
        seeds = (SEEDS[0],)
        layers = LAYERS
        output_dir = arguments.output_dir or (
            ROOT / "output" / "high_impact_revision" / "r006b_smoke"
        )
    else:
        config = R006BConfig()
        approximation_targets = APPROXIMATION_TARGETS
        stability_levels = STABILITY_LEVELS
        seeds = SEEDS
        layers = LAYERS
        output_dir = arguments.output_dir or DEFAULT_OUTPUT_DIR

    payload = run_grid(
        config=config,
        approximation_targets=approximation_targets,
        stability_levels=stability_levels,
        seeds=seeds,
        layers=layers,
        workers=arguments.workers,
        output_dir=output_dir,
        smoke=arguments.smoke,
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "run_type": payload["run_type"],
                "output_dir": str(output_dir),
                "rows": payload["row_count"],
                "elapsed_seconds": payload["elapsed_seconds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
