"""Record a completed source-only gate-test run without invoking science."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GATE_TEST_MODULES = (
    "scripts.experiments.test_e3_synthetic_core",
    "scripts.experiments.test_e3_family2_preoutcome",
    "scripts.experiments.test_e3_family2_candidate_package",
    "scripts.experiments.test_e3_family2_synthetic_runner",
    "scripts.experiments.test_e3_family2_authorized_executor",
    "scripts.experiments.test_e3_family2_gate_receipt",
)
GATE_TEST_PATHS = tuple(
    ROOT / f"{module.replace('.', '/')}.py" for module in GATE_TEST_MODULES
)
SCHEMA_VERSION = "e4-gate-test-execution-receipt-v1"
_FIELDS = frozenset(
    {
        "schema_version",
        "verdict",
        "command",
        "suite_modules",
        "suite_sha256",
        "recorder",
        "started_at",
        "completed_at",
        "returncode",
        "tests_run",
        "stdout",
        "stderr",
        "stdout_sha256",
        "stderr_sha256",
        "scientific_execution",
    }
)
_RECORDER_FIELDS = frozenset({"path", "sha256"})


class GateReceiptError(RuntimeError):
    """Raised when test execution or its receipt is incomplete."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(Path(path).read_bytes())


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise GateReceiptError(f"{label} is not an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as error:
        raise GateReceiptError(f"{label} is invalid") from error
    return parsed


def _expected_command() -> list[str]:
    return [sys.executable, "-m", "unittest", *GATE_TEST_MODULES]


def _suite_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for module, path in zip(GATE_TEST_MODULES, GATE_TEST_PATHS):
        if not path.is_file():
            raise GateReceiptError(f"gate-test module is missing: {module}")
        result[module] = _sha256_file(path)
    return result


def _recorder_identity() -> dict[str, str]:
    path = Path(__file__).resolve()
    return {"path": str(path.relative_to(ROOT)), "sha256": _sha256_file(path)}


def _extract_test_count(stderr: str) -> int:
    matches = re.findall(r"^Ran ([1-9][0-9]*) tests? in ", stderr, flags=re.MULTILINE)
    if len(matches) != 1:
        raise GateReceiptError("gate-test transcript lacks one unambiguous test count")
    return int(matches[0])


def _validate_mapping(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if set(receipt) != _FIELDS:
        raise GateReceiptError("gate-test execution receipt has an invalid field set")
    if receipt["schema_version"] != SCHEMA_VERSION:
        raise GateReceiptError("gate-test execution receipt schema is invalid")
    if receipt["verdict"] != "PASS" or receipt["returncode"] != 0:
        raise GateReceiptError("gate-test execution receipt does not record a passing run")
    if receipt["scientific_execution"] != "NOT_AUTHORIZED":
        raise GateReceiptError("gate-test execution receipt cannot authorize science")
    if receipt["command"] != _expected_command():
        raise GateReceiptError("gate-test execution command differs from the frozen suite")
    if receipt["suite_modules"] != list(GATE_TEST_MODULES):
        raise GateReceiptError("gate-test module inventory differs from the frozen suite")
    if receipt["suite_sha256"] != _suite_hashes():
        raise GateReceiptError("gate-test suite hashes do not match current sources")
    recorder = receipt["recorder"]
    if not isinstance(recorder, Mapping) or set(recorder) != _RECORDER_FIELDS:
        raise GateReceiptError("gate-test recorder identity has an invalid field set")
    if dict(recorder) != _recorder_identity():
        raise GateReceiptError("gate-test recorder identity does not match current source")
    started = _parse_utc(receipt["started_at"], "gate-test start")
    completed = _parse_utc(receipt["completed_at"], "gate-test completion")
    if completed < started:
        raise GateReceiptError("gate-test completion precedes its start")
    stdout = receipt["stdout"]
    stderr = receipt["stderr"]
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise GateReceiptError("gate-test transcript fields must be strings")
    if receipt["stdout_sha256"] != _sha256_bytes(stdout.encode("utf-8")):
        raise GateReceiptError("gate-test stdout hash is invalid")
    if receipt["stderr_sha256"] != _sha256_bytes(stderr.encode("utf-8")):
        raise GateReceiptError("gate-test stderr hash is invalid")
    tests_run = _extract_test_count(stderr)
    if receipt["tests_run"] != tests_run or not re.search(r"^OK\s*$", stderr, re.MULTILINE):
        raise GateReceiptError("gate-test transcript does not support the PASS verdict")
    return dict(receipt)


def validate_gate_test_receipt(path: Path) -> dict[str, Any]:
    """Validate a no-science test-run receipt against current source hashes."""

    source = Path(path).expanduser().resolve(strict=False)
    if not source.is_file():
        raise GateReceiptError("gate-test execution receipt is missing")
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateReceiptError("gate-test execution receipt is invalid JSON") from error
    if not isinstance(value, Mapping):
        raise GateReceiptError("gate-test execution receipt must be an object")
    return _validate_mapping(value)


def record_gate_test_run(destination: Path) -> dict[str, Any]:
    """Execute the frozen non-scientific suites and write PASS only on success."""

    target = Path(destination).expanduser().resolve(strict=False)
    if target.exists():
        raise GateReceiptError("gate-test execution receipt path must be new and absent")
    command = _expected_command()
    started_at = _utc_now()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    completed_at = _utc_now()
    if completed.returncode != 0:
        raise GateReceiptError("gate-test suite did not pass; no receipt was written")
    tests_run = _extract_test_count(completed.stderr)
    if not re.search(r"^OK\s*$", completed.stderr, re.MULTILINE):
        raise GateReceiptError("gate-test suite did not emit an OK verdict")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "verdict": "PASS",
        "command": command,
        "suite_modules": list(GATE_TEST_MODULES),
        "suite_sha256": _suite_hashes(),
        "recorder": _recorder_identity(),
        "started_at": started_at,
        "completed_at": completed_at,
        "returncode": completed.returncode,
        "tests_run": tests_run,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sha256": _sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": _sha256_bytes(completed.stderr.encode("utf-8")),
        "scientific_execution": "NOT_AUTHORIZED",
    }
    validated = _validate_mapping(receipt)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(validated, sort_keys=True, separators=(",", ":"), allow_nan=False)
    with target.open("x", encoding="utf-8") as handle:
        handle.write(f"{payload}\n")
        handle.flush()
        os.fsync(handle.fileno())
    return validated
