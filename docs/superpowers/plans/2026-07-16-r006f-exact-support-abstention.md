# R006f Exact-Support Abstention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an isolated, prespecified fixed-design experiment that verifies exact topology-query support, principled abstention, paired-world non-identifiability and excitation-dependent amplification without promoting a recovery estimator.

**Architecture:** Separate the immutable scientific protocol, exact DCT/basis construction, estimator/readout algebra and run/provenance governance into focused files. Construction-only code may create and hash official designs but cannot generate official noise or outcomes. The formal runner requires an explicit authorization flag and a matching `PASS` pre-outcome artifact, writes only to the R006f directory, and is followed by an isolated duplicate comparison and result-to-claim audit.

**Tech Stack:** Python 3 standard library, NumPy, `unittest`, JSON/CSV/Markdown artifacts, SHA-256 provenance, Git checkpoint commits.

---

## Scope And File Map

Create only the following source files during implementation:

- `refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md`: frozen scientific contract, claims, constants, gates, stop rules and prohibited interpretations.
- `scripts/experiments/r006f_exact_support.py`: DCT bases, deterministic fixed design, topology/query construction, exact and SVD certificates, invariants and analytic diagnostics. This module must not accept a noise seed or create outcomes.
- `scripts/experiments/test_r006f_exact_support.py`: construction, topology, projector, certificate and provenance-free algebra tests.
- `scripts/experiments/r006f_estimators.py`: paired-world outcome generator, FWL min-norm fit, certificate-aware and silent readouts, decomposition and half-gap diagnostics.
- `scripts/experiments/test_r006f_estimators.py`: observational identity, estimator behavior, excitation scaling and analytic lower-bound tests on non-official test seeds.
- `scripts/experiments/r006f_exact_support_abstention.py`: pre-outcome artifact, formal authorization barrier, official run serialization, analytic gate aggregation, duplicate audit, result-to-claim audit and CLI.
- `scripts/experiments/test_r006f_exact_support_abstention.py`: hash mismatch, output isolation, formal labeling, serialization, duplicate and claim-boundary regression tests.

Generated files belong only under:

```text
output/high_impact_revision/r006f_exact_support_abstention/
output/high_impact_revision/r006f_exact_support_abstention_repeat/
```

The implementation phase may generate `construction_gate_preoutcome.json` only. It must not generate `r006f_replications.csv`, `r006f_results.json`, `r006f_results.md`, duplicate comparison or result-to-claim artifacts until formal outcome execution is separately authorized.

The repository is a Git worktree. Every commit below must stage only the files listed in that task; do not stage unrelated user changes.

### Frozen Public Interfaces

The implementation must preserve these names and signatures across tasks:

```python
@dataclass(frozen=True)
class R006FConfig:
    n: int = 6
    t_len: int = 96
    rank: int = 2
    excitation_levels: tuple[float, ...] = (1.0, 0.25)
    beta: float = 0.50
    sigma: float = 0.05
    kappa_max: float = 50.0
    absolute_floor: float = 1e-12
    support_threshold: float = 0.05
    seeds: tuple[int, ...] = tuple(range(620001, 620051))

def dct_ii_basis(length: int) -> np.ndarray: ...
def build_exact_construction(config: R006FConfig, excitation: float) -> ExactConstruction: ...
def support_certificate(construction: ExactConstruction, delta_w: np.ndarray) -> QueryCertificate: ...
def validate_construction(construction: ExactConstruction) -> dict[str, float | int | bool]: ...

def generate_paired_worlds(construction: ExactConstruction, seed: int) -> PairedWorlds: ...
def fwl_min_norm_fit(x: np.ndarray, z: np.ndarray, y: np.ndarray) -> np.ndarray: ...
def certificate_aware_readout(b_hat: np.ndarray, delta_w: np.ndarray, certificate: QueryCertificate, threshold: float) -> QueryReadout: ...
def silent_readout(b_hat: np.ndarray, delta_w: np.ndarray) -> QueryReadout: ...
def evaluate_seed(config: R006FConfig, seed: int) -> list[dict[str, object]]: ...

def current_provenance() -> dict[str, object]: ...
def write_construction_gate(config: R006FConfig, output_dir: Path) -> dict[str, object]: ...
def verify_construction_gate(config: R006FConfig, output_dir: Path) -> dict[str, object]: ...
def run_formal(config: R006FConfig, output_dir: Path, *, authorized: bool = False) -> dict[str, object]: ...
def compare_run_directories(primary: Path, repeat: Path) -> dict[str, object]: ...
def audit_result_to_claim(primary: Path, repeat: Path) -> dict[str, object]: ...
```

---

### Task 1: Freeze The R006f Protocol

**Files:**
- Create: `refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md`

- [ ] **Step 1: Write the protocol header and claim boundary**

Use this exact opening:

```markdown
# R006f Exact-Support Abstention Protocol

**Date:** 2026-07-16
**Status:** FROZEN PRE-OUTCOME PROTOCOL; formal outcomes not yet authorized
**Parent design:** `docs/superpowers/specs/2026-07-16-r006e-r006f-dual-track-design.md`

## Primary Claim

In a fixed low-dimensional design with a known rank-two excitation subspace, an exact query-support certificate accepts a prespecified supported topology query and abstains on a prespecified unsupported query. Paired observationally indistinguishable coefficient worlds establish that a numerical unsupported readout is not identified by the training data.

R006f tests identification and abstention only. It cannot promote CP, Tucker, the R006e candidate or any recovery estimator, and it cannot alter the R006c or R006e verdict.
```

