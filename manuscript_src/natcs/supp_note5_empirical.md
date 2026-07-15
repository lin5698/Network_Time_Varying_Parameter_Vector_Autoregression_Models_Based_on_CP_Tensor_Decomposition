This supplementary note expands `Results > RCEP case study` in the main manuscript and the benchmark panel collected in Supplementary Table 4. The empirical construction uses four data blocks already summarized in the main manuscript: quarterly macro inputs from IMF IFS and national statistical offices, annual MRIO-derived trade inputs converted to quarter-end series by country-year proportional allocation using the available quarterly indicator, official RCEP tariff schedules, and bilateral trade data used to form lagged network matrices. The pair-level tariff-relief regressor is stored as an absolute reduction magnitude multiplied by 100 before entering the panel regressions.

The effective sample size in the baseline pair-level regression is 7560 observations. This follows mechanically from 210 ordered non-self country pairs and 36 post-burn-in dates after the rolling window has been imposed on the differenced quarterly panel. The baseline panel regression uses the bounded pair-level contribution with pair and quarter fixed effects and pair-clustered standard errors; Supplementary Table 4 also reports the untruncated raw-metric sensitivity, the 1st-99th percentile trimmed raw-metric sensitivity, and a two-way clustered variance sensitivity.

All frozen-topology empirical outputs use the same comparator,

$$
W_{pre} = \frac{1}{16}\sum_{t \in \text{2016 Q1--2019 Q4}} W_t,
$$

that is, the average import-share matrix over 2016 Q1-2019 Q4. The regression benchmark, aggregate-series figure and frozen-topology comparison use one unified fixed-window benchmark matrix.
