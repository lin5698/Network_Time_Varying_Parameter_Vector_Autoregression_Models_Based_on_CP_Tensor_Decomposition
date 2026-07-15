# R006c Endpoint-Aware Estimator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and audit the frozen R006c experiment that estimates `M_ref` and `B` separately, protects recovery at `W_ref`, and evaluates topology substitution at held-out `W_alt_main` without endpoint leakage.

**Architecture:** Keep the approved protocol, numerical estimators, endpoint metrics, and experiment runner in separate Python modules. The estimator API accepts only fitting data and `W_ref`; held-out topologies enter only the evaluation layer. A formal run requires a passing, hash-matched construction artifact created before outcome execution, and an isolated duplicate run must match every non-runtime field.

**Tech Stack:** Python 3, NumPy linked to Apple Accelerate, standard-library `unittest`, existing R005/R006b CP/Tucker/fused-TV helpers, CSV/JSON/Markdown artifacts.

---

## Scope And File Map

- Create `scripts/experiments/r006c_endpoint_protocol.py`: frozen constants, configuration, named random streams, panel and held-out topology construction, deterministic method seeds, fitting-only dataclass.
- Create `scripts/experiments/r006c_endpoint_estimators.py`: rolling anchor regression, endpoint-blind method fitting, split CP/Tucker reconstruction, collapsed/oracle diagnostics.
- Create `scripts/experiments/r006c_endpoint_metrics.py`: endpoint query construction, endpoint metric aggregation, separated-object diagnostics, cancellation index.
- Create `scripts/experiments/r006c_endpoint_aware_experiment.py`: replication orchestration, 16-cell stop-go gate, reports, construction pre-gate, CLI and duplicate comparison.
- Create `scripts/experiments/test_r006c_endpoint_protocol.py`: construction, random stream and holdout tests.
- Create `scripts/experiments/test_r006c_endpoint_estimators.py`: anchor estimator, leakage, ridge and causal-validation tests.
- Create `scripts/experiments/test_r006c_endpoint_metrics.py`: query, availability, oracle and cancellation tests.
- Create `scripts/experiments/test_r006c_endpoint_aware_experiment.py`: row schema, gate semantics, smoke status, provenance and deterministic comparison tests.
- Create only new artifacts under `output/high_impact_revision/r006c_endpoint_aware/` and `output/high_impact_revision/r006c_endpoint_aware_repeat/`.
- Modify `refine-logs/EXPERIMENT_TRACKER.md` only after the full result and independent judgment exist.
- Preserve all R006/R006b, rejected-submission and manuscript-facing files.

The workspace is not a Git repository (`git status` returns “not a git repository”), so the commit steps normally required by the planning workflow are replaced by explicit test checkpoints and SHA-256 provenance artifacts. No repository initialization is permitted as part of R006c.

### Task 1: Freeze Protocol Types And Named Random Streams

**Files:**
- Create: `scripts/experiments/r006c_endpoint_protocol.py`
- Create: `scripts/experiments/test_r006c_endpoint_protocol.py`
- Read: `refine-logs/R006C_ENDPOINT_AWARE_ESTIMATOR_DESIGN_20260715.md`

- [ ] **Step 1: Write RED tests for frozen constants, seed mapping and deterministic method seeds**

```python
import unittest
import numpy as np

from scripts.experiments import r006c_endpoint_protocol as protocol


class R006CEndpointProtocolTest(unittest.TestCase):
    def test_full_grid_has_2160_rows_and_16_required_cells_per_candidate(self):
        self.assertEqual(protocol.expected_row_count(), 2160)
        self.assertEqual(len(protocol.required_cells()), 16)

    def test_named_streams_are_reproducible_and_independent(self):
        first = protocol.spawn_named_streams(240100)
        second = protocol.spawn_named_streams(240100)
        self.assertEqual(tuple(first), protocol.STREAM_NAMES)
        draws_first = [first[name].normal(size=8) for name in protocol.STREAM_NAMES]
        draws_second = [second[name].normal(size=8) for name in protocol.STREAM_NAMES]
        for left, right in zip(draws_first, draws_second):
            np.testing.assert_array_equal(left, right)
        self.assertEqual(len({draw.tobytes() for draw in draws_first}), 5)

    def test_method_seed_is_stable_and_key_sensitive(self):
        key = (240100, "matched", 0.80, 0.10, 0.15, "anchor_split_cp3")
        self.assertEqual(protocol.method_seed(*key), protocol.method_seed(*key))
        self.assertNotEqual(
            protocol.method_seed(*key),
            protocol.method_seed(*key[:-1], "anchor_split_tucker333"),
        )
```

