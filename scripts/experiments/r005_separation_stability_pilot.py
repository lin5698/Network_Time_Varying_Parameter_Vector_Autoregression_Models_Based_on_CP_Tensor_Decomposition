"""R005 theory-aligned separation x stability stop-go pilot."""

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
from scipy.interpolate import BSpline

try:
    from scripts.experiments.high_impact_metrics import (
        evaluate_response_pair,
        spectral_radius,
    )
except ModuleNotFoundError:  # Direct script execution from this directory.
    from high_impact_metrics import evaluate_response_pair, spectral_radius


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "output" / "high_impact_revision" / "r005_phase_pilot"
SEPARATION_LEVELS = (0.02, 0.15, 0.45)
STABILITY_LEVELS = (0.50, 0.95, 1.01)
SEEDS = tuple(range(240100, 240110))


@dataclass(frozen=True)
class PilotConfig:
    n: int = 20
    t_len: int = 200
    window: int = 80
    rank: int = 3
    sigma: float = 0.25
    ridge: float = 0.001
    horizon: int = 8
    stability_threshold: float = 0.98
    projection_target: float = 0.95
    spline_df: int = 10
    cp_iterations: int = 50
    cp_starts: int = 2
    cp_tolerance: float = 1e-6
    evaluation_fraction: float = 0.30


def _row_normalize(matrix: np.ndarray) -> np.ndarray:
    result = np.maximum(np.asarray(matrix, dtype=float), 0.0).copy()
    np.fill_diagonal(result, 0.0)
    row_sums = result.sum(axis=1)
    for row_index, row_sum in enumerate(row_sums):
        if row_sum <= 1e-12:
            result[row_index, (row_index + 1) % result.shape[0]] = 1.0
    return result / result.sum(axis=1, keepdims=True)


def _random_topology(rng: np.random.Generator, n: int) -> np.ndarray:
    weights = rng.gamma(shape=1.5, scale=1.0, size=(n, n))
    mask = rng.random((n, n)) < 0.45
    weights[mask] = 0.0
    return _row_normalize(weights)


def _topology_path(
    rng: np.random.Generator,
    n: int,
    t_len: int,
    separation_strength: float,
) -> tuple[np.ndarray, np.ndarray]:
    if not 0.0 <= separation_strength <= 1.0:
        raise ValueError("separation_strength must lie in [0, 1]")

    base = _random_topology(rng, n)
    latent = _random_topology(rng, n)
    path = np.empty((t_len, n, n), dtype=float)
    for date in range(t_len):
        innovation = _random_topology(rng, n)
        latent = _row_normalize(0.70 * latent + 0.30 * innovation)
        path[date] = _row_normalize(
            (1.0 - separation_strength) * base
            + separation_strength * latent
        )
    return base, path


def generate_panel(
    *,
    n: int,
    t_len: int,
    rank: int,
    separation_strength: float,
    target_rho: float,
    sigma: float,
    seed: int,
) -> dict[str, np.ndarray]:
    """Generate a separated low-rank network VAR with a fixed query radius."""
    if rank <= 0 or rank > n:
        raise ValueError("rank must be between 1 and n")
    if t_len < 3:
        raise ValueError("t_len must be at least 3")
    if target_rho <= 0:
        raise ValueError("target_rho must be positive")

    rng = np.random.default_rng(seed)
    spatial, _ = np.linalg.qr(rng.normal(size=(n, rank)), mode="reduced")
    base_topology, topology = _topology_path(
        rng, n, t_len, separation_strength
    )

    phase = np.linspace(0.0, np.pi, rank, endpoint=False)
    direct_weights = np.linspace(0.65, 0.35, rank)
    network_weights = np.linspace(0.25, -0.15, rank)
    dates = np.linspace(0.0, 1.0, t_len)
    temporal = np.column_stack(
        [
            1.0
            + 0.18 * np.sin(2.0 * np.pi * (component + 1) * dates + phase[component])
            + 0.06 * np.cos(2.0 * np.pi * dates + 0.5 * phase[component])
            for component in range(rank)
        ]
    )

    direct = np.empty((t_len, n, n), dtype=float)
    network = np.empty((t_len, n, n), dtype=float)
    query_operator = np.empty((t_len, n, n), dtype=float)
    observed_operator = np.empty((t_len, n, n), dtype=float)

    for date in range(t_len):
        direct_raw = (spatial * (direct_weights * temporal[date])) @ spatial.T
        network_raw = (spatial * (network_weights * temporal[date])) @ spatial.T
        query_raw = direct_raw + network_raw @ base_topology
        raw_radius = spectral_radius(query_raw)
        if raw_radius <= 1e-12:
            raise RuntimeError("generated query operator has zero spectral radius")
        scale = target_rho / raw_radius
        direct[date] = scale * direct_raw
        network[date] = scale * network_raw
        query_operator[date] = direct[date] + network[date] @ base_topology
        observed_operator[date] = direct[date] + network[date] @ topology[date]

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
    }


