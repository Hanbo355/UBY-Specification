#!/usr/bin/env python3
"""
Download NASA/JPL CNEOS Fireball and Bolide Data and annotate events with UBY Level 1 labels.

This script uses real authoritative event records from the NASA/JPL SSD/CNEOS
Fireball Data API. Each row is an observed fireball/bolide event with a native
UTC event timestamp; UBY is added only as an auxiliary cross-scale time key.

Source:
- NASA/JPL CNEOS Fireball and Bolide Data
- API: https://ssd-api.jpl.nasa.gov/fireball.api
"""

from __future__ import annotations

import csv
import json
import sqlite3
import ssl
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.anchors import DEFAULT_ANCHOR
from uby_time.constants import DEFAULT_MODEL_VERSION, DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from uby_time.conversion import iso_to_uby
from uby_time.formatting import format_full, format_magnitude
from uby_time.models import PrecisionLevel
from uby_time.utils import decimal_to_plain_text
from uby_time.validation import validate_uby_time

RAW_DIR = ROOT / "data" / "raw" / "nasa_jpl_cneos_fireballs"
PROCESSED_DIR = ROOT / "data" / "processed"

RAW_JSON = RAW_DIR / "cneos_fireballs.json"
RAW_CSV = RAW_DIR / "cneos_fireballs.csv"
CSV_OUT = PROCESSED_DIR / "nasa_jpl_cneos_fireballs_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "nasa_jpl_cneos_fireballs_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "nasa_jpl_cneos_fireballs_uby_metadata.json"

CNEOS_API = "https://ssd-api.jpl.nasa.gov/fireball.api"
SOURCE_DATASET = "NASA/JPL CNEOS Fireball and Bolide Data"


@dataclass(frozen=True)
class AnnotatedCneosFireball:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    source_time_utc: str
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
    energy_kt: str
    impact_energy_kt: str
    latitude: str
    longitude: str
    altitude_km: str
    velocity_km_s: str
    validation_messages: str
    attribution: str


def _clean(value: object | None) -> str:
    return "" if value is None else str(value).strip()


def _download_text(url: str) -> str:
    try:
        with urlopen(url, timeout=120) as response:
            return response.read().decode("utf-8")
    except (ssl.SSLCertVerificationError, URLError):
        # Some Windows Python installations lack the required CA bundle. The
        # endpoint is still the official NASA/JPL HTTPS endpoint; this fallback
        # keeps the example runnable in those environments.
        with urlopen(url, timeout=120, context=ssl._create_unverified_context()) as response:
            return response.read().decode("utf-8")


def _signed_coordinate(value: str, direction: str) -> str:
    if value == "":
        return ""
    sign = -1 if direction.upper() in {"S", "W"} else 1
    try:
        return str(sign * float(value))
    except ValueError:
        return ""


def _iso_utc_from_cneos_date(value: str) -> str:
    # CNEOS API uses "YYYY-MM-DD HH:MM:SS" UTC strings.
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def download_cneos_fireballs() -> dict[str, object]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = CNEOS_API + "?" + urlencode({"sort": "-date"})
    payload = json.loads(_download_text(url))
    RAW_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = list(payload.get("fields", []))
    rows = payload.get("data", [])
    with RAW_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        writer.writerows(rows)

    return payload


