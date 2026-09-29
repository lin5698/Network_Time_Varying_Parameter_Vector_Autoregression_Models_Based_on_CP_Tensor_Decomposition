"""Synthetic-only computational core for the frozen NCS E3 design.

This module contains no command-line entrypoint and does not write results.
It is a deterministic implementation of the pre-outcome design in
``refine-logs/NCS_E3_SYNTHETIC_EXECUTION_DESIGN_v1.md``. A separate,
candidate-bound execution layer must validate authority and isolate outputs
before calling any grid function here.

The implementation deliberately keeps topology-query evaluation separate from
fitting and validation. In particular, held-out query matrices are absent from
all fitting and hyperparameter-selection interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Iterable, Literal, Mapping, Sequence

import numpy as np


Family = Literal["family1", "family2"]
Method = Literal["local_structured", "causal_temporal_smoother", "fixed_rank_basis"]
QueryClass = Literal["in_family_interpolation", "cross_generator"]

STATUS_AVAILABLE = "AVAILABLE"
STATUS_OUTSIDE_TARGET = "OUTSIDE_TARGET"
STATUS_NONCONVERGED = "NONCONVERGED"
STATUS_NONFINITE = "NONFINITE"
STATUS_UNSTABLE = "UNSTABLE"
STATUS_SCHEMA = frozenset(
    {
        STATUS_AVAILABLE,
        STATUS_OUTSIDE_TARGET,
        STATUS_NONCONVERGED,
        STATUS_NONFINITE,
        STATUS_UNSTABLE,
    }
)

FAMILY1 = "family1"
FAMILY2 = "family2"
METHODS: tuple[Method, ...] = (
    "local_structured",
    "causal_temporal_smoother",
    "fixed_rank_basis",
)
QUERY_CLASSES: tuple[QueryClass, ...] = (
    "in_family_interpolation",
    "cross_generator",
)
FIXED_RANK_BOOTSTRAP_LOCAL_WINDOW = 12
MINIMUM_LOCAL_ESTIMATES_FOR_TEMPORAL_METHOD = 2


class E3SyntheticError(RuntimeError):
    """Raised when a frozen E3 synthetic contract is violated."""


class OutsideTargetError(E3SyntheticError):
    """Raised when a collapsed representation is asked for a query endpoint."""


@dataclass(frozen=True)
class E3SyntheticConfig:
    """All run parameters that affect the synthetic evidence route.

    The standard configuration is intentionally small enough for a local CPU
    execution, but it retains the two scales, two query classes, two horizons,
    and twenty paired panels specified in the E3 design.
    """

    n: int
    total_time: int = 144
    train_stop: int = 72
    validation_stop: int = 96
    evaluation_stop: int = 144
    horizons: tuple[int, ...] = (4, 12)
    local_windows: tuple[int, ...] = (8, 12, 16)
    smoother_alphas: tuple[float, ...] = (0.25, 0.55, 0.85)
    basis_ranks: tuple[int, ...] = (1, 2, 3)
    ridge: float = 1e-5
    noise_std: float = 0.08
    stability_envelope: float = 0.90
    stability_threshold: float = 0.98
    bootstrap_replicates: int = 80
    bootstrap_block_length: int = 5

    def __post_init__(self) -> None:
        if self.n < 3:
            raise ValueError("N must be at least 3")
        if self.total_time != self.evaluation_stop:
            raise ValueError("evaluation_stop must equal total_time")
        if not (8 < self.train_stop < self.validation_stop < self.evaluation_stop):
            raise ValueError("chronological split boundaries are invalid")
        if tuple(self.horizons) != (4, 12):
            raise ValueError("E3 headline horizons must be exactly (4, 12)")
        if len(self.local_windows) != 3 or min(self.local_windows) < 2:
            raise ValueError("the local window candidate list is invalid")
        if len(self.smoother_alphas) != 3 or any(not 0 < value <= 1 for value in self.smoother_alphas):
            raise ValueError("the smoother candidate list is invalid")
        if len(self.basis_ranks) != 3 or min(self.basis_ranks) < 1:
            raise ValueError("the basis-rank candidate list is invalid")
        if self.ridge <= 0 or self.noise_std <= 0:
            raise ValueError("ridge and innovation standard deviation must be positive")
        if not 0 < self.stability_envelope < self.stability_threshold < 1:
            raise ValueError(
                "the stability envelope and threshold must satisfy "
                "0 < envelope < threshold < 1"
            )
        if self.bootstrap_replicates < 2 or self.bootstrap_block_length < 1:
            raise ValueError("bootstrap settings are invalid")

    @property
    def train_indices(self) -> np.ndarray:
        return np.arange(1, self.train_stop, dtype=int)

    @property
    def validation_indices(self) -> np.ndarray:
        return np.arange(self.train_stop, self.validation_stop, dtype=int)

    @property
    def evaluation_indices(self) -> np.ndarray:
        return np.arange(self.validation_stop, self.evaluation_stop, dtype=int)


@dataclass(frozen=True)
class FixedRankBootstrapRefitSchedule:
    """Rank-aware causal refit times for the fixed-rank bootstrap route."""

    rank: int
    local_window: int
    target_time: int
    first_refit_time: int
    refit_times: tuple[int, ...]

    @property
    def valid_refit_count(self) -> int:
        return len(self.refit_times)


def fixed_rank_bootstrap_refit_schedule(
    config: E3SyntheticConfig,
    rank: int,
    *,
    target_time: int,
) -> FixedRankBootstrapRefitSchedule:
    """Return only causal fixed-rank refit times with a valid local history.

    A temporal fit needs two local estimates. The fixed-rank reconstruction
    additionally needs at least ``rank`` rows. For the frozen local window,
    the first usable refit time is ``window + max(2, rank)``. The E3-4 route
    requires at least two such refits before the evaluated target.
    """

    if isinstance(rank, bool) or not isinstance(rank, int) or rank not in config.basis_ranks:
        raise E3SyntheticError("bootstrap rank is not in the frozen fixed-rank candidate list")
    if isinstance(target_time, bool) or not isinstance(target_time, int):
        raise E3SyntheticError("bootstrap target time must be an integer")
    first_refit_time = FIXED_RANK_BOOTSTRAP_LOCAL_WINDOW + max(
        MINIMUM_LOCAL_ESTIMATES_FOR_TEMPORAL_METHOD, rank
    )
    refit_times = tuple(range(first_refit_time, target_time))
    if len(refit_times) < 2:
        raise E3SyntheticError(
            "fixed-rank bootstrap requires at least two valid causal refit opportunities"
        )
    return FixedRankBootstrapRefitSchedule(
        rank=rank,
        local_window=FIXED_RANK_BOOTSTRAP_LOCAL_WINDOW,
        target_time=target_time,
        first_refit_time=first_refit_time,
        refit_times=refit_times,
    )


@dataclass(frozen=True)
class SyntheticPanel:
    """A full synthetic panel, including query routes inaccessible to fitting."""

    family: Family
    config: E3SyntheticConfig
    seed: int
    observed_topologies: np.ndarray
    responses: np.ndarray
    true_blocks: np.ndarray
    query_topologies: Mapping[QueryClass, np.ndarray]

    def __post_init__(self) -> None:
        n = self.config.n
        blocks = coefficient_block_count(self.family)
        if self.observed_topologies.shape != (self.config.total_time, n, n):
            raise ValueError("observed topology shape is invalid")
        if self.responses.shape != (self.config.total_time, n):
            raise ValueError("response shape is invalid")
        if self.true_blocks.shape != (self.config.total_time, blocks, n):
            raise ValueError("true coefficient-block shape is invalid")
        if set(self.query_topologies) != set(QUERY_CLASSES):
            raise ValueError("query topology inventory is invalid")
        for topology in self.query_topologies.values():
            if topology.shape != (self.config.total_time, n, n):
                raise ValueError("query topology shape is invalid")


@dataclass(frozen=True)
class FitData:
    """The only data object accepted by fitting and validation selection.

    It deliberately excludes held-out query matrices and response truth at
    those matrices. This makes the no-query selection contract structural,
    rather than merely a convention inside a fitting function.
    """

    family: Family
    config: E3SyntheticConfig
    seed: int
    observed_topologies: np.ndarray
    responses: np.ndarray

    def __post_init__(self) -> None:
        n = self.config.n
        if self.observed_topologies.shape != (self.config.total_time, n, n):
            raise ValueError("fit topology shape is invalid")
        if self.responses.shape != (self.config.total_time, n):
            raise ValueError("fit response shape is invalid")


def fit_data_from_panel(panel: SyntheticPanel) -> FitData:
    """Expose the restricted observed-history view for fit and validation."""

    return FitData(
        family=panel.family,
        config=panel.config,
        seed=panel.seed,
        observed_topologies=panel.observed_topologies,
        responses=panel.responses,
    )


def _fit_data_matches_panel(fit_data: FitData, panel: SyntheticPanel) -> bool:
    """Require a cached path to retain the exact observed history of its panel.

    ``fit_data_from_panel`` intentionally returns a fresh immutable wrapper on
    each call.  Comparing wrapper identities would therefore reject a valid
    cached path during recovery.  The arrays themselves must still be the
    exact panel arrays, which prevents a fitted state from another panel or a
    copied/mutated history from being evaluated here.
    """

    return (
        fit_data.family == panel.family
        and fit_data.config == panel.config
        and fit_data.seed == panel.seed
        and fit_data.observed_topologies is panel.observed_topologies
        and fit_data.responses is panel.responses
    )


@dataclass(frozen=True)
class Endpoint:
    """One native topology-query endpoint."""

    status: str
    reason: str
    blocks: np.ndarray | None
    operator: np.ndarray | None
    responses: np.ndarray | None
    spectral_radius: float | None

    def __post_init__(self) -> None:
        if self.status not in STATUS_SCHEMA:
            raise ValueError("endpoint status is invalid")
        if self.status == STATUS_AVAILABLE:
            if self.blocks is None or self.operator is None or self.responses is None:
                raise ValueError("available endpoints must retain the complete endpoint")
        elif any(value is not None for value in (self.blocks, self.operator, self.responses)):
            raise ValueError("failed or outside-target endpoints cannot expose numerical objects")


@dataclass(frozen=True)
class SelectionResult:
    """Validation-only hyperparameter selection for one native method."""

    method: Method
    selected: float | int | None
    validation_loss: float | None
    status: str
    candidate_losses: tuple[float | None, ...]


@dataclass(frozen=True)
class _FittedNativePath:
    """Internal native method state; it is never a public E3 entrypoint."""

    fit_data: FitData
    method: Method
    hyperparameter: float | int
    features: np.ndarray

    def _evaluate_unchecked(
        self, query_topology: np.ndarray, horizon: int, target_time: int
    ) -> Endpoint:
        """Evaluate a supplied query after a public caller has passed E3-1."""

        if not 1 <= target_time < self.fit_data.config.total_time:
            raise ValueError("target time is outside the fitted path")
        try:
            blocks = _estimate_native_blocks(
                self.fit_data.family,
                self.method,
                self.features,
                self.fit_data.responses,
                target_time,
                self.hyperparameter,
                ridge=self.fit_data.config.ridge,
                stability_envelope=self.fit_data.config.stability_envelope,
            )
        except (E3SyntheticError, FloatingPointError, np.linalg.LinAlgError, ValueError) as error:
            return Endpoint(STATUS_NONCONVERGED, f"native fit failed: {error}", None, None, None, None)
        return _native_endpoint(
            self.fit_data.family,
            blocks,
            query_topology,
            horizon,
            stability_threshold=self.fit_data.config.stability_threshold,
        )

@dataclass(frozen=True)
class NativePath:
    """Public, E3-1-gated handle for a native fitted state."""

    _state: _FittedNativePath

    def evaluate(self, query_topology: np.ndarray, horizon: int, target_time: int) -> Endpoint:
        """Evaluate a held-out query only after exact classification passes."""

        require_e3_1_gate()
        return self._state._evaluate_unchecked(query_topology, horizon, target_time)


def _fit_native_path(
    fit_data: FitData, method: Method, frozen_hyperparameter: float | int
) -> NativePath:
    """Internal fit implementation; public callers use ``fit_native_path``."""

    if frozen_hyperparameter not in _candidate_values(fit_data.config, method):
        raise ValueError("native method hyperparameter is outside the frozen candidate list")
    return NativePath(
        _FittedNativePath(
            fit_data,
            method,
            frozen_hyperparameter,
            _panel_features(fit_data),
        )
    )


def fit_native_path(
    fit_data: FitData, method: Method, frozen_hyperparameter: float | int
) -> NativePath:
    """Freeze one native implementation without exposing a query during fit."""

    require_e3_1_gate()
    return _fit_native_path(fit_data, method, frozen_hyperparameter)


@dataclass(frozen=True)
class EvaluationRecord:
    """One retained panel-method-query-horizon outcome record."""

    family: Family
    n: int
    seed: int
    method: str
    query_class: QueryClass
    target_time: int
    horizon: int
    status: str
    operator_mse: float | None
    response_mse: float | None
    estimated_spectral_radius: float | None
    truth_spectral_radius: float | None
    selected_hyperparameter: float | int | None
    validation_loss: float | None


def coefficient_block_count(family: Family) -> int:
    if family == FAMILY1:
        return 2
    if family == FAMILY2:
        return 3
    raise ValueError("unknown operator family")


def project_blocks_to_stability_envelope(
    blocks: np.ndarray, envelope: float
) -> np.ndarray:
    """Project each node's retained block vector onto an L1 envelope."""

    values = np.asarray(blocks, dtype=float)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("coefficient blocks must be a finite two-dimensional array")
    if not np.isfinite(envelope) or not 0 < envelope < 1:
        raise ValueError("the stability envelope must be finite and in (0, 1)")
    node_norms = np.sum(np.abs(values), axis=0)
    scales = np.minimum(
        1.0,
        envelope / np.maximum(node_norms, np.finfo(float).eps),
    )
    return values * scales[None, :]


