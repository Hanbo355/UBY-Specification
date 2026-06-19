from __future__ import annotations

from decimal import Decimal

from .constants import DEFAULT_LEVEL1_RANGE_YEARS
from .models import PrecisionLevel


def infer_precision_level(
    uby_value: Decimal,
    *,
    anchor_uby: Decimal,
    source_system: str | None = None,
    model_version: str | None = None,
) -> PrecisionLevel:
    """Infer a conservative precision level from value and context.

    This is a helper, not a substitute for explicit domain metadata.
    """
    if source_system == "CosmologicalRedshift":
        return PrecisionLevel.LEVEL_3

    if abs(uby_value - anchor_uby) <= Decimal(DEFAULT_LEVEL1_RANGE_YEARS):
        return PrecisionLevel.LEVEL_1

    if model_version:
        return PrecisionLevel.LEVEL_2

    return PrecisionLevel.LEVEL_2
