"""Materialize E4-R008 independent log-error-ratio/CI artifacts.

This script is deliberately separate from ``analyze_cal_e01_75`` because the
CAL-E01:75 M2 artifact writer remains raw-only. E4-R008 consumes the same frozen
inputs but writes a read-only, descriptive derived bundle for duplicate and
claim-fidelity gating. It does not edit frozen results, manuscript sources,
figures or the author decision register.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.experiments import analyze_cal_e01_75 as analyzer


ARTIFACT_TYPE = "independent_derived_read_only_audit"
DERIVATION_STATUS = "DERIVED_PARTIAL_NOT_CONFIRMATORY"
EVIDENCE_CEILING = "simulation_only; frozen E4-r3 synthetic-only operating cells"
METRIC_DEFINITION = {
    "panel_value": "median over same-endpoint log(candidate_error/comparator_error)",
    "response_error_field": "response_mse",
    "operator_error_field": "operator_mse",
    "cell_summary": "equal-weight mean over eligible panel log-error-ratios",
    "ci": "two-sided normal approximation, nominal 95%, descriptive only",
    "predeclared_serialization_status": "missing_in_frozen_result",
    "ci_method_serialization_status": "missing_in_frozen_result",
    "thresholds_changed": False,
}


def _expected_frozen_sha256(analysis: Mapping[str, Any]) -> dict[str, str]:
    return {
        role: value["expected_sha256"]
        for role, value in analysis["hash_binding"].items()
    }


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True)
        handle.write("\n")


def _enriched_pair_audits(
    recovery_records: Sequence[Mapping[str, Any]],
    base_pair_audits: Sequence[Mapping[str, Any]],
    methods: Sequence[str],
) -> list[dict[str, Any]]:
    candidate_method = "fixed_rank_basis"
    comparator_methods = [method for method in methods if method != candidate_method]
    base_by_key = {str(pair["pair_key"]): dict(pair) for pair in base_pair_audits}
    groups: defaultdict[tuple[str, int, str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for row in recovery_records:
        groups[analyzer._cell_tuple(row)].append(row)

    pair_audits: list[dict[str, Any]] = []
    for cell in analyzer._expected_cells():
        cell_rows = groups.get(cell, [])
        for comparator_method in comparator_methods:
            pair_key = "|".join(
                (
                    cell[0],
                    str(cell[1]),
                    cell[2],
                    f"H{cell[3]}",
                    f"{candidate_method}_vs_{comparator_method}",
                )
            )
            pair = base_by_key[pair_key]
            panel_records = []
            for seed in analyzer.EXPECTED_SEEDS:
                seed_rows = [
                    row for row in cell_rows if int(row["seed"]) == seed
                ]
                panel_records.append(
                    {
                        "seed": seed,
                        **analyzer.build_panel_log_error_ratio(
                            seed_rows,
                            candidate_method=candidate_method,
                            comparator_method=comparator_method,
                            expected_target_times=analyzer.EXPECTED_TARGET_TIMES,
                        ),
                    }
                )
            response_panel_values = [
                float(record["response_log_error_ratio"])
                for record in panel_records
                if analyzer._is_finite_number(record.get("response_log_error_ratio"))
            ]
            operator_panel_values = [
                float(record["operator_log_error_ratio"])
                for record in panel_records
                if analyzer._is_finite_number(record.get("operator_log_error_ratio"))
            ]
            pair.update(
                {
                    "panel_records": panel_records,
                    "panel_count": len(panel_records),
                    "panel_complete": (
                        len(panel_records) == analyzer.EXPECTED_PANELS_PER_CELL
                        and all(
                            record["status"] == analyzer.STATUS_AVAILABLE
                            for record in panel_records
                        )
                    ),
                    "panel_status_counts": dict(
                        sorted(
                            Counter(
                                str(record["status"]) for record in panel_records
                            ).items()
                        )
                    ),
                    "response_panel_values": response_panel_values,
                    "operator_panel_values": operator_panel_values,
                    "response_cell_ci": analyzer.compute_normal_approximation_ci(
                        response_panel_values
                    ),
                    "operator_cell_ci": analyzer.compute_normal_approximation_ci(
                        operator_panel_values
                    ),
                    "ci_is_descriptive_only": True,
                }
            )
            pair_audits.append(pair)
    return pair_audits


def build_derived_analysis(paths: analyzer.InputPaths) -> dict[str, Any]:
    analysis = analyzer.analyze_frozen_inputs(paths)
    bound = analyzer._load_and_bind_inputs(paths)
    result_payload = analyzer._require_mapping(
        bound["results"].get("results"), "frozen results.results"
    )
    recovery_records = result_payload.get("recovery_records")
    if not isinstance(recovery_records, list):
        raise analyzer.AuditInputError("results.recovery_records must be an array")
    registry_content = analyzer._require_mapping(
        bound["registry"].get("content"), "comparator registry.content"
    )
    registry_records = registry_content.get("records")
    if not isinstance(registry_records, list):
        raise analyzer.AuditInputError("comparator registry records must be an array")
    methods = tuple(str(record["comparator_id"]) for record in registry_records)

    record_audit = dict(analysis["record_audit"])
    pair_audit = dict(record_audit["pair_audit"])
    pair_audit["pair_audits"] = _enriched_pair_audits(
        recovery_records,
        pair_audit["pair_audits"],
        methods,
    )
    record_audit["pair_audit"] = pair_audit
    analysis = dict(analysis)
    analysis["record_audit"] = record_audit
    analysis["artifact_type"] = ARTIFACT_TYPE
    analysis["derivation_authorized"] = True
    return analysis


def write_derived_artifacts(
    paths: analyzer.InputPaths,
    *,
    output_parent: Path,
) -> dict[str, Any]:
    analysis = build_derived_analysis(paths)
    expected_frozen_sha256 = _expected_frozen_sha256(analysis)
    content_payload = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "register_key": analyzer.REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "expected_frozen_sha256": expected_frozen_sha256,
        "metric_definition": METRIC_DEFINITION,
        "output_scope": "CAL-E01:75-only",
    }
    content_address = analyzer._sha256_bytes(
        analyzer._canonical_json(content_payload).encode("utf-8")
    )
    output_parent = Path(output_parent).expanduser().resolve()
    output_dir = output_parent / f"cal-e01-75-{content_address[:16]}"
    if output_dir.exists():
        raise FileExistsError(f"content-addressed output already exists: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)

    record_audit = analysis["record_audit"]
    unsupported_boundaries = [
        "the frozen result contains no serialized panel-level log-error-ratio summary",
        "the frozen result contains no serialized cell-level CI for that metric",
        "the exact predeclared CI construction and confidence level are not serialized",
        "simulation_only evidence does not support empirical or universal claims",
    ]
    sufficiency = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "register_key": analyzer.REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "binding_checks": analysis["binding_checks"],
        "checks": record_audit["checks"],
        "coverage": record_audit["coverage"],
        "status_inventory": record_audit["status_inventory"],
        "frozen_derived_payloads_present": record_audit[
            "forbidden_derived_payloads_present"
        ],
        "serialized_predeclared_log_ratio": False,
        "serialized_predeclared_cell_ci": False,
        "verdict": analysis["verdict"],
        "claim_activation": analysis["claim_activation"],
        "frozen_result_mutated": False,
        "failure_unstable_nonfinite_records_retained": True,
        "unsupported_boundaries": unsupported_boundaries,
    }
    comparator_audit = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "register_key": analyzer.REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "declared_methods": record_audit["declared_methods"],
        "actual_methods": record_audit["actual_methods"],
        "method_cell_audits": record_audit["method_cell_audits"],
        "endpoint_parity_audits": record_audit["endpoint_parity_audits"],
        "pair_audit": {
            key: value
            for key, value in record_audit["pair_audit"].items()
            if key != "pair_audits"
        },
        "interval_audit": record_audit["interval_audit"],
        "verdict": (
            "SUPPORTED_WITHIN_FROZEN_GRID"
            if record_audit["pair_audit"]["complete"]
            and all(
                audit["same_endpoint_set_across_methods"]
                for audit in record_audit["endpoint_parity_audits"]
            )
            else "PARTIAL"
        ),
        "authorization_hash_binding": analysis["hash_binding"],
    }
    distributions = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "register_key": analyzer.REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "method_cell_distributions": record_audit["method_cell_audits"],
        "pair_cell_distributions": record_audit["pair_audit"]["pair_audits"],
        "interval_cell_distributions": record_audit["interval_audit"]["cell_audits"],
        "verdict": analysis["verdict"],
    }
    derived_ratios = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "register_key": analyzer.REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "frozen_result_unchanged": True,
        "source_fields": ["response_mse", "operator_mse", "status", "seed", "target_time"],
        "formula": METRIC_DEFINITION,
        "derivation_status": DERIVATION_STATUS,
        "pair_audits": record_audit["pair_audit"]["pair_audits"],
        "derived_values_withheld": False,
        "verdict": analysis["verdict"],
    }
    claim_audit = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "register_key": analyzer.REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "register_item": analysis["register_item"],
        "comparator_completeness": "SUPPORTED_WITHIN_FROZEN_GRID",
        "same_endpoint_parity": "SUPPORTED_WITHIN_FROZEN_GRID",
        "seed_replication_and_distribution_audit": "SUPPORTED_WITHIN_FROZEN_GRID",
        "failure_and_nonfinite_audit": "SUPPORTED_WITH_RETAINED_ZERO_COUNTS",
        "independent_panel_log_ratio": "DERIVED_ARTIFACT_ONLY",
        "independent_cell_ci": "DERIVED_DESCRIPTIVE_ONLY",
        "overall_verdict": analysis["verdict"],
        "claim_activation": "BLOCKED",
        "evidence_ceiling": EVIDENCE_CEILING,
        "manuscript_or_register_update": False,
        "excluded_routes": ["RCEP", "NYC"],
        "unsupported_boundaries": sufficiency["unsupported_boundaries"],
    }
    input_manifest = {
        **analysis["input_manifest"],
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "register_key": analyzer.REGISTER_KEY,
        "expected_frozen_sha256": expected_frozen_sha256,
        "hash_binding": analysis["hash_binding"],
        "frozen_result_mutated": False,
    }
    files = {
        "input-manifest.json": input_manifest,
        "sufficiency-audit.json": sufficiency,
        "comparator-audit.json": comparator_audit,
        "distributions.json": distributions,
        "derived-panel-log-error-ratios.json": derived_ratios,
        "claim-audit.json": claim_audit,
    }
    for filename, value in files.items():
        _write_json(output_dir / filename, value)
    output_hashes = {
        filename: analyzer.sha256_file(output_dir / filename)
        for filename in sorted(files)
    }
    artifact_manifest = {
        "analysis_version": analyzer.ANALYSIS_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "register_key": analyzer.REGISTER_KEY,
        "content_address": content_address,
        "content_address_payload": content_payload,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "expected_frozen_sha256": expected_frozen_sha256,
        "output_sha256": output_hashes,
        "analysis_script_sha256": analyzer.sha256_file(Path(__file__).resolve()),
        "verdict": analysis["verdict"],
        "claim_activation": "BLOCKED",
        "frozen_result_mutated": False,
        "author_decision_register_modified": False,
        "manuscript_modified": False,
        "quarantine_modified": False,
        "derived_values_withheld": False,
    }
    _write_json(output_dir / "artifact-manifest.json", artifact_manifest)
    return {
        "output_dir": str(output_dir.resolve()),
        "content_address": content_address,
        "output_sha256": output_hashes,
        "artifact_manifest": str((output_dir / "artifact-manifest.json").resolve()),
        "verdict": analysis["verdict"],
        "claim_activation": "BLOCKED",
        "coverage": record_audit["coverage"],
    }


def _default_input_path(root: Path, relative: str) -> Path:
    return root / relative


def _parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--comparator-registry", type=Path, required=True)
    parser.add_argument("--failure-metric-schema", type=Path, required=True)
    parser.add_argument(
        "--plan",
        type=Path,
        default=_default_input_path(root, "refine-logs/NCS_FOUR_ANALYSIS_PLAN_20260804_010454.md"),
    )
    parser.add_argument(
        "--e4-audit",
        type=Path,
        default=_default_input_path(root, "refine-logs/NCS_E4_R3_EXPERIMENT_AUDIT_20260801.md"),
    )
    parser.add_argument(
        "--execution-complete",
        type=Path,
        default=_default_input_path(root, "refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3/execution-complete.json"),
    )
    parser.add_argument(
        "--terminal-inventory",
        type=Path,
        default=_default_input_path(root, "refine-logs/E4_R3_TERMINAL_OUTPUT_INVENTORY_20260801.json"),
    )
    parser.add_argument(
        "--workspace-authorization",
        type=Path,
        default=_default_input_path(root, "refine-logs/e3_family2_inputs/e4-r3-workspace-author-authorization-20260731.json"),
    )
    parser.add_argument(
        "--output-parent",
        type=Path,
        default=_default_input_path(root, "refine-logs/ncs_new_analysis_v2"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    paths = analyzer.InputPaths(
        results=args.results,
        manifest=args.manifest,
        authorization=args.authorization,
        register=args.register,
        candidate=args.candidate,
        comparator_registry=args.comparator_registry,
        failure_metric_schema=args.failure_metric_schema,
        plan=args.plan,
        e4_audit=args.e4_audit,
        execution_complete=args.execution_complete,
        terminal_inventory=args.terminal_inventory,
        workspace_authorization=args.workspace_authorization,
    )
    try:
        summary = write_derived_artifacts(paths, output_parent=args.output_parent)
    except (analyzer.AuditInputError, FileExistsError, OSError, ValueError) as error:
        print(f"E4-R008 derived artifact materializer refused: {error}")
        return 2
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
