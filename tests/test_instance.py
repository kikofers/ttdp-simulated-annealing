import random
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.instance import load_instance, make_instance, save_instance
from tests.helpers import random_instance, random_route

ROOT = Path(__file__).resolve().parent.parent
CLASSIC = ROOT / "instances" / "classic"

# Expected number of files and points per classic set (from the KU Leuven archive).
CLASSIC_SETS = {
    "TsiligiridesOP1": (18, 32),
    "TsiligiridesOP2": (11, 21),
    "TsiligiridesOP3": (20, 33),
    "ChaoOP64": (14, 64),
    "ChaoOP66": (26, 66),
}


class TestClassicInstances(unittest.TestCase):
    def test_all_files_load(self):
        for set_name, (n_files, n_points) in CLASSIC_SETS.items():
            files = sorted((CLASSIC / set_name).glob("*.txt"))
            self.assertEqual(len(files), n_files, set_name)
            for f in files:
                with self.subTest(file=f.name):
                    inst = load_instance(f)
                    self.assertEqual(inst.n, n_points)
                    self.assertTrue(np.all(inst.visit == 0))
                    self.assertEqual(inst.score[inst.start], 0)
                    self.assertEqual(inst.score[inst.end], 0)
                    # Tmax in the header equals the budget in the file name.
                    budget = int(re.search(r"_(\d+)$", f.stem).group(1))
                    self.assertEqual(inst.tmax, budget)

    def test_start_and_end_are_reordered(self):
        # File: line 2 = start (10.5, 14.4), line 3 = end (11.2, 14.1), line 4 = first attraction.
        inst = load_instance(CLASSIC / "TsiligiridesOP1" / "tsiligirides_problem_1_budget_05.txt")
        self.assertEqual((inst.x[0], inst.y[0]), (10.5, 14.4))
        self.assertEqual((inst.x[-1], inst.y[-1]), (11.2, 14.1))
        self.assertEqual((inst.x[1], inst.y[1], inst.score[1]), (18.0, 15.9, 10.0))

    def test_without_visit_times_cost_equals_distance(self):
        inst = load_instance(CLASSIC / "ChaoOP64" / "set_64_1_15.txt")
        np.testing.assert_allclose(inst.cost, inst.dist)


class TestCostMatrix(unittest.TestCase):
    def test_matrices_symmetric_with_zero_diagonal(self):
        inst = random_instance(20, seed=1)
        for m in (inst.dist, inst.cost):
            np.testing.assert_allclose(m, m.T)
            np.testing.assert_allclose(np.diag(m), 0)

    def test_route_length_under_modified_cost(self):
        """Length under t' == travel time + visit times, for random routes."""
        inst = random_instance(15, seed=2)
        rng = random.Random(3)
        for _ in range(100):
            route = random_route(inst, rng)
            edges = list(zip(route, route[1:]))
            modified = sum(inst.cost[i, j] for i, j in edges)
            direct = sum(inst.dist[i, j] for i, j in edges) + sum(inst.visit[i] for i in route)
            self.assertAlmostEqual(modified, direct, places=9)


class TestFileFormat(unittest.TestCase):
    def test_save_load_round_trip(self):
        inst = random_instance(12, seed=4)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inst.txt"
            save_instance(inst, path)
            loaded = load_instance(path)
        self.assertEqual(loaded.tmax, inst.tmax)
        for attr in ("x", "y", "score", "visit", "cost"):
            np.testing.assert_allclose(getattr(loaded, attr), getattr(inst, attr), rtol=1e-9)

    def test_rejects_visit_time_at_start(self):
        with self.assertRaises(ValueError):
            make_instance("bad", 10, [0, 1, 2], [0, 0, 0], [0, 5, 0], [3, 1, 0])

    def test_rejects_multiple_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inst.txt"
            path.write_text("10 2\n0 0 0\n1 1 0\n2 2 5\n")
            with self.assertRaises(ValueError):
                load_instance(path)


if __name__ == "__main__":
    unittest.main()
