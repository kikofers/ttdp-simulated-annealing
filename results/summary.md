# Experiment results

SA with 1,000,000 iterations (main budget), 10 runs per instance (seeds 0-9). Gap % = (reference - score) / reference * 100; 'hits' = runs that reach the reference. Runtime = average wall time of one run.
Machine: AMD64 Family 25 Model 80 Stepping 0, AuthenticAMD, Python 3.14.0, runs executed with 1 worker(s). Total experiment time 17.2 min.

## Classic OP benchmarks (v = 0), reference = best-known from the literature

| Instance | n | Tmax | Reference | Greedy | Best | Avg | Worst | Gap best % | Gap avg % | Gap worst % | Hits | SA time s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TsiligiridesOP1/tsiligirides_problem_1_budget_20 | 32 | 20 | 65 | 35 | 65 | 65.00 | 65 | 0.00 | 0.00 | 0.00 | 10/10 | 2.378 |
| TsiligiridesOP1/tsiligirides_problem_1_budget_40 | 32 | 40 | 155 | 115 | 155 | 155.00 | 155 | 0.00 | 0.00 | 0.00 | 10/10 | 2.607 |
| TsiligiridesOP1/tsiligirides_problem_1_budget_60 | 32 | 60 | 225 | 170 | 225 | 224.00 | 220 | 0.00 | 0.44 | 2.22 | 8/10 | 2.844 |
| TsiligiridesOP2/tsiligirides_problem_2_budget_15 | 21 | 15 | 120 | 110 | 120 | 120.00 | 120 | 0.00 | 0.00 | 0.00 | 10/10 | 2.419 |
| TsiligiridesOP2/tsiligirides_problem_2_budget_25 | 21 | 25 | 230 | 200 | 230 | 230.00 | 230 | 0.00 | 0.00 | 0.00 | 10/10 | 2.628 |
| TsiligiridesOP2/tsiligirides_problem_2_budget_35 | 21 | 35 | 320 | 260 | 320 | 319.00 | 310 | 0.00 | 0.31 | 3.12 | 9/10 | 2.726 |
| TsiligiridesOP3/tsiligirides_problem_3_budget_020 | 33 | 20 | 200 | 180 | 200 | 200.00 | 200 | 0.00 | 0.00 | 0.00 | 10/10 | 2.489 |
| TsiligiridesOP3/tsiligirides_problem_3_budget_040 | 33 | 40 | 430 | 380 | 430 | 430.00 | 430 | 0.00 | 0.00 | 0.00 | 10/10 | 2.683 |
| TsiligiridesOP3/tsiligirides_problem_3_budget_070 | 33 | 70 | 640 | 600 | 640 | 640.00 | 640 | 0.00 | 0.00 | 0.00 | 10/10 | 2.906 |
| ChaoOP64/set_64_1_20 | 64 | 20 | 294 | 168 | 294 | 294.00 | 294 | 0.00 | 0.00 | 0.00 | 10/10 | 2.552 |
| ChaoOP64/set_64_1_40 | 64 | 40 | 714 | 570 | 714 | 714.00 | 714 | 0.00 | 0.00 | 0.00 | 10/10 | 3.009 |
| ChaoOP64/set_64_1_55 | 64 | 55 | 984 | 840 | 984 | 981.60 | 978 | 0.00 | 0.24 | 0.61 | 6/10 | 3.301 |
| ChaoOP64/set_64_1_70 | 64 | 70 | 1188 | 1104 | 1188 | 1188.00 | 1188 | 0.00 | 0.00 | 0.00 | 10/10 | 3.483 |
| ChaoOP66/set_66_1_030 | 66 | 30 | 400 | 350 | 400 | 400.00 | 400 | 0.00 | 0.00 | 0.00 | 10/10 | 2.678 |
| ChaoOP66/set_66_1_060 | 66 | 60 | 915 | 815 | 915 | 914.00 | 905 | 0.00 | 0.11 | 1.09 | 9/10 | 3.167 |
| ChaoOP66/set_66_1_090 | 66 | 90 | 1340 | 1270 | 1340 | 1339.00 | 1330 | 0.00 | 0.07 | 0.75 | 9/10 | 3.522 |
| ChaoOP66/set_66_1_110 | 66 | 110 | 1560 | 1550 | 1560 | 1559.00 | 1550 | 0.00 | 0.06 | 0.64 | 9/10 | 3.701 |

