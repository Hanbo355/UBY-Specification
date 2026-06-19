from __future__ import annotations

from decimal import Decimal

from uby_time import (
    DEFAULT_ANCHOR,
    AnchorCompatibilityMapping,
    UBYAnchor,
    anchor_mapping_to_dict,
    anchor_to_dict,
    are_anchors_compatible,
    get_anchor,
    get_anchor_mapping,
    iso_to_uby,
    reanchor_uby_value,
    register_anchor,
    register_anchor_mapping,
    validate_anchor_compatibility,
)


def test_default_anchor_is_registered_and_identity_mapping_exists() -> None:
    anchor = get_anchor(DEFAULT_ANCHOR.anchor_id)
    mapping = get_anchor_mapping(DEFAULT_ANCHOR.anchor_id, DEFAULT_ANCHOR.anchor_id)

    assert anchor == DEFAULT_ANCHOR
    assert mapping.offset_years == Decimal("0")
    assert are_anchors_compatible(DEFAULT_ANCHOR.anchor_id, DEFAULT_ANCHOR.anchor_id) is True
    assert anchor_to_dict(anchor)["anchor_uby"] == "13787002026.0"
    assert anchor_mapping_to_dict(mapping)["mapping_rule"] == "identity"


def test_register_anchor_and_mapping_supports_explicit_reanchoring() -> None:
    alternate = UBYAnchor(
        anchor_id="UBY-ANCHOR-2030-01-01Z",
        anchor_iso="2030-01-01T00:00:00Z",
        anchor_jd=Decimal("2462502.5"),
        anchor_uby=Decimal("13787002030.0"),
        model_version="LCDM-Planck2018",
        uby_version="0.1.0",
    )
    register_anchor(alternate)

    mapping = AnchorCompatibilityMapping(
        source_anchor_id=DEFAULT_ANCHOR.anchor_id,
        target_anchor_id=alternate.anchor_id,
        offset_years=Decimal("4"),
        mapping_rule="declared-anchor-offset",
        compatibility_note="Test mapping only.",
    )
    register_anchor_mapping(mapping)

    assert get_anchor(alternate.anchor_id) == alternate
    assert get_anchor_mapping(DEFAULT_ANCHOR.anchor_id, alternate.anchor_id) == mapping
    assert reanchor_uby_value(Decimal("13787002026.0"), mapping) == Decimal("13787002030.0")


def test_validate_anchor_compatibility_accepts_default_record() -> None:
    uby = iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False)

    assert validate_anchor_compatibility(uby) == []


def test_validate_anchor_compatibility_detects_mismatch() -> None:
    uby = iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False)
    broken = type(uby)(
        **{
            **uby.__dict__,
            "anchor_jd": Decimal("1"),
            "anchor_uby": Decimal("2"),
        }
    )

    codes = {message.code for message in validate_anchor_compatibility(broken)}

    assert "ANCHOR_JD_MISMATCH" in codes
    assert "ANCHOR_UBY_MISMATCH" in codes
