"""Endpoint-blind estimators for the R006c experiment."""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from scripts.experiments.r005_separation_stability_pilot import (
        _cp_reconstruct,
        _tucker_reconstruct,
    )
    from scripts.experiments.r006b_stability_signal_deconfounding import (
        _fused_reconstruct,
        _prediction_rmse,
        estimate_local_blocks,
        fit_scale_adaptive_ridge,
    )
    from scripts.experiments.r006c_endpoint_protocol import (
        METHODS,
        EstimationInputs,
        R006CConfig,
        method_seed,
    )
except ModuleNotFoundError:  # Direct execution from scripts/experiments.
    from r005_separation_stability_pilot import (  # type: ignore
        _cp_reconstruct,
        _tucker_reconstruct,
    )
    from r006b_stability_signal_deconfounding import (  # type: ignore
        _fused_reconstruct,
        _prediction_rmse,
        estimate_local_blocks,
        fit_scale_adaptive_ridge,
    )
    from r006c_endpoint_protocol import (  # type: ignore
        METHODS,
        EstimationInputs,
        R006CConfig,
        method_seed,
    )


@dataclass(frozen=True)
class FittedMethod:
    name: str
    parameterization: str
    tensor: np.ndarray
    indices: np.ndarray
    separation: np.ndarray
    ridge_diagnostics: dict[str, np.ndarray]
    runtime_seconds: float
    reconstruction_diagnostics: dict[str, Any]
    selected_fused_penalty: float | None = None


