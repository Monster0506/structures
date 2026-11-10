from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).with_name('runner.py')
SHOW = 'print(length(argv)); i = 0; while (i < length(argv)) { print(argv[i]); i = i + 1 }'


class OsArgumentTests(unittest.TestCase):
    def run_runner(self, *arguments):
        return subprocess.run([sys.executable, str(RUNNER), *arguments], capture_output=True,
                              text=True, stdin=subprocess.DEVNULL, timeout=10)

    def test_inline_source_arguments(self):
        cases = [
            ([], []),
            (['one'], ['one']),
            (['first', 'two words'], ['first', 'two words']),
            (['b', 'a', 'c'], ['b', 'a', 'c']),
            ([''], ['']),
            (['', 'x', ''], ['', 'x', '']),
            (['  padded  '], ['  padded  ']),
            (['42', '3.5', '-7', 'true', 'null'], ['42', '3.5', '-7', 'true', 'null']),
            (['--help', '-x', '--', '-', '--flag=value'], ['--help', '-x', '--', '-', '--flag=value']),
            (['a;b', '$HOME', '*', 'a"b', "it's"], ['a;b', '$HOME', '*', 'a"b', "it's"]),
            (['x.v', 'y.t'], ['x.v', 'y.t']),
            (['caf\u00e9'], ['caf\u00e9']),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result = self.run_runner(SHOW, *arguments)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, '')
                self.assertEqual(result.stdout.splitlines(), [str(len(expected)), *expected])

    def test_source_file_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory, 'program.v')
            program.write_text(SHOW)
            for arguments in ([], ['first', 'two words'], ['', '--flag', '12']):
                with self.subTest(arguments=arguments):
                    result = self.run_runner(str(program), *arguments)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.splitlines(), [str(len(arguments)), *arguments])
                    self.assertNotIn('program.v', result.stdout)

    def test_arguments_are_strings_and_argv_is_an_ordinary_binding(self):
        result = self.run_runner('print(type(argv)); print(type(argv[0])); print(argv[0] == "5")', '5')
        self.assertEqual(result.stdout.splitlines(), ['list', 'string', 'true'])
        result = self.run_runner('argv = 1; print(argv)', 'x')
        self.assertEqual(result.stdout.splitlines(), ['1'])
        result = self.run_runner('function f() { return length(argv) }; print(f())', 'a', 'b')
        self.assertEqual(result.stdout.splitlines(), ['2'])

    def test_arguments_do_not_change_the_exit_status(self):
        self.assertEqual(self.run_runner('exit(3)', 'a', 'b').returncode, 3)
        self.assertEqual(self.run_runner('exit(length(argv))', 'a', 'b').returncode, 2)

    def test_usage_without_a_program(self):
        result = self.run_runner()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Usage', result.stdout)


if __name__ == '__main__':
    unittest.main()
