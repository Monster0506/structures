import tempfile
import unittest
from pathlib import Path

from evaluator import evaluate_source

PRELUDE = '''
    record = {"b": 1, "a": [2], "c": {"d": 3}}; empty = {}; items = [1];
    function f() { return 1 };
    function quit() { exit(3) };
'''


class KeysValuesTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = keys(record)', ['b', 'a', 'c']),
            ('x = values(record)', [1, [2], {'d': 3}]),
            ('x = keys(empty)', []),
            ('x = values(empty)', []),
            ('x = keys(record["c"])', ['d']),
            ('x = keys({"z": 1, "y": 2})', ['z', 'y']),
            ('record["new"] = 4; x = keys(record)', ['b', 'a', 'c', 'new']),
            ('record["b"] = 9; x = keys(record)', ['b', 'a', 'c']),
            ('x = values(record["c"])', [3]),
            ('x = length(keys(record))', 3),
            ('x = type(keys(record))', 'list'),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_snapshots_and_aliases(self):
        environment = self.run_source(
            'k = keys(record); v = values(record); '
            'record["late"] = 0; k[0] = "changed"; v[0] = 100; '
            'v[1][0] = 7; v[2]["d"] = 8'
        )
        self.assertEqual(list(environment['record']), ['b', 'a', 'c', 'late'])
        self.assertEqual(environment['record']['b'], 1)
        self.assertIs(environment['v'][1], environment['record']['a'])
        self.assertEqual(environment['record']['a'], [7])
        self.assertEqual(environment['record']['c'], {'d': 8})
        self.assertEqual(environment['k'], ['changed', 'a', 'c'])

    def test_failures(self):
        cases = [
            ('keys(items)', TypeError),
            ('values(items)', TypeError),
            ('keys("abc")', TypeError),
            ('values(1)', TypeError),
            ('keys(null)', TypeError),
            ('keys(f)', TypeError),
            ('values(f)', TypeError),
            ('keys()', SyntaxError),
            ('keys record', SyntaxError),
            ('keys(record, record)', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        for source in ['keys(quit())', 'values(quit())']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))

    def test_module_exposes_only_public_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'm.v').write_text('value = 1; function g() { return value }')
            _, environment = evaluate_source(
                'm = import("m.v"); k = keys(m); v = values(m)',
                source_path=Path(directory, 'main.v'))
        self.assertEqual(environment['k'], ['value', 'g'])
        self.assertEqual(len(environment['v']), 2)


if __name__ == '__main__':
    unittest.main()
