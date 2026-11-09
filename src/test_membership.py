import unittest

from evaluator import evaluate_source

PRELUDE = '''
    record = {"name": "Ada", "": 0}; numbers = [1, 2, 3];
    nested = [[1, 2], [3, [4]]]; flags = [true]; ones = [1];
    a = [0]; a[0] = a; b = [0]; b[0] = b;
    function f(x) { return x };
'''


class MembershipTests(unittest.TestCase):
    def test_results(self):
        cases = [
            ('"name" in record', True),
            ('3 in numbers', True),
            ('4 in numbers', False),
            ('[1, 2] in nested', True),
            ('[3, [4]] in nested', True),
            ('[3, [5]] in nested', False),
            ('2 in nested', False),
            ('1 in flags', False),
            ('true in ones', False),
            ('true in flags', True),
            ('b in [a]', True),
            ('a in a', True),
            ('"age" in record', False),
            ('"Ada" in record', False),
            ('"" in record', True),
            ('"" in {}', False),
            ('"" in "abc"', True),
            ('"" in ""', True),
            ('"a" in ""', False),
            ('"" in []', False),
            ('"bc" in "abc"', True),
            ('"ca" in "abc"', False),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result, env = evaluate_source(PRELUDE + f'r = {source}')
                self.assertEqual(result, (None, None))
                self.assertIs(env['r'], expected)

    def test_invalid_operand_types(self):
        cases = [
            ('1 in 5', 'in requires a list, object, or string on the right'),
            ('1 in true', 'in requires a list, object, or string on the right'),
            ('1 in null', 'in requires a list, object, or string on the right'),
            ('"parameters" in f', 'in requires a list, object, or string on the right'),
            ('1 in record', 'in requires a string on the left of an object or string'),
            ('1 in "123"', 'in requires a string on the left of an object or string'),
            ('["a"] in "abc"', 'in requires a string on the left of an object or string'),
        ]
        for source, message in cases:
            with self.subTest(source=source), self.assertRaisesRegex(TypeError, message):
                evaluate_source(PRELUDE + f'r = {source}')


if __name__ == '__main__':
    unittest.main()
