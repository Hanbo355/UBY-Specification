#!/usr/bin/env python3
"""
Download authoritative high-redshift astronomical objects from SIMBAD/CDS and
annotate them with UBY Level 3 labels.

This script intentionally uses real database records instead of generated
redshift grid points. Source records come from the SIMBAD Astronomical Database
through the CDS TAP service.

Source:
- SIMBAD Astronomical Database, CDS, Strasbourg, France
- TAP endpoint: https://simbad.cds.unistra.fr/simbad/sim-tap/sync
- Reference: Wenger et al. 2000, A&AS, 143, 9
"""

from __future__ import annotations

import csv
import json
import sqlite3
import ssl
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uby_time.anchors import DEFAULT_ANCHOR
from uby_time.constants import DEFAULT_ROUNDING_RULE, GENERATED_BY, UBY_SPEC_VERSION
from uby_time.cosmology import redshift_to_uby

RAW_DIR = ROOT / "data" / "raw" / "simbad"
PROCESSED_DIR = ROOT / "data" / "processed"

RAW_CSV = RAW_DIR / "simbad_high_redshift_objects.csv"
CSV_OUT = PROCESSED_DIR / "simbad_high_redshift_objects_uby.csv"
SQLITE_OUT = PROCESSED_DIR / "simbad_high_redshift_objects_uby.sqlite"
METADATA_OUT = PROCESSED_DIR / "simbad_high_redshift_objects_uby_metadata.json"

SIMBAD_TAP_ENDPOINT = "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"
SIMBAD_DATASET = "SIMBAD Astronomical Database high-redshift objects"
SIMBAD_REFERENCE = "Wenger et al. 2000, A&AS, 143, 9"
SIMBAD_REFERENCE_URI = "https://ui.adsabs.harvard.edu/abs/2000A%26AS..143....9W/abstract"

DEFAULT_LIMIT = 5000


@dataclass(frozen=True)
class AnnotatedSimbadHighRedshiftObject:
    source_dataset: str
    source_record_id: str
    source_record_uri: str
    event_label: str
    event_type: str
    object_name: str
    object_type: str
    right_ascension_deg: str
    declination_deg: str
    redshift: str
    original_time_unit: str
    original_time_value: str
    uncertainty_years: str
    precision_level: str
    uby_value: str
    uby_value_text: str
    model_version: str
    uby_version: str
    anchor_id: str
    anchor_jd: str
    anchor_uby: str
    rounding_rule: str
    generated_by: str
    propagation_note: str
    attribution: str


def _clean(value: str | None) -> str:
    return "" if value is None else value.strip()


def _simbad_object_uri(main_id: str) -> str:
    return "https://simbad.cds.unistra.fr/simbad/sim-id?Ident=" + quote(main_id)


def _download_text(url: str) -> str:
    try:
        with urlopen(url, timeout=120) as response:
            return response.read().decode("utf-8-sig")
    except ssl.SSLCertVerificationError:
        # Some Windows Python installations lack the required CA bundle. The
        # endpoint is still the official CDS HTTPS endpoint; this fallback keeps
        # the example runnable in those environments.
        with urlopen(url, timeout=120, context=ssl._create_unverified_context()) as response:
            return response.read().decode("utf-8-sig")


def download_simbad_high_redshift_objects(limit: int = DEFAULT_LIMIT) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    query = f"""
SELECT TOP {int(limit)}
    main_id,
    ra,
    dec,
    rvz_redshift,
    otype
FROM basic
WHERE rvz_redshift BETWEEN 0.000001 AND 30
ORDER BY rvz_redshift DESC
""".strip()

    url = SIMBAD_TAP_ENDPOINT + "?" + urlencode(
        {
            "request": "doQuery",
            "lang": "adql",
            "format": "csv",
            "query": query,
        }
    )
    text = _download_text(url)

    if text.lstrip().startswith("<?xml") or "QUERY_STATUS" in text[:1000]:
        raise RuntimeError(f"SIMBAD TAP query did not return CSV data:\n{text[:2000]}")

    RAW_CSV.write_text(text, encoding="utf-8")


