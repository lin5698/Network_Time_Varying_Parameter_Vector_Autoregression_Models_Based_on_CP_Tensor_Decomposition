# NCS E4 r3 Detached-execution Readiness

**Date:** 2026-07-31  
**Status:** CANDIDATE_READY_NOT_AUTHORIZED  
**Candidate:** `e4-domain-stable-v4-20260731-candidate-r3`  
**Candidate SHA-256:**
`0c49bca63813316ed65119f0f891074a290bd03392e5e9121c435dc936c199f6`

## Purpose

r3 replaces the consumed-incomplete r2 execution identity after the attached
PTY process was externally terminated. It does not change the scientific
question, grid, estimator, uncertainty procedure, failure retention or claim
boundary.

## Static equivalence to r2

Direct comparison confirms equality of:

- candidate schema version;
- synthetic-only execution scope and excluded routes;
- trust policy;
- complete source-hash closure;
- runner SHA-256;
- scientific configuration and configuration SHA-256;
- frozen synthetic specification input;
- all eight pre-outcome artifact content hashes.

The package-local node-order and dependency-lock paths, candidate identity,
artifact paths and quarantine output root are new, as required for a distinct
one-time attempt. Their contents remain semantically validated.

## Static verification

The full r3 candidate validation path passes:

- execution-candidate shape;
- source and dependency hashes;
- eight artifact hashes and semantic validators;
- synthetic inputs;
- configuration and bootstrap-history bindings;
- new absent quarantine-root rule.

The frozen quarantine root is:

`refine-logs/e3_family2_quarantine/e4-domain-stable-v4-20260731-quarantine-r3`

It remains absent.

## Durable launch correction

The next authorized run must not be attached to the interactive execution PTY.
A local `launchd` LaunchAgent will be generated only after exact authorization
so that its command binds the final authorization SHA. Its contract is:

- `RunAtLoad=true`;
- `KeepAlive=false`;
- one executor command only;
- bound candidate and authorization SHA arguments;
- standard output and error written to an operational log, not a manuscript
  evidence path;
- no automatic retry after any exit;
- job unloaded after terminal status is recorded.

A non-scientific 30-second probe completed once with `runs=1`, exit code 0 and
no restart, then was unloaded and removed.

## Authorization boundary

No r3 authorization file exists. No r3 scientific process or output root has
been created. Exact authorization must bind candidate SHA-256
`0c49bca63813316ed65119f0f891074a290bd03392e5e9121c435dc936c199f6`
before launch. RCEP, NYC, R006e, R006f, downstream builds, audit-status changes
and manuscript promotion remain prohibited.
