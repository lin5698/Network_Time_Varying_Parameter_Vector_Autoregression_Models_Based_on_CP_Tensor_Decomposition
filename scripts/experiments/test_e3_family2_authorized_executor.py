"""Static gate tests for the SHA-bound E3 synthetic execution executor.

These tests construct only temporary candidate and authorization JSON files.
They never call ``execute_authorized_e3`` with a valid capability, generate an
E3 panel, fit a method, evaluate a response, run a bootstrap, or reserve a
scientific quarantine output root.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.experiments import e3_family2_artifact_schemas as artifact_schemas
from scripts.experiments import e3_family2_authorized_executor as executor
from scripts.experiments import e3_family2_candidate_package as package


class E3Family2AuthorizedExecutorTests(unittest.TestCase):
    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_gate_receipt(self, root: Path) -> Path:
        receipt = root / package.GATE_RECEIPT_FILENAME
        stdout = ""
        stderr = (
            ".\n----------------------------------------------------------------------\n"
            "Ran 1 test in 0.001s\n\nOK\n"
        )
        payload = {
            "schema_version": package.gate_receipt.SCHEMA_VERSION,
            "verdict": "PASS",
            "command": package.gate_receipt._expected_command(),
            "suite_modules": list(package.gate_receipt.GATE_TEST_MODULES),
            "suite_sha256": package.gate_receipt._suite_hashes(),
            "recorder": package.gate_receipt._recorder_identity(),
            "started_at": "2026-07-31T00:00:00Z",
            "completed_at": "2026-07-31T00:00:01Z",
            "returncode": 0,
            "tests_run": 1,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": package.gate_receipt._sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": package.gate_receipt._sha256_bytes(stderr.encode("utf-8")),
            "scientific_execution": "NOT_AUTHORIZED",
        }
        receipt.write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )
        return receipt

    def _build_candidate(self, root: Path) -> tuple[Path, str, Path]:
        quarantine_root = root / "e3-authorized-executor-quarantine"
        built = package.build_candidate_ready_package(
            root / "candidate-package",
            candidate_id="e3-authorized-executor-fixture-v1",
            quarantine_output_root=quarantine_root,
            gate_test_receipt_path=self._write_gate_receipt(root),
        )
        return built.candidate_path, built.candidate_sha256, quarantine_root

    def _authorization_payload(
        self, candidate_path: Path, candidate_sha256: str, quarantine_root: Path
    ) -> dict[str, object]:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        bindings = candidate["bindings"]
        return {
            "schema_version": executor.AUTHORIZATION_SCHEMA_VERSION,
            "decision_id": "e3-authorized-executor-fixture-decision",
            "decision": "AUTHORIZED",
            "scientific_execution_authorized": True,
            "authorized_by": "workspace-author-fixture",
            "authorized_at": "2026-07-23T00:00:00Z",
            "action": executor.ACTION,
            "candidate_sha256": candidate_sha256,
            "candidate_id": candidate["candidate_id"],
            "execution": candidate["execution"],
            "bindings": {
                "source_hashes_sha256": artifact_schemas.canonical_sha256(
                    bindings["source_hashes"]
                ),
                "dependency_hashes_sha256": artifact_schemas.canonical_sha256(
                    bindings["dependency_hashes"]
                ),
                "configuration_sha256": bindings["configuration_sha256"],
                "preoutcome_artifacts_sha256": artifact_schemas.canonical_sha256(
                    bindings["preoutcome_artifacts"]
                ),
            },
            "output_root": str(quarantine_root.resolve(strict=False)),
            "overwrite": "deny",
            "r006e_outcome_authorized": False,
            "r006f_outcome_authorized": False,
            "downstream_builds_authorized": False,
            "post_run_controls": dict(executor._POST_RUN_CONTROLS),
        }

    def _write_authorization(
        self, root: Path, candidate_path: Path, candidate_sha256: str, quarantine_root: Path
    ) -> tuple[Path, str]:
        path = root / "workspace-author-authorization.json"
        path.write_text(
            json.dumps(
                self._authorization_payload(candidate_path, candidate_sha256, quarantine_root),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return path, self._sha256(path)

    def test_frozen_v4_specification_requires_recursive_retuned_bootstrap(self) -> None:
        specification = executor._expected_frozen_specification()
        procedure = specification["uncertainty"]["bootstrap_procedure"]

        self.assertEqual(specification["schema_version"], "e3-synthetic-input-v4")
        self.assertEqual(specification["stability"]["domain_uniform_envelope"]["value"], 0.90)
        self.assertEqual(
            procedure["method"],
            "recursive_residual_circular_moving_block_bootstrap",
        )
        self.assertEqual(procedure["lag_feature_source"], "pseudo_response_history")
        self.assertTrue(procedure["retune_inside_bootstrap"])
        self.assertEqual(procedure["retune_candidate_list"], [1, 2, 3])
        self.assertEqual(procedure["failure_retention"], "all_replicates")

    def test_missing_or_mismatched_authorization_refuses_before_science_or_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate_path, candidate_sha256, quarantine_root = self._build_candidate(root)
            authorization_path, _authorization_sha256 = self._write_authorization(
                root, candidate_path, candidate_sha256, quarantine_root
            )
            calls: list[str] = []

            def forbidden(name: str):
                def callback(*_args: object, **_kwargs: object) -> object:
                    calls.append(name)
                    raise AssertionError(f"{name} must not be called")

                return callback

            with (
                mock.patch.object(
                    executor.core, "make_synthetic_panel", side_effect=forbidden("panel")
                ),
                mock.patch.object(
                    executor.core, "select_hyperparameter", side_effect=forbidden("selection")
                ),
                mock.patch.object(
                    executor, "_reserve_quarantine_root", side_effect=forbidden("root")
                ),
            ):
                with self.assertRaisesRegex(executor.AuthorizationError, "exact SHA-256"):
                    executor.prepare_authorized_execution(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        authorization_path=None,
                        expected_authorization_sha256=None,
                        expected_quarantine_root=quarantine_root,
                    )
                with self.assertRaisesRegex(executor.AuthorizationError, "does not match"):
                    executor.prepare_authorized_execution(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        authorization_path=authorization_path,
                        expected_authorization_sha256="0" * 64,
                        expected_quarantine_root=quarantine_root,
                    )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_exact_authorization_preflight_is_nonexecuting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate_path, candidate_sha256, quarantine_root = self._build_candidate(root)
            authorization_path, authorization_sha256 = self._write_authorization(
                root, candidate_path, candidate_sha256, quarantine_root
            )
            calls: list[str] = []

            def forbidden(*_args: object, **_kwargs: object) -> object:
                calls.append("scientific")
                raise AssertionError("scientific entrypoints must not be called by preflight")

            with (
                mock.patch.object(executor.core, "make_synthetic_panel", side_effect=forbidden),
                mock.patch.object(executor.core, "select_hyperparameter", side_effect=forbidden),
                mock.patch.object(executor, "_reserve_quarantine_root", side_effect=forbidden),
            ):
                capability = executor.prepare_authorized_execution(
                    candidate_path=candidate_path,
                    expected_candidate_sha256=candidate_sha256,
                    authorization_path=authorization_path,
                    expected_authorization_sha256=authorization_sha256,
                    expected_quarantine_root=quarantine_root,
                )

            self.assertIsInstance(capability, executor._ExecutionCapability)
            self.assertEqual(capability.quarantine_output_root, quarantine_root.resolve())
            self.assertIsInstance(capability.specification_snapshot, bytes)
            self.assertFalse(hasattr(capability, "candidate"))
            self.assertFalse(hasattr(capability, "authorization"))
            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_candidate_missing_current_executor_hash_refuses_before_science_or_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate_path, _candidate_sha256, quarantine_root = self._build_candidate(root)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["bindings"]["source_hashes"].pop(
                str(Path(executor.__file__).resolve())
            )
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            authorization_path, authorization_sha256 = self._write_authorization(
                root, candidate_path, candidate_sha256, quarantine_root
            )
            calls: list[str] = []

            def forbidden(*_args: object, **_kwargs: object) -> object:
                calls.append("scientific")
                raise AssertionError("science must not run")

            with mock.patch.object(executor.core, "make_synthetic_panel", side_effect=forbidden):
                with self.assertRaisesRegex(executor.AuthorizationError, "authorized E3 executor source"):
                    executor.prepare_authorized_execution(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        authorization_path=authorization_path,
                        expected_authorization_sha256=authorization_sha256,
                        expected_quarantine_root=quarantine_root,
                    )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_candidate_missing_scientific_core_hash_refuses_before_science_or_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate_path, _candidate_sha256, quarantine_root = self._build_candidate(root)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["bindings"]["source_hashes"].pop(
                str(Path(executor.core.__file__).resolve())
            )
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            authorization_path, authorization_sha256 = self._write_authorization(
                root, candidate_path, candidate_sha256, quarantine_root
            )
            calls: list[str] = []

            def forbidden(*_args: object, **_kwargs: object) -> object:
                calls.append("scientific")
                raise AssertionError("science must not run")

            with mock.patch.object(executor.core, "make_synthetic_panel", side_effect=forbidden):
                with self.assertRaisesRegex(executor.AuthorizationError, "scientific core"):
                    executor.prepare_authorized_execution(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        authorization_path=authorization_path,
                        expected_authorization_sha256=authorization_sha256,
                        expected_quarantine_root=quarantine_root,
                    )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_configuration_drift_refuses_before_science_or_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate_path, _candidate_sha256, quarantine_root = self._build_candidate(root)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["bindings"]["configuration"]["comparators"] = ["fixed_rank_basis"]
            candidate["bindings"]["configuration_sha256"] = artifact_schemas.canonical_sha256(
                candidate["bindings"]["configuration"]
            )
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            authorization_path, authorization_sha256 = self._write_authorization(
                root, candidate_path, candidate_sha256, quarantine_root
            )
            calls: list[str] = []

            def forbidden(*_args: object, **_kwargs: object) -> object:
                calls.append("scientific")
                raise AssertionError("science must not run")

            with mock.patch.object(executor.core, "make_synthetic_panel", side_effect=forbidden):
                with self.assertRaisesRegex(executor.AuthorizationError, "configuration does not match"):
                    executor.prepare_authorized_execution(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        authorization_path=authorization_path,
                        expected_authorization_sha256=authorization_sha256,
                        expected_quarantine_root=quarantine_root,
                    )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_runtime_dependency_drift_refuses_before_science_or_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            candidate_path, _candidate_sha256, quarantine_root = self._build_candidate(root)
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            dependency_path = Path(
                next(iter(candidate["bindings"]["dependency_hashes"]))
            )
            dependency_lock = json.loads(dependency_path.read_text(encoding="utf-8"))
            dependency_lock["numpy_version"] = "0.0.0-fixture-drift"
            dependency_path.write_text(json.dumps(dependency_lock, sort_keys=True), encoding="utf-8")
            candidate["bindings"]["dependency_hashes"] = {
                str(dependency_path): self._sha256(dependency_path)
            }
            candidate_path.write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            candidate_sha256 = self._sha256(candidate_path)
            authorization_path, authorization_sha256 = self._write_authorization(
                root, candidate_path, candidate_sha256, quarantine_root
            )
            calls: list[str] = []

            def forbidden(*_args: object, **_kwargs: object) -> object:
                calls.append("scientific")
                raise AssertionError("science must not run")

            with mock.patch.object(executor.core, "make_synthetic_panel", side_effect=forbidden):
                with self.assertRaisesRegex(executor.AuthorizationError, "current runtime"):
                    executor.prepare_authorized_execution(
                        candidate_path=candidate_path,
                        expected_candidate_sha256=candidate_sha256,
                        authorization_path=authorization_path,
                        expected_authorization_sha256=authorization_sha256,
                        expected_quarantine_root=quarantine_root,
                    )

            self.assertEqual(calls, [])
            self.assertFalse(quarantine_root.exists())

    def test_forged_capability_cannot_reserve_or_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            quarantine_root = Path(temporary_directory) / "forged-capability-quarantine"
            forged = executor._ExecutionCapability(
                object(), "0" * 64, "0" * 64, "forged", quarantine_root, b"{}"
            )
            with mock.patch.object(executor, "_reserve_quarantine_root") as reserve:
                with self.assertRaisesRegex(executor.AuthorizationError, "requires a capability"):
                    executor.execute_authorized_e3(forged)

            reserve.assert_not_called()
            self.assertFalse(quarantine_root.exists())

    def test_interval_summary_never_conditions_coverage_on_successful_panels(self) -> None:
        records = [
            {
                "family": "family2",
                "n": 20,
                "seed": 4101,
                "query_class": "cross_generator",
                "status": "AVAILABLE",
                "coverage": 1.0,
                "mean_interval_width": 0.2,
                "raw_response_mse": 0.1,
                "stability_qualified_response_mse": 0.1,
                "estimated_spectral_radius": 0.4,
                "truth_spectral_radius": 0.3,
                "completed_replicates": 80,
                "requested_replicates": 80,
                "bootstrap_status_counts": {
                    "AVAILABLE": 80,
                    "OUTSIDE_TARGET": 0,
                    "NONCONVERGED": 0,
                    "NONFINITE": 0,
                    "UNSTABLE": 0,
                },
            },
            {
                "family": "family2",
                "n": 20,
                "seed": 4102,
                "query_class": "cross_generator",
                "status": "NONCONVERGED",
                "coverage": None,
                "mean_interval_width": None,
                "raw_response_mse": 0.3,
                "stability_qualified_response_mse": None,
                "estimated_spectral_radius": 0.5,
                "truth_spectral_radius": 0.3,
                "completed_replicates": 79,
                "requested_replicates": 80,
                "bootstrap_status_counts": {
                    "AVAILABLE": 79,
                    "OUTSIDE_TARGET": 0,
                    "NONCONVERGED": 1,
                    "NONFINITE": 0,
                    "UNSTABLE": 0,
                },
            },
        ]

        summary = executor._interval_summaries(records)["family2|20|cross_generator"]
        self.assertEqual(summary["declared_panel_records"], 2)
        self.assertEqual(summary["available_interval_records"], 1)
        self.assertFalse(summary["all_declared_intervals_available"])
        self.assertIsNone(summary["coverage"])
        self.assertIsNone(summary["mean_interval_width"])
        self.assertAlmostEqual(float(summary["raw_response_mse_mean"]), 0.2)
        self.assertEqual(summary["bootstrap_status_counts"]["NONCONVERGED"], 1)


if __name__ == "__main__":
    unittest.main()
