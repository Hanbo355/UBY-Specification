"""Mine a signal that ONLY a unified cross-scale time axis (UBY) can reveal:
the relative-time-precision scaling law across the whole observable record.

Motivation
----------
Single-scale analyses (e.g. "which mass extinction came first") never need UBY:
plain Ma-before-present is enough, and that is what paleontologists already use.
UBY's irreplaceable value is CROSS-SCALE UNIFICATION: it expresses a z=6 quasar
(cosmology), a 440 Ma stage boundary (geology), a Cambrian genus (paleontology),
a 2013 Chelyabinsk fireball (spaceflight) and a present-day earthquake on ONE
ruler -- same unit (Julian years), same origin (the Big Bang), each carrying a
propagated uncertainty in the SAME unit.

That single fact lets us ask a question no single discipline can ask alone:

    Across ~10 orders of magnitude of time depth, how does the *relative*
    precision of a dated event (uncertainty / age) scale with how far back
    in time it is?

This is an epistemological signal about the structure of human time knowledge.
Cosmologists quote Gyr, geologists Ma, historians years, seismologists seconds;
nobody can plot their *relative precisions* on one axis -- unless every event is
first reduced to a common absolute unit and origin. That reduction is exactly
what UBY provides via `uby_value` (years from the Big Bang) and a uniform
`original_error` / uncertainty in years.

What this script does
---------------------
1. Stream the real unified timeline (cosmology + astronomy + geology +
   paleontology + spaceflight) already annotated on the UBY axis.
2. For each event compute age = anchor - uby_value and, where an uncertainty is
   present, relative precision = uncertainty / age.
3. Per domain: count, age span, and the distribution of relative precision.
4. Global log-log scaling: fit log10(relative_uncertainty) vs log10(age_years)
   by ordinary least squares, reporting slope (scaling exponent) and R^2.
5. The "precision frontier": the best (smallest) relative uncertainty attainable
   in each decade of time depth -- the envelope of what humanity can know.
6. Quantify the UBY advantage explicitly: how many heterogeneous native units
   and ad-hoc conversions a traditional workflow would need versus one.

Research status: exploratory_cross_scale_signal_not_final_claim.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

ANCHOR_UBY = 13787002026.0  # Big Bang origin: 13.787 Ga + CE 2026 (Julian years)


def find_timeline() -> Path:
    here = Path(__file__).resolve().parent.parent
    candidate = here / "data" / "processed" / "uby_unified_timeline.csv"
    if not candidate.exists():
        raise FileNotFoundError(f"Expected unified timeline at {candidate}")
    return candidate


def ols(xs: list[float], ys: list[float]):
    """Ordinary least squares; returns (slope, intercept, r2) or None."""
    n = len(xs)
    if n < 3:
        return None
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    # R^2
    ybar = sy / n
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, r2


def main() -> int:
    t0 = time.perf_counter()
    path = find_timeline()
    print(f"[1/4] Streaming unified timeline {path.name} ...", flush=True)

    # Per-domain accumulators.
    domain_count: dict[str, int] = defaultdict(int)
    domain_age_min: dict[str, float] = {}
    domain_age_max: dict[str, float] = {}
    domain_relunc: dict[str, list[float]] = defaultdict(list)
    domain_units: dict[str, set] = defaultdict(set)

    # Global log-log points (subsampled for the fit to stay light).
    log_age: list[float] = []
    log_relunc: list[float] = []

    # Precision frontier: best (min) relative uncertainty per integer decade of age.
    frontier: dict[int, float] = {}

    total = 0
    used = 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            total += 1
            cat = (row.get("event_category") or "unknown").strip() or "unknown"
            unit = (row.get("original_time_unit") or "").strip()
            try:
                uby_value = float(row["uby_value"])
            except (KeyError, ValueError):
                continue
            age = ANCHOR_UBY - uby_value
            if age <= 0:
                continue
            domain_count[cat] += 1
            domain_units[cat].add(unit)
            domain_age_min[cat] = min(domain_age_min.get(cat, age), age)
            domain_age_max[cat] = max(domain_age_max.get(cat, age), age)

            err_raw = (row.get("original_error") or "").strip()
            if not err_raw:
                continue
            try:
                err = float(err_raw)
            except ValueError:
                continue
            if err <= 0:
                continue
            rel = err / age
            if rel <= 0:
                continue
            domain_relunc[cat].append(rel)
            used += 1

            la = math.log10(age)
            lr = math.log10(rel)
            # subsample the global fit to ~ every record (cheap enough), but cap
            if len(log_age) < 200000:
                log_age.append(la)
                log_relunc.append(lr)

            decade = int(math.floor(la))
            if decade not in frontier or rel < frontier[decade]:
                frontier[decade] = rel

    print(f"      rows total={total}, with usable uncertainty={used}, "
          f"domains={len(domain_count)}", flush=True)

    print("[2/4] Per-domain relative-precision summary ...", flush=True)

    def median(vals):
        s = sorted(vals)
        m = len(s)
        if m == 0:
            return None
        return s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2

    def yr_to_human(years: float) -> str:
        if years >= 1e9:
            return f"{years/1e9:.3f} Gyr"
        if years >= 1e6:
            return f"{years/1e6:.3f} Myr"
        if years >= 1e3:
            return f"{years/1e3:.3f} kyr"
        return f"{years:.2f} yr"

    domains = {}
    for cat in sorted(domain_count, key=lambda c: domain_age_max.get(c, 0), reverse=True):
        rels = domain_relunc.get(cat, [])
        med = median(rels)
        domains[cat] = {
            "event_count": domain_count[cat],
            "events_with_uncertainty": len(rels),
            "age_min_years": domain_age_min.get(cat),
            "age_max_years": domain_age_max.get(cat),
            "age_min_human": yr_to_human(domain_age_min[cat]) if cat in domain_age_min else None,
            "age_max_human": yr_to_human(domain_age_max[cat]) if cat in domain_age_max else None,
            "median_relative_uncertainty": med,
            "median_relative_uncertainty_pct": round(med * 100, 4) if med is not None else None,
            "best_relative_uncertainty": min(rels) if rels else None,
            "worst_relative_uncertainty": max(rels) if rels else None,
            "native_units_seen": sorted(u for u in domain_units[cat] if u),
        }

    print("[3/4] Global log-log scaling fit ...", flush=True)
    fit = ols(log_age, log_relunc)
    scaling = None
    if fit:
        slope, intercept, r2 = fit
        scaling = {
            "model": "log10(relative_uncertainty) = slope * log10(age_years) + intercept",
            "slope_scaling_exponent": round(slope, 4),
            "intercept": round(intercept, 4),
            "r_squared": round(r2, 4),
            "n_points": len(log_age),
            "interpretation": (
                "slope > 0 means relative precision DEGRADES with time depth "
                "(older events are known less precisely, in relative terms); "
                "slope ~ 0 would mean scale-invariant relative precision."
            ),
        }

    # Total age span covered (orders of magnitude) -- the headline UBY capability.
    all_ages_min = min(domain_age_min.values())
    all_ages_max = max(domain_age_max.values())
    orders_of_magnitude = math.log10(all_ages_max / all_ages_min) if all_ages_min > 0 else None

    print("[4/4] Building precision frontier and UBY-advantage accounting ...", flush=True)
    frontier_sorted = [
        {
            "age_decade_log10": d,
            "age_decade_human": yr_to_human(10 ** d),
            "best_relative_uncertainty": frontier[d],
            "best_relative_uncertainty_pct": round(frontier[d] * 100, 6),
        }
        for d in sorted(frontier)
    ]

    native_units_all = sorted({u for s in domain_units.values() for u in s if u})
    uby_advantage = {
        "events_unified": total,
        "domains_unified": len(domain_count),
        "time_orders_of_magnitude_on_one_axis": round(orders_of_magnitude, 2) if orders_of_magnitude else None,
        "age_span_youngest": yr_to_human(all_ages_min),
        "age_span_oldest": yr_to_human(all_ages_max),
        "heterogeneous_native_units_reconciled": native_units_all,
        "n_native_units": len(native_units_all),
        "why_traditional_fails": [
            "Cosmology events are native in redshift z (dimensionless); turning z into an age needs a cosmological model.",
            "Geology/paleontology events are native in Ma before present.",
            "Spaceflight/seismic events are native in calendar dates / SI seconds.",
            "Plotting their RELATIVE precisions on one axis requires a single absolute unit AND a single origin.",
            "UBY supplies both (Julian years from the Big Bang) plus a uniform uncertainty-in-years, so the cross-scale comparison becomes a single column operation instead of N bespoke conversions.",
        ],
    }

    elapsed = time.perf_counter() - t0

    report = {
        "database": "UBY cross-scale relative-time-precision scaling law",
        "description": (
            "A signal obtainable only on a unified cross-scale time axis: how the "
            "relative precision (uncertainty/age) of dated events scales across ~10 "
            "orders of magnitude of time depth, spanning cosmology to present day, "
            "using real UBY-annotated events from five domains."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "anchor_uby": ANCHOR_UBY,
        "inputs": {"uby_unified_timeline_csv": str(path)},
        "counts": {
            "rows_total": total,
            "rows_with_usable_uncertainty": used,
            "domains": len(domain_count),
        },
        "uby_advantage": uby_advantage,
        "per_domain_precision": domains,
        "global_scaling_law": scaling,
        "precision_frontier_by_decade": frontier_sorted,
        "research_status": "exploratory_cross_scale_signal_not_final_claim",
        "claim_boundary": [
            "original_error is taken as-provided per source; cross-domain error semantics are heterogeneous (1-sigma, half-interval, model-dependent) and are NOT harmonized here.",
            "The scaling fit mixes physically different uncertainty types; the slope is a descriptive cross-scale summary, not a single physical law.",
            "Cosmological relative uncertainties are model-dependent (LCDM-Planck2018) per the UBY Level 3 convention.",
            "The real, defensible result is the DEMONSTRATION that one axis makes the cross-scale comparison computable at all.",
        ],
        "build_performance": {
            "wall_seconds": elapsed,
            "rows_per_second": total / elapsed if elapsed > 0 else None,
        },
    }

    out_dir = path.parent
    report_path = out_dir / "cross_scale_precision_law_report.json"
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    # Console summary.
    print("\n=== CROSS-SCALE PRECISION LAW (UBY-only signal) ===")
    print(f"Unified events: {total} across {len(domain_count)} domains")
    if orders_of_magnitude:
        print(f"Time depth on ONE axis: {yr_to_human(all_ages_min)} -> {yr_to_human(all_ages_max)} "
              f"({orders_of_magnitude:.1f} orders of magnitude)")
    print(f"Heterogeneous native units reconciled: {native_units_all}")
    print("\n-- Per-domain median relative precision (uncertainty/age) --")
    for cat, d in domains.items():
        if d["median_relative_uncertainty_pct"] is not None:
            print(f"  {cat:14s}: age {d['age_min_human']:>12s} .. {d['age_max_human']:>10s} | "
                  f"median rel.unc = {d['median_relative_uncertainty_pct']:.4f}%  "
                  f"(n={d['events_with_uncertainty']})")
    if scaling:
        print(f"\n-- Global log-log scaling --")
        print(f"  log10(rel.unc) = {scaling['slope_scaling_exponent']} * log10(age) "
              f"+ {scaling['intercept']}  (R^2={scaling['r_squared']}, n={scaling['n_points']})")
        print(f"  -> scaling exponent {scaling['slope_scaling_exponent']}: "
              f"{'precision degrades with depth' if scaling['slope_scaling_exponent']>0.05 else ('roughly scale-invariant' if abs(scaling['slope_scaling_exponent'])<=0.05 else 'precision improves with depth (!)')}")
    print(f"\nWall time: {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
