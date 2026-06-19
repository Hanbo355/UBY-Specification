#!/usr/bin/env python3
"""
Annotate downloaded NASA/IPAC Exoplanet Archive confirmed exoplanets with UBY labels.

Normative UBY principles applied:
- preserve the archive's native discovery year field;
- use UBY only as an auxiliary cross-scale label/index;
- do not invent a month/day/time for records that only provide a discovery year;
- mark the derived UBY label as year-resolution Level 1 data;
- carry a one-year temporal resolution as uncertainty_years;
- keep source/spec/anchor/rounding metadata with every record.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.anchors import DEFAULT_ANCHOR
from uby_time.constants import DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from uby_time.conversion import astronomical_year_to_uby
from uby_time.formatting import format_full, format_magnitude
from uby_time.models import PrecisionLevel
from uby_time.utils import decimal_to_plain_text
from uby_time.validation import validate_uby_time

RAW_CSV = ROOT / "data" / "raw" / "nasa_exoplanet_archive" / "confirmed_exoplanets.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
CSV_OUT = PROCESSED_DIR / "nasa_exoplanet_archive_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "nasa_exoplanet_archive_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "nasa_exoplanet_archive_uby_metadata.json"


@dataclass(frozen=True)
class AnnotatedExoplanet:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    planet_name: str
    hostname: str
    discovery_year: str
    representative_astronomical_year: str
    uncertainty_years: str
    precision_level: str
    uby_value: str
    uby_expression: str
    uby_magnitude_expression: str
    model_version: str
    uby_version: str
    anchor_id: str
    anchor_jd: str
    anchor_uby: str
    rounding_rule: str
    generated_by: str
    discovery_method: str
    discovery_facility: str
    system_planet_count: str
    orbital_period_days: str
    planet_radius_earth: str
    planet_mass_earth: str
    stellar_effective_temperature_k: str
    stellar_radius_solar: str
    stellar_mass_solar: str
    right_ascension_deg: str
    declination_deg: str
    validation_messages: str
    attribution: str


def _int_year(value: str) -> int | None:
    if value is None or value.strip() == "":
        return None
    try:
        year_decimal = Decimal(value.strip())
    except InvalidOperation:
        return None

    if year_decimal != year_decimal.to_integral_value():
        return None
    return int(year_decimal)


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def annotate() -> list[AnnotatedExoplanet]:
    records: list[AnnotatedExoplanet] = []

    with RAW_CSV.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            discovery_year = _int_year(row.get("disc_year", ""))
            planet_name = _clean(row.get("pl_name"))
            if discovery_year is None or planet_name == "":
                continue

            uby = astronomical_year_to_uby(discovery_year, include_model=False).with_uncertainty(
                uncertainty_years=Decimal("1"),
                uncertainty_kind="temporal_resolution",
                interval_start=Decimal(uby_value := str(astronomical_year_to_uby(discovery_year).uby_value)),
                interval_end=Decimal(uby_value) + Decimal("1"),
            )
            messages = validate_uby_time(uby)
            hostname = _clean(row.get("hostname"))

            records.append(
                AnnotatedExoplanet(
                    source_dataset="NASA/IPAC Exoplanet Archive Planetary Systems Composite Parameters",
                    source_record_id=planet_name,
                    source_record_uri=(
                        "https://exoplanetarchive.ipac.caltech.edu/overview/"
                        + planet_name.replace(" ", "%20")
                    ),
                    event_label=f"Discovery of exoplanet {planet_name}",
                    event_type="exoplanet_discovery_year",
                    planet_name=planet_name,
                    hostname=hostname,
                    discovery_year=str(discovery_year),
                    representative_astronomical_year=str(discovery_year),
                    uncertainty_years="1",
                    precision_level=PrecisionLevel.LEVEL_1.value,
                    uby_value=decimal_to_plain_text(uby.uby_value),
                    uby_expression=format_full(uby, include_model=True, include_spec=True),
                    uby_magnitude_expression=format_magnitude(uby, include_model=True, include_spec=True),
                    model_version=uby.model_version or "",
                    uby_version=uby.uby_version,
                    anchor_id=uby.anchor_id,
                    anchor_jd=str(uby.anchor_jd),
                    anchor_uby=str(uby.anchor_uby),
                    rounding_rule=uby.rounding_rule,
                    generated_by=uby.generated_by,
                    discovery_method=_clean(row.get("discoverymethod")),
                    discovery_facility=_clean(row.get("disc_facility")),
                    system_planet_count=_clean(row.get("sy_pnum")),
                    orbital_period_days=_clean(row.get("pl_orbper")),
                    planet_radius_earth=_clean(row.get("pl_rade")),
                    planet_mass_earth=_clean(row.get("pl_bmasse")),
                    stellar_effective_temperature_k=_clean(row.get("st_teff")),
                    stellar_radius_solar=_clean(row.get("st_rad")),
                    stellar_mass_solar=_clean(row.get("st_mass")),
                    right_ascension_deg=_clean(row.get("ra")),
                    declination_deg=_clean(row.get("dec")),
                    validation_messages=json.dumps([asdict(m) for m in messages], ensure_ascii=False),
                    attribution=(
                        "Data from the NASA/IPAC Exoplanet Archive, "
                        "https://exoplanetarchive.ipac.caltech.edu; "
                        "downloaded via TAP sync CSV; UBY annotation added by uby-time."
                    ),
                )
            )

    return records


def write_csv(records: list[AnnotatedExoplanet]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(AnnotatedExoplanet.__dataclass_fields__))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def write_sqlite(records: list[AnnotatedExoplanet]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedExoplanet.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            "CREATE TABLE nasa_exoplanet_archive_uby ("
            + ", ".join(f"{column} TEXT" for column in quoted_columns)
            + ")"
        )
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            f"INSERT INTO nasa_exoplanet_archive_uby ({', '.join(quoted_columns)}) VALUES ({placeholders})",
            [[getattr(record, c) for c in columns] for record in records],
        )
        conn.execute(
            "CREATE INDEX idx_nasa_exoplanet_archive_uby_value "
            f"ON nasa_exoplanet_archive_uby ({_quote_identifier('uby_value')})"
        )
        conn.execute(
            "CREATE INDEX idx_nasa_exoplanet_archive_planet "
            f"ON nasa_exoplanet_archive_uby ({_quote_identifier('planet_name')})"
        )
        conn.execute(
            "CREATE INDEX idx_nasa_exoplanet_archive_year "
            f"ON nasa_exoplanet_archive_uby ({_quote_identifier('discovery_year')})"
        )


def write_metadata(records: list[AnnotatedExoplanet]) -> None:
    years = [int(record.discovery_year) for record in records]
    metadata = {
        "dataset": "NASA/IPAC Exoplanet Archive confirmed exoplanets",
        "source_api": (
            "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
            "query=select pl_name,hostname,disc_year,discoverymethod,disc_facility,"
            "sy_pnum,pl_orbper,pl_rade,pl_bmasse,st_teff,st_rad,st_mass,ra,dec "
            "from pscomppars where disc_year is not null&format=csv"
        ),
        "source_file": str(RAW_CSV.as_posix()),
        "record_count": len(records),
        "discovery_year_min": min(years) if years else None,
        "discovery_year_max": max(years) if years else None,
        "uby_annotation_principles": [
            "Native NASA/IPAC discovery year values are preserved.",
            "UBY is added only as an auxiliary cross-scale label/index.",
            "No month/day/time is fabricated for year-only source records.",
            "All records are marked Level 1 because discovery years are historical calendar data.",
            "uncertainty_years=1 records the year-level temporal resolution.",
        ],
        "uby_version": UBY_SPEC_VERSION,
        "model_version": None,
        "anchor": {
            "anchor_id": DEFAULT_ANCHOR.anchor_id,
            "anchor_jd": str(DEFAULT_ANCHOR.anchor_jd),
            "anchor_uby": str(DEFAULT_ANCHOR.anchor_uby),
        },
        "rounding_rule": DEFAULT_ROUNDING_RULE,
        "outputs": {
            "csv": str(CSV_OUT.as_posix()),
            "sqlite": str(SQLITE_OUT.as_posix()),
        },
    }
    METADATA_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if not RAW_CSV.exists():
        raise FileNotFoundError(f"NASA/IPAC Exoplanet Archive source file not found: {RAW_CSV}")

    records = annotate()
    write_csv(records)
    write_sqlite(records)
    write_metadata(records)

    print(f"Annotated records: {len(records)}")
    print(f"CSV: {CSV_OUT}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Metadata: {METADATA_OUT}")

    if records:
        print("Sample:")
        for record in records[:5]:
            print(
                f"- {record.event_label}: year={record.discovery_year} "
                f"-> {record.uby_expression} ±{record.uncertainty_years} year"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
