"""Read-only comparator and claim audit for CAL-E01:75.

This module consumes the frozen E4-r3 JSON files. It never mutates a frozen
input and emits only raw comparator, paired-difference, and status inventory
artifacts for this recovery route. Historical metric helpers remain available
for audit traceability but are not serialized by the artifact writer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable, Iterable, Mapping, Sequence


ANALYSIS_VERSION = "cal-e01-75-independent-audit-v1"
REGISTER_KEY = "CAL-E01:75"
CALIBRATION_ID = "CAL-E01"
ITEM_INDEX = 75
AUTHORIZATION_SCHEMA_VERSION = "ncs-four-analysis-authorization-v2"
V2_ITEM_BINDING = {
    "item_id": "V1-026",
    "calibration_id": "CAL-E01",
    "item_index": 75,
    "priority": "P0",
    "action_class": "DIRECT_TEXT_REVISION",
}
V2_FROZEN_HASH_FIELDS = {
    "results": "results_sha256",
    "execution_manifest": "execution_manifest_sha256",
    "execution_complete": "execution_complete_sha256",
    "terminal_inventory": "terminal_inventory_sha256",
    "candidate": "candidate_sha256",
}
V2_REQUIRED_REC_M2_ACTION = "run_read_only_derived_analysis_after_m1_and_separate_go_gate"
V2_REQUIRED_TASK_LIMITS = {
    "m2_scientific_analysis": "BLOCKED_IN_THIS_TASK",
    "s1_s4": "NOT_AUTHORIZED",
    "manuscript": "NOT_AUTHORIZED",
    "register_decision": "NOT_AUTHORIZED",
    "promotion": "NOT_AUTHORIZED",
    "rcep_nyc_activation": "NOT_AUTHORIZED",
    "e4_r3_mutation": "NOT_AUTHORIZED",
    "claim_or_promotion_state_change": "NOT_AUTHORIZED",
    "old_authorization_reuse": "PROHIBITED",
}

STATUS_AVAILABLE = "AVAILABLE"
STATUS_NONCONVERGED = "NONCONVERGED"
STATUS_NONFINITE = "NONFINITE"
STATUS_OUTSIDE_TARGET = "OUTSIDE_TARGET"
STATUS_UNSTABLE = "UNSTABLE"
STATUS_SCHEMA = (
    STATUS_AVAILABLE,
    STATUS_NONCONVERGED,
    STATUS_NONFINITE,
    STATUS_OUTSIDE_TARGET,
    STATUS_UNSTABLE,
)

EXPECTED_FAMILIES = ("family1", "family2")
EXPECTED_SCALES = (20, 50)
EXPECTED_QUERIES = ("in_family_interpolation", "cross_generator")
EXPECTED_HORIZONS = (4, 12)
EXPECTED_SEEDS = tuple(range(4101, 4121))
EXPECTED_TARGET_TIMES = tuple(range(96, 144))
EXPECTED_PANELS_PER_CELL = len(EXPECTED_SEEDS)
EXPECTED_DATES_PER_PANEL = len(EXPECTED_TARGET_TIMES)
EXPECTED_RECOVERY_CELLS = (
    len(EXPECTED_FAMILIES)
    * len(EXPECTED_SCALES)
    * len(EXPECTED_QUERIES)
    * len(EXPECTED_HORIZONS)
)
NORMAL_APPROXIMATION_Z_95 = 1.96


class AuditInputError(ValueError):
    """Raised when a frozen input cannot be safely bound to this audit."""


@dataclass(frozen=True)
class InputPaths:
    """Absolute or repository-relative paths consumed by the audit."""

    results: Path
    manifest: Path
    authorization: Path
    register: Path
    candidate: Path
    comparator_registry: Path
    failure_metric_schema: Path
    plan: Path
    e4_audit: Path
    execution_complete: Path
    terminal_inventory: Path
    workspace_authorization: Path


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _finite_positive(value: Any) -> bool:
    return _is_finite_number(value) and float(value) > 0.0


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _recursive_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _recursive_sort(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_recursive_sort(item) for item in value]
    return value


def _canonical_v2_item_bytes(value: Any) -> bytes:
    return json.dumps(
        _recursive_sort(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _require_v2_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuditInputError(f"{label} must be a non-null JSON object")
    return value


def _require_v2_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise AuditInputError(f"{label} must be a non-null lowercase SHA-256")
    return value


def _resolve_inventory_path(raw_path: Any, project_root: Path) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise AuditInputError("terminal inventory artifact path is missing")
    path = Path(raw_path).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def validate_authorization_v2(
    authorization: Mapping[str, Any],
    *,
    register_path: Path,
    register: Mapping[str, Any],
    frozen_paths: Mapping[str, Path],
    frozen_values: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed on the v2 register, item, and frozen E4-r3 binding chain."""

    authorization = _require_v2_mapping(authorization, "authorization")
    if authorization.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION:
        raise AuditInputError("legacy or unsupported authorization schema")
    if any(key in authorization for key in ("frozen_inputs", "authorized_register_items", "execution_policy")):
        raise AuditInputError("legacy authorization fields are prohibited")
    authorized_scope = _require_v2_mapping(
        authorization.get("authorized_scope"), "authorization.authorized_scope"
    )
    rec_m2_actions = authorized_scope.get("REC_M2")
    if not isinstance(rec_m2_actions, list) or V2_REQUIRED_REC_M2_ACTION not in rec_m2_actions:
        raise AuditInputError("authorization.authorized_scope.REC_M2 is not bound")
    current_task_limits = _require_v2_mapping(
        authorization.get("current_task_limits"), "authorization.current_task_limits"
    )
    for field, expected in V2_REQUIRED_TASK_LIMITS.items():
        if current_task_limits.get(field) != expected:
            raise AuditInputError(f"authorization.current_task_limits.{field} drifted")

    binding = _require_v2_mapping(authorization.get("binding"), "authorization.binding")
    declared_register = binding.get("decision_register_path")
    if not isinstance(declared_register, str) or not declared_register:
        raise AuditInputError("authorization.binding.decision_register_path is required")
    project_root = Path(__file__).resolve().parents[2]
    expected_register_path = Path(declared_register).expanduser()
    if not expected_register_path.is_absolute():
        expected_register_path = project_root / expected_register_path
    observed_register_path = Path(register_path).expanduser().resolve(strict=True)
    if observed_register_path != expected_register_path.resolve():
        raise AuditInputError("decision-register path is not the v2-bound path")
    expected_register_sha = _require_v2_sha(
        binding.get("decision_register_sha256"),
        "authorization.binding.decision_register_sha256",
    )
    observed_register_sha = sha256_file(observed_register_path)
    if observed_register_sha != expected_register_sha:
        raise AuditInputError("decision-register SHA-256 mismatch")
    if binding.get("item_payload_sha256_algorithm") != "recursive_object_key_sort_then_JSON.stringify_utf8_no_whitespace":
        raise AuditInputError("unsupported item payload canonicalization")
    item_payloads = _require_v2_mapping(binding.get("item_payloads"), "authorization.binding.item_payloads")
    expected_item_sha = _require_v2_sha(
        item_payloads.get(V2_ITEM_BINDING["item_id"]),
        f"authorization.binding.item_payloads.{V2_ITEM_BINDING['item_id']}",
    )

    register_items = register.get("items")
    if not isinstance(register_items, list):
        raise AuditInputError("decision register.items must be a non-null array")
    selected = []
    for item in register_items:
        if not isinstance(item, Mapping) or item.get("item_id") != V2_ITEM_BINDING["item_id"]:
            continue
        source = item.get("calibration_source")
        if isinstance(source, Mapping) and source.get("calibration_id") == V2_ITEM_BINDING["calibration_id"] and item.get("item_index") == V2_ITEM_BINDING["item_index"]:
            selected.append(item)
    if len(selected) != 1:
        raise AuditInputError("exact current register item mapping is not unique")
    register_item = selected[0]
    for field in ("item_id", "item_index", "priority", "action_class"):
        if register_item.get(field) != V2_ITEM_BINDING[field]:
            raise AuditInputError(f"current register item {field} drifted")
    if hashlib.sha256(_canonical_v2_item_bytes(register_item)).hexdigest() != expected_item_sha:
        raise AuditInputError("canonical register item payload SHA-256 mismatch")

    frozen = _require_v2_mapping(
        authorization.get("frozen_e4_r3_inputs"),
        "authorization.frozen_e4_r3_inputs",
    )
    actual_hashes: dict[str, str] = {}
    for role, field in V2_FROZEN_HASH_FIELDS.items():
        expected = _require_v2_sha(frozen.get(field), f"authorization.frozen_e4_r3_inputs.{field}")
        path = frozen_paths.get(role)
        if not isinstance(path, Path):
            raise AuditInputError(f"frozen input path is missing: {role}")
        resolved = path.expanduser().resolve(strict=True)
        actual = sha256_file(resolved)
        if actual != expected:
            raise AuditInputError(f"frozen input SHA-256 mismatch: {role}")
        actual_hashes[role] = actual
    workspace_path = frozen_paths.get("workspace_authorization")
    if not isinstance(workspace_path, Path):
        raise AuditInputError("workspace authorization path is required for the E4 chain")
    workspace_hash = sha256_file(workspace_path.expanduser().resolve(strict=True))
    workspace = _require_v2_mapping(frozen_values.get("workspace_authorization"), "workspace authorization")
    candidate = _require_v2_mapping(frozen_values.get("candidate"), "frozen candidate")
    candidate_id = candidate.get("candidate_id")
    candidate_sha = actual_hashes["candidate"]
    if not isinstance(candidate_id, str) or not candidate_id:
        raise AuditInputError("candidate.candidate_id is required")
    if workspace.get("candidate_id") != candidate_id or workspace.get("candidate_sha256") != candidate_sha:
        raise AuditInputError("workspace authorization candidate chain mismatch")
    for role in ("results", "execution_manifest", "execution_complete"):
        value = _require_v2_mapping(frozen_values.get(role), f"frozen {role}")
        if value.get("authorization_sha256") != workspace_hash or value.get("candidate_sha256") != candidate_sha:
            raise AuditInputError(f"frozen {role} authorization/candidate chain mismatch")
    inventory = _require_v2_mapping(frozen_values.get("terminal_inventory"), "terminal inventory")
    artifacts = inventory.get("artifacts")
    if not isinstance(artifacts, list):
        raise AuditInputError("terminal inventory.artifacts is required")
    inventory_roles = {role: frozen_paths[role] for role in V2_FROZEN_HASH_FIELDS if role != "terminal_inventory"}
    inventory_roles["workspace_authorization"] = workspace_path
    for role, path in inventory_roles.items():
        resolved = path.expanduser().resolve(strict=True)
        matches = [entry for entry in artifacts if isinstance(entry, Mapping) and _resolve_inventory_path(entry.get("path"), project_root) == resolved]
        if len(matches) != 1 or matches[0].get("sha256") != sha256_file(resolved):
            raise AuditInputError(f"terminal inventory chain mismatch: {role}")
    return {
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "decision_register_sha256": observed_register_sha,
        "register_item": dict(register_item),
        "item_payload_sha256": expected_item_sha,
        "frozen_input_sha256": actual_hashes,
        "workspace_authorization_sha256": workspace_hash,
        "e4_chain": {"complete": True, "candidate_id": candidate_id},
        "scope_binding": {
            "rec_m2_action": V2_REQUIRED_REC_M2_ACTION,
            "m2_scientific_analysis": V2_REQUIRED_TASK_LIMITS["m2_scientific_analysis"],
        },
    }


