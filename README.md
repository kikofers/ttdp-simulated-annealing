# Tourist Trip Design Problem — Simulated Annealing

University assignment (DatZM014 Practical Combinatorial Optimization). A self-written
simulated annealing (SA) algorithm for the Tourist Trip Design Problem, tested on
classic benchmarks and generated instances with visit times. Python 3, no optimization
libraries (only the standard library, numpy for distance matrices, matplotlib for the plot).

## Problem

Nodes `0..n-1`: node 0 is the start, node `n-1` the end (e.g. a hotel). Every
attraction `i` has a score `S_i` and a visit time `v_i`; travel time `t_ij` is the
Euclidean distance. Find a route start → subset of attractions → end with maximal
total score such that travel time + visit time ≤ `Tmax`.

Modelling trick: with modified costs `t'_ij = t_ij + (v_i + v_j) / 2` every visited
attraction contributes exactly `v_i` (half when entering, half when leaving), so the
route length under `t'` equals travel time + visit time and the problem becomes a
standard Orienteering Problem (`src/instance.py`, `build_cost_matrix`).

## Algorithm (`src/sa.py`)

- **Solution:** ordered route `[start, ..., end]` + set of unvisited attractions; only
  feasible routes are kept (a move exceeding `Tmax` is rejected).
- **Objective:** maximize score, shorter route as tie-break: `f = score − 10⁻⁶ · length`.
- **Initial solution:** greedy insertion by score / added time.
- **Moves** (random each iteration): insert an unvisited node at its cheapest position,
  remove a visited node, replace a visited node by an unvisited one, 2-opt.
  Length changes are evaluated in O(1) (`src/evaluation.py`).
- **Acceptance:** improvements always; a score loss `Δ` with probability `exp(Δ / T)`;
  equal score but longer route never.
- **Cooling:** geometric `T ← α·T`. `T0` / `T_end` accept the average sampled score
  loss with probability 0.05 / 0.001; `α` makes cooling span the fixed iteration budget.
  Random seed parameter.

The exact reference solver `src/exact_dp.py` (bitmask dynamic programming, ≤ 18
attractions) is only used to obtain optima of the small instances.

## Test instances and reference values

| Group | Folder | Instances | Reference |
|---|---|---|---|
| Classic OP benchmarks (v = 0) | `instances/classic/` | Tsiligirides sets 1–3, Chao 64/66 (89 files; 17 used, `selection.csv`) | best-known values from Szwarc & Boryczka (2022), PLoS ONE 17(2): e0264584 — see `SOURCE.md` |
| Small, with visit times | `instances/visit_small/` | 12 generated, 10–20 nodes | exact optimum (DP) |
| Large, with visit times | `instances/visit_large/` | 4, Chao 64/66 coordinates ×10 + generated visit times | best-known: best of 10 SA runs × 10M iterations |

Reference values with their sources are in each folder's `references.csv`. The
distance convention of the classic references was verified
(`results/distance_convention/`).

## How to run

```bash
pip install -r requirements.txt
python -m unittest                               # all tests
python -m src.sa instances/classic/ChaoOP64/set_64_1_55.txt --iterations 1000000 --seed 0
python -m src.exact_dp instances/visit_small/*.txt   # exact optima of small instances
python -m src.generate                           # regenerate visit_small / visit_large
python -m experiments.large_references           # references of visit_large (10 runs x 10M, 8 processes)
python -m experiments.run_all                    # all experiments (17 min, serial) -> results/
python -m experiments.plot_convergence           # results/convergence.png
```

## Results

`results/summary.md` (tables), `results/results.csv` (per instance and budget),
`results/runs.csv` (every run), `results/convergence.png` (convergence plot),
`results/tuning_initial_accept.md` (start temperature choice).

## Repository structure

```text
src/          instance.py, evaluation.py, sa.py, exact_dp.py, generate.py
instances/    classic/, visit_small/, visit_large/
experiments/  run_all.py, large_references.py, plot_convergence.py,
              tune_initial_accept.py, check_distance_convention.py
results/      experiment output
tests/        unit tests (feasibility, delta == full evaluation, DP == brute force, ...)
```
