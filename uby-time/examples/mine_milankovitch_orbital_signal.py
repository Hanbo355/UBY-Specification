"""Cross-domain signal with REAL physical causation: Milankovitch orbital forcing
of Pleistocene climate, mined from authoritative downloaded data on the UBY axis.

Unlike the "cross-scale precision law" (which was a near-tautology), this targets
a genuine, falsifiable cross-domain coupling:

    ASTRONOMY (Earth's orbital geometry: eccentricity ~100 kyr, obliquity ~41 kyr,
    precession ~23/19 kyr)  -->  drives  -->  GEOLOGY/PALEOCLIMATE (global ice
    volume recorded as benthic d18O).

This is the Hays, Imbrie & Shackleton (1976) "Pacemaker of the Ice Ages" result.
We do NOT claim a new discovery; we test whether downloading an authoritative
external dataset, ingesting it on the UBY axis, and running a spectral analysis
RECOVERS the known orbital periods -- a real, reproducible cross-domain signal
(as opposed to the spurious precision-scaling tautology).

Data
----
LR04 benthic d18O stack (Lisiecki & Raymo 2005), 0-5.32 Ma, downloaded to
data/raw/external/LR04stack.txt. Native unit: ka before present. We annotate
each sample with its UBY value (years from the Big Bang) to place it in the
unified framework, then analyse the well-resolved 0-1000 ka and 0-2000 ka
windows where orbital pacing is strongest and the record is evenly sampled.

Method
------
1. Parse LR04 (skip header), resample to an even 1-kyr grid by linear
   interpolation, linearly detrend, apply a Hann window.
2. Compute the power spectrum via FFT.
3. Identify spectral peaks and report their periods (kyr).
4. Check the power at the canonical Milankovitch periods and whether the
   strongest peaks coincide with them.

Research status: reproduction_of_known_result_via_uby_ingestion.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    print("numpy is required for this example.")
    sys.exit(1)

ANCHOR_UBY = 13787002026.0

# Canonical Milankovitch periods (kyr) for cross-checking only.
MILANKOVITCH = {
    "eccentricity_long": 405.0,
    "eccentricity_short": 100.0,
    "obliquity": 41.0,
    "precession_1": 23.0,
    "precession_2": 19.0,
}


def find_lr04() -> Path:
    here = Path(__file__).resolve().parent.parent
    return here / "data" / "raw" / "external" / "LR04stack.txt"


def parse_lr04(path: Path):
    """Return (time_ka, d18o) arrays, sorted by increasing age."""
    t, x = [], []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.replace("\t", " ").split()
            if len(parts) < 2:
                continue
            try:
                tk = float(parts[0])
                d = float(parts[1])
            except ValueError:
                continue  # header lines
            t.append(tk)
            x.append(d)
    order = np.argsort(t)
    return np.array(t)[order], np.array(x)[order]


def power_spectrum(time_ka, d18o, t_max_ka, dt=1.0):
    """Resample to even dt grid up to t_max_ka, detrend, window, FFT.

    Returns (periods_kyr, power) for positive frequencies.
    """
    mask = time_ka <= t_max_ka
    t = time_ka[mask]
    x = d18o[mask]
    grid = np.arange(t.min(), t.max() + dt, dt)
    xi = np.interp(grid, t, x)
    # linear detrend
    coef = np.polyfit(grid, xi, 1)
    xi = xi - np.polyval(coef, grid)
    # Hann window
    win = np.hanning(len(xi))
    xw = xi * win
    # FFT
    n = len(xw)
    freq = np.fft.rfftfreq(n, d=dt)  # cycles per kyr
    spec = np.abs(np.fft.rfft(xw)) ** 2
    # drop the zero-frequency bin
    freq = freq[1:]
    spec = spec[1:]
    periods = 1.0 / freq  # kyr
    return periods, spec


def find_peaks(periods, power, min_period=15.0, max_period=500.0, top=8):
    """Local maxima within a period band, sorted by power."""
    band = (periods >= min_period) & (periods <= max_period)
    p = periods[band]
    w = power[band]
    order = np.argsort(p)
    p = p[order]
    w = w[order]
    peaks = []
    for i in range(1, len(w) - 1):
        if w[i] >= w[i - 1] and w[i] >= w[i + 1]:
            peaks.append((float(p[i]), float(w[i])))
    peaks.sort(key=lambda kv: kv[1], reverse=True)
    return peaks[:top]


def nearest_milankovitch(period_kyr):
    best, bestd = None, 1e9
    for name, val in MILANKOVITCH.items():
        d = abs(period_kyr - val)
        if d < bestd:
            bestd = d
            best = (name, val)
    return best[0], best[1], bestd


def main() -> int:
    t0 = time.perf_counter()
    path = find_lr04()
    if not path.exists():
        print(f"Missing LR04 data at {path}; download it first.")
        return 1
    print(f"[1/4] Parsing LR04 stack {path.name} ...", flush=True)
    time_ka, d18o = parse_lr04(path)
    print(f"      samples={len(time_ka)}, span={time_ka.min():.1f}-{time_ka.max():.1f} ka", flush=True)

    windows = {}
    for label, tmax in [("0-1000ka", 1000.0), ("0-2000ka", 2000.0), ("0-5320ka", time_ka.max())]:
        print(f"[2/4] Spectrum for window {label} ...", flush=True)
        periods, power = power_spectrum(time_ka, d18o, tmax)
        peaks = find_peaks(periods, power)
        # power at canonical periods (nearest bin)
        canonical_power = {}
        total_power = float(np.sum(power))
        for name, val in MILANKOVITCH.items():
            idx = int(np.argmin(np.abs(periods - val)))
            canonical_power[name] = {
                "target_period_kyr": val,
                "nearest_resolved_period_kyr": round(float(periods[idx]), 2),
                "power_fraction_pct": round(float(power[idx]) / total_power * 100, 4),
            }
        peak_table = []
        for per, pw in peaks:
            nm, nv, dd = nearest_milankovitch(per)
            peak_table.append({
                "period_kyr": round(per, 2),
                "power_fraction_pct": round(pw / total_power * 100, 4),
                "nearest_milankovitch": nm,
                "nearest_target_kyr": nv,
                "distance_kyr": round(dd, 2),
                "matches_within_15pct": bool(dd <= 0.15 * nv),
            })
        # how many of the dominant peaks land on a Milankovitch band
        matched = sum(1 for r in peak_table if r["matches_within_15pct"])
        windows[label] = {
            "dominant_peaks": peak_table,
            "canonical_period_power": canonical_power,
            "dominant_peaks_matching_milankovitch": f"{matched}/{len(peak_table)}",
        }

    # UBY ingestion demonstration: annotate sample ages on the unified axis.
    uby_min = ANCHOR_UBY - float(time_ka.max()) * 1000.0
    uby_max = ANCHOR_UBY - float(time_ka.min()) * 1000.0
    elapsed = time.perf_counter() - t0

    report = {
        "database": "Milankovitch orbital forcing signal from LR04 on the UBY axis",
        "description": (
            "Spectral analysis of the authoritative LR04 benthic d18O stack, "
            "downloaded externally and ingested on the UBY axis, testing recovery "
            "of astronomical orbital periods (a real astronomy<->paleoclimate "
            "coupling, the Hays-Imbrie-Shackleton 1976 result)."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "inputs": {
            "lr04_stack": str(path),
            "citation": "Lisiecki, L.E. & Raymo, M.E. (2005), Paleoceanography 20, PA1003, doi:10.1029/2004PA001071",
        },
        "uby_ingestion": {
            "samples": len(time_ka),
            "native_unit": "ka before present",
            "uby_value_min": uby_min,
            "uby_value_max": uby_max,
            "note": "Each climate sample is placed on the same UBY axis as cosmological/biological events; here UBY is the common ledger, the science is the orbital coupling.",
        },
        "canonical_milankovitch_periods_kyr": MILANKOVITCH,
        "windows": windows,
        "research_status": "reproduction_of_known_result_via_uby_ingestion",
        "claim_boundary": [
            "This REPRODUCES the well-established Milankovitch result; it is not a new discovery.",
            "The astronomy<->paleoclimate coupling is real and falsifiable, unlike the earlier precision-scaling tautology.",
            "Spectral peaks depend on interpolation, detrending and windowing choices; this is a first-pass periodogram, not a full multitaper/red-noise significance test.",
            "UBY here is the common time ledger for ingestion, not the source of the scientific signal.",
        ],
        "build_performance": {"wall_seconds": elapsed},
    }

    proc = path.resolve().parent.parent.parent / "processed"
    out = proc / "milankovitch_orbital_signal_report.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    # Plot: d18O series + power spectra with Milankovitch markers.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))
        m1 = time_ka <= 2000
        ax1.plot(time_ka[m1], d18o[m1], lw=0.8, color="#1f77b4")
        ax1.invert_yaxis()  # heavier d18O (colder) downward conventionally up
        ax1.set_xlabel("Age (ka before present)")
        ax1.set_ylabel("Benthic \u03b4\u00b9\u2078O (\u2030)  \u2192 colder up")
        ax1.set_title("LR04 benthic \u03b4\u00b9\u2078O (ice volume proxy), 0\u20132000 ka")
        ax1.grid(True, alpha=0.3)

        for label, tmax, color in [("0-1000ka", 1000.0, "#d62728"),
                                   ("0-2000ka", 2000.0, "#2ca02c"),
                                   ("0-5320ka", time_ka.max(), "#9467bd")]:
            periods, power = power_spectrum(time_ka, d18o, tmax)
            band = (periods >= 15) & (periods <= 500)
            ax2.plot(periods[band], power[band] / power[band].max(),
                     lw=1.0, color=color, alpha=0.8, label=label)
        for name, val in MILANKOVITCH.items():
            ax2.axvline(val, color="grey", ls=":", lw=0.8, alpha=0.7)
            ax2.text(val, 1.02, f"{val:.0f}", rotation=0, ha="center",
                     fontsize=8, color="grey")
        ax2.set_xlim(15, 500)
        ax2.set_xscale("log")
        ax2.set_xlabel("Period (kyr)  [log]  \u2014 grey lines = Milankovitch periods")
        ax2.set_ylabel("Normalised power")
        ax2.set_title("Power spectrum: orbital periods recovered from real climate data")
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        fig.tight_layout()
        png = proc / "milankovitch_orbital_signal.png"
        fig.savefig(png, dpi=140)
        plt.close(fig)
        print(f"\nSaved plot -> {png}")
    except Exception as exc:  # pragma: no cover
        print(f"\nPlot skipped ({type(exc).__name__}: {exc})")

    # Console summary.
    print("\n=== MILANKOVITCH ORBITAL SIGNAL (real astronomy<->climate coupling) ===")
    for label, w in windows.items():
        print(f"\n[{label}] dominant peaks vs Milankovitch ({w['dominant_peaks_matching_milankovitch']} matched):")
        for r in w["dominant_peaks"][:6]:
            flag = "MATCH" if r["matches_within_15pct"] else "-----"
            print(f"  [{flag}] period={r['period_kyr']:7.2f} kyr  "
                  f"power={r['power_fraction_pct']:6.3f}%  "
                  f"~ {r['nearest_milankovitch']} ({r['nearest_target_kyr']} kyr, \u0394={r['distance_kyr']})")
    print(f"\nWall time: {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
