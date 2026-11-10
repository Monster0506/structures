import unittest

from evaluator import evaluate_source

PRELUDE = """
calls = 0;
function nextIndex() { set calls = calls + 1; return calls - 1 };
function stop() { exit(3) };
items = [10, 20];
"""


def run(source, environment=None):
    (value, status), environment = evaluate_source(PRELUDE + source, environment)
    return value, status, environment


class CompoundAssignmentTests(unittest.TestCase):
    def test_side_effecting_index_runs_once(self):
        _, _, env = run("items[nextIndex()] += 1; items[nextIndex()] *= 3;")
        self.assertEqual(env["items"], [11, 60])
        self.assertEqual(env["calls"], 2)

    def test_chained_fields(self):
        _, _, env = run('o = { "a": { "b": [1, 2] } }; o.a.b[nextIndex()] -= 5; o.a["b"][1] /= 2;')
        self.assertEqual(env["o"], {"a": {"b": [-4, 1.0]}})
        self.assertEqual(env["calls"], 1)

    def test_invalid_targets_are_rejected_before_the_rhs(self):
        for source, error in [("1 += nextIndex();", ValueError),
                              ("nextIndex() += nextIndex();", ValueError),
                              ('s = "ab"; s[0] += nextIndex();', TypeError),
                              ("items[5] += nextIndex();", IndexError),
                              ("missing += nextIndex();", NameError)]:
            with self.subTest(source=source):
                env = {}
                with self.assertRaises(error):
                    run(source, env)
                self.assertEqual(env["calls"], 0)

    def test_failed_rhs_leaves_target_unchanged(self):
        value, status, env = run("items[nextIndex()] += stop();")
        self.assertEqual((value, status), (3, "exit"))
        self.assertEqual((env["items"], env["calls"]), ([10, 20], 1))

        env = {}
        with self.assertRaises(TypeError):
            run('items[nextIndex()] += "text";', env)
        self.assertEqual((env["items"], env["calls"]), ([10, 20], 1))


if __name__ == "__main__":
    unittest.main()
