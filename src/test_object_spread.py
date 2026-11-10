import unittest

from evaluator import evaluate_source

PRELUDE = '''
    a = {"p": 1, "n": "a", "list": [1, 2]}; b = {"n": "b", "q": 2}; empty = {};
    log = [];
    function mark(v) { set log = log + [v]; return v };
    function source() { set log = log + ["source"]; return {"s": 1} };
    function quit() { exit(3) };
    function f() { return 1 };
'''


class ObjectSpreadTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = {...a}', {'p': 1, 'n': 'a', 'list': [1, 2]}),
            ('x = {...empty}', {}),
            ('x = {...empty, ...empty}', {}),
            ('x = {...empty, "k": 1}', {'k': 1}),
            ('x = {"k": 1, ...empty}', {'k': 1}),
            ('x = {...b, "k": 1}', {'n': 'b', 'q': 2, 'k': 1}),
            ('x = {"k": 1, ...b}', {'k': 1, 'n': 'b', 'q': 2}),
            ('x = {...a, "n": 9}', {'p': 1, 'n': 9, 'list': [1, 2]}),
            ('x = {"n": 9, ...a}', {'n': 'a', 'p': 1, 'list': [1, 2]}),
            ('x = {...a, ...b}["n"]', 'b'),
            ('x = {...b, ...a}["n"]', 'a'),
            ('x = {...a, ...b, "n": 0}["n"]', 0),
            ('x = {...a, "n": 0, ...b}["n"]', 'b'),
            ('x = {...{"u": 1}, ...{"v": 2}, "w": 3}', {'u': 1, 'v': 2, 'w': 3}),
            ('x = {...{...b, "z": 0}, "y": 1}', {'n': 'b', 'q': 2, 'z': 0, 'y': 1}),
            ('x = {"k" + "1": 1, ...b}', {'k1': 1, 'n': 'b', 'q': 2}),
            ('x = {...{"f": f}}["f"] == f', True),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_spread_is_shallow(self):
        environment = self.run_source('x = {...a}; x.p = 5; x.list[0] = 99; y = {...a}')
        self.assertEqual(environment['a'], {'p': 1, 'n': 'a', 'list': [99, 2]})
        self.assertIs(environment['x']['list'], environment['a']['list'])
        self.assertIs(environment['y']['list'], environment['a']['list'])
        self.assertIsNot(environment['x'], environment['a'])

    def test_entries_are_evaluated_in_source_order(self):
        environment = self.run_source('x = {"x": mark(1), ...source(), "y": mark(3), ...{"z": mark(4)}}')
        self.assertEqual(environment['log'], [1, 'source', 3, 4])
        self.assertEqual(environment['x'], {'x': 1, 's': 1, 'y': 3, 'z': 4})

    def test_explicit_duplicates_are_still_rejected(self):
        for source in ['{"a": 1, "a": 2}', '{"a": 1, ...b, "a": 2}', '{"n": 1, "n": 2, ...b}']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.run_source(source)

    def test_failures(self):
        cases = [
            ('{...[1]}', TypeError),
            ('{..."ab"}', TypeError),
            ('{...1}', TypeError),
            ('{...null}', TypeError),
            ('{...true}', TypeError),
            ('{...f}', TypeError),
            ('{...a, ...f}', TypeError),
            ('{...}', SyntaxError),
            ('{... ...a}', SyntaxError),
            ('{...a ...b}', SyntaxError),
            ('{...a: 1}', SyntaxError),
            ('{...a,}', SyntaxError),
            ('[...a]', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        for source in ['{...quit()}', '{"k": 1, ...quit()}', '{...a, "k": quit()}']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
