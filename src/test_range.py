import unittest

from evaluator import evaluate_source
from parser import parse
from tokenizer import tokenize

PRELUDE = 'two = 2; ten = 10; step = -3;'


class RangeTests(unittest.TestCase):
    def test_values(self):
        cases = [
            ('range(2, 10, 2)', [2, 4, 6, 8]),
            ('range(two, ten, two)', [2, 4, 6, 8]),
            ('range(0, 3, 1)', [0, 1, 2]),
            ('range(0, 4, 2)', [0, 2]),
            ('range(0, 5, 2)', [0, 2, 4]),
            ('range(-2, 2, 1)', [-2, -1, 0, 1]),
            ('range(10, 2, -2)', [10, 8, 6, 4]),
            ('range(5, 0, step)', [5, 2]),
            ('range(3, -1, -1)', [3, 2, 1, 0]),
            ('range(0, 1, 5)', [0]),
            ('range(0, 0, 1)', []),
            ('range(0, 0, -1)', []),
            ('range(5, 0, 1)', []),
            ('range(0, 5, -1)', []),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                _, env = evaluate_source(PRELUDE + 'values = ' + source + ';')
                self.assertEqual(env['values'], expected)

    def test_rejected_arguments(self):
        cases = [
            ('range(0, 5, 0)', ValueError, 'range step must not be zero'),
            ('range(0, 1000001, 1)', ValueError,
             'range must not produce more than 1000000 elements'),
            ('range(true, 5, 1)', TypeError, 'range arguments must be integers'),
            ('range(0, false, 1)', TypeError, 'range arguments must be integers'),
            ('range(0, 5, 1.5)', TypeError, 'range arguments must be integers'),
            ('range(0.0, 5, 1)', TypeError, 'range arguments must be integers'),
            ('range("0", 5, 1)', TypeError, 'range arguments must be integers'),
            ('range(0, [5], 1)', TypeError, 'range arguments must be integers'),
            ('range(0, 5, null)', TypeError, 'range arguments must be integers'),
        ]
        for source, error, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(error) as caught:
                    evaluate_source(PRELUDE + source)
                self.assertEqual(str(caught.exception), message)

    def test_large_range_at_limit(self):
        _, env = evaluate_source('values = range(0, 1000000, 1);')
        self.assertEqual(len(env['values']), 1000000)

    def test_requires_three_arguments(self):
        for source in ('range()', 'range(1)', 'range(1, 2)', 'range(1, 2, 3, 4)'):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(tokenize(source))


if __name__ == '__main__':
    unittest.main()
