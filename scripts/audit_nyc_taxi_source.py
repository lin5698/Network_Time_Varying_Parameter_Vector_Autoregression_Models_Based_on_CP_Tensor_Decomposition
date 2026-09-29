#!/usr/bin/env python3
"""Record fixed-commit provenance for the public NYC Taxi source checkout."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_cp_empirical_pipeline import _validated_nyc_taxi_source


def git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_report(dataset_dir: Path) -> dict[str, Any]:
    taxi_root, commit, file_hashes = _validated_nyc_taxi_source(dataset_dir)
    git_root = Path(git_output(taxi_root, "rev-parse", "--show-toplevel")).resolve()
    try:
        origin = git_output(git_root, "remote", "get-url", "origin")
    except subprocess.CalledProcessError:
        origin = None
    return {
        "schema_version": 1,
        "audit_date": date.today().isoformat(),
        "audit_type": "read_only_public_source_preflight",
        "dataset": "NYC Taxi",
        "source_preflight_status": "PASS",
        "source_repository": "xinychen/vars",
        "origin_url_observed": origin,
        "git_commit": commit,
        "git_worktree_clean": not bool(git_output(git_root, "status", "--porcelain=v1", "--untracked-files=all")),
        "dataset_path": str(taxi_root),
        "dataset_path_within_repository": str(taxi_root.relative_to(git_root)),
        "required_files": [
            {
                "name": name,
                "sha256": digest,
                "size_bytes": (taxi_root / name).stat().st_size,
                "is_symlink": (taxi_root / name).is_symlink(),
            }
            for name, digest in file_hashes
        ],
        "scientific_execution_authorized": False,
        "authorization_boundary": (
            "The public NYC source identity is verified, but the joint RCEP/NYC production run remains closed "
            "until the RCEP helper candidate and schema-v2 trust manifest receive explicit author approval."
        ),
        "r006e_outcome_authorized": False,
        "r006f_outcome_authorized": False,
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# NYC Taxi Fixed-Commit Source Preflight",
        "",
        f"**Date:** {report['audit_date']}",
        "",
        f"**Source preflight:** {report['source_preflight_status']}",
        "",
        f"- Repository: `{report['source_repository']}`",
        f"- Observed origin: `{report['origin_url_observed']}`",
        f"- Commit: `{report['git_commit']}`",
        f"- Dataset path: `{report['dataset_path_within_repository']}`",
        f"- Git worktree clean: `{report['git_worktree_clean']}`",
        "- Scientific execution authorized: `false`",
        "- R006e/R006f outcomes authorized: `false` / `false`",
        "",
        "| File | Size (bytes) | SHA-256 | Symlink |",
        "|---|---:|---|---:|",
    ]
    for item in report["required_files"]:
        lines.append(
            f"| `{item['name']}` | {item['size_bytes']} | `{item['sha256']}` | `{item['is_symlink']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            report["authorization_boundary"],
            "",
            "This preflight verifies source identity and file provenance only. It does not load arrays, construct a panel, validate scientific dimensions, reproduce any archived NYC value or authorize manuscript claims.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)

    report = build_report(args.dataset_dir)
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    rendered_markdown = markdown_report(report)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered_json, encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(rendered_markdown, encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        sys.stdout.write(rendered_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
