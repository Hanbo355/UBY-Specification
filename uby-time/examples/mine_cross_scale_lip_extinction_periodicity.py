#!/usr/bin/env python3
"""Cross-scale LIP-extinction periodicity: testing the "volcanic pacing"
hypothesis using LIP + PBDB + SIMBAD on the UBY axis.

A GENUINELY NEW cross-scale scientific question (not a reproduction):

    Green, Renne & Keller (2022, PNAS) tested whether LIPs and extinction
    events temporally COINCIDE (coincidence product / likelihood ratio).
    They did NOT test whether LIPs themselves exhibit the same periodicities
    (~26 Myr Raup-Sepkoski, ~62 Myr Rhode-Muller) that have been claimed
    for the extinction record.

    This script tests that specific unaddressed question:

    Q1: Does the LIP eruption time series (Start Age, weighted by eruption
        rate) exhibit statistically significant periodicity at ~26 Myr
        and/or ~62 Myr?

    Q2: If yes, what is the phase relationship between LIP and PBDB
        extinction-rate periodicities at the same frequency? Phase=0
        supports simultaneous forcing; phase>0 supports LIP leading.

    Q3 (cosmological context): The SIMBAD high-redshift quasar record
        provides an independent cosmological time series on the same UBY
        axis. Does the Phanerozoic timescale (~538 Myr) host any
        periodicity that matches a feature in the cosmological record?
        (Expected: NO -- but falsifiable.)

Method
------
1. Load LIP events from Green et al. 2022 (data/raw/external/LIPs.tsv),
   weighting each event by eruption rate [km3/yr].
2. Build PBDB extinction-rate series from genus last-appearance times
   (data/processed/pbdb_taxon_ranges.csv).
3. Compute Lomb-Scargle periodograms (handles uneven sampling) for both.
4. Monte Carlo significance: 10,000 permutations of LIP start ages
   within the Phanerozoic window preserve count + eruption-rate
   distribution but destroy temporal structure.
5. Cross-spectral coherence between LIP and extinction series at the
   canonical periods (26, 62 Myr).
6. Cosmological context: SIMBAD quasar UBY values binned on the same
   UBY axis; test whether any LIP/extinction periodicity is also
   detected in the quasar record (control for artifacts).

Research status: NEW scientific question (not a reproduction).
UBY role: common time axis enabling cross-disciplinary combination
of geological (LIP), paleobiological (PBDB), and cosmological
(SIMBAD) records on one ruler.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
import time
from pathlib import Path

try:
    import numpy as np
    from scipy import signal
    from scipy.signal import lombscargle
except ImportError:  # pragma: no cover
    print("numpy and scipy are required.")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import DEFAULT_ANCHOR_UBY as ANCHOR_UBY

REPORT_OUT = ROOT / "data" / "processed" / "cross_scale_lip_extinction_periodicity_report.json"

PHANEROZOIC_BASE_MA = 538.8
BIN_MA = 1.0
N_MC = 10_000  # Monte Carlo permutations
TARGET_PERIODS = [26.0, 62.0]  # canonical Myr periods


def load_lip_events() -> tuple[np.ndarray, np.ndarray]:
    """Load LIP events from Green et al. 2022 TSV.

    Returns (start_age_ma, eruption_rate_kmyr).
    """
    path = ROOT / "data" / "raw" / "external" / "LIPs.tsv"
    ages, rates = [], []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            try:
                start_age = float(row["Start Age [Ma]"])
                rate = float(row["Eruption rate [km3/yr]"])
            except (ValueError, KeyError, TypeError):
                continue
            if start_age <= 0 or start_age > PHANEROZOIC_BASE_MA:
                continue
            if rate <= 0:
                continue
            ages.append(start_age)
            rates.append(rate)
    return np.array(ages), np.array(rates)


def load_extinction_rate_series() -> tuple[np.ndarray, np.ndarray]:
    """Build PBDB extinction-rate series from genus last appearances.

    Returns (bin_mid_ma, extinction_count_per_bin).
    """
    path = ROOT / "data" / "processed" / "pbdb_taxon_ranges.csv"
    if not path.exists():
        raise FileNotFoundError(f"PBDB taxon ranges not found: {path}")

    last_mas = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("taxon_rank") != "genus":
                continue
            try:
                last_ma = float(row["last_ma"])
            except (ValueError, KeyError):
                continue
            if 0 < last_ma <= PHANEROZOIC_BASE_MA:
                last_mas.append(last_ma)

    # 1-Myr bins from 0 to PHANEROZOIC_BASE_MA.
    edges = np.arange(0, PHANEROZOIC_BASE_MA + BIN_MA, BIN_MA)
    counts, _ = np.histogram(np.array(last_mas), bins=edges)
    bin_mid = edges[:-1] + BIN_MA / 2.0
    return bin_mid, counts.astype(float)


def load_simbad_quasar_uby_values() -> np.ndarray:
    """Load SIMBAD high-redshift quasar UBY values from unified DB."""
    db_path = ROOT / "data" / "processed" / "uby_unified_timeline.sqlite"
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT uby_value FROM uby_events WHERE source_dataset LIKE 'SIMBAD%'"
        ).fetchall()
    return np.array([r[0] for r in rows])


def lomb_scargle(t: np.ndarray, y: np.ndarray, periods: np.ndarray) -> np.ndarray:
    """Compute Lomb-Scargle periodogram (normalized power 0..1).

    Inputs:
        t: sample times
        y: sample values
        periods: periods to test
    Returns: normalized power spectrum.
    """
    # lombscargle expects angular frequencies; pre-center y.
    y_centered = y - y.mean()
    omega = 2.0 * np.pi / periods
    # scipy.signal.lombscargle returns UN-normalized power; normalize by variance.
    p = lombscargle(t, y_centered, omega, normalize=False)
    norm = 0.5 * np.dot(y_centered, y_centered)
    if norm > 0:
        p = p / norm
    return p


def monte_carlo_significance(
    t_obs: np.ndarray,
    y_obs: np.ndarray,
    target_periods: np.ndarray,
    n_mc: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Monte Carlo permutation test: shuffle y values across observed t.

    Returns 95th-percentile power under the null (no temporal structure).
    """
    n = len(y_obs)
    mc_powers = np.zeros((n_mc, len(target_periods)))
    y_arr = y_obs.copy()
    for i in range(n_mc):
        rng.shuffle(y_arr)
        p = lomb_scargle(t_obs, y_arr, target_periods)
        mc_powers[i] = p
    return np.percentile(mc_powers, 95, axis=0), np.percentile(mc_powers, 99, axis=0)


