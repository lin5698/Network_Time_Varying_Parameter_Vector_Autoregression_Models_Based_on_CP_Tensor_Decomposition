# R006e Native Supported-Endpoint Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, freeze, execute and independently audit R006e, which tests one fixed design-weighted joint Tucker estimator against three same-target comparators at two never-fitted, design-supported topology endpoints in the frozen native endogenous simulation regime.

**Architecture:** Keep protocol constants and immutable fit/evaluation types separate from support-only endpoint construction, estimator fitting, endpoint evaluation, gates and audit code. Promotion-fit functions receive only `FitInputs`; held-out endpoints and simulation truth enter only the evaluator. Construction produces a hash-locked outcome-free artifact, screening is the only initially authorized outcome phase, and confirmation refuses to run unless the unchanged screening gate passes.

**Tech Stack:** Python 3, NumPy, standard-library `unittest`, `csv`, `json`, `hashlib`, `statistics` and `concurrent.futures`; existing R006c/R006d DGP, Tucker, fused-TV, response-metric and support utilities.

---

## Scope And File Map

- Create `refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md`: human-readable frozen protocol copied from the approved dual-track design, including claims, anti-claims and stop rules.
- Create `scripts/experiments/r006e_native_protocol.py`: constants, immutable dataclasses, split/grid/seed functions, named streams and fit/truth separation.
- Create `scripts/experiments/r006e_endpoint_support.py`: interpolation and cross-family endpoint construction, support/amplification paths and calibration-only selection.
- Create `scripts/experiments/r006e_native_estimators.py`: anchor-local, anchor fused-TV, split Tucker and endpoint-blind fit-bundle APIs.
- Create `scripts/experiments/r006e_dw_tucker.py`: normalized candidate objective, projected optimization, deterministic starts and strict-prefix hyperparameter selection.
- Create `scripts/experiments/r006e_native_metrics.py`: endpoint queries and raw/secondary evaluation metrics; this is the first module allowed to receive truth and held-out endpoints.
- Create `scripts/experiments/r006e_native_gates.py`: screening cells, confirmation contrasts, Holm-adjusted exact sign inference and result status.
- Create `scripts/experiments/r006e_native_experiment.py`: construction, screening, conditional confirmation, output writers and duplicate comparison CLI.
- Create `scripts/experiments/r006e_result_claim_audit.py`: independent artifact recalculation and claim-boundary verdict.
- Create focused tests named `scripts/experiments/test_r006e_*.py` alongside each module.
- Create artifacts only below `output/high_impact_revision/r006e_native_supported_recovery/` and `output/high_impact_revision/r006e_native_supported_recovery_repeat/`.
- Do not modify R006c/R006d artifacts, manuscript files, claim ledger, figures, R007, N=50/100 experiments or R006f.

The workspace is a Git repository. At each checkpoint, run the specified tests, write the sorted SHA-256 manifest under the ignored `output/` tree, and commit only the protocol, source and test files named by that task. Never use `git add -f` to place formal outcomes, raw data or generated artifacts in Git.

Formal outcome execution is deliberately absent from Tasks 1-10. Task 11 authorizes screening only after an outcome-free construction artifact passes. Task 12 authorizes confirmation only if the frozen screening result is `PASS`.

## Frozen Public Interfaces

All later tasks must use these names and signatures unchanged:

```python
# r006e_native_protocol.py
@dataclass(frozen=True)
class R006EConfig: ...

@dataclass(frozen=True)
class FitInputs:
    predictors: np.ndarray
    outcomes: np.ndarray
    topology: np.ndarray
    w_ref: np.ndarray
    coefficient_dates: np.ndarray
    def sha256(self) -> str: ...

@dataclass(frozen=True)
class TruthBundle:
    m_ref: np.ndarray
    b: np.ndarray
    observed_operator: np.ndarray

@dataclass(frozen=True)
class NativePanel:
    fit: FitInputs
    truth: TruthBundle
    w_alt_interp: np.ndarray
    endpoint_stream_seed: int

def chronological_regions(config: R006EConfig) -> ChronologicalRegions: ...
def primary_cells() -> tuple[tuple[float, float, float], ...]: ...
def build_native_panel(config: R006EConfig, *, rho: float, a3: float,
                       eta: float, seed: int) -> NativePanel: ...

# r006e_endpoint_support.py
def construct_supported_endpoints(fit: FitInputs, *, w_alt_interp: np.ndarray,
                                  family_seed: int,
                                  config: R006EConfig) -> EndpointConstruction: ...

# r006e_native_estimators.py
def fit_required_comparators(fit: FitInputs, *, config: R006EConfig,
                             method_seed: int) -> dict[str, FittedPath]: ...

# r006e_dw_tucker.py
def fit_dw_joint_tucker(fit: FitInputs, *, config: R006EConfig,
                        method_seed: int) -> FittedPath: ...

# r006e_native_metrics.py
def evaluate_method(fitted: FittedPath, *, fit: FitInputs, truth: TruthBundle,
                    endpoints: EndpointConstruction,
                    config: R006EConfig) -> dict[str, object]: ...

# r006e_native_gates.py
def evaluate_screening_gate(rows: list[dict[str, object]], *,
                            config: R006EConfig) -> dict[str, object]: ...
def evaluate_confirmation_gate(rows: list[dict[str, object]], *,
                               config: R006EConfig) -> dict[str, object]: ...
```

### Task 1: Freeze The Human-Readable Protocol

**Files:**
- Create: `refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md`
- Read: `docs/superpowers/specs/2026-07-16-r006e-r006f-dual-track-design.md`
- Read: `refine-logs/R006D_DESIGN_WEIGHTED_ENDPOINT_PROTOCOL_20260715.md`

- [ ] **Step 1: Write the protocol with an explicit outcome prohibition**

The document must contain these exact headings and declarations:

```markdown
# R006e Native Supported-Endpoint Recovery Protocol

**Status:** frozen design; construction and implementation authorized; formal outcomes prohibited until the hash-locked construction gate passes

## Primary Claim
In the frozen N=20, T=200 native endogenous VAR simulation regime, one fixed design-weighted joint Tucker estimator improves finite-horizon response recovery at two never-fitted, design-supported topology endpoints relative to three fixed same-target comparators.

## Anti-Claims
- no CP superiority;
- no universal topology-switch recovery;
- no causal or empirical-generalization claim;
- no calibrated uncertainty;
- no scale claim beyond N=20;
- no abstention claim.

## Frozen DGP And Splits
## Supported Endpoints
## Compared Systems
## Candidate Objective And Optimizer
## Chronology And Leakage Contract
## Screening Gate
## Conditional Confirmation Gate
## Failure Interpretations
## Artifact And Provenance Contract
```

Copy every numeric field from sections 3.1-3.10 of the approved spec. State that `W_ref` is a safety endpoint, not part of the primary held-out claim, and that R006f cannot rescue R006e. Describe any later confirmation as independent conditional confirmation of a candidate fixed after historical development and screening; do not claim project-start, unconditional confirmatory error control.

