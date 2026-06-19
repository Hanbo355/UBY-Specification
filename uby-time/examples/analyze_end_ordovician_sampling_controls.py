#!/usr/bin/env python3
"""
PBDB sampling-control follow-up for the End-Ordovician UBY signal.

This script focuses on the most important unresolved caveat from
``analyze_end_ordovician_signal.py``: whether the apparent End-Ordovician
pre-boundary disappearance concentration could be a simple PBDB sampling artifact.

Because the current annotated PBDB occurrence export does not include a native
PBDB collection number, this first-pass control uses transparent sampling proxies:
- occurrence count per 1 Myr bin,
- unique accepted names / genera / families,
- unique references,
- unique formations,
- geographic grid cells,
- pseudo-collections based on interval + formation/group/member + reference + grid cell.

It also compares the pre-boundary disappearance window with the rest of the
local +/-15 Myr interval and records whether high disappearance concentration is
paired with an extreme sampling collapse.

Inputs:
- data/processed/pbdb_animalia_phanerozoic_uby.csv

Outputs:
- data/processed/end_ordovician_sampling_controls.sqlite
- data/processed/end_ordovician_sampling_control_bins.csv
- data/processed/end_ordovician_sampling_control_summary.json
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
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import GENERATED_BY, UBY_SPEC_VERSION

PROCESSED_DIR = ROOT / "data" / "processed"
PBDB_UBY_CSV = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.csv"

SQLITE_OUT = PROCESSED_DIR / "end_ordovician_sampling_controls.sqlite"
BIN_CSV_OUT = PROCESSED_DIR / "end_ordovician_sampling_control_bins.csv"
REPORT_OUT = PROCESSED_DIR / "end_ordovician_sampling_control_summary.json"

EVENT_NAME = "End-Ordovician mass extinction"
EVENT_MA = Decimal("443.8")
LOCAL_WINDOW_MA = Decimal("15")
SIGNAL_WINDOW_MA = Decimal("5")
BIN_SIZE_MA = Decimal("1")


@dataclass(frozen=True)
class Occurrence:
    accepted_name: str
    genus: str
    family: str
    midpoint_ma: Decimal
    early_interval: str
    late_interval: str
    formation: str
    geological_group: str
    member: str
    reference_no: str
    longitude: str
    latitude: str


@dataclass(frozen=True)
class TaxonRange:
    taxon_level: str
    taxon_name: str
    last_ma: Decimal


@dataclass(frozen=True)
class SamplingControlBin:
    bin_young_ma: str
    bin_old_ma: str
    bin_mid_ma: str
    relation_to_boundary: str
    occurrence_count: int
    unique_accepted_names: int
    unique_genera: int
    unique_families: int
    reference_count: int
    formation_count: int
    geo_cell_count: int
    pseudo_collection_count: int
    accepted_last_taxa: int
    genus_last_taxa: int
    family_last_taxa: int
    accepted_last_per_occurrence: str
    accepted_last_per_pseudo_collection: str
    genus_last_per_occurrence: str
    family_last_per_occurrence: str


def _decimal_or_none(value: str | None) -> Decimal | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _geo_cell(latitude: str, longitude: str) -> str:
    try:
        lat = float(latitude)
        lon = float(longitude)
    except Exception:
        return "NO_GEO"
    if not math.isfinite(lat) or not math.isfinite(lon):
        return "NO_GEO"
    lat_cell = math.floor(lat / 5.0) * 5
    lon_cell = math.floor(lon / 5.0) * 5
    return f"{lat_cell}:{lon_cell}"


def _pseudo_collection_key(occ: Occurrence) -> str:
    interval = occ.late_interval or occ.early_interval or "NO_INTERVAL"
    lithostrat = occ.formation or occ.geological_group or occ.member or "NO_LITHOSTRAT"
    reference = occ.reference_no or "NO_REFERENCE"
    return "|".join((interval, lithostrat, reference, _geo_cell(occ.latitude, occ.longitude)))


def _load_local_occurrences() -> tuple[list[Occurrence], int, int]:
    young_limit = EVENT_MA - LOCAL_WINDOW_MA
    old_limit = EVENT_MA + LOCAL_WINDOW_MA
    raw_rows = 0
    skipped_rows = 0
    occurrences: list[Occurrence] = []

    with PBDB_UBY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            raw_rows += 1
            midpoint = _decimal_or_none(row.get("representative_ma_midpoint"))
            if midpoint is None:
                skipped_rows += 1
                continue
            if not (young_limit <= midpoint < old_limit):
                continue
            occurrences.append(
                Occurrence(
                    accepted_name=str(row.get("accepted_name") or "").strip(),
                    genus=str(row.get("genus") or "").strip(),
                    family=str(row.get("family") or "").strip(),
                    midpoint_ma=midpoint,
                    early_interval=str(row.get("early_interval") or "").strip(),
                    late_interval=str(row.get("late_interval") or "").strip(),
                    formation=str(row.get("formation") or "").strip(),
                    geological_group=str(row.get("geological_group") or "").strip(),
                    member=str(row.get("member") or "").strip(),
                    reference_no=str(row.get("reference_no") or "").strip(),
                    longitude=str(row.get("longitude") or "").strip(),
                    latitude=str(row.get("latitude") or "").strip(),
                )
            )
    return occurrences, raw_rows, skipped_rows


def _load_global_ranges() -> dict[str, list[TaxonRange]]:
    """Build global last-appearance ranges from the full PBDB export.

    Sampling proxies are evaluated only in the local +/-15 Myr window, but last
    appearances must be global.  If ranges were computed only from local rows,
    taxa that continue outside the window would be falsely treated as disappearing
    at the local window edge.
    """

    last_by_level: dict[str, dict[str, Decimal]] = {
        "accepted_name": {},
        "genus": {},
        "family": {},
    }

    with PBDB_UBY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            midpoint = _decimal_or_none(row.get("representative_ma_midpoint"))
            if midpoint is None:
                continue
            values = {
                "accepted_name": str(row.get("accepted_name") or "").strip(),
                "genus": str(row.get("genus") or "").strip(),
                "family": str(row.get("family") or "").strip(),
            }
            for level, name in values.items():
                if not name:
                    continue
                previous = last_by_level[level].get(name)
                if previous is None or midpoint < previous:
                    last_by_level[level][name] = midpoint

    return {
        level: [
            TaxonRange(taxon_level=level, taxon_name=name, last_ma=last_ma)
            for name, last_ma in values.items()
        ]
        for level, values in last_by_level.items()
    }


def _taxon_name(occ: Occurrence, level: str) -> str:
    if level == "accepted_name":
        return occ.accepted_name
    if level == "genus":
        return occ.genus
    if level == "family":
        return occ.family
    raise ValueError(level)


def _build_ranges(occurrences: list[Occurrence], level: str) -> list[TaxonRange]:
    last_by_taxon: dict[str, Decimal] = {}
    for occ in occurrences:
        name = _taxon_name(occ, level)
        if not name:
            continue
        previous = last_by_taxon.get(name)
        if previous is None or occ.midpoint_ma < previous:
            last_by_taxon[name] = occ.midpoint_ma
    return [
        TaxonRange(taxon_level=level, taxon_name=name, last_ma=last_ma)
        for name, last_ma in last_by_taxon.items()
    ]


def _relation_to_boundary(young: Decimal, old: Decimal) -> str:
    if old <= EVENT_MA:
        return "post_boundary_younger_side"
    if young >= EVENT_MA:
        return "pre_boundary_older_side"
    return "boundary_crossing_bin"


def _count_last_taxa(ranges: list[TaxonRange], young: Decimal, old: Decimal) -> int:
    return sum(1 for item in ranges if young <= item.last_ma < old)


def _safe_ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0"
    return str(Decimal(numerator) / Decimal(denominator))


def _build_bins(occurrences: list[Occurrence], ranges_by_level: dict[str, list[TaxonRange]]) -> list[SamplingControlBin]:
    young_limit = EVENT_MA - LOCAL_WINDOW_MA
    old_limit = EVENT_MA + LOCAL_WINDOW_MA
    rows: list[SamplingControlBin] = []

    current = young_limit
    while current < old_limit:
        young = current
        old = current + BIN_SIZE_MA
        mid = young + BIN_SIZE_MA / Decimal("2")
        occs = [occ for occ in occurrences if young <= occ.midpoint_ma < old]

        accepted_last = _count_last_taxa(ranges_by_level["accepted_name"], young, old)
        genus_last = _count_last_taxa(ranges_by_level["genus"], young, old)
        family_last = _count_last_taxa(ranges_by_level["family"], young, old)
        pseudo_collections = {_pseudo_collection_key(occ) for occ in occs}

        rows.append(
            SamplingControlBin(
                bin_young_ma=str(young),
                bin_old_ma=str(old),
                bin_mid_ma=str(mid),
                relation_to_boundary=_relation_to_boundary(young, old),
                occurrence_count=len(occs),
                unique_accepted_names=len({occ.accepted_name for occ in occs if occ.accepted_name}),
                unique_genera=len({occ.genus for occ in occs if occ.genus}),
                unique_families=len({occ.family for occ in occs if occ.family}),
                reference_count=len({occ.reference_no for occ in occs if occ.reference_no}),
                formation_count=len({occ.formation for occ in occs if occ.formation}),
                geo_cell_count=len({_geo_cell(occ.latitude, occ.longitude) for occ in occs}),
                pseudo_collection_count=len(pseudo_collections),
                accepted_last_taxa=accepted_last,
                genus_last_taxa=genus_last,
                family_last_taxa=family_last,
                accepted_last_per_occurrence=_safe_ratio(accepted_last, len(occs)),
                accepted_last_per_pseudo_collection=_safe_ratio(accepted_last, len(pseudo_collections)),
                genus_last_per_occurrence=_safe_ratio(genus_last, len(occs)),
                family_last_per_occurrence=_safe_ratio(family_last, len(occs)),
            )
        )
        current = old

    return rows


def _window_rows(rows: list[SamplingControlBin], relation: str) -> list[SamplingControlBin]:
    return [row for row in rows if row.relation_to_boundary == relation]


def _median_int(rows: list[SamplingControlBin], attr: str) -> float:
    values = [int(getattr(row, attr)) for row in rows]
    return float(median(values)) if values else 0.0


def _sum_int(rows: list[SamplingControlBin], attr: str) -> int:
    return sum(int(getattr(row, attr)) for row in rows)


def _write_csv(rows: list[SamplingControlBin]) -> None:
    with BIN_CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(SamplingControlBin.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_sqlite(rows: list[SamplingControlBin]) -> None:
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()
    with sqlite3.connect(SQLITE_OUT) as conn:
        columns = list(SamplingControlBin.__dataclass_fields__)
        conn.execute(
            "CREATE TABLE sampling_control_bins ("
            + ", ".join(f"{column} TEXT" for column in columns)
            + ")"
        )
        conn.executemany(
            "INSERT INTO sampling_control_bins VALUES ("
            + ", ".join(":" + column for column in columns)
            + ")",
            [asdict(row) for row in rows],
        )
        conn.execute("CREATE INDEX idx_endord_sampling_control_mid ON sampling_control_bins (bin_mid_ma)")
        conn.execute("CREATE INDEX idx_endord_sampling_control_relation ON sampling_control_bins (relation_to_boundary)")


def _report(
    occurrences: list[Occurrence],
    raw_rows: int,
    skipped_rows: int,
    ranges_by_level: dict[str, list[TaxonRange]],
    rows: list[SamplingControlBin],
    wall_seconds: float,
) -> dict[str, object]:
    pre_rows = _window_rows(rows, "pre_boundary_older_side")
    post_rows = _window_rows(rows, "post_boundary_younger_side")
    boundary_rows = _window_rows(rows, "boundary_crossing_bin")

    event_bin = min(rows, key=lambda row: abs(Decimal(row.bin_mid_ma) - EVENT_MA))
    min_occurrence_bin = min(rows, key=lambda row: int(row.occurrence_count))
    max_last_ratio_bin = max(rows, key=lambda row: Decimal(row.accepted_last_per_occurrence))

    pre_occurrence_median = _median_int(pre_rows, "occurrence_count")
    post_occurrence_median = _median_int(post_rows, "occurrence_count")
    pre_pseudo_collection_median = _median_int(pre_rows, "pseudo_collection_count")
    post_pseudo_collection_median = _median_int(post_rows, "pseudo_collection_count")

    pre_accepted_last = _sum_int(pre_rows, "accepted_last_taxa")
    post_accepted_last = _sum_int(post_rows, "accepted_last_taxa")
    pre_genus_last = _sum_int(pre_rows, "genus_last_taxa")
    post_genus_last = _sum_int(post_rows, "genus_last_taxa")
    pre_family_last = _sum_int(pre_rows, "family_last_taxa")
    post_family_last = _sum_int(post_rows, "family_last_taxa")

    event_occurrences = int(event_bin.occurrence_count)
    event_pseudo_collections = int(event_bin.pseudo_collection_count)
    local_occurrence_median = _median_int(rows, "occurrence_count")
    local_pseudo_collection_median = _median_int(rows, "pseudo_collection_count")

    event_occurrence_fraction_of_local_median = (
        event_occurrences / local_occurrence_median if local_occurrence_median else 0
    )
    event_pseudo_collection_fraction_of_local_median = (
        event_pseudo_collections / local_pseudo_collection_median if local_pseudo_collection_median else 0
    )

    return {
        "database": "End-Ordovician PBDB sampling-control proxy analysis",
        "description": (
            "First-pass sampling controls for the End-Ordovician UBY signal using occurrence, reference, "
            "formation, geographic-grid, and pseudo-collection proxies."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "event": {
            "event_name": EVENT_NAME,
            "event_ma": str(EVENT_MA),
            "local_window_ma": str(LOCAL_WINDOW_MA),
            "bin_size_ma": str(BIN_SIZE_MA),
        },
        "inputs": {
            "pbdb_uby_csv": str(PBDB_UBY_CSV.as_posix()),
        },
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "bin_csv": str(BIN_CSV_OUT.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "counts": {
            "raw_rows": raw_rows,
            "skipped_rows": skipped_rows,
            "local_occurrences_within_30myr": len(occurrences),
            "accepted_name_ranges_global": len(ranges_by_level["accepted_name"]),
            "genus_ranges_global": len(ranges_by_level["genus"]),
            "family_ranges_global": len(ranges_by_level["family"]),
            "sampling_bins": len(rows),
        },
        "key_findings": {
            "pre_boundary_accepted_last_taxa": pre_accepted_last,
            "post_boundary_accepted_last_taxa": post_accepted_last,
            "pre_boundary_genus_last_taxa": pre_genus_last,
            "post_boundary_genus_last_taxa": post_genus_last,
            "pre_boundary_family_last_taxa": pre_family_last,
            "post_boundary_family_last_taxa": post_family_last,
            "pre_boundary_occurrence_median": pre_occurrence_median,
            "post_boundary_occurrence_median": post_occurrence_median,
            "pre_boundary_pseudo_collection_median": pre_pseudo_collection_median,
            "post_boundary_pseudo_collection_median": post_pseudo_collection_median,
            "event_bin": asdict(event_bin),
            "min_occurrence_bin": asdict(min_occurrence_bin),
            "max_accepted_last_per_occurrence_bin": asdict(max_last_ratio_bin),
            "event_occurrence_fraction_of_local_median": event_occurrence_fraction_of_local_median,
            "event_pseudo_collection_fraction_of_local_median": event_pseudo_collection_fraction_of_local_median,
            "simple_sampling_collapse_flag": (
                event_occurrence_fraction_of_local_median < 0.25
                and event_pseudo_collection_fraction_of_local_median < 0.25
            ),
            "pre_boundary_last_taxa_exceed_post_boundary": (
                pre_accepted_last > post_accepted_last
                and pre_genus_last > post_genus_last
                and pre_family_last > post_family_last
            ),
            "boundary_crossing_bins": [asdict(row) for row in boundary_rows],
        },
        "claim_boundary": [
            "This is not full PBDB collection-level standardization because collection numbers are not present in the current annotated export.",
            "Pseudo-collections are transparent proxies built from interval, lithostratigraphy, reference, and 5-degree geographic grid cells.",
            "A publication-grade analysis still requires PBDB collection-level data, shareholder quorum subsampling, preservation modeling, and geographic standardization.",
        ],
        "build_performance": {
            "wall_seconds": wall_seconds,
            "rows_per_second_raw_scan": raw_rows / wall_seconds if wall_seconds else 0,
        },
    }


def main() -> int:
    start = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    occurrences, raw_rows, skipped_rows = _load_local_occurrences()
    ranges_by_level = _load_global_ranges()
    rows = _build_bins(occurrences, ranges_by_level)

    _write_csv(rows)
    _write_sqlite(rows)

    wall_seconds = time.perf_counter() - start
    report = _report(occurrences, raw_rows, skipped_rows, ranges_by_level, rows, wall_seconds)
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    key = report["key_findings"]
    print(f"PBDB raw rows scanned: {raw_rows}")
    print(f"Local occurrences within +/-{LOCAL_WINDOW_MA} Myr: {len(occurrences)}")
    print(f"Sampling bins: {len(rows)}")
    print(f"Simple sampling collapse flag: {key['simple_sampling_collapse_flag']}")
    print(f"Pre-boundary last taxa exceed post-boundary: {key['pre_boundary_last_taxa_exceed_post_boundary']}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Report: {REPORT_OUT}")
    print(f"Build wall seconds: {wall_seconds:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