- [ ] **Step 2: Record every frozen constant and construction formula**

Include `N=6`, `T=96`, `r=2`, the ordered node DCT-II basis, normalized temporal DCT columns, `U=[q1,q2]`, `u_perp=q3`, `v1=q4`, `v2=q5`, `W_ref=11'/N`, the exact `x_t`, `h_t`, both epsilon formulas, both endpoint formulas, self-loop permission and the prohibition on nonlinear row normalization exactly as specified in the approved design.

- [ ] **Step 3: Record worlds, estimator controls and gates**

Include the exact `M`, `B0`, `B1`, `beta`, `a`, `sigma`, seed range, FWL min-norm estimator, certificate-aware readout, silent readout and oracle projection diagnostic. Copy every numeric construction, identification, classification, amplification, half-gap and decomposition tolerance from Sections 4.4-4.6 of the approved design.

- [ ] **Step 4: Record governance and stop interpretations**

State explicitly:

```markdown
- Construction code may not receive a seed, noise, outcome, truth error or estimator loss.
- Formal outcome generation requires both an explicit CLI authorization flag and a matching `PASS` pre-outcome hash artifact.
- Any protocol/code/dependency change invalidates the pre-outcome artifact.
- Bug fixes require a failing regression test, a new artifact hash and a complete primary/repeat rerun.
- Outcome-informed changes to endpoint, rank, threshold, excitation, beta, sigma or seed list terminate this protocol version.
- Primary and repeat outputs remain separate and are never pooled.
- No manuscript or claim-ledger edit is allowed before duplicate and result-to-claim audits pass.
```

- [ ] **Step 5: Check the protocol for forbidden ambiguity**

Run:

```bash
rg -n "TBD|TODO|candidate pool|redraw|renormali[sz]e|CP|Tucker|GNN|promote.*estimator" refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md
```

Expected: no `TBD`, `TODO`, candidate-pool, redraw or renormalization permission; CP/Tucker/GNN appear only in the prohibited-claim boundary.

- [ ] **Step 6: Commit the frozen protocol**

```bash
git add refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md
git commit -m "docs: freeze R006f exact-support protocol"
```

Expected: one commit containing only the protocol.

---

### Task 2: Implement The Exact DCT And Fixed-Design Construction

**Files:**
- Create: `scripts/experiments/test_r006f_exact_support.py`
- Create: `scripts/experiments/r006f_exact_support.py`

- [ ] **Step 1: Write failing DCT and configuration tests**

Add:

```python
import unittest
import numpy as np

from scripts.experiments import r006f_exact_support as support


class R006FExactSupportTest(unittest.TestCase):
    def test_frozen_config_and_seed_namespace(self):
        config = support.R006FConfig()
        self.assertEqual((config.n, config.t_len, config.rank), (6, 96, 2))
        self.assertEqual(config.excitation_levels, (1.0, 0.25))
        self.assertEqual(config.seeds, tuple(range(620001, 620051)))

    def test_dct_basis_is_orthonormal_and_has_constant_first_column(self):
        basis = support.dct_ii_basis(6)
        np.testing.assert_allclose(basis.T @ basis, np.eye(6), atol=1e-14)
        np.testing.assert_allclose(basis[:, 0], np.ones(6) / np.sqrt(6), atol=1e-14)
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support.R006FExactSupportTest.test_frozen_config_and_seed_namespace scripts.experiments.test_r006f_exact_support.R006FExactSupportTest.test_dct_basis_is_orthonormal_and_has_constant_first_column -v
```

Expected: `ERROR` because `r006f_exact_support` does not exist.

- [ ] **Step 3: Implement frozen configuration and DCT-II basis**

Create the module with:

```python
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class R006FConfig:
    n: int = 6
    t_len: int = 96
    rank: int = 2
    excitation_levels: tuple[float, ...] = (1.0, 0.25)
    beta: float = 0.50
    sigma: float = 0.05
    kappa_max: float = 50.0
    absolute_floor: float = 1e-12
    support_threshold: float = 0.05
    seeds: tuple[int, ...] = tuple(range(620001, 620051))


def dct_ii_basis(length: int) -> np.ndarray:
    if length < 2:
        raise ValueError("length must be at least two")
    positions = np.arange(length, dtype=float) + 0.5
    frequencies = np.arange(length, dtype=float)
    basis = np.cos(np.pi * positions[:, None] * frequencies[None, :] / length)
    basis[:, 0] *= np.sqrt(1.0 / length)
    basis[:, 1:] *= np.sqrt(2.0 / length)
    return basis
```

- [ ] **Step 4: Run the DCT tests and verify GREEN**

Run the command from Step 2.

Expected: `Ran 2 tests` and `OK`.

- [ ] **Step 5: Write the failing exact-construction test**

Add:

