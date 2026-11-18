import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'cli.py'


def run_cli(*args):
    return subprocess.run([sys.executable, '-B', str(CLI), *args], cwd=ROOT,
                          capture_output=True, text=True, encoding='utf-8', check=False)


class CliTests(unittest.TestCase):
    def test_successful_conversion_and_output_precision(self):
        result = run_cli('1', 'mi', 'km', '--places', '3')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '1.609 km\n')
        self.assertEqual(result.stderr, '')

    def test_default_precision_and_negative_number(self):
        result = run_cli('-2', 'ft', 'in')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '-24.00 in\n')

    def test_negative_scientific_number_after_double_dash(self):
        result = run_cli('--places', '2', '--', '-1e2', 'cm', 'm')
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '-1.00 m\n')

    def test_unit_list_matches_supported_codes(self):
        result = run_cli('--units')
        self.assertEqual(result.returncode, 0)
        lines = [line.split('\t') for line in result.stdout.splitlines()]
        self.assertTrue(all(len(line) == 2 for line in lines))
        self.assertEqual(len(lines), 12)
        self.assertEqual({line[0] for line in lines},
                         {'mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi',
                          'vershok', 'arshin', 'sazhen', 'verst'})
        self.assertEqual(dict(lines)['mi'], '1609.344')
        self.assertEqual(dict(lines)['verst'], '1066.8')

    def test_invalid_value_and_unit_exit_2_without_traceback(self):
        for args in [('NaN', 'm', 'cm'), ('1', 'bad', 'm'), ('1', 'm', 'bad')]:
            with self.subTest(args=args):
                result = run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertNotIn('Traceback', result.stderr)
                self.assertIn('error:', result.stderr)

    def test_invalid_precision_and_missing_arguments(self):
        for args in [('1', 'm', 'cm', '--places', '9'), ('1', 'm'), ()]:
            with self.subTest(args=args):
                result = run_cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stderr)

    def test_help_succeeds(self):
        result = run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('--units', result.stdout)
        self.assertIn('--places', result.stdout)
