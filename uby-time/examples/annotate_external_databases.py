#!/usr/bin/env python3
"""
Annotate 4 newly-downloaded external databases with UBY time values.

Processes:
  - Smithsonian GVP Holocene volcanoes (BCE/CE eruption years)
  - NASA Exoplanet Archive confirmed planets (discovery year + stellar age)
  - NOAA ITRDB tree-ring chronologies (annual, decadal format)
  - Neotoma paleoecology sites (radiocarbon/cal yr BP from collection units)

Each record's native chronology is converted to the UBY axis (years from
the Big Bang) using the UBY anchor (2026-01-01T00:00:00Z, UBY=13787002026.0).

Output:
- data/processed/external_databases_uby.csv
- data/processed/external_databases_uby_metadata.json
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.constants import (
    DEFAULT_ANCHOR_UBY as ANCHOR_UBY,
    DEFAULT_ANCHOR_ID,
    DEFAULT_ANCHOR_ISO,
    DEFAULT_ANCHOR_JD,
    GENERATED_BY,
    UBY_SPEC_VERSION,
)

RAW_DIR = ROOT / "data" / "raw" / "external"
PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "external_databases_uby.csv"
METADATA_OUT = PROCESSED_DIR / "external_databases_uby_metadata.json"

MODEL_VERSION = "none"


# ---------------------------------------------------------------------------
# UBY converters
# ---------------------------------------------------------------------------

def _decimal_year_to_uby(decimal_year: float) -> float:
    """Convert a decimal calendar year (CE) to UBY."""
    return float(ANCHOR_UBY) + (decimal_year - 2026.0)


def _yr_bp_to_uby(yr: float) -> float:
    """Convert years-before-present (present=anchor 2026) to UBY."""
    return float(ANCHOR_UBY) - yr


def _gyr_to_uby(gyr: float) -> float:
    """Convert Gyr (billion years before present) to UBY."""
    return float(ANCHOR_UBY) - gyr * 1.0e9


def _bce_ce_to_decimal_year(text: str) -> float | None:
    """Parse Smithsonian 'Last Known Eruption' field.

    Examples:
      '8300 BCE'  -> -8299.0  (year -8299 CE = 8300 BCE)
      '2025 CE'   -> 2025.0
      'Unknown'   -> None
      'D1' etc.   -> None
    """
    text = text.strip()
    if not text or text.lower() in ("unknown", "none"):
        return None
    parts = text.split()
    if len(parts) < 2:
        return None
    try:
        year = int(parts[0])
    except ValueError:
        return None
    era = parts[1].upper()
    if era == "BCE":
        # BCE year N corresponds to CE year -(N-1) (astronomical year numbering)
        # 1 BCE = year 0, 2 BCE = year -1, ... N BCE = year -(N-1)
        return float(-(year - 1))
    elif era in ("CE", "BP"):
        return float(year)
    return None


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_gvp(path: Path):
    """Smithsonian GVP Holocene volcano list CSV.

    Row 1: title banner, Row 2: header, Row 3+: data.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if len(rows) < 3:
        return
    header = rows[1]
    # Find column indices
    idx = {name: i for i, name in enumerate(header)}
    for row in rows[2:]:
        if not row or not row[0]:
            continue
        rec = {
            "volcano_number": row[idx.get("Volcano Number", 0)] if idx.get("Volcano Number", 0) < len(row) else "",
            "volcano_name": row[idx.get("Volcano Name", 1)] if idx.get("Volcano Name", 1) < len(row) else "",
            "country": row[idx.get("Country", 2)] if idx.get("Country", 2) < len(row) else "",
            "volcano_type": row[idx.get("Primary Volcano Type", 6)] if idx.get("Primary Volcano Type", 6) < len(row) else "",
            "activity_evidence": row[idx.get("Activity Evidence", 7)] if idx.get("Activity Evidence", 7) < len(row) else "",
            "last_eruption": row[idx.get("Last Known Eruption", 8)] if idx.get("Last Known Eruption", 8) < len(row) else "",
            "latitude": row[idx.get("Latitude", 9)] if idx.get("Latitude", 9) < len(row) else "",
            "longitude": row[idx.get("Longitude", 10)] if idx.get("Longitude", 10) < len(row) else "",
            "elevation_m": row[idx.get("Elevation (m)", 11)] if idx.get("Elevation (m)", 11) < len(row) else "",
            "tectonic_setting": row[idx.get("Tectonic Setting", 12)] if idx.get("Tectonic Setting", 12) < len(row) else "",
            "rock_type": row[idx.get("Dominant Rock Type", 13)] if idx.get("Dominant Rock Type", 13) < len(row) else "",
        }
        decimal_year = _bce_ce_to_decimal_year(rec["last_eruption"])
        if decimal_year is None:
            continue
        yield {
            "decimal_year": decimal_year,
            "value": rec["elevation_m"],
            "value_label": "volcano_elevation",
            "value_unit": "m",
            "description": (
                f"Volcano {rec['volcano_name']} ({rec['country']}, type={rec['volcano_type']}); "
                f"last known eruption {rec['last_eruption']}; "
                f"lat={rec['latitude']}, lon={rec['longitude']}, elev={rec['elevation_m']}m; "
                f"tectonic={rec['tectonic_setting']}, rock={rec['rock_type']}"
            ),
            "source_record_id": rec["volcano_number"],
        }


