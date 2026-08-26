"""Fixture-only tests for the outcome-free R006e v2 construction contract."""

from __future__ import annotations

import copy
import json
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.experiments import r006e_construction_v2 as construction


class ConstructionV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = Path("output/high_impact_revision/r006e_native_supported_recovery/construction_gate_preoutcome.json")
        cls.certificates = json.loads(source.read_text(encoding="utf-8"))["screening_support_certificates"]

    def _paths(self) -> construction.ConstructionV2Paths:
        self.tmp = tempfile.TemporaryDirectory()
        parent = Path(self.tmp.name)
        (parent / construction.V2_REPEAT_ROOT_NAME).mkdir()
        (parent / construction.V2_CONTROL_ROOT_NAME).mkdir()
        return construction.ConstructionV2Paths(
            parent / construction.V2_PRIMARY_ROOT_NAME,
            parent / construction.V2_REPEAT_ROOT_NAME,
            parent / construction.V2_CONTROL_ROOT_NAME,
            future_checklist=parent / "future-checklist.md",
        )

    def tearDown(self) -> None:
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def test_build_and_verify_are_fixture_only_and_publish_two_files(self) -> None:
        paths = self._paths()
        class NoScienceSpy:
            def __getattr__(self, name: str) -> object:
                raise AssertionError(f"scientific outcome operation accessed: {name}")

        spy = NoScienceSpy()
        with mock.patch.object(construction, "_build_certificates", return_value=copy.deepcopy(self.certificates)) as build:
            artifact = construction.build_construction_v2(paths, scientific_spy=spy)
        build.assert_called_once_with()
        self.assertEqual(artifact["status"], "CONSTRUCTION_PASS")
        self.assertEqual(artifact["current_state"], "NOT_AUTHORIZED")
        self.assertEqual(
            sorted(path.name for path in paths.primary.iterdir()),
            [construction.CONSTRUCTION_ARTIFACT_NAME, construction.CONSTRUCTION_MANIFEST_NAME],
        )
        self.assertEqual(tuple(paths.repeat.iterdir()), ())
        self.assertEqual(tuple(paths.control.iterdir()), ())
        self.assertEqual(construction.verify_construction_v2(paths)["artifact_sha256"], artifact["artifact_sha256"])

    def test_certificate_builder_contains_no_scientific_entry_points(self) -> None:
        source = inspect.getsource(construction._build_certificates)
        for marker in ("run_screening_cell", "evaluate_screening", "compute_gate", "r006f_exact"):
            self.assertNotIn(marker, source)

    def test_unknown_or_outcome_fields_refuse(self) -> None:
        paths = self._paths()
        with mock.patch.object(construction, "_build_certificates", return_value=copy.deepcopy(self.certificates)):
            construction.build_construction_v2(paths)
        artifact_path = paths.primary / construction.CONSTRUCTION_ARTIFACT_NAME
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact["unknown"] = 1
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        with self.assertRaises(construction.ConstructionV2Error):
            construction.verify_construction_v2(paths)

    def test_v1_and_repeat_control_roots_are_not_written(self) -> None:
        paths = self._paths()
        before = construction._root_inventory(construction.ROOT / "output/high_impact_revision/r006e_native_supported_recovery")
        with mock.patch.object(construction, "_build_certificates", return_value=copy.deepcopy(self.certificates)):
            construction.build_construction_v2(paths)
        after = construction._root_inventory(construction.ROOT / "output/high_impact_revision/r006e_native_supported_recovery")
        self.assertEqual(before, after)
        self.assertEqual(tuple(paths.repeat.iterdir()), ())
        self.assertEqual(tuple(paths.control.iterdir()), ())

    def test_repeat_and_control_roots_may_be_absent(self) -> None:
        paths = self._paths()
        paths.repeat.rmdir()
        paths.control.rmdir()
        with mock.patch.object(construction, "_build_certificates", return_value=copy.deepcopy(self.certificates)):
            artifact = construction.build_construction_v2(paths)
        self.assertFalse(paths.repeat.exists())
        self.assertFalse(paths.control.exists())
        self.assertEqual(construction.verify_construction_v2(paths)["artifact_sha256"], artifact["artifact_sha256"])

    def test_frozen_v1_authority_binding_cannot_be_forged(self) -> None:
        paths = self._paths()
        with mock.patch.object(construction, "_build_certificates", return_value=copy.deepcopy(self.certificates)):
            construction.build_construction_v2(paths)
        artifact_path = paths.primary / construction.CONSTRUCTION_ARTIFACT_NAME
        manifest_path = paths.primary / construction.CONSTRUCTION_MANIFEST_NAME
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact["frozen_v1_authority"]["digest"] = "0" * 64
        artifact["canonical_sha256"] = construction.canonical_json_sha256(
            {key: artifact[key] for key in construction.CONSTRUCTION_ARTIFACT_FIELDS
             if key not in {"canonical_sha256", "artifact_sha256"}}
        )
        artifact["artifact_sha256"] = construction.canonical_json_sha256(artifact)
        artifact_path.write_bytes(construction._canonical(artifact))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifact_sha256"] = artifact["artifact_sha256"]
        manifest_path.write_bytes(construction._canonical(manifest))
        with self.assertRaisesRegex(construction.ConstructionV2Error, "frozen v1 authority"):
            construction.verify_construction_v2(paths)

    def test_source_drift_refuses_before_accepting_artifact(self) -> None:
        paths = self._paths()
        with mock.patch.object(construction, "_build_certificates", return_value=copy.deepcopy(self.certificates)):
            construction.build_construction_v2(paths)
        target = construction.ROOT / construction.V2_SOURCE_PATHS[0]
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n")
            with self.assertRaises(construction.ConstructionV2Error):
                construction.verify_construction_v2(paths)
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
