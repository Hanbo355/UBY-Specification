#!/usr/bin/env python3
"""
Build Zenodo/GitHub release metadata for the UBY dataset.

This script prepares a publication-ready data-release control package without
duplicating the large processed datasets.  The generated release directory
contains:
- dataset manifest with file sizes, row counts, SHA-256 checksums;
- checksums_sha256.txt for integrity verification;
- Zenodo metadata JSON;
- README_DATASET.md;
- DATA_DICTIONARY.md;
- QUALITY_CONTROL.md and quality_control_report.json;
- DATA_AVAILABILITY.md;
- CODE_AVAILABILITY.md;
- LICENSE_DATA_CC_BY_4.0.md;
- LICENSES_AND_ATTRIBUTION.md;
- GITHUB_ZENODO_RELEASE_GUIDE.md.

The large dataset files remain in data/processed/ and can be uploaded to Zenodo
together with the generated files.  This avoids making a second local copy of
multi-GB data while still producing all metadata required for long-term
archiving and DOI assignment.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
RELEASE_ROOT = ROOT / "data_release"
RELEASE_VERSION = "0.1.0"
RELEASE_ID = "uby-time-dataset-v0.1.0"
RELEASE_DIR = RELEASE_ROOT / RELEASE_ID

GITHUB_REPOSITORY_URL = "https://github.com/Hanbo355/UBY-Specification"
ZENODO_DOI = "10.5281/zenodo.20763218"
ZENODO_DOI_URL = "https://doi.org/" + ZENODO_DOI

DATASET_TITLE = (
    "UBY-labeled cross-scale temporal database for Phanerozoic fossil occurrences, "
    "forcing events, astronomical records, and mass-extinction dynamics"
)
CREATORS = [
    {
        "name": "Han, Bo",
        "affiliation": "UBY Specification Project",
        "orcid": "",
    }
]

PROCESSED_FILE_PATTERNS = (
    "*.csv",
    "*.json",
    "*.sqlite",
)

EXCLUDE_SUFFIXES = (
    ".sqlite-wal",
    ".sqlite-shm",
)

EXCLUDE_NAMES = {
    "simbad_probe.csv",
}

TRANSIENT_TEXT_FILES = {
    "pbdb_collections_download_output.txt",
    "pbdb_collections_download_output_fixed.txt",
    "pbdb_collections_field_probe.txt",
    "pbdb_collections_validity_probe.txt",
    "pbdb_field_probe.txt",
    "pbdb_download_status.txt",
    "pbdb_extinction_dynamics_analysis.txt",
    "forcing_extinction_leadlag_run_output_after_fix.txt",
    "forcing_extinction_leadlag_run_output_csv_source.txt",
    "forcing_extinction_leadlag_run_output_final.txt",
    "forcing_sqlite_inspection.txt",
    "forcing_sqlite_inspection_after_fix.txt",
    "simbad_unified_verification.txt",
}

# Intermediate analytical / derived artefacts that are not part of the final
# journal-grade data release.  Only core UBY-labeled source datasets, the
# unified timeline, the forcing-event compilation, and their metadata are
# archived.  Downstream analysis tables remain reproducible from the code in
# `examples/` and are deliberately excluded from the deposition.
INTERMEDIATE_EXCLUDE_PREFIXES = (
    "end_ordovician_",
    "extinction_sensitivity",
    "pbdb_extinction_dynamics",
    "pbdb_extinction_intensity_by_bin",
    "pbdb_recovery_lag",
    "pbdb_taxon_disappearances",
    "pbdb_taxon_ranges",
    "uby_forcing_extinction_leadlag",
    "uby_mass_extinction_lag",
    "phanerozoic_diversity_",
    "phanerozoic_sqs_diversity_",
)

INTERMEDIATE_EXCLUDE_NAMES = {
    "mass_extinction_periodicity_report.json",
    "milankovitch_orbital_signal_report.json",
    "modern_climate_attribution_report.json",
    "modern_co2_rate_uniqueness_report.json",
    "cross_scale_lip_extinction_periodicity_report.json",
    "cross_scale_precision_law_report.json",
    "true_cross_scale_precision_report.json",
    "paleoclimate_multisource_report.json",
    "dataset_merge_report.json",
    "external_databases_integration_report.json",
    "processed_datasets_conformance_report.json",
}


@dataclass(frozen=True)
class FileManifestEntry:
    path: str
    release_role: str
    format: str
    size_bytes: int
    sha256: str
    row_count: int | None
    sqlite_tables: dict[str, int] | None
    json_top_level_keys: list[str] | None


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return sum(1 for _ in reader)


def _sqlite_table_counts(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with sqlite3.connect(path) as conn:
        table_names = [
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        ]
        for table in table_names:
            escaped = table.replace('"', '""')
            counts[table] = int(conn.execute(f'SELECT COUNT(*) FROM "{escaped}"').fetchone()[0])
    return counts


def _json_top_level_keys(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, dict):
        return sorted(str(key) for key in payload.keys())
    return []


def _classify_file(path: Path) -> str:
    name = path.name
    if name.endswith("_metadata.json") or name.endswith("_report.json") or name.endswith("_summary.json"):
        return "metadata_or_report"
    if name.endswith(".sqlite"):
        return "sqlite_database"
    if name.endswith(".csv"):
        return "tabular_dataset"
    if name.endswith(".json"):
        return "json_metadata"
    return "supporting_file"


def _is_intermediate(name: str) -> bool:
    if name in INTERMEDIATE_EXCLUDE_NAMES:
        return True
    return any(name.startswith(prefix) for prefix in INTERMEDIATE_EXCLUDE_PREFIXES)


def _processed_files() -> list[Path]:
    files: list[Path] = []
    for pattern in PROCESSED_FILE_PATTERNS:
        files.extend(PROCESSED_DIR.glob(pattern))
    output = []
    for path in sorted(set(files)):
        if path.name in EXCLUDE_NAMES or path.name in TRANSIENT_TEXT_FILES:
            continue
        if any(path.name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES):
            continue
        if _is_intermediate(path.name):
            continue
        if path.is_file():
            output.append(path)
    return output


def _manifest_entry(path: Path) -> FileManifestEntry:
    row_count: int | None = None
    sqlite_tables: dict[str, int] | None = None
    json_keys: list[str] | None = None

    if path.suffix.lower() == ".csv":
        row_count = _csv_row_count(path)
    elif path.suffix.lower() == ".sqlite":
        sqlite_tables = _sqlite_table_counts(path)
        row_count = sum(sqlite_tables.values())
    elif path.suffix.lower() == ".json":
        json_keys = _json_top_level_keys(path)

    return FileManifestEntry(
        path=_relative(path),
        release_role=_classify_file(path),
        format=path.suffix.lower().lstrip("."),
        size_bytes=path.stat().st_size,
        sha256=_sha256(path),
        row_count=row_count,
        sqlite_tables=sqlite_tables,
        json_top_level_keys=json_keys,
    )


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_checksums(entries: list[FileManifestEntry]) -> None:
    lines = [f"{entry.sha256}  {entry.path}" for entry in entries]
    (RELEASE_DIR / "checksums_sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_readme(entries: list[FileManifestEntry], total_size: int) -> None:
    text = f"""# UBY Time Dataset v{RELEASE_VERSION}

