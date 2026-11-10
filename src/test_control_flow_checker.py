import contextlib
import io
import unittest

import checker
import evaluator
from parser import parse
from tokenizer import tokenize


def check_source(source):
    checker.check(parse(tokenize(source)))


class ControlFlowCheckerTests(unittest.TestCase):
    def test_accepted_programs(self):
        sources = [
            '',
            'x = 1',
            'while (true) { break }',
            'while (true) { continue }',
            'while (true) { if (true) { break } else { continue } }',
            'while (true) { while (true) { break }; break }',
            'function f() { return 1 }',
            'function f() { return }',
            'function f() { if (true) { return 1 }; return 2 }',
            'function f() { while (true) { return 1 } }',
            'function f() { while (true) { break }; return 1 }',
            'function f() { function g() { return 1 }; return g }',
            'function f() { return function() { return 1 } }',
            'while (true) { function f() { while (true) { break }; return 1 }; break }',
            'while (true) { function f() { return 1 }; continue }',
            'f = function(a, b) { return a + b }',
            'function f(a, b, c) { }',
            'x = function() { while (true) { continue } }',
            'if (true) { function f() { return 1 } }',
            'function f() { while (false) { }; return 1 }; while (false) { break }',
        ]
        for source in sources:
            with self.subTest(source=source):
                check_source(source)

    def test_rejected_programs(self):
        cases = [
            ('break', "'break' used outside a loop"),
            ('continue', "'continue' used outside a loop"),
            ('return', "'return' used outside a function"),
            ('return 1', "'return' used outside a function"),
            ('if (true) { break }', "'break' used outside a loop"),
            ('if (true) { continue } else { }', "'continue' used outside a loop"),
            ('if (true) { return 1 }', "'return' used outside a function"),
            ('while (true) { return 1 }', "'return' used outside a function"),
            ('while (false) { }; break', "'break' used outside a loop"),
            ('while (true) { break }; continue', "'continue' used outside a loop"),
            ('function f() { break }', "'break' used outside a loop"),
            ('function f() { continue }', "'continue' used outside a loop"),
            ('function f() { if (true) { break } }', "'break' used outside a loop"),
            ('x = function() { break }', "'break' used outside a loop"),
            ('while (true) { function f() { break } }', "'break' used outside a loop"),
            ('while (true) { function f() { continue } }', "'continue' used outside a loop"),
            ('while (true) { x = function() { break } }', "'break' used outside a loop"),
            ('while (true) { function f() { while (true) { break }; break } }', "'break' used outside a loop"),
            ('function f() { while (true) { function g() { break } } }', "'break' used outside a loop"),
            ('function f() { return 1 }; return 2', "'return' used outside a function"),
            ('function f(a, a) { }', 'Duplicate parameter name: a'),
            ('function f(a, b, a) { }', 'Duplicate parameter name: a'),
            ('x = function(a, a) { }', 'Duplicate parameter name: a'),
            ('function f() { function g(b, c, b) { } }', 'Duplicate parameter name: b'),
            ('while (true) { x = function(q, q) { } }', 'Duplicate parameter name: q'),
            ('function f(a) { return function(a, a) { } }', 'Duplicate parameter name: a'),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(ValueError) as raised:
                    check_source(source)
                self.assertEqual(str(raised.exception), message)

    def test_shadowed_parameter_names_are_not_duplicates(self):
        check_source('function f(a) { return function(a) { return a } }')
        check_source('function f(a, b) { }; function g(a, b) { }')

    def test_rejection_happens_before_any_statement_runs(self):
        for source in ['print(1); break', 'x = 1; return', 'print(1); function f(a, a) { }; print(2)',
                       'print(1); while (true) { function f() { break } }']:
            with self.subTest(source=source):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    with self.assertRaises(ValueError):
                        evaluator.evaluate_source(source, {})
                self.assertEqual(output.getvalue(), '')

    def test_uncalled_and_unreached_code_is_still_checked(self):
        for source in ['if (false) { break }', 'function f() { break }; x = 1', 'while (false) { function f(a, a) { } }']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    evaluator.evaluate_source(source, {})

    def test_accepted_programs_still_run(self):
        _, environment = evaluator.evaluate_source(
            'i = 0; while (true) { i = i + 1; if (i == 3) { break } }; '
            'function f(n) { while (true) { return n * 2 } }; x = f(i)', {})
        self.assertEqual((environment['i'], environment['x']), (3, 6))


if __name__ == '__main__':
    unittest.main()
