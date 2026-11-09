import unittest

import evaluator

PRELUDE = 'n = 3; count = 0; '


class RepeatUntilTests(unittest.TestCase):
    def run_source(self, source):
        return evaluator.evaluate_source(PRELUDE + source, {})

    def test_repeat_until(self):
        cases = [
            ('one execution',
             'repeat { count = count + 1 } until (true)',
             {'count': 1}),
            ('repeated execution',
             'repeat { set n = n - 1; count = count + 1 } until (n == 0)',
             {'n': 0, 'count': 3}),
            ('break',
             'repeat { count = count + 1; if (count == 2) { break } } until (false)',
             {'count': 2}),
            ('continue goes to the condition',
             'repeat { set n = n - 1; if (n == 0) { continue }; '
             'count = count + 1 } until (n <= 0)',
             {'n': 0, 'count': 2}),
            ('return through a function',
             'function f() { repeat { return n } until (false) }; r = f()',
             {'r': 3}),
        ]
        for name, source, expected in cases:
            with self.subTest(name):
                result, env = self.run_source(source)
                self.assertEqual(result, (None, None))
                for key, value in expected.items():
                    self.assertEqual(env[key], value)

    def test_exit_is_not_consumed(self):
        result, env = self.run_source('repeat { exit(n) } until (false)')
        self.assertEqual(result, (3, 'exit'))

    def test_non_boolean_condition_is_a_language_error(self):
        with self.assertRaises(TypeError) as raised:
            self.run_source('repeat { count = 1 } until (n)')
        self.assertEqual(str(raised.exception),
                         'until condition must be a boolean expression')


if __name__ == '__main__':
    unittest.main()
