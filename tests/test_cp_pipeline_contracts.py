import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from scripts import run_cp_empirical_pipeline as pipeline
from scripts.natcs_design_contract import equationwise_ridge_fit


class ResponseSummaryContractTests(unittest.TestCase):
    def test_half_life_search_starts_at_first_peak(self):
        self.assertEqual(pipeline.half_life_pair([0.0, 1.0, 4.0, 2.0, 1.0]), 3.0)

    def test_half_life_is_horizon_censored_when_no_crossing_occurs(self):
        self.assertEqual(pipeline.half_life_pair([0.0, 1.0, 4.0, 3.0, 2.5]), 4.0)

    def test_signed_ratio_preserves_negative_denominator_sign(self):
        self.assertEqual(pipeline.signed_ratio_or_none(-1.0, -2.0), 0.5)
        self.assertIsNone(pipeline.signed_ratio_or_none(1.0, pipeline.EPS / 2.0))


class StabilityExclusionContractTests(unittest.TestCase):
    def _rank_deficient_inputs(self):
        dates = pipeline.pd.to_datetime(["2020-03-31", "2020-06-30", "2020-09-30"])
        rows = []
        for date_idx, date in enumerate(dates):
            for pair_idx, pair in enumerate(("A_B", "B_A")):
                rows.append(
                    {
                        "date": date,
                        "pair": pair,
                        "s_net_clip": float(date_idx + pair_idx),
                        # The full sample is identified by a post-boundary
                        # change, while the retained stable dates have no
                        # treatment variation and must be reported as NI.
                        "TC_relief": 0.0 if date_idx < 2 else float(pair_idx + 1),
                    }
                )
        panel = pipeline.pd.DataFrame(rows)
        aggregate = pipeline.pd.DataFrame(
            {
                "date": dates,
                "g_net": [0.1, 0.2, 0.3],
            }
        )
        stability = pipeline.pd.DataFrame(
            {
                "date": dates,
                "unstable": [0, 0, 1],
            }
        )
        return panel, aggregate, stability

    def test_stability_exclusion_reports_unidentified_regression(self):
        panel, aggregate, stability = self._rank_deficient_inputs()
        with self.assertRaisesRegex(ValueError, "full column rank"):
            pipeline.fit_panel(panel[panel["date"] < pipeline.pd.Timestamp("2020-09-30")])

        result = pipeline.fit_panel(
            panel[panel["date"] < pipeline.pd.Timestamp("2020-09-30")],
            allow_unidentified=True,
        )
        self.assertEqual(result["Status"], "not_identified")
        self.assertTrue(np.isnan(result["Coefficient"]))
        self.assertIn("collinear", result["Identification"])

        summary = pipeline.stability_exclusion_summary(panel, aggregate, aggregate, stability)
        stable = summary[
            (summary["Statistic"] == "Pair-level coefficient")
            & (summary["Sample"] == "Stable dates only")
        ].iloc[0]
        self.assertEqual(stable["Status"], "not_identified")
        self.assertTrue(np.isnan(float(stable["Value"])))


class LoadedDatasetContractTests(unittest.TestCase):
    def _base_panel(self):
        return {
            "dataset": "nyc_taxi",
            "Y": np.zeros((4, 2), dtype=float),
            "dates": list(np.array(["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30"], dtype="datetime64[ns]")),
            "unit_names": ["Zone-1", "Zone-2"],
            "girf_pair": ("Zone-1", "Zone-2"),
            "requested_girf_dates": ["2020-02-29", "2020-04-30"],
            "w_list": [np.zeros((2, 2), dtype=float) for _ in range(4)],
            "W_pre": np.zeros((2, 2), dtype=float),
            "df_bilateral": None,
            "df_tc": None,
            "level_panel": None,
            "acquisition_info": {},
        }

    def test_loaded_panel_schema_is_checked_before_output_reservation(self):
        panel = self._base_panel()
        panel["Y"] = np.array([1.0, 2.0])
        with self.assertRaisesRegex(ValueError, "Y.*two-dimensional"):
            pipeline._validate_loaded_dataset(panel, "nyc_taxi", p=2)

    def test_loaded_panel_rejects_nonmonotone_dates_and_duplicate_units(self):
        panel = self._base_panel()
        panel["dates"] = ["2020-02-29", "2020-01-31", "2020-03-31", "2020-04-30"]
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            pipeline._validate_loaded_dataset(panel, "nyc_taxi", p=2)

        panel = self._base_panel()
        panel["unit_names"] = ["Zone-1", "Zone-1"]
        with self.assertRaisesRegex(ValueError, "unique"):
            pipeline._validate_loaded_dataset(panel, "nyc_taxi", p=2)

    def test_loaded_nyc_topology_schema_is_checked(self):
        panel = self._base_panel()
        panel["w_list"] = panel["w_list"][:-1]
        with self.assertRaisesRegex(ValueError, "w_list"):
            pipeline._validate_loaded_dataset(panel, "nyc_taxi", p=2)

    def test_sha256_refuses_symlink_and_nonregular_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            regular = root / "regular"
            regular.write_bytes(b"fixture")
            link = root / "link"
            link.symlink_to(regular)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                pipeline._sha256(link)

            fifo = root / "fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(RuntimeError, "regular file"):
                pipeline._sha256(fifo)

    def test_nyc_tensor_builder_uses_authorized_bound_path(self):
        bound = Path("/authorized/nyc").resolve()
        other = Path("/mutable/nyc").resolve()
        calls = []

        def validated(dataset_dir=None):
            calls.append(dataset_dir)
            return bound, "fixture-commit", tuple(
                (f"yellow_taxi_trip_{year}.npz", "a" * 64) for year in range(2012, 2022)
            )

        with patch.object(pipeline, "_validated_nyc_taxi_source", side_effect=validated), patch.object(
            pipeline, "read_authorized_input_snapshot", return_value=b""
        ):
            # The source loader must be called with the authorized path before any
            # fixture bytes are decoded; the patched byte reader is never reached
            # in the current implementation once the path binding is violated.
            with self.assertRaises(Exception):
                pipeline._build_monthly_taxi_tensor({"nyc_upstream_commit": "fixture-commit", "nyc_dataset_dir": str(bound)})
        self.assertEqual(calls, [str(bound)])


class HelperImportTrustRootContractTests(unittest.TestCase):
    def test_trusted_import_roots_include_global_and_user_site_packages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            stdlib = root / "stdlib"
            global_site = root / "global-site-packages"
            user_site = root / "user-site-packages"

            with patch.object(
                pipeline.sysconfig,
                "get_paths",
                return_value={
                    "stdlib": str(stdlib),
                    "platstdlib": str(stdlib),
                    "purelib": str(global_site),
                    "platlib": str(global_site),
                },
            ), patch.object(
                pipeline.site,
                "getsitepackages",
                return_value=[str(global_site)],
            ), patch.object(
                pipeline.site,
                "getusersitepackages",
                return_value=str(user_site),
            ):
                trusted_roots = pipeline._trusted_helper_import_roots()

            self.assertEqual(trusted_roots, {stdlib, global_site, user_site})
            user_package_spec = SimpleNamespace(
                origin=str(user_site / "pandas" / "__init__.py"),
                submodule_search_locations=[str(user_site / "pandas")],
            )
            self.assertFalse(
                pipeline._helper_spec_uses_untrusted_code(
                    user_package_spec,
                    root / "helper",
                    trusted_roots,
                )
            )

    def test_current_installed_pandas_passes_the_restricted_import_guard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir).resolve()
            trusted_roots = pipeline._trusted_helper_import_roots()
            pandas_spec = pipeline._loaded_module_spec(pipeline.pd)

            self.assertFalse(
                pipeline._helper_spec_uses_untrusted_code(
                    pandas_spec,
                    repo,
                    trusted_roots,
                )
            )
            guarded_import = pipeline._helper_import_guard(repo, set(), trusted_roots)
            self.assertIs(guarded_import("pandas"), pipeline.pd)


