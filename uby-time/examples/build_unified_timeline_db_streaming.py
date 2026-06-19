#!/usr/bin/env python3
"""
Build the unified UBY timeline database using a streaming pipeline.

This script is intended for large processed datasets such as the full paged PBDB
Animalia/Phanerozoic occurrence download. It writes CSV and SQLite outputs
incrementally instead of holding all unified events in memory.

Output:
- data/processed/uby_unified_timeline.sqlite
- data/processed/uby_unified_timeline.csv
- data/processed/uby_unified_timeline_metadata.json
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
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import GENERATED_BY, UBY_SPEC_VERSION
from uby_time.cosmology import redshift_to_uby

PROCESSED_DIR = ROOT / "data" / "processed"
SQLITE_OUT = PROCESSED_DIR / "uby_unified_timeline.sqlite"
CSV_OUT = PROCESSED_DIR / "uby_unified_timeline.csv"
METADATA_OUT = PROCESSED_DIR / "uby_unified_timeline_metadata.json"

ICS_CSV = PROCESSED_DIR / "ics_chart_uby.csv"
PBDB_CSV = PROCESSED_DIR / "pbdb_dinosauria_uby.csv"
PBDB_ANIMALIA_CSV = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.csv"
NASA_CSV = PROCESSED_DIR / "nasa_exoplanet_archive_uby.csv"
USGS_CSV = PROCESSED_DIR / "usgs_earthquakes_uby_benchmark.csv"
CNEOS_FIREBALLS_CSV = PROCESSED_DIR / "nasa_jpl_cneos_fireballs_uby.csv"
SIMBAD_HIGH_REDSHIFT_CSV = PROCESSED_DIR / "simbad_high_redshift_objects_uby.csv"

SQLITE_BATCH_SIZE = 10000

COSMOLOGICAL_SOURCE_DATASET = "Planck 2018 cosmological milestone compilation"
SIMBAD_SOURCE_DATASET = "SIMBAD Astronomical Database high-redshift objects"
COSMOLOGICAL_SOURCE_DOI = "10.1051/0004-6361/201833910"
COSMOLOGICAL_SOURCE_URI = "https://doi.org/10.1051/0004-6361/201833910"

COSMOLOGICAL_MILESTONES: tuple[dict[str, object], ...] = (
    {
        "event_name": "Big Bang model origin",
        "event_subcategory": "model_origin",
        "original_time_unit": "cosmic_age_years",
        "original_time_value": "0",
        "uby_value": "0",
        "original_error": "",
        "source_record_id": "cosmology-age-0",
        "description": (
            "Conventional UBY model origin at cosmic age 0. This is a model coordinate "
            "origin, not a database observation or a claim about pre-Planck-epoch physics."
        ),
    },
    {
        "event_name": "Cosmic microwave background decoupling",
        "event_subcategory": "reference_milestone",
        "original_time_unit": "redshift",
        "redshift": 1100.0,
        "source_record_id": "cosmology-z-1100",
        "description": (
            "Reference cosmological milestone for recombination / CMB last scattering. "
            "Kept as a model benchmark, not counted as a database object."
        ),
    },
    {
        "event_name": "Planck 2018 reference present cosmic age",
        "event_subcategory": "reference_milestone",
        "original_time_unit": "redshift",
        "redshift": 0.0,
        "source_record_id": "cosmology-z-0",
        "description": (
            "Planck18 astropy reference cosmic age at z=0. Kept as a model benchmark, "
            "not counted as a database object."
        ),
    },
)


@dataclass(frozen=True)
class UnifiedTimelineEvent:
    event_id: int
    event_name: str
    event_category: str
    event_subcategory: str
    original_time_unit: str
    original_time_value: str
    original_error: str
    uby_value: str
    uby_value_text: str
    uby_model: str
    uby_precision_level: int
    uby_precision_label: str
    uby_mnemonic_iso: str
    source_dataset: str
    source_doi: str
    source_record_id: str
    source_record_uri: str
    description: str
    attribution: str


def _iter_csv(path: Path) -> Iterable[dict[str, str]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def _decimal_text(value: str | None) -> str:
    text = _clean(value)
    if text == "":
        return ""
    try:
        return str(Decimal(text))
    except InvalidOperation:
        return text


def _precision_int(value: str | None) -> int:
    text = _clean(value)
    if text == "Level 1":
        return 1
    if text == "Level 2":
        return 2
    if text == "Level 3":
        return 3
    return 0


def _source_doi(source_dataset: str) -> str:
    if "Paleobiology Database" in source_dataset:
        return "10.1111/1475-4983.00265"
    if source_dataset == COSMOLOGICAL_SOURCE_DATASET:
        return COSMOLOGICAL_SOURCE_DOI
    if source_dataset == SIMBAD_SOURCE_DATASET:
        return "2000A&AS..143....9W"
    return ""


def _cosmology_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for milestone in COSMOLOGICAL_MILESTONES:
        if "redshift" in milestone:
            z = float(milestone["redshift"])
            uby = redshift_to_uby(
                z,
                cosmology_name="Planck18",
                model_version="LCDM-Planck2018",
                include_uncertainty=True,
            )
            original_time_value = f"z={z:g}"
            uby_value = _decimal_text(str(uby.uby_value))
            original_error = _decimal_text(str(uby.uncertainty_years)) if uby.uncertainty_years else ""
            description = (
                f"{_clean(str(milestone.get('description')))}; "
                f"{_clean(uby.propagation_note)}"
            )
        else:
            original_time_value = _clean(str(milestone.get("original_time_value")))
            uby_value = _decimal_text(str(milestone.get("uby_value")))
            original_error = _decimal_text(str(milestone.get("original_error")))
            description = _clean(str(milestone.get("description")))

        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(str(milestone.get("event_name"))),
            event_category="cosmology",
            event_subcategory=_clean(str(milestone.get("event_subcategory"))),
            original_time_unit=_clean(str(milestone.get("original_time_unit"))),
            original_time_value=original_time_value,
            original_error=original_error,
            uby_value=uby_value,
            uby_value_text=uby_value,
            uby_model="LCDM-Planck2018",
            uby_precision_level=3,
            uby_precision_label="Level 3",
            uby_mnemonic_iso="",
            source_dataset=COSMOLOGICAL_SOURCE_DATASET,
            source_doi=COSMOLOGICAL_SOURCE_DOI,
            source_record_id=_clean(str(milestone.get("source_record_id"))),
            source_record_uri=COSMOLOGICAL_SOURCE_URI,
            description=description,
            attribution="Planck Collaboration 2018; Astropy cosmology Planck18 age(z)",
        )
        event_id += 1


def _simbad_high_redshift_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(SIMBAD_HIGH_REDSHIFT_CSV):
        object_name = _clean(row.get("object_name"))
        redshift = _clean(row.get("redshift"))
        source_dataset = _clean(row.get("source_dataset")) or SIMBAD_SOURCE_DATASET
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")) or f"Observed high-redshift object {object_name}",
            event_category="cosmology",
            event_subcategory=_clean(row.get("event_type")) or "high_redshift_astronomical_object",
            original_time_unit=_clean(row.get("original_time_unit")) or "redshift",
            original_time_value=_clean(row.get("original_time_value")) or f"z={redshift}",
            original_error=_decimal_text(row.get("uncertainty_years")),
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value_text")) or _decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "LCDM-Planck2018",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")) or "Level 3",
            uby_mnemonic_iso="",
            source_dataset=source_dataset,
            source_doi=_source_doi(source_dataset),
            source_record_id=_clean(row.get("source_record_id")) or object_name,
            source_record_uri=_clean(row.get("source_record_uri")),
            description=(
                f"SIMBAD high-redshift object; object={object_name}; "
                f"type={_clean(row.get('object_type'))}; "
                f"ra={_clean(row.get('right_ascension_deg'))}; "
                f"dec={_clean(row.get('declination_deg'))}; redshift={redshift}"
            ),
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _ics_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(ICS_CSV):
        source_dataset = _clean(row.get("source_dataset"))
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")),
            event_category="geology",
            event_subcategory=_clean(row.get("event_type")) or "geochronology",
            original_time_unit=_clean(row.get("original_time_unit")) or "ma_bp",
            original_time_value=_decimal_text(row.get("original_time_value")),
            original_error=_decimal_text(row.get("uncertainty_years")),
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "none",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")),
            uby_mnemonic_iso="",
            source_dataset=source_dataset,
            source_doi=_source_doi(source_dataset),
            source_record_id=_clean(row.get("source_record_id")),
            source_record_uri=_clean(row.get("source_record_uri")),
            description=f"{_clean(row.get('event_label'))}; source time={_clean(row.get('original_time_value'))} {_clean(row.get('original_time_unit'))}",
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _pbdb_dinosauria_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(PBDB_CSV):
        source_dataset = _clean(row.get("source_dataset"))
        min_ma = _clean(row.get("min_ma"))
        max_ma = _clean(row.get("max_ma"))
        accepted_name = _clean(row.get("accepted_name"))
        interval = "–".join(part for part in (min_ma, max_ma) if part)
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")) or accepted_name,
            event_category="paleontology",
            event_subcategory="fossil_occurrence",
            original_time_unit="ma_bp_interval",
            original_time_value=_decimal_text(row.get("representative_ma_midpoint")),
            original_error=_decimal_text(row.get("uncertainty_years")),
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "none",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")),
            uby_mnemonic_iso="",
            source_dataset=source_dataset,
            source_doi=_source_doi(source_dataset),
            source_record_id=_clean(row.get("source_record_id")),
            source_record_uri=_clean(row.get("source_record_uri")),
            description=f"{accepted_name} fossil occurrence; PBDB interval={interval} Ma BP; formation={_clean(row.get('formation'))}",
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _pbdb_animalia_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(PBDB_ANIMALIA_CSV):
        source_dataset = _clean(row.get("source_dataset"))
        min_ma = _clean(row.get("min_ma"))
        max_ma = _clean(row.get("max_ma"))
        accepted_name = _clean(row.get("accepted_name"))
        interval = "–".join(part for part in (min_ma, max_ma) if part)
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")) or accepted_name,
            event_category="paleontology",
            event_subcategory="fossil_occurrence",
            original_time_unit="ma_bp_interval",
            original_time_value=_decimal_text(row.get("representative_ma_midpoint")),
            original_error=_decimal_text(row.get("uncertainty_years")),
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "none",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")),
            uby_mnemonic_iso="",
            source_dataset=source_dataset,
            source_doi=_source_doi(source_dataset),
            source_record_id=_clean(row.get("source_record_id")),
            source_record_uri=_clean(row.get("source_record_uri")),
            description=f"{accepted_name} fossil occurrence; PBDB interval={interval} Ma BP; formation={_clean(row.get('formation'))}",
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _nasa_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(NASA_CSV):
        source_dataset = _clean(row.get("source_dataset"))
        year = _clean(row.get("discovery_year"))
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")),
            event_category="spaceflight",
            event_subcategory="exoplanet_discovery",
            original_time_unit="gregorian_year",
            original_time_value=year,
            original_error=_decimal_text(row.get("uncertainty_years")),
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "none",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")),
            uby_mnemonic_iso=year,
            source_dataset=source_dataset,
            source_doi=_source_doi(source_dataset),
            source_record_id=_clean(row.get("source_record_id")),
            source_record_uri=_clean(row.get("source_record_uri")),
            description=f"Exoplanet discovery; method={_clean(row.get('discovery_method'))}; facility={_clean(row.get('discovery_facility'))}",
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _cneos_fireball_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(CNEOS_FIREBALLS_CSV):
        source_dataset = _clean(row.get("source_dataset"))
        source_time = _clean(row.get("source_time_utc"))
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")),
            event_category="astronomy",
            event_subcategory=_clean(row.get("event_type")) or "fireball_event_time",
            original_time_unit="gregorian_utc",
            original_time_value=source_time,
            original_error="",
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "none",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")),
            uby_mnemonic_iso=source_time,
            source_dataset=source_dataset,
            source_doi="",
            source_record_id=_clean(row.get("source_record_id")),
            source_record_uri=_clean(row.get("source_record_uri")),
            description=(
                f"NASA/JPL CNEOS fireball; energy_kt={_clean(row.get('energy_kt'))}; "
                f"impact_energy_kt={_clean(row.get('impact_energy_kt'))}; "
                f"lat={_clean(row.get('latitude'))}; lon={_clean(row.get('longitude'))}; "
                f"alt_km={_clean(row.get('altitude_km'))}; vel_km_s={_clean(row.get('velocity_km_s'))}"
            ),
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _usgs_events(start_id: int) -> Iterable[UnifiedTimelineEvent]:
    event_id = start_id
    for row in _iter_csv(USGS_CSV):
        source_dataset = _clean(row.get("source_dataset"))
        source_time = _clean(row.get("source_time_utc"))
        yield UnifiedTimelineEvent(
            event_id=event_id,
            event_name=_clean(row.get("event_label")),
            event_category="geology",
            event_subcategory="earthquake",
            original_time_unit="gregorian_utc",
            original_time_value=source_time,
            original_error="",
            uby_value=_decimal_text(row.get("uby_value")),
            uby_value_text=_decimal_text(row.get("uby_value")),
            uby_model=_clean(row.get("model_version")) or "none",
            uby_precision_level=_precision_int(row.get("precision_level")),
            uby_precision_label=_clean(row.get("precision_level")),
            uby_mnemonic_iso=source_time,
            source_dataset=source_dataset,
            source_doi=_source_doi(source_dataset),
            source_record_id=_clean(row.get("source_record_id")),
            source_record_uri=_clean(row.get("source_record_uri")),
            description=f"USGS earthquake; magnitude={_clean(row.get('magnitude'))}; place={_clean(row.get('place'))}",
            attribution=_clean(row.get("attribution")),
        )
        event_id += 1


def _create_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE uby_events (
            event_id INTEGER PRIMARY KEY,
            event_name TEXT NOT NULL,
            event_category TEXT NOT NULL,
            event_subcategory TEXT,
            original_time_unit TEXT,
            original_time_value TEXT,
            original_error TEXT,
            uby_value REAL NOT NULL,
            uby_value_text TEXT NOT NULL,
            uby_model TEXT,
            uby_precision_level INTEGER NOT NULL,
            uby_precision_label TEXT,
            uby_mnemonic_iso TEXT,
            source_dataset TEXT NOT NULL,
            source_doi TEXT,
            source_record_id TEXT,
            source_record_uri TEXT,
            description TEXT,
            attribution TEXT
        )
        """
    )