def parse_nasa_exoplanet(path: Path):
    """NASA Exoplanet Archive confirmed planets CSV.

    Time-bearing columns:
      - disc_year: discovery year (CE)
      - st_age: stellar age (Gyr)
    """
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Primary record: discovery event
            disc_year_str = row.get("disc_year", "").strip()
            pl_name = row.get("pl_name", "").strip()
            hostname = row.get("hostname", "").strip()
            method = row.get("discoverymethod", "").strip()
            facility = row.get("disc_facility", "").strip()
            try:
                disc_year = float(disc_year_str)
            except ValueError:
                continue
            description = (
                f"Exoplanet {pl_name} around {hostname}; "
                f"discovery method={method}, facility={facility}, year={disc_year_str}"
            )
            yield {
                "decimal_year": disc_year,
                "value": "1",  # discovery event marker
                "value_label": "exoplanet_discovery",
                "value_unit": "event",
                "description": description,
                "source_record_id": pl_name,
            }

            # Optional secondary record: stellar age
            st_age_str = row.get("st_age", "").strip()
            if st_age_str:
                try:
                    st_age_gyr = float(st_age_str)
                    if 0 < st_age_gyr < 20:  # sanity range
                        yield {
                            "gyr": st_age_gyr,
                            "value": st_age_str,
                            "value_label": "stellar_age",
                            "value_unit": "Gyr",
                            "description": (
                                f"Host star {hostname} age = {st_age_str} Gyr "
                                f"(planet {pl_name}); teff={row.get('st_teff', '')}K"
                            ),
                            "source_record_id": f"{pl_name}_star_age",
                        }
                except ValueError:
                    pass


def _parse_itrdb_header(path: Path) -> dict | None:
    """Parse first 3 header lines of a .crn file (Tucson decadal format).

    Returns dict with keys: site_id, name, country, species, lat, lon, alt,
    start_year, end_year.
    """
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = [fh.readline() for _ in range(3)]
    except OSError:
        return None
    if len(lines) < 3:
        return None

    # Line 1: cols 1-6 site_id, 9-30 site name, 41-45 species, 62-65 elevation-ish
    # Line 2: cols 1-6 site_id, 9-25 country, 25-40 species name, 41-45 lat, ...
    # Line 3: cols 1-6 site_id, investigator
    # The exact column layout varies; use field positions per ITRDB spec.
    line1 = lines[0]
    line2 = lines[1]
    line3 = lines[2]

    site_id = line1[:6].strip()
    name = line1[8:30].strip() if len(line1) > 8 else ""
    species_code = line1[40:44].strip() if len(line1) > 40 else ""

    country = line2[8:24].strip() if len(line2) > 8 else ""
    species_name = line2[24:40].strip() if len(line2) > 24 else ""
    # Try to extract lat/lon from line 2 columns 40-48 and 48-56
    lat_str = line2[40:48].strip() if len(line2) > 40 else ""
    lon_str = line2[48:56].strip() if len(line2) > 48 else ""
    # Start/end year are typically in line 2 columns ~60-70
    year_part = line2[60:75] if len(line2) > 60 else ""
    start_year = end_year = None
    if year_part:
        year_tokens = year_part.split()
        if len(year_tokens) >= 2:
            try:
                start_year = int(year_tokens[0])
                end_year = int(year_tokens[1])
            except ValueError:
                pass

    # Elevation from line1 cols 41-45 (could be in line2 too)
    elev_str = ""
    if len(line2) > 40:
        # Try to find an "M" suffix elevation in line2
        for token in line2.split():
            if token.endswith("M") and token[:-1].isdigit():
                elev_str = token[:-1]
                break

    return {
        "site_id": site_id,
        "name": name,
        "country": country,
        "species_code": species_code,
        "species_name": species_name,
        "lat": lat_str,
        "lon": lon_str,
        "elev_m": elev_str,
        "start_year": start_year,
        "end_year": end_year,
    }


