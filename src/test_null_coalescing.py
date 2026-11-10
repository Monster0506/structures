import unittest

from evaluator import evaluate_source

PRELUDE = '''
    n = 0; function tick() { set n = n + 1; return n };
    function quit() { exit(3) };
    nothing = null; zero = 0; blank = ""; no = false; items = [];
'''


class NullCoalescingTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = nothing ?? "untitled"', 'untitled'),
            ('x = "given" ?? "untitled"', 'given'),
            ('x = zero ?? 5', 0),
            ('x = blank ?? "d"', ''),
            ('x = no ?? true', False),
            ('x = items ?? [1]', []),
            ('x = null ?? null', None),
            ('x = nothing ?? nothing ?? 3', 3),
            ('x = nothing ?? 2 ?? 3', 2),
            ('x = 1 ?? 2 ?? 3', 1),
            ('x = (nothing ?? nothing) ?? 4', 4),
            ('x = nothing ?? (nothing ?? 5)', 5),
            ('x = nothing ?? 1 + 2', 3),
            ('x = nothing ?? false or true', True),
            ('x = nothing ?? 1 == 1', True),
            ('x = nothing ?? zero', 0),
            ('x = y = nothing ?? 6', 6),
            ('x = [nothing ?? 7][0]', 7),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_assignment_takes_the_whole_chain(self):
        environment = self.run_source('x = nothing ?? 8; y = 1; y = nothing ?? y + 1')
        self.assertEqual((environment['x'], environment['y']), (8, 2))

    def test_right_side_is_lazy(self):
        cases = [
            ('x = 1 ?? tick()', 1, 0),
            ('x = zero ?? tick()', 0, 0),
            ('x = nothing ?? tick()', 1, 1),
            ('x = nothing ?? tick() ?? tick()', 1, 1),
            ('x = tick() ?? tick()', 1, 1),
            ('x = nothing ?? nothing ?? tick()', 1, 1),
        ]
        for source, expected, calls in cases:
            with self.subTest(source=source):
                environment = self.run_source(source)
                self.assertEqual((environment['x'], environment['n']), (expected, calls))

    def test_failures(self):
        cases = [
            ('missing ?? 1', ValueError),
            ('nothing ?? missing', ValueError),
            ('1 ?? missing', None),
            ('nothing ??', SyntaxError),
            ('?? 1', SyntaxError),
            ('nothing ? 1', SyntaxError),
            ('(nothing ?? 1) = 2', ValueError),
            ('nothing ?? x = 2', ValueError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                if error is None:
                    self.run_source(source)
                else:
                    with self.assertRaises(error):
                        self.run_source(source)

    def test_evaluation_status(self):
        for source in ['quit() ?? 1', 'nothing ?? quit()', 'nothing ?? nothing ?? quit()', '(nothing ?? quit()) ?? 1']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))
        result, _ = evaluate_source(PRELUDE + '1 ?? quit()', {})
        self.assertEqual(result, (None, None))


if __name__ == '__main__':
    unittest.main()
