from __future__ import annotations

from decimal import Decimal, localcontext

from .anchors import DEFAULT_ANCHOR
from .constants import (
    DEFAULT_MODEL_VERSION,
    DEFAULT_MNEMONIC_PREFIX,
    DEFAULT_ROUNDING_RULE,
    GENERATED_BY,
    JULIAN_YEAR_DAYS,
    UBY_SPEC_VERSION,
)
from .models import PrecisionLevel, UBYAnchor, UBYTime
from .utils import datetime_to_jd, iso_to_datetime_utc, jd_to_datetime, to_decimal


def _iso_to_jd_with_optional_astropy(iso_time: str, *, scale: str = "utc") -> tuple[Decimal, str]:
    """Convert ISO time to JD.

    Prefer astropy when available because it provides better astronomical time handling.
    Fall back to the standard-library implementation for the minimum dependency profile.
    """
    try:
        from astropy.time import Time  # type: ignore
    except Exception:
        dt = iso_to_datetime_utc(iso_time)
        return datetime_to_jd(dt), "stdlib-datetime"

    time = Time(iso_time, scale=scale)
    return Decimal(str(time.jd)), "astropy.time.Time"


def _jd_to_iso_with_optional_astropy(jd: Decimal, *, scale: str = "utc") -> tuple[str, str]:
    """Convert JD to ISO time.

    Prefer astropy when available. Fall back to the standard-library implementation.
    """
    try:
        from astropy.time import Time  # type: ignore
    except Exception:
        dt = jd_to_datetime(jd)
        return dt.isoformat().replace("+00:00", "Z"), "stdlib-datetime"

    time = Time(float(jd), format="jd", scale=scale)
    return time.isot + "Z", "astropy.time.Time"


def jd_to_uby(
    jd: Decimal | float | str,
    *,
    anchor: UBYAnchor = DEFAULT_ANCHOR,
    model_version: str = DEFAULT_MODEL_VERSION,
    uby_version: str = UBY_SPEC_VERSION,
    rounding_rule: str = DEFAULT_ROUNDING_RULE,
    source_time: str | None = None,
    source_system: str | None = "JD",
) -> UBYTime:
    jd_dec = to_decimal(jd)
    # Use a fixed local precision for reference-level interoperability.
    # This prevents callers or tests that change the global Decimal context from
    # changing canonical UBY strings for the same JD input.
    with localcontext() as ctx:
        ctx.prec = 28
        uby_value = (jd_dec - anchor.anchor_jd) / JULIAN_YEAR_DAYS + anchor.anchor_uby
    return UBYTime(
        uby_value=uby_value,
        uby_version=uby_version,
        model_version=model_version,
        precision_level=PrecisionLevel.LEVEL_1,
        source_time=source_time if source_time is not None else str(jd),
        source_system=source_system,
        rounding_rule=rounding_rule,
        generated_by=GENERATED_BY,
        anchor_id=anchor.anchor_id,
        anchor_jd=anchor.anchor_jd,
        anchor_uby=anchor.anchor_uby,
    )


def uby_to_jd(
    uby_value: Decimal | float | str,
    *,
    anchor: UBYAnchor = DEFAULT_ANCHOR,
) -> Decimal:
    value = to_decimal(uby_value)
    return (value - anchor.anchor_uby) * JULIAN_YEAR_DAYS + anchor.anchor_jd


def iso_to_uby(
    iso_time: str,
    *,
    anchor: UBYAnchor = DEFAULT_ANCHOR,
    model_version: str = DEFAULT_MODEL_VERSION,
    uby_version: str = UBY_SPEC_VERSION,
    rounding_rule: str = DEFAULT_ROUNDING_RULE,
    source_system: str = "UTC/ISO8601",
    scale: str = "utc",
    prefer_astropy: bool = True,
) -> UBYTime:
    if prefer_astropy:
        jd, converter = _iso_to_jd_with_optional_astropy(iso_time, scale=scale)
    else:
        dt = iso_to_datetime_utc(iso_time)
        jd, converter = datetime_to_jd(dt), "stdlib-datetime"

    uby = jd_to_uby(
        jd,
        anchor=anchor,
        model_version=model_version,
        uby_version=uby_version,
        rounding_rule=rounding_rule,
        source_time=iso_time,
        source_system=source_system,
    )

    return UBYTime(
        **{
            **uby.__dict__,
            "propagation_note": (
                f"iso_to_uby converter={converter}; "
                "stdlib fallback is not intended for leap-second-sensitive timing"
            ),
        }
    )


def uby_to_iso(
    uby_value: Decimal | float | str,
    *,
    anchor: UBYAnchor = DEFAULT_ANCHOR,
    scale: str = "utc",
    prefer_astropy: bool = True,
) -> str:
    jd = uby_to_jd(uby_value, anchor=anchor)
    if prefer_astropy:
        iso, _converter = _jd_to_iso_with_optional_astropy(jd, scale=scale)
        return iso

    dt = jd_to_datetime(jd)
    return dt.isoformat().replace("+00:00", "Z")


def astronomical_year_to_uby(
    year: int,
    *,
    mnemonic_prefix: int = DEFAULT_MNEMONIC_PREFIX,
    model_version: str | None = DEFAULT_MODEL_VERSION,
    include_model: bool = False,
    uby_version: str = UBY_SPEC_VERSION,
    rounding_rule: str = DEFAULT_ROUNDING_RULE,
) -> UBYTime:
    base = Decimal(mnemonic_prefix) * Decimal("100000")
    value = base + Decimal(year)
    return UBYTime(
        uby_value=value,
        uby_version=uby_version,
        model_version=model_version if include_model else None,
        precision_level=PrecisionLevel.LEVEL_1,
        source_time=str(year),
        source_system="AstronomicalYear",
        rounding_rule=rounding_rule,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )


def bc_year_to_astronomical_year(bc_year: int) -> int:
    if bc_year <= 0:
        raise ValueError("BC year must be positive")
    return 1 - bc_year


def bc_year_to_uby(bc_year: int, **kwargs) -> UBYTime:
    return astronomical_year_to_uby(bc_year_to_astronomical_year(bc_year), **kwargs)
