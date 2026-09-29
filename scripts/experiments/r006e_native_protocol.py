"""Frozen protocol and native-panel construction for R006e."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields
from itertools import product

import numpy as np

from scripts.experiments import r006c_endpoint_protocol as r006c


STABILITY_LEVELS = (0.80, 0.95)
APPROXIMATION_TARGETS = (0.10, 0.25)
SEPARATION_LEVELS = (0.15, 0.45)
SCREENING_SEEDS = tuple(range(240100, 240110))
CONFIRMATION_SEEDS = tuple(range(250100, 250130))
METHODS = (
    "anchor_local",
    "anchor_fused_tv",
    "anchor_split_tucker333",
    "dw_joint_tucker333",
)
STREAM_NAMES = (
    "operator_structure",
    "estimation_topology",
    "innovations",
    "interp_endpoint",
    "family_endpoint",
    "optimizer",
)


def _readonly_copy(value: np.ndarray) -> np.ndarray:
    contiguous = np.ascontiguousarray(value)
    return np.frombuffer(contiguous.tobytes(), dtype=contiguous.dtype).reshape(
        contiguous.shape
    )


@dataclass(frozen=True)
class R006EConfig:
    n: int = 20
    t_len: int = 200
    window: int = 80
    true_rank: int = 8
    fitted_rank: int = 3
    sigma: float = 0.25
    ridge_multiplier: float = 0.001
    horizon: int = 8
    stability_threshold: float = 0.98
    projection_target: float = 0.95
    fused_penalties: tuple[float, ...] = (0.10, 0.25, 0.50, 1.00)
    temporal_penalties: tuple[float, ...] = (0.0, 0.01, 0.05, 0.20)
    optimizer_starts: int = 3
    optimizer_iterations: int = 300
    objective_tolerance: float = 1e-6
    stationarity_tolerance: float = 1e-4
    kappa_max: float = 50.0
    support_floor: float = 1e-10
    support_threshold: float = 0.10
    family_pool_size: int = 64

    def __post_init__(self) -> None:
        try:
            fused_penalties = tuple(self.fused_penalties)
            temporal_penalties = tuple(self.temporal_penalties)
        except TypeError as error:
            raise ValueError("penalty collections must be iterable") from error
        object.__setattr__(self, "fused_penalties", fused_penalties)
        object.__setattr__(self, "temporal_penalties", temporal_penalties)

        integral_fields = (
            "n",
            "t_len",
            "window",
            "true_rank",
            "fitted_rank",
            "horizon",
            "optimizer_starts",
            "optimizer_iterations",
            "family_pool_size",
        )
        if any(
            isinstance(getattr(self, name), (bool, np.bool_))
            or not isinstance(getattr(self, name), (int, np.integer))
            for name in integral_fields
        ):
            raise ValueError("integral config controls must be integers")
        for name in integral_fields:
            object.__setattr__(self, name, int(getattr(self, name)))

        scalar_values = (
            getattr(self, field.name)
            for field in fields(self)
            if field.name not in {"fused_penalties", "temporal_penalties"}
        )
        try:
            all_finite = all(np.isfinite(value) for value in scalar_values)
            penalties_finite = all(
                np.isfinite(value)
                for value in fused_penalties + temporal_penalties
            )
        except TypeError as error:
            raise ValueError("numeric config values must be finite") from error
        if not all_finite or not penalties_finite:
            raise ValueError("numeric config values must be finite")

        if not 0 < self.window < self.t_len or self.t_len - self.window != 120:
            raise ValueError("R006e requires exactly 120 post-warm-up dates")
        if self.n <= 0 or not 0 < self.fitted_rank < self.true_rank <= self.n:
            raise ValueError("R006e requires fitted_rank < true_rank <= n")
        if self.sigma <= 0.0 or self.ridge_multiplier <= 0.0:
            raise ValueError("innovation scale and ridge multiplier must be positive")
        if self.horizon <= 0 or self.optimizer_starts <= 0:
            raise ValueError("horizon and optimizer starts must be positive")
        if self.optimizer_iterations <= 0 or self.family_pool_size <= 0:
            raise ValueError("iteration and candidate counts must be positive")
        if not 0.0 < self.stability_threshold < 1.0:
            raise ValueError("stability_threshold must lie in (0, 1)")
        if not 0.0 < self.projection_target < 1.0:
            raise ValueError("projection_target must lie in (0, 1)")
        if self.objective_tolerance <= 0.0 or self.stationarity_tolerance <= 0.0:
            raise ValueError("optimizer tolerances must be positive")
        if self.kappa_max <= 1.0 or self.support_floor <= 0.0:
            raise ValueError("support conditioning parameters are invalid")
        if not 0.0 <= self.support_threshold <= 1.0:
            raise ValueError("support_threshold must lie in [0, 1]")
        if not fused_penalties or any(x < 0.0 for x in fused_penalties):
            raise ValueError("fused_penalties must be non-negative")
        if not temporal_penalties or any(x < 0.0 for x in temporal_penalties):
            raise ValueError("temporal_penalties must be non-negative")


@dataclass(frozen=True)
class ChronologicalRegions:
    calibration: np.ndarray
    validation: np.ndarray
    evaluation: np.ndarray

    def __post_init__(self) -> None:
        for field in fields(self):
            value = np.asarray(getattr(self, field.name))
            if value.ndim != 1:
                raise ValueError(f"{field.name} must be a vector")
            object.__setattr__(self, field.name, _readonly_copy(value))


@dataclass(frozen=True)
class FitInputs:
    predictors: np.ndarray
    outcomes: np.ndarray
    topology: np.ndarray
    w_ref: np.ndarray
    coefficient_dates: np.ndarray

    def __post_init__(self) -> None:
        predictors = np.asarray(self.predictors)
        outcomes = np.asarray(self.outcomes)
        topology = np.asarray(self.topology)
        reference = np.asarray(self.w_ref)
        dates = np.asarray(self.coefficient_dates)
        if predictors.ndim != 2 or outcomes.shape != predictors.shape:
            raise ValueError("predictors and outcomes must be aligned matrices")
        t_len, n = predictors.shape
        if topology.shape != (t_len, n, n) or reference.shape != (n, n):
            raise ValueError("topology arrays have incompatible dimensions")
        if dates.ndim != 1 or dates.size == 0:
            raise ValueError("coefficient_dates must be a non-empty vector")
        if not np.issubdtype(dates.dtype, np.integer):
            raise ValueError("coefficient_dates must contain integers")
        if np.any(dates[1:] <= dates[:-1]):
            raise ValueError("coefficient_dates must be strictly increasing")
        if np.any(dates < 0) or np.any(dates >= t_len):
            raise ValueError("coefficient_dates must index the panel")
        for field in fields(self):
            object.__setattr__(
                self, field.name, _readonly_copy(getattr(self, field.name))
            )

    def sha256(self) -> str:
        digest = hashlib.sha256()
        for value in (
            self.predictors,
            self.outcomes,
            self.topology,
            self.w_ref,
            self.coefficient_dates,
        ):
            digest.update(np.ascontiguousarray(value).tobytes())
        return digest.hexdigest()


@dataclass(frozen=True)
class TruthBundle:
    m_ref: np.ndarray
    b: np.ndarray
    observed_operator: np.ndarray

    def __post_init__(self) -> None:
        shape = np.asarray(self.m_ref).shape
        if len(shape) != 3 or any(
            np.asarray(value).shape != shape
            for value in (self.b, self.observed_operator)
        ):
            raise ValueError("truth operators must be aligned tensors")
        for field in fields(self):
            object.__setattr__(
                self, field.name, _readonly_copy(getattr(self, field.name))
            )


@dataclass(frozen=True)
class NativePanel:
    fit: FitInputs
    truth: TruthBundle
    w_alt_interp: np.ndarray
    endpoint_stream_seed: int

    def __post_init__(self) -> None:
        endpoint = np.asarray(self.w_alt_interp)
        if endpoint.shape != self.fit.w_ref.shape:
            raise ValueError("interpolation endpoint has incompatible dimensions")
        if self.truth.m_ref.shape != self.fit.topology.shape:
            raise ValueError("fit and truth tensors must be aligned")
        object.__setattr__(self, "w_alt_interp", _readonly_copy(endpoint))


@dataclass(frozen=True)
class NativeConstructionInputs:
    fit: FitInputs
    w_alt_interp: np.ndarray
    family_seed: int
    stream_metadata: tuple[r006c.StreamDeclaration, ...]

    def __post_init__(self) -> None:
        endpoint = np.asarray(self.w_alt_interp)
        if endpoint.shape != self.fit.w_ref.shape:
            raise ValueError("interpolation endpoint has incompatible dimensions")
        object.__setattr__(self, "w_alt_interp", _readonly_copy(endpoint))
        object.__setattr__(self, "stream_metadata", tuple(self.stream_metadata))

    def design_sha256(self) -> str:
        digest = hashlib.sha256()
        for value in (
            self.fit.predictors, self.fit.topology, self.fit.w_ref,
            self.fit.coefficient_dates,
        ):
            digest.update(np.ascontiguousarray(value).tobytes())
        return digest.hexdigest()


def chronological_regions(config: R006EConfig) -> ChronologicalRegions:
    dates = np.arange(config.window, config.t_len, dtype=int)
    if len(dates) != 120:
        raise ValueError("R006e requires exactly 60/24/36 post-warm-up dates")
    return ChronologicalRegions(
        calibration=dates[:60],
        validation=dates[60:84],
        evaluation=dates[84:],
    )


def primary_cells() -> tuple[tuple[float, float, float], ...]:
    return tuple(
        product(STABILITY_LEVELS, APPROXIMATION_TARGETS, SEPARATION_LEVELS)
    )


def _seed_key(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def keyed_seed(seed: int, *keys: object) -> int:
    key = "|".join(_seed_key(value) for value in (seed, *keys))
    return int.from_bytes(hashlib.sha256(key.encode("ascii")).digest()[:8], "big")


def spawn_named_streams(seed: int) -> dict[str, np.random.Generator]:
    return {
        name: np.random.default_rng(keyed_seed(seed, name))
        for name in STREAM_NAMES
    }


def _r006c_config(config: R006EConfig) -> r006c.R006CConfig:
    return r006c.R006CConfig(
            n=config.n,
            t_len=config.t_len,
            window=config.window,
            true_rank=config.true_rank,
            head_rank=config.fitted_rank,
            fitted_rank=config.fitted_rank,
            sigma=config.sigma,
            ridge_multiplier=config.ridge_multiplier,
            horizon=config.horizon,
            stability_threshold=config.stability_threshold,
            projection_target=config.projection_target,
            fused_penalties=config.fused_penalties,
        )


def _fit_from_estimation(
    estimation: r006c.EstimationInputs, config: R006EConfig
) -> FitInputs:
    return FitInputs(
        predictors=estimation.predictors,
        outcomes=estimation.outcomes,
        topology=estimation.topology,
        w_ref=estimation.W_ref,
        coefficient_dates=np.arange(config.window, config.t_len, dtype=int),
    )


def build_native_construction_inputs(
    config: R006EConfig, *, rho: float, a3: float, eta: float, seed: int,
) -> NativeConstructionInputs:
    source = r006c.generate_estimation_construction_inputs(
        config=_r006c_config(config),
        layer="native",
        target_rho=rho,
        approximation_target=a3,
        separation_strength=eta,
        seed=seed,
    )
    zero_outcomes = np.zeros_like(source.predictors)
    fit = FitInputs(
        predictors=source.predictors,
        outcomes=zero_outcomes,
        topology=source.topology,
        w_ref=source.W_ref,
        coefficient_dates=np.arange(config.window, config.t_len, dtype=int),
    )
    return NativeConstructionInputs(
        fit=fit,
        w_alt_interp=source.W_alt_main,
        family_seed=keyed_seed(seed, rho, a3, eta, "family_endpoint"),
        stream_metadata=source.stream_declarations,
    )


def build_native_panel(
    config: R006EConfig, *, rho: float, a3: float, eta: float, seed: int,
) -> NativePanel:
    source = r006c.generate_endpoint_panel(
        config=_r006c_config(config), layer="native", target_rho=rho,
        approximation_target=a3, separation_strength=eta, seed=seed,
    )
    fit = _fit_from_estimation(source.estimation, config)
    truth = TruthBundle(
        m_ref=source.M_ref,
        b=source.B,
        observed_operator=source.M_observed,
    )
    return NativePanel(
        fit=fit,
        truth=truth,
        w_alt_interp=source.W_alt_main,
        endpoint_stream_seed=keyed_seed(seed, rho, a3, eta, "family_endpoint"),
    )
