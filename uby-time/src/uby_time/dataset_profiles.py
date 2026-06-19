from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from .constants import UBY_SPEC_VERSION
from .models import PrecisionLevel, ValidationMessage

CORE_UBY_FIELDS = (
    "uby_value",
    "uby_expression",
    "uby_version",
    "precision_level",
    "anchor_id",
    "anchor_jd",
    "anchor_uby",
    "rounding_rule",
    "generated_by",
)

MODEL_FIELDS = (
    "model_version",
)

INTERVAL_FIELDS = (
    "interval_start_uby",
    "interval_end_uby",
)

UNCERTAINTY_FIELDS = (
    "uncertainty_years",
    "uncertainty_kind",
    "confidence_level",
)


@dataclass(frozen=True)
class DatasetProfile:
    """Dataset-level conformance profile for UBY-annotated event tables.

    A dataset profile complements the record-level UBY conformance profile.  It
    states which source fields must be preserved, how a representative UBY value
    is derived, and what precision/model/uncertainty policy is expected for a
    particular class of authority dataset.
    """

    profile_id: str
    name: str
    authority: str
    source_uri: str
    event_type: str
    allowed_precision_levels: tuple[PrecisionLevel, ...]
    required_fields: tuple[str, ...]
    recommended_fields: tuple[str, ...]
    source_time_fields: tuple[str, ...]
    representative_time_rule: str
    uncertainty_policy: str
    provenance_policy: str
    model_policy: str
    requires_model_version: bool = False
    requires_uncertainty_or_interval: bool = False


@dataclass(frozen=True)
class DatasetValidationSummary:
    profile_id: str
    record_count: int
    error_count: int
    warning_count: int
    skipped_count: int


ICS_CHART_PROFILE = DatasetProfile(
    profile_id="UBY-DATASET-ICS-CHART-WD-0.1.0",
    name="ICS Chronostratigraphic Chart UBY annotation profile",
    authority="International Commission on Stratigraphy",
    source_uri="https://github.com/i-c-stratigraphy/chart",
    event_type="geologic_boundary_or_event",
    allowed_precision_levels=(PrecisionLevel.LEVEL_1, PrecisionLevel.LEVEL_2),
    required_fields=(
        "source_dataset",
        "source_record_id",
        "event_label",
        "event_type",
        "source_time",
        "source_system",
        "uby_value",
        "uby_expression",
        "precision_level",
        "model_version",
        "uby_version",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
        "rounding_rule",
        "generated_by",
        "attribution",
    ),
    recommended_fields=(
        "uncertainty_years",
        "interval_start_uby",
        "interval_end_uby",
        "uncertainty_kind",
        "validation_messages",
    ),
    source_time_fields=("source_time",),
    representative_time_rule="Use the source Ma/BP value as a boundary/event representative while preserving uncertainty.",
    uncertainty_policy="Use source uncertainty where available; missing uncertainty remains unknown, not zero.",
    provenance_policy="Preserve ICS source identifier, label, source time, source system, attribution, UBY anchor, and version.",
    model_policy="Deep-time Ma/BP conversion requires a declared UBY model_version.",
    requires_model_version=True,
    requires_uncertainty_or_interval=False,
)

PBDB_DINOSAURIA_PROFILE = DatasetProfile(
    profile_id="UBY-DATASET-PBDB-DINOSAURIA-WD-0.1.0",
    name="PBDB Dinosauria occurrence UBY annotation profile",
    authority="Paleobiology Database",
    source_uri="https://paleobiodb.org/data1.2/occs/list.csv",
    event_type="fossil_occurrence_age_interval",
    allowed_precision_levels=(PrecisionLevel.LEVEL_1, PrecisionLevel.LEVEL_2),
    required_fields=(
        "source_dataset",
        "source_record_id",
        "event_label",
        "event_type",
        "accepted_name",
        "max_ma",
        "min_ma",
        "representative_ma_midpoint",
        "years_before_present_midpoint",
        "uncertainty_years",
        "precision_level",
        "uby_value",
        "uby_expression",
        "model_version",
        "uby_version",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
        "rounding_rule",
        "generated_by",
        "attribution",
    ),
    recommended_fields=(
        "early_interval",
        "late_interval",
        "longitude",
        "latitude",
        "formation",
        "geological_group",
        "member",
        "validation_messages",
    ),
    source_time_fields=("min_ma", "max_ma"),
    representative_time_rule="Use midpoint(max_ma, min_ma) as the representative label and half-width as uncertainty_years.",
    uncertainty_policy="The half-width of the PBDB min_ma/max_ma interval is mandatory uncertainty metadata.",
    provenance_policy="Preserve PBDB occurrence number, taxonomic name, stratigraphic interval, coordinates, and attribution.",
    model_policy="Geologic-age conversion requires a declared UBY model_version.",
    requires_model_version=True,
    requires_uncertainty_or_interval=True,
)

