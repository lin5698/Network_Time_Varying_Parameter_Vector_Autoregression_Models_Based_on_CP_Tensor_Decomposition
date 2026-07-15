"""Run the frozen R006c endpoint-aware estimator experiment."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scripts.experiments.high_impact_metrics import spectral_radius
    from scripts.experiments.r005_separation_stability_pilot import ROOT
    from scripts.experiments.r006c_endpoint_estimators import (
        estimate_local_blocks,
        fit_method_bundle,
        fit_scale_adaptive_ridge,
        select_fused_penalty,
    )
    from scripts.experiments.r006c_endpoint_metrics import evaluate_fitted_method
    from scripts.experiments.r006c_endpoint_protocol import (
        APPROXIMATION_TARGETS,
        LAYERS,
        METHODS,
        SEEDS,
        SEPARATION_LEVELS,
        STABILITY_LEVELS,
        EstimationInputs,
        EndpointPanel,
        R006CConfig,
        generate_endpoint_panel,
        required_cells,
        row_normalize,
        spawn_named_streams,
    )
except ModuleNotFoundError:  # Direct execution from scripts/experiments.
    from high_impact_metrics import spectral_radius  # type: ignore
    from r005_separation_stability_pilot import ROOT  # type: ignore
    from r006c_endpoint_estimators import (  # type: ignore
        estimate_local_blocks,
        fit_method_bundle,
        fit_scale_adaptive_ridge,
        select_fused_penalty,
    )
    from r006c_endpoint_metrics import evaluate_fitted_method  # type: ignore
    from r006c_endpoint_protocol import (  # type: ignore
        APPROXIMATION_TARGETS,
        LAYERS,
        METHODS,
        SEEDS,
        SEPARATION_LEVELS,
        STABILITY_LEVELS,
        EstimationInputs,
        EndpointPanel,
        R006CConfig,
        generate_endpoint_panel,
        required_cells,
        row_normalize,
        spawn_named_streams,
    )


DEFAULT_OUTPUT_DIR = (
    ROOT / "output" / "high_impact_revision" / "r006c_endpoint_aware"
)
PROTOCOL_PATH = (
    ROOT / "refine-logs" / "R006C_ENDPOINT_AWARE_ESTIMATOR_DESIGN_20260715.md"
)
CORRECTION_PATH = (
    ROOT / "refine-logs" / "R006C_CHRONOLOGICAL_CORRECTION_20260715.md"
)
CODE_PATHS = {
    "protocol": ROOT / "scripts" / "experiments" / "r006c_endpoint_protocol.py",
    "estimators": ROOT / "scripts" / "experiments" / "r006c_endpoint_estimators.py",
    "metrics": ROOT / "scripts" / "experiments" / "r006c_endpoint_metrics.py",
    "experiment": Path(__file__).resolve(),
    "high_impact_metrics": (
        ROOT / "scripts" / "experiments" / "high_impact_metrics.py"
    ),
    "r005_numerical_dependencies": (
        ROOT / "scripts" / "experiments" / "r005_separation_stability_pilot.py"
    ),
    "r006b_numerical_dependencies": (
        ROOT
        / "scripts"
        / "experiments"
        / "r006b_stability_signal_deconfounding.py"
    ),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def current_provenance() -> dict[str, Any]:
    return {
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "protocol_sha256": _sha256_file(PROTOCOL_PATH),
        "correction_addendum": str(CORRECTION_PATH.relative_to(ROOT)),
        "correction_addendum_sha256": _sha256_file(CORRECTION_PATH),
        "code_sha256": {
            name: _sha256_file(path) for name, path in CODE_PATHS.items()
        },
    }


def _design_diagnostics(
    panel: EndpointPanel,
    parameterization: str,
) -> dict[str, float]:
    x = panel.estimation.predictors
    if parameterization == "block":
        topology = panel.estimation.topology
    else:
        topology = panel.estimation.topology - panel.W_ref[None, :, :]
    exposure = np.einsum("tij,tj->ti", topology, x, optimize=True)
    design = np.concatenate([x, exposure], axis=1)
    gram = design.T @ design / design.shape[0]
    eigenvalues = np.linalg.eigvalsh(gram)
    minimum = max(float(eigenvalues[0]), 0.0)
    maximum = float(eigenvalues[-1])
    return {
        "design_gram_min_eigenvalue": minimum,
        "design_gram_max_eigenvalue": maximum,
        "design_gram_condition": maximum / max(minimum, 1e-12),
    }


def _layer_diagnostics(panel: EndpointPanel) -> dict[str, float | None]:
    predictors = panel.estimation.predictors
    predictor_variance = float(np.mean(np.var(predictors, axis=0)))
    innovation_variance = float(np.mean(np.square(panel.innovations)))
    return {
        "predictor_rms": float(np.sqrt(np.mean(np.square(predictors)))),
        "predictor_covariance_trace": float(
            np.trace(np.cov(predictors, rowvar=False))
        ),
        "innovation_to_state_variance_ratio": (
            innovation_variance / max(predictor_variance, 1e-12)
            if panel.layer == "native"
            else None
        ),
    }


def _construction_diagnostics(
    panel: EndpointPanel,
    *,
    rho: float,
    a3: float,
    query_frobenius_norm: float,
) -> dict[str, float]:
    anchored = panel.A + np.einsum(
        "tij,jk->tik", panel.B, panel.W_ref, optimize=True
    )
    declared_main = row_normalize(0.75 * panel.W_ref + 0.25 * panel.W_holdout)
    return {
        "true_radius_max_abs_error": max(
            abs(spectral_radius(matrix) - rho) for matrix in panel.M_ref
        ),
        "query_frobenius_max_abs_error": max(
            abs(float(np.linalg.norm(matrix)) - query_frobenius_norm)
            for matrix in panel.M_ref
        ),
        "anchor_identity_max_abs_error": float(
            np.max(np.abs(anchored - panel.M_ref))
        ),
        "a3_calibration_abs_error": abs(panel.a3_ratio - a3),
        "observed_radius_max": max(
            spectral_radius(matrix) for matrix in panel.M_observed
        ),
        "main_holdout_mixture_max_abs_error": float(
            np.max(np.abs(declared_main - panel.W_alt_main))
        ),
        "stress_topology_row_sum_max_abs_error": float(
            np.max(np.abs(panel.W_alt_stress.sum(axis=1) - 1.0))
        ),
    }


def _adaptive_ridge_scale_error() -> float:
    rng = np.random.default_rng(606_003)
    design = rng.normal(size=(128, 16))
    outcome = rng.normal(size=(128, 6))
    reference, _ = fit_scale_adaptive_ridge(
        design, outcome, ridge_multiplier=0.001
    )
    errors = []
    for scale in (0.05, 7.0, 100.0):
        estimate, _ = fit_scale_adaptive_ridge(
            scale * design,
            scale * outcome,
            ridge_multiplier=0.001,
        )
        errors.append(float(np.max(np.abs(reference - estimate))))
    return max(errors)


def write_construction_gate(
    *,
    config: R006CConfig,
    output_dir: Path,
) -> dict[str, Any]:
    diagnostics = []
    for layer in LAYERS:
        for rho in STABILITY_LEVELS:
            for a3 in APPROXIMATION_TARGETS:
                for eta in SEPARATION_LEVELS:
                    panel = generate_endpoint_panel(
                        config=config,
                        layer=layer,
                        target_rho=rho,
                        approximation_target=a3,
                        separation_strength=eta,
                        seed=SEEDS[0],
                    )
                    diagnostics.append(
                        _construction_diagnostics(
                            panel,
                            rho=rho,
                            a3=a3,
                            query_frobenius_norm=config.query_frobenius_norm,
                        )
                    )

    def maximum(field: str) -> float:
        return max(float(record[field]) for record in diagnostics)

    panel = generate_endpoint_panel(
        config=config,
        layer="matched",
        target_rho=STABILITY_LEVELS[0],
        approximation_target=APPROXIMATION_TARGETS[0],
        separation_strength=0.15,
        seed=SEEDS[0],
    )
    first_bundle = fit_method_bundle(
        panel.estimation,
        truth_B=panel.B,
        config=config,
        seed=SEEDS[0],
        layer="matched",
        rho=STABILITY_LEVELS[0],
        a3=APPROXIMATION_TARGETS[0],
        eta=0.15,
    )
    holdout_rng = np.random.default_rng(91)
    changed_holdout = row_normalize(
        holdout_rng.uniform(size=panel.W_ref.shape)
    )
    changed_panel = replace(
        panel,
        W_holdout=changed_holdout,
        W_alt_main=row_normalize(
            0.75 * panel.W_ref + 0.25 * changed_holdout
        ),
        W_alt_stress=row_normalize(
            holdout_rng.uniform(size=panel.W_ref.shape)
        ),
    )
    second_bundle = fit_method_bundle(
        changed_panel.estimation,
        truth_B=changed_panel.B,
        config=config,
        seed=SEEDS[0],
        layer="matched",
        rho=STABILITY_LEVELS[0],
        a3=APPROXIMATION_TARGETS[0],
        eta=0.15,
    )
    heldouts_changed = (
        not np.array_equal(panel.W_alt_main, changed_panel.W_alt_main)
        and not np.array_equal(panel.W_alt_stress, changed_panel.W_alt_stress)
    )

    local_tensor, indices, _, _ = estimate_local_blocks(
        panel.estimation.predictors,
        panel.estimation.outcomes,
        panel.estimation.topology,
        window=config.window,
        ridge_multiplier=config.ridge_multiplier,
    )
    evaluation_count = max(
        1, int(math.ceil(config.evaluation_fraction * len(indices)))
    )
    perturbed = local_tensor.copy()
    perturbed[:, :, -evaluation_count:] += 100.0
    fit_panel = {
        "predictors": panel.estimation.predictors,
        "outcomes": panel.estimation.outcomes,
        "W": panel.estimation.topology,
    }
    selected, selection_diagnostics = select_fused_penalty(
        local_tensor, fit_panel, indices, config
    )
    changed_selected, changed_selection_diagnostics = select_fused_penalty(
        perturbed, fit_panel, indices, config
    )

    streams_a = spawn_named_streams(SEEDS[0])
    streams_b = spawn_named_streams(SEEDS[0])
    stream_reproducible = all(
        np.array_equal(
            streams_a[name].normal(size=16),
            streams_b[name].normal(size=16),
        )
        for name in streams_a
    )
    alt_truth_anchor = panel.M_ref + np.einsum(
        "tij,jk->tik",
        panel.B,
        panel.W_alt_main - panel.W_ref,
        optimize=True,
    )
    alt_truth_block = panel.A + np.einsum(
        "tij,jk->tik", panel.B, panel.W_alt_main, optimize=True
    )
    alt_query_identity_error = float(
        np.max(np.abs(alt_truth_anchor - alt_truth_block))
    )
    scale_error = _adaptive_ridge_scale_error()
    checks = {
        "named_stream_reproducibility": stream_reproducible,
        "radius": maximum("true_radius_max_abs_error") < 1e-10,
        "query_frobenius": maximum("query_frobenius_max_abs_error") < 1e-6,
        "anchor_identity": maximum("anchor_identity_max_abs_error") < 1e-10,
        "alternative_query_identity": alt_query_identity_error < 1e-10,
        "a3_calibration": maximum("a3_calibration_abs_error") < 1e-6,
        "observed_operator_bound": maximum("observed_radius_max") < 1.05,
        "main_holdout_mixture": (
            maximum("main_holdout_mixture_max_abs_error") < 1e-12
        ),
        "stress_topology_normalization": (
            maximum("stress_topology_row_sum_max_abs_error") < 1e-12
        ),
        "heldouts_actually_perturbed": heldouts_changed,
        "heldout_fit_invariance": (
            first_bundle.fit_digest() == second_bundle.fit_digest()
        ),
        "heldout_selection_invariance": (
            first_bundle.selected_hyperparameters()
            == second_bundle.selected_hyperparameters()
        ),
        "adaptive_ridge_scale_invariance": scale_error < 1e-8,
        "causal_fused_validation": (
            selected == changed_selected
            and selection_diagnostics["candidate_scores"]
            == changed_selection_diagnostics["candidate_scores"]
            and selection_diagnostics["evaluation_dates_excluded"]
            == evaluation_count
        ),
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "provenance": current_provenance(),
        "config": json.loads(json.dumps(asdict(config))),
        "checks": checks,
        "diagnostics": {
            "max_radius_error": maximum("true_radius_max_abs_error"),
            "max_query_frobenius_error": maximum(
                "query_frobenius_max_abs_error"
            ),
            "max_anchor_identity_error": maximum(
                "anchor_identity_max_abs_error"
            ),
            "max_alternative_query_identity_error": alt_query_identity_error,
            "max_a3_calibration_error": maximum("a3_calibration_abs_error"),
            "max_observed_radius": maximum("observed_radius_max"),
            "adaptive_ridge_scale_error": scale_error,
            "selected_fused_penalty": selected,
            "construction_cells": len(diagnostics),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "construction_gate_preoutcome.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return payload


def verify_construction_gate(
    *,
    config: R006CConfig,
    output_dir: Path,
) -> dict[str, Any]:
    path = output_dir / "construction_gate_preoutcome.json"
    if not path.exists():
        raise RuntimeError("formal run requires construction_gate_preoutcome.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS":
        raise RuntimeError("construction gate did not pass")
    if payload.get("config") != json.loads(json.dumps(asdict(config))):
        raise RuntimeError("construction gate config mismatch")
    if payload.get("provenance") != current_provenance():
        raise RuntimeError("construction gate protocol/code hash mismatch")
    return payload


def _identity_fields(
    *,
    config: R006CConfig,
    layer: str,
    rho: float,
    a3: float,
    eta: float,
    seed: int,
    method: str,
) -> dict[str, Any]:
    return {
        "layer": layer,
        "rho": rho,
        "a3": a3,
        "eta": eta,
        "seed": seed,
        "method": method,
        "N": config.n,
        "T": config.t_len,
    }


def run_replication(
    *,
    config: R006CConfig,
    layer: str,
    rho: float,
    a3: float,
    eta: float,
    seed: int,
) -> list[dict[str, Any]]:
    try:
        panel = generate_endpoint_panel(
            config=config,
            layer=layer,
            target_rho=rho,
            approximation_target=a3,
            separation_strength=eta,
            seed=seed,
        )
        bundle = fit_method_bundle(
            panel.estimation,
            truth_B=panel.B,
            config=config,
            seed=seed,
            layer=layer,
            rho=rho,
            a3=a3,
            eta=eta,
        )
        layer_diagnostics = _layer_diagnostics(panel)
        construction = _construction_diagnostics(
            panel,
            rho=rho,
            a3=a3,
            query_frobenius_norm=config.query_frobenius_norm,
        )
        fit_digest = bundle.fit_digest()
        rows = []
        for method in METHODS:
            fitted = bundle.methods[method]
            row = _identity_fields(
                config=config,
                layer=layer,
                rho=rho,
                a3=a3,
                eta=eta,
                seed=seed,
                method=method,
            )
            row.update(
                {
                    "actual_a3_ratio": panel.a3_ratio,
                    "fit_digest": fit_digest,
                    "failure": 0,
                    "failure_reason": None,
                }
            )
            row.update(evaluate_fitted_method(fitted, panel, config))
            row.update(_design_diagnostics(panel, fitted.parameterization))
            row.update(layer_diagnostics)
            row.update(construction)
            rows.append(row)
        return rows
    except Exception as error:  # Preserve every frozen method identity on failure.
        reason = f"{type(error).__name__}: {error}"
        return [
            {
                **_identity_fields(
                    config=config,
                    layer=layer,
                    rho=rho,
                    a3=a3,
                    eta=eta,
                    seed=seed,
                    method=method,
                ),
                "failure": 1,
                "failure_reason": reason,
            }
            for method in METHODS
        ]


def _run_task(
    task: tuple[R006CConfig, str, float, float, float, int],
) -> list[dict[str, Any]]:
    config, layer, rho, a3, eta, seed = task
    return run_replication(
        config=config,
        layer=layer,
        rho=rho,
        a3=a3,
        eta=eta,
        seed=seed,
    )


def _summarize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["layer"], row["rho"], row["a3"], row["eta"], row["method"])
        groups.setdefault(key, []).append(row)
    summary = []
    for key, group in sorted(groups.items()):
        valid = [row for row in group if row["failure"] == 0]
        record = {
            "layer": key[0],
            "rho": key[1],
            "a3": key[2],
            "eta": key[3],
            "method": key[4],
            "replications": len(group),
            "failures": len(group) - len(valid),
        }
        for field in (
            "w_ref_operator_relative_error_mean",
            "w_ref_raw_response_error_mean",
            "w_alt_main_operator_relative_error_mean",
            "w_alt_main_raw_response_error_mean",
            "w_alt_stress_operator_relative_error_mean",
            "w_alt_stress_raw_response_error_mean",
            "retrospective_prediction_rmse",
            "runtime_seconds",
        ):
            values = [float(row[field]) for row in valid if row.get(field) is not None]
            record[f"{field}_median"] = (
                float(np.median(values)) if values else None
            )
        summary.append(record)
    return summary


def _median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def evaluate_promotion_gate(
    rows: list[dict[str, Any]],
    *,
    seeds: tuple[int, ...] = SEEDS,
) -> dict[str, Any]:
    comparators = ("block_local", "block_fused_tv", "block_tucker333")
    candidates = ("anchor_split_cp3", "anchor_split_tucker333")
    lookup = {
        (
            row["layer"], row["rho"], row["a3"], row["eta"],
            row["seed"], row["method"],
        ): row
        for row in rows
    }
    candidate_results: dict[str, Any] = {}

    for candidate in candidates:
        cell_results = []
        for layer, rho, a3, eta in required_cells():
            candidate_rows = [
                lookup.get((layer, rho, a3, eta, seed, candidate))
                for seed in seeds
            ]
            candidate_complete = all(
                row is not None and row.get("failure") == 0
                for row in candidate_rows
            )
            endpoints: dict[str, Any] = {}
            for endpoint in ("w_ref", "w_alt_main"):
                operator_values = [
                    float(row[f"{endpoint}_operator_relative_error_mean"])
                    for row in candidate_rows
                    if row is not None
                    and row.get("failure") == 0
                    and row.get(f"{endpoint}_operator_relative_error_mean") is not None
                ]
                zero_values = [
                    float(row[f"{endpoint}_response_zero_ratio_mean"])
                    for row in candidate_rows
                    if row is not None
                    and row.get("failure") == 0
                    and row.get(f"{endpoint}_response_zero_ratio_mean") is not None
                ]
                availability = (
                    candidate_complete
                    and all(
                        row is not None and row.get(f"{endpoint}_available") == 1
                        for row in candidate_rows
                    )
                )
                improvements: dict[str, float | None] = {}
                paired_counts: dict[str, int] = {}
                for comparator in comparators:
                    paired = []
                    for seed in seeds:
                        candidate_row = lookup.get(
                            (layer, rho, a3, eta, seed, candidate)
                        )
                        comparator_row = lookup.get(
                            (layer, rho, a3, eta, seed, comparator)
                        )
                        if (
                            candidate_row is None
                            or comparator_row is None
                            or candidate_row.get("failure") != 0
                            or comparator_row.get("failure") != 0
                            or candidate_row.get(f"{endpoint}_raw_response_error_mean") is None
                            or comparator_row.get(f"{endpoint}_raw_response_error_mean") is None
                        ):
                            continue
                        candidate_error = float(
                            candidate_row[f"{endpoint}_raw_response_error_mean"]
                        )
                        comparator_error = float(
                            comparator_row[f"{endpoint}_raw_response_error_mean"]
                        )
                        paired.append(
                            (comparator_error - candidate_error)
                            / max(comparator_error, 1e-12)
                        )
                    improvements[comparator] = _median(paired)
                    paired_counts[comparator] = len(paired)

                joint_wins = []
                for seed in seeds:
                    candidate_row = lookup.get(
                        (layer, rho, a3, eta, seed, candidate)
                    )
                    comparator_rows = [
                        lookup.get((layer, rho, a3, eta, seed, comparator))
                        for comparator in comparators
                    ]
                    if (
                        candidate_row is None
                        or candidate_row.get("failure") != 0
                        or candidate_row.get(f"{endpoint}_raw_response_error_mean") is None
                        or any(
                            row is None
                            or row.get("failure") != 0
                            or row.get(f"{endpoint}_raw_response_error_mean") is None
                            for row in comparator_rows
                        )
                    ):
                        continue
                    candidate_error = float(
                        candidate_row[f"{endpoint}_raw_response_error_mean"]
                    )
                    joint_wins.append(
                        all(
                            candidate_error
                            < float(row[f"{endpoint}_raw_response_error_mean"])
                            for row in comparator_rows
                            if row is not None
                        )
                    )
                operator_median = _median(operator_values)
                zero_median = _median(zero_values)
                joint_win_rate = (
                    float(np.mean(joint_wins)) if joint_wins else None
                )
                endpoint_pass = (
                    availability
                    and len(operator_values) == len(seeds)
                    and len(zero_values) == len(seeds)
                    and operator_median is not None
                    and operator_median < 1.0
                    and zero_median is not None
                    and zero_median < 1.0
                    and all(count == len(seeds) for count in paired_counts.values())
                    and all(
                        value is not None and value + 1e-12 >= 0.10
                        for value in improvements.values()
                    )
                    and len(joint_wins) == len(seeds)
                    and joint_win_rate is not None
                    and joint_win_rate + 1e-12 >= 0.80
                )
                endpoints[endpoint] = {
                    "availability_100pct": availability,
                    "operator_error_median": operator_median,
                    "zero_ratio_median": zero_median,
                    "paired_median_improvement": improvements,
                    "paired_counts": paired_counts,
                    "joint_win_rate": joint_win_rate,
                    "pass": endpoint_pass,
                }

            worst_improvements: dict[str, float | None] = {}
            worst_counts: dict[str, int] = {}
            for comparator in comparators:
                paired = []
                for seed in seeds:
                    candidate_row = lookup.get(
                        (layer, rho, a3, eta, seed, candidate)
                    )
                    comparator_row = lookup.get(
                        (layer, rho, a3, eta, seed, comparator)
                    )
                    if (
                        candidate_row is None
                        or comparator_row is None
                        or candidate_row.get("failure") != 0
                        or comparator_row.get("failure") != 0
                    ):
                        continue
                    required_fields = (
                        "w_ref_raw_response_error_mean",
                        "w_alt_main_raw_response_error_mean",
                    )
                    if any(
                        candidate_row.get(field) is None
                        or comparator_row.get(field) is None
                        for field in required_fields
                    ):
                        continue
                    candidate_worst = max(
                        float(candidate_row[field]) for field in required_fields
                    )
                    comparator_worst = max(
                        float(comparator_row[field]) for field in required_fields
                    )
                    paired.append(
                        (comparator_worst - candidate_worst)
                        / max(comparator_worst, 1e-12)
                    )
                worst_improvements[comparator] = _median(paired)
                worst_counts[comparator] = len(paired)
            worst_pass = (
                all(count == len(seeds) for count in worst_counts.values())
                and all(
                    value is not None and value + 1e-12 >= 0.10
                    for value in worst_improvements.values()
                )
            )
            cell_pass = (
                candidate_complete
                and all(record["pass"] for record in endpoints.values())
                and worst_pass
            )
            cell_results.append(
                {
                    "layer": layer,
                    "rho": rho,
                    "a3": a3,
                    "eta": eta,
                    "candidate_seeds": sum(row is not None for row in candidate_rows),
                    "no_candidate_failures": candidate_complete,
                    "endpoints": endpoints,
                    "worst_endpoint": {
                        "paired_median_improvement": worst_improvements,
                        "paired_counts": worst_counts,
                        "pass": worst_pass,
                    },
                    "pass": cell_pass,
                }
            )
        passed_cells = sum(record["pass"] for record in cell_results)
        candidate_results[candidate] = {
            "required_cells": cell_results,
            "passed_cells": passed_cells,
            "pass": passed_cells == len(required_cells()),
        }

    promotion_candidates = [
        name for name in candidates if candidate_results[name]["pass"]
    ]
    return {
        "candidates": candidate_results,
        "promotion_candidates": promotion_candidates,
        "pass": bool(promotion_candidates),
    }


def evaluate_grid_gate(
    rows: list[dict[str, Any]],
    *,
    config: R006CConfig,
    layers: tuple[str, ...],
    rhos: tuple[float, ...],
    a3_values: tuple[float, ...],
    eta_values: tuple[float, ...],
    seeds: tuple[int, ...],
    smoke: bool,
) -> dict[str, Any]:
    expected_rows = (
        len(layers)
        * len(rhos)
        * len(a3_values)
        * len(eta_values)
        * len(seeds)
        * len(METHODS)
    )
    identities = {
        (
            row["layer"], row["rho"], row["a3"], row["eta"],
            row["seed"], row["method"],
        )
        for row in rows
    }
    valid = [row for row in rows if row.get("failure") == 0]
    failures = [row for row in rows if row.get("failure") != 0]

    def maximum(field: str) -> float:
        values = [
            float(row[field])
            for row in valid
            if row.get(field) is not None
        ]
        return max(values, default=math.inf)

    construction = {
        "radius": maximum("true_radius_max_abs_error") < 1e-10,
        "query_frobenius": maximum("query_frobenius_max_abs_error") < 1e-6,
        "anchor_identity": maximum("anchor_identity_max_abs_error") < 1e-10,
        "a3_calibration": maximum("a3_calibration_abs_error") < 1e-6,
        "observed_operator_bound": maximum("observed_radius_max") < 1.05,
        "main_holdout_mixture": (
            maximum("main_holdout_mixture_max_abs_error") < 1e-12
        ),
        "stress_topology_normalization": (
            maximum("stress_topology_row_sum_max_abs_error") < 1e-12
        ),
    }
    full_grid_declared = (
        layers == LAYERS
        and rhos == STABILITY_LEVELS
        and a3_values == APPROXIMATION_TARGETS
        and eta_values == SEPARATION_LEVELS
        and seeds == SEEDS
        and config == R006CConfig()
    )
    completion = {
        "row_count": len(rows) == expected_rows,
        "unique_rows": len(identities) == expected_rows,
        "no_failures": not failures,
        "full_grid_declared": full_grid_declared,
    }
    metric_suffixes = (
        "raw_response_error_mean",
        "stability_qualified_error_mean",
        "projected_sensitivity_error_mean",
    )
    separate_response_metrics = all(
        all(
            f"{endpoint}_{suffix}" in row
            for endpoint in ("w_ref", "w_alt_main", "w_alt_stress")
            for suffix in metric_suffixes
        )
        for row in valid
    )
    endpoint_availability_contract = all(
        row.get("w_ref_available") == 1
        and (
            row.get("w_alt_main_available") == 0
            and row.get("w_alt_stress_available") == 0
            if row["method"] == "collapsed_ref_tucker333"
            else row.get("w_alt_main_available") == 1
            and row.get("w_alt_stress_available") == 1
        )
        for row in valid
    )
    promotion = evaluate_promotion_gate(rows, seeds=seeds)
    construction_pass = all(construction.values())
    supplied_grid_complete = all(
        completion[name] for name in ("row_count", "unique_rows", "no_failures")
    )
    smoke_pass = (
        construction_pass
        and supplied_grid_complete
        and separate_response_metrics
        and endpoint_availability_contract
    )
    full_pass = (
        smoke_pass
        and completion["full_grid_declared"]
        and promotion["pass"]
    )
    status = (
        "SMOKE_PASS" if smoke and smoke_pass else
        "SMOKE_FAIL" if smoke else
        "PASS" if full_pass else
        "FAIL"
    )
    return {
        "status": status,
        "construction": construction,
        "completion": completion,
        "separate_response_metrics": separate_response_metrics,
        "endpoint_availability_contract": endpoint_availability_contract,
        "promotion": promotion,
        "expected_rows": expected_rows,
        "row_count": len(rows),
        "unique_rows": len(identities),
        "failure_count": len(failures),
        "failure_reasons": sorted(
            {row.get("failure_reason") for row in failures if row.get("failure_reason")}
        ),
        "max_radius_error": maximum("true_radius_max_abs_error"),
        "max_query_frobenius_error": maximum(
            "query_frobenius_max_abs_error"
        ),
        "max_anchor_identity_error": maximum(
            "anchor_identity_max_abs_error"
        ),
        "max_a3_calibration_error": maximum("a3_calibration_abs_error"),
        "max_observed_radius": maximum("observed_radius_max"),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_outputs(
    output_dir: Path,
    rows: list[dict[str, Any]],
    summary: list[dict[str, Any]],
    payload: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "r006c_replications.csv", rows)
    _write_csv(output_dir / "r006c_summary.csv", summary)
    (output_dir / "r006c_results.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    checks = payload["checks"]
    construction_lines = [
        f"- {name}: `{'PASS' if passed else 'FAIL'}`"
        for name, passed in checks["construction"].items()
    ]
    required_lines = []
    for candidate, candidate_record in checks["promotion"]["candidates"].items():
        for cell in candidate_record["required_cells"]:
            required_lines.append(
                "| "
                f"{candidate} | {cell['layer']} | {cell['rho']:.2f} | "
                f"{cell['a3']:.2f} | {cell['eta']:.2f} | "
                f"{'PASS' if cell['endpoints']['w_ref']['pass'] else 'FAIL'} | "
                f"{'PASS' if cell['endpoints']['w_alt_main']['pass'] else 'FAIL'} | "
                f"{'PASS' if cell['worst_endpoint']['pass'] else 'FAIL'} | "
                f"{'PASS' if cell['pass'] else 'FAIL'} |"
            )
    promotion_candidates = checks["promotion"]["promotion_candidates"]
    promotion_text = (
        ", ".join(f"`{name}`" for name in promotion_candidates)
        if promotion_candidates
        else "none"
    )
    report = f"""# R006c Endpoint-Aware Estimator Results

