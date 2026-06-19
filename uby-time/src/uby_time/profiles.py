from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .constants import DEFAULT_ANCHOR_ISO, DEFAULT_LEVEL1_RANGE_YEARS, UBY_SPEC_VERSION
from .models import PrecisionLevel, UBYTime, ValidationMessage

UncertaintyKind = Literal[
    "measurement",
    "temporal_resolution",
    "interval",
    "model",
    "observational",
    "propagated",
    "propagated_addition",
    "propagated_multiplication",
]

IntervalInterpretation = Literal[
    "closed",
    "open",
    "left_open",
    "right_open",
    "representative_with_bounds",
]

ProvenanceRequirement = Literal["required", "recommended", "optional"]


class ConformanceLevel(str, Enum):
    """Conformance outcomes for UBY profile validation."""

    CONFORMANT = "conformant"
    WARNING = "warning"
    NON_CONFORMANT = "non_conformant"


@dataclass(frozen=True)
class PrecisionLevelDefinition:
    """Formal definition of a UBY precision level."""

    level: PrecisionLevel
    name: str
    normative_scope: str
    intended_sources: tuple[str, ...]
    required_metadata: tuple[str, ...]
    recommended_metadata: tuple[str, ...]
    false_precision_risks: tuple[str, ...]
    default_range_years: str | None = None
    requires_model_version: bool = False
    requires_uncertainty_or_interval: bool = False
    requires_model_dependency_metadata: bool = False


@dataclass(frozen=True)
class UncertaintySchema:
    """Normative uncertainty metadata contract."""

    allowed_kinds: tuple[UncertaintyKind, ...]
    required_when_source_is_interval: tuple[str, ...]
    confidence_level_range: tuple[str, str]
    interval_rule: str
    missing_uncertainty_rule: str
    false_precision_rule: str


@dataclass(frozen=True)
class IntervalRepresentation:
    """Normative interval representation contract."""

    start_field: str
    end_field: str
    interpretation: IntervalInterpretation
    ordering_rule: str
    representative_rule: str
    source_preservation_rule: str


@dataclass(frozen=True)
class ProvenanceModel:
    """Normative provenance metadata contract."""

    required_fields: tuple[str, ...]
    recommended_fields: tuple[str, ...]
    source_time_rule: str
    source_system_rule: str
    generated_by_rule: str


@dataclass(frozen=True)
class ModelDependencyMetadata:
    """Normative metadata for model-derived UBY values."""

    required_for_levels: tuple[PrecisionLevel, ...]
    required_fields: tuple[str, ...]
    recommended_fields: tuple[str, ...]
    model_version_rule: str
    propagation_rule: str


@dataclass(frozen=True)
class AnchorVersionCompatibility:
    """Compatibility contract between anchors, spec versions, and generated records."""

    default_anchor_iso: str
    current_spec_version: str
    required_anchor_fields: tuple[str, ...]
    compatibility_rule: str
    version_rule: str
    anchor_change_rule: str


@dataclass(frozen=True)
class UBYConformanceProfile:
    """A complete conformance profile for UBY WD 0.1.0."""

    profile_id: str
    spec_version: str
    precision_levels: tuple[PrecisionLevelDefinition, ...]
    uncertainty_schema: UncertaintySchema
    interval_representation: IntervalRepresentation
    provenance_model: ProvenanceModel
    model_dependency_metadata: ModelDependencyMetadata
    anchor_version_compatibility: AnchorVersionCompatibility


LEVEL_1_DEFINITION = PrecisionLevelDefinition(
    level=PrecisionLevel.LEVEL_1,
    name="Relative precise measurement level",
    normative_scope=(
        "Near-present civil, historical, astronomical-year, Julian Date, and UTC/ISO "
        "data that can be converted relative to the declared UBY anchor."
    ),
    default_range_years=str(DEFAULT_LEVEL1_RANGE_YEARS),
    intended_sources=(
        "UTC/ISO8601",
        "JulianDate",
        "AstronomicalYear",
        "HistoricalBC",
        "near-present event catalogs",
    ),
    required_metadata=(
        "uby_value",
        "uby_version",
        "precision_level",
        "source_time",
        "source_system",
        "rounding_rule",
        "generated_by",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
    ),
    recommended_metadata=(
        "uncertainty_years",
        "confidence_level",
        "propagation_note",
    ),
    false_precision_risks=(
        "Historical calendar ambiguity must not be hidden.",
        "Year-only data must not be converted into fabricated month/day timestamps.",
        "UTC/ISO labels must not be used as legal or precision-timing replacements.",
    ),
)

