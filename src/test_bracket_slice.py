import unittest

from evaluator import evaluate_source

PRELUDE = 'items = [10, [20], 30, 40]; text = "hello"; empty = []; '


class BracketSliceTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = items[1:3]', [[20], 30]),
            ('x = items[:2]', [10, [20]]),
            ('x = items[2:]', [30, 40]),
            ('x = items[:]', [10, [20], 30, 40]),
            ('x = text[1:4]', 'ell'),
            ('x = text[:3]', 'hel'),
            ('x = text[3:]', 'lo'),
            ('x = items[2:2]', []),
            ('x = text[5:]', ''),
            ('x = empty[:]', []),
            ('x = items[1.0:3.0]', [[20], 30]),
            ('x = items[1:4][1:2]', [30]),
            ('x = items[1:3][0][0]', 20),
            ('x = text[1:4][1:]', 'll'),
            ('x = [[1, 2, 3]][0][1:]', [2, 3]),
            ('x = items[1:3] == slice(items, 1, 3)', True),
            ('x = items[1]', [20]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_shallow_copy(self):
        environment = self.run_source('x = items[1:3]; x[0][0] = 99; x[1] = 0')
        self.assertEqual(environment['items'], [10, [99], 30, 40])
        self.assertEqual(environment['x'], [[99], 0])

    def test_failures(self):
        cases = [
            ('items[3:1]', IndexError),
            ('items[:5]', IndexError),
            ('items[-1:]', IndexError),
            ('text[:9]', IndexError),
            ('items[1.5:]', TypeError),
            ('items["a":]', TypeError),
            ('items[true:]', TypeError),
            ('5[1:2]', TypeError),
            ('items[1:2] = [0]', ValueError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_syntax_errors(self):
        for source in ['items[1:2:3]', 'items[1 2]', 'items[1:', 'items[:', 'items[]']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    self.run_source(source)

    def test_evaluation_status(self):
        for source in ['items[quit():]', 'items[:quit()]', 'quit()[1:2]']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + 'function quit() { exit(3) }; ' + source, {})
                self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