def zero_diagonal_row_normalize(topology: np.ndarray) -> np.ndarray:
    """Normalize a raw adjacency once, before the declared ``W @ W`` step."""

    array = np.asarray(topology, dtype=float).copy()
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("topology must be square")
    np.fill_diagonal(array, 0.0)
    maximum = float(np.max(np.sum(np.abs(array), axis=1)))
    if not np.isfinite(maximum) or maximum <= 0:
        raise ValueError("topology must contain a non-zero finite row")
    return array / maximum


def topology_square(topology: np.ndarray) -> np.ndarray:
    """Return exactly ``W @ W`` with no post-square transformation."""

    array = np.asarray(topology, dtype=float)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError("topology must be square")
    return array @ array


def _diagonal_blocks_to_operator(family: Family, blocks: np.ndarray, topology: np.ndarray) -> np.ndarray:
    """Evaluate a native retained-block operator at a supplied topology."""

    values = np.asarray(blocks, dtype=float)
    topology_array = np.asarray(topology, dtype=float)
    n = topology_array.shape[0]
    if topology_array.shape != (n, n) or values.shape != (coefficient_block_count(family), n):
        raise ValueError("coefficient blocks or topology have an invalid shape")
    if family == FAMILY1:
        return np.diag(values[0]) + np.diag(values[1]) @ topology_array
    return (
        np.diag(values[0])
        + np.diag(values[1]) @ topology_array
        + np.diag(values[2]) @ topology_square(topology_array)
    )


def _finite_horizon_responses(operator: np.ndarray, horizon: int) -> np.ndarray:
    """Return the lag-one finite-horizon response sequence with shock map ``I``."""

    value = np.asarray(operator, dtype=float)
    if value.ndim != 2 or value.shape[0] != value.shape[1] or horizon < 1:
        raise ValueError("operator or horizon is invalid")
    current = np.eye(value.shape[0], dtype=float)
    result: list[np.ndarray] = []
    for _ in range(horizon):
        current = current @ value
        result.append(current.copy())
    return np.stack(result, axis=0)


def spectral_radius(operator: np.ndarray) -> float:
    values = np.linalg.eigvals(np.asarray(operator, dtype=float))
    return float(np.max(np.abs(values)))


