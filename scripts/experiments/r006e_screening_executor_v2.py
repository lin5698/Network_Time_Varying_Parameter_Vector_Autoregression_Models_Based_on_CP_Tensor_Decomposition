"""Governed single-cell execution boundary for R006e screening v2."""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import numpy as np

from scripts.experiments import r006c_endpoint_protocol as r006c
from scripts.experiments.r006e_dw_tucker import fit_dw_joint_tucker
from scripts.experiments.r006e_endpoint_support import construct_supported_endpoints
from scripts.experiments.r006e_native_estimators import fit_required_comparators
from scripts.experiments.r006e_native_experiment import SCREENING_STRING_FIELDS
from scripts.experiments.r006e_native_metrics import evaluate_method
from scripts.experiments.r006e_native_metrics import EVALUATOR_ROW_FIELDS
from scripts.experiments.r006e_native_protocol import (
    METHODS,
    R006EConfig,
    SCREENING_SEEDS,
    build_native_panel,
    keyed_seed,
    primary_cells,
)
from scripts.experiments.r006e_screening_schema_v2 import (
    DIAGNOSTIC_FIELDS,
    FORMAL_REPLICATION_FIELDS,
    FORMAL_REPLICATION_FLAG_FIELDS,
    FORMAL_REPLICATION_INTEGER_FIELDS,
    FORMAL_REPLICATION_NULLABLE_FIELDS,
    FORMAL_PEAK_MEMORY_SCOPE,
    RESOURCE_FIELDS,
    REPLICATION_IDENTITIES,
    ROW_JOURNAL_FIELDS,
    SchemaValidationError,
    SUMMARY_FIELDS,
    validate_diagnostic_record,
    validate_formal_replication_record,
    validate_resource_record,
    validate_row_journal_record,
)


PEAK_MEMORY_SCOPE = FORMAL_PEAK_MEMORY_SCOPE
CERTIFICATE_EVIDENCE_FIELDS = (
    "status",
    "failure_reasons",
    "design_inputs_sha256",
    "family_seed",
    "dgp_and_interp_streams",
    "interp_endpoint_sha256",
    "family_endpoint_sha256",
    "family_selected_index",
    "interp_calibration",
    "interp_prospective",
    "family_calibration",
    "family_prospective",
    "family_candidate_certificates",
)
CERTIFICATE_FIELDS = ("seed", "rho", "a3", "eta", *CERTIFICATE_EVIDENCE_FIELDS)


@dataclass(frozen=True)
class ScreeningCellTask:
    seed: int
    rho: float
    a3: float
    eta: float

    @property
    def identity(self) -> tuple[int, float, float, float]:
        return (self.seed, self.rho, self.a3, self.eta)

    @property
    def method_seed(self) -> int:
        return keyed_seed(self.seed, self.rho, self.a3, self.eta, "optimizer")

    @property
    def method_identities(
        self,
    ) -> tuple[tuple[int, float, float, float, str], ...]:
        return tuple((*self.identity, method) for method in METHODS)


@dataclass(frozen=True)
class ScientificPrimitives:
    build_native_panel: Callable[..., Any]
    construct_supported_endpoints: Callable[..., Any]
    fit_required_comparators: Callable[..., Any]
    fit_dw_joint_tucker: Callable[..., Any]
    evaluate_method: Callable[..., Mapping[str, object]]
    certificate_evidence: Callable[..., Mapping[str, object]]


@dataclass(frozen=True)
class CellExecution:
    replications: tuple[Mapping[str, object], ...]
    diagnostics: tuple[Mapping[str, object], ...]
    resources: tuple[Mapping[str, object], ...]
    row_journals: tuple[Mapping[str, object], ...]


class ConstructionCertificateError(RuntimeError):
    """Raised before fitting when runtime construction evidence drifts."""


class WorkerFailureError(RuntimeError):
    """Represents an unclean cell worker exit reported by its supervisor."""


def _array_digest(value: Any) -> str | None:
    if value is None:
        return None
    array = np.ascontiguousarray(np.asarray(value))
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(str(array.shape).encode("ascii"))
    digest.update(array.tobytes())
    return digest.hexdigest()