def rolling_separation_diagnostics(
    observations: np.ndarray,
    topology: np.ndarray,
    window: int,
) -> np.ndarray:
    """Return normalized residualized-exposure minimum eigenvalues."""
    y = np.asarray(observations, dtype=float)
    w = np.asarray(topology, dtype=float)
    if y.ndim != 2 or w.shape != (y.shape[0], y.shape[1], y.shape[1]):
        raise ValueError("observations and topology have incompatible shapes")
    if window <= y.shape[1] or window >= y.shape[0] - 1:
        raise ValueError("window must exceed n and leave evaluation dates")

    diagnostics = []
    for date in range(window, y.shape[0] - 1):
        direct_design = y[date - window : date]
        relevant_topology = w[date - window : date]
        exposure_design = np.einsum(
            "tij,tj->ti", relevant_topology, direct_design, optimize=True
        )
        projection, *_ = np.linalg.lstsq(
            direct_design, exposure_design, rcond=1e-10
        )
        residual = exposure_design - direct_design @ projection
        residual_gram = residual.T @ residual / window
        exposure_scale = float(np.trace(exposure_design.T @ exposure_design / window))
        exposure_scale /= y.shape[1]
        minimum_eigenvalue = max(
            float(np.linalg.eigvalsh(residual_gram)[0]), 0.0
        )
        diagnostics.append(minimum_eigenvalue / max(exposure_scale, 1e-12))
    return np.asarray(diagnostics)


