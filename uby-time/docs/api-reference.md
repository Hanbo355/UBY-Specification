# API Reference

This page lists the minimum public API exposed by `uby_time`.

## Conversion

```python
jd_to_uby(jd)
uby_to_jd(uby_value)
iso_to_uby(iso_time)
uby_to_iso(uby_value)
astronomical_year_to_uby(year)
bc_year_to_uby(bc_year)
redshift_to_uby(z)
```

## Formatting

```python
format_full(uby)
format_magnitude(uby)
format_scientific(uby)
format_academic_mnemonic(astronomical_year)
format_friendly_mnemonic(year, era="AD")
```

## Parsing and validation

```python
parse_uby_expression(expression)
validate_uby_time(uby)
infer_precision_level(...)
```

## Serialization

```python
to_dict(uby)
from_dict(data)
to_json(uby)
from_json(text)
```

All Decimal-valued fields are serialized as strings.

## Pandas

```python
register_pandas_accessors()
```

This function returns `False` if pandas is not installed.