```python
    def test_exact_construction_has_declared_direct_and_excitation_spaces(self):
        construction = support.build_exact_construction(support.R006FConfig(), 1.0)
        self.assertEqual(construction.x.shape, (96, 6))
        self.assertEqual(construction.z.shape, (96, 6))
        np.testing.assert_allclose(construction.x @ construction.v1, np.ones(96), atol=1e-13)
        np.testing.assert_allclose(construction.x.T @ construction.z, np.zeros((6, 6)), atol=1e-12)
        np.testing.assert_allclose(construction.z_tilde, construction.z, atol=1e-12)
```

- [ ] **Step 6: Run the construction test and verify RED**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support.R006FExactSupportTest.test_exact_construction_has_declared_direct_and_excitation_spaces -v
```

Expected: `ERROR` because `build_exact_construction` is absent.

- [ ] **Step 7: Implement the construction dataclass and builder**

Add an `ExactConstruction` dataclass containing `config`, `excitation`, `node_basis`, `time_basis`, `u`, `u_perp`, `v1`, `v2`, `w_ref`, `x`, `h`, `epsilon`, `topology`, `z`, `z_tilde`, `projector_exact`, `delta_w_supported`, `delta_w_unsupported` and `epsilon_star`. Implement the approved formulas literally. Compute residualization as:

```python
projection = np.linalg.lstsq(x, z, rcond=None)[0]
z_tilde = z - x @ projection
```

Build `topology[t]` directly as `w_ref + epsilon * np.outer(u @ h[t], v1)`. Do not clip or normalize it.

- [ ] **Step 8: Run all construction tests**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support -v
```

Expected: all current tests pass.

- [ ] **Step 9: Commit the exact construction**

```bash
git add scripts/experiments/r006f_exact_support.py scripts/experiments/test_r006f_exact_support.py
git commit -m "feat: add exact R006f DCT construction"
```

---

### Task 3: Lock Topology Invariants And Exact/Numerical Certificates

**Files:**
- Modify: `scripts/experiments/test_r006f_exact_support.py`
- Modify: `scripts/experiments/r006f_exact_support.py`

- [ ] **Step 1: Write failing topology and scale tests**

Add tests requiring, for both excitation levels:

```python
    def test_topologies_and_queries_are_nonnegative_row_stochastic_without_normalization(self):
        for level in (1.0, 0.25):
            item = support.build_exact_construction(support.R006FConfig(), level)
            self.assertGreaterEqual(float(item.topology.min()), 0.0)
            np.testing.assert_allclose(item.topology.sum(axis=2), 1.0, atol=1e-12)
            for delta in (item.delta_w_supported, item.delta_w_unsupported):
                endpoint = item.w_ref + delta
                self.assertGreaterEqual(float(endpoint.min()), 0.0)
                np.testing.assert_allclose(endpoint.sum(axis=1), 1.0, atol=1e-12)

    def test_weak_construction_scales_only_training_excitation(self):
        strong = support.build_exact_construction(support.R006FConfig(), 1.0)
        weak = support.build_exact_construction(support.R006FConfig(), 0.25)
        np.testing.assert_allclose(weak.z, strong.z / 4.0, atol=1e-14)
        np.testing.assert_allclose(weak.delta_w_supported, strong.delta_w_supported, atol=0.0)
        np.testing.assert_allclose(weak.delta_w_unsupported, strong.delta_w_unsupported, atol=0.0)
```

- [ ] **Step 2: Run tests and verify RED**

Run the two new test methods with `python3 -m unittest ... -v`.

Expected: at least one failure until endpoint scale and topology invariants are fully implemented.

- [ ] **Step 3: Complete deterministic epsilon and endpoint construction**

Use exactly:

```python
training_outer = np.einsum("ir,tr,j->tij", u, h, v1, optimize=True)
epsilon_strong = 1.0 / (4.0 * n * np.max(np.abs(training_outer)))
epsilon = excitation * epsilon_strong
epsilon_star = 1.0 / (
    4.0 * n * max(
        np.max(np.abs(np.outer(u[:, 0], v2))),
        np.max(np.abs(np.outer(u_perp, v2))),
    )
)
```

Raise `ValueError` unless `excitation` is one of `config.excitation_levels`; do not silently coerce another value.

- [ ] **Step 4: Write failing certificate tests**

Add:

```python
    def test_exact_and_svd_projectors_match_and_queries_separate(self):
        item = support.build_exact_construction(support.R006FConfig(), 1.0)
        sup = support.support_certificate(item, item.delta_w_supported)
        unsup = support.support_certificate(item, item.delta_w_unsupported)
        self.assertEqual(sup.retained_rank, 2)
        self.assertLessEqual(np.linalg.norm(sup.projector_svd - item.projector_exact), 1e-10)
        self.assertLessEqual(sup.chi_exact, 1e-10)
        self.assertLessEqual(sup.chi_svd, 1e-10)
        self.assertGreaterEqual(unsup.chi_exact, 1.0 - 1e-10)
        self.assertGreaterEqual(unsup.chi_svd, 1.0 - 1e-10)

    def test_excitation_changes_singular_values_and_alpha_not_chi(self):
        strong = support.build_exact_construction(support.R006FConfig(), 1.0)
        weak = support.build_exact_construction(support.R006FConfig(), 0.25)
        strong_cert = support.support_certificate(strong, strong.delta_w_supported)
        weak_cert = support.support_certificate(weak, weak.delta_w_supported)
        np.testing.assert_allclose(weak_cert.singular_values[:2], strong_cert.singular_values[:2] / 4.0, rtol=1e-10)
        self.assertAlmostEqual(weak_cert.chi_svd, strong_cert.chi_svd, places=10)
        self.assertAlmostEqual(weak_cert.alpha / strong_cert.alpha, 4.0, places=8)
```