- [ ] **Step 2: Run the protocol tests and verify the missing module fails**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol -v`

Expected: `ERROR` with `ImportError` for `r006c_endpoint_protocol`.

- [ ] **Step 3: Implement the frozen configuration and seed functions**

```python
from dataclasses import dataclass
import hashlib
import numpy as np

LAYERS = ("matched", "native")
STABILITY_LEVELS = (0.80, 0.95)
APPROXIMATION_TARGETS = (0.10, 0.25)
SEPARATION_LEVELS = (0.02, 0.15, 0.45)
SEEDS = tuple(range(240100, 240110))
METHODS = (
    "block_local", "block_fused_tv", "block_cp3", "block_tucker333",
    "anchor_local", "anchor_split_cp3", "anchor_split_tucker333",
    "collapsed_ref_tucker333", "oracle_b_anchor",
)
STREAM_NAMES = (
    "operator_structure", "estimation_topology", "innovations",
    "main_holdout_topology", "stress_topology",
)


@dataclass(frozen=True)
class R006CConfig:
    n: int = 20
    t_len: int = 200
    window: int = 80
    true_rank: int = 8
    head_rank: int = 3
    fitted_rank: int = 3
    query_frobenius_norm: float = 1.20
    sigma: float = 0.25
    ridge_multiplier: float = 0.001
    horizon: int = 8
    stability_threshold: float = 0.98
    projection_target: float = 0.95
    cp_iterations: int = 50
    cp_starts: int = 2
    cp_tolerance: float = 1e-6
    fused_penalties: tuple[float, ...] = (0.10, 0.25, 0.50, 1.00)
    fused_max_iterations: int = 200
    fused_tolerance: float = 1e-5
    evaluation_fraction: float = 0.30
    validation_fraction: float = 0.20


def spawn_named_streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAM_NAMES))
    return {name: np.random.default_rng(child) for name, child in zip(STREAM_NAMES, children)}


def method_seed(seed, layer, rho, a3, eta, method) -> int:
    key = f"{seed}|{layer}|{rho:.12g}|{a3:.12g}|{eta:.12g}|{method}"
    return int.from_bytes(hashlib.sha256(key.encode("ascii")).digest()[:8], "big")


def expected_row_count() -> int:
    return len(LAYERS) * len(STABILITY_LEVELS) * len(APPROXIMATION_TARGETS) * len(SEPARATION_LEVELS) * len(SEEDS) * len(METHODS)


def required_cells() -> tuple[tuple[str, float, float, float], ...]:
    return tuple(
        (layer, rho, a3, eta)
        for layer in LAYERS for rho in STABILITY_LEVELS
        for a3 in APPROXIMATION_TARGETS for eta in (0.15, 0.45)
    )
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol -v`

Expected: all protocol tests `OK`.

### Task 2: Generate Panels And Held-Out Topologies Without Shared Random State

**Files:**
- Modify: `scripts/experiments/r006c_endpoint_protocol.py`
- Modify: `scripts/experiments/test_r006c_endpoint_protocol.py`
- Reuse: `scripts/experiments/r006b_stability_signal_deconfounding.py`
- Reuse: `scripts/experiments/r005_separation_stability_pilot.py`

- [ ] **Step 1: Write RED tests for anchor identity, holdout construction and stream isolation**

```python
def test_panel_has_exact_anchor_identity_and_declared_holdouts(self):
    panel = protocol.generate_endpoint_panel(
        config=protocol.R006CConfig(n=8, t_len=48, window=24, true_rank=8),
        layer="matched", target_rho=0.80, approximation_target=0.10,
        separation_strength=0.15, seed=240100,
    )
    anchored = panel.A + np.einsum("tij,jk->tik", panel.B, panel.W_ref)
    np.testing.assert_allclose(anchored, panel.M_ref, atol=1e-10, rtol=0.0)
    expected_main = protocol.row_normalize(0.75 * panel.W_ref + 0.25 * panel.W_holdout)
    np.testing.assert_allclose(panel.W_alt_main, expected_main, atol=0.0, rtol=0.0)
    self.assertFalse(np.array_equal(panel.W_alt_main, panel.W_alt_stress))

def test_changing_holdout_streams_does_not_change_fitting_inputs(self):
    panel = protocol.generate_endpoint_panel(
        config=protocol.R006CConfig(n=8, t_len=48, window=24, true_rank=8),
        layer="matched", target_rho=0.80, approximation_target=0.10,
        separation_strength=0.15, seed=240100,
    )
    rng = np.random.default_rng(91)
    holdout = protocol.row_normalize(rng.uniform(size=panel.W_ref.shape))
    changed = dataclasses.replace(
        panel,
        W_holdout=holdout,
        W_alt_main=protocol.row_normalize(0.75 * panel.W_ref + 0.25 * holdout),
        W_alt_stress=protocol.row_normalize(rng.uniform(size=panel.W_ref.shape)),
    )
    self.assertEqual(panel.estimation.sha256(), changed.estimation.sha256())
    self.assertFalse(np.array_equal(panel.W_alt_main, changed.W_alt_main))
    self.assertFalse(np.array_equal(panel.W_alt_stress, changed.W_alt_stress))
