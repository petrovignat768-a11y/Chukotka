import subprocess
import sys
import unittest
from decimal import Decimal, localcontext
from pathlib import Path

from converter import ConversionError, LengthConverter, UNIT_IN_METERS

ROOT = Path(__file__).resolve().parents[1]


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.converter = LengthConverter()

    def test_all_144_unit_pairs_round_trip(self):
        for source in UNIT_IN_METERS:
            for target in UNIT_IN_METERS:
                with self.subTest(source=source, target=target):
                    forward = self.converter.convert("1", source, target)
                    backward = self.converter.convert(str(forward), target, source)
                    self.assertLessEqual(abs(backward - Decimal("1")), Decimal("1e-45"))

    def test_reference_conversions(self):
        examples = [
            ("1", "in", "mm", "25.4"),
            ("1", "mi", "km", "1.609344"),
            ("1", "arshin", "in", "28"),
            ("1", "sazhen", "ft", "7"),
            ("1", "versta", "sazhen", "500"),
        ]
        for value, source, target, expected in examples:
            with self.subTest(source=source, target=target):
                self.assertEqual(self.converter.convert(value, source, target), Decimal(expected))

    def test_input_and_unit_whitespace_and_case(self):
        self.assertEqual(self.converter.convert("  +1.5  ", " M ", " CM "), Decimal("150"))

    def test_zero_and_bounds(self):
        for value in ("0", "-0", "1e-12", "1e12"):
            with self.subTest(value=value):
                self.converter.convert(value, "m", "m")

    def test_errors_have_stable_codes(self):
        examples = [
            ("-1", "m", "m", "negative"),
            ("1e-13", "m", "m", "out_of_range"),
            ("1000000000001", "m", "m", "out_of_range"),
            ("NaN", "m", "m", "invalid_number"),
            ("1,5", "m", "m", "invalid_number"),
            ("", "m", "m", "invalid_number"),
            ("1", "m", "unknown", "unknown_unit"),
            ("1", "unknown", "m", "unknown_unit"),
        ]
        for value, source, target, code in examples:
            with self.subTest(value=value, source=source, target=target):
                with self.assertRaises(ConversionError) as raised:
                    self.converter.convert(value, source, target)
                self.assertEqual(raised.exception.code, code)

    def test_non_string_and_too_long_input_rejected(self):
        for value in (1, None, "1" * 129):
            with self.subTest(value=value):
                with self.assertRaises(ConversionError) as raised:
                    self.converter.convert(value, "m", "m")
                self.assertEqual(raised.exception.code, "invalid_number")
        with self.assertRaises(ConversionError) as raised:
            self.converter.convert("1", None, "m")
        self.assertEqual(raised.exception.code, "unknown_unit")

    def test_internal_precision_does_not_depend_on_caller_precision(self):
        with localcontext() as ctx:
            ctx.prec = 6
            actual = self.converter.convert("1", "m", "ft")
        self.assertTrue(str(actual).startswith("3.280839895013123"), actual)

    def test_unit_mapping_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            UNIT_IN_METERS["m"] = Decimal("7")


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "converter.py"), *args],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )

    def test_success(self):
        result = self.run_cli("2", "arshin", "m")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "1.4224 m")
        self.assertEqual(result.stderr, "")

    def test_invalid_input(self):
        result = self.run_cli("--", "-1", "m", "ft")
        self.assertEqual(result.returncode, 2)
        self.assertIn("negative", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_list(self):
        result = self.run_cli("--list")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout.splitlines()), 12)
        self.assertIn("versta", result.stdout)

    def test_missing_arguments(self):
        result = self.run_cli("1", "m")
        self.assertEqual(result.returncode, 2)
        self.assertIn("укажите значение", result.stderr)

    def test_list_cannot_be_combined_with_conversion(self):
        result = self.run_cli("--list", "1", "m", "ft")
        self.assertEqual(result.returncode, 2)
        self.assertIn("нельзя сочетать", result.stderr)


if __name__ == "__main__":
    unittest.main()
