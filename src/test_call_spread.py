import unittest

from evaluator import evaluate_source

PRELUDE = '''
    log = [];
    function add(a, b) { return a + b };
    function none() { return "none" };
    function three(a, b, c) { return [a, b, c] };
    function mark(v) { set log = log + [v]; return v };
    function items() { set log = log + ["items"]; return [1, 2] };
    function quit() { exit(3) };
    pair = [10, 20]; empty = [];
'''


class CallSpreadTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = add(...pair)', 30),
            ('x = add(1, ...[2])', 3),
            ('x = add(...[1], 2)', 3),
            ('x = add(...[1], ...[2])', 3),
            ('x = add(...[], ...pair)', 30),
            ('x = none(...empty)', 'none'),
            ('x = none(...[], ...[])', 'none'),
            ('x = three(...[1], 2, ...[3])', [1, 2, 3]),
            ('x = three(0, ...[1, 2])', [0, 1, 2]),
            ('x = three(...[1, 2, 3])', [1, 2, 3]),
            ('x = [1, 2]; x = add(...x)', 3),
            ('f = function(a) { return a * 2 }; x = f(...[4])', 8),
            ('x = add(...[add(1, 2), 4])', 7),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_arguments_are_evaluated_once_in_source_order(self):
        cases = [
            ('x = three(mark("a"), ...[mark("b"), mark("c")])', ['a', 'b', 'c'], ['a', 'b', 'c']),
            ('x = add(...items())', 3, ['items']),
            ('x = three(mark(1), ...items())', [1, 1, 2], [1, 'items']),
            ('x = add(...[mark(1), mark(2)])', 3, [1, 2]),
        ]
        for source, expected, order in cases:
            with self.subTest(source=source):
                environment = self.run_source(source)
                self.assertEqual((environment['x'], environment['log']), (expected, order))

    def test_spread_does_not_change_the_source_list(self):
        environment = self.run_source('src = [1, 2]; x = add(...src); src[0] = 9; y = add(...src)')
        self.assertEqual((environment['x'], environment['y'], environment['src']), (3, 11, [9, 2]))

    def test_failures(self):
        cases = [
            ('add(...1)', TypeError),
            ('add(...null)', TypeError),
            ('add(..."ab")', TypeError),
            ('add(...{"a": 1})', TypeError),
            ('add(...add)', TypeError),
            ('add(...[1])', TypeError),
            ('add(...[1, 2, 3])', TypeError),
            ('add(...[1], ...[2], ...[3])', TypeError),
            ('none(...[1])', TypeError),
            ('add(...)', SyntaxError),
            ('add(......pair)', SyntaxError),
            ('add(1, ...)', SyntaxError),
            ('add(... ...pair)', SyntaxError),
            ('x = ...pair', SyntaxError),
            ('[...pair]', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_arity_is_checked_after_expansion(self):
        self.assertEqual(self.run_source('x = three(...[1, 2], 3)')['x'], [1, 2, 3])
        with self.assertRaises(TypeError):
            self.run_source('three(...[1, 2])')

    def test_evaluation_status(self):
        for source in ['add(...quit())', 'add(1, ...[quit()])', 'add(quit(), ...pair)']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
