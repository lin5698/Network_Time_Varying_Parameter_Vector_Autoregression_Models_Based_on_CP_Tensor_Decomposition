"""One-time, SHA-bound execution of the frozen synthetic E3 evidence route.

The module is intentionally separate from the source-only pre-outcome runner.
It refuses before any synthetic panel, estimator, response evaluator or
quarantine root is created unless an exact workspace-author approval binds the
current candidate SHA-256, complete source/dependency closure, configuration,
pre-outcome artifact package and a new output root.  Successful outputs remain
quarantine material and have no manuscript-writing path.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import sys
from typing import Any

import numpy as np

from scripts.experiments import e3_family2_artifact_schemas as artifact_schemas
from scripts.experiments import e3_family2_preoutcome as preoutcome
from scripts.experiments import e3_synthetic_core as core


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION_SCHEMA_VERSION = "e3-family2-synthetic-execution-authorization-v3"
ACTION = "run_e3_family2_synthetic"
RESULT_SCHEMA_VERSION = "e3-family2-synthetic-quarantine-results-v3"

_AUTHORIZATION_FIELDS = frozenset(
    {
        "schema_version",
        "decision_id",
        "decision",
        "scientific_execution_authorized",
        "authorized_by",
        "authorized_at",
        "action",
        "candidate_sha256",
        "candidate_id",
        "execution",
        "bindings",
        "output_root",
        "overwrite",
        "r006e_outcome_authorized",
        "r006f_outcome_authorized",
        "downstream_builds_authorized",
        "post_run_controls",
    }
)
_AUTHORIZATION_BINDINGS = frozenset(
    {
        "source_hashes_sha256",
        "dependency_hashes_sha256",
        "configuration_sha256",
        "preoutcome_artifacts_sha256",
    }
)
_POST_RUN_CONTROLS = {
    "quarantine_outputs": True,
    "freeze_inventory_sha256_before_value_review": True,
    "independent_claim_audit_required": True,
    "manuscript_promotion_authorized": False,
}
_EXPECTED_TRUST_EVIDENCE = {
    "pinned_key_id": "workspace-author-via-explicit-exact-sha-instruction",
    "trust_policy_id": "one-time-synthetic-only-e3-v4",
    "detached_signature": "PENDING",
}
_CAPABILITY_TOKEN = object()


class AuthorizationError(RuntimeError):
    """Raised before scientific computation when exact authorization fails."""


class ExecutionError(RuntimeError):
    """Raised after a reserved execution begins but cannot complete."""


@dataclass(frozen=True)
class _ExecutionCapability:
    """Opaque result of a successful preflight; not constructible by callers."""

    _token: object
    candidate_sha256: str
    authorization_sha256: str
    decision_id: str
    quarantine_output_root: Path
    specification_snapshot: bytes


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _read_nofollow_snapshot(path: Path, label: str) -> bytes:
    source = Path(path).expanduser()
    if source.is_symlink():
        raise AuthorizationError(f"{label} must not be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(source, flags)
    except OSError as error:
        raise AuthorizationError(f"{label} cannot be opened safely") from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise AuthorizationError(f"{label} must be a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def _load_hashed_json(path: Path | None, expected_sha256: str | None, label: str) -> tuple[dict[str, Any], bytes]:
    if path is None or not _is_sha256(expected_sha256):
        raise AuthorizationError(f"{label} and its exact SHA-256 are required")
    snapshot = _read_nofollow_snapshot(Path(path), label)
    actual_sha256 = _sha256_bytes(snapshot)
    if actual_sha256 != expected_sha256:
        raise AuthorizationError(f"{label} SHA-256 does not match the approved value")
    try:
        value = json.loads(snapshot.decode("utf-8"), parse_constant=_reject_nonfinite_constant)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise AuthorizationError(f"{label} is not valid JSON") from error
    if not isinstance(value, dict):
        raise AuthorizationError(f"{label} must be a JSON object")
    return value, snapshot


def _require_exact_fields(value: Any, fields: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise AuthorizationError(f"{label} has an invalid field set")
    return value


def _validate_candidate_preflight(candidate: Mapping[str, Any], output_root: Path) -> None:
    """Reuse all semantic candidate checks before reading any scientific input."""

    try:
        preoutcome._validate_execution_candidate_shape(candidate)
        bindings = candidate["bindings"]
        preoutcome._validate_source_hashes(bindings)
        preoutcome._validate_dependency_hashes(bindings)
        preoutcome._validate_preoutcome_artifacts(bindings)
        preoutcome._validate_synthetic_inputs(bindings)
        preoutcome._validate_configuration(bindings)
        preoutcome._validate_bootstrap_history_bindings(bindings)
        preoutcome._validate_new_quarantine_root(bindings["quarantine_output_root"], output_root)
    except (preoutcome.AuthorizationError, preoutcome.ContractError, KeyError, OSError, TypeError, ValueError) as error:
        raise AuthorizationError(f"candidate preflight refused: {error}") from error
    if candidate.get("trust_evidence") != _EXPECTED_TRUST_EVIDENCE:
        raise AuthorizationError("candidate trust-evidence policy is not eligible for exact user approval")
    _validate_authorized_executor_binding(bindings)
    _validate_scientific_core_binding(bindings)
    _validate_dependency_environment(bindings)


def _validate_authorized_executor_binding(bindings: Mapping[str, Any]) -> None:
    """Require the exact executor source in the candidate's reviewed closure."""

    source_hashes = bindings.get("source_hashes")
    if not isinstance(source_hashes, Mapping):
        raise AuthorizationError("candidate source closure is unavailable")
    executor_path = Path(__file__).resolve()
    bound_hash: str | None = None
    for raw_path, raw_hash in source_hashes.items():
        if not isinstance(raw_path, str) or not isinstance(raw_hash, str):
            continue
        if Path(raw_path).expanduser().resolve(strict=False) == executor_path:
            bound_hash = raw_hash
            break
    if bound_hash is None:
        raise AuthorizationError("candidate does not bind the authorized E3 executor source")
    current_hash = _sha256_bytes(_read_nofollow_snapshot(executor_path, "authorized E3 executor source"))
    if bound_hash != current_hash:
        raise AuthorizationError("candidate authorized E3 executor hash does not match disk")


