import random
import unittest

from src.evaluation import (
    cheapest_insertion,
    insert_delta,
    is_feasible,
    objective,
    remove_delta,
    replace_delta,
    route_errors,
    route_length,
    route_score,
    two_opt_delta,
)
from src.instance import make_instance
from tests.helpers import random_instance, random_route

TRIALS = 500


class TestFullEvaluation(unittest.TestCase):
    def setUp(self):
        # start (0,0) -> A (3,0) -> B (3,4) -> end (0,4), visit times A=1, B=2.
        self.inst = make_instance("square", tmax=15, x=[0, 3, 3, 0], y=[0, 0, 4, 4],
                                  score=[0, 5, 7, 0], visit=[0, 1, 2, 0])

    def test_hand_computed_route(self):
        route = [0, 1, 2, 3]
        # travel 3 + 4 + 3 = 10, visit 1 + 2 = 3
        self.assertAlmostEqual(route_length(self.inst.cost, route), 13)
        self.assertEqual(route_score(self.inst.score, route), 12)
        self.assertTrue(is_feasible(self.inst, route))

    def test_empty_route(self):
        self.assertAlmostEqual(route_length(self.inst.cost, [0, 3]), 4)
        self.assertEqual(route_score(self.inst.score, [0, 3]), 0)

    def test_over_budget(self):
        self.inst.tmax = 12.9
        self.assertFalse(is_feasible(self.inst, [0, 1, 2, 3]))
        self.assertTrue(is_feasible(self.inst, [0, 1, 3]))  # 3 + 1 + 5 = 9

    def test_structural_errors(self):
        for bad in ([0, 1, 2], [1, 0, 3], [0, 1, 1, 3], [0, 3, 1, 3], [0, 0, 3], [0, 5, 3], [3]):
            with self.subTest(route=bad):
                self.assertTrue(route_errors(self.inst, bad))

    def test_objective_prefers_score_then_length(self):
        # One extra score point beats any length difference within Tmax.
        self.assertGreater(objective(11, 10_000), objective(10, 0))
        self.assertGreater(objective(10, 50), objective(10, 51))


class TestDeltaEvaluation(unittest.TestCase):
    """Every O(1) delta must equal full re-evaluation of the modified route."""

    def setUp(self):
        self.inst = random_instance(20, seed=7)
        self.cost = self.inst.cost.tolist()
        self.rng = random.Random(11)

    def assertDeltaMatches(self, old_route, new_route, delta):
        expected = route_length(self.cost, new_route) - route_length(self.cost, old_route)
        self.assertAlmostEqual(delta, expected, places=9)

    def test_insert(self):
        for _ in range(TRIALS):
            route = random_route(self.inst, self.rng)
            unvisited = [i for i in range(1, self.inst.end) if i not in route]
            if not unvisited:
                continue
            node = self.rng.choice(unvisited)
            pos = self.rng.randint(1, len(route) - 1)
            new = route[:pos] + [node] + route[pos:]
            self.assertDeltaMatches(route, new, insert_delta(self.cost, route, pos, node))

    def test_remove(self):
        for _ in range(TRIALS):
            route = random_route(self.inst, self.rng, min_size=1)
            pos = self.rng.randint(1, len(route) - 2)
            new = route[:pos] + route[pos + 1:]
            self.assertDeltaMatches(route, new, remove_delta(self.cost, route, pos))

    def test_replace(self):
        for _ in range(TRIALS):
            route = random_route(self.inst, self.rng, min_size=1)
            unvisited = [i for i in range(1, self.inst.end) if i not in route]
            if not unvisited:
                continue
            node = self.rng.choice(unvisited)
            pos = self.rng.randint(1, len(route) - 2)
            new = route[:pos] + [node] + route[pos + 1:]
            self.assertDeltaMatches(route, new, replace_delta(self.cost, route, pos, node))

    def test_two_opt(self):
        for _ in range(TRIALS):
            route = random_route(self.inst, self.rng, min_size=2)
            i, j = sorted(self.rng.sample(range(1, len(route) - 1), 2))
            new = route[:i] + route[i:j + 1][::-1] + route[j + 1:]
            self.assertDeltaMatches(route, new, two_opt_delta(self.cost, route, i, j))

    def test_cheapest_insertion_is_minimum(self):
        for _ in range(TRIALS):
            route = random_route(self.inst, self.rng)
            unvisited = [i for i in range(1, self.inst.end) if i not in route]
            if not unvisited:
                continue
            node = self.rng.choice(unvisited)
            pos, delta = cheapest_insertion(self.cost, route, node)
            all_deltas = [insert_delta(self.cost, route, p, node) for p in range(1, len(route))]
            self.assertAlmostEqual(delta, min(all_deltas), places=12)
            self.assertAlmostEqual(insert_delta(self.cost, route, pos, node), delta, places=12)

    def test_numpy_and_list_cost_agree(self):
        route = random_route(self.inst, self.rng, min_size=3)
        self.assertAlmostEqual(route_length(self.inst.cost, route), route_length(self.cost, route))
        self.assertAlmostEqual(two_opt_delta(self.inst.cost, route, 1, 3),
                               two_opt_delta(self.cost, route, 1, 3))


if __name__ == "__main__":
    unittest.main()
