# RCEP/NYC Scientific Execution Authorization v1

This contract separates static production trust from permission to execute a scientific rebuild. Installing a helper trust manifest does not authorize data access, estimation, outcome inspection, downstream evidence builds or manuscript promotion.

## One Manifest Per Dataset

Each authorization must bind exactly one invocation of `scripts/run_cp_empirical_pipeline.py` for either `rcep` or `nyc_taxi`. The runner requires all of the following CLI arguments:

```text
--dataset
--authorization
--authorization-sha256
--output-root
--window
--p
--n-boot
--block-size
--cp-inits
--cp-max-iter
--cp-tol
```

The authorization file is read once through an `O_NOFOLLOW` descriptor. The runner verifies the separately approved SHA-256 over that in-memory snapshot and parses only those verified bytes.

## Required Bindings

The schema binds:

1. decision ID, authorizer and authorization time;
2. exact dataset and numeric arguments;
3. SHA-256 values for the runner and its design-contract dependency;
4. dataset-specific input identity;
5. a new absolute output root under `output/natcs_empirical_cp_authorized_runs/<decision_id>/<dataset>`;
6. overwrite denial and post-run quarantine/audit obligations;
7. explicit exclusion of R006e/R006f outcomes, downstream builds and manuscript promotion.

For RCEP, the runner's frozen input contract selects two required CSV filenames from the authorized helper checkout or its declared fallback data directory. The authorization binds the resolved path and SHA-256 of each selected file. The helper trust manifest and all three bound Python sources are read through `O_NOFOLLOW` descriptors; helper modules are compiled and executed from the verified in-memory source snapshots rather than re-imported from mutable paths. Static and runtime guards reject relative imports, dynamic code/import controls, import-path mutation and module resolution outside the three in-memory helper modules or the invoking interpreter's standard-library and installed-package roots. The helper builtins map is read-only and omits direct file and dynamic-code execution primitives, helper-added search paths are not retained, and a cached helper is reused only after the current checkout reproduces the same authorized identity. The verified helper bytes are the authorized trust root; this is a constrained loader, not a general sandbox for malicious authorized source. The two CSV files are likewise parsed only from verified in-memory byte snapshots.

For NYC, the authorization binds the verified `datasets/NYC-taxi` path and frozen upstream commit. For each required annual NPZ file, the runner computes the expected SHA-256 from the corresponding blob stored at that commit, compares the worktree file through a no-follow snapshot, and uses the same commit-derived SHA-256 for the final in-memory read. Git index flags such as `assume-unchanged` therefore cannot substitute modified bytes for the frozen source.

## Output Isolation

The authorized output target and its decision directory must not exist. Before reserving them, the runner verifies the current RCEP helper checkout or NYC checkout and reads every authorized dataset file through a no-follow descriptor into a hash-verified in-memory snapshot. It parses those snapshots, validates panel/date/unit/GIRF schemas and validates or constructs the dataset topology before reserving the base, decision, dataset and figure directories through no-follow directory descriptors. Reservation therefore precedes estimator fitting, bootstrap, GIRF computation and scientific output writes, but follows authorized data parsing and structural preprocessing. The runner records the dataset and figure directory device/inode identities; every CSV, JSON, PNG and PDF is created relative to a revalidated directory with `O_CREAT|O_EXCL|O_NOFOLLOW`. Existing files, child symlinks, replaced parent directories and directory reuse are rejected. A failed run after reservation leaves its quarantine directory in place and it cannot be reused.

The authorization gate is a scientific-execution boundary, not a Python-process bootstrap sandbox. Module imports and creation of the configured Matplotlib/XDG cache directories occur when the runner module starts, before the authorization document is evaluated. The verified ordering claim is narrower and explicit: the gate precedes helper loading, authorized RCEP/NYC input reads, estimator/statistical/GIRF calls and creation of the scientific quarantine output tree. Callers must therefore treat the interpreter, installed dependencies and configured cache locations as trusted static runtime prerequisites.

The isolated output tree is not a manuscript evidence tree. Promotion requires a separate inventory freeze, SHA-256 closure, independent result/claim audit and explicit promotion authorization. `scripts/build_natcs_evidence.mjs` and `scripts/build_natcs_manuscript.mjs` are outside this execution authorization.

## Current State

`refine-logs/SCIENTIFIC_EXECUTION_AUTHORIZATION_TEMPLATE_V1.json` is deliberately `NOT_AUTHORIZED` and contains `UNSET` fields. It is a schema template, not an executable candidate. No scientific command may be assembled from it until a completed candidate is reviewed and its exact SHA-256 is explicitly approved.