```

- [ ] **Step 2: Run the two new tests and verify missing symbols fail**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol -v`

Expected: `ERROR` naming `generate_endpoint_panel` or `EndpointPanel`.

- [ ] **Step 3: Implement immutable fitting inputs and endpoint panel construction**

```python
@dataclass(frozen=True)
class EstimationInputs:
    predictors: np.ndarray
    outcomes: np.ndarray
    topology: np.ndarray
    W_ref: np.ndarray

    def sha256(self) -> str:
        digest = hashlib.sha256()
        for array in (self.predictors, self.outcomes, self.topology, self.W_ref):
            digest.update(np.ascontiguousarray(array).tobytes())
        return digest.hexdigest()


@dataclass(frozen=True)
class EndpointPanel:
    estimation: EstimationInputs
    A: np.ndarray
    B: np.ndarray
    M_ref: np.ndarray
    M_observed: np.ndarray
    innovations: np.ndarray
    W_ref: np.ndarray
    W_holdout: np.ndarray
    W_alt_main: np.ndarray
    W_alt_stress: np.ndarray
    a3_ratio: float
    layer: str


def row_normalize(matrix: np.ndarray) -> np.ndarray:
    values = np.maximum(np.asarray(matrix, dtype=float), 0.0).copy()
    np.fill_diagonal(values, 0.0)
    return values / np.maximum(values.sum(axis=1, keepdims=True), 1e-12)
```

Use child stream `0` only for spatial/operator draws, child `1` only for `_topology_path`, child `2` for innovations plus matched predictors or native initial state, child `3` only for `W_holdout`, and child `4` only for `W_alt_stress`. Reuse R006b `_calibrate_components` so the `rho` and `a3` construction gates remain identical. Return holdouts only on `EndpointPanel`; never add them to `EstimationInputs`.

- [ ] **Step 4: Run protocol tests and the unchanged R006b tests**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol scripts.experiments.test_r006b_stability_signal_deconfounding -v`

Expected: all tests `OK`; no R006b behavior changes.

### Task 3: Implement Anchor-Local Estimation And Endpoint-Blind Reconstruction

**Files:**
- Create: `scripts/experiments/r006c_endpoint_estimators.py`
- Create: `scripts/experiments/test_r006c_endpoint_estimators.py`

- [ ] **Step 1: Write RED tests for anchor design, adaptive ridge and endpoint-blind fitting**

```python
import unittest
import numpy as np

from scripts.experiments.r006c_endpoint_estimators import (
    estimate_anchor_local, fit_method_bundle,
)
from scripts.experiments.r006c_endpoint_protocol import R006CConfig, generate_endpoint_panel


class R006CEndpointEstimatorsTest(unittest.TestCase):
    def test_anchor_local_uses_delta_topology_design(self):
        config = R006CConfig(n=8, t_len=48, window=24, true_rank=8)
        panel = generate_endpoint_panel(
            config=config, layer="matched", target_rho=0.80,
            approximation_target=0.10, separation_strength=0.15, seed=240100,
        )
        tensor, indices, separation, ridge = estimate_anchor_local(
            panel.estimation, window=config.window,
            ridge_multiplier=config.ridge_multiplier,
        )
        self.assertEqual(tensor.shape, (8, 16, 24))
        self.assertEqual(indices.tolist(), list(range(24, 48)))
        self.assertTrue(np.all(ridge["ridge_penalties"] > 0.0))
        self.assertTrue(np.all(np.isfinite(separation)))

    def test_fit_bundle_cannot_observe_heldout_topologies(self):
        config = R006CConfig(
            n=8, t_len=48, window=24, true_rank=8,
            cp_iterations=3, cp_starts=1, fused_penalties=(0.10,),
            fused_max_iterations=100,
        )
        panel = generate_endpoint_panel(
            config=config, layer="matched", target_rho=0.80,
            approximation_target=0.10, separation_strength=0.15, seed=240100,
        )
        first = fit_method_bundle(
            panel.estimation, truth_B=panel.B, config=config, seed=240100,
            layer="matched", rho=0.80, a3=0.10, eta=0.15,
        )
        rng = np.random.default_rng(91)
        holdout = protocol.row_normalize(rng.uniform(size=panel.W_ref.shape))
        changed = dataclasses.replace(
            panel,
            W_holdout=holdout,
            W_alt_main=protocol.row_normalize(0.75 * panel.W_ref + 0.25 * holdout),
            W_alt_stress=protocol.row_normalize(rng.uniform(size=panel.W_ref.shape)),
        )
        second = fit_method_bundle(
            changed.estimation, truth_B=changed.B, config=config, seed=240100,
            layer="matched", rho=0.80, a3=0.10, eta=0.15,
        )
        self.assertFalse(np.array_equal(panel.W_alt_main, changed.W_alt_main))
        self.assertFalse(np.array_equal(panel.W_alt_stress, changed.W_alt_stress))
        self.assertEqual(first.fit_digest(), second.fit_digest())
        self.assertEqual(first.selected_hyperparameters(), second.selected_hyperparameters())
