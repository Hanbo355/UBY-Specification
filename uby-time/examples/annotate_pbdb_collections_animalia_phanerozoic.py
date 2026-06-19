#!/usr/bin/env python3
"""
Annotate PBDB Animalia/Phanerozoic collection-level records with UBY labels.

This expands the UBY paleobiology layer from occurrence-only records to
collection-level sampling metadata.  Collection-level data are required for
stronger sampling controls, including formation/reference/geography/environment
standardization and future shareholder quorum subsampling.

Inputs:
- data/raw/pbdb_collections/pbdb_collections_animalia_phanerozoic_offset_*.csv

Outputs:
- data/processed/pbdb_collections_animalia_phanerozoic_uby.csv
- data/processed/pbdb_collections_animalia_phanerozoic_uby.sqlite
- data/processed/pbdb_collections_animalia_phanerozoic_uby_metadata.json
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

RAW_DIR = ROOT / "data" / "raw" / "pbdb_collections"
PROCESSED_DIR = ROOT / "data" / "processed"

CSV_OUT = PROCESSED_DIR / "pbdb_collections_animalia_phanerozoic_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "pbdb_collections_animalia_phanerozoic_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "pbdb_collections_animalia_phanerozoic_uby_metadata.json"

SOURCE_API = (
    "https://paleobiodb.org/data1.2/colls/list.csv?"
    "base_name=Animalia&interval=Phanerozoic&show=full,loc,locext,paleoloc,strat,lith,env,time,ref,refattr"
    " with offset-based pagination"
)
SOURCE_DATASET = "Paleobiology Database collection API (Animalia Phanerozoic paged download)"
MODEL_BASE_UBY = Decimal(DEFAULT_MNEMONIC_PREFIX) * Decimal("100000")
BATCH_INSERT_SIZE = 5000


@dataclass(frozen=True)
class AnnotatedCollection:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    collection_name: str
    collection_no: str
    n_occs: str
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
    paleolongitude: str
    paleolatitude: str
    country: str
    state: str
    county: str
    formation: str
    geological_group: str
    member: str
    environment: str
    lithology1: str
    lithology2: str
    lithification1: str
    lithification2: str
    collection_type: str
    collection_methods: str
    research_group: str
    reference_no: str
    primary_reference: str
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
        source_system="PBDB collection age interval midpoint",
        rounding_rule=DEFAULT_ROUNDING_RULE,
        generated_by=GENERATED_BY,
        anchor_id=DEFAULT_ANCHOR.anchor_id,
        anchor_jd=DEFAULT_ANCHOR.anchor_jd,
        anchor_uby=DEFAULT_ANCHOR.anchor_uby,
    )


def _is_valid_collection_csv(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    with path.open("r", encoding="utf-8", newline="") as file:
        fields = set(csv.DictReader(file).fieldnames or [])
    return "collection_no" in fields and "record_type" in fields


def _raw_csvs() -> tuple[Path, ...]:
    return tuple(
        path
        for path in sorted(RAW_DIR.glob("pbdb_collections_animalia_phanerozoic_offset_*.csv"))
        if _is_valid_collection_csv(path)
    )


def _iter_raw_rows() -> Iterable[dict[str, str]]:
    for raw_csv in _raw_csvs():
        with raw_csv.open("r", encoding="utf-8", newline="") as file:
            yield from csv.DictReader(file)


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _annotate_row(row: dict[str, str]) -> AnnotatedCollection | None:
    max_ma = _decimal(row.get("max_ma", ""))
    min_ma = _decimal(row.get("min_ma", ""))

    if max_ma is None or min_ma is None or max_ma < min_ma:
        return None

    collection_no = (row.get("collection_no") or "").strip()
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

    collection_name = (row.get("collection_name") or "").strip()
    label = collection_name or f"PBDB collection {collection_no}"

    return AnnotatedCollection(
        source_dataset=SOURCE_DATASET,
        source_record_id=collection_no,
        source_record_uri=f"https://paleobiodb.org/classic/displayCollResults?collection_no={collection_no}",
        event_label=f"PBDB collection {collection_no}: {label}",
        event_type="fossil_collection_age_interval",
        collection_name=collection_name,
        collection_no=collection_no,
        n_occs=(row.get("n_occs") or "").strip(),
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
        paleolongitude=(row.get("paleolng") or "").strip(),
        paleolatitude=(row.get("paleolat") or "").strip(),
        country=(row.get("cc") or "").strip(),
        state=(row.get("state") or "").strip(),
        county=(row.get("county") or "").strip(),
        formation=(row.get("formation") or "").strip(),
        geological_group=(row.get("geological_group") or "").strip(),
        member=(row.get("member") or "").strip(),
        environment=(row.get("environment") or "").strip(),
        lithology1=(row.get("lithology1") or "").strip(),
        lithology2=(row.get("lithology2") or "").strip(),
        lithification1=(row.get("lithification1") or "").strip(),
        lithification2=(row.get("lithification2") or "").strip(),
        collection_type=(row.get("collection_type") or "").strip(),
        collection_methods=(row.get("collection_methods") or "").strip(),
        research_group=(row.get("research_group") or "").strip(),
        reference_no=(row.get("reference_no") or "").strip(),
        primary_reference=(row.get("primary_reference") or "").strip(),
        validation_messages=json.dumps([asdict(m) for m in messages], ensure_ascii=False),
        attribution=(
            "Data from the Paleobiology Database (PBDB), https://paleobiodb.org; "
            "downloaded via PBDB data1.2 collection API; UBY annotation added by uby-time."
        ),
    )


def _create_sqlite(conn: sqlite3.Connection) -> None:
    columns = list(AnnotatedCollection.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    conn.execute(
        "CREATE TABLE pbdb_collections_animalia_phanerozoic_uby ("
        + ", ".join(f"{column} TEXT" for column in quoted_columns)
        + ")"
    )


def _write_indexes(conn: sqlite3.Connection) -> None:
    table = "pbdb_collections_animalia_phanerozoic_uby"
    for index_name, columns in (
        ("idx_pbdb_collections_uby_value", ("uby_value",)),
        ("idx_pbdb_collections_collection_no", ("collection_no",)),
        ("idx_pbdb_collections_interval", ("early_interval", "late_interval")),
        ("idx_pbdb_collections_environment", ("environment",)),
        ("idx_pbdb_collections_reference", ("reference_no",)),
        ("idx_pbdb_collections_formation", ("formation",)),
    ):
        quoted = ", ".join(_quote_identifier(column) for column in columns)
        conn.execute(f"CREATE INDEX {index_name} ON {table} ({quoted})")


def write_outputs() -> dict[str, object]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedCollection.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    placeholders = ", ".join("?" for _ in columns)
    insert_sql = (
        f"INSERT INTO pbdb_collections_animalia_phanerozoic_uby ({', '.join(quoted_columns)}) "
        f"VALUES ({placeholders})"
    )

    seen_collection_numbers: set[str] = set()
    stats: dict[str, object] = {
        "raw_rows": 0,
        "record_count": 0,
        "skipped_records": 0,
        "duplicate_records": 0,
        "source_file_count": len(_raw_csvs()),
        "precision_counts": {},
        "environment_counts": {},
        "country_counts": {},
        "research_group_counts": {},
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
            collection_no = (row.get("collection_no") or "").strip()
            if collection_no and collection_no in seen_collection_numbers:
                stats["duplicate_records"] = int(stats["duplicate_records"]) + 1
                stats["skipped_records"] = int(stats["skipped_records"]) + 1
                continue
            if collection_no:
                seen_collection_numbers.add(collection_no)

            record = _annotate_row(row)
            if record is None:
                stats["skipped_records"] = int(stats["skipped_records"]) + 1
                continue

            payload = asdict(record)
            writer.writerow(payload)
            sqlite_batch.append([payload[column] for column in columns])

            stats["record_count"] = int(stats["record_count"]) + 1
            for key, value in (
                ("precision_counts", record.precision_level),
                ("environment_counts", record.environment or "NO_ENVIRONMENT"),
                ("country_counts", record.country or "NO_COUNTRY"),
                ("research_group_counts", record.research_group or "NO_RESEARCH_GROUP"),
            ):
                counts = stats[key]
                assert isinstance(counts, dict)
                counts[value] = int(counts.get(value, 0)) + 1

            if len(sqlite_batch) >= BATCH_INSERT_SIZE:
                conn.executemany(insert_sql, sqlite_batch)
                sqlite_batch.clear()

        if sqlite_batch:
            conn.executemany(insert_sql, sqlite_batch)

        _write_indexes(conn)

    return stats


def _top_counts(stats: dict[str, object], key: str, limit: int = 20) -> dict[str, int]:
    counts = stats.get(key, {})
    assert isinstance(counts, dict)
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit])


def write_metadata(stats: dict[str, object], wall_seconds: float) -> None:
    metadata = {
        "dataset": "Paleobiology Database Animalia Phanerozoic collection paged download with UBY labels",
        "source_api": SOURCE_API,
        "source_files": [str(path.as_posix()) for path in _raw_csvs()],
        "source_file_count": stats["source_file_count"],
        "raw_rows": stats["raw_rows"],
        "record_count": stats["record_count"],
        "skipped_records": stats["skipped_records"],
        "duplicate_records": stats["duplicate_records"],
        "precision_counts": stats["precision_counts"],
        "top_environment_counts": _top_counts(stats, "environment_counts"),
        "top_country_counts": _top_counts(stats, "country_counts"),
        "top_research_group_counts": _top_counts(stats, "research_group_counts"),
        "uby_annotation_principles": [
            "PBDB native min_ma/max_ma collection intervals are preserved.",
            "UBY is added only as an auxiliary cross-scale label/index.",
            "Representative UBY values use midpoint(max_ma,min_ma).",
            "Half interval width is carried as uncertainty_years.",
            "No extra precision beyond PBDB collection age intervals is introduced.",
        ],
        "scientific_use": [
            "Collection-level sampling controls for fossil occurrence analyses.",
            "Formation/reference/geographic/environment standardization.",
            "Future shareholder quorum subsampling and sampling-standardized extinction timing tests.",
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
            "No valid PBDB Animalia Phanerozoic collection CSV batches found. "
            "Run examples/download_pbdb_collections_animalia_phanerozoic.py first."
        )

    start = time.perf_counter()
    stats = write_outputs()
    wall_seconds = time.perf_counter() - start
    write_metadata(stats, wall_seconds)

    print(f"Source files: {stats['source_file_count']}")
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