def _finalize_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX idx_uby_events_uby_value ON uby_events (uby_value)")
    conn.execute("CREATE INDEX idx_uby_events_category ON uby_events (event_category)")
    conn.execute("CREATE INDEX idx_uby_events_precision ON uby_events (uby_precision_level)")
    conn.execute("CREATE INDEX idx_uby_events_source_dataset ON uby_events (source_dataset)")
    conn.execute("CREATE INDEX idx_uby_events_category_uby ON uby_events (event_category, uby_value)")
    conn.execute(
        """
        CREATE VIEW uby_events_summary AS
        SELECT
            event_category,
            event_subcategory,
            uby_precision_level,
            COUNT(*) AS event_count,
            MIN(uby_value) AS min_uby_value,
            MAX(uby_value) AS max_uby_value
        FROM uby_events
        GROUP BY event_category, event_subcategory, uby_precision_level
        """
    )
    conn.execute(
        """
        CREATE VIEW uby_cross_domain_timeline AS
        SELECT
            event_id,
            event_name,
            event_category,
            event_subcategory,
            original_time_unit,
            original_time_value,
            original_error,
            uby_value,
            uby_precision_level,
            source_dataset,
            source_record_uri,
            description
        FROM uby_events
        ORDER BY uby_value, uby_precision_level, event_id
        """
    )


