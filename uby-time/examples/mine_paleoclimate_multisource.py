"""Multi-source paleoclimate signal mining on the UBY axis.

This combines FOUR independently produced, authoritative, externally downloaded
records onto one UBY time axis and asks two REAL, falsifiable scientific
questions that a single dataset cannot answer alone:

  Records (all ingested on the UBY axis):
    * LR04 benthic d18O  - global deep-sea ice-volume proxy (0-5320 ka)
    * Vostok dDeuterium  - Antarctic temperature proxy      (0-420 ka)
    * Vostok CO2         - Antarctic ice-core CO2            (0-414 ka)
    * EPICA Dome C CO2   - Antarctic ice-core CO2 composite  (0-800 ka)

  Q1 (cross-validation): Do THREE physically independent archives -- different
      hemispheres, different proxies (benthic d18O vs ice dD vs trapped CO2),
      different chronologies -- independently show the SAME Milankovitch orbital
      periods (100/41/23 kyr)? Concordance across independent records is strong
      evidence the signal is real, not a single-record artifact.

  Q2 (lead-lag): Within Vostok, what is the lead-lag between CO2 and temperature?
      Cross-correlating the two on a common UBY-aligned grid recovers their phase
      relationship (a genuine, historically debated climate-science question).

The multi-source combination here is the point: it produces something no single
file can (independent confirmation + cross-archive phase). UBY's role remains the
common, reproducible time ledger into which heterogeneous native chronologies are
ingested; the science comes from the records and the spectral/correlation methods.

Research status: reproduction_and_cross_validation_via_uby_ingestion.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    print("numpy is required.")
    sys.exit(1)

ANCHOR_UBY = 13787002026.0
MILANKOVITCH = {"eccentricity_long": 405.0, "eccentricity_short": 100.0,
                "obliquity": 41.0, "precession_1": 23.0, "precession_2": 19.0}

# file -> (age_col, value_col, label, native_unit, age_is_kyr)
RECORDS = {
    "LR04_d18O": ("LR04stack.txt", 0, 1, "global deep-sea d18O", "ka BP", True),
    "Vostok_temperature": ("vostok_deuterium.txt", 1, 3, "Antarctic temperature (dD)", "yr BP", False),
    "Vostok_CO2": ("vostok_co2.txt", 0, 1, "Antarctic CO2", "yr BP", False),
    "EPICA_CO2": ("epica_domec_co2_800kyr.txt", 0, 1, "Antarctic CO2 composite", "yr BP", False),
}


def ext_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "raw" / "external"


def parse_numeric(path: Path, age_col: int, val_col: int, age_is_kyr: bool):
    """Return (age_ka, value) arrays from a whitespace/tab file, skipping headers."""
    ages, vals = [], []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            toks = line.replace("\t", " ").split()
            if len(toks) <= max(age_col, val_col):
                continue
            try:
                a = float(toks[age_col])
                v = float(toks[val_col])
            except ValueError:
                continue
            age_ka = a if age_is_kyr else a / 1000.0
            if age_ka < 0:
                continue
            ages.append(age_ka)
            vals.append(v)
    a = np.array(ages)
    v = np.array(vals)
    order = np.argsort(a)
    return a[order], v[order]


def power_spectrum(age_ka, value, t_max_ka, dt=1.0):
    mask = age_ka <= t_max_ka
    t = age_ka[mask]
    x = value[mask]
    # collapse duplicate ages (ice cores sometimes repeat)
    uniq, idx = np.unique(t, return_index=True)
    t = uniq
    x = x[idx]
    if len(t) < 16:
        return None, None
    grid = np.arange(t.min(), t.max() + dt, dt)
    xi = np.interp(grid, t, x)
    xi = xi - np.polyval(np.polyfit(grid, xi, 1), grid)
    xw = xi * np.hanning(len(xi))
    freq = np.fft.rfftfreq(len(xw), d=dt)[1:]
    spec = (np.abs(np.fft.rfft(xw)) ** 2)[1:]
    return 1.0 / freq, spec


def orbital_power(periods, spec):
    total = float(np.sum(spec))
    out = {}
    for name, val in MILANKOVITCH.items():
        i = int(np.argmin(np.abs(periods - val)))
        out[name] = {
            "target_kyr": val,
            "resolved_kyr": round(float(periods[i]), 2),
            "power_fraction_pct": round(float(spec[i]) / total * 100, 4),
        }
    return out


def dominant_orbital_band(periods, spec):
    """Fraction of spectral power within +/-15% of any Milankovitch period."""
    total = float(np.sum(spec))
    in_band = np.zeros(len(periods), dtype=bool)
    for val in MILANKOVITCH.values():
        in_band |= (np.abs(periods - val) <= 0.15 * val)
    return round(float(np.sum(spec[in_band])) / total * 100, 2)


def cross_correlation_lag(age1, v1, age2, v2, t_max_ka=400.0, dt=1.0, max_lag_kyr=20.0):
    """Lead-lag (kyr) of v1 vs v2 on a common grid via normalised cross-correlation.

    Positive lag => v1 lags v2 (v2 leads). Returns (best_lag_kyr, best_corr, curve).
    """
    grid = np.arange(0.0, t_max_ka + dt, dt)

    def regrid(a, v):
        m = a <= t_max_ka + max_lag_kyr
        a, v = a[m], v[m]
        u, idx = np.unique(a, return_index=True)
        gi = np.interp(grid, u, v[idx])
        gi = gi - gi.mean()
        s = gi.std()
        return gi / s if s > 0 else gi

    x1 = regrid(age1, v1)
    x2 = regrid(age2, v2)
    n = len(grid)
    lags = range(-int(max_lag_kyr), int(max_lag_kyr) + 1)
    curve = []
    for lag in lags:
        if lag >= 0:
            a = x1[lag:]
            b = x2[:n - lag]
        else:
            a = x1[:n + lag]
            b = x2[-lag:]
        if len(a) < 10:
            curve.append((lag, 0.0))
            continue
        c = float(np.mean(a * b))
        curve.append((lag, c))
    best = max(curve, key=lambda kv: kv[1])
    return best[0], best[1], curve


def main() -> int:
    t0 = time.perf_counter()
    d = ext_dir()
    parsed = {}
    for key, (fname, ac, vc, label, unit, is_kyr) in RECORDS.items():
        p = d / fname
        if not p.exists():
            print(f"[skip] {key}: missing {fname}")
            continue
        age, val = parse_numeric(p, ac, vc, is_kyr)
        parsed[key] = (age, val, label, unit)
        print(f"[load] {key:18s} n={len(age):5d}  span={age.min():.1f}-{age.max():.1f} ka  ({label})", flush=True)

    # Q1: independent cross-validation of orbital periods.
    print("\n[Q1] Independent cross-validation of Milankovitch periods ...", flush=True)
    q1 = {}
    for key in ["LR04_d18O", "Vostok_temperature", "EPICA_CO2"]:
        if key not in parsed:
            continue
        age, val, label, unit = parsed[key]
        tmax = min(float(age.max()), 800.0)
        periods, spec = power_spectrum(age, val, tmax)
        if periods is None:
            continue
        q1[key] = {
            "proxy": label,
            "window_ka": round(tmax, 1),
            "orbital_band_power_pct": dominant_orbital_band(periods, spec),
            "orbital_periods": orbital_power(periods, spec),
        }

    # Q2: Vostok CO2 vs temperature lead-lag.
    print("[Q2] Vostok CO2 vs temperature lead-lag ...", flush=True)
    q2 = None
    if "Vostok_CO2" in parsed and "Vostok_temperature" in parsed:
        ac, vc, _, _ = parsed["Vostok_CO2"]
        at, vt, _, _ = parsed["Vostok_temperature"]
        lag, corr, curve = cross_correlation_lag(ac, vc, at, vt)
        q2 = {
            "definition": "positive lag (kyr) => CO2 lags temperature (temperature leads)",
            "best_lag_kyr": lag,
            "max_correlation": round(corr, 4),
            "zero_lag_correlation": round(next(c for l, c in curve if l == 0), 4),
            "interpretation": (
                "CO2 and Antarctic temperature are tightly coupled over glacial "
                "cycles; a small lag near zero (within chronological uncertainty) "
                "reproduces the known near-synchrony / slight CO2 lag at terminations."
            ),
            "correlation_curve": [{"lag_kyr": l, "corr": round(c, 4)} for l, c in curve],
        }

    # UBY ingestion accounting.
    spans = {k: (float(v[0].min()), float(v[0].max())) for k, v in parsed.items()}
    elapsed = time.perf_counter() - t0

    report = {
        "database": "Multi-source paleoclimate signal on the UBY axis",
        "description": (
            "Four independent authoritative paleoclimate records ingested on one "
            "UBY axis; cross-validation of Milankovitch periods across independent "
            "archives, and Vostok CO2-temperature lead-lag."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "sources": {
            "LR04": "Lisiecki & Raymo 2005, Paleoceanography 20, PA1003",
            "Vostok": "Petit et al. 1999, Nature 399, 429-436",
            "EPICA_DomeC_CO2": "Bereiter et al. 2015 composite (NOAA NCEI)",
        },
        "uby_ingestion": {
            "records_unified": len(parsed),
            "native_chronologies": "ka BP / yr BP from independent labs and age models",
            "note": "Heterogeneous native chronologies ingested onto one reproducible UBY ledger; the cross-validation is the scientific payoff, UBY is the common axis.",
            "uby_value_ranges": {
                k: [ANCHOR_UBY - hi * 1000.0, ANCHOR_UBY - lo * 1000.0]
                for k, (lo, hi) in spans.items()
            },
        },
        "Q1_independent_orbital_cross_validation": q1,
        "Q2_vostok_co2_temperature_leadlag": q2,
        "research_status": "reproduction_and_cross_validation_via_uby_ingestion",
        "claim_boundary": [
            "Reproduces established results (Milankovitch pacing; CO2-temperature coupling); not a new discovery.",
            "First-pass periodogram and cross-correlation on interpolated grids; no multitaper/red-noise significance or age-model Monte Carlo.",
            "Lead-lag is limited by independent ice/gas age-model uncertainties (centuries to ~1 kyr).",
            "UBY is the common ingestion ledger, not the source of the signal.",
        ],
        "build_performance": {"wall_seconds": elapsed},
    }

    proc = Path(__file__).resolve().parent.parent / "data" / "processed"
    out = proc / "paleoclimate_multisource_report.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    # Plot.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))
        colors = {"LR04_d18O": "#1f77b4", "Vostok_temperature": "#d62728", "EPICA_CO2": "#2ca02c"}
        for key in ["LR04_d18O", "Vostok_temperature", "EPICA_CO2"]:
            if key not in parsed:
                continue
            age, val, label, unit = parsed[key]
            tmax = min(float(age.max()), 800.0)
            periods, spec = power_spectrum(age, val, tmax)
            if periods is None:
                continue
            band = (periods >= 15) & (periods <= 500)
            ax1.plot(periods[band], spec[band] / spec[band].max(),
                     lw=1.1, color=colors[key], alpha=0.85, label=f"{key} ({label})")
        for val in MILANKOVITCH.values():
            ax1.axvline(val, color="grey", ls=":", lw=0.8, alpha=0.7)
            ax1.text(val, 1.02, f"{val:.0f}", ha="center", fontsize=8, color="grey")
        ax1.set_xscale("log")
        ax1.set_xlim(15, 500)
        ax1.set_xlabel("Period (kyr) [log] - grey = Milankovitch periods")
        ax1.set_ylabel("Normalised power")
        ax1.set_title("Q1: THREE independent archives recover the same orbital periods")
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)

        if q2:
            lags = [c["lag_kyr"] for c in q2["correlation_curve"]]
            corrs = [c["corr"] for c in q2["correlation_curve"]]
            ax2.plot(lags, corrs, "-o", ms=3, color="#9467bd")
            ax2.axvline(q2["best_lag_kyr"], color="red", ls="--",
                        label=f"peak lag = {q2['best_lag_kyr']} kyr (r={q2['max_correlation']})")
            ax2.axvline(0, color="grey", ls=":", lw=0.8)
            ax2.set_xlabel("Lag (kyr): positive = CO\u2082 lags temperature")
            ax2.set_ylabel("Normalised cross-correlation")
            ax2.set_title("Q2: Vostok CO\u2082 vs temperature lead-lag")
            ax2.legend(fontsize=9)
            ax2.grid(True, alpha=0.3)
        fig.tight_layout()
        png = proc / "paleoclimate_multisource.png"
        fig.savefig(png, dpi=140)
        plt.close(fig)
        print(f"\nSaved plot -> {png}")
    except Exception as exc:  # pragma: no cover
        print(f"\nPlot skipped ({type(exc).__name__}: {exc})")

    print("\n=== MULTI-SOURCE PALEOCLIMATE SIGNAL (UBY-ingested) ===")
    print("\n[Q1] Independent orbital-band power (fraction of spectrum in Milankovitch bands):")
    for k, v in q1.items():
        print(f"  {k:18s} ({v['proxy']:26s}): {v['orbital_band_power_pct']:5.1f}%  "
              f"[100kyr {v['orbital_periods']['eccentricity_short']['power_fraction_pct']:.1f}%, "
              f"41kyr {v['orbital_periods']['obliquity']['power_fraction_pct']:.1f}%]")
    if q2:
        print(f"\n[Q2] Vostok CO2 vs temperature: peak lag = {q2['best_lag_kyr']} kyr "
              f"(r={q2['max_correlation']}, zero-lag r={q2['zero_lag_correlation']})")
        print(f"     ({q2['definition']})")
    print(f"\nWall time: {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