def _validate_scientific_core_binding(bindings: Mapping[str, Any]) -> None:
    """Require the exact imported scientific core in the execution closure."""

    source_hashes = bindings.get("source_hashes")
    if not isinstance(source_hashes, Mapping):
        raise AuthorizationError("candidate source closure is unavailable")
    core_path = Path(core.__file__).resolve()
    bound_hash: str | None = None
    for raw_path, raw_hash in source_hashes.items():
        if not isinstance(raw_path, str) or not isinstance(raw_hash, str):
            continue
        if Path(raw_path).expanduser().resolve(strict=False) == core_path:
            bound_hash = raw_hash
            break
    if bound_hash is None:
        raise AuthorizationError("candidate does not bind the E3 scientific core source")
    current_hash = _sha256_bytes(_read_nofollow_snapshot(core_path, "E3 scientific core source"))
    if bound_hash != current_hash:
        raise AuthorizationError("candidate E3 scientific core hash does not match disk")


def _validate_dependency_environment(bindings: Mapping[str, Any]) -> None:
    """Require the single frozen dependency lock to describe this interpreter."""

    dependency_hashes = bindings.get("dependency_hashes")
    if not isinstance(dependency_hashes, Mapping) or len(dependency_hashes) != 1:
        raise AuthorizationError("candidate must bind exactly one dependency lock")
    raw_path, expected_hash = next(iter(dependency_hashes.items()))
    if not isinstance(raw_path, str) or not isinstance(expected_hash, str):
        raise AuthorizationError("candidate dependency-lock binding is invalid")
    lock_path = Path(raw_path).expanduser()
    if lock_path.name != "dependency-lock.json":
        raise AuthorizationError("candidate dependency lock has an unexpected filename")
    snapshot = _read_nofollow_snapshot(lock_path, "bound dependency lock")
    if _sha256_bytes(snapshot) != expected_hash:
        raise AuthorizationError("bound dependency lock changed after preflight")
    try:
        lock = json.loads(snapshot.decode("utf-8"), parse_constant=_reject_nonfinite_constant)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise AuthorizationError("bound dependency lock is invalid JSON") from error
    expected_lock = {
        "schema_version": "e3-synthetic-dependency-lock-v1",
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scientific_execution": "NOT_AUTHORIZED",
    }
    if lock != expected_lock:
        raise AuthorizationError("candidate dependency lock does not match the current runtime")


