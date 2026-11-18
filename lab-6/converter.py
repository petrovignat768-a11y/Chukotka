"""Учебный конвертер длины: десятичные коэффициенты относительно метра."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, localcontext
import re
import sys
from types import MappingProxyType


# Международные единицы США; для исторических мер выбраны стандартные
# соотношения XIX века, а не все исторически существовавшие варианты.
UNIT_IN_METERS = MappingProxyType({
    "mm": Decimal("0.001"),
    "cm": Decimal("0.01"),
    "m": Decimal("1"),
    "km": Decimal("1000"),
    "in": Decimal("0.0254"),
    "ft": Decimal("0.3048"),
    "yd": Decimal("0.9144"),
    "mi": Decimal("1609.344"),
    "vershok": Decimal("0.04445"),
    "arshin": Decimal("0.7112"),
    "sazhen": Decimal("2.1336"),
    "versta": Decimal("1066.8"),
})
MIN_POSITIVE = Decimal("1e-12")
MAX_VALUE = Decimal("1e12")
NUMBER_RE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


class ConversionError(ValueError):
    """Ошибка пользовательского ввода со стабильным машинным кодом."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class LengthConverter:
    """Перевод длины через метр без зависимости от пользовательского EXE."""

    @staticmethod
    def _number(value: str) -> Decimal:
        if not isinstance(value, str):
            raise ConversionError("invalid_number", "Значение должно быть десятичной строкой")
        text = value.strip()
        if len(text) > 128 or not NUMBER_RE.fullmatch(text):
            raise ConversionError("invalid_number", "Некорректное конечное десятичное число")
        try:
            number = Decimal(text)
        except InvalidOperation as exc:
            raise ConversionError("invalid_number", "Некорректное конечное десятичное число") from exc
        if not number.is_finite():
            raise ConversionError("invalid_number", "Число должно быть конечным")
        if number < 0:
            raise ConversionError("negative", "Длина не может быть отрицательной")
        if number > MAX_VALUE or (number != 0 and number < MIN_POSITIVE):
            raise ConversionError("out_of_range", "Разрешены ноль и значения от 1e-12 до 1e12 включительно")
        return number

    @staticmethod
    def _unit(unit: str) -> str:
        if not isinstance(unit, str) or unit.strip().lower() not in UNIT_IN_METERS:
            raise ConversionError("unknown_unit", f"Неизвестная единица измерения: {unit!r}")
        return unit.strip().lower()

    def convert(self, value: str, source: str, target: str) -> Decimal:
        """Вернуть длину в целевой единице; бросить ConversionError при ошибке."""
        number = self._number(value)
        source_key = self._unit(source)
        target_key = self._unit(target)
        with localcontext() as ctx:
            ctx.prec = 50
            return number * UNIT_IN_METERS[source_key] / UNIT_IN_METERS[target_key]


def _format_decimal(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Конвертер длины: единицы СИ, США и старорусские")
    parser.add_argument("value", nargs="?", help="десятичное значение; разделитель — точка")
    parser.add_argument("source", nargs="?", help="код исходной единицы")
    parser.add_argument("target", nargs="?", help="код целевой единицы")
    parser.add_argument("--list", action="store_true", help="показать коды единиц и их размеры в метрах")
    args = parser.parse_args(argv)
    if args.list:
        if any(x is not None for x in (args.value, args.source, args.target)):
            parser.error("--list нельзя сочетать с аргументами конвертации")
        for unit, meters in UNIT_IN_METERS.items():
            print(f"{unit:8} {_format_decimal(meters)} m")
        return 0
    if any(x is None for x in (args.value, args.source, args.target)):
        parser.error("укажите значение, исходную и целевую единицы или --list")
    try:
        result = LengthConverter().convert(args.value, args.source, args.target)
    except ConversionError as exc:
        print(f"Ошибка [{exc.code}]: {exc}", file=sys.stderr)
        return 2
    print(f"{_format_decimal(result)} {args.target.strip().lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
