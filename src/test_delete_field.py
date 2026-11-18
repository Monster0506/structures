import tempfile
import unittest
from pathlib import Path

from evaluator import evaluate_source

PRELUDE = '''
    record = {"a": 1, "temporary": 2, "b": {"c": 3}}; alias = record;
    items = [1, 2]; text = "abc"; calls = 0;
    function key() { set calls = calls + 1; return "temporary" };
    function quit() { exit(3) };
    function f() { return 1 };
'''


class DeleteFieldTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('delete record["temporary"]', {"a": 1, "b": {"c": 3}}),
            ('delete record.temporary', {"a": 1, "b": {"c": 3}}),
            ('delete record["a"]; delete record["b"]', {"temporary": 2}),
            ('delete record.b.c', {"a": 1, "temporary": 2, "b": {}}),
            ('delete record["b"]["c"]', {"a": 1, "temporary": 2, "b": {}}),
            ('delete alias["temporary"]', {"a": 1, "b": {"c": 3}}),
            ('delete {"x": 1}["x"]', {"a": 1, "temporary": 2, "b": {"c": 3}}),
            ('delete record["a"]; record["a"] = 5', {"temporary": 2, "b": {"c": 3}, "a": 5}),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                environment = self.run_source(source)
                self.assertEqual(environment['record'], expected)
                self.assertIs(environment['alias'], environment['record'])

    def test_key_is_evaluated_once(self):
        environment = self.run_source('delete record[key()]')
        self.assertEqual((environment['calls'], 'temporary' in environment['record']), (1, False))

    def test_failures(self):
        cases = [
            ('delete record["missing"]', KeyError),
            ('delete record["a"]; delete record["a"]', KeyError),
            ('delete record[1]', TypeError),
            ('delete items[0]', TypeError),
            ('delete text[0]', TypeError),
            ('delete f["parameters"]', TypeError),
            ('delete record', ValueError),
            ('delete f()', ValueError),
            ('delete 1', ValueError),
            ('delete', SyntaxError),
            ('delete record["a"] = 1', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)
        self.assertEqual(self.run_source('x = 1; delete record["a"]')['x'], 1)

    def test_evaluation_status(self):
        for source in ['delete quit()["a"]', 'delete record[quit()]']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))

    def test_module_bindings_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'm.v').write_text('value = 1')
            with self.assertRaises(TypeError):
                evaluate_source('m = import("m.v"); delete m["value"]',
                                source_path=Path(directory, 'main.v'))


if __name__ == '__main__':
    unittest.main()
