"""Fail-closed, source-only pre-outcome boundary for NCS E3 Family-2.

This module deliberately contains no topology generation, fitting, response
evaluation, simulation metrics, or scientific output writer.  It can only
construct and verify static pre-outcome contracts.  A future execution engine
must be separately authorized and reviewed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, ClassVar

from scripts.experiments import e3_family2_artifact_schemas as artifact_schemas


ROOT = Path(__file__).resolve().parents[2]
FAMILY2_CONTRACT_PATH = ROOT / "refine-logs" / "NCS_E3_FAMILY2_CANDIDATE_CONTRACT.md"
ARTIFACT_NAME = "e3_family2_preoutcome.json"
SCHEMA_VERSION = "e3-family2-preoutcome-v1"
EXECUTION_CANDIDATE_SCHEMA_VERSION = "e3-family2-execution-candidate-v4"

STATUS_AVAILABLE = "AVAILABLE"
STATUS_OUTSIDE_TARGET = "OUTSIDE_TARGET"
STATUS_NONCONVERGED = "NONCONVERGED"
STATUS_NONFINITE = "NONFINITE"
STATUS_UNSTABLE = "UNSTABLE"
NOT_AUTHORIZED = artifact_schemas.NOT_AUTHORIZED

_ARTIFACT_FIELDS = frozenset(
    {
        "schema_version",
        "run_type",
        "status",
        "scientific_execution",
        "contract",
        "fixtures",
        "comparator_rules",
        "preoutcome_artifact_inventory",
        "provenance",
        "artifact_sha256",
    }
)
_FIXTURE_NAMES = (
    "f1_negative",
    "f2_unrestricted_negative",
    "f2_diagonal_negative",
    "f2_diagonal_positive",
    "non_equivalence",
)
REQUIRED_PREOUTCOME_ARTIFACT_IDS = artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS
_CANDIDATE_FIELDS = frozenset(
    {
        "schema_version",
        "candidate_id",
        "execution",
        "bindings",
        "trust_evidence",
    }
)
_EXECUTION_FIELDS = frozenset(
    {"invocation_limit", "input_route", "excluded_routes", "prohibitions"}
)
_BINDING_FIELDS = frozenset(
    {
        "runner_sha256",
        "source_hashes",
        "dependency_hashes",
        "preoutcome_artifacts",
        "inputs",
        "configuration",
        "configuration_sha256",
        "quarantine_output_root",
    }
)
_PREOUTCOME_BINDING_FIELDS = frozenset({"path", "sha256"})
_INPUT_BINDING_FIELDS = frozenset({"input_id", "path", "sha256"})
_TRUST_EVIDENCE_FIELDS = frozenset(
    {"pinned_key_id", "trust_policy_id", "detached_signature"}
)
_CONFIGURATION_FIELDS = frozenset(
    {
        "topology_generators",
        "scales",
        "panel_lengths",
        "horizons",
        "seeds",
        "split_policy",
        "tuning_budget",
        "comparators",
        "bootstrap_refit_history",
        "bootstrap_procedure",
        "domain_stability",
        "cross_generator_failure_boundary",
    }
)
_CROSS_GENERATOR_FAILURE_BOUNDARY = {
    "query_class": "cross_generator",
    "instability": "scientific_failure_boundary",
    "threshold_relaxation": "PROHIBITED",
    "stable_cell_selection": "PROHIBITED",
    "retention": "all_predeclared_cells",
}
_EXCLUDED_ROUTES = frozenset({"RCEP", "NYC", "R006e", "R006f"})
_REQUIRED_PROHIBITIONS = frozenset(
    {
        "outcome_promotion",
        "downstream_builds",
        "manuscript_promotion",
        "audit_status_changes",
    }
)


class AuthorizationError(RuntimeError):
    """Raised before any scientific operation when authorization is incomplete."""


class ContractError(RuntimeError):
    """Raised when a source-only E3 pre-outcome contract is malformed."""


class ComparatorEligibilityError(ContractError):
    """Raised before fitting when a candidate cannot natively answer the endpoint."""


def write_source_only_preoutcome_artifacts(artifact_root: Path) -> dict[str, Path]:
    """Write the complete source-only artifact package without authorizing science."""

    try:
        return artifact_schemas.write_source_only_preoutcome_artifacts(artifact_root)
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"source-only pre-outcome package refused: {error}") from error


def verify_preoutcome_artifact(
    artifact_path: Path,
    *,
    artifact_id: str,
    require_candidate_ready: bool = False,
) -> dict[str, Any]:
    """Verify one versioned artifact's hash, schema and semantic contract."""

    try:
        return artifact_schemas.verify_preoutcome_artifact(
            artifact_path,
            artifact_id=artifact_id,
            require_candidate_ready=require_candidate_ready,
        )
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"pre-outcome artifact {artifact_id} refused: {error}") from error


def validate_fixed_rank_bootstrap_history_gate(contract: Any) -> Mapping[str, Any]:
    """Expose the static E3-4 history gate at the pre-outcome boundary."""

    try:
        return artifact_schemas.validate_fixed_rank_bootstrap_history_gate(contract)
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"fixed-rank bootstrap history gate refused: {error}") from error


