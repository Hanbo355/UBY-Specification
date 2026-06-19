# UBY Cross-scale Time Labeling Specification Python Official Reference Implementation Development Guide

**Project name:** `uby-time`  
**Document type:** Official reference implementation development guide  
**Corresponding specification:** UBY Cross-scale Time Labeling Specification — Working Draft 0.1.0  
**Development guide version:** 0.1.0  
**Release stage:** Working Draft  
**Recommended language:** Python 3.10+  
**Core role:** Reference implementation, interoperability validation, formatted output, and batch conversion helper tools  
**Last updated:** 2026-06-17

---

## 0 Preliminary Boundary Statement

`uby-time` is the official Python reference implementation for the UBY Cross-scale Time Labeling Specification. Its purpose is to help developers, researchers, and content producers generate, parse, validate, and convert UBY time labels in a consistent and reproducible way.

This library MUST strictly observe the following boundaries:

1. `uby-time` is **not a timekeeping system**;
2. `uby-time` is **not a replacement for UTC, TAI, JD, MJD, GNSS time, or geological timescales**;
3. `uby-time` **does not provide absolute time in a fundamental physical sense**;
4. `uby-time` **is not intended for aerospace telemetry and control, navigation and positioning, legal documents, commercial transactions, or high-precision raw scientific records**;
5. cosmology-related computations in `uby-time` MUST rely on mature astronomy libraries such as `astropy.cosmology`; high-risk physical integration MUST NOT be implemented as the default path by the library itself;
6. UBY outputs MUST explicitly express the specification version, model version, precision level, and uncertainty semantics to avoid false precision.

---

## 1 Project Goals

### 1.1 Core Goals

The core goal of `uby-time` is to provide a Python reference implementation of UBY Working Draft 0.1.0, including:

- bidirectional Level 1 conversions among Gregorian calendar / ISO 8601 / JD and UBY;
- Level 3 conversion from redshift `z` to UBY cosmic age;
- formatting of UBY full numeric notation, magnitude shorthand, scientific notation, academic mnemonic notation, and public-friendly mnemonic notation;
- parsing and validation of UBY expressions;
- metadata management for model versions, specification versions, anchors, rounding rules, and precision levels;
- batch data processing support;
- CLI command-line tools;
- minimum interoperability test vectors.

### 1.2 Non-goals

This library does not aim to:

- replace `astropy.time`;
- replace professional geological timescale databases;
- replace high-precision calendar conversion libraries;
- maintain an authoritative cosmological-parameter database by itself;
- provide nanosecond-, microsecond-, or millisecond-level timekeeping capabilities;
- provide authoritative conversion for all historical calendar systems;
- directly handle relativistic coordinate time, proper time, or spacecraft orbital dynamics.

---

## 2 Design Principles

### 2.1 Specification First

Library behavior MUST be based solely on `UBY-TLS-WD-0.1.0.md` as the normative specification. If an implementation conflicts with the specification, the implementation SHOULD be corrected rather than allowing the implementation to define a de facto standard.

### 2.2 Metadata Must Not Be Omitted

Any formal output object MUST include at least:

- `uby_value`
- `uby_version`
- `model_version`
- `precision_level`
- `source_time`
- `source_system`
- `rounding_rule`
- `generated_by`

### 2.3 No False Precision

The library MUST NOT output precision beyond what is supported by the input data, model parameters, or normative anchor.

Examples:

- CMB decoupling may be output as `UBY 380K`; it SHOULD NOT be output by default as `UBY 380000.000000`;
- if the source says "approximately 300,000 years ago", the library SHOULD NOT output a UBY value precise to the day or second;
- the cosmic age at `z=0` MUST NOT be confused with a concrete calendar-date Level 1 anchor.

### 2.4 Separation of Model Version and Specification Version

The following version types MUST be strictly distinguished:

| Type | Example | Purpose |
| --- | --- | --- |
| Specification version | `0.1.0` | Indicates the UBY syntax, field, and rule version |
| Model version | `LCDM-Planck2018` | Indicates the cosmological model or parameter version |
| Implementation version | `uby-time 0.1.0` | Indicates the Python library version |

### 2.5 Reproducibility

The same input, same model, same anchor, and same rounding rule SHOULD produce consistent results across machines and implementations.

---

## 3 Recommended Technology Stack

### 3.1 Python Version

Recommended:

```text
Python >= 3.10
```

Rationale:

