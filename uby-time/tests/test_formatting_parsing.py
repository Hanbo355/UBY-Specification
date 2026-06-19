from decimal import Decimal

from uby_time import (
    format_full,
    format_magnitude,
    format_scientific,
    jd_to_uby,
    parse_uby_expression,
)


def test_format_full():
    uby = jd_to_uby("2461041.5")
    assert format_full(uby) == "UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]"


def test_format_magnitude():
    parsed = parse_uby_expression("UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]")
    from uby_time.models import UBYTime, PrecisionLevel
    from uby_time.anchors import DEFAULT_ANCHOR
    from uby_time.constants import DEFAULT_ROUNDING_RULE, GENERATED_BY

    uby = UBYTime(
        uby_value=parsed.uby_value,
        uby_version=parsed.uby_version,
        model_version=parsed.model_version,
        precision_level=PrecisionLevel.LEVEL_3,
        source_time=None,
        source_system=None,
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )
    assert format_magnitude(uby) == "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"


def test_parse_magnitude():
    parsed = parse_uby_expression("UBY 13.787G [model=LCDM-Planck2018] [spec=0.1.0]")
    assert parsed.uby_value == Decimal("13787000000.000")


def test_parse_mnemonic():
    parsed = parse_uby_expression("UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]")
    assert parsed.uby_value == Decimal("13786999780")


def test_format_scientific():
    uby = jd_to_uby("2461041.5")
    assert "×10^" in format_scientific(uby)