def parse_itrdb(base_dir: Path):
    """Iterate all .crn chronology files; one record per site (start year)."""
    regions = ["africa", "asia", "australia", "canada", "europe",
               "mexico", "southamerica", "usa"]
    for region in regions:
        region_dir = base_dir / region
        if not region_dir.exists():
            continue
        for crn_path in sorted(region_dir.glob("*.crn")):
            header = _parse_itrdb_header(crn_path)
            if not header or header["start_year"] is None:
                continue
            description = (
                f"ITRDB tree-ring chronology site {header['site_id']} "
                f"({header['name']}, {header['country']}, region={region}); "
                f"species={header['species_code']}/{header['species_name']}; "
                f"lat={header['lat']}, lon={header['lon']}, elev={header['elev_m']}m; "
                f"chronology span {header['start_year']}-{header['end_year']}; "
                f"file={crn_path.name}"
            )
            yield {
                "decimal_year": float(header["start_year"]),
                "value": str(header["end_year"]),
                "value_label": "chronology_end_year",
                "value_unit": "year",
                "description": description,
                "source_record_id": header["site_id"],
            }


def parse_neotoma(path: Path):
    """Neotoma sites JSONL. Extract earliest sample age from collection units."""
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            site_id = obj.get("siteid")
            site_name = obj.get("sitename", "")
            site_desc = obj.get("sitedescription", "") or ""
            altitude = obj.get("altitude")

            # Extract lat/lon from geography
            geo = obj.get("geography") or {}
            coords = geo.get("coordinates") if isinstance(geo, dict) else None
            lon = lat = ""
            if coords and len(coords) >= 2:
                lon, lat = str(coords[0]), str(coords[1])

            # Find the earliest sample age across all collection units
            earliest_age = None
            dataset_types = set()
            for cu in obj.get("collectionunits", []) or []:
                for ds in cu.get("datasets", []) or []:
                    ds_type = ds.get("datasettype", "")
                    if ds_type:
                        dataset_types.add(ds_type)
                    # Look for age info in dataset
                    for key in ("ageyoung", "ageold", "age_range_young",
                                "age_range_old"):
                        v = ds.get(key)
                        if v is None:
                            continue
                        try:
                            age = float(v)
                        except (TypeError, ValueError):
                            continue
                        # 'ageold' is the older (larger) bound
                        if key in ("ageold", "age_range_old") and (earliest_age is None or age > earliest_age):
                            earliest_age = age
                        elif key in ("ageyoung", "age_range_young") and (earliest_age is None or age > earliest_age):
                            earliest_age = age

            ds_types_str = "; ".join(sorted(dataset_types)) if dataset_types else "unknown"
            description = (
                f"Neotoma site {site_id} ({site_name}); "
                f"lat={lat}, lon={lon}, altitude={altitude}m; "
                f"dataset types=[{ds_types_str}]; "
                f"earliest sample age={earliest_age} yr BP; "
                f"desc={site_desc[:80]}"
            )

            if earliest_age is not None:
                yield {
                    "yr_bp": earliest_age,
                    "value": str(earliest_age),
                    "value_label": "earliest_sample_age",
                    "value_unit": "yr_bp",
                    "description": description,
                    "source_record_id": str(site_id),
                }
            else:
                # No age info; record as a "present-day" reference event
                yield {
                    "decimal_year": 2026.0,
                    "value": "0",
                    "value_label": "site_present_reference",
                    "value_unit": "event",
                    "description": description,
                    "source_record_id": str(site_id),
                }


# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "key": "gvp_holocene_volcanoes",
        "subdir": "gvp",
        "file": "holocene_volcano_list.csv",
        "parser": parse_gvp,
        "source_dataset": "Smithsonian GVP Holocene Volcanoes (v5.3.6)",
        "source_doi": "",
        "source_uri": "https://volcano.si.edu/",
        "event_category": "geological",
        "event_subcategory": "volcanic_eruption",
        "original_time_unit": "decimal_year",
        "precision_level": "Level 2",
        "time_uncertainty_years": "1",
        "uby_converter": lambda rec: _decimal_year_to_uby(rec["decimal_year"]),
        "original_time_extractor": lambda rec: str(rec["decimal_year"]),
        "attribution": "Global Volcanism Program, 2025. Volcanoes of the World (v.5.3.6; 28 Jun 2026). Smithsonian Institution.",
    },
    {
        "key": "nasa_exoplanets",
        "subdir": "nasa_exoplanets",
        "file": "confirmed_planets_default.csv",
        "parser": parse_nasa_exoplanet,
        "source_dataset": "NASA Exoplanet Archive (confirmed planets)",
        "source_doi": "",
        "source_uri": "https://exoplanetarchive.ipac.caltech.edu/",
        "event_category": "astronomical",
        "event_subcategory": "exoplanet_discovery",
        "original_time_unit": "decimal_year",  # will be overridden for stellar_age rows
        "precision_level": "Level 1",
        "time_uncertainty_years": "0.5",
        "uby_converter": lambda rec: (
            _decimal_year_to_uby(rec["decimal_year"]) if "decimal_year" in rec
            else _gyr_to_uby(rec["gyr"])
        ),
        "original_time_extractor": lambda rec: (
            str(rec["decimal_year"]) if "decimal_year" in rec
            else f"{rec['gyr']} Gyr"
        ),
        "attribution": "NASA Exoplanet Archive. Confirmed planets table (default columns). IPAC, Caltech.",
    },
    {
        "key": "noaa_itrdb",
        "subdir": "itrdb",
        "parser": parse_itrdb,  # special: takes a directory, not a file
        "source_dataset": "NOAA ITRDB v7.13 tree-ring chronologies",
        "source_doi": "",
        "source_uri": "https://www.ncei.noaa.gov/products/paleoclimatology/tree-ring",
        "event_category": "paleoclimate",
        "event_subcategory": "tree_ring_chronology",
        "original_time_unit": "decimal_year",
        "precision_level": "Level 1",
        "time_uncertainty_years": "1",
        "uby_converter": lambda rec: _decimal_year_to_uby(rec["decimal_year"]),
        "original_time_extractor": lambda rec: str(rec["decimal_year"]),
        "attribution": "International Tree-Ring Data Bank (ITRDB) v7.13. NOAA World Data Service for Paleoclimatology.",
    },
    {
        "key": "neotoma_sites",
        "subdir": "neotoma",
        "file": "sites.jsonl",
        "parser": parse_neotoma,
        "source_dataset": "Neotoma Paleoecology Database",
        "source_doi": "10.1111/2041-210X.12869",
        "source_uri": "https://www.neotomadb.org/",
        "event_category": "paleoecology",
        "event_subcategory": "fossil_sample",
        "original_time_unit": "yr_bp",
        "precision_level": "Level 3",
        "time_uncertainty_years": "500",
        "uby_converter": lambda rec: (
            _yr_bp_to_uby(rec["yr_bp"]) if "yr_bp" in rec
            else _decimal_year_to_uby(rec["decimal_year"])
        ),
        "original_time_extractor": lambda rec: (
            str(rec["yr_bp"]) if "yr_bp" in rec
            else str(rec["decimal_year"])
        ),
        "attribution": "Williams, J.W. et al. (2018). The Neotoma Paleoecology Database: a multi-proxy, international, community-curated data resource. Quaternary Research 89, 156-177.",
    },
]


