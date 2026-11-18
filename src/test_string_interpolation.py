import unittest

from evaluator import evaluate_source

PRELUDE = '''
    name = "Ada"; count = 3; ratio = 1.5; flag = true; nothing = null;
    items = [1, "two"]; record = {"a": 1}; tricky = "$${name}";
    function greet() { local = "inner"; return "${local}/${name}" };
'''


class StringInterpolationTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            (r'"Hello, ${name}!"', 'Hello, Ada!'),
            (r'"${name}"', 'Ada'),
            (r'"${name}${count}"', 'Ada3'),
            (r'"${count} + ${ratio} = ${flag}"', '3 + 1.5 = true'),
            (r'"${nothing} ${items} ${record}"', 'null [1, "two"] {"a": 1}'),
            (r'"${tricky}"', '${name}'),
            (r'greet()', 'inner/Ada'),
            (r'"a" + "${name}" + "b"', 'aAdab'),
            (r'"$${name}"', '${name}'),
            (r'"$${name} ${name}"', '${name} Ada'),
            (r'"plain"', 'plain'),
            (r'""', ''),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source('x = ' + source)['x'], expected)

    def test_dollar_without_marker_is_text(self):
        for text in ['cost: $5', '$', '$$', '$ {name}', '{name}', '$name']:
            with self.subTest(text=text):
                self.assertEqual(self.run_source(f'x = "{text}"')['x'], text)

    def test_escapes_still_decode(self):
        self.assertEqual(self.run_source(r'x = "\t${name}\n\"${count}\""')['x'], '\tAda\n"3"')

    def test_failures(self):
        cases = [
            (r'"${missing}"', ValueError),
            (r'"${"', SyntaxError),
            (r'"${name"', SyntaxError),
            (r'"${}"', SyntaxError),
            (r'"${ name }"', SyntaxError),
            (r'"${1x}"', SyntaxError),
            (r'"${a.b}"', SyntaxError),
            (r'"${name + 1}"', SyntaxError),
            (r'"${${name}}"', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source('x = ' + source)

    def test_syntax_error_has_location(self):
        with self.assertRaisesRegex(SyntaxError, 'line 2, column 5'):
            evaluate_source('a = 1;\nx = "${}"', {})


if __name__ == '__main__':
    unittest.main()
