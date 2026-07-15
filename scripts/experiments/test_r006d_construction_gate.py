import inspect
import json
import unittest

import numpy as np

from scripts.experiments import r006d_construction_gate as gate
from scripts.experiments.r006c_endpoint_protocol import row_normalize
from scripts.experiments.r006d_endpoint_support import chronological_regions


class R006DConstructionGateTest(unittest.TestCase):
    def test_construction_seed_is_reproducible_and_key_sensitive(self):
        first = gate.construction_seed(
            240100, "matched", 0.80, 0.10, 0.15, "family"
        )
        second = gate.construction_seed(
            240100, "matched", 0.80, 0.10, 0.15, "family"
        )
        changed = gate.construction_seed(
            240100, "native", 0.80, 0.10, 0.15, "family"
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_panel_gate_keeps_pool_certificates_and_no_forbidden_inputs(self):
        rng = np.random.default_rng(606_009)
        n = 4
        t_len = 40
        window = 20
        predictors = rng.normal(size=(t_len, n))
        topology = np.stack(
            [row_normalize(rng.uniform(size=(n, n))) for _ in range(t_len)]
        )
        w_ref = row_normalize(rng.uniform(size=(n, n)))
        w_interp = row_normalize(
            0.75 * w_ref + 0.25 * row_normalize(rng.uniform(size=(n, n)))
        )
        regions = chronological_regions(
            t_len=t_len,
            window=window,
            validation_fraction=0.20,
            evaluation_fraction=0.30,
        )
        config = gate.R006DConstructionConfig(pool_size=4)
        record = gate.evaluate_panel_construction(
            predictors=predictors,
            topology=topology,
            w_ref=w_ref,
            w_interp=w_interp,
            regions=regions,
            family_seed=101,
            unsupported_seed=102,
            config=config,
        )

        self.assertIn(record["status"], {"CONSTRUCTION_PASS", "CONSTRUCTION_FAIL"})
        self.assertEqual(len(record["family_candidates"]), 4)
        self.assertEqual(len(record["unsupported_candidates"]), 4)
        self.assertEqual(
            len(record["interp_calibration"]["tau"]),
            len(regions.calibration),
        )
        self.assertEqual(
            len(record["interp_calibration"]["singular_values"]),
            len(regions.calibration),
        )
        self.assertNotIn("singular_values", record["family_candidates"][0])
        serialized = json.dumps(record, sort_keys=True)
        for forbidden in ("outcomes", "truth", "endpoint_error"):
            self.assertNotIn(forbidden, serialized)

        parameters = inspect.signature(
            gate.evaluate_panel_construction
        ).parameters
        for forbidden in ("outcomes", "truth", "endpoint_error"):
            self.assertNotIn(forbidden, parameters)

    def test_gate_schema_records_disjoint_region_dates(self):
        schema = gate.construction_schema(
            chronological_regions(
                t_len=200,
                window=80,
                validation_fraction=0.20,
                evaluation_fraction=0.30,
            )
        )
        self.assertEqual(schema["calibration_dates"], list(range(80, 140)))
        self.assertEqual(schema["validation_dates"], list(range(140, 164)))
        self.assertEqual(schema["evaluation_dates"], list(range(164, 200)))


if __name__ == "__main__":
    unittest.main()