def _path_certificate(path: Any) -> dict[str, object] | None:
    if path is None:
        return None
    return {
        "dates": np.asarray(path.dates, dtype=int).tolist(),
        "chi": np.asarray(path.chi, dtype=float).tolist(),
        "maximum_chi": float(path.maximum_chi),
        "amplification": np.asarray(path.amplification, dtype=float).tolist(),
        "alpha": np.asarray(path.alpha, dtype=float).tolist(),
        "retained_rank": np.asarray(path.retained_rank, dtype=int).tolist(),
        "condition_number": np.asarray(
            path.condition_number, dtype=float
        ).tolist(),
        "singular_values": [
            np.asarray(values, dtype=float).tolist()
            for values in path.singular_values
        ],
    }


def _stream_certificate(seed: int) -> dict[str, object]:
    children = r006c.spawn_named_seed_sequences(seed)
    return {
        name: {
            "entropy": int(child.entropy),
            "spawn_key": [int(value) for value in child.spawn_key],
            "spawned": True,
            "used": name != "stress_topology",
        }
        for name, child in children.items()
    }


def _runtime_certificate_evidence(
    panel: Any,
    endpoints: Any,
    *,
    task: ScreeningCellTask,
    config: R006EConfig,
) -> dict[str, object]:
    del config
    design = hashlib.sha256()
    for value in (
        panel.fit.predictors,
        panel.fit.topology,
        panel.fit.w_ref,
        panel.fit.coefficient_dates,
    ):
        design.update(np.ascontiguousarray(value).tobytes())
    return {
        "status": endpoints.status,
        "failure_reasons": list(endpoints.failure_reasons),
        "design_inputs_sha256": design.hexdigest(),
        "family_seed": panel.endpoint_stream_seed,
        "dgp_and_interp_streams": _stream_certificate(task.seed),
        "interp_endpoint_sha256": _array_digest(endpoints.w_alt_interp),
        "family_endpoint_sha256": _array_digest(endpoints.w_alt_family),
        "family_selected_index": endpoints.family_selected_index,
        "interp_calibration": _path_certificate(endpoints.interp_calibration),
        "interp_prospective": _path_certificate(endpoints.interp_prospective),
        "family_calibration": _path_certificate(endpoints.family_calibration),
        "family_prospective": _path_certificate(endpoints.family_prospective),
        "family_candidate_certificates": [
            {
                "index": int(record.index),
                "endpoint_sha256": _array_digest(record.endpoint),
                "calibration_maximum_chi": float(record.path.maximum_chi),
            }
            for record in endpoints.family_candidates
        ],
    }


def production_scientific_primitives() -> ScientificPrimitives:
    """Return the frozen production scientific wiring without invoking it."""

    return ScientificPrimitives(
        build_native_panel=build_native_panel,
        construct_supported_endpoints=construct_supported_endpoints,
        fit_required_comparators=fit_required_comparators,
        fit_dw_joint_tucker=fit_dw_joint_tucker,
        evaluate_method=evaluate_method,
        certificate_evidence=_runtime_certificate_evidence,
    )


def _peak_rss_bytes() -> int:
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak * 1024 if sys.platform.startswith("linux") else peak


def screening_cell_tasks() -> tuple[ScreeningCellTask, ...]:
    """Return the exact frozen 80-cell screening order."""

    return tuple(
        ScreeningCellTask(seed=seed, rho=rho, a3=a3, eta=eta)
        for seed in SCREENING_SEEDS
        for rho, a3, eta in primary_cells()
    )


def _canonical_sha256(value: Mapping[str, object]) -> str:
    payload = json.dumps(
        dict(value),
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _failure_metadata(error: Exception) -> tuple[str, str]:
    if isinstance(error, ConstructionCertificateError):
        return "V2_CERTIFICATE_MISMATCH", "construction_certificate_mismatch"
    if isinstance(error, WorkerFailureError):
        return "V2_WORKER_FAILURE", "worker_failure"
    return "V2_CELL_EXECUTION_FAILURE", "cell_execution_failure"


def _is_finite_json(value: object, active: set[int] | None = None) -> bool:
    if value is None or type(value) in {str, bool, int}:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) not in {dict, list}:
        return False
    seen = set() if active is None else active
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    try:
        if type(value) is dict:
            return all(
                type(key) is str and _is_finite_json(item, seen)
                for key, item in value.items()
            )
        return all(_is_finite_json(item, seen) for item in value)
    finally:
        seen.remove(identity)


