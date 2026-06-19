# Quickstart

## Install

For local development:

```bash
python -m pip install -e .
```

For development tools:

```bash
python -m pip install -e ".[dev]"
```

For optional cosmology support:

```bash
python -m pip install -e ".[cosmology]"
```

## Convert ISO time to UBY

```python
from uby_time import iso_to_uby, format_full

uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))
```

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
```

## Convert astronomical year

```python
from uby_time import astronomical_year_to_uby, format_academic_mnemonic

uby = astronomical_year_to_uby(-220)
print(uby.uby_value)
print(format_academic_mnemonic(-220))
```

```text
13786999780
UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]
```

## Parse an expression

```python
from uby_time import parse_uby_expression

parsed = parse_uby_expression("UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]")
print(parsed.notation)
print(parsed.uby_value)
```

## JSON serialization

```python
from uby_time import iso_to_uby, to_json, from_json

uby = iso_to_uby("2026-01-01T00:00:00Z")
payload = to_json(uby)
restored = from_json(payload)
```
