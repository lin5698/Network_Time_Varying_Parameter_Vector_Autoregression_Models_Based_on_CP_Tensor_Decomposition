# Figure 2 Redesign Contract

Purpose: define a safe redesign path for Main Figure 2 if the journal upload preview makes the current embedded figure hard to scan. This is a working figure contract, not manuscript text.

Boundary: this contract does not add evidence, remove benchmark rows or change numerical claims. It only reorganizes the existing endpoint-availability and benchmark evidence so the visual hierarchy matches the NCS methods argument.

## Core Conclusion

Endpoint preservation, not raw numerical ranking alone, determines which topology-substitution responses can be evaluated after reconstruction.

## Reviewer Job

Figure 2 must let a methods reviewer answer three questions within a quick scan:

1. Which fitted objects define the topology-substitution endpoints?
2. Where does the endpoint-preserving implementation recover the submitted operator endpoints?
3. Which comparisons are bounded stress tests or projection checks rather than native forecasting rankings?

## Current Risk

The current all-in-one figure is logically strong but visually dense. Panel a carries the endpoint gate, panels b-c carry the headline recovery result, and panels d-e carry topology-measurement stress and stability. In the embedded manuscript PDF, panel a and the bounded-stress annotations require close viewing. This creates a first-impression risk: a reviewer may scan the figure as a benchmark ranking before seeing the endpoint-availability logic.

Serves: rigour / clarity / visual communication.

## Redesign Archetype

Use a two-tier quantitative grid with a larger endpoint gate.

- Top tier: endpoint-availability gate, occupying about 35-45% of the figure height.
- Bottom tier: reduced benchmark evidence, occupying about 55-65% of the figure height.
- Keep the same restrained method palette and marker family.
- Keep "Outside target" visible as a structural endpoint label, not as a failed score.

## Recommended Panel Structure

### Panel a. Endpoint Gate

Question: which response endpoints remain defined after reconstruction?

Design:

- Expand the fitted-object x endpoint matrix.
- Use three rows: separated operator path, collapsed total map, no-network map.
- Use three endpoint columns: total response, network component, frozen topology.
- Add a compact callout: "Topology can be supplied at readout only when direct and network blocks remain separate."
- Remove any nonessential legend from this panel; encode available/outside target directly in the cells.

Claim supported: collapsed-map smoothing can keep total responses while losing topology-substitution endpoints.

Tags: novelty / rigour / clarity / visual communication.

### Panel b. Headline Operator Recovery

Question: does the endpoint-preserving implementation recover the operator on the replicated scale rows?

Design:

- Keep effective-operator recovery for N=15 and N=30 as the main scale evidence.
- Show N=50 as a visually separated bounded stress column or move it to a small inset.
- Keep points as medians and intervals as IQRs.
- Use direct labels for CP-network and unrestricted local if space is tight.

Claim supported: effective-operator recovery improves on replicated N=15/N=30 settings.

Tags: rigour / clarity.

### Panel c. Topology-Substitution Endpoint Recovery

Question: does the fitted object recover the topology-specific endpoint after preserving the direct/network split?

Design:

- Choose either network-channel GIRF recovery or frozen-topology recovery as the main bottom-right panel.
- If both are retained, make them small aligned subpanels with identical "outside target" notation.
- Keep collapsed and no-network rows as outside-target marks.
- Move the stability-boundary bar chart to Supplementary unless journal preview confirms the current five-panel layout remains readable.

Claim supported: topology-specific readouts require the preserved endpoint and remain bounded by stability diagnostics.

Tags: rigour / visual communication.

### Optional Panel d. Stability Boundary

Question: where do finite-horizon response errors need stability qualification?

Design:

- Include only if the figure remains readable at final journal width.
- Otherwise move to Supplementary and cite it from the caption.
- If retained, use a compact horizontal bar or dot strip rather than a full axes-heavy bar chart.

Claim supported: response-error interpretation depends on finite-horizon stability.

Tags: rigour / clarity.

## What To Move To Supplementary If Space Is Tight

- Full topology-measurement stress stability bars.
- N=50 graph-feature stress details.
- Projection-boundary explanation longer than one line.
- Raw pair-level error and prediction diagnostics, which are already secondary to the endpoint argument.

## Caption Requirements

The redesigned caption must preserve four definitions:

- Panel a is an endpoint-availability gate before numerical errors are compared.
- Points are medians and intervals are interquartile ranges.
- N=50 is a bounded stress check; headline recovery rests on replicated N=15/N=30 rows.
- Projected graph-feature rows are operator-recovery stress tests under the submitted readout, not native graph-learning forecasting rankings.

## Acceptance Criteria Before Replacing The Current Main Figure

1. At final manuscript width, panel a must be readable without zooming.
2. The phrase "endpoint availability" or "availability gate" must be visible in the figure itself.
3. Outside-target endpoints must be visually distinct from numerical error values.
4. The N=15/N=30 headline evidence must remain traceable to Table 1 and Supplementary Tables 1b-3.
5. No new baseline, replication count, statistical interval or empirical claim may be introduced by the redesign.
6. The standalone PDF/SVG must be included in the main figure source package.

## Next Action

If the journal portal preview rasterizes the current Fig. 2 poorly, redraw Fig. 2 using this contract and keep the current figure as a traceability reference until the redesigned output passes the acceptance criteria above.
