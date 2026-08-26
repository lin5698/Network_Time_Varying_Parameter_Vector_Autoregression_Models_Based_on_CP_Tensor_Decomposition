"""Pure aggregation and inference gates for frozen R006e replication rows."""

from __future__ import annotations

import math
from numbers import Real
from statistics import median

import numpy as np

from scripts.experiments.r006e_native_protocol import (
    CONFIRMATION_SEEDS,
    METHODS,
    SCREENING_SEEDS,
    R006EConfig,
    primary_cells,
)


CANDIDATE = "dw_joint_tucker333"
COMPARATORS = tuple(method for method in METHODS if method != CANDIDATE)
ENDPOINTS = ("w_alt_interp", "w_alt_family")
FLOOR = 1e-12
FLAG_KEYS = (
    "scorable",
    "w_alt_interp_available",
    "w_alt_family_available",
    "at_least_one_converged_start",
    "selected_objective_trace_nonincreasing",
)


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _improvement(candidate: float, baseline: float) -> float:
    return 1.0 - candidate / max(baseline, FLOOR)


def _all_numeric_values_finite(row: dict[str, object]) -> bool:
    return all(
        not isinstance(value, (int, float)) or math.isfinite(float(value))
        for value in row.values()
    )


def _resource_fields_valid(row: dict[str, object]) -> bool:
    memory = row.get("peak_memory_bytes")
    if type(memory) is not int or memory < 0:
        return False
    if "runtime_seconds" not in row:
        return True
    runtime = row["runtime_seconds"]
    return (
        type(runtime) in (int, float)
        and math.isfinite(float(runtime))
        and float(runtime) >= 0.0
    )


def _flags_have_exact_native_type(row: dict[str, object]) -> bool:
    return all(type(row.get(key)) is int and row[key] in (0, 1) for key in FLAG_KEYS)


def _scientific_metrics_nonnegative(row: dict[str, object]) -> bool:
    metric_markers = ("norm", "loss", "error", "rmse", "ratio")
    return all(
        not any(marker in key.lower() for marker in metric_markers)
        or not isinstance(value, (int, float))
        or (not isinstance(value, bool) and float(value) >= 0.0)
        for key, value in row.items()
    )