@dataclass(frozen=True)
class TestOnlyFixtureTrustVerifier:
    """Legacy fixture-verifier record retained without executable authority."""

    verify_fixture: Callable[[Mapping[str, Any], bytes], bool]
    test_only: ClassVar[bool] = True

    def verify(self, evidence: Mapping[str, Any], signed_payload: bytes) -> bool:
        """Refuse before invoking a caller-supplied callback.

        The source-only build has no trusted fixture-verification boundary.
        Retaining this method prevents an older caller from silently gaining a
        callback execution surface while a later, deployment-owned verifier is
        designed and independently reviewed.
        """

        del evidence, signed_payload
        raise AuthorizationError(
            "fixture trust verification is unavailable in the source-only build"
        )


@dataclass(frozen=True)
class ConfiguredTrustVerifier:
    """Legacy verifier record retained without production trust authority."""

    pinned_key_id: str
    trust_policy_id: str
    verify_detached: Callable[[Mapping[str, Any], bytes], bool]

    def verify(self, evidence: Mapping[str, Any], signed_payload: bytes) -> bool:
        """Refuse before invoking a caller-supplied detached verifier.

        Pinned metadata alone does not establish deployment-owned trust.  A
        future production implementation must replace this inert compatibility
        record with a separately reviewed trust adapter.
        """

        del evidence, signed_payload
        raise AuthorizationError(
            "configured trust verification is unavailable in the source-only build"
        )


@dataclass(frozen=True)
class ScientificEntrypoints:
    """Future scientific hooks retained only so the gate can prove non-invocation."""

    topology_generator: Callable[..., Any]
    estimator: Callable[..., Any]
    response_evaluator: Callable[..., Any]


@dataclass(frozen=True)
class EndpointStatus:
    """A non-numeric availability classification made before any evaluation."""

    status: str
    reason: str
    numerical_score: None = None


@dataclass(frozen=True)
class PreparedProductionExecution:
    """A static preflight receipt, deliberately without an execution method."""

    candidate_id: str
    candidate_sha256: str
    quarantine_output_root: Path
    execution_status: str = "PREPARED_NO_EXECUTION"


Matrix = tuple[tuple[int, ...], ...]


def classify_endpoint_availability(comparator: Mapping[str, Any]) -> EndpointStatus:
    """Classify static endpoint availability before response or loss construction."""

    if not isinstance(comparator, Mapping):
        raise ComparatorEligibilityError("comparator metadata must be a mapping")
    if comparator.get("representation") == "collapsed_only":
        return EndpointStatus(
            status=STATUS_OUTSIDE_TARGET,
            reason="collapsed-only representations retain D but not C0, C1 and C2",
        )
    if comparator.get("representation") != "coefficient_blocks":
        raise ComparatorEligibilityError("comparator must retain native coefficient blocks")
    if comparator.get("projected_output") is not False:
        raise ComparatorEligibilityError("projected comparator outputs are ineligible")
    if comparator.get("posthoc_mapping") is not False:
        raise ComparatorEligibilityError("post-hoc comparator mappings are ineligible")
    retained_blocks = comparator.get("retained_blocks")
    if not isinstance(retained_blocks, (tuple, list)) or set(retained_blocks) != {
        "C0",
        "C1",
        "C2",
    }:
        raise ComparatorEligibilityError("comparator must retain exactly C0, C1 and C2")
    if comparator.get("endpoint_output") != "full_operator_and_finite_horizon_response":
        raise ComparatorEligibilityError("comparator must natively return the full endpoint")
    return EndpointStatus(
        status=STATUS_AVAILABLE,
        reason="native three-block representation exposes the declared endpoint",
    )


