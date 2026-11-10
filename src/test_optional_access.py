import unittest

from evaluator import evaluate_source

PRELUDE = '''
    a = {"b": {"c": 1}, "n": null, "list": [1, 2]}; nothing = null; zero = 0;
    log = [];
    function mark(v) { set log = log + [v]; return v };
    function quit() { exit(3) };
'''


class OptionalAccessTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = a?.b', {'c': 1}),
            ('x = a?.b?.c', 1),
            ('x = a?.b.c', 1),
            ('x = a.b?.c', 1),
            ('x = a?.list[1]', 2),
            ('x = nothing?.b', None),
            ('x = a?.n?.c', None),
            ('x = a.n?.c', None),
            ('x = a?.n?.c?.d', None),
            ('x = nothing?.b.c', None),
            ('x = nothing?.b.c.d', None),
            ('x = nothing?.b["c"]', None),
            ('x = nothing?.b[0].c', None),
            ('x = a?.b?.c + 1', 2),
            ('x = nothing?.b == null', True),
            ('x = a?.b?.c == 1', True),
            ('x = (nothing?.b)', None),
            ('x = [nothing?.b, a?.b?.c]', [None, 1]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_skipped_chain_is_not_evaluated(self):
        cases = [
            ('x = nothing?.b[mark(1)]', []),
            ('x = nothing?.b[mark(1)][mark(2)]', []),
            ('x = nothing?.f(mark(1))', []),
            ('x = a?.b[mark("c")]', ['c']),
            ('x = a?.n?.c[mark(1)]', []),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['log'], expected)

    def test_grouping_ends_the_chain(self):
        for source in ['(nothing?.b).c', '(nothing?.b)[0]', '(a?.n).c']:
            with self.subTest(source=source):
                with self.assertRaises(TypeError):
                    self.run_source(source)

    def test_failures(self):
        cases = [
            ('a?.n.c', TypeError),
            ('a?.b?.missing', KeyError),
            ('a?.missing', KeyError),
            ('zero?.b', TypeError),
            ('a?.list?.b', TypeError),
            ('a?.b = 1', ValueError),
            ('nothing?.b = 1', ValueError),
            ('a?.', SyntaxError),
            ('a?.1', SyntaxError),
            ('a?."b"', SyntaxError),
            ('a ? b', SyntaxError),
            ('a?', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        for source in ['quit()?.b', 'a?.b[quit()]', 'a?.b?.c[quit()]']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
