import itertools
import random

import numpy as np

from src.evaluation import objective, route_length, route_score
from src.instance import make_instance


def random_instance(n, seed, tmax=500):
    """Random instance with visit times 5-60 and integer scores 1-9."""
    rng = np.random.default_rng(seed)
    visit = rng.uniform(5, 60, n)
    visit[0] = visit[-1] = 0
    score = rng.integers(1, 10, n)
    score[0] = score[-1] = 0
    return make_instance("random", tmax, rng.uniform(0, 100, n), rng.uniform(0, 100, n), score, visit)


def random_route(inst, rng, min_size=0):
    """Random route start -> random subset of attractions in random order -> end."""
    k = rng.randint(min_size, inst.n - 2)
    return [inst.start] + rng.sample(range(1, inst.end), k) + [inst.end]


def brute_force_best(inst):
    """(score, length) of the best route over every subset in every order; tiny n only."""
    cost = inst.cost.tolist()
    best = (route_score(inst.score, [inst.start, inst.end]), cost[inst.start][inst.end])
    for k in range(1, inst.n - 1):
        for perm in itertools.permutations(range(1, inst.end), k):
            route = [inst.start, *perm, inst.end]
            length = route_length(cost, route)
            if length <= inst.tmax:
                candidate = (route_score(inst.score, route), length)
                if objective(*candidate) > objective(*best):
                    best = candidate
    return best
