from __future__ import annotations

from decimal import Decimal

from uby_time import (
    MODEL_DEPENDENCY_PROFILES,
    PLANCK2018_LCDM_PROFILE,
    STRICT_LEVEL3_LCDM_PROFILE,
    ModelParameter,
    PrecisionLevel,
    UBYTime,
    get_model_dependency_profile,
    model_dependency_profile_to_dict,
    validate_model_dependency,
)


def _level2_record(**overrides: object) -> UBYTime:
    base = UBYTime(
        uby_value=Decimal("13346200000.0"),
        uby_version="0.1.0",
        model_version="LCDM-Planck2018",
        precision_level=PrecisionLevel.LEVEL_2,
        source_time="440.8 Ma BP",
        source_system="ICS geologic age Ma before present",
        rounding_rule="year-floor",
        generated_by="uby-time/0.1.0",
        anchor_id="UBY-ANCHOR-2026-01-01Z",
        anchor_jd=Decimal("2461041.5"),
        anchor_uby=Decimal("13787002026.0"),
    )
    return UBYTime(**{**base.__dict__, **overrides})


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
        propagation_note="Derived from redshift using LCDM-Planck2018 parameters.",
    )
    return UBYTime(**{**base.__dict__, **overrides})


def test_model_dependency_profile_registry_and_serialization() -> None:
    assert get_model_dependency_profile("LCDM-Planck2018") is PLANCK2018_LCDM_PROFILE
    assert get_model_dependency_profile("LCDM-Planck2018:strict-level3") is STRICT_LEVEL3_LCDM_PROFILE
    assert set(MODEL_DEPENDENCY_PROFILES) == {"LCDM-Planck2018", "LCDM-Planck2018:strict-level3"}

    payload = model_dependency_profile_to_dict(STRICT_LEVEL3_LCDM_PROFILE)

    assert payload["model_version"] == "LCDM-Planck2018"
    assert payload["model_family"] == "LCDM"
    assert payload["applies_to_levels"] == ["Level 3"]
    assert payload["required_parameters"] == ["H0", "Om0"]
    assert "propagation_note" in payload["required_provenance_fields"]


def test_level2_default_model_metadata_accepts_model_version_with_recommendations() -> None:
    messages = validate_model_dependency(_level2_record(), profile=PLANCK2018_LCDM_PROFILE)

    assert {message.code for message in messages} == {"MODEL_PARAMETER_RECOMMENDED"}
    assert all(message.level == "warning" for message in messages)


def test_level3_strict_profile_requires_parameters() -> None:
    messages = validate_model_dependency(_level3_record(), profile=STRICT_LEVEL3_LCDM_PROFILE, strict=True)
    codes = [message.code for message in messages]

    assert codes.count("MODEL_PARAMETER_REQUIRED") == 2
    assert "MODEL_PARAMETERS_RECOMMENDED" in codes
    assert "MODEL_PROVENANCE_FIELD_REQUIRED" not in codes


def test_level3_strict_profile_accepts_numeric_parameters() -> None:
    parameters = {
        "H0": "67.66",
        "Om0": "0.30966",
        "Ode0": "0.6889",
        "Tcmb0": "2.7255",
        "Neff": "3.046",
        "m_nu": "0.06",
        "implementation": "astropy",
        "integration_method": "FLRW.age",
    }

    messages = validate_model_dependency(
        _level3_record(),
        profile=STRICT_LEVEL3_LCDM_PROFILE,
        parameters=parameters,
        strict=True,
    )

    assert messages == []


def test_model_parameter_tuple_input_and_numeric_validation() -> None:
    parameters = (
        ModelParameter(name="H0", value="not numeric", unit="km/s/Mpc"),
        ModelParameter(name="Om0", value="0.30966"),
    )

    messages = validate_model_dependency(
        _level3_record(),
        profile=STRICT_LEVEL3_LCDM_PROFILE,
        parameters=parameters,
        strict=True,
    )

    assert ("MODEL_PARAMETER_NOT_NUMERIC", "error") in [(message.code, message.level) for message in messages]


def test_model_profile_detects_mismatch_and_wrong_level() -> None:
    wrong_model = _level3_record(model_version="Other-Model")
    wrong_level = _level2_record()

    mismatch_codes = {message.code for message in validate_model_dependency(wrong_model, profile=STRICT_LEVEL3_LCDM_PROFILE)}
    wrong_level_codes = {message.code for message in validate_model_dependency(wrong_level, profile=STRICT_LEVEL3_LCDM_PROFILE)}

    assert "MODEL_VERSION_PROFILE_MISMATCH" in mismatch_codes
    assert "MODEL_PROFILE_LEVEL_NOT_APPLICABLE" in wrong_level_codes
