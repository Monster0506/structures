import unittest

from evaluator import evaluate_source

PRELUDE = '''
    n = 0; function next() { set n = n + 1; return n };
    function quit() { exit(3) };
'''


class ChainedComparisonTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = 1 < 2 < 3', True),
            ('x = 1 < 3 < 2', False),
            ('x = 3 < 2 < 1', False),
            ('x = 1 <= 1 < 2 <= 2', True),
            ('x = 3 > 2 >= 2 > 1', True),
            ('x = 1 < 2 > 1', True),
            ('x = 1 < 5 > 6', False),
            ('x = 1 == 1 == 1', True),
            ('x = 1 == 1 == 2', False),
            ('x = 1 != 2 != 1', True),
            ('x = 1 < 2 == true', False),
            ('x = 1 + 1 < 1 + 2 < 2 * 3', True),
            ('x = "a" < "b" < "c"', True),
            ('x = [1] == [1] == [1]', True),
            ('x = not 1 < 2 < 3', False),
            ('x = 1 < 2 < 3 and 3 > 2 > 1', True),
            ('x = 1 < 2', True),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_operands_are_evaluated_once_and_lazily(self):
        cases = [
            ('x = 0 < next() < 10', True, 1),
            ('x = 0 < next() < next() < 10', True, 2),
            ('x = 5 < next() < next()', False, 1),
            ('x = 5 < 3 < next()', False, 0),
            ('x = 0 < next() < 0 < next() < next()', False, 1),
            ('x = 1 == 2 != next()', False, 0),
        ]
        for source, expected, calls in cases:
            with self.subTest(source=source):
                environment = self.run_source(source)
                self.assertEqual((environment['x'], environment['n']), (expected, calls))

    def test_failures(self):
        cases = [
            ('1 < "a" < 3', TypeError),
            ('1 < 2 < "a"', TypeError),
            ('true < false < true', TypeError),
            ('1 < 2 <', SyntaxError),
            ('1 < < 2', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        for source in ['1 < quit() < 3', '1 < 2 < quit()', 'quit() < 2 < 3']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