def _estimate_local_blocks(
    observations: np.ndarray,
    topology: np.ndarray,
    window: int,
    ridge: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = observations.shape[1]
    blocks = []
    indices = []
    diagnostics = rolling_separation_diagnostics(observations, topology, window)

    for date in range(window, observations.shape[0] - 1):
        direct_design = observations[date - window : date]
        relevant_topology = topology[date - window : date]
        exposure_design = np.einsum(
            "tij,tj->ti", relevant_topology, direct_design, optimize=True
        )
        design = np.concatenate([direct_design, exposure_design], axis=1)
        outcome = observations[date - window + 1 : date + 1]
        gram = design.T @ design / window + ridge * np.eye(2 * n)
        cross_product = design.T @ outcome / window
        coefficient = np.linalg.solve(gram, cross_product).T
        blocks.append(coefficient)
        indices.append(date)

    tensor = np.stack(blocks, axis=2)
    return tensor, np.asarray(indices, dtype=int), diagnostics


def _cp_reconstruct(
    tensor: np.ndarray,
    rank: int,
    *,
    seed: int,
    iterations: int,
    starts: int,
    tolerance: float,
    return_diagnostics: bool = False,
) -> np.ndarray | tuple[np.ndarray, dict[str, Any]]:
    shape = tensor.shape
    if rank > min(shape):
        raise ValueError("CP rank exceeds a tensor dimension")
    tensor_norm = max(float(np.linalg.norm(tensor)), 1e-12)
    best_error = math.inf
    best_reconstruction = None
    start_errors = []

    def left_vectors(mode: int) -> np.ndarray:
        unfolded = np.moveaxis(tensor, mode, 0).reshape(shape[mode], -1)
        return np.linalg.svd(unfolded, full_matrices=False)[0][:, :rank]

    for start in range(starts):
        rng = np.random.default_rng(seed + 1009 * start)
        if start == 0:
            factor_a = left_vectors(0)
            factor_b = left_vectors(1)
            factor_c = left_vectors(2)
        else:
            factor_a = rng.normal(scale=0.3, size=(shape[0], rank))
            factor_b = rng.normal(scale=0.3, size=(shape[1], rank))
            factor_c = rng.normal(scale=0.3, size=(shape[2], rank))

        previous_error = math.inf
        for _ in range(iterations):
            gram = (factor_b.T @ factor_b) * (factor_c.T @ factor_c)
            mttkrp = np.einsum(
                "ijk,jr,kr->ir", tensor, factor_b, factor_c, optimize=True
            )
            factor_a = np.linalg.solve(
                gram + 1e-10 * np.eye(rank), mttkrp.T
            ).T

            gram = (factor_a.T @ factor_a) * (factor_c.T @ factor_c)
            mttkrp = np.einsum(
                "ijk,ir,kr->jr", tensor, factor_a, factor_c, optimize=True
            )
            factor_b = np.linalg.solve(
                gram + 1e-10 * np.eye(rank), mttkrp.T
            ).T

            gram = (factor_a.T @ factor_a) * (factor_b.T @ factor_b)
            mttkrp = np.einsum(
                "ijk,ir,jr->kr", tensor, factor_a, factor_b, optimize=True
            )
            factor_c = np.linalg.solve(
                gram + 1e-10 * np.eye(rank), mttkrp.T
            ).T

            for factor in (factor_b, factor_c):
                norms = np.maximum(np.linalg.norm(factor, axis=0), 1e-12)
                factor /= norms
                factor_a *= norms

            reconstruction = np.einsum(
                "ir,jr,kr->ijk",
                factor_a,
                factor_b,
                factor_c,
                optimize=True,
            )
            error = float(np.linalg.norm(tensor - reconstruction) / tensor_norm)
            if abs(previous_error - error) <= tolerance * max(previous_error, 1.0):
                break
            previous_error = error

        if error < best_error:
            best_error = error
            best_reconstruction = reconstruction.copy()
        start_errors.append(error)

    if best_reconstruction is None:
        raise RuntimeError("CP-ALS did not produce a reconstruction")
    if return_diagnostics:
        return best_reconstruction, {
            "start_relative_objectives": [float(value) for value in start_errors],
            "best_relative_objective": float(best_error),
            "start_objective_spread": float(max(start_errors) - min(start_errors)),
        }
    return best_reconstruction


def _tucker_reconstruct(tensor: np.ndarray, rank: int) -> np.ndarray:
    factors = []
    for mode, dimension in enumerate(tensor.shape):
        unfolded = np.moveaxis(tensor, mode, 0).reshape(dimension, -1)
        factors.append(
            np.linalg.svd(unfolded, full_matrices=False)[0][
                :, : min(rank, dimension)
            ]
        )
    factor_a, factor_b, factor_c = factors
    core = np.einsum(
        "ia,jb,kc,ijk->abc",
        factor_a,
        factor_b,
        factor_c,
        tensor,
        optimize=True,
    )
    return np.einsum(
        "ia,jb,kc,abc->ijk",
        factor_a,
        factor_b,
        factor_c,
        core,
        optimize=True,
    )


def _spline_reconstruct(tensor: np.ndarray, degrees_of_freedom: int) -> np.ndarray:
    dates = tensor.shape[2]
    degree = 3
    basis_count = min(max(degrees_of_freedom, degree + 1), dates)
    internal_count = basis_count - degree - 1
    internal = (
        np.linspace(0.0, 1.0, internal_count + 2)[1:-1]
        if internal_count > 0
        else np.asarray([], dtype=float)
    )
    knots = np.concatenate(
        [np.zeros(degree + 1), internal, np.ones(degree + 1)]
    )
    locations = np.linspace(0.0, 1.0, dates)
    design = BSpline.design_matrix(locations, knots, degree).toarray()
    flattened = np.moveaxis(tensor, 2, 0).reshape(dates, -1)
    coefficients, *_ = np.linalg.lstsq(design, flattened, rcond=1e-10)
    reconstructed = design @ coefficients
    return np.moveaxis(reconstructed.reshape(dates, *tensor.shape[:2]), 0, 2)


def _mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def _evaluate_method(
    *,
    method: str,
    tensor: np.ndarray,
    panel: dict[str, np.ndarray],
    indices: np.ndarray,
    diagnostics: np.ndarray,
    config: PilotConfig,
    separation_strength: float,
    target_rho: float,
    seed: int,
    runtime_seconds: float,
) -> dict[str, Any]:
    n = config.n
    evaluation_count = max(1, int(math.ceil(config.evaluation_fraction * len(indices))))
    evaluation_positions = range(len(indices) - evaluation_count, len(indices))
    operator_errors = []
    raw_errors = []
    qualified_errors = []
    projected_errors = []
    prediction_squared_errors = []
    estimated_unstable = 0

    for position in evaluation_positions:
        date = int(indices[position])
        coefficient = tensor[:, :, position]
        direct_estimate = coefficient[:, :n]
        network_estimate = coefficient[:, n:]
        query_estimate = (
            direct_estimate + network_estimate @ panel["W_reference"]
        )
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
        raw_errors.append(float(response["raw_response_error"]))
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
        "separation_strength": separation_strength,
        "target_rho": target_rho,
        "seed": seed,
        "method": method,
        "N": config.n,
        "T": config.t_len,
        "evaluation_dates": evaluation_count,
        "separation_diagnostic_median": float(
            np.median(diagnostics[-evaluation_count:])
        ),
        "true_radius_max_abs_error": float(true_radius_error),
        "operator_error_mean": float(np.mean(operator_errors)),
        "operator_error_median": float(np.median(operator_errors)),
        "raw_response_error_mean": float(np.mean(raw_errors)),
        "raw_response_error_median": float(np.median(raw_errors)),
        "stability_qualified_error_mean": _mean_or_none(qualified_errors),
        "stability_qualified_rate": len(qualified_errors) / evaluation_count,
        "projected_sensitivity_error_mean": float(np.mean(projected_errors)),
        "prediction_rmse": float(np.sqrt(np.mean(prediction_squared_errors))),
        "estimated_instability_rate": estimated_unstable / evaluation_count,
        "runtime_seconds": runtime_seconds,
        "failure": 0,
        "failure_reason": "",
    }