def annotate() -> list[AnnotatedSimbadHighRedshiftObject]:
    if not RAW_CSV.exists():
        download_simbad_high_redshift_objects()

    records: list[AnnotatedSimbadHighRedshiftObject] = []
    with RAW_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            object_name = _clean(row.get("main_id"))
            redshift_text = _clean(row.get("rvz_redshift"))
            if object_name == "" or redshift_text == "":
                continue

            try:
                redshift = float(redshift_text)
            except ValueError:
                continue
            if redshift < 0:
                continue

            uby = redshift_to_uby(
                redshift,
                cosmology_name="Planck18",
                model_version="LCDM-Planck2018",
                include_uncertainty=True,
            )
            uby_value = str(uby.uby_value)

            records.append(
                AnnotatedSimbadHighRedshiftObject(
                    source_dataset=SIMBAD_DATASET,
                    source_record_id=object_name,
                    source_record_uri=_simbad_object_uri(object_name),
                    event_label=f"Observed high-redshift object {object_name}",
                    event_type="high_redshift_astronomical_object",
                    object_name=object_name,
                    object_type=_clean(row.get("otype")),
                    right_ascension_deg=_clean(row.get("ra")),
                    declination_deg=_clean(row.get("dec")),
                    redshift=redshift_text,
                    original_time_unit="redshift",
                    original_time_value=f"z={redshift:g}",
                    uncertainty_years=str(uby.uncertainty_years) if uby.uncertainty_years else "",
                    precision_level="Level 3",
                    uby_value=uby_value,
                    uby_value_text=uby_value,
                    model_version=uby.model_version or "",
                    uby_version=uby.uby_version,
                    anchor_id=uby.anchor_id,
                    anchor_jd=str(uby.anchor_jd),
                    anchor_uby=str(uby.anchor_uby),
                    rounding_rule=uby.rounding_rule,
                    generated_by=uby.generated_by,
                    propagation_note=uby.propagation_note,
                    attribution=(
                        "Object data from the SIMBAD Astronomical Database, CDS, Strasbourg, France; "
                        f"database reference: {SIMBAD_REFERENCE}; UBY annotation added by uby-time."
                    ),
                )
            )

    return records


def write_csv(records: list[AnnotatedSimbadHighRedshiftObject]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(AnnotatedSimbadHighRedshiftObject.__dataclass_fields__),
        )
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def write_sqlite(records: list[AnnotatedSimbadHighRedshiftObject]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if SQLITE_OUT.exists():
        SQLITE_OUT.unlink()

    columns = list(AnnotatedSimbadHighRedshiftObject.__dataclass_fields__)
    quoted_columns = [_quote_identifier(column) for column in columns]
    with sqlite3.connect(SQLITE_OUT) as conn:
        conn.execute(
            "CREATE TABLE simbad_high_redshift_objects_uby ("
            + ", ".join(f"{column} TEXT" for column in quoted_columns)
            + ")"
        )
        placeholders = ", ".join("?" for _ in columns)
        conn.executemany(
            "INSERT INTO simbad_high_redshift_objects_uby "
            f"({', '.join(quoted_columns)}) VALUES ({placeholders})",
            [[getattr(record, column) for column in columns] for record in records],
        )
        conn.execute(
            "CREATE INDEX idx_simbad_high_redshift_uby_value "
            f"ON simbad_high_redshift_objects_uby ({_quote_identifier('uby_value')})"
        )
        conn.execute(
            "CREATE INDEX idx_simbad_high_redshift_redshift "
            f"ON simbad_high_redshift_objects_uby ({_quote_identifier('redshift')})"
        )


def write_metadata(records: list[AnnotatedSimbadHighRedshiftObject]) -> None:
    redshifts = [float(record.redshift) for record in records]
    metadata = {
        "dataset": SIMBAD_DATASET,
        "source_database": "SIMBAD Astronomical Database",
        "source_provider": "CDS, Strasbourg Astronomical Data Center",
        "source_api": SIMBAD_TAP_ENDPOINT,
        "source_reference": SIMBAD_REFERENCE,
        "source_reference_uri": SIMBAD_REFERENCE_URI,
        "source_file": str(RAW_CSV.as_posix()),
        "record_count": len(records),
        "redshift_min": min(redshifts) if redshifts else None,
        "redshift_max": max(redshifts) if redshifts else None,
        "selection": (
            f"Top {DEFAULT_LIMIT} SIMBAD basic-table records ordered by rvz_redshift descending, "
            "with rvz_redshift between 0.000001 and 30."
        ),
        "uby_annotation_principles": [
            "Each row corresponds to a real SIMBAD database object, not a generated redshift grid point.",
            "Native SIMBAD object identifier, coordinates, object type, and redshift are preserved.",
            "UBY is added as a model-dependent Level 3 cosmological age label computed from redshift.",
            "The cosmological conversion uses astropy.cosmology.Planck18 age(z).",
            "uncertainty_years is the existing uby-time heuristic model uncertainty annotation.",
        ],
        "uby_version": UBY_SPEC_VERSION,
        "model_version": "LCDM-Planck2018",
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
    download_simbad_high_redshift_objects()
    records = annotate()
    write_csv(records)
    write_sqlite(records)
    write_metadata(records)

    print(f"Downloaded SIMBAD raw records: {RAW_CSV}")
    print(f"Annotated records: {len(records)}")
    print(f"CSV: {CSV_OUT}")
    print(f"SQLite: {SQLITE_OUT}")
    print(f"Metadata: {METADATA_OUT}")

    if records:
        print("Sample:")
        for record in records[:5]:
            print(
                f"- {record.object_name}: z={record.redshift} "
                f"-> UBY {record.uby_value} [model={record.model_version}]"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