def _native_endpoint(
    family: Family,
    blocks: np.ndarray,
    query_topology: np.ndarray,
    horizon: int,
    *,
    stability_threshold: float,
) -> Endpoint:
    """Construct the complete endpoint from native coefficient blocks only."""

    try:
        operator = _diagonal_blocks_to_operator(family, blocks, query_topology)
        if not np.all(np.isfinite(operator)):
            return Endpoint(STATUS_NONFINITE, "non-finite operator", None, None, None, None)
        radius = spectral_radius(operator)
        if not np.isfinite(radius):
            return Endpoint(STATUS_NONFINITE, "non-finite spectral radius", None, None, None, None)
        if radius >= stability_threshold:
            return Endpoint(
                STATUS_UNSTABLE,
                f"spectral radius {radius:.12g} exceeds the frozen threshold",
                None,
                None,
                None,
                radius,
            )
        responses = _finite_horizon_responses(operator, horizon)
        if not np.all(np.isfinite(responses)):
            return Endpoint(STATUS_NONFINITE, "non-finite response", None, None, None, radius)
        return Endpoint(STATUS_AVAILABLE, "native retained-block endpoint", np.asarray(blocks, dtype=float).copy(), operator, responses, radius)
    except (FloatingPointError, np.linalg.LinAlgError, ValueError) as error:
        return Endpoint(STATUS_NONCONVERGED, f"endpoint construction failed: {error}", None, None, None, None)


def collapsed_endpoint_control(*_args: object, **_kwargs: object) -> Endpoint:
    """Return the non-rankable negative control required by the E3 contract."""

    return Endpoint(
        STATUS_OUTSIDE_TARGET,
        "collapsed-only maps do not retain the coefficient blocks needed for a topology query",
        None,
        None,
        None,
        None,
    )


def _rng(seed: int, *parts: int) -> np.random.Generator:
    sequence = np.random.SeedSequence([seed, *parts])
    return np.random.default_rng(sequence)


def _directed_sparse_topology_path(n: int, total_time: int, rng: np.random.Generator) -> np.ndarray:
    support = rng.random((n, n)) < min(0.18, 4.5 / n)
    np.fill_diagonal(support, False)
    for row in range(n):
        if not np.any(support[row]):
            target = int((row + 1 + rng.integers(0, n - 1)) % n)
            if target == row:
                target = (target + 1) % n
            support[row, target] = True
    base = rng.uniform(0.25, 1.0, size=(n, n)) * support
    phase = rng.uniform(0.0, 2.0 * np.pi, size=(n, n)) * support
    path = np.empty((total_time, n, n), dtype=float)
    for time in range(total_time):
        modulation = 1.0 + 0.22 * np.sin(2.0 * np.pi * time / 36.0 + phase)
        path[time] = zero_diagonal_row_normalize(base * modulation)
    return path


def _latent_position_topology_path(n: int, total_time: int, rng: np.random.Generator) -> np.ndarray:
    initial = rng.uniform(-1.0, 1.0, size=(n, 2))
    drift = rng.normal(scale=0.015, size=(n, 2))
    directional = rng.uniform(0.7, 1.3, size=(n, n))
    np.fill_diagonal(directional, 0.0)
    path = np.empty((total_time, n, n), dtype=float)
    for time in range(total_time):
        positions = initial + time * drift
        distances = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
        weights = np.exp(-2.0 * distances) * directional
        np.fill_diagonal(weights, 0.0)
        for row in range(n):
            retained = np.argpartition(weights[row], -min(4, n - 1))[-min(4, n - 1) :]
            mask = np.zeros(n, dtype=bool)
            mask[retained] = True
            weights[row, ~mask] = 0.0
        path[time] = zero_diagonal_row_normalize(weights)
    return path


def _interpolation_query_path(n: int, total_time: int, rng: np.random.Generator) -> np.ndarray:
    left = _directed_sparse_topology_path(n, total_time, rng)
    right = _directed_sparse_topology_path(n, total_time, rng)
    path = np.empty_like(left)
    for time in range(total_time):
        path[time] = zero_diagonal_row_normalize(0.5 * left[time] + 0.5 * right[time])
    return path


def domain_stability_fixture_report() -> Mapping[str, Any]:
    """Verify the frozen envelope on deterministic Family-1/2 fixtures."""

    envelope = 0.90
    topology_cases = {
        "signed_row_normalized": zero_diagonal_row_normalize(
            np.array(
                [
                    [0.0, 1.0, -0.5],
                    [-0.25, 0.0, 0.5],
                    [0.2, -0.8, 0.0],
                ],
                dtype=float,
            )
        ),
        "directed_sparse": _directed_sparse_topology_path(3, 1, _rng(7001))[0],
        "latent_position": _latent_position_topology_path(3, 1, _rng(7002))[0],
    }
    block_cases = {
        FAMILY1: {
            "zero": np.zeros((2, 3), dtype=float),
            "boundary": np.repeat(np.array([[0.4], [-0.5]], dtype=float), 3, axis=1),
            "projected": np.repeat(np.array([[0.9], [-0.9]], dtype=float), 3, axis=1),
        },
        FAMILY2: {
            "zero": np.zeros((3, 3), dtype=float),
            "boundary": np.repeat(
                np.array([[0.2], [0.3], [-0.4]], dtype=float), 3, axis=1
            ),
            "projected": np.repeat(
                np.array([[0.6], [-0.6], [0.6]], dtype=float), 3, axis=1
            ),
        },
    }
    records: list[Mapping[str, Any]] = []
    for family in (FAMILY1, FAMILY2):
        for coefficient_case in ("zero", "boundary", "projected"):
            raw_blocks = block_cases[family][coefficient_case]
            projected = project_blocks_to_stability_envelope(raw_blocks, envelope)
            block_norm = float(np.max(np.sum(np.abs(projected), axis=0)))
            for topology_case in (
                "signed_row_normalized",
                "directed_sparse",
                "latent_position",
            ):
                topology = topology_cases[topology_case]
                operator = _diagonal_blocks_to_operator(family, projected, topology)
                records.append(
                    {
                        "family": family,
                        "coefficient_case": coefficient_case,
                        "topology_case": topology_case,
                        "projected_block_norm": block_norm,
                        "topology_infinity_norm": float(
                            np.max(np.sum(np.abs(topology), axis=1))
                        ),
                        "topology_square_infinity_norm": float(
                            np.max(np.sum(np.abs(topology_square(topology)), axis=1))
                        ),
                        "operator_infinity_norm": float(
                            np.max(np.sum(np.abs(operator), axis=1))
                        ),
                        "spectral_radius": spectral_radius(operator),
                    }
                )
    max_projected_block_norm = max(record["projected_block_norm"] for record in records)
    max_spectral_radius = max(record["spectral_radius"] for record in records)
    status = (
        STATUS_AVAILABLE
        if max_projected_block_norm <= envelope + 1e-12
        and max_spectral_radius <= envelope + 1e-12
        and all(record["topology_infinity_norm"] <= 1.0 + 1e-12 for record in records)
        and all(
            record["topology_square_infinity_norm"] <= 1.0 + 1e-12
            for record in records
        )
        else STATUS_NONCONVERGED
    )
    return {
        "status": status,
        "envelope": envelope,
        "families": [FAMILY1, FAMILY2],
        "coefficient_cases": ["zero", "boundary", "projected"],
        "topology_cases": [
            "signed_row_normalized",
            "directed_sparse",
            "latent_position",
        ],
        "checked_endpoints": len(records),
        "max_projected_block_norm": max_projected_block_norm,
        "max_spectral_radius": max_spectral_radius,
        "records": records,
    }


def _coefficient_paths(family: Family, config: E3SyntheticConfig, rng: np.random.Generator) -> np.ndarray:
    blocks = coefficient_block_count(family)
    n = config.n
    time = np.arange(config.total_time, dtype=float)[:, None]
    phases = rng.uniform(0.0, 2.0 * np.pi, size=(blocks, n))
    # Bounded offsets, together with row-normalized W and W@W, give a
    # deterministic infinity-norm stability bound for every query topology.
    offsets = rng.uniform(-0.012, 0.012, size=(blocks, n))
    if family == FAMILY1:
        bases = np.array([0.18, 0.22], dtype=float)[:, None]
        amplitudes = np.array([0.035, 0.045], dtype=float)[:, None]
    else:
        bases = np.array([0.14, 0.18, 0.10], dtype=float)[:, None]
        amplitudes = np.array([0.030, 0.040, 0.025], dtype=float)[:, None]
    path = np.empty((config.total_time, blocks, n), dtype=float)
    for block in range(blocks):
        path[:, block, :] = (
            bases[block]
            + offsets[block]
            + amplitudes[block] * np.sin(2.0 * np.pi * time / 48.0 + phases[block])
        )
    if family == FAMILY2 and np.any(np.abs(path[:, 2, :]) < 0.02):
        raise E3SyntheticError("Family-2 structural second-order witness vanished")
    if float(np.max(np.sum(np.abs(path), axis=1))) >= 0.8:
        raise E3SyntheticError("bounded coefficient construction escaped the stable regime")
    return path