def validate_comparator_before_fitting(comparator: Mapping[str, Any]) -> EndpointStatus:
    """Reject ineligible comparison rows without accessing a fitting callback."""

    endpoint = classify_endpoint_availability(comparator)
    if endpoint.status == STATUS_OUTSIDE_TARGET:
        raise ComparatorEligibilityError(
            "collapsed-only comparators are availability controls, not fitted competitors"
        )
    return endpoint


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _assert_finite_json(value: Any) -> None:
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        raise ContractError("non-finite values are forbidden in static contracts")
    if isinstance(value, Mapping):
        for item in value.values():
            _assert_finite_json(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _assert_finite_json(item)


def _canonical_json_bytes(value: Any) -> bytes:
    _assert_finite_json(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _reject_nonfinite_constant(value: str) -> None:
    raise ContractError(f"non-finite JSON constant is forbidden: {value}")


def _identity(size: int) -> Matrix:
    return tuple(
        tuple(1 if row == column else 0 for column in range(size))
        for row in range(size)
    )


def _zero(size: int) -> Matrix:
    return tuple(tuple(0 for _ in range(size)) for _ in range(size))


def _matrix_add(*matrices: Matrix) -> Matrix:
    if not matrices:
        raise ValueError("at least one matrix is required")
    size = len(matrices[0])
    if any(len(matrix) != size or any(len(row) != size for row in matrix) for matrix in matrices):
        raise ValueError("matrices must be square and equally sized")
    return tuple(
        tuple(sum(matrix[row][column] for matrix in matrices) for column in range(size))
        for row in range(size)
    )


def _matrix_scale(matrix: Matrix, scalar: int) -> Matrix:
    return tuple(tuple(scalar * value for value in row) for row in matrix)


def _matrix_product(left: Matrix, right: Matrix) -> Matrix:
    size = len(left)
    if (
        len(right) != size
        or any(len(row) != size for row in left)
        or any(len(row) != size for row in right)
    ):
        raise ValueError("matrices must be square and equally sized")
    return tuple(
        tuple(
            sum(left[row][index] * right[index][column] for index in range(size))
            for column in range(size)
        )
        for row in range(size)
    )


def _family1_operator(a: Matrix, b: Matrix, topology: Matrix) -> Matrix:
    return _matrix_add(a, _matrix_product(b, topology))


def _family2_operator(
    c0: Matrix,
    c1: Matrix,
    c2: Matrix,
    topology: Matrix,
) -> Matrix:
    topology_squared = _matrix_product(topology, topology)
    return _matrix_add(
        c0,
        _matrix_product(c1, topology),
        _matrix_product(c2, topology_squared),
    )


def _row_factor_matrix(topology: Matrix, row: int) -> Matrix:
    size = len(topology)
    topology_squared = _matrix_product(topology, topology)
    return tuple(
        (
            1 if index == row else 0,
            topology[row][index],
            topology_squared[row][index],
        )
        for index in range(size)
    )


def _exact_rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    working = [[Fraction(value) for value in row] for row in matrix]
    n_rows = len(working)
    n_columns = len(working[0])
    pivot_row = 0
    for column in range(n_columns):
        candidate = next(
            (row for row in range(pivot_row, n_rows) if working[row][column] != 0),
            None,
        )
        if candidate is None:
            continue
        working[pivot_row], working[candidate] = working[candidate], working[pivot_row]
        pivot = working[pivot_row][column]
        working[pivot_row] = [value / pivot for value in working[pivot_row]]
        for row in range(n_rows):
            if row == pivot_row:
                continue
            factor = working[row][column]
            if factor:
                working[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(working[row], working[pivot_row])
                ]
        pivot_row += 1
        if pivot_row == n_rows:
            break
    return pivot_row


def _exact_fixture_audit() -> dict[str, dict[str, Any]]:
    """Classify the contract's rational/integer fixtures without outcomes."""

    permutation: Matrix = ((0, 1, 0), (0, 0, 1), (1, 0, 0))
    permutation_squared = _matrix_product(permutation, permutation)
    identity = _identity(3)
    zero = _zero(3)

    f1_observed_equal = _family1_operator(zero, zero, permutation) == _family1_operator(
        _matrix_scale(permutation, -1), identity, permutation
    )
    f1_query_differs = _family1_operator(zero, zero, permutation_squared) != _family1_operator(
        _matrix_scale(permutation, -1), identity, permutation_squared
    )
    if not (f1_observed_equal and f1_query_differs):
        raise ContractError("F1 exact structural-negative fixture failed")

    f2_observed_equal = _family2_operator(zero, zero, zero, permutation) == _family2_operator(
        _matrix_add(
            _matrix_scale(permutation, -1),
            _matrix_scale(permutation_squared, -2),
        ),
        identity,
        _matrix_scale(identity, 2),
        permutation,
    )
    f2_query_differs = _family2_operator(zero, zero, zero, permutation_squared) != _family2_operator(
        _matrix_add(
            _matrix_scale(permutation, -1),
            _matrix_scale(permutation_squared, -2),
        ),
        identity,
        _matrix_scale(identity, 2),
        permutation_squared,
    )
    if not (f2_observed_equal and f2_query_differs):
        raise ContractError("F2 unrestricted exact structural-negative fixture failed")

    diagonal_observed: Matrix = ((0, 1, 0), (0, 0, 0), (0, 0, 0))
    diagonal_query: Matrix = ((0, 1, 0), (0, 0, 1), (0, 0, 0))
    c2_witness: Matrix = ((1, 0, 0), (0, 0, 0), (0, 0, 0))
    diagonal_observed_equal = _family2_operator(
        zero, zero, zero, diagonal_observed
    ) == _family2_operator(zero, zero, c2_witness, diagonal_observed)
    diagonal_query_differs = _family2_operator(
        zero, zero, zero, diagonal_query
    ) != _family2_operator(zero, zero, c2_witness, diagonal_query)
    observed_rank = _exact_rank(_row_factor_matrix(diagonal_observed, 0))
    query_rank = _exact_rank(_row_factor_matrix(diagonal_query, 0))
    if not (
        diagonal_observed_equal
        and diagonal_query_differs
        and observed_rank < query_rank
    ):
        raise ContractError("F2 diagonal exact structural-negative fixture failed")

    positive_ranks = tuple(
        _exact_rank(_row_factor_matrix(permutation, row)) for row in range(3)
    )
    if positive_ranks != (3, 3, 3):
        raise ContractError("F2 diagonal structured-positive fixture failed")

    swap: Matrix = ((0, 1), (1, 0))
    twice_swap = _matrix_scale(swap, 2)
    if _matrix_product(swap, swap) != _identity(2) or _matrix_product(
        twice_swap, twice_swap
    ) != _matrix_scale(_identity(2), 4):
        raise ContractError("Family-2 non-equivalence witness failed")

    return {
        "f1_negative": {
            "status": STATUS_OUTSIDE_TARGET,
            "basis": "observed-collapsed equality with query disagreement",
            "static_only": True,
        },
        "f2_unrestricted_negative": {
            "status": STATUS_OUTSIDE_TARGET,
            "basis": "observed-collapsed equality with query disagreement",
            "static_only": True,
        },
        "f2_diagonal_negative": {
            "status": STATUS_OUTSIDE_TARGET,
            "basis": "rowwise kernel inclusion fails at the declared query",
            "observed_row_rank": observed_rank,
            "query_row_rank": query_rank,
            "static_only": True,
        },
        "f2_diagonal_positive": {
            "status": STATUS_AVAILABLE,
            "basis": "every observed row factor matrix has full column rank",
            "row_ranks": list(positive_ranks),
            "availability_route": "identified_inverse",
            "static_only": True,
        },
        "non_equivalence": {
            "status": "DISTINCT_FAMILY",
            "basis": "W-squared disagrees with any fixed first-order map on 0,V,2V",
            "static_only": True,
        },
    }


def _artifact_body() -> dict[str, Any]:
    if not FAMILY2_CONTRACT_PATH.is_file():
        raise ContractError(f"missing Family-2 candidate contract: {FAMILY2_CONTRACT_PATH}")
    runner_path = Path(__file__).resolve()
    try:
        preoutcome_artifact_inventory = artifact_schemas.source_only_artifact_inventory()
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"source-only pre-outcome package is invalid: {error}") from error
    return {
        "schema_version": SCHEMA_VERSION,
        "run_type": "construction_only",
        "status": "CONSTRUCTION_PASS",
        "scientific_execution": "NOT_AUTHORIZED",
        "contract": {
            "operator_family": "C0_plus_C1W_plus_C2W2_with_diagonal_blocks",
            "topology_square": "exact_matrix_product_WW",
            "topology_square_reprocessing": "prohibited",
            "shock_map": "identity",
            "endpoint": "full_operator_and_finite_horizon_response",
            "status_schema": [
                STATUS_AVAILABLE,
                STATUS_OUTSIDE_TARGET,
                STATUS_NONCONVERGED,
                STATUS_NONFINITE,
                STATUS_UNSTABLE,
            ],
            "outside_target_numerical_score": "prohibited",
        },
        "fixtures": _exact_fixture_audit(),
        "comparator_rules": {
            "native_full_endpoint_required": True,
            "collapsed_only": "availability_negative_control_only",
            "projected_output": "ineligible",
            "posthoc_mapping": "ineligible",
            "pre_fitting_validation": "required",
        },
        "preoutcome_artifact_inventory": preoutcome_artifact_inventory,
        "provenance": {
            "family2_contract": str(FAMILY2_CONTRACT_PATH.relative_to(ROOT)),
            "family2_contract_sha256": _sha256_file(FAMILY2_CONTRACT_PATH),
            "runner": str(runner_path.relative_to(ROOT)),
            "runner_sha256": _sha256_file(runner_path),
        },
    }


def _validate_static_artifact(artifact: Mapping[str, Any]) -> None:
    if set(artifact) != _ARTIFACT_FIELDS:
        raise ContractError("pre-outcome artifact field set is invalid")
    if artifact["schema_version"] != SCHEMA_VERSION:
        raise ContractError("pre-outcome artifact schema version is invalid")
    if artifact["run_type"] != "construction_only":
        raise ContractError("pre-outcome artifact cannot contain an execution run type")
    if artifact["status"] != "CONSTRUCTION_PASS":
        raise ContractError("pre-outcome artifact construction did not pass")
    if artifact["scientific_execution"] != "NOT_AUTHORIZED":
        raise ContractError("pre-outcome artifact cannot authorize science")
    fixtures = artifact["fixtures"]
    if not isinstance(fixtures, Mapping) or set(fixtures) != set(_FIXTURE_NAMES):
        raise ContractError("pre-outcome fixture inventory is invalid")
    expected_statuses = {
        "f1_negative": STATUS_OUTSIDE_TARGET,
        "f2_unrestricted_negative": STATUS_OUTSIDE_TARGET,
        "f2_diagonal_negative": STATUS_OUTSIDE_TARGET,
        "f2_diagonal_positive": STATUS_AVAILABLE,
        "non_equivalence": "DISTINCT_FAMILY",
    }
    for name, expected in expected_statuses.items():
        if fixtures[name].get("status") != expected or fixtures[name].get("static_only") is not True:
            raise ContractError(f"invalid static fixture: {name}")
    if artifact["contract"].get("outside_target_numerical_score") != "prohibited":
        raise ContractError("OUTSIDE_TARGET must remain non-numeric")
    try:
        expected_inventory = artifact_schemas.source_only_artifact_inventory()
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"source-only pre-outcome package is invalid: {error}") from error
    if artifact["preoutcome_artifact_inventory"] != expected_inventory:
        raise ContractError("static artifact does not bind the current source-only artifact package")
    _assert_finite_json(artifact)


