import random

import numpy as np

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
