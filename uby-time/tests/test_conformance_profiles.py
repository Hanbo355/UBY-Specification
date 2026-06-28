from __future__ import annotations

from decimal import Decimal

from uby_time import (
    PrecisionLevel,
    UBYTime,
    WD_0_1_0_PROFILE,
    get_precision_definition,
    is_conformant,
    iso_to_uby,
    validate_conformance_profile,
)


def _level2_record(**overrides: object) -> UBYTime:
    base = UBYTime(
        uby_value=Decimal("13346200000.0"),
        uby_version="0.1.0",
        model_version="LCDM-Planck2018",
        precision_level=PrecisionLevel.LEVEL_2,
        source_time="440.8 Ma BP",
        source_system="ICS geologic age Ma before present; representative=boundary estimate",
        rounding_rule="year-floor",
        generated_by="uby-time/0.1.0",
        anchor_id="UBY-ANCHOR-2026-01-01Z",
        anchor_jd=Decimal("2461041.5"),
        anchor_uby=Decimal("13787002026.0"),
        uncertainty_years=Decimal("1200000"),
        interval_start_uby=Decimal("13345000000.0"),
        interval_end_uby=Decimal("13347400000.0"),
        uncertainty_kind="measurement",
        propagation_note="Representative UBY value derived from ICS Ma BP boundary estimate.",
    )
    values = {**base.__dict__, **overrides}
    return UBYTime(**values)


def _level3_record(**overrides: object) -> UBYTime:
    base = UBYTime(
        uby_value=Decimal("380000"),
        uby_version="0.1.0",
        model_version="LCDM-Planck2018",
        precision_level=PrecisionLevel.LEVEL_3,
        source_time="z≈1100",
        source_system="CosmologicalRedshift",
        rounding_rule="significant-digits:2",
        generated_by="uby-time/0.1.0",
        anchor_id="UBY-ANCHOR-2026-01-01Z",
        anchor_jd=Decimal("2461041.5"),
        anchor_uby=Decimal("13787002026.0"),
        uncertainty_years=Decimal("20000"),
        uncertainty_kind="model",
        propagation_note="Derived from redshift using LCDM-Planck2018 parameters.",
    )
    values = {**base.__dict__, **overrides}
    return UBYTime(**values)


def test_wd_profile_formalizes_all_three_precision_levels() -> None:
    profile = WD_0_1_0_PROFILE

    assert profile.profile_id == "UBY-WD-0.1.0-Core-Conformance"
    assert profile.spec_version == "0.1.0"
    assert [definition.level for definition in profile.precision_levels] == [
        PrecisionLevel.LEVEL_1,
        PrecisionLevel.LEVEL_2,
        PrecisionLevel.LEVEL_3,
    ]

    level1 = get_precision_definition(PrecisionLevel.LEVEL_1)
    level2 = get_precision_definition("Level 2")
    level3 = get_precision_definition(PrecisionLevel.LEVEL_3)

    assert level1.default_range_years == "1000000"
    assert level1.requires_model_version is False
    assert level2.requires_model_version is True
    assert level2.requires_uncertainty_or_interval is True
    assert level3.requires_model_version is True
    assert level3.requires_model_dependency_metadata is True


def test_profile_declares_uncertainty_interval_provenance_model_and_anchor_contracts() -> None:
    profile = WD_0_1_0_PROFILE

    assert "measurement" in profile.uncertainty_schema.allowed_kinds
    assert "temporal_resolution" in profile.uncertainty_schema.allowed_kinds
    assert profile.uncertainty_schema.confidence_level_range == ("0", "1")
    assert "MUST NOT be interpreted as zero" in profile.uncertainty_schema.missing_uncertainty_rule

    assert profile.interval_representation.start_field == "interval_start_uby"
    assert profile.interval_representation.end_field == "interval_end_uby"
    assert profile.interval_representation.interpretation == "closed"

    assert "source_time" in profile.provenance_model.required_fields
    assert "source_system" in profile.provenance_model.required_fields
    assert "generated_by" in profile.provenance_model.required_fields

    assert PrecisionLevel.LEVEL_2 in profile.model_dependency_metadata.required_for_levels
    assert PrecisionLevel.LEVEL_3 in profile.model_dependency_metadata.required_for_levels
    assert profile.model_dependency_metadata.required_fields == ("model_version",)

    assert profile.anchor_version_compatibility.default_anchor_iso == "2026-01-01T00:00:00Z"
    assert profile.anchor_version_compatibility.current_spec_version == "0.1.0"
    assert profile.anchor_version_compatibility.required_anchor_fields == ("anchor_id", "anchor_jd", "anchor_uby")


def test_level1_iso_record_conforms_to_core_profile() -> None:
    uby = iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False)

    messages = validate_conformance_profile(uby)

    assert messages == []
    assert is_conformant(uby) is True


def test_level2_record_requires_model_version_and_prefers_uncertainty_or_interval() -> None:
    valid = _level2_record()
    assert validate_conformance_profile(valid) == []
    assert is_conformant(valid) is True

    missing_model = _level2_record(model_version=None)
    missing_model_codes = {message.code for message in validate_conformance_profile(missing_model)}
    assert "MODEL_DEPENDENCY_METADATA_REQUIRED" in missing_model_codes
    assert "PRECISION_LEVEL_METADATA_REQUIRED" in missing_model_codes
    assert is_conformant(missing_model) is False

    missing_uncertainty = _level2_record(
        uncertainty_years=None,
        interval_start_uby=None,
        interval_end_uby=None,
    )
    messages = validate_conformance_profile(missing_uncertainty)
    assert [(message.code, message.level) for message in messages] == [
        ("UNCERTAINTY_OR_INTERVAL_RECOMMENDED", "warning")
    ]
    assert is_conformant(missing_uncertainty) is True


def test_interval_order_and_uncertainty_kind_are_checked() -> None:
    invalid_interval = _level2_record(
        interval_start_uby=Decimal("13347400000.0"),
        interval_end_uby=Decimal("13345000000.0"),
    )
    invalid_interval_codes = {message.code for message in validate_conformance_profile(invalid_interval)}
    assert "INTERVAL_ORDER_INVALID" in invalid_interval_codes
    assert is_conformant(invalid_interval) is False

    unknown_kind = _level2_record(uncertainty_kind="unsupported-kind")
    messages = validate_conformance_profile(unknown_kind)
    assert [(message.code, message.level) for message in messages] == [
        ("UNCERTAINTY_KIND_UNKNOWN", "warning")
    ]
    assert is_conformant(unknown_kind) is True


def test_level3_model_dependency_recommends_propagation_note_without_failing_conformance() -> None:
    valid = _level3_record()
    assert validate_conformance_profile(valid) == []

    missing_note = _level3_record(propagation_note=None)
    messages = validate_conformance_profile(missing_note)

    assert [(message.code, message.level) for message in messages] == [
        ("MODEL_PROPAGATION_NOTE_RECOMMENDED", "warning")
    ]
    assert is_conformant(missing_note) is True


def test_profile_detects_spec_version_mismatch_as_warning() -> None:
    uby = _level2_record(uby_version="0.0.9")
    messages = validate_conformance_profile(uby)

    assert [(message.code, message.level) for message in messages] == [
        ("PROFILE_SPEC_VERSION_MISMATCH", "warning")
    ]
    assert is_conformant(uby) is True