def _atomic_write(destination: Path, payload: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def write_preoutcome_contract(artifact_path: Path) -> dict[str, Any]:
    """Publish one static E3 contract artifact and no scientific output."""

    destination = Path(artifact_path).expanduser().resolve(strict=False)
    if destination.name != ARTIFACT_NAME:
        raise ValueError(f"artifact filename must be {ARTIFACT_NAME}")
    body = _artifact_body()
    artifact = {**body, "artifact_sha256": _canonical_sha256(body)}
    _validate_static_artifact(artifact)
    _atomic_write(destination, _canonical_json_bytes(artifact) + b"\n")
    return artifact


def verify_preoutcome_contract(artifact_path: Path) -> dict[str, Any]:
    """Verify that an artifact is current, static and source-only."""

    source = Path(artifact_path).expanduser().resolve(strict=False)
    if not source.is_file():
        raise ContractError("missing E3 pre-outcome artifact")
    try:
        artifact = json.loads(source.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite_constant)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ContractError("invalid E3 pre-outcome artifact") from error
    if not isinstance(artifact, Mapping):
        raise ContractError("E3 pre-outcome artifact must be an object")
    _validate_static_artifact(artifact)
    body = {name: artifact[name] for name in artifact if name != "artifact_sha256"}
    if not hmac.compare_digest(str(artifact["artifact_sha256"]), _canonical_sha256(body)):
        raise ContractError("E3 pre-outcome artifact digest mismatch")
    expected_body = _artifact_body()
    if body != expected_body:
        raise ContractError("E3 pre-outcome artifact differs from current static contract")
    return dict(artifact)


def verify_source_only_contract(artifact_path: Path) -> dict[str, Any]:
    """Return a read-only, machine-readable verification summary.

    This function validates the static contract and every current source-only
    artifact. It neither prepares nor invokes a production execution path.
    """

    source = Path(artifact_path).expanduser().resolve(strict=False)
    artifact = verify_preoutcome_contract(source)
    inventory = artifact_schemas.source_only_artifact_inventory()
    artifacts: list[dict[str, str]] = []
    for artifact_id in REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        binding = inventory[artifact_id]
        artifact_path = Path(binding["path"])
        if not artifact_path.is_absolute():
            artifact_path = ROOT / artifact_path
        verified = verify_preoutcome_artifact(
            artifact_path, artifact_id=artifact_id
        )
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "artifact_sha256": binding["sha256"],
                "lifecycle": str(verified["lifecycle"]),
                "scientific_execution": str(verified["scientific_execution"]),
            }
        )
    return {
        "run_type": "verification_only",
        "status": "SOURCE_ONLY_VERIFIED",
        "scientific_execution": NOT_AUTHORIZED,
        "production_execution": "UNAVAILABLE",
        "contract": {
            "path": str(source),
            "artifact_sha256": str(artifact["artifact_sha256"]),
            "status": str(artifact["status"]),
        },
        "preoutcome_artifacts": artifacts,
    }


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_exact_fields(value: Any, fields: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ContractError(f"{label} has an invalid field set")
    return value


def _forbid_external_route(value: str, label: str) -> None:
    folded = value.casefold()
    if any(route.casefold() in folded for route in _EXCLUDED_ROUTES):
        raise ContractError(f"{label} references an excluded route")


def _resolve_existing_file(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label} must be a non-empty path")
    _forbid_external_route(value, label)
    path = Path(value).expanduser().resolve(strict=False)
    if not path.is_file():
        raise ContractError(f"{label} must identify an existing regular file")
    return path


def _validate_execution_candidate_shape(candidate: Mapping[str, Any]) -> None:
    _require_exact_fields(candidate, _CANDIDATE_FIELDS, "execution candidate")
    if candidate["schema_version"] != EXECUTION_CANDIDATE_SCHEMA_VERSION:
        raise ContractError("execution candidate schema version is invalid")
    candidate_id = candidate["candidate_id"]
    if not isinstance(candidate_id, str) or not candidate_id:
        raise ContractError("execution candidate id is invalid")
    _forbid_external_route(candidate_id, "execution candidate id")

    execution = _require_exact_fields(candidate["execution"], _EXECUTION_FIELDS, "execution scope")
    if execution["invocation_limit"] != 1:
        raise ContractError("execution candidate must bind exactly one invocation")
    if execution["input_route"] != "synthetic_only":
        raise ContractError("execution candidate must use the synthetic-only route")
    excluded_routes = execution["excluded_routes"]
    if not isinstance(excluded_routes, list) or set(excluded_routes) != _EXCLUDED_ROUTES:
        raise ContractError("execution candidate exclusion set is incomplete")
    prohibitions = execution["prohibitions"]
    if not isinstance(prohibitions, list) or set(prohibitions) != _REQUIRED_PROHIBITIONS:
        raise ContractError("execution candidate prohibition set is incomplete")

    raw_bindings = candidate["bindings"]
    if isinstance(raw_bindings, Mapping) and "dependency_hashes" not in raw_bindings:
        raise ContractError("dependency hashes are required")
    bindings = _require_exact_fields(raw_bindings, _BINDING_FIELDS, "execution bindings")
    if not _is_sha256(bindings["runner_sha256"]):
        raise ContractError("runner hash is invalid")
    if not _is_sha256(bindings["configuration_sha256"]):
        raise ContractError("configuration hash is invalid")
    if not isinstance(bindings["quarantine_output_root"], str):
        raise ContractError("quarantine output root is invalid")

    evidence = _require_exact_fields(candidate["trust_evidence"], _TRUST_EVIDENCE_FIELDS, "trust evidence")
    if any(not isinstance(evidence[field], str) or not evidence[field] for field in evidence):
        raise ContractError("trust evidence must contain non-empty string fields")
    _assert_finite_json(candidate)


def _validate_source_hashes(bindings: Mapping[str, Any]) -> None:
    source_hashes = bindings["source_hashes"]
    if not isinstance(source_hashes, Mapping) or not source_hashes:
        raise ContractError("source hashes are required")
    runner_path = Path(__file__).resolve()
    schema_path = Path(artifact_schemas.__file__).resolve()
    required_paths = {runner_path, schema_path}
    found_paths: set[Path] = set()
    for raw_path, expected_hash in source_hashes.items():
        if not isinstance(raw_path, str) or not _is_sha256(expected_hash):
            raise ContractError("source hash binding is invalid")
        _forbid_external_route(raw_path, "source hash path")
        source_path = Path(raw_path).expanduser().resolve(strict=False)
        if not source_path.is_file() or not source_path.is_relative_to(ROOT):
            raise ContractError("source hash path must be an in-repository source file")
        if not hmac.compare_digest(_sha256_file(source_path), expected_hash):
            raise ContractError("source hash binding does not match disk")
        if source_path == runner_path:
            if not hmac.compare_digest(expected_hash, bindings["runner_sha256"]):
                raise ContractError("runner hash binding is inconsistent")
        if source_path in required_paths:
            found_paths.add(source_path)
    if found_paths != required_paths:
        raise ContractError("candidate does not bind the complete E3 pre-outcome source boundary")
    if not hmac.compare_digest(_sha256_file(runner_path), bindings["runner_sha256"]):
        raise ContractError("candidate does not bind the current E3 runner")


def _validate_dependency_hashes(bindings: Mapping[str, Any]) -> None:
    dependency_hashes = bindings["dependency_hashes"]
    if not isinstance(dependency_hashes, Mapping) or not dependency_hashes:
        raise ContractError("dependency hashes are required")
    for raw_path, expected_hash in dependency_hashes.items():
        if not isinstance(raw_path, str) or not _is_sha256(expected_hash):
            raise ContractError("dependency hash binding is invalid")
        path = _resolve_existing_file(raw_path, "dependency hash path")
        if not hmac.compare_digest(_sha256_file(path), expected_hash):
            raise ContractError("dependency hash binding does not match disk")


def _validate_preoutcome_artifacts(bindings: Mapping[str, Any]) -> None:
    artifacts = bindings["preoutcome_artifacts"]
    if not isinstance(artifacts, Mapping) or set(artifacts) != set(REQUIRED_PREOUTCOME_ARTIFACT_IDS):
        raise ContractError("candidate must bind every pre-outcome artifact")
    for artifact_id in REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        binding = _require_exact_fields(
            artifacts[artifact_id], _PREOUTCOME_BINDING_FIELDS, f"pre-outcome artifact {artifact_id}"
        )
        path = _resolve_existing_file(binding["path"], f"pre-outcome artifact {artifact_id}")
        if not _is_sha256(binding["sha256"]) or not hmac.compare_digest(
            _sha256_file(path), binding["sha256"]
        ):
            raise ContractError(f"pre-outcome artifact {artifact_id} hash does not match disk")
        verify_preoutcome_artifact(
            path,
            artifact_id=artifact_id,
            require_candidate_ready=True,
        )


def _validate_synthetic_inputs(bindings: Mapping[str, Any]) -> None:
    inputs = bindings["inputs"]
    if not isinstance(inputs, list) or not inputs:
        raise ContractError("synthetic input bindings are required")
    input_ids: set[str] = set()
    for item in inputs:
        binding = _require_exact_fields(item, _INPUT_BINDING_FIELDS, "synthetic input binding")
        input_id = binding["input_id"]
        if not isinstance(input_id, str) or not input_id.startswith("synthetic-"):
            raise ContractError("input binding must be explicitly synthetic")
        if input_id in input_ids:
            raise ContractError("synthetic input ids must be unique")
        input_ids.add(input_id)
        path = _resolve_existing_file(binding["path"], f"synthetic input {input_id}")
        if not _is_sha256(binding["sha256"]) or not hmac.compare_digest(
            _sha256_file(path), binding["sha256"]
        ):
            raise ContractError("synthetic input hash does not match disk")


def _validate_configuration(bindings: Mapping[str, Any]) -> None:
    configuration = _require_exact_fields(
        bindings["configuration"], _CONFIGURATION_FIELDS, "execution configuration"
    )
    for field in ("topology_generators", "scales", "panel_lengths", "horizons", "seeds", "comparators"):
        if not isinstance(configuration[field], list) or not configuration[field]:
            raise ContractError(f"execution configuration field {field} is incomplete")
    if not isinstance(configuration["split_policy"], str) or not configuration["split_policy"]:
        raise ContractError("execution configuration split policy is invalid")
    if not isinstance(configuration["tuning_budget"], int) or configuration["tuning_budget"] < 1:
        raise ContractError("execution configuration tuning budget is invalid")
    validate_fixed_rank_bootstrap_history_gate(configuration["bootstrap_refit_history"])
    try:
        artifact_schemas.validate_recursive_bootstrap_procedure(
            configuration["bootstrap_procedure"]
        )
        artifact_schemas.validate_domain_stability_contract(
            configuration["domain_stability"]
        )
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"execution configuration refused: {error}") from error
    if configuration["cross_generator_failure_boundary"] != _CROSS_GENERATOR_FAILURE_BOUNDARY:
        raise ContractError("cross-generator failure boundary is invalid")
    for generator in configuration["topology_generators"]:
        if not isinstance(generator, str):
            raise ContractError("topology generator names must be strings")
        _forbid_external_route(generator, "topology generator")
    if not hmac.compare_digest(_canonical_sha256(configuration), bindings["configuration_sha256"]):
        raise ContractError("execution configuration hash does not match content")


