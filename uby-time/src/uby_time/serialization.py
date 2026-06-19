from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from .anchors import DEFAULT_ANCHOR
from .constants import DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from .models import PrecisionLevel, UBYTime


_DECIMAL_FIELDS = {
    "uby_value",
    "anchor_jd",
    "anchor_uby",
    "uncertainty_years",
    "confidence_level",
    "interval_start_uby",
    "interval_end_uby",
}


def _decimal_to_json(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _json_to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def to_dict(uby: UBYTime) -> dict[str, Any]:
    """Serialize a UBYTime object to a JSON-safe dictionary.

    Decimal values are emitted as strings to avoid float precision loss.
    """
    return {
        "uby_value": str(uby.uby_value),
        "uby_version": uby.uby_version,
        "model_version": uby.model_version,
        "precision_level": uby.precision_level.value,
        "source_time": uby.source_time,
        "source_system": uby.source_system,
        "rounding_rule": uby.rounding_rule,
        "generated_by": uby.generated_by,
        "anchor_id": uby.anchor_id,
        "anchor_jd": str(uby.anchor_jd),
        "anchor_uby": str(uby.anchor_uby),
        "uncertainty_years": _decimal_to_json(uby.uncertainty_years),
        "confidence_level": _decimal_to_json(uby.confidence_level),
        "interval_start_uby": _decimal_to_json(uby.interval_start_uby),
        "interval_end_uby": _decimal_to_json(uby.interval_end_uby),
        "uncertainty_kind": uby.uncertainty_kind,
        "propagation_note": uby.propagation_note,
    }


def from_dict(data: dict[str, Any]) -> UBYTime:
    precision_raw = data.get("precision_level", PrecisionLevel.LEVEL_1.value)
    precision_level = precision_raw if isinstance(precision_raw, PrecisionLevel) else PrecisionLevel(precision_raw)

    return UBYTime(
        uby_value=Decimal(str(data["uby_value"])),
        uby_version=str(data.get("uby_version") or UBY_SPEC_VERSION),
        model_version=data.get("model_version"),
        precision_level=precision_level,
        source_time=data.get("source_time"),
        source_system=data.get("source_system"),
        rounding_rule=str(data.get("rounding_rule") or DEFAULT_ROUNDING_RULE),
        generated_by=str(data.get("generated_by") or GENERATED_BY),
        anchor_id=str(data.get("anchor_id") or DEFAULT_ANCHOR.anchor_id),
        anchor_jd=Decimal(str(data.get("anchor_jd") or DEFAULT_ANCHOR.anchor_jd)),
        anchor_uby=Decimal(str(data.get("anchor_uby") or DEFAULT_ANCHOR.anchor_uby)),
        uncertainty_years=_json_to_decimal(data.get("uncertainty_years")),
        confidence_level=_json_to_decimal(data.get("confidence_level")),
        interval_start_uby=_json_to_decimal(data.get("interval_start_uby")),
        interval_end_uby=_json_to_decimal(data.get("interval_end_uby")),
        uncertainty_kind=data.get("uncertainty_kind"),
        propagation_note=data.get("propagation_note"),
    )


def to_json(uby: UBYTime, *, indent: int | None = None) -> str:
    return json.dumps(to_dict(uby), ensure_ascii=False, indent=indent)


def from_json(text: str) -> UBYTime:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("UBY JSON payload must be an object")
    return from_dict(data)
