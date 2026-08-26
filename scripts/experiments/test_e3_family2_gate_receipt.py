"""Fixture-only tests for the non-scientific gate-test run recorder."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.experiments import e3_family2_gate_receipt as receipt


class E3Family2GateReceiptTests(unittest.TestCase):
    def test_successful_subprocess_run_is_bound_before_pass_receipt_is_written(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["python", "-m", "unittest"],
            returncode=0,
            stdout="",
            stderr="......................................................................\n"
            "----------------------------------------------------------------------\n"
            "Ran 70 tests in 1.600s\n\nOK\n",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "gate-receipt.json"
            with mock.patch.object(receipt.subprocess, "run", return_value=completed):
                written = receipt.record_gate_test_run(destination)

            self.assertTrue(destination.is_file())
            self.assertEqual(written["verdict"], "PASS")
            self.assertEqual(written["tests_run"], 70)
            self.assertEqual(written["returncode"], 0)
            self.assertEqual(receipt.validate_gate_test_receipt(destination), written)

    def test_failed_subprocess_run_cannot_write_a_receipt(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["python", "-m", "unittest"],
            returncode=1,
            stdout="",
            stderr="FAILED (failures=1)\n",
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "gate-receipt.json"
            with mock.patch.object(receipt.subprocess, "run", return_value=completed):
                with self.assertRaisesRegex(receipt.GateReceiptError, "did not pass"):
                    receipt.record_gate_test_run(destination)
            self.assertFalse(destination.exists())

    def test_self_declared_pass_without_execution_record_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "gate-receipt.json"
            destination.write_text(
                json.dumps({"verdict": "PASS", "scientific_execution": "NOT_AUTHORIZED"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(receipt.GateReceiptError, "field set"):
                receipt.validate_gate_test_receipt(destination)


if __name__ == "__main__":
    unittest.main()
