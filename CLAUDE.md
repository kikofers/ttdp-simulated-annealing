# Project: Tourist Trip Design Problem (Orienteering with visit times) — Simulated Annealing

University assignment. Approved by professor. Do NOT extend the problem (no time windows).

## Hard requirements
- Python 3. The optimization algorithm must be fully self-written.
- FORBIDDEN: any optimization/metaheuristic libraries (OR-Tools, PuLP, scipy.optimize,
  simanneal, pymoo, networkx algorithms, etc.). Allowed: standard library, numpy
  (distance matrices), matplotlib (plots), pandas (results tables).
- Test on several instance sizes; record runtime and solution quality compared to the
  optimal or best-known solution.
- Repository must contain code, test instances, and experiment results.

## Problem
Nodes 0..n-1. Node 0 = start, node n-1 = end (e.g. hotel). Each node i has score S_i
and visit duration v_i (v = 0 for start and end). Travel time t_ij = Euclidean distance.
Find a route start -> subset of nodes -> end maximizing total score such that
sum of travel times + sum of visit durations <= Tmax.

Implementation trick: use modified costs t'_ij = t_ij + (v_i + v_j)/2. Then route
length under t' equals travel time + visit time, and the problem becomes a standard
Orienteering Problem. Document this in the code.

## Algorithm (Simulated Annealing)
- Solution: ordered list of visited nodes (start/end fixed) + set of unvisited nodes.
- Only feasible solutions are kept (moves that exceed Tmax are rejected).
- Objective: maximize score; tie-break by shorter route (e.g. f = score - eps*length).
- Initial solution: greedy insertion by ratio score / added time.
- Moves (chosen randomly each iteration):
  insert unvisited node (cheapest position), remove visited node,
  replace visited node with unvisited one, 2-opt within the route.
- Use O(1) delta evaluation for insert/remove where possible.
- SA: initial temperature estimated from sampled |delta|, geometric cooling
  T <- alpha*T, fixed iteration budget, random seed parameter.

## Exact reference solver (for small instances only)
Bitmask dynamic programming: dp[mask][last] = minimal time to visit mask ending at
last. Optimum = max score over masks where dp[mask][last] + t'(last, end) <= Tmax.
Feasible up to ~15-18 intermediate nodes. This is only for obtaining reference
optima, not the optimization method itself.

## Test instances (three groups)
1. Classic benchmarks with v = 0 (Tsiligirides and Chao sets, standard OP format —
   verify the file format from the source; usually first line Tmax and number of
   paths, then "x y score" lines, first point = start, second = end).
   Compare to published best-known scores. Record each reference value with its
   source in a CSV. NEVER invent reference values — if unsure, ask me.
2. Small generated instances with visit times (~10-16 nodes), fixed seeds.
   Reference = exact DP optimum.
3. Larger instances with visit times (50-100 nodes, based on Chao coordinates +
   generated visit times 5-60, fixed seeds). Choose Tmax so the problem is
   non-trivial. Reference = best result over many long SA runs (best known).
Optional: small hand-made Riga instance (~25 attractions, realistic visit times).

## Experiments
- Each instance: 10 runs with different seeds.
- Record: best / average / worst score, gap % = (ref - score) / ref * 100,
  average runtime.
- Output results/results.csv and a markdown summary table.
- One convergence plot (score vs iteration) for a representative instance.

## Repository structure (suggested)
src/        instance loading, evaluation, SA, exact DP, instance generation
instances/  classic/, visit_small/, visit_large/, (riga/)
experiments/run_all.py
results/
tests/      unit tests: feasibility check, delta evaluation == full evaluation
README.md   how to run, short description

## Working style
Propose a plan first. Implement step by step, run tests after each step,
commit with clear messages. Keep code readable — it will be described in a report.