```

- [ ] **Step 2: Run estimator tests and verify the missing module fails**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_estimators -v`

Expected: `ERROR` with `ImportError` for `r006c_endpoint_estimators`.

- [ ] **Step 3: Implement rolling `[M_ref,B]` estimation**

```python
def estimate_anchor_local(inputs, *, window, ridge_multiplier):
    x, y, w, w_ref = inputs.predictors, inputs.outcomes, inputs.topology, inputs.W_ref
    blocks, indices, separation, gram_scales, penalties = [], [], [], [], []
    for date in range(window, x.shape[0]):
        x_window = x[date-window:date]
        delta_w = w[date-window:date] - w_ref[None, :, :]
        delta_exposure = np.einsum("tij,tj->ti", delta_w, x_window, optimize=True)
        design = np.concatenate([x_window, delta_exposure], axis=1)
        coefficient, diagnostic = fit_scale_adaptive_ridge(
            design, y[date-window:date], ridge_multiplier=ridge_multiplier,
        )
        blocks.append(coefficient)
        indices.append(date)
        gram_scales.append(diagnostic["gram_scale"])
        penalties.append(diagnostic["ridge_penalty"])
        projection, *_ = np.linalg.lstsq(x_window, delta_exposure, rcond=1e-10)
        residual = delta_exposure - x_window @ projection
        residual_gram = residual.T @ residual / window
        scale = np.mean(np.square(delta_exposure))
        separation.append(max(float(np.linalg.eigvalsh(residual_gram)[0]), 0.0) / max(scale, 1e-12))
    return (
        np.stack(blocks, axis=2), np.asarray(indices), np.asarray(separation),
        {"gram_scales": np.asarray(gram_scales), "ridge_penalties": np.asarray(penalties)},
    )
```

- [ ] **Step 4: Implement the nine-method fit bundle**

Define a `FittedMethod` dataclass with `name`, `parameterization` (`block`, `anchor`, or `collapsed`), `tensor`, `indices`, `runtime_seconds`, `cp_diagnostics`, `selected_fused_penalty`, and availability flags. Define `FittedBundle.fit_digest()` over sorted method names, tensors, indices and selected hyperparameters while excluding runtime.

Fit `block_local` with corrected R006b `estimate_local_blocks`; select `block_fused_tv` on the pre-evaluation prefix with corrected `select_fused_penalty`; reconstruct block CP/Tucker with fixed rank 3. Fit `anchor_local` once, split it into `M_ref` and `B`, reconstruct each half independently for `anchor_split_cp3` and `anchor_split_tucker333`, then concatenate. Use method seeds keyed with suffixes `anchor_split_cp3:M_ref` and `anchor_split_cp3:B`. Build `collapsed_ref_tucker333` from the Tucker-smoothed `M_ref` only. Build `oracle_b_anchor` by concatenating the same Tucker-smoothed `M_ref` with `truth_B[indices]` transposed to tensor order.

The public function signature must remain:

```python
def fit_method_bundle(
    inputs: EstimationInputs,
    *,
    truth_B: np.ndarray,
    config: R006CConfig,
    seed: int,
    layer: str,
    rho: float,
    a3: float,
    eta: float,
) -> FittedBundle:
    ...
```

Neither `W_alt_main` nor `W_alt_stress` is accepted by this function or any helper it calls.

- [ ] **Step 5: Add causal fused-selection and scaling regression tests**

Perturb only the evaluation-period local tensor and assert the selected penalty and all candidate scores remain unchanged. Multiply anchor design and outcome windows by `0.05`, `7.0`, and `100.0`; assert maximum coefficient difference from the unscaled fit is below `1e-8`.

