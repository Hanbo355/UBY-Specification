from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from examples import build_pbdb_extinction_dynamics as builder


pytestmark = [pytest.mark.integration, pytest.mark.data, pytest.mark.slow]


@pytest.mark.skipif(
    not builder.PBDB_UBY_CSV.exists(),
    reason="Full PBDB Animalia/Phanerozoic UBY CSV is required for this integration test.",
)
def test_pbdb_extinction_dynamics_outputs() -> None:
    builder.main()

    assert builder.SQLITE_OUT.exists()
    assert builder.TAXON_RANGES_CSV.exists()
    assert builder.INTENSITY_CSV.exists()
    assert builder.RECOVERY_CSV.exists()
    assert builder.DISAPPEARANCES_CSV.exists()
    assert builder.REPORT_OUT.exists()

    with sqlite3.connect(builder.SQLITE_OUT) as conn:
        reference_events = conn.execute("SELECT COUNT(*) FROM reference_mass_extinctions").fetchone()[0]
        taxon_ranges = conn.execute("SELECT COUNT(*) FROM pbdb_taxon_ranges").fetchone()[0]
        intensity_bins = conn.execute("SELECT COUNT(*) FROM pbdb_extinction_intensity_by_bin").fetchone()[0]
        recovery_rows = conn.execute("SELECT COUNT(*) FROM pbdb_recovery_lag").fetchone()[0]
        disappearance_rows = conn.execute("SELECT COUNT(*) FROM pbdb_taxon_disappearances").fetchone()[0]
        max_hotspot = conn.execute(
            """
            SELECT bin_mid_ma, standing_taxa, last_appearances, extinction_intensity
            FROM pbdb_extinction_hotspots
            WHERE bin_mid_ma > 1.0
            ORDER BY extinction_intensity DESC, last_appearances DESC
            LIMIT 1
            """
        ).fetchone()
        end_permian = conn.execute(
            """
            SELECT disappearing_taxa
            FROM pbdb_disappearance_summary_by_event
            WHERE event_name='End-Permian mass extinction'
            """
        ).fetchone()

    assert reference_events == len(builder.REFERENCE_MASS_EXTINCTIONS)
    assert taxon_ranges > 100_000
    assert intensity_bins >= 500
    assert recovery_rows == len(builder.REFERENCE_MASS_EXTINCTIONS)
    assert disappearance_rows > 1_000

    assert max_hotspot is not None
    assert max_hotspot[1] >= 100
    assert max_hotspot[2] > 0
    assert max_hotspot[3] > 0

    assert end_permian is not None
    assert end_permian[0] > 0

    with builder.TAXON_RANGES_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        taxon_csv_rows = sum(1 for _ in csv.DictReader(file))
    with builder.INTENSITY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        intensity_csv_rows = sum(1 for _ in csv.DictReader(file))
    with builder.RECOVERY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        recovery_csv_rows = sum(1 for _ in csv.DictReader(file))
    with builder.DISAPPEARANCES_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        disappearance_csv_rows = sum(1 for _ in csv.DictReader(file))

    assert taxon_csv_rows == taxon_ranges
    assert intensity_csv_rows == intensity_bins
    assert recovery_csv_rows == recovery_rows
    assert disappearance_csv_rows == disappearance_rows

    report = json.loads(builder.REPORT_OUT.read_text(encoding="utf-8"))
    assert report["research_status"] == "pbdb_derived_macroecology_first_pass_not_final_causal_claim"
    assert report["counts"]["raw_rows"] >= 1_000_000
    assert report["counts"]["usable_rows"] == report["counts"]["raw_rows"]
    assert report["counts"]["taxon_ranges"] == taxon_ranges
    assert report["counts"]["binned_intensity_rows"] == intensity_bins
    assert report["counts"]["recovery_lag_rows"] == recovery_rows
    assert report["counts"]["taxon_disappearance_rows"] == disappearance_rows