def _finite_json_equal(left: object, right: object) -> bool:
    if not _is_finite_json(left) or not _is_finite_json(right):
        return False
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if set(left) != set(right):
            return False
        return all(_finite_json_equal(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(
            _finite_json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    if type(left) is float:
        return json.dumps(left, allow_nan=False) == json.dumps(right, allow_nan=False)
    return left == right


def _certificate_provenance(
    construction_certificate: Mapping[str, object],
) -> dict[str, str]:
    if (
        type(construction_certificate) is dict
        and set(construction_certificate) == set(CERTIFICATE_FIELDS)
        and _is_finite_json(construction_certificate)
    ):
        return {"certificate_state": "schema_valid"}
    return {"certificate_state": "malformed"}


def _failure_replication_row(
    identity: tuple[int, float, float, float, str],
    *,
    failure_code: str,
    failure_reason: str,
    provenance_json: str,
    peak_memory_bytes: int,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for field in FORMAL_REPLICATION_FIELDS:
        if field in FORMAL_REPLICATION_NULLABLE_FIELDS:
            values[field] = None
        elif field in FORMAL_REPLICATION_FLAG_FIELDS:
            values[field] = 0
        elif field in FORMAL_REPLICATION_INTEGER_FIELDS:
            values[field] = 0
        elif field in SCREENING_STRING_FIELDS:
            values[field] = "runner_failure"
        else:
            values[field] = 0.0
    values.update(zip(("seed", "rho", "a3", "eta", "method"), identity))
    values.update(
        {
            "parameterization": "runner_failure",
            "fit_sha256": hashlib.sha256(
                provenance_json.encode("utf-8")
            ).hexdigest(),
            "fit_success": 0,
            "scorable": 0,
            "failure_code": failure_code,
            "failure_reason": failure_reason,
            "fit_diagnostics_json": provenance_json,
            "endpoint_construction_status": "RUNNER_FAILURE",
            "endpoint_failure_reasons_json": json.dumps(
                [failure_reason], separators=(",", ":")
            ),
            "peak_memory_bytes": peak_memory_bytes,
            "peak_memory_scope": PEAK_MEMORY_SCOPE,
        }
    )
    return {field: values[field] for field in FORMAL_REPLICATION_FIELDS}


def _validated_cell_execution(
    execution: CellExecution,
) -> CellExecution:
    specifications = (
        (execution.replications, validate_formal_replication_record),
        (execution.diagnostics, validate_diagnostic_record),
        (execution.resources, validate_resource_record),
        (execution.row_journals, validate_row_journal_record),
    )
    for records, validator in specifications:
        for record in records:
            validator(record)
    cardinality = len(execution.replications)
    if any(
        len(records) != cardinality
        for records in (
            execution.diagnostics,
            execution.resources,
            execution.row_journals,
        )
    ):
        raise SchemaValidationError("record-class cardinality mismatch")
    for index, journal in enumerate(execution.row_journals):
        expected = {
            "replication_sha256": _canonical_sha256(execution.replications[index]),
            "diagnostic_sha256": _canonical_sha256(execution.diagnostics[index]),
            "resource_sha256": _canonical_sha256(execution.resources[index]),
        }
        if any(journal[field] != digest for field, digest in expected.items()):
            raise SchemaValidationError(f"row_journal hash binding mismatch at {index}")
    return execution


def _retain_failed_cell(
    task: ScreeningCellTask,
    error: Exception,
    *,
    construction_certificate: Mapping[str, object],
    attempt_id: str,
    role: str,
    generated_at: str,
    worker_pid: int,
    peak_memory_bytes: int,
) -> CellExecution:
    failure_code, failure_reason = _failure_metadata(error)
    provenance_json = json.dumps(
        {
            "runner_failure_code": failure_code,
            "runner_failure_reason": failure_reason,
            "construction_support_provenance": _certificate_provenance(
                construction_certificate
            ),
        },
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    )
    replications: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    resources: list[dict[str, object]] = []
    journals: list[dict[str, object]] = []
    for identity in task.method_identities:
        replication = _failure_replication_row(
            identity,
            failure_code=failure_code,
            failure_reason=failure_reason,
            provenance_json=provenance_json,
            peak_memory_bytes=peak_memory_bytes,
        )
        diagnostic_values: dict[str, object] = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            "method": identity[4],
            "method_seed": task.method_seed,
            "fit_sha256": None,
            "fit_success": False,
            "scorable": False,
            "failure_code": failure_code,
            "failure_reason": failure_reason,
            "fit_diagnostics_json": provenance_json,
            "generated_at": generated_at,
        }
        diagnostic = {
            field: diagnostic_values[field] for field in DIAGNOSTIC_FIELDS
        }
        resource_values: dict[str, object] = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            "method": identity[4],
            "worker_pid": worker_pid,
            "peak_memory_bytes": peak_memory_bytes,
            "peak_memory_scope": PEAK_MEMORY_SCOPE,
            "attempt_id": attempt_id,
            "role": role,
        }
        resource_record = {
            field: resource_values[field] for field in RESOURCE_FIELDS
        }
        journal_values: dict[str, object] = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            "method": identity[4],
            "attempt_id": attempt_id,
            "role": role,
            "row_status": "RUNNER_FAILURE",
            "replication_sha256": _canonical_sha256(replication),
            "diagnostic_sha256": _canonical_sha256(diagnostic),
            "resource_sha256": _canonical_sha256(resource_record),
            "generated_at": generated_at,
        }
        journal = {field: journal_values[field] for field in ROW_JOURNAL_FIELDS}
        replications.append(replication)
        diagnostics.append(diagnostic)
        resources.append(resource_record)
        journals.append(journal)
    return _validated_cell_execution(
        CellExecution(
            replications=tuple(replications),
            diagnostics=tuple(diagnostics),
            resources=tuple(resources),
            row_journals=tuple(journals),
        )
    )


def _successful_execution(
    task: ScreeningCellTask,
    evaluated_rows: Mapping[str, Mapping[str, object]],
    *,
    attempt_id: str,
    role: str,
    generated_at: str,
    worker_pid: int,
    peak_memory_bytes: int,
) -> CellExecution:
    replications: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    resources: list[dict[str, object]] = []
    journals: list[dict[str, object]] = []
    for identity in task.method_identities:
        method = identity[-1]
        evaluated = evaluated_rows[method]
        if set(evaluated) != set(EVALUATOR_ROW_FIELDS):
            raise RuntimeError(f"evaluator schema mismatch for {method}")
        if evaluated["method"] != method:
            raise RuntimeError(f"evaluator method identity mismatch for {method}")
        replication_values = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            **dict(evaluated),
            "peak_memory_bytes": peak_memory_bytes,
            "peak_memory_scope": PEAK_MEMORY_SCOPE,
        }
        replication = {
            field: replication_values[field] for field in FORMAL_REPLICATION_FIELDS
        }
        diagnostic_values: dict[str, object] = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            "method": method,
            "method_seed": task.method_seed,
            "fit_sha256": evaluated["fit_sha256"],
            "fit_success": bool(evaluated["fit_success"]),
            "scorable": bool(evaluated["scorable"]),
            "failure_code": evaluated["failure_code"],
            "failure_reason": evaluated["failure_reason"],
            "fit_diagnostics_json": evaluated["fit_diagnostics_json"],
            "generated_at": generated_at,
        }
        diagnostic = {
            field: diagnostic_values[field] for field in DIAGNOSTIC_FIELDS
        }
        resource_values: dict[str, object] = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            "method": method,
            "worker_pid": worker_pid,
            "peak_memory_bytes": peak_memory_bytes,
            "peak_memory_scope": PEAK_MEMORY_SCOPE,
            "attempt_id": attempt_id,
            "role": role,
        }
        resource_record = {
            field: resource_values[field] for field in RESOURCE_FIELDS
        }
        journal_values: dict[str, object] = {
            "seed": identity[0],
            "rho": identity[1],
            "a3": identity[2],
            "eta": identity[3],
            "method": method,
            "attempt_id": attempt_id,
            "role": role,
            "row_status": "RECORDED",
            "replication_sha256": _canonical_sha256(replication),
            "diagnostic_sha256": _canonical_sha256(diagnostic),
            "resource_sha256": _canonical_sha256(resource_record),
            "generated_at": generated_at,
        }
        journal = {field: journal_values[field] for field in ROW_JOURNAL_FIELDS}
        replications.append(replication)
        diagnostics.append(diagnostic)
        resources.append(resource_record)
        journals.append(journal)
    return _validated_cell_execution(
        CellExecution(
            replications=tuple(replications),
            diagnostics=tuple(diagnostics),
            resources=tuple(resources),
            row_journals=tuple(journals),
        )
    )


