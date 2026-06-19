from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping
from urllib.parse import quote

from .dataset_profiles import DatasetProfile, dataset_profile_to_dict
from .models import UBYTime
from .serialization import to_dict

UBY_NAMESPACE = "https://uby-time.org/ontology#"
UBY_RECORD_BASE = "https://uby-time.org/id/record/"
UBY_DATASET_PROFILE_BASE = "https://uby-time.org/id/dataset-profile/"

JSONLD_CONTEXT: dict[str, Any] = {
    "@version": 1.1,
    "uby": UBY_NAMESPACE,
    "time": "http://www.w3.org/2006/time#",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "https://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "uby_value": {"@id": "uby:ubyValue", "@type": "xsd:decimal"},
    "uby_expression": "uby:ubyExpression",
    "uby_magnitude_expression": "uby:ubyMagnitudeExpression",
    "uby_version": "uby:ubyVersion",
    "model_version": "uby:modelVersion",
    "precision_level": "uby:precisionLevel",
    "source_time": "uby:sourceTime",
    "source_system": "uby:sourceSystem",
    "rounding_rule": "uby:roundingRule",
    "generated_by": "prov:wasGeneratedBy",
    "anchor_id": "uby:anchorId",
    "anchor_jd": {"@id": "uby:anchorJulianDate", "@type": "xsd:decimal"},
    "anchor_uby": {"@id": "uby:anchorUbyValue", "@type": "xsd:decimal"},
    "uncertainty_years": {"@id": "uby:uncertaintyYears", "@type": "xsd:decimal"},
    "confidence_level": {"@id": "uby:confidenceLevel", "@type": "xsd:decimal"},
    "interval_start_uby": {"@id": "uby:intervalStartUby", "@type": "xsd:decimal"},
    "interval_end_uby": {"@id": "uby:intervalEndUby", "@type": "xsd:decimal"},
    "uncertainty_kind": "uby:uncertaintyKind",
    "propagation_note": "uby:propagationNote",
    "source_dataset": "schema:dataset",
    "source_record_id": "schema:identifier",
    "source_record_uri": {"@id": "schema:url", "@type": "@id"},
    "event_label": "schema:name",
    "event_type": "uby:eventType",
    "dataset_profile_id": "uby:datasetProfileId",
    "attribution": "schema:creditText",
    "profile_id": "uby:datasetProfileId",
    "authority": "schema:publisher",
    "source_uri": {"@id": "schema:url", "@type": "@id"},
    "allowed_precision_levels": "uby:allowedPrecisionLevel",
    "required_fields": "uby:requiredField",
    "recommended_fields": "uby:recommendedField",
    "source_time_fields": "uby:sourceTimeField",
    "representative_time_rule": "uby:representativeTimeRule",
    "uncertainty_policy": "uby:uncertaintyPolicy",
    "provenance_policy": "uby:provenancePolicy",
    "model_policy": "uby:modelPolicy",
    "requires_model_version": {"@id": "uby:requiresModelVersion", "@type": "xsd:boolean"},
    "requires_uncertainty_or_interval": {"@id": "uby:requiresUncertaintyOrInterval", "@type": "xsd:boolean"},
}


def _slug(value: str) -> str:
    safe = quote(value.strip().replace(" ", "-"), safe="-._~")
    return safe or "unknown"


def _record_id_from_uby(uby: UBYTime) -> str:
    return _slug(f"{uby.source_system or 'uby'}-{uby.source_time or uby.uby_value}")


def _jsonld_clean(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def uby_time_to_jsonld(uby: UBYTime, *, record_id: str | None = None) -> dict[str, Any]:
    """Convert a UBYTime record to JSON-LD.

    The JSON-LD representation keeps the same JSON-safe scalar fields as
    serialization.to_dict while adding a context, @id, and @type suitable for
    RDF tooling.
    """

    identifier = record_id or _record_id_from_uby(uby)
    payload = _jsonld_clean(to_dict(uby))
    return {
        "@context": JSONLD_CONTEXT,
        "@id": UBY_RECORD_BASE + _slug(identifier),
        "@type": "uby:UBYTimeRecord",
        **payload,
    }


def dataset_profile_to_jsonld(profile: DatasetProfile) -> dict[str, Any]:
    """Convert a dataset profile to JSON-LD."""

    payload = dataset_profile_to_dict(profile)
    return {
        "@context": JSONLD_CONTEXT,
        "@id": UBY_DATASET_PROFILE_BASE + _slug(profile.profile_id),
        "@type": "uby:DatasetProfile",
        **payload,
    }


def dataset_record_to_jsonld(record: Mapping[str, Any], *, record_id: str | None = None) -> dict[str, Any]:
    """Convert a UBY-annotated dataset row to JSON-LD."""

    identifier = record_id or str(record.get("source_record_id") or record.get("event_label") or "dataset-record")
    return {
        "@context": JSONLD_CONTEXT,
        "@id": UBY_RECORD_BASE + _slug(identifier),
        "@type": "uby:AnnotatedDatasetRecord",
        **_jsonld_clean(record),
    }


def _literal(value: Any) -> str:
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _decimal_literal(value: Decimal | str) -> str:
    return f'"{value}"^^xsd:decimal'


def uby_time_to_turtle(uby: UBYTime, *, record_id: str | None = None) -> str:
    """Render a compact Turtle representation for a UBYTime record.

    This is intentionally dependency-free and conservative.  Applications that
    need full RDF graph manipulation can load the emitted Turtle with rdflib.
    """

    identifier = record_id or _record_id_from_uby(uby)
    subject = f"ubyid:{_slug(identifier)}"

    triples = [
        "@prefix uby: <https://uby-time.org/ontology#> .",
        "@prefix ubyid: <https://uby-time.org/id/record/> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        f"{subject} a uby:UBYTimeRecord ;",
        f"    uby:ubyValue {_decimal_literal(uby.uby_value)} ;",
        f"    uby:ubyVersion {_literal(uby.uby_version)} ;",
        f"    uby:precisionLevel {_literal(uby.precision_level.value)} ;",
        f"    uby:sourceTime {_literal(uby.source_time or '')} ;",
        f"    uby:sourceSystem {_literal(uby.source_system or '')} ;",
        f"    uby:roundingRule {_literal(uby.rounding_rule)} ;",
        f"    prov:wasGeneratedBy {_literal(uby.generated_by)} ;",
        f"    uby:anchorId {_literal(uby.anchor_id)} ;",
        f"    uby:anchorJulianDate {_decimal_literal(uby.anchor_jd)} ;",
        f"    uby:anchorUbyValue {_decimal_literal(uby.anchor_uby)}",
    ]

    optional_predicates = [
        ("uby:modelVersion", uby.model_version, _literal),
        ("uby:uncertaintyYears", uby.uncertainty_years, _decimal_literal),
        ("uby:confidenceLevel", uby.confidence_level, _decimal_literal),
        ("uby:intervalStartUby", uby.interval_start_uby, _decimal_literal),
        ("uby:intervalEndUby", uby.interval_end_uby, _decimal_literal),
        ("uby:uncertaintyKind", uby.uncertainty_kind, _literal),
        ("uby:propagationNote", uby.propagation_note, _literal),
    ]

    for predicate, value, formatter in optional_predicates:
        if value is not None:
            triples.append(f"    ; {predicate} {formatter(value)}")

    triples[-1] += " ."
    return "\n".join(triples) + "\n"
