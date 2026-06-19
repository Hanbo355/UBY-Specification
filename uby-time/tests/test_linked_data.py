from __future__ import annotations

from uby_time import (
    JSONLD_CONTEXT,
    USGS_EARTHQUAKE_PROFILE,
    dataset_profile_to_jsonld,
    dataset_record_to_jsonld,
    iso_to_uby,
    uby_time_to_jsonld,
    uby_time_to_turtle,
)


def test_uby_time_to_jsonld_preserves_serialized_fields_and_context() -> None:
    uby = iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False)

    payload = uby_time_to_jsonld(uby, record_id="anchor")

    assert payload["@context"] is JSONLD_CONTEXT
    assert payload["@id"] == "https://uby-time.org/id/record/anchor"
    assert payload["@type"] == "uby:UBYTimeRecord"
    assert payload["uby_value"] == str(uby.uby_value)
    assert payload["source_time"] == "2026-01-01T00:00:00Z"
    assert payload["anchor_id"] == "UBY-ANCHOR-2026-01-01Z"
    assert "uby_value" in payload["@context"]
    assert payload["@context"]["prov"] == "http://www.w3.org/ns/prov#"


def test_dataset_profile_to_jsonld_serializes_profile() -> None:
    payload = dataset_profile_to_jsonld(USGS_EARTHQUAKE_PROFILE)

    assert payload["@id"].endswith("UBY-DATASET-USGS-EARTHQUAKE-WD-0.1.0")
    assert payload["@type"] == "uby:DatasetProfile"
    assert payload["profile_id"] == "UBY-DATASET-USGS-EARTHQUAKE-WD-0.1.0"
    assert payload["allowed_precision_levels"] == ["Level 1"]
    assert payload["uby_version"] == "0.1.0"


def test_dataset_record_to_jsonld_uses_source_record_id() -> None:
    record = {
        "dataset_profile_id": "UBY-DATASET-USGS-EARTHQUAKE-WD-0.1.0",
        "source_record_id": "usc000lv5e",
        "event_label": "USGS earthquake usc000lv5e",
        "event_type": "earthquake_event_time",
        "uby_value": "13787002014.00000242762440743",
    }

    payload = dataset_record_to_jsonld(record)

    assert payload["@id"] == "https://uby-time.org/id/record/usc000lv5e"
    assert payload["@type"] == "uby:AnnotatedDatasetRecord"
    assert payload["dataset_profile_id"] == "UBY-DATASET-USGS-EARTHQUAKE-WD-0.1.0"


def test_uby_time_to_turtle_emits_compact_rdf() -> None:
    uby = iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False)

    turtle = uby_time_to_turtle(uby, record_id="anchor")

    assert "@prefix uby:" in turtle
    assert "@prefix prov:" in turtle
    assert "ubyid:anchor a uby:UBYTimeRecord" in turtle
    assert 'uby:ubyValue "13787002026.0"^^xsd:decimal' in turtle
    assert 'uby:sourceTime "2026-01-01T00:00:00Z"' in turtle
    assert 'prov:wasGeneratedBy "uby-time/0.1.0"' in turtle
    assert turtle.endswith(" .\n")