def make_synthetic_panel(family: Family, config: E3SyntheticConfig, seed: int) -> SyntheticPanel:
    """Generate a synthetic panel before all fitting and selection takes place."""

    require_e3_1_gate()
    topology_rng = _rng(seed, 1)
    coefficient_rng = _rng(seed, 2)
    innovation_rng = _rng(seed, 3)
    interpolation_rng = _rng(seed, 4)
    cross_generator_rng = _rng(seed, 5)
    observed = _directed_sparse_topology_path(config.n, config.total_time, topology_rng)
    queries: dict[QueryClass, np.ndarray] = {
        "in_family_interpolation": _interpolation_query_path(
            config.n, config.total_time, interpolation_rng
        ),
        "cross_generator": _latent_position_topology_path(
            config.n, config.total_time, cross_generator_rng
        ),
    }
    blocks = _coefficient_paths(family, config, coefficient_rng)
    responses = np.empty((config.total_time, config.n), dtype=float)
    responses[0] = innovation_rng.normal(scale=config.noise_std, size=config.n)
    for time in range(1, config.total_time):
        operator = _diagonal_blocks_to_operator(family, blocks[time], observed[time])
        if spectral_radius(operator) >= 0.8:
            raise E3SyntheticError("truth operator escaped the declared stable regime")
        responses[time] = operator @ responses[time - 1] + innovation_rng.normal(
            scale=config.noise_std, size=config.n
        )
    return SyntheticPanel(
        family=family,
        config=config,
        seed=seed,
        observed_topologies=observed,
        responses=responses,
        true_blocks=blocks,
        query_topologies=queries,
    )


def _feature_vector(family: Family, previous: np.ndarray, topology: np.ndarray) -> np.ndarray:
    first_order = topology @ previous
    if family == FAMILY1:
        return np.stack((previous, first_order), axis=1)
    second_order = topology_square(topology) @ previous
    return np.stack((previous, first_order, second_order), axis=1)


def _panel_features(fit_data: FitData) -> np.ndarray:
    features = np.empty(
        (fit_data.config.total_time, fit_data.config.n, coefficient_block_count(fit_data.family)), dtype=float
    )
    features[0] = 0.0
    for time in range(1, fit_data.config.total_time):
        features[time] = _feature_vector(
            fit_data.family, fit_data.responses[time - 1], fit_data.observed_topologies[time]
        )
    return features


def _ridge_rowwise(features: np.ndarray, outputs: np.ndarray, ridge: float) -> np.ndarray:
    """Fit diagonal coefficient blocks to time-indexed rowwise regressions."""

    if features.ndim != 3 or outputs.ndim != 2 or features.shape[:2] != outputs.shape:
        raise ValueError("feature and output arrays have incompatible shapes")
    _, n, blocks = features.shape
    result = np.empty((blocks, n), dtype=float)
    penalty = ridge * np.eye(blocks, dtype=float)
    for node in range(n):
        design = features[:, node, :]
        target = outputs[:, node]
        gram = design.T @ design + penalty
        rhs = design.T @ target
        try:
            result[:, node] = np.linalg.solve(gram, rhs)
        except np.linalg.LinAlgError as error:
            raise E3SyntheticError(f"ridge fit failed at node {node}: {error}") from error
    return result


def _local_blocks_for_target(
    features: np.ndarray,
    outputs: np.ndarray,
    target_time: int,
    window: int,
    ridge: float,
) -> np.ndarray:
    """Estimate target-time blocks using only observations strictly before target."""

    start = max(1, target_time - window)
    stop = target_time
    if stop - start < MINIMUM_LOCAL_ESTIMATES_FOR_TEMPORAL_METHOD:
        raise E3SyntheticError("insufficient causal observations for local fit")
    return _ridge_rowwise(features[start:stop], outputs[start:stop], ridge)


def _all_local_blocks(
    features: np.ndarray,
    outputs: np.ndarray,
    target_time: int,
    window: int,
    ridge: float,
) -> tuple[np.ndarray, np.ndarray]:
    times = np.arange(max(window + 1, 3), target_time + 1, dtype=int)
    if len(times) < MINIMUM_LOCAL_ESTIMATES_FOR_TEMPORAL_METHOD:
        raise E3SyntheticError("insufficient causal history for temporal method")
    estimates = np.stack(
        [_local_blocks_for_target(features, outputs, int(time), window, ridge) for time in times], axis=0
    )
    return times, estimates


def _causal_smoothed_blocks(local_estimates: np.ndarray, alpha: float) -> np.ndarray:
    result = np.empty_like(local_estimates)
    result[0] = local_estimates[0]
    for index in range(1, len(local_estimates)):
        result[index] = alpha * local_estimates[index] + (1.0 - alpha) * result[index - 1]
    return result


def _fixed_rank_last_block(local_estimates: np.ndarray, rank: int) -> np.ndarray:
    flattened = local_estimates.reshape(len(local_estimates), -1)
    if rank > min(flattened.shape):
        raise E3SyntheticError("fixed rank exceeds available causal design dimensions")
    mean = np.mean(flattened, axis=0, keepdims=True)
    centered = flattened - mean
    try:
        left, singular, right = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError as error:
        raise E3SyntheticError(f"fixed-rank basis fit failed: {error}") from error
    reconstructed = (left[:, :rank] * singular[:rank]) @ right[:rank] + mean
    return reconstructed[-1].reshape(local_estimates.shape[1:])


def _estimate_native_blocks(
    family: Family,
    method: Method,
    features: np.ndarray,
    outputs: np.ndarray,
    target_time: int,
    hyperparameter: float | int,
    *,
    ridge: float,
    stability_envelope: float,
) -> np.ndarray:
    """Fit one native retained-block state without accepting a query topology."""

    expected_blocks = coefficient_block_count(family)
    if features.shape[2] != expected_blocks:
        raise ValueError("feature block count does not match the declared family")
    if method == "local_structured":
        if not isinstance(hyperparameter, int):
            raise ValueError("local structured method requires an integer window")
        blocks = _local_blocks_for_target(features, outputs, target_time, hyperparameter, ridge)
    elif method == "causal_temporal_smoother":
        if not isinstance(hyperparameter, float):
            raise ValueError("causal temporal smoother requires a floating alpha")
        _, local = _all_local_blocks(
            features, outputs, target_time, FIXED_RANK_BOOTSTRAP_LOCAL_WINDOW, ridge
        )
        blocks = _causal_smoothed_blocks(local, hyperparameter)[-1]
    elif method == "fixed_rank_basis":
        if not isinstance(hyperparameter, int):
            raise ValueError("fixed-rank basis requires an integer rank")
        _, local = _all_local_blocks(
            features, outputs, target_time, FIXED_RANK_BOOTSTRAP_LOCAL_WINDOW, ridge
        )
        blocks = _fixed_rank_last_block(local, hyperparameter)
    else:
        raise ValueError("unknown native method")
    return project_blocks_to_stability_envelope(blocks, stability_envelope)


def _candidate_values(config: E3SyntheticConfig, method: Method) -> tuple[float | int, ...]:
    if method == "local_structured":
        return config.local_windows
    if method == "causal_temporal_smoother":
        return config.smoother_alphas
    if method == "fixed_rank_basis":
        return config.basis_ranks
    raise ValueError("unknown native method")


def _select_hyperparameter(fit_data: FitData, method: Method) -> SelectionResult:
    """Select only from observed-topology one-step validation prediction loss.

    Held-out query topologies and all topology-response truth are deliberately
    absent from this function's arguments and implementation.
    """

    features = _panel_features(fit_data)
    candidates = _candidate_values(fit_data.config, method)
    candidate_losses: list[float | None] = []
    for candidate in candidates:
        errors: list[float] = []
        try:
            path = _fit_native_path(fit_data, method, candidate)
            for time in fit_data.config.validation_indices:
                endpoint = path._state._evaluate_unchecked(
                    fit_data.observed_topologies[time], 1, int(time)
                )
                if endpoint.status != STATUS_AVAILABLE or endpoint.operator is None:
                    raise E3SyntheticError("validation endpoint is unavailable")
                prediction = endpoint.operator @ fit_data.responses[time - 1]
                errors.append(float(np.mean((prediction - fit_data.responses[time]) ** 2)))
        except (E3SyntheticError, FloatingPointError, np.linalg.LinAlgError, ValueError):
            candidate_losses.append(None)
            continue
        if not errors or not np.all(np.isfinite(errors)):
            candidate_losses.append(None)
            continue
        candidate_losses.append(float(np.mean(errors)))
    finite = [(index, value) for index, value in enumerate(candidate_losses) if value is not None]
    if not finite:
        return SelectionResult(method, None, None, STATUS_NONCONVERGED, tuple(candidate_losses))
    selected_index, loss = min(finite, key=lambda pair: (float(pair[1]), pair[0]))
    return SelectionResult(method, candidates[selected_index], float(loss), STATUS_AVAILABLE, tuple(candidate_losses))


