from decimal import Decimal

from .constants import (
    DEFAULT_ANCHOR_ID,
    DEFAULT_ANCHOR_ISO,
    DEFAULT_ANCHOR_JD,
    DEFAULT_ANCHOR_UBY,
    DEFAULT_MODEL_VERSION,
    UBY_SPEC_VERSION,
)
from .models import UBYAnchor

DEFAULT_ANCHOR = UBYAnchor(
    anchor_id=DEFAULT_ANCHOR_ID,
    anchor_iso=DEFAULT_ANCHOR_ISO,
    anchor_jd=Decimal(DEFAULT_ANCHOR_JD),
    anchor_uby=Decimal(DEFAULT_ANCHOR_UBY),
    model_version=DEFAULT_MODEL_VERSION,
    uby_version=UBY_SPEC_VERSION,
)
