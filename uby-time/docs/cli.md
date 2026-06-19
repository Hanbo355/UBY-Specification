# CLI Guide

`uby-time` exposes the `uby` command after installation.

## Convert ISO time

```bash
uby convert iso 2026-01-01T00:00:00Z
```

## Convert Julian Date

```bash
uby convert jd 2461041.5
```

## Convert astronomical year

```bash
uby convert year 2026
uby convert year -220 --include-model
```

## Convert BC year

```bash
uby convert bc 221
```

## Parse expression

```bash
uby parse "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"
uby parse "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]" --format json
```

## Validate expression

```bash
uby validate "UBY 137720+002026 [model=LCDM-Planck2018] [spec=0.1.0]"
```

## Lint specification documents

Scan Markdown/specification documents for embedded UBY expressions:

```bash
uby lint spec "../UBY-TLS-WD-0.1.0.md"
uby lint spec "../UBY-TLS-WD-0.1.0.md" --format json
```

By default, formal examples without `[spec=<version>]` produce an error. To allow missing specification version tags:

```bash
uby lint spec draft-notes.md --allow-missing-spec
```

## Reformat expression

```bash
uby format full "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]"
uby format magnitude "UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]"
uby format scientific "UBY 380000 [model=LCDM-Planck2018] [spec=0.1.0]"
```

## Redshift conversion

Requires optional `astropy` support:

```bash
python -m pip install -e ".[cosmology]"
uby redshift 1100
```
