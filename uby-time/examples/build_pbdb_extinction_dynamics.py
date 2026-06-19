#!/usr/bin/env python3
"""
Build PBDB-derived extinction dynamics on a UBY time axis.

This script replaces the earlier "seed-only" extinction layer with an automated
PBDB-derived macroevolutionary layer.  It does not infer causality.  Instead, it
derives publication-auditable intermediate products from the full annotated PBDB
Animalia/Phanerozoic occurrence table:

- taxon stratigraphic ranges from PBDB occurrences
- binned extinction/origination intensity
- recovery-lag estimates around reference mass-extinction boundaries
- taxon-specific disappearance records near mass-extinction boundaries

Input:
- data/processed/pbdb_animalia_phanerozoic_uby.csv

Outputs:
- data/processed/pbdb_extinction_dynamics.sqlite
- data/processed/pbdb_taxon_ranges.csv
- data/processed/pbdb_extinction_intensity_by_bin.csv
- data/processed/pbdb_recovery_lag.csv
- data/processed/pbdb_taxon_disappearances.csv
- data/processed/pbdb_extinction_dynamics_report.json

Important scientific boundary:
This is a first automated PBDB-derived analysis layer.  It is far stronger than
the transparent seed scaffold because extinction intensity and disappearances
come from the full PBDB occurrence table.  However, it still uses a simple
range-through midpoint method and should not be treated as final causal
inference without sampling correction, taxonomic standardization review,
Monte Carlo interval propagation, and independent forcing-event compilations.
"""

from __future__ import annotations

import csv
import json
import math
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import DEFAULT_MODEL_VERSION, GENERATED_BY, UBY_SPEC_VERSION

PROCESSED_DIR = ROOT / "data" / "processed"
PBDB_UBY_CSV = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.csv"

SQLITE_OUT = PROCESSED_DIR / "pbdb_extinction_dynamics.sqlite"
TAXON_RANGES_CSV = PROCESSED_DIR / "pbdb_taxon_ranges.csv"
INTENSITY_CSV = PROCESSED_DIR / "pbdb_extinction_intensity_by_bin.csv"
RECOVERY_CSV = PROCESSED_DIR / "pbdb_recovery_lag.csv"
DISAPPEARANCES_CSV = PROCESSED_DIR / "pbdb_taxon_disappearances.csv"
REPORT_OUT = PROCESSED_DIR / "pbdb_extinction_dynamics_report.json"

MODEL_BASE_UBY = Decimal("13787000000")
MILLION = Decimal("1000000")
BIN_SIZE_MA = Decimal("1.0")
MAX_PHANEROZOIC_MA = Decimal("541.0")
RECOVERY_BASELINE_WINDOW_MA = Decimal("10.0")
RECOVERY_THRESHOLD_FRACTION = Decimal("0.8")
DISAPPEARANCE_WINDOW_MIN_MA = Decimal("2.5")


@dataclass(frozen=True)
class ReferenceMassExtinction:
    event_name: str
    event_subcategory: str
    ma_bp: str
    uncertainty_ma: str
    source_dataset: str
    source_doi: str
    source_record_id: str
    source_record_uri: str
    attribution: str

    @property
    def ma_decimal(self) -> Decimal:
        return Decimal(self.ma_bp)

    @property
    def uncertainty_decimal(self) -> Decimal:
        return Decimal(self.uncertainty_ma)

    @property
    def uby_value(self) -> Decimal:
        return MODEL_BASE_UBY - self.ma_decimal * MILLION


