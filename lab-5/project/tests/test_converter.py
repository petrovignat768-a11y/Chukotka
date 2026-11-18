import unittest
from decimal import Decimal

from converter import LengthConverter


class BasicMetricTests(unittest.TestCase):
    def setUp(self):
        self.converter = LengthConverter()

    def test_meters_to_centimeters(self):
        self.assertEqual(self.converter.convert('2.5', 'm', 'cm', 2), Decimal('250.00'))

    def test_centimeters_to_meters(self):
        self.assertEqual(self.converter.convert('125', 'cm', 'm', 2), Decimal('1.25'))


class UnitSystemTests(unittest.TestCase):
    def setUp(self):
        self.converter = LengthConverter()

    def test_si_millimeters_and_kilometers(self):
        self.assertEqual(self.converter.convert('3', 'km', 'mm', 0), Decimal('3000000'))

    def test_international_imperial_factors_in_meters(self):
        for unit, meters in [('in', '0.0254'), ('ft', '0.3048'),
                             ('yd', '0.9144'), ('mi', '1609.344')]:
            with self.subTest(unit=unit):
                self.assertEqual(self.converter.convert('1', unit, 'm', 8), Decimal(meters))

    def test_traditional_russian_factors_in_meters(self):
        for unit, meters in [('vershok', '0.04445'), ('arshin', '0.7112'),
                             ('sazhen', '2.1336'), ('verst', '1066.8')]:
            with self.subTest(unit=unit):
                self.assertEqual(self.converter.convert('1', unit, 'm', 8), Decimal(meters))

    def test_cross_system_conversion(self):
        self.assertEqual(self.converter.convert('1', 'sazhen', 'ft', 2), Decimal('7.00'))
        self.assertEqual(self.converter.convert('1', 'mi', 'km', 3), Decimal('1.609'))

    def test_identity_for_all_units(self):
        for unit in ('mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi',
                     'vershok', 'arshin', 'sazhen', 'verst'):
            with self.subTest(unit=unit):
                self.assertEqual(self.converter.convert('3.25', unit, unit, 2), Decimal('3.25'))


class ValidationAndRoundingTests(unittest.TestCase):
    def setUp(self):
        self.converter = LengthConverter()

    def test_half_up_positive_and_negative_ties(self):
        self.assertEqual(self.converter.convert('2.675', 'm', 'm', 2), Decimal('2.68'))
        self.assertEqual(self.converter.convert('-2.675', 'm', 'm', 2), Decimal('-2.68'))

    def test_rounding_zero_places(self):
        self.assertEqual(self.converter.convert('2.5', 'm', 'm', 0), Decimal('3'))
        self.assertEqual(self.converter.convert('-2.5', 'm', 'm', 0), Decimal('-3'))

    def test_rounding_eight_places_and_trailing_zeros(self):
        result = self.converter.convert('1', 'm', 'm', 8)
        self.assertEqual(str(result), '1.00000000')

    def test_small_negative_rounds_to_unsigned_zero(self):
        self.assertEqual(str(self.converter.convert('-0.001', 'm', 'm', 2)), '0.00')

    def test_zero_and_negative_are_valid(self):
        self.assertEqual(self.converter.convert('0', 'mi', 'm', 2), Decimal('0.00'))
        self.assertEqual(self.converter.convert('-2', 'ft', 'in', 2), Decimal('-24.00'))

    def test_range_inclusive_and_overflow(self):
        self.assertEqual(self.converter.convert('1000000000000', 'km', 'mm', 0),
                         Decimal('1000000000000000000'))
        self.assertEqual(self.converter.convert('-1000000000000', 'm', 'm', 0),
                         Decimal('-1000000000000'))
        for value in ('1000000000000.1', '-1000000000000.1'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.converter.convert(value, 'm', 'm')

    def test_invalid_places(self):
        for places in (-1, 9, 2.5, True, '2'):
            with self.subTest(places=places), self.assertRaises(ValueError):
                self.converter.convert('1', 'm', 'm', places)

    def test_unknown_or_wrong_case_units(self):
        for source, target in (('wrong', 'm'), ('m', 'wrong'), ('M', 'm'), ('', 'm')):
            with self.subTest(source=source, target=target), self.assertRaises(ValueError):
                self.converter.convert('1', source, target)

    def test_reject_nonfinite_and_invalid_number_strings(self):
        for value in ('NaN', 'Infinity', '-Infinity', 'abc', '1,2', '', ' 1 ', '1_0'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.converter.convert(value, 'm', 'm')

    def test_reject_nonstring_and_overlong_input(self):
        for value in (1.25, None, '0' * 65):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.converter.convert(value, 'm', 'm')

    def test_scientific_decimal_syntax(self):
        self.assertEqual(self.converter.convert('1.25e2', 'cm', 'm', 2), Decimal('1.25'))
        self.assertEqual(self.converter.convert('.5', 'm', 'cm', 0), Decimal('50'))


class PrecisionAndMatrixTests(unittest.TestCase):
    def test_all_unit_pairs_against_exact_rational_oracle(self):
        from fractions import Fraction

        factors = {
            'mm': '0.001', 'cm': '0.01', 'm': '1', 'km': '1000',
            'in': '0.0254', 'ft': '0.3048', 'yd': '0.9144', 'mi': '1609.344',
            'vershok': '0.04445', 'arshin': '0.7112', 'sazhen': '2.1336', 'verst': '1066.8',
        }
        converter = LengthConverter()
        for source, source_factor in factors.items():
            for target, target_factor in factors.items():
                # Независимый эталон на рациональных числах: округление от нуля.
                exact = Fraction('123.456') * Fraction(source_factor) / Fraction(target_factor)
                scaled = exact * 10**8
                whole, remainder = divmod(scaled.numerator, scaled.denominator)
                whole += (remainder * 2 >= scaled.denominator)
                expected = f'{whole // 10**8}.{whole % 10**8:08d}'
                with self.subTest(source=source, target=target):
                    self.assertEqual(str(converter.convert('123.456', source, target, 8)), expected)

    def test_external_decimal_context_does_not_change_results(self):
        from decimal import Inexact, localcontext

        with localcontext() as ctx:
            ctx.prec = 3
            ctx.Emax = 9
            ctx.traps[Inexact] = True
            self.assertEqual(LengthConverter().convert('1', 'mm', 'ft', 8), Decimal('0.00328084'))
            self.assertEqual(LengthConverter().convert('1000000000000', 'km', 'mm', 0),
                             Decimal('1000000000000000000'))
