#!/usr/bin/env python3
"""
Run first-pass extinction sensitivity analysis on PBDB-derived UBY data.

This script tests whether the current extinction/forcing signals are stable
under simple methodological changes:

- bin size: 0.5, 1, 2, 5 Myr
- taxon level: accepted_name, genus, family
- disappearance window: 1, 2.5, 5 Myr

Inputs:
- data/processed/pbdb_animalia_phanerozoic_uby.csv
- data/processed/uby_forcing_events.csv

Outputs:
- data/processed/extinction_sensitivity.sqlite
- data/processed/extinction_sensitivity_summary.csv
- data/processed/extinction_sensitivity_report.json

Scientific boundary:
This is a first robustness screen.  It uses range-through diversity and
representative midpoint ranges.  It is not yet Monte Carlo interval propagation
or sampling-standardized macroevolutionary inference.
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
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import GENERATED_BY, UBY_SPEC_VERSION

PROCESSED_DIR = ROOT / "data" / "processed"
PBDB_UBY_CSV = PROCESSED_DIR / "pbdb_animalia_phanerozoic_uby.csv"
FORCING_CSV = PROCESSED_DIR / "uby_forcing_events.csv"

SQLITE_OUT = PROCESSED_DIR / "extinction_sensitivity.sqlite"
SUMMARY_CSV_OUT = PROCESSED_DIR / "extinction_sensitivity_summary.csv"
REPORT_OUT = PROCESSED_DIR / "extinction_sensitivity_report.json"

MODEL_BASE_UBY = Decimal("13787000000")
MILLION = Decimal("1000000")

BIN_SIZES_MA = (Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("5"))
TAXON_LEVELS = ("accepted_name", "genus", "family")
DISAPPEARANCE_WINDOWS_MA = (Decimal("1"), Decimal("2.5"), Decimal("5"))
RECOVERY_BASELINE_WINDOW_MA = Decimal("10")
RECOVERY_THRESHOLD_FRACTION = Decimal("0.8")
FORCING_WINDOW_YEARS = Decimal("5000000")


@dataclass(frozen=True)
class ReferenceMassExtinction:
    event_name: str
    short_name: str
    ma_bp: str
    uncertainty_ma: str

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
    ReferenceMassExtinction("End-Ordovician mass extinction", "End-Ordovician", "443.8", "1.5"),
    ReferenceMassExtinction("Late Devonian Kellwasser extinction pulse", "Kellwasser", "372.2", "1.6"),
    ReferenceMassExtinction("Late Devonian Hangenberg extinction pulse", "Hangenberg", "358.9", "0.4"),
    ReferenceMassExtinction("End-Permian mass extinction", "End-Permian", "251.902", "0.024"),
    ReferenceMassExtinction("End-Triassic mass extinction", "End-Triassic", "201.36", "0.17"),
    ReferenceMassExtinction("End-Cretaceous mass extinction", "K-Pg", "66.043", "0.011"),
)


@dataclass
class TaxonAccumulator:
    taxon_name: str
    first_ma: Decimal
    last_ma: Decimal
    occurrence_count: int = 0

    def update(self, midpoint_ma: Decimal) -> None:
        if midpoint_ma > self.first_ma:
            self.first_ma = midpoint_ma
        if midpoint_ma < self.last_ma:
            self.last_ma = midpoint_ma
        self.occurrence_count += 1


@dataclass(frozen=True)
class TaxonRange:
    taxon_level: str
    taxon_name: str
    first_ma: Decimal
    last_ma: Decimal
    occurrence_count: int


@dataclass(frozen=True)
class ForcingEvent:
    event_name: str
    forcing_category: str
    forcing_subcategory: str
    ma_bp: Decimal
    uncertainty_ma: Decimal

    @property
    def uby_value(self) -> Decimal:
        return MODEL_BASE_UBY - self.ma_bp * MILLION

    @property
    def uncertainty_years(self) -> Decimal:
        return self.uncertainty_ma * MILLION


@dataclass(frozen=True)
class SensitivityResult:
    bin_size_ma: str
    taxon_level: str
    disappearance_window_ma: str
    event_name: str
    event_ma: str
    standing_taxa: int
    first_appearances: int
    last_appearances: int
    extinction_intensity: str
    disappearing_taxa: int
    before_boundary: int
    after_boundary: int
    before_fraction: str
    after_fraction: str
    mean_disappearance_lag_years: str
    recovery_lag_years: str
    recovered_flag: int
    nearest_forcing_event: str
    nearest_forcing_category: str
    nearest_forcing_subcategory: str
    nearest_forcing_lag_years: str
    nearest_forcing_overlap_flag: int
    end_permian_strongest_flag: int
    kpg_impact_synchronous_flag: int
    end_ordovician_sea_level_or_climate_flag: int


def _decimal_or_none(value: str | None) -> Decimal | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _taxon_name(row: dict[str, str], level: str) -> str:
    if level == "accepted_name":
        return str(row.get("accepted_name") or "").strip()
    if level == "genus":
        return str(row.get("genus") or "").strip()
    if level == "family":
        return str(row.get("family") or "").strip()
    raise ValueError(f"Unsupported taxon level: {level}")


def _load_taxon_ranges_by_level() -> tuple[dict[str, list[TaxonRange]], dict[str, int]]:
    accumulators: dict[str, dict[str, TaxonAccumulator]] = {level: {} for level in TAXON_LEVELS}
    raw_rows = 0
    usable_rows = 0
    skipped_rows = 0

    with PBDB_UBY_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            raw_rows += 1
            midpoint_ma = _decimal_or_none(row.get("representative_ma_midpoint"))
            if midpoint_ma is None:
                skipped_rows += 1
                continue

            row_used = False
            for level in TAXON_LEVELS:
                name = _taxon_name(row, level)
                if not name:
                    continue
                if name not in accumulators[level]:
                    accumulators[level][name] = TaxonAccumulator(name, midpoint_ma, midpoint_ma, 0)
                accumulators[level][name].update(midpoint_ma)
                row_used = True

            if row_used:
                usable_rows += 1
            else:
                skipped_rows += 1

    ranges_by_level: dict[str, list[TaxonRange]] = {}
    for level, level_accumulators in accumulators.items():
        ranges_by_level[level] = [
            TaxonRange(
                taxon_level=level,
                taxon_name=acc.taxon_name,
                first_ma=acc.first_ma,
                last_ma=acc.last_ma,
                occurrence_count=acc.occurrence_count,
            )
            for acc in level_accumulators.values()
        ]

    stats = {
        "raw_rows": raw_rows,
        "usable_rows": usable_rows,
        "skipped_rows": skipped_rows,
        "accepted_name_taxa": len(ranges_by_level["accepted_name"]),
        "genus_taxa": len(ranges_by_level["genus"]),
        "family_taxa": len(ranges_by_level["family"]),
    }
    return ranges_by_level, stats


def _load_forcing_events() -> list[ForcingEvent]:
    events: list[ForcingEvent] = []
    with FORCING_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ma_bp = _decimal_or_none(row.get("ma_bp"))
            uncertainty_ma = _decimal_or_none(row.get("uncertainty_ma"))
            if ma_bp is None or uncertainty_ma is None:
                continue
            events.append(
                ForcingEvent(
                    event_name=str(row.get("event_name") or ""),
                    forcing_category=str(row.get("forcing_category") or ""),
                    forcing_subcategory=str(row.get("forcing_subcategory") or ""),
                    ma_bp=ma_bp,
                    uncertainty_ma=uncertainty_ma,
                )
            )
    return events


def _bin_id(ma: Decimal, bin_size_ma: Decimal) -> int:
    return int(ma / bin_size_ma)


def _build_bin_metrics(ranges: list[TaxonRange], bin_size_ma: Decimal) -> dict[int, dict[str, int]]:
    metrics: dict[int, dict[str, int]] = {}

    for item in ranges:
        first_bin = _bin_id(item.first_ma, bin_size_ma)
        last_bin = _bin_id(item.last_ma, bin_size_ma)

        for bin_id in range(last_bin, first_bin + 1):
            metrics.setdefault(bin_id, {"standing": 0, "first": 0, "last": 0})
            metrics[bin_id]["standing"] += 1

        metrics.setdefault(first_bin, {"standing": 0, "first": 0, "last": 0})
        metrics[first_bin]["first"] += 1

        metrics.setdefault(last_bin, {"standing": 0, "first": 0, "last": 0})
        metrics[last_bin]["last"] += 1

    return metrics


def _event_bin_metrics(metrics: dict[int, dict[str, int]], event_ma: Decimal, bin_size_ma: Decimal) -> tuple[int, int, int, Decimal]:
    event_bin = _bin_id(event_ma, bin_size_ma)
    values = metrics.get(event_bin, {"standing": 0, "first": 0, "last": 0})
    standing = values["standing"]
    first = values["first"]
    last = values["last"]
    extinction_intensity = Decimal(last) / Decimal(standing) if standing else Decimal("0")
    return standing, first, last, extinction_intensity


def _disappearance_stats(ranges: list[TaxonRange], event_ma: Decimal, window_ma: Decimal) -> tuple[int, int, int, Decimal]:
    young = event_ma - window_ma
    old = event_ma + window_ma

    lags: list[Decimal] = []
    before = 0
    after = 0

    for item in ranges:
        if not (young <= item.last_ma <= old):
            continue

        lag_years = (event_ma - item.last_ma) * MILLION
        lags.append(lag_years)

        if lag_years < 0:
            before += 1
        elif lag_years > 0:
            after += 1

    mean_lag = sum(lags, Decimal("0")) / Decimal(len(lags)) if lags else Decimal("0")
    return len(lags), before, after, mean_lag


def _recovery_lag(metrics: dict[int, dict[str, int]], event_ma: Decimal, bin_size_ma: Decimal) -> tuple[Decimal, int]:
    baseline_values: list[int] = []
    baseline_start = event_ma
    baseline_end = event_ma + RECOVERY_BASELINE_WINDOW_MA

    for bin_id, values in metrics.items():
        mid_ma = (Decimal(bin_id) + Decimal("0.5")) * bin_size_ma
        if baseline_start < mid_ma <= baseline_end and values["standing"] > 0:
            baseline_values.append(values["standing"])

    if not baseline_values:
        return Decimal("0"), 0

    threshold = Decimal(str(mean(baseline_values))) * RECOVERY_THRESHOLD_FRACTION

    post_bins: list[tuple[Decimal, int]] = []
    for bin_id, values in metrics.items():
        mid_ma = (Decimal(bin_id) + Decimal("0.5")) * bin_size_ma
        if mid_ma < event_ma:
            post_bins.append((mid_ma, values["standing"]))

    post_bins.sort(key=lambda pair: pair[0], reverse=True)
    for mid_ma, standing in post_bins:
        if Decimal(standing) >= threshold:
            return (event_ma - mid_ma) * MILLION, 1

    return Decimal("0"), 0


def _nearest_forcing(event: ReferenceMassExtinction, forcing_events: list[ForcingEvent]) -> tuple[str, str, str, Decimal, int]:
    best: tuple[str, str, str, Decimal, int] | None = None
    event_uby = event.uby_value
    event_uncertainty_years = event.uncertainty_decimal * MILLION

    for forcing in forcing_events:
        lag_years = event_uby - forcing.uby_value
        abs_lag = abs(lag_years)
        if abs_lag > FORCING_WINDOW_YEARS:
            continue

        overlap = int(abs_lag <= event_uncertainty_years + forcing.uncertainty_years)
        candidate = (
            forcing.event_name,
            forcing.forcing_category,
            forcing.forcing_subcategory,
            lag_years,
            overlap,
        )
        if best is None or abs(candidate[3]) < abs(best[3]):
            best = candidate

    if best is None:
        return "", "", "", Decimal("0"), 0
    return best


def _compute_results(ranges_by_level: dict[str, list[TaxonRange]], forcing_events: list[ForcingEvent]) -> list[SensitivityResult]:
    results: list[SensitivityResult] = []

    for taxon_level in TAXON_LEVELS:
        ranges = ranges_by_level[taxon_level]

        for bin_size_ma in BIN_SIZES_MA:
            metrics = _build_bin_metrics(ranges, bin_size_ma)
            base_by_event: dict[str, dict[str, object]] = {}

            for event in REFERENCE_MASS_EXTINCTIONS:
                standing, first, last, intensity = _event_bin_metrics(metrics, event.ma_decimal, bin_size_ma)
                recovery_lag_years, recovered_flag = _recovery_lag(metrics, event.ma_decimal, bin_size_ma)
                nearest = _nearest_forcing(event, forcing_events)
                base_by_event[event.event_name] = {
                    "standing": standing,
                    "first": first,
                    "last": last,
                    "intensity": intensity,
                    "recovery_lag_years": recovery_lag_years,
                    "recovered_flag": recovered_flag,
                    "nearest": nearest,
                }

            strongest_event = max(
                REFERENCE_MASS_EXTINCTIONS,
                key=lambda event: Decimal(str(base_by_event[event.event_name]["intensity"])),
            ).event_name

            for window_ma in DISAPPEARANCE_WINDOWS_MA:
                for event in REFERENCE_MASS_EXTINCTIONS:
                    disappearing, before, after, mean_lag = _disappearance_stats(ranges, event.ma_decimal, window_ma)
                    base = base_by_event[event.event_name]
                    nearest_name, nearest_category, nearest_subcategory, nearest_lag, nearest_overlap = base["nearest"]  # type: ignore[misc]

                    before_fraction = Decimal(before) / Decimal(disappearing) if disappearing else Decimal("0")
                    after_fraction = Decimal(after) / Decimal(disappearing) if disappearing else Decimal("0")

                    results.append(
                        SensitivityResult(
                            bin_size_ma=str(bin_size_ma),
                            taxon_level=taxon_level,
                            disappearance_window_ma=str(window_ma),
                            event_name=event.event_name,
                            event_ma=str(event.ma_decimal),
                            standing_taxa=int(base["standing"]),
                            first_appearances=int(base["first"]),
                            last_appearances=int(base["last"]),
                            extinction_intensity=str(base["intensity"]),
                            disappearing_taxa=disappearing,
                            before_boundary=before,
                            after_boundary=after,
                            before_fraction=str(before_fraction),
                            after_fraction=str(after_fraction),
                            mean_disappearance_lag_years=str(mean_lag),
                            recovery_lag_years=str(base["recovery_lag_years"]),
                            recovered_flag=int(base["recovered_flag"]),
                            nearest_forcing_event=nearest_name,
                            nearest_forcing_category=nearest_category,
                            nearest_forcing_subcategory=nearest_subcategory,
                            nearest_forcing_lag_years=str(nearest_lag),
                            nearest_forcing_overlap_flag=nearest_overlap,
                            end_permian_strongest_flag=int(strongest_event == "End-Permian mass extinction"),
                            kpg_impact_synchronous_flag=int(
                                event.event_name == "End-Cretaceous mass extinction"
                                and nearest_category == "impact"
                                and abs(nearest_lag) <= event.uncertainty_decimal * MILLION
                            ),
                            end_ordovician_sea_level_or_climate_flag=int(
                                event.event_name == "End-Ordovician mass extinction"
                                and nearest_category in {"sea_level", "climate"}
                            ),
                        )
                    )

    return results


def _write_summary_csv(results: list[SensitivityResult]) -> None:
    with SUMMARY_CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(SensitivityResult.__dataclass_fields__))
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def _write_sqlite(results: list[SensitivityResult]) -> None:
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            """
            CREATE TABLE extinction_sensitivity_summary (
                bin_size_ma TEXT NOT NULL,
                taxon_level TEXT NOT NULL,
                disappearance_window_ma TEXT NOT NULL,
                event_name TEXT NOT NULL,
                event_ma TEXT NOT NULL,
                standing_taxa INTEGER NOT NULL,
                first_appearances INTEGER NOT NULL,
                last_appearances INTEGER NOT NULL,
                extinction_intensity TEXT NOT NULL,
                disappearing_taxa INTEGER NOT NULL,
                before_boundary INTEGER NOT NULL,
                after_boundary INTEGER NOT NULL,
                before_fraction TEXT NOT NULL,
                after_fraction TEXT NOT NULL,
                mean_disappearance_lag_years TEXT NOT NULL,
                recovery_lag_years TEXT NOT NULL,
                recovered_flag INTEGER NOT NULL,
                nearest_forcing_event TEXT,
                nearest_forcing_category TEXT,
                nearest_forcing_subcategory TEXT,
                nearest_forcing_lag_years TEXT,
                nearest_forcing_overlap_flag INTEGER NOT NULL,
                end_permian_strongest_flag INTEGER NOT NULL,
                kpg_impact_synchronous_flag INTEGER NOT NULL,
                end_ordovician_sea_level_or_climate_flag INTEGER NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO extinction_sensitivity_summary VALUES (
                :bin_size_ma,
                :taxon_level,
                :disappearance_window_ma,
                :event_name,
                :event_ma,
                :standing_taxa,
                :first_appearances,
                :last_appearances,
                :extinction_intensity,
                :disappearing_taxa,
                :before_boundary,
                :after_boundary,
                :before_fraction,
                :after_fraction,
                :mean_disappearance_lag_years,
                :recovery_lag_years,
                :recovered_flag,
                :nearest_forcing_event,
                :nearest_forcing_category,
                :nearest_forcing_subcategory,
                :nearest_forcing_lag_years,
                :nearest_forcing_overlap_flag,
                :end_permian_strongest_flag,
                :kpg_impact_synchronous_flag,
                :end_ordovician_sea_level_or_climate_flag
            )
            """,
            [asdict(result) for result in results],
        )

        conn.execute("CREATE INDEX idx_sensitivity_event ON extinction_sensitivity_summary (event_name)")
        conn.execute("CREATE INDEX idx_sensitivity_params ON extinction_sensitivity_summary (bin_size_ma, taxon_level, disappearance_window_ma)")
        conn.execute("CREATE INDEX idx_sensitivity_intensity ON extinction_sensitivity_summary (extinction_intensity)")
        conn.execute("DROP VIEW IF EXISTS sensitivity_event_stability")
        conn.execute(
            """
            CREATE VIEW sensitivity_event_stability AS
            SELECT
                event_name,
                COUNT(*) AS parameter_cases,
                AVG(CAST(extinction_intensity AS REAL)) AS mean_extinction_intensity,
                AVG(disappearing_taxa) AS mean_disappearing_taxa,
                AVG(CAST(before_fraction AS REAL)) AS mean_before_fraction,
                AVG(CAST(after_fraction AS REAL)) AS mean_after_fraction,
                AVG(CAST(recovery_lag_years AS REAL)) AS mean_recovery_lag_years,
                SUM(kpg_impact_synchronous_flag) AS kpg_impact_synchronous_cases,
                SUM(end_ordovician_sea_level_or_climate_flag) AS end_ordovician_sea_level_or_climate_cases
            FROM extinction_sensitivity_summary
            GROUP BY event_name
            ORDER BY mean_extinction_intensity DESC
            """
        )


def _stability_report(results: list[SensitivityResult], stats: dict[str, int], forcing_count: int, wall_seconds: float) -> dict[str, object]:
    cases = len({(r.bin_size_ma, r.taxon_level, r.disappearance_window_ma) for r in results})

    end_permian_cases = [r for r in results if r.event_name == "End-Permian mass extinction"]
    kpg_cases = [r for r in results if r.event_name == "End-Cretaceous mass extinction"]
    ord_cases = [r for r in results if r.event_name == "End-Ordovician mass extinction"]

    strongest_cases = sum(1 for r in end_permian_cases if r.end_permian_strongest_flag)
    kpg_impact_cases = sum(1 for r in kpg_cases if r.kpg_impact_synchronous_flag)
    ord_forcing_cases = sum(1 for r in ord_cases if r.end_ordovician_sea_level_or_climate_flag)

    before_after_by_event: dict[str, dict[str, float]] = {}
    recovery_by_event: dict[str, float] = {}
    intensity_by_event: dict[str, float] = {}

    for event in REFERENCE_MASS_EXTINCTIONS:
        event_results = [r for r in results if r.event_name == event.event_name]
        before_after_by_event[event.event_name] = {
            "mean_before_fraction": mean(float(r.before_fraction) for r in event_results),
            "mean_after_fraction": mean(float(r.after_fraction) for r in event_results),
            "before_dominant_cases": sum(1 for r in event_results if float(r.before_fraction) > float(r.after_fraction)),
            "after_dominant_cases": sum(1 for r in event_results if float(r.after_fraction) > float(r.before_fraction)),
            "total_cases": len(event_results),
        }
        recovery_by_event[event.event_name] = mean(float(r.recovery_lag_years) for r in event_results)
        intensity_by_event[event.event_name] = mean(float(r.extinction_intensity) for r in event_results)

    recovery_rank = sorted(recovery_by_event.items(), key=lambda item: item[1], reverse=True)
    intensity_rank = sorted(intensity_by_event.items(), key=lambda item: item[1], reverse=True)

    return {
        "database": "UBY extinction sensitivity analysis",
        "description": "First-pass robustness analysis for PBDB-derived extinction dynamics and forcing lead-lag signals.",
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "inputs": {
            "pbdb_uby_csv": str(PBDB_UBY_CSV.as_posix()),
            "forcing_csv": str(FORCING_CSV.as_posix()),
        },
        "outputs": {
            "sqlite": str(SQLITE_OUT.as_posix()),
            "summary_csv": str(SUMMARY_CSV_OUT.as_posix()),
            "report": str(REPORT_OUT.as_posix()),
        },
        "parameters": {
            "bin_sizes_ma": [str(value) for value in BIN_SIZES_MA],
            "taxon_levels": list(TAXON_LEVELS),
            "disappearance_windows_ma": [str(value) for value in DISAPPEARANCE_WINDOWS_MA],
            "parameter_cases": cases,
        },
        "counts": {
            **stats,
            "forcing_events": forcing_count,
            "summary_rows": len(results),
        },
        "key_stability_tests": {
            "end_permian_strongest_cases": strongest_cases,
            "end_permian_total_cases": len(end_permian_cases),
            "end_permian_strongest_fraction": strongest_cases / len(end_permian_cases) if end_permian_cases else 0,
            "kpg_impact_synchronous_cases": kpg_impact_cases,
            "kpg_total_cases": len(kpg_cases),
            "kpg_impact_synchronous_fraction": kpg_impact_cases / len(kpg_cases) if kpg_cases else 0,
            "end_ordovician_sea_level_or_climate_cases": ord_forcing_cases,
            "end_ordovician_total_cases": len(ord_cases),
            "end_ordovician_sea_level_or_climate_fraction": ord_forcing_cases / len(ord_cases) if ord_cases else 0,
        },
        "before_after_stability_by_event": before_after_by_event,
        "mean_recovery_lag_rank_years": recovery_rank,
        "mean_extinction_intensity_rank": intensity_rank,
        "research_status": "sensitivity_first_pass_not_sampling_standardized",
        "claim_boundary": [
            "This analysis tests robustness over bin size, taxon level, and disappearance window.",
            "It does not yet perform interval Monte Carlo sampling, shareholder quorum subsampling, or PyRate-style preservation modeling.",
            "Stable signals should be treated as candidates for deeper statistical testing, not final claims.",
        ],
        "build_performance": {
            "wall_seconds": wall_seconds,
            "pbdb_rows_per_second": stats["raw_rows"] / wall_seconds if wall_seconds else 0,
            "summary_rows_per_second": len(results) / wall_seconds if wall_seconds else 0,
        },
    }


def main() -> int:
    start = time.perf_counter()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    ranges_by_level, stats = _load_taxon_ranges_by_level()
    forcing_events = _load_forcing_events()
    results = _compute_results(ranges_by_level, forcing_events)

    _write_summary_csv(results)
    _write_sqlite(results)

    wall_seconds = time.perf_counter() - start
    report = _stability_report(results, stats, len(forcing_events), wall_seconds)
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    key = report["key_stability_tests"]
    print(f"PBDB rows scanned: {stats['raw_rows']}")
    print(f"Accepted-name taxa: {stats['accepted_name_taxa']}")
    print(f"Genus taxa: {stats['genus_taxa']}")
    print(f"Family taxa: {stats['family_taxa']}")
    print(f"Forcing events: {len(forcing_events)}")
    print(f"Sensitivity rows: {len(results)}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Summary CSV: {SUMMARY_CSV_OUT}")
    print(f"Report: {REPORT_OUT}")
    print(f"End-Permian strongest fraction: {key['end_permian_strongest_fraction']}")
    print(f"K-Pg impact synchronous fraction: {key['kpg_impact_synchronous_fraction']}")
    print(f"End-Ordovician sea-level/climate fraction: {key['end_ordovician_sea_level_or_climate_fraction']}")
    print(f"Build wall seconds: {wall_seconds:.6f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