class GlobalBootstrapContractTests(unittest.TestCase):
    def test_one_draw_uses_one_global_residual_index_path(self):
        y = np.arange(6, dtype=float).reshape(-1, 1)
        w_list = [np.zeros((1, 1)) for _ in range(len(y))]
        local_results = [
            {
                "t_idx": t,
                "c": np.zeros(1),
                "beta": np.zeros((1, 2)),
            }
            for t in range(2, len(y))
        ]
        rng = np.random.default_rng(19)

        y_star, sampled_indices = pipeline.simulate_global_bootstrap_panel(
            y,
            w_list,
            local_results,
            rng,
            block_size=2,
            p=1,
            window=2,
        )

        residuals = y[2:] - y[2:].mean(axis=0)
        np.testing.assert_allclose(y_star[:2], y[:2])
        np.testing.assert_allclose(y_star[2:], residuals[sampled_indices])
        self.assertEqual(len(sampled_indices), len(y) - 2)


class ResponseBackendContractTests(unittest.TestCase):
    def test_nyc_local_response_backend_avoids_rcep_globals(self):
        unit_names = ["Zone-1", "Zone-2"]
        date = pipeline.pd.Timestamp("2020-01-31")
        cp_result = {
            "date": date,
            "A_list_cp": [np.diag([0.1, 0.2])],
            "B_list_cp": [np.diag([0.3, 0.4])],
            "Sigma": np.eye(2),
            "W_window": [np.array([[0.0, 1.0], [1.0, 0.0]])],
        }
        response_backend = (pipeline._local_moving_average_coefficients, pipeline._local_girf_one)

        def forbidden_global(*_args, **_kwargs):
            raise AssertionError("RCEP response helper must not be called for the NYC backend")

        with patch.object(
            pipeline, "moving_average_coefficients", side_effect=forbidden_global
        ) as global_moving_average, patch.object(
            pipeline, "girf_one", side_effect=forbidden_global
        ) as global_girf:
            pair_df, aggregate_df, girf_store = pipeline.build_pair_panel(
                [cp_result],
                None,
                horizon=2,
                W_mode="local",
                w_label="NYC local",
                unit_names=unit_names,
                girf_pair=("Zone-1", "Zone-2"),
                target_dates={date: "fixture-date"},
                response_backend=response_backend,
            )
            perturb_df = pipeline.top_exposure_propagation_perturbations(
                [cp_result],
                horizon=2,
                unit_names=unit_names,
                response_backend=response_backend,
            )

        global_moving_average.assert_not_called()
        global_girf.assert_not_called()
        self.assertFalse(pair_df.empty)
        self.assertEqual(len(aggregate_df), 1)
        self.assertIn("fixture-date", girf_store)
        self.assertEqual(len(perturb_df), 1)
        self.assertIn("g_net_delta", perturb_df.columns)


