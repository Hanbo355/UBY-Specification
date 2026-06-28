"""Demonstrate UBY's irreplaceable strength: a TRUE cross-scale precision law.

Why this script exists
-----------------------
A first attempt that read `uby_unified_timeline.csv` revealed that this "unified"
file actually contains only two adjacent domains (geology + paleontology, both
native in Ma-before-present, oldest 4.567 Gyr). On those two scales UBY adds
little, because plain Ma already works. That is NOT where UBY earns its keep.

UBY's unique value appears only when events span MANY orders of magnitude with
INCOMPATIBLE native units. So here we bypass the partial unified file and read
the raw per-domain UBY-annotated exports directly, reconciling genuinely
heterogeneous natives onto ONE axis:

  * cosmology   : SIMBAD high-redshift objects, native unit = redshift z
                  (dimensionless; needs a cosmological model to become an age)
  * geology     : ICS chronostratigraphic chart, native unit = Ma BP
  * spaceflight : NASA/JPL CNEOS fireballs, native unit = UTC calendar timestamp
  * seismology  : USGS earthquakes, native unit = UTC timestamp / SI seconds

A z=24 quasar (~13.5 Gyr ago) and a fireball from last week (~days ago) differ
in time depth by ~10 orders of magnitude and have NOTHING in common in their
native units. The only reason we can put their RELATIVE precisions on a single
log axis is that UBY reduces every one of them to Julian years from the Big Bang
plus an uncertainty in the same unit.

Signal mined
------------
The relative-precision scaling law: log10(uncertainty/age) vs log10(age) across
the full observable record, plus the per-decade "precision frontier" (the best
relative precision humanity can attach to an event of a given age).

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

ANCHOR_UBY = 13787002026.0

# Representative 1-sigma-ish uncertainty (in years) when a record carries no
# explicit uncertainty column but its precision level implies a scale.
# Level 1 events here are timestamped to ~seconds.
ONE_SECOND_YEARS = 1.0 / (365.25 * 86400.0)

# Per-domain ingestion config. Each entry lists the file, the domain label, the
# uby_value column, and an ordered list of candidate uncertainty-year columns;
# if none are present we fall back to a precision-level-based representative.
DOMAIN_CONFIG = [
    {
        "domain": "cosmology",
        "file": "simbad_high_redshift_objects_uby.csv",
        "uby_col": "uby_value",
        "unc_cols": ["uncertainty_years"],
        "fallback_years": None,
        "native_unit": "redshift z",
        "max_rows": None,
    },
    {
        "domain": "geology",
        "file": "ics_chart_uby.csv",
        "uby_col": "uby_value",
        "unc_cols": ["uncertainty_years", "original_error"],
        "fallback_years": None,
        "native_unit": "Ma BP",
        "max_rows": None,
    },
    {
        "domain": "spaceflight",
        "file": "nasa_jpl_cneos_fireballs_uby.csv",
        "uby_col": "uby_value",
        "unc_cols": ["uncertainty_years"],
        "fallback_years": ONE_SECOND_YEARS,  # UTC timestamp ~ second precision
        "native_unit": "UTC timestamp",
        "max_rows": None,
    },
    {
        "domain": "seismology",
        "file": "usgs_earthquakes_uby_benchmark.csv",
        "uby_col": "uby_value",
        "unc_cols": ["uncertainty_years"],
        "fallback_years": ONE_SECOND_YEARS,  # USGS origin times ~ sub-second
        "native_unit": "UTC timestamp / SI seconds",
        "max_rows": 50000,  # large file; sample is plenty for a scaling law
    },
]


def find_processed() -> Path:
    here = Path(__file__).resolve().parent.parent
    return here / "data" / "processed"


def ols(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    ybar = sy / n
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, r2


def yr_to_human(years: float) -> str:
    if years >= 1e9:
        return f"{years/1e9:.3f} Gyr"
    if years >= 1e6:
        return f"{years/1e6:.3f} Myr"
    if years >= 1e3:
        return f"{years/1e3:.3f} kyr"
    if years >= 1.0:
        return f"{years:.3f} yr"
    return f"{years*365.25:.3f} days"


def median(vals):
    s = sorted(vals)
    m = len(s)
    if m == 0:
        return None
    return s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2


def main() -> int:
    t0 = time.perf_counter()
    proc = find_processed()

    points = []  # (domain, age_years, rel_unc)
    domain_stats = {}
    frontier: dict[int, float] = {}
    native_units = {}

    for cfg in DOMAIN_CONFIG:
        path = proc / cfg["file"]
        dom = cfg["domain"]
        native_units[dom] = cfg["native_unit"]
        if not path.exists():
            print(f"[skip] {dom}: missing {path.name}", flush=True)
            continue
        print(f"[load] {dom:11s} <- {path.name}", flush=True)
        rels = []
        ages = []
        n_rows = 0
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            unc_col = None
            for col in cfg["unc_cols"]:
                if reader.fieldnames and col in reader.fieldnames:
                    unc_col = col
                    break
            for row in reader:
                if cfg["max_rows"] and n_rows >= cfg["max_rows"]:
                    break
                try:
                    uby_value = float(row[cfg["uby_col"]])
                except (KeyError, ValueError, TypeError):
                    continue
                age = ANCHOR_UBY - uby_value
                if age <= 0:
                    continue
                # uncertainty in years
                err = None
                if unc_col:
                    raw = (row.get(unc_col) or "").strip()
                    if raw:
                        try:
                            err = float(raw)
                        except ValueError:
                            err = None
                if (err is None or err <= 0) and cfg["fallback_years"]:
                    err = cfg["fallback_years"]
                if err is None or err <= 0:
                    continue
                rel = err / age
                if rel <= 0:
                    continue
                n_rows += 1
                ages.append(age)
                rels.append(rel)
                points.append((dom, age, rel))
                la = math.log10(age)
                decade = int(math.floor(la))
                if decade not in frontier or rel < frontier[decade]:
                    frontier[decade] = rel
        if rels:
            domain_stats[dom] = {
                "events_used": len(rels),
                "native_unit": cfg["native_unit"],
                "age_min_years": min(ages),
                "age_max_years": max(ages),
                "age_min_human": yr_to_human(min(ages)),
                "age_max_human": yr_to_human(max(ages)),
                "median_relative_uncertainty_pct": round(median(rels) * 100, 6),
                "best_relative_uncertainty_pct": round(min(rels) * 100, 6),
                "worst_relative_uncertainty_pct": round(max(rels) * 100, 6),
            }
            print(f"        {dom:11s}: n={len(rels):6d}  "
                  f"age {yr_to_human(min(ages))} .. {yr_to_human(max(ages))}  "
                  f"median rel.unc={median(rels)*100:.4f}%", flush=True)

    if not points:
        print("No usable cross-scale points found.")
        return 1

    all_ages = [p[1] for p in points]
    a_min, a_max = min(all_ages), max(all_ages)
    oom = math.log10(a_max / a_min)

    # Global scaling fit.
    log_age = [math.log10(p[1]) for p in points]
    log_rel = [math.log10(p[2]) for p in points]
    fit = ols(log_age, log_rel)
    scaling = None
    if fit:
        slope, intercept, r2 = fit
        scaling = {
            "model": "log10(relative_uncertainty) = slope * log10(age_years) + intercept",
            "slope_scaling_exponent": round(slope, 4),
            "intercept": round(intercept, 4),
            "r_squared": round(r2, 4),
            "n_points": len(points),
        }

    frontier_sorted = [
        {
            "age_decade_log10": d,
            "age_decade_human": yr_to_human(10 ** d),
            "best_relative_uncertainty_pct": round(frontier[d] * 100, 8),
        }
        for d in sorted(frontier)
    ]

    elapsed = time.perf_counter() - t0

    report = {
        "database": "UBY TRUE cross-scale relative-time-precision law",
        "description": (
            "Relative-precision scaling across the full observable record, built "
            "by reconciling genuinely heterogeneous native units (redshift, Ma BP, "
            "UTC timestamps, SI seconds) from four real domains onto one UBY axis."
        ),
        "generated_by": "uby-time/0.1.0",
        "uby_version": "0.1.0",
        "anchor_uby": ANCHOR_UBY,
        "uby_advantage": {
            "events_unified": len(points),
            "domains_unified": len(domain_stats),
            "time_orders_of_magnitude_on_one_axis": round(oom, 2),
            "age_span_youngest": yr_to_human(a_min),
            "age_span_oldest": yr_to_human(a_max),
            "native_units_reconciled": {d: native_units[d] for d in domain_stats},
            "why_traditional_fails": [
                "redshift z is dimensionless and needs a cosmological model to become a time.",
                "Ma BP, UTC timestamps and SI seconds share neither unit nor origin.",
                "Comparing their RELATIVE precisions requires one absolute unit and one origin for all.",
                "UBY provides exactly that, turning an otherwise impossible plot into a single column operation.",
            ],
        },
        "per_domain": domain_stats,
        "global_scaling_law": scaling,
        "precision_frontier_by_decade": frontier_sorted,
        "research_status": "exploratory_cross_scale_signal_not_final_claim",
        "claim_boundary": [
            "Cross-domain uncertainty semantics are heterogeneous (1-sigma, model-dependent, timestamp precision) and are NOT harmonized; the slope is descriptive.",
            "Cosmological ages/uncertainties are LCDM-Planck2018 model-dependent (UBY Level 3).",
            "Level 1 timestamp uncertainties use a representative ~1 s where no explicit column exists.",
            "The defensible result is that one axis makes a 10-order-of-magnitude precision comparison computable at all.",
        ],
        "build_performance": {
            "wall_seconds": elapsed,
            "events_per_second": len(points) / elapsed if elapsed > 0 else None,
        },
    }

    out = proc / "true_cross_scale_precision_report.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print("\n=== TRUE CROSS-SCALE PRECISION LAW (the UBY-only signal) ===")
    print(f"Unified events: {len(points)} across {len(domain_stats)} domains")
    print(f"Time depth on ONE axis: {yr_to_human(a_min)} .. {yr_to_human(a_max)} "
          f"({oom:.1f} ORDERS OF MAGNITUDE)")
    print("Native units reconciled:")
    for d in domain_stats:
        print(f"    {d:11s}: {native_units[d]}")
    print("\n-- Per-domain median relative precision --")
    for d, s in sorted(domain_stats.items(), key=lambda kv: kv[1]["age_max_years"], reverse=True):
        print(f"  {d:11s}: age {s['age_min_human']:>11s} .. {s['age_max_human']:>10s} | "
              f"median rel.unc={s['median_relative_uncertainty_pct']:.4f}%  (n={s['events_used']})")
    if scaling:
        print(f"\n-- Global log-log scaling (n={scaling['n_points']}) --")
        print(f"  log10(rel.unc) = {scaling['slope_scaling_exponent']}*log10(age) "
              f"+ {scaling['intercept']}  (R^2={scaling['r_squared']})")
    print("\n-- Precision frontier (best relative precision per age decade) --")
    for f in frontier_sorted:
        print(f"  {f['age_decade_human']:>11s}: {f['best_relative_uncertainty_pct']}%")

    # Plot the cross-scale precision law (log-log).
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        colors = {
            "cosmology": "#d62728",
            "geology": "#2ca02c",
            "spaceflight": "#1f77b4",
            "seismology": "#9467bd",
        }
        fig, ax = plt.subplots(figsize=(10, 7))
        for dom in domain_stats:
            xs = [math.log10(p[1]) for p in points if p[0] == dom]
            ys = [math.log10(p[2]) for p in points if p[0] == dom]
            if len(xs) > 2000:
                step = max(1, len(xs) // 2000)
                xs = xs[::step]
                ys = ys[::step]
            ax.scatter(xs, ys, s=10, alpha=0.45,
                       color=colors.get(dom, "#777777"),
                       label=f"{dom} (n={domain_stats[dom]['events_used']})")
        if scaling:
            xr = [min(log_age), max(log_age)]
            yr = [scaling["slope_scaling_exponent"] * x + scaling["intercept"] for x in xr]
            ax.plot(xr, yr, "k--", lw=2,
                    label=(f"OLS fit: slope={scaling['slope_scaling_exponent']}, "
                           f"R\u00b2={scaling['r_squared']}"))
        fx = [f["age_decade_log10"] for f in frontier_sorted]
        fy = [math.log10(f["best_relative_uncertainty_pct"] / 100.0) for f in frontier_sorted]
        ax.plot(fx, fy, "o-", color="orange", lw=1.6, ms=6,
                label="precision frontier (best per decade)")

        # Reference annotations for human time anchors.
        for label, age_yr in [("days", 0.01), ("1 yr", 1.0), ("1 Myr", 1e6),
                              ("66 Ma (K-Pg)", 66e6), ("13.8 Gyr (Big Bang)", 13.8e9)]:
            ax.axvline(math.log10(age_yr), color="grey", ls=":", lw=0.6, alpha=0.5)
            ax.text(math.log10(age_yr), ax.get_ylim()[1], label, rotation=90,
                    va="top", ha="right", fontsize=7, color="grey")

        ax.set_xlabel("log\u2081\u2080( event age / years )   \u2014 measured on the unified UBY axis (Big Bang origin)")
        ax.set_ylabel("log\u2081\u2080( relative time uncertainty = \u03c3 / age )")
        ax.set_title(
            "Cross-scale time-precision law on one UBY axis\n"
            f"{len(points)} real events, 4 domains, {oom:.1f} orders of magnitude "
            "(redshift \u2194 Ma BP \u2194 UTC \u2194 SI seconds)"
        )
        ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        png = proc / "true_cross_scale_precision_law.png"
        fig.savefig(png, dpi=140)
        plt.close(fig)
        print(f"\nSaved plot -> {png}")
    except Exception as exc:  # pragma: no cover - plotting is optional
        print(f"\nPlot skipped ({type(exc).__name__}: {exc})")

    print(f"\nWall time: {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
