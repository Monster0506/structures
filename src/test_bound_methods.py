import contextlib
import io
import unittest

from evaluator import evaluate_source

PRELUDE = '''
    step = 5;
    function incr() { self.count = self.count + 1; return self.count };
    counter = {
        "count": 0, "name": "c", "items": [1, 2],
        "increment": incr,
        "add": function(n) { self.count = self.count + n; return self.count },
        "stepUp": function() { self.count = self.count + step; return self.count },
        "me": function() { return self },
        "own": function(self) { return self },
        "fact": function(n) { if (n <= 1) { return 1 }; return n * self.fact(n - 1) }
    };
    a = {"count": 0, "inc": incr}; b = {"count": 10, "inc": incr};
    function quit() { exit(3) };
'''


class BoundMethodTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluate_source(PRELUDE + source, {})
        return environment

    def test_results(self):
        cases = [
            ('x = counter.increment()', 1),
            ('counter.increment(); x = counter.increment()', 2),
            ('x = counter.add(5)', 5),
            ('x = counter["increment"]()', 1),
            ('x = counter.stepUp()', 5),
            ('step = 100; x = counter.stepUp()', 100),
            ('x = counter.fact(5)', 120),
            ('x = counter.own(7)', 7),
            ('x = counter.name', 'c'),
            ('x = counter.count', 0),
            ('x = counter.items', [1, 2]),
            ('saved = counter.increment; saved(); x = saved()', 2),
            ('saved = counter.increment; counter = null; x = saved()', 1),
            ('saved = counter.add; x = saved(2) + saved(3)', 7),
            ('a.inc(); a.inc(); b.inc(); x = [a.count, b.count]', [2, 11]),
            ('b.borrowed = a.inc; b.borrowed(); x = [a.count, b.count]', [1, 10]),
            ('fs = [counter.increment]; x = fs[0]() + fs[0]()', 3),
            ('x = counter.me() == counter', True),
            ('x = type(counter.increment)', 'function'),
            ('x = string(counter.increment)', '<function>'),
            ('x = counter.increment == counter.increment', True),
            ('saved = counter.increment; x = saved == counter.increment', True),
            ('x = a.inc == b.inc', False),
            ('x = a.inc == a.inc', True),
            ('x = counter.increment == incr', False),
            ('x = copy(counter.increment) == counter.increment', True),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_self_is_the_receiver_object(self):
        environment = self.run_source('x = counter.me()')
        self.assertIs(environment['x'], environment['counter'])

    def test_unbound_function_has_no_self(self):
        for source in ['incr()', 'f = function() { return self }; f()', 'fs = [incr]; fs[0]()']:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.run_source(source)

    def test_print(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.run_source('print(counter.increment)')
        self.assertEqual(output.getvalue(), '<function>\n')

    def test_failures(self):
        cases = [
            ('counter.increment(1)', TypeError),
            ('counter.add()', TypeError),
            ('counter.increment["parameters"]', TypeError),
            ('counter.increment.x = 1', TypeError),
            ('counter.increment + 1', TypeError),
            ('x = counter.name()', TypeError),
            ('x = counter.missing()', KeyError),
        ]
        for source, error in cases:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    self.run_source(source)

    def test_evaluation_status(self):
        result, _ = evaluate_source(PRELUDE + 'o = {"f": function() { exit(4) }}; o.f()', {})
        self.assertEqual(result, (4, 'exit'))
        result, _ = evaluate_source(PRELUDE + 'counter.add(quit())', {})
        self.assertEqual(result, (3, 'exit'))


if __name__ == '__main__':
    unittest.main()
