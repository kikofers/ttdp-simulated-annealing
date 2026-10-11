import random
import unittest
from pathlib import Path

from src.evaluation import route_errors, route_length, route_score
from src.instance import load_instance
from src.sa import _NodePool, greedy_initial, simulated_annealing
from tests.helpers import brute_force_best, random_instance

CLASSIC = Path(__file__).resolve().parent.parent / "instances" / "classic"
SAMPLE_FILES = [
    CLASSIC / "TsiligiridesOP1" / "tsiligirides_problem_1_budget_40.txt",
    CLASSIC / "TsiligiridesOP2" / "tsiligirides_problem_2_budget_25.txt",
    CLASSIC / "ChaoOP66" / "set_66_1_050.txt",
]


class TestGreedy(unittest.TestCase):
    def test_greedy_is_feasible(self):
        instances = [load_instance(f) for f in SAMPLE_FILES]
        instances += [random_instance(30, seed=s, tmax=300) for s in range(5)]
        for inst in instances:
            with self.subTest(inst=inst.name):
                route, length = greedy_initial(inst.cost.tolist(), inst.score.tolist(),
                                               inst.tmax, inst.start, inst.end)
                self.assertEqual(route_errors(inst, route), [])
                self.assertAlmostEqual(length, route_length(inst.cost, route), places=9)


class TestSimulatedAnnealing(unittest.TestCase):
    def test_result_is_feasible_and_consistent(self):
        instances = [load_instance(f) for f in SAMPLE_FILES]
        instances += [random_instance(30, seed=s, tmax=300) for s in range(3)]
        for inst in instances:
            for seed in range(2):
                with self.subTest(inst=inst.name, seed=seed):
                    res = simulated_annealing(inst, iterations=20_000, seed=seed)
                    self.assertEqual(route_errors(inst, res.route), [])
                    self.assertEqual(res.score, route_score(inst.score, res.route))
                    self.assertAlmostEqual(res.length, route_length(inst.cost, res.route), places=6)
                    self.assertGreaterEqual(res.score, res.initial_score)

    def test_same_seed_same_result(self):
        inst = load_instance(SAMPLE_FILES[2])
        a = simulated_annealing(inst, iterations=20_000, seed=42)
        b = simulated_annealing(inst, iterations=20_000, seed=42)
        self.assertEqual(a.route, b.route)
        self.assertEqual(a.score, b.score)

    def test_finds_optimum_on_tiny_instances(self):
        for seed in range(5):
            inst = random_instance(8, seed=seed, tmax=200)
            with self.subTest(seed=seed):
                res = simulated_annealing(inst, iterations=20_000, seed=seed)
                self.assertEqual(res.score, brute_force_best(inst)[0])

    def test_nothing_fits(self):
        inst = random_instance(10, seed=0, tmax=500)
        inst.tmax = inst.cost[inst.start, inst.end] + 1.0  # visit times are >= 5
        res = simulated_annealing(inst, iterations=1_000, seed=0)
        self.assertEqual(res.route, [inst.start, inst.end])
        self.assertEqual(res.score, 0)

    def test_history_best_is_nondecreasing(self):
        inst = load_instance(SAMPLE_FILES[0])
        res = simulated_annealing(inst, iterations=10_000, seed=0, history_every=100)
        self.assertEqual(len(res.history), 100)
        best = [b for _, _, b in res.history]
        self.assertEqual(best, sorted(best))
        self.assertTrue(all(cur <= b for _, cur, b in res.history))


class TestNodePool(unittest.TestCase):
    def test_matches_python_set(self):
        rng = random.Random(0)
        pool, reference = _NodePool(range(10)), set(range(10))
        for _ in range(1000):
            if reference and rng.random() < 0.5:
                node = pool.choice(rng)
                self.assertIn(node, reference)
                pool.remove(node)
                reference.remove(node)
            else:
                node = rng.randrange(100)
                if node not in reference:
                    pool.add(node)
                    reference.add(node)
            self.assertEqual(set(pool.items), reference)
            self.assertEqual(len(pool), len(reference))


if __name__ == "__main__":
    unittest.main()