def _validate_bootstrap_history_bindings(bindings: Mapping[str, Any]) -> None:
    """Require the v4 bootstrap and stability contracts to agree everywhere."""

    configuration = _require_exact_fields(
        bindings["configuration"], _CONFIGURATION_FIELDS, "execution configuration"
    )
    configuration_gate = validate_fixed_rank_bootstrap_history_gate(
        configuration["bootstrap_refit_history"]
    )
    try:
        configuration_procedure = artifact_schemas.validate_recursive_bootstrap_procedure(
            configuration["bootstrap_procedure"]
        )
        configuration_stability = artifact_schemas.validate_domain_stability_contract(
            configuration["domain_stability"]
        )
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"recursive bootstrap procedure refused: {error}") from error

    artifacts = bindings["preoutcome_artifacts"]
    tuning_binding = _require_exact_fields(
        artifacts["tuning_split_manifest"],
        _PREOUTCOME_BINDING_FIELDS,
        "bootstrap-history tuning manifest binding",
    )
    tuning_path = _resolve_existing_file(
        tuning_binding["path"], "bootstrap-history tuning manifest"
    )
    if not _is_sha256(tuning_binding["sha256"]) or not hmac.compare_digest(
        _sha256_file(tuning_path), tuning_binding["sha256"]
    ):
        raise ContractError("bootstrap-history tuning manifest hash does not match disk")
    try:
        tuning_artifact = json.loads(
            tuning_path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite_constant
        )
        tuning_gate = tuning_artifact["content"]["bootstrap_refit_history"]
        tuning_procedure = tuning_artifact["content"]["bootstrap_procedure"]
        tuning_stability = tuning_artifact["content"]["domain_stability"]
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ContractError("bootstrap-history tuning manifest is invalid") from error
    validate_fixed_rank_bootstrap_history_gate(tuning_gate)
    if tuning_gate != configuration_gate:
        raise ContractError("bootstrap-history tuning gate does not match candidate configuration")
    try:
        artifact_schemas.validate_recursive_bootstrap_procedure(tuning_procedure)
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"recursive bootstrap tuning manifest refused: {error}") from error
    if tuning_procedure != configuration_procedure:
        raise ContractError("bootstrap procedure does not match candidate configuration")
    try:
        artifact_schemas.validate_domain_stability_contract(tuning_stability)
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"domain-stability tuning manifest refused: {error}") from error
    if tuning_stability != configuration_stability:
        raise ContractError("domain stability does not match candidate configuration")

    query_binding = _require_exact_fields(
        artifacts["family2_query_contract"],
        _PREOUTCOME_BINDING_FIELDS,
        "domain-stability query contract binding",
    )
    query_path = _resolve_existing_file(
        query_binding["path"], "domain-stability query contract"
    )
    if not _is_sha256(query_binding["sha256"]) or not hmac.compare_digest(
        _sha256_file(query_path), query_binding["sha256"]
    ):
        raise ContractError("domain-stability query contract hash does not match disk")
    try:
        query_artifact = json.loads(
            query_path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite_constant
        )
        query_stability = query_artifact["content"]["domain_stability"]
        artifact_schemas.validate_domain_stability_contract(query_stability)
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        artifact_schemas.ArtifactValidationError,
    ) as error:
        raise ContractError("domain-stability query contract is invalid") from error
    if query_stability != configuration_stability:
        raise ContractError("domain stability does not match the Family-2 query contract")

    specification_rows = [
        item
        for item in bindings["inputs"]
        if isinstance(item, Mapping) and item.get("input_id") == "synthetic-e3-specification"
    ]
    if not specification_rows:
        return
    if len(specification_rows) != 1:
        raise ContractError("candidate must bind exactly one synthetic E3 specification")
    specification_binding = _require_exact_fields(
        specification_rows[0], _INPUT_BINDING_FIELDS, "synthetic E3 specification binding"
    )
    specification_path = _resolve_existing_file(
        specification_binding["path"], "synthetic E3 specification"
    )
    if not _is_sha256(specification_binding["sha256"]) or not hmac.compare_digest(
        _sha256_file(specification_path), specification_binding["sha256"]
    ):
        raise ContractError("synthetic E3 specification hash does not match disk")
    try:
        specification = json.loads(
            specification_path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite_constant
        )
        specification_gate = specification["uncertainty"]["bootstrap_refit_history"]
        specification_procedure = specification["uncertainty"]["bootstrap_procedure"]
        allowed_ranks = specification["methods"]["fixed_rank_basis"]["ranks"]
        target_times = specification["uncertainty"]["evaluation_target_times"]
        failure_boundary = specification["stability"]["cross_generator_failure_boundary"]
        specification_stability = specification["stability"]["domain_uniform_envelope"]
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ContractError("synthetic E3 specification is invalid") from error
    validate_fixed_rank_bootstrap_history_gate(specification_gate)
    if specification_gate != configuration_gate:
        raise ContractError("bootstrap-history specification gate does not match candidate configuration")
    try:
        artifact_schemas.validate_recursive_bootstrap_procedure(specification_procedure)
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"synthetic bootstrap procedure refused: {error}") from error
    if specification_procedure != configuration_procedure:
        raise ContractError("bootstrap procedure specification does not match candidate configuration")
    if allowed_ranks != configuration_gate["allowed_ranks"]:
        raise ContractError("bootstrap-history allowed ranks do not match the frozen method list")
    if target_times != configuration_gate["evaluation_target_times"]:
        raise ContractError("bootstrap-history target times do not match the frozen uncertainty schedule")
    if failure_boundary != configuration["cross_generator_failure_boundary"]:
        raise ContractError("cross-generator failure boundary does not match the frozen specification")
    try:
        artifact_schemas.validate_domain_stability_contract(specification_stability)
    except artifact_schemas.ArtifactValidationError as error:
        raise ContractError(f"synthetic domain-stability contract refused: {error}") from error
    if specification_stability != configuration_stability:
        raise ContractError("domain stability does not match the frozen specification")