REFERENCE_MASS_EXTINCTIONS: tuple[ReferenceMassExtinction, ...] = (
    ReferenceMassExtinction(
        event_name="End-Ordovician mass extinction",
        event_subcategory="extinction_boundary",
        ma_bp="443.8",
        uncertainty_ma="1.5",
        source_dataset="Reference mass-extinction boundary compilation",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="end_ordovician_extinction",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        attribution="Reference boundary used for PBDB-derived disappearance/recovery analysis; verify age model for final claims.",
    ),
    ReferenceMassExtinction(
        event_name="Late Devonian Kellwasser extinction pulse",
        event_subcategory="extinction_boundary",
        ma_bp="372.2",
        uncertainty_ma="1.6",
        source_dataset="Reference mass-extinction boundary compilation",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="late_devonian_kellwasser",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        attribution="Reference boundary used for PBDB-derived disappearance/recovery analysis; verify age model for final claims.",
    ),
    ReferenceMassExtinction(
        event_name="Late Devonian Hangenberg extinction pulse",
        event_subcategory="extinction_boundary",
        ma_bp="358.9",
        uncertainty_ma="0.4",
        source_dataset="Reference mass-extinction boundary compilation",
        source_doi="10.1144/GSL.SP.2005.248",
        source_record_id="late_devonian_hangenberg",
        source_record_uri="https://doi.org/10.1144/GSL.SP.2005.248",
        attribution="Reference boundary used for PBDB-derived disappearance/recovery analysis; verify age model for final claims.",
    ),
    ReferenceMassExtinction(
        event_name="End-Permian mass extinction",
        event_subcategory="extinction_boundary",
        ma_bp="251.902",
        uncertainty_ma="0.024",
        source_dataset="Reference mass-extinction boundary compilation",
        source_doi="10.1126/science.aaa1152",
        source_record_id="end_permian_extinction",
        source_record_uri="https://doi.org/10.1126/science.aaa1152",
        attribution="Reference boundary used for PBDB-derived disappearance/recovery analysis; verify age model for final claims.",
    ),
    ReferenceMassExtinction(
        event_name="End-Triassic mass extinction",
        event_subcategory="extinction_boundary",
        ma_bp="201.36",
        uncertainty_ma="0.17",
        source_dataset="Reference mass-extinction boundary compilation",
        source_doi="10.1126/science.1234204",
        source_record_id="end_triassic_extinction",
        source_record_uri="https://doi.org/10.1126/science.1234204",
        attribution="Reference boundary used for PBDB-derived disappearance/recovery analysis; verify age model for final claims.",
    ),
    ReferenceMassExtinction(
        event_name="End-Cretaceous mass extinction",
        event_subcategory="extinction_boundary",
        ma_bp="66.043",
        uncertainty_ma="0.011",
        source_dataset="Reference mass-extinction boundary compilation",
        source_doi="10.1126/science.1230492",
        source_record_id="end_cretaceous_extinction",
        source_record_uri="https://doi.org/10.1126/science.1230492",
        attribution="Reference boundary used for PBDB-derived disappearance/recovery analysis; verify age model for final claims.",
    ),
)


@dataclass
class TaxonAccumulator:
    taxon_name: str
    taxon_rank: str
    phylum: str
    class_name: str
    taxonomic_order: str
    family: str
    genus: str
    first_ma: Decimal
    last_ma: Decimal
    max_ma_observed: Decimal
    min_ma_observed: Decimal
    max_uncertainty_years: Decimal
    occurrence_count: int
    source_record_examples: list[str]

    def update(self, midpoint_ma: Decimal, max_ma: Decimal, min_ma: Decimal, uncertainty_years: Decimal, source_record_id: str) -> None:
        if midpoint_ma > self.first_ma:
            self.first_ma = midpoint_ma
        if midpoint_ma < self.last_ma:
            self.last_ma = midpoint_ma
        if max_ma > self.max_ma_observed:
            self.max_ma_observed = max_ma
        if min_ma < self.min_ma_observed:
            self.min_ma_observed = min_ma
        if uncertainty_years > self.max_uncertainty_years:
            self.max_uncertainty_years = uncertainty_years
        self.occurrence_count += 1
        if len(self.source_record_examples) < 5:
            self.source_record_examples.append(source_record_id)


@dataclass(frozen=True)
class TaxonRange:
    taxon_name: str
    taxon_rank: str
    phylum: str
    class_name: str
    taxonomic_order: str
    family: str
    genus: str
    first_ma: str
    last_ma: str
    duration_myr: str
    max_ma_observed: str
    min_ma_observed: str
    max_uncertainty_years: str
    first_uby_value: str
    last_uby_value: str
    occurrence_count: int
    source_record_examples: str


@dataclass(frozen=True)
class BinnedIntensity:
    bin_id: int
    bin_young_ma: str
    bin_old_ma: str
    bin_mid_ma: str
    bin_mid_uby_value: str
    standing_taxa: int
    first_appearances: int
    last_appearances: int
    extinction_intensity: str
    origination_intensity: str


@dataclass(frozen=True)
class RecoveryLag:
    event_name: str
    event_ma: str
    event_uby_value: str
    event_uncertainty_ma: str
    baseline_window_ma: str
    baseline_mean_standing_taxa: str
    recovery_threshold_fraction: str
    recovery_threshold_taxa: str
    event_bin_standing_taxa: int
    minimum_post_event_standing_taxa: int
    recovery_bin_mid_ma: str
    recovery_lag_years: str
    recovered_flag: int
    method: str
    source_doi: str