NASA_EXOPLANET_ARCHIVE_PROFILE = DatasetProfile(
    profile_id="UBY-DATASET-NASA-EXOPLANET-ARCHIVE-WD-0.1.0",
    name="NASA/IPAC Exoplanet Archive discovery-year UBY annotation profile",
    authority="NASA/IPAC Exoplanet Archive",
    source_uri="https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
    event_type="exoplanet_discovery_year",
    allowed_precision_levels=(PrecisionLevel.LEVEL_1,),
    required_fields=(
        "source_dataset",
        "source_record_id",
        "event_label",
        "event_type",
        "planet_name",
        "discovery_year",
        "representative_astronomical_year",
        "uncertainty_years",
        "precision_level",
        "uby_value",
        "uby_expression",
        "uby_version",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
        "rounding_rule",
        "generated_by",
        "attribution",
    ),
    recommended_fields=(
        "hostname",
        "discovery_method",
        "discovery_facility",
        "right_ascension_deg",
        "declination_deg",
        "validation_messages",
    ),
    source_time_fields=("discovery_year",),
    representative_time_rule="Use the source discovery year as an astronomical-year Level 1 label; do not fabricate month/day/time.",
    uncertainty_policy="Use uncertainty_years=1 to record year-level temporal resolution.",
    provenance_policy="Preserve NASA/IPAC source record name, host, discovery method/facility, coordinates, and attribution.",
    model_policy="No cosmological model is required for discovery-year event labels.",
)

USGS_EARTHQUAKE_PROFILE = DatasetProfile(
    profile_id="UBY-DATASET-USGS-EARTHQUAKE-WD-0.1.0",
    name="USGS Earthquake Catalog UTC event-time UBY annotation profile",
    authority="U.S. Geological Survey",
    source_uri="https://earthquake.usgs.gov/fdsnws/event/1/",
    event_type="earthquake_event_time",
    allowed_precision_levels=(PrecisionLevel.LEVEL_1,),
    required_fields=(
        "source_dataset",
        "source_record_id",
        "source_time_utc",
        "event_label",
        "event_type",
        "precision_level",
        "uby_value",
        "uby_expression",
        "uby_version",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
        "rounding_rule",
        "generated_by",
        "latitude",
        "longitude",
        "magnitude",
        "attribution",
    ),
    recommended_fields=(
        "depth_km",
        "magnitude_type",
        "place",
        "usgs_type",
        "status",
        "location_source",
        "magnitude_source",
        "updated_time_utc",
        "validation_messages",
    ),
    source_time_fields=("source_time_utc",),
    representative_time_rule="Use the USGS UTC event timestamp directly as a Level 1 source time.",
    uncertainty_policy="Do not invent temporal uncertainty when the source CSV does not provide it.",
    provenance_policy="Preserve USGS event id, UTC time, spatial fields, magnitude, event page URI, and attribution.",
    model_policy="No cosmological model is required for near-present UTC event labels.",
)


DATASET_PROFILES = {
    ICS_CHART_PROFILE.profile_id: ICS_CHART_PROFILE,
    PBDB_DINOSAURIA_PROFILE.profile_id: PBDB_DINOSAURIA_PROFILE,
    NASA_EXOPLANET_ARCHIVE_PROFILE.profile_id: NASA_EXOPLANET_ARCHIVE_PROFILE,
    USGS_EARTHQUAKE_PROFILE.profile_id: USGS_EARTHQUAKE_PROFILE,
}


def dataset_profile_to_dict(profile: DatasetProfile) -> dict[str, Any]:
    """Serialize a dataset profile to a JSON-safe dictionary."""

    payload = asdict(profile)
    payload["allowed_precision_levels"] = [level.value for level in profile.allowed_precision_levels]
    payload["required_fields"] = list(profile.required_fields)
    payload["recommended_fields"] = list(profile.recommended_fields)
    payload["source_time_fields"] = list(profile.source_time_fields)
    payload["uby_version"] = UBY_SPEC_VERSION
    return payload


def dataset_profiles_to_dicts() -> list[dict[str, Any]]:
    """Serialize all built-in dataset profiles to JSON-safe dictionaries."""

    return [dataset_profile_to_dict(profile) for profile in DATASET_PROFILES.values()]


def get_dataset_profile(profile_id: str) -> DatasetProfile:
    try:
        return DATASET_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown dataset profile: {profile_id}") from exc


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def _decimal_or_none(value: Any) -> Decimal | None:
    if _is_missing(value):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _precision_level(value: Any) -> PrecisionLevel | None:
    if _is_missing(value):
        return None
    try:
        return value if isinstance(value, PrecisionLevel) else PrecisionLevel(str(value))
    except ValueError:
        return None


