#!/usr/bin/env python3
"""Modern CO2 rise rate in 800-kyr historical context.

A NEW cross-scale signal mining on the UBY axis combining THREE ice-core CO2
records with the modern instrumental Mauna Loa record, all on one time axis:

  - EPICA Dome C CO2 composite (Bereiter et al. 2015): 0-800 ka
  - Vostok CO2 (Petit et al. 1999): 0-414 ka
  - NOAA GML Mauna Loa monthly CO2: 1958-2026

The scientific question (genuine, falsifiable, IPCC-relevant):

    The modern atmospheric CO2 rise rate is ~2.4 ppm/yr (decadal mean).
    Is this rate UNPRECEDENTED in the 800 kyr ice-core record?

    Specifically:
      Q1: What is the maximum decadal-mean dCO2/dt in the EPICA + Vostok
          composite over 0-800 ka?
      Q2: Where does the modern rate rank relative to the historical
          distribution of decadal rates?
      Q3: Has the modern CO2 level (420+ ppm) been exceeded at any point
          in the past 800 kyr?

Method
------
1. Load all three records and convert ages to the UBY axis.
2. For the ice-core composite (EPICA + Vostok, with EPICA preferred for
   overlap), resample onto a uniform 100-yr grid.
3. Compute the derivative dCO2/dt (ppm/yr) at each grid point.
4. Compute decadal (10-yr) and centennial (100-yr) running mean rates.
5. Compare the modern Mauna Loa decadal rate to the historical distribution.
6. Test whether the modern rate exceeds the historical 99.9th percentile.

Research status: exploratory_signal_mining_not_final_claim.
UBY role: common time axis enabling direct comparison of modern instrumental
data with deep-time paleoclimate archives.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    print("numpy is required for this example.")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import DEFAULT_ANCHOR_UBY as ANCHOR_UBY

REPORT_OUT = ROOT / "data" / "processed" / "modern_co2_rate_uniqueness_report.json"


def _yr_bp_to_uby(yr_bp: float) -> float:
    return float(ANCHOR_UBY) - yr_bp


def _decimal_year_to_uby(dy: float) -> float:
    return float(ANCHOR_UBY) + (dy - 2026.0)


def parse_epica_co2() -> tuple[np.ndarray, np.ndarray]:
    """EPICA Dome C CO2. Columns: age_yr_bp  co2  stderr."""
    path = ROOT / "data" / "raw" / "external" / "epica_domec_co2_800kyr.txt"
    ages, values = [], []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = line.replace("\t", " ").split()
            if len(parts) < 2:
                continue
            try:
                age_yr = float(parts[0])
                co2 = float(parts[1])
            except ValueError:
                continue
            if age_yr < 0:
                continue
            ages.append(age_yr)
            values.append(co2)
    a = np.array(ages)
    v = np.array(values)
    order = np.argsort(a)
    return a[order], v[order]


def parse_vostok_co2() -> tuple[np.ndarray, np.ndarray]:
    """Vostok ice core CO2. Columns: gas_age_yr  co2_ppmv."""
    path = ROOT / "data" / "raw" / "external" / "vostok_co2.txt"
    in_data = False
    ages, values = [], []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "Gas age" in line and "CO2" in line:
                in_data = True
                continue
            if not in_data:
                continue
            parts = line.replace("\t", " ").split()
            if len(parts) < 2:
                continue
            try:
                age_yr = float(parts[0])
                co2 = float(parts[1])
            except ValueError:
                continue
            if age_yr < 0:
                continue
            ages.append(age_yr)
            values.append(co2)
    a = np.array(ages)
    v = np.array(values)
    order = np.argsort(a)
    return a[order], v[order]


def parse_maunaloa_co2() -> tuple[np.ndarray, np.ndarray]:
    """Mauna Loa monthly CO2. Columns: year month decimal_year co2 interp trend."""
    path = ROOT / "data" / "raw" / "external" / "maunaloa_co2_monthly.txt"
    years, values = [], []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                dy = float(parts[2])
                co2 = float(parts[3])
            except ValueError:
                continue
            if co2 < 0:
                continue
            years.append(dy)
            values.append(co2)
    a = np.array(years)
    v = np.array(values)
    order = np.argsort(a)
    return a[order], v[order]


def merge_ice_core_records() -> tuple[np.ndarray, np.ndarray]:
    """Merge EPICA and Vostok, preferring EPICA for overlap (longer, newer composite).

    Returns (age_yr_bp, co2) on a uniform 100-yr grid from 0 to 800 ka.
    """
    e_age, e_co2 = parse_epica_co2()
    v_age, v_co2 = parse_vostok_co2()
    print(f"[load] EPICA CO2: n={len(e_age):5d}  span={e_age.min():.0f}-{e_age.max():.0f} yr BP")
    print(f"[load] Vostok CO2: n={len(v_age):5d}  span={v_age.min():.0f}-{v_age.max():.0f} yr BP")

    # Use EPICA up to its max age, then extend with Vostok where EPICA has no data.
    epoca_max = float(e_age.max())
    v_mask = v_age > epoca_max
    combined_age = np.concatenate([e_age, v_age[v_mask]])
    combined_co2 = np.concatenate([e_co2, v_co2[v_mask]])
    order = np.argsort(combined_age)
    combined_age = combined_age[order]
    combined_co2 = combined_co2[order]

    # Resample onto uniform 100-yr grid.
    grid = np.arange(0, 800_000 + 100, 100, dtype=float)
    interp = np.interp(grid, combined_age, combined_co2)
    return grid, interp


def compute_rates(age_yr: np.ndarray, co2: np.ndarray, window_yr: float) -> np.ndarray:
    """Compute centered rolling-mean dCO2/dt (ppm/yr) with window of length `window_yr`.

    Each grid step is 100 yr, so window of 10 grid points = 1000 yr (centennial).
    For decadal rate we cannot resolve from a 100-yr grid; use 100-yr window.
    """
    n = len(co2)
    half = int(window_yr / 200)  # window_yr / 2 / grid_step(100)
    if half < 1:
        half = 1
    rates = np.zeros(n)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        if hi - lo < 2:
            rates[i] = 0.0
            continue
        # Linear fit slope (ppm/yr).
        t = age_yr[lo:hi]
        c = co2[lo:hi]
        if len(t) < 2 or np.ptp(t) == 0:
            rates[i] = 0.0
            continue
        slope = float(np.polyfit(t, c, 1)[0])
        rates[i] = slope
    return rates


def main() -> int:
    t0 = time.perf_counter()

    # --- Ice-core composite on UBY axis ---
    print("[1/4] Building ice-core CO2 composite (EPICA + Vostok) ...", flush=True)
    ice_age, ice_co2 = merge_ice_core_records()
    print(f"      composite: n={len(ice_age)}  grid=100 yr  "
          f"span={ice_age.min():.0f}-{ice_age.max():.0f} yr BP", flush=True)

    # --- Modern Mauna Loa on UBY axis ---
    print("[2/4] Loading modern Mauna Loa CO2 ...", flush=True)
    mlo_age, mlo_co2 = parse_maunaloa_co2()
    print(f"      Mauna Loa: n={len(mlo_age)}  span={mlo_age.min():.2f}-{mlo_age.max():.2f} yr",
          flush=True)

    # --- Compute historical rates ---
    print("[3/4] Computing historical CO2 rates (centennial windows) ...", flush=True)
    # 1000-yr (centennial-equivalent) and 5000-yr (millennial) windows.
    cent_rates = compute_rates(ice_age, ice_co2, 1000.0)
    mill_rates = compute_rates(ice_age, ice_co2, 5000.0)

    # Absolute values (positive = rising).
    cent_rising = np.abs(cent_rates)
    mill_rising = np.abs(mill_rates)

    # Historical percentiles of |dCO2/dt|.
    pcts = [50, 90, 95, 99, 99.9]
    cent_percentiles = {f"p{p}": float(np.percentile(cent_rising, p)) for p in pcts}
    mill_percentiles = {f"p{p}": float(np.percentile(mill_rising, p)) for p in pcts}
    max_cent = float(cent_rising.max())
    max_mill = float(mill_rising.max())
    max_cent_age = float(ice_age[int(np.argmax(cent_rising))])
    max_mill_age = float(ice_age[int(np.argmax(mill_rising))])

    print(f"      centennial |dCO2/dt|: max={max_cent:.6f} ppm/yr at {max_cent_age:.0f} yr BP",
          flush=True)
    print(f"      millennial |dCO2/dt|: max={max_mill:.6f} ppm/yr at {max_mill_age:.0f} yr BP",
          flush=True)
    print(f"      centennial p99.9 = {cent_percentiles['p99.9']:.6f} ppm/yr", flush=True)

    # --- Modern rate (decadal mean, last 10 years of Mauna Loa) ---
    print("[4/4] Computing modern decadal CO2 rate ...", flush=True)
    # Last 10 years of Mauna Loa (decimal year >= 2014).
    recent_mask = mlo_age >= (mlo_age.max() - 10.0)
    recent_age = mlo_age[recent_mask]
    recent_co2 = mlo_co2[recent_mask]
    modern_slope = float(np.polyfit(recent_age, recent_co2, 1)[0])  # ppm/yr
    modern_co2_latest = float(mlo_co2[-1])
    modern_year_latest = float(mlo_age[-1])

    # Also compute over the full Mauna Loa record (1958-2024).
    full_slope = float(np.polyfit(mlo_age, mlo_co2, 1)[0])

    print(f"      modern decadal rate (last 10 yr): {modern_slope:.4f} ppm/yr", flush=True)
    print(f"      modern full-record rate (1958-2024): {full_slope:.4f} ppm/yr", flush=True)
    print(f"      latest CO2: {modern_co2_latest:.2f} ppm  (year {modern_year_latest:.2f})",
          flush=True)

    # --- Comparison ---
    # Ratio of modern rate to historical max.
    ratio_to_max_cent = modern_slope / max_cent if max_cent > 0 else float("inf")
    ratio_to_max_mill = modern_slope / max_mill if max_mill > 0 else float("inf")
    ratio_to_p999_cent = modern_slope / cent_percentiles["p99.9"] if cent_percentiles["p99.9"] > 0 else float("inf")

    # Has modern CO2 level been exceeded in past 800 kyr?
    max_historical_co2 = float(ice_co2.max())
    max_historical_co2_age = float(ice_age[int(np.argmax(ice_co2))])
    modern_exceeds_historical = bool(modern_co2_latest > max_historical_co2)
    modern_minus_historical_max = float(modern_co2_latest - max_historical_co2)

    print(f"\n[compare] modern rate / historical centennial max = "
          f"{ratio_to_max_cent:.1f}x", flush=True)
    print(f"[compare] modern rate / historical millennial max = "
          f"{ratio_to_max_mill:.1f}x", flush=True)
    print(f"[compare] modern rate / historical p99.9 = "
          f"{ratio_to_p999_cent:.1f}x", flush=True)
    print(f"[compare] max historical CO2: {max_historical_co2:.2f} ppm "
          f"at {max_historical_co2_age:.0f} yr BP", flush=True)
    print(f"[compare] modern CO2 ({modern_co2_latest:.2f} ppm) exceeds "
          f"historical max: {modern_exceeds_historical}", flush=True)

    elapsed = time.perf_counter() - t0

    # UBY axis metadata.
    uby_now = _decimal_year_to_uby(modern_year_latest)
    uby_800ka = _yr_bp_to_uby(800_000.0)

    report = {
        "database": "Modern CO2 rise rate in 800-kyr historical context (UBY axis)",
        "description": (
            "Three CO2 records (EPICA Dome C composite, Vostok, Mauna Loa) "
            "ingested on one UBY time axis to test whether the modern CO2 rise "
            "rate is unprecedented in the past 800 kyr."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "anchor_uby": float(ANCHOR_UBY),
        "uby_value_range": [uby_800ka, uby_now],
        "data_sources": {
            "ice_core_composite": {
                "EPICA_DomeC": "Bereiter et al. 2015, Geophys. Res. Lett. 42, 542-549",
                "Vostok": "Petit et al. 1999, Nature 399, 429-436",
                "merge_strategy": "EPICA preferred for overlap; Vostok extends beyond EPICA max age",
                "grid_years": 100,
                "span_yr_bp": "0 - 800,000",
            },
            "modern_instrumental": {
                "Mauna_Loa": "NOAA GML, monthly interpolated CO2",
                "span_decimal_year": f"{float(mlo_age.min()):.2f} - {float(mlo_age.max()):.2f}",
            },
        },
        "modern_rate": {
            "decadal_mean_ppm_per_yr": modern_slope,
            "full_record_mean_ppm_per_yr": full_slope,
            "window_years": 10,
            "latest_co2_ppm": modern_co2_latest,
            "latest_year": modern_year_latest,
        },
        "historical_rates": {
            "centennial_window": {
                "window_years": 1000,
                "max_ppm_per_yr": max_cent,
                "max_age_yr_bp": max_cent_age,
                "percentiles_ppm_per_yr": cent_percentiles,
            },
            "millennial_window": {
                "window_years": 5000,
                "max_ppm_per_yr": max_mill,
                "max_age_yr_bp": max_mill_age,
                "percentiles_ppm_per_yr": mill_percentiles,
            },
        },
        "comparison": {
            "modern_to_historical_max_centennial": float(ratio_to_max_cent),
            "modern_to_historical_max_millennial": float(ratio_to_max_mill),
            "modern_to_historical_p999_centennial": float(ratio_to_p999_cent),
            "modern_exceeds_historical_p999": bool(modern_slope > cent_percentiles["p99.9"]),
            "max_historical_co2_ppm": max_historical_co2,
            "max_historical_co2_age_yr_bp": max_historical_co2_age,
            "modern_co2_exceeds_historical_max": modern_exceeds_historical,
            "modern_minus_historical_max_ppm": modern_minus_historical_max,
        },
        "interpretation": {
            "key_findings": [
                f"Modern decadal CO2 rate: {modern_slope:.4f} ppm/yr "
                f"(last 10 years of Mauna Loa).",
                f"Historical max centennial |dCO2/dt|: {max_cent:.6f} ppm/yr "
                f"at {max_cent_age:.0f} yr BP.",
                f"Modern rate is {ratio_to_max_cent:.1f}x the historical centennial max.",
                f"Modern rate is {ratio_to_p999_cent:.1f}x the historical p99.9.",
                f"Modern CO2 ({modern_co2_latest:.2f} ppm) vs historical max "
                f"({max_historical_co2:.2f} ppm at {max_historical_co2_age:.0f} yr BP): "
                f"{'EXCEEDS' if modern_exceeds_historical else 'within range'} "
                f"by {modern_minus_historical_max:+.2f} ppm.",
            ],
            "claim_boundary": [
                "First-pass comparison on a 100-yr ice-core grid; centennial resolution "
                "cannot resolve decadal events in the paleo record.",
                "Ice-core age models have uncertainties of centuries to millennia; "
                "fast CO2 excursions may be smoothed.",
                "Reproduces the well-established IPCC conclusion that the modern CO2 "
                "rise rate and level are unprecedented in the ice-core record; "
                "not a new climate-science discovery.",
                "UBY role: common time axis enabling direct comparison of modern "
                "instrumental data with deep-time paleoclimate archives.",
            ],
        },
        "research_status": "exploratory_signal_mining_not_final_claim",
        "build_performance": {"wall_seconds": round(elapsed, 4)},
    }

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[done] Report: {REPORT_OUT}  (wall={elapsed:.3f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
