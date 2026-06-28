#!/usr/bin/env python3
"""Modern climate attribution: solar activity vs CO2 on global temperature.

A NEW cross-domain signal mining on the UBY axis using THREE modern
instrumental records that have never been combined in this codebase:

  - SILSO sunspot number (solar activity proxy, 1749-2024)
  - NASA GISS GISTEMP v4 global surface temperature anomaly (1880-2025)
  - NOAA GML Mauna Loa monthly atmospheric CO2 (1958-2026)

The scientific question (genuine, falsifiable, IPCC-relevant):

    Over the 1958-2024 common instrument era, what is the RELATIVE
    contribution of (a) solar activity variation and (b) atmospheric CO2
    rise to the observed global temperature anomaly?

Method
------
1. Restrict to the common overlap window (1958-2024) on the UBY axis.
2. Resample all three series to a common annual grid by linear interpolation.
3. Compute pairwise Pearson correlations and lagged cross-correlations.
4. Decompose the temperature anomaly:
       T(t) = a * S(t) + b * C(t) + residual
   where S is solar (sunspot) and C is CO2, via ordinary least squares.
5. Quantify the variance fraction attributable to each driver:
       R^2_solar = |a|^2 * var(S) / var(T)
       R^2_co2   = |b|^2 * var(C) / var(T)
6. Test whether the solar-temperature correlation survives after removing
   the CO2 trend (partial correlation) -- the key falsifiable test:
   if solar activity drives modern warming, it should remain correlated
   with temperature residuals after detrending CO2.

Research status: exploratory_signal_mining_not_final_claim.
UBY role: common time axis for heterogeneous instrument records.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

try:
    import numpy as np
    from scipy import stats
except ImportError:  # pragma: no cover
    print("numpy and scipy are required for this example.")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import DEFAULT_ANCHOR_UBY as ANCHOR_UBY

PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "modern_climate_attribution_report.json"

# Common analysis window (calendar years).
WINDOW_START = 1958.0
WINDOW_END = 2024.0


def _decimal_year_to_uby(dy: float) -> float:
    return float(ANCHOR_UBY) + (dy - 2026.0)


def load_sunspot_yearly() -> tuple[np.ndarray, np.ndarray]:
    """Returns (decimal_year, ssn) arrays, sunspot >= 0 only."""
    path = ROOT / "data" / "raw" / "external" / "SN_y_tot_V2.0.txt"
    years, values = [], []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                dy = float(parts[0])
                ssn = float(parts[1])
            except ValueError:
                continue
            if ssn < 0:
                continue
            years.append(dy)
            values.append(ssn)
    return np.array(years), np.array(values)


def load_gistemp() -> tuple[np.ndarray, np.ndarray]:
    """Returns (decimal_year_midyear, anomaly_degC) arrays."""
    path = ROOT / "data" / "raw" / "external" / "gistemp_global.csv"
    years, values = [], []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        next(fh, None)  # skip title
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                year = int(row["Year"])
                jd = row.get("J-D", "").strip()
                if jd == "***" or not jd:
                    continue
                anomaly = float(jd)
            except (ValueError, KeyError):
                continue
            years.append(year + 0.5)
            values.append(anomaly)
    return np.array(years), np.array(values)


def load_maunaloa_co2() -> tuple[np.ndarray, np.ndarray]:
    """Returns (decimal_year, co2_ppm) arrays."""
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
    return np.array(years), np.array(values)


def resample_annual(years: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Resample to integer-year grid by linear interpolation within the window."""
    grid = np.arange(int(np.floor(WINDOW_START)), int(np.ceil(WINDOW_END)) + 1, dtype=float)
    mask = (years >= WINDOW_START - 1) & (years <= WINDOW_END + 1)
    interp = np.interp(grid, years[mask], values[mask])
    return grid, interp