- [ ] **Step 5: Run certificate tests and verify RED**

Expected: `ERROR` because `support_certificate` is absent.

- [ ] **Step 6: Implement `QueryCertificate` and certificate algebra**

The dataclass must store `tau`, full `singular_values`, `retained_rank`, `projector_exact`, `projector_svd`, `projector_error`, `chi_exact`, `chi_svd`, `alpha` and `minimum_retained_singular_value`. Use `tau=max(config.absolute_floor, s_max/config.kappa_max)`. Compute `alpha` from `G=z_tilde.T @ z_tilde / T` using an eigendecomposition of `P G P` and the pseudoinverse square root on eigenvalues above `tau**2/T`.

- [ ] **Step 7: Implement one invariant report**

`validate_construction(construction)` must return named numeric diagnostics and booleans for row sums, non-negativity, residualization, rank, projector error and both query certificates. It must not return a formal claim verdict.

- [ ] **Step 8: Run the full construction test module**

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support -v
```

Expected: all tests pass for both excitation levels.

- [ ] **Step 9: Commit certificate and invariant support**

```bash
git add scripts/experiments/r006f_exact_support.py scripts/experiments/test_r006f_exact_support.py
git commit -m "feat: certify exact R006f query support"
```

---

### Task 4: Implement Paired Observationally Indistinguishable Worlds

**Files:**
- Create: `scripts/experiments/test_r006f_estimators.py`
- Create: `scripts/experiments/r006f_estimators.py`

- [ ] **Step 1: Write failing paired-world tests with a non-official test seed**

Use seed `906001`, never an official `620001-620050` seed:

```python
import unittest
import numpy as np

from scripts.experiments import r006f_exact_support as support
from scripts.experiments import r006f_estimators as estimators


class R006FEstimatorsTest(unittest.TestCase):
    def test_paired_worlds_share_observations_but_not_unsupported_truth(self):
        construction = support.build_exact_construction(support.R006FConfig(), 1.0)
        worlds = estimators.generate_paired_worlds(construction, seed=906001)
        np.testing.assert_array_equal(worlds.world0.y, worlds.world1.y)
        supported_gap = (worlds.world1.b - worlds.world0.b) @ construction.delta_w_supported
        unsupported_gap = (worlds.world1.b - worlds.world0.b) @ construction.delta_w_unsupported
        self.assertLessEqual(np.linalg.norm(supported_gap), 1e-12)
        expected = construction.config.beta * construction.epsilon_star * np.outer(worlds.a, construction.v2)
        np.testing.assert_allclose(unsupported_gap, expected, rtol=1e-10, atol=1e-12)

    def test_seed_changes_noise_but_truth_and_design_remain_fixed(self):
        construction = support.build_exact_construction(support.R006FConfig(), 1.0)
        first = estimators.generate_paired_worlds(construction, seed=906001)
        second = estimators.generate_paired_worlds(construction, seed=906002)
        np.testing.assert_array_equal(first.world0.b, second.world0.b)
        self.assertFalse(np.array_equal(first.world0.y, second.world0.y))
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m unittest scripts.experiments.test_r006f_estimators -v
```

Expected: `ERROR` because `r006f_estimators` does not exist.

- [ ] **Step 3: Implement immutable world dataclasses and generator**

Define `RegressionWorld(m, b, y)` and `PairedWorlds(world0, world1, noise, a, analytic_unsupported_gap)`. Implement:

```python
m = 0.20 * np.eye(n)
b0 = 0.15 * np.eye(n)
a = construction.node_basis[:, 0]
b1 = b0 + config.beta * np.outer(a, construction.u_perp)
noise = np.random.default_rng(seed).normal(size=(config.t_len, n))
y0 = construction.x @ m.T + construction.z @ b0.T + config.sigma * noise
y1 = construction.x @ m.T + construction.z @ b1.T + config.sigma * noise
```

Reject seeds in the official namespace only in test helpers, not in the scientific generator. Official-seed protection belongs to the formal runner.

- [ ] **Step 4: Add an explicit observational-identity guard**

Raise `RuntimeError("paired worlds are not observationally identical")` if `max(abs(y0-y1))>1e-12`. This turns an orientation or basis error into a hard failure before evaluation.

- [ ] **Step 5: Run paired-world tests and verify GREEN**

Expected: `Ran 2 tests` and `OK`.

- [ ] **Step 6: Commit paired-world generation**

```bash
git add scripts/experiments/r006f_estimators.py scripts/experiments/test_r006f_estimators.py
git commit -m "feat: add R006f indistinguishable worlds"
```

---

### Task 5: Implement Certificate-Aware And Silent Readouts

**Files:**
- Modify: `scripts/experiments/test_r006f_estimators.py`
- Modify: `scripts/experiments/r006f_estimators.py`

- [ ] **Step 1: Write failing FWL fit and readout tests**

Add:

```python
    def test_certificate_aware_readout_returns_supported_and_abstains_unsupported(self):
        construction = support.build_exact_construction(support.R006FConfig(), 1.0)
        worlds = estimators.generate_paired_worlds(construction, seed=906001)
        b_hat = estimators.fwl_min_norm_fit(construction.x, construction.z, worlds.world0.y)
        sup_cert = support.support_certificate(construction, construction.delta_w_supported)
        unsup_cert = support.support_certificate(construction, construction.delta_w_unsupported)
        sup = estimators.certificate_aware_readout(b_hat, construction.delta_w_supported, sup_cert, 0.05)
        unsup = estimators.certificate_aware_readout(b_hat, construction.delta_w_unsupported, unsup_cert, 0.05)
        self.assertEqual(sup.status, "SUPPORTED")
        self.assertIsNotNone(sup.value)
        self.assertEqual(unsup.status, "UNSUPPORTED")
        self.assertIsNone(unsup.value)

    def test_silent_readout_always_returns_a_number(self):
        construction = support.build_exact_construction(support.R006FConfig(), 1.0)
        worlds = estimators.generate_paired_worlds(construction, seed=906001)
        b_hat = estimators.fwl_min_norm_fit(construction.x, construction.z, worlds.world0.y)
        readout = estimators.silent_readout(b_hat, construction.delta_w_unsupported)
        self.assertEqual(readout.status, "NUMERIC_UNSUPPORTED")
        self.assertTrue(np.isfinite(readout.value).all())