- [ ] **Step 2: Run a protocol completeness check**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md')
t = p.read_text()
required = ['Primary Claim', 'Anti-Claims', 'Frozen DGP And Splits',
            'Supported Endpoints', 'Compared Systems',
            'Candidate Objective And Optimizer',
            'Chronology And Leakage Contract', 'Screening Gate',
            'Conditional Confirmation Gate', 'Failure Interpretations',
            'Artifact And Provenance Contract', '250100', '250129']
missing = [x for x in required if x not in t]
assert not missing, missing
assert 'formal outcomes prohibited' in t
print('R006e protocol completeness check passed.')
PY
```

Expected: `R006e protocol completeness check passed.`

- [ ] **Step 3: Provenance checkpoint**

Run:

```bash
shasum -a 256 refine-logs/R006E_NATIVE_SUPPORTED_RECOVERY_PROTOCOL_20260716.md
```

Record the digest in the execution log, then commit only the protocol with message `docs: freeze R006e native recovery protocol`.

### Task 2: Implement Frozen Types, Grid, Splits And Streams

**Files:**
- Create: `scripts/experiments/r006e_native_protocol.py`
- Create: `scripts/experiments/test_r006e_native_protocol.py`
- Read: `scripts/experiments/r006c_endpoint_protocol.py`
- Read: `scripts/experiments/r006d_endpoint_support.py`

- [ ] **Step 1: Write RED tests for constants, regions, cells and seed namespaces**

```python
import dataclasses
import unittest
import numpy as np

from scripts.experiments import r006e_native_protocol as p


class R006ENativeProtocolTest(unittest.TestCase):
    def test_frozen_grid_and_regions(self):
        config = p.R006EConfig()
        self.assertEqual(config.n, 20)
        self.assertEqual(config.t_len, 200)
        self.assertEqual(config.window, 80)
        self.assertEqual(config.horizon, 8)
        self.assertEqual(p.SCREENING_SEEDS, tuple(range(240100, 240110)))
        self.assertEqual(p.CONFIRMATION_SEEDS, tuple(range(250100, 250130)))
        self.assertEqual(len(p.primary_cells()), 8)
        regions = p.chronological_regions(config)
        self.assertEqual(regions.calibration.tolist(), list(range(80, 140)))
        self.assertEqual(regions.validation.tolist(), list(range(140, 164)))
        self.assertEqual(regions.evaluation.tolist(), list(range(164, 200)))

    def test_named_streams_are_reproducible_and_distinct(self):
        left = p.spawn_named_streams(250100)
        right = p.spawn_named_streams(250100)
        self.assertEqual(tuple(left), p.STREAM_NAMES)
        a = [left[name].normal(size=16) for name in p.STREAM_NAMES]
        b = [right[name].normal(size=16) for name in p.STREAM_NAMES]
        for x, y in zip(a, b):
            np.testing.assert_array_equal(x, y)
        self.assertEqual(len({x.tobytes() for x in a}), len(a))

    def test_fit_inputs_have_no_truth_or_endpoint_fields(self):
        names = {field.name for field in dataclasses.fields(p.FitInputs)}
        self.assertEqual(names, {
            'predictors', 'outcomes', 'topology', 'w_ref', 'coefficient_dates'
        })
        self.assertTrue(names.isdisjoint({
            'truth', 'm_ref', 'b', 'w_alt_interp', 'w_alt_family'
        }))
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006e_native_protocol -v
```

Expected: `ERROR` because `r006e_native_protocol` does not yet exist.

- [ ] **Step 3: Implement constants and immutable types**

Implement exactly:

```python
STABILITY_LEVELS = (0.80, 0.95)
APPROXIMATION_TARGETS = (0.10, 0.25)
SEPARATION_LEVELS = (0.15, 0.45)
SCREENING_SEEDS = tuple(range(240100, 240110))
CONFIRMATION_SEEDS = tuple(range(250100, 250130))
METHODS = (
    'anchor_local', 'anchor_fused_tv',
    'anchor_split_tucker333', 'dw_joint_tucker333',
)
STREAM_NAMES = (
    'operator_structure', 'estimation_topology', 'innovations',
    'interp_endpoint', 'family_endpoint', 'optimizer',
)

@dataclass(frozen=True)
class R006EConfig:
    n: int = 20
    t_len: int = 200
    window: int = 80
    true_rank: int = 8
    fitted_rank: int = 3
    sigma: float = 0.25
    ridge_multiplier: float = 0.001
    horizon: int = 8
    stability_threshold: float = 0.98
    projection_target: float = 0.95
    fused_penalties: tuple[float, ...] = (0.10, 0.25, 0.50, 1.00)
    temporal_penalties: tuple[float, ...] = (0.0, 0.01, 0.05, 0.20)
    optimizer_starts: int = 3
    optimizer_iterations: int = 300
    objective_tolerance: float = 1e-6
    stationarity_tolerance: float = 1e-4
    kappa_max: float = 50.0
    support_floor: float = 1e-10
    support_threshold: float = 0.10
    family_pool_size: int = 64

@dataclass(frozen=True)
class ChronologicalRegions:
    calibration: np.ndarray
    validation: np.ndarray
    evaluation: np.ndarray

@dataclass(frozen=True)
class FitInputs:
    predictors: np.ndarray
    outcomes: np.ndarray
    topology: np.ndarray
    w_ref: np.ndarray
    coefficient_dates: np.ndarray

    def sha256(self) -> str:
        digest = hashlib.sha256()
        for value in (self.predictors, self.outcomes, self.topology,
                      self.w_ref, self.coefficient_dates):
            digest.update(np.ascontiguousarray(value).tobytes())
        return digest.hexdigest()

@dataclass(frozen=True)
class TruthBundle:
    m_ref: np.ndarray
    b: np.ndarray
    observed_operator: np.ndarray

@dataclass(frozen=True)
class NativePanel:
    fit: FitInputs
    truth: TruthBundle
    w_alt_interp: np.ndarray
    endpoint_stream_seed: int
```

Implement `chronological_regions`, `primary_cells`, deterministic `keyed_seed` and `spawn_named_streams`. Reject any config that does not leave exactly 60/24/36 post-warm-up dates.

- [ ] **Step 4: Implement the native panel adapter**

`build_native_panel` must call the unchanged R006c `generate_endpoint_panel(..., layer='native')`, copy only estimation arrays into `FitInputs`, copy truth into `TruthBundle`, rename `W_alt_main` to `w_alt_interp`, and derive `endpoint_stream_seed` with:

```python
keyed_seed(seed, rho, a3, eta, 'family_endpoint')
```

Do not pass the R006c stress endpoint forward.

- [ ] **Step 5: Run focused and inherited tests**

Run:

```bash
python3 -m unittest \
  scripts.experiments.test_r006e_native_protocol \
  scripts.experiments.test_r006c_endpoint_protocol -v
