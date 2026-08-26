"""Fail-closed authorization and durable attempt ledger for R006e screening v2."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import secrets
import socket
import stat
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar, Protocol

from scripts.experiments.r006e_screening_schema_v2 import (
    DOCUMENT_TYPES,
    SCHEMA_VERSION,
    SCREENING_OUTPUT_NAMES,
    V2_CONTROL_ROOT,
    V2_PRIMARY_ROOT,
    V2_REPEAT_ROOT,
    validate_schema,
)


PAIR_CLAIM_FILENAME = "screening_pair_claim.json"
ROLE_START_FILENAMES = {
    "primary": "screening_primary_start.json",
    "repeat": "screening_repeat_start.json",
}
ROLE_TERMINAL_FILENAMES = {
    "primary": "screening_primary_terminal.json",
    "repeat": "screening_repeat_terminal.json",
}
ROLE_CONTROL_START_FILENAMES = {
    "primary": "screening_primary_start_claim.json",
    "repeat": "screening_repeat_start_claim.json",
}
ROLE_CONTROL_TERMINAL_FILENAMES = {
    "primary": "screening_primary_terminal_claim.json",
    "repeat": "screening_repeat_terminal_claim.json",
}
PRIMARY_CONSTRUCTION_NAMES = (
    "construction_gate_preoutcome.json",
    "construction_manifest.sha256",
)
_ROLE_OUTPUT_FILENAMES = frozenset(
    (
        *SCREENING_OUTPUT_NAMES,
        "screening_diagnostics.jsonl",
        "screening_resources.jsonl",
        "screening_row_journal.jsonl",
        "screening_terminal.json",
        "screening_manifest.json",
    )
)
_EXPECTED_ROOT_NAMES = (
    Path(V2_PRIMARY_ROOT).name,
    Path(V2_REPEAT_ROOT).name,
    Path(V2_CONTROL_ROOT).name,
)
_FIXTURE_PATH_CAPABILITY = object()
_DESCRIPTOR_PUBLICATION_SUPPORTED = all(
    function in os.supports_dir_fd
    for function in (os.open, os.link, os.unlink, os.stat)
)


class AuthorizationError(RuntimeError):
    """Raised before science when screening authorization is not valid."""


class ClaimError(RuntimeError):
    """Raised when an output root or durable claim is not pristine."""


class TrustVerifier(Protocol):
    def verify(self, evidence: Mapping[str, Any], signed_payload: bytes) -> bool: ...


@dataclass(frozen=True)
class ConfiguredTrustVerifier:
    """Production boundary for externally supplied detached-signature verification."""

    pinned_key_id: str
    trust_policy_id: str
    verify_detached: Callable[[Mapping[str, Any], bytes], bool]
    def verify(self, evidence: Mapping[str, Any], signed_payload: bytes) -> bool:
        if evidence["pinned_key_id"] != self.pinned_key_id:
            return False
        if evidence["trust_policy_id"] != self.trust_policy_id:
            return False
        return self.verify_detached(evidence, signed_payload) is True


@dataclass(frozen=True)
class TestOnlyFixtureTrustVerifier:
    """Explicit fixture-only substitute; production entry points reject it."""

    verify_fixture: Callable[[Mapping[str, Any], bytes], bool]
    test_only: ClassVar[bool] = True

    def verify(self, evidence: Mapping[str, Any], signed_payload: bytes) -> bool:
        return self.verify_fixture(evidence, signed_payload) is True


@dataclass(frozen=True)
class ScreeningV2Paths:
    primary: Path
    repeat: Path
    control: Path

    @classmethod
    def under(cls, parent: Path) -> "ScreeningV2Paths":
        return cls(
            Path(parent) / _EXPECTED_ROOT_NAMES[0],
            Path(parent) / _EXPECTED_ROOT_NAMES[1],
            Path(parent) / _EXPECTED_ROOT_NAMES[2],
        )


@dataclass(frozen=True)
class DirectoryFileSnapshot:
    name: str
    identity: tuple[int, int, int, int]
    sha256: str


@dataclass(frozen=True)
class DirectorySnapshot:
    path: Path
    identity: tuple[int, int]
    entries: tuple[str, ...]
    files: tuple[DirectoryFileSnapshot, ...]
    descriptor: int


class _DescriptorLease:
    """Private synchronized ownership of immutable snapshot descriptors."""

    __slots__ = ("__active", "__lock")

    def __init__(self, descriptors: tuple[int, ...]) -> None:
        self.__active = set(descriptors)
        self.__lock = threading.Lock()

    def close(self) -> None:
        with self.__lock:
            descriptors = tuple(self.__active)
            self.__active.clear()
        for descriptor in descriptors:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def active_descriptors(self) -> tuple[int, ...]:
        with self.__lock:
            return tuple(sorted(self.__active))


@dataclass(frozen=True)
class RootSnapshot:
    paths: ScreeningV2Paths
    primary: DirectorySnapshot
    repeat: DirectorySnapshot
    control: DirectorySnapshot
    fixture_capability: object | None = None
    _close_lock: threading.Lock = field(
        default_factory=threading.Lock, compare=False, repr=False
    )
    _descriptor_lease: _DescriptorLease = field(
        init=False, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_descriptor_lease",
            _DescriptorLease(
                (
                    self.primary.descriptor,
                    self.repeat.descriptor,
                    self.control.descriptor,
                )
            ),
        )

    def close(self) -> None:
        """Release held directory descriptors (populated by descriptor scans)."""

        with self._close_lock:
            lease = self._descriptor_lease
        lease.close()


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    content: bytes
    identity: tuple[int, int, int, int]


@dataclass(frozen=True)
class ScreeningAuthorization:
    envelope: Mapping[str, Any]
    payload: Mapping[str, Any]
    artifact_path: Path
    artifact_file_snapshot: FileSnapshot

    @property
    def decision_id(self) -> str:
        return str(self.payload["decision_id"])


_CAPABILITY_CONSTRUCTOR_KEY = object()


class PreparedPairCapability:
    """Opaque one-use proof that every authorization barrier completed."""

    __slots__ = ("_nonce",)

    def __new__(cls, key: object = None, nonce: str = "") -> "PreparedPairCapability":
        if key is not _CAPABILITY_CONSTRUCTOR_KEY:
            raise TypeError("PreparedPairCapability cannot be constructed directly")
        instance = super().__new__(cls)
        instance._nonce = nonce
        return instance


@dataclass(frozen=True)
class _PreparedPairState:
    authorization: ScreeningAuthorization
    snapshot: RootSnapshot


_PREPARED_PAIR_CAPABILITIES: dict[str, _PreparedPairState] = {}


@dataclass(frozen=True)
class PairClaimToken:
    paths: ScreeningV2Paths
    authorization: ScreeningAuthorization
    claim_path: Path
    pair_claim_sha256: str
    primary_attempt_id: str
    repeat_attempt_id: str
    supervisor_pid: int
    capability: str
    root_identities: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]
    root_snapshot: RootSnapshot


@dataclass(frozen=True)
class AttemptToken:
    claim: PairClaimToken
    role: str
    attempt_id: str
    start_path: Path
    role_start_sha256: str
    started_at: str


@dataclass(frozen=True)
class TerminalToken:
    attempt: AttemptToken
    path: Path
    status: str
    terminal_sha256: str


_ACTIVE_CLAIMS: dict[Path, str] = {}
_ROOT_TRANSACTION_LOCK = threading.RLock()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _stable_read(path: Path) -> FileSnapshot:
    target = Path(path)
    try:
        link_stat = os.lstat(target)
    except OSError as error:
        raise AuthorizationError(f"authorization file is missing: {target}") from error
    if stat.S_ISLNK(link_stat.st_mode) or not stat.S_ISREG(link_stat.st_mode):
        raise AuthorizationError("authorization requires a regular non-symlink file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags)
    except OSError as error:
        raise AuthorizationError("authorization requires a regular non-symlink file") from error
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    before_id = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_id = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    link_id = (
        link_stat.st_dev, link_stat.st_ino, link_stat.st_size, link_stat.st_mtime_ns,
    )
    content = b"".join(chunks)
    if before_id != after_id or before_id != link_id or len(content) != before.st_size:
        raise AuthorizationError("authorization file changed during stable read")
    return FileSnapshot(target, content, before_id)


def _require_unchanged(snapshot: FileSnapshot) -> None:
    current = _stable_read(snapshot.path)
    if current.identity != snapshot.identity or current.content != snapshot.content:
        raise AuthorizationError("authorization file changed during verification")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuthorizationError(f"authorization has duplicate key: {key}")
        result[key] = value
    return result


def _parse_json(content: bytes) -> Mapping[str, Any]:
    try:
        value = json.loads(
            content.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                AuthorizationError(f"authorization has non-finite value: {value}")
            ),
        )
    except AuthorizationError:
        raise
    except Exception as error:
        raise AuthorizationError("authorization is not strict UTF-8 JSON") from error
    if not isinstance(value, Mapping):
        raise AuthorizationError("authorization envelope must be an object")
    return value


def _require_sha256_fields(value: Any, path: str = "authorization") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key.endswith("_sha256"):
                if (
                    not isinstance(item, str) or len(item) != 64
                    or any(character not in "0123456789abcdef" for character in item)
                ):
                    raise AuthorizationError(f"{child} must be a lowercase SHA-256")
            _require_sha256_fields(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _require_sha256_fields(item, f"{path}[{index}]")


def _verify_envelope(path: Path) -> ScreeningAuthorization:
    snapshot = _stable_read(path)
    envelope = _parse_json(snapshot.content)
    try:
        validate_schema("authorization_envelope", envelope)
        payload = envelope["payload"]
        trust = envelope["trust_evidence"]
        validate_schema("authorization_payload", payload)
        validate_schema("trust_evidence", trust)
    except Exception as error:
        raise AuthorizationError(f"authorization schema violation: {error}") from error
    _require_sha256_fields(envelope)
    for field in ("decision_id", "authorizer_id", "issued_at"):
        if not isinstance(payload[field], str) or not payload[field]:
            raise AuthorizationError(f"authorization payload {field} must be non-empty")
    for field in (
        "signature_algorithm", "pinned_key_id", "detached_signature",
        "trust_policy_id", "external_witness_id",
    ):
        if not isinstance(trust[field], str) or not trust[field]:
            raise AuthorizationError(f"trust evidence {field} must be non-empty")
    payload_sha256 = canonical_json_sha256(payload)
    if envelope["payload_sha256"] != payload_sha256:
        raise AuthorizationError("authorization payload digest mismatch")
    artifact_core = {
        "schema_version": envelope["schema_version"],
        "document_type": envelope["document_type"],
        "payload": payload,
        "payload_sha256": payload_sha256,
    }
    artifact_sha256 = canonical_json_sha256(artifact_core)
    if envelope["artifact_sha256"] != artifact_sha256:
        raise AuthorizationError("authorization artifact digest mismatch")
    if canonical_json_sha256(trust) != envelope["trust_evidence_sha256"]:
        raise AuthorizationError("authorization trust evidence digest mismatch")
    if trust["authorization_artifact_sha256"] != artifact_sha256:
        raise AuthorizationError("trust evidence artifact digest mismatch")
    if trust["signed_payload_sha256"] != payload_sha256:
        raise AuthorizationError("trust evidence signed payload digest mismatch")
    signature = trust["detached_signature"]
    if hashlib.sha256(signature.encode("utf-8")).hexdigest() != trust[
        "detached_signature_sha256"
    ]:
        raise AuthorizationError("detached signature digest mismatch")
    return ScreeningAuthorization(envelope, payload, Path(path), snapshot)


def _validate_path_names(paths: ScreeningV2Paths) -> None:
    actual = (paths.primary.name, paths.repeat.name, paths.control.name)
    if actual != _EXPECTED_ROOT_NAMES:
        raise ClaimError("paths must use the three exact v2 output roots")
    if any(name in {"r006e_native_supported_recovery", "r006e_native_supported_recovery_repeat"} for name in actual):
        raise ClaimError("v1 roots are forbidden")


def _validate_production_paths(paths: ScreeningV2Paths) -> None:
    expected = tuple(
        (Path.cwd() / relative).resolve(strict=False)
        for relative in (V2_PRIMARY_ROOT, V2_REPEAT_ROOT, V2_CONTROL_ROOT)
    )
    actual = tuple(
        path.expanduser().resolve(strict=False)
        for path in (paths.primary, paths.repeat, paths.control)
    )
    if actual != expected:
        raise ClaimError("production requires the exact frozen absolute v2 roots")


def _stable_directory_file(
    descriptor: int, name: str,
) -> tuple[bytes, tuple[int, int, int, int]]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        path_before = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        file_descriptor = os.open(name, flags, dir_fd=descriptor)
    except OSError as error:
        raise ClaimError(f"entry must be a stable regular non-symlink file: {name}") from error
    try:
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ClaimError(f"entry must be a regular non-symlink file: {name}")
        chunks: list[bytes] = []
        while chunk := os.read(file_descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(file_descriptor)
    finally:
        os.close(file_descriptor)
    try:
        path_after = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except OSError as error:
        raise ClaimError(f"construction file changed during scan: {name}") from error
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    if (
        before_identity
        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        or before_identity
        != (
            path_before.st_dev, path_before.st_ino, path_before.st_size,
            path_before.st_mtime_ns,
        )
        or before_identity
        != (
            path_after.st_dev, path_after.st_ino, path_after.st_size,
            path_after.st_mtime_ns,
        )
    ):
        raise ClaimError(f"construction file changed during scan: {name}")
    content = b"".join(chunks)
    if len(content) != before.st_size:
        raise ClaimError(f"construction file changed during scan: {name}")
    return content, before_identity


def _snapshot_directory_file(descriptor: int, name: str) -> DirectoryFileSnapshot:
    content, identity = _stable_directory_file(descriptor, name)
    return DirectoryFileSnapshot(name, identity, hashlib.sha256(content).hexdigest())


def _scan_directory(path: Path, allowed: frozenset[str]) -> DirectorySnapshot:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        path_before = os.lstat(path)
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ClaimError(f"v2 root must be an existing non-symlink directory: {path}") from error
    if stat.S_ISLNK(path_before.st_mode) or not stat.S_ISDIR(path_before.st_mode):
        os.close(descriptor)
        raise ClaimError(f"v2 root must be an existing non-symlink directory: {path}")
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISDIR(before.st_mode):
            raise ClaimError(f"v2 root is not a directory: {path}")
        entries = tuple(sorted(os.listdir(descriptor)))
        files: list[DirectoryFileSnapshot] = []
        for name in entries:
            if name.startswith("."):
                raise ClaimError(f"unexpected dotfile in v2 root: {name}")
            if name not in allowed:
                raise ClaimError(f"unexpected entry in v2 root: {name}")
            files.append(_snapshot_directory_file(descriptor, name))
        after = os.fstat(descriptor)
        path_after = os.lstat(path)
        before_id = (before.st_dev, before.st_ino)
        if (
            before_id != (after.st_dev, after.st_ino)
            or before_id != (path_before.st_dev, path_before.st_ino)
            or before_id != (path_after.st_dev, path_after.st_ino)
        ):
            raise ClaimError(f"v2 root swapped during scan: {path}")
        return DirectorySnapshot(
            Path(path), before_id, entries, tuple(files), descriptor
        )
    except BaseException:
        os.close(descriptor)
        raise


def _scan_roots(paths: ScreeningV2Paths, fixture: bool) -> RootSnapshot:
    opened: list[DirectorySnapshot] = []
    try:
        opened.append(
            _scan_directory(paths.primary, frozenset(PRIMARY_CONSTRUCTION_NAMES))
        )
        opened.append(_scan_directory(paths.repeat, frozenset()))
        opened.append(_scan_directory(paths.control, frozenset()))
        return RootSnapshot(
            paths, opened[0], opened[1], opened[2],
            _FIXTURE_PATH_CAPABILITY if fixture else None,
        )
    except BaseException:
        for snapshot in opened:
            try:
                os.close(snapshot.descriptor)
            except OSError:
                pass
        raise


def scan_v2_roots(
    paths: ScreeningV2Paths, *, existing_names: Any = None,
) -> RootSnapshot:
    """Inventory only the exact production roots using directory descriptors."""

    del existing_names
    _validate_path_names(paths)
    _validate_production_paths(paths)
    return _scan_roots(paths, False)


def scan_v2_roots_for_test(
    paths: ScreeningV2Paths, *, existing_names: Any = None,
) -> RootSnapshot:
    """Explicit fixture-only scan for exact v2 basenames under a temporary parent."""

    del existing_names
    _validate_path_names(paths)
    return _scan_roots(paths, True)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_directory_descriptor(snapshot: DirectorySnapshot) -> os.stat_result:
    try:
        descriptor_stat = os.fstat(snapshot.descriptor)
    except OSError as error:
        raise ClaimError(f"verified directory descriptor was closed: {snapshot.path}") from error
    if (
        (descriptor_stat.st_dev, descriptor_stat.st_ino) != snapshot.identity
        or not stat.S_ISDIR(descriptor_stat.st_mode)
    ):
        raise ClaimError(f"verified directory descriptor changed: {snapshot.path}")
    return descriptor_stat


def _require_directory_binding(snapshot: DirectorySnapshot) -> None:
    _require_directory_descriptor(snapshot)
    try:
        path_stat = os.lstat(snapshot.path)
    except OSError as error:
        raise ClaimError(f"verified directory was replaced: {snapshot.path}") from error
    if (
        (path_stat.st_dev, path_stat.st_ino) != snapshot.identity
        or stat.S_ISLNK(path_stat.st_mode)
        or not stat.S_ISDIR(path_stat.st_mode)
    ):
        raise ClaimError(f"verified directory identity changed: {snapshot.path}")


@contextmanager
def _locked_directories(
    directories: tuple[DirectorySnapshot, ...], *, exclusive: bool
) -> Iterator[None]:
    ordered = tuple(
        sorted(
            {directory.descriptor: directory for directory in directories}.values(),
            key=lambda directory: (directory.identity, directory.descriptor),
        )
    )
    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    acquired: list[DirectorySnapshot] = []
    with _ROOT_TRANSACTION_LOCK:
        try:
            for directory in ordered:
                _require_directory_binding(directory)
                try:
                    fcntl.flock(directory.descriptor, operation)
                except OSError as error:
                    raise ClaimError(
                        f"could not lock verified directory: {directory.path}"
                    ) from error
                acquired.append(directory)
                _require_directory_binding(directory)
            yield
        finally:
            for directory in reversed(acquired):
                try:
                    fcntl.flock(directory.descriptor, fcntl.LOCK_UN)
                except OSError:
                    pass


def _rescan_directory(
    snapshot: DirectorySnapshot,
    allowed: frozenset[str],
    *,
    lock_held: bool = False,
) -> DirectorySnapshot:
    if not lock_held:
        with _locked_directories((snapshot,), exclusive=False):
            return _rescan_directory(snapshot, allowed, lock_held=True)
    _require_directory_binding(snapshot)
    entries = tuple(sorted(os.listdir(snapshot.descriptor)))
    files: list[DirectoryFileSnapshot] = []
    for name in entries:
        if name.startswith("."):
            raise ClaimError(f"unexpected dotfile in v2 root: {name}")
        if name not in allowed:
            raise ClaimError(f"unexpected entry in v2 root: {name}")
        files.append(_snapshot_directory_file(snapshot.descriptor, name))
    _require_directory_binding(snapshot)
    return DirectorySnapshot(
        snapshot.path, snapshot.identity, entries, tuple(files), snapshot.descriptor
    )


def _rollback_exact_publication(
    directory: DirectorySnapshot,
    name: str,
    expected_identity: tuple[int, int],
    *,
    tolerate_unrelated: bool = False,
) -> None:
    """Remove only the unactivated inode created by this publication attempt."""

    _require_directory_descriptor(directory)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory.descriptor)
    except FileNotFoundError:
        return
    except OSError as error:
        if tolerate_unrelated:
            return
        raise ClaimError("unactivated publication is not a regular nofollow file") from error
    try:
        opened = os.fstat(descriptor)
        path_stat = os.stat(
            name,
            dir_fd=directory.descriptor,
            follow_symlinks=False,
        )
        opened_identity = (opened.st_dev, opened.st_ino)
        path_identity = (path_stat.st_dev, path_stat.st_ino)
        if (
            opened_identity != expected_identity
            or path_identity != expected_identity
            or not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(path_stat.st_mode)
        ):
            if tolerate_unrelated:
                return
            raise ClaimError("refused to roll back a different publication inode")
        os.unlink(name, dir_fd=directory.descriptor)
        os.fsync(directory.descriptor)
        try:
            os.stat(name, dir_fd=directory.descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ClaimError("unactivated publication rollback did not remove its name")
        _require_directory_descriptor(directory)
    finally:
        os.close(descriptor)


def _exclusive_publish_at(
    directory: DirectorySnapshot,
    name: str,
    value: Mapping[str, Any],
    *,
    post_link_check: Callable[[], None] | None = None,
    lock_held: bool = False,
) -> str:
    """Publish relative to one continuously verified directory descriptor."""

    if not lock_held:
        with _locked_directories((directory,), exclusive=True):
            return _exclusive_publish_at(
                directory,
                name,
                value,
                post_link_check=post_link_check,
                lock_held=True,
            )
    if not _DESCRIPTOR_PUBLICATION_SUPPORTED:
        raise ClaimError("descriptor-relative publication is unavailable")
    payload = _canonical_json_bytes(value) + b"\n"
    payload_sha256 = hashlib.sha256(payload).hexdigest()
    temporary = f".{name}.{os.getpid()}.{secrets.token_hex(16)}"
    descriptor: int | None = None
    linked = False
    link_attempted = False
    activated = False
    source_identity: tuple[int, int] | None = None
    try:
        _require_directory_binding(directory)
        flags = (
            os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(
            temporary, flags, 0o600, dir_fd=directory.descriptor
        )
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
        os.fsync(descriptor)
        source_stat = os.fstat(descriptor)
        source_identity = (source_stat.st_dev, source_stat.st_ino)
        os.close(descriptor)
        descriptor = None
        try:
            link_attempted = True
            os.link(
                temporary, name,
                src_dir_fd=directory.descriptor,
                dst_dir_fd=directory.descriptor,
                follow_symlinks=False,
            )
            linked = True
        except FileExistsError as error:
            raise ClaimError(f"retained prior claim refuses publication: {name}") from error
        except (NotImplementedError, TypeError) as error:
            raise ClaimError("descriptor-relative hard-link publication is unavailable") from error
        os.unlink(temporary, dir_fd=directory.descriptor)
        published = os.stat(name, dir_fd=directory.descriptor, follow_symlinks=False)
        if (published.st_dev, published.st_ino) != source_identity:
            raise ClaimError("durable publication identity mismatch")
        published_snapshot = _snapshot_directory_file(directory.descriptor, name)
        if published_snapshot.sha256 != payload_sha256:
            raise ClaimError("durable publication content mismatch")
        if post_link_check is not None:
            post_link_check()
        validated_publication = _snapshot_directory_file(directory.descriptor, name)
        if validated_publication.identity[:2] != source_identity:
            raise ClaimError("durable publication identity changed after post-link check")
        if validated_publication.sha256 != payload_sha256:
            raise ClaimError("durable publication content changed after post-link check")
        os.fsync(directory.descriptor)
        _require_directory_binding(directory)
        activated = True
    except BaseException:
        if (
            not activated
            and source_identity is not None
            and (linked or link_attempted)
        ):
            _rollback_exact_publication(
                directory,
                name,
                source_identity,
                tolerate_unrelated=link_attempted and not linked,
            )
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(temporary, dir_fd=directory.descriptor)
        except FileNotFoundError:
            pass
        except OSError:
            if not linked:
                raise
    return payload_sha256


def _require_unchanged_directory_inventory(
    prior: DirectorySnapshot, current: DirectorySnapshot
) -> None:
    if (
        prior.identity != current.identity
        or prior.entries != current.entries
        or prior.files != current.files
    ):
        raise ClaimError(f"v2 root changed after preflight: {prior.path}")


def _claim_screening_pair(state: _PreparedPairState) -> PairClaimToken:
    """Consume verified state and publish the singleton claim for both roles."""

    authorization = state.authorization
    snapshot = state.snapshot

    if snapshot.primary.entries != tuple(sorted(PRIMARY_CONSTRUCTION_NAMES)):
        raise ClaimError("primary root requires both exact v2 construction inputs")
    if snapshot.repeat.entries or snapshot.control.entries:
        raise ClaimError("repeat and control roots must be empty before pair claim")
    if snapshot.fixture_capability not in (None, _FIXTURE_PATH_CAPABILITY):
        raise ClaimError("invalid fixture path capability")
    payload = authorization.payload
    claim = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["pair_claim"],
        "decision_id": payload["decision_id"],
        "authorization_artifact_sha256": authorization.envelope["artifact_sha256"],
        "authorization_payload_sha256": authorization.envelope["payload_sha256"],
        "trust_evidence_sha256": authorization.envelope["trust_evidence_sha256"],
        "frozen_v1_authority_digest": payload["frozen_v1_authority_digest"],
        "primary_attempt_id": payload["primary_attempt_id"],
        "repeat_attempt_id": payload["repeat_attempt_id"],
        "primary_root": payload["primary_root"],
        "repeat_root": payload["repeat_root"],
        "control_root": payload["control_root"],
        "claimed_at": _iso_now(),
        "supervisor_pid": os.getpid(),
        "supervisor_hostname": socket.gethostname(),
        "status": "CLAIMED",
    }
    try:
        validate_schema("pair_claim", claim)
    except Exception as error:
        raise ClaimError(f"pair claim schema violation: {error}") from error
    destination = snapshot.paths.control / PAIR_CLAIM_FILENAME
    token_capability = secrets.token_hex(32)
    roots = (snapshot.primary, snapshot.repeat, snapshot.control)
    with _locked_directories(roots, exclusive=True):
        current = (
            _rescan_directory(
                snapshot.primary,
                frozenset(PRIMARY_CONSTRUCTION_NAMES),
                lock_held=True,
            ),
            _rescan_directory(
                snapshot.repeat,
                frozenset(),
                lock_held=True,
            ),
            _rescan_directory(
                snapshot.control,
                frozenset(),
                lock_held=True,
            ),
        )
        for prior, now in zip(roots, current):
            _require_unchanged_directory_inventory(prior, now)

        def validate_post_link_inventory() -> None:
            post_primary = _rescan_directory(
                snapshot.primary,
                frozenset(PRIMARY_CONSTRUCTION_NAMES),
                lock_held=True,
            )
            post_repeat = _rescan_directory(
                snapshot.repeat,
                frozenset(),
                lock_held=True,
            )
            post_control = _rescan_directory(
                snapshot.control,
                frozenset({PAIR_CLAIM_FILENAME}),
                lock_held=True,
            )
            _require_unchanged_directory_inventory(snapshot.primary, post_primary)
            _require_unchanged_directory_inventory(snapshot.repeat, post_repeat)
            if (
                post_control.identity != snapshot.control.identity
                or post_control.entries != (PAIR_CLAIM_FILENAME,)
            ):
                raise ClaimError("control root changed during pair claim publication")

        claim_sha256 = _exclusive_publish_at(
            snapshot.control,
            PAIR_CLAIM_FILENAME,
            claim,
            post_link_check=validate_post_link_inventory,
            lock_held=True,
        )
        token = PairClaimToken(
            snapshot.paths, authorization, destination, claim_sha256,
            str(payload["primary_attempt_id"]), str(payload["repeat_attempt_id"]),
            os.getpid(), token_capability,
            (snapshot.primary.identity, snapshot.repeat.identity, snapshot.control.identity),
            snapshot,
        )
        _ACTIVE_CLAIMS[destination] = token.capability
        return token


def claim_screening_pair(capability: PreparedPairCapability) -> PairClaimToken:
    """Consume an opaque, one-use capability issued after full preparation."""

    nonce = getattr(capability, "_nonce", None)
    if not isinstance(nonce, str):
        raise ClaimError("invalid prepared-pair capability")
    state = _PREPARED_PAIR_CAPABILITIES.pop(nonce, None)
    if state is None:
        raise ClaimError("invalid or consumed prepared-pair capability")
    try:
        return _claim_screening_pair(state)
    except BaseException:
        state.snapshot.close()
        raise


def _issue_prepared_pair_capability(
    authorization: ScreeningAuthorization, snapshot: RootSnapshot,
) -> PreparedPairCapability:
    nonce = secrets.token_hex(32)
    _PREPARED_PAIR_CAPABILITIES[nonce] = _PreparedPairState(authorization, snapshot)
    return PreparedPairCapability(_CAPABILITY_CONSTRUCTOR_KEY, nonce)


def _prepare(
    *, paths: ScreeningV2Paths, authorization: Path | None,
    trust_verifier: TrustVerifier | None,
    frozen_v1_verifier: Callable[[], str] | None,
    preflight: Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None,
    post_trust_preclaim: (
        Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None
    ),
    fixture_mode: bool,
) -> PairClaimToken:
    if authorization is None:
        raise AuthorizationError("screening authorization is required")
    if trust_verifier is None:
        raise AuthorizationError("configured production trust verifier is required")
    is_fixture_verifier = isinstance(
        trust_verifier, TestOnlyFixtureTrustVerifier
    )
    if is_fixture_verifier != fixture_mode:
        if is_fixture_verifier:
            raise AuthorizationError("test-only trust verifier is production-inaccessible")
        raise AuthorizationError("fixture API requires an explicit test-only verifier")
    if frozen_v1_verifier is None:
        raise AuthorizationError("complete frozen v1 authority verifier is required")
    if preflight is None:
        raise AuthorizationError("authorization preflight verifier is required")
    _validate_path_names(paths)
    if not fixture_mode:
        _validate_production_paths(paths)
    verified = _verify_envelope(Path(authorization))
    expected_v1 = verified.payload["frozen_v1_authority_digest"]
    try:
        first_v1 = frozen_v1_verifier()
    except Exception as error:
        raise AuthorizationError("frozen v1 authority verification failed") from error
    if first_v1 != expected_v1:
        raise AuthorizationError("frozen v1 authority digest mismatch")
    try:
        preflight(verified.payload, paths)
    except Exception as error:
        raise AuthorizationError("authorization preflight failed") from error
    snapshot = (
        scan_v2_roots_for_test(paths) if fixture_mode else scan_v2_roots(paths)
    )
    try:
        try:
            second_v1 = frozen_v1_verifier()
        except Exception as error:
            raise AuthorizationError("frozen v1 authority recheck failed") from error
        if second_v1 != expected_v1 or second_v1 != first_v1:
            raise AuthorizationError("frozen v1 authority drift detected")
        signed_payload = _canonical_json_bytes(verified.payload)
        try:
            trust_accepted = trust_verifier.verify(
                verified.envelope["trust_evidence"], signed_payload
            )
        except Exception as error:
            raise AuthorizationError("trust verifier failed") from error
        if not trust_accepted:
            raise AuthorizationError("configured trust verifier rejected authorization")
        try:
            final_v1 = frozen_v1_verifier()
        except Exception as error:
            raise AuthorizationError(
                "frozen v1 authority final recheck failed"
            ) from error
        if final_v1 != expected_v1 or final_v1 != second_v1:
            raise AuthorizationError(
                "frozen v1 authority drift after trust verification"
            )
        _require_unchanged(verified.artifact_file_snapshot)
        if post_trust_preclaim is not None:
            try:
                post_trust_preclaim(deepcopy(dict(verified.payload)), paths)
            except Exception as error:
                raise AuthorizationError(
                    "post-trust preclaim verification failed"
                ) from error
            try:
                post_callback_v1 = frozen_v1_verifier()
            except Exception as error:
                raise AuthorizationError(
                    "frozen v1 authority post-preclaim recheck failed"
                ) from error
            if post_callback_v1 != expected_v1 or post_callback_v1 != final_v1:
                raise AuthorizationError(
                    "frozen v1 authority drift during post-trust preclaim"
                )
            _require_unchanged(verified.artifact_file_snapshot)
        capability = _issue_prepared_pair_capability(verified, snapshot)
        return claim_screening_pair(capability)
    except BaseException:
        snapshot.close()
        raise


def prepare_screening_pair(
    *, paths: ScreeningV2Paths, authorization: Path | None,
    scientific_runner: Callable[[], Any], trust_verifier: TrustVerifier | None = None,
    frozen_v1_verifier: Callable[[], str] | None = None,
    preflight: Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None = None,
    post_trust_preclaim: (
        Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None
    ) = None,
) -> PairClaimToken:
    """Production preparation boundary; it never invokes the scientific runner."""

    del scientific_runner
    return _prepare(
        paths=paths, authorization=authorization, trust_verifier=trust_verifier,
        frozen_v1_verifier=frozen_v1_verifier, preflight=preflight,
        post_trust_preclaim=post_trust_preclaim,
        fixture_mode=False,
    )


def prepare_screening_pair_for_test(
    *, paths: ScreeningV2Paths, authorization: Path,
    fixture_trust_verifier: TestOnlyFixtureTrustVerifier,
    frozen_v1_verifier: Callable[[], str],
    preflight: Callable[[Mapping[str, Any], ScreeningV2Paths], None],
    scientific_runner: Callable[[], Any],
    post_trust_preclaim: (
        Callable[[Mapping[str, Any], ScreeningV2Paths], None] | None
    ) = None,
) -> PairClaimToken:
    """Explicit test-only authorization path; production cannot select it."""

    del scientific_runner
    return _prepare(
        paths=paths, authorization=authorization,
        trust_verifier=fixture_trust_verifier,
        frozen_v1_verifier=frozen_v1_verifier, preflight=preflight,
        post_trust_preclaim=post_trust_preclaim,
        fixture_mode=True,
    )


def _root_for_role(paths: ScreeningV2Paths, role: str) -> Path:
    if role == "primary":
        return paths.primary
    if role == "repeat":
        return paths.repeat
    raise ClaimError("role must be primary or repeat")


def _read_governance_record(path: Path, schema: str) -> tuple[Mapping[str, Any], str]:
    try:
        snapshot = _stable_read(path)
    except AuthorizationError as error:
        raise ClaimError(f"missing or unstable {schema} record: {path}") from error
    value = _parse_json(snapshot.content)
    try:
        validate_schema(schema, value)
    except Exception as error:
        raise ClaimError(f"invalid {schema} record: {error}") from error
    return value, hashlib.sha256(snapshot.content).hexdigest()


def _read_governance_record_at(
    directory: DirectorySnapshot,
    name: str,
    schema: str,
    *,
    lock_held: bool = False,
) -> tuple[Mapping[str, Any], str]:
    if not lock_held:
        with _locked_directories((directory,), exclusive=False):
            return _read_governance_record_at(
                directory, name, schema, lock_held=True
            )
    _require_directory_binding(directory)
    try:
        content, _ = _stable_directory_file(directory.descriptor, name)
    except ClaimError as error:
        raise ClaimError(f"missing or unstable {schema} record: {name}") from error
    value = _parse_json(content)
    try:
        validate_schema(schema, value)
    except Exception as error:
        raise ClaimError(f"invalid {schema} record: {error}") from error
    _require_directory_binding(directory)
    return value, hashlib.sha256(content).hexdigest()


def _require_role_start_bindings(
    record: Mapping[str, Any],
    *,
    role: str,
    decision_id: str,
    attempt_id: str,
    pair_claim_sha256: str,
) -> None:
    expected = {
        "role": role,
        "decision_id": decision_id,
        "attempt_id": attempt_id,
        "pair_claim_sha256": pair_claim_sha256,
    }
    for field_name, expected_value in expected.items():
        if record[field_name] != expected_value:
            raise ClaimError(f"role start {field_name} binding changed")


def _require_terminal_bindings(
    record: Mapping[str, Any],
    *,
    role: str,
    decision_id: str,
    attempt_id: str,
    pair_claim_sha256: str,
    role_start_sha256: str,
    started_at: str,
) -> None:
    expected = {
        "role": role,
        "decision_id": decision_id,
        "attempt_id": attempt_id,
        "pair_claim_sha256": pair_claim_sha256,
        "role_start_sha256": role_start_sha256,
        "started_at": started_at,
    }
    for field_name, expected_value in expected.items():
        if record[field_name] != expected_value:
            raise ClaimError(f"terminal {field_name} binding changed")


def _require_terminal_semantics(record: Mapping[str, Any]) -> None:
    status = record["status"]
    if status not in {"PASS", "FAIL", "INCOMPLETE"}:
        raise ClaimError("terminal status must be PASS, FAIL, or INCOMPLETE")
    hashes = tuple(
        record[field_name]
        for field_name in (
            "replication_sha256",
            "summary_sha256",
            "result_sha256",
            "diagnostics_sha256",
            "resources_sha256",
            "row_journal_sha256",
        )
    )
    if status == "PASS" and (
        any(value is None for value in hashes)
        or record["exit_code"] != 0
        or record["failure_code"] is not None
        or record["failure_reason"] is not None
    ):
        raise ClaimError("PASS terminal requires complete hashes and clean exit")
    if status == "INCOMPLETE" and any(value is not None for value in hashes):
        raise ClaimError("INCOMPLETE terminal cannot claim complete output hashes")


def _snapshot_for_role(claim: PairClaimToken, role: str) -> DirectorySnapshot:
    if role == "primary":
        return claim.root_snapshot.primary
    if role == "repeat":
        return claim.root_snapshot.repeat
    raise ClaimError("role must be primary or repeat")


def _require_original_supervisor(claim: PairClaimToken) -> None:
    if claim.supervisor_pid != os.getpid():
        raise ClaimError("only the original supervisor may advance the pair")
    if _ACTIVE_CLAIMS.get(claim.claim_path) != claim.capability:
        raise ClaimError("original supervisor capability is unavailable")
    record, digest = _read_governance_record_at(
        claim.root_snapshot.control, PAIR_CLAIM_FILENAME, "pair_claim"
    )
    if digest != claim.pair_claim_sha256:
        raise ClaimError("pair claim digest changed")
    if record["decision_id"] != claim.authorization.decision_id:
        raise ClaimError("pair claim decision binding changed")
    for root in (
        claim.root_snapshot.primary,
        claim.root_snapshot.repeat,
        claim.root_snapshot.control,
    ):
        _require_directory_binding(root)


def start_screening_role(claim: PairClaimToken, role: str) -> AttemptToken:
    """Exclusively publish one role start under the original supervisor."""

    _require_original_supervisor(claim)
    role_snapshot = _snapshot_for_role(claim, role)
    attempt_id = (
        claim.primary_attempt_id if role == "primary" else claim.repeat_attempt_id
    )
    started_at = _iso_now()
    start = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["role_start"],
        "decision_id": claim.authorization.decision_id,
        "attempt_id": attempt_id,
        "role": role,
        "pair_claim_sha256": claim.pair_claim_sha256,
        "started_at": started_at,
        "worker_pid": os.getpid(),
        "hostname": socket.gethostname(),
        "status": "STARTED",
    }
    try:
        validate_schema("role_start", start)
    except Exception as error:
        raise ClaimError(f"role start schema violation: {error}") from error
    destination = _root_for_role(claim.paths, role) / ROLE_START_FILENAMES[role]
    roots = (
        claim.root_snapshot.primary,
        claim.root_snapshot.repeat,
        claim.root_snapshot.control,
    )
    if role == "primary":
        allowed = (
            frozenset((*PRIMARY_CONSTRUCTION_NAMES, ROLE_START_FILENAMES[role])),
            frozenset(),
            frozenset(
                (PAIR_CLAIM_FILENAME, ROLE_CONTROL_START_FILENAMES[role])
            ),
        )
    else:
        allowed = (
            frozenset(
                (
                    *PRIMARY_CONSTRUCTION_NAMES,
                    ROLE_START_FILENAMES["primary"],
                    ROLE_TERMINAL_FILENAMES["primary"],
                    *_ROLE_OUTPUT_FILENAMES,
                )
            ),
            frozenset((ROLE_START_FILENAMES[role],)),
            frozenset(
                (
                    PAIR_CLAIM_FILENAME,
                    ROLE_CONTROL_START_FILENAMES["primary"],
                    ROLE_CONTROL_TERMINAL_FILENAMES["primary"],
                    ROLE_CONTROL_START_FILENAMES[role],
                )
            ),
        )
    with _locked_directories(roots, exclusive=True):
        for root, names in zip(roots, allowed):
            _rescan_directory(root, names, lock_held=True)
        if role == "repeat":
            try:
                pair_record, pair_digest = _read_governance_record_at(
                    claim.root_snapshot.control,
                    PAIR_CLAIM_FILENAME,
                    "pair_claim",
                    lock_held=True,
                )
                primary_terminal, primary_terminal_digest = (
                    _read_governance_record_at(
                        claim.root_snapshot.primary,
                        ROLE_TERMINAL_FILENAMES["primary"],
                        "terminal",
                        lock_held=True,
                    )
                )
                control_terminal, control_terminal_digest = (
                    _read_governance_record_at(
                        claim.root_snapshot.control,
                        ROLE_CONTROL_TERMINAL_FILENAMES["primary"],
                        "terminal",
                        lock_held=True,
                    )
                )
                primary_start, primary_start_digest = _read_governance_record_at(
                    claim.root_snapshot.primary,
                    ROLE_START_FILENAMES["primary"],
                    "role_start",
                    lock_held=True,
                )
                control_start, control_start_digest = _read_governance_record_at(
                    claim.root_snapshot.control,
                    ROLE_CONTROL_START_FILENAMES["primary"],
                    "role_start",
                    lock_held=True,
                )
            except ClaimError as error:
                raise ClaimError(
                    "repeat requires paired retained primary terminal and start markers"
                ) from error
            if (
                pair_digest != claim.pair_claim_sha256
                or pair_record["decision_id"] != claim.authorization.decision_id
                or pair_record["primary_attempt_id"] != claim.primary_attempt_id
                or pair_record["repeat_attempt_id"] != claim.repeat_attempt_id
            ):
                raise ClaimError("retained pair claim binding changed")
            if (
                primary_terminal_digest != control_terminal_digest
                or primary_terminal != control_terminal
            ):
                raise ClaimError("primary role/control terminal records differ")
            if (
                primary_start_digest != control_start_digest
                or primary_start != control_start
            ):
                raise ClaimError("primary role/control start records differ")
            _require_role_start_bindings(
                primary_start,
                role="primary",
                decision_id=claim.authorization.decision_id,
                attempt_id=claim.primary_attempt_id,
                pair_claim_sha256=claim.pair_claim_sha256,
            )
            _require_terminal_bindings(
                primary_terminal,
                role="primary",
                decision_id=claim.authorization.decision_id,
                attempt_id=claim.primary_attempt_id,
                pair_claim_sha256=claim.pair_claim_sha256,
                role_start_sha256=primary_start_digest,
                started_at=str(primary_start["started_at"]),
            )
            _require_terminal_semantics(primary_terminal)
        digest = _exclusive_publish_at(
            claim.root_snapshot.control,
            ROLE_CONTROL_START_FILENAMES[role],
            start,
            lock_held=True,
        )
        role_digest = _exclusive_publish_at(
            role_snapshot,
            ROLE_START_FILENAMES[role],
            start,
            lock_held=True,
        )
    if role_digest != digest:
        raise ClaimError("control and role start digests differ")
    return AttemptToken(claim, role, attempt_id, destination, digest, started_at)


def _require_active_attempt(attempt: AttemptToken) -> None:
    _require_original_supervisor(attempt.claim)
    marker, marker_digest = _read_governance_record_at(
        attempt.claim.root_snapshot.control,
        ROLE_CONTROL_START_FILENAMES[attempt.role],
        "role_start",
    )
    record, digest = _read_governance_record_at(
        _snapshot_for_role(attempt.claim, attempt.role),
        ROLE_START_FILENAMES[attempt.role],
        "role_start",
    )
    if (
        digest != attempt.role_start_sha256
        or marker_digest != attempt.role_start_sha256
        or marker != record
    ):
        raise ClaimError("role start digest changed")
    if record["attempt_id"] != attempt.attempt_id or record["role"] != attempt.role:
        raise ClaimError("role start identity binding changed")


def publish_terminal(
    attempt: AttemptToken,
    *,
    status: str,
    replication_sha256: str | None,
    summary_sha256: str | None,
    result_sha256: str | None,
    diagnostics_sha256: str | None,
    resources_sha256: str | None,
    row_journal_sha256: str | None,
    exit_code: int | None,
    failure_code: str | None,
    failure_reason: str | None,
) -> TerminalToken:
    """Publish one immutable terminal; no replacement or cleanup is available."""

    _require_active_attempt(attempt)
    terminal = {
        "schema_version": SCHEMA_VERSION,
        "document_type": DOCUMENT_TYPES["terminal"],
        "decision_id": attempt.claim.authorization.decision_id,
        "attempt_id": attempt.attempt_id,
        "role": attempt.role,
        "status": status,
        "pair_claim_sha256": attempt.claim.pair_claim_sha256,
        "role_start_sha256": attempt.role_start_sha256,
        "replication_sha256": replication_sha256,
        "summary_sha256": summary_sha256,
        "result_sha256": result_sha256,
        "diagnostics_sha256": diagnostics_sha256,
        "resources_sha256": resources_sha256,
        "row_journal_sha256": row_journal_sha256,
        "started_at": attempt.started_at,
        "finished_at": _iso_now(),
        "exit_code": exit_code,
        "failure_code": failure_code,
        "failure_reason": failure_reason,
    }
    _require_terminal_semantics(terminal)
    try:
        validate_schema("terminal", terminal)
    except Exception as error:
        raise ClaimError(f"terminal schema violation: {error}") from error
    destination = _root_for_role(attempt.claim.paths, attempt.role) / (
        ROLE_TERMINAL_FILENAMES[attempt.role]
    )
    roots = (
        attempt.claim.root_snapshot.primary,
        attempt.claim.root_snapshot.repeat,
        attempt.claim.root_snapshot.control,
    )
    primary_allowed = frozenset(
        (
            *PRIMARY_CONSTRUCTION_NAMES,
            ROLE_START_FILENAMES["primary"],
            ROLE_TERMINAL_FILENAMES["primary"],
            *_ROLE_OUTPUT_FILENAMES,
        )
    )
    if attempt.role == "primary":
        allowed = (
            primary_allowed,
            frozenset(),
            frozenset(
                (
                    PAIR_CLAIM_FILENAME,
                    ROLE_CONTROL_START_FILENAMES["primary"],
                    ROLE_CONTROL_TERMINAL_FILENAMES["primary"],
                )
            ),
        )
    else:
        allowed = (
            primary_allowed,
            frozenset(
                (
                    ROLE_START_FILENAMES["repeat"],
                    ROLE_TERMINAL_FILENAMES["repeat"],
                    *_ROLE_OUTPUT_FILENAMES,
                )
            ),
            frozenset(
                (
                    PAIR_CLAIM_FILENAME,
                    ROLE_CONTROL_START_FILENAMES["primary"],
                    ROLE_CONTROL_TERMINAL_FILENAMES["primary"],
                    ROLE_CONTROL_START_FILENAMES["repeat"],
                    ROLE_CONTROL_TERMINAL_FILENAMES["repeat"],
                )
            ),
        )
    with _locked_directories(roots, exclusive=True):
        for root, names in zip(roots, allowed):
            _rescan_directory(root, names, lock_held=True)
        control_digest = _exclusive_publish_at(
            attempt.claim.root_snapshot.control,
            ROLE_CONTROL_TERMINAL_FILENAMES[attempt.role],
            terminal,
            lock_held=True,
        )
        digest = _exclusive_publish_at(
            _snapshot_for_role(attempt.claim, attempt.role),
            ROLE_TERMINAL_FILENAMES[attempt.role],
            terminal,
            lock_held=True,
        )
    if digest != control_digest:
        raise ClaimError("control and role terminal digests differ")
    return TerminalToken(attempt, destination, status, digest)


def publish_incomplete_terminal(
    attempt: AttemptToken, *, exit_code: int | None,
    failure_code: str, failure_reason: str,
) -> TerminalToken:
    """Ledger-side live-supervisor response to an unclean child death."""

    return publish_terminal(
        attempt, status="INCOMPLETE", replication_sha256=None,
        summary_sha256=None, result_sha256=None, diagnostics_sha256=None,
        resources_sha256=None, row_journal_sha256=None, exit_code=exit_code,
        failure_code=failure_code, failure_reason=failure_reason,
    )


def derive_attempt_state(paths: ScreeningV2Paths, role: str) -> str:
    """Derive retained state; a start without terminal is permanently incomplete."""

    root = _root_for_role(paths, role)
    claim_path = paths.control / PAIR_CLAIM_FILENAME
    if not claim_path.exists():
        return "UNCLAIMED"
    pair_claim, pair_claim_digest = _read_governance_record(
        claim_path, "pair_claim"
    )
    terminal_path = root / ROLE_TERMINAL_FILENAMES[role]
    control_terminal_path = paths.control / ROLE_CONTROL_TERMINAL_FILENAMES[role]
    control_start_path = paths.control / ROLE_CONTROL_START_FILENAMES[role]
    start_path = root / ROLE_START_FILENAMES[role]
    terminal_exists = terminal_path.exists()
    control_terminal_exists = control_terminal_path.exists()
    if terminal_exists or control_terminal_exists:
        if not terminal_exists or not control_terminal_exists:
            raise ClaimError("terminal requires paired role/control markers")
        terminal, terminal_digest = _read_governance_record(
            terminal_path, "terminal"
        )
        control_terminal, control_terminal_digest = _read_governance_record(
            control_terminal_path, "terminal"
        )
        if (
            terminal_digest != control_terminal_digest
            or terminal != control_terminal
        ):
            raise ClaimError("role/control terminal records differ")
        if not start_path.exists() or not control_start_path.exists():
            raise ClaimError("terminal requires paired retained role start markers")
        start, start_digest = _read_governance_record(start_path, "role_start")
        control_start, control_start_digest = _read_governance_record(
            control_start_path, "role_start"
        )
        if start_digest != control_start_digest or start != control_start:
            raise ClaimError("role/control start records differ")
        _require_role_start_bindings(
            start,
            role=role,
            decision_id=str(pair_claim["decision_id"]),
            attempt_id=str(pair_claim[f"{role}_attempt_id"]),
            pair_claim_sha256=pair_claim_digest,
        )
        _require_terminal_bindings(
            terminal,
            role=role,
            decision_id=str(pair_claim["decision_id"]),
            attempt_id=str(pair_claim[f"{role}_attempt_id"]),
            pair_claim_sha256=pair_claim_digest,
            role_start_sha256=start_digest,
            started_at=str(start["started_at"]),
        )
        _require_terminal_semantics(terminal)
        return str(terminal["status"])
    if control_start_path.exists():
        start, control_digest = _read_governance_record(
            control_start_path, "role_start"
        )
        _require_role_start_bindings(
            start,
            role=role,
            decision_id=str(pair_claim["decision_id"]),
            attempt_id=str(pair_claim[f"{role}_attempt_id"]),
            pair_claim_sha256=pair_claim_digest,
        )
        if start_path.exists():
            role_start, role_digest = _read_governance_record(start_path, "role_start")
            if role_start != start or role_digest != control_digest:
                raise ClaimError("control and role start records differ")
        return "INCOMPLETE"
    if start_path.exists():
        raise ClaimError("role start exists without durable control marker")
    return "CLAIMED"
