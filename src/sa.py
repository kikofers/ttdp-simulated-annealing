"""Simulated Annealing for the TTDP (Orienteering Problem on modified costs t').

Solution: ordered route [start, ..., end] plus the set of unvisited attractions.
Only feasible solutions are kept: a move whose new length exceeds Tmax is
rejected before the acceptance test.

Moves (one chosen at random per iteration):
  insert   - random unvisited node at its cheapest position
  remove   - random visited node
  replace  - random visited node swapped for a random unvisited node
             (same position)
  two_opt  - reverse a random segment of the route

Objective: f = score - eps * length (see src/evaluation.py), i.e. score
first, shorter route as a tie-break. Acceptance is lexicographic, matching f:
  - delta_f >= 0 (more score, or equal score and not longer): always accept;
  - delta_score < 0: accept with probability exp(delta_score / T);
  - equal score but longer route: reject.
Plain Metropolis on f would accept almost every equal-score move that makes
the route longer (|delta_f| ~ eps is far below T), turning the route order
into a random walk and wasting the time budget.

Cooling: geometric, T <- alpha * T after every iteration. The initial and
final temperatures are set so that the average sampled score loss is
accepted with probability initial_accept and final_accept respectively;
alpha = (T_end / T0) ** (1 / iterations) makes cooling span the budget.
"""

import argparse
import math
import random
import time
from dataclasses import dataclass, field

from src.evaluation import (
    FEASIBILITY_TOL,
    cheapest_insertion,
    objective,
    remove_delta,
    replace_delta,
    route_errors,
    route_length,
    route_score,
    two_opt_delta,
)
from src.instance import load_instance

MOVES = ("insert", "remove", "replace", "two_opt")


@dataclass
class SAResult:
    route: list
    score: float
    length: float
    initial_score: float
    iterations: int
    runtime: float          # seconds
    t0: float
    alpha: float
    seed: int
    history: list = field(default_factory=list)  # (iteration, current score, best score)

    @property
    def objective(self):
        return objective(self.score, self.length)


def greedy_initial(cost, score, tmax, start, end):
    """Greedy insertion: repeatedly insert the unvisited node with the best
    ratio score / added time (at its cheapest position) while it fits."""
    route = [start, end]
    length = cost[start][end]
    unvisited = set(range(start + 1, end))
    while True:
        best = None  # (ratio, node, pos, delta)
        for node in unvisited:
            pos, delta = cheapest_insertion(cost, route, node)
            if length + delta > tmax + FEASIBILITY_TOL:
                continue
            ratio = score[node] / max(delta, 1e-12)
            if best is None or ratio > best[0]:
                best = (ratio, node, pos, delta)
        if best is None:
            return route, length
        _, node, pos, delta = best
        route.insert(pos, node)
        length += delta
        unvisited.remove(node)


class _NodePool:
    """Set of unvisited nodes with O(1) add, remove and random choice."""

    def __init__(self, nodes):
        self.items = list(nodes)
        self.index = {node: i for i, node in enumerate(self.items)}

    def __len__(self):
        return len(self.items)

    def choice(self, rng):
        return self.items[rng.randrange(len(self.items))]

    def add(self, node):
        self.index[node] = len(self.items)
        self.items.append(node)

    def remove(self, node):
        i = self.index.pop(node)
        last = self.items.pop()
        if last != node:
            self.items[i] = last
            self.index[last] = i


def estimate_mean_loss(route, score, unvisited, rng, samples=200):
    """Average score loss of random remove/replace moves from `route`.
    Only these moves can lower the score, so they determine the temperature."""
    losses = []
    for _ in range(samples):
        if len(route) <= 2:
            break
        old = route[rng.randint(1, len(route) - 2)]
        new_score = score[rng.choice(unvisited)] if unvisited and rng.random() < 0.5 else 0
        loss = score[old] - new_score
        if loss > 0:
            losses.append(loss)
    if losses:
        return sum(losses) / len(losses)
    # Empty route or no worsening move found: fall back to the average score.
    attraction_scores = [s for s in score[1:-1] if s > 0]
    return sum(attraction_scores) / len(attraction_scores) if attraction_scores else 1.0


