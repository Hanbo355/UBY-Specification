#!/usr/bin/env python3
"""
Annotate the downloaded ICS Chronostratigraphic Chart RDF data with UBY labels.

This script intentionally uses only the Python standard library plus uby-time.
It is a lightweight extraction path for the downloaded Turtle files when rdflib
is not installed.

Normative UBY principles applied:
- preserve the native ICS geologic time fields;
- add UBY only as an auxiliary cross-scale index;
- keep model/spec/anchor/rounding metadata with every generated record;
- treat geologic Ma/BP data as approximate and avoid inventing extra precision;
- keep source and license attribution in the generated metadata sidecar.
"""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.anchors import DEFAULT_ANCHOR
from uby_time.constants import (  # noqa: E402
    DEFAULT_MNEMONIC_PREFIX,
    DEFAULT_MODEL_VERSION,
    DEFAULT_ROUNDING_RULE,
    GENERATED_BY,
    UBY_SPEC_VERSION,
)
from uby_time.formatting import format_full, format_magnitude  # noqa: E402
from uby_time.models import PrecisionLevel, UBYTime  # noqa: E402
from uby_time.utils import decimal_to_plain_text  # noqa: E402
from uby_time.validation import validate_uby_time  # noqa: E402

RAW_TTL = ROOT / "data" / "raw" / "ics-chart" / "supermodel" / "datasets" / "gts2020.ttl"
PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "ics_chart_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "ics_chart_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "ics_chart_uby_metadata.json"

ICS_BASE_URI = "http://resource.geosciml.org/classifier/ics/ischart/"
MODEL_BASE_UBY = Decimal(DEFAULT_MNEMONIC_PREFIX) * Decimal("100000")


@dataclass(frozen=True)
class TimePosition:
    subject: str
    numeric_position: Decimal
    trs: str
    uncertainty_ref: str | None


@dataclass(frozen=True)
class Boundary:
    subject: str
    label: str
    time_position_ref: str


@dataclass(frozen=True)
class AnnotatedBoundary:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    original_time_value: str
    original_time_unit: str
    source_system: str
    years_before_present: str
    uncertainty_years: str | None
    precision_level: str
    uby_value: str
    uby_expression: str
    uby_magnitude_expression: str
    model_version: str
    uby_version: str
    anchor_id: str
    anchor_jd: str
    anchor_uby: str
    rounding_rule: str
    generated_by: str
    validation_messages: str
    attribution: str


def _split_turtle_blocks(text: str) -> list[str]:
    """Split a simple Turtle file into subject blocks.

    The ICS file is regular enough for this extraction path: each resource block
    ends with a line containing ".".
    """
    return [block.strip() for block in re.split(r"\n\.\s*\n", text) if block.strip()]


def _subject(block: str) -> str | None:
    match = re.match(r"^(ischart:[A-Za-z0-9_.-]+)\s*$", block.splitlines()[0].strip())
    return match.group(1) if match else None


def _english_pref_label(block: str) -> str | None:
    labels = re.findall(r'skos:prefLabel\s+"([^"]+)"@en', block)
    if labels:
        return labels[0].strip()
    labels = re.findall(r'skos:prefLabel\s*\n(?:\s+"[^"]+"@[a-z]+\s*,\n)*\s+"([^"]+)"@en', block)
    return labels[0].strip() if labels else None


def _parse_time_positions(blocks: Iterable[str]) -> dict[str, TimePosition]:
    positions: dict[str, TimePosition] = {}

    for block in blocks:
        subj = _subject(block)
        if not subj or "time:TimePosition" not in block or "time:numericPosition" not in block:
            continue

        numeric_match = re.search(r"time:numericPosition\s+([0-9]+(?:\.[0-9]+)?)\s*;", block)
        trs_match = re.search(r"time:hasTRS\s+<([^>]+)>\s*;", block)
        uncertainty_match = re.search(r"gts:positionalUncertainty\s+(ischart:[A-Za-z0-9_.-]+)\s*;", block)

        if not numeric_match or not trs_match:
            continue

        positions[subj] = TimePosition(
            subject=subj,
            numeric_position=Decimal(numeric_match.group(1)),
            trs=trs_match.group(1),
            uncertainty_ref=uncertainty_match.group(1) if uncertainty_match else None,
        )

    return positions