- supports modern type annotations;
- is compatible with the mainstream scientific-computing ecosystem;
- is suitable for publication to PyPI;
- supports standard-library capabilities such as `dataclasses`, `typing.Literal`, and `zoneinfo`.

### 3.2 Core Dependencies

The recommended core dependency set should remain small:

```toml
dependencies = [
  "astropy>=5.3",
  "pydantic>=2.0",
  "pandas>=2.0",
  "click>=8.0"
]
```

Explanation:

| Dependency | Purpose | Core |
| --- | --- | --- |
| `astropy` | JD, ISO time, cosmological models, and redshift-age calculation | Yes |
| `pydantic` | Metadata object validation and JSON serialization | Yes |
| `pandas` | Batch conversion and tabular data processing | Optional core |
| `click` | CLI command-line tool | Optional core |

### 3.3 Optional Dependencies

```toml
optional-dependencies = {
  "dev" = [
    "pytest",
    "pytest-cov",
    "ruff",
    "mypy",
    "build",
    "twine"
  ],
  "docs" = [
    "mkdocs",
    "mkdocs-material"
  ],
  "viz" = [
    "matplotlib",
    "plotly"
  ]
}
```

---

## 4 Project Directory Structure

The recommended directory structure is:

```text
uby-time/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ CHANGELOG.md
├─ docs/
│  ├─ index.md
│  ├─ quickstart.md
│  ├─ api.md
│  ├─ cli.md
│  ├─ precision.md
│  └─ interoperability.md
├─ src/
│  └─ uby_time/
│     ├─ __init__.py
│     ├─ constants.py
│     ├─ models.py
│     ├─ anchors.py
│     ├─ precision.py
│     ├─ conversion.py
│     ├─ formatting.py
│     ├─ parsing.py
│     ├─ validation.py
│     ├─ uncertainty.py
│     ├─ cosmology.py
│     ├─ pandas_ext.py
│     └─ cli.py
├─ tests/
│  ├─ test_conversion.py
│  ├─ test_formatting.py
│  ├─ test_parsing.py
│  ├─ test_precision.py
│  ├─ test_uncertainty.py
│  ├─ test_vectors.py
│  └─ fixtures/
│     └─ vectors_wd_0_1_0.json
└─ examples/
   ├─ basic_usage.py
   ├─ batch_pandas.py
   ├─ redshift_to_uby.py
   └─ cli_examples.md
```

---

## 5 Core Constants

### 5.1 Specification Version

```python
UBY_SPEC_VERSION = "0.1.0"
UBY_SPEC_STAGE = "Working Draft"
```

### 5.2 Standard Julian Year

```python
JULIAN_YEAR_DAYS = 365.25
JULIAN_YEAR_SECONDS = 31_557_600
```

### 5.3 Default Anchor

Corresponding to UBY Working Draft 0.1.0:

```python
DEFAULT_ANCHOR_ID = "UBY-ANCHOR-2026-01-01Z"
DEFAULT_ANCHOR_ISO = "2026-01-01T00:00:00Z"
DEFAULT_ANCHOR_JD = 2461041.5
DEFAULT_ANCHOR_UBY = 13787002026.0
DEFAULT_MODEL_VERSION = "LCDM-Planck2018"
DEFAULT_LEVEL1_RANGE_YEARS = 1_000_000
```

### 5.4 Default Rounding Rule

```python
DEFAULT_ROUNDING_RULE = "year-floor"
```

---

## 6 Core Data Models

### 6.1 Precision Level Enumeration

```python
from enum import Enum


class PrecisionLevel(str, Enum):
    LEVEL_1 = "Level 1"
    LEVEL_2 = "Level 2"
    LEVEL_3 = "Level 3"
```

Meaning:

| Enumeration | English name | Description |
| --- | --- | --- |
| `Level 1` | Relatively precise metrological level | Approximately ±1 million years around the Common Era |
| `Level 2` | Proportional narrative level | Large-scale cosmic, geological, and life-evolution narratives |
| `Level 3` | Model-dependent level | High-redshift, early-universe, and model-integration events |

### 6.2 Core `UBYTime` Object

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class UBYTime:
    uby_value: Decimal
    uby_version: str
    model_version: Optional[str]
    precision_level: PrecisionLevel
    source_time: Optional[str]
    source_system: Optional[str]
    rounding_rule: str
    generated_by: str
    anchor_id: str
    anchor_jd: Decimal
    anchor_uby: Decimal
    uncertainty_years: Optional[Decimal] = None
    confidence_level: Optional[Decimal] = None
    interval_start_uby: Optional[Decimal] = None
    interval_end_uby: Optional[Decimal] = None
    uncertainty_kind: Optional[str] = None
    propagation_note: Optional[str] = None
