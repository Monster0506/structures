import unittest

from evaluator import evaluate_source

PRELUDE = '''
    calls=0;
    function makePair() { set calls=calls+1; return [1, 2] };
    first=0; second=0;
'''


class DestructuringTests(unittest.TestCase):
    def test_flat_pattern_binds_in_order(self):
        cases = [
            ('result = [first, second] = makePair()', [1, 2, 1, [1, 2]]),
            ('first = 1; result = [first, second] = [second, first]', [0, 1, 0, [0, 1]]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                _, env = evaluate_source(PRELUDE + source)
                self.assertEqual([env['first'], env['second'], env['calls'], env['result']], expected)

    def test_rejected_without_partial_writes(self):
        cases = [
            ('[first] = makePair()', ValueError, 1),
            ('[first, second, third] = makePair()', ValueError, 1),
            ('[first, second] = 12', TypeError, 0),
            ('[first, [second, third]] = [1, [2, 3]]', ValueError, 0),
            ('[first, second[0]] = makePair()', ValueError, 0),
            ('[first, first] = makePair()', ValueError, 0),
        ]
        for source, error, calls in cases:
            with self.subTest(source=source):
                env = {}
                with self.assertRaises(error):
                    evaluate_source(PRELUDE + source, env)
                self.assertEqual([env['first'], env['second'], env['calls']], [0, 0, calls])
                self.assertNotIn('third', env)


if __name__ == '__main__':
    unittest.main()
