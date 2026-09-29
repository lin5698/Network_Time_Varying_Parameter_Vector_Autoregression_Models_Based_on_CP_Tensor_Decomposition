### NYC second-domain portability check

The NYC Taxi readout applies the same topology-indexed operator to time-varying trip-share exposure matrices. It is a second-domain portability check for the same operator readouts, not evidence of broad empirical generality or a mobility-policy mechanism.

Mean aggregate propagation is {{nyc_mean_gnet}} and mean frozen-topology propagation is {{nyc_mean_frozen_gnet}}, giving a mean observed-minus-frozen difference of {{nyc_mean_topology_difference_4}}. Network shares use the absolute explicit-channel estimand, and the values reported here are bootstrap-draw medians; point-path shares are a different quantity. The median network share is {{nyc_early_share_median}} for the early mapped date and {{nyc_late_share_median}} for the late mapped date. The validation had 69 available origins and evaluated 66 origins uniformly across ranks.

These descriptive values carry explicit limitations: the stability-rate label follows the pipeline's current semantics, requested GIRF dates were remapped, three of 69 origins were not evaluated, late-period `g_net` estimates can be negative, and no RNG seed was recorded. Those limitations prevent causal or mechanism interpretations; they do not turn the readout into a favorable policy result.
