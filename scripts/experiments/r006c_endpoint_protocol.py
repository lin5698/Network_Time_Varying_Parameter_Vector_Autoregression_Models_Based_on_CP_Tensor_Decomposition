"""Frozen protocol and data construction for R006c."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np


LAYERS = ("matched", "native")
STABILITY_LEVELS = (0.80, 0.95)
APPROXIMATION_TARGETS = (0.10, 0.25)
SEPARATION_LEVELS = (0.02, 0.15, 0.45)
SEEDS = tuple(range(240100, 240110))
METHODS = (
    "block_local",
    "block_fused_tv",
    "block_cp3",
    "block_tucker333",
    "anchor_local",
    "anchor_split_cp3",
    "anchor_split_tucker333",
    "collapsed_ref_tucker333",
    "oracle_b_anchor",
)
STREAM_NAMES = (
    "operator_structure",
    "estimation_topology",
    "innovations",
    "main_holdout_topology",
    "stress_topology",
)


@dataclass(frozen=True)
class R006CConfig:
    n: int = 20
    t_len: int = 200
    window: int = 80
    true_rank: int = 8
    head_rank: int = 3
    fitted_rank: int = 3
    query_frobenius_norm: float = 1.20
    sigma: float = 0.25
    ridge_multiplier: float = 0.001
    horizon: int = 8
    stability_threshold: float = 0.98
    projection_target: float = 0.95
    cp_iterations: int = 50
    cp_starts: int = 2
    cp_tolerance: float = 1e-6
    fused_penalties: tuple[float, ...] = (0.10, 0.25, 0.50, 1.00)
    fused_max_iterations: int = 200
    fused_tolerance: float = 1e-5
    evaluation_fraction: float = 0.30
    validation_fraction: float = 0.20


@dataclass(frozen=True)
class EstimationInputs:
    predictors: np.ndarray
    outcomes: np.ndarray
    topology: np.ndarray
    W_ref: np.ndarray

    def sha256(self) -> str:
        digest = hashlib.sha256()
        for array in (
            self.predictors,
            self.outcomes,
            self.topology,
            self.W_ref,
        ):
            digest.update(np.ascontiguousarray(array).tobytes())
        return digest.hexdigest()


@dataclass(frozen=True)
class EndpointPanel:
    estimation: EstimationInputs
    A: np.ndarray
    B: np.ndarray
    M_ref: np.ndarray
    M_observed: np.ndarray
    innovations: np.ndarray
    W_ref: np.ndarray
    W_holdout: np.ndarray
    W_alt_main: np.ndarray
    W_alt_stress: np.ndarray
    a3_ratio: float
    layer: str


def spawn_named_streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAM_NAMES))
    return {
        name: np.random.default_rng(child)
        for name, child in zip(STREAM_NAMES, children)
    }


def method_seed(
    seed: int,
    layer: str,
    rho: float,
    a3: float,
    eta: float,
    method: str,
) -> int:
    key = f"{seed}|{layer}|{rho:.12g}|{a3:.12g}|{eta:.12g}|{method}"
    return int.from_bytes(
        hashlib.sha256(key.encode("ascii")).digest()[:8], "big"
    )


def expected_row_count() -> int:
    return (
        len(LAYERS)
        * len(STABILITY_LEVELS)
        * len(APPROXIMATION_TARGETS)
        * len(SEPARATION_LEVELS)
        * len(SEEDS)
        * len(METHODS)
    )


def required_cells() -> tuple[tuple[str, float, float, float], ...]:
    return tuple(
        (layer, rho, a3, eta)
        for layer in LAYERS
        for rho in STABILITY_LEVELS
        for a3 in APPROXIMATION_TARGETS
        for eta in (0.15, 0.45)
    )


def row_normalize(matrix: np.ndarray) -> np.ndarray:
    values = np.maximum(np.asarray(matrix, dtype=float), 0.0).copy()
    np.fill_diagonal(values, 0.0)
    return values / np.maximum(values.sum(axis=1, keepdims=True), 1e-12)


def generate_endpoint_panel(
    *,
    config: R006CConfig,
    layer: str,
    target_rho: float,
    approximation_target: float,
    separation_strength: float,
    seed: int,
) -> EndpointPanel:
    if layer not in LAYERS:
        raise ValueError(f"layer must be one of {LAYERS}")
    if config.head_rank != 3 or not config.head_rank < config.true_rank <= config.n:
        raise ValueError("R006c requires head_rank=3 < true_rank <= n")
    if config.t_len < 4 or config.sigma <= 0.0:
        raise ValueError("invalid panel length or innovation scale")
    if not 0.0 <= approximation_target < 1.0:
        raise ValueError("approximation_target must lie in [0, 1)")
    if not 0.0 <= separation_strength <= 1.0:
        raise ValueError("separation_strength must lie in [0, 1]")
    if not 0.0 < target_rho < config.query_frobenius_norm:
        raise ValueError("rho must be positive and below the query norm")

    try:
        from scripts.experiments.r005_separation_stability_pilot import (
            _random_topology,
            _topology_path,
        )
        from scripts.experiments.r006b_stability_signal_deconfounding import (
            _calibrate_components,
        )
    except ModuleNotFoundError:  # Direct execution from scripts/experiments.
        from r005_separation_stability_pilot import (  # type: ignore
            _random_topology,
            _topology_path,
        )
        from r006b_stability_signal_deconfounding import (  # type: ignore
            _calibrate_components,
        )

    streams = spawn_named_streams(seed)
    structure_rng = streams["operator_structure"]
    spatial, _ = np.linalg.qr(
        structure_rng.normal(size=(config.n, config.true_rank)), mode="reduced"
    )
    w_ref, topology = _topology_path(
        streams["estimation_topology"],
        config.n,
        config.t_len,
        separation_strength,
    )
    block_multipliers = np.concatenate(
        [
            np.full(config.head_rank, 0.08),
            np.full(config.true_rank - config.head_rank, 1.00),
        ]
    )
    direct_components, network_components, query_components, _, a3_ratio = (
        _calibrate_components(
            t_len=config.t_len,
            true_rank=config.true_rank,
            head_rank=config.head_rank,
            approximation_target=approximation_target,
            target_rho=target_rho,
            query_frobenius_norm=config.query_frobenius_norm,
            spatial=spatial,
            block_multipliers=block_multipliers,
            reference_topology=w_ref,
        )
    )
    direct = direct_components.sum(axis=0)
    network = network_components.sum(axis=0)
    query = query_components.sum(axis=0)
    observed = direct + np.einsum(
        "tij,tjk->tik", network, topology, optimize=True
    )

    excitation_rng = streams["innovations"]
    innovations = excitation_rng.normal(
        scale=config.sigma, size=(config.t_len, config.n)
    )
    if layer == "matched":
        raw_predictors = excitation_rng.normal(size=(config.t_len, config.n))
        covariance_root = np.diag(np.linspace(1.0, 1.4, config.n))
        predictors = raw_predictors @ covariance_root
        outcomes = np.einsum(
            "tij,tj->ti", observed, predictors, optimize=True
        ) + innovations
    else:
        states = np.empty((config.t_len + 1, config.n), dtype=float)
        states[0] = excitation_rng.normal(scale=config.sigma, size=config.n)
        for date in range(config.t_len):
            states[date + 1] = observed[date] @ states[date] + innovations[date]
        predictors = states[:-1]
        outcomes = states[1:]

    w_holdout = _random_topology(streams["main_holdout_topology"], config.n)
    w_alt_main = row_normalize(0.75 * w_ref + 0.25 * w_holdout)
    w_alt_stress = _random_topology(streams["stress_topology"], config.n)
    estimation = EstimationInputs(
        predictors=predictors,
        outcomes=outcomes,
        topology=topology,
        W_ref=w_ref,
    )
    return EndpointPanel(
        estimation=estimation,
        A=direct,
        B=network,
        M_ref=query,
        M_observed=observed,
        innovations=innovations,
        W_ref=w_ref,
        W_holdout=w_holdout,
        W_alt_main=w_alt_main,
        W_alt_stress=w_alt_stress,
        a3_ratio=float(a3_ratio),
        layer=layer,
    )