def _screening_cell(
    indexed: dict[tuple[int, float, float, float, str], dict[str, object]],
    cell: tuple[float, float, float],
) -> dict[str, object]:
    rho, a3, eta = cell
    rows = {
        (seed, method): indexed[(seed, rho, a3, eta, method)]
        for seed in SCREENING_SEEDS
        for method in METHODS
    }
    availability = all(
        type(row.get(f"{endpoint}_available")) is int
        and row[f"{endpoint}_available"] == 1
        for row in rows.values()
        for endpoint in ENDPOINTS
    )
    numeric_keys = (
        "observed_topology_prediction_rmse",
        "w_ref_raw_response_error_mean",
        *(
            f"{endpoint}_{suffix}"
            for endpoint in ENDPOINTS
            for suffix in (
                "raw_response_error_mean",
                "operator_relative_error_mean",
                "response_zero_ratio_mean",
            )
        ),
    )
    finite_converged = all(
        _flags_have_exact_native_type(row)
        and row["scorable"] == 1
        and _all_numeric_values_finite(row)
        and _resource_fields_valid(row)
        and _scientific_metrics_nonnegative(row)
        and all(_finite_number(row.get(key)) for key in numeric_keys)
        for row in rows.values()
    ) and all(
        rows[(seed, CANDIDATE)]["at_least_one_converged_start"] == 1
        and rows[(seed, CANDIDATE)]["selected_objective_trace_nonincreasing"] == 1
        for seed in SCREENING_SEEDS
    )

    if not availability or not finite_converged:
        conditions = {
            "availability": availability,
            "finite_and_converged": finite_converged,
            "operator_relative_error": False,
            "response_zero_ratio": False,
            "paired_improvement": False,
            "joint_win_rate": False,
            "worst_endpoint_improvement": False,
            "observed_rmse_guardrail": False,
            "w_ref_guardrail": False,
        }
        return {
            "rho": rho,
            "a3": a3,
            "eta": eta,
            "passed": False,
            "conditions": conditions,
            "failed_conditions": [
                name for name, passed in conditions.items() if not passed
            ],
        }

    operator = all(
        median(
            float(rows[(seed, CANDIDATE)][f"{endpoint}_operator_relative_error_mean"])
            for seed in SCREENING_SEEDS
        )
        < 1.0
        for endpoint in ENDPOINTS
    )
    response_zero = all(
        median(
            float(rows[(seed, CANDIDATE)][f"{endpoint}_response_zero_ratio_mean"])
            for seed in SCREENING_SEEDS
        )
        < 1.0
        for endpoint in ENDPOINTS
    )
    improvements = {
        (seed, comparator, endpoint): _improvement(
            float(rows[(seed, CANDIDATE)][f"{endpoint}_raw_response_error_mean"]),
            float(rows[(seed, comparator)][f"{endpoint}_raw_response_error_mean"]),
        )
        for seed in SCREENING_SEEDS
        for comparator in COMPARATORS
        for endpoint in ENDPOINTS
    }
    paired = all(
        median(improvements[(seed, comparator, endpoint)] for seed in SCREENING_SEEDS)
        >= 0.10
        for comparator in COMPARATORS
        for endpoint in ENDPOINTS
    )
    joint = all(
        sum(
            all(
                float(rows[(seed, CANDIDATE)][f"{endpoint}_raw_response_error_mean"])
                < float(rows[(seed, comparator)][f"{endpoint}_raw_response_error_mean"])
                for comparator in COMPARATORS
            )
            for seed in SCREENING_SEEDS
        )
        / len(SCREENING_SEEDS)
        >= 0.80
        for endpoint in ENDPOINTS
    )
    worst_endpoint = all(
        median(
            min(improvements[(seed, comparator, endpoint)] for endpoint in ENDPOINTS)
            for seed in SCREENING_SEEDS
        )
        >= 0.10
        for comparator in COMPARATORS
    )

    def guardrail(key: str) -> bool:
        candidate_median = median(
            float(rows[(seed, CANDIDATE)][key]) for seed in SCREENING_SEEDS
        )
        best = min(
            median(float(rows[(seed, comparator)][key]) for seed in SCREENING_SEEDS)
            for comparator in COMPARATORS
        )
        return candidate_median <= 1.05 * best

    conditions = {
        "availability": availability,
        "finite_and_converged": finite_converged,
        "operator_relative_error": operator,
        "response_zero_ratio": response_zero,
        "paired_improvement": paired,
        "joint_win_rate": joint,
        "worst_endpoint_improvement": worst_endpoint,
        "observed_rmse_guardrail": guardrail("observed_topology_prediction_rmse"),
        "w_ref_guardrail": guardrail("w_ref_raw_response_error_mean"),
    }
    return {
        "rho": rho,
        "a3": a3,
        "eta": eta,
        "passed": all(conditions.values()),
        "conditions": conditions,
        "failed_conditions": [name for name, passed in conditions.items() if not passed],
    }


def evaluate_screening_gate(
    rows: list[dict[str, object]], *, config: R006EConfig
) -> dict[str, object]:
    """Evaluate all nine frozen screening conditions over exactly eight cells."""
    if not isinstance(config, R006EConfig):
        raise TypeError("config must be an R006EConfig")

    def identity_failure(code: str) -> dict[str, object]:
        return {
            "status": "FAIL",
            "failure_code": code,
            "passed_cells": 0,
            "total_cells": len(primary_cells()),
            "cells": [],
        }

    expected_cells = set(primary_cells())
    indexed: dict[tuple[int, float, float, float, str], dict[str, object]] = {}
    for row in rows:
        if not all(key in row for key in ("seed", "rho", "a3", "eta", "method")):
            return identity_failure("INCOMPLETE_ROW_IDENTITY")
        seed = row["seed"]
        if type(seed) is not int:
            return identity_failure("INVALID_ROW_IDENTITY")
        if seed not in SCREENING_SEEDS:
            raise ValueError("rows must use the screening seed set")
        coordinates = (row["rho"], row["a3"], row["eta"])
        method = row["method"]
        if (
            any(
                isinstance(value, bool) or not isinstance(value, Real)
                for value in coordinates
            )
            or not all(math.isfinite(float(value)) for value in coordinates)
            or coordinates not in expected_cells
            or type(method) is not str
            or method not in METHODS
        ):
            return identity_failure("INVALID_ROW_IDENTITY")
        cell = tuple(float(value) for value in coordinates)
        key = (seed, *cell, method)
        if key in indexed:
            return identity_failure("DUPLICATE_ROW_IDENTITY")
        indexed[key] = row
    expected = {
        (seed, *cell, method)
        for seed in SCREENING_SEEDS
        for cell in primary_cells()
        for method in METHODS
    }
    if set(indexed) != expected:
        return identity_failure("MISSING_ROW_IDENTITY")
    cells = [_screening_cell(indexed, cell) for cell in primary_cells()]
    passed_cells = sum(bool(cell["passed"]) for cell in cells)
    return {
        "status": "PASS" if passed_cells == len(cells) else "FAIL",
        "passed_cells": passed_cells,
        "total_cells": len(cells),
        "cells": cells,
    }


