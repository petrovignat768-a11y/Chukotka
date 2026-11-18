"""Преобразование длины; значения передаются как десятичные строки."""
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP, localcontext
import re
from types import MappingProxyType

# Для 64-символьного ввода и заявленных коэффициентов с запасом.
WORKING_PRECISION = 128


class LengthConverter:
    # Коэффициенты: сколько метров в одной единице.
    FACTORS = MappingProxyType({
        'mm': Decimal('0.001'), 'cm': Decimal('0.01'),
        'm': Decimal('1'), 'km': Decimal('1000'),
        'in': Decimal('0.0254'), 'ft': Decimal('0.3048'),
        'yd': Decimal('0.9144'), 'mi': Decimal('1609.344'),
        'vershok': Decimal('0.04445'), 'arshin': Decimal('0.7112'),
        'sazhen': Decimal('2.1336'), 'verst': Decimal('1066.8'),
    })

    def _validate(self, value, source, target, places):
        if type(places) is not int or not 0 <= places <= 8:
            raise ValueError('Точность должна быть целым числом от 0 до 8')
        if not isinstance(source, str) or source not in self.FACTORS:
            raise ValueError('Неизвестная исходная единица')
        if not isinstance(target, str) or target not in self.FACTORS:
            raise ValueError('Неизвестная целевая единица')
        if (not isinstance(value, str) or len(value) > 64 or
            not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', value)):
            raise ValueError('Число должно быть десятичной строкой длиной до 64 символов')
        try:
            amount = Decimal(value)
        except DecimalException as exc:
            raise ValueError('Недопустимое число') from exc
        if not amount.is_finite() or amount.copy_abs() > Decimal('1000000000000'):
            raise ValueError('Модуль числа не должен превышать 1000000000000')
        return amount

    def convert(self, value, source, target, places=2):
        amount = self._validate(value, source, target, places)
        try:
            with localcontext(Context(prec=WORKING_PRECISION, rounding=ROUND_HALF_UP)):
                result = amount * self.FACTORS[source] / self.FACTORS[target]
                rounded = result.quantize(Decimal('1').scaleb(-places))
                return rounded.copy_abs() if rounded.is_zero() else rounded
        except DecimalException as exc:
            raise ValueError('Невозможно преобразовать это число') from exc
