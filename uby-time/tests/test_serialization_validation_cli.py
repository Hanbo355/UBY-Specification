import json
from decimal import Decimal

import pytest

from uby_time import (
    DEFAULT_ANCHOR,
    PrecisionLevel,
    UBYTime,
    format_friendly_mnemonic,
    from_json,
    infer_precision_level,
    iso_to_uby,
    parse_uby_expression,
    to_json,
    validate_uby_time,
)
from uby_time.cli import main
from uby_time.constants import DEFAULT_ROUNDING_RULE, GENERATED_BY
from uby_time.errors import UBYParseError


def test_json_roundtrip_preserves_decimal_strings():
    uby = iso_to_uby("2026-01-01T00:00:00Z")
    text = to_json(uby)
    assert '"uby_value": "13787002026.0"' in text
    restored = from_json(text)
    assert restored.uby_value == Decimal("13787002026.0")


def test_mnemonic_model_mismatch_warning():
    parsed = parse_uby_expression("UBY 137720+002026 [model=LCDM-Planck2018] [spec=0.1.0]")
    assert "MNEMONIC_MODEL_MISMATCH" in parsed.warnings
    assert parsed.mnemonic_prefix == 137720


def test_missing_spec_warning():
    parsed = parse_uby_expression("UBY 380K [model=LCDM-Planck2018]")
    assert "SPEC_VERSION_UNDECLARED" in parsed.warnings


def test_missing_model_warning_for_magnitude():
    parsed = parse_uby_expression("UBY 380K [spec=0.1.0]")
    assert "MODEL_VERSION_REQUIRED" in parsed.warnings


def test_friendly_mnemonic_format_and_parse():
    label = format_friendly_mnemonic(221, era="BC")
    parsed = parse_uby_expression(label)
    assert parsed.uby_value == Decimal("13786999780")


def test_scientific_ascii_x_parse():
    parsed = parse_uby_expression("UBY 3.8x10^5 [model=LCDM-Planck2018] [spec=0.1.0]")
    assert parsed.uby_value == Decimal("380000.0")


def test_multi_component_model_tag_parse():
    parsed = parse_uby_expression("UBY 1.0×10^12 [model=Scenario-FutureA] [spec=0.1.0]")
    assert parsed.model_version == "Scenario-FutureA"


def test_infer_precision_level_redshift_context():
    level = infer_precision_level(
        Decimal("380000"),
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
        source_system="CosmologicalRedshift",
        model_version="LCDM-Planck2018",
    )
    assert level == PrecisionLevel.LEVEL_3


def test_validation_requires_model_for_level_3():
    uby = UBYTime(
        uby_value=Decimal("380000"),
        uby_version="0.1.0",
        model_version=None,
        precision_level=PrecisionLevel.LEVEL_3,
        source_time=None,
        source_system=None,
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )
    messages = validate_uby_time(uby)
    assert any(message.code == "MODEL_REQUIRED_FOR_LEVEL_2_3" for message in messages)


def test_cli_convert_year(capsys):
    assert main(["convert", "year", "2026"]) == 0
    output = capsys.readouterr().out
    assert "UBY 13787002026 [spec=0.1.0]" in output
    assert "academic_mnemonic=UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]" in output


def test_cli_parse_json(capsys):
    assert main(["parse", "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]", "--format", "json"]) == 0
    output = capsys.readouterr().out
    assert '"notation": "magnitude"' in output
    assert '"uby_value": "380000"' in output


def test_cli_format_magnitude(capsys):
    assert main(["format", "magnitude", "UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]"]) == 0
    output = capsys.readouterr().out.strip()
    assert output == "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"


def test_parser_rejects_invalid_expression():
    with pytest.raises(UBYParseError):
        parse_uby_expression("UBY not-a-valid-expression [spec=0.1.0]")


def test_parser_rejects_reversed_tag_order():
    with pytest.raises(UBYParseError):
        parse_uby_expression("UBY 380K [spec=0.1.0] [model=LCDM-Planck2018]")