@dataclass(frozen=True)
class TaxonDisappearance:
    event_name: str
    event_ma: str
    event_uncertainty_ma: str
    disappearance_window_ma: str
    taxon_name: str
    taxon_rank: str
    phylum: str
    class_name: str
    taxonomic_order: str
    family: str
    genus: str
    last_ma: str
    first_ma: str
    duration_myr: str
    lag_years: str
    lag_direction: str
    occurrence_count: int
    max_uncertainty_years: str
    source_record_examples: str


def _decimal_or_none(value: str | None) -> Decimal | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _taxon_key(row: dict[str, str]) -> tuple[str, str]:
    accepted_name = str(row.get("accepted_name") or "").strip()
    accepted_rank = str(row.get("accepted_rank") or "").strip()
    genus = str(row.get("genus") or "").strip()
    family = str(row.get("family") or "").strip()

    if accepted_name:
        return accepted_name, accepted_rank or "accepted_name"
    if genus:
        return genus, "genus"
    if family:
        return family, "family"
    return "", ""


def _uby_from_ma(ma: Decimal) -> Decimal:
    return MODEL_BASE_UBY - ma * MILLION


def _load_taxon_ranges() -> tuple[list[TaxonRange], dict[str, int]]:
    if not PBDB_UBY_CSV.exists():
        raise FileNotFoundError(f"Missing {PBDB_UBY_CSV}. Run examples/annotate_pbdb_animalia_phanerozoic.py first.")

    accumulators: dict[tuple[str, str], TaxonAccumulator] = {}
    raw_rows = 0
    usable_rows = 0
    skipped_rows = 0

    with PBDB_UBY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            raw_rows += 1

            taxon_name, taxon_rank = _taxon_key(row)
            midpoint_ma = _decimal_or_none(row.get("representative_ma_midpoint"))
            max_ma = _decimal_or_none(row.get("max_ma"))
            min_ma = _decimal_or_none(row.get("min_ma"))
            uncertainty_years = _decimal_or_none(row.get("uncertainty_years")) or Decimal("0")
            source_record_id = str(row.get("source_record_id") or "")

            if not taxon_name or midpoint_ma is None or max_ma is None or min_ma is None:
                skipped_rows += 1
                continue

            usable_rows += 1
            key = (taxon_name, taxon_rank)

            if key not in accumulators:
                accumulators[key] = TaxonAccumulator(
                    taxon_name=taxon_name,
                    taxon_rank=taxon_rank,
                    phylum=str(row.get("phylum") or ""),
                    class_name=str(row.get("class_name") or ""),
                    taxonomic_order=str(row.get("taxonomic_order") or ""),
                    family=str(row.get("family") or ""),
                    genus=str(row.get("genus") or ""),
                    first_ma=midpoint_ma,
                    last_ma=midpoint_ma,
                    max_ma_observed=max_ma,
                    min_ma_observed=min_ma,
                    max_uncertainty_years=uncertainty_years,
                    occurrence_count=0,
                    source_record_examples=[],
                )

            accumulators[key].update(midpoint_ma, max_ma, min_ma, uncertainty_years, source_record_id)

    ranges: list[TaxonRange] = []
    for accumulator in accumulators.values():
        duration = accumulator.first_ma - accumulator.last_ma
        ranges.append(
            TaxonRange(
                taxon_name=accumulator.taxon_name,
                taxon_rank=accumulator.taxon_rank,
                phylum=accumulator.phylum,
                class_name=accumulator.class_name,
                taxonomic_order=accumulator.taxonomic_order,
                family=accumulator.family,
                genus=accumulator.genus,
                first_ma=str(accumulator.first_ma),
                last_ma=str(accumulator.last_ma),
                duration_myr=str(duration),
                max_ma_observed=str(accumulator.max_ma_observed),
                min_ma_observed=str(accumulator.min_ma_observed),
                max_uncertainty_years=str(accumulator.max_uncertainty_years),
                first_uby_value=str(_uby_from_ma(accumulator.first_ma)),
                last_uby_value=str(_uby_from_ma(accumulator.last_ma)),
                occurrence_count=accumulator.occurrence_count,
                source_record_examples=";".join(accumulator.source_record_examples),
            )
        )

    ranges.sort(key=lambda item: (Decimal(item.last_ma), item.taxon_name))
    stats = {
        "raw_rows": raw_rows,
        "usable_rows": usable_rows,
        "skipped_rows": skipped_rows,
        "taxon_ranges": len(ranges),
    }
    return ranges, stats