@dataclass(frozen=True)
class FittedBundle:
    methods: dict[str, FittedMethod]

    def fit_digest(self) -> str:
        digest = hashlib.sha256()
        for name in METHODS:
            method = self.methods[name]
            digest.update(name.encode("ascii"))
            digest.update(method.parameterization.encode("ascii"))
            digest.update(np.ascontiguousarray(method.tensor).tobytes())
            digest.update(np.ascontiguousarray(method.indices).tobytes())
            digest.update(
                json.dumps(
                    method.reconstruction_diagnostics,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("ascii")
            )
            digest.update(repr(method.selected_fused_penalty).encode("ascii"))
        return digest.hexdigest()

    def selected_hyperparameters(self) -> dict[str, Any]:
        return {
            name: {
                "rank": 3 if name in {
                    "block_cp3",
                    "block_tucker333",
                    "anchor_split_cp3",
                    "anchor_split_tucker333",
                    "collapsed_ref_tucker333",
                    "oracle_b_anchor",
                } else None,
                "fused_penalty": method.selected_fused_penalty,
                "reconstruction": method.reconstruction_diagnostics,
            }
            for name, method in self.methods.items()
        }


def estimate_anchor_local(
    inputs: EstimationInputs,
    *,
    window: int,
    ridge_multiplier: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    x = np.asarray(inputs.predictors, dtype=float)
    y = np.asarray(inputs.outcomes, dtype=float)
    w = np.asarray(inputs.topology, dtype=float)
    w_ref = np.asarray(inputs.W_ref, dtype=float)
    if x.ndim != 2 or y.shape != x.shape:
        raise ValueError("predictors and outcomes must be aligned matrices")
    if w.shape != (x.shape[0], x.shape[1], x.shape[1]):
        raise ValueError("topology has incompatible dimensions")
    if w_ref.shape != (x.shape[1], x.shape[1]):
        raise ValueError("W_ref has incompatible dimensions")
    if window <= 2 * x.shape[1] or window >= x.shape[0]:
        raise ValueError("window must exceed 2N and leave evaluation dates")

    blocks = []
    indices = []
    separation = []
    gram_scales = []
    ridge_penalties = []
    for date in range(window, x.shape[0]):
        predictor_window = x[date - window : date]
        outcome_window = y[date - window : date]
        delta_topology = w[date - window : date] - w_ref[None, :, :]
        delta_exposure = np.einsum(
            "tij,tj->ti", delta_topology, predictor_window, optimize=True
        )
        design = np.concatenate([predictor_window, delta_exposure], axis=1)
        coefficient, diagnostics = fit_scale_adaptive_ridge(
            design,
            outcome_window,
            ridge_multiplier=ridge_multiplier,
        )
        blocks.append(coefficient)
        indices.append(date)
        gram_scales.append(diagnostics["gram_scale"])
        ridge_penalties.append(diagnostics["ridge_penalty"])

        projection, *_ = np.linalg.lstsq(
            predictor_window, delta_exposure, rcond=1e-10
        )
        residual = delta_exposure - predictor_window @ projection
        residual_gram = residual.T @ residual / window
        exposure_scale = float(np.mean(np.square(delta_exposure)))
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


def select_fused_penalty(
    local_tensor: np.ndarray,
    panel: dict[str, Any],
    indices: np.ndarray,
    config: R006CConfig,
) -> tuple[float, dict[str, Any]]:
    """Select fused-TV strength with rolling-prefix validation fits."""
    total_dates = len(indices)
    evaluation_count = max(
        1, int(math.ceil(config.evaluation_fraction * total_dates))
    )
    validation_count = max(
        1, int(math.ceil(config.validation_fraction * total_dates))
    )
    validation_stop = total_dates - evaluation_count
    validation_start = max(0, validation_stop - validation_count)
    if validation_stop <= 1 or validation_start >= validation_stop:
        raise ValueError("insufficient pre-evaluation dates for fused-TV validation")

    validation_positions = list(range(validation_start, validation_stop))
    candidates = []
    candidate_scores: dict[str, float] = {}
    candidate_date_scores: dict[str, list[float]] = {}
    for penalty in config.fused_penalties:
        date_scores = []
        for position in validation_positions:
            prefix = local_tensor[:, :, : position + 1]
            reconstructed, diagnostics = _fused_reconstruct(
                prefix, penalty, config
            )
            if not diagnostics["converged"]:
                raise RuntimeError(
                    f"fused-TV did not converge for penalty {penalty} "
                    f"at validation position {position}"
                )
            score = _prediction_rmse(
                reconstructed,
                panel,
                indices[: position + 1],
                range(position, position + 1),
                config.n,
            )
            date_scores.append(score)
        aggregate_score = float(
            np.sqrt(np.mean(np.square(date_scores)))
        )
        key = f"{penalty:.12g}"
        candidate_scores[key] = aggregate_score
        candidate_date_scores[key] = date_scores
        candidates.append((aggregate_score, penalty))
    _, selected_penalty = min(candidates, key=lambda item: item[0])
    return selected_penalty, {
        "candidate_scores": candidate_scores,
        "candidate_date_scores": candidate_date_scores,
        "selection_dates": validation_stop,
        "validation_dates": validation_count,
        "validation_positions": validation_positions,
        "evaluation_dates_excluded": evaluation_count,
        "strict_rolling_prefix": True,
    }


def _cp_split(
    tensor: np.ndarray,
    *,
    n: int,
    config: R006CConfig,
    seed_m_ref: int,
    seed_b: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    m_ref, m_diagnostics = _cp_reconstruct(
        tensor[:, :n, :],
        config.fitted_rank,
        seed=seed_m_ref,
        iterations=config.cp_iterations,
        starts=config.cp_starts,
        tolerance=config.cp_tolerance,
        return_diagnostics=True,
    )
    b, b_diagnostics = _cp_reconstruct(
        tensor[:, n:, :],
        config.fitted_rank,
        seed=seed_b,
        iterations=config.cp_iterations,
        starts=config.cp_starts,
        tolerance=config.cp_tolerance,
        return_diagnostics=True,
    )
    return np.concatenate([m_ref, b], axis=1), {
        "M_ref": m_diagnostics,
        "B": b_diagnostics,
    }


def _tucker_split(
    tensor: np.ndarray,
    *,
    n: int,
    rank: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    m_ref = _tucker_reconstruct(tensor[:, :n, :], rank)
    b = _tucker_reconstruct(tensor[:, n:, :], rank)
    diagnostics = {
        "M_ref": {"kind": "tucker", "rank": rank},
        "B": {"kind": "tucker", "rank": rank},
    }
    return np.concatenate([m_ref, b], axis=1), diagnostics


def fit_method_bundle(
    inputs: EstimationInputs,
    *,
    truth_B: np.ndarray,
    config: R006CConfig,
    seed: int,
    layer: str,
    rho: float,
    a3: float,
    eta: float,
) -> FittedBundle:
    if truth_B.shape != (config.t_len, config.n, config.n):
        raise ValueError("truth_B has incompatible dimensions")

    methods: dict[str, FittedMethod] = {}

    started = time.perf_counter()
    block_local, indices, block_separation, block_ridge = estimate_local_blocks(
        inputs.predictors,
        inputs.outcomes,
        inputs.topology,
        window=config.window,
        ridge_multiplier=config.ridge_multiplier,
    )
    methods["block_local"] = FittedMethod(
        name="block_local",
        parameterization="block",
        tensor=block_local,
        indices=indices,
        separation=block_separation,
        ridge_diagnostics=block_ridge,
        runtime_seconds=time.perf_counter() - started,
        reconstruction_diagnostics={"kind": "none"},
    )

    fit_panel = {
        "predictors": inputs.predictors,
        "outcomes": inputs.outcomes,
        "W": inputs.topology,
    }
    started = time.perf_counter()
    selected_penalty, selection_diagnostics = select_fused_penalty(
        block_local, fit_panel, indices, config
    )
    block_fused, fused_diagnostics = _fused_reconstruct(
        block_local, selected_penalty, config
    )
    methods["block_fused_tv"] = FittedMethod(
        name="block_fused_tv",
        parameterization="block",
        tensor=block_fused,
        indices=indices,
        separation=block_separation,
        ridge_diagnostics=block_ridge,
        runtime_seconds=time.perf_counter() - started,
        reconstruction_diagnostics={
            "selection": selection_diagnostics,
            "fit": fused_diagnostics,
        },
        selected_fused_penalty=selected_penalty,
    )

    started = time.perf_counter()
    block_cp, block_cp_diagnostics = _cp_reconstruct(
        block_local,
        config.fitted_rank,
        seed=method_seed(seed, layer, rho, a3, eta, "block_cp3"),
        iterations=config.cp_iterations,
        starts=config.cp_starts,
        tolerance=config.cp_tolerance,
        return_diagnostics=True,
    )
    methods["block_cp3"] = FittedMethod(
        name="block_cp3",
        parameterization="block",
        tensor=block_cp,
        indices=indices,
        separation=block_separation,
        ridge_diagnostics=block_ridge,
        runtime_seconds=time.perf_counter() - started,
        reconstruction_diagnostics={"joint": block_cp_diagnostics},
    )

    started = time.perf_counter()
    block_tucker = _tucker_reconstruct(block_local, config.fitted_rank)
    methods["block_tucker333"] = FittedMethod(
        name="block_tucker333",
        parameterization="block",
        tensor=block_tucker,
        indices=indices,
        separation=block_separation,
        ridge_diagnostics=block_ridge,
        runtime_seconds=time.perf_counter() - started,
        reconstruction_diagnostics={
            "joint": {"kind": "tucker", "rank": config.fitted_rank}
        },
    )

    started = time.perf_counter()
    anchor_local, anchor_indices, anchor_separation, anchor_ridge = (
        estimate_anchor_local(
            inputs,
            window=config.window,
            ridge_multiplier=config.ridge_multiplier,
        )
    )
    if not np.array_equal(indices, anchor_indices):
        raise RuntimeError("block and anchor estimators returned different dates")
    methods["anchor_local"] = FittedMethod(
        name="anchor_local",
        parameterization="anchor",
        tensor=anchor_local,
        indices=indices,
        separation=anchor_separation,
        ridge_diagnostics=anchor_ridge,
        runtime_seconds=time.perf_counter() - started,
        reconstruction_diagnostics={"kind": "none"},
    )

    started = time.perf_counter()
    anchor_cp, anchor_cp_diagnostics = _cp_split(
        anchor_local,
        n=config.n,
        config=config,
        seed_m_ref=method_seed(
            seed, layer, rho, a3, eta, "anchor_split_cp3:M_ref"
        ),
        seed_b=method_seed(seed, layer, rho, a3, eta, "anchor_split_cp3:B"),
    )
    methods["anchor_split_cp3"] = FittedMethod(
        name="anchor_split_cp3",
        parameterization="anchor",
        tensor=anchor_cp,
        indices=indices,
        separation=anchor_separation,
        ridge_diagnostics=anchor_ridge,
        runtime_seconds=time.perf_counter() - started,
        reconstruction_diagnostics=anchor_cp_diagnostics,
    )

    started = time.perf_counter()
    anchor_tucker, anchor_tucker_diagnostics = _tucker_split(
        anchor_local, n=config.n, rank=config.fitted_rank
    )
    tucker_runtime = time.perf_counter() - started
    methods["anchor_split_tucker333"] = FittedMethod(
        name="anchor_split_tucker333",
        parameterization="anchor",
        tensor=anchor_tucker,
        indices=indices,
        separation=anchor_separation,
        ridge_diagnostics=anchor_ridge,
        runtime_seconds=tucker_runtime,
        reconstruction_diagnostics=anchor_tucker_diagnostics,
    )

    smoothed_m_ref = anchor_tucker[:, : config.n, :]
    methods["collapsed_ref_tucker333"] = FittedMethod(
        name="collapsed_ref_tucker333",
        parameterization="collapsed",
        tensor=smoothed_m_ref,
        indices=indices,
        separation=anchor_separation,
        ridge_diagnostics=anchor_ridge,
        runtime_seconds=tucker_runtime,
        reconstruction_diagnostics=anchor_tucker_diagnostics["M_ref"],
    )

    true_b_tensor = np.moveaxis(truth_B[indices], 0, 2)
    methods["oracle_b_anchor"] = FittedMethod(
        name="oracle_b_anchor",
        parameterization="anchor",
        tensor=np.concatenate([smoothed_m_ref, true_b_tensor], axis=1),
        indices=indices,
        separation=anchor_separation,
        ridge_diagnostics=anchor_ridge,
        runtime_seconds=tucker_runtime,
        reconstruction_diagnostics={
            "M_ref": anchor_tucker_diagnostics["M_ref"],
            "B": {"kind": "oracle"},
        },
    )

    if tuple(methods) != METHODS:
        raise RuntimeError("fitted method order differs from the frozen protocol")
    return FittedBundle(methods=methods)
