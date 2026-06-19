from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from uby_time import (
    astronomical_year_to_uby,
    bc_year_to_uby,
    format_academic_mnemonic,
    format_full,
    iso_to_uby,
    parse_uby_expression,
    uby_to_jd,
)
from uby_time.serialization import from_dict, to_dict

ROOT = Path(__file__).resolve().parents[1]
VECTORS_PATH = ROOT / "tests" / "fixtures" / "uby_wd_0_1_0_interop_vectors.json"
SCHEMA_PATH = ROOT / "schemas" / "uby-time-wd-0.1.0.schema.json"


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


def _validate_record_against_schema(record: dict[str, Any], schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"

    required = set(schema["required"])
    assert required <= set(record), f"missing required fields: {sorted(required - set(record))}"

    if schema.get("additionalProperties") is False:
        allowed = set(schema["properties"])
        assert set(record) <= allowed, f"unexpected fields: {sorted(set(record) - allowed)}"

    for key, value in record.items():
        _validate_value(value, schema["properties"][key], schema, key)


def test_schema_structure_matches_serialized_uby_time_records() -> None:
    schema = _load_json(SCHEMA_PATH)

    assert schema["title"] == "UBY Time JSON Record"
    assert schema["additionalProperties"] is False
    assert "uby_value" in schema["required"]
    assert "precision_level" in schema["properties"]
    assert schema["properties"]["precision_level"]["enum"] == ["Level 1", "Level 2", "Level 3"]
    assert schema["$defs"]["modelVersion"]["pattern"] == r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+$"
    assert schema["$defs"]["specVersion"]["pattern"] == r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?$"


def test_serialized_records_validate_against_lightweight_schema() -> None:
    schema = _load_json(SCHEMA_PATH)

    records = [
        iso_to_uby("2026-01-01T00:00:00Z", prefer_astropy=False),
        iso_to_uby("2000-01-01T00:00:00Z", prefer_astropy=False),
        astronomical_year_to_uby(1, include_model=True),
        bc_year_to_uby(221, include_model=True),
    ]

    for uby in records:
        payload = to_dict(uby)
        _validate_record_against_schema(payload, schema)
        round_tripped = from_dict(payload)
        assert round_tripped == uby


def test_interoperability_vectors_are_stable() -> None:
    vectors = _load_json(VECTORS_PATH)
    ids = [vector["id"] for vector in vectors]

    assert len(ids) == len(set(ids)), "interop vector ids must be unique"
    assert len(vectors) >= 10

    for vector in vectors:
        kind = vector["kind"]

        if kind == "iso":
            uby = iso_to_uby(vector["source_time"], prefer_astropy=False)
            assert str(uby.uby_value) == vector["expected_uby_value"]
            assert abs(uby_to_jd(uby.uby_value) - Decimal(vector["expected_jd"])) < Decimal("1e-12")
            assert uby.precision_level.value == vector["expected_precision_level"]
            assert uby.model_version == vector["expected_model_version"]
            assert uby.uby_version == vector["expected_uby_version"]
            assert format_full(uby) == vector["expected_expression"]

        elif kind == "astronomical_year":
            uby = astronomical_year_to_uby(vector["astronomical_year"], include_model=True)
            assert str(uby.uby_value) == vector["expected_uby_value"]
            assert uby.precision_level.value == vector["expected_precision_level"]
            assert uby.model_version == vector["expected_model_version"]
            assert uby.uby_version == vector["expected_uby_version"]
            assert format_academic_mnemonic(vector["astronomical_year"]) == vector["expected_mnemonic"]

        elif kind == "bc_year":
            uby = bc_year_to_uby(vector["bc_year"], include_model=True)
            assert vector["astronomical_year"] == 1 - vector["bc_year"]
            assert str(uby.uby_value) == vector["expected_uby_value"]
            assert uby.precision_level.value == vector["expected_precision_level"]
            assert uby.model_version == vector["expected_model_version"]
            assert uby.uby_version == vector["expected_uby_version"]
            assert format_academic_mnemonic(vector["astronomical_year"]) == vector["expected_mnemonic"]

        elif kind == "expression":
            parsed = parse_uby_expression(vector["expression"])
            assert parsed.notation == vector["expected_notation"]
            assert parsed.uby_value == Decimal(vector["expected_uby_value"])
            assert parsed.precision_level is not None
            assert parsed.precision_level.value == vector["expected_precision_level"]
            assert parsed.model_version == vector["expected_model_version"]
            assert parsed.uby_version == vector["expected_uby_version"]
            assert parsed.warnings == vector["expected_warnings"]
            if "expected_mnemonic_prefix" in vector:
                assert parsed.mnemonic_prefix == vector["expected_mnemonic_prefix"]

        else:
            raise AssertionError(f"unknown interop vector kind: {kind}")


def test_interoperability_vectors_file_has_portable_shape() -> None:
    vectors = _load_json(VECTORS_PATH)

    for vector in vectors:
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", vector["id"])
        assert vector["kind"] in {"iso", "astronomical_year", "bc_year", "expression"}
        assert "expected_uby_value" in vector
        assert isinstance(vector["expected_uby_value"], str)
        assert Decimal(vector["expected_uby_value"]) >= 0

        if vector["kind"] == "expression":
            assert vector["expression"].startswith("UBY ")
            assert isinstance(vector["expected_warnings"], list)
