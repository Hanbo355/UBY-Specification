from __future__ import annotations

import re
from decimal import Decimal

from .constants import (
    DEFAULT_ANCHOR_ID,
    DEFAULT_ANCHOR_JD,
    DEFAULT_ANCHOR_UBY,
    DEFAULT_LEVEL1_RANGE_YEARS,
    UBY_SPEC_VERSION,
)
from .models import PrecisionLevel, UBYTime, ValidationMessage

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$")
MODEL_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+$")
ACADEMIC_MNEMONIC_RE = re.compile(r"^UBY (?P<prefix>\d{6})(?P<sign>[+-])(?P<year>\d{6})(?:\s|$)")
FRIENDLY_MNEMONIC_RE = re.compile(r"^UBY (?P<prefix>\d{6}) (?P<era>AD|BC)(?P<year>\d+)(?:\s|$)")


def _meaningful_fractional_digits(value: Decimal) -> int:
    """Return fractional digits that carry information, ignoring trailing zeros."""
    normalized = value.normalize()
    exponent = normalized.as_tuple().exponent
    return max(-exponent, 0)


def _has_declared_uncertainty(uby: UBYTime) -> bool:
    return (
        uby.uncertainty_years is not None
        or (uby.interval_start_uby is not None and uby.interval_end_uby is not None)
    )


def _mnemonic_astronomical_year(raw: str | None) -> int | None:
    if not raw:
        return None

    expression = raw.strip()

    if match := ACADEMIC_MNEMONIC_RE.match(expression):
        year = int(match.group("year"))
        return year if match.group("sign") == "+" else -year

    if match := FRIENDLY_MNEMONIC_RE.match(expression):
        year = int(match.group("year"))
        return year if match.group("era") == "AD" else 1 - year

    return None


def validate_uby_time(uby: UBYTime) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []

    if uby.uby_value < 0:
        messages.append(ValidationMessage("UBY_NEGATIVE_VALUE", "error", "UBY value must be non-negative."))

    if not uby.uby_version:
        messages.append(ValidationMessage("SPEC_VERSION_UNDECLARED", "warning", "UBY specification version is not declared."))
    elif not SEMVER_RE.match(uby.uby_version):
        messages.append(ValidationMessage("INVALID_SPEC_VERSION", "error", "uby_version must use semantic versioning."))

    if uby.model_version and not MODEL_RE.match(uby.model_version):
        messages.append(ValidationMessage("INVALID_MODEL_VERSION", "error", "model_version does not match the model tag syntax."))

    if uby.precision_level in {PrecisionLevel.LEVEL_2, PrecisionLevel.LEVEL_3} and not uby.model_version:
        messages.append(ValidationMessage("MODEL_REQUIRED_FOR_LEVEL_2_3", "error", "Level 2 and Level 3 UBY values require model_version."))

    if uby.anchor_id == DEFAULT_ANCHOR_ID:
        if uby.uby_version and uby.uby_version != UBY_SPEC_VERSION:
            messages.append(
                ValidationMessage(
                    "ANCHOR_VERSION_MISMATCH",
                    "error",
                    f"{DEFAULT_ANCHOR_ID} is defined for UBY spec {UBY_SPEC_VERSION}, not {uby.uby_version}.",
                )
            )
        if uby.anchor_jd != DEFAULT_ANCHOR_JD or uby.anchor_uby != DEFAULT_ANCHOR_UBY:
            messages.append(
                ValidationMessage(
                    "ANCHOR_VALUE_MISMATCH",
                    "error",
                    "Default anchor_id is paired with non-default anchor_jd or anchor_uby.",
                )
            )

    if uby.precision_level == PrecisionLevel.LEVEL_1:
        delta = abs(uby.uby_value - uby.anchor_uby)
        if delta > Decimal(DEFAULT_LEVEL1_RANGE_YEARS):
            messages.append(ValidationMessage("LEVEL1_RANGE_EXCEEDED", "warning", "Value is outside the default ±1,000,000 year Level 1 window."))

    mnemonic_year = _mnemonic_astronomical_year(uby.source_time)
    if mnemonic_year is not None and not (-999999 <= mnemonic_year <= 999999):
        messages.append(
            ValidationMessage(
                "MNEMONIC_OUT_OF_LEVEL1_RANGE",
                "error",
                "AD/BC and academic mnemonics are only valid within the ±999999 astronomical-year Level 1 mnemonic range.",
            )
        )

    if (uby.interval_start_uby is None) ^ (uby.interval_end_uby is None):
        messages.append(
            ValidationMessage(
                "INCOMPLETE_UNCERTAINTY_INTERVAL",
                "error",
                "interval_start_uby and interval_end_uby must be supplied together.",
            )
        )

    if uby.interval_start_uby is not None and uby.interval_end_uby is not None:
        if uby.interval_start_uby > uby.interval_end_uby:
            messages.append(ValidationMessage("INVALID_UNCERTAINTY_INTERVAL", "error", "interval_start_uby must be <= interval_end_uby."))
        elif not (uby.interval_start_uby <= uby.uby_value <= uby.interval_end_uby):
            messages.append(
                ValidationMessage(
                    "UBY_VALUE_OUTSIDE_UNCERTAINTY_INTERVAL",
                    "warning",
                    "uby_value is outside the declared uncertainty interval.",
                )
            )

    if uby.uncertainty_years is not None and uby.uncertainty_years < 0:
        messages.append(ValidationMessage("INVALID_UNCERTAINTY", "error", "uncertainty_years must be non-negative."))

    if uby.confidence_level is not None and not (Decimal("0") < uby.confidence_level <= Decimal("1")):
        messages.append(
            ValidationMessage(
                "INVALID_CONFIDENCE_LEVEL",
                "error",
                "confidence_level must be greater than 0 and less than or equal to 1.",
            )
        )

    fractional_digits = _meaningful_fractional_digits(uby.uby_value)
    if uby.uncertainty_years is not None:
        if uby.uncertainty_years >= Decimal("1000") and fractional_digits > 0:
            messages.append(
                ValidationMessage(
                    "FALSE_PRECISION_RISK",
                    "warning",
                    "Declared uncertainty is at least 1000 years; fractional-year display may imply unsupported precision.",
                )
            )
        if uby.uncertainty_years >= Decimal("1000000"):
            messages.append(
                ValidationMessage(
                    "MAGNITUDE_DISPLAY_RECOMMENDED",
                    "warning",
                    "Declared uncertainty is at least 1e6 years; formal display should prefer M/G magnitude labels with uncertainty.",
                )
            )
    elif uby.precision_level in {PrecisionLevel.LEVEL_2, PrecisionLevel.LEVEL_3} and fractional_digits > 0:
        messages.append(
            ValidationMessage(
                "FALSE_PRECISION_RISK",
                "warning",
                "Model-dependent Level 2/3 value has fractional years but no uncertainty metadata.",
            )
        )

    if uby.precision_level == PrecisionLevel.LEVEL_3:
        if not uby.model_version:
            # MODEL_REQUIRED_FOR_LEVEL_2_3 already reports the normative error.
            pass
        elif not uby.propagation_note:
            messages.append(
                ValidationMessage(
                    "MODEL_PROVENANCE_FIELD_REQUIRED",
                    "warning",
                    "Level 3 model-derived records should include propagation_note describing the computation path.",
                )
            )
        if not _has_declared_uncertainty(uby):
            messages.append(
                ValidationMessage(
                    "UNCERTAINTY_UNDECLARED",
                    "warning",
                    "Level 3 model-derived records should declare uncertainty or an explicit uncertainty policy.",
                )
            )

    return messages
