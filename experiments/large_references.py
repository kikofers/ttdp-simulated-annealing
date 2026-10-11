"""Best-known reference values for instances/visit_large (no exact method is feasible).

Reference = best score over RUNS long SA runs with ITERATIONS iterations each.
The seeds (1000, 1001, ...) are disjoint from the seeds used in run_all.py
(0..9), so the experiments are not compared against their own runs.

Usage: python -m experiments.large_references [--runs 10] [--iterations 10000000] [--workers 8]
Writes instances/visit_large/references.csv.
"""

import argparse
import csv
import sys
from multiprocessing import Pool
from pathlib import Path

from src.instance import load_instance
from src.sa import simulated_annealing

ROOT = Path(__file__).resolve().parent.parent
LARGE = ROOT / "instances" / "visit_large"
SEED_OFFSET = 1000


def run_one(task):
    path, seed, iterations = task
    res = simulated_annealing(load_instance(path), iterations=iterations, seed=seed)
    return path.stem, seed, res.score, res.length, res.route


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=10_000_000)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.runs < 1 or args.workers < 1:
        sys.exit("error: --runs and --workers must be positive")

    files = sorted(LARGE.glob("*.txt"))
    tasks = [(f, SEED_OFFSET + s, args.iterations) for f in files for s in range(args.runs)]
    with Pool(args.workers) as pool:
        results = pool.map(run_one, tasks)

    rows = []
    for f in files:
        mine = [r for r in results if r[0] == f.stem]
        # Best score, shorter route as tie-break (same order as the SA objective).
        name, seed, score, length, route = max(mine, key=lambda r: (r[2], -r[3]))
        scores = sorted((r[2] for r in mine), reverse=True)
        print(f"{name:20} reference={score:g} (seed {seed})  all runs: {scores}")
        rows.append({
            "instance": name, "reference": f"{score:g}", "type": "best-known",
            "source": f"best of {args.runs} SA runs x {args.iterations} iterations "
                      f"(seeds {SEED_OFFSET}-{SEED_OFFSET + args.runs - 1}, "
                      f"experiments/large_references.py); all run scores: "
                      + " ".join(f"{s:g}" for s in scores),
            "length": f"{length:.6f}", "route": " ".join(map(str, route)),
        })
    with open(LARGE / "references.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
