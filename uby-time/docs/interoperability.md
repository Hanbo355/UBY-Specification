# Interoperability

`uby-time` provides two interchange assets for UBY Working Draft 0.1.0:

- JSON Schema: `schemas/uby-time-wd-0.1.0.schema.json`
- Interoperability vectors: `tests/fixtures/uby_wd_0_1_0_interop_vectors.json`

These files are intended for independent implementations that need to compare parser, formatter, serializer, and conversion behavior against the Python reference implementation.

## Required metadata

Formal UBY exchange records should preserve at least:

- `uby_value`
- `uby_version`
- `model_version`
- `precision_level`
- `source_time`
- `source_system`
- `rounding_rule`
- `generated_by`
- `anchor_id`
- `anchor_jd`
- `anchor_uby`

The JSON Schema follows the complete `to_dict()` output shape and also includes nullable optional uncertainty fields:

- `uncertainty_years`
- `confidence_level`
- `interval_start_uby`
- `interval_end_uby`
- `uncertainty_kind`
- `propagation_note`

## JSON safety

`Decimal` values are encoded as strings to avoid float precision loss.

Examples:

```json
{
  "uby_value": "13787002026.0",
  "anchor_jd": "2461041.5",
  "anchor_uby": "13787002026.0"
}
```

Implementations should not coerce these fields to binary floating-point values during interchange.

## JSON Schema

The schema file is:

```text
schemas/uby-time-wd-0.1.0.schema.json
```

It uses JSON Schema Draft 2020-12 and validates the JSON-safe `UBYTime` record shape emitted by `uby_time.serialization.to_dict()`.

Important schema rules:

- `uby_value`, `anchor_jd`, `anchor_uby`, and uncertainty numeric fields are decimal strings.
- `uby_value` and `anchor_uby` are non-negative decimal strings.
- `uby_version` follows semantic-version syntax, including optional prerelease suffixes.
- `model_version` is either `null` or an ASCII hyphen-separated model identifier.
- `precision_level` is one of `Level 1`, `Level 2`, or `Level 3`.
- Additional properties are rejected.

The schema deliberately allows `model_version: null` so that Level 1 civil-time records and partially specified interchange data can be represented. Validation policy still requires a model for Level 2 and Level 3 records.

## Interoperability vectors

The vector file is:

```text
tests/fixtures/uby_wd_0_1_0_interop_vectors.json
```

It covers:

- ISO-to-UBY conversion at the default anchor;
- ISO-to-UBY conversion before the default anchor;
- astronomical year conversion;
- BC year conversion;
- full numeric expressions;
- magnitude expressions;
- scientific notation with `×` and ASCII `x`;
- academic mnemonics;
- friendly mnemonics;
- missing `[spec=...]` warnings;
- missing model warnings for Level 2 expressions;
- mnemonic-prefix/model mismatch warnings.

Each vector has a stable `id`, a `kind`, and expected values for the relevant conversion or parser behavior.

## Running interoperability tests

Run only the schema/vector tests:

```bash
python -m pytest tests/test_interop_vectors_schema.py -q
```

Run the full test suite:

```bash
python -m pytest -q
```

For local source-tree execution without installing the package, set `PYTHONPATH=src` first. On PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/test_interop_vectors_schema.py -q
```

## Version separation

Do not confuse:

- `uby_version`: UBY specification version;
- `model_version`: cosmological model / parameter version;
- implementation version: Python package version.

## Model tags

Model tags use ASCII components separated by hyphens, for example:

```text
LCDM-Planck2018
LCDM-Planck2018-base
Custom-ArchiveA-2026
Scenario-FutureA
```

## Mnemonic prefixes

Known mnemonic prefixes include:

```text
LCDM-Planck2018 -> 137870
LCDM-WMAP9 -> 137720
LCDM-SH0ES2022 -> 138000
```

Mismatches should produce a `MNEMONIC_MODEL_MISMATCH` warning.