def run_replication(
    *,
    config: PilotConfig,
    separation_strength: float,
    target_rho: float,
    seed: int,
) -> list[dict[str, Any]]:
    panel = generate_panel(
        n=config.n,
        t_len=config.t_len,
        rank=config.rank,
        separation_strength=separation_strength,
        target_rho=target_rho,
        sigma=config.sigma,
        seed=seed,
    )
    local_started = time.perf_counter()
    local_tensor, indices, diagnostics = _estimate_local_blocks(
        panel["y"], panel["W"], config.window, config.ridge
    )
    local_runtime = time.perf_counter() - local_started

    method_tensors = [("local", local_tensor, local_runtime)]

    cp_started = time.perf_counter()
    cp_tensor = _cp_reconstruct(
        local_tensor,
        config.rank,
        seed=seed + 700_001,
        iterations=config.cp_iterations,
        starts=config.cp_starts,
        tolerance=config.cp_tolerance,
    )
    method_tensors.append(
        (
            f"cp_rank{config.rank}",
            cp_tensor,
            local_runtime + time.perf_counter() - cp_started,
        )
    )

    tucker_started = time.perf_counter()
    tucker_tensor = _tucker_reconstruct(local_tensor, config.rank)
    method_tensors.append(
        (
            f"tucker_{config.rank}{config.rank}{config.rank}",
            tucker_tensor,
            local_runtime + time.perf_counter() - tucker_started,
        )
    )

    spline_started = time.perf_counter()
    spline_tensor = _spline_reconstruct(local_tensor, config.spline_df)
    method_tensors.append(
        (
            f"spline_df{config.spline_df}",
            spline_tensor,
            local_runtime + time.perf_counter() - spline_started,
        )
    )

    return [
        _evaluate_method(
            method=method,
            tensor=tensor,
            panel=panel,
            indices=indices,
            diagnostics=diagnostics,
            config=config,
            separation_strength=separation_strength,
            target_rho=target_rho,
            seed=seed,
            runtime_seconds=runtime,
        )
        for method, tensor, runtime in method_tensors
    ]