```

Expected: all tests `OK`; eight primary cells and exact split indices are verified.

- [ ] **Step 6: Provenance checkpoint**

Run `shasum -a 256` on the two R006e files and save the sorted output as `output/high_impact_revision/r006e_native_supported_recovery/checkpoint_task02.sha256`. Commit only the two source/test files with message `feat: add frozen R006e protocol types`.

### Task 3: Build Calibration-Only Supported Endpoints And Amplification Diagnostics

**Files:**
- Create: `scripts/experiments/r006e_endpoint_support.py`
- Create: `scripts/experiments/test_r006e_endpoint_support.py`
- Read: `scripts/experiments/r006d_endpoint_support.py`
- Read: `scripts/experiments/r006d_construction_gate.py`

- [ ] **Step 1: Write RED tests for selection, no replacement and amplification**

```python
import unittest
import numpy as np
from scripts.experiments.r006e_endpoint_support import (
    EndpointConstruction, construct_supported_endpoints,
    query_amplification,
)


class R006EEndpointSupportTest(unittest.TestCase):
    def test_family_selection_uses_lowest_supported_index(self):
        maxima = np.array([0.12, 0.08, 0.02])
        from scripts.experiments.r006e_endpoint_support import first_supported
        self.assertEqual(first_supported(maxima, threshold=0.10), 1)

    def test_family_selection_does_not_replace_lost_endpoint(self):
        from scripts.experiments.r006e_endpoint_support import availability_status
        self.assertEqual(
            availability_status(calibration_max=0.08,
                                prospective_max=0.11,
                                threshold=0.10),
            'lost_support',
        )

    def test_query_amplification_uses_absolute_gram_scale(self):
        gram = np.diag([4.0, 1.0])
        projector = np.eye(2)
        delta = np.eye(2)
        value = query_amplification(gram, projector, delta)
        expected = np.sqrt(1 / 4 + 1) / np.sqrt(2)
        self.assertAlmostEqual(value, expected)
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_endpoint_support -v`

Expected: `ERROR` because the support module does not exist.

- [ ] **Step 3: Implement serialized support records**

```python
@dataclass(frozen=True)
class QuerySupportPath:
    dates: np.ndarray
    chi: np.ndarray
    amplification: np.ndarray
    alpha: np.ndarray
    retained_rank: np.ndarray
    condition_number: np.ndarray
    singular_values: tuple[np.ndarray, ...]

@dataclass(frozen=True)
class FamilyCandidateRecord:
    index: int
    endpoint: np.ndarray
    path: QuerySupportPath
    def to_json_dict(self) -> dict[str, object]: ...

@dataclass(frozen=True)
class EndpointConstruction:
    status: str
    failure_reasons: tuple[str, ...]
    w_alt_interp: np.ndarray
    w_alt_family: np.ndarray | None
    family_selected_index: int | None
    interp_calibration: QuerySupportPath
    interp_prospective: QuerySupportPath
    family_calibration: QuerySupportPath | None
    family_prospective: QuerySupportPath | None
    family_candidates: tuple[FamilyCandidateRecord, ...]
```

All arrays exposed by these frozen records must use immutable backing storage rather than only `writeable=False`. `EndpointConstruction` must enforce exactly 64 candidate records indexed `0..63`, validate the selected endpoint against its selected record, and serialize candidates through `to_json_dict()` using JSON primitives only.

Use R006d `build_design_support_path`, `evaluate_query_path` and `generate_family_pool`. Add `query_amplification`:

```python
def query_amplification(gram, projector, delta_w):
    retained_inverse = projector @ np.linalg.pinv(gram) @ projector
    variance_mass = np.trace(delta_w.T @ retained_inverse @ delta_w)
    return float(np.sqrt(max(variance_mass, 0.0)) /
                 max(np.linalg.norm(delta_w), 1e-12))
```

Set `alpha=1/max(amplification,1e-12)`. Store absolute singular values and `s_max/s_min_retained`; do not use `alpha` to select endpoints or pass recovery.

- [ ] **Step 4: Enforce calibration-only construction**

`construct_supported_endpoints` must:

1. build calibration designs from dates `80-139` only;
2. construct `W_alt_interp` once, with no redraw;
3. generate exactly 64 family candidates from `family_seed`;
4. choose the lowest calibration-supported index;
5. recompute that fixed endpoint over dates `140-199`;
6. return `CONSTRUCTION_FAIL` for missing family support or prospective support loss;
7. retain all 64 calibration certificates.

The function signature must contain no outcomes argument separate from `FitInputs`, no truth and no endpoint-error callback.

- [ ] **Step 5: Run support and inherited algebra tests**

Run:

```bash
python3 -m unittest \
  scripts.experiments.test_r006e_endpoint_support \
  scripts.experiments.test_r006d_endpoint_support -v
```

Expected: all tests `OK`, including lowest-index selection, `chi`, amplification and no-replacement behavior.

- [ ] **Step 6: Provenance checkpoint**

Hash the module and test into `checkpoint_task03.sha256`. Commit only the module and test with message `feat: add supported endpoint construction for R006e`.

### Task 4: Enforce Truth-Isolated Promotion APIs

**Files:**
- Create: `scripts/experiments/r006e_native_estimators.py`
- Create: `scripts/experiments/test_r006e_truth_isolation.py`

- [ ] **Step 1: Write RED tests that inspect and perturb the fit boundary**

```python
import dataclasses
import inspect
import unittest
import numpy as np

from scripts.experiments.r006e_native_protocol import R006EConfig, build_native_panel
from scripts.experiments.r006e_native_estimators import fit_required_comparators


class R006ETruthIsolationTest(unittest.TestCase):
    def test_promotion_fit_signature_has_no_truth_or_endpoint(self):
        names = set(inspect.signature(fit_required_comparators).parameters)
        self.assertEqual(names, {'fit', 'config', 'method_seed'})
        self.assertTrue(names.isdisjoint({
            'truth', 'b_true', 'm_ref_true', 'w_alt_interp', 'w_alt_family'
        }))

    def test_truth_and_endpoint_changes_do_not_change_fit_digest(self):
        config = R006EConfig(n=8, t_len=48, window=24, true_rank=8)
        panel = build_native_panel(config, rho=.8, a3=.1, eta=.15, seed=240100)
        first = fit_required_comparators(panel.fit, config=config, method_seed=91)
        altered_truth = dataclasses.replace(
            panel.truth, b=panel.truth.b + 100.0,
            m_ref=panel.truth.m_ref - 100.0,
        )
        altered_panel = dataclasses.replace(
            panel, truth=altered_truth,
            w_alt_interp=np.flip(panel.w_alt_interp, axis=0),
        )
        second = fit_required_comparators(altered_panel.fit,
                                          config=config, method_seed=91)
        self.assertEqual(fit_bundle_digest(first), fit_bundle_digest(second))
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_truth_isolation -v`

Expected: import error or missing `fit_required_comparators`.

- [ ] **Step 3: Implement the endpoint-blind fit record**

```python
@dataclass(frozen=True)
class FittedPath:
    method: str
    parameterization: str
    tensor: np.ndarray
    dates: np.ndarray
    selected_penalty: float | None
    diagnostics: dict[str, object]
    runtime_seconds: float

