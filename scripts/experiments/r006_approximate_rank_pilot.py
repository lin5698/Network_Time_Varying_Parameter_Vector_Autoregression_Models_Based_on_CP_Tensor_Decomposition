"""R006 approximate-rank stress test for block-preserving reconstruction."""

from __future__ import annotations

import argparse
import csv
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
from scipy.linalg import solve_banded

try:
    from scripts.experiments.high_impact_metrics import (
        evaluate_response_pair,
        spectral_radius,
    )
    from scripts.experiments.r005_separation_stability_pilot import (
        ROOT,
        _cp_reconstruct,
        _estimate_local_blocks,
        _spline_reconstruct,
        _topology_path,
        _tucker_reconstruct,
    )
except ModuleNotFoundError:  # Direct script execution from this directory.
    from high_impact_metrics import evaluate_response_pair, spectral_radius
    from r005_separation_stability_pilot import (
        ROOT,
        _cp_reconstruct,
        _estimate_local_blocks,
        _spline_reconstruct,
        _topology_path,
        _tucker_reconstruct,
    )


DEFAULT_OUTPUT_DIR = ROOT / "output" / "high_impact_revision" / "r006_approximate_rank"
APPROXIMATION_TARGETS = (0.0, 0.10, 0.25, 0.50)
STABILITY_LEVELS = (0.80, 0.95)
SEEDS = tuple(range(240100, 240110))


@dataclass(frozen=True)
class R006Config:
    n: int = 20
    t_len: int = 200
    window: int = 80
    true_rank: int = 8
    head_rank: int = 3
    fitted_ranks: tuple[int, ...] = (2, 3, 5)
    sigma: float = 0.25
    ridge: float = 0.001
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


def _component_approximation_ratio(component_norms: np.ndarray, rank: int) -> float:
    squared = np.square(np.asarray(component_norms, dtype=float))
    if squared.sum() <= 1e-24:
        return 0.0
    retained = np.sort(squared)[::-1][:rank].sum()
    tail = max(float(squared.sum() - retained), 0.0)
    return math.sqrt(tail / float(squared.sum()))


