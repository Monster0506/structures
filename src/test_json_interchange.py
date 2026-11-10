import unittest

from evaluator import evaluate_source

PRELUDE = '''
    record = {"name": "Ada", "scores": [10, 2.5, 0], "active": true, "none": null, "nested": {"a": [[], {}]}};
    function f() { return 1 };
    function quit() { exit(3) };
'''


class JsonInterchangeTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_encode(self):
        cases = [
            ('null', 'null'),
            ('true', 'true'),
            ('false', 'false'),
            ('1', '1'),
            ('2.0', '2.0'),
            ('1.5', '1.5'),
            ('-3', '-3'),
            ('"a"', '"a"'),
            ('""', '""'),
            ('[]', '[]'),
            ('{}', '{}'),
            ('[1, "a", null, true]', '[1, "a", null, true]'),
            ('{"b": 1, "a": 2}', '{"b": 1, "a": 2}'),
            ('{"a": {"b": [1, {"c": null}]}}', '{"a": {"b": [1, {"c": null}]}}'),
            ('[true, 1, false, 0]', '[true, 1, false, 0]'),
            (r'"q\"s\\n\t"', '"q\\"s\\\\n\\t"'),
            (r'"line\nbreak"', '"line\\nbreak"'),
            ('"\u00e9"', '"\u00e9"'),
            ('[[1], [1]]', '[[1], [1]]'),
            ('{"k": "v", "k2": [] }', '{"k": "v", "k2": []}'),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(f'x = jsonEncode({source})')['x'], expected)

    def test_shared_references_are_not_cycles(self):
        self.assertEqual(self.run_source('s = [1]; x = jsonEncode([s, s, {"k": s}])')['x'], '[[1], [1], {"k": [1]}]')

    def test_decode(self):
        cases = [
            ('null', None),
            ('true', True),
            ('false', False),
            ('1', 1),
            ('-4', -4),
            ('2.5', 2.5),
            ('1.0', 1.0),
            ('1e2', 100.0),
            ('"a"', 'a'),
            ('[]', []),
            ('{}', {}),
            (' [1, 2 , 3] ', [1, 2, 3]),
            ('{"a": [1, {"b": null}], "c": true}', {'a': [1, {'b': None}], 'c': True}),
            (r'"a\"b\\c\nd"', 'a"b\\c\nd'),
            (r'"\u00e9"', '\u00e9'),
            ('"\u00e9"', '\u00e9'),
            ('"\\ud83d\\ude00"', '\U0001f600'),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                _, environment = evaluate_source('source = ' + _quote(text) + '; x = jsonDecode(source)', {})
                self.assertEqual(environment['x'], expected)

    def test_boolean_and_number_stay_distinct(self):
        environment = self.run_source(
            'x = jsonDecode("[true, 1, false, 0, 1.0]"); '
            't = [type(x[0]), type(x[1]), type(x[2]), type(x[3]), type(x[4])]; '
            'same = [x[0] == 1, x[1] == true, x[2] == 0, x[3] == false]')
        self.assertEqual(environment['t'], ['boolean', 'number', 'boolean', 'number', 'number'])
        self.assertEqual(environment['same'], [False, False, False, False])
        self.assertEqual(self.run_source('x = jsonEncode(jsonDecode("[true, 1]"))')['x'], '[true, 1]')

    def test_round_trips(self):
        sources = [
            'record',
            '[]', '{}', '[[], {}, [[]]]', '0', '""', 'false', 'null',
            '{"\u00e9": ["\u00fc", "\\n", "\\"", "\\\\"]}',
            '[1, 2.5, -3, 1.0, true, false, null]',
            '{"a": {"b": {"c": [1, {"d": []}]}}}',
        ]
        for source in sources:
            with self.subTest(source=source):
                environment = self.run_source(f'v = {source}; w = jsonDecode(jsonEncode(v)); same = w == v')
                self.assertTrue(environment['same'])

    def test_decoded_data_is_independent(self):
        environment = self.run_source(
            'text = jsonEncode(record); a = jsonDecode(text); b = jsonDecode(text); '
            'a.scores[0] = 99; same = a == b; first = b.scores[0]')
        self.assertEqual((environment['same'], environment['first']), (False, 10))

    def test_cycles_and_functions_are_rejected(self):
        cases = [
            ('a = [0]; a[0] = a; jsonEncode(a)', ValueError),
            ('o = {}; o.me = o; jsonEncode(o)', ValueError),
            ('a = [0]; b = [a]; a[0] = b; jsonEncode(b)', ValueError),
            ('o = {"list": []}; o.list = [o]; jsonEncode(o)', ValueError),
            ('jsonEncode(f)', TypeError),
            ('jsonEncode([f])', TypeError),
            ('jsonEncode({"a": [1, {"b": f}]})', TypeError),
            ('jsonEncode({"a": function() { return 1 }})', TypeError),
            ('jsonEncode(jsonEncode)', TypeError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_nonfinite_numbers_are_rejected(self):
        huge = '1' + '0' * 400 + '.0'
        for source in [f'jsonEncode({huge})', f'jsonEncode([-{huge}])', f'jsonEncode({{"a": {huge}}})']:
            with self.subTest(source=source[:20]):
                with self.assertRaises(ValueError):
                    self.run_source(source)

    def test_malformed_json_is_rejected(self):
        for text in ['', ' ', '{', '[1,', '{"a"}', '{"a": }', "{'a': 1}", '[1] x', 'tru', '"abc',
                     '[1 2]', '{"a": 1,}', '[,]', 'NaN', 'Infinity', '-Infinity', '[NaN]', '1e999', '[1e999]',
                     '01', '+1', '.5', "'a'", 'undefined']:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    evaluate_source('x = jsonDecode(' + _quote(text) + ')', {})

    def test_wrong_arguments(self):
        for source, error in [('jsonDecode(1)', TypeError), ('jsonDecode(null)', TypeError),
                              ('jsonDecode([])', TypeError), ('jsonDecode({})', TypeError),
                              ('jsonDecode(true)', TypeError), ('jsonDecode()', TypeError),
                              ('jsonDecode("1", "2")', TypeError), ('jsonEncode()', TypeError),
                              ('jsonEncode(1, 2)', TypeError)]:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_names_are_ordinary_functions(self):
        environment = self.run_source('x = type(jsonEncode); y = type(jsonDecode); jsonEncode = 5; z = jsonEncode')
        self.assertEqual((environment['x'], environment['y'], environment['z']), ('function', 'function', 5))

    def test_evaluation_status(self):
        for source in ['jsonEncode(quit())', 'jsonDecode(quit())', 'jsonEncode([1, quit()])']:
            with self.subTest(source=source):
                result, _ = evaluate_source(PRELUDE + source, {})
                self.assertEqual(result, (3, 'exit'))


def _quote(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


if __name__ == '__main__':
    unittest.main()
