# Start temperature (initial_accept) sensitivity

T0 is set so that the average sampled score loss is accepted with probability
p0 = initial_accept. Command: `python -m experiments.tune_initial_accept`
(1,000,000 iterations, seeds 0-4, final_accept = 0.001). Cells: average score (best score).

| Instance | p0 = 0.5 avg (best) | p0 = 0.2 avg (best) | p0 = 0.05 avg (best) | p0 = 0.01 avg (best) |
|---|---|---|---|---|
| tsiligirides_problem_1_budget_60 | 225.0 (225) | 225.0 (225) | 224.0 (225) | 224.0 (225) |
| set_64_1_55 | 980.4 (984) | 980.4 (984) | 981.6 (984) | 980.4 (984) |
| set_66_1_110 | 1554.0 (1560) | 1558.0 (1560) | 1558.0 (1560) | 1560.0 (1560) |
| small_n20_r50 | 717.0 (717) | 717.0 (717) | 717.0 (717) | 717.0 (717) |
| large_chao64_r30 | 734.4 (744) | 732.0 (732) | 740.4 (744) | 736.8 (744) |
| large_chao64_r60 | 1140.0 (1140) | 1140.0 (1140) | 1140.0 (1140) | 1140.0 (1140) |
| large_chao66_r30 | 767.0 (775) | 767.0 (775) | 774.0 (775) | 775.0 (775) |
| large_chao66_r60 | 1362.0 (1370) | 1367.0 (1375) | 1372.0 (1375) | 1368.0 (1370) |

Decision: p0 = 0.05 (the new default). It is equal on the classic and small
instances and better on the large ones; 0.01 is not better overall. With only
5 seeds per cell the differences are indicative, not statistically tested.
Note: the visit_large references (10 runs x 10M iterations) were computed before
this change, with p0 = 0.5; they are best-known values regardless of the setting.
