import unittest

from evaluator import evaluate_source

PRELUDE = '''
    values = [1, 2, 3]; k = 10; x = "outer"; calls = 0; reads = 0;
    function source() { set reads = reads + 1; return values };
    function stopAt2(n) { set calls = calls + 1; if (n == 2) { exit(7) }; return n };
'''


class ListComprehensionTests(unittest.TestCase):
    def test_results_and_scope(self):
        cases = [
            ('r = [n * n for n in values]', {'r': [1, 4, 9]}),
            ('r = [n * n for n in []]', {'r': []}),
            ('r = [n * k for n in values]', {'r': [10, 20, 30]}),
            ('r = [x * x for x in values]', {'r': [1, 4, 9], 'x': 'outer'}),
            ('r = [n for n in source()]', {'r': [1, 2, 3], 'reads': 1}),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result, env = evaluate_source(PRELUDE + source)
                self.assertEqual(result, (None, None))
                self.assertEqual({key: env[key] for key in expected}, expected)
                self.assertNotIn('n', env)

    def test_exit_from_called_expression_propagates(self):
        result, env = evaluate_source(PRELUDE + 'r = [stopAt2(n) for n in values]')
        self.assertEqual(result, (7, 'exit'))
        self.assertEqual(env['calls'], 2)
        self.assertNotIn('r', env)
        self.assertNotIn('n', env)

    def test_invalid_source_types(self):
        for source in ('5', '"abc"', 'true', 'null', '{"a": 1}', 'source'):
            with self.subTest(source=source), self.assertRaisesRegex(
                    TypeError, 'list comprehension source must be a list'):
                evaluate_source(PRELUDE + f'r = [n for n in {source}]')


if __name__ == '__main__':
    unittest.main()