def select_hyperparameter(fit_data: FitData, method: Method) -> SelectionResult:
    """Select a frozen hyperparameter after the E3-1 classification gate."""

    require_e3_1_gate()
    return _select_hyperparameter(fit_data, method)


def _evaluate_method_at_query(
    panel: SyntheticPanel,
    method: Method,
    selection: SelectionResult,
    query_class: QueryClass,
    target_time: int,
    horizon: int,
    *,
    fitted_path: NativePath | None = None,
) -> EvaluationRecord:
    """Internal held-out-query evaluation after a public E3-1 gate."""

    query = panel.query_topologies[query_class][target_time]
    truth = _native_endpoint(
        panel.family,
        panel.true_blocks[target_time],
        query,
        horizon,
        stability_threshold=panel.config.stability_threshold,
    )
    if truth.status != STATUS_AVAILABLE:
        raise E3SyntheticError("truth endpoint failed the declared stable-regime contract")
    if selection.status != STATUS_AVAILABLE or selection.selected is None:
        return EvaluationRecord(
            panel.family,
            panel.config.n,
            panel.seed,
            method,
            query_class,
            target_time,
            horizon,
            STATUS_NONCONVERGED,
            None,
            None,
            None,
            truth.spectral_radius,
            selection.selected,
            selection.validation_loss,
        )
    fit_data = fit_data_from_panel(panel)
    try:
        if fitted_path is None:
            path = _fit_native_path(fit_data, method, selection.selected)
        else:
            if (
                not _fit_data_matches_panel(fitted_path._state.fit_data, panel)
                or fitted_path._state.method != method
                or fitted_path._state.hyperparameter != selection.selected
            ):
                raise E3SyntheticError("fitted path does not match the declared evaluation state")
            path = fitted_path
        estimated = path._state._evaluate_unchecked(
            panel.query_topologies[query_class][target_time], horizon, target_time
        )
    except (E3SyntheticError, FloatingPointError, np.linalg.LinAlgError, ValueError):
        return EvaluationRecord(
            panel.family,
            panel.config.n,
            panel.seed,
            method,
            query_class,
            target_time,
            horizon,
            STATUS_NONCONVERGED,
            None,
            None,
            None,
            truth.spectral_radius,
            selection.selected,
            selection.validation_loss,
        )
    if estimated.status != STATUS_AVAILABLE:
        return EvaluationRecord(
            panel.family,
            panel.config.n,
            panel.seed,
            method,
            query_class,
            target_time,
            horizon,
            estimated.status,
            None,
            None,
            estimated.spectral_radius,
            truth.spectral_radius,
            selection.selected,
            selection.validation_loss,
        )
    assert estimated.operator is not None and estimated.responses is not None
    assert truth.operator is not None and truth.responses is not None
    operator_mse = float(np.mean((estimated.operator - truth.operator) ** 2))
    response_mse = float(np.mean((estimated.responses - truth.responses) ** 2))
    if not np.isfinite(operator_mse) or not np.isfinite(response_mse):
        return EvaluationRecord(
            panel.family,
            panel.config.n,
            panel.seed,
            method,
            query_class,
            target_time,
            horizon,
            STATUS_NONFINITE,
            None,
            None,
            estimated.spectral_radius,
            truth.spectral_radius,
            selection.selected,
            selection.validation_loss,
        )
    return EvaluationRecord(
        panel.family,
        panel.config.n,
        panel.seed,
        method,
        query_class,
        target_time,
        horizon,
        STATUS_AVAILABLE,
        operator_mse,
        response_mse,
        estimated.spectral_radius,
        truth.spectral_radius,
        selection.selected,
        selection.validation_loss,
    )


def evaluate_method_at_query(
    panel: SyntheticPanel,
    method: Method,
    selection: SelectionResult,
    query_class: QueryClass,
    target_time: int,
    horizon: int,
    *,
    fitted_path: NativePath | None = None,
) -> EvaluationRecord:
    """Evaluate a fixed method at a held-out topology after E3-1 passes."""

    require_e3_1_gate()
    return _evaluate_method_at_query(
        panel,
        method,
        selection,
        query_class,
        target_time,
        horizon,
        fitted_path=fitted_path,
    )


def evaluate_panel_recovery(panel: SyntheticPanel) -> tuple[EvaluationRecord, ...]:
    """Return all retained E3-3 records for one paired panel.

    The function does not make a comparison decision or drop unsuccessful
    endpoints. Consumers must retain every returned record.
    """

    require_e3_1_gate()
    fit_data = fit_data_from_panel(panel)
    selections = {method: _select_hyperparameter(fit_data, method) for method in METHODS}
    fitted_paths: dict[Method, NativePath | None] = {}
    for method, selection in selections.items():
        if selection.status != STATUS_AVAILABLE or selection.selected is None:
            fitted_paths[method] = None
            continue
        try:
            fitted_paths[method] = _fit_native_path(fit_data, method, selection.selected)
        except (E3SyntheticError, FloatingPointError, np.linalg.LinAlgError, ValueError):
            fitted_paths[method] = None
    records: list[EvaluationRecord] = []
    for method, selection in selections.items():
        for query_class in QUERY_CLASSES:
            for horizon in panel.config.horizons:
                for target_time in panel.config.evaluation_indices:
                    records.append(
                        _evaluate_method_at_query(
                            panel,
                            method,
                            selection,
                            query_class,
                            int(target_time),
                            horizon,
                            fitted_path=fitted_paths[method],
                        )
                    )
    return tuple(records)