def _verify_construction_certificate(
    task: ScreeningCellTask,
    certificate: Mapping[str, object],
    evidence: Mapping[str, object],
) -> None:
    if type(certificate) is not dict or set(certificate) != set(CERTIFICATE_FIELDS):
        raise ConstructionCertificateError("certificate schema mismatch")
    if type(evidence) is not dict or set(evidence) != set(CERTIFICATE_EVIDENCE_FIELDS):
        raise ConstructionCertificateError("runtime evidence schema mismatch")
    expected_identity = dict(zip(("seed", "rho", "a3", "eta"), task.identity))
    if any(
        not _finite_json_equal(certificate[key], value)
        for key, value in expected_identity.items()
    ):
        raise ConstructionCertificateError("certificate identity mismatch")
    for field in CERTIFICATE_EVIDENCE_FIELDS:
        if not _finite_json_equal(certificate[field], evidence[field]):
            raise ConstructionCertificateError(f"certificate {field} mismatch")


def retain_worker_failure(
    task: ScreeningCellTask,
    *,
    construction_certificate: Mapping[str, object],
    attempt_id: str,
    role: str,
    generated_at: str,
    worker_pid: int,
    peak_memory_bytes: int,
) -> CellExecution:
    """Retain all four identities after an unclean cell worker exit."""

    return _retain_failed_cell(
        task,
        WorkerFailureError("worker_failure"),
        construction_certificate=construction_certificate,
        attempt_id=attempt_id,
        role=role,
        generated_at=generated_at,
        worker_pid=worker_pid,
        peak_memory_bytes=peak_memory_bytes,
    )


