from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from examples import build_forcing_event_compilation as forcing_builder
from examples import build_forcing_extinction_leadlag as leadlag_builder


pytestmark = [pytest.mark.integration, pytest.mark.data, pytest.mark.slow]


def test_forcing_event_compilation_outputs() -> None:
    forcing_builder.main()

    assert forcing_builder.SQLITE_OUT.exists()
    assert forcing_builder.CSV_OUT.exists()
    assert forcing_builder.REPORT_OUT.exists()

    with sqlite3.connect(forcing_builder.SQLITE_OUT) as conn:
        forcing_events = conn.execute("SELECT COUNT(*) FROM forcing_events").fetchone()[0]
        categories = dict(
            conn.execute(
                """
                SELECT forcing_category, COUNT(*)
                FROM forcing_events
                GROUP BY forcing_category
                ORDER BY forcing_category
                """
            ).fetchall()
        )
        summary_rows = conn.execute("SELECT COUNT(*) FROM forcing_events_summary").fetchone()[0]

    with forcing_builder.CSV_OUT.open("r", encoding="utf-8-sig", newline="") as file:
        csv_rows = list(csv.DictReader(file))

    report = json.loads(forcing_builder.REPORT_OUT.read_text(encoding="utf-8"))

    assert forcing_events == len(forcing_builder.FORCING_EVENTS)
    assert len(csv_rows) == forcing_events
    assert report["counts"]["forcing_events"] == forcing_events
    assert summary_rows > 0

    assert categories["volcanism"] >= 1
    assert categories["impact"] >= 1
    assert categories["geochemistry"] >= 1
    assert categories["ocean_redox"] >= 1
    assert categories["sea_level"] >= 1
    assert categories["climate"] >= 1


def test_forcing_extinction_leadlag_outputs() -> None:
    forcing_builder.main()
    leadlag_builder.main()

    assert leadlag_builder.SQLITE_OUT.exists()
    assert leadlag_builder.PAIRS_CSV_OUT.exists()
    assert leadlag_builder.REPORT_OUT.exists()

    with sqlite3.connect(leadlag_builder.SQLITE_OUT) as conn:
        forcing_events = conn.execute("SELECT COUNT(*) FROM forcing_events").fetchone()[0]
        pairs = conn.execute("SELECT COUNT(*) FROM forcing_extinction_leadlag_pairs").fetchone()[0]
        overlap_pairs = conn.execute(
            "SELECT COUNT(*) FROM forcing_extinction_leadlag_pairs WHERE uncertainty_overlap_flag=1"
        ).fetchone()[0]
        nearest = conn.execute(
            """
            SELECT extinction_event_name, forcing_event_name, lag_direction, uncertainty_overlap_flag
            FROM nearest_forcing_by_extinction
            ORDER BY extinction_ma DESC, CAST(abs_lag_years AS REAL), forcing_event_name
            LIMIT 1
            """
        ).fetchone()
        summary_rows = conn.execute("SELECT COUNT(*) FROM forcing_extinction_lag_summary").fetchone()[0]

    with leadlag_builder.PAIRS_CSV_OUT.open("r", encoding="utf-8-sig", newline="") as file:
        csv_rows = list(csv.DictReader(file))

    report = json.loads(leadlag_builder.REPORT_OUT.read_text(encoding="utf-8"))

    assert forcing_events == len(forcing_builder.FORCING_EVENTS)
    assert pairs == report["counts"]["forcing_extinction_pairs"]
    assert pairs == len(csv_rows)
    assert pairs > 0
    assert overlap_pairs == report["counts"]["uncertainty_overlap_pairs"]
    assert overlap_pairs > 0
    assert summary_rows > 0

    assert nearest is not None
    assert nearest[0]
    assert nearest[1]
    assert nearest[2] in {
        "forcing_precedes_extinction",
        "forcing_follows_extinction",
        "same_representative_time",
    }
    assert nearest[3] in {0, 1}

    assert report["research_status"] == "integrated_forcing_extinction_first_pass_not_final_causal_claim"
    assert "forcing_events_csv" in report["inputs"]
