"""Fail-closed pair supervisor and CLI for governed R006e screening v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import signal
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from multiprocessing.connection import Connection, wait
from pathlib import Path
import secrets
from types import MappingProxyType
from typing import Any

from scripts.experiments.r006e_attempt_ledger_v2 import (
    AuthorizationError,
    ClaimError,
    PairClaimToken,
    ScreeningV2Paths,
    TestOnlyFixtureTrustVerifier,
    TrustVerifier,
    prepare_screening_pair,
    prepare_screening_pair_for_test,
    publish_incomplete_terminal,
    publish_terminal,
    start_screening_role,
)
from scripts.experiments.r006e_duplicate_audit_v2 import (
    DuplicateIntegrityError,
    compare_scientific_attempts,
)
from scripts.experiments.r006e_native_protocol import R006EConfig
from scripts.experiments.r006e_screening_executor_v2 import (
    CellExecution,
    ScreeningCellTask,
    _validated_cell_execution,
    combine_cell_executions,
    retain_worker_failure,
    run_screening_cell,
    screening_cell_tasks,
)
from scripts.experiments.r006e_screening_outputs_v2 import (
    RoleMetadata,
    build_role_artifacts,
    parse_replication_csv,
    publish_role_artifacts,
    verify_published_role,
)
from scripts.experiments.r006e_screening_schema_v2 import (
    V2_CONTROL_ROOT,
    V2_PRIMARY_ROOT,
    V2_REPEAT_ROOT,
)


def _six_workers(value: str) -> int:
    if value != "6":
        raise argparse.ArgumentTypeError("--workers must equal 6")
    return 6


_FIXTURE_CAPABILITY_KEY = object()
_FIXTURE_STATES: dict[str, "_FixtureSupervisorState"] = {}
_ROLE_TIMEOUT_SECONDS = 120.0
_CELL_TIMEOUT_SECONDS = 30.0
_JOIN_TIMEOUT_SECONDS = 10.0
_PRODUCTION_TRUST_VERIFIER: TrustVerifier | None = None
_PRODUCTION_FROZEN_V1_VERIFIER: Callable[[], str] | None = None
_PRODUCTION_PREFLIGHT: (
    Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None
) = None
_PRODUCTION_CERTIFICATE_LOADER: (
    Callable[
        [Mapping[str, Any]],
        Mapping[tuple[int, float, float, float], Mapping[str, object]],
    ]
    | None
) = None


class _FixtureSupervisorCapability:
    """Private one-use handle to an already claimed fixture pair."""

    __slots__ = ("_nonce",)

    def __new__(cls, key: object = None, nonce: str = ""):
        if key is not _FIXTURE_CAPABILITY_KEY:
            raise TypeError("fixture supervisor capability is private")
        instance = super().__new__(cls)
        instance._nonce = nonce
        return instance


@dataclass(frozen=True)
class _FixtureSupervisorState:
    claim: PairClaimToken
    config: R006EConfig
    construction_certificates: Mapping[tuple[int, float, float, float], Mapping[str, object]]


@dataclass(frozen=True)
class PairScreeningResult:
    integrity_status: str
    primary_status: str
    repeat_status: str
    comparison: Mapping[str, object] | None


@dataclass(frozen=True)
class _RoleOutcome:
    status: str
    payload: Mapping[str, object] | None
    hashes: Mapping[str, str] | None


@dataclass(frozen=True)
class _ProductionCellRunner:
    config: R006EConfig

    def __call__(
        self,
        task: ScreeningCellTask,
        certificate: Mapping[str, object],
        attempt_id: str,
        role: str,
        generated_at: str,
    ) -> CellExecution:
        return run_screening_cell(
            task,
            construction_certificate=certificate,
            config=self.config,
            attempt_id=attempt_id,
            role=role,
            generated_at=generated_at,
        )


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _plain_execution(execution: CellExecution) -> dict[str, list[dict[str, object]]]:
    return {
        name: [dict(record) for record in getattr(execution, name)]
        for name in ("replications", "diagnostics", "resources", "row_journals")
    }


def _restore_execution(value: Mapping[str, Any]) -> CellExecution:
    return CellExecution(
        **{
            name: tuple(MappingProxyType(dict(record)) for record in value[name])
            for name in ("replications", "diagnostics", "resources", "row_journals")
        }
    )


def _validate_worker_execution(
    execution: CellExecution, task: ScreeningCellTask
) -> CellExecution:
    validated = _validated_cell_execution(execution)
    fields = ("seed", "rho", "a3", "eta", "method")
    for records in (
        validated.replications,
        validated.diagnostics,
        validated.resources,
        validated.row_journals,
    ):
        identities = tuple(tuple(record[field] for field in fields) for record in records)
        if identities != task.method_identities:
            raise ValueError("worker result must contain the task's exact four identities")
    return validated


def _cell_process(
    sender: Connection,
    task: ScreeningCellTask,
    certificate: Mapping[str, object],
    attempt_id: str,
    role: str,
    generated_at: str,
    runner: Callable[..., CellExecution],
) -> None:
    try:
        execution = runner(task, certificate, attempt_id, role, generated_at)
        sender.send(("ok", os.getpid(), _plain_execution(execution)))
    except BaseException:
        try:
            sender.send(("failure", os.getpid(), None))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        sender.close()


def _stop_process(process: multiprocessing.Process) -> None:
    if process.is_alive():
        process.terminate()
    process.join(_JOIN_TIMEOUT_SECONDS)
    if process.is_alive():
        process.kill()
        process.join(_JOIN_TIMEOUT_SECONDS)


def _run_cells(
    *,
    runner: Callable[..., CellExecution],
    certificates: Mapping[tuple[int, float, float, float], Mapping[str, object]],
    attempt_id: str,
    role: str,
    generated_at: str,
    workers: int,
) -> CellExecution:
    if workers != 6:
        raise ValueError("workers must equal 6")
    tasks = screening_cell_tasks()
    if len(tasks) != 80:
        raise RuntimeError("screening task inventory must equal 80")
    context = multiprocessing.get_context("fork")
    pending = list(enumerate(tasks))
    active: dict[Connection, tuple[int, ScreeningCellTask, multiprocessing.Process, float]] = {}
    completed: dict[int, CellExecution] = {}
    try:
        while pending or active:
            while pending and len(active) < workers:
                index, task = pending.pop(0)
                receiver, sender = context.Pipe(duplex=False)
                process = context.Process(
                    target=_cell_process,
                    args=(
                        sender,
                        task,
                        certificates[task.identity],
                        attempt_id,
                        role,
                        generated_at,
                        runner,
                    ),
                )
                process.start()
                sender.close()
                active[receiver] = (index, task, process, time.monotonic())

            ready = wait(tuple(active), timeout=0.05)
            for receiver in ready:
                index, task, process, _ = active.pop(receiver)
                try:
                    kind, worker_pid, value = receiver.recv()
                except EOFError:
                    kind, worker_pid, value = "failure", process.pid or 0, None
                finally:
                    receiver.close()
                process.join(_JOIN_TIMEOUT_SECONDS)
                if process.is_alive():
                    _stop_process(process)
                    kind = "failure"
                if kind == "ok" and process.exitcode == 0:
                    try:
                        completed[index] = _validate_worker_execution(
                            _restore_execution(value), task
                        )
                    except Exception:
                        kind = "failure"
                if kind != "ok" or process.exitcode != 0:
                    completed[index] = retain_worker_failure(
                        task,
                        construction_certificate=certificates[task.identity],
                        attempt_id=attempt_id,
                        role=role,
                        generated_at=generated_at,
                        worker_pid=int(worker_pid),
                        peak_memory_bytes=0,
                    )

            now = time.monotonic()
            for receiver, (index, task, process, started) in tuple(active.items()):
                if process.is_alive() and now - started <= _CELL_TIMEOUT_SECONDS:
                    continue
                if not process.is_alive() and receiver.poll():
                    continue
                active.pop(receiver)
                receiver.close()
                if process.is_alive():
                    _stop_process(process)
                else:
                    process.join()
                completed[index] = retain_worker_failure(
                    task,
                    construction_certificate=certificates[task.identity],
                    attempt_id=attempt_id,
                    role=role,
                    generated_at=generated_at,
                    worker_pid=process.pid or 0,
                    peak_memory_bytes=0,
                )
        ordered = tuple(completed[index] for index in range(len(tasks)))
        return combine_cell_executions(ordered, governance_only=True)
    finally:
        for receiver, (_, _, process, _) in tuple(active.items()):
            receiver.close()
            _stop_process(process)


def _role_process(
    sender: Connection,
    *,
    root: Path,
    claim_values: Mapping[str, object],
    attempt_values: Mapping[str, object],
    config: R006EConfig,
    certificates: Mapping[tuple[int, float, float, float], Mapping[str, object]],
    runner: Callable[..., CellExecution],
    workers: int,
) -> None:
    def stop_role(signum: int, frame: object) -> None:
        del signum, frame
        raise SystemExit(1)

    signal.signal(signal.SIGTERM, stop_role)
    snapshot = None
    try:
        generated_at = _iso_now()
        execution = _run_cells(
            runner=runner,
            certificates=certificates,
            attempt_id=str(attempt_values["attempt_id"]),
            role=str(attempt_values["role"]),
            generated_at=generated_at,
            workers=workers,
        )
        payload = claim_values["payload"]
        metadata = RoleMetadata(
            decision_id=str(claim_values["decision_id"]),
            attempt_id=str(attempt_values["attempt_id"]),
            role=str(attempt_values["role"]),
            pair_claim_sha256=str(claim_values["pair_claim_sha256"]),
            role_start_sha256=str(attempt_values["role_start_sha256"]),
            construction_sha256=str(payload["construction_canonical_sha256"]),
            config_sha256=str(payload["config_sha256"]),
            candidate_sha256=str(payload["candidate_sha256"]),
            provenance_sha256=str(payload["provenance_sha256"]),
            started_at=str(attempt_values["started_at"]),
            finished_at=_iso_now(),
            generated_at=generated_at,
        )
        artifacts = build_role_artifacts(execution, config=config, metadata=metadata)
        snapshot = publish_role_artifacts(root, artifacts)
        verified = verify_published_role(snapshot, config=config)
        result = json.loads(verified["result"])
        scientific = {
            "replication": [dict(row) for row in parse_replication_csv(verified["replication"])],
            "summary": _screening_summary_from_bytes(verified["summary"]),
            "result": result,
        }
        hashes = {
            name: hashlib.sha256(verified[key]).hexdigest()
            for name, key in (
                ("replication_sha256", "replication"),
                ("summary_sha256", "summary"),
                ("result_sha256", "result"),
                ("diagnostics_sha256", "diagnostic"),
                ("resources_sha256", "resource"),
                ("row_journal_sha256", "row_journal"),
            )
        }
        sender.send(("complete", result["status"], scientific, hashes))
    except BaseException:
        try:
            sender.send(("incomplete", None, None, None))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        if snapshot is not None:
            snapshot.close()
        sender.close()


def _screening_summary_from_bytes(payload: bytes) -> list[dict[str, object]]:
    """Parse a role summary through the exact output schema."""

    # The output module intentionally keeps this parser private. Reconstructing
    # through its canonical CSV scalar parser would duplicate governance logic,
    # so role children use the verified result's internal parser here.
    from scripts.experiments import r006e_screening_outputs_v2 as outputs

    return [dict(row) for row in outputs._parse_summary_csv(payload)]


def _await_role(
    process: multiprocessing.Process,
    receiver: Connection,
) -> tuple[str, str | None, Mapping[str, object] | None, Mapping[str, str] | None]:
    deadline = time.monotonic() + _ROLE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if receiver.poll(0.05):
            try:
                message = receiver.recv()
            except EOFError:
                break
            process.join(_JOIN_TIMEOUT_SECONDS)
            if process.is_alive():
                _stop_process(process)
                return ("incomplete", None, None, None)
            return message if process.exitcode == 0 else ("incomplete", None, None, None)
        if not process.is_alive():
            break
    _stop_process(process)
    return ("incomplete", None, None, None)


def _run_role(
    state: _FixtureSupervisorState,
    role: str,
    runner: Callable[..., CellExecution],
    workers: int,
    crash: bool,
) -> _RoleOutcome:
    attempt = start_screening_role(state.claim, role)
    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    target = _crash_role_process if crash else _role_process
    process = context.Process(
        target=target,
        kwargs={
            "sender": sender,
            "root": state.claim.paths.primary if role == "primary" else state.claim.paths.repeat,
            "claim_values": {
                "decision_id": state.claim.authorization.decision_id,
                "pair_claim_sha256": state.claim.pair_claim_sha256,
                "payload": dict(state.claim.authorization.payload),
            },
            "attempt_values": {
                "attempt_id": attempt.attempt_id,
                "role": attempt.role,
                "role_start_sha256": attempt.role_start_sha256,
                "started_at": attempt.started_at,
            },
            "config": state.config,
            "certificates": state.construction_certificates,
            "runner": runner,
            "workers": workers,
        },
    )
    process.start()
    sender.close()
    kind, status, payload, hashes = _await_role(process, receiver)
    receiver.close()
    if kind != "complete" or status not in {"PASS", "FAIL"} or hashes is None:
        publish_incomplete_terminal(
            attempt,
            exit_code=process.exitcode,
            failure_code="ROLE_CHILD_DIED",
            failure_reason="role child exited without complete verified output",
        )
        return _RoleOutcome("INCOMPLETE", None, None)
    publish_terminal(
        attempt,
        status=status,
        exit_code=0,
        failure_code=None,
        failure_reason=None,
        **hashes,
    )
    return _RoleOutcome(status, payload, hashes)


def _crash_role_process(**kwargs: Any) -> None:
    del kwargs
    os._exit(91)


def _prepare_production_claim(
    *, paths: ScreeningV2Paths, authorization: Path
) -> PairClaimToken:
    """Prepare an authorization-only durable claim without screening certificates."""

    return _prepare_production_pair(paths=paths, authorization=authorization)


def _prepare_production_pair(
    *,
    paths: ScreeningV2Paths,
    authorization: Path,
    post_trust_preclaim: (
        Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None
    ) = None,
) -> PairClaimToken:
    """Enter Task 3 only when every private production binding is configured."""

    if (
        _PRODUCTION_TRUST_VERIFIER is None
        or _PRODUCTION_FROZEN_V1_VERIFIER is None
        or _PRODUCTION_PREFLIGHT is None
    ):
        raise AuthorizationError("production runtime bindings are unavailable")
    return prepare_screening_pair(
        paths=paths,
        authorization=authorization,
        scientific_runner=lambda: None,
        trust_verifier=_PRODUCTION_TRUST_VERIFIER,
        frozen_v1_verifier=_PRODUCTION_FROZEN_V1_VERIFIER,
        preflight=_PRODUCTION_PREFLIGHT,
        post_trust_preclaim=post_trust_preclaim,
    )


def _load_production_certificates(
    authorization_payload: Mapping[str, Any],
) -> Mapping[tuple[int, float, float, float], Mapping[str, object]]:
    if _PRODUCTION_CERTIFICATE_LOADER is None:
        raise AuthorizationError("production certificate loader is unavailable")
    certificates = _PRODUCTION_CERTIFICATE_LOADER(
        deepcopy(dict(authorization_payload))
    )
    owned = {
        identity: deepcopy(dict(certificate))
        for identity, certificate in certificates.items()
    }
    expected = {task.identity for task in screening_cell_tasks()}
    if set(owned) != expected:
        raise AuthorizationError("production certificates must cover exactly 80 tasks")
    return MappingProxyType(owned)


def _prepare_production_screening_pair(
    *, paths: ScreeningV2Paths, authorization: Path
) -> tuple[
    PairClaimToken,
    Mapping[tuple[int, float, float, float], Mapping[str, object]],
]:
    if _PRODUCTION_CERTIFICATE_LOADER is None:
        raise AuthorizationError("production certificate loader is unavailable")
    prepared: dict[
        str,
        Mapping[tuple[int, float, float, float], Mapping[str, object]],
    ] = {}

    def load_after_trust(
        payload: Mapping[str, Any], active_paths: ScreeningV2Paths
    ) -> None:
        if active_paths != paths or prepared:
            raise AuthorizationError("invalid post-trust certificate callback state")
        prepared["certificates"] = _load_production_certificates(payload)

    claim = _prepare_production_pair(
        paths=paths,
        authorization=authorization,
        post_trust_preclaim=load_after_trust,
    )
    return claim, prepared["certificates"]


def _run_claimed_pair(
    state: _FixtureSupervisorState,
    *,
    cell_runner: Callable[..., CellExecution],
    workers: int,
    crash_roles: frozenset[str],
) -> PairScreeningResult:
    try:
        primary = _run_role(
            state, "primary", cell_runner, workers, "primary" in crash_roles
        )
        repeat = _run_role(
            state, "repeat", cell_runner, workers, "repeat" in crash_roles
        )
        comparison = None
        integrity = "FAIL"
        if primary.payload is not None and repeat.payload is not None:
            try:
                comparison = compare_scientific_attempts(primary.payload, repeat.payload)
            except DuplicateIntegrityError:
                comparison = None
            else:
                integrity = str(comparison["status"])
        return PairScreeningResult(
            integrity_status=integrity,
            primary_status=primary.status,
            repeat_status=repeat.status,
            comparison=comparison,
        )
    finally:
        state.claim.root_snapshot.close()


def _run_production_screening_pair(
    *,
    claim: PairClaimToken,
    certificates: Mapping[tuple[int, float, float, float], Mapping[str, object]],
    workers: int,
) -> PairScreeningResult:
    config = R006EConfig()
    state = _FixtureSupervisorState(claim, config, certificates)
    return _run_claimed_pair(
        state,
        cell_runner=_ProductionCellRunner(config),
        workers=workers,
        crash_roles=frozenset(),
    )


def _prepare_fixture_supervisor(
    *,
    paths: ScreeningV2Paths,
    authorization: Path,
    trust_verifier: TestOnlyFixtureTrustVerifier,
    frozen_v1_verifier: Callable[[], str],
    preflight: Callable[[Mapping[str, Any], ScreeningV2Paths], None],
    config: R006EConfig,
    construction_certificates: Mapping[
        tuple[int, float, float, float], Mapping[str, object]
    ],
) -> _FixtureSupervisorCapability:
    expected = {task.identity for task in screening_cell_tasks()}
    if set(construction_certificates) != expected:
        raise ValueError("construction certificates must cover exactly 80 tasks")
    claim = prepare_screening_pair_for_test(
        paths=paths,
        authorization=authorization,
        fixture_trust_verifier=trust_verifier,
        frozen_v1_verifier=frozen_v1_verifier,
        preflight=preflight,
        scientific_runner=lambda: None,
    )
    nonce = secrets.token_hex(32)
    _FIXTURE_STATES[nonce] = _FixtureSupervisorState(
        claim=claim,
        config=config,
        construction_certificates=MappingProxyType(dict(construction_certificates)),
    )
    return _FixtureSupervisorCapability(_FIXTURE_CAPABILITY_KEY, nonce)


def _run_fixture_screening_pair(
    capability: _FixtureSupervisorCapability,
    *,
    cell_runner: Callable[..., CellExecution],
    workers: int,
    crash_roles: frozenset[str] = frozenset(),
) -> PairScreeningResult:
    if workers != 6:
        raise ValueError("workers must equal 6")
    nonce = getattr(capability, "_nonce", None)
    state = _FIXTURE_STATES.pop(nonce, None)
    if state is None:
        raise ValueError("invalid or consumed fixture supervisor capability")
    return _run_claimed_pair(
        state,
        cell_runner=cell_runner,
        workers=workers,
        crash_roles=crash_roles,
    )


def _fixture_supervisor_loss(capability: _FixtureSupervisorCapability) -> None:
    """Fixture-only irreversible supervisor loss after the primary start claim."""

    nonce = getattr(capability, "_nonce", None)
    state = _FIXTURE_STATES.pop(nonce, None)
    if state is None:
        raise ValueError("invalid or consumed fixture supervisor capability")
    start_screening_role(state.claim, "primary")
    os._exit(92)


def _add_production_roots(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--primary-root", default=V2_PRIMARY_ROOT)
    parser.add_argument("--repeat-root", default=V2_REPEAT_ROOT)
    parser.add_argument("--control-root", default=V2_CONTROL_ROOT)


def _run_construction_v2(paths: ScreeningV2Paths) -> Mapping[str, object]:
    """Run the outcome-free construction boundary for the exact v2 roots.

    Keep this import and call isolated from the production claim path.  The
    construction builder only publishes its two construction files; it does
    not prepare a claim, load screening certificates, or execute a cell.
    """

    from scripts.experiments.r006e_construction_v2 import (
        ConstructionV2Paths,
        build_construction_v2,
    )

    construction_paths = ConstructionV2Paths(
        paths.primary,
        paths.repeat,
        paths.control,
        plan=getattr(paths, "plan", ConstructionV2Paths.__dataclass_fields__["plan"].default),
        protocol=getattr(paths, "protocol", ConstructionV2Paths.__dataclass_fields__["protocol"].default),
        future_checklist=getattr(
            paths,
            "future_checklist",
            ConstructionV2Paths.__dataclass_fields__["future_checklist"].default,
        ),
    )
    return build_construction_v2(construction_paths)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="r006e-screening-v2")
    commands = parser.add_subparsers(dest="phase", required=True)
    construction = commands.add_parser("construction-v2")
    _add_production_roots(construction)

    authorization = commands.add_parser("verify-authorization")
    authorization.add_argument("--authorization", required=True)
    _add_production_roots(authorization)

    screening = commands.add_parser("screening-pair")
    screening.add_argument("--workers", required=True, type=_six_workers)
    screening.add_argument("--authorization", required=True)
    _add_production_roots(screening)
    return parser


def _validated_production_paths(arguments: argparse.Namespace) -> ScreeningV2Paths:
    expected = tuple(
        (Path.cwd() / relative).resolve(strict=False)
        for relative in (V2_PRIMARY_ROOT, V2_REPEAT_ROOT, V2_CONTROL_ROOT)
    )
    actual = tuple(
        Path(value).expanduser().resolve(strict=False)
        for value in (
            arguments.primary_root,
            arguments.repeat_root,
            arguments.control_root,
        )
    )
    if actual != expected:
        raise ClaimError("production roots do not match the frozen v2 roots")
    return ScreeningV2Paths(*actual)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        paths = _validated_production_paths(arguments)
        if arguments.phase == "construction-v2":
            artifact = _run_construction_v2(paths)
            print(f"construction-v2 status: {artifact['status']}")
            return 0
        if arguments.phase == "verify-authorization":
            claim = _prepare_production_claim(
                paths=paths,
                authorization=Path(arguments.authorization),
            )
            claim.root_snapshot.close()
            print("verify-authorization completed with a retained pair claim")
            return 0
        claim, certificates = _prepare_production_screening_pair(
            paths=paths,
            authorization=Path(arguments.authorization),
        )
        result = _run_production_screening_pair(
            claim=claim,
            certificates=certificates,
            workers=arguments.workers,
        )
        print(f"screening-pair integrity status: {result.integrity_status}")
        return 0 if result.integrity_status == "PASS" else 1
    except (AuthorizationError, ClaimError, OSError, RuntimeError, TypeError, ValueError):
        print(f"{arguments.phase} refused by governed preflight", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
