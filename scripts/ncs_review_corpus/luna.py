"""Run evidence coding through Codex CLI with Luna at max effort."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .core import MODEL_ID, REASONING_EFFORT, sha256_bytes, utc_now


TRANSIENT_FAILURE_MARKERS = (
    "429 too many requests",
    "502 bad gateway",
    "503 service unavailable",
    "504 gateway timeout",
    "504 gateway time-out",
    "connection reset",
    "stream disconnected",
    "temporarily unavailable",
)


def is_transient_failure(stderr: str) -> bool:
    normalized = stderr.lower()
    return any(marker in normalized for marker in TRANSIENT_FAILURE_MARKERS)


def run_luna(
    prompt: str,
    schema: Path,
    cwd: Path,
    timeout: float = 1800.0,
    max_attempts: int = 3,
) -> dict[str, Any]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    with tempfile.TemporaryDirectory(prefix="ncs-luna-") as temporary_dir:
        output_path = Path(temporary_dir) / "result.json"
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--model",
            MODEL_ID,
            "--config",
            f'model_reasoning_effort="{REASONING_EFFORT}"',
            "--sandbox",
            "read-only",
            "--output-schema",
            str(schema.resolve()),
            "--output-last-message",
            str(output_path),
            "-",
        ]
        failures: list[str] = []
        completed: subprocess.CompletedProcess[str] | None = None
        for attempt in range(1, max_attempts + 1):
            output_path.unlink(missing_ok=True)
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                cwd=cwd,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            if completed.returncode == 0:
                break
            failure_tail = completed.stderr[-4000:]
            failures.append(failure_tail)
            if attempt == max_attempts or not is_transient_failure(completed.stderr):
                raise RuntimeError(
                    "Luna CLI failed with exit code "
                    f"{completed.returncode} after {attempt} attempt(s): {failure_tail}"
                )
            time.sleep(min(5 * attempt, 15))
        assert completed is not None
        if not output_path.exists():
            raise RuntimeError("Luna CLI did not write the structured result")
        raw = output_path.read_text(encoding="utf-8")
        result = json.loads(raw)
        return {
            "result": result,
            "metadata": {
                "model": MODEL_ID,
                "reasoning_effort": REASONING_EFFORT,
                "invoked_at": utc_now(),
                "attempt_count": len(failures) + 1,
                "transient_failure_count": len(failures),
                "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                "schema_sha256": sha256_bytes(schema.read_bytes()),
                "stdout_tail": completed.stdout[-2000:],
                "stderr_warnings_present": bool(completed.stderr.strip()),
            },
        }
