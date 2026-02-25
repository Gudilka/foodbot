from __future__ import annotations

from decimal import Decimal, InvalidOperation


def parse_decimal_in_range(value: str, *, min_value: Decimal, max_value: Decimal, field_name: str) -> Decimal:
    raw = value.strip().replace(",", ".")
    try:
        parsed = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name}: ожидается число") from exc
    if parsed < min_value or parsed > max_value:
        raise ValueError(f"{field_name}: диапазон {min_value}..{max_value}")
    return parsed


def parse_int_in_range(value: str, *, min_value: int, max_value: int, field_name: str) -> int:
    raw = value.strip()
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name}: ожидается целое число") from exc
    if parsed < min_value or parsed > max_value:
        raise ValueError(f"{field_name}: диапазон {min_value}..{max_value}")
    return parsed


def parse_optional_decimal(value: str, *, min_value: Decimal, field_name: str) -> Decimal | None:
    raw = value.strip()
    if not raw or raw == "-":
        return None
    try:
        parsed = Decimal(raw.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name}: ожидается число или '-'") from exc
    if parsed < min_value:
        raise ValueError(f"{field_name}: значение должно быть >= {min_value}")
    return parsed
