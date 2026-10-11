import unittest

from experiments.run_all import gap, load_tasks, run_one, summarize


class TestGap(unittest.TestCase):
    def test_values(self):
        self.assertEqual(gap(200, 200), 0)
        self.assertAlmostEqual(gap(200, 190), 5.0)
        self.assertAlmostEqual(gap(200, 210), -5.0)  # score above the reference

    def test_rejects_non_positive_reference(self):
        with self.assertRaises(ValueError):
            gap(0, 10)


class TestExperimentSetup(unittest.TestCase):
    def test_all_instances_have_references(self):
        tasks = load_tasks()
        groups = [t["group"] for t in tasks]
        self.assertEqual(groups.count("classic"), 17)
        self.assertEqual(groups.count("visit_small"), 12)
        self.assertEqual(groups.count("visit_large"), 4)
        for t in tasks:
            with self.subTest(instance=t["instance"]):
                self.assertTrue(t["path"].exists())
                self.assertGreater(t["reference"], 0)
                self.assertIn(t["reference_type"], ("optimal", "best-known"))
        small_types = {t["reference_type"] for t in tasks if t["group"] == "visit_small"}
        self.assertEqual(small_types, {"optimal"})

    def test_summary_of_runs(self):
        task = next(t for t in load_tasks() if t["group"] == "visit_small")
        runs = [run_one((task, 2_000, seed)) for seed in range(3)]
        (row,) = summarize(runs, {task["instance"]: 0.5})
        scores = [r["score"] for r in runs]
        self.assertEqual(row["runs"], 3)
        self.assertEqual(float(row["best"]), max(scores))
        self.assertEqual(float(row["worst"]), min(scores))
        self.assertAlmostEqual(float(row["gap_best_pct"]), gap(task["reference"], max(scores)), places=2)
        self.assertEqual(row["hits"], sum(s >= task["reference"] for s in scores))
        self.assertEqual(row["exact_dp_runtime_s"], "0.500")


if __name__ == "__main__":
    unittest.main()