def _validate_authorization(
    authorization: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
    candidate_sha256: str,
    output_root: Path,
) -> None:
    approval = _require_exact_fields(authorization, _AUTHORIZATION_FIELDS, "execution authorization")
    if approval["schema_version"] != AUTHORIZATION_SCHEMA_VERSION:
        raise AuthorizationError("execution authorization schema version is invalid")
    if approval["decision"] != "AUTHORIZED" or approval["scientific_execution_authorized"] is not True:
        raise AuthorizationError("execution authorization does not permit science")
    if not all(
        isinstance(approval[field], str) and approval[field]
        for field in ("decision_id", "authorized_by", "authorized_at", "candidate_id")
    ):
        raise AuthorizationError("execution authorization identity is incomplete")
    if approval["action"] != ACTION:
        raise AuthorizationError("execution authorization action is invalid")
    if approval["candidate_id"] != candidate["candidate_id"] or approval["candidate_sha256"] != candidate_sha256:
        raise AuthorizationError("execution authorization is not bound to the exact candidate")
    if approval["execution"] != candidate["execution"]:
        raise AuthorizationError("execution authorization scope differs from the candidate")

    bindings = _require_exact_fields(approval["bindings"], _AUTHORIZATION_BINDINGS, "authorization bindings")
    candidate_bindings = candidate["bindings"]
    expected_bindings = {
        "source_hashes_sha256": artifact_schemas.canonical_sha256(candidate_bindings["source_hashes"]),
        "dependency_hashes_sha256": artifact_schemas.canonical_sha256(candidate_bindings["dependency_hashes"]),
        "configuration_sha256": candidate_bindings["configuration_sha256"],
        "preoutcome_artifacts_sha256": artifact_schemas.canonical_sha256(
            candidate_bindings["preoutcome_artifacts"]
        ),
    }
    if dict(bindings) != expected_bindings:
        raise AuthorizationError("execution authorization bindings differ from the candidate")
    if approval["overwrite"] != "deny":
        raise AuthorizationError("execution authorization must deny overwrite")
    if (
        approval["r006e_outcome_authorized"] is not False
        or approval["r006f_outcome_authorized"] is not False
        or approval["downstream_builds_authorized"] is not False
    ):
        raise AuthorizationError("execution authorization attempts to broaden the allowed scope")
    if approval["post_run_controls"] != _POST_RUN_CONTROLS:
        raise AuthorizationError("execution authorization post-run controls are invalid")
    requested = Path(approval["output_root"]).expanduser()
    if not requested.is_absolute() or requested.resolve(strict=False) != output_root.resolve(strict=False):
        raise AuthorizationError("execution authorization output root differs from the requested root")
    if requested.exists():
        raise AuthorizationError("execution authorization output root must be new and absent")


def prepare_authorized_execution(
    *,
    candidate_path: Path | None,
    expected_candidate_sha256: str | None,
    authorization_path: Path | None,
    expected_authorization_sha256: str | None,
    expected_quarantine_root: Path,
) -> _ExecutionCapability:
    """Validate a one-time scope before any generator, estimator or output root.

    The approval checksum is an integrity binding for a workspace-author's
    separately recorded exact-SHA instruction. It is not represented as a
    cryptographic signature or a general-purpose trust root.
    """

    candidate, candidate_snapshot = _load_hashed_json(
        candidate_path, expected_candidate_sha256, "execution candidate"
    )
    authorization, authorization_snapshot = _load_hashed_json(
        authorization_path, expected_authorization_sha256, "execution authorization"
    )
    output_root = Path(expected_quarantine_root).expanduser().resolve(strict=False)
    _validate_candidate_preflight(candidate, output_root)
    _validate_authorization(
        authorization,
        candidate=candidate,
        candidate_sha256=_sha256_bytes(candidate_snapshot),
        output_root=output_root,
    )
    specification = _bound_synthetic_specification(candidate)
    _validate_bound_node_order_manifest(candidate, specification)
    _validate_configuration_matches_specification(candidate, specification)
    _validate_bound_bootstrap_history_manifest(candidate, specification)
    return _ExecutionCapability(
        _CAPABILITY_TOKEN,
        _sha256_bytes(candidate_snapshot),
        _sha256_bytes(authorization_snapshot),
        str(authorization["decision_id"]),
        output_root,
        _canonical_json_bytes(specification),
    )


