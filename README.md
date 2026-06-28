# UBY Specification

**Universal Big-bang Year (UBY) Cross-scale Time Labeling Specification**

UBY is a conventional time-coordinate system that places cosmic history, geological history, human history, and long-term future events on a single monotonically increasing labeling axis anchored to the Big Bang. It uses the comoving-time origin as the conventional zero point and the standard Julian year as the base unit.

UBY is **not** an absolute time system, an authoritative timekeeping system, or a replacement for native time representations (UTC, JD, BP, Ma, redshift, etc.). It is a supplementary auxiliary time label designed for cross-scale visualization, long-term archival, data indexing, and cross-domain data integration.

- **Current version**: 0.1.0 (Working Draft)
- **Release date**: 2026-06-28
- **Status**: Exploratory working draft; not yet a formal specification

---

## Repository contents

| Path | Description |
| --- | --- |
| [`UBY-TLS-WD-0.1.0.md`](UBY-TLS-WD-0.1.0.md) | English specification (authoritative) |
| [`UBY-TLS-WD-0.1.0-CN.md`](UBY-TLS-WD-0.1.0-CN.md) | Chinese reference translation |
| [`UBY-Time-Python-Reference-Implementation-Development-Guide-WD-0.1.0.md`](UBY-Time-Python-Reference-Implementation-Development-Guide-WD-0.1.0.md) | Python reference implementation development guide |
| [`uby-time/`](uby-time/) | Python reference implementation and data processing pipeline |

---

## Key features

- **Dual-track design**: a semantic track that preserves native time representations, and a numeric projection track that maps every event onto a single real-valued UBY axis.
- **Cross-scale**: covers ~13.8 billion years from the Big Bang to the present, across cosmology, geology, biology, and human history.
- **Cross-domain JOIN**: enables proximity-based joins across heterogeneous time units (redshift, Ma, ka, BP, JD, UTC) via a single sortable numeric axis.
- **Versioned and traceable**: every UBY expression carries `[spec=...]` and `[model=...]` tags; a provenance framework satisfies FAIR principles.
- **Null-hypothesis testing protocol**: built-in methodology for validating cross-domain signals against sampling and dating artifacts.

---

## Quick start

### Install the Python package

```bash
cd uby-time
pip install -e .
```

### Convert a time value to UBY

```python
from uby_time import iso_to_uby, redshift_to_uby, format_full

# ISO 8601 date -> UBY
uby = iso_to_uby("2026-06-28T00:00:00")
print(format_full(uby))
# UBY 13787002026.48733744010951403 [model=LCDM-Planck2018] [spec=0.1.0]

# Redshift z = 7.5 (high-redshift galaxy) -> UBY
high_z = redshift_to_uby(7.5)
print(format_full(high_z))
# UBY 694421043.861485 [model=LCDM-Planck2018] [spec=0.1.0]
```

### Parse a UBY expression

```python
from uby_time import parse_uby_expression

parsed = parse_uby_expression("UBY 13786999780 [spec=0.1.0]")
print(parsed.uby_value)   # 13786999780
print(parsed.uby_version)  # 0.1.0
```

### Run the test suite

```bash
cd uby-time
pytest
```

---

## Citation

If you use UBY in your work, please cite both the specification and the dataset:

> Han, Bo, and UBY Specification Contributors. UBY Cross-scale Time Labeling
> Specification, Working Draft 0.1.0. GitHub.
> https://github.com/Hanbo355/UBY-Specification

> Han, Bo, and UBY Specification Contributors. UBY-labeled cross-scale temporal
> database for Phanerozoic fossil occurrences, forcing events, astronomical
> records, and mass-extinction dynamics. Version 0.1.0. Zenodo.
> https://doi.org/10.5281/zenodo.20763218

---

## Data and code availability

| Resource | Location | License |
| --- | --- | --- |
| Specification & code | [GitHub](https://github.com/Hanbo355/UBY-Specification) | BSD 3-Clause |
| Processed dataset (5.8 GiB) | [Zenodo DOI 10.5281/zenodo.20763218](https://doi.org/10.5281/zenodo.20763218) | CC-BY-4.0 |

The dataset includes UBY-labeled annotations for:
- PBDB Phanerozoic fossil occurrences (Animalia, Dinosauria, collections)
- ICS chronostratigraphic chart
- NASA Exoplanet Archive discovery times
- NASA/JPL CNEOS fireball events
- SIMBAD high-redshift objects
- USGS earthquake benchmarks
- A unified cross-domain timeline (1,586,016 records)
- A forcing-event compilation

---

## Documentation

- [Specification (English, authoritative)](UBY-TLS-WD-0.1.0.md)
- [Specification (Chinese reference)](UBY-TLS-WD-0.1.0-CN.md)
- [Python implementation guide](UBY-Time-Python-Reference-Implementation-Development-Guide-WD-0.1.0.md)
- [Package README](uby-time/README.md)

A MkDocs site is available locally:

```bash
cd uby-time
mkdocs serve
```

---

## Conformance

The specification defines three conformance levels:

| Level | Scope |
| --- | --- |
| **C1 — Minimal** | UBY expression syntax compliance |
| **C2 — Indexed** | C1 plus metadata sidecar and provenance |
| **C3 — Unified** | C2 plus cross-domain JOIN and null-hypothesis testing |

See §23 of the specification for detailed conformance requirements.

---

## Out of scope

UBY **must not** be used for:

- Legal documents, contracts, or financial settlement
- Satellite navigation, aerospace telemetry, or deep-space navigation
- Replacement of atomic time, UTC, or GNSS time
- The sole authoritative time record for raw scientific data
- Engineering calculations requiring relativistic proper time

---

## License

- **Specification and code**: BSD 3-Clause License
- **Dataset**: Creative Commons Attribution 4.0 International (CC-BY-4.0)

---

## Contact

- **Repository**: https://github.com/Hanbo355/UBY-Specification
- **Issues**: https://github.com/Hanbo355/UBY-Specification/issues
- **Dataset**: https://doi.org/10.5281/zenodo.20763218
