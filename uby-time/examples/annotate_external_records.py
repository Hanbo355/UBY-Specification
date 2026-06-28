#!/usr/bin/env python3
"""
Annotate external paleoclimate and instrumental records with UBY time values.

Processes 8 raw data sources that are not yet integrated into the unified
timeline database:

  Paleoclimate archives (Level 2):
    - LR04 benthic d18O stack (Lisiecki & Raymo 2005)
    - Vostok ice core deuterium/temperature (Petit et al. 1999)
    - Vostok ice core CO2 (Petit et al. 1999)
    - EPICA Dome C CO2 composite (Bereiter et al. 2015)

  Instrumental records (Level 1):
    - Sunspot number monthly (SILSO/WDC)
    - Sunspot number yearly (SILSO/WDC)
    - GISS global surface temperature anomaly (GISTEMP v4)
    - Mauna Loa monthly CO2 (NOAA GML)

Each record's native chronology is converted to the UBY axis (years from the
Big Bang) using the UBY anchor (2026-01-01T00:00:00Z, UBY=13787002026.0).

Output:
- data/processed/external_records_uby.csv
- data/processed/external_records_uby_metadata.json
"""

from __future__ import annotations

import csv
import json
import sys
import time
from decimal import Decimal
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
CSV_OUT = PROCESSED_DIR / "external_records_uby.csv"
METADATA_OUT = PROCESSED_DIR / "external_records_uby_metadata.json"

MODEL_VERSION = "none"


def _ka_bp_to_uby(ka: float) -> float:
    """Convert ka-before-present (present=anchor 2026) to UBY."""
    return float(ANCHOR_UBY) - ka * 1000.0


def _yr_bp_to_uby(yr: float) -> float:
    """Convert years-before-present (present=anchor 2026) to UBY."""
    return float(ANCHOR_UBY) - yr


def _decimal_year_to_uby(decimal_year: float) -> float:
    """Convert a decimal calendar year to UBY."""
    return float(ANCHOR_UBY) + (decimal_year - 2026.0)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_lr04(path: Path):
    """LR04 benthic d18O stack. Format: time_ka d18O stderr (skip header)."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.replace("\t", " ").split()
            if len(parts) < 2:
                continue
            try:
                ka = float(parts[0])
                d18o = float(parts[1])
            except ValueError:
                continue  # header lines
            yield {
                "age_ka": ka,
                "value": d18o,
                "value_label": "d18O",
                "value_unit": "per_mil",
            }


def parse_vostok_deuterium(path: Path):
    """Vostok ice core deuterium. Data starts after 'Depth corrected' header.

    Columns: depth  ice_age_yr  deut  deltaTS
    """
    in_data = False
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "Depth corrected" in line:
                in_data = True
                continue
            if not in_data:
                continue
            parts = line.replace("\t", " ").split()
            if len(parts) < 4:
                continue
            try:
                age_yr = float(parts[1])
                deut = float(parts[2])
            except ValueError:
                continue
            if age_yr < 0:
                continue
            yield {
                "age_yr": age_yr,
                "value": deut,
                "value_label": "deuterium",
                "value_unit": "per_mil",
            }


def parse_vostok_co2(path: Path):
    """Vostok ice core CO2. Data starts after 'Gas age  CO2 (ppmv)' header.

    Columns: gas_age_yr  co2_ppmv
    """
    in_data = False
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "Gas age" in line and "CO2" in line:
                in_data = True
                continue
            if not in_data:
                continue
            parts = line.replace("\t", " ").split()
            if len(parts) < 2:
                continue
            try:
                age_yr = float(parts[0])
                co2 = float(parts[1])
            except ValueError:
                continue
            if age_yr < 0:
                continue
            yield {
                "age_yr": age_yr,
                "value": co2,
                "value_label": "CO2",
                "value_unit": "ppmv",
            }


def parse_epica_co2(path: Path):
    """EPICA Dome C CO2. Data starts after comment block.

    Columns: age_yr  co2  stderr
    """
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = line.replace("\t", " ").split()
            if len(parts) < 2:
                continue
            try:
                age_yr = float(parts[0])
                co2 = float(parts[1])
            except ValueError:
                continue
            if age_yr < 0:
                continue
            yield {
                "age_yr": age_yr,
                "value": co2,
                "value_label": "CO2",
                "value_unit": "ppmv",
            }


def parse_sunspot_monthly(path: Path):
    """SILSO monthly sunspot number. Columns: year month decimal_year ssn stddev obs."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                decimal_year = float(parts[2])
                ssn = float(parts[3])
            except ValueError:
                continue
            # Skip missing values (-1 means no data)
            if ssn < 0:
                continue
            yield {
                "decimal_year": decimal_year,
                "value": ssn,
                "value_label": "sunspot_number",
                "value_unit": "count",
            }