## Overview

This release packages the processed datasets generated by the UBY Time Python
reference implementation.  The dataset maps heterogeneous time-bearing records
into a common UBY cross-scale temporal labeling framework while preserving source
time fields and uncertainty metadata.

The release includes:

- PBDB Animalia / Phanerozoic fossil occurrence UBY annotations.
- PBDB collection-level UBY annotations for sampling-control analyses.
- PBDB Dinosauria UBY annotations.
- ICS chronostratigraphic chart UBY annotations.
- NASA Exoplanet Archive discovery-time annotations.
- NASA/JPL CNEOS fireball event annotations.
- SIMBAD high-redshift object UBY annotations.
- USGS earthquake benchmark annotations.
- External-database UBY cross-reference records.
- A unified cross-domain UBY timeline.
- A forcing-event compilation.

Intermediate analytical artefacts (end-Ordovician signal extractions,
extinction-sensitivity sweeps, mass-extinction lead/lag databases, periodogram
reports, diversity curves, etc.) are deliberately excluded from the deposition:
they remain fully reproducible from the source datasets and the scripts in
`examples/`.

## Release identity

- Dataset release: `{RELEASE_ID}`
- UBY software/specification version: `0.1.0`
- Recommended data license: Creative Commons Attribution 4.0 International (`CC-BY-4.0`)
- Code license: BSD 3-Clause, as specified in `LICENSE`
- Total archived processed-file size: {total_size:,} bytes
- Number of processed files in manifest: {len(entries)}

