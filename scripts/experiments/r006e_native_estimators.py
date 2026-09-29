"""Fit-boundary-isolated estimators for the R006e native protocol."""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Iterator, Mapping

import numpy as np

from scripts.experiments.r005_separation_stability_pilot import (
    _tucker_reconstruct,
)
from scripts.experiments.r006b_stability_signal_deconfounding import (
    _fused_reconstruct,
)
from scripts.experiments.r006c_endpoint_estimators import (
    estimate_anchor_local as _estimate_anchor_local,
)
from scripts.experiments.r006c_endpoint_protocol import (
    EstimationInputs,
    R006CConfig,
)
from scripts.experiments.r006e_native_protocol import FitInputs, R006EConfig


REQUIRED_COMPARATORS = (
    "anchor_local",
    "anchor_fused_tv",
    "anchor_split_tucker333",
)
FUSED_PENALTIES = (0.10, 0.25, 0.50, 1.00)
SPLIT_TUCKER_RANK = 3


@dataclass(frozen=True)
class _ImmutableJSONMapping(Mapping[str, object]):
    """Tuple-backed mapping with fresh JSON-primitive export snapshots."""

    _items: tuple[tuple[str, object], ...]

    def __getitem__(self, key: str) -> object:
        for item_key, value in self._items:
            if item_key == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def to_json_dict(self) -> dict[str, object]:
        return {
            key: _plain_json(value)
            for key, value in self._items
        }


def _freeze_json(value: object, *, location: str = "diagnostics") -> object:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{location} contains a non-finite float")
        return value
    if isinstance(value, Mapping):
        frozen: list[tuple[str, object]] = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{location} keys must be strings")
            frozen.append(
                (key, _freeze_json(item, location=f"{location}.{key}"))
            )
        return _ImmutableJSONMapping(tuple(frozen))
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_json(item, location=f"{location}[{index}]")
            for index, item in enumerate(value)
        )
    raise TypeError(f"{location} must contain only JSON primitives")


def _plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain_json(item) for item in value]
    return value


def _without_timing_metadata(value: object) -> object:
    """Remove only declared runtime metadata from digest input, recursively."""
    if isinstance(value, Mapping):
        return {
            key: _without_timing_metadata(item)
            for key, item in value.items()
            if key != "runtime_seconds"
        }
    if isinstance(value, (list, tuple)):
        return [_without_timing_metadata(item) for item in value]
    return value


def _readonly_array(value: np.ndarray) -> np.ndarray:
    contiguous = np.ascontiguousarray(value)
    immutable_buffer = contiguous.tobytes()
    return np.frombuffer(immutable_buffer, dtype=contiguous.dtype).reshape(
        contiguous.shape
    )