- [ ] **Step 6: Run estimator, R006b and shared metric tests**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_estimators scripts.experiments.test_r006b_stability_signal_deconfounding scripts.experiments.test_high_impact_metrics -v`

Expected: all tests `OK`.

### Task 4: Implement Endpoint Metrics And Cancellation Diagnostics

**Files:**
- Create: `scripts/experiments/r006c_endpoint_metrics.py`
- Create: `scripts/experiments/test_r006c_endpoint_metrics.py`

- [ ] **Step 1: Write RED tests for endpoint queries, collapsed availability, oracle substitution and cancellation**

```python
import unittest
import numpy as np

from scripts.experiments import r006c_endpoint_metrics as metrics


class R006CEndpointMetricsTest(unittest.TestCase):
    def test_anchor_queries_are_exact_at_reference_and_alternative(self):
        rng = np.random.default_rng(3)
        m_ref = rng.normal(size=(4, 3, 3))
        b = rng.normal(size=(4, 3, 3))
        w_ref = rng.normal(size=(3, 3))
        w_alt = rng.normal(size=(3, 3))
        np.testing.assert_array_equal(metrics.query_anchor(m_ref, b, w_ref, w_ref), m_ref)
        np.testing.assert_allclose(
            metrics.query_anchor(m_ref, b, w_ref, w_alt),
            m_ref + np.einsum("tij,jk->tik", b, w_alt - w_ref),
        )

    def test_cancellation_index_handles_exact_and_cancelling_errors(self):
        zeros = np.zeros((3, 3))
        self.assertEqual(metrics.cancellation_index(zeros, zeros, np.eye(3)), 0.0)
        delta_b = np.eye(3)
        delta_a = -delta_b
        self.assertGreater(metrics.cancellation_index(delta_a, delta_b, np.eye(3)), 1e12)

    def test_collapsed_marks_both_alternative_endpoints_unavailable(self):
        result = metrics.endpoint_availability("collapsed_ref_tucker333")
        self.assertEqual(result, {"w_ref": True, "w_alt_main": False, "w_alt_stress": False})

    def test_oracle_b_query_uses_true_b_exactly(self):
        rng = np.random.default_rng(4)
        m_ref = rng.normal(size=(5, 3, 3))
        true_b = rng.normal(size=(5, 3, 3))
        w_ref = rng.normal(size=(3, 3))
        w_alt = rng.normal(size=(3, 3))
        expected = m_ref + np.einsum("tij,jk->tik", true_b, w_alt - w_ref)
        np.testing.assert_allclose(metrics.query_anchor(m_ref, true_b, w_ref, w_alt), expected)
```

- [ ] **Step 2: Run metric tests and verify the missing module fails**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_metrics -v`

Expected: `ERROR` with `ImportError` for `r006c_endpoint_metrics`.

- [ ] **Step 3: Implement query and cancellation primitives**

```python
def query_anchor(m_ref, b, w_ref, endpoint):
    return m_ref + np.einsum("tij,jk->tik", b, endpoint - w_ref, optimize=True)


def cancellation_index(delta_a, delta_b, w_ref):
    numerator = float(np.linalg.norm(delta_a) + np.linalg.norm(delta_b @ w_ref))
    denominator = float(np.linalg.norm(delta_a + delta_b @ w_ref))
    if numerator == 0.0 and denominator == 0.0:
        return 0.0
    return numerator / max(denominator, 1e-12)


def endpoint_availability(method):
    available = method != "collapsed_ref_tucker333"
    return {"w_ref": True, "w_alt_main": available, "w_alt_stress": available}
```

- [ ] **Step 4: Implement one-row, three-endpoint evaluation**

For each available endpoint store prefixed temporal aggregates:

```python
{
    f"{endpoint}_available": 1,
    f"{endpoint}_operator_relative_error_mean": float(np.mean(relative_errors)),
    f"{endpoint}_operator_absolute_error_mean": float(np.mean(absolute_errors)),
    f"{endpoint}_raw_response_error_mean": float(np.mean(raw_errors)),
    f"{endpoint}_response_zero_ratio_mean": float(np.mean(zero_ratios)),
    f"{endpoint}_stability_qualified_error_mean": qualified_mean_or_none,
    f"{endpoint}_stability_qualified_rate": len(qualified) / evaluation_count,
    f"{endpoint}_projected_sensitivity_error_mean": float(np.mean(projected)),
    f"{endpoint}_estimated_spectral_radius_mean": float(np.mean(estimated_radii)),
    f"{endpoint}_estimated_instability_rate": unstable / evaluation_count,
}
```

Unavailable endpoints must retain the same keys with `available=0` and every numerical field `None`. Store `B_relative_error_mean`, main/stress topology-slope errors, full stored-object error and `cancellation_index_w_ref_mean` for every separated method. Never use projected sensitivity in the pass/fail gate.