def simulated_annealing(inst, iterations=100_000, seed=0, initial_accept=0.5,
                        final_accept=0.001, move_weights=(1, 1, 1, 1), history_every=0):
    """Run SA on `inst` and return the best solution found (SAResult).

    history_every > 0 records (iteration, current score, best score) every
    that many iterations, for convergence plots.
    """
    t_begin = time.perf_counter()
    rng = random.Random(seed)
    cost = inst.cost.tolist()   # list indexing is much faster than numpy in a Python loop
    score = inst.score.tolist()
    tmax = inst.tmax + FEASIBILITY_TOL

    route, length = greedy_initial(cost, score, inst.tmax, inst.start, inst.end)
    current_score = route_score(score, route)
    on_route = set(route)
    unvisited = _NodePool(i for i in range(1, inst.end) if i not in on_route)
    initial_score = current_score

    best_route, best_score, best_length = route[:], current_score, length

    mean_loss = estimate_mean_loss(route, score, unvisited.items, rng)
    t0 = -mean_loss / math.log(initial_accept)
    t_end = -mean_loss / math.log(final_accept)
    alpha = (t_end / t0) ** (1.0 / iterations)
    temp = t0

    history = []
    for it in range(iterations):
        move = rng.choices(MOVES, weights=move_weights)[0]
        n_visited = len(route) - 2

        # Each branch proposes a move: d_score, d_len and how to apply it.
        if move == "insert":
            if not unvisited:
                apply = None
            else:
                node = unvisited.choice(rng)
                pos, d_len = cheapest_insertion(cost, route, node)
                d_score = score[node]
                apply = ("insert", pos, node)
        elif move == "remove":
            if n_visited == 0:
                apply = None
            else:
                pos = rng.randint(1, n_visited)
                d_len = remove_delta(cost, route, pos)
                d_score = -score[route[pos]]
                apply = ("remove", pos, None)
        elif move == "replace":
            if n_visited == 0 or not unvisited:
                apply = None
            else:
                pos = rng.randint(1, n_visited)
                node = unvisited.choice(rng)
                d_len = replace_delta(cost, route, pos, node)
                d_score = score[node] - score[route[pos]]
                apply = ("replace", pos, node)
        else:  # two_opt
            if n_visited < 2:
                apply = None
            else:
                i, j = sorted(rng.sample(range(1, n_visited + 1), 2))
                d_len = two_opt_delta(cost, route, i, j)
                d_score = 0
                apply = ("two_opt", i, j)

        if apply is not None and length + d_len <= tmax:
            if objective(d_score, d_len) >= 0:
                accept = True
            elif d_score < 0:
                accept = rng.random() < math.exp(d_score / temp)
            else:
                accept = False

            if accept:
                kind, a, b = apply
                if kind == "insert":
                    route.insert(a, b)
                    unvisited.remove(b)
                elif kind == "remove":
                    unvisited.add(route.pop(a))
                elif kind == "replace":
                    unvisited.add(route[a])
                    unvisited.remove(b)
                    route[a] = b
                else:
                    route[a:b + 1] = route[a:b + 1][::-1]
                length += d_len
                current_score += d_score

                if objective(current_score, length) > objective(best_score, best_length):
                    length = route_length(cost, route)  # resync to avoid float drift
                    best_route, best_score, best_length = route[:], current_score, length

        temp *= alpha
        if history_every and it % history_every == 0:
            history.append((it, current_score, best_score))

    errors = route_errors(inst, best_route)
    assert not errors, errors
    return SAResult(
        route=best_route,
        score=best_score,
        length=best_length,
        initial_score=initial_score,
        iterations=iterations,
        runtime=time.perf_counter() - t_begin,
        t0=t0,
        alpha=alpha,
        seed=seed,
        history=history,
    )


def main():
    parser = argparse.ArgumentParser(description="Run SA on one instance file.")
    parser.add_argument("instance")
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    inst = load_instance(args.instance)
    res = simulated_annealing(inst, iterations=args.iterations, seed=args.seed)
    print(f"instance   {inst.name} (n={inst.n}, Tmax={inst.tmax:g})")
    print(f"score      {res.score:g}  (greedy start {res.initial_score:g})")
    print(f"length     {res.length:.3f}")
    print(f"runtime    {res.runtime:.2f} s")
    print(f"route      {res.route}")


if __name__ == "__main__":
    main()
