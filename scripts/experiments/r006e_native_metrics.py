"""Truth-isolated endpoint evaluation for the frozen R006e protocol."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence

import numpy as np

from scripts.experiments.high_impact_metrics import evaluate_response_pair
from scripts.experiments.r006e_endpoint_support import (
    CONSTRUCTION_FAILURE_REASONS,
    CONSTRUCTION_STATUSES,
    FINITE_QUERY_AVAILABILITY_STATUSES,
    FAMILY_POOL_SIZE,
    EndpointConstruction,
    QuerySupportPath,
    availability_status,
)
from scripts.experiments.r006e_native_estimators import FittedPath, fit_path_digest
from scripts.experiments.r006e_native_protocol import (
    FitInputs,
    R006EConfig,
    TruthBundle,
)


EVALUATION_DATE_COUNT = 36
EVALUATION_DATES = np.arange(164, 200, dtype=int)
ENDPOINT_METRICS = (
    "operator_relative_error_mean",
    "operator_absolute_error_mean",
    "raw_response_error_mean",
    "response_zero_ratio_mean",
    "stability_qualified_error_mean",
    "stability_qualified_rate",
    "projected_sensitivity_error_mean",
    "estimated_spectral_radius_mean",
    "estimated_instability_rate",
    "raw_date_count",
    "evaluation_dates",
)
ENDPOINT_NAMES = ("w_ref", "w_alt_interp", "w_alt_family")
BASE_ROW_FIELDS = (
    "method", "fit_sha256", "parameterization", "fit_success", "scorable",
    "selected_hyperparameter", "at_least_one_converged_start",
    "selected_objective_trace_nonincreasing", "failure_code", "failure_reason",
    "runtime_seconds", "fit_diagnostics_json", "endpoint_construction_status",
    "endpoint_failure_reasons_json", "family_selected_index",
)
MECHANISM_AND_EVALUATION_FIELDS = (
    "observed_topology_prediction_rmse", "m_ref_relative_error_mean",
    "b_relative_error_mean", "topology_slope_interp_error_mean",
    "topology_slope_family_error_mean", "estimated_instability_rate",
    "evaluation_date_start", "evaluation_date_end", "evaluation_dates",
)
SUPPORT_SUFFIXES = (
    "calibration_chi_max", "evaluation_chi_mean", "evaluation_chi_max",
    "evaluation_amplification_mean", "evaluation_amplification_max",
    "evaluation_alpha_mean", "evaluation_retained_rank_min",
    "evaluation_condition_number_max",
)
EVALUATOR_ROW_FIELDS = BASE_ROW_FIELDS + tuple(
    field
    for endpoint in ENDPOINT_NAMES
    for field in (
        f"{endpoint}_available", f"{endpoint}_availability_status",
        *(f"{endpoint}_{metric}" for metric in ENDPOINT_METRICS),
    )
) + MECHANISM_AND_EVALUATION_FIELDS + tuple(
    f"{endpoint}_{suffix}"
    for endpoint in ("w_alt_interp", "w_alt_family")
    for suffix in SUPPORT_SUFFIXES
)
EVALUATOR_STRING_FIELDS = frozenset({
    "method", "fit_sha256", "parameterization", "failure_code", "failure_reason",
    "fit_diagnostics_json", "endpoint_construction_status",
    "endpoint_failure_reasons_json",
    *(f"{endpoint}_availability_status" for endpoint in ENDPOINT_NAMES),
})
EVALUATOR_INTEGER_FIELDS = frozenset({
    "fit_success", "scorable", "at_least_one_converged_start",
    "selected_objective_trace_nonincreasing", "family_selected_index",
    "evaluation_date_start", "evaluation_date_end", "evaluation_dates",
    *(f"{endpoint}_available" for endpoint in ENDPOINT_NAMES),
    *(f"{endpoint}_{metric}" for endpoint in ENDPOINT_NAMES for metric in ("raw_date_count", "evaluation_dates")),
    *(f"{endpoint}_evaluation_retained_rank_min" for endpoint in ("w_alt_interp", "w_alt_family")),
})
EVALUATOR_NULLABLE_FIELDS = frozenset({
    "selected_hyperparameter", "failure_code", "failure_reason",
    "family_selected_index", *MECHANISM_AND_EVALUATION_FIELDS[:-3],
    *(f"{endpoint}_{metric}" for endpoint in ENDPOINT_NAMES for metric in ENDPOINT_METRICS),
    *(f"w_alt_family_{suffix}" for suffix in SUPPORT_SUFFIXES),
})
EVALUATOR_PARAMETERIZATION = "anchor"
EVALUATOR_NUMERICAL_FAILURE_CODE = "EVALUATION_NUMERICAL_FAIL"
EVALUATOR_FAMILY_AVAILABILITY_STATUSES = (
    FINITE_QUERY_AVAILABILITY_STATUSES | {"unavailable"}
)


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"nonstandard JSON constant: {value}")


def _require_finite_json_tree(value: object, *, path: str) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite float")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_finite_json_tree(item, path=f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} contains a non-string object key")
            _require_finite_json_tree(item, path=f"{path}.{key}")
        return
    raise ValueError(f"{path} contains a non-JSON value")


def validate_evaluator_row_contract(row: Mapping[str, object]) -> None:
    """Validate semantic fields that CSV primitive types cannot express."""
    digest = row.get("fit_sha256")
    if (
        type(digest) is not str
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("fit_sha256 must be exactly 64 lowercase hex characters")
    if row.get("parameterization") != EVALUATOR_PARAMETERIZATION:
        raise ValueError("parameterization must be exactly anchor")
    try:
        diagnostics = json.loads(
            row.get("fit_diagnostics_json", ""),
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("fit_diagnostics_json must encode a JSON object") from error
    if type(diagnostics) is not dict:
        raise ValueError("fit_diagnostics_json must encode a JSON object")
    _require_finite_json_tree(diagnostics, path="fit_diagnostics_json")
    try:
        failure_reasons = json.loads(
            row.get("endpoint_failure_reasons_json", ""),
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "endpoint_failure_reasons_json must encode a JSON string array"
        ) from error
    if type(failure_reasons) is not list or any(
        type(reason) is not str or not reason for reason in failure_reasons
    ):
        raise ValueError(
            "endpoint_failure_reasons_json must encode a JSON string array"
        )
    construction_status = row.get("endpoint_construction_status")
    if construction_status not in CONSTRUCTION_STATUSES:
        raise ValueError("invalid endpoint construction status")
    if not set(failure_reasons) <= CONSTRUCTION_FAILURE_REASONS:
        raise ValueError("invalid endpoint construction failure reason")
    if (construction_status == "CONSTRUCTION_PASS") != (not failure_reasons):
        raise ValueError("endpoint construction status and failure reasons disagree")
    for endpoint in ENDPOINT_NAMES:
        available = row.get(f"{endpoint}_available")
        status = row.get(f"{endpoint}_availability_status")
        allowed_statuses = (
            EVALUATOR_FAMILY_AVAILABILITY_STATUSES
            if endpoint == "w_alt_family"
            else FINITE_QUERY_AVAILABILITY_STATUSES
        )
        if status not in allowed_statuses:
            raise ValueError(f"invalid {endpoint} availability status")
        if available != int(status == "available"):
            raise ValueError(f"{endpoint} availability flag and status disagree")
        if available == 0 and any(
            row.get(f"{endpoint}_{metric}") is not None
            for metric in ENDPOINT_METRICS
        ):
            raise ValueError(
                f"availability contract: unavailable {endpoint} has an endpoint metric"
            )
    if (
        row.get("w_ref_available") != 1
        or row.get("w_ref_availability_status") != "available"
    ):
        raise ValueError("w_ref availability must always be available")
    family_selected_index = row.get("family_selected_index")
    family_is_unavailable = (
        row.get("w_alt_family_availability_status") == "unavailable"
    )
    if (family_selected_index is None) != family_is_unavailable:
        raise ValueError("family selected index disagrees with family availability")
    if family_selected_index is not None and (
        type(family_selected_index) is not int
        or not 0 <= family_selected_index < FAMILY_POOL_SIZE
    ):
        raise ValueError("family selected index is outside the frozen pool")
    family_support_values = tuple(
        row.get(f"w_alt_family_{suffix}") for suffix in SUPPORT_SUFFIXES
    )
    if family_selected_index is not None and any(
        value is None for value in family_support_values
    ):
        raise ValueError("selected family is missing a family support summary")
    if family_selected_index is None and any(
        value is not None for value in family_support_values
    ):
        raise ValueError("absent family retains a family support summary")
    fit_success = row.get("fit_success")
    scorable = row.get("scorable")
    converged, nonincreasing, diagnostics_scorable = _fit_gate_diagnostics(
        diagnostics
    )
    if row.get("at_least_one_converged_start") != converged:
        raise ValueError("converged-start flag disagrees with fit diagnostics")
    if row.get("selected_objective_trace_nonincreasing") != nonincreasing:
        raise ValueError("objective-trace flag disagrees with fit diagnostics")
    diagnostics_status = diagnostics.get("status")
    expected_diagnostics_status = "success" if fit_success == 1 else "failure"
    if diagnostics_status != expected_diagnostics_status:
        raise ValueError("fit diagnostics status disagrees with fit_success")
    failure_code = row.get("failure_code")
    failure_reason = row.get("failure_reason")
    if (failure_code is None) != (failure_reason is None):
        raise ValueError("failure_code and failure_reason must be paired")
    if failure_code is not None and (
        type(failure_code) is not str
        or not failure_code
        or type(failure_reason) is not str
        or not failure_reason
    ):
        raise ValueError("failure_code and failure_reason must be non-empty strings")
    if fit_success == 0:
        if scorable != 0 or failure_code is None:
            raise ValueError("failed fit must be non-scorable with failure details")
        required_failure_fields = {
            "error_type", "error_message", "intended_dates",
            "intended_count", "expected_tensor_shape",
        }
        if not required_failure_fields <= set(diagnostics):
            raise ValueError("failure diagnostics are incomplete")
        intended_dates = diagnostics["intended_dates"]
        intended_count = diagnostics["intended_count"]
        expected_shape = diagnostics["expected_tensor_shape"]
        if (
            type(diagnostics["error_type"]) is not str
            or not diagnostics["error_type"]
            or type(diagnostics["error_message"]) is not str
        ):
            raise ValueError("failure diagnostics contain invalid error details")
        if (
            type(intended_dates) is not list
            or any(type(value) is not int for value in intended_dates)
        ):
            raise ValueError("failure diagnostic intended_dates must be an integer list")
        if (
            type(intended_count) is not int
            or intended_count < 0
            or intended_count != len(intended_dates)
        ):
            raise ValueError("failure diagnostic intended count disagrees")
        if (
            type(expected_shape) is not list
            or len(expected_shape) != 3
            or any(type(value) is not int or value < 0 for value in expected_shape)
            or expected_shape[2] != intended_count
        ):
            raise ValueError("failure diagnostic expected tensor shape is invalid")
        if (
            failure_code != diagnostics["error_type"]
            or failure_reason != diagnostics["error_message"]
        ):
            raise ValueError("failure row details disagree with fit diagnostics")
        if row.get("selected_hyperparameter") is not None:
            raise ValueError("failed fit cannot retain a selected hyperparameter")
    elif failure_code is not None and (
        failure_code != EVALUATOR_NUMERICAL_FAILURE_CODE or scorable != 0
    ):
        raise ValueError("successful fit failure must be numerical and non-scorable")
    expected_scorable = (
        0
        if fit_success == 0 or failure_code == EVALUATOR_NUMERICAL_FAILURE_CODE
        else diagnostics_scorable
    )
    if scorable != expected_scorable:
        raise ValueError("scorable flag disagrees with fit diagnostics")
    scientific_metric_fields = (
        tuple(
            f"{endpoint}_{metric}"
            for endpoint in ENDPOINT_NAMES
            for metric in ENDPOINT_METRICS
        )
        + MECHANISM_AND_EVALUATION_FIELDS[:-3]
    )
    if scorable == 0 and any(
        row.get(field) is not None for field in scientific_metric_fields
    ):
        raise ValueError("non-scorable row retains a scientific metric")
    if scorable == 1:
        for endpoint in ENDPOINT_NAMES:
            if row.get(f"{endpoint}_available") == 1 and any(
                row.get(f"{endpoint}_{metric}") is None
                for metric in ENDPOINT_METRICS
                if metric != "stability_qualified_error_mean"
            ):
                raise ValueError(
                    f"scorable available {endpoint} is missing an endpoint metric"
                )
        required_mechanism_fields = (
            "observed_topology_prediction_rmse",
            "m_ref_relative_error_mean",
            "b_relative_error_mean",
            "topology_slope_interp_error_mean",
            "estimated_instability_rate",
        )
        if any(row.get(field) is None for field in required_mechanism_fields):
            raise ValueError("scorable row is missing a mechanism metric")
        family_slope_is_none = row.get("topology_slope_family_error_mean") is None
        family_is_unavailable = (
            row.get("w_alt_family_availability_status") == "unavailable"
        )
        if family_slope_is_none != family_is_unavailable:
            raise ValueError("family slope nullability disagrees with availability")


class _NonfiniteScientificResultError(RuntimeError):
    """A structurally valid evaluation produced a non-finite metric."""


def anchor_query(
    m_ref: np.ndarray,
    b: np.ndarray,
    w_ref: np.ndarray,
    endpoint: np.ndarray,
) -> np.ndarray:
    """Query an anchor-parameterized operator at a topology endpoint."""
    return np.asarray(m_ref) + np.einsum(
        "...ij,...jk->...ik",
        np.asarray(b),
        np.asarray(endpoint) - np.asarray(w_ref),
        optimize=True,
    )


def evaluate_endpoint_path(
    truth: np.ndarray,
    estimate: np.ndarray,
    *,
    horizon: int,
    stability_threshold: float,
    projection_target: float,
) -> dict[str, float | int | None]:
    """Evaluate one frozen 36-date endpoint path without stability filtering."""
    true_path = np.asarray(truth, dtype=float)
    estimated_path = np.asarray(estimate, dtype=float)
    if (
        true_path.ndim != 3
        or true_path.shape != estimated_path.shape
        or true_path.shape[0] != EVALUATION_DATE_COUNT
        or true_path.shape[1] != true_path.shape[2]
    ):
        raise ValueError("endpoint paths must be aligned 36-date square matrices")
    if not np.all(np.isfinite(true_path)) or not np.all(np.isfinite(estimated_path)):
        raise _NonfiniteScientificResultError("endpoint paths must be finite")

    relative_errors: list[float] = []
    absolute_errors: list[float] = []
    raw_errors: list[float] = []
    zero_ratios: list[float] = []
    qualified_errors: list[float] = []
    projected_errors: list[float] = []
    estimated_radii: list[float] = []
    unstable_count = 0
    for truth_matrix, estimate_matrix in zip(true_path, estimated_path):
        absolute_error = float(np.linalg.norm(estimate_matrix - truth_matrix))
        absolute_errors.append(absolute_error)
        relative_errors.append(
            absolute_error / max(float(np.linalg.norm(truth_matrix)), 1e-12)
        )
        response = evaluate_response_pair(
            truth_matrix,
            estimate_matrix,
            horizon=horizon,
            stability_threshold=stability_threshold,
            projection_target=projection_target,
        )
        zero_response = evaluate_response_pair(
            truth_matrix,
            np.zeros_like(truth_matrix),
            horizon=horizon,
            stability_threshold=stability_threshold,
        )
        raw_error = float(response["raw_response_error"])
        raw_errors.append(raw_error)
        zero_ratios.append(
            raw_error
            / max(float(zero_response["raw_response_error"]), 1e-12)
        )
        qualified = response["stability_qualified_error"]
        if qualified is not None:
            qualified_errors.append(float(qualified))
        projected_errors.append(float(response["projected_sensitivity_error"]))
        radius = float(response["estimated_spectral_radius"])
        estimated_radii.append(radius)
        unstable_count += radius >= stability_threshold

    return {
        "operator_relative_error_mean": float(np.mean(relative_errors)),
        "operator_absolute_error_mean": float(np.mean(absolute_errors)),
        "raw_response_error_mean": float(np.mean(raw_errors)),
        "response_zero_ratio_mean": float(np.mean(zero_ratios)),
        "stability_qualified_error_mean": (
            float(np.mean(qualified_errors)) if qualified_errors else None
        ),
        "stability_qualified_rate": len(qualified_errors) / EVALUATION_DATE_COUNT,
        "projected_sensitivity_error_mean": float(np.mean(projected_errors)),
        "estimated_spectral_radius_mean": float(np.mean(estimated_radii)),
        "estimated_instability_rate": unstable_count / EVALUATION_DATE_COUNT,
        "raw_date_count": EVALUATION_DATE_COUNT,
        "evaluation_dates": EVALUATION_DATE_COUNT,
    }


def evaluate_method(
    fitted: FittedPath,
    *,
    fit: FitInputs,
    truth: TruthBundle,
    endpoints: EndpointConstruction,
    config: R006EConfig,
) -> dict[str, object]:
    """Evaluate one fitted R006e method at the frozen held-out endpoints."""
    _validate_evaluation_inputs(fitted, fit, truth, endpoints, config)
    positions = _evaluation_positions(fitted)
    _validate_support_contract(endpoints)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            row = _evaluate_method_scientific(
                fitted,
                fit=fit,
                truth=truth,
                endpoints=endpoints,
                config=config,
                positions=positions,
            )
            _assert_complete_evaluator_row(row)
            return row
    except (
        FloatingPointError,
        OverflowError,
        np.linalg.LinAlgError,
        _NonfiniteScientificResultError,
    ) as error:
        diagnostics = fitted.diagnostics.to_json_dict()
        row = _base_row(fitted, diagnostics)
        row.update(_construction_provenance(endpoints))
        failed = _evaluation_failure_row(row, endpoints, config, error)
        _assert_complete_evaluator_row(failed)
        return failed


def _assert_complete_evaluator_row(row: Mapping[str, object]) -> None:
    if set(row) != set(EVALUATOR_ROW_FIELDS):
        missing = sorted(set(EVALUATOR_ROW_FIELDS) - set(row))
        unexpected = sorted(set(row) - set(EVALUATOR_ROW_FIELDS))
        raise RuntimeError(
            f"evaluator row schema mismatch: missing={missing}, unexpected={unexpected}"
        )
    validate_evaluator_row_contract(row)


def _evaluate_method_scientific(
    fitted: FittedPath,
    *,
    fit: FitInputs,
    truth: TruthBundle,
    endpoints: EndpointConstruction,
    config: R006EConfig,
    positions: np.ndarray | None,
) -> dict[str, object]:
    diagnostics = fitted.diagnostics.to_json_dict()
    row = _base_row(fitted, diagnostics)
    row.update(_construction_provenance(endpoints))
    if not fitted.is_success:
        return _failure_row(row, fitted, endpoints, config)
    if row["scorable"] == 0:
        return _complete_nonscorable_row(row, endpoints, config)

    if positions is None:
        raise RuntimeError("successful fit positions were not validated")
    tensor_path = np.moveaxis(fitted.tensor[:, :, positions], 2, 0)
    estimated_m_ref = tensor_path[:, :, : config.n]
    estimated_b = tensor_path[:, :, config.n :]
    truth_m_ref = truth.m_ref[EVALUATION_DATES]
    truth_b = truth.b[EVALUATION_DATES]

    endpoint_specs: dict[str, tuple[np.ndarray, bool, str]] = {
        "w_ref": (fit.w_ref, True, "available"),
        "w_alt_interp": (
            endpoints.w_alt_interp,
            _support_status(endpoints.interp_calibration, endpoints.interp_prospective, config)
            == "available",
            _support_status(endpoints.interp_calibration, endpoints.interp_prospective, config),
        ),
    }
    family_status = "unavailable"
    if endpoints.family_calibration is not None and endpoints.family_prospective is not None:
        family_status = _support_status(
            endpoints.family_calibration, endpoints.family_prospective, config
        )
    family_endpoint = endpoints.w_alt_family
    endpoint_specs["w_alt_family"] = (
        fit.w_ref if family_endpoint is None else family_endpoint,
        family_endpoint is not None and family_status == "available",
        family_status,
    )

    instability_rates: list[float] = []
    for name, (endpoint, available, status) in endpoint_specs.items():
        row[f"{name}_available"] = int(available)
        row[f"{name}_availability_status"] = status
        if not available:
            for metric in ENDPOINT_METRICS:
                row[f"{name}_{metric}"] = None
            continue
        truth_path = anchor_query(truth_m_ref, truth_b, fit.w_ref, endpoint)
        estimate_path = anchor_query(
            estimated_m_ref, estimated_b, fit.w_ref, endpoint
        )
        values = evaluate_endpoint_path(
            truth_path,
            estimate_path,
            horizon=config.horizon,
            stability_threshold=config.stability_threshold,
            projection_target=config.projection_target,
        )
        for metric, value in values.items():
            row[f"{name}_{metric}"] = value
        instability_rates.append(float(values["estimated_instability_rate"]))

    row.update(
        _mechanism_metrics(
            estimated_m_ref,
            estimated_b,
            truth_m_ref,
            truth_b,
            fit,
            endpoints,
        )
    )
    observed_estimate = anchor_query(
        estimated_m_ref,
        estimated_b,
        fit.w_ref,
        fit.topology[EVALUATION_DATES],
    )
    predictions = np.einsum(
        "tij,tj->ti",
        observed_estimate,
        fit.predictors[EVALUATION_DATES],
        optimize=True,
    )
    row.update(
        {
            "observed_topology_prediction_rmse": float(
                np.sqrt(
                    np.mean(
                        np.square(fit.outcomes[EVALUATION_DATES] - predictions)
                    )
                )
            ),
            "estimated_instability_rate": max(instability_rates),
            "evaluation_date_start": 164,
            "evaluation_date_end": 199,
            "evaluation_dates": EVALUATION_DATE_COUNT,
        }
    )
    row.update(_support_summaries("w_alt_interp", endpoints.interp_calibration, endpoints.interp_prospective))
    if endpoints.family_calibration is not None and endpoints.family_prospective is not None:
        row.update(_support_summaries("w_alt_family", endpoints.family_calibration, endpoints.family_prospective))
    else:
        row.update(_empty_support_summaries("w_alt_family"))
    _require_flat_finite_json(row)
    return row


def _construction_provenance(
    endpoints: EndpointConstruction,
) -> dict[str, object]:
    return {
        "endpoint_construction_status": endpoints.status,
        "endpoint_failure_reasons_json": json.dumps(
            list(endpoints.failure_reasons),
            ensure_ascii=True,
            separators=(",", ":"),
        ),
        "family_selected_index": endpoints.family_selected_index,
    }


def _validate_evaluation_inputs(
    fitted: FittedPath,
    fit: FitInputs,
    truth: TruthBundle,
    endpoints: EndpointConstruction,
    config: R006EConfig,
) -> None:
    if not isinstance(fitted, FittedPath):
        raise TypeError("fitted must be a FittedPath")
    if fit.predictors.shape != (config.t_len, config.n):
        raise ValueError("fit inputs do not match config")
    if truth.m_ref.shape != (config.t_len, config.n, config.n):
        raise ValueError("truth inputs do not match config")
    if endpoints.w_alt_interp.shape != (config.n, config.n):
        raise ValueError("endpoints do not match config")
    if not np.array_equal(fit.coefficient_dates, np.arange(80, 200)):
        raise ValueError("fit coefficient dates must be exactly 80..199")
    if fitted.parameterization != "anchor":
        raise ValueError("R006e fitted paths must use anchor parameterization")
    if fitted.is_success and fitted.tensor.shape[:2] != (config.n, 2 * config.n):
        raise ValueError("fitted tensor does not match config")


def _evaluation_positions(fitted: FittedPath) -> np.ndarray | None:
    if not fitted.is_success:
        return None
    positions_by_date = {
        int(date): index for index, date in enumerate(fitted.dates)
    }
    try:
        return np.asarray(
            [positions_by_date[int(date)] for date in EVALUATION_DATES],
            dtype=int,
        )
    except KeyError as error:
        raise ValueError(
            "successful fit must contain every evaluation date 164..199"
        ) from error


def _validate_support_contract(endpoints: EndpointConstruction) -> None:
    paths = [endpoints.interp_prospective]
    if endpoints.family_prospective is not None:
        paths.append(endpoints.family_prospective)
    for path in paths:
        if not np.all(np.isin(EVALUATION_DATES, path.dates)):
            raise ValueError("support path must contain every evaluation date")


def _failure_row(
    row: dict[str, object],
    fitted: FittedPath,
    endpoints: EndpointConstruction,
    config: R006EConfig,
) -> dict[str, object]:
    diagnostics = fitted.diagnostics
    row.update(
        {
            "scorable": 0,
            "failure_code": str(diagnostics["error_type"]),
            "failure_reason": str(diagnostics["error_message"]),
        }
    )
    return _complete_nonscorable_row(row, endpoints, config)


def _evaluation_failure_row(
    row: dict[str, object],
    endpoints: EndpointConstruction,
    config: R006EConfig,
    error: Exception,
) -> dict[str, object]:
    row.update(
        {
            "scorable": 0,
            "failure_code": "EVALUATION_NUMERICAL_FAIL",
            "failure_reason": f"{type(error).__name__}: {error}",
        }
    )
    return _complete_nonscorable_row(row, endpoints, config)


def _complete_nonscorable_row(
    row: dict[str, object],
    endpoints: EndpointConstruction,
    config: R006EConfig,
) -> dict[str, object]:
    row.update(
        {
            "evaluation_date_start": 164,
            "evaluation_date_end": 199,
            "evaluation_dates": EVALUATION_DATE_COUNT,
            "observed_topology_prediction_rmse": None,
            "m_ref_relative_error_mean": None,
            "b_relative_error_mean": None,
            "topology_slope_interp_error_mean": None,
            "topology_slope_family_error_mean": None,
            "estimated_instability_rate": None,
        }
    )
    interp_status = _support_status(
        endpoints.interp_calibration, endpoints.interp_prospective, config
    )
    family_status = "unavailable"
    if endpoints.family_calibration is not None and endpoints.family_prospective is not None:
        family_status = _support_status(
            endpoints.family_calibration, endpoints.family_prospective, config
        )
    statuses = {
        "w_ref": (1, "available"),
        "w_alt_interp": (int(interp_status == "available"), interp_status),
        "w_alt_family": (
            int(endpoints.w_alt_family is not None and family_status == "available"),
            family_status,
        ),
    }
    for prefix, (available, status) in statuses.items():
        row[f"{prefix}_available"] = available
        row[f"{prefix}_availability_status"] = status
        for metric in ENDPOINT_METRICS:
            row[f"{prefix}_{metric}"] = None
    row.update(
        _support_summaries(
            "w_alt_interp",
            endpoints.interp_calibration,
            endpoints.interp_prospective,
        )
    )
    if endpoints.family_calibration is not None and endpoints.family_prospective is not None:
        row.update(
            _support_summaries(
                "w_alt_family",
                endpoints.family_calibration,
                endpoints.family_prospective,
            )
        )
    else:
        row.update(_empty_support_summaries("w_alt_family"))
    _require_flat_finite_json(row)
    return row


def _support_status(
    calibration: QuerySupportPath,
    prospective: QuerySupportPath,
    config: R006EConfig,
) -> str:
    return availability_status(
        calibration_max=calibration.maximum_chi,
        prospective_max=prospective.maximum_chi,
        threshold=config.support_threshold,
    )


def _trace_is_nonincreasing(trace: object) -> bool:
    if not isinstance(trace, Sequence) or isinstance(trace, (str, bytes)):
        return False
    try:
        values = [float(value) for value in trace]
    except (TypeError, ValueError):
        return False
    return bool(values) and all(
        math.isfinite(value) for value in values
    ) and all(right <= left + 1e-12 for left, right in zip(values, values[1:]))


def _fit_gate_diagnostics(
    diagnostics: Mapping[str, object],
) -> tuple[int, int, int]:
    raw_records = diagnostics.get("evaluation")
    has_prefix_records = raw_records is not None
    records = (
        list(raw_records)
        if isinstance(raw_records, Sequence)
        and not isinstance(raw_records, (str, bytes))
        else [diagnostics]
    )
    convergence_flags: list[bool] = []
    monotonic_flags: list[bool] = []
    selected_valid_flags: list[bool] = []
    for raw_record in records:
        if not isinstance(raw_record, Mapping):
            convergence_flags.append(False)
            monotonic_flags.append(False)
            selected_valid_flags.append(False)
            continue
        raw_starts = raw_record.get("starts", ())
        starts = (
            list(raw_starts)
            if isinstance(raw_starts, Sequence)
            and not isinstance(raw_starts, (str, bytes))
            else []
        )
        converged = [
            start
            for start in starts
            if isinstance(start, Mapping) and bool(start.get("converged", False))
        ]
        convergence_flags.append(
            bool(converged) or bool(raw_record.get("converged", False))
        )
        selected_index = raw_record.get("selected_start_index")
        selected: Mapping[str, object] | None = None
        if (
            isinstance(selected_index, int)
            and not isinstance(selected_index, bool)
            and 0 <= selected_index < len(starts)
        ):
            candidate = starts[selected_index]
            if isinstance(candidate, Mapping):
                selected = candidate
        trace = (
            selected.get(
                "objective_trace", selected.get("accepted_objective_trace")
            )
            if selected is not None
            else raw_record.get(
                "objective_trace", raw_record.get("accepted_objective_trace")
            )
        )
        selected_valid = selected is not None and bool(
            selected.get("converged", False)
        )
        selected_valid_flags.append(selected_valid)
        monotonic_flags.append(selected_valid and _trace_is_nonincreasing(trace))
    all_have_converged = bool(records) and all(convergence_flags)
    selected_traces_pass = bool(records) and all(monotonic_flags)
    diagnostics_scorable = (
        bool(records)
        and all(selected_valid_flags)
        and selected_traces_pass
        if has_prefix_records
        else True
    )
    return (
        int(all_have_converged),
        int(selected_traces_pass),
        int(diagnostics_scorable),
    )


def _base_row(fitted: FittedPath, diagnostics: Mapping[str, object]) -> dict[str, object]:
    converged, nonincreasing, diagnostics_scorable = _fit_gate_diagnostics(
        diagnostics
    )
    return {
        "method": fitted.method,
        "fit_sha256": fit_path_digest(fitted),
        "parameterization": fitted.parameterization,
        "fit_success": int(fitted.is_success),
        "scorable": int(fitted.is_success and bool(diagnostics_scorable)),
        "selected_hyperparameter": fitted.selected_penalty,
        "at_least_one_converged_start": converged,
        "selected_objective_trace_nonincreasing": nonincreasing,
        "failure_code": None,
        "failure_reason": None,
        "runtime_seconds": fitted.runtime_seconds,
        "fit_diagnostics_json": json.dumps(
            diagnostics, allow_nan=False, sort_keys=True, separators=(",", ":")
        ),
    }


def _relative_errors(estimate: np.ndarray, truth: np.ndarray) -> list[float]:
    return [
        float(np.linalg.norm(estimate_value - truth_value))
        / max(float(np.linalg.norm(truth_value)), 1e-12)
        for estimate_value, truth_value in zip(estimate, truth)
    ]


def _mechanism_metrics(
    estimated_m_ref: np.ndarray,
    estimated_b: np.ndarray,
    truth_m_ref: np.ndarray,
    truth_b: np.ndarray,
    fit: FitInputs,
    endpoints: EndpointConstruction,
) -> dict[str, object]:
    delta_b = estimated_b - truth_b
    output: dict[str, object] = {
        "m_ref_relative_error_mean": float(
            np.mean(_relative_errors(estimated_m_ref, truth_m_ref))
        ),
        "b_relative_error_mean": float(
            np.mean(_relative_errors(estimated_b, truth_b))
        ),
        "topology_slope_interp_error_mean": float(
            np.mean(
                [
                    np.linalg.norm(value @ (endpoints.w_alt_interp - fit.w_ref))
                    for value in delta_b
                ]
            )
        ),
    }
    output["topology_slope_family_error_mean"] = (
        None
        if endpoints.w_alt_family is None
        else float(
            np.mean(
                [
                    np.linalg.norm(value @ (endpoints.w_alt_family - fit.w_ref))
                    for value in delta_b
                ]
            )
        )
    )
    return output


def _support_summaries(
    prefix: str,
    calibration: QuerySupportPath,
    prospective: QuerySupportPath,
) -> dict[str, object]:
    evaluation_mask = np.isin(prospective.dates, EVALUATION_DATES)
    if int(np.sum(evaluation_mask)) != EVALUATION_DATE_COUNT:
        raise ValueError("support path must contain every evaluation date")
    return {
        f"{prefix}_calibration_chi_max": calibration.maximum_chi,
        f"{prefix}_evaluation_chi_mean": float(np.mean(prospective.chi[evaluation_mask])),
        f"{prefix}_evaluation_chi_max": float(np.max(prospective.chi[evaluation_mask])),
        f"{prefix}_evaluation_amplification_mean": float(np.mean(prospective.amplification[evaluation_mask])),
        f"{prefix}_evaluation_amplification_max": float(np.max(prospective.amplification[evaluation_mask])),
        f"{prefix}_evaluation_alpha_mean": float(np.mean(prospective.alpha[evaluation_mask])),
        f"{prefix}_evaluation_retained_rank_min": int(np.min(prospective.retained_rank[evaluation_mask])),
        f"{prefix}_evaluation_condition_number_max": float(np.max(prospective.condition_number[evaluation_mask])),
    }


def _empty_support_summaries(prefix: str) -> dict[str, object]:
    suffixes = (
        "calibration_chi_max",
        "evaluation_chi_mean",
        "evaluation_chi_max",
        "evaluation_amplification_mean",
        "evaluation_amplification_max",
        "evaluation_alpha_mean",
        "evaluation_retained_rank_min",
        "evaluation_condition_number_max",
    )
    return {f"{prefix}_{suffix}": None for suffix in suffixes}


def _require_flat_finite_json(row: Mapping[str, object]) -> None:
    for key, value in row.items():
        if not isinstance(key, str):
            raise TypeError("metric row keys must be strings")
        if value is not None and not isinstance(value, (str, bool, int, float)):
            raise TypeError(f"metric row value {key} is not a JSON primitive")
        if isinstance(value, float) and not math.isfinite(value):
            raise _NonfiniteScientificResultError(
                f"metric row value {key} is non-finite"
            )
    json.dumps(dict(row), allow_nan=False, sort_keys=True)