```

- [ ] **Step 2: Run tests and verify RED**

Expected: `ERROR` because fit/readout functions are absent.

- [ ] **Step 3: Implement FWL min-norm fitting**

Use:

```python
x_coef = np.linalg.lstsq(x, y, rcond=None)[0]
y_tilde = y - x @ x_coef
z_coef = np.linalg.lstsq(x, z, rcond=None)[0]
z_tilde = z - x @ z_coef
b_transpose = np.linalg.pinv(z_tilde) @ y_tilde
return b_transpose.T
```

Validate aligned two-dimensional arrays and finite values before fitting.

- [ ] **Step 4: Implement readout dataclass and controls**

Define `QueryReadout(status: str, value: np.ndarray | None, chi: float)`. The certificate-aware path uses `certificate.chi_svd`; the silent path must label its output `NUMERIC_UNSUPPORTED`, not `SUPPORTED`.

- [ ] **Step 5: Write failing decomposition and half-gap tests**

For the same fitted `b_hat`, verify:

```python
gap = worlds.analytic_unsupported_gap
error0 = np.linalg.norm(silent.value - worlds.world0.b @ construction.delta_w_unsupported)
error1 = np.linalg.norm(silent.value - worlds.world1.b @ construction.delta_w_unsupported)
self.assertGreaterEqual(max(error0, error1) + 1e-12, 0.5 * np.linalg.norm(gap))

p = construction.projector_exact
delta = construction.delta_w_unsupported
b = worlds.world1.b
np.testing.assert_allclose(delta.T @ b.T, delta.T @ p @ b.T + delta.T @ (np.eye(6)-p) @ b.T, atol=1e-10)
```

- [ ] **Step 6: Implement `analytic_diagnostics`**

Return `paired_observation_max_difference`, `supported_truth_gap`, `unsupported_truth_gap_relative_error`, `silent_error_world0`, `silent_error_world1`, `half_gap_lower_bound_satisfied` and `decomposition_residual`. Do not calculate a comparative estimator win rate.

- [ ] **Step 7: Run estimator tests**

```bash
python3 -m unittest scripts.experiments.test_r006f_estimators -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit readout and analytic gates**

```bash
git add scripts/experiments/r006f_estimators.py scripts/experiments/test_r006f_estimators.py
git commit -m "feat: add R006f abstention readouts"
```

---

### Task 6: Lock Same-Noise Excitation Scaling

**Files:**
- Modify: `scripts/experiments/test_r006f_estimators.py`
- Modify: `scripts/experiments/r006f_estimators.py`

- [ ] **Step 1: Write the failing paired-excitation test**

Add:

```python
    def test_same_noise_supported_query_error_scales_with_inverse_excitation(self):
        config = support.R006FConfig()
        strong = support.build_exact_construction(config, 1.0)
        weak = support.build_exact_construction(config, 0.25)
        strong_worlds = estimators.generate_paired_worlds(strong, seed=906001)
        weak_worlds = estimators.generate_paired_worlds(weak, seed=906001)
        np.testing.assert_array_equal(strong_worlds.noise, weak_worlds.noise)
        strong_hat = estimators.fwl_min_norm_fit(strong.x, strong.z, strong_worlds.world0.y)
        weak_hat = estimators.fwl_min_norm_fit(weak.x, weak.z, weak_worlds.world0.y)
        delta = strong.delta_w_supported
        strong_error = np.linalg.norm((strong_hat - strong_worlds.world0.b) @ delta)
        weak_error = np.linalg.norm((weak_hat - weak_worlds.world0.b) @ delta)
        self.assertAlmostEqual(weak_error / strong_error, 4.0, places=8)
```