def annotate() -> list[AnnotatedCneosFireball]:
    payload = download_cneos_fireballs()
    fields = list(payload.get("fields", []))
    rows = payload.get("data", [])

    records: list[AnnotatedCneosFireball] = []
    for index, values in enumerate(rows, start=1):
        row = dict(zip(fields, values))
        source_date = _clean(row.get("date"))
        if source_date == "":
            continue

        source_time_utc = _iso_utc_from_cneos_date(source_date)
        uby = iso_to_uby(
            source_time_utc,
            source_system="NASA/JPL CNEOS Fireball UTC event time",
            prefer_astropy=False,
        )
        messages = validate_uby_time(uby)

        latitude = _signed_coordinate(_clean(row.get("lat")), _clean(row.get("lat-dir")))
        longitude = _signed_coordinate(_clean(row.get("lon")), _clean(row.get("lon-dir")))
        energy = _clean(row.get("energy"))
        impact_energy = _clean(row.get("impact-e"))
        record_id = source_time_utc.replace(":", "").replace("-", "").replace("T", "_").replace("Z", "")

        records.append(
            AnnotatedCneosFireball(
                source_dataset=SOURCE_DATASET,
                source_record_id=record_id,
                source_record_uri=CNEOS_API,
                event_label=f"NASA/JPL CNEOS fireball {source_time_utc}",
                event_type="fireball_event_time",
                source_time_utc=source_time_utc,
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
                energy_kt=energy,
                impact_energy_kt=impact_energy,
                latitude=latitude,
                longitude=longitude,
                altitude_km=_clean(row.get("alt")),
                velocity_km_s=_clean(row.get("vel")),
                validation_messages=json.dumps([asdict(message) for message in messages], ensure_ascii=False),
                attribution=(
                    "Data from NASA/JPL CNEOS Fireball and Bolide Data API, "
                    "https://ssd-api.jpl.nasa.gov/fireball.api; UBY annotation added by uby-time."
                ),
            )
        )

    return records


def write_csv(records: list[AnnotatedCneosFireball]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(AnnotatedCneosFireball.__dataclass_fields__))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def write_sqlite(records: list[AnnotatedCneosFireball]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedCneosFireball.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            "CREATE TABLE nasa_jpl_cneos_fireballs_uby ("
            + ", ".join(f"{column} TEXT" for column in quoted_columns)
            + ")"
        )
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            "INSERT INTO nasa_jpl_cneos_fireballs_uby "
            f"({', '.join(quoted_columns)}) VALUES ({placeholders})",
            [[getattr(record, column) for column in columns] for record in records],
        )
        conn.execute(
            "CREATE INDEX idx_cneos_fireballs_uby_value "
            f"ON nasa_jpl_cneos_fireballs_uby ({_quote_identifier('uby_value')})"
        )
        conn.execute(
            "CREATE INDEX idx_cneos_fireballs_source_time "
            f"ON nasa_jpl_cneos_fireballs_uby ({_quote_identifier('source_time_utc')})"
        )


def write_metadata(records: list[AnnotatedCneosFireball]) -> None:
    times = [record.source_time_utc for record in records]
    metadata = {
        "dataset": SOURCE_DATASET,
        "source_api": CNEOS_API,
        "source_file_json": str(RAW_JSON.as_posix()),
        "source_file_csv": str(RAW_CSV.as_posix()),
        "record_count": len(records),
        "source_time_min_utc": min(times) if times else None,
        "source_time_max_utc": max(times) if times else None,
        "uby_annotation_principles": [
            "Each row corresponds to a real NASA/JPL CNEOS fireball event record.",
            "Native UTC event time, energy, impact energy, location, altitude, and velocity fields are preserved where present.",
            "UBY is added only as an auxiliary cross-scale label/index.",
            "All records are Level 1 because CNEOS fireball event times are modern UTC timestamps.",
            "No temporal uncertainty is invented when the source API does not provide one.",
        ],
        "uby_version": UBY_SPEC_VERSION,
        "model_version": DEFAULT_MODEL_VERSION,
        "anchor": {
            "anchor_id": DEFAULT_ANCHOR.anchor_id,
            "anchor_jd": str(DEFAULT_ANCHOR.anchor_jd),
            "anchor_uby": str(DEFAULT_ANCHOR.anchor_uby),
        },
        "rounding_rule": DEFAULT_ROUNDING_RULE,
        "generated_by": GENERATED_BY,
        "outputs": {
            "csv": str(CSV_OUT.as_posix()),
            "sqlite": str(SQLITE_OUT.as_posix()),
        },
    }
    METADATA_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
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
            print(f"- {record.event_label}: {record.uby_expression}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
