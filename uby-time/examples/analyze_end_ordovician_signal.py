#!/usr/bin/env python3
"""
Analyze the End-Ordovician pre-boundary disappearance signal.

This script is a focused follow-up to the extinction sensitivity analysis.  It
tests whether the End-Ordovician signal is driven by particular taxonomic groups,
whether it plausibly reflects a PBDB sampling artifact, whether it persists at
genus/family levels, whether the nearest forcing relationship is stable, and
whether traditional coarse binning compresses pre-boundary disappearances into a
boundary-synchronous event.

Inputs:
- data/processed/pbdb_animalia_phanerozoic_uby.csv
- data/processed/uby_forcing_events.csv

Outputs:
- data/processed/end_ordovician_signal.sqlite
- data/processed/end_ordovician_taxonomic_drivers.csv
- data/processed/end_ordovician_sampling_bins.csv
- data/processed/end_ordovician_taxon_level_stability.csv
- data/processed/end_ordovician_forcing_lags.csv
- data/processed/end_ordovician_binning_compression.csv
- data/processed/end_ordovician_signal_report.json
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
PBDB_UBY_CSV = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.csv"
FORCING_CSV = PROCESSED_DIR / "uby_forcing_events.csv"

SQLITE_OUT = PROCESSED_DIR / "end_ordovician_signal.sqlite"
TAXONOMIC_DRIVERS_CSV = PROCESSED_DIR / "end_ordovician_taxonomic_drivers.csv"
SAMPLING_BINS_CSV = PROCESSED_DIR / "end_ordovician_sampling_bins.csv"
TAXON_LEVEL_STABILITY_CSV = PROCESSED_DIR / "end_ordovician_taxon_level_stability.csv"
FORCING_LAGS_CSV = PROCESSED_DIR / "end_ordovician_forcing_lags.csv"
BINNING_COMPRESSION_CSV = PROCESSED_DIR / "end_ordovician_binning_compression.csv"
REPORT_OUT = PROCESSED_DIR / "end_ordovician_signal_report.json"

EVENT_NAME = "End-Ordovician mass extinction"
EVENT_MA = Decimal("443.8")
EVENT_UNCERTAINTY_MA = Decimal("1.5")
MODEL_BASE_UBY = Decimal("13787000000")
MILLION = Decimal("1000000")
DRIVER_WINDOW_MA = Decimal("5")
SAMPLING_WINDOW_MA = Decimal("15")
SAMPLING_BIN_SIZE_MA = Decimal("1")
COARSE_STAGE_WINDOW_MA = Decimal("5")


@dataclass(frozen=True)
class Occurrence:
    source_record_id: str
    accepted_name: str
    genus: str
    family: str
    taxonomic_order: str
    class_name: str
    phylum: str
    midpoint_ma: Decimal
    max_ma: Decimal
    min_ma: Decimal
    early_interval: str
    late_interval: str


@dataclass(frozen=True)
class TaxonRange:
    taxon_level: str
    taxon_name: str
    phylum: str
    class_name: str
    taxonomic_order: str
    family: str
    first_ma: Decimal
    last_ma: Decimal
    occurrence_count: int


@dataclass(frozen=True)
class TaxonomicDriver:
    grouping_level: str
    group_name: str
    disappearing_taxa: int
    before_boundary: int
    after_boundary: int
    before_fraction: str
    after_fraction: str
    mean_lag_years: str


@dataclass(frozen=True)
class SamplingBin:
    bin_young_ma: str
    bin_old_ma: str
    bin_mid_ma: str
    occurrence_count: int
    unique_accepted_names: int
    unique_genera: int
    unique_families: int
    last_accepted_names: int
    last_genera: int
    last_families: int


@dataclass(frozen=True)
class TaxonLevelStability:
    taxon_level: str
    disappearing_taxa: int
    before_boundary: int
    after_boundary: int
    before_fraction: str
    after_fraction: str
    mean_lag_years: str


@dataclass(frozen=True)
class ForcingLag:
    forcing_event_name: str
    forcing_category: str
    forcing_subcategory: str
    forcing_ma: str
    forcing_uncertainty_ma: str
    lag_years: str
    abs_lag_years: str
    overlap_flag: int


@dataclass(frozen=True)
class BinningCompression:
    taxon_level: str
    window_ma: str
    precise_before_boundary: int
    precise_after_boundary: int
    precise_before_fraction: str
    coarse_boundary_synchronous_count: int
    compression_ratio: str
    interpretation: str


def _decimal_or_none(value: str | None) -> Decimal | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _load_occurrences() -> tuple[list[Occurrence], int, int]:
    occurrences: list[Occurrence] = []
    skipped = 0
    raw = 0
    with PBDB_UBY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            raw += 1
            midpoint = _decimal_or_none(row.get("representative_ma_midpoint"))
            max_ma = _decimal_or_none(row.get("max_ma"))
            min_ma = _decimal_or_none(row.get("min_ma"))
            if midpoint is None or max_ma is None or min_ma is None:
                skipped += 1
                continue
            occurrences.append(
                Occurrence(
                    source_record_id=str(row.get("source_record_id") or ""),
                    accepted_name=str(row.get("accepted_name") or "").strip(),
                    genus=str(row.get("genus") or "").strip(),
                    family=str(row.get("family") or "").strip(),
                    taxonomic_order=str(row.get("taxonomic_order") or "").strip(),
                    class_name=str(row.get("class_name") or "").strip(),
                    phylum=str(row.get("phylum") or "").strip(),
                    midpoint_ma=midpoint,
                    max_ma=max_ma,
                    min_ma=min_ma,
                    early_interval=str(row.get("early_interval") or "").strip(),
                    late_interval=str(row.get("late_interval") or "").strip(),
                )
            )
    return occurrences, raw, skipped


def _taxon_key(occurrence: Occurrence, level: str) -> str:
    if level == "accepted_name":
        return occurrence.accepted_name
    if level == "genus":
        return occurrence.genus
    if level == "family":
        return occurrence.family
    raise ValueError(level)


def _build_ranges(occurrences: list[Occurrence], level: str) -> list[TaxonRange]:
    records: dict[str, dict[str, object]] = {}
    for occ in occurrences:
        name = _taxon_key(occ, level)
        if not name:
            continue
        if name not in records:
            records[name] = {
                "first_ma": occ.midpoint_ma,
                "last_ma": occ.midpoint_ma,
                "phylum": occ.phylum,
                "class_name": occ.class_name,
                "taxonomic_order": occ.taxonomic_order,
                "family": occ.family,
                "occurrence_count": 0,
            }
        rec = records[name]
        if occ.midpoint_ma > rec["first_ma"]:
            rec["first_ma"] = occ.midpoint_ma
        if occ.midpoint_ma < rec["last_ma"]:
            rec["last_ma"] = occ.midpoint_ma
        rec["occurrence_count"] = int(rec["occurrence_count"]) + 1

    return [
        TaxonRange(
            taxon_level=level,
            taxon_name=name,
            phylum=str(rec["phylum"]),
            class_name=str(rec["class_name"]),
            taxonomic_order=str(rec["taxonomic_order"]),
            family=str(rec["family"]),
            first_ma=rec["first_ma"],  # type: ignore[arg-type]
            last_ma=rec["last_ma"],  # type: ignore[arg-type]
            occurrence_count=int(rec["occurrence_count"]),
        )
        for name, rec in records.items()
    ]


def _disappearing_ranges(ranges: list[TaxonRange], window_ma: Decimal) -> list[TaxonRange]:
    young = EVENT_MA - window_ma
    old = EVENT_MA + window_ma
    return [item for item in ranges if young <= item.last_ma <= old]


def _lag_years(last_ma: Decimal) -> Decimal:
    return (EVENT_MA - last_ma) * MILLION


def _driver_rows(ranges: list[TaxonRange]) -> list[TaxonomicDriver]:
    disappearing = _disappearing_ranges(ranges, DRIVER_WINDOW_MA)
    output: list[TaxonomicDriver] = []

    for grouping in ("phylum", "class_name", "taxonomic_order", "family"):
        groups: dict[str, list[TaxonRange]] = {}
        for item in disappearing:
            group_name = str(getattr(item, grouping)) or "UNKNOWN"
            groups.setdefault(group_name, []).append(item)

        for group_name, items in groups.items():
            lags = [_lag_years(item.last_ma) for item in items]
            before = sum(1 for lag in lags if lag < 0)
            after = sum(1 for lag in lags if lag > 0)
            total = len(items)
            if total < 5:
                continue
            output.append(
                TaxonomicDriver(
                    grouping_level=grouping,
                    group_name=group_name,
                    disappearing_taxa=total,
                    before_boundary=before,
                    after_boundary=after,
                    before_fraction=str(Decimal(before) / Decimal(total)),
                    after_fraction=str(Decimal(after) / Decimal(total)),
                    mean_lag_years=str(sum(lags, Decimal("0")) / Decimal(total)),
                )
            )

    output.sort(key=lambda row: (row.disappearing_taxa, Decimal(row.before_fraction)), reverse=True)
    return output


def _sampling_bins(occurrences: list[Occurrence], accepted_ranges: list[TaxonRange], genus_ranges: list[TaxonRange], family_ranges: list[TaxonRange]) -> list[SamplingBin]:
    young_limit = EVENT_MA - SAMPLING_WINDOW_MA
    old_limit = EVENT_MA + SAMPLING_WINDOW_MA
    rows: list[SamplingBin] = []

    current = young_limit
    while current < old_limit:
        young = current
        old = current + SAMPLING_BIN_SIZE_MA
        midpoint = young + SAMPLING_BIN_SIZE_MA / Decimal("2")

        occs = [occ for occ in occurrences if young <= occ.midpoint_ma < old]
        rows.append(
            SamplingBin(
                bin_young_ma=str(young),
                bin_old_ma=str(old),
                bin_mid_ma=str(midpoint),
                occurrence_count=len(occs),
                unique_accepted_names=len({occ.accepted_name for occ in occs if occ.accepted_name}),
                unique_genera=len({occ.genus for occ in occs if occ.genus}),
                unique_families=len({occ.family for occ in occs if occ.family}),
                last_accepted_names=sum(1 for item in accepted_ranges if young <= item.last_ma < old),
                last_genera=sum(1 for item in genus_ranges if young <= item.last_ma < old),
                last_families=sum(1 for item in family_ranges if young <= item.last_ma < old),
            )
        )
        current = old

    return rows


def _taxon_level_stability(ranges_by_level: dict[str, list[TaxonRange]]) -> list[TaxonLevelStability]:
    rows: list[TaxonLevelStability] = []
    for level, ranges in ranges_by_level.items():
        disappearing = _disappearing_ranges(ranges, DRIVER_WINDOW_MA)
        lags = [_lag_years(item.last_ma) for item in disappearing]
        before = sum(1 for lag in lags if lag < 0)
        after = sum(1 for lag in lags if lag > 0)
        total = len(disappearing)
        rows.append(
            TaxonLevelStability(
                taxon_level=level,
                disappearing_taxa=total,
                before_boundary=before,
                after_boundary=after,
                before_fraction=str(Decimal(before) / Decimal(total) if total else Decimal("0")),
                after_fraction=str(Decimal(after) / Decimal(total) if total else Decimal("0")),
                mean_lag_years=str(sum(lags, Decimal("0")) / Decimal(total) if total else Decimal("0")),
            )
        )
    return rows


def _forcing_lags() -> list[ForcingLag]:
    event_uby = MODEL_BASE_UBY - EVENT_MA * MILLION
    event_uncertainty_years = EVENT_UNCERTAINTY_MA * MILLION
    rows: list[ForcingLag] = []

    with FORCING_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ma = _decimal_or_none(row.get("ma_bp"))
            uncertainty_ma = _decimal_or_none(row.get("uncertainty_ma"))
            if ma is None or uncertainty_ma is None:
                continue
            forcing_uby = MODEL_BASE_UBY - ma * MILLION
            lag = event_uby - forcing_uby
            abs_lag = abs(lag)
            if abs_lag > Decimal("10000000"):
                continue
            overlap = int(abs_lag <= event_uncertainty_years + uncertainty_ma * MILLION)
            rows.append(
                ForcingLag(
                    forcing_event_name=str(row.get("event_name") or ""),
                    forcing_category=str(row.get("forcing_category") or ""),
                    forcing_subcategory=str(row.get("forcing_subcategory") or ""),
                    forcing_ma=str(ma),
                    forcing_uncertainty_ma=str(uncertainty_ma),
                    lag_years=str(lag),
                    abs_lag_years=str(abs_lag),
                    overlap_flag=overlap,
                )
            )

    rows.sort(key=lambda item: Decimal(item.abs_lag_years))
    return rows


def _binning_compression(ranges_by_level: dict[str, list[TaxonRange]]) -> list[BinningCompression]:
    rows: list[BinningCompression] = []
    for level, ranges in ranges_by_level.items():
        disappearing = _disappearing_ranges(ranges, COARSE_STAGE_WINDOW_MA)
        lags = [_lag_years(item.last_ma) for item in disappearing]
        before = sum(1 for lag in lags if lag < 0)
        after = sum(1 for lag in lags if lag > 0)
        total = len(disappearing)
        before_fraction = Decimal(before) / Decimal(total) if total else Decimal("0")
        compression_ratio = Decimal(total) / Decimal(before) if before else Decimal("0")
        rows.append(
            BinningCompression(
                taxon_level=level,
                window_ma=str(COARSE_STAGE_WINDOW_MA),
                precise_before_boundary=before,
                precise_after_boundary=after,
                precise_before_fraction=str(before_fraction),
                coarse_boundary_synchronous_count=total,
                compression_ratio=str(compression_ratio),
                interpretation=(
                    "Traditional coarse-window binning would count all taxa in this interval as boundary-associated; "
                    "compression_ratio compares coarse synchronous count to explicitly pre-boundary disappearances."
                ),
            )
        )
    return rows


def _write_csv(path: Path, rows: list[object], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_sqlite(
    drivers: list[TaxonomicDriver],
    sampling: list[SamplingBin],
    stability: list[TaxonLevelStability],
    forcing: list[ForcingLag],
    compression: list[BinningCompression],
) -> None:
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    with sqlite3.connect(SQLITE_OUT) as conn:
        for table_name, rows, cls in (
            ("taxonomic_drivers", drivers, TaxonomicDriver),
            ("sampling_bins", sampling, SamplingBin),
            ("taxon_level_stability", stability, TaxonLevelStability),
            ("forcing_lags", forcing, ForcingLag),
            ("binning_compression", compression, BinningCompression),
        ):
            columns = list(cls.__dataclass_fields__)
            conn.execute(f"CREATE TABLE {table_name} ({', '.join(column + ' TEXT' for column in columns)})")
            placeholders = ", ".join(":" + column for column in columns)
            conn.executemany(
                f"INSERT INTO {table_name} VALUES ({placeholders})",
                [asdict(row) for row in rows],
            )

        conn.execute("CREATE INDEX idx_endord_drivers_group ON taxonomic_drivers (grouping_level, group_name)")
        conn.execute("CREATE INDEX idx_endord_sampling_mid ON sampling_bins (bin_mid_ma)")
        conn.execute("CREATE INDEX idx_endord_forcing_abs_lag ON forcing_lags (abs_lag_years)")


def _report(
    raw_rows: int,
    skipped_rows: int,
    ranges_by_level: dict[str, list[TaxonRange]],
    drivers: list[TaxonomicDriver],
    sampling: list[SamplingBin],
    stability: list[TaxonLevelStability],
    forcing: list[ForcingLag],
    compression: list[BinningCompression],
    wall_seconds: float,
) -> dict[str, object]:
    top_driver_classes = [
        asdict(row)
        for row in drivers
        if row.grouping_level == "class_name"
    ][:10]
    top_driver_orders = [
        asdict(row)
        for row in drivers
        if row.grouping_level == "taxonomic_order"
    ][:10]

    nearest_forcing = asdict(forcing[0]) if forcing else {}
    sampling_event_bin = min(
        sampling,
        key=lambda row: abs(Decimal(row.bin_mid_ma) - EVENT_MA),
    )

    accepted_stability = next(row for row in stability if row.taxon_level == "accepted_name")
    genus_stability = next(row for row in stability if row.taxon_level == "genus")
    family_stability = next(row for row in stability if row.taxon_level == "family")

    stable_across_levels = all(
        Decimal(row.before_fraction) > Decimal(row.after_fraction)
        for row in stability
    )
    sea_level_or_climate_overlap = any(
        row.overlap_flag == 1 and row.forcing_category in {"sea_level", "climate"}
        for row in forcing
    )

    return {
        "database": "End-Ordovician UBY signal analysis",
        "description": "Focused analysis of PBDB-derived End-Ordovician pre-boundary disappearance and recovery signal.",
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "event": {
            "event_name": EVENT_NAME,
            "event_ma": str(EVENT_MA),
            "event_uncertainty_ma": str(EVENT_UNCERTAINTY_MA),
        },
        "inputs": {
            "pbdb_uby_csv": str(PBDB_UBY_CSV.as_posix()),
            "forcing_csv": str(FORCING_CSV.as_posix()),
        },
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "taxonomic_drivers_csv": str(TAXONOMIC_DRIVERS_CSV.as_posix()),
            "sampling_bins_csv": str(SAMPLING_BINS_CSV.as_posix()),
            "taxon_level_stability_csv": str(TAXON_LEVEL_STABILITY_CSV.as_posix()),
            "forcing_lags_csv": str(FORCING_LAGS_CSV.as_posix()),
            "binning_compression_csv": str(BINNING_COMPRESSION_CSV.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "counts": {
            "raw_rows": raw_rows,
            "skipped_rows": skipped_rows,
            "accepted_name_ranges": len(ranges_by_level["accepted_name"]),
            "genus_ranges": len(ranges_by_level["genus"]),
            "family_ranges": len(ranges_by_level["family"]),
            "taxonomic_driver_rows": len(drivers),
            "sampling_bins": len(sampling),
            "forcing_lags_within_10myr": len(forcing),
        },
        "key_findings": {
            "stable_pre_boundary_across_accepted_genus_family": stable_across_levels,
            "accepted_name_before_fraction": accepted_stability.before_fraction,
            "genus_before_fraction": genus_stability.before_fraction,
            "family_before_fraction": family_stability.before_fraction,
            "nearest_forcing": nearest_forcing,
            "sea_level_or_climate_overlap": sea_level_or_climate_overlap,
            "event_bin_sampling": asdict(sampling_event_bin),
            "top_driver_classes": top_driver_classes,
            "top_driver_orders": top_driver_orders,
            "binning_compression": [asdict(row) for row in compression],
        },
        "research_status": "focused_signal_analysis_not_final_claim",
        "claim_boundary": [
            "This analysis identifies candidate taxonomic and temporal structure but does not perform sampling standardization.",
            "Traditional binning compression is estimated by a coarse time-window comparison, not a full stratigraphic-stage model.",
            "Publication-grade claims require interval Monte Carlo, PBDB collection-level sampling controls, and external Ordovician specialist validation.",
        ],
        "build_performance": {
            "wall_seconds": wall_seconds,
            "rows_per_second": raw_rows / wall_seconds if wall_seconds else 0,
        },
    }


def main() -> int:
    start = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    occurrences, raw_rows, skipped_rows = _load_occurrences()
    ranges_by_level = {
        "accepted_name": _build_ranges(occurrences, "accepted_name"),
        "genus": _build_ranges(occurrences, "genus"),
        "family": _build_ranges(occurrences, "family"),
    }

    drivers = _driver_rows(ranges_by_level["accepted_name"])
    sampling = _sampling_bins(
        occurrences,
        ranges_by_level["accepted_name"],
        ranges_by_level["genus"],
        ranges_by_level["family"],
    )
    stability = _taxon_level_stability(ranges_by_level)
    forcing = _forcing_lags()
    compression = _binning_compression(ranges_by_level)

    _write_csv(TAXONOMIC_DRIVERS_CSV, drivers, list(TaxonomicDriver.__dataclass_fields__))
    _write_csv(SAMPLING_BINS_CSV, sampling, list(SamplingBin.__dataclass_fields__))
    _write_csv(TAXON_LEVEL_STABILITY_CSV, stability, list(TaxonLevelStability.__dataclass_fields__))
    _write_csv(FORCING_LAGS_CSV, forcing, list(ForcingLag.__dataclass_fields__))
    _write_csv(BINNING_COMPRESSION_CSV, compression, list(BinningCompression.__dataclass_fields__))
    _write_sqlite(drivers, sampling, stability, forcing, compression)

    wall_seconds = time.perf_counter() - start
    report = _report(
        raw_rows,
        skipped_rows,
        ranges_by_level,
        drivers,
        sampling,
        stability,
        forcing,
        compression,
        wall_seconds,
    )
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    findings = report["key_findings"]
    print(f"PBDB rows scanned: {raw_rows}")
    print(f"Accepted-name ranges: {len(ranges_by_level['accepted_name'])}")
    print(f"Genus ranges: {len(ranges_by_level['genus'])}")
    print(f"Family ranges: {len(ranges_by_level['family'])}")
    print(f"Stable pre-boundary across levels: {findings['stable_pre_boundary_across_accepted_genus_family']}")
    print(f"Nearest forcing: {findings['nearest_forcing']}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Report: {REPORT_OUT}")
    print(f"Build wall seconds: {wall_seconds:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
