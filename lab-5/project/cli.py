"""Консольный интерфейс конвертера длин."""
import argparse

from converter import LengthConverter


def build_parser():
    parser = argparse.ArgumentParser(description='Конвертер единиц длины')
    parser.add_argument('value', nargs='?', help='десятичное число')
    parser.add_argument('source', nargs='?', help='исходная единица')
    parser.add_argument('target', nargs='?', help='целевая единица')
    parser.add_argument('--places', type=int, default=2, help='знаков после точки: 0–8 (по умолчанию 2)')
    parser.add_argument('--units', action='store_true', help='список кодов и коэффициентов в метрах')
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.units:
        if any(v is not None for v in (args.value, args.source, args.target)):
            parser.error('--units нельзя сочетать с позиционными аргументами')
        for code, factor in LengthConverter.FACTORS.items():
            print(f'{code}\t{factor}')
        return 0
    if any(v is None for v in (args.value, args.source, args.target)):
        parser.error('нужны три аргумента: число, исходная и целевая единицы')
    try:
        result = LengthConverter().convert(args.value, args.source, args.target, args.places)
    except ValueError as exc:
        parser.error(str(exc))
    print(f'{result:f} {args.target}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
