# RCEP Helper Trust Manifest Candidate Review

Date: 2026-07-19

Status: **CANDIDATE VALID; NOT INSTALLED; EXECUTION NOT AUTHORIZED**

## Candidate Identity

- Candidate file: `refine-logs/RCEP_HELPER_TRUST_MANIFEST_CANDIDATE_20260719.json`
- Candidate SHA-256: `02b151473116bbea39e1dc200f7299cd1d1a3451f8e430bc4d59392eb2525256`
- Schema version: `2`
- Selected helper: `C3`
- Helper commit: `d0e398b896848f26413cf9aa9dfca15fb4e7ce64`
- Bound files: `config.py`, `research_data_construction.py`, `research_network_tvp_var.py`

The candidate contains only the three keys accepted by the production schema: `schema_version`, `helper_git_commit` and `files`. It contains no absolute helper path, credential, environment value, execution instruction or scientific result.

## Static Production-Guard Check

The candidate was supplied temporarily to `_validated_helper_identity()` together with the selected C3 checkout. The guard accepted:

- the exact schema and three-file set;
- the C3 Git commit;
- all three file SHA-256 values;
- Git tracking for all three files; and
- clean status for all three files relative to the frozen commit.

The check did not call `require_raw_helper()`, import any helper module, load data, construct output paths or run RCEP/NYC estimation.

## Authorization Boundary

- `candidate_selected = true`
- `manifest_candidate_generated = true`
- `production_manifest_installed = false`
- `production_trust_granted = false`
- `scientific_execution_authorized = false`
- `R006e outcome authorized = false`
- `R006f outcome authorized = false`

The production path `manuscript_src/natcs/rcep_helper_trust_manifest.json` remains absent. The candidate cannot affect runtime unless a later, explicit author instruction authorizes installation at that exact path.

## Next Separate Decision

Installation requires a new authorization that identifies the candidate by SHA-256. A valid installation-only instruction is:

> I approve installing candidate SHA-256 `02b151473116bbea39e1dc200f7299cd1d1a3451f8e430bc4d59392eb2525256` as `manuscript_src/natcs/rcep_helper_trust_manifest.json`. This authorizes installation and static gate verification only; it does not authorize RCEP/NYC scientific execution or R006e/R006f outcomes.

This staging serves `rigour` and `reproducibility` by separating code identity, installation and scientific execution into independently reviewable decisions.