class ProductionEntryContractTests(unittest.TestCase):
    RCEP_INPUT_FIXTURE_FILES = (
        "master_quarterly_macro_2005_2024.csv",
        "master_quarterly_bilateral_2005_2024.csv",
    )

    def make_run_args(self, dataset="rcep", **overrides):
        values = {
            "dataset": dataset,
            "window": 40,
            "p": 2,
            "n_boot": 500,
            "block_size": 4,
            "cp_inits": 6,
            "cp_max_iter": 100,
            "cp_tol": 1e-6,
            "authorization": None,
            "authorization_sha256": None,
            "output_root": None,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def write_execution_authorization(
        self,
        path: Path,
        args,
        output_root: Path,
        *,
        helper_repo: Path | None = None,
        nyc_dataset_dir: Path | None = None,
        decision="AUTHORIZED",
        argv_overrides=None,
    ) -> str:
        args.output_root = str(output_root.resolve())
        argv = {
            "window": args.window,
            "p": args.p,
            "n_boot": args.n_boot,
            "block_size": args.block_size,
            "cp_inits": args.cp_inits,
            "cp_max_iter": args.cp_max_iter,
            "cp_tol": args.cp_tol,
        }
        argv.update(argv_overrides or {})
        manifest = {
            "schema_version": 1,
            "decision_id": "fixture-decision",
            "decision": decision,
            "scientific_execution_authorized": decision == "AUTHORIZED",
            "authorized_by": "fixture-author",
            "authorized_at": "2026-07-19T00:00:00+08:00",
            "action": "run_cp_empirical_pipeline",
            "dataset": args.dataset,
            "argv": argv,
            "implementation_files": {
                "scripts/run_cp_empirical_pipeline.py": pipeline._sha256(
                    pipeline.ROOT / "scripts" / "run_cp_empirical_pipeline.py"
                ),
                "scripts/natcs_design_contract.py": pipeline._sha256(
                    pipeline.ROOT / "scripts" / "natcs_design_contract.py"
                ),
            },
            "input_identity": {
                "rcep_helper_repo": str(helper_repo.resolve()) if helper_repo else None,
                "rcep_helper_manifest_sha256": (
                    pipeline._sha256(pipeline.RCEP_HELPER_TRUST_MANIFEST) if helper_repo else None
                ),
                "rcep_input_files": (
                    {
                        str((helper_repo / "data" / name).resolve()): pipeline._sha256(
                            helper_repo / "data" / name
                        )
                        for name in self.RCEP_INPUT_FIXTURE_FILES
                    }
                    if helper_repo
                    else {}
                ),
                "nyc_dataset_dir": str(nyc_dataset_dir.resolve()) if nyc_dataset_dir else None,
                "nyc_upstream_commit": pipeline.NYC_TAXI_UPSTREAM_COMMIT if nyc_dataset_dir else None,
            },
            "output_root": str(output_root.resolve()),
            "overwrite": "deny",
            "r006e_outcome_authorized": False,
            "r006f_outcome_authorized": False,
            "downstream_builds_authorized": False,
            "post_run_controls": {
                "quarantine_outputs": True,
                "freeze_inventory_sha256_before_value_review": True,
                "independent_claim_audit_required": True,
                "manuscript_promotion_authorized": False,
            },
        }
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return pipeline._sha256(path)

    def make_helper_repo(self, root: Path) -> tuple[Path, str]:
        repo = root / "helper"
        repo.mkdir()
        for name in ("config.py", "research_data_construction.py", "research_network_tvp_var.py"):
            (repo / name).write_text(f"SOURCE_NAME = {name!r}\n", encoding="utf-8")
        data_dir = repo / "data"
        data_dir.mkdir()
        for name in self.RCEP_INPUT_FIXTURE_FILES:
            (data_dir / name).write_text("fixture,data\n1,2\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.name=Production Guard Test",
                "-c",
                "user.email=production-guard@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return repo, commit

    def write_full_manifest(self, manifest_path: Path, repo: Path, commit: str) -> None:
        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "helper_git_commit": commit,
                    "files": {name: pipeline._sha256(repo / name) for name in sorted(pipeline.RCEP_HELPER_FILES)},
                }
            ),
            encoding="utf-8",
        )

    def make_nyc_source_repo(self, root: Path) -> tuple[Path, str]:
        repo = root / "vars"
        dataset_dir = repo / "datasets" / "NYC-taxi"
        dataset_dir.mkdir(parents=True)
        for year in range(2012, 2022):
            (dataset_dir / f"yellow_taxi_trip_{year}.npz").write_bytes(f"fixture-{year}".encode("ascii"))
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.name=NYC Source Test",
                "-c",
                "user.email=nyc-source@example.invalid",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return dataset_dir, commit

    def test_invalid_run_parameters_are_rejected(self):
        base = dict(
            dataset="rcep",
            window=40,
            p=2,
            n_boot=500,
            block_size=4,
            cp_inits=6,
            cp_max_iter=100,
            cp_tol=1e-6,
        )
        for field, value in [
            ("p", 0),
            ("window", 2),
            ("n_boot", 0),
            ("block_size", 0),
            ("cp_inits", 0),
            ("cp_max_iter", 0),
            ("cp_tol", 0.0),
        ]:
            args = SimpleNamespace(**{**base, field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                pipeline.validate_run_args(args)

    def test_missing_scientific_authorization_refuses_before_helper_data_or_output(self):
        args = self.make_run_args()
        with patch.object(
            pipeline.importlib, "import_module", side_effect=AssertionError("helper import forbidden")
        ) as import_module, patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
            pipeline, "load_dataset", side_effect=RuntimeError("data should not be loaded")
        ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
            with self.assertRaisesRegex(RuntimeError, "scientific execution authorization"):
                pipeline.run(args)
        require_helper.assert_not_called()
        import_module.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_not_authorized_template_refuses_before_input_helper_data_or_output(self):
        template = pipeline.ROOT / "refine-logs" / "SCIENTIFIC_EXECUTION_AUTHORIZATION_TEMPLATE_V1.json"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "authorized-runs" / "UNSET" / "rcep"
            args = self.make_run_args(
                authorization=str(template),
                authorization_sha256=pipeline._sha256(template),
                output_root=str(output_root),
            )
            with patch.object(
                pipeline, "_resolved_rcep_input_files", side_effect=AssertionError("input read forbidden")
            ) as resolve_inputs, patch.object(
                pipeline.importlib, "import_module", side_effect=AssertionError("helper import forbidden")
            ) as import_module, patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=AssertionError("scientific data load forbidden")
            ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
                with self.assertRaisesRegex(RuntimeError, "Scientific execution is not authorized"):
                    pipeline.run(args)

            self.assertFalse(output_root.exists())
        resolve_inputs.assert_not_called()
        require_helper.assert_not_called()
        import_module.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_authorization_is_parsed_from_the_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            args = self.make_run_args(output_root=str(output_root))
            authorization_path = root / "authorization.json"
            args.authorization_sha256 = self.write_execution_authorization(
                authorization_path,
                args,
                output_root,
                decision="NOT_AUTHORIZED",
            )
            args.authorization = str(authorization_path)
            original_snapshot_reader = pipeline.read_authorized_input_snapshot

            def mutate_after_snapshot(path, expected_sha256):
                snapshot = original_snapshot_reader(path, expected_sha256)
                authorization_path.write_text("{}\n", encoding="utf-8")
                return snapshot

            with patch.object(
                pipeline, "read_authorized_input_snapshot", side_effect=mutate_after_snapshot
            ) as snapshot_reader, patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
                pipeline, "load_dataset"
            ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
                with self.assertRaisesRegex(RuntimeError, "Scientific execution is not authorized"):
                    pipeline.run(args)

        snapshot_reader.assert_called_once_with(authorization_path, args.authorization_sha256)
        require_helper.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_authorization_sha256_mismatch_refuses_before_helper_data_or_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper_repo, _ = self.make_helper_repo(root)
            args = self.make_run_args(output_root=str(root / "authorized-runs" / "fixture-decision" / "rcep"))
            auth_path = root / "authorization.json"
            self.write_execution_authorization(
                auth_path,
                args,
                Path(args.output_root),
                helper_repo=helper_repo,
            )
            args.authorization = str(auth_path)
            args.authorization_sha256 = "0" * 64
            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs", create=True), patch.object(
                pipeline, "require_raw_helper"
            ) as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=RuntimeError("data should not be loaded")
            ) as load_dataset, patch.object(
                pipeline, "output_paths"
            ) as output_paths:
                with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                    pipeline.run(args)
        require_helper.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_authorization_argv_mismatch_refuses_before_helper_data_or_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper_repo, _ = self.make_helper_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            args = self.make_run_args(output_root=str(output_root))
            auth_path = root / "authorization.json"
            args.authorization_sha256 = self.write_execution_authorization(
                auth_path,
                args,
                output_root,
                helper_repo=helper_repo,
                argv_overrides={"window": 41},
            )
            args.authorization = str(auth_path)
            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs", create=True), patch.object(
                pipeline, "helper_repo", str(helper_repo)
            ), patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=RuntimeError("data should not be loaded")
            ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
                with self.assertRaisesRegex(RuntimeError, "argv"):
                    pipeline.run(args)
        require_helper.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_execution_boundary_flags_refuse_before_helper_data_or_output(self):
        for field in (
            "r006e_outcome_authorized",
            "r006f_outcome_authorized",
            "downstream_builds_authorized",
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                helper_repo, commit = self.make_helper_repo(root)
                trust_manifest = root / "trust.json"
                self.write_full_manifest(trust_manifest, helper_repo, commit)
                output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
                args = self.make_run_args(output_root=str(output_root))
                authorization_path = root / "authorization.json"
                with patch.object(pipeline, "RCEP_HELPER_TRUST_MANIFEST", trust_manifest):
                    self.write_execution_authorization(
                        authorization_path,
                        args,
                        output_root,
                        helper_repo=helper_repo,
                    )
                authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
                authorization[field] = True
                authorization_path.write_text(json.dumps(authorization, indent=2) + "\n", encoding="utf-8")
                args.authorization = str(authorization_path)
                args.authorization_sha256 = pipeline._sha256(authorization_path)

                with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"), patch.object(
                    pipeline, "helper_repo", str(helper_repo)
                ), patch.object(
                    pipeline, "RCEP_HELPER_TRUST_MANIFEST", trust_manifest
                ), patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
                    pipeline, "load_dataset"
                ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
                    with self.assertRaisesRegex(RuntimeError, "execution boundary"):
                        pipeline.run(args)

                self.assertFalse(output_root.exists())
                require_helper.assert_not_called()
                load_dataset.assert_not_called()
                output_paths.assert_not_called()

    def test_rcep_input_hash_mismatch_refuses_before_helper_data_or_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper_repo, commit = self.make_helper_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            args = self.make_run_args(output_root=str(output_root))
            authorization_path = root / "authorization.json"
            self.write_execution_authorization(
                authorization_path,
                args,
                output_root,
                helper_repo=helper_repo,
            )
            authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
            first_path = next(iter(authorization["input_identity"]["rcep_input_files"]))
            authorization["input_identity"]["rcep_input_files"][first_path] = "0" * 64
            authorization_path.write_text(json.dumps(authorization, indent=2) + "\n", encoding="utf-8")
            args.authorization = str(authorization_path)
            args.authorization_sha256 = pipeline._sha256(authorization_path)
            helper_identity = (helper_repo.resolve(), commit, (), "a" * 64, ())
            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"), patch.object(
                pipeline, "helper_repo", str(helper_repo)
            ), patch.object(pipeline, "require_raw_helper", return_value=helper_identity) as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=RuntimeError("data should not be loaded")
            ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
                with self.assertRaisesRegex(RuntimeError, "RCEP input identity"):
                    pipeline.run(args)
        require_helper.assert_called_once_with(authorization["input_identity"]["rcep_helper_manifest_sha256"])
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_valid_rcep_authorization_reaches_helper_before_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper_repo, commit = self.make_helper_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            args = self.make_run_args(output_root=str(output_root))
            authorization_path = root / "authorization.json"
            args.authorization_sha256 = self.write_execution_authorization(
                authorization_path,
                args,
                output_root,
                helper_repo=helper_repo,
            )
            args.authorization = str(authorization_path)
            authorized_inputs = json.loads(authorization_path.read_text(encoding="utf-8"))["input_identity"]
            helper_identity = (helper_repo.resolve(), commit, ())
            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"), patch.object(
                pipeline, "helper_repo", str(helper_repo)
            ), patch.object(pipeline, "require_raw_helper", return_value=helper_identity) as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=RuntimeError("fixture data stop")
            ) as load_dataset, patch.object(
                pipeline, "output_paths", return_value=(output_root, output_root / "figures")
            ) as output_paths:
                with self.assertRaisesRegex(RuntimeError, "fixture data stop"):
                    pipeline.run(args)
        require_helper.assert_called_once_with(authorized_inputs["rcep_helper_manifest_sha256"])
        load_dataset.assert_called_once_with("rcep", authorized_inputs)
        output_paths.assert_not_called()

    def test_output_paths_refuses_symlinked_decision_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            authorized_root = root / "authorized-runs"
            authorized_root.mkdir()
            outside = root / "outside"
            outside.mkdir()
            decision_parent = authorized_root / "fixture-decision"
            decision_parent.symlink_to(outside, target_is_directory=True)
            output_root = decision_parent / "rcep"
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                pipeline.output_paths("rcep", output_root)
            self.assertFalse((outside / "rcep").exists())

    def test_output_writer_refuses_child_symlink_after_directory_reservation(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            pipeline, "_AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES", {}
        ):
            root = Path(tmpdir).resolve()
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            out_dir, _ = pipeline.output_paths("rcep", output_root)
            outside = root / "outside.csv"
            outside.write_text("unchanged\n", encoding="utf-8")
            (out_dir / "probe.csv").symlink_to(outside)

            with self.assertRaisesRegex(RuntimeError, "already exists or is unsafe"):
                pipeline.write_output_csv(pipeline.pd.DataFrame({"value": [1]}), out_dir / "probe.csv")

            self.assertEqual(outside.read_text(encoding="utf-8"), "unchanged\n")

    def test_output_writers_create_csv_json_and_figures_exclusively(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            pipeline, "_AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES", {}
        ):
            root = Path(tmpdir).resolve()
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            out_dir, figure_dir = pipeline.output_paths("rcep", output_root)
            pipeline.write_output_csv(pipeline.pd.DataFrame({"value": [1]}), out_dir / "probe.csv")
            pipeline.write_output_json({"value": 1}, out_dir / "probe.json")
            figure, axis = pipeline.plt.subplots()
            axis.plot([0, 1], [0, 1])
            try:
                pipeline.save_output_figure(figure, figure_dir / "probe.png", dpi=72)
                pipeline.save_output_figure(figure, figure_dir / "probe.pdf")
            finally:
                pipeline.plt.close(figure)

            self.assertEqual((out_dir / "probe.csv").read_text(encoding="utf-8"), "value\n1\n")
            self.assertEqual(json.loads((out_dir / "probe.json").read_text(encoding="utf-8")), {"value": 1})
            self.assertGreater((figure_dir / "probe.png").stat().st_size, 0)
            self.assertGreater((figure_dir / "probe.pdf").stat().st_size, 0)
            with self.assertRaisesRegex(RuntimeError, "already exists or is unsafe"):
                pipeline.write_output_json({"value": 2}, out_dir / "probe.json")

    def test_output_writer_rejects_replaced_reserved_parent_inode(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            pipeline, "_AUTHORIZED_OUTPUT_DIRECTORY_IDENTITIES", {}
        ):
            root = Path(tmpdir).resolve()
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            out_dir, _ = pipeline.output_paths("rcep", output_root)
            displaced = out_dir.parent / "rcep-displaced"
            out_dir.rename(displaced)
            out_dir.mkdir()

            with self.assertRaisesRegex(RuntimeError, "identity changed"):
                pipeline.write_output_json({"value": 1}, out_dir / "probe.json")

            self.assertFalse((out_dir / "probe.json").exists())

    def test_helper_commit_summary_is_dataset_specific(self):
        self.assertTrue(hasattr(pipeline, "helper_commit_for_summary"))
        self.assertIsNone(pipeline.helper_commit_for_summary(None))
        self.assertEqual(
            pipeline.helper_commit_for_summary((Path("/fixture"), "abc123", ())),
            "abc123",
        )

    def test_authorized_input_snapshot_rejects_changed_bytes(self):
        self.assertTrue(hasattr(pipeline, "read_authorized_input_snapshot"))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.csv"
            path.write_bytes(b"approved\n")
            expected_hash = pipeline._sha256(path)
            path.write_bytes(b"changed\n")
            with self.assertRaisesRegex(RuntimeError, "snapshot SHA-256"):
                pipeline.read_authorized_input_snapshot(path, expected_hash)

    def test_authorized_input_snapshot_rejects_symlink(self):
        self.assertTrue(hasattr(pipeline, "read_authorized_input_snapshot"))
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "target.csv"
            target.write_bytes(b"approved\n")
            link = root / "link.csv"
            link.symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                pipeline.read_authorized_input_snapshot(link, pipeline._sha256(target))

    def test_existing_authorized_output_root_refuses_before_helper_or_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper_repo, _ = self.make_helper_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            output_root.mkdir(parents=True)
            args = self.make_run_args(output_root=str(output_root))
            auth_path = root / "authorization.json"
            args.authorization_sha256 = self.write_execution_authorization(
                auth_path,
                args,
                output_root,
                helper_repo=helper_repo,
            )
            args.authorization = str(auth_path)
            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs", create=True), patch.object(
                pipeline, "helper_repo", str(helper_repo)
            ), patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=RuntimeError("data should not be loaded")
            ) as load_dataset, patch.object(pipeline, "output_paths") as output_paths:
                with self.assertRaisesRegex(RuntimeError, "already exists"):
                    pipeline.run(args)
        require_helper.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_valid_nyc_authorization_does_not_require_rcep_helper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            nyc_dataset_dir, commit = self.make_nyc_source_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "nyc_taxi"
            args = self.make_run_args(dataset="nyc_taxi", output_root=str(output_root))
            auth_path = root / "authorization.json"
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                args.authorization_sha256 = self.write_execution_authorization(
                    auth_path,
                    args,
                    output_root,
                    nyc_dataset_dir=nyc_dataset_dir,
                )
            args.authorization = str(auth_path)
            authorized_inputs = json.loads(auth_path.read_text(encoding="utf-8"))["input_identity"]
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit), patch.object(
                pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs", create=True
            ), patch.dict(
                pipeline.os.environ, {"NATCS_NYC_TAXI_DATASET_DIR": str(nyc_dataset_dir)}
            ), patch.object(pipeline, "require_raw_helper") as require_helper, patch.object(
                pipeline, "load_dataset", side_effect=RuntimeError("fixture data stop")
            ) as load_dataset, patch.object(
                pipeline, "output_paths", return_value=(output_root, output_root / "figures")
            ) as output_paths:
                with self.assertRaisesRegex(RuntimeError, "fixture data stop"):
                    pipeline.run(args)
        require_helper.assert_not_called()
        load_dataset.assert_called_once_with("nyc_taxi", authorized_inputs)
        output_paths.assert_not_called()

    def test_malformed_loaded_nyc_panel_refuses_before_output_reservation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            nyc_dataset_dir, commit = self.make_nyc_source_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "nyc_taxi"
            args = self.make_run_args(dataset="nyc_taxi", output_root=str(output_root))
            auth_path = root / "authorization.json"
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                args.authorization_sha256 = self.write_execution_authorization(
                    auth_path,
                    args,
                    output_root,
                    nyc_dataset_dir=nyc_dataset_dir,
                )
            args.authorization = str(auth_path)
            malformed = {
                "Y": np.array([1.0, 2.0]),
                "dates": ["2020-01-31", "2020-02-29"],
                "unit_names": ["Zone-1"],
                "girf_pair": ("Zone-1", "Zone-2"),
            }
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit), patch.object(
                pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"
            ), patch.dict(
                pipeline.os.environ, {"NATCS_NYC_TAXI_DATASET_DIR": str(nyc_dataset_dir)}
            ), patch.object(
                pipeline, "load_dataset", return_value=malformed
            ) as load_dataset, patch.object(
                pipeline, "output_paths"
            ) as output_paths:
                with self.assertRaisesRegex(ValueError, "two-dimensional"):
                    pipeline.run(args)

        load_dataset.assert_called_once()
        output_paths.assert_not_called()
        self.assertFalse(output_root.exists())

    def test_too_short_loaded_nyc_panel_refuses_before_output_or_estimation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            nyc_dataset_dir, commit = self.make_nyc_source_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "nyc_taxi"
            args = self.make_run_args(dataset="nyc_taxi", p=2, window=40, output_root=str(output_root))
            auth_path = root / "authorization.json"
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                args.authorization_sha256 = self.write_execution_authorization(
                    auth_path,
                    args,
                    output_root,
                    nyc_dataset_dir=nyc_dataset_dir,
                )
            args.authorization = str(auth_path)
            dates = pipeline.pd.to_datetime(["2020-01-31", "2020-02-29", "2020-03-31"])
            loaded_panel = {
                "dataset": "nyc_taxi",
                "Y": np.zeros((3, 2), dtype=float),
                "dates": list(dates),
                "unit_names": ["Zone-1", "Zone-2"],
                "girf_pair": ("Zone-1", "Zone-2"),
                "requested_girf_dates": [dates[0], dates[-1]],
                "w_list": [np.zeros((2, 2), dtype=float) for _ in range(3)],
                "W_pre": np.zeros((2, 2), dtype=float),
                "level_panel": pipeline.pd.DataFrame(
                    {
                        "date": dates,
                        "Zone-1": [1.0, 2.0, 3.0],
                        "Zone-2": [4.0, 5.0, 6.0],
                    }
                ),
                "acquisition_info": {"source": "fixture"},
                "primary_label": "Fixture mobility network",
                "w_mode": "mobility",
            }
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit), patch.object(
                pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"
            ), patch.dict(
                pipeline.os.environ, {"NATCS_NYC_TAXI_DATASET_DIR": str(nyc_dataset_dir)}
            ), patch.object(
                pipeline, "load_dataset", return_value=loaded_panel
            ) as load_dataset, patch.object(
                pipeline,
                "output_paths",
                side_effect=AssertionError("output reservation is forbidden"),
            ) as output_paths, patch.object(
                pipeline,
                "select_global_ridge_lambda",
                side_effect=AssertionError("scientific estimation is forbidden"),
            ) as select_global_ridge_lambda:
                with self.assertNoLogs(pipeline.logger, level="INFO"):
                    with self.assertRaisesRegex(ValueError, "loaded panel is too short for rolling estimation"):
                        pipeline.run(args)

            load_dataset.assert_called_once()
            output_paths.assert_not_called()
            select_global_ridge_lambda.assert_not_called()
            self.assertFalse(output_root.exists())

    def test_dirty_rcep_helper_refuses_before_output_reservation_or_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            helper_repo, commit = self.make_helper_repo(root)
            trust_manifest = root / "trust.json"
            self.write_full_manifest(trust_manifest, helper_repo, commit)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            args = self.make_run_args(output_root=str(output_root))
            authorization_path = root / "authorization.json"
            with patch.object(pipeline, "RCEP_HELPER_TRUST_MANIFEST", trust_manifest):
                args.authorization_sha256 = self.write_execution_authorization(
                    authorization_path,
                    args,
                    output_root,
                    helper_repo=helper_repo,
                )
            args.authorization = str(authorization_path)
            (helper_repo / "config.py").write_text("SOURCE_NAME = 'dirty'\n", encoding="utf-8")

            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"), patch.object(
                pipeline, "helper_repo", str(helper_repo)
            ), patch.object(pipeline, "RCEP_HELPER_TRUST_MANIFEST", trust_manifest), patch.object(
                pipeline, "_HELPER_IDENTITY", None
            ), patch.object(pipeline, "load_dataset") as load_dataset, patch.object(
                pipeline, "output_paths"
            ) as output_paths:
                with self.assertRaisesRegex(RuntimeError, "not clean"):
                    pipeline.run(args)

        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_dirty_nyc_source_refuses_before_output_reservation_or_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            nyc_dataset_dir, commit = self.make_nyc_source_repo(root)
            output_root = root / "authorized-runs" / "fixture-decision" / "nyc_taxi"
            args = self.make_run_args(dataset="nyc_taxi", output_root=str(output_root))
            authorization_path = root / "authorization.json"
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                args.authorization_sha256 = self.write_execution_authorization(
                    authorization_path,
                    args,
                    output_root,
                    nyc_dataset_dir=nyc_dataset_dir,
                )
            args.authorization = str(authorization_path)
            (nyc_dataset_dir / "yellow_taxi_trip_2012.npz").write_bytes(b"dirty")

            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit), patch.object(
                pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"
            ), patch.dict(
                pipeline.os.environ, {"NATCS_NYC_TAXI_DATASET_DIR": str(nyc_dataset_dir)}
            ), patch.object(pipeline, "load_dataset") as load_dataset, patch.object(
                pipeline, "output_paths"
            ) as output_paths:
                with self.assertRaisesRegex(RuntimeError, "not clean"):
                    pipeline.run(args)

        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_nonempty_helper_path_without_trust_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_manifest = Path(tmpdir) / "missing-trust.json"
            with patch.object(pipeline, "helper_repo", tmpdir), patch.object(
                pipeline, "RCEP_HELPER_TRUST_MANIFEST", missing_manifest
            ):
                with self.assertRaisesRegex(RuntimeError, "trust manifest"):
                    pipeline.require_raw_helper()

    def test_two_file_manifest_cannot_omit_imported_config_dependency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, commit = self.make_helper_repo(root)
            manifest_path = root / "trust.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "helper_git_commit": commit,
                        "files": {
                            name: pipeline._sha256(repo / name)
                            for name in ("research_data_construction.py", "research_network_tvp_var.py")
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(pipeline, "helper_repo", str(repo)), patch.object(
                pipeline, "RCEP_HELPER_TRUST_MANIFEST", manifest_path
            ):
                with self.assertRaisesRegex(RuntimeError, "file set"):
                    pipeline._validated_helper_identity()

    def test_manifest_hash_cannot_authorize_bound_file_that_differs_from_head(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, commit = self.make_helper_repo(root)
            (repo / "config.py").write_text("SOURCE_NAME = 'dirty config'\n", encoding="utf-8")
            manifest_path = root / "trust.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "helper_git_commit": commit,
                        "files": {
                            name: pipeline._sha256(repo / name)
                            for name in (
                                "config.py",
                                "research_data_construction.py",
                                "research_network_tvp_var.py",
                            )
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(pipeline, "helper_repo", str(repo)), patch.object(
                pipeline, "RCEP_HELPER_TRUST_MANIFEST", manifest_path
            ):
                with self.assertRaisesRegex(RuntimeError, "not clean"):
                    pipeline._validated_helper_identity()

    def test_complete_clean_manifest_validates_three_file_identity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, commit = self.make_helper_repo(root)
            manifest_path = root / "trust.json"
            self.write_full_manifest(manifest_path, repo, commit)
            with patch.object(pipeline, "helper_repo", str(repo)), patch.object(
                pipeline, "RCEP_HELPER_TRUST_MANIFEST", manifest_path
            ):
                identity = pipeline._validated_helper_identity()
        self.assertEqual(identity[1], commit)
        self.assertEqual({name for name, _ in identity[2]}, pipeline.RCEP_HELPER_FILES)

    def test_preloaded_config_module_is_rejected_before_helper_import(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo, commit = self.make_helper_repo(root)
            manifest_path = root / "trust.json"
            self.write_full_manifest(manifest_path, repo, commit)
            fake_config = SimpleNamespace(__file__=str(root / "outside" / "config.py"))
            with patch.object(pipeline, "helper_repo", str(repo)), patch.object(
                pipeline, "RCEP_HELPER_TRUST_MANIFEST", manifest_path
            ), patch.object(pipeline, "_HELPER_IDENTITY", None), patch.dict(
                sys.modules, {"config": fake_config}
            ):
                with self.assertRaisesRegex(RuntimeError, "preloaded"):
                    pipeline.require_raw_helper()

    def test_helper_executes_verified_source_snapshots_after_path_mutation(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        api_names = ("RCEP_LIST", *pipeline.RCEP_DATA_APIS[1:], *pipeline.RCEP_NETWORK_APIS)
        original_modules = {name: sys.modules.get(name) for name in helper_module_names}
        original_globals = {name: getattr(pipeline, name) for name in api_names}
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir).resolve()
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        b"from config import VALUE\n"
                        b"RCEP_LIST = (VALUE,)\n"
                        b"def build_tariff_relief_tc(*args, **kwargs): return VALUE\n"
                        b"def chow_lin_quarterly_vax(*args, **kwargs): return VALUE\n"
                        b"def load_quarterly_macro_and_bilateral(*args, **kwargs): return VALUE\n"
                        b"def quality_control_missing(*args, **kwargs): return VALUE\n"
                        b"def quality_control_outliers(*args, **kwargs): return VALUE\n"
                    ),
                    "research_network_tvp_var.py": (
                        b"from config import VALUE\n"
                        b"def girf_one(*args, **kwargs): return VALUE\n"
                        b"def moving_average_coefficients(*args, **kwargs): return VALUE\n"
                    ),
                }
                for name, source in sources.items():
                    (repo / name).write_bytes(source)
                manifest_sha256 = "a" * 64
                identity = (
                    repo,
                    "fixture-commit",
                    tuple(
                        sorted(
                            (name, pipeline.hashlib.sha256(source).hexdigest())
                            for name, source in sources.items()
                        )
                    ),
                    manifest_sha256,
                    tuple(sorted(sources.items())),
                )

                def mutate_paths_after_validation(_expected_manifest_sha256):
                    for name in sources:
                        (repo / name).write_text("raise RuntimeError('tampered path executed')\n", encoding="utf-8")
                    return identity

                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", side_effect=mutate_paths_after_validation
                ), patch.object(pipeline.importlib, "import_module") as import_module:
                    result = pipeline.require_raw_helper(manifest_sha256)

                self.assertEqual(result, identity)
                self.assertEqual(pipeline.RCEP_LIST, ("approved",))
                self.assertEqual(pipeline.build_tariff_relief_tc(), "approved")
                self.assertEqual(pipeline.girf_one(), "approved")
                import_module.assert_not_called()
        finally:
            for name, value in original_globals.items():
                setattr(pipeline, name, value)
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_cached_helper_identity_rejects_same_manifest_from_changed_checkout(self):
        cached_identity = (Path("/fixture"), "fixture-commit", (), "a" * 64, ())
        current_identity = (Path("/other-fixture"), "fixture-commit", (), "a" * 64, ())
        with patch.object(pipeline, "_HELPER_IDENTITY", cached_identity), patch.object(
            pipeline, "_validated_helper_identity", return_value=current_identity
        ) as validate_identity:
            with self.assertRaisesRegex(RuntimeError, "cached helper identity"):
                pipeline.require_raw_helper("a" * 64)
        validate_identity.assert_called_once_with("a" * 64)

    def test_cached_helper_identity_is_revalidated_on_noarg_access(self):
        cached_identity = (Path("/fixture"), "fixture-commit", (), "a" * 64, ())
        changed_identity = (Path("/fixture"), "fixture-commit", (), "a" * 64, (("config.py", b"changed"),))
        with patch.object(pipeline, "_HELPER_IDENTITY", cached_identity), patch.object(
            pipeline, "_validated_helper_identity", return_value=changed_identity
        ) as validate_identity:
            with self.assertRaisesRegex(RuntimeError, "cached helper identity"):
                pipeline.require_raw_helper()
        validate_identity.assert_called_once_with(None)

    def test_runpy_path_execution_is_rejected_before_payload_execution(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        original_modules = {name: sys.modules.get(name) for name in helper_module_names}
        original_globals = {name: getattr(pipeline, name) for name in ("RCEP_LIST", *pipeline.RCEP_DATA_APIS[1:], *pipeline.RCEP_NETWORK_APIS)}
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                payload = root / "payload.py"
                marker = root / "payload-executed.txt"
                payload.write_text(
                    f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
                    encoding="utf-8",
                )
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        f"import runpy\n"
                        f"def build_tariff_relief_tc(*args, **kwargs): return runpy.run_path({str(payload)!r})\n"
                        "RCEP_LIST = ('approved',)\n"
                        "def chow_lin_quarterly_vax(*args, **kwargs): return 'approved'\n"
                        "def load_quarterly_macro_and_bilateral(*args, **kwargs): return 'approved'\n"
                        "def quality_control_missing(*args, **kwargs): return 'approved'\n"
                        "def quality_control_outliers(*args, **kwargs): return 'approved'\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": (
                        "def girf_one(*args, **kwargs): return 'approved'\n"
                        "def moving_average_coefficients(*args, **kwargs): return 'approved'\n"
                    ).encode("utf-8"),
                }
                identity = (
                    root,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "Dynamic"):
                        pipeline.require_raw_helper("a" * 64)
                self.assertFalse(marker.exists())
        finally:
            for name, value in original_globals.items():
                setattr(pipeline, name, value)
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_unbound_local_helper_import_is_rejected_before_execution(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        original_modules = {name: sys.modules.get(name) for name in helper_module_names}
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir).resolve()
                marker = repo / "unbound-executed.txt"
                (repo / "unbound_helper.py").write_text(
                    f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
                    encoding="utf-8",
                )
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": b"import unbound_helper\n",
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "Unbound local helper import"):
                        pipeline.require_raw_helper("a" * 64)

                self.assertFalse(marker.exists())
                for name in helper_module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_unbound_namespace_package_import_is_rejected_before_execution(self):
        module_names = (
            "config",
            "research_data_construction",
            "research_network_tvp_var",
            "pkg",
            "pkg.mod",
        )
        original_modules = {name: sys.modules.get(name) for name in module_names}
        for name in module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir).resolve()
                marker = repo / "namespace-package-executed.txt"
                package_dir = repo / "pkg"
                package_dir.mkdir()
                (package_dir / "mod.py").write_text(
                    f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
                    encoding="utf-8",
                )
                self.assertFalse((package_dir / "__init__.py").exists())
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": b"import pkg.mod\n",
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "Unbound local helper import"):
                        pipeline.require_raw_helper("a" * 64)

                self.assertFalse(marker.exists())
                for name in module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_aliased_dynamic_import_is_rejected_before_any_helper_execution(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        original_modules = {name: sys.modules.get(name) for name in helper_module_names}
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir).resolve()
                marker = repo / "dynamic-import-executed.txt"
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        f"from pathlib import Path\n"
                        f"Path({str(marker)!r}).write_text('executed')\n"
                        "import importlib as loader\n"
                        "loader.import_module('unbound_helper')\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        r"Dynamic-import facilities|Dynamic helper imports",
                    ):
                        pipeline.require_raw_helper("a" * 64)

                self.assertFalse(marker.exists())
                for name in helper_module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_meta_path_mutation_is_rejected_before_any_helper_execution(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        original_modules = {name: sys.modules.get(name) for name in helper_module_names}
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir).resolve()
                marker = repo / "meta-path-mutation-executed.txt"
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        f"from pathlib import Path\n"
                        f"Path({str(marker)!r}).write_text('executed')\n"
                        "import sys\n"
                        "sys.meta_path.clear()\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "import-path mutation"):
                        pipeline.require_raw_helper("a" * 64)

                self.assertFalse(marker.exists())
                for name in helper_module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def assert_runtime_mapping_path_mutation_rejected(self, runtime_expression, marker_prefix):
        module_names = (
            "config",
            "research_data_construction",
            "research_network_tvp_var",
            "external_payload",
        )
        original_modules = {name: sys.modules.get(name) for name in module_names}
        original_sys_path = sys.path
        original_sys_path_snapshot = tuple(sys.path)
        original_meta_path = sys.meta_path
        original_meta_path_snapshot = tuple(sys.meta_path)
        for name in module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                repo = root / "helper"
                repo.mkdir()
                external_dir = root / "external"
                external_dir.mkdir()
                helper_marker = root / f"{marker_prefix}-helper-executed.txt"
                payload_marker = root / f"{marker_prefix}-payload-executed.txt"
                (external_dir / "external_payload.py").write_text(
                    f"from pathlib import Path\nPath({str(payload_marker)!r}).write_text('executed')\n",
                    encoding="utf-8",
                )
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        f"from pathlib import Path\n"
                        f"Path({str(helper_marker)!r}).write_text('executed')\n"
                        "import sys\n"
                        f"runtime = {runtime_expression}\n"
                        f'runtime["path"].insert(0, {str(external_dir)!r})\n'
                        'runtime["meta_path"][:] = []\n'
                        "import external_payload\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "import-path mutation"):
                        pipeline.require_raw_helper("a" * 64)

                self.assertIs(sys.path, original_sys_path)
                self.assertEqual(tuple(sys.path), original_sys_path_snapshot)
                self.assertIs(sys.meta_path, original_meta_path)
                self.assertEqual(tuple(sys.meta_path), original_meta_path_snapshot)
                self.assertFalse(helper_marker.exists())
                self.assertFalse(payload_marker.exists())
                for name in module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            sys.path = original_sys_path
            sys.path[:] = original_sys_path_snapshot
            sys.meta_path = original_meta_path
            sys.meta_path[:] = original_meta_path_snapshot
            for name in module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_sys_dict_import_path_mutation_is_rejected_before_any_helper_execution(self):
        self.assert_runtime_mapping_path_mutation_rejected("sys.__dict__", "sys-dict")

    def test_sys_getattribute_dict_import_path_mutation_is_rejected_before_any_helper_execution(self):
        self.assert_runtime_mapping_path_mutation_rejected(
            'sys.__getattribute__("__dict__")',
            "sys-getattribute-dict",
        )

    def test_stdlib_package_path_mutation_is_rejected_before_any_helper_execution(self):
        module_names = ("config", "research_data_construction", "research_network_tvp_var", "email")
        original_modules = {name: sys.modules.get(name) for name in module_names}
        for name in module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                repo = root / "helper"
                repo.mkdir()
                external_dir = root / "external"
                external_dir.mkdir()
                marker = root / "package-path-mutation-executed.txt"
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        f"from pathlib import Path\n"
                        f"Path({str(marker)!r}).write_text('executed')\n"
                        "import email\n"
                        f"email.__path__.append({str(external_dir)!r})\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "import-path mutation"):
                        pipeline.require_raw_helper("a" * 64)

                self.assertFalse(marker.exists())
                for name in module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_external_compile_exec_is_rejected_before_any_helper_execution(self):
        module_names = (
            "config",
            "research_data_construction",
            "research_network_tvp_var",
            "external_payload",
        )
        original_modules = {name: sys.modules.get(name) for name in module_names}
        for name in module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                repo = root / "helper"
                repo.mkdir()
                external_dir = root / "external"
                external_dir.mkdir()
                helper_marker = root / "compile-exec-helper-executed.txt"
                payload_marker = root / "compile-exec-payload-executed.txt"
                payload_path = external_dir / "external_payload.py"
                payload_path.write_text(
                    f"from pathlib import Path\nPath({str(payload_marker)!r}).write_text('executed')\n",
                    encoding="utf-8",
                )
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        f"from pathlib import Path\n"
                        f"Path({str(helper_marker)!r}).write_text('executed')\n"
                        f"payload_path = Path({str(payload_path)!r})\n"
                        "exec(compile(payload_path.read_bytes(), str(payload_path), 'exec'))\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "Dynamic code or imports"):
                        pipeline.require_raw_helper("a" * 64)

                self.assertFalse(helper_marker.exists())
                self.assertFalse(payload_marker.exists())
                for name in module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_external_sys_path_payload_is_rejected_by_runtime_import_guard(self):
        module_names = (
            "config",
            "research_data_construction",
            "research_network_tvp_var",
            "external_payload",
        )
        original_modules = {name: sys.modules.get(name) for name in module_names}
        original_sys_path = tuple(sys.path)
        for name in module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                repo = root / "helper"
                repo.mkdir()
                external_dir = root / "external"
                external_dir.mkdir()
                marker = root / "external-payload-executed.txt"
                (external_dir / "external_payload.py").write_text(
                    f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
                    encoding="utf-8",
                )
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": (
                        "import sys\n"
                        f"sys.path.insert(0, {str(external_dir)!r})\n"
                        "import external_payload\n"
                    ).encode("utf-8"),
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "source execution failed") as raised:
                        pipeline.require_raw_helper("a" * 64)

                self.assertIsNotNone(raised.exception.__cause__)
                self.assertRegex(str(raised.exception.__cause__), "Unbound local helper import: external_payload")
                self.assertFalse(marker.exists())
                self.assertEqual(tuple(sys.path), original_sys_path)
                for name in module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            sys.path[:] = original_sys_path
            for name in module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_preloaded_module_without_spec_is_rejected_despite_trusted_file_spoof(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        original_helper_modules = {name: sys.modules.get(name) for name in helper_module_names}
        original_external_payload = sys.modules.get("external_payload")
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir).resolve()
                repo = root / "helper"
                repo.mkdir()
                trusted_root = root / "trusted"
                trusted_root.mkdir()
                marker = root / "preloaded-payload-executed.txt"
                payload_calls = []

                def execute_payload():
                    payload_calls.append("called")
                    marker.write_text("executed", encoding="utf-8")

                external_payload = types.ModuleType("external_payload")
                external_payload.__spec__ = None
                external_payload.__file__ = str(trusted_root / "external_payload.py")
                external_payload.execute = execute_payload
                sys.modules["external_payload"] = external_payload
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": b"import external_payload\nexternal_payload.execute()\n",
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ), patch.object(pipeline, "_trusted_helper_import_roots", return_value={trusted_root}):
                    with self.assertRaisesRegex(RuntimeError, "source execution failed") as raised:
                        pipeline.require_raw_helper("a" * 64)

                self.assertIsNotNone(raised.exception.__cause__)
                self.assertRegex(str(raised.exception.__cause__), "Unbound local helper import: external_payload")
                self.assertEqual(payload_calls, [])
                self.assertFalse(marker.exists())
                self.assertIs(sys.modules.get("external_payload"), external_payload)
                for name in helper_module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_helper_modules[name] is not None:
                    sys.modules[name] = original_helper_modules[name]
            sys.modules.pop("external_payload", None)
            if original_external_payload is not None:
                sys.modules["external_payload"] = original_external_payload

    def test_partial_helper_execution_failure_cleans_module_cache(self):
        helper_module_names = ("config", "research_data_construction", "research_network_tvp_var")
        original_modules = {name: sys.modules.get(name) for name in helper_module_names}
        for name in helper_module_names:
            sys.modules.pop(name, None)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo = Path(tmpdir).resolve()
                sources = {
                    "config.py": b"VALUE = 'approved'\n",
                    "research_data_construction.py": b"raise RuntimeError('fixture failure')\n",
                    "research_network_tvp_var.py": b"VALUE = 'unreached'\n",
                }
                identity = (
                    repo,
                    "fixture-commit",
                    (),
                    "a" * 64,
                    tuple(sorted(sources.items())),
                )
                with patch.object(pipeline, "_HELPER_IDENTITY", None), patch.object(
                    pipeline, "_validated_helper_identity", return_value=identity
                ):
                    with self.assertRaisesRegex(RuntimeError, "source execution failed"):
                        pipeline.require_raw_helper("a" * 64)

                for name in helper_module_names:
                    self.assertNotIn(name, sys.modules)
        finally:
            for name in helper_module_names:
                sys.modules.pop(name, None)
                if original_modules[name] is not None:
                    sys.modules[name] = original_modules[name]

    def test_cli_requires_explicit_numeric_configuration(self):
        argv = [
            "run_cp_empirical_pipeline.py",
            "--dataset",
            "rcep",
            "--authorization",
            "authorization.json",
            "--authorization-sha256",
            "0" * 64,
            "--output-root",
            "/tmp/authorized-runs/fixture-decision/rcep",
        ]
        with patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
            pipeline.parse_args()

    def test_clean_fixed_commit_nyc_source_validates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir, commit = self.make_nyc_source_repo(Path(tmpdir))
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                identity = pipeline._validated_nyc_taxi_source(dataset_dir)
        self.assertEqual(identity[0], dataset_dir.resolve())
        self.assertEqual(identity[1], commit)
        self.assertEqual(len(identity[2]), 10)

    def test_nyc_source_at_wrong_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir, _ = self.make_nyc_source_repo(Path(tmpdir))
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", "0" * 40):
                with self.assertRaisesRegex(RuntimeError, "commit"):
                    pipeline._validated_nyc_taxi_source(dataset_dir)

    def test_dirty_nyc_source_file_is_rejected_even_at_expected_commit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir, commit = self.make_nyc_source_repo(Path(tmpdir))
            (dataset_dir / "yellow_taxi_trip_2012.npz").write_bytes(b"dirty")
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                with self.assertRaisesRegex(RuntimeError, "not clean"):
                    pipeline._validated_nyc_taxi_source(dataset_dir)

    def test_nyc_source_byte_drift_cannot_hide_behind_assume_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir, commit = self.make_nyc_source_repo(Path(tmpdir))
            git_root = dataset_dir.parent.parent
            relative_path = "datasets/NYC-taxi/yellow_taxi_trip_2012.npz"
            subprocess.run(
                ["git", "-C", str(git_root), "update-index", "--assume-unchanged", relative_path],
                check=True,
            )
            (dataset_dir / "yellow_taxi_trip_2012.npz").write_bytes(b"hidden-drift")
            status = subprocess.run(
                ["git", "-C", str(git_root), "status", "--porcelain=v1", "--", relative_path],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(status, "")
            with patch.object(pipeline, "NYC_TAXI_UPSTREAM_COMMIT", commit):
                with self.assertRaisesRegex(RuntimeError, "byte mismatch"):
                    pipeline._validated_nyc_taxi_source(dataset_dir)

    def test_run_refuses_before_data_or_output_calls_without_trust_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            helper_repo, commit = self.make_helper_repo(root)
            trust_manifest = root / "trust.json"
            self.write_full_manifest(trust_manifest, helper_repo, commit)
            output_root = root / "authorized-runs" / "fixture-decision" / "rcep"
            args = self.make_run_args(output_root=str(output_root))
            authorization_path = root / "authorization.json"
            with patch.object(pipeline, "RCEP_HELPER_TRUST_MANIFEST", trust_manifest):
                args.authorization_sha256 = self.write_execution_authorization(
                    authorization_path,
                    args,
                    output_root,
                    helper_repo=helper_repo,
                )
            args.authorization = str(authorization_path)
            trust_manifest.unlink()
            with patch.object(pipeline, "AUTHORIZED_OUTPUT_ROOT", root / "authorized-runs"), patch.object(
                pipeline, "helper_repo", str(helper_repo)
            ), patch.object(pipeline, "RCEP_HELPER_TRUST_MANIFEST", trust_manifest), patch.object(
                pipeline, "require_raw_helper"
            ) as require_helper, patch.object(pipeline, "load_dataset") as load_dataset, patch.object(
                pipeline, "output_paths"
            ) as output_paths:
                try:
                    pipeline.run(args)
                except Exception as exc:
                    self.assertIsInstance(exc, RuntimeError)
                    self.assertRegex(str(exc), "helper manifest identity")
                else:
                    self.fail("missing helper manifest was accepted")

        require_helper.assert_not_called()
        load_dataset.assert_not_called()
        output_paths.assert_not_called()

    def test_estimator_rejects_invalid_lag_and_penalty(self):
        y = np.ones((4, 1))
        w_list = [np.zeros((1, 1)) for _ in range(4)]
        with self.assertRaises(ValueError):
            equationwise_ridge_fit(y, w_list, p=0, lambda_ridge=0.1)
        with self.assertRaises(ValueError):
            equationwise_ridge_fit(y, w_list, p=1, lambda_ridge=-0.1)
        with self.assertRaises(ValueError):
            equationwise_ridge_fit(y[:1], w_list[:1], p=1, lambda_ridge=0.1)


if __name__ == "__main__":
    unittest.main()