LEVEL_2_DEFINITION = PrecisionLevelDefinition(
    level=PrecisionLevel.LEVEL_2,
    name="Proportional narrative level",
    normative_scope=(
        "Geological, paleobiological, paleoclimate, and other deep-time records "
        "whose source times are broad estimates, intervals, or scale positions."
    ),
    intended_sources=(
        "Ma BP",
        "Ga BP",
        "geologic interval",
        "stratigraphic boundary",
        "fossil occurrence age range",
        "paleoclimate age model",
    ),
    required_metadata=(
        "uby_value",
        "uby_version",
        "model_version",
        "precision_level",
        "source_time",
        "source_system",
        "rounding_rule",
        "generated_by",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
    ),
    recommended_metadata=(
        "uncertainty_years",
        "interval_start_uby",
        "interval_end_uby",
        "uncertainty_kind",
        "propagation_note",
    ),
    false_precision_risks=(
        "Intervals must not be collapsed into exact instants without declaring a representative rule.",
        "Ma/Ga source precision must not be expanded into unsupported decimal places.",
        "Chronostratigraphic names must not be treated as exact numeric times.",
    ),
    requires_model_version=True,
    requires_uncertainty_or_interval=True,
)

LEVEL_3_DEFINITION = PrecisionLevelDefinition(
    level=PrecisionLevel.LEVEL_3,
    name="Model-dependent cosmological level",
    normative_scope=(
        "High-redshift, early-universe, cosmological-lookback, and other records "
        "whose UBY value depends on an explicit physical or computational model."
    ),
    intended_sources=(
        "CosmologicalRedshift",
        "lookback time",
        "cosmological age",
        "model-derived early universe event",
    ),
    required_metadata=(
        "uby_value",
        "uby_version",
        "model_version",
        "precision_level",
        "source_time",
        "source_system",
        "rounding_rule",
        "generated_by",
        "anchor_id",
        "anchor_jd",
        "anchor_uby",
    ),
    recommended_metadata=(
        "propagation_note",
        "uncertainty_years",
        "confidence_level",
        "interval_start_uby",
        "interval_end_uby",
        "uncertainty_kind",
    ),
    false_precision_risks=(
        "Redshift-to-age conversion must not be reported without cosmological model metadata.",
        "Model-dependent values must not be compared as model-independent instants.",
        "Derived effective digits must not exceed source/model support.",
    ),
    requires_model_version=True,
    requires_uncertainty_or_interval=True,
    requires_model_dependency_metadata=True,
)

WD_0_1_0_PROFILE = UBYConformanceProfile(
    profile_id="UBY-WD-0.1.0-Core-Conformance",
    spec_version=UBY_SPEC_VERSION,
    precision_levels=(LEVEL_1_DEFINITION, LEVEL_2_DEFINITION, LEVEL_3_DEFINITION),
    uncertainty_schema=UncertaintySchema(
        allowed_kinds=(
            "measurement",
            "temporal_resolution",
            "interval",
            "model",
            "observational",
            "propagated",
            "propagated_addition",
            "propagated_multiplication",
        ),
        required_when_source_is_interval=("interval_start_uby", "interval_end_uby", "uncertainty_kind"),
        confidence_level_range=("0", "1"),
        interval_rule="If both interval_start_uby and interval_end_uby are present, start MUST be <= end.",
        missing_uncertainty_rule=(
            "Missing uncertainty means unknown or undeclared uncertainty; it MUST NOT be interpreted as zero."
        ),
        false_precision_rule=(
            "A representative uby_value derived from an interval MUST preserve the source interval or "
            "uncertainty metadata and MUST declare the representative rule in source_system or propagation_note."
        ),
    ),
    interval_representation=IntervalRepresentation(
        start_field="interval_start_uby",
        end_field="interval_end_uby",
        interpretation="closed",
        ordering_rule="interval_start_uby MUST be less than or equal to interval_end_uby.",
        representative_rule=(
            "uby_value MAY be a midpoint, boundary, or model-derived representative only when the rule "
            "is documented in source_system or propagation_note."
        ),
        source_preservation_rule=(
            "The original source interval string or native interval fields MUST remain available through "
            "source_time, source_system, or dataset-level provenance."
        ),
    ),
    provenance_model=ProvenanceModel(
        required_fields=(
            "source_time",
            "source_system",
            "rounding_rule",
            "generated_by",
            "uby_version",
            "anchor_id",
            "anchor_jd",
            "anchor_uby",
        ),
        recommended_fields=(
            "propagation_note",
            "model_version",
            "confidence_level",
            "uncertainty_kind",
        ),
        source_time_rule="source_time MUST preserve the native source time expression when available.",
        source_system_rule="source_system MUST identify the native or derived time system used for conversion.",
        generated_by_rule="generated_by MUST identify the implementation and version that produced the record.",
    ),
    model_dependency_metadata=ModelDependencyMetadata(
        required_for_levels=(PrecisionLevel.LEVEL_2, PrecisionLevel.LEVEL_3),
        required_fields=("model_version",),
        recommended_fields=(
            "propagation_note",
            "uncertainty_years",
            "confidence_level",
            "interval_start_uby",
            "interval_end_uby",
        ),
        model_version_rule=(
            "Level 2 and Level 3 records MUST declare model_version. Level 3 records SHOULD include "
            "model parameters or a resolvable model profile in propagation_note or dataset provenance."
        ),
        propagation_rule=(
            "Any model-derived conversion SHOULD describe the conversion method and assumptions in propagation_note."
        ),
    ),
    anchor_version_compatibility=AnchorVersionCompatibility(
        default_anchor_iso=DEFAULT_ANCHOR_ISO,
        current_spec_version=UBY_SPEC_VERSION,
        required_anchor_fields=("anchor_id", "anchor_jd", "anchor_uby"),
        compatibility_rule=(
            "A record is comparable within a UBY series only when anchor fields and version semantics are compatible."
        ),
        version_rule="uby_version MUST use semantic versioning.",
        anchor_change_rule=(
            "Any future anchor change MUST be represented by a new anchor_id and compatibility mapping; "
            "existing serialized records MUST retain their original anchor fields."
        ),
    ),
)