```

Design requirements:

- `uby_value` is RECOMMENDED to use `Decimal` to avoid floating-point display errors;
- `model_version` MUST be present for Level 2 and Level 3 precision;
- `source_time` and `source_system` SHOULD be retained whenever possible;
- `generated_by` SHOULD include the library name and version, for example `uby-time/0.1.0`.

### 6.3 `UBYAnchor` Anchor Object

```python
@dataclass(frozen=True)
class UBYAnchor:
    anchor_id: str
    anchor_iso: str
    anchor_jd: Decimal
    anchor_uby: Decimal
    model_version: str
    uby_version: str
```

Default anchor:

```python
DEFAULT_ANCHOR = UBYAnchor(
    anchor_id="UBY-ANCHOR-2026-01-01Z",
    anchor_iso="2026-01-01T00:00:00Z",
    anchor_jd=Decimal("2461041.5"),
    anchor_uby=Decimal("13787002026.0"),
    model_version="LCDM-Planck2018",
    uby_version="0.1.0",
)
```

---

## 7 Conversion Module Design

File: `conversion.py`

### 7.1 JD to UBY

Formula:

\[
UBY = \frac{JD - 2461041.5}{365.25} + 13787002026.0
\]

Function signature:

```python
def jd_to_uby(
    jd: Decimal | float | str,
    *,
    anchor: UBYAnchor = DEFAULT_ANCHOR,
    model_version: str = DEFAULT_MODEL_VERSION,
    uby_version: str = UBY_SPEC_VERSION,
    rounding_rule: str = DEFAULT_ROUNDING_RULE,
) -> UBYTime:
    ...
```

Implementation requirements:

- when the input is a `float`, it SHOULD be converted with `Decimal(str(value))`;
- decimals SHOULD NOT be truncated by default;
- if the caller specifies `rounding_rule="year-floor"`, flooring to the year may be applied at the formatting stage;
- the returned object MUST include anchor information.

### 7.2 UBY to JD

Formula:

\[
JD = (UBY - 13787002026.0) \times 365.25 + 2461041.5
\]

Function signature:

```python
def uby_to_jd(
    uby_value: Decimal | float | str,
    *,
    anchor: UBYAnchor = DEFAULT_ANCHOR,
) -> Decimal:
    ...
```

### 7.3 ISO 8601 to UBY

Using `astropy.time.Time` is RECOMMENDED:

```python
from astropy.time import Time


def iso_to_uby(
    iso_time: str,
    *,
    scale: str = "utc",
    anchor: UBYAnchor = DEFAULT_ANCHOR,
) -> UBYTime:
    time = Time(iso_time, scale=scale)
    return jd_to_uby(time.jd, anchor=anchor)
```

Notes:

- the input `source_time` SHOULD be retained;
- `source_system` SHOULD be marked as `UTC/ISO8601` or as a caller-specified value;
- leap-second support SHOULD follow `astropy` behavior.

### 7.4 UBY to ISO 8601

```python
def uby_to_iso(
    uby_value: Decimal | float | str,
    *,
    scale: str = "utc",
    anchor: UBYAnchor = DEFAULT_ANCHOR,
) -> str:
    jd = uby_to_jd(uby_value, anchor=anchor)
    return Time(float(jd), format="jd", scale=scale).isot
```

Notes:

- converting `Decimal` to `float` may lose high precision;
- the documentation MUST state that this function is suitable for auxiliary Level 1 display and is not suitable for high-precision timekeeping.

### 7.5 Astronomical Year to UBY

Formula:

\[
UBY_{year}=13787000000+AstronomicalYear
\]

where:

```text
13787000000 = 137870 × 100000
```

Function signature:

```python
def astronomical_year_to_uby(
    year: int,
    *,
    mnemonic_prefix: int = 137870,
    model_version: str = DEFAULT_MODEL_VERSION,
    include_model: bool = False,
) -> UBYTime:
    ...