def adapt_runner_failure_gates(
    replication_row: Mapping[str, object],
) -> dict[str, bool]:
    """Force all frozen gates false for a retained runner-failure row."""

    if replication_row.get("failure_code") not in {
        "V2_CERTIFICATE_MISMATCH",
        "V2_CELL_EXECUTION_FAILURE",
        "V2_WORKER_FAILURE",
    }:
        raise ValueError("row is not a retained v2 runner failure")
    return {field: False for field in SUMMARY_FIELDS}


def combine_cell_executions(
    executions: tuple[CellExecution, ...],
    *,
    governance_only: bool = False,
) -> CellExecution:
    """Combine exactly 80 fixture cells after strict schema/identity checks."""

    if not governance_only:
        raise RuntimeError("fixture aggregation requires governance_only=True")
    if len(executions) != 80:
        raise ValueError("exactly 80 cell executions are required")
    specifications = (
        ("replications", FORMAL_REPLICATION_FIELDS),
        ("diagnostics", DIAGNOSTIC_FIELDS),
        ("resources", RESOURCE_FIELDS),
        ("row_journals", ROW_JOURNAL_FIELDS),
    )
    combined: dict[str, tuple[Mapping[str, object], ...]] = {}
    identity_fields = ("seed", "rho", "a3", "eta", "method")
    for attribute, fields in specifications:
        records = tuple(
            record for execution in executions for record in getattr(execution, attribute)
        )
        if len(records) != 320:
            raise ValueError(f"{attribute} cardinality must equal 320")
        if any(tuple(record) != fields for record in records):
            raise ValueError(f"{attribute} schema mismatch")
        identities = tuple(
            tuple(record[field] for field in identity_fields) for record in records
        )
        if identities != REPLICATION_IDENTITIES:
            raise ValueError(f"{attribute} identities/order mismatch")
        validator = {
            "replications": validate_formal_replication_record,
            "diagnostics": validate_diagnostic_record,
            "resources": validate_resource_record,
            "row_journals": validate_row_journal_record,
        }[attribute]
        for record in records:
            validator(record)
        combined[attribute] = tuple(
            MappingProxyType(dict(record)) for record in records
        )
    return _validated_cell_execution(
        CellExecution(
            replications=combined["replications"],
            diagnostics=combined["diagnostics"],
            resources=combined["resources"],
            row_journals=combined["row_journals"],
        )
    )


