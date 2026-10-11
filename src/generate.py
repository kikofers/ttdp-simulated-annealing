"""Generate the test instances with visit times (fixed seeds, reproducible).

Units are minutes: travel time = Euclidean distance, visit times are integers
drawn uniformly from VISIT_RANGE.

visit_small (reference = exact DP optimum):
    n in SMALL_SIZES nodes; attractions uniform in a 100 x 100 area with
    integer scores 1..100; a round trip from a hotel at a random position
    (start and end have the same coordinates). Seed = n, so the instances
    of one size share the same points and differ only in Tmax.

visit_large (reference = best of many long SA runs, computed in experiments):
    coordinates and scores of the Chao OP sets 64 and 66 (start/end as in the
    original), coordinates scaled by COORD_SCALE so that travel times between
    neighbouring points (~15-20 min) are comparable to visit times; seed = set size.

Tmax = round(ratio * T_all), where T_all is the length (under t') of a
nearest-neighbour route that visits all attractions. A ratio < 1 leaves out
part of the attractions, so the selection problem is non-trivial.

Usage: python -m src.generate  (writes instances/visit_small, instances/visit_large)
"""

import argparse
import csv
import random
import sys
from pathlib import Path

from src.instance import load_instance, make_instance, save_instance

ROOT = Path(__file__).resolve().parent.parent

SMALL_SIZES = (10, 12, 14, 16)
SMALL_RATIOS = (0.3, 0.5)
SMALL_AREA = 100.0
SMALL_SCORE_RANGE = (1, 100)

# name: (file with the original coordinates and scores, seed for visit times)
CHAO_BASES = {
    "chao64": (ROOT / "instances" / "classic" / "ChaoOP64" / "set_64_1_15.txt", 64),
    "chao66": (ROOT / "instances" / "classic" / "ChaoOP66" / "set_66_1_005.txt", 66),
}
LARGE_RATIOS = (0.3, 0.6)
COORD_SCALE = 10.0

VISIT_RANGE = (5, 60)


def nearest_neighbour_length(inst):
    """Length under t' of start -> all attractions (nearest neighbour order) -> end."""
    unvisited = set(range(1, inst.end))
    current, length = inst.start, 0.0
    while unvisited:
        nxt = min(unvisited, key=lambda j: inst.cost[current, j])
        length += inst.cost[current, nxt]
        unvisited.remove(nxt)
        current = nxt
    return length + inst.cost[current, inst.end]


def with_budget(name, ratio, x, y, score, visit):
    """Build the instance with Tmax = round(ratio * nearest-neighbour length of all)."""
    if not 0 < ratio < 1:
        raise ValueError(f"ratio must be in (0, 1), got {ratio!r}")
    unlimited = make_instance(name, float("1e12"), x, y, score, visit)
    tmax = round(ratio * nearest_neighbour_length(unlimited))
    return make_instance(name, tmax, x, y, score, visit)


def random_visits(rng, n):
    """Visit times for nodes 0..n-1 (0 for start and end)."""
    return [0] + [rng.randint(*VISIT_RANGE) for _ in range(n - 2)] + [0]


def small_instance(n, ratio, seed):
    """Random round-trip instance with n nodes (n-2 attractions)."""
    if not isinstance(n, int) or n < 3:
        raise ValueError(f"n must be an integer >= 3, got {n!r}")
    rng = random.Random(seed)
    hotel = (round(rng.uniform(0, SMALL_AREA), 1), round(rng.uniform(0, SMALL_AREA), 1))
    points = [(round(rng.uniform(0, SMALL_AREA), 1), round(rng.uniform(0, SMALL_AREA), 1))
              for _ in range(n - 2)]
    points = [hotel] + points + [hotel]
    score = [0] + [rng.randint(*SMALL_SCORE_RANGE) for _ in range(n - 2)] + [0]
    visit = random_visits(rng, n)
    x, y = zip(*points)
    return with_budget(f"small_n{n:02d}_r{round(ratio * 100):02d}", ratio, x, y, score, visit)


def large_instance(base_name, ratio, seed):
    """Chao coordinates (scaled) and scores with generated visit times."""
    if base_name not in CHAO_BASES:
        raise ValueError(f"unknown base {base_name!r}, choose from {', '.join(CHAO_BASES)}")
    base = load_instance(CHAO_BASES[base_name][0])
    rng = random.Random(seed)
    visit = random_visits(rng, base.n)
    return with_budget(f"large_{base_name}_r{round(ratio * 100):02d}", ratio,
                       base.x * COORD_SCALE, base.y * COORD_SCALE, base.score, visit)


def write_group(instances, folder, seeds):
    """Save instances and a manifest.csv describing how each was generated."""
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for inst, seed in zip(instances, seeds):
        save_instance(inst, folder / f"{inst.name}.txt")
        rows.append({"instance": inst.name, "n": inst.n, "attractions": inst.n - 2,
                     "tmax": f"{inst.tmax:g}", "seed": seed,
                     "total_score": f"{inst.score.sum():g}",
                     "total_visit_time": f"{inst.visit.sum():g}"})
        print(f"  {folder.name}/{inst.name}.txt  n={inst.n}  Tmax={inst.tmax:g}")
    with open(folder / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate visit-time instances.")
    parser.add_argument("--out", default=ROOT / "instances", type=Path,
                        help="root folder (default: the repository's instances/)")
    args = parser.parse_args()
    out = args.out

    try:
        small = [(small_instance(n, r, seed=n), n) for n in SMALL_SIZES for r in SMALL_RATIOS]
        large = [(large_instance(b, r, seed=seed), seed)
                 for b, (_, seed) in CHAO_BASES.items() for r in LARGE_RATIOS]
    except (OSError, ValueError) as e:  # InstanceError is a ValueError
        sys.exit(f"error: {e}")

    write_group([i for i, _ in small], out / "visit_small", [s for _, s in small])
    write_group([i for i, _ in large], out / "visit_large", [s for _, s in large])


if __name__ == "__main__":
    main()
