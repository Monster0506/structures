from pathlib import Path
import subprocess
import sys
import unittest

from evaluator import evaluate_source

PRELUDE = '''
    log = []; n = 0;
    function boom(v) { throw v; set n = 99 };
    function quiet() { return 5 };
'''


class TryCatchTests(unittest.TestCase):
    def run_source(self, source):
        return evaluate_source(PRELUDE + source, {})

    def test_results(self):
        cases = [
            ('try { throw "problem" } catch e { x = e }', 'problem'),
            ('try { throw 42 } catch e { x = e + 1 }', 43),
            ('try { throw [1, 2] } catch e { x = e[1] }', 2),
            ('try { throw {"code": 7} } catch e { x = e.code }', 7),
            ('try { throw null } catch e { x = e }', None),
            ('try { throw 1 + 2 } catch e { x = e }', 3),
            ('x = 0; try { x = 1 } catch e { x = 2 }', 1),
            ('try { throw 1; x = 2 } catch e { x = 3 }', 3),
            ('try { boom("deep") } catch e { x = e }', 'deep'),
            ('try { x = boom(1) } catch e { x = e + 10 }', 11),
            ('try { try { throw 1 } catch e { throw e + 1 } } catch e { x = e }', 2),
            ('try { try { throw 1 } catch e { x = e } } catch e { x = 99 }', 1),
            ('try { try { throw 1 } catch inner { y = 0 } ; x = 5 } catch e { x = 6 }', 5),
            ('try { i = 0; while (true) { i = i + 1; if (i == 3) { throw i } } } catch e { x = e }', 3),
            ('try { throw "a" } catch e { y = 1 }; try { throw "b" } catch e { x = e }', 'b'),
            ('function f() { try { throw 1 } catch e { return e + 1 } }; x = f()', 2),
            ('function f() { try { return 1 } catch e { return 2 } }; x = f()', 1),
            ('function f() { try { boom(1) } catch e { return e }; return 0 }; x = f()', 1),
            ('x = 0; try { x = quiet() } catch e { x = -1 }', 5),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result, environment = self.run_source(source)
                self.assertEqual(result, (None, None))
                self.assertEqual(environment['x'], expected)

    def test_statements_after_a_throw_do_not_run(self):
        _, environment = self.run_source('try { boom(1); n = 1 } catch e { x = n }')
        self.assertEqual((environment['x'], environment['n']), (0, 0))

    def test_other_statuses_pass_through_try(self):
        cases = [
            ('try { exit(3) } catch e { x = 1 }', (3, 'exit')),
            ('while (true) { try { break } catch e { x = 1 } }', (None, None)),
            ('try { assert false, "no" } catch e { x = 1 }', (1, 'exit')),
            ('try { throw 1 } catch e { exit(4) }', (4, 'exit')),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)[0], expected)

    def test_uncaught_error_reaches_the_program_boundary(self):
        cases = [
            ('throw "bad"', ('bad', 'throw')),
            ('boom(2); n = 1', (2, 'throw')),
            ('try { throw 1 } catch e { throw e + 1 }', (2, 'throw')),
            ('i = 0; while (true) { i = i + 1; throw i }', (1, 'throw')),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result, environment = self.run_source(source)
                self.assertEqual(result, expected)
                self.assertEqual(environment['n'], 0)

    def test_runner_reports_uncaught_error(self):
        runner = Path(__file__).with_name('runner.py')
        cases = [
            ('throw "bad"', 'Uncaught error: "bad"'),
            ('function f() { throw [1, 2] }; f()', 'Uncaught error: [1, 2]'),
        ]
        for source, message in cases:
            with self.subTest(source=source):
                result = subprocess.run([sys.executable, str(runner), source],
                                        capture_output=True, text=True,
                                        stdin=subprocess.DEVNULL, timeout=10)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr.strip(), message)
        result = subprocess.run([sys.executable, str(runner), 'try { throw 1 } catch e { print(e) }'],
                                capture_output=True, text=True,
                                stdin=subprocess.DEVNULL, timeout=10)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '1\n', ''))

    def test_syntax_errors(self):
        for source in ['try { } catch { }', 'try { } catch (e) { }', 'try { }', 'try { } catch e',
                       'try catch e { }', 'throw', 'catch e { }', 'try { } catch 1 { }']:
            with self.subTest(source=source):
                with self.assertRaises(SyntaxError):
                    evaluate_source(source, {})


if __name__ == '__main__':
    unittest.main()
