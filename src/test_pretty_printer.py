import contextlib
import io
import unittest

import evaluator
from parser import parse
from pretty_printer import format_source
from tokenizer import tokenize

EXPRESSIONS = [
    '1', '2.5', '0.1', '1.0', '10000000000000000.0', '"text"', '""', 'true', 'false', 'null', 'name',
    '"quote\\" back\\\\ new\\n tab\\t cr\\r"', '"caf\u00e9 \u2603"',
    'a + b * c', '(a + b) * c', 'a - (b - c)', 'a - b - c', 'a / (b * c)', 'a * b / c', 'a * (b / c)',
    '-a', '- -a', '-(a * b)', '-a * b', '-(a + b)', 'a - -b', '(-a)[0]', '-a[0]',
    'a < b', '(a < b) == (c < d)', 'a + 1 < b * 2', 'a == b', 'a != b', 'a <= b', 'a >= b', 'a > b',
    'not a', 'not not a', 'not (a and b)', 'not a and b', 'not a == b', '(not a) == b',
    'a and b and c', 'a and (b and c)', 'a or b or c', 'a or (b or c)', 'a or b and c', '(a or b) and c',
    'a and not b or c',
    'x = 1', 'x = y = 1', '(x = 1) + 1', '[x = 1, y = 2]', 'f(x = 1)', 'a[0] = 1', 'a[b][c] = d',
    '[]', '[1, 2, 3]', '[1, [2, [3]]]', '{}', '{"a": 1, "b": [1, 2]}', '{"a": {"b": {}}}', '{"k" + "1": 2}',
    'a[0]', 'a[0][1]', '(a + b)[0]', 'a.b.c', 'a["b"]["c"]', '[1, 2][0]', '{"a": 1}["a"]',
    'f()', 'f(1)', 'f(1, 2)(3)', 'f(g(1), [2])', '(f)(1)', 'a[0](1)', 'a.b(1).c',
    'function() { }', 'function(a, b) { return a + b }', '(function(x) { return x })(1)',
    'function(x) { return function(y) { return x + y } }',
    'input()', 'input("name? ")', 'length(a)', 'head(a)', 'tail(a)', 'copy(a)', 'type(a)', 'string(a)',
    'number("5")', 'boolean("true")', 'slice(a, 1, 2)', 'slice(tail(a), 0, length(a) - 1)',
]

PROGRAMS = [
    '',
    'x = 1',
    'x = 1; y = x + 1; print(y)',
    'print(1 + 2 * 3)',
    'print("a" + "b")',
    'exit()',
    'exit(3)',
    'assert 1 < 2, "must hold"',
    'assert true, "quote \\" and \\\\"',
    'if (true) { print(1) }',
    'if (false) { } else { print(2) }',
    'if (true) { if (false) { print(1) } else { print(2) } } else { print(3) }',
    'i = 0; while (i < 3) { i = i + 1; if (i == 2) { continue }; print(i) }',
    'while (true) { break }',
    'i = 0; while (true) { i = i + 1; if (i > 2) { break } }',
    'function f(a, b) { return a + b }; print(f(1, 2))',
    'function f() { return }',
    'function f() { }',
    'function fact(n) { if (n <= 1) { return 1 }; return n * fact(n - 1) }; print(fact(5))',
    'x = 1; function f() { set x = x + 1 }; f(); print(x)',
    'function counter() { n = 0; return function() { set n = n + 1; return n } }; c = counter(); c(); print(c())',
    'a = [1, 2, 3]; a[1] = 9; print(a)',
    'o = {"a": 1, "b": [1, 2]}; o.a = 2; o["c"] = null; print(o)',
    'a = [3, 1, 2]; print(slice(a, 0, 2)); print(head(a)); print(tail(a)); print(length(a))',
    'x = y = 2; print(x + y)',
    'print(not (1 < 2 and 2 < 3) or false)',
    'print(-(2 + 3) * 2)',
    'print(type(copy([1, [2]])))',
    'print(string(1.5) + "!")',
    'print(number("7") + 1)',
    'print(boolean("true"))',
    'f = function(x) { return x * 2 }; print(f(4))',
    'print((function(x) { return x + 1 })(1))',
    'print([1, 2][1]); print({"a": 3}["a"])',
    'x = 0; while (x < 2) { y = 0; while (y < 2) { y = y + 1; set x = x + 1 } }; print(x)',
    '// comment\nx = 1 // trailing\n',
]


def parse_source(source):
    return parse(tokenize(source))


def run(source):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result, _ = evaluator.evaluate_source(source, {})
    return output.getvalue(), result


class PrettyPrinterTests(unittest.TestCase):
    def test_expressions_round_trip(self):
        for source in EXPRESSIONS:
            with self.subTest(source=source):
                ast = parse_source(source)
                printed = format_source(ast)
                self.assertEqual(parse_source(printed), ast)

    def test_programs_round_trip(self):
        for source in PROGRAMS:
            with self.subTest(source=source):
                ast = parse_source(source)
                printed = format_source(ast)
                self.assertEqual(parse_source(printed), ast)

    def test_printing_is_stable(self):
        for source in EXPRESSIONS + PROGRAMS:
            with self.subTest(source=source):
                printed = format_source(parse_source(source))
                self.assertEqual(format_source(parse_source(printed)), printed)

    def test_printed_programs_behave_the_same(self):
        for source in PROGRAMS:
            with self.subTest(source=source):
                printed = format_source(parse_source(source))
                self.assertEqual(run(printed), run(source))

    def test_printed_failures_are_the_same(self):
        for source in ['x = 1 + "a"', 'a = [1]; a[5]', 'unknown', 'function f(a) { }; f()', 'assert 1 > 2, "no"']:
            with self.subTest(source=source):
                printed = format_source(parse_source(source))
                try:
                    expected = run(source)
                except Exception as error:
                    with self.assertRaises(type(error)):
                        run(printed)
                else:
                    self.assertEqual(run(printed), expected)

    def test_exact_text(self):
        cases = [
            ('x=1+2*3', 'x = 1 + 2 * 3;\n'),
            ('x=(1+2)*3', 'x = (1 + 2) * 3;\n'),
            ('x=1-(2-3)', 'x = 1 - (2 - 3);\n'),
            ('x=-(a*b)', 'x = -(a * b);\n'),
            ('x=not(a and b)', 'x = not (a and b);\n'),
            ('o.a.b = 1', 'o["a"]["b"] = 1;\n'),
            ('f = 1.0', 'f = 1.0;\n'),
            ('s = "a\\n\\"b"', 's = "a\\n\\"b";\n'),
            ('print(1);print(2)', 'print(1);\nprint(2);\n'),
            ('function f(a,b){return a+b}', 'f = function(a, b) {\n    return a + b;\n};\n'),
            ('if(x){y=1}else{y=2}', 'if (x) {\n    y = 1;\n} else {\n    y = 2;\n};\n'),
            ('while(true){break}', 'while (true) {\n    break;\n};\n'),
            ('while(true){if(a){continue}}',
             'while (true) {\n    if (a) {\n        continue;\n    };\n};\n'),
            ('if(a){}', 'if (a) {};\n'),
            ('f=function(){return function(){return 1}}',
             'f = function() {\n    return function() {\n        return 1;\n    };\n};\n'),
            ('', ''),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(format_source(parse_source(source)), expected)

    def test_unknown_node_is_rejected(self):
        with self.assertRaises(ValueError):
            format_source({"tag": "program", "statements": {"tag": "statement_list",
                                                            "statements": [{"tag": "mystery"}]}})


if __name__ == '__main__':
    unittest.main()
