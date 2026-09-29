import tempfile
import unittest
import json
import hashlib
import io
import os
from dataclasses import FrozenInstanceError
from types import MappingProxyType
from pathlib import Path
from unittest.mock import patch

from scripts.experiments import r006f_construction_gate as gate


class R006FConstructionGateTest(unittest.TestCase):
    def test_writer_rejects_smoke_at_the_formal_artifact_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            formal_path = Path(temporary_directory) / gate.ARTIFACT_NAME
            formal_path.write_bytes(b"existing formal artifact\n")

            with patch.object(gate, "DEFAULT_OUTPUT", formal_path):
                with self.assertRaisesRegex(ValueError, "smoke"):
                    gate.write_preoutcome_gate(formal_path, smoke=True)

                self.assertEqual(
                    formal_path.read_bytes(), b"existing formal artifact\n"
                )
                formal = gate.write_preoutcome_gate(formal_path)

            self.assertIn(
                formal.artifact["status"],
                {"CONSTRUCTION_PASS", "CONSTRUCTION_FAIL"},
            )

    def test_directory_writer_rejects_smoke_at_the_formal_output_dir(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            formal_dir = Path(temporary_directory)
            formal_path = formal_dir / gate.ARTIFACT_NAME
            formal_path.write_bytes(b"existing formal artifact\n")

            with patch.object(gate, "DEFAULT_OUTPUT", formal_path):
                with self.assertRaisesRegex(ValueError, "smoke"):
                    gate.write_preoutcome_gate_to_dir(formal_dir, smoke=True)

            self.assertEqual(
                formal_path.read_bytes(), b"existing formal artifact\n"
            )

    def test_writer_accepts_and_returns_the_exact_artifact_path(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = (
                Path(temporary_directory) / "nested" / gate.ARTIFACT_NAME
            )
            result = gate.write_preoutcome_gate(artifact_path)

            self.assertEqual(result.artifact_path, artifact_path.resolve())
            self.assertTrue(result.artifact_path.is_file())
            self.assertEqual(
                json.loads(result.artifact_path.read_text(encoding="utf-8")),
                result.artifact,
            )
            self.assertFalse(
                (artifact_path / gate.ARTIFACT_NAME).exists()
            )

    def test_write_gate_is_construction_only_and_never_generates_worlds(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "scripts.experiments.r006f_exact_design.generate_paired_worlds",
                side_effect=AssertionError("world generation is forbidden"),
            ):
                artifact = gate.write_preoutcome_gate_to_dir(
                    Path(temporary_directory)
                )

        self.assertIn(
            artifact["status"], {"CONSTRUCTION_PASS", "CONSTRUCTION_FAIL"}
        )

    def test_artifact_serializes_frozen_contract_provenance_and_checks_only(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            artifact = gate.write_preoutcome_gate_to_dir(output_dir)
            serialized = (output_dir / gate.ARTIFACT_NAME).read_text(
                encoding="utf-8"
            )

            self.assertEqual(
                artifact["contract"]["formal_seeds"],
                list(range(620001, 620051)),
            )
            self.assertEqual(
                artifact["contract"]["excitation_scales"], [1.0, 0.25]
            )
            self.assertEqual(artifact["provenance"], gate.current_provenance())
            self.assertEqual(set(artifact["checks"]), {"strong", "weak", "cross_scale"})
            self.assertEqual(artifact["checks"]["strong"]["rank"], 2)
            self.assertEqual(artifact["checks"]["weak"]["rank"], 2)
            self.assertIn("analytic_gap", artifact["checks"]["strong"])
            json.loads(serialized)
            self.assertEqual(list(output_dir.glob("*.csv")), [])

    def test_verify_accepts_an_unchanged_preoutcome_artifact(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            written = gate.write_preoutcome_gate_to_dir(output_dir)
            with patch(
                "scripts.experiments.r006f_exact_design.generate_paired_worlds",
                side_effect=AssertionError("world generation is forbidden"),
            ):
                token = gate.verify_preoutcome_gate(output_dir)

        self.assertEqual(token.artifact_sha256, written["artifact_sha256"])

    def test_verify_rejects_fields_outside_the_exact_schema(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            artifact = gate.write_preoutcome_gate_to_dir(output_dir)
            self.assertEqual(artifact["run_type"], "construction_only")
            self.assertEqual(
                set(artifact),
                {
                    "schema_version",
                    "run_type",
                    "status",
                    "contract",
                    "provenance",
                    "checks",
                    "artifact_sha256",
                },
            )
            artifact["formal_pass"] = True
            (output_dir / gate.ARTIFACT_NAME).write_text(
                json.dumps(artifact), encoding="utf-8"
            )

            with self.assertRaises(RuntimeError):
                gate.verify_preoutcome_gate(output_dir)

    def test_verify_rejects_nested_injection_and_modified_checks(self):
        mutations = (
            lambda artifact: artifact["checks"]["strong"].__setitem__(
                "world", {}
            ),
            lambda artifact: artifact["checks"]["strong"].__setitem__(
                "rank", 1
            ),
            lambda artifact: artifact["checks"]["strong"].__setitem__(
                "response_error", 0.0
            ),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    output_dir = Path(temporary_directory)
                    artifact = gate.write_preoutcome_gate_to_dir(output_dir)
                    mutate(artifact)
                    body = dict(artifact)
                    body.pop("artifact_sha256")
                    artifact["artifact_sha256"] = hashlib.sha256(
                        json.dumps(
                            body,
                            sort_keys=True,
                            separators=(",", ":"),
                            allow_nan=False,
                        ).encode("utf-8")
                    ).hexdigest()
                    (output_dir / gate.ARTIFACT_NAME).write_text(
                        json.dumps(artifact), encoding="utf-8"
                    )

                    with self.assertRaises(RuntimeError):
                        gate.verify_preoutcome_gate(output_dir)

    def test_verify_rejects_raw_byte_tamper_and_nonpass_statuses(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            destination = output_dir / gate.ARTIFACT_NAME
            gate.write_preoutcome_gate_to_dir(output_dir)
            destination.write_bytes(
                destination.read_bytes().replace(
                    b"CONSTRUCTION_PASS", b"CONSTRUCTION_FASS", 1
                )
            )
            with self.assertRaises(RuntimeError):
                gate.verify_preoutcome_gate(output_dir)

        original_panel_checks = gate._panel_checks

        def failed_panel_checks(panel):
            record = original_panel_checks(panel)
            record["passed"] = False
            record["failure_reasons"] = ["forced_test_failure"]
            return record

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            with patch.object(
                gate, "_panel_checks", side_effect=failed_panel_checks
            ):
                failed = gate.write_preoutcome_gate_to_dir(output_dir)
            self.assertEqual(failed["status"], "CONSTRUCTION_FAIL")
            with self.assertRaises(RuntimeError):
                gate.verify_preoutcome_gate(output_dir)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            gate.write_preoutcome_gate_to_dir(output_dir, smoke=True)
            with self.assertRaises(RuntimeError):
                gate.verify_preoutcome_gate(output_dir)

    def test_loaded_source_disk_mismatch_stops_before_world_generation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "loaded.py"
            loaded_content = b"loaded version\n"
            source_path.write_bytes(b"changed on disk\n")
            snapshot = MappingProxyType(
                {
                    "gate_code": gate.LoadedSource(
                        path=source_path,
                        content=loaded_content,
                        sha256=hashlib.sha256(loaded_content).hexdigest(),
                    )
                }
            )
            with patch.object(gate, "LOADED_SOURCE_SNAPSHOT", snapshot):
                with patch(
                    "scripts.experiments.r006f_exact_design.generate_paired_worlds",
                    side_effect=AssertionError("world generation is forbidden"),
                ) as generator:
                    with self.assertRaisesRegex(
                        RuntimeError, "loaded-source snapshot mismatch"
                    ):
                        gate.write_preoutcome_gate_to_dir(Path(temporary_directory))

            generator.assert_not_called()

    def test_artifact_has_canonical_self_digest_and_repeated_bytes(self):
        with tempfile.TemporaryDirectory() as first_directory:
            first = gate.write_preoutcome_gate_to_dir(Path(first_directory))
            first_bytes = (
                Path(first_directory) / gate.ARTIFACT_NAME
            ).read_bytes()
        with tempfile.TemporaryDirectory() as second_directory:
            second = gate.write_preoutcome_gate_to_dir(Path(second_directory))
            second_bytes = (
                Path(second_directory) / gate.ARTIFACT_NAME
            ).read_bytes()

        body = dict(first)
        stored_digest = body.pop("artifact_sha256")
        canonical_body = json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(
            stored_digest, hashlib.sha256(canonical_body).hexdigest()
        )
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, second_bytes)

    def test_verify_returns_frozen_token_with_runtime_provenance_digest(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            artifact = gate.write_preoutcome_gate_to_dir(output_dir)
            token = gate.verify_preoutcome_gate(output_dir)

        provenance = artifact["provenance"]
        self.assertIn("python_version", provenance)
        self.assertIn("numpy_config", provenance)
        self.assertIn("numpy_config_sha256", provenance)
        expected_provenance_digest = hashlib.sha256(
            json.dumps(
                provenance,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            token,
            gate.GateToken(
                artifact_sha256=artifact["artifact_sha256"],
                provenance_sha256=expected_provenance_digest,
            ),
        )
        with self.assertRaises(FrozenInstanceError):
            token.artifact_sha256 = "0" * 64

    def test_verify_rejects_changed_code_hash_before_world_generation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            gate.write_preoutcome_gate_to_dir(output_dir)
            changed = gate.current_provenance()
            changed["gate_code_sha256"] = "0" * 64
            with patch.object(gate, "current_provenance", return_value=changed):
                with patch(
                    "scripts.experiments.r006f_exact_design.generate_paired_worlds",
                    side_effect=AssertionError("world generation is forbidden"),
                ) as generator:
                    with self.assertRaises(RuntimeError):
                        gate.verify_preoutcome_gate(output_dir)

            generator.assert_not_called()

    def test_verify_rejects_missing_artifact_fields(self):
        for missing_field in ("provenance", "contract"):
            with self.subTest(missing_field=missing_field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    output_dir = Path(temporary_directory)
                    artifact = gate.write_preoutcome_gate_to_dir(output_dir)
                    artifact.pop(missing_field)
                    (output_dir / gate.ARTIFACT_NAME).write_text(
                        json.dumps(artifact), encoding="utf-8"
                    )
                    with self.assertRaises(RuntimeError):
                        gate.verify_preoutcome_gate(output_dir)

    def test_cli_defaults_to_formal_construction_path_and_supports_smoke(self):
        arguments = gate.build_argument_parser().parse_args([])

        self.assertEqual(arguments.output, gate.DEFAULT_OUTPUT)
        self.assertFalse(arguments.smoke)
        self.assertEqual(
            gate.DEFAULT_OUTPUT,
            gate.ROOT
            / "output"
            / "high_impact_revision"
            / "r006f_exact_support_abstention"
            / "construction_gate_preoutcome.json",
        )
        with self.assertRaises(SystemExit):
            gate.build_argument_parser().parse_args(["--smoke"])
        with self.assertRaises(SystemExit):
            gate.build_argument_parser().parse_args(
                ["--smoke", "--output", str(gate.DEFAULT_OUTPUT)]
            )
        with tempfile.TemporaryDirectory() as temporary_directory:
            smoke_output = Path(temporary_directory) / gate.ARTIFACT_NAME
            parsed = gate.build_argument_parser().parse_args(
                ["--smoke", "--output", str(smoke_output)]
            )
            self.assertEqual(
                parsed.output, smoke_output.resolve(strict=False)
            )
            smoke = gate.write_preoutcome_gate_to_dir(
                Path(temporary_directory), smoke=True
            )
        self.assertIn(
            smoke["status"],
            {"SMOKE_CONSTRUCTION_PASS", "SMOKE_CONSTRUCTION_FAIL"},
        )

    def test_parser_rejects_formal_path_aliases_and_other_filenames(self):
        parent_alias = (
            gate.DEFAULT_OUTPUT.parent
            / "nonexistent-subdirectory"
            / ".."
            / gate.ARTIFACT_NAME
        )
        with self.assertRaises(SystemExit):
            gate.build_argument_parser().parse_args(
                ["--smoke", "--output", str(parent_alias)]
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            symlink_parent = Path(temporary_directory) / "formal-alias"
            symlink_parent.symlink_to(
                gate.DEFAULT_OUTPUT.parent, target_is_directory=True
            )
            symlink_output = symlink_parent / gate.ARTIFACT_NAME
            with self.assertRaises(SystemExit):
                gate.build_argument_parser().parse_args(
                    ["--smoke", "--output", str(symlink_output)]
                )

            wrong_name = Path(temporary_directory) / "smoke.json"
            for arguments in (
                ["--output", str(wrong_name)],
                ["--smoke", "--output", str(wrong_name)],
            ):
                with self.subTest(arguments=arguments):
                    with self.assertRaises(SystemExit):
                        gate.build_argument_parser().parse_args(arguments)

    def test_cli_returns_nonzero_for_formal_construction_failure(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / gate.ARTIFACT_NAME
            with patch.object(
                gate,
                "write_preoutcome_gate",
                return_value=gate.GateWriteResult(
                    artifact={"status": "CONSTRUCTION_FAIL"},
                    artifact_path=output.resolve(strict=False),
                ),
            ):
                with patch("sys.stdout", new=io.StringIO()):
                    exit_code = gate.main(["--output", str(output)])

        self.assertEqual(exit_code, 1)

    def test_main_prints_the_exact_path_that_it_created(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_path = Path(temporary_directory) / gate.ARTIFACT_NAME
            stdout = io.StringIO()
            with patch("sys.stdout", new=stdout):
                exit_code = gate.main(["--output", str(artifact_path)])

            printed = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                printed["output"], str(artifact_path.resolve(strict=False))
            )
            self.assertTrue(Path(printed["output"]).is_file())
            token = gate.verify_preoutcome_gate(artifact_path.parent)
            self.assertEqual(
                token.artifact_sha256,
                json.loads(artifact_path.read_text(encoding="utf-8"))[
                    "artifact_sha256"
                ],
            )

    def test_write_publishes_with_atomic_replace(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            with patch.object(gate.os, "replace", wraps=os.replace) as replace:
                gate.write_preoutcome_gate_to_dir(output_dir)

        replace.assert_called_once()
        temporary_path, destination = replace.call_args.args
        self.assertEqual(
            Path(temporary_path).parent, output_dir.resolve(strict=False)
        )
        self.assertEqual(
            Path(destination),
            output_dir.resolve(strict=False) / gate.ARTIFACT_NAME,
        )

    def test_interrupted_replace_preserves_the_old_valid_artifact(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            destination = output_dir / gate.ARTIFACT_NAME
            gate.write_preoutcome_gate_to_dir(output_dir)
            old_bytes = destination.read_bytes()

            with patch.object(
                gate.os, "replace", side_effect=OSError("interrupted")
            ):
                with self.assertRaises(OSError):
                    gate.write_preoutcome_gate_to_dir(output_dir)

            self.assertEqual(destination.read_bytes(), old_bytes)
            gate.verify_preoutcome_gate(output_dir)
            self.assertEqual(
                list(output_dir.glob(f".{gate.ARTIFACT_NAME}.*")), []
            )

    def test_verify_normalizes_malformed_or_nonfinite_json_errors_with_path(self):
        invalid_payloads = (
            b"not-json",
            b"[]",
            b'{"value":NaN}',
            b'{"value":Infinity}',
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    output_dir = Path(temporary_directory)
                    artifact_path = output_dir / gate.ARTIFACT_NAME
                    artifact_path.write_bytes(payload)

                    with self.assertRaisesRegex(
                        RuntimeError, str(artifact_path)
                    ):
                        gate.verify_preoutcome_gate(output_dir)


if __name__ == "__main__":
    unittest.main()