Every method row must also store `retrospective_prediction_rmse` computed at the observed training topology; it must never be labelled or reused as an out-of-sample forecast score.

- [ ] **Step 5: Test raw, qualified and projected fields remain distinct**

Construct a deliberately unstable estimate and assert all three keys exist, raw is finite, qualification rate is below one, and projected sensitivity is finite. Assert no aliasing or fallback copies raw values into qualified/projected fields.

- [ ] **Step 6: Run all metric tests**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_metrics scripts.experiments.test_high_impact_metrics -v`

Expected: all tests `OK`.

### Task 5: Implement Replications And The Frozen Stop-Go Gate

**Files:**
- Create: `scripts/experiments/r006c_endpoint_aware_experiment.py`
- Create: `scripts/experiments/test_r006c_endpoint_aware_experiment.py`

- [ ] **Step 1: Write RED tests for nine rows, endpoint schema and smoke status**

```python
import tempfile
import unittest
from pathlib import Path

from scripts.experiments.r006c_endpoint_aware_experiment import run_grid, run_replication
from scripts.experiments.r006c_endpoint_protocol import METHODS, R006CConfig


class R006CEndpointAwareExperimentTest(unittest.TestCase):
    def test_small_replication_returns_exactly_nine_methods(self):
        config = R006CConfig(
            n=8, t_len=48, window=24, true_rank=8,
            cp_iterations=3, cp_starts=1, fused_penalties=(0.10,),
            fused_max_iterations=100,
        )
        rows = run_replication(
            config=config, layer="matched", rho=0.80, a3=0.10,
            eta=0.15, seed=240100,
        )
        self.assertEqual({row["method"] for row in rows}, set(METHODS))
        self.assertEqual(len(rows), 9)
        collapsed = next(row for row in rows if row["method"] == "collapsed_ref_tucker333")
        self.assertEqual(collapsed["w_ref_available"], 1)
        self.assertEqual(collapsed["w_alt_main_available"], 0)
        self.assertIsNone(collapsed["w_alt_main_raw_response_error_mean"])

    def test_smoke_cannot_return_full_pass(self):
        config = R006CConfig(
            n=8, t_len=48, window=24, true_rank=8,
            cp_iterations=2, cp_starts=1, fused_penalties=(0.10,),
            fused_max_iterations=100,
        )
        with tempfile.TemporaryDirectory() as directory:
            payload = run_grid(
                config=config, layers=("matched",), rhos=(0.80,), a3_values=(0.10,),
                eta_values=(0.15,), seeds=(240100,), workers=1,
                output_dir=Path(directory), smoke=True,
            )
            self.assertIn(payload["status"], {"SMOKE_PASS", "SMOKE_FAIL"})
            self.assertNotEqual(payload["status"], "PASS")
            self.assertEqual(payload["row_count"], 9)
```

- [ ] **Step 2: Run experiment tests and verify the missing module fails**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_aware_experiment -v`

Expected: `ERROR` with `ImportError` for `r006c_endpoint_aware_experiment`.

- [ ] **Step 3: Implement replication orchestration and failure rows**

`run_replication` must generate one panel, call `fit_method_bundle` exactly once, evaluate all nine methods and return nine rows keyed by `(layer, rho, a3, eta, seed, method)`. Each successful row must carry the separation diagnostic, design-Gram minimum/maximum/condition, adaptive ridge scale and penalty, selected fused penalty, CP multi-start diagnostics, runtime, layer-state diagnostics and construction-error fields. A numerical exception returns nine explicit failure rows with the same keys and `failure=1`; it must not silently delete a method or seed.

- [ ] **Step 4: Write synthetic gate fixtures before implementing the gate**

Create fixture rows for one candidate across all 16 required cells and 10 seeds. Verify:

- exactly `10%` paired median improvement passes;
- `79%` joint wins fails and `80%` passes;
- one missing seed fails;
- one unavailable main endpoint fails;
- `operator_relative_error == 1.0` fails because the rule is strict `< 1.0`;
- `response_zero_ratio == 1.0` fails;
- passing only matched cells cannot promote;
- CP/Tucker cellwise switching cannot promote either fixed candidate;
- stress and `eta=0.02` metrics cannot rescue a required-cell failure.

- [ ] **Step 5: Implement fixed-candidate cell gates**

For each candidate in `("anchor_split_cp3", "anchor_split_tucker333")`, each required cell and endpoint in `("w_ref", "w_alt_main")`, compute across the ten paired seed rows:

```python
improvement = (comparator_error - candidate_error) / max(comparator_error, 1e-12)
joint_win = all(candidate_error < comparator_error for comparator_error in comparator_errors)
worst_endpoint = max(row["w_ref_raw_response_error_mean"], row["w_alt_main_raw_response_error_mean"])
```

