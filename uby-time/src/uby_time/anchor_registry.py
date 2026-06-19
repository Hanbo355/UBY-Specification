from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .anchors import DEFAULT_ANCHOR
from .models import UBYAnchor, UBYTime, ValidationMessage


@dataclass(frozen=True)
class AnchorCompatibilityMapping:
    """Compatibility metadata between two UBY anchors."""

    source_anchor_id: str
    target_anchor_id: str
    offset_years: Decimal
    mapping_rule: str
    compatibility_note: str


ANCHOR_REGISTRY: dict[str, UBYAnchor] = {
    DEFAULT_ANCHOR.anchor_id: DEFAULT_ANCHOR,
}

ANCHOR_COMPATIBILITY_MAPPINGS: dict[tuple[str, str], AnchorCompatibilityMapping] = {
    (DEFAULT_ANCHOR.anchor_id, DEFAULT_ANCHOR.anchor_id): AnchorCompatibilityMapping(
        source_anchor_id=DEFAULT_ANCHOR.anchor_id,
        target_anchor_id=DEFAULT_ANCHOR.anchor_id,
        offset_years=Decimal("0"),
        mapping_rule="identity",
        compatibility_note="Same anchor; no conversion is required.",
    )
}


def register_anchor(anchor: UBYAnchor) -> None:
    """Register an anchor for compatibility checks.

    The registry is intentionally in-memory for the reference implementation.
    Serialized records must still carry their own anchor fields.
    """

    ANCHOR_REGISTRY[anchor.anchor_id] = anchor
    ANCHOR_COMPATIBILITY_MAPPINGS[(anchor.anchor_id, anchor.anchor_id)] = AnchorCompatibilityMapping(
        source_anchor_id=anchor.anchor_id,
        target_anchor_id=anchor.anchor_id,
        offset_years=Decimal("0"),
        mapping_rule="identity",
        compatibility_note="Same anchor; no conversion is required.",
    )


def get_anchor(anchor_id: str) -> UBYAnchor:
    try:
        return ANCHOR_REGISTRY[anchor_id]
    except KeyError as exc:
        raise ValueError(f"Unknown UBY anchor: {anchor_id}") from exc


def register_anchor_mapping(mapping: AnchorCompatibilityMapping) -> None:
    ANCHOR_COMPATIBILITY_MAPPINGS[(mapping.source_anchor_id, mapping.target_anchor_id)] = mapping


def get_anchor_mapping(source_anchor_id: str, target_anchor_id: str) -> AnchorCompatibilityMapping:
    try:
        return ANCHOR_COMPATIBILITY_MAPPINGS[(source_anchor_id, target_anchor_id)]
    except KeyError as exc:
        raise ValueError(f"No compatibility mapping from {source_anchor_id!r} to {target_anchor_id!r}") from exc


def are_anchors_compatible(source_anchor_id: str, target_anchor_id: str) -> bool:
    return (source_anchor_id, target_anchor_id) in ANCHOR_COMPATIBILITY_MAPPINGS


def validate_anchor_compatibility(uby: UBYTime, *, target_anchor: UBYAnchor = DEFAULT_ANCHOR) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []

    if uby.anchor_id not in ANCHOR_REGISTRY:
        messages.append(
            ValidationMessage(
                "ANCHOR_NOT_REGISTERED",
                "error",
                f"anchor_id={uby.anchor_id!r} is not registered.",
            )
        )
        return messages

    registered = ANCHOR_REGISTRY[uby.anchor_id]
    if uby.anchor_jd != registered.anchor_jd:
        messages.append(
            ValidationMessage(
                "ANCHOR_JD_MISMATCH",
                "error",
                f"Record anchor_jd={uby.anchor_jd} differs from registered anchor_jd={registered.anchor_jd}.",
            )
        )

    if uby.anchor_uby != registered.anchor_uby:
        messages.append(
            ValidationMessage(
                "ANCHOR_UBY_MISMATCH",
                "error",
                f"Record anchor_uby={uby.anchor_uby} differs from registered anchor_uby={registered.anchor_uby}.",
            )
        )

    if not are_anchors_compatible(uby.anchor_id, target_anchor.anchor_id):
        messages.append(
            ValidationMessage(
                "ANCHOR_COMPATIBILITY_MAPPING_MISSING",
                "error",
                f"No compatibility mapping from {uby.anchor_id!r} to {target_anchor.anchor_id!r}.",
            )
        )

    return messages


def reanchor_uby_value(uby_value: Decimal, mapping: AnchorCompatibilityMapping) -> Decimal:
    """Convert a UBY value with an explicit compatibility mapping.

    Positive offset_years means target_anchor_uby = source_anchor_uby + offset.
    The mapping is purely conventional and must be registered explicitly.
    """

    return uby_value + mapping.offset_years


def anchor_to_dict(anchor: UBYAnchor) -> dict[str, Any]:
    return {
        "anchor_id": anchor.anchor_id,
        "anchor_iso": anchor.anchor_iso,
        "anchor_jd": str(anchor.anchor_jd),
        "anchor_uby": str(anchor.anchor_uby),
        "model_version": anchor.model_version,
        "uby_version": anchor.uby_version,
    }


def anchor_mapping_to_dict(mapping: AnchorCompatibilityMapping) -> dict[str, str]:
    return {
        "source_anchor_id": mapping.source_anchor_id,
        "target_anchor_id": mapping.target_anchor_id,
        "offset_years": str(mapping.offset_years),
        "mapping_rule": mapping.mapping_rule,
        "compatibility_note": mapping.compatibility_note,
    }