def get_precision_definition(level: PrecisionLevel | str) -> PrecisionLevelDefinition:
    precision_level = level if isinstance(level, PrecisionLevel) else PrecisionLevel(level)
    for definition in WD_0_1_0_PROFILE.precision_levels:
        if definition.level == precision_level:
            return definition
    raise ValueError(f"Unknown precision level: {level}")


def validate_conformance_profile(
    uby: UBYTime,
    *,
    profile: UBYConformanceProfile = WD_0_1_0_PROFILE,
) -> list[ValidationMessage]:
    """Validate a UBYTime record against the WD 0.1.0 conformance profile.

    This function complements the low-level validator.  It checks normative
    metadata expectations that are not expressible as simple numeric validation.
    """

    messages: list[ValidationMessage] = []
    definition = get_precision_definition(uby.precision_level)

    for field_name in profile.provenance_model.required_fields:
        value = getattr(uby, field_name)
        if value is None or value == "":
            messages.append(
                ValidationMessage(
                    "PROVENANCE_FIELD_REQUIRED",
                    "error",
                    f"{field_name} is required by the provenance model.",
                )
            )

    for field_name in definition.required_metadata:
        value = getattr(uby, field_name)
        if value is None or value == "":
            messages.append(
                ValidationMessage(
                    "PRECISION_LEVEL_METADATA_REQUIRED",
                    "error",
                    f"{field_name} is required for {definition.level.value}.",
                )
            )

    if definition.requires_model_version and not uby.model_version:
        messages.append(
            ValidationMessage(
                "MODEL_DEPENDENCY_METADATA_REQUIRED",
                "error",
                f"{definition.level.value} records require model_version.",
            )
        )

    has_interval = uby.interval_start_uby is not None and uby.interval_end_uby is not None
    has_uncertainty = uby.uncertainty_years is not None
    if definition.requires_uncertainty_or_interval and not (has_interval or has_uncertainty):
        messages.append(
            ValidationMessage(
                "UNCERTAINTY_OR_INTERVAL_RECOMMENDED",
                "warning",
                f"{definition.level.value} records should carry uncertainty_years or interval bounds.",
            )
        )

    if has_interval and uby.interval_start_uby is not None and uby.interval_end_uby is not None:
        if uby.interval_start_uby > uby.interval_end_uby:
            messages.append(
                ValidationMessage(
                    "INTERVAL_ORDER_INVALID",
                    "error",
                    profile.interval_representation.ordering_rule,
                )
            )

    if uby.uncertainty_kind is not None:
        allowed = set(profile.uncertainty_schema.allowed_kinds)
        if uby.uncertainty_kind not in allowed:
            messages.append(
                ValidationMessage(
                    "UNCERTAINTY_KIND_UNKNOWN",
                    "warning",
                    f"uncertainty_kind should be one of {sorted(allowed)}.",
                )
            )

    if uby.precision_level == PrecisionLevel.LEVEL_3 and not uby.propagation_note:
        messages.append(
            ValidationMessage(
                "MODEL_PROPAGATION_NOTE_RECOMMENDED",
                "warning",
                "Level 3 model-dependent records should describe conversion assumptions in propagation_note.",
            )
        )

    if uby.uby_version != profile.spec_version:
        messages.append(
            ValidationMessage(
                "PROFILE_SPEC_VERSION_MISMATCH",
                "warning",
                f"Record uby_version={uby.uby_version!r} differs from profile spec_version={profile.spec_version!r}.",
            )
        )

    return messages


def is_conformant(uby: UBYTime, *, profile: UBYConformanceProfile = WD_0_1_0_PROFILE) -> bool:
    return all(message.level != "error" for message in validate_conformance_profile(uby, profile=profile))