def _run_task(task: tuple[PilotConfig, float, float, int]) -> list[dict[str, Any]]:
    config, separation_strength, target_rho, seed = task
    try:
        return run_replication(
            config=config,
            separation_strength=separation_strength,
            target_rho=target_rho,
            seed=seed,
        )
    except Exception as exc:  # Preserve failed grid cells for the stop-go audit.
        methods = [
            "local",
            f"cp_rank{config.rank}",
            f"tucker_{config.rank}{config.rank}{config.rank}",
            f"spline_df{config.spline_df}",
        ]
        return [
            {
                "separation_strength": separation_strength,
                "target_rho": target_rho,
                "seed": seed,
                "method": method,
                "N": config.n,
                "T": config.t_len,
                "evaluation_dates": 0,
                "separation_diagnostic_median": None,
                "true_radius_max_abs_error": None,
                "operator_error_mean": None,
                "operator_error_median": None,
                "raw_response_error_mean": None,
                "raw_response_error_median": None,
                "stability_qualified_error_mean": None,
                "stability_qualified_rate": None,
                "projected_sensitivity_error_mean": None,
                "prediction_rmse": None,
                "estimated_instability_rate": None,
                "runtime_seconds": None,
                "failure": 1,
                "failure_reason": f"{type(exc).__name__}: {exc}",
            }
            for method in methods
        ]


def _quantile(values: list[float], probability: float) -> float | None:
    return float(np.quantile(values, probability)) if values else None


