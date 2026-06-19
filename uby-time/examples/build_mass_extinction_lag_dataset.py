#!/usr/bin/env python3
"""
Build a UBY mass-extinction lead-lag analysis dataset.

This script is the first concrete scientific-discovery layer on top of the
unified UBY timeline database.  It copies the existing heterogeneous `uby_events`
table, inserts a small curated seed set of extinction and forcing events, and
derives cross-domain extinction-forcing pairs for lead-lag analysis.

The curated seed set is intentionally small and transparent.  It is not intended
to be a final scientific database; it is an executable research scaffold showing
how UBY can turn heterogeneous deep-time event data into reproducible lag
queries.

Input:
- data/processed/uby_unified_timeline.sqlite

Output:
- data/processed/uby_mass_extinction_lag.sqlite
- data/processed/uby_mass_extinction_lag_pairs.csv
- data/processed/uby_mass_extinction_lag_report.json
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

from uby_time.constants import DEFAULT_MODEL_VERSION, GENERATED_BY, UBY_SPEC_VERSION

PROCESSED_DIR = ROOT / "data" / "processed"
UNIFIED_DB = PROCESSED_DIR / "uby_unified_timeline.sqlite"

SQLITE_OUT = PROCESSED_DIR / "uby_mass_extinction_lag.sqlite"
PAIRS_CSV_OUT = PROCESSED_DIR / "uby_mass_extinction_lag_pairs.csv"
REPORT_OUT = PROCESSED_DIR / "uby_mass_extinction_lag_report.json"

MODEL_BASE_UBY = Decimal("13787000000")
MILLION = Decimal("1000000")
DEFAULT_WINDOW_YEARS = Decimal("5000000")


@dataclass(frozen=True)
class CuratedDeepTimeEvent:
    event_name: str
    event_category: str
    event_subcategory: str
    ma_bp: str
    uncertainty_ma: str
    source_dataset: str
    source_doi: str
    source_record_id: str
    source_record_uri: str
    description: str
    attribution: str

    @property
    def uby_value(self) -> Decimal:
        return MODEL_BASE_UBY - Decimal(self.ma_bp) * MILLION

    @property
    def uncertainty_years(self) -> Decimal:
        return Decimal(self.uncertainty_ma) * MILLION


@dataclass(frozen=True)
class ExtinctionForcingPair:
    extinction_event_id: int
    extinction_event_name: str
    extinction_subcategory: str
    extinction_ma_bp: str
    extinction_uby_value: str
    extinction_uncertainty_years: str
    forcing_event_id: int
    forcing_event_name: str
    forcing_subcategory: str
    forcing_ma_bp: str
    forcing_uby_value: str
    forcing_uncertainty_years: str
    lag_years: str
    abs_lag_years: str
    window_years: str
    overlap_flag: int
    lag_direction: str
    source_pair_key: str


MASS_EXTINCTION_EVENTS: tuple[CuratedDeepTimeEvent, ...] = (
    CuratedDeepTimeEvent(
        event_name="End-Ordovician mass extinction",
        event_category="paleontology",
        event_subcategory="extinction_boundary",
        ma_bp="443.8",
        uncertainty_ma="1.5",
        source_dataset="Curated mass-extinction seed table",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="end_ordovician_extinction",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        description="Seed event for the Late Ordovician mass extinction boundary; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="Late Devonian Kellwasser extinction pulse",
        event_category="paleontology",
        event_subcategory="extinction_boundary",
        ma_bp="372.2",
        uncertainty_ma="1.6",
        source_dataset="Curated mass-extinction seed table",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="late_devonian_kellwasser",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        description="Seed event for the Frasnian-Famennian/Kellwasser extinction pulse; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="Late Devonian Hangenberg extinction pulse",
        event_category="paleontology",
        event_subcategory="extinction_boundary",
        ma_bp="358.9",
        uncertainty_ma="0.4",
        source_dataset="Curated mass-extinction seed table",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="late_devonian_hangenberg",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        description="Seed event for the Devonian-Carboniferous/Hangenberg extinction pulse; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="End-Permian mass extinction",
        event_category="paleontology",
        event_subcategory="extinction_boundary",
        ma_bp="251.902",
        uncertainty_ma="0.024",
        source_dataset="Curated mass-extinction seed table",
        source_doi="10.1126/science.aaa1152",
        source_record_id="end_permian_extinction",
        source_record_uri="https://doi.org/10.1126/science.aaa1152",
        description="Seed event for the Permian-Triassic mass extinction boundary; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="End-Triassic mass extinction",
        event_category="paleontology",
        event_subcategory="extinction_boundary",
        ma_bp="201.36",
        uncertainty_ma="0.17",
        source_dataset="Curated mass-extinction seed table",
        source_doi="10.1126/science.1234204",
        source_record_id="end_triassic_extinction",
        source_record_uri="https://doi.org/10.1126/science.1234204",
        description="Seed event for the Triassic-Jurassic mass extinction boundary; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="End-Cretaceous mass extinction",
        event_category="paleontology",
        event_subcategory="extinction_boundary",
        ma_bp="66.043",
        uncertainty_ma="0.011",
        source_dataset="Curated mass-extinction seed table",
        source_doi="10.1126/science.1230492",
        source_record_id="end_cretaceous_extinction",
        source_record_uri="https://doi.org/10.1126/science.1230492",
        description="Seed event for the Cretaceous-Paleogene mass extinction boundary; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
)

FORCING_EVENTS: tuple[CuratedDeepTimeEvent, ...] = (
    CuratedDeepTimeEvent(
        event_name="Viluy Traps volcanism seed event",
        event_category="geology",
        event_subcategory="large_igneous_province",
        ma_bp="372.0",
        uncertainty_ma="2.0",
        source_dataset="Curated large igneous province seed table",
        source_doi="",
        source_record_id="viluy_traps_seed",
        source_record_uri="",
        description="Seed large-igneous-province event near the Late Devonian interval; representative age in Ma BP.",
        attribution="Curated seed record for UBY lead-lag demonstration; replace with authoritative LIP compilation for publication.",
    ),
    CuratedDeepTimeEvent(
        event_name="Siberian Traps main magmatic pulse",
        event_category="geology",
        event_subcategory="large_igneous_province",
        ma_bp="252.24",
        uncertainty_ma="0.10",
        source_dataset="Curated large igneous province seed table",
        source_doi="10.1126/science.aaa1152",
        source_record_id="siberian_traps_main_pulse",
        source_record_uri="https://doi.org/10.1126/science.aaa1152",
        description="Seed forcing event for Siberian Traps volcanism around the Permian-Triassic boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="Central Atlantic Magmatic Province onset",
        event_category="geology",
        event_subcategory="large_igneous_province",
        ma_bp="201.56",
        uncertainty_ma="0.05",
        source_dataset="Curated large igneous province seed table",
        source_doi="10.1126/science.1234204",
        source_record_id="camp_onset",
        source_record_uri="https://doi.org/10.1126/science.1234204",
        description="Seed forcing event for CAMP onset around the Triassic-Jurassic boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="Deccan Traps main eruptive phase",
        event_category="geology",
        event_subcategory="large_igneous_province",
        ma_bp="66.30",
        uncertainty_ma="0.20",
        source_dataset="Curated large igneous province seed table",
        source_doi="10.1126/science.aau2422",
        source_record_id="deccan_traps_main_phase",
        source_record_uri="https://doi.org/10.1126/science.aau2422",
        description="Seed forcing event for Deccan Traps volcanism near the Cretaceous-Paleogene boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="Chicxulub impact",
        event_category="geology",
        event_subcategory="impact_crater",
        ma_bp="66.043",
        uncertainty_ma="0.011",
        source_dataset="Curated impact-event seed table",
        source_doi="10.1126/science.1230492",
        source_record_id="chicxulub_impact",
        source_record_uri="https://doi.org/10.1126/science.1230492",
        description="Seed impact event associated with the Cretaceous-Paleogene boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
    CuratedDeepTimeEvent(
        event_name="Permian-Triassic carbon isotope excursion",
        event_category="geochemistry",
        event_subcategory="carbon_isotope_excursion",
        ma_bp="251.90",
        uncertainty_ma="0.05",
        source_dataset="Curated geochemical excursion seed table",
        source_doi="10.1126/science.aaa1152",
        source_record_id="pt_boundary_cie",
        source_record_uri="https://doi.org/10.1126/science.aaa1152",
        description="Seed carbon-cycle perturbation event near the Permian-Triassic boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; replace with geochemical compilation for publication.",
    ),
    CuratedDeepTimeEvent(
        event_name="Triassic-Jurassic carbon isotope excursion",
        event_category="geochemistry",
        event_subcategory="carbon_isotope_excursion",
        ma_bp="201.36",
        uncertainty_ma="0.10",
        source_dataset="Curated geochemical excursion seed table",
        source_doi="10.1126/science.1234204",
        source_record_id="tj_boundary_cie",
        source_record_uri="https://doi.org/10.1126/science.1234204",
        description="Seed carbon-cycle perturbation event near the Triassic-Jurassic boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; replace with geochemical compilation for publication.",
    ),
    CuratedDeepTimeEvent(
        event_name="Cretaceous-Paleogene iridium anomaly",
        event_category="geochemistry",
        event_subcategory="iridium_anomaly",
        ma_bp="66.043",
        uncertainty_ma="0.011",
        source_dataset="Curated geochemical anomaly seed table",
        source_doi="10.1126/science.1230492",
        source_record_id="kpg_iridium_anomaly",
        source_record_uri="https://doi.org/10.1126/science.1230492",
        description="Seed geochemical anomaly associated with the K-Pg boundary.",
        attribution="Curated seed record for UBY lead-lag demonstration; verify against domain literature before scientific use.",
    ),
)


def _copy_unified_database() -> None:
    if not UNIFIED_DB.exists():
        raise FileNotFoundError(
            f"Missing {UNIFIED_DB}. Run examples/build_unified_timeline_db.py first."
        )

    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    with sqlite3.connect(UNIFIED_DB) as source, sqlite3.connect(SQLITE_OUT) as target:
        source.backup(target)


def _next_event_id(conn: sqlite3.Connection) -> int:
    value = conn.execute("SELECT COALESCE(MAX(event_id), 0) + 1 FROM uby_events").fetchone()[0]
    return int(value)


def _insert_curated_events(conn: sqlite3.Connection, events: tuple[CuratedDeepTimeEvent, ...]) -> list[int]:
    inserted_ids: list[int] = []
    next_id = _next_event_id(conn)

    for event in events:
        event_id = next_id
        next_id += 1
        inserted_ids.append(event_id)

        conn.execute(
            """
            INSERT INTO uby_events (
                event_id,
                event_name,
                event_category,
                event_subcategory,
                original_time_unit,
                original_time_value,
                original_error,
                uby_value,
                uby_value_text,
                uby_model,
                uby_precision_level,
                uby_precision_label,
                uby_mnemonic_iso,
                source_dataset,
                source_doi,
                source_record_id,
                source_record_uri,
                description,
                attribution
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event.event_name,
                event.event_category,
                event.event_subcategory,
                "Ma BP",
                event.ma_bp,
                f"{event.uncertainty_ma} Ma",
                float(event.uby_value),
                str(event.uby_value),
                DEFAULT_MODEL_VERSION,
                2,
                "Level 2",
                "",
                event.source_dataset,
                event.source_doi,
                event.source_record_id,
                event.source_record_uri,
                event.description,
                event.attribution,
            ),
        )

    return inserted_ids