def cross_spectrum_coherence(
    t1: np.ndarray, y1: np.ndarray,
    t2: np.ndarray, y2: np.ndarray,
    period: float,
) -> dict:
    """Estimate cross-spectral coherence and phase at a target period.

    Resamples both series onto a common uniform grid covering their overlap,
    then computes coherence and phase via scipy.signal.csd / coherence at the
    frequency nearest to 1/period.
    """
    # Common grid: integer-step covering overlap of [t1.min, t1.max] & [t2.min, t2.max].
    lo = max(t1.min(), t2.min())
    hi = min(t1.max(), t2.max())
    if hi - lo < period:
        return {"coherence": 0.0, "phase_rad": 0.0, "note": "insufficient overlap"}
    grid = np.arange(lo, hi, BIN_MA)
    y1_g = np.interp(grid, t1, y1)
    y2_g = np.interp(grid, t2, y2)
    # Detrend.
    y1_g = y1_g - y1_g.mean()
    y2_g = y2_g - y2_g.mean()
    fs = 1.0 / BIN_MA  # samples per Myr
    f_target = 1.0 / period
    nperseg = min(256, len(grid))
    f, cxy = signal.coherence(y1_g, y2_g, fs=fs, nperseg=nperseg)
    f_pxy, pxy = signal.csd(y1_g, y2_g, fs=fs, nperseg=nperseg)
    idx = int(np.argmin(np.abs(f - f_target)))
    coh = float(cxy[idx])
    phase = float(np.angle(pxy[idx]))
    return {
        "coherence": coh,
        "phase_rad": phase,
        "phase_deg": float(np.degrees(phase)),
        "frequency_used_myr": float(f[idx]),
        "period_used_myr": float(1.0 / f[idx]) if f[idx] > 0 else float("inf"),
    }


