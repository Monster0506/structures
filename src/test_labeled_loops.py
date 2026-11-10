import unittest

from evaluator import evaluate_source

NESTED = '''
    out = []; i = 0;
    outer: while (i < 3) {
        i = i + 1; j = 0;
        while (j < 3) {
            j = j + 1;
            %s;
            out = out + [[i, j]]
        }
    }
'''


class LabeledLoopTests(unittest.TestCase):
    def run_source(self, source):
        return evaluate_source(source, {})

    def test_results(self):
        cases = [
            ('if (j == 2) { continue outer }', [[1, 1], [2, 1], [3, 1]]),
            ('if (j == 2) { break outer }', [[1, 1]]),
            ('if (i == 2 and j == 2) { break outer }', [[1, 1], [1, 2], [1, 3], [2, 1]]),
            ('if (j == 2) { continue }', [[1, 1], [1, 3], [2, 1], [2, 3], [3, 1], [3, 3]]),
            ('if (j == 2) { break }', [[1, 1], [2, 1], [3, 1]]),
            ('if (j == 4) { continue outer }', [[i, j] for i in (1, 2, 3) for j in (1, 2, 3)]),
        ]
        for jump, expected in cases:
            with self.subTest(jump=jump):
                result, environment = self.run_source(NESTED % jump)
                self.assertEqual(result, (None, None))
                self.assertEqual(environment['out'], expected)

    def test_each_loop_consumes_only_its_own_label(self):
        source = '''
            log = [];
            a: while (true) {
                b: while (true) {
                    c: while (true) { log = log + ["c"]; break a };
                    log = log + ["b"]
                };
                log = log + ["a"]
            };
            log = log + ["end"]
        '''
        self.assertEqual(self.run_source(source)[1]['log'], ['c', 'end'])
        source = '''
            log = []; n = 0;
            a: while (n < 2) {
                n = n + 1;
                b: while (true) {
                    c: while (true) { log = log + ["c"]; break b };
                    log = log + ["b"]
                };
                log = log + ["a"]
            }
        '''
        self.assertEqual(self.run_source(source)[1]['log'], ['c', 'a', 'c', 'a'])

    def test_labeled_continue_reevaluates_the_target_condition(self):
        source = '''
            n = 0; m = 0;
            outer: while (n < 3) {
                n = n + 1;
                while (true) { m = m + 1; continue outer }
            }
        '''
        _, environment = self.run_source(source)
        self.assertEqual((environment['n'], environment['m']), (3, 3))

    def test_label_on_own_loop_and_name_reuse(self):
        cases = [
            ('i = 0; loop: while (i < 5) { i = i + 1; if (i == 2) { break loop } }', 2),
            ('i = 0; loop: while (i < 5) { i = i + 1; if (i < 4) { continue loop } ; break }', 4),
            ('i = 0; i: while (i < 3) { i = i + 1; continue i }', 3),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)[1]['i'], expected)

    def test_inner_label_shadows_outer_label(self):
        source = '''
            log = []; n = 0;
            same: while (n < 2) {
                n = n + 1;
                same: while (true) { log = log + [n]; break same }
            }
        '''
        self.assertEqual(self.run_source(source)[1]['log'], [1, 2])

    def test_unknown_and_cross_function_labels_are_rejected(self):
        cases = [
            'break nowhere',
            'continue nowhere',
            'while (true) { break nowhere }',
            'a: while (true) { break b }',
            'a: while (true) { while (true) { continue b } }',
            'a: while (true) { function f() { break a }; f() }',
            'function f() { break a }; a: while (true) { f() }',
            'function f() { a: while (true) { function g() { continue a }; g() } }; f()',
        ]
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(ValueError) as raised:
                    self.run_source(source)
                self.assertIn('label', str(raised.exception))

    def test_unlabeled_behavior_is_unchanged(self):
        for keyword in ('break', 'continue'):
            with self.subTest(keyword=keyword):
                with self.assertRaisesRegex(ValueError, f"'{keyword}' used outside a loop"):
                    self.run_source(keyword)
                with self.assertRaisesRegex(ValueError, f"'{keyword}' used outside a loop"):
                    self.run_source(f'function f() {{ {keyword} }}; f()')
        self.assertEqual(self.run_source('i = 0; while (true) { i = i + 1; if (i == 3) { break } }')[1]['i'], 3)

    def test_statuses_pass_through_labeled_loops(self):
        self.assertEqual(self.run_source('a: while (true) { exit(3) }')[0], (3, 'exit'))
        self.assertEqual(self.run_source('function f() { a: while (true) { return 5 } }; x = f()')[1]['x'], 5)
        self.assertEqual(self.run_source('a: while (false) { }')[0], (None, None))

    def test_syntax_errors(self):
        for source in ['a: print(1)', 'a: 1', 'a: if (true) { }', ': while (true) { }', '1: while (true) { }',
                       'a: b: while (true) { }', 'while (true) { break a b }', 'while (true) { break 1 }']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    self.run_source(source)


if __name__ == '__main__':
    unittest.main()
