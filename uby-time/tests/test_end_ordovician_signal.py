from __future__ import annotations

import csv
import json
import sqlite3
from decimal import Decimal

import pytest

from examples import analyze_end_ordovician_signal as endord


pytestmark = [pytest.mark.integration, pytest.mark.data, pytest.mark.slow]


@pytest.mark.skipif(
    not endord.PBDB_UBY_CSV.exists() or not endord.FORCING_CSV.exists(),
    reason="Full PBDB UBY CSV and forcing CSV are required for this integration test.",
)
def test_end_ordovician_signal_outputs_and_key_findings() -> None:
    endord.main()

    assert endord.SQLITE_OUT.exists()
    assert endord.TAXONOMIC_DRIVERS_CSV.exists()
    assert endord.SAMPLING_BINS_CSV.exists()
    assert endord.TAXON_LEVEL_STABILITY_CSV.exists()
    assert endord.FORCING_LAGS_CSV.exists()
    assert endord.BINNING_COMPRESSION_CSV.exists()
    assert endord.REPORT_OUT.exists()

    report = json.loads(endord.REPORT_OUT.read_text(encoding="utf-8"))
    key = report["key_findings"]

    assert report["research_status"] == "focused_signal_analysis_not_final_claim"
    assert key["stable_pre_boundary_across_accepted_genus_family"] is True
    assert Decimal(key["accepted_name_before_fraction"]) > Decimal(key["accepted_name_before_fraction"]) * 0
    assert Decimal(key["accepted_name_before_fraction"]) > Decimal("0.5")
    assert Decimal(key["genus_before_fraction"]) > Decimal("0.5")
    assert Decimal(key["family_before_fraction"]) > Decimal("0.5")

    nearest = key["nearest_forcing"]
    assert nearest["forcing_category"] in {"sea_level", "climate"}
    assert nearest["overlap_flag"] == 1
    assert key["sea_level_or_climate_overlap"] is True

    assert key["top_driver_classes"]
    assert key["top_driver_orders"]
    assert key["binning_compression"]

    event_bin = key["event_bin_sampling"]
    assert int(event_bin["occurrence_count"]) > 0
    assert int(event_bin["unique_accepted_names"]) > 0

    with endord.TAXON_LEVEL_STABILITY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        stability_rows = list(csv.DictReader(file))

    assert {row["taxon_level"] for row in stability_rows} == {"accepted_name", "genus", "family"}
    for row in stability_rows:
        assert Decimal(row["before_fraction"]) > Decimal(row["after_fraction"])
        assert int(row["disappearing_taxa"]) > 0

    with endord.FORCING_LAGS_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        forcing_rows = list(csv.DictReader(file))

    assert forcing_rows
    assert any(
        row["forcing_category"] in {"sea_level", "climate"} and int(row["overlap_flag"]) == 1
        for row in forcing_rows
    )

    with endord.BINNING_COMPRESSION_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        compression_rows = list(csv.DictReader(file))

    assert {row["taxon_level"] for row in compression_rows} == {"accepted_name", "genus", "family"}
    for row in compression_rows:
        assert int(row["coarse_boundary_synchronous_count"]) > int(row["precise_after_boundary"])
        assert Decimal(row["compression_ratio"]) >= Decimal("1")

    with sqlite3.connect(endord.SQLITE_OUT) as conn:
        driver_count = conn.execute("SELECT COUNT(*) FROM taxonomic_drivers").fetchone()[0]
        sampling_count = conn.execute("SELECT COUNT(*) FROM sampling_bins").fetchone()[0]
        stability_count = conn.execute("SELECT COUNT(*) FROM taxon_level_stability").fetchone()[0]
        forcing_count = conn.execute("SELECT COUNT(*) FROM forcing_lags").fetchone()[0]
        compression_count = conn.execute("SELECT COUNT(*) FROM binning_compression").fetchone()[0]

    assert driver_count == report["counts"]["taxonomic_driver_rows"]
    assert sampling_count == report["counts"]["sampling_bins"]
    assert stability_count == 3
    assert forcing_count == report["counts"]["forcing_lags_within_10myr"]
    assert compression_count == 3
