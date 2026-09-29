"""Versioned, semantic pre-outcome artifacts for the E3 Family-2 boundary.

The module creates only source-only protocol artifacts.  It contains no
topology generation, fitting, response evaluation, output writing, or outcome
metric calculation.  Candidate-ready artifacts can be validated, but are not
produced by the source-only builder and cannot execute science through this
module.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from scripts.experiments import e3_family2_gate_receipt as gate_receipt


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "refine-logs" / "NCS_E3_FAMILY2_CANDIDATE_CONTRACT.md"
PROOF_PACKET_PATH = ROOT / "refine-logs" / "NCS_E3_FAMILY2_FACTORIZATION_PROOF_PACKET.md"
PROOF_SKELETON_PATH = ROOT / "refine-logs" / "NCS_E3_FAMILY2_PROOF_SKELETON.md"
PROOF_REVIEW_RECEIPT_PATH = ROOT / "refine-logs" / "NCS_E3_FAMILY2_PROOF_BLIND_REVIEW_RECEIPT.json"
DOMAIN_STABILITY_PROOF_PATH = (
    ROOT / "refine-logs" / "NCS_E4_DOMAIN_STABILITY_PROOF_PACKET_20260731.md"
)
GATE_TEST_PATH = ROOT / "scripts" / "experiments" / "test_e3_family2_preoutcome.py"
DEFAULT_ARTIFACT_ROOT = ROOT / "refine-logs" / "e3_family2_artifacts"

SOURCE_ONLY = "SOURCE_ONLY"
CANDIDATE_READY = "CANDIDATE_READY"
NOT_AUTHORIZED = "NOT_AUTHORIZED"
PROOF_REVIEWER_MODEL = "gpt-5.6-terra"
PROOF_REVIEWER_REASONING = "xhigh"

STATUS_SCHEMA = (
    "AVAILABLE",
    "OUTSIDE_TARGET",
    "NONCONVERGED",
    "NONFINITE",
    "UNSTABLE",
)
REQUIRED_PREOUTCOME_ARTIFACT_IDS = (
    "family2_query_contract",
    "family2_factorization_proof_packet",
    "exact_fixture_manifest",
    "comparator_registry",
    "tuning_split_manifest",
    "failure_metric_schema",
    "authorization_gate_tests",
    "duplicate_and_claim_audit_design",
)
SCHEMA_VERSIONS = {
    "family2_query_contract": "e3-family2-query-contract-v2",
    "family2_factorization_proof_packet": "e3-family2-factorization-proof-v1",
    "exact_fixture_manifest": "e3-family2-exact-fixtures-v2",
    "comparator_registry": "e3-family2-comparator-registry-v1",
    "tuning_split_manifest": "e3-family2-tuning-split-v4",
    "failure_metric_schema": "e3-family2-failure-metric-v2",
    "authorization_gate_tests": "e3-family2-authorization-gates-v2",
    "duplicate_and_claim_audit_design": "e3-family2-duplicate-claim-audit-v1",
}
ARTIFACT_FILENAMES = {
    artifact_id: f"{artifact_id}.json" for artifact_id in REQUIRED_PREOUTCOME_ARTIFACT_IDS
}

_BASE_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_id",
        "lifecycle",
        "scientific_execution",
        "content",
        "provenance",
        "artifact_sha256",
    }
)
_REFERENCE_FIELDS = frozenset({"path", "sha256"})
_BOOTSTRAP_REFIT_HISTORY_FIELDS = frozenset(
    {
        "method",
        "local_window",
        "minimum_local_estimates",
        "allowed_ranks",
        "minimum_valid_refit_opportunities_per_allowed_rank",
        "evaluation_target_times",
        "rank_aware_start_times",
    }
)
_BOOTSTRAP_PROCEDURE_FIELDS = frozenset(
    {
        "method",
        "initial_history",
        "lag_feature_source",
        "parameter_selection",
        "retune_inside_bootstrap",
        "retune_candidate_list",
        "failure_retention",
    }
)
_DOMAIN_STABILITY_CONTRACT = {
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
}
_CROSS_GENERATOR_INSTABILITY_POLICY = (
    "retain_as_scientific_failure_boundary_without_threshold_relaxation_or_stable_cell_selection"
)
_PROOF_REVIEW_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "audit_skill",
        "verdict",
        "proof_packet_sha256",
        "reviewer_model",
        "reviewer_reasoning",
        "review_mode",
        "scientific_execution",
        "open_findings",
        "generated_at",
    }
)
_PROVENANCE_FIELDS = frozenset(
    {
        "family2_contract",
        "family2_contract_sha256",
        "artifact_schema_module",
        "artifact_schema_module_sha256",
    }
)
_EXCLUDED_ROUTES = frozenset({"RCEP", "NYC", "R006e", "R006f"})
_REQUIRED_PROOF_PACKET_ANCHORS = (
    "## 1. Scope, domains and notation",
    "## 2. Full endpoint as a deterministic composition",
    "## 3. Linear factorization lemma",
    "**Theorem 1 (rowwise exact query factorization).**",
    "## 5. Full-rank structured-positive corollary",
    "### F1 structural negative",
    "### F2 unrestricted structural negative",
    "### F2 diagonal structural negative",
    "### F2 diagonal structured positive",
    "### Non-equivalence with a fixed one-hop family",
)
_REQUIRED_DOMAIN_STABILITY_PROOF_ANCHORS = (
    "## 1. Declared topology domain",
    "## 2. Query-independent coefficient projection",
    "## 3. Operator bound",
    "## 4. Exact fixture derivation",
    "## 5. Scope boundary",
)
_REQUIRED_GATE_TEST_ANCHORS = (
    "test_missing_authorization_refuses_before_science_or_quarantine_root",
    "test_fixture_trust_verifier_is_rejected_by_production_before_science",
    "test_candidate_sha_mismatch_refuses_before_science_or_quarantine_root",
    "test_each_semantically_empty_artifact_with_matching_hash_is_refused_before_science",
    "test_excluded_route_in_a_candidate_binding_refuses_before_science",
    "test_existing_quarantine_root_refuses_before_science",
    "test_cli_exposes_static_construction_and_verification_without_scientific_run",
    "test_bootstrap_history_gate_refuses_legacy_start_and_insufficient_rank_opportunities",
)


class ArtifactValidationError(RuntimeError):
    """Raised when a required static artifact is malformed or incomplete."""


def canonical_json_bytes(value: Any) -> bytes:
    """Encode a finite JSON value in the canonical form used by all artifacts."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_utc_iso8601(value: Any) -> bool:
    """Accept only a timezone-explicit UTC ISO-8601 timestamp."""

    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


