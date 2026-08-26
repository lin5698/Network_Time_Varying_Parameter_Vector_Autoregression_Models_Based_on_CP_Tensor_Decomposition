"""Fail-closed source scaffold for the E3 Family-2 synthetic-only runner.

This source revision deliberately contains no installed scientific executor and
no production trust authority.  It can validate the exact authorization shape
against fixture-only inputs, but every production entrypoint rejects before it
reads bound inputs, creates a quarantine directory, or calls scientific code.

An executable E3-1 runner requires a later, separately reviewed source change
that binds both a deployment-owned trust authority and a candidate-owned
executor into the exact authorization closure.  That change is outside this
source-only authorization.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from scripts.experiments import e3_family2_artifact_schemas as artifact_schemas
from scripts.experiments import e3_family2_preoutcome as preoutcome


EXECUTION_APPROVAL_SCHEMA_VERSION = "e3-family2-synthetic-execution-approval-v1"
STATIC_VALIDATED_NO_EXECUTION = "STATIC_VALIDATED_NO_EXECUTION"

_APPROVAL_FIELDS = frozenset(
    {
        "schema_version",
        "approval_id",
        "decision",
        "candidate_sha256",
        "candidate_id",
        "synthetic_runner_sha256",
        "execution",
        "bindings",
        "trust_evidence",
    }
)
_APPROVAL_BINDING_FIELDS = frozenset(
    {
        "source_hashes_sha256",
        "dependency_hashes_sha256",
        "configuration_sha256",
        "preoutcome_artifacts_sha256",
        "quarantine_output_root",
    }
)
_EXECUTION_FIELDS = frozenset(
    {"invocation_limit", "input_route", "excluded_routes", "prohibitions"}
)
_TRUST_EVIDENCE_FIELDS = frozenset(
    {"pinned_key_id", "trust_policy_id", "detached_signature"}
)
_EXCLUDED_ROUTES = frozenset({"RCEP", "NYC", "R006e", "R006f"})
_REQUIRED_PROHIBITIONS = frozenset(
    {
        "outcome_promotion",
        "downstream_builds",
        "manuscript_promotion",
        "audit_status_changes",
    }
)

AuthorizationError = preoutcome.AuthorizationError


@dataclass(frozen=True)
class FixtureAuthorizationReceipt:
    """A static fixture receipt; it is explicitly not an execution capability."""

    candidate_id: str
    candidate_sha256: str
    approval_sha256: str
    quarantine_output_root: Path
    status: str = STATIC_VALIDATED_NO_EXECUTION


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _require_exact_fields(value: Any, fields: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise AuthorizationError(f"{label} has an invalid field set")
    return value


def _read_hashed_json(
    source: Path | None,
    expected_sha256: str | None,
    *,
    label: str,
) -> tuple[Mapping[str, Any], Path, str]:
    if source is None or expected_sha256 is None:
        raise AuthorizationError(f"{label} is required")
    if not _is_sha256(expected_sha256):
        raise AuthorizationError(f"{label} hash is invalid")
    path = Path(source).expanduser().resolve(strict=False)
    if not path.is_file():
        raise AuthorizationError(f"{label} file is missing")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"), parse_constant=_reject_nonfinite_constant)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise AuthorizationError(f"{label} is invalid") from error
    actual_sha256 = _sha256_bytes(raw)
    if not hmac.compare_digest(actual_sha256, expected_sha256):
        raise AuthorizationError(f"{label} hash does not match disk")
    if not isinstance(value, Mapping):
        raise AuthorizationError(f"{label} must be a JSON object")
    return value, path, actual_sha256


def _validate_execution_scope(value: Any, *, label: str) -> Mapping[str, Any]:
    execution = _require_exact_fields(value, _EXECUTION_FIELDS, label)
    if execution["invocation_limit"] != 1:
        raise AuthorizationError(f"{label} must bind exactly one invocation")
    if execution["input_route"] != "synthetic_only":
        raise AuthorizationError(f"{label} must use the synthetic-only route")
    if not isinstance(execution["excluded_routes"], list) or set(execution["excluded_routes"]) != _EXCLUDED_ROUTES:
        raise AuthorizationError(f"{label} exclusion set is incomplete")
    if not isinstance(execution["prohibitions"], list) or set(execution["prohibitions"]) != _REQUIRED_PROHIBITIONS:
        raise AuthorizationError(f"{label} prohibition set is incomplete")
    return execution


def _candidate_identity_and_bindings(
    candidate: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise AuthorizationError("candidate id is invalid")
    execution = _validate_execution_scope(candidate.get("execution"), label="candidate execution scope")
    bindings = candidate.get("bindings")
    if not isinstance(bindings, Mapping):
        raise AuthorizationError("candidate bindings are invalid")
    required_bindings = {
        "source_hashes",
        "dependency_hashes",
        "configuration_sha256",
        "preoutcome_artifacts",
        "quarantine_output_root",
    }
    if not required_bindings.issubset(bindings):
        raise AuthorizationError("candidate bindings are incomplete")
    return candidate_id, execution, bindings


def _validate_fixture_trust_evidence(evidence: Any, *, label: str) -> None:
    """Check fixture evidence shape without invoking caller-controlled code."""

    value = _require_exact_fields(evidence, _TRUST_EVIDENCE_FIELDS, f"{label} trust evidence")
    if any(not isinstance(value[field], str) or not value[field] for field in value):
        raise AuthorizationError(f"{label} trust evidence is invalid")


def _validate_synthetic_runner_binding(
    candidate_bindings: Mapping[str, Any],
    approval_runner_sha256: Any,
) -> None:
    own_path = Path(__file__).resolve()
    own_sha256 = artifact_schemas.sha256_file(own_path)
    source_hashes = candidate_bindings.get("source_hashes")
    if not isinstance(source_hashes, Mapping):
        raise AuthorizationError("candidate synthetic runner binding is missing")
    bound_sha256: str | None = None
    for raw_path, raw_sha256 in source_hashes.items():
        if not isinstance(raw_path, str) or not isinstance(raw_sha256, str):
            continue
        if Path(raw_path).expanduser().resolve(strict=False) == own_path:
            bound_sha256 = raw_sha256
            break
    if bound_sha256 is None:
        raise AuthorizationError("candidate does not bind the synthetic runner source")
    if not _is_sha256(bound_sha256) or not hmac.compare_digest(bound_sha256, own_sha256):
        raise AuthorizationError("candidate synthetic runner hash does not match disk")
    if not _is_sha256(approval_runner_sha256) or not hmac.compare_digest(
        approval_runner_sha256, own_sha256
    ):
        raise AuthorizationError("approval synthetic runner hash does not match disk")


def _validate_exact_approval(
    approval: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
    candidate_sha256: str,
    expected_quarantine_root: Path,
) -> None:
    value = _require_exact_fields(approval, _APPROVAL_FIELDS, "synthetic execution approval")
    if value["schema_version"] != EXECUTION_APPROVAL_SCHEMA_VERSION:
        raise AuthorizationError("synthetic execution approval schema version is invalid")
    if value["decision"] != "AUTHORIZE":
        raise AuthorizationError("synthetic execution approval decision is not AUTHORIZE")
    if not isinstance(value["approval_id"], str) or not value["approval_id"]:
        raise AuthorizationError("synthetic execution approval id is invalid")
    if not _is_sha256(value["candidate_sha256"]) or not hmac.compare_digest(
        value["candidate_sha256"], candidate_sha256
    ):
        raise AuthorizationError("approval candidate SHA does not match the exact candidate")

    candidate_id, candidate_execution, candidate_bindings = _candidate_identity_and_bindings(candidate)
    if value["candidate_id"] != candidate_id:
        raise AuthorizationError("approval candidate id does not match the exact candidate")
    approval_execution = _validate_execution_scope(value["execution"], label="approval execution scope")
    if dict(approval_execution) != dict(candidate_execution):
        raise AuthorizationError("approval execution scope does not match the exact candidate")
    _validate_synthetic_runner_binding(candidate_bindings, value["synthetic_runner_sha256"])

    bindings = _require_exact_fields(value["bindings"], _APPROVAL_BINDING_FIELDS, "approval bindings")
    source_hashes = candidate_bindings["source_hashes"]
    dependency_hashes = candidate_bindings["dependency_hashes"]
    preoutcome_artifacts = candidate_bindings["preoutcome_artifacts"]
    configuration_sha256 = candidate_bindings["configuration_sha256"]
    candidate_root = candidate_bindings["quarantine_output_root"]
    if (
        not isinstance(source_hashes, Mapping)
        or not isinstance(dependency_hashes, Mapping)
        or not isinstance(preoutcome_artifacts, Mapping)
        or not _is_sha256(configuration_sha256)
        or not isinstance(candidate_root, str)
    ):
        raise AuthorizationError("candidate bindings are invalid")
    expected_binding_hashes = {
        "source_hashes_sha256": artifact_schemas.canonical_sha256(source_hashes),
        "dependency_hashes_sha256": artifact_schemas.canonical_sha256(dependency_hashes),
        "configuration_sha256": configuration_sha256,
        "preoutcome_artifacts_sha256": artifact_schemas.canonical_sha256(preoutcome_artifacts),
    }
    for field, expected in expected_binding_hashes.items():
        if not _is_sha256(bindings[field]) or not hmac.compare_digest(bindings[field], expected):
            raise AuthorizationError("approval bindings do not match the exact candidate")
    if not isinstance(bindings["quarantine_output_root"], str):
        raise AuthorizationError("approval quarantine root is invalid")
    raw_root = Path(bindings["quarantine_output_root"]).expanduser()
    if not raw_root.is_absolute():
        raise AuthorizationError("approval quarantine root must be absolute")
    root = raw_root.resolve(strict=False)
    expected_root = Path(expected_quarantine_root).expanduser().resolve(strict=False)
    if root != expected_root or bindings["quarantine_output_root"] != candidate_root:
        raise AuthorizationError("approval quarantine root does not match the exact candidate")
    _validate_fixture_trust_evidence(value["trust_evidence"], label="approval")


def verify_fixture_synthetic_authorization(
    *,
    candidate_path: Path | None,
    expected_candidate_sha256: str | None,
    approval_path: Path | None,
    expected_approval_sha256: str | None,
    expected_quarantine_root: Path,
) -> FixtureAuthorizationReceipt:
    """Statically validate fixture-only artifacts without issuing a run capability.

    It only validates the shape and binding of fixture trust evidence.  It
    neither verifies a detached signature nor invokes caller-provided code,
    and its return value has no execution method.  The function never creates
    the authorized output root.
    """

    candidate, _candidate_source, candidate_sha256 = _read_hashed_json(
        candidate_path,
        expected_candidate_sha256,
        label="candidate authorization",
    )
    approval, _approval_source, approval_sha256 = _read_hashed_json(
        approval_path,
        expected_approval_sha256,
        label="synthetic execution approval",
    )
    _validate_fixture_trust_evidence(candidate.get("trust_evidence"), label="candidate")
    _validate_exact_approval(
        approval,
        candidate=candidate,
        candidate_sha256=candidate_sha256,
        expected_quarantine_root=expected_quarantine_root,
    )
    try:
        preoutcome._validate_execution_candidate_shape(candidate)
        bindings = candidate["bindings"]
        _validate_synthetic_runner_binding(bindings, approval["synthetic_runner_sha256"])
        preoutcome._validate_source_hashes(bindings)
        preoutcome._validate_dependency_hashes(bindings)
        preoutcome._validate_preoutcome_artifacts(bindings)
        preoutcome._validate_synthetic_inputs(bindings)
        preoutcome._validate_configuration(bindings)
        preoutcome._validate_bootstrap_history_bindings(bindings)
        root = preoutcome._validate_new_quarantine_root(
            bindings["quarantine_output_root"], expected_quarantine_root
        )
    except (preoutcome.ContractError, KeyError, TypeError, ValueError, OSError) as error:
        raise AuthorizationError(f"fixture static preflight refused: {error}") from error
    return FixtureAuthorizationReceipt(
        candidate_id=str(candidate["candidate_id"]),
        candidate_sha256=candidate_sha256,
        approval_sha256=approval_sha256,
        quarantine_output_root=root,
    )


def prepare_production_synthetic_execution(
    *,
    candidate_path: Path | None,
    expected_candidate_sha256: str | None,
    approval_path: Path | None,
    expected_approval_sha256: str | None,
    expected_quarantine_root: Path,
) -> None:
    """Hard-refuse production before input access in this source-only revision."""

    del (
        candidate_path,
        expected_candidate_sha256,
        approval_path,
        expected_approval_sha256,
        expected_quarantine_root,
    )
    raise AuthorizationError(
        "production trust authority and candidate-bound E3-1 executor are unavailable in the source-only build"
    )


def run_synthetic_once(*_args: object, **_kwargs: object) -> None:
    """Hard-refuse every scientific call until a later authorized implementation."""

    raise AuthorizationError(
        "E3-1 scientific execution is unavailable in the source-only build"
    )