Require 100% availability, ten seeds, no failures, median operator error `<1`, median zero ratio `<1`, median raw-response improvement `>=0.10` against each of `block_local`, `block_fused_tv`, and `block_tucker333` at each endpoint, joint win rate `>=0.80` at each endpoint, and median worst-endpoint improvement `>=0.10` against every comparator. Set `promotion_candidate` only when one fixed candidate passes all 16 cells.

- [ ] **Step 6: Implement full-grid accounting and reports**

Write:

- `r006c_replications.csv` with 2160 sorted unique rows;
- `r006c_summary.csv` grouped by layer/rho/a3/eta/method;
- `r006c_results.json` with protocol/config/environment/provenance/checks;
- `r006c_results.md` with candidate × required-cell tables and failure interpretation;
- `r006c_run.log` from the shell invocation.

Full status is `PASS` only when the declared grid is exact, all rows are unique and successful, construction gates pass, and one fixed candidate passes all 16 required cells. Otherwise full status is `FAIL`. Smoke status is always prefixed `SMOKE_`.

- [ ] **Step 7: Run all four R006c test modules**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_protocol scripts.experiments.test_r006c_endpoint_estimators scripts.experiments.test_r006c_endpoint_metrics scripts.experiments.test_r006c_endpoint_aware_experiment -v`

Expected: all tests `OK`.

### Task 6: Enforce Pre-Outcome Construction Gates And Provenance

**Files:**
- Modify: `scripts/experiments/r006c_endpoint_aware_experiment.py`
- Modify: `scripts/experiments/test_r006c_endpoint_aware_experiment.py`

- [ ] **Step 1: Write RED tests for construction artifact and hash mismatch refusal**

Use a temporary output directory. Assert `write_construction_gate(...)` creates `construction_gate_preoutcome.json` with status `PASS`, protocol SHA-256, hashes for all four R006c code modules, exact anchor/query errors, leakage digest equality, scale-invariance error and causal-validation exclusion. Mutate a copied protocol file or supply a mismatched digest and assert a non-smoke `run_grid` raises `RuntimeError` before its first replication.

- [ ] **Step 2: Implement construction-only mode and formal-run verification**

Add CLI options:

```text
--construction-gate-only
--smoke
--workers INTEGER
--output-dir PATH
--compare-to PATH
```

`--construction-gate-only` writes the artifact and exits without calling `run_replication`. A non-smoke run loads the existing artifact, requires `status == "PASS"`, and requires current protocol/code hashes to match. `--smoke` writes to `output/high_impact_revision/r006c_endpoint_aware_smoke/` unless overridden and cannot satisfy the formal pre-gate.

- [ ] **Step 3: Implement deterministic duplicate comparison**

Compare `r006c_replications.csv` after excluding only `runtime_seconds`; compare summary fields after excluding runtime aggregates; compare gate payloads after excluding `generated_at`, `elapsed_seconds`, runtime fields, environment path noise and output-directory paths. Return a machine-readable report containing row counts, missing identities, extra identities and field-level differences. Exit nonzero on any non-runtime difference.

- [ ] **Step 4: Run construction/provenance tests**

Run: `python3 -m unittest scripts.experiments.test_r006c_endpoint_aware_experiment -v`

Expected: all tests `OK`, including refusal before any outcome row is generated.

### Task 7: Run The Smoke Matrix And Audit Its Schema

**Files:**
- Create: `output/high_impact_revision/r006c_endpoint_aware_smoke/`

- [ ] **Step 1: Run the full one-seed smoke shape**

Run:

```bash
VECLIB_MAXIMUM_THREADS=1 python3 scripts/experiments/r006c_endpoint_aware_experiment.py \
  --smoke --workers 4 \
  --output-dir output/high_impact_revision/r006c_endpoint_aware_smoke \
  2>&1 | tee output/high_impact_revision/r006c_endpoint_aware_smoke/r006c_run.log
```

Expected: `2 layers × 2 rho × 2 a3 × 3 eta × 1 seed × 9 methods = 216` unique rows, zero missing methods, status `SMOKE_PASS` or an explicit construction/numerical failure. Status must never be `PASS`.

- [ ] **Step 2: Verify endpoint availability and no-leakage fields**

Run a short Python read-only audit that asserts all collapsed rows have only `w_ref_available=1`, every feasible separated method has all endpoints available, every identity is unique, raw/qualified/projected keys are all present, and `fit_digest` is shared across endpoint evaluation variants.

- [ ] **Step 3: Run the complete regression suite**

Run: `python3 -m unittest discover -s scripts/experiments -p 'test_*.py' -v`

Expected: all experiment tests `OK`; record the test count and elapsed time in the smoke log.

### Task 8: Freeze Construction Evidence And Execute Two Full Runs

**Files:**
- Create: `output/high_impact_revision/r006c_endpoint_aware/construction_gate_preoutcome.json`
- Create: `output/high_impact_revision/r006c_endpoint_aware_repeat/construction_gate_preoutcome.json`
- Create: remaining R006c full-run artifacts in both isolated directories.

- [ ] **Step 1: Generate both pre-outcome construction artifacts**

Run:

```bash
python3 scripts/experiments/r006c_endpoint_aware_experiment.py \
  --construction-gate-only \
  --output-dir output/high_impact_revision/r006c_endpoint_aware