## Important scientific boundary

UBY is a temporal annotation and interoperability layer.  It does not replace
source time systems such as UTC, Julian Day, Ma BP, geological intervals, or
cosmological model-derived ages.  UBY labels are auxiliary indices and must be
interpreted with the original source fields and explicit uncertainty metadata.

For PBDB fossil records, representative UBY values are derived from PBDB
`min_ma`/`max_ma` interval midpoints.  These midpoint labels are useful for
indexing and large-scale comparison but must not be interpreted as exact
biological extinction or origination times.

## How to cite

If this dataset is used, cite the Zenodo DOI assigned to this release and cite
the original data providers listed in `LICENSES_AND_ATTRIBUTION.md`.

Suggested citation:

> Han, Bo, and UBY Specification Contributors. UBY-labeled cross-scale temporal
> database for Phanerozoic fossil occurrences, forcing events, astronomical
> records, and mass-extinction dynamics. Version {RELEASE_VERSION}. Zenodo.
> DOI: {ZENODO_DOI}.

## Integrity verification

Use:

```bash
sha256sum -c checksums_sha256.txt
```

On Windows PowerShell, checksums can be verified with:

```powershell
Get-Content checksums_sha256.txt | ForEach-Object {{
  $parts = $_ -split "  ", 2
  $expected = $parts[0]
  $file = $parts[1]
  $actual = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
  if ($actual -ne $expected) {{ Write-Error "Checksum mismatch: $file" }}
}}
```

## Reproducibility

Processing scripts are located in `examples/`.  The most important scripts are:

- `download_pbdb_animalia_phanerozoic_all.py`
- `annotate_pbdb_animalia_phanerozoic.py`
- `download_pbdb_collections_animalia_phanerozoic.py`
- `annotate_pbdb_collections_animalia_phanerozoic.py`
- `annotate_pbdb_dinosauria.py`
- `annotate_ics_chart.py`
- `annotate_nasa_exoplanet_archive.py`
- `annotate_nasa_jpl_cneos_fireballs.py`
- `annotate_simbad_high_redshift_objects.py`
- `benchmark_usgs_earthquake_annotation.py`
- `build_external_databases_uby.py`
- `build_unified_timeline_db_streaming.py`
- `build_forcing_event_compilation.py`

## Files

