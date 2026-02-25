from decimal import Decimal

import pytest

from bot.utils.validators import parse_decimal_in_range, parse_int_in_range, parse_optional_decimal


def test_parse_decimal_in_range_success() -> None:
    value = parse_decimal_in_range('1500', min_value=Decimal('500'), max_value=Decimal('100000'), field_name='Budget')
    assert value == Decimal('1500')


def test_parse_decimal_in_range_error() -> None:
    with pytest.raises(ValueError):
        parse_decimal_in_range('12', min_value=Decimal('500'), max_value=Decimal('100000'), field_name='Budget')


def test_parse_int_in_range_success() -> None:
    assert parse_int_in_range('3', min_value=1, max_value=5, field_name='Skill') == 3


def test_parse_optional_decimal_dash() -> None:
    assert parse_optional_decimal('-', min_value=Decimal('0'), field_name='Kcal') is None
