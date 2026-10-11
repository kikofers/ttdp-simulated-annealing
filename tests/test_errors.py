"""Invalid input must fail loudly with a clear message, never silently."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.evaluation import (
    cheapest_insertion,
    insert_delta,
    remove_delta,
    replace_delta,
    route_errors,
    two_opt_delta,
)
from src.instance import InstanceError, load_instance, make_instance, validate_instance
from src.sa import simulated_annealing
from tests.helpers import random_instance

ROOT = Path(__file__).resolve().parent.parent


class TestInstanceFileErrors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "inst.txt"

    def tearDown(self):
        self.tmp.cleanup()

    def assertLoadFails(self, text, *fragments):
        self.path.write_text(text)
        with self.assertRaises(InstanceError) as ctx:
            load_instance(self.path)
        message = str(ctx.exception)
        self.assertIn("inst.txt", message)
        for fragment in fragments:
            self.assertIn(fragment, message)

    def test_empty_file(self):
        self.assertLoadFails("", "empty")
        self.assertLoadFails("\n  \n", "empty")

    def test_too_few_points(self):
        self.assertLoadFails("10 1\n0 0 0\n", "at least a start and an end")

    def test_bad_header(self):
        self.assertLoadFails("10 1 7\n0 0 0\n1 1 0\n", "line 1", "header")
        self.assertLoadFails("ten 1\n0 0 0\n1 1 0\n", "line 1", "Tmax")
        self.assertLoadFails("10 2\n0 0 0\n1 1 0\n", "line 1", "P = 1")

    def test_header_with_float_path_count_is_accepted(self):
        self.path.write_text("10 1.0\n0 0 0\n1 1 0\n2 2 5\n")
        self.assertEqual(load_instance(self.path).n, 3)

    def test_bad_values_report_line_number(self):
        self.assertLoadFails("10 1\n0 0 0\n1 1 0\n2 2 x\n", "line 4", "score")
        self.assertLoadFails("10 1\n0 0 0\n1 1 0\ninf 2 5\n", "line 4", "finite")
        self.assertLoadFails("nan 1\n0 0 0\n1 1 0\n", "line 1", "finite")
        self.assertLoadFails("10 1\n0 0 0\n1 1 0\n2 2 -5\n", "line 4", ">= 0")
        self.assertLoadFails("10 1\n0 0 0\n1 1 0\n2 2 5 -1\n", "line 4", "visit")
        self.assertLoadFails("10 1\n0 0 0\n1 1 0\n2 2\n", "line 4", "x y S [v]")

    def test_line_numbers_skip_blank_lines_correctly(self):
        self.assertLoadFails("10 1\n\n0 0 0\n1 1 0\n\n2 2 x\n", "line 6")

    def test_visit_time_at_start_or_end(self):
        self.assertLoadFails("10 1\n0 0 0 3\n1 1 0\n2 2 5\n", "visit time 0")
        self.assertLoadFails("10 1\n0 0 0\n1 1 0 3\n2 2 5\n", "visit time 0")

    def test_no_feasible_route(self):
        self.assertLoadFails("1 1\n0 0 0\n5 0 0\n2 2 5\n", "no feasible route")

    def test_missing_file_raises_os_error(self):
        with self.assertRaises(FileNotFoundError):
            load_instance(Path(self.tmp.name) / "missing.txt")


class TestInstanceDataErrors(unittest.TestCase):
    def test_make_instance_rejects_bad_arrays(self):
        with self.assertRaisesRegex(InstanceError, "differ in length"):
            make_instance("bad", 10, [0, 1], [0, 1, 2], [0, 0], [0, 0])
        with self.assertRaisesRegex(InstanceError, "numbers"):
            make_instance("bad", 10, [0, "a"], [0, 1], [0, 0], [0, 0])
        with self.assertRaisesRegex(InstanceError, "one-dimensional"):
            make_instance("bad", 10, [[0, 1]], [[0, 1]], [[0, 0]], [[0, 0]])
        with self.assertRaisesRegex(InstanceError, "finite"):
            make_instance("bad", 10, [0, float("nan"), 1], [0, 0, 0], [0, 1, 0], [0, 1, 0])
        with self.assertRaisesRegex(InstanceError, "negative score"):
            make_instance("bad", 10, [0, 1, 2], [0, 0, 0], [0, -1, 0], [0, 1, 0])

    def test_validate_catches_later_modification(self):
        inst = random_instance(10, seed=0)
        inst.tmax = float("inf")
        with self.assertRaisesRegex(InstanceError, "Tmax"):
            validate_instance(inst)
        inst = random_instance(10, seed=0)
        inst.tmax = 0.5 * inst.cost[inst.start, inst.end]
        with self.assertRaisesRegex(InstanceError, "no feasible route"):
            validate_instance(inst)


class TestEvaluationErrors(unittest.TestCase):
    def setUp(self):
        self.inst = random_instance(10, seed=0)
        self.cost = self.inst.cost.tolist()
        self.route = [0, 3, 5, 7, self.inst.end]

    def test_positions_out_of_range(self):
        r = self.route
        for call in (lambda: insert_delta(self.cost, r, 0, 2),
                     lambda: insert_delta(self.cost, r, len(r), 2),
                     lambda: remove_delta(self.cost, r, 0),
                     lambda: remove_delta(self.cost, r, -1),
                     lambda: remove_delta(self.cost, r, len(r) - 1),
                     lambda: replace_delta(self.cost, r, 0, 2),
                     lambda: two_opt_delta(self.cost, r, 0, 2),
                     lambda: two_opt_delta(self.cost, r, 2, 2),
                     lambda: two_opt_delta(self.cost, r, 1, len(r) - 1),
                     lambda: remove_delta(self.cost, [0, self.inst.end], 1)):
            with self.assertRaises(IndexError):
                call()

    def test_cheapest_insertion_needs_start_and_end(self):
        with self.assertRaises(ValueError):
            cheapest_insertion(self.cost, [0], 2)

    def test_route_errors_on_non_integer_nodes(self):
        self.assertTrue(route_errors(self.inst, [0, 2.5, self.inst.end]))
        self.assertTrue(route_errors(self.inst, [0, "2", self.inst.end]))


class TestSAParameterErrors(unittest.TestCase):
    def setUp(self):
        self.inst = random_instance(10, seed=0)

    def test_invalid_parameters(self):
        for kwargs in ({"iterations": 0}, {"iterations": -5}, {"iterations": 10.5},
                       {"initial_accept": 1.0}, {"initial_accept": 0.0},
                       {"final_accept": 0.0}, {"final_accept": 0.9},
                       {"move_weights": (0, 0, 0, 0)}, {"move_weights": (1, 1, 1)},
                       {"move_weights": (1, -1, 1, 1)}, {"move_weights": (1, float("nan"), 1, 1)},
                       {"history_every": -1}):
            with self.subTest(**{k: repr(v) for k, v in kwargs.items()}):
                with self.assertRaises(ValueError):
                    simulated_annealing(self.inst, **kwargs)

    def test_invalid_instance_is_rejected(self):
        self.inst.tmax = 0.5 * self.inst.cost[self.inst.start, self.inst.end]
        with self.assertRaisesRegex(InstanceError, "no feasible route"):
            simulated_annealing(self.inst, iterations=100)

    def test_some_moves_disabled_still_works(self):
        res = simulated_annealing(self.inst, iterations=2_000, move_weights=(1, 1, 0, 0))
        self.assertEqual(route_errors(self.inst, res.route), [])


class TestCommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "src.sa", *args], cwd=ROOT,
                              capture_output=True, text=True)

    def test_missing_file_gives_clean_error(self):
        result = self.run_cli("no_such_file.txt")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stderr.startswith("error:"))
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_iterations_gives_clean_error(self):
        f = ROOT / "instances" / "classic" / "TsiligiridesOP2" / "tsiligirides_problem_2_budget_15.txt"
        result = self.run_cli(str(f), "--iterations", "0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("iterations", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