See `dataset_manifest.json` for a complete machine-readable file inventory,
row counts, SQLite table counts, and SHA-256 checksums.
"""
    (RELEASE_DIR / "README_DATASET.md").write_text(text, encoding="utf-8")


def _write_data_dictionary(entries: list[FileManifestEntry]) -> None:
    lines = [
        "# Data Dictionary",
        "",
        "This file summarizes columns for CSV datasets included in the UBY Time data release.",
        "Types are inferred at the exchange-format level; most CSV fields are serialized as text for transparency.",
        "",
    ]

    for entry in entries:
        path = ROOT / entry.path
        if path.suffix.lower() != ".csv":
            continue
        lines.append(f"## `{entry.path}`")
        lines.append("")
        lines.append(f"- Rows: {entry.row_count}")
        lines.append("")
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            fields = reader.fieldnames or []
        lines.append("| Field | Description | Unit / convention |")
        lines.append("|---|---|---|")
        for field in fields:
            description, unit = _field_description(field)
            lines.append(f"| `{field}` | {description} | {unit} |")
        lines.append("")

    (RELEASE_DIR / "DATA_DICTIONARY.md").write_text("\n".join(lines), encoding="utf-8")


def _field_description(field: str) -> tuple[str, str]:
    descriptions = {
        "uby_value": ("Representative UBY numeric label derived from source time.", "UBY years"),
        "uby_expression": ("Human-readable full UBY expression.", "UBY syntax"),
        "uby_magnitude_expression": ("Compact magnitude-style UBY expression.", "UBY syntax"),
        "uncertainty_years": ("Half-width or propagated time uncertainty.", "years"),
        "representative_ma_midpoint": ("Midpoint of geological age interval.", "Ma BP"),
        "years_before_present_midpoint": ("Midpoint expressed as years before present.", "years BP"),
        "max_ma": ("Older bound of geological age interval.", "Ma BP"),
        "min_ma": ("Younger bound of geological age interval.", "Ma BP"),
        "precision_level": ("UBY precision level assigned by source time type.", "Level 1/2/3"),
        "model_version": ("Model or convention used for UBY conversion.", "text"),
        "uby_version": ("UBY specification/software version.", "semantic version"),
        "anchor_id": ("UBY anchor identifier.", "text"),
        "anchor_jd": ("Julian Day of anchor.", "JD"),
        "anchor_uby": ("UBY value of anchor.", "UBY years"),
        "source_dataset": ("Source dataset or API.", "text"),
        "source_record_id": ("Source record identifier.", "text"),
        "source_record_uri": ("Source record URI if available.", "URI"),
        "event_label": ("Human-readable event label.", "text"),
        "event_type": ("Event category.", "controlled text"),
        "longitude": ("Modern longitude when available.", "decimal degrees"),
        "latitude": ("Modern latitude when available.", "decimal degrees"),
        "paleolongitude": ("Paleogeographic longitude when available.", "decimal degrees"),
        "paleolatitude": ("Paleogeographic latitude when available.", "decimal degrees"),
    }
    if field in descriptions:
        return descriptions[field]
    if field.endswith("_ma"):
        return ("Age or duration field.", "Ma")
    if field.endswith("_years") or field.endswith("_years_bp"):
        return ("Year-valued time field.", "years")
    if "count" in field or field.endswith("_rows") or field.endswith("_taxa"):
        return ("Count field.", "integer")
    if "fraction" in field or "ratio" in field:
        return ("Ratio or fraction field.", "dimensionless")
    return ("Source or derived attribute; see dataset README and source script for exact derivation.", "text")


def _write_quality_control(entries: list[FileManifestEntry]) -> None:
    csv_entries = [entry for entry in entries if entry.format == "csv"]
    sqlite_entries = [entry for entry in entries if entry.format == "sqlite"]
    json_entries = [entry for entry in entries if entry.format == "json"]

    report = {
        "release_id": RELEASE_ID,
        "generated_at_unix": time.time(),
        "checks": {
            "processed_directory_exists": PROCESSED_DIR.exists(),
            "file_manifest_entries": len(entries),
            "csv_file_count": len(csv_entries),
            "sqlite_file_count": len(sqlite_entries),
            "json_file_count": len(json_entries),
            "all_files_nonempty": all(entry.size_bytes > 0 for entry in entries),
            "all_csv_have_row_counts": all(entry.row_count is not None for entry in csv_entries),
            "all_sqlite_have_table_counts": all(bool(entry.sqlite_tables) for entry in sqlite_entries),
            "sha256_generated_for_all_files": all(bool(entry.sha256) for entry in entries),
        },
        "summary_counts": {
            "total_size_bytes": sum(entry.size_bytes for entry in entries),
            "total_csv_rows": sum(entry.row_count or 0 for entry in csv_entries),
            "total_sqlite_table_rows": sum(entry.row_count or 0 for entry in sqlite_entries),
        },
        "known_limitations": [
            "PBDB fossil occurrence representative UBY values use geological interval midpoints and must not be treated as exact last appearances.",
            "Some forcing-event records are a first-pass literature-backed compilation and should be treated as a curated seed layer rather than an exhaustive authority.",
            "End-Ordovician pre-boundary disappearance is a candidate signal with explicit sampling caveats.",
            "Collection-level PBDB data improve sampling controls but do not by themselves replace full shareholder quorum subsampling or preservation modeling.",
        ],
        "status": "pass",
    }
    _write_json(RELEASE_DIR / "quality_control_report.json", report)

    text = f"""# Quality Control

The generated `quality_control_report.json` summarizes automated release checks.

## Automated checks

- Processed data directory exists.
- All manifest files are non-empty.
- SHA-256 checksums were generated for every archived processed file.
- CSV row counts were computed.
- SQLite table row counts were computed.
- JSON top-level keys were recorded.

