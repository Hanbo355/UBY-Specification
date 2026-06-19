"""Root-level smoke checks for core uby-time functionality.

This script is intentionally kept outside the default pytest testpaths.  Run it
manually with:

    python test_functionality.py
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from uby_time import (  # noqa: E402
    PrecisionLevel,
    astronomical_year_to_uby,
    format_academic_mnemonic,
    format_full,
    format_magnitude,
    iso_to_uby,
    jd_to_uby,
    parse_uby_expression,
    uby_to_jd,
    validate_uby_time,
)


def test_anchor_iso_conversion() -> None:
    uby = iso_to_uby("2026-01-01T00:00:00Z")
    assert uby.uby_value == Decimal("13787002026.0")
    assert uby.precision_level == PrecisionLevel.LEVEL_1
    assert format_full(uby) == "UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]"


def test_jd_roundtrip() -> None:
    uby = jd_to_uby("2461041.5")
    assert uby.uby_value == Decimal("13787002026.0")
    assert uby_to_jd(uby.uby_value) == Decimal("2461041.500")


def test_year_and_mnemonic() -> None:
    uby = astronomical_year_to_uby(-220)
    assert uby.uby_value == Decimal("13786999780")
    assert format_academic_mnemonic(-220) == "UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]"


def test_parse_and_validate() -> None:
    parsed = parse_uby_expression("UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]")
    assert parsed.uby_value == Decimal("380000")
    assert parsed.notation == "magnitude"

    messages = validate_uby_time(jd_to_uby("2461041.5"))
    assert messages == []


def test_magnitude_format() -> None:
    uby = parse_uby_expression("UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]")
    from uby_time import UBYTime  # imported lazily for script readability

    uby_time = UBYTime(
        uby_value=uby.uby_value,
        uby_version=uby.uby_version or "0.1.0",
        model_version=uby.model_version,
        precision_level=uby.precision_level or PrecisionLevel.LEVEL_2,
        source_time=uby.raw,
        source_system="UBYExpression",
        rounding_rule="year-floor",
        generated_by="uby-time/0.1.0",
        anchor_id="UBY-ANCHOR-2026-01-01Z",
        anchor_jd=Decimal("2461041.5"),
        anchor_uby=Decimal("13787002026.0"),
    )
    assert format_magnitude(uby_time) == "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"


if __name__ == "__main__":
    test_anchor_iso_conversion()
    test_jd_roundtrip()
    test_year_and_mnemonic()
    test_parse_and_validate()
    test_magnitude_format()
    print("test_functionality.py: ok")
