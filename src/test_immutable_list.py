import contextlib
import io
import unittest

from evaluator import evaluate_source

PRELUDE = 'items = immutable([1, "two", true, null, 2.5]); alias = items; plain = [1, "two", true, null, 2.5]; '


class ImmutableListTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = items[0]', 1),
            ('x = items[1]', 'two'),
            ('x = items[3]', None),
            ('x = alias[4]', 2.5),
            ('x = items[1.0]', 'two'),
            ('x = length(items)', 5),
            ('x = length(immutable([]))', 0),
            ('x = type(items)', 'immutable list'),
            ('x = type(plain)', 'list'),
            ('x = items == alias', True),
            ('x = items == immutable([1, "two", true, null, 2.5])', True),
            ('x = immutable([1, 2]) == immutable([1, 2, 3])', False),
            ('x = immutable([1]) == immutable([true])', False),
            ('x = items == plain', False),
            ('x = plain == items', False),
            ('x = immutable([1, 2]) != immutable([1, 3])', True),
            ('x = [items] == [alias]', True),
            ('x = string(immutable([1, "a", null]))', 'immutable([1, "a", null])'),
            ('x = string([immutable([true])])', '[immutable([true])]'),
            ('x = copy(items) == items', True),
            ('x = immutable(items) == items', True),
            ('x = immutable(plain) == items', True),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_copy_is_the_same_immutable_value(self):
        environment = self.run_source('c = copy(items); items = immutable([9]); x = c[0]')
        self.assertEqual(environment['x'], 1)
        self.assertIsInstance(environment['c'], tuple)

    def test_construction_snapshots_the_list(self):
        environment = self.run_source('source = [1, 2]; frozen = immutable(source); source[0] = 9; x = frozen[0]')
        self.assertEqual(environment['x'], 1)

    def test_names_can_be_rebound(self):
        environment = self.run_source('items = immutable([7]); x = items[0]; y = alias[0]')
        self.assertEqual((environment['x'], environment['y']), (7, 1))

    def test_print(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.run_source('print(items)')
        self.assertEqual(output.getvalue(), 'immutable([1, "two", true, null, 2.5])\n')

    def test_failures(self):
        cases = [
            ('items[0] = 9', TypeError),
            ('alias[0] = 9', TypeError),
            ('items[10] = 9', TypeError),
            ('items["a"] = 9', TypeError),
            ('x = items[5]', IndexError),
            ('x = items[-1]', IndexError),
            ('x = items["a"]', TypeError),
            ('x = items + items', TypeError),
            ('x = items + plain', TypeError),
            ('x = plain + items', TypeError),
            ('x = items * 2', TypeError),
            ('x = items < items', TypeError),
            ('x = -items', TypeError),
            ('x = head(items)', TypeError),
            ('x = tail(items)', TypeError),
            ('x = slice(items, 0, 1)', TypeError),
            ('x = immutable([[1]])', TypeError),
            ('x = immutable([{"a": 1}])', TypeError),
            ('x = immutable([items])', TypeError),
            ('x = immutable([function() { return 1 }])', TypeError),
            ('x = immutable(1)', TypeError),
            ('x = immutable("ab")', TypeError),
            ('x = immutable({"a": 1})', TypeError),
            ('x = immutable()', SyntaxError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        result, _ = evaluate_source('function quit() { exit(3) }; immutable([quit()])', {})
        self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
