#!/usr/bin/env python3
"""Read-only preflight for candidate RCEP helper checkouts.

The auditor never imports candidate modules and cannot create a production trust
manifest. It records identity and static-contract evidence for author review.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
REQUIRED_FILES = (
    "research_data_construction.py",
    "research_network_tvp_var.py",
    "config.py",
)
DATA_REQUIRED_BINDINGS = (
    "RCEP_LIST",
    "build_tariff_relief_tc",
    "chow_lin_quarterly_vax",
    "load_quarterly_macro_and_bilateral",
    "quality_control_missing",
    "quality_control_outliers",
)
NETWORK_REQUIRED_CALLABLES = (
    "girf_one",
    "moving_average_coefficients",
)

_ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?P<quote>['\"])/(?:Users|home|Volumes|private|tmp|var)/[^'\"]+(?P=quote)"),
    re.compile(r"(?P<quote>['\"])[A-Za-z]:\\\\[^'\"]+(?P=quote)"),
)
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|secret|password|private[_-]?key)\b\s*=\s*['\"][^'\"]+['\"]"
)
_PRIVATE_KEY_HEADER = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo: Path, *args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        output = getattr(exc, "stderr", "") or getattr(exc, "stdout", "") or str(exc)
        return False, output.strip()
    return True, result.stdout.strip()


def bound_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def callable_names(tree: ast.Module) -> set[str]:
    names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def local_imports(tree: ast.Module, source: Path, repo: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [(alias.name, 0) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [(node.module or "", node.level)]
        else:
            continue
        for module, level in modules:
            root = module.split(".")[0] if module else ""
            candidates: list[Path] = []
            if level:
                base = source.parent
                for _ in range(max(0, level - 1)):
                    base = base.parent
                if module:
                    candidates.extend((base / f"{module.replace('.', '/')}.py", base / module.replace(".", "/") / "__init__.py"))
                else:
                    candidates.append(base / "__init__.py")
            elif root:
                candidates.extend((repo / f"{root}.py", repo / root / "__init__.py"))
            dependency = next((item for item in candidates if item.is_file()), None)
            if dependency is not None:
                findings.append(
                    {
                        "source_file": source.name,
                        "line": node.lineno,
                        "module": ("." * level) + module,
                        "dependency_file": str(dependency.resolve()),
                        "bound_by_current_manifest": dependency.name in REQUIRED_FILES,
                    }
                )
    return findings


def call_name(node: ast.Call) -> str:
    current: ast.AST = node.func
    parts: list[str] = []
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def static_scan(path: Path, repo: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    absolute_paths: list[dict[str, Any]] = []
    credentials: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in _ABSOLUTE_PATH_PATTERNS):
            absolute_paths.append({"file": path.name, "line": line_no, "kind": "absolute_path_literal"})
        if _CREDENTIAL_ASSIGNMENT.search(line):
            credentials.append({"file": path.name, "line": line_no, "kind": "credential_assignment"})
        if _PRIVATE_KEY_HEADER.search(line):
            credentials.append({"file": path.name, "line": line_no, "kind": "private_key_material"})
    top_level_calls: list[dict[str, Any]] = []
    top_level_side_effects: list[dict[str, Any]] = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            item = {"file": path.name, "line": node.lineno, "call": name or "<dynamic>"}
            top_level_calls.append(item)
            terminal_name = name.rsplit(".", 1)[-1]
            if terminal_name in {"mkdir", "write_text", "write_bytes", "touch", "unlink", "rename", "replace"}:
                top_level_side_effects.append(item)
            elif name in {"open", "os.mkdir", "os.makedirs", "sys.path.insert", "sys.path.append"}:
                top_level_side_effects.append(item)
    return {
        "syntax_valid": True,
        "bound_names": sorted(bound_names(tree)),
        "callable_names": sorted(callable_names(tree)),
        "local_imports": local_imports(tree, path, repo),
        "absolute_path_indicators": absolute_paths,
        "credential_indicators": credentials,
        "top_level_calls": sorted(top_level_calls, key=lambda item: (item["line"], item["call"])),
        "top_level_side_effect_indicators": sorted(
            top_level_side_effects, key=lambda item: (item["line"], item["call"])
        ),
    }


def discover_governance_files(repo: Path) -> dict[str, list[str]]:
    top_level_files = [item for item in repo.iterdir() if item.is_file() and not item.is_symlink()]
    return {
        "license_files": sorted(item.name for item in top_level_files if item.name.lower().startswith(("license", "copying", "notice"))),
        "readme_files": sorted(item.name for item in top_level_files if item.name.lower().startswith("readme")),
    }


def audit_dependency_closure(
    repo: Path, initial_imports: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_paths = {(repo / name).resolve() for name in REQUIRED_FILES}
    queue = [Path(item["dependency_file"]) for item in initial_imports]
    audited: dict[Path, dict[str, Any]] = {}
    import_edges: list[dict[str, Any]] = list(initial_imports)
    while queue:
        dependency = queue.pop(0).resolve()
        if dependency in manifest_paths or dependency in audited:
            continue
        info: dict[str, Any] = {
            "dependency_file": str(dependency),
            "relative_path": str(dependency.relative_to(repo)),
            "exists_as_file": dependency.is_file(),
            "is_symlink": dependency.is_symlink(),
        }
        if dependency.is_file() and not dependency.is_symlink():
            info["sha256"] = sha256_file(dependency)
            tracked_ok, _ = run_git(repo, "ls-files", "--error-unmatch", "--", info["relative_path"])
            status_ok, status = run_git(repo, "status", "--porcelain=v1", "--", info["relative_path"])
            info["git_tracked"] = tracked_ok
            info["git_status"] = status if status_ok else None
            try:
                scan = static_scan(dependency, repo)
            except (OSError, UnicodeError, SyntaxError) as exc:
                info["syntax_valid"] = False
                info["scan_error"] = f"{type(exc).__name__}: {exc}"
            else:
                info["syntax_valid"] = True
                info["local_imports"] = scan["local_imports"]
                info["absolute_path_indicators"] = scan["absolute_path_indicators"]
                info["credential_indicators"] = scan["credential_indicators"]
                info["top_level_side_effect_indicators"] = scan["top_level_side_effect_indicators"]
                import_edges.extend(scan["local_imports"])
                queue.extend(Path(item["dependency_file"]) for item in scan["local_imports"])
        audited[dependency] = info
    unique_edges = {
        (item["source_file"], item["line"], item["module"], item["dependency_file"]): item
        for item in import_edges
    }
    return list(audited.values()), list(unique_edges.values())


def audit_candidate(candidate_id: str, candidate_path: Path) -> dict[str, Any]:
    supplied_path = candidate_path.expanduser()
    result: dict[str, Any] = {
        "candidate_id": candidate_id,
        "supplied_path": str(supplied_path),
        "path_is_symlink": supplied_path.is_symlink(),
        "path_is_directory": supplied_path.is_dir(),
        "production_trust_granted": False,
    }
    failures: list[str] = []
    warnings: list[str] = []
    if result["path_is_symlink"] or not result["path_is_directory"]:
        failures.append("candidate_path_is_not_a_non_symlink_directory")
        result.update({"preflight_status": "FAIL", "failures": failures, "warnings": warnings})
        return result

    repo = supplied_path.resolve()
    result["resolved_path"] = str(repo)
    git_ok, git_root = run_git(repo, "rev-parse", "--show-toplevel")
    commit_ok, commit = run_git(repo, "rev-parse", "HEAD")
    status_ok, dirty = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    dirty_entries = dirty.splitlines() if status_ok and dirty else []
    result["git"] = {
        "is_repository": git_ok and commit_ok,
        "root": git_root if git_ok else None,
        "head_commit": commit if commit_ok else None,
        "status_readable": status_ok,
        "worktree_clean": status_ok and not dirty,
        "dirty_entry_count": len(dirty_entries),
        "dirty_status_sha256": hashlib.sha256(dirty.encode("utf-8")).hexdigest() if status_ok else None,
        "dirty_entries_sample": dirty_entries[:100],
        "dirty_entries_truncated": len(dirty_entries) > 100,
    }
    if not (git_ok and commit_ok):
        failures.append("git_identity_unavailable")
    if not status_ok:
        warnings.append("git_worktree_status_unavailable")
    elif dirty:
        warnings.append("git_worktree_is_dirty")

    files: dict[str, Any] = {}
    local_dependencies: list[dict[str, Any]] = []
    absolute_path_indicators: list[dict[str, Any]] = []
    credential_indicators: list[dict[str, Any]] = []
    import_time_side_effect_indicators: list[dict[str, Any]] = []
    for name in REQUIRED_FILES:
        source = repo / name
        file_info: dict[str, Any] = {
            "exists_as_file": source.is_file(),
            "is_symlink": source.is_symlink(),
        }
        if source.is_file() and not source.is_symlink():
            file_info["sha256"] = sha256_file(source)
            file_info["size_bytes"] = source.stat().st_size
            tracked_ok, _ = run_git(repo, "ls-files", "--error-unmatch", "--", name)
            file_info["git_tracked"] = tracked_ok
            if not tracked_ok:
                failures.append(f"required_file_not_git_tracked:{name}")
            status_ok, file_status = run_git(repo, "status", "--porcelain=v1", "--", name)
            file_info["git_status"] = file_status if status_ok else None
            if not status_ok:
                failures.append(f"required_file_git_status_unavailable:{name}")
            elif file_status:
                failures.append(f"required_file_differs_from_head:{name}")
            try:
                scan = static_scan(source, repo)
            except (OSError, UnicodeError, SyntaxError) as exc:
                file_info["syntax_valid"] = False
                file_info["scan_error"] = f"{type(exc).__name__}: {exc}"
                failures.append(f"required_file_static_scan_failed:{name}")
            else:
                file_info.update(scan)
                local_dependencies.extend(scan["local_imports"])
                absolute_path_indicators.extend(scan["absolute_path_indicators"])
                credential_indicators.extend(scan["credential_indicators"])
                import_time_side_effect_indicators.extend(scan["top_level_side_effect_indicators"])
        else:
            failures.append(f"required_file_missing_or_symlink:{name}")
        files[name] = file_info
    result["files"] = files

    data_names = set(files.get(REQUIRED_FILES[0], {}).get("bound_names", []))
    network_callables = set(files.get(REQUIRED_FILES[1], {}).get("callable_names", []))
    missing_data = sorted(set(DATA_REQUIRED_BINDINGS) - data_names)
    missing_network = sorted(set(NETWORK_REQUIRED_CALLABLES) - network_callables)
    result["api_contract"] = {
        "required_data_bindings": list(DATA_REQUIRED_BINDINGS),
        "required_network_callables": list(NETWORK_REQUIRED_CALLABLES),
        "missing_data_bindings": missing_data,
        "missing_network_callables": missing_network,
        "static_contract_pass": not missing_data and not missing_network,
    }
    if missing_data or missing_network:
        failures.append("required_api_static_contract_failed")

    closure_files, all_import_edges = audit_dependency_closure(repo, local_dependencies)
    unbound_dependencies_by_path = {
        item["dependency_file"]: item
        for item in all_import_edges
        if not item["bound_by_current_manifest"]
    }
    unbound_dependencies = list(unbound_dependencies_by_path.values())
    result["dependency_scan"] = {
        "local_imports": all_import_edges,
        "unbound_local_dependencies": unbound_dependencies,
        "unbound_dependency_files": closure_files,
    }
    if unbound_dependencies:
        failures.append("local_import_dependency_not_bound_by_current_manifest")
    if any(not item.get("git_tracked") for item in closure_files):
        failures.append("unbound_dependency_not_git_tracked")
    if any(not item.get("syntax_valid") for item in closure_files):
        failures.append("unbound_dependency_static_scan_failed")

    dependency_absolute_paths = [
        finding
        for item in closure_files
        for finding in item.get("absolute_path_indicators", [])
    ]
    dependency_credentials = [
        finding for item in closure_files for finding in item.get("credential_indicators", [])
    ]
    dependency_side_effects = [
        finding
        for item in closure_files
        for finding in item.get("top_level_side_effect_indicators", [])
    ]
    result["safety_scan"] = {
        "absolute_path_indicators": absolute_path_indicators,
        "credential_indicators": credential_indicators,
        "import_time_side_effect_indicators": import_time_side_effect_indicators,
        "dependency_absolute_path_indicators": dependency_absolute_paths,
        "dependency_credential_indicators": dependency_credentials,
        "dependency_import_time_side_effect_indicators": dependency_side_effects,
    }
    if absolute_path_indicators:
        warnings.append("hardcoded_absolute_path_indicator_present")
    if credential_indicators:
        failures.append("credential_or_private_key_indicator_present")
    if dependency_absolute_paths:
        warnings.append("dependency_hardcoded_absolute_path_indicator_present")
    if dependency_credentials:
        failures.append("dependency_credential_or_private_key_indicator_present")
    if import_time_side_effect_indicators:
        warnings.append("import_time_side_effect_indicator_present")
    if dependency_side_effects:
        warnings.append("dependency_import_time_side_effect_indicator_present")

    governance = discover_governance_files(repo)
    result["governance_files"] = governance
    if not governance["license_files"]:
        warnings.append("no_top_level_license_file")
    if not governance["readme_files"]:
        warnings.append("no_top_level_readme_file")

    result["failures"] = sorted(set(failures))
    result["warnings"] = sorted(set(warnings))
    result["preflight_status"] = "FAIL" if failures else ("WARN" if warnings else "PASS")
    return result


def build_report(candidates: list[tuple[str, Path]]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_date": date.today().isoformat(),
        "audit_type": "read_only_candidate_preflight",
        "contract_source": "scripts/run_cp_empirical_pipeline.py",
        "production_trust_schema_version": 2,
        "candidate_selection_made": False,
        "production_trust_granted": False,
        "scientific_execution_authorized": False,
        "r006e_outcome_authorized": False,
        "r006f_outcome_authorized": False,
        "limitations": [
            "Static AST inspection does not prove runtime correctness or scientific validity.",
            "Secret scanning is pattern-based and cannot establish that a checkout is credential-free.",
            "A candidate preflight cannot substitute for author confirmation of ownership, licence and permitted use.",
        ],
        "candidates": [audit_candidate(candidate_id, path) for candidate_id, path in candidates],
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# RCEP Helper Candidate Preflight",
        "",
        f"**Date:** {report['audit_date']}",
        "",
        "**Decision boundary:** This is a read-only candidate comparison. It does not select a candidate, grant production trust, authorize scientific execution, or open R006e/R006f outcomes.",
        "",
        "| Candidate | Static preflight | Git HEAD | Worktree | API contract | Unbound local dependencies | Licence file |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for candidate in report["candidates"]:
        git = candidate.get("git", {})
        api = candidate.get("api_contract", {})
        dependencies = candidate.get("dependency_scan", {}).get("unbound_local_dependencies", [])
        licences = candidate.get("governance_files", {}).get("license_files", [])
        commit = git.get("head_commit") or "unavailable"
        lines.append(
            "| {id} | {status} | `{commit}` | {clean} | {api} | {deps} | {licence} |".format(
                id=candidate["candidate_id"],
                status=candidate["preflight_status"],
                commit=commit[:12],
                clean="clean" if git.get("worktree_clean") else "dirty/unavailable",
                api="PASS" if api.get("static_contract_pass") else "FAIL",
                deps=len(dependencies),
                licence=", ".join(licences) if licences else "absent",
            )
        )
    for candidate in report["candidates"]:
        lines.extend(
            [
                "",
                f"## {candidate['candidate_id']}",
                "",
                f"- Supplied path: `{candidate['supplied_path']}`",
                f"- Preflight status: **{candidate['preflight_status']}**",
                f"- Failures: {', '.join(candidate.get('failures', [])) or 'none'}",
                f"- Warnings: {', '.join(candidate.get('warnings', [])) or 'none'}",
            ]
        )
        for name, file_info in candidate.get("files", {}).items():
            lines.append(
                f"- `{name}`: sha256 `{file_info.get('sha256', 'unavailable')}`; "
                f"tracked={file_info.get('git_tracked', False)}; symlink={file_info.get('is_symlink', False)}; "
                f"Git status=`{file_info.get('git_status') or 'clean'}`"
            )
        api = candidate.get("api_contract", {})
        lines.append(
            "- Missing required APIs: "
            + (", ".join(api.get("missing_data_bindings", []) + api.get("missing_network_callables", [])) or "none")
        )
        safety = candidate.get("safety_scan", {})
        for dependency in candidate.get("dependency_scan", {}).get("unbound_dependency_files", []):
            status = dependency.get("git_status") or "clean"
            lines.append(
                f"- Unbound `{dependency.get('relative_path', 'unknown')}`: sha256 "
                f"`{dependency.get('sha256', 'unavailable')}`; tracked={dependency.get('git_tracked', False)}; "
                f"Git status=`{status}`"
            )
        lines.append(f"- Absolute-path indicators: {len(safety.get('absolute_path_indicators', []))}")
        lines.append(f"- Credential/private-key indicators: {len(safety.get('credential_indicators', []))}")
        lines.append(f"- Import-time side-effect indicators: {len(safety.get('import_time_side_effect_indicators', []))}")
        lines.append(f"- Dependency credential/private-key indicators: {len(safety.get('dependency_credential_indicators', []))}")
        lines.append(f"- Dependency import-time side-effect indicators: {len(safety.get('dependency_import_time_side_effect_indicators', []))}")
    lines.extend(
        [
            "",
            "## Author Decision Still Required",
            "",
            "No candidate is production-authorized. Before a trust manifest can be drafted, the author must identify one candidate and confirm ownership, licence/permitted use, and whether any private-code dependency may be used for this manuscript rebuild.",
            "",
            "Even after that decision, production execution must remain closed until the selected checkout is clean or its deviations are resolved, every code dependency is hash-bound, and the manifest candidate is reviewed and explicitly signed off.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_candidate(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("candidate must use ID=PATH")
    candidate_id, raw_path = value.split("=", 1)
    if not candidate_id.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("candidate must use non-empty ID=PATH")
    return candidate_id.strip(), Path(raw_path.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", action="append", required=True, type=parse_candidate)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)

    report = build_report(args.candidate)
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
