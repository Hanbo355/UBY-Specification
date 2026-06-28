#!/usr/bin/env python3
"""
Verify integration of the 4 new external databases (GVP, NASA Exoplanet,
ITRDB, Neotoma) into the unified UBY timeline database.

Generates a verification report:
- Per-source counts
- UBY value ranges (min/max/median)
- Sanity checks (e.g., stellar age <= universe age)
- Cross-domain sample queries
- UBY axis coverage summary
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQLITE_OUT = ROOT / "data" / "processed" / "uby_unified_timeline.sqlite"
REPORT_OUT = ROOT / "data" / "processed" / "external_databases_integration_report.json"


def main() -> int:
    if not SQLITE_OUT.exists():
        print(f"[ERROR] SQLite DB not found: {SQLITE_OUT}")
        return 1

    conn = sqlite3.connect(SQLITE_OUT)

    report: dict[str, object] = {
        "database": str(SQLITE_OUT),
        "checks": {},
    }

    # 1. Total count
    total = conn.execute("SELECT COUNT(*) FROM uby_events").fetchone()[0]
    report["checks"]["total_events"] = total
    print(f"Total events in unified DB: {total}")

    # 2. New source counts
    new_sources = {
        "Smithsonian GVP Holocene Volcanoes (v5.3.6)": "geology",
        "NASA Exoplanet Archive (confirmed planets)": "astronomy",
        "NOAA ITRDB v7.13 tree-ring chronologies": "paleoclimate",
        "Neotoma Paleoecology Database": "paleoecology",
    }
    per_source_counts = {}
    for src_name, category in new_sources.items():
        row = conn.execute(
            "SELECT COUNT(*) FROM uby_events WHERE source_dataset LIKE ?",
            (src_name + "%",),
        ).fetchone()
        per_source_counts[src_name] = {"count": row[0], "expected_category": category}
    report["checks"]["new_sources"] = per_source_counts
    print("\nNew source counts:")
    for k, v in per_source_counts.items():
        print(f"  - {k}: {v['count']}")

    # 3. UBY range per new source
    print("\nUBY range per new source:")
    uby_ranges = {}
    for src_name in new_sources:
        rows = conn.execute(
            "SELECT MIN(uby_value), MAX(uby_value), COUNT(*) FROM uby_events WHERE source_dataset LIKE ?",
            (src_name + "%",),
        ).fetchone()
        min_uby, max_uby, count = rows
        uby_ranges[src_name] = {"min_uby": min_uby, "max_uby": max_uby, "count": count}
        print(f"  - {src_name}: count={count}, UBY range=[{min_uby}, {max_uby}]")

    report["checks"]["uby_ranges"] = uby_ranges

    # 4. Sanity checks: negative UBY means before Big Bang (anomaly)
    print("\nSanity checks:")
    anomalies = {}

    # 4a. Stellar age <= 13.8 Gyr (universe age)
    rows = conn.execute(
        """
        SELECT source_record_id, original_time_value, uby_value
        FROM uby_events
        WHERE source_dataset LIKE 'NASA Exoplanet%'
          AND original_time_unit='gyr'
          AND CAST(original_time_value AS REAL) > 13.8
        ORDER BY CAST(original_time_value AS REAL) DESC
        LIMIT 5
        """,
    ).fetchall()
    anomalies["stellar_age_gt_universe_age"] = {
        "count": len(rows),
        "sample": [{"record_id": r[0], "value": r[1], "uby": r[2]} for r in rows],
    }
    print(f"  - stellar age > 13.8 Gyr: {len(rows)} records (capped to 5 shown)")

    # 4b. GVP eruptions in Holocene (UBY should be near anchor)
    ANCHOR_UBY = 13787002026.0  # UBY value at 2026-01-01 (anchor)

    rows = conn.execute(
        """
        SELECT MIN(uby_value), MAX(uby_value)
        FROM uby_events
        WHERE source_dataset LIKE 'Smithsonian%'
        """,
    ).fetchone()
    gvp_min, gvp_max = rows
    anomalies["gvp_range_deviation_from_anchor"] = {
        "gvp_min_uby": gvp_min,
        "gvp_max_uby": gvp_max,
        "anchor_uby": ANCHOR_UBY,
        "max_deviation_years": max(abs(gvp_min - ANCHOR_UBY), abs(gvp_max - ANCHOR_UBY)),
    }
    print(f"  - GVP UBY range: [{gvp_min}, {gvp_max}]")
    print(f"    deviation from anchor (2026): {max(abs(gvp_min - ANCHOR_UBY), abs(gvp_max - ANCHOR_UBY))} years")

    # 4c. ITRDB chronologies within ~10000 yr of anchor
    rows = conn.execute(
        """
        SELECT MIN(uby_value), MAX(uby_value)
        FROM uby_events
        WHERE source_dataset LIKE 'NOAA ITRDB%'
        """,
    ).fetchone()
    itrdb_min, itrdb_max = rows
    anomalies["itrdb_range"] = {
        "min_uby": itrdb_min,
        "max_uby": itrdb_max,
        "span_years": itrdb_max - itrdb_min,
    }
    print(f"  - ITRDB span: {itrdb_max - itrdb_min} years")

    # 5. Cross-domain query: events within last 1000 years
    print("\nCross-domain query: events in last 1000 years (multiple categories):")
    cross_domain = []
    for row in conn.execute(
        """
        SELECT event_category, COUNT(*) AS n
        FROM uby_events
        WHERE uby_value > ? - 1000
        GROUP BY event_category
        ORDER BY n DESC
        """,
        (ANCHOR_UBY,),
    ):
        cross_domain.append({"category": row[0], "count": row[1]})
        print(f"  - {row[0]}: {row[1]}")
    report["checks"]["last_1000_years_by_category"] = cross_domain

    # 6. Full cross-scale coverage summary
    print("\nFull UBY axis coverage:")
    coverage = []
    for row in conn.execute(
        """
        SELECT
            event_category,
            COUNT(*) AS n,
            MIN(uby_value) AS min_uby,
            MAX(uby_value) AS max_uby
        FROM uby_events
        GROUP BY event_category
        ORDER BY min_uby
        """,
    ):
        entry = {
            "category": row[0],
            "count": row[1],
            "min_uby": row[2],
            "max_uby": row[3],
            "min_age_years_before_anchor": ANCHOR_UBY - row[2],
            "max_age_years_before_anchor": ANCHOR_UBY - row[3],
        }
        coverage.append(entry)
        print(
            f"  - {row[0]}: count={row[1]}, "
            f"range=[{ANCHOR_UBY - row[2]:,.0f} to {ANCHOR_UBY - row[3]:,.0f} yr BP]"
        )
    report["checks"]["uby_coverage_by_category"] = coverage

    # 7. Cross-scale JOIN example (the UBY axis advantage):
    #    Find astronomical + geological events within 100 years of each other
    print("\nCross-domain proximity example (astronomy vs geology, within 100 yr):")
    proximity = []
    for row in conn.execute(
        """
        SELECT
            a.event_name AS astro_event,
            b.event_name AS geo_event,
            ABS(a.uby_value - b.uby_value) AS delta_years,
            a.source_dataset AS astro_src,
            b.source_dataset AS geo_src
        FROM uby_events a
        JOIN uby_events b
          ON a.event_category IN ('astronomy', 'cosmology')
         AND b.event_category = 'geology'
         AND ABS(a.uby_value - b.uby_value) < 100
        ORDER BY delta_years
        LIMIT 5
        """,
    ):
        proximity.append({
            "astro_event": row[0],
            "geo_event": row[1],
            "delta_years": row[2],
            "astro_src": row[3],
            "geo_src": row[4],
        })
    for p in proximity:
        print(f"  - {p['astro_event']} <-> {p['geo_event']} (Δ={p['delta_years']:.1f} yr)")
    report["checks"]["cross_domain_proximity_examples"] = proximity

    conn.close()

    REPORT_OUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nReport: {REPORT_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
