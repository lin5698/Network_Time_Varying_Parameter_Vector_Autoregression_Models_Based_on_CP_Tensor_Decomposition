"""Run the outcome-free R006d endpoint construction gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

try:
    from scripts.experiments.r005_separation_stability_pilot import ROOT
    from scripts.experiments.r006c_endpoint_protocol import (
        APPROXIMATION_TARGETS,
        LAYERS,
        SEEDS,
        STABILITY_LEVELS,
        R006CConfig,
        generate_endpoint_panel,
        required_cells,
    )
    from scripts.experiments.r006d_endpoint_support import (
        ChronologicalRegions,
        SupportPath,
        build_design_support_path,
        chronological_regions,
        evaluate_candidate_pool,
        evaluate_query_path,
        generate_family_pool,
        generate_unsupported_pool,
        select_supported_index,
        select_unsupported_index,
    )
except ModuleNotFoundError:  # Direct execution from scripts/experiments.
    from r005_separation_stability_pilot import ROOT  # type: ignore
    from r006c_endpoint_protocol import (  # type: ignore
        APPROXIMATION_TARGETS,
        LAYERS,
        SEEDS,
        STABILITY_LEVELS,
        R006CConfig,
        generate_endpoint_panel,
        required_cells,
    )
    from r006d_endpoint_support import (  # type: ignore
        ChronologicalRegions,
        SupportPath,
        build_design_support_path,
        chronological_regions,
        evaluate_candidate_pool,
        evaluate_query_path,
        generate_family_pool,
        generate_unsupported_pool,
        select_supported_index,
        select_unsupported_index,
    )


PROTOCOL_PATH = (
    ROOT / "refine-logs" / "R006D_DESIGN_WEIGHTED_ENDPOINT_PROTOCOL_20260715.md"
)
DEFAULT_OUTPUT = (
    ROOT
    / "output"
    / "high_impact_revision"
    / "r006d_design_weighted_endpoint"
    / "construction_gate_preoutcome.json"
)


@dataclass(frozen=True)
class R006DConstructionConfig:
    pool_size: int = 64
    kappa_max: float = 50.0
    absolute_floor: float = 1e-10
    supported_threshold: float = 0.10
    unsupported_median_threshold: float = 0.20
    unsupported_maximum_threshold: float = 0.35


def construction_seed(
    seed: int,
    layer: str,
    rho: float,
    a3: float,
    eta: float,
    role: str,
) -> int:
    key = f"{seed}|{layer}|{rho:.12g}|{a3:.12g}|{eta:.12g}|{role}"
    return int.from_bytes(
        hashlib.sha256(key.encode("ascii")).digest()[:8], "big"
    )


def construction_schema(regions: ChronologicalRegions) -> dict[str, Any]:
    return {
        "calibration_dates": regions.calibration.tolist(),
        "validation_dates": regions.validation.tolist(),
        "evaluation_dates": regions.evaluation.tolist(),
    }


def _path_record(
    path: SupportPath,
    *,
    include_dates: bool = True,
    include_design: bool = True,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "chi": path.chi.tolist(),
        "maximum_chi": path.maximum_chi,
        "median_chi": path.median_chi,
        "retained_rank": path.retained_rank.tolist(),
    }
    if include_dates:
        record["dates"] = path.dates.tolist()
    if include_design:
        record["tau"] = path.tau.tolist()
        record["singular_values"] = [
            values.tolist() for values in path.singular_values
        ]
    return record


def _candidate_records(paths: tuple[SupportPath, ...]) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            **_path_record(
                path, include_dates=False, include_design=False
            ),
        }
        for index, path in enumerate(paths)
    ]


def evaluate_panel_construction(
    *,
    predictors: np.ndarray,
    topology: np.ndarray,
    w_ref: np.ndarray,
    w_interp: np.ndarray,
    regions: ChronologicalRegions,
    family_seed: int,
    unsupported_seed: int,
    config: R006DConstructionConfig = R006DConstructionConfig(),
) -> dict[str, Any]:
    if config.pool_size <= 0:
        raise ValueError("pool_size must be positive")
    scored_dates = np.concatenate([regions.validation, regions.evaluation])
    calibration_design = build_design_support_path(
        predictors,
        topology,
        w_ref,
        regions.calibration,
        window=int(regions.calibration[0]),
        kappa_max=config.kappa_max,
        absolute_floor=config.absolute_floor,
    )
    scored_design = build_design_support_path(
        predictors,
        topology,
        w_ref,
        scored_dates,
        window=int(regions.calibration[0]),
        kappa_max=config.kappa_max,
        absolute_floor=config.absolute_floor,
    )

    interp_calibration = evaluate_query_path(
        calibration_design, w_ref, w_interp
    )
    interp_scored = evaluate_query_path(scored_design, w_ref, w_interp)

    family_pool = generate_family_pool(
        n=w_ref.shape[0], size=config.pool_size, seed=family_seed
    )
    family_calibration = evaluate_candidate_pool(
        calibration_design, w_ref, family_pool
    )
    family_index = select_supported_index(
        [path.maximum_chi for path in family_calibration],
        threshold=config.supported_threshold,
    )
    family_scored = (
        evaluate_query_path(scored_design, w_ref, family_pool[family_index])
        if family_index is not None
        else None
    )

    unsupported_pool = generate_unsupported_pool(
        n=w_ref.shape[0], size=config.pool_size, seed=unsupported_seed
    )
    unsupported_calibration = evaluate_candidate_pool(
        calibration_design, w_ref, unsupported_pool
    )
    unsupported_index = select_unsupported_index(
        median_chi=[path.median_chi for path in unsupported_calibration],
        maximum_chi=[path.maximum_chi for path in unsupported_calibration],
        median_threshold=config.unsupported_median_threshold,
        maximum_threshold=config.unsupported_maximum_threshold,
    )
    unsupported_scored = (
        evaluate_query_path(
            scored_design, w_ref, unsupported_pool[unsupported_index]
        )
        if unsupported_index is not None
        else None
    )

    failures = []
    if interp_calibration.maximum_chi > config.supported_threshold:
        failures.append("interp_not_supported_in_calibration")
    if interp_scored.maximum_chi > config.supported_threshold:
        failures.append("interp_lost_support_prospectively")
    if family_index is None:
        failures.append("no_supported_family_candidate")
    elif family_scored is not None and (
        family_scored.maximum_chi > config.supported_threshold
    ):
        failures.append("family_lost_support_prospectively")
    if unsupported_index is None:
        failures.append("no_unsupported_candidate")
    elif unsupported_scored is not None and (
        unsupported_scored.maximum_chi
        < config.unsupported_maximum_threshold
        or unsupported_scored.median_chi
        < config.unsupported_median_threshold
    ):
        failures.append("unsupported_endpoint_lost_status_prospectively")

    return {
        "status": "CONSTRUCTION_PASS" if not failures else "CONSTRUCTION_FAIL",
        "failure_reasons": failures,
        "regions": construction_schema(regions),
        "thresholds": {
            "kappa_max": config.kappa_max,
            "absolute_floor": config.absolute_floor,
            "supported": config.supported_threshold,
            "unsupported_median": config.unsupported_median_threshold,
            "unsupported_maximum": config.unsupported_maximum_threshold,
        },
        "interp_calibration": _path_record(interp_calibration),
        "interp_scored": _path_record(interp_scored),
        "family_seed": family_seed,
        "family_selected_index": family_index,
        "family_candidates": _candidate_records(family_calibration),
        "family_selected_scored": (
            _path_record(family_scored) if family_scored is not None else None
        ),
        "unsupported_seed": unsupported_seed,
        "unsupported_selected_index": unsupported_index,
        "unsupported_candidates": _candidate_records(
            unsupported_calibration
        ),
        "unsupported_selected_scored": (
            _path_record(unsupported_scored)
            if unsupported_scored is not None
            else None
        ),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_full_construction_gate(
    *,
    output_path: Path = DEFAULT_OUTPUT,
    config: R006DConstructionConfig = R006DConstructionConfig(),
    panel_config: R006CConfig = R006CConfig(),
) -> dict[str, Any]:
    regions = chronological_regions(
        t_len=panel_config.t_len,
        window=panel_config.window,
        validation_fraction=panel_config.validation_fraction,
        evaluation_fraction=panel_config.evaluation_fraction,
    )
    records = []
    for layer, rho, a3, eta in required_cells():
        for seed in SEEDS:
            panel = generate_endpoint_panel(
                config=panel_config,
                layer=layer,
                target_rho=rho,
                approximation_target=a3,
                separation_strength=eta,
                seed=seed,
            )
            family_seed = construction_seed(
                seed, layer, rho, a3, eta, "family"
            )
            unsupported_seed = construction_seed(
                seed, layer, rho, a3, eta, "unsupported"
            )
            record = evaluate_panel_construction(
                predictors=panel.estimation.predictors,
                topology=panel.estimation.topology,
                w_ref=panel.W_ref,
                w_interp=panel.W_alt_main,
                regions=regions,
                family_seed=family_seed,
                unsupported_seed=unsupported_seed,
                config=config,
            )
            record["cell"] = {
                "seed": seed,
                "layer": layer,
                "rho": rho,
                "a3": a3,
                "eta": eta,
            }
            records.append(record)

    failed = [record for record in records if record["status"] != "CONSTRUCTION_PASS"]
    artifact = {
        "status": "CONSTRUCTION_PASS" if not failed else "CONSTRUCTION_FAIL",
        "run_type": "PREOUTCOME_CONSTRUCTION_ONLY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "failed_record_count": len(failed),
        "regions": construction_schema(regions),
        "grid": {
            "layers": list(LAYERS),
            "rhos": list(STABILITY_LEVELS),
            "a3_values": list(APPROXIMATION_TARGETS),
            "eta_values": [0.15, 0.45],
            "seeds": list(SEEDS),
        },
        "provenance": {
            "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
            "protocol_sha256": _sha256_file(PROTOCOL_PATH),
            "support_code_sha256": _sha256_file(
                Path(__file__).with_name("r006d_endpoint_support.py")
            ),
            "gate_code_sha256": _sha256_file(Path(__file__)),
        },
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> None:
    arguments = build_argument_parser().parse_args()
    artifact = run_full_construction_gate(output_path=arguments.output)
    print(
        json.dumps(
            {
                "status": artifact["status"],
                "record_count": artifact["record_count"],
                "failed_record_count": artifact["failed_record_count"],
                "output": str(arguments.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