def build_outputs() -> dict[str, object]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(UnifiedTimelineEvent.__dataclass_fields__)
    placeholders = ", ".join("?" for _ in columns)
    insert_sql = f"INSERT INTO uby_events ({', '.join(columns)}) VALUES ({placeholders})"

    category_counts: dict[str, int] = {}
    precision_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    event_count = 0
    next_id = 1

    producers: tuple[Callable[[int], Iterable[UnifiedTimelineEvent]], ...] = (
        _cosmology_events,
        _simbad_high_redshift_events,
        _ics_events,
        _pbdb_dinosauria_events,
        _pbdb_animalia_events,
        _nasa_events,
        _cneos_fireball_events,
        _usgs_events,
    )

    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as csv_file, sqlite3.connect(SQLITE_OUT) as conn:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()

        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        _create_sqlite(conn)

        batch: list[list[object]] = []
        for producer in producers:
            for event in producer(next_id):
                next_id = event.event_id + 1
                event_count += 1

                category_counts[event.event_category] = category_counts.get(event.event_category, 0) + 1
                precision_key = str(event.uby_precision_level)
                precision_counts[precision_key] = precision_counts.get(precision_key, 0) + 1
                source_counts[event.source_dataset] = source_counts.get(event.source_dataset, 0) + 1

                payload = asdict(event)
                writer.writerow(payload)
                batch.append([payload[column] for column in columns])

                if len(batch) >= SQLITE_BATCH_SIZE:
                    conn.executemany(insert_sql, batch)
                    batch.clear()

        if batch:
            conn.executemany(insert_sql, batch)

        _finalize_sqlite(conn)

    return {
        "event_count": event_count,
        "category_counts": category_counts,
        "precision_counts": precision_counts,
        "source_counts": source_counts,
    }