## Summary

- CSV files: {len(csv_entries)}
- SQLite files: {len(sqlite_entries)}
- JSON files: {len(json_entries)}
- Total CSV rows: {report["summary_counts"]["total_csv_rows"]:,}
- Total SQLite table rows: {report["summary_counts"]["total_sqlite_table_rows"]:,}

## Scientific limitations

This release is intended for reusable time-labeling, interoperability, and
hypothesis generation.  Some downstream scientific analyses, especially
mass-extinction timing claims, require additional uncertainty propagation,
collection-level standardization, subsampling, and domain-specialist validation.
"""
    (RELEASE_DIR / "QUALITY_CONTROL.md").write_text(text, encoding="utf-8")


def _write_license_and_attribution() -> None:
    data_license = """# Dataset License: Creative Commons Attribution 4.0 International

The UBY-derived dataset files and release metadata generated by this project are
released under the Creative Commons Attribution 4.0 International License
(CC-BY-4.0), unless a source dataset imposes additional attribution requirements.

You are free to:

- Share — copy and redistribute the material in any medium or format.
- Adapt — remix, transform, and build upon the material for any purpose, even commercially.

Under the following terms:

- Attribution — You must give appropriate credit, provide a link to the license,
  and indicate if changes were made.

License text: https://creativecommons.org/licenses/by/4.0/
"""
    (RELEASE_DIR / "LICENSE_DATA_CC_BY_4.0.md").write_text(data_license, encoding="utf-8")

    attribution = """# Licenses and Attribution

## UBY-derived data release

The UBY-derived annotations, manifests, metadata, and derived analysis tables are
released under CC-BY-4.0.

## Code

The UBY Time Python reference implementation is released under the BSD 3-Clause
License.  See the repository `LICENSE` file.

## Source data providers

This release integrates and annotates records derived from external public
scientific databases.  Users must cite and acknowledge the original data
providers when using the corresponding records.

### Paleobiology Database (PBDB)

- Source: https://paleobiodb.org
- Used for fossil occurrences and collection-level records.
- Attribution: Data from the Paleobiology Database; UBY annotation added by
  uby-time.
- Users should cite PBDB and relevant PBDB data contributors according to PBDB
  citation guidance.

### International Chronostratigraphic Chart / ICS-related data

- Used for geological interval reference records.
- Users should cite the International Commission on Stratigraphy and the source
  chart/repository used to construct the local raw files.

### NASA Exoplanet Archive

- Source: https://exoplanetarchive.ipac.caltech.edu
- Used for exoplanet discovery records.
- Users should cite NASA/IPAC Exoplanet Archive according to archive guidance.

### NASA/JPL CNEOS Fireball Data

- Source: NASA/JPL Center for Near Earth Object Studies.
- Used for fireball event records.
- Users should cite NASA/JPL CNEOS according to CNEOS guidance.

### USGS Earthquake Catalog

- Source: https://earthquake.usgs.gov
- Used for earthquake benchmark records.
- Users should cite USGS Earthquake Hazards Program.

### SIMBAD / CDS

- Source: SIMBAD astronomical database, CDS, Strasbourg.
- Used for high-redshift object demonstration records.
- Users should cite SIMBAD/CDS according to CDS citation guidance.

### Literature-backed forcing-event compilation

- Used for first-pass forcing/extinction lead-lag examples.
- Users should cite the DOI/source records listed in the forcing-event table.
"""
    (RELEASE_DIR / "LICENSES_AND_ATTRIBUTION.md").write_text(attribution, encoding="utf-8")


def _write_availability_docs() -> None:
    data_availability = f"""# Data Availability

The UBY Time Dataset v{RELEASE_VERSION} is archived on Zenodo under a Creative
Commons Attribution 4.0 International (CC-BY-4.0) license.

- Dataset release: `{RELEASE_ID}`
- DOI: {ZENODO_DOI}
- Landing page: {ZENODO_DOI_URL}
- License: CC-BY-4.0
- Files: listed in `dataset_manifest.json`
- Integrity: `checksums_sha256.txt`

Recommended citation:

