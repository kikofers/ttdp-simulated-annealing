import unittest
from pathlib import Path

import numpy as np

from src.generate import (
    CHAO_BASES,
    COORD_SCALE,
    LARGE_RATIOS,
    SMALL_RATIOS,
    SMALL_SIZES,
    VISIT_RANGE,
    large_instance,
    nearest_neighbour_length,
    small_instance,
)
from src.instance import load_instance

INSTANCES = Path(__file__).resolve().parent.parent / "instances"


def all_generated():
    for n in SMALL_SIZES:
        for r in SMALL_RATIOS:
            yield "visit_small", small_instance(n, r, seed=n)
    for base, (_, seed) in CHAO_BASES.items():
        for r in LARGE_RATIOS:
            yield "visit_large", large_instance(base, r, seed=seed)


class TestGenerator(unittest.TestCase):
    def test_committed_files_match_generator(self):
        """Every instance file in the repository can be regenerated exactly."""
        for folder, inst in all_generated():
            with self.subTest(instance=inst.name):
                saved = load_instance(INSTANCES / folder / f"{inst.name}.txt")
                self.assertEqual(saved.tmax, inst.tmax)
                for attr in ("x", "y", "score", "visit"):
                    np.testing.assert_allclose(getattr(saved, attr), getattr(inst, attr))

    def test_deterministic(self):
        a, b = small_instance(12, 0.5, seed=12), small_instance(12, 0.5, seed=12)
        np.testing.assert_array_equal(a.cost, b.cost)

    def test_properties(self):
        for _, inst in all_generated():
            with self.subTest(instance=inst.name):
                attractions = inst.visit[1:-1]
                self.assertTrue(np.all((attractions >= VISIT_RANGE[0]) & (attractions <= VISIT_RANGE[1])))
                self.assertTrue(np.all(attractions == np.round(attractions)))
                self.assertTrue(np.all(inst.score[1:-1] > 0))
                # Not everything fits: Tmax is a fraction of the visit-all route length.
                self.assertLess(inst.tmax, nearest_neighbour_length(inst))

    def test_small_is_round_trip(self):
        inst = small_instance(10, 0.3, seed=10)
        self.assertEqual((inst.x[0], inst.y[0]), (inst.x[-1], inst.y[-1]))

    def test_large_uses_scaled_chao_data(self):
        path, seed = CHAO_BASES["chao66"]
        base = load_instance(path)
        inst = large_instance("chao66", 0.3, seed=seed)
        np.testing.assert_allclose(inst.x, base.x * COORD_SCALE)
        np.testing.assert_allclose(inst.y, base.y * COORD_SCALE)
        np.testing.assert_array_equal(inst.score, base.score)

    def test_invalid_parameters(self):
        for call in (lambda: small_instance(2, 0.5, seed=0),
                     lambda: small_instance(10, 0.0, seed=0),
                     lambda: small_instance(10, 1.5, seed=0),
                     lambda: large_instance("chao99", 0.5, seed=0)):
            with self.assertRaises(ValueError):
                call()


if __name__ == "__main__":
    unittest.main()