def _write_new_json(path: Path, value: Any) -> None:
    payload = _canonical_json_bytes(value) + b"\n"
    with Path(path).open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _reserve_quarantine_root(root: Path) -> None:
    if root.exists() or root.is_symlink():
        raise ExecutionError("authorized quarantine root was claimed before reservation")
    root.parent.mkdir(parents=True, exist_ok=True)
    try:
        root.mkdir(mode=0o700)
    except FileExistsError as error:
        raise ExecutionError("authorized quarantine root was claimed during reservation") from error


def _bound_synthetic_specification(candidate: Mapping[str, Any]) -> dict[str, Any]:
    bindings = candidate["bindings"]
    input_rows = bindings["inputs"]
    matching = [row for row in input_rows if row.get("input_id") == "synthetic-e3-specification"]
    if len(matching) != 1:
        raise ExecutionError("candidate does not bind exactly one synthetic E3 specification")
    row = matching[0]
    path = Path(row["path"]).expanduser()
    expected_path = ROOT / "refine-logs" / "e3_family2_inputs" / "synthetic-e3-v4.json"
    if path.resolve(strict=False) != expected_path.resolve():
        raise ExecutionError("candidate synthetic specification path is not the frozen E3 v4 input")
    snapshot = _read_nofollow_snapshot(path, "bound synthetic specification")
    if _sha256_bytes(snapshot) != row["sha256"]:
        raise ExecutionError("bound synthetic specification changed after preflight")
    try:
        specification = json.loads(
            snapshot.decode("utf-8"), parse_constant=_reject_nonfinite_constant
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise ExecutionError("bound synthetic specification is invalid JSON") from error
    if not isinstance(specification, dict):
        raise ExecutionError("bound synthetic specification is not an object")
    if specification != _expected_frozen_specification():
        raise ExecutionError("bound synthetic specification differs from frozen E3 v4")
    return specification


def _expected_frozen_specification() -> dict[str, Any]:
    """Return the full predeclared E3 v4 contract accepted by this executor."""

    return {
        "schema_version": "e3-synthetic-input-v4",
        "lifecycle": "PRE_OUTCOME",
        "input_route": "synthetic_only",
        "excluded_routes": ["RCEP", "NYC", "R006e", "R006f"],
        "operator_families": ["family1", "family2"],
        "operator_forms": {
            "family1": "A_plus_BW_with_diagonal_blocks",
            "family2": "C0_plus_C1W_plus_C2W2_with_diagonal_blocks",
        },
        "topology_preprocessing": {
            "raw_zero_diagonal": True,
            "normalization": "maximum_absolute_row_sum_once_before_fitting_and_evaluation",
            "square": "W@W",
            "post_square_reprocessing": "PROHIBITED",
        },
        "endpoint": "full_operator_and_finite_horizon_response",
        "lag_order": 1,
        "shock_map": "identity",
        "total_time": 144,
        "chronological_partitions": {
            "train": {"start": 1, "stop": 72},
            "validation": {"start": 72, "stop": 96},
            "evaluation": {"start": 96, "stop": 144},
        },
        "scales": [20, 50],
        "horizons": [4, 12],
        "query_classes": ["in_family_interpolation", "cross_generator"],
        "panel_seeds": list(range(4101, 4121)),
        "methods": {
            "local_structured": {"windows": [8, 12, 16]},
            "causal_temporal_smoother": {"alphas": [0.25, 0.55, 0.85]},
            "fixed_rank_basis": {"ranks": [1, 2, 3]},
        },
        "selection": {
            "loss": "observed_topology_one_step_prediction",
            "maximum_trials_per_method": 3,
            "tie_break": "lowest_candidate_list_index",
            "held_out_topology_truth_access": "PROHIBITED",
        },
        "stability": {
            "threshold": 0.98,
            "domain_uniform_envelope": {
                "value": 0.90,
                "norm": "nodewise_l1_over_retained_blocks",
                "application_stage": "after_fit_before_query",
                "query_topology_access": "PROHIBITED",
                "applies_to": [
                    "selection",
                    "evaluation",
                    "recursive_bootstrap_refit",
                    "bootstrap_retuning",
                ],
                "topology_domain": "maximum_absolute_row_sum_at_most_one",
            },
            "retain_statuses": [
                "AVAILABLE",
                "OUTSIDE_TARGET",
                "NONCONVERGED",
                "NONFINITE",
                "UNSTABLE",
            ],
            "cross_generator_failure_boundary": {
                "query_class": "cross_generator",
                "instability": "scientific_failure_boundary",
                "threshold_relaxation": "PROHIBITED",
                "stable_cell_selection": "PROHIBITED",
                "retention": "all_predeclared_cells",
            },
        },
        "uncertainty": {
            "replicates": 80,
            "block_length": 5,
            "confidence": 0.95,
            "confidence_allocation": "simultaneous_max_deviation_over_N_by_N_response_at_H4",
            "bootstrap_procedure": {
                "method": "recursive_residual_circular_moving_block_bootstrap",
                "initial_history": "observed_prefix_before_rank_aware_start",
                "lag_feature_source": "pseudo_response_history",
                "parameter_selection": "validation_loss_on_each_pseudo_series",
                "retune_inside_bootstrap": True,
                "retune_candidate_list": [1, 2, 3],
                "failure_retention": "all_replicates",
            },
            "evaluation_target_times": [143],
            "query_classes": ["in_family_interpolation", "cross_generator"],
            "bootstrap_seed_derivation": "620001_plus_family_index_times_100000_plus_scale_plus_panel_seed_plus_query_index_times_1000_plus_target_time",
            "bootstrap_refit_history": {
                "method": "fixed_rank_basis",
                "local_window": 12,
                "minimum_local_estimates": 2,
                "allowed_ranks": [1, 2, 3],
                "minimum_valid_refit_opportunities_per_allowed_rank": 2,
                "evaluation_target_times": [143],
                "rank_aware_start_times": {"1": 14, "2": 14, "3": 15},
            },
        },
        "scientific_execution": "NOT_AUTHORIZED",
    }


def _configuration_from_specification(specification: Mapping[str, Any]) -> dict[str, Any]:
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
        "tuning_budget": int(specification["selection"]["maximum_trials_per_method"]),
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


def _validate_bound_node_order_manifest(
    candidate: Mapping[str, Any], specification: Mapping[str, Any]
) -> None:
    """Bind the reviewed node order to both the candidate input and query contract."""

    input_rows = candidate["bindings"]["inputs"]
    expected_input_ids = {"synthetic-e3-specification", "synthetic-node-order-manifest"}
    if not isinstance(input_rows, list) or {
        row.get("input_id") for row in input_rows if isinstance(row, Mapping)
    } != expected_input_ids:
        raise AuthorizationError("candidate synthetic input inventory differs from the frozen E3 route")
    matching = [
        row for row in input_rows if row.get("input_id") == "synthetic-node-order-manifest"
    ]
    if len(matching) != 1:
        raise AuthorizationError("candidate does not bind exactly one synthetic node-order manifest")
    node_row = matching[0]
    node_path = Path(node_row["path"]).expanduser()
    if node_path.name != "synthetic-node-order-manifest.json":
        raise AuthorizationError("candidate node-order manifest has an unexpected filename")
    snapshot = _read_nofollow_snapshot(node_path, "bound synthetic node-order manifest")
    if _sha256_bytes(snapshot) != node_row["sha256"]:
        raise AuthorizationError("bound synthetic node-order manifest changed after preflight")
    try:
        manifest = json.loads(snapshot.decode("utf-8"), parse_constant=_reject_nonfinite_constant)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise AuthorizationError("bound synthetic node-order manifest is invalid JSON") from error
    expected_manifest = {
        "schema_version": "e3-synthetic-node-order-v1",
        "input_route": "synthetic_only",
        "node_orders": {
            str(scale): list(range(int(scale))) for scale in specification["scales"]
        },
    }
    if manifest != expected_manifest:
        raise AuthorizationError("bound synthetic node-order manifest differs from frozen E3 v4")

    query_binding = candidate["bindings"]["preoutcome_artifacts"]["family2_query_contract"]
    query_snapshot = _read_nofollow_snapshot(
        Path(query_binding["path"]), "bound Family-2 query contract"
    )
    if _sha256_bytes(query_snapshot) != query_binding["sha256"]:
        raise AuthorizationError("bound Family-2 query contract changed after preflight")
    try:
        query_contract = json.loads(
            query_snapshot.decode("utf-8"), parse_constant=_reject_nonfinite_constant
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise AuthorizationError("bound Family-2 query contract is invalid JSON") from error
    try:
        contract_node_hash = query_contract["content"]["node_order"]["node_order_sha256"]
    except (KeyError, TypeError) as error:
        raise AuthorizationError("bound Family-2 query contract lacks a node-order binding") from error
    if contract_node_hash != node_row["sha256"]:
        raise AuthorizationError("Family-2 query contract node order differs from the candidate input")


def _validate_configuration_matches_specification(
    candidate: Mapping[str, Any], specification: Mapping[str, Any]
) -> None:
    expected = _configuration_from_specification(specification)
    bindings = candidate["bindings"]
    if bindings["configuration"] != expected:
        raise AuthorizationError("candidate configuration does not match the frozen E3 specification")
    if bindings["configuration_sha256"] != artifact_schemas.canonical_sha256(expected):
        raise AuthorizationError("candidate configuration hash does not match the frozen E3 specification")


def _validate_bound_bootstrap_history_manifest(
    candidate: Mapping[str, Any], specification: Mapping[str, Any]
) -> None:
    """Require the tuning artifact to bind the v4 history and stability contract."""

    binding = candidate["bindings"]["preoutcome_artifacts"]["tuning_split_manifest"]
    snapshot = _read_nofollow_snapshot(
        Path(binding["path"]), "bound bootstrap-history tuning manifest"
    )
    if _sha256_bytes(snapshot) != binding["sha256"]:
        raise AuthorizationError("bound bootstrap-history tuning manifest changed after preflight")
    try:
        artifact = json.loads(snapshot.decode("utf-8"), parse_constant=_reject_nonfinite_constant)
        gate = artifact["content"]["bootstrap_refit_history"]
        procedure = artifact["content"]["bootstrap_procedure"]
        domain_stability = artifact["content"]["domain_stability"]
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise AuthorizationError("bound bootstrap-history tuning manifest is invalid") from error
    expected_gate = specification["uncertainty"]["bootstrap_refit_history"]
    if gate != expected_gate:
        raise AuthorizationError("bound bootstrap-history gate differs from frozen E3 v4")
    expected_procedure = specification["uncertainty"]["bootstrap_procedure"]
    if procedure != expected_procedure:
        raise AuthorizationError("bound bootstrap procedure differs from frozen E3 v4")
    expected_stability = specification["stability"]["domain_uniform_envelope"]
    if domain_stability != expected_stability:
        raise AuthorizationError("bound domain stability differs from frozen E3 v4")


def _config_from_specification(specification: Mapping[str, Any], n: int) -> core.E3SyntheticConfig:
    methods = specification["methods"]
    stability = specification["stability"]
    uncertainty = specification["uncertainty"]
    return core.E3SyntheticConfig(
        n=n,
        total_time=int(specification["total_time"]),
        train_stop=int(specification["chronological_partitions"]["train"]["stop"]),
        validation_stop=int(specification["chronological_partitions"]["validation"]["stop"]),
        evaluation_stop=int(specification["chronological_partitions"]["evaluation"]["stop"]),
        horizons=tuple(int(value) for value in specification["horizons"]),
        local_windows=tuple(int(value) for value in methods["local_structured"]["windows"]),
        smoother_alphas=tuple(float(value) for value in methods["causal_temporal_smoother"]["alphas"]),
        basis_ranks=tuple(int(value) for value in methods["fixed_rank_basis"]["ranks"]),
        stability_envelope=float(stability["domain_uniform_envelope"]["value"]),
        stability_threshold=float(stability["threshold"]),
        bootstrap_replicates=int(uncertainty["replicates"]),
        bootstrap_block_length=int(uncertainty["block_length"]),
    )


def _bootstrap_seed(family_index: int, scale: int, panel_seed: int, query_index: int, target_time: int) -> int:
    return 620001 + family_index * 100000 + scale + panel_seed + query_index * 1000 + target_time


def _serialise_recovery_records(records: Sequence[core.EvaluationRecord]) -> list[dict[str, Any]]:
    return [asdict(record) for record in records]


def _pairwise_summaries(records: Sequence[core.EvaluationRecord]) -> dict[str, Mapping[str, Any]]:
    summaries: dict[str, Mapping[str, Any]] = {}
    for family in (core.FAMILY1, core.FAMILY2):
        for scale in (20, 50):
            for query_class in core.QUERY_CLASSES:
                for horizon in (4, 12):
                    cell = [
                        record
                        for record in records
                        if (
                            record.family == family
                            and record.n == scale
                            and record.query_class == query_class
                            and record.horizon == horizon
                        )
                    ]
                    for comparator in ("local_structured", "causal_temporal_smoother"):
                        key = f"{family}|{scale}|{query_class}|H{horizon}|fixed_rank_basis_vs_{comparator}"
                        summaries[key] = core.paired_common_completion(
                            cell,
                            candidate_method="fixed_rank_basis",
                            comparator_method=comparator,
                        )
    return summaries


def _interval_summaries(records: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    """Report E3-4 cells without conditioning coverage on successful panels."""

    buckets: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        key = "|".join((str(record["family"]), str(record["n"]), str(record["query_class"])))
        buckets.setdefault(key, []).append(record)
    summaries: dict[str, Mapping[str, Any]] = {}
    for key, group in buckets.items():
        status_counts = {status: 0 for status in sorted(core.STATUS_SCHEMA)}
        bootstrap_status_counts = {status: 0 for status in sorted(core.STATUS_SCHEMA)}
        for record in group:
            status_counts[str(record["status"])] += 1
            for status, count in record["bootstrap_status_counts"].items():
                bootstrap_status_counts[str(status)] += int(count)
        available = [record for record in group if record["status"] == core.STATUS_AVAILABLE]
        all_available = len(available) == len(group)
        raw_errors = [
            float(record["raw_response_mse"])
            for record in group
            if record["raw_response_mse"] is not None
        ]
        estimated_radii = [
            float(record["estimated_spectral_radius"])
            for record in group
            if record["estimated_spectral_radius"] is not None
        ]
        truth_radii = [
            float(record["truth_spectral_radius"])
            for record in group
            if record["truth_spectral_radius"] is not None
        ]
        summaries[key] = {
            "declared_panel_records": len(group),
            "distinct_panels": len({int(record["seed"]) for record in group}),
            "available_interval_records": len(available),
            "status_counts": status_counts,
            "all_declared_intervals_available": all_available,
            "coverage": (
                float(sum(float(record["coverage"]) for record in available) / len(available))
                if all_available
                else None
            ),
            "mean_interval_width": (
                float(sum(float(record["mean_interval_width"]) for record in available) / len(available))
                if all_available
                else None
            ),
            "raw_response_mse_mean": (
                float(sum(raw_errors) / len(raw_errors)) if raw_errors else None
            ),
            "raw_response_mse_records": len(raw_errors),
            "stability_qualified_response_mse_mean": (
                float(
                    sum(float(record["stability_qualified_response_mse"]) for record in available)
                    / len(available)
                )
                if all_available
                else None
            ),
            "estimated_spectral_radius_max": max(estimated_radii) if estimated_radii else None,
            "truth_spectral_radius_max": max(truth_radii) if truth_radii else None,
            "requested_bootstrap_replicates": sorted(
                {int(record["requested_replicates"]) for record in group}
            ),
            "completed_bootstrap_replicates": sum(
                int(record["completed_replicates"]) for record in group
            ),
            "bootstrap_status_counts": bootstrap_status_counts,
        }
    return summaries


def _run_frozen_e3(specification: Mapping[str, Any]) -> dict[str, Any]:
    """Execute E3-1 through E3-4 only after an output root is reserved."""

    fixture_report = core.require_e3_1_gate()
    recovery_records: list[core.EvaluationRecord] = []
    interval_records: list[dict[str, Any]] = []
    for family_index, family in enumerate((core.FAMILY1, core.FAMILY2), start=1):
        for scale in specification["scales"]:
            config = _config_from_specification(specification, int(scale))
            for panel_seed in specification["panel_seeds"]:
                panel = core.make_synthetic_panel(family, config, int(panel_seed))
                recovery_records.extend(core.evaluate_panel_recovery(panel))
                selection = core.select_hyperparameter(
                    core.fit_data_from_panel(panel), "fixed_rank_basis"
                )
                for query_index, query_class in enumerate(specification["uncertainty"]["query_classes"], start=1):
                    for target_time in specification["uncertainty"]["evaluation_target_times"]:
                        interval = core.simultaneous_response_interval(
                            panel,
                            selection,
                            query_class,
                            int(target_time),
                            bootstrap_seed=_bootstrap_seed(
                                family_index,
                                int(scale),
                                int(panel_seed),
                                query_index,
                                int(target_time),
                            ),
                        )
                        interval_records.append(
                            {
                                "family": family,
                                "n": int(scale),
                                "seed": int(panel_seed),
                                "method": "fixed_rank_basis",
                                "query_class": query_class,
                                "target_time": int(target_time),
                                "horizon": 4,
                                "selected_hyperparameter": selection.selected,
                                "selection_status": selection.status,
                                "selection_validation_loss": selection.validation_loss,
                                **interval,
                            }
                        )
    return {
        "fixture_report": fixture_report,
        "recovery_records": _serialise_recovery_records(recovery_records),
        "recovery_summary": core.aggregate_recovery_records(recovery_records),
        "paired_common_completion": _pairwise_summaries(recovery_records),
        "interval_records": interval_records,
        "interval_summary": _interval_summaries(interval_records),
    }


def _capability_specification(capability: _ExecutionCapability) -> Mapping[str, Any]:
    """Recover the immutable preflight snapshot immediately before computation."""

    try:
        specification = json.loads(
            capability.specification_snapshot.decode("utf-8"),
            parse_constant=_reject_nonfinite_constant,
        )
    except (AttributeError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise ExecutionError("authorized E3 capability specification is invalid") from error
    if specification != _expected_frozen_specification():
        raise ExecutionError("authorized E3 capability specification differs from frozen E3 v4")
    return specification


def execute_authorized_e3(capability: object) -> Path:
    """Reserve the authorized root and run the frozen E3 grid once.

    Callers cannot obtain a usable capability without an exact author-approved
    candidate and authorization SHA.  An exception after reservation leaves the
    quarantine root in place, preventing automatic retry or root reuse.
    """

    if not isinstance(capability, _ExecutionCapability) or capability._token is not _CAPABILITY_TOKEN:
        raise AuthorizationError("E3 execution requires a capability from successful exact-SHA preflight")
    root = capability.quarantine_output_root
    _reserve_quarantine_root(root)
    _write_new_json(
        root / "execution-manifest.json",
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "status": "RUNNING_QUARANTINE_ONLY",
            "candidate_sha256": capability.candidate_sha256,
            "authorization_sha256": capability.authorization_sha256,
            "decision_id": capability.decision_id,
            "scientific_execution": "AUTHORIZED_SYNTHETIC_ONLY",
            "promotion": "PROHIBITED",
        },
    )
    try:
        outputs = _run_frozen_e3(_capability_specification(capability))
        _write_new_json(
            root / "e3-results.json",
            {
                "schema_version": RESULT_SCHEMA_VERSION,
                "status": "COMPLETE_QUARANTINE_ONLY",
                "candidate_sha256": capability.candidate_sha256,
                "authorization_sha256": capability.authorization_sha256,
                "results": outputs,
                "promotion": "PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT",
            },
        )
        _write_new_json(
            root / "execution-complete.json",
            {
                "schema_version": RESULT_SCHEMA_VERSION,
                "status": "COMPLETE_QUARANTINE_ONLY",
                "candidate_sha256": capability.candidate_sha256,
                "authorization_sha256": capability.authorization_sha256,
                "promotion": "PROHIBITED",
            },
        )
    except BaseException as error:
        _write_new_json(
            root / "execution-failure.json",
            {
                "schema_version": RESULT_SCHEMA_VERSION,
                "status": "FAILED_QUARANTINE_ONLY",
                "candidate_sha256": capability.candidate_sha256,
                "authorization_sha256": capability.authorization_sha256,
                "error_type": type(error).__name__,
                "error": str(error),
                "promotion": "PROHIBITED",
            },
        )
        raise
    return root


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="e3-family2-authorized-executor")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--authorization-sha256", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    try:
        capability = prepare_authorized_execution(
            candidate_path=arguments.candidate,
            expected_candidate_sha256=arguments.candidate_sha256,
            authorization_path=arguments.authorization,
            expected_authorization_sha256=arguments.authorization_sha256,
            expected_quarantine_root=arguments.output_root,
        )
        root = execute_authorized_e3(capability)
    except (AuthorizationError, ExecutionError, OSError, ValueError) as error:
        print(f"E3 execution refused or failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "COMPLETE_QUARANTINE_ONLY", "output_root": str(root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
