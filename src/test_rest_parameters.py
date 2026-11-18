import unittest

from evaluator import evaluate_source
from parser import parse
from tokenizer import tokenize

PRELUDE = '''
    function count(...items) { return length(items) };
    function pair(first, ...rest) { return [first, rest] };
'''


class RestParameterTests(unittest.TestCase):
    def test_collects_extra_arguments(self):
        cases = [
            ('count()', 0),
            ('pair(1)', [1, []]),
            ('count(1, "a", [2])', 3),
            ('pair(1, 2, 3, 4)', [1, [2, 3, 4]]),
        ]
        for call, expected in cases:
            with self.subTest(call=call):
                _, env = evaluate_source(PRELUDE + 'answer=' + call)
                self.assertEqual(env['answer'], expected)

    def test_too_few_fixed_arguments(self):
        with self.assertRaisesRegex(TypeError, r'^Function expects at least 1 argument\(s\), got 0$'):
            evaluate_source(PRELUDE + 'pair()')

    def test_invalid_parameter_placement(self):
        for source in ('function f(...a, b) { }', 'function f(...a, ...b) { }',
                       'function f(a ...b) { }', 'function f(...) { }'):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(tokenize(source))


if __name__ == '__main__':
    unittest.main()
