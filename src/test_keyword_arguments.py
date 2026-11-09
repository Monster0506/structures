import unittest

from evaluator import evaluate_source
from parser import parse
from tokenizer import tokenize

PRELUDE = '''
    order = "";
    function note(tag, value) { set order = order + tag; return value };
    function divide(numerator, denominator) { return numerator / denominator };
    function triple(a, b, c) { return [a, b, c] };
'''


class KeywordArgumentTests(unittest.TestCase):
    def test_binding_by_name(self):
        for call, expected in (
            ('divide(denominator: 2, numerator: 10)', 5),
            ('divide(numerator: 10, denominator: 2)', 5),
            ('divide(10, denominator: 2)', 5),
            ('triple(1, c: 3, b: 2)', [1, 2, 3]),
            ('triple(c: 3, a: 1, b: 2)', [1, 2, 3]),
        ):
            with self.subTest(call=call):
                _, env = evaluate_source(PRELUDE + 'result = ' + call)
                self.assertEqual(env['result'], expected)

    def test_arguments_evaluated_in_source_order(self):
        for call, expected_order in (
            ('divide(denominator: note("d", 2), numerator: note("n", 10))', 'dn'),
            ('triple(note("a", 1), c: note("c", 3), b: note("b", 2))', 'acb'),
        ):
            with self.subTest(call=call):
                _, env = evaluate_source(PRELUDE + 'result = ' + call)
                self.assertEqual(env['order'], expected_order)

    def test_binding_errors_after_all_arguments_evaluated(self):
        for call, message in (
            ('divide(note("n", 10), numerator: note("k", 2))', 'Duplicate argument: numerator'),
            ('divide(numerator: note("n", 10), numerator: note("k", 2))', 'Duplicate argument: numerator'),
            ('divide(numerator: note("n", 10), bogus: note("k", 2))', 'Unknown argument name: bogus'),
            ('divide(note("n", 10), note("k", 2), denominator: 3)', 'Duplicate argument: denominator'),
            ('triple(note("n", 1), c: note("k", 3))', 'Missing argument: b'),
        ):
            with self.subTest(call=call):
                env = {}
                with self.assertRaisesRegex(TypeError, message):
                    evaluate_source(PRELUDE + 'result = ' + call, env)
                self.assertEqual(env['order'], 'nk')
                self.assertNotIn('result', env)

    def test_positional_after_keyword_rejected(self):
        for source in ('divide(numerator: 10, 2)', 'f(a: 1, b: 2, 3)'):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(tokenize(source))


if __name__ == '__main__':
    unittest.main()
