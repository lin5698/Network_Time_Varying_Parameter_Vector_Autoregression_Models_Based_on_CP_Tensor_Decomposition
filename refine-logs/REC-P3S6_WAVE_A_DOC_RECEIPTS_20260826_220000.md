# REC-P3S6 WAVE A DOCUMENTATION RECEIPTS (2026-08-26)

Authorized: author Wave A decision (2026-08-26). These receipts characterize implementation
semantics from frozen, already value-audited artifacts. They do NOT activate any quarantined
result; the RCEP and NYC empirical sections remain inactive boundary drafts until a later
re-adjudication and author promotion decision. Review-only, fail-closed register.

## RCEP F1 - GIRF date substitution
- Characterization: `resolve_target_dates` substitutes the nearest STABLE date when a requested
  date is unstable (scripts/run_cp_empirical_pipeline.py:1533-1545). The rule reproduces the
  observed 2022-12-31 -> 2020-03-31 mapping from the frozen stability_summary.csv.
- Evidence: girf_cp_point.json:37 confirms the literal "2022-12-31" key; substitution rule at
  :1533-1545; frozen stability_summary.csv radii.
- Residual scope: none for characterization. Artifact provenance already value-audited.
- Wording proposal (register): "Requested GIRF dates that fall on unstable-period points are
  resolved to the nearest stable quarterly date by the declared substitution rule."

## NYC-a - stability_rate semantics
- Characterization: the metric is computed as mean(radius >= 1.0), i.e. the UNSTABLE-origin
  share, despite its name (:2913; 48/69 origins verified).
- Evidence: scripts/run_cp_empirical_pipeline.py:2913; 48/69 radius observations.
- Residual scope: naming gloss only; no numeric change.
- Wording proposal: "stability_rate denotes the share of origins with normalized radius at or
  above 1.0 (the unstable-origin share), per the computed predicate radius>=1.0."

## NYC-b - GIRF date remap
- Characterization: same nearest-stable-date rule as RCEP F1; both remaps verified against
  frozen stability_summary.csv radii: 2019-12-31 (radius 1.0027) -> 2020-03-31 and 2021-12-31
  (radius 1.617) -> 2020-04-30, matching selection_summary.
- Evidence: stability_summary.csv radii; selection_summary mappings; rule :1533-1545.
- Residual scope: none.
- Wording proposal: mirror of F1 for the NYC quarterly schedule.

## NYC-c - origins 66-of-69
- Characterization: warm-up skip of the first max(ranks)-1 = 3 origins after the cutoff filter
  (:1311-1314, :1358) fully explains 66-of-69. RCEP 24->21 follows identical arithmetic.
- Evidence: :1311-1314, :1358; rank-warm-up arithmetic.
- Residual scope: none.
- Wording proposal: "The leading max(rank)-1 origins are skipped as a warm-up after the cutoff
  filter, accounting for the 66-of-69 (NYC) and 21-of-24 (RCEP) origin coverage."

## Flag d - RNG seed provenance
- Characterization: deterministic seeds are present in source (root 20260328 at
  :1244/:1735/:1758/:2779) but are NOT echoed into the produced artifacts.
- Evidence: source seed assignments at the cited lines; absence of seed echo in frozen outputs.
- Residual scope: echoing seeds into artifacts (and any run) is deferred to Wave B.
- Wording proposal: "All empirical runs use a fixed documented seed (root 20260328); artifact
  seed echo is implemented in the Wave B run refresh."

## Flag e - negative late-period g_net
- Characterization: g_net is an uncensored signed share (:1459-1486); its negativity coincides
  with the radius<=1.76 instability episode and is visible in existing aggregate_cp_metrics and
  bootstrap CSVs (aggregate_cp_metrics.csv:63-70, :133). Offline decomposition is available
  without re-running estimation.
- Evidence: :1459-1486; aggregate_cp_metrics.csv:63-70, :133.
- Residual scope: optional offline decomposition in Wave B.
- Wording proposal: "g_net is reported as an uncensored signed share; negative late-period
  values coincide with the declared instability episode and are not clipped."

## Provenance
Drafted 2026-08-26 under author Wave A authorization; orchestrator-executed after two child
lanes failed identically before write (spawn ENOENT); evidence compiled from the read-only
reconnaissance report tmp/empirical_remediation_feasibility_20260826.md and self-verified
line reads of scripts/run_cp_empirical_pipeline.py. Hash executed by orchestrator (disclosed).
