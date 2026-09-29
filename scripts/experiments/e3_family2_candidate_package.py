"""Build a hash-bound, synthetic-only E3 candidate package without running science.

This module materializes the eight semantically validated pre-outcome artifacts
and a complete candidate document from the frozen E3 design.  It deliberately
does not contain topology generation, estimation, response evaluation,
bootstrap execution, an outcome writer, or a command-line entrypoint.  The
returned package is still ``NOT_AUTHORIZED`` until a separately verified,
candidate-specific production approval exists.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
from typing import Any

import numpy as np

from scripts.experiments import e3_family2_artifact_schemas as artifact_schemas
from scripts.experiments import e3_family2_candidate_ready as candidate_ready
from scripts.experiments import e3_family2_gate_receipt as gate_receipt
from scripts.experiments import e3_family2_preoutcome as preoutcome


ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_SPECIFICATION_PATH = ROOT / "refine-logs" / "e3_family2_inputs" / "synthetic-e3-v4.json"
FROZEN_SYNTHETIC_SPECIFICATION_SHA256 = "e8301d647ce88681347228824a497fde8158f748ab4cdf1208612ed805003cd4"
NATIVE_INTERFACE_PROOF_PATH = ROOT / "refine-logs" / "NCS_E3_NATIVE_ENDPOINT_INTERFACE_PROOF.md"
CORE_PATH = ROOT / "scripts" / "experiments" / "e3_synthetic_core.py"
AUTHORIZED_EXECUTOR_PATH = ROOT / "scripts" / "experiments" / "e3_family2_authorized_executor.py"
GATE_TEST_PATHS = gate_receipt.GATE_TEST_PATHS

CANDIDATE_FILENAME = "candidate.json"
GATE_RECEIPT_FILENAME = "authorization-gate-test-receipt.json"
NODE_ORDER_FILENAME = "synthetic-node-order-manifest.json"
DEPENDENCY_LOCK_FILENAME = "dependency-lock.json"


class CandidatePackageError(RuntimeError):
    """Raised before a candidate-ready package can be materialized."""


@dataclass(frozen=True)
class CandidatePackage:
    """A static package description; it intentionally has no run capability."""

    root: Path
    candidate_path: Path
    candidate_sha256: str
    artifact_paths: Mapping[str, Path]
    status: str = "CANDIDATE_READY_NOT_AUTHORIZED"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = _canonical_json_bytes(value) + b"\n"
    with Path(path).open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _require_existing(path: Path, label: str) -> Path:
    resolved = Path(path).resolve(strict=False)
    if not resolved.is_file():
        raise CandidatePackageError(f"{label} is missing: {resolved}")
    return resolved


def _relative_source_identity(path: Path) -> str:
    resolved = _require_existing(path, "source")
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError as error:
        raise CandidatePackageError("candidate source must remain within the repository") from error
    return f"{relative}@sha256:{_sha256_file(resolved)}"


def _reference(path: Path) -> dict[str, str]:
    resolved = _require_existing(path, "referenced file")
    try:
        reference_path = str(resolved.relative_to(ROOT))
    except ValueError:
        reference_path = str(resolved)
    return {"path": reference_path, "sha256": _sha256_file(resolved)}


def _load_frozen_specification() -> dict[str, Any]:
    specification = _require_existing(SYNTHETIC_SPECIFICATION_PATH, "synthetic specification")
    if not hmac.compare_digest(
        _sha256_file(specification), FROZEN_SYNTHETIC_SPECIFICATION_SHA256
    ):
        raise CandidatePackageError("synthetic specification differs from the exact frozen E3 v4 specification")
    try:
        value = json.loads(specification.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CandidatePackageError("synthetic specification is invalid JSON") from error
    if not isinstance(value, dict):
        raise CandidatePackageError("synthetic specification must be an object")
    required = {
        "input_route",
        "excluded_routes",
        "operator_families",
        "total_time",
        "chronological_partitions",
        "scales",
        "horizons",
        "query_classes",
        "panel_seeds",
        "methods",
        "selection",
        "stability",
        "uncertainty",
    }
    if (
        not required.issubset(value)
        or value.get("schema_version") != "e3-synthetic-input-v4"
        or value["input_route"] != "synthetic_only"
    ):
        raise CandidatePackageError("synthetic specification does not define the frozen E3 route")
    if set(value["excluded_routes"]) != {"RCEP", "NYC", "R006e", "R006f"}:
        raise CandidatePackageError("synthetic specification exclusion set is incomplete")
    if value["operator_families"] != ["family1", "family2"]:
        raise CandidatePackageError("synthetic specification operator families drifted")
    if value["scales"] != [20, 50] or value["horizons"] != [4, 12]:
        raise CandidatePackageError("synthetic specification headline cells drifted")
    if value["panel_seeds"] != list(range(4101, 4121)):
        raise CandidatePackageError("synthetic specification paired seed schedule drifted")
    stability = value["stability"]
    if not isinstance(stability, Mapping) or stability.get("threshold") != 0.98:
        raise CandidatePackageError("synthetic specification stability threshold drifted")
    try:
        artifact_schemas.validate_domain_stability_contract(
            stability["domain_uniform_envelope"]
        )
    except (KeyError, artifact_schemas.ArtifactValidationError) as error:
        raise CandidatePackageError(
            "synthetic specification domain-stability contract drifted"
        ) from error
    uncertainty = value["uncertainty"]
    if (
        not isinstance(uncertainty, Mapping)
        or uncertainty.get("evaluation_target_times") != [143]
        or uncertainty.get("query_classes") != ["in_family_interpolation", "cross_generator"]
        or not isinstance(uncertainty.get("bootstrap_seed_derivation"), str)
    ):
        raise CandidatePackageError("synthetic specification E3-4 evaluation schedule drifted")
    try:
        preoutcome.validate_fixed_rank_bootstrap_history_gate(
            uncertainty["bootstrap_refit_history"]
        )
        artifact_schemas.validate_recursive_bootstrap_procedure(
            uncertainty["bootstrap_procedure"]
        )
    except (
        KeyError,
        preoutcome.ContractError,
        artifact_schemas.ArtifactValidationError,
    ) as error:
        raise CandidatePackageError("synthetic specification bootstrap contract drifted") from error
    expected_boundary = {
        "query_class": "cross_generator",
        "instability": "scientific_failure_boundary",
        "threshold_relaxation": "PROHIBITED",
        "stable_cell_selection": "PROHIBITED",
        "retention": "all_predeclared_cells",
    }
    if stability.get("cross_generator_failure_boundary") != expected_boundary:
        raise CandidatePackageError("synthetic specification cross-generator failure boundary drifted")
    return value


def _node_order_manifest(specification: Mapping[str, Any]) -> dict[str, Any]:
    scales = specification["scales"]
    return {
        "schema_version": "e3-synthetic-node-order-v1",
        "input_route": "synthetic_only",
        "node_orders": {
            str(scale): list(range(int(scale)))
            for scale in scales
        },
    }


def _dependency_lock() -> dict[str, str]:
    return {
        "schema_version": "e3-synthetic-dependency-lock-v1",
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scientific_execution": "NOT_AUTHORIZED",
    }


def _validate_gate_test_receipt(path: Path) -> dict[str, Any]:
    try:
        return gate_receipt.validate_gate_test_receipt(path)
    except gate_receipt.GateReceiptError as error:
        raise CandidatePackageError(
            f"authorization gate test execution receipt refused: {error}"
        ) from error


def _candidate_ready_content(
    *,
    node_order_path: Path,
    gate_test_receipt_path: Path,
    specification: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    content_by_id = {
        artifact_id: artifact_schemas.source_only_content(artifact_id)
        for artifact_id in artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS
    }
    query_contract = content_by_id["family2_query_contract"]
    query_contract["node_order"] = {
        "hash_algorithm": "sha256",
        "node_order_sha256": _sha256_file(node_order_path),
    }
    query_contract["topology_preprocessing"]["normalization"] = (
        "maximum_absolute_row_sum_once_before_fitting_and_evaluation"
    )
    query_contract["lag_order"] = 1
    query_contract["maximum_horizon"] = max(specification["horizons"])
    query_contract["domain_stability"] = specification["stability"][
        "domain_uniform_envelope"
    ]

    registry = content_by_id["comparator_registry"]
    interface = registry["required_interface"]
    native_proof = _reference(NATIVE_INTERFACE_PROOF_PATH)
    registry["registry_state"] = "FROZEN"
    registry["records"] = [
        {
            "comparator_id": "local_structured",
            "role": "native_local_structured",
            "source_identity": _relative_source_identity(CORE_PATH),
            "parameterization": {"windows": specification["methods"]["local_structured"]["windows"]},
            "fit_signature": interface["fit"],
            "evaluate_signature": interface["evaluate"],
            "endpoint_shape": "full_operator_and_finite_horizon_response",
            "native_evaluator_proof": native_proof,
        },
        {
            "comparator_id": "causal_temporal_smoother",
            "role": "causal_temporal_structured",
            "source_identity": _relative_source_identity(CORE_PATH),
            "parameterization": {"alphas": specification["methods"]["causal_temporal_smoother"]["alphas"]},
            "fit_signature": interface["fit"],
            "evaluate_signature": interface["evaluate"],
            "endpoint_shape": "full_operator_and_finite_horizon_response",
            "native_evaluator_proof": native_proof,
        },
        {
            "comparator_id": "fixed_rank_basis",
            "role": "fixed_low_rank_or_basis",
            "source_identity": _relative_source_identity(CORE_PATH),
            "parameterization": {"ranks": specification["methods"]["fixed_rank_basis"]["ranks"]},
            "fit_signature": interface["fit"],
            "evaluate_signature": interface["evaluate"],
            "endpoint_shape": "full_operator_and_finite_horizon_response",
            "native_evaluator_proof": native_proof,
        },
    ]

    content_by_id["tuning_split_manifest"] = {
        "manifest_state": "FROZEN",
        "selection_loss": "observed_topology_one_step_prediction",
        "truth_access": "PROHIBITED",
        "chronological_partitions": {
            "train": {"start_inclusive": 1, "stop_exclusive": 72},
            "validation": {"start_inclusive": 72, "stop_exclusive": 96},
            "evaluation": {"start_inclusive": 96, "stop_exclusive": 144},
        },
        "candidate_lists": {
            "local_structured": specification["methods"]["local_structured"]["windows"],
            "causal_temporal_smoother": specification["methods"]["causal_temporal_smoother"]["alphas"],
            "fixed_rank_basis": specification["methods"]["fixed_rank_basis"]["ranks"],
        },
        "maximum_budget": 3,
        "tie_break": "lowest_candidate_list_index",
        "random_streams": {
            "panel_seed": "SeedSequence(panel_seed, stream_id)",
            "topology": 1,
            "coefficient": 2,
            "innovation": 3,
            "interpolation_query": 4,
            "cross_generator_query": 5,
            "bootstrap": "SeedSequence(bootstrap_seed, panel_seed, target_time)",
        },
        "bootstrap_refit_history": specification["uncertainty"]["bootstrap_refit_history"],
        "bootstrap_procedure": specification["uncertainty"]["bootstrap_procedure"],
        "domain_stability": specification["stability"]["domain_uniform_envelope"],
    }

    gates = content_by_id["authorization_gate_tests"]
    gates["verification_receipt"] = {
        "status": "PASS",
        "receipt": _reference(gate_test_receipt_path),
    }
    content_by_id["duplicate_and_claim_audit_design"]["design_state"] = "FROZEN"
    return content_by_id


def _source_hashes() -> dict[str, str]:
    source_paths = (
        Path(preoutcome.__file__).resolve(),
        Path(artifact_schemas.__file__).resolve(),
        Path(candidate_ready.__file__).resolve(),
        Path(gate_receipt.__file__).resolve(),
        Path(__file__).resolve(),
        CORE_PATH.resolve(),
        AUTHORIZED_EXECUTOR_PATH.resolve(),
        *(path.resolve() for path in GATE_TEST_PATHS),
    )
    return {str(path): _sha256_file(path) for path in source_paths}


def _configuration(specification: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "topology_generators": [
            "directed_sparse_weighted_observed",
            "held_out_weighted_interpolation",
            "held_out_directed_latent_position",
        ],
        "scales": list(specification["scales"]),
        "panel_lengths": [int(specification["total_time"])],
        "horizons": list(specification["horizons"]),
        "seeds": list(specification["panel_seeds"]),
        "split_policy": "chronological_target_time_stop_exclusive",
        "tuning_budget": 3,
        "comparators": [
            "local_structured",
            "causal_temporal_smoother",
            "fixed_rank_basis",
        ],
        "bootstrap_refit_history": specification["uncertainty"]["bootstrap_refit_history"],
        "bootstrap_procedure": specification["uncertainty"]["bootstrap_procedure"],
        "domain_stability": specification["stability"]["domain_uniform_envelope"],
        "cross_generator_failure_boundary": specification["stability"][
            "cross_generator_failure_boundary"
        ],
    }


def build_candidate_ready_package(
    package_root: Path,
    *,
    candidate_id: str,
    quarantine_output_root: Path,
    gate_test_receipt_path: Path,
) -> CandidatePackage:
    """Materialize a new static candidate package without an execution grant.

    ``quarantine_output_root`` is checked for absence and hash-bound, but is
    never created.  The resulting candidate records intentionally pending trust
    evidence; it cannot become a scientific execution authorization merely by
    construction.
    """

    root = Path(package_root).expanduser().resolve(strict=False)
    if root.exists():
        raise CandidatePackageError("candidate package root must be new and absent")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CandidatePackageError("candidate id must be a non-empty string")
    quarantine = Path(quarantine_output_root).expanduser()
    if not quarantine.is_absolute() or quarantine.exists() or "quarantine" not in quarantine.name.casefold():
        raise CandidatePackageError("quarantine root must be a new absolute path labelled quarantine")
    _validate_gate_test_receipt(gate_test_receipt_path)
    specification = _load_frozen_specification()

    root.mkdir(parents=True, mode=0o700)
    try:
        node_order_path = root / NODE_ORDER_FILENAME
        dependency_lock_path = root / DEPENDENCY_LOCK_FILENAME
        _write_new_json(node_order_path, _node_order_manifest(specification))
        _write_new_json(dependency_lock_path, _dependency_lock())
        artifact_paths = candidate_ready.materialize_candidate_ready_artifacts(
            root / "preoutcome-artifacts",
            content_by_id=_candidate_ready_content(
                node_order_path=node_order_path,
                gate_test_receipt_path=gate_test_receipt_path,
                specification=specification,
            ),
        )
        configuration = _configuration(specification)
        candidate = {
            "schema_version": preoutcome.EXECUTION_CANDIDATE_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "execution": {
                "invocation_limit": 1,
                "input_route": "synthetic_only",
                "excluded_routes": ["RCEP", "NYC", "R006e", "R006f"],
                "prohibitions": [
                    "outcome_promotion",
                    "downstream_builds",
                    "manuscript_promotion",
                    "audit_status_changes",
                ],
            },
            "bindings": {
                "runner_sha256": _sha256_file(Path(preoutcome.__file__).resolve()),
                "source_hashes": _source_hashes(),
                "dependency_hashes": {str(dependency_lock_path): _sha256_file(dependency_lock_path)},
                "preoutcome_artifacts": {
                    artifact_id: {"path": str(path), "sha256": _sha256_file(path)}
                    for artifact_id, path in artifact_paths.items()
                },
                "inputs": [
                    {
                        "input_id": "synthetic-e3-specification",
                        "path": str(SYNTHETIC_SPECIFICATION_PATH),
                        "sha256": _sha256_file(SYNTHETIC_SPECIFICATION_PATH),
                    },
                    {
                        "input_id": "synthetic-node-order-manifest",
                        "path": str(node_order_path),
                        "sha256": _sha256_file(node_order_path),
                    },
                ],
                "configuration": configuration,
                "configuration_sha256": artifact_schemas.canonical_sha256(configuration),
                "quarantine_output_root": str(quarantine.resolve(strict=False)),
            },
            "trust_evidence": {
                "pinned_key_id": "workspace-author-via-explicit-exact-sha-instruction",
                "trust_policy_id": "one-time-synthetic-only-e3-v4",
                "detached_signature": "PENDING",
            },
        }
        candidate_path = root / CANDIDATE_FILENAME
        _write_new_json(candidate_path, candidate)
        candidate_sha256 = _sha256_file(candidate_path)
        preoutcome._validate_execution_candidate_shape(candidate)
        bindings = candidate["bindings"]
        preoutcome._validate_source_hashes(bindings)
        preoutcome._validate_dependency_hashes(bindings)
        preoutcome._validate_preoutcome_artifacts(bindings)
        preoutcome._validate_synthetic_inputs(bindings)
        preoutcome._validate_configuration(bindings)
        preoutcome._validate_bootstrap_history_bindings(bindings)
        preoutcome._validate_new_quarantine_root(
            bindings["quarantine_output_root"], quarantine
        )
    except BaseException:
        raise
    return CandidatePackage(root, candidate_path, candidate_sha256, artifact_paths)
