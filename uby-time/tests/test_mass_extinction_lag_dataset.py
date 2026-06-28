from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from examples import build_mass_extinction_lag_dataset as builder


pytestmark = [pytest.mark.integration, pytest.mark.data, pytest.mark.slow]


def test_mass_extinction_lag_dataset_outputs() -> None:
    builder.main()

    assert builder.SQLITE_OUT.exists()
    assert builder.PAIRS_CSV_OUT.exists()
    assert builder.REPORT_OUT.exists()

    with sqlite3.connect(builder.SQLITE_OUT) as conn:
        total_events = conn.execute("SELECT COUNT(*) FROM uby_events").fetchone()[0]
        extinction_events = conn.execute("SELECT COUNT(*) FROM extinction_events").fetchone()[0]
        forcing_events = conn.execute("SELECT COUNT(*) FROM forcing_events").fetchone()[0]
        pairs = conn.execute("SELECT COUNT(*) FROM extinction_forcing_pairs").fetchone()[0]
        overlap_pairs = conn.execute(
            "SELECT COUNT(*) FROM extinction_forcing_pairs WHERE overlap_flag=1"
        ).fetchone()[0]
        nearest = conn.execute(
            """
            SELECT extinction_event_name, forcing_event_name, lag_years, overlap_flag
            FROM extinction_forcing_pairs
            ORDER BY CAST(abs_lag_years AS REAL), extinction_event_name, forcing_event_name
            LIMIT 1
            """
        ).fetchone()

        # Verify that all seed extinction events are present in the extinction_events table.
        seed_extinction_names = {e.event_name for e in builder.MASS_EXTINCTION_EVENTS}
        db_extinction_names = {
            row[0] for row in conn.execute("SELECT DISTINCT event_name FROM extinction_events")
        }
        assert seed_extinction_names.issubset(db_extinction_names)

        # Verify that all seed forcing events are present in the forcing_events table.
        seed_forcing_names = {e.event_name for e in builder.FORCING_EVENTS}
        db_forcing_names = {
            row[0] for row in conn.execute("SELECT DISTINCT event_name FROM forcing_events")
        }
        assert seed_forcing_names.issubset(db_forcing_names)

    # Structural invariants derived from the database, not hardcoded constants.
    assert total_events >= len(builder.MASS_EXTINCTION_EVENTS) + len(builder.FORCING_EVENTS)
    assert extinction_events >= len(builder.MASS_EXTINCTION_EVENTS)
    assert forcing_events >= len(builder.FORCING_EVENTS)
    assert pairs > 0
    assert overlap_pairs <= pairs
    assert nearest is not None
    assert nearest[2] == "0.0"
    assert nearest[3] == 1

    with builder.PAIRS_CSV_OUT.open("r", encoding="utf-8-sig", newline="") as file:
        csv_rows = list(csv.DictReader(file))
    assert len(csv_rows) == pairs

    report = json.loads(builder.REPORT_OUT.read_text(encoding="utf-8"))
    assert report["research_status"] == "seed_scaffold_not_final_scientific_claim"
    assert report["counts"]["extinction_forcing_pairs"] == pairs
    assert report["counts"]["uncertainty_overlap_pairs"] == overlap_pairs
