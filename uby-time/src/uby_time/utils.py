from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, localcontext


def to_decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def decimal_to_plain_text(value: Decimal) -> str:
    """Return a non-scientific Decimal string without thousands separators."""
    if value == value.to_integral():
        return format(value, "f")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def iso_to_datetime_utc(iso_time: str) -> datetime:
    text = iso_time.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def datetime_to_jd(dt: datetime) -> Decimal:
    """Convert UTC datetime to Julian Date using Unix epoch JD.

    This is sufficient for UBY reference-level labeling in the level-1 range.
    For leap-second-sensitive work, callers should use astropy.
    """
    timestamp = Decimal(str(dt.timestamp()))
    return Decimal("2440587.5") + timestamp / Decimal("86400")


def jd_to_datetime(jd: Decimal) -> datetime:
    seconds = (jd - Decimal("2440587.5")) * Decimal("86400")
    return datetime.fromtimestamp(float(seconds), tz=timezone.utc)


def floor_decimal(value: Decimal) -> Decimal:
    return value.to_integral_value(rounding=ROUND_FLOOR)


def quantize_decimal(value: Decimal, places: int) -> Decimal:
    if places < 0:
        raise ValueError("decimal places must be non-negative")
    quantum = Decimal("1") if places == 0 else Decimal("1").scaleb(-places)
    with localcontext() as ctx:
        ctx.prec = max(28, len(str(value).replace(".", "").replace("-", "")) + places + 2)
        return value.quantize(quantum)