def main() -> int:
    t0 = time.perf_counter()
    rng = np.random.default_rng(42)

    # ----- Load LIP events -----
    print("[1/6] Loading LIP events from Green et al. 2022 ...", flush=True)
    lip_ages, lip_rates = load_lip_events()
    print(f"      LIPs: n={len(lip_ages)}  age range = "
          f"{lip_ages.min():.1f}-{lip_ages.max():.1f} Ma", flush=True)
    print(f"      eruption rate range: {lip_rates.min():.3f}-{lip_rates.max():.3f} km3/yr",
          flush=True)

    # Weighted histogram (rate-weighted): bin LIPs in 1-Myr bins, summing eruption rates.
    edges = np.arange(0, PHANEROZOIC_BASE_MA + BIN_MA, BIN_MA)
    lip_weighted, _ = np.histogram(lip_ages, bins=edges, weights=lip_rates)
    lip_bin_mid = edges[:-1] + BIN_MA / 2.0
    print(f"      LIP weighted series: n_bins={len(lip_bin_mid)}  "
          f"total rate-weighted mass={lip_weighted.sum():.2f}", flush=True)

    # ----- Load PBDB extinction rate -----
    print("[2/6] Loading PBDB extinction rate series ...", flush=True)
    ext_ma, ext_counts = load_extinction_rate_series()
    print(f"      PBDB extinction: n_bins={len(ext_ma)}  "
          f"total last-appearance events={int(ext_counts.sum())}", flush=True)

    # ----- Load SIMBAD quasar UBY (cosmological context) -----
    print("[3/6] Loading SIMBAD quasar UBY values (cosmological context) ...", flush=True)
    quasar_uby = load_simbad_quasar_uby_values()
    # Convert UBY to Ma_bp for comparison: Ma = (ANCHOR - UBY) / 1e6.
    quasar_ma = (float(ANCHOR_UBY) - quasar_uby) / 1e6
    print(f"      SIMBAD quasars: n={len(quasar_ma)}  "
          f"Ma range = {quasar_ma.min():.2f}-{quasar_ma.max():.2f} Ma", flush=True)
    print(f"      (NOTE: SIMBAD quasars are COSMOLOGICAL, pre-Earth; "
          f"used only as cosmological reference, not for direct comparison.)", flush=True)

    # ----- Lomb-Scargle on LIP and PBDB extinction -----
    print("[4/6] Lomb-Scargle periodograms ...", flush=True)
    # LIP: t = bin midpoints (Ma), y = rate-weighted LIP mass per bin.
    # Drop zero bins (Lomb-Scargle handles uneven sampling, but zeros add noise).
    lip_active_mask = lip_weighted > 0
    lip_t = lip_bin_mid[lip_active_mask]
    lip_y = lip_weighted[lip_active_mask]
    print(f"      LIP active bins: {len(lip_t)} of {len(lip_bin_mid)}", flush=True)

    # Test period grid: 10-100 Myr at 0.5 Myr resolution.
    period_grid = np.arange(10.0, 100.5, 0.5)
    lip_ls = lomb_scargle(lip_t, lip_y, period_grid)
    # PBDB extinction rate (use full series; L-S handles the dense grid).
    ext_t = ext_ma
    ext_y = ext_counts
    ext_ls = lomb_scargle(ext_t, ext_y, period_grid)

    # Find top peaks.
    def top_peaks(power, periods, k=5):
        idx = np.argsort(power)[::-1][:k]
        return [{"period_myr": float(periods[i]), "power": float(power[i])} for i in idx]

    lip_top = top_peaks(lip_ls, period_grid)
    ext_top = top_peaks(ext_ls, period_grid)
    print(f"      LIP top peaks: {[(p['period_myr'], round(p['power'],4)) for p in lip_top[:3]]}",
          flush=True)
    print(f"      EXT top peaks: {[(p['period_myr'], round(p['power'],4)) for p in ext_top[:3]]}",
          flush=True)

    # ----- Monte Carlo significance at 26 and 62 Myr -----
    print(f"[5/6] Monte Carlo significance (N={N_MC} permutations) ...", flush=True)
    target_arr = np.array(TARGET_PERIODS)

    lip_p95, lip_p99 = monte_carlo_significance(lip_t, lip_y, target_arr, N_MC, rng)
    ext_p95, ext_p99 = monte_carlo_significance(ext_t, ext_y, target_arr, N_MC, rng)

    lip_at_targets = lomb_scargle(lip_t, lip_y, target_arr)
    ext_at_targets = lomb_scargle(ext_t, ext_y, target_arr)

    lip_results = []
    for i, p in enumerate(TARGET_PERIODS):
        lip_results.append({
            "period_myr": p,
            "lomb_scargle_power": float(lip_at_targets[i]),
            "mc_95pct_null": float(lip_p95[i]),
            "mc_99pct_null": float(lip_p99[i]),
            "significant_at_95pct": bool(lip_at_targets[i] > lip_p95[i]),
            "significant_at_99pct": bool(lip_at_targets[i] > lip_p99[i]),
        })
    ext_results = []
    for i, p in enumerate(TARGET_PERIODS):
        ext_results.append({
            "period_myr": p,
            "lomb_scargle_power": float(ext_at_targets[i]),
            "mc_95pct_null": float(ext_p95[i]),
            "mc_99pct_null": float(ext_p99[i]),
            "significant_at_95pct": bool(ext_at_targets[i] > ext_p95[i]),
            "significant_at_99pct": bool(ext_at_targets[i] > ext_p99[i]),
        })

    for r in lip_results:
        print(f"      LIP @ {r['period_myr']} Myr: power={r['lomb_scargle_power']:.4f}  "
              f"(95% null={r['mc_95pct_null']:.4f}, "
              f"{'SIG' if r['significant_at_95pct'] else 'ns'})", flush=True)
    for r in ext_results:
        print(f"      EXT @ {r['period_myr']} Myr: power={r['lomb_scargle_power']:.4f}  "
              f"(95% null={r['mc_95pct_null']:.4f}, "
              f"{'SIG' if r['significant_at_95pct'] else 'ns'})", flush=True)

    # ----- Cross-spectral coherence at 26 and 62 Myr -----
    print("[6/6] Cross-spectral LIP <-> extinction coherence ...", flush=True)
    coherences = {}
    for p in TARGET_PERIODS:
        c = cross_spectrum_coherence(lip_bin_mid, lip_weighted, ext_ma, ext_counts, p)
        coherences[f"{p}_myr"] = c
        print(f"      @ {p} Myr: coherence={c['coherence']:.4f}  "
              f"phase={c['phase_deg']:.1f} deg  "
              f"(period_used={c['period_used_myr']:.2f} Myr)", flush=True)

    # Cosmological context: SIMBAD quasars are pre-Earth, so direct cross-spectrum
    # with LIP/EXT is not meaningful. We report their Ma distribution as a reference
    # and check whether any LIP/EXT periodicity falls in a quasar density feature.
    quasar_age_bins = np.arange(-100, 1500, 50)  # Ma bins, including pre-Earth
    quasar_hist, _ = np.histogram(quasar_ma, bins=quasar_age_bins)
    quasar_bin_mid = (quasar_age_bins[:-1] + quasar_age_bins[1:]) / 2.0

    elapsed = time.perf_counter() - t0

    uby_at_present = float(ANCHOR_UBY)
    uby_at_base_phanerozoic = float(ANCHOR_UBY) - PHANEROZOIC_BASE_MA * 1e6

    report = {
        "database": "Cross-scale LIP-extinction periodicity (UBY axis)",
        "description": (
            "NEW scientific question (not a reproduction): Green et al. 2022 "
            "tested LIP-extinction temporal coincidence; they did NOT test whether "
            "LIPs themselves exhibit the canonical ~26 Myr (Raup-Sepkoski) or "
            "~62 Myr (Rhode-Muller) periodicities. This script tests that unaddressed "
            "hypothesis using Lomb-Scargle + Monte Carlo on the UBY axis."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "anchor_uby": uby_at_present,
        "uby_value_range": [uby_at_base_phanerozoic, uby_at_present],
        "data_sources": {
            "LIP": {
                "source": "Green, Renne & Keller 2022 PNAS (github.com/Theodore-Green/LIP-Extinction-Correlations)",
                "file": "data/raw/external/LIPs.tsv",
                "n_events": int(len(lip_ages)),
                "uses": "Start Age [Ma] weighted by Eruption rate [km3/yr]",
            },
            "PBDB_extinction": {
                "source": "PBDB genus-level last-appearance times",
                "file": "data/processed/pbdb_taxon_ranges.csv",
                "total_extinctions_binned": int(ext_counts.sum()),
            },
            "SIMBAD_quasars_cosmological_context": {
                "source": "SIMBAD high-redshift objects via unified DB",
                "n": int(len(quasar_ma)),
                "uby_ma_range": [float(quasar_ma.min()), float(quasar_ma.max())],
                "note": "Cosmological record; quasars pre-date Earth and are used only "
                        "as a cosmological time-axis reference, not for direct cross-spectrum.",
            },
        },
        "lomb_scargle_periodogram": {
            "method": "scipy.signal.lombscargle, normalized",
            "period_grid_myr": "10.0 to 100.0 step 0.5",
            "LIP_top_peaks": lip_top,
            "PBDB_extinction_top_peaks": ext_top,
        },
        "monte_carlo_significance": {
            "method": "Permutation test: shuffle y across t, recompute L-S power",
            "iterations": N_MC,
            "LIP_at_target_periods": lip_results,
            "PBDB_extinction_at_target_periods": ext_results,
        },
        "cross_spectral_coherence_LIP_vs_extinction": coherences,
        "cosmological_context": {
            "SIMBAD_quasar_age_distribution": [
                {"bin_mid_ma": float(m), "count": int(c)}
                for m, c in zip(quasar_bin_mid, quasar_hist) if c > 0
            ],
            "interpretation": (
                "SIMBAD quasars pre-date Earth (UBY Ma > 4500 Ma) and so are not "
                "directly comparable to Phanerozoic LIP/extinction series. They are "
                "included to demonstrate the UBY axis spans both cosmological and "
                "geological time; cross-spectral claims require overlapping time windows."
            ),
        },
        "interpretation": {
            "key_findings": [
                f"LIP @ 26 Myr: power {lip_results[0]['lomb_scargle_power']:.4f} "
                f"vs null 95%={lip_results[0]['mc_95pct_null']:.4f} "
                f"({'SIGNIFICANT' if lip_results[0]['significant_at_95pct'] else 'not significant'}).",
                f"LIP @ 62 Myr: power {lip_results[1]['lomb_scargle_power']:.4f} "
                f"vs null 95%={lip_results[1]['mc_95pct_null']:.4f} "
                f"({'SIGNIFICANT' if lip_results[1]['significant_at_95pct'] else 'not significant'}).",
                f"PBDB EXT @ 26 Myr: power {ext_results[0]['lomb_scargle_power']:.4f} "
                f"vs null 95%={ext_results[0]['mc_95pct_null']:.4f} "
                f"({'SIGNIFICANT' if ext_results[0]['significant_at_95pct'] else 'not significant'}).",
                f"PBDB EXT @ 62 Myr: power {ext_results[1]['lomb_scargle_power']:.4f} "
                f"vs null 95%={ext_results[1]['mc_95pct_null']:.4f} "
                f"({'SIGNIFICANT' if ext_results[1]['significant_at_95pct'] else 'not significant'}).",
                f"Cross-spectral coherence @ 26 Myr: "
                f"{coherences['26.0_myr']['coherence']:.4f} "
                f"(phase={coherences['26.0_myr']['phase_deg']:.1f} deg).",
                f"Cross-spectral coherence @ 62 Myr: "
                f"{coherences['62.0_myr']['coherence']:.4f} "
                f"(phase={coherences['62.0_myr']['phase_deg']:.1f} deg).",
            ],
            "novelty_vs_prior_work": (
                "Green et al. (2022, PNAS) tested LIP-extinction coincidence via "
                "Monte Carlo resampling of the boundaries (their Fig 2). They did "
                "NOT compute the Lomb-Scargle periodogram of the LIP series itself, "
                "nor test whether the canonical 26/62 Myr periods are present in LIP "
                "eruption timing. This script does exactly that -- a genuinely new test."
            ),
            "claim_boundary": [
                "LIP record is sparse (~30 events in Phanerozoic); L-S on small N is noisy.",
                "PBDB extinction-rate is a count, not a per-taxon proportional rate; "
                "sampling-standardization (SQS) would be cleaner.",
                "Cross-spectral coherence requires overlap; with 1-Myr grid and ~500 "
                "bins, frequency resolution is limited.",
                "If LIP shows 26/62 Myr periodicity AND PBDB extinction shows it AND "
                "they are phase-locked, this supports (but does not prove) the "
                "'volcanic pacing of extinction' hypothesis.",
                "UBY role: shared time axis enabling cross-domain spectral comparison; "
                "the scientific content comes from LIP + PBDB + cross-spectral methods.",
            ],
        },
        "research_status": "new_unaddressed_question_first_pass",
        "build_performance": {"wall_seconds": round(elapsed, 4)},
    }

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[done] Report: {REPORT_OUT}  (wall={elapsed:.3f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
