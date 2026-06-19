# uby-time

[![CI](https://github.com/uby-spec/uby-time/actions/workflows/ci.yml/badge.svg)](https://github.com/uby-spec/uby-time/actions/workflows/ci.yml)

Python reference implementation for the **UBY Cross-scale Time Labeling Specification — Working Draft 0.1.0**.

## Author

**Han Bo** is the original author of this reference implementation, with contributions from the UBY Specification Contributors.

## License and attribution

This project is released under the **BSD 3-Clause License**.

The license permits redistribution and use in source and binary forms, with or without modification, provided that the copyright notice, license conditions, and disclaimer are retained.

Required copyright attribution:

```text
Copyright (c) 2026, Han Bo and UBY Specification Contributors
```

For environments where Unicode display is unreliable, the ASCII-safe attribution form is:

```text
Copyright (c) 2026, Han Bo and UBY Specification Contributors
```

The license also prohibits using the names `Han Bo`, `UBY`, `UBY Time`, or `UBY Specification Contributors` to endorse or promote derived products without prior written permission.

See [`LICENSE`](LICENSE) for the full license terms.

> UBY is a conventional cross-scale time labeling framework, not an absolute physical time system.
> This library does not replace UTC, TAI, JD, MJD, GNSS time, geological timescales, or authoritative scientific datasets.

## Status

`uby-time 0.1.0` is a reference implementation prototype.

| Field | Value |
| --- | --- |
| Specification | UBY Cross-scale Time Labeling Specification |
| Specification stage | Working Draft |
| Specification version | `0.1.0` |
| Implementation version | `0.1.0` |
| Package maturity | Experimental / pre-1.0 |
| Release target | TestPyPI first |

It includes core conversion, formatting, parsing, validation, serialization, CLI, interoperability vectors, JSON Schema, specification linting, docs, and optional extension entry points.

## Install

```bash
pip install -e .
```

For redshift/cosmology support:

```bash
pip install -e ".[cosmology]"
```

For pandas support:

```bash
pip install -e ".[pandas]"
```

For documentation tools:

```bash
pip install -e ".[docs]"
```

For development:

```bash
pip install -e ".[dev]"
```

From TestPyPI after a test release:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ uby-time
```

## Quick start

```python
from uby_time import iso_to_uby, format_full, format_academic_mnemonic

uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))
print(format_academic_mnemonic(-220))
```

Expected output:

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]
```

## Precision levels

UBY values must be interpreted with an explicit precision level.

| Level | Meaning | Typical use | Key restriction |
| --- | --- | --- | --- |
| `Level 1` | Relative near-Earth measurement/indexing level | ISO/JD/year conversion within about ±1,000,000 years around the civil-era anchor | UBY does not improve the precision of the source record |
| `Level 2` | Proportional narrative level | geology, deep-time timelines, cross-scale visualization | model/source version and effective digits must be explicit |
| `Level 3` | Model-dependent cosmological level | redshift-derived early-universe ages | model versions must be declared; cross-model values are not directly comparable |

## Version fields

UBY separates three version concepts:

| Field | Example | Meaning |
| --- | --- | --- |
| `uby_version` / `[spec=...]` | `0.1.0` | UBY syntax, fields, anchor rules, and conformance rules |
| `model_version` / `[model=...]` | `LCDM-Planck2018` | cosmological or deep-time model/parameter provenance |
| implementation version | `uby-time/0.1.0` | this Python package/tool version, usually stored in `generated_by` |

A cosmological parameter update is not the same thing as a UBY specification update.  Do not use
`uby_version` as a substitute for `model_version`.

## JSON serialization

```python
from uby_time import iso_to_uby, to_json, from_json

uby = iso_to_uby("2026-01-01T00:00:00Z")
payload = to_json(uby)
restored = from_json(payload)
```

`Decimal` values are serialized as strings to avoid float precision loss.

## Cosmology uncertainty note

`redshift_to_uby()` uses `astropy.cosmology.<model>.age(z)` for the age calculation.  When
`include_uncertainty=True`, the emitted `uncertainty_years` value is a heuristic annotation for
downstream labeling and QA.  It is not a strict covariance propagation and is not a substitute for
re-integrating the cosmology under a documented parameter set.

## CLI

```bash
uby convert iso 2026-01-01T00:00:00Z
uby convert year 2026
uby convert bc 221
uby parse "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"
uby validate "UBY 137720+002026 [model=LCDM-Planck2018] [spec=0.1.0]"
uby format magnitude "UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]"
uby lint spec "../UBY-TLS-WD-0.1.0.md"
```

Structured output supports text, JSON, and CSV for conversion, parse, validate, redshift, and lint
commands where applicable:

```bash
uby convert iso 2026-01-01T00:00:00Z --format json
uby convert iso 2026-01-01T00:00:00Z --format csv
uby validate "UBY 380K [spec=0.1.0]" --format csv
```

## Optional pandas accessor

```python
from uby_time import register_pandas_accessors

registered = register_pandas_accessors()
```

If pandas is unavailable, `registered` is `False`.

## Precision boundary

`uby-time` is suitable for labeling, indexing, education, archival metadata, and cross-scale narrative tooling.

It must not be used for:

- legal timestamps;
- navigation;
- high-precision timing;
- financial settlement;
- authoritative scientific primary records.

## Development checks

The default pytest suite is intentionally kept fast and focused on the reference implementation core:
conversion, formatting, parsing, validation, serialization, CLI behavior, interoperability vectors,
schemas, and lightweight extension contracts.

Real-dataset annotation, database generation, and scientific analysis pipelines are marked as
`data`, `slow`, and `integration`, and are excluded from the default test run.

```bash
python -m pytest -q --tb=short
python -m build
python -m twine check dist/*
```

Run the real-data integration pipelines explicitly when needed:

```bash
python -m pytest -q -m "data"
python -m pytest -q -m "integration"
```

For release-candidate validation, also run the real specification lint when the specification document is available next to this package checkout:

```bash
uby lint spec "../UBY-TLS-WD-0.1.0.md"
```

## Documentation

A MkDocs configuration is provided in `mkdocs.yml`.

```bash
mkdocs serve
```
