import unittest
from unittest.mock import patch

from evaluator import evaluate_source
from parser import parse
from tokenizer import tokenize

PRELUDE = 'neg=-7; three=3; half=0.5; '


class NumericOperatorTests(unittest.TestCase):
    def test_slide_program(self):
        with patch('builtins.print') as output:
            evaluate_source('print(2 ** 3 ** 2); print(17 % 5);')
        self.assertEqual([c.args[0] for c in output.call_args_list], ['512', '2'])

    def test_tokens(self):
        self.assertEqual([t['tag'] for t in tokenize('a**b*c%d')],
                         ['identifier', '**', 'identifier', '*', 'identifier',
                          '%', 'identifier', None])

    def test_results(self):
        cases = [
            ('2 ** 3 ** 2', 512),
            ('(2 ** 3) ** 2', 64),
            ('-2 ** 2', -4),
            ('(-2) ** 2', 4),
            ('2 ** -1', 0.5),
            ('2 * 3 ** 2', 18),
            ('10 - 7 % 4 * 2', 4),
            ('17 % 5', 2),
            ('neg % three', 2),
            ('7 % -three', -2),
            ('neg % -three', -1),
            ('7.5 % 2', 1.5),
            ('-7.5 % 2', 0.5),
            ('4 ** half', 2.0),
            ('half ** 2', 0.25),
            ('(-8) ** 2.0', 64.0),
            ('0 ** 0', 1),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                _, env = evaluate_source(PRELUDE + 'result=' + source)
                self.assertEqual(env['result'], expected)
                self.assertIs(type(env['result']), type(expected))

    def test_runtime_errors(self):
        cases = [
            ('true ** 2', TypeError, 'Arithmetic does not accept boolean operands'),
            ('2 % false', TypeError, 'Arithmetic does not accept boolean operands'),
            ('"%d" % 5', TypeError, 'Operator % requires two numbers'),
            ('"ab" ** 2', TypeError, 'Operator ** requires two numbers'),
            ('17 / 0', ZeroDivisionError, 'Division by zero'),
            ('half / 0.0', ZeroDivisionError, 'Division by zero'),
            ('17 % 0', ZeroDivisionError, 'Remainder by zero'),
            ('17 % 0.0', ZeroDivisionError, 'Remainder by zero'),
            ('0 ** -1', ZeroDivisionError, 'Cannot raise zero to a negative power'),
            ('(-8) ** half', ValueError, 'Negative base requires an integer exponent'),
            ('10.0 ** 400', OverflowError, 'Exponent result is too large'),
        ]
        for source, error, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(error) as caught:
                    evaluate_source(PRELUDE + 'result=' + source)
                self.assertEqual(str(caught.exception), message)

    def test_syntax_errors(self):
        for source in ('2 **', '% 3', '2 ** ** 3', '2 % % 3'):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                parse(tokenize(source))


if __name__ == '__main__':
    unittest.main()