```

Implementation requirements:

- CE 1 corresponds to astronomical year `1`;
- 1 BC corresponds to astronomical year `0`;
- 221 BC corresponds to astronomical year `-220`;
- the default output is Level 1 precision;
- the model version may be omitted in Level 1 display, but the object SHOULD still retain the default model internally for traceability.

### 7.6 Redshift to UBY

File: `cosmology.py`

Level 3 conversion:

```python
def redshift_to_uby(
    z: float,
    *,
    cosmology_name: str = "Planck18",
    model_version: str = "LCDM-Planck2018",
    uby_version: str = UBY_SPEC_VERSION,
) -> UBYTime:
    ...
```

Recommended implementation:

```python
from astropy.cosmology import Planck18


age = Planck18.age(z)
years = age.to("yr").value
```

Requirements:

- output `precision_level = Level 3`;
- `model_version` MUST be included;
- `t0 - t(z)` MUST NOT be output as UBY;
- `z=0` is the model-reference current cosmic age and is not equal to the concrete calendar-date Level 1 anchor;
- the output SHOULD provide `propagation_note="computed by astropy.cosmology.<model>.age(z)"`.

---

## 8 Formatting Module Design

File: `formatting.py`

### 8.1 Full Numeric Format

Normative format:

```text
UBY <value> [model=<model-id>] [spec=<spec-version>]
```

Function signature:

```python
def format_full(
    uby: UBYTime,
    *,
    include_model: bool = True,
    include_spec: bool = True,
    decimal_places: int | None = None,
) -> str:
    ...
