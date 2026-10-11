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
- Final deliverable (written later, in Latvian, 2-3 pages): problem statement;
  algorithm description with subsections domain / evaluation / move / algorithm;
  testing description; repo link. Keep code and results easy to describe.

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
1. classic/ — published OP benchmarks, v = 0 (special case of our problem):
   - Tsiligirides sets 1, 2, 3 (~21-33 nodes) and Chao sets (64 and 66 nodes).
   - Each set has many Tmax values: use ~3-4 per set (small/medium/large budget).
   - Optional: a few larger TSPLIB-based OP instances (Fischetti,
     Salazar-Gonzalez, Toth 1998) with published optima.
   - Reference values: take ALL from one reliable source, store in
     instances/classic/references.csv with columns: instance, Tmax, reference,
     type (optimal/best-known), source. Verify file format and distance
     convention from the source. NEVER invent reference values — if a value
     cannot be confirmed, ask me.
2. visit_small/ — generated, ~10-16 nodes, visit times 5-60, fixed seeds.
   Reference = exact DP optimum.
3. visit_large/ — generated, 50-100+ nodes (e.g. Chao/TSPLIB coordinates +
   generated visit times), fixed seeds, Tmax chosen so the problem is
   non-trivial. Reference = best result over many long SA runs (best known);
   label it as such.

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
Plan order: loader -> evaluation -> SA -> exact DP + instance generator -> experiments.
After each step: run `python -m unittest` (stdlib unittest, no pytest), then
commit AND push to GitHub (origin = github.com/kikofers/ttdp-simulated-annealing).
Ask before big design changes.

## Implementation decisions (already made — keep consistent)
Instances (src/instance.py)
- File format = standard OP format (`Tmax P`, then `x y S` per point; first point
  start, second point end) with an OPTIONAL 4th column v (visit time, default 0).
  Same format for classic, generated and Riga instances; save_instance writes it.
- Internal order: node 0 = start, attractions 1..n-2, node n-1 = end (the loader
  moves the file's second point to the end).
- Instance.cost = t' (modified cost) is built once in the loader; all other code
  treats the problem as a plain OP on t' and never handles visit times itself.
- Classic files come from https://www.mech.kuleuven.be/en/cib/op (documented in
  instances/classic/SOURCE.md). TsiligiridesOP1 is the ORIGINAL set 1 (point
  (4.9, 18.9)), not the corrected "set 4" used by some papers.
- Classic references (APPROVED by the user): instances/classic/references.csv, all
  89 values from ONE source, Szwarc & Boryczka (2022), PLoS ONE 17(2): e0264584,
  column "Best" of Tables 1, 2, 3, 5, 6 (pp. 12-14); type = best-known for all.
- Distance convention verified: unrounded Euclidean (our code) reaches all 89
  references and never exceeds one; nint/floor/ceil contradict them
  (results/distance_convention/, experiments/check_distance_convention.py).
- Classic instances used in experiments (APPROVED): instances/classic/selection.csv,
  17 instances: Tsiligirides 1: Tmax 20/40/60, set 2: 15/25/35, set 3: 20/40/70,
  Chao 64: 20/40/55/70, Chao 66: 30/60/90/110 (~25/50/75 % of total score + one
  instance per Chao set that published heuristics found hard).

Evaluation (src/evaluation.py)
- Objective f = score - LENGTH_WEIGHT * length, LENGTH_WEIGHT = 1e-6 (valid for
  integer scores and route lengths < 1e6). FEASIBILITY_TOL = 1e-9 vs Tmax.
- Delta functions only compute the length change; they never modify the route.
- Hot loops pass cost as a list of lists (inst.cost.tolist()): ~4.5x faster than
  indexing numpy element by element.

SA (src/sa.py)
- Acceptance is lexicographic, matching f: delta_f >= 0 -> accept; score loss ->
  accept with exp(delta_score / T); equal score but longer -> reject. (Plain
  Metropolis on f would accept nearly all lengthening equal-score moves.)
- Replace move keeps the same position (O(1) delta).
- T0 / T_end: the mean sampled score loss is accepted with probability
  initial_accept = 0.5 / final_accept = 0.001; alpha = (T_end/T0)^(1/iterations).
- Default 100k iterations (~0.8 s on 64-66 nodes). Larger budgets clearly help
  (1M: ~8 s); the experiment budget is still to be decided in step 5. On the
  classic sets 200k iterations reach 80/89 references; the hardest Chao instances
  need 1M-3M (Chao 66 Tmax 100 reached by 2 of 4 seeds at 3M).
- CLI: python -m src.sa <instance> --iterations N --seed S

Exact DP (src/exact_dp.py)
- Pure Python bitmask DP with pruning of states that cannot reach the end within
  Tmax (valid because t' satisfies the triangle inequality). Limit 18 attractions;
  ~1 s at 16, ~5 s at 18 attractions. Verified against brute force.
- CLI: python -m src.exact_dp <files> --csv out.csv

Generated instances (src/generate.py, run: python -m src.generate)
- Units = minutes; visit times integer 5-60; Tmax = round(ratio * T_all), T_all =
  nearest-neighbour route through all attractions under t'.
- visit_small: n in {10,...,20} (step 2), ratio {0.3, 0.5}, 100x100 area, scores 1-100,
  round trip from a hotel, seed = n. References: instances/visit_small/references.csv.
- visit_large: Chao 64/66 coordinates x10 (so travel ~ visit time scale) and
  original scores, ratio {0.3, 0.6}, seed = 64/66. Reference = best of long SA runs
  (step 5).
- Each folder has manifest.csv; tests check committed files == regenerated ones.

## Error handling conventions (keep for new modules)
- Invalid instance data -> InstanceError (subclass of ValueError) with file name and
  line number; validate_instance() checks finiteness, non-negative S and v, v = 0 at
  start/end, matrix shapes, and that the direct start -> end trip fits in Tmax.
- Invalid parameters -> ValueError naming the parameter and the allowed range.
  Solvers call validate_instance() and check their parameters before solving.
- Never fail silently: delta functions range-check positions (Python would
  otherwise accept negative indices and return a wrong delta).
- Final safety net instead of assert (asserts vanish under python -O): a solver
  re-evaluates its result from scratch and raises RuntimeError if it is infeasible
  or its tracked score/length disagree.
- Incrementally tracked values (route length) are resynced periodically.
- CLIs print `error: <message>` and exit 1 instead of a traceback.
- Every new failure mode gets a test (tests/test_errors.py).
