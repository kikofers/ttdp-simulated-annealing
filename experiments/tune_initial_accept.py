"""Sensitivity of SA to the initial acceptance probability (start temperature).

T0 is set so that the average sampled score loss is accepted with probability
initial_accept. This script compares several values on hard instances with the
same budget and seeds and prints the average / best score per setting.

Usage: python -m experiments.tune_initial_accept [--values 0.5 0.2 0.05 0.01]
                                                 [--iterations 1000000] [--seeds 5] [--workers 6]
"""

import argparse
import statistics
from multiprocessing import Pool
from pathlib import Path

from src.instance import load_instance
from src.sa import simulated_annealing

ROOT = Path(__file__).resolve().parent.parent
INSTANCES = [
    "classic/TsiligiridesOP1/tsiligirides_problem_1_budget_60",
    "classic/ChaoOP64/set_64_1_55",
    "classic/ChaoOP66/set_66_1_110",
    "visit_small/small_n20_r50",
    "visit_large/large_chao64_r30",
    "visit_large/large_chao64_r60",
    "visit_large/large_chao66_r30",
    "visit_large/large_chao66_r60",
]


def run_one(job):
    name, initial_accept, iterations, seed = job
    inst = load_instance(ROOT / "instances" / f"{name}.txt")
    res = simulated_annealing(inst, iterations=iterations, seed=seed, initial_accept=initial_accept)
    return name, initial_accept, res.score


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--values", type=float, nargs="+", default=[0.5, 0.2, 0.05, 0.01])
    parser.add_argument("--iterations", type=int, default=1_000_000)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    jobs = [(n, v, args.iterations, s) for n in INSTANCES for v in args.values for s in range(args.seeds)]
    with Pool(args.workers) as pool:
        results = pool.map(run_one, jobs)

    header = "| Instance | " + " | ".join(f"p0 = {v:g} avg (best)" for v in args.values) + " |"
    print(f"{args.iterations:,} iterations, seeds 0-{args.seeds - 1}\n")
    print(header)
    print("|---|" + "---|" * len(args.values))
    for name in INSTANCES:
        cells = []
        for v in args.values:
            scores = [s for n, val, s in results if n == name and val == v]
            cells.append(f"{statistics.mean(scores):.1f} ({max(scores):g})")
        print(f"| {name.split('/')[-1]} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
