"""Mine a new scientific signal: Phanerozoic genus-level diversity and rate spectrum.

This example goes beyond the existing per-event extinction analyses by building a
*global* Phanerozoic picture directly on the unified UBY axis from real PBDB
genus first/last appearance ranges:

  1. Standing genus diversity through time (a Sepkoski-style diversity curve),
     reconstructed in 1-Myr bins from real first/last appearances.
  2. Per-bin origination and extinction proportions (boundary-crosser rates).
  3. Automatic detection of extinction-rate peaks (data-driven, NOT a hardcoded
     list of the "big five"), then cross-checking which detected peaks fall near
     the canonical mass-extinction boundaries.
  4. A first-pass test of the Raup & Sepkoski (1984) ~26 Myr periodicity
     hypothesis via autocorrelation of the extinction-rate series.

All times are handled on the UBY axis (anchor = 13.787 Ga + 2026) so that the
same machinery could, in principle, place these biological events alongside
cosmological / astronomical events on one ruler.

Research status: exploratory_signal_mining_not_final_claim.
This reproduces the data structure and pipeline; publication-grade diversity
work still requires sampling standardization (SQS), interval Monte Carlo, and
preservation modeling.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

# Real canonical mass-extinction boundaries (Ma BP) for *cross-checking only*,
# never used to bias peak detection.
CANONICAL_BOUNDARIES_MA = {
    "End-Ordovician": 443.8,
    "Late Devonian (Frasnian-Famennian)": 372.0,
    "End-Permian": 251.9,
    "End-Triassic": 201.4,
    "End-Cretaceous": 66.0,
}

PHANEROZOIC_BASE_MA = 538.8  # base of Cambrian
BIN_MA = 1.0  # 1-Myr bins


def find_data_file() -> Path:
    here = Path(__file__).resolve().parent.parent
    candidate = here / "data" / "processed" / "pbdb_taxon_ranges.csv"
    if not candidate.exists():
        raise FileNotFoundError(f"Expected PBDB taxon ranges at {candidate}")
    return candidate


def load_genus_ranges(path: Path) -> list[tuple[float, float]]:
    """Return list of (first_ma, last_ma) for genus-rank records within Phanerozoic."""
    ranges: list[tuple[float, float]] = []
    skipped = 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("taxon_rank") != "genus":
                continue
            try:
                first_ma = float(row["first_ma"])  # older
                last_ma = float(row["last_ma"])  # younger
            except (KeyError, ValueError):
                skipped += 1
                continue
            if first_ma < last_ma:
                first_ma, last_ma = last_ma, first_ma
            if first_ma <= 0 or first_ma > PHANEROZOIC_BASE_MA:
                skipped += 1
                continue
            ranges.append((first_ma, last_ma))
    return ranges, skipped


def build_bins() -> list[float]:
    """Bin midpoints (Ma) from base Phanerozoic to present."""
    edges = []
    ma = PHANEROZOIC_BASE_MA
    while ma > 0:
        edges.append(round(ma, 4))
        ma -= BIN_MA
    return edges


def main() -> int:
    t0 = time.perf_counter()
    data_path = find_data_file()
    print(f"[1/5] Loading genus ranges from {data_path.name} ...", flush=True)
    ranges, skipped = load_genus_ranges(data_path)
    print(f"      genus ranges loaded: {len(ranges)} (skipped {skipped})", flush=True)

    bins = build_bins()
    n = len(bins)

    # Per-bin tallies.
    standing = [0] * n           # diversity: genera whose range spans the bin
    originations = [0] * n       # genera whose first_ma falls in this bin
    extinctions = [0] * n        # genera whose last_ma falls in this bin

    print(f"[2/5] Binning {len(ranges)} ranges into {n} x {BIN_MA}-Myr bins ...", flush=True)
    for first_ma, last_ma in ranges:
        # bin index by upper edge: bin i covers (bins[i]-BIN_MA, bins[i]]
        for i, mid in enumerate(bins):
            lo = mid - BIN_MA
            hi = mid
            # standing if range overlaps [lo, hi]
            if first_ma >= lo and last_ma <= hi:
                standing[i] += 1
            # origination bin = where first appearance lands
            if lo < first_ma <= hi:
                originations[i] += 1
            # extinction bin = where last appearance lands
            if lo < last_ma <= hi:
                extinctions[i] += 1

    # Per-bin proportional extinction/origination rates (relative to standing).
    ext_rate = []
    ori_rate = []
    for i in range(n):
        d = standing[i]
        ext_rate.append(extinctions[i] / d if d > 0 else 0.0)
        ori_rate.append(originations[i] / d if d > 0 else 0.0)

    # [3/5] Data-driven peak detection on extinction rate.
    print("[3/5] Detecting extinction-rate peaks (data-driven) ...", flush=True)
    vals = [r for r in ext_rate if r > 0]
    mean_r = sum(vals) / len(vals) if vals else 0.0
    var_r = sum((r - mean_r) ** 2 for r in vals) / len(vals) if vals else 0.0
    std_r = math.sqrt(var_r)
    threshold = mean_r + 2.0 * std_r  # 2-sigma peaks

    peaks = []
    for i in range(1, n - 1):
        if (
            ext_rate[i] >= threshold
            and ext_rate[i] >= ext_rate[i - 1]
            and ext_rate[i] >= ext_rate[i + 1]
            and standing[i] >= 30  # minimum diversity to be meaningful
        ):
            peaks.append((bins[i], ext_rate[i], standing[i], extinctions[i]))
    peaks.sort(key=lambda p: p[1], reverse=True)

    # Cross-check detected peaks against canonical boundaries (+/- 5 Myr).
    cross_checks = {}
    for name, b_ma in CANONICAL_BOUNDARIES_MA.items():
        nearest = None
        best = 1e9
        for (p_ma, p_rate, p_div, p_ext) in peaks:
            d = abs(p_ma - b_ma)
            if d < best:
                best = d
                nearest = (p_ma, p_rate)
        cross_checks[name] = {
            "boundary_ma": b_ma,
            "nearest_detected_peak_ma": nearest[0] if nearest else None,
            "distance_myr": round(best, 2) if nearest else None,
            "recovered_within_5myr": bool(nearest and best <= 5.0),
        }
    recovered = sum(1 for v in cross_checks.values() if v["recovered_within_5myr"])

    # [4/5] Raup-Sepkoski 26-Myr periodicity test via autocorrelation.
    print("[4/5] Testing extinction periodicity (autocorrelation) ...", flush=True)
    # Use the extinction-rate series over a continuous well-sampled window
    # (last 250 Myr, where the Raup-Sepkoski analysis was originally framed).
    series = []
    for i, mid in enumerate(bins):
        if mid <= 250.0 and standing[i] >= 30:
            series.append(ext_rate[i])
    autocorr = {}
    if len(series) > 60:
        s_mean = sum(series) / len(series)
        denom = sum((x - s_mean) ** 2 for x in series)
        for lag in range(10, 41):  # lags 10..40 Myr
            num = sum(
                (series[k] - s_mean) * (series[k - lag] - s_mean)
                for k in range(lag, len(series))
            )
            autocorr[lag] = num / denom if denom > 0 else 0.0
        best_lag = max(autocorr, key=lambda k: autocorr[k])
        periodicity = {
            "series_length_bins": len(series),
            "best_lag_myr": best_lag,
            "best_lag_autocorrelation": round(autocorr[best_lag], 4),
            "autocorr_at_26myr": round(autocorr.get(26, 0.0), 4),
            "raup_sepkoski_26myr_note": (
                "Autocorrelation peak lag is the data-driven dominant spacing; "
                "compare to the historically proposed 26 Myr. A weak/insignificant "
                "peak is itself the modern consensus outcome."
            ),
        }
    else:
        periodicity = {"status": "insufficient_well_sampled_bins"}

    # Diversity curve highlights.
    max_div_i = max(range(n), key=lambda i: standing[i])
    diversity_peak = {
        "bin_mid_ma": bins[max_div_i],
        "standing_genera": standing[max_div_i],
    }

    elapsed = time.perf_counter() - t0

    report = {
        "database": "UBY Phanerozoic genus diversity and rate spectrum",
        "description": (
            "Global Phanerozoic standing diversity, origination/extinction rate "
            "spectrum, data-driven extinction-peak detection, and a first-pass "
            "Raup-Sepkoski 26-Myr periodicity test, all on the unified UBY axis."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "inputs": {"pbdb_taxon_ranges_csv": str(data_path)},
        "parameters": {
            "bin_ma": BIN_MA,
            "phanerozoic_base_ma": PHANEROZOIC_BASE_MA,
            "peak_threshold": "mean + 2*std of nonzero extinction rate",
            "min_standing_diversity_for_peak": 30,
        },
        "counts": {
            "genus_ranges_used": len(ranges),
            "skipped_rows": skipped,
            "bins": n,
            "detected_extinction_peaks": len(peaks),
        },
        "diversity_peak": diversity_peak,
        "extinction_rate_stats": {
            "mean_nonzero": round(mean_r, 5),
            "std_nonzero": round(std_r, 5),
            "peak_threshold_2sigma": round(threshold, 5),
        },
        "top_detected_extinction_peaks": [
            {
                "bin_mid_ma": p[0],
                "extinction_rate": round(p[1], 4),
                "standing_genera": p[2],
                "extinguished_genera": p[3],
            }
            for p in peaks[:12]
        ],
        "canonical_boundary_cross_check": cross_checks,
        "canonical_boundaries_recovered_within_5myr": f"{recovered}/{len(CANONICAL_BOUNDARIES_MA)}",
        "periodicity_test": periodicity,
        "research_status": "exploratory_signal_mining_not_final_claim",
        "claim_boundary": [
            "Diversity and rates are raw (range-through) counts without sampling standardization.",
            "Peak detection uses a simple 2-sigma rule; it is a discovery heuristic, not a significance test.",
            "Periodicity autocorrelation is descriptive; rigorous testing needs spectral analysis with red-noise null models.",
            "Publication-grade work requires SQS subsampling, interval Monte Carlo, and preservation modeling.",
        ],
        "build_performance": {
            "wall_seconds": elapsed,
            "genus_ranges_per_second": len(ranges) / elapsed if elapsed > 0 else None,
        },
    }

    out_dir = data_path.parent
    report_path = out_dir / "phanerozoic_diversity_signal_report.json"
    curve_path = out_dir / "phanerozoic_diversity_curve.csv"

    print(f"[5/5] Writing report -> {report_path.name}, curve -> {curve_path.name}", flush=True)
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    with curve_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([
            "bin_mid_ma", "standing_genera", "originations",
            "extinctions", "extinction_rate", "origination_rate",
        ])
        for i in range(n):
            w.writerow([
                bins[i], standing[i], originations[i],
                extinctions[i], round(ext_rate[i], 6), round(ori_rate[i], 6),
            ])

    # Console summary.
    print("\n=== PHANEROZOIC DIVERSITY SIGNAL SUMMARY ===")
    print(f"Genus ranges used: {len(ranges)}")
    print(f"Diversity peak: {diversity_peak['standing_genera']} genera at {diversity_peak['bin_mid_ma']} Ma")
    print(f"Detected 2-sigma extinction peaks: {len(peaks)}")
    print(f"Canonical mass extinctions recovered within 5 Myr: {recovered}/{len(CANONICAL_BOUNDARIES_MA)}")
    for name, c in cross_checks.items():
        flag = "OK" if c["recovered_within_5myr"] else "--"
        print(f"  [{flag}] {name}: boundary {c['boundary_ma']} Ma, "
              f"nearest peak {c['nearest_detected_peak_ma']} Ma (Δ={c['distance_myr']} Myr)")
    if "best_lag_myr" in periodicity:
        print(f"Periodicity: dominant autocorr lag = {periodicity['best_lag_myr']} Myr "
              f"(r={periodicity['best_lag_autocorrelation']}), "
              f"r@26Myr={periodicity['autocorr_at_26myr']}")
    print(f"Wall time: {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
