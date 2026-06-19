from __future__ import annotations

import csv
import json
import sqlite3

import pytest

from examples import analyze_end_ordovician_sampling_controls as controls


pytestmark = [pytest.mark.integration, pytest.mark.data, pytest.mark.slow]


@pytest.mark.skipif(
    not controls.PBDB_UBY_CSV.exists(),
    reason="Full PBDB UBY CSV is required for this integration test.",
)
def test_end_ordovician_sampling_control_outputs_and_flags() -> None:
    controls.main()

    assert controls.SQLITE_OUT.exists()
    assert controls.BIN_CSV_OUT.exists()
    assert controls.REPORT_OUT.exists()

    report = json.loads(controls.REPORT_OUT.read_text(encoding="utf-8"))
    key = report["key_findings"]

    assert report["database"] == "End-Ordovician PBDB sampling-control proxy analysis"
    assert report["counts"]["raw_rows"] > 1_000_000
    assert report["counts"]["local_occurrences_within_30myr"] > 0
    assert report["counts"]["accepted_name_ranges_global"] > 0
    assert report["counts"]["genus_ranges_global"] > 0
    assert report["counts"]["family_ranges_global"] > 0
    assert report["counts"]["sampling_bins"] == 30

    assert key["pre_boundary_last_taxa_exceed_post_boundary"] is True
    assert key["pre_boundary_accepted_last_taxa"] > key["post_boundary_accepted_last_taxa"]
    assert key["pre_boundary_genus_last_taxa"] > key["post_boundary_genus_last_taxa"]
    assert key["pre_boundary_family_last_taxa"] > key["post_boundary_family_last_taxa"]

    # This first-pass proxy explicitly detects a sharp event-bin sampling drop,
    # so the End-Ordovician signal must be treated as sampling-sensitive until
    # collection-level standardization is added.
    assert key["simple_sampling_collapse_flag"] is True
    assert key["event_occurrence_fraction_of_local_median"] < 0.25
    assert key["event_pseudo_collection_fraction_of_local_median"] < 0.25

    event_bin = key["event_bin"]
    assert int(event_bin["occurrence_count"]) > 0
    assert int(event_bin["pseudo_collection_count"]) > 0
    assert int(event_bin["unique_accepted_names"]) > 0

    with controls.BIN_CSV_OUT.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == report["counts"]["sampling_bins"]
    assert {row["relation_to_boundary"] for row in rows} == {
        "pre_boundary_older_side",
        "post_boundary_younger_side",
    }

    with sqlite3.connect(controls.SQLITE_OUT) as conn:
        sqlite_rows = conn.execute("SELECT COUNT(*) FROM sampling_control_bins").fetchone()[0]
        pre_rows = conn.execute(
            "SELECT COUNT(*) FROM sampling_control_bins WHERE relation_to_boundary='pre_boundary_older_side'"
        ).fetchone()[0]
        post_rows = conn.execute(
            "SELECT COUNT(*) FROM sampling_control_bins WHERE relation_to_boundary='post_boundary_younger_side'"
        ).fetchone()[0]

    assert sqlite_rows == len(rows)
    assert pre_rows > 0
    assert post_rows > 0
