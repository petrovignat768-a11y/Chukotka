from decimal import Decimal

from behave import given, then, use_step_matcher, when

from converter import ConversionError, LengthConverter

use_step_matcher("re")


@given(r'исходное значение "(?P<value>.*)"')
def enter_value(context, value):
    context.value = value
    context.converter = LengthConverter()
    context.result = None
    context.error = None


@given(r'единицы измерения "(?P<source>.*)" и "(?P<target>.*)"')
def select_units(context, source, target):
    context.source = source
    context.target = target


@when(r'выполняется конвертация')
def convert(context):
    try:
        context.result = context.converter.convert(context.value, context.source, context.target)
    except ConversionError as exc:
        context.error = exc


@when(r'величина переводится в целевую единицу и обратно')
def round_trip(context):
    try:
        intermediate = context.converter.convert(context.value, context.source, context.target)
        context.result = context.converter.convert(str(intermediate), context.target, context.source)
    except ConversionError as exc:
        context.error = exc


@then(r'результат равен "(?P<expected>.*)" с точностью "(?P<tolerance>.*)"')
def result_equals(context, expected, tolerance):
    if context.error is not None:
        raise AssertionError(f"Неожиданная ошибка: {context.error.code}: {context.error}")
    if context.result is None:
        raise AssertionError("Результат конвертации отсутствует")
    difference = abs(context.result - Decimal(expected))
    if difference > Decimal(tolerance):
        raise AssertionError(f"получено {context.result}, ожидалось {expected}, погрешность {difference}")


@then(r'ошибка имеет код "(?P<error>.*)"')
def error_equals(context, error):
    if context.error is None:
        raise AssertionError(f"Ожидалась ошибка {error}, получено {context.result}")
    if context.error.code != error:
        raise AssertionError(f"Получена ошибка {context.error.code}, ожидалась {error}")