def _build_binned_intensity(taxon_ranges: list[TaxonRange]) -> list[BinnedIntensity]:
    max_first_ma = Decimal("0")
    for item in taxon_ranges:
        first_ma = Decimal(item.first_ma)
        if first_ma > max_first_ma:
            max_first_ma = first_ma

    max_ma = min(MAX_PHANEROZOIC_MA, Decimal(math.ceil(float(max_first_ma))))
    bin_count = int((max_ma / BIN_SIZE_MA).to_integral_value(rounding="ROUND_CEILING"))

    standing = [0 for _ in range(bin_count)]
    first_appearances = [0 for _ in range(bin_count)]
    last_appearances = [0 for _ in range(bin_count)]

    for item in taxon_ranges:
        first_ma = Decimal(item.first_ma)
        last_ma = Decimal(item.last_ma)

        if first_ma < Decimal("0") or last_ma > max_ma:
            continue

        first_bin = min(bin_count - 1, max(0, int(first_ma // BIN_SIZE_MA)))
        last_bin = min(bin_count - 1, max(0, int(last_ma // BIN_SIZE_MA)))

        first_appearances[first_bin] += 1
        last_appearances[last_bin] += 1

        for bin_id in range(last_bin, first_bin + 1):
            standing[bin_id] += 1

    result: list[BinnedIntensity] = []
    for bin_id in range(bin_count):
        young = Decimal(bin_id) * BIN_SIZE_MA
        old = young + BIN_SIZE_MA
        mid = young + BIN_SIZE_MA / Decimal("2")
        standing_taxa = standing[bin_id]
        last_count = last_appearances[bin_id]
        first_count = first_appearances[bin_id]
        extinction_intensity = Decimal(last_count) / Decimal(standing_taxa) if standing_taxa else Decimal("0")
        origination_intensity = Decimal(first_count) / Decimal(standing_taxa) if standing_taxa else Decimal("0")

        result.append(
            BinnedIntensity(
                bin_id=bin_id,
                bin_young_ma=str(young),
                bin_old_ma=str(old),
                bin_mid_ma=str(mid),
                bin_mid_uby_value=str(_uby_from_ma(mid)),
                standing_taxa=standing_taxa,
                first_appearances=first_count,
                last_appearances=last_count,
                extinction_intensity=str(extinction_intensity),
                origination_intensity=str(origination_intensity),
            )
        )

    return result


def _lookup_bin(intensity: list[BinnedIntensity], ma: Decimal) -> BinnedIntensity | None:
    bin_id = int(ma // BIN_SIZE_MA)
    if 0 <= bin_id < len(intensity):
        return intensity[bin_id]
    return None


def _build_recovery_lags(intensity: list[BinnedIntensity]) -> list[RecoveryLag]:
    result: list[RecoveryLag] = []

    for event in REFERENCE_MASS_EXTINCTIONS:
        event_ma = event.ma_decimal
        event_bin = _lookup_bin(intensity, event_ma)
        if event_bin is None:
            continue

        baseline_bins: list[BinnedIntensity] = []
        baseline_start = event_ma
        baseline_end = event_ma + RECOVERY_BASELINE_WINDOW_MA

        for item in intensity:
            mid_ma = Decimal(item.bin_mid_ma)
            if baseline_start < mid_ma <= baseline_end:
                baseline_bins.append(item)

        baseline_values = [item.standing_taxa for item in baseline_bins if item.standing_taxa > 0]
        baseline_mean = Decimal(str(mean(baseline_values))) if baseline_values else Decimal("0")
        threshold = baseline_mean * RECOVERY_THRESHOLD_FRACTION

        post_event_bins = [
            item for item in intensity
            if Decimal(item.bin_mid_ma) < event_ma
        ]
        post_event_bins.sort(key=lambda item: Decimal(item.bin_mid_ma), reverse=True)

        minimum_post_event = min((item.standing_taxa for item in post_event_bins), default=0)
        recovery_bin: BinnedIntensity | None = None
        for item in post_event_bins:
            if Decimal(item.standing_taxa) >= threshold and threshold > 0:
                recovery_bin = item
                break

        if recovery_bin is None:
            recovery_mid = Decimal("NaN")
            recovery_lag_years = Decimal("NaN")
            recovered_flag = 0
        else:
            recovery_mid = Decimal(recovery_bin.bin_mid_ma)
            recovery_lag_years = (event_ma - recovery_mid) * MILLION
            recovered_flag = 1

        result.append(
            RecoveryLag(
                event_name=event.event_name,
                event_ma=str(event.ma_decimal),
                event_uby_value=str(event.uby_value),
                event_uncertainty_ma=str(event.uncertainty_decimal),
                baseline_window_ma=str(RECOVERY_BASELINE_WINDOW_MA),
                baseline_mean_standing_taxa=str(baseline_mean),
                recovery_threshold_fraction=str(RECOVERY_THRESHOLD_FRACTION),
                recovery_threshold_taxa=str(threshold),
                event_bin_standing_taxa=event_bin.standing_taxa,
                minimum_post_event_standing_taxa=minimum_post_event,
                recovery_bin_mid_ma=str(recovery_mid),
                recovery_lag_years=str(recovery_lag_years),
                recovered_flag=recovered_flag,
                method="range-through midpoint diversity; recovery when post-event standing taxa reaches 80% of older-side 10 Myr baseline",
                source_doi=event.source_doi,
            )
        )

    return result


def _build_taxon_disappearances(taxon_ranges: list[TaxonRange]) -> list[TaxonDisappearance]:
    result: list[TaxonDisappearance] = []

    for event in REFERENCE_MASS_EXTINCTIONS:
        event_ma = event.ma_decimal
        window_ma = max(event.uncertainty_decimal, DISAPPEARANCE_WINDOW_MIN_MA)
        young_limit = event_ma - window_ma
        old_limit = event_ma + window_ma

        for item in taxon_ranges:
            last_ma = Decimal(item.last_ma)
            if not (young_limit <= last_ma <= old_limit):
                continue

            lag_years = (event_ma - last_ma) * MILLION
            if lag_years > 0:
                lag_direction = "taxon_disappears_after_boundary"
            elif lag_years < 0:
                lag_direction = "taxon_disappears_before_boundary"
            else:
                lag_direction = "same_representative_time"

            result.append(
                TaxonDisappearance(
                    event_name=event.event_name,
                    event_ma=str(event.ma_decimal),
                    event_uncertainty_ma=str(event.uncertainty_decimal),
                    disappearance_window_ma=str(window_ma),
                    taxon_name=item.taxon_name,
                    taxon_rank=item.taxon_rank,
                    phylum=item.phylum,
                    class_name=item.class_name,
                    taxonomic_order=item.taxonomic_order,
                    family=item.family,
                    genus=item.genus,
                    last_ma=item.last_ma,
                    first_ma=item.first_ma,
                    duration_myr=item.duration_myr,
                    lag_years=str(lag_years),
                    lag_direction=lag_direction,
                    occurrence_count=item.occurrence_count,
                    max_uncertainty_years=item.max_uncertainty_years,
                    source_record_examples=item.source_record_examples,
                )
            )

    result.sort(key=lambda item: (item.event_name, Decimal(item.last_ma), item.taxon_name))
    return result


def _write_csv(path: Path, rows: list[object], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _create_sqlite(
    taxon_ranges: list[TaxonRange],
    intensity: list[BinnedIntensity],
    recovery: list[RecoveryLag],
    disappearances: list[TaxonDisappearance],
) -> None:
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            """
            CREATE TABLE reference_mass_extinctions (
                event_name TEXT NOT NULL,
                event_subcategory TEXT NOT NULL,
                ma_bp REAL NOT NULL,
                uncertainty_ma REAL NOT NULL,
                uby_value REAL NOT NULL,
                uby_value_text TEXT NOT NULL,
                source_dataset TEXT NOT NULL,
                source_doi TEXT,
                source_record_id TEXT PRIMARY KEY,
                source_record_uri TEXT,
                attribution TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO reference_mass_extinctions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    event.event_name,
                    event.event_subcategory,
                    float(event.ma_decimal),
                    float(event.uncertainty_decimal),
                    float(event.uby_value),
                    str(event.uby_value),
                    event.source_dataset,
                    event.source_doi,
                    event.source_record_id,
                    event.source_record_uri,
                    event.attribution,
                )
                for event in REFERENCE_MASS_EXTINCTIONS
            ],
        )

        conn.execute(
            """
            CREATE TABLE pbdb_taxon_ranges (
                taxon_name TEXT NOT NULL,
                taxon_rank TEXT,
                phylum TEXT,
                class_name TEXT,
                taxonomic_order TEXT,
                family TEXT,
                genus TEXT,
                first_ma REAL NOT NULL,
                last_ma REAL NOT NULL,
                duration_myr REAL NOT NULL,
                max_ma_observed REAL,
                min_ma_observed REAL,
                max_uncertainty_years REAL,
                first_uby_value REAL NOT NULL,
                last_uby_value REAL NOT NULL,
                occurrence_count INTEGER NOT NULL,
                source_record_examples TEXT,
                PRIMARY KEY (taxon_name, taxon_rank)
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO pbdb_taxon_ranges VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.taxon_name,
                    item.taxon_rank,
                    item.phylum,
                    item.class_name,
                    item.taxonomic_order,
                    item.family,
                    item.genus,
                    float(Decimal(item.first_ma)),
                    float(Decimal(item.last_ma)),
                    float(Decimal(item.duration_myr)),
                    float(Decimal(item.max_ma_observed)),
                    float(Decimal(item.min_ma_observed)),
                    float(Decimal(item.max_uncertainty_years)),
                    float(Decimal(item.first_uby_value)),
                    float(Decimal(item.last_uby_value)),
                    item.occurrence_count,
                    item.source_record_examples,
                )
                for item in taxon_ranges
            ],
        )

        conn.execute(
            """
            CREATE TABLE pbdb_extinction_intensity_by_bin (
                bin_id INTEGER PRIMARY KEY,
                bin_young_ma REAL NOT NULL,
                bin_old_ma REAL NOT NULL,
                bin_mid_ma REAL NOT NULL,
                bin_mid_uby_value REAL NOT NULL,
                standing_taxa INTEGER NOT NULL,
                first_appearances INTEGER NOT NULL,
                last_appearances INTEGER NOT NULL,
                extinction_intensity REAL NOT NULL,
                origination_intensity REAL NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO pbdb_extinction_intensity_by_bin VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.bin_id,
                    float(Decimal(item.bin_young_ma)),
                    float(Decimal(item.bin_old_ma)),
                    float(Decimal(item.bin_mid_ma)),
                    float(Decimal(item.bin_mid_uby_value)),
                    item.standing_taxa,
                    item.first_appearances,
                    item.last_appearances,
                    float(Decimal(item.extinction_intensity)),
                    float(Decimal(item.origination_intensity)),
                )
                for item in intensity
            ],
        )

        conn.execute(
            """
            CREATE TABLE pbdb_recovery_lag (
                event_name TEXT PRIMARY KEY,
                event_ma REAL NOT NULL,
                event_uby_value REAL NOT NULL,
                event_uncertainty_ma REAL NOT NULL,
                baseline_window_ma REAL NOT NULL,
                baseline_mean_standing_taxa REAL NOT NULL,
                recovery_threshold_fraction REAL NOT NULL,
                recovery_threshold_taxa REAL NOT NULL,
                event_bin_standing_taxa INTEGER NOT NULL,
                minimum_post_event_standing_taxa INTEGER NOT NULL,
                recovery_bin_mid_ma TEXT NOT NULL,
                recovery_lag_years TEXT NOT NULL,
                recovered_flag INTEGER NOT NULL,
                method TEXT NOT NULL,
                source_doi TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO pbdb_recovery_lag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.event_name,
                    float(Decimal(item.event_ma)),
                    float(Decimal(item.event_uby_value)),
                    float(Decimal(item.event_uncertainty_ma)),
                    float(Decimal(item.baseline_window_ma)),
                    float(Decimal(item.baseline_mean_standing_taxa)),
                    float(Decimal(item.recovery_threshold_fraction)),
                    float(Decimal(item.recovery_threshold_taxa)),
                    item.event_bin_standing_taxa,
                    item.minimum_post_event_standing_taxa,
                    item.recovery_bin_mid_ma,
                    item.recovery_lag_years,
                    item.recovered_flag,
                    item.method,
                    item.source_doi,
                )
                for item in recovery
            ],
        )

        conn.execute(
            """
            CREATE TABLE pbdb_taxon_disappearances (
                event_name TEXT NOT NULL,
                event_ma REAL NOT NULL,
                event_uncertainty_ma REAL NOT NULL,
                disappearance_window_ma REAL NOT NULL,
                taxon_name TEXT NOT NULL,
                taxon_rank TEXT,
                phylum TEXT,
                class_name TEXT,
                taxonomic_order TEXT,
                family TEXT,
                genus TEXT,
                last_ma REAL NOT NULL,
                first_ma REAL NOT NULL,
                duration_myr REAL NOT NULL,
                lag_years REAL NOT NULL,
                lag_direction TEXT NOT NULL,
                occurrence_count INTEGER NOT NULL,
                max_uncertainty_years REAL,
                source_record_examples TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO pbdb_taxon_disappearances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.event_name,
                    float(Decimal(item.event_ma)),
                    float(Decimal(item.event_uncertainty_ma)),
                    float(Decimal(item.disappearance_window_ma)),
                    item.taxon_name,
                    item.taxon_rank,
                    item.phylum,
                    item.class_name,
                    item.taxonomic_order,
                    item.family,
                    item.genus,
                    float(Decimal(item.last_ma)),
                    float(Decimal(item.first_ma)),
                    float(Decimal(item.duration_myr)),
                    float(Decimal(item.lag_years)),
                    item.lag_direction,
                    item.occurrence_count,
                    float(Decimal(item.max_uncertainty_years)),
                    item.source_record_examples,
                )
                for item in disappearances
            ],
        )

        conn.execute("CREATE INDEX idx_taxon_ranges_first_ma ON pbdb_taxon_ranges (first_ma)")
        conn.execute("CREATE INDEX idx_taxon_ranges_last_ma ON pbdb_taxon_ranges (last_ma)")
        conn.execute("CREATE INDEX idx_taxon_ranges_class ON pbdb_taxon_ranges (class_name)")
        conn.execute("CREATE INDEX idx_intensity_mid_ma ON pbdb_extinction_intensity_by_bin (bin_mid_ma)")
        conn.execute("CREATE INDEX idx_disappearances_event ON pbdb_taxon_disappearances (event_name)")
        conn.execute("CREATE INDEX idx_disappearances_last_ma ON pbdb_taxon_disappearances (last_ma)")
        conn.execute("CREATE INDEX idx_disappearances_class ON pbdb_taxon_disappearances (class_name)")

        conn.execute("DROP VIEW IF EXISTS pbdb_extinction_hotspots")
        conn.execute(
            """
            CREATE VIEW pbdb_extinction_hotspots AS
            SELECT *
            FROM pbdb_extinction_intensity_by_bin
            WHERE standing_taxa >= 100
            ORDER BY extinction_intensity DESC, last_appearances DESC
            LIMIT 50
            """
        )

        conn.execute("DROP VIEW IF EXISTS pbdb_disappearance_summary_by_event")
        conn.execute(
            """
            CREATE VIEW pbdb_disappearance_summary_by_event AS
            SELECT
                event_name,
                COUNT(*) AS disappearing_taxa,
                SUM(CASE WHEN lag_direction='taxon_disappears_before_boundary' THEN 1 ELSE 0 END) AS before_boundary,
                SUM(CASE WHEN lag_direction='same_representative_time' THEN 1 ELSE 0 END) AS same_representative_time,
                SUM(CASE WHEN lag_direction='taxon_disappears_after_boundary' THEN 1 ELSE 0 END) AS after_boundary,
                AVG(lag_years) AS mean_lag_years
            FROM pbdb_taxon_disappearances
            GROUP BY event_name
            ORDER BY event_ma DESC
            """
        )


def _write_report(
    stats: dict[str, int],
    taxon_ranges: list[TaxonRange],
    intensity: list[BinnedIntensity],
    recovery: list[RecoveryLag],
    disappearances: list[TaxonDisappearance],
    wall_seconds: float,
) -> None:
    top_hotspots = sorted(
        [item for item in intensity if item.standing_taxa >= 100],
        key=lambda item: (Decimal(item.extinction_intensity), item.last_appearances),
        reverse=True,
    )[:20]

    disappearances_by_event: dict[str, int] = {}
    for item in disappearances:
        disappearances_by_event[item.event_name] = disappearances_by_event.get(item.event_name, 0) + 1

    report = {
        "database": "PBDB-derived UBY extinction dynamics",
        "description": (
            "Automated extinction intensity, recovery lag, and taxon-specific disappearance "
            "analysis derived from the full PBDB Animalia/Phanerozoic UBY occurrence table."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "uby_model": DEFAULT_MODEL_VERSION,
        "source_pbdb_uby_csv": str(PBDB_UBY_CSV.as_posix()),
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "taxon_ranges_csv": str(TAXON_RANGES_CSV.as_posix()),
            "intensity_csv": str(INTENSITY_CSV.as_posix()),
            "recovery_csv": str(RECOVERY_CSV.as_posix()),
            "disappearances_csv": str(DISAPPEARANCES_CSV.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "counts": {
            **stats,
            "binned_intensity_rows": len(intensity),
            "reference_mass_extinction_events": len(REFERENCE_MASS_EXTINCTIONS),
            "recovery_lag_rows": len(recovery),
            "taxon_disappearance_rows": len(disappearances),
        },
        "method_summary": {
            "taxon_range_method": "accepted_name/genus/family fallback; first_ma=max representative midpoint; last_ma=min representative midpoint",
            "bin_size_ma": str(BIN_SIZE_MA),
            "extinction_intensity": "last appearances in bin / standing range-through taxa in bin",
            "origination_intensity": "first appearances in bin / standing range-through taxa in bin",
            "recovery_lag": "first younger post-boundary bin where standing taxa reaches 80% of older-side 10 Myr baseline",
            "taxon_disappearance_window": f"max(reference uncertainty, {DISAPPEARANCE_WINDOW_MIN_MA} Ma)",
        },
        "top_extinction_hotspots": [
            {
                "bin_mid_ma": item.bin_mid_ma,
                "standing_taxa": item.standing_taxa,
                "last_appearances": item.last_appearances,
                "extinction_intensity": item.extinction_intensity,
            }
            for item in top_hotspots
        ],
        "recovery_lag": [asdict(item) for item in recovery],
        "disappearances_by_event": disappearances_by_event,
        "research_status": "pbdb_derived_macroecology_first_pass_not_final_causal_claim",
        "claim_boundary": [
            "Extinction intensity and taxon disappearances are now derived from the full PBDB occurrence table rather than seed extinction rows.",
            "Reference mass-extinction boundaries are used only as externally documented comparison anchors.",
            "The current forcing-event replacement is not complete until independent LIP, impact, geochemical, anoxia, sea-level, and climate-proxy databases are ingested.",
            "This first pass does not include sampling standardization, shareholder quorum subsampling, PyRate-style preservation modeling, or Monte Carlo interval propagation.",
            "Use this output as a reproducible discovery dataset, not as a final causal inference.",
        ],
        "build_performance": {
            "wall_seconds": wall_seconds,
            "raw_rows_per_second": stats["raw_rows"] / wall_seconds if wall_seconds else 0,
            "taxa_per_second": len(taxon_ranges) / wall_seconds if wall_seconds else 0,
        },
    }

    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    start = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    taxon_ranges, stats = _load_taxon_ranges()
    intensity = _build_binned_intensity(taxon_ranges)
    recovery = _build_recovery_lags(intensity)
    disappearances = _build_taxon_disappearances(taxon_ranges)

    _write_csv(TAXON_RANGES_CSV, taxon_ranges, list(TaxonRange.__dataclass_fields__))
    _write_csv(INTENSITY_CSV, intensity, list(BinnedIntensity.__dataclass_fields__))
    _write_csv(RECOVERY_CSV, recovery, list(RecoveryLag.__dataclass_fields__))
    _write_csv(DISAPPEARANCES_CSV, disappearances, list(TaxonDisappearance.__dataclass_fields__))
    _create_sqlite(taxon_ranges, intensity, recovery, disappearances)

    wall_seconds = time.perf_counter() - start
    _write_report(stats, taxon_ranges, intensity, recovery, disappearances, wall_seconds)

    print(f"PBDB rows scanned: {stats['raw_rows']}")
    print(f"Usable occurrence rows: {stats['usable_rows']}")
    print(f"Taxon ranges: {len(taxon_ranges)}")
    print(f"Binned intensity rows: {len(intensity)}")
    print(f"Recovery rows: {len(recovery)}")
    print(f"Taxon disappearance rows: {len(disappearances)}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Taxon ranges CSV: {TAXON_RANGES_CSV}")
    print(f"Intensity CSV: {INTENSITY_CSV}")
    print(f"Recovery CSV: {RECOVERY_CSV}")
    print(f"Disappearances CSV: {DISAPPEARANCES_CSV}")
    print(f"Report: {REPORT_OUT}")
    print(f"Build wall seconds: {wall_seconds:.6f}")
    print(f"Rows/s: {stats['raw_rows'] / wall_seconds:.2f}" if wall_seconds else "Rows/s: 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