def _validate_new_quarantine_root(
    candidate_root: Any, expected_root: Path
) -> Path:
    if not isinstance(candidate_root, str) or not candidate_root:
        raise ContractError("candidate quarantine root is invalid")
    _forbid_external_route(candidate_root, "quarantine root")
    raw_root = Path(candidate_root).expanduser()
    if not raw_root.is_absolute():
        raise ContractError("candidate quarantine root must be absolute")
    resolved = raw_root.resolve(strict=False)
    expected = Path(expected_root).expanduser().resolve(strict=False)
    if resolved != expected:
        raise ContractError("candidate quarantine root does not match the authorized root")
    if "quarantine" not in resolved.name.casefold():
        raise ContractError("candidate root is not labelled as quarantine")
    if resolved.exists():
        raise ContractError("candidate quarantine root must be new and absent")
    return resolved


def _load_candidate(candidate_path: Path) -> tuple[Mapping[str, Any], bytes]:
    source = Path(candidate_path).expanduser().resolve(strict=False)
    if not source.is_file():
        raise ContractError("candidate authorization file is missing")
    try:
        content = source.read_bytes()
        candidate = json.loads(content.decode("utf-8"), parse_constant=_reject_nonfinite_constant)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("candidate authorization file is invalid") from error
    if not isinstance(candidate, Mapping):
        raise ContractError("candidate authorization must be a JSON object")
    return candidate, content


