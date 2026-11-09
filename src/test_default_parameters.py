import unittest

from evaluator import evaluate_source

PRELUDE = '''
    function greet(name, prefix = "Hello ") { return prefix + name };
    function pick(value = "default") { return value };
    function bump(items = [0]) { items[0] = items[0] + 1; return items[0] };
    function makeGreeter(word) { return function(name, prefix = word) { return prefix + name } };
    function range(low, high = low + 1) { return [low, high] };
    n = 1;
    function current(x = n) { return x };
'''


class DefaultParameterTests(unittest.TestCase):
    def test_results(self):
        cases = [
            ('result = greet("Ann")', "Hello Ann"),
            ('result = greet("Ann", "Hi ")', "Hi Ann"),
            ('result = pick()', "default"),
            ('result = pick(null)', None),
            ('result = makeGreeter("Hey ")("Bo")', "Hey Bo"),
            ('result = range(3)', [3, 4]),
            ('set n = 2; result = current()', 2),
            ('result = [bump(), bump()]', [1, 1]),
            ('shared = [5]; result = [bump(shared), bump(shared), shared]', [6, 7, [7]]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                _, env = evaluate_source(PRELUDE + source)
                self.assertEqual(env['result'], expected)

    def test_failures(self):
        cases = [
            ('greet("a", "b", "c")', TypeError, "Function expects 1 to 2 argument(s), got 3"),
            ('greet()', TypeError, "Function expects 1 to 2 argument(s), got 0"),
            ('function bad(a = 1, b) { }', SyntaxError,
             "Expected a default value for parameter b after a defaulted parameter"),
        ]
        for source, error, message in cases:
            with self.subTest(source=source):
                with self.assertRaises(error) as caught:
                    evaluate_source(PRELUDE + source)
                self.assertEqual(str(caught.exception), message)


if __name__ == '__main__':
    unittest.main()
