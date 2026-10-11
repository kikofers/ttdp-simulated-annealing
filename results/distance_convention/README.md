# Distance convention check for the classic reference values

The reference paper (see `instances/classic/SOURCE.md`) does not state how distances
were computed. We ran our SA on all 89 classic instances under four conventions
(`experiments/check_distance_convention.py`):

| Convention | SA above reference | equal | below | Conclusion |
|---|---|---|---|---|
| nint (round to nearest integer) | 52 | 31 | 6 | not the paper's convention |
| floor | 81 | 7 | 1 | not the paper's convention |
| ceil | 0 | 5 | 84 | not the paper's convention (misses 47 of 49 Tsiligirides values that unrounded distances reach) |
| unrounded Euclidean (our code) | 0 | 89 | 0 | consistent |

A score above a reference is impossible if the reference was computed with that
convention (the reference is the best known value). With unrounded Euclidean
distances every reference is reached and none is exceeded:

- `euclid_200k_3seeds.txt`: all 89 instances, 3 seeds x 200k iterations: 80 equal, 9 below.
- `euclid_1M_5seeds_remaining.txt`: the 9 remaining instances, 5 seeds x 1M: 8 equal.
- `euclid_3M_chao66_100.txt`: the last one (Chao 66, Tmax 100), 4 seeds x 3M: reached by 2 seeds.

For the 9 hardest instances (the only runs that recorded slack = Tmax - length) the
best routes keep at least 0.08 time units of slack, far above the floating point
tolerance of 1e-9.