```

Example:

```python
format_full(uby)
# "UBY 13787002026 [model=LCDM-Planck2018] [spec=0.1.0]"
```

### 8.2 Magnitude Shorthand Format

Symbols:

| Symbol | Years |
| --- | --- |
| `K` | \(10^3\) |
| `M` | \(10^6\) |
| `G` | \(10^9\) |
| `T` | \(10^{12}\) |

Function signature:

```python
def format_magnitude(
    uby: UBYTime,
    *,
    digits: int = 4,
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    ...
```

Examples:

```text
UBY 13.787G [model=LCDM-Planck2018] [spec=0.1.0]
UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]
```

### 8.3 Scientific Notation Format

```python
def format_scientific(
    uby: UBYTime,
    *,
    significant_digits: int = 3,
    multiplication_sign: str = "×",
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    ...
```

Example:

```text
UBY 3.8×10^5 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 8.4 Academic Mnemonic Format

```python
def format_academic_mnemonic(
    astronomical_year: int,
    *,
    mnemonic_prefix: int = 137870,
    model_version: str = DEFAULT_MODEL_VERSION,
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    ...
```

Rule:

```text
base = P × 100000
UBY_year = base + AstronomicalYear
```

Examples:

```text
UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]
```

Implementation requirements:

- non-negative astronomical years use `+`;
- negative astronomical years use `-`;
- the suffix is a six-digit absolute value;
- if input exceeds `±999999`, the function SHOULD reject it or switch to the full numeric format;
- the mnemonic MUST NOT be used outside Level 1 precision.

### 8.5 Public-friendly Mnemonic Format

```python
def format_friendly_mnemonic(
    year: int,
    *,
    era: str,
    mnemonic_prefix: int = 137870,
    model_version: str = DEFAULT_MODEL_VERSION,
    include_model: bool = True,
    include_spec: bool = True,
) -> str:
    ...
```

Examples:

```text
UBY 137870 AD2026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870 BC221 [model=LCDM-Planck2018] [spec=0.1.0]
```

Notes:

- `BC221` corresponds to astronomical year `-220`;
- traditional BC years and ISO astronomical year numbering MUST be clearly distinguished.

---

## 9 Parsing Module Design

File: `parsing.py`

### 9.1 Supported Expressions

The parser SHOULD support:

```text
UBY 13787002026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 13.787G [model=LCDM-Planck2018] [spec=0.1.0]
UBY 3.8×10^5 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870+002026 [model=LCDM-Planck2018] [spec=0.1.0]
UBY 137870 AD2026 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 9.2 Recommended Regular Expressions

Full numeric:

```python
FULL_RE = r"^UBY (?P<value>\d+(?:\.\d+)?)(?: \[model=(?P<model>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)\])?(?: \[spec=(?P<spec>\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?)\])?$"
```

Magnitude shorthand:

```python
MAG_RE = r"^UBY (?P<value>\d+(?:\.\d+)?)(?P<mag>[KMGT])(?: \[model=(?P<model>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)\])?(?: \[spec=(?P<spec>\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?)\])?$"
```

Scientific notation:

```python
SCI_RE = r"^UBY (?P<coef>\d+(?:\.\d+)?)(?:x|×)10\^(?P<exp>-?\d+)(?: \[model=(?P<model>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)\])?(?: \[spec=(?P<spec>\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?)\])?$"
```

Academic mnemonic:

```python
MNEMONIC_RE = r"^UBY (?P<prefix>\d{6})(?P<sign>[+-])(?P<year>\d{6})(?: \[model=(?P<model>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)\])?(?: \[spec=(?P<spec>\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?)\])?$"
```

Public-friendly mnemonic:

```python
FRIENDLY_RE = r"^UBY (?P<prefix>\d{6}) (?P<era>AD|BC)(?P<year>\d+)(?: \[model=(?P<model>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)\])?(?: \[spec=(?P<spec>\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?)\])?$"
```

### 9.3 Parsed Output Object

```python
@dataclass(frozen=True)
class ParsedUBYExpression:
    notation: str
    uby_value: Decimal
    model_version: str | None
    uby_version: str | None
    precision_level: PrecisionLevel | None
    raw: str
    warnings: list[str]
```

### 9.4 Parser Warnings

The parser SHOULD emit warnings rather than silently fixing issues:

| Case | Warning |
| --- | --- |
| Missing `[spec=...]` and no outer version | `SPEC_VERSION_UNDECLARED` |
| Level 2/3 expression missing `[model=...]` | `MODEL_VERSION_REQUIRED` |
| Mnemonic prefix inconsistent with model version | `MNEMONIC_MODEL_MISMATCH` |
| Magnitude shorthand used for high-precision computation | `MAGNITUDE_NOT_FOR_STORAGE` |
| Scientific notation missing significant-digit statement | `SIGNIFICANT_DIGITS_UNDECLARED` |

---

## 10 Validation Module Design

File: `validation.py`

### 10.1 Validation Scope

The library SHOULD provide:

```python
def validate_uby_time(uby: UBYTime) -> list[ValidationMessage]:
    ...
```

Validation items include:

- specification version format;
- model version format;
- consistency between precision level and model tag;
- whether the UBY value is non-negative;
- whether Level 1 falls within the ±1 million year window;
- whether the mnemonic is out of range;
- whether decimal places exceed recommended precision;
- whether uncertainty fields are self-consistent.

### 10.2 `ValidationMessage`

```python
@dataclass(frozen=True)
class ValidationMessage:
    code: str
    level: str  # "info" | "warning" | "error"
    message: str
```

### 10.3 Typical Error Codes

| Error code | Level | Meaning |
| --- | --- | --- |
| `UBY_NEGATIVE_VALUE` | error | UBY value is negative |
| `MODEL_REQUIRED_FOR_LEVEL_2_3` | error | Level 2/3 precision is missing a model version |
| `SPEC_VERSION_UNDECLARED` | warning | Specification version is undeclared |
| `FALSE_PRECISION_RISK` | warning | There is a risk of false precision |
| `MNEMONIC_OUT_OF_LEVEL1_RANGE` | error | Mnemonic is outside the Level 1 range |
| `MNEMONIC_MODEL_MISMATCH` | warning | Mnemonic prefix is inconsistent with the model tag |
| `ANCHOR_VERSION_MISMATCH` | error | Anchor and specification version mismatch |

---

## 11 Uncertainty Module Design

File: `uncertainty.py`

### 11.1 Uncertainty Object

```python
@dataclass(frozen=True)
class UBYUncertainty:
    uncertainty_years: Decimal | None = None
    confidence_level: Decimal | None = None
    interval_start_uby: Decimal | None = None
    interval_end_uby: Decimal | None = None
    uncertainty_kind: str | None = None
    propagation_note: str | None = None
```

### 11.2 Interval-precedence Rule

```python
def get_effective_interval(uby: UBYTime) -> tuple[Decimal, Decimal] | None:
    if uby.interval_start_uby is not None and uby.interval_end_uby is not None:
        return uby.interval_start_uby, uby.interval_end_uby
    if uby.uncertainty_years is not None:
        return (
            uby.uby_value - uby.uncertainty_years,
            uby.uby_value + uby.uncertainty_years,
        )
    return None
```

### 11.3 Recommended Error Combination

```python
def combine_uncertainties_quadrature(
    source_sigma: Decimal,
    model_sigma: Decimal,
) -> Decimal:
    return (source_sigma ** 2 + model_sigma ** 2).sqrt()
```

Notes:

- this function is only an informative helper;
- model errors for high-redshift integration SHOULD NOT simply use a global `t0_sigma`; they SHOULD be reintegrated.

---

## 12 Pandas Batch Processing Design

File: `pandas_ext.py`

### 12.1 Accessor Design

```python
@pd.api.extensions.register_series_accessor("uby")
class UBYSeriesAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def from_iso(self, **kwargs) -> pd.Series:
        ...

    def from_jd(self, **kwargs) -> pd.Series:
        ...

    def format_full(self, **kwargs) -> pd.Series:
        ...
```

### 12.2 Example

```python
import pandas as pd
import uby_time

df = pd.DataFrame({
    "event": ["Apollo 11", "Reference Anchor"],
    "iso": ["1969-07-20T20:17:40Z", "2026-01-01T00:00:00Z"],
})

df["uby"] = df["iso"].uby.from_iso()
df["uby_label"] = df["uby"].uby.format_full()
```

### 12.3 Batch Processing Requirements

- failure of a single row SHOULD NOT interrupt the entire table by default;
- `errors="raise" | "coerce" | "ignore"` SHOULD be supported;
- batch outputs SHOULD be able to retain an error-information column.

---

## 13 CLI Command-line Tool Design

File: `cli.py`

### 13.1 Command Structure

```text
uby --help
uby convert iso <ISO_TIME>
uby convert jd <JD>
uby convert year <ASTRONOMICAL_YEAR>
uby convert bc <BC_YEAR>
uby redshift <Z>
uby parse <EXPRESSION>
uby validate <EXPRESSION>
uby reverse jd <UBY_VALUE>
uby reverse iso <UBY_VALUE>
```

### 13.2 Examples

#### ISO to UBY

```bash
uby convert iso 2026-01-01T00:00:00Z
```

Output:

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
precision_level=Level 1
source_system=UTC/ISO8601
anchor_id=UBY-ANCHOR-2026-01-01Z
```

#### BC Year to UBY

```bash
uby convert bc 221
```

Output:

```text
UBY 13786999780 [spec=0.1.0]
academic_mnemonic=UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]
precision_level=Level 1
```

#### Redshift to UBY

```bash
uby redshift 1100 --model LCDM-Planck2018
```

Output:

```text
UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]
precision_level=Level 3
note=computed by astropy.cosmology.Planck18.age(z)
```

### 13.3 CLI Output Formats

Supported formats:

```text
--format text
--format json
--format csv
```

JSON example:

```json
{
  "uby_value": "13787002026.0",
  "uby_version": "0.1.0",
  "model_version": "LCDM-Planck2018",
  "precision_level": "Level 1",
  "source_time": "2026-01-01T00:00:00Z",
  "source_system": "UTC/ISO8601",
  "rounding_rule": "year-floor",
  "anchor_id": "UBY-ANCHOR-2026-01-01Z"
}
```

---

## 14 Test Design

### 14.1 Testing Principles

Tests MUST cover:

- specification examples;
- boundary values;
- invalid inputs;
- cross-format consistency;
- parse-format round trips;
- metadata completeness;
- uncertainty interval logic.

### 14.2 Minimum Test Vectors

File: `tests/fixtures/vectors_wd_0_1_0.json`

```json
[
  {
    "name": "anchor_2026",
    "source_system": "UTC/ISO8601",
    "source_time": "2026-01-01T00:00:00Z",
    "jd": "2461041.5",
    "expected_uby": "13787002026.0",
    "expected_full": "UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]"
  },
  {
    "name": "astronomical_year_1",
    "astronomical_year": 1,
    "expected_uby": "13787000001",
    "expected_mnemonic": "UBY 137870+000001 [model=LCDM-Planck2018] [spec=0.1.0]"
  },
  {
    "name": "bc_221",
    "astronomical_year": -220,
    "expected_uby": "13786999780",
    "expected_mnemonic": "UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]"
  },
  {
    "name": "cmb_decoupling_nominal",
    "uby_value": "380000",
    "expected_magnitude": "UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]",
    "precision_level": "Level 3"
  }
]
```

### 14.3 Key Unit Tests

```python
def test_anchor_iso_to_uby():
    uby = iso_to_uby("2026-01-01T00:00:00Z")
    assert str(uby.uby_value) == "13787002026.0"


def test_bc_221_mnemonic():
    label = format_academic_mnemonic(-220)
    assert label == "UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]"


def test_jd_roundtrip():
    uby = jd_to_uby("2461041.5")
    jd = uby_to_jd(uby.uby_value)
    assert jd == Decimal("2461041.5")
```

---

## 15 Package Configuration

### 15.1 `pyproject.toml` Example

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "uby-time"
version = "0.1.0"
description = "Official Python reference implementation for the UBY Cross-scale Time Labeling Specification"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
  { name = "UBY Specification Contributors" }
]
keywords = [
  "time",
  "chronology",
  "cosmology",
  "julian-date",
  "cross-scale-time",
  "UBY"
]
dependencies = [
  "astropy>=5.3",
  "pydantic>=2.0",
  "click>=8.0"
]

