# E3 Static Candidate Preflight

Date: 2026-07-23

Status: `STATIC_CANDIDATE_PREFLIGHT_PASS`; `NOT_AUTHORIZED_FOR_SCIENTIFIC_EXECUTION`.

## Frozen Candidate

- Candidate ID: `e3-family2-synthetic-v1-20260723-run1`
- Candidate SHA-256: `5974a68832587092580b64c141128469dd06376bd279477e9a3bf81e5b8120c8`
- Candidate path: `refine-logs/e3_family2_candidates/e3-family2-synthetic-v1-20260723-run1/candidate.json`
- Bound quarantine root: `refine-logs/e3_family2_quarantine/e3-family2-synthetic-v1-20260723-run1-quarantine`

The quarantine root did not exist before or after preflight. No authorization
JSON has been generated, installed or approved.

## Static Checks Passed

1. The candidate SHA-256 matched the bytes on disk.
2. The schema-v1 candidate, source closure, single dependency lock, eight
   `CANDIDATE_READY` artifacts, two synthetic inputs and canonical
   configuration all passed their semantic validators.
3. The candidate binds these eight artifact IDs: `family2_query_contract`,
   `family2_factorization_proof_packet`, `exact_fixture_manifest`,
   `comparator_registry`, `tuning_split_manifest`, `failure_metric_schema`,
   `authorization_gate_tests` and `duplicate_and_claim_audit_design`.
4. A deliberate call without an authorization file refused with
   `execution authorization and its exact SHA-256 are required`; the
   quarantine root remained absent.

This record reports no numerical output. It does not authorize E3-1, E3-2,
E3-3 or E3-4 execution, alter either controlling audit state, inspect
RCEP/NYC/R006e/R006f, or permit manuscript promotion.

## Required Exact Authorization

Before the candidate can run, the workspace author must explicitly approve the
candidate SHA above for exactly one invocation at the bound quarantine root.
Only then may an authorization JSON be created to record that instruction; its
SHA-256 is verified by the executor at invocation time. The record must keep
`r006e_outcome_authorized`, `r006f_outcome_authorized` and
`downstream_builds_authorized` false, and must prohibit manuscript promotion.