def _parse_uncertainties(blocks: Iterable[str]) -> dict[str, Decimal]:
    uncertainties: dict[str, Decimal] = {}

    for block in blocks:
        subj = _subject(block)
        if not subj or "time:Duration" not in block or "time:numericDuration" not in block:
            continue

        duration_match = re.search(r"time:numericDuration\s+([0-9]+(?:\.[0-9]+)?)\s*;", block)
        unit_is_ma = "time:unitType ucum-ma:" in block
        if duration_match and unit_is_ma:
            uncertainties[subj] = Decimal(duration_match.group(1)) * Decimal("1000000")

    return uncertainties


def _parse_boundaries(blocks: Iterable[str]) -> dict[str, Boundary]:
    boundaries: dict[str, Boundary] = {}

    for block in blocks:
        subj = _subject(block)
        if not subj or "time:inTemporalPosition" not in block:
            continue

        label = _english_pref_label(block)
        time_ref_match = re.search(r"time:inTemporalPosition\s+(ischart:[A-Za-z0-9_.-]+)\s*;", block)

        if not label or not time_ref_match:
            continue

        # Keep geochronologic boundary events, not geometry/location helper records.
        if not label.startswith(("Base of ", "Formation of ")):
            continue

        boundaries[subj] = Boundary(
            subject=subj,
            label=label,
            time_position_ref=time_ref_match.group(1),
        )

    return boundaries


def _trs_to_years(position: TimePosition) -> tuple[Decimal, str, str]:
    if position.trs.endswith("/ma"):
        return position.numeric_position * Decimal("1000000"), "Ma BP", "ICS geologic age Ma before present"
    if position.trs.endswith("/bp"):
        return position.numeric_position, "years BP", "ICS geologic age years before present (1950)"
    raise ValueError(f"Unsupported temporal reference system: {position.trs}")


def _precision_for_years_before_present(years_bp: Decimal) -> PrecisionLevel:
    if abs(years_bp) <= Decimal("1000000"):
        return PrecisionLevel.LEVEL_1
    return PrecisionLevel.LEVEL_2


def _make_uby(years_before_present: Decimal, precision_level: PrecisionLevel, source_time: str) -> UBYTime:
    # For ICS Ma/BP geologic ages, follow the WD 0.1.0 appendix convention:
    # UBY ~= Planck2018 model-base age minus years before present. This preserves
    # geologic-scale significant figures and avoids implying day/second precision.
    uby_value = MODEL_BASE_UBY - years_before_present
    return UBYTime(
        uby_value=uby_value,
        uby_version=UBY_SPEC_VERSION,
        model_version=DEFAULT_MODEL_VERSION,
        precision_level=precision_level,
        source_time=source_time,
        source_system="ICS Chronostratigraphic Chart",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )


