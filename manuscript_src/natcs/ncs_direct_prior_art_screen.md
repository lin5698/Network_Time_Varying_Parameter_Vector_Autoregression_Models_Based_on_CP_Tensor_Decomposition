# Direct Prior-Art Screen: Dynamic Network Response Models

Purpose: record a narrow, evidence-limited screen of the closest dynamic spatial/network autoregression candidates for the present manuscript's contribution. This is a positioning record, not manuscript text and not a proof that no equivalent prior method exists.

## Scope Status (2026-07-22)

This record contains sources outside the current author-approved whitelist of Nature, Nature Reviews, Nature disciplinary journals and Nature Communications. It is retained as excluded historical background only. It must not set current NCS positioning, novelty wording, literature tasks or manuscript claims. No additional screening may be added to this record unless the author explicitly authorizes an expanded source corpus.

## Question Screened

For each candidate, the relevant question is whether the paper documents all four elements below:

1. a separated direct/network response representation;
2. temporal smoothing or regularization of that representation;
3. evaluation of one fitted coefficient path after replacing a supplied topology/exposure argument; and
4. an endpoint-availability check before numerical recovery or comparison.

Only a source that directly documents an element can be marked as present. An unavailable full text is not negative evidence.

## Evidence Reviewed

| Candidate | Source status | Directly verified content | What cannot be inferred |
| --- | --- | --- | --- |
| Ahelegbey, Giudici and Hashem, *Network VAR models to measure financial contagion*, North American Journal of Economics and Finance (2021), DOI `10.1016/j.najef.2020.101318` | 17-page author working-paper PDF, DEM Working Paper 178 (2020), downloaded from the University of Pavia site | The paper fits a VAR jointly to market-index and bank-lending variables. Its equations contain coefficient blocks `A(s), B(s), C(s), D(s)`; weighted adjacency graphs are then constructed by summing estimated VAR coefficients. It reports network representations across four non-overlapping crisis subperiods and network centrality/exposure summaries. | The inspected text does not document a supplied exposure matrix substituted into a fixed coefficient path, a frozen-topology finite-horizon response, temporal low-rank smoothing, or an endpoint-availability gate. This does not prove that no later version or related paper has these features. |
| Chudik and Pesaran, *Theory and Practice of GVAR Modeling* (2016), DOI `10.1002/jae.2446` | 55-page Federal Reserve Bank of Dallas working-paper PDF, version dated 2014, inspected against the cited review | The review states that GVAR models use weighted foreign "star variables", can use time-varying trade weights, and conduct scenario/GIRF analysis. It reports that changing trade weights can alter shock transmission and reviews counterfactual macroeconomic scenarios. | The reviewed material does not define a reconstruction endpoint contract, test endpoint availability after temporal smoothing, or document the specific operation of replacing the exposure matrix while holding one reconstructed coefficient path, shocks and horizons fixed. Its scenario/counterfactual discussion means the present manuscript must acknowledge GVAR response-analysis precedent. |
| Lee and Yu, *QML Estimation of Spatial Dynamic Panel Data Models with Time Varying Spatial Weights Matrices* (2012), DOI `10.1080/17421772.2011.647057` | Crossref and Semantic Scholar metadata; publisher full text was inaccessible | Title and metadata confirm a spatial dynamic panel model with time-varying spatial weights. | The available metadata does not establish its response endpoints, treatment of a fixed fitted path under alternative weights, or any availability test. No comparative claim may be made from this record. |

## Closest Verified Difference

The Ahelegbey et al. working paper is the closest inspected network-VAR near neighbour. It demonstrates that joint multichannel VAR/network analysis and coefficient-derived network graphs are established. The present manuscript must not frame separated network channels or shock propagation alone as new.

The present manuscript's narrower, testable distinction is different in kind: it treats an externally supplied exposure topology as an argument of a reconstructed response operator, holds the fitted coefficient path fixed while the supplied topology changes, and tests whether the reconstructed object still defines the needed direct-only and frozen-topology endpoints. The inspected network-VAR paper constructs its reported graphs from estimated coefficient matrices and compares estimated subperiod networks. The inspected GVAR review documents time-varying weights and scenario/GIRF analysis, but not this reconstruction-endpoint test. This is a source-specific distinction, not a field-wide absence claim.

## Manuscript Rule

Do not add language such as "the first", "unlike existing network VARs", "previous models cannot" or "unavailable in GVARs" unless a systematic full-text comparison supports it. The defensible manuscript language is:

> "Whether a dynamic network specification supports topology substitution after reconstruction is specification-dependent. We evaluate this property for the fitted object used here."

This wording serves `novelty / rigour / clarity`: it states the tested contribution without turning an incomplete literature screen into a priority claim.

## Next Most Valuable Modification

No current action is authorized. A broader full-text screen of dynamic spatial, GVAR or network-VAR candidates requires an explicit author instruction to expand the source corpus; until then, this record cannot support a comparative novelty claim.