def fit_path_digest(path: FittedPath) -> str:
    digest = hashlib.sha256()
    digest.update(path.method.encode('ascii'))
    digest.update(np.ascontiguousarray(path.tensor).tobytes())
    digest.update(np.ascontiguousarray(path.dates).tobytes())
    digest.update(repr(path.selected_penalty).encode('ascii'))
    digest.update(json.dumps(path.diagnostics, sort_keys=True,
                             separators=(',', ':')).encode('ascii'))
    return digest.hexdigest()
```

Exclude runtime from fit digests. Add a separate `OracleInputs` type only if later mechanism controls are implemented; it must not be accepted by either required fit function.

- [ ] **Step 4: Run isolation tests**

Run: `python3 -m unittest scripts.experiments.test_r006e_truth_isolation -v`

Expected: tests progress past signature inspection; estimator-content tests may remain RED until Task 5, but no truth or endpoint can cross the API.

- [ ] **Step 5: Provenance checkpoint**

Hash files into `checkpoint_task04.sha256`. Commit only the named source/test files with message `test: enforce R006e truth-isolated fit API`.

### Task 5: Implement Three Same-Target Anchor Comparators

**Files:**
- Modify: `scripts/experiments/r006e_native_estimators.py`
- Create: `scripts/experiments/test_r006e_native_estimators.py`
- Read: `scripts/experiments/r006c_endpoint_estimators.py`
- Read: `scripts/experiments/r006b_stability_signal_deconfounding.py`

- [ ] **Step 1: Write RED tests for method set and equal tuning declarations**

```python
class R006ENativeEstimatorsTest(unittest.TestCase):
    def test_required_comparator_names(self):
        self.assertEqual(REQUIRED_COMPARATORS, (
            'anchor_local', 'anchor_fused_tv', 'anchor_split_tucker333'
        ))

    def test_candidate_and_fused_have_four_declared_penalties(self):
        config = R006EConfig()
        self.assertEqual(len(config.fused_penalties), 4)
        self.assertEqual(len(config.temporal_penalties), 4)

    def test_anchor_fused_validation_is_strict_prefix(self):
        local = fixed_toy_anchor_path(dates=12)
        fit = fixed_toy_fit_inputs(dates=12)
        first = select_anchor_fused_penalty(local, fit=fit,
                                            validation_positions=(6, 7, 8),
                                            config=toy_config())
        changed = local.copy()
        changed[:, :, 9:] += 1000.0
        second = select_anchor_fused_penalty(changed, fit=fit,
                                             validation_positions=(6, 7, 8),
                                             config=toy_config())
        self.assertEqual(first, second)
```

Define the fixed toy helpers inside the test file so it has no formal DGP outcomes.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_native_estimators -v`

Expected: missing comparator symbols.

- [ ] **Step 3: Implement `anchor_local`**

Reuse R006c `estimate_anchor_local`, but return a R006e `FittedPath`. The tensor is `[M_ref,B]`, dates are `80-199`, and all ridge scales and penalties are stored.

- [ ] **Step 4: Implement strict-prefix `anchor_fused_tv`**

For each of all 24 validation positions, reconstruct only `local[:, :, :position+1]`, score only its final coefficient at the observed topology, and aggregate date scores. Select from `(0.10,0.25,0.50,1.00)` by `(score, penalty)` so ties choose the smaller penalty. Refit each evaluation prefix with the selected penalty and retain only the final slice for that date. Do not smooth the complete evaluation tail in one call.

- [ ] **Step 5: Implement strict-prefix `anchor_split_tucker333`**

At each scored prefix, apply `_tucker_reconstruct` separately to `M_ref` and `B`, each rank 3, concatenate them, and retain the final slice. No endpoint or truth enters reconstruction.

- [ ] **Step 6: Implement `fit_required_comparators`**

Return exactly three keys in `REQUIRED_COMPARATORS` order. Record 24 validation positions and 36 evaluation dates in diagnostics. A failure produces a finite serialized failure record; it is never silently dropped.

- [ ] **Step 7: Run estimator, isolation and inherited tests**

Run:

```bash
python3 -m unittest \
  scripts.experiments.test_r006e_native_estimators \
  scripts.experiments.test_r006e_truth_isolation \
  scripts.experiments.test_r006c_endpoint_estimators -v
```

Expected: all tests `OK`; later-prefix perturbations cannot change earlier validation choices.

- [ ] **Step 8: Provenance checkpoint**

Hash files into `checkpoint_task05.sha256`. Commit only the named source/test files with message `feat: add same-target R006e comparators`.

### Task 6: Implement The Design-Weighted Joint Tucker Candidate

**Files:**
- Create: `scripts/experiments/r006e_dw_tucker.py`
- Create: `scripts/experiments/test_r006e_dw_tucker.py`
- Read: `refine-logs/R006D_DESIGN_WEIGHTED_ENDPOINT_PROTOCOL_20260715.md`
- Read: `scripts/experiments/r005_separation_stability_pilot.py`

- [ ] **Step 1: Write RED tests for loss equivalence and monotone optimization**

```python
class R006EDWTuckerTest(unittest.TestCase):
    def test_direct_and_gram_losses_agree(self):
        fit, theta = fixed_quadratic_fixture(seed=7)
        direct = normalized_outcome_loss(theta, fit)
        gram = normalized_gram_loss(theta, build_gram_cache(fit))
        self.assertLess(abs(direct - gram), 1e-8)

    def test_accepted_objective_trace_is_non_increasing(self):
        fit = fixed_optimizer_fixture(seed=9)
        result = optimize_dw_tucker_prefix(
            fit, lambda_t=.05, rank=3, start_seed=11,
            max_iterations=20, objective_tolerance=1e-6,
            stationarity_tolerance=1e-4,
        )
        trace = np.asarray(result.objective_trace)
        self.assertTrue(np.all(np.diff(trace) <= 1e-12))

    def test_start_selection_uses_training_objective_only(self):
        candidates = [fake_start(2.0, 0), fake_start(1.0, 1), fake_start(3.0, 2)]
        self.assertEqual(select_optimizer_start(candidates).start_index, 1)

    def test_perturbation_starts_are_keyed_scaled_and_projected(self): ...

    def test_start_selection_rejects_lower_objective_nonconverged_start(self): ...

    def test_only_tolerance_or_stationarity_sets_converged(self): ...

    def test_backtracking_exhaustion_is_retained_as_failure(self): ...

    def test_projected_gradient_proxy_matches_frozen_unit_step_formula(self): ...
```

