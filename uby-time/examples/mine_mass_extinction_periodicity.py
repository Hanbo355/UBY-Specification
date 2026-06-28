#!/usr/bin/env python3
"""Mass extinction periodicity: Rhode & Muller (2005) ~62 Myr hypothesis.

A NEW cross-scale signal mining on the UBY unified timeline database using
the FULL PBDB occurrence + collection data (1.53M records, never before
combined for periodicity analysis in this codebase).

The scientific question (genuine, falsifiable, debated in paleontology):

    Does the Phanerozoic extinction-rate time series show a statistically
    significant periodicity near 62 Myr, as proposed by Rhode & Muller
    (2005) and debated by Smith & McGowan (2005), Melott & Bambach (2010)?

    If the periodicity is real, what is its exact period, amplitude, and
    phase on the UBY axis?

Method
------
1. Query the unified database for all PBDB paleontology events with
   `original_time_unit = 'ma_bp_interval'` and a valid `original_time_value`
   (representative Ma midpoint).
2. Build a 1-Myr resolution extinction-intensity time series on the UBY axis
   by counting fossil-bearing events per bin (occurrences + collections).
3. Apply a Hann window and compute the power spectrum via FFT.
4. Identify dominant periods in the 30-80 Myr band (extinction-periodicity range).
5. Test significance against a red-noise (AR1) null model via Monte Carlo.
6. Report the detected period, power fraction, and significance.

Research status: exploratory_signal_mining_not_final_claim.
UBY role: common time axis enabling cross-dataset combination (occurrences
+ collections together for the first time).
"""

from __future__ import annotations

import json
import sqlite3
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

DB_PATH = ROOT / "data" / "processed" / "uby_unified_timeline.sqlite"
REPORT_OUT = ROOT / "data" / "processed" / "mass_extinction_periodicity_report.json"

PHANEROZOIC_BASE_MA = 538.8  # base of Cambrian
BIN_MA = 1.0  # 1-Myr bins
N_MC = 1000  # Monte Carlo iterations for red-noise significance


def load_event_ma_midpoints() -> np.ndarray:
    """Load Ma midpoints of all PBDB paleontology events from the unified DB."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Unified database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        # Select all paleontology events with ma_bp_interval time unit
        rows = conn.execute(
            """
            SELECT original_time_value, event_subcategory
            FROM uby_events
            WHERE event_category = 'paleontology'
              AND original_time_unit = 'ma_bp_interval'
              AND original_time_value != ''
            """
        ).fetchall()

    midpoints = []
    for value, _subcat in rows:
        try:
            ma = float(value)
        except ValueError:
            continue
        if 0 < ma <= PHANEROZOIC_BASE_MA:
            midpoints.append(ma)
    return np.array(midpoints)


def build_intensity_series(midpoints: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Build a 1-Myr extinction-intensity series (events per bin)."""
    # Bin midpoints from present (0 Ma) to base Phanerozoic (538.8 Ma).
    edges = np.arange(0, PHANEROZOIC_BASE_MA + BIN_MA, BIN_MA)
    # np.histogram: bin i covers [edges[i], edges[i+1]); we want bin midpoints.
    counts, _ = np.histogram(midpoints, bins=edges)
    # Bin midpoints (Ma) aligned so index 0 = youngest bin (near present).
    bin_mid_ma = edges[:-1] + BIN_MA / 2.0
    return bin_mid_ma, counts.astype(float)


