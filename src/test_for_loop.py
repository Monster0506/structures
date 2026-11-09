import unittest

from evaluator import evaluate_source
from parser import parse
from tokenizer import tokenize

PRELUDE = 'trace = ""; c = {"i": 0}; '


class ForLoopTests(unittest.TestCase):
    def test_runs(self):
        cases = [
            ('counts and leaves i visible after the loop',
             'for (i = 0; i < 10; i = i + 1) { trace = trace + string(i) };',
             (None, None), {'trace': '0123456789', 'i': 10}),
            ('continue in nested conditional runs the update',
             'for (i = 0; i < 5; i = i + 1) { if (i > 0) { if (i == 2) { continue } }; '
             'trace = trace + string(i) }',
             (None, None), {'trace': '0134', 'i': 5}),
            ('break in nested loop stops only the inner loop and skips its update',
             'for (i = 0; i < 3; i = i + 1) { for (j = 0; j < 3; j = j + 1) { '
             'if (j == 1) { break }; trace = trace + string(i) + string(j) } }',
             (None, None), {'trace': '001020', 'i': 3, 'j': 1}),
            ('return escapes without running the update',
             'function f() { for (c.i = 0; c.i < 5; c.i = c.i + 1) { '
             'if (c.i == 2) { return "out" } } }; r = f()',
             (None, None), {'r': 'out', 'c': {'i': 2}}),
            ('exit escapes without running the update',
             'for (i = 0; i < 5; i = i + 1) { if (i == 2) { exit(7) } }',
             (7, 'exit'), {'i': 2}),
            ('exit from the update propagates',
             'function stop() { exit(3) }; for (i = 0; i < 5; stop()) { trace = trace + string(i) }',
             (3, 'exit'), {'trace': '0', 'i': 0}),
            ('omitted initializer uses the existing variable',
             'i = 3; for (; i < 5; i = i + 1) { trace = trace + string(i) }',
             (None, None), {'trace': '34', 'i': 5}),
            ('omitted condition loops until break',
             'for (i = 0; ; i = i + 1) { if (i == 3) { break }; trace = trace + string(i) }',
             (None, None), {'trace': '012', 'i': 3}),
            ('omitted update lets continue go straight to the condition',
             'for (i = 0; i < 4; ) { i = i + 1; if (i == 2) { continue }; trace = trace + string(i) }',
             (None, None), {'trace': '134', 'i': 4}),
            ('all clauses omitted',
             'i = 0; for (;;) { i = i + 1; if (i == 3) { break } }',
             (None, None), {'i': 3}),
        ]
        for name, source, result, expected in cases:
            with self.subTest(name):
                actual, env = evaluate_source(PRELUDE + source)
                self.assertEqual(actual, result)
                self.assertEqual({k: env[k] for k in expected}, expected)

    def test_header_semicolons_and_block_required(self):
        for source in ('for () { }',
                       'for (;) { }',
                       'for (i = 0; i < 3) { }',
                       'for (;;) print(1)'):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(tokenize(source))


if __name__ == '__main__':
    unittest.main()