@dataclass(frozen=True)
class FittedPath:
    method: str
    parameterization: str
    tensor: np.ndarray
    dates: np.ndarray
    selected_penalty: float | None
    diagnostics: Mapping[str, object]
    runtime_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.method, str) or not self.method:
            raise ValueError("method must be a non-empty string")
        if not isinstance(self.parameterization, str) or not self.parameterization:
            raise ValueError("parameterization must be a non-empty string")

        tensor = np.asarray(self.tensor)
        dates = np.asarray(self.dates)
        if tensor.ndim != 3 or not np.issubdtype(tensor.dtype, np.number):
            raise ValueError("tensor must be a numeric three-dimensional array")
        if not np.all(np.isfinite(tensor)):
            raise ValueError("tensor must be finite")
        if dates.ndim != 1 or not np.issubdtype(dates.dtype, np.integer):
            raise ValueError("dates must be an integer vector")
        if dates.size != tensor.shape[2]:
            raise ValueError("dates must align with the tensor time dimension")
        if np.any(dates[1:] <= dates[:-1]):
            raise ValueError("dates must be strictly increasing")

        penalty = self.selected_penalty
        if penalty is not None:
            if not isinstance(penalty, (int, float)):
                raise TypeError("selected_penalty must be numeric or None")
            if not math.isfinite(float(penalty)) or float(penalty) < 0.0:
                raise ValueError("selected_penalty must be finite and non-negative")
            object.__setattr__(self, "selected_penalty", float(penalty))
        if not isinstance(self.diagnostics, Mapping):
            raise TypeError("diagnostics must be a mapping")
        if not isinstance(self.runtime_seconds, (int, float)):
            raise TypeError("runtime_seconds must be numeric")
        if not math.isfinite(float(self.runtime_seconds)) or self.runtime_seconds < 0.0:
            raise ValueError("runtime_seconds must be finite and non-negative")

        diagnostics = _freeze_json(self.diagnostics)
        if not isinstance(diagnostics, _ImmutableJSONMapping):
            raise TypeError("diagnostics must freeze to a mapping")
        status = diagnostics.get("status")
        if status not in {"success", "failure"}:
            raise ValueError("diagnostics status must be 'success' or 'failure'")
        if status == "success":
            if tensor.shape[2] == 0:
                raise ValueError("successful paths must contain scientific dates")
        else:
            if tensor.shape[2] != 0 or dates.size != 0:
                raise ValueError("failure paths cannot contain scientific payload")
            if penalty is not None:
                raise ValueError("failure paths cannot select a penalty")
            required = (
                "error_type",
                "error_message",
                "intended_dates",
                "intended_count",
                "expected_tensor_shape",
            )
            if any(key not in diagnostics for key in required):
                raise ValueError("failure diagnostics are incomplete")
            error_type = diagnostics["error_type"]
            error_message = diagnostics["error_message"]
            intended_dates = diagnostics["intended_dates"]
            intended_count = diagnostics["intended_count"]
            expected_shape = diagnostics["expected_tensor_shape"]
            if not isinstance(error_type, str) or not error_type:
                raise ValueError("failure error_type must be a non-empty string")
            if not isinstance(error_message, str):
                raise ValueError("failure error_message must be a string")
            if not isinstance(intended_dates, tuple) or any(
                not isinstance(value, int) for value in intended_dates
            ):
                raise ValueError("failure intended_dates must contain integers")
            if not isinstance(intended_count, int) or intended_count < 0:
                raise ValueError("failure intended_count must be non-negative")
            if intended_count != len(intended_dates):
                raise ValueError("failure intended dates and count disagree")
            if (
                not isinstance(expected_shape, tuple)
                or len(expected_shape) != 3
                or any(not isinstance(value, int) or value < 0 for value in expected_shape)
                or expected_shape[2] != intended_count
            ):
                raise ValueError("failure expected tensor shape is invalid")

        object.__setattr__(self, "tensor", _readonly_array(tensor))
        object.__setattr__(self, "dates", _readonly_array(dates))
        object.__setattr__(self, "diagnostics", diagnostics)
        object.__setattr__(self, "runtime_seconds", float(self.runtime_seconds))

    @property
    def status(self) -> str:
        return str(self.diagnostics["status"])

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    def require_success(self) -> FittedPath:
        if not self.is_success:
            raise RuntimeError(
                f"{self.method} fit failed: {self.diagnostics['error_type']}: "
                f"{self.diagnostics['error_message']}"
            )
        return self


def _update_array_digest(digest: object, array: np.ndarray) -> None:
    contiguous = np.ascontiguousarray(array)
    metadata = {
        "dtype": contiguous.dtype.str,
        "shape": list(contiguous.shape),
    }
    digest.update(
        json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("ascii")
    )
    digest.update(contiguous.tobytes())