def _require_exact_fields(value: Any, fields: frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ArtifactValidationError(f"{label} has an invalid field set")
    return value


def _forbid_excluded_route(value: str, label: str) -> None:
    folded = value.casefold()
    if any(route.casefold() in folded for route in _EXCLUDED_ROUTES):
        raise ArtifactValidationError(f"{label} references an excluded route")


def _resolve_existing_file(value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ArtifactValidationError(f"{label} must be a non-empty path")
    _forbid_excluded_route(value, label)
    raw_path = Path(value).expanduser()
    path = (ROOT / raw_path).resolve(strict=False) if not raw_path.is_absolute() else raw_path.resolve(strict=False)
    if not path.is_file():
        raise ArtifactValidationError(f"{label} must identify an existing regular file")
    return path


def _relative_path(path: Path) -> str:
    return str(Path(path).resolve().relative_to(ROOT))


def _reference(path: Path) -> dict[str, str]:
    return {"path": _relative_path(path), "sha256": sha256_file(path)}


def _validate_reference(value: Any, label: str) -> Path:
    reference = _require_exact_fields(value, _REFERENCE_FIELDS, label)
    if not _is_sha256(reference["sha256"]):
        raise ArtifactValidationError(f"{label} has an invalid SHA-256")
    path = _resolve_existing_file(reference["path"], label)
    if not hmac.compare_digest(sha256_file(path), reference["sha256"]):
        raise ArtifactValidationError(f"{label} hash does not match disk")
    return path


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


def _base_provenance() -> dict[str, str]:
    if not CONTRACT_PATH.is_file():
        raise ArtifactValidationError(f"missing Family-2 contract: {CONTRACT_PATH}")
    schema_path = Path(__file__).resolve()
    return {
        "family2_contract": _relative_path(CONTRACT_PATH),
        "family2_contract_sha256": sha256_file(CONTRACT_PATH),
        "artifact_schema_module": _relative_path(schema_path),
        "artifact_schema_module_sha256": sha256_file(schema_path),
    }


def _validate_provenance(value: Any) -> None:
    provenance = _require_exact_fields(value, _PROVENANCE_FIELDS, "artifact provenance")
    contract = _resolve_existing_file(provenance["family2_contract"], "Family-2 contract")
    schema_module = _resolve_existing_file(
        provenance["artifact_schema_module"], "artifact schema module"
    )
    if contract != CONTRACT_PATH.resolve() or schema_module != Path(__file__).resolve():
        raise ArtifactValidationError("artifact provenance does not bind the current Family-2 sources")
    if not _is_sha256(provenance["family2_contract_sha256"]) or not hmac.compare_digest(
        sha256_file(contract), provenance["family2_contract_sha256"]
    ):
        raise ArtifactValidationError("Family-2 contract provenance hash does not match disk")
    if not _is_sha256(provenance["artifact_schema_module_sha256"]) or not hmac.compare_digest(
        sha256_file(schema_module), provenance["artifact_schema_module_sha256"]
    ):
        raise ArtifactValidationError("artifact schema module provenance hash does not match disk")


def _candidate_bound(label: str, minimum: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"state": "CANDIDATE_BOUND", "label": label}
    if minimum is not None:
        value["minimum"] = minimum
    return value


def _fixture_specifications() -> list[dict[str, Any]]:
    permutation = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]
    return [
        {
            "fixture_id": "f1_negative",
            "matrices": {"P": permutation, "W0": permutation, "Wq": [[0, 0, 1], [1, 0, 0], [0, 1, 0]]},
            "expected_status": "OUTSIDE_TARGET",
            "hard_rejection": "collapsed_one_hop_query_scoring",
        },
        {
            "fixture_id": "f2_unrestricted_negative",
            "matrices": {"P": permutation, "W0": permutation, "Wq": [[0, 0, 1], [1, 0, 0], [0, 1, 0]]},
            "expected_status": "OUTSIDE_TARGET",
            "hard_rejection": "universal_collapsed_three_block_claim",
        },
        {
            "fixture_id": "f2_diagonal_negative",
            "matrices": {
                "W0": [[0, 1, 0], [0, 0, 0], [0, 0, 0]],
                "Wq": [[0, 1, 0], [0, 0, 1], [0, 0, 0]],
                "C2_witness": [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            },
            "expected_status": "OUTSIDE_TARGET",
            "hard_rejection": "rank_deficient_diagonal_inverse_claim",
        },
        {
            "fixture_id": "f2_diagonal_positive",
            "matrices": {"P": permutation, "W0": permutation, "Wq": [[0, 0, 1], [1, 0, 0], [0, 1, 0]]},
            "expected_status": "AVAILABLE",
            "hard_rejection": "unrestricted_negative_overgeneralization",
        },
        {
            "fixture_id": "non_equivalence",
            "matrices": {"V": [[0, 1], [1, 0]], "topology_set": [[[0, 0], [0, 0]], [[0, 1], [1, 0]], [[0, 2], [2, 0]]]},
            "expected_status": "DISTINCT_FAMILY",
            "hard_rejection": "two_hop_input_relabelling_or_fixed_one_hop_surrogate",
        },
    ]


def source_only_content(artifact_id: str) -> dict[str, Any]:
    """Return the complete source-only template for one required artifact."""

    if artifact_id not in REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        raise ArtifactValidationError(f"unknown pre-outcome artifact id: {artifact_id}")
    content_by_id: dict[str, dict[str, Any]] = {
        "family2_query_contract": {
            "operator_family": "C0_plus_C1W_plus_C2W2_with_diagonal_blocks",
            "coefficient_blocks": ["C0", "C1", "C2"],
            "node_order": _candidate_bound("node_order_sha256"),
            "topology_preprocessing": {
                "raw_zero_diagonal": True,
                "normalization": "CANDIDATE_BOUND",
                "normalization_stage": "once_before_fitting_and_evaluation",
                "square": "WW",
                "post_square_reprocessing": "PROHIBITED",
            },
            "lag_order": _candidate_bound("p", minimum=1),
            "maximum_horizon": _candidate_bound("H_max", minimum=1),
            "shock_map": "identity",
            "endpoint": "full_operator_and_finite_horizon_response",
            "status_schema": list(STATUS_SCHEMA),
            "domain_stability": json.loads(
                canonical_json_bytes(_DOMAIN_STABILITY_CONTRACT).decode("utf-8")
            ),
        },
        "family2_factorization_proof_packet": {
            "proof_packet": _reference(PROOF_PACKET_PATH),
            "proof_skeleton": _reference(PROOF_SKELETON_PATH),
            "theorem_id": "T1_rowwise_exact_query_factorization",
            "fixture_derivations": [
                "f1_negative",
                "f2_unrestricted_negative",
                "f2_diagonal_negative",
                "f2_diagonal_positive",
                "non_equivalence",
            ],
            "independent_blind_review": _source_only_proof_review(),
        },
        "exact_fixture_manifest": {
            "verification_domain": "exact_integer_or_rational_algebra",
            "float64_max_abs_error": 1e-12,
            "fixtures": _fixture_specifications(),
            "domain_stability_proof": _reference(DOMAIN_STABILITY_PROOF_PATH),
            "domain_stability_exact_summary": {
                "status": "AVAILABLE",
                "arithmetic": "fractions.Fraction",
                "envelope": "9/10",
                "checked_operators": 18,
                "max_projected_block_norm": "9/10",
                "max_operator_infinity_norm": "9/10",
                "spectral_radius_bound_follows_from_induced_norm": True,
            },
            "hard_rejections": [
                "floating_point_rank_as_proof",
                "collapsed_only_query_scoring",
                "topology_square_reprocessing",
            ],
        },
        "comparator_registry": {
            "registry_state": "CANDIDATE_BOUND",
            "required_interface": {
                "fit": "fit(training_histories, observed_training_topologies, frozen_hyperparameters)",
                "evaluate": "evaluate(fitted_state, W_q, H_max)->{G_1:p,R_1:H_max,status}",
            },
            "minimum_roles": ["native_local_structured", "fixed_low_rank_or_basis"],
            "records": [],
            "ineligible_forms": ["collapsed_only", "projected_output", "posthoc_mapping", "refit_at_query"],
        },
        "tuning_split_manifest": {
            "manifest_state": "CANDIDATE_BOUND",
            "selection_loss": "observed_topology_one_step_prediction",
            "truth_access": "PROHIBITED",
            "required_fields": [
                "chronological_partitions",
                "candidate_lists",
                "maximum_budget",
                "tie_break",
                "random_streams",
                "bootstrap_refit_history",
                "bootstrap_procedure",
                "domain_stability",
            ],
        },
        "failure_metric_schema": {
            "statuses": {
                "AVAILABLE": {"numerical_metrics": ["L_G", "L_R"]},
                "OUTSIDE_TARGET": {"numerical_metrics": []},
                "NONCONVERGED": {"numerical_metrics": []},
                "NONFINITE": {"numerical_metrics": []},
                "UNSTABLE": {"numerical_metrics": []},
            },
            "mutually_exclusive": True,
            "common_completion_rule": "pairwise_metrics_only_on_predeclared_common_completion_set",
            "failure_retention": "required",
            "cross_generator_instability_policy": _CROSS_GENERATOR_INSTABILITY_POLICY,
        },
        "authorization_gate_tests": {
            "test_suite": _reference(GATE_TEST_PATH),
            "required_refusals": [
                "missing_candidate_authorization",
                "missing_or_test_only_trust",
                "candidate_sha256_mismatch",
                "invalid_preoutcome_artifact",
                "excluded_route",
                "existing_quarantine_root",
                "outcome_writer_or_scientific_output_before_authorization",
                "bootstrap_history_gate",
            ],
            "science_entrypoints": [
                "topology_generator",
                "estimator",
                "response_evaluator",
                "outcome_writer",
                "scientific_output_directory",
            ],
            "verification_receipt": {"status": "PENDING"},
        },
        "duplicate_and_claim_audit_design": {
            "design_state": "CANDIDATE_BOUND",
            "same_manifest_binding": "REQUIRED",
            "isolated_duplicate": "new_isolated_output_root_required",
            "independent_result_to_claim_audit": "required_before_promotion",
            "promotion_prohibition": "outcomes_remain_quarantine_material_until_separate_authorization",
        },
    }
    return json.loads(canonical_json_bytes(content_by_id[artifact_id]).decode("utf-8"))


def _validate_proof_review_receipt(review: Any, proof_packet_sha256: str) -> None:
    review = _require_exact_fields(review, frozenset({"status", "receipt"}), "proof review")
    if review["status"] != "PASS":
        raise ArtifactValidationError("proof review receipt lacks PASS")
    receipt_path = _validate_reference(review["receipt"], "proof review receipt")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArtifactValidationError("proof review receipt is invalid JSON") from error
    receipt = _require_exact_fields(receipt, _PROOF_REVIEW_RECEIPT_FIELDS, "proof review receipt")
    if (
        receipt["schema_version"] != "e3-family2-proof-blind-review-v1"
        or receipt["audit_skill"] != "proof-checker"
        or receipt["verdict"] != "PASS"
        or receipt["proof_packet_sha256"] != proof_packet_sha256
        or receipt["reviewer_model"] != PROOF_REVIEWER_MODEL
        or receipt["reviewer_reasoning"] != PROOF_REVIEWER_REASONING
        or receipt["review_mode"] != "fresh_blind_read_only"
        or receipt["scientific_execution"] != NOT_AUTHORIZED
        or receipt["open_findings"] != []
        or not _is_utc_iso8601(receipt["generated_at"])
    ):
        raise ArtifactValidationError("proof review receipt does not meet the blind-review contract")


def _source_only_proof_review() -> dict[str, Any]:
    if not PROOF_REVIEW_RECEIPT_PATH.is_file():
        return {"status": "PENDING_BLIND_REVIEW"}
    review = {"status": "PASS", "receipt": _reference(PROOF_REVIEW_RECEIPT_PATH)}
    _validate_proof_review_receipt(review, sha256_file(PROOF_PACKET_PATH))
    return review


def validate_domain_stability_contract(contract: Any) -> Mapping[str, Any]:
    """Validate the query-independent E4 coefficient-envelope contract."""

    value = _require_exact_fields(
        contract,
        frozenset(_DOMAIN_STABILITY_CONTRACT),
        "domain-stability contract",
    )
    if value != _DOMAIN_STABILITY_CONTRACT:
        raise ArtifactValidationError(
            "domain stability must use the frozen query-independent L1 envelope"
        )
    return value


def _validate_query_contract(content: Any, lifecycle: str) -> None:
    fields = frozenset(
        {
            "operator_family",
            "coefficient_blocks",
            "node_order",
            "topology_preprocessing",
            "lag_order",
            "maximum_horizon",
            "shock_map",
            "endpoint",
            "status_schema",
            "domain_stability",
        }
    )
    contract = _require_exact_fields(content, fields, "Family-2 query contract")
    if contract["operator_family"] != "C0_plus_C1W_plus_C2W2_with_diagonal_blocks":
        raise ArtifactValidationError("Family-2 query contract changes the operator family")
    if contract["coefficient_blocks"] != ["C0", "C1", "C2"]:
        raise ArtifactValidationError("Family-2 query contract changes coefficient blocks")
    preprocessing = _require_exact_fields(
        contract["topology_preprocessing"],
        frozenset(
            {
                "raw_zero_diagonal",
                "normalization",
                "normalization_stage",
                "square",
                "post_square_reprocessing",
            }
        ),
        "topology preprocessing",
    )
    if (
        preprocessing["raw_zero_diagonal"] is not True
        or preprocessing["normalization_stage"] != "once_before_fitting_and_evaluation"
        or preprocessing["square"] != "WW"
        or preprocessing["post_square_reprocessing"] != "PROHIBITED"
    ):
        raise ArtifactValidationError("Family-2 topology semantics are invalid")
    if contract["shock_map"] != "identity" or contract["endpoint"] != "full_operator_and_finite_horizon_response":
        raise ArtifactValidationError("Family-2 endpoint semantics are invalid")
    if contract["status_schema"] != list(STATUS_SCHEMA):
        raise ArtifactValidationError("Family-2 status schema is invalid")
    validate_domain_stability_contract(contract["domain_stability"])
    if lifecycle == SOURCE_ONLY:
        if contract["node_order"] != _candidate_bound("node_order_sha256"):
            raise ArtifactValidationError("source-only query contract node-order marker is invalid")
        if contract["lag_order"] != _candidate_bound("p", minimum=1):
            raise ArtifactValidationError("source-only query contract lag-order marker is invalid")
        if contract["maximum_horizon"] != _candidate_bound("H_max", minimum=1):
            raise ArtifactValidationError("source-only query contract horizon marker is invalid")
        if preprocessing["normalization"] != "CANDIDATE_BOUND":
            raise ArtifactValidationError("source-only query contract normalization marker is invalid")
        return
    node_order = _require_exact_fields(
        contract["node_order"], frozenset({"hash_algorithm", "node_order_sha256"}), "node order"
    )
    if node_order["hash_algorithm"] != "sha256" or not _is_sha256(node_order["node_order_sha256"]):
        raise ArtifactValidationError("candidate-ready node order is invalid")
    for field in ("lag_order", "maximum_horizon"):
        if not isinstance(contract[field], int) or contract[field] < 1:
            raise ArtifactValidationError(f"candidate-ready {field} is invalid")
    if not isinstance(preprocessing["normalization"], str) or not preprocessing["normalization"]:
        raise ArtifactValidationError("candidate-ready normalization is invalid")
    if preprocessing["normalization"] == "CANDIDATE_BOUND":
        raise ArtifactValidationError("candidate-ready normalization remains unresolved")


def _validate_proof_packet(content: Any, lifecycle: str) -> None:
    fields = frozenset(
        {
            "proof_packet",
            "proof_skeleton",
            "theorem_id",
            "fixture_derivations",
            "independent_blind_review",
        }
    )
    packet = _require_exact_fields(content, fields, "Family-2 factorization proof packet")
    proof_path = _validate_reference(packet["proof_packet"], "factorization proof packet")
    _validate_reference(packet["proof_skeleton"], "factorization proof skeleton")
    if proof_path != PROOF_PACKET_PATH.resolve():
        raise ArtifactValidationError("factorization proof packet does not bind the declared packet")
    proof_text = proof_path.read_text(encoding="utf-8")
    if any(anchor not in proof_text for anchor in _REQUIRED_PROOF_PACKET_ANCHORS):
        raise ArtifactValidationError("factorization proof packet is missing a required derivation section")
    if packet["theorem_id"] != "T1_rowwise_exact_query_factorization":
        raise ArtifactValidationError("factorization proof theorem identity is invalid")
    if packet["fixture_derivations"] != [
        "f1_negative",
        "f2_unrestricted_negative",
        "f2_diagonal_negative",
        "f2_diagonal_positive",
        "non_equivalence",
    ]:
        raise ArtifactValidationError("factorization proof fixture inventory is invalid")
    review = packet["independent_blind_review"]
    if lifecycle == SOURCE_ONLY:
        if review == {"status": "PENDING_BLIND_REVIEW"}:
            return
        _validate_proof_review_receipt(review, packet["proof_packet"]["sha256"])
        return
    _validate_proof_review_receipt(review, packet["proof_packet"]["sha256"])


def _validate_fixture_manifest(content: Any, _lifecycle: str) -> None:
    manifest = _require_exact_fields(
        content,
        frozenset(
            {
                "verification_domain",
                "float64_max_abs_error",
                "fixtures",
                "domain_stability_proof",
                "domain_stability_exact_summary",
                "hard_rejections",
            }
        ),
        "exact fixture manifest",
    )
    if manifest["verification_domain"] != "exact_integer_or_rational_algebra":
        raise ArtifactValidationError("exact fixture verification domain is invalid")
    if manifest["float64_max_abs_error"] != 1e-12:
        raise ArtifactValidationError("exact fixture float64 tolerance is invalid")
    if manifest["fixtures"] != _fixture_specifications():
        raise ArtifactValidationError("exact fixture matrices or classifications changed")
    proof_path = _validate_reference(
        manifest["domain_stability_proof"], "domain-stability proof packet"
    )
    if proof_path != DOMAIN_STABILITY_PROOF_PATH.resolve():
        raise ArtifactValidationError("exact fixture manifest binds an unexpected stability proof")
    proof_text = proof_path.read_text(encoding="utf-8")
    if any(anchor not in proof_text for anchor in _REQUIRED_DOMAIN_STABILITY_PROOF_ANCHORS):
        raise ArtifactValidationError("domain-stability proof packet lacks a required section")
    expected_summary = {
        "status": "AVAILABLE",
        "arithmetic": "fractions.Fraction",
        "envelope": "9/10",
        "checked_operators": 18,
        "max_projected_block_norm": "9/10",
        "max_operator_infinity_norm": "9/10",
        "spectral_radius_bound_follows_from_induced_norm": True,
    }
    if manifest["domain_stability_exact_summary"] != expected_summary:
        raise ArtifactValidationError("domain-stability exact fixture summary is invalid")
    if manifest["hard_rejections"] != [
        "floating_point_rank_as_proof",
        "collapsed_only_query_scoring",
        "topology_square_reprocessing",
    ]:
        raise ArtifactValidationError("exact fixture hard-rejection rules are invalid")


def _validate_comparator_registry(content: Any, lifecycle: str) -> None:
    source_fields = frozenset(
        {
            "registry_state",
            "required_interface",
            "minimum_roles",
            "records",
            "ineligible_forms",
        }
    )
    registry = _require_exact_fields(content, source_fields, "comparator registry")
    interface = _require_exact_fields(
        registry["required_interface"], frozenset({"fit", "evaluate"}), "comparator interface"
    )
    if interface != source_only_content("comparator_registry")["required_interface"]:
        raise ArtifactValidationError("comparator interface is invalid")
    if registry["minimum_roles"] != ["native_local_structured", "fixed_low_rank_or_basis"]:
        raise ArtifactValidationError("comparator minimum roles are invalid")
    if registry["ineligible_forms"] != [
        "collapsed_only",
        "projected_output",
        "posthoc_mapping",
        "refit_at_query",
    ]:
        raise ArtifactValidationError("comparator ineligibility rules are invalid")
    if lifecycle == SOURCE_ONLY:
        if registry["registry_state"] != "CANDIDATE_BOUND" or registry["records"] != []:
            raise ArtifactValidationError("source-only comparator registry is invalid")
        return
    if registry["registry_state"] != "FROZEN" or not isinstance(registry["records"], list):
        raise ArtifactValidationError("candidate-ready comparator registry is invalid")
    roles: set[str] = set()
    record_fields = frozenset(
        {
            "comparator_id",
            "role",
            "source_identity",
            "parameterization",
            "fit_signature",
            "evaluate_signature",
            "endpoint_shape",
            "native_evaluator_proof",
        }
    )
    for record in registry["records"]:
        record = _require_exact_fields(record, record_fields, "comparator record")
        if not all(isinstance(record[field], str) and record[field] for field in ("comparator_id", "role", "source_identity")):
            raise ArtifactValidationError("comparator identity is incomplete")
        if not isinstance(record["parameterization"], Mapping) or not record["parameterization"]:
            raise ArtifactValidationError("comparator parameterization is incomplete")
        if record["fit_signature"] != interface["fit"] or record["evaluate_signature"] != interface["evaluate"]:
            raise ArtifactValidationError("comparator does not implement the common interface")
        if record["endpoint_shape"] != "full_operator_and_finite_horizon_response":
            raise ArtifactValidationError("comparator endpoint shape is invalid")
        _validate_reference(record["native_evaluator_proof"], "native evaluator proof")
        roles.add(record["role"])
    if not set(registry["minimum_roles"]).issubset(roles):
        raise ArtifactValidationError("candidate-ready comparator registry lacks required roles")


def _validate_tuning_split_manifest(content: Any, lifecycle: str) -> None:
    if lifecycle == SOURCE_ONLY:
        manifest = _require_exact_fields(
            content,
            frozenset({"manifest_state", "selection_loss", "truth_access", "required_fields"}),
            "source-only tuning manifest",
        )
        if (
            manifest["manifest_state"] != "CANDIDATE_BOUND"
            or manifest["selection_loss"] != "observed_topology_one_step_prediction"
            or manifest["truth_access"] != "PROHIBITED"
            or manifest["required_fields"]
            != [
                "chronological_partitions",
                "candidate_lists",
                "maximum_budget",
                "tie_break",
                "random_streams",
                "bootstrap_refit_history",
                "bootstrap_procedure",
                "domain_stability",
            ]
        ):
            raise ArtifactValidationError("source-only tuning manifest is invalid")
        return
    manifest = _require_exact_fields(
        content,
        frozenset(
            {
                "manifest_state",
                "selection_loss",
                "truth_access",
                "chronological_partitions",
                "candidate_lists",
                "maximum_budget",
                "tie_break",
                "random_streams",
                "bootstrap_refit_history",
                "bootstrap_procedure",
                "domain_stability",
            }
        ),
        "candidate-ready tuning manifest",
    )
    if (
        manifest["manifest_state"] != "FROZEN"
        or manifest["selection_loss"] != "observed_topology_one_step_prediction"
        or manifest["truth_access"] != "PROHIBITED"
    ):
        raise ArtifactValidationError("candidate-ready tuning policy is invalid")
    partitions = _require_exact_fields(
        manifest["chronological_partitions"], frozenset({"train", "validation", "evaluation"}), "chronological partitions"
    )
    if not all(isinstance(value, Mapping) and value for value in partitions.values()):
        raise ArtifactValidationError("candidate-ready chronological partitions are incomplete")
    if not isinstance(manifest["candidate_lists"], Mapping) or not manifest["candidate_lists"]:
        raise ArtifactValidationError("candidate-ready tuning candidate lists are incomplete")
    if not isinstance(manifest["maximum_budget"], int) or manifest["maximum_budget"] < 1:
        raise ArtifactValidationError("candidate-ready tuning budget is invalid")
    if not isinstance(manifest["tie_break"], str) or not manifest["tie_break"]:
        raise ArtifactValidationError("candidate-ready tuning tie-break is invalid")
    if not isinstance(manifest["random_streams"], Mapping) or not manifest["random_streams"]:
        raise ArtifactValidationError("candidate-ready random-stream binding is incomplete")
    validate_fixed_rank_bootstrap_history_gate(manifest["bootstrap_refit_history"])
    validate_recursive_bootstrap_procedure(manifest["bootstrap_procedure"])
    validate_domain_stability_contract(manifest["domain_stability"])


def validate_recursive_bootstrap_procedure(contract: Any) -> Mapping[str, Any]:
    """Validate recursive pseudo-history generation and per-replicate retuning."""

    procedure = _require_exact_fields(
        contract, _BOOTSTRAP_PROCEDURE_FIELDS, "recursive bootstrap procedure"
    )
    expected = {
        "method": "recursive_residual_circular_moving_block_bootstrap",
        "initial_history": "observed_prefix_before_rank_aware_start",
        "lag_feature_source": "pseudo_response_history",
        "parameter_selection": "validation_loss_on_each_pseudo_series",
        "retune_inside_bootstrap": True,
        "retune_candidate_list": [1, 2, 3],
        "failure_retention": "all_replicates",
    }
    if procedure != expected:
        raise ArtifactValidationError(
            "bootstrap procedure must rebuild pseudo lags, retune every replicate and retain failures"
        )
    return procedure


def validate_fixed_rank_bootstrap_history_gate(contract: Any) -> Mapping[str, Any]:
    """Validate the rank-aware E3-4 bootstrap history gate without running science."""

    gate = _require_exact_fields(
        contract, _BOOTSTRAP_REFIT_HISTORY_FIELDS, "fixed-rank bootstrap refit history"
    )
    if gate["method"] != "fixed_rank_basis":
        raise ArtifactValidationError("bootstrap history gate must bind the fixed-rank basis method")
    for field in ("local_window", "minimum_local_estimates"):
        if isinstance(gate[field], bool) or not isinstance(gate[field], int) or gate[field] < 1:
            raise ArtifactValidationError(f"bootstrap history {field} is invalid")
    local_window = int(gate["local_window"])
    minimum_local_estimates = int(gate["minimum_local_estimates"])
    if local_window != 12 or minimum_local_estimates != 2:
        raise ArtifactValidationError("bootstrap history gate drifted from the frozen local-history rule")
    ranks = gate["allowed_ranks"]
    if (
        not isinstance(ranks, list)
        or not ranks
        or any(isinstance(rank, bool) or not isinstance(rank, int) or rank < 1 for rank in ranks)
        or len(set(ranks)) != len(ranks)
    ):
        raise ArtifactValidationError("bootstrap history allowed ranks are invalid")
    required_opportunities = gate["minimum_valid_refit_opportunities_per_allowed_rank"]
    if (
        isinstance(required_opportunities, bool)
        or not isinstance(required_opportunities, int)
        or required_opportunities < 2
    ):
        raise ArtifactValidationError(
            "bootstrap history must require at least two valid bootstrap refit opportunities"
        )
    target_times = gate["evaluation_target_times"]
    if (
        not isinstance(target_times, list)
        or not target_times
        or any(
            isinstance(target_time, bool)
            or not isinstance(target_time, int)
            or target_time < 1
            for target_time in target_times
        )
        or len(set(target_times)) != len(target_times)
    ):
        raise ArtifactValidationError("bootstrap history evaluation target times are invalid")
    expected_starts = {
        str(rank): local_window + max(minimum_local_estimates, rank) for rank in ranks
    }
    if gate["rank_aware_start_times"] != expected_starts:
        raise ArtifactValidationError("bootstrap history rank-aware start times are invalid")
    for rank in ranks:
        start_time = expected_starts[str(rank)]
        for target_time in target_times:
            if target_time - start_time < required_opportunities:
                raise ArtifactValidationError(
                    f"rank {rank} does not have two valid bootstrap refit opportunities "
                    f"before target {target_time}"
                )
    return gate


def _validate_failure_metric_schema(content: Any, _lifecycle: str) -> None:
    schema = _require_exact_fields(
        content,
        frozenset(
            {
                "statuses",
                "mutually_exclusive",
                "common_completion_rule",
                "failure_retention",
                "cross_generator_instability_policy",
            }
        ),
        "failure metric schema",
    )
    if schema["mutually_exclusive"] is not True or schema["failure_retention"] != "required":
        raise ArtifactValidationError("failure metric status handling is invalid")
    if schema["common_completion_rule"] != "pairwise_metrics_only_on_predeclared_common_completion_set":
        raise ArtifactValidationError("failure metric completion rule is invalid")
    if schema["cross_generator_instability_policy"] != _CROSS_GENERATOR_INSTABILITY_POLICY:
        raise ArtifactValidationError("cross-generator instability policy is invalid")
    statuses = schema["statuses"]
    if not isinstance(statuses, Mapping) or set(statuses) != set(STATUS_SCHEMA):
        raise ArtifactValidationError("failure metric status inventory is invalid")
    for status in STATUS_SCHEMA:
        expected = ["L_G", "L_R"] if status == "AVAILABLE" else []
        if statuses[status] != {"numerical_metrics": expected}:
            raise ArtifactValidationError("failure metric numerical-score rule is invalid")


def _validate_authorization_gate_tests(content: Any, lifecycle: str) -> None:
    fields = frozenset(
        {"test_suite", "required_refusals", "science_entrypoints", "verification_receipt"}
    )
    gates = _require_exact_fields(content, fields, "authorization gate tests")
    suite_path = _validate_reference(gates["test_suite"], "authorization gate test suite")
    if suite_path != GATE_TEST_PATH.resolve():
        raise ArtifactValidationError("authorization gate tests bind an unexpected test suite")
    suite_text = suite_path.read_text(encoding="utf-8")
    if any(anchor not in suite_text for anchor in _REQUIRED_GATE_TEST_ANCHORS):
        raise ArtifactValidationError("authorization gate test suite lacks a required refusal test")
    expected_refusals = [
        "missing_candidate_authorization",
        "missing_or_test_only_trust",
        "candidate_sha256_mismatch",
        "invalid_preoutcome_artifact",
        "excluded_route",
        "existing_quarantine_root",
        "outcome_writer_or_scientific_output_before_authorization",
        "bootstrap_history_gate",
    ]
    if gates["required_refusals"] != expected_refusals:
        raise ArtifactValidationError("authorization gate refusal inventory is invalid")
    if gates["science_entrypoints"] != [
        "topology_generator",
        "estimator",
        "response_evaluator",
        "outcome_writer",
        "scientific_output_directory",
    ]:
        raise ArtifactValidationError("authorization gate entrypoint inventory is invalid")
    receipt = gates["verification_receipt"]
    if lifecycle == SOURCE_ONLY:
        if receipt != {"status": "PENDING"}:
            raise ArtifactValidationError("source-only gate-test receipt is invalid")
        return
    receipt = _require_exact_fields(receipt, frozenset({"status", "receipt"}), "gate-test receipt")
    if receipt["status"] != "PASS":
        raise ArtifactValidationError("candidate-ready gate-test receipt lacks PASS")
    receipt_path = _validate_reference(receipt["receipt"], "gate-test verification receipt")
    try:
        payload = gate_receipt.validate_gate_test_receipt(receipt_path)
    except gate_receipt.GateReceiptError as error:
        raise ArtifactValidationError(
            f"gate-test execution receipt refused: {error}"
        ) from error
    primary_module = "scripts.experiments.test_e3_family2_preoutcome"
    if payload["suite_sha256"].get(primary_module) != gates["test_suite"]["sha256"]:
        raise ArtifactValidationError("gate-test receipt binds a different test suite")


def _validate_duplicate_claim_audit_design(content: Any, lifecycle: str) -> None:
    design = _require_exact_fields(
        content,
        frozenset(
            {
                "design_state",
                "same_manifest_binding",
                "isolated_duplicate",
                "independent_result_to_claim_audit",
                "promotion_prohibition",
            }
        ),
        "duplicate and claim audit design",
    )
    if (
        design["same_manifest_binding"] != "REQUIRED"
        or design["isolated_duplicate"] != "new_isolated_output_root_required"
        or design["independent_result_to_claim_audit"] != "required_before_promotion"
        or design["promotion_prohibition"]
        != "outcomes_remain_quarantine_material_until_separate_authorization"
    ):
        raise ArtifactValidationError("duplicate and claim audit safeguards are invalid")
    expected_state = "CANDIDATE_BOUND" if lifecycle == SOURCE_ONLY else "FROZEN"
    if design["design_state"] != expected_state:
        raise ArtifactValidationError("duplicate and claim audit lifecycle is invalid")


_SEMANTIC_VALIDATORS = {
    "family2_query_contract": _validate_query_contract,
    "family2_factorization_proof_packet": _validate_proof_packet,
    "exact_fixture_manifest": _validate_fixture_manifest,
    "comparator_registry": _validate_comparator_registry,
    "tuning_split_manifest": _validate_tuning_split_manifest,
    "failure_metric_schema": _validate_failure_metric_schema,
    "authorization_gate_tests": _validate_authorization_gate_tests,
    "duplicate_and_claim_audit_design": _validate_duplicate_claim_audit_design,
}


def build_preoutcome_artifact(
    artifact_id: str,
    *,
    lifecycle: str,
    content: Mapping[str, Any],
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one static artifact after validating its artifact-specific schema."""

    if artifact_id not in REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        raise ArtifactValidationError(f"unknown pre-outcome artifact id: {artifact_id}")
    if lifecycle not in {SOURCE_ONLY, CANDIDATE_READY}:
        raise ArtifactValidationError("pre-outcome artifact lifecycle is invalid")
    body = {
        "schema_version": SCHEMA_VERSIONS[artifact_id],
        "artifact_id": artifact_id,
        "lifecycle": lifecycle,
        "scientific_execution": NOT_AUTHORIZED,
        "content": json.loads(canonical_json_bytes(content).decode("utf-8")),
        "provenance": dict(_base_provenance() if provenance is None else provenance),
    }
    artifact = {**body, "artifact_sha256": canonical_sha256(body)}
    validate_preoutcome_artifact_mapping(artifact, artifact_id=artifact_id)
    return artifact


def validate_preoutcome_artifact_mapping(
    artifact: Mapping[str, Any], *, artifact_id: str, require_candidate_ready: bool = False
) -> dict[str, Any]:
    """Validate one artifact's envelope, immutable digest, and semantic schema."""

    value = _require_exact_fields(artifact, _BASE_FIELDS, "pre-outcome artifact")
    if artifact_id not in REQUIRED_PREOUTCOME_ARTIFACT_IDS or value["artifact_id"] != artifact_id:
        raise ArtifactValidationError("pre-outcome artifact id is invalid")
    if value["schema_version"] != SCHEMA_VERSIONS[artifact_id]:
        raise ArtifactValidationError("pre-outcome artifact schema version is invalid")
    lifecycle = value["lifecycle"]
    if lifecycle not in {SOURCE_ONLY, CANDIDATE_READY}:
        raise ArtifactValidationError("pre-outcome artifact lifecycle is invalid")
    if require_candidate_ready and lifecycle != CANDIDATE_READY:
        raise ArtifactValidationError("pre-outcome artifact is not candidate-ready")
    if value["scientific_execution"] != NOT_AUTHORIZED:
        raise ArtifactValidationError("pre-outcome artifacts cannot authorize science")
    if not isinstance(value["content"], Mapping):
        raise ArtifactValidationError("pre-outcome artifact content must be an object")
    body = {name: value[name] for name in value if name != "artifact_sha256"}
    if not isinstance(value["artifact_sha256"], str) or not hmac.compare_digest(
        value["artifact_sha256"], canonical_sha256(body)
    ):
        raise ArtifactValidationError("pre-outcome artifact canonical digest mismatch")
    _validate_provenance(value["provenance"])
    _SEMANTIC_VALIDATORS[artifact_id](value["content"], lifecycle)
    return dict(value)


def verify_preoutcome_artifact(
    artifact_path: Path, *, artifact_id: str, require_candidate_ready: bool = False
) -> dict[str, Any]:
    """Read and semantically validate one versioned artifact from disk."""

    path = Path(artifact_path).expanduser().resolve(strict=False)
    if not path.is_file():
        raise ArtifactValidationError("pre-outcome artifact is missing")
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArtifactValidationError("pre-outcome artifact is invalid JSON") from error
    if not isinstance(artifact, Mapping):
        raise ArtifactValidationError("pre-outcome artifact must be an object")
    return validate_preoutcome_artifact_mapping(
        artifact, artifact_id=artifact_id, require_candidate_ready=require_candidate_ready
    )


def write_preoutcome_artifact(
    artifact_path: Path,
    *,
    artifact_id: str,
    lifecycle: str,
    content: Mapping[str, Any],
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Write one semantically validated static artifact with an atomic replace."""

    artifact = build_preoutcome_artifact(
        artifact_id, lifecycle=lifecycle, content=content, provenance=provenance
    )
    destination = Path(artifact_path).expanduser().resolve(strict=False)
    if destination.name != ARTIFACT_FILENAMES[artifact_id]:
        raise ArtifactValidationError("pre-outcome artifact filename does not match its artifact id")
    _atomic_write(destination, canonical_json_bytes(artifact) + b"\n")
    return artifact


def write_source_only_preoutcome_artifacts(artifact_root: Path) -> dict[str, Path]:
    """Write all eight source-only artifacts; no candidate-ready artifact is emitted."""

    root = Path(artifact_root).expanduser().resolve(strict=False)
    written: dict[str, Path] = {}
    for artifact_id in REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        destination = root / ARTIFACT_FILENAMES[artifact_id]
        write_preoutcome_artifact(
            destination,
            artifact_id=artifact_id,
            lifecycle=SOURCE_ONLY,
            content=source_only_content(artifact_id),
        )
        written[artifact_id] = destination
    return written


def source_only_artifact_inventory(artifact_root: Path = DEFAULT_ARTIFACT_ROOT) -> dict[str, dict[str, str]]:
    """Verify the repository's complete source-only package and return its hashes."""

    root = Path(artifact_root).expanduser().resolve(strict=False)
    inventory: dict[str, dict[str, str]] = {}
    for artifact_id in REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        path = root / ARTIFACT_FILENAMES[artifact_id]
        verified = verify_preoutcome_artifact(path, artifact_id=artifact_id)
        if verified["lifecycle"] != SOURCE_ONLY:
            raise ArtifactValidationError("source-only inventory contains a candidate-ready artifact")
        inventory[artifact_id] = {
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "sha256": sha256_file(path),
        }
    return inventory