[project.optional-dependencies]
pandas = ["pandas>=2.0"]
dev = [
  "pytest",
  "pytest-cov",
  "ruff",
  "mypy",
  "build",
  "twine"
]
docs = [
  "mkdocs",
  "mkdocs-material"
]

[project.scripts]
uby = "uby_time.cli:main"

[tool.ruff]
line-length = 100

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## 16 Required README Content

The `README.md` front page MUST include:

1. UBY boundary statement;
2. corresponding specification version;
3. installation instructions;
4. quick examples;
5. precision-level explanation;
6. distinction between model version and specification version;
7. out-of-scope scenarios;
8. citation of the specification document;
9. license.

### 16.1 README Opening Template

```markdown
# uby-time

Official Python reference implementation for the UBY Cross-scale Time Labeling Specification.

> UBY is a conventional cross-scale labeling framework, not an absolute physical time system.
> This library does not replace UTC, TAI, JD, MJD, GNSS time, geological timescales, or authoritative scientific datasets.
```

---

## 17 API Usage Examples

### 17.1 ISO Time to UBY

```python
from uby_time import iso_to_uby, format_full

uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))
```

Output:

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 17.2 BC Year

```python
from uby_time import astronomical_year_to_uby, format_academic_mnemonic

uby = astronomical_year_to_uby(-220)
label = format_academic_mnemonic(-220)

print(uby.uby_value)
print(label)
```

