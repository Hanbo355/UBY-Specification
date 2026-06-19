from __future__ import annotations

import re
from decimal import Decimal

from .constants import MAGNITUDE_FACTORS, MODEL_MNEMONIC_PREFIX
from .errors import UBYParseError
from .models import ParsedUBYExpression, PrecisionLevel
from .utils import to_decimal

MODEL_PATTERN = r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+"
SPEC_PATTERN = r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?"
TAGS_PATTERN = rf"(?: \[model=(?P<model>{MODEL_PATTERN})\])?(?: \[spec=(?P<spec>{SPEC_PATTERN})\])?"

FULL_RE = re.compile(rf"^UBY (?P<value>\d+(?:\.\d+)?){TAGS_PATTERN}$")
MAG_RE = re.compile(rf"^UBY (?P<value>\d+(?:\.\d+)?)(?P<mag>[KMGT]){TAGS_PATTERN}$")
SCI_RE = re.compile(rf"^UBY (?P<coef>\d+(?:\.\d+)?)(?:x|×)10\^(?P<exp>-?\d+){TAGS_PATTERN}$")
MNEMONIC_RE = re.compile(rf"^UBY (?P<prefix>\d{{6}})(?P<sign>[+-])(?P<year>\d{{6}}){TAGS_PATTERN}$")
FRIENDLY_RE = re.compile(rf"^UBY (?P<prefix>\d{{6}}) (?P<era>AD|BC)(?P<year>\d+){TAGS_PATTERN}$")


def _warnings(
    model: str | None,
    spec: str | None,
    precision: PrecisionLevel | None,
    *,
    mnemonic_prefix: int | None = None,
) -> list[str]:
    warnings: list[str] = []
    if spec is None:
        warnings.append("SPEC_VERSION_UNDECLARED")
    if precision in {PrecisionLevel.LEVEL_2, PrecisionLevel.LEVEL_3} and model is None:
        warnings.append("MODEL_VERSION_REQUIRED")
    if mnemonic_prefix is not None and model in MODEL_MNEMONIC_PREFIX:
        if MODEL_MNEMONIC_PREFIX[model] != mnemonic_prefix:
            warnings.append("MNEMONIC_MODEL_MISMATCH")
    return warnings


def parse_uby_expression(expression: str) -> ParsedUBYExpression:
    raw = expression
    expression = expression.strip()

    if match := FULL_RE.match(expression):
        value = to_decimal(match.group("value"))
        model = match.group("model")
        spec = match.group("spec")
        precision = PrecisionLevel.LEVEL_1
        return ParsedUBYExpression("full-numeric", value, model, spec, precision, raw, _warnings(model, spec, precision))

    if match := MAG_RE.match(expression):
        value = to_decimal(match.group("value")) * MAGNITUDE_FACTORS[match.group("mag")]
        model = match.group("model")
        spec = match.group("spec")
        precision = PrecisionLevel.LEVEL_2
        return ParsedUBYExpression(
            "magnitude",
            value,
            model,
            spec,
            precision,
            raw,
            _warnings(model, spec, precision) + ["MAGNITUDE_NOT_FOR_STORAGE"],
        )

    if match := SCI_RE.match(expression):
        value = to_decimal(match.group("coef")) * (Decimal(10) ** int(match.group("exp")))
        model = match.group("model")
        spec = match.group("spec")
        precision = PrecisionLevel.LEVEL_2
        return ParsedUBYExpression(
            "scientific",
            value,
            model,
            spec,
            precision,
            raw,
            _warnings(model, spec, precision) + ["SIGNIFICANT_DIGITS_UNDECLARED"],
        )

    if match := MNEMONIC_RE.match(expression):
        prefix = int(match.group("prefix"))
        year = int(match.group("year"))
        sign = match.group("sign")
        astronomical_year = year if sign == "+" else -year
        value = Decimal(prefix) * Decimal("100000") + Decimal(astronomical_year)
        model = match.group("model")
        spec = match.group("spec")
        precision = PrecisionLevel.LEVEL_1
        return ParsedUBYExpression(
            "academic-mnemonic",
            value,
            model,
            spec,
            precision,
            raw,
            _warnings(model, spec, precision, mnemonic_prefix=prefix),
            prefix,
        )

    if match := FRIENDLY_RE.match(expression):
        prefix = int(match.group("prefix"))
        era = match.group("era")
        year = int(match.group("year"))
        astronomical_year = year if era == "AD" else 1 - year
        value = Decimal(prefix) * Decimal("100000") + Decimal(astronomical_year)
        model = match.group("model")
        spec = match.group("spec")
        precision = PrecisionLevel.LEVEL_1
        return ParsedUBYExpression(
            "friendly-mnemonic",
            value,
            model,
            spec,
            precision,
            raw,
            _warnings(model, spec, precision, mnemonic_prefix=prefix),
            prefix,
        )

    raise UBYParseError(f"Invalid UBY expression: {raw}")
