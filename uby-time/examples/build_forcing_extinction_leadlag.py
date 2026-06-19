#!/usr/bin/env python3
"""
Build forcing-extinction lead-lag analysis from PBDB-derived extinction dynamics.

This script joins:
- data/processed/pbdb_extinction_dynamics.sqlite
- data/processed/uby_forcing_events.sqlite

It produces a reproducible lead-lag table linking DOI-backed forcing-event
anchors to PBDB-derived extinction/recovery/disappearance metrics around
reference mass-extinction boundaries.

Outputs:
- data/processed/uby_forcing_extinction_leadlag.sqlite
- data/processed/uby_forcing_extinction_leadlag_pairs.csv
- data/processed/uby_forcing_extinction_leadlag_report.json

Scientific boundary:
This is a first-pass integration layer.  Extinction-side signals are derived
from full PBDB occurrences.  Forcing-side records are DOI-backed reference
anchors, but not yet complete frozen external compilations.  Treat output as a
hypothesis-generation and conformance dataset, not a final causal inference.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import GENERATED_BY, UBY_SPEC_VERSION

PROCESSED_DIR = ROOT / "data" / "processed"
EXTINCTION_DB = PROCESSED_DIR / "pbdb_extinction_dynamics.sqlite"
FORCING_DB = PROCESSED_DIR / "uby_forcing_events.sqlite"
FORCING_CSV = PROCESSED_DIR / "uby_forcing_events.csv"

SQLITE_OUT = PROCESSED_DIR / "uby_forcing_extinction_leadlag.sqlite"
PAIRS_CSV_OUT = PROCESSED_DIR / "uby_forcing_extinction_leadlag_pairs.csv"
REPORT_OUT = PROCESSED_DIR / "uby_forcing_extinction_leadlag_report.json"

MILLION = Decimal("1000000")
DEFAULT_WINDOW_YEARS = Decimal("5000000")


@dataclass(frozen=True)
class ForcingExtinctionPair:
    extinction_event_name: str
    extinction_ma: str
    extinction_uby_value: str
    extinction_uncertainty_years: str
    extinction_event_bin_standing_taxa: int
    extinction_boundary_bin_last_appearances: int
    extinction_boundary_bin_extinction_intensity: str
    extinction_disappearing_taxa: int
    extinction_disappearances_before_boundary: int
    extinction_disappearances_after_boundary: int
    extinction_mean_disappearance_lag_years: str
    extinction_recovery_lag_years: str
    forcing_event_name: str
    forcing_category: str
    forcing_subcategory: str
    forcing_ma: str
    forcing_uby_value: str
    forcing_uncertainty_years: str
    forcing_duration_ma: str
    forcing_confidence_level: str
    forcing_source_doi: str
    lag_years: str
    abs_lag_years: str
    lag_direction: str
    uncertainty_overlap_flag: int
    combined_uncertainty_years: str
    window_years: str
    pair_key: str


def _require_inputs() -> None:
    missing = [str(path) for path in (EXTINCTION_DB, FORCING_DB, FORCING_CSV) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required inputs: {', '.join(missing)}")


def _copy_extinction_db() -> None:
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    with sqlite3.connect(EXTINCTION_DB) as source, sqlite3.connect(SQLITE_OUT) as target:
        source.backup(target)


def _attach_forcing(conn: sqlite3.Connection) -> None:
    """Copy forcing events into the output database.

    The forcing compilation is distributed as both SQLite and CSV.  Use the CSV
    as the integration source here because it is append-only text and avoids any
    platform-specific SQLite attach/cache issues while preserving the same
    schema and provenance.
    """
    with FORCING_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    conn.execute("DROP TABLE IF EXISTS forcing_events")
    conn.execute(
        """
        CREATE TABLE forcing_events (
            event_name TEXT NOT NULL,
            forcing_category TEXT NOT NULL,
            forcing_subcategory TEXT NOT NULL,
            ma_bp REAL NOT NULL,
            uncertainty_ma REAL NOT NULL,
            duration_ma REAL,
            source_compilation TEXT NOT NULL,
            source_doi TEXT,
            source_record_id TEXT PRIMARY KEY,
            source_record_uri TEXT,
            evidence_type TEXT,
            confidence_level TEXT,
            notes TEXT,
            original_time_unit TEXT NOT NULL,
            uby_value TEXT NOT NULL,
            uby_value_float REAL NOT NULL,
            uby_model TEXT NOT NULL,
            uby_precision_level INTEGER NOT NULL,
            uby_precision_label TEXT NOT NULL,
            uncertainty_years TEXT NOT NULL,
            generated_by TEXT NOT NULL,
            uby_version TEXT NOT NULL
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO forcing_events VALUES (
            :event_name,
            :forcing_category,
            :forcing_subcategory,
            :ma_bp,
            :uncertainty_ma,
            :duration_ma,
            :source_compilation,
            :source_doi,
            :source_record_id,
            :source_record_uri,
            :evidence_type,
            :confidence_level,
            :notes,
            :original_time_unit,
            :uby_value,
            :uby_value_float,
            :uby_model,
            :uby_precision_level,
            :uby_precision_label,
            :uncertainty_years,
            :generated_by,
            :uby_version
        )
        """,
        rows,
    )
    conn.execute("CREATE INDEX idx_integrated_forcing_ma ON forcing_events (ma_bp)")
    conn.execute("CREATE INDEX idx_integrated_forcing_category ON forcing_events (forcing_category)")
    conn.commit()


def _create_pairs_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS forcing_extinction_leadlag_pairs")
    conn.execute(
        """
        CREATE TABLE forcing_extinction_leadlag_pairs (
            extinction_event_name TEXT NOT NULL,
            extinction_ma TEXT NOT NULL,
            extinction_uby_value TEXT NOT NULL,
            extinction_uncertainty_years TEXT NOT NULL,
            extinction_event_bin_standing_taxa INTEGER NOT NULL,
            extinction_boundary_bin_last_appearances INTEGER NOT NULL,
            extinction_boundary_bin_extinction_intensity TEXT NOT NULL,
            extinction_disappearing_taxa INTEGER NOT NULL,
            extinction_disappearances_before_boundary INTEGER NOT NULL,
            extinction_disappearances_after_boundary INTEGER NOT NULL,
            extinction_mean_disappearance_lag_years TEXT NOT NULL,
            extinction_recovery_lag_years TEXT NOT NULL,
            forcing_event_name TEXT NOT NULL,
            forcing_category TEXT NOT NULL,
            forcing_subcategory TEXT NOT NULL,
            forcing_ma TEXT NOT NULL,
            forcing_uby_value TEXT NOT NULL,
            forcing_uncertainty_years TEXT NOT NULL,
            forcing_duration_ma TEXT NOT NULL,
            forcing_confidence_level TEXT NOT NULL,
            forcing_source_doi TEXT,
            lag_years TEXT NOT NULL,
            abs_lag_years TEXT NOT NULL,
            lag_direction TEXT NOT NULL,
            uncertainty_overlap_flag INTEGER NOT NULL,
            combined_uncertainty_years TEXT NOT NULL,
            window_years TEXT NOT NULL,
            pair_key TEXT NOT NULL
        )
        """
    )


def _build_pairs(conn: sqlite3.Connection, window_years: Decimal = DEFAULT_WINDOW_YEARS) -> list[ForcingExtinctionPair]:
    conn.row_factory = sqlite3.Row

    extinctions = conn.execute(
        """
        SELECT
            r.event_name,
            r.ma_bp,
            r.uby_value,
            r.uncertainty_ma,
            COALESCE(i.standing_taxa, 0) AS event_bin_standing_taxa,
            COALESCE(i.last_appearances, 0) AS boundary_bin_last_appearances,
            COALESCE(i.extinction_intensity, 0) AS boundary_bin_extinction_intensity,
            COALESCE(d.disappearing_taxa, 0) AS disappearing_taxa,
            COALESCE(d.before_boundary, 0) AS before_boundary,
            COALESCE(d.after_boundary, 0) AS after_boundary,
            COALESCE(d.mean_lag_years, 0) AS mean_disappearance_lag_years,
            COALESCE(recovery.recovery_lag_years, '') AS recovery_lag_years
        FROM reference_mass_extinctions r
        LEFT JOIN pbdb_extinction_intensity_by_bin i
          ON CAST(r.ma_bp AS INTEGER) = i.bin_id
        LEFT JOIN pbdb_disappearance_summary_by_event d
          ON r.event_name = d.event_name
        LEFT JOIN pbdb_recovery_lag recovery
          ON r.event_name = recovery.event_name
        ORDER BY r.ma_bp DESC
        """
    ).fetchall()

    forcings = conn.execute(
        """
        SELECT
            event_name,
            forcing_category,
            forcing_subcategory,
            ma_bp,
            uncertainty_ma,
            duration_ma,
            source_doi,
            source_record_id,
            uby_value,
            uncertainty_years,
            confidence_level
        FROM forcing_events
        ORDER BY ma_bp DESC
        """
    ).fetchall()

    pairs: list[ForcingExtinctionPair] = []

    for extinction in extinctions:
        extinction_ma = Decimal(str(extinction["ma_bp"]))
        extinction_uby = Decimal(str(extinction["uby_value"]))
        extinction_uncertainty_years = Decimal(str(extinction["uncertainty_ma"])) * MILLION

        for forcing in forcings:
            forcing_ma = Decimal(str(forcing["ma_bp"]))
            forcing_uby = Decimal(str(forcing["uby_value"]))
            forcing_uncertainty_years = Decimal(str(forcing["uncertainty_years"]))
            lag_years = extinction_uby - forcing_uby
            abs_lag_years = abs(lag_years)

            if abs_lag_years > window_years:
                continue

            if lag_years > 0:
                lag_direction = "forcing_precedes_extinction"
            elif lag_years < 0:
                lag_direction = "forcing_follows_extinction"
            else:
                lag_direction = "same_representative_time"

            combined_uncertainty = extinction_uncertainty_years + forcing_uncertainty_years
            uncertainty_overlap_flag = int(abs_lag_years <= combined_uncertainty)

            pair = ForcingExtinctionPair(
                extinction_event_name=str(extinction["event_name"]),
                extinction_ma=str(extinction_ma),
                extinction_uby_value=str(extinction_uby),
                extinction_uncertainty_years=str(extinction_uncertainty_years),
                extinction_event_bin_standing_taxa=int(extinction["event_bin_standing_taxa"]),
                extinction_boundary_bin_last_appearances=int(extinction["boundary_bin_last_appearances"]),
                extinction_boundary_bin_extinction_intensity=str(extinction["boundary_bin_extinction_intensity"]),
                extinction_disappearing_taxa=int(extinction["disappearing_taxa"]),
                extinction_disappearances_before_boundary=int(extinction["before_boundary"]),
                extinction_disappearances_after_boundary=int(extinction["after_boundary"]),
                extinction_mean_disappearance_lag_years=str(extinction["mean_disappearance_lag_years"]),
                extinction_recovery_lag_years=str(extinction["recovery_lag_years"]),
                forcing_event_name=str(forcing["event_name"]),
                forcing_category=str(forcing["forcing_category"]),
                forcing_subcategory=str(forcing["forcing_subcategory"]),
                forcing_ma=str(forcing_ma),
                forcing_uby_value=str(forcing_uby),
                forcing_uncertainty_years=str(forcing_uncertainty_years),
                forcing_duration_ma=str(forcing["duration_ma"]),
                forcing_confidence_level=str(forcing["confidence_level"]),
                forcing_source_doi=str(forcing["source_doi"] or ""),
                lag_years=str(lag_years),
                abs_lag_years=str(abs_lag_years),
                lag_direction=lag_direction,
                uncertainty_overlap_flag=uncertainty_overlap_flag,
                combined_uncertainty_years=str(combined_uncertainty),
                window_years=str(window_years),
                pair_key=f"{extinction['event_name']}::{forcing['source_record_id']}",
            )
            pairs.append(pair)

    conn.executemany(
        """
        INSERT INTO forcing_extinction_leadlag_pairs VALUES (
            :extinction_event_name,
            :extinction_ma,
            :extinction_uby_value,
            :extinction_uncertainty_years,
            :extinction_event_bin_standing_taxa,
            :extinction_boundary_bin_last_appearances,
            :extinction_boundary_bin_extinction_intensity,
            :extinction_disappearing_taxa,
            :extinction_disappearances_before_boundary,
            :extinction_disappearances_after_boundary,
            :extinction_mean_disappearance_lag_years,
            :extinction_recovery_lag_years,
            :forcing_event_name,
            :forcing_category,
            :forcing_subcategory,
            :forcing_ma,
            :forcing_uby_value,
            :forcing_uncertainty_years,
            :forcing_duration_ma,
            :forcing_confidence_level,
            :forcing_source_doi,
            :lag_years,
            :abs_lag_years,
            :lag_direction,
            :uncertainty_overlap_flag,
            :combined_uncertainty_years,
            :window_years,
            :pair_key
        )
        """,
        [asdict(pair) for pair in pairs],
    )

    conn.execute("CREATE INDEX idx_fel_pairs_extinction ON forcing_extinction_leadlag_pairs (extinction_event_name)")
    conn.execute("CREATE INDEX idx_fel_pairs_forcing_category ON forcing_extinction_leadlag_pairs (forcing_category)")
    conn.execute("CREATE INDEX idx_fel_pairs_forcing_subcategory ON forcing_extinction_leadlag_pairs (forcing_subcategory)")
    conn.execute("CREATE INDEX idx_fel_pairs_abs_lag ON forcing_extinction_leadlag_pairs (abs_lag_years)")
    conn.execute("CREATE INDEX idx_fel_pairs_direction ON forcing_extinction_leadlag_pairs (lag_direction)")
    conn.execute("CREATE INDEX idx_fel_pairs_overlap ON forcing_extinction_leadlag_pairs (uncertainty_overlap_flag)")

    conn.execute("DROP VIEW IF EXISTS forcing_extinction_lag_summary")
    conn.execute(
        """
        CREATE VIEW forcing_extinction_lag_summary AS
        SELECT
            forcing_category,
            forcing_subcategory,
            lag_direction,
            COUNT(*) AS pair_count,
            AVG(CAST(lag_years AS REAL)) AS mean_lag_years,
            MIN(CAST(lag_years AS REAL)) AS min_lag_years,
            MAX(CAST(lag_years AS REAL)) AS max_lag_years,
            SUM(uncertainty_overlap_flag) AS uncertainty_overlap_pairs,
            AVG(CAST(extinction_disappearing_taxa AS REAL)) AS mean_disappearing_taxa,
            AVG(CAST(extinction_boundary_bin_extinction_intensity AS REAL)) AS mean_boundary_extinction_intensity
        FROM forcing_extinction_leadlag_pairs
        GROUP BY forcing_category, forcing_subcategory, lag_direction
        ORDER BY forcing_category, forcing_subcategory, lag_direction
        """
    )

    conn.execute("DROP VIEW IF EXISTS nearest_forcing_by_extinction")
    conn.execute(
        """
        CREATE VIEW nearest_forcing_by_extinction AS
        SELECT *
        FROM forcing_extinction_leadlag_pairs p
        WHERE CAST(abs_lag_years AS REAL) = (
            SELECT MIN(CAST(q.abs_lag_years AS REAL))
            FROM forcing_extinction_leadlag_pairs q
            WHERE q.extinction_event_name = p.extinction_event_name
        )
        ORDER BY extinction_ma DESC, CAST(abs_lag_years AS REAL), forcing_event_name
        """
    )

    return pairs


def _write_pairs_csv(pairs: list[ForcingExtinctionPair]) -> None:
    with PAIRS_CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(ForcingExtinctionPair.__dataclass_fields__))
        writer.writeheader()
        for pair in pairs:
            writer.writerow(asdict(pair))


def _write_report(conn: sqlite3.Connection, pairs: list[ForcingExtinctionPair], wall_seconds: float) -> None:
    conn.row_factory = None

    direction_counts = dict(
        conn.execute(
            """
            SELECT lag_direction, COUNT(*)
            FROM forcing_extinction_leadlag_pairs
            GROUP BY lag_direction
            ORDER BY lag_direction
            """
        ).fetchall()
    )
    category_counts = dict(
        conn.execute(
            """
            SELECT forcing_category, COUNT(*)
            FROM forcing_extinction_leadlag_pairs
            GROUP BY forcing_category
            ORDER BY forcing_category
            """
        ).fetchall()
    )
    overlap_count = conn.execute(
        "SELECT COUNT(*) FROM forcing_extinction_leadlag_pairs WHERE uncertainty_overlap_flag=1"
    ).fetchone()[0]
    nearest_pairs = conn.execute(
        """
        SELECT
            extinction_event_name,
            forcing_event_name,
            forcing_category,
            forcing_subcategory,
            lag_years,
            abs_lag_years,
            lag_direction,
            uncertainty_overlap_flag,
            extinction_disappearing_taxa,
            extinction_recovery_lag_years
        FROM nearest_forcing_by_extinction
        ORDER BY extinction_ma DESC, CAST(abs_lag_years AS REAL), forcing_event_name
        """
    ).fetchall()
    summary = conn.execute(
        """
        SELECT
            forcing_category,
            forcing_subcategory,
            lag_direction,
            pair_count,
            mean_lag_years,
            uncertainty_overlap_pairs,
            mean_disappearing_taxa,
            mean_boundary_extinction_intensity
        FROM forcing_extinction_lag_summary
        ORDER BY forcing_category, forcing_subcategory, lag_direction
        """
    ).fetchall()

    report = {
        "database": "UBY forcing-extinction lead-lag analysis",
        "description": (
            "Lead-lag pairs between DOI-backed forcing-event anchors and PBDB-derived "
            "mass-extinction dynamics on a unified UBY axis."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "inputs": {
            "extinction_dynamics_sqlite": str(EXTINCTION_DB.as_posix()),
            "forcing_events_sqlite": str(FORCING_DB.as_posix()),
            "forcing_events_csv": str(FORCING_CSV.as_posix()),
        },
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "pairs_csv": str(PAIRS_CSV_OUT.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "window_years": str(DEFAULT_WINDOW_YEARS),
        "counts": {
            "forcing_extinction_pairs": len(pairs),
            "uncertainty_overlap_pairs": overlap_count,
            "direction_counts": direction_counts,
            "forcing_category_pair_counts": category_counts,
        },
        "nearest_forcing_by_extinction": [
            {
                "extinction_event_name": row[0],
                "forcing_event_name": row[1],
                "forcing_category": row[2],
                "forcing_subcategory": row[3],
                "lag_years": row[4],
                "abs_lag_years": row[5],
                "lag_direction": row[6],
                "uncertainty_overlap_flag": row[7],
                "extinction_disappearing_taxa": row[8],
                "extinction_recovery_lag_years": row[9],
            }
            for row in nearest_pairs
        ],
        "forcing_extinction_lag_summary": [
            {
                "forcing_category": row[0],
                "forcing_subcategory": row[1],
                "lag_direction": row[2],
                "pair_count": row[3],
                "mean_lag_years": row[4],
                "uncertainty_overlap_pairs": row[5],
                "mean_disappearing_taxa": row[6],
                "mean_boundary_extinction_intensity": row[7],
            }
            for row in summary
        ],
        "research_status": "integrated_forcing_extinction_first_pass_not_final_causal_claim",
        "claim_boundary": [
            "Extinction-side metrics are PBDB-derived but use a first-pass range-through midpoint method.",
            "Forcing-side records are DOI-backed reference anchors but not yet complete frozen external databases.",
            "Lag direction is temporal association only, not causal attribution.",
            "Publication-grade inference requires sampling correction, Monte Carlo uncertainty propagation, and independent forcing compilations.",
        ],
        "build_performance": {
            "wall_seconds": wall_seconds,
            "pairs_per_second": len(pairs) / wall_seconds if wall_seconds else 0,
        },
    }

    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    start = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    _require_inputs()

    _copy_extinction_db()

    with sqlite3.connect(SQLITE_OUT) as conn:
        _attach_forcing(conn)
        _create_pairs_table(conn)
        pairs = _build_pairs(conn)
        _write_pairs_csv(pairs)

        wall_seconds = time.perf_counter() - start
        _write_report(conn, pairs, wall_seconds)

        print(f"Forcing-extinction pairs: {len(pairs)}")
        print(f"SQLite: {SQLITE_OUT}")
        print(f"Pairs CSV: {PAIRS_CSV_OUT}")
        print(f"Report: {REPORT_OUT}")
        print(f"Build wall seconds: {wall_seconds:.6f}")

        print("Nearest forcing by extinction:")
        for row in conn.execute(
            """
            SELECT extinction_event_name, forcing_event_name, forcing_category, lag_years, uncertainty_overlap_flag
            FROM nearest_forcing_by_extinction
            ORDER BY extinction_ma DESC, CAST(abs_lag_years AS REAL), forcing_event_name
            """
        ):
            print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
