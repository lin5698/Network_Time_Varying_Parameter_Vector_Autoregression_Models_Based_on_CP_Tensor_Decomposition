"""No-replacement, source-only materialization of E3 Family-2 artifacts.

This module accepts complete caller-supplied artifact content and writes the
eight semantically validated ``CANDIDATE_READY`` artifacts into a new package
root.
``CANDIDATE_READY`` means schema-complete and hash-verifiable only; it is not
an audit signature, an execution authorization, or evidence of a result.  The
module does not create an execution candidate, approval, output root, or
scientific result, and it intentionally exposes no command-line entrypoint.
Portable filesystem operations cannot simultaneously provide whole-directory
atomic publication and no-replacement semantics here: the new root is created
before staged files are moved into it.  Consumers must therefore validate the
complete package after materialization; no enabled E3 execution route consumes
these artifacts in this source-only build.
"""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from scripts.experiments import e3_family2_artifact_schemas as artifact_schemas


class CandidateReadyArtifactError(RuntimeError):
    """Raised when a candidate-ready artifact package cannot be materialized."""


def _canonical_payload(content_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, bytes]:
    """Validate every artifact before any target-directory write occurs."""

    expected_ids = set(artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS)
    if set(content_by_id) != expected_ids:
        raise CandidateReadyArtifactError(
            "candidate-ready content must supply the complete artifact set"
        )

    payloads: dict[str, bytes] = {}
    for artifact_id in artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        content = content_by_id[artifact_id]
        if not isinstance(content, Mapping):
            raise CandidateReadyArtifactError(
                f"candidate-ready content for {artifact_id} must be an object"
            )
        try:
            artifact = artifact_schemas.build_preoutcome_artifact(
                artifact_id,
                lifecycle=artifact_schemas.CANDIDATE_READY,
                content=content,
            )
        except artifact_schemas.ArtifactValidationError as error:
            raise CandidateReadyArtifactError(
                f"candidate-ready artifact {artifact_id} refused: {error}"
            ) from error
        payloads[artifact_id] = artifact_schemas.canonical_json_bytes(artifact) + b"\n"
    return payloads


def _write_staged_package(staging_root: Path, payloads: Mapping[str, bytes]) -> None:
    for artifact_id in artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS:
        destination = staging_root / artifact_schemas.ARTIFACT_FILENAMES[artifact_id]
        with destination.open("xb") as handle:
            handle.write(payloads[artifact_id])
            handle.flush()
            os.fsync(handle.fileno())


def _path_entry_exists(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def materialize_candidate_ready_artifacts(
    artifact_root: Path,
    *,
    content_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Path]:
    """Write a complete candidate-ready package without replacing a prior root.

    The caller must provide all eight concrete content records.  The target
    root must be new, which prevents this construction helper from silently
    replacing a previously reviewed package.
    """

    payloads = _canonical_payload(content_by_id)
    root = Path(artifact_root).expanduser().resolve(strict=False)
    if _path_entry_exists(root):
        raise CandidateReadyArtifactError("candidate-ready artifact root must be new and absent")
    parent = root.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=f".{root.name}.staging-", dir=parent))
    try:
        _write_staged_package(staging_root, payloads)
        try:
            os.mkdir(root, 0o700)
        except FileExistsError as error:
            raise CandidateReadyArtifactError(
                "candidate-ready artifact root was claimed during construction"
            ) from error
        for artifact_id in artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS:
            filename = artifact_schemas.ARTIFACT_FILENAMES[artifact_id]
            os.replace(staging_root / filename, root / filename)
        staging_root.rmdir()
    except BaseException:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        raise
    return {
        artifact_id: root / artifact_schemas.ARTIFACT_FILENAMES[artifact_id]
        for artifact_id in artifact_schemas.REQUIRED_PREOUTCOME_ARTIFACT_IDS
    }