- [ ] **Step 2: Run the test and verify RED if implementation leaks excitation into endpoints/noise**

Run the single method with `python3 -m unittest ... -v`.

Expected before correction: failure if noise streams, endpoints or nuisance residualization differ across levels. If it already passes, retain it as a regression test and do not alter the construction.

- [ ] **Step 3: Implement `evaluate_seed` with excitation pairing**

`evaluate_seed(config, seed)` must build both excitation levels, reuse the seed-keyed noise, and emit deterministic rows with identity fields:

```text
seed, excitation, world, endpoint, evaluator
```

and metrics:

```text
chi_exact, chi_svd, alpha, retained_rank, minimum_retained_singular_value,
readout_status, query_error, paired_observation_max_difference,
truth_gap, truth_gap_relative_error, half_gap_lower_bound_satisfied,
decomposition_residual
```

It must emit explicit `UNSUPPORTED` rows with an empty numeric readout, not drop them.

- [ ] **Step 4: Add an aggregate excitation-ratio helper**

Implement `excitation_scaling_diagnostics(rows)` to pair by seed/world/endpoint/evaluator and return singular-value, alpha, chi and supported-error ratios. Raise on missing or duplicate identities.

- [ ] **Step 5: Run all construction and estimator tests**

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support scripts.experiments.test_r006f_estimators -v
```

Expected: all tests pass; no official output directory is created.

- [ ] **Step 6: Commit excitation scaling**

```bash
git add scripts/experiments/r006f_estimators.py scripts/experiments/test_r006f_estimators.py
git commit -m "test: lock R006f excitation scaling"
```

---

### Task 7: Add Pre-Outcome Hashing And Construction-Only CLI

**Files:**
- Create: `scripts/experiments/test_r006f_exact_support_abstention.py`
- Create: `scripts/experiments/r006f_exact_support_abstention.py`

- [ ] **Step 1: Write failing provenance and construction-gate tests**

Use `tempfile.TemporaryDirectory()` and assert:

```python
artifact = experiment.write_construction_gate(config, output_dir)
self.assertEqual(artifact["status"], "PASS")
self.assertRegex(artifact["artifact_sha256"], r"^[0-9a-f]{64}$")
self.assertEqual(set(artifact["provenance"]["code_sha256"]), {
    "support", "estimators", "runner"
})
self.assertEqual(artifact["config"]["seeds"], list(range(620001, 620051)))
self.assertFalse((output_dir / "r006f_replications.csv").exists())
experiment.verify_construction_gate(config, output_dir)
```

- [ ] **Step 2: Run tests and verify RED**

Expected: `ERROR` because the runner module does not exist.

- [ ] **Step 3: Implement provenance hashing**

Hash these exact inputs:

```text
refine-logs/R006F_EXACT_SUPPORT_ABSTENTION_PROTOCOL_20260716.md
docs/superpowers/specs/2026-07-16-r006e-r006f-dual-track-design.md
scripts/experiments/r006f_exact_support.py
scripts/experiments/r006f_estimators.py
scripts/experiments/r006f_exact_support_abstention.py
```

Store Python, NumPy and platform versions separately. Compute `artifact_sha256` from canonical JSON (`sort_keys=True`, compact separators) after removing `generated_at` and `artifact_sha256` itself.

- [ ] **Step 4: Implement construction-only gate aggregation**

For both excitation levels, store full singular spectra, exact/SVD projector hashes, epsilon values, topology minima and row-sum errors, both query certificates and every gate boolean. Status is `PASS` only if every frozen construction gate passes.

- [ ] **Step 5: Implement hash-verifying gate loader**

`verify_construction_gate` must reject missing artifact, non-`PASS` status, config mismatch, provenance mismatch or canonical artifact-hash mismatch before importing/calling any outcome generator.

- [ ] **Step 6: Implement a construction-only CLI mode**

Support:

```bash
python3 scripts/experiments/r006f_exact_support_abstention.py \
  --construction-gate-only \
  --output-dir output/high_impact_revision/r006f_exact_support_abstention
```

This mode is the only repository output command authorized during implementation. Expected: writes only `construction_gate_preoutcome.json`, prints `R006f construction gate: PASS`, and exits zero.

- [ ] **Step 7: Test in a temporary directory**

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support_abstention -v
```

Expected: provenance and construction tests pass without official outcomes.

- [ ] **Step 8: Commit pre-outcome governance**

```bash
git add scripts/experiments/r006f_exact_support_abstention.py scripts/experiments/test_r006f_exact_support_abstention.py
git commit -m "feat: freeze R006f pre-outcome provenance"
```

---

### Task 8: Isolate Formal Outcomes And Serialize Analytic Gates

**Files:**
- Modify: `scripts/experiments/test_r006f_exact_support_abstention.py`
- Modify: `scripts/experiments/r006f_exact_support_abstention.py`

- [ ] **Step 1: Write failing authorization and hash-mismatch tests**

Add tests that patch `r006f_estimators.evaluate_seed` and assert it is never called when:

```python
with self.assertRaisesRegex(RuntimeError, "explicit authorization"):
    experiment.run_formal(config, output_dir, authorized=False)
```

