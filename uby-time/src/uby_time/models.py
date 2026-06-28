from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple
import re

from .constants import (
    DEFAULT_ANCHOR_ID,
    DEFAULT_ANCHOR_JD,
    DEFAULT_ANCHOR_UBY,
    DEFAULT_MODEL_VERSION,
    DEFAULT_ROUNDING_RULE,
    GENERATED_BY,
    UBY_SPEC_VERSION,
)


class PrecisionLevel(str, Enum):
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"

    @property
    def ordinal(self) -> int:
        """Return the coarseness rank: 1=finest, 3=coarsest."""
        return {"Level 1": 1, "Level 2": 2, "Level 3": 3}[self.value]


@dataclass(frozen=True)
class UBYAnchor:
    anchor_id: str
    anchor_iso: str
    anchor_jd: Decimal
    anchor_uby: Decimal
    model_version: str
    uby_version: str


@dataclass(frozen=True)
class UBYTime:
    uby_value: Decimal
    uby_version: str
    model_version: Optional[str]
    precision_level: PrecisionLevel
    source_time: Optional[str]
    source_system: Optional[str]
    rounding_rule: str
    generated_by: str
    anchor_id: str
    anchor_jd: Decimal
    anchor_uby: Decimal
    uncertainty_years: Optional[Decimal] = None
    confidence_level: Optional[Decimal] = None
    interval_start_uby: Optional[Decimal] = None
    interval_end_uby: Optional[Decimal] = None
    uncertainty_kind: Optional[str] = None
    propagation_note: Optional[str] = None

    # Magnitude shorthand pattern, e.g. "1G", "13.8G", "500M".
    _MAGNITUDE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*([KMGTP])$")

    @classmethod
    def _from_parsed_expression(cls, expression: str) -> "UBYTime":
        """Build a UBYTime from a full UBY expression via the canonical parser.

        The parser is the single source of truth for precision level and tags,
        so this method does not re-infer precision from the numeric magnitude.
        """
        from .parsing import parse_uby_expression

        parsed = parse_uby_expression(expression)
        return cls(
            uby_value=parsed.uby_value,
            uby_version=parsed.uby_version or UBY_SPEC_VERSION,
            model_version=parsed.model_version,
            precision_level=parsed.precision_level or PrecisionLevel.LEVEL_1,
            source_time=parsed.raw,
            source_system="UBYExpression",
            rounding_rule=DEFAULT_ROUNDING_RULE,
            generated_by=GENERATED_BY,
            anchor_id=DEFAULT_ANCHOR_ID,
            anchor_jd=DEFAULT_ANCHOR_JD,
            anchor_uby=DEFAULT_ANCHOR_UBY,
        )

    @classmethod
    def _from_magnitude_shorthand(cls, uby_str: str, match: "re.Match[str]") -> "UBYTime":
        """Build a UBYTime from magnitude shorthand such as ``13.8G``.

        Magnitude shorthand is, by specification, a Level 2 display form, so the
        precision level is assigned from the notation type rather than guessed
        from the numeric magnitude.
        """
        from .constants import MAGNITUDE_FACTORS

        numeric_value = Decimal(match.group(1))
        multiplier = MAGNITUDE_FACTORS.get(match.group(2), Decimal("1"))
        return cls(
            uby_value=numeric_value * multiplier,
            uby_version=UBY_SPEC_VERSION,
            model_version=DEFAULT_MODEL_VERSION,
            precision_level=PrecisionLevel.LEVEL_2,
            source_time=uby_str,
            source_system="UBYExpression",
            rounding_rule=DEFAULT_ROUNDING_RULE,
            generated_by=GENERATED_BY,
            anchor_id=DEFAULT_ANCHOR_ID,
            anchor_jd=DEFAULT_ANCHOR_JD,
            anchor_uby=DEFAULT_ANCHOR_UBY,
        )

    @staticmethod
    def from_uby_string(uby_str: str) -> "UBYTime":
        """Create a UBYTime from a UBY string.

        Supports three input shapes, tried in order:

        1. A full UBY expression beginning with ``UBY`` (delegated to the parser).
        2. Magnitude shorthand such as ``13.8G`` (Level 2 display form).
        3. A bare value or expression body, parsed by prefixing ``UBY ``.

        Precision level is always derived from the notation/parser, never from
        the numeric magnitude, in line with the specification rule that UBY does
        not infer precision from the size of the value.
        """
        from .errors import UBYParseError

        stripped = uby_str.strip()

        # Case 1: already a full UBY expression.
        if stripped.upper().startswith("UBY"):
            return UBYTime._from_parsed_expression(uby_str)

        # Case 2: magnitude shorthand, e.g. "13.8G".
        if match := UBYTime._MAGNITUDE_RE.match(stripped.upper()):
            return UBYTime._from_magnitude_shorthand(uby_str, match)

        # Case 3: treat the remainder as an expression body and let the parser
        # validate it. This covers bare numeric values and tagged bodies.
        try:
            return UBYTime._from_parsed_expression(f"UBY {stripped}")
        except UBYParseError as exc:
            raise ValueError(f"Cannot parse UBY string: {uby_str}") from exc

    def to_uby_string(self, simplified: bool = False) -> str:
        """Render this UBYTime as a UBY string.

        When ``simplified`` is requested (or the instance was created from
        magnitude shorthand), the original shorthand source is returned.
        Otherwise the canonical full-numeric form with ``[model=...]`` and
        ``[spec=...]`` tags is produced.
        """
        # Return the original shorthand form when applicable.
        if simplified or (self.source_time and not self.source_time.upper().startswith("UBY ")):
            if self.source_time and self._MAGNITUDE_RE.match(self.source_time.strip().upper()):
                return self.source_time

        # Default: full-numeric form with tags.
        result = f"UBY {self.uby_value}"
        tags = []
        if self.model_version:
            tags.append(f"[model={self.model_version}]")
        if self.uby_version:
            tags.append(f"[spec={self.uby_version}]")
        if tags:
            result += " " + " ".join(tags)
        return result

    @staticmethod
    def from_julian_day(jd: float) -> "UBYTime":
        """Create a UBYTime from a Julian Day value.

        Delegates to the reference ``jd_to_uby`` conversion, which returns a
        fully-populated UBYTime, so the JD is never mis-stored as the value.
        """
        from .conversion import jd_to_uby

        return jd_to_uby(
            Decimal(str(jd)),
            source_time=str(jd),
            source_system="JulianDay",
        )

    def to_julian_day(self) -> float:
        """Convert this UBYTime back to a Julian Day value."""
        from .conversion import uby_to_jd

        return float(uby_to_jd(self.uby_value))

    def with_uncertainty(self,
                        uncertainty_years: Optional[Decimal] = None,
                        confidence_level: Optional[Decimal] = None,
                        interval_start: Optional[Decimal] = None,
                        interval_end: Optional[Decimal] = None,
                        uncertainty_kind: Optional[str] = None) -> "UBYTime":
        """Return a copy of this UBYTime with uncertainty fields filled in.

        Any argument left as ``None`` preserves the current value of the
        corresponding field.

        Parameters
        ----------
        uncertainty_years : Decimal, optional
            Symmetric uncertainty in years.
        confidence_level : Decimal, optional
            Confidence level (e.g. 0.95).
        interval_start, interval_end : Decimal, optional
            Explicit lower/upper interval bounds in UBY years.
        uncertainty_kind : str, optional
            Kind of uncertainty (measurement, model, combined, ...).
        """
        return UBYTime(
            uby_value=self.uby_value,
            uby_version=self.uby_version,
            model_version=self.model_version,
            precision_level=self.precision_level,
            source_time=self.source_time,
            source_system=self.source_system,
            rounding_rule=self.rounding_rule,
            generated_by=self.generated_by,
            anchor_id=self.anchor_id,
            anchor_jd=self.anchor_jd,
            anchor_uby=self.anchor_uby,
            uncertainty_years=uncertainty_years if uncertainty_years is not None else self.uncertainty_years,
            confidence_level=confidence_level if confidence_level is not None else self.confidence_level,
            interval_start_uby=interval_start if interval_start is not None else self.interval_start_uby,
            interval_end_uby=interval_end if interval_end is not None else self.interval_end_uby,
            uncertainty_kind=uncertainty_kind if uncertainty_kind is not None else self.uncertainty_kind,
            propagation_note=self.propagation_note
        )

    def get_confidence_interval(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Return the (lower, upper) confidence interval in UBY years.

        An explicit interval takes precedence; otherwise a symmetric interval is
        derived from ``uncertainty_years``. Returns ``(None, None)`` if neither
        is available.
        """
        if self.interval_start_uby is not None and self.interval_end_uby is not None:
            return (self.interval_start_uby, self.interval_end_uby)
        elif self.uby_value is not None and self.uncertainty_years is not None:
            lower = self.uby_value - self.uncertainty_years
            upper = self.uby_value + self.uncertainty_years
            return (lower, upper)
        else:
            return (None, None)

    def get_relative_uncertainty(self) -> Optional[Decimal]:
        """Return the relative uncertainty as a percentage, or ``None``."""
        if self.uncertainty_years is not None and abs(self.uby_value) > Decimal('1e-10'):
            return (self.uncertainty_years / abs(self.uby_value)) * Decimal('100')
        return None

    def propagate_uncertainty_add(self, other: 'UBYTime') -> 'UBYTime':
        """Add two UBYTime values and propagate their uncertainties.

        Uncertainties are combined in quadrature (root-sum-of-squares). The
        result keeps the lower (coarser) precision level and the lower
        confidence level of the two operands.
        """
        from .uncertainty import decimal_sqrt

        # Combine uncertainties via root-sum-of-squares (RSS).
        unc1 = self.uncertainty_years or Decimal('0')
        unc2 = other.uncertainty_years or Decimal('0')

        combined_uncertainty = decimal_sqrt(unc1 ** 2 + unc2 ** 2)

        # Use the lower confidence level since multiple sources are combined.
        confidence = min(
            self.confidence_level or Decimal('0.68'),
            other.confidence_level or Decimal('0.68')
        )
        
        new_value = self.uby_value + other.uby_value
        
        return UBYTime(
            uby_value=new_value,
            uby_version=max(self.uby_version, other.uby_version),
            model_version=self.model_version or other.model_version,
            precision_level=max([self.precision_level, other.precision_level], key=lambda x: x.ordinal),
            source_time=f"Sum({self.source_time}, {other.source_time})",
            source_system="UncertaintyPropagation",
            rounding_rule=self.rounding_rule,
            generated_by=GENERATED_BY,
            anchor_id=self.anchor_id if self.anchor_id == other.anchor_id else DEFAULT_ANCHOR_ID,
            anchor_jd=self.anchor_jd if self.anchor_jd == other.anchor_jd else DEFAULT_ANCHOR_JD,
            anchor_uby=self.anchor_uby if self.anchor_uby == other.anchor_uby else DEFAULT_ANCHOR_UBY,
            uncertainty_years=combined_uncertainty,
            confidence_level=confidence,
            interval_start_uby=new_value - combined_uncertainty,
            interval_end_uby=new_value + combined_uncertainty,
            uncertainty_kind="propagated_addition",
            propagation_note=f"Propagated from addition of {self.uby_value}±{unc1} and {other.uby_value}±{unc2}"
        )

    def propagate_uncertainty_multiply(self, factor: Decimal) -> 'UBYTime':
        """Multiply this UBYTime by a scalar factor and propagate uncertainty.

        The relative uncertainty is preserved under scalar multiplication.
        """
        # Preserve relative uncertainty under scalar multiplication.
        if self.uncertainty_years and abs(self.uby_value) > Decimal('1e-10'):
            rel_uncertainty = self.uncertainty_years / abs(self.uby_value)
            new_abs_uncertainty = abs(factor) * rel_uncertainty * abs(self.uby_value)
        else:
            new_abs_uncertainty = Decimal('0')
        
        new_value = self.uby_value * factor
        
        return UBYTime(
            uby_value=new_value,
            uby_version=self.uby_version,
            model_version=self.model_version,
            precision_level=self.precision_level,
            source_time=f"Product({self.source_time}, {factor})",
            source_system="UncertaintyPropagation",
            rounding_rule=self.rounding_rule,
            generated_by=self.generated_by,
            anchor_id=self.anchor_id,
            anchor_jd=self.anchor_jd,
            anchor_uby=self.anchor_uby,
            uncertainty_years=new_abs_uncertainty,
            confidence_level=self.confidence_level,
            interval_start_uby=new_value - new_abs_uncertainty,
            interval_end_uby=new_value + new_abs_uncertainty,
            uncertainty_kind="propagated_multiplication",
            propagation_note=f"Propagated from multiplication of {self.uby_value}±{self.uncertainty_years or 0} by {factor}"
        )

    def get_effective_precision_level(self) -> str:
        """Return an effective precision level derived from relative uncertainty.

        This is a convenience heuristic for downstream display only; it does not
        override the declared ``precision_level`` of the record.
        """
        if self.uncertainty_years is None:
            return self.precision_level.value

        rel_uncertainty = (self.uncertainty_years / abs(self.uby_value)) * Decimal('100') if abs(self.uby_value) > Decimal('1e-10') else Decimal('0')

        # Map relative uncertainty to an effective precision level.
        if rel_uncertainty < Decimal('0.001'):  # < 0.001%
            return "Level 1"
        elif rel_uncertainty < Decimal('0.1'):   # < 0.1%
            return "Level 2"
        else:                                    # >= 0.1%
            return "Level 3"


@dataclass(frozen=True)
class ParsedUBYExpression:
    notation: str
    uby_value: Decimal
    model_version: Optional[str]
    uby_version: Optional[str]
    precision_level: Optional[PrecisionLevel]
    raw: str
    warnings: list[str] = field(default_factory=list)
    mnemonic_prefix: Optional[int] = None


@dataclass(frozen=True)
class ValidationMessage:
    code: str
    level: str
    message: str


@dataclass(frozen=True)
class UBYUncertainty:
    uncertainty_years: Optional[Decimal] = None
    confidence_level: Optional[Decimal] = None
    interval_start_uby: Optional[Decimal] = None
    interval_end_uby: Optional[Decimal] = None
    uncertainty_kind: Optional[str] = None
    propagation_note: Optional[str] = None
