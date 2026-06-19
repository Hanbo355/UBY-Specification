from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from .constants import DEFAULT_MODEL_VERSION
from .models import PrecisionLevel, UBYTime, ValidationMessage


@dataclass(frozen=True)
class ModelParameter:
    """A named model parameter with optional units and provenance."""

    name: str
    value: str
    unit: str | None = None
    uncertainty: str | None = None
    reference: str | None = None


@dataclass(frozen=True)
class ModelDependencyProfile:
    """Strict metadata profile for Level 2/3 model-dependent records."""

    model_version: str
    model_family: str
    description: str
    applies_to_levels: tuple[PrecisionLevel, ...]
    required_parameters: tuple[str, ...]
    recommended_parameters: tuple[str, ...]
    required_provenance_fields: tuple[str, ...]
    reference_uri: str | None = None


PLANCK2018_LCDM_PROFILE = ModelDependencyProfile(
    model_version=DEFAULT_MODEL_VERSION,
    model_family="LCDM",
    description=(
        "Default UBY WD 0.1.0 cosmological/deep-time reference model tag. "
        "For Level 3 redshift/age conversion, callers should provide explicit "
        "cosmological parameters in dataset-level provenance or propagation notes."
    ),
    applies_to_levels=(PrecisionLevel.LEVEL_2, PrecisionLevel.LEVEL_3),
    required_parameters=(),
    recommended_parameters=("H0", "Om0", "Ode0", "Tcmb0", "Neff"),
    required_provenance_fields=("model_version",),
    reference_uri="https://www.cosmos.esa.int/web/planck",
)

STRICT_LEVEL3_LCDM_PROFILE = ModelDependencyProfile(
    model_version=DEFAULT_MODEL_VERSION,
    model_family="LCDM",
    description="Strict Level 3 LCDM profile for cosmological redshift/lookback-time conversions.",
    applies_to_levels=(PrecisionLevel.LEVEL_3,),
    required_parameters=("H0", "Om0"),
    recommended_parameters=("Ode0", "Tcmb0", "Neff", "m_nu", "implementation", "integration_method"),
    required_provenance_fields=("model_version", "propagation_note"),
    reference_uri="https://docs.astropy.org/en/stable/cosmology/",
)

MODEL_DEPENDENCY_PROFILES = {
    PLANCK2018_LCDM_PROFILE.model_version: PLANCK2018_LCDM_PROFILE,
    f"{STRICT_LEVEL3_LCDM_PROFILE.model_version}:strict-level3": STRICT_LEVEL3_LCDM_PROFILE,
}


def get_model_dependency_profile(profile_id: str = DEFAULT_MODEL_VERSION) -> ModelDependencyProfile:
    try:
        return MODEL_DEPENDENCY_PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown model dependency profile: {profile_id}") from exc


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def _parse_parameters(parameters: Mapping[str, Any] | tuple[ModelParameter, ...] | None) -> dict[str, Any]:
    if parameters is None:
        return {}
    if isinstance(parameters, tuple):
        return {parameter.name: parameter.value for parameter in parameters}
    return dict(parameters)


def _is_decimal_like(value: Any) -> bool:
    if _is_missing(value):
        return False
    try:
        Decimal(str(value))
    except (InvalidOperation, ValueError):
        return False
    return True


def validate_model_dependency(
    uby: UBYTime,
    *,
    profile: ModelDependencyProfile = PLANCK2018_LCDM_PROFILE,
    parameters: Mapping[str, Any] | tuple[ModelParameter, ...] | None = None,
    strict: bool = False,
) -> list[ValidationMessage]:
    """Validate Level 2/3 model metadata.

    The record-level conformance profile checks that model_version exists.  This
    stricter validator checks that the declared model profile applies to the
    precision level and, in strict mode, that required numeric parameters are
    supplied for Level 3 model-derived records.
    """

    messages: list[ValidationMessage] = []
    parsed_parameters = _parse_parameters(parameters)

    if uby.precision_level not in profile.applies_to_levels:
        messages.append(
            ValidationMessage(
                "MODEL_PROFILE_LEVEL_NOT_APPLICABLE",
                "error",
                f"{profile.model_version} profile does not apply to {uby.precision_level.value}.",
            )
        )

    if not uby.model_version:
        messages.append(
            ValidationMessage(
                "MODEL_VERSION_REQUIRED",
                "error",
                f"{uby.precision_level.value} model-dependent records require model_version.",
            )
        )
    elif uby.model_version != profile.model_version:
        messages.append(
            ValidationMessage(
                "MODEL_VERSION_PROFILE_MISMATCH",
                "error",
                f"Record model_version={uby.model_version!r} does not match profile model_version={profile.model_version!r}.",
            )
        )

    for field_name in profile.required_provenance_fields:
        value = getattr(uby, field_name)
        if _is_missing(value):
            messages.append(
                ValidationMessage(
                    "MODEL_PROVENANCE_FIELD_REQUIRED",
                    "error",
                    f"{field_name} is required by model profile {profile.model_version}.",
                )
            )

    required_parameters = profile.required_parameters if strict or uby.precision_level == PrecisionLevel.LEVEL_3 else ()
    for parameter_name in required_parameters:
        value = parsed_parameters.get(parameter_name)
        if _is_missing(value):
            messages.append(
                ValidationMessage(
                    "MODEL_PARAMETER_REQUIRED",
                    "error",
                    f"{parameter_name} is required by model profile {profile.model_version}.",
                )
            )
        elif not _is_decimal_like(value):
            messages.append(
                ValidationMessage(
                    "MODEL_PARAMETER_NOT_NUMERIC",
                    "error",
                    f"{parameter_name} must be numeric.",
                )
            )

    if uby.precision_level == PrecisionLevel.LEVEL_3 and not parsed_parameters:
        messages.append(
            ValidationMessage(
                "MODEL_PARAMETERS_RECOMMENDED",
                "warning",
                "Level 3 records should include model parameters in metadata or dataset provenance.",
            )
        )

    for parameter_name in profile.recommended_parameters:
        if parameter_name not in parsed_parameters:
            messages.append(
                ValidationMessage(
                    "MODEL_PARAMETER_RECOMMENDED",
                    "warning",
                    f"{parameter_name} is recommended for model profile {profile.model_version}.",
                )
            )

    return messages


def model_dependency_profile_to_dict(profile: ModelDependencyProfile) -> dict[str, Any]:
    return {
        "model_version": profile.model_version,
        "model_family": profile.model_family,
        "description": profile.description,
        "applies_to_levels": [level.value for level in profile.applies_to_levels],
        "required_parameters": list(profile.required_parameters),
        "recommended_parameters": list(profile.recommended_parameters),
        "required_provenance_fields": list(profile.required_provenance_fields),
        "reference_uri": profile.reference_uri,
    }
