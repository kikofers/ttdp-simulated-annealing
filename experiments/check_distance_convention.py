"""Check which distance convention the classic reference values were computed with.

The reference paper (instances/classic/SOURCE.md) does not state how distances
are computed. We test candidate conventions on the classic instances with SA:

- a convention under which SA finds a score ABOVE a reference cannot be the one
  used for that reference (the reference would not be the best known value);
- under the right convention every reference must be reachable, and never exceeded.

Usage:
    python -m experiments.check_distance_convention CONVENTION [--iterations N] [--seeds K]
        [--only-below FILE]   (re-run only instances listed as 'below' in an earlier output)
CONVENTION: euclid (unrounded, our code), nint (round to nearest integer, TSPLIB),
            floor, ceil.
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

from src.instance import build_cost_matrix, load_instance, validate_instance
from src.sa import simulated_annealing

ROOT = Path(__file__).resolve().parent.parent
CLASSIC = ROOT / "instances" / "classic"

CONVENTIONS = {
    "euclid": lambda d: d,
    "nint": lambda d: np.floor(d + 0.5),   # TSPLIB nint, ties rounded up
    "floor": np.floor,
    "ceil": np.ceil,
}


def with_convention(inst, convention):
    """Return the instance with its distances replaced by the given convention."""
    inst.dist = CONVENTIONS[convention](inst.dist)
    inst.cost = build_cost_matrix(inst.dist, inst.visit)
    validate_instance(inst)
    return inst


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("convention", choices=CONVENTIONS)
    parser.add_argument("--iterations", type=int, default=200_000)
    parser.add_argument("--seeds", type=int, default=2)
    parser.add_argument("--only-below", type=Path,
                        help="output of an earlier run; re-run only its 'below' instances")
    args = parser.parse_args()

    with open(CLASSIC / "references.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.only_below:
        below = {line.split()[0] for line in args.only_below.read_text().splitlines()
                 if line.rstrip().endswith("below")}
        rows = [r for r in rows if r["instance"] in below]

    counts = {"equal": 0, "below": 0, "ABOVE": 0}
    for r in rows:
        inst = with_convention(load_instance(CLASSIC / f"{r['instance']}.txt"), args.convention)
        ref = float(r["reference"])
        results = [simulated_annealing(inst, iterations=args.iterations, seed=s)
                   for s in range(args.seeds)]
        best = max(results, key=lambda res: res.objective)
        status = "ABOVE" if best.score > ref else ("equal" if best.score == ref else "below")
        counts[status] += 1
        print(f"{r['instance']:48} ref={ref:6g} best={best.score:6g} "
              f"slack={inst.tmax - best.length:.6f} "
              f"runs={[res.score for res in results]} {status}", flush=True)
    print(f"SUMMARY {args.convention}: " + " ".join(f"{k}={v}" for k, v in counts.items())
          + f" of {len(rows)}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