def fit_path_digest(path: FittedPath) -> str:
    """Hash all scientific path content while deliberately excluding runtime."""
    digest = hashlib.sha256()
    for value in (path.method, path.parameterization):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    _update_array_digest(digest, path.tensor)
    _update_array_digest(digest, path.dates)
    scientific = {
        "selected_penalty": path.selected_penalty,
        "diagnostics": _without_timing_metadata(path.diagnostics.to_json_dict()),
    }
    digest.update(
        json.dumps(
            scientific,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return digest.hexdigest()


def fit_bundle_digest(bundle: Mapping[str, FittedPath]) -> str:
    """Return an order-independent canonical digest of fitted paths."""
    if not isinstance(bundle, Mapping):
        raise TypeError("bundle must be a mapping")
    digest = hashlib.sha256()
    for name in sorted(bundle):
        if not isinstance(name, str) or not isinstance(bundle[name], FittedPath):
            raise TypeError("bundle must map string names to FittedPath records")
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(bytes.fromhex(fit_path_digest(bundle[name])))
    return digest.hexdigest()


def _validate_local_tensor(
    local_tensor: np.ndarray,
    *,
    fit: FitInputs | None,
    config: R006EConfig,
) -> np.ndarray:
    local = np.asarray(local_tensor, dtype=float)
    expected_dates = len(fit.coefficient_dates) if fit is not None else local.shape[2]
    if local.shape != (config.n, 2 * config.n, expected_dates):
        raise ValueError("anchor-local tensor has incompatible dimensions")
    if not np.all(np.isfinite(local)):
        raise ValueError("anchor-local tensor must be finite")
    return local


def _r006c_fused_config(config: R006EConfig) -> R006CConfig:
    return R006CConfig(
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
        fused_penalties=FUSED_PENALTIES,
    )


def fit_anchor_local(fit: FitInputs, *, config: R006EConfig) -> FittedPath:
    """Adapt the unchanged R006c scale-adaptive anchor-local estimator."""
    started = time.perf_counter()
    inputs = EstimationInputs(
        predictors=fit.predictors,
        outcomes=fit.outcomes,
        topology=fit.topology,
        W_ref=fit.w_ref,
    )
    tensor, dates, separation, ridge = _estimate_anchor_local(
        inputs,
        window=config.window,
        ridge_multiplier=config.ridge_multiplier,
    )
    if not np.array_equal(dates, fit.coefficient_dates):
        raise ValueError("fit coefficient dates do not match anchor-local dates")
    return FittedPath(
        method="anchor_local",
        parameterization="anchor",
        tensor=tensor,
        dates=dates,
        selected_penalty=None,
        diagnostics={
            "status": "success",
            "kind": "scale_adaptive_ridge",
            "gram_scales": [float(value) for value in ridge["gram_scales"]],
            "ridge_penalties": [
                float(value) for value in ridge["ridge_penalties"]
            ],
            "separation": [float(value) for value in separation],
        },
        runtime_seconds=time.perf_counter() - started,
    )


def anchor_prediction_rmse(
    tensor: np.ndarray,
    *,
    fit: FitInputs,
    position: int,
) -> float:
    """Score one anchor coefficient at its observed estimation topology."""
    coefficient = np.asarray(tensor, dtype=float)
    if coefficient.ndim != 3 or not 0 <= position < coefficient.shape[2]:
        raise ValueError("position must index the coefficient path")
    if coefficient.shape[:2] != (fit.predictors.shape[1], 2 * fit.predictors.shape[1]):
        raise ValueError("coefficient has incompatible anchor dimensions")
    date = int(fit.coefficient_dates[position])
    n = fit.predictors.shape[1]
    m_ref = coefficient[:, :n, position]
    b = coefficient[:, n:, position]
    delta_topology = fit.topology[date] - fit.w_ref
    observed = m_ref + b @ delta_topology
    residual = fit.outcomes[date] - observed @ fit.predictors[date]
    return float(np.sqrt(np.mean(np.square(residual))))


def _positions(
    values: tuple[int, ...] | list[int] | range,
    *,
    total: int,
    label: str,
) -> tuple[int, ...]:
    positions = tuple(values)
    if not positions or any(
        not isinstance(value, (int, np.integer)) for value in positions
    ):
        raise ValueError(f"{label} must be a non-empty integer sequence")
    normalized = tuple(int(value) for value in positions)
    if any(value < 1 or value >= total for value in normalized):
        raise ValueError(f"{label} must index prefixes with at least two dates")
    if any(right <= left for left, right in zip(normalized, normalized[1:])):
        raise ValueError(f"{label} must be strictly increasing")
    return normalized


def select_anchor_fused_penalty(
    local_tensor: np.ndarray,
    *,
    fit: FitInputs,
    validation_positions: tuple[int, ...] | list[int] | range,
    config: R006EConfig,
) -> tuple[float, dict[str, object]]:
    """Select fused-TV strength using a separate strict fit for each prefix."""
    local = _validate_local_tensor(local_tensor, fit=fit, config=config)
    positions = _positions(
        validation_positions, total=local.shape[2], label="validation_positions"
    )
    fused_config = _r006c_fused_config(config)
    candidate_scores: dict[str, float] = {}
    candidate_date_scores: dict[str, list[float]] = {}
    candidates: list[tuple[float, float]] = []
    for raw_penalty in FUSED_PENALTIES:
        penalty = float(raw_penalty)
        date_scores: list[float] = []
        for position in positions:
            reconstructed, diagnostics = _fused_reconstruct(
                local[:, :, : position + 1], penalty, fused_config
            )
            if not bool(diagnostics.get("converged", False)):
                raise RuntimeError(
                    f"fused-TV did not converge for penalty {penalty} "
                    f"at validation position {position}"
                )
            score = anchor_prediction_rmse(
                reconstructed, fit=fit, position=position
            )
            if not math.isfinite(score):
                raise RuntimeError("fused-TV validation produced a non-finite score")
            date_scores.append(score)
        pooled_rmse = float(np.sqrt(np.mean(np.square(date_scores))))
        key = f"{penalty:.12g}"
        candidate_scores[key] = pooled_rmse
        candidate_date_scores[key] = date_scores
        candidates.append((pooled_rmse, penalty))
    _, selected = min(candidates, key=lambda item: (item[0], item[1]))
    return selected, {
        "candidate_scores": candidate_scores,
        "candidate_date_scores": candidate_date_scores,
        "validation_positions": positions,
        "validation_count": len(positions),
        "strict_rolling_prefix": True,
    }


def fit_anchor_fused_evaluation(
    local_tensor: np.ndarray,
    *,
    dates: np.ndarray,
    evaluation_positions: tuple[int, ...] | list[int] | range,
    selected_penalty: float,
    config: R006EConfig,
    selection_diagnostics: Mapping[str, object],
) -> FittedPath:
    """Refit fused-TV separately through every evaluation position."""
    started = time.perf_counter()
    local = _validate_local_tensor(local_tensor, fit=None, config=config)
    all_dates = np.asarray(dates)
    if all_dates.shape != (local.shape[2],):
        raise ValueError("dates must align with the anchor-local path")
    positions = _positions(
        evaluation_positions, total=local.shape[2], label="evaluation_positions"
    )
    fused_config = _r006c_fused_config(config)
    final_slices: list[np.ndarray] = []
    iterations: list[int] = []
    for position in positions:
        reconstructed, diagnostics = _fused_reconstruct(
            local[:, :, : position + 1], selected_penalty, fused_config
        )
        if not bool(diagnostics.get("converged", False)):
            raise RuntimeError(
                f"fused-TV did not converge at evaluation position {position}"
            )
        final_slices.append(reconstructed[:, :, -1])
        iterations.append(int(diagnostics.get("iterations", 0)))
    return FittedPath(
        method="anchor_fused_tv",
        parameterization="anchor",
        tensor=np.stack(final_slices, axis=2),
        dates=all_dates[list(positions)],
        selected_penalty=selected_penalty,
        diagnostics={
            **dict(selection_diagnostics),
            "status": "success",
            "evaluation_positions": positions,
            "evaluation_dates": [int(all_dates[position]) for position in positions],
            "evaluation_count": len(positions),
            "evaluation_iterations": iterations,
            "prefixwise_evaluation": True,
        },
        runtime_seconds=time.perf_counter() - started,
    )


def fit_anchor_split_tucker_evaluation(
    local_tensor: np.ndarray,
    *,
    dates: np.ndarray,
    evaluation_positions: tuple[int, ...] | list[int] | range,
    config: R006EConfig,
) -> FittedPath:
    """Reconstruct M_ref and B separately on every evaluation prefix."""
    started = time.perf_counter()
    local = _validate_local_tensor(local_tensor, fit=None, config=config)
    all_dates = np.asarray(dates)
    if all_dates.shape != (local.shape[2],):
        raise ValueError("dates must align with the anchor-local path")
    positions = _positions(
        evaluation_positions, total=local.shape[2], label="evaluation_positions"
    )
    final_slices: list[np.ndarray] = []
    for position in positions:
        prefix = local[:, :, : position + 1]
        m_ref = _tucker_reconstruct(
            prefix[:, : config.n, :], SPLIT_TUCKER_RANK
        )
        b = _tucker_reconstruct(
            prefix[:, config.n :, :], SPLIT_TUCKER_RANK
        )
        final_slices.append(np.concatenate([m_ref[:, :, -1], b[:, :, -1]], axis=1))
    return FittedPath(
        method="anchor_split_tucker333",
        parameterization="anchor",
        tensor=np.stack(final_slices, axis=2),
        dates=all_dates[list(positions)],
        selected_penalty=None,
        diagnostics={
            "status": "success",
            "split_rank": SPLIT_TUCKER_RANK,
            "split_components": ["M_ref", "B"],
            "evaluation_positions": positions,
            "evaluation_dates": [int(all_dates[position]) for position in positions],
            "evaluation_count": len(positions),
            "prefixwise_evaluation": True,
        },
        runtime_seconds=time.perf_counter() - started,
    )


def _failure_path(
    method: str,
    *,
    config: R006EConfig,
    dates: np.ndarray,
    error: Exception,
    runtime_seconds: float,
    method_seed: int,
) -> FittedPath:
    intended_dates = np.asarray(dates, dtype=int)
    expected_shape = (config.n, 2 * config.n, len(intended_dates))
    diagnostics: dict[str, object] = {
        "status": "failure",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "method_seed": method_seed,
        "intended_dates": [int(value) for value in intended_dates],
        "intended_count": len(intended_dates),
        "expected_tensor_shape": list(expected_shape),
    }
    if method != "anchor_local":
        diagnostics.update(
            {
                "validation_positions": tuple(range(60, 84)),
                "validation_count": 24,
                "evaluation_positions": tuple(range(84, 120)),
                "evaluation_dates": [int(value) for value in intended_dates],
                "evaluation_count": 36,
            }
        )
    return FittedPath(
        method=method,
        parameterization="anchor",
        tensor=np.zeros((config.n, 2 * config.n, 0)),
        dates=np.asarray([], dtype=int),
        selected_penalty=None,
        diagnostics=diagnostics,
        runtime_seconds=max(float(runtime_seconds), 0.0),
    )


def _attach_method_seed(path: FittedPath, method_seed: int) -> FittedPath:
    return FittedPath(
        method=path.method,
        parameterization=path.parameterization,
        tensor=path.tensor,
        dates=path.dates,
        selected_penalty=path.selected_penalty,
        diagnostics={**dict(path.diagnostics), "method_seed": method_seed},
        runtime_seconds=path.runtime_seconds,
    )


def fit_required_comparators(
    fit: FitInputs,
    *,
    config: R006EConfig,
    method_seed: int,
) -> dict[str, FittedPath]:
    if not isinstance(fit, FitInputs) or not isinstance(config, R006EConfig):
        raise TypeError("fit and config must be frozen R006e protocol records")
    if not isinstance(method_seed, int) or isinstance(method_seed, bool):
        raise TypeError("method_seed must be an integer")
    if fit.predictors.shape != (config.t_len, config.n):
        raise ValueError("fit dimensions do not match config")
    expected_dates = np.arange(config.window, config.t_len, dtype=int)
    if not np.array_equal(fit.coefficient_dates, expected_dates):
        raise ValueError("fit must contain the frozen 120 coefficient dates")

    methods: dict[str, FittedPath] = {}
    evaluation_positions = tuple(range(84, 120))
    evaluation_dates = fit.coefficient_dates[list(evaluation_positions)]

    started = time.perf_counter()
    try:
        local = _attach_method_seed(fit_anchor_local(fit, config=config), method_seed)
        methods["anchor_local"] = local
    except Exception as error:
        elapsed = time.perf_counter() - started
        for name in REQUIRED_COMPARATORS:
            dates = fit.coefficient_dates if name == "anchor_local" else evaluation_dates
            methods[name] = _failure_path(
                name,
                config=config,
                dates=dates,
                error=error,
                runtime_seconds=elapsed,
                method_seed=method_seed,
            )
        return methods

    started = time.perf_counter()
    try:
        penalty, selection = select_anchor_fused_penalty(
            local.tensor,
            fit=fit,
            validation_positions=tuple(range(60, 84)),
            config=config,
        )
        fused = fit_anchor_fused_evaluation(
            local.tensor,
            dates=local.dates,
            evaluation_positions=evaluation_positions,
            selected_penalty=penalty,
            config=config,
            selection_diagnostics=selection,
        )
        methods["anchor_fused_tv"] = _attach_method_seed(fused, method_seed)
    except Exception as error:
        methods["anchor_fused_tv"] = _failure_path(
            "anchor_fused_tv",
            config=config,
            dates=evaluation_dates,
            error=error,
            runtime_seconds=time.perf_counter() - started,
            method_seed=method_seed,
        )

    started = time.perf_counter()
    try:
        tucker = fit_anchor_split_tucker_evaluation(
            local.tensor,
            dates=local.dates,
            evaluation_positions=evaluation_positions,
            config=config,
        )
        methods["anchor_split_tucker333"] = _attach_method_seed(
            tucker, method_seed
        )
    except Exception as error:
        methods["anchor_split_tucker333"] = _failure_path(
            "anchor_split_tucker333",
            config=config,
            dates=evaluation_dates,
            error=error,
            runtime_seconds=time.perf_counter() - started,
            method_seed=method_seed,
        )

    if tuple(methods) != REQUIRED_COMPARATORS:
        raise RuntimeError("required comparator order differs from the frozen protocol")
    return methods
