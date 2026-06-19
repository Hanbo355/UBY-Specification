from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from examples import run_extinction_sensitivity_analysis as sensitivity


pytestmark = [pytest.mark.integration, pytest.mark.data, pytest.mark.slow]


@pytest.mark.skipif(
    not sensitivity.PBDB_UBY_CSV.exists() or not sensitivity.FORCING_CSV.exists(),
    reason="Full PBDB UBY CSV and forcing CSV are required for this integration test.",
)
def test_extinction_sensitivity_analysis_outputs() -> None:
    sensitivity.main()

    assert sensitivity.SQLITE_OUT.exists()
    assert sensitivity.SUMMARY_CSV_OUT.exists()
    assert sensitivity.REPORT_OUT.exists()

    with sqlite3.connect(sensitivity.SQLITE_OUT) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM extinction_sensitivity_summary").fetchone()[0]
        event_rows = dict(
            conn.execute(
                """
                SELECT event_name, COUNT(*)
                FROM extinction_sensitivity_summary
                GROUP BY event_name
                ORDER BY event_name
                """
            ).fetchall()
        )
        stability_rows = conn.execute("SELECT COUNT(*) FROM sensitivity_event_stability").fetchone()[0]
        kpg_impact_cases = conn.execute(
            """
            SELECT SUM(kpg_impact_synchronous_flag)
            FROM extinction_sensitivity_summary
            WHERE event_name='End-Cretaceous mass extinction'
            """
        ).fetchone()[0]
        ord_forcing_cases = conn.execute(
            """
            SELECT SUM(end_ordovician_sea_level_or_climate_flag)
            FROM extinction_sensitivity_summary
            WHERE event_name='End-Ordovician mass extinction'
            """
        ).fetchone()[0]

    with sensitivity.SUMMARY_CSV_OUT.open("r", encoding="utf-8-sig", newline="") as file:
        csv_rows = list(csv.DictReader(file))

    report = json.loads(sensitivity.REPORT_OUT.read_text(encoding="utf-8"))
    parameter_cases = report["parameters"]["parameter_cases"]
    expected_rows = parameter_cases * len(sensitivity.REFERENCE_MASS_EXTINCTIONS)

    assert rows == expected_rows
    assert len(csv_rows) == rows
    assert report["counts"]["summary_rows"] == rows
    assert stability_rows == len(sensitivity.REFERENCE_MASS_EXTINCTIONS)

    for event in sensitivity.REFERENCE_MASS_EXTINCTIONS:
        assert event_rows[event.event_name] == parameter_cases

    key = report["key_stability_tests"]
    assert key["end_permian_total_cases"] == parameter_cases
    assert key["end_permian_strongest_cases"] > 0
    assert 0 <= key["end_permian_strongest_fraction"] <= 1

    assert key["kpg_total_cases"] == parameter_cases
    assert key["kpg_impact_synchronous_cases"] == kpg_impact_cases
    assert key["kpg_impact_synchronous_fraction"] >= 0.5

    assert key["end_ordovician_total_cases"] == parameter_cases
    assert key["end_ordovician_sea_level_or_climate_cases"] == ord_forcing_cases
    assert key["end_ordovician_sea_level_or_climate_fraction"] >= 0.5

    assert report["research_status"] == "sensitivity_first_pass_not_sampling_standardized"
