import json
import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.experiments import r006c_endpoint_aware_experiment as experiment
from scripts.experiments.r006c_endpoint_protocol import METHODS, R006CConfig


class R006CEndpointAwareExperimentTest(unittest.TestCase):
    @staticmethod
    def config():
        return R006CConfig(
            n=8,
            t_len=48,
            window=24,
            true_rank=8,
            cp_iterations=3,
            cp_starts=1,
            fused_penalties=(0.10,),
            fused_max_iterations=100,
        )

    def test_small_replication_returns_exactly_nine_methods(self):
        rows = experiment.run_replication(
            config=self.config(),
            layer="matched",
            rho=0.80,
            a3=0.10,
            eta=0.15,
            seed=240100,
        )
        self.assertEqual(len(rows), 9)
        self.assertEqual({row["method"] for row in rows}, set(METHODS))
        self.assertTrue(all(row["failure"] == 0 for row in rows))
        self.assertEqual(
            len(
                {
                    (
                        row["layer"], row["rho"], row["a3"], row["eta"],
                        row["seed"], row["method"],
                    )
                    for row in rows
                }
            ),
            9,
        )

    def test_replication_rows_include_layer_and_construction_diagnostics(self):
        rows = experiment.run_replication(
            config=self.config(),
            layer="native",
            rho=0.80,
            a3=0.10,
            eta=0.15,
            seed=240100,
        )
        for row in rows:
            self.assertIn("design_gram_min_eigenvalue", row)
            self.assertIn("design_gram_max_eigenvalue", row)
            self.assertIn("design_gram_condition", row)
            self.assertIsInstance(
                row["innovation_to_state_variance_ratio"], float
            )
            self.assertLess(row["true_radius_max_abs_error"], 1e-10)
            self.assertLess(row["anchor_identity_max_abs_error"], 1e-10)
            self.assertLess(row["a3_calibration_abs_error"], 1e-6)

    def test_numerical_failure_returns_nine_explicit_failure_rows(self):
        invalid = replace(self.config(), window=12)
        rows = experiment.run_replication(
            config=invalid,
            layer="matched",
            rho=0.80,
            a3=0.10,
            eta=0.15,
            seed=240100,
        )
        self.assertEqual(len(rows), 9)
        self.assertEqual({row["method"] for row in rows}, set(METHODS))
        self.assertTrue(all(row["failure"] == 1 for row in rows))
        self.assertTrue(all(row["failure_reason"] for row in rows))

    def test_smoke_cannot_return_full_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            payload = experiment.run_grid(
                config=self.config(),
                layers=("matched",),
                rhos=(0.80,),
                a3_values=(0.10,),
                eta_values=(0.15,),
                seeds=(240100,),
                workers=1,
                output_dir=output_dir,
                smoke=True,
            )
            self.assertIn(payload["status"], {"SMOKE_PASS", "SMOKE_FAIL"})
            self.assertNotEqual(payload["status"], "PASS")
            self.assertEqual(payload["row_count"], 9)
            self.assertTrue((output_dir / "r006c_replications.csv").exists())
            self.assertTrue((output_dir / "r006c_summary.csv").exists())
            self.assertTrue((output_dir / "r006c_results.json").exists())
            self.assertTrue((output_dir / "r006c_results.md").exists())
            report = (output_dir / "r006c_results.md").read_text(encoding="utf-8")
            self.assertIn("## Required Cell Gates", report)
            self.assertIn("anchor_split_cp3", report)
            self.assertIn("anchor_split_tucker333", report)
            self.assertIn("W_ref", report)
            self.assertIn("W_alt_main", report)
            self.assertIn("worst endpoint", report)
            stored = json.loads(
                (output_dir / "r006c_results.json").read_text(encoding="utf-8")
            )
            self.assertEqual(stored["row_count"], 9)
            self.assertRegex(
                stored["provenance"]["protocol_sha256"], r"^[0-9a-f]{64}$"
            )
            self.assertEqual(len(stored["provenance"]["code_sha256"]), 7)

    def test_construction_gate_records_protocol_code_and_leakage_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            artifact = experiment.write_construction_gate(
                config=self.config(), output_dir=output_dir
            )
            self.assertEqual(artifact["status"], "PASS")
            self.assertRegex(
                artifact["provenance"]["protocol_sha256"], r"^[0-9a-f]{64}$"
            )
            self.assertRegex(
                artifact["provenance"]["correction_addendum_sha256"],
                r"^[0-9a-f]{64}$",
            )
            self.assertEqual(len(artifact["provenance"]["code_sha256"]), 7)
            self.assertTrue(artifact["checks"]["heldout_fit_invariance"])
            self.assertTrue(artifact["checks"]["heldout_selection_invariance"])
            self.assertTrue(artifact["checks"]["adaptive_ridge_scale_invariance"])
            self.assertTrue(artifact["checks"]["causal_fused_validation"])
            self.assertTrue(
                (output_dir / "construction_gate_preoutcome.json").exists()
            )
            experiment.verify_construction_gate(
                config=self.config(), output_dir=output_dir
            )

    def test_formal_run_refuses_hash_mismatch_before_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            artifact = experiment.write_construction_gate(
                config=self.config(), output_dir=output_dir
            )
            artifact["provenance"]["protocol_sha256"] = "0" * 64
            (output_dir / "construction_gate_preoutcome.json").write_text(
                json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                experiment.run_grid(
                    config=self.config(),
                    layers=("matched",),
                    rhos=(0.80,),
                    a3_values=(0.10,),
                    eta_values=(0.15,),
                    seeds=(240100,),
                    workers=1,
                    output_dir=output_dir,
                    smoke=False,
                )
            self.assertFalse((output_dir / "r006c_replications.csv").exists())

    def test_duplicate_comparison_ignores_runtime_but_detects_numeric_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = root / "primary"
            repeat = root / "repeat"
            arguments = {
                "config": self.config(),
                "layers": ("matched",),
                "rhos": (0.80,),
                "a3_values": (0.10,),
                "eta_values": (0.15,),
                "seeds": (240100,),
                "workers": 1,
                "smoke": True,
            }
            experiment.run_grid(output_dir=primary, **arguments)
            experiment.run_grid(output_dir=repeat, **arguments)
            comparison = experiment.compare_run_directories(primary, repeat)
            self.assertEqual(comparison["status"], "PASS")
            self.assertEqual(comparison["non_runtime_field_differences"], 0)
            self.assertTrue(
                (primary / "r006c_duplicate_comparison.json").exists()
            )

            csv_path = repeat / "r006c_replications.csv"
            with csv_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[0]["w_ref_raw_response_error_mean"] = str(
                float(rows[0]["w_ref_raw_response_error_mean"]) + 0.1
            )
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            changed = experiment.compare_run_directories(primary, repeat)
            self.assertEqual(changed["status"], "FAIL")
            self.assertGreater(changed["non_runtime_field_differences"], 0)

    def test_cli_parser_exposes_frozen_execution_modes(self):
        parser = experiment.build_argument_parser()
        arguments = parser.parse_args(
            [
                "--construction-gate-only",
                "--workers", "4",
                "--output-dir", "primary",
            ]
        )
        self.assertTrue(arguments.construction_gate_only)
        self.assertEqual(arguments.workers, 4)
        self.assertEqual(arguments.output_dir, Path("primary"))
        comparison = parser.parse_args(
            ["--compare-to", "repeat", "--output-dir", "primary"]
        )
        self.assertEqual(comparison.compare_to, Path("repeat"))

    @staticmethod
    def passing_gate_rows(candidate_error=0.80):
        rows = []
        for layer in ("matched", "native"):
            for rho in (0.80, 0.95):
                for a3 in (0.10, 0.25):
                    for eta in (0.15, 0.45):
                        for seed in range(240100, 240110):
                            for method in (
                                "block_local",
                                "block_fused_tv",
                                "block_tucker333",
                                "anchor_split_cp3",
                                "anchor_split_tucker333",
                            ):
                                error = (
                                    candidate_error
                                    if method == "anchor_split_cp3"
                                    else 1.10
                                    if method == "anchor_split_tucker333"
                                    else 1.00
                                )
                                rows.append(
                                    {
                                        "layer": layer,
                                        "rho": rho,
                                        "a3": a3,
                                        "eta": eta,
                                        "seed": seed,
                                        "method": method,
                                        "failure": 0,
                                        "w_ref_available": 1,
                                        "w_alt_main_available": 1,
                                        "w_ref_operator_relative_error_mean": 0.50,
                                        "w_alt_main_operator_relative_error_mean": 0.50,
                                        "w_ref_response_zero_ratio_mean": 0.50,
                                        "w_alt_main_response_zero_ratio_mean": 0.50,
                                        "w_ref_raw_response_error_mean": error,
                                        "w_alt_main_raw_response_error_mean": error,
                                    }
                                )
        return rows

    @staticmethod
    def row_matches(row, *, candidate="anchor_split_cp3", **cell):
        return row["method"] == candidate and all(
            row[key] == value for key, value in cell.items()
        )

    def test_exact_ten_percent_improvement_passes_all_cells(self):
        checks = experiment.evaluate_promotion_gate(
            self.passing_gate_rows(candidate_error=0.90),
            seeds=tuple(range(240100, 240110)),
        )
        candidate = checks["candidates"]["anchor_split_cp3"]
        self.assertTrue(candidate["pass"])
        self.assertEqual(candidate["passed_cells"], 16)
        self.assertEqual(checks["promotion_candidates"], ["anchor_split_cp3"])

    def test_eight_of_ten_joint_wins_passes_but_seven_fails(self):
        for wins, expected in ((8, True), (7, False)):
            rows = self.passing_gate_rows()
            for row in rows:
                if self.row_matches(
                    row,
                    layer="matched",
                    rho=0.80,
                    a3=0.10,
                    eta=0.15,
                ) and row["seed"] >= 240100 + wins:
                    row["w_ref_raw_response_error_mean"] = 1.01
            checks = experiment.evaluate_promotion_gate(
                rows, seeds=tuple(range(240100, 240110))
            )
            first_cell = checks["candidates"]["anchor_split_cp3"][
                "required_cells"
            ][0]
            self.assertEqual(first_cell["endpoints"]["w_ref"]["pass"], expected)

    def test_missing_seed_or_unavailable_main_endpoint_fails_cell(self):
        rows = self.passing_gate_rows()
        rows = [
            row for row in rows
            if not self.row_matches(
                row,
                layer="matched", rho=0.80, a3=0.10, eta=0.15,
            ) or row["seed"] != 240109
        ]
        checks = experiment.evaluate_promotion_gate(
            rows, seeds=tuple(range(240100, 240110))
        )
        self.assertFalse(
            checks["candidates"]["anchor_split_cp3"]["required_cells"][0]["pass"]
        )

        rows = self.passing_gate_rows()
        target = next(
            row for row in rows
            if self.row_matches(
                row,
                layer="matched", rho=0.80, a3=0.10, eta=0.15,
            )
        )
        target["w_alt_main_available"] = 0
        checks = experiment.evaluate_promotion_gate(
            rows, seeds=tuple(range(240100, 240110))
        )
        self.assertFalse(
            checks["candidates"]["anchor_split_cp3"]["required_cells"][0]["pass"]
        )

    def test_operator_and_zero_ratio_boundaries_are_strict(self):
        for field in (
            "w_ref_operator_relative_error_mean",
            "w_ref_response_zero_ratio_mean",
        ):
            rows = self.passing_gate_rows()
            for row in rows:
                if self.row_matches(
                    row,
                    layer="matched", rho=0.80, a3=0.10, eta=0.15,
                ):
                    row[field] = 1.0
            checks = experiment.evaluate_promotion_gate(
                rows, seeds=tuple(range(240100, 240110))
            )
            self.assertFalse(
                checks["candidates"]["anchor_split_cp3"]["required_cells"][0]["pass"]
            )

    def test_cellwise_switching_cannot_promote_either_candidate(self):
        rows = self.passing_gate_rows()
        for row in rows:
            cp_first_cell = self.row_matches(
                row,
                candidate="anchor_split_cp3",
                layer="matched", rho=0.80, a3=0.10, eta=0.15,
            )
            tucker_other_cells = (
                row["method"] == "anchor_split_tucker333" and not (
                    row["layer"] == "matched" and row["rho"] == 0.80
                    and row["a3"] == 0.10 and row["eta"] == 0.15
                )
            )
            if cp_first_cell:
                row["w_ref_raw_response_error_mean"] = 1.10
                row["w_alt_main_raw_response_error_mean"] = 1.10
            if row["method"] == "anchor_split_tucker333" and not tucker_other_cells:
                row["w_ref_raw_response_error_mean"] = 0.80
                row["w_alt_main_raw_response_error_mean"] = 0.80
            elif tucker_other_cells:
                row["w_ref_raw_response_error_mean"] = 1.10
                row["w_alt_main_raw_response_error_mean"] = 1.10
        checks = experiment.evaluate_promotion_gate(
            rows, seeds=tuple(range(240100, 240110))
        )
        self.assertEqual(checks["promotion_candidates"], [])

    @staticmethod
    def full_grid_rows():
        rows = []
        for layer in ("matched", "native"):
            for rho in (0.80, 0.95):
                for a3 in (0.10, 0.25):
                    for eta in (0.02, 0.15, 0.45):
                        for seed in range(240100, 240110):
                            for method in METHODS:
                                candidate_error = (
                                    0.80 if method == "anchor_split_cp3" else
                                    1.10 if method == "anchor_split_tucker333" else
                                    1.00
                                )
                                alternative_available = (
                                    method != "collapsed_ref_tucker333"
                                )
                                row = {
                                    "layer": layer,
                                    "rho": rho,
                                    "a3": a3,
                                    "eta": eta,
                                    "seed": seed,
                                    "method": method,
                                    "failure": 0,
                                    "failure_reason": None,
                                    "w_ref_available": 1,
                                    "w_alt_main_available": int(alternative_available),
                                    "w_alt_stress_available": int(alternative_available),
                                    "w_ref_operator_relative_error_mean": 0.50,
                                    "w_ref_response_zero_ratio_mean": 0.50,
                                    "w_ref_raw_response_error_mean": candidate_error,
                                    "w_ref_stability_qualified_error_mean": candidate_error,
                                    "w_ref_projected_sensitivity_error_mean": 99.0,
                                    "true_radius_max_abs_error": 0.0,
                                    "query_frobenius_max_abs_error": 0.0,
                                    "anchor_identity_max_abs_error": 0.0,
                                    "a3_calibration_abs_error": 0.0,
                                    "observed_radius_max": 0.96,
                                    "main_holdout_mixture_max_abs_error": 0.0,
                                    "stress_topology_row_sum_max_abs_error": 0.0,
                                }
                                if alternative_available:
                                    row.update(
                                        {
                                            "w_alt_main_operator_relative_error_mean": 0.50,
                                            "w_alt_main_response_zero_ratio_mean": 0.50,
                                            "w_alt_main_raw_response_error_mean": candidate_error,
                                            "w_alt_main_stability_qualified_error_mean": candidate_error,
                                            "w_alt_main_projected_sensitivity_error_mean": 99.0,
                                            "w_alt_stress_operator_relative_error_mean": 99.0,
                                            "w_alt_stress_response_zero_ratio_mean": 99.0,
                                            "w_alt_stress_raw_response_error_mean": 99.0,
                                            "w_alt_stress_stability_qualified_error_mean": None,
                                            "w_alt_stress_projected_sensitivity_error_mean": 0.0,
                                        }
                                    )
                                else:
                                    for endpoint in ("w_alt_main", "w_alt_stress"):
                                        row.update(
                                            {
                                                f"{endpoint}_operator_relative_error_mean": None,
                                                f"{endpoint}_response_zero_ratio_mean": None,
                                                f"{endpoint}_raw_response_error_mean": None,
                                                f"{endpoint}_stability_qualified_error_mean": None,
                                                f"{endpoint}_projected_sensitivity_error_mean": None,
                                            }
                                        )
                                rows.append(row)
        return rows

    def test_full_grid_gate_passes_only_with_declared_grid_and_fixed_candidate(self):
        checks = experiment.evaluate_grid_gate(
            self.full_grid_rows(),
            config=R006CConfig(),
            layers=("matched", "native"),
            rhos=(0.80, 0.95),
            a3_values=(0.10, 0.25),
            eta_values=(0.02, 0.15, 0.45),
            seeds=tuple(range(240100, 240110)),
            smoke=False,
        )
        self.assertEqual(checks["status"], "PASS")
        self.assertTrue(checks["completion"]["full_grid_declared"])
        self.assertEqual(
            checks["promotion"]["promotion_candidates"],
            ["anchor_split_cp3"],
        )

    def test_weak_separation_stress_and_projected_metrics_cannot_rescue_failure(self):
        rows = self.full_grid_rows()
        for row in rows:
            if self.row_matches(
                row,
                layer="matched", rho=0.80, a3=0.10, eta=0.15,
            ):
                row["w_ref_raw_response_error_mean"] = 1.10
                row["w_ref_projected_sensitivity_error_mean"] = 0.0
        checks = experiment.evaluate_grid_gate(
            rows,
            config=R006CConfig(),
            layers=("matched", "native"),
            rhos=(0.80, 0.95),
            a3_values=(0.10, 0.25),
            eta_values=(0.02, 0.15, 0.45),
            seeds=tuple(range(240100, 240110)),
            smoke=False,
        )
        self.assertEqual(checks["status"], "FAIL")
        self.assertEqual(checks["promotion"]["promotion_candidates"], [])

    def test_partial_non_smoke_grid_cannot_pass(self):
        rows = [row for row in self.full_grid_rows() if row["eta"] != 0.02]
        checks = experiment.evaluate_grid_gate(
            rows,
            config=R006CConfig(),
            layers=("matched", "native"),
            rhos=(0.80, 0.95),
            a3_values=(0.10, 0.25),
            eta_values=(0.15, 0.45),
            seeds=tuple(range(240100, 240110)),
            smoke=False,
        )
        self.assertEqual(checks["status"], "FAIL")
        self.assertFalse(checks["completion"]["full_grid_declared"])


if __name__ == "__main__":
    unittest.main()