**Status:** `{payload['status']}`  
**Run type:** `{payload['run_type']}`  
**Rows:** `{payload['row_count']}`  
**Failures:** `{checks['failure_count']}`

This report evaluates only the frozen R006c protocol. A smoke result cannot promote a method claim.

## Construction Gates

{chr(10).join(construction_lines)}

## Required Cell Gates

| candidate | layer | rho | a3 | eta | W_ref | W_alt_main | worst endpoint | cell |
| --- | --- | ---: | ---: | ---: | :---: | :---: | :---: | :---: |
{chr(10).join(required_lines)}

Promotion candidates: {promotion_text}.

`eta=0.02`, `W_alt_stress`, collapsed-reference and oracle-B rows are diagnostics only. Projected sensitivity never substitutes for a failed raw-response gate.
"""
    (output_dir / "r006c_results.md").write_text(report, encoding="utf-8")


def _read_csv_lookup(
    path: Path,
    identity_fields: tuple[str, ...],
) -> dict[tuple[str, ...], dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        tuple(row[field] for field in identity_fields): row for row in rows
    }


def _strip_runtime_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_runtime_metadata(item)
            for key, item in value.items()
            if key not in {"generated_at", "elapsed_seconds"}
            and "runtime" not in key.lower()
        }
    if isinstance(value, list):
        return [_strip_runtime_metadata(item) for item in value]
    return value


def compare_run_directories(primary: Path, repeat: Path) -> dict[str, Any]:
    difference_details = []
    difference_count = 0

    def compare_csv(
        filename: str,
        identity_fields: tuple[str, ...],
    ) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
        nonlocal difference_count
        left = _read_csv_lookup(primary / filename, identity_fields)
        right = _read_csv_lookup(repeat / filename, identity_fields)
        missing = sorted(set(left) - set(right))
        extra = sorted(set(right) - set(left))
        difference_count += len(missing) + len(extra)
        for identity in sorted(set(left) & set(right)):
            fields = sorted(set(left[identity]) | set(right[identity]))
            for field in fields:
                if "runtime" in field.lower():
                    continue
                if left[identity].get(field) != right[identity].get(field):
                    difference_count += 1
                    if len(difference_details) < 100:
                        difference_details.append(
                            {
                                "artifact": filename,
                                "identity": list(identity),
                                "field": field,
                                "primary": left[identity].get(field),
                                "repeat": right[identity].get(field),
                            }
                        )
        return missing, extra

    replication_identity = ("layer", "rho", "a3", "eta", "seed", "method")
    summary_identity = ("layer", "rho", "a3", "eta", "method")
    missing_rows, extra_rows = compare_csv(
        "r006c_replications.csv", replication_identity
    )
    missing_summary, extra_summary = compare_csv(
        "r006c_summary.csv", summary_identity
    )

    left_results = _strip_runtime_metadata(
        json.loads((primary / "r006c_results.json").read_text(encoding="utf-8"))
    )
    right_results = _strip_runtime_metadata(
        json.loads((repeat / "r006c_results.json").read_text(encoding="utf-8"))
    )
    result_payload_equal = left_results == right_results
    if not result_payload_equal:
        difference_count += 1
        if len(difference_details) < 100:
            difference_details.append(
                {"artifact": "r006c_results.json", "field": "normalized_payload"}
            )

    construction_name = "construction_gate_preoutcome.json"
    left_construction_path = primary / construction_name
    right_construction_path = repeat / construction_name
    if left_construction_path.exists() and right_construction_path.exists():
        left_construction = _strip_runtime_metadata(
            json.loads(left_construction_path.read_text(encoding="utf-8"))
        )
        right_construction = _strip_runtime_metadata(
            json.loads(right_construction_path.read_text(encoding="utf-8"))
        )
        construction_equal = left_construction == right_construction
    else:
        construction_equal = (
            left_construction_path.exists() == right_construction_path.exists()
        )
    if not construction_equal:
        difference_count += 1
        if len(difference_details) < 100:
            difference_details.append(
                {"artifact": construction_name, "field": "normalized_payload"}
            )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if difference_count == 0 else "FAIL",
        "primary": str(primary),
        "repeat": str(repeat),
        "primary_replication_rows": len(
            _read_csv_lookup(primary / "r006c_replications.csv", replication_identity)
        ),
        "repeat_replication_rows": len(
            _read_csv_lookup(repeat / "r006c_replications.csv", replication_identity)
        ),
        "missing_replication_identities": [list(item) for item in missing_rows],
        "extra_replication_identities": [list(item) for item in extra_rows],
        "missing_summary_identities": [list(item) for item in missing_summary],
        "extra_summary_identities": [list(item) for item in extra_summary],
        "result_payload_equal_excluding_runtime": result_payload_equal,
        "construction_payload_equal_excluding_generation_time": construction_equal,
        "non_runtime_field_differences": difference_count,
        "difference_details": difference_details,
    }
    (primary / "r006c_duplicate_comparison.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return payload


def run_grid(
    *,
    config: R006CConfig,
    layers: tuple[str, ...] = LAYERS,
    rhos: tuple[float, ...] = STABILITY_LEVELS,
    a3_values: tuple[float, ...] = APPROXIMATION_TARGETS,
    eta_values: tuple[float, ...] = SEPARATION_LEVELS,
    seeds: tuple[int, ...] = SEEDS,
    workers: int = 1,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    smoke: bool = False,
) -> dict[str, Any]:
    if not smoke:
        verify_construction_gate(config=config, output_dir=output_dir)
    started = time.perf_counter()
    tasks = [
        (config, layer, rho, a3, eta, seed)
        for layer in layers
        for rho in rhos
        for a3 in a3_values
        for eta in eta_values
        for seed in seeds
    ]
    if workers <= 1:
        nested_rows = [_run_task(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            nested_rows = list(executor.map(_run_task, tasks))
    rows = [row for group in nested_rows for row in group]
    rows.sort(
        key=lambda row: (
            row["layer"], row["rho"], row["a3"], row["eta"],
            row["seed"], row["method"],
        )
    )
    checks = evaluate_grid_gate(
        rows,
        config=config,
        layers=layers,
        rhos=rhos,
        a3_values=a3_values,
        eta_values=eta_values,
        seeds=seeds,
        smoke=smoke,
    )
    summary = _summarize_rows(rows)
    elapsed = time.perf_counter() - started
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_type": "SMOKE" if smoke else "FULL_PROTOCOL",
        "status": checks["status"],
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "provenance": current_provenance(),
        "config": asdict(config),
        "grid": {
            "layers": list(layers),
            "rhos": list(rhos),
            "a3_values": list(a3_values),
            "eta_values": list(eta_values),
            "seeds": list(seeds),
            "workers": workers,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "elapsed_seconds": elapsed,
        "row_count": len(rows),
        "checks": checks,
        "summary": summary,
    }
    _write_outputs(output_dir, rows, summary, payload)
    return payload


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, min(8, (os.cpu_count() or 2) - 1)),
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--smoke", action="store_true")
    modes.add_argument("--construction-gate-only", action="store_true")
    modes.add_argument("--compare-to", type=Path)
    return parser


def main() -> None:
    arguments = build_argument_parser().parse_args()
    output_dir = arguments.output_dir or DEFAULT_OUTPUT_DIR
    if arguments.compare_to is not None:
        payload = compare_run_directories(output_dir, arguments.compare_to)
        print(json.dumps(payload, indent=2))
        if payload["status"] != "PASS":
            raise SystemExit(1)
        return
    if arguments.construction_gate_only:
        payload = write_construction_gate(
            config=R006CConfig(), output_dir=output_dir
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "run_type": "CONSTRUCTION_GATE_ONLY",
                    "output_dir": str(output_dir),
                },
                indent=2,
            )
        )
        if payload["status"] != "PASS":
            raise SystemExit(1)
        return
    if arguments.smoke:
        config = R006CConfig(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            cp_iterations=10,
            cp_starts=1,
            fused_penalties=(0.10, 0.50),
            fused_max_iterations=100,
        )
        layers = LAYERS
        rhos = STABILITY_LEVELS
        a3_values = APPROXIMATION_TARGETS
        eta_values = SEPARATION_LEVELS
        seeds = (SEEDS[0],)
        if arguments.output_dir is None:
            output_dir = (
                ROOT
                / "output"
                / "high_impact_revision"
                / "r006c_endpoint_aware_smoke"
            )
    else:
        config = R006CConfig()
        layers = LAYERS
        rhos = STABILITY_LEVELS
        a3_values = APPROXIMATION_TARGETS
        eta_values = SEPARATION_LEVELS
        seeds = SEEDS
    payload = run_grid(
        config=config,
        layers=layers,
        rhos=rhos,
        a3_values=a3_values,
        eta_values=eta_values,
        seeds=seeds,
        workers=arguments.workers,
        output_dir=output_dir,
        smoke=arguments.smoke,
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "run_type": payload["run_type"],
                "output_dir": str(output_dir),
                "rows": payload["row_count"],
                "elapsed_seconds": payload["elapsed_seconds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
