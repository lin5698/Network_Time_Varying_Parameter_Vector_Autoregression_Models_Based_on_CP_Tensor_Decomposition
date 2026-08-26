"""E4-R008 duplicate and claim-fidelity gate for CAL-E01:75 artifacts.

The gate consumes two independently materialized CAL-E01:75 analysis roots.
It does not derive new numerical values, inspect manuscript text, or mutate the
frozen E4-r3 quarantine output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "ncs-e4-r008-duplicate-claim-fidelity-v1"
GATE_ID = "E4-R008"
REGISTER_KEY = "CAL-E01:75"
EVIDENCE_CEILING = "simulation_only; frozen E4-r3 synthetic-only operating cells"
REQUIRED_FILES = (
    "artifact-manifest.json",
    "claim-audit.json",
    "comparator-audit.json",
    "derived-panel-log-error-ratios.json",
    "distributions.json",
    "input-manifest.json",
    "sufficiency-audit.json",
)


class GateError(RuntimeError):
    """Raised when a duplicate or claim-fidelity requirement fails closed."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateError(f"cannot load JSON artifact {path}: {error}") from error


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise GateError(f"{label} must be a JSON object")
    return value


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise GateError(f"artifact root is not a directory: {root}")
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        entries.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return entries


def _inventory_digest(entries: Sequence[Mapping[str, Any]]) -> str:
    return _sha256_bytes(_canonical_json_bytes(list(entries)))