def test_parser_full_numeric_without_spec_warns():
    parsed = parse_uby_expression("UBY 13787002026.0 [model=LCDM-Planck2018]")
    assert parsed.notation == "full-numeric"
    assert parsed.uby_value == Decimal("13787002026.0")
    assert parsed.warnings == ["SPEC_VERSION_UNDECLARED"]


def test_cli_convert_jd_json(capsys):
    assert main(["convert", "jd", "2461041.5", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["uby_value"] == "13787002026.0"
    assert payload["model_version"] == "LCDM-Planck2018"
    assert payload["uby_version"] == "0.1.0"
    assert payload["precision_level"] == "Level 1"


def test_cli_convert_bc_with_model_and_no_spec(capsys):
    assert main(["convert", "bc", "221", "--include-model", "--no-spec"]) == 0
    output = capsys.readouterr().out
    assert "UBY 13786999780 [model=LCDM-Planck2018]" in output
    assert "[spec=0.1.0]" not in output
    assert "academic_mnemonic=UBY 137870-000220 [model=LCDM-Planck2018]" in output


def test_cli_validate_includes_parser_warnings(capsys):
    assert main(["validate", "UBY 380K [spec=0.1.0]"]) == 0
    output = capsys.readouterr().out
    assert "error:MODEL_REQUIRED_FOR_LEVEL_2_3:" in output
    assert "warning:MODEL_VERSION_REQUIRED:MODEL_VERSION_REQUIRED" in output
    assert "warning:MAGNITUDE_NOT_FOR_STORAGE:MAGNITUDE_NOT_FOR_STORAGE" in output


def test_cli_validate_json_ok_for_full_numeric(capsys):
    assert main(["validate", "UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == []


def test_cli_format_scientific_with_digit_option(capsys):
    assert main(["format", "scientific", "UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]", "--digits", "4"]) == 0
    output = capsys.readouterr().out.strip()
    assert output == "UBY 1.379×10^10 [model=LCDM-Planck2018] [spec=0.1.0]"


def test_validation_detects_anchor_version_mismatch():
    uby = UBYTime(
        uby_value=Decimal("13787002026.0"),
        uby_version="0.0.9",
        model_version="LCDM-Planck2018",
        precision_level=PrecisionLevel.LEVEL_1,
        source_time="2026-01-01T00:00:00Z",
        source_system="UTC/ISO8601",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )
    messages = validate_uby_time(uby)
    assert any(message.code == "ANCHOR_VERSION_MISMATCH" for message in messages)


def test_validation_warns_about_false_precision_with_large_uncertainty():
    uby = UBYTime(
        uby_value=Decimal("380000.123"),
        uby_version="0.1.0",
        model_version="LCDM-Planck2018",
        precision_level=PrecisionLevel.LEVEL_3,
        source_time="z=1100",
        source_system="CosmologicalRedshift",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
        uncertainty_years=Decimal("1000"),
        propagation_note="computed by astropy.cosmology.Planck18.age(z=1100)",
    )
    messages = validate_uby_time(uby)
    assert any(message.code == "FALSE_PRECISION_RISK" for message in messages)


def test_validation_detects_invalid_confidence_level():
    uby = iso_to_uby("2026-01-01T00:00:00Z").with_uncertainty(
        uncertainty_years=Decimal("1"),
        confidence_level=Decimal("1.5"),
    )
    messages = validate_uby_time(uby)
    assert any(message.code == "INVALID_CONFIDENCE_LEVEL" for message in messages)


def test_cli_convert_jd_csv(capsys):
    assert main(["convert", "jd", "2461041.5", "--format", "csv"]) == 0
    output = capsys.readouterr().out
    assert "uby_value,uby_version,model_version,precision_level" in output
    assert "13787002026.0,0.1.0,LCDM-Planck2018,Level 1" in output


def test_cli_validate_csv(capsys):
    assert main(["validate", "UBY 380K [spec=0.1.0]", "--format", "csv"]) == 0
    output = capsys.readouterr().out
    assert "code,level,message" in output
    assert "MODEL_REQUIRED_FOR_LEVEL_2_3,error" in output


def test_cli_reverse_jd(capsys):
    assert main(["reverse", "jd", "13787002026.0"]) == 0
    output = capsys.readouterr().out.strip()
    assert output == "2461041.500"