def _create_analysis_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS extinction_events")
    conn.execute("DROP TABLE IF EXISTS forcing_events")
    conn.execute("DROP TABLE IF EXISTS extinction_forcing_pairs")

    conn.execute(
        """
        CREATE TABLE extinction_events AS
        SELECT *
        FROM uby_events
        WHERE event_subcategory IN ('extinction_boundary', 'extinction_intensity_peak')
        """
    )

    conn.execute(
        """
        CREATE TABLE forcing_events AS
        SELECT *
        FROM uby_events
        WHERE event_subcategory IN (
            'large_igneous_province',
            'volcanic_pulse',
            'impact_crater',
            'carbon_isotope_excursion',
            'iridium_anomaly',
            'anoxia_event',
            'sea_level_fall'
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE extinction_forcing_pairs (
            extinction_event_id INTEGER NOT NULL,
            extinction_event_name TEXT NOT NULL,
            extinction_subcategory TEXT NOT NULL,
            extinction_ma_bp TEXT,
            extinction_uby_value TEXT NOT NULL,
            extinction_uncertainty_years TEXT,
            forcing_event_id INTEGER NOT NULL,
            forcing_event_name TEXT NOT NULL,
            forcing_subcategory TEXT NOT NULL,
            forcing_ma_bp TEXT,
            forcing_uby_value TEXT NOT NULL,
            forcing_uncertainty_years TEXT,
            lag_years TEXT NOT NULL,
            abs_lag_years TEXT NOT NULL,
            window_years TEXT NOT NULL,
            overlap_flag INTEGER NOT NULL,
            lag_direction TEXT NOT NULL,
            source_pair_key TEXT NOT NULL
        )
        """
    )