def main() -> int:
    t0 = time.perf_counter()

    # Load all three series.
    sy, sv = load_sunspot_yearly()
    gy, gv = load_gistemp()
    my, mv = load_maunaloa_co2()
    print(f"[load] sunspot yearly:  n={len(sy):4d}  span={sy.min():.1f}-{sy.max():.1f}")
    print(f"[load] gistemp:         n={len(gy):4d}  span={gy.min():.1f}-{gy.max():.1f}")
    print(f"[load] maunaloa co2:    n={len(my):4d}  span={my.min():.1f}-{my.max():.1f}")

    # Resample onto a common annual grid within the overlap window.
    sg, s_interp = resample_annual(sy, sv)
    gg, g_interp = resample_annual(gy, gv)
    mg, m_interp = resample_annual(my, mv)

    # All grids should now match (same annual integers).
    assert np.array_equal(sg, gg) and np.array_equal(sg, mg), "Grid mismatch"
    years = sg
    n = len(years)
    print(f"[align] common annual grid: n={n}  years={int(years.min())}-{int(years.max())}")

    # UBY-aligned sample for the first point of each series.
    uby_first = _decimal_year_to_uby(years[0])
    uby_last = _decimal_year_to_uby(years[-1])

    # --- Pairwise correlations ---
    r_sg, p_sg = stats.pearsonr(s_interp, g_interp)
    r_mg, p_mg = stats.pearsonr(m_interp, g_interp)
    r_sm, p_sm = stats.pearsonr(s_interp, m_interp)

    print(f"\n[corr] solar vs temperature:  r={r_sg:+.4f}  p={p_sg:.2e}")
    print(f"[corr] CO2 vs temperature:     r={r_mg:+.4f}  p={p_mg:.2e}")
    print(f"[corr] solar vs CO2:           r={r_sm:+.4f}  p={p_sm:.2e}")

    # --- Lagged cross-correlations (temperature response to each driver) ---
    max_lag_years = 10
    lags = np.arange(-max_lag_years, max_lag_years + 1)

    def xcorr(a, b, lags):
        a = a - a.mean()
        b = b - b.mean()
        out = []
        for lag in lags:
            if lag >= 0:
                x = a[lag:]
                y = b[: len(b) - lag]
            else:
                x = a[: len(a) + lag]
                y = b[-lag:]
            if len(x) < 5:
                out.append(0.0)
                continue
            out.append(float(np.corrcoef(x, y)[0, 1]))
        return out

    solar_temp_xcorr = xcorr(s_interp, g_interp, lags)
    co2_temp_xcorr = xcorr(m_interp, g_interp, lags)

    best_solar_lag = lags[int(np.argmax(np.abs(solar_temp_xcorr)))]
    best_solar_r = solar_temp_xcorr[int(np.argmax(np.abs(solar_temp_xcorr)))]
    best_co2_lag = lags[int(np.argmax(np.abs(co2_temp_xcorr)))]
    best_co2_r = co2_temp_xcorr[int(np.argmax(np.abs(co2_temp_xcorr)))]
    print(f"[xcorr] solar->temp: best lag={best_solar_lag} yr, r={best_solar_r:+.4f}")
    print(f"[xcorr] CO2->temp:   best lag={best_co2_lag} yr, r={best_co2_r:+.4f}")

    # --- Multiple linear regression: T = a*S + b*C + intercept ---
    design = np.column_stack([s_interp, m_interp])
    design = np.column_stack([design, np.ones(n)])  # intercept
    coeffs, residuals_, rank, sv = np.linalg.lstsq(design, g_interp, rcond=None)
    a_solar, b_co2, c_intercept = coeffs
    pred = design @ coeffs
    ss_res = float(np.sum((g_interp - pred) ** 2))
    ss_tot = float(np.sum((g_interp - g_interp.mean()) ** 2))
    r2_full = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Variance fractions via standardized coefficients.
    # var(T) ~= a^2 * var(S) + b^2 * var(C) + 2ab*cov(S,C)
    var_s = float(np.var(s_interp))
    var_c = float(np.var(m_interp))
    var_t = float(np.var(g_interp))
    cov_sc = float(np.cov(s_interp, m_interp)[0, 1])
    var_solar_alone = a_solar ** 2 * var_s
    var_co2_alone = b_co2 ** 2 * var_c
    var_cross = 2.0 * a_solar * b_co2 * cov_sc
    # Normalize to var(T).
    frac_solar = var_solar_alone / var_t if var_t > 0 else 0.0
    frac_co2 = var_co2_alone / var_t if var_t > 0 else 0.0
    frac_cross = var_cross / var_t if var_t > 0 else 0.0
    frac_resid = max(0.0, 1.0 - frac_solar - frac_co2 - frac_cross)

    print(f"\n[regression] T = {a_solar:+.6e} * S + {b_co2:+.6e} * C + {c_intercept:+.4f}")
    print(f"[regression] R^2 (full model) = {r2_full:.4f}")
    print(f"[regression] variance fraction solar   = {frac_solar:.4f}")
    print(f"[regression] variance fraction CO2     = {frac_co2:.4f}")
    print(f"[regression] variance fraction cross   = {frac_cross:.4f}")
    print(f"[regression] variance fraction residual= {frac_resid:.4f}")

    # --- Partial correlation: solar vs temperature after removing CO2 trend ---
    # Residualize T and S against C.
    def resid(y, x):
        x1 = np.column_stack([x, np.ones_like(x)])
        c, *_ = np.linalg.lstsq(x1, y, rcond=None)
        return y - x1 @ c

    t_resid_co2 = resid(g_interp, m_interp)
    s_resid_co2 = resid(s_interp, m_interp)
    r_partial, p_partial = stats.pearsonr(s_resid_co2, t_resid_co2)
    print(f"\n[partial] solar vs temp | CO2 removed:  r={r_partial:+.4f}  p={p_partial:.2e}")

    # Likewise, CO2 vs temperature after removing solar.
    t_resid_solar = resid(g_interp, s_interp)
    m_resid_solar = resid(m_interp, s_interp)
    r_partial_co2, p_partial_co2 = stats.pearsonr(m_resid_solar, t_resid_solar)
    print(f"[partial] CO2 vs temp | solar removed:  r={r_partial_co2:+.4f}  p={p_partial_co2:.2e}")

    # --- Solar cycle (Schwabe ~11 yr) detection in temperature residual ---
    # FFT of the CO2-detrended temperature residual.
    t_detrended = t_resid_co2 - t_resid_co2.mean()
    window = np.hanning(n)
    spec = np.abs(np.fft.rfft(t_detrended * window)) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0)  # cycles per year
    periods = np.where(freqs > 0, 1.0 / freqs, np.inf)
    # Find dominant peak in 8-14 yr band (Schwabe range).
    band = (periods >= 8) & (periods <= 14)
    if band.any():
        peak_idx = band.nonzero()[0][np.argmax(spec[band])]
        peak_period = float(periods[peak_idx])
        peak_power_frac = float(spec[peak_idx] / spec.sum()) if spec.sum() > 0 else 0.0
    else:
        peak_period = None
        peak_power_frac = 0.0
    print(f"\n[spectral] T residual (CO2 removed): dominant 8-14yr peak = "
          f"{peak_period} yr  (power fraction = {peak_power_frac:.4f})")

    elapsed = time.perf_counter() - t0

    report = {
        "database": "Modern climate attribution: solar vs CO2 on global temperature (UBY axis)",
        "description": (
            "Three modern instrumental records (SILSO sunspot, GISTEMP v4, "
            "Mauna Loa CO2) aligned on a common UBY time axis to quantify the "
            "relative contribution of solar activity and CO2 rise to modern "
            "global warming over 1958-2024."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "anchor_uby": float(ANCHOR_UBY),
        "uby_value_range": [uby_first, uby_last],
        "common_window": {"start_year": int(years.min()), "end_year": int(years.max()), "n": n},
        "data_sources": {
            "solar": "SILSO yearly sunspot number v2.0 (WDC, Royal Observatory of Belgium)",
            "temperature": "NASA GISS GISTEMP v4 global surface temperature anomaly (J-D annual mean)",
            "co2": "NOAA GML Mauna Loa monthly CO2 (interpolated, monthly mean)",
        },
        "pairwise_correlations": {
            "solar_vs_temperature": {"r": float(r_sg), "p": float(p_sg)},
            "co2_vs_temperature": {"r": float(r_mg), "p": float(p_mg)},
            "solar_vs_co2": {"r": float(r_sm), "p": float(p_sm)},
        },
        "lagged_cross_correlation": {
            "max_lag_years": int(max_lag_years),
            "solar_to_temperature": {
                "best_lag_years": int(best_solar_lag),
                "best_r": float(best_solar_r),
                "curve": [{"lag_years": int(l), "r": float(r)} for l, r in zip(lags, solar_temp_xcorr)],
            },
            "co2_to_temperature": {
                "best_lag_years": int(best_co2_lag),
                "best_r": float(best_co2_r),
                "curve": [{"lag_years": int(l), "r": float(r)} for l, r in zip(lags, co2_temp_xcorr)],
            },
        },
        "multiple_regression": {
            "model": "T_anomaly = a * sunspot + b * CO2 + intercept",
            "coefficients": {
                "a_solar": float(a_solar),
                "b_co2": float(b_co2),
                "intercept": float(c_intercept),
            },
            "r_squared_full": float(r2_full),
            "variance_fractions": {
                "solar_alone": float(frac_solar),
                "co2_alone": float(frac_co2),
                "cross_term": float(frac_cross),
                "residual": float(frac_resid),
            },
        },
        "partial_correlations": {
            "solar_vs_temp_given_co2": {"r": float(r_partial), "p": float(p_partial)},
            "co2_vs_temp_given_solar": {"r": float(r_partial_co2), "p": float(p_partial_co2)},
        },
        "solar_cycle_in_temperature_residual": {
            "method": "Hann-windowed FFT of CO2-detrended temperature residual",
            "dominant_period_years": peak_period,
            "power_fraction": float(peak_power_frac),
            "schwabe_band": "8-14 years",
        },
        "interpretation": {
            "key_findings": [
                f"CO2 explains ~{frac_co2*100:.1f}% of temperature variance, "
                f"solar explains ~{frac_solar*100:.1f}% (single-driver attribution).",
                f"After removing CO2 trend, solar-temperature partial correlation "
                f"r={r_partial:+.4f} (p={p_partial:.2e}).",
                f"Full bivariate model R^2 = {r2_full:.4f}.",
                f"Schwabe ~11yr cycle in CO2-detrended T residual: "
                f"period={peak_period} yr, power={peak_power_frac*100:.2f}%.",
            ],
            "claim_boundary": [
                "First-pass OLS on annual means; no autocorrelation correction (Newey-West), "
                "no ENSO/volcanic aerosol confounders removed.",
                "Solar proxy is sunspot number, not total solar irradiance (TSI).",
                "Reproduces the well-established IPCC attribution that CO2 dominates "
                "modern warming; not a new climate-science discovery.",
                "UBY role: common reproducible time axis for heterogeneous instrument records; "
                "the science comes from the records and the regression.",
            ],
        },
        "research_status": "exploratory_signal_mining_not_final_claim",
        "build_performance": {"wall_seconds": round(elapsed, 4)},
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    CSV_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[done] Report: {CSV_OUT}  (wall={elapsed:.3f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
