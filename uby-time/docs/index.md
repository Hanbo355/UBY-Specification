# uby-time

`uby-time` is the Python reference implementation for the UBY Cross-scale Time Labeling Specification — Working Draft 0.1.0.

UBY is a conventional cross-scale time labeling framework. It is not an absolute physical time system and does not replace UTC, TAI, JD, MJD, GNSS time, geological timescales, or authoritative scientific datasets.

## Scope

Use `uby-time` for:

- cross-scale timeline labeling;
- long-term archival metadata;
- education and science communication;
- auxiliary data indexing;
- reference implementation and interoperability tests.

Do not use it for:

- legal timestamps;
- financial settlement;
- navigation;
- high-precision timing;
- authoritative primary scientific records.

## Quick example

```python
from uby_time import iso_to_uby, format_full

uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))
```

Output:

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
```

## Main features

- JD / ISO / astronomical year / BC year conversion.
- UBY full numeric, magnitude, scientific, academic mnemonic and friendly mnemonic formatting.
- UBY expression parsing.
- JSON-safe serialization with `Decimal` values preserved as strings.
- Validation messages for model, spec, precision and uncertainty issues.
- Optional `astropy` integration for astronomical time and redshift conversion.
- Optional pandas accessor registration.
- CLI entry point.
