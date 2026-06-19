#!/usr/bin/env python3
"""
Annotate downloaded PBDB Dinosauria occurrence records with UBY labels.

Normative UBY principles applied:
- preserve PBDB native min_ma/max_ma interval fields;
- use UBY only as an auxiliary index/label;
- use interval midpoint only as a derived representative label;
- carry half interval width as uncertainty_years;
- keep source/model/spec/anchor/rounding metadata with every record;
- avoid inventing precision beyond PBDB geological age ranges.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.anchors import DEFAULT_ANCHOR
from uby_time.constants import (
    DEFAULT_MNEMONIC_PREFIX,
    DEFAULT_MODEL_VERSION,
    DEFAULT_ROUNDING_RULE,
    GENERATED_BY,
    UBY_SPEC_VERSION,
)
from uby_time.formatting import format_full, format_magnitude
from uby_time.models import PrecisionLevel, UBYTime
from uby_time.utils import decimal_to_plain_text
from uby_time.validation import validate_uby_time

RAW_CSV = ROOT / "data" / "raw" / "pbdb" / "pbdb_dinosauria_occurrences.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "pbdb_dinosauria_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "pbdb_dinosauria_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "pbdb_dinosauria_uby_metadata.json"

MODEL_BASE_UBY = Decimal(DEFAULT_MNEMONIC_PREFIX) * Decimal("100000")


@dataclass(frozen=True)
class AnnotatedOccurrence:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    accepted_name: str
    identified_name: str
    identified_rank: str
    accepted_rank: str
    early_interval: str
    late_interval: str
    max_ma: str
    min_ma: str
    representative_ma_midpoint: str
    years_before_present_midpoint: str
    uncertainty_years: str
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
    longitude: str
    latitude: str
    phylum: str
    class_name: str
    taxonomic_order: str
    family: str
    genus: str
    formation: str
    geological_group: str
    member: str
    reference_no: str
    validation_messages: str
    attribution: str


def _decimal(value: str) -> Decimal | None:
    if value is None or value.strip() == "":
        return None
    try:
        return Decimal(value.strip())
    except InvalidOperation:
        return None


def _precision_for_years_before_present(years_bp: Decimal) -> PrecisionLevel:
    return PrecisionLevel.LEVEL_1 if abs(years_bp) <= Decimal("1000000") else PrecisionLevel.LEVEL_2


def _make_uby(years_before_present: Decimal, precision_level: PrecisionLevel, source_time: str) -> UBYTime:
    uby_value = MODEL_BASE_UBY - years_before_present
    return UBYTime(
        uby_value=uby_value,
        uby_version=UBY_SPEC_VERSION,
        model_version=DEFAULT_MODEL_VERSION,
        precision_level=precision_level,
        source_time=source_time,
        source_system="PBDB occurrence age interval midpoint",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )


def annotate() -> list[AnnotatedOccurrence]:
    records: list[AnnotatedOccurrence] = []

    with RAW_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            max_ma = _decimal(row.get("max_ma", ""))
            min_ma = _decimal(row.get("min_ma", ""))
            occurrence_no = row.get("occurrence_no", "").strip()

            if max_ma is None or min_ma is None or max_ma < min_ma:
                continue

            midpoint_ma = (max_ma + min_ma) / Decimal("2")
            half_width_ma = (max_ma - min_ma) / Decimal("2")
            years_bp = midpoint_ma * Decimal("1000000")
            uncertainty_years = half_width_ma * Decimal("1000000")
            precision = _precision_for_years_before_present(years_bp)
            source_time = f"{decimal_to_plain_text(min_ma)}-{decimal_to_plain_text(max_ma)} Ma BP"

            uby = _make_uby(years_bp, precision, source_time).with_uncertainty(
                uncertainty_years=uncertainty_years,
                uncertainty_kind="measurement",
                interval_start=MODEL_BASE_UBY - (max_ma * Decimal("1000000")),
                interval_end=MODEL_BASE_UBY - (min_ma * Decimal("1000000")),
            )
            messages = validate_uby_time(uby)

            accepted_name = row.get("accepted_name", "").strip()
            identified_name = row.get("identified_name", "").strip()
            label_name = accepted_name or identified_name or f"PBDB occurrence {occurrence_no}"

            records.append(
                AnnotatedOccurrence(
                    source_dataset="Paleobiology Database occurrence API (Dinosauria subset)",
                    source_record_id=occurrence_no,
                    source_record_uri=f"https://paleobiodb.org/classic/checkTaxonInfo?taxon_no={row.get('accepted_no', '').strip()}",
                    event_label=f"PBDB occurrence {occurrence_no}: {label_name}",
                    event_type="fossil_occurrence_age_interval",
                    accepted_name=accepted_name,
                    identified_name=identified_name,
                    identified_rank=row.get("identified_rank", "").strip(),
                    accepted_rank=row.get("accepted_rank", "").strip(),
                    early_interval=row.get("early_interval", "").strip(),
                    late_interval=row.get("late_interval", "").strip(),
                    max_ma=decimal_to_plain_text(max_ma),
                    min_ma=decimal_to_plain_text(min_ma),
                    representative_ma_midpoint=decimal_to_plain_text(midpoint_ma),
                    years_before_present_midpoint=decimal_to_plain_text(years_bp),
                    uncertainty_years=decimal_to_plain_text(uncertainty_years),
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
                    longitude=row.get("lng", "").strip(),
                    latitude=row.get("lat", "").strip(),
                    phylum=row.get("phylum", "").strip(),
                    class_name=row.get("class", "").strip(),
                    taxonomic_order=row.get("order", "").strip(),
                    family=row.get("family", "").strip(),
                    genus=row.get("genus", "").strip(),
                    formation=row.get("formation", "").strip(),
                    geological_group=row.get("geological_group", "").strip(),
                    member=row.get("member", "").strip(),
                    reference_no=row.get("reference_no", "").strip(),
                    validation_messages=json.dumps([asdict(m) for m in messages], ensure_ascii=False),
                    attribution=(
                        "Data from the Paleobiology Database (PBDB), https://paleobiodb.org; "
                        "downloaded via PBDB data1.2 API; UBY annotation added by uby-time."
                    ),
                )
            )

    return records


def write_csv(records: list[AnnotatedOccurrence]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(AnnotatedOccurrence.__dataclass_fields__))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier defensively.

    The PBDB source schema contains fields such as ``order`` that collide with
    SQL reserved words.  Quoting every generated column name keeps the export
    robust if future PBDB fields have similar names.
    """

    return '"' + identifier.replace('"', '""') + '"'


