from __future__ import annotations

from uby_time.dataset_profiles import (
    DATASET_PROFILES,
    NASA_EXOPLANET_ARCHIVE_PROFILE,
    PBDB_DINOSAURIA_PROFILE,
    USGS_EARTHQUAKE_PROFILE,
    DatasetProfile,
    get_dataset_profile,
    validate_dataset_record,
    validate_dataset_records,
)


def _valid_pbdb_record() -> dict[str, str]:
    return {
        "source_dataset": "Paleobiology Database occurrence API (Dinosauria subset)",
        "source_record_id": "130209",
        "event_label": "PBDB occurrence 130209: Chaoyangsaurus youngi",
        "event_type": "fossil_occurrence_age_interval",
        "accepted_name": "Chaoyangsaurus youngi",
        "max_ma": "152.21",
        "min_ma": "132.6",
        "representative_ma_midpoint": "142.405",
        "years_before_present_midpoint": "142405000",
        "uncertainty_years": "9805000",
        "precision_level": "Level 2",
        "uby_value": "13644595000",
        "uby_expression": "UBY 13644595000 [model=LCDM-Planck2018] [spec=0.1.0]",
        "model_version": "LCDM-Planck2018",
        "uby_version": "0.1.0",
        "anchor_id": "UBY-ANCHOR-2026-01-01Z",
        "anchor_jd": "2461041.5",
        "anchor_uby": "13787002026.0",
        "rounding_rule": "year-floor",
        "generated_by": "uby-time/0.1.0",
        "attribution": "Data from the Paleobiology Database (PBDB).",
    }


def _valid_nasa_record() -> dict[str, str]:
    return {
        "source_dataset": "NASA/IPAC Exoplanet Archive Planetary Systems Composite Parameters",
        "source_record_id": "51 Peg b",
        "event_label": "Discovery of exoplanet 51 Peg b",
        "event_type": "exoplanet_discovery_year",
        "planet_name": "51 Peg b",
        "discovery_year": "1995",
        "representative_astronomical_year": "1995",
        "uncertainty_years": "1",
        "precision_level": "Level 1",
        "uby_value": "13787001995",
        "uby_expression": "UBY 13787001995 [spec=0.1.0]",
        "uby_version": "0.1.0",
        "anchor_id": "UBY-ANCHOR-2026-01-01Z",
        "anchor_jd": "2461041.5",
        "anchor_uby": "13787002026.0",
        "rounding_rule": "year-floor",
        "generated_by": "uby-time/0.1.0",
        "attribution": "Data from the NASA/IPAC Exoplanet Archive.",
    }


def _valid_usgs_record() -> dict[str, str]:
    return {
        "source_dataset": "USGS Earthquake Catalog",
        "source_record_id": "usc000lv5e",
        "source_time_utc": "2014-01-01T00:01:16.610Z",
        "event_label": "USGS earthquake usc000lv5e: M5.1 76 km NNW of Davila, Philippines",
        "event_type": "earthquake_event_time",
        "precision_level": "Level 1",
        "uby_value": "13787002014.00000242762440743",
        "uby_expression": "UBY 13787002014.00000242762440743 [model=LCDM-Planck2018] [spec=0.1.0]",
        "uby_version": "0.1.0",
        "anchor_id": "UBY-ANCHOR-2026-01-01Z",
        "anchor_jd": "2461041.5",
        "anchor_uby": "13787002026.0",
        "rounding_rule": "year-floor",
        "generated_by": "uby-time/0.1.0",
        "latitude": "19.0868",
        "longitude": "120.2389",
        "magnitude": "5.1",
        "attribution": "Data from the U.S. Geological Survey (USGS) Earthquake Catalog.",
    }


def test_dataset_profile_registry_contains_authority_profiles() -> None:
    assert len(DATASET_PROFILES) == 4
    assert get_dataset_profile(PBDB_DINOSAURIA_PROFILE.profile_id) is PBDB_DINOSAURIA_PROFILE
    assert get_dataset_profile(NASA_EXOPLANET_ARCHIVE_PROFILE.profile_id) is NASA_EXOPLANET_ARCHIVE_PROFILE
    assert get_dataset_profile(USGS_EARTHQUAKE_PROFILE.profile_id) is USGS_EARTHQUAKE_PROFILE

    for profile in DATASET_PROFILES.values():
        assert isinstance(profile, DatasetProfile)
        assert profile.profile_id.startswith("UBY-DATASET-")
        assert profile.authority
        assert profile.source_uri.startswith("https://")
        assert "uby_value" in profile.required_fields
        assert "precision_level" in profile.required_fields
        assert profile.source_time_fields


def test_pbdb_profile_valid_record_passes() -> None:
    messages = validate_dataset_record(_valid_pbdb_record(), PBDB_DINOSAURIA_PROFILE)

    assert messages == []


def test_pbdb_profile_requires_model_and_uncertainty() -> None:
    record = _valid_pbdb_record()
    record["model_version"] = ""
    record["uncertainty_years"] = ""

    messages = validate_dataset_record(record, PBDB_DINOSAURIA_PROFILE)
    codes = {message.code for message in messages}

    assert "DATASET_REQUIRED_FIELD_MISSING" in codes
    assert "DATASET_MODEL_VERSION_REQUIRED" in codes
    assert "DATASET_UNCERTAINTY_OR_INTERVAL_REQUIRED" in codes


def test_level1_dataset_profiles_reject_level2_rows() -> None:
    nasa = _valid_nasa_record()
    nasa["precision_level"] = "Level 2"

    usgs = _valid_usgs_record()
    usgs["precision_level"] = "Level 2"

    nasa_codes = {message.code for message in validate_dataset_record(nasa, NASA_EXOPLANET_ARCHIVE_PROFILE)}
    usgs_codes = {message.code for message in validate_dataset_record(usgs, USGS_EARTHQUAKE_PROFILE)}

    assert "DATASET_PRECISION_LEVEL_NOT_ALLOWED" in nasa_codes
    assert "DATASET_PRECISION_LEVEL_NOT_ALLOWED" in usgs_codes


def test_dataset_record_numeric_checks() -> None:
    record = _valid_usgs_record()
    record["uby_value"] = "not-a-decimal"

    messages = validate_dataset_record(record, USGS_EARTHQUAKE_PROFILE)

    assert [(message.code, message.level) for message in messages] == [
        ("DATASET_UBY_VALUE_INVALID", "error")
    ]


def test_dataset_records_summary_counts_errors_warnings_and_skipped_rows() -> None:
    valid = _valid_nasa_record()
    warning = _valid_nasa_record()
    warning["uby_version"] = "0.2.0"
    invalid = _valid_nasa_record()
    invalid["uby_value"] = "-1"

    summary, messages = validate_dataset_records(
        [valid, warning, invalid, {}],
        NASA_EXOPLANET_ARCHIVE_PROFILE,
    )

    assert summary.profile_id == NASA_EXOPLANET_ARCHIVE_PROFILE.profile_id
    assert summary.record_count == 4
    assert summary.error_count == 1
    assert summary.warning_count == 1
    assert summary.skipped_count == 1
    assert [message.code for message in messages] == [
        "DATASET_SPEC_VERSION_MISMATCH",
        "DATASET_UBY_VALUE_NEGATIVE",
    ]