and when the stored protocol hash is changed to `"0" * 64`. Assert no replication/result file exists after either rejection.

- [ ] **Step 2: Run tests and verify RED**

Expected: failures until `run_formal` enforces both barriers.

- [ ] **Step 3: Implement formal output isolation**

Require:

```python
FORMAL_DIR_NAMES = {
    "r006f_exact_support_abstention",
    "r006f_exact_support_abstention_repeat",
}
```

`run_formal` must reject `authorized=False`, reject an output basename outside this set, verify the pre-outcome artifact, refuse to overwrite an existing `r006f_results.json`, then evaluate exactly the 50 frozen seeds. Unit tests must create a nested directory with one of these two exact basenames inside `TemporaryDirectory`; do not weaken the basename check for tests.

- [ ] **Step 4: Implement deterministic serialization**

Sort rows by `(seed, excitation, world, endpoint, evaluator)`. Write:

```text
r006f_replications.csv
r006f_results.json
r006f_results.md
```

The JSON payload must contain `run_type="FULL_PROTOCOL"`, config, provenance, construction artifact hash, environment, row count, every analytic gate, and `status` in `{PASS, FAIL, CONSTRUCTION_FAIL}`. Runtime and generation timestamp are metadata only.

- [ ] **Step 5: Implement exact gate aggregation**

Require all frozen gates from approved design Section 4.6. Classification counts must be exactly 50 supported returns and 50 unsupported abstentions at each excitation level. Treat missing/non-finite rows as `FAIL`; never filter them. Do not add a method-win or promotion field.

- [ ] **Step 6: Add CLI parser tests without running official outcomes**

Require parser behavior:

```python
args = parser.parse_args(["--formal-outcomes", "--output-dir", str(output_dir)])
self.assertTrue(args.formal_outcomes)
self.assertFalse(args.construction_gate_only)
```

The parser must make the three execution flags `--formal-outcomes`, `--construction-gate-only` and `--result-to-claim-audit` mutually exclusive. `--compare-to PATH` is an auxiliary path: by itself it selects duplicate comparison; with `--result-to-claim-audit` it supplies the required repeat directory. Reject `--result-to-claim-audit` without `--compare-to`, and reject `--compare-to` when either construction or formal mode is selected.

- [ ] **Step 7: Document but do not execute the future formal commands**

After separate authorization, the future operator will run:

```bash
python3 scripts/experiments/r006f_exact_support_abstention.py \
  --formal-outcomes \
  --output-dir output/high_impact_revision/r006f_exact_support_abstention

python3 scripts/experiments/r006f_exact_support_abstention.py \
  --formal-outcomes \
  --output-dir output/high_impact_revision/r006f_exact_support_abstention_repeat
```

**Do not run either command while executing this implementation plan unless the user separately authorizes formal outcomes after inspecting the pre-outcome artifact.**

- [ ] **Step 8: Run only unit tests**

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support_abstention -v
```

Expected: all tests pass and official result files remain absent.

- [ ] **Step 9: Commit the isolated formal runner**

```bash
git add scripts/experiments/r006f_exact_support_abstention.py scripts/experiments/test_r006f_exact_support_abstention.py
git commit -m "feat: isolate R006f formal outcomes"
```

---

### Task 9: Add Independent Duplicate And Result-To-Claim Audits

**Files:**
- Modify: `scripts/experiments/test_r006f_exact_support_abstention.py`
- Modify: `scripts/experiments/r006f_exact_support_abstention.py`

- [ ] **Step 1: Write failing duplicate-comparison tests using synthetic temporary artifacts**

Create two minimal temporary run directories with identical CSV/JSON payloads except `generated_at` and `elapsed_seconds`. Require `PASS` and zero non-runtime differences. Then alter one `chi_svd` CSV value and require `FAIL` with the changed identity and field recorded.

- [ ] **Step 2: Implement strict duplicate comparison**

Compare CSV rows by `(seed, excitation, world, endpoint, evaluator)`. Normalize JSON by removing only `generated_at`, `elapsed_seconds`, runtime-named fields and absolute output-directory strings. Do not ignore status, gates, hashes, errors, certificates or readout values. Write `r006f_duplicate_comparison.json` only in the primary directory.

- [ ] **Step 3: Write failing result-to-claim audit tests**

Test three cases:

```text
formal PASS + duplicate PASS -> claim_verdict=SUPPORTED_WITHIN_R006F_SCOPE
formal FAIL + duplicate PASS -> claim_verdict=NOT_SUPPORTED
formal PASS + duplicate FAIL -> claim_verdict=NOT_AUDITABLE
```

Every case must include prohibited claims for estimator superiority, native recovery, dynamic generality, causal topology effects and rescue of R006e.

- [ ] **Step 4: Implement `audit_result_to_claim`**

Require both directories, matching construction/provenance hashes, `FULL_PROTOCOL` run types, exact seed/grid identity and a passing duplicate comparison. The sole allowed positive wording is:

```text
In the prespecified N=6 fixed-design stress test, the exact support certificate accepted the supported query and abstained on the unsupported query; paired observationally indistinguishable worlds showed that an unsupported numerical readout was not identified by the training data.
```

Never emit that wording unless all formal gates and duplicate audit pass. Write `r006f_result_to_claim_audit.json` and `.md` in the primary directory.

- [ ] **Step 5: Test CLI audit isolation**

`--compare-to REPEAT` may only compare existing outputs. `--result-to-claim-audit --compare-to REPEAT` may only read existing formal outputs and write audit artifacts; neither path may call `evaluate_seed`.

- [ ] **Step 6: Run the audit tests**

```bash
python3 -m unittest scripts.experiments.test_r006f_exact_support_abstention -v
```

Expected: duplicate mutation is detected; all claim-verdict branches pass.

- [ ] **Step 7: Commit audit logic**

```bash
git add scripts/experiments/r006f_exact_support_abstention.py scripts/experiments/test_r006f_exact_support_abstention.py
git commit -m "feat: audit R006f duplicates and claims"
```

---

### Task 10: Complete Pre-Outcome Verification Without Outcomes

**Files:**
- Modify only if a failing regression test justifies it:
  - `scripts/experiments/r006f_exact_support.py`
  - `scripts/experiments/r006f_estimators.py`
  - `scripts/experiments/r006f_exact_support_abstention.py`
  - their three test modules
- Generate: `output/high_impact_revision/r006f_exact_support_abstention/construction_gate_preoutcome.json`

- [ ] **Step 1: Run the complete R006f unit suite**

```bash
python3 -m unittest \
  scripts.experiments.test_r006f_exact_support \
  scripts.experiments.test_r006f_estimators \
  scripts.experiments.test_r006f_exact_support_abstention -v