def _validate_manifest(root: Path, entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    manifest = _require_mapping(
        _load_json(root / "artifact-manifest.json"), "artifact manifest"
    )
    if manifest.get("register_key") != REGISTER_KEY:
        raise GateError("artifact manifest register key mismatch")
    if manifest.get("claim_activation") != "BLOCKED":
        raise GateError("artifact manifest must keep claim activation blocked")
    if manifest.get("frozen_result_mutated") is not False:
        raise GateError("artifact manifest must not mutate the frozen result")
    if manifest.get("manuscript_modified") is not False:
        raise GateError("artifact manifest must not modify manuscript sources")
    if manifest.get("author_decision_register_modified") is not False:
        raise GateError("artifact manifest must not modify the author decision register")
    if manifest.get("quarantine_modified") is not False:
        raise GateError("artifact manifest must not modify quarantine artifacts")
    output_sha256 = manifest.get("output_sha256")
    if not isinstance(output_sha256, Mapping):
        raise GateError("artifact manifest output_sha256 is missing")
    observed = {entry["path"]: entry["sha256"] for entry in entries}
    for filename in REQUIRED_FILES:
        if filename == "artifact-manifest.json":
            continue
        expected = output_sha256.get(filename)
        if expected != observed.get(filename):
            raise GateError(f"artifact manifest hash mismatch: {filename}")
    return dict(manifest)


def _validate_claim_fidelity(root: Path) -> list[dict[str, Any]]:
    claim = _require_mapping(_load_json(root / "claim-audit.json"), "claim audit")
    derived = _require_mapping(
        _load_json(root / "derived-panel-log-error-ratios.json"),
        "derived panel log-error-ratio artifact",
    )
    sufficiency = _require_mapping(
        _load_json(root / "sufficiency-audit.json"), "sufficiency audit"
    )
    checks = [
        {
            "name": "claim_activation_blocked",
            "status": "PASS" if claim.get("claim_activation") == "BLOCKED" else "FAIL",
            "details": str(claim.get("claim_activation")),
        },
        {
            "name": "no_manuscript_or_register_update",
            "status": "PASS"
            if claim.get("manuscript_or_register_update") is False
            else "FAIL",
            "details": str(claim.get("manuscript_or_register_update")),
        },
        {
            "name": "simulation_only_ceiling_retained",
            "status": "PASS" if claim.get("evidence_ceiling") == EVIDENCE_CEILING else "FAIL",
            "details": str(claim.get("evidence_ceiling")),
        },
        {
            "name": "excluded_routes_retained",
            "status": "PASS"
            if set(claim.get("excluded_routes") or []) >= {"RCEP", "NYC"}
            else "FAIL",
            "details": json.dumps(
                claim.get("excluded_routes"), ensure_ascii=True, sort_keys=True
            ),
        },
        {
            "name": "derived_metric_is_artifact_only",
            "status": "PASS"
            if claim.get("independent_panel_log_ratio") == "DERIVED_ARTIFACT_ONLY"
            and claim.get("independent_cell_ci") == "DERIVED_DESCRIPTIVE_ONLY"
            else "FAIL",
            "details": json.dumps(
                {
                    "independent_panel_log_ratio": claim.get("independent_panel_log_ratio"),
                    "independent_cell_ci": claim.get("independent_cell_ci"),
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        },
        {
            "name": "frozen_result_unchanged",
            "status": "PASS"
            if derived.get("frozen_result_unchanged") is True
            and sufficiency.get("frozen_result_mutated") is False
            else "FAIL",
            "details": json.dumps(
                {
                    "derived_frozen_result_unchanged": derived.get(
                        "frozen_result_unchanged"
                    ),
                    "sufficiency_frozen_result_mutated": sufficiency.get(
                        "frozen_result_mutated"
                    ),
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        },
        {
            "name": "derived_values_present_but_descriptive",
            "status": "PASS"
            if derived.get("derived_values_withheld") is False
            and bool(derived.get("pair_audits"))
            and all(
                isinstance(item, Mapping) and item.get("ci_is_descriptive_only") is True
                for item in derived.get("pair_audits", [])
            )
            else "FAIL",
            "details": json.dumps(
                {
                    "derived_values_withheld": derived.get("derived_values_withheld"),
                    "pair_audit_count": len(derived.get("pair_audits") or []),
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        },
    ]
    failed = [check for check in checks if check["status"] != "PASS"]
    if failed:
        names = ", ".join(check["name"] for check in failed)
        raise GateError(f"claim-fidelity checks failed: {names}")
    return checks


def build_gate_receipt(primary_root: Path, duplicate_root: Path) -> dict[str, Any]:
    primary = primary_root.expanduser().resolve(strict=True)
    duplicate = duplicate_root.expanduser().resolve(strict=True)
    if primary == duplicate:
        raise GateError("primary and duplicate roots must be different directories")

    primary_entries = _file_inventory(primary)
    duplicate_entries = _file_inventory(duplicate)
    primary_paths = [entry["path"] for entry in primary_entries]
    duplicate_paths = [entry["path"] for entry in duplicate_entries]
    missing_required = sorted(set(REQUIRED_FILES) - set(primary_paths))
    if missing_required:
        raise GateError(f"primary root lacks required files: {missing_required}")
    if primary_paths != duplicate_paths:
        raise GateError("primary and duplicate roots have different file sets")

    primary_hashes = {entry["path"]: entry["sha256"] for entry in primary_entries}
    duplicate_hashes = {entry["path"]: entry["sha256"] for entry in duplicate_entries}
    mismatched = sorted(
        path for path in primary_hashes if primary_hashes[path] != duplicate_hashes[path]
    )
    if mismatched:
        raise GateError(f"primary and duplicate artifacts differ: {mismatched}")

    primary_manifest = _validate_manifest(primary, primary_entries)
    duplicate_manifest = _validate_manifest(duplicate, duplicate_entries)
    if primary_manifest.get("content_address") != duplicate_manifest.get("content_address"):
        raise GateError("duplicate root content address mismatch")
    claim_checks = _validate_claim_fidelity(primary)
    _validate_claim_fidelity(duplicate)

    primary_digest = _inventory_digest(primary_entries)
    duplicate_digest = _inventory_digest(duplicate_entries)
    if primary_digest != duplicate_digest:
        raise GateError("root inventory digest mismatch")

    return {
        "schema_version": SCHEMA_VERSION,
        "gate_id": GATE_ID,
        "register_key": REGISTER_KEY,
        "status": "PASS",
        "duplicate_status": "PASS",
        "claim_fidelity_status": "PASS",
        "primary_root": str(primary),
        "duplicate_root": str(duplicate),
        "content_address": primary_manifest.get("content_address"),
        "primary_root_sha256": primary_digest,
        "duplicate_root_sha256": duplicate_digest,
        "file_count": len(primary_entries),
        "file_sha256": primary_hashes,
        "claim_fidelity_checks": claim_checks,
        "manuscript_values_written_by_gate": False,
        "figure_values_written_by_gate": False,
        "frozen_quarantine_modified_by_gate": False,
    }


def write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    target = path.expanduser().resolve(strict=False)
    if target.exists():
        raise GateError(f"refusing to overwrite existing receipt: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True)
        handle.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", type=Path, required=True)
    parser.add_argument("--duplicate-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = build_gate_receipt(args.primary_root, args.duplicate_root)
        write_receipt(args.receipt, receipt)
    except (GateError, OSError) as error:
        print(f"E4-R008 gate refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
