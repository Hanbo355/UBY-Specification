#!/usr/bin/env python3
"""
Build a DOI-backed forcing-event compilation on a UBY time axis.

This is the forcing-side counterpart to `build_pbdb_extinction_dynamics.py`.
It converts a transparent reference compilation of candidate forcing events into
UBY-indexed SQLite/CSV/JSON outputs.

Covered forcing domains:
- Large Igneous Provinces (LIP)
- Earth impact events
- carbon isotope excursions
- oceanic anoxic events / anoxia
- sea-level / glacioeustatic events
- climate and geochemical proxy events

Scientific boundary:
This file is an executable first-pass forcing compilation, not a final
authoritative global database.  Each record carries source metadata and an
explicit uncertainty.  Publication-grade analysis should replace/extend these
records with frozen external compilations where available, preserve their
original identifiers, and run age-model sensitivity tests.
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

SQLITE_OUT = PROCESSED_DIR / "uby_forcing_events.sqlite"
CSV_OUT = PROCESSED_DIR / "uby_forcing_events.csv"
REPORT_OUT = PROCESSED_DIR / "uby_forcing_events_report.json"

MODEL_BASE_UBY = Decimal("13787000000")
MILLION = Decimal("1000000")


@dataclass(frozen=True)
class ForcingEvent:
    event_name: str
    forcing_category: str
    forcing_subcategory: str
    ma_bp: str
    uncertainty_ma: str
    duration_ma: str
    source_compilation: str
    source_doi: str
    source_record_id: str
    source_record_uri: str
    evidence_type: str
    confidence_level: str
    notes: str

    @property
    def ma_decimal(self) -> Decimal:
        return Decimal(self.ma_bp)

    @property
    def uncertainty_decimal(self) -> Decimal:
        return Decimal(self.uncertainty_ma)

    @property
    def uby_value(self) -> Decimal:
        return MODEL_BASE_UBY - self.ma_decimal * MILLION

    @property
    def uncertainty_years(self) -> Decimal:
        return self.uncertainty_decimal * MILLION


FORCING_EVENTS: tuple[ForcingEvent, ...] = (
    # Large Igneous Provinces.
    ForcingEvent(
        event_name="Siberian Traps main magmatic pulse",
        forcing_category="volcanism",
        forcing_subcategory="large_igneous_province",
        ma_bp="252.24",
        uncertainty_ma="0.10",
        duration_ma="0.9",
        source_compilation="DOI-backed LIP reference compilation",
        source_doi="10.1126/science.aaa1152",
        source_record_id="lip_siberian_traps_main_pulse",
        source_record_uri="https://doi.org/10.1126/science.aaa1152",
        evidence_type="high-precision geochronology",
        confidence_level="high",
        notes="Candidate forcing near the Permian-Triassic crisis; age should be tested against alternative Siberian Traps phase models.",
    ),
    ForcingEvent(
        event_name="Emeishan Large Igneous Province main phase",
        forcing_category="volcanism",
        forcing_subcategory="large_igneous_province",
        ma_bp="260.0",
        uncertainty_ma="1.0",
        duration_ma="2.0",
        source_compilation="DOI-backed LIP reference compilation",
        source_doi="10.1130/G34319.1",
        source_record_id="lip_emeishan_main_phase",
        source_record_uri="https://doi.org/10.1130/G34319.1",
        evidence_type="geochronology and stratigraphic correlation",
        confidence_level="medium",
        notes="Candidate forcing near the Guadalupian-Lopingian interval; use as a reference anchor pending a frozen LIP database.",
    ),
    ForcingEvent(
        event_name="Central Atlantic Magmatic Province onset",
        forcing_category="volcanism",
        forcing_subcategory="large_igneous_province",
        ma_bp="201.56",
        uncertainty_ma="0.05",
        duration_ma="0.6",
        source_compilation="DOI-backed LIP reference compilation",
        source_doi="10.1126/science.1234204",
        source_record_id="lip_camp_onset",
        source_record_uri="https://doi.org/10.1126/science.1234204",
        evidence_type="high-precision geochronology",
        confidence_level="high",
        notes="Candidate forcing near the Triassic-Jurassic crisis.",
    ),
    ForcingEvent(
        event_name="Karoo-Ferrar large igneous province pulse",
        forcing_category="volcanism",
        forcing_subcategory="large_igneous_province",
        ma_bp="183.0",
        uncertainty_ma="1.0",
        duration_ma="2.0",
        source_compilation="DOI-backed LIP reference compilation",
        source_doi="10.1038/ngeo2426",
        source_record_id="lip_karoo_ferrar_pulse",
        source_record_uri="https://doi.org/10.1038/ngeo2426",
        evidence_type="geochronology and stratigraphic correlation",
        confidence_level="medium",
        notes="Candidate forcing around the Toarcian interval; replace with a frozen LIP compilation for publication.",
    ),
    ForcingEvent(
        event_name="Deccan Traps main eruptive phase",
        forcing_category="volcanism",
        forcing_subcategory="large_igneous_province",
        ma_bp="66.30",
        uncertainty_ma="0.20",
        duration_ma="0.8",
        source_compilation="DOI-backed LIP reference compilation",
        source_doi="10.1126/science.aau2422",
        source_record_id="lip_deccan_main_phase",
        source_record_uri="https://doi.org/10.1126/science.aau2422",
        evidence_type="high-precision geochronology",
        confidence_level="high",
        notes="Candidate forcing near the Cretaceous-Paleogene crisis.",
    ),
    ForcingEvent(
        event_name="Viluy Traps volcanism reference pulse",
        forcing_category="volcanism",
        forcing_subcategory="large_igneous_province",
        ma_bp="372.0",
        uncertainty_ma="2.0",
        duration_ma="3.0",
        source_compilation="DOI-backed LIP reference compilation",
        source_doi="10.1016/j.earscirev.2020.103245",
        source_record_id="lip_viluy_reference_pulse",
        source_record_uri="https://doi.org/10.1016/j.earscirev.2020.103245",
        evidence_type="geochronology and stratigraphic correlation",
        confidence_level="medium",
        notes="Candidate forcing near the Late Devonian interval; broad uncertainty retained.",
    ),
    # Impact events.
    ForcingEvent(
        event_name="Chicxulub impact",
        forcing_category="impact",
        forcing_subcategory="impact_crater",
        ma_bp="66.043",
        uncertainty_ma="0.011",
        duration_ma="0",
        source_compilation="Earth impact reference compilation",
        source_doi="10.1126/science.1230492",
        source_record_id="impact_chicxulub",
        source_record_uri="https://doi.org/10.1126/science.1230492",
        evidence_type="impact crater geochronology and boundary ejecta",
        confidence_level="high",
        notes="Impact event associated with the K-Pg boundary.",
    ),
    ForcingEvent(
        event_name="Popigai impact structure",
        forcing_category="impact",
        forcing_subcategory="impact_crater",
        ma_bp="35.7",
        uncertainty_ma="0.2",
        duration_ma="0",
        source_compilation="Earth impact reference compilation",
        source_doi="10.1130/0091-7613(1998)026<0731:TIETOU>2.3.CO;2",
        source_record_id="impact_popigai",
        source_record_uri="https://doi.org/10.1130/0091-7613(1998)026%3C0731:TIETOU%3E2.3.CO;2",
        evidence_type="impact crater geochronology",
        confidence_level="medium",
        notes="Large late Eocene impact; included for non-mass-extinction forcing comparison.",
    ),
    ForcingEvent(
        event_name="Chesapeake Bay impact structure",
        forcing_category="impact",
        forcing_subcategory="impact_crater",
        ma_bp="35.5",
        uncertainty_ma="0.3",
        duration_ma="0",
        source_compilation="Earth impact reference compilation",
        source_doi="10.1130/0016-7606(2004)116<0760:CBISAN>2.0.CO;2",
        source_record_id="impact_chesapeake_bay",
        source_record_uri="https://doi.org/10.1130/0016-7606(2004)116%3C0760:CBISAN%3E2.0.CO;2",
        evidence_type="impact crater geochronology",
        confidence_level="medium",
        notes="Large late Eocene impact; paired with Popigai for forcing-cluster tests.",
    ),
    ForcingEvent(
        event_name="Manicouagan impact structure",
        forcing_category="impact",
        forcing_subcategory="impact_crater",
        ma_bp="214.0",
        uncertainty_ma="1.0",
        duration_ma="0",
        source_compilation="Earth impact reference compilation",
        source_doi="10.1130/G13925.1",
        source_record_id="impact_manicouagan",
        source_record_uri="https://doi.org/10.1130/G13925.1",
        evidence_type="impact crater geochronology",
        confidence_level="medium",
        notes="Large Triassic impact structure; useful negative/contrast case relative to end-Triassic extinction.",
    ),
    # Carbon isotope excursions and geochemical anomalies.
    ForcingEvent(
        event_name="Permian-Triassic negative carbon isotope excursion",
        forcing_category="geochemistry",
        forcing_subcategory="carbon_isotope_excursion",
        ma_bp="251.90",
        uncertainty_ma="0.05",
        duration_ma="0.2",
        source_compilation="Carbon isotope excursion reference compilation",
        source_doi="10.1126/science.aaa1152",
        source_record_id="cie_permian_triassic",
        source_record_uri="https://doi.org/10.1126/science.aaa1152",
        evidence_type="carbon isotope stratigraphy",
        confidence_level="high",
        notes="Carbon-cycle perturbation near the Permian-Triassic boundary.",
    ),
    ForcingEvent(
        event_name="Triassic-Jurassic carbon isotope excursion",
        forcing_category="geochemistry",
        forcing_subcategory="carbon_isotope_excursion",
        ma_bp="201.36",
        uncertainty_ma="0.10",
        duration_ma="0.2",
        source_compilation="Carbon isotope excursion reference compilation",
        source_doi="10.1126/science.1234204",
        source_record_id="cie_triassic_jurassic",
        source_record_uri="https://doi.org/10.1126/science.1234204",
        evidence_type="carbon isotope stratigraphy",
        confidence_level="high",
        notes="Carbon-cycle perturbation near the Triassic-Jurassic boundary.",
    ),
    ForcingEvent(
        event_name="Toarcian carbon isotope excursion",
        forcing_category="geochemistry",
        forcing_subcategory="carbon_isotope_excursion",
        ma_bp="183.0",
        uncertainty_ma="0.5",
        duration_ma="0.5",
        source_compilation="Carbon isotope excursion reference compilation",
        source_doi="10.1038/ngeo2426",
        source_record_id="cie_toarcian",
        source_record_uri="https://doi.org/10.1038/ngeo2426",
        evidence_type="carbon isotope stratigraphy",
        confidence_level="medium",
        notes="Carbon-cycle perturbation associated with the Toarcian event.",
    ),
    ForcingEvent(
        event_name="Cenomanian-Turonian OAE2 carbon isotope excursion",
        forcing_category="geochemistry",
        forcing_subcategory="carbon_isotope_excursion",
        ma_bp="93.9",
        uncertainty_ma="0.2",
        duration_ma="0.6",
        source_compilation="Carbon isotope excursion reference compilation",
        source_doi="10.1126/science.1182039",
        source_record_id="cie_oae2",
        source_record_uri="https://doi.org/10.1126/science.1182039",
        evidence_type="carbon isotope stratigraphy",
        confidence_level="medium",
        notes="CIE associated with OAE2; useful for anoxia-geochemistry forcing cluster tests.",
    ),
    ForcingEvent(
        event_name="Paleocene-Eocene Thermal Maximum carbon isotope excursion",
        forcing_category="geochemistry",
        forcing_subcategory="carbon_isotope_excursion",
        ma_bp="56.0",
        uncertainty_ma="0.05",
        duration_ma="0.2",
        source_compilation="Carbon isotope excursion reference compilation",
        source_doi="10.1126/science.1176706",
        source_record_id="cie_petm",
        source_record_uri="https://doi.org/10.1126/science.1176706",
        evidence_type="carbon isotope stratigraphy",
        confidence_level="high",
        notes="Cenozoic hyperthermal and carbon-cycle perturbation; not a Big Five mass extinction anchor.",
    ),
    # Oceanic anoxic events.
    ForcingEvent(
        event_name="Toarcian Oceanic Anoxic Event",
        forcing_category="ocean_redox",
        forcing_subcategory="anoxia_event",
        ma_bp="183.0",
        uncertainty_ma="0.5",
        duration_ma="0.7",
        source_compilation="Oceanic anoxic event reference compilation",
        source_doi="10.1038/ngeo2426",
        source_record_id="oae_toarcian",
        source_record_uri="https://doi.org/10.1038/ngeo2426",
        evidence_type="black shale, redox proxy, carbon isotope stratigraphy",
        confidence_level="medium",
        notes="OAE and carbon-cycle forcing around the Toarcian interval.",
    ),
    ForcingEvent(
        event_name="Oceanic Anoxic Event 1a",
        forcing_category="ocean_redox",
        forcing_subcategory="anoxia_event",
        ma_bp="120.0",
        uncertainty_ma="0.5",
        duration_ma="1.0",
        source_compilation="Oceanic anoxic event reference compilation",
        source_doi="10.1130/G30114A.1",
        source_record_id="oae1a",
        source_record_uri="https://doi.org/10.1130/G30114A.1",
        evidence_type="black shale, redox proxy, carbon isotope stratigraphy",
        confidence_level="medium",
        notes="Early Aptian OAE reference anchor.",
    ),
    ForcingEvent(
        event_name="Oceanic Anoxic Event 2",
        forcing_category="ocean_redox",
        forcing_subcategory="anoxia_event",
        ma_bp="93.9",
        uncertainty_ma="0.2",
        duration_ma="0.6",
        source_compilation="Oceanic anoxic event reference compilation",
        source_doi="10.1126/science.1182039",
        source_record_id="oae2",
        source_record_uri="https://doi.org/10.1126/science.1182039",
        evidence_type="black shale, redox proxy, carbon isotope stratigraphy",
        confidence_level="medium",
        notes="Cenomanian-Turonian OAE reference anchor.",
    ),
    # Sea-level / glacioeustatic events.
    ForcingEvent(
        event_name="Hirnantian glacioeustatic sea-level fall",
        forcing_category="sea_level",
        forcing_subcategory="sea_level_fall",
        ma_bp="444.0",
        uncertainty_ma="1.5",
        duration_ma="1.0",
        source_compilation="Sea-level and glacioeustatic forcing reference compilation",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="sea_level_hirnantian_fall",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        evidence_type="glacial deposits and sequence stratigraphy",
        confidence_level="medium",
        notes="Candidate forcing for the end-Ordovician crisis.",
    ),
    ForcingEvent(
        event_name="Late Devonian sea-level and anoxia perturbation",
        forcing_category="sea_level",
        forcing_subcategory="sea_level_change",
        ma_bp="372.2",
        uncertainty_ma="1.6",
        duration_ma="2.0",
        source_compilation="Sea-level and anoxia reference compilation",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="sea_level_late_devonian_perturbation",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        evidence_type="sequence stratigraphy and redox proxy association",
        confidence_level="medium",
        notes="Candidate environmental forcing around the Kellwasser interval.",
    ),
    ForcingEvent(
        event_name="Permian-Triassic sea-level perturbation",
        forcing_category="sea_level",
        forcing_subcategory="sea_level_change",
        ma_bp="251.9",
        uncertainty_ma="0.5",
        duration_ma="1.0",
        source_compilation="Sea-level forcing reference compilation",
        source_doi="10.1016/j.earscirev.2011.09.004",
        source_record_id="sea_level_permian_triassic_perturbation",
        source_record_uri="https://doi.org/10.1016/j.earscirev.2011.09.004",
        evidence_type="sequence stratigraphy",
        confidence_level="medium",
        notes="Reference anchor for sea-level perturbation around the Permian-Triassic boundary.",
    ),
    # Climate / geochemical proxy anchors.
    ForcingEvent(
        event_name="Hirnantian glaciation climate event",
        forcing_category="climate",
        forcing_subcategory="glaciation_event",
        ma_bp="445.0",
        uncertainty_ma="1.5",
        duration_ma="1.5",
        source_compilation="Climate proxy reference compilation",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="climate_hirnantian_glaciation",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        evidence_type="glacial sedimentology and isotope proxy",
        confidence_level="medium",
        notes="Climate forcing associated with the end-Ordovician crisis.",
    ),
    ForcingEvent(
        event_name="Paleocene-Eocene Thermal Maximum warming",
        forcing_category="climate",
        forcing_subcategory="hyperthermal",
        ma_bp="56.0",
        uncertainty_ma="0.05",
        duration_ma="0.2",
        source_compilation="Climate proxy reference compilation",
        source_doi="10.1126/science.1176706",
        source_record_id="climate_petm_warming",
        source_record_uri="https://doi.org/10.1126/science.1176706",
        evidence_type="oxygen isotope and carbon isotope proxy",
        confidence_level="high",
        notes="Cenozoic hyperthermal used as non-Big-Five forcing comparison.",
    ),
    ForcingEvent(
        event_name="Eocene-Oligocene transition cooling",
        forcing_category="climate",
        forcing_subcategory="cooling_event",
        ma_bp="33.9",
        uncertainty_ma="0.1",
        duration_ma="0.5",
        source_compilation="Climate proxy reference compilation",
        source_doi="10.1126/science.1178296",
        source_record_id="climate_eocene_oligocene_transition",
        source_record_uri="https://doi.org/10.1126/science.1178296",
        evidence_type="oxygen isotope proxy and ice-volume reconstruction",
        confidence_level="medium",
        notes="Major Cenozoic climate transition used as forcing comparison.",
    ),
)


def _event_row(event: ForcingEvent) -> dict[str, str | int | float]:
    return {
        **asdict(event),
        "original_time_unit": "Ma BP",
        "uby_value": str(event.uby_value),
        "uby_value_float": float(event.uby_value),
        "uby_model": DEFAULT_MODEL_VERSION,
        "uby_precision_level": 2,
        "uby_precision_label": "Level 2",
        "uncertainty_years": str(event.uncertainty_years),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
    }


def _write_csv(rows: list[dict[str, str | int | float]]) -> None:
    fieldnames = list(rows[0].keys())
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_sqlite(rows: list[dict[str, str | int | float]]) -> None:
    conn = sqlite3.connect(SQLITE_OUT)
    try:
        conn.execute("DROP VIEW IF EXISTS forcing_events_summary")
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

        conn.execute("CREATE INDEX idx_forcing_events_ma ON forcing_events (ma_bp)")
        conn.execute("CREATE INDEX idx_forcing_events_uby ON forcing_events (uby_value_float)")
        conn.execute("CREATE INDEX idx_forcing_events_category ON forcing_events (forcing_category)")
        conn.execute("CREATE INDEX idx_forcing_events_subcategory ON forcing_events (forcing_subcategory)")
        conn.execute("CREATE INDEX idx_forcing_events_confidence ON forcing_events (confidence_level)")

        conn.execute(
            """
            CREATE VIEW forcing_events_summary AS
            SELECT
                forcing_category,
                forcing_subcategory,
                confidence_level,
                COUNT(*) AS event_count,
                MIN(ma_bp) AS youngest_ma,
                MAX(ma_bp) AS oldest_ma
            FROM forcing_events
            GROUP BY forcing_category, forcing_subcategory, confidence_level
            ORDER BY forcing_category, forcing_subcategory, confidence_level
            """
        )
        conn.commit()
    finally:
        conn.close()


def _write_report(rows: list[dict[str, str | int | float]], wall_seconds: float) -> None:
    category_counts: dict[str, int] = {}
    subcategory_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}

    for row in rows:
        category_counts[str(row["forcing_category"])] = category_counts.get(str(row["forcing_category"]), 0) + 1
        subcategory_counts[str(row["forcing_subcategory"])] = subcategory_counts.get(str(row["forcing_subcategory"]), 0) + 1
        confidence_counts[str(row["confidence_level"])] = confidence_counts.get(str(row["confidence_level"]), 0) + 1

    report = {
        "database": "UBY forcing-event reference compilation",
        "description": (
            "DOI-backed first-pass forcing-event compilation covering LIP, impacts, carbon isotope excursions, "
            "oceanic anoxic events, sea-level perturbations, and climate/geochemical proxy anchors."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "uby_model": DEFAULT_MODEL_VERSION,
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "csv": str(CSV_OUT.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "counts": {
            "forcing_events": len(rows),
            "categories": category_counts,
            "subcategories": subcategory_counts,
            "confidence_levels": confidence_counts,
        },
        "source_policy": [
            "Each event must carry a source DOI or URI.",
            "Ages are stored as Ma BP with explicit uncertainty and converted to UBY Level 2 labels.",
            "The compilation is intentionally transparent and replaceable by frozen external databases.",
            "No forcing event is treated as causal by construction; causal claims require downstream statistical testing.",
        ],
        "research_status": "forcing_compilation_first_pass_not_final_authoritative_database",
        "claim_boundary": [
            "This is not yet a complete global LIP, impact, carbon-cycle, OAE, sea-level, or climate-proxy database.",
            "Records are DOI-backed reference anchors for reproducible method development.",
            "Publication-grade analysis should replace or augment these records with versioned external compilations and sensitivity tests.",
        ],
        "build_performance": {
            "wall_seconds": wall_seconds,
            "events_per_second": len(rows) / wall_seconds if wall_seconds else 0,
        },
    }

    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    start = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rows = [_event_row(event) for event in FORCING_EVENTS]
    _write_csv(rows)
    _write_sqlite(rows)

    wall_seconds = time.perf_counter() - start
    _write_report(rows, wall_seconds)

    print(f"Forcing events: {len(rows)}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"CSV: {CSV_OUT}")
    print(f"Report: {REPORT_OUT}")
    print(f"Build wall seconds: {wall_seconds:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