Fixtures contain fixed arrays only and must not call `build_native_panel`. The start fixture must assert the exact `0.05` Frobenius scaling, key tuple, tensor-space application and deterministic projected bytes. The stopping fixture must separately exercise `OBJECTIVE_TOLERANCE`, `STATIONARITY`, `BACKTRACK_FAIL`, `ITERATION_CAP` and `NUMERICAL_FAIL`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_dw_tucker -v`

Expected: module import failure.

- [ ] **Step 3: Implement the normalized objective**

For prefix coefficient dates `d=0,...,D-1`, implement:

```text
(1/D) sum_d L_d(Theta_d)/(N n_d)
+ lambda_T g_bar/[2 N^2 (D-1)]
  sum_{d=1}^{D-1} ||Theta_d-Theta_{d-1}||_F^2
```

where each `L_d` uses only its previous 80 observations and `g_bar` is the mean per-coordinate design Gram scale. There is no unsupported-direction penalty. Provide both direct and Gram-cache forms and test equality within `1e-8`.

- [ ] **Step 4: Implement projected optimization**

Use the exact optimizer construction frozen in the R006e protocol. Start 0 separately reconstructs the prefix-specific `M_ref` and `B` split-Tucker blocks, concatenates them, and then applies the joint deterministic rank-`(3,3,3)` projection and normalization. Starts 1 and 2 add tensor-space i.i.d. standard-normal perturbations scaled to `0.05 * max(||Theta_0||_F,1)`, keyed by `(method_seed,prefix_end_date,lambda_T_grid_index,start_index)`, then apply the same deterministic truncated-HOSVD rank-`(3,3,3)` projection, sign convention and factor normalization as the iterations. Implement the protocol's `64 * eps * max(s_max,1)` tied-block rule and projector/coordinate-axis modified-Gram-Schmidt canonical basis, including cutoff-tie tests.

Each iteration performs a complete-objective gradient step, rank `(3,3,3)` projection, factor normalization and post-projection objective evaluation. Backtracking tests `2^{-j}` for `j=0,...,24` and accepts the first finite objective no larger than the preceding objective plus `1e-12`. Freeze the protocol's relative-improvement formula and unit-step projected-gradient mapping. Only the five-consecutive-step objective tolerance or stationarity `<=1e-4` sets `converged=True`; `BACKTRACK_FAIL`, `ITERATION_CAP` and `NUMERICAL_FAIL` remain non-converged failures.

Store per start: initial/final objective, objective trace, accepted step sizes, iteration count, stationarity proxy, stopping reason, convergence, runtime and pairwise final-solution distance. Select the finite converged start with smallest training objective, breaking exact ties by start index; never pass endpoint loss to this function.

- [ ] **Step 5: Implement strict-prefix lambda selection**

For every `lambda_T` in `(0,0.01,0.05,0.20)` and every one of 24 validation dates, fit only the available coefficient prefix and score the final slice at the observed topology. Select by `(aggregate RMSE, lambda_T)`. With the selected value, fit every one of 36 evaluation prefixes independently and retain the final slice.

Expose only:

```python
def fit_dw_joint_tucker(fit: FitInputs, *, config: R006EConfig,
                        method_seed: int) -> FittedPath
```

- [ ] **Step 6: Add an outcome-free runtime fixture**

Add CLI `python3 -m scripts.experiments.r006e_dw_tucker --fixture-benchmark`. It must use deterministic synthetic matrices created inside the module, print iterations/second and estimated projected-iteration count, and write no formal result artifact. It must not call the native DGP generator.

- [ ] **Step 7: Run candidate tests and fixture benchmark**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006e_dw_tucker -v
python3 -m scripts.experiments.r006e_dw_tucker --fixture-benchmark
```

Expected: all tests `OK`; benchmark output contains `OUTCOME_FREE_FIXTURE` and no file below the formal screening/confirmation paths.

- [ ] **Step 8: Provenance checkpoint**

Hash files into `checkpoint_task06.sha256`. Commit only the named source/test files with message `feat: implement design-weighted joint Tucker candidate`.

### Task 7: Add Chronology, Leakage And Tuning-Budget Regression Tests

**Files:**
- Create: `scripts/experiments/test_r006e_chronology_leakage.py`
- Modify only if a test fails: R006e modules from Tasks 2-6

- [ ] **Step 1: Write the complete leakage test suite**

Tests must verify:

```python
def test_endpoints_absent_from_all_fit_signatures(): ...
def test_truth_perturbation_keeps_candidate_digest_bitwise_identical(): ...
def test_endpoint_perturbation_keeps_all_fit_digests_identical(): ...
def test_later_local_estimate_cannot_change_earlier_validation_score(): ...
def test_evaluation_target_cannot_change_selected_penalty(): ...
def test_family_selection_reads_calibration_dates_only(): ...
def test_lost_family_support_is_not_replaced(): ...
def test_all_24_validation_positions_are_used(): ...
def test_candidate_and_fused_each_have_four_penalty_options(): ...
def test_optimizer_randomness_cannot_change_dgp_or_endpoint_streams(): ...
```

For endpoint and truth perturbation tests, change values by at least `100.0` and require exact digest equality. For chronology tests, alter only dates after the scored prefix and require exact earlier score equality.

- [ ] **Step 2: Run the new suite and verify failures are specific**

Run: `python3 -m unittest scripts.experiments.test_r006e_chronology_leakage -v`

Expected before fixes: any failure names the exact violated boundary; no formal outcome artifact is created.

- [ ] **Step 3: Apply minimal fixes one failing test at a time**

Do not weaken assertions. Do not add endpoint/truth arguments to fit functions. Do not reduce 24 validation positions. After each fix rerun only the failing test by its full unittest name.

- [ ] **Step 4: Run all pre-outcome tests**

Run:

```bash
python3 -m unittest \
  scripts.experiments.test_r006e_native_protocol \
  scripts.experiments.test_r006e_endpoint_support \
  scripts.experiments.test_r006e_truth_isolation \
  scripts.experiments.test_r006e_native_estimators \
  scripts.experiments.test_r006e_dw_tucker \
  scripts.experiments.test_r006e_chronology_leakage -v
```

Expected: all tests `OK` and zero formal R006e outcome files.

- [ ] **Step 5: Provenance checkpoint**

Hash all R006e source and test files into `checkpoint_task07.sha256`. Commit only the chronology/leakage tests and necessary source changes with message `test: lock R006e chronology and leakage contracts`.

### Task 8: Implement Truth-Only Endpoint Evaluation

**Files:**
- Create: `scripts/experiments/r006e_native_metrics.py`
- Create: `scripts/experiments/test_r006e_native_metrics.py`
- Read: `scripts/experiments/r006c_endpoint_metrics.py`
- Read: `scripts/experiments/high_impact_metrics.py`

