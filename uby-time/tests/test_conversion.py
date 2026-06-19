from decimal import Decimal

from uby_time import (
    astronomical_year_to_uby,
    bc_year_to_astronomical_year,
    format_academic_mnemonic,
    iso_to_uby,
    jd_to_uby,
    uby_to_jd,
)


def test_anchor_iso_to_uby():
    uby = iso_to_uby("2026-01-01T00:00:00Z")
    assert str(uby.uby_value) == "13787002026.0"


def test_anchor_jd_to_uby():
    uby = jd_to_uby("2461041.5")
    assert str(uby.uby_value) == "13787002026.0"


def test_jd_roundtrip():
    uby = jd_to_uby("2461041.5")
    assert uby_to_jd(uby.uby_value) == Decimal("2461041.5")


def test_astronomical_year_1():
    uby = astronomical_year_to_uby(1)
    assert str(uby.uby_value) == "13787000001"


def test_bc_221():
    assert bc_year_to_astronomical_year(221) == -220
    assert format_academic_mnemonic(-220) == "UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]"