Output:

```text
13786999780
UBY 137870-000220 [model=LCDM-Planck2018] [spec=0.1.0]
```

### 17.3 Redshift to UBY

```python
from uby_time import redshift_to_uby, format_magnitude

uby = redshift_to_uby(1100)
print(format_magnitude(uby))
```

Example output:

```text
UBY 380K [model=LCDM-Planck2018] [spec=0.1.0]
```

---

## 18 Versioning Strategy

### 18.1 Relationship Between Library Versions and Specification Versions

| Library version | Corresponding specification | Description |
| --- | --- | --- |
| `uby-time 0.1.x` | UBY WD 0.1.x | Initial reference implementation |
| `uby-time 0.2.x` | UBY WD 0.2.x | Compatibility enhancements |
| `uby-time 1.0.x` | UBY SPEC 1.0.x | Formal specification implementation |

### 18.2 Version Increment Rules

- documentation, test, or non-behavioral fixes: increment PATCH;
- compatible API additions: increment MINOR;
- changes to default anchors, parsing rules, or output formats: increment MAJOR;
- breaking changes during the Working Draft phase SHOULD be clearly marked in `CHANGELOG.md`.

---

## 19 Error Handling Strategy

### 19.1 Exception Types

```python
class UBYError(Exception):
    pass


class UBYParseError(UBYError):
    pass


class UBYValidationError(UBYError):
    pass


class UBYPrecisionError(UBYError):
    pass


class UBYModelError(UBYError):
    pass


class UBYAnchorError(UBYError):
    pass
```

### 19.2 Error Handling Principles

- parsing failures raise `UBYParseError`;
- normative requirement violations raise `UBYValidationError`;
- precision misuse raises or warns with `UBYPrecisionError`;
- nonexistent or unmappable models raise `UBYModelError`;
- anchor-version conflicts raise `UBYAnchorError`.

---

## 20 Security and Reliability Requirements

### 20.1 No-network-by-default Principle

Core library functions MUST NOT retrieve parameters or specification files from the network by default. All default parameters SHOULD be fixed and released with the package.

### 20.2 Parameter Traceability

If user-defined cosmological model parameters are allowed, the following MUST be required:

- `model_version`
- parameter source description
- parameter values
- units
- generation time
- notes

### 20.3 Auditable Results

All formal conversion results SHOULD be exportable as JSON and include sufficient metadata for reproducibility.

---

## 21 Documentation Site Structure