- [ ] **Step 1: Write RED tests for query identity and raw-loss retention**

```python
class R006ENativeMetricsTest(unittest.TestCase):
    def test_anchor_query_at_reference_is_m_ref(self):
        m = np.arange(8.0).reshape(2, 2, 2)
        b = np.ones_like(m)
        w = np.eye(2)
        np.testing.assert_array_equal(anchor_query(m, b, w, w), m)

    def test_unstable_dates_remain_in_raw_mean(self):
        truth, estimate = fixed_unstable_path_fixture()
        result = evaluate_endpoint_path(truth, estimate, horizon=8,
                                        stability_threshold=.98,
                                        projection_target=.95)
        self.assertEqual(result['raw_date_count'], len(truth))
        self.assertEqual(result['evaluation_dates'], 36)

    def test_evaluator_is_only_required_api_accepting_truth_and_endpoints(self):
        names = set(inspect.signature(evaluate_method).parameters)
        self.assertEqual(names, {'fitted', 'fit', 'truth', 'endpoints', 'config'})
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_native_metrics -v`

Expected: missing metrics module.

- [ ] **Step 3: Implement endpoint evaluation**

Evaluate `W_ref`, `W_alt_interp` and `W_alt_family` over exactly dates `164-199`. Primary loss is mean raw finite-horizon response error. Never remove unstable dates and never substitute projected sensitivity for raw loss. Store all secondary metrics from approved spec, endpoint availability, support/amplification summaries and fit diagnostics.

The evaluator must produce one flat serializable method-level scientific payload with keys prefixed by endpoint, including:

```text
w_alt_interp_raw_response_error_mean
w_alt_family_raw_response_error_mean
w_ref_raw_response_error_mean
*_operator_relative_error_mean
*_response_zero_ratio_mean
observed_topology_prediction_rmse
m_ref_relative_error_mean
b_relative_error_mean
topology_slope_*_error_mean
estimated_instability_rate
```

The exact frozen evaluator signature intentionally contains no seed or cell coordinates. Task 10's phase-locked runner must turn this payload into a self-contained method/seed/cell replication row by attaching `seed`, `rho`, `a3`, and `eta` directly from the frozen loop context and `peak_memory_bytes` from the measured fit/evaluation resource context. It must not infer identity from method seeds, array contents, truth, endpoints, or results. Missing identity or a missing memory measurement makes the row incomplete and non-scorable. `evaluate_method` must not add identity arguments or fabricate these fields.

- [ ] **Step 4: Run metric and inherited response tests**

Run:

```bash
python3 -m unittest \
  scripts.experiments.test_r006e_native_metrics \
  scripts.experiments.test_r006c_endpoint_metrics -v
```

Expected: all tests `OK`; raw count remains 36 regardless of stability.

- [ ] **Step 5: Provenance checkpoint**

Hash files into `checkpoint_task08.sha256`. Commit only the named source/test files with message `feat: add truth-isolated R006e evaluation`.

### Task 9: Implement Screening And Confirmation Gates

**Files:**
- Create: `scripts/experiments/r006e_native_gates.py`
- Create: `scripts/experiments/test_r006e_native_gates.py`

- [ ] **Step 1: Write RED tests with hand-constructed rows**

```python
class R006ENativeGatesTest(unittest.TestCase):
    def test_one_failed_primary_cell_stops_screening(self):
        rows = synthetic_passing_screening_rows()
        rows = replace_cell_metric(rows, cell=(.95,.25,.45),
                                   endpoint='w_alt_family',
                                   metric='operator_relative_error_mean',
                                   value=1.01)
        result = evaluate_screening_gate(rows, config=R006EConfig())
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['passed_cells'], 7)

    def test_confirmation_contrast_uses_worst_cell_and_endpoint(self):
        rows = synthetic_confirmation_rows(default_ratio=1.20)
        rows = set_single_ratio(rows, seed=250100, cell=(.8,.1,.15),
                                endpoint='w_alt_family', ratio=1.05)
        contrasts = confirmation_contrasts(rows)
        self.assertAlmostEqual(contrasts['anchor_local'][250100],
                               np.log(1.05))

    def test_confirmation_refuses_screening_seeds(self):
        with self.assertRaisesRegex(ValueError, 'confirmation seed set'):
            evaluate_confirmation_gate(synthetic_passing_screening_rows(),
                                       config=R006EConfig())

    def test_confirmation_bound_is_unavailable_without_frozen_spec(self):
        with self.assertRaisesRegex(RuntimeError, 'median-bound specification'):
            evaluate_confirmation_gate(synthetic_confirmation_rows(),
                                       config=R006EConfig())
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_native_gates -v`

Expected: missing gate module.

- [ ] **Step 3: Implement all nine screening conditions**

Group by exactly eight primary cells and ten seeds. Require all four methods and both held-out endpoints in every seed-cell. Implement availability, finite/convergence, operator `<1`, zero ratio `<1`, each-comparator median improvement `>=10%`, joint win `>=80%`, worst-endpoint improvement `>=10%`, prediction RMSE `<=1.05*best`, and `W_ref` raw response `<=1.05*best`. Comparisons use denominator floor `1e-12`.

- [ ] **Step 4: Implement exact confirmation inference**

For each comparator and seed, compute the minimum log ratio across 16 cell-endpoint combinations. Implement the protocol's exact one-sided binomial sign test against `log(1.10)` and deterministic Holm adjustment at familywise `0.05`.

Do not implement or guess the simultaneous median lower-bound inversion in this task. Until a separate pre-outcome specification freezes its confidence allocation, order-statistic indexing, equality handling and finite-sample rounding, `evaluate_confirmation_gate` must return or raise an explicit `CONFIRMATION_NOT_AUTHORIZED` refusal before producing any gating confirmation verdict. After such a specification is approved and hash-locked, this task must be amended with RED tests containing hand-calculated order-statistic cases before bound implementation begins.

Implement the deterministic paired-seed bootstrap frozen in the protocol as secondary output only: NumPy `Generator(PCG64(260901))`, exactly 10,000 replicates, joint resampling of the 30 seed indices across all comparators, comparator-wise median contrast, and 0.025/0.975 empirical quantiles with NumPy's `linear` method. Its output must include `audit_seed=260901`, `replicates=10000`, and `gating=false`; it may not enter a confirmation verdict.

- [ ] **Step 5: Run gate tests**

Run: `python3 -m unittest scripts.experiments.test_r006e_native_gates -v`

Expected: all tests `OK`; one failed cell or one wrong seed namespace cannot pass.

- [ ] **Step 6: Provenance checkpoint**

Hash files into `checkpoint_task09.sha256`. Commit only the named source/test files with message `feat: add R006e screening and confirmation gates`.

### Task 10: Build The Construction Artifact And Phase-Locked Runner

