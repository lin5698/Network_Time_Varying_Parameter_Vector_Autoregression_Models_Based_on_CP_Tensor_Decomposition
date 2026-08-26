"""Fixture-only tests for deterministic R006e screening v2 outputs."""

from __future__ import annotations

import json
import hashlib
import inspect
import math
import os
from pathlib import Path
import queue
import tempfile
import threading
from types import MappingProxyType
import unittest
from unittest.mock import patch

from scripts.experiments.r006e_native_gates import evaluate_screening_gate
from scripts.experiments.r006e_native_protocol import R006EConfig
from scripts.experiments.r006e_screening_executor_v2 import (
    CellExecution,
    combine_cell_executions,
    retain_worker_failure,
    screening_cell_tasks,
)
from scripts.experiments.r006e_screening_schema_v2 import (
    FORMAL_REPLICATION_FIELDS,
    REPLICATION_IDENTITIES,
    SUMMARY_FIELDS,
    SUMMARY_IDENTITIES,
    SUMMARY_ROW_FIELDS,
    SCIENTIFIC_RESULT_FIELDS,
    MANIFEST_FIELDS,
    derive_attempt_id,
)
from scripts.experiments.r006e_screening_outputs_v2 import (
    PUBLICATION_ORDER,
    ROLE_FILE_NAMES,
    OutputIntegrityError,
    RoleArtifacts,
    RoleMetadata,
    build_role_artifacts,
    build_summary_rows,
    parse_diagnostic_jsonl,
    parse_replication_csv,
    parse_resource_jsonl,
    parse_row_journal_jsonl,
    serialize_diagnostic_jsonl,
    serialize_replication_csv,
    serialize_resource_jsonl,
    serialize_row_journal_jsonl,
    publish_role_artifacts,
    verify_published_role,
)
import scripts.experiments.r006e_screening_outputs_v2 as outputs_v2


ATTEMPT_ID = derive_attempt_id("task5-fixture", "primary")


def fixture_execution() -> CellExecution:
    cells = tuple(
        retain_worker_failure(
            task,
            construction_certificate={},
            attempt_id=ATTEMPT_ID,
            role="primary",
            generated_at="2026-07-18T00:00:00Z",
            worker_pid=1234,
            peak_memory_bytes=4096,
        )
        for task in screening_cell_tasks()
    )
    return combine_cell_executions(cells, governance_only=True)


def passing_gate_rows() -> list[dict[str, object]]:
    rows = [dict(row) for row in fixture_execution().replications]
    for row in rows:
        row["scorable"] = 1
        row["at_least_one_converged_start"] = 1
        row["selected_objective_trace_nonincreasing"] = 1
        row["w_alt_interp_available"] = 1
        row["w_alt_family_available"] = 1
        row["observed_topology_prediction_rmse"] = 0.8
        row["w_ref_raw_response_error_mean"] = 0.8
        for endpoint in ("w_alt_interp", "w_alt_family"):
            row[f"{endpoint}_operator_relative_error_mean"] = 0.5
            row[f"{endpoint}_response_zero_ratio_mean"] = 0.5
            row[f"{endpoint}_raw_response_error_mean"] = (
                0.8 if row["method"] == "dw_joint_tucker333" else 1.0
            )
    return rows


def set_candidate_metric(
    rows: list[dict[str, object]],
    suffix: str,
    value: float,
) -> None:
    for row in rows:
        if row["method"] == "dw_joint_tucker333":
            row[suffix] = value


def gate_conditions(rows: list[dict[str, object]]) -> tuple[dict[str, bool], ...]:
    verdict = evaluate_screening_gate(rows, config=R006EConfig())
    return tuple(cell["conditions"] for cell in verdict["cells"])


def run_fifo_attack(call, fifo: Path) -> tuple[bool, BaseException | None]:
    results: queue.Queue[BaseException | None] = queue.Queue()

    def invoke() -> None:
        try:
            call()
        except BaseException as exc:
            results.put(exc)
        else:
            results.put(None)

    worker = threading.Thread(target=invoke, daemon=True)
    worker.start()
    worker.join(0.5)
    blocked = worker.is_alive()
    if blocked:
        writer = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
        os.close(writer)
        fifo.unlink()
        fifo.write_bytes(b"unblock")
        worker.join(2.0)
    if worker.is_alive():
        raise AssertionError("FIFO attack worker did not terminate")
    return blocked, results.get_nowait()