def annotate() -> list[AnnotatedBoundary]:
    text = RAW_TTL.read_text(encoding="utf-8")
    blocks = _split_turtle_blocks(text)

    positions = _parse_time_positions(blocks)
    uncertainties = _parse_uncertainties(blocks)
    boundaries = _parse_boundaries(blocks)

    records: list[AnnotatedBoundary] = []

    for boundary in sorted(boundaries.values(), key=lambda item: item.label):
        position = positions.get(boundary.time_position_ref)
        if position is None:
            continue

        years_bp, original_unit, source_system = _trs_to_years(position)
        uncertainty_years = (
            uncertainties.get(position.uncertainty_ref) if position.uncertainty_ref else None
        )
        precision = _precision_for_years_before_present(years_bp)
        source_time = f"{decimal_to_plain_text(position.numeric_position)} {original_unit}"

        uby = _make_uby(years_bp, precision, source_time)
        if uncertainty_years is not None:
            uby = uby.with_uncertainty(
                uncertainty_years=uncertainty_years,
                uncertainty_kind="measurement",
                interval_start=uby.uby_value - uncertainty_years,
                interval_end=uby.uby_value + uncertainty_years,
            )

        validation_messages = validate_uby_time(uby)

        records.append(
            AnnotatedBoundary(
                source_dataset="International Chronostratigraphic Chart RDF (gts2020.ttl)",
                source_record_id=boundary.subject.replace("ischart:", ""),
                source_record_uri=ICS_BASE_URI + boundary.subject.replace("ischart:", ""),
                event_label=boundary.label,
                event_type="geochronologic_boundary",
                original_time_value=decimal_to_plain_text(position.numeric_position),
                original_time_unit=original_unit,
                source_system=source_system,
                years_before_present=decimal_to_plain_text(years_bp),
                uncertainty_years=(
                    decimal_to_plain_text(uncertainty_years) if uncertainty_years is not None else None
                ),
                precision_level=precision.value,
                uby_value=decimal_to_plain_text(uby.uby_value),
                uby_expression=format_full(uby, include_model=True, include_spec=True),
                uby_magnitude_expression=format_magnitude(uby, include_model=True, include_spec=True),
                model_version=uby.model_version or "",
                uby_version=uby.uby_version,
                anchor_id=uby.anchor_id,
                anchor_jd=str(uby.anchor_jd),
                anchor_uby=str(uby.anchor_uby),
                rounding_rule=uby.rounding_rule,
                generated_by=uby.generated_by,
                validation_messages=json.dumps(
                    [asdict(message) for message in validation_messages],
                    ensure_ascii=False,
                ),
                attribution=(
                    "© International Commission on Stratigraphy, 2024; "
                    "CC BY 4.0; source=https://github.com/i-c-stratigraphy/chart"
                ),
            )
        )

    return records


def write_csv(records: list[AnnotatedBoundary]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(AnnotatedBoundary.__dataclass_fields__))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def write_sqlite(records: list[AnnotatedBoundary]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedBoundary.__dataclass_fields__)
    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            "CREATE TABLE ics_chart_uby ("
            + ", ".join(f"{column} TEXT" for column in columns)
            + ")"
        )
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            f"INSERT INTO ics_chart_uby ({', '.join(columns)}) VALUES ({placeholders})",
            [[getattr(record, column) for column in columns] for record in records],
        )
        conn.execute("CREATE INDEX idx_ics_chart_uby_value ON ics_chart_uby (uby_value)")
        conn.execute("CREATE INDEX idx_ics_chart_event_label ON ics_chart_uby (event_label)")


def write_metadata(records: list[AnnotatedBoundary]) -> None:
    metadata = {
        "dataset": "International Chronostratigraphic Chart RDF",
        "source_repository": "https://github.com/i-c-stratigraphy/chart",
        "source_file": str(RAW_TTL.as_posix()),
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "attribution": "© International Commission on Stratigraphy, 2024",
        "record_count": len(records),
        "uby_annotation_principles": [
            "Native ICS Ma/BP values are preserved.",
            "UBY is added only as an auxiliary cross-scale label/index.",
            "Level 2 geologic values retain model_version and uby_version.",
            "No extra precision beyond source numericPosition is introduced.",
            "Uncertainty durations are carried when provided by ICS.",
        ],
        "uby_version": UBY_SPEC_VERSION,
        "model_version": DEFAULT_MODEL_VERSION,
        "anchor": {
            "anchor_id": DEFAULT_ANCHOR.anchor_id,
            "anchor_jd": str(DEFAULT_ANCHOR.anchor_jd),
            "anchor_uby": str(DEFAULT_ANCHOR.anchor_uby),
        },
        "rounding_rule": DEFAULT_ROUNDING_RULE,
        "outputs": {
            "csv": str(CSV_OUT.as_posix()),
            "sqlite": str(SQLITE_OUT.as_posix()),
        },
    }
    METADATA_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if not RAW_TTL.exists():
        raise FileNotFoundError(
            f"ICS source file not found: {RAW_TTL}. Download the ICS chart dataset first."
        )

    records = annotate()
    write_csv(records)
    write_sqlite(records)
    write_metadata(records)

    print(f"Annotated records: {len(records)}")
    print(f"CSV: {CSV_OUT}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Metadata: {METADATA_OUT}")

    if records:
        print("Sample:")
        for record in records[:5]:
            print(f"- {record.event_label}: {record.source_system}={record.original_time_value} {record.original_time_unit} -> {record.uby_expression}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