def write_metadata(stats: dict[str, object], wall_seconds: float) -> None:
    event_count = int(stats["event_count"])
    metadata = {
        "database": "UBY Unified Cross-Scale Timeline",
        "description": (
            "Single-file SQLite database integrating heterogeneous cosmology, geology, "
            "paleontology, astronomy, space discovery, and geophysical event datasets through UBY "
            "as a common temporal key."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "event_count": event_count,
        "category_counts": stats["category_counts"],
        "precision_counts": stats["precision_counts"],
        "source_counts": stats["source_counts"],
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "csv": str(CSV_OUT.as_posix()),
        },
        "main_table": "uby_events",
        "views": ["uby_events_summary", "uby_cross_domain_timeline"],
        "core_query_examples": {
            "full_timeline": "SELECT * FROM uby_cross_domain_timeline ORDER BY uby_value LIMIT 100;",
            "cretaceous_to_jurassic_paleontology": (
                "SELECT event_name, original_time_value, original_time_unit, uby_value "
                "FROM uby_events WHERE event_category='paleontology' "
                "AND original_time_unit='ma_bp_interval' "
                "ORDER BY uby_value;"
            ),
            "cosmological_level3_events": (
                "SELECT event_name, original_time_value, uby_value, original_error, description "
                "FROM uby_events WHERE uby_precision_level=3 ORDER BY uby_value;"
            ),
            "modern_level1_events": (
                "SELECT event_name, event_category, uby_mnemonic_iso, uby_value "
                "FROM uby_events WHERE uby_precision_level=1 ORDER BY uby_value DESC LIMIT 50;"
            ),
            "cross_domain_window": (
                "SELECT event_name, event_category, event_subcategory, uby_value, source_dataset "
                "FROM uby_events WHERE uby_value BETWEEN ? AND ? ORDER BY uby_value;"
            ),
        },
        "build_performance": {
            "wall_seconds": wall_seconds,
            "records_per_second": event_count / wall_seconds if wall_seconds else 0,
        },
        "notes": [
            "uby_value is stored as REAL for direct SQLite range indexing and uby_value_text preserves the decimal string.",
            "original_time_value remains text because native source time values may be ISO timestamps, years, Ma midpoints, or other unit-specific values.",
            "source_doi is populated only where a stable dataset DOI is known; otherwise source_record_uri and attribution carry provenance.",
            "This database includes Level 3 cosmology records from SIMBAD/CDS high-redshift database objects, plus a minimal set of explicitly labeled cosmological model reference milestones.",
            "This database was built with the streaming builder to support million-row PBDB inputs.",
        ],
    }
    METADATA_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    start = time.perf_counter()
    stats = build_outputs()
    wall_seconds = time.perf_counter() - start
    write_metadata(stats, wall_seconds)

    print(f"Unified events: {stats['event_count']}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"CSV: {CSV_OUT}")
    print(f"Metadata: {METADATA_OUT}")
    print(f"Build wall seconds: {wall_seconds:.6f}")
    print(f"Build records/s: {int(stats['event_count']) / wall_seconds if wall_seconds else 0:.2f}")
    print("Category counts:")
    for key, value in sorted(dict(stats["category_counts"]).items()):
        print(f"- {key}: {value}")

    with sqlite3.connect(SQLITE_OUT) as conn:
        print("Timeline sample:")
        for row in conn.execute(
            """
            SELECT event_id, event_name, event_category, original_time_unit, original_time_value, uby_value
            FROM uby_events
            ORDER BY uby_value
            LIMIT 5
            """
        ):
            print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