def power_spectrum(series: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute Hann-windowed power spectrum. Returns (periods_myr, power)."""
    n = len(series)
    # Detrend linearly.
    t = np.arange(n, dtype=float)
    coeffs = np.polyfit(t, series, 1)
    detrended = series - np.polyval(coeffs, t)
    # Hann window.
    window = np.hanning(n)
    windowed = detrended * window
    spec = np.abs(np.fft.rfft(windowed)) ** 2
    freqs = np.fft.rfftfreq(n, d=BIN_MA)  # cycles per Myr
    # Avoid divide-by-zero at DC.
    periods = np.where(freqs > 0, 1.0 / freqs, np.inf)
    return periods[1:], spec[1:]  # drop DC component


def ar1_red_noise(series: np.ndarray, n_mc: int) -> tuple[np.ndarray, np.ndarray]:
    """Monte Carlo AR(1) red-noise 95% confidence threshold.

    Returns (periods_myr, percentile_95_power).
    """
    n = len(series)
    # Estimate AR(1) coefficient.
    x = series - series.mean()
    if np.sum(x[:-1] ** 2) > 0:
        phi = np.sum(x[:-1] * x[1:]) / np.sum(x[:-1] ** 2)
    else:
        phi = 0.0
    phi = max(-0.99, min(0.99, float(phi)))
    sigma = float(np.sqrt(np.var(x) * (1 - phi ** 2))) if abs(phi) < 1 else float(np.std(x))

    rng = np.random.default_rng(42)
    t = np.arange(n, dtype=float)
    window = np.hanning(n)

    specs = []
    for _ in range(n_mc):
        noise = np.zeros(n)
        noise[0] = rng.normal(0, sigma)
        for i in range(1, n):
            noise[i] = phi * noise[i - 1] + rng.normal(0, sigma)
        noise = noise - noise.mean()
        spec = np.abs(np.fft.rfft(noise * window)) ** 2
        specs.append(spec[1:])  # drop DC

    specs_arr = np.array(specs)
    p95 = np.percentile(specs_arr, 95, axis=0)
    freqs = np.fft.rfftfreq(n, d=BIN_MA)
    periods = np.where(freqs > 0, 1.0 / freqs, np.inf)
    return periods[1:], p95


def detect_peaks(periods: np.ndarray, power: np.ndarray,
                 p95: np.ndarray, band: tuple[float, float]) -> list[dict]:
    """Find peaks within a frequency band that exceed the 95% red-noise threshold."""
    lo, hi = band
    mask = (periods >= lo) & (periods <= hi)
    if not mask.any():
        return []
    p_band = periods[mask]
    power_band = power[mask]
    p95_band = p95[mask]

    peaks = []
    # Local maxima above threshold.
    for i in range(1, len(p_band) - 1):
        if power_band[i] > p95_band[i] and \
           power_band[i] >= power_band[i - 1] and \
           power_band[i] >= power_band[i + 1]:
            peaks.append({
                "period_myr": float(p_band[i]),
                "power": float(power_band[i]),
                "red_noise_95": float(p95_band[i]),
                "power_ratio": float(power_band[i] / p95_band[i]) if p95_band[i] > 0 else 0.0,
            })
    return peaks


def main() -> int:
    t0 = time.perf_counter()

    print("[1/5] Loading PBDB events from unified database ...", flush=True)
    midpoints = load_event_ma_midpoints()
    print(f"      events loaded: {len(midpoints)}", flush=True)
    print(f"      Ma range: {midpoints.min():.2f} - {midpoints.max():.2f}", flush=True)

    print("[2/5] Building 1-Myr extinction-intensity series ...", flush=True)
    bin_mid_ma, intensity = build_intensity_series(midpoints)
    n_bins = len(intensity)
    print(f"      bins: {n_bins}, total events: {int(intensity.sum()):,}", flush=True)
    print(f"      mean events/bin: {intensity.mean():.1f}, "
          f"max: {intensity.max():.0f} at {bin_mid_ma[np.argmax(intensity)]:.1f} Ma", flush=True)

    print("[3/5] Computing power spectrum (Hann + FFT) ...", flush=True)
    periods, power = power_spectrum(intensity)
    print(f"      spectrum length: {len(periods)}", flush=True)
    # Band-averaged power in the canonical periodicity range.
    band_mask = (periods >= 30) & (periods <= 80)
    band_power_frac = float(power[band_mask].sum() / power.sum()) if power.sum() > 0 else 0.0
    print(f"      power fraction in 30-80 Myr band: {band_power_frac:.4f}", flush=True)

    print("[4/5] Estimating AR(1) red-noise 95% threshold "
          f"(Monte Carlo N={N_MC}) ...", flush=True)
    noise_periods, p95 = ar1_red_noise(intensity, N_MC)
    # periods and noise_periods should be aligned; verify.
    assert len(periods) == len(noise_periods), "Spectrum length mismatch"

    print("[5/5] Detecting peaks in 30-80 Myr band ...", flush=True)
    peaks = detect_peaks(periods, power, p95, (30.0, 80.0))

    # Also check the canonical Rhode & Muller ~62 Myr directly.
    target_period = 62.0
    idx_62 = int(np.argmin(np.abs(periods - target_period)))
    power_at_62 = float(power[idx_62])
    p95_at_62 = float(p95[idx_62])
    ratio_at_62 = power_at_62 / p95_at_62 if p95_at_62 > 0 else 0.0
    print(f"      power @ ~62 Myr: {power_at_62:.2f} "
          f"(red-noise 95%: {p95_at_62:.2f}, ratio: {ratio_at_62:.2f})", flush=True)

    # Top 5 strongest peaks anywhere in the 20-100 Myr band.
    broad_mask = (periods >= 20) & (periods <= 100)
    broad_periods = periods[broad_mask]
    broad_power = power[broad_mask]
    broad_p95 = p95[broad_mask]
    top_idx = np.argsort(broad_power)[::-1][:5]
    top_peaks = []
    for i in top_idx:
        top_peaks.append({
            "period_myr": float(broad_periods[i]),
            "power": float(broad_power[i]),
            "red_noise_95": float(broad_p95[i]),
            "above_95pct": bool(broad_power[i] > broad_p95[i]),
            "power_ratio": float(broad_power[i] / broad_p95[i]) if broad_p95[i] > 0 else 0.0,
        })

    elapsed = time.perf_counter() - t0

    # UBY axis metadata.
    uby_at_present = float(ANCHOR_UBY)
    uby_at_base_phanerozoic = float(ANCHOR_UBY) - PHANEROZOIC_BASE_MA * 1e6

    report = {
        "database": "Mass extinction periodicity on the UBY axis",
        "description": (
            "Test of the Rhode & Muller (2005) ~62 Myr mass-extinction "
            "periodicity hypothesis using the full PBDB occurrence + collection "
            "data (1.53M events) from the unified UBY timeline database."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "anchor_uby": uby_at_present,
        "uby_value_range": [uby_at_base_phanerozoic, uby_at_present],
        "data_sources": {
            "primary": "uby_unified_timeline.sqlite (uby_events table)",
            "filter": "event_category='paleontology' AND original_time_unit='ma_bp_interval'",
            "events_used": int(len(midpoints)),
            "datasets_combined": [
                "PBDB occurrence API (Animalia Phanerozoic): 1,348,072 events",
                "PBDB collection API (Animalia Phanerozoic): 180,000 events",
                "PBDB occurrence API (Dinosauria subset): 94 events",
            ],
        },
        "time_series": {
            "bin_size_myr": BIN_MA,
            "n_bins": int(n_bins),
            "phanerozoic_base_ma": PHANEROZOIC_BASE_MA,
            "total_events_binned": int(intensity.sum()),
            "mean_events_per_bin": float(intensity.mean()),
            "max_events_per_bin": float(intensity.max()),
            "max_bin_ma": float(bin_mid_ma[np.argmax(intensity)]),
        },
        "power_spectrum": {
            "method": "Hann-windowed FFT on linearly-detrended series",
            "band_power_fractions": {
                "30_80_myr": float(band_power_frac),
            },
            "canonical_62myr_test": {
                "target_period_myr": target_period,
                "power": power_at_62,
                "red_noise_95pct": p95_at_62,
                "power_ratio": ratio_at_62,
                "significant_at_95pct": bool(power_at_62 > p95_at_62),
            },
            "top_5_peaks_20_100myr": top_peaks,
            "significant_peaks_30_80myr": peaks,
        },
        "red_noise_null": {
            "model": "AR(1) Monte Carlo",
            "iterations": N_MC,
            "percentile": 95,
        },
        "interpretation": {
            "key_findings": [
                f"Combined PBDB events: {len(midpoints):,} (occurrences + collections, "
                f"first time combined in this codebase).",
                f"Power fraction in 30-80 Myr band: {band_power_frac*100:.2f}%.",
                f"At ~62 Myr (Rhode-Muller): power ratio vs red-noise = {ratio_at_62:.2f} "
                f"({'significant' if power_at_62 > p95_at_62 else 'NOT significant'} at 95%).",
                f"Strongest peak in 20-100 Myr band: "
                f"{top_peaks[0]['period_myr']:.2f} Myr "
                f"(power ratio {top_peaks[0]['power_ratio']:.2f}).",
            ],
            "claim_boundary": [
                "First-pass FFT on event-count intensity (not per-taxon extinction rate).",
                "Combines occurrences and collections, which double-count some events; "
                "a cleaner analysis would use only taxon first/last appearances.",
                "AR(1) red noise is a simple null; no spectral smoothing (MTM) applied.",
                "Reproduces the methodology to test Rhode & Muller (2005); not a new "
                "paleontology discovery. The ~62 Myr periodicity remains scientifically debated.",
                "UBY role: unified query of multiple PBDB datasets on one time axis.",
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