def _summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[float, float, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["separation_strength"], row["target_rho"], row["method"])
        groups.setdefault(key, []).append(row)

    summary = []
    metrics = [
        "operator_error_mean",
        "raw_response_error_mean",
        "stability_qualified_error_mean",
        "projected_sensitivity_error_mean",
        "prediction_rmse",
        "estimated_instability_rate",
        "runtime_seconds",
    ]
    for (separation_strength, target_rho, method), group in sorted(groups.items()):
        record: dict[str, Any] = {
            "separation_strength": separation_strength,
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


def _paired_improvements(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[float, float, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        if row["failure"] == 0:
            key = (row["separation_strength"], row["target_rho"], row["seed"])
            groups.setdefault(key, {})[row["method"]] = row

    records = []
    for (separation_strength, target_rho, seed), methods in sorted(groups.items()):
        local = methods.get("local")
        if local is None or not local["raw_response_error_mean"]:
            continue
        for method, row in methods.items():
            if method == "local":
                continue
            improvement = 1.0 - (
                row["raw_response_error_mean"] / local["raw_response_error_mean"]
            )
            records.append(
                {
                    "separation_strength": separation_strength,
                    "target_rho": target_rho,
                    "seed": seed,
                    "method": method,
                    "paired_raw_response_improvement": float(improvement),
                    "viable_cell": separation_strength >= 0.15 and target_rho <= 0.95,
                }
            )
    return records


def _stop_go_checks(
    rows: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    expected_rows: int,
) -> dict[str, Any]:
    successful = [row for row in rows if row["failure"] == 0]
    local_rows = [row for row in successful if row["method"] == "local"]
    separation_medians = {}
    for level in SEPARATION_LEVELS:
        values = [
            row["separation_diagnostic_median"]
            for row in local_rows
            if math.isclose(row["separation_strength"], level)
        ]
        if values:
            separation_medians[str(level)] = float(np.median(values))
    ordered = [separation_medians.get(str(level)) for level in SEPARATION_LEVELS]
    separation_monotone = all(
        left is not None and right is not None and right > left
        for left, right in zip(ordered, ordered[1:])
    )
    high_low_ratio = (
        ordered[-1] / max(ordered[0], 1e-15)
        if ordered[0] is not None and ordered[-1] is not None
        else None
    )

    radius_errors = [
        row["true_radius_max_abs_error"]
        for row in successful
        if row["true_radius_max_abs_error"] is not None
    ]
    max_radius_error = max(radius_errors) if radius_errors else math.inf
    completion_rate = len(successful) / expected_rows

    viable_by_method: dict[str, list[float]] = {}
    for record in paired:
        if record["viable_cell"]:
            viable_by_method.setdefault(record["method"], []).append(
                record["paired_raw_response_improvement"]
            )
    viable_medians = {
        method: float(np.median(values))
        for method, values in sorted(viable_by_method.items())
    }
    best_viable_improvement = max(viable_medians.values(), default=-math.inf)

    unstable_storage_valid = all(
        row["stability_qualified_rate"] == 0.0
        and row["stability_qualified_error_mean"] is None
        for row in successful
        if row["target_rho"] >= 0.98
    )
    projected_stored_separately = all(
        row["raw_response_error_mean"] is not None
        and row["projected_sensitivity_error_mean"] is not None
        for row in successful
    )

    criteria = {
        "separation_axis_controlled": separation_monotone
        and high_low_ratio is not None
        and high_low_ratio >= 4.0,
        "true_radius_targeted": max_radius_error < 1e-8,
        "viable_smoother_improvement": best_viable_improvement >= 0.10,
        "completion_rate_at_least_95_percent": completion_rate >= 0.95,
        "metric_storage_contract": unstable_storage_valid
        and projected_stored_separately,
    }
    return {
        "status": "PASS" if all(criteria.values()) else "FAIL",
        "criteria": criteria,
        "separation_medians": separation_medians,
        "separation_high_low_ratio": high_low_ratio,
        "max_true_radius_abs_error": max_radius_error,
        "completion_rate": completion_rate,
        "viable_paired_improvement_medians": viable_medians,
        "best_viable_paired_improvement": best_viable_improvement,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty CSV")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_report(
    output_dir: Path,
    *,
    config: PilotConfig,
    rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    paired: list[dict[str, Any]],
    checks: dict[str, Any],
    smoke: bool,
    elapsed_seconds: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "r005_replications.csv", rows)
    _write_csv(output_dir / "r005_summary.csv", summary)
    _write_csv(output_dir / "r005_paired_improvements.csv", paired)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_type": "SMOKE" if smoke else "FULL_PROTOCOL",
        "status": checks["status"],
        "protocol": "refine-logs/R005_PROTOCOL_20260715.md",
        "config": asdict(config),
        "grid": {
            "separation_levels": sorted(
                {row["separation_strength"] for row in rows}
            ),
            "stability_levels": sorted({row["target_rho"] for row in rows}),
            "seeds": sorted({row["seed"] for row in rows}),
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "machine": platform.machine(),
            "processor": platform.processor(),
            "compute_route": "CPU / Apple Accelerate",
            "metal_backend_used": False,
        },
        "elapsed_seconds": elapsed_seconds,
        "checks": checks,
        "row_count": len(rows),
        "summary": summary,
    }
    (output_dir / "r005_results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    criteria_rows = "\n".join(
        f"| {name} | {'PASS' if passed else 'FAIL'} |"
        for name, passed in checks["criteria"].items()
    )
    viable_rows = "\n".join(
        f"| `{method}` | {100.0 * value:.1f}% |"
        for method, value in checks["viable_paired_improvement_medians"].items()
    ) or "| n/a | n/a |"
    cell_rows = "\n".join(
        "| {separation_strength:.2f} | {target_rho:.2f} | `{method}` | {error} | {failures}/{replications} |".format(
            error=(
                f"{record['raw_response_error_mean_median']:.6f}"
                if record["raw_response_error_mean_median"] is not None
                else "n/a"
            ),
            **record,
        )
        for record in summary
    )
    markdown = f"""# R005 Separation x Stability Pilot

- Run type: **{'SMOKE' if smoke else 'FULL_PROTOCOL'}**
- Stop-go status: **{checks['status']}**
- Completed rows: {sum(row['failure'] == 0 for row in rows)}/{len(rows)}
- Elapsed time: {elapsed_seconds:.2f} seconds
- Compute route: CPU / Apple Accelerate; Metal backend not used
- Protocol: `refine-logs/R005_PROTOCOL_20260715.md`

## Frozen Checks

| Criterion | Result |
| --- | --- |
{criteria_rows}

- Separation medians: `{json.dumps(checks['separation_medians'], sort_keys=True)}`
- High/low separation ratio: `{checks['separation_high_low_ratio']}`
- Maximum true-radius absolute error: `{checks['max_true_radius_abs_error']:.3e}`

## Viable-Regime Paired Raw-Response Improvement

| Method | Median improvement vs local |
| --- | ---: |
{viable_rows}

## Cell Summary

| Separation | Query rho | Method | Median raw response error | Failures |
| ---: | ---: | --- | ---: | ---: |
{cell_rows}

Raw, stability-qualified and projected-sensitivity response errors are stored as separate fields. This pilot does not alter the rejected NCS manuscript or its canonical benchmark outputs.
"""
    (output_dir / "r005_results.md").write_text(markdown, encoding="utf-8")


def run_grid(
    *,
    config: PilotConfig,
    separation_levels: tuple[float, ...],
    stability_levels: tuple[float, ...],
    seeds: tuple[int, ...],
    workers: int,
    output_dir: Path,
    smoke: bool,
) -> dict[str, Any]:
    output_dir = output_dir.expanduser()
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir = output_dir.resolve()
    tasks = [
        (config, separation_strength, target_rho, seed)
        for separation_strength in separation_levels
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
    paired = _paired_improvements(rows)
    checks = _stop_go_checks(rows, paired, expected_rows=len(tasks) * 4)
    elapsed = time.perf_counter() - started
    _write_report(
        output_dir,
        config=config,
        rows=rows,
        summary=summary,
        paired=paired,
        checks=checks,
        smoke=smoke,
        elapsed_seconds=elapsed,
    )
    try:
        display_output_dir = output_dir.relative_to(ROOT)
    except ValueError:
        display_output_dir = output_dir
    return {
        "status": checks["status"],
        "run_type": "SMOKE" if smoke else "FULL_PROTOCOL",
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
        config = PilotConfig(
            n=8,
            t_len=80,
            window=36,
            rank=2,
            spline_df=6,
            cp_iterations=20,
            cp_starts=1,
            evaluation_fraction=0.20,
        )
        separation_levels = (0.02, 0.45)
        stability_levels = (0.50, 1.01)
        seeds = (240100,)
        output_dir = args.output_dir or (
            ROOT / "output" / "high_impact_revision" / "r005_smoke"
        )
    else:
        config = PilotConfig()
        separation_levels = SEPARATION_LEVELS
        stability_levels = STABILITY_LEVELS
        seeds = SEEDS
        output_dir = args.output_dir or DEFAULT_OUTPUT_DIR

    result = run_grid(
        config=config,
        separation_levels=separation_levels,
        stability_levels=stability_levels,
        seeds=seeds,
        workers=args.workers,
        output_dir=output_dir,
        smoke=args.smoke,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
