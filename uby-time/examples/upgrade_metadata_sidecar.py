"""Upgrade uby_unified_timeline_metadata.json to a C2-compliant sidecar per §21.5.

Reads the existing SQLite database, computes the §21.4 QC summary (per-category
counts, missing-field counts for semantic-track and provenance fields, and
physical-bound-filtered counts), and writes the upgraded metadata sidecar.

Required §21.5 fields:
  - uby_specification_version
  - model_version
  - anchor_id
  - build_timestamp_utc
  - source_datasets (with per-source record counts)
  - qc_summary (per §21.4)
  - software_version
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from uby_time.constants import (
    DEFAULT_ANCHOR_ID,
    DEFAULT_ANCHOR_UBY,
    DEFAULT_MODEL_VERSION,
    GENERATED_BY,
    UBY_SPEC_VERSION,
)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "uby_unified_timeline.sqlite"
META_PATH = ROOT / "data" / "processed" / "uby_unified_timeline_metadata.json"

# §13.2 semantic-track fields (original native time + UBY precision metadata)
SEMANTIC_TRACK_FIELDS = [
    "original_time_unit",
    "original_time_value",
    "original_error",
    "uby_model",
    "uby_precision_level",
    "uby_precision_label",
    "uby_mnemonic_iso",
]

# §22.1 provenance fields
PROVENANCE_FIELDS = [
    "source_dataset",
    "source_record_id",
    "source_doi",
    "source_record_uri",
    "attribution",
]


def _count_missing(conn: sqlite3.Connection, column: str) -> int:
    """Count rows where `column` is NULL or empty string."""
    return conn.execute(
        f"SELECT COUNT(*) FROM uby_events WHERE {column} IS NULL OR {column} = ''"
    ).fetchone()[0]


def _count_by_category(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT event_category, COUNT(*) FROM uby_events GROUP BY event_category"
    ).fetchall()
    return {str(r[0]): int(r[1]) for r in rows}


def _count_by_source(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT source_dataset, COUNT(*) FROM uby_events GROUP BY source_dataset"
    ).fetchall()
    return {str(r[0]): int(r[1]) for r in rows}


def _count_by_precision(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT uby_precision_level, COUNT(*) FROM uby_events GROUP BY uby_precision_level"
    ).fetchall()
    return {str(int(r[0])): int(r[1]) for r in rows}


def _count_physical_bound_filtered(conn: sqlite3.Connection) -> int:
    """Count records that would be flagged by physical-bound filters (§21.3).

    Physical bounds: UBY value must be in [0, anchor_uby]. The anchor_uby
    represents the age of the universe at the anchor epoch (2026-01-01);
    records above it are dated after the universe's current age (impossible)
    and records below 0 predate the Big Bang.
    """
    upper_bound = float(DEFAULT_ANCHOR_UBY)
    return conn.execute(
        "SELECT COUNT(*) FROM uby_events WHERE uby_value < 0 OR uby_value > ?",
        (upper_bound,),
    ).fetchone()[0]


def _total_records(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM uby_events").fetchone()[0]


def _database_file_mtime_utc() -> str:
    ts = DB_PATH.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    if not DB_PATH.exists():
        print(f"ERROR: database not found at {DB_PATH}")
        return 1
    if not META_PATH.exists():
        print(f"ERROR: metadata sidecar not found at {META_PATH}")
        return 1

    # Load existing sidecar to preserve fields not covered by the QC audit
    existing = json.loads(META_PATH.read_text(encoding="utf-8"))

    conn = sqlite3.connect(str(DB_PATH))
    try:
        total = _total_records(conn)
        category_counts = _count_by_category(conn)
        source_counts = _count_by_source(conn)
        precision_counts = _count_by_precision(conn)

        semantic_missing = {
            field: _count_missing(conn, field) for field in SEMANTIC_TRACK_FIELDS
        }
        provenance_missing = {
            field: _count_missing(conn, field) for field in PROVENANCE_FIELDS
        }
        physical_filtered = _count_physical_bound_filtered(conn)
    finally:
        conn.close()

    qc_summary = {
        "total_records": total,
        "category_counts": category_counts,
        "semantic_track_missing": semantic_missing,
        "provenance_missing": provenance_missing,
        "physical_bound_filtered": physical_filtered,
    }

    sidecar = {
        "uby_specification_version": UBY_SPEC_VERSION,
        "model_version": DEFAULT_MODEL_VERSION,
        "anchor_id": DEFAULT_ANCHOR_ID,
        "build_timestamp_utc": _database_file_mtime_utc(),
        "software_version": GENERATED_BY,
        "database": existing.get("database", "UBY Unified Cross-Scale Timeline"),
        "description": existing.get("description", ""),
        "main_table": existing.get("main_table", "uby_events"),
        "views": existing.get("views", []),
        "event_count": total,
        "category_counts": category_counts,
        "precision_counts": precision_counts,
        "source_datasets": source_counts,
        "qc_summary": qc_summary,
        "outputs": existing.get("outputs", {}),
        "core_query_examples": existing.get("core_query_examples", {}),
        "build_performance": existing.get("build_performance", {}),
        "notes": existing.get("notes", []),
    }

    META_PATH.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Upgraded sidecar written to {META_PATH}")
    print(f"  uby_specification_version = {UBY_SPEC_VERSION}")
    print(f"  model_version             = {DEFAULT_MODEL_VERSION}")
    print(f"  anchor_id                 = {DEFAULT_ANCHOR_ID}")
    print(f"  build_timestamp_utc       = {sidecar['build_timestamp_utc']}")
    print(f"  software_version          = {GENERATED_BY}")
    print(f"  total_records             = {total}")
    print(f"  categories                = {len(category_counts)}")
    print(f"  sources                   = {len(source_counts)}")
    print(f"  physical_bound_filtered   = {physical_filtered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
