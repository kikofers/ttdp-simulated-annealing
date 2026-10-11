"""Exact reference solver: bitmask dynamic programming (small instances only).

This is NOT the optimization method of the project; it only provides proven
optima for the small generated instances, so that SA results can be compared
with the true optimum.

Let A = attractions 1..n-2, k = |A|, and identify attraction a with bit a-1.
    dp[mask][j] = minimal cost (under t') of a path that starts at node 0,
                  visits exactly the attractions in `mask` and ends at j in mask.
    dp[{j}][j]  = t'(0, j)
    dp[mask | {m}][m] = min over j of dp[mask][j] + t'(j, m)      (m not in mask)
The optimum is the best mask (highest score, then shortest length) for which
some j has dp[mask][j] + t'(j, end) <= Tmax. The empty route start -> end is
always a candidate (validate_instance guarantees it is feasible).

Pruning: a state with dp[mask][j] + t'(j, end) > Tmax is discarded. This is
safe because t' satisfies the triangle inequality (t is Euclidean and visiting
an extra node only adds v >= 0), so every extension of such a state would
also exceed Tmax.

Time O(2^k * k^2), memory O(2^k * k); k <= MAX_ATTRACTIONS (18).
"""

import argparse
import csv
import sys
import time
from dataclasses import dataclass

from src.evaluation import FEASIBILITY_TOL, objective, route_errors, route_length, route_score
from src.instance import load_instance, validate_instance

MAX_ATTRACTIONS = 18

INF = float("inf")


@dataclass
class ExactResult:
    route: list
    score: float
    length: float
    runtime: float  # seconds
    states: int     # number of feasible (mask, last) states kept

    @property
    def objective(self):
        return objective(self.score, self.length)


def solve_exact(inst):
    """Return the optimal route of `inst` (ExactResult) by bitmask DP."""
    validate_instance(inst)
    k = inst.n - 2
    if k > MAX_ATTRACTIONS:
        raise ValueError(f"{inst.name}: exact DP supports at most {MAX_ATTRACTIONS} attractions, "
                         f"instance has {k} (memory and time grow as 2^k)")

    t_begin = time.perf_counter()
    cost = inst.cost.tolist()
    score = inst.score.tolist()
    start, end = inst.start, inst.end
    limit = inst.tmax + FEASIBILITY_TOL

    # Work with attraction indices 0..k-1 (node = index + 1).
    c = [[cost[a + 1][b + 1] for b in range(k)] for a in range(k)]
    from_start = [cost[start][a + 1] for a in range(k)]
    to_end = [cost[a + 1][end] for a in range(k)]
    s = [score[a + 1] for a in range(k)]

    full = 1 << k
    dp = [None] * full  # dp[mask] = list of k costs, or None if no feasible state
    for j in range(k):
        if from_start[j] + to_end[j] <= limit:
            row = [INF] * k
            row[j] = from_start[j]
            dp[1 << j] = row

    mask_score = [0.0] * full
    best_value = objective(score[start] + score[end], cost[start][end])
    best_state = None  # (mask, last) of the best non-empty route
    states = 0

    for mask in range(1, full):
        low = mask & -mask
        mask_score[mask] = mask_score[mask ^ low] + s[low.bit_length() - 1]
        row = dp[mask]
        if row is None:
            continue
        total_score = mask_score[mask] + score[start] + score[end]
        for j in range(k):
            d = row[j]
            if d == INF:
                continue
            states += 1
            value = objective(total_score, d + to_end[j])
            if value > best_value:
                best_value, best_state = value, (mask, j)
            cj = c[j]
            for m in range(k):
                bit = 1 << m
                if mask & bit:
                    continue
                nd = d + cj[m]
                if nd + to_end[m] > limit:
                    continue  # pruned: cannot reach the end within Tmax
                new = mask | bit
                new_row = dp[new]
                if new_row is None:
                    new_row = dp[new] = [INF] * k
                if nd < new_row[m]:
                    new_row[m] = nd

    route = [start] + _reconstruct(dp, c, from_start, best_state) + [end]

    # Final safety net: the reconstructed route must be feasible and consistent.
    errors = route_errors(inst, route)
    length = route_length(cost, route)
    expected = best_value
    if abs(objective(route_score(score, route), length) - expected) > 1e-6:
        errors.append(f"reconstructed route value differs from DP value {expected}")
    if errors:
        raise RuntimeError(f"internal error in exact DP on {inst.name}: {'; '.join(errors)}")

    return ExactResult(route=route, score=route_score(score, route), length=length,
                       runtime=time.perf_counter() - t_begin, states=states)


def _reconstruct(dp, c, from_start, state):
    """Follow the DP backwards from (mask, last); returns attraction nodes in order."""
    if state is None:
        return []
    mask, j = state
    path = [j]
    while mask != 1 << j:
        prev_mask = mask ^ (1 << j)
        target = dp[mask][j]
        prev_row = dp[prev_mask]
        # The predecessor i reproduces dp[mask][j] exactly (same float sum).
        i = min((i for i in range(len(c)) if prev_row[i] != INF),
                key=lambda i: abs(prev_row[i] + c[i][j] - target))
        path.append(i)
        mask, j = prev_mask, i
    if abs(from_start[j] - dp[mask][j]) > 1e-9:
        raise RuntimeError("internal error in exact DP: inconsistent first step")
    return [a + 1 for a in reversed(path)]


def main():
    parser = argparse.ArgumentParser(description="Solve small instances exactly by bitmask DP.")
    parser.add_argument("instances", nargs="+", help="instance files")
    parser.add_argument("--csv", help="write instance,reference,source,... rows to this CSV")
    args = parser.parse_args()

    rows = []
    try:
        for path in args.instances:
            inst = load_instance(path)
            res = solve_exact(inst)
            print(f"{inst.name:24} n={inst.n:3} optimum={res.score:g} length={res.length:.3f} "
                  f"visited={len(res.route) - 2}/{inst.n - 2} time={res.runtime:.2f}s")
            rows.append({"instance": inst.name, "reference": f"{res.score:g}",
                         "source": "exact optimum, bitmask DP (src/exact_dp.py)",
                         "length": f"{res.length:.6f}", "route": " ".join(map(str, res.route))})
    except (OSError, ValueError) as e:  # InstanceError is a ValueError
        sys.exit(f"error: {e}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