def write_sqlite(records: list[AnnotatedOccurrence]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedOccurrence.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            "CREATE TABLE pbdb_dinosauria_uby ("
            + ", ".join(f"{column} TEXT" for column in quoted_columns)
            + ")"
        )
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            f"INSERT INTO pbdb_dinosauria_uby ({', '.join(quoted_columns)}) VALUES ({placeholders})",
            [[getattr(record, c) for c in columns] for record in records],
        )
        conn.execute(
            "CREATE INDEX idx_pbdb_dinosauria_uby_value "
            f"ON pbdb_dinosauria_uby ({_quote_identifier('uby_value')})"
        )
        conn.execute(
            "CREATE INDEX idx_pbdb_dinosauria_name "
            f"ON pbdb_dinosauria_uby ({_quote_identifier('accepted_name')})"
        )


def write_metadata(records: list[AnnotatedOccurrence]) -> None:
    metadata = {
        "dataset": "Paleobiology Database Dinosauria occurrences",
        "source_api": "https://paleobiodb.org/data1.2/occs/list.csv?base_name=Dinosauria&show=coords,phylo,ident,attr,strat,time&limit=5000",
        "source_file": str(RAW_CSV.as_posix()),
        "record_count": len(records),
        "uby_annotation_principles": [
            "PBDB native min_ma/max_ma intervals are preserved.",
            "UBY is added only as an auxiliary cross-scale label/index.",
            "Representative UBY values use midpoint(max_ma,min_ma).",
            "Half interval width is carried as uncertainty_years.",
            "No extra precision beyond PBDB age intervals is introduced.",
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
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"PBDB source file not found: {RAW_CSV}")

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
            print(
                f"- {record.event_label}: {record.min_ma}-{record.max_ma} Ma BP "
                f"mid={record.representative_ma_midpoint} Ma -> {record.uby_expression} "
                f"±{record.uncertainty_years} years"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