def parse_sunspot_yearly(path: Path):
    """SILSO yearly sunspot number. Columns: decimal_year ssn stddev obs."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                decimal_year = float(parts[0])
                ssn = float(parts[1])
            except ValueError:
                continue
            if ssn < 0:
                continue
            yield {
                "decimal_year": decimal_year,
                "value": ssn,
                "value_label": "sunspot_number",
                "value_unit": "count",
            }


def parse_gistemp(path: Path):
    """GISTEMP global temperature anomaly. CSV with Year + monthly columns.

    The first line is a title ("Land-Ocean: Global Means"), the second line
    is the actual CSV header.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        next(fh, None)  # skip the title line
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                year = int(row["Year"])
                # J-D is the annual mean anomaly
                jd_str = row.get("J-D", "").strip()
                if jd_str == "***" or not jd_str:
                    continue
                anomaly = float(jd_str)
            except (ValueError, KeyError):
                continue
            decimal_year = year + 0.5
            yield {
                "decimal_year": decimal_year,
                "value": anomaly,
                "value_label": "temperature_anomaly",
                "value_unit": "degC",
            }


def parse_maunaloa_co2(path: Path):
    """NOAA GML Mauna Loa monthly CO2. Columns: year month decimal_year co2 interp trend."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                decimal_year = float(parts[2])
                # Use interpolated value (fills gaps); fall back to raw if -1
                co2 = float(parts[3])
            except ValueError:
                continue
            if co2 < 0:
                continue
            yield {
                "decimal_year": decimal_year,
                "value": co2,
                "value_label": "CO2",
                "value_unit": "ppm",
            }


# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

SOURCES = [
    {
        "key": "lr04_benthic_d18o",
        "file": "LR04stack.txt",
        "parser": parse_lr04,
        "source_dataset": "LR04 benthic d18O stack (Lisiecki & Raymo 2005)",
        "source_doi": "10.1029/2004PA001071",
        "source_uri": "https://doi.org/10.1029/2004PA001071",
        "event_category": "paleoclimate",
        "event_subcategory": "benthic_d18O",
        "original_time_unit": "ka_bp",
        "precision_level": "Level 2",
        "time_uncertainty_years": "500",
        "uby_converter": lambda rec: _ka_bp_to_uby(rec["age_ka"]),
        "original_time_extractor": lambda rec: str(rec["age_ka"]),
        "description_template": "Benthic d18O = {value} per mil; age = {age} ka BP",
        "attribution": "Lisiecki, L.E. & Raymo, M.E. (2005), Paleoceanography 20, PA1003, doi:10.1029/2004PA001071",
    },
    {
        "key": "vostok_temperature",
        "file": "vostok_deuterium.txt",
        "parser": parse_vostok_deuterium,
        "source_dataset": "Vostok ice core deuterium (Petit et al. 1999)",
        "source_doi": "10.1038/43848",
        "source_uri": "https://doi.org/10.1038/43848",
        "event_category": "paleoclimate",
        "event_subcategory": "ice_core_temperature",
        "original_time_unit": "yr_bp",
        "precision_level": "Level 2",
        "time_uncertainty_years": "1000",
        "uby_converter": lambda rec: _yr_bp_to_uby(rec["age_yr"]),
        "original_time_extractor": lambda rec: str(rec["age_yr"]),
        "description_template": "Deuterium = {value} per mil; ice age = {age} yr BP",
        "attribution": "Petit, J.R. et al. (1999), Nature 399, 429-436, doi:10.1038/20807",
    },
    {
        "key": "vostok_co2",
        "file": "vostok_co2.txt",
        "parser": parse_vostok_co2,
        "source_dataset": "Vostok ice core CO2 (Petit et al. 1999)",
        "source_doi": "10.1038/43848",
        "source_uri": "https://doi.org/10.1038/43848",
        "event_category": "paleoclimate",
        "event_subcategory": "ice_core_co2",
        "original_time_unit": "yr_bp",
        "precision_level": "Level 2",
        "time_uncertainty_years": "1000",
        "uby_converter": lambda rec: _yr_bp_to_uby(rec["age_yr"]),
        "original_time_extractor": lambda rec: str(rec["age_yr"]),
        "description_template": "CO2 = {value} ppmv; gas age = {age} yr BP",
        "attribution": "Petit, J.R. et al. (1999), Nature 399, 429-436, doi:10.1038/20807",
    },
    {
        "key": "epica_co2",
        "file": "epica_domec_co2_800kyr.txt",
        "parser": parse_epica_co2,
        "source_dataset": "EPICA Dome C CO2 composite (Bereiter et al. 2015)",
        "source_doi": "10.1002/2014GL061957",
        "source_uri": "https://doi.org/10.1002/2014GL061957",
        "event_category": "paleoclimate",
        "event_subcategory": "ice_core_co2",
        "original_time_unit": "yr_bp",
        "precision_level": "Level 2",
        "time_uncertainty_years": "1000",
        "uby_converter": lambda rec: _yr_bp_to_uby(rec["age_yr"]),
        "original_time_extractor": lambda rec: str(rec["age_yr"]),
        "description_template": "CO2 = {value} ppmv; gas age = {age} yr BP",
        "attribution": "Bereiter, B. et al. (2015), Geophys. Res. Lett. 42, 542-549, doi:10.1002/2014GL061957",
    },
    {
        "key": "sunspot_monthly",
        "file": "SN_m_tot_V2.0.txt",
        "parser": parse_sunspot_monthly,
        "source_dataset": "SILSO sunspot number monthly (WDC v2.0)",
        "source_doi": "",
        "source_uri": "https://www.sidc.be/SILSO/datafiles",
        "event_category": "instrumental",
        "event_subcategory": "sunspot_number",
        "original_time_unit": "decimal_year",
        "precision_level": "Level 1",
        "time_uncertainty_years": "0.042",
        "uby_converter": lambda rec: _decimal_year_to_uby(rec["decimal_year"]),
        "original_time_extractor": lambda rec: str(rec["decimal_year"]),
        "description_template": "Sunspot number = {value}; decimal year = {age}",
        "attribution": "SILSO World Data Center, Royal Observatory of Belgium, Brussels. Yearly sunspot number v2.0.",
    },
    {
        "key": "sunspot_yearly",
        "file": "SN_y_tot_V2.0.txt",
        "parser": parse_sunspot_yearly,
        "source_dataset": "SILSO sunspot number yearly (WDC v2.0)",
        "source_doi": "",
        "source_uri": "https://www.sidc.be/SILSO/datafiles",
        "event_category": "instrumental",
        "event_subcategory": "sunspot_number",
        "original_time_unit": "decimal_year",
        "precision_level": "Level 1",
        "time_uncertainty_years": "0.5",
        "uby_converter": lambda rec: _decimal_year_to_uby(rec["decimal_year"]),
        "original_time_extractor": lambda rec: str(rec["decimal_year"]),
        "description_template": "Sunspot number = {value}; decimal year = {age}",
        "attribution": "SILSO World Data Center, Royal Observatory of Belgium, Brussels. Yearly sunspot number v2.0.",
    },
    {
        "key": "gistemp_global",
        "file": "gistemp_global.csv",
        "parser": parse_gistemp,
        "source_dataset": "NASA GISS global surface temperature anomaly (GISTEMP v4)",
        "source_doi": "10.1029/2018JD029522",
        "source_uri": "https://data.giss.nasa.gov/gistemp/",
        "event_category": "instrumental",
        "event_subcategory": "global_temperature_anomaly",
        "original_time_unit": "decimal_year",
        "precision_level": "Level 1",
        "time_uncertainty_years": "0.5",
        "uby_converter": lambda rec: _decimal_year_to_uby(rec["decimal_year"]),
        "original_time_extractor": lambda rec: str(rec["decimal_year"]),
        "description_template": "Temperature anomaly = {value} degC; decimal year = {age}",
        "attribution": "Lenssen, N.J.L. et al. (2019), J. Geophys. Res. Atmos. 124, 6278-6291, doi:10.1029/2018JD029522. NASA GISS GISTEMP v4.",
    },
    {
        "key": "maunaloa_co2",
        "file": "maunaloa_co2_monthly.txt",
        "parser": parse_maunaloa_co2,
        "source_dataset": "NOAA GML Mauna Loa monthly CO2",
        "source_doi": "",
        "source_uri": "https://gml.noaa.gov/ccgg/trends/",
        "event_category": "instrumental",
        "event_subcategory": "atmospheric_co2",
        "original_time_unit": "decimal_year",
        "precision_level": "Level 1",
        "time_uncertainty_years": "0.042",
        "uby_converter": lambda rec: _decimal_year_to_uby(rec["decimal_year"]),
        "original_time_extractor": lambda rec: str(rec["decimal_year"]),
        "description_template": "CO2 = {value} ppm; decimal year = {age}",
        "attribution": "Tans, P. and Keeling, R., NOAA/GML and Scripps Institution of Oceanography. Monthly atmospheric CO2 from Mauna Loa Observatory.",
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
            path = RAW_DIR / src["file"]
            if not path.exists():
                print(f"[skip] {src['key']}: missing {src['file']}")
                continue

            count = 0
            for rec in src["parser"](path):
                uby_val = src["uby_converter"](rec)
                original_time = src["original_time_extractor"](rec)
                age_for_desc = original_time

                row = {
                    "source_dataset": src["source_dataset"],
                    "source_record_id": f"{src['key']}-{count + 1}",
                    "source_record_uri": src["source_uri"],
                    "event_label": f"{src['key']} sample {count + 1}",
                    "event_subcategory": src["event_subcategory"],
                    "original_time_unit": src["original_time_unit"],
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
                    "description": src["description_template"].format(
                        value=rec["value"], age=age_for_desc
                    ),
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
        "database": "External paleoclimate and instrumental records on the UBY axis",
        "description": (
            "8 external raw data sources (paleoclimate archives and instrumental "
            "records) annotated with UBY time values for integration into the "
            "unified cross-scale timeline."
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
                "file": s["file"],
                "source_dataset": s["source_dataset"],
                "event_category": s["event_category"],
                "event_subcategory": s["event_subcategory"],
                "precision_level": s["precision_level"],
            }
            for s in SOURCES
        ],
        "outputs": {
            "csv": str(CSV_OUT.as_posix()),
        },
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
