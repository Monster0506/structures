import tempfile
import unittest
from pathlib import Path

from evaluator import evaluate_source

PRELUDE = 'const limit = 10; const items = [1, 2]; plain = 1; '


class ConstBindingTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = limit', 10),
            ('x = limit + 1', 11),
            ('const y = limit * 2; x = y', 20),
            ('const x = null', None),
            ('function f() { limit = 5; return limit }; x = f()', 5),
            ('function f(limit) { return limit }; x = f(3)', 3),
            ('function f() { const limit = 7; return limit }; x = f() + limit', 17),
            ('function f() { return limit }; x = f()', 10),
            ('items[0] = 9; x = items', [9, 2]),
            ('plain = 2; set plain = plain + 1; x = plain', 3),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_shadowing_leaves_the_constant_alone(self):
        environment = self.run_source('function f() { limit = 5 }; f(); x = limit')
        self.assertEqual(environment['x'], 10)

    def test_rebinding_is_rejected(self):
        cases = [
            'limit = 5',
            'set limit = 5',
            'limit = limit + 1',
            'x = limit = 1',
            'const limit = 5',
            'const plain = 5',
            'function f() { set limit = 5 }; f()',
            'function f() { const k = 1; function g() { set k = 2 }; g() }; f()',
            'function f() { const k = 1; const k = 2 }; f()',
        ]
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(NameError):
                    self.run_source(source)

    def test_constants_are_not_fields(self):
        environment = self.run_source('record = {"$CONST": 1}; record["$CONST"] = 2; x = record["$CONST"]')
        self.assertEqual((environment['x'], environment['record']), (2, {'$CONST': 2}))

    def test_syntax_errors(self):
        for source in ['const', 'const 1 = 2', 'const x', 'const x =', 'const x == 1']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    self.run_source(source)

    def test_evaluation_status(self):
        result, _ = evaluate_source('function quit() { exit(3) }; const k = quit(); k = 1', {})
        self.assertEqual(result, (3, 'exit'))

    def test_module_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'm.v').write_text('const pi = 3; value = 1')
            source_path = Path(directory, 'main.v')
            _, environment = evaluate_source(
                'm = import("m.v"); a = m.pi; m.value = 2; b = m.value', {}, source_path)
            self.assertEqual((environment['a'], environment['b'], set(environment['m'])),
                             (3, 2, {'pi', 'value'}))
            for source in ['m = import("m.v"); m.pi = 4', 'm = import("m.v"); m["pi"] = 4']:
                with self.subTest(source=source):
                    with self.assertRaises(NameError):
                        evaluate_source(source, {}, source_path)


if __name__ == '__main__':
    unittest.main()