python3 scripts/experiments/r006c_endpoint_aware_experiment.py \
  --construction-gate-only \
  --output-dir output/high_impact_revision/r006c_endpoint_aware_repeat
```

Expected: both artifacts report `PASS` and identical protocol/code/construction fields apart from generation time and output path.

- [ ] **Step 2: Execute the frozen 2160-row primary run on Apple Accelerate CPU**

Run:

```bash
VECLIB_MAXIMUM_THREADS=1 python3 scripts/experiments/r006c_endpoint_aware_experiment.py \
  --workers 8 \
  --output-dir output/high_impact_revision/r006c_endpoint_aware \
  2>&1 | tee output/high_impact_revision/r006c_endpoint_aware/r006c_run.log
```

Expected: 2160 sorted unique rows and zero numerical failures. A scientific `FAIL` is a valid completed result; do not change thresholds or delete failed cells.

- [ ] **Step 3: Execute the isolated duplicate run**

Run the identical command with `--output-dir output/high_impact_revision/r006c_endpoint_aware_repeat` and preserve its separate log.

- [ ] **Step 4: Compare all non-runtime fields**

Run:

```bash
python3 scripts/experiments/r006c_endpoint_aware_experiment.py \
  --compare-to output/high_impact_revision/r006c_endpoint_aware_repeat \
  --output-dir output/high_impact_revision/r006c_endpoint_aware
```

Expected: zero missing/extra identities and zero non-runtime field differences. Save the comparison JSON in the primary output directory.

### Task 9: Independent Integrity And Claim Gates

**Files:**
- Create: `refine-logs/R006C_AUDIT_20260715.md`
- Modify: `EXPERIMENT_AUDIT.md`
- Modify: `findings.md`
- Modify: `refine-logs/EXPERIMENT_TRACKER.md`

- [ ] **Step 1: Recompute every gate from CSV rather than trusting JSON**

The audit must independently reconstruct all 16 required cells for both fixed candidates, all endpoint-specific comparator improvements, joint-win rates, worst-endpoint improvements, row counts, failure counts and availability rates. It must also verify both construction artifacts and duplicate equality.

- [ ] **Step 2: Apply the approved interpretation without manuscript edits**

Record exactly one of these outcomes:

- one fixed anchor candidate passes all 16 cells: authorize reconsideration of the method headline, but do not edit the manuscript until result-to-claim review;
- matched passes and native fails: retain as controlled diagnostic only;
- reference passes and main holdout fails: record anchor protection without switchability;
- both candidates fail: retain the target-mismatch result and stop before R007/N=50/N=100.

Collapsed, oracle, stress and `eta=0.02` rows remain diagnostics under every outcome.

- [ ] **Step 3: Run the independent result-to-claim judgment**

Judge whether the primary claim is fully supported, partially supported or unsupported using only the frozen protocol and audited artifacts. Preserve the rule that no cellwise method switching can promote a headline. Record the evidence path and remaining claim boundaries in `findings.md`.

- [ ] **Step 4: Update the experiment tracker last**

Add the R006c status, row/failure counts, duplicate-integrity result, fixed-candidate result and next authorized action to `refine-logs/EXPERIMENT_TRACKER.md`. Keep manuscript revision and N=50/100 frozen unless both the numerical and result-to-claim gates explicitly release them.

## Final Verification

- [ ] Run `python3 -m unittest discover -s scripts/experiments -p 'test_*.py' -v` and record the exact pass count.
- [ ] Confirm primary and repeat CSVs each contain 2160 unique identities.
- [ ] Confirm no R006/R006b or manuscript-facing file timestamp/content changed during Tasks 1-8.
- [ ] Confirm `W_alt_main` and `W_alt_stress` do not occur in estimator function signatures or validation inputs.
- [ ] Confirm smoke and partial grids cannot emit full `PASS`.
- [ ] Confirm projected sensitivity is absent from all pass/fail expressions.
- [ ] Confirm the final scientific status is reported even when it is `FAIL`.