> Han, Bo, and UBY Specification Contributors. UBY-labeled cross-scale temporal
> database for Phanerozoic fossil occurrences, forcing events, astronomical
> records, and mass-extinction dynamics. Version {RELEASE_VERSION}. Zenodo.
> DOI: {ZENODO_DOI}.
"""
    (RELEASE_DIR / "DATA_AVAILABILITY.md").write_text(data_availability, encoding="utf-8")

    code_availability = f"""# Code Availability

The full processing workflow is archived through GitHub and linked to Zenodo.

- GitHub repository: {GITHUB_REPOSITORY_URL}
- Recommended release tag: `v{RELEASE_VERSION}`
- Code license: BSD 3-Clause

Repository contents:

- `src/uby_time/` — UBY Time Python package.
- `examples/` — complete data processing scripts.
- `tests/` — regression and integration tests.
- `schemas/` — JSON Schemas.
- `specs/` and `docs/` — specification and user documentation.
- `pyproject.toml` — reproducible Python package metadata.
- `data_release/{RELEASE_ID}/` — release metadata and manifests.

Recommended release steps:

1. Commit all source code, scripts, schemas, and documentation.
2. Tag a release, for example `v{RELEASE_VERSION}`.
3. Enable GitHub-Zenodo integration to obtain a software DOI.
4. Record the software DOI in this document if minted.
"""
    (RELEASE_DIR / "CODE_AVAILABILITY.md").write_text(code_availability, encoding="utf-8")


def _write_zenodo_metadata(entries: list[FileManifestEntry]) -> None:
    metadata = {
        "title": DATASET_TITLE,
        "upload_type": "dataset",
        "description": (
            "A UBY-labeled, uncertainty-aware cross-scale temporal database integrating "
            "Paleobiology Database fossil occurrences and collections, chronostratigraphic "
            "records, astronomical records, Earth event benchmarks, forcing events, and "
            "derived mass-extinction dynamics. The dataset includes CSV, SQLite, and JSON "
            "outputs plus checksums, manifest, data dictionary, and quality-control reports."
        ),
        "creators": CREATORS,
        "version": RELEASE_VERSION,
        "license": "cc-by-4.0",
        "access_right": "open",
        "keywords": [
            "UBY",
            "time labeling",
            "cross-scale time",
            "Paleobiology Database",
            "mass extinction",
            "Phanerozoic",
            "chronostratigraphy",
            "uncertainty",
            "SQLite",
            "scientific data",
        ],
        "related_identifiers": [
            {
                "identifier": GITHUB_REPOSITORY_URL,
                "relation": "isSupplementTo",
                "scheme": "url",
            },
            {
                "identifier": "https://paleobiodb.org",
                "relation": "isDerivedFrom",
                "scheme": "url",
            },
            {
                "identifier": "https://exoplanetarchive.ipac.caltech.edu",
                "relation": "isDerivedFrom",
                "scheme": "url",
            },
            {
                "identifier": "https://earthquake.usgs.gov",
                "relation": "isDerivedFrom",
                "scheme": "url",
            },
            {
                "identifier": "https://simbad.cds.unistra.fr",
                "relation": "isDerivedFrom",
                "scheme": "url",
            },
        ],
        "notes": (
            "UBY labels are auxiliary time indices. Users must preserve and interpret the "
            "source time fields and uncertainty metadata. Geological fossil occurrence "
            "midpoints must not be treated as exact event times."
        ),
        "communities": [],
        "references": [
            "Paleobiology Database, https://paleobiodb.org",
            "NASA Exoplanet Archive, https://exoplanetarchive.ipac.caltech.edu",
            "USGS Earthquake Hazards Program, https://earthquake.usgs.gov",
            "SIMBAD astronomical database, CDS, Strasbourg, https://simbad.cds.unistra.fr",
        ],
        "file_count": len(entries),
        "total_size_bytes": sum(entry.size_bytes for entry in entries),
    }
    _write_json(RELEASE_DIR / "zenodo_metadata.json", metadata)

    # Zenodo reads .zenodo.json for GitHub repository archival metadata.
    github_metadata = {
        "title": "UBY Time Python reference implementation and dataset processing workflow",
        "upload_type": "software",
        "description": (
            "Python reference implementation and reproducible processing workflow for "
            "the UBY cross-scale time labeling dataset."
        ),
        "creators": CREATORS,
        "version": RELEASE_VERSION,
        "license": "bsd-3-clause",
        "keywords": ["UBY", "time labeling", "Python", "scientific data", "reproducibility"],
    }
    _write_json(ROOT / ".zenodo.json", github_metadata)


def _write_github_zenodo_guide() -> None:
    guide = f"""# GitHub and Zenodo Release Guide

