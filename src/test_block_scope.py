import unittest

from evaluator import evaluate_source

PRELUDE = 'total = 10; x = 1; '


class BlockScopeTests(unittest.TestCase):
    def run_source(self, source):
        result, environment = evaluate_source(PRELUDE + source, {})
        return result, environment

    def test_results(self):
        cases = [
            ('if (true) { x = 2 }', {'x': 1}),
            ('if (true) { x = 2; set total = total + x }', {'x': 1, 'total': 12}),
            ('if (false) { } else { x = 2; set total = x }', {'x': 1, 'total': 2}),
            ('if (true) { if (true) { set x = 5 } }', {'x': 5}),
            ('if (true) { x = 2; if (true) { set x = 3 }; set total = x }', {'x': 1, 'total': 3}),
            ('if (true) { x = 2; if (true) { x = 3 }; set total = x }', {'x': 1, 'total': 2}),
            ('i = 0; while (i < 3) { y = i; set i = i + 1 }', {'i': 3}),
            ('i = 0; while (i < 3) { set i = i + 1; set total = total + i }', {'total': 16}),
            ('while (true) { x = 9; break }', {'x': 1}),
            ('function f() { if (true) { return 4 } }; total = f()', {'total': 4}),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                _, environment = self.run_source(source)
                for name, value in expected.items():
                    self.assertEqual(environment[name], value)
        for source, name in [('if (true) { y = 2 }', 'y'), ('while (true) { y = 2; break }', 'y'),
                             ('if (true) { if (true) { y = 2 } }', 'y')]:
            with self.subTest(source=source):
                self.assertNotIn(name, self.run_source(source)[1])

    def test_block_reads_enclosing_bindings(self):
        _, environment = self.run_source('if (true) { y = x + total }; z = 0; if (true) { set z = x + total }')
        self.assertEqual(environment['z'], 11)

    def test_loop_iterations_get_fresh_environments(self):
        source = (
            'fs = []; i = 0; '
            'while (i < 3) { n = i * 10; set fs = fs + [function() { return n }]; set i = i + 1 }; '
            'a = fs[0](); b = fs[1](); c = fs[2]()'
        )
        _, environment = self.run_source(source)
        self.assertEqual((environment['a'], environment['b'], environment['c']), (0, 10, 20))
        self.assertNotIn('n', environment)

    def test_closure_retains_block_bindings(self):
        source = (
            'get = null; put = null; '
            'if (true) { hidden = 7; set get = function() { return hidden }; '
            'set put = function(v) { set hidden = v } }; '
            'a = get(); put(8); b = get()'
        )
        _, environment = self.run_source(source)
        self.assertEqual((environment['a'], environment['b']), (7, 8))
        self.assertNotIn('hidden', environment)

    def test_set_requires_an_existing_binding(self):
        for source in ['if (true) { set missing = 1 }', 'if (true) { y = 1 }; set y = 2',
                       'while (true) { y = 1; break }; set y = 2']:
            with self.subTest(source=source):
                with self.assertRaises(NameError):
                    self.run_source(source)

    def test_statuses_propagate_out_of_blocks(self):
        cases = [
            ('if (true) { if (true) { exit(3) } }', (3, 'exit')),
            ('while (true) { if (true) { exit(4) } }', (4, 'exit')),
            ('while (true) { if (true) { break } }; exit(5)', (5, 'exit')),
            ('i = 0; while (i < 3) { set i = i + 1; if (true) { continue }; exit(6) }', (None, None)),
            ('function f() { while (true) { if (true) { return 7 } } }; exit(f())', (7, 'exit')),
            ('assert false, "no"', (1, 'exit')),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)[0], expected)

    def test_break_and_continue_outside_a_loop_still_fail(self):
        for source in ['if (true) { break }', 'if (true) { continue }']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.run_source(source)


if __name__ == '__main__':
    unittest.main()