def confirmation_contrasts(
    rows: list[dict[str, object]],
) -> dict[str, dict[int, float]]:
    """Return each seed/comparator's worst log loss ratio over 16 queries."""
    expected_cells = set(primary_cells())
    indexed: dict[tuple[int, float, float, float, str], dict[str, object]] = {}
    for row in rows:
        if not all(key in row for key in ("seed", "rho", "a3", "eta", "method")):
            raise ValueError("confirmation row identity is incomplete")
        seed = row["seed"]
        if type(seed) is not int or seed not in CONFIRMATION_SEEDS:
            raise ValueError("rows must use the confirmation seed set")
        coordinates = (row["rho"], row["a3"], row["eta"])
        method = row["method"]
        if (
            any(
                isinstance(value, bool) or not isinstance(value, Real)
                for value in coordinates
            )
            or not all(math.isfinite(float(value)) for value in coordinates)
            or coordinates not in expected_cells
            or type(method) is not str
            or method not in METHODS
        ):
            raise ValueError("confirmation row identity is outside the frozen design")
        losses = [
            row.get(f"{endpoint}_raw_response_error_mean")
            for endpoint in ENDPOINTS
        ]
        if not all(_finite_number(value) and float(value) >= 0.0 for value in losses):
            raise ValueError("confirmation losses must be finite and nonnegative")
        if (
            not _flags_have_exact_native_type(row)
            or row["scorable"] != 1
            or any(row[f"{endpoint}_available"] != 1 for endpoint in ENDPOINTS)
            or not _resource_fields_valid(row)
            or not _all_numeric_values_finite(row)
            or not _scientific_metrics_nonnegative(row)
        ):
            raise ValueError("confirmation row is incomplete or nonscorable")
        cell = tuple(float(value) for value in coordinates)
        key = (seed, *cell, method)
        if key in indexed:
            raise ValueError("duplicate confirmation row identity")
        indexed[key] = row
    expected = {
        (seed, *cell, method)
        for seed in CONFIRMATION_SEEDS
        for cell in primary_cells()
        for method in METHODS
    }
    if set(indexed) != expected:
        raise ValueError("missing confirmation row identity")

    output: dict[str, dict[int, float]] = {name: {} for name in COMPARATORS}
    for comparator in COMPARATORS:
        for seed in CONFIRMATION_SEEDS:
            values: list[float] = []
            for rho, a3, eta in primary_cells():
                candidate = indexed[(seed, rho, a3, eta, CANDIDATE)]
                baseline = indexed[(seed, rho, a3, eta, comparator)]
                for endpoint in ENDPOINTS:
                    if (
                        candidate.get(f"{endpoint}_available") != 1
                        or baseline.get(f"{endpoint}_available") != 1
                    ):
                        raise ValueError("confirmation endpoint is unavailable")
                    candidate_loss = candidate.get(
                        f"{endpoint}_raw_response_error_mean"
                    )
                    baseline_loss = baseline.get(
                        f"{endpoint}_raw_response_error_mean"
                    )
                    if not _finite_number(candidate_loss) or not _finite_number(
                        baseline_loss
                    ):
                        raise ValueError("confirmation losses must be finite")
                    values.append(
                        math.log(
                            max(float(baseline_loss), FLOOR)
                            / max(float(candidate_loss), FLOOR)
                        )
                    )
            if len(values) != 16:
                raise ValueError("confirmation requires 16 cell-endpoint ratios")
            output[comparator][seed] = min(values)
    return output


def exact_binomial_upper_tail(successes: int, n: int = 30) -> float:
    """Exact P{Binomial(n, .5) >= successes}, without an approximation."""
    if (
        isinstance(successes, bool)
        or isinstance(n, bool)
        or not isinstance(successes, int)
        or not isinstance(n, int)
        or n < 0
        or not 0 <= successes <= n
    ):
        raise ValueError("successes and n must be integers with 0 <= successes <= n")
    return sum(math.comb(n, value) for value in range(successes, n + 1)) / 2**n