EXECUTION_AUTHORIZATION_SCHEMA_VERSION = "ncs-post-acceptance-recovery-m2b2-execution-authorization-v1"
EXECUTION_AUTHORIZATION_STATUS = "PLANNED_PENDING_INDEPENDENT_PREFLIGHT_ACCEPTANCE"
EXECUTION_AUTHORIZATION_FILENAME_PREFIX = "NCS_POST_ACCEPTANCE_RECOVERY_M2B2_EXECUTION_AUTHORIZATION_V1_"
EXECUTION_M2A_RECEIPT_RELATIVE_PATH = "refine-logs/NCS_POST_ACCEPTANCE_RECOVERY_M2A_REPAIR_RECEIPT_V1_20260810_222232.json"
EXECUTION_SOURCE_AUTHORIZATION_V2_SHA256 = "7d65768118f5517b76a01acef3b7f15390a60ed8a50f09ebae4379330dd6ac59"
EXECUTION_M2A_RECEIPT_SHA256 = "b98f8a4dc6dd36ee28426182d9320d0696880867544a0cc05dd6c1fb5e943395"
EXECUTION_REGISTER_SHA256 = "c970d82959aa447a5ad3d7d4a02008e98c6c81552991b4dcb97a1e082b901fb2"
EXECUTION_WORKSPACE_AUTHORIZATION_SHA256 = "73c135edef24e8b4310297070d127d4be6f12d857e009fe178d62e30dba694e6"
EXECUTION_CODE_FILES = (
    "scripts/experiments/analyze_cal_e01_75.py",
    "scripts/experiments/test_analyze_cal_e01_75.py",
    "scripts/experiments/analyze_cal_e02_128.py",
    "scripts/experiments/test_analyze_cal_e02_128.py",
    "scripts/experiments/analyze_cal_e02_135.py",
    "scripts/experiments/test_analyze_cal_e02_135.py",
    "scripts/experiments/analyze_cal_e03_164.py",
    "tests/test_analyze_cal_e03_164.py",
)
EXECUTION_ITEM_SHA256 = {
    "V1-026": "eb30214e8c353b27d446c1c77242bd6b2dd246841150205c8f339ddafc8f7e20",
    "V1-033": "79937fd8b053e2bc7fd9abb864938b35a72134ecf93f5f621d7c8088fd383630",
    "V1-035": "c9b9c201f94a7fd37b2049bfc44220258947f22483e769b39c19253a37e55ee8",
    "V1-045": "25cd8fbf2e623cfd2fbcdc163f50959f1beb8e8cb1b59322da78d191e802cf82",
}
EXECUTION_E4_LEAF_SHA256 = {
    "results": "09394a3c68a0babcc9cda7f704b78245553d61a40131e91ff1fc9157ece85032",
    "execution_manifest": "42d2b2da3649c4cfb7f72060ba9ff0587f108f7609177c23d5f68fda1f9a536d",
    "execution_complete": "18e7dc81acf8c75d53835bcc751d8f37a89645357d302349631dc86d839a775b",
    "terminal_inventory": "5cf086c49ea72e694e76bba9faf976950960b2a42951eec26a262d7b276f9046",
    "candidate": "0c49bca63813316ed65119f0f891074a290bd03392e5e9121c435dc936c199f6",
}
EXECUTION_SCOPE = {
    "run_type": "deterministic_read_only_derived_m2",
    "run_count": 2,
    "run_ids": ["primary", "duplicate"],
    "read_only_derived": True,
    "deterministic": True,
    "register_mutation": False,
    "manuscript_mutation": False,
    "e4_r3_mutation": False,
    "claim_activation": "NOT_AUTHORIZED",
    "promotion": "NOT_AUTHORIZED",
    "rcep_nyc": "NOT_AUTHORIZED",
    "s1_s4": "NOT_AUTHORIZED",
    "n100_n200": "NOT_AUTHORIZED",
}
EXECUTION_ARTIFACT_BOUNDARY = {
    "CAL-E01:75": {
        "allowed": ["raw_comparator", "raw_paired_differences", "status_inventory"],
        "fresh_freezes": False,
    },
    "CAL-E02:128": {"allowed": ["descriptive_only"], "fresh_freezes": False},
    "CAL-E02:135": {"allowed": ["descriptive_only"], "fresh_freezes": False},
    "CAL-E03:164": {
        "allowed_scales": [20, 50],
        "n100": "NOT_RUN/ABSTAIN",
        "n200": "NOT_RUN/ABSTAIN",
    },
}
EXECUTION_ARTIFACT_PREFIXES = [
    "cal-e01-75-",
    "cal-e02-128-",
    "cal-e02-135-",
    "cal-e03-164-",
]
EXECUTION_ROOT_HEX_LENGTHS = {
    "cal-e01-75-": [16],
    "cal-e02-128-": [64],
    "cal-e02-135-": [16],
    "cal-e03-164-": [64],
}
EXECUTION_RUN_LAYOUT = {
    "primary": "primary/<one-content-addressed-root-per-authorized-analyzer>",
    "duplicate": "duplicate/<one-content-addressed-root-per-authorized-analyzer>",
}
EXECUTION_CONTINUATION_POLICY = {
    "primary": {
        "first_call": "declared_parent_absent",
        "later_calls": "only_primary_directory_with_prior_unique_roots",
        "duplicate_run_forbidden": True,
    },
    "duplicate": {
        "first_call": "completed_primary_directory_with_all_four_roots",
        "later_calls": "only_primary_and_duplicate_directories",
        "root_reuse_forbidden": True,
    },
}
EXECUTION_CONTEXT_KEYS = (
    "source_authorization_v2",
    "m2a_repair_receipt",
    "decision_register",
    "e4_results",
    "e4_execution_manifest",
    "e4_execution_complete",
    "e4_terminal_inventory",
    "e4_candidate",
    "workspace_authorization",
)


class ExecutionAuthorizationError(ValueError):
    """Raised when the separate M2 execution authorization is not exact."""


def _execution_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExecutionAuthorizationError(f"{label} must be a JSON object")
    return value


def _execution_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ExecutionAuthorizationError(f"{label} must be a lowercase SHA-256")
    return value


def _execution_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ExecutionAuthorizationError(f"{label} has missing or unsupported fields")


