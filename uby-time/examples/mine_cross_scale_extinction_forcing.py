#!/usr/bin/env python3
"""
Cross-Scale Extinction-Forcing Signal Mining
==============================================
Mine new scientific signals by correlating extinction events with potential
forcing mechanisms across multiple time scales using the UBY unified timeline.

This analysis investigates:
1. Temporal clustering of extinction events at different scales
2. Correlation between volcanic/tectonic events and biodiversity changes
3. Astronomical event coincidence with geological transitions
4. Multi-scale periodicity in extinction intensity
5. Lead-lag relationships between forcing events and biological responses

Research status: exploratory_signal_mining_not_final_claim
"""

from __future__ import annotations

import csv
import json
import math
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

# ============================================================
# Configuration
# ============================================================

# Time windows for multi-scale analysis (in years)
TIME_WINDOWS = {
    "short": 1e4,       # 10 kyr - orbital scale
    "medium": 1e5,      # 100 kyr - glacial-interglacial
    "long": 1e6,        # 1 Myr - geological stage
    "very_long": 1e7,   # 10 Myr - epoch scale
}

# Minimum events required for statistical significance
MIN_EVENTS_FOR_ANALYSIS = 10


def find_database() -> Path:
    """Find the unified timeline database."""
    here = Path(__file__).resolve().parent.parent
    db_path = here / "data" / "processed" / "uby_unified_timeline.sqlite"
    if not db_path.exists():
        raise FileNotFoundError(f"Unified timeline database not found at {db_path}")
    return db_path