def _ma_from_event(row: sqlite3.Row) -> str:
    if row["original_time_unit"] == "Ma BP":
        return str(row["original_time_value"])
    return ""


def _uncertainty_years_from_event(row: sqlite3.Row) -> Decimal:
    original_error = str(row["original_error"] or "").strip()
    if original_error.endswith(" Ma"):
        return Decimal(original_error[:-3].strip()) * MILLION

    try:
        return Decimal(original_error)
    except Exception:
        return Decimal("0")


def _build_pairs(conn: sqlite3.Connection, window_years: Decimal = DEFAULT_WINDOW_YEARS) -> list[ExtinctionForcingPair]:
    conn.row_factory = sqlite3.Row

    extinction_rows = conn.execute(
        "SELECT * FROM extinction_events ORDER BY uby_value, event_id"
    ).fetchall()
    forcing_rows = conn.execute(
        "SELECT * FROM forcing_events ORDER BY uby_value, event_id"
    ).fetchall()

    pairs: list[ExtinctionForcingPair] = []
    for extinction in extinction_rows:
        extinction_uby = Decimal(str(extinction["uby_value"]))
        extinction_uncertainty = _uncertainty_years_from_event(extinction)

        for forcing in forcing_rows:
            forcing_uby = Decimal(str(forcing["uby_value"]))
            forcing_uncertainty = _uncertainty_years_from_event(forcing)
            lag_years = extinction_uby - forcing_uby
            abs_lag_years = abs(lag_years)

            if abs_lag_years > window_years:
                continue

            overlap_flag = int(abs_lag_years <= extinction_uncertainty + forcing_uncertainty)
            if lag_years > 0:
                lag_direction = "forcing_precedes_extinction"
            elif lag_years < 0:
                lag_direction = "forcing_follows_extinction"
            else:
                lag_direction = "same_representative_time"

            pair = ExtinctionForcingPair(
                extinction_event_id=int(extinction["event_id"]),
                extinction_event_name=str(extinction["event_name"]),
                extinction_subcategory=str(extinction["event_subcategory"]),
                extinction_ma_bp=_ma_from_event(extinction),
                extinction_uby_value=str(extinction_uby),
                extinction_uncertainty_years=str(extinction_uncertainty),
                forcing_event_id=int(forcing["event_id"]),
                forcing_event_name=str(forcing["event_name"]),
                forcing_subcategory=str(forcing["event_subcategory"]),
                forcing_ma_bp=_ma_from_event(forcing),
                forcing_uby_value=str(forcing_uby),
                forcing_uncertainty_years=str(forcing_uncertainty),
                lag_years=str(lag_years),
                abs_lag_years=str(abs_lag_years),
                window_years=str(window_years),
                overlap_flag=overlap_flag,
                lag_direction=lag_direction,
                source_pair_key=f"{extinction['source_record_id']}::{forcing['source_record_id']}",
            )
            pairs.append(pair)

    conn.executemany(
        """
        INSERT INTO extinction_forcing_pairs (
            extinction_event_id,
            extinction_event_name,
            extinction_subcategory,
            extinction_ma_bp,
            extinction_uby_value,
            extinction_uncertainty_years,
            forcing_event_id,
            forcing_event_name,
            forcing_subcategory,
            forcing_ma_bp,
            forcing_uby_value,
            forcing_uncertainty_years,
            lag_years,
            abs_lag_years,
            window_years,
            overlap_flag,
            lag_direction,
            source_pair_key
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [[getattr(pair, field) for field in ExtinctionForcingPair.__dataclass_fields__] for pair in pairs],
    )

    conn.execute("CREATE INDEX IF NOT EXISTS idx_extinction_events_uby ON extinction_events (uby_value)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_forcing_events_uby ON forcing_events (uby_value)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_extinction ON extinction_forcing_pairs (extinction_event_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_forcing ON extinction_forcing_pairs (forcing_event_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_abs_lag ON extinction_forcing_pairs (abs_lag_years)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pairs_direction ON extinction_forcing_pairs (lag_direction)")

    conn.execute("DROP VIEW IF EXISTS extinction_forcing_lag_summary")
    conn.execute(
        """
        CREATE VIEW extinction_forcing_lag_summary AS
        SELECT
            forcing_subcategory,
            lag_direction,
            COUNT(*) AS pair_count,
            AVG(CAST(lag_years AS REAL)) AS mean_lag_years,
            MIN(CAST(lag_years AS REAL)) AS min_lag_years,
            MAX(CAST(lag_years AS REAL)) AS max_lag_years,
            SUM(overlap_flag) AS overlap_count
        FROM extinction_forcing_pairs
        GROUP BY forcing_subcategory, lag_direction
        ORDER BY forcing_subcategory, lag_direction
        """
    )

    return pairs


def _write_pairs_csv(pairs: list[ExtinctionForcingPair]) -> None:
    with PAIRS_CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(ExtinctionForcingPair.__dataclass_fields__))
        writer.writeheader()
        for pair in pairs:
            writer.writerow(asdict(pair))


def _write_report(conn: sqlite3.Connection, pairs: list[ExtinctionForcingPair], wall_seconds: float) -> None:
    conn.row_factory = None

    total_events = conn.execute("SELECT COUNT(*) FROM uby_events").fetchone()[0]
    extinction_count = conn.execute("SELECT COUNT(*) FROM extinction_events").fetchone()[0]
    forcing_count = conn.execute("SELECT COUNT(*) FROM forcing_events").fetchone()[0]
    pair_count = conn.execute("SELECT COUNT(*) FROM extinction_forcing_pairs").fetchone()[0]
    overlap_count = conn.execute("SELECT COUNT(*) FROM extinction_forcing_pairs WHERE overlap_flag=1").fetchone()[0]
    direction_counts = conn.execute(
        """
        SELECT lag_direction, COUNT(*)
        FROM extinction_forcing_pairs
        GROUP BY lag_direction
        ORDER BY lag_direction
        """
    ).fetchall()
    forcing_summary = conn.execute(
        """
        SELECT forcing_subcategory, lag_direction, pair_count, mean_lag_years, overlap_count
        FROM extinction_forcing_lag_summary
        ORDER BY forcing_subcategory, lag_direction
        """
    ).fetchall()
    nearest_pairs = conn.execute(
        """
        SELECT
            extinction_event_name,
            forcing_event_name,
            forcing_subcategory,
            lag_years,
            abs_lag_years,
            overlap_flag,
            lag_direction
        FROM extinction_forcing_pairs
        ORDER BY CAST(abs_lag_years AS REAL), extinction_event_name, forcing_event_name
        LIMIT 20
        """
    ).fetchall()

    report = {
        "database": "UBY Mass Extinction Lead-Lag Analysis Seed Dataset",
        "description": (
            "Executable seed dataset for testing lead-lag relationships among mass extinctions, "
            "large igneous provinces, impact events, and geochemical anomalies on a unified UBY axis."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "source_unified_database": str(UNIFIED_DB.as_posix()),
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "pairs_csv": str(PAIRS_CSV_OUT.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "window_years": str(DEFAULT_WINDOW_YEARS),
        "counts": {
            "total_uby_events_after_insertion": total_events,
            "seed_extinction_events": len(MASS_EXTINCTION_EVENTS),
            "seed_forcing_events": len(FORCING_EVENTS),
            "extinction_events_table_rows": extinction_count,
            "forcing_events_table_rows": forcing_count,
            "extinction_forcing_pairs": pair_count,
            "uncertainty_overlap_pairs": overlap_count,
        },
        "direction_counts": dict(direction_counts),
        "forcing_summary": [
            {
                "forcing_subcategory": row[0],
                "lag_direction": row[1],
                "pair_count": row[2],
                "mean_lag_years": row[3],
                "overlap_count": row[4],
            }
            for row in forcing_summary
        ],
        "nearest_pairs": [
            {
                "extinction_event_name": row[0],
                "forcing_event_name": row[1],
                "forcing_subcategory": row[2],
                "lag_years": row[3],
                "abs_lag_years": row[4],
                "overlap_flag": row[5],
                "lag_direction": row[6],
            }
            for row in nearest_pairs
        ],
        "research_status": "seed_scaffold_not_final_scientific_claim",
        "claim_boundary": [
            "The inserted extinction and forcing events are transparent seed records for method development.",
            "Do not treat this seed output as a final causal inference.",
            "Publication-grade analysis should replace seed tables with authoritative, versioned compilations and uncertainty models.",
            "The useful result at this stage is the reproducible UBY lead-lag data structure and query pipeline.",
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

    _copy_unified_database()

    with sqlite3.connect(SQLITE_OUT) as conn:
        _insert_curated_events(conn, MASS_EXTINCTION_EVENTS)
        _insert_curated_events(conn, FORCING_EVENTS)
        _create_analysis_tables(conn)
        pairs = _build_pairs(conn)
        _write_pairs_csv(pairs)

        wall_seconds = time.perf_counter() - start
        _write_report(conn, pairs, wall_seconds)

        print(f"Mass-extinction lag database: {SQLITE_OUT}")
        print(f"Pairs CSV: {PAIRS_CSV_OUT}")
        print(f"Report: {REPORT_OUT}")
        print(f"Seed extinction events inserted: {len(MASS_EXTINCTION_EVENTS)}")
        print(f"Seed forcing events inserted: {len(FORCING_EVENTS)}")
        print(f"Extinction-forcing pairs within ±{DEFAULT_WINDOW_YEARS} years: {len(pairs)}")
        print(f"Build wall seconds: {wall_seconds:.6f}")

        print("Nearest lag pairs:")
        for row in conn.execute(
            """
            SELECT extinction_event_name, forcing_event_name, forcing_subcategory, lag_years, overlap_flag, lag_direction
            FROM extinction_forcing_pairs
            ORDER BY CAST(abs_lag_years AS REAL), extinction_event_name, forcing_event_name
            LIMIT 10
            """
        ):
            print(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