def _load_execution_json(path: Path, label: str) -> Any:
    try:
        raw = path.read_bytes()
        return json.loads(raw.decode("utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ExecutionAuthorizationError(f"cannot read {label}: {error}") from error


def _resolve_execution_path(raw_path: Any, project_root: Path, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise ExecutionAuthorizationError(f"{label} path is required")
    path = Path(raw_path).expanduser()
    if any(part in {".", ".."} for part in path.parts):
        raise ExecutionAuthorizationError(f"{label} path traversal is prohibited")
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _execution_context_path(observed_paths: Mapping[str, Path], key: str) -> Path:
    path = observed_paths.get(key)
    if not isinstance(path, Path):
        raise ExecutionAuthorizationError(f"execution context is missing: {key}")
    try:
        return path.expanduser().resolve(strict=True)
    except OSError as error:
        raise ExecutionAuthorizationError(f"execution context path is unavailable: {key}") from error


def _execution_path_has_traversal(path: Path, label: str) -> None:
    if any(part in {".", ".."} for part in path.parts):
        raise ExecutionAuthorizationError(f"{label} path traversal is prohibited")


def _execution_root_entries(run_directory: Path, label: str) -> dict[str, Path]:
    if run_directory.is_symlink() or not run_directory.is_dir():
        raise ExecutionAuthorizationError(f"{label} must be a non-symlink directory")
    roots: dict[str, Path] = {}
    try:
        children = sorted(run_directory.iterdir(), key=lambda child: child.name)
    except OSError as error:
        raise ExecutionAuthorizationError(f"cannot inspect {label}: {error}") from error
    for child in children:
        if child.is_symlink() or not child.is_dir():
            raise ExecutionAuthorizationError(f"{label} contains a symlink or non-directory child")
        matching_prefixes = [prefix for prefix in EXECUTION_ARTIFACT_PREFIXES if child.name.startswith(prefix)]
        if len(matching_prefixes) != 1:
            raise ExecutionAuthorizationError(f"{label} contains an unknown or malformed root")
        prefix = matching_prefixes[0]
        suffix = child.name[len(prefix) :]
        if len(suffix) not in EXECUTION_ROOT_HEX_LENGTHS[prefix] or re.fullmatch(r"[0-9a-f]+", suffix) is None:
            raise ExecutionAuthorizationError(f"{label} contains an invalid content-addressed root")
        if prefix in roots:
            raise ExecutionAuthorizationError(f"{label} reuses an analyzer root prefix")
        roots[prefix] = child
    return roots


def _execution_require_complete_primary(primary_directory: Path) -> dict[str, Path]:
    roots = _execution_root_entries(primary_directory, "primary run directory")
    if set(roots) != set(EXECUTION_ARTIFACT_PREFIXES):
        raise ExecutionAuthorizationError("primary continuation is not complete for all four analyzers")
    return roots


def _check_execution_binding(
    declared: Mapping[str, Any],
    observed_path: Path,
    expected_sha256: str,
    label: str,
    project_root: Path,
) -> str:
    _execution_exact_keys(declared, {"path", "raw_sha256"}, label)
    bound_path = _resolve_execution_path(declared.get("path"), project_root, f"{label}.path")
    observed_path = observed_path.expanduser().resolve(strict=True)
    if bound_path != observed_path:
        raise ExecutionAuthorizationError(f"{label} path drifted")
    declared_sha = _execution_sha(declared.get("raw_sha256"), f"{label}.raw_sha256")
    observed_sha = sha256_file(observed_path)
    if declared_sha != observed_sha or observed_sha != expected_sha256:
        raise ExecutionAuthorizationError(f"{label} SHA-256 drifted")
    return observed_sha


def _validate_execution_authorization_common(
    execution_authorization_path: Path | None,
    *,
    output_root: Path,
    run_id: str,
    observed_paths: Mapping[str, Path],
    artifact_prefix: str,
    v2_validator: Callable[..., dict[str, Any]] = validate_authorization_v2,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Validate the separate planned M2 execution authorization before writing."""

    project_root = (project_root or Path(__file__).resolve().parents[2]).expanduser().resolve()
    if execution_authorization_path is None:
        raise ExecutionAuthorizationError("separate execution authorization is required")
    execution_path = Path(execution_authorization_path).expanduser()
    if execution_path.is_symlink() or not execution_path.is_file():
        raise ExecutionAuthorizationError("execution authorization must be a regular file")
    if not execution_path.name.startswith(EXECUTION_AUTHORIZATION_FILENAME_PREFIX) or execution_path.suffix != ".json":
        raise ExecutionAuthorizationError("execution authorization filename is not versioned")
    auth = _execution_mapping(_load_execution_json(execution_path.resolve(), "execution authorization"), "execution authorization")
    _execution_exact_keys(
        auth,
        {
            "schema_version",
            "authorization_id",
            "authorized_at",
            "status",
            "purpose",
            "source_bindings",
            "implementation",
            "scope",
            "artifact_boundary",
            "output_plan",
            "provenance",
        },
        "execution authorization",
    )
    if auth.get("schema_version") != EXECUTION_AUTHORIZATION_SCHEMA_VERSION:
        raise ExecutionAuthorizationError("legacy or unsupported execution authorization schema")
    if auth.get("status") != EXECUTION_AUTHORIZATION_STATUS:
        raise ExecutionAuthorizationError("execution authorization is not pending independent preflight acceptance")
    if not isinstance(auth.get("authorization_id"), str) or not re.fullmatch(
        r"ncs-post-acceptance-recovery-m2b2-execution-[a-z0-9-]+", auth["authorization_id"]
    ):
        raise ExecutionAuthorizationError("execution authorization id is not versioned")
    if auth.get("purpose") != "planned_shared_two_run_read_only_derived_m2b2":
        raise ExecutionAuthorizationError("execution authorization purpose is out of scope")

    context = _execution_mapping(observed_paths, "execution context")
    if set(context) != set(EXECUTION_CONTEXT_KEYS):
        raise ExecutionAuthorizationError("execution context has missing or unsupported paths")
    observed = {key: _execution_context_path(context, key) for key in EXECUTION_CONTEXT_KEYS}

    source_bindings = _execution_mapping(auth.get("source_bindings"), "source_bindings")
    _execution_exact_keys(
        source_bindings,
        {
            "source_authorization_v2",
            "m2a_repair_receipt",
            "decision_register",
            "frozen_e4_r3_inputs",
            "workspace_authorization_chain",
        },
        "source_bindings",
    )
    _check_execution_binding(
        _execution_mapping(source_bindings["source_authorization_v2"], "source_authorization_v2"),
        observed["source_authorization_v2"],
        EXECUTION_SOURCE_AUTHORIZATION_V2_SHA256,
        "source_authorization_v2",
        project_root,
    )
    _check_execution_binding(
        _execution_mapping(source_bindings["m2a_repair_receipt"], "m2a_repair_receipt"),
        observed["m2a_repair_receipt"],
        EXECUTION_M2A_RECEIPT_SHA256,
        "m2a_repair_receipt",
        project_root,
    )
    register_binding = _execution_mapping(source_bindings["decision_register"], "decision_register")
    _execution_exact_keys(register_binding, {"path", "raw_sha256", "canonical_item_sha256"}, "decision_register")
    _check_execution_binding(
        {"path": register_binding["path"], "raw_sha256": register_binding["raw_sha256"]},
        observed["decision_register"],
        EXECUTION_REGISTER_SHA256,
        "decision_register",
        project_root,
    )
    declared_items = _execution_mapping(register_binding.get("canonical_item_sha256"), "canonical_item_sha256")
    if dict(declared_items) != EXECUTION_ITEM_SHA256:
        raise ExecutionAuthorizationError("canonical item hash binding is not the current four-item set")
    register = _execution_mapping(_load_execution_json(observed["decision_register"], "decision register"), "decision register")
    register_items = register.get("items")
    if not isinstance(register_items, list):
        raise ExecutionAuthorizationError("decision register.items is required")
    for item_id, expected_item_sha in EXECUTION_ITEM_SHA256.items():
        matches = [item for item in register_items if isinstance(item, Mapping) and item.get("item_id") == item_id]
        if len(matches) != 1 or _sha256_bytes(_canonical_v2_item_bytes(matches[0])) != expected_item_sha:
            raise ExecutionAuthorizationError(f"canonical register item hash drifted: {item_id}")

    frozen_binding = _execution_mapping(source_bindings["frozen_e4_r3_inputs"], "frozen_e4_r3_inputs")
    if set(frozen_binding) != set(EXECUTION_E4_LEAF_SHA256):
        raise ExecutionAuthorizationError("frozen E4-r3 leaf set drifted")
    frozen_paths = {
        "results": observed["e4_results"],
        "execution_manifest": observed["e4_execution_manifest"],
        "execution_complete": observed["e4_execution_complete"],
        "terminal_inventory": observed["e4_terminal_inventory"],
        "candidate": observed["e4_candidate"],
        "workspace_authorization": observed["workspace_authorization"],
    }
    frozen_values = {
        role: _execution_mapping(_load_execution_json(path, f"frozen {role}"), f"frozen {role}")
        for role, path in frozen_paths.items()
    }
    for role, expected_sha256 in EXECUTION_E4_LEAF_SHA256.items():
        _check_execution_binding(
            _execution_mapping(frozen_binding[role], f"frozen_e4_r3_inputs.{role}"),
            observed[
                {
                    "results": "e4_results",
                    "execution_manifest": "e4_execution_manifest",
                    "execution_complete": "e4_execution_complete",
                    "terminal_inventory": "e4_terminal_inventory",
                    "candidate": "e4_candidate",
                }[role]
            ],
            expected_sha256,
            f"frozen_e4_r3_inputs.{role}",
            project_root,
        )
    workspace_binding = _execution_mapping(source_bindings["workspace_authorization_chain"], "workspace_authorization_chain")
    _check_execution_binding(
        workspace_binding,
        observed["workspace_authorization"],
        EXECUTION_WORKSPACE_AUTHORIZATION_SHA256,
        "workspace_authorization_chain",
        project_root,
    )

    source_v2 = _execution_mapping(
        _load_execution_json(observed["source_authorization_v2"], "source authorization v2"),
        "source authorization v2",
    )
    if source_v2.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION:
        raise ExecutionAuthorizationError("source authorization v2 is missing or legacy")
    source_limits = _execution_mapping(source_v2.get("current_task_limits"), "source authorization v2 limits")
    if source_limits.get("m2_scientific_analysis") != "BLOCKED_IN_THIS_TASK":
        raise ExecutionAuthorizationError("source v2 m2 scientific-analysis limit was activated")
    try:
        v2_binding = v2_validator(
            source_v2,
            register_path=observed["decision_register"],
            register=register,
            frozen_paths=frozen_paths,
            frozen_values=frozen_values,
        )
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        raise ExecutionAuthorizationError(f"source authorization v2 chain rejected: {error}") from error

    m2a = _execution_mapping(
        _load_execution_json(observed["m2a_repair_receipt"], "REC-M2A repair receipt"),
        "REC-M2A repair receipt",
    )
    if m2a.get("schema_version") != "ncs-post-acceptance-recovery-m2a-repair-receipt-v1" or m2a.get("result") != "REC-M2A_PASS":
        raise ExecutionAuthorizationError("REC-M2A repair receipt is not the accepted v1 receipt")
    m2a_sources = _execution_mapping(m2a.get("source_bindings"), "REC-M2A source_bindings")
    if m2a_sources.get("register_sha256") != EXECUTION_REGISTER_SHA256 or m2a_sources.get("canonical_item_hashes") != EXECUTION_ITEM_SHA256:
        raise ExecutionAuthorizationError("REC-M2A receipt source binding drifted")
    m2a_scope = _execution_mapping(m2a.get("scope"), "REC-M2A scope")
    if m2a_scope.get("real_analyzer_cli_invoked") is not False or m2a_scope.get("scientific_results_generated") is not False:
        raise ExecutionAuthorizationError("REC-M2A receipt does not prove a non-scientific repair")
    m2a_v2 = _execution_mapping(_execution_mapping(m2a.get("provenance"), "REC-M2A provenance").get("authorization_v2"), "REC-M2A v2 provenance")
    if m2a_v2.get("sha256") != EXECUTION_SOURCE_AUTHORIZATION_V2_SHA256:
        raise ExecutionAuthorizationError("REC-M2A receipt v2 provenance drifted")

    implementation = _execution_mapping(auth.get("implementation"), "implementation")
    _execution_exact_keys(
        implementation,
        {"sha256_algorithm", "source_test_sha256", "source_test_bytes"},
        "implementation",
    )
    if implementation.get("sha256_algorithm") != "sha256(raw bytes)":
        raise ExecutionAuthorizationError("unsupported implementation hash algorithm")
    source_test_hashes = _execution_mapping(implementation.get("source_test_sha256"), "source_test_sha256")
    source_test_bytes = _execution_mapping(implementation.get("source_test_bytes"), "source_test_bytes")
    if set(source_test_hashes) != set(EXECUTION_CODE_FILES) or set(source_test_bytes) != set(EXECUTION_CODE_FILES):
        raise ExecutionAuthorizationError("execution code hash set is incomplete or contains unsupported files")
    for relative_path in EXECUTION_CODE_FILES:
        expected_sha256 = _execution_sha(source_test_hashes.get(relative_path), f"source_test_sha256.{relative_path}")
        code_path = (project_root / relative_path).resolve(strict=True)
        if sha256_file(code_path) != expected_sha256:
            raise ExecutionAuthorizationError(f"execution code SHA-256 drifted: {relative_path}")
        expected_bytes = source_test_bytes.get(relative_path)
        if isinstance(expected_bytes, bool) or not isinstance(expected_bytes, int) or expected_bytes < 0:
            raise ExecutionAuthorizationError(f"source_test_bytes.{relative_path} is invalid")
        if code_path.stat().st_size != expected_bytes:
            raise ExecutionAuthorizationError(f"execution code byte count drifted: {relative_path}")

    if auth.get("scope") != EXECUTION_SCOPE:
        raise ExecutionAuthorizationError("execution authorization scope or limit was activated")
    if auth.get("artifact_boundary") != EXECUTION_ARTIFACT_BOUNDARY:
        raise ExecutionAuthorizationError("artifact boundary drifted")

    output_plan = _execution_mapping(auth.get("output_plan"), "output_plan")
    _execution_exact_keys(
        output_plan,
        {
            "output_parent",
            "execution_id",
            "fresh_before_execution",
            "no_overwrite",
            "allowed_run_ids",
            "run_layout",
            "authorized_artifact_prefixes",
            "root_hex_lengths",
            "prohibited_path_tokens",
            "continuation_policy",
        },
        "output_plan",
    )
    if output_plan.get("allowed_run_ids") != ["primary", "duplicate"]:
        raise ExecutionAuthorizationError("output run set drifted")
    if (
        output_plan.get("run_layout") != EXECUTION_RUN_LAYOUT
        or output_plan.get("authorized_artifact_prefixes") != EXECUTION_ARTIFACT_PREFIXES
        or output_plan.get("root_hex_lengths") != EXECUTION_ROOT_HEX_LENGTHS
        or output_plan.get("continuation_policy") != EXECUTION_CONTINUATION_POLICY
        or output_plan.get("prohibited_path_tokens") != ["e4_r008", "E4_R008"]
    ):
        raise ExecutionAuthorizationError("output layout or quarantine refusal drifted")
    if output_plan.get("fresh_before_execution") is not True or output_plan.get("no_overwrite") is not True:
        raise ExecutionAuthorizationError("fresh/no-overwrite output policy is not enabled")
    declared_parent = _resolve_execution_path(output_plan.get("output_parent"), project_root, "output_plan.output_parent")
    output_parent_raw = Path(output_plan["output_parent"]).expanduser()
    _execution_path_has_traversal(output_parent_raw, "output_plan.output_parent")
    if declared_parent.is_symlink():
        raise ExecutionAuthorizationError("authorized output parent must not be a symlink")
    execution_id = output_plan.get("execution_id")
    if not isinstance(execution_id, str) or not re.fullmatch(r"rec-m2b2-[a-z0-9-]+", execution_id) or declared_parent.name != execution_id:
        raise ExecutionAuthorizationError("output execution id is not fresh and versioned")
    if len(declared_parent.parts) < 3 or declared_parent.parts[-3:-1] != ("refine-logs", "ncs_new_analysis_v2"):
        raise ExecutionAuthorizationError("output parent is outside refine-logs/ncs_new_analysis_v2")
    output_target_raw = Path(output_root).expanduser()
    _execution_path_has_traversal(output_target_raw, "output root")
    if not output_target_raw.is_absolute():
        output_target_raw = project_root / output_target_raw
    if output_target_raw.is_symlink() or output_target_raw.parent.is_symlink():
        raise ExecutionAuthorizationError("output root and its run directory must not be symlinks")
    output_target = output_target_raw.resolve()
    if any(token.lower() in str(output_target).lower() for token in ("e4_r008", "e4-r008")):
        raise ExecutionAuthorizationError("E4-r008 output paths are prohibited")
    if run_id not in ("primary", "duplicate"):
        raise ExecutionAuthorizationError("run id must be primary or duplicate")
    expected_run_directory = declared_parent / run_id
    if output_target.parent != expected_run_directory:
        raise ExecutionAuthorizationError("output root does not match the authorized two-run layout")
    if artifact_prefix not in EXECUTION_ARTIFACT_PREFIXES:
        raise ExecutionAuthorizationError("artifact prefix is not authorized")
    root_suffix = output_target.name[len(artifact_prefix) :] if output_target.name.startswith(artifact_prefix) else ""
    if (
        not output_target.name.startswith(artifact_prefix)
        or len(root_suffix) not in EXECUTION_ROOT_HEX_LENGTHS[artifact_prefix]
        or re.fullmatch(r"[0-9a-f]+", root_suffix) is None
    ):
        raise ExecutionAuthorizationError("output root is not an exact content-addressed analyzer root")
    if output_target.exists() or output_target.is_symlink():
        raise ExecutionAuthorizationError("output run root already exists; reuse is prohibited")

    if run_id == "primary":
        if not declared_parent.exists():
            pass
        else:
            if not declared_parent.is_dir():
                raise ExecutionAuthorizationError("existing output parent is not a directory")
            parent_children = sorted(declared_parent.iterdir(), key=lambda child: child.name)
            if any(child.is_symlink() or not child.is_dir() for child in parent_children):
                raise ExecutionAuthorizationError("output parent contains a symlink or non-directory child")
            if {child.name for child in parent_children} != {"primary"}:
                raise ExecutionAuthorizationError("primary continuation has unexpected run siblings")
            existing_roots = _execution_root_entries(declared_parent / "primary", "primary run directory")
            if not existing_roots:
                raise ExecutionAuthorizationError("primary continuation has no committed analyzer roots")
            if artifact_prefix in existing_roots:
                raise ExecutionAuthorizationError("primary analyzer root prefix is already committed")
    else:
        if not declared_parent.is_dir() or declared_parent.is_symlink():
            raise ExecutionAuthorizationError("duplicate requires the authorized output parent")
        parent_children = sorted(declared_parent.iterdir(), key=lambda child: child.name)
        if any(child.is_symlink() or not child.is_dir() for child in parent_children):
            raise ExecutionAuthorizationError("output parent contains a symlink or non-directory child")
        child_names = {child.name for child in parent_children}
        if child_names not in ({"primary"}, {"primary", "duplicate"}):
            raise ExecutionAuthorizationError("duplicate output layout has unexpected run siblings")
        _execution_require_complete_primary(declared_parent / "primary")
        if "duplicate" in child_names:
            existing_duplicate_roots = _execution_root_entries(
                declared_parent / "duplicate", "duplicate run directory"
            )
            if not existing_duplicate_roots:
                raise ExecutionAuthorizationError("duplicate continuation has no committed analyzer roots")
            if artifact_prefix in existing_duplicate_roots:
                raise ExecutionAuthorizationError("duplicate analyzer root prefix is already committed")

    provenance = _execution_mapping(auth.get("provenance"), "provenance")
    if provenance != {
        "parent_task": "019fbdde-2c02-7662-b9d2-9dc2b70e1253",
        "delegated_model": "gpt-5.6-luna",
        "delegated_reasoning_effort": "max",
        "independent_preflight_required": True,
        "m2_execution_proof": "NOT_ESTABLISHED",
        "historic_m2b1_status_preserved": True,
    }:
        raise ExecutionAuthorizationError("execution authorization provenance is not the planned M2B2 provenance")
    return {
        "schema_version": EXECUTION_AUTHORIZATION_SCHEMA_VERSION,
        "authorization_id": auth["authorization_id"],
        "status": auth["status"],
        "run_id": run_id,
        "output_root": str(output_target),
        "fresh_output_required": True,
        "source_authorization_v2_sha256": EXECUTION_SOURCE_AUTHORIZATION_V2_SHA256,
        "m2a_receipt_sha256": EXECUTION_M2A_RECEIPT_SHA256,
        "v2_binding": v2_binding,
    }


def validate_execution_authorization(
    execution_authorization_path: Path | None,
    *,
    output_root: Path,
    run_id: str,
    observed_paths: Mapping[str, Path],
    artifact_prefix: str = "cal-e01-75-",
    project_root: Path | None = None,
) -> dict[str, Any]:
    try:
        return _validate_execution_authorization_common(
            execution_authorization_path,
            output_root=output_root,
            run_id=run_id,
            observed_paths=observed_paths,
            artifact_prefix=artifact_prefix,
            v2_validator=validate_authorization_v2,
            project_root=project_root,
        )
    except ExecutionAuthorizationError as error:
        raise AuditInputError(str(error)) from error


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise AuditInputError(f"cannot read JSON input {path}: {error}") from error


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuditInputError(f"{label} must be a JSON object")
    return value


def _status_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in STATUS_SCHEMA}
    for row in rows:
        status = row.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def _counter_to_status_counts(counter: Counter[str]) -> dict[str, int]:
    return {status: int(counter.get(status, 0)) for status in STATUS_SCHEMA}


def _mean(values: Sequence[float]) -> float | None:
    return float(statistics.fmean(values)) if values else None


def _sample_std(values: Sequence[float]) -> float | None:
    return float(statistics.stdev(values)) if len(values) >= 2 else None


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def _distribution(rows: Iterable[Mapping[str, Any]], field: str) -> dict[str, Any]:
    values = [float(row[field]) for row in rows if _is_finite_number(row.get(field))]
    return {
        "field": field,
        "n": len(values),
        "min": min(values) if values else None,
        "q25": _percentile(values, 0.25),
        "median": _percentile(values, 0.50),
        "mean": _mean(values),
        "q75": _percentile(values, 0.75),
        "max": max(values) if values else None,
        "sample_std": _sample_std(values),
    }


def _cell_tuple(row: Mapping[str, Any]) -> tuple[str, int, str, int]:
    return (
        str(row["family"]),
        int(row["n"]),
        str(row["query_class"]),
        int(row["horizon"]),
    )


def _cell_label(cell: tuple[str, int, str, int]) -> dict[str, Any]:
    family, n, query_class, horizon = cell
    return {
        "family": family,
        "n": n,
        "query_class": query_class,
        "horizon": horizon,
    }


def _cell_sort_key(cell: tuple[str, int, str, int]) -> tuple[Any, ...]:
    return (cell[0], cell[1], cell[2], cell[3])


def _expected_cells() -> tuple[tuple[str, int, str, int], ...]:
    return tuple(
        (family, n, query_class, horizon)
        for family in EXPECTED_FAMILIES
        for n in EXPECTED_SCALES
        for query_class in EXPECTED_QUERIES
        for horizon in EXPECTED_HORIZONS
    )


def _expected_method_cell_keys(methods: Sequence[str]) -> set[tuple[Any, ...]]:
    return {
        (*cell, method)
        for cell in _expected_cells()
        for method in methods
    }


def _endpoint_key(row: Mapping[str, Any]) -> tuple[int, int]:
    return (int(row["seed"]), int(row["target_time"]))


def _record_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "family": row.get("family"),
        "n": row.get("n"),
        "query_class": row.get("query_class"),
        "horizon": row.get("horizon"),
        "method": row.get("method"),
        "seed": row.get("seed"),
        "target_time": row.get("target_time"),
        "status": row.get("status"),
        "operator_mse": row.get("operator_mse"),
        "response_mse": row.get("response_mse"),
    }


def _sequence_matches(left: Sequence[Any], right: Sequence[Any]) -> bool:
    if len(left) != len(right):
        return False
    return all(
        _is_finite_number(a)
        and _is_finite_number(b)
        and math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-15)
        for a, b in zip(left, right)
    )


def compute_normal_approximation_ci(
    values: Sequence[float], *, confidence_level: float = 0.95
) -> dict[str, Any]:
    """Return a deterministic two-sided normal-approximation interval.

    The frozen E4-r3 output does not serialize the CI construction for the
    paired log-ratio metric. This fixed calculation is therefore descriptive
    and independent, not a claim that the missing predeclared CI was present.
    """

    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one")
    finite_values = [float(value) for value in values if _is_finite_number(value)]
    result: dict[str, Any] = {
        "method": "normal_approximation_two_sided",
        "confidence_level": float(confidence_level),
        "n": len(finite_values),
        "mean": _mean(finite_values),
        "sample_std": _sample_std(finite_values),
        "standard_error": None,
        "lower": None,
        "upper": None,
    }
    if len(finite_values) < 2:
        return result
    sample_std = float(statistics.stdev(finite_values))
    standard_error = sample_std / math.sqrt(len(finite_values))
    if math.isclose(confidence_level, 0.95, rel_tol=0.0, abs_tol=1e-15):
        critical_value = NORMAL_APPROXIMATION_Z_95
    else:
        critical_value = NormalDist().inv_cdf(0.5 + confidence_level / 2.0)
    margin = critical_value * standard_error
    result.update(
        {
            "standard_error": standard_error,
            "critical_value": critical_value,
            "lower": float(statistics.fmean(finite_values) - margin),
            "upper": float(statistics.fmean(finite_values) + margin),
        }
    )
    return result


def build_panel_log_error_ratio(
    rows: Iterable[Mapping[str, Any]],
    *,
    candidate_method: str,
    comparator_method: str,
    expected_target_times: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Summarize paired per-date errors for one panel.

    A panel value is the median over same-endpoint ``log(candidate/comparator)``
    values. Failed, non-finite, missing, and non-positive endpoints are kept in
    the counts and are never imputed.
    """

    selected = [
        row
        for row in rows
        if row.get("method") in {candidate_method, comparator_method}
    ]
    endpoint_times = tuple(
        sorted(
            set(int(time) for time in expected_target_times)
            if expected_target_times is not None
            else {
                int(row["target_time"])
                for row in selected
                if "target_time" in row
            }
        )
    )
    indexed: dict[tuple[int, str], Mapping[str, Any]] = {}
    duplicate_count = 0
    for row in selected:
        key = (int(row["target_time"]), str(row["method"]))
        if key in indexed:
            duplicate_count += 1
        indexed[key] = row

    candidate_status = Counter[str]()
    comparator_status = Counter[str]()
    response_ratios: list[float] = []
    operator_ratios: list[float] = []
    missing_count = 0
    nonfinite_or_failed_count = 0
    for target_time in endpoint_times:
        candidate = indexed.get((target_time, candidate_method))
        comparator = indexed.get((target_time, comparator_method))
        if candidate is not None:
            candidate_status[str(candidate.get("status"))] += 1
        if comparator is not None:
            comparator_status[str(comparator.get("status"))] += 1
        if candidate is None or comparator is None:
            missing_count += 1
            continue
        if (
            candidate.get("status") != STATUS_AVAILABLE
            or comparator.get("status") != STATUS_AVAILABLE
            or not _finite_positive(candidate.get("response_mse"))
            or not _finite_positive(comparator.get("response_mse"))
            or not _finite_positive(candidate.get("operator_mse"))
            or not _finite_positive(comparator.get("operator_mse"))
        ):
            nonfinite_or_failed_count += 1
            continue
        response_ratios.append(
            math.log(float(candidate["response_mse"]) / float(comparator["response_mse"]))
        )
        operator_ratios.append(
            math.log(float(candidate["operator_mse"]) / float(comparator["operator_mse"]))
        )

    declared_count = len(endpoint_times)
    paired_count = len(response_ratios)
    if paired_count == declared_count and declared_count > 0 and duplicate_count == 0:
        status = STATUS_AVAILABLE
    elif paired_count > 0:
        status = "PARTIAL_COMMON_COMPLETION"
    else:
        status = "NO_COMMON_COMPLETION"
    return {
        "status": status,
        "declared_count": declared_count,
        "paired_count": paired_count,
        "missing_count": missing_count,
        "nonfinite_or_failed_count": nonfinite_or_failed_count,
        "duplicate_endpoint_count": duplicate_count,
        "candidate_status_counts": _counter_to_status_counts(candidate_status),
        "comparator_status_counts": _counter_to_status_counts(comparator_status),
        "response_log_error_ratio": (
            float(statistics.median(response_ratios)) if response_ratios else None
        ),
        "operator_log_error_ratio": (
            float(statistics.median(operator_ratios)) if operator_ratios else None
        ),
    }


def reconstruct_paired_differences(
    rows: Iterable[Mapping[str, Any]],
    *,
    candidate_method: str,
    comparator_method: str,
) -> dict[str, Any]:
    """Recompute the frozen executor's common-completion difference arrays."""

    indexed: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    base_keys: set[tuple[Any, ...]] = set()
    candidate_status = Counter[str]()
    comparator_status = Counter[str]()
    for row in rows:
        method = row.get("method")
        if method not in {candidate_method, comparator_method}:
            continue
        base = (
            str(row["family"]),
            int(row["n"]),
            int(row["seed"]),
            str(row["query_class"]),
            int(row["horizon"]),
            int(row["target_time"]),
        )
        key = (*base, str(method))
        if key in indexed:
            raise AuditInputError(f"duplicate paired endpoint: {key}")
        indexed[key] = row
        base_keys.add(base)

    operator_differences: list[float] = []
    response_differences: list[float] = []
    for base in sorted(base_keys):
        candidate = indexed.get((*base, candidate_method))
        comparator = indexed.get((*base, comparator_method))
        if candidate is None or comparator is None:
            raise AuditInputError(f"missing paired method for endpoint: {base}")
        candidate_status[str(candidate.get("status"))] += 1
        comparator_status[str(comparator.get("status"))] += 1
        if (
            candidate.get("status") != STATUS_AVAILABLE
            or comparator.get("status") != STATUS_AVAILABLE
        ):
            continue
        if not _is_finite_number(candidate.get("operator_mse")) or not _is_finite_number(
            comparator.get("operator_mse")
        ):
            continue
        if not _is_finite_number(candidate.get("response_mse")) or not _is_finite_number(
            comparator.get("response_mse")
        ):
            continue
        operator_differences.append(
            float(candidate["operator_mse"]) - float(comparator["operator_mse"])
        )
        response_differences.append(
            float(candidate["response_mse"]) - float(comparator["response_mse"])
        )
    return {
        "declared_count": len(base_keys),
        "common_completion_count": len(response_differences),
        "candidate_status_counts": _counter_to_status_counts(candidate_status),
        "comparator_status_counts": _counter_to_status_counts(comparator_status),
        "operator_mse_differences": tuple(operator_differences),
        "response_mse_differences": tuple(response_differences),
    }


def _failure_records(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        _record_identity(row)
        for row in rows
        if row.get("status") != STATUS_AVAILABLE
    ]


def _binding_check(name: str, status: str, details: str) -> dict[str, str]:
    return {"name": name, "status": status, "details": details}


def _find_key(value: Any, wanted: set[str]) -> bool:
    if isinstance(value, Mapping):
        if any(key in value for key in wanted):
            return True
        return any(_find_key(child, wanted) for child in value.values())
    if isinstance(value, list):
        return any(_find_key(child, wanted) for child in value)
    return False


def _parse_paired_key(key: str) -> tuple[str, int, str, int, str, str] | None:
    parts = key.split("|")
    if len(parts) != 5 or not parts[3].startswith("H"):
        return None
    methods = parts[4].split("_vs_")
    if len(methods) != 2:
        return None
    try:
        return (parts[0], int(parts[1]), parts[2], int(parts[3][1:]), methods[0], methods[1])
    except ValueError:
        return None


def _parse_interval_key(key: str) -> tuple[str, int, str] | None:
    parts = key.split("|")
    if len(parts) != 3:
        return None
    try:
        return (parts[0], int(parts[1]), parts[2])
    except ValueError:
        return None


def _key_hash(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _input_paths_manifest(paths: InputPaths) -> dict[str, Any]:
    path_values = {
        "results": paths.results,
        "manifest": paths.manifest,
        "authorization": paths.authorization,
        "register": paths.register,
        "candidate": paths.candidate,
        "comparator_registry": paths.comparator_registry,
        "failure_metric_schema": paths.failure_metric_schema,
        "plan": paths.plan,
        "e4_audit": paths.e4_audit,
        "execution_complete": paths.execution_complete,
        "terminal_inventory": paths.terminal_inventory,
        "workspace_authorization": paths.workspace_authorization,
    }
    entries: dict[str, Any] = {}
    for name, path in sorted(path_values.items()):
        if not path.exists():
            raise AuditInputError(f"missing input: {path}")
        resolved = path.resolve()
        entries[name] = {
            "path": str(resolved),
            "sha256": sha256_file(resolved),
        }
    return {
        "hash_algorithm": "sha256",
        "inputs": entries,
        "sha256_by_role": {
            name: entry["sha256"] for name, entry in entries.items()
        },
    }


def _load_and_bind_inputs(paths: InputPaths) -> dict[str, Any]:
    input_manifest = _input_paths_manifest(paths)
    authorization = _require_mapping(_load_json(paths.authorization), "authorization")
    register = _require_mapping(_load_json(paths.register), "author decision register")
    results = _require_mapping(_load_json(paths.results), "frozen results")
    manifest = _require_mapping(_load_json(paths.manifest), "execution manifest")
    candidate = _require_mapping(_load_json(paths.candidate), "candidate")
    execution_complete = _require_mapping(_load_json(paths.execution_complete), "execution completion marker")
    terminal_inventory = _require_mapping(_load_json(paths.terminal_inventory), "terminal inventory")
    workspace_authorization = _require_mapping(
        _load_json(paths.workspace_authorization), "workspace authorization"
    )
    registry = _require_mapping(
        _load_json(paths.comparator_registry), "comparator registry"
    )
    failure_schema = _require_mapping(
        _load_json(paths.failure_metric_schema), "failure metric schema"
    )
    v2_binding = validate_authorization_v2(
        authorization,
        register_path=paths.register,
        register=register,
        frozen_paths={
            "results": paths.results,
            "execution_manifest": paths.manifest,
            "execution_complete": paths.execution_complete,
            "terminal_inventory": paths.terminal_inventory,
            "candidate": paths.candidate,
            "workspace_authorization": paths.workspace_authorization,
        },
        frozen_values={
            "results": results,
            "execution_manifest": manifest,
            "execution_complete": execution_complete,
            "terminal_inventory": terminal_inventory,
            "candidate": candidate,
            "workspace_authorization": workspace_authorization,
        },
    )
    register_item = v2_binding["register_item"]
    hash_binding = {
        "register": {
            "expected_sha256": authorization["binding"]["decision_register_sha256"],
            "observed_sha256": v2_binding["decision_register_sha256"],
            "matches": True,
        },
        "results": {
            "expected_sha256": authorization["frozen_e4_r3_inputs"]["results_sha256"],
            "observed_sha256": v2_binding["frozen_input_sha256"]["results"],
            "matches": True,
        },
        "manifest": {
            "expected_sha256": authorization["frozen_e4_r3_inputs"]["execution_manifest_sha256"],
            "observed_sha256": v2_binding["frozen_input_sha256"]["execution_manifest"],
            "matches": True,
        },
        "execution_complete": {
            "expected_sha256": authorization["frozen_e4_r3_inputs"]["execution_complete_sha256"],
            "observed_sha256": v2_binding["frozen_input_sha256"]["execution_complete"],
            "matches": True,
        },
        "terminal_inventory": {
            "expected_sha256": authorization["frozen_e4_r3_inputs"]["terminal_inventory_sha256"],
            "observed_sha256": v2_binding["frozen_input_sha256"]["terminal_inventory"],
            "matches": True,
        },
        "candidate": {
            "expected_sha256": authorization["frozen_e4_r3_inputs"]["candidate_sha256"],
            "observed_sha256": v2_binding["frozen_input_sha256"]["candidate"],
            "matches": True,
        },
        "workspace_authorization": {
            "expected_sha256": v2_binding["workspace_authorization_sha256"],
            "observed_sha256": v2_binding["workspace_authorization_sha256"],
            "matches": True,
        },
    }

    return {
        "input_manifest": input_manifest,
        "hash_binding": hash_binding,
        "authorization": authorization,
        "register": register,
        "register_item": register_item,
        "results": results,
        "manifest": manifest,
        "candidate": candidate,
        "registry": registry,
        "failure_schema": failure_schema,
        "execution_complete": execution_complete,
        "terminal_inventory": terminal_inventory,
        "workspace_authorization": workspace_authorization,
        "v2_binding": v2_binding,
    }


def _method_cell_audit(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_count: int,
) -> dict[str, Any]:
    endpoint_keys = sorted(_endpoint_key(row) for row in rows)
    endpoint_counter = Counter(endpoint_keys)
    duplicate_count = sum(count - 1 for count in endpoint_counter.values() if count > 1)
    seed_counts = Counter(int(row["seed"]) for row in rows)
    target_times = sorted({int(row["target_time"]) for row in rows})
    return {
        "expected_records": expected_count,
        "observed_records": len(rows),
        "record_count_complete": len(rows) == expected_count,
        "duplicate_endpoint_records": duplicate_count,
        "endpoint_key_sha256": _key_hash(endpoint_keys),
        "endpoint_key_count": len(endpoint_keys),
        "seed_count": len(seed_counts),
        "seed_counts": {str(seed): seed_counts[seed] for seed in sorted(seed_counts)},
        "target_time_count": len(target_times),
        "target_times": target_times,
        "status_counts": _status_counts(rows),
        "failure_records": _failure_records(rows),
        "operator_distribution": _distribution(rows, "operator_mse"),
        "response_distribution": _distribution(rows, "response_mse"),
        "validation_loss_distribution": _distribution(rows, "validation_loss"),
        "selected_hyperparameters": {
            str(value): count
            for value, count in sorted(
                Counter(row.get("selected_hyperparameter") for row in rows).items(),
                key=lambda item: str(item[0]),
            )
        },
    }


def _status_inventory(
    recovery_records: Sequence[Mapping[str, Any]],
    interval_records: Sequence[Mapping[str, Any]],
    interval_summaries: Mapping[str, Any],
    paired_summaries: Mapping[str, Any],
) -> dict[str, Any]:
    recovery_statuses = _status_counts(recovery_records)
    interval_statuses = _status_counts(interval_records)
    paired_candidate = Counter[str]()
    paired_comparator = Counter[str]()
    bootstrap = Counter[str]()
    for value in paired_summaries.values():
        for status, count in (value.get("candidate_status_counts") or {}).items():
            paired_candidate[status] += int(count)
        for status, count in (value.get("comparator_status_counts") or {}).items():
            paired_comparator[status] += int(count)
    for value in interval_summaries.values():
        for status, count in (value.get("bootstrap_status_counts") or {}).items():
            bootstrap[status] += int(count)
    interval_bins_present = all(
        all(status in (value.get("status_counts") or {}) for status in STATUS_SCHEMA)
        for value in interval_summaries.values()
        if isinstance(value, Mapping)
    )
    paired_bins_present = all(
        all(
            status in (value.get("candidate_status_counts") or {})
            and status in (value.get("comparator_status_counts") or {})
            for status in STATUS_SCHEMA
        )
        for value in paired_summaries.values()
        if isinstance(value, Mapping)
    )
    return {
        "recovery_records": _counter_to_status_counts(Counter(recovery_statuses)),
        "paired_candidate_records": _counter_to_status_counts(paired_candidate),
        "paired_comparator_records": _counter_to_status_counts(paired_comparator),
        "interval_records": _counter_to_status_counts(Counter(interval_statuses)),
        "bootstrap_replicates": _counter_to_status_counts(bootstrap),
        "retained_failure_records": {
            status: recovery_statuses[status]
            for status in STATUS_SCHEMA
            if status != STATUS_AVAILABLE
        },
        "failure_bins_present_in_summaries": interval_bins_present and paired_bins_present,
    }


def _audit_intervals(
    interval_records: Sequence[Mapping[str, Any]],
    interval_summaries: Mapping[str, Any],
) -> dict[str, Any]:
    groups: defaultdict[tuple[str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in interval_records:
        groups[(str(row["family"]), int(row["n"]), str(row["query_class"]))].append(row)
    expected_cells = tuple(
        (family, n, query_class)
        for family in EXPECTED_FAMILIES
        for n in EXPECTED_SCALES
        for query_class in EXPECTED_QUERIES
    )
    cell_audits: list[dict[str, Any]] = []
    for cell in expected_cells:
        rows = sorted(groups.get(cell, []), key=lambda row: int(row["seed"]))
        statuses = _status_counts(rows)
        bootstrap_counts = {status: 0 for status in STATUS_SCHEMA}
        for row in rows:
            for status, count in (row.get("bootstrap_status_counts") or {}).items():
                if status in bootstrap_counts:
                    bootstrap_counts[status] += int(count)
        summary_key = "|".join((cell[0], str(cell[1]), cell[2]))
        summary = interval_summaries.get(summary_key)
        cell_audits.append(
            {
                "family": cell[0],
                "n": cell[1],
                "query_class": cell[2],
                "expected_panel_records": EXPECTED_PANELS_PER_CELL,
                "observed_panel_records": len(rows),
                "seed_count": len({int(row["seed"]) for row in rows}),
                "status_counts": statuses,
                "bootstrap_status_counts": bootstrap_counts,
                "failure_records": _failure_records(rows),
                "summary_present": isinstance(summary, Mapping),
                "summary": summary,
            }
        )
    actual_keys = set(groups)
    return {
        "expected_cells": len(expected_cells),
        "observed_cells": len(actual_keys),
        "unexpected_cells": [
            {"family": cell[0], "n": cell[1], "query_class": cell[2]}
            for cell in sorted(actual_keys - set(expected_cells))
        ],
        "cell_audits": cell_audits,
        "complete": (
            actual_keys == set(expected_cells)
            and all(
                audit["observed_panel_records"] == EXPECTED_PANELS_PER_CELL
                and audit["summary_present"]
                for audit in cell_audits
            )
        ),
    }


def _audit_pairs(
    recovery_records: Sequence[Mapping[str, Any]],
    paired_summaries: Mapping[str, Any],
    *,
    methods: Sequence[str],
) -> dict[str, Any]:
    candidate_method = "fixed_rank_basis"
    comparator_methods = [method for method in methods if method != candidate_method]
    groups: defaultdict[tuple[str, int, str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for row in recovery_records:
        groups[_cell_tuple(row)].append(row)

    pair_audits: list[dict[str, Any]] = []
    expected_pair_keys: set[str] = set()
    for cell in _expected_cells():
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
            expected_pair_keys.add(pair_key)
            frozen = paired_summaries.get(pair_key)
            reconstructed = reconstruct_paired_differences(
                cell_rows,
                candidate_method=candidate_method,
                comparator_method=comparator_method,
            )
            stored_operator = tuple((frozen or {}).get("operator_mse_differences") or ())
            stored_response = tuple((frozen or {}).get("response_mse_differences") or ())
            raw_match = isinstance(frozen, Mapping) and _sequence_matches(
                reconstructed["operator_mse_differences"], stored_operator
            ) and _sequence_matches(
                reconstructed["response_mse_differences"], stored_response
            )
            pair_audits.append(
                {
                    "pair_key": pair_key,
                    **_cell_label(cell),
                    "candidate_method": candidate_method,
                    "comparator_method": comparator_method,
                    "frozen_summary_present": isinstance(frozen, Mapping),
                    "frozen_declared_date_keys": (
                        frozen.get("declared_date_keys") if isinstance(frozen, Mapping) else None
                    ),
                    "frozen_common_completion_date_keys": (
                        frozen.get("common_completion_date_keys") if isinstance(frozen, Mapping) else None
                    ),
                    "reconstructed_declared_date_keys": reconstructed["declared_count"],
                    "reconstructed_common_completion_date_keys": reconstructed[
                        "common_completion_count"
                    ],
                    "frozen_status_counts_match": isinstance(frozen, Mapping)
                    and frozen.get("candidate_status_counts")
                    == reconstructed["candidate_status_counts"]
                    and frozen.get("comparator_status_counts")
                    == reconstructed["comparator_status_counts"],
                    "raw_paired_difference_arrays_match": raw_match,
                    "frozen_raw_difference_sha256": _key_hash(
                        {
                            "operator_mse_differences": list(stored_operator),
                            "response_mse_differences": list(stored_response),
                        }
                    ),
                    "reconstructed_raw_difference_sha256": _key_hash(
                        {
                            "operator_mse_differences": list(
                                reconstructed["operator_mse_differences"]
                            ),
                            "response_mse_differences": list(
                                reconstructed["response_mse_differences"]
                            ),
                        }
                    ),
                    "raw_paired_differences": {
                        "operator_mse": list(reconstructed["operator_mse_differences"]),
                        "response_mse": list(reconstructed["response_mse_differences"]),
                    },
                    "audit_status": (
                        STATUS_AVAILABLE
                        if raw_match
                        and isinstance(frozen, Mapping)
                        and frozen.get("declared_date_keys") == EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL
                        and frozen.get("common_completion_date_keys")
                        == EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL
                        else "PARTIAL"
                    ),
                }
            )
    actual_keys = set(paired_summaries)
    return {
        "expected_pair_cells": len(expected_pair_keys),
        "observed_pair_cells": len(actual_keys),
        "unexpected_pair_keys": sorted(actual_keys - expected_pair_keys),
        "missing_pair_keys": sorted(expected_pair_keys - actual_keys),
        "pair_audits": pair_audits,
        "complete": actual_keys == expected_pair_keys
        and all(audit["audit_status"] == STATUS_AVAILABLE for audit in pair_audits),
    }


def _audit_frozen_records(bound: Mapping[str, Any]) -> dict[str, Any]:
    results = bound["results"]
    candidate = bound["candidate"]
    registry = bound["registry"]
    failure_schema = bound["failure_schema"]
    result_payload = _require_mapping(results.get("results"), "frozen results.results")
    recovery_records = result_payload.get("recovery_records")
    interval_records = result_payload.get("interval_records")
    recovery_summary = result_payload.get("recovery_summary")
    paired_summaries = result_payload.get("paired_common_completion")
    interval_summaries = result_payload.get("interval_summary")
    if not isinstance(recovery_records, list):
        raise AuditInputError("results.recovery_records must be an array")
    if not isinstance(interval_records, list):
        raise AuditInputError("results.interval_records must be an array")
    if not isinstance(recovery_summary, Mapping):
        raise AuditInputError("results.recovery_summary must be an object")
    if not isinstance(paired_summaries, Mapping):
        raise AuditInputError("results.paired_common_completion must be an object")
    if not isinstance(interval_summaries, Mapping):
        raise AuditInputError("results.interval_summary must be an object")

    registry_content = _require_mapping(registry.get("content"), "comparator registry.content")
    registry_records = registry_content.get("records")
    if not isinstance(registry_records, list):
        raise AuditInputError("comparator registry records must be an array")
    methods = tuple(str(record["comparator_id"]) for record in registry_records)
    if len(set(methods)) != len(methods):
        raise AuditInputError("comparator registry contains duplicate method ids")
    actual_methods = tuple(sorted({str(row.get("method")) for row in recovery_records}))
    expected_methods = tuple(sorted(methods))
    method_cell_groups: defaultdict[tuple[str, int, str, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    cell_groups: defaultdict[tuple[str, int, str, int], list[Mapping[str, Any]]] = defaultdict(list)
    duplicate_keys = Counter[tuple[Any, ...]]()
    for row in recovery_records:
        if not isinstance(row, Mapping):
            raise AuditInputError("recovery record must be an object")
        cell = _cell_tuple(row)
        method = str(row["method"])
        method_cell_groups[(*cell, method)].append(row)
        cell_groups[cell].append(row)
        duplicate_keys[(*cell, method, int(row["seed"]), int(row["target_time"]))] += 1

    expected_method_cell_keys = _expected_method_cell_keys(methods)
    actual_method_cell_keys = set(method_cell_groups)
    method_cell_audits = []
    for key in sorted(expected_method_cell_keys):
        cell = key[:4]
        method = key[4]
        method_cell_audits.append(
            {
                **_cell_label(cell),
                "method": method,
                **_method_cell_audit(
                    method_cell_groups.get(key, []),
                    expected_count=EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL,
                ),
            }
        )

    endpoint_parity_audits = []
    for cell in _expected_cells():
        by_method = {
            method: sorted(
                _endpoint_key(row) for row in method_cell_groups.get((*cell, method), [])
            )
            for method in methods
        }
        endpoint_parity_audits.append(
            {
                **_cell_label(cell),
                "method_endpoint_key_sha256": {
                    method: _key_hash(keys) for method, keys in sorted(by_method.items())
                },
                "same_endpoint_set_across_methods": len({tuple(keys) for keys in by_method.values()}) == 1,
                "expected_endpoint_count": EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL,
                "endpoint_count_by_method": {
                    method: len(keys) for method, keys in sorted(by_method.items())
                },
            }
        )

    interval_audit = _audit_intervals(interval_records, interval_summaries)
    pair_audit = _audit_pairs(recovery_records, paired_summaries, methods=methods)
    status_inventory = _status_inventory(
        recovery_records, interval_records, interval_summaries, paired_summaries
    )

    status_fields_present = all(
        all(status in (value.get("status_counts") or {}) for status in STATUS_SCHEMA)
        for value in recovery_summary.values()
        if isinstance(value, Mapping)
    )
    failure_statuses = _require_mapping(failure_schema.get("content"), "failure_metric_schema.content").get("statuses")
    failure_statuses_present = isinstance(failure_statuses, Mapping) and all(
        status in failure_statuses for status in STATUS_SCHEMA
    )
    method_cells_complete = (
        actual_method_cell_keys == expected_method_cell_keys
        and len(recovery_records)
        == EXPECTED_RECOVERY_CELLS * len(methods) * EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL
        and all(
            audit["record_count_complete"]
            and audit["duplicate_endpoint_records"] == 0
            for audit in method_cell_audits
        )
    )
    endpoint_parity_complete = all(
        audit["same_endpoint_set_across_methods"]
        and all(
            count == EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL
            for count in audit["endpoint_count_by_method"].values()
        )
        for audit in endpoint_parity_audits
    )
    forbidden_derived_payloads = _find_key(
        result_payload,
        {
            "panel_log_error_ratio",
            "response_log_error_ratio",
            "operator_log_error_ratio",
            "log_error_ratio_ci",
            "response_log_error_ratio_ci",
            "operator_log_error_ratio_ci",
            "normal_approximation_ci",
            "bootstrap_ci",
        },
    )

    checks = [
        _binding_check(
            "comparator_registry_complete",
            "PASS" if actual_methods == expected_methods and len(methods) == 3 else "FAIL",
            f"registry methods={expected_methods}; recovery methods={actual_methods}",
        ),
        _binding_check(
            "same_endpoint_and_cell_coverage",
            "PASS" if method_cells_complete and endpoint_parity_complete else "FAIL",
            f"method_cell_complete={method_cells_complete}; endpoint_parity_complete={endpoint_parity_complete}",
        ),
        _binding_check(
            "seed_and_replication_coverage",
            "PASS"
            if all(
                audit["seed_count"] == EXPECTED_PANELS_PER_CELL
                and audit["target_time_count"] == EXPECTED_DATES_PER_PANEL
                for audit in method_cell_audits
            )
            else "FAIL",
            f"expected seeds={len(EXPECTED_SEEDS)}; target dates={len(EXPECTED_TARGET_TIMES)}",
        ),
        _binding_check(
            "failure_status_retention",
            "PASS" if status_fields_present and failure_statuses_present else "FAIL",
            "all declared status bins are retained in the frozen summaries and failure schema",
        ),
        _binding_check(
            "raw_paired_difference_reconstruction",
            "PASS" if pair_audit["complete"] else "FAIL",
            f"paired cells={pair_audit['observed_pair_cells']}; all stored arrays independently matched={pair_audit['complete']}",
        ),
        _binding_check(
            "m2_raw_payload_boundary",
            "PASS" if not forbidden_derived_payloads else "FAIL",
            "artifact builder is restricted to raw comparator, paired-difference, and status inventory fields",
        ),
    ]

    coverage = {
        "recovery_records": len(recovery_records),
        "expected_recovery_records": EXPECTED_RECOVERY_CELLS * len(methods) * EXPECTED_PANELS_PER_CELL * EXPECTED_DATES_PER_PANEL,
        "recovery_summary_cells": len(recovery_summary),
        "expected_recovery_summary_cells": EXPECTED_RECOVERY_CELLS * len(methods),
        "paired_cells": len(paired_summaries),
        "expected_paired_cells": EXPECTED_RECOVERY_CELLS * (len(methods) - 1),
        "interval_records": len(interval_records),
        "expected_interval_records": len(EXPECTED_FAMILIES) * len(EXPECTED_SCALES) * len(EXPECTED_QUERIES) * EXPECTED_PANELS_PER_CELL,
        "interval_cells": interval_audit["observed_cells"],
        "expected_interval_cells": interval_audit["expected_cells"],
        "methods": list(methods),
        "families": list(EXPECTED_FAMILIES),
        "scales": list(EXPECTED_SCALES),
        "queries": list(EXPECTED_QUERIES),
        "horizons": list(EXPECTED_HORIZONS),
        "seeds": list(EXPECTED_SEEDS),
        "target_times": list(EXPECTED_TARGET_TIMES),
    }
    return {
        "coverage": coverage,
        "method_cell_audits": method_cell_audits,
        "endpoint_parity_audits": endpoint_parity_audits,
        "pair_audit": pair_audit,
        "interval_audit": interval_audit,
        "status_inventory": status_inventory,
        "checks": checks,
        "forbidden_derived_payloads_present": forbidden_derived_payloads,
        "actual_methods": list(actual_methods),
        "declared_methods": list(methods),
        "candidate_id_read_only": candidate.get("candidate_id"),
    }


def analyze_frozen_inputs(paths: InputPaths) -> dict[str, Any]:
    """Run the complete CAL-E01:75 audit without writing any output."""

    bound = _load_and_bind_inputs(paths)
    record_audit = _audit_frozen_records(bound)
    register_item = bound["register_item"]
    authorization = bound["authorization"]
    results = bound["results"]
    manifest = bound["manifest"]
    candidate = bound["candidate"]
    binding_checks = [
        _binding_check(
            "authorization_schema_v2",
            "PASS" if bound["v2_binding"]["schema_version"] == AUTHORIZATION_SCHEMA_VERSION else "FAIL",
            "authorization schema is directly bound to v2",
        ),
        _binding_check(
            "canonical_item_payload",
            "PASS" if bound["v2_binding"]["item_payload_sha256"] == authorization["binding"]["item_payloads"][V2_ITEM_BINDING["item_id"]] else "FAIL",
            "exact current register item payload is hash-bound",
        ),
        _binding_check(
            "e4_input_chain",
            "PASS" if bound["v2_binding"]["e4_chain"]["complete"] else "FAIL",
            "results, manifest, completion, inventory, candidate, and workspace authorization are chained",
        ),
        _binding_check(
            "register_hash",
            "PASS" if bound["hash_binding"]["register"]["matches"] else "BLOCKED",
            "expected={}; observed={}".format(
                bound["hash_binding"]["register"]["expected_sha256"],
                bound["hash_binding"]["register"]["observed_sha256"],
            ),
        ),
        _binding_check(
            "frozen_result_hash",
            "PASS",
            bound["input_manifest"]["sha256_by_role"]["results"],
        ),
        _binding_check(
            "frozen_manifest_hash",
            "PASS",
            bound["input_manifest"]["sha256_by_role"]["manifest"],
        ),
        _binding_check(
            "explicit_authorization",
            "PASS",
            f"{REGISTER_KEY} requested_action=NEW_ANALYSIS",
        ),
        _binding_check(
            "quarantine_and_promotion_boundary",
            "PASS"
            if results.get("status") == "COMPLETE_QUARANTINE_ONLY"
            and results.get("promotion") == "PROHIBITED_PENDING_DUPLICATE_AND_RESULT_TO_CLAIM_AUDIT"
            and manifest.get("promotion") == "PROHIBITED"
            else "FAIL",
            f"result_status={results.get('status')}; result_promotion={results.get('promotion')}; manifest_promotion={manifest.get('promotion')}",
        ),
        _binding_check(
            "excluded_routes",
            "PASS"
            if set(candidate.get("execution", {}).get("excluded_routes", []))
            >= {"RCEP", "NYC"}
            else "FAIL",
            str(candidate.get("execution", {}).get("excluded_routes")),
        ),
        _binding_check(
            "execution_manifest_terminal_status",
            "PASS"
            if manifest.get("status") == "COMPLETE_QUARANTINE_ONLY"
            else (
                "WARN"
                if bound["execution_complete"] is not None
                and bound["execution_complete"].get("status") == "COMPLETE_QUARANTINE_ONLY"
                else "FAIL"
            ),
            "manifest_status={}; completion_marker_status={}".format(
                manifest.get("status"),
                (bound["execution_complete"] or {}).get("status"),
            ),
        ),
    ]
    all_checks = binding_checks + record_audit["checks"]
    binding_statuses = {check["status"] for check in binding_checks}
    record_statuses = {check["status"] for check in record_audit["checks"]}
    verdict = "PASS"
    if "FAIL" in binding_statuses or "BLOCKED" in binding_statuses or "FAIL" in record_statuses:
        verdict = "BLOCKED"
    elif "BLOCKED" in record_statuses or "PARTIAL" in record_statuses:
        verdict = "PARTIAL"
    claim_activation = "BLOCKED"
    return {
        "analysis_version": ANALYSIS_VERSION,
        "artifact_type": "cal-e01-75-raw-read-only-audit",
        "register_key": REGISTER_KEY,
        "calibration_id": CALIBRATION_ID,
        "item_index": ITEM_INDEX,
        "input_manifest": bound["input_manifest"],
        "hash_binding": bound["hash_binding"],
        "v2_binding": bound["v2_binding"],
        "binding_checks": binding_checks,
        "record_audit": record_audit,
        "register_item": {
            "item_id": register_item.get("item_id"),
            "item_index": register_item.get("item_index"),
            "calibration_id": register_item.get("calibration_source", {}).get("calibration_id"),
            "action_class": register_item.get("action_class"),
            "calibration_requested_action": register_item.get("calibration_requested_action"),
            "priority": register_item.get("priority"),
            "stop_condition_zh": register_item.get("stop_condition_zh"),
            "minimum_action_zh": register_item.get("minimum_action_zh"),
            "target_manuscript_files": register_item.get("target_manuscript_files"),
        },
        "authorization_id": authorization.get("authorization_id"),
        "frozen_result_status": results.get("status"),
        "frozen_result_promotion": results.get("promotion"),
        "candidate_id_read_only": candidate.get("candidate_id"),
        "manifest_status": manifest.get("status"),
        "verdict": verdict,
        "claim_activation": claim_activation,
        "claim_ceiling": "simulation_only; frozen E4-r3 synthetic-only operating cells",
        "manuscript_modified": False,
        "author_decision_register_modified": False,
        "frozen_quarantine_modified": False,
        "rcep_or_nyc_used": False,
        "raw_metric_definition": {
            "comparator_ledger_fields": ["family", "n", "query_class", "horizon", "method", "seed", "target_time", "status", "operator_mse", "response_mse"],
            "paired_difference_fields": ["operator_mse", "response_mse"],
            "status_policy": "retain every declared status and non-finite inventory entry",
            "claim_policy": "descriptive_audit_only",
        },
        "derivation_authorized": False,
    }


def _write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True)
        handle.write("\n")


def _execution_context_from_e01_paths(paths: InputPaths) -> dict[str, Path]:
    root = Path(__file__).resolve().parents[2]
    return {
        "source_authorization_v2": paths.authorization,
        "m2a_repair_receipt": root / EXECUTION_M2A_RECEIPT_RELATIVE_PATH,
        "decision_register": paths.register,
        "e4_results": paths.results,
        "e4_execution_manifest": paths.manifest,
        "e4_execution_complete": paths.execution_complete,
        "e4_terminal_inventory": paths.terminal_inventory,
        "e4_candidate": paths.candidate,
        "workspace_authorization": paths.workspace_authorization,
    }


def _e01_output_target(analysis: Mapping[str, Any], output_parent: Path) -> Path:
    content_payload = {
        "analysis_version": ANALYSIS_VERSION,
        "register_key": REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "raw_scope": analysis["raw_metric_definition"],
    }
    content_address = _sha256_bytes(_canonical_json(content_payload).encode("utf-8"))
    return Path(output_parent).expanduser().resolve() / f"cal-e01-75-{content_address[:16]}"


def _write_raw_e01_artifacts(
    analysis: Mapping[str, Any],
    output_parent: Path,
    *,
    execution_authorization_path: Path | None,
    run_id: str,
    observed_paths: Mapping[str, Path],
) -> dict[str, Any]:
    content_payload = {
        "analysis_version": ANALYSIS_VERSION,
        "register_key": REGISTER_KEY,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "raw_scope": analysis["raw_metric_definition"],
    }
    content_address = _sha256_bytes(_canonical_json(content_payload).encode("utf-8"))
    output_dir = _e01_output_target(analysis, output_parent)
    validate_execution_authorization(
        execution_authorization_path,
        output_root=output_dir,
        run_id=run_id,
        observed_paths=observed_paths,
        artifact_prefix="cal-e01-75-",
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    record_audit = analysis["record_audit"]
    raw_pair_fields = {
        "pair_key",
        "family",
        "n",
        "query_class",
        "horizon",
        "candidate_method",
        "comparator_method",
        "frozen_summary_present",
        "frozen_declared_date_keys",
        "frozen_common_completion_date_keys",
        "reconstructed_declared_date_keys",
        "reconstructed_common_completion_date_keys",
        "frozen_status_counts_match",
        "raw_paired_difference_arrays_match",
        "frozen_raw_difference_sha256",
        "reconstructed_raw_difference_sha256",
        "raw_paired_differences",
        "audit_status",
    }
    pair_rows = [
        {key: value for key, value in pair.items() if key in raw_pair_fields}
        for pair in record_audit["pair_audit"]["pair_audits"]
    ]
    files: dict[str, Any] = {
        "input-manifest.json": {
            **analysis["input_manifest"],
            "authorization_schema_version": AUTHORIZATION_SCHEMA_VERSION,
            "v2_binding": analysis["v2_binding"] if "v2_binding" in analysis else None,
            "frozen_result_mutated": False,
        },
        "comparator-ledger.json": {
            "analysis_version": ANALYSIS_VERSION,
            "register_key": REGISTER_KEY,
            "declared_methods": record_audit["declared_methods"],
            "actual_methods": record_audit["actual_methods"],
            "method_cell_audits": record_audit["method_cell_audits"],
            "endpoint_parity_audits": record_audit["endpoint_parity_audits"],
            "interval_cell_audits": record_audit["interval_audit"]["cell_audits"],
        },
        "paired-differences.json": {
            "analysis_version": ANALYSIS_VERSION,
            "register_key": REGISTER_KEY,
            "pairs": pair_rows,
            "raw_difference_status": record_audit["pair_audit"]["complete"],
        },
        "status-inventory.json": {
            "analysis_version": ANALYSIS_VERSION,
            "register_key": REGISTER_KEY,
            "inventory": record_audit["status_inventory"],
            "failure_records": [
                audit["failure_records"]
                for audit in record_audit["method_cell_audits"]
                if audit["failure_records"]
            ],
            "nonfinite_policy": "retain and count; never impute",
        },
    }
    for filename, value in files.items():
        _write_json(output_dir / filename, value)
    output_hashes = {filename: sha256_file(output_dir / filename) for filename in sorted(files)}
    artifact_manifest = {
        "analysis_version": ANALYSIS_VERSION,
        "artifact_type": "cal-e01-75-raw-audit",
        "register_key": REGISTER_KEY,
        "content_address": content_address,
        "content_address_payload": content_payload,
        "input_sha256": analysis["input_manifest"]["sha256_by_role"],
        "output_sha256": output_hashes,
        "analysis_script_sha256": sha256_file(Path(__file__).resolve()),
        "verdict": analysis["verdict"],
        "claim_activation": "BLOCKED",
        "frozen_result_mutated": False,
        "author_decision_register_modified": False,
        "manuscript_modified": False,
        "quarantine_modified": False,
        "scientific_execution": "NOT_RUN",
    }
    _write_json(output_dir / "artifact-manifest.json", artifact_manifest)
    return {
        "output_dir": str(output_dir),
        "content_address": content_address,
        "output_sha256": output_hashes,
        "artifact_manifest": str(output_dir / "artifact-manifest.json"),
        "verdict": analysis["verdict"],
        "claim_activation": "BLOCKED",
        "coverage": record_audit["coverage"],
        "scientific_execution": "NOT_RUN",
    }


def write_analysis_artifacts(
    paths: InputPaths,
    *,
    output_parent: Path,
    artifact_mode: str = "raw",
    execution_authorization_path: Path | None = None,
    run_id: str = "primary",
    observed_paths: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Write a new content-addressed output root for this register key."""

    analysis = analyze_frozen_inputs(paths)
    if artifact_mode != "raw":
        raise ValueError("CAL-E01:75 M2 accepts only raw artifacts")
    return _write_raw_e01_artifacts(
        analysis,
        output_parent,
        execution_authorization_path=execution_authorization_path,
        run_id=run_id,
        observed_paths=observed_paths or _execution_context_from_e01_paths(paths),
    )

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
    parser.add_argument("--execution-authorization", type=Path, required=True)
    parser.add_argument("--run-id", choices=("primary", "duplicate"), required=True)
    parser.add_argument(
        "--artifact-mode",
        choices=("raw",),
        default="raw",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    paths = InputPaths(
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
        observed_paths = _execution_context_from_e01_paths(paths)
        analysis = analyze_frozen_inputs(paths)
        validate_execution_authorization(
            args.execution_authorization,
            output_root=_e01_output_target(analysis, args.output_parent),
            run_id=args.run_id,
            observed_paths=observed_paths,
            artifact_prefix="cal-e01-75-",
        )
        summary = write_analysis_artifacts(
            paths,
            output_parent=args.output_parent,
            artifact_mode=args.artifact_mode,
            execution_authorization_path=args.execution_authorization,
            run_id=args.run_id,
            observed_paths=observed_paths,
        )
    except (AuditInputError, FileExistsError, OSError, ValueError) as error:
        print(f"CAL-E01:75 audit refused: {error}")
        return 2
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
