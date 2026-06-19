from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from uby_time.dataset_profiles import USGS_EARTHQUAKE_PROFILE, dataset_profile_to_dict

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "uby-dataset-profile-wd-0.1.0.schema.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    assert ref.startswith("#/")
    node: Any = schema
    for part in ref[2:].split("/"):
        node = node[part]
    assert isinstance(node, dict)
    return node


def _matches_type(value: Any, type_spec: str | list[str]) -> bool:
    types = [type_spec] if isinstance(type_spec, str) else type_spec
    for type_name in types:
        if type_name == "null" and value is None:
            return True
        if type_name == "string" and isinstance(value, str):
            return True
        if type_name == "object" and isinstance(value, dict):
            return True
        if type_name == "array" and isinstance(value, list):
            return True
        if type_name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if type_name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if type_name == "boolean" and isinstance(value, bool):
            return True
    return False


def _validate_value(value: Any, rule: dict[str, Any], schema: dict[str, Any], path: str) -> None:
    if "$ref" in rule:
        _validate_value(value, _resolve_ref(schema, rule["$ref"]), schema, path)
        return

    if "anyOf" in rule:
        errors: list[AssertionError] = []
        for branch in rule["anyOf"]:
            try:
                _validate_value(value, branch, schema, path)
                return
            except AssertionError as exc:
                errors.append(exc)
        raise AssertionError(f"{path} did not match anyOf: {errors}")

    if "type" in rule:
        assert _matches_type(value, rule["type"]), f"{path} has invalid type: {type(value).__name__}"

    if value is None:
        return

    if "enum" in rule:
        assert value in rule["enum"], f"{path}={value!r} not in enum {rule['enum']!r}"

    if "minLength" in rule and isinstance(value, str):
        assert len(value) >= rule["minLength"], f"{path} is shorter than minLength"

    if "pattern" in rule and isinstance(value, str):
        assert re.fullmatch(rule["pattern"], value), f"{path}={value!r} does not match {rule['pattern']!r}"

    if "items" in rule and isinstance(value, list):
        for index, item in enumerate(value):
            _validate_value(item, rule["items"], schema, f"{path}[{index}]")

    if "minItems" in rule and isinstance(value, list):
        assert len(value) >= rule["minItems"], f"{path} has too few items"

    if rule.get("uniqueItems") is True and isinstance(value, list):
        assert len(value) == len(set(value)), f"{path} has duplicate items"


def _validate_object_against_def(record: dict[str, Any], schema: dict[str, Any], def_name: str) -> None:
    rule = schema["$defs"][def_name]
    assert rule["type"] == "object"

    required = set(rule["required"])
    assert required <= set(record), f"missing required fields: {sorted(required - set(record))}"

    if rule.get("additionalProperties") is False:
        allowed = set(rule["properties"])
        assert set(record) <= allowed, f"unexpected fields: {sorted(set(record) - allowed)}"

    for key, value in record.items():
        if key in rule["properties"]:
            _validate_value(value, rule["properties"][key], schema, key)


def test_dataset_profile_schema_has_required_defs() -> None:
    schema = _load_json(SCHEMA_PATH)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "UBY Dataset Profile and Annotated Dataset Record"
    assert "datasetProfile" in schema["$defs"]
    assert "annotatedDatasetRecord" in schema["$defs"]
    assert schema["$defs"]["precisionLevel"]["enum"] == ["Level 1", "Level 2", "Level 3"]


def test_builtin_dataset_profile_serializes_against_schema() -> None:
    schema = _load_json(SCHEMA_PATH)
    payload = dataset_profile_to_dict(USGS_EARTHQUAKE_PROFILE)

    _validate_object_against_def(payload, schema, "datasetProfile")


def test_annotated_dataset_record_shape_validates_against_schema() -> None:
    schema = _load_json(SCHEMA_PATH)
    record = {
        "dataset_profile_id": "UBY-DATASET-USGS-EARTHQUAKE-WD-0.1.0",
        "source_dataset": "USGS Earthquake Catalog",
        "source_record_id": "usc000lv5e",
        "source_record_uri": "https://earthquake.usgs.gov/earthquakes/eventpage/usc000lv5e",
        "event_label": "USGS earthquake usc000lv5e",
        "event_type": "earthquake_event_time",
        "source_time": "2014-01-01T00:01:16.610Z",
        "source_system": "USGS Earthquake Catalog UTC event time",
        "uby_value": "13787002014.00000242762440743",
        "uby_expression": "UBY 13787002014.00000242762440743 [model=LCDM-Planck2018] [spec=0.1.0]",
        "uby_magnitude_expression": "UBY 13.787G [model=LCDM-Planck2018] [spec=0.1.0]",
        "uby_version": "0.1.0",
        "model_version": "LCDM-Planck2018",
        "precision_level": "Level 1",
        "anchor_id": "UBY-ANCHOR-2026-01-01Z",
        "anchor_jd": "2461041.5",
        "anchor_uby": "13787002026.0",
        "rounding_rule": "year-floor",
        "generated_by": "uby-time/0.1.0",
        "uncertainty_years": None,
        "confidence_level": None,
        "interval_start_uby": None,
        "interval_end_uby": None,
        "uncertainty_kind": None,
        "propagation_note": "stdlib conversion path",
        "validation_messages": "[]",
        "attribution": "Data from the U.S. Geological Survey (USGS) Earthquake Catalog.",
    }

    _validate_object_against_def(record, schema, "annotatedDatasetRecord")