**Files:**
- Create: `scripts/experiments/r006e_native_experiment.py`
- Create: `scripts/experiments/test_r006e_native_experiment.py`

- [ ] **Step 1: Write RED tests for phase locks and hashes**

```python
class R006ENativeExperimentTest(unittest.TestCase):
    def test_construction_artifact_contains_no_recovery_metrics(self):
        artifact = build_construction_artifact(config=toy_config())
        serialized = json.dumps(artifact, sort_keys=True)
        for forbidden in ('raw_response_error', 'operator_error',
                          'truth_b', 'promotion'):
            self.assertNotIn(forbidden, serialized)

    def test_screening_refuses_hash_mismatch(self):
        artifact = fixed_construction_artifact(status='CONSTRUCTION_PASS')
        artifact['provenance']['protocol_sha256'] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'provenance mismatch'):
            verify_construction_artifact(artifact)

    def test_confirmation_refuses_nonpassing_screening(self):
        with self.assertRaisesRegex(RuntimeError, 'screening PASS required'):
            authorize_confirmation({'status': 'FAIL'},
                                   fixed_construction_artifact())

    def test_confirmation_refuses_missing_median_bound_specification(self):
        screening = fixed_screening_artifact(status='PASS')
        construction = fixed_construction_artifact(status='CONSTRUCTION_PASS')
        with self.assertRaisesRegex(RuntimeError, 'median-bound specification'):
            authorize_confirmation(screening, construction,
                                   median_bound_specification=None)

    def test_smoke_cannot_emit_formal_pass(self):
        self.assertNotEqual(normalize_run_status('PASS', run_type='SMOKE'),
                            'PASS')
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_native_experiment -v`

Expected: missing experiment runner.

- [ ] **Step 3: Implement construction-only execution**

CLI:

```bash
python3 -m scripts.experiments.r006e_native_experiment \
  --phase construction \
  --output output/high_impact_revision/r006e_native_supported_recovery
```

Construction iterates screening seed-cell endpoint designs only, fits no estimator, and evaluates no truth. It stores splits, grids, screening seeds, confirmation seed identifiers and stream declarations as metadata, screening support certificates and endpoint indices, source/dependency hashes, Python/NumPy/platform versions and test-command status. It must not instantiate confirmation panels, predictors, outcomes, endpoint candidates, or support certificates. Overall status is `CONSTRUCTION_PASS` only if every required screening endpoint remains supported prospectively.

Here outcome-free excludes recovery evaluation, recovery metrics, promotion verdicts, serialized truth, and exposed true response targets. Screening support construction simulates native states only to obtain predictors. Its support-only DGP adapter may compute operators internally, but returns predictors, topology, reference topology, the interpolation endpoint and stream declarations only. The frozen `FitInputs` API receives an immutable all-zero outcome sentinel which endpoint construction may not read; neither actual outcomes, `TruthBundle`, nor the full truth-bearing `EndpointPanel` crosses the boundary.

For later outcome phases, the runner owns replication-row identity and resource accounting. It must attach the exact loop values `seed`, `rho`, `a3`, and `eta` to every method payload returned by `evaluate_method`, measure and attach `peak_memory_bytes`, and reject a row with missing identity or memory data as incomplete and non-scorable. Identity and memory are runner context, not evaluator inputs, and may not be reconstructed from scientific results.

- [ ] **Step 4: Implement hash verification and phase authorization**

Before screening or confirmation, recompute every protocol/code/dependency hash and refuse any mismatch. Confirmation additionally verifies:

- screening status exactly `PASS`;
- screening uses exactly `240100-240109`;
- candidate/config hashes equal construction hashes;
- confirmation uses exactly `250100-250129`;
- a separately approved simultaneous-median-bound specification and its tests are present, their hashes match the confirmation-authorization manifest, and the specification freezes confidence allocation, order-statistic indexing, equality handling and finite-sample rounding;
- a separate `confirmation_construction_gate_preoutcome.json` was generated only after the unchanged screening `PASS`, constructs every confirmation seed-cell endpoint exactly once, contains no recovery metrics, and matches the confirmation-authorization hashes;
- no confirmation artifact already exists unless `--repeat` targets the isolated repeat directory.

- [ ] **Step 5: Implement row and artifact writers**

Use atomic temporary-file replacement. Write construction as `construction_gate_preoutcome.json`; screening names as `screening_replications.csv`, `screening_summary.csv`, `screening_results.json`; confirmation names as `confirmation_replications.csv`, `confirmation_inference.csv`, `confirmation_results.json`; diagnostics as JSONL. Never overwrite R006c/R006d.

- [ ] **Step 6: Run runner tests, then execute construction only**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006e_native_experiment -v
python3 -m scripts.experiments.r006e_native_experiment \
  --phase construction \
  --output output/high_impact_revision/r006e_native_supported_recovery
```

Expected: tests `OK`; command writes only the screening-seed `construction_gate_preoutcome.json`, endpoint certificates and provenance/checkpoint files. It must not write any `screening_*`, `confirmation_*`, or `confirmation_construction_gate_preoutcome.json` file and must not instantiate confirmation panels or endpoints.

- [ ] **Step 7: Verify the artifact is outcome-free**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('output/high_impact_revision/r006e_native_supported_recovery/construction_gate_preoutcome.json')
x = json.loads(p.read_text())
assert x['status'] in {'CONSTRUCTION_PASS', 'CONSTRUCTION_FAIL'}
s = json.dumps(x).lower()
assert not any(k in s for k in ('raw_response_error', 'operator_relative_error',
                                'promotion_result'))
assert not list(p.parent.glob('screening_*'))
assert not list(p.parent.glob('confirmation_*'))
print('R006e construction artifact is outcome-free.')
PY
```

Expected: `R006e construction artifact is outcome-free.`

- [ ] **Step 8: Provenance checkpoint**

Hash all protocol/source/test files and the construction artifact into `construction_manifest.sha256`. Commit only protocol/source/test files with message `feat: add phase-locked R006e experiment runner`; keep the construction artifact and manifest in ignored `output/`.

### Task 11: Execute Screening Only And Apply The Stop Rule

**Files:**
- Generate only under: `output/high_impact_revision/r006e_native_supported_recovery/`
- Do not modify source after construction hash freeze

- [ ] **Step 1: Verify all preconditions without generating outcomes**

Run all R006e tests plus inherited R006c/R006d construction tests. Expected: all `OK`. Recompute `construction_manifest.sha256`; expected: no mismatch. Inspect the construction artifact; expected: `CONSTRUCTION_PASS`. If it is `CONSTRUCTION_FAIL`, stop here and write a construction-failure audit without running screening.

- [ ] **Step 2: Run formal screening**

Run:

```bash
python3 -m scripts.experiments.r006e_native_experiment \
  --phase screening --workers 6 \
  --output output/high_impact_revision/r006e_native_supported_recovery
```