def load_events_by_category(db_path: Path) -> dict:
    """Load events grouped by category from the unified timeline."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    categories = {}
    
    # Get all distinct categories
    cursor.execute("SELECT DISTINCT event_category FROM uby_events")
    cat_rows = cursor.fetchall()
    
    for (cat,) in cat_rows:
        cursor.execute("""
            SELECT event_name, uby_value, original_time_value, 
                   original_time_unit, event_subcategory, source_dataset,
                   original_error
            FROM uby_events 
            WHERE event_category = ?
            ORDER BY uby_value
        """, (cat,))
        
        events = []
        for row in cursor.fetchall():
            # Parse error value - may be numeric string or text like "0.05 Ma"
            error_val = None
            if row[6]:
                try:
                    error_val = float(row[6])
                except (ValueError, TypeError):
                    # Try to extract numeric part from strings like "0.05 Ma"
                    import re
                    match = re.search(r'([\d.]+)', str(row[6]))
                    if match:
                        try:
                            error_val = float(match.group(1))
                        except ValueError:
                            pass
            
            events.append({
                "name": row[0],
                "uby_value": float(row[1]) if row[1] else None,
                "original_time": row[2],
                "time_unit": row[3],
                "subcategory": row[4],
                "source": row[5],
                "error": error_val,
            })
        
        categories[cat] = events
    
    conn.close()
    return categories


def compute_event_density(uby_values: list[float], window_years: float, 
                          anchor_uby: float = 13787002026.0) -> dict:
    """
    Compute event density in sliding windows across UBY time.
    
    Returns density peaks that may indicate clustered events.
    """
    if len(uby_values) < MIN_EVENTS_FOR_ANALYSIS:
        return {"status": "insufficient_data", "n_events": len(uby_values)}
    
    # Convert window to UBY units (approximately 1 year = 1 UBY unit near present)
    window_uby = window_years
    
    # Sort values
    sorted_vals = sorted(uby_values)
    
    # Sliding window density
    densities = []
    positions = []
    
    step = window_uby / 10  # 10% overlap
    start = sorted_vals[0]
    end = sorted_vals[-1]
    
    pos = start
    while pos + window_uby <= end:
        count = sum(1 for v in sorted_vals if pos <= v < pos + window_uby)
        density = count / window_uby * 1e6  # events per million years
        densities.append(density)
        positions.append(pos + window_uby / 2)
        pos += step
    
    if not densities:
        return {"status": "no_windows", "n_events": len(uby_values)}
    
    # Find density peaks (> mean + 2*std)
    mean_d = sum(densities) / len(densities)
    std_d = math.sqrt(sum((d - mean_d)**2 for d in densities) / len(densities))
    threshold = mean_d + 2 * std_d
    
    peaks = []
    for i, (pos, dens) in enumerate(zip(positions, densities)):
        if dens > threshold:
            # Convert UBY position back to approximate Ma BP
            ma_bp = (anchor_uby - pos) / 1e6
            peaks.append({
                "uby_position": round(pos, 2),
                "ma_bp": round(ma_bp, 2),
                "density": round(dens, 4),
                "deviation_sigma": round((dens - mean_d) / std_d, 2) if std_d > 0 else 0,
            })
    
    peaks.sort(key=lambda x: x["density"], reverse=True)
    
    return {
        "status": "success",
        "n_events": len(uby_values),
        "window_years": window_years,
        "mean_density": round(mean_d, 4),
        "std_density": round(std_d, 4),
        "threshold_2sigma": round(threshold, 4),
        "n_peaks": len(peaks),
        "top_peaks": peaks[:10],
    }


def cross_correlate_events(events_a: list[dict], events_b: list[dict],
                           max_lag_years: float = 5e6, 
                           bin_years: float = 1e5) -> dict:
    """
    Cross-correlate two event series to find lead-lag relationships.
    
    Positive lag means A leads B (A happens before B).
    """
    uby_a = [e["uby_value"] for e in events_a if e["uby_value"]]
    uby_b = [e["uby_value"] for e in events_b if e["uby_value"]]
    
    if len(uby_a) < 5 or len(uby_b) < 5:
        return {"status": "insufficient_data"}
    
    # Create binned time series
    all_times = uby_a + uby_b
    t_min, t_max = min(all_times), max(all_times)
    
    n_bins = int((t_max - t_min) / bin_years) + 1
    if n_bins < 10:
        return {"status": "insufficient_range"}
    
    # Bin edges
    bin_edges = [t_min + i * bin_years for i in range(n_bins + 1)]
    
    # Count events per bin
    counts_a = [0] * n_bins
    counts_b = [0] * n_bins
    
    for t in uby_a:
        idx = int((t - t_min) / bin_years)
        if 0 <= idx < n_bins:
            counts_a[idx] += 1
    
    for t in uby_b:
        idx = int((t - t_min) / bin_years)
        if 0 <= idx < n_bins:
            counts_b[idx] += 1
    
    # Normalize
    mean_a = sum(counts_a) / n_bins
    mean_b = sum(counts_b) / n_bins
    std_a = math.sqrt(sum((c - mean_a)**2 for c in counts_a) / n_bins)
    std_b = math.sqrt(sum((c - mean_b)**2 for c in counts_b) / n_bins)
    
    if std_a == 0 or std_b == 0:
        return {"status": "zero_variance"}
    
    # Cross-correlation at different lags
    max_lag_bins = int(max_lag_years / bin_years)
    correlations = []
    
    for lag in range(-max_lag_bins, max_lag_bins + 1):
        corr_sum = 0
        count = 0
        for i in range(n_bins):
            j = i + lag
            if 0 <= j < n_bins:
                corr_sum += (counts_a[i] - mean_a) * (counts_b[j] - mean_b)
                count += 1
        
        if count > 0:
            corr = corr_sum / (count * std_a * std_b)
            lag_years = lag * bin_years
            correlations.append({
                "lag_years": lag_years,
                "lag_myr": round(lag_years / 1e6, 3),
                "correlation": round(corr, 4),
            })
    
    if not correlations:
        return {"status": "no_correlations"}
    
    # Find best correlation
    best = max(correlations, key=lambda x: abs(x["correlation"]))
    
    return {
        "status": "success",
        "n_bins": n_bins,
        "bin_years": bin_years,
        "best_lag_years": best["lag_years"],
        "best_lag_myr": best["lag_myr"],
        "best_correlation": best["correlation"],
        "interpretation": (
            f"Series A leads Series B by {best['lag_myr']:.2f} Myr "
            if best["lag_years"] > 0
            else f"Series B leads Series A by {-best['lag_myr']:.2f} Myr"
        ),
        "correlation_curve": correlations[::max(1, len(correlations)//50)],  # Sample for output
    }


def detect_periodicity(uby_values: list[float], min_period: float = 1e4,
                       max_period: float = 1e8) -> dict:
    """
    Detect periodicity in event timing using inter-event interval analysis.
    """
    if len(uby_values) < 20:
        return {"status": "insufficient_data"}
    
    sorted_vals = sorted(uby_values)
    
    # Compute inter-event intervals
    intervals = [sorted_vals[i+1] - sorted_vals[i] for i in range(len(sorted_vals)-1)]
    
    # Filter to relevant period range
    filtered = [iv for iv in intervals if min_period <= iv <= max_period]
    
    if len(filtered) < 10:
        return {"status": "insufficient_intervals"}
    
    # Histogram of intervals (log-spaced bins)
    log_min = math.log10(min(filtered))
    log_max = math.log10(max(filtered))
    n_bins = 50
    bin_width = (log_max - log_min) / n_bins
    
    histogram = defaultdict(int)
    for iv in filtered:
        bin_idx = int((math.log10(iv) - log_min) / bin_width)
        histogram[bin_idx] += 1
    
    # Find dominant interval
    if not histogram:
        return {"status": "no_histogram"}
    
    dominant_bin = max(histogram, key=histogram.get)
    dominant_interval = 10 ** (log_min + (dominant_bin + 0.5) * bin_width)
    
    # Check for harmonics
    harmonics = []
    for mult in [0.5, 1, 2, 3, 4]:
        test_interval = dominant_interval * mult
        test_log = math.log10(test_interval)
        test_bin = int((test_log - log_min) / bin_width)
        if test_bin in histogram:
            harmonics.append({
                "multiple": mult,
                "interval_years": round(test_interval, 0),
                "interval_myr": round(test_interval / 1e6, 3),
                "count": histogram[test_bin],
            })
    
    return {
        "status": "success",
        "n_intervals": len(filtered),
        "dominant_interval_years": round(dominant_interval, 0),
        "dominant_interval_myr": round(dominant_interval / 1e6, 3),
        "harmonics": harmonics,
        "note": "Dominant interval suggests characteristic timescale of the process",
    }


def analyze_extinction_forcing_coincidence(paleo_events: list[dict], 
                                            geo_events: list[dict],
                                            tolerance_years: float = 5e5) -> dict:
    """
    Analyze coincidence between extinction events and geological forcing events.
    
    Looks for temporal proximity suggesting causal relationships.
    """
    paleo_uby = [(e["uby_value"], e["name"]) for e in paleo_events if e["uby_value"]]
    geo_uby = [(e["uby_value"], e["name"], e.get("subcategory", "")) 
               for e in geo_events if e["uby_value"]]
    
    coincidences = []
    
    for p_uby, p_name in paleo_uby:
        for g_uby, g_name, g_sub in geo_uby:
            diff = abs(p_uby - g_uby)
            if diff <= tolerance_years:
                coincidences.append({
                    "paleo_event": p_name,
                    "geo_event": g_name,
                    "geo_subcategory": g_sub,
                    "uby_difference": round(diff, 0),
                    "time_difference_myr": round(diff / 1e6, 3),
                    "paleo_uby": round(p_uby, 2),
                    "geo_uby": round(g_uby, 2),
                })
    
    coincidences.sort(key=lambda x: x["uby_difference"])
    
    # Statistical significance: compare to random expectation
    if paleo_uby and geo_uby:
        total_span = max(e[0] for e in paleo_uby + geo_uby) - min(e[0] for e in paleo_uby + geo_uby)
        expected_random = len(paleo_uby) * len(geo_uby) * (2 * tolerance_years) / total_span if total_span > 0 else 0
    else:
        expected_random = 0
    
    return {
        "n_paleo_events": len(paleo_uby),
        "n_geo_events": len(geo_uby),
        "tolerance_years": tolerance_years,
        "tolerance_myr": tolerance_years / 1e6,
        "n_coincidences": len(coincidences),
        "expected_random": round(expected_random, 2),
        "significance_ratio": round(len(coincidences) / expected_random, 2) if expected_random > 0 else None,
        "top_coincidences": coincidences[:20],
    }


def main() -> int:
    t0 = time.perf_counter()
    
    print("=" * 72)
    print("  CROSS-SCALE EXTINCTION-FORCING SIGNAL MINING")
    print("  Using UBY Unified Timeline Database")
    print("=" * 72)
    print()
    
    # Load database
    db_path = find_database()
    print(f"[1/6] Loading unified timeline from {db_path.name}...")
    categories = load_events_by_category(db_path)
    
    for cat, events in categories.items():
        print(f"       {cat}: {len(events)} events")
    print()
    
    # Extract relevant event sets
    paleontology = categories.get("paleontology", [])
    geology = categories.get("geology", [])
    cosmology = categories.get("cosmology", [])
    
    # Filter paleontology for extinction-related events
    extinction_events = [e for e in paleontology 
                        if e.get("subcategory") and 
                        any(kw in str(e.get("subcategory", "")).lower() 
                            for kw in ["extinct", "disappear", "last", "end"])]
    
    # Filter geology for forcing events (volcanic, tectonic, impact)
    forcing_events = [e for e in geology
                     if e.get("subcategory") and
                     any(kw in str(e.get("subcategory", "")).lower()
                         for kw in ["volcan", "tecton", "impact", "eruption", "flood basalt"])]
    
    print(f"[2/6] Event filtering:")
    print(f"       Total paleontology events: {len(paleontology)}")
    print(f"       Extinction-related events: {len(extinction_events)}")
    print(f"       Total geology events: {len(geology)}")
    print(f"       Forcing events: {len(forcing_events)}")
    print()
    
    # ANALYSIS 1: Event density analysis at multiple scales
    print("[3/6] Multi-scale event density analysis...")
    density_results = {}
    
    for scale_name, window in TIME_WINDOWS.items():
        # Paleontology density
        paleo_uby = [e["uby_value"] for e in paleontology if e["uby_value"]]
        paleo_density = compute_event_density(paleo_uby, window)
        
        # Geology density
        geo_uby = [e["uby_value"] for e in geology if e["uby_value"]]
        geo_density = compute_event_density(geo_uby, window)
        
        density_results[scale_name] = {
            "window_years": window,
            "paleontology": paleo_density,
            "geology": geo_density,
        }
        
        if paleo_density.get("status") == "success":
            n_peaks = paleo_density.get("n_peaks", 0)
            print(f"       {scale_name} ({window:.0e} yr window): {n_peaks} paleontology density peaks")
    
    print()
    
    # ANALYSIS 2: Cross-correlation between paleontology and geology
    print("[4/6] Cross-correlation analysis (paleontology vs geology)...")
    
    paleo_uby_events = [e for e in paleontology if e["uby_value"]]
    geo_uby_events = [e for e in geology if e["uby_value"]]
    
    cross_corr = cross_correlate_events(paleo_uby_events, geo_uby_events,
                                         max_lag_years=1e7, bin_years=5e5)
    
    if cross_corr.get("status") == "success":
        print(f"       Best lag: {cross_corr['best_lag_myr']:.2f} Myr")
        print(f"       Best correlation: {cross_corr['best_correlation']:.4f}")
        print(f"       Interpretation: {cross_corr['interpretation']}")
    else:
        print(f"       Status: {cross_corr.get('status')}")
    print()
    
    # ANALYSIS 3: Periodicity detection
    print("[5/6] Periodicity detection in event series...")
    
    periodicity_results = {}
    
    for name, events in [("paleontology", paleontology), ("geology", geology)]:
        uby_vals = [e["uby_value"] for e in events if e["uby_value"]]
        result = detect_periodicity(uby_vals, min_period=1e5, max_period=1e8)
        periodicity_results[name] = result
        
        if result.get("status") == "success":
            dom_myr = result.get("dominant_interval_myr", 0)
            print(f"       {name}: dominant interval = {dom_myr:.3f} Myr")
            for h in result.get("harmonics", [])[:3]:
                print(f"         Harmonic {h['multiple']}x: {h['interval_myr']:.3f} Myr (n={h['count']})")
    print()
    
    # ANALYSIS 4: Extinction-forcing coincidence
    print("[6/6] Extinction-forcing event coincidence analysis...")
    
    coincidence = analyze_extinction_forcing_coincidence(
        extinction_events, forcing_events, tolerance_years=5e5
    )
    
    print(f"       Paleo events analyzed: {coincidence['n_paleo_events']}")
    print(f"       Forcing events analyzed: {coincidence['n_geo_events']}")
    print(f"       Coincidences found: {coincidence['n_coincidences']}")
    print(f"       Expected by chance: {coincidence['expected_random']}")
    if coincidence.get("significance_ratio"):
        print(f"       Significance ratio: {coincidence['significance_ratio']}x")
    print()
    
    # ================================================================
    # COMPILE RESULTS AND IDENTIFY CANDIDATE DISCOVERIES
    # ================================================================
    
    elapsed = time.perf_counter() - t0
    
    candidate_discoveries = []
    
    # Check for significant density peaks
    for scale, results in density_results.items():
        paleo = results.get("paleontology", {})
        if paleo.get("status") == "success" and paleo.get("n_peaks", 0) > 0:
            top_peak = paleo.get("top_peaks", [{}])[0] if paleo.get("top_peaks") else {}
            if top_peak.get("deviation_sigma", 0) > 3:
                candidate_discoveries.append({
                    "type": "EVENT CLUSTERING",
                    "scale": scale,
                    "finding": f"Significant paleontology event cluster at {top_peak.get('ma_bp', '?')} Ma BP "
                              f"({top_peak.get('deviation_sigma', 0):.1f}σ above mean)",
                    "why_novel": f"Event clustering at {scale} scale may indicate previously unrecognized "
                                f"coordinated biological response",
                    "confidence": "MEDIUM" if top_peak.get("deviation_sigma", 0) > 4 else "LOW-MEDIUM",
                })
    
    # Check for significant cross-correlation
    if cross_corr.get("status") == "success":
        best_corr = abs(cross_corr.get("best_correlation", 0))
        if best_corr > 0.3:
            candidate_discoveries.append({
                "type": "CROSS-DOMAIN CORRELATION",
                "finding": f"Paleontology-geology correlation r={cross_corr['best_correlation']:.4f} "
                          f"at lag {cross_corr['best_lag_myr']:.2f} Myr",
                "why_novel": "Suggests systematic coupling between geological processes and "
                            "biological evolution at this timescale",
                "confidence": "MEDIUM-HIGH" if best_corr > 0.5 else "MEDIUM",
            })
    
    # Check for interesting periodicities
    for name, result in periodicity_results.items():
        if result.get("status") == "success":
            dom_myr = result.get("dominant_interval_myr", 0)
            # Flag periods that don't match known Milankovitch cycles
            known_periods = [0.019, 0.023, 0.041, 0.1, 0.405]  # Myr
            is_novel = all(abs(dom_myr - kp) > 0.01 for kp in known_periods)
            if is_novel and dom_myr > 0.5:
                candidate_discoveries.append({
                    "type": "NOVEL PERIODICITY",
                    "dataset": name,
                    "finding": f"Dominant event interval of {dom_myr:.3f} Myr in {name} "
                              f"(not matching known orbital periods)",
                    "why_novel": "May reflect Earth-internal processes or external forcing "
                                "not related to Milankovitch cycles",
                    "confidence": "MEDIUM",
                })
    
    # Check for significant extinction-forcing coincidences
    if coincidence.get("significance_ratio", 0) and coincidence["significance_ratio"] > 2:
        candidate_discoveries.append({
            "type": "EXTINCTION-FORCING ASSOCIATION",
            "finding": f"{coincidence['n_coincidences']} extinction-forcing coincidences "
                      f"({coincidence['significance_ratio']}x random expectation)",
            "why_novel": "Statistically significant association suggests causal link between "
                        "geological forcing and biological extinction",
            "confidence": "HIGH" if coincidence["significance_ratio"] > 3 else "MEDIUM",
        })
    
    # Build final report
    report = {
        "database": "UBY Cross-Scale Extinction-Forcing Signal Mining",
        "description": (
            "Multi-scale analysis of extinction events and geological forcing mechanisms "
            "using the UBY unified timeline database. Investigates event clustering, "
            "cross-domain correlations, periodicity, and extinction-forcing coincidences."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "inputs": {
            "unified_timeline_db": str(db_path),
        },
        "event_counts": {
            "paleontology": len(paleontology),
            "extinction_related": len(extinction_events),
            "geology": len(geology),
            "forcing": len(forcing_events),
            "cosmology": len(cosmology),
        },
        "analyses": {
            "multi_scale_density": density_results,
            "cross_correlation": cross_corr,
            "periodicity": periodicity_results,
            "extinction_forcing_coincidence": coincidence,
        },
        "candidate_discoveries": candidate_discoveries,
        "research_status": "exploratory_signal_mining_not_final_claim",
        "claim_boundary": [
            "Exploratory analysis using simple statistical methods; not publication-grade.",
            "Event categorization based on keyword matching may have false positives/negatives.",
            "Temporal uncertainties in source data not fully propagated.",
            "Multiple testing corrections not applied to significance estimates.",
            "Publication requires rigorous statistical validation and domain expert review.",
        ],
        "build_performance": {
            "wall_seconds": round(elapsed, 2),
        },
    }
    
    # Save report
    out_dir = db_path.parent
    report_path = out_dir / "cross_scale_extinction_forcing_report.json"
    
    print("=" * 72)
    print("  CANDIDATE SCIENTIFIC DISCOVERIES")
    print("=" * 72)
    
    if candidate_discoveries:
        for i, disc in enumerate(candidate_discoveries, 1):
            print(f"\n  Discovery #{i} [{disc['confidence']}]")
            print(f"  Type: {disc['type']}")
            print(f"  Finding: {disc['finding']}")
            print(f"  Why Novel: {disc['why_novel']}")
    else:
        print("\n  No definitive new signals detected at current thresholds.")
        print("  Consider adjusting parameters or adding more specific event filters.")
    
    print(f"\nFull report saved to: {report_path}")
    print(f"Wall time: {elapsed:.2f}s")
    
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
