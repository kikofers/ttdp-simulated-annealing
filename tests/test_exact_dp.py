import csv
import unittest
from pathlib import Path

from src.evaluation import route_errors, route_length, route_score
from src.exact_dp import MAX_ATTRACTIONS, solve_exact
from src.instance import InstanceError, load_instance, make_instance
from src.sa import simulated_annealing
from tests.helpers import brute_force_best, random_instance

SMALL = Path(__file__).resolve().parent.parent / "instances" / "visit_small"


class TestExactDP(unittest.TestCase):
    def test_matches_brute_force(self):
        checked = 0
        for seed in range(20):
            for tmax in (150, 250, 400):
                try:
                    inst = random_instance(8, seed=seed, tmax=tmax)
                except InstanceError:
                    continue  # direct start -> end trip longer than Tmax
                with self.subTest(seed=seed, tmax=tmax):
                    res = solve_exact(inst)
                    best_score, best_length = brute_force_best(inst)
                    self.assertEqual(res.score, best_score)
                    self.assertAlmostEqual(res.length, best_length, places=9)
                    checked += 1
        self.assertGreater(checked, 40)

    def test_result_is_feasible_and_consistent(self):
        inst = random_instance(14, seed=3, tmax=400)
        res = solve_exact(inst)
        self.assertEqual(route_errors(inst, res.route), [])
        self.assertEqual(res.score, route_score(inst.score, res.route))
        self.assertAlmostEqual(res.length, route_length(inst.cost, res.route), places=9)

    def test_nothing_fits_gives_empty_route(self):
        inst = random_instance(8, seed=0)
        inst.tmax = inst.cost[inst.start, inst.end] + 1.0  # every visit takes >= 5
        res = solve_exact(inst)
        self.assertEqual(res.route, [inst.start, inst.end])
        self.assertEqual(res.score, 0)

    def test_everything_fits(self):
        inst = random_instance(8, seed=0, tmax=10_000)
        res = solve_exact(inst)
        self.assertEqual(sorted(res.route[1:-1]), list(range(1, inst.end)))

    def test_no_attractions(self):
        inst = make_instance("two", 10, [0, 3], [0, 4], [0, 0], [0, 0])
        res = solve_exact(inst)
        self.assertEqual(res.route, [0, 1])
        self.assertAlmostEqual(res.length, 5)

    def test_too_many_attractions(self):
        inst = random_instance(MAX_ATTRACTIONS + 3, seed=0)
        with self.assertRaisesRegex(ValueError, "at most"):
            solve_exact(inst)

    def test_sa_never_beats_optimum(self):
        for seed in range(3):
            inst = random_instance(12, seed=seed, tmax=300)
            optimum = solve_exact(inst).score
            with self.subTest(seed=seed):
                self.assertLessEqual(simulated_annealing(inst, iterations=5_000, seed=seed).score,
                                     optimum)


class TestSmallReferences(unittest.TestCase):
    def test_reference_csv_matches_dp(self):
        """instances/visit_small/references.csv must be reproducible by the DP."""
        with open(SMALL / "references.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        files = sorted(SMALL.glob("*.txt"))
        self.assertEqual(sorted(r["instance"] for r in rows), [f.stem for f in files])
        for row in rows:
            with self.subTest(instance=row["instance"]):
                res = solve_exact(load_instance(SMALL / f"{row['instance']}.txt"))
                self.assertEqual(float(row["reference"]), res.score)


if __name__ == "__main__":
    unittest.main()