## Small instances with visit times, reference = exact DP optimum

| Instance | n | Tmax | Reference | Greedy | Best | Avg | Worst | Gap best % | Gap avg % | Gap worst % | Hits | SA time s | DP time s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| small_n10_r30 | 10 | 181 | 193 | 193 | 193 | 193.00 | 193 | 0.00 | 0.00 | 0.00 | 10/10 | 2.527 | 0.000 |
| small_n10_r50 | 10 | 301 | 278 | 278 | 278 | 278.00 | 278 | 0.00 | 0.00 | 0.00 | 10/10 | 2.626 | 0.000 |
| small_n12_r30 | 12 | 195 | 166 | 166 | 166 | 166.00 | 166 | 0.00 | 0.00 | 0.00 | 10/10 | 2.557 | 0.000 |
| small_n12_r50 | 12 | 325 | 286 | 286 | 286 | 286.00 | 286 | 0.00 | 0.00 | 0.00 | 10/10 | 2.561 | 0.002 |
| small_n14_r30 | 14 | 242 | 301 | 267 | 301 | 301.00 | 301 | 0.00 | 0.00 | 0.00 | 10/10 | 2.510 | 0.001 |
| small_n14_r50 | 14 | 403 | 427 | 425 | 427 | 427.00 | 427 | 0.00 | 0.00 | 0.00 | 10/10 | 2.471 | 0.006 |
| small_n16_r30 | 16 | 259 | 294 | 273 | 294 | 294.00 | 294 | 0.00 | 0.00 | 0.00 | 10/10 | 2.508 | 0.004 |
| small_n16_r50 | 16 | 432 | 453 | 453 | 453 | 453.00 | 453 | 0.00 | 0.00 | 0.00 | 10/10 | 2.579 | 0.050 |
| small_n18_r30 | 18 | 286 | 349 | 342 | 349 | 349.00 | 349 | 0.00 | 0.00 | 0.00 | 10/10 | 2.618 | 0.012 |
| small_n18_r50 | 18 | 477 | 542 | 521 | 542 | 542.00 | 542 | 0.00 | 0.00 | 0.00 | 10/10 | 2.656 | 0.183 |
| small_n20_r30 | 20 | 330 | 413 | 409 | 413 | 413.00 | 413 | 0.00 | 0.00 | 0.00 | 10/10 | 2.509 | 0.041 |
| small_n20_r50 | 20 | 549 | 717 | 683 | 717 | 717.00 | 717 | 0.00 | 0.00 | 0.00 | 10/10 | 2.646 | 1.062 |

## Large instances with visit times, reference = best of 10 long SA runs

| Instance | n | Tmax | Reference | Greedy | Best | Avg | Worst | Gap best % | Gap avg % | Gap worst % | Hits | SA time s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| large_chao64_r30 | 64 | 954 | 744 | 726 | 744 | 739.80 | 732 | 0.00 | 0.56 | 1.61 | 5/10 | 3.041 |
| large_chao64_r60 | 64 | 1909 | 1140 | 1140 | 1140 | 1140.00 | 1140 | 0.00 | 0.00 | 0.00 | 10/10 | 3.653 |
| large_chao66_r30 | 66 | 1098 | 775 | 650 | 775 | 771.50 | 760 | 0.00 | 0.45 | 1.94 | 6/10 | 3.005 |
| large_chao66_r60 | 66 | 2196 | 1375 | 1355 | 1375 | 1368.50 | 1365 | 0.00 | 0.47 | 0.73 | 3/10 | 3.513 |

## Budget comparison (averages over the instances of each group)

| Group | Iterations | Avg gap % | Worst gap % | Hits | Avg SA time s |
|---|---|---|---|---|---|
| classic | 100,000 | 1.29 | 19.35 | 109/170 | 0.324 |
| classic | 1,000,000 | 0.07 | 3.12 | 160/170 | 2.888 |
| visit_small | 100,000 | 0.00 | 0.00 | 120/120 | 0.260 |
| visit_small | 1,000,000 | 0.00 | 0.00 | 120/120 | 2.564 |
| visit_large | 100,000 | 1.21 | 3.23 | 13/40 | 0.352 |
| visit_large | 1,000,000 | 0.37 | 1.94 | 24/40 | 3.303 |