def validate_dataset_record(
    record: Mapping[str, Any],
    profile: DatasetProfile,
    *,
    row_number: int | None = None,
) -> list[ValidationMessage]:
    """Validate a UBY-annotated dataset row against a dataset profile."""

    prefix = f"row {row_number}: " if row_number is not None else ""
    messages: list[ValidationMessage] = []

    for field_name in profile.required_fields:
        if field_name not in record or _is_missing(record.get(field_name)):
            messages.append(
                ValidationMessage(
                    "DATASET_REQUIRED_FIELD_MISSING",
                    "error",
                    f"{prefix}{field_name} is required by {profile.profile_id}.",
                )
            )

    for field_name in CORE_UBY_FIELDS:
        if field_name in profile.required_fields and _is_missing(record.get(field_name)):
            messages.append(
                ValidationMessage(
                    "DATASET_CORE_UBY_FIELD_MISSING",
                    "error",
                    f"{prefix}{field_name} is a required UBY field.",
                )
            )

    precision = _precision_level(record.get("precision_level"))
    if precision is None:
        messages.append(
            ValidationMessage(
                "DATASET_PRECISION_LEVEL_INVALID",
                "error",
                f"{prefix}precision_level must be one of {[level.value for level in profile.allowed_precision_levels]}.",
            )
        )
    elif precision not in profile.allowed_precision_levels:
        messages.append(
            ValidationMessage(
                "DATASET_PRECISION_LEVEL_NOT_ALLOWED",
                "error",
                f"{prefix}{precision.value} is not allowed by {profile.profile_id}.",
            )
        )

    model_version = record.get("model_version")
    if profile.requires_model_version and _is_missing(model_version):
        messages.append(
            ValidationMessage(
                "DATASET_MODEL_VERSION_REQUIRED",
                "error",
                f"{prefix}model_version is required by {profile.profile_id}.",
            )
        )

    if str(record.get("uby_version", "")) != UBY_SPEC_VERSION:
        messages.append(
            ValidationMessage(
                "DATASET_SPEC_VERSION_MISMATCH",
                "warning",
                f"{prefix}uby_version differs from profile spec version {UBY_SPEC_VERSION}.",
            )
        )

    has_uncertainty = not _is_missing(record.get("uncertainty_years"))
    has_interval = not _is_missing(record.get("interval_start_uby")) and not _is_missing(record.get("interval_end_uby"))
    if profile.requires_uncertainty_or_interval and not (has_uncertainty or has_interval):
        messages.append(
            ValidationMessage(
                "DATASET_UNCERTAINTY_OR_INTERVAL_REQUIRED",
                "error",
                f"{prefix}{profile.profile_id} requires uncertainty_years or interval bounds.",
            )
        )

    start = _decimal_or_none(record.get("interval_start_uby"))
    end = _decimal_or_none(record.get("interval_end_uby"))
    if start is not None and end is not None and start > end:
        messages.append(
            ValidationMessage(
                "DATASET_INTERVAL_ORDER_INVALID",
                "error",
                f"{prefix}interval_start_uby must be <= interval_end_uby.",
            )
        )

    uby_value = _decimal_or_none(record.get("uby_value"))
    if uby_value is None:
        messages.append(
            ValidationMessage(
                "DATASET_UBY_VALUE_INVALID",
                "error",
                f"{prefix}uby_value must be a decimal string.",
            )
        )
    elif uby_value < 0:
        messages.append(
            ValidationMessage(
                "DATASET_UBY_VALUE_NEGATIVE",
                "error",
                f"{prefix}uby_value must be non-negative.",
            )
        )

    uncertainty = _decimal_or_none(record.get("uncertainty_years"))
    if not _is_missing(record.get("uncertainty_years")) and uncertainty is None:
        messages.append(
            ValidationMessage(
                "DATASET_UNCERTAINTY_INVALID",
                "error",
                f"{prefix}uncertainty_years must be a decimal string.",
            )
        )
    elif uncertainty is not None and uncertainty < 0:
        messages.append(
            ValidationMessage(
                "DATASET_UNCERTAINTY_NEGATIVE",
                "error",
                f"{prefix}uncertainty_years must be non-negative.",
            )
        )

    return messages


def validate_dataset_records(
    records: list[Mapping[str, Any]],
    profile: DatasetProfile,
) -> tuple[DatasetValidationSummary, list[ValidationMessage]]:
    messages: list[ValidationMessage] = []
    skipped_count = 0

    for index, record in enumerate(records, start=1):
        if not record:
            skipped_count += 1
            continue
        messages.extend(validate_dataset_record(record, profile, row_number=index))

    error_count = sum(1 for message in messages if message.level == "error")
    warning_count = sum(1 for message in messages if message.level == "warning")
    return (
        DatasetValidationSummary(
            profile_id=profile.profile_id,
            record_count=len(records),
            error_count=error_count,
            warning_count=warning_count,
            skipped_count=skipped_count,
        ),
        messages,
    )
