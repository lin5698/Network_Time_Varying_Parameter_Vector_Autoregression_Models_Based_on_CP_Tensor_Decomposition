"""Outcome-free construction for the R006f exact-support design."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

import numpy as np


@dataclass(frozen=True)
class R006FConfig:
    n: int = 6
    rank: int = 2
    t_len: int = 96
    seeds: tuple[int, ...] = tuple(range(620001, 620051))
    excitation_scales: tuple[float, ...] = (1.0, 0.25)
    kappa_max: float = 50.0
    absolute_floor: float = 1e-12
    classification_threshold: float = 0.05
    m_scale: float = 0.20
    b0_scale: float = 0.15
    beta: float = 0.50
    sigma: float = 0.05


@dataclass(frozen=True)
class ExactPanel:
    """Deterministic design quantities for one excitation scale."""

    config: R006FConfig
    scale: float
    node_basis: np.ndarray
    time_basis: np.ndarray
    u: np.ndarray
    u_perp: np.ndarray
    v1: np.ndarray
    v2: np.ndarray
    w_ref: np.ndarray
    x: np.ndarray
    h: np.ndarray
    epsilon_strong: float
    epsilon: float
    topology: np.ndarray
    direct_exposure: np.ndarray
    topology_exposure: np.ndarray
    z_tilde: np.ndarray
    epsilon_star: float
    delta_supported: np.ndarray
    delta_unsupported: np.ndarray
    analytic_projector: np.ndarray
    singular_values: np.ndarray
    tau: float
    svd_projector: np.ndarray
    supported_chi: float
    unsupported_chi: float

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if isinstance(value, np.ndarray):
                defensive_copy = np.array(value, copy=True)
                defensive_copy.setflags(write=False)
                object.__setattr__(self, name, defensive_copy)


@dataclass(frozen=True)
class RegressionWorld:
    """One fixed coefficient world and its observed outcomes."""

    m: np.ndarray
    b: np.ndarray
    y: np.ndarray

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            defensive_copy = np.array(value, copy=True)
            defensive_copy.setflags(write=False)
            object.__setattr__(self, name, defensive_copy)


@dataclass(frozen=True)
class PairedWorlds:
    """Observationally identical outcomes under two coefficient truths."""

    panel: ExactPanel
    world0: RegressionWorld
    world1: RegressionWorld
    noise: np.ndarray
    a: np.ndarray
    analytic_unsupported_gap: np.ndarray

    def __post_init__(self) -> None:
        for name in ("noise", "a", "analytic_unsupported_gap"):
            defensive_copy = np.array(getattr(self, name), copy=True)
            defensive_copy.setflags(write=False)
            object.__setattr__(self, name, defensive_copy)


def _dct_ii_basis(length: int) -> np.ndarray:
    positions = np.arange(length, dtype=float) + 0.5
    frequencies = np.arange(length, dtype=float)
    basis = np.cos(
        np.pi * positions[:, None] * frequencies[None, :] / length
    )
    basis[:, 0] *= np.sqrt(1.0 / length)
    basis[:, 1:] *= np.sqrt(2.0 / length)
    return basis


def _query_chi(delta: np.ndarray, projector: np.ndarray) -> float:
    residual = delta.T @ (np.eye(delta.shape[0]) - projector)
    return float(
        np.linalg.norm(residual, ord="fro")
        / max(float(np.linalg.norm(delta.T, ord="fro")), 1e-12)
    )


def build_exact_panel(scale: Real = 1.0) -> ExactPanel:
    """Build the fixed R006f panel without noise or outcomes."""
    config = R006FConfig()
    if isinstance(scale, bool) or not isinstance(scale, Real):
        raise TypeError("scale must be a real number")
    scale = float(scale)
    if not math.isfinite(scale):
        raise ValueError("scale must be finite")
    if scale not in config.excitation_scales:
        raise ValueError(
            f"scale must be one of {config.excitation_scales}, got {scale}"
        )

    node_basis = _dct_ii_basis(config.n)
    time_basis = _dct_ii_basis(config.t_len)
    q0, q1, q2, q3, q4, q5 = node_basis.T
    u = np.column_stack((q1, q2))
    u_perp = q3
    v1 = q4
    v2 = q5
    h = time_basis[:, 6:8]
    x = (
        q4[None, :]
        + time_basis[:, 1, None] * q0[None, :]
        + time_basis[:, 2, None] * q1[None, :]
        + time_basis[:, 3, None] * q2[None, :]
        + time_basis[:, 4, None] * q3[None, :]
        + time_basis[:, 5, None] * q5[None, :]
    )
    w_ref = np.ones((config.n, config.n), dtype=float) / config.n
    training_outer = np.einsum(
        "ir,tr,j->tij", u, h, v1, optimize=True
    )
    epsilon_strong = 1.0 / (
        4.0 * config.n * float(np.max(np.abs(training_outer)))
    )
    epsilon = scale * epsilon_strong
    topology = w_ref[None, :, :] + epsilon * training_outer
    direct_exposure = x
    topology_exposure = np.einsum(
        "tij,tj->ti", topology - w_ref[None, :, :], x, optimize=True
    )
    direct_projection = np.linalg.lstsq(
        direct_exposure, topology_exposure, rcond=None
    )[0]
    z_tilde = topology_exposure - direct_exposure @ direct_projection
    endpoint_bound = max(
        float(np.max(np.abs(np.outer(q1, v2)))),
        float(np.max(np.abs(np.outer(u_perp, v2)))),
    )
    epsilon_star = 1.0 / (4.0 * config.n * endpoint_bound)
    delta_supported = epsilon_star * np.outer(q1, v2)
    delta_unsupported = epsilon_star * np.outer(u_perp, v2)
    analytic_projector = u @ u.T
    _, singular_values, right_vectors = np.linalg.svd(
        z_tilde, full_matrices=False
    )
    tau = max(
        config.absolute_floor,
        float(singular_values[0]) / config.kappa_max,
    )
    retained = singular_values >= tau
    retained_vectors = right_vectors[retained]
    svd_projector = retained_vectors.T @ retained_vectors
    supported_chi = _query_chi(delta_supported, svd_projector)
    unsupported_chi = _query_chi(delta_unsupported, svd_projector)

    return ExactPanel(
        config=config,
        scale=scale,
        node_basis=node_basis,
        time_basis=time_basis,
        u=u,
        u_perp=u_perp,
        v1=v1,
        v2=v2,
        w_ref=w_ref,
        x=x,
        h=h,
        epsilon_strong=epsilon_strong,
        epsilon=epsilon,
        topology=topology,
        direct_exposure=direct_exposure,
        topology_exposure=topology_exposure,
        z_tilde=z_tilde,
        epsilon_star=epsilon_star,
        delta_supported=delta_supported,
        delta_unsupported=delta_unsupported,
        analytic_projector=analytic_projector,
        singular_values=singular_values,
        tau=tau,
        svd_projector=svd_projector,
        supported_chi=supported_chi,
        unsupported_chi=unsupported_chi,
    )


def generate_paired_worlds(seed: int, scale: Real = 1.0) -> PairedWorlds:
    """Generate the two approved worlds using seed-keyed shared noise."""
    panel = build_exact_panel(scale=scale)
    config = panel.config
    identity = np.eye(config.n)
    m = config.m_scale * identity
    b0 = config.b0_scale * identity
    a = panel.node_basis[:, 0]
    b1 = b0 + config.beta * np.outer(a, panel.u_perp)
    noise = np.random.default_rng(seed).normal(size=(config.t_len, config.n))
    direct_mean = panel.x @ m.T
    y0 = direct_mean + panel.topology_exposure @ b0.T + config.sigma * noise
    y1 = direct_mean + panel.topology_exposure @ b1.T + config.sigma * noise
    if float(np.max(np.abs(y0 - y1))) > 1e-12:
        raise RuntimeError("paired worlds are not observationally identical")
    analytic_gap = (
        config.beta * panel.epsilon_star * np.outer(a, panel.v2)
    )
    return PairedWorlds(
        panel=panel,
        world0=RegressionWorld(m=m, b=b0, y=y0),
        world1=RegressionWorld(m=m, b=b1, y=y1),
        noise=noise,
        a=a,
        analytic_unsupported_gap=analytic_gap,
    )