```

Expected: all tests pass; no official outcome file exists.

- [ ] **Step 2: Run relevant legacy support tests**

```bash
python3 -m unittest \
  scripts.experiments.test_r006d_endpoint_support \
  scripts.experiments.test_r006d_construction_gate -v
```

Expected: all legacy tests pass; R006d remains unchanged and recorded as `CONSTRUCTION_FAIL`.

- [ ] **Step 3: Generate the authorized construction-only artifact**

```bash
python3 scripts/experiments/r006f_exact_support_abstention.py \
  --construction-gate-only \
  --output-dir output/high_impact_revision/r006f_exact_support_abstention
```

Expected: `R006f construction gate: PASS`; exactly one new file, `construction_gate_preoutcome.json`.

- [ ] **Step 4: Inspect the artifact without reading outcomes**

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("output/high_impact_revision/r006f_exact_support_abstention/construction_gate_preoutcome.json")
x = json.loads(p.read_text())
assert x["status"] == "PASS"
assert x["config"]["seeds"] == list(range(620001, 620051))
assert set(x["construction"]) == {"1.0", "0.25"}
assert not list(p.parent.glob("r006f_replications.csv"))
assert not list(p.parent.glob("r006f_results.*"))
print(x["artifact_sha256"])
PY
```

Expected: one 64-character SHA-256 line and no assertion failure.

- [ ] **Step 5: Scan for prohibited cross-track and outcome paths**

```bash
rg -n "r006e|r006c_endpoint_aware|anchor_split|dw_joint|CP|Tucker|GNN" \
  scripts/experiments/r006f_*.py
```

Expected: no imports or execution paths into R006e/R006c estimators; any matched text occurs only in explicit prohibited-claim strings in the audit.

- [ ] **Step 6: Verify the worktree and commit the pre-outcome artifact**

```bash
git status --short
git add output/high_impact_revision/r006f_exact_support_abstention/construction_gate_preoutcome.json
git commit -m "chore: freeze R006f pre-outcome artifact"
```

Expected: the commit contains the construction artifact only. Formal outcome, duplicate and claim-audit files remain absent.

- [ ] **Step 7: Stop for explicit authorization**

Report the construction artifact hash, test count, exact gate status and absence of formal outcomes. Do not proceed to the two `--formal-outcomes` commands in Task 8 without a new explicit user instruction.

---

## Post-Authorization Run Order

This section is operational sequencing, not authorization.

1. Verify a clean worktree and the committed pre-outcome hash.
2. Run the primary formal command once.
3. Run the repeat formal command independently in the repeat directory.
4. Run duplicate comparison:

```bash
python3 scripts/experiments/r006f_exact_support_abstention.py \
  --compare-to output/high_impact_revision/r006f_exact_support_abstention_repeat \
  --output-dir output/high_impact_revision/r006f_exact_support_abstention
```

5. Run result-to-claim audit:

```bash
python3 scripts/experiments/r006f_exact_support_abstention.py \
  --result-to-claim-audit \
  --compare-to output/high_impact_revision/r006f_exact_support_abstention_repeat \
  --output-dir output/high_impact_revision/r006f_exact_support_abstention
```

6. Preserve `FAIL`, `CONSTRUCTION_FAIL` or `NOT_AUDITABLE` unchanged. Do not edit the manuscript or claim ledger unless the audit returns `SUPPORTED_WITHIN_R006F_SCOPE`.

## Final Claim Boundary

Even a complete R006f `PASS` supports only exact certificate behavior and the paired-world identification statement in this fixed `N=6` design. It does not establish estimator superiority, time-varying VAR recovery, finite-horizon response accuracy, performance under endogenous state dynamics, topology-family generalization, uncertainty calibration, causal effects or application validity.
