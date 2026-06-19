#!/usr/bin/env python3
"""
Benchmark UBY annotation performance on a larger downloaded authority dataset.

Dataset:
- USGS Earthquake Catalog CSV
- Source file: data/raw/usgs_earthquakes/usgs_m2_5_2014_2026_monthly.csv

Normative UBY principles applied:
- preserve the USGS native UTC event timestamp;
- use UBY only as an auxiliary cross-scale label/index;
- keep the USGS source event id and spatial/magnitude fields;
- mark earthquake event timestamps as Level 1 near-present UTC data;
- do not invent temporal uncertainty when the source CSV does not provide one;
- record benchmark metadata separately from the source data.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.anchors import DEFAULT_ANCHOR
from uby_time.constants import DEFAULT_MODEL_VERSION, DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from uby_time.conversion import iso_to_uby
from uby_time.formatting import format_full, format_magnitude
from uby_time.models import PrecisionLevel
from uby_time.utils import decimal_to_plain_text
from uby_time.validation import validate_uby_time

RAW_CSV = ROOT / "data" / "raw" / "usgs_earthquakes" / "usgs_m2_5_2014_2026_monthly.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "usgs_earthquakes_uby_benchmark.csv"
SQLITE_OUT = PROCESSED_DIR / "usgs_earthquakes_uby_benchmark.sqlite"
METADATA_OUT = PROCESSED_DIR / "usgs_earthquakes_uby_benchmark_metadata.json"

TABLE_NAME = "usgs_earthquakes_uby_benchmark"
BATCH_SIZE = 1000


@dataclass(frozen=True)
class AnnotatedEarthquake:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    source_time_utc: str
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
    latitude: str
    longitude: str
    depth_km: str
    magnitude: str
    magnitude_type: str
    place: str
    usgs_type: str
    status: str
    location_source: str
    magnitude_source: str
    updated_time_utc: str
    validation_messages: str
    attribution: str


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _source_uri(event_id: str) -> str:
    return f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}" if event_id else ""


def _make_record(row: dict[str, str]) -> AnnotatedEarthquake | None:
    event_time = _clean(row.get("time"))
    event_id = _clean(row.get("id"))
    if not event_time or not event_id:
        return None

    # Use the standard-library conversion path to benchmark the dependency-free
    # reference implementation and avoid astropy import overhead in this large run.
    uby = iso_to_uby(
        event_time,
        source_system="USGS Earthquake Catalog UTC event time",
        prefer_astropy=False,
    )
    messages = validate_uby_time(uby)

    place = _clean(row.get("place"))
    magnitude = _clean(row.get("mag"))
    event_label = f"USGS earthquake {event_id}"
    if magnitude or place:
        event_label += f": M{magnitude} {place}".rstrip()

    return AnnotatedEarthquake(
        source_dataset="USGS Earthquake Catalog",
        source_record_id=event_id,
        source_record_uri=_source_uri(event_id),
        event_label=event_label,
        event_type="earthquake_event_time",
        source_time_utc=event_time,
        precision_level=PrecisionLevel.LEVEL_1.value,
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
        latitude=_clean(row.get("latitude")),
        longitude=_clean(row.get("longitude")),
        depth_km=_clean(row.get("depth")),
        magnitude=magnitude,
        magnitude_type=_clean(row.get("magType")),
        place=place,
        usgs_type=_clean(row.get("type")),
        status=_clean(row.get("status")),
        location_source=_clean(row.get("locationSource")),
        magnitude_source=_clean(row.get("magSource")),
        updated_time_utc=_clean(row.get("updated")),
        validation_messages=json.dumps([asdict(message) for message in messages], ensure_ascii=False),
        attribution=(
            "Data from the U.S. Geological Survey (USGS) Earthquake Catalog, "
            "https://earthquake.usgs.gov/fdsnws/event/1/; "
            "UBY annotation added by uby-time."
        ),
    )


def _create_sqlite_table(conn: sqlite3.Connection, columns: list[str]) -> None:
    conn.execute(f"DROP TABLE IF EXISTS {_quote_identifier(TABLE_NAME)}")
    conn.execute(
        f"CREATE TABLE {_quote_identifier(TABLE_NAME)} ("
        + ", ".join(f"{_quote_identifier(column)} TEXT" for column in columns)
        + ")"
    )
    conn.execute(
        f"CREATE INDEX idx_usgs_earthquakes_uby_value "
        f"ON {_quote_identifier(TABLE_NAME)} ({_quote_identifier('uby_value')})"
    )
    conn.execute(
        f"CREATE INDEX idx_usgs_earthquakes_source_time "
        f"ON {_quote_identifier(TABLE_NAME)} ({_quote_identifier('source_time_utc')})"
    )
    conn.execute(
        f"CREATE INDEX idx_usgs_earthquakes_magnitude "
        f"ON {_quote_identifier(TABLE_NAME)} ({_quote_identifier('magnitude')})"
    )


def _insert_batch(conn: sqlite3.Connection, columns: list[str], batch: list[AnnotatedEarthquake]) -> None:
    if not batch:
        return
    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
    conn.executemany(
        f"INSERT INTO {_quote_identifier(TABLE_NAME)} ({quoted_columns}) VALUES ({placeholders})",
        [[getattr(record, column) for column in columns] for record in batch],
    )


def _read_source_rows() -> Iterable[dict[str, str]]:
    with RAW_CSV.open("r", encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)


def run_benchmark() -> dict[str, object]:
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"USGS source file not found: {RAW_CSV}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedEarthquake.__dataclass_fields__)
    source_size_bytes = RAW_CSV.stat().st_size

    tracemalloc.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()

    annotated_count = 0
    skipped_count = 0
    first_time = ""
    last_time = ""
    first_uby = ""
    last_uby = ""
    min_uby: str | None = None
    max_uby: str | None = None

    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as csv_file, sqlite3.connect(SQLITE_OUT) as conn:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        _create_sqlite_table(conn, columns)

        batch: list[AnnotatedEarthquake] = []
        for row in _read_source_rows():
            record = _make_record(row)
            if record is None:
                skipped_count += 1
                continue

            writer.writerow(asdict(record))
            batch.append(record)
            annotated_count += 1

            if annotated_count == 1:
                first_time = record.source_time_utc
                first_uby = record.uby_value
            last_time = record.source_time_utc
            last_uby = record.uby_value
            min_uby = record.uby_value if min_uby is None or record.uby_value < min_uby else min_uby
            max_uby = record.uby_value if max_uby is None or record.uby_value > max_uby else max_uby

            if len(batch) >= BATCH_SIZE:
                _insert_batch(conn, columns, batch)
                batch.clear()

        _insert_batch(conn, columns, batch)
        conn.commit()

    wall_seconds = time.perf_counter() - wall_start
    cpu_seconds = time.process_time() - cpu_start
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    rows_per_second = annotated_count / wall_seconds if wall_seconds else 0.0
    cpu_rows_per_second = annotated_count / cpu_seconds if cpu_seconds else 0.0

    metadata: dict[str, object] = {
        "dataset": "USGS Earthquake Catalog M2.5+ monthly CSV performance subset",
        "source_file": str(RAW_CSV.as_posix()),
        "source_size_bytes": source_size_bytes,
        "record_count": annotated_count,
        "skipped_count": skipped_count,
        "first_source_time_utc": first_time,
        "last_source_time_utc": last_time,
        "first_uby_value": first_uby,
        "last_uby_value": last_uby,
        "min_uby_value": min_uby,
        "max_uby_value": max_uby,
        "benchmark": {
            "wall_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "rows_per_second_wall": rows_per_second,
            "rows_per_second_cpu": cpu_rows_per_second,
            "peak_memory_bytes_tracemalloc": peak_bytes,
            "current_memory_bytes_tracemalloc": current_bytes,
            "batch_size": BATCH_SIZE,
            "python_version": sys.version,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "uby_annotation_principles": [
            "USGS native UTC event timestamps are preserved.",
            "UBY is added only as an auxiliary cross-scale label/index.",
            "All records are Level 1 near-present UTC event data.",
            "No temporal uncertainty is invented when the source CSV does not provide it.",
            "Benchmark metadata is stored separately from source event fields.",
        ],
        "uby_version": UBY_SPEC_VERSION,
        "model_version": DEFAULT_MODEL_VERSION,
        "anchor": {
            "anchor_id": DEFAULT_ANCHOR.anchor_id,
            "anchor_jd": str(DEFAULT_ANCHOR.anchor_jd),
            "anchor_uby": str(DEFAULT_ANCHOR.anchor_uby),
        },
        "rounding_rule": DEFAULT_ROUNDING_RULE,
        "generated_by": GENERATED_BY,
        "outputs": {
            "csv": str(CSV_OUT.as_posix()),
            "sqlite": str(SQLITE_OUT.as_posix()),
        },
    }

    METADATA_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def main() -> int:
    metadata = run_benchmark()
    benchmark = metadata["benchmark"]

    print(f"Annotated records: {metadata['record_count']}")
    print(f"Skipped records: {metadata['skipped_count']}")
    print(f"Source size bytes: {metadata['source_size_bytes']}")
    print(f"CSV: {CSV_OUT}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Metadata: {METADATA_OUT}")
    print(
        "Performance: "
        f"wall={benchmark['wall_seconds']:.6f}s, "
        f"cpu={benchmark['cpu_seconds']:.6f}s, "
        f"rows/s wall={benchmark['rows_per_second_wall']:.2f}, "
        f"rows/s cpu={benchmark['rows_per_second_cpu']:.2f}, "
        f"peak_mem={benchmark['peak_memory_bytes_tracemalloc']} bytes"
    )
    print(
        "Range: "
        f"{metadata['first_source_time_utc']} -> {metadata['last_source_time_utc']}; "
        f"UBY {metadata['first_uby_value']} -> {metadata['last_uby_value']}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
