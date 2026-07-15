This supplementary note expands the `Data availability` and `Code availability` statements in the main manuscript. The reproducibility materials include estimator and benchmark code, empirical analysis scripts, environment specifications, random-seed conventions and the derived inputs used for the reported figures and tables.

The materials support two computational operations. The first regenerates figures, tables and numerical summaries from redistributable derived panels, time-indexed network matrices, benchmark summaries and bootstrap outputs. The second re-estimates the empirical and benchmark analyses from those derived inputs under the documented settings. Reconstructing the derived panels from original source files is a separate data-acquisition operation and depends on third-party access conditions.

Source access and manuscript use are recorded for each data block.

Quarterly macro indicators. Provider/source: IMF International Financial Statistics and national statistical offices. Access: source files are not redistributed because provider access and reuse terms apply. Manuscript use: RCEP quarterly outcome panel. Available materials: derived quarterly panel and acquisition notes.

Bilateral trade weights. Provider/source: UN Comtrade extracts, with documented BACI, WITS, OEC and Atlas fallback or cross-check sources. Access: raw exports and fallback files are not redistributed. Manuscript use: import-share network matrices and source cross-checks. Available materials: derived network matrices, source-coverage summaries and acquisition notes.

Tariff schedules. Provider/source: official RCEP tariff schedules and bilateral import records. Access: source files remain subject to upstream access terms. Manuscript use: tariff-relief regressor and pair-level descriptive association. Available materials: derived tariff-relief panel and association outputs.

MRIO-derived exposure inputs. Provider/source: annual multi-regional input-output information used to construct value-added trade proxies. Access: licensed or otherwise restricted inputs are not redistributed. Manuscript use: quarterly value-added exposure proxies and robustness inputs. Available materials: derived exposure variables and robustness summaries.

NYC Taxi mobility analysis. Provider/source: the public Manhattan yellow-taxi tensor and the New York City Taxi and Limousine Commission portal. Access: the public source route and version are recorded with the data-acquisition instructions. Manuscript use: aggregate, frozen-topology and impulse-response calculations in a second network domain. Available materials: the derived monthly mobility panel, acquisition notes and operator outputs.

The reported figures and tables use the complete CP and 500-draw bootstrap outputs. Each bootstrap draw holds the derived panel, topology matrices, benchmark topology, lag order, rolling window, selected ridge penalty, selected CP rank and response definitions fixed. It resamples residual blocks, re-estimates the local ridge stage, refits CP and recomputes the response summaries. Hyperparameters are not reselected. Bootstrap CP fits use `n_init=4`, `max_iter=80` and `tol=1e-5`; main fits use 6 initializations, 100 maximum iterations and tolerance 1e-6.

The redistributable code and derived data will be deposited in a DOI-minting repository before publication. The persistent identifier, licence and access terms will be added to the final availability statements.
