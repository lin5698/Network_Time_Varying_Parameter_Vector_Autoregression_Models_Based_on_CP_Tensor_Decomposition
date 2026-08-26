# Production Scientific Authorization Approval

Recorded at: 2026-07-19T03:13:04Z  
Authorizer: workspace author through explicit instruction in the active Codex task

## Approved One-Time Invocations

1. RCEP
   - Candidate: `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_RCEP_20260719.json`
   - Approved SHA-256: `04eb83670e0648d8e42e0194fcb3795499c296363ae91b6dc8e94fd2d7f14d84`
   - Decision ID: `psa-20260719-rcep-01`
2. NYC Taxi
   - Candidate: `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_NYC_20260719.json`
   - Approved SHA-256: `4155bbed29b18be0fcd6d7c052439e26e946fcc37c47f6170862a1a0c3a8bd5d`
   - Decision ID: `psa-20260719-nyc-01`
3. RCEP remediation
   - Candidate: `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_RCEP_02_20260719.json`
   - Approved SHA-256: `c06b34c44081a390d0ea277db8c80640ccd7e0737b6dc0fc83f1ddc255f47fbc`
   - Decision ID: `psa-20260719-rcep-02`
4. RCEP rank-deficiency remediation
   - Candidate: `SCIENTIFIC_EXECUTION_AUTHORIZATION_CANDIDATE_RCEP_03_20260719.json`
   - Approved SHA-256: `ab9556bef62a8086bb6b05787f5442318107507ed8ffc06b9b289747f22f347f`
   - Decision ID: `psa-20260719-rcep-03`
   - Scope: one invocation using only the repaired runner, authorized helper,
     two bound CSV inputs, frozen numeric arguments and new quarantine output
     root declared by the candidate

Each approval permits exactly one production invocation using only the input
identity, numeric arguments and new quarantine output root bound in the named
candidate. An invocation that reserves its output namespace consumes that
decision ID even if the run later fails. No automatic retry, overwrite or
output-root reuse is authorized.

## Explicitly Not Authorized

- R006e outcome execution or inspection;
- R006f outcome execution or inspection;
- downstream evidence or manuscript builds;
- manuscript promotion of any produced artifact;
- execution with a different candidate SHA-256, implementation hash, input
  identity, numeric argument or output root.

Produced artifacts must remain quarantined until an inventory and SHA-256
closure is frozen and an independent result/claim audit is completed.