def canonical_json_document(value: dict[str, object]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def fixture_metadata() -> RoleMetadata:
    return RoleMetadata(
        decision_id="task5-fixture",
        attempt_id=ATTEMPT_ID,
        role="primary",
        pair_claim_sha256="a" * 64,
        role_start_sha256="b" * 64,
        construction_sha256="c" * 64,
        config_sha256="d" * 64,
        candidate_sha256="e" * 64,
        provenance_sha256="f" * 64,
        started_at="2026-07-18T00:00:00Z",
        finished_at="2026-07-18T00:01:00Z",
        generated_at="2026-07-18T00:01:00Z",
    )


class ScreeningOutputsV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.execution = fixture_execution()

    def test_replication_csv_is_canonical_and_round_trips_exact_identities(self) -> None:
        payload = serialize_replication_csv(self.execution)
        self.assertEqual(
            payload.splitlines()[0].decode("utf-8"),
            ",".join(FORMAL_REPLICATION_FIELDS),
        )
        self.assertNotIn(b"\r", payload)
        self.assertTrue(payload.endswith(b"\n"))
        parsed = parse_replication_csv(payload)
        self.assertEqual(
            tuple(
                (row["seed"], row["rho"], row["a3"], row["eta"], row["method"])
                for row in parsed
            ),
            REPLICATION_IDENTITIES,
        )

    def test_operational_jsonl_is_canonical_and_shares_exact_identities(self) -> None:
        pairs = (
            (serialize_diagnostic_jsonl, parse_diagnostic_jsonl),
            (serialize_resource_jsonl, parse_resource_jsonl),
            (serialize_row_journal_jsonl, parse_row_journal_jsonl),
        )
        for serialize, parse in pairs:
            with self.subTest(serializer=serialize.__name__):
                payload = serialize(self.execution)
                self.assertNotIn(b"\r", payload)
                self.assertTrue(payload.endswith(b"\n"))
                records = parse(payload)
                self.assertEqual(
                    tuple(
                        (
                            row["seed"], row["rho"], row["a3"],
                            row["eta"], row["method"],
                        )
                        for row in records
                    ),
                    REPLICATION_IDENTITIES,
                )

    def test_production_builders_have_no_public_gate_adapter(self) -> None:
        for builder in (build_summary_rows, build_role_artifacts):
            with self.subTest(builder=builder.__name__):
                parameters = inspect.signature(builder).parameters
                self.assertNotIn("gate_adapter", parameters)
                self.assertIn("config", parameters)

    def test_native_gate_exact_flags_and_strict_unit_boundaries(self) -> None:
        baseline = passing_gate_rows()
        self.assertTrue(all(c["availability"] for c in gate_conditions(baseline)))
        self.assertTrue(all(c["finite_and_converged"] for c in gate_conditions(baseline)))

        unavailable = passing_gate_rows()
        unavailable[0]["w_alt_interp_available"] = 0
        self.assertFalse(gate_conditions(unavailable)[0]["availability"])
        unscorable = passing_gate_rows()
        unscorable[0]["scorable"] = 0
        self.assertFalse(gate_conditions(unscorable)[0]["finite_and_converged"])

        for gate, suffix in (
            ("operator_relative_error", "operator_relative_error_mean"),
            ("response_zero_ratio", "response_zero_ratio_mean"),
        ):
            exact = passing_gate_rows()
            below = passing_gate_rows()
            for endpoint in ("w_alt_interp", "w_alt_family"):
                set_candidate_metric(exact, f"{endpoint}_{suffix}", 1.0)
                set_candidate_metric(
                    below,
                    f"{endpoint}_{suffix}",
                    math.nextafter(1.0, -math.inf),
                )
            with self.subTest(gate=gate, boundary="exact"):
                self.assertTrue(all(not c[gate] for c in gate_conditions(exact)))
            with self.subTest(gate=gate, boundary="just-below"):
                self.assertTrue(all(c[gate] for c in gate_conditions(below)))

    def test_native_gate_relative_improvement_adjacent_float_boundary(self) -> None:
        literal = passing_gate_rows()
        above = passing_gate_rows()
        literal_ratio = 0.9
        first_lower_ratio = math.nextafter(literal_ratio, -math.inf)
        self.assertLess(1.0 - literal_ratio, 0.1)
        self.assertGreater(1.0 - first_lower_ratio, 0.1)
        for endpoint in ("w_alt_interp", "w_alt_family"):
            set_candidate_metric(
                literal, f"{endpoint}_raw_response_error_mean", literal_ratio
            )
            set_candidate_metric(
                above, f"{endpoint}_raw_response_error_mean", first_lower_ratio
            )
        # The gate freezes 1-ratio arithmetic: literal 9/10 lands below 0.10.
        for gate in ("paired_improvement", "worst_endpoint_improvement"):
            with self.subTest(gate=gate, side="below"):
                self.assertTrue(all(not c[gate] for c in gate_conditions(literal)))
            with self.subTest(gate=gate, side="above"):
                self.assertTrue(all(c[gate] for c in gate_conditions(above)))

    def test_native_gate_joint_win_accepts_exactly_eight_of_ten(self) -> None:
        rows = passing_gate_rows()
        candidate_rows = [
            row for row in rows if row["method"] == "dw_joint_tucker333"
        ]
        losing_seeds = {240108, 240109}
        for row in candidate_rows:
            value = 1.2 if row["seed"] in losing_seeds else 0.8
            for endpoint in ("w_alt_interp", "w_alt_family"):
                row[f"{endpoint}_raw_response_error_mean"] = value
        self.assertTrue(all(c["joint_win_rate"] for c in gate_conditions(rows)))

        seven_wins = [dict(row) for row in rows]
        for row in seven_wins:
            if row["method"] == "dw_joint_tucker333" and row["seed"] == 240107:
                for endpoint in ("w_alt_interp", "w_alt_family"):
                    row[f"{endpoint}_raw_response_error_mean"] = 1.2
        self.assertTrue(
            all(not c["joint_win_rate"] for c in gate_conditions(seven_wins))
        )

    def test_native_gate_guardrails_accept_exact_105_percent(self) -> None:
        for gate, key in (
            ("observed_rmse_guardrail", "observed_topology_prediction_rmse"),
            ("w_ref_guardrail", "w_ref_raw_response_error_mean"),
        ):
            exact = passing_gate_rows()
            above = passing_gate_rows()
            set_candidate_metric(exact, key, 1.05)
            set_candidate_metric(above, key, math.nextafter(1.05, math.inf))
            for row in exact:
                if row["method"] != "dw_joint_tucker333":
                    row[key] = 1.0
            for row in above:
                if row["method"] != "dw_joint_tucker333":
                    row[key] = 1.0
            with self.subTest(gate=gate, side="exact"):
                self.assertTrue(all(c[gate] for c in gate_conditions(exact)))
            with self.subTest(gate=gate, side="above"):
                self.assertTrue(all(not c[gate] for c in gate_conditions(above)))

    def test_summary_uses_native_gate_and_freezes_exact_rows(self) -> None:
        summary = build_summary_rows(self.execution, config=R006EConfig())
        self.assertEqual(summary.status, "FAIL")
        self.assertTrue(summary.identity_completeness)
        self.assertEqual(len(summary.rows), 8)
        self.assertEqual(tuple(summary.rows[0]), SUMMARY_ROW_FIELDS)
        self.assertEqual(summary.rows[0]["audit_values_json"], "{}")

    def test_role_bundle_is_exact_exclusive_and_separates_science_from_operations(self) -> None:
        artifacts = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        self.assertEqual(tuple(artifacts.files), PUBLICATION_ORDER)
        self.assertEqual(
            tuple(ROLE_FILE_NAMES[name] for name in PUBLICATION_ORDER),
            (
                "screening_row_journal.jsonl",
                "screening_replications.csv",
                "screening_diagnostics.jsonl",
                "screening_resources.jsonl",
                "screening_summary.csv",
                "screening_results.json",
                "screening_terminal.json",
                "screening_manifest.json",
            ),
        )
        result = json.loads(artifacts.files["result"])
        self.assertEqual(tuple(result), SCIENTIFIC_RESULT_FIELDS)
        self.assertEqual(result["status"], "FAIL")
        self.assertNotIn("diagnostic", " ".join(result))
        manifest = json.loads(artifacts.files["manifest"])
        self.assertEqual(tuple(manifest), MANIFEST_FIELDS)
        self.assertEqual(manifest["replication_count"], 320)
        self.assertEqual(manifest["diagnostic_count"], 320)
        self.assertEqual(manifest["resource_count"], 320)
        self.assertEqual(manifest["row_journal_count"], 320)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = publish_role_artifacts(root, artifacts)
            self.assertEqual(snapshot.published_names, PUBLICATION_ORDER)
            self.assertEqual(
                tuple(path.name for path in snapshot.paths),
                tuple(ROLE_FILE_NAMES[name] for name in PUBLICATION_ORDER),
            )
            try:
                verified = verify_published_role(snapshot, config=R006EConfig())
                self.assertEqual(tuple(verified), PUBLICATION_ORDER)
                with self.assertRaises(FileExistsError):
                    publish_role_artifacts(root, artifacts)
            finally:
                snapshot.close()

    def test_stable_reread_rejects_mutation_and_replacement_without_cleanup(self) -> None:
        artifacts = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        drift_names = (
            "replication", "summary", "result",
            "diagnostic", "resource", "row_journal",
        )
        for mode in ("mutate", "replace"):
            for name in drift_names:
                with (
                    self.subTest(mode=mode, name=name),
                    tempfile.TemporaryDirectory() as directory,
                ):
                    snapshot = publish_role_artifacts(Path(directory), artifacts)
                    target = Path(directory) / ROLE_FILE_NAMES[name]
                    if mode == "mutate":
                        target.write_bytes(target.read_bytes() + b"drift")
                    else:
                        replacement = Path(directory) / "replacement.tmp"
                        replacement.write_bytes(target.read_bytes())
                        os.replace(replacement, target)
                    with self.assertRaisesRegex(
                        OutputIntegrityError, "changed|drift"
                    ):
                        verify_published_role(snapshot, config=R006EConfig())
                    self.assertTrue(all(path.exists() for path in snapshot.paths))
                    snapshot.close()

    def test_root_swap_during_link_never_publishes_into_replacement_root(self) -> None:
        artifacts = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "role"
            displaced = parent / "displaced"
            root.mkdir()
            real_link = os.link
            swapped = False

            def swap_then_link(src, dst, **kwargs):
                nonlocal swapped
                if not swapped:
                    root.rename(displaced)
                    root.mkdir()
                    swapped = True
                return real_link(src, dst, **kwargs)

            with patch.object(outputs_v2.os, "link", side_effect=swap_then_link):
                with self.assertRaisesRegex(OutputIntegrityError, "root|binding|changed"):
                    publish_role_artifacts(root, artifacts)
            self.assertEqual(tuple(root.iterdir()), ())

    def test_same_root_replacement_immediately_after_link_is_rejected(self) -> None:
        artifacts = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_link = os.link
            replaced = False

            def replace_after_link(src, dst, **kwargs):
                nonlocal replaced
                result = real_link(src, dst, **kwargs)
                if not replaced:
                    target = root / dst
                    replacement = root / "same-bytes.tmp"
                    replacement.write_bytes(target.read_bytes())
                    os.replace(replacement, target)
                    replaced = True
                return result

            with patch.object(outputs_v2.os, "link", side_effect=replace_after_link):
                with self.assertRaisesRegex(
                    OutputIntegrityError, "binding|changed|inode|fingerprint"
                ):
                    publish_role_artifacts(root, artifacts)

    def test_fifo_replacement_after_link_fails_without_blocking(self) -> None:
        artifacts = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fifo = root / ROLE_FILE_NAMES[PUBLICATION_ORDER[0]]
            real_link = os.link
            replaced = False

            def replace_with_fifo(src, dst, **kwargs):
                nonlocal replaced
                result = real_link(src, dst, **kwargs)
                if not replaced:
                    (root / dst).unlink()
                    os.mkfifo(root / dst)
                    replaced = True
                return result

            with patch.object(outputs_v2.os, "link", side_effect=replace_with_fifo):
                blocked, failure = run_fifo_attack(
                    lambda: publish_role_artifacts(root, artifacts), fifo
                )
            self.assertFalse(blocked, "destination FIFO open blocked publication")
            self.assertIsInstance(failure, OutputIntegrityError)

    def test_fifo_replacement_before_stable_reread_fails_without_blocking(self) -> None:
        artifacts = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = publish_role_artifacts(root, artifacts)
            fifo = root / ROLE_FILE_NAMES["replication"]
            fifo.unlink()
            os.mkfifo(fifo)
            try:
                blocked, failure = run_fifo_attack(
                    lambda: verify_published_role(snapshot, config=R006EConfig()), fifo
                )
                self.assertFalse(blocked, "published FIFO open blocked verification")
                self.assertIsInstance(failure, OutputIntegrityError)
            finally:
                snapshot.close()

    def test_verification_rejects_stale_row_journal_after_raw_hash_rewrite(self) -> None:
        original = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        files = dict(original.files)
        diagnostic_lines = files["diagnostic"].splitlines()
        diagnostic = json.loads(diagnostic_lines[0])
        diagnostic["generated_at"] = "2026-07-18T00:00:01Z"
        diagnostic_lines[0] = canonical_json_document(diagnostic).rstrip(b"\n")
        files["diagnostic"] = b"\n".join(diagnostic_lines) + b"\n"

        terminal = json.loads(files["terminal"])
        terminal["diagnostics_sha256"] = hashlib.sha256(files["diagnostic"]).hexdigest()
        files["terminal"] = canonical_json_document(terminal)
        manifest = json.loads(files["manifest"])
        manifest["diagnostics_sha256"] = terminal["diagnostics_sha256"]
        manifest["terminal_sha256"] = hashlib.sha256(files["terminal"]).hexdigest()
        files["manifest"] = canonical_json_document(manifest)
        artifacts = RoleArtifacts(
            files=MappingProxyType({name: files[name] for name in PUBLICATION_ORDER})
        )

        with tempfile.TemporaryDirectory() as directory:
            snapshot = publish_role_artifacts(Path(directory), artifacts)
            try:
                with self.assertRaisesRegex(OutputIntegrityError, "journal.*hash|row.*hash"):
                    verify_published_role(snapshot, config=R006EConfig())
            finally:
                snapshot.close()

    def test_verification_rejects_coherent_pass_forgery_of_failed_evidence(self) -> None:
        original = build_role_artifacts(
            self.execution,
            config=R006EConfig(),
            metadata=fixture_metadata(),
        )
        files = dict(original.files)
        summaries = [
            dict(row) for row in outputs_v2._parse_summary_csv(files["summary"])
        ]
        for row in summaries:
            row["passed"] = True
            for field in SUMMARY_FIELDS:
                row[field] = True
            row["failed_conditions_json"] = "[]"
            row["audit_values_json"] = "{}"
        files["summary"] = outputs_v2._serialize_csv(summaries, SUMMARY_ROW_FIELDS)

        result = json.loads(files["result"])
        result["status"] = "PASS"
        replications = [
            dict(row) for row in parse_replication_csv(files["replication"])
        ]
        semantic = outputs_v2.recompute_scientific_digests(
            {"replication": replications, "summary": summaries, "result": result}
        )
        result["semantic_replication_sha256"] = semantic["replication"]
        result["semantic_summary_sha256"] = semantic["summary"]
        files["result"] = canonical_json_document(result)

        terminal = json.loads(files["terminal"])
        terminal["status"] = "PASS"
        terminal["summary_sha256"] = hashlib.sha256(files["summary"]).hexdigest()
        terminal["result_sha256"] = hashlib.sha256(files["result"]).hexdigest()
        files["terminal"] = canonical_json_document(terminal)

        manifest = json.loads(files["manifest"])
        manifest["status"] = "PASS"
        manifest["summary_sha256"] = terminal["summary_sha256"]
        manifest["result_sha256"] = terminal["result_sha256"]
        manifest["terminal_sha256"] = hashlib.sha256(files["terminal"]).hexdigest()
        files["manifest"] = canonical_json_document(manifest)
        artifacts = RoleArtifacts(
            files=MappingProxyType({name: files[name] for name in PUBLICATION_ORDER})
        )

        with tempfile.TemporaryDirectory() as directory:
            snapshot = publish_role_artifacts(Path(directory), artifacts)
            try:
                with self.assertRaisesRegex(
                    OutputIntegrityError, "native gate|summary.*drift|gate.*drift"
                ):
                    verify_published_role(snapshot, config=R006EConfig())
            finally:
                snapshot.close()

    def test_strict_json_rejects_nonstring_duplicate_and_nonfinite_values(self) -> None:
        payload = serialize_diagnostic_jsonl(self.execution)
        lines = payload.splitlines()
        duplicate = lines[0][:-1] + b',"seed":240100}\n' + b"\n".join(lines[1:]) + b"\n"
        with self.assertRaisesRegex(OutputIntegrityError, "duplicate"):
            parse_diagnostic_jsonl(duplicate)
        nonfinite = lines[0][:-1] + b',"extra":NaN}\n' + b"\n".join(lines[1:]) + b"\n"
        with self.assertRaisesRegex(OutputIntegrityError, "non-finite"):
            parse_diagnostic_jsonl(nonfinite)


if __name__ == "__main__":
    unittest.main()
