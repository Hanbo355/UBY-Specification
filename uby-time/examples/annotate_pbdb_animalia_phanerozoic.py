#!/usr/bin/env python3
"""
Annotate a paged PBDB Animalia/Phanerozoic occurrence download with UBY labels.

This script is designed for large PBDB downloads. It streams raw CSV batches into
processed CSV and SQLite outputs without holding all annotated records in memory.

Normative UBY principles applied:
- preserve PBDB native min_ma/max_ma interval fields;
- use UBY only as an auxiliary cross-scale label/index;
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
import time
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

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

RAW_DIR = ROOT / "data" / "raw" / "pbdb"
PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby_metadata.json"

SOURCE_API = (
    "https://paleobiodb.org/data1.2/occs/list.csv?"
    "base_name=Animalia&interval=Phanerozoic&show=coords,phylo,ident,attr,strat,time&limit=10000"
    " with offset-based pagination"
)
SOURCE_DATASET = "Paleobiology Database occurrence API (Animalia Phanerozoic paged download)"
MODEL_BASE_UBY = Decimal(DEFAULT_MNEMONIC_PREFIX) * Decimal("100000")
BATCH_INSERT_SIZE = 5000


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


def _decimal(value: str | None) -> Decimal | None:
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


def _raw_csvs() -> tuple[Path, ...]:
    paged = tuple(sorted(RAW_DIR.glob("pbdb_animalia_phanerozoic_occurrences_offset_*.csv")))
    if paged:
        return paged

    legacy = (
        RAW_DIR / "pbdb_animalia_phanerozoic_occurrences_50k.csv",
        RAW_DIR / "pbdb_animalia_phanerozoic_occurrences_50k_offset_50000.csv",
    )
    return tuple(path for path in legacy if path.exists())


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _iter_raw_rows() -> Iterable[dict[str, str]]:
    for raw_csv in _raw_csvs():
        with raw_csv.open("r", encoding="utf-8", newline="") as file:
            yield from csv.DictReader(file)


def _annotate_row(row: dict[str, str]) -> AnnotatedOccurrence | None:
    max_ma = _decimal(row.get("max_ma", ""))
    min_ma = _decimal(row.get("min_ma", ""))

    if max_ma is None or min_ma is None or max_ma < min_ma:
        return None

    occurrence_no = (row.get("occurrence_no") or "").strip()
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

    accepted_name = (row.get("accepted_name") or "").strip()
    identified_name = (row.get("identified_name") or "").strip()
    label_name = accepted_name or identified_name or f"PBDB occurrence {occurrence_no}"
    accepted_no = (row.get("accepted_no") or "").strip()

    return AnnotatedOccurrence(
        source_dataset=SOURCE_DATASET,
        source_record_id=occurrence_no,
        source_record_uri=f"https://paleobiodb.org/classic/checkTaxonInfo?taxon_no={accepted_no}",
        event_label=f"PBDB occurrence {occurrence_no}: {label_name}",
        event_type="fossil_occurrence_age_interval",
        accepted_name=accepted_name,
        identified_name=identified_name,
        identified_rank=(row.get("identified_rank") or "").strip(),
        accepted_rank=(row.get("accepted_rank") or "").strip(),
        early_interval=(row.get("early_interval") or "").strip(),
        late_interval=(row.get("late_interval") or "").strip(),
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
        longitude=(row.get("lng") or "").strip(),
        latitude=(row.get("lat") or "").strip(),
        phylum=(row.get("phylum") or "").strip(),
        class_name=(row.get("class") or "").strip(),
        taxonomic_order=(row.get("order") or "").strip(),
        family=(row.get("family") or "").strip(),
        genus=(row.get("genus") or "").strip(),
        formation=(row.get("formation") or "").strip(),
        geological_group=(row.get("geological_group") or "").strip(),
        member=(row.get("member") or "").strip(),
        reference_no=(row.get("reference_no") or "").strip(),
        validation_messages=json.dumps([asdict(m) for m in messages], ensure_ascii=False),
        attribution=(
            "Data from the Paleobiology Database (PBDB), https://paleobiodb.org; "
            "downloaded via PBDB data1.2 API; UBY annotation added by uby-time."
        ),
    )


def _create_sqlite(conn: sqlite3.Connection) -> None:
    columns = list(AnnotatedOccurrence.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    conn.execute(
        "CREATE TABLE pbdb_animalia_phanerozoic_uby ("
        + ", ".join(f"{column} TEXT" for column in quoted_columns)
        + ")"
    )


def _write_indexes(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE INDEX idx_pbdb_animalia_phanerozoic_uby_value "
        f"ON pbdb_animalia_phanerozoic_uby ({_quote_identifier('uby_value')})"
    )
    conn.execute(
        "CREATE INDEX idx_pbdb_animalia_phanerozoic_name "
        f"ON pbdb_animalia_phanerozoic_uby ({_quote_identifier('accepted_name')})"
    )
    conn.execute(
        "CREATE INDEX idx_pbdb_animalia_phanerozoic_interval "
        f"ON pbdb_animalia_phanerozoic_uby ({_quote_identifier('early_interval')}, {_quote_identifier('late_interval')})"
    )
    conn.execute(
        "CREATE INDEX idx_pbdb_animalia_phanerozoic_class "
        f"ON pbdb_animalia_phanerozoic_uby ({_quote_identifier('class_name')})"
    )


def write_outputs() -> dict[str, object]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedOccurrence.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    placeholders = ", ".join("?" for _ in columns)
    insert_sql = (
        f"INSERT INTO pbdb_animalia_phanerozoic_uby ({', '.join(quoted_columns)}) "
        f"VALUES ({placeholders})"
    )

    seen_occurrence_numbers: set[str] = set()
    stats: dict[str, object] = {
        "raw_rows": 0,
        "record_count": 0,
        "skipped_records": 0,
        "duplicate_records": 0,
        "precision_counts": {},
        "class_counts": {},
    }

    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as csv_file, sqlite3.connect(SQLITE_OUT) as conn:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()

        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        _create_sqlite(conn)

        sqlite_batch: list[list[str]] = []
        for row in _iter_raw_rows():
            stats["raw_rows"] = int(stats["raw_rows"]) + 1
            occurrence_no = (row.get("occurrence_no") or "").strip()
            if occurrence_no and occurrence_no in seen_occurrence_numbers:
                stats["duplicate_records"] = int(stats["duplicate_records"]) + 1
                stats["skipped_records"] = int(stats["skipped_records"]) + 1
                continue
            if occurrence_no:
                seen_occurrence_numbers.add(occurrence_no)

            record = _annotate_row(row)
            if record is None:
                stats["skipped_records"] = int(stats["skipped_records"]) + 1
                continue

            payload = asdict(record)
            writer.writerow(payload)
            sqlite_batch.append([payload[column] for column in columns])

            stats["record_count"] = int(stats["record_count"]) + 1
            precision_counts = stats["precision_counts"]
            class_counts = stats["class_counts"]
            assert isinstance(precision_counts, dict)
            assert isinstance(class_counts, dict)
            precision_counts[record.precision_level] = int(precision_counts.get(record.precision_level, 0)) + 1
            if record.class_name:
                class_counts[record.class_name] = int(class_counts.get(record.class_name, 0)) + 1

            if len(sqlite_batch) >= BATCH_INSERT_SIZE:
                conn.executemany(insert_sql, sqlite_batch)
                sqlite_batch.clear()

        if sqlite_batch:
            conn.executemany(insert_sql, sqlite_batch)

        _write_indexes(conn)

    return stats


def write_metadata(stats: dict[str, object], wall_seconds: float) -> None:
    class_counts = stats.get("class_counts", {})
    assert isinstance(class_counts, dict)

    metadata = {
        "dataset": "Paleobiology Database Animalia Phanerozoic occurrence paged download",
        "source_api": SOURCE_API,
        "source_files": [str(path.as_posix()) for path in _raw_csvs()],
        "source_file_count": len(_raw_csvs()),
        "raw_rows": stats["raw_rows"],
        "record_count": stats["record_count"],
        "skipped_records": stats["skipped_records"],
        "duplicate_records": stats["duplicate_records"],
        "precision_counts": stats["precision_counts"],
        "top_class_counts": dict(sorted(class_counts.items(), key=lambda item: item[1], reverse=True)[:20]),
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
        "build_performance": {
            "wall_seconds": wall_seconds,
            "records_per_second": int(stats["record_count"]) / wall_seconds if wall_seconds else 0,
        },
    }
    METADATA_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if not _raw_csvs():
        raise FileNotFoundError(
            "No PBDB Animalia Phanerozoic raw CSV batches found. "
            "Run examples/download_pbdb_animalia_phanerozoic_all.py first."
        )

    start = time.perf_counter()
    stats = write_outputs()
    wall_seconds = time.perf_counter() - start
    write_metadata(stats, wall_seconds)

    print(f"Raw rows: {stats['raw_rows']}")
    print(f"Annotated records: {stats['record_count']}")
    print(f"Skipped records: {stats['skipped_records']}")
    print(f"Duplicate records: {stats['duplicate_records']}")
    print(f"CSV: {CSV_OUT}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Metadata: {METADATA_OUT}")
    print(f"Build wall seconds: {wall_seconds:.6f}")
    print(f"Records/s: {int(stats['record_count']) / wall_seconds if wall_seconds else 0:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