Expected: exactly `8 cells × 10 seeds × 4 methods = 320` replication rows, no confirmation files, and status either `PASS` or `FAIL` determined only by the frozen nine-condition gate.

- [ ] **Step 3: Run an isolated screening duplicate**

Run the identical command with `--repeat` and output directory `output/high_impact_revision/r006e_native_supported_recovery_repeat`. Compare all non-runtime fields and require zero differences.

- [ ] **Step 4: Apply the unconditional stop rule**

If screening is `FAIL`, do not run Task 12. Preserve all rows and failures, write `r006e_results.md` with the failed cells and the approved failure interpretation, and proceed only to Task 13 audit. Do not alter estimator, thresholds, endpoints, rank, penalties, starts or cells.

- [ ] **Step 5: Provenance checkpoint**

Create `screening_manifest.sha256` covering both screening directories and frozen sources. Do not commit or force-add screening artifacts; record their hashes in the subsequent tracked audit report.

### Task 12: Run Confirmation Only After An Unchanged Screening Pass

**Files:**
- Generate only under the two R006e output directories
- Do not modify source, protocol or construction artifacts

- [ ] **Step 1: Verify conditional authorization**

Run:

```bash
python3 -m scripts.experiments.r006e_native_experiment \
  --phase verify-confirmation-authorization \
  --output output/high_impact_revision/r006e_native_supported_recovery
```

Expected: `CONFIRMATION_AUTHORIZED` only when screening status is `PASS`, all hashes match, no source changed, and a separate pre-outcome specification has frozen and hash-locked the simultaneous median lower-bound confidence allocation, order-statistic indexing, equality handling and finite-sample rounding required by the R006e protocol. Until that prerequisite exists, the only valid response is `CONFIRMATION_NOT_AUTHORIZED`. Any other output terminates this task.

- [ ] **Step 2: Run confirmation on frozen new seeds**

Run:

```bash
python3 -m scripts.experiments.r006e_native_experiment \
  --phase confirmation --workers 6 \
  --output output/high_impact_revision/r006e_native_supported_recovery
```

Expected: exactly `8 × 30 × 4 = 960` confirmation rows, seeds exactly `250100-250129`, three Holm-adjusted contrasts and no pooling with the 320 screening rows.

- [ ] **Step 3: Run isolated confirmation duplicate**

Run with `--repeat`; require zero non-runtime differences across replication, summary, inference and result payloads.

- [ ] **Step 4: Freeze the outcome manifest**

Create `confirmation_manifest.sha256` covering primary/repeat outcomes and all frozen inputs. Do not edit manuscript or claim ledger and do not commit or force-add confirmation artifacts; record their hashes in the subsequent tracked audit report.

### Task 13: Independently Recalculate Results And Audit The Claim

**Files:**
- Create: `scripts/experiments/r006e_result_claim_audit.py`
- Create: `scripts/experiments/test_r006e_result_claim_audit.py`
- Generate: `refine-logs/R006E_RESULT_TO_CLAIM_AUDIT_20260716.md`

- [ ] **Step 1: Write RED tests for independent recalculation**

```python
class R006EResultClaimAuditTest(unittest.TestCase):
    def test_audit_rejects_missing_seed_cell_method(self):
        rows = synthetic_passing_screening_rows()
        rows.pop()
        report = audit_rows(rows, phase='screening')
        self.assertEqual(report['integrity_status'], 'FAIL')

    def test_audit_rejects_claim_beyond_protocol(self):
        result = fixed_pass_result()
        verdict = claim_verdict(result, proposed_claim='universal recovery')
        self.assertEqual(verdict['claim_status'], 'REJECT')

    def test_runtime_is_only_duplicate_exclusion(self):
        allowed = duplicate_excluded_fields()
        self.assertEqual(allowed, {'runtime_seconds', 'peak_memory_bytes',
                                   'generated_at'})
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest scripts.experiments.test_r006e_result_claim_audit -v`

Expected: missing audit module.

- [ ] **Step 3: Implement the read-only audit**

The audit must parse raw CSV independently of stored summaries and recalculate:

- row count and unique identities;
- exact seed/cell/method coverage;
- availability, finite and optimizer-failure counts;
- all nine screening gates;
- all confirmation worst-case contrasts, exact sign tests, Holm adjustment and median bounds when confirmation exists;
- primary/repeat equality excluding only declared runtime metadata;
- protocol/code/construction/outcome hashes;
- whether confirmation was legally authorized;
- the narrowest claim licensed by the result.

The audit script must never import gate results from `screening_results.json` as truth; stored results are comparison targets only.

- [ ] **Step 4: Run audit tests and the formal audit**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006e_result_claim_audit -v
python3 -m scripts.experiments.r006e_result_claim_audit \
  --primary output/high_impact_revision/r006e_native_supported_recovery \
  --repeat output/high_impact_revision/r006e_native_supported_recovery_repeat \
  --report refine-logs/R006E_RESULT_TO_CLAIM_AUDIT_20260716.md
```

Expected: report states separate `integrity_status`, `scientific_status` and `claim_status`; it preserves a `FAIL` without proposing a threshold change. If confirmation does not exist because screening failed, the audit explicitly states that no confirmatory estimator claim is available.

- [ ] **Step 5: Run the full regression suite**

Run all `test_r006e_*.py` modules plus unchanged R006c/R006d tests. Expected: all tests `OK`, zero non-runtime duplicate differences and no manuscript changes.

- [ ] **Step 6: Final provenance checkpoint**

Create `final_manifest.sha256` covering protocol, source, tests, construction, available outcome artifacts and audit report. Commit only the three tracked Task 13 files (audit source, focused test and audit report) with message `audit: finalize R006e result-to-claim review`.

## Execution Decision Tree

```text
pre-outcome tests fail
  -> fix only with a new failing regression test; regenerate hashes

construction fails
  -> record CONSTRUCTION_FAIL; no screening

screening fails
  -> record FAIL; no confirmation; audit only

screening passes unchanged
  -> run 30-seed confirmation and duplicate

confirmation fails
  -> exploratory screening only; no headline claim

confirmation passes and independent audit passes
  -> only then consider manuscript and claim-ledger revision
```

## Self-Review Checklist

- [ ] Every numeric DGP, split, endpoint, method, seed and gate matches the approved dual-track spec.
- [ ] No fit API accepts truth or held-out endpoints.
- [ ] All 24 validation positions and 36 evaluation positions remain chronological.
- [ ] Construction artifacts contain support/design information only, not recovery outcomes.
- [ ] Screening and confirmation are isolated and never pooled.
- [ ] Confirmation is technically impossible to run after a screening failure or hash mismatch.
- [ ] Duplicate and audit steps recalculate rather than trust stored summaries.
- [ ] No task edits R006c/R006d, R006f, manuscript, figures or claim ledger.
- [ ] No placeholder such as `TBD`, `TODO` or unspecified “appropriate tests” remains.