def prepare_production_execution(
    *,
    candidate_path: Path | None,
    expected_candidate_sha256: str | None,
    trust_verifier: object | None,
    scientific_entrypoints: ScientificEntrypoints,
    expected_quarantine_root: Path,
) -> PreparedProductionExecution:
    """Hard-refuse production preflight in the current source-only revision.

    A previous static preflight accepted caller-supplied verifier callbacks.
    Even though it never called the declared scientific entrypoints, such a
    callback is an uncontrolled execution surface.  Until a separately
    reviewed deployment-owned trust authority is installed, this public API
    must refuse before dereferencing a candidate, verifier, or output root.
    """

    del (
        candidate_path,
        expected_candidate_sha256,
        trust_verifier,
        scientific_entrypoints,
        expected_quarantine_root,
    )
    raise AuthorizationError(
        "production E3 preflight is unavailable in the source-only build"
    )


def build_argument_parser() -> argparse.ArgumentParser:
    """Expose static construction and verification, never production science."""

    parser = argparse.ArgumentParser(prog="e3-family2-preoutcome")
    commands = parser.add_subparsers(dest="command", required=True)
    construction = commands.add_parser("construction")
    construction.add_argument("--output", type=Path, required=True)
    verification = commands.add_parser("verify")
    verification.add_argument("--input", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a static construction or verification command, never science."""

    arguments = build_argument_parser().parse_args(argv)
    try:
        if arguments.command == "construction":
            artifact = write_preoutcome_contract(arguments.output)
            result = {
                "status": artifact["status"],
                "scientific_execution": artifact["scientific_execution"],
                "output": str(Path(arguments.output).expanduser().resolve(strict=False)),
            }
        elif arguments.command == "verify":
            result = verify_source_only_contract(arguments.input)
        else:  # pragma: no cover - argparse constrains this branch.
            raise ValueError("unsupported static command")
    except (ContractError, OSError, TypeError, ValueError) as error:
        print(f"{arguments.command} refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