def generate_approximate_rank_panel(
    *,
    n: int,
    t_len: int,
    true_rank: int,
    head_rank: int,
    approximation_target: float,
    separation_strength: float,
    target_rho: float,
    sigma: float,
    seed: int,
) -> dict[str, Any]:
    """Generate orthogonal CP components with a calibrated best-rank tail."""
    if not 0.0 <= approximation_target < 1.0:
        raise ValueError("approximation_target must lie in [0, 1)")
    if not 0 < head_rank < true_rank <= n:
        raise ValueError("require 0 < head_rank < true_rank <= n")

    rng = np.random.default_rng(seed)
    raw_spatial = np.column_stack([rng.normal(size=n) for _ in range(true_rank)])
    spatial, _ = np.linalg.qr(raw_spatial, mode="reduced")
    base_topology, topology = _topology_path(
        rng, n, t_len, separation_strength
    )

    direct_weights = np.empty(true_rank)
    network_weights = np.empty(true_rank)
    direct_weights[:head_rank] = np.linspace(0.65, 0.35, head_rank)
    network_weights[:head_rank] = np.linspace(0.25, -0.15, head_rank)
    direct_weights[head_rank:] = np.linspace(0.45, 0.25, true_rank - head_rank)
    network_weights[head_rank:] = 0.18 * np.cos(
        np.linspace(0.0, 2.0 * np.pi, true_rank - head_rank, endpoint=False)
    )

    phases = np.empty(true_rank)
    phases[:head_rank] = np.linspace(0.0, np.pi, head_rank, endpoint=False)
    phases[head_rank:] = np.linspace(
        np.pi / 7.0, 2.0 * np.pi, true_rank - head_rank, endpoint=False
    )
    dates = np.linspace(0.0, 1.0, t_len)
    temporal = np.column_stack(
        [
            1.0
            + 0.18 * np.sin(2.0 * np.pi * (component + 1) * dates + phases[component])
            + 0.06 * np.cos(2.0 * np.pi * dates + 0.5 * phases[component])
            for component in range(true_rank)
        ]
    )

    direct_base = np.empty((true_rank, t_len, n, n), dtype=float)
    network_base = np.empty_like(direct_base)
    for component in range(true_rank):
        outer = np.outer(spatial[:, component], spatial[:, component])
        direct_base[component] = (
            direct_weights[component] * temporal[:, component, None, None] * outer
        )
        network_base[component] = (
            network_weights[component] * temporal[:, component, None, None] * outer
        )

    def scaled_components(tail_multiplier: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        amplitudes = np.ones(true_rank)
        amplitudes[head_rank:] = tail_multiplier
        direct_raw = np.einsum(
            "r,rtij->tij", amplitudes, direct_base, optimize=True
        )
        network_raw = np.einsum(
            "r,rtij->tij", amplitudes, network_base, optimize=True
        )
        scales = np.empty(t_len)
        for date in range(t_len):
            query_raw = direct_raw[date] + network_raw[date] @ base_topology
            radius = spectral_radius(query_raw)
            if radius <= 1e-12:
                raise RuntimeError("generated query operator has zero spectral radius")
            scales[date] = target_rho / radius
        direct_components = (
            direct_base * amplitudes[:, None, None, None] * scales[None, :, None, None]
        )
        network_components = (
            network_base * amplitudes[:, None, None, None] * scales[None, :, None, None]
        )
        norms = np.asarray(
            [
                np.linalg.norm(
                    np.concatenate(
                        [direct_components[component], network_components[component]],
                        axis=2,
                    )
                )
                for component in range(true_rank)
            ]
        )
        return direct_components, network_components, norms

    if approximation_target == 0.0:
        tail_multiplier = 0.0
    else:
        lower = 0.0
        upper = 1.0
        while True:
            _, _, upper_norms = scaled_components(upper)
            if _component_approximation_ratio(upper_norms, head_rank) >= approximation_target:
                break
            upper *= 2.0
            if upper > 1e6:
                raise RuntimeError("failed to bracket approximation target")
        for _ in range(60):
            midpoint = 0.5 * (lower + upper)
            _, _, midpoint_norms = scaled_components(midpoint)
            ratio = _component_approximation_ratio(midpoint_norms, head_rank)
            if ratio < approximation_target:
                lower = midpoint
            else:
                upper = midpoint
        tail_multiplier = 0.5 * (lower + upper)

    direct_components, network_components, component_norms = scaled_components(
        tail_multiplier
    )
    direct = direct_components.sum(axis=0)
    network = network_components.sum(axis=0)
    query_operator = direct + np.einsum(
        "tij,jk->tik", network, base_topology, optimize=True
    )
    observed_operator = direct + np.einsum(
        "tij,tjk->tik", network, topology, optimize=True
    )
    truth_tensor = np.moveaxis(np.concatenate([direct, network], axis=2), 0, 2)

    observations = np.empty((t_len, n), dtype=float)
    observations[0] = rng.normal(scale=sigma, size=n)
    for date in range(t_len - 1):
        observations[date + 1] = (
            observed_operator[date] @ observations[date]
            + rng.normal(scale=sigma, size=n)
        )

    return {
        "y": observations,
        "A": direct,
        "B": network,
        "W": topology,
        "W_reference": base_topology,
        "M": query_operator,
        "M_observed": observed_operator,
        "truth_tensor": truth_tensor,
        "component_norms": component_norms,
        "tail_multiplier": float(tail_multiplier),
        "a3_ratio": _component_approximation_ratio(component_norms, head_rank),
        "a5_ratio": _component_approximation_ratio(
            component_norms, min(5, true_rank)
        ),
    }


def _difference_transpose(values: np.ndarray, length: int) -> np.ndarray:
    result = np.zeros((length, values.shape[1]), dtype=float)
    result[0] = -values[0]
    result[-1] = values[-1]
    if length > 2:
        result[1:-1] = values[:-1] - values[1:]
    return result


def fused_tv_denoise(
    series: np.ndarray,
    *,
    penalty_multiplier: float,
    max_iterations: int = 200,
    tolerance: float = 1e-5,
    rho: float = 1.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Denoise columns with a vectorized 1D fused-lasso ADMM solver."""
    observations = np.asarray(series, dtype=float)
    if observations.ndim != 2 or observations.shape[0] < 2:
        raise ValueError("series must be a time-by-feature matrix with at least two rows")
    if penalty_multiplier < 0 or max_iterations <= 0 or tolerance <= 0 or rho <= 0:
        raise ValueError("invalid fused-TV optimization setting")

    differences = np.diff(observations, axis=0)
    scales = np.median(np.abs(differences), axis=0)
    penalties = penalty_multiplier * scales
    if np.max(penalties) <= 1e-15:
        return observations.copy(), {
            "converged": True,
            "iterations": 0,
            "primal_residual": 0.0,
            "dual_residual": 0.0,
        }

    length = observations.shape[0]
    banded = np.zeros((3, length), dtype=float)
    banded[1] = 1.0 + 2.0 * rho
    banded[1, 0] = 1.0 + rho
    banded[1, -1] = 1.0 + rho
    banded[0, 1:] = -rho
    banded[2, :-1] = -rho

    estimate = observations.copy()
    auxiliary = np.diff(estimate, axis=0)
    dual = np.zeros_like(auxiliary)
    converged = False
    primal_residual = math.inf
    dual_residual = math.inf
    normalizer = math.sqrt(max(auxiliary.size, 1))

    for iteration in range(1, max_iterations + 1):
        right_hand_side = observations + rho * _difference_transpose(
            auxiliary - dual, length
        )
        estimate = solve_banded((1, 1), banded, right_hand_side)
        estimate_difference = np.diff(estimate, axis=0)
        previous_auxiliary = auxiliary
        threshold_input = estimate_difference + dual
        auxiliary = np.sign(threshold_input) * np.maximum(
            np.abs(threshold_input) - penalties[None, :] / rho, 0.0
        )
        dual += estimate_difference - auxiliary

        primal_residual = float(
            np.linalg.norm(estimate_difference - auxiliary) / normalizer
        )
        dual_change = _difference_transpose(
            auxiliary - previous_auxiliary, length
        )
        dual_residual = float(rho * np.linalg.norm(dual_change) / normalizer)
        if max(primal_residual, dual_residual) <= tolerance:
            converged = True
            break

    return estimate, {
        "converged": converged,
        "iterations": iteration,
        "primal_residual": primal_residual,
        "dual_residual": dual_residual,
    }


def _fused_reconstruct(
    tensor: np.ndarray,
    penalty_multiplier: float,
    config: R006Config,
) -> tuple[np.ndarray, dict[str, Any]]:
    dates = tensor.shape[2]
    flattened = np.moveaxis(tensor, 2, 0).reshape(dates, -1)
    denoised, diagnostics = fused_tv_denoise(
        flattened,
        penalty_multiplier=penalty_multiplier,
        max_iterations=config.fused_max_iterations,
        tolerance=config.fused_tolerance,
    )
    reconstructed = np.moveaxis(denoised.reshape(dates, *tensor.shape[:2]), 0, 2)
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
        error = panel["y"][date + 1] - observed_operator @ panel["y"][date]
        squared_errors.extend(np.square(error).tolist())
    return float(np.sqrt(np.mean(squared_errors)))


def _evaluate_method(
    *,
    method: str,
    tensor: np.ndarray,
    panel: dict[str, Any],
    indices: np.ndarray,
    diagnostics: np.ndarray,
    config: R006Config,
    approximation_target: float,
    target_rho: float,
    seed: int,
    runtime_seconds: float,
    method_rank: int | None = None,
    cp_diagnostics: dict[str, Any] | None = None,
    selected_fused_penalty: float | None = None,
) -> dict[str, Any]:
    evaluation_count = max(1, int(math.ceil(config.evaluation_fraction * len(indices))))
    positions = range(len(indices) - evaluation_count, len(indices))
    block_errors = []
    operator_errors = []
    raw_errors = []
    zero_ratios = []
    qualified_errors = []
    projected_errors = []
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
        operator_errors.append(
            float(
                np.linalg.norm(query_estimate - query_truth)
                / max(np.linalg.norm(query_truth), 1e-12)
            )
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
        if response["stability_qualified_error"] is not None:
            qualified_errors.append(float(response["stability_qualified_error"]))
        projected_errors.append(float(response["projected_sensitivity_error"]))
        estimated_unstable += (
            response["estimated_spectral_radius"] >= config.stability_threshold
        )

        observed_estimate = direct_estimate + network_estimate @ panel["W"][date]
        prediction_error = panel["y"][date + 1] - observed_estimate @ panel["y"][date]
        prediction_squared_errors.extend(np.square(prediction_error).tolist())

    true_radius_error = max(
        abs(spectral_radius(matrix) - target_rho) for matrix in panel["M"]
    )
    return {
        "approximation_target": approximation_target,
        "actual_a3_ratio": float(panel["a3_ratio"]),
        "actual_a5_ratio": float(panel["a5_ratio"]),
        "target_rho": target_rho,
        "seed": seed,
        "method": method,
        "method_rank": method_rank,
        "N": config.n,
        "T": config.t_len,
        "evaluation_dates": evaluation_count,
        "separation_diagnostic_median": float(
            np.median(diagnostics[-evaluation_count:])
        ),
        "true_radius_max_abs_error": float(true_radius_error),
        "block_error_mean": float(np.mean(block_errors)),
        "block_error_median": float(np.median(block_errors)),
        "operator_error_mean": float(np.mean(operator_errors)),
        "operator_error_median": float(np.median(operator_errors)),
        "raw_response_error_mean": float(np.mean(raw_errors)),
        "raw_response_error_median": float(np.median(raw_errors)),
        "response_error_zero_ratio_mean": float(np.mean(zero_ratios)),
        "response_error_zero_ratio_median": float(np.median(zero_ratios)),
        "stability_qualified_error_mean": (
            float(np.mean(qualified_errors)) if qualified_errors else None
        ),
        "stability_qualified_rate": len(qualified_errors) / evaluation_count,
        "projected_sensitivity_error_mean": float(np.mean(projected_errors)),
        "prediction_rmse": float(np.sqrt(np.mean(prediction_squared_errors))),
        "estimated_instability_rate": estimated_unstable / evaluation_count,
        "cp_start_objective_spread": (
            cp_diagnostics["start_objective_spread"] if cp_diagnostics else None
        ),
        "cp_best_relative_objective": (
            cp_diagnostics["best_relative_objective"] if cp_diagnostics else None
        ),
        "selected_fused_penalty": selected_fused_penalty,
        "runtime_seconds": runtime_seconds,
        "failure": 0,
        "failure_reason": "",
    }


def run_replication(
    *,
    config: R006Config,
    approximation_target: float,
    target_rho: float,
    seed: int,
) -> list[dict[str, Any]]:
    panel = generate_approximate_rank_panel(
        n=config.n,
        t_len=config.t_len,
        true_rank=config.true_rank,
        head_rank=config.head_rank,
        approximation_target=approximation_target,
        separation_strength=config.separation_strength,
        target_rho=target_rho,
        sigma=config.sigma,
        seed=seed,
    )
    local_started = time.perf_counter()
    local_tensor, indices, separation_diagnostics = _estimate_local_blocks(
        panel["y"], panel["W"], config.window, config.ridge
    )
    local_runtime = time.perf_counter() - local_started

    methods: list[tuple[str, np.ndarray, float, int | None, dict[str, Any] | None, float | None]] = [
        ("local", local_tensor, local_runtime, None, None, None)
    ]

    spline_started = time.perf_counter()
    spline_tensor = _spline_reconstruct(local_tensor, config.spline_df)
    methods.append(
        (
            f"spline_df{config.spline_df}",
            spline_tensor,
            local_runtime + time.perf_counter() - spline_started,
            None,
            None,
            None,
        )
    )

    total_dates = len(indices)
    evaluation_count = max(1, int(math.ceil(config.evaluation_fraction * total_dates)))
    validation_count = max(1, int(math.ceil(config.validation_fraction * total_dates)))
    validation_stop = total_dates - evaluation_count
    validation_start = max(0, validation_stop - validation_count)
    validation_positions = range(validation_start, validation_stop)
    fused_started = time.perf_counter()
    fused_candidates = []
    for penalty in config.fused_penalties:
        candidate, candidate_diagnostics = _fused_reconstruct(
            local_tensor, penalty, config
        )
        if not candidate_diagnostics["converged"]:
            raise RuntimeError(f"fused-TV did not converge for penalty {penalty}")
        score = _prediction_rmse(
            candidate, panel, indices, validation_positions, config.n
        )
        fused_candidates.append((score, penalty, candidate))
    _, selected_penalty, fused_tensor = min(fused_candidates, key=lambda item: item[0])
    methods.append(
        (
            "fused_tv",
            fused_tensor,
            local_runtime + time.perf_counter() - fused_started,
            None,
            None,
            selected_penalty,
        )
    )

    for rank in config.fitted_ranks:
        cp_started = time.perf_counter()
        cp_result = _cp_reconstruct(
            local_tensor,
            rank,
            seed=seed + 700_001 + 100 * rank,
            iterations=config.cp_iterations,
            starts=config.cp_starts,
            tolerance=config.cp_tolerance,
            return_diagnostics=True,
        )
        cp_tensor, cp_diagnostics = cp_result
        methods.append(
            (
                f"cp_rank{rank}",
                cp_tensor,
                local_runtime + time.perf_counter() - cp_started,
                rank,
                cp_diagnostics,
                None,
            )
        )

        tucker_started = time.perf_counter()
        tucker_tensor = _tucker_reconstruct(local_tensor, rank)
        methods.append(
            (
                f"tucker_{rank}{rank}{rank}",
                tucker_tensor,
                local_runtime + time.perf_counter() - tucker_started,
                rank,
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
            diagnostics=separation_diagnostics,
            config=config,
            approximation_target=approximation_target,
            target_rho=target_rho,
            seed=seed,
            runtime_seconds=runtime,
            method_rank=method_rank,
            cp_diagnostics=cp_diagnostics,
            selected_fused_penalty=selected_penalty,
        )
        for method, tensor, runtime, method_rank, cp_diagnostics, selected_penalty in methods
    ]


def _method_names(config: R006Config) -> list[str]:
    names = ["local", f"spline_df{config.spline_df}", "fused_tv"]
    for rank in config.fitted_ranks:
        names.extend([f"cp_rank{rank}", f"tucker_{rank}{rank}{rank}"])
    return names


def _run_task(task: tuple[R006Config, float, float, int]) -> list[dict[str, Any]]:
    config, approximation_target, target_rho, seed = task
    try:
        return run_replication(
            config=config,
            approximation_target=approximation_target,
            target_rho=target_rho,
            seed=seed,
        )
    except Exception as exc:
        return [
            {
                "approximation_target": approximation_target,
                "actual_a3_ratio": None,
                "actual_a5_ratio": None,
                "target_rho": target_rho,
                "seed": seed,
                "method": method,
                "method_rank": None,
                "N": config.n,
                "T": config.t_len,
                "evaluation_dates": 0,
                "separation_diagnostic_median": None,
                "true_radius_max_abs_error": None,
                "block_error_mean": None,
                "block_error_median": None,
                "operator_error_mean": None,
                "operator_error_median": None,
                "raw_response_error_mean": None,
                "raw_response_error_median": None,
                "response_error_zero_ratio_mean": None,
                "response_error_zero_ratio_median": None,
                "stability_qualified_error_mean": None,
                "stability_qualified_rate": None,
                "projected_sensitivity_error_mean": None,
                "prediction_rmse": None,
                "estimated_instability_rate": None,
                "cp_start_objective_spread": None,
                "cp_best_relative_objective": None,
                "selected_fused_penalty": None,
                "runtime_seconds": None,
                "failure": 1,
                "failure_reason": f"{type(exc).__name__}: {exc}",
            }
            for method in _method_names(config)
        ]


def _quantile(values: list[float], probability: float) -> float | None:
    return float(np.quantile(values, probability)) if values else None


def _summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[float, float, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["approximation_target"], row["target_rho"], row["method"])
        groups.setdefault(key, []).append(row)
    metrics = [
        "actual_a3_ratio",
        "actual_a5_ratio",
        "block_error_mean",
        "operator_error_mean",
        "raw_response_error_mean",
        "response_error_zero_ratio_mean",
        "stability_qualified_rate",
        "projected_sensitivity_error_mean",
        "prediction_rmse",
        "estimated_instability_rate",
        "cp_start_objective_spread",
        "runtime_seconds",
    ]
    summary = []
    for (approximation_target, target_rho, method), group in sorted(groups.items()):
        record: dict[str, Any] = {
            "approximation_target": approximation_target,
            "target_rho": target_rho,
            "method": method,
            "replications": len(group),
            "failures": sum(row["failure"] for row in group),
        }
        for metric in metrics:
            values = [
                float(row[metric])
                for row in group
                if row["failure"] == 0 and row[metric] is not None
            ]
            record[f"{metric}_median"] = _quantile(values, 0.5)
            record[f"{metric}_q25"] = _quantile(values, 0.25)
            record[f"{metric}_q75"] = _quantile(values, 0.75)
        summary.append(record)
    return summary


def _gate_checks(
    rows: list[dict[str, Any]], config: R006Config, expected_rows: int
) -> dict[str, Any]:
    successful = [row for row in rows if row["failure"] == 0]
    calibration_errors = [
        abs(row["actual_a3_ratio"] - row["approximation_target"])
        for row in successful
    ]
    radius_errors = [row["true_radius_max_abs_error"] for row in successful]
    completion_rate = len(successful) / expected_rows

    by_key: dict[tuple[float, float, int], dict[str, dict[str, Any]]] = {}
    for row in successful:
        key = (row["approximation_target"], row["target_rho"], row["seed"])
        by_key.setdefault(key, {})[row["method"]] = row

    cell_results: dict[str, Any] = {}
    primary_methods = [
        f"cp_rank{config.head_rank}",
        f"tucker_{config.head_rank}{config.head_rank}{config.head_rank}",
    ]
    required_cells_pass = True
    for approximation_target in (0.10, 0.25):
        for target_rho in STABILITY_LEVELS:
            method_results = {}
            for method in primary_methods:
                improvements_local = []
                improvements_fused = []
                joint_wins = []
                operator_errors = []
                zero_ratios = []
                for seed in SEEDS:
                    methods = by_key.get((approximation_target, target_rho, seed), {})
                    if not {method, "local", "fused_tv"}.issubset(methods):
                        continue
                    current = methods[method]
                    local = methods["local"]
                    fused = methods["fused_tv"]
                    improvements_local.append(
                        1.0
                        - current["raw_response_error_mean"]
                        / local["raw_response_error_mean"]
                    )
                    improvements_fused.append(
                        1.0
                        - current["raw_response_error_mean"]
                        / fused["raw_response_error_mean"]
                    )
                    joint_wins.append(
                        current["raw_response_error_mean"]
                        < min(
                            local["raw_response_error_mean"],
                            fused["raw_response_error_mean"],
                        )
                    )
                    operator_errors.append(current["operator_error_mean"])
                    zero_ratios.append(current["response_error_zero_ratio_mean"])
                result = {
                    "paired_median_improvement_vs_local": _quantile(
                        improvements_local, 0.5
                    ),
                    "paired_median_improvement_vs_fused": _quantile(
                        improvements_fused, 0.5
                    ),
                    "joint_win_rate": float(np.mean(joint_wins)) if joint_wins else 0.0,
                    "median_relative_operator_error": _quantile(operator_errors, 0.5),
                    "median_response_zero_ratio": _quantile(zero_ratios, 0.5),
                }
                result["pass"] = (
                    result["paired_median_improvement_vs_local"] is not None
                    and result["paired_median_improvement_vs_local"] >= 0.10
                    and result["paired_median_improvement_vs_fused"] >= 0.10
                    and result["joint_win_rate"] >= 0.70
                    and result["median_relative_operator_error"] < 1.0
                    and result["median_response_zero_ratio"] < 1.0
                )
                method_results[method] = result
            cell_pass = any(result["pass"] for result in method_results.values())
            required_cells_pass &= cell_pass
            cell_results[f"a3={approximation_target:.2f},rho={target_rho:.2f}"] = {
                "pass": cell_pass,
                "methods": method_results,
            }

    metric_storage_contract = all(
        row["raw_response_error_mean"] is not None
        and row["projected_sensitivity_error_mean"] is not None
        and row["response_error_zero_ratio_mean"] is not None
        for row in successful
    )
    criteria = {
        "a3_calibration": max(calibration_errors, default=math.inf) < 1e-6,
        "rank3_approximate_truth_gate": required_cells_pass,
        "completion_rate_at_least_95_percent": completion_rate >= 0.95,
        "radius_and_metric_contract": max(radius_errors, default=math.inf) < 1e-8
        and metric_storage_contract,
    }
    return {
        "status": "PASS" if all(criteria.values()) else "FAIL",
        "criteria": criteria,
        "max_a3_calibration_error": max(calibration_errors, default=math.inf),
        "max_true_radius_abs_error": max(radius_errors, default=math.inf),
        "completion_rate": completion_rate,
        "required_cell_results": cell_results,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_report(
    output_dir: Path,
    *,
    config: R006Config,
    rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    checks: dict[str, Any],
    run_type: str,
    elapsed_seconds: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "r006_replications.csv", rows)
    _write_csv(output_dir / "r006_summary.csv", summary)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_type": run_type,
        "status": checks["status"],
        "protocol": "refine-logs/R006_PROTOCOL_20260715.md",
        "config": asdict(config),
        "grid": {
            "approximation_targets": sorted(
                {row["approximation_target"] for row in rows}
            ),
            "stability_levels": sorted({row["target_rho"] for row in rows}),
            "seeds": sorted({row["seed"] for row in rows}),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "machine": platform.machine(),
            "compute_route": "CPU / Apple Accelerate",
            "metal_backend_used": False,
        },
        "elapsed_seconds": elapsed_seconds,
        "checks": checks,
        "row_count": len(rows),
        "summary": summary,
    }
    (output_dir / "r006_results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    criteria_rows = "\n".join(
        f"| {name} | {'PASS' if passed else 'FAIL'} |"
        for name, passed in checks["criteria"].items()
    )
    gate_rows = []
    for cell, cell_result in checks["required_cell_results"].items():
        for method, result in cell_result["methods"].items():
            improvement_local = result["paired_median_improvement_vs_local"]
            improvement_fused = result["paired_median_improvement_vs_fused"]
            operator_error = result["median_relative_operator_error"]
            zero_ratio = result["median_response_zero_ratio"]
            gate_rows.append(
                f"| `{cell}` | `{method}` | {'PASS' if result['pass'] else 'FAIL'} | "
                f"{f'{100.0 * improvement_local:.1f}%' if improvement_local is not None else 'n/a'} | "
                f"{f'{100.0 * improvement_fused:.1f}%' if improvement_fused is not None else 'n/a'} | "
                f"{100.0 * result['joint_win_rate']:.1f}% | "
                f"{f'{operator_error:.3f}' if operator_error is not None else 'n/a'} | "
                f"{f'{zero_ratio:.3f}' if zero_ratio is not None else 'n/a'} |"
            )
    primary_summary = [
        record
        for record in summary
        if record["method"]
        in {"local", "fused_tv", f"cp_rank{config.head_rank}", f"tucker_{config.head_rank}{config.head_rank}{config.head_rank}"}
    ]
    cell_rows = "\n".join(
        "| {approximation_target:.2f} | {target_rho:.2f} | `{method}` | {operator:.3f} | {response:.6f} | {zero:.3f} | {failures}/{replications} |".format(
            operator=record["operator_error_mean_median"] or 0.0,
            response=record["raw_response_error_mean_median"] or 0.0,
            zero=record["response_error_zero_ratio_mean_median"] or 0.0,
            **record,
        )
        for record in primary_summary
    )
    markdown = f"""# R006 Approximate-Rank Pilot

- Run type: **{run_type}**
- Stop-go status: **{checks['status']}**
- Completed rows: {sum(row['failure'] == 0 for row in rows)}/{len(rows)}
- Elapsed time: {elapsed_seconds:.2f} seconds
- Compute route: CPU / Apple Accelerate; Metal backend not used
- Protocol: `refine-logs/R006_PROTOCOL_20260715.md`

## Frozen Checks

| Criterion | Result |
| --- | --- |
{criteria_rows}

- Maximum a3 calibration error: `{checks['max_a3_calibration_error']:.3e}`
- Maximum true-radius absolute error: `{checks['max_true_radius_abs_error']:.3e}`

## Required Rank-3 Cells

| Cell | Method | Gate | vs local | vs fused-TV | Joint win rate | Operator error | Zero ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(gate_rows)}

## Primary Method Summary

| a3 target | Query rho | Method | Operator error | Raw response error | Zero ratio | Failures |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
{cell_rows}

Rank-2 and rank-5 rows are diagnostic only. Raw, stability-qualified and projected-sensitivity errors remain separate. This pilot does not alter the rejected NCS manuscript or canonical benchmark outputs.
"""
    (output_dir / "r006_results.md").write_text(markdown, encoding="utf-8")


def run_grid(
    *,
    config: R006Config,
    approximation_targets: tuple[float, ...],
    stability_levels: tuple[float, ...],
    seeds: tuple[int, ...],
    workers: int,
    output_dir: Path,
    run_type: str,
) -> dict[str, Any]:
    output_dir = output_dir.expanduser()
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir = output_dir.resolve()
    tasks = [
        (config, approximation_target, target_rho, seed)
        for approximation_target in approximation_targets
        for target_rho in stability_levels
        for seed in seeds
    ]
    started = time.perf_counter()
    if workers == 1:
        nested_rows = [_run_task(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            nested_rows = list(executor.map(_run_task, tasks))
    rows = [row for group in nested_rows for row in group]
    summary = _summarize_rows(rows)
    checks = _gate_checks(rows, config, expected_rows=len(tasks) * len(_method_names(config)))
    elapsed = time.perf_counter() - started
    _write_report(
        output_dir,
        config=config,
        rows=rows,
        summary=summary,
        checks=checks,
        run_type=run_type,
        elapsed_seconds=elapsed,
    )
    try:
        display_output_dir = output_dir.relative_to(ROOT)
    except ValueError:
        display_output_dir = output_dir
    return {
        "status": checks["status"],
        "run_type": run_type,
        "output_dir": str(display_output_dir),
        "rows": len(rows),
        "elapsed_seconds": elapsed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, default=min(5, max(1, os.cpu_count() or 1)))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")

    if args.smoke:
        config = R006Config(
            n=8,
            t_len=90,
            window=36,
            true_rank=6,
            head_rank=3,
            fitted_ranks=(2, 3, 5),
            spline_df=6,
            cp_iterations=15,
            cp_starts=2,
            fused_penalties=(0.10, 0.50),
            fused_max_iterations=100,
            evaluation_fraction=0.20,
            validation_fraction=0.20,
        )
        approximation_targets = (0.0, 0.25)
        stability_levels = (0.80,)
        seeds = (240100, 240101)
        output_dir = args.output_dir or (
            ROOT / "output" / "high_impact_revision" / "r006_smoke"
        )
        run_type = "SMOKE"
    else:
        config = R006Config()
        approximation_targets = APPROXIMATION_TARGETS
        stability_levels = STABILITY_LEVELS
        seeds = SEEDS
        output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
        run_type = "FULL_PROTOCOL"

    result = run_grid(
        config=config,
        approximation_targets=approximation_targets,
        stability_levels=stability_levels,
        seeds=seeds,
        workers=args.workers,
        output_dir=output_dir,
        run_type=run_type,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