def holm_adjust(
    raw_p_values: dict[str, float], *, alpha: float = 0.05
) -> dict[str, object]:
    """Apply frozen three-test Holm ordering, adjustment, and stop rule."""
    if set(raw_p_values) != set(COMPARATORS):
        raise ValueError("Holm input must contain exactly the three comparators")
    if not _finite_number(alpha) or not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie in (0, 1)")
    for value in raw_p_values.values():
        if not _finite_number(value) or not 0.0 <= float(value) <= 1.0:
            raise ValueError("p-values must lie in [0, 1]")
    tie_rank = {name: position for position, name in enumerate(COMPARATORS)}
    order = sorted(
        COMPARATORS,
        key=lambda name: (float(raw_p_values[name]), tie_rank[name]),
    )
    adjusted: dict[str, float] = {}
    running = 0.0
    rejected = dict.fromkeys(COMPARATORS, False)
    stopped = False
    for position, name in enumerate(order, start=1):
        multiplier = 4 - position
        running = max(running, multiplier * float(raw_p_values[name]))
        adjusted[name] = min(1.0, running)
        if not stopped and float(raw_p_values[name]) <= float(alpha) / multiplier:
            rejected[name] = True
        else:
            stopped = True
    return {
        "order": order,
        "adjusted_p_values": {
            name: adjusted[name] for name in COMPARATORS
        },
        "rejected": rejected,
    }


def confirmation_sign_inference(
    contrasts: dict[str, dict[int, float]],
) -> dict[str, object]:
    """Compute frozen strict sign counts, exact tails, and Holm summaries."""
    if set(contrasts) != set(COMPARATORS):
        raise ValueError("contrasts must contain exactly the three comparators")
    threshold = math.log(1.10)
    success_counts: dict[str, int] = {}
    raw_p_values: dict[str, float] = {}
    for comparator in COMPARATORS:
        values = contrasts[comparator]
        if set(values) != set(CONFIRMATION_SEEDS):
            raise ValueError("each comparator requires exactly 30 confirmation seeds")
        if not all(_finite_number(value) for value in values.values()):
            raise ValueError("confirmation contrasts must be finite")
        successes = sum(
            float(values[seed]) > threshold for seed in CONFIRMATION_SEEDS
        )
        success_counts[comparator] = successes
        raw_p_values[comparator] = exact_binomial_upper_tail(successes)
    holm = holm_adjust(raw_p_values)
    return {
        "threshold": threshold,
        "success_counts": success_counts,
        "raw_p_values": raw_p_values,
        **holm,
    }


def paired_seed_bootstrap(
    contrasts: dict[str, dict[int, float]],
) -> dict[str, object]:
    """Return the frozen non-gating paired-seed median bootstrap intervals."""
    if set(contrasts) != set(COMPARATORS):
        raise ValueError("contrasts must contain exactly the three comparators")
    for comparator in COMPARATORS:
        values = contrasts[comparator]
        if set(values) != set(CONFIRMATION_SEEDS):
            raise ValueError("each comparator requires exactly 30 confirmation seeds")
        if not all(_finite_number(value) for value in values.values()):
            raise ValueError("confirmation contrasts must be finite")

    audit_seed = 260901
    replicates = 10000
    generator = np.random.Generator(np.random.PCG64(audit_seed))
    sampled_indices = generator.integers(
        0, len(CONFIRMATION_SEEDS), size=(replicates, len(CONFIRMATION_SEEDS))
    )
    intervals: dict[str, dict[str, float]] = {}
    for comparator in COMPARATORS:
        ordered = np.asarray(
            [contrasts[comparator][seed] for seed in CONFIRMATION_SEEDS],
            dtype=float,
        )
        statistics = np.median(ordered[sampled_indices], axis=1)
        bounds = np.quantile(statistics, [0.025, 0.975], method="linear")
        intervals[comparator] = {
            "lower": float(bounds[0]),
            "upper": float(bounds[1]),
        }
    return {
        "audit_seed": audit_seed,
        "replicates": replicates,
        "gating": False,
        "intervals": intervals,
    }


def evaluate_confirmation_gate(
    rows: list[dict[str, object]], *, config: R006EConfig
) -> dict[str, object]:
    """Refuse confirmation until its simultaneous median bound is frozen."""
    if not isinstance(config, R006EConfig):
        raise TypeError("config must be an R006EConfig")
    seeds = {row.get("seed") for row in rows}
    if seeds != set(CONFIRMATION_SEEDS):
        raise ValueError("rows must use exactly the confirmation seed set")
    confirmation_contrasts(rows)
    raise RuntimeError(
        "CONFIRMATION_NOT_AUTHORIZED: simultaneous median-bound specification "
        "is unresolved; no gating verdict may be produced"
    )