MkDocs is RECOMMENDED:

```text
docs/
├─ index.md
├─ quickstart.md
├─ concepts.md
├─ precision-levels.md
├─ conversions.md
├─ formatting.md
├─ parsing.md
├─ uncertainty.md
├─ cli.md
├─ api-reference.md
└─ interoperability.md
```

### 21.1 Required API Documentation

Each public function MUST document:

- input parameters;
- output object;
- precision level;
- whether it depends on a model;
- whether it may create false-precision risk;
- examples;
- exceptions;
- corresponding specification section.

---

## 22 Release Process

### 22.1 Pre-release Checks

```bash
ruff check src tests
mypy src
pytest --cov=uby_time
python -m build
```

### 22.2 Release to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

### 22.3 Release to PyPI

```bash
python -m twine upload dist/*
```

### 22.4 Release Checklist

Each release MUST update:

- `CHANGELOG.md`
- `pyproject.toml`
- `docs/index.md`
- corresponding specification-version notes
- test-vector version

---

## 23 Minimum Implementation Milestones

### Milestone 0: Project Skeleton

- create `pyproject.toml`
- create package directory
- create test framework
- create README
- create basic constants

### Milestone 1: Level 1 Conversion

- JD ↔ UBY
- ISO ↔ UBY
- astronomical year ↔ UBY
- default anchor
- basic test vectors

### Milestone 2: Formatting and Parsing

- full numeric format
- magnitude shorthand format
- scientific notation format
- academic mnemonic
- public-friendly mnemonic
- expression parsing

### Milestone 3: Precision and Uncertainty

- precision-level detection
- uncertainty fields
- validation against false precision
- validation message system

### Milestone 4: Level 3 Cosmological Conversion

- `astropy.cosmology` integration
- redshift `z` to UBY
- model-version recording
- explanation of the difference between `z=0` and the Level 1 anchor

### Milestone 5: CLI and Pandas

- CLI conversion commands
- JSON output
- Pandas batch conversion
- example scripts

### Milestone 6: Documentation and Release

- MkDocs documentation site
- PyPI release
- interoperability test vectors
- version compatibility notes

---

## 24 Minimum Public API List

It is recommended that `uby_time.__init__` expose:

```python
from .conversion import (
    jd_to_uby,
    uby_to_jd,
    iso_to_uby,
    uby_to_iso,
    astronomical_year_to_uby,
)

from .cosmology import redshift_to_uby

from .formatting import (
    format_full,
    format_magnitude,
    format_scientific,
    format_academic_mnemonic,
    format_friendly_mnemonic,
)

from .parsing import parse_uby_expression
from .validation import validate_uby_time
from .models import UBYTime, UBYAnchor, PrecisionLevel
```

---

## 25 Mapping to Specification Sections

| Development module | Corresponding specification section |
| --- | --- |
| `models.py` | Sections 3, 9, and 11 |
| `anchors.py` | Section 7 |
| `conversion.py` | Section 7 |
| `cosmology.py` | Sections 5.3 and 7.4 |
| `formatting.py` | Section 6 |
| `parsing.py` | Section 6 and Appendix E |
| `validation.py` | Sections 4, 5, 6, 9, and 11 |
| `uncertainty.py` | Section 11 |
| `pandas_ext.py` | Appendix F and Appendix G |
| `cli.py` | Appendix F.4 |

---

## 26 Development Red Lines

Implementers MUST NOT:

1. omit the model version by default for Level 2 and Level 3 precision;
2. output `t0 - t(z)` as UBY;
3. confuse the cosmic age at `z=0` with a concrete calendar-date anchor;
4. assume uncertainty is zero when no uncertainty statement is provided;
5. use magnitude shorthand as the only storage format;
6. use mnemonics outside Level 1 precision;
7. claim that UBY is an absolute time system;
8. use the library for legal, commercial, navigation, timekeeping, or other prohibited contexts;
9. automatically assume the latest version when the specification version is undeclared;
10. upgrade only `uby_version` without recording `model_version` when model parameters change.

---

## 27 Conclusion

`uby-time` is not intended to pursue feature expansion for its own sake. Its role is to provide a clear, reproducible, auditable, and testable minimum authoritative implementation for the UBY Cross-scale Time Labeling Specification.

The success criteria for this library are:

- consistency with the specification;
- traceable outputs;
- explainable errors;
- no precision inflation;
- interoperable formats;
- easy integration for developers;
- reproducibility in long-term archival contexts.