def _run_screening_cell(
    task: ScreeningCellTask,
    *,
    construction_certificate: Mapping[str, object],
    config: R006EConfig,
    primitives: ScientificPrimitives | None = None,
    attempt_id: str,
    role: str,
    generated_at: str,
    worker_pid: int | None = None,
    peak_rss_reader: Callable[[], int] | None = None,
) -> CellExecution:
    """Return four records per class while retaining every cell failure."""

    active = production_scientific_primitives() if primitives is None else primitives
    read_peak = _peak_rss_bytes if peak_rss_reader is None else peak_rss_reader
    pid = os.getpid() if worker_pid is None else worker_pid
    try:
        panel = active.build_native_panel(
            config,
            rho=task.rho,
            a3=task.a3,
            eta=task.eta,
            seed=task.seed,
        )
        endpoints = active.construct_supported_endpoints(
            panel.fit,
            w_alt_interp=panel.w_alt_interp,
            family_seed=panel.endpoint_stream_seed,
            config=config,
        )
        evidence = active.certificate_evidence(
            panel,
            endpoints,
            task=task,
            config=config,
        )
        _verify_construction_certificate(task, construction_certificate, evidence)
        comparator_paths = active.fit_required_comparators(
            panel.fit,
            config=config,
            method_seed=task.method_seed,
        )
        if tuple(comparator_paths) != METHODS[:3]:
            raise RuntimeError("required comparator identity/order mismatch")
        candidate_path = active.fit_dw_joint_tucker(
            panel.fit,
            config=config,
            method_seed=task.method_seed,
        )
        fitted_paths = {**dict(comparator_paths), METHODS[3]: candidate_path}
        evaluated_rows = {
            method: active.evaluate_method(
                fitted_paths[method],
                fit=panel.fit,
                truth=panel.truth,
                endpoints=endpoints,
                config=config,
            )
            for method in METHODS
        }
        peak = read_peak()
        return _successful_execution(
            task,
            evaluated_rows,
            attempt_id=attempt_id,
            role=role,
            generated_at=generated_at,
            worker_pid=pid,
            peak_memory_bytes=peak,
        )
    except Exception as error:
        try:
            peak = read_peak()
        except Exception:
            peak = 0
        return _retain_failed_cell(
            task,
            error,
            construction_certificate=construction_certificate,
            attempt_id=attempt_id,
            role=role,
            generated_at=generated_at,
            worker_pid=pid,
            peak_memory_bytes=peak,
        )


class _FixtureCapability:
    __slots__ = ()


_FIXTURE_CAPABILITY = _FixtureCapability()


def run_screening_cell_fixture(
    task: ScreeningCellTask,
    *,
    construction_certificate: Mapping[str, object],
    config: R006EConfig,
    primitives: ScientificPrimitives,
    attempt_id: str,
    role: str,
    generated_at: str,
    worker_pid: int,
    peak_rss_reader: Callable[[], int],
    fixture_capability: object,
) -> CellExecution:
    """Test-only injected boundary guarded by an opaque module capability."""

    if fixture_capability is not _FIXTURE_CAPABILITY:
        raise RuntimeError("invalid fixture capability")
    return _run_screening_cell(
        task,
        construction_certificate=construction_certificate,
        config=config,
        primitives=primitives,
        attempt_id=attempt_id,
        role=role,
        generated_at=generated_at,
        worker_pid=worker_pid,
        peak_rss_reader=peak_rss_reader,
    )


def run_screening_cell(
    task: ScreeningCellTask,
    *,
    construction_certificate: Mapping[str, object],
    config: R006EConfig,
    attempt_id: str,
    role: str,
    generated_at: str,
) -> CellExecution:
    """Production cell boundary with fixed scientific and resource wiring."""

    return _run_screening_cell(
        task,
        construction_certificate=construction_certificate,
        config=config,
        primitives=production_scientific_primitives(),
        attempt_id=attempt_id,
        role=role,
        generated_at=generated_at,
        worker_pid=os.getpid(),
        peak_rss_reader=_peak_rss_bytes,
    )