def main() -> int:
    start = time.perf_counter()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source_dataset",
        "source_record_id",
        "source_record_uri",
        "event_label",
        "event_subcategory",
        "original_time_unit",
        "original_time_value",
        "measured_value",
        "measured_value_unit",
        "uncertainty_years",
        "precision_level",
        "uby_value",
        "model_version",
        "uby_version",
        "anchor_id",
        "anchor_uby",
        "description",
        "attribution",
    ]

    source_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    total = 0

    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for src in SOURCES:
            if "file" in src:
                path = RAW_DIR / src["subdir"] / src["file"]
                if not path.exists():
                    print(f"[skip] {src['key']}: missing {path.name}")
                    continue
                records = src["parser"](path)
            else:
                # Directory-based parser (e.g., ITRDB)
                base_dir = RAW_DIR / src["subdir"]
                if not base_dir.exists():
                    print(f"[skip] {src['key']}: missing dir {src['subdir']}")
                    continue
                records = src["parser"](base_dir)

            count = 0
            for rec in records:
                uby_val = src["uby_converter"](rec)
                original_time = src["original_time_extractor"](rec)

                # Determine time unit for this row (handles mixed records)
                if "decimal_year" in rec:
                    time_unit = "decimal_year"
                elif "yr_bp" in rec:
                    time_unit = "yr_bp"
                elif "gyr" in rec:
                    time_unit = "gyr"
                else:
                    time_unit = src["original_time_unit"]

                row = {
                    "source_dataset": src["source_dataset"],
                    "source_record_id": rec.get("source_record_id", f"{src['key']}-{count + 1}"),
                    "source_record_uri": src["source_uri"],
                    "event_label": f"{src['key']} sample {count + 1}",
                    "event_subcategory": src["event_subcategory"],
                    "original_time_unit": time_unit,
                    "original_time_value": original_time,
                    "measured_value": str(rec["value"]),
                    "measured_value_unit": rec["value_unit"],
                    "uncertainty_years": src["time_uncertainty_years"],
                    "precision_level": src["precision_level"],
                    "uby_value": str(uby_val),
                    "model_version": MODEL_VERSION,
                    "uby_version": UBY_SPEC_VERSION,
                    "anchor_id": DEFAULT_ANCHOR_ID,
                    "anchor_uby": str(ANCHOR_UBY),
                    "description": rec["description"],
                    "attribution": src["attribution"],
                }
                writer.writerow(row)
                count += 1

            source_counts[src["source_dataset"]] = count
            category_counts[src["event_category"]] = (
                category_counts.get(src["event_category"], 0) + count
            )
            total += count
            print(f"[ok] {src['key']:24s} {count:6d} samples")

    elapsed = time.perf_counter() - start

    metadata = {
        "database": "External databases (GVP, NASA Exoplanet, ITRDB, Neotoma) on UBY axis",
        "description": (
            "4 newly-downloaded external databases annotated with UBY time "
            "values: Holocene volcanoes, confirmed exoplanets, tree-ring "
            "chronologies, and paleoecology sites. Showcases UBY's cross-scale "
            "advantage (1 yr -> 1 Gyr in a single axis)."
        ),
        "generated_by": GENERATED_BY,
        "uby_version": UBY_SPEC_VERSION,
        "anchor": {
            "anchor_id": DEFAULT_ANCHOR_ID,
            "anchor_iso": DEFAULT_ANCHOR_ISO,
            "anchor_jd": str(DEFAULT_ANCHOR_JD),
            "anchor_uby": str(ANCHOR_UBY),
        },
        "total_records": total,
        "source_counts": source_counts,
        "category_counts": category_counts,
        "sources": [
            {
                "key": s["key"],
                "source_dataset": s["source_dataset"],
                "event_category": s["event_category"],
                "event_subcategory": s["event_subcategory"],
                "precision_level": s["precision_level"],
            }
            for s in SOURCES
        ],
        "outputs": {"csv": str(CSV_OUT.as_posix())},
        "build_performance": {
            "wall_seconds": round(elapsed, 4),
            "records_per_second": round(total / elapsed, 2) if elapsed else 0,
        },
    }
    METADATA_OUT.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nTotal records: {total}")
    print(f"CSV: {CSV_OUT}")
    print(f"Metadata: {METADATA_OUT}")
    print(f"Wall seconds: {elapsed:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