This guide prepares the UBY project for long-term archival, DOI assignment, and
global reuse.

## 1. Repository preparation

1. Ensure the repository contains:
   - `src/uby_time/`
   - `examples/`
   - `tests/`
   - `schemas/`
   - `docs/`
   - `specs/`
   - `README.md`
   - `LICENSE`
   - `.zenodo.json`
   - `data_release/{RELEASE_ID}/`

2. Do not commit very large raw API batch files unless Git LFS is explicitly
   configured.  For GitHub, commit the code, schemas, documentation, and release
   metadata.  For Zenodo dataset deposition, upload the large processed data
   files directly.

## 2. Code archival through GitHub-Zenodo

1. Create or update the public GitHub repository.
2. Push all source code and release metadata.
3. Enable the repository in Zenodo GitHub integration.
4. Create a GitHub release tagged `v{RELEASE_VERSION}`.
5. Zenodo will archive the GitHub release and mint a software DOI.
6. Add the software DOI to `CODE_AVAILABILITY.md`.

## 3. Dataset archival through Zenodo

Create a separate Zenodo upload with upload type `Dataset`.

Recommended files to upload:

- All files listed in `dataset_manifest.json`.
- `README_DATASET.md`
- `DATA_DICTIONARY.md`
- `DATA_AVAILABILITY.md`
- `CODE_AVAILABILITY.md`
- `LICENSE_DATA_CC_BY_4.0.md`
- `LICENSES_AND_ATTRIBUTION.md`
- `QUALITY_CONTROL.md`
- `quality_control_report.json`
- `dataset_manifest.json`
- `checksums_sha256.txt`
- `zenodo_metadata.json`

Use metadata from `zenodo_metadata.json`.

## 4. License

- Dataset: CC-BY-4.0.
- Code: BSD 3-Clause.

## 5. After DOI assignment

Update:

- `README_DATASET.md`
- `DATA_AVAILABILITY.md`
- project `README.md`
- manuscript or preprint citation
- GitHub release notes

with the final Zenodo dataset DOI and GitHub software DOI.
"""
    (RELEASE_DIR / "GITHUB_ZENODO_RELEASE_GUIDE.md").write_text(guide, encoding="utf-8")


def build_release_package() -> dict[str, Any]:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    entries = [_manifest_entry(path) for path in _processed_files()]
    total_size = sum(entry.size_bytes for entry in entries)

    manifest = {
        "release_id": RELEASE_ID,
        "release_version": RELEASE_VERSION,
        "title": DATASET_TITLE,
        "generated_at_unix": time.time(),
        "root": str(ROOT.as_posix()),
        "license": "CC-BY-4.0 for UBY-derived data and release metadata; BSD-3-Clause for code",
        "file_count": len(entries),
        "total_size_bytes": total_size,
        "files": [asdict(entry) for entry in entries],
    }

    _write_json(RELEASE_DIR / "dataset_manifest.json", manifest)
    _write_checksums(entries)
    _write_readme(entries, total_size)
    _write_data_dictionary(entries)
    _write_quality_control(entries)
    _write_license_and_attribution()
    _write_availability_docs()
    _write_zenodo_metadata(entries)
    _write_github_zenodo_guide()

    return manifest


def main() -> int:
    manifest = build_release_package()
    print(f"Release directory: {RELEASE_DIR}")
    print(f"Manifest: {RELEASE_DIR / 'dataset_manifest.json'}")
    print(f"Files in manifest: {manifest['file_count']}")
    print(f"Total size bytes: {manifest['total_size_bytes']}")
    print(f"Checksums: {RELEASE_DIR / 'checksums_sha256.txt'}")
    print(f"Zenodo metadata: {RELEASE_DIR / 'zenodo_metadata.json'}")
    print(f"GitHub Zenodo metadata: {ROOT / '.zenodo.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
