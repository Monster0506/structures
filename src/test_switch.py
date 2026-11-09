import unittest

import evaluator

PRELUDE = ('calls = 0; r = "none"; '
           'function next() { set calls = calls + 1; return calls }; ')
CASES = ('case 1: { r = "one" } case "1": { r = "string one" } '
         'case true: { r = "true" } ')


class SwitchTests(unittest.TestCase):
    def run_source(self, source):
        return evaluator.evaluate_source(PRELUDE + source, {})

    def test_switch(self):
        cases = [
            ('number match', 'switch (1.0) { ' + CASES + '}',
             {'r': 'one'}),
            ('string match', 'switch ("1") { ' + CASES + '}',
             {'r': 'string one'}),
            ('boolean match', 'switch (true) { ' + CASES + '}',
             {'r': 'true'}),
            ('default', 'switch (2) { ' + CASES + 'default: { r = "other" } }',
             {'r': 'other'}),
            ('no match', 'switch (false) { ' + CASES + '}',
             {'r': 'none'}),
            ('side-effecting selector evaluated once',
             'switch (next()) { case 2: { r = "two" } case 1: { r = "one" } '
             'default: { r = "other" } }',
             {'r': 'one', 'calls': 1}),
            ('no fall-through',
             'switch (1) { case 1: { calls = calls + 1 } '
             'case 2: { calls = calls + 10 } default: { calls = calls + 100 } }',
             {'calls': 1}),
            ('break passes to the loop',
             'while (true) { switch (1) { case 1: { break } }; r = "after" }',
             {'r': 'none'}),
            ('continue passes to the loop',
             'while (calls < 2) { set calls = calls + 1; '
             'switch (calls) { case 1: { continue } }; r = "two" }',
             {'r': 'two', 'calls': 2}),
        ]
        for name, source, expected in cases:
            with self.subTest(name):
                result, env = self.run_source(source)
                self.assertEqual(result, (None, None))
                for key, value in expected.items():
                    self.assertEqual(env[key], value)

    def test_duplicate_cases_are_rejected(self):
        for first, second in (('1', '1'), ('1', '1.0'), ('"a"', '"a"'),
                              ('true', 'true')):
            with self.subTest(first + ' and ' + second):
                with self.assertRaises(SyntaxError) as raised:
                    self.run_source('switch (1) { case ' + first + ': { } '
                                    'case ' + second + ': { } }')
                self.assertIn('Duplicate case label', str(raised.exception))


if __name__ == '__main__':
    unittest.main()
