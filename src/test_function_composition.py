import unittest

from evaluator import evaluate_source

PRELUDE = '''
    log = [];
    function inc(v) { return v + 1 };
    function dbl(v) { return v * 2 };
    function neg(v) { return -v };
    function two(a, b) { return a + b };
    function zero() { return 0 };
    function noteF(v) { set log = log + ["f"]; return v };
    function noteG(v) { set log = log + ["g"]; return v };
    function adder(n) { return function(v) { return v + n } };
    function build(name) { set log = log + [name]; return inc };
    function quit() { exit(3) };
    function quitter(v) { exit(3) };
'''


class FunctionCompositionTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = (inc << dbl)(5)', 11),
            ('x = (dbl << inc)(5)', 12),
            ('x = (inc << inc)(5)', 7),
            ('x = (inc << dbl << neg)(5)', -9),
            ('x = ((inc << dbl) << neg)(5)', -9),
            ('x = (inc << (dbl << neg))(5)', -9),
            ('h = inc << dbl; x = h(1) + h(2)', 8),
            ('x = (adder(10) << adder(100))(1)', 111),
            ('x = (adder(1) << adder(2) << adder(3))(0)', 6),
            ('x = (function(v) { return v * v } << inc)(2)', 9),
            ('x = ((function(v) { return [v] }) << inc)(2)', [3]),
            ('x = (inc << dbl)(inc(1))', 5),
            ('fs = [inc << dbl, dbl << inc]; x = fs[0](3) + fs[1](3)', 15),
            ('x = type(inc << dbl)', 'function'),
            ('x = (inc << dbl) == (inc << dbl)', False),
            ('c = inc << dbl; x = c == c', True),
            ('x = string(inc << dbl)', '<function>'),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_precedence_and_associativity(self):
        self.assertEqual(self.run_source('x = (inc << dbl)(1) * 10')['x'], 30)
        self.assertEqual(self.run_source('x = 2 * (inc << dbl)(1)')['x'], 6)
        for source in ['inc << dbl * 2', 'inc * dbl << neg']:
            with self.subTest(source=source):
                with self.assertRaises(TypeError):
                    self.run_source(source)

    def test_environments_are_preserved(self):
        environment = self.run_source(
            'n = 1; function make() { n = 100; return function(v) { return v + n } }; '
            'g = make(); x = (g << inc)(0); n = 5; y = (inc << g)(0)')
        self.assertEqual((environment['x'], environment['y']), (101, 101))

    def test_call_order_and_single_evaluation(self):
        cases = [
            ('x = (noteF << noteG)(1)', ['g', 'f']),
            ('x = (noteF << noteG << noteF)(1)', ['f', 'g', 'f']),
            ('h = build("a") << build("b"); x = 0', ['a', 'b']),
            ('h = build("a") << build("b"); h(1); h(2); x = 0', ['a', 'b']),
        ]
        for source, order in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['log'], order)

    def test_failures(self):
        cases = [
            ('1 << inc', TypeError),
            ('inc << 1', TypeError),
            ('null << inc', TypeError),
            ('"a" << "b"', TypeError),
            ('[inc] << inc', TypeError),
            ('two << inc', TypeError),
            ('inc << two', TypeError),
            ('zero << inc', TypeError),
            ('(inc << dbl)(1, 2)', TypeError),
            ('(inc << dbl)()', TypeError),
            ('(inc << neg)("a")', TypeError),
            ('inc <<', SyntaxError),
            ('<< inc', SyntaxError),
            ('inc << << dbl', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        for source in ['quit() << inc', 'inc << quit()', '(inc << quitter)(1)', '(quitter << inc)(1)']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
