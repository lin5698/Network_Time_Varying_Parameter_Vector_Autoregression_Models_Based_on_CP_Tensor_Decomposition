"""Outcome-free supported-endpoint construction for R006e."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from scripts.experiments.r006d_endpoint_support import (
    DesignSupportPath,
    build_design_support_path,
    evaluate_query_path,
    generate_family_pool,
)
from scripts.experiments.r006e_native_protocol import FitInputs, R006EConfig


CALIBRATION_DATES = tuple(range(80, 140))
PROSPECTIVE_DATES = tuple(range(140, 200))
FAMILY_POOL_SIZE = 64
CONSTRUCTION_STATUSES = frozenset({"CONSTRUCTION_PASS", "CONSTRUCTION_FAIL"})
CONSTRUCTION_FAILURE_REASONS = frozenset({
    "interp_not_supported_in_calibration",
    "interp_lost_support_prospectively",
    "no_supported_family_candidate",
    "family_lost_support_prospectively",
})
FINITE_QUERY_AVAILABILITY_STATUSES = frozenset({
    "available", "calibration_unsupported", "lost_support",
})


def _readonly_copy(value: np.ndarray, *, dtype: object | None = None) -> np.ndarray:
    contiguous = np.ascontiguousarray(np.asarray(value, dtype=dtype))
    return np.frombuffer(
        contiguous.tobytes(), dtype=contiguous.dtype
    ).reshape(contiguous.shape)


@dataclass(frozen=True)
class QuerySupportPath:
    dates: np.ndarray
    chi: np.ndarray
    amplification: np.ndarray
    alpha: np.ndarray
    retained_rank: np.ndarray
    condition_number: np.ndarray
    singular_values: tuple[np.ndarray, ...]

    def __post_init__(self) -> None:
        dates = np.asarray(self.dates)
        if dates.ndim != 1 or dates.size == 0:
            raise ValueError("dates must be a non-empty vector")
        if not np.issubdtype(dates.dtype, np.integer):
            raise ValueError("dates must contain integers")
        if np.any(dates[1:] <= dates[:-1]):
            raise ValueError("dates must be strictly increasing")

        count = dates.size
        vectors: dict[str, np.ndarray] = {}
        for name in (
            "chi",
            "amplification",
            "alpha",
            "retained_rank",
            "condition_number",
        ):
            value = np.asarray(getattr(self, name))
            if value.shape != (count,):
                raise ValueError(f"{name} must align with dates")
            if not np.all(np.isfinite(value)):
                raise ValueError(f"{name} must be finite")
            vectors[name] = value

        ranks = vectors["retained_rank"]
        if not np.issubdtype(ranks.dtype, np.integer) or np.any(ranks < 0):
            raise ValueError("retained_rank must contain non-negative integers")
        for name in ("chi", "amplification", "condition_number"):
            if np.any(vectors[name] < 0.0):
                raise ValueError(f"{name} must be non-negative")
        if np.any(vectors["alpha"] <= 0.0):
            raise ValueError("alpha must be positive")

        spectra = tuple(np.asarray(value) for value in self.singular_values)
        if len(spectra) != count:
            raise ValueError("singular_values must align with dates")
        for rank, spectrum in zip(ranks, spectra):
            if spectrum.ndim != 1 or not np.all(np.isfinite(spectrum)):
                raise ValueError("singular spectra must be finite vectors")
            if np.any(spectrum < 0.0) or int(rank) > spectrum.size:
                raise ValueError("singular spectra and retained ranks disagree")

        object.__setattr__(self, "dates", _readonly_copy(dates))
        for name, value in vectors.items():
            object.__setattr__(self, name, _readonly_copy(value))
        object.__setattr__(
            self,
            "singular_values",
            tuple(_readonly_copy(value, dtype=float) for value in spectra),
        )

    @property
    def maximum_chi(self) -> float:
        return float(np.max(self.chi))


def _path_json_dict(path: QuerySupportPath) -> dict[str, object]:
    return {
        "dates": path.dates.tolist(),
        "chi": path.chi.tolist(),
        "maximum_chi": path.maximum_chi,
        "amplification": path.amplification.tolist(),
        "alpha": path.alpha.tolist(),
        "retained_rank": path.retained_rank.tolist(),
        "condition_number": path.condition_number.tolist(),
        "singular_values": [values.tolist() for values in path.singular_values],
    }


@dataclass(frozen=True)
class FamilyCandidateRecord:
    index: int
    endpoint: np.ndarray
    path: QuerySupportPath

    def __post_init__(self) -> None:
        if not isinstance(self.index, (int, np.integer)) or int(self.index) < 0:
            raise ValueError("candidate index must be a non-negative integer")
        endpoint = np.asarray(self.endpoint, dtype=float)
        if (
            endpoint.ndim != 2
            or endpoint.shape[0] != endpoint.shape[1]
            or not np.all(np.isfinite(endpoint))
        ):
            raise ValueError("candidate endpoint must be a finite square matrix")
        if not isinstance(self.path, QuerySupportPath):
            raise ValueError("candidate path must be a QuerySupportPath")
        object.__setattr__(self, "index", int(self.index))
        object.__setattr__(self, "endpoint", _readonly_copy(endpoint))

    def to_json_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "endpoint": self.endpoint.tolist(),
            **_path_json_dict(self.path),
        }


def _paths_equal(left: QuerySupportPath, right: QuerySupportPath) -> bool:
    return all(
        np.array_equal(getattr(left, name), getattr(right, name))
        for name in (
            "dates",
            "chi",
            "amplification",
            "alpha",
            "retained_rank",
            "condition_number",
        )
    ) and all(
        np.array_equal(a, b)
        for a, b in zip(left.singular_values, right.singular_values)
    ) and len(left.singular_values) == len(right.singular_values)


def _require_path_dates(
    path: QuerySupportPath, expected: tuple[int, ...], *, name: str
) -> None:
    if not np.array_equal(path.dates, np.asarray(expected, dtype=int)):
        raise ValueError(f"{name} has invalid dates")


@dataclass(frozen=True)
class EndpointConstruction:
    status: str
    failure_reasons: tuple[str, ...]
    w_alt_interp: np.ndarray
    w_alt_family: np.ndarray | None
    family_selected_index: int | None
    interp_calibration: QuerySupportPath
    interp_prospective: QuerySupportPath
    family_calibration: QuerySupportPath | None
    family_prospective: QuerySupportPath | None
    family_candidates: tuple[FamilyCandidateRecord, ...]

    def __post_init__(self) -> None:
        if self.status not in CONSTRUCTION_STATUSES:
            raise ValueError("invalid construction status")
        failures = tuple(self.failure_reasons)
        if any(not isinstance(reason, str) or not reason for reason in failures):
            raise ValueError("failure reasons must be non-empty strings")
        if not set(failures) <= CONSTRUCTION_FAILURE_REASONS:
            raise ValueError("invalid construction failure reason")
        if (self.status == "CONSTRUCTION_PASS") != (not failures):
            raise ValueError("status and failure reasons disagree")
        _require_path_dates(
            self.interp_calibration,
            CALIBRATION_DATES,
            name="interp_calibration",
        )
        _require_path_dates(
            self.interp_prospective,
            PROSPECTIVE_DATES,
            name="interp_prospective",
        )

        interp = np.asarray(self.w_alt_interp, dtype=float)
        if interp.ndim != 2 or interp.shape[0] != interp.shape[1]:
            raise ValueError("interpolation endpoint must be square")
        if not np.all(np.isfinite(interp)):
            raise ValueError("interpolation endpoint must be finite")
        family = None
        if self.w_alt_family is not None:
            family = np.asarray(self.w_alt_family, dtype=float)
            if family.shape != interp.shape or not np.all(np.isfinite(family)):
                raise ValueError("family endpoint must be finite and aligned")

        selected = self.family_selected_index
        if selected is not None and (
            not isinstance(selected, (int, np.integer))
            or not 0 <= int(selected) < FAMILY_POOL_SIZE
        ):
            raise ValueError("family_selected_index must lie in [0, 63]")
        if (selected is None) != (family is None):
            raise ValueError("selected family index and endpoint disagree")
        if (self.family_calibration is None) != (selected is None):
            raise ValueError("selected family index and calibration path disagree")
        if (self.family_prospective is None) != (selected is None):
            raise ValueError("selected family index and prospective path disagree")

        records = tuple(self.family_candidates)
        if len(records) != FAMILY_POOL_SIZE or any(
            not isinstance(record, FamilyCandidateRecord)
            for record in records
        ):
            raise ValueError("family_candidates must contain exactly 64 records")
        if tuple(record.index for record in records) != tuple(
            range(FAMILY_POOL_SIZE)
        ):
            raise ValueError("family candidate indices must be exactly 0..63")
        for record in records:
            if record.endpoint.shape != interp.shape:
                raise ValueError("candidate endpoints must align with interpolation")
            _require_path_dates(
                record.path,
                CALIBRATION_DATES,
                name=f"family_candidates[{record.index}]",
            )
        if selected is not None:
            selected_record = records[int(selected)]
            family_calibration = self.family_calibration
            family_prospective = self.family_prospective
            if (
                family is None
                or family_calibration is None
                or family_prospective is None
            ):
                raise ValueError("selected family diagnostics are incomplete")
            if not np.array_equal(family, selected_record.endpoint):
                raise ValueError("selected endpoint disagrees with candidate record")
            if not _paths_equal(family_calibration, selected_record.path):
                raise ValueError("selected calibration path disagrees with candidate")
            _require_path_dates(
                family_prospective,
                PROSPECTIVE_DATES,
                name="family_prospective",
            )
        object.__setattr__(self, "failure_reasons", failures)
        object.__setattr__(self, "w_alt_interp", _readonly_copy(interp))
        object.__setattr__(
            self,
            "w_alt_family",
            None if family is None else _readonly_copy(family),
        )
        object.__setattr__(
            self, "family_selected_index", None if selected is None else int(selected)
        )
        object.__setattr__(self, "family_candidates", records)


def query_amplification(
    gram: np.ndarray, projector: np.ndarray, delta_w: np.ndarray
) -> float:
    gram_matrix = np.asarray(gram, dtype=float)
    retained_projector = np.asarray(projector, dtype=float)
    delta = np.asarray(delta_w, dtype=float)
    if gram_matrix.ndim != 2 or gram_matrix.shape[0] != gram_matrix.shape[1]:
        raise ValueError("gram must be square")
    if retained_projector.shape != gram_matrix.shape:
        raise ValueError("projector must align with gram")
    if delta.ndim != 2 or delta.shape[0] != gram_matrix.shape[0]:
        raise ValueError("delta_w must align with gram")
    if not all(
        np.all(np.isfinite(value))
        for value in (gram_matrix, retained_projector, delta)
    ):
        raise ValueError("amplification inputs must be finite")

    retained_inverse = (
        retained_projector
        @ np.linalg.pinv(gram_matrix)
        @ retained_projector
    )
    variance_mass = float(np.trace(delta.T @ retained_inverse @ delta))
    value = float(
        np.sqrt(max(variance_mass, 0.0))
        / max(float(np.linalg.norm(delta)), 1e-12)
    )
    if not np.isfinite(value):
        raise ValueError("query amplification must be finite")
    return value


def first_supported(
    maximum_chi: Sequence[float], *, threshold: float
) -> int | None:
    if not np.isfinite(threshold) or threshold < 0.0:
        raise ValueError("threshold must be finite and non-negative")
    for index, value in enumerate(maximum_chi):
        numeric = float(value)
        if np.isfinite(numeric) and numeric <= threshold:
            return index
    return None


def availability_status(
    *, calibration_max: float, prospective_max: float, threshold: float
) -> str:
    values = np.asarray([calibration_max, prospective_max, threshold], dtype=float)
    if not np.all(np.isfinite(values)) or threshold < 0.0:
        return "nonfinite"
    if calibration_max > threshold:
        return "calibration_unsupported"
    if prospective_max > threshold:
        return "lost_support"
    return "available"


def _residual_grams(
    fit: FitInputs, dates: np.ndarray, *, window: int
) -> tuple[np.ndarray, ...]:
    grams = []
    for date in dates:
        direct = np.asarray(fit.predictors[date - window : date], dtype=float)
        delta_topology = (
            np.asarray(fit.topology[date - window : date], dtype=float)
            - np.asarray(fit.w_ref, dtype=float)[None, :, :]
        )
        exposure = np.einsum(
            "tij,tj->ti", delta_topology, direct, optimize=True
        )
        coefficients, *_ = np.linalg.lstsq(direct, exposure, rcond=None)
        residual = exposure - direct @ coefficients
        grams.append(residual.T @ residual)
    return tuple(grams)


def _condition_number(spectrum: np.ndarray, tau: float) -> float:
    absolute = np.abs(np.asarray(spectrum, dtype=float))
    retained = absolute[absolute >= float(tau)]
    if retained.size == 0:
        return 0.0
    return float(np.max(absolute) / np.min(retained))


def _query_path(
    design: DesignSupportPath,
    grams: tuple[np.ndarray, ...],
    w_ref: np.ndarray,
    endpoint: np.ndarray,
) -> QuerySupportPath:
    base = evaluate_query_path(design, w_ref, endpoint)
    if len(grams) != len(base.dates):
        raise ValueError("gram path must align with support dates")
    delta = np.asarray(endpoint, dtype=float) - np.asarray(w_ref, dtype=float)
    amplification = np.asarray(
        [
            query_amplification(gram, projector, delta)
            for gram, projector in zip(grams, design.projectors)
        ],
        dtype=float,
    )
    spectra = tuple(np.abs(np.asarray(values, dtype=float)) for values in base.singular_values)
    condition = np.asarray(
        [
            _condition_number(values, tau)
            for values, tau in zip(spectra, design.tau)
        ],
        dtype=float,
    )
    return QuerySupportPath(
        dates=base.dates,
        chi=base.chi,
        amplification=amplification,
        alpha=1.0 / np.maximum(amplification, 1e-12),
        retained_rank=base.retained_rank,
        condition_number=condition,
        singular_values=spectra,
    )


def _validate_inputs(
    fit: FitInputs, w_alt_interp: np.ndarray, config: R006EConfig
) -> np.ndarray:
    if config.t_len != 200 or config.window != 80:
        raise ValueError("R006e support construction requires T=200 and window=80")
    if config.family_pool_size != FAMILY_POOL_SIZE:
        raise ValueError("R006e support construction requires exactly 64 candidates")
    if fit.predictors.shape != (config.t_len, config.n):
        raise ValueError("fit predictors do not match config")
    if fit.topology.shape != (config.t_len, config.n, config.n):
        raise ValueError("fit topology does not match config")
    if fit.w_ref.shape != (config.n, config.n):
        raise ValueError("fit reference topology does not match config")
    expected_dates = np.arange(config.window, config.t_len, dtype=int)
    if not np.array_equal(fit.coefficient_dates, expected_dates):
        raise ValueError("fit coefficient_dates must be exactly 80..199")
    endpoint = np.asarray(w_alt_interp, dtype=float)
    if endpoint.shape != fit.w_ref.shape or not np.all(np.isfinite(endpoint)):
        raise ValueError("interpolation endpoint must be finite and aligned")
    for name in ("predictors", "topology", "w_ref"):
        if not np.all(np.isfinite(getattr(fit, name))):
            raise ValueError(f"fit {name} must be finite")
    return endpoint


def construct_supported_endpoints(
    fit: FitInputs,
    *,
    w_alt_interp: np.ndarray,
    family_seed: int,
    config: R006EConfig,
) -> EndpointConstruction:
    endpoint = _validate_inputs(fit, w_alt_interp, config)
    calibration_dates = np.asarray(CALIBRATION_DATES, dtype=int)
    prospective_dates = np.asarray(PROSPECTIVE_DATES, dtype=int)
    calibration_design = build_design_support_path(
        fit.predictors,
        fit.topology,
        fit.w_ref,
        calibration_dates,
        window=config.window,
        kappa_max=config.kappa_max,
        absolute_floor=config.support_floor,
    )
    prospective_design = build_design_support_path(
        fit.predictors,
        fit.topology,
        fit.w_ref,
        prospective_dates,
        window=config.window,
        kappa_max=config.kappa_max,
        absolute_floor=config.support_floor,
    )
    calibration_grams = _residual_grams(
        fit, calibration_dates, window=config.window
    )
    prospective_grams = _residual_grams(
        fit, prospective_dates, window=config.window
    )

    interp_calibration = _query_path(
        calibration_design, calibration_grams, fit.w_ref, endpoint
    )
    interp_prospective = _query_path(
        prospective_design, prospective_grams, fit.w_ref, endpoint
    )

    family_pool = generate_family_pool(
        n=config.n, size=FAMILY_POOL_SIZE, seed=family_seed
    )
    family_paths = tuple(
        _query_path(calibration_design, calibration_grams, fit.w_ref, candidate)
        for candidate in family_pool
    )
    family_index = first_supported(
        [path.maximum_chi for path in family_paths],
        threshold=config.support_threshold,
    )
    family_endpoint = (
        None if family_index is None else family_pool[family_index]
    )
    family_calibration = (
        None if family_index is None else family_paths[family_index]
    )
    family_prospective = (
        None
        if family_endpoint is None
        else _query_path(
            prospective_design,
            prospective_grams,
            fit.w_ref,
            family_endpoint,
        )
    )

    failures: list[str] = []
    if interp_calibration.maximum_chi > config.support_threshold:
        failures.append("interp_not_supported_in_calibration")
    elif interp_prospective.maximum_chi > config.support_threshold:
        failures.append("interp_lost_support_prospectively")
    if family_index is None:
        failures.append("no_supported_family_candidate")
    elif (
        family_prospective is not None
        and family_prospective.maximum_chi > config.support_threshold
    ):
        failures.append("family_lost_support_prospectively")

    return EndpointConstruction(
        status="CONSTRUCTION_PASS" if not failures else "CONSTRUCTION_FAIL",
        failure_reasons=tuple(failures),
        w_alt_interp=endpoint,
        w_alt_family=family_endpoint,
        family_selected_index=family_index,
        interp_calibration=interp_calibration,
        interp_prospective=interp_prospective,
        family_calibration=family_calibration,
        family_prospective=family_prospective,
        family_candidates=tuple(
            FamilyCandidateRecord(index=index, endpoint=candidate, path=path)
            for index, (candidate, path) in enumerate(
                zip(family_pool, family_paths)
            )
        ),
    )