def _method_predictions_before_target(
    panel: SyntheticPanel,
    method: Method,
    selection: SelectionResult,
    target_time: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return fixed-design fitted values and residuals for the bootstrap route."""

    if selection.status != STATUS_AVAILABLE or selection.selected is None:
        raise E3SyntheticError("cannot bootstrap a non-converged selected method")
    if method != "fixed_rank_basis" or isinstance(selection.selected, bool) or not isinstance(
        selection.selected, int
    ):
        raise E3SyntheticError("bootstrap route requires a selected fixed-rank basis method")
    fit_data = fit_data_from_panel(panel)
    features = _panel_features(fit_data)
    schedule = fixed_rank_bootstrap_refit_schedule(
        panel.config, selection.selected, target_time=target_time
    )
    times = np.asarray(schedule.refit_times, dtype=int)
    predictions = np.empty((len(times), panel.config.n), dtype=float)
    outputs = np.empty_like(predictions)
    for index, time in enumerate(times):
        blocks = _estimate_native_blocks(
            panel.family,
            method,
            features,
            fit_data.responses,
            int(time),
            selection.selected,
            ridge=fit_data.config.ridge,
            stability_envelope=fit_data.config.stability_envelope,
        )
        predictions[index] = np.sum(features[time] * blocks.T, axis=1)
        outputs[index] = panel.responses[time]
    return predictions, outputs


def _moving_block_indices(length: int, block_length: int, rng: np.random.Generator) -> np.ndarray:
    if length < 2 or block_length < 1:
        raise ValueError("bootstrap sequence is invalid")
    blocks: list[np.ndarray] = []
    while sum(len(block) for block in blocks) < length:
        start = int(rng.integers(0, length))
        blocks.append((start + np.arange(block_length, dtype=int)) % length)
    return np.concatenate(blocks)[:length]


def _bootstrap_outputs(
    panel: SyntheticPanel,
    method: Method,
    selection: SelectionResult,
    target_time: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return one recursively generated residual-bootstrap response path."""

    return _recursive_bootstrap_fit_data(
        panel, method, selection, target_time, rng
    ).responses


def _recursive_bootstrap_fit_data(
    panel: SyntheticPanel,
    method: Method,
    selection: SelectionResult,
    target_time: int,
    rng: np.random.Generator,
) -> FitData:
    """Generate a pseudo-series whose lagged design follows its own history.

    The observed prefix supplies the minimum causal initialization. Every later
    pseudo-response is generated from blocks fitted only to the pseudo-history
    available before that time, followed by one resampled residual vector.
    """

    predicted, outputs = _method_predictions_before_target(panel, method, selection, target_time)
    residuals = outputs - predicted
    if not np.all(np.isfinite(residuals)):
        raise FloatingPointError("bootstrap residual pool contains non-finite values")
    indices = _moving_block_indices(len(residuals), panel.config.bootstrap_block_length, rng)
    pseudo = panel.responses.copy()
    if selection.selected is None or isinstance(selection.selected, bool) or not isinstance(
        selection.selected, int
    ):
        raise E3SyntheticError("bootstrap route requires a selected integer fixed rank")
    schedule = fixed_rank_bootstrap_refit_schedule(
        panel.config, selection.selected, target_time=target_time
    )
    times = np.asarray(schedule.refit_times, dtype=int)
    for index, time in enumerate(times):
        current_fit_data = FitData(
            family=panel.family,
            config=panel.config,
            seed=panel.seed,
            observed_topologies=panel.observed_topologies,
            responses=pseudo,
        )
        current_features = _panel_features(current_fit_data)
        blocks = _estimate_native_blocks(
            panel.family,
            method,
            current_features,
            pseudo,
            int(time),
            selection.selected,
            ridge=panel.config.ridge,
            stability_envelope=panel.config.stability_envelope,
        )
        recursive_prediction = np.sum(current_features[time] * blocks.T, axis=1)
        pseudo[time] = recursive_prediction + residuals[indices[index]]
        if not np.all(np.isfinite(pseudo[time])):
            raise FloatingPointError("recursive bootstrap generated a non-finite response")
    return FitData(
        family=panel.family,
        config=panel.config,
        seed=panel.seed,
        observed_topologies=panel.observed_topologies,
        responses=pseudo,
    )


def simultaneous_response_interval(
    panel: SyntheticPanel,
    selection: SelectionResult,
    query_class: QueryClass,
    target_time: int,
    *,
    bootstrap_seed: int,
) -> Mapping[str, Any]:
    """Run the frozen E3-4 interval procedure for a selected basis method.

    This is a recursive residual moving-block bootstrap. Each pseudo-series
    rebuilds lagged features, retunes over the frozen candidate list and refits
    the selected method. Failed replicates remain in the status inventory.
    """

    require_e3_1_gate()
    method: Method = "fixed_rank_basis"
    horizon = 4
    if selection.method != method:
        raise ValueError("E3-4 is frozen to the selected fixed-rank basis method")
    baseline_record = _evaluate_method_at_query(
        panel, method, selection, query_class, target_time, horizon
    )
    if baseline_record.status != STATUS_AVAILABLE or selection.selected is None:
        return {
            "status": baseline_record.status,
            "coverage": None,
            "mean_interval_width": None,
            "raw_response_mse": None,
            "stability_qualified_response_mse": None,
            "estimated_spectral_radius": baseline_record.estimated_spectral_radius,
            "truth_spectral_radius": baseline_record.truth_spectral_radius,
            "completed_replicates": 0,
            "requested_replicates": panel.config.bootstrap_replicates,
            "bootstrap_retune_attempts": 0,
            "bootstrap_status_counts": {status: 0 for status in sorted(STATUS_SCHEMA)},
        }
    fit_data = fit_data_from_panel(panel)
    features = _panel_features(fit_data)
    query = panel.query_topologies[query_class][target_time]
    point_blocks = _estimate_native_blocks(
        panel.family,
        method,
        features,
        fit_data.responses,
        target_time,
        selection.selected,
        ridge=fit_data.config.ridge,
        stability_envelope=fit_data.config.stability_envelope,
    )
    point_endpoint = _native_endpoint(
        panel.family,
        point_blocks,
        query,
        horizon,
        stability_threshold=panel.config.stability_threshold,
    )
    truth_endpoint = _native_endpoint(
        panel.family,
        panel.true_blocks[target_time],
        query,
        horizon,
        stability_threshold=panel.config.stability_threshold,
    )
    if point_endpoint.status != STATUS_AVAILABLE or truth_endpoint.status != STATUS_AVAILABLE:
        raise E3SyntheticError("available E3-4 baseline lost its full endpoint")
    assert point_endpoint.responses is not None and truth_endpoint.responses is not None
    point_response = point_endpoint.responses[-1]
    truth_response = truth_endpoint.responses[-1]
    raw_response_mse = float(np.mean((point_response - truth_response) ** 2))
    rng = _rng(bootstrap_seed, panel.seed, target_time)
    bootstrap_responses: list[np.ndarray] = []
    bootstrap_status_counts = {status: 0 for status in sorted(STATUS_SCHEMA)}
    bootstrap_retune_attempts = 0
    for _ in range(panel.config.bootstrap_replicates):
        try:
            pseudo_outputs = _bootstrap_outputs(panel, method, selection, target_time, rng)
            pseudo_fit_data = FitData(
                family=panel.family,
                config=panel.config,
                seed=panel.seed,
                observed_topologies=panel.observed_topologies,
                responses=pseudo_outputs,
            )
            bootstrap_retune_attempts += 1
            bootstrap_selection = _select_hyperparameter(pseudo_fit_data, method)
            if (
                bootstrap_selection.status != STATUS_AVAILABLE
                or bootstrap_selection.selected is None
            ):
                bootstrap_status_counts[STATUS_NONCONVERGED] += 1
                continue
            pseudo_features = _panel_features(pseudo_fit_data)
            blocks = _estimate_native_blocks(
                panel.family,
                method,
                pseudo_features,
                pseudo_fit_data.responses,
                target_time,
                bootstrap_selection.selected,
                ridge=panel.config.ridge,
                stability_envelope=panel.config.stability_envelope,
            )
            endpoint = _native_endpoint(
                panel.family,
                blocks,
                query,
                horizon,
                stability_threshold=panel.config.stability_threshold,
            )
        except FloatingPointError:
            bootstrap_status_counts[STATUS_NONFINITE] += 1
            continue
        except (E3SyntheticError, np.linalg.LinAlgError, ValueError):
            bootstrap_status_counts[STATUS_NONCONVERGED] += 1
            continue
        if endpoint.status == STATUS_AVAILABLE and endpoint.responses is not None:
            bootstrap_status_counts[STATUS_AVAILABLE] += 1
            bootstrap_responses.append(endpoint.responses[-1])
        else:
            bootstrap_status_counts[endpoint.status] += 1
    if len(bootstrap_responses) < 2:
        return {
            "status": STATUS_NONCONVERGED,
            "coverage": None,
            "mean_interval_width": None,
            "raw_response_mse": raw_response_mse,
            "stability_qualified_response_mse": None,
            "estimated_spectral_radius": baseline_record.estimated_spectral_radius,
            "truth_spectral_radius": baseline_record.truth_spectral_radius,
            "completed_replicates": len(bootstrap_responses),
            "requested_replicates": panel.config.bootstrap_replicates,
            "bootstrap_retune_attempts": bootstrap_retune_attempts,
            "bootstrap_status_counts": bootstrap_status_counts,
        }
    failed_statuses = [
        status for status, count in bootstrap_status_counts.items() if status != STATUS_AVAILABLE and count
    ]
    if failed_statuses:
        failure_status = (
            STATUS_NONFINITE
            if STATUS_NONFINITE in failed_statuses
            else STATUS_UNSTABLE
            if STATUS_UNSTABLE in failed_statuses
            else STATUS_NONCONVERGED
        )
        return {
            "status": failure_status,
            "coverage": None,
            "mean_interval_width": None,
            "raw_response_mse": raw_response_mse,
            "stability_qualified_response_mse": None,
            "estimated_spectral_radius": baseline_record.estimated_spectral_radius,
            "truth_spectral_radius": baseline_record.truth_spectral_radius,
            "completed_replicates": len(bootstrap_responses),
            "requested_replicates": panel.config.bootstrap_replicates,
            "bootstrap_retune_attempts": bootstrap_retune_attempts,
            "bootstrap_status_counts": bootstrap_status_counts,
        }
    draws = np.stack(bootstrap_responses, axis=0)
    deviations = np.max(np.abs(draws - point_response[None, ...]), axis=(1, 2))
    critical = float(np.quantile(deviations, 0.95, method="higher"))
    lower = point_response - critical
    upper = point_response + critical
    coverage = float(np.all((truth_response >= lower) & (truth_response <= upper)))
    return {
        "status": STATUS_AVAILABLE,
        "coverage": coverage,
        "mean_interval_width": float(np.mean(upper - lower)),
        "raw_response_mse": raw_response_mse,
        "stability_qualified_response_mse": raw_response_mse,
        "estimated_spectral_radius": baseline_record.estimated_spectral_radius,
        "truth_spectral_radius": baseline_record.truth_spectral_radius,
        "completed_replicates": len(bootstrap_responses),
        "requested_replicates": panel.config.bootstrap_replicates,
        "bootstrap_retune_attempts": bootstrap_retune_attempts,
        "bootstrap_status_counts": bootstrap_status_counts,
    }


def _fraction_matrix_product(left: tuple[tuple[int, ...], ...], right: tuple[tuple[int, ...], ...]) -> tuple[tuple[Fraction, ...], ...]:
    size = len(left)
    return tuple(
        tuple(
            sum(Fraction(left[row][index]) * Fraction(right[index][column]) for index in range(size))
            for column in range(size)
        )
        for row in range(size)
    )


def _fraction_identity(size: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(Fraction(int(row == column)) for column in range(size)) for row in range(size))


def _fraction_add(*matrices: tuple[tuple[Fraction, ...], ...]) -> tuple[tuple[Fraction, ...], ...]:
    size = len(matrices[0])
    return tuple(
        tuple(sum(matrix[row][column] for matrix in matrices) for column in range(size))
        for row in range(size)
    )


def _fraction_scale(matrix: tuple[tuple[Fraction, ...], ...], scalar: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(Fraction(scalar) * value for value in row) for row in matrix)


def _fraction_zero(size: int) -> tuple[tuple[Fraction, ...], ...]:
    return tuple(tuple(Fraction(0) for _ in range(size)) for _ in range(size))


def exact_domain_stability_certificate_report() -> Mapping[str, Any]:
    """Check the E4 row-sum certificate using rational arithmetic only."""

    envelope = Fraction(9, 10)
    topology_cases: Mapping[str, tuple[tuple[Fraction, ...], ...]] = {
        "signed_row_normalized": (
            (Fraction(0), Fraction(2, 3), Fraction(-1, 3)),
            (Fraction(-1, 4), Fraction(0), Fraction(3, 4)),
            (Fraction(1, 5), Fraction(-4, 5), Fraction(0)),
        ),
        "directed_sparse": (
            (Fraction(0), Fraction(1), Fraction(0)),
            (Fraction(0), Fraction(0), Fraction(1)),
            (Fraction(1), Fraction(0), Fraction(0)),
        ),
        "latent_position": (
            (Fraction(0), Fraction(1, 2), Fraction(1, 2)),
            (Fraction(1, 3), Fraction(0), Fraction(2, 3)),
            (Fraction(3, 4), Fraction(1, 4), Fraction(0)),
        ),
    }
    block_cases: Mapping[str, Mapping[str, tuple[tuple[Fraction, ...], ...]]] = {
        FAMILY1: {
            "zero": ((Fraction(0),) * 3, (Fraction(0),) * 3),
            "boundary": ((Fraction(2, 5),) * 3, (Fraction(-1, 2),) * 3),
            "projected": ((Fraction(9, 10),) * 3, (Fraction(-9, 10),) * 3),
        },
        FAMILY2: {
            "zero": ((Fraction(0),) * 3,) * 3,
            "boundary": (
                (Fraction(1, 5),) * 3,
                (Fraction(3, 10),) * 3,
                (Fraction(-2, 5),) * 3,
            ),
            "projected": (
                (Fraction(3, 5),) * 3,
                (Fraction(-3, 5),) * 3,
                (Fraction(3, 5),) * 3,
            ),
        },
    }

    records: list[Mapping[str, str]] = []
    maximum_block_norm = Fraction(0)
    maximum_operator_norm = Fraction(0)
    for family in (FAMILY1, FAMILY2):
        for coefficient_case in ("zero", "boundary", "projected"):
            raw = block_cases[family][coefficient_case]
            node_norms = tuple(
                sum(abs(raw[block][node]) for block in range(len(raw)))
                for node in range(3)
            )
            scales = tuple(
                Fraction(1) if norm == 0 else min(Fraction(1), envelope / norm)
                for norm in node_norms
            )
            projected = tuple(
                tuple(raw[block][node] * scales[node] for node in range(3))
                for block in range(len(raw))
            )
            projected_norm = max(
                sum(abs(projected[block][node]) for block in range(len(projected)))
                for node in range(3)
            )
            maximum_block_norm = max(maximum_block_norm, projected_norm)
            for topology_case, topology in topology_cases.items():
                squared = _fraction_matrix_product(topology, topology)
                operator = tuple(
                    tuple(
                        projected[0][row] * Fraction(int(row == column))
                        + projected[1][row] * topology[row][column]
                        + (
                            projected[2][row] * squared[row][column]
                            if family == FAMILY2
                            else Fraction(0)
                        )
                        for column in range(3)
                    )
                    for row in range(3)
                )
                topology_norm = max(sum(abs(value) for value in row) for row in topology)
                squared_norm = max(sum(abs(value) for value in row) for row in squared)
                operator_norm = max(sum(abs(value) for value in row) for row in operator)
                maximum_operator_norm = max(maximum_operator_norm, operator_norm)
                records.append(
                    {
                        "family": family,
                        "coefficient_case": coefficient_case,
                        "topology_case": topology_case,
                        "projected_block_norm": str(projected_norm),
                        "topology_infinity_norm": str(topology_norm),
                        "topology_square_infinity_norm": str(squared_norm),
                        "operator_infinity_norm": str(operator_norm),
                    }
                )
    status = (
        STATUS_AVAILABLE
        if maximum_block_norm <= envelope
        and maximum_operator_norm <= envelope
        and all(Fraction(record["topology_infinity_norm"]) <= 1 for record in records)
        and all(Fraction(record["topology_square_infinity_norm"]) <= 1 for record in records)
        else STATUS_NONCONVERGED
    )
    return {
        "status": status,
        "arithmetic": "fractions.Fraction",
        "envelope": str(envelope),
        "checked_operators": len(records),
        "max_projected_block_norm": str(maximum_block_norm),
        "max_operator_infinity_norm": str(maximum_operator_norm),
        "spectral_radius_bound_follows_from_induced_norm": True,
        "records": records,
    }


def _fraction_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    if not matrix:
        return 0
    working = [list(row) for row in matrix]
    rows, columns = len(working), len(working[0])
    pivot_row = 0
    for column in range(columns):
        pivot = next((row for row in range(pivot_row, rows) if working[row][column] != 0), None)
        if pivot is None:
            continue
        working[pivot_row], working[pivot] = working[pivot], working[pivot_row]
        pivot_value = working[pivot_row][column]
        working[pivot_row] = [value / pivot_value for value in working[pivot_row]]
        for row in range(rows):
            if row == pivot_row:
                continue
            scale = working[row][column]
            if scale:
                working[row] = [value - scale * base for value, base in zip(working[row], working[pivot_row])]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def _row_design(topology: tuple[tuple[int, ...], ...], row: int) -> tuple[tuple[Fraction, ...], ...]:
    squared = _fraction_matrix_product(topology, topology)
    return tuple(
        (Fraction(int(column == row)), Fraction(topology[row][column]), squared[row][column])
        for column in range(len(topology))
    )


def exact_query_transfer_fixture_report() -> Mapping[str, Mapping[str, Any]]:
    """Verify the frozen Family-1/Family-2 exact fixture classifications.

    The returned values are classifications and algebraic witness booleans, not
    recovery metrics or a model ranking. Integer/Fraction arithmetic prevents a
    floating-point rank test from acting as proof.
    """

    p = ((0, 1, 0), (0, 0, 1), (1, 0, 0))
    p2 = _fraction_matrix_product(p, p)
    zero = _fraction_zero(3)
    identity = _fraction_identity(3)
    f1_world0 = zero
    f1_world1_observed = _fraction_add(_fraction_scale(p, -1), _fraction_matrix_product(identity, p))
    f1_world1_query = _fraction_add(_fraction_scale(p, -1), _fraction_matrix_product(identity, p2))
    if f1_world0 != f1_world1_observed or f1_world0 == f1_world1_query:
        raise E3SyntheticError("Family-1 exact negative fixture failed")

    f2_world1_observed = _fraction_add(
        _fraction_scale(p, -1),
        _fraction_scale(p2, -2),
        _fraction_matrix_product(identity, p),
        _fraction_scale(_fraction_matrix_product(identity, p2), 2),
    )
    f2_world1_query = _fraction_add(
        _fraction_scale(p, -1),
        _fraction_scale(p2, -2),
        _fraction_matrix_product(identity, p2),
        _fraction_scale(_fraction_matrix_product(identity, _fraction_matrix_product(p2, p2)), 2),
    )
    if f2_world1_observed != zero or f2_world1_query == zero:
        raise E3SyntheticError("Family-2 unrestricted exact negative fixture failed")

    w0 = ((0, 1, 0), (0, 0, 0), (0, 0, 0))
    wq = ((0, 1, 0), (0, 0, 1), (0, 0, 0))
    c2 = ((1, 0, 0), (0, 0, 0), (0, 0, 0))
    diagonal_observed = _fraction_matrix_product(c2, _fraction_matrix_product(w0, w0))
    diagonal_query = _fraction_matrix_product(c2, _fraction_matrix_product(wq, wq))
    if diagonal_observed != zero or diagonal_query == zero:
        raise E3SyntheticError("Family-2 diagonal exact negative fixture failed")

    ranks = tuple(_fraction_rank(_row_design(p, row)) for row in range(3))
    if ranks != (3, 3, 3):
        raise E3SyntheticError("Family-2 structured-positive rank witness failed")

    v = ((0, 1), (1, 0))
    zero_two = _fraction_zero(2)
    identity_two = _fraction_identity(2)
    # Equality at W=0 fixes A=0. Equality at W=V then fixes B=V^{-1}=V.
    # The forced one-hop continuation at 2V is therefore 2I, not 4I.
    forced_a = zero_two
    forced_b = tuple(tuple(Fraction(value) for value in row) for row in v)
    one_hop_at_zero = forced_a
    one_hop_at_v = _fraction_add(forced_a, _fraction_matrix_product(forced_b, v))
    two_v = tuple(tuple(2 * entry for entry in row) for row in v)
    one_hop_at_two_v = _fraction_add(forced_a, _fraction_matrix_product(forced_b, two_v))
    two_hop_at_zero = zero_two
    two_hop_at_v = _fraction_matrix_product(v, v)
    two_hop_at_two_v = _fraction_matrix_product(two_v, two_v)
    four_identity = _fraction_scale(identity_two, 4)
    if (
        one_hop_at_zero != two_hop_at_zero
        or one_hop_at_v != identity_two
        or two_hop_at_v != identity_two
        or one_hop_at_two_v == two_hop_at_two_v
        or one_hop_at_two_v != _fraction_scale(identity_two, 2)
        or two_hop_at_two_v != four_identity
    ):
        raise E3SyntheticError("Family-2 non-equivalence witness failed")

    return {
        "f1_negative": {
            "status": STATUS_OUTSIDE_TARGET,
            "observed_worlds_equal": True,
            "queried_worlds_disagree": True,
        },
        "f2_unrestricted_negative": {
            "status": STATUS_OUTSIDE_TARGET,
            "observed_worlds_equal": True,
            "queried_worlds_disagree": True,
        },
        "f2_diagonal_negative": {
            "status": STATUS_OUTSIDE_TARGET,
            "observed_worlds_equal": True,
            "queried_worlds_disagree": True,
        },
        "f2_diagonal_positive": {
            "status": STATUS_AVAILABLE,
            "row_ranks": list(ranks),
            "identified_inverse_available": True,
        },
        "non_equivalence": {
            "status": "DISTINCT_FAMILY",
            "one_hop_at_v_equals_identity": True,
            "one_hop_at_2v_equals_2i": True,
            "two_hop_at_2v_equals_4i": True,
        },
    }


def require_e3_1_gate() -> Mapping[str, Mapping[str, Any]]:
    """Run and validate the prerequisite exact two-family classification gate.

    This function is intentionally called by every fitting/evaluation path in
    this module. A fixture failure therefore prevents E3-2 through E3-4 from
    starting rather than merely appearing in a separate test report.
    """

    report = exact_query_transfer_fixture_report()
    expected = {
        "f1_negative": STATUS_OUTSIDE_TARGET,
        "f2_unrestricted_negative": STATUS_OUTSIDE_TARGET,
        "f2_diagonal_negative": STATUS_OUTSIDE_TARGET,
        "f2_diagonal_positive": STATUS_AVAILABLE,
        "non_equivalence": "DISTINCT_FAMILY",
    }
    for fixture_id, expected_status in expected.items():
        if report.get(fixture_id, {}).get("status") != expected_status:
            raise E3SyntheticError(f"E3-1 gate failed for {fixture_id}")
    return report


def aggregate_recovery_records(records: Iterable[EvaluationRecord]) -> Mapping[str, Mapping[str, Any]]:
    """Summarize every retained date-level record without masking failures."""

    buckets: dict[str, list[EvaluationRecord]] = {}
    for record in records:
        key = "|".join(
            (
                record.family,
                str(record.n),
                record.method,
                record.query_class,
                str(record.horizon),
            )
        )
        buckets.setdefault(key, []).append(record)
    summary: dict[str, Mapping[str, Any]] = {}
    for key, group in buckets.items():
        available = [record for record in group if record.status == STATUS_AVAILABLE]
        status_counts = {status: 0 for status in sorted(STATUS_SCHEMA)}
        for record in group:
            status_counts[record.status] += 1
        summary[key] = {
            "retained_date_records": len(group),
            "distinct_panels": len({record.seed for record in group}),
            "available_date_records": len(available),
            "status_counts": status_counts,
            "operator_mse_mean": (
                float(np.mean([record.operator_mse for record in available if record.operator_mse is not None]))
                if available
                else None
            ),
            "response_mse_mean": (
                float(np.mean([record.response_mse for record in available if record.response_mse is not None]))
                if available
                else None
            ),
        }
    return summary


def paired_common_completion(
    records: Iterable[EvaluationRecord], *, candidate_method: str, comparator_method: str
) -> Mapping[str, Any]:
    """Construct the declared same-endpoint common-completion comparison set.

    Every date-level key remains counted even when either method fails. Only
    the explicit common-completion subset receives paired numerical
    differences; unavailable endpoints are never imputed or ranked.
    """

    indexed: dict[tuple[str, int, int, QueryClass, int, int, str], EvaluationRecord] = {}
    for record in records:
        if record.method not in {candidate_method, comparator_method}:
            continue
        key = (
            record.family,
            record.n,
            record.seed,
            record.query_class,
            record.horizon,
            record.target_time,
            record.method,
        )
        if key in indexed:
            raise E3SyntheticError("duplicate recovery record for a declared paired key")
        indexed[key] = record
    base_keys = {
        key[:-1]
        for key in indexed
    }
    candidate_status_counts = {status: 0 for status in sorted(STATUS_SCHEMA)}
    comparator_status_counts = {status: 0 for status in sorted(STATUS_SCHEMA)}
    operator_differences: list[float] = []
    response_differences: list[float] = []
    for base in sorted(base_keys):
        candidate = indexed.get((*base, candidate_method))
        comparator = indexed.get((*base, comparator_method))
        if candidate is not None:
            candidate_status_counts[candidate.status] += 1
        if comparator is not None:
            comparator_status_counts[comparator.status] += 1
        if candidate is None or comparator is None:
            raise E3SyntheticError("declared paired comparison is missing a method record")
        if candidate.status != STATUS_AVAILABLE or comparator.status != STATUS_AVAILABLE:
            continue
        if (
            candidate.operator_mse is None
            or comparator.operator_mse is None
            or candidate.response_mse is None
            or comparator.response_mse is None
        ):
            raise E3SyntheticError("available common-completion row lacks a numerical endpoint loss")
        operator_differences.append(candidate.operator_mse - comparator.operator_mse)
        response_differences.append(candidate.response_mse - comparator.response_mse)
    return {
        "declared_date_keys": len(base_keys),
        "common_completion_date_keys": len(response_differences),
        "candidate_status_counts": candidate_status_counts,
        "comparator_status_counts": comparator_status_counts,
        "operator_mse_differences": tuple(operator_differences),
        "response_mse_differences": tuple(response_differences),
    }
