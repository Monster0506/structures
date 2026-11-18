import contextlib
import io
import unittest

import evaluator


PRELUDE = 'items=[10, 20, 30]; text="abc"; '


class NegativeIndexingTests(unittest.TestCase):
    def run_source(self, source):
        _, environment = evaluator.evaluate_source(PRELUDE + source, {})
        return environment

    def test_negative_reads(self):
        cases = [
            ('x=items[-1]', 30),
            ('x=items[-3]', 10),
            ('x=items[-length(items)]', 10),
            ('x=text[-1]', 'c'),
            ('x=text[-length(text)]', 'a'),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['x'], expected)

    def test_negative_list_writes(self):
        cases = [
            ('items[-2]=7', [10, 7, 30]),
            ('items[-1]=0', [10, 20, 0]),
            ('items[-length(items)]=1', [1, 20, 30]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(self.run_source(source)['items'], expected)

    def test_slide_example(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            env = self.run_source('print(items[-1]); items[-2] = 7;')
        self.assertEqual(output.getvalue(), '30\n')
        self.assertEqual(env['items'], [10, 7, 30])

    def test_out_of_range_negative_rejected(self):
        cases = [
            'x=items[-4]',
            'x=text[-4]',
            'items[-4]=1',
            'x=[][-1]',
            'x=""[-1]',
            'e=[]; e[-1]=1',
        ]
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaisesRegex(IndexError, 'Index out of range'):
                    self.run_source(source)

    def test_failed_write_leaves_list_unchanged(self):
        env = {}
        with self.assertRaises(IndexError):
            evaluator.evaluate_source(PRELUDE + 'items[-4]=1', env)
        self.assertEqual(env['items'], [10, 20, 30])


if __name__ == '__main__':
    unittest.main()
