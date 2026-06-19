from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .constants import (
    DEFAULT_MNEMONIC_PREFIX,
    DEFAULT_MODEL_VERSION,
    MAGNITUDE_FACTORS,
    UBY_SPEC_VERSION,
)
from .models import UBYTime
from .utils import decimal_to_plain_text, quantize_decimal


def _tags(model_version: str | None, uby_version: str | None, include_model: bool, include_spec: bool) -> str:
    parts: list[str] = []
    if include_model and model_version:
        parts.append(f"[model={model_version}]")
    if include_spec and uby_version:
        parts.append(f"[spec={uby_version}]")
    return (" " + " ".join(parts)) if parts else ""


def format_full(
    uby: UBYTime,
    *,
    include_model: bool = True,
    include_spec: bool = True,
    decimal_places: int | None = None,
) -> str:
    value = uby.uby_value if decimal_places is None else quantize_decimal(uby.uby_value, decimal_places)
    return f"UBY {decimal_to_plain_text(value)}{_tags(uby.model_version, uby.uby_version, include_model, include_spec)}"


def format_magnitude(
    uby: UBYTime,
    *,
    digits: int = 4,
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    value = abs(uby.uby_value)
    chosen_symbol = "K"
    for symbol in ("T", "G", "M", "K"):
        if value >= MAGNITUDE_FACTORS[symbol]:
            chosen_symbol = symbol
            break
    scaled = uby.uby_value / MAGNITUDE_FACTORS[chosen_symbol]
    if scaled == scaled.to_integral():
        text = decimal_to_plain_text(scaled)
    else:
        # significant-ish display for labels; not for storage
        quant = Decimal("1").scaleb(-(max(digits - 1, 0)))
        text = decimal_to_plain_text(scaled.quantize(quant, rounding=ROUND_HALF_UP))
    return f"UBY {text}{chosen_symbol}{_tags(uby.model_version, uby.uby_version, include_model, include_spec)}"


def format_scientific(
    uby: UBYTime,
    *,
    significant_digits: int = 3,
    multiplication_sign: str = "×",
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    value = uby.uby_value
    if value == 0:
        coeff = Decimal("0")
        exponent = 0
    else:
        adjusted = value.adjusted()
        exponent = adjusted
        coeff = value.scaleb(-exponent)
        places = max(significant_digits - 1, 0)
        coeff = quantize_decimal(coeff, places)
    return f"UBY {decimal_to_plain_text(coeff)}{multiplication_sign}10^{exponent}{_tags(uby.model_version, uby.uby_version, include_model, include_spec)}"


def format_academic_mnemonic(
    astronomical_year: int,
    *,
    mnemonic_prefix: int = DEFAULT_MNEMONIC_PREFIX,
    model_version: str = DEFAULT_MODEL_VERSION,
    uby_version: str = UBY_SPEC_VERSION,
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    if astronomical_year < -999999 or astronomical_year > 999999:
        raise ValueError("academic mnemonic supports astronomical years within ±999999")
    sign = "+" if astronomical_year >= 0 else "-"
    suffix = f"{abs(astronomical_year):06d}"
    return f"UBY {mnemonic_prefix:06d}{sign}{suffix}{_tags(model_version, uby_version, include_model, include_spec)}"


def format_friendly_mnemonic(
    year: int,
    *,
    era: str,
    mnemonic_prefix: int = DEFAULT_MNEMONIC_PREFIX,
    model_version: str = DEFAULT_MODEL_VERSION,
    uby_version: str = UBY_SPEC_VERSION,
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    era_norm = era.upper()
    if era_norm not in {"AD", "BC"}:
        raise ValueError("era must be AD or BC")
    if year <= 0:
        raise ValueError("friendly mnemonic year must be positive")
    return f"UBY {mnemonic_prefix:06d} {era_norm}{year}{_tags(model_version, uby_version, include_model, include_spec)}"